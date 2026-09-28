# -*- coding: utf-8 -*-
"""TASK-140 §F: the artifact hash table (markdown) for the report.

Every path is repo-relative, every sha256 is full, every image carries its pixel dimensions.
Output: `runs/model-player/_scripts/t140_hash_table.md`.

Usage (through the ledger wrapper):
    t140_cmd.py --cwd F:\\moonbit-hof-rs\\godot-mcp -- <py> runs\\model-player\\_scripts\\t140_hash_table.py
"""
from __future__ import print_function

import hashlib
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))          # godot-mcp
REPO = os.path.abspath(os.path.join(ROOT, ".."))                       # the repository root
OUT = os.path.join(HERE, "t140_hash_table.md")

GROUPS = [
    ("改动的工具与声明（可提交）", [
        "godot-mcp/tools/playtest_player.py",
        "godot-mcp/tools/playability_gate.py",
        "godot-mcp/tools/playability_controls.json",
        "godot-mcp/tools/tests/test_playability_model_player.py",
        "godot-mcp/tools/playtest_artifact_index.py",
    ]),
    ("4 款游戏源码（可提交）", [
        "godot-mcp/projects/asteroids/src/AsteroidsGame.cs",
        "godot-mcp/projects/frogger/src/FroggerGame.cs",
        "godot-mcp/projects/bomberman/src/BombermanGame.cs",
        "godot-mcp/projects/flappy/src/FlappyBirdGame.cs",
    ]),
    ("记录（可提交）", [
        "DECISIONS.md",
        "godot-mcp/recovery/tasks/TEMPLATE-logic-feedback.md",
        "godot-mcp/recovery/reports/TASK-140-REPORT.md",
    ]),
    ("L3：本批的脚本与结果摘要（git add -f 入库）", [
        "godot-mcp/runs/model-player/_scripts/t140_sweep.log",
        "godot-mcp/runs/model-player/_scripts/t140_results_t140-scripted-w90-r1.json",
        "godot-mcp/runs/model-player/_scripts/t140_results_t140-scripted-w90-r2.json",
        "godot-mcp/runs/model-player/_scripts/t140_results_t140-jev-v3-w90-r1.json",
        "godot-mcp/runs/model-player/_scripts/t140_results_t140-jev-v3-w90-r2.json",
        "godot-mcp/runs/model-player/_scripts/t140_results_t140-playjev-v3-w90-r1.json",
        "godot-mcp/runs/model-player/_scripts/t140_results_t140-playjev-v3-w90-r2.json",
        "godot-mcp/runs/model-player/_scripts/t140_results_t140-prefix4-w90-r1.json",
        "godot-mcp/runs/model-player/_scripts/t140_stability_scripted.json",
        "godot-mcp/runs/model-player/_scripts/t140_stability_model.json",
        "godot-mcp/runs/model-player/_scripts/t140_stability_playjev.json",
        "godot-mcp/runs/model-player/_scripts/t140_unstable_breakout.json",
        "godot-mcp/runs/model-player/_scripts/t140_redirect_scan.json",
        "godot-mcp/runs/model-player/_scripts/t140_fix_evidence.json",
        "godot-mcp/runs/model-player/_scripts/t140_hash_table.md",
        "godot-mcp/runs/model-player/_index/ARTIFACTS-TASK-140.json",
        "godot-mcp/runs/model-player/_index/ARTIFACTS-TASK-140.md",
    ]),
    ("L4：run 数据（不入库，索引给哈希）", [
        "godot-mcp/runs/model-player/t140-scripted-w90-r1/asteroids/scripted/player.json",
        "godot-mcp/runs/model-player/t140-scripted-w90-r2/asteroids/scripted/player.json",
        "godot-mcp/runs/model-player/t140-jev-v3-w90-r1/asteroids/jev/player.json",
        "godot-mcp/runs/model-player/t140-jev-v3-w90-r2/asteroids/jev/player.json",
        "godot-mcp/runs/model-player/t140-w30-demo/asteroids/scripted/player.json",
        "godot-mcp/runs/model-player/t140-prefix4-w90-r1/frogger/scripted/player.json",
        "godot-mcp/runs/model-player/t140-prefix4-w90-r1/bomberman/scripted/player.json",
        "godot-mcp/runs/model-player/t140-prefix4-w90-r1/flappy/scripted/player.json",
        "godot-mcp/runs/model-player/t140-respawn-probe/probe.json",
        "godot-mcp/runs/model-player/t140-gate-4/playability.json",
        "godot-mcp/runs/model-player/t140-gate-4/asteroids/gate.json",
        "godot-mcp/runs/model-player/t140-gate-mpctx/asteroids/gate.json",
    ]),
    ("读图证据帧（全部 800×600，L4）", [
        "godot-mcp/runs/model-player/t140-prefix4-w90-r1/frogger/scripted/frames/004_01_after.png",
        "godot-mcp/runs/model-player/t140-postfix4-w90-r2/frogger/scripted/frames/004_01_after.png",
        "godot-mcp/runs/model-player/t140-prefix4-w90-r1/bomberman/scripted/frames/007_02_after.png",
        "godot-mcp/runs/model-player/t140-postfix4-w90-r3/bomberman/scripted/frames/007_02_after.png",
        "godot-mcp/runs/model-player/t140-prefix4-w90-r1/flappy/scripted/frames/002_01_before.png",
        "godot-mcp/runs/model-player/t140-postfix4-w90-r2/flappy/scripted/frames/002_01_before.png",
        "godot-mcp/runs/model-player/t139-jev-v3-w90/asteroids/jev/frames/016_05_after.png",
        "godot-mcp/runs/model-player/t139-jev-v3-w90/asteroids/jev/frames/037_12_after.png",
        "godot-mcp/runs/model-player/t140-respawn-probe/asteroids/frames/028_default_respawn_1s_01.png",
        "godot-mcp/runs/model-player/t140-respawn-probe/asteroids/frames/032_default_respawn_1s_05.png",
        "godot-mcp/runs/model-player/t140-respawn-probe/asteroids/frames/003_variant_respawn_delay_0_01.png",
    ]),
]


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def dims(p):
    try:
        from PIL import Image
        with Image.open(p) as im:
            return "%dx%d" % im.size
    except Exception:  # noqa: BLE001
        return "-"


def main():
    L = [u"# TASK-140 产物哈希表（生成器：`_scripts/t140_hash_table.py`）", u""]
    L.append(u"生成时刻：`%s`（本机）" % __import__("time").strftime("%Y-%m-%dT%H:%M:%S"))
    L.append(u"")
    for title, paths in GROUPS:
        L.append(u"### %s" % title)
        L.append(u"")
        L.append(u"| 路径 | 字节 | 尺寸 | sha256 |")
        L.append(u"|---|---|---|---|")
        for rel in paths:
            p = os.path.join(REPO, rel)
            if not os.path.isfile(p):
                L.append(u"| `%s` | - | - | **MISSING** |" % rel)
                continue
            L.append(u"| `%s` | %d | %s | `%s` |"
                     % (rel, os.path.getsize(p), dims(p), sha(p)))
        L.append(u"")
    with io.open(OUT, "w", encoding="utf-8") as fh:
        fh.write(u"\n".join(L))
    print("wrote %s" % OUT)
    for title, paths in GROUPS:
        miss = [r for r in paths if not os.path.isfile(os.path.join(REPO, r))]
        print("%-40s %d files%s" % (title, len(paths),
                                    (" MISSING: %s" % miss) if miss else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
