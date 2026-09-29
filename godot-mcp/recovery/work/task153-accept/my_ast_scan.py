"""Independent acceptance AST scan for TASK-153.

Authored by the acceptance subagent (NOT copied from the implementer).
Purpose: prove that no *executable* string literal in the generator names the
hof-rs repository, and resolve the three default paths by actually loading the
module (not by reading the source text).
"""
import ast
import importlib.util
import io
import os
import sys

GEN = r"F:\moonbit-hof-rs\godot-mcp\godot\modules\mcp_server\scripts\gen_renamed_contract.py"
NEEDLES = ("hof-rs", "moonbit-hof-rs")

with io.open(GEN, "r", encoding="utf-8") as fh:
    src = fh.read()
tree = ast.parse(src, filename=GEN)

# 1. collect every docstring node so they can be excluded
docstrings = set()
for node in ast.walk(tree):
    if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
        body = getattr(node, "body", None)
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                and isinstance(body[0].value.value, str):
            docstrings.add(id(body[0].value))

# 2. every executable string constant that names hof-rs
hits = []
for node in ast.walk(tree):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        if id(node) in docstrings:
            continue
        low = node.value.lower()
        if any(n in low for n in NEEDLES):
            hits.append((node.lineno, node.value))

# 3. also catch implicit concatenation inside JoinedStr / f-strings
joined = []
for node in ast.walk(tree):
    if isinstance(node, ast.JoinedStr):
        for part in node.values:
            if isinstance(part, ast.Constant) and isinstance(part.value, str):
                if any(n in part.value.lower() for n in NEEDLES):
                    joined.append((node.lineno, part.value))

# 4. every open() call and its first argument
opens = []
for node in ast.walk(tree):
    if isinstance(node, ast.Call):
        fn = node.func
        name = getattr(fn, "id", None) or getattr(fn, "attr", None)
        if name == "open" and node.args:
            a = node.args[0]
            opens.append((node.lineno, ast.dump(a)[:120]))

# 5. top-level assignments of the three defaults + their source expression
defaults_src = {}
for node in tree.body:
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Name) and t.id in ("DOCS", "MODULE_ROOT", "HERE",
                                                    "DEFAULT_OLD_CONTRACT", "DEFAULT_MAP",
                                                    "DEFAULT_OUT", "OLD_CONTRACT_SHA256"):
                defaults_src[t.id] = (node.lineno, ast.unparse(node.value)
                                      if hasattr(ast, "unparse") else ast.dump(node.value))

# 6. actually load the module and read the resolved defaults
spec = importlib.util.spec_from_file_location("gen_probe", GEN)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

print("script                     : %s" % GEN)
print("docstrings excluded        : %d" % len(docstrings))
print("executable hof-rs literals : %d" % len(hits))
for ln, val in hits:
    print("   HIT line %d: %r" % (ln, val))
print("f-string hof-rs fragments  : %d" % len(joined))
for ln, val in joined:
    print("   HIT line %d: %r" % (ln, val))
print("open() calls and first arg :")
for ln, dump in opens:
    print("   line %-5d %s" % (ln, dump))
print("defaults (source expression):")
for k in ("HERE", "MODULE_ROOT", "DOCS", "DEFAULT_OLD_CONTRACT", "DEFAULT_MAP",
          "DEFAULT_OUT", "OLD_CONTRACT_SHA256"):
    if k in defaults_src:
        print("   %-22s line %-5d %s" % (k, defaults_src[k][0], defaults_src[k][1]))
print("defaults (resolved at import time):")
print("   DEFAULT_OLD_CONTRACT = %s" % mod.DEFAULT_OLD_CONTRACT)
print("   DEFAULT_MAP          = %s" % mod.DEFAULT_MAP)
print("   DEFAULT_OUT          = %s" % mod.DEFAULT_OUT)
print("   OLD_CONTRACT_SHA256  = %s" % mod.OLD_CONTRACT_SHA256)

engine_docs = os.path.normcase(os.path.join(
    r"F:\moonbit-hof-rs\godot-mcp\godot\modules\mcp_server", "docs"))
ok_inside = os.path.normcase(os.path.dirname(mod.DEFAULT_OLD_CONTRACT)) == engine_docs
print("DEFAULT_OLD_CONTRACT lives in the ENGINE module docs dir : %s" % ok_inside)
print("SCAN_EXIT=%d" % (0 if (not hits and not joined and ok_inside) else 3))
sys.exit(0 if (not hits and not joined and ok_inside) else 3)
