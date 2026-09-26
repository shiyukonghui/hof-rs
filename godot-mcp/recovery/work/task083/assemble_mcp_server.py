# -*- coding: utf-8 -*-
"""TASK-083 tool 2: assemble mcp_server.cpp.

The tree copy is a gap-collapsed splice whose fragments are also out of order
(TASK-082 diagnosed a "lost head"; the truth is worse).  This script rebuilds a
single coherent translation unit:

  H  <- backup  1-51    licence, includes, singleton, `namespace MCPPort {`
  A  <- tree    1-119   MCPPort + MCPPendingTimeout + ctor/dtor + _bind_methods
                        + TASK-063 endpoint-state accessors      (newest text)
  B  <- backup  149-222 _notification, _retire_unattached, bootstrap
  C  <- backup  224     `void MCPServer::pump_frame(double) {`   (signature only)
  D  <- tree    121-153 pump_frame body                          (newest text)
  E  <- tree    155-238 _shutdown, handle_jsonrpc_request        (newest text)
  F  <- backup  344-352 build_deferred_body
  G  <- backup  354-433 get_status_body .. _register_tools
  I  <- tree    304-522 _start_service                           (newest text)

Every segment boundary is a function boundary, so the join points are safe.
"""
import io
import os
import sys

TREE = r"H:\rebuild\godot\modules\mcp_server\mcp_server.cpp"
BAK = r"C:\Users\wyl\AppData\Local\Temp\mcp044-module-backup\mcp_server\mcp_server.cpp"
OUT = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task083"

SEGMENTS = [
    ("H", BAK, 1, 51),
    ("A", TREE, 1, 119),
    ("B", BAK, 149, 222),
    ("C", BAK, 224, 224),
    ("D", TREE, 121, 153),
    ("E", TREE, 155, 238),
    ("F", BAK, 344, 352),
    ("G", BAK, 354, 433),
    ("I", TREE, 304, 522),
]


def read_plain(path):
    with io.open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
        return [ln.rstrip("\r\n") for ln in f]


def main():
    write = "--write" in sys.argv
    srcs = {TREE: read_plain(TREE), BAK: read_plain(BAK)}
    out = []
    for name, path, a, b in SEGMENTS:
        lines = srcs[path][a - 1:b]
        assert len(lines) == b - a + 1, "segment %s short" % name
        out.append(("# SEG-%s <- %s %d-%d" % (name,
                    "backup" if path == BAK else "tree", a, b), name))
        out.extend([(l, name) for l in lines])
    text = [l for l, _ in out if not l.startswith("# SEG-")]
    if write:
        with io.open(TREE, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(text) + "\n")
        print("written %s (%d lines)" % (TREE, len(text)))
    else:
        with io.open(os.path.join(OUT, "mcp_server.assembled.txt"), "w",
                     encoding="utf-8", newline="\n") as f:
            f.write("\n".join(text) + "\n")
        print("dry-run -> %s (%d lines)" % (os.path.join(OUT, "mcp_server.assembled.txt"), len(text)))


if __name__ == "__main__":
    main()
