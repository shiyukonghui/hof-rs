import io, json
d = json.load(io.open('godot/modules/mcp_server/docs/tools_list.renamed.json', encoding='utf-8'))
print(type(d))
if isinstance(d, dict):
    print('keys:', list(d.keys())[:10])
    for k in list(d)[:3]:
        print(k, type(d[k]))
        print(json.dumps(d[k], ensure_ascii=False)[:400])
elif isinstance(d, list):
    print('len', len(d), type(d[0]))
    print(json.dumps(d[0], ensure_ascii=False)[:400])
