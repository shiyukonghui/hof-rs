#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-103: the last F4 patch, with the boundary measured rather than reasoned about.

Measured after the final commit: the helper's **pair** is left modified, not one file.
`git_commit.ps1` writes its own stdout/stderr, runs `git add -A` and commits, and then
runs `git log --oneline -3` + `git status --short` **into the same stdout handle** — so
both the `.out.txt` (the post-commit lines) and the `.err.txt` (the warnings the status
run emits) change after the commit they belong to.

F4 now states that, with a file-name pattern instead of a tag that the next commit
would make stale.
"""

import io
import sys

REPORT = r"F:\moonbit-hof-rs\godot-mcp\recovery\reports\TASK-103-REPORT.md"

OLD = """**收尾之后，主仓工作树里剩下的只有一个文件**：**最后一次提交的提交助手自己写的那一个 `.err.txt`**
（文件名形如 `logs/git-main-<tag>.err.txt`，内容是 git 关于 CRLF 的警告文字，不是错误）。
为什么是**一个**而不是一对：`git_commit.ps1` 先写自己的 stdout/stderr、再 `git add -A`，
所以它刚写下的 `.out.txt` 被那次提交**收进去了**，而 `.err.txt` 是提交**执行期间**写的、落在索引之后，因此留在工作树里。"""

NEW = """**收尾之后，主仓工作树里剩下的是「最后一次提交的提交助手自己写的那一对日志」**：
文件名形如 `logs/git-main-<tag>.out.txt` 与 `logs/git-main-<tag>.err.txt`
（`git status --short` 会把它们报成 ` M`；`.err.txt` 的内容是 git 关于 CRLF 的警告文字，不是错误）。

为什么必然是**一对**、而且必然落在它们所属那次提交**之后**（本轮实测，不是推理）：
`git_commit.ps1` 先写自己的 stdout/stderr，再 `git add -A` + `git commit`，提交之后**又往同一个 stdout 句柄里**
写 `GIT_EXIT`、`git log --oneline -3` 与 `git status --short` —— 于是 `.out.txt` 因为这几行而变、`.err.txt` 因为那条
`git status` 触发的 CRLF 警告而变。改名不做提交助手就不成立；改名做第 N 次 housekeeping 只会换出第 N+1 对同名新文件。
TASK-102 遇到过同一个循环并同样如实记录。**故到此为止，不再提交。**"""


def main():
    with io.open(REPORT, encoding="utf-8", newline="") as handle:
        text = handle.read()
    if text.count(OLD) != 1:
        sys.exit("FATAL: the F4 paragraph is not unique (found %d)" % text.count(OLD))
    text = text.replace(OLD, NEW)
    with io.open(REPORT, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    print("patched F4 of %s (%d bytes)" % (REPORT, len(text.encode("utf-8"))))


if __name__ == "__main__":
    main()
