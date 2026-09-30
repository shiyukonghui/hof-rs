import json, sys, re

path = sys.argv[1]
needle = sys.argv[2]
d = json.load(open(path, encoding='utf-8', errors='replace'))
msgs = d['messages']
for i, m in enumerate(msgs):
    c = m.get('content')
    if not isinstance(c, str):
        c = json.dumps(c, ensure_ascii=False)
    if needle in c:
        role = m.get('role')
        tcs = m.get('tool_calls') or []
        cmds = []
        for t in tcs:
            a = (t.get('function') or {}).get('arguments')
            try:
                aa = json.loads(a) if isinstance(a, str) else a
            except Exception:
                aa = {}
            if isinstance(aa, dict) and 'command' in aa:
                cmds.append(aa['command'])
        pos = c.index(needle)
        print(f"### msg[{i}] role={role} len={len(c)} tool_calls={len(tcs)}")
        if cmds:
            print("   CMD:", cmds[0][:300])
        print("   CTX:", c[max(0, pos-600):pos+900].replace('\n', '\\n')[:1600])
        print()
