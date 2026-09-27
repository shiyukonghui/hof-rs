#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""jev_dumb_server.py -- a stdlib-only *dumb* NeoHorse-Jev decision service (TASK-124 D).

Why this exists
---------------
NeoHorse-Jev is a *structured-decision* model (prefill-only), not a chat model: its
native runtime `neohorse-decision serve` exposes exactly three endpoints -- `POST
/v1/decision`, `POST /v1/systemone` and `GET /health` -- and no OpenAI-compatible
endpoint, no `/v1/models`, no GGUF.  The protocol facts this server re-implements come
from TASK-123's read-only research of the vendor's own documentation
(github.com/TokenRhythm/NeoHorse, "NeoHorse Decision API"), quoted in
`recovery/tasks/TASK-124.md` §1:

  * request fields: **only** `model`, `state`, `questions`, `image` (unknown fields are
    rejected);
  * `questions.<key>.type` in `noul` | `choice` | `score`, with `criteria`:
      - `noul`   : optional, only the two keys `false`/`true`; answer is P(true);
      - `choice` : candidate key -> description dict, 1..255 items;
      - `score`  : **ordered** description list (low -> high), 2..255 items
                   (`/v1/systemone` caps at 2..10);
  * answer shapes: choice -> `type`/`choice`/`probabilities`/`confidence`,
    noul -> `type`/`noul` (+ yes/no `probabilities`), score ->
    `type`/`score`/`legend`/`probabilities`/`confidence`;
  * `confidence` is a local distribution statistic, not a calibrated probability
    (choice `(max(p)-1/K)/(1-1/K)`, score `1 - sum_i p_i*|i-argmax|/(L-1)`);
  * response headers `X-NeoHorse-Confidence: local-distribution-statistic-v1` and, for
    `/v1/systemone`, `X-NeoHorse-Usage: local-tokenizer-not-jev-billing`;
  * limits: `state` 2048 tokens, 16 questions/request, 1 MiB body, exactly 1 image + 1
    question on an image request; 401/413/422/429(busy, `Retry-After: 1`)/529.

The server is *dumb*: on `ok` it answers canned values derived from the requested
question keys, so the client's request shape and response parsing can be proven while no
weights exist on this machine.  It also *validates* every request exactly like the real
service would, which is what makes "our constructor never emits an illegal request" a
checkable claim instead of a hope.

Modes (`--mode`)
----------------
  ok          normal: validate, then answer.
  busy        the first `--busy-retries` POSTs return HTTP 429 + `Retry-After: 1`,
              then behave like `ok` -- proves the client's backoff really retries.
  invalid     every POST returns HTTP 422 with a JSON error -- proves the client
              reports the error instead of inventing an action.
  unhealthy   `GET /health` returns HTTP 503 -- proves the client degrades safely.

Run (no redirection, fixed high port; check the port first):

    netstat -ano | findstr :55124
    D:\\Anaconda\\Scripts\\python.exe tools\\tests\\jev_dumb_server.py --mode ok --port 55124

The `--log` option writes the full request/validation log through Python (UTF-8), never
through a shell redirect.
"""

from __future__ import print_function

import argparse
import json
import os
import socket
import sys
import threading
import time

try:
    from http.server import BaseHTTPRequestHandler, HTTPServer
except ImportError:  # pragma: no cover
    raise SystemExit("jev_dumb_server.py needs python 3")


# ---------------------------------------------------------------------------
# the documented protocol surface, as constants
# ---------------------------------------------------------------------------
ALLOWED_REQUEST_FIELDS = ("model", "state", "questions", "image")
ACCEPTED_MODELS = ("neohorse-jev", "NeoHorse-Jev-4B", "NeoHorse-JEV-4B",
                   "TokenRhythm/NeoHorse-Jev-4B")
ANSWER_MODEL = "NeoHorse-Jev-4B"
QUESTION_TYPES = ("noul", "choice", "score")
STATE_MAX_TOKENS = 2048
MAX_QUESTIONS = 16
MAX_BODY_BYTES = 1024 * 1024
SYSTEMONE_SCORE_MAX_LEVELS = 10
SCORE_MAX_LEVELS = 255
CHOICE_MAX_CANDIDATES = 255
DEFAULT_PORT = 55124


def estimate_tokens(text):
    """A conservative token estimate, independent of the client's own copy.

    Basis: BPE tokenizers of this family pack about four ASCII characters per token,
    and a non-ASCII character (CJK is 3 bytes in UTF-8) is charged a full token.  No
    tokenizer is bundled here, so the estimate is deliberately an upper bound -- a
    request that passes it is smaller than the documented limit, never larger.
    """
    ascii_n = 0
    other_n = 0
    for ch in text:
        if ord(ch) < 128:
            ascii_n += 1
        else:
            other_n += 1
    return (ascii_n + 3) // 4 + other_n


def validate_request(payload, path="/v1/systemone"):
    """Return a list of {'field','error'} for every protocol violation found.

    This mirrors the vendor's own checks: unknown request fields are a hard error
    (`unknown = set(request) - {'model','state','questions','image'}`), and the
    per-question `criteria` cardinalities are enforced per type and per endpoint.
    """
    errs = []

    def bad(field, error):
        errs.append({"field": field, "error": error})

    if not isinstance(payload, dict):
        bad("$", "the request body must be a JSON object")
        return errs

    unknown = sorted(set(payload) - set(ALLOWED_REQUEST_FIELDS))
    if unknown:
        bad("$", "Unknown request fields: %s" % unknown)

    model = payload.get("model")
    if model is not None and model not in ACCEPTED_MODELS:
        bad("model", "unknown model %r; accepted: %s" % (model, list(ACCEPTED_MODELS)))

    state = payload.get("state")
    if state is None:
        bad("state", "`state` is required")
    elif not isinstance(state, (str, dict, list)):
        bad("state", "`state` must be a string, object or array (got %s)"
                      % type(state).__name__)
    else:
        rendered = state if isinstance(state, str) else json.dumps(state, ensure_ascii=False)
        n = estimate_tokens(rendered)
        if n > STATE_MAX_TOKENS:
            bad("state", "state is ~%d tokens, over the %d-token limit" % (n, STATE_MAX_TOKENS))

    questions = payload.get("questions")
    if not isinstance(questions, dict) or not questions:
        bad("questions", "`questions` must be a non-empty object")
    else:
        if len(questions) > MAX_QUESTIONS:
            bad("questions", "%d questions, over the %d-per-request limit"
                             % (len(questions), MAX_QUESTIONS))
        for key, q in questions.items():
            where = "questions.%s" % key
            if not isinstance(q, dict):
                bad(where, "a question must be an object")
                continue
            qtype = q.get("type")
            if qtype not in QUESTION_TYPES:
                bad(where + ".type", "unknown question type %r; expected one of %s"
                                     % (qtype, list(QUESTION_TYPES)))
                continue
            criteria = q.get("criteria")
            if qtype == "noul":
                if criteria is not None:
                    if not isinstance(criteria, dict):
                        bad(where + ".criteria", "noul criteria must be an object")
                    else:
                        allowed = set(criteria) - {"false", "true"}
                        if allowed:
                            bad(where + ".criteria",
                                "noul criteria only allows the keys 'false'/'true'; got %s"
                                % sorted(allowed))
            elif qtype == "choice":
                if not isinstance(criteria, dict) or not criteria:
                    bad(where + ".criteria",
                        "choice criteria must be a non-empty candidate dict")
                elif len(criteria) > CHOICE_MAX_CANDIDATES:
                    bad(where + ".criteria", "choice has %d candidates, over the %d limit"
                                             % (len(criteria), CHOICE_MAX_CANDIDATES))
            elif qtype == "score":
                if not isinstance(criteria, list):
                    bad(where + ".criteria", "score criteria must be an ordered list")
                else:
                    hi = SYSTEMONE_SCORE_MAX_LEVELS if path.endswith("systemone") \
                        else SCORE_MAX_LEVELS
                    if not (2 <= len(criteria) <= hi):
                        bad(where + ".criteria",
                            "score needs 2..%d ordered levels, got %d" % (hi, len(criteria)))

    image = payload.get("image")
    if image is not None:
        if not isinstance(image, str) or not image:
            bad("image", "`image` must be a non-empty data: URI or a local path string")
        elif not (image.startswith("data:image/png;base64,")
                  or image.startswith("data:image/jpeg;base64,")):
            bad("image", "`image` must be a data:image/png;base64 or "
                         "data:image/jpeg;base64 URI (no remote URLs, no server paths)")
        if isinstance(questions, dict) and len(questions) != 1:
            bad("image", "an image request carries exactly 1 question, got %d"
                         % len(questions))

    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    if len(body) > MAX_BODY_BYTES:
        bad("$", "request body is %d bytes, over the 1 MiB limit" % len(body))

    return errs


def canonical_answers(questions):
    """Canned answers derived from the requested keys/types.

    The values are fixed on purpose: the client-side test asserts that exactly these
    numbers come back out of the parser, so parsing and evidence capture are proven,
    not the model (there is no model here).
    """
    answers = {}
    for key, q in (questions or {}).items():
        qtype = (q or {}).get("type")
        if qtype == "choice":
            cands = list((q.get("criteria") or {}).keys())
            first = cands[0] if cands else "noop"
            probs = {}
            for i, c in enumerate(cands):
                probs[c] = round(1.0 / (i + 1.5), 6)
            total = sum(probs.values()) or 1.0
            probs = {c: round(v / total, 6) for c, v in probs.items()}
            p_max = max(probs.values()) if probs else 0.0
            k = max(1, len(cands))
            conf = (p_max - 1.0 / k) / (1.0 - 1.0 / k) if k > 1 else 0.0
            answers[key] = {"type": "choice", "choice": first, "probabilities": probs,
                            "confidence": round(conf, 6)}
        elif qtype == "noul":
            answers[key] = {"type": "noul", "noul": 0.75,
                            "probabilities": {"false": 0.25, "true": 0.75}}
        elif qtype == "score":
            levels = q.get("criteria") or []
            n = max(1, len(levels))
            probs = {}
            for i, label in enumerate(levels):
                probs[str(label)] = round(1.0 / n, 6)
            # expected level 2.5 on a 0-based index scale; `legend` echoes the order
            answers[key] = {"type": "score", "score": 2.5, "legend": list(levels),
                            "probabilities": probs, "confidence": 0.5}
    return answers


class DumbJevConfig(object):
    def __init__(self, mode="ok", busy_retries=1, retry_after=1):
        self.mode = mode
        self.busy_retries = int(busy_retries)
        self.retry_after = int(retry_after)
        self.requests = []          # every request, with headers and validation result
        self.post_count = 0
        self.lock = threading.Lock()


def _make_handler(cfg):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *a):  # keep the console clean; requests go to cfg.requests
            pass

        # ---- helpers -----------------------------------------------------
        def _send(self, status, payload, extra_headers=None, raw=None):
            body = raw if raw is not None else json.dumps(payload, ensure_ascii=False,
                                                          indent=1).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            for k, v in (extra_headers or {}).items():
                self.send_header(k, str(v))
            self.end_headers()
            self.wfile.write(body)

        def _record(self, method, payload, errors, status, headers):
            with cfg.lock:
                cfg.requests.append({
                    "n": len(cfg.requests) + 1, "method": method, "path": self.path,
                    "headers": {k.lower(): v for k, v in self.headers.items()},
                    "payload": payload, "validation_errors": errors,
                    "responded_status": status, "responded_headers": headers,
                })

        # ---- GET ---------------------------------------------------------
        def do_GET(self):
            if self.path == "/health":
                status = 503 if cfg.mode == "unhealthy" else 200
                payload = ({"status": "unavailable", "error": "dumb server: unhealthy mode"}
                           if status != 200 else
                           {"status": "ready", "model": ANSWER_MODEL,
                            "input_modalities": ["text", "image"],
                            "endpoints": ["/v1/decision", "/v1/systemone", "/health"]})
                self._record("GET", None, [], status, {})
                self._send(status, payload)
                return
            # /v1/models is deliberately NOT provided (the vendor says so, and the
            # client must never call it): answering 404 turns that into evidence.
            self._record("GET", None, [], 404, {})
            self._send(404, {"error": "not found", "detail":
                             "only /health, /v1/decision and /v1/systemone exist"})

        # ---- POST --------------------------------------------------------
        def do_POST(self):
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b""
            try:
                payload = json.loads(raw.decode("utf-8", "replace") or "{}")
            except Exception as e:  # noqa: BLE001
                payload = {"_unparsable": raw[:200].decode("utf-8", "replace"),
                           "_error": str(e)}
            errors = validate_request(payload, self.path)

            if self.path not in ("/v1/systemone", "/v1/decision"):
                self._record("POST", payload, errors, 404, {})
                self._send(404, {"error": "not found", "path": self.path})
                return

            if cfg.mode == "invalid":
                self._record("POST", payload, errors, 422, {})
                self._send(422, {"error": "unprocessable",
                                 "detail": "dumb server: simulated 422 (invalid mode)"})
                return

            if errors:
                self._record("POST", payload, errors, 422, {})
                self._send(422, {"error": "unprocessable", "detail": errors})
                return

            if cfg.mode == "busy":
                with cfg.lock:
                    cfg.post_count += 1
                    attempt = cfg.post_count
                if attempt <= cfg.busy_retries:
                    headers = {"Retry-After": cfg.retry_after}
                    self._record("POST", payload, [], 429, headers)
                    self._send(429, {"error": "worker busy",
                                     "detail": "dumb server: simulated 429 on attempt %d"
                                               % attempt},
                               extra_headers=headers)
                    return

            questions = payload.get("questions") or {}
            answers = canonical_answers(questions)
            state = payload.get("state")
            rendered = state if isinstance(state, str) else json.dumps(state, ensure_ascii=False)
            input_tokens = estimate_tokens(rendered)
            usage = {"input_tokens": input_tokens, "output_tokens": 0, "image_tokens": 0}
            body = {"model": ANSWER_MODEL, "answers": answers, "usage": usage}
            if self.path.endswith("/decision"):
                body = {"model": ANSWER_MODEL, "answers": answers,
                        "input_tokens": input_tokens}
            headers = {"X-NeoHorse-Confidence": "local-distribution-statistic-v1"}
            if self.path.endswith("/systemone"):
                headers["X-NeoHorse-Usage"] = "local-tokenizer-not-jev-billing"
            self._record("POST", payload, [], 200, headers)
            self._send(200, body, extra_headers=headers)

    return Handler


class DumbJevServer(object):
    """A threaded HTTP server wrapping the dumb handler; usable from tests."""

    def __init__(self, port=DEFAULT_PORT, host="127.0.0.1", mode="ok", busy_retries=1,
                 retry_after=1):
        self.host = host
        self.port = int(port)
        self.cfg = DumbJevConfig(mode=mode, busy_retries=busy_retries,
                                 retry_after=retry_after)
        self._srv = None
        self._thread = None

    @property
    def url(self):
        return "http://%s:%d" % (self.host, self.port)

    def start(self):
        handler = _make_handler(self.cfg)
        self._srv = HTTPServer((self.host, self.port), handler)
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
    ap = argparse.ArgumentParser(description="dumb NeoHorse-Jev decision service (TASK-124)")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--mode", default="ok", choices=("ok", "busy", "invalid", "unhealthy"))
    ap.add_argument("--busy-retries", type=int, default=1)
    ap.add_argument("--retry-after", type=int, default=1)
    ap.add_argument("--log", default="", help="write the request log to this JSON file")
    ap.add_argument("--seconds", type=float, default=0.0,
                    help="serve for N seconds then exit (0 = until Ctrl+C)")
    args = ap.parse_args(argv)

    if not port_status(args.port, args.host):
        print("REFUSING TO START: %s:%d is already in use -- pick another 5xxxx port "
              "after `netstat -ano | findstr :%d`" % (args.host, args.port, args.port))
        return 3

    srv = DumbJevServer(port=args.port, host=args.host, mode=args.mode,
                        busy_retries=args.busy_retries, retry_after=args.retry_after)
    srv.start()
    print("dumb jev server: %s  mode=%s  (endpoints: GET /health, POST /v1/systemone, "
          "POST /v1/decision; /v1/models is deliberately 404)" % (srv.url, args.mode))
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
