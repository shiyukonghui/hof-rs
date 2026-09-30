import hashlib, os, sys

EXCLUDE = {'.hoh', '.godot', '.import', '.git'}

def tree(root):
    rows = []
    root = os.path.abspath(root)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted([d for d in dirnames if d not in EXCLUDE])
        for fn in sorted(filenames):
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root).replace('\\', '/').lower()
            data = open(full, 'rb').read()
            rows.append(f"{rel}\t{len(data)}\t{hashlib.sha256(data).hexdigest()}")
    rows.sort()
    blob = "\n".join(rows).encode('utf-8')
    return len(rows), sum(int(r.split('\t')[1]) for r in rows), hashlib.sha256(blob).hexdigest()

if __name__ == '__main__':
    prev = None
    for t in sys.argv[1:]:
        n, b, dg = tree(t)
        same = '' if prev is None else ('  SAME_AS_PREVIOUS' if dg == prev else '  DIFFERS_FROM_PREVIOUS')
        print(f"{n:>4} files {b:>8} B  {dg}  {t}{same}")
        prev = dg
