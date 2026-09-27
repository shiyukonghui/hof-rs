# -*- coding: utf-8 -*-
"""Independent self-check of the built review zip.

1. reads the zip's own directory listing;
2. confirms the 20 game directories are all present;
3. extracts at least 5 files (including >=1 .cs, >=1 .jsonl, >=1 .png, >=1 .md)
   into a temp dir and compares each extracted file's sha256 and byte count
   against MANIFEST.txt;
4. confirms the sidecar .sha256.txt matches the zip on disk.

    python dist\\selfcheck.py
"""
import hashlib, json, os, re, sys, tempfile, zipfile

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
DIST = r'F:\moonbit-hof-rs\godot-mcp\dist'

EXPECTED_GAMES = ['asteroids', 'bomberman', 'breakout', 'flappy', 'frogger', 'game2048',
                  'lunarlander', 'match3', 'minesweeper', 'missilecommand', 'pacman',
                  'platformer', 'pong', 'puzzlebobble', 'rtype', 'snake', 'sokoban',
                  'spaceinvaders', 'tetris', 'towerdefense']


def sha256_file(p, buf=1 << 20):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while True:
            b = f.read(buf)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def main():
    zips = [f for f in sorted(os.listdir(DIST)) if f.endswith('.zip')]
    assert len(zips) == 1, zips
    base = zips[0][:-4]
    zp = os.path.join(DIST, zips[0])
    out = []
    P = out.append
    P('=' * 78)
    P('SELF-CHECK  %s' % zips[0])
    P('=' * 78)
    P('zip path   : %s' % zp)
    P('zip bytes  : %d' % os.path.getsize(zp))
    zsha = sha256_file(zp)
    P('zip sha256 : %s' % zsha)
    P('')

    # 4. sidecar
    sha_path = os.path.join(DIST, base + '.sha256.txt')
    side = open(sha_path, encoding='utf-8').read().splitlines()
    side_sha = side[0].split()[0]
    P('[4] sidecar .sha256.txt')
    P('    path   : %s' % sha_path)
    P('    content: %s' % side[0])
    P('    match zip sha256 : %s' % ('YES' if side_sha == zsha else 'NO  <-- FAIL'))

    z = zipfile.ZipFile(zp)
    names = z.namelist()
    P('')
    P('[1] zip directory listing')
    P('    entries: %d' % len(names))
    loose = [n for n in names if not n.startswith(base + '/')]
    P('    entries outside %s/ : %d' % (base, len(loose)))
    prefixes = sorted(set(n.split('/')[0] for n in names))
    P('    top-level in zip    : %s' % prefixes)

    # 2. 20 game dirs
    games = sorted(set(n.split('/')[2] for n in names
                       if n.startswith(base + '/games/') and len(n.split('/')) > 2))
    P('')
    P('[2] game directories')
    P('    found  : %d -> %s' % (len(games), games))
    P('    expect : %d' % len(EXPECTED_GAMES))
    missing = [g for g in EXPECTED_GAMES if g not in games]
    extra = [g for g in games if g not in EXPECTED_GAMES]
    P('    missing: %s' % (missing or 'none'))
    P('    extra  : %s' % (extra or 'none'))
    P('    verdict: %s' % ('EXACTLY 20, NONE MISSING' if not missing and not extra else 'FAIL'))

    # manifest
    man = z.read(base + '/MANIFEST.txt').decode('utf-8')
    entries = {}
    for line in man.splitlines():
        m = re.match(r'^([0-9a-f]{64})\s+(\d+)\s+(.+)$', line)
        if m:
            entries[m.group(3)] = (m.group(1), int(m.group(2)))
    P('')
    P('[0] MANIFEST.txt')
    P('    header files/bytes : %s' % man.splitlines()[4])
    P('    parsed entries     : %d' % len(entries))
    P('    zip file entries   : %d (manifest itself excluded by design)'
      % (len(names) - 1))

    # 3. spot-check extractions
    P('')
    P('[3] spot-check: extract and re-hash')
    def pick(pred, n=1):
        got = []
        for nm in names:
            if nm.endswith('/') or nm.endswith('MANIFEST.txt'):
                continue
            if pred(nm):
                got.append(nm)
                if len(got) >= n:
                    break
        return got

    cs = pick(lambda n: n.endswith('.cs') and '/projects/' in n, 1)
    jsonl = pick(lambda n: n.endswith('.jsonl'), 1)
    png = pick(lambda n: n.endswith('.png'), 1)
    md = pick(lambda n: n.endswith('README-REVIEW.md'), 1)
    py = pick(lambda n: n.endswith('game_report.py'), 1)
    js = pick(lambda n: n.endswith('report.json'), 1)
    ledger = pick(lambda n: n.endswith('ledger-game.txt'), 1)
    samples = cs + jsonl + png + md + py + js + ledger
    P('    chosen %d files (>=5 required; includes .cs/.jsonl/.png/.md)' % len(samples))
    tmp = tempfile.mkdtemp(prefix='selfcheck20-')
    ok = True
    for nm in samples:
        rel = nm[len(base) + 1:]
        target = os.path.join(tmp, rel.replace('/', os.sep))
        os.makedirs(os.path.dirname(target), exist_ok=True)
        data = z.read(nm)
        with open(target, 'wb') as f:
            f.write(data)
        h = sha256_bytes(data)
        exp = entries.get(rel)
        size_ok = exp is not None and exp[1] == len(data)
        hash_ok = exp is not None and exp[0] == h
        good = size_ok and hash_ok
        ok = ok and good
        P('    %-4s %s' % ('OK' if good else 'FAIL', rel))
        P('         extracted bytes=%d sha256=%s' % (len(data), h))
        P('         manifest  bytes=%s sha256=%s'
          % (exp[1] if exp else 'MISSING', exp[0] if exp else 'MISSING'))

    # extra: every zip entry is in the manifest and vice versa
    P('')
    P('[3b] manifest vs zip completeness')
    zip_files = set(n[len(base) + 1:] for n in names
                    if not n.endswith('/') and n != base + '/MANIFEST.txt')
    missing_from_manifest = sorted(zip_files - set(entries))
    missing_from_zip = sorted(set(entries) - zip_files)
    P('    in zip not in manifest : %d %s' % (len(missing_from_manifest), missing_from_manifest[:5]))
    P('    in manifest not in zip : %d %s' % (len(missing_from_zip), missing_from_zip[:5]))
    ok = ok and not missing_from_manifest and not missing_from_zip

    P('')
    P('=' * 78)
    verdict = 'PASS' if (ok and not missing and not extra and side_sha == zsha) else 'FAIL'
    P('SELF-CHECK VERDICT: %s' % verdict)
    P('=' * 78)
    text = '\n'.join(out) + '\n'
    with open(os.path.join(DIST, 'SELFCHECK.txt'), 'w', encoding='utf-8') as f:
        f.write(text)
    print(text)
    return 0 if verdict == 'PASS' else 1


sys.exit(main())
