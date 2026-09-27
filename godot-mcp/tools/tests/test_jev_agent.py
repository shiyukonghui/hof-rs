#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""test_jev_agent.py -- prove the TASK-124 `jev` backend against a dumb service.

This is the evidence generator for TASK-124 deliverable D.  It starts
`tools/tests/jev_dumb_server.py` (stdlib only, no weights, no GPU, no network) and
exercises the `JevAgent` backend against it, covering:

  D1  GET /health readiness -> the agent treats the service as reachable
  D2  POST /v1/systemone with a fixed answer set -> request shape and response
      parsing are correct (choice -> action dict, noul -> float, score -> expected
      level, probabilities/confidence/usage captured into the evidence)
  D3  HTTP 429 + `Retry-After: 1` -> backoff really retries (attempt count recorded)
  D4  HTTP 422 -> reported as an explicit error, never a silent success
  D5  unknown field / over-long `state` -> our constructor emits NO illegal request,
      and the dumb server's own validator rejects the hand-built illegal ones
      (so the "we never send illegal requests" claim is checkable, not a tautology)
  D6  image request -> exactly 1 image + 1 question; multi-question is a clear error
  D7  unconfigured base URL / nothing listening -> safe `wait` + recorded reason

Run (fixed high port, checked first; python writes the evidence file itself -- no shell
redirection anywhere):

    netstat -ano | findstr :55124
    D:\\Anaconda\\Scripts\\python.exe tools\\tests\\test_jev_agent.py --port 55124 ^
        --out runs\\playability\\agent-probe-jev.json

Exit code 0 means every check below passed.  The full evidence -- including the exact
request JSON the dumb server received and the exact response it sent -- is written to
the `--out` file.
"""

from __future__ import print_function

import argparse
import base64
import json
import os
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)
sys.path.insert(0, HERE)

from playtest_agent import JevAgent, build_agent  # noqa: E402
import jev_dumb_server as dumb  # noqa: E402

DEFAULT_PORT = 55124
DEAD_PORT = 55129          # deliberately nothing listening here
DEFAULT_OUT = os.path.join(ROOT, "runs", "playability", "agent-probe-jev.json")


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------
def sample_inputs():
    """A frame list, a structured state and a goal shaped like the gate's own."""
    tmpdir = tempfile.mkdtemp(prefix="jev_probe_")
    png = os.path.join(tmpdir, "frame_00.png")
    with open(png, "wb") as fh:
        fh.write(base64.b64decode(
            b"iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAYAAACZgbYnAAAAFklEQVR4nGP8z8DAwMDA"
            b"xMDAwMAAAA0AAf8B2S0AAAAASUVORK5CYII="))
    frames = [{"index": 0, "path": png, "width": 2, "height": 2, "window": [2, 2],
               "declared": [2, 2], "content_fraction": 1.0, "bbox": [0, 0, 2, 2],
               "changed_pixels_vs_prev": 0}]
    state = {
        "window": {"visible": [1280, 720], "declared": [1280, 720], "matches": True},
        "engine": {"fps": 60, "frame": 1234},
        "nodes": {"Paddle": {"x": 100, "y": 300}, "Ball": {"x": 640, "y": 360}},
        "hud_text": "Score 0 - 0",
        "pixel_delta": 812,
        "assertions": [{"id": "P2", "pass": True}, {"id": "P6", "pass": False}],
        "digest": "probe",
    }
    goal = {"game": "pong", "objective": "make the score advance",
            "actions": {"pong_left_up": ["W"], "pong_left_down": ["S"],
                        "pong_serve": ["SPACE"]},
            "keys": ["W", "S", "SPACE"]}
    return frames, state, goal


def port_report(port):
    """'check the port before you start it' -- a real bind test plus netstat lines."""
    lines = []
    try:
        proc = subprocess.run(["netstat", "-ano"], stdout=subprocess.PIPE,
                              stderr=subprocess.DEVNULL, timeout=30)
        text = proc.stdout.decode("utf-8", "replace")
        lines = [l.strip() for l in text.splitlines() if (":%d" % port) in l]
    except Exception as e:  # noqa: BLE001
        lines = ["netstat unavailable: %s" % e]
    # A TIME_WAIT pair left over from an earlier probe is not an owner; what matters is
    # that nothing is LISTENING and that a real bind succeeds.
    owners = [l for l in lines if "TIME_WAIT" not in l]
    return {"port": port, "free_to_bind": dumb.port_status(port),
            "owners": owners, "time_wait_pairs": len(lines) - len(owners),
            "netstat_lines": lines}


def _mk_agent(url, **opts):
    o = {"base_url": url, "api_key": "sk-jev-probe"}
    o.update(opts)
    return JevAgent("probe", "prove the jev protocol", o)


# ---------------------------------------------------------------------------
# the checks
# ---------------------------------------------------------------------------
def run_all(verbose=True, argv=None):
    ap = argparse.ArgumentParser(description="TASK-124 jev dumb-service verification")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--seconds", type=float, default=0.0,
                    help="unused; kept so the report's commands stay stable")
    args = ap.parse_args(argv or [])

    frames, state, goal = sample_inputs()
    results = {"task": "TASK-124", "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
               "dumb_server": os.path.join("tools", "tests", "jev_dumb_server.py"),
               "agent_module": os.path.join("tools", "playtest_agent.py"),
               "port": args.port, "checks": {}, "errors": []}
    port_ev = port_report(args.port)
    results["port_check"] = port_ev
    if not port_ev["free_to_bind"]:
        results["ok"] = False
        results["stopped"] = ("port %d is not free to bind; `netstat -ano | findstr :%d` "
                              "shows who owns it" % (args.port, args.port))
        _write(args.out, results)
        if verbose:
            print(json.dumps(results, ensure_ascii=False, indent=1))
        return results

    def serve(mode, busy_retries=1, retry_after=1):
        return dumb.DumbJevServer(port=args.port, mode=mode, busy_retries=busy_retries,
                                  retry_after=retry_after).start()

    # ---- D1: /health readiness -------------------------------------------
    srv = serve("ok")
    try:
        agent = _mk_agent(srv.url)
        health = agent.check_health()
        act = agent.decide(frames, state, goal)
        paths = [r["path"] for r in srv.requests]
        results["D1_health"] = {
            "health_status": health.get("status"),
            "health_json": health.get("json"),
            "action_type": act.get("type"),
            "request_paths": paths,
            "errors": agent.errors,
        }
        results["checks"]["D1_health_ok"] = (
            health.get("status") == 200
            and isinstance(health.get("json"), dict)
            and "text" in (health.get("json", {}).get("input_modalities") or [])
            and act.get("type") == "action")
        results["checks"]["D1_health_not_models"] = (
            "/health" in paths and not any("/v1/models" in p for p in paths))
        results["D1_health_not_models_note"] = (
            "the vendor documents that /v1/models does not exist; the probe never asks "
            "for it, and the dumb server answers 404 for it on purpose")
    finally:
        srv.stop()

    # ---- D2: request shape + response parsing ----------------------------
    srv = serve("ok")
    try:
        agent = _mk_agent(srv.url)
        act = agent.decide(frames, state, goal)
        judge = agent.judge(frames, state, goal)
        reqs = srv.requests
        req = reqs[-1] if reqs else {}
        payload = req.get("payload") or {}
        questions = payload.get("questions") or {}
        types = {k: (v or {}).get("type") for k, v in questions.items()}
        ev = agent.calls[-1] if agent.calls else {}
        expected_choice = sorted((goal.get("actions") or {}))[0] \
            if goal.get("actions") else None
        results["D2_request"] = {
            "received_payload": payload,
            "received_headers": req.get("headers"),
            "server_validation_errors": srv.validation_errors,
            "request_meta": ev.get("request_meta"),
        }
        results["D2_response"] = {
            "action": act,
            "action_then_evidence": {
                "choice_answer": ev.get("choice"),
                "noul": ev.get("noul"),
                "scores": ev.get("scores"),
                "usage": ev.get("usage"),
                "input_tokens": ev.get("input_tokens"),
                "image_tokens": ev.get("image_tokens"),
                "confidence_header": ev.get("confidence_header"),
                "usage_header": ev.get("usage_header"),
                "probabilities": ev.get("probabilities"),
                "confidences": ev.get("confidences"),
            },
            "judge": judge,
        }
        field_table = [
            {"field": "model", "expected": "one of the accepted Jev names",
             "actual": payload.get("model"),
             "ok": payload.get("model") in ("neohorse-jev", "NeoHorse-Jev-4B")},
            {"field": "state", "expected": "string | object | array (our structured state)",
             "actual_type": type(payload.get("state")).__name__,
             "ok": isinstance(payload.get("state"), (str, dict, list))},
            {"field": "questions", "expected": "object, keys -> {type, instructions, criteria}",
             "actual_keys": list(questions),
             "ok": isinstance(questions, dict) and 1 <= len(questions) <= 16},
            {"field": "questions.move.type", "expected": "choice",
             "actual": types.get("move"),
             "ok": types.get("move") == "choice"},
            {"field": "questions.move.criteria", "expected": "candidate dict, 1..255",
             "actual_keys": sorted((questions.get("move") or {}).get("criteria") or {}),
             "ok": isinstance((questions.get("move") or {}).get("criteria"), dict)},
            {"field": "questions.<noul>.type", "expected": "noul",
             "actual": {k: v for k, v in types.items() if v == "noul"},
             "ok": sum(1 for v in types.values() if v == "noul") >= 2},
            {"field": "questions.<score>.type", "expected": "score",
             "actual": {k: v for k, v in types.items() if v == "score"},
             "ok": sum(1 for v in types.values() if v == "score") == 1},
            {"field": "questions.<score>.criteria", "expected": "ordered list, 2..10",
             "actual": len(((questions.get("brokenness") or {}).get("criteria") or [])),
             "ok": 2 <= len(((questions.get("brokenness") or {}).get("criteria") or [])) <= 10},
            {"field": "$unknown", "expected": "none",
             "actual": sorted(set(payload) - {"model", "state", "questions", "image"}),
             "ok": not (set(payload) - {"model", "state", "questions", "image"})},
            {"field": "image", "expected": "absent on a text request",
             "actual": "present" if "image" in payload else "absent",
             "ok": "image" not in payload},
        ]
        results["D2_field_table"] = field_table
        results["checks"]["D2_request_shape"] = all(r["ok"] for r in field_table)
        results["checks"]["D2_constructor_legal"] = not srv.validation_errors
        results["checks"]["D2_choice_mapped_to_action"] = (
            act.get("type") == "action" and act.get("action") == expected_choice)
        noul_vals = [a.get("noul") for a in (ev.get("noul") or {}).values()]
        score_vals = [a.get("score") for a in (ev.get("scores") or {}).values()]
        results["checks"]["D2_noul_is_float"] = bool(noul_vals) and all(
            isinstance(v, float) for v in noul_vals)
        results["checks"]["D2_score_is_expected_level"] = bool(score_vals) and all(
            isinstance(v, float) for v in score_vals)
        results["checks"]["D2_evidence_captured"] = bool(
            ev.get("probabilities") and ev.get("usage") is not None
            and ev.get("confidence_header"))
        results["checks"]["D2_auth_header_sent"] = (
            (req.get("headers") or {}).get("authorization") == "Bearer sk-jev-probe")
    finally:
        srv.stop()

    # ---- D3: 429 + Retry-After -> backoff retry --------------------------
    srv = serve("busy", busy_retries=1, retry_after=1)
    try:
        agent = _mk_agent(srv.url, max_retries=2, retry_backoff=1.0)
        t0 = time.time()
        act = agent.decide(frames, state, goal)
        elapsed = round(time.time() - t0, 2)
        ev = agent.calls[-1] if agent.calls else {}
        attempts = (ev.get("transport") or {}).get("attempts") or []
        statuses = [r.get("responded_status") for r in srv.requests]
        results["D3_retry"] = {
            "action_type": act.get("type"), "attempts": attempts, "elapsed_s": elapsed,
            "server_responded_statuses": statuses,
            "retry_after_header_seen": [a.get("retry_after") for a in attempts],
        }
        results["checks"]["D3_retried_on_429"] = (
            len(attempts) == 2 and attempts[0].get("status") == 429
            and attempts[1].get("status") == 200)
        results["checks"]["D3_honoured_retry_after"] = elapsed >= 0.9
        results["checks"]["D3_retry_after_recorded"] = (
            attempts[0].get("retry_after") == "1" if attempts else False)
        results["checks"]["D3_succeeded_after_retry"] = act.get("type") == "action"
    finally:
        srv.stop()

    # ---- D4: 422 -> explicit error --------------------------------------
    srv = serve("invalid")
    try:
        agent = _mk_agent(srv.url)
        act = agent.decide(frames, state, goal)
        ev = agent.calls[-1] if agent.calls else {}
        attempts = (ev.get("transport") or {}).get("attempts") or []
        results["D4_422"] = {"action": act, "errors": agent.errors,
                             "why": act.get("why"), "attempts": attempts}
        results["checks"]["D4_422_reported"] = bool(
            any(e.get("status") == 422 for e in agent.errors))
        results["checks"]["D4_422_not_retried"] = len(attempts) == 1
        results["checks"]["D4_422_degrades_to_wait"] = act.get("type") == "wait"
    finally:
        srv.stop()

    # ---- D5: the constructor never emits an illegal request --------------
    srv = serve("ok")
    try:
        # (a) the server-side validator is real, not a tautology: a hand-built payload
        #     with an unknown field must be refused by the SERVER.
        agent = _mk_agent(srv.url)
        question = {"type": "noul", "instructions": "Does it work?"}
        bad_unknown = {"model": "NeoHorse-Jev-4B", "state": "x", "questions": {"q": question},
                       "bogus_field": 1}
        rec_unknown = agent._request("POST", "/v1/systemone", bad_unknown)
        bad_state = {"model": "NeoHorse-Jev-4B", "state": "a" * 30000,
                     "questions": {"q": {"type": "noul", "instructions": "ok?"}}}
        rec_state = agent._request("POST", "/v1/systemone", bad_state)
        results["D5_server_rejects"] = {
            "unknown_field_status": rec_unknown.get("status"),
            "unknown_field_body": (rec_unknown.get("body") or "")[:400],
            "overlong_state_status": rec_state.get("status"),
            "overlong_state_body": (rec_state.get("body") or "")[:400],
            "state_estimate_for_30000_ascii_chars":
                dumb.estimate_tokens("a" * 30000),
        }
        results["checks"]["D5_server_validator_is_real"] = (
            rec_unknown.get("status") == 422 and rec_state.get("status") == 422)
        results["checks"]["D5_unknown_field_named"] = (
            "Unknown request fields" in (rec_unknown.get("body") or ""))

        # (b) a fresh agent: our own builder's payload passes the same validator offline
        agent2 = _mk_agent(srv.url)
        payload, meta = agent2.build_request(frames, state, goal, "action")
        offline_errors = dumb.validate_request(payload)
        results["D5_our_payload_offline"] = {
            "payload_fields": sorted(payload), "offline_validation_errors": offline_errors,
            "request_meta": meta,
        }
        results["checks"]["D5_our_payload_is_legal"] = not offline_errors

        # (c) over-long state is REFUSED client-side, and nothing is POSTed
        before = len([r for r in srv.requests if r["method"] == "POST"])
        agent3 = _mk_agent(srv.url)
        act_over = agent3.decide(frames, {"note": "x" * 30000, "probe": state}, goal)
        after = len([r for r in srv.requests if r["method"] == "POST"])
        results["D5_overlong_state"] = {
            "action": act_over, "errors": agent3.errors,
            "post_requests_before": before, "post_requests_after": after,
        }
        results["checks"]["D5_overlong_state_refused"] = (
            act_over.get("type") == "wait" and bool(agent3.errors)
            and "over the 2048-token" in (act_over.get("why") or ""))
        results["checks"]["D5_overlong_state_not_sent"] = after == before

        # (d) explicit clip mode: it declares exactly what it dropped
        #     (note: srv.validation_errors still holds the two DELIBERATE rejections from
        #     (a), so only NEW errors count here)
        errs_before_clip = len(srv.validation_errors)
        agent4 = _mk_agent(srv.url, state_overflow="clip")
        big = {"a": "x" * 8000, "b": "y" * 8000, "c": "keep me", "probe": state}
        act_clip = agent4.decide(frames, big, goal)
        ev4 = agent4.calls[-1] if agent4.calls else {}
        clip = ((ev4.get("request_meta") or {}).get("state") or {}).get("clipped")
        new_errs = srv.validation_errors[errs_before_clip:]
        results["D5_clip"] = {"action_type": act_clip.get("type"), "clipped": clip,
                              "kept_state_tokens":
                                  ((ev4.get("request_meta") or {}).get("state") or {})
                                  .get("state_tokens_estimate"),
                              "new_validation_errors": new_errs,
                              "errors": agent4.errors}
        results["checks"]["D5_clip_declares_dropped"] = bool(
            clip and clip.get("dropped_keys") and act_clip.get("type") == "action")
        results["checks"]["D5_clip_request_legal"] = not new_errs
    finally:
        srv.stop()

    # ---- D6: image request = exactly 1 image + 1 question ----------------
    srv = serve("ok")
    try:
        agent = _mk_agent(srv.url, send_images=True)
        before = len([r for r in srv.requests if r["method"] == "POST"])
        act_img = agent.decide(frames, state, goal)
        after = len([r for r in srv.requests if r["method"] == "POST"])
        results["D6_image_multi"] = {"action": act_img, "errors": agent.errors,
                                     "posts_before": before, "posts_after": after}
        results["checks"]["D6_image_multi_question_refused"] = (
            act_img.get("type") == "wait" and bool(agent.errors)
            and "exactly 1 image + 1 question" in (act_img.get("why") or ""))
        results["checks"]["D6_multi_question_image_not_sent"] = after == before

        agent2 = _mk_agent(srv.url, send_images=True, image_multi_question="trim",
                           invariant_questions=0, score_question=False)
        act_img2 = agent2.decide(frames, state, goal)
        ev6 = agent2.calls[-1] if agent2.calls else {}
        img_payload = None
        for r in reversed(srv.requests):
            if r["method"] == "POST" and (r.get("payload") or {}).get("image"):
                img_payload = r["payload"]
                break
        results["D6_image_ok"] = {
            "action_type": act_img2.get("type"),
            "policy": (ev6.get("request_meta") or {}).get("image_question_policy"),
            "with_image": (ev6.get("request_meta") or {}).get("with_image"),
            "image_prefix": (img_payload or {}).get("image", "")[:40],
            "image_fields": sorted(img_payload) if img_payload else [],
            "questions_sent": sorted((img_payload or {}).get("questions") or {}),
            "server_validation_errors": srv.validation_errors,
        }
        results["checks"]["D6_image_single_question_ok"] = (
            act_img2.get("type") == "action" and img_payload is not None
            and len(img_payload.get("questions") or {}) == 1
            and (img_payload.get("image") or "").startswith("data:image/png;base64,"))
        results["checks"]["D6_image_payload_legal"] = not srv.validation_errors
    finally:
        srv.stop()

    # ---- D7: unconfigured / unreachable -> safe wait ---------------------
    unconfigured = JevAgent("probe", "", {"base_url": ""})
    act_unconf = unconfigured.decide(frames, state, goal)
    dead_ev = port_report(DEAD_PORT)
    dead = JevAgent("probe", "", {"base_url": "http://127.0.0.1:%d" % DEAD_PORT,
                                  "timeout": 3})
    act_dead = dead.decide(frames, state, goal)
    results["D7_unconfigured"] = {"action": act_unconf, "errors": unconfigured.errors}
    results["D7_dead_port"] = {"port": DEAD_PORT, "port_check": dead_ev,
                               "action": act_dead, "errors": dead.errors}
    results["checks"]["D7_unconfigured_is_safe_wait"] = (
        act_unconf.get("type") == "wait" and bool(unconfigured.errors))
    results["checks"]["D7_dead_port_is_safe_wait"] = (
        act_dead.get("type") == "wait" and bool(dead.errors)
        and dead_ev["free_to_bind"])
    results["checks"]["D7_no_silent_success"] = (
        (act_unconf.get("type") != "action") and (act_dead.get("type") != "action"))

    # ---- regressions: scripted / openai untouched ------------------------
    sa = build_agent("scripted", "probe", "probe", {"plan": None})
    sa_act = sa.decide([], {}, {"keys": ["W", "SPACE"]})
    ja = build_agent("jev", "probe", "probe", {"base_url": ""})
    results["regression"] = {
        "scripted_action": sa_act,
        "openai_still_builds": build_agent("openai", "probe", "probe",
                                           {"base_url": "http://127.0.0.1:1"}).name,
        "jev_builds": ja.name,
    }
    results["checks"]["R_scripted_unchanged"] = (
        sa_act.get("type") == "key" and sa_act.get("keycode") == 87)
    results["checks"]["R_openai_still_available"] = results["regression"][
        "openai_still_builds"] == "openai"
    results["checks"]["R_jev_factory"] = ja.name == "jev"

    results["ok"] = all(results["checks"].values())
    results["reproduce"] = [
        "netstat -ano | findstr :%d" % args.port,
        "D:\\Anaconda\\Scripts\\python.exe tools\\tests\\jev_dumb_server.py --mode ok "
        "--port %d" % args.port,
        "D:\\Anaconda\\Scripts\\python.exe tools\\tests\\test_jev_agent.py --port %d "
        "--out runs\\playability\\agent-probe-jev.json" % args.port,
        "D:\\Anaconda\\Scripts\\python.exe tools\\playtest_agent.py --probe-jev",
    ]
    _write(args.out, results)
    if verbose:
        print(json.dumps({"ok": results["ok"], "checks": results["checks"],
                          "out": os.path.abspath(args.out), "failed":
                          [k for k, v in results["checks"].items() if not v]},
                         ensure_ascii=False, indent=1))
    return results


def _write(path, results):
    if not path:
        return
    d = os.path.dirname(os.path.abspath(path))
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(results, fh, ensure_ascii=False, indent=1)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    return 0 if run_all(verbose=True, argv=argv)["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
