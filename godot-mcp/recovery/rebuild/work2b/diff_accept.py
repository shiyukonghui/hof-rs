import io, os, difflib

R = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery"
tree = io.open(os.path.join(R, "rebuild", "godot", "modules", "mcp_server", "scripts", "accept_m1.ps1"),
               "rb").read().decode("utf-8", "replace").replace("\r\n", "\n").split("\n")
merged_txt = os.path.join(R, "rebuild", "work2b", "accept-final.txt")
merged = []
for ln in io.open(merged_txt, encoding="utf-8"):
    parts = ln.rstrip("\n").split("\t", 2)
    if len(parts) == 3:
        merged.append(parts[2])
print("tree lines:", len(tree), "merged lines:", len(merged))
sm = difflib.SequenceMatcher(None, tree, merged, autojunk=False)
ops = sm.get_opcodes()
del_rows = []
ins_rows = []
for tag, i1, i2, j1, j2 in ops:
    if tag in ("delete", "replace"):
        del_rows.append((i1 + 1, i2, j1 + 1, j2, tree[i1:i2], merged[j1:j2]))
n_del = sum(t[1] - (t[0] - 1) + (t[3] - t[2]) for t in del_rows)
print("tree-only lines:", sum(t[1] - (t[0] - 1) for t in del_rows), "merged-only:", sum(t[3] - t[2] for t in del_rows))
print("diff chunks:", len(del_rows))
with io.open(os.path.join(R, "rebuild", "work2b", "accept-diff.txt"), "w", encoding="utf-8", newline="\n") as f:
    for i1, i2, j1, j2, tl, ml in del_rows:
        f.write("### tree[%d:%d] vs merged[%d:%d]\n" % (i1, i2, j1, j2))
        for t in tl[:40]:
            f.write("- %s\n" % t[:160])
        for m in ml[:40]:
            f.write("+ %s\n" % m[:160])
print("wrote accept-diff.txt")
