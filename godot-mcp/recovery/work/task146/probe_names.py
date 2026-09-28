#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prototype: parse the TC-PY rows of recovery/TEST-CASES.md and check that each
row's referenced test name really exists.  Prints every mismatch."""
import html
import io
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
MD = os.path.join(REPO, "recovery", "TEST-CASES.md")

ID_RE = re.compile(r"^\|\s*(TC-(?:TOOL|GATE|M1|ENG|PY|CONS))-[^|]*\|")


def unesc(s):
    return html.unescape(s)


def rows():
    with io.open(MD, "r", encoding="utf-8") as fh:
        lines = fh.readlines()
    out = []
    for ln, line in enumerate(lines, 1):
        s = line.rstrip("\n")
        if not s.startswith("| TC-PY-"):
            continue
        cells = [c.strip() for c in s.split("|")]
        # cells[0] == '' ; cells[1] == id
        ident = cells[1]
        src = cells[2].strip("`")
        item = ident.split(":", 1)[1] if ":" in ident else ""
        note = cells[-2]
        out.append({"line": ln, "id": ident, "src": src, "item": item,
                    "note": note})
    return out


def kind_of(note):
    if "pytest 条目" in note:
        return "pytest"
    if "脚本内 check" in note:
        return "script_check"
    if "自打印的 case 名" in note:
        return "printed"
    return "unknown"


def run_printed(rel):
    path = os.path.join(REPO, rel.replace("/", os.sep))
    proc = subprocess.run([sys.executable, path], cwd=REPO,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = proc.stdout.decode("utf-8", "replace")
    names = []
    base = os.path.basename(rel)
    if base == "test_playability_p7.py":
        for line in text.splitlines():
            if line.startswith("ok  ") or line.startswith("FAIL"):
                names.append(line[6:].rstrip())
    elif base == "test_playability_model_player.py":
        for line in text.splitlines():
            m = re.match(r"^(.*?)\s+(OK|MISMATCH)(\s|$)", line)
            if not m:
                continue
            cand = m.group(1).rstrip()
            if len(cand) >= 58:
                cand = line[:58].rstrip()
            names.append(cand)
    return names, proc.returncode


def main():
    rs = rows()
    print("TC-PY rows: %d" % len(rs))
    bysrc = {}
    for r in rs:
        bysrc.setdefault(r["src"], []).append(r)
    problems = []
    for src in sorted(bysrc):
        group = bysrc[src]
        kinds = {}
        for r in group:
            kinds.setdefault(kind_of(r["note"]), []).append(r)
        print("%s: %s" % (src, {k: len(v) for k, v in kinds.items()}))
        path = os.path.join(REPO, src.replace("/", os.sep))
        if not os.path.exists(path):
            problems.append("missing file %s" % src)
            continue
        with io.open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
        want_pytest = len(re.findall(r"^def test_", text, re.M))
        have_pytest = len(kinds.get("pytest", []))
        print("   def test_ in file=%d, pytest rows=%d" % (want_pytest, have_pytest))
        for r in kinds.get("pytest", []):
            if not re.search(r"^def %s\(" % re.escape(r["item"]), text, re.M):
                problems.append("line %d: pytest %r not found in %s"
                                % (r["line"], r["item"], src))
        for r in kinds.get("script_check", []):
            if ('["%s"]' % r["item"]) not in text:
                problems.append("line %d: check %r not found in %s"
                                % (r["line"], r["item"], src))
        for r in kinds.get("unknown", []):
            problems.append("line %d: unknown note %r" % (r["line"], r["note"]))
        if kinds.get("printed"):
            names, code = run_printed(src)
            print("   printed=%d exit=%d" % (len(names), code))
            nset = set(names)
            missing = []
            for r in kinds["printed"]:
                if unesc(r["item"]) not in nset:
                    missing.append((r["line"], r["item"]))
            print("   printed rows=%d, not found=%d" % (len(kinds["printed"]), len(missing)))
            for ln, nm in missing[:15]:
                problems.append("line %d: printed case %r not printed by %s"
                                % (ln, nm, src))
    print("")
    print("PROBLEMS: %d" % len(problems))
    for p in problems[:60]:
        print("  " + p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
