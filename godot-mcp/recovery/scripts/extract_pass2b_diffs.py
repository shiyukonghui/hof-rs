# TASK-078 pass 2b: extract diff-class payloads (git diff/show/status output) into staging\__diffs\
# WRITES ONLY UNDER C:\Users\wyl\AppData\Local\Temp\mcp-recovery\
import json, os, re, collections

ROOT = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery'
W = os.path.join(ROOT, 'work')
ST = os.path.join(ROOT, 'staging')
REPO = 'F:\\RustProjects\\godot-mcp-pro\\code\\godot\\'

def norm(p):
    return (p or '').replace('/', '\\')

def safe_rel(rel):
    parts = []
    for c in norm(rel).split('\\'):
        if c in ('', '.'):
            continue
        if c == '..':
            c = '__up__'
        parts.append(re.sub(r'[*?"<>|]', '_', c))
    return '\\'.join(parts)

def stage_rel(path):
    n = norm(path)
    if n.lower().startswith(REPO.lower()):
        return safe_rel(n[len(REPO):])
    return safe_rel('__external\\' + n.replace(':', ''))

RE_GITDIFF = re.compile(r'^diff --git a/(\S+) b/(\S+)\s*$', re.M)
RE_PLUS = re.compile(r'^\+\+\+ b/(\S+)', re.M)

D = os.path.join(ST, '__diffs')
os.makedirs(D, exist_ok=True)
idx = []
n = 0
n_empty = 0
n_unparsed = 0
targets = collections.Counter()
KEYWORK = ('save_custom_section', 'save_preserving_text', 'is_source_newer_than_assembly',
           'editor_set_node_property_updates', 'update_settings_section_text',
           'publish_settings_sections_text')
kw = collections.Counter()
kw_files = collections.defaultdict(list)

with open(os.path.join(W, 'events-diff.jsonl'), 'r', encoding='utf-8') as f:
    for line in f:
        try:
            e = json.loads(line)
        except Exception:
            continue
        out = e.get('out') or ''
        ts = [b for a, b in RE_GITDIFF.findall(out)]
        if not ts:
            ts = RE_PLUS.findall(out)
        ts = [t.strip('"') for t in ts][:4]
        n += 1
        if not out.strip():
            n_empty += 1
        for k in KEYWORK:
            if k in out:
                kw[k] += 1
        sub = '\\'.join(stage_rel(t) for t in ts) if ts else '_unparsed'
        if not ts:
            n_unparsed += 1
        for t in ts:
            targets[t] += 1
        base = '%04d_t%s_seq%s' % (n, e.get('time'), e.get('seq'))
        d = os.path.join(D, sub if ts else '_unparsed')
        os.makedirs(d, exist_ok=True)
        fp = os.path.join(d, base + '.diff')
        with open(fp, 'w', encoding='utf-8', newline='') as g:
            g.write(out)
        with open(os.path.join(d, base + '.cmd.txt'), 'w', encoding='utf-8', newline='\n') as g:
            g.write('source=%s seq=%s time=%s\nworkdir=%s\nterminal=%s\ncommand:\n%s\n' %
                    (e.get('f'), e.get('seq'), e.get('time'), e.get('workdir'), e.get('term'), e.get('cmd')))
        idx.append((os.path.relpath(fp, ST), ','.join(ts) or '(none)', e.get('time'), e.get('seq'), e.get('f'), len(out)))
        for k in KEYWORK:
            if k in out:
                kw_files[k].append(os.path.relpath(fp, ST))

with open(os.path.join(D, 'INDEX.md'), 'w', encoding='utf-8', newline='\n') as g:
    g.write('# diff-class payload index (TASK-078, pass 2b)\n\n')
    g.write('total diff/git-capture events = %d (empty output = %d, unparsed target = %d)\n\n' % (n, n_empty, n_unparsed))
    g.write('| file | targets | time | seq | transcript | bytes |\n|---|---|---|---|---|---|\n')
    for r in idx:
        g.write('| %s | %s | %s | %s | %s | %d |\n' % r)

print('diff events=%d empty=%d unparsed=%d' % (n, n_empty, n_unparsed))
print('keyword hits:', dict(kw))
for k, v in kw_files.items():
    print(' ', k, len(v))
print('distinct targets:', len(targets))
for t, c in targets.most_common(25):
    print('%5d %s' % (c, t))
