import sys, re
path = r'F:\moonbit-hof-rs\runs\smoke-t10\iter-1\traj\tester.attempt1.json'
needle = sys.argv[1]
width = int(sys.argv[2]) if len(sys.argv) > 2 else 1600
raw = open(path, encoding='utf-8', errors='replace').read()
start = 0
n = 0
while n < 4:
    pos = raw.find(needle, start)
    if pos < 0:
        break
    n += 1
    print(f"===== occurrence {n} at {pos} =====")
    print(raw[pos - 500:pos + width])
    print()
    start = pos + 1
