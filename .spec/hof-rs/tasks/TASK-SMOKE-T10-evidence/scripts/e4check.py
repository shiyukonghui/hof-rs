import json, os

base = r'F:\moonbit-hof-rs\runs\smoke-t10\iter-1'
for p in [os.path.join(base, 'evidence.json'), os.path.join(base, 'candidate', '.hoh', 'evidence.json')]:
    d = json.load(open(p, encoding='utf-8'))
    print("=====", p)
    croot = os.path.join(base, 'candidate')
    miss = []
    for rec in d['verified_records']:
        for er in rec.get('execution_records', []):
            fp = er.get('path', '')
            full = os.path.join(croot, fp.replace('/', os.sep))
            ok = os.path.exists(full)
            if not ok:
                miss.append((rec['claim_id'], fp))
            print(f"  {rec['claim_id']:>4} {er.get('type'):>12} exists={ok} {fp}")
    print("  MISSING:", miss)
    print("  verified ids:", [r['claim_id'] for r in d['verified_records']])
    print("  gap ids:", [r['claim_id'] for r in d['gap_records']])
    ov = set(r['claim_id'] for r in d['verified_records']) & set(r['claim_id'] for r in d['gap_records'])
    print("  overlap:", ov)
    print("  handoff keys:", {k: (len(v) if isinstance(v, list) else v) for k, v in d['planner_handoff'].items()})
