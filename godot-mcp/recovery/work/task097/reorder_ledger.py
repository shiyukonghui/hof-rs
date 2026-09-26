# TASK-097: put the two ledger rows back in numeric order (the Space Invaders row
# was inserted before the Tetris row by an edit that anchored on Tetris' header).
import io

PATH = r"F:\moonbit-hof-rs\godot-mcp\GAME-LOOP-LOG.md"
text = io.open(PATH, encoding="utf-8").read()
lines = text.splitlines()
si = [i for i, line in enumerate(lines) if line.startswith("| 5 | Space Invaders")]
te = [i for i, line in enumerate(lines) if line.startswith("| 4 | Tetris")]
if len(si) != 1 or len(te) != 1:
    raise SystemExit("FATAL: expected exactly one SI row and one Tetris row (si=%s te=%s)" % (si, te))
si_index, te_index = si[0], te[0]
if si_index < te_index:
    row = lines.pop(si_index)
    te_index -= 1
    lines.insert(te_index + 1, row)
    io.open(PATH, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print("swapped: SI row moved after the Tetris row")
else:
    print("already ordered")
