import io, json
d = json.load(io.open('tools/tool_channels.json', encoding='utf-8'))
print('keys:', list(d.keys()))
ch = d.get('channels', d.get('tools', {}))
print('channels type:', type(ch), 'len:', len(ch) if hasattr(ch, '__len__') else '')
k = list(ch)[:2] if isinstance(ch, dict) else None
for kk in (k or []):
    print(' ', kk, '->', json.dumps(ch[kk], ensure_ascii=False)[:200])
c = json.load(io.open('coverage.json', encoding='utf-8'))
print('\ncoverage keys:', list(c.keys())[:15])
print(json.dumps(c, ensure_ascii=False)[:900])
