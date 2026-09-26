# -*- coding: utf-8 -*-
"""Definitive truncation classes for the module sources (self-contained)."""
import os, re, sys

ROOT = r'H:\rebuild\godot\modules\mcp_server'
OUT = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task082\truncation-classes.txt'
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
lines = []
def w(s=''):
    lines.append(str(s))
    print(s)


def lex_balance(txt):
    i, n = 0, len(txt)
    ob = cb = op = cp = 0
    unterminated = False
    while i < n:
        c = txt[i]
        if c == 'R' and i + 1 < n and txt[i + 1] == '"':
            j = i + 2
            ds = j
            while j < n and txt[j] != '(':
                j += 1
            if j >= n:
                unterminated = True
                break
            closer = ')' + txt[ds:j] + '"'
            k = txt.find(closer, j + 1)
            if k == -1:
                unterminated = True
                break
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
    return ob - cb, op - cp, unterminated


GOOD_TAIL = ('}', ';', '#endif', '*/', ')', ',')

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
        bd, pd, unterm = lex_balance(txt)
        ls = txt.split('\n')
        first = next((l.strip() for l in ls if l.strip()), '')
        last = next((l.strip() for l in reversed(ls) if l.strip()), '')
        head_ok = first.startswith(('/*', '#include', '#pragma', '#ifndef'))
        tail_ok = last.endswith(GOOD_TAIL) or last.endswith('#endif')
        rows.append(dict(rel=rel, bytes=len(raw), lines=len(ls), bd=bd, pd=pd,
                         unterm=unterm, head_ok=head_ok, tail_ok=tail_ok,
                         first=first[:80], last=last[:80]))

c1 = [r for r in rows if not r['head_ok']]
c2 = [r for r in rows if not r['tail_ok']]
c3 = [r for r in rows if r['head_ok'] and r['tail_ok'] and not r['unterm'] and (r['bd'] or r['pd'])]
c4 = [r for r in rows if r['unterm']]

w('scanned=%d' % len(rows))
w('')
w('CLASS 1 - head does not begin with the Godot licence block (head truncation): %d' % len(c1))
for r in c1:
    w('  %-44s %7d B  %3d lines  first=%r' % (r['rel'], r['bytes'], r['lines'], r['first']))
w('')
w('CLASS 2 - last non-blank line ends in neither } ; #endif */ ) , (tail truncation): %d' % len(c2))
for r in c2:
    w('  %-44s %7d B  %3d lines  bd=%-3d pd=%-3d last=%r' % (r['rel'], r['bytes'], r['lines'], r['bd'], r['pd'], r['last']))
w('')
w('CLASS 3 - unterminated string/comment (lexer could not close it): %d' % len(c4))
for r in c4:
    w('  %-44s %7d B  last=%r' % (r['rel'], r['bytes'], r['last']))
w('')
w('CLASS 4 - well-formed ends but unbalanced braces/parens (interior block suspect): %d' % len(c3))
for r in c3:
    w('  %-44s %7d B  %3d lines  bd=%-4d pd=%-4d' % (r['rel'], r['bytes'], r['lines'], r['bd'], r['pd']))

w('')
w('UNION of all four classes: %d files' % len({r['rel'] for r in c1 + c2 + c3 + c4}))
for rel in sorted({r['rel'] for r in c1 + c2 + c3 + c4}):
    w('  %s' % rel)

open(OUT, 'w', encoding='utf-8').write('\n'.join(lines))
print('->', OUT)
