# TASK-078 pass 2b (v2): extract diff-class payloads (git diff/show/status output) into staging\__diffs\
# v2 resolves each diff target against the repo root named in the command (git -C / cd / workdir),
# so godot-tree and other-repo diffs cannot be confused.
# WRITES ONLY UNDER C:\Users\wyl\AppData\Local\Temp\mcp-recovery\
import json, os, re, collections

ROOT = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery'
W = os.path.join(ROOT, 'work')
ST = os.path.join(ROOT, 'staging')
GODOT = 'f:\\rustprojects\\godot-mcp-pro\\code\\godot'
HOF = 'f:\\moonbit-hof-rs'

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

RE_GITDIFF = re.compile(r'^diff --git a/(\S+) b/(\S+)\s*$', re.M)
RE_PLUS = re.compile(r'^\+\+\+ b/(\S+)', re.M)
RE_GITC = re.compile(r'git\s+-C\s+"?([A-Za-z]:[\\/][^\s";|)]*|[^\s";|)]*)"?', re.I)
RE_CD = re.compile(r'\bcd\s+(?:/d\s+)?(?:"([^"]+)"|([^\s&;|]+))', re.I)

def repo_root(e):
    cmd = e.get('cmd') or ''
    for m in RE_GITC.finditer(cmd):
        return norm(m.group(1)).rstrip('\\')
    m = RE_CD.search(cmd)
    if m:
        return norm(m.group(1) or m.group(2)).rstrip('\\')
    wd = e.get('workdir')
    if wd:
        return norm(wd).rstrip('\\')
    return ''

def tag_for(root):
    rl = root.lower()
    if rl.startswith(GODOT):
        return 'godot'
    if rl.startswith(HOF):
        return 'moonbit-hof-rs'
    if ':\\' in root or root.startswith('\\\\'):
        return safe_rel('__root__\\' + root.replace(':', ''))
    return 'unknown-root'

RE_GITDIFF2 = RE_GITDIFF
D = os.path.join(ST, '__diffs')
os.makedirs(D, exist_ok=True)
idx = []
n = 0
n_empty = 0
n_unparsed = 0
tagc = collections.Counter()
keywork = ('save_custom_section', 'save_preserving_text', 'is_source_newer_than_assembly',
           'editor_set_node_property_updates', 'update_settings_section_text',
           'publish_settings_sections_text')
kw = collections.Counter()

for line in open(os.path.join(W, 'events-diff.jsonl'), 'r', encoding='utf-8'):
    try:
        e = json.loads(line)
    except Exception:
        continue
    out = e.get('out') or ''
    n += 1
    if not out.strip():
        n_empty += 1
    root = repo_root(e)
    tag = tag_for(root)
    tagc[tag] += 1
    ts = [b for a, b in RE_GITDIFF2.findall(out)]
    if not ts:
        ts = RE_PLUS.findall(out)
    ts = [t.strip('"') for t in ts][:4]
    if not ts:
        n_unparsed += 1
    for k in keywork:
        if k in out:
            kw[k] += 1
    subs = [safe_rel(('__root__\\' + tag + '\\' + t) if tag in ('godot', 'moonbit-hof-rs') else t) for t in ts]
    sub = '\\'.join(subs) if subs else ('_unparsed\\' + safe_rel(tag))
    base = '%04d_t%s_seq%s' % (n, e.get('time'), e.get('seq'))
    d = os.path.join(D, sub)
    os.makedirs(d, exist_ok=True)
    fp = os.path.join(d, base + '.diff')
    with open(fp, 'w', encoding='utf-8', newline='') as g:
        g.write(out)
    with open(os.path.join(d, base + '.cmd.txt'), 'w', encoding='utf-8', newline='\n') as g:
        g.write('source=%s seq=%s time=%s\nrepo_root=%s\nworkdir=%s\nterminal=%s\ncommand:\n%s\n' %
                (e.get('f'), e.get('seq'), e.get('time'), root, e.get('workdir'), e.get('term'), e.get('cmd')))
    idx.append((os.path.relpath(fp, ST), tag, ','.join(ts) or '(none)', e.get('time'), e.get('seq'), e.get('f'), len(out)))

with open(os.path.join(D, 'INDEX.md'), 'w', encoding='utf-8', newline='\n') as g:
    g.write('# diff-class payload index (TASK-078 pass 2b v2)\n\n')
    g.write('captured git/diff events = %d (empty output = %d, no parsable target = %d)\n\n' % (n, n_empty, n_unparsed))
    g.write('repo tags: %s\n\n' % json.dumps(dict(tagc), ensure_ascii=False))
    g.write('| file | repo | targets | time | seq | transcript | bytes |\n|---|---|---|---|---|---|---|\n')
    for r in idx:
        g.write('| %s | %s | %s | %s | %s | %s | %d |\n' % r)

print('diff events=%d empty=%d unparsed=%d' % (n, n_empty, n_unparsed))
print('tags:', dict(tagc))
print('keyword hits:', dict(kw))
