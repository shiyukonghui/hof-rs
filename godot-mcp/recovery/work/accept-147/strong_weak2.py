import io, json, sys
sys.stdout.reconfigure(encoding='utf-8')
cov = {t['tool']: t for t in json.load(io.open('coverage.json', encoding='utf-8'))['tools']}
probe = json.load(io.open('recovery/work/task143/probe-live.json', encoding='utf-8'))['tools']
strong = [n for n, t in cov.items() if (t.get('boundary') or 0) >= 1]
tb = [n for n, r in probe.items() if r.get('verdict') == 'refused_-32602'
      and (r['error_message'].startswith('Missing required parameter:')
           or ("must be" in r['error_message'] and r['error_message'].startswith("Parameter '")))]
print("tools with boundary>=1                       : %d" % len(strong))
print("tools with handler-side -32602 (tool_builder): %d" % len(tb))
print("tools with a failed trace call               : 172 (swept)")
print("union estimate 172 | tb | boundary            : %d"
      % len(set(tb) | set(strong) | set(
          n for n in cov if cov[n]['verdicts'].get('failed'))))
missing = [n for n in cov if not (cov[n]['verdicts'].get('failed') or n in tb or (cov[n].get('boundary') or 0) >= 1)]
print("tools with NO failed call / no handler probe / boundary 0: %d -> %s" % (len(missing), missing))
print()
print("live probes refused_-32602 (task143)         : %d" % sum(1 for r in probe.values() if r.get('verdict') == 'refused_-32602'))
u2 = json.load(io.open('recovery/work/task144/probe-u2.json', encoding='utf-8'))
print("live probes refused_-32602 (task144 u2)      : %d" % len(u2['tools']))
print("total live -32602 observations               : %d (matrix says 144)"
      % (sum(1 for r in probe.values() if r.get('verdict') == 'refused_-32602') + len(u2['tools'])))
print()
import collections
sc = collections.Counter(t['status'] for t in cov.values())
print("ledger status_counts:", dict(sc))
print("ledger JSON status_counts:", json.load(io.open('coverage.json', encoding='utf-8'))['status_counts'])
print()
print("tools with channel_evidence_ok=False: %d" % sum(1 for t in cov.values() if not t['channel_evidence_ok']))
