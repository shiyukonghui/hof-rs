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
| `editor_errors_baseline` | N1, N3 | `ok` and the observation says the editor has no errors |
| `play_scene_ready` | N1 | `ok`; the scene booted and the game answered |
| `scene_tree` | N2, F5 | `ok`; the named nodes exist in the tree |
| `screenshot` | N2, F4, F13, F16 | `ok` and the PNG really exists |
| `input_replay` | F1, F2, F3 | `ok` **and** the recorded `position` actually changed |
| `node_and_collision_assertions` | F5, F6, F10, F13, F14, F16 | `ok`; every named body has `shape_count > 0` and the HUD has a text node |
| `stop_scene` | N1 | `ok` |

`ok = false` means the evidence is **unavailable**. Every claim that depends on
that step is a `gap` with `player_impact` and `recommended_update` — never
`verified`. A step that succeeded but shows a constant `position`, or a body
with `shape_count = 0`, does not support a movement or collision claim either:
the records give you the numbers, you supply the judgement.

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
- One `execution_records` entry per observation, carrying the *verbatim*
  value/observation text.
- When a battery record is ambiguous, you may add a few read-only calls
  (`get_game_node_properties`, `monitor_properties`, `simulate_action`,
  `get_collision_info`, `assert_node_state`) — but collection is not your main
  work, and you must never modify the project to make a check pass.
- Records are only mutually referenceable under the same `candidate_id`.
- A regression (previously verified, now failing) is its own `gap` record that
  names the earlier evidence which reported it working.
