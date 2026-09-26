import io, json, sys
d = json.load(io.open(sys.argv[1], encoding='utf-8-sig'))
t = json.loads(d['result']['content'][0]['text'])
print("TOP KEYS:", list(t.keys()))
print(json.dumps(t, ensure_ascii=False, indent=1)[:1200])
