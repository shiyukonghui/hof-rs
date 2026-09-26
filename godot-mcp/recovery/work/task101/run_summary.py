# -*- coding: utf-8 -*-
"""TASK-098: the one-glance summary of a finished run directory.

Prints exactly the numbers the task書 asks for: call counts per phase, the verdict
distribution, facts_complete, the pixel column, and the two declared failures. It reads
report.json (written by tools/game_report.py) rather than re-deriving anything, so the
summary and the report cannot disagree.
"""
import io
import json
import os
import sys


def main():
    run = sys.argv[1]
    with io.open(os.path.join(run, "report.json"), "r", encoding="utf-8") as handle:
        rep = json.load(handle)

    print("run        : %s" % run)
    print("game       : %s  tag: %s  pillow: %s" % (rep["game"], rep["run_tag"], rep["pillow"]))
    total_calls = 0
    total_facts = 0
    verdicts = {}
    for name in ("editor", "game"):
        summary = rep["endpoints"][name]["ledger"]
        if summary is None:
            print("%-7s: NO LEDGER" % name)
            continue
        calls = summary["calls"] or 0
        total_calls += calls
        total_facts += summary["facts_complete"]
        for key, value in (summary["verdicts"] or {}).items():
            verdicts[key] = verdicts.get(key, 0) + value
        print("%-7s: calls=%-3d facts=%d/%d  args=%s" % (
            name, calls, summary["facts_complete"], calls,
            ", ".join("%s=%d" % kv for kv in sorted((summary["args_evidence"] or {}).items()))))
        print("         verdicts=%s" % ", ".join(
            "%s=%d" % kv for kv in sorted((summary["verdicts"] or {}).items())))
    print("-" * 78)
    print("TOTAL  : calls=%d  facts_complete=%d/%d (%.1f%%)"
          % (total_calls, total_facts, total_calls,
             100.0 * total_facts / total_calls if total_calls else 0.0))
    print("         verdicts=%s" % ", ".join("%s=%d" % kv for kv in sorted(verdicts.items())))

    pairs = []
    for name in ("editor", "game"):
        for pair in rep["endpoints"][name]["captures"]:
            pairs.append((name, pair))
    nonzero = [(n, p) for n, p in pairs
               if ((p.get("recomputed") or {}).get("changed_pixels") or 0) > 0]
    print("pixels : %d capture pairs, %d recomputed non-zero (editor %d/%d, game %d/%d)"
          % (len(pairs), len(nonzero),
             len([1 for n, p in nonzero if n == "editor"]),
             len([1 for n, p in pairs if n == "editor"]),
             len([1 for n, p in nonzero if n == "game"]),
             len([1 for n, p in pairs if n == "game"])))
    print("         pixel_evidence verdict=%s" % rep["pixel_evidence"]["verdict"])

    frames = (rep.get("saved_frames") or {}).get("frames") or []
    print("frames : %d in %s" % (len(frames), (rep.get("saved_frames") or {}).get("dir")))
    prev = None
    for frame in frames:
        diff = frame.get("diff_vs_prev") or {}
        print("         %-12s %-9s %6d B  %s  px_vs_prev=%s"
              % (frame["name"], "x".join(str(v) for v in (frame.get("size") or ["?"])),
                 frame["bytes"], frame["sha256"][:12],
                 diff.get("changed_pixels", "-")))

    defects = rep.get("defects") or []
    print("defects: %d (auto)" % len(defects))
    for defect in defects:
        print("         [%s] %s | %s" % (defect["severity"], defect["claim"], defect["root_cause"]))

    mismatches = []
    for name, pair in pairs:
        if pair.get("recomputed_matches_reported") is False:
            mismatches.append((name, pair.get("seq")))
    print("recomputed-vs-trace mismatches: %s" % (mismatches or "none"))


if __name__ == "__main__":
    main()
