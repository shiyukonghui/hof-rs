import io, json, os, re
R = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery"
G = os.path.join(R, "rebuild", "godot", "modules", "mcp_server")
reg = io.open(os.path.join(G, "tools", "registration.cpp"), encoding="utf-8").read()
includes = re.findall(r'#include "([^"]+)"', reg)
calls = re.findall(r"register_([a-z0-9_]+)_tools\(r_registry\)", reg)
print("includes:", len(includes), "unique:", len(set(includes)))
print("register calls:", len(calls), "unique:", len(set(calls)))
inc_names = set(i for i in includes)
call_names = set(c + ".h" for c in calls)
print("calls without include:", sorted(call_names - inc_names))
print("includes without call:", sorted(inc_names - call_names))
docs = os.path.join(G, "docs")
allgroups = {}
for mf in sorted(os.listdir(docs)):
    if not mf.startswith("tool-groups") or not mf.endswith(".json"): continue
    p = os.path.join(docs, mf)
    try: d = json.load(io.open(p, encoding="utf-8"))
    except Exception as e:
        print("MANIFEST", mf, "UNPARSEABLE", e); continue
    groups = d.get("groups") if isinstance(d, dict) else None
    if groups is None and isinstance(d, list): groups = d
    names=[]; tools=0
    if isinstance(groups, list):
        for g in groups:
            nm = g.get("name") or g.get("group"); names.append(nm)
            tl = g.get("tools") or g.get("members") or []
            if isinstance(tl, list): tools += len(tl)
            allgroups[nm] = (mf, len(tl) if isinstance(tl,list) else None)
    print("MANIFEST %-26s groups=%d tools=%s" % (mf, len(names), tools))
    miss=[n for n in names if n and (n+".h") not in inc_names]
    if miss: print("   groups NOT included:", miss)
inc_bases = set(i[:-2] for i in includes)
print("tools/*.h not in any manifest:", sorted(inc_bases - set(allgroups)))
