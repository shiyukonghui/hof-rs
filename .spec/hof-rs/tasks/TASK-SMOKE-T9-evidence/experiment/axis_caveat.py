import json, sys, urllib.request

PORT = sys.argv[1]

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

print('axis sample (input_axis) =', json.dumps(call('running_game_get_node_property_samples',
      {"node_path": "/root/Main/Player", "properties": ["input_axis"], "frame_count": 3})))
print('test_scenario assert input_axis =', json.dumps(call('running_game_run_test_scenario',
      {"steps": [{"type": "input", "action": "move_right", "pressed": True}, {"type": "wait", "seconds": 0.1},
                 {"type": "assert", "node_path": "Player", "property": "input_axis", "expected": 0}]}))[:500])
print('scene tree node count =', len(call('running_game_get_scene_tree', {}).get('tree', {}).get('children', [])))
print('Main props =', json.dumps(call('running_game_get_node_properties',
      {"node_path": "/root/Main", "properties": ["coins", "lives", "state"]})))
