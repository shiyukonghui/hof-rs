# TASK-097 (B): verify one game's cleanup run from its own response files.
#
#   python check_cleanup.py <game> <run-dir>
#
# The four claims, each from a pair of the run's real answers:
#   1. the duplicate layer is gone from the saved scene file;
#   2. the scene file differs from the pre-cleanup one by the duplicate node
#      blocks ONLY - every named node's serialized block is byte-identical, so the
#      game's own content is untouched (this is the "logic unchanged" half that
#      does not depend on the game running);
#   3. the before/after property samples of the named nodes are equal;
#   4. no duplicate came back during the replay (the replayed
#      `editor_add_nodes_batch` was refused by the TASK-097 policy, and the tree
#      read at the end of the replay has no auto-named node).
import json
import os
import re
import sys

RUN = sys.argv[2]
AUTO_RE = re.compile(r"^@([A-Za-z0-9_]+)@(\d+)$")


def load(tag):
    path = os.path.join(RUN, tag + ".json")
    if not os.path.isfile(path):
        return None, "MISSING %s" % path
    doc = json.loads(open(path, encoding="utf-8-sig").read())
    if "error" in doc:
        return None, "ERROR %s" % json.dumps(doc["error"], ensure_ascii=False)
    content = doc["result"]["content"]
    return json.loads(content[0]["text"]), None


def blocks(text):
    """The `[node ...]` blocks of a .tscn, keyed by the node's name."""
    out = {}
    order = []
    for match in re.finditer(r'^\[node name="([^"]+)"', text, re.M):
        out.setdefault(match.group(1), []).append(match.start())
        order.append(match.group(1))
    result = {}
    positions = [(m.start(), m.group(1)) for m in re.finditer(r'^\[node name="([^"]+)"', text, re.M)]
    for index, (start, name) in enumerate(positions):
        end = positions[index + 1][0] if index + 1 < len(positions) else len(text)
        result.setdefault(name, []).append(text[start:end])
    return result, order


before, err = load("c03-read-before")
if err:
    sys.exit("FATAL: " + err)
after, err = load("c08-read-after")
if err:
    sys.exit("FATAL: " + err)

b_text, b_order = before["text"], None
a_text = after["text"]
b_blocks, b_keys = blocks(b_text)
a_blocks, a_keys = blocks(a_text)

b_dup = [n for n in b_keys if AUTO_RE.match(n)]
a_dup = [n for n in a_keys if AUTO_RE.match(n)]
b_named = [n for n in b_keys if not AUTO_RE.match(n)]
a_named = [n for n in a_keys if not AUTO_RE.match(n)]

print("== %s in %s" % (sys.argv[1], RUN))
print("1. duplicates in the file before=%d after=%d" % (len(b_dup), len(a_dup)))
print("   file sha before=%s after=%s" % (before["sha256"][:16], after["sha256"][:16]))
print("   size before=%d after=%d" % (before["size"], after["size"]))

# 2. named nodes byte-identical (modulo the blank line that separates one block
#    from the next: the last node of a file carries no trailing separator)
def norm(text):
    return (text or "").rstrip("\n")


same = [n for n in b_named if norm(b_blocks.get(n, [""])[0]) == norm(a_blocks.get(n, [""])[0])]
diff = [n for n in b_named if norm(b_blocks.get(n, [""])[0]) != norm(a_blocks.get(n, [""])[0])]
print("2. named node blocks: identical=%d changed=%d (named count before=%d after=%d)" % (
    len(same), len(diff), len(b_named), len(a_named)))
for name in diff[:5]:
    print("   CHANGED: %s" % name)
print("   reconstructed == after-text with all duplicates removed? %s" % (
    "yes" if b_text == a_text else "see below"))
stripped_parts = []
positions = [(m.start(), m.group(1)) for m in re.finditer(r'^\[node name="([^"]+)"', b_text, re.M)]
header = b_text[:positions[0][0]] if positions else b_text
stripped = header
for index, (start, name) in enumerate(positions):
    end = positions[index + 1][0] if index + 1 < len(positions) else len(b_text)
    if not AUTO_RE.match(name):
        stripped += b_text[start:end]
print("   before-minus-duplicates == after (byte for byte, ignoring the trailing newline AND the")
print("   scene's own uid, which editor_save_scene re-issues once per editor session): %s" % (
    "yes" if re.sub(r'uid="uid://[^"]+"', 'uid="UID"', stripped).rstrip("\n")
    == re.sub(r'uid="uid://[^"]+"', 'uid="UID"', a_text).rstrip("\n") else "NO"))

# 3. property samples
ok_samples = 0
bad_samples = 0
for index in range(0, 12):
    b_sample, err_b = load("c04-sample-before-%d" % index)
    if err_b:
        break
    a_sample, err_a = load("c09-sample-after-%d" % index)
    if err_a:
        sys.exit("FATAL: " + err_a)
    if b_sample == a_sample:
        ok_samples += 1
        print("3. sample %d equal: %s" % (index, json.dumps(b_sample.get("properties", b_sample), ensure_ascii=False)[:160]))
    else:
        bad_samples += 1
        print("3. sample %d DIFFERS:\n   before=%s\n   after =%s" % (
            index, json.dumps(b_sample, ensure_ascii=False), json.dumps(a_sample, ensure_ascii=False)))
print("   samples equal=%d differ=%d" % (ok_samples, bad_samples))

# 4. no duplicate came back
tree, err = load("c06-tree-after")
if err:
    print("4. tree-after: %s" % err)
else:
    names = []

    def walk(node):
        names.append(node.get("name"))
        for child in node.get("children", []) or []:
            walk(child)

    walk(tree["tree"] if "tree" in tree else tree)
    back = [n for n in names if n and AUTO_RE.match(n)]
    print("4. tree-after auto-named nodes: %d (%s)" % (len(back), ", ".join(back[:5])))
