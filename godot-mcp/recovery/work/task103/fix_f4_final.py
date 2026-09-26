#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-103: the last report patch before the final commit.

It has to describe a state that will hold *after* the commit it is part of, so it
names the file pair that commit's own helper will leave behind (the tag is chosen
here: `main-final`) and points at the log rather than inventing a hash for a commit
that does not exist yet.
"""

import io
import sys

REPORT = r"F:\moonbit-hof-rs\godot-mcp\recovery\reports\TASK-103-REPORT.md"

OLD = """**housekeeping 提交之后，主仓工作树里还剩两个文件**：

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

NEW = """**收尾之后，主仓工作树里剩下的只有「最后一次提交的提交助手自己在提交之后写的那一对日志」**：
先出现的是 housekeeping 提交 `85fe8ca` 留下的 `logs/git-main-housekeeping.{out,err}.txt`，
最后一次是**本报告这一版所在的提交**留下的 `logs/git-main-final.{out,err}.txt`
（`.err.txt` 里是 git 关于 CRLF 的警告文字，不是错误）。

这是**收尾自身的边界**，不是漏提交：`git_commit.ps1` 按铁律 1 用
`Start-Process -RedirectStandardOutput/-RedirectStandardError` 拥有自己的输出，所以它写的每个日志都必然落在它所属的那次提交**之后**；
再做一次 housekeeping 只会产生同样的一对新文件。TASK-102 遇到过同一个循环并同样如实记录。**故到此为止，不再提交。**

两仓的最终 HEAD：

| 仓 | HEAD | 工作树 |
|---|---|---|
| 主仓 `F:\\moonbit-hof-rs`（`master`） | `85fe8ca`（housekeeping）→ 之后是**报告修订提交**（`docs(godot-mcp): TASK-103 - …`，即本文件这一版所在的提交）。它自己的哈希在提交之后才存在，逐字记在 `logs/git-main-final.out.txt` 的 `git log --oneline -3` 段里 | 只剩该提交的助手自有日志一对 |
| 引擎仓 `godot\\`（`feature/mcp-server-module-rebuild`） | `1f9d0cb1c983301d4efa575c16986c551df23600` | **空**，且 HEAD == `refs/remotes/origin/feature/mcp-server-module-rebuild`（push 已生效） |
"""


def main():
    with io.open(REPORT, encoding="utf-8", newline="") as handle:
        text = handle.read()
    if text.count(OLD) != 1:
        sys.exit("FATAL: the F4 body is not unique (found %d)" % text.count(OLD))
    text = text.replace(OLD, NEW)
    with io.open(REPORT, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    print("patched F4 of %s (%d bytes)" % (REPORT, len(text.encode("utf-8"))))


if __name__ == "__main__":
    main()
