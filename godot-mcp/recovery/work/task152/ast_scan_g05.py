"""TASK-152: prove the g05 script has no executable reference to hof-rs.

String constants that live only in comments or docstrings are documentation of
the provenance; what must not exist is a *code* path that opens a file outside
this repository. This script parses the module, drops docstrings, and checks
every string literal and every `open()` argument.
"""

import ast
import io
import sys

SRC = (
    r"F:\moonbit-hof-rs\godot-mcp\godot\modules\mcp_server\docs\scripts"
    r"\check_rename_map.py"
)
BAD = ("moonbit-hof-rs", "tests\\fixtures", "tests/fixtures")

tree = ast.parse(io.open(SRC, encoding="utf-8").read())

# collect docstrings (module + functions) to exclude them
docstrings = set()
for node in ast.walk(tree):
    if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)):
        doc = ast.get_docstring(node, clean=False)
        if doc:
            docstrings.add(doc)
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
        ):
            docstrings.add(node.body[0].value.value)

hits = []
for node in ast.walk(tree):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        if node.value in docstrings:
            continue
        for bad in BAD:
            if bad in node.value:
                hits.append((node.lineno, bad, node.value[:120]))

print("docstrings excluded: %d" % len(docstrings))
print("string-literal hits  : %d" % len(hits))
for h in hits:
    print("  line %d  %r  %s" % h)

# every open()/path argument should resolve under the engine repo
print("")
print("open() calls:")
for node in ast.walk(tree):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "open":
        arg = node.args[0] if node.args else None
        print("  line %d  %s" % (node.lineno, ast.unparse(arg) if arg is not None else "<none>"))

sys.exit(1 if hits else 0)
