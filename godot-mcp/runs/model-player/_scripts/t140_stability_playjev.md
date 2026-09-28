### arm `playjev` -- rounds: t140-playjev-v3-w90-r1, t140-playjev-v3-w90-r2   other-window recordings: t139-playjev-v3-w30   same-window other batch: (none)

| game | t140-playjev-v3-w90-r1 | t140-playjev-v3-w90-r2 | t139-playjev-v3-w30 | UNSTABLE | SENSITIVE | CROSS-BATCH |
|---|---|---|---|---|---|---|
| `asteroids` | `PASS`* | `PASS`* | `INCONCLUSIVE` |  | **SENSITIVE** |  |
| `game2048` | `PASS`* | `PASS`* | `PASS`* |  |  |  |
| `match3` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` |  |  |  |
| `minesweeper` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` |  |  |  |
| `pacman` | `FAIL` | `FAIL` | `FAIL` |  |  |  |
| `pong` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` |  |  |  |
| `rtype` | `PASS`* | `PASS`* | `PASS`* |  |  |  |
| `snake` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` |  |  |  |
| `sokoban` | `PASS`* | `PASS`* | `PASS`* |  |  |  |
| `tetris` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` |  |  |  |

(`*` = `counts_as_pass: true`; a class without it is reported but never counted.  `UNSTABLE` = the two rounds of THIS batch at the SAME window disagree; `SENSITIVE` = two DIFFERENT windows disagree (either TASK-139's own two rungs, or this batch's w90 against a TASK-139 recording); `CROSS-BATCH` = this batch's w90 reading differs from TASK-139's w90 reading of the same arm -- a third independent reading at the reporting window that does NOT agree with the two TASK-139 had.)
