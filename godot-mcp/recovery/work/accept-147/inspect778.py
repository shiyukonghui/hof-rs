import io
lines = io.open('recovery/TEST-CASES.md', encoding='utf-8').read().splitlines()
for n in (778, 779):
    print('line', n)
    print(repr(lines[n-1][:150]))
    cells = [c.strip() for c in lines[n-1].split('|')]
    print('  cells[1]=%r' % cells[1])
    print('  cells[3]=%r' % cells[3])
