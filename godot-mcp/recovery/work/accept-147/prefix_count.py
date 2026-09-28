import io, subprocess, sys, collections
sys.stdout.reconfigure(encoding='utf-8')
old = subprocess.run(['git', 'show', '85dc5d5:godot-mcp/recovery/TEST-CASES.md'],
                     stdout=subprocess.PIPE).stdout.decode('utf-8')
lines = old.splitlines()
def cnt(pat, rows_only=False):
    n = 0
    for l in lines:
        if pat in l and (not rows_only or l.startswith('| TC-PY-')):
            n += 1
    return n
print('pre-fix (85dc5d5) file: %d lines' % len(lines))
print('  occurrences of "23 passed"                 :', cnt('23 passed'))
print('  occurrences of "23 passed" in TC-PY rows   :', cnt('23 passed', True))
print('  occurrences of "23 passed" outside rows    :', cnt('23 passed') - cnt('23 passed', True))
print('  occurrences of "27 passed"                 :', cnt('27 passed'))
print('  occurrences of "27 passed" in TC-PY rows   :', cnt('27 passed', True))
for i, l in enumerate(lines, 1):
    if '23 passed' in l and not l.startswith('| TC-PY-'):
        print('   non-row line %d: %s' % (i, l.strip()[:150]))
