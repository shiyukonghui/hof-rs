import json, sys
p = sys.argv[1]
d = json.load(open(p, encoding='utf-8', errors='replace'))
print("INFO:", json.dumps(d.get('info'), ensure_ascii=False)[:2000])
msgs = d['messages']
print("n:", len(msgs))
for i, m in enumerate(msgs[-10:], start=len(msgs)-10):
    role = m.get('role')
    c = m.get('content')
    if not isinstance(c, str):
        c = json.dumps(c, ensure_ascii=False)
    tcs = m.get('tool_calls') or []
    names = [ (t.get('function') or {}).get('name') for t in tcs ]
    print(f"--- msg[{i}] role={role} len={len(c)} tool_calls={names}")
    print(c[:1500])
