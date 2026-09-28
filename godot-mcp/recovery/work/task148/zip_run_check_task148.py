#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-148 evidence: end-to-end check of the delivered archive.

1. Extract two whole games (pong, snake) straight out of the delivered zip.
2. Re-hash every extracted file against the in-zip MANIFEST (not a sample: all of them).
3. Run each extracted game with `--headless --quit-after 120` from its own directory and
   require exit code 0 -- i.e. the archived copy is itself runnable, with no --mcp-port.
4. Confirm the reserved MCP ports gain no listener.

No shell redirection: subprocess pipes, this process writes its own report.
"""
import hashlib
import json
import os
import socket
import subprocess
import sys
import time
import zipfile

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = r'F:\moonbit-hof-rs\godot-mcp'
WORK = os.path.join(ROOT, 'recovery', 'work', 'task148')
UNZIP = os.path.join(WORK, 'unzip-test')
GAMES = ['pong', 'snake']
RESERVED = [9877, 9888, 9889, 8080, 8081]


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def reserved_listeners():
    found = []
    for p in RESERVED:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.2)
        try:
            if s.connect_ex(('127.0.0.1', p)) == 0:
                found.append(p)
        finally:
            s.close()
    return found


with open(os.path.join(WORK, 'package-results.json'), encoding='utf-8') as fh:
    arch = json.load(fh)[0]

pkgname = arch['pkgname']
zip_path = arch['zip']
out = []
failures = []

baseline = reserved_listeners()
out.append('delivered zip : %s' % zip_path)
out.append('volume        : %s' % pkgname)
out.append('baseline reserved listeners on %s : %s' % (RESERVED, baseline))
out.append('')

with zipfile.ZipFile(zip_path) as z:
    man_text = z.read('%s/MANIFEST.txt' % pkgname).decode('utf-8')
    man = {}
    for line in man_text.splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        parts = line.split('  ')
        if len(parts) == 4:
            man[parts[3]] = (parts[0], int(parts[1]))

    for g in GAMES:
        dest = os.path.join(UNZIP, pkgname, 'games', g)
        os.makedirs(dest, exist_ok=True)
        prefix = '%s/games/%s/' % (pkgname, g)
        names = [n for n in z.namelist() if n.startswith(prefix) and not n.endswith('/')]
        out.append('=' * 78)
        out.append('GAME %s -- %d files in the archive' % (g, len(names)))
        out.append('=' * 78)
        bad = 0
        for n in names:
            rel = n[len(pkgname) + 1:]
            data = z.read(n)
            target = os.path.join(UNZIP, pkgname, rel.replace('/', os.sep))
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, 'wb') as fh:
                fh.write(data)
            exp = man.get(rel)
            if exp is None or exp[0] != sha_bytes(data) or exp[1] != len(data):
                bad += 1
                out.append('  MISMATCH %s' % rel)
        out.append('extracted files re-hashed against MANIFEST : %d/%d ok' % (len(names) - bad, len(names)))
        if bad:
            failures.append('%s: %d extracted files do not match the manifest' % (g, bad))

        exe = os.path.join(dest, '%s.exe' % g)
        cmd = [exe, '--headless', '--quit-after', '120']
        out.append('run command : %s' % ' '.join(cmd))
        out.append('working dir : %s' % dest)
        t0 = time.time()
        try:
            p = subprocess.run(cmd, cwd=dest, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               timeout=180)
            rc = p.returncode
            sout = p.stdout.decode('utf-8', 'replace')
            serr = p.stderr.decode('utf-8', 'replace')
        except subprocess.TimeoutExpired as e:
            rc = -999
            sout = (e.stdout or b'').decode('utf-8', 'replace')
            serr = (e.stderr or b'').decode('utf-8', 'replace')
        secs = time.time() - t0
        out.append('exit code   : %s   (%.2f s)' % (rc, secs))
        out.append('stdout tail :')
        for line in [l for l in sout.splitlines() if l.strip()][-6:]:
            out.append('    ' + line)
        if serr.strip():
            out.append('stderr tail :')
            for line in [l for l in serr.splitlines() if l.strip()][-6:]:
                out.append('    ' + line)
        if rc != 0:
            failures.append('%s: extracted exe exited %s' % (g, rc))
        out.append('')

final = reserved_listeners()
out.append('final reserved listeners on %s : %s' % (RESERVED, final))
if final != baseline:
    failures.append('reserved listeners changed: %s -> %s' % (baseline, final))

out.append('')
if failures:
    out.append('ZIP RUN-CHECK VERDICT: FAIL')
    for f in failures:
        out.append('  - %s' % f)
else:
    out.append('ZIP RUN-CHECK VERDICT: PASS')
    out.append('  both extracted games re-hash 100% against the in-zip MANIFEST and run')
    out.append('  headless (120 frames) with exit code 0, without opening any MCP port.')

text = '\n'.join(out)
print(text)
with open(os.path.join(WORK, 'zip-run-check.txt'), 'w', encoding='utf-8') as fh:
    fh.write(text + '\n')
sys.exit(0 if not failures else 1)
