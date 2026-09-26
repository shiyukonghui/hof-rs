# TASK-078: compare the captured modules\mcp_server listing with the staged set.
import json, os, re, collections

ROOT = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery'
W = os.path.join(ROOT, 'work')
raw = open(os.path.join(W, 'module-listing-raw.txt'), encoding='utf-8').read()
listing = set()
for ln in raw.split('\n'):
    ln = ln.strip().strip('"')
    if not ln or ln.startswith('===') or ln.startswith('---') or ' ' in ln:
        continue
    if re.match(r'^[\w.\\/-]+$', ln):
        listing.add(('modules\\mcp_server\\' + ln).lower())
print('entries parsed from the captured listing: %d' % len(listing))
recs = [json.loads(l) for l in open(os.path.join(W, 'reconstruction.jsonl'), encoding='utf-8')]
staged = set(r['rel'].lower() for r in recs if r['rel'].lower().startswith('modules\\mcp_server'))
print('staged modules\\mcp_server entries: %d' % len(staged))
missing = sorted(listing - staged)
extra = sorted(staged - listing)
print('listed but NOT staged: %d' % len(missing))
print('staged but not in that listing: %d' % len(extra))
cat = collections.Counter()
for p in missing:
    parts = p.split('\\')
    cat['\\'.join(parts[2:4]) if len(parts) > 3 else '\\'.join(parts[2:])] += 1
print('missing by subdir:')
for k, v in cat.most_common(20):
    print('  %5d %s' % (v, k))
with open(os.path.join(W, 'module-listing-missing.txt'), 'w', encoding='utf-8', newline='\n') as g:
    g.write('\n'.join(missing))
print('first 25 missing:')
for p in missing[:25]:
    print('  -', p)
