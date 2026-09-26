# TASK-078: objective syntax check of .py candidates (staged vs preserved alternative).
import ast, json, os, collections

ST = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging'
W = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work'

def parses(p):
    try:
        src = open(p, 'r', encoding='utf-8').read()
    except Exception as e:
        return 'read-error:%s' % e
    try:
        ast.parse(src)
        return 'ok'
    except SyntaxError as e:
        return 'syntax-error:%s' % e.msg
    except Exception as e:
        return 'error:%s' % e

res = collections.Counter()
bad = []
for r in (json.loads(l) for l in open(os.path.join(W, 'reconstruction.jsonl'), encoding='utf-8')):
    rel = r['rel']
    if not rel.lower().endswith('.py'):
        continue
    main = os.path.join(ST, rel)
    a = parses(main) if os.path.exists(main) else 'missing'
    alt = None
    for tag in ('write-chain', 'read-epoch'):
        cand = os.path.join(ST, '__candidates', rel + '.' + tag + '.txt')
        if os.path.exists(cand):
            alt = (tag, parses(cand))
    res[a.split(':')[0]] += 1
    if a != 'ok':
        bad.append((rel, r['chosen'], r['conf'], a, alt))
print('py staged parse:', dict(res))
print('--- non-ok .py staged (top 40, in-repo first) ---')
bad.sort(key=lambda x: (not x[0].lower().startswith('modules'), -1))
for b in bad[:40]:
    print('%-70s chosen=%-12s conf=%-4s %-45s alt=%s' % (b[0][:70], b[1], b[2], b[3][:45], b[4]))
print('total non-ok py =', len(bad))
