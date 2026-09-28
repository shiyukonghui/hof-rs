### arm `model` -- rounds: t140-jev-v3-w90-r1, t140-jev-v3-w90-r2   other-window recordings: t139-jev-v3-w30   same-window other batch: t139-jev-v3-w90

| game | t140-jev-v3-w90-r1 | t140-jev-v3-w90-r2 | t139-jev-v3-w30 | t139-jev-v3-w90 | UNSTABLE | SENSITIVE | CROSS-BATCH |
|---|---|---|---|---|---|---|---|
| `asteroids` | `PASS`* | `PASS(baseline only)` | `PASS`* | `FAIL` | **UNSTABLE** | **SENSITIVE** | **DIFFERS** |
| `bomberman` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` |  |  |  |
| `breakout` | `FAIL` | `FAIL` | `FAIL` | `FAIL` |  |  |  |
| `flappy` | `FAIL` | `FAIL` | `INCONCLUSIVE` | `INCONCLUSIVE` |  | **SENSITIVE** | **DIFFERS** |
| `frogger` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` |  |  |  |
| `game2048` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` |  |  |  |
| `lunarlander` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` |  |  |  |
| `match3` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` |  |  |  |
| `minesweeper` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` |  |  |  |
| `missilecommand` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` |  |  |  |
| `pacman` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` |  |  |  |
| `platformer` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` |  |  |  |
| `pong` | `PASS(baseline only)` | `PASS(baseline only)` | `FAIL` | `PASS(baseline only)` |  | **SENSITIVE** |  |
| `puzzlebobble` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` |  |  |  |
| `rtype` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` |  |  |  |
| `snake` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` |  |  |  |
| `sokoban` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` |  |  |  |
| `spaceinvaders` | `INCONCLUSIVE` | `INCONCLUSIVE` | `FAIL` | `INCONCLUSIVE` |  | **SENSITIVE** |  |
| `tetris` | `PASS`* | `PASS`* | `PASS`* | `PASS`* |  |  |  |
| `towerdefense` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` | `INCONCLUSIVE` |  |  |  |

(`*` = `counts_as_pass: true`; a class without it is reported but never counted.  `UNSTABLE` = the two rounds of THIS batch at the SAME window disagree; `SENSITIVE` = two DIFFERENT windows disagree (either TASK-139's own two rungs, or this batch's w90 against a TASK-139 recording); `CROSS-BATCH` = this batch's w90 reading differs from TASK-139's w90 reading of the same arm -- a third independent reading at the reporting window that does NOT agree with the two TASK-139 had.)
