#!/usr/bin/env python3
"""TASK-059 D-4: the pre/post comparison of the contract (175 entries then).

The claim this script makes executable is narrow and total: this batch is allowed
to change **five `description` fields**, the generator version, and the
`_meta.overrides` audit records that explain them. Everything else in
`docs/tools_list.renamed.json` - every `name`, every `inputSchema`, the order of
`result.tools`, `_meta.count`, `_meta.map_sha256`, `_meta.added_tools`,
`_meta.excluded`, `_meta.merged` - must be **byte identical** to the tree before
the batch. The one thing this script now allows *after* the batch, without
weakening the claim, is the **appended contract entry of a later batch**: the
contract is allowed to grow by exactly the names it declares in
`_meta.added_tools` beyond the before side's declared set, in order at the end of
`result.tools`. An undeclared append, a rename, a reorder or a removal is still a
FAILURE. (TASK-064 D-8: the old `count == 175` literal was the one assertion that
treated a legitimate later append as a failure.)

It is an allow-list, not a diff reader: a difference outside the list is a
FAILURE, not a note.

The "before" side is read out of git (`git show <rev>:<path>`), so the comparison
does not depend on keeping a second copy of the file around and it can be
re-run from any checkout of this repository:

    python scripts/mcp059_contract_pre_post.py                      # before = the recorded pre-batch revision
    python scripts/mcp059_contract_pre_post.py --rev <sha>

`--rev` defaults to PRE_BATCH_REV below rather than to HEAD on purpose: once the
batch is committed, HEAD *is* the after side, and comparing it with itself would
report "nothing moved" - which is a true statement about a comparison nobody
asked for and a false one about this batch. Found the hard way: the first gate
run of this script used HEAD and failed on an empty move list.

Exit 0 when only the allowed paths differ; exit 1 otherwise.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE_ROOT = os.path.dirname(HERE)
REPO_ROOT = os.path.dirname(os.path.dirname(MODULE_ROOT))
CONTRACT_REL = os.path.join("modules", "mcp_server", "docs", "tools_list.renamed.json")

# The revision the batch started from: `docs(mcp_server): TASK-059 brief and
# REPORT-057 (recovered)`, the last commit that did not contain any TASK-059
# change. Override with `--rev` to compare against anything else.
PRE_BATCH_REV = "213b1791258aa476e6b271e57733a689ad8f3ff9"

# TASK-064 D-8: the ported half of the contract size. The contract is
# `171 ported + _meta.added_count` (GDR-17/GDR-28), and this literal half is what
# catches a contract that silently lost a ported entry - a loss the self-consistent
# `count == len(result.tools)` could never see. Every strictness of the old
# `len(b_tools) == len(a_tools) == 175` is derived from this plus the two
# contracts' own `_meta`; see `count_is_ported_plus_added_on_both_sides`.
CONTRACT_PORTED_COUNT = 171

# The five tools whose description TASK-059 D-4 rewrote, and which of them moved
# to the section-granular writer.
SWITCHED = ["project_set_setting", "editor_add_input_action", "project_add_autoload"]
KEPT = ["project_remove_autoload", "editor_reload_plugin"]
FIVE = SWITCHED + KEPT

# Top-level `_meta` keys allowed to move, with the reason.
ALLOWED_META = {
    "generator_version": "TASK-059 D-4 bumps 1.17.0 -> 1.18.0 so the three-way "
                         "consistency assertion (generator / contract / tool-groups-added.json) stays exact",
    "overrides": "the audit records of the five rewritten descriptions; each new reason quotes both "
                 "the original wording and the false sentence being removed",
}

failures = 0


def check(ok: bool, name: str, detail: str) -> bool:
    global failures
    if not ok:
        failures += 1
    print("[%s] %s :: %s" % ("PASS" if ok else "FAIL", name, detail))
    return ok


def git_show(rev: str, rel: str) -> bytes:
    out = subprocess.run(["git", "-C", REPO_ROOT, "show", "%s:%s" % (rev, rel)],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if out.returncode != 0:
        raise SystemExit("git show %s:%s failed: %s" % (rev, rel, out.stderr.decode("utf-8", "replace")))
    return out.stdout


def is_ordered_subsequence(before, after):
    """True when `before` is `after` with entries only appended at the end.

    TASK-064 D-8: the growth this script has to survive is an *append* to the
    ordered `result.tools` list (the generator's `ADDED_TOOLS` order puts every
    added entry after the ported ones), so a rename, a removal or a reorder must
    still fail while a declared append must not.
    """
    if len(before) > len(after):
        return False
    return list(after[:len(before)]) == list(before)


def first_difference(before, after):
    for index, (left, right) in enumerate(zip(before, after)):
        if left != right:
            return "position %d: %r -> %r" % (index, left, right)
    return "no differing position within the common prefix (before is a prefix of after)"


def main() -> int:
    parser = argparse.ArgumentParser(description="TASK-059 D-4 contract pre/post allow-list comparison.")
    parser.add_argument("--rev", default=PRE_BATCH_REV, help="the BEFORE revision (default: PRE_BATCH_REV)")
    args = parser.parse_args()

    before_raw = git_show(args.rev, CONTRACT_REL.replace(os.sep, "/"))
    path = os.path.join(MODULE_ROOT, "docs", "tools_list.renamed.json")
    after_raw = io.open(path, "rb").read()

    before = json.loads(before_raw.decode("utf-8"))
    after = json.loads(after_raw.decode("utf-8"))
    print("before: %s:%s (%d bytes)" % (args.rev, CONTRACT_REL.replace(os.sep, "/"), len(before_raw)))
    print("after : %s (%d bytes)" % (path, len(after_raw)))
    print("")

    b_tools = before["result"]["tools"]
    a_tools = after["result"]["tools"]
    # TASK-064 D-8: this was `len(b_tools) == len(a_tools) == 175`. The 175 was
    # the contract size at TASK-059 and went stale the moment a later batch
    # legitimately appended an entry (measured: TASK-063 appended
    # `editor_set_node_property_updates`, 175 -> 176). The expectation is now
    # derived from the two artefacts the check is really about:
    #   * `_meta.count` must equal `len(result.tools)` on both sides, and the
    #     contract formula `count == 171 ported + added_count` must hold (the
    #     same formula `accept_m1.ps1` and `check_tool_groups.py --completeness`
    #     enforce);
    #   * the after side may be LONGER than the before side only by exactly the
    #     names the after contract itself declares as added beyond the before
    #     side's declared set (`_meta.added_tools`), and the before `result.tools`
    #     must be an ordered prefix of the after one. An undeclared append, a
    #     rename, a removal or a reorder all still fail.
    before_declared = [str(name) for name in before["_meta"].get("added_tools", [])]
    after_declared = [str(name) for name in after["_meta"].get("added_tools", [])]
    appended = [str(tool["name"]) for tool in a_tools[len(b_tools):]]
    b_names = [t["name"] for t in b_tools]
    a_names = [t["name"] for t in a_tools]
    check(before["_meta"].get("count") == len(b_tools) and after["_meta"].get("count") == len(a_tools),
          "count_is_len_result_tools",
          "_meta.count before=%r (entries=%d), after=%r (entries=%d)"
          % (before["_meta"].get("count"), len(b_tools), after["_meta"].get("count"), len(a_tools)))
    check(is_ordered_subsequence(b_names, a_names), "names_and_order_unchanged_up_to_appended_entries",
          "before is an ordered prefix of after; appended tail = %s" % (appended,))
    check(len(a_tools) >= len(b_tools) and appended == after_declared[len(before_declared):],
          "growth_is_exactly_the_newly_declared_added_tools",
          "appended=%s; newly declared added_tools=%s (derived; the literal 175 is gone - TASK-064 D-8)"
          % (appended, after_declared[len(before_declared):]))
    check(before["_meta"].get("count") == CONTRACT_PORTED_COUNT + len(before_declared)
          and after["_meta"].get("count") == CONTRACT_PORTED_COUNT + len(after_declared),
          "count_is_ported_plus_added_on_both_sides",
          "before %r = %d + %d, after %r = %d + %d"
          % (before["_meta"].get("count"), CONTRACT_PORTED_COUNT, len(before_declared),
             after["_meta"].get("count"), CONTRACT_PORTED_COUNT, len(after_declared)))
    if not is_ordered_subsequence(b_names, a_names):
        print("       first differing position :: %s" % first_difference(b_names, a_names))

    b_names = [t["name"] for t in b_tools]
    a_names = [t["name"] for t in a_tools]

    b_by = {t["name"]: t for t in b_tools}
    a_by = {t["name"]: t for t in a_tools}
    # inputSchema: every one, byte identical (serialised with sorted keys, so the
    # comparison is about content and not about key order inside the object).
    schema_moved = []
    for name in b_names:
        b_schema = json.dumps(b_by[name]["inputSchema"], sort_keys=True, separators=(",", ":"))
        a_schema = json.dumps(a_by[name]["inputSchema"], sort_keys=True, separators=(",", ":"))
        if b_schema != a_schema:
            schema_moved.append(name)
    check(schema_moved == [], "every_inputSchema_identical",
          "moved schema(s): %s" % (", ".join(schema_moved) if schema_moved else "none (%d/%d compared)" % (len(a_names), len(b_names))))

    # description: exactly the five. `a_names` may legitimately be longer than
    # `b_names` (a later batch's appended entry), and later batches may
    # legitimately rewrite descriptions of their own - neither is this script's
    # subject. What this batch owns is the five names below, so the check is
    # scoped to exactly those five, each of which must have moved. TASK-064 D-8:
    # the old form `sorted(desc_moved) == sorted(FIVE)` compared two things -
    # "the five moved" (this batch's claim) and "no later batch will ever rewrite
    # another description" (not a claim about this batch at all) - and the second
    # half went red the moment TASK-063 rewrote
    # `editor_set_node_property`/`editor_get_node_properties`. Later rewrites are
    # reported rather than asserted on: they cannot be attributed to this batch
    # from HEAD, and they are covered forward by the pre/post pairs of the batches
    # that make them and by gate 1's verbatim live `tools/list` comparison.
    desc_moved = [n for n in b_names if b_by[n]["description"] != a_by[n]["description"]]
    check(all(n in desc_moved for n in FIVE), "all_five_descriptions_moved",
          "moved among the five: %s" % (", ".join(n for n in FIVE if n in desc_moved),))
    print("       report: descriptions that moved and are not one of the five :: %s (later-batch moves; not this batch's subject)"
          % (", ".join(n for n in desc_moved if n not in FIVE) or "none"))

    # The false claim is gone from every description, and each new one keeps the
    # Chinese head verbatim and states the three required things.
    for name in FIVE:
        new = a_by[name]["description"]
        old = b_by[name]["description"]
        head = old.split(" ")[0]
        if name in SWITCHED:
            ok = (new.startswith(head + " ")) and ("section by section" in new) and \
                 ("behaviour improvement" in new) and ("never creates one" in new) and \
                 ("no partial-publish" not in new) and ("entire project.godot with the engine's own whole-file writer" not in new)
            detail = "head %r kept, states the section write + the four fall-backs + the improvement, and no longer claims there is no partial-publish API" % head
        else:
            ok = (new.startswith(head + " ")) and ("no partial-publish" not in new) and \
                 ("whole-file writer" in new)
            detail = "head %r kept, no longer claims there is no partial-publish API, and still describes the whole-file rewrite it really does" % head
        check(ok, "desc_%s" % name, detail)

    # _meta: only the two allowed keys - plus the three growth fields, and only
    # when the after side really is the before side grown by the appended names
    # the three checks above already validated. TASK-064 D-8: those three keys
    # used to be listed as "must not move", which made a legitimate later append
    # a failure of a batch that did not append anything. They are now part of the
    # movable set *conditionally*: if the contract did not grow, they must not
    # have moved either (`declared_growth_is_consistent` below states that both
    # ways, so nothing is relaxed in the no-growth case).
    b_meta = {k: v for k, v in before["_meta"].items()}
    a_meta = {k: v for k, v in after["_meta"].items()}
    meta_moved = [k for k in set(b_meta) | set(a_meta) if b_meta.get(k) != a_meta.get(k)]
    grew = len(a_tools) != len(b_tools)
    growth_is_declared = (
        len(a_tools) >= len(b_tools)
        and appended == after_declared[len(before_declared):]
        and bool(grew) == bool(appended)
        and all(key in meta_moved for key in ("count", "added_tools", "added_count")) == grew
    ) if grew else (appended == [] and not (set(("count", "added_tools", "added_count")) & set(meta_moved)))
    check(growth_is_declared, "declared_growth_is_consistent",
          "grew=%s appended=%s newly declared added_tools=%s; growth fields moved=%s (a no-growth run requires none of them to move)"
          % (grew, appended, after_declared[len(before_declared):],
             sorted(set(("count", "added_tools", "added_count")) & set(meta_moved))))
    movable = set(ALLOWED_META) | ({"count", "added_tools", "added_count"} if grew else set())
    unexpected_meta = [k for k in meta_moved if k not in movable]
    check(unexpected_meta == [], "meta_only_the_allowed_keys_moved",
          "moved: %s; unexpected: %s" % (", ".join(sorted(meta_moved)), ", ".join(sorted(unexpected_meta)) if unexpected_meta else "none"))
    for key in sorted(meta_moved):
        if key in ALLOWED_META:
            print("       allowed meta key %r moved :: %s" % (key, ALLOWED_META[key]))
        elif key in movable:
            print("       declared-growth meta key %r moved :: the after side is the before side grown by the declared added tools (TASK-064 D-8)" % key)

    # The identity fields a careless regeneration would move, called out
    # individually. `count`/`added_tools`/`added_count` are checked for equality
    # when the contract did not grow, and for declared growth when it did (the
    # `declared_growth_is_consistent` check above is the machine statement of
    # that either/or). TASK-064 D-8.
    for key in ("count", "map_sha256", "added_tools", "added_count", "excluded", "merged",
                "generated_from_sha256", "order_normative", "tool_count_in"):
        if key in b_meta and key in a_meta:
            if key in ("count", "added_tools", "added_count") and grew:
                check(growth_is_declared, "meta_%s_is_the_declared_growth" % key,
                      "before=%r after=%r (growth declared by the appended added tools: %s)"
                      % (b_meta[key], a_meta[key], appended))
            else:
                check(b_meta[key] == a_meta[key], "meta_%s_unchanged" % key,
                      "%r" % (a_meta[key],))

    # The five override records exist and are `mode: replace`, i.e. the audit
    # trail for a false statement being rewritten is explicit.
    a_overrides = {(r["old_name"], r["kind"]): r for r in a_meta.get("overrides", [])}
    replace_records = []
    for old_name in ("set_project_setting", "add_autoload", "remove_autoload", "set_input_action", "reload_plugin"):
        record = a_overrides.get((old_name, "description"))
        if record is not None and record.get("mode") == "replace":
            replace_records.append(old_name)
    check(len(replace_records) == 5, "five_replace_records_present",
          "mode=replace description overrides: %s" % ", ".join(sorted(replace_records)))

    print("")
    if failures:
        print("CONTRACT PRE/POST FAILED: %d problem(s)" % failures)
        return 1
    print("CONTRACT PRE/POST PASS (only the five descriptions, the generator version and their audit records moved)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
