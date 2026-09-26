# TASK-078 pass 2 (v3): candidate model with a version-coherent "read epoch" reconstruction.
#   candidate A = write/edit replay in time order
#   candidate E = mutually consistent read-epoch base (newest-first acceptance, conflicting
#                 reads dropped) + edits that happened after the epoch's newest read
# The rejected candidate is always preserved under staging\__candidates\.
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

groups = collections.OrderedDict()
for kind in ('write', 'edit', 'read'):
    for e in load(kind):
        p = e.get('path')
        if not p:
            continue
        e['kind'] = kind
        k = key(p)
        if k not in groups:
            groups[k] = {'names': collections.Counter(), 'evs': []}
        groups[k]['names'][p] += 1
        groups[k]['evs'].append(e)
for rec in groups.values():
    seen = set()
    out = []
    for e in rec['evs']:
        if e['kind'] == 'read':
            kk = (e['f'], e['seq'], e['call'], e.get('offset'))
            if kk in seen:
                continue
            seen.add(kk)
        out.append(e)
    rec['evs'] = out

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

def read_epoch(reads):
    """newest-first greedy acceptance of mutually consistent read windows"""
    acc = {}
    ordered = sorted(reads, key=lambda x: (x['time'], x['seq']), reverse=True)
    newest = ordered[0]['time'] if ordered else None
    dropped = 0
    for e in ordered:
        lines = e.get('lines') or []
        bad = False
        for num, txt in lines:
            t = txt if isinstance(txt, str) else ''
            if num in acc and acc[num] != t:
                bad = True
                break
        if bad:
            dropped += 1
            continue
        for num, txt in lines:
            acc[num] = txt if isinstance(txt, str) else ''
    total = max([e.get('totalLines') or 0 for e in reads] or [0])
    return acc, total, newest, dropped

HIST = collections.Counter()
HIST_BYTES = [0]

def hist_write(rel, content, e):
    if content is None:
        return
    hdir = os.path.join(ST, '__history', rel)
    os.makedirs(hdir, exist_ok=True)
    sha = hashlib.sha256(content.encode('utf-8', 'surrogatepass')).hexdigest()[:8]
    n = HIST[rel]
    HIST[rel] = n + 1
    src = re.sub(r'[^A-Za-z0-9_.-]', '', os.path.basename(e.get('f', 'x'))[:16])
    with open(os.path.join(hdir, '%04d_%s_seq%s_%s.bak' % (n, src, e.get('seq'), sha)), 'w', encoding='utf-8', newline='') as f:
        f.write(content)
    HIST_BYTES[0] += len(content.encode('utf-8'))

REC = []
for k, rec in groups.items():
    disp = rec['names'].most_common(1)[0][0]
    rel = stage_rel(disp)
    evs = sorted(rec['evs'], key=lambda x: (x['time'] or 0, x['seq'] or 0, x['f']))
    reads = [e for e in evs if e['kind'] == 'read']
    edits = [e for e in evs if e['kind'] == 'edit']
    writes = [e for e in evs if e['kind'] == 'write']

    # candidate A
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

    # candidate E
    eacc, etotal, enewest, edropped = read_epoch(reads)
    ecov = len(eacc)
    ecov_pct = (100.0 * ecov / etotal) if etotal else 0.0
    egaps = 0
    if eacc:
        lo, hi = min(eacc), max(eacc)
        egaps = (hi - lo + 1) - ecov
        ecand_noedit = '\n'.join(eacc[n] for n in sorted(eacc))
    else:
        ecand_noedit = ''
    post_edits = [e for e in edits if enewest is not None and (e['time'] or 0) > enewest]
    candE = ecand_noedit
    epost_fail = 0
    if candE:
        for e in post_edits:
            candE, n = apply_edit(candE, e)
            if n == 0:
                epost_fail += 1

    # later complete read
    later_complete = None
    if last_auth is not None:
        for e in sorted([x for x in reads if (x['time'] or 0) > last_auth], key=lambda x: (x['time'], x['seq'])):
            tl = e.get('totalLines') or 0
            got = [l[0] for l in (e.get('lines') or [])]
            if tl and got and min(got) == 1 and max(got) == tl:
                later_complete = e

    notes = []
    if candA is not None and not failed:
        chosen, conf = 'write-chain', 'high'
        if later_complete is not None:
            cb = '\n'.join((l[1] if isinstance(l[1], str) else '') for l in later_complete['lines'])
            if cb != candA:
                hist_write(rel, candA, later_complete)
                candA = cb
                chosen, conf = 'read-complete', 'mid'
                notes.append('LATER_COMPLETE_READ_DIFFERS(t=%s,seq=%s)' % (later_complete['time'], later_complete['seq']))
            else:
                notes.append('VERIFIED_BY_LATER_COMPLETE_READ(t=%s)' % later_complete['time'])
    elif candA is not None and failed:
        if candE and ecov_pct >= 60.0:
            chosen, conf = 'read-epoch', 'mid'
            notes.append('REPLAY_UNRELIABLE(%d failed edits); using read-epoch (cov %.1f%%, dropped %d old reads, +%d post-epoch edits, %d failed)'
                         % (len(failed), ecov_pct, edropped, len(post_edits), epost_fail))
        else:
            chosen, conf = 'write-chain', 'low'
            notes.append('REPLAY_HAS_FAILURES_UNVERIFIED(%d); epoch coverage only %.1f%%' % (len(failed), ecov_pct))
    elif candE:
        chosen = 'read-epoch'
        conf = 'mid' if not edropped else 'mid'
        notes.append('NO_WRITE_PAYLOAD; read-epoch cov %.1f%% (dropped %d conflicting old reads, %d post-epoch edits, %d failed)'
                     % (ecov_pct, edropped, len(post_edits), epost_fail))
        if edits and not post_edits and not edropped:
            base = candE
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
            if ok and chk == candE:
                conf = 'high'
                notes.append('EDIT_CHAIN_ROUNDTRIP_OK(%d edits)' % len(edits))
    else:
        chosen, conf = None, 'low'
        notes.append('NO_WRITE_NO_READ')

    final = {'write-chain': candA, 'read-complete': candA, 'read-epoch': candE}.get(chosen)

    # missing-tail / gap accounting for the chosen candidate
    if chosen in ('read-epoch', 'read-complete') or (final is not None and candA is None):
        nums = sorted(eacc) if chosen != 'read-complete' else list(range(1, (etotal or 0) + 1))
        if nums:
            missing = [n for n in range(1, (etotal or max(nums)) + 1) if n not in set(nums)]
            miss_tail = 'yes' if missing and max(missing) == (etotal or max(nums)) else ('partial-only' if missing else 'no')
            miss_n = len(missing)
        else:
            miss_tail, miss_n = 'unknown', None
    else:
        miss_tail, miss_n = ('no' if final is not None else 'unknown'), 0

    if final is not None:
        wtext(os.path.join(ST, rel), final)
        out_bytes = len(final.encode('utf-8'))
        other = candA if chosen.startswith('read') else (candE if candE else None)
        if other is not None and other != final:
            tag = 'write-chain' if chosen.startswith('read') else 'read-epoch'
            wtext(os.path.join(ST, '__candidates', safe_rel(rel + '.' + tag + '.txt')), other)
    else:
        out_bytes = None
        other = None

    REC.append({'path': disp, 'rel': rel, 'wrote': final is not None, 'bytes': out_bytes, 'conf': conf, 'chosen': chosen,
                'notes': notes, 'failed': failed[:20], 'n_failed': len(failed), 'versions': vers,
                'hist_files': HIST[rel], 'read_total': etotal, 'read_cov': ecov, 'read_cov_pct': round(ecov_pct, 1),
                'read_dropped': edropped, 'read_missing_n': miss_n, 'miss_tail': miss_tail,
                'post_epoch_edits': len(post_edits), 'post_epoch_failed': epost_fail,
                'n_write': len(writes), 'n_edit': len(edits), 'n_read': len(reads),
                'last_src': ({'kind': last_src['kind'], 'f': last_src['f'], 'seq': last_src['seq'], 'time': last_src['time']} if last_src else None),
                'alt_saved': bool(other is not None and other != final)})

with open(os.path.join(W, 'reconstruction.jsonl'), 'w', encoding='utf-8', newline='\n') as f:
    for x in REC:
        f.write(json.dumps(x, ensure_ascii=False) + '\n')

print('paths=%d staged=%d' % (len(REC), sum(1 for x in REC if x['wrote'])))
print('history files=%d bytes=%d' % (sum(HIST.values()), HIST_BYTES[0]))
print('conf:', dict(collections.Counter(x['conf'] for x in REC)))
print('chosen:', dict(collections.Counter(str(x['chosen']) for x in REC)))
print('alt saved:', sum(1 for x in REC if x['alt_saved']))
print('miss_tail:', dict(collections.Counter(str(x['miss_tail']) for x in REC)))
print('failed-edit paths:', sum(1 for x in REC if x['n_failed']))
