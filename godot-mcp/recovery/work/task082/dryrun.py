# -*- coding: utf-8 -*-
"""Dry-run: show the transformed region to find the syntax break."""
import ast, re

GEN = r'H:\rebuild\godot\modules\mcp_server\scripts\gen_renamed_contract.py'
RPT = r'H:\rebuild\godot\modules\mcp_server\docs\reports\REPORT-076-small-items.md'
CPP = r'H:\rebuild\godot\modules\mcp_server\tools\editor_tilemap_write.cpp'
OUT = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task082\dryrun.txt'
log = []
def w(s=''):
    log.append(str(s))

src = open(GEN, 'rb').read().decode('utf-8')
DUP_START = '    # TASK-024 E-10: the new optional `mcp_port` argument. A schema override\n'
DUP_END = '    # TASK-024a E-10: the new optional `mcp_port` argument.'
i = src.find(DUP_START); j = src.find(DUP_END)
w('DUP_START idx=%d (line %d)' % (i, src[:i].count('\n') + 1))
w('DUP_END   idx=%d (line %d)' % (j, src[:j].count('\n') + 1))
new = src[:i] + src[j:]
w('after removal: DESCRIPTION_OVERRIDES at line %d' % (new[:new.find('DESCRIPTION_OVERRIDES = {')].count('\n') + 1))

anchor = 'DESCRIPTION_OVERRIDES = {\n'
w('anchor count=%d' % new.count(anchor))
literals_block = '# ==== INSERTED LITERALS MARKER ====\nSCENE_TREE_ADDRESSABILITY_SENTENCE = (\n    %r\n)\n\n' % 'X'
new2 = new.replace(anchor, literals_block + anchor, 1)
w('after literal insert: marker at line %d, DESCRIPTION_OVERRIDES at line %d'
  % (new2[:new2.find('==== INSERTED LITERALS MARKER')].count('\n') + 1,
     new2[:new2.find('DESCRIPTION_OVERRIDES = {')].count('\n') + 1))

# find the real end of DESCRIPTION_OVERRIDES: bracket matching
start = new2.find('DESCRIPTION_OVERRIDES = {')
k = new2.find('{', start)
depth = 0
in_str = None
idx = k
while idx < len(new2):
    c = new2[idx]
    if in_str:
        if c == '\\':
            idx += 2
            continue
        if c == in_str:
            in_str = None
    elif c in '"\'':
        in_str = c
    elif c == '#':
        nl = new2.find('\n', idx)
        idx = nl if nl != -1 else len(new2)
        continue
    elif c in '{([':
        depth += 1
    elif c in '})]':
        depth -= 1
        if depth == 0:
            break
    idx += 1
end_line = new2[:idx].count('\n') + 1
w('DESCRIPTION_OVERRIDES closes at line %d' % end_line)
w('text right after close: %r' % new2[idx:idx + 90])

w('')
w('=== lines %d..%d of new2 ===' % (max(1, end_line - 3), end_line + 6))
for n in range(max(1, end_line - 3), min(len(new2.split('\n')), end_line + 6) + 1):
    w('%5d: %s' % (n, new2.split('\n')[n - 1][:150]))

open(OUT, 'w', encoding='utf-8').write('\n'.join(log))
print('written', OUT)
