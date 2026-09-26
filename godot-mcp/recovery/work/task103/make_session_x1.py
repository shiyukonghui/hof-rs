#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-103 (A): the minimal same-batch reproduction of tool defect X-1.

The script below is the *original* body of TASK-102's `g115-runtime-overlay`
call, recovered verbatim from `runs/match3/m3-task102-r1/trace-game.jsonl`
(seq 115, `args` field): it calls `main.addChild(c)` - the C# spelling of the
method - on a C# `Node2D`, which GDScript answers with

    SCRIPT ERROR: Invalid call. Nonexistent function 'addChild' in base
    'Node2D (Match3Game.cs)'.

The session that runs this file is used twice, unchanged:

  * against the pre-fix binary  -> X-1: `{"result":null,"result_type":"Nil"}`
    inside an `ok` answer, with no error code, no message and no suggestion;
  * against the post-fix binary -> `-32000` with
    `data.script_error` (message / line / script path / function) and
    `data.suggestion`, and the same facts on the trace call line.

The other five calls are the controls the verdict needs:

  g02  the scene tree right after the failure - no `ProbeOverlay` (the failure
       really did nothing);
  g03  the same body with the correct `add_child` - the engine, the mount point
       and the address of the C# node are all fine, so `g01`'s verdict is about
       the script and not about the environment (this is the control that makes
       the pair a comparison rather than an anecdote);
  g04  the scene tree right after the success - `ProbeOverlay` is there;
  g05  a body that returns nothing (`null`) and does nothing: the success path
       has to be distinguishable from "ran and changed something";
  g06  a body that does not parse: `-32602`, the pre-existing parse contract,
       which the fix must leave byte for byte.

Written by a Python writer, never by a shell redirect (iron rule 1).
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

# Verbatim from trace-game.jsonl seq 115 (the `args` string of that call).
FAILING_BODY = (
    "var main = get_parent()\n"
    "var c = ColorRect.new()\n"
    'c.name = StringName("ProbeOverlay")\n'
    "c.position = Vector2(20, 556)\n"
    "c.size = Vector2(120, 30)\n"
    "c.color = Color(0.95, 0.35, 0.95, 1.0)\n"
    "main.addChild(c)\n"
    'return "overlay added"'
)
# The same eight lines with the one character that matters changed.
FIXED_BODY = FAILING_BODY.replace("main.addChild(c)", "main.add_child(c)")
# A body with no `return` at all: succeeds and answers `null`.
NULL_BODY = "var c = ColorRect.new()\nc.queue_free()"
# A body that does not compile.
PARSE_BODY = "return ("


def call(tag, tool, arguments, note):
    return {"tag": tag, "port": "game", "tool": tool, "arguments": arguments, "note": note}


def main():
    session = {
        "import": True,
        "calls": [
            call("g01-failing-addchild", "running_game_execute_gdscript", {"code": FAILING_BODY},
                 "X-1 的最小复现：TASK-102 g115 那段原文（C# 的 addChild 拼写打在一个 C# Node2D 上）"),
            call("g02-scene-tree-after-fail", "running_game_get_scene_tree", {},
                 "失败之后立刻读一次场景树：没有任何 ProbeOverlay（失败确实什么也没做）"),
            call("g03-control-add_child", "running_game_execute_gdscript", {"code": FIXED_BODY},
                 "正控：同样的八行只把 addChild 改成 add_child；环境、挂载点、这个 C# 节点都是好的"),
            call("g04-scene-tree-after-ok", "running_game_get_scene_tree", {},
                 "成功之后读场景树：ProbeOverlay 在树上"),
            call("g05-success-null", "running_game_execute_gdscript", {"code": NULL_BODY},
                 "成功但没有返回值：要能与「跑了且有副作用」区分开"),
            call("g06-parse-fail", "running_game_execute_gdscript", {"code": PARSE_BODY},
                 "解析失败：-32602 的既有契约，本轮必须一字不动"),
        ],
    }
    out_dir = os.path.join(ROOT, "recovery", "work", "task103", "sessions")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "session-x1.json")
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(session, handle, ensure_ascii=False, indent=1)
        handle.write("\n")
    print("wrote %s (%d calls)" % (path, len(session["calls"])))
    # Round-trip so a malformed file can never be handed to the driver.
    with open(path, "r", encoding="utf-8") as handle:
        again = json.load(handle)
    assert len(again["calls"]) == 6
    print("json round-trip: OK (6 calls)")


if __name__ == "__main__":
    main()
