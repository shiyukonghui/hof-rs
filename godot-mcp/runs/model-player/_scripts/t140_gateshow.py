# -*- coding: utf-8 -*-
"""TASK-140 §1.A.3 (Y3): show `gate.json -> model_player_criterion`'s new attribution fields.

Usage (through the ledger wrapper):
    t140_cmd.py --cwd F:\\moonbit-hof-rs\\godot-mcp -- <py> runs\\model-player\\_scripts\\t140_gateshow.py <gate.json...>
"""
from __future__ import print_function

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))


def main(argv):
    for p in argv:
        if p.startswith("--"):
            continue
        p = p if os.path.isabs(p) else os.path.join(ROOT, p)
        if not os.path.isfile(p):
            print("no file: %s" % p)
            continue
        with io.open(p, encoding="utf-8") as fh:
            g = json.load(fh)
        ev = ((g.get("model_player_criterion") or {}).get("evidence")) or {}
        print("== %s" % os.path.relpath(p, ROOT))
        print("   model_player_criterion.steps_file = %s"
              % (g.get("model_player_criterion") or {}).get("steps_file"))
        print("   verdict=%s (pass=%s)" % (ev.get("verdict"), ev.get("pass")))
        print("   qualified_verdict = %s" % ev.get("qualified_verdict"))
        print("   verdict_context   = %s" % json.dumps(ev.get("verdict_context"),
                                                       ensure_ascii=False))
        print("   reporting_window  = %s" % json.dumps(ev.get("reporting_window"),
                                                       ensure_ascii=False))
        print("   reporting_why     = %s" % ev.get("reporting_why"))
        print("   criteria: %s" % json.dumps(
            dict((k, v) for k, v in (g.get("criteria") or {}).items()
                 if k in ("P7",)), ensure_ascii=False)[:200])
        print("   scope: %s" % (g.get("scope") or g.get("only_p7")))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
