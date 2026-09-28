import io, json
c = json.load(io.open('coverage.json', encoding='utf-8'))
tools = c['tools']
print('n tools:', len(tools))
print('sample:', json.dumps(tools[0], ensure_ascii=False, indent=1)[:1200])
