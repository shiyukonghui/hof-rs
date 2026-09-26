# TASK-078 audit: inspect reconstruction records for the reconciliation-critical paths.
import json, os, sys, re

W = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work'
recs = []
with open(os.path.join(W, 'reconstruction.jsonl'), 'r', encoding='utf-8') as f:
    for line in f:
        recs.append(json.loads(line))

WANT = ['project_settings.cpp', 'project_settings.h', 'editor_node.cpp', 'csharp_script.cpp', 'csharp_script.h',
        'gen_renamed_contract.py', 'tools_list.renamed.json', 'check_engine_anchor.ps1', 'mcp_evidence_guard.ps1',
        'mcp_watch_run.ps1', 'check_exit_propagation.py', 'check_tautologies.py', 'check_hardcoded_counts.py',
        'accept_m1.ps1', 'DECISIONS.md']
for w in WANT:
    hits = [r for r in recs if r['path'].lower().endswith(w)]
    for h in hits:
        print('%-26s conf=%-5s bytes=%-8s miss=%-13s missN=%-5s nW=%d nE=%d nR=%d vers=%d fails=%d' %
              (w, h['conf'], h['bytes'], str(h['miss_tail']), str(h['read_missing_n']),
               h['n_write'], h['n_edit'], h['n_read'], h['versions'], h['n_failed']))
        if h['notes']:
            print('     notes:', '; '.join(h['notes'])[:300])
        if h['failed']:
            print('     failed:', h['failed'][:5])
        if h['last_src']:
            print('     last:', h['last_src'])
    if not hits:
        print('%-26s NOT PRESENT' % w)

print()
print('=== in-repo files with failed edits (top by edit count) ===')
bad = [r for r in recs if r['n_failed'] and r['path'].lower().startswith('f:\\rustprojects\\godot-mcp-pro\\code\\godot\\')]
bad.sort(key=lambda r: -r['n_edit'])
for r in bad[:30]:
    print('%-3d fail=%-3d bytes=%-8s conf=%-5s %s' % (r['n_edit'], r['n_failed'], r['bytes'], r['conf'], r['path'][len('F:\\RustProjects\\godot-mcp-pro\\code\\godot\\'):]))
print('in-repo paths with failed edits =', len(bad))
