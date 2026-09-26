#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-103: state the closing boundary of the working tree exactly, instead of
claiming a clean tree the last commit cannot produce.

The commit helper owns its own stdout/stderr by design (iron rule 1: no shell
redirection), so the files it writes land *after* the commit they belong to. One
housekeeping commit therefore always leaves exactly one more pair dirty. TASK-102 hit
the same recursion and restated the boundary; this does the same, with the two file
names it actually leaves behind.
"""

import io
import os
import sys

REPORT = r"F:\moonbit-hof-rs\godot-mcp\recovery\reports\TASK-103-REPORT.md"

OLD = """### F4 快照之后

快照记录的是「提交完成、housekeeping 尚未发生」的那一瞬。§F2 列出的那 6 条助手自有文件由 housekeeping 提交收尾；
之后两仓的工作树都为空，两仓 HEAD 分别是主仓 `5a364575641a6eff7422fbc990348ca8ca781dee` 与引擎仓
`1f9d0cb1c983301d4efa575c16986c551df23600`（= 远端）。
"""

NEW = """### F4 快照之后，以及收尾边界的如实说明

快照记录的是「第一次提交完成、housekeeping 尚未发生」的那一瞬（主仓 `5a36457564…`）。§F2 列出的那 6 条助手自有文件
由 housekeeping 提交 `85fe8ca` 收尾。

**housekeeping 提交之后，主仓工作树里还剩两个文件**：

```
 M godot-mcp/recovery/work/task103/logs/git-main-housekeeping.err.txt
 M godot-mcp/recovery/work/task103/logs/git-main-housekeeping.out.txt
```

它们是**提交助手自己在提交之后写的**那一对 stdout/stderr 日志（1 017 B 的 `.err.txt` 全是 git 关于 CRLF 的警告文字，
没有错误）。这是**收尾自身的边界**，不是漏提交：`git_commit.ps1` 按铁律 1 用
`Start-Process -RedirectStandardOutput/-RedirectStandardError` 拥有自己的输出，所以它写的每个日志都必然落在它所属的那次提交**之后**；
再做第 3 次 housekeeping 只会产生同样的一对新文件。TASK-102 遇到过同一个循环并同样如实记录。**故到此为止，不再提交。**

两仓的最终 HEAD：

| 仓 | HEAD | 工作树 |
|---|---|---|
| 主仓 `F:\\moonbit-hof-rs`（`master`） | `85fe8ca4…`（`git log --oneline -3`：`85fe8ca` → `5a36457` → `9733cae`） | 只剩上面那一对助手自有日志 |
| 引擎仓 `godot\\`（`feature/mcp-server-module-rebuild`） | `1f9d0cb1c983301d4efa575c16986c551df23600` | **空**，且 HEAD == `refs/remotes/origin/feature/mcp-server-module-rebuild`（push 已生效） |
"""


def main():
    with io.open(REPORT, encoding="utf-8", newline="") as handle:
        text = handle.read()
    if text.count(OLD) != 1:
        sys.exit("FATAL: the F4 block is not unique (found %d)" % text.count(OLD))
    text = text.replace(OLD, NEW)
    with io.open(REPORT, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    print("updated F4 of %s (%d bytes)" % (REPORT, len(text.encode("utf-8"))))


if __name__ == "__main__":
    main()
