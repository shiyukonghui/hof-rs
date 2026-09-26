"""TASK-089: before/after ledger comparison over the SAME call set.

The two sessions ran the same 45 calls (ids 102..131 on the editor endpoint,
201..215 on the game endpoint) against the same mini project with the same
switches. Only the tool's values differed per run (a run tag in the text, the
colour, the setting) so that "the first call really changes something" also
holds on the second run.

Prints, per endpoint, every call whose scene_effect / file_effect / verdict
changed, plus the aggregate counts of both runs.
"""
import io
import json
import sys


def load(path):
    payload = json.load(io.open(path, encoding="utf-8"))
    return {(row["generation"], row["call_id"]): row for row in payload["rows"]}


def counts(rows):
    out = {}
    for row in rows.values():
        out[row["verdict"]] = out.get(row["verdict"], 0) + 1
    return out


def main():
    base = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task089"
    for endpoint in ("editor", "game"):
        before = load(base + r"\live-before\ledger-%s.json" % endpoint)
        after = load(base + r"\live-after\ledger-%s.json" % endpoint)
        print("=== %s endpoint ===" % endpoint)
        print("calls before=%d after=%d" % (len(before), len(after)))
        print("verdicts before: %s" % json.dumps(counts(before), sort_keys=True))
        print("verdicts after : %s" % json.dumps(counts(after), sort_keys=True))
        changed = 0
        for key in sorted(before, key=lambda k: (k[0], k[1])):
            if key not in after:
                print("  MISSING in after: %s" % (key,))
                continue
            b = before[key]
            a = after[key]
            fields = ("scene_effect", "file_effect", "verdict", "ok", "error_code")
            diffs = [(f, b[f], a[f]) for f in fields if b[f] != a[f]]
            if diffs:
                changed += 1
                print("  seq=%-3s id=%-4s %-40s %s" % (
                    b["call_id"], b["request_id"], b["tool"],
                    "; ".join("%s %r->%r" % d for d in diffs)))
        if changed == 0:
            print("  (no scene/file/verdict field changed for any call)")
        # The flags are new in the after run (the before trace carries no
        # result_json), so they are listed separately rather than as a diff.
        flagged = [(k, r) for k, r in sorted(after.items(), key=lambda kv: kv[0][1]) if r.get("result_flags")]
        print("  after-run calls carrying a result flag: %d" % len(flagged))
        for key, row in flagged:
            print("    seq=%s id=%s %s flags=%s" % (
                row["call_id"], row["request_id"], row["tool"], ",".join(row["result_flags"])))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
