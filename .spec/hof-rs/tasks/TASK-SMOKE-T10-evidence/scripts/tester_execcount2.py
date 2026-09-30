import re
from collections import Counter

path = r'F:\moonbit-hof-rs\runs\smoke-t10\iter-1\traj\tester.attempt1.json'
raw = open(path, encoding='utf-8', errors='replace').read()

pat = re.compile(r'"actions":\s*\[\s*\{\s*"command":\s*"((?:[^"\\]|\\.)*)"')
cmds = pat.findall(raw)
print("executed bash commands (one per tool result, from extra.actions[0].command):", len(cmds))
rg = [c for c in cmds if 'tools call running_game_' in c]
print("of which invoke 'tools call running_game_*':", len(rg))
tools = Counter(re.findall(r'tools call (running_game_[a-z_]+)', ' ;; '.join(rg)))
print("distinct running_game tools used:", dict(tools))
print("of which mention 'tools call' for a NON game tool:", sum(1 for c in cmds if 'tools call ' in c and 'tools call running_game_' not in c))
print("commands containing 'game_endpoint_unavailable':", sum(1 for c in cmds if 'game_endpoint_unavailable' in c))
print()
print("--- the 3 shortest running_game invocations, verbatim (unescaped) ---")
for c in sorted(rg, key=len)[:3]:
    print("   $", c.replace('\\"', '"')[:300])
