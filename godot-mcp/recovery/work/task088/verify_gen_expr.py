# -*- coding: utf-8 -*-
"""task088 (3): unit-test the two repaired lines of _tmp_gen_b3_b5.py.

The generator cannot run end to end on today's tree (its SPEC predates the six
ADDED_TOOLS, so its own completeness check exits 1 before serialising - a
pre-existing condition, not a regression). What CAN be tested directly is the
change itself: bind `contract_names` to the real contract and evaluate exactly
the two expressions that now stand in the file.

usage: python verify_gen_expr.py <outfile>
"""
from __future__ import print_function
import io, json, re, sys

REPO = r"H:\rebuild\godot"
GEN = REPO + r"\modules\mcp_server\docs\scripts\_tmp_gen_b3_b5.py"
CONTRACT = REPO + r"\modules\mcp_server\docs\tools_list.renamed.json"


def main():
    out = sys.argv[1]
    src = io.open(GEN, encoding="utf-8").read()
    contract = json.load(io.open(CONTRACT, encoding="utf-8"))
    names = [t["name"] for t in contract["result"]["tools"]]
    env = {"contract_names": names}

    lines = []
    lines.append("contract entries = %d" % len(names))
    exprs = []
    m = re.search(r'^\s*"names": (".*" % \(len\(contract_names\),\)),?$', src, re.M)
    if not m:
        raise SystemExit("REFUSED: the repaired `names` line was not found")
    exprs.append(("names", m.group(1)))
    m2 = re.search(r'^\s*"excluded": (".*" % \(len\(contract_names\),\)),?$', src, re.M)
    if not m2:
        raise SystemExit("REFUSED: the repaired `excluded` line was not found")
    exprs.append(("excluded", m2.group(1)))

    ok = True
    for tag, expr in exprs:
        value = eval(expr, env)
        has_real = ("%d" % len(names)) in value
        has_stale = "171" in value
        if not has_real or has_stale:
            ok = False
        lines.append("%s: evaluates to -> %s" % (tag, value))
        lines.append("   names the real size (%d): %s   still says 171: %s"
                     % (len(names), has_real, has_stale))

    # Counter-check: the text this line USED to hold is now false.
    old_text = "docs/tools_list.renamed.json (171 entries) minus the 66 tools"
    lines.append("the literal this line used to carry is still in the file: %s"
                 % (old_text in src))
    if old_text in src:
        ok = False
    # No scanned number may remain on either repaired line.
    scanned = ("171", "173", "175", "176", "152", "72", "153")
    for tag, expr in exprs:
        hit = [n for n in scanned if re.search(r"(?<![0-9A-Za-z_])%s(?![0-9A-Za-z_])" % n, expr)]
        lines.append("%s: scanned numbers on the line = %s" % (tag, hit if hit else "none"))
        if hit:
            ok = False
    lines.append("RESULT: %s" % ("PASS" if ok else "FAIL"))
    data = "\n".join(lines) + "\n"
    io.open(out, "w", encoding="utf-8", newline="\n").write(data)
    print(data)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
