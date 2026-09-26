#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-104 correction pass 2: the --import cumulative denominator.

The milestone was written as "3/48, 25 imports since TASK-099 with 0
recurrences", derived from TASK-099's own 3/23 mark. That base is wrong: the
ledger shows the running counter going 3/13 -> 3/17 -> 3/23 -> 3/28 (TASK-102)
-> 3/34 (TASK-103), i.e. TASK-099's 3/23 is the mark AT THE END OF TASK-099, not
before TASK-100. The correct arithmetic is therefore 3/34 + four TASK-104 imports
= 3/38, and fifteen imports since the 3/23 mark (23 -> 28 -> 34 -> 38), not
twenty-five. Exact-match-one per edit.
"""

import io
import os
import sys

ROOT = r"F:\moonbit-hof-rs"
LOG = os.path.join(ROOT, "godot-mcp", "GAME-LOOP-LOG.md")
REPORT = os.path.join(ROOT, "godot-mcp", "recovery", "reports", "TASK-104-REPORT.md")

NEW_LOG = (
    u"* **崩溃形态（`exit=-1073741819` / `0xC0000005`，stderr 只有 `Parameter \"singleton\" is null.`）**：\n"
    u"  TASK-099 留档时是 **3/23**，此后台账口径按轮推进 **3/28**（TASK-102）→ **3/34**（TASK-103）→\n"
    u"  **本轮 3/38**：TASK-104 的 **4 次导入全部 `IMPORT_EXIT=0`**、其中 3 次 `import.stderr.txt` 0 字节。\n"
    u"  也就是说：**3/23 这个标记之后，台账口径走过 23→28→34→38 共 15 次导入、0 次复现。**\n"
    u"  （不要把 TASK-099 的 3/23 当成 TASK-100 之前的基数 —— 它是那一轮**结束时**的标记，这才是台账里\n"
    u"  `3/13 → 3/17 → 3/23 → 3/28 → 3/34` 这条链的含义。）"
)

OLD_LOG = (
    u"* **崩溃形态（`exit=-1073741819` / `0xC0000005`，stderr 只有 `Parameter \"singleton\" is null.`）**：\n"
    u"  TASK-099 留档时是 **3/23**；TASK-100 的 4 次、TASK-101 的 6 次、TASK-102 的 5 次、TASK-103 的 6 次、\n"
    u"  TASK-104 的 **4 次**全部 `IMPORT_EXIT=0`。**累计 3/48，TASK-099 之后 25 次导入 0 次复现。**"
)

EDITS = {
    REPORT: [
        (u"**崩溃形态累计 3/48**（TASK-099 之后 25 次导入 0 次复现）。",
         u"**崩溃形态台账口径**：TASK-099 留档 **3/23**，此后按轮推进 3/28（TASK-102）→ 3/34（TASK-103）→\n"
         u"   **本轮 3/38**（本轮 4 次导入全部 `IMPORT_EXIT=0`）；即 3/23 这个标记之后共 **15 次导入、0 次复现**。"),
    ],
}

# Every remaining "3/48" in the report is the same wrong denominator (the §0 row
# and the §G summary line); they are replaced together and the count asserted.
COUNTED = {
    REPORT: [(u"3/48", u"3/38", 1)],
}


def main():
    for path, edits in EDITS.items():
        with io.open(path, "r", encoding="utf-8", newline="") as handle:
            text = handle.read()
        for index, (old, new) in enumerate(edits):
            if old == new:
                continue
            count = text.count(old)
            if count != 1:
                raise SystemExit("REFUSED: %s edit #%d matched %d time(s)" % (os.path.basename(path), index, count))
            text = text.replace(old, new)
        for old, new, expected in COUNTED.get(path, []):
            count = text.count(old)
            if count != expected:
                raise SystemExit("REFUSED: %s counted replace %r matched %d time(s), expected %d"
                                 % (os.path.basename(path), old, count, expected))
            text = text.replace(old, new)
            print("  %s: replaced %r -> %r (%d occurrence(s))" % (os.path.basename(path), old, new, count))
        with io.open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        print("corrected %s" % path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
