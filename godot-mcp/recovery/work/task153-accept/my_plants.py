"""Independent acceptance plants for TASK-153 (authored by the acceptor).

Plants are chosen to be DIFFERENT from the implementer's and from TASK-152's:
  A1  engine baseline : swap two equal-length tool `name` values
                        (JSON stays valid, 174 unique names, byte count unchanged)
  A2  engine baseline : delete one whole tool object (174 -> 173, JSON valid)
  B1  rename map      : make two entries share a new_name, keeping their declared
                        channel/verb consistent so the L1..L3 lint still passes and
                        only the duplicate-name self-check can fire
  B2  rename map      : new_name whose verb disagrees with the entry's declared
                        verb (L3), verb still inside the closed set

Every plant refuses to write unless its needle occurs exactly once.
"""
import hashlib
import io
import json
import os
import sys

ENGINE = r"F:\moonbit-hof-rs\godot-mcp\godot"
BASE = ENGINE + r"\modules\mcp_server\docs\rename-baseline-tools-list.json"
MAP = ENGINE + r"\modules\mcp_server\docs\tool-rename-map.json"

# plant id -> (file, old_needle, new_needle)
SIMPLE = {
    # A1: exchange two equal-length names (both 10 chars)
    "A1": (BASE, b'"name":"open_scene"', b'"name":"zyme_scene"'),
    # B1: give search_in_files the same new_name as search_files (both verb=search,
    #     channel=project, so L1/L2/L3 still pass -> only the duplicate check can fire)
    "B1": (MAP, b'"new_name": "project_search_file_contents"',
           b'"new_name": "project_search_file_names"'),    # B2: project_get_info -> project_read_info; declared verb stays "get" (L3)
    "B2": (MAP, b'"new_name": "project_get_info"', b'"new_name": "project_read_info"'),
}

# A1 is a two-step permutation: open_scene -> placeholder, stop_scene -> open_scene,
# placeholder -> stop_scene. Handled specially below.
A1_NEEDLES = [b'"name":"open_scene"', b'"name":"stop_scene"']


def sha(p):
    return hashlib.sha256(io.open(p, "rb").read()).hexdigest()


def count_needle(raw, needle):
    n = 0
    start = 0
    while True:
        i = raw.find(needle, start)
        if i < 0:
            return n
        n += 1
        start = i + 1


def compact(obj):
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def plant_A2():
    raw = io.open(BASE, "rb").read()
    obj = json.loads(raw.decode("utf-8"))
    # prove the re-serialisation is byte-lossless BEFORE mutating anything
    if compact(obj) != raw:
        sys.exit("REFUSED: A2 compact re-serialisation is not byte-lossless")
    print("A2 lossless compact round-trip = True  (%d bytes)" % len(raw))
    tools = obj["result"]["tools"]
    victim = [t for t in tools if t["name"] == "tilemap_get_cell"]
    if len(victim) != 1:
        sys.exit("REFUSED: A2 victim not unique")
    tools.remove(victim[0])
    new = compact(obj)
    reparsed = json.loads(new.decode("utf-8"))
    n = len(reparsed["result"]["tools"])
    names = [t["name"] for t in reparsed["result"]["tools"]]
    print("A2 deleted tool 'tilemap_get_cell'; tools %d -> %d unique=%d"
          % (len(tools) + 1, n, len(set(names))))
    print("A2 bytes %d -> %d   sha256 %s -> %s"
          % (len(raw), len(new), hashlib.sha256(raw).hexdigest(),
             hashlib.sha256(new).hexdigest()))
    if n != 173:
        sys.exit("REFUSED: A2 expected 173 tools, got %d" % n)
    io.open(BASE, "wb").write(new)


def plant_simple(pid):
    path, old, new = SIMPLE[pid]
    raw = io.open(path, "rb").read()
    c = count_needle(raw, old)
    print("%s needle %r occurrences = %d" % (pid, old, c))
    if c != 1:
        sys.exit("REFUSED: %s needle not unique" % pid)
    # B1 deliberately collides with an existing new_name, so a pre-existing
    # replacement is EXPECTED there; every other plant requires a fresh target.
    if pid != "B1" and count_needle(raw, new) != 0:
        sys.exit("REFUSED: %s replacement already present" % pid)
    out = raw.replace(old, new)
    if pid == "B1":
        n = count_needle(out, new)
        print("%s shared new_name now occurs %d times (was %d)"
              % (pid, n, count_needle(raw, new)))
        if n != 2:
            sys.exit("REFUSED: B1 expected the shared new_name twice, got %d" % n)
    obj = json.loads(out.decode("utf-8"))
    print("%s json still parses = True  bytes %d -> %d" % (pid, len(raw), len(out)))
    print("%s sha256 %s -> %s" % (pid, hashlib.sha256(raw).hexdigest(),
                                  hashlib.sha256(out).hexdigest()))
    io.open(path, "wb").write(out)


def plant_A1():
    raw = io.open(BASE, "rb").read()
    for n in A1_NEEDLES:
        c = count_needle(raw, n)
        print("A1 needle %r occurrences = %d" % (n, c))
        if c != 1:
            sys.exit("REFUSED: A1 needle not unique")
    tmp = b'"name":"__PLANT_TMP__"'
    if count_needle(raw, tmp) != 0:
        sys.exit("REFUSED: A1 temp marker already present")
    out = raw.replace(A1_NEEDLES[0], tmp)
    out = out.replace(A1_NEEDLES[1], A1_NEEDLES[0])
    out = out.replace(tmp, A1_NEEDLES[1])
    obj = json.loads(out.decode("utf-8"))
    names = [t["name"] for t in obj["result"]["tools"]]
    print("A1 json still parses = True  tools=%d unique=%d"
          % (len(names), len(set(names))))
    print("A1 bytes %d -> %d   sha256 %s -> %s"
          % (len(raw), len(out), hashlib.sha256(raw).hexdigest(),
             hashlib.sha256(out).hexdigest()))
    io.open(BASE, "wb").write(out)


if __name__ == "__main__":
    pid = sys.argv[1]
    print("=== PLANT %s target=%s ===" % (pid, "baseline" if pid.startswith("A") else "map"))
    if pid == "A1":
        plant_A1()
    elif pid == "A2":
        plant_A2()
    else:
        plant_simple(pid)
    print("PLANT_OK")
