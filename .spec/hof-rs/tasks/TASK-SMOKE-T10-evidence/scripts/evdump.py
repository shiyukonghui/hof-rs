import json, sys

for p in sys.argv[1:]:
    d = json.load(open(p, encoding='utf-8'))
    print("=====", p)
    print("TOP KEYS:", list(d.keys()))
    for k, v in d.items():
        if isinstance(v, (list, dict)):
            print(f"  {k}: {type(v).__name__} len={len(v)}")
        else:
            print(f"  {k}: {json.dumps(v, ensure_ascii=False)[:400]}")
    # handle handoff / records
    for k in ('verified', 'verified_records', 'verified_claims', 'gap', 'gap_records', 'handoff'):
        v = d.get(k)
        if isinstance(v, list) and v:
            print(f"--- {k}[0] ---")
            print(json.dumps(v[0], ensure_ascii=False, indent=1)[:2500])
    if 'evidence' in d and isinstance(d['evidence'], dict):
        for k, v in d['evidence'].items():
            if isinstance(v, list) and v:
                print(f"--- evidence.{k}[0] ---")
                print(json.dumps(v[0], ensure_ascii=False, indent=1)[:2500])
