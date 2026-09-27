#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""playjev_dumb_server.py -- a stdlib-only *dumb* PlayJev /v1/systemone service (TASK-127).

Why this exists
---------------
PlayJev 0.8B ships its own server, `playjev/serve.py`, and exposes `POST /v1/systemone`
plus `GET /health` -- the same endpoint *names* as NeoHorse-Jev, with a DIFFERENT request
shape.  The protocol facts this dumb server re-implements are transcribed from the
deployed source at commit `ea3a514d2fcbc0756c36eabe052439db54544542`
(`github.com/OmniJev/PlayJev`, `playjev/serve.py`), and every rule below quotes the line
it comes from:

  * `POST /v1/systemone` is the ONLY decision endpoint; anything else is 404
    `{"error": "not found"}` (serve.py:111-112);
  * the state must be `{"frames": [...]}` with at least one frame; a *text* state is
    refused: `'state must be {"frames": [...]} with at least one frame; text states
    belong to OpenJev'` (serve.py:41-42);
  * each frame is a non-empty base64 string or a `data:` URL; a non-string frame is a
    ValueError -> 400 (serve.py:32-37, 120-121);
  * `questions` must be a non-empty object (serve.py:49-50);
  * every question must have `type` absent-or-`"choice"`: `'only type "choice" is
    served'` (serve.py:53-54) -- so a `noul` or `score` question, both legal on Jev, is
    a 400 here;
  * `criteria` must be a dict (name -> description) or a list (name == description),
    with at least two options (serve.py:55-63); the alphabet caps it at 26
    (`playjev/model.py:38`);
  * the answer is `{"model", "answers": {q: {"type", "choice", "probabilities",
    "confidence"}}, "timing"}` (serve.py:69-74, plus `total_ms` at serve.py:118), where
    `confidence` is the Jev Choice statistic `(p_max - 1/K) / (1 - 1/K)`
    (`playjev/model.py:90-94`);
  * a `ValueError` becomes 400 with `{"error": ...}` and any other exception becomes 500
    with `{"error": "<type>: <msg>"}` (serve.py:120-123);
  * `GET /health` is `{"ok": true, "model", "two_frame"}` (serve.py:105-106) -- NOT
    Jev's `{"status": "ready", ...}`;
  * `GET /v1/models` IS provided (serve.py:103-104), unlike Jev;
  * CORS is open (serve.py:94-100).

Two facts the dumb server *deliberately does not implement* and the tests assert as
ABSENCES, because they are the real protocol traps:

  * there is no `abstain` field anywhere in serve.py -- neither accepted nor emitted;
  * the request's `model` field is never read by serve.py (the reply echoes the
    `--name` the server was started with).

The server is *dumb*: on `ok` it answers canned numbers derived from the requested
options, so the client's request construction and response mapping are provable with no
weights and no GPU.  Modes:

  ok        validate, then answer every question (and the canned numbers are chosen to
            PASS the agent's default thresholds, so "the happy path is a pass" is a
            checkable claim).
  abstain   200, but EVERY question abstains -- proves an abstain on the ACTION
            question degrades to `wait` and is recorded as a reason, never as success.
  abstain_score
            200, but only the LAST question (the score) abstains -- proves an abstain
            outside the action leaves the action usable while the VERDICT becomes
            "no verdict" (pass: null), never a pass.
  noanswer  200, but the answer object omits one requested question entirely -- proves a
            MISSING answer is classified as an abstain too.
  invalid   every POST is 400 `{"error": "unprocessable"}`.
  broken    200 with a non-JSON body -- proves a parse failure is reported, not invented.
  unhealthy GET /health is 503.

Run (no redirection, fixed high port; check the port first):

    netstat -ano | findstr :55127
    python tools\\tests\\playjev_dumb_server.py --mode ok --port 55127

The `--log` option writes the full request/validation log through Python (UTF-8), never
through a shell redirect.
"""

from __future__ import print_function

import argparse
import base64
import binascii
import json
import os
import socket
import sys
import threading
import time

try:
    from http.server import BaseHTTPRequestHandler, HTTPServer
except ImportError:  # pragma: no cover
    raise SystemExit("playjev_dumb_server.py needs python 3")


# ---------------------------------------------------------------------------
# the deployed protocol surface, as constants (serve.py line refs in the docstring)
# ---------------------------------------------------------------------------
ALLOWED_REQUEST_FIELDS = ("model", "state", "questions")
ANSWER_MODEL = "playjev-0.8b"
DECISION_PATH = "/v1/systemone"
HEALTH_PATH = "/health"
MODELS_PATH = "/v1/models"
DEFAULT_INSTRUCTIONS = "Which move should the player make next?"  # model.py:37
MIN_OPTIONS = 2                                                  # serve.py:62
MAX_OPTIONS = 26                                                 # model.py:38 LETTERS
DEFAULT_PORT = 55127


def choice_confidence(probs):
    """The Jev Choice statistic, verbatim from playjev/model.py:90-94."""
    k = len(probs)
    if k == 1:
        return 1.0
    return (max(probs) - 1.0 / k) / (1.0 - 1.0 / k)


def options_of(criteria):
    """`criteria` -> the option name list, exactly as serve.py:55-63 builds it."""
    if isinstance(criteria, dict):
        return [str(k) for k in criteria]
    if isinstance(criteria, list):
        return [str(k) for k in criteria]
    return None


def validate_request(payload, path=DECISION_PATH):
    """Return a list of {'field','error'} for every violation serve.py would raise.

    The distinction that matters: a `ValueError` in serve.py is a 400, anything else is
    a 500.  So a non-string frame and a bad `criteria` type are *400*s, while a frame
    that is a string but not decodable base64 raises `binascii.Error` -- a 500.  Both
    are modelled here so the client cannot accidentally depend on the wrong status.
    """
    errs = []

    def bad(field, error, status=400):
        errs.append({"field": field, "error": error, "status": status})

    if not isinstance(payload, dict):
        bad("$", "the request body must be a JSON object")
        return errs

    unknown = sorted(set(payload) - set(ALLOWED_REQUEST_FIELDS))
    if unknown:
        # serve.py ignores extra fields rather than rejecting them; recorded, not an
        # error, so the difference from Jev (which rejects unknown fields) is explicit.
        errs.append({"field": "$", "error": "note: serve.py ignores unknown request "
                                            "fields %s (Jev would reject them)" % unknown,
                     "status": None, "severity": "note"})

    state = payload.get("state")
    frames = state.get("frames") if isinstance(state, dict) else None
    if not isinstance(state, dict) or not isinstance(frames, list) or not frames:
        bad("state", 'state must be {"frames": [...]} with at least one frame; '
                     'text states belong to OpenJev')
        return errs
    for i, f in enumerate(frames):
        if not isinstance(f, str) or not f:
            bad("state.frames[%d]" % i,
                "each frame must be a base64 string or a data URL")
            continue
        s = f
        if s.startswith("data:"):
            s = s.split(",", 1)[1] if "," in s else ""
        try:
            base64.b64decode(s, validate=True)
        except (binascii.Error, ValueError) as e:
            bad("state.frames[%d]" % i,
                "base64 decode failed (%s: %s) -- serve.py answers 500 for this"
                % (type(e).__name__, e), status=500)

    questions = payload.get("questions")
    if not isinstance(questions, dict) or not questions:
        bad("questions", "questions must be a non-empty object")
        return errs
    for key, q in questions.items():
        where = "questions.%s" % key
        if not isinstance(q, dict):
            bad(where, "a question must be an object")
            continue
        if q.get("type", "choice") != "choice":
            bad(where + ".type", 'only type "choice" is served')
            continue
        opts = options_of(q.get("criteria"))
        if opts is None:
            bad(where + ".criteria", "criteria must be an object or a list")
            continue
        if len(opts) < MIN_OPTIONS:
            bad(where + ".criteria", "a choice needs at least two options")
        elif len(opts) > MAX_OPTIONS:
            bad(where + ".criteria", "%d options exceed the %d letter slots"
                % (len(opts), MAX_OPTIONS))
    return errs


def canonical_answers(questions, mode="ok"):
    """Canned answers derived from the requested options.

    `ok` numbers are chosen so the agent's DEFAULT thresholds pass:
      * the action question's first option wins with a modest confidence;
      * a yes/no question (the agent's `noul`) gets P(yes) = 0.8 >= 0.5;
      * the ordered-levels question (the agent's `score`) leans on level 1, giving an
        expected level near 1.4 <= 2.5.
    """
    answers = {}
    keys = list((questions or {}).keys())
    for key, q in (questions or {}).items():
        opts = options_of((q or {}).get("criteria")) or []
        if not opts:
            continue
        n = len(opts)
        if mode == "abstain" or (mode == "abstain_score" and key == keys[-1]):
            # `abstain` : every question abstains (the ACTION question included).
            # `abstain_score`: only the LAST question (the score) abstains, so the
            # action is still answerable -- the two cases exercise different branches.
            answers[key] = {"type": "choice", "abstain": True,
                            "choice": None, "probabilities": {}, "confidence": 0.0}
            continue
        if opts == ["yes", "no"]:
            probs = {"yes": 0.8, "no": 0.2}
        elif key == keys[-1] and n >= 3:
            # ordered brokenness levels: mostly level 1, a little spread
            probs = {}
            for i, name in enumerate(opts):
                probs[name] = round(0.7 if i == 0 else 0.3 / (n - 1), 6)
            total = sum(probs.values())
            probs = {k: round(v / total, 6) for k, v in probs.items()}
        else:
            probs = {name: round(1.0 / (i + 1.5), 6) for i, name in enumerate(opts)}
            total = sum(probs.values())
            probs = {k: round(v / total, 6) for k, v in probs.items()}
        answers[key] = {"type": "choice", "choice": opts[0],
                        "probabilities": probs,
                        "confidence": round(choice_confidence(list(probs.values())), 6)}
    if mode == "noanswer" and keys:
        answers.pop(keys[0], None)
    return answers


class DumbPlayJevConfig(object):
    def __init__(self, mode="ok", name=ANSWER_MODEL, two_frame=False):
        self.mode = mode
        self.name = name
        self.two_frame = two_frame
        self.requests = []
        self.lock = threading.Lock()


def _make_handler(cfg):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *a):  # requests go to cfg.requests
            pass

        def _cors(self):
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

        def _send(self, status, payload=None, raw=None):
            body = raw if raw is not None else json.dumps(payload or {}).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self._cors()
            self.end_headers()
            self.wfile.write(body)

        def _record(self, method, payload, errors, status):
            with cfg.lock:
                cfg.requests.append({
                    "n": len(cfg.requests) + 1, "method": method, "path": self.path,
                    "headers": {k.lower(): v for k, v in self.headers.items()},
                    "payload": payload,
                    "validation_errors": [e for e in errors if e.get("status")],
                    "validation_notes": [e for e in errors if not e.get("status")],
                    "responded_status": status,
                })

        def do_OPTIONS(self):
            self.send_response(204)
            self.send_header("Content-Length", "0")
            self._cors()
            self.end_headers()

        def do_GET(self):
            if self.path.rstrip("/") == MODELS_PATH:
                self._record("GET", None, [], 200)
                self._send(200, {"object": "list",
                                 "data": [{"id": cfg.name, "object": "model",
                                           "owned_by": "playjev"}]})
                return
            if self.path.rstrip("/") in ("", HEALTH_PATH):
                status = 503 if cfg.mode == "unhealthy" else 200
                self._record("GET", None, [], status)
                if status != 200:
                    self._send(503, {"ok": False, "error": "dumb server: unhealthy mode"})
                else:
                    self._send(200, {"ok": True, "model": cfg.name,
                                     "two_frame": cfg.two_frame})
                return
            self._record("GET", None, [], 404)
            self._send(404, {"error": "not found"})

        def do_POST(self):
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b""
            try:
                payload = json.loads(raw.decode("utf-8", "replace") or "{}")
            except Exception as e:  # noqa: BLE001
                payload = {"_unparsable": raw[:200].decode("utf-8", "replace"),
                           "_error": str(e)}
            if self.path.rstrip("/") != DECISION_PATH:
                self._record("POST", payload, [], 404)
                self._send(404, {"error": "not found"})
                return
            errors = validate_request(payload, self.path)
            hard = [e for e in errors if e.get("status")]

            if cfg.mode == "invalid":
                self._record("POST", payload, errors, 400)
                self._send(400, {"error": "dumb server: simulated 400 (invalid mode)"})
                return

            if hard:
                status = 500 if any(e["status"] == 500 for e in hard) else 400
                self._record("POST", payload, errors, status)
                detail = "; ".join(e["error"] for e in hard)
                self._send(status, {"error": detail if status == 400
                                    else "binascii.Error: %s" % detail})
                return

            if cfg.mode == "broken":
                self._record("POST", payload, errors, 200)
                self._send(200, raw=b"this is not json {")
                return

            answers = canonical_answers(payload.get("questions") or {}, cfg.mode)
            body = {"model": cfg.name, "answers": answers,
                    "timing": {"prep_ms": 1.0, "forward_ms": 2.0, "input_tokens": 100,
                               "visual_tokens": 64, "total_ms": 3.0}}
            self._record("POST", payload, errors, 200)
            self._send(200, body)

    return Handler


class DumbPlayJevServer(object):
    """A threaded HTTP server wrapping the dumb handler; usable from tests."""

    def __init__(self, port=DEFAULT_PORT, host="127.0.0.1", mode="ok",
                 name=ANSWER_MODEL, two_frame=False):
        self.host = host
        self.port = int(port)
        self.cfg = DumbPlayJevConfig(mode=mode, name=name, two_frame=two_frame)
        self._srv = None
        self._thread = None

    @property
    def url(self):
        return "http://%s:%d" % (self.host, self.port)

    def start(self):
        self._srv = HTTPServer((self.host, self.port), _make_handler(self.cfg))
        self.port = self._srv.server_address[1]
        self._thread = threading.Thread(target=self._srv.serve_forever)
        self._thread.daemon = True
        self._thread.start()
        return self

    def stop(self):
        if self._srv is not None:
            self._srv.shutdown()
            self._srv.server_close()
            self._srv = None
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None

    @property
    def requests(self):
        return list(self.cfg.requests)

    @property
    def validation_errors(self):
        out = []
        for r in self.cfg.requests:
            for e in r.get("validation_errors") or []:
                out.append(dict(e, request_n=r["n"], path=r["path"]))
        return out


def port_status(port, host="127.0.0.1"):
    """True when the port is free to bind (checked with a real bind, not a guess)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, int(port)))
        return True
    except OSError:
        return False
    finally:
        s.close()


def main(argv=None):
    ap = argparse.ArgumentParser(description="dumb PlayJev /v1/systemone service (TASK-127)")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--mode", default="ok",
                    choices=("ok", "abstain", "abstain_score", "noanswer", "invalid",
                             "broken", "unhealthy"))
    ap.add_argument("--name", default=ANSWER_MODEL)
    ap.add_argument("--two-frame", action="store_true")
    ap.add_argument("--log", default="", help="write the request log to this JSON file")
    ap.add_argument("--seconds", type=float, default=0.0,
                    help="serve for N seconds then exit (0 = until Ctrl+C)")
    args = ap.parse_args(argv)

    if not port_status(args.port, args.host):
        print("REFUSING TO START: %s:%d is already in use -- pick another 5xxxx port "
              "after `netstat -ano | findstr :%d`" % (args.host, args.port, args.port))
        return 3

    srv = DumbPlayJevServer(port=args.port, host=args.host, mode=args.mode,
                            name=args.name, two_frame=args.two_frame)
    srv.start()
    print("dumb playjev server: %s  mode=%s  (endpoints: GET /health, GET /v1/models, "
          "POST /v1/systemone; choice questions over state.frames only)"
          % (srv.url, args.mode))
    t0 = time.time()
    try:
        while True:
            time.sleep(0.2)
            if args.seconds and (time.time() - t0) >= args.seconds:
                break
    except KeyboardInterrupt:
        pass
    finally:
        srv.stop()
    log = {"url": srv.url, "mode": args.mode, "requests": srv.requests}
    if args.log:
        with open(args.log, "w", encoding="utf-8") as fh:
            json.dump(log, fh, ensure_ascii=False, indent=1)
        print("request log written to %s" % os.path.abspath(args.log))
    print(json.dumps(log, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
