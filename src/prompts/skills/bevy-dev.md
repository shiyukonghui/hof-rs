# Skill: developing the `hof_game` Bevy project

This is the recipe book for the project you are writing. Everything below is
local and offline: `cargo build --offline`, your editor, and the harness's own
`hoh tools call` bridge. The game itself is a Bevy 0.19.1 crate that must keep
its observation contract, because the harness reads your game **from inside its
process** through Bevy Remote Protocol.

## 0. What is in the project

```
Cargo.toml          # crate `hof_game`; bevy 0.19.1 with the `bevy_remote` feature
Cargo.lock          # frozen: do not delete it
src/main.rs         # the app: plugins, the headless switch, the schedule runner
src/contract.rs     # the frozen reflectable contract (seven surfaces)
src/game.rs         # the game's behaviour: this is where you work
```

`src/main.rs` already does the four things that make the game observable, and
none of them may be removed:

1. `bevy = { features = ["bevy_remote"] }` in `Cargo.toml`;
2. `RemotePlugin::default()` + `RemoteHttpPlugin::default()`, which bind
   `127.0.0.1:15702`;
3. `ScheduleRunnerPlugin::run_loop(1/60)` in headless mode — **without it the
   app runs one frame, exits with code 0 and never binds the endpoint**;
4. the runtime switch `HOF_GAME_HEADLESS`: the same binary runs with one window,
   or with no window and no GPU.

## 1. Build — your launchability check

```
cargo build --offline
```

Exit code 0 is the requirement. `CARGO_TARGET_DIR` is already exported into your
shell (`%CARGO_TARGET_DIR%`, the same directory as `%HOH_TARGET_DIR%`), so this
is a warm rebuild of the one crate you edited — seconds, not the ~5-minute cold
build of a second target tree. Do **not** pass `--target-dir` and do not build
the dependencies again.

## 1b. Writing the file you edited

Every source write goes through the write directive; it is executed by the
harness, not by `cmd.exe`, so multi-line Rust with quotes, `%`, `$`, `(` and `)`
goes in unchanged:

```text
HOH_WRITE_FILE src/game.rs
use bevy::prelude::*;
// …the whole file…
HOH_END_WRITE_FILE
```

Read it back with `HOH_READ_FILE src/game.rs` (or `type src\game.rs`). Never
assemble a file with `echo … >> file`, and never write content through
`bash -c`, a heredoc, or `python -c` — none of those survive this shell. A file
you write is **never left empty**: an empty or half-written `src/game.rs` is a
broken candidate, and a round whose only writes were empty is recorded as a
failure.

## 2. The frozen contract, in Bevy terms

`src/contract.rs` declares and registers the seven surfaces. A new state you
want the harness to see must live in one of them (or in a new type you register
the same way), never in a private struct:

```rust
/// A marker the semantic tools address by its full path.
#[derive(Component, Reflect, Debug, Default)]
#[reflect(Component)]
pub struct Player;

/// A resource the semantic tools read by its full path.
#[derive(Resource, Reflect, Debug, Clone, Copy, Default)]
#[reflect(Resource)]
pub struct CoinCounter { pub coins: i64 }

// …and registration, without which Bevy Remote Protocol answers
// `Unknown resource type` and every observation becomes a gap:
app.register_type::<Player>().register_type::<CoinCounter>();
```

Three rules that the earlier spikes paid for:

- **`#[reflect(Component)]` / `#[reflect(Resource)]` plus `register_type`** — a
  type that is not registered is invisible, and the adapter reports a contract
  violation rather than a zero;
- **the crate name is part of the path**: keep `name = "hof_game"` in
  `Cargo.toml` and the types in `src/contract.rs`;
- **do not hide state in an engine resource**: `bevy_time::time::Time` is not
  reflectable, which is why the game has its own `FrameCounter`.

## 3. The game's own clock

```rust
fn count_frames(mut counter: ResMut<FrameCounter>) {
    counter.frames = counter.frames.saturating_add(1);
}
```

Every observation the harness takes is stamped with this number, so it must
increment exactly once per frame.

## 4. Level-triggered input

`InputIntent` is written from outside the game
(`world.mutate_resources` on `hof_game::contract::InputIntent`), so its fields
are a **level**, not an event:

```rust
fn apply_input(
    intent: Res<InputIntent>,
    mut player: Query<(&mut Velocity, &mut Grounded, &mut JumpLatch), With<Player>>,
) {
    for (mut velocity, mut grounded, mut latch) in &mut player {
        // Held: the velocity follows the level every frame, and writing 0 stops
        // the player immediately (no inertia).
        velocity.x = MOVE_SPEED * intent.move_dir as f32;
        // Edge: the *game* consumes the press, so holding it is one jump.
        if intent.jump_pressed && grounded.on_ground && !latch.0 {
            velocity.y = JUMP_SPEED;
            grounded.on_ground = false;
        }
        latch.0 = intent.jump_pressed;
    }
}
```

Do **not** clear `move_dir` every frame: that is what made an early experiment
move 2 px where a held level moved 92 px.

## 5. A jump the harness can see

The criterion is not "the player pressed jump" but "the sampled heights rise
**and** fall, and the peak is above the take-off height". Aim for an apex about a
quarter of a second after take-off and a landing after roughly half a second:

```
rise time  ≈ JUMP_SPEED / GRAVITY      (seconds)
air time   ≈ 2 * JUMP_SPEED / GRAVITY
```

With `JUMP_SPEED = 300` and `GRAVITY = 1200` the player is airborne for ~0.5 s:
about 30 frames at 60 FPS, which the battery's sampler covers with both
directions. A jump with no gravity never falls, and a jump with no upward
impulse never rises — both are red.

## 6. Reading your own state through the tool bridge

The Developer does not need the game process to do its work (the runtime owns
the round's session and the Tester judges it), but the tools exist and their
schemas are in `.hoh/TOOLS.md`. Prefer an args file, because the shell is
`cmd.exe` on Windows:

```
{{HOH_HOH_BIN}} tools call bevy_coin_counter --args-file {{HOH_ARTIFACT_DIR}}/args/coins.json
```

Write `args/coins.json` with the write directive first (it is one line `{}`):

```text
HOH_WRITE_FILE .hoh/scratch/coins.json
{}
HOH_END_WRITE_FILE
```

and pass that path. The argument names are exactly what
`.hoh/TOOLS.md` lists — `dir` and `level` for `bevy_inject_move`, `press` for
`bevy_inject_jump`, `n` for `bevy_wait_frames`.

Reading the state of a game that was started **before you changed the code** is
not evidence about your edit; use it only to understand the tools' shapes. The
runtime owns the round's session: **do not start a game of your own** — a second
boot would replace the session the Tester is meant to reach, and the game it
started predates your edits, so it can never confirm them. Your launchability
check is `cargo build --offline`; the harness's own `play_scene_ready` step is
the boot check.

## 7. Scratch discipline

Every probe, log and temporary JSON goes under the scratch directory, which the
artifact hash ignores:

```
type {{HOH_SCRATCH_DIR}}\probe.json
```

Nothing may be left in the project root: no `_*`, no `tmp_*`, no `*.bak`, no
`*.tmp`, and never a second `Cargo.toml`.

## 8. When a call comes back empty

A `bevy_*` tool that answers with an empty output means the harness rejected the
request before the game saw it — almost always a missing or unreadable args
file. Write the args file first, then call:

```
{{HOH_HOH_BIN}} tools call bevy_health --args-file {{HOH_ARTIFACT_DIR}}/args/health.json
```

```
HOH_WRITE_FILE .hoh/scratch/health.json
{}
HOH_END_WRITE_FILE
```

Then read the call's own message: a contract violation names the type path that
is not registered, and a transport failure names the endpoint the runtime
published (`.hoh/PROJECT_MAP.md` and `.hoh/TOOLS.md` carry both). Do not
hand-roll JSON-RPC, do not probe ports, and do not start a second game.
