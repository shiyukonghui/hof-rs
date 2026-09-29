"""Independent acceptance: does the ten-gate path carry any EXECUTABLE
cross-repository reference?  Scans every file a gate command actually runs.

For .py the string-literal scan excludes module/class/function docstrings (an AST
walk), i.e. it reports only constants that can reach an interpreter call.  For
.ps1/.psm1 the classifier is line-based: a line whose first non-space character
is '#' is a comment, everything else could execute.
"""
import ast
import io
import os
import re
import sys

ENGINE = r"F:\moonbit-hof-rs\godot-mcp\godot"
NEEDLES = ("moonbit-hof-rs", "hof-rs")

GATE_FILES = [
    r"modules\mcp_server\docs\scripts\check_tool_groups.py",
    r"modules\mcp_server\scripts\check_contract_subset.ps1",
    r"modules\mcp_server\docs\scripts\check_rename_map.py",
    r"modules\mcp_server\scripts\check_tautologies.py",
    r"modules\mcp_server\scripts\check_exit_propagation.py",
    r"modules\mcp_server\scripts\check_hardcoded_counts.py",
    r"modules\mcp_server\scripts\check_engine_anchor.ps1",
    r"modules\mcp_server\scripts\accept_m1.ps1",
]

total_exec = 0
for rel in GATE_FILES:
    path = os.path.join(ENGINE, rel)
    raw = io.open(path, "r", encoding="utf-8", errors="replace").read()
    if not any(n in raw.lower() for n in NEEDLES):
        print("%-58s NO hof-rs text at all" % rel)
        continue
    lines = raw.splitlines()
    hits = [(i + 1, l) for i, l in enumerate(lines)
            if any(n in l.lower() for n in NEEDLES)]
    print("%-58s %d textual hit(s)" % (rel, len(hits)))
    if rel.endswith(".py"):
        tree = ast.parse(raw)
        docstrings = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                b = getattr(node, "body", None)
                if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) \
                        and isinstance(b[0].value.value, str):
                    docstrings.add(id(b[0].value))
        exec_lines = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if id(node) in docstrings:
                    continue
                if any(n in node.value.lower() for n in NEEDLES):
                    exec_lines.add(node.lineno)
        for ln, l in hits:
            kind = "EXECUTABLE" if ln in exec_lines else "comment/docstring"
            if kind == "EXECUTABLE":
                total_exec += 1
            print("    :%d  [%s]  %s" % (ln, kind, l.strip()[:110]))
    else:
        for ln, l in hits:
            st = l.lstrip()
            kind = "comment" if st.startswith("#") else "EXECUTABLE"
            if kind == "EXECUTABLE":
                total_exec += 1
            print("    :%d  [%s]  %s" % (ln, kind, st[:110]))

print()
print("EXECUTABLE cross-repo references on the ten-gate path: %d" % total_exec)
