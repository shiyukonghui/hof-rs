import io, json, os, re

R = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery"
LC = os.path.join(R, "rebuild", "_low-confidence", "modules", "mcp_server", "tools", "registration.cpp")
G = os.path.join(R, "rebuild", "godot", "modules", "mcp_server")
TREE = os.path.join(G, "tools", "registration.cpp")

txt = io.open(LC, encoding="utf-8").read()
raw = io.open(LC, "rb").read()
print("low-conf registration.cpp bytes=%d lines=%d crlf=%d lf=%d" % (len(raw), len(txt.split("\n")), raw.count(b"\r\n"), raw.count(b"\n")))
inc = re.findall(r'#include "([^"]+)"', txt)
calls = re.findall(r"register_([a-z0-9_]+)_tools\(r_registry\)", txt)
print("includes=%d unique=%d  calls=%d unique=%d" % (len(inc), len(set(inc)), len(calls), len(set(calls))))
inc_h = [i for i in inc if i.endswith(".h")]
print("group includes:", len(inc_h))
call_h = set(c + ".h" for c in calls)
print("calls without include:", sorted(call_h - set(inc_h)))
print("includes without call:", sorted(set(inc_h) - call_h))
tools_dir = os.path.join(G, "tools")
present = set(os.listdir(tools_dir)) if os.path.isdir(tools_dir) else set()
missing_files = [i for i in inc_h if i not in present]
print("referenced group headers NOT present in tree/tools:", len(missing_files))
for m in missing_files:
    print("   MISSING", m)
# fossil header count in tools dir
print("tools/ dir entries:", len(present))

# how many names are there in the contract? use generated low-confidence? no, report struct only
