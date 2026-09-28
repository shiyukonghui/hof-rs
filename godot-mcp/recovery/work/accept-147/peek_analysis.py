import io, json
d = json.load(io.open('recovery/work/task143/analysis.json', encoding='utf-8'))
print('top keys:', list(d.keys()))
t = d.get('totals') or d.get('summary')
print('totals:', json.dumps(t, ensure_ascii=False, indent=1) if t else None)
for k in d:
    if 'engine_cases' in str(k):
        print(k, '->', d[k] if not isinstance(d[k], (list, dict)) else type(d[k]))
