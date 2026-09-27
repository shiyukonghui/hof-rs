# -*- coding: utf-8 -*-
"""Read-only probe: recompute per-game facts from the final run products."""
import json, os, sys, glob, hashlib

ROOT = r'F:\moonbit-hof-rs\godot-mcp'

FINALS = [
    ('pong',          'pong-clean-task097',   'Pong'),
    ('breakout',      'breakout-clean-task097','Breakout'),
    ('snake',         'snake-task106-r1',     'Snake'),
    ('tetris',        'tetris-task096-r2',    'Tetris'),
    ('spaceinvaders', 'si-task097-r1',        'Space Invaders'),
    ('asteroids',     'ast-task098-r2',       'Asteroids'),
    ('pacman',        'pac-task098-r2',       'Pac-Man'),
    ('frogger',       'frog-task099-r1',      'Frogger'),
    ('flappy',        'flappy-task099-r2',    'Flappy Bird'),
    ('game2048',      '2048-task100-r2',      '2048'),
    ('minesweeper',   'mine-task100-r2',      'Minesweeper'),
    ('sokoban',       'soko-task101-r2',      'Sokoban'),
    ('bomberman',     'bomb-task101-r4',      'Bomberman'),
    ('platformer',    'plat-task102-r2',      'Platformer'),
    ('match3',        'm3-task102-r3',        'Match-3'),
    ('towerdefense',  'td-task103-r3',        'Tower Defense'),
    ('missilecommand','mc-task103-r3',        'Missile Command'),
    ('rtype',         'rt-task104-r2',        'R-Type'),
    ('puzzlebobble',  'pb-task104-r1',        'Puzzle Bobble'),
    ('lunarlander',   'll-task104-r1',        'Lunar Lander'),
]

DECL_KEYS = ('must-fail', 'must_fail', 'expected to fail', 'declared',
             'by design', 'intentionally', 'boundary', 'refus', 'negative')


def load_json(p):
    for enc in ('utf-8-sig', 'utf-8'):
        try:
            with open(p, encoding=enc) as f:
                return json.load(f)
        except UnicodeDecodeError:
            continue
    raise ValueError('cannot decode ' + p)


def parse_call_index(run):
    p = os.path.join(run, 'call-index.txt')
    rows = []
    if not os.path.exists(p):
        return rows
    for line in open(p, encoding='utf-8-sig', errors='replace'):
        parts = line.rstrip('\n').split('|')
        if len(parts) < 5:
            continue
        rows.append({'tag': parts[0], 'port': parts[1], 'req_bytes': parts[2],
                     'resp_bytes': parts[3], 'note': '|'.join(parts[4:])})
    return rows


def scan_assertions(run, tags):
    """Mirror the report layer: count from the run's own saved responses."""
    passed = failed = errors = 0
    failing = []
    scanned = 0
    for t in tags:
        f = os.path.join(run, t + '.json')
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
                passed += int(body.get('passed', 0) or 0)
                failed += int(body.get('failed', 0) or 0)
                errors += int(body.get('errors', 0) or 0)
                if not body.get('all_passed'):
                    for r in body.get('results', []):
                        if r.get('type') == 'assert' and r.get('passed') is False:
                            failing.append((t, r.get('assertion', '?'),
                                            str(r.get('expected'))[:60],
                                            str(r.get('actual'))[:60]))
            elif 'passed' in body:
                if body.get('passed'):
                    passed += 1
                else:
                    failed += 1
                    failing.append((t, body.get('assertion', '?'),
                                    str(body.get('expected'))[:60],
                                    str(body.get('actual'))[:60]))
    return passed, failed, errors, failing, scanned


def ledger_stats(run, phase):
    p = os.path.join(run, 'ledger-%s.json' % phase)
    if not os.path.exists(p):
        return None
    o = load_json(p)
    rows = o.get('rows', [])
    complete = 0
    flags = {}
    for r in rows:
        fc = r.get('facts_complete')
        if fc is None:
            fc = all(r.get('facts', {}).values()) if r.get('facts') else False
        if fc:
            complete += 1
        for fl in (r.get('error_flags') or []):
            flags[fl] = flags.get(fl, 0) + 1
        for fl in (r.get('flags') or []):
            flags[fl] = flags.get(fl, 0) + 1
    return {'calls': len(rows), 'malformed': o.get('malformed_lines', 0),
            'facts_complete': complete, 'flags': flags}


def report_stats(run):
    p = os.path.join(run, 'report.json')
    if not os.path.exists(p):
        return None
    o = load_json(p)
    pe = o.get('pixel_evidence') or {}
    return {'pixel': pe, 'defects': o.get('defects'),
            'defects_manual': o.get('defects_manual'),
            'assertions': o.get('assertions'),
            'saved_frames': len(o.get('saved_frames') or [])}


def shots(run):
    out = {}
    for phase in ('editor', 'game'):
        d = os.path.join(run, 'shots-%s' % phase)
        if os.path.isdir(d):
            out[phase] = sorted(f for f in os.listdir(d) if f.lower().endswith('.png'))
        else:
            out[phase] = []
    return out


def main():
    result = []
    for game, tag, label in FINALS:
        run = os.path.join(ROOT, 'runs', game, tag)
        rec = {'game': game, 'label': label, 'tag': tag,
               'run': 'runs\\%s\\%s' % (game, tag), 'exists': os.path.isdir(run)}
        if not rec['exists']:
            result.append(rec)
            continue
        idx = parse_call_index(run)
        tags = [r['tag'] for r in idx]
        rec['calls_total'] = len(idx)
        rec['calls_editor'] = sum(1 for r in idx if r['port'] == 'editor')
        rec['calls_game'] = sum(1 for r in idx if r['port'] == 'game')
        p, f, e, failing, scanned = scan_assertions(run, tags)
        rec['assertions'] = {'passed': p, 'failed': f, 'errors': e,
                             'responses_scanned': scanned}
        rec['failing'] = [{'tag': t, 'what': w, 'expected': ex, 'actual': ac,
                           'declared': any(k in t.lower() for k in ('must-fail', 'must_fail'))
                           or any(k in (dict((r['tag'], r['note']) for r in idx).get(t, '') or '').lower()
                                  for k in DECL_KEYS)}
                          for (t, w, ex, ac) in failing]
        rec['ledger_editor'] = ledger_stats(run, 'editor')
        rec['ledger_game'] = ledger_stats(run, 'game')
        rec['report'] = report_stats(run)
        rec['shots'] = shots(run)
        rec['has'] = {n: os.path.exists(os.path.join(run, n)) for n in
                      ('report.json', 'report.md', 'trace-editor.jsonl',
                       'trace-game.jsonl', 'call-index.txt')}
        result.append(rec)

    with open(os.path.join(ROOT, 'dist', 'probe_runs.json'), 'w', encoding='utf-8') as fh:
        json.dump(result, fh, ensure_ascii=False, indent=1)

    # console summary
    tp = tf = te = tu = 0
    for r in result:
        if not r['exists']:
            print('MISSING', r['game']); continue
        a = r['assertions']
        und = sum(1 for x in r['failing'] if not x['declared'])
        tp += a['passed']; tf += a['failed']; te += a['errors']; tu += und
        pe = r['report']['pixel'] if r['report'] else {}
        print('%-15s %-24s calls=%3d (%2d/%3d) facts=%s assert p%4d f%d e%d und%d pixel=%s/%s' % (
            r['game'], r['tag'], r['calls_total'], r['calls_editor'], r['calls_game'],
            'ok', a['passed'], a['failed'], a['errors'], und,
            pe.get('non_zero_pairs', '?'), pe.get('comparable_pairs', '?')))
    print('TOTAL passed=%d failed=%d errors=%d undeclared=%d' % (tp, tf, te, tu))


main()
