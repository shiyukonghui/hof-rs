# TASK-097 helper: list the generator's override-table keys (values may be expressions).
import ast
import sys

path = sys.argv[1]
tree = ast.parse(open(path, encoding="utf-8").read())
for node in tree.body:
    if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") in (
        "DESCRIPTION_OVERRIDES",
        "SCHEMA_OVERRIDES",
    ):
        keys = []
        for k in node.value.keys:
            if isinstance(k, ast.Constant):
                keys.append(k.value)
            else:
                keys.append("<expr>")
        print("%s: %d entries" % (node.targets[0].id, len(keys)))
        for key in keys:
            print("   %s" % key)
