import json, os

base = r'F:\moonbit-hof-rs\runs\smoke-t10\iter-1\candidate\.hoh\deterministic'
d = json.load(open(os.path.join(base, 'raw', 'input_replay.json'), encoding='utf-8', errors='replace'))
calls = d['calls']

def unwrap(c):
    p = c.get('payload')
    if isinstance(p, dict) and 'content' in p:
        cts = p['content']
        out = []
        for ct in cts:
            t = ct.get('text') if isinstance(ct, dict) else None
            if t is None:
                out.append(ct)
            else:
                try:
                    out.append(json.loads(t))
                except Exception:
                    out.append(t)
        return out[0] if len(out) == 1 else out
    return p

def series(sample_payload, key='position'):
    # find samples list
    if isinstance(sample_payload, dict):
        cand = sample_payload.get('samples') or sample_payload.get('result') or sample_payload
    else:
        cand = sample_payload
    if isinstance(cand, dict) and 'samples' in cand:
        cand = cand['samples']
    return cand

for idx in [1, 7, 8, 9, 10, 13, 19, 21, 25, 31, 33, 37, 43, 45]:
    c = calls[idx]
    u = unwrap(c)
    print(f"===== call[{idx}] tool={c['tool']} label={c.get('label')!r} ok={c.get('ok')} =====")
    s = json.dumps(u, ensure_ascii=False)
    if len(s) > 3000:
        print(s[:3000] + f"... [truncated, total {len(s)} chars]")
    else:
        print(s)
    print()
