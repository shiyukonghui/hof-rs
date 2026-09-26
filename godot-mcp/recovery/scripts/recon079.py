import io, json, os, re, sys

ROOT = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery'
IDX = os.path.join(ROOT, 'staging', '__payload-index')
TREE = os.path.join(os.environ['TEMP'], 'audit002', 'tree')
OUT = os.path.join(ROOT, 'work', 'recon.txt')

lines = []
def w(s=''):
    lines.append(s)

# ---- 1. distinct tools_list-ish tokens in the spool ----
pat = re.compile(r'tools_list[A-Za-z0-9_.\-]*\.json')
tok = {}
for fn in sorted(os.listdir(IDX)):
    if not fn.endswith('.jsonl'):
        continue
    p = os.path.join(IDX, fn)
    with io.open(p, encoding='utf-8', errors='replace') as f:
        for line in f:
            for m in pat.findall(line):
                tok.setdefault(m, set()).add(fn)
w('== distinct tools_list*.json tokens in payload index ==')
for k in sorted(tok):
    w('  %-45s %s' % (k, ','.join(sorted(tok[k]))))

pat2 = re.compile(r'tool-rename-map[A-Za-z0-9_.\-]*\.json')
tok2 = {}
for fn in sorted(os.listdir(IDX)):
    if not fn.endswith('.jsonl'):
        continue
    with io.open(os.path.join(IDX, fn), encoding='utf-8', errors='replace') as f:
        for line in f:
            for m in pat2.findall(line):
                tok2.setdefault(m, set()).add(fn)
w('== distinct tool-rename-map*.json tokens ==')
for k in sorted(tok2):
    w('  %-45s %s' % (k, ','.join(sorted(tok2[k]))))

# ---- 2. baseline tree engine-patch marker scan ----
MARK1 = ['is_source_newer_than_assembly', 'source_newer_than_assembly']
MARK2 = ['update_settings_section_text', 'save_custom_section', '_publish_section',
         'save_preserving_text']
MARK3 = ['save_preserving_text']
files = ['core/config/project_settings.cpp', 'core/config/project_settings.h',
         'editor/editor_node.cpp', 'modules/mono/csharp_script.cpp',
         'modules/mono/csharp_script.h']
w()
w('== baseline tree engine marker scan (blob text search) ==')
for rel in files:
    p = os.path.join(TREE, rel.replace('/', os.sep))
    if not os.path.exists(p):
        w('  %-45s MISSING' % rel)
        continue
    txt = io.open(p, encoding='utf-8', errors='replace').read()
    hits = {s: txt.count(s) for s in MARK1 + MARK2 if s in txt}
    w('  %-45s bytes=%-8d %s' % (rel, os.path.getsize(p), hits if hits else 'no patch markers'))

# ---- 3. hard gap files: presence anywhere ----
GAPS = [
    r'modules\mcp_server\tests\test_mcp_server.h',
    r'modules\mcp_server\docs\DESIGN-DETAIL.md',
    r'modules\mcp_server\tools\registration.cpp',
    r'modules\mcp_server\scripts\accept_m1.ps1',
    r'modules\mcp_server\scripts\gen_renamed_contract.py',
]
w()
w('== hard gap status ==')
for rel in GAPS:
    sp = os.path.join(ROOT, 'staging', rel)
    tp = os.path.join(TREE, rel)
    w('  %-52s staging=%s tree=%s' % (
        rel,
        (os.path.getsize(sp) if os.path.exists(sp) else 'MISSING'),
        (os.path.getsize(tp) if os.path.exists(tp) else 'MISSING')))

# ---- 4. reconstruction rows for the gaps ----
w()
w('== reconstruction rows for gaps (and tools assets) ==')
want = ['test_mcp_server.h', 'DESIGN-DETAIL.md', 'registration.cpp', 'accept_m1.ps1',
        'gen_renamed_contract.py', 'tool-rename-map.json', 'tools_list.renamed.json',
        'MCP-SERVER-HANDOVER.md', 'ACCEPTANCE.md', 'REQUIREMENTS.md']
with io.open(os.path.join(IDX, 'reconstruction.jsonl'), encoding='utf-8', errors='replace') as f:
    for line in f:
        d = json.loads(line)
        rel = d['rel']
        if any(x in rel for x in want):
            w('  %-70s conf=%-4s wrote=%-5s bytes=%-7s cov=%-6s tail=%-4s failed=%s n_edit=%s' % (
                rel, d['conf'], d['wrote'], d['bytes'], d['read_cov_pct'], d['miss_tail'],
                d['n_failed'], d['n_edit']))

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
print('\n'.join(lines))
