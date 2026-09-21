# Skill: judging the deterministic evidence battery

## You are judging, not collecting
Before you start, the runtime already ran a fixed battery against the frozen
candidate. Read these first — they are the primary input to every claim:

- `.hoh/deterministic/battery.json` — one entry per step, with `step_id`,
  `supports` (the `F*`/`N*` requirements the step can speak for), `record`
  (the observation text) and `ok`.
- `.hoh/deterministic/raw/<step>.json` — the verbatim payloads behind that
  observation, including every MCP call and its arguments.
- `.hoh/deterministic/mcp-errors.jsonl` — every failed MCP call with its
  `timestamp`, `tool`, `code`, `message` and `attempt`.
- `.hoh/evidence/frame-00.png` — the screenshot captured in the same window.

## What the battery can and cannot support
| step_id | supports | a claim is supported only if… |
|---|---|---|
| `project_reload_and_open` | N1 | `ok`; the editor was reloaded onto the on-disk scene |
| `scene_structure` | N1, F5, F6 | `ok`; the `.tscn` declares exactly one root node and every `parent=` resolves |
| `editor_errors_baseline` | N1, N3 | `ok` and the observation says the editor has no errors |
| `play_scene_ready` | N1 | `ok`; the scene booted and the game answered |
| `scene_tree` | N2, F5 | `ok`; the named nodes exist in the tree |
| `screenshot` | N2, F4, F13, F16 | `ok` and the PNG really exists |
| `input_channel_probe` | F1, F2 (+P3 when the game really has no such action) | the observation says `GAME_INPUT_CHANNEL_OK`; `ACTION_NOT_BOUND` and `ACTION_BINDING_UNKNOWN` are both failures, but they are *different* facts |
| `input_replay` | F1, F2, F3 | `ok` **and** a `game_process` quadruple whose `after_position` differs from `before_position` |
| `node_and_collision_assertions` | F5, F6, F10, F13, F14, F16 | `ok`; every named body has `shape_count > 0` and the HUD has a text node |
| `stop_scene` | N1 | `ok` |

`ok = false` means the evidence is **unavailable**. Every claim that depends on
that step is a `gap` with `player_impact` and `recommended_update` — never
`verified`. A step that succeeded but shows a constant `position`, or a body
with `shape_count = 0`, does not support a movement or collision claim either:
the records give you the numbers, you supply the judgement.

## The game process is not the editor
The running game is a **separate process**; the editor can only talk to it
through the addon's file IPC. Consequences you must respect:

- Every quadruple and every replay record names its process (`channel`):
  `game_process` for `monitor_properties` / `get_game_node_properties`, and
  `editor_process` for `simulate_action` / `get_input_actions`.
- Records labelled `EDITOR_SIDE_INJECTION` come from the **editor's** own
  `InputMap`/`Input` and say nothing about the game. `get_input_actions` lists
  the editor's built-in `ui_*` actions; it is not evidence that a project action
  is missing.
- `ACTION_BINDING_UNKNOWN` means the game-process channel could not be read.
  Record a gap for F1/F2 and say the channel was unreadable — **never** write it
  up as "the action is not bound". That false reading has already sent a round
  off to fix a defect that did not exist.
- `ACTION_NOT_BOUND` is only credible when it comes from the game-process probe.

## How to reference evidence
`execution_records[*].path` must be **relative** to the candidate root and must
really exist. Use `.hoh/deterministic/raw/input_replay.json` or
`.hoh/deterministic/battery.json` rather than copying text into the claim, and
put any new artifact you create under `.hoh/evidence/`. An absolute path, a
`..` component, or a path to a file that is not there makes the whole round
invalid. Leave `candidate_id` empty; the runtime stamps and checks it.

## Discipline
- **Source code existing is not behaviour verification.** A non-empty
  `player.gd` proves nothing about `F1`; only a recording whose `position`
  changes does.
- Every temporary file you create goes under `$HOH_SCRATCH_DIR`
  (`<view>/.hoh/scratch`, excluded from the artifact hash). Never leave `_*`,
  `tmp_*`, `*.bak` or `*.tmp` files in the candidate: the runtime lists them in
  `result.json.artifact_hygiene.suspicious_files` and they are a `gap`.
- Do not read `src/**`, `.spec/**`, `tests/**`, `.git/**` or `F:\RustProjects\**`
  to decide what is true: the tool schemas are in `.hoh/TOOLS.md` and the truth
  is in the battery records.
- One `execution_records` entry per observation, carrying the *verbatim*
  value/observation text.
- When a battery record is ambiguous, you may add a few read-only calls
  (`get_game_node_properties`, `monitor_properties`, `simulate_action`,
  `get_collision_info`, `assert_node_state`) — but collection is not your main
  work, and you must never modify the project to make a check pass.
- Records are only mutually referenceable under the same `candidate_id`.
- A regression (previously verified, now failing) is its own `gap` record that
  names the earlier evidence which reported it working.
