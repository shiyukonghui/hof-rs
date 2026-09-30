# QA Report - iteration 1 (tester)

Candidate: res://scenes/main.tscn as the main scene; the frozen candidate was judged from the deterministic battery plus a few read-only probes in the round game process.

## What was checked
- Battery steps project_reload_and_open, scene_structure, editor_errors_baseline, play_scene_ready, scene_tree, screenshot, input_channel_probe, input_replay, node_and_collision_assertions and editor_stop_scene all report ok=true.
- Read-only probes: Player, Player/Camera and HUD label properties; run_test_scenario for move_right, move_left and jump; a jump restart after GAME OVER.

## Verified observations
- N1: the project reloads and opens main.tscn, the game boots with 53 nodes and stops cleanly; the editor log holds only 1 informational MCP banner.
- N2: stable node names and paths exist (Player, Ground, Coin1..4, Enemy1..2, QuestionBlock, Brick1, Goal, HUD/Score, Lives, Coins, Time, Result).
- F1: move_right quadruple x 184.667 to 401.0 (delta 216.33) and move_left 448.667 to 232.333 (delta -216.33) in the game process, POSITION_ASSERT_PASSED.
- F2: jump quadruple y 269.981 to 242.592 with velocity.y 4.5, POSITION_ASSERT_PASSED.
- F4: .hoh/evidence/frame-00.png exists; Player/Camera is an enabled Camera2D child of Player.
- F5: collision shape_count Ground=1 and Player=1; the player rests grounded at y about 284 without sinking.
- F14/F15: the HUD Result label showed GAME OVER - press Jump to restart; a jump restarted the level to spawn x=60 and cleared the label.
- F16: HUD/Lives is Lives: 3, HUD/Coins is Coins: 0, HUD/Time is Time: 0, all visible; 5 visible HUD text nodes.

## Open gaps
- F3 facing: a move_left injection left facing=1 where -1 was expected; the deterministic replay never reports facing either.
- F6 wall blocking, F7 patrol, F8 side/bottom enemy damage, F9 stomp, F11 question block, F12 brick: no public execution record observed, so they are unverified.
- F10 coin: the Coins label stayed 0 while the player was driven across the level; no coin was collected.
- F13 victory: Goal.reached=false and no victory text was ever seen; only GAME OVER appeared.
- F17 level duration (30-120s) and N3 60s stability were not measured this round.

qa_status: partial. The launchable observable baseline, movement/jump/camera, HUD, failure and restart are verified; combat, coins, blocks and the win condition remain open.

Evidence: .hoh/deterministic/battery.json and .hoh/deterministic/raw/*.json; .hoh/evidence/frame-00.png and replay-*.png; .hoh/evidence/hud-labels.json, camera-node.json, failure-state.json, restart-state.json, facing-scenario.json.