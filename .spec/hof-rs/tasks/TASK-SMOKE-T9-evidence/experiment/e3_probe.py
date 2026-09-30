import json, sys, urllib.request, time

PORT = sys.argv[1]
OUT = open(sys.argv[2], 'w', encoding='utf-8') if len(sys.argv) > 2 else sys.stdout

def log(*a):
    s = ' '.join(str(x) for x in a)
    print(s)
    if OUT is not sys.stdout:
        print(s, file=OUT)

def call(tool, args, timeout=120):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                       "params": {"name": tool, "arguments": args}}).encode()
    req = urllib.request.Request('http://127.0.0.1:%s/mcp' % PORT, data=body,
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read().decode('utf-8'))
    if 'error' in d:
        return {'__error': d['error']}
    try:
        return json.loads(d['result']['content'][0]['text'])
    except Exception:
        return d

def release_all():
    return call('running_game_play_input_recording',
                {"events": [{"type": "action", "action": a, "pressed": False}
                            for a in ("move_left", "move_right", "jump")], "speed": 1.0})

def inject(action, pressed=True):
    return call('running_game_play_input_recording',
                {"events": [{"type": "action", "action": action, "pressed": pressed}], "speed": 1.0})

def samples(frames):
    return call('running_game_get_node_property_samples',
                {"node_path": "/root/Main/Player", "properties": ["position"],
                 "frame_count": frames, "frame_interval": 1})

def props():
    return call('running_game_get_node_properties',
                {"node_path": "/root/Main/Player",
                 "properties": ["position", "velocity", "facing", "controllable"]})

def window(label, action, frames=60):
    rel = release_all()
    time.sleep(0.4)
    before = props()
    inj = inject(action, True)
    time.sleep(0.2)
    s = samples(frames)
    if 'samples' not in s:
        log('WINDOW %s ERROR %s' % (label, json.dumps(s)[:300]))
        return
    xs = [f['position']['x'] for f in s['samples']]
    ys = [f['position']['y'] for f in s['samples']]
    dx = xs[-1] - xs[0]
    dy = ys[-1] - ys[0]
    steps = [round(xs[i+1] - xs[i], 6) for i in range(len(xs) - 1)]
    uniq = sorted(set(steps))
    log('WINDOW %-12s action=%-10s frames=%d' % (label, action, len(xs)))
    log('  release=%s inject=%s' % (json.dumps(rel)[:160], json.dumps(inj)[:160]))
    log('  before=%s' % json.dumps(before.get('properties', before))[:220])
    log('  x first=%.6f last=%.6f dx=%.6f | y first=%.6f last=%.6f dy=%.6f' % (xs[0], xs[-1], dx, ys[0], ys[-1], dy))
    log('  per-frame dx unique=%s' % uniq[:10])
    log('  x per frame: ' + ' '.join('%.3f' % v for v in xs))
    log('  y per frame: ' + ' '.join('%.3f' % v for v in ys))

def main():
    log('PORT', PORT)
    rel0 = release_all()
    log('initial release_all=', json.dumps(rel0)[:200])
    time.sleep(0.5)
    log('initial props=', json.dumps(props())[:400])
    # baseline without injection
    release_all(); time.sleep(0.5)
    s = samples(30)
    xs = [f['position']['x'] for f in s['samples']]
    ys = [f['position']['y'] for f in s['samples']]
    log('WINDOW BASELINE_NO_INJECT frames=%d dx=%.6f dy=%.6f' % (len(xs), xs[-1]-xs[0], ys[-1]-ys[0]))
    window('MOVE_RIGHT', 'move_right', 60)
    release_all(); time.sleep(0.4)
    window('MOVE_LEFT', 'move_left', 60)
    release_all(); time.sleep(0.4)
    window('JUMP', 'jump', 30)
    release_all(); time.sleep(0.4)
    log('final props=', json.dumps(props())[:400])

main()
if OUT is not sys.stdout:
    OUT.close()
