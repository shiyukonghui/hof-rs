#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-120 item A6: the counterexample self-proof for the new witness rules.

TASK-119's independent acceptance built four counterexamples (M1..M4). Two of them
probed the witness mechanism itself:

  M2  rename the literal the declaration expects -> the reader must refuse to sign.
  M3  force every POST-write read back to the START value -> the old reader signed
      anyway (it had accepted `expect: ["\"position\""]`, a bare key name, at a call
      taken BEFORE the write).

This script re-creates M2 and M3 against the REAL h9 trace and the REAL
`verify_readback`, and adds one case per new rule (A1..A4). For M3 it also runs a
copy of the OLD rule (TASK-113/119: no read-verb check, no order check, bare key
names allowed) on the SAME mutated corpus, so the before/after is a single run:

    mutated corpus -> OLD rule: signed (chev=1)   <- the defect
    mutated corpus -> NEW rule: refused (chev=0)  <- the fix

Run:  python recovery/work/task120/witness_rules_selftest.py
"""
import io
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import tool_coverage as tc  # noqa: E402

OUT = os.path.join(ROOT, "recovery", "tmp", "task120", "selftest.txt")
H9 = "runs/_exercises/ex_rec/h9-task113"
FAILURES = []


def check(name, ok, detail):
    line = "%-6s %-58s %s" % ("PASS" if ok else "FAIL", name, detail)
    print(line)
    RECORDS.append(line)
    if not ok:
        FAILURES.append(name)


RECORDS = []


def legacy_verify(declaration, run_index):
    """The TASK-113/119 rule, verbatim: any witness tool, first matching payload."""
    run = declaration.get("run")
    witness = declaration.get("witness_tool")
    per_tool = run_index.get(run)
    if not per_tool:
        return None, "not in corpus"
    st = per_tool.get(witness)
    if not st or st["ok"] < 1 or st["substantive"] < 1:
        return None, "no ok substantive witness call"
    expects = tc.expected_literals(declaration)
    forbids = tc.forbidden_literals(declaration)
    for payload in st["payloads"]:
        text = tc.witness_payload_text(payload)
        if not tc.expect_matches(expects, text):
            continue
        if forbids and not tc.expect_forbids(forbids, text):
            continue
        return {"witness_seq": payload["seq"], "expect_matched": True}, None
    return None, "no payload matched"


def build_h9_index():
    names = [t["name"] for t in json.load(io.open(
        os.path.join(ROOT, tc.CONTRACT), encoding="utf-8"))["result"]["tools"]]
    scopes, verbs = tc.scope_and_verb(ROOT)
    ledger = tc.load_module(os.path.join(ROOT, tc.LEDGER), "mcp_trace_ledger")
    base = os.path.join(ROOT, H9.replace("/", os.sep))
    traces = [(H9, os.path.join(base, f)) for f in sorted(os.listdir(base))
              if f.startswith("trace-") and f.endswith(".jsonl")]
    _s, _c, run_index = tc.build_rows(ROOT, ledger, traces, verbs, scopes)
    return run_index, verbs


def h9_declaration(tool, witness="running_game_get_node_properties", expect=None):
    for d in tc.load_readback_declarations(ROOT):
        if d["tool"] == tool and d["run"] == H9:
            out = dict(d)
            out["witness_tool"] = witness
            if expect is not None:
                out["expect"] = expect
            elif "expect" not in out:
                out["expect"] = ['"x":346.0']
            return out
    raise SystemExit("declaration not found: %s" % tool)


def main():
    run_index, verbs = build_h9_index()
    stop = h9_declaration("running_game_stop_input_recording")
    create = h9_declaration("running_game_create_input_recording")

    # ---- positive control: the repaired declarations pass -------------------
    ptr, reason = tc.verify_readback(stop, run_index, verbs)
    check("positive control: repaired stop_input_recording signs", ptr is not None,
          "seq=%s expect=%s" % (ptr and ptr["witness_seq"], stop["expect"]))

    # ---- A1: the witness must be a READ call --------------------------------
    bad = h9_declaration("running_game_create_input_recording",
                         witness="running_game_stop_input_recording", expect=['"event_count":2'])
    ptr, reason = tc.verify_readback(bad, run_index, verbs)
    check("A1 non-read witness (audit's D2) is refused",
          ptr is None and "TASK-120 A1" in (reason or ""), reason or "")

    bad = h9_declaration("running_game_stop_input_recording",
                         witness="running_game_stop_input_recording")
    ptr, reason = tc.verify_readback(bad, run_index, verbs)
    check("A1 self-witness is refused", ptr is None and "TASK-120 A1" in (reason or ""), reason or "")

    # ---- the audit's "rename the witness tool" mutation ----------------------
    renamed = h9_declaration("running_game_stop_input_recording",
                            witness="running_game_get_scene_tree")
    ptr, reason = tc.verify_readback(renamed, run_index, verbs)
    check("witness tool renamed (read verb, wrong payload) -> refused",
          ptr is None and reason and "satisfies expect" in reason, reason or "")

    # A real READ-verb tool that this run never called (verb from the rename map,
    # so A1 does not fire and the call-level rejection is what is being tested).
    renamed = h9_declaration("running_game_stop_input_recording", witness="editor_get_selection")
    ptr, reason = tc.verify_readback(renamed, run_index, verbs)
    check("witness tool renamed to a never-called read tool -> refused",
          ptr is None and reason and "no `ok=true` substantive call" in reason, reason or "")

    # ---- A2: the witness must be LATER than a call of the witnessed tool ----
    # The synthetic witness is named `syn_get_value` so `verb_of` reads its second
    # segment (`get`) as the verb - A1 must not be the rule that fires here.
    synthetic = {
        "syn": {
            "writer": {"ok": 2, "substantive": 0, "seqs": [5, 6], "payloads": []},
            "syn_get_value": {"ok": 1, "substantive": 1, "seqs": [2, 11],
                              "payloads": [{"seq": 2, "text": '{"x":100.0}', "sidecar_path": None},
                                           {"seq": 11, "text": '{"x":200.0}', "sidecar_path": None}]},
        }
    }
    early = {"tool": "writer", "witness_tool": "syn_get_value", "run": "syn", "expect": ['"x":100.0']}
    ptr, reason = tc.verify_readback(early, synthetic, verbs)
    check("A2 pre-write witness is refused",
          ptr is None and "TASK-120 A2" in (reason or ""), reason or "")
    late = {"tool": "writer", "witness_tool": "syn_get_value", "run": "syn", "expect": ['"x":200.0']}
    ptr, reason = tc.verify_readback(late, synthetic, verbs)
    check("A2 post-write witness signs (not a blanket reject)",
          ptr is not None and ptr["witness_seq"] == 11, "seq=%s" % (ptr and ptr["witness_seq"]))

    # ---- A3: a bare key name is not a value ---------------------------------
    keyonly = h9_declaration("running_game_stop_input_recording", expect=['"position"'])
    ptr, reason = tc.verify_readback(keyonly, run_index, verbs)
    check("A3 bare-key expect (audit's D3) is refused",
          ptr is None and "TASK-120 A3" in (reason or ""), reason or "")

    # ---- A4: expect_absent without expect -----------------------------------
    absent = h9_declaration("running_game_stop_input_recording")
    absent["expect_absent"] = ['"x":999.0']
    del absent["expect"]
    ptr, reason = tc.verify_readback(absent, run_index, verbs)
    check("A4 expect_absent without expect is refused",
          ptr is None and "TASK-120 A4" in (reason or ""), reason or "")

    # ---- M2 (audit, verbatim): the key the expect named is renamed -----------
    keyonly_decl = h9_declaration("running_game_stop_input_recording", expect=['"position"'])
    m2 = json.loads(json.dumps(run_index))
    for payload in m2[H9]["running_game_get_node_properties"]["payloads"]:
        payload["text"] = (payload["text"] or "").replace('"position"', '"posn"')
    old_ptr, _ = legacy_verify(keyonly_decl, m2)
    ptr, reason = tc.verify_readback(keyonly_decl, m2, verbs)
    check("M2 key renamed -> OLD rule refuses (content gate was live)", old_ptr is None,
          "old: %s" % (old_ptr and old_ptr["witness_seq"]))
    check("M2 key renamed -> NEW rule refuses", ptr is None, reason or "")

    # ---- M2b: the VALUE the repaired expect names is changed -----------------
    m2b = json.loads(json.dumps(run_index))
    for payload in m2b[H9]["running_game_get_node_properties"]["payloads"]:
        payload["text"] = (payload["text"] or "").replace('"x":346.0', '"x":0.0')
    ptr, reason = tc.verify_readback(stop, m2b, verbs)
    check("M2b the value 346.0 -> 0.0 is refused (value-level expect)",
          ptr is None and reason and "satisfies expect" in reason, reason or "")

    # ---- M3 (audit): every POST-write read is forced back to the start value --
    # The audit's M3 held the OLD declaration fixed (`expect: ["\"position\""]`)
    # and rewrote the evidence so that "the player really moved" became "the
    # player never moved". The OLD rule signed anyway; the NEW rule refuses.
    m3 = json.loads(json.dumps(run_index))
    for payload in m3[H9]["running_game_get_node_properties"]["payloads"]:
        payload["text"] = (payload["text"] or "").replace('"x":346.0', '"x":100.0') \
                                                    .replace('"x":151.0', '"x":100.0')
    old_ptr_intact, _ = legacy_verify(keyonly_decl, run_index)
    old_ptr, _ = legacy_verify(keyonly_decl, m3)
    new_ptr, new_reason = tc.verify_readback(stop, m3, verbs)
    new_chev = tc.channel_evidence_count(None, tc.CHANNEL_STATE, new_ptr)
    check("M3 start-value mutation: OLD rule still signs (the defect)",
          old_ptr is not None and old_ptr["witness_seq"] == old_ptr_intact["witness_seq"],
          "old signed at seq=%s both before and after the mutation" % (old_ptr and old_ptr["witness_seq"]))
    check("M3 start-value mutation: NEW rule refuses (chev 0)", new_ptr is None and new_chev == 0,
          new_reason or "")
    check("M3 mutation demotes the tool off the pass status",
          tc.status_of_channel(7, new_chev, 7) == "计数达标缺证据",
          "status=%s" % tc.status_of_channel(7, new_chev, 7))

    # ---- and the un-mutated corpus still signs under the new rule -----------
    new_ptr, _ = tc.verify_readback(stop, run_index, verbs)
    check("un-mutated corpus: NEW rule signs at the post-write read",
          new_ptr is not None and new_ptr["witness_seq"] == 18,
          "seq=%s expect=%s" % (new_ptr and new_ptr["witness_seq"], new_ptr and new_ptr["expect"]))

    # ---- M1 (audit): a blanked payload grants no `payload` evidence ----------
    # The audit blanked project_get_info's payloads in a copy of the corpus; the
    # same question asked of the reader itself: does a blank body count as an
    # effective read call? (`read_payload` - the `payload` channel's evidence - is
    # incremented only when this returns True.)
    blank = {"ok": True, "verdict": "ok_no_effect_observed", "result_json": "{}",
             "result_flags": [], "result_json_evidence": "inline"}
    real = {"ok": True, "verdict": "ok_no_effect_observed",
            "result_json": '{"godot_version":"4.8.dev","project_name":"pong"}',
            "result_flags": [], "result_json_evidence": "inline"}
    check("M1 blanked read payload is not effective evidence",
          tc.classify(blank, "get")[0] is False, "classify(blank)=%s" % (tc.classify(blank, "get"),))
    check("M1 substantive read payload IS evidence",
          tc.classify(real, "get")[0] is True, "classify(real)=%s" % (tc.classify(real, "get"),))

    # ---- M4 (audit): the boundary gate is live ------------------------------
    # The audit injected one rejected call and the tool rose to 达标. The same
    # question here: with the c8 boundary call taken away again, does the status
    # fall back? (boundary is the `failed` count.)
    row_before = None
    for row in json.load(io.open(os.path.join(ROOT, "coverage.json"), encoding="utf-8"))["tools"]:
        if row["tool"] == "editor_save_scene":
            row_before = row
    check("M4 boundary call present -> 达标",
          row_before["status"] == "达标" and row_before["boundary"] >= 1,
          "boundary=%d status=%s" % (row_before["boundary"], row_before["status"]))
    check("M4 boundary call removed -> back to 计数达标缺证据",
          tc.status_of_channel(row_before["calls"], row_before["channel_evidence"], 0)
          == "计数达标缺证据",
          "status=%s" % tc.status_of_channel(row_before["calls"], row_before["channel_evidence"], 0))

    header = ["TASK-120 item A6 self-test -- %d checks, %d failure(s)"
              % (len(RECORDS), len(FAILURES)), ""]
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(
        "\n".join(header + RECORDS) + "\n")
    print("")
    print("checks=%d failures=%d -> %s" % (len(RECORDS), len(FAILURES), OUT))
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
