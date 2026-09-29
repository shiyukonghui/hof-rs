# Independent (acceptance-side, TASK-152) AST scan of the g05 script.
# Walks every module/docstring-excluded string constant and every call, reporting
# any literal that contains a path outside the engine repository, plus every
# open()/Path()/environ/subprocess touch on the execution path.
import ast, os, sys

TARGET = r"F:\moonbit-hof-rs\godot-mcp\godot\modules\mcp_server\docs\scripts\check_rename_map.py"
FORBIDDEN = ("moonbit-hof-rs", "hof-rs", "F:\\", "F:/", "C:\\", "..")

src = open(TARGET, "r", encoding="utf-8").read()
tree = ast.parse(src)

docstrings = set()
for node in ast.walk(tree):
    if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        ds = ast.get_docstring(node, clean=False)
        if ds is not None and node.body and isinstance(node.body[0], ast.Expr):
            docstrings.add(id(node.body[0].value))

hits = []
for node in ast.walk(tree):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        if id(node) in docstrings:
            continue
        for bad in FORBIDDEN:
            if bad in node.value:
                hits.append((node.lineno, bad, node.value[:90]))

calls = []
for node in ast.walk(tree):
    if isinstance(node, ast.Call):
        fn = node.func
        name = ""
        if isinstance(fn, ast.Name):
            name = fn.id
        elif isinstance(fn, ast.Attribute):
            name = (ast.unparse(fn.value) if hasattr(ast, "unparse") else "") + "." + fn.attr
        if any(k in name for k in ("open", "Path", "environ", "getenv", "subprocess", "system", "popen", "import_module")):
            arg = ast.unparse(node.args[0]) if (node.args and hasattr(ast, "unparse")) else "<call>"
            calls.append((node.lineno, name, arg))

print("docstrings excluded :", len(docstrings))
print("string-literal hits :", len(hits))
for h in hits:
    print("  HIT", h)
print("path-ish calls:")
for c in calls:
    print("  line %d  %s  arg=%s" % c)
print("SCAN_EXIT=%d" % (1 if hits else 0))
sys.exit(1 if hits else 0)
