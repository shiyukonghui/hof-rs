# -*- coding: utf-8 -*-
"""TASK-082 item 4: assemble the build evidence bundle inside the work tree."""
import hashlib, os, re, shutil, sys

C = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery'
W = os.path.join(C, 'work', 'task082')
L = os.path.join(C, 'logs')
DST = r'H:\rebuild\godot\modules\mcp_server\docs\reports\evidence\task082'

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
os.makedirs(DST, exist_ok=True)


def decode(src, dst):
    raw = open(src, 'rb').read()
    for enc in ('utf-8', 'cp936'):
        try:
            t = raw.decode(enc)
            used = enc
            break
        except Exception:
            continue
    else:
        t = raw.decode('utf-8', 'replace')
        used = 'utf-8/replace'
    t = t.replace('\r\n', '\n').replace('\r', '\n')
    open(dst, 'w', encoding='utf-8', newline='\n').write(t)
    print('%-40s -> %-46s %8d B  (decoded %s)' % (os.path.basename(src), os.path.basename(dst), os.path.getsize(dst), used))


print('=== decoded logs ===')
for src, dst in [
    (os.path.join(L, 'task082_build1.err.txt'), os.path.join(DST, 'build1-tests-yes.stderr.txt')),
    (os.path.join(L, 'task082_build2_notests.err.txt'), os.path.join(DST, 'build2-tests-no.stderr.txt')),
    (os.path.join(L, 'task082_build3_keepgoing.err.txt'), os.path.join(DST, 'build3-keepgoing.stderr.txt')),
]:
    decode(src, dst)

print('=== copied stdout logs (already UTF-8 because cmd ran under chcp 65001) ===')
for src, dst in [
    (os.path.join(L, 'task082_build1.txt'), os.path.join(DST, 'build1-tests-yes.stdout.txt')),
    (os.path.join(L, 'task082_build2_notests.txt'), os.path.join(DST, 'build2-tests-no.stdout.txt')),
    (os.path.join(L, 'task082_build3_keepgoing.txt'), os.path.join(DST, 'build3-keepgoing.stdout.txt')),
]:
    shutil.copyfile(src, dst)
    print('%-40s -> %-46s %8d B' % (os.path.basename(src), os.path.basename(dst), os.path.getsize(dst)))

print('=== copied analysis artefacts ===')
for src, dst in [
    (os.path.join(W, 'promoted-lowconf.txt'), os.path.join(DST, 'item1-promoted-lowconf.txt')),
    (os.path.join(W, 'truncation-classes.txt'), os.path.join(DST, 'item4-truncation-classes.txt')),
    (os.path.join(W, 'build3-errors.txt'), os.path.join(DST, 'item4-build3-errors-summary.txt')),
    (os.path.join(C, 'logs', 'task082_contract.txt'), os.path.join(DST, 'item3-contract-regeneration.txt')),
]:
    shutil.copyfile(src, dst)
    print('%-40s -> %-46s %8d B' % (os.path.basename(src), os.path.basename(dst), os.path.getsize(dst)))

print()
print('=== bundle manifest (path | bytes | sha256) ===')
for fn in sorted(os.listdir(DST)):
    p = os.path.join(DST, fn)
    if os.path.isfile(p):
        b = open(p, 'rb').read()
        print('%s | %d | %s' % (fn, len(b), hashlib.sha256(b).hexdigest()))
