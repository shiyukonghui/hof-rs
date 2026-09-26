import io, os, re, hashlib, subprocess, json

R = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery"
W = os.path.join(R, "rebuild", "work2b")
G = os.path.join(R, "rebuild", "godot")

tree_path = os.path.join(G, "modules", "mcp_server", "scripts", "accept_m1.ps1")
tree = io.open(tree_path, encoding="utf-8", errors="replace").read().replace("\r\n", "\n").split("\n")
if tree and tree[-1] == "":
    tree = tree[:-1]

merged = {}
for ln in io.open(os.path.join(W, "accept-final.txt"), encoding="utf-8"):
    parts = ln.rstrip("\n").split("\t", 2)
    if len(parts) == 3:
        num = int(parts[0])
        merged[num] = parts[2] if parts[2] != "<<<MISSING>>>" else None
maxn = max(merged)

# banded alignment: merged[1..maxn] vs tree[1..len(tree)]
N, M = maxn, len(tree)
BAND = 420
INF = 1 << 30
prev = {}
for j in range(0, min(M, BAND) + 1):
    prev[j] = (0, "s" * 0)
# store backpointers in a dict keyed by (i,j) only within band
bp = {}
score = {j: (0, None) for j in range(0, min(M, BAND) + 1)}
for i in range(1, N + 1):
    cur = {}
    lo = max(0, i - BAND)
    hi = min(M, i + BAND)
    for j in range(lo, hi + 1):
        best = None
        if j > 0:
            diag = score.get(j - 1)
            if diag is not None:
                same = merged.get(i) is not None and merged[i] == tree[j - 1]
                val = diag[0] + (0 if same else 1)
                best = (val, (i - 1, j - 1), "d" if same else "x")
        if j in score:
            up = score[j]
            val = up[0] + 1
            if best is None or val < best[0]:
                best = (val, (i - 1, j), "u")
        if j - 1 in cur:
            left = cur[j - 1]
            val = left[0] + 1
            if best is None or val < best[0]:
                best = (val, (i, j - 1), "l")
        if best is not None:
            cur[j] = (best[0], best[1], best[2])
    if not cur:
        raise SystemExit("alignment band collapsed at i=%d" % i)
    score = {j: (v[0], v[1], v[2]) for j, v in cur.items()}
print("aligned rows:", N, "tree lines:", M)

# map merged line -> tree line via diagonal moves
m2t = {}
path = []
jend = min(score.keys(), key=lambda j: score[j][0])
node = (N, jend)
while node[0] > 0 or node[1] > 0:
    st = cur if False else None
    break
# rebuild path by recomputing with stored chains is heavy; instead rerun keeping full dict
