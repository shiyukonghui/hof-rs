import io, re, collections, sys
sys.stdout.reconfigure(encoding='utf-8')
t = io.open('recovery/TEST-CASES.md', encoding='utf-8').read()
lines = t.splitlines()
for pat in ['27 passed', '23 passed']:
    print('=== %s ===' % pat)
    for i, line in enumerate(lines, 1):
        if pat in line:
            print('  line %d: %s' % (i, line.strip()[:200]))
    print()
print('=== lines with "30 passed" that are NOT TC-PY rows ===')
for i, line in enumerate(lines, 1):
    if '30 passed' in line and not line.startswith('| TC-PY-'):
        print('  line %d: %s' % (i, line.strip()[:200]))
print()
print('count of TC-PY rows containing "30 passed":',
      sum(1 for l in lines if l.startswith('| TC-PY-') and '30 passed' in l))
print()
for pat in ['785', '781', '404', '407', '788', '177/177']:
    print('=== %s ===' % pat)
    for i, line in enumerate(lines, 1):
        if pat in line:
            print('  line %d: %s' % (i, line.strip()[:160]))
    print()
