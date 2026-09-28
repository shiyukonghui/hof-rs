import io, json, sys
d = json.load(io.open('recovery/work/task143/probe-live.json', encoding='utf-8'))
print(json.dumps(d['counters'], ensure_ascii=False, indent=1))
k = list(d['tools'])[0]
print('sample tool key:', k)
print(json.dumps(d['tools'][k], ensure_ascii=False, indent=1)[:2000])
