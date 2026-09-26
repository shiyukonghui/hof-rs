import ast, json, os, sys

root = sys.argv[1]
out = sys.argv[2]
total = 0
ok = 0
fails = []
for dirpath, dirnames, filenames in os.walk(root):
    for fn in filenames:
        if fn.lower().endswith(".py"):
            p = os.path.join(dirpath, fn)
            total += 1
            try:
                with open(p, "rb") as fh:
                    src = fh.read()
                ast.parse(src, filename=p)
                ok += 1
            except SyntaxError as e:
                fails.append({"path": os.path.relpath(p, root), "line": e.lineno, "msg": str(e.msg)})
            except Exception as e:
                fails.append({"path": os.path.relpath(p, root), "line": None, "msg": type(e).__name__ + ": " + str(e)})
res = {"root": root, "total": total, "ok": ok, "failed": len(fails), "fails": fails}
with open(out, "w", encoding="utf-8", newline="\n") as fh:
    json.dump(res, fh, indent=2, ensure_ascii=False)
print(json.dumps({"total": total, "ok": ok, "failed": len(fails)}))
for f in fails:
    print("FAIL " + f["path"] + " @" + str(f["line"]) + " " + f["msg"])
