import io, json, collections
d = json.load(io.open('recovery/work/task143/probe-live.json', encoding='utf-8'))
tools = d['tools']
kinds = collections.Counter()
per = collections.defaultdict(list)
for name, rec in sorted(tools.items()):
    if not isinstance(rec, dict):
        continue
    if any(k not in rec for k in ('code',)):
        pass
    code = rec.get('code', rec.get('error_code'))
    msg = rec.get('message', rec.get('error_message')) or ''
    if code != -32602:
        continue
    if msg.startswith('Missing required parameter:'):
        k = 'missing_required'
    elif msg.startswith("Parameter '") and 'must be' in msg:
        k = 'wrong_type'
    elif msg.startswith('Unknown parameter'):
        k = 'unknown_parameter'
    else:
        k = 'other'
    kinds[k] += 1
    per[k].append((name, msg[:70]))
print('keys of a probed record:', sorted(list(tools['project_get_filesystem_tree'].keys())))
print()
for k, v in kinds.most_common():
    print('%-20s %d' % (k, v))
print()
for k in sorted(per):
    print('--', k)
    for n, m in per[k][:6]:
        print('   ', n, '|', m)
