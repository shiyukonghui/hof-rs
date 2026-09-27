#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-106 part A: the acceptance criteria of the re-run, checked against the
run's own files, with the numbers printed rather than asserted in prose.

    python check_snake_task106.py <run-dir>

Criteria (from the TASK-106 order, section A):

  A1  the engine's stdout carries SNAKE_SELF at least once (the self-collision
      rule was really walked, not just asserted about);
  A2  the ledger's game phase has NO `scenario_assertion_failed` row;
  A3  the only failing calls it does have are the two DECLARED ones
      (`g04-park-check-must-fail`, `g26-wall-assert-must-fail`);
  A4  the response files carry no undeclared failing assertion;
  A5  g19-turn-down, g20b-dump-self-board, g22-self-collision and
      g25-wall-collision say what they are supposed to say.

The script writes its own report; the caller decides where. Nothing is written
into the run directory.
"""
import glob
import io
import json
import os
import sys

RESULT = []


def say(line=""):
    print(line)
    RESULT.append(line)


def read(path, encoding="utf-8-sig"):
    if not os.path.exists(path):
        return None
    with io.open(path, encoding=encoding, errors="replace") as handle:
        return handle.read()


def read_json(path):
    text = read(path)
    if text is None:
        return None
    try:
        return json.loads(text)
    except ValueError:
        return None


def body_of(path):
    obj = read_json(path)
    if not isinstance(obj, dict):
        return None
    try:
        body = json.loads(obj["result"]["content"][0]["text"])
    except Exception:
        return None
    return body if isinstance(body, dict) else None


DECLARED_KEYS = ("must fail", "must-fail", "boundary", "boundary call",
                 "注定失败", "intentionally", "expected to fail", "declared failure")


def declared_tags(run):
    tags = {}
    for line in (read(os.path.join(run, "call-index.txt")) or "").splitlines():
        parts = line.split("|")
        if len(parts) < 5:
            continue
        note = "|".join(parts[4:]).strip()
        if any(k in note.lower() for k in DECLARED_KEYS):
            tags[parts[0].strip()] = note
    return tags


def seq_to_tag(run, trace_name="trace-game.jsonl"):
    """Map the ledger's own `call_id` (the trace sequence number) back to the call's
    tag, through the trace's `id` and the `id` every saved request file carries."""
    id_to_tag = {}
    for path in glob.glob(os.path.join(run, "*.request.json")):
        obj = read_json(path)
        if isinstance(obj, dict) and obj.get("id") is not None:
            id_to_tag[obj["id"]] = os.path.basename(path)[:-len(".request.json")]
    mapping = {}
    for line in (read(os.path.join(run, trace_name)) or "").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        if rec.get("seq") is None or rec.get("id") is None:
            continue
        tag = id_to_tag.get(rec["id"])
        if tag:
            mapping[rec["seq"]] = tag
    return mapping


def main():
    run = os.path.abspath(sys.argv[1])
    ok = True

    # --- A1: SNAKE_SELF in the engine's own stdout ---------------------------
    stdout = read(os.path.join(run, "engine-game.stdout.txt")) or ""
    self_lines = [l for l in stdout.splitlines() if "SNAKE_SELF" in l]
    aim_lines = [l for l in stdout.splitlines() if "SNAKE_AIM" in l]
    say("== A1 self-collision really walked")
    say("   SNAKE_SELF lines: %d" % len(self_lines))
    for l in self_lines:
        say("     %s" % l)
    say("   SNAKE_AIM boards in engine order:")
    for l in aim_lines:
        say("     %s" % l)
    if len(self_lines) < 1:
        ok = False
        say("   FAIL: SNAKE_SELF never appeared")
    if not any("head=9,10" in l for l in self_lines):
        ok = False
        say("   FAIL: the self-collision was not the aimed head 10,10 -> 9,10")

    # --- A2/A3: the ledger's flags -------------------------------------------
    ledger = read_json(os.path.join(run, "ledger-game.json")) or {}
    rows = ledger.get("rows") or []
    scenario_failed = [r for r in rows if "scenario_assertion_failed" in (r.get("result_flags") or [])]
    assertion_failed = [r for r in rows if "assertion_failed" in (r.get("result_flags") or [])]
    say("")
    say("== A2/A3 ledger flags (game phase)")
    say("   calls=%s malformed_lines=%s" % (ledger.get("calls"), ledger.get("malformed_lines")))
    say("   rows with scenario_assertion_failed: %d" % len(scenario_failed))
    for r in scenario_failed:
        say("     seq=%s %s %s" % (r.get("seq"), r.get("call_id"), r.get("tool")))
    say("   rows with assertion_failed: %d" % len(assertion_failed))
    declared = declared_tags(run)
    seqmap = seq_to_tag(run)
    for r in assertion_failed:
        seq = r.get("call_id")
        tag = seqmap.get(seq, "<unmapped seq %s>" % seq)
        say("     seq=%s tag=%s declared=%s" % (
            seq, tag, "YES" if (tag in declared or "must-fail" in tag) else "NO"))
    if scenario_failed:
        ok = False
        say("   FAIL: a scenario assertion failure is still unaccounted for")
    if len(assertion_failed) != 2:
        ok = False
        say("   FAIL: expected exactly the 2 declared must-fail rows")
    for r in assertion_failed:
        tag = seqmap.get(r.get("call_id"), "")
        if not (tag in declared or "must-fail" in tag):
            ok = False
            say("   FAIL: seq %s (%s) is not a declared failure" % (r.get("call_id"), tag))

    # --- A4: no undeclared failing assertion among the responses --------------
    say("")
    say("== A4 declared vs undeclared failing assertions (from the run's own *.json)")
    passed = failed = errors = 0
    undeclared = []
    failure_rows = []
    for path in sorted(glob.glob(os.path.join(run, "*.json"))):
        if path.endswith(".request.json"):
            continue
        body = body_of(path)
        if body is None:
            continue
        tag = os.path.basename(path)[:-len(".json")]
        entries = []
        if "all_passed" in body:
            passed += int(body.get("passed") or 0)
            failed += int(body.get("failed") or 0)
            errors += int(body.get("errors") or 0)
            for step in body.get("results") or []:
                if isinstance(step, dict) and step.get("type") == "assert" and step.get("passed") is False:
                    entries.append("scenario:%s %s %s -> actual %s" % (
                        step.get("property"), step.get("operator"), step.get("expected"), step.get("actual")))
        elif "passed" in body:
            if body.get("passed"):
                passed += 1
            else:
                failed += 1
                entries.append("node_state:%s %s %s -> actual %s" % (
                    body.get("property"), body.get("operator"), body.get("expected"), body.get("actual")))
        for what in entries:
            is_declared = ("must-fail" in tag) or (tag in declared)
            failure_rows.append((tag, what, is_declared))
            if not is_declared:
                undeclared.append((tag, what))
    say("   assertions: passed=%d failed=%d errors=%d" % (passed, failed, errors))
    for tag, what, is_declared in failure_rows:
        say("   %-32s declared=%-3s %s" % (tag, "YES" if is_declared else "NO", what))
    say("   UNDECLARED failing assertions: %d" % len(undeclared))
    for tag, what in undeclared:
        say("     %s :: %s" % (tag, what))
    if undeclared:
        ok = False
        say("   FAIL: undeclared failures present")

    # --- A5: the five named calls --------------------------------------------
    say("")
    say("== A5 the named calls")
    expectations = [
        ("g19-turn-down", lambda b: b.get("all_passed") is True and b.get("failed") == 0,
         "DirectionY assertion passed"),
        ("g20-aim-self", lambda b: "dir=-1,0" in str(b.get("result")), "aim writes dir=-1,0"),
        ("g20b-dump-self-board",
         lambda b: "segs=10,10|9,10|8,10|7,10|6,10" in str(b.get("result")) and "dir=-1,0" in str(b.get("result")),
         "the board dump shows the head aimed into the neck"),
        ("g22-self-collision", lambda b: b.get("all_passed") is True and b.get("passed") == 2,
         "GameOver and LoseReason=self both passed"),
        ("g25-wall-collision", lambda b: b.get("all_passed") is True and b.get("passed") == 2,
         "GameOver and LoseReason=wall both passed"),
        ("g26-wall-assert-must-fail", lambda b: b.get("passed") is False, "declared must-fail still fails"),
        ("g04-park-check-must-fail", lambda b: b.get("passed") is False, "declared must-fail still fails"),
    ]
    for tag, predicate, description in expectations:
        body = body_of(os.path.join(run, tag + ".json"))
        good = body is not None and predicate(body)
        if not good:
            ok = False
        say("   %-30s %s  (%s)" % (tag, "OK" if good else "FAIL", description))
    # the raw numbers behind the two biggest ones
    for tag in ("g19-turn-down", "g22-self-collision"):
        body = body_of(os.path.join(run, tag + ".json")) or {}
        for step in body.get("results") or []:
            if isinstance(step, dict) and step.get("type") == "assert":
                say("     %s %s: expected=%s actual=%s passed=%s" % (
                    tag, step.get("property"), step.get("expected"), step.get("actual"), step.get("passed")))

    # --- the scene tree must be the built one, with no duplicate layer --------
    say("")
    say("== scene tree")
    tree = body_of(os.path.join(run, "g28-scene-tree-final.json"))
    names = []
    if isinstance(tree, dict):
        def walk(node):
            if not isinstance(node, dict):
                return
            names.append(str(node.get("name")))
            for child in node.get("children") or []:
                walk(child)
        walk(tree.get("tree") or tree.get("result") or {})
    if not names:
        text = read(os.path.join(run, "g28-scene-tree-final.json")) or ""
        names = [n for n in ("SnakeSeg00", "Background", "GridLineV0") if n in text]
    at_names = [n for n in names if n.startswith("@")]
    say("   names found: %d ; names starting with '@': %d" % (len(names), len(at_names)))
    if at_names:
        ok = False
        say("   FAIL: automatic duplicate names in the tree: %s" % at_names[:10])

    # --- the report's own assertion column must agree ------------------------
    say("")
    say("== report.json cross-check")
    report = read_json(os.path.join(run, "report.json"))
    if isinstance(report, dict) and "assertions" in report:
        aa = report["assertions"]
        say("   report assertions: passed=%s failed=%s undeclared=%s" % (
            aa.get("passed"), aa.get("failed"), aa.get("undeclared_count")))
        if aa.get("undeclared_count") != len(undeclared):
            ok = False
            say("   FAIL: report's undeclared count disagrees with the independent count")
        if aa.get("passed") != passed or aa.get("failed") != failed:
            ok = False
            say("   FAIL: report's passed/failed tallies disagree")
    else:
        ok = False
        say("   FAIL: report.json carries no assertions section")

    say("")
    say("CHECK_SNAKE_TASK106 %s" % ("OK" if ok else "FAIL"))
    if len(sys.argv) > 2:
        # iron rule 1: the log is written by this Python writer, never by a shell
        # redirect.
        with io.open(sys.argv[2], "w", encoding="utf-8", newline="\n") as handle:
            handle.write("\n".join(RESULT) + "\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
