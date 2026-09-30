import json, sys, collections

for path in sys.argv[1:]:
    raw0 = open(path, encoding='utf-8', errors='replace').read()
    d = json.loads(raw0, strict=False)
    msgs = d['messages']
    raw = open(path, encoding='utf-8', errors='replace').read()
    print("=====", path)
    print("  n_messages:", len(msgs), " roles:", dict(collections.Counter(m.get('role') for m in msgs)))
    for pat in ['-32602', 'JSON-RPC error', 'hoh_output_truncated', 'game_endpoint_unavailable',
                'No tool calls found', 'RepeatedFormatError', 'POSITION_ASSERT_PASSED',
                'rmdir', 'rd /s', '-p']:
        print(f"  {pat!r}: {raw.count(pat)}")
    tools = collections.Counter()
    cmds = []
    for m in msgs:
        if m.get('role') == 'assistant':
            for t in (m.get('tool_calls') or []):
                fn = t.get('function') or {}
                tools[fn.get('name')] += 1
                a = fn.get('arguments')
                try:
                    aa = json.loads(a) if isinstance(a, str) else a
                except Exception:
                    aa = {}
                if isinstance(aa, dict) and 'command' in aa:
                    cmds.append(aa['command'])
    print("  tool calls:", dict(tools))
    print("  n_bash:", len(cmds))
    j = "\n".join(cmds)
    for pat in ['running_game_', 'editor_', 'rmdir', 'del ', '%HOH_', 'python -c', 'bash -c', '-p']:
        print(f"    cmd {pat!r}: {j.count(pat)}")
    sizes = []
    for i, m in enumerate(msgs):
        c = m.get('content')
        if not isinstance(c, str):
            c = json.dumps(c, ensure_ascii=False)
        sizes.append((len(c), i, m.get('role')))
    sizes.sort(reverse=True)
    print("  largest messages:", sizes[:5])
    # commands that mention -p removal
    for c in cmds:
        if 'rmdir' in c or 'rd ' in c or 'del ' in c:
            print("   DELCMD:", c[:250])
