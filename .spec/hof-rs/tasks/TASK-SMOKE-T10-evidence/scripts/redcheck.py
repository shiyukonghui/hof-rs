import json, os, glob

root = r'F:\moonbit-hof-rs\runs\smoke-t10'
for dirpath, dirnames, filenames in os.walk(root):
    for fn in filenames:
        p = os.path.join(dirpath, fn)
        try:
            raw = open(p, encoding='utf-8').read()
        except Exception:
            continue
        n = raw.count('<redacted>')
        if n:
            print(f"REDACTED x{n}: {os.path.relpath(p, root)}")

print()
print("=== JSON validity of trajectories ===")
for p in sorted(glob.glob(os.path.join(root, 'iter-1', 'traj', '*.json'))):
    raw = open(p, encoding='utf-8', errors='replace').read()
    try:
        json.loads(raw, strict=False)
        print("  OK    ", os.path.basename(p), len(raw))
    except Exception as e:
        print("  BROKEN", os.path.basename(p), len(raw), "->", e)

print()
print("=== exact bytes at the tester break ===")
p = os.path.join(root, 'iter-1', 'traj', 'tester.attempt1.json')
raw = open(p, encoding='utf-8', errors='replace').read()
pos = raw.find('HOH_MODEL_API_KEY=<redacted>')
print("pos:", pos)
print("repr:", repr(raw[pos - 120:pos + 80]))
