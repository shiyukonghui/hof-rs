# -*- coding: utf-8 -*-
"""TASK-082 item 3: run the repaired generator twice (idempotence) and verify."""
import hashlib, io, json, os, subprocess, sys

GEN   = r'H:\rebuild\godot\modules\mcp_server\scripts\gen_renamed_contract.py'
OLD   = r'F:\moonbit-hof-rs\tests\fixtures\mcp\tools_list.json'          # READ ONLY
GENOUT = r'H:\rebuild\godot\modules\mcp_server\docs\tools_list.renamed.json'
MAP   = r'H:\rebuild\godot\modules\mcp_server\docs\tool-rename-map.json'
LOG   = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\logs\task082_contract.txt'
OUTJSON = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task082\contract-verify.txt'

log = []
def w(s=''):
    log.append(str(s))
    print(s)

def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()

TARGET = 'a5c59853c1e5a4913d600c663c8e972f058f7144869ec20337ab41b7a7bb17ea'

w('old contract (F:, READ ONLY): exists=%s sha256=%s' % (os.path.exists(OLD), sha(OLD)))
old_before = sha(OLD)
w('map: %s sha256=%s' % (MAP, sha(MAP)))
w('out before: exists=%s sha256=%s' % (os.path.exists(GENOUT), sha(GENOUT) if os.path.exists(GENOUT) else '-'))

runs = []
for n in (1, 2):
    cmd = [sys.executable, GEN, '--old-contract', OLD, '--map', MAP, '--out', GENOUT]
    w('')
    w('=== run %d ===' % n)
    w('$ ' + ' '.join(cmd))
    p = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    w('exit=%d' % p.returncode)
    if p.stdout:
        for ln in p.stdout.rstrip('\n').split('\n'):
            w('  out| %s' % ln)
    if p.stderr:
        for ln in p.stderr.rstrip('\n').split('\n'):
            w('  err| %s' % ln)
    b = open(GENOUT, 'rb').read()
    h = hashlib.sha256(b).hexdigest()
    runs.append((h, len(b)))
    w('  bytes=%d sha256=%s' % (len(b), h))

w('')
w('=== idempotence ===')
w('run1 = %s' % runs[0][0])
w('run2 = %s' % runs[1][0])
w('same sha: %s' % (runs[0][0] == runs[1][0]))
w('same bytes: %s' % (runs[0][1] == runs[1][1]))

j = json.loads(open(GENOUT, 'rb').read().decode('utf-8'))
m = j['_meta']
tools = j['result']['tools']
names = [t['name'] for t in tools]
ed = sorted(n for n in names if n.startswith('editor_'))
pr = sorted(n for n in names if n.startswith('project_'))
gm = sorted(n for n in names if n.startswith('running_game_'))
osn = sorted(n for n in names if n.startswith('os_') or n.startswith('game_') or n.startswith('mcp_'))
other = sorted(set(names) - set(ed) - set(pr) - set(gm) - set(osn))

w('')
w('=== verification ===')
w('_meta.count            = %s   (required 177) -> %s' % (m['count'], 'PASS' if m['count'] == 177 else 'FAIL'))
w('_meta.added_count      = %s   (required 6)   -> %s' % (m['added_count'], 'PASS' if m['added_count'] == 6 else 'FAIL'))
w('_meta.generator_version= %s (required 1.22.0)-> %s' % (m['generator_version'], 'PASS' if m['generator_version'] == '1.22.0' else 'FAIL'))
w('result.tools           = %d' % len(tools))
editor_endpoint = len(ed) + len(pr) + len(osn)
game_endpoint = len(gm) + len(pr) + len(osn)
w('editor endpoint        = %d (required 154) -> %s' % (editor_endpoint, 'PASS' if editor_endpoint == 154 else 'FAIL'))
w('game endpoint          = %d (required 73)  -> %s' % (game_endpoint, 'PASS' if game_endpoint == 73 else 'FAIL'))
w('  decomposition: editor_*=%d project_*=%d running_game_*=%d other=%d (%s)'
  % (len(ed), len(pr), len(gm), len(other), other))
w('_meta.overrides        = %d (TASK-076A recorded target 36)' % len(m.get('overrides', [])))
kinds = {}
for o in m.get('overrides', []):
    kinds.setdefault(o['kind'], []).append(o['old_name'])
for k, v in sorted(kinds.items()):
    w('    %s: %d -> %s' % (k, len(v), sorted(v)))
w('_meta.added_tools      = %s' % m['added_tools'])
w('_meta.map_sha256       = %s' % m['map_sha256'])
w('_meta.generated_from_sha256 = %s' % m['generated_from_sha256'])
w('_meta.order_normative  = %s' % m['order_normative'])
w('')
w('contract sha256        = %s' % runs[0][0])
w('recorded target        = %s' % TARGET)
w('MATCH                  = %s' % (runs[0][0] == TARGET))
w('byte delta vs target   = %d (target 163,520 B; actual %d B)' % (runs[0][1] - 163520, runs[0][1]))
w('')
w('old contract sha after  = %s (unchanged: %s)' % (sha(OLD), sha(OLD) == old_before))

# the three TASK-076A descriptions as emitted
w('')
w('=== the three TASK-076A descriptions as emitted ===')
EXPECT = {'editor_get_scene_tree': 898, 'editor_set_tilemap_cell': 717, 'editor_set_tilemap_cells_in_rect': 720}
byname = {t['name']: t for t in tools}
for n, exp in EXPECT.items():
    d = byname[n]['description']
    b = len(d.encode('utf-8'))
    w('  %s: bytes=%d (expected %d) -> %s' % (n, b, exp, 'MATCH' if b == exp else 'MISMATCH'))
    w('     prefix-ok=%s' % d.startswith({'editor_get_scene_tree': '获取当前编辑场景的完整场景树',
                                          'editor_set_tilemap_cell': '设置瓦片地图单元格',
                                          'editor_set_tilemap_cells_in_rect': '填充瓦片地图矩形区域'}[n] + ' '))

# inputSchema must be byte-identical to the pre-change output for the 3 + all others
w('')
w('=== inputSchema stability check vs the pre-repair contract ===')
PRE = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task082\pre-repair-tools_list.renamed.json'
if os.path.exists(PRE):
    pre = json.loads(open(PRE, 'rb').read().decode('utf-8'))
    pm = {t['name']: t for t in pre['result']['tools']}
    diffs = [n for n in names if json.dumps(pm[n]['inputSchema'], sort_keys=True) != json.dumps(byname[n]['inputSchema'], sort_keys=True)]
    w('  inputSchema differing entries: %s' % (diffs or 'NONE'))
    dd = [n for n in names if pm[n]['description'] != byname[n]['description']]
    w('  description differing entries: %s' % sorted(dd))
else:
    w('  (pre-repair copy missing)')

open(LOG, 'w', encoding='utf-8').write('\n'.join(log))
open(OUTJSON, 'w', encoding='utf-8').write('\n'.join(log))
print('log ->', LOG)
