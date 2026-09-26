import io, json, os, re, hashlib

R = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery"
W = os.path.join(R, "rebuild", "work2b")
C = os.path.join(R, "rebuild", "godot", "modules", "mcp_server", "docs", "tools_list.renamed.json")
c = json.load(io.open(C, encoding="utf-8"))
tools = c["result"]["tools"]
names = [t["name"] for t in tools]
print("count=%s added_count=%s generator_version=%s tools=%d" % (
    c["_meta"]["count"], c["_meta"]["added_count"], c["_meta"]["generator_version"], len(tools)))
# channel prefix census
cens = {}
for n in names:
    for ch in ("running_game_", "editor_", "project_", "os_"):
        if n.startswith(ch):
            cens[ch] = cens.get(ch, 0) + 1
            break
print("channel census:", cens)
# endpoint split (editor endpoint = editor + project + os; game = running_game + project + os)
editor = [n for n in names if n.startswith("editor_")]
game = [n for n in names if n.startswith("running_game_")]
both = [n for n in names if n.startswith("project_") or n.startswith("os_")]
print("editor_ prefix=%d running_game_ prefix=%d project_/os_ (both scopes)=%d" % (len(editor), len(game), len(both)))
print("editor endpoint = %d, game endpoint = %d" % (len(editor) + len(both), len(game) + len(both)))
# tool-groups-added.json (low confidence) scope data
tg = os.path.join(R, "rebuild", "godot", "modules", "mcp_server", "docs", "tool-groups-added.json")
print("tool-groups-added.json present:", os.path.isfile(tg))
if os.path.isfile(tg):
    try:
        d = json.load(io.open(tg, encoding="utf-8"))
        print("  keys:", sorted(d.keys())[:20])
    except Exception as e:
        print("  unparseable:", e)

# provenance anchors
print("contract sha256=%s bytes=%d" % (hashlib.sha256(io.open(C, "rb").read()).hexdigest(), os.path.getsize(C)))
print("target TASK-076A sha256=a5c59853c1e5a4913d600c663c8e972f058f7144869ec20337ab41b7a7bb17ea bytes=163520")
