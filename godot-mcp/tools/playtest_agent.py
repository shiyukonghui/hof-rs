#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""playtest_agent.py -- the pluggable "playtest agent" interface (TASK-116 item D).

One interface, two backends
---------------------------
    decide(frames, state, goal) -> action

    frames : list[dict]   the frames the gate has already captured, oldest first.
                          Each entry is
                            {"index": int, "path": str, "width": int, "height": int,
                             "window": [w, h], "declared": [w, h],
                             "content_fraction": float, "bbox": [x, y, w, h],
                             "sha256": str, "changed_pixels_vs_prev": int}
                          `path` is a real PNG on disk (the agent may read it).
    state  : dict         the latest sampled game state
                            {"window": {...}, "engine": {...}, "nodes": {...},
                             "digest": str, "changed_keys": [...]}
    goal   : dict|str     what the agent is asked to achieve, e.g.
                            {"game": "pong", "objective": "make the score advance",
                             "keys": ["W", "S", "Space"], "actions": {...}}

    action : dict         exactly one of
                            {"type": "key",    "keycode": int, "pressed": bool,
                             "hold_ms": int, "why": str}
                            {"type": "action", "action": "ast_thrust",
                             "pressed": bool, "hold_ms": int, "why": str}
                            {"type": "wait",   "ms": int, "why": str}
                            {"type": "script", "code": "return 1", "why": str}
                            {"type": "done",   "why": str}

Backends
--------
  scripted : a built-in scripted action sequence.  It is what the gate uses by
             default, so the gate is reproducible without any model.
  openai   : an OpenAI-compatible HTTP chat-completions client.  It sends the
             screenshots (base64 PNG) *and* the structured state to the model and
             requires a JSON action back; in `judge` mode it asks the very same
             endpoint the question a human reviewer would ask -- "does this frame
             look playable, is anything wrong?".

    env var            meaning                          example
    -----------------  -------------------------------  -------------------------------
    PLAYTEST_BASE_URL  OpenAI-compatible base URL       http://127.0.0.1:8000/v1
    PLAYTEST_API_KEY   bearer token (may be empty)      sk-local
    PLAYTEST_MODEL     model name                       neo-horse-jev

Wiring a local model such as NeoHorse-Jev (documented contract, item D)
----------------------------------------------------------------------
    :: 1. start the model as an OpenAI-compatible server (pick the one you have)
    ::    vLLM:
    D:\\Anaconda\\Scripts\\python.exe -m vllm.entrypoints.openai.api_server ^
         --model <path-or-hf-id-of-NeoHorse-Jev> --served-model-name neo-horse-jev ^
         --port 8000 --host 127.0.0.1
    ::    llama.cpp:  llama-server.exe -m NeoHorse-Jev.gguf --port 8000 --host 127.0.0.1
    ::    (llama.cpp serves /v1/chat/completions too; it ignores the api key.)
    ::
    :: 2. point the gate at it
    set PLAYTEST_BASE_URL=http://127.0.0.1:8000/v1
    set PLAYTEST_API_KEY=sk-local
    set PLAYTEST_MODEL=neo-horse-jev
    ::
    :: 3. run the gate with the model in the loop
    D:\\Anaconda\\Scripts\\python.exe F:\\moonbit-hof-rs\\godot-mcp\\tools\\playability_gate.py ^
         --games pong --agent=openai

    That is *all* the coupling there is: the backend speaks/consumes JSON over
    HTTP and nothing in the gate knows the model's name.  A vision-less model
    still works -- the state JSON is always sent and the images become optional
    when `--no-images` is passed.

Self-test without any model
---------------------------
    python tools\\playtest_agent.py --probe
        starts a *dumb* OpenAI-compatible server on 127.0.0.1 (one endpoint that
        answers a canned completion, one that answers HTTP 500) and exercises the
        openai backend against both, so the transport is proven while a real
        model is absent.  Exit code 0 means: request built, auth header sent,
        image part attached, JSON action extracted, server error reported as an
        error (and *not* as a silent success).
"""

from __future__ import print_function

import base64
import io
import json
import os
import re
import sys
import threading
import time

try:  # python 3
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError, URLError
except ImportError:  # pragma: no cover - python 2 is not supported, but be explicit
    raise SystemExit("playtest_agent.py needs python 3")


# ---------------------------------------------------------------------------
# key names -> Godot keycodes (the subset the 20 games actually use)
# ---------------------------------------------------------------------------
KEYCODES = {
    "A": 65, "B": 66, "C": 67, "D": 68, "E": 69, "F": 70, "G": 71, "H": 72,
    "I": 73, "J": 74, "K": 75, "L": 76, "M": 77, "N": 78, "O": 79, "P": 80,
    "Q": 81, "R": 82, "S": 83, "T": 84, "U": 85, "V": 86, "W": 87, "X": 88,
    "Y": 89, "Z": 90,
    "0": 48, "1": 49, "2": 50, "3": 51, "4": 52, "5": 53, "6": 54, "7": 55,
    "8": 56, "9": 57,
    "SPACE": 32, "ENTER": 4194309, "ESCAPE": 4194305, "TAB": 4194306,
    "UP": 4194320, "DOWN": 4194322, "LEFT": 4194319, "RIGHT": 4194321,
    "SHIFT": 4194325, "CTRL": 4194326, "ALT": 4194327,
}
GODOT_TO_NAME = {}
for _n, _c in KEYCODES.items():
    GODOT_TO_NAME.setdefault(_c, _n)


def keycode_of(name_or_code):
    """Accept an int keycode, an action name, or a human key name ('W', 'SPACE')."""
    if isinstance(name_or_code, int):
        return name_or_code
    s = str(name_or_code).strip().upper()
    if s in KEYCODES:
        return KEYCODES[s]
    if s.startswith("KEY_"):
        s = s[4:]
        if s in KEYCODES:
            return KEYCODES[s]
    if re.match(r"^\d+$", s):
        return int(s)
    return None


def keyname_of(code):
    return GODOT_TO_NAME.get(int(code), "KEY_%d" % int(code))


# ---------------------------------------------------------------------------
# the interface
# ---------------------------------------------------------------------------
class PlaytestAgent(object):
    """The one interface the playability gate talks to."""

    name = "abstract"

    def __init__(self, game=None, objective="", options=None):
        self.game = game or ""
        self.objective = objective or ""
        self.options = options or {}
        self.calls = []          # every (request, response-summary) pair, for evidence

    # ---- the contract ----------------------------------------------------
    def decide(self, frames, state, goal):
        """Return exactly one action dict (see the module docstring)."""
        raise NotImplementedError

    def judge(self, frames, state, goal):
        """Optional: "does this look playable / what is wrong?".

        Returns None when the backend cannot answer (the scripted backend always
        returns None).  The gate records the answer as human-readable commentary
        only -- it never feeds a P-verdict, because a language model's opinion is
        not machine-checkable evidence.
        """
        return None

    def report(self):
        return {"backend": self.name, "game": self.game,
                "objective": self.objective, "calls": self.calls}


# ---------------------------------------------------------------------------
# backend 1: scripted
# ---------------------------------------------------------------------------
class ScriptedAgent(PlaytestAgent):
    """A deterministic action sequence: the gate can always run without a model.

    The plan is either passed in (`options["plan"]`) or built from the goal's
    `keys` / `actions` lists by a fixed rule:

      * for every declared action (up to `max_actions`), press its own key for
        `hold_ms`, then release it, then wait `settle_ms`;
      * then one `done`.

    This is not a smart player -- it is a *probe*.  Its job is to make the gate's
    P2/P3 checks reproducible, and to leave the frames a person (or a model in
    `judge` mode) needs in order to answer "could a human play this?".
    """

    name = "scripted"

    def __init__(self, game=None, objective="", options=None):
        PlaytestAgent.__init__(self, game, objective, options)
        self._plan = list(self.options.get("plan") or [])
        self._i = 0

    def _builtin_plan(self, goal):
        plan = []
        hold = int(self.options.get("hold_ms", 350))
        settle = int(self.options.get("settle_ms", 250))
        actions = list(goal.get("actions") or [])
        ordered = list(goal.get("actions_order") or actions)
        if not ordered:
            # fall back to the audit's own key list
            for k in goal.get("keys") or []:
                plan.append({"type": "key", "keycode": keycode_of(k), "pressed": True,
                             "hold_ms": hold, "why": "documented key %s (down)" % k})
                plan.append({"type": "key", "keycode": keycode_of(k), "pressed": False,
                             "hold_ms": 0, "why": "documented key %s (up)" % k})
                plan.append({"type": "wait", "ms": settle, "why": "let the frame settle"})
            plan.append({"type": "done", "why": "scripted probe finished"})
            return plan
        for a in ordered:
            plan.append({"type": "action", "action": a, "pressed": True, "hold_ms": hold,
                         "why": "declared action %s (down)" % a})
            plan.append({"type": "action", "action": a, "pressed": False, "hold_ms": 0,
                         "why": "declared action %s (up)" % a})
            plan.append({"type": "wait", "ms": settle, "why": "let the frame settle"})
        plan.append({"type": "done", "why": "scripted probe finished"})
        return plan

    def decide(self, frames, state, goal):
        if not self._plan:
            self._plan = self._builtin_plan(goal or {})
        if self._i >= len(self._plan):
            act = {"type": "done", "why": "plan exhausted"}
        else:
            act = dict(self._plan[self._i])
            self._i += 1
        self.calls.append({"n": self._i, "action": act})
        return act


# ---------------------------------------------------------------------------
# backend 2: openai (OpenAI-compatible HTTP)
# ---------------------------------------------------------------------------
ACTION_SCHEMA_HINT = {
    "type": "key", "keycode": 87, "pressed": True, "hold_ms": 300, "why": "short reason",
}
JUDGE_SCHEMA_HINT = {
    "playable": True,
    "confidence": 0.0,
    "abnormalities": ["..."],
    "why": "short reason",
}


class OpenAIAgent(PlaytestAgent):
    """OpenAI-compatible chat-completions backend.

    It never raises out of `decide`: a transport failure becomes a safe `wait`
    action and is recorded in `self.errors`, so a broken model endpoint degrades
    the gate to "no agent input" instead of crashing a 20-game sweep.
    """

    name = "openai"

    def __init__(self, game=None, objective="", options=None):
        PlaytestAgent.__init__(self, game, objective, options)
        self.base_url = (self.options.get("base_url")
                         or os.environ.get("PLAYTEST_BASE_URL", "")).rstrip("/")
        self.api_key = self.options.get("api_key")
        if self.api_key is None:
            self.api_key = os.environ.get("PLAYTEST_API_KEY", "")
        self.model = self.options.get("model") or os.environ.get("PLAYTEST_MODEL", "")
        self.timeout = float(self.options.get("timeout", 60))
        self.send_images = bool(self.options.get("send_images", True))
        self.max_images = int(self.options.get("max_images", 3))
        self.errors = []
        self._plan = []

    # ---- transport -------------------------------------------------------
    def _post(self, path, payload):
        url = self.base_url + path
        body = json.dumps(payload).encode("utf-8")
        req = Request(url, data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        if self.api_key:
            req.add_header("Authorization", "Bearer %s" % self.api_key)
        t0 = time.time()
        try:
            resp = urlopen(req, timeout=self.timeout)
            raw = resp.read().decode("utf-8", "replace")
            rec = {"url": url, "status": getattr(resp, "status", 200),
                   "seconds": round(time.time() - t0, 3), "body": raw}
        except HTTPError as e:
            raw = e.read().decode("utf-8", "replace") if hasattr(e, "read") else ""
            rec = {"url": url, "status": e.code, "seconds": round(time.time() - t0, 3),
                   "body": raw, "error": "HTTPError"}
        except URLError as e:
            rec = {"url": url, "status": None, "seconds": round(time.time() - t0, 3),
                   "body": "", "error": "URLError: %s" % e}
        except Exception as e:  # noqa: BLE001 - the gate must never die on a model
            rec = {"url": url, "status": None, "seconds": round(time.time() - t0, 3),
                   "body": "", "error": "%s: %s" % (type(e).__name__, e)}
        return rec

    def _chat(self, messages):
        payload = {"model": self.model, "messages": messages,
                   "temperature": 0.0, "max_tokens": 400}
        rec = self._post("/chat/completions", payload)
        text = ""
        if rec.get("status") == 200 and rec.get("body"):
            try:
                data = json.loads(rec["body"])
                text = data["choices"][0]["message"]["content"]
            except Exception as e:  # noqa: BLE001
                rec["parse_error"] = "%s: %s" % (type(e).__name__, e)
        else:
            self.errors.append({"status": rec.get("status"), "error": rec.get("error"),
                                "body": (rec.get("body") or "")[:400]})
        rec["content"] = text
        self.calls.append({"payload_bytes": len(json.dumps(payload)),
                           "status": rec.get("status"), "content": text[:400]})
        return text

    # ---- message building ------------------------------------------------
    def _image_parts(self, frames):
        parts = []
        if not self.send_images:
            return parts
        for f in frames[-self.max_images:]:
            p = f.get("path")
            if not p or not os.path.isfile(p):
                continue
            with open(p, "rb") as fh:
                b64 = base64.b64encode(fh.read()).decode("ascii")
            parts.append({"type": "image_url",
                          "image_url": {"url": "data:image/png;base64,%s" % b64}})
        return parts

    def _build_user_message(self, frames, state, goal, want):
        slim = []
        for f in frames[-6:]:
            slim.append({k: f.get(k) for k in
                         ("index", "width", "height", "window", "declared",
                          "content_fraction", "bbox", "changed_pixels_vs_prev")})
        text = (
            "You are a game playtest agent. You are looking at frames captured from a "
            "REAL, full-window run of the game (not the editor's embedded window).\n"
            "GAME: %s\nOBJECTIVE: %s\nGOAL: %s\n"
            "FRAMES (oldest first): %s\n"
            "LATEST STATE: %s\n"
            "Available input actions and their keys: %s\n"
            "Answer with ONE JSON object and nothing else.\n"
            "If you are asked for an ACTION, use this shape:\n%s\n"
            "If you are asked to JUDGE the frame, use this shape:\n%s\n"
            "Now answer as JSON: %s"
        ) % (
            json.dumps(self.game),
            json.dumps(self.objective),
            json.dumps(goal, ensure_ascii=False)[:1200],
            json.dumps(slim, ensure_ascii=False),
            json.dumps(state, ensure_ascii=False)[:2500],
            json.dumps((goal or {}).get("actions", {}), ensure_ascii=False),
            json.dumps(ACTION_SCHEMA_HINT),
            json.dumps(JUDGE_SCHEMA_HINT),
            "judge" if want == "judge" else "action",
        )
        parts = [{"type": "text", "text": text}]
        parts.extend(self._image_parts(frames))
        return {"role": "user", "content": parts}

    # ---- JSON extraction -------------------------------------------------
    @staticmethod
    def extract_json(text):
        if not text:
            return None
        t = text.strip()
        if t.startswith("```"):
            t = re.sub(r"^```[a-zA-Z]*\s*", "", t)
            t = re.sub(r"```\s*$", "", t)
        try:
            return json.loads(t)
        except Exception:  # noqa: BLE001
            pass
        m = re.search(r"\{.*\}", t, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:  # noqa: BLE001
                return None
        return None

    @staticmethod
    def normalise_action(obj):
        if not isinstance(obj, dict):
            return None
        t = obj.get("type") or obj.get("action_type")
        if t in ("key", "action", "wait", "script", "done"):
            out = dict(obj)
            out["type"] = t
            if t == "key" and not isinstance(out.get("keycode"), int):
                kc = keycode_of(out.get("key") or out.get("keycode") or "")
                if kc is None:
                    return None
                out["keycode"] = kc
            out.setdefault("why", "openai backend")
            return out
        # be forgiving: a bare keycode / action name is an implicit key press
        if isinstance(obj.get("keycode"), int) or obj.get("key"):
            kc = obj.get("keycode")
            if not isinstance(kc, int):
                kc = keycode_of(obj.get("key"))
            if kc is not None:
                return {"type": "key", "keycode": kc, "pressed": True,
                        "hold_ms": int(obj.get("hold_ms", 300)), "why": "openai backend"}
        return None

    # ---- the interface ---------------------------------------------------
    def decide(self, frames, state, goal):
        if not self.base_url:
            self.errors.append({"error": "PLAYTEST_BASE_URL is not set"})
            return {"type": "wait", "ms": 100, "why": "openai backend unconfigured"}
        msgs = [{"role": "system",
                 "content": "You are a precise game playtest agent. Reply with JSON only."},
                self._build_user_message(frames, state, goal, "action")]
        text = self._chat(msgs)
        act = self.normalise_action(self.extract_json(text))
        if act is None:
            return {"type": "wait", "ms": 200,
                    "why": "openai backend returned no usable action"}
        return act

    def judge(self, frames, state, goal):
        if not self.base_url:
            return None
        msgs = [{"role": "system",
                 "content": "You are a strict game playability reviewer. Reply with JSON only."},
                self._build_user_message(frames, state, goal, "judge")]
        text = self._chat(msgs)
        return self.extract_json(text)

    def report(self):
        rep = PlaytestAgent.report(self)
        rep["base_url"] = self.base_url
        rep["model"] = self.model
        rep["errors"] = self.errors
        return rep


# ---------------------------------------------------------------------------
# factory
# ---------------------------------------------------------------------------
def build_agent(name, game=None, objective="", options=None):
    n = (name or "scripted").strip().lower()
    if n == "scripted":
        return ScriptedAgent(game, objective, options)
    if n == "openai":
        return OpenAIAgent(game, objective, options)
    raise ValueError("unknown agent backend %r (expected scripted|openai)" % name)


# ---------------------------------------------------------------------------
# --probe: prove the openai transport without a real model
# ---------------------------------------------------------------------------
class _DumbOpenAIHandler(object):
    """A stdlib HTTP handler factory implementing just enough OpenAI shape."""

    @staticmethod
    def make(mode):
        from http.server import BaseHTTPRequestHandler

        class H(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *a):  # silence
                pass

            def do_POST(self):
                length = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(length) if length else b"{}"
                H.last_request = {
                    "path": self.path,
                    "auth": self.headers.get("Authorization"),
                    "content_type": self.headers.get("Content-Type"),
                    "payload": json.loads(raw.decode("utf-8", "replace") or "{}"),
                }
                if mode == "error":
                    body = b'{"error":{"message":"dumb server: simulated 500"}}'
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                    return
                # decide whether the caller wants an action or a judgement from the
                # prompt itself, so one dumb endpoint can serve both shapes
                blob = json.dumps(H.last_request["payload"].get("messages") or [],
                                  ensure_ascii=False)
                wants_judge = "answer as JSON: judge" in blob
                if mode == "action":
                    if wants_judge:
                        content = json.dumps({"playable": False, "confidence": 0.5,
                                              "abnormalities": ["dumb server judge"],
                                              "why": "dumb server judge"})
                    else:
                        content = json.dumps({"type": "key", "keycode": 87, "pressed": True,
                                              "hold_ms": 200, "why": "dumb server action"})
                else:
                    content = ""
                body = json.dumps({
                    "id": "dumb-1", "object": "chat.completion", "model": "dumb",
                    "choices": [{"index": 0, "finish_reason": "stop",
                                 "message": {"role": "assistant", "content": content}}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                }).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        return H


def probe(verbose=True):
    """Start a dumb OpenAI-compatible server and exercise the openai backend.

    Two servers, two runs:
      * `action` mode -> the backend must return the canned key action;
      * `error`  mode -> the backend must report the failure (never a silent
        success), and `decide()` must still return a safe action.
    """
    from http.server import HTTPServer

    results = {}
    frames = []
    # a 2x2 PNG so the image part is real
    png = base64.b64decode(
        b"iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAYAAACZgbYnAAAAFklEQVR4nGP8z8DAwMDA"
        b"xMDAwMAAAA0AAf8B2S0AAAAASUVORK5CYII=")
    import tempfile
    tmpdir = tempfile.mkdtemp(prefix="playtest_probe_")
    fpath = os.path.join(tmpdir, "frame_00.png")
    with open(fpath, "wb") as fh:
        fh.write(png)
    frames.append({"index": 0, "path": fpath, "width": 2, "height": 2,
                   "window": [2, 2], "declared": [2, 2], "content_fraction": 1.0,
                   "bbox": [0, 0, 2, 2], "changed_pixels_vs_prev": 0})
    state = {"window": {"visible": [2, 2]}, "digest": "probe", "nodes": {}}
    goal = {"game": "probe", "objective": "prove the transport",
            "actions": {"probe_action": ["W"]}}

    def run_mode(mode, handler_cls):
        srv = HTTPServer(("127.0.0.1", 0), handler_cls)
        port = srv.server_address[1]
        th = threading.Thread(target=srv.serve_forever)
        th.daemon = True
        th.start()
        try:
            agent = OpenAIAgent("probe", "prove the transport",
                                {"base_url": "http://127.0.0.1:%d/v1" % port,
                                 "api_key": "sk-probe", "model": "dumb"})
            act = agent.decide(frames, state, goal)
            judg = agent.judge(frames, state, goal)
            req = getattr(handler_cls, "last_request", {})
            sent_images = 0
            for m in (req.get("payload", {}).get("messages") or []):
                c = m.get("content")
                if isinstance(c, list):
                    sent_images += sum(1 for p in c if p.get("type") == "image_url")
            out = {"port": port, "action": act, "judge": judg,
                   "request_path": req.get("path"),
                   "auth_header": req.get("auth"),
                   "images_sent": sent_images,
                   "errors": agent.errors,
                   "calls": agent.calls}
        finally:
            srv.shutdown()
            srv.server_close()
        return out

    results["action_mode"] = run_mode("action", _DumbOpenAIHandler.make("action"))
    results["error_mode"] = run_mode("error", _DumbOpenAIHandler.make("error"))

    a = results["action_mode"]
    e = results["error_mode"]
    # a real check, not a tautology: an unconfigured backend must say so and must
    # still hand the gate a safe action
    unconfigured = OpenAIAgent("probe", "", {"base_url": ""})
    unconfigured_action = unconfigured.decide(frames, state, goal)

    checks = {
        "request_hits_chat_completions": a["request_path"] == "/v1/chat/completions",
        "bearer_token_sent": a["auth_header"] == "Bearer sk-probe",
        "base64_image_attached": a["images_sent"] >= 1,
        "canned_action_extracted": a["action"].get("type") == "key"
                                   and a["action"].get("keycode") == 87,
        "judge_json_extracted": isinstance(a["judge"], dict)
                                and a["judge"].get("playable") is False,
        "http_error_reported": any(x.get("status") == 500 for x in e["errors"]),
        "error_did_not_raise": e["action"].get("type") in ("wait", "done"),
        "unconfigured_is_safe": unconfigured_action.get("type") in ("wait", "done")
                                and bool(unconfigured.errors),
    }
    results["unconfigured_backend"] = {"action": unconfigured_action,
                                       "errors": unconfigured.errors}
    results["checks"] = checks
    results["ok"] = all(checks.values())
    if verbose:
        print(json.dumps(results, ensure_ascii=False, indent=1))
    return results


def main(argv):
    args = argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if args[0] == "--probe":
        r = probe()
        return 0 if r["ok"] else 1
    if args[0] == "--selfcheck":
        # interface shape only, no network
        ag = build_agent("scripted", "demo", "demo")
        act = ag.decide([], {}, {"keys": ["W", "SPACE"]})
        print(json.dumps(act, ensure_ascii=False))
        return 0
    print("unknown arguments: %r (try --probe or --help)" % (args,))
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
