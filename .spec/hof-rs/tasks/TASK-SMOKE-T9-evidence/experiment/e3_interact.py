import json, sys, urllib.request, time

PORT = sys.argv[1]
OUT = open(sys.argv[2], 'w', encoding='utf-8') if len(sys.argv) > 2 else sys.stdout

def log(*a):
    s = ' '.join(str(x) for x in a)
    print(s)
    if OUT is not sys.stdout:
        print(s, file=OUT)

def call(tool, args, timeout=120, rid=1):
    body = json.dumps({"jsonrpc": "2.0", "id": rid, "method": "tools/call",
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

def main_props():
    return call('running_game_get_node_properties',
                {"node_path": "/root/Main", "properties": ["coins", "lives", "state", "time_left"]})

def player_props():
    return call('running_game_get_node_properties',
                {"node_path": "/root/Main/Player", "properties": ["position", "velocity"]})

def node_props(path, props):
    return call('running_game_get_node_properties', {"node_path": path, "properties": props})

def move_to(x, y):
    return call('running_game_set_node_property',
                {"node_path": "/root/Main/Player", "property": "position", "value": {"x": x, "y": y}})

def main():
    log('PORT', PORT)
    for a in ("move_left", "move_right", "jump"):
        call('running_game_play_input_recording',
             {"events": [{"type": "action", "action": a, "pressed": False}], "speed": 1.0})
    time.sleep(0.5)
    log('start Main=', json.dumps(main_props().get('properties')))
    log('start Player=', json.dumps(player_props().get('properties')))
    tree = call('running_game_get_scene_tree', {})
    def names(n, acc):
        for c in n.get('children', []) or []:
            acc.append(c.get('name') or c.get('path'))
            names(c, acc)
        return acc
    log('tree names=', names(tree.get('tree', {}), []))
    for nm in ('Coin1', 'Coin2', 'Goal'):
        log('%s=' % nm, json.dumps(node_props('/root/Main/%s' % nm, ['position']).get('properties')))
    coin = node_props('/root/Main/Coin1', ['position']).get('properties', {})
    goal = node_props('/root/Main/Goal', ['position']).get('properties', {})
    # --- coin pickup: put the player on the coin
    before = main_props().get('properties', {})
    cp = coin.get('position', {})
    log('teleport player onto Coin1 at', cp)
    log('move_to=', json.dumps(move_to(cp.get('x'), cp.get('y')))[:200])
    time.sleep(1.0)
    after = main_props().get('properties', {})
    log('coins before=%s after=%s' % (before.get('coins'), after.get('coins')))
    log('Coin1 present in tree after pickup?', 'Coin1' in names(call('running_game_get_scene_tree', {}).get('tree', {}), []))
    # --- goal: put the player on the goal
    gp = goal.get('position', {})
    log('teleport player onto Goal at', gp)
    log('move_to=', json.dumps(move_to(gp.get('x'), gp.get('y')))[:200])
    time.sleep(1.5)
    log('Main after goal=', json.dumps(main_props().get('properties')))
    log('Player after goal=', json.dumps(player_props().get('properties')))

main()
if OUT is not sys.stdout:
    OUT.close()
