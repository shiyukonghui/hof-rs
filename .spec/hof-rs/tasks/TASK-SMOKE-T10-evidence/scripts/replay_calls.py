import json, sys, os

base = r'F:\moonbit-hof-rs\runs\smoke-t10\iter-1\candidate\.hoh\deterministic'
d = json.load(open(os.path.join(base, 'raw', 'input_replay.json'), encoding='utf-8', errors='replace'))
calls = d['calls']
print("n_calls:", len(calls), "ok:", d['ok'], "supports:", d.get('supports'))
for i, c in enumerate(calls):
    tool = c.get('tool')
    label = c.get('label')
    args = json.dumps(c.get('args'), ensure_ascii=False)
    ok = c.get('ok')
    print(f"[{i:02d}] tool={tool} label={label!r} ok={ok} args={args[:200]}")
