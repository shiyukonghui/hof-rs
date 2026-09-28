import io, re, collections, json

text = io.open('recovery/TEST-CASES.md', encoding='utf-8').read()
lines = text.splitlines()
printed = []
for ln, raw in enumerate(lines, 1):
    if not raw.startswith('| TC-PY-'):
        continue
    cells = [c.strip() for c in raw.split('|')]
    note = cells[-2]
    if u'\u81ea\u6253\u5370\u7684 case \u540d' in note and 'model_player' in cells[2]:
        printed.append(cells[3].strip('`'))

out = io.open('recovery/work/accept-147/mp.out.txt', encoding='utf-8').read().splitlines()
names = []
for line in out:
    tail = line[59:] if len(line) > 59 else ''
    if len(line) >= 58 and (tail.startswith('OK') or tail.startswith('MISMATCH')):
        names.append(line[:58].rstrip())

print('matrix printed rows (model_player):', len(printed))
print('really printed names             :', len(names))
print('duplicates in matrix rows        :', [k for k, v in collections.Counter(printed).items() if v > 1])
print('duplicates in printed names      :', [k for k, v in collections.Counter(names).items() if v > 1])
mset, nset = set(printed), set(names)
print('in matrix but not printed        :', sorted(mset - nset))
print('printed but NOT in matrix        :', sorted(nset - mset))
print('set-equal                        :', mset == nset)

# uniqueness: does the self-consistency checker catch a duplicate row?
print()
print('matrix row line numbers for printed rows:',
      [ln for ln, raw in enumerate(lines, 1)
       if raw.startswith('| TC-PY-test_playability_model_player.py:') and
       u'\u81ea\u6253\u5370' in raw][:5])
