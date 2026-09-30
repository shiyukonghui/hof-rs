import re

path = r'F:\moonbit-hof-rs\runs\smoke-t10\iter-1\traj\tester.attempt1.json'
raw = open(path, encoding='utf-8', errors='replace').read()

# every tool result carries a <returncode>NN</returncode>; pair each with the nearest PRECEDING command
rc_positions = [m.start() for m in re.finditer(r'<returncode>(-?\d+)</returncode>', raw)]
print("total tool results (returncode blocks):", len(rc_positions))

cmds = [(m.start(), m.group(1)) for m in re.finditer(r'tools call ([a-z_]+)', raw)]
print("total 'tools call <tool>' literal occurrences (both copies):", len(cmds))

run_game = 0
other = 0
none = 0
rcs = []
for p in rc_positions:
    prior = [c for c in cmds if c[0] < p]
    if not prior:
        none += 1
        continue
    tool = prior[-1][1]
    m = re.search(r'<returncode>(-?\d+)</returncode>', raw[p:p+40])
    rcs.append(m.group(1) if m else '?')
    if tool.startswith('running_game_'):
        run_game += 1
    else:
        other += 1
print("tool results whose nearest preceding 'tools call' is a running_game_* :", run_game)
print("tool results whose nearest preceding 'tools call' is another tool       :", other)
print("no preceding 'tools call'                                              :", none)
from collections import Counter
print("returncode histogram over all results:", dict(Counter(rcs)))
