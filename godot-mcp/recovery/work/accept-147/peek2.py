import io, json
c = json.load(io.open('coverage.json', encoding='utf-8'))
print('top keys:', list(c.keys()))
for k in c:
    v = c[k]
    if isinstance(v, list):
        print(k, 'is list len', len(v))
        print('  sample:', json.dumps(v[0], ensure_ascii=False)[:600])
    elif isinstance(v, dict):
        print(k, 'is dict len', len(v))
