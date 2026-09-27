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
  jev      : NeoHorse-Jev's *native* structured-decision protocol (TASK-124).  Jev
             is not a chat model; see the next section.  It posts typed questions
             (`noul` / `choice` / `score`) to `POST <base>/v1/systemone` (or
             `/v1/decision`), checks readiness with `GET <base>/health`, and maps the
             answers back to the same action dict the other backends return.
  playjev  : PlayJev 0.8B's image-state decision server (TASK-127), the *vision
             fine-tuned* sibling of Jev.  Same endpoint name (`POST /v1/systemone`,
             `GET /health`) but a DIFFERENT request shape: the state is
             `{"frames": ["data:image/png;base64,..."]}` and every question must be
             `type: "choice"` -- PlayJev serves no `noul`/`score` question type and no
             text state (both are HTTP 400).  This backend therefore expresses the
             invariants as yes/no Choices and the brokenness rating as an
             ordered-levels Choice with an expected value, and it treats an absent or
             unusable answer as an ABSTAIN (never as a success).  It is the backend to
             use when the question is about the PIXELS; `jev` is the text-state one.

    env var                meaning                        example
    ---------------------  -----------------------------  ------------------------------
    PLAYTEST_BASE_URL      root URL of the model server   http://127.0.0.1:8080
                           (`jev`: a ROOT url -- the path  (no /v1 suffix for jev)
                            is /v1/systemone by default)    http://127.0.0.1:8081
                                                            for `playjev`
    PLAYTEST_API_KEY       bearer token (may be empty)    sk-local
    PLAYTEST_MODEL         model name                     NeoHorse-Jev-4B
                                                          (playjev: cosmetic -- its
                                                           serve.py ignores the field)
    PLAYTEST_DECISION_PATH jev decision endpoint           /v1/systemone
    PLAYTEST_STATE_OVERFLOW  error | clip                 error
    PLAYTEST_ABSTAIN_MIN_CONFIDENCE  playjev: a confidence below this is an
                                     abstain (0 = off; the declared-abstain and
                                     missing-answer rules are always on)   0

NeoHorse-Jev is NOT an OpenAI model (corrected in TASK-124)
-----------------------------------------------------------
Jev (ModelScope `TokenRhythm/NeoHorse-Jev-4B`; source github.com/TokenRhythm/NeoHorse)
is a *structured decision* model: prefill-only, it generates no text, it is not a chat
causal LM, it ships no GGUF, and the vendor explicitly documents that **its server has no
OpenAI-compatible endpoint** ("Only the endpoints and protocol scope described here are
supported; `/v1/models` is not provided.").  So `--agent=openai` pointed at Jev cannot
work.  Earlier revisions of this header told you to start Jev either through an
OpenAI-compatible launcher (vLLM's `api_server` with a Jev model id) or through a
`llama-server` GGUF launch -- **both are impossible for Jev** (no chat causal LM, no
GGUF: `model_manifest.json` says "unified multimodal backbone + independent decision
pointer head; NOT chat causal LM").  Those two wrong recipes are replaced by the two
real paths (commands verbatim from the vendor's documentation, read as first-party
sources in TASK-123; see `recovery/tasks/TASK-124.md` §1):

    :: A. NeoHorse-Jev through its native runtime -- the supported path (text, or
    ::    text + exactly one image).  Source: NeoHorse README / decision API docs.
    neohorse-decision serve --model-dir "<MODEL_DIR>" --port 8080
    ::    endpoints: GET /health, POST /v1/decision, POST /v1/systemone.
    ::    No /v1/models, no /v1/chat/completions, no GGUF, no quantised Jev.
    ::    Weights: ModelScope TokenRhythm/NeoHorse-Jev-4B (Apache-2.0, ~9.15 GB).
    ::    HuggingFace is UNREACHABLE from this machine (measured HTTP 000 / connect
    ::    timeout); the vendor's recorded runtime is Linux (python 3.12 / torch 2.8 /
    ::    CUDA 12.8); Windows feasibility on this box is UNVERIFIED and is a pending
    ::    user decision.  TASK-124 downloads no weights.
    set PLAYTEST_BASE_URL=http://127.0.0.1:8080
    set PLAYTEST_MODEL=NeoHorse-Jev-4B
    D:\\Anaconda\\Scripts\\python.exe tools\\playability_gate.py --games pong --agent=jev

    :: B. Alternative: the vLLM 0.28.0 *pooling* adapter -- the decision head is
    ::    computed on the client's CPU (`infer.py` posts /pooling for token embeddings)
    CUDA_VISIBLE_DEVICES=0 python infer/vllm/launch.py --bundle /path/to/model --port 30000

    :: --agent=openai remains available, but ONLY for a model that really speaks
    :: OpenAI chat-completions -- e.g. the sibling NeoHorse-1-4B/9B (text-only, real
    :: /v1/chat/completions, GGUF quantisations exist).  It is not a Jev path.

    That is *all* the coupling there is: the backend speaks/consumes JSON over
    HTTP and nothing in the gate knows the model's name.  A vision-less model
    still works -- the state JSON is always sent and the images become optional
    when `--no-images` is passed.  For `jev`, images are opt-in (there the vendor's own
    numbers say the text state is the strong path and the vision head is weak), and an
    image request is limited to exactly one question, one image.

Self-test without any model
---------------------------
    python tools\\playtest_agent.py --probe
        starts a *dumb* OpenAI-compatible server on 127.0.0.1 (one endpoint that
        answers a canned completion, one that answers HTTP 500) and exercises the
        openai backend against both, so the transport is proven while a real
        model is absent.  Exit code 0 means: request built, auth header sent,
        image part attached, JSON action extracted, server error reported as an
        error (and *not* as a silent success).

    python tools\\tests\\test_jev_agent.py
        the same idea for the `jev` backend: `tools/tests/jev_dumb_server.py` is a
        stdlib dumb `/v1/systemone` + `/health` service that VALIDATES every request
        against the documented protocol (unknown fields, question cardinalities, the
        2048-token `state` limit, the 1-image/1-question rule) and can replay 429 +
        `Retry-After: 1`, 422 and an unhealthy `/health`.  Evidence is written to
        `runs/playability/agent-probe-jev.json`.  No weights, no GPU, stdlib only.
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
# backend 3: jev -- NeoHorse-Jev's NATIVE structured-decision protocol (TASK-124)
# ---------------------------------------------------------------------------
# Every protocol constant below is a first-party fact from TASK-123's read-only
# research of the vendor documentation (URL + HTTP 200; verbatim excerpts in
# recovery/tasks/TASK-124.md §1).  In particular:
#   * the server has exactly three endpoints: POST /v1/decision, POST /v1/systemone,
#     GET /health -- and "/v1/models is not provided";
#   * the request fields are ONLY model/state/questions/image; unknown fields raise
#     `ValueError('Unknown request fields: ...')`;
#   * question types are noul | choice | score, with per-type `criteria` rules;
#   * confidence is a local distribution statistic, NOT a calibrated probability;
#   * limits: state 2048 tokens, 16 questions/request, 1 MiB body, exactly 1 image +
#     1 question per image request; busy => 429/529 + `Retry-After: 1`;
#   * no dynamic batching: "HTTP text and image requests share the same backbone,
#     decision head, and GPU lock, without dynamic batching." => serialize.
JEV_ANSWER_MODEL = "NeoHorse-Jev-4B"
JEV_ACCEPTED_MODELS = ("neohorse-jev", "NeoHorse-Jev-4B", "NeoHorse-JEV-4B",
                       "TokenRhythm/NeoHorse-Jev-4B")
JEV_HEALTH_PATH = "/health"
JEV_DECISION_PATHS = ("/v1/systemone", "/v1/decision")
JEV_LIMITS = {
    "state_max_tokens": 2048,
    "branch_max_tokens": 8192,
    "request_max_tokens": 32768,
    "max_questions": 16,
    "request_max_bytes": 1048576,          # 1 MiB
    "image_request_max_bytes": 8388608,    # 8 MiB
    "image_decoded_max_bytes": 4194304,    # 4 MiB
    "image_max_pixels": 4194304,
    "image_max_tokens": 1024,
    "image_request_max_tokens": 12288,
    "choice_max_candidates": 255,
    "score_min_levels": 2,
    "score_max_levels_decision": 255,
    "score_max_levels_systemone": 10,      # /v1/systemone caps score at 2..10
}

# The default text request: one action choice + N invariants + one score question.
# "Does this frame clearly look playable, with no visual corruption or freeze?"
JEV_INVARIANT_QUESTIONS = [
    ("playable_frame",
     "Does this frame clearly look playable, with no visual corruption or freeze?"),
    ("no_render_failure",
     "Is the frame free of an error dialog, a blank/flat screen, or an obvious "
     "rendering failure?"),
    ("responds_to_input",
     "Did the game visibly respond to the last injected input (its exported state or "
     "its pixels changed)?"),
    ("loop_running",
     "Is the game loop still running, i.e. the screen is not frozen on the same frame "
     "count?"),
]
# score criteria is an ORDERED list, low -> high.  Here the ordering is brokenness,
# so the expected level is an upper bound: lower is better.
JEV_BROKENNESS_LEVELS = [
    "1 = fully working: content is drawn, input responds, nothing looks wrong",
    "2 = minor glitches only; still clearly playable",
    "3 = partially broken: some documented capability is missing or unresponsive",
    "4 = badly broken: the game barely responds or renders garbage",
    "5 = unusable: flat/blank screen, error dialog, or frozen",
]

# Thresholds are PRIOR values and are explicitly NOT calibrated.  The vendor reports
# no calibration and warns: "NLL, Brier, and ECE calibration results have not been
# reported. Set thresholds on an independent dataset."  TASK-124 §C wires these into
# the gate as *configurable* values and documents the labelling plan (our 20 fixed
# games = positive, dist/exe-task109-pre-fix = negative) in TASK-124-REPORT.md.
DEFAULT_JEV_THRESHOLDS = {
    "noul_min_p_true": 0.5,       # every invariant's P(true) must be >= this
    "score_max_expected": 2.5,    # expected brokenness level must be <= this
}
JEV_THRESHOLD_NOTE = (
    "PRIOR ONLY, NOT CALIBRATED. The vendor reports no NLL/Brier/ECE calibration for "
    "NeoHorse-Jev and warns: 'Set thresholds on an independent dataset.' Replace these "
    "defaults with thresholds fitted on our own labelled frames (positives: the 20 "
    "fixed games; negatives: dist/exe-task109-pre-fix, the pre-fix builds whose input "
    "was disabled) before any threshold is treated as a verdict."
)


class JevProtocolError(Exception):
    """A request that must not be sent (or an answer that cannot be trusted)."""


JEV_TOKEN_SAFETY_FACTOR = 2.5
# TASK-129 D-C.  The pre-TASK-129 estimator claimed to be an upper bound and was not:
# the service's own `usage.input_tokens` says this JSON tokenizes 2.12-2.36x denser.
# Measured on the deployed service (TASK-128 §3.1, verbatim in TASK-129's report):
#
#     breakout    client_raw 1018 -> service 2160   ratio 2.12   (HTTP 200 after trim)
#     breakout    client_raw 1800 -> service 2172   ratio 1.21   (trimmed)
#     bomberman   client_raw 1791 -> service 4229   ratio 2.36   (the worst case)
#     pong        client_raw  431 -> accepted 200
#
# The coefficient is the worst measured ratio rounded UP (2.36 -> 2.5), so the estimate
# stays on the safe side of the service's 2048-token `state` cap.  It is a SEPARATION
# coefficient fitted on the service's own counter, not a tokenizer: this machine has no
# Jev tokenizer.  What it buys is that the client guard now refuses the requests the
# service really refuses, and that the 422 auto-halving retry (see `JevAgent.decide`)
# stops being the only thing standing between us and a silently truncated state.
JEV_TOKEN_SAFETY_BASIS = {
    "kind": "conservative coefficient over the service's own usage.input_tokens",
    "factor": JEV_TOKEN_SAFETY_FACTOR,
    "measured_pairs": [
        {"sample": "breakout untrimmed", "client_raw": 1018, "service_usage_input": 2160,
         "ratio": 2.12},
        {"sample": "breakout trimmed", "client_raw": 1800, "service_usage_input": 2172,
         "ratio": 1.21},
        {"sample": "bomberman trimmed", "client_raw": 1791, "service_usage_input": 4229,
         "ratio": 2.36},
        {"sample": "pong", "client_raw": 431, "service_usage_input": None,
         "ratio": None, "note": "accepted (HTTP 200); no usage recorded in TASK-128"},
    ],
    "why_2_5": "ceil(2.36) rounded up; the ratio is the worst case observed, so the "
               "estimate errs high (the safe direction for a hard 2048-token refusal)",
    "bridge_to_task128": "the estimate is exactly ceil(2.5 * raw), so a budget of 2000 "
                         "under this estimator selects EXACTLY the same state as the "
                         "legacy budget of 800 did (2000 / 2.5 = 800).  TASK-128's "
                         "fitted jev thresholds therefore remain comparable when the "
                         "gate is re-run with --agent-state-budget 2000.",
}


def jev_estimate_tokens_raw(text):
    """The pre-TASK-129 estimator (kept: it is the basis of the TASK-128 budget).

    BPE tokenizers of this family pack roughly four ASCII characters per token, and every
    non-ASCII character (CJK is 3 bytes in UTF-8) is charged one full token.  It is called
    `raw` because it is NOT an upper bound -- see `JEV_TOKEN_SAFETY_FACTOR`.
    """
    ascii_n = 0
    other_n = 0
    for ch in text:
        if ord(ch) < 128:
            ascii_n += 1
        else:
            other_n += 1
    return (ascii_n + 3) // 4 + other_n


def jev_estimate_tokens(text):
    """TASK-129 D-C: a CONSERVATIVE estimate, calibrated on the service's own `usage`.

    `ceil(2.5 * raw)` written in integers, so the caller never sees a float comparison
    decide whether a request fits the documented cap.  The old behaviour is preserved
    behind `jev_estimate_tokens_raw()` for every number that was fitted on it.
    """
    return (5 * jev_estimate_tokens_raw(text) + 1) // 2


def jev_render_state(state):
    """The runtime flattens fields into a labelled text form; JSON is equivalent.

    `state` may be a string, object or array (verbatim: "state can be a string, object
    or array; render() flattens field names as labels"), so our structured state JSON
    is passed through almost verbatim -- no translation layer is needed.
    """
    if isinstance(state, str):
        return state
    return json.dumps(state, ensure_ascii=False, sort_keys=True)


def action_from_choice(choice, goal, hold_ms, why):
    """`answers.<action key>.choice` -> the existing action dict.

    Reuses `OpenAIAgent.normalise_action` / `keycode_of` so the gate sees exactly the
    same shapes as the other backends.
    """
    if choice is None:
        return None
    acts = (goal or {}).get("actions") or {}
    if choice in acts:
        return OpenAIAgent.normalise_action({"type": "action", "action": choice,
                                             "pressed": True, "hold_ms": int(hold_ms),
                                             "why": why})
    low = str(choice).strip().lower()
    if low in ("wait", "noop", "no_op", "none", "observe", "hold"):
        return {"type": "wait", "ms": int(hold_ms or 200), "why": why}
    if low in ("done", "finish", "stop", "end"):
        return {"type": "done", "why": why}
    kc = keycode_of(choice)
    if kc is not None:
        return OpenAIAgent.normalise_action({"type": "key", "keycode": kc,
                                             "pressed": True, "hold_ms": int(hold_ms),
                                             "why": why})
    return None


def action_criteria(goal):
    """`goal["actions"]` / `goal["keys"]` -> the Choice criteria dict.

    A pure function shared by the two decision backends (`jev`, `playjev`), which
    differ in the wire shape of a question but not in what an option means: one
    option per declared InputMap action, one per documented key, plus `wait` and
    `done`.  TASK-127 lifted this out of `JevAgent` unchanged so `PlayJevAgent`
    could reuse it verbatim; `JevAgent.build_action_criteria` still returns exactly
    the same dict it always did.
    """
    crit = {}
    acts = (goal or {}).get("actions") or {}
    for name in sorted(acts):
        keys = acts.get(name)
        if isinstance(keys, (list, tuple)):
            keys_s = ",".join(str(k) for k in keys)
        elif keys is None:
            keys_s = ""
        else:
            keys_s = str(keys)
        crit[name] = ("hold the game's InputMap action '%s' (bound key(s): %s)"
                      % (name, keys_s or "?"))
    for k in ((goal or {}).get("keys") or []):
        if keycode_of(k) is None:
            continue
        ck = "key_%s" % str(k).strip().upper()
        crit.setdefault(ck, "press and release the key %s" % k)
    crit.setdefault("wait", "do nothing this step (hold position / observe)")
    crit.setdefault("done", "stop probing: no further action is likely to help")
    return crit


class JevAgent(PlaytestAgent):
    """NeoHorse-Jev native decision backend.

    It never raises out of `decide`: an unconfigured endpoint, an unreachable service,
    an over-limit request, a busy worker or a rejected request all become a safe `wait`
    action plus a recorded reason -- never a silent success.
    """

    name = "jev"

    def __init__(self, game=None, objective="", options=None):
        PlaytestAgent.__init__(self, game, objective, options)
        o = self.options
        self.base_url = (o.get("base_url") or os.environ.get("PLAYTEST_BASE_URL", "")
                         ).rstrip("/")
        self.api_key = o.get("api_key")
        if self.api_key is None:
            self.api_key = os.environ.get("PLAYTEST_API_KEY", "")
        self.model = (o.get("model") or os.environ.get("PLAYTEST_MODEL", "")
                      or JEV_ANSWER_MODEL)
        self.decision_path = (o.get("decision_path")
                              or os.environ.get("PLAYTEST_DECISION_PATH", "")
                              or "/v1/systemone")
        self.health_path = o.get("health_path") or JEV_HEALTH_PATH
        self.timeout = float(o.get("timeout", 60))
        self.send_images = bool(o.get("send_images", False))   # text state is the strong path
        self.require_health = bool(o.get("require_health", True))
        self.max_retries = max(0, int(o.get("max_retries", 2)))
        self.retry_backoff = float(o.get("retry_backoff", 1.0))
        self.retry_backoff_max = float(o.get("retry_backoff_max", 10.0))
        self.hold_ms = int(o.get("hold_ms", 300))
        self.state_overflow = (o.get("state_overflow")
                               or os.environ.get("PLAYTEST_STATE_OVERFLOW", "error")).lower()
        self.max_questions = min(int(o.get("max_questions", JEV_LIMITS["max_questions"])),
                                 JEV_LIMITS["max_questions"])
        self.invariant_questions = max(0, int(o.get("invariant_questions", 3)))
        self.score_question = bool(o.get("score_question", True))
        self.action_key = o.get("action_key") or "move"
        self.score_key = o.get("score_key") or "brokenness"
        self.image_multi_question = str(o.get("image_multi_question", "error")).lower()
        # TASK-129 D-C: how many times a REAL 422 `state exceeds N tokens` may be answered
        # by halving the state and re-POSTing.  Bounded, recorded, never silent.
        self.max_state_retries = max(0, int(o.get("max_state_retries", 2)))
        self.score_levels = list(o.get("score_levels") or JEV_BROKENNESS_LEVELS)
        self.thresholds = dict(DEFAULT_JEV_THRESHOLDS)
        self.thresholds.update(o.get("thresholds") or {})

        self.errors = []
        self.calls = []            # request/response evidence for the gate
        self.attempts = []         # every transport attempt (proves the retries)
        self.health = None
        self.last_evidence = None
        self.last_noul = {}
        self.last_scores = {}
        self._ready = None
        # The service has no dynamic batching, so requests are serialized here.
        self._lock = threading.Lock()

    # ---- error/evidence bookkeeping -------------------------------------
    def _error(self, kind, message, **extra):
        rec = {"kind": kind, "error": message}
        rec.update(extra)
        self.errors.append(rec)
        return rec

    # ---- transport -------------------------------------------------------
    def _request(self, method, path, payload=None):
        """One transport attempt.  The lock is intentional: the service serializes."""
        url = self.base_url + path
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = Request(url, data=body, method=method)
        req.add_header("Content-Type", "application/json")
        if self.api_key:
            req.add_header("Authorization", "Bearer %s" % self.api_key)
        rec = {"method": method, "url": url, "status": None, "headers": {},
               "body": "", "seconds": 0.0, "lock": "serialized"}
        t0 = time.time()
        with self._lock:
            try:
                resp = urlopen(req, timeout=self.timeout)
                raw = resp.read().decode("utf-8", "replace")
                rec["status"] = getattr(resp, "status", 200)
                rec["headers"] = dict((k.lower(), v) for k, v in resp.headers.items())
                rec["body"] = raw
            except HTTPError as e:
                raw = e.read().decode("utf-8", "replace") if hasattr(e, "read") else ""
                rec["status"] = e.code
                try:
                    rec["headers"] = dict((k.lower(), v) for k, v in e.headers.items())
                except Exception:  # noqa: BLE001
                    rec["headers"] = {}
                rec["body"] = raw
                rec["error"] = "HTTPError"
            except URLError as e:
                rec["error"] = "URLError: %s" % e
            except Exception as e:  # noqa: BLE001 - the gate must never die on a model
                rec["error"] = "%s: %s" % (type(e).__name__, e)
        rec["seconds"] = round(time.time() - t0, 3)
        return rec

    def check_health(self):
        """`GET /health` -- the only readiness probe Jev has (there is no /v1/models)."""
        rec = self._request("GET", self.health_path)
        parsed = None
        if rec.get("status") == 200 and rec.get("body"):
            try:
                parsed = json.loads(rec["body"])
            except Exception as e:  # noqa: BLE001
                rec["parse_error"] = "%s: %s" % (type(e).__name__, e)
        rec["json"] = parsed
        self.health = {"url": rec["url"], "status": rec.get("status"),
                       "seconds": rec.get("seconds"), "json": parsed,
                       "input_modalities": (parsed or {}).get("input_modalities")
                       if isinstance(parsed, dict) else None,
                       "error": rec.get("error")}
        return rec

    def _post_decision(self, payload):
        """POST with the documented busy protocol: 429/529 honour `Retry-After`."""
        attempts = []
        delay = self.retry_backoff
        max_attempts = self.max_retries + 1
        rec = None
        for i in range(1, max_attempts + 1):
            rec = self._request("POST", self.decision_path, payload)
            status = rec.get("status")
            retry_after = (rec.get("headers") or {}).get("retry-after")
            attempts.append({"attempt": i, "status": status, "seconds": rec.get("seconds"),
                             "retry_after": retry_after, "error": rec.get("error")})
            if status == 200:
                break
            if status in (429, 529):
                wait = delay
                try:
                    wait = float(retry_after)
                except (TypeError, ValueError):
                    pass
                wait = min(max(0.0, wait), self.retry_backoff_max)
                if i < max_attempts:
                    time.sleep(wait)
                    delay = min(delay * 2.0, self.retry_backoff_max)
                continue
            break  # 401/413/422/... are hard errors: no retry, report them
        rec["attempts"] = attempts
        self.attempts.extend(attempts)
        return rec

    # ---- request construction -------------------------------------------
    def build_action_criteria(self, goal):
        return action_criteria(goal)

    def build_questions(self, goal, with_image=False):
        """The typed `questions` object.  Image requests carry EXACTLY one question."""
        q = {}
        q[self.action_key] = {
            "type": "choice",
            "instructions": self.options.get(
                "action_instructions",
                "Choose the single next input that best serves the objective."),
            "criteria": self.build_action_criteria(goal),
        }
        if with_image:
            # Documented as hard: an image request carries exactly 1 image + 1 question.
            if len(q) != 1:
                raise JevProtocolError("an image request must carry exactly 1 question")
            return q
        for key, text in JEV_INVARIANT_QUESTIONS[:self.invariant_questions]:
            q[key] = {"type": "noul", "instructions": text}
        if self.score_question:
            q[self.score_key] = {
                "type": "score",
                "instructions": ("Rate how broken this frame is, from 1 (fully working) "
                                 "to %d (unusable)." % len(self.score_levels)),
                "criteria": list(self.score_levels),
            }
        if len(q) > self.max_questions:
            raise JevProtocolError("built %d questions, over the %d-per-request limit"
                                   % (len(q), self.max_questions))
        if not (JEV_LIMITS["score_min_levels"] <= len(self.score_levels)
                <= JEV_LIMITS["score_max_levels_systemone"]):
            raise JevProtocolError("score criteria needs 2..%d ordered levels for "
                                   "/v1/systemone, got %d"
                                   % (JEV_LIMITS["score_max_levels_systemone"],
                                      len(self.score_levels)))
        return q

    def prepare_state(self, state):
        """Enforce the 2048-token `state` limit; never truncate silently.

        Returns (state_value, evidence).  `state_overflow="error"` (the default)
        refuses the request; `"clip"` drops whole fields/items/trailing characters and
        records exactly what was dropped in the returned evidence.
        """
        text = jev_render_state(state) if not isinstance(state, str) else state
        n = jev_estimate_tokens(text)
        ev = {"state_tokens_estimate": n, "state_bytes": len(text.encode("utf-8")),
              "limit": JEV_LIMITS["state_max_tokens"], "clipped": None}
        if n <= JEV_LIMITS["state_max_tokens"]:
            return state, ev
        limit = JEV_LIMITS["state_max_tokens"]
        if self.state_overflow != "clip":
            raise JevProtocolError(
                "state is ~%d tokens (estimated), over the %d-token documented limit; "
                "the service REJECTS over-limit requests rather than truncating. Pass "
                "state_overflow='clip' to drop whole fields and record what was dropped."
                % (n, limit))
        kept, dropped = self._clip_state(state, limit)
        kept_text = jev_render_state(kept) if not isinstance(kept, str) else kept
        ev["clipped"] = dropped
        ev["state_tokens_estimate"] = jev_estimate_tokens(kept_text)
        ev["state_bytes"] = len(kept_text.encode("utf-8"))
        return kept, ev

    @staticmethod
    def _clip_state(state, limit):
        """Explicit clipping: drop whole fields/items/trailing chars, record each."""
        dropped = {"reason": "state over the %d-token limit; explicit clip "
                             "(NOT a silent truncation)" % limit,
                   "dropped_keys": [], "dropped_items": 0, "dropped_chars": 0}
        if isinstance(state, dict):
            kept = dict(state)
            order = sorted(kept, key=lambda k: len(json.dumps(kept[k], ensure_ascii=False)),
                           reverse=True)
            for k in order:
                if jev_estimate_tokens(jev_render_state(kept)) <= limit:
                    break
                dropped["dropped_keys"].append(
                    {"key": k, "estimated_tokens":
                     jev_estimate_tokens(json.dumps(kept[k], ensure_ascii=False))})
                kept.pop(k, None)
            return kept, dropped
        if isinstance(state, list):
            kept = list(state)
            while kept and jev_estimate_tokens(jev_render_state(kept)) > limit:
                kept.pop()
                dropped["dropped_items"] += 1
            return kept, dropped
        text = state if isinstance(state, str) else jev_render_state(state)
        lo, hi = 0, len(text)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if jev_estimate_tokens(text[:mid]) <= limit:
                lo = mid
            else:
                hi = mid - 1
        dropped["dropped_chars"] = len(text) - lo
        dropped["dropped_tail_preview"] = text[lo:lo + 120]
        return text[:lo], dropped

    # ---- TASK-129 D-C: answer a REAL 422 by halving the budget, once per attempt --
    @staticmethod
    def _is_state_overflow(rec):
        """True only for the 422 the service uses for an over-limit `state`.

        The check is deliberately textual: TASK-128 measured the service's own wording
        (`{"detail":"state exceeds 2048 tokens: 2160"}`), and a 422 for any OTHER reason
        (model alias, unknown field) must NOT be turned into a budget retry -- that would
        loop without making the request any more legal.
        """
        if rec.get("status") != 422:
            return False
        body = (rec.get("body") or "").lower()
        return ("exceeds" in body and "token" in body) or "state" in body and "token" in body

    def shrink_state(self, state):
        """Halve the state's estimated size, keeping the SAME policy as the gate.

        The gate trims `nodes` in tree order (`trim_state_for_agent`); this repeats that
        shape at half the previous estimate, so a retried judgement is still a judgement
        of the same construction -- only smaller -- and every dropped node is named.
        Returns (state, evidence).  Never silent: the caller records `evidence`.
        """
        before = jev_estimate_tokens(jev_render_state(state))
        target = max(1, before // 2)
        ev = {"reason": "the service answered 422 for an over-limit `state`; the budget "
                        "was halved and the request re-sent (no silent truncation)",
              "before_tokens_estimate": before, "target_tokens_estimate": target}
        if isinstance(state, dict) and isinstance(state.get("nodes"), dict):
            kept, dropped = {}, []
            for key, value in state["nodes"].items():
                kept[key] = value
                trial = dict(state)
                trial["nodes"] = kept
                if jev_estimate_tokens(jev_render_state(trial)) > target:
                    kept.pop(key, None)
                    dropped.append(key)
            out = dict(state)
            out["nodes"] = kept
            after = jev_estimate_tokens(jev_render_state(out))
            ev.update({"policy": "keep `nodes` in tree order until the estimate fits half "
                                 "the previous budget; name every dropped node",
                       "nodes_in_source": len(state["nodes"]), "nodes_kept": len(kept),
                       "nodes_dropped": dropped, "after_tokens_estimate": after})
            return out, ev
        if isinstance(state, dict):
            kept, dropped = self._clip_state(state, target)
            ev.update({"policy": "client clip to half the previous budget",
                       "clipped": dropped,
                       "after_tokens_estimate": jev_estimate_tokens(jev_render_state(kept))})
            return kept, ev
        text = state if isinstance(state, str) else jev_render_state(state)
        lo, hi = 0, len(text)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if jev_estimate_tokens(text[:mid]) <= target:
                lo = mid
            else:
                hi = mid - 1
        ev.update({"policy": "truncate the text to half the previous budget (recorded)",
                   "dropped_chars": len(text) - lo,
                   "dropped_tail_preview": text[lo:lo + 120],
                   "after_tokens_estimate": jev_estimate_tokens(text[:lo])})
        return text[:lo], ev

    def build_request(self, frames, state, goal, want="action"):
        """Build the typed request and its limits evidence (raises JevProtocolError)."""
        usable = [f for f in (frames or [])
                  if f.get("path") and os.path.isfile(f["path"])]
        with_image = bool(self.send_images and usable)
        questions = self.build_questions(goal or {}, with_image=False)
        image_question_policy = None
        if with_image:
            # Documented as hard: exactly 1 image + 1 question.  Sending several
            # questions "as an image request" is what the task forbids, so the default
            # policy is a CLEAR ERROR, not a silent trim.
            if len(questions) > 1:
                if self.image_multi_question != "trim":
                    raise JevProtocolError(
                        "an image request carries exactly 1 image + 1 question, but this "
                        "agent built %d questions (%s); the service would reject it. "
                        "Build a single question (invariant_questions=0, score_question="
                        "False) or explicitly opt into image_multi_question='trim' (which "
                        "records the questions it drops)."
                        % (len(questions), sorted(questions)))
                image_question_policy = {
                    "policy": "trim", "dropped_questions": sorted(
                        k for k in questions if k != self.action_key),
                    "kept_questions": [self.action_key]}
                questions = {self.action_key: questions[self.action_key]}
        state_value, state_ev = self.prepare_state(state)
        payload = {"model": self.model, "state": state_value, "questions": questions}
        if with_image:
            path = usable[-1]["path"]
            with open(path, "rb") as fh:
                data = fh.read()
            if len(data) > JEV_LIMITS["image_decoded_max_bytes"]:
                raise JevProtocolError(
                    "image %s is %d bytes, over the documented %d-byte decoded limit"
                    % (path, len(data), JEV_LIMITS["image_decoded_max_bytes"]))
            payload["image"] = "data:image/png;base64,%s" % base64.b64encode(data).decode("ascii")

        body = json.dumps(payload).encode("utf-8")
        meta = {
            "decision_path": self.decision_path,
            "with_image": with_image,
            "question_count": len(questions),
            "question_keys": list(questions.keys()),
            "question_types": {k: v.get("type") for k, v in questions.items()},
            "image_question_policy": image_question_policy,
            "body_bytes": len(body),
            "body_tokens_estimate": jev_estimate_tokens(
                json.dumps(payload, ensure_ascii=False)),
            "state": state_ev,
        }
        cap = JEV_LIMITS["image_request_max_bytes"] if with_image \
            else JEV_LIMITS["request_max_bytes"]
        if len(body) > cap:
            raise JevProtocolError("request body is %d bytes, over the %d-byte limit"
                                   % (len(body), cap))
        tok_cap = JEV_LIMITS["image_request_max_tokens"] if with_image \
            else JEV_LIMITS["request_max_tokens"]
        if meta["body_tokens_estimate"] > tok_cap:
            raise JevProtocolError(
                "request is ~%d tokens (estimated), over the %d-token limit for this "
                "endpoint%s" % (meta["body_tokens_estimate"], tok_cap,
                                " (image request)" if with_image else ""))
        return payload, meta

    # ---- response parsing ------------------------------------------------
    def parse_response(self, body):
        if not body:
            raise JevProtocolError("the service returned an empty body")
        try:
            data = json.loads(body)
        except Exception as e:  # noqa: BLE001
            raise JevProtocolError("the response body is not JSON: %s" % e)
        if not isinstance(data, dict) or not isinstance(data.get("answers"), dict):
            raise JevProtocolError("the response has no `answers` object: %s"
                                   % list(data)[:8])
        return data

    def collect_answers(self, answers):
        """Split the answers into the action choice, the noul P(true)s and the scores."""
        noul, scores, choice = {}, {}, None
        for key, a in (answers or {}).items():
            if not isinstance(a, dict):
                continue
            t = a.get("type")
            if t == "noul":
                noul[key] = a
            elif t == "score":
                scores[key] = a
            elif t == "choice" and (choice is None or key == self.action_key):
                choice = (key, a)
        return choice, noul, scores

    # ---- the interface ---------------------------------------------------
    def decide(self, frames, state, goal):
        if not self.base_url:
            self._error("unconfigured", "PLAYTEST_BASE_URL is not set")
            return {"type": "wait", "ms": 100,
                    "why": "jev backend unconfigured: PLAYTEST_BASE_URL is not set "
                           "(recorded, not a success)"}
        if self.decision_path not in JEV_DECISION_PATHS:
            self._error("unconfigured",
                        "unknown decision path %r; Jev only provides %s"
                        % (self.decision_path, list(JEV_DECISION_PATHS)))
            return {"type": "wait", "ms": 100,
                    "why": "jev backend misconfigured: decision path %r"
                           % self.decision_path}
        if self.require_health and self._ready is not True:
            rec = self.check_health()
            if rec.get("status") != 200:
                self._error("health", "GET %s failed: status=%s error=%s"
                            % (self.health_path, rec.get("status"), rec.get("error")),
                            body=(rec.get("body") or "")[:400])
                self._ready = False
                return {"type": "wait", "ms": 200,
                        "why": "jev service is not reachable/ready (see recorded "
                               "health error); degraded to wait"}

        # TASK-129 D-C: a REAL 422 (`state exceeds 2048 tokens: N`) is answered by halving
        # the state and re-sending, up to `max_state_retries` times.  The retry lives here,
        # NOT inside `_post_decision`: that method's `attempts` list is the transport-level
        # retry record (429/529) and TASK-124's `D4_422_not_retried` check is about 422 not
        # being a busy-retry.  Every budget retry is recorded separately and in full.
        state_retries = []
        state_value = state
        payload = meta = rec = None
        for attempt_i in range(self.max_state_retries + 1):
            try:
                payload, meta = self.build_request(frames, state_value, goal, "action")
            except JevProtocolError as e:
                self._error("request", str(e))
                return {"type": "wait", "ms": 200,
                        "why": "jev request refused before sending: %s" % e}
            except Exception as e:  # noqa: BLE001
                self._error("request", "%s: %s" % (type(e).__name__, e))
                return {"type": "wait", "ms": 200,
                        "why": "jev request build failed: %s" % e}
            if state_retries:
                meta = dict(meta)
                meta["state_budget_retries"] = state_retries
            rec = self._post_decision(payload)
            if rec.get("status") != 422 or attempt_i >= self.max_state_retries:
                break
            if not self._is_state_overflow(rec):
                break
            state_value, shrink_ev = self.shrink_state(state_value)
            entry = {"attempt": attempt_i + 1, "status": 422,
                     "service_says": (rec.get("body") or "")[:300],
                     "max_state_retries": self.max_state_retries,
                     "baseline_is_halved_not_guessed": True}
            entry.update(shrink_ev)
            state_retries.append(entry)
            if shrink_ev.get("after_tokens_estimate") in (None, 0):
                break  # nothing left to shrink: do not loop on a hopeless request

        evidence = {"kind": "decision", "transport": rec, "request_meta": meta,
                    "request_payload": payload, "state_budget_retries": state_retries}
        if rec.get("status") != 200:
            msg = self._map_http_error(rec)
            self._error("http", msg, status=rec.get("status"))
            evidence["error"] = msg
            self.calls.append(evidence)
            self.last_evidence = evidence
            return {"type": "wait", "ms": 200, "why": msg}

        try:
            data = self.parse_response(rec.get("body"))
        except JevProtocolError as e:
            msg = "jev response could not be parsed: %s" % e
            self._error("response", msg)
            evidence["error"] = msg
            self.calls.append(evidence)
            self.last_evidence = evidence
            return {"type": "wait", "ms": 200, "why": msg}

        answers = data["answers"]
        choice, noul, scores = self.collect_answers(answers)
        evidence.update({
            "response_status": rec.get("status"),
            "model": data.get("model"),
            "usage": data.get("usage"),
            "input_tokens": data.get("input_tokens"),
            "image_tokens": data.get("image_tokens"),
            "answers_raw": answers,
            "choice": choice[1] if choice else None,
            "noul": noul,
            "scores": scores,
            "confidence_header": (rec.get("headers") or {}).get("x-neohorse-confidence"),
            "usage_header": (rec.get("headers") or {}).get("x-neohorse-usage"),
            "probabilities": {k: a.get("probabilities") for k, a in list(noul.items())
                              + list(scores.items())},
            "confidences": {k: a.get("confidence") for k, a in list(noul.items())
                            + list(scores.items())},
        })
        self.last_noul = noul
        self.last_scores = scores
        act = None
        if choice:
            why = ("jev choice=%r confidence=%s probabilities=%s"
                   % (choice[1].get("choice"), choice[1].get("confidence"),
                      choice[1].get("probabilities")))
            act = action_from_choice(choice[1].get("choice"), goal, self.hold_ms, why)
        if act is None:
            msg = ("jev returned no usable choice (answers=%s)"
                   % list(answers.keys())[:8])
            self._error("response", msg)
            evidence["error"] = msg
            act = {"type": "wait", "ms": 200, "why": msg}
        evidence["action"] = act
        self.calls.append(evidence)
        self.last_evidence = evidence
        return act

    def _map_http_error(self, rec):
        status = rec.get("status")
        detail = (rec.get("body") or "")[:300]
        n = len(rec.get("attempts") or [])
        if status == 401:
            return ("jev service rejected the credentials (401): set PLAYTEST_API_KEY. "
                    "body=%s" % detail)
        if status == 413:
            return ("jev service refused the request body as too large (413); the "
                    "documented caps are 1 MiB text / 8 MiB image. body=%s" % detail)
        if status == 422:
            return ("jev service rejected the request as invalid/unsupported (422): "
                    "%s" % detail)
        if status in (429, 529):
            return ("jev worker is busy (HTTP %s) and still busy after %d attempts; "
                    "`Retry-After` was honoured. body=%s" % (status, n, detail))
        if status is None:
            return ("jev service is not reachable (%s)" % rec.get("error"))
        return "jev service returned HTTP %s: %s" % (status, detail)

    def judge(self, frames, state, goal):
        """A machine-readable playability verdict from the noul/score answers.

        If `decide()` already ran, this reuses that evidence instead of paying for a
        second forward pass (the service has no dynamic batching).  The verdict is
        explicitly marked UNCALIBRATED.
        """
        if self.last_evidence is None:
            self.decide(frames, state, goal)
        return self.threshold_verdict()

    def threshold_verdict(self):
        crit = []
        for key, a in sorted(self.last_noul.items()):
            val = a.get("noul")
            ok = isinstance(val, (int, float)) and val >= self.thresholds["noul_min_p_true"]
            crit.append({"id": "noul:%s" % key, "value": val,
                         "rule": "P(true) >= %.3f" % self.thresholds["noul_min_p_true"],
                         "pass": bool(ok)})
        for key, a in sorted(self.last_scores.items()):
            val = a.get("score")
            ok = isinstance(val, (int, float)) and val <= self.thresholds["score_max_expected"]
            crit.append({"id": "score:%s" % key, "value": val,
                         "rule": "expected level <= %.3f"
                                 % self.thresholds["score_max_expected"],
                         "pass": bool(ok)})
        verdict = all(c["pass"] for c in crit) if crit else None
        return {"backend": "jev", "pass": verdict,
                "why": ("no noul/score answer was captured: no threshold verdict is "
                        "possible" if verdict is None else
                        ("%d/%d threshold criteria passed"
                         % (sum(1 for c in crit if c["pass"]), len(crit)))),
                "criteria": crit,
                "thresholds": dict(self.thresholds),
                "uncalibrated": True,
                "note": JEV_THRESHOLD_NOTE,
                "source": ("last decision response" if self.last_evidence else "none")}

    def report(self):
        rep = PlaytestAgent.report(self)
        rep.update({"base_url": self.base_url, "model": self.model,
                    "decision_path": self.decision_path, "health": self.health,
                    "errors": self.errors, "attempts": self.attempts,
                    "max_state_retries": self.max_state_retries,
                    "token_estimator": {
                        "name": "jev_estimate_tokens (TASK-129 D-C calibrated)",
                        "safety_factor": JEV_TOKEN_SAFETY_FACTOR,
                        "basis": JEV_TOKEN_SAFETY_BASIS},
                    "thresholds": dict(self.thresholds),
                    "threshold_verdict": self.threshold_verdict()})
        return rep


# ---------------------------------------------------------------------------
# backend 4: playjev -- PlayJev 0.8B, the VISION fine-tuned sibling (TASK-127)
# ---------------------------------------------------------------------------
# Every protocol constant below is a first-party fact read out of the deployed
# source, `playjev/serve.py` at commit ea3a514d2fcbc0756c36eabe052439db54544542
# (`omnijev/PlayJev`, 2026-09-24); the line numbers are the ones in that file and
# are quoted verbatim in the TASK-127 report.  The differences from Jev that
# force this to be a separate backend rather than a flag on `JevAgent`:
#
#   * the state is `{"frames": [...]}` where each frame is a base64 string or a
#     data URL (serve.py:32-37, 41-43).  A text state does not exist here: it is
#     refused with 400 "text states belong to OpenJev" (serve.py:41-42).
#   * ONLY `type: "choice"` questions are served (serve.py:53-54).  A `noul` or
#     `score` question -- both legal on Jev -- is a 400 here.  So this backend
#     expresses an invariant as a yes/no Choice and the brokenness rating as an
#     ordered-levels Choice whose expected value is the score.
#   * `criteria` is a dict (name -> description) or a list of names, with at
#     least two options (serve.py:55-63); at most 26, the alphabet in
#     `playjev/model.py:38`.
#   * ONE image + N questions IS legal: the frames are shared by every question of
#     one request (serve.py:16, 52-73).  That is the opposite of Jev's hard
#     "exactly 1 image + 1 question" rule, and it is why a single PlayJev request
#     can carry the action choice, the invariants and the score together.
#   * the reply is `{"model", "answers", "timing"}` (serve.py:11-13, 69-74); there
#     is no `usage`, no `input_tokens`/`image_tokens` at the top level and no
#     `x-neohorse-*` header.
#   * `serve.py` NEVER emits `abstain`, in the request or in the answer.  The
#     `Decision` object it discards does carry `allowed_mass` -- "share of the
#     full-vocabulary softmax that lands on the K answer slots" (model.py:102),
#     i.e. the real "is the model answering at all?" diagnostic -- but the HTTP
#     answer keeps only choice/probabilities/confidence.  This backend therefore
#     (a) honours a server-sent `abstain` should a later build add one, and
#     (b) classifies a MISSING or structurally unusable answer as an abstain, so
#     "the model did not answer" can never be read as "the model said yes".
#
# One more fact worth recording: serve.py never reads the request's `model` field
# (it answers with the `--name` the server was started with), so PLAYTEST_MODEL is
# cosmetic for this backend.
PLAYJEV_ANSWER_MODEL = "playjev-0.8b"
PLAYJEV_HEALTH_PATH = "/health"
PLAYJEV_MODELS_PATH = "/v1/models"
PLAYJEV_DECISION_PATHS = ("/v1/systemone",)
PLAYJEV_DEFAULT_BASE_URL = "http://127.0.0.1:8081"
PLAYJEV_MIN_OPTIONS = 2
PLAYJEV_MAX_OPTIONS = 26           # playjev/model.py:38 LETTERS
PLAYJEV_TRUE = "yes"
PLAYJEV_FALSE = "no"
# The ordered brokenness levels, low -> high, WITHOUT the "N = " prefix (the option
# NAME is the level number here, so the model never has to parse the number back
# out of a sentence).  Same wording and same ordering as JEV_BROKENNESS_LEVELS.
PLAYJEV_BROKENNESS_CRITERIA = [
    ("1", "fully working: content is drawn, input responds, nothing looks wrong"),
    ("2", "minor glitches only; still clearly playable"),
    ("3", "partially broken: some documented capability is missing or unresponsive"),
    ("4", "badly broken: the game barely responds or renders garbage"),
    ("5", "unusable: flat/blank screen, error dialog, or frozen"),
]
PLAYJEV_ABSTAIN_NOTE = (
    "ABSTAIN IS NOT SUCCESS.  PlayJev's serve.py has no abstain field, so this "
    "backend derives one: an answer that is absent, or that carries no usable "
    "probabilities, or whose confidence is below abstain_min_confidence is recorded "
    "as abstain=true and the verdict becomes 'no verdict' (pass=null), never a pass. "
    "The upstream `allowed_mass` diagnostic (playjev/model.py:102) would make this "
    "much sharper and serve.py drops it -- see the TASK-127 report."
)
# TASK-129 D-E.  `score` is withdrawn from the decision path.  TASK-127 measured that the
# DEPLOYED service rates a black screen 2.41 while a real snake frame gets 3.97 -- i.e. the
# expected breakage level runs the WRONG WAY for the deployed weights -- so the number is
# kept as an explicitly UNCALIBRATED, DIRECTION-SUSPECT observation and nothing more.  The
# only way it can still block a verdict is structural: if the score answer is unusable the
# model did not answer, and "the model did not answer" is never a pass (TASK-127's rule).
PLAYJEV_PLAYABLE_KEY = "playable"
PLAYJEV_PLAYABLE_QUESTION = (
    "Does this frame clearly look playable, with no visual corruption or freeze?")
PLAYJEV_SCORE_DIRECTION_NOTE = (
    "OBSERVATION ONLY -- NOT IN THE DECISION PATH.  TASK-127 measured the direction as "
    "INVERTED on the deployed PlayJev weights (black screen 2.41 < a real snake frame "
    "3.97 on a 1=working..5=unusable legend), so this expected level is recorded with "
    "`direction: suspect` and is never compared with a threshold to produce a verdict. "
    "TASK-129 D-E; the flip-legend probe exists to test whether the inversion is a "
    "wording/legend-order artefact, and its result never enters the verdict either."
)


class PlayJevAgent(PlaytestAgent):
    """PlayJev 0.8B (image states) native decision backend.

    Like `JevAgent` it never raises out of `decide`: an unconfigured endpoint, an
    unreachable service, a refused request or an unusable answer all become a safe
    `wait` action plus a recorded reason.  Unlike `JevAgent` the frames are the
    whole input -- PlayJev has no text-state path at all.
    """

    name = "playjev"

    def __init__(self, game=None, objective="", options=None):
        PlaytestAgent.__init__(self, game, objective, options)
        o = self.options
        self.base_url = ((o.get("base_url") or os.environ.get("PLAYTEST_BASE_URL", "")
                          or PLAYJEV_DEFAULT_BASE_URL).rstrip("/"))
        self.api_key = o.get("api_key")
        if self.api_key is None:
            self.api_key = os.environ.get("PLAYTEST_API_KEY", "")
        self.model = (o.get("model") or os.environ.get("PLAYTEST_MODEL", "")
                      or PLAYJEV_ANSWER_MODEL)
        self.decision_path = (o.get("decision_path")
                              or os.environ.get("PLAYTEST_DECISION_PATH", "")
                              or "/v1/systemone")
        self.health_path = o.get("health_path") or PLAYJEV_HEALTH_PATH
        self.timeout = float(o.get("timeout", 120))
        self.send_images = bool(o.get("send_images", True))    # pixels are the point
        self.require_health = bool(o.get("require_health", True))
        self.max_retries = max(0, int(o.get("max_retries", 1)))
        self.retry_backoff = float(o.get("retry_backoff", 1.0))
        self.retry_backoff_max = float(o.get("retry_backoff_max", 10.0))
        self.hold_ms = int(o.get("hold_ms", 300))
        self.invariant_questions = max(0, int(o.get("invariant_questions", 3)))
        self.score_question = bool(o.get("score_question", True))
        # TASK-129 D-E: the playability invariant is asked under this key, and the score
        # question's VALUE is not a criterion unless a caller explicitly asks for the old
        # TASK-127 behaviour.
        self.playable_key = o.get("playable_key") or PLAYJEV_PLAYABLE_KEY
        self.score_in_verdict = bool(o.get("score_in_verdict", False))
        self.score_abstain_blocks_verdict = bool(o.get("score_abstain_blocks_verdict", True))
        # TASK-129 C: which noul questions may act as CRITERIA.  Empty/None = every noul
        # question is a criterion (the TASK-127 behaviour).  The gate's visual path sets
        # ["playable"], so the other invariants stay recorded observations.
        self.verdict_invariant_keys = list(o.get("verdict_invariant_keys") or []) or None
        # TASK-129 D-E: the declarative flip-legend probe.  It only reverses the OPTION
        # ORDER of the score question so the same weights are asked the opposite way; the
        # expected level is still computed in the canonical level order, and the probe's
        # result is recorded outside the verdict.
        self.legend_flipped = bool(o.get("legend_flipped", False))
        self.action_key = o.get("action_key") or "move"
        self.score_key = o.get("score_key") or "brokenness"
        self.score_criteria = list(o.get("score_criteria")
                                   or PLAYJEV_BROKENNESS_CRITERIA)
        self.abstain_min_confidence = float(
            o.get("abstain_min_confidence")
            if o.get("abstain_min_confidence") is not None
            else (os.environ.get("PLAYTEST_ABSTAIN_MIN_CONFIDENCE") or 0.0))
        self.thresholds = dict(DEFAULT_JEV_THRESHOLDS)
        self.thresholds.update(o.get("thresholds") or {})

        self.errors = []
        self.calls = []            # request/response evidence for the gate
        self.attempts = []         # every transport attempt
        self.health = None
        self.last_evidence = None
        self.last_answers = {}     # question key -> classified answer record
        self.last_roles = {}       # question key -> {"role", "options", ...}
        self.last_noul = {}        # key -> record, for the gate's threshold rule
        self.last_scores = {}
        self.last_timings = {}
        self._ready = None
        # The service holds one engine lock and serves "one forward at a time"
        # (serve.py:29, 65-68): serialise on this side too.
        self._lock = threading.Lock()

    # ---- error/evidence bookkeeping -------------------------------------
    def _error(self, kind, message, **extra):
        rec = {"kind": kind, "error": message}
        rec.update(extra)
        self.errors.append(rec)
        return rec

    # ---- transport -------------------------------------------------------
    def _request(self, method, path, payload=None):
        url = self.base_url + path
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = Request(url, data=body, method=method)
        req.add_header("Content-Type", "application/json")
        if self.api_key:
            req.add_header("Authorization", "Bearer %s" % self.api_key)
        rec = {"method": method, "url": url, "status": None, "headers": {},
               "body": "", "seconds": 0.0, "lock": "serialized"}
        t0 = time.time()
        with self._lock:
            try:
                resp = urlopen(req, timeout=self.timeout)
                raw = resp.read().decode("utf-8", "replace")
                rec["status"] = getattr(resp, "status", 200)
                rec["headers"] = dict((k.lower(), v) for k, v in resp.headers.items())
                rec["body"] = raw
            except HTTPError as e:
                raw = e.read().decode("utf-8", "replace") if hasattr(e, "read") else ""
                rec["status"] = e.code
                try:
                    rec["headers"] = dict((k.lower(), v) for k, v in e.headers.items())
                except Exception:  # noqa: BLE001
                    rec["headers"] = {}
                rec["body"] = raw
                rec["error"] = "HTTPError"
            except URLError as e:
                rec["error"] = "URLError: %s" % e
            except Exception as e:  # noqa: BLE001 - the gate must never die
                rec["error"] = "%s: %s" % (type(e).__name__, e)
        rec["seconds"] = round(time.time() - t0, 3)
        return rec

    def check_health(self):
        """`GET /health` -- PlayJev answers `{"ok": true, "model", "two_frame"}`
        (serve.py:105-106), NOT Jev's `{"status": "ready", ...}`."""
        rec = self._request("GET", self.health_path)
        parsed = None
        if rec.get("status") == 200 and rec.get("body"):
            try:
                parsed = json.loads(rec["body"])
            except Exception as e:  # noqa: BLE001
                rec["parse_error"] = "%s: %s" % (type(e).__name__, e)
        rec["json"] = parsed
        self.health = {"url": rec["url"], "status": rec.get("status"),
                       "seconds": rec.get("seconds"), "json": parsed,
                       "ok": parsed.get("ok") if isinstance(parsed, dict) else None,
                       "model": parsed.get("model") if isinstance(parsed, dict) else None,
                       "two_frame": parsed.get("two_frame") if isinstance(parsed, dict) else None,
                       "error": rec.get("error")}
        return rec

    def _post_decision(self, payload):
        """POST /v1/systemone.  Kept retry-shaped for forward compatibility: the
        deployed serve.py has no busy protocol (its engine lock queues instead),
        but a later build may answer 429/529 and `Retry-After` is honoured."""
        attempts = []
        delay = self.retry_backoff
        max_attempts = self.max_retries + 1
        rec = None
        for i in range(1, max_attempts + 1):
            rec = self._request("POST", self.decision_path, payload)
            status = rec.get("status")
            retry_after = (rec.get("headers") or {}).get("retry-after")
            attempts.append({"attempt": i, "status": status, "seconds": rec.get("seconds"),
                             "retry_after": retry_after, "error": rec.get("error")})
            if status == 200:
                break
            if status in (429, 529):
                wait = delay
                try:
                    wait = float(retry_after)
                except (TypeError, ValueError):
                    pass
                wait = min(max(0.0, wait), self.retry_backoff_max)
                if i < max_attempts:
                    time.sleep(wait)
                    delay = min(delay * 2.0, self.retry_backoff_max)
                continue
            break  # 400/404/500 are hard errors here: report, do not retry
        rec["attempts"] = attempts
        self.attempts.extend(attempts)
        return rec

    # ---- request construction -------------------------------------------
    def build_questions(self, goal):
        """Every question is a Choice.  Returns (questions, roles).

        `roles[key]` is what the ANSWER means, which is how the response mapping
        stays honest: a `noul` role reports P(true) from the yes/no Choice, a
        `score` role reports the expected level from the ordered-levels Choice.
        """
        questions, roles = {}, {}
        # TASK-132: go through the same hook `JevAgent` exposes, so a caller that needs a
        # different option set (a PLAYER must not be offered "stop probing") can override
        # one method instead of rebuilding the question.  `action_criteria` is unchanged
        # and remains the default, so this is byte-identical for every existing caller.
        act = (self.build_action_criteria(goal) if hasattr(self, "build_action_criteria")
               else action_criteria(goal))
        questions[self.action_key] = {
            "type": "choice",
            "instructions": self.options.get(
                "action_instructions",
                "Choose the single next input that best serves the objective."),
            "criteria": act,
        }
        roles[self.action_key] = {"role": "action", "options": list(act)}
        # TASK-129 D-E: the playability question comes FIRST and under its own key
        # (`playable`), asked with exactly the wording TASK-124/127 used for
        # `playable_frame`, so the number is comparable with the earlier runs while the
        # name says what it means.
        invariants = [(self.playable_key, PLAYJEV_PLAYABLE_QUESTION)]
        for key, text in JEV_INVARIANT_QUESTIONS:
            if key == "playable_frame":
                continue          # already asked, as `playable`
            invariants.append((key, text))
        for key, text in invariants[:self.invariant_questions]:
            crit = {PLAYJEV_TRUE: "the frame does satisfy this statement",
                    PLAYJEV_FALSE: "the frame does not satisfy this statement"}
            questions[key] = {"type": "choice", "instructions": text, "criteria": crit}
            roles[key] = {"role": "noul", "options": list(crit),
                          "true_option": PLAYJEV_TRUE}
        if self.score_question:
            ordered = list(self.score_criteria)
            crit = dict(reversed(ordered) if self.legend_flipped else ordered)
            questions[self.score_key] = {
                "type": "choice",
                "instructions": ("Rate how broken this frame is, from %s (fully working) "
                                 "to %s (unusable)."
                                 % (ordered[0][0], ordered[-1][0])),
                "criteria": crit,
            }
            roles[self.score_key] = {"role": "score", "options": list(crit),
                                     "value_order": [name for name, _t in ordered],
                                     "legend_flipped": self.legend_flipped}
        for key, q in questions.items():
            if q.get("type") != "choice":
                raise JevProtocolError("playjev serves choice questions only (serve.py:53)")
            n = len(q["criteria"])
            if not (PLAYJEV_MIN_OPTIONS <= n <= PLAYJEV_MAX_OPTIONS):
                raise JevProtocolError(
                    "question %r has %d options; serve.py needs >= %d (serve.py:62) and "
                    "model.py allows at most %d" % (key, n, PLAYJEV_MIN_OPTIONS,
                                                    PLAYJEV_MAX_OPTIONS))
        return questions, roles

    def build_request(self, frames, state, goal):
        """Build the image-state request.  There is no text-state fallback."""
        usable = [f for f in (frames or [])
                  if f.get("path") and os.path.isfile(f["path"])]
        if not self.send_images:
            raise JevProtocolError(
                "PlayJev serves pixels only: with send_images=False there is no state "
                "to send (a text state is refused 400, serve.py:41-42)")
        if not usable:
            raise JevProtocolError(
                "PlayJev has no text-state path and no readable frame was given; the "
                "service would answer 400 'state must be {\"frames\": [...]}'")
        questions, roles = self.build_questions(goal or {})
        f = usable[-1]
        path = f["path"]
        with open(path, "rb") as fh:
            data = fh.read()
        payload = {
            "model": self.model,
            "state": {"frames": ["data:image/png;base64,%s"
                                 % base64.b64encode(data).decode("ascii")]},
            "questions": questions,
        }
        body = json.dumps(payload).encode("utf-8")
        meta = {
            "decision_path": self.decision_path,
            "transport": "state.frames (one data URL) -- NOT a top-level `image` field",
            "frame_path": path,
            "frame_bytes": len(data),
            "frame_sha256": f.get("sha256"),
            "frame_index": f.get("index"),
            "question_count": len(questions),
            "question_keys": list(questions.keys()),
            "question_types": dict((k, v["type"]) for k, v in questions.items()),
            "option_counts": dict((k, len(v["criteria"])) for k, v in questions.items()),
            "question_roles": dict((k, v["role"]) for k, v in roles.items()),
            "body_bytes": len(body),
            "image_plus_n_questions": True,
            "model_field_read_by_server": False,
        }
        if len(body) > JEV_LIMITS["image_request_max_bytes"]:
            raise JevProtocolError(
                "request body is %d bytes; kept under the Jev 8 MiB image cap so the "
                "same frame could go to either backend" % len(body))
        return payload, roles, meta

    # ---- response parsing ------------------------------------------------
    def parse_response(self, body):
        if not body:
            raise JevProtocolError("the service returned an empty body")
        try:
            data = json.loads(body)
        except Exception as e:  # noqa: BLE001
            raise JevProtocolError("the response body is not JSON: %s" % e)
        if not isinstance(data, dict) or not isinstance(data.get("answers"), dict):
            raise JevProtocolError("the response has no `answers` object: %s"
                                   % (list(data)[:8] if isinstance(data, dict) else type(data)))
        return data

    def classify_answer(self, key, role, answer):
        """One answer -> a record that says, explicitly, whether it is an ABSTAIN.

        The abstain rules, in order (any hit sets `abstain` and records why):
          1. the answer object is missing or not a dict;
          2. the server declared `abstain: true`;
          3. there are no usable `probabilities`;
          4. the declared `choice` is not one of the returned probabilities;
          5. `confidence` is below `abstain_min_confidence`;
          6. the option this role needs (yes/no, or a level) is absent.
        """
        rec = {"key": key, "role": role["role"], "answer": answer,
               "abstain": False, "abstain_reasons": []}
        if not isinstance(answer, dict):
            rec["abstain"] = True
            rec["abstain_reasons"].append("the server sent no answer object for this question")
            return rec
        if answer.get("abstain") is not None:
            rec["server_abstain"] = answer.get("abstain")
            if answer.get("abstain"):
                rec["abstain"] = True
                rec["abstain_reasons"].append("the server declared abstain=true")
        if answer.get("type") not in (None, "choice"):
            rec["abstain"] = True
            rec["abstain_reasons"].append("unexpected answer type %r" % answer.get("type"))
        probs = answer.get("probabilities")
        if not isinstance(probs, dict) or not probs:
            rec["abstain"] = True
            rec["abstain_reasons"].append("the answer carries no probabilities")
            return rec
        rec["probabilities"] = probs
        rec["confidence"] = answer.get("confidence")
        rec["choice"] = answer.get("choice")
        if answer.get("choice") not in probs:
            rec["abstain"] = True
            rec["abstain_reasons"].append(
                "choice %r is not one of the returned probabilities %s"
                % (answer.get("choice"), sorted(probs)[:8]))
        conf = answer.get("confidence")
        if isinstance(conf, (int, float)) and conf < self.abstain_min_confidence:
            rec["abstain"] = True
            rec["abstain_reasons"].append(
                "confidence %.6f < abstain_min_confidence %.6f"
                % (conf, self.abstain_min_confidence))
        if role["role"] == "noul":
            p = probs.get(role["true_option"])
            rec["noul"] = p if isinstance(p, (int, float)) else None
            if rec["noul"] is None:
                rec["abstain"] = True
                rec["abstain_reasons"].append(
                    "the option %r is missing from the probabilities" % role["true_option"])
        elif role["role"] == "score":
            # TASK-129 D-E: the expected level is ALWAYS computed against the canonical
            # level order (`value_order`), so a flip-legend probe measures the model and
            # not our own re-ordering of the options.
            order = role.get("value_order") or role["options"]
            idx = dict((name, i) for i, name in enumerate(order))
            tot, mass = 0.0, 0.0
            for name, p in probs.items():
                if name in idx and isinstance(p, (int, float)):
                    tot += (idx[name] + 1) * p
                    mass += p
            rec["score_mass"] = mass
            rec["score"] = (tot / mass) if mass > 0 else None
            rec["score_levels"] = role["options"]
            rec["legend_flipped"] = bool(role.get("legend_flipped"))
            if rec["score"] is None:
                rec["abstain"] = True
                rec["abstain_reasons"].append("no level probability was recognised")
        elif role["role"] == "action":
            rec["action_choice"] = answer.get("choice")
        return rec

    def collect_answers(self, answers, roles):
        """Classify EVERY question this agent asked -- a missing answer to a
        question we asked is an abstain, not a silence to be ignored."""
        out = {}
        for key, role in roles.items():
            out[key] = self.classify_answer(key, role, (answers or {}).get(key))
        return out

    # ---- the interface ---------------------------------------------------
    def decide(self, frames, state, goal):
        if not self.base_url:
            self._error("unconfigured", "PLAYTEST_BASE_URL is not set")
            return {"type": "wait", "ms": 100,
                    "why": "playjev backend unconfigured: PLAYTEST_BASE_URL is not set "
                           "(recorded, not a success)"}
        if self.decision_path not in PLAYJEV_DECISION_PATHS:
            self._error("unconfigured",
                        "unknown decision path %r; playjev serve.py provides %s"
                        % (self.decision_path, list(PLAYJEV_DECISION_PATHS)))
            return {"type": "wait", "ms": 100,
                    "why": "playjev backend misconfigured: decision path %r"
                           % self.decision_path}
        if self.require_health and self._ready is not True:
            rec = self.check_health()
            ok = rec.get("status") == 200
            if ok and isinstance(rec.get("json"), dict) and "ok" in rec["json"]:
                ok = bool(rec["json"]["ok"])
            if not ok:
                self._error("health", "GET %s failed: status=%s error=%s"
                            % (self.health_path, rec.get("status"), rec.get("error")),
                            body=(rec.get("body") or "")[:400])
                self._ready = False
                return {"type": "wait", "ms": 200,
                        "why": "playjev service is not reachable/ready (see recorded "
                               "health error); degraded to wait"}
            self._ready = True

        try:
            payload, roles, meta = self.build_request(frames, state, goal)
        except JevProtocolError as e:
            self._error("request", str(e))
            return {"type": "wait", "ms": 200,
                    "why": "playjev request refused before sending: %s" % e}
        except Exception as e:  # noqa: BLE001
            self._error("request", "%s: %s" % (type(e).__name__, e))
            return {"type": "wait", "ms": 200, "why": "playjev request build failed: %s" % e}

        rec = self._post_decision(payload)
        evidence = {"kind": "decision", "transport": rec, "request_meta": meta,
                    "request_payload": payload}
        if rec.get("status") != 200:
            msg = self._map_http_error(rec)
            self._error("http", msg, status=rec.get("status"))
            evidence["error"] = msg
            self.calls.append(evidence)
            self.last_evidence = evidence
            return {"type": "wait", "ms": 200, "why": msg}

        try:
            data = self.parse_response(rec.get("body"))
        except JevProtocolError as e:
            msg = "playjev response could not be parsed: %s" % e
            self._error("response", msg)
            evidence["error"] = msg
            self.calls.append(evidence)
            self.last_evidence = evidence
            return {"type": "wait", "ms": 200, "why": msg}

        answers = data["answers"]
        classified = self.collect_answers(answers, roles)
        abstained = sorted(k for k, r in classified.items() if r["abstain"])
        self.last_answers = classified
        self.last_roles = roles
        self.last_noul = dict((k, r) for k, r in classified.items() if r["role"] == "noul")
        self.last_scores = dict((k, r) for k, r in classified.items() if r["role"] == "score")
        self.last_timings = data.get("timing")
        evidence.update({
            "response_status": rec.get("status"),
            "model": data.get("model"),
            "timing": data.get("timing"),
            "answers_raw": answers,
            "answers_classified": classified,
            "probability_tables": dict((k, r.get("probabilities")) for k, r in classified.items()),
            "confidences": dict((k, r.get("confidence")) for k, r in classified.items()),
            "abstain": bool(abstained),
            "abstained_questions": abstained,
            "abstain_reasons": dict((k, classified[k]["abstain_reasons"]) for k in abstained),
            "unrequested_answers": sorted(set(answers) - set(roles)),
            # TASK-129 D-E: the playability answer under its own key, and the score kept
            # as an explicitly direction-suspect observation OUTSIDE the verdict.
            "playable_key": self.playable_key,
            "score_observation": {
                "in_decision_path": False, "direction": "suspect", "uncalibrated": True,
                "note": PLAYJEV_SCORE_DIRECTION_NOTE,
                "legend_flipped": bool(self.legend_flipped),
                "values": dict((k, r.get("score")) for k, r in classified.items()
                               if r["role"] == "score")},
        })
        act = None
        a = classified.get(self.action_key)
        if a is not None and a["abstain"]:
            msg = ("playjev ABSTAINED on %s (undecidable, NOT a success): %s"
                   % (self.action_key, "; ".join(a["abstain_reasons"])))
            self._error("abstain", msg, question=self.action_key)
            evidence["error"] = msg
            act = {"type": "wait", "ms": 200, "why": msg}
        elif a is not None:
            why = ("playjev choice=%r confidence=%s probabilities=%s"
                   % (a.get("choice"), a.get("confidence"), a.get("probabilities")))
            act = action_from_choice(a.get("choice"), goal, self.hold_ms, why)
        if act is None:
            msg = ("playjev returned no usable choice (answers=%s)"
                   % list(answers.keys())[:8])
            self._error("response", msg)
            evidence["error"] = msg
            act = {"type": "wait", "ms": 200, "why": msg}
        evidence["action"] = act
        self.calls.append(evidence)
        self.last_evidence = evidence
        return act

    def _map_http_error(self, rec):
        status = rec.get("status")
        detail = (rec.get("body") or "")[:300]
        n = len(rec.get("attempts") or [])
        if status == 400:
            return ("playjev refused the request as invalid (400) -- it serves choice "
                    "questions over `state.frames` and nothing else: %s" % detail)
        if status == 404:
            return ("playjev has no such path (404): the only decision endpoint is "
                    "POST /v1/systemone (serve.py:111). body=%s" % detail)
        if status == 500:
            return ("playjev failed on the request (500): %s" % detail)
        if status in (429, 529):
            return ("playjev worker is busy (HTTP %s) and still busy after %d attempts; "
                    "`Retry-After` was honoured. body=%s" % (status, n, detail))
        if status is None:
            return "playjev service is not reachable (%s)" % rec.get("error")
        return "playjev service returned HTTP %s: %s" % (status, detail)

    def judge(self, frames, state, goal):
        """Machine-readable verdict from the noul/score answers.  `decide()`'s
        evidence is reused (one forward pass is enough and the service serialises)."""
        if self.last_evidence is None:
            self.decide(frames, state, goal)
        return self.threshold_verdict()

    def threshold_verdict(self):
        crit = []
        noul_obs = []
        for key, r in sorted(self.last_noul.items()):
            val = r.get("noul")
            obs = {"id": "noul:%s" % key, "value": val,
                   "confidence": r.get("confidence"),
                   "probabilities": r.get("probabilities"),
                   "abstain": r["abstain"], "abstain_reasons": r["abstain_reasons"]}
            if self.verdict_invariant_keys is not None \
                    and key not in self.verdict_invariant_keys:
                obs["in_decision_path"] = False
                noul_obs.append(obs)
                continue
            ok = (not r["abstain"]) and isinstance(val, (int, float)) \
                and val >= self.thresholds["noul_min_p_true"]
            obs.update({"rule": "P(true) >= %.3f"
                                % self.thresholds["noul_min_p_true"],
                        "pass": bool(ok), "in_decision_path": True})
            crit.append(obs)
        # TASK-129 D-E: the score answers are OBSERVATIONS.  Their value is never a
        # pass/fail criterion; only a structurally unusable answer (an abstain) can make
        # the verdict undecidable, which is TASK-127's "an abstain is not a pass" rule.
        score_obs = []
        for key, r in sorted(self.last_scores.items()):
            val = r.get("score")
            obs = {"id": "score:%s" % key, "value": val,
                   "direction": "suspect",
                   "in_decision_path": bool(self.score_in_verdict),
                   "levels": r.get("score_levels"),
                   "legend_flipped": r.get("legend_flipped"),
                   "probabilities": r.get("probabilities"),
                   "confidence": r.get("confidence"),
                   "abstain": r["abstain"], "abstain_reasons": r["abstain_reasons"]}
            if self.score_in_verdict:
                obs["rule"] = ("expected level <= %.3f"
                               % self.thresholds["score_max_expected"])
                obs["pass"] = bool((not r["abstain"]) and isinstance(val, (int, float))
                                   and val <= self.thresholds["score_max_expected"])
                crit.append(obs)
            score_obs.append(obs)
        undecidable = sorted(c["id"] for c in crit if c["abstain"])
        if not self.score_in_verdict and self.score_abstain_blocks_verdict:
            undecidable = sorted(set(undecidable) | set(o["id"] for o in score_obs
                                                        if o["abstain"]))
        if not crit and not score_obs:
            verdict = None
        elif not crit:
            # only observations were collected (score_question alone): neither a pass nor
            # a fail can be claimed
            verdict = None
        elif undecidable:
            verdict = None           # an abstain is NEVER a pass
        else:
            verdict = all(c["pass"] for c in crit)
        return {"backend": "playjev", "pass": verdict,
                "decidable": not undecidable,
                "undecidable": undecidable,
                "why": ("no answer was captured at all: no threshold verdict is possible"
                        if (not crit and not noul_obs and not score_obs) else
                        ("no question is in the decision path: no verdict is possible"
                         if not crit else
                         ("%d criterion/criteria abstained: no verdict (an abstain is not "
                          "a pass)" % len(undecidable) if undecidable else
                          ("%d/%d threshold criteria passed"
                           % (sum(1 for c in crit if c["pass"]), len(crit)))))),
                "criteria": crit,
                "noul_observations": noul_obs,
                "verdict_invariant_keys": self.verdict_invariant_keys,
                "score_observations": score_obs,
                "score_in_decision_path": bool(self.score_in_verdict),
                "score_direction_note": PLAYJEV_SCORE_DIRECTION_NOTE,
                "legend_flipped": bool(self.legend_flipped),
                "thresholds": dict(self.thresholds),
                "abstain_min_confidence": self.abstain_min_confidence,
                "uncalibrated": True,
                "note": JEV_THRESHOLD_NOTE,
                "abstain_note": PLAYJEV_ABSTAIN_NOTE,
                "source": ("last decision response" if self.last_evidence else "none")}

    def score_observation_only(self):
        """TASK-129 D-E: what the VISION backend says about brokenness, as an observation.

        Returned separately from `threshold_verdict()` so no caller can accidentally use it
        as a verdict, and marked with the reason it is not one.
        """
        return {"role": "observation", "in_decision_path": False,
                "direction": "suspect", "uncalibrated": True,
                "note": PLAYJEV_SCORE_DIRECTION_NOTE,
                "legend_flipped": bool(self.legend_flipped),
                "questions": [k for k, r in sorted(self.last_scores.items())],
                "values": dict((k, r.get("score")) for k, r in sorted(self.last_scores.items())),
                "per_question": dict((k, {"value": r.get("score"),
                                          "levels": r.get("score_levels"),
                                          "legend_flipped": r.get("legend_flipped"),
                                          "probabilities": r.get("probabilities"),
                                          "confidence": r.get("confidence"),
                                          "abstain": r["abstain"]})
                                     for k, r in sorted(self.last_scores.items()))}

    def report(self):
        rep = PlaytestAgent.report(self)
        rep.update({"base_url": self.base_url, "model": self.model,
                    "decision_path": self.decision_path, "health": self.health,
                    "errors": self.errors, "attempts": self.attempts,
                    "playable_key": self.playable_key,
                    "invariant_questions": self.invariant_questions,
                    "score_in_verdict": self.score_in_verdict,
                    "legend_flipped": self.legend_flipped,
                    "abstain_min_confidence": self.abstain_min_confidence,
                    "thresholds": dict(self.thresholds),
                    "last_timings": self.last_timings,
                    "score_observation": self.score_observation_only(),
                    "last_abstained": sorted(k for k, r in self.last_answers.items()
                                             if r["abstain"]),
                    "threshold_verdict": self.threshold_verdict()})
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
    if n == "jev":
        return JevAgent(game, objective, options)
    if n == "playjev":
        return PlayJevAgent(game, objective, options)
    raise ValueError("unknown agent backend %r (expected scripted|openai|jev|playjev)"
                     % name)


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
    if args[0] == "--probe-jev":
        # TASK-124 D: the jev dumb-service verification lives in tools/tests/ so it is
        # also runnable on its own.  No weights, no GPU, stdlib only.
        tests_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests")
        sys.path.insert(0, tests_dir)
        import test_jev_agent
        r = test_jev_agent.run_all(verbose=True, argv=args[1:])
        return 0 if r["ok"] else 1
    if args[0] == "--probe-playjev":
        # TASK-127: same idea for the PlayJev backend -- a stdlib dumb
        # /v1/systemone service that VALIDATES the request against the deployed
        # serve.py's rules.  No weights, no GPU, stdlib only.
        tests_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests")
        sys.path.insert(0, tests_dir)
        import test_playjev_agent
        r = test_playjev_agent.run_all(verbose=True, argv=args[1:])
        return 0 if r["ok"] else 1
    if args[0] == "--selfcheck":
        # interface shape only, no network.  The two decision backends are pointed at
        # a port nothing listens on, so this proves the DEGRADED path (a recorded safe
        # action) without ever touching a real service.
        dead = {"base_url": "http://127.0.0.1:9", "timeout": 2}
        for backend in ("scripted", "openai", "jev", "playjev"):
            ag = build_agent(backend, "demo", "demo", dead)
            act = ag.decide([], {}, {"keys": ["W", "SPACE"]})
            print(json.dumps({"backend": backend, "name": ag.name, "action": act},
                             ensure_ascii=False))
        return 0
    print("unknown arguments: %r (try --probe, --probe-jev, --probe-playjev, "
          "--selfcheck or --help)" % (args,))
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
