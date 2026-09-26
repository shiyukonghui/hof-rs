import io, os, re

R = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery"
p = os.path.join(R, "rebuild", "godot", "modules", "mcp_server", "tools", "registration.cpp")
raw = io.open(p, "rb").read()
print("bytes", len(raw), "CRLF", raw.count(b"\r\n"), "LF", raw.count(b"\n"))
txt = raw.decode("utf-8", "replace")
print("lines", len(txt.split("\n")))
inc = re.findall(r'#include "([^"]+)"', txt)
print("includes", len(inc), inc[:5])
calls = re.findall(r"register_([a-z0-9_]+)_tools\(r_registry\)", txt)
print("calls", len(calls), calls[:5])
print("count of '#include'", txt.count("#include"))
print("count of '_tools(r_registry)'", txt.count("_tools(r_registry)"))
