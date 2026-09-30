import re, sys

path = r'F:\moonbit-hof-rs\runs\smoke-t10\iter-1\traj\tester.attempt1.json'
raw = open(path, encoding='utf-8', errors='replace').read()

# correlate each running_game CLI invocation with the next <returncode>
pat = re.compile(r'tools call (running_game_[a-z_]+)')
rcs = {}
for m in re.finditer(r'<returncode>(\d+)</returncode>', raw):
    rcs[m.start()] = m.group(1)
print("returncode histogram:", {k: list(rcs.values()).count(k) for k in set(rcs.values())})

# first few CLI calls and the nearest following returncode
idxs = [m.start() for m in pat.finditer(raw)]
print("n CLI running_game invocations (raw text):", len(idxs))
shown = 0
for i in idxs[:6]:
    later = [k for k in rcs if k > i]
    rc = rcs[min(later)] if later else '?'
    seg = raw[i:i+260].replace('\n', ' ')
    print(f"--- rc={rc} :: {seg[:250]}")
    shown += 1

print()
print("=== a full successful call + result ===")
pos = raw.find('tools call running_game_get_node_properties')
print(repr(raw[pos-200:pos+1400]))
