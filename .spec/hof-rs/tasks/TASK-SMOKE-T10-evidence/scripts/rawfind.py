import sys
path, needle = sys.argv[1], sys.argv[2]
raw = open(path, encoding='utf-8', errors='replace').read()
print("file chars:", len(raw))
start = 0
n = 0
while True:
    pos = raw.find(needle, start)
    if pos < 0:
        break
    n += 1
    print(f"--- occurrence {n} at char {pos} ---")
    print(raw[max(0, pos - 900):pos + 1200].replace('\\n', '\n')[:2200])
    print()
    start = pos + 1
    if n > 8:
        break
print("total occurrences:", n)
