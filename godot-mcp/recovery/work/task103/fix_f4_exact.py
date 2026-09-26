#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-103: make F4 exact about *which* file is left dirty.

`git_commit.ps1` writes its own stdout/stderr pair, then runs `git add -A` + commit:
so the `.out.txt` it has just written is taken *into* that commit, and only the
`.err.txt` (written as the commit ran, i.e. after the index was built) is left
modified. F4 said "a pair"; it is one file, and it now says so with a pattern rather
than a name that the next commit would make stale.
"""

import io
import sys

REPORT = r"F:\moonbit-hof-rs\godot-mcp\recovery\reports\TASK-103-REPORT.md"

OLD = """**收尾之后，主仓工作树里剩下的只有「最后一次提交的提交助手自己在提交之后写的那一对日志」**：
先出现的是 housekeeping 提交 `85fe8ca` 留下的 `logs/git-main-housekeeping.{out,err}.txt`，
最后一次是**本报告这一版所在的提交**留下的 `logs/git-main-final.{out,err}.txt`
（`.err.txt` 里是 git 关于 CRLF 的警告文字，不是错误）。"""

NEW = """**收尾之后，主仓工作树里剩下的只有一个文件**：**最后一次提交的提交助手自己写的那一个 `.err.txt`**
（文件名形如 `logs/git-main-<tag>.err.txt`，内容是 git 关于 CRLF 的警告文字，不是错误）。
为什么是**一个**而不是一对：`git_commit.ps1` 先写自己的 stdout/stderr、再 `git add -A`，
所以它刚写下的 `.out.txt` 被那次提交**收进去了**，而 `.err.txt` 是提交**执行期间**写的、落在索引之后，因此留在工作树里。"""


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
