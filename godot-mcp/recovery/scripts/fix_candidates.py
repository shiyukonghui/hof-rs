# TASK-078: post-fix - swap in the alternative candidate when it is objectively better.
#   .py : ast.parse  (staged fails, alternative parses  ->  swap)
# Records the swap in work\swaps.json (read by the manifest builder).
import ast, json, os

ROOT = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery'
ST = os.path.join(ROOT, 'staging')
W = os.path.join(ROOT, 'work')
REC = os.path.join(W, 'reconstruction.jsonl')

def parses(p):
    try:
        ast.parse(open(p, 'r', encoding='utf-8').read())
        return True
    except Exception:
        return False

recs = [json.loads(l) for l in open(REC, encoding='utf-8')]
swaps = []
for r in recs:
    if not r['rel'].lower().endswith('.py') or not r['wrote']:
        continue
    main = os.path.join(ST, r['rel'])
    if not os.path.exists(main) or parses(main):
        continue
    for tag in ('write-chain', 'read-epoch'):
        cand = os.path.join(ST, '__candidates', r['rel'] + '.' + tag + '.txt')
        if os.path.exists(cand) and parses(cand):
            data = open(cand, 'r', encoding='utf-8').read()
            with open(main, 'w', encoding='utf-8', newline='') as f:
                f.write(data)
            r['notes'].append('SWAPPED_BY_SYNTAX_CHECK(staged failed ast.parse; %s parses)' % tag)
            r['chosen_original'] = r['chosen']
            r['chosen'] = tag + '+syntax-fix'
            r['conf'] = 'mid' if r['n_write'] == 0 else 'mid'
            r['bytes'] = len(data.encode('utf-8'))
            swaps.append({'rel': r['rel'], 'from': r['chosen_original'], 'to': tag, 'bytes': r['bytes']})
            break

with open(REC, 'w', encoding='utf-8', newline='\n') as f:
    for r in recs:
        f.write(json.dumps(r, ensure_ascii=False) + '\n')
with open(os.path.join(W, 'swaps.json'), 'w', encoding='utf-8', newline='\n') as f:
    json.dump(swaps, f, ensure_ascii=False, indent=1)

still = [r['rel'] for r in recs if r['rel'].lower().endswith('.py') and r['wrote'] and not parses(os.path.join(ST, r['rel']))]
print('swapped:', len(swaps))
for s in swaps:
    print(' ', s['rel'], s['from'], '->', s['to'])
print('still non-parsing .py:', still)
