# -*- coding: utf-8 -*-
"""TASK-082 item 4 recon v2: C++-aware structural scan (comments, raw strings, chars)."""
import os, re, sys

ROOT = r'H:\rebuild\godot\modules\mcp_server'
OUT = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task082\damage-scan2.txt'
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
lines = []
def w(s=''):
    lines.append(str(s))
    print(s)


def lex_balance(txt):
    """Return (brace_delta, paren_delta, n_raw_strings, unterminated_flag)."""
    i = 0
    n = len(txt)
    ob = cb = op = cp = 0
    nraw = 0
    unterminated = False
    while i < n:
        c = txt[i]
        # raw string literal: R"delim( ... )delim"
        if c == 'R' and i + 1 < n and txt[i + 1] == '"':
            j = i + 2
            delim_start = j
            while j < n and txt[j] != '(':
                j += 1
            if j >= n:
                unterminated = True
                break
            delim = txt[delim_start:j]
            closer = ')' + delim + '"'
            k = txt.find(closer, j + 1)
            if k == -1:
                unterminated = True
                break
            nraw += 1
            i = k + len(closer)
            continue
        if c == '/' and i + 1 < n and txt[i + 1] == '/':
            k = txt.find('\n', i)
            i = n if k == -1 else k
            continue
        if c == '/' and i + 1 < n and txt[i + 1] == '*':
            k = txt.find('*/', i + 2)
            if k == -1:
                unterminated = True
                break
            i = k + 2
            continue
        if c == '"':
            i += 1
            while i < n:
                if txt[i] == '\\':
                    i += 2
                    continue
                if txt[i] == '"':
                    break
                if txt[i] == '\n':
                    unterminated = True
                    break
                i += 1
            i += 1
            continue
        if c == "'":
            i += 1
            while i < n:
                if txt[i] == '\\':
                    i += 2
                    continue
                if txt[i] == "'":
                    break
                i += 1
            i += 1
            continue
        if c == '{':
            ob += 1
        elif c == '}':
            cb += 1
        elif c == '(':
            op += 1
        elif c == ')':
            cp += 1
        i += 1
    return ob - cb, op - cp, nraw, unterminated


TAIL_OK = re.compile(r'^(\}\s*(//.*)?|\}\s*;|\#endif.*|\#pragma.*|\}\s*\w+\s*\}\s*(//.*)?)$')

rows = []
for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in ('__pycache__', '.git')]
    for fn in sorted(filenames):
        if not fn.endswith(('.cpp', '.h')):
            continue
        p = os.path.join(dirpath, fn)
        rel = os.path.relpath(p, ROOT).replace('\\', '/')
        raw = open(p, 'rb').read()
        txt = raw.decode('utf-8', 'replace')
        bd, pd, nraw, unterm = lex_balance(txt)
        ls = txt.split('\n')
        first = next((l.strip() for l in ls if l.strip()), '')
        last = next((l.strip() for l in reversed(ls) if l.strip()), '')
        head_ok = first.startswith(('/*', '#include', '#pragma', '#ifndef'))
        tail_ok = bool(TAIL_OK.match(last))
        rows.append(dict(rel=rel, bytes=len(raw), lines=len(ls), bd=bd, pd=pd, nraw=nraw,
                         unterm=unterm, head_ok=head_ok, tail_ok=tail_ok,
                         first=first[:80], last=last[:80]))

w('scanned=%d' % len(rows))
w('')
w('=== A. HEAD does not start with license/include/pragma (unambiguous head truncation) ===')
for r in rows:
    if not r['head_ok']:
        w('  %-46s %7d B  first=%r' % (r['rel'], r['bytes'], r['first']))

w('')
w('=== B. lexer found an UNTERMINATED literal/comment (unambiguous truncation) ===')
for r in rows:
    if r['unterm']:
        w('  %-46s %7d B  last=%r' % (r['rel'], r['bytes'], r['last']))

w('')
w('=== C. TAIL is not a balanced closer (unambiguous tail truncation) ===')
for r in rows:
    if not r['tail_ok']:
        w('  %-46s %7d B  bd=%-4d pd=%-4d last=%r' % (r['rel'], r['bytes'], r['bd'], r['pd'], r['last']))

w('')
w('=== D. balanced tail but brace/paren delta != 0 (interior block dropped) ===')
for r in rows:
    if r['tail_ok'] and r['head_ok'] and (r['bd'] != 0 or r['pd'] != 0):
        w('  %-46s %7d B  bd=%-4d pd=%-4d' % (r['rel'], r['bytes'], r['bd'], r['pd']))

w('')
w('=== E. summary ===')
w('  head-bad   : %d' % sum(1 for r in rows if not r['head_ok']))
w('  unterminated: %d' % sum(1 for r in rows if r['unterm']))
w('  tail-bad   : %d' % sum(1 for r in rows if not r['tail_ok']))
w('  delta-only : %d' % sum(1 for r in rows if r['tail_ok'] and r['head_ok'] and (r['bd'] or r['pd'])))
w('  fully clean: %d' % sum(1 for r in rows if r['head_ok'] and r['tail_ok'] and not r['unterm'] and not r['bd'] and not r['pd']))

open(OUT, 'w', encoding='utf-8').write('\n'.join(lines))
print('->', OUT)
