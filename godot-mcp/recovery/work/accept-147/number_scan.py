import io, re, collections
t = io.open('recovery/TEST-CASES.md', encoding='utf-8').read()
for k in ['23 passed', '30 passed', '27 passed', '177/177', '175', '407', '788', '785', '781', '404', '400']:
    n = t.count(k)
    print('%-12s total occurrences: %d' % (k, n))
print()
m = re.findall(r'`(\d+ passed)`', t)
print('backticked "<n> passed":', collections.Counter(m))
print('rows containing "30 passed":', t.count('30 passed'))
# per-line context of 30 passed that are NOT TC-PY rows
for i, line in enumerate(t.splitlines(), 1):
    if '30 passed' in line and not line.startswith('| TC-PY-'):
        print('  line %d: %s' % (i, line.strip()[:170]))
print()
for i, line in enumerate(t.splitlines(), 1):
    if '23 passed' in line:
        print('  23passed line %d: %s' % (i, line.strip()[:170]))
