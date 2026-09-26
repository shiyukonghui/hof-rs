# TASK-078 inventory: path prefixes and payload coverage (read-only over work/).
import json, os, collections

W = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work'
REPO = 'f:\\rustprojects\\godot-mcp-pro\\code\\godot\\'

def load(kind):
    p = os.path.join(W, 'events-%s.jsonl' % kind)
    with open(p, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                yield json.loads(line)
            except Exception:
                pass

kinds = collections.defaultdict(set)
prefix = collections.Counter()
for k in ('write', 'edit', 'read'):
    for e in load(k):
        p = (e.get('path') or '').strip()
        if not p:
            kinds[k].add('<EMPTY>')
            continue
        kinds[k].add(p)
        low = p.replace('/', '\\').lower()
        if not low.startswith(REPO):
            prefix[low.split('\\')[0] + '\\' + (low.split('\\')[1] if len(low.split('\\')) > 1 else '')] += 1

allp = set()
for k in ('write', 'edit', 'read'):
    allp |= kinds[k]
print('distinct paths: write=%d edit=%d read=%d union=%d' % (len(kinds['write']), len(kinds['edit']), len(kinds['read']), len(allp)))
inrepo = [p for p in allp if p.replace('/', '\\').lower().startswith(REPO)]
print('in-repo distinct paths = %d ; out-of-repo = %d' % (len(inrepo), len(allp) - len(inrepo)))
print('--- out-of-repo prefixes (top 25) ---')
for k, v in prefix.most_common(25):
    print('%6d  %s' % (v, k))
print('--- in-repo top-level dirs ---')
c = collections.Counter()
for p in inrepo:
    rel = p.replace('/', '\\')[len(REPO):]
    parts = rel.split('\\')
    c['\\'.join(parts[:2]) if len(parts) > 1 else parts[0]] += 1
for k, v in c.most_common(40):
    print('%6d  %s' % (v, k))
print('--- write-only / edit-only / read-only counts (in repo) ---')
w = set(p for p in inrepo if p in kinds['write'])
e = set(p for p in inrepo if p in kinds['edit'])
r = set(p for p in inrepo if p in kinds['read'])
print('in write only:', len(w - e - r), 'write+...', len(w))
print('edit but no write:', len(e - w))
print('read but no write/edit:', len(r - w - e))
print('--- the six tool scripts ---')
for want in ('check_engine_anchor.ps1', 'mcp_evidence_guard.ps1', 'mcp_watch_run.ps1',
             'check_exit_propagation.py', 'check_tautologies.py', 'check_hardcoded_counts.py',
             'gen_renamed_contract.py', 'tools_list.renamed.json'):
    hits = [p for p in allp if p.replace('/', '\\').lower().endswith(want)]
    for h in hits:
        print('%-28s W=%-5s E=%-5s R=%-5s %s' % (want, h in kinds['write'], h in kinds['edit'], h in kinds['read'], h))
    if not hits:
        print('%-28s NOT FOUND in write/edit/read payloads' % want)
print('--- duplicate (f,seq,call) read events? ---')
seen = collections.Counter()
for e in load('read'):
    seen[(e['f'], e['seq'], e['call'])] += 1
dups = [k for k, v in seen.items() if v > 1]
print('read dup keys =', len(dups), 'total read events =', sum(seen.values()))
