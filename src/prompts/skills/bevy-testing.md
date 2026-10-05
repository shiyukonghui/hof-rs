# Skill: judging the `hof_game` Bevy candidate

Your window opens on a **running game**: the runtime built the frozen candidate,
launched it headless, and published the game route for the whole round. The
tools you may call are in `.hoh/TOOLS.md`; the battery's own records are in
`.hoh/deterministic/`. This skill is the recipe book for both.

## 0. What the battery already recorded

```
.hoh/deterministic/battery.json              # one entry per step: ok, observation
.hoh/deterministic/raw/e3_movement.json      # criterion ①: the player's x changed
.hoh/deterministic/raw/e3_coin_counter.json  # criterion ②: coins 0 -> N
.hoh/deterministic/raw/e3_win_flag.json      # criterion ③: won false -> true
.hoh/deterministic/raw/e3_jump_arc.json      # criterion ④: the arc rises AND falls
.hoh/deterministic/raw/e3_grounded.json      # criterion ⑤: grounded true before take-off
.hoh/deterministic/raw/e3_movement_left.json      # P1-left: `-1` moves x down
.hoh/deterministic/raw/e3_movement_release.json   # P1-release: `0` stops it
.hoh/deterministic/raw/e3_win_position.json       # P3-position: a sample at the win frame
.hoh/deterministic/raw/e3_grounded_payload.json   # P5-gate: the payload on its own
.hoh/deterministic/raw/e3_process_liveness.json   # Q-startup: the frame counter advanced, last
.hoh/deterministic/raw/editor_errors_baseline.json  # the build
.hoh/deterministic/raw/play_scene_ready.json        # the launch and the endpoint
.hoh/deterministic/mcp-errors.jsonl          # every failed call, one JSON per line
```

Each `raw/e3_*.json` carries the criterion's `observed` flag, its failure reason
(if any), its readings **and the verbatim request/response of every call behind
them**. That is what a claim cites. `ok = false` in `battery.json` means the
evidence is **unavailable** — the claim it supports is a `gap`, not `verified`.

`raw/e3_process_liveness.json` is the one step with a `frames` block instead of a
readings list: `first_frame`, `second_frame` and `requested`, the game's own
counter before and after a wait. It runs **last**, so it is the evidence that the
process was still stepping at the end of the pass (PRD §4 `**启动**`, and the
`Q-startup` surface). `observed = false` there means the counter did not move,
which is a defect of the candidate and never a `verified`.

## 1. Reading the evidence

```
type {{HOH_ARTIFACT_DIR}}\..\.hoh\deterministic\battery.json
```

Read `raw/e3_jump_arc.json` closely when judging criterion ④: the arc is a list
of `(game frame, y)` samples, and the criterion holds only when the sample values
both increase and decrease. A monotone fall — every sample lower than the last —
is a `gap`, however far the player fell.

## 2. Your own calls, against the frozen candidate

The game is running now and it is the artifact you are judging, so a call you
make is independent evidence. One call at a time (a batch is not frame-atomic
and the adapter never sends one):

```
{{HOH_HOH_BIN}} tools call bevy_player_transform --args-file {{HOH_ARTIFACT_DIR}}/args/transform.json
{{HOH_HOH_BIN}} tools call bevy_grounded --args-file {{HOH_ARTIFACT_DIR}}/args/grounded.json
{{HOH_HOH_BIN}} tools call bevy_coin_counter --args-file {{HOH_ARTIFACT_DIR}}/args/coins.json
{{HOH_HOH_BIN}} tools call bevy_win_flag --args-file {{HOH_ARTIFACT_DIR}}/args/win.json
{{HOH_HOH_BIN}} tools call bevy_health --args-file {{HOH_ARTIFACT_DIR}}/args/health.json
```

All five take `{}`. Driving the game takes a level and a frame wait:

```
{{HOH_HOH_BIN}} tools call bevy_inject_move --args-file {{HOH_ARTIFACT_DIR}}/args/right.json
{{HOH_HOH_BIN}} tools call bevy_wait_frames --args-file {{HOH_ARTIFACT_DIR}}/args/wait.json
{{HOH_HOH_BIN}} tools call bevy_inject_move --args-file {{HOH_ARTIFACT_DIR}}/args/stop.json
```

where `right.json` is `{"dir": 1, "level": true}`, `stop.json` is
`{"dir": 0, "level": true}` and `wait.json` is `{"n": 12}`. Every reply carries
`frame`, the **game's own** frame counter — never a count of your calls. The
`world.*` verbs are also available when you need a raw read:

```
{{HOH_HOH_BIN}} tools call world.query --args-file {{HOH_ARTIFACT_DIR}}/args/query.json
```

with `{"data": {"components": ["bevy_transform::components::transform::Transform"]},
"filter": {"with": ["hof_game::contract::Player"]}}`.

Record what you call in `.hoh/evidence/` if you want it cited: a claim's
`execution_records` path must be a **relative** path that really exists.

## 3. What a verified claim needs

- a `claim_id` and a claim derived from the public specification (this project's
  requirements are `P1..P5`);
- at least one `execution_records` entry whose `path` exists and whose content
  visibly supports the claim — the battery's raw payload, or your own recorded
  call;
- `status: "verified"`.

Anything else is a `gap`: an unmet requirement, a regression, or a behaviour
nobody observed. Gaps need `player_impact` and `recommended_update`.

## 4. Scratch discipline

Every temporary, probe or log file goes under the scratch directory, which the
artifact hash ignores:

```
type {{HOH_SCRATCH_DIR}}\probe.json
```

Never leave a probe in the project root: it becomes part of the candidate
identity and is reported in `artifact_hygiene.suspicious_files`.

## 5. The mistake to avoid

Existing source code is **not** evidence. `src/game.rs` containing a coin
counter, a win flag and a jump is exactly what a broken game also contains: the
question is whether the running game's numbers moved. If `battery.json` says
`ok = false`, or a criterion's `observed` is `false`, write the gap — do not
promote it because the code looks right.
