import re
path = r'F:\moonbit-hof-rs\runs\smoke-t10\iter-1\traj\tester.attempt1.json'
raw = open(path, encoding='utf-8', errors='replace').read()

# actual executions: the model's bash argument string containing tools call running_game
execs = []
for m in re.finditer(r'\{\\"command\\": \\"(.{0,600}?)\\"\}', raw):
    cmd = m.group(1)
    if 'tools call running_game' in cmd or 'tools\\\", \\\"call' in cmd:
        execs.append((m.start(), cmd))
print("assistant bash calls whose command mentions running_game:", len(execs))
for i, (pos, c) in enumerate(execs[:12]):
    print(f"--- exec[{i}] ---")
    print("  CMD:", c[:260])
    # find the next <returncode> after this point
    m2 = re.search(r'<returncode>(-?\d+)</returncode>', raw[pos:pos+4000])
    print("  RC:", m2.group(1) if m2 else None)
    seg = raw[pos:pos+2200].replace('\\n', ' ')
    idx = seg.find('resolved_node_path')
    print("  has resolved_node_path:", idx >= 0)
