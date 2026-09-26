# TASK-078 pass 2 (v2): rebuild final versions of every file payload into staging\.
# v2 adds: read-merge coverage metrics, candidate comparison, safer selection when the
# write/edit replay has failures, __candidates\ preservation of the rejected candidate,
# hash-deduped __history.
# WRITES ONLY UNDER C:\Users\wyl\AppData\Local\Temp\mcp-recovery\
import json, os, re, sys, collections, hashlib

ROOT = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery'
W = os.path.join(ROOT, 'work')
ST = os.path.join(ROOT, 'staging')
REPO = 'F:\\RustProjects\\godot-mcp-pro\\code\\godot\\'

def norm(p):
    return (p or '').replace('/', '\\')

def key(p):
    return norm(p).lower()

def load(kind):
    with open(os.path.join(W, 'events-%s.jsonl' % kind), 'r', encoding='utf-8') as f:
        for line in f:
            try:
                yield json.loads(line)
            except Exception:
                pass

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

def ensure_parent(p):
    d = os.path.dirname(p)
    if d:
        os.makedirs(d, exist_ok=True)

def wtext(path, data):
    ensure_parent(path)
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(data)

# ---------------- load & group ----------------
groups = collections.OrderedDict()
counts = collections.Counter()
for kind in ('write', 'edit', 'read'):
    for e in load(kind):
        p = e.get('path')
        if not p:
            counts['skip-empty-path-' + kind] += 1
            continue
        e['kind'] = kind
        k = key(p)
        if k not in groups:
            groups[k] = {'names': collections.Counter(), 'evs': []}
        groups[k]['names'][p] += 1
        groups[k]['evs'].append(e)
        counts[kind] += 1

dedup = 0
for rec in groups.values():
    seen = set()
    out = []
    for e in rec['evs']:
        if e['kind'] == 'read':
            kk = (e['f'], e['seq'], e['call'], e.get('offset'))
            if kk in seen:
                dedup += 1
                continue
            seen.add(kk)
        out.append(e)
    rec['evs'] = out
counts['read-dedup'] = dedup

# ---------------- helpers ----------------
def merge_reads(reads):
    best = {}
    conflicts = set()
    total = 0
    for e in sorted(reads, key=lambda x: (x['time'], x['seq'])):
        total = max(total, e.get('totalLines') or 0)
        for num, txt in e.get('lines') or []:
            if num is None:
                continue
            t = txt if isinstance(txt, str) else ''
            prev = best.get(num)
            if prev is not None and prev[0] != t:
                conflicts.add(num)
            best[num] = (t, e['time'])
    return best, total, conflicts

def join_lines(best, total):
    nums = sorted(best)
    if not nums:
        return '', []
    total = total or nums[-1]
    missing = [n for n in range(1, total + 1) if n not in best]
    return '\n'.join(best[n][0] for n in nums), missing

def apply_edit(state, e):
    old = e.get('old') or ''
    new = e.get('new') or ''
    if old == '':
        return state, 0
    cnt = state.count(old)
    if e.get('replace_all'):
        return state.replace(old, new), cnt
    if cnt == 0:
        return state, 0
    return state.replace(old, new, 1), 1

HIST = collections.Counter()
HIST_BYTES = [0]

def hist_write(rel, content, e):
    if content is None:
        return None
    hdir = os.path.join(ST, '__history', rel)
    os.makedirs(hdir, exist_ok=True)
    sha = hashlib.sha256(content.encode('utf-8', 'surrogatepass')).hexdigest()[:8]
    n = HIST[rel]
    HIST[rel] = n + 1
    src = re.sub(r'[^A-Za-z0-9_.-]', '', os.path.basename(e.get('f', 'x'))[:16])
    name = '%04d_%s_seq%s_%s.bak' % (n, src, e.get('seq'), sha)
    fp = os.path.join(hdir, name)
    with open(fp, 'w', encoding='utf-8', newline='') as f:
        f.write(content)
    HIST_BYTES[0] += len(content.encode('utf-8'))
    return name

REC = []
for k, rec in groups.items():
    disp = rec['names'].most_common(1)[0][0]
    rel = stage_rel(disp)
    evs = sorted(rec['evs'], key=lambda x: (x['time'] or 0, x['seq'] or 0, x['f']))
    reads = [e for e in evs if e['kind'] == 'read']

    # --- candidate A: write/edit replay in time order
    state = None
    vers = 0
    failed = []
    last_auth = None
    last_src = None
    for e in evs:
        if e['kind'] == 'write':
            c = e.get('content')
            c = c if isinstance(c, str) else ''
            if state is not None and state != c:
                hist_write(rel, state, e)
                vers += 1
            state = c
            last_auth = e['time']
            last_src = e
        elif e['kind'] == 'edit':
            if state is None:
                failed.append([e['time'], e['seq'], 'no-base'])
                last_auth = e['time']
                last_src = e
                continue
            ns, n = apply_edit(state, e)
            if n == 0:
                failed.append([e['time'], e['seq'], 'old-not-found'])
            else:
                if ns != state:
                    hist_write(rel, state, e)
                    vers += 1
                state = ns
            last_auth = e['time']
            last_src = e
    candA = state

    # --- candidate B: read-merge (latest observation per line number)
    rbest, rtotal, rconf = merge_reads(reads)
    candB, rmissing = join_lines(rbest, rtotal)
    cov = len(rbest)
    cov_pct = (100.0 * cov / rtotal) if rtotal else 0.0

    # --- later complete read = ground truth
    later_complete = None
    if last_auth is not None:
        for e in sorted([x for x in reads if (x['time'] or 0) > last_auth], key=lambda x: (x['time'], x['seq'])):
            tl = e.get('totalLines') or 0
            got = [l[0] for l in (e.get('lines') or [])]
            if tl and got and min(got) == 1 and max(got) == tl:
                later_complete = e
    notes = []
    chosen = None
    conf = 'low'
    if candA is not None:
        if not failed:
            chosen, conf = 'write-chain', 'high'
        elif cov_pct >= 80.0 and cov:
            chosen, conf = 'read-merge', 'mid'
            notes.append('REPLAY_UNRELIABLE(%d failed edits); read coverage %.1f%%' % (len(failed), cov_pct))
        else:
            chosen, conf = 'write-chain', 'low'
            notes.append('REPLAY_HAS_FAILURES_UNVERIFIED(%d) and read coverage only %.1f%%' % (len(failed), cov_pct))
    elif candB:
        chosen, conf = 'read-merge', 'low' if rconf else 'mid'
        if rconf:
            notes.append('READ_WINDOW_CONFLICTS(%d lines)' % len(rconf))
    if later_complete is not None:
        cb = '\n'.join((l[1] if isinstance(l[1], str) else '') for l in later_complete['lines'])
        if chosen == 'write-chain' and cb != candA:
            hist_write(rel, candA, later_complete)
            candA = cb
            chosen, conf = 'read-complete', 'mid'
            notes.append('LATER_COMPLETE_READ_DIFFERS(t=%s,seq=%s)' % (later_complete['time'], later_complete['seq']))
        elif cb == candA and chosen == 'write-chain':
            conf = 'high'
            notes.append('VERIFIED_BY_LATER_COMPLETE_READ(t=%s)' % later_complete['time'])

    final = {'write-chain': candA, 'read-merge': candB, 'read-complete': candA}.get(chosen)
    if final is None:
        final = candA if candA is not None else (candB or None)

    # edit-chain roundtrip test for the no-write case
    edits = [e for e in evs if e['kind'] == 'edit']
    if candA is None and candB and edits and chosen == 'read-merge' and not rconf:
        base = candB
        ok = True
        for e in reversed(edits):
            new = e.get('new') or ''
            old = e.get('old') or ''
            if new and new in base:
                n = base.count(new) if e.get('replace_all') else 1
                base = base.replace(new, old, n)
            else:
                ok = False
                break
        chk = base
        for e in edits:
            chk, n = apply_edit(chk, e)
            if n == 0:
                ok = False
                break
        if ok and chk == candB:
            conf = 'high'
            notes.append('EDIT_CHAIN_ROUNDTRIP_OK(%d edits)' % len(edits))
        else:
            notes.append('EDIT_CHAIN_UNVERIFIED')

    other = candB if chosen == 'write-chain' else candA
    if final is not None:
        wtext(os.path.join(ST, rel), final)
        if other is not None and other != final:
            wtext(os.path.join(ST, '__candidates', rel + '.write-chain.txt' if chosen != 'write-chain' else rel + '.read-merge.txt'), other)

    wrote = final is not None
    if wrote:
        out_bytes = len(final.encode('utf-8'))
        if chosen in ('read-merge', 'read-complete'):
            miss_tail = 'yes' if rmissing and max(rmissing) == (rtotal or max(rbest)) else ('partial-only' if rmissing else 'no')
        else:
            miss_tail = 'no'
    else:
        out_bytes = None
        miss_tail = 'unknown'
    REC.append({'path': disp, 'rel': rel, 'wrote': wrote, 'bytes': out_bytes, 'conf': conf, 'chosen': chosen,
                'notes': notes, 'failed': failed[:20], 'n_failed': len(failed),
                'versions': vers, 'hist_files': HIST[rel],
                'read_total': rtotal, 'read_cov': cov, 'read_cov_pct': round(cov_pct, 1),
                'read_missing_n': len(rmissing), 'miss_tail': miss_tail,
                'read_conflicts': len(rconf),
                'n_write': sum(1 for e in evs if e['kind'] == 'write'),
                'n_edit': len(edits), 'n_read': len(reads),
                'last_src': ({'kind': last_src['kind'], 'f': last_src['f'], 'seq': last_src['seq'], 'time': last_src['time']} if last_src else None),
                'alt_saved': bool(other is not None and final is not None and other != final)})

with open(os.path.join(W, 'reconstruction.jsonl'), 'w', encoding='utf-8', newline='\n') as f:
    for x in REC:
        f.write(json.dumps(x, ensure_ascii=False) + '\n')

print('paths=%d staged=%d' % (len(REC), sum(1 for x in REC if x['wrote'])))
print('history files=%d bytes=%d' % (sum(HIST.values()), HIST_BYTES[0]))
print('conf:', dict(collections.Counter(x['conf'] for x in REC)))
print('chosen:', dict(collections.Counter(str(x['chosen']) for x in REC)))
print('alt saved:', sum(1 for x in REC if x['alt_saved']))
print('miss_tail:', dict(collections.Counter(str(x['miss_tail']) for x in REC)))
print('no-write paths:', sum(1 for x in REC if x['n_write'] == 0))
print('failed-edit paths:', sum(1 for x in REC if x['n_failed']))
print('counts:', dict(counts))
