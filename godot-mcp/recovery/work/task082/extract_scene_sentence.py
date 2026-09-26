# -*- coding: utf-8 -*-
"""TASK-082 item 3e: pull the get_scene_tree description verbatim out of REPORT-076."""
import hashlib, io, json, os

RPT = r'H:\rebuild\godot\modules\mcp_server\docs\reports\REPORT-076-small-items.md'
OUT = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task082\task076-scene-tree.txt'
lines = []
def w(s=''):
    lines.append(str(s))

tl = open(RPT, 'rb').read().decode('utf-8').split('\n')
w('report lines=%d' % len(tl))

# blockquote paragraphs: line starts with '> ' and holds the new description
cand = []
i = 0
while i < len(tl):
    s = tl[i].lstrip()
    if s.startswith('> 获取当前编辑场景的完整场景树'):
        cand.append(i + 1)
    i += 1
w('candidate blockquote lines: %s' % cand)

for ln in cand:
    text = tl[ln - 1].lstrip()
    text = text[1:].lstrip()          # drop '>' and one space
    b = text.encode('utf-8')
    w('')
    w('line %d: total bytes=%d' % (ln, len(b)))
    w('  repr-first-80=%r' % text[:80])
    w('  repr-last-60=%r' % text[-60:])
    orig = '获取当前编辑场景的完整场景树'
    w('  startswith(orig + " ") = %s' % text.startswith(orig + ' '))
    sentence = text[len(orig) + 1:]
    w('  derived SCENE_TREE_ADDRESSABILITY_SENTENCE bytes=%d' % len(sentence.encode('utf-8')))
    w('  sentence starts=%r' % sentence[:60])
    w('  sentence ends  =%r' % sentence[-60:])
    w('  EXPECTED total = 898 -> got %d -> %s' % (len(b), 'MATCH' if len(b) == 898 else 'MISMATCH'))
    w('  ---FULL---')
    w(text)
    open(OUT, 'w', encoding='utf-8').write('\n'.join(lines + [text]))
print('written', OUT)
