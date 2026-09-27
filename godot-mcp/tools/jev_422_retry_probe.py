#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""jev_422_retry_probe.py -- TASK-129 D-C: prove the "answer a real 422 by halving" rule.

Why this exists
---------------
D-C asks for two things beyond the estimator fix: a **real** `422 state exceeds N tokens`
retry record, and a bounded number of retries with per-attempt evidence.  Now that
`jev_estimate_tokens` carries a conservative x2.5 coefficient, the gate no longer produces
that 422 by accident -- which is the point.  So the retry is exercised with a state built to
be exactly the case the client CANNOT see: a JSON document made of thousands of very short
tokens (`{"k12":0,...}`), which tokenizes far denser than the "4 ASCII chars per token"
assumption and therefore passes the client guard while the service's own tokenizer refuses
it.  Everything the probe measures is the real service's real behaviour on 127.0.0.1:8080:

  * the client-side estimate and the service's verbatim 422 body;
  * the halving the agent performs, with the nodes/characters it dropped;
  * the final status and the agent's own `state_budget_retries` evidence.

Nothing is stubbed and no third-party endpoint is contacted.  Serial by construction (the
agent locks), one state at a time.

Usage (from godot-mcp, cmd):
    python tools\\jev_422_retry_probe.py --base-url http://127.0.0.1:8080
"""

from __future__ import print_function

import argparse
import io
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from playtest_agent import (JevAgent, jev_estimate_tokens,   # noqa: E402
                            jev_estimate_tokens_raw, jev_render_state, JEV_LIMITS)

OUT_DEFAULT = os.path.join(ROOT, "runs", "playability", "t129-jev-422-retry.json")
GOAL = {"game": "probe", "objective": "exercise the 422 budget retry",
        "actions": {"probe_move": ["W"]}, "keys": []}


DENSE_ALPHABET = ("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/")


def dense_chunk(n, seed=12345):
    """`n` characters of a DETERMINISTIC pseudo-random base64-ish string.

    Why this shape: the client's estimator charges one token per four ASCII characters,
    which is right for prose.  Random base64 tokenizes at ~1.3-1.5 characters per token,
    so the client under-counts it by ~2.5-3x -- exactly the case D-C's 422 retry exists
    for.  The sequence is an LCG, so the probe is reproducible byte for byte.
    """
    out = []
    x = seed
    for _ in range(n):
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        out.append(DENSE_ALPHABET[(x >> 16) % 64])
    return "".join(out)


def dense_state(chunks, chunk_len=400):
    """The gate's shape (`nodes`), with token-dense strings as the payload."""
    nodes = {}
    for i in range(chunks):
        nodes["b%d" % i] = dense_chunk(chunk_len, seed=1000 + i)
    return {"nodes": nodes, "node_count": chunks, "drawn": 1, "ms": 0}


def build_over_limit_state(agent, chunk_len=400, max_chunks=40):
    """The LARGEST dense state the CLIENT accepts (`estimate <= 2048`) -- the exact case
    the client cannot see: it fits the estimate and still exceeds the service's real count.
    """
    log = []
    accepted, accepted_chunks = None, None
    for chunks in range(1, max_chunks + 1):
        state = dense_state(chunks, chunk_len)
        est = jev_estimate_tokens(jev_render_state(state))
        raw = jev_estimate_tokens_raw(jev_render_state(state))
        ok = est <= JEV_LIMITS["state_max_tokens"]
        log.append({"chunks": chunks, "chars": chunks * chunk_len,
                    "client_estimate": est, "client_raw": raw,
                    "client_accepts": ok,
                    "client_refuses": (not ok)})
        if ok:
            accepted, accepted_chunks = state, chunks
        else:
            break
    return accepted, accepted_chunks, log


def main(argv=None):
    ap = argparse.ArgumentParser(description="TASK-129 real 422 retry probe")
    ap.add_argument("--base-url", default="http://127.0.0.1:8080")
    ap.add_argument("--out", default=OUT_DEFAULT)
    ap.add_argument("--max-state-retries", type=int, default=2)
    args = ap.parse_args(argv)

    doc = {"task": "TASK-129 D-C", "purpose": "a REAL 422 state-overflow and the bounded "
                                              "halving retry that answers it",
           "third_party_endpoints_used": [],
           "started": time.strftime("%Y-%m-%d %H:%M:%S"),
           "question_types_sent": ["noul"],
           "attempts": [], "state_budget_retries": [], "final": None}

    agent = JevAgent("probe", GOAL["objective"],
                     {"base_url": args.base_url, "model": "NeoHorse-Jev-4B",
                      "max_retries": 0, "max_state_retries": args.max_state_retries,
                      "timeout": 120})
    health = agent.check_health()
    doc["endpoint"] = agent.base_url + agent.decision_path
    doc["health"] = {"status": health.get("status"), "url": health.get("url"),
                     "json": health.get("json")}
    print("health: %s %s" % (health.get("status"), health.get("json")))

    state, chosen, log = build_over_limit_state(agent)
    doc["size_search"] = log
    doc["chosen_size"] = [e for e in log if e["chunks"] == chosen]
    last = doc["chosen_size"][0] if doc["chosen_size"] else {}
    print("dense state: %s chunks / %s chars, client estimate %s (cap %s)"
          % (chosen, last.get("chars"), last.get("client_estimate"),
             JEV_LIMITS["state_max_tokens"]))

    hit = None
    if state is None:
        doc["result"] = "no state was built; reported, not hidden"
    else:
        payload = {"model": agent.model, "state": state,
                   "questions": {"q": {"type": "noul", "instructions": "Is this fine?"}}}
        rec = agent._request("POST", agent.decision_path, payload)
        hit = {"client_estimate": last.get("client_estimate"),
               "service_status": rec.get("status"),
               "service_body": (rec.get("body") or "")[:300],
               "seconds": rec.get("seconds")}
        doc["refused_state"] = hit
        print("direct POST -> %s %s" % (hit["service_status"], hit["service_body"]))

    if not hit or hit.get("service_status") != 422:
        doc["result"] = ("the service did NOT refuse this state (status=%s), so the 422 "
                         "retry path could not be exercised with it -- reported, not hidden"
                         % (hit or {}).get("service_status"))
        print(doc["result"])
    else:
        # now the real thing: the agent's own decide() must halve and retry, bounded
        action = agent.decide([], state, GOAL)
        ev = agent.last_evidence or {}
        retries = ev.get("state_budget_retries") or []
        doc["state_budget_retries"] = retries
        doc["transport_attempts"] = (ev.get("transport") or {}).get("attempts")
        doc["final"] = {
            "action": action,
            "status": (ev.get("transport") or {}).get("status"),
            "model": ev.get("model"),
            "usage": ev.get("usage"),
            "errors": [e for e in agent.errors],
            "n_retries": len(retries),
            "bounded_by": args.max_state_retries,
            "answer_keys": sorted((ev.get("answers_raw") or {}).keys()),
            "noul": {k: (v or {}).get("noul") for k, v in (ev.get("noul") or {}).items()},
        }
        print("after %d retry(ies): status=%s model=%s action=%s"
              % (len(retries), doc["final"]["status"], doc["final"]["model"],
                 (action or {}).get("type")))
        if retries:
            for r in retries:
                print("   retry %s: %s -> %s tokens, dropped %s node(s), policy=%s"
                      % (r.get("attempt"), r.get("before_tokens_estimate"),
                         r.get("after_tokens_estimate"),
                         len(r.get("nodes_dropped") or []), r.get("policy")))
    doc["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with io.open(args.out, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(doc, ensure_ascii=False, indent=1))
    print("written: %s" % os.path.abspath(args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
