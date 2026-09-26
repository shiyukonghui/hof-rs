# -*- coding: utf-8 -*-
"""TASK-102: rename this round's tool-defect id from T-1 to X-1.

T-1 is already taken by Tetris in the 游戏或驱动缺陷 table (TASK-096), and this
round's tool-defect row lives in the 工具缺陷 table, whose ids have so far been
unique (D-1, D-2, G-1).  Two different T-1 rows -- one per table -- would be read
as the same id, so the tool row gets a free id instead.  Every replacement is
count-checked so nothing else is touched.
"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
LOG = os.path.join(ROOT, "GAME-LOOP-LOG.md")

with io.open(LOG, "r", encoding="utf-8") as handle:
    text = handle.read()

PAIRS = [
    ("| **T-1** | 运行期 / 错误信息（`running_game_execute_gdscript`）",
     "| **X-1** | 运行期 / 错误信息（`running_game_execute_gdscript`）"),
    ("工具 **T-1**（只记录、未改模块）", "工具 **X-1**（只记录、未改模块）"),
    ("**工具缺陷 1 条（T-1，只记录、未改模块）**", "**工具缺陷 1 条（X-1，只记录、未改模块）**"),
    ("（T-1 只是记录，没有动模块）", "（X-1 只是记录，没有动模块）"),
    ("必须配像素差与场景树证据（T-1）", "必须配像素差与场景树证据（X-1）"),
]
for old, new in PAIRS:
    count = text.count(old)
    if count != 1:
        raise SystemExit("FATAL: %r occurs %d times" % (old[:40], count))
    text = text.replace(old, new)

with io.open(LOG, "w", encoding="utf-8", newline="\n") as handle:
    handle.write(text)
print("renamed T-1 -> X-1 in %s (%d bytes)" % (LOG, len(text)))
for token in ("X-1", "**T-1**"):
    print("  occurrences of %-8s : %d" % (token, text.count(token)))
