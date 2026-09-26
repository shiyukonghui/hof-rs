# -*- coding: utf-8 -*-
"""TASK-083 recon: compare damaged files against the TASK-044 backup donor.

Read-only.  No shell redirection anywhere near this script's *output* path
(the caller passes an absolute -OutFile / RedirectStandardOutput).
"""
import difflib
import hashlib
import io
import json
import os
import sys

TREE = r"H:\rebuild\godot\modules\mcp_server"
BAK = r"C:\Users\wyl\AppData\Local\Temp\mcp044-module-backup\mcp_server"
OUT = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task083"


def readlines(path):
    with io.open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
        return f.readlines()


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def head_tail(path, n=6):
    ls = readlines(path)
    return ls[:n], ls[-n:], len(ls)


def brace_balance(path):
    """Approximate brace/paren balance ignoring strings, chars, comments."""
    src = io.open(path, "r", encoding="utf-8", errors="replace", newline="").read()
    depth_c = 0
    depth_p = 0
    depth_b = 0
    i = 0
    n = len(src)
    state = None
    while i < n:
        c = src[i]
        nxt = src[i + 1] if i + 1 < n else ""
        if state is None:
            if c == "/" and nxt == "/":
                state = "line"
                i += 2
                continue
            if c == "/" and nxt == "*":
                state = "block"
                i += 2
                continue
            if c == '"':
                if src[max(0, i - 1):i] in ('R"',) or src[i - 1:i] == "R":
                    pass
                state = "str"
                i += 1
                continue
            if c == "'":
                state = "chr"
                i += 1
                continue
            if c == "{":
                depth_c += 1
            elif c == "}":
                depth_c -= 1
            elif c == "(":
                depth_p += 1
            elif c == ")":
                depth_p -= 1
            elif c == "[":
                depth_b += 1
            elif c == "]":
                depth_b -= 1
            i += 1
            continue
        if state == "line":
            if c == "\n":
                state = None
            i += 1
            continue
        if state == "block":
            if c == "*" and nxt == "/":
                state = None
                i += 2
                continue
            i += 1
            continue
        if state == "str":
            if c == "\\":
                i += 2
                continue
            if c == '"':
                state = None
            i += 1
            continue
        if state == "chr":
            if c == "\\":
                i += 2
                continue
            if c == "'":
                state = None
            i += 1
            continue
    return {"brace": depth_c, "paren": depth_p, "bracket": depth_b, "end_state": state}


def main():
    lines = []
    for rel in [
        "mcp_server.cpp",
        "tools/editor_node_read.cpp",
        "tools/running_game_read_scene.cpp",
        "tools/project_write_resource_scene.cpp",
        "tools/running_game_frame_observation.cpp",
        "tools/running_game_node_write.cpp",
        "tools/tool_helpers.h",
        "tools/project_read_files.h",
        "tools/project_validate_scripts.cpp",
        "tool_registry.cpp",
        "tools/editor_input_simulation.cpp",
        "tools/editor_node_batch_write.cpp",
        "tools/editor_node_setup.cpp",
        "tools/editor_node_write.cpp",
        "tools/editor_write_scene_editor.cpp",
        "tools/running_game_script_execution.cpp",
        "tools/running_game_test_execution.cpp",
        "tools/tool_helpers.cpp",
    ]:
        p = os.path.join(TREE, rel.replace("/", os.sep))
        b = os.path.join(BAK, rel.replace("/", os.sep))
        entry = {"rel": rel, "tree_exists": os.path.exists(p), "bak_exists": os.path.exists(b)}
        if entry["tree_exists"]:
            h, t, n = head_tail(p)
            entry["tree_lines"] = n
            entry["tree_bytes"] = os.path.getsize(p)
            entry["tree_sha"] = sha(p)[:16]
            entry["tree_first6"] = [x.rstrip("\r\n") for x in h]
            entry["tree_last6"] = [x.rstrip("\r\n") for x in t]
            entry["tree_balance"] = brace_balance(p)
        if entry["bak_exists"]:
            h, t, n = head_tail(b)
            entry["bak_lines"] = n
            entry["bak_bytes"] = os.path.getsize(b)
            entry["bak_sha"] = sha(b)[:16]
            entry["bak_first6"] = [x.rstrip("\r\n") for x in h]
            entry["bak_last6"] = [x.rstrip("\r\n") for x in t]
            entry["bak_balance"] = brace_balance(b)
        lines.append(json.dumps(entry, ensure_ascii=False, sort_keys=True))
    with io.open(os.path.join(OUT, "survey.jsonl"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")

    # ---- targeted head comparison: tree file vs backup ----
    for rel, skip in [("mcp_server.cpp", 51)]:
        p = os.path.join(TREE, rel.replace("/", os.sep))
        b = os.path.join(BAK, rel.replace("/", os.sep))
        tl = readlines(p)
        bl = readlines(b)
        sm = difflib.SequenceMatcher(None, tl, bl[skip:], autojunk=False)
        opcodes = [op for op in sm.get_opcodes() if op[0] != "equal"]
        rec = {
            "rel": rel,
            "skipped_backup_lines": skip,
            "tree_lines": len(tl),
            "bak_remaining": len(bl) - skip,
            "ratio": round(sm.ratio(), 5),
            "non_equal_ops": opcodes[:40],
        }
        with io.open(os.path.join(OUT, "diff_mcp_server.json"), "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(rec, ensure_ascii=False, indent=1))
    print("survey written")


if __name__ == "__main__":
    main()
