# TASK-078 pass 2: rebuild final versions of every file payload into C:\...\mcp-recovery\staging\
# Also emits work\reconstruction.jsonl (one record per path) for the manifest.
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
        c = re.sub(r'[*?"<>|]', '_', c)
        parts.append(c)
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

# ---------------- load & group ----------------
groups = collections.OrderedDict()   # key -> {'names':Counter,'evs':[]}
def g(k, name):
    if k not in groups:
        groups[k] = {'names': collections.Counter(), 'evs': []}
    groups[k]['names'][name] += 1
    return groups[k]

counts = collections.Counter()
for kind in ('write', 'edit', 'read'):
    for e in load(kind):
        p = e.get('path')
        if not p:
            counts['skip-empty-path-' + kind] += 1
            continue
        e['kind'] = kind
        g(key(p), p)['evs'].append(e)
        counts[kind] += 1

# dedupe reads (identical f/seq/call/offset)
dedup = 0
for rec in groups.values():
    seen = set()
    out = []
    for e in rec['evs']:
        if e['kind'] == 'read':
            k = (e['f'], e['seq'], e['call'], e.get('offset'))
            if k in seen:
                dedup += 1
                continue
            seen.add(k)
        out.append(e)
    rec['evs'] = out
counts['read-dedup'] = dedup

# ---------------- reconstruction ----------------
def merge_reads(reads):
    """latest observation per line number"""
    best = {}
    conflicts = []
    total = 0
    for e in sorted(reads, key=lambda x: (x['time'], x['seq'])):
        tl = e.get('totalLines') or 0
        if tl > total:
            total = tl
        for num, txt in e.get('lines') or []:
            if num is None:
                continue
            t = txt if isinstance(txt, str) else ''
            prev = best.get(num)
            if prev is None:
                best[num] = (t, e['time'])
            else:
                if prev[0] != t:
                    conflicts.append(num)
                best[num] = (t, e['time'])
    return best, total, sorted(set(conflicts))

def join_lines(best, total):
    nums = sorted(best)
    if not nums:
        return '', []
    missing = [n for n in range(1, (total or max(nums)) + 1) if n not in best]
    body = '\n'.join(best[n][0] for n in nums)
    if nums and best[nums[-1]][0] == '' and nums[-1] == (total or max(nums)):
        pass
    return body, missing

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

REC = []
HIST_N = collections.Counter()
HIST_BYTES = 0

def hist_write(path, content, e):
    global HIST_BYTES
    hdir = os.path.join(ST, '__history', stage_rel(path))
    os.makedirs(hdir, exist_ok=True)
    n = HIST_N[stage_rel(path)]
    HIST_N[stage_rel(path)] += 1
    name = '%04d_%s_seq%s.bak' % (n, re.sub(r'[^A-Za-z0-9_.-]', '', os.path.basename(e.get('f', 'x'))[:20]), e.get('seq'))
    fp = os.path.join(hdir, name)
    with open(fp, 'w', encoding='utf-8', newline='') as f:
        f.write(content)
    HIST_BYTES += len(content.encode('utf-8'))
    return os.path.relpath(fp, ST)

def recon(rec):
    evs = sorted(rec['evs'], key=lambda x: (x['time'] or 0, x['seq'] or 0, x['f']))
    writes = [e for e in evs if e['kind'] == 'write']
    edits = [e for e in evs if e['kind'] == 'edit']
    reads = [e for e in evs if e['kind'] == 'read']
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
                hist_write(rec['names'].most_common(1)[0][0], state, e)
                vers += 1
            state = c
            last_auth = e['time']
            last_src = e
        elif e['kind'] == 'edit':
            if state is None:
                failed.append((e['time'], e['seq'], 'no-base'))
                last_auth = e['time']
                last_src = e
                continue
            ns, n = apply_edit(state, e)
            if n == 0:
                failed.append((e['time'], e['seq'], 'old-not-found'))
            else:
                if ns != state:
                    hist_write(rec['names'].most_common(1)[0][0], state, e)
                    vers += 1
                state = ns
            last_auth = e['time']
            last_src = e
    read_best, read_total, read_conflicts = merge_reads(reads)
    read_body, read_missing = join_lines(read_best, read_total)
    later = [e for e in reads if last_auth is not None and (e['time'] or 0) > last_auth]

    conf = 'low'
    notes = []
    final = None
    if state is not None:
        conf = 'high' if not failed else 'mid'
        final = state
        # a later COMPLETE read is ground truth (files can also be rewritten by term commands)
        complete_later = None
        for e in sorted(later, key=lambda x: (x['time'], x['seq'])):
            tl = e.get('totalLines') or 0
            got = [l[0] for l in (e.get('lines') or [])]
            if tl and len(got) == tl and got and min(got) == 1 and max(got) == tl:
                complete_later = e
        if complete_later is not None:
            cb = '\n'.join((l[1] if isinstance(l[1], str) else '') for l in complete_later['lines'])
            if cb != state:
                notes.append('LATER_COMPLETE_READ_DIFFERS(t=%s,seq=%s): took read version' % (complete_later['time'], complete_later['seq']))
                hist_write(rec['names'].most_common(1)[0][0], state, complete_later)
                vers += 1
                final = cb
                conf = 'mid'
            else:
                notes.append('VERIFIED_BY_LATER_COMPLETE_READ(t=%s,seq=%s)' % (complete_later['time'], complete_later['seq']))
                conf = 'high'
        elif later and read_body:
            # compare overlap between replayed state and later partial reads
            sl = state.split('\n')
            bad = 0
            for n, t in read_best.items():
                if 1 <= n <= len(sl) and sl[n - 1] != t:
                    bad += 1
            if bad:
                notes.append('CONFLICT_WITH_LATER_PARTIAL_READ(%d lines)' % bad)
                conf = 'mid'
    else:
        # no write at all -> read reconstruction
        if read_best:
            final = read_body
            lo = max(read_best)
            if read_total and lo < read_total:
                pass
            if read_conflicts:
                conf = 'low'
                notes.append('READ_WINDOW_CONFLICTS(%d lines)' % len(read_conflicts))
            else:
                conf = 'mid'
            if edits:
                # try reverse-apply of the whole edit chain onto the final read, then verify forward
                base = final
                ok = True
                for e in reversed(edits):
                    new = e.get('new') or ''
                    old = e.get('old') or ''
                    if new and new in base:
                        n = base.count(new) if e.get('replace_all') else 1
                        base = base.replace(new, old, n)
                    elif new == '':
                        ok = False
                        break
                    else:
                        ok = False
                        break
                chk = base
                for e in edits:
                    chk, n = apply_edit(chk, e)
                    if n == 0:
                        ok = False
                        break
                if ok and chk == final:
                    conf = 'high'
                    notes.append('EDIT_CHAIN_ROUNDTRIP_OK(%d edits)' % len(edits))
                else:
                    notes.append('EDIT_CHAIN_UNVERIFIED; using read reconstruction')
        else:
            final = None
            conf = 'low'
            notes.append('NO_WRITE_NO_READ')
    return {'state': final, 'conf': conf, 'notes': notes, 'failed': failed,
            'versions': vers, 'read_total': read_total, 'read_missing': read_missing,
            'read_conflicts': read_conflicts, 'n_write': len(writes), 'n_edit': len(edits),
            'n_read': len(reads), 'last_auth': last_auth,
            'last_src': ({'kind': last_src['kind'], 'f': last_src['f'], 'seq': last_src['seq'], 'time': last_src['time']} if last_src else None)}

n_out = 0
for k, rec in groups.items():
    disp = rec['names'].most_common(1)[0][0]
    r = recon(rec)
    rel = stage_rel(disp)
    data = r['state']
    out_bytes = None
    wrote = False
    if data is not None:
        fp = os.path.join(ST, rel)
        ensure_parent(fp)
        with open(fp, 'w', encoding='utf-8', newline='') as f:
            f.write(data)
        out_bytes = len(data.encode('utf-8'))
        n_out += 1
        wrote = True
    miss_tail = 'unknown'
    miss_n = None
    if r['state'] is not None and r['n_write'] == 0 and r['read_total']:
        got = max([l for l in range(1, r['read_total'] + 1)]) if False else None
        miss_n = len(r['read_missing'])
        miss_tail = 'yes' if (r['read_missing'] and max(r['read_missing']) == r['read_total']) else ('partial-only' if r['read_missing'] else 'no')
    elif wrote:
        miss_tail = 'no'
    REC.append({'path': disp, 'rel': rel, 'wrote': wrote, 'bytes': out_bytes, 'conf': r['conf'],
                'notes': r['notes'], 'failed': r['failed'][:20], 'n_failed': len(r['failed']),
                'versions': r['versions'], 'read_total': r['read_total'],
                'read_missing_n': miss_n, 'miss_tail': miss_tail,
                'read_conflicts': len(r['read_conflicts']),
                'n_write': r['n_write'], 'n_edit': r['n_edit'], 'n_read': r['n_read'],
                'last_src': r['last_src']})

with open(os.path.join(W, 'reconstruction.jsonl'), 'w', encoding='utf-8', newline='\n') as f:
    for x in REC:
        f.write(json.dumps(x, ensure_ascii=False) + '\n')

print('paths=%d staged=%d' % (len(REC), n_out))
print('history files=%d bytes=%d' % (sum(HIST_N.values()), HIST_BYTES))
print('conf:', dict(collections.Counter(x['conf'] for x in REC)))
print('miss_tail:', dict(collections.Counter(str(x['miss_tail']) for x in REC)))
print('no-write paths:', sum(1 for x in REC if x['n_write'] == 0))
print('failed edits paths:', sum(1 for x in REC if x['n_failed']))
print('counts:', dict(counts))
