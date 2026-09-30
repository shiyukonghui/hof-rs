import hashlib, os, sys

EXCLUDE = {'.hoh', '.godot', '.import', '.git'}

def collect(root):
    m = {}
    root = os.path.abspath(root)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE]
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root).replace('\\', '/')
            data = open(full, 'rb').read()
            m[rel] = (len(data), hashlib.sha256(data).hexdigest())
    return m

a = collect(sys.argv[1])
b = collect(sys.argv[2])
print(f"A={sys.argv[1]}  files={len(a)}")
print(f"B={sys.argv[2]}  files={len(b)}")
added = sorted(set(b) - set(a))
removed = sorted(set(a) - set(b))
modified = sorted(k for k in set(a) & set(b) if a[k] != b[k])
print("ADDED:", added)
print("REMOVED:", removed)
print("MODIFIED:")
for k in modified:
    print(f"  {k}: {a[k][0]} B {a[k][1][:12]} -> {b[k][0]} B {b[k][1][:12]}")
print(f"counts added={len(added)} removed={len(removed)} modified={len(modified)}")
