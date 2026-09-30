import json, sys, re, collections

path = sys.argv[1]
d = json.load(open(path, encoding='utf-8', errors='replace'))
msgs = d['messages'] if isinstance(d, dict) and 'messages' in d else d
print("type:", type(d).__name__, "keys:", list(d.keys())[:12] if isinstance(d, dict) else None)
print("n_messages:", len(msgs))
roles = collections.Counter(m.get('role') for m in msgs)
print("roles:", dict(roles))

commands = []
tool_results = []
for m in msgs:
    if m.get('role') == 'assistant':
        for tc in (m.get('tool_calls') or []):
            fn = (tc.get('function') or {})
            name = fn.get('name')
            args = fn.get('arguments')
            commands.append((name, args))
    if m.get('role') == 'tool':
        c = m.get('content')
        if not isinstance(c, str):
            c = json.dumps(c, ensure_ascii=False)
        tool_results.append((m.get('name'), c))

print("n_tool_calls:", len(commands))
print("tool name counts:", dict(collections.Counter(n for n, _ in commands)))

bash_cmds = []
for name, args in commands:
    try:
        a = json.loads(args) if isinstance(args, str) else (args or {})
    except Exception:
        a = {}
    if isinstance(a, dict) and 'command' in a:
        bash_cmds.append(a['command'])
print("n_bash:", len(bash_cmds))

joined = "\n".join(bash_cmds)
for pat in ['running_game_', 'game_endpoint_unavailable', 'editor_play_scene', 'hoh tools call',
            'echo ', 'type ', 'dir ', 'python', 'curl', 'netstat', 'Invoke-RestMethod', 'raw http',
            'editor_get_errors', 'set ', 'create_file', 'write']:
    print(f"  {pat!r}: {joined.count(pat)}")

print("--- first 40 commands ---")
for i, c in enumerate(bash_cmds[:40]):
    print(f"[{i}] {c[:300]!r}")
print("--- last 30 commands ---")
for i, c in enumerate(bash_cmds[-30:]):
    print(f"[{len(bash_cmds)-30+i}] {c[:300]!r}")

print("--- strings in tool results ---")
allres = "\n".join(c for _, c in tool_results)
for pat in ['game_endpoint_unavailable', 'hoh_output_truncated', 'POSITION_ASSERTION_UNAVAILABLE',
            'editor_side_injection', 'was unexpected at this time', 'No tool calls found']:
    print(f"  {pat!r}: {allres.count(pat)}")
print("--- largest tool results ---")
sz = sorted(((len(c), n, i) for i, (n, c) in enumerate(tool_results)), reverse=True)[:8]
for s, n, i in sz:
    print(f"  msg#{i} name={n} bytes={s}")
