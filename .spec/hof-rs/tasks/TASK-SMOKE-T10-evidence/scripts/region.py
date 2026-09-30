import sys
path = sys.argv[1]
pos = int(sys.argv[2])
raw = open(path, encoding='utf-8', errors='replace').read()
print("len:", len(raw))
print("--- region ---")
print(raw[pos-500:pos+700])
print("--- repr of 200 around pos ---")
print(repr(raw[pos-100:pos+200]))
