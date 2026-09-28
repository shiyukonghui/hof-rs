import io, json
d = json.load(io.open('recovery/work/task143/analysis.json', encoding='utf-8'))
print(json.dumps(d['stats'], ensure_ascii=False, indent=1))
