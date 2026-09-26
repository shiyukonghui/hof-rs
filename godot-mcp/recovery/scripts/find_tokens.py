# TASK-078 evidence search: literal-token sweep over the raw transcripts (read-only).
import json, glob, os, re, sys

T = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\transcripts'
PATS = [
    ('added_count', re.compile(r'.{0,90}added_count.{0,90}')),
    ('count177', re.compile(r'.{0,60}(?:"count"|\bcount\b)\s*[:=]?\s*177.{0,60}')),
    ('genver122', re.compile(r'.{0,60}1\.22\.0.{0,60}')),
    ('meta177', re.compile(r'.{0,80}177.{0,40}added.{0,60}')),
]
MAXPER = 12
counts = {k: 0 for k, _ in PATS}
shown = {k: 0 for k, _ in PATS}
files = sorted(glob.glob(os.path.join(T, '*.jsonl')))
for f in files:
    base = os.path.basename(f)
    with open(f, 'r', encoding='utf-8', errors='replace') as fh:
        for line in fh:
            if '"added_count"' not in line and 'added_count' not in line and '1.22.0' not in line and '177' not in line:
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue
            blob = line
            for name, pat in PATS:
                for m in pat.finditer(blob):
                    counts[name] += 1
                    if shown[name] < MAXPER:
                        shown[name] += 1
                        s = m.group(0).replace('\\n', ' ').replace('\\"', '"')
                        print('[%s] %s t=%s seq=%s type=%s :: %s' % (name, base[:20], d.get('time'), d.get('seq'), d.get('type'), s[:200]))
    if len(sys.argv) > 1 and sys.argv[1] == 'verbose':
        pass
print('--- counts (occurrences) ---')
for k in counts:
    print('%-12s %d' % (k, counts[k]))
