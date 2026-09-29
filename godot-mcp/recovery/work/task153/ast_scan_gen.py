#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-153: prove no EXECUTABLE string in the generator points outside the
engine repository.

It walks the AST (so comments never appear), skips module/class/function
docstrings, and reports every `ast.Constant` string that names the hof-rs
repository, plus every `open()` argument. Exit 0 = no such string literal.
"""
import ast
import sys

PATH = r"F:\moonbit-hof-rs\godot-mcp\godot\modules\mcp_server\scripts\gen_renamed_contract.py"
src = open(PATH, encoding="utf-8").read()
tree = ast.parse(src)

doc_nodes = set()
for node in ast.walk(tree):
    if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        body = getattr(node, "body", [])
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                and isinstance(body[0].value.value, str):
            doc_nodes.add(id(body[0].value))

hits = []
for node in ast.walk(tree):
    if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in doc_nodes:
        if "hof-rs" in node.value or "moonbit-hof-rs" in node.value:
            hits.append((node.lineno, node.value[:70]))

opens = []
for node in ast.walk(tree):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "open":
        if node.args:
            opens.append((node.lineno, ast.unparse(node.args[0])[:70]))

print("script                     :", PATH)
print("docstrings excluded        :", len(doc_nodes))
print("executable string-literal hits naming hof-rs :", len(hits))
for h in hits:
    print("   line %d %s" % h)
print("open() calls               :")
for o in opens:
    print("   line %d  %s" % o)
print("SCAN_EXIT=1 (a hof-rs string literal remains)" if hits else "SCAN_EXIT=0 (no executable hof-rs path)")
sys.exit(1 if hits else 0)
