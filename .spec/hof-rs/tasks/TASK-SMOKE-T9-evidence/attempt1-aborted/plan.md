## Project Planner Priorities
### Priority Order
1. **Buildable playable baseline** - Ensure the project opens in Godot 4.7 with no script compile errors and the main scene launches via MCP play_scene; observable outcome: play_scene reports a running scene, the run log shows zero parse/compile errors, and a screenshot shows the Player, ground, and HUD labels rendered.
2. **Core player control on terrain** - Make horizontal movement, jumping, and ground collision observable through the named InputMap actions move_left, move_right, and jump; observable outcome: simulate_action(move_right) increases the Player node x position, simulate_action(jump) raises the player off the ground and then returns it to the ground, and ground/wall contact leaves the player resting without sinking, confirmed via get_game_node_properties.
3. **Core game-flow state visibility** - Make win, lose, and restart observable end-to-end; observable outcome: reaching the Goal sets a victory state with a visible HUD/Result label, exhausting lives or falling below the level sets an observable failure state, and restarting restores initial position, lives, and coin count as reported by node property snapshots.
### Preservation Gate
- project.godot keeps run/main_scene="res://scenes/main.tscn" and the InputMap actions move_left, move_right, and jump stay bound, so the project remains openable and launchable (N1).
- The Main scene instantiates without missing-resource or UID errors, so previously launchable state does not regress (N4).
- The HUD continues to display lives, coins, and time at all times (F16).
### Acceptance Gate
- Launch the main scene via play_scene, drive move_right for a short interval, then issue jump: assert the Player x position increased, the player left the ground and landed again, and no script runtime errors appeared, with a screenshot capturing the player, terrain, and HUD together.
