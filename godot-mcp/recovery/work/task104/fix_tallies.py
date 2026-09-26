#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-104 correction pass: the assertion-tally decomposition was stated as
"99 PASS + 1 declared boundary + 1 screen text = 101", which is off by one
category. The measured decomposition (re-derived from the run's own response
files, one class per PASS) is:

    R-Type          101 PASS = 99 node-state + 1 screen_text + 1 scenario assert
    Puzzle Bobble    87 PASS = 85 node-state + 1 screen_text + 1 scenario assert
    Lunar Lander    150 PASS = 148 node-state + 1 screen_text + 1 scenario assert

with the one declared -32001 boundary refusal counted in NO column. This script
fixes the wording in the report and in the ledger rows, and each replacement is
asserted to happen exactly once so a silent no-op is impossible.
"""

import io
import os
import sys

ROOT = r"F:\moonbit-hof-rs"
LOG = os.path.join(ROOT, "godot-mcp", "GAME-LOOP-LOG.md")
REPORT = os.path.join(ROOT, "godot-mcp", "recovery", "reports", "TASK-104-REPORT.md")

EDITS = {
    LOG: [
        (u"断言 **99 PASS + 1 \u6761\u58f0\u660e\u7684\u8fb9\u754c\u5931\u8d25**\uff08`-32001`\uff09\uff0b **1 \u6761\u5c4f\u5e55\u6587\u672c PASS**\uff08`WAVE CLEARED`\uff09= **101 PASS / 0 FAIL**\u3002",
         u"断言 **101 PASS / 0 FAIL** = 99 \u6761\u5e26\u5c5e\u6027\u7684 node-state \uff0b **1 \u6761\u5c4f\u5e55\u6587\u672c PASS**\uff08`WAVE CLEARED`\uff09"
         u"\uff0b 1 \u6761 `run_test_scenario` \u81ea\u5e26\u7684\u65ad\u8a00\uff0c**\u53e6\u6709 1 \u6761\u58f0\u660e\u7684\u8fb9\u754c\u5931\u8d25**\uff08`-32001`\uff0c\u4e0d\u8ba1\u5165 PASS\uff09\u3002"),
        (u"断言 **85 PASS + 1 \u6761\u58f0\u660e\u7684\u8fb9\u754c\u5931\u8d25**\uff08`-32001`\uff09\uff0b **1 \u6761\u5c4f\u5e55\u6587\u672c PASS**\uff08`BOARD CLEARED`\uff09= **87 PASS / 0 FAIL**\u3002",
         u"断言 **87 PASS / 0 FAIL** = 85 \u6761\u5e26\u5c5e\u6027\u7684 node-state \uff0b **1 \u6761\u5c4f\u5e55\u6587\u672c PASS**\uff08`BOARD CLEARED`\uff09"
         u"\uff0b 1 \u6761\u573a\u666f\u65ad\u8a00\uff0c**\u53e6\u6709 1 \u6761\u58f0\u660e\u7684\u8fb9\u754c\u5931\u8d25**\uff08`-32001`\uff09\u3002"),
        (u"断言 **148 PASS + 1 \u6761\u58f0\u660e\u7684\u8fb9\u754c\u5931\u8d25**\uff08`-32001`\uff09\uff0b **1 \u6761\u5c4f\u5e55\u6587\u672c PASS**\uff08`THE EAGLE HAS LANDED`\uff09= **150 PASS / 0 FAIL**\u3002",
         u"断言 **150 PASS / 0 FAIL** = 148 \u6761\u5e26\u5c5e\u6027\u7684 node-state \uff0b **1 \u6761\u5c4f\u5e55\u6587\u672c PASS**\uff08`THE EAGLE HAS LANDED`\uff09"
         u"\uff0b 1 \u6761\u573a\u666f\u65ad\u8a00\uff0c**\u53e6\u6709 1 \u6761\u58f0\u660e\u7684\u8fb9\u754c\u5931\u8d25**\uff08`-32001`\uff09\u3002"),
        (u"\u4e09\u6b21 `running_game_get_scene_tree` \u5171 **214 \u4e2a\u8282\u70b9\u540d 0 \u4e2a `@` \u5f00\u5934**",
         u"\u4e09\u6b21\u573a\u666f\u6811\u8bfb\u53d6\uff08\u7f16\u8f91\u5668\u76f8 1 + \u6e38\u620f\u76f8 2\uff09\u5171 **214 \u4e2a\u8282\u70b9\u540d 0 \u4e2a `@` \u5f00\u5934**"),
        (u"\u6811\u91cc **214 \u4e2a\u8282\u70b9\u540d 0 \u4e2a `@` \u5f00\u5934**",
         u"\u4e09\u6b21\u573a\u666f\u6811\u8bfb\u53d6\u5171 **214 \u4e2a\u8282\u70b9\u540d 0 \u4e2a `@` \u5f00\u5934**"),
        (u"\u6811\u91cc **136 \u4e2a\u8282\u70b9\u540d 0 \u4e2a `@` \u5f00\u5934**",
         u"\u4e09\u6b21\u573a\u666f\u6811\u8bfb\u53d6\u5171 **136 \u4e2a\u8282\u70b9\u540d 0 \u4e2a `@` \u5f00\u5934**"),
    ],
    REPORT: [
        (u"\uff1b\u65ad\u8a00 **99 PASS + 1 \u6761\u58f0\u660e\u7684\u8fb9\u754c\u5931\u8d25**\uff08`-32001`\uff09\uff0b 1 \u6761\u5c4f\u5e55\u6587\u672c = **101 PASS / 0 FAIL**\uff1b",
         u"\uff1b\u65ad\u8a00 **101 PASS / 0 FAIL** = 99 \u6761\u5e26\u5c5e\u6027\u7684 node-state \uff0b 1 \u6761\u5c4f\u5e55\u6587\u672c \uff0b 1 \u6761\u573a\u666f\u81ea\u5e26\u65ad\u8a00\uff0c"
         u"**\u53e6\u6709 1 \u6761\u58f0\u660e\u7684\u8fb9\u754c\u5931\u8d25**\uff08`-32001`\uff0c\u4e0d\u8ba1\u5165 PASS\uff09\uff1b"),
        (u"\uff1b\u65ad\u8a00 **85 PASS + 1 \u6761\u58f0\u660e\u7684\u8fb9\u754c\u5931\u8d25** \uff0b 1 \u6761\u5c4f\u5e55\u6587\u672c = **87 PASS / 0 FAIL**\uff1b",
         u"\uff1b\u65ad\u8a00 **87 PASS / 0 FAIL** = 85 \u6761\u5e26\u5c5e\u6027\u7684 node-state \uff0b 1 \u6761\u5c4f\u5e55\u6587\u672c \uff0b 1 \u6761\u573a\u666f\u81ea\u5e26\u65ad\u8a00\uff0c"
         u"**\u53e6\u6709 1 \u6761\u58f0\u660e\u7684\u8fb9\u754c\u5931\u8d25**\uff08`-32001`\uff0c\u4e0d\u8ba1\u5165 PASS\uff09\uff1b"),
        (u"\uff1b\u65ad\u8a00 **148 PASS + 1 \u6761\u58f0\u660e\u7684\u8fb9\u754c\u5931\u8d25** \uff0b 1 \u6761\u5c4f\u5e55\u6587\u672c = **150 PASS / 0 FAIL**\uff1b",
         u"\uff1b\u65ad\u8a00 **150 PASS / 0 FAIL** = 148 \u6761\u5e26\u5c5e\u6027\u7684 node-state \uff0b 1 \u6761\u5c4f\u5e55\u6587\u672c \uff0b 1 \u6761\u573a\u666f\u81ea\u5e26\u65ad\u8a00\uff0c"
         u"**\u53e6\u6709 1 \u6761\u58f0\u660e\u7684\u8fb9\u754c\u5931\u8d25**\uff08`-32001`\uff0c\u4e0d\u8ba1\u5165 PASS\uff09\uff1b"),
        (u"* **\u65ad\u8a00**\uff1aR-Type **101 PASS / 0 FAIL**\uff0899 \u6761 node-state + 1 \u6761\u58f0\u660e\u7684\u8fb9\u754c\u5931\u8d25 + 1 \u6761\u5c4f\u5e55\u6587\u672c `WAVE CLEARED`\uff09\uff1b\n"
         u"  Puzzle Bobble **87 PASS / 0 FAIL**\uff0885 + 1 + 1\uff0c\u5c4f\u5e55\u6587\u672c `BOARD CLEARED`\uff09\uff1b\n"
         u"  Lunar Lander **150 PASS / 0 FAIL**\uff08148 + 1 + 1\uff0c\u5c4f\u5e55\u6587\u672c `THE EAGLE HAS LANDED`\uff09\u3002\u9010\u5c5e\u6027\u5206\u680f\u89c1 `logs\\assert-*.txt`\u3002",
         u"* **\u65ad\u8a00**\uff08\u5206\u89e3\u9010\u6b3e\u7528\u811a\u672c\u6838\u5bf9\u8fc7\uff1a`assert_summary.py` \u7684\u6bcf\u4e00\u5904 PASS \u90fd\u5f52\u5230\u5b83\u81ea\u5df1\u90a3\u4e00\u7c7b\uff09\uff1a\n"
         u"  R-Type **101 PASS / 0 FAIL** = 99 \u6761\u5e26\u5c5e\u6027\u7684 `running_game_assert_node_state` \uff0b 1 \u6761\u5c4f\u5e55\u6587\u672c\uff08`WAVE CLEARED`\uff09\n"
         u"  \uff0b 1 \u6761 `running_game_run_test_scenario` \u81ea\u5e26\u7684\u65ad\u8a00\uff1b**\u53e6\u6709 1 \u6761\u58f0\u660e\u7684\u8fb9\u754c\u5931\u8d25**\uff08`-32001`\uff0c\u4e0d\u8ba1\u5165 PASS\uff09\u3002\n"
         u"  Puzzle Bobble **87 PASS / 0 FAIL** = 85 + 1 \u6761\u5c4f\u5e55\u6587\u672c\uff08`BOARD CLEARED`\uff09+ 1 \u6761\u573a\u666f\u65ad\u8a00\uff0c\u53e6\u6709 1 \u6761\u8fb9\u754c\u5931\u8d25\u3002\n"
         u"  Lunar Lander **150 PASS / 0 FAIL** = 148 + 1 \u6761\u5c4f\u5e55\u6587\u672c\uff08`THE EAGLE HAS LANDED`\uff09+ 1 \u6761\u573a\u666f\u65ad\u8a00\uff0c\u53e6\u6709 1 \u6761\u8fb9\u754c\u5931\u8d25\u3002\n"
         u"  \u9010\u5c5e\u6027\u5206\u680f\u89c1 `logs\\assert-*.txt`\u3002"),
        (u"\u6811\u91cc **214 \u4e2a\u8282\u70b9\u540d 0 \u4e2a `@` \u5f00\u5934** | `runs\\rtype",
         u"\u4e09\u6b21\u573a\u666f\u6811\u8bfb\u53d6\u5171 **214 \u4e2a\u8282\u70b9\u540d 0 \u4e2a `@` \u5f00\u5934** | `runs\\rtype"),
        (u"\u6811\u91cc **214 \u4e2a\u8282\u70b9\u540d 0 \u4e2a `@` \u5f00\u5934** | `runs\\puzzlebobble",
         u"\u4e09\u6b21\u573a\u666f\u6811\u8bfb\u53d6\u5171 **214 \u4e2a\u8282\u70b9\u540d 0 \u4e2a `@` \u5f00\u5934** | `runs\\puzzlebobble"),
        (u"\u6811\u91cc **136 \u4e2a\u8282\u70b9\u540d 0 \u4e2a `@` \u5f00\u5934** | `runs\\lunarlander",
         u"\u4e09\u6b21\u573a\u666f\u6811\u8bfb\u53d6\u5171 **136 \u4e2a\u8282\u70b9\u540d 0 \u4e2a `@` \u5f00\u5934** | `runs\\lunarlander"),
    ],
}


def main():
    for path, edits in EDITS.items():
        with io.open(path, "r", encoding="utf-8", newline="") as handle:
            text = handle.read()
        for index, (old, new) in enumerate(edits):
            count = text.count(old)
            if count != 1:
                raise SystemExit("REFUSED: %s edit #%d matched %d time(s)" % (os.path.basename(path), index, count))
            text = text.replace(old, new)
        with io.open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        print("corrected %s (%d replacement(s))" % (path, len(edits)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
