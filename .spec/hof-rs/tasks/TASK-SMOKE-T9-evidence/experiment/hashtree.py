import sys, os, hashlib

root = sys.argv[1]
excl = {'.godot', '.import', '.hoh', '.git'}
rows = []
for dirpath, dirnames, filenames in os.walk(root):
    dirnames[:] = [d for d in dirnames if d not in excl]
    for fn in filenames:
        full = os.path.join(dirpath, fn)
        rel = os.path.relpath(full, root).replace('\\', '/')
        data = open(full, 'rb').read()
        rows.append((rel, len(data), hashlib.sha256(data).hexdigest()))

def digest(rows, prefix_rel=''):
    lines = []
    for rel, sz, h in rows:
        lines.append('%s\t%d\t%s' % ((prefix_rel + rel).lower(), sz, h))
    lines.sort()
    t = '\n'.join(lines)
    return hashlib.sha256(t.encode('utf-8')).hexdigest()

print('root=', os.path.abspath(root))
print('files=', len(rows))
print('total_bytes=', sum(r[1] for r in rows))
print('digest_ordinal=', digest(rows))
# culture-ish: python default sort is ordinal for ascii; try casefold variant
print('digest_nosize=', hashlib.sha256('\n'.join(sorted((rel.lower() + '\t' + h) for rel, sz, h in rows)).encode()).hexdigest())
print('digest_pathonly=', hashlib.sha256('\n'.join(sorted(rel.lower() for rel, sz, h in rows)).encode()).hexdigest())
for rel, sz, h in sorted(rows):
    print('   %8d  %s  %s' % (sz, h[:12], rel))
