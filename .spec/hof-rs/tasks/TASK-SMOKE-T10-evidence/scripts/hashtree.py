import hashlib, os, sys, json

# Project-tree digest scheme (my own, declared):
#   recursive over the given root, excluding any path segment in EXCLUDE
#   rel path (repo-root relative if under repo, else root-relative), POSIX separators, lowercased
#   + byte length + sha256 hex; rows joined by "\n"; ordinal sort of rows; sha256 of utf-8 bytes.
EXCLUDE = {'.hoh', '.godot', '.import', '.git'}

def tree(root, repo):
    rows = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted([d for d in dirnames if d not in EXCLUDE])
        for fn in sorted(filenames):
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, repo).replace('\\', '/').lower()
            data = open(full, 'rb').read()
            rows.append(f"{rel}\t{len(data)}\t{hashlib.sha256(data).hexdigest()}")
    rows.sort()
    blob = "\n".join(rows).encode('utf-8')
    return len(rows), sum(int(r.split('\t')[1]) for r in rows), hashlib.sha256(blob).hexdigest()

if __name__ == '__main__':
    repo = r'F:\moonbit-hof-rs'
    for t in sys.argv[1:]:
        n, b, d = tree(t, repo)
        print(f"{t}\t{n} files\t{b} bytes\t{d}")
