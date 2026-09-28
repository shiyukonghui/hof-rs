# -*- coding: utf-8 -*-
"""TASK-140 §I: list the residual `code`-classified source hits and their file/line/text.

Usage (through the ledger wrapper):
    t140_cmd.py --cwd F:\\moonbit-hof-rs\\godot-mcp -- <py> runs\\model-player\\_scripts\\t140_scan_show.py
"""
from __future__ import print_function

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, "t140_redirect_scan.json")


def main():
    with io.open(P, encoding="utf-8") as fh:
        rep = json.load(fh)
    print("commands=%d hits=%d false_positives=%d shell_true=%d"
          % (rep["this_batch_commands"], rep["hits"], len(rep["false_positives"]),
             len(rep["shell_true"])))
    print("cut: first_task140_index=%s first_ts=%s"
          % (rep["cut"]["first_task140_index"], rep["this_batch_first_ts"]))
    code = [h for h in rep["script_hits"] if h["kind"] == "code"]
    print("residual code hits: %d" % len(code))
    for h in code:
        print("  %s:%d [%s] %s" % (os.path.basename(h["file"]), h["line"], h["token"],
                                   h["text"][:110]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
