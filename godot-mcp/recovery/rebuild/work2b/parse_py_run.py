
import io, os, sys, json, ast
R = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery"
G = os.path.join(R, "rebuild", "godot")
rows = []
for root, dirs, files in os.walk(G):
    for fn in files:
        if not fn.endswith(".py"):
            continue
        p = os.path.join(root, fn)
        rel = os.path.relpath(p, G)
        try:
            src = io.open(p, "rb").read()
            ast.parse(src.decode("utf-8", "replace"), filename=rel)
            rows.append({"rel": rel, "errors": 0, "first": ""})
        except SyntaxError as e:
            rows.append({"rel": rel, "errors": 1, "first": "%s:%s" % (e.lineno, e.msg)})
        except Exception as e:
            rows.append({"rel": rel, "errors": 1, "first": "EXC:" + str(e)})
io.open(os.path.join(R, "rebuild", "work2b", "parse-py-2b.json"), "w", encoding="utf-8", newline="\n").write(
    json.dumps(rows, ensure_ascii=False, indent=1))
bad = [r for r in rows if r["errors"]]
print("py scanned=%d withErrors=%d" % (len(rows), len(bad)))
for r in bad:
    print(" ", r["rel"], r["first"])
