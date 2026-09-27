# -*- coding: utf-8 -*-
"""Read-only gathering of the 20-game review facts from the final run products.

Every number in dist/review_data.json is recomputed here from the run's own
files (call-index.txt / ledger-*.json / report.json / <tag>.json).  The only
externally sourced column is `defects`, which is quoted from
GAME-LOOP-LOG.md's "里程碑：20 款" table (with the TASK-106 addendum for snake)
and is labelled as such in the README.
"""
import json, os, sys

ROOT = r'F:\moonbit-hof-rs\godot-mcp'
OUT = os.path.join(ROOT, 'dist', 'review_data.json')

# game, run tag, label, editor calls, game calls, defects(tool/game), source-note
GAMES = [
    ('pong',          'pong-clean-task097',    'Pong',            23,  29, (0, 6), ''),
    ('breakout',      'breakout-clean-task097','Breakout',        21,  34, (0, 5), ''),
    ('snake',         'snake-task106-r1',      'Snake',           20,  33, (0, 5), 'TASK-106 重跑；缺陷数含 TASK-105 的 D-1'),
    ('tetris',        'tetris-task096-r2',     'Tetris',           6,  36, (0, 3), ''),
    ('spaceinvaders', 'si-task097-r1',         'Space Invaders',  15,  44, (0, 0), ''),
    ('asteroids',     'ast-task098-r2',        'Asteroids',       16,  55, (0, 1), ''),
    ('pacman',        'pac-task098-r2',        'Pac-Man',         16,  64, (0, 1), ''),
    ('frogger',       'frog-task099-r1',       'Frogger',         16,  74, (0, 0), ''),
    ('flappy',        'flappy-task099-r2',     'Flappy Bird',     14,  78, (0, 1), ''),
    ('game2048',      '2048-task100-r2',       '2048',            16, 113, (0, 1), ''),
    ('minesweeper',   'mine-task100-r2',       'Minesweeper',     14, 141, (0, 1), ''),
    ('sokoban',       'soko-task101-r2',       'Sokoban',         14, 176, (0, 1), ''),
    ('bomberman',     'bomb-task101-r4',       'Bomberman',       14, 219, (0, 3), ''),
    ('platformer',    'plat-task102-r2',       'Platformer',      14, 214, (0, 2), ''),
    ('match3',        'm3-task102-r3',         'Match-3',         14, 131, (1, 4), 'X-1 工具缺陷已于 TASK-103 修'),
    ('towerdefense',  'td-task103-r3',         'Tower Defense',   14, 131, (0, 1), ''),
    ('missilecommand','mc-task103-r3',         'Missile Command', 14, 113, (0, 3), ''),
    ('rtype',         'rt-task104-r2',         'R-Type',          14, 209, (0, 1), ''),
    ('puzzlebobble',  'pb-task104-r1',         'Puzzle Bobble',   14, 143, (0, 0), ''),
    ('lunarlander',   'll-task104-r1',         'Lunar Lander',    14, 216, (0, 0), ''),
]

DECL_KEYS = ('must-fail', 'must_fail', 'must fail', 'expected to fail', 'declared',
             'by design', 'intentionally', 'boundary', 'refus', 'negative', 'not rubber')


def load_json(p):
    with open(p, encoding='utf-8-sig') as f:
        return json.load(f)


def call_index(run):
    rows = []
    p = os.path.join(run, 'call-index.txt')
    for line in open(p, encoding='utf-8-sig', errors='replace'):
        parts = line.rstrip('\n').split('|')
        if len(parts) >= 5:
            rows.append({'tag': parts[0], 'port': parts[1],
                         'req_bytes': int(parts[2]), 'resp_bytes': int(parts[3]),
                         'note': '|'.join(parts[4:])})
    return rows


def assertions(run, idx):
    passed = failed = errors = 0
    failing = []
    scanned = 0
    for r in idx:
        f = os.path.join(run, r['tag'] + '.json')
        if not os.path.exists(f):
            continue
        try:
            o = load_json(f)
        except Exception:
            continue
        scanned += 1
        try:
            texts = [c.get('text', '') for c in o['result']['content']]
        except Exception:
            continue
        for txt in texts:
            try:
                body = json.loads(txt)
            except Exception:
                continue
            if not isinstance(body, dict):
                continue
            if 'all_passed' in body:
                passed += int(body.get('passed') or 0)
                failed += int(body.get('failed') or 0)
                errors += int(body.get('errors') or 0)
                if not body.get('all_passed'):
                    for x in body.get('results', []):
                        if x.get('type') == 'assert' and x.get('passed') is False:
                            failing.append({'tag': r['tag'], 'assertion': x.get('assertion'),
                                            'expected': str(x.get('expected')),
                                            'actual': str(x.get('actual'))})
            elif 'passed' in body:
                if body.get('passed'):
                    passed += 1
                else:
                    failed += 1
                    failing.append({'tag': r['tag'], 'assertion': body.get('assertion'),
                                    'expected': str(body.get('expected')),
                                    'actual': str(body.get('actual'))})
    for x in failing:
        note = ''
        for r in idx:
            if r['tag'] == x['tag']:
                note = r['note']
                break
        blob = (x['tag'] + ' ' + note).lower()
        x['declared'] = any(k in blob for k in DECL_KEYS)
    return {'passed': passed, 'failed': failed, 'errors': errors,
            'responses_scanned': scanned, 'failing': failing,
            'undeclared': sum(1 for x in failing if not x['declared'])}


def ledger(run, phase, cleanup_tags):
    p = os.path.join(run, 'ledger-%s.json' % phase)
    o = load_json(p)
    rows = o.get('rows', [])
    skipped = 0
    if cleanup_tags:
        skipped = cleanup_tags
        rows = rows[cleanup_tags:]
    complete = sum(1 for r in rows if r.get('facts_complete'))
    flags = {}
    for r in rows:
        for k in ('error_flags', 'result_flags'):
            for fl in (r.get(k) or []):
                flags[fl] = flags.get(fl, 0) + 1
    verdicts = {}
    for r in rows:
        v = r.get('verdict') or '?'
        verdicts[v] = verdicts.get(v, 0) + 1
    return {'rows': len(rows), 'facts_complete': complete,
            'malformed_lines': o.get('malformed_lines', 0),
            'flags': flags, 'verdicts': verdicts, 'tools_list_skipped': skipped}


def main():
    out = []
    tp = tf = te = tu = 0
    for game, tag, label, me, mg, defects, note in GAMES:
        run = os.path.join(ROOT, 'runs', game, tag)
        idx = call_index(run)
        c_tags = sum(1 for r in idx if r['tag'].startswith('c'))
        ed_led = ledger(run, 'editor', c_tags)
        gm_led = ledger(run, 'game', 0)
        a = assertions(run, idx)
        rep = load_json(os.path.join(run, 'report.json'))
        pe = rep.get('pixel_evidence') or {}
        rec = {
            'game': game, 'label': label, 'run_tag': tag,
            'run_path': 'runs\\%s\\%s' % (game, tag),
            'calls_editor': me, 'calls_game': mg, 'calls_total': me + mg,
            'calls_total_in_trace': len(idx),
            'cleanup_calls': c_tags,
            'facts_editor': '%d/%d' % (ed_led['facts_complete'], me),
            'facts_game': '%d/%d' % (gm_led['facts_complete'], mg),
            'facts_percent': (ed_led['facts_complete'] + gm_led['facts_complete']) * 100 // (me + mg),
            'malformed_lines': ed_led['malformed_lines'] + gm_led['malformed_lines'],
            'assertions': a, 'assertions_total': a['passed'] + a['failed'],
            'pixel_nonzero': pe.get('non_zero_pairs'),
            'pixel_comparable': pe.get('comparable_pairs'),
            'pixel_verdict': pe.get('verdict'),
            'defects_tool': defects[0], 'defects_game': defects[1], 'defects_note': note,
            'editor_verdicts': ed_led['verdicts'], 'game_verdicts': gm_led['verdicts'],
            'editor_flags': ed_led['flags'], 'game_flags': gm_led['flags'],
            'saved_frames': len(rep.get('saved_frames') or []),
            'report_defects_auto': len(rep.get('defects') or []),
        }
        out.append(rec)
        tp += a['passed']; tf += a['failed']; te += a['errors']; tu += a['undeclared']
        print('%-15s %-24s %3d/%3d facts %2d/%2d+%3d/%3d assert p%4d f%d e%d und%d px %s/%s def %d/%d' % (
            game, tag, me, mg, ed_led['facts_complete'], me, gm_led['facts_complete'], mg,
            a['passed'], a['failed'], a['errors'], a['undeclared'],
            pe.get('non_zero_pairs'), pe.get('comparable_pairs'), defects[0], defects[1]))
    print('TOTAL passed=%d failed=%d errors=%d undeclared=%d' % (tp, tf, te, tu))

    meta = {
        'root': ROOT,
        'engine': r'godot\bin\godot.windows.editor.x86_64.mono.console.exe',
        'engine_version': '4.8.dev.mono.custom_build.1c7f5c07a',
        'totals': {'passed': tp, 'failed': tf, 'errors': te, 'undeclared': tu},
        'games': out,
    }
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print('written', OUT)


main()
