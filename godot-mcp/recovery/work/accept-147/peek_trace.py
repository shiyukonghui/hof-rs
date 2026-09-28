import io, json
p = 'runs/_exercises/ex_grid/c8-task120/trace-editor.jsonl'
lines = io.open(p, encoding='utf-8').read().splitlines()
print('lines:', len(lines))
print(json.dumps(json.loads(lines[1]), ensure_ascii=False, indent=1)[:1500])
