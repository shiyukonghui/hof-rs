# -*- coding: utf-8 -*-
"""Decode the build stderr log (OEM/GBK) into UTF-8 and extract the errors."""
import io, os, re, sys

SRC = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\logs\task082_build1.err.txt'
DST = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task082\task082_build1.err.utf8.txt'

raw = open(SRC, 'rb').read()
for enc in ('utf-8', 'cp936', 'cp1252', 'mbcs'):
    try:
        text = raw.decode(enc)
        used = enc
        break
    except Exception:
        continue
else:
    text = raw.decode('utf-8', 'replace')
    used = 'utf-8/replace'

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
print('decoded with %s, bytes=%d' % (used, len(raw)))
print('CR count=%d' % raw.count(b'\r'))
open(DST, 'w', encoding='utf-8', newline='\n').write(text)
print('written %s' % DST)
print('---- content ----')
print(text)
