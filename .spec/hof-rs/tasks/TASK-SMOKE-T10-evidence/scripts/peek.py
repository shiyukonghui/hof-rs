import json, sys, os

base = r'F:\moonbit-hof-rs\runs\smoke-t10\iter-1\candidate\.hoh\deterministic'

def load(p):
    return json.load(open(os.path.join(base, p), encoding='utf-8', errors='replace'))

def shape(o, depth=0, maxd=3):
    pad = '  ' * depth
    if isinstance(o, dict):
        for k, v in o.items():
            if isinstance(v, (dict, list)) and depth < maxd:
                print(f"{pad}{k}: {type(v).__name__}(len={len(v)})")
                shape(v, depth + 1, maxd)
            else:
                s = json.dumps(v, ensure_ascii=False)
                print(f"{pad}{k}: {s[:220]}")
    elif isinstance(o, list):
        print(f"{pad}[list len={len(o)}]")
        if o and depth < maxd:
            shape(o[0], depth + 1, maxd)

which = sys.argv[1]
d = load(which)
print("==== ", which, " ====")
shape(d)
