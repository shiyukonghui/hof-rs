#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""test_playjev_agent.py -- the PlayJev backend against a dumb, validating server (TASK-127).

What is proven here, with no weights, no GPU and the standard library only:

  P7-ish  the `playjev` backend builds a request the DEPLOYED serve.py would accept
          (`state.frames` with a real base64 PNG, every question `type: "choice"`,
          >= 2 options, one frame + N questions in one request) and maps the answers
          back to the same action dict the other backends return;
  P9      `abstain` is explicit: a server-declared `abstain`, a MISSING answer and an
          unusable answer all become abstain=true, the action degrades to `wait`, and
          the threshold verdict becomes `pass: null` -- never a pass;
  --      the traps are ABSENCES, and they are asserted as such: no top-level `image`
          field, no `noul`/`score` question type, no text state -- and the dumb server
          (which mirrors serve.py's own checks) rejects each of them, so the client
          cannot silently drift back to the Jev shape;
  --      `jev`, `openai` and `scripted` still construct and still degrade safely.

Run:

    python tools\\playtest_agent.py --probe-playjev
    python tools\\tests\\test_playjev_agent.py

Evidence is written to `runs\\playability\\agent-probe-playjev.json` (via Python UTF-8,
never a shell redirect) when `--evidence` is given.
"""

from __future__ import print_function

import base64
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from playtest_agent import (  # noqa: E402
    PlayJevAgent, JevAgent, OpenAIAgent, ScriptedAgent, build_agent,
    PLAYJEV_DEFAULT_BASE_URL, PLAYJEV_DECISION_PATHS, PLAYJEV_MIN_OPTIONS,
    PLAYJEV_MAX_OPTIONS, PLAYJEV_TRUE,
)
from playjev_dumb_server import (  # noqa: E402
    DumbPlayJevServer, validate_request, canonical_answers,
)

# a real 2x2 PNG, so the base64 the client sends decodes to actual PNG bytes
PNG_2X2 = base64.b64decode(
    b"iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAYAAACZgbYnAAAAFklEQVR4nGP8z8DAwMDA"
    b"xMDAwMAAAA0AAf8B2S0AAAAASUVORK5CYII=")

GAME_FRAME = os.path.join(
    os.path.dirname(TOOLS), "runs", "playability-exe", "pong", "frames", "20_post1.png")

GOAL = {"game": "pong", "objective": "make the score advance",
        "keys": ["W", "S"],
        "actions": {"pong_left_up": ["W"], "pong_left_down": ["S"],
                    "pong_serve": ["SPACE"]}}


def _frame(path):
    return {"index": 0, "path": path, "width": 2, "height": 2, "window": [2, 2],
            "declared": [2, 2], "content_fraction": 1.0, "bbox": [0, 0, 2, 2],
            "changed_pixels_vs_prev": 0, "sha256": "probe"}


def _tmp_png():
    d = tempfile.mkdtemp(prefix="playjev_probe_")
    p = os.path.join(d, "frame_00.png")
    with open(p, "wb") as fh:
        fh.write(PNG_2X2)
    return p


def _agent(server, **opts):
    o = {"base_url": server.url, "timeout": 20}
    o.update(opts)
    return PlayJevAgent("pong", GOAL["objective"], o)


def _server_case(mode, **kw):
    srv = DumbPlayJevServer(port=0, mode=mode, **kw).start()
    return srv


def run_all(verbose=True, argv=None, evidence_path=None):
    argv = list(argv or [])
    checks = {}
    ev = {}
    tmp_png = _tmp_png()
    frames = [_frame(tmp_png)]
    real_frames = [_frame(GAME_FRAME)] if os.path.isfile(GAME_FRAME) else []
    if real_frames:
        frames.extend(real_frames)

    # ---- 1. the happy path -------------------------------------------------
    ok_srv = DumbPlayJevServer(port=0, mode="ok").start()
    try:
        ag = _agent(ok_srv)
        health = ag.check_health()
        action = ag.decide(frames, {}, GOAL)
        verdict = ag.judge(frames, {}, GOAL)
        report = ag.report()
        reqs = ok_srv.requests
        verrors = ok_srv.validation_errors
    finally:
        ok_srv.stop()

    ev["ok_mode"] = {"health": report["health"], "action": action, "verdict": verdict,
                     "request_count": len(reqs), "validation_errors": verrors,
                     "requests": reqs, "errors": report["errors"],
                     "calls": ag.calls}

    post = [r for r in reqs if r["method"] == "POST"]
    payload = post[-1]["payload"] if post else {}
    questions = payload.get("questions") or {}
    state = payload.get("state") or {}
    frame_urls = state.get("frames") or []

    checks["dumb_server_validates_clean"] = (len(verrors) == 0)
    checks["posts_to_v1_systemone"] = bool(post) and post[-1]["path"] == "/v1/systemone"
    checks["health_ok_true"] = (health.get("status") == 200
                                and health.get("json", {}).get("ok") is True
                                and health.get("json", {}).get("model") == "playjev-0.8b")
    checks["state_frames_is_one_data_url"] = (len(frame_urls) == 1
                                              and frame_urls[0].startswith(
                                                  "data:image/png;base64,"))
    checks["frame_decodes_to_png"] = bool(frame_urls) and base64.b64decode(
        frame_urls[0].split(",", 1)[1])[:8] == b"\x89PNG\r\n\x1a\n"
    checks["no_toplevel_image_field"] = "image" not in payload
    checks["one_image_many_questions"] = (len(frame_urls) == 1 and len(questions) >= 3)
    checks["all_questions_are_choice"] = bool(questions) and all(
        q.get("type") == "choice" for q in questions.values())
    checks["every_question_has_ge_2_options"] = bool(questions) and all(
        len(q.get("criteria") or []) >= PLAYJEV_MIN_OPTIONS for q in questions.values())
    checks["no_noul_or_score_question_type"] = all(
        q.get("type") not in ("noul", "score") for q in questions.values())
    checks["action_is_a_real_action"] = (isinstance(action, dict)
                                         and action.get("type") in ("key", "action", "wait", "done"))
    checks["action_probabilities_in_evidence"] = bool(
        ag.calls and ag.calls[-1].get("probability_tables"))
    checks["abstain_flag_recorded"] = (bool(ag.calls)
                                       and "abstain" in ag.calls[-1])
    checks["confidence_recorded"] = bool(ag.calls and ag.calls[-1].get("confidences"))
    checks["timing_recorded"] = bool(ag.calls and ag.calls[-1].get("timing"))
    # the canned numbers were chosen to pass the default thresholds
    checks["noul_p_true_from_yes_no_choice"] = bool(
        verdict["criteria"]) and all(
        (c["id"].startswith("score:") or c["value"] == 0.8)
        for c in verdict["criteria"])
    checks["score_is_expected_level_le_2"] = all(
        (not c["id"].startswith("score:")) or (c["value"] is not None and c["value"] < 2.0)
        for c in verdict["criteria"])
    checks["threshold_verdict_passes_on_ok"] = (verdict["pass"] is True
                                                and verdict["decidable"] is True)
    checks["judge_reuses_decide_evidence"] = (report["base_url"] == ok_srv.url)

    # ---- 2. the traps: the dumb server must REJECT the Jev shape -----------
    good_q = {"move": {"type": "choice",
                       "instructions": "pick one",
                       "criteria": {"a": "alpha", "b": "beta"}}}
    good_state = {"frames": ["data:image/png;base64,%s"
                             % base64.b64encode(PNG_2X2).decode("ascii")]}
    trap = {}
    # (a) a noul question -- legal on Jev, 400 on PlayJev
    trap["noul_question_rejected"] = [e for e in validate_request(
        {"model": "m", "state": good_state,
         "questions": {"q": {"type": "noul", "instructions": "x"}}})
        if e.get("status")]
    # (b) a score question
    trap["score_question_rejected"] = [e for e in validate_request(
        {"model": "m", "state": good_state,
         "questions": {"q": {"type": "score", "criteria": ["a", "b"]}}})
        if e.get("status")]
    # (c) a text state
    trap["text_state_rejected"] = [e for e in validate_request(
        {"model": "m", "state": "the game is running", "questions": good_q})
        if e.get("status")]
    # (d) the Jev top-level `image` field with no frames
    trap["toplevel_image_not_enough"] = [e for e in validate_request(
        {"model": "m", "state": good_state, "image": "data:image/png;base64,AAAA",
         "questions": good_q}) if e.get("status")]
    # (e) a single-option choice
    trap["single_option_rejected"] = [e for e in validate_request(
        {"model": "m", "state": good_state,
         "questions": {"q": {"type": "choice", "criteria": {"only": "one"}}}})
        if e.get("status")]
    # (f) a frame that is a string but not base64 -> 500, like serve.py
    trap["bad_base64_is_500"] = [e for e in validate_request(
        {"model": "m", "state": {"frames": ["not base64 !!!"]}, "questions": good_q})
        if e.get("status")]
    ev["protocol_traps"] = trap
    checks["server_rejects_noul_question"] = bool(trap["noul_question_rejected"])
    checks["server_rejects_score_question"] = bool(trap["score_question_rejected"])
    checks["server_rejects_text_state"] = bool(trap["text_state_rejected"])
    checks["server_rejects_single_option_choice"] = bool(trap["single_option_rejected"])
    checks["server_500_on_bad_base64"] = any(
        e["status"] == 500 for e in trap["bad_base64_is_500"])

    # ---- 3. abstain, declared and missing ----------------------------------
    abst_srv = DumbPlayJevServer(port=0, mode="abstain").start()
    try:
        ag_abst = _agent(abst_srv)
        act_abst = ag_abst.decide(frames, {}, GOAL)
        verdict_abst = ag_abst.threshold_verdict()
        calls_abst = ag_abst.calls[-1]
        abst_errors = ag_abst.errors
    finally:
        abst_srv.stop()
    ev["abstain_mode"] = {"action": act_abst, "verdict": verdict_abst,
                          "abstained_questions": calls_abst.get("abstained_questions"),
                          "abstain_reasons": calls_abst.get("abstain_reasons"),
                          "errors": abst_errors}
    checks["declared_abstain_seen"] = bool(calls_abst.get("abstained_questions"))
    checks["abstain_action_is_wait_not_success"] = (
        act_abst.get("type") == "wait" and "ABSTAIN" in (act_abst.get("why") or ""))
    checks["abstain_verdict_is_not_pass"] = (verdict_abst["pass"] is not True
                                             and verdict_abst["decidable"] is False)
    checks["abstain_recorded_as_error"] = any(
        e.get("kind") == "abstain" for e in abst_errors)

    # an abstain OUTSIDE the action question: the action stays usable, the VERDICT
    # still must not become a pass.
    absts_srv = DumbPlayJevServer(port=0, mode="abstain_score").start()
    try:
        ag_absts = _agent(absts_srv)
        act_absts = ag_absts.decide(frames, {}, GOAL)
        verdict_absts = ag_absts.threshold_verdict()
        calls_absts = ag_absts.calls[-1]
    finally:
        absts_srv.stop()
    ev["abstain_score_mode"] = {"action": act_absts, "verdict": verdict_absts,
                                "abstained_questions": calls_absts.get("abstained_questions"),
                                "abstain_reasons": calls_absts.get("abstain_reasons")}
    checks["score_only_abstain_keeps_action"] = (act_absts.get("type") in
                                                 ("action", "key", "wait", "done"))
    checks["score_only_abstain_is_not_a_pass"] = (verdict_absts["pass"] is not True
                                                  and verdict_absts["decidable"] is False)

    noans_srv = DumbPlayJevServer(port=0, mode="noanswer").start()
    try:
        ag_na = _agent(noans_srv)
        act_na = ag_na.decide(frames, {}, GOAL)
        verdict_na = ag_na.threshold_verdict()
        calls_na = ag_na.calls[-1]
    finally:
        noans_srv.stop()
    ev["noanswer_mode"] = {"action": act_na, "verdict": verdict_na,
                           "abstained_questions": calls_na.get("abstained_questions"),
                           "abstain_reasons": calls_na.get("abstain_reasons")}
    checks["missing_answer_is_abstain"] = bool(calls_na.get("abstained_questions"))
    checks["missing_answer_not_a_success"] = (act_na.get("type") == "wait")

    # ---- 4. a confidence threshold can turn a normal answer into an abstain --
    thr_srv = DumbPlayJevServer(port=0, mode="ok").start()
    try:
        ag_thr = _agent(thr_srv, abstain_min_confidence=1.01)  # impossible -> all abstain
        act_thr = ag_thr.decide(frames, {}, GOAL)
        verdict_thr = ag_thr.threshold_verdict()
        calls_thr = ag_thr.calls[-1]
    finally:
        thr_srv.stop()
    ev["confidence_abstain_mode"] = {"action": act_thr, "verdict": verdict_thr,
                                     "abstained_questions": calls_thr.get("abstained_questions"),
                                     "abstain_reasons": calls_thr.get("abstain_reasons")}
    checks["confidence_threshold_abstains"] = (verdict_thr["pass"] is not True
                                               and verdict_thr["decidable"] is False)

    # ---- 5. error / broken-body paths --------------------------------------
    inv_srv = DumbPlayJevServer(port=0, mode="invalid").start()
    try:
        ag_inv = _agent(inv_srv)
        act_inv = ag_inv.decide(frames, {}, GOAL)
        errs_inv = ag_inv.errors
    finally:
        inv_srv.stop()
    brk_srv = DumbPlayJevServer(port=0, mode="broken").start()
    try:
        ag_brk = _agent(brk_srv)
        act_brk = ag_brk.decide(frames, {}, GOAL)
        errs_brk = ag_brk.errors
    finally:
        brk_srv.stop()
    un_srv = DumbPlayJevServer(port=0, mode="unhealthy").start()
    try:
        ag_un = _agent(un_srv)
        act_un = ag_un.decide(frames, {}, GOAL)
        errs_un = ag_un.errors
        posted_un = [r for r in un_srv.requests if r["method"] == "POST"]
    finally:
        un_srv.stop()
    ev["error_paths"] = {"invalid_action": act_inv, "invalid_errors": errs_inv,
                         "broken_action": act_brk, "broken_errors": errs_brk,
                         "unhealthy_action": act_un, "unhealthy_errors": errs_un,
                         "unhealthy_posts": len(posted_un)}
    checks["http_400_reported"] = any(e.get("status") == 400 for e in errs_inv)
    checks["http_400_not_a_success"] = act_inv.get("type") == "wait"
    checks["broken_body_reported"] = any(e.get("kind") == "response" for e in errs_brk)
    checks["broken_body_not_a_success"] = act_brk.get("type") == "wait"
    checks["unhealthy_reported"] = any(e.get("kind") == "health" for e in errs_un)
    checks["unhealthy_no_post"] = (len(posted_un) == 0)

    # ---- 6. refusals that must happen BEFORE the wire ----------------------
    noimg = _agent(DumbPlayJevServer(port=0, mode="ok"), send_images=False)
    act_noimg = noimg.decide(frames, {}, GOAL)
    noframe = _agent(DumbPlayJevServer(port=0, mode="ok"))
    act_noframe = noframe.decide([], {}, GOAL)
    badpath = _agent(DumbPlayJevServer(port=0, mode="ok"),
                     decision_path="/v1/decision")
    act_badpath = badpath.decide(frames, {}, GOAL)
    manyopts = _agent(DumbPlayJevServer(port=0, mode="ok"),
                      score_criteria=[(str(i), "level %d" % i) for i in range(1, 30)])
    act_manyopts = manyopts.decide(frames, {}, GOAL)
    ev["pre_wire_refusals"] = {"no_images": act_noimg, "no_frame": act_noframe,
                               "jev_path": act_badpath, "too_many_options": act_manyopts,
                               "errors": noimg.errors + noframe.errors
                                         + badpath.errors + manyopts.errors}
    checks["send_images_false_refused"] = (act_noimg.get("type") == "wait"
                                           and bool(noimg.errors))
    checks["no_frame_refused"] = (act_noframe.get("type") == "wait"
                                  and bool(noframe.errors))
    checks["jev_decision_path_refused"] = (act_badpath.get("type") == "wait"
                                           and bool(badpath.errors))
    checks["over_26_options_refused"] = (act_manyopts.get("type") == "wait"
                                         and bool(manyopts.errors))

    # ---- 7. the other backends did not regress -----------------------------
    others = {}
    others["scripted"] = isinstance(build_agent("scripted"), ScriptedAgent)
    others["openai"] = isinstance(build_agent("openai"), OpenAIAgent)
    others["jev"] = isinstance(build_agent("jev"), JevAgent)
    others["playjev"] = isinstance(build_agent("playjev"), PlayJevAgent)
    others["playjev_default_port_is_8081"] = (
        build_agent("playjev").base_url == PLAYJEV_DEFAULT_BASE_URL
        and PLAYJEV_DEFAULT_BASE_URL.endswith(":8081"))
    try:
        build_agent("nope")
        others["unknown_backend_raises"] = False
    except ValueError as e:
        others["unknown_backend_raises"] = "playjev" in str(e)
    # a jev agent must still build its OLD text-shaped request (regression guard)
    try:
        j = build_agent("jev", "pong", "", {"base_url": "http://127.0.0.1:9"})
        _payload, meta = j.build_request([], {"digest": "x"}, GOAL, "action")
        others["jev_still_sends_text_state"] = ("image" not in _payload
                                                and isinstance(_payload.get("state"),
                                                               (dict, str)))
    except Exception as e:  # noqa: BLE001
        others["jev_still_sends_text_state"] = "raised %s: %s" % (type(e).__name__, e)
    ev["other_backends"] = others
    checks["scripted_regression_none"] = others["scripted"]
    checks["openai_regression_none"] = others["openai"]
    checks["jev_regression_none"] = others["jev"]
    checks["playjev_wired_in_factory"] = others["playjev"]
    checks["playjev_default_base_url_8081"] = others["playjev_default_port_is_8081"]
    checks["unknown_backend_error_names_playjev"] = others["unknown_backend_raises"]

    result = {"ok": all(checks.values()), "passed": sum(1 for v in checks.values() if v),
              "total": len(checks), "checks": checks, "evidence": ev,
              "frame_paths": [f["path"] for f in frames]}
    if evidence_path:
        os.makedirs(os.path.dirname(evidence_path), exist_ok=True)
        with open(evidence_path, "w", encoding="utf-8") as fh:
            json.dump(result, fh, ensure_ascii=False, indent=1)
        result["evidence_path"] = os.path.abspath(evidence_path)
    if verbose:
        print(json.dumps({"ok": result["ok"], "passed": result["passed"],
                          "total": result["total"], "checks": checks,
                          "evidence_path": result.get("evidence_path")},
                         ensure_ascii=False, indent=1))
    return result


def main(argv=None):
    argv = list(argv or sys.argv[1:])
    evidence = os.path.join(os.path.dirname(TOOLS), "runs", "playability",
                            "agent-probe-playjev.json")
    r = run_all(verbose=True, argv=argv, evidence_path=evidence)
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
