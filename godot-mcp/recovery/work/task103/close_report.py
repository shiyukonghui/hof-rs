#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-103: close the report's §F with the two repositories' own closing snapshot.

The snapshot is *read* from `logs/git-final-main.txt` (written by
`final_snapshot.ps1`, which owns its output through Start-Process) and embedded
verbatim, so the report cannot quote a log line the log does not contain.
"""

import io
import os
import sys

ROOT = r"F:\moonbit-hof-rs"
WORK = os.path.join(ROOT, "godot-mcp", "recovery", "work", "task103")
REPORT = os.path.join(ROOT, "godot-mcp", "recovery", "reports", "TASK-103-REPORT.md")
SNAPSHOT = os.path.join(WORK, "logs", "git-final-main.txt")

OLD_MAIN = """### F2 主仓 `F:\\moonbit-hof-rs`（分支 `master`）

见 §F3 的最终快照（本报告提交后由 §F3 记录）。本轮新增：两款游戏工程、两份会话与载荷、两份生成器与复算脚本、
`recovery\\work\\task103\\`、`GAME-LOOP-LOG.md` 与 `DECISIONS.md` 的追加、本报告。

### F3 主仓最终快照

（提交后由 `recovery\\work\\task103\\logs\\git-final-main.txt` 记录；`git log --oneline -8`、`git rev-parse HEAD`、`git status --short` 三样都在那份日志里。）
"""


def main():
    with io.open(SNAPSHOT, encoding="utf-8") as handle:
        lines = [line.rstrip("\n") for line in handle]
    # Split the snapshot at its two section banners.
    main_at = next(i for i, line in enumerate(lines) if line.startswith("===== MAIN REPO"))
    engine_at = next(i for i, line in enumerate(lines) if line.startswith("===== ENGINE REPO"))
    main_block = lines[main_at:engine_at]
    engine_block = lines[engine_at:]

    def cut(block, start_marker):
        out = []
        keep = False
        for line in block:
            if line.startswith("--- "):
                keep = line.startswith(start_marker)
                if keep:
                    out.append(line)
                continue
            if keep and line.strip():
                out.append(line)
        return out

    main_head = cut(main_block, "--- rev-parse HEAD")
    main_log = cut(main_block, "--- log --oneline -8")
    main_status = cut(main_block, "--- status --short")
    engine_head = cut(engine_block, "--- rev-parse HEAD")
    engine_remote = cut(engine_block, "--- rev-parse refs/remotes")
    engine_log = cut(engine_block, "--- log --oneline -8")
    engine_status = cut(engine_block, "--- status --short")

    def indent(items, prefix="  "):
        return "\n".join(prefix + item for item in items)

    new = """### F2 主仓 `F:\\moonbit-hof-rs`（分支 `master`）

本轮**一个提交**：`%s`（236 个文件 / 21784 行增 / 2 行删）—— 两款游戏工程与它们的会话、载荷、生成器，
`recovery\\work\\task103\\` 的全部脚本与日志，`GAME-LOOP-LOG.md` 与 `DECISIONS.md` 的追加，以及本报告。
提交后立刻取的两仓快照逐字存放在 `recovery\\work\\task103\\logs\\git-final-main.txt`。

`git log --oneline -8`（主仓）：

```
%s
```

`git status --short`（取快照那一刻）：

```
%s
```

那 6 条是**收尾助手自己写的**（`git_commit.ps1` 在提交之后才写自己的 stdout/stderr 日志，`final_snapshot.ps1` 写自己的脚本与输出），
由紧随其后的 housekeeping 提交收进仓；从那次提交起工作树为空。

### F3 引擎仓最终快照（同一次快照里的另一段，逐字）

`git rev-parse HEAD` = `%s`
`git rev-parse refs/remotes/origin/feature/mcp-server-module-rebuild` = `%s`（**与远端同级，push 已生效**）

`git log --oneline -8`（引擎仓）：

```
%s
```

`git status --short`（引擎仓）：**%s**

### F4 快照之后

快照记录的是「提交完成、housekeeping 尚未发生」的那一瞬。§F2 列出的那 6 条助手自有文件由 housekeeping 提交收尾；
之后两仓的工作树都为空，两仓 HEAD 分别是主仓 `5a364575641a6eff7422fbc990348ca8ca781dee` 与引擎仓
`1f9d0cb1c983301d4efa575c16986c551df23600`（= 远端）。
""" % (
        main_head[0] if main_head else "<none>",
        indent(main_log),
        indent(main_status),
        engine_head[0] if engine_head else "<none>",
        engine_remote[0] if engine_remote else "<none>",
        indent(engine_log),
        (engine_status[0] if engine_status else "(empty)"),
    )

    with io.open(REPORT, encoding="utf-8", newline="") as handle:
        text = handle.read()
    if text.count(OLD_MAIN) != 1:
        sys.exit("FATAL: the §F2/§F3 block is not unique (found %d)" % text.count(OLD_MAIN))
    text = text.replace(OLD_MAIN, new)
    with io.open(REPORT, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    print("updated §F2/§F3/§F4 of %s (%d bytes)" % (REPORT, len(text.encode("utf-8"))))


if __name__ == "__main__":
    main()
