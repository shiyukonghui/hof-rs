import json
d = json.load(open(r'F:\moonbit-hof-rs\runs\smoke-t10\iter-1\evidence.json', encoding='utf-8'))
print("qa_status:", d['qa_status'])
print("=== VERIFIED ===")
for r in d['verified_records']:
    print(f"[{r['claim_id']}] {r['claim']}")
    for er in r.get('execution_records', []):
        print(f"     - {er.get('type')} {er.get('path')} :: {er.get('observation','')[:220]}")
print("=== GAP ===")
for r in d['gap_records']:
    print(f"[{r['claim_id']}] {r['claim']}")
    print(f"     impact: {r.get('player_impact','')[:200]}")
    for er in r.get('execution_records', []):
        print(f"     - {er.get('type')} {er.get('path')} :: {er.get('observation','')[:200]}")
print("=== HANDOFF ===")
for k, v in d['planner_handoff'].items():
    print(f"{k}:")
    for x in v:
        print("   -", json.dumps(x, ensure_ascii=False)[:240])
