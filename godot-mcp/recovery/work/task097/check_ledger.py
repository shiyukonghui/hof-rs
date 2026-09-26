# TASK-097: sanity-check the ledger table (column count per row) and the presence
# of the numbers this task put there.
import io

PATH = r"F:\moonbit-hof-rs\godot-mcp\GAME-LOOP-LOG.md"
text = io.open(PATH, encoding="utf-8").read()
lines = text.splitlines()
rows = [line for line in lines if line.startswith("| ") and not set(line) <= set("|- ")]
header = rows[0]
columns = header.count("|")
print("header columns: %d" % columns)
bad = 0
for row in rows[1:]:
    if row.count("|") != columns:
        bad += 1
        print("COLUMN MISMATCH (%d): %s" % (row.count("|"), row[:80]))
print("data rows: %d, mismatched: %d" % (len(rows) - 1, bad))
for needle in ("| 1 | Pong", "| 2 | Breakout", "| 3 | Snake", "| 4 | Tetris", "| 5 | Space Invaders",
               "14/74", "14/89", "13/102", "12/59", "D-1 结案与副本层清理存证", "TASK-097 已结案"):
    print("%-28s %s" % (needle, "present" if needle in text else "MISSING"))
print("still says unavailable in a table cell: %s" % ("不可得（D-1）" in text))
