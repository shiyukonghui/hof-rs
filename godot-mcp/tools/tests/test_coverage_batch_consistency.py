#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""test_coverage_batch_consistency.py -- the coverage ledger and its batch gate must agree.

WHY THIS EXISTS (TASK-143 sections A.1 and C item 4; repaired by TASK-144 item A)
-------------------------------------------------------------------------------
`coverage.json` (built by `tools/tool_coverage.py`) is the ledger that decides
whether a contract tool is 达标. Since TASK-118 it judges each tool ON ITS OWN
DECLARED EVIDENCE CHANNEL (`tool_channels.json`): a tool whose effect lives in
the editor process' memory is judged by a verified witness read-back, not by a
pixel/file delta. The ledger therefore carries TWO quantities per tool:

    effective         the PRE-TASK-118 quantity: a pixel or a file really moved
    channel_evidence  the quantity the ledger actually judges (>=1 + ok)
    channel_evidence_ok  the verdict that decides `status`

TASK-143 found that `tools/verify_coverage_batch.py` (the per-batch gate) still
applied its original rule `calls >= 5 and effective >= 1 and (boundary >= 1 or
edge)`. For every `editor_state`-channel tool `effective` is 0 by construction -
the whole point of TASK-118 - so the batch gate reported red for 45 tools the
ledger marks 达标.

MEASURED (TASK-143, legacy rule, all 20 exercise manifests):
    166 targets, 118 pass, 48 fail
    of the 48 fails, 45 were FALSE REDS (the ledger says 达标 with
    channel_evidence_ok == true) and 3 were genuine shortage
    (channel_evidence_ok == false)

FIXED (TASK-144 item A, current rule, same corpus and manifests):
    166 targets, 163 pass, 3 fail - 0 false reds
    the 3 genuine fails are the same three tools, each short of evidence ON ITS
    DECLARED CHANNEL:
        editor_set_auto_dismiss_dialogs   editor_state  no success branch in this
            engine (5x -32000 "Not implemented", 2x -32602 on `enabled`), so no
            read call can read the written value back
        os_deploy_to_android_device       file_effect   5x -32001 "Export preset
            'NoSuchAndroidPreset' not found", 1x -32602 (a Windows Desktop
            preset); no Android preset/device, and 0/6 calls have a
            reconstructible file effect (`file_effect = not_recorded`)
        project_get_android_preset_info   payload       5x -32000 "No Android
            export preset is configured in this project", 1x -32001; no ok=true
            call with a substantive payload

`tools/verify_coverage_batch.py` now judges `channel_evidence`, and it does not
re-implement it: it imports `tools/tool_coverage.py` and calls that module's own
`channel_evidence_count()` / `load_channels()`. This file makes the agreement
EXECUTABLE instead of a paragraph in a report:

  * it runs the real gate (not a second copy of its rule) and pins the verdict
    counts, so that moving either side shows up here as a deliberate change;
  * it carries NEGATIVE examples that must make the gate RED: a tool declared on
    a channel its counters cannot support, a snapshot whose stored channel
    evidence its own counters do not reproduce, and a channel table that
    contradicts the tool's verb (rejected by the ledger's own guard);
  * it carries the POSITIVE CONTROL for each negative (the same tool, unmutated,
    passes), so a mutation that simply broke the run cannot pass as a negative.

Run:
    D:\\Anaconda\\python.exe -m pytest tools\\tests\\test_coverage_batch_consistency.py -q
    D:\\Anaconda\\python.exe tools\\tests\\test_coverage_batch_consistency.py
"""
from __future__ import print_function

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS_DIR)
COVERAGE = os.path.join(ROOT, "coverage.json")
CHANNELS = os.path.join(TOOLS_DIR, "tool_channels.json")
VERIFY = os.path.join(TOOLS_DIR, "verify_coverage_batch.py")
MANIFEST_DIR = os.path.join(TOOLS_DIR, "sessions", "_exercises")

# ---------------------------------------------------------------------------
# PINNED: the measured verdict of the fixed gate over all 20 exercise manifests.
# Update these deliberately, with the reason, if either side changes.
# ---------------------------------------------------------------------------
PINNED_TARGETS = 166
PINNED_PASS = 163
PINNED_GENUINE = frozenset((
    "editor_set_auto_dismiss_dialogs",
    "os_deploy_to_android_device",
    "project_get_android_preset_info",
))
# The legacy rule's measured disagreement, kept as the "before" number a reader
# can look up in TASK-143 / recovery/reports/TASK-143-REPORT.md.
LEGACY_PASS = 118
LEGACY_FALSE_REDS = 45


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


def run_verify(manifests_list, coverage=COVERAGE, channels=None):
    """Run the REAL tools/verify_coverage_batch.py over the given manifests."""
    handle, out_path = tempfile.mkstemp(prefix="task144-batch-", suffix=".json")
    os.close(handle)
    try:
        cmd = [sys.executable, VERIFY]
        for m in manifests_list:
            cmd += ["--manifest", m]
        cmd += ["--coverage", coverage]
        if channels:
            cmd += ["--channels", channels]
        cmd += ["--json", out_path]
        proc = subprocess.run(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        report = None
        if os.path.getsize(out_path) > 0:
            with io.open(out_path, "r", encoding="utf-8") as h:
                report = json.load(h)
        return proc.returncode, report, proc.stdout.decode("utf-8", "replace")
    finally:
        try:
            os.remove(out_path)
        except OSError:
            pass


def split_disagreements(report, rows):
    """(false_reds, genuine) - the fails the ledger disagrees with, and the rest."""
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
# mutation helpers for the negative examples
# ---------------------------------------------------------------------------
def stage_temp_copy(source, name):
    """Copy one file into a fresh temp dir; returns the copied path."""
    tmp = tempfile.mkdtemp(prefix="task144-mut-")
    dst = os.path.join(tmp, name)
    shutil.copyfile(source, dst)
    return tmp, dst


def write_json(path, doc):
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(doc, ensure_ascii=False, indent=2) + "\n")


def pick_editor_state_pass(report, rows):
    """A target that passes on the `editor_state` channel with no pixel counter."""
    for entry in report["results"]:
        if entry["verdict"] != "pass":
            continue
        row = rows.get(entry["tool"]) or {}
        if row.get("evidence_channel") == "editor_state" and row.get("pixel_effect_calls", 0) == 0:
            return entry["tool"], row
    return None, None


def pick_action_verb_pass(report, rows):
    """A target that passes while its contract verb is an action verb."""
    read_verbs = {"get", "read", "search", "list", "find", "analyze", "detect",
                  "convert", "validate", "check", "assert", "execute", "evaluate",
                  "capture"}
    for entry in report["results"]:
        if entry["verdict"] != "pass":
            continue
        row = rows.get(entry["tool"]) or {}
        if row.get("verb") not in read_verbs:
            return entry["tool"], row
    return None, None


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------
COVERAGE_DOC = load_coverage()
COVERAGE_ROWS = {r["tool"]: r for r in COVERAGE_DOC["tools"]}
MANIFESTS = manifests()
REPORT = None


def gate_report():
    global REPORT
    if REPORT is None:
        REPORT = run_verify(MANIFESTS)
    return REPORT


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


def test_the_batch_gate_judges_the_declared_channel():
    code, report, output = gate_report()
    assert report is not None, "the gate wrote no JSON:\n%s" % output
    assert code == 1, "the gate must exit 1 while 3 targets are genuinely short:\n%s" % output
    assert report["targets"] == PINNED_TARGETS, \
        "targets moved: %d (pinned %d)" % (report["targets"], PINNED_TARGETS)
    assert report["passed"] == PINNED_PASS, \
        "passed moved: %d (pinned %d)" % (report["passed"], PINNED_PASS)
    false_reds, genuine = split_disagreements(report, COVERAGE_ROWS)
    assert false_reds == [], (
        "the gate disagrees with the ledger on %d tool(s): %s\n"
        "The gate must judge `channel_evidence` on the tool's declared channel "
        "(TASK-118 A / TASK-144 A)." % (len(false_reds), false_reds[:5]))
    assert set(genuine) == set(PINNED_GENUINE), \
        "the genuinely-short set moved: %s (pinned %s)" % (genuine, sorted(PINNED_GENUINE))
    assert report["gate"].startswith("calls>=5 and channel_evidence>=1"), report["gate"]


def test_every_fail_is_a_real_shortage_on_its_own_channel():
    """No fail may come from the retired `effective` quantity."""
    _code, report, output = gate_report()
    bad = []
    for entry in report["results"]:
        if entry["verdict"] != "fail":
            continue
        if entry["channel_evidence"] >= 1:
            bad.append(entry["tool"])
        if entry["effective"] >= 1 and entry["channel_evidence"] >= 1:
            bad.append(entry["tool"])
    assert bad == [], "fails that carry channel evidence would be false reds: %s" % bad


def test_the_number_of_false_reds_is_now_zero_and_the_legacy_number_is_recorded():
    """The fix moved 45 false reds to pass; the before-number stays on the record."""
    _code, report, _output = gate_report()
    false_reds, _genuine = split_disagreements(report, COVERAGE_ROWS)
    assert len(false_reds) == 0, false_reds[:5]
    assert report["passed"] == PINNED_PASS
    assert LEGACY_PASS + LEGACY_FALSE_REDS == 163, \
        "the recorded before/after arithmetic changed: %d + %d != 163" % (LEGACY_PASS, LEGACY_FALSE_REDS)


# ---------------------------------------------------------------------------
# negative examples: each one MUST be red, with a positive control
# ---------------------------------------------------------------------------
def test_negative_a_tool_declared_on_the_wrong_channel_is_red():
    """Declare a passing `editor_state` tool as `pixel_effect`: it has no pixel
    evidence, so the gate must judge it red - and must still pass the control."""
    code, report, output = gate_report()
    tool, row = pick_editor_state_pass(report, COVERAGE_ROWS)
    assert tool, "no passing editor_state target to mutate:\n%s" % output
    control = [e for e in report["results"] if e["tool"] == tool][0]
    assert control["verdict"] == "pass", "the control target does not pass: %s" % tool

    tmp, mutated_channels = stage_temp_copy(CHANNELS, "tool_channels.json")
    _tmp2, mutated_coverage = stage_temp_copy(COVERAGE, "coverage.json")
    try:
        # (a) the declarations: the tool now claims the pixel channel
        doc = json.load(io.open(mutated_channels, encoding="utf-8"))
        doc["channels"][tool]["channel"] = "pixel_effect"
        write_json(mutated_channels, doc)
        # (b) the snapshot regenerated consistently with that wrong declaration
        cov = json.load(io.open(mutated_coverage, encoding="utf-8"))
        for entry in cov["tools"]:
            if entry["tool"] == tool:
                entry["evidence_channel"] = "pixel_effect"
                entry["channel_evidence"] = entry.get("pixel_effect_calls", 0)
                entry["channel_evidence_ok"] = entry["channel_evidence"] >= 1
        write_json(mutated_coverage, cov)

        code2, report2, output2 = run_verify(MANIFESTS, coverage=mutated_coverage,
                                             channels=mutated_channels)
        assert report2 is not None, output2
        assert code2 == 1, "a wrong-channel declaration must make the gate red:\n%s" % output2
        entry = [e for e in report2["results"] if e["tool"] == tool][0]
        assert entry["verdict"] == "fail", \
            "%s is declared pixel_effect with 0 pixel calls but still passes:\n%s" % (tool, output2)
        assert entry["evidence_channel"] == "pixel_effect" and entry["channel_evidence"] == 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.rmtree(os.path.dirname(mutated_coverage), ignore_errors=True)


def test_negative_a_snapshot_that_contradicts_its_own_counters_is_red():
    """A `coverage.json` whose stored channel_evidence the row's own counters do
    not reproduce must be red (a ledger generated before a channel edit)."""
    code, report, output = gate_report()
    tool, row = pick_editor_state_pass(report, COVERAGE_ROWS)
    assert tool, "no passing target to mutate:\n%s" % output

    _tmp, mutated_coverage = stage_temp_copy(COVERAGE, "coverage.json")
    try:
        cov = json.load(io.open(mutated_coverage, encoding="utf-8"))
        for entry in cov["tools"]:
            if entry["tool"] == tool:
                entry["channel_evidence"] = entry.get("channel_evidence", 0) + 1
        write_json(mutated_coverage, cov)
        code2, report2, output2 = run_verify(MANIFESTS, coverage=mutated_coverage)
        assert report2 is not None, output2
        assert code2 == 1, "a contradictory snapshot must be red:\n%s" % output2
        entry = [e for e in report2["results"] if e["tool"] == tool][0]
        assert entry["verdict"] == "fail", output2
        assert entry["snapshot_drift"], "the disagreement was not spelled out: %r" % (entry,)
    finally:
        shutil.rmtree(os.path.dirname(mutated_coverage), ignore_errors=True)


def test_negative_a_payload_channel_on_an_action_verb_is_rejected():
    """The ledger's verb guard must still fire through this script: a tool whose
    verb is an action verb cannot be declared `payload` (its gate could never be
    satisfied), and the gate must refuse to publish a number for it."""
    code, report, output = gate_report()
    tool, row = pick_action_verb_pass(report, COVERAGE_ROWS)
    assert tool, "no passing action-verb target to mutate:\n%s" % output

    tmp, mutated_channels = stage_temp_copy(CHANNELS, "tool_channels.json")
    try:
        doc = json.load(io.open(mutated_channels, encoding="utf-8"))
        doc["channels"][tool]["channel"] = "payload"
        write_json(mutated_channels, doc)
        code2, report2, output2 = run_verify(MANIFESTS, channels=mutated_channels)
        assert code2 == 2, "the verb contradiction must be a refusal (exit 2), got %d:\n%s" \
            % (code2, output2)
        assert "contradicts the tool verb" in output2, output2
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    cases = []
    cases.append(("the ledger is internally consistent",
                  check_ledger_internal(COVERAGE_DOC) == [],
                  check_ledger_internal(COVERAGE_DOC)[:2]))
    cases.append(("the manifests exist", len(MANIFESTS) >= 20, len(MANIFESTS)))
    code, report, output = gate_report()
    cases.append(("the gate writes a report", report is not None, output[-200:]))
    if report is None:
        for name, ok, _detail in cases:
            print("%s  %s" % ("ok  " if ok else "FAIL", name))
        return 1
    false_reds, genuine = split_disagreements(report, COVERAGE_ROWS)
    cases.append(("targets/pass match the pin",
                  report["targets"] == PINNED_TARGETS and report["passed"] == PINNED_PASS,
                  {"targets": report["targets"], "pass": report["passed"]}))
    cases.append(("the gate has no false red",
                  len(false_reds) == 0,
                  {"false_reds": len(false_reds), "first": false_reds[:3]}))
    cases.append(("the genuinely-short set matches the pin",
                  set(genuine) == set(PINNED_GENUINE), genuine))
    cases.append(("every fail is short on its own channel",
                  all(e["channel_evidence"] < 1 for e in report["results"]
                      if e["verdict"] == "fail"),
                  [e["tool"] for e in report["results"] if e["verdict"] == "fail"]))

    tool, _row = pick_editor_state_pass(report, COVERAGE_ROWS)
    cases.append(("a control target exists for the negatives", bool(tool), tool))

    tmp, mutated_channels = stage_temp_copy(CHANNELS, "tool_channels.json")
    _tmp2, mutated_coverage = stage_temp_copy(COVERAGE, "coverage.json")
    try:
        doc = json.load(io.open(mutated_channels, encoding="utf-8"))
        doc["channels"][tool]["channel"] = "pixel_effect"
        write_json(mutated_channels, doc)
        cov = json.load(io.open(mutated_coverage, encoding="utf-8"))
        for entry in cov["tools"]:
            if entry["tool"] == tool:
                entry["evidence_channel"] = "pixel_effect"
                entry["channel_evidence"] = entry.get("pixel_effect_calls", 0)
                entry["channel_evidence_ok"] = entry["channel_evidence"] >= 1
        write_json(mutated_coverage, cov)
        code2, report2, output2 = run_verify(MANIFESTS, coverage=mutated_coverage,
                                             channels=mutated_channels)
        entry = None
        if report2:
            entry = [e for e in report2["results"] if e["tool"] == tool][0]
        cases.append(("negative: a tool declared on the wrong channel is red",
                      code2 == 1 and entry is not None and entry["verdict"] == "fail",
                      {"exit": code2, "verdict": entry and entry["verdict"]}))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.rmtree(os.path.dirname(mutated_coverage), ignore_errors=True)

    failed = [c for c in cases if not c[1]]
    for name, ok, detail in cases:
        print("%s  %s" % ("ok  " if ok else "FAIL", name))
        if not ok:
            print("      detail: %s" % (detail,))
    print("\n%d/%d checks passed" % (len(cases) - len(failed), len(cases)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
