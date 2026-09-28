import io, json, re, sys, hashlib, os
sys.stdout.reconfigure(encoding='utf-8')
p = 'recovery/reports/ACCEPTANCE-TASK-147.md'
t = io.open(p, encoding='utf-8').read()
blocks = re.findall(r'```json\n(.*?)```', t, re.S)
print('json blocks:', len(blocks))
d = json.loads(blocks[-1])
print('verdict:', d['verdict'])
print('criteria:', len(d['criteria']), 'all pass:', all(c['pass'] for c in d['criteria']))
print('defects:', [(x['severity']) for x in d['defects']])
print('blockers:', [x for x in d['defects'] if x['severity'] == 'blocker'])
print('keys:', sorted(d.keys()))
print('report bytes:', len(t.encode('utf-8')))
print('\nfinal hashes:')
for f in ['recovery/TEST-CASES.md', 'tools/tests/test_matrix_self_consistency.py']:
    print('  %s %s' % (hashlib.sha256(io.open(f,'rb').read()).hexdigest(), f))
print('\nstray temp files:',
      [f for f in ['tools/tests/conftest.py', 'tools/tests/test_accept147_bypass_probe.py'] if os.path.exists(f)] or 'none')
