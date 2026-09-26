# TASK-097 (B): generate the "clean the duplicate layer, then replay the same
# batch of calls" session of one game.
#
#   python make_cleanup_session.py <game> [--no-replay]
#
# Input : tools/sessions/<game>/session.json  (the game's original session)
#         projects/<game>/scenes/main.tscn    (the scene the duplicates are in)
# Output: tools/sessions/<game>/session-clean-task097.json
#
# The generated session is placed next to the original one on purpose: the
# original session's `content_file` references are resolved relative to the
# session file's own directory (`payload/*.cs`), so a session kept anywhere else
# could not replay the same calls.
#
# The cleanup half is: open the scene, read the tree, read the scene file's bytes,
# sample the named nodes' properties, delete every node whose name is an engine
# auto-name (`@Type@NNNN`), read the tree again, read the file again, sample the
# same properties again. The replay half is the original session's calls, verbatim
# and in the original order - including its own `editor_add_nodes_batch`, which
# the TASK-097 fix turns into a refusal (that is the "no re-pollution" evidence).
import json
import os
import re
import sys

GAME = sys.argv[1]
NO_REPLAY = "--no-replay" in sys.argv
ROOT = r"F:\moonbit-hof-rs\godot-mcp"
SESSION = os.path.join(ROOT, "tools", "sessions", GAME, "session.json")
SCENE = os.path.join(ROOT, "projects", GAME, "scenes", "main.tscn")
OUT = os.path.join(ROOT, "tools", "sessions", GAME, "session-clean-task097.json")

NODE_RE = re.compile(r'^\[node name="([^"]+)" type="([^"]+)" parent="([^"]*)"', re.M)
AUTO_RE = re.compile(r"^@([A-Za-z0-9_]+)@(\d+)$")

text = open(SCENE, encoding="utf-8").read()
duplicates = []
named = []
for match in NODE_RE.finditer(text):
    name, node_type, parent = match.group(1), match.group(2), match.group(3)
    if AUTO_RE.match(name):
        duplicates.append({"name": name, "type": node_type, "parent": parent})
    else:
        named.append({"name": name, "type": node_type, "parent": parent})

# The sampled nodes: the first few named nodes (the ones the duplicate layer was
# drawn over) plus the last one, so the before/after property comparison covers
# more than one class. The property list is per class, because
# `editor_get_node_properties` refuses a property the node does not declare
# (`text` is a Label's, `color` a ColorRect's).
SAMPLED_PROPERTIES = {
    "Label": ["position", "size", "text", "visible"],
    "ColorRect": ["position", "size", "color", "visible"],
}
DEFAULT_PROPERTIES = ["position", "size", "visible"]

samples = [n for n in named if n["name"] != "Main"][:3]
if named:
    samples.append(named[-1])
samples_by_name = {n["name"]: n for n in samples}


def sample_properties(name):
    node = samples_by_name.get(name)
    return SAMPLED_PROPERTIES.get(node["type"] if node else "", DEFAULT_PROPERTIES)


calls = []
def add(tag, tool, arguments, note):
    calls.append({"tag": tag, "port": "editor", "tool": tool, "arguments": arguments, "note": note})

add("c01-open-scene", "editor_open_scene", {"path": "res://scenes/main.tscn"},
    "open the scene whose duplicate layer is to be removed")
add("c02-tree-before", "editor_get_scene_tree", {},
    "the tree WITH the duplicate layer (before)")
add("c03-read-before", "project_read_text_file", {"path": "res://scenes/main.tscn"},
    "the scene file's bytes and sha256 before the cleanup")
for index, node in enumerate(samples):
    add("c04-sample-before-%d" % index, "editor_get_node_properties",
        {"path": node["name"], "properties": sample_properties(node["name"])},
        "property sample of the named node '%s' (%s) before the cleanup" % (node["name"], node["type"]))
for index, dup in enumerate(duplicates):
    add("c05-delete-%03d" % index, "editor_delete_node", {"path": dup["name"]},
        "delete the duplicate node %s (%s), which the engine created because the name was taken" % (dup["name"], dup["type"]))
add("c06-tree-after", "editor_get_scene_tree", {},
    "the tree WITHOUT the duplicate layer (after)")
add("c07-save-scene", "editor_save_scene", {},
    "publish the cleaned scene; the duplicates must be gone from the FILE, not just from the editor")
add("c08-read-after", "project_read_text_file", {"path": "res://scenes/main.tscn"},
    "the scene file's bytes and sha256 after the cleaned scene was published; the diff against c03 is the duplicate blocks only")
for index, node in enumerate(samples):
    add("c09-sample-after-%d" % index, "editor_get_node_properties",
        {"path": node["name"], "properties": sample_properties(node["name"])},
        "property sample of the named node '%s' after the cleanup (must equal c04-sample-before-%d)" % (node["name"], index))

original = json.load(open(SESSION, encoding="utf-8"))
replay_count = 0
if not NO_REPLAY:
    for call in original["calls"]:
        calls.append(call)
        replay_count += 1

doc = {"import": True, "calls": calls}
with open(OUT, "w", encoding="utf-8", newline="\n") as handle:
    json.dump(doc, handle, ensure_ascii=False, indent=2)
    handle.write("\n")

print("game=%s scene=%s" % (GAME, SCENE))
print("named nodes=%d duplicates=%d" % (len(named), len(duplicates)))
print("duplicate names: %s" % ", ".join(d["name"] for d in duplicates))
print("sampled nodes: %s" % ", ".join("%s(%s:%s)" % (n["name"], n["type"], ",".join(sample_properties(n["name"]))) for n in samples))
print("cleanup calls=%d replayed calls=%d total=%d" % (len(calls) - replay_count, replay_count, len(calls)))
print("wrote %s" % OUT)
