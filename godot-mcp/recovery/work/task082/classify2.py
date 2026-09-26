# -*- coding: utf-8 -*-
"""Definitive truncation classes v2 (trailing line comment stripped before the tail test)."""
import os, re, sys

ROOT = r'H:\rebuild\godot\modules\mcp_server'
OUT = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task082\truncation-classes.txt'
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
lines = []
def w(s=''):
    lines.append(str(s))
    print(s)


def lex(txt):
    i, n = 0, len(txt)
    ob = cb = op = cp = 0
    unterm = False
    while i < n:
        c = txt[i]
        if c == 'R' and i + 1 < n and txt[i + 1] == '"':
            j = i + 2
            ds = j
            while j < n and txt[j] != '(':
                j += 1
            if j >= n:
                unterm = True
                break
            closer = ')' + txt[ds:j] + '"'
            k = txt.find(closer, j + 1)
            if k == -1:
                unterm = True
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
                unterm = True
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
                    unterm = True
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
    return ob - cb, op - cp, unterm


def tail_verdict(last):
    """Strip a trailing // comment, then require a real terminator."""
    body = re.sub(r'\s*//.*$', '', last).rstrip()
    if body == '':
        return False, '<empty after comment strip>'
    if body.endswith(('}', ';', '#endif', '*/', ')', ',')):
        return True, body
    return False, body


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
        bd, pd, unterm = lex(txt)
        ls = txt.split('\n')
        first = next((l.strip() for l in ls if l.strip()), '')
        last = next((l.strip() for l in reversed(ls) if l.strip()), '')
        tok, body = tail_verdict(last)
        head_ok = first.startswith(('/*', '#include', '#pragma', '#ifndef'))
        rows.append(dict(rel=rel, bytes=len(raw), lines=len(ls), bd=bd, pd=pd, unterm=unterm,
                         head_ok=head_ok, tail_ok=tok, first=first[:80], last=last[:80], body=body[:80]))

A = [r for r in rows if not r['head_ok']]
B = [r for r in rows if not r['tail_ok']]
C = [r for r in rows if r['unterm']]
D = [r for r in rows if r['head_ok'] and r['tail_ok'] and not r['unterm'] and (r['bd'] or r['pd'])]

w('scanned=%d' % len(rows))
w('')
w('## CLASS A - HEAD does not open with the Godot licence block  (head truncation, unambiguous): %d' % len(A))
for r in A:
    w('  %-42s %7d B %5d lines  first=%r' % (r['rel'], r['bytes'], r['lines'], r['first']))
w('')
w('## CLASS B - TAIL does not end in a C++ terminator (tail truncation, unambiguous): %d' % len(B))
for r in B:
    w('  %-42s %7d B %5d lines  bd=%-3d pd=%-3d  last=%r' % (r['rel'], r['bytes'], r['lines'], r['bd'], r['pd'], r['last']))
w('')
w('## CLASS C - unterminated string/comment found by the lexer (unambiguous): %d' % len(C))
for r in C:
    w('  %-42s %7d B  last=%r' % (r['rel'], r['bytes'], r['last']))
w('')
w('## CLASS D - well-formed ends but unbalanced braces/parens (interior damage SUSPECTED, needs review): %d' % len(D))
for r in D:
    w('  %-42s %7d B %5d lines  bd=%-4d pd=%-4d' % (r['rel'], r['bytes'], r['lines'], r['bd'], r['pd']))

union = sorted({r['rel'] for r in A + B + C + D})
w('')
w('## UNION (files carrying at least one structural red flag): %d of %d' % (len(union), len(rows)))
for rel in union:
    w('  %s' % rel)

w('')
w('## PROVEN damage (A + B + C), the list the fix plan must start from: %d' % len(sorted({r['rel'] for r in A + B + C})))
for rel in sorted({r['rel'] for r in A + B + C}):
    w('  %s' % rel)

open(OUT, 'w', encoding='utf-8').write('\n'.join(lines))
print('->', OUT)
