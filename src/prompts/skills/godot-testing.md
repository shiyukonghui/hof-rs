# Skill: Godot evidence collection and judgement discipline

## The collection pattern
For each checkable claim, run this four-step pattern and keep every artifact:

1. **Drive the input** — `simulate_sequence` (or `simulate_action`) with the
   named actions (`move_right`, `jump`), e.g.
   `{"actions":[{"action":"move_right","duration_ms":800}]}`
2. **Capture the state** — `capture_frames` (or `get_game_screenshot`) into
   `.hoh/evidence/`; record the returned relative path.
3. **Observe the numbers** — `monitor_properties` on a stable node path, e.g.
   `{"node_path":"/root/Main/Player","properties":["position"]}`
4. **Assert** — `assert_node_state` with an explicit expected value, e.g.
   `{"node_path":"/root/Main/Player","property":"position:x","expected":">0"}`

Then write one `execution_records` entry per observation, with `path` relative
to the project root (`.hoh/evidence/...`) and the *verbatim* output in
`observation`.

## Discipline
- Records are only mutually referenceable when they share the same
  `candidate_id`; a record produced under a different candidate invalidates the
  claim.
- Source code existing is **not** behaviour verification. The claim is verified
  only if the cited record shows the behaviour happening.
- Anything you could not observe is a `gap`, with `player_impact` and
  `recommended_update`. An honest gap is a correct answer; an invented
  `verified` is a failed round.
- Deterministic build/boot records under `.hoh/deterministic/` cover
  "it still starts". They never cover gameplay behaviour.
- Never modify the project to make a check pass. Use `simulate_*` inputs only.
