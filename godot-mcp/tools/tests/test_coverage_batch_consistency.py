#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""test_coverage_batch_consistency.py -- the coverage ledger and its batch gate must agree.

WHY THIS EXISTS (TASK-143 sections A.1 and C item 4)
----------------------------------------------------
`coverage.json` (built by `tools/tool_coverage.py`) is the ledger that decides
whether a contract tool is 达标. Since TASK-118 it judges each tool ON ITS OWN
DECLARED EVIDENCE CHANNEL (`tool_channels.json`): a tool whose effect lives in
the editor process' memory is judged by a verified witness read-back, not by a
pixel/file delta. The ledger therefore carries TWO quantities per tool:

    effective        the PRE-TASK-118 quantity: a pixel or a file really moved
    channel_evidence the quantity the ledger actually judges (>=1 + ok)
    channel_evidence_ok  the verdict that decides `status`

`tools/verify_coverage_batch.py` is the per-batch gate, and it still applies its
original rule `calls >= 5 and effective >= 1 and (boundary >= 1 or edge)`. For
every `editor_state`-channel tool `effective` is 0 by construction - the whole
point of TASK-118 - so the batch gate reports red for tools the ledger marks
达标.

MEASURED (TASK-143, current corpus, all 20 exercise manifests):
    166 targets, 118 pass, 48 fail
    of the 48 fails, 45 are FALSE REDS (the ledger says 达标 with
    channel_evidence_ok == true) and 3 are genuine shortage
    (channel_evidence_ok == false):
        editor_set_auto_dismiss_dialogs, os_deploy_to_android_device,
        project_get_android_preset_info

This file makes that disagreement EXECUTABLE instead of a paragraph in a report:
it runs the real `verify_coverage_batch.py` (not a second copy of its rule) and
pins the disagreement, so that fixing the gate shows up here as a deliberate
change rather than passing unnoticed.

Run:
    D:\\Anaconda\\python.exe -m pytest tools\\tests\\test_coverage_batch_consistency.py -q
"""
from __future__ import print_function

import io
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS_DIR)
COVERAGE = os.path.join(ROOT, "coverage.json")
VERIFY = os.path.join(TOOLS_DIR, "verify_coverage_batch.py")
MANIFEST_DIR = os.path.join(TOOLS_DIR, "sessions", "_exercises")

# ---------------------------------------------------------------------------
# PINNED: the measured disagreement of the legacy batch rule with the ledger.
# Update these deliberately, with the reason, if either side changes.
# ---------------------------------------------------------------------------
PINNED_TARGETS = 166
PINNED_PASS = 118
PINNED_FALSE_REDS = 45
PINNED_GENUINE = frozenset((
    "editor_set_auto_dismiss_dialogs",
    "os_deploy_to_android_device",
    "project_get_android_preset_info",
))


def manifests():
    found = []
    for dirpath, _dirnames, filenames in os.walk(MANIFEST_DIR):
        for name in sorted(filenames):
            if name.endswith("-manifest.json"):
                found.append(os.path.join(dirpath, name))
    return sorted(found)


def load_coverage(path=COVERAGE):
    with io.open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def run_verify(manifests_list):
    """Run the REAL tools/verify_coverage_batch.py over the given manifests."""
    handle, out_path = tempfile.mkstemp(prefix="task143-batch-", suffix=".json")
    os.close(handle)
    try:
        cmd = [sys.executable, VERIFY]
        for m in manifests_list:
            cmd += ["--manifest", m]
        cmd += ["--coverage", COVERAGE, "--json", out_path]
        proc = subprocess.run(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if proc.returncode not in (0, 1):
            raise AssertionError("verify_coverage_batch.py exited %d:\n%s"
                                 % (proc.returncode, proc.stdout.decode("utf-8", "replace")))
        with io.open(out_path, "r", encoding="utf-8") as h:
            return json.load(h)
    finally:
        try:
            os.remove(out_path)
        except OSError:
            pass


def split_disagreements(report, rows):
    """(false_reds, genuine) - the fails of the legacy rule the ledger disagrees with."""
    false_reds, genuine = [], []
    for entry in report["results"]:
        if entry["verdict"] != "fail":
            continue
        row = rows.get(entry["tool"]) or {}
        if row.get("channel_evidence_ok") is True:
            false_reds.append(entry["tool"])
        else:
            genuine.append(entry["tool"])
    return sorted(false_reds), sorted(genuine)


# ---------------------------------------------------------------------------
# the ledger's own internal invariant
# ---------------------------------------------------------------------------
def check_ledger_internal(coverage):
    """`channel_evidence_ok` must be exactly `channel_evidence >= 1`, and it alone
    must decide the 达标 status of a tool that is not registered as unreachable."""
    bad = []
    for row in coverage["tools"]:
        ev = row.get("channel_evidence")
        ok = row.get("channel_evidence_ok")
        if not isinstance(ev, int):
            bad.append("%s: channel_evidence is %r" % (row["tool"], ev))
            continue
        if bool(ok) != (ev >= 1):
            bad.append("%s: channel_evidence=%s but channel_evidence_ok=%r" % (row["tool"], ev, ok))
        if row.get("unreachable_category"):
            continue
        chose = (row.get("status") == "达标")
        if chose != bool(ok):
            bad.append("%s: status=%r with channel_evidence_ok=%r" % (row["tool"], row.get("status"), ok))
    return bad


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------
COVERAGE_DOC = load_coverage()
COVERAGE_ROWS = {r["tool"]: r for r in COVERAGE_DOC["tools"]}
MANIFESTS = manifests()


def test_the_ledger_is_internally_consistent():
    complaints = check_ledger_internal(COVERAGE_DOC)
    assert complaints == [], complaints[:5]


def test_the_negative_the_internal_check_is_not_vacuous():
    """A row whose channel_evidence is zeroed must make the check complain."""
    doc = json.loads(json.dumps(COVERAGE_DOC))
    target = None
    for row in doc["tools"]:
        if row.get("channel_evidence", 0) >= 1:
            target = row
            break
    assert target is not None, "no ledger row carries channel evidence to mutate"
    target["channel_evidence"] = 0
    complaints = check_ledger_internal(doc)
    assert any(target["tool"] in c for c in complaints), \
        "zeroing channel_evidence did not make the ledger check complain"


def test_the_manifests_exist():
    assert len(MANIFESTS) >= 20, "only %d exercise manifest(s) found" % len(MANIFESTS)


def test_the_batch_gate_disagreement_is_exactly_the_pinned_one():
    report = run_verify(MANIFESTS)
    false_reds, genuine = split_disagreements(report, COVERAGE_ROWS)
    assert report["targets"] == PINNED_TARGETS, \
        "targets moved: %d (pinned %d)" % (report["targets"], PINNED_TARGETS)
    assert report["passed"] == PINNED_PASS, \
        "passed moved: %d (pinned %d)" % (report["passed"], PINNED_PASS)
    assert len(false_reds) == PINNED_FALSE_REDS, (
        "the number of false reds moved: %d (pinned %d).\n"
        "If tools/verify_coverage_batch.py was fixed to judge the declared channel, "
        "this should become 0 - update the pin and the docstring deliberately.\n"
        "first few now: %s" % (len(false_reds), PINNED_FALSE_REDS, false_reds[:5]))
    assert set(genuine) == set(PINNED_GENUINE), \
        "the genuinely-short set moved: %s (pinned %s)" % (genuine, sorted(PINNED_GENUINE))


def test_every_false_red_is_an_editor_state_channel_tool():
    """The disagreement is fully explained: it is the channel!=pixel/file class."""
    report = run_verify(MANIFESTS)
    false_reds, _ = split_disagreements(report, COVERAGE_ROWS)
    channels = {t: COVERAGE_ROWS[t].get("evidence_channel") for t in false_reds}
    unexpected = {t: c for t, c in channels.items() if c != "editor_state"}
    assert not unexpected, (
        "false reds outside the editor_state channel would NOT be explained by the "
        "legacy rule: %s" % json.dumps(unexpected, ensure_ascii=False))


def main():
    cases = []
    cases.append(("the ledger is internally consistent",
                  check_ledger_internal(COVERAGE_DOC) == [],
                  check_ledger_internal(COVERAGE_DOC)[:2]))
    cases.append(("the manifests exist", len(MANIFESTS) >= 20, len(MANIFESTS)))
    report = run_verify(MANIFESTS)
    false_reds, genuine = split_disagreements(report, COVERAGE_ROWS)
    channels = {t: COVERAGE_ROWS[t].get("evidence_channel") for t in false_reds}
    unexpected = {t: c for t, c in channels.items() if c != "editor_state"}
    cases.append(("targets/pass match the pin",
                  report["targets"] == PINNED_TARGETS and report["passed"] == PINNED_PASS,
                  {"targets": report["targets"], "pass": report["passed"]}))
    cases.append(("false reds of the legacy batch rule match the pin",
                  len(false_reds) == PINNED_FALSE_REDS,
                  {"false_reds": len(false_reds), "first": false_reds[:3]}))
    cases.append(("every false red is an editor_state-channel tool",
                  not unexpected, unexpected))
    cases.append(("the genuinely-short set matches the pin",
                  set(genuine) == set(PINNED_GENUINE), genuine))
    failed = [c for c in cases if not c[1]]
    for ok, name, detail in cases:
        print("%s  %s" % ("ok  " if ok else "FAIL", name))
        if not ok:
            print("      detail: %s" % (detail,))
    print("\n%d/%d checks passed" % (len(cases) - len(failed), len(cases)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
