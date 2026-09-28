### arm `scripted` -- rounds: t140-scripted-w90-r1, t140-scripted-w90-r2   other-window recordings: t139-scripted-w30   same-window other batch: t139-scripted-w90

| game | t140-scripted-w90-r1 | t140-scripted-w90-r2 | t139-scripted-w30 | t139-scripted-w90 | UNSTABLE | SENSITIVE | CROSS-BATCH |
|---|---|---|---|---|---|---|---|
| `asteroids` | `PASS`* | `PASS`* | `PASS`* | `PASS`* |  |  |  |
| `bomberman` | `PASS`* | `PASS`* | `INCONCLUSIVE` | `INCONCLUSIVE` |  | **SENSITIVE** | **DIFFERS** |
| `breakout` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | `FAIL` |  |  | **DIFFERS** |
| `flappy` | `PASS(baseline only)` | `PASS(baseline only)` | `INCONCLUSIVE` | `INCONCLUSIVE` |  | **SENSITIVE** | **DIFFERS** |
| `frogger` | `PASS`* | `PASS`* | `INCONCLUSIVE` | `INCONCLUSIVE` |  | **SENSITIVE** | **DIFFERS** |
| `game2048` | `PASS`* | `PASS`* | `PASS`* | `PASS`* |  |  |  |
| `lunarlander` | `PASS`* | `PASS`* | `PASS`* | `PASS`* |  |  |  |
| `match3` | `PASS`* | `PASS`* | `PASS`* | `PASS`* |  |  |  |
| `minesweeper` | `PASS`* | `PASS`* | `PASS`* | `PASS`* |  |  |  |
| `missilecommand` | `PASS`* | `PASS`* | `PASS`* | `PASS`* |  |  |  |
| `pacman` | `PASS`* | `PASS`* | `PASS`* | `PASS`* |  |  |  |
| `platformer` | `INCONCLUSIVE` | `INCONCLUSIVE` | `PASS`* | `INCONCLUSIVE` |  | **SENSITIVE** |  |
| `pong` | `PASS`* | `PASS`* | `PASS(baseline only)` | `PASS`* |  | **SENSITIVE** |  |
| `puzzlebobble` | `PASS`* | `PASS`* | `PASS`* | `PASS`* |  |  |  |
| `rtype` | `PASS`* | `PASS`* | `PASS`* | `PASS`* |  |  |  |
| `snake` | `PASS`* | `PASS`* | `PASS`* | `PASS`* |  |  |  |
| `sokoban` | `PASS`* | `PASS`* | `PASS`* | `PASS`* |  |  |  |
| `spaceinvaders` | `PASS`* | `PASS`* | `PASS`* | `PASS`* |  |  |  |
| `tetris` | `PASS`* | `PASS`* | `PASS`* | `PASS`* |  |  |  |
| `towerdefense` | `PASS`* | `PASS`* | `PASS`* | `PASS`* |  |  |  |

(`*` = `counts_as_pass: true`; a class without it is reported but never counted.  `UNSTABLE` = the two rounds of THIS batch at the SAME window disagree; `SENSITIVE` = two DIFFERENT windows disagree (either TASK-139's own two rungs, or this batch's w90 against a TASK-139 recording); `CROSS-BATCH` = this batch's w90 reading differs from TASK-139's w90 reading of the same arm -- a third independent reading at the reporting window that does NOT agree with the two TASK-139 had.)
