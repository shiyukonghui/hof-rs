# TASK-116 — 可玩性缺陷登记（PLAYABILITY-DEFECTS）

> 生成时间：2026-09-27 13:46:56 ｜ 每一条都由 `runs/playability/<game>/gate.json` 的机检事实或源码 `file:line` 支撑。
> 现象 / 证据 / 根因 / 建议修法，四栏齐全；没有「应该可以」的转述。
> **登记来源是修复前那一轮**（`runs/playability/playability.before.json`）；每条后面的
> 「复跑状态」来自修复后同一道门的复跑，所以本文件既记录了发现了什么，也记录了修没修掉。

## 汇总

| 类 | 数量 | 已修复（复跑验证） | 仍存在 | 说明 |
|---|---|---|---|---|
| D1 | 16 | 16 | 0 | 玩家输入默认关闭（`PollInput = false`，且 `_Ready()` 里的 `Reset*` 又关一次）——本轮最严重的系统性缺陷 |
| D11 | 29 | 29 | 0 | 玩家需要的能力没有任何动作提供（P6 逐条） |
| D2 | 4 | 4 | 0 | 代码读取了 InputMap 未声明的动作 |
| D3 | 16 | 16 | 0 | 已声明的控制按下去没有可归因的效果 |
| D5 | 19 | 19 | 0 | README 没有玩法章节，操作不可发现 |

总计 **84** 条，其中复跑验证已修复 **84** 条。

涉及的工程（19 款）：`asteroids`, `bomberman`, `breakout`, `flappy`, `frogger`, `game2048`, `lunarlander`, `match3`, `minesweeper`, `missilecommand`, `pacman`, `platformer`, `puzzlebobble`, `rtype`, `snake`, `sokoban`, `spaceinvaders`, `tetris`, `towerdefense`

## D1 — 玩家输入默认关闭（`PollInput = false`，且 `_Ready()` 里的 `Reset*` 又关一次）——本轮最严重的系统性缺陷（16 条）

### `asteroids` — player input was switched off in the shipped build (fixed; registered from the before-run evidence)

- **严重度**：blocker
- **现象**：in the before run not one of the 4 declared actions responded on either injected channel; the game listened to nothing
- **证据**：
  - `projects/asteroids/src/AsteroidsGame.cs:150  [Export] public bool PollInput = true;   (this line now reads `= true`; `git diff` of the task's commit shows the flip)`
  - `before-run P2: 0/4 declared actions produced a state or pixel change within 45 frames; key-event channel 0/4, action-state channel 0/4`
- **根因**：`projects/asteroids/src/AsteroidsGame.cs:150`
- **建议修法**：the field initialiser was flipped to `= true` and the assignment inside the startup `Reset*()` was removed
- **验证方式**：the same game re-run through the gate (P2 is blue in the after run)
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `bomberman` — player input was switched off in the shipped build (fixed; registered from the before-run evidence)

- **严重度**：blocker
- **现象**：in the before run not one of the 3 declared actions responded on either injected channel; the game listened to nothing
- **证据**：
  - `projects/bomberman/src/BombermanGame.cs:223  [Export] public bool PollInput = true;   (this line now reads `= true`; `git diff` of the task's commit shows the flip)`
  - `before-run P2: 0/3 declared actions produced a state or pixel change within 45 frames; key-event channel 0/3, action-state channel 0/3`
- **根因**：`projects/bomberman/src/BombermanGame.cs:223`
- **建议修法**：the field initialiser was flipped to `= true` and the assignment inside the startup `Reset*()` was removed
- **验证方式**：the same game re-run through the gate (P2 is blue in the after run)
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `flappy` — player input was switched off in the shipped build (fixed; registered from the before-run evidence)

- **严重度**：blocker
- **现象**：in the before run not one of the 2 declared actions responded on either injected channel; the game listened to nothing
- **证据**：
  - `projects/flappy/src/FlappyBirdGame.cs:119  [Export] public bool PollInput = true;   (this line now reads `= true`; `git diff` of the task's commit shows the flip)`
  - `before-run P2: 0/2 declared actions produced a state or pixel change within 45 frames; key-event channel 0/2, action-state channel 0/2`
- **根因**：`projects/flappy/src/FlappyBirdGame.cs:119`
- **建议修法**：the field initialiser was flipped to `= true` and the assignment inside the startup `Reset*()` was removed
- **验证方式**：the same game re-run through the gate (P2 is blue in the after run)
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `frogger` — player input was switched off in the shipped build (fixed; registered from the before-run evidence)

- **严重度**：blocker
- **现象**：in the before run not one of the 4 declared actions responded on either injected channel; the game listened to nothing
- **证据**：
  - `projects/frogger/src/FroggerGame.cs:157  [Export] public bool PollInput = true;   (this line now reads `= true`; `git diff` of the task's commit shows the flip)`
  - `before-run P2: 0/4 declared actions produced a state or pixel change within 45 frames; key-event channel 0/4, action-state channel 0/4`
- **根因**：`projects/frogger/src/FroggerGame.cs:157`
- **建议修法**：the field initialiser was flipped to `= true` and the assignment inside the startup `Reset*()` was removed
- **验证方式**：the same game re-run through the gate (P2 is blue in the after run)
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `game2048` — player input was switched off in the shipped build (fixed; registered from the before-run evidence)

- **严重度**：blocker
- **现象**：in the before run not one of the 4 declared actions responded on either injected channel; the game listened to nothing
- **证据**：
  - `projects/game2048/src/Game2048Game.cs:156  [Export] public bool PollInput = true;   (this line now reads `= true`; `git diff` of the task's commit shows the flip)`
  - `before-run P2: 0/4 declared actions produced a state or pixel change within 45 frames; key-event channel 0/4, action-state channel 0/4`
- **根因**：`projects/game2048/src/Game2048Game.cs:156`
- **建议修法**：the field initialiser was flipped to `= true` and the assignment inside the startup `Reset*()` was removed
- **验证方式**：the same game re-run through the gate (P2 is blue in the after run)
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `lunarlander` — player input was switched off in the shipped build (fixed; registered from the before-run evidence)

- **严重度**：blocker
- **现象**：in the before run not one of the 1 declared actions responded on either injected channel; the game listened to nothing
- **证据**：
  - `projects/lunarlander/src/LunarLanderGame.cs:212  [Export] public bool PollInput = true;   (this line now reads `= true`; `git diff` of the task's commit shows the flip)`
  - `before-run P2: 0/1 declared actions produced a state or pixel change within 45 frames; key-event channel 0/1, action-state channel 0/1`
- **根因**：`projects/lunarlander/src/LunarLanderGame.cs:212`
- **建议修法**：the field initialiser was flipped to `= true` and the assignment inside the startup `Reset*()` was removed
- **验证方式**：the same game re-run through the gate (P2 is blue in the after run)
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `match3` — player input was switched off in the shipped build (fixed; registered from the before-run evidence)

- **严重度**：blocker
- **现象**：in the before run not one of the 3 declared actions responded on either injected channel; the game listened to nothing
- **证据**：
  - `projects/match3/src/Match3Game.cs:162  [Export] public bool PollInput = true;   (this line now reads `= true`; `git diff` of the task's commit shows the flip)`
  - `before-run P2: 0/3 declared actions produced a state or pixel change within 45 frames; key-event channel 0/3, action-state channel 0/3`
- **根因**：`projects/match3/src/Match3Game.cs:162`
- **建议修法**：the field initialiser was flipped to `= true` and the assignment inside the startup `Reset*()` was removed
- **验证方式**：the same game re-run through the gate (P2 is blue in the after run)
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `minesweeper` — player input was switched off in the shipped build (fixed; registered from the before-run evidence)

- **严重度**：blocker
- **现象**：in the before run not one of the 2 declared actions responded on either injected channel; the game listened to nothing
- **证据**：
  - `projects/minesweeper/src/MinesweeperGame.cs:175  [Export] public bool PollInput = true;   (this line now reads `= true`; `git diff` of the task's commit shows the flip)`
  - `before-run P2: 0/2 declared actions produced a state or pixel change within 45 frames; key-event channel 0/2, action-state channel 0/2`
- **根因**：`projects/minesweeper/src/MinesweeperGame.cs:175`
- **建议修法**：the field initialiser was flipped to `= true` and the assignment inside the startup `Reset*()` was removed
- **验证方式**：the same game re-run through the gate (P2 is blue in the after run)
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `missilecommand` — player input was switched off in the shipped build (fixed; registered from the before-run evidence)

- **严重度**：blocker
- **现象**：in the before run not one of the 1 declared actions responded on either injected channel; the game listened to nothing
- **证据**：
  - `projects/missilecommand/src/MissileCommandGame.cs:211  [Export] public bool PollInput = true;   (this line now reads `= true`; `git diff` of the task's commit shows the flip)`
  - `before-run P2: 0/1 declared actions produced a state or pixel change within 45 frames; key-event channel 0/1, action-state channel 0/1`
- **根因**：`projects/missilecommand/src/MissileCommandGame.cs:211`
- **建议修法**：the field initialiser was flipped to `= true` and the assignment inside the startup `Reset*()` was removed
- **验证方式**：the same game re-run through the gate (P2 is blue in the after run)
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `pacman` — player input was switched off in the shipped build (fixed; registered from the before-run evidence)

- **严重度**：blocker
- **现象**：in the before run not one of the 4 declared actions responded on either injected channel; the game listened to nothing
- **证据**：
  - `projects/pacman/src/PacManGame.cs:148  [Export] public bool PollInput = true;   (this line now reads `= true`; `git diff` of the task's commit shows the flip)`
  - `before-run P2: 0/4 declared actions produced a state or pixel change within 45 frames; key-event channel 0/4, action-state channel 0/4`
- **根因**：`projects/pacman/src/PacManGame.cs:148`
- **建议修法**：the field initialiser was flipped to `= true` and the assignment inside the startup `Reset*()` was removed
- **验证方式**：the same game re-run through the gate (P2 is blue in the after run)
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `platformer` — player input was switched off in the shipped build (fixed; registered from the before-run evidence)

- **严重度**：blocker
- **现象**：in the before run not one of the 3 declared actions responded on either injected channel; the game listened to nothing
- **证据**：
  - `projects/platformer/src/PlatformerGame.cs:230  [Export] public bool PollInput = true;   (this line now reads `= true`; `git diff` of the task's commit shows the flip)`
  - `before-run P2: 0/3 declared actions produced a state or pixel change within 45 frames; key-event channel 0/3, action-state channel 0/3`
- **根因**：`projects/platformer/src/PlatformerGame.cs:230`
- **建议修法**：the field initialiser was flipped to `= true` and the assignment inside the startup `Reset*()` was removed
- **验证方式**：the same game re-run through the gate (P2 is blue in the after run)
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `puzzlebobble` — player input was switched off in the shipped build (fixed; registered from the before-run evidence)

- **严重度**：blocker
- **现象**：in the before run not one of the 1 declared actions responded on either injected channel; the game listened to nothing
- **证据**：
  - `projects/puzzlebobble/src/PuzzleBobbleGame.cs:206  [Export] public bool PollInput = true;   (this line now reads `= true`; `git diff` of the task's commit shows the flip)`
  - `before-run P2: 0/1 declared actions produced a state or pixel change within 45 frames; key-event channel 0/1, action-state channel 0/1`
- **根因**：`projects/puzzlebobble/src/PuzzleBobbleGame.cs:206`
- **建议修法**：the field initialiser was flipped to `= true` and the assignment inside the startup `Reset*()` was removed
- **验证方式**：the same game re-run through the gate (P2 is blue in the after run)
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `rtype` — player input was switched off in the shipped build (fixed; registered from the before-run evidence)

- **严重度**：blocker
- **现象**：in the before run not one of the 1 declared actions responded on either injected channel; the game listened to nothing
- **证据**：
  - `projects/rtype/src/RTypeGame.cs:250  [Export] public bool PollInput = true;   (this line now reads `= true`; `git diff` of the task's commit shows the flip)`
  - `before-run P2: 0/1 declared actions produced a state or pixel change within 45 frames; key-event channel 0/1, action-state channel 0/1`
- **根因**：`projects/rtype/src/RTypeGame.cs:250`
- **建议修法**：the field initialiser was flipped to `= true` and the assignment inside the startup `Reset*()` was removed
- **验证方式**：the same game re-run through the gate (P2 is blue in the after run)
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `sokoban` — player input was switched off in the shipped build (fixed; registered from the before-run evidence)

- **严重度**：blocker
- **现象**：in the before run not one of the 2 declared actions responded on either injected channel; the game listened to nothing
- **证据**：
  - `projects/sokoban/src/SokobanGame.cs:186  [Export] public bool PollInput = true;   (this line now reads `= true`; `git diff` of the task's commit shows the flip)`
  - `before-run P2: 0/2 declared actions produced a state or pixel change within 45 frames; key-event channel 0/2, action-state channel 0/2`
- **根因**：`projects/sokoban/src/SokobanGame.cs:186`
- **建议修法**：the field initialiser was flipped to `= true` and the assignment inside the startup `Reset*()` was removed
- **验证方式**：the same game re-run through the gate (P2 is blue in the after run)
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `spaceinvaders` — player input was switched off in the shipped build (fixed; registered from the before-run evidence)

- **严重度**：blocker
- **现象**：in the before run not one of the 3 declared actions responded on either injected channel; the game listened to nothing
- **证据**：
  - `projects/spaceinvaders/src/SpaceInvadersGame.cs:130  [Export] public bool PollInput = true;   (this line now reads `= true`; `git diff` of the task's commit shows the flip)`
  - `before-run P2: 0/3 declared actions produced a state or pixel change within 45 frames; key-event channel 0/3, action-state channel 0/3`
- **根因**：`projects/spaceinvaders/src/SpaceInvadersGame.cs:130`
- **建议修法**：the field initialiser was flipped to `= true` and the assignment inside the startup `Reset*()` was removed
- **验证方式**：the same game re-run through the gate (P2 is blue in the after run)
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `towerdefense` — player input was switched off in the shipped build (fixed; registered from the before-run evidence)

- **严重度**：blocker
- **现象**：in the before run not one of the 1 declared actions responded on either injected channel; the game listened to nothing
- **证据**：
  - `projects/towerdefense/src/TowerDefenseGame.cs:199  [Export] public bool PollInput = true;   (this line now reads `= true`; `git diff` of the task's commit shows the flip)`
  - `before-run P2: 0/1 declared actions produced a state or pixel change within 45 frames; key-event channel 0/1, action-state channel 0/1`
- **根因**：`projects/towerdefense/src/TowerDefenseGame.cs:199`
- **建议修法**：the field initialiser was flipped to `= true` and the assignment inside the startup `Reset*()` was removed
- **验证方式**：the same game re-run through the gate (P2 is blue in the after run)
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

## D11 — 玩家需要的能力没有任何动作提供（P6 逐条）（29 条）

### `bomberman` — no declared action delivered a capability a player needs

- **严重度**：blocker
- **现象**：`walk down` had no key at all: the before InputMap was ['bomb_place', 'bomb_right', 'bomb_up']
- **证据**：
  - `tools/playability_controls.json: bomberman -> walk down`
  - `the action `bomb_down` was added by this task`
- **根因**：`projects/bomberman/project.godot [input] + src/bomberman`
- **建议修法**：declare the action and wire it to the game's own API (see the D2/D3 rows for the same game)
- **验证方式**：the gate's P6 row in the after run
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `bomberman` — no declared action delivered a capability a player needs

- **严重度**：blocker
- **现象**：`walk left` had no key at all: the before InputMap was ['bomb_place', 'bomb_right', 'bomb_up']
- **证据**：
  - `tools/playability_controls.json: bomberman -> walk left`
  - `the action `bomb_left` was added by this task`
- **根因**：`projects/bomberman/project.godot [input] + src/bomberman`
- **建议修法**：declare the action and wire it to the game's own API (see the D2/D3 rows for the same game)
- **验证方式**：the gate's P6 row in the after run
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `lunarlander` — no declared action delivered a capability a player needs

- **严重度**：blocker
- **现象**：`turn left` had no key at all: the before InputMap was ['ll_thrust']
- **证据**：
  - `tools/playability_controls.json: lunarlander -> turn left`
  - `the action `ll_rotate_left` was added by this task`
- **根因**：`projects/lunarlander/project.godot [input] + src/lunarlander`
- **建议修法**：declare the action and wire it to the game's own API (see the D2/D3 rows for the same game)
- **验证方式**：the gate's P6 row in the after run
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `lunarlander` — no declared action delivered a capability a player needs

- **严重度**：blocker
- **现象**：`turn right` had no key at all: the before InputMap was ['ll_thrust']
- **证据**：
  - `tools/playability_controls.json: lunarlander -> turn right`
  - `the action `ll_rotate_right` was added by this task`
- **根因**：`projects/lunarlander/project.godot [input] + src/lunarlander`
- **建议修法**：declare the action and wire it to the game's own API (see the D2/D3 rows for the same game)
- **验证方式**：the gate's P6 row in the after run
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `match3` — no declared action delivered a capability a player needs

- **严重度**：blocker
- **现象**：`move the cursor up` had no key at all: the before InputMap was ['m3_auto_move', 'm3_left', 'm3_right']
- **证据**：
  - `tools/playability_controls.json: match3 -> move the cursor up`
  - `the action `m3_up` was added by this task`
- **根因**：`projects/match3/project.godot [input] + src/match3`
- **建议修法**：declare the action and wire it to the game's own API (see the D2/D3 rows for the same game)
- **验证方式**：the gate's P6 row in the after run
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `match3` — no declared action delivered a capability a player needs

- **严重度**：blocker
- **现象**：`move the cursor down` had no key at all: the before InputMap was ['m3_auto_move', 'm3_left', 'm3_right']
- **证据**：
  - `tools/playability_controls.json: match3 -> move the cursor down`
  - `the action `m3_down` was added by this task`
- **根因**：`projects/match3/project.godot [input] + src/match3`
- **建议修法**：declare the action and wire it to the game's own API (see the D2/D3 rows for the same game)
- **验证方式**：the gate's P6 row in the after run
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `match3` — no declared action delivered a capability a player needs

- **严重度**：blocker
- **现象**：`swap the cursor's gem with the one to its right` had no key at all: the before InputMap was ['m3_auto_move', 'm3_left', 'm3_right']
- **证据**：
  - `tools/playability_controls.json: match3 -> swap the cursor's gem with the one to its right`
  - `the action `m3_swap` was added by this task`
- **根因**：`projects/match3/project.godot [input] + src/match3`
- **建议修法**：declare the action and wire it to the game's own API (see the D2/D3 rows for the same game)
- **验证方式**：the gate's P6 row in the after run
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `minesweeper` — no declared action delivered a capability a player needs

- **严重度**：blocker
- **现象**：`move the cursor left` had no key at all: the before InputMap was ['mine_flag_next', 'mine_reveal_next']
- **证据**：
  - `tools/playability_controls.json: minesweeper -> move the cursor left`
  - `the action `mine_left` was added by this task`
- **根因**：`projects/minesweeper/project.godot [input] + src/minesweeper`
- **建议修法**：declare the action and wire it to the game's own API (see the D2/D3 rows for the same game)
- **验证方式**：the gate's P6 row in the after run
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `minesweeper` — no declared action delivered a capability a player needs

- **严重度**：blocker
- **现象**：`move the cursor right` had no key at all: the before InputMap was ['mine_flag_next', 'mine_reveal_next']
- **证据**：
  - `tools/playability_controls.json: minesweeper -> move the cursor right`
  - `the action `mine_right` was added by this task`
- **根因**：`projects/minesweeper/project.godot [input] + src/minesweeper`
- **建议修法**：declare the action and wire it to the game's own API (see the D2/D3 rows for the same game)
- **验证方式**：the gate's P6 row in the after run
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `minesweeper` — no declared action delivered a capability a player needs

- **严重度**：blocker
- **现象**：`move the cursor up` had no key at all: the before InputMap was ['mine_flag_next', 'mine_reveal_next']
- **证据**：
  - `tools/playability_controls.json: minesweeper -> move the cursor up`
  - `the action `mine_up` was added by this task`
- **根因**：`projects/minesweeper/project.godot [input] + src/minesweeper`
- **建议修法**：declare the action and wire it to the game's own API (see the D2/D3 rows for the same game)
- **验证方式**：the gate's P6 row in the after run
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `minesweeper` — no declared action delivered a capability a player needs

- **严重度**：blocker
- **现象**：`move the cursor down` had no key at all: the before InputMap was ['mine_flag_next', 'mine_reveal_next']
- **证据**：
  - `tools/playability_controls.json: minesweeper -> move the cursor down`
  - `the action `mine_down` was added by this task`
- **根因**：`projects/minesweeper/project.godot [input] + src/minesweeper`
- **建议修法**：declare the action and wire it to the game's own API (see the D2/D3 rows for the same game)
- **验证方式**：the gate's P6 row in the after run
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `minesweeper` — no declared action delivered a capability a player needs

- **严重度**：blocker
- **现象**：`reveal the cell under the cursor` had no key at all: the before InputMap was ['mine_flag_next', 'mine_reveal_next']
- **证据**：
  - `tools/playability_controls.json: minesweeper -> reveal the cell under the cursor`
  - `the action `mine_reveal` was added by this task`
- **根因**：`projects/minesweeper/project.godot [input] + src/minesweeper`
- **建议修法**：declare the action and wire it to the game's own API (see the D2/D3 rows for the same game)
- **验证方式**：the gate's P6 row in the after run
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `minesweeper` — no declared action delivered a capability a player needs

- **严重度**：blocker
- **现象**：`flag the cell under the cursor` had no key at all: the before InputMap was ['mine_flag_next', 'mine_reveal_next']
- **证据**：
  - `tools/playability_controls.json: minesweeper -> flag the cell under the cursor`
  - `the action `mine_flag` was added by this task`
- **根因**：`projects/minesweeper/project.godot [input] + src/minesweeper`
- **建议修法**：declare the action and wire it to the game's own API (see the D2/D3 rows for the same game)
- **验证方式**：the gate's P6 row in the after run
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `missilecommand` — no declared action delivered a capability a player needs

- **严重度**：blocker
- **现象**：`aim left` had no key at all: the before InputMap was ['mc_auto_fire']
- **证据**：
  - `tools/playability_controls.json: missilecommand -> aim left`
  - `the action `mc_left` was added by this task`
- **根因**：`projects/missilecommand/project.godot [input] + src/missilecommand`
- **建议修法**：declare the action and wire it to the game's own API (see the D2/D3 rows for the same game)
- **验证方式**：the gate's P6 row in the after run
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `missilecommand` — no declared action delivered a capability a player needs

- **严重度**：blocker
- **现象**：`aim right` had no key at all: the before InputMap was ['mc_auto_fire']
- **证据**：
  - `tools/playability_controls.json: missilecommand -> aim right`
  - `the action `mc_right` was added by this task`
- **根因**：`projects/missilecommand/project.godot [input] + src/missilecommand`
- **建议修法**：declare the action and wire it to the game's own API (see the D2/D3 rows for the same game)
- **验证方式**：the gate's P6 row in the after run
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `missilecommand` — no declared action delivered a capability a player needs

- **严重度**：blocker
- **现象**：`fire at the cursor` had no key at all: the before InputMap was ['mc_auto_fire']
- **证据**：
  - `tools/playability_controls.json: missilecommand -> fire at the cursor`
  - `the action `mc_fire` was added by this task`
- **根因**：`projects/missilecommand/project.godot [input] + src/missilecommand`
- **建议修法**：declare the action and wire it to the game's own API (see the D2/D3 rows for the same game)
- **验证方式**：the gate's P6 row in the after run
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `puzzlebobble` — no declared action delivered a capability a player needs

- **严重度**：blocker
- **现象**：`aim left` had no key at all: the before InputMap was ['pb_shoot']
- **证据**：
  - `tools/playability_controls.json: puzzlebobble -> aim left`
  - `the action `pb_left` was added by this task`
- **根因**：`projects/puzzlebobble/project.godot [input] + src/puzzlebobble`
- **建议修法**：declare the action and wire it to the game's own API (see the D2/D3 rows for the same game)
- **验证方式**：the gate's P6 row in the after run
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `puzzlebobble` — no declared action delivered a capability a player needs

- **严重度**：blocker
- **现象**：`aim right` had no key at all: the before InputMap was ['pb_shoot']
- **证据**：
  - `tools/playability_controls.json: puzzlebobble -> aim right`
  - `the action `pb_right` was added by this task`
- **根因**：`projects/puzzlebobble/project.godot [input] + src/puzzlebobble`
- **建议修法**：declare the action and wire it to the game's own API (see the D2/D3 rows for the same game)
- **验证方式**：the gate's P6 row in the after run
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `rtype` — no declared action delivered a capability a player needs

- **严重度**：blocker
- **现象**：`fly left` had no key at all: the before InputMap was ['rt_fire']
- **证据**：
  - `tools/playability_controls.json: rtype -> fly left`
  - `the action `rt_left` was added by this task`
- **根因**：`projects/rtype/project.godot [input] + src/rtype`
- **建议修法**：declare the action and wire it to the game's own API (see the D2/D3 rows for the same game)
- **验证方式**：the gate's P6 row in the after run
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `rtype` — no declared action delivered a capability a player needs

- **严重度**：blocker
- **现象**：`fly right` had no key at all: the before InputMap was ['rt_fire']
- **证据**：
  - `tools/playability_controls.json: rtype -> fly right`
  - `the action `rt_right` was added by this task`
- **根因**：`projects/rtype/project.godot [input] + src/rtype`
- **建议修法**：declare the action and wire it to the game's own API (see the D2/D3 rows for the same game)
- **验证方式**：the gate's P6 row in the after run
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `rtype` — no declared action delivered a capability a player needs

- **严重度**：blocker
- **现象**：`fly up` had no key at all: the before InputMap was ['rt_fire']
- **证据**：
  - `tools/playability_controls.json: rtype -> fly up`
  - `the action `rt_up` was added by this task`
- **根因**：`projects/rtype/project.godot [input] + src/rtype`
- **建议修法**：declare the action and wire it to the game's own API (see the D2/D3 rows for the same game)
- **验证方式**：the gate's P6 row in the after run
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `rtype` — no declared action delivered a capability a player needs

- **严重度**：blocker
- **现象**：`fly down` had no key at all: the before InputMap was ['rt_fire']
- **证据**：
  - `tools/playability_controls.json: rtype -> fly down`
  - `the action `rt_down` was added by this task`
- **根因**：`projects/rtype/project.godot [input] + src/rtype`
- **建议修法**：declare the action and wire it to the game's own API (see the D2/D3 rows for the same game)
- **验证方式**：the gate's P6 row in the after run
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `sokoban` — no declared action delivered a capability a player needs

- **严重度**：blocker
- **现象**：`walk down` had no key at all: the before InputMap was ['soko_right', 'soko_up']
- **证据**：
  - `tools/playability_controls.json: sokoban -> walk down`
  - `the action `soko_down` was added by this task`
- **根因**：`projects/sokoban/project.godot [input] + src/sokoban`
- **建议修法**：declare the action and wire it to the game's own API (see the D2/D3 rows for the same game)
- **验证方式**：the gate's P6 row in the after run
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `sokoban` — no declared action delivered a capability a player needs

- **严重度**：blocker
- **现象**：`walk left` had no key at all: the before InputMap was ['soko_right', 'soko_up']
- **证据**：
  - `tools/playability_controls.json: sokoban -> walk left`
  - `the action `soko_left` was added by this task`
- **根因**：`projects/sokoban/project.godot [input] + src/sokoban`
- **建议修法**：declare the action and wire it to the game's own API (see the D2/D3 rows for the same game)
- **验证方式**：the gate's P6 row in the after run
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `towerdefense` — no declared action delivered a capability a player needs

- **严重度**：blocker
- **现象**：`move the cursor left` had no key at all: the before InputMap was ['td_auto_step']
- **证据**：
  - `tools/playability_controls.json: towerdefense -> move the cursor left`
  - `the action `td_left` was added by this task`
- **根因**：`projects/towerdefense/project.godot [input] + src/towerdefense`
- **建议修法**：declare the action and wire it to the game's own API (see the D2/D3 rows for the same game)
- **验证方式**：the gate's P6 row in the after run
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `towerdefense` — no declared action delivered a capability a player needs

- **严重度**：blocker
- **现象**：`move the cursor right` had no key at all: the before InputMap was ['td_auto_step']
- **证据**：
  - `tools/playability_controls.json: towerdefense -> move the cursor right`
  - `the action `td_right` was added by this task`
- **根因**：`projects/towerdefense/project.godot [input] + src/towerdefense`
- **建议修法**：declare the action and wire it to the game's own API (see the D2/D3 rows for the same game)
- **验证方式**：the gate's P6 row in the after run
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `towerdefense` — no declared action delivered a capability a player needs

- **严重度**：blocker
- **现象**：`move the cursor up` had no key at all: the before InputMap was ['td_auto_step']
- **证据**：
  - `tools/playability_controls.json: towerdefense -> move the cursor up`
  - `the action `td_up` was added by this task`
- **根因**：`projects/towerdefense/project.godot [input] + src/towerdefense`
- **建议修法**：declare the action and wire it to the game's own API (see the D2/D3 rows for the same game)
- **验证方式**：the gate's P6 row in the after run
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `towerdefense` — no declared action delivered a capability a player needs

- **严重度**：blocker
- **现象**：`move the cursor down` had no key at all: the before InputMap was ['td_auto_step']
- **证据**：
  - `tools/playability_controls.json: towerdefense -> move the cursor down`
  - `the action `td_down` was added by this task`
- **根因**：`projects/towerdefense/project.godot [input] + src/towerdefense`
- **建议修法**：declare the action and wire it to the game's own API (see the D2/D3 rows for the same game)
- **验证方式**：the gate's P6 row in the after run
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `towerdefense` — no declared action delivered a capability a player needs

- **严重度**：blocker
- **现象**：`place a tower at the cursor` had no key at all: the before InputMap was ['td_auto_step']
- **证据**：
  - `tools/playability_controls.json: towerdefense -> place a tower at the cursor`
  - `the action `td_place` was added by this task`
- **根因**：`projects/towerdefense/project.godot [input] + src/towerdefense`
- **建议修法**：declare the action and wire it to the game's own API (see the D2/D3 rows for the same game)
- **验证方式**：the gate's P6 row in the after run
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

## D2 — 代码读取了 InputMap 未声明的动作（4 条）

### `bomberman` — the code reads an InputMap action that is not declared

- **严重度**：blocker
- **现象**：pressing that key can never work: Godot's InputMap has no such action, so bomb_down stays 0 forever
- **证据**：
  - `BombermanGame.cs:1155`
  - `declared actions: ['bomb_up', 'bomb_right', 'bomb_place']`
- **根因**：`BombermanGame.cs:1155`
- **建议修法**：declare `bomb_down` in project.godot's [input] section next to its siblings
- **验证方式**：the same game re-run through the gate (P5 and P2 must go blue)
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `bomberman` — the code reads an InputMap action that is not declared

- **严重度**：blocker
- **现象**：pressing that key can never work: Godot's InputMap has no such action, so bomb_left stays 0 forever
- **证据**：
  - `BombermanGame.cs:1156`
  - `declared actions: ['bomb_up', 'bomb_right', 'bomb_place']`
- **根因**：`BombermanGame.cs:1156`
- **建议修法**：declare `bomb_left` in project.godot's [input] section next to its siblings
- **验证方式**：the same game re-run through the gate (P5 and P2 must go blue)
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `sokoban` — the code reads an InputMap action that is not declared

- **严重度**：blocker
- **现象**：pressing that key can never work: Godot's InputMap has no such action, so soko_down stays 0 forever
- **证据**：
  - `SokobanGame.cs:937`
  - `declared actions: ['soko_up', 'soko_right']`
- **根因**：`SokobanGame.cs:937`
- **建议修法**：declare `soko_down` in project.godot's [input] section next to its siblings
- **验证方式**：the same game re-run through the gate (P5 and P2 must go blue)
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `sokoban` — the code reads an InputMap action that is not declared

- **严重度**：blocker
- **现象**：pressing that key can never work: Godot's InputMap has no such action, so soko_left stays 0 forever
- **证据**：
  - `SokobanGame.cs:938`
  - `declared actions: ['soko_up', 'soko_right']`
- **根因**：`SokobanGame.cs:938`
- **建议修法**：declare `soko_left` in project.godot's [input] section next to its siblings
- **验证方式**：the same game re-run through the gate (P5 and P2 must go blue)
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

## D3 — 已声明的控制按下去没有可归因的效果（16 条）

### `asteroids` — declared control did not respond to its own key

- **严重度**：blocker
- **现象**：the InputMap declares `ast_left` (A) but injecting it changed neither state nor pixels beyond the no-input control window
- **证据**：
  - `before-run P2 action row: {"action": "ast_left", "key": "A", "responds": false}`
  - `before-run P2: 0/4 declared actions produced a state or pixel change within 45 frames; key-event channel 0/4, action-state channel 0/4`
- **根因**：`see D1 (the read is guarded by PollInput, which was false)`
- **建议修法**：either wire the action to the behaviour the player expects, or stop declaring it
- **验证方式**：the same game re-run through the gate
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `bomberman` — declared control did not respond to its own key

- **严重度**：blocker
- **现象**：the InputMap declares `bomb_up` (W) but injecting it changed neither state nor pixels beyond the no-input control window
- **证据**：
  - `before-run P2 action row: {"action": "bomb_up", "key": "W", "responds": false}`
  - `before-run P2: 0/3 declared actions produced a state or pixel change within 45 frames; key-event channel 0/3, action-state channel 0/3`
- **根因**：`see D1 (the read is guarded by PollInput, which was false)`
- **建议修法**：either wire the action to the behaviour the player expects, or stop declaring it
- **验证方式**：the same game re-run through the gate
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `flappy` — declared control did not respond to its own key

- **严重度**：blocker
- **现象**：the InputMap declares `flap` (SPACE) but injecting it changed neither state nor pixels beyond the no-input control window
- **证据**：
  - `before-run P2 action row: {"action": "flap", "key": "SPACE", "responds": false}`
  - `before-run P2: 0/2 declared actions produced a state or pixel change within 45 frames; key-event channel 0/2, action-state channel 0/2`
- **根因**：`see D1 (the read is guarded by PollInput, which was false)`
- **建议修法**：either wire the action to the behaviour the player expects, or stop declaring it
- **验证方式**：the same game re-run through the gate
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `frogger` — declared control did not respond to its own key

- **严重度**：blocker
- **现象**：the InputMap declares `frog_left` (A) but injecting it changed neither state nor pixels beyond the no-input control window
- **证据**：
  - `before-run P2 action row: {"action": "frog_left", "key": "A", "responds": false}`
  - `before-run P2: 0/4 declared actions produced a state or pixel change within 45 frames; key-event channel 0/4, action-state channel 0/4`
- **根因**：`see D1 (the read is guarded by PollInput, which was false)`
- **建议修法**：either wire the action to the behaviour the player expects, or stop declaring it
- **验证方式**：the same game re-run through the gate
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `game2048` — declared control did not respond to its own key

- **严重度**：blocker
- **现象**：the InputMap declares `m2048_up` (W) but injecting it changed neither state nor pixels beyond the no-input control window
- **证据**：
  - `before-run P2 action row: {"action": "m2048_up", "key": "W", "responds": false}`
  - `before-run P2: 0/4 declared actions produced a state or pixel change within 45 frames; key-event channel 0/4, action-state channel 0/4`
- **根因**：`see D1 (the read is guarded by PollInput, which was false)`
- **建议修法**：either wire the action to the behaviour the player expects, or stop declaring it
- **验证方式**：the same game re-run through the gate
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `lunarlander` — declared control did not respond to its own key

- **严重度**：blocker
- **现象**：the InputMap declares `ll_thrust` (SPACE) but injecting it changed neither state nor pixels beyond the no-input control window
- **证据**：
  - `before-run P2 action row: {"action": "ll_thrust", "key": "SPACE", "responds": false}`
  - `before-run P2: 0/1 declared actions produced a state or pixel change within 45 frames; key-event channel 0/1, action-state channel 0/1`
- **根因**：`see D1 (the read is guarded by PollInput, which was false)`
- **建议修法**：either wire the action to the behaviour the player expects, or stop declaring it
- **验证方式**：the same game re-run through the gate
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `match3` — declared control did not respond to its own key

- **严重度**：blocker
- **现象**：the InputMap declares `m3_auto_move` (SPACE) but injecting it changed neither state nor pixels beyond the no-input control window
- **证据**：
  - `before-run P2 action row: {"action": "m3_auto_move", "key": "SPACE", "responds": false}`
  - `before-run P2: 0/3 declared actions produced a state or pixel change within 45 frames; key-event channel 0/3, action-state channel 0/3`
- **根因**：`see D1 (the read is guarded by PollInput, which was false)`
- **建议修法**：either wire the action to the behaviour the player expects, or stop declaring it
- **验证方式**：the same game re-run through the gate
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `minesweeper` — declared control did not respond to its own key

- **严重度**：blocker
- **现象**：the InputMap declares `mine_reveal_next` (R) but injecting it changed neither state nor pixels beyond the no-input control window
- **证据**：
  - `before-run P2 action row: {"action": "mine_reveal_next", "key": "R", "responds": false}`
  - `before-run P2: 0/2 declared actions produced a state or pixel change within 45 frames; key-event channel 0/2, action-state channel 0/2`
- **根因**：`see D1 (the read is guarded by PollInput, which was false)`
- **建议修法**：either wire the action to the behaviour the player expects, or stop declaring it
- **验证方式**：the same game re-run through the gate
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `missilecommand` — declared control did not respond to its own key

- **严重度**：blocker
- **现象**：the InputMap declares `mc_auto_fire` (SPACE) but injecting it changed neither state nor pixels beyond the no-input control window
- **证据**：
  - `before-run P2 action row: {"action": "mc_auto_fire", "key": "SPACE", "responds": false}`
  - `before-run P2: 0/1 declared actions produced a state or pixel change within 45 frames; key-event channel 0/1, action-state channel 0/1`
- **根因**：`see D1 (the read is guarded by PollInput, which was false)`
- **建议修法**：either wire the action to the behaviour the player expects, or stop declaring it
- **验证方式**：the same game re-run through the gate
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `pacman` — declared control did not respond to its own key

- **严重度**：blocker
- **现象**：the InputMap declares `pac_left` (A) but injecting it changed neither state nor pixels beyond the no-input control window
- **证据**：
  - `before-run P2 action row: {"action": "pac_left", "key": "A", "responds": false}`
  - `before-run P2: 0/4 declared actions produced a state or pixel change within 45 frames; key-event channel 0/4, action-state channel 0/4`
- **根因**：`see D1 (the read is guarded by PollInput, which was false)`
- **建议修法**：either wire the action to the behaviour the player expects, or stop declaring it
- **验证方式**：the same game re-run through the gate
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `platformer` — declared control did not respond to its own key

- **严重度**：blocker
- **现象**：the InputMap declares `plat_left` (A) but injecting it changed neither state nor pixels beyond the no-input control window
- **证据**：
  - `before-run P2 action row: {"action": "plat_left", "key": "A", "responds": false}`
  - `before-run P2: 0/3 declared actions produced a state or pixel change within 45 frames; key-event channel 0/3, action-state channel 0/3`
- **根因**：`see D1 (the read is guarded by PollInput, which was false)`
- **建议修法**：either wire the action to the behaviour the player expects, or stop declaring it
- **验证方式**：the same game re-run through the gate
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `puzzlebobble` — declared control did not respond to its own key

- **严重度**：blocker
- **现象**：the InputMap declares `pb_shoot` (SPACE) but injecting it changed neither state nor pixels beyond the no-input control window
- **证据**：
  - `before-run P2 action row: {"action": "pb_shoot", "key": "SPACE", "responds": false}`
  - `before-run P2: 0/1 declared actions produced a state or pixel change within 45 frames; key-event channel 0/1, action-state channel 0/1`
- **根因**：`see D1 (the read is guarded by PollInput, which was false)`
- **建议修法**：either wire the action to the behaviour the player expects, or stop declaring it
- **验证方式**：the same game re-run through the gate
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `rtype` — declared control did not respond to its own key

- **严重度**：blocker
- **现象**：the InputMap declares `rt_fire` (SPACE) but injecting it changed neither state nor pixels beyond the no-input control window
- **证据**：
  - `before-run P2 action row: {"action": "rt_fire", "key": "SPACE", "responds": false}`
  - `before-run P2: 0/1 declared actions produced a state or pixel change within 45 frames; key-event channel 0/1, action-state channel 0/1`
- **根因**：`see D1 (the read is guarded by PollInput, which was false)`
- **建议修法**：either wire the action to the behaviour the player expects, or stop declaring it
- **验证方式**：the same game re-run through the gate
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `sokoban` — declared control did not respond to its own key

- **严重度**：blocker
- **现象**：the InputMap declares `soko_up` (W) but injecting it changed neither state nor pixels beyond the no-input control window
- **证据**：
  - `before-run P2 action row: {"action": "soko_up", "key": "W", "responds": false}`
  - `before-run P2: 0/2 declared actions produced a state or pixel change within 45 frames; key-event channel 0/2, action-state channel 0/2`
- **根因**：`see D1 (the read is guarded by PollInput, which was false)`
- **建议修法**：either wire the action to the behaviour the player expects, or stop declaring it
- **验证方式**：the same game re-run through the gate
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `spaceinvaders` — declared control did not respond to its own key

- **严重度**：blocker
- **现象**：the InputMap declares `si_left` (A) but injecting it changed neither state nor pixels beyond the no-input control window
- **证据**：
  - `before-run P2 action row: {"action": "si_left", "key": "A", "responds": false}`
  - `before-run P2: 0/3 declared actions produced a state or pixel change within 45 frames; key-event channel 0/3, action-state channel 0/3`
- **根因**：`see D1 (the read is guarded by PollInput, which was false)`
- **建议修法**：either wire the action to the behaviour the player expects, or stop declaring it
- **验证方式**：the same game re-run through the gate
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `towerdefense` — declared control did not respond to its own key

- **严重度**：blocker
- **现象**：the InputMap declares `td_auto_step` (SPACE) but injecting it changed neither state nor pixels beyond the no-input control window
- **证据**：
  - `before-run P2 action row: {"action": "td_auto_step", "key": "SPACE", "responds": false}`
  - `before-run P2: 0/1 declared actions produced a state or pixel change within 45 frames; key-event channel 0/1, action-state channel 0/1`
- **根因**：`see D1 (the read is guarded by PollInput, which was false)`
- **建议修法**：either wire the action to the behaviour the player expects, or stop declaring it
- **验证方式**：the same game re-run through the gate
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

## D5 — README 没有玩法章节，操作不可发现（19 条）

### `asteroids` — no documented controls (the README has no 玩法 section)

- **严重度**：major
- **现象**：nothing on disk tells a human which keys to press; the only source of truth is project.godot's InputMap, which players never read
- **证据**：
  - `README.md: no '## 玩法'`
  - `declared actions: ['ast_left', 'ast_right', 'ast_thrust', 'ast_fire']`
- **根因**：`projects/asteroids/README.md`
- **建议修法**：document every declared action and its key in a '## 玩法' section
- **验证方式**：the gate's README-vs-InputMap cross-check
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `bomberman` — no documented controls (the README has no 玩法 section)

- **严重度**：major
- **现象**：nothing on disk tells a human which keys to press; the only source of truth is project.godot's InputMap, which players never read
- **证据**：
  - `README.md: no '## 玩法'`
  - `declared actions: ['bomb_up', 'bomb_right', 'bomb_place']`
- **根因**：`projects/bomberman/README.md`
- **建议修法**：document every declared action and its key in a '## 玩法' section
- **验证方式**：the gate's README-vs-InputMap cross-check
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `breakout` — no documented controls (the README has no 玩法 section)

- **严重度**：major
- **现象**：nothing on disk tells a human which keys to press; the only source of truth is project.godot's InputMap, which players never read
- **证据**：
  - `README.md: no '## 玩法'`
  - `declared actions: ['breakout_left', 'breakout_right', 'breakout_launch']`
- **根因**：`projects/breakout/README.md`
- **建议修法**：document every declared action and its key in a '## 玩法' section
- **验证方式**：the gate's README-vs-InputMap cross-check
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `flappy` — no documented controls (the README has no 玩法 section)

- **严重度**：major
- **现象**：nothing on disk tells a human which keys to press; the only source of truth is project.godot's InputMap, which players never read
- **证据**：
  - `README.md: no '## 玩法'`
  - `declared actions: ['flap', 'flappy_restart']`
- **根因**：`projects/flappy/README.md`
- **建议修法**：document every declared action and its key in a '## 玩法' section
- **验证方式**：the gate's README-vs-InputMap cross-check
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `frogger` — no documented controls (the README has no 玩法 section)

- **严重度**：major
- **现象**：nothing on disk tells a human which keys to press; the only source of truth is project.godot's InputMap, which players never read
- **证据**：
  - `README.md: no '## 玩法'`
  - `declared actions: ['frog_left', 'frog_right', 'frog_up', 'frog_down']`
- **根因**：`projects/frogger/README.md`
- **建议修法**：document every declared action and its key in a '## 玩法' section
- **验证方式**：the gate's README-vs-InputMap cross-check
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `game2048` — no documented controls (the README has no 玩法 section)

- **严重度**：major
- **现象**：nothing on disk tells a human which keys to press; the only source of truth is project.godot's InputMap, which players never read
- **证据**：
  - `README.md: no '## 玩法'`
  - `declared actions: ['m2048_up', 'm2048_right', 'm2048_down', 'm2048_left']`
- **根因**：`projects/game2048/README.md`
- **建议修法**：document every declared action and its key in a '## 玩法' section
- **验证方式**：the gate's README-vs-InputMap cross-check
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `lunarlander` — no documented controls (the README has no 玩法 section)

- **严重度**：major
- **现象**：nothing on disk tells a human which keys to press; the only source of truth is project.godot's InputMap, which players never read
- **证据**：
  - `README.md: no '## 玩法'`
  - `declared actions: ['ll_thrust']`
- **根因**：`projects/lunarlander/README.md`
- **建议修法**：document every declared action and its key in a '## 玩法' section
- **验证方式**：the gate's README-vs-InputMap cross-check
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `match3` — no documented controls (the README has no 玩法 section)

- **严重度**：major
- **现象**：nothing on disk tells a human which keys to press; the only source of truth is project.godot's InputMap, which players never read
- **证据**：
  - `README.md: no '## 玩法'`
  - `declared actions: ['m3_auto_move', 'm3_left', 'm3_right']`
- **根因**：`projects/match3/README.md`
- **建议修法**：document every declared action and its key in a '## 玩法' section
- **验证方式**：the gate's README-vs-InputMap cross-check
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `minesweeper` — no documented controls (the README has no 玩法 section)

- **严重度**：major
- **现象**：nothing on disk tells a human which keys to press; the only source of truth is project.godot's InputMap, which players never read
- **证据**：
  - `README.md: no '## 玩法'`
  - `declared actions: ['mine_reveal_next', 'mine_flag_next']`
- **根因**：`projects/minesweeper/README.md`
- **建议修法**：document every declared action and its key in a '## 玩法' section
- **验证方式**：the gate's README-vs-InputMap cross-check
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `missilecommand` — no documented controls (the README has no 玩法 section)

- **严重度**：major
- **现象**：nothing on disk tells a human which keys to press; the only source of truth is project.godot's InputMap, which players never read
- **证据**：
  - `README.md: no '## 玩法'`
  - `declared actions: ['mc_auto_fire']`
- **根因**：`projects/missilecommand/README.md`
- **建议修法**：document every declared action and its key in a '## 玩法' section
- **验证方式**：the gate's README-vs-InputMap cross-check
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `pacman` — no documented controls (the README has no 玩法 section)

- **严重度**：major
- **现象**：nothing on disk tells a human which keys to press; the only source of truth is project.godot's InputMap, which players never read
- **证据**：
  - `README.md: no '## 玩法'`
  - `declared actions: ['pac_left', 'pac_right', 'pac_up', 'pac_down']`
- **根因**：`projects/pacman/README.md`
- **建议修法**：document every declared action and its key in a '## 玩法' section
- **验证方式**：the gate's README-vs-InputMap cross-check
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `platformer` — no documented controls (the README has no 玩法 section)

- **严重度**：major
- **现象**：nothing on disk tells a human which keys to press; the only source of truth is project.godot's InputMap, which players never read
- **证据**：
  - `README.md: no '## 玩法'`
  - `declared actions: ['plat_left', 'plat_right', 'plat_jump']`
- **根因**：`projects/platformer/README.md`
- **建议修法**：document every declared action and its key in a '## 玩法' section
- **验证方式**：the gate's README-vs-InputMap cross-check
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `puzzlebobble` — no documented controls (the README has no 玩法 section)

- **严重度**：major
- **现象**：nothing on disk tells a human which keys to press; the only source of truth is project.godot's InputMap, which players never read
- **证据**：
  - `README.md: no '## 玩法'`
  - `declared actions: ['pb_shoot']`
- **根因**：`projects/puzzlebobble/README.md`
- **建议修法**：document every declared action and its key in a '## 玩法' section
- **验证方式**：the gate's README-vs-InputMap cross-check
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `rtype` — no documented controls (the README has no 玩法 section)

- **严重度**：major
- **现象**：nothing on disk tells a human which keys to press; the only source of truth is project.godot's InputMap, which players never read
- **证据**：
  - `README.md: no '## 玩法'`
  - `declared actions: ['rt_fire']`
- **根因**：`projects/rtype/README.md`
- **建议修法**：document every declared action and its key in a '## 玩法' section
- **验证方式**：the gate's README-vs-InputMap cross-check
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `snake` — no documented controls (the README has no 玩法 section)

- **严重度**：major
- **现象**：nothing on disk tells a human which keys to press; the only source of truth is project.godot's InputMap, which players never read
- **证据**：
  - `README.md: no '## 玩法'`
  - `declared actions: ['snake_up', 'snake_down', 'snake_left', 'snake_right', 'snake_pause']`
- **根因**：`projects/snake/README.md`
- **建议修法**：document every declared action and its key in a '## 玩法' section
- **验证方式**：the gate's README-vs-InputMap cross-check
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `sokoban` — no documented controls (the README has no 玩法 section)

- **严重度**：major
- **现象**：nothing on disk tells a human which keys to press; the only source of truth is project.godot's InputMap, which players never read
- **证据**：
  - `README.md: no '## 玩法'`
  - `declared actions: ['soko_up', 'soko_right']`
- **根因**：`projects/sokoban/README.md`
- **建议修法**：document every declared action and its key in a '## 玩法' section
- **验证方式**：the gate's README-vs-InputMap cross-check
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `spaceinvaders` — no documented controls (the README has no 玩法 section)

- **严重度**：major
- **现象**：nothing on disk tells a human which keys to press; the only source of truth is project.godot's InputMap, which players never read
- **证据**：
  - `README.md: no '## 玩法'`
  - `declared actions: ['si_left', 'si_right', 'si_fire']`
- **根因**：`projects/spaceinvaders/README.md`
- **建议修法**：document every declared action and its key in a '## 玩法' section
- **验证方式**：the gate's README-vs-InputMap cross-check
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `tetris` — no documented controls (the README has no 玩法 section)

- **严重度**：major
- **现象**：nothing on disk tells a human which keys to press; the only source of truth is project.godot's InputMap, which players never read
- **证据**：
  - `README.md: no '## 玩法'`
  - `declared actions: ['tetris_left', 'tetris_right', 'tetris_rotate', 'tetris_down', 'tetris_drop']`
- **根因**：`projects/tetris/README.md`
- **建议修法**：document every declared action and its key in a '## 玩法' section
- **验证方式**：the gate's README-vs-InputMap cross-check
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

### `towerdefense` — no documented controls (the README has no 玩法 section)

- **严重度**：major
- **现象**：nothing on disk tells a human which keys to press; the only source of truth is project.godot's InputMap, which players never read
- **证据**：
  - `README.md: no '## 玩法'`
  - `declared actions: ['td_auto_step']`
- **根因**：`projects/towerdefense/README.md`
- **建议修法**：document every declared action and its key in a '## 玩法' section
- **验证方式**：the gate's README-vs-InputMap cross-check
- **复跑状态**：已修复，并在同一道门的复跑中验证（复跑判定：可玩）（复跑判定：playable）

## 复跑中新发现

无：修复后那一轮没有出现修复前不存在的缺陷类。
