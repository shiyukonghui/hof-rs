#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""TASK-079 stage 2a: assemble the rebuild tree on C: from the audit002 baseline
and the TASK-078 staging payloads.  Move + inventory only.  No shell redirects,
no writes outside C:\\Users\\wyl\\AppData\\Local\\Temp\\mcp-recovery\\, no F: writes.
"""
import io, json, os, shutil, sys, hashlib, time

ROOT = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery'
STAGING = os.path.join(ROOT, 'staging')
TEMP = os.environ['TEMP']
BASELINE = os.path.join(TEMP, 'audit002', 'tree')
REBUILD = os.path.join(ROOT, 'rebuild')
GODOT = os.path.join(REBUILD, 'godot')
LOW = os.path.join(REBUILD, '_low-confidence')
EXCL = os.path.join(REBUILD, '_excluded')
REFS = os.path.join(REBUILD, '_refs')
WORK = os.path.join(ROOT, 'work')

ALLOWED = ROOT.rstrip('\\') + '\\'

BASE_EXCLUDE_DIRS = {'__pycache__'}
BASE_EXCLUDE_TOP = {os.path.join('bin', 'obj')}


def guard(p):
    ap = os.path.abspath(p)
    if not ap.startswith(ALLOWED):
        raise RuntimeError('refusing path outside mcp-recovery: %s' % ap)
    if '..' in ap.split(os.sep):
        raise RuntimeError('refusing path with ..: %s' % ap)
    if any(ch in ap for ch in '*?'):
        raise RuntimeError('refusing path with wildcard: %s' % ap)
    if not os.path.isabs(ap):
        raise RuntimeError('refusing relative path: %s' % ap)
    return ap


def sha256(p, n=1 << 20):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while True:
            b = f.read(n)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def put(src, dst):
    """copy src -> dst (never overwrites silently across roots: caller decides)"""
    guard(dst)
    d = os.path.dirname(dst)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    shutil.copyfile(src, dst)
    return os.path.getsize(dst)


def read_index():
    rows = []
    with io.open(os.path.join(STAGING, '__payload-index', 'reconstruction.jsonl'),
                 encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def main():
    t0 = time.time()
    # ---------- guards ----------
    for d in (REBUILD, GODOT, LOW, EXCL, REFS, WORK):
        guard(d)

    resume = os.path.isdir(GODOT) and any(os.scandir(GODOT))
    if resume and not os.path.isfile(os.path.join(GODOT, 'SConstruct')):
        raise RuntimeError('rebuild\\godot exists but has no SConstruct; refusing to resume. '
                           'A guarded clean must be authorised first (no deletion performed).')

    stats = {'generated': time.strftime('%Y-%m-%d %H:%M:%S'), 'baseline': BASELINE,
             'excluded_from_baseline': sorted(BASE_EXCLUDE_TOP) + sorted(BASE_EXCLUDE_DIRS),
             'baseline_resumed': resume}

    # ---------- 1. baseline copy (verified / idempotent) ----------
    base_files = base_bytes = 0
    base_verified = base_repaired = 0
    for dirpath, dirnames, filenames in os.walk(BASELINE):
        rel = os.path.relpath(dirpath, BASELINE)
        if rel == '.':
            rel = ''
        keep = []
        for d in dirnames:
            full_rel = os.path.join(rel, d)
            if d in BASE_EXCLUDE_DIRS or full_rel in BASE_EXCLUDE_TOP:
                continue
            keep.append(d)
        dirnames[:] = keep
        for fn in filenames:
            s = os.path.join(dirpath, fn)
            r = os.path.join(rel, fn) if rel else fn
            try:
                sz = os.path.getsize(s)
            except OSError:
                continue
            dst = os.path.join(GODOT, r)
            if os.path.isfile(dst) and os.path.getsize(dst) == sz:
                base_verified += 1
            else:
                if os.path.isfile(dst):
                    base_repaired += 1
                put(s, dst)
            base_files += 1
            base_bytes += sz
    # count what we skipped, for the record
    base_skipped_files = base_skipped_bytes = 0
    for top in BASE_EXCLUDE_TOP:
        p = os.path.join(BASELINE, top)
        if os.path.isdir(p):
            for dirpath2, _dn2, fs in os.walk(p):
                for fn in fs:
                    fp = os.path.join(dirpath2, fn)
                    try:
                        base_skipped_files += 1
                        base_skipped_bytes += os.path.getsize(fp)
                    except OSError:
                        pass
    stats['baseline_copy'] = {'files': base_files, 'bytes': base_bytes,
                              'already_present_verified': base_verified,
                              'size_mismatch_repaired': base_repaired}
    stats['baseline_skipped'] = {'files': base_skipped_files, 'bytes': base_skipped_bytes}

    # ---------- 2. overlay staged payloads ----------
    rows = read_index()
    landed = []          # dicts
    lowlanded = []
    excluded = []
    skipped = []         # staging fragment not landed (baseline copy already complete)

    for d in rows:
        rel = d['rel']
        if not d.get('wrote'):
            skipped.append({'rel': rel, 'why': 'no staged payload (wrote=false)', 'conf': d['conf']})
            continue
        if rel.startswith('__external'):
            skipped.append({'rel': rel, 'why': 'out-of-repo payload (not part of the godot tree)', 'conf': d['conf']})
            continue
        src = os.path.join(STAGING, rel)
        if not os.path.isfile(src):
            skipped.append({'rel': rel, 'why': 'indexed but no staged file on disk', 'conf': d['conf']})
            continue

        conf = d['conf']          # high | mid | low  (raw: 高/中/低 in manifest)
        c = {'high': 'high', 'mid': 'mid', 'low': 'low'}.get(conf, conf)
        in_module = rel.startswith('modules\\mcp_server\\')
        rec = {'rel': rel, 'conf': conf, 'bytes': d['bytes'], 'cov': d['read_cov_pct'],
               'tail': d['miss_tail'], 'failed': d['n_failed'], 'n_edit': d['n_edit']}

        if rel.startswith('modules\\mcp_server\\.git\\'):
            put(src, os.path.join(EXCL, rel))
            rec['why'] = 'scratch file written into .git/ (not repo content); parked under _excluded'
            excluded.append(rec)
            continue

        dest_root = GODOT
        if c == 'low':
            dest_root = LOW
        elif not in_module:
            # engine / root / docs asset: only land when the baseline has no copy
            dst_probe = os.path.join(GODOT, rel)
            if os.path.isfile(dst_probe):
                if sha256(dst_probe) == sha256(src):
                    rec['dest'] = os.path.relpath(dst_probe, ROOT)
                    rec['sha256'] = sha256(dst_probe)
                    rec['note'] = 'already present in the baseline copy and byte-identical'
                    landed.append(rec)
                    continue
                skipped.append({'rel': rel, 'why':
                                'staging copy is a partial read (%s%%, tail=%s, %d failed edits); '
                                'baseline copy is complete -> kept baseline, fragment NOT overlaid'
                                % (d['read_cov_pct'], d['miss_tail'], d['n_failed']), 'conf': conf})
                continue
        n = put(src, os.path.join(dest_root, rel))
        rec['dest'] = os.path.relpath(os.path.join(dest_root, rel), ROOT)
        rec['sha256'] = sha256(os.path.join(dest_root, rel))
        if dest_root is LOW:
            lowlanded.append(rec)
        else:
            landed.append(rec)

    stats['module_landed_high_mid'] = len([r for r in landed if r['rel'].startswith('modules\\mcp_server\\')])
    stats['other_landed_high_mid'] = len([r for r in landed if not r['rel'].startswith('modules\\mcp_server\\')])
    stats['low_confidence_landed'] = len(lowlanded)
    stats['excluded'] = len(excluded)
    stats['skipped'] = len(skipped)

    # ---------- 3. docs assets rule (4) ----------
    assets = []

    def land_with_source(rel_repo, src, note, stale):
        dst = os.path.join(GODOT, rel_repo)
        n = put(src, dst)
        assets.append({'repo_path': rel_repo, 'source': src.replace(TEMP, '%TEMP%').replace(ROOT, '%RECOVERY%'),
                       'bytes': n, 'sha256': sha256(dst), 'note': note, 'stale': stale})

    mbackup = os.path.join(TEMP, 'mcp044-module-backup', 'mcp_server', 'docs')
    land_with_source(r'modules\mcp_server\docs\tools_list.renamed.json',
                     os.path.join(mbackup, 'tools_list.renamed.json'),
                     'staging copy is a truncated read-epoch (20.3% coverage, tail missing) -> '
                     'full copy taken from the TASK-044 module backup. _meta lists 171 tools, '
                     'NOT the final 176; RECOVERY-PLAN 4.2 requires regeneration by '
                     'scripts/gen_renamed_contract.py, do not trust this copy.',
                     True)
    land_with_source(r'modules\mcp_server\docs\tool-rename-map.json',
                     os.path.join(mbackup, 'tool-rename-map.json'),
                     'staging copy is a truncated read-epoch (14.8% coverage, tail missing) -> full copy '
                     'from the TASK-044 module backup; sha256 matches _meta.map_sha256 of the '
                     'tools_list.renamed.json contracts, so this is the last known good map.',
                     False)
    # legacy 174-tool input fixture (read-only from the intact outer repo F:)
    legacy_src = r'F:\moonbit-hof-rs\tests\fixtures\mcp\tools_list.json'
    legacy_dst = os.path.join(REFS, 'legacy-174', 'tools_list.json')
    n = put(legacy_src, legacy_dst)
    assets.append({'repo_path': r'_refs\legacy-174\tools_list.json', 'source': legacy_src,
                   'bytes': n, 'sha256': sha256(legacy_dst),
                   'note': 'READ-ONLY from the intact outer repo F:\\moonbit-hof-rs; 174 tools; '
                           'its sha256 equals _meta.generated_from_sha256 of the renamed contract, '
                           'i.e. this is the legacy 174-tool generator input.',
                   'stale': False})
    # keep the truncated staging variants next to the low-confidence material, for audit
    for rel in (r'modules\mcp_server\docs\tools_list.renamed.json',
                r'modules\mcp_server\docs\tool-rename-map.json'):
        s = os.path.join(STAGING, rel)
        if os.path.isfile(s):
            put(s, os.path.join(LOW, rel))
            lowlanded.append({'rel': rel, 'conf': 'mid(truncated)', 'bytes': os.path.getsize(s),
                              'cov': None, 'tail': 'yes', 'failed': None, 'n_edit': None,
                              'dest': os.path.relpath(os.path.join(LOW, rel), ROOT),
                              'why': 'kept for audit; the truncated staging variant'})
    stats['assets'] = assets

    # ---------- 4. per-directory inventory of rebuild\godot ----------
    inv = {}
    total_f = total_b = 0
    for dirpath, dirnames, filenames in os.walk(GODOT):
        rel = os.path.relpath(dirpath, GODOT)
        top = rel.split(os.sep)[0] if rel != '.' else '(root)'
        for fn in filenames:
            fp = os.path.join(dirpath, fn)
            try:
                sz = os.path.getsize(fp)
            except OSError:
                continue
            e = inv.setdefault(top, {'files': 0, 'bytes': 0})
            e['files'] += 1
            e['bytes'] += sz
            total_f += 1
            total_b += sz
    stats['godot_inventory'] = inv
    stats['godot_totals'] = {'files': total_f, 'bytes': total_b}

    inv_low = {}
    for dirpath, dirnames, filenames in os.walk(LOW):
        rel = os.path.relpath(dirpath, LOW)
        top = rel.split(os.sep)[0] if rel != '.' else '(root)'
        for fn in filenames:
            sz = os.path.getsize(os.path.join(dirpath, fn))
            e = inv_low.setdefault(top, {'files': 0, 'bytes': 0})
            e['files'] += 1
            e['bytes'] += sz
    stats['low_inventory'] = inv_low

    stats['landed'] = landed
    stats['low_landed'] = lowlanded
    stats['excluded_list'] = excluded
    stats['skipped'] = skipped
    byreason = {}
    for s in skipped:
        key = s['why'].split(';')[0].split(' -> ')[0][:90]
        byreason[key] = byreason.get(key, 0) + 1
    stats['skipped_by_reason'] = byreason
    stats['elapsed_s'] = round(time.time() - t0, 1)

    out = os.path.join(WORK, 'assembly-stats.json')
    with io.open(out, 'w', encoding='utf-8') as f:
        f.write(json.dumps(stats, ensure_ascii=False, indent=1))

    print('baseline copied : %d files / %d bytes' % (base_files, base_bytes))
    print('baseline skipped: %d files / %d bytes (bin\\obj + __pycache__)' % (base_skipped_files, base_skipped_bytes))
    print('module landed   : %d' % stats['module_landed_high_mid'])
    print('other landed    : %d' % stats['other_landed_high_mid'])
    print('low-confidence  : %d' % stats['low_confidence_landed'])
    print('excluded        : %d' % stats['excluded'])
    print('skipped         : %d' % len(stats['skipped']))
    print('godot totals    : %d files / %d bytes' % (total_f, total_b))
    print('assets          : %d' % len(assets))
    print('stats -> ' + out)


if __name__ == '__main__':
    main()
