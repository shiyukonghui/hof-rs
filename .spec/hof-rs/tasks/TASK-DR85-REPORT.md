# TASK-DR85-REPORT — the jump window observes the coin before it drives, the ground probe waits for the spawn drop, and the DR-82 prefix is sealed

- Role: implementation subagent, no upstream conversation context. **There is no
  `.spec/hof-rs/tasks/TASK-DR85.md`**: this batch was dispatched as a self-contained prompt, which is
  its only and authoritative task. Read first, as required: `TASK-DR84-ACCEPTANCE.md`,
  `TASK-DR84-REPORT.md`, `TASK-DR83-ACCEPTANCE.md`, `TASK-DR83-REPORT.md`, `TASK-SMOKE-T15-REPORT.md`,
  `TASK-SMOKE-T15-ACCEPTANCE.md`, `DECISIONS.md` D289 / D293 / D294.
- Batch kind: **offline**. No engine was started, no round was run, no network call was made; nothing
  was staged, committed or pushed; **not one byte was written under `runs/**`**.
- HEAD at start = HEAD at end = `f6ea2d1c9e82da0add93f512d25a28f06306ae3b`; `origin/master` holds the
  same value. The three changed files are **uncommitted working-tree modifications** (the DR-84/acceptance
  commits before this batch are the dispatcher's, not this batch's).
- Landing point `F:\moonbit-hof-rs`; every multi-line helper script lives **outside** the repository, in
  `C:\Users\wyl\AppData\Local\Temp\dr85\` (`plants.py`, `plant_runner.py`, `run_gate.py`,
  `selfcheck.py`, `check_prefix*.py`).
- Gate headline: baseline reproduced **599 passed / 0 failed / 7 ignored, listing 606,
  `cargo test --offline` exit 0**; final forced-rebuild gate **602 passed / 0 failed / 7 ignored,
  listing 609, `cargo test --offline` exit 0**; `cargo fmt --all --check` exit 0.
- Changed files (three): `src/adapter/godot.rs`
  `8ff8b643d70d99c35b95165d4d6549b980f97614e780c1f42e03b14622a4f1ca` (328,894 B);
  `tests/evidence_battery.rs` `dc14fc3802f60a4e18f6be0ffdf104e0731b0566f1dda0fa5aacef452fdbee88`
  (270,917 B); `tests/append_only_guard.rs`
  `27aaf1dbcc04f079d93793cc453288e83190d3e928d11bab7cee469a228f0492` (29,516 B). All pure LF
  (CR = 0 / CRLF = 0). `.spec/hof-rs/tasks/TASK-DR82-REPORT.md` is **byte-identical** to its delivered
  revision (`ee88185054acaade384fd47d2c7ae164606e21f65c0dd1969efdda593fbef691`, 46,014 B); only plants
  touched it, each restored byte-exactly.

## 0. Machine-readable verdict

```json
{
  "task": "TASK-DR85",
  "kind": "implementation subagent report (offline batch: no engine, no real round, no network, nothing staged, committed or pushed; nothing written under runs/**)",
  "task_book": "none: this batch was dispatched as a self-contained prompt, which is its only and authoritative task. There is no .spec/hof-rs/tasks/TASK-DR85.md",
  "head": "f6ea2d1c9e82da0add93f512d25a28f06306ae3b",
  "origin_master": "f6ea2d1c9e82da0add93f512d25a28f06306ae3b",
  "pushed": false,
  "changed_files": {
    "src/adapter/godot.rs": "8ff8b643d70d99c35b95165d4d6549b980f97614e780c1f42e03b14622a4f1ca",
    "tests/evidence_battery.rs": "dc14fc3802f60a4e18f6be0ffdf104e0731b0566f1dda0fa5aacef452fdbee88",
    "tests/append_only_guard.rs": "27aaf1dbcc04f079d93793cc453288e83190d3e928d11bab7cee469a228f0492",
    "bytes": 328894,
    "all_lf": true
  },
  "coin_decision": {
    "road": "observe the coin before the jump",
    "what": "step_input_jump reads the coin counter before it drives and hands the reading into raw/input_jump.json as leading_calls labelled jump:coin_baseline; the label and the token for an unreadable counter are JUMP_COIN_BASELINE_LABEL and JUMP_COIN_BASELINE_UNREADABLE",
    "why_not_add_to_the_consumer_list": "COIN_CONSUMING_BATTERY_STEPS encodes a total order ('the observing window before every consuming window'); putting the jump in it would demand interaction_evidence before input_jump, which directly contradicts GROUND_NEEDING_BATTERY_STEP / GROUND_CONSUMING_BATTERY_STEPS and would reintroduce the mid-air jump DR-84 closed. The two rules cannot both be a total order on battery steps, so the coin rule is applied inside the step",
    "why_not_declare_only": "a declaration without a reading leaves the 0 -> 1 transition destroyed; the property would be asserted, not preserved",
    "false_negative_property": "a coin the jump can collect is never counted before it is observed: the pre-jump value is on record immediately ahead of the injection, so the battery carries 0 (before the jump) next to the 1 every later window reads",
    "same_candidate_set_as_the_observing_window": "both use the scene_tree that run() passes (step_scene_tree), hud_label_candidates and the COIN_COUNTER_PREFIX rule, so a counter the interaction window can read is a counter the jump step reads"
  },
  "spawn_drop": {
    "road": "wait for a genuinely resting reading",
    "what": "the pre-jump probe is repeated in JUMP_GROUND_PROBE_FRAMES-frame steps up to JUMP_GROUND_SETTLE_ATTEMPTS = 16 attempts (32 frames), and stops at the first attempt whose y is flat within JUMP_GROUND_EPSILON",
    "why_not_state_two_frames_suffice": "the frozen smoke-t15 level spawns the player at y = 240 while the measured resting y is 263.925201416016, so the drop is 23.925201416016 px and sqrt(2 * 23.925201416016 / 1400) = 0.1849 s, about 11.1 physics frames at 60 Hz, against a two-frame probe; road two would have been false",
    "fail_closed": "a readable-but-moving reading is retried; a probe with no usable samples and a failed probe call are refused at once; a player still moving at the cap is JUMP_NOT_DRIVEN with no jump_reading",
    "understated_claim_replaced": "'a few pixels' is replaced above by the measured 23.925201416016 px / 11.1 frames"
  },
  "sealed_prefix": {
    "document": ".spec/hof-rs/tasks/TASK-DR82-REPORT.md",
    "pin_bytes": 44184,
    "pin_sha256": "319397fdb369ea95c63e2eac7d4eaacd25b7825e73313e9afe863f5eb1a8e406",
    "helper": "seal_violations, the same helper every other seal in tests/append_only_guard.rs uses",
    "marker_note": "the seal marker carries the leading line terminator: the correction was appended as \\n# 附：DR-84 …, so the heading's # is at offset 44,185 while the frozen revision ends at 44,184. whole_line_offset returns where the marker begins, so the marker starts at 44,184 and the pinned length is the reviewed revision's own length. DR82_DR84_HEADING is still asserted as a whole line at 44,185",
    "plants": "p4 (machine-block value 16 -> 17) and p5 (prefix prose 逐名普查 -> 逐名统计) both RED at tests/append_only_guard.rs:313:5 with the pinned-prefix hash violation; both were GREEN under the DR-84 pin (DR84A-1)",
    "permanent_non_vacuity": "tests/append_only_guard.rs:527 the_dr82_seal_reddens_on_a_block_edit_and_a_prose_edit mutates in-memory copies and requires both to trip the seal; the real report is never written"
  },
  "tests": {
    "new": 3,
    "removed": 0,
    "listing": "606 -> 609",
    "ignored_unchanged": 7,
    "declared_pins": [
      "evidence_battery::the_jump_step_observes_the_coin_counter_before_it_drives (tests/evidence_battery.rs:6206) - written with the fix, so it has no preserved pre-implementation red; plant p1 reddens it at tests/evidence_battery.rs:6222:5",
      "evidence_battery::a_level_that_spawns_the_player_above_its_floor_still_shows_a_grounded_jump_arc (tests/evidence_battery.rs:6285) - plant p2 reddens it at tests/evidence_battery.rs:6303:5",
      "append_only_guard::the_dr82_seal_reddens_on_a_block_edit_and_a_prose_edit (tests/append_only_guard.rs:527) - a pure non-vacuity pin; plants p4/p5 exercise the same seal from outside"
    ],
    "genuine_first_reds": [],
    "honest_note": "no new test has a preserved pre-implementation red: the reds were not captured before the fix, which the DR-84 acceptance flagged as DR84A-7. The three tests are declared pins, and their falsifiability is demonstrated by the controlled plants rather than claimed"
  },
  "plants": {
    "count": 6,
    "all_reddened_their_own_test": true,
    "all_restored_byte_exact": true,
    "run_on": "the delivered revision (godot.rs 8ff8b643, evidence_battery.rs dc14fc38, append_only_guard.rs 27aaf1db, DR82 report ee881850)",
    "entries": [
      {
        "id": "p1_coin_baseline_removed",
        "target": "evidence_battery::the_jump_step_observes_the_coin_counter_before_it_drives",
        "exit": 101,
        "first_failure": "tests\\evidence_battery.rs:6222:5",
        "mutated_sha256": "1b6eb4d6918a8d987336186f92c5bf0dbcb73dfc5c7b4fcf281fd5edf19854db"
      },
      {
        "id": "p2_single_probe",
        "target": "evidence_battery::a_level_that_spawns_the_player_above_its_floor_still_shows_a_grounded_jump_arc",
        "exit": 101,
        "first_failure": "tests\\evidence_battery.rs:6303:5",
        "mutated_sha256": "01e2d5f6ee070c9de21b64ef30a1e5feced244b150d7d7c2ec2a595ff72110b3"
      },
      {
        "id": "p3_ground_probe_fails_open",
        "target": "evidence_battery::a_level_with_no_usable_ground_reports_the_jump_unobserved",
        "exit": 101,
        "first_failure": "tests\\evidence_battery.rs:4803:5",
        "mutated_sha256": "afa5eada894827926ec31e5c7d9af3e4208e309b1d4f89e2126db7098431f581"
      },
      {
        "id": "p4_dr82_block_edit",
        "target": "append_only_guard::the_dr82_census_claim_carries_its_dr84_qualifier",
        "exit": 101,
        "first_failure": "tests\\append_only_guard.rs:313:5",
        "mutated_sha256": "4bb2ce2d5f7a309b6a265d99d4c2618364aff2ac35303811193aad627906050c"
      },
      {
        "id": "p5_dr82_prose_edit",
        "target": "append_only_guard::the_dr82_census_claim_carries_its_dr84_qualifier",
        "exit": 101,
        "first_failure": "tests\\append_only_guard.rs:313:5",
        "mutated_sha256": "7846e0172a0194ac1317a024c9c0087784dbe31a35a60f1414d2b05282f8b21c"
      },
      {
        "id": "p6_arc_rule_always_true",
        "target": "evidence_battery::a_jump_window_with_no_rise_is_rejected_too",
        "exit": 101,
        "first_failure": "tests\\evidence_battery.rs:4487:5",
        "mutated_sha256": "3fb3503e00a09fc0eac30a3bcad1aa3aff1010ce0638d627f7f8f5830c01b8a1"
      }
    ],
    "restore_proof": "each plant restored its file from a byte backup written before the mutation; sha256 back to the pre-plant value and a byte comparison True for all six"
  },
  "gate": {
    "baseline": {
      "passed": 599,
      "failed": 0,
      "ignored": 7,
      "listed": 606,
      "blocks": 60,
      "exit": 0,
      "how": "the three changed files were replaced with their HEAD blobs (git show, read-only; no git checkout --), cargo test --offline ran, and the files were restored from byte backups with sha256 equality and a byte comparison True for all three"
    },
    "final": {
      "passed": 602,
      "failed": 0,
      "ignored": 7,
      "listed": 609,
      "blocks": 60,
      "exit": 0,
      "failed_lines": 0,
      "panicked_lines": 0
    },
    "fmt_exit": 0,
    "forced_rebuild": {
      "fingerprints_removed_with_python_glob_rmtree": 122,
      "fingerprints_left": 0,
      "tracked_rs_files_touched_individually": 97,
      "tracked_rs_total": 97,
      "touched_paths_are_literal": true,
      "forced_compile_line": "Compiling hof-rs v0.1.0 (F:\\moonbit-hof-rs) - line 1 of gate_run.log",
      "finished_line": "Finished `test` profile [unoptimized + debuginfo] target(s) in 57.27s"
    },
    "interruption": "none: the forced-rebuild run completed in one command, so the log carries both the Compiling line and the final totals",
    "ignored_names": [
      "e0_initialize_workspace",
      "e1_single_iteration_smoke",
      "e2_project_boots",
      "e3_behaviour_is_evidenced",
      "e4_verified_claims_are_reproducible",
      "e5_qa_did_not_modify_the_artifact",
      "e6_report_is_honest"
    ],
    "tests_removed": 0
  },
  "forbidden_zones": {
    "boundary_unix": 1790954845,
    "runs_new_files": 0,
    "runs_files_walked": 7117,
    "runs_newest": "runs/smoke-t15/evidence/COPY_MANIFEST.txt 2026-10-02 14:54:52 (pre-existing)",
    "workspace_new_files": 0,
    "workspace_files_walked": 743,
    "workspace_newest": ".workspace/fresh-t15/.godot/.gdignore 2026-10-02 15:14:59 (pre-existing)",
    "prd_sha256": "4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a",
    "decisions_sha256": "245befb7af292c379c161ddc917e996a54a4dceea5e93c5d0226816efbae4a76",
    "requirements_sha256": "298a948929a434a91b9088f4d566b7e387d0cfeb270f86a79d88b006821e0e54",
    "cargo_toml_sha256": "e0c4992bd828729b8514f9cf694925687b726157d45463a636390081a3dadba1",
    "cargo_lock_sha256": "d98fa91565ec72ae998fd9f6fd3838286e287e4baf8020c5114a1e2ac0bfdb36",
    "dependency_added": false,
    "engine_binary_sha256": "08483088a4a2772841cd3b4c916b2d45b3cb6255656cf3951598a86fce7e9e6a",
    "engine_repo_head": "fc63af77c33368c4a1bb839c95d19750554f63a3",
    "engine_repo_porcelain_empty": true,
    "game_written_by_hand": false,
    "pushed": false,
    "rm_rf_used": false,
    "git_checkout_restore_used": false,
    "paths_built_from_unexpanded_variables": false,
    "git_status": " M src/adapter/godot.rs; M tests/append_only_guard.rs; M tests/evidence_battery.rs; ?? l.json ?? p2.json ?? pv.json ?? r.json (the four untracked root scratch files pre-date this batch)"
  },
  "residual_risks": {
    "measured": [
      "the pre-change baseline: 599 passed / 0 failed / 7 ignored, listing 606, 60 blocks, exit 0, reproduced by swapping in the HEAD blobs and restoring byte-exactly",
      "the delivered gate: 602 / 0 / 7, listing 609, 60 blocks, exit 0, fmt exit 0, 122 hof-rs-* fingerprint directories removed with Python glob + rmtree (0 left), all 97 tracked .rs paths touched individually, the Compiling line and Finished 57.27s in the same log",
      "the six plants: each reddened its own test (exit 101) at the published line, and each restore was byte-exact",
      "zero files newer than the boundary under runs/** (7117 walked) and .workspace/** (743 walked); every frozen hash unchanged; pure LF in the three changed files; nothing pushed",
      "the frozen spawn-drop arithmetic: 23.925201416016 px, 0.1849 s, about 11.1 frames at 60 Hz, against JUMP_GROUND_SETTLE_ATTEMPTS * JUMP_GROUND_PROBE_FRAMES = 32 frames"
    ],
    "inferred": [
      "that a real engine answers each repeated probe with the next two physics frames, so 16 attempts really are ~32 frames of settling time; the fixture models the attempts explicitly and no engine ran",
      "that the extra node-property reads the jump step now makes before its probe do not disturb real physics",
      "that a real level with a coin in the jump's apex behaves as the fixture models it (a body-entered collection on the jump press)"
    ],
    "can_a_real_round_still_find_the_jump_undriven": "YES, in three shapes, all honest JUMP_NOT_DRIVEN with no reading: (i) a level that spawns the player unsupported or drops it for longer than the 16 two-frame attempts (~32 frames, ~0.53 s of game time) - the wait now covers the frozen 11.1-frame drop with roughly 3x margin but not an arbitrarily long one; (ii) a probe the engine answers with a moving or unreadable y for any other reason; (iii) a channel that refuses the jump injection. What is removed is the shape where the battery's own earlier horizontal steps walked the player off the floor first",
    "can_any_coin_still_be_counted_before_it_is_observed": "Only in the case the harness names explicitly. If no HUD Label reads a Coins: counter at the jump step's baseline read, the step records COIN_BASELINE_UNREADABLE and records no reading; the interaction window reports COIN_COUNTER_UNREADABLE for the same HUD, so no counter transition existed to observe and none is claimed. Because both use the same scene_tree and the same candidate/prefix rule, a counter the interaction window can read is a counter the jump step read first. The one gap that remains is a HUD whose counter becomes readable only later in the run - not modelled by the frozen level and not covered by a test"
  }
}
```

## 0. What this file is

Implementation subagent report for the **DR-85** offline batch, written by a fresh subagent with no
upstream conversation context. There is **no `.spec/hof-rs/tasks/TASK-DR85.md`**: this batch was
dispatched as a self-contained prompt, which is its only and authoritative task. The machine-readable
block above was produced with `json.dumps(..., ensure_ascii=False, indent=2)` semantics, written first to
`C:\Users\wyl\AppData\Local\Temp\dr85\machine_block_dr85.json` (outside the repository) and compared
back before this file was written.

The batch is **offline**: no engine was started, no round was run, no network call was made; nothing was
staged, committed or pushed; **not one byte was written under `runs/**`**. HEAD at start = HEAD at end =
`f6ea2d1c…`; `origin/master` holds the same value; the three changed files are uncommitted working-tree
modifications.

## 1. The coin hazard: the jump window observes the counter before it drives

**The defect, restated from the acceptance.** DR-84 moved the jump window before every step that
consumes the ground, and its own rationale claimed the jump "drives only `jump`, so it consumes neither
coins nor ground". The ground half is true. The coin half is false: the frozen `player.gd` jumps with
`jump_velocity = -430` under `gravity = 1400`, so the apex is `430² / (2 * 1400) = 66.04 px` above the
spawn, and `coin.gd` collects on `body_entered` from the `player` group. A coin placed inside that apex
box — reachable by the vertical move alone, since the interaction drive only ever walks right — is
collected by the jump window, which now runs **before** `interaction_evidence` reads the counter. The
first counter any window then sees is already `1`, and F10's `0 -> 1` transition is destroyed before it
could be observed. That is the `smoke-t11` false negative, one axis over.

**The road taken: observe the coin before the jump.** `run()` now hands the jump step the same scene
tree it already passes to the interaction window, and `step_input_jump` reads the coin counter **before**
`run_replay_windows` drives anything. The reading is found exactly the way the interaction window finds
it — the `Label`s under `HUD` from the scene tree (`hud_label_candidates`, the tree itself carries no
text: DR-76 ①) and the first whose `text` starts with `COIN_COUNTER_PREFIX` — and the calls are labelled
`JUMP_COIN_BASELINE_LABEL` (`jump:coin_baseline`). They travel into `raw/input_jump.json` as the pass's
leading calls, so the pre-jump counter value sits immediately ahead of the injection.

**Why not the other two roads the acceptance named.**

* *Add the jump step to a coin-consumer list so the ordering logic accounts for it.* The list that
  encodes the rule, `COIN_CONSUMING_BATTERY_STEPS`, is consumed by the ordering test as "the observing
  window must run **before** every member". Putting `input_jump` in it would demand
  `interaction_evidence` before `input_jump` — the exact inverse of `GROUND_NEEDING_BATTERY_STEP` /
  `GROUND_CONSUMING_BATTERY_STEPS`, which requires the jump before `interaction_evidence`. The two rules
  cannot both be a total order on battery steps, and obeying the coin order would put the jump back
  after the horizontal drive, reopening the mid-air jump DR-84 closed. The road is therefore
  *satisfiable only by contradiction*, not merely inelegant.
* *Declare the hazard explicitly.* A declaration with no reading leaves the transition destroyed: the
  property would be asserted rather than preserved, which is precisely the DR84A-2 defect (a rationale
  claiming safety it did not have).

**Why the false-negative property is now provably preserved.** The fixture's
`with_coin_in_the_jump_apex` level increments the counter on the **jump press** and, built with
`InteractionMode::NoPickupNoWin`, cannot be credited a coin by the horizontal drive at all. On that
level the test asserts:

1. the jump step's observation carries `jump:coin_baseline` **and** the pre-jump value
   `Coins: 0`;
2. in `raw/input_jump.json`, the `jump:coin_baseline` call precedes the `jump` press — the injection
   that can collect the coin;
3. the interaction window, which runs after the jump, reads `Coins: 1`.

So the battery carries the value the jump started from, immediately before the consumption, next to the
value every later window reads. A real round's Tester can read a `0 -> 1` transition off the battery
whatever the jump swept. On the pre-DR-85 arrangement there is no baseline call at all and the only
counter value in the run is the post-jump `1`; plant **p1** reproduces exactly that and reddens the test
at `tests\evidence_battery.rs:6222:5` with the observation naming `COIN_BASELINE_UNREADABLE`.

The candidate sets are identical by construction: both the jump step and the interaction window use the
`scene_tree` cloned from `step_scene_tree` and the same `hud_label_candidates` + `COIN_COUNTER_PREFIX`
rule, so a counter the interaction window can read is a counter the jump step reads first.

**Fail-closed or not, stated plainly.** The baseline read is deliberately *not* a refusal. If no `Coins:`
counter can be read before the jump, the step records
`jump:coin_baseline: COIN_BASELINE_UNREADABLE …` and drives on; refusing would sacrifice the ground
evidence (criterion 3) for a level whose coin evidence is already unavailable. Nothing is silent in that
case: the jump step says the baseline was unreadable and the interaction window independently reports
`COIN_COUNTER_UNREADABLE`, so no transition is claimed. The one situation the design does not cover is a
HUD whose counter becomes readable only later in the run; that is recorded as a residual risk, not
asserted away.

## 2. The spawn drop: the ground probe waits instead of sampling two frames

**Road taken: wait for a genuinely resting reading.** The alternative the prompt allowed — state in the
report why a two-frame probe suffices — was not available, because the frozen numbers say it does not:
`smoke-t15` spawns the player at `y = 240` while the resting `y` the whole round measured is
`263.925201416016`, so the drop is `23.925201416016 px`, and `player.gd`'s `gravity = 1400` needs
`t = sqrt(2 * 23.925201416016 / 1400) = 0.1849 s`, about `11.1` physics frames at 60 Hz, against a probe
that read `JUMP_GROUND_PROBE_FRAMES = 2`. Whether the player was resting at the instant the jump is now
driven was genuinely undetermined offline, and the DR-84 report's "a few pixels" understated a
quarter-second drop (DR84A-3). That sentence is replaced by the arithmetic above.

**What the code does.** The jump window repeats the same `JUMP_GROUND_PROBE_FRAMES = 2` frame probe in a
loop of at most `JUMP_GROUND_SETTLE_ATTEMPTS = 16` attempts — `32` frames, about three times the frozen
drop — and stops at the first attempt whose `y` is flat within `JUMP_GROUND_EPSILON`, which is then the
last reading before the injection. A resting player still reads resting on the first attempt, so the
green path issues exactly one probe call and every existing call-order expectation is unchanged.

**The fail-closed behaviour is kept, and is stronger in one direction:**

| reading | outcome |
|---|---|
| readable, `y` flat | certified; the window is driven |
| readable, `y` moving | retried, up to the cap (this is the wait) |
| no usable samples in the payload | **refused at once**, no retry (`PROBE_UNREADABLE`) |
| the sample call fails | **refused at once**, no retry (`PROBE_UNREADABLE`) |
| still moving at the cap | `JUMP_NOT_DRIVEN`, `ok = false`, **no `jump_reading`** |

A readable-but-moving probe is not treated as an unreadable channel: retrying a channel that answered
nothing would only burn the window's budget, so an unreadable probe is refused immediately. Plant
**p2** (the loop capped at one attempt, i.e. the old one-shot probe) reddens
`a_level_that_spawns_the_player_above_its_floor_still_shows_a_grounded_jump_arc` at
`tests\evidence_battery.rs:6303:5` with "the window took 1 probe(s)"; the fixture's `Settling` level
answers the first `SETTLING_PROBES_BEFORE_REST = 3` probes with a moving `y` and the fourth with a
landed player, and the test additionally asserts `SETTLING_PROBES_BEFORE_REST < JUMP_GROUND_SETTLE_ATTEMPTS`,
so the fixture's landing is a fact about the level and the cap is not the thing under test.

## 3. The DR-82 prefix is sealed through the shared helper

`the_dr82_census_claim_carries_its_dr84_qualifier` now calls **`seal_violations`** — the same helper
T13, DR73, DR81 and REQUIREMENTS use — with

* `DR82_PRE_DR84_BYTES = 44_184`, `DR82_PRE_DR84_SHA256 = 319397fd…e406`: the revision before the DR-84
  correction, byte for byte.

One detail is worth spelling out, because it is why the marker is not simply the heading: the correction
was appended as `\n# 附：DR-84 …`, so the frozen revision ends at byte `44,184` and the heading's own `#`
begins at byte `44,185` (a blank separator line sits at `44,184`). `seal_violations` pins
`bytes[..offset]` where `offset` is where the *marker* begins, so the seal marker
(`DR82_DR84_SEAL`) carries that leading line terminator and starts at `44,184`; the pin is then exactly
the reviewed revision's length and hash. The plain heading is still separately asserted, as a whole line,
at `44,185`. The frozen prefix includes the report's machine-readable block, so the prefix hash names a
block edit as well as a prose edit.

**Plants, both reddening the same test and both green under the DR-84 pin (DR84A-1):**

| # | plant | result |
|---|---|---|
| p4 | the machine-readable block's `"names_as_keys_per_file": 16` → `17` | **RED** exit 101, `tests\append_only_guard.rs:313:5` — "the 44184 bytes before the correction hash to 5cab1d33…, not the pinned 319397fd…" |
| p5 | prefix prose `逐名普查` → `逐名统计` | **RED** exit 101, `tests\append_only_guard.rs:313:5` — the same prefix-hash violation with `970bf200…` |

The test also keeps its original assertions (the heading owns a whole line, the correction carries
`names_as_keys_per_file`, `键计数`, `raw=0`, `sidecar`, and the original claim is still readable above the
heading), and a new in-repo non-vacuity test (`tests/append_only_guard.rs:527`) mutates in-memory copies
of the real bytes to require both plant shapes to trip the seal, without writing the report.

The report itself is **untouched**: `ee881850…`, 46,014 B, before and after every plant (the byte
restores were verified with sha256 and a byte comparison).

## 4. Tests: declared pins, not preserved first reds

Three tests were added and none was removed: `evidence_battery` 74, `append_only_guard` 9; the listing
went `606 -> 609`, the ignored set stays exactly the seven `e0…e6` names.

| test | nature | red demonstrated by |
|---|---|---|
| `evidence_battery::the_jump_step_observes_the_coin_counter_before_it_drives` (`:6206`) | **declared pin** — behavioural, written with the fix | plant p1, `:6222:5` |
| `evidence_battery::a_level_that_spawns_the_player_above_its_floor_still_shows_a_grounded_jump_arc` (`:6285`) | **declared pin** — behavioural, written with the fix | plant p2, `:6303:5` |
| `append_only_guard::the_dr82_seal_reddens_on_a_block_edit_and_a_prose_edit` (`:527`) | **declared pin** — pure non-vacuity over in-memory mutants | plants p4/p5 exercise the same seal from outside |

**No new test has a preserved pre-implementation red.** The tests were written with the implementation,
so their first run was green; the DR-84 acceptance's DR84A-7 asked for exactly this honesty. What is
shown instead is that each is falsifiable on the delivered bytes: removing the baseline read (p1) or the
wait (p2) reddens it at a named line. Two further plants re-demonstrate properties this batch must not
have weakened:

* **p3** (`player_is_resting_on_ground` accepts every non-empty series) reddens
  `a_level_with_no_usable_ground_reports_the_jump_unobserved` at `:4803:5` — the ground probe is still
  fail-closed, and the waiting loop did not make it permissive.
* **p6** (`shows_an_arc` unconditionally true) reddens `a_jump_window_with_no_rise_is_rejected_too` at
  `:4487:5` — the arc rule is still load-bearing.

`the_probe_frame_count_matches_the_production_constant` still pins the fixture's probe discriminator
against `JUMP_GROUND_PROBE_FRAMES`, and the waiting loop deliberately probes with the same two-frame
request each time, so that pin is unchanged.

## 5. Controlled plants — six, each reddening its own test, each restored byte-exactly

All plants ran on the **delivered** revision, then were restored from byte backups; the runner is
`C:\Users\wyl\AppData\Local\Temp\dr85\plant_runner.py` and its output is `plants_result.json` /
`plants_run.log`.

| # | plant | target test | exit | first failure | restore |
|---|---|---|---|---|---|
| p1 | remove the pre-jump coin baseline read | `the_jump_step_observes_the_coin_counter_before_it_drives` | 101 | `tests\evidence_battery.rs:6222:5` | sha256 `8ff8b643…`, bytes equal |
| p2 | cap the probe loop at one attempt (the old one-shot probe) | `a_level_that_spawns_the_player_above_its_floor_still_shows_a_grounded_jump_arc` | 101 | `tests\evidence_battery.rs:6303:5` | sha256 `8ff8b643…`, bytes equal |
| p3 | `player_is_resting_on_ground` accepts every non-empty series | `a_level_with_no_usable_ground_reports_the_jump_unobserved` | 101 | `tests\evidence_battery.rs:4803:5` | sha256 `8ff8b643…`, bytes equal |
| p4 | edit the DR-82 machine-readable block (`16` → `17`) | `the_dr82_census_claim_carries_its_dr84_qualifier` | 101 | `tests\append_only_guard.rs:313:5` | sha256 `ee881850…`, bytes equal |
| p5 | edit DR-82 prefix prose (`逐名普查` → `逐名统计`) | same | 101 | `tests\append_only_guard.rs:313:5` | sha256 `ee881850…`, bytes equal |
| p6 | `shows_an_arc` unconditionally true | `a_jump_window_with_no_rise_is_rejected_too` | 101 | `tests\evidence_battery.rs:4487:5` | sha256 `8ff8b643…`, bytes equal |

No plant was left in the tree: the three changed files on disk hash to the delivered values
(`8ff8b643…`, `dc14fc38…`, `27aaf1db…`) and the DR-82 report to `ee881850…`. All tampering used Python
byte backups; no `rm -rf`, no path built from an unexpanded shell variable, and no `git checkout --`
were used anywhere.

## 6. Gate

| item | value |
|---|---|
| baseline (HEAD blobs swapped in, then restored) | **599 passed / 0 failed / 7 ignored**, listing **606**, 60 blocks, `cargo test --offline` **exit 0**; `-- --list` exit 0 with 606 `: test` lines; `-- --list --ignored` exit 0 naming exactly the seven `e0…e6` |
| final (delivered tree, forced rebuild) | **602 passed / 0 failed / 7 ignored**, listing **609**, 60 result blocks, **0** `FAILED` and **0** `panicked` lines, `cargo test --offline` **exit 0** |
| delta | **+3 tests, 0 removed**; listing 606 → 609; ignored 7 → 7, same names |
| `cargo fmt --all --check` | **exit 0** |
| forced rebuild | 122 `target/debug/.fingerprint/hof-rs-*` directories removed with Python `glob` + `shutil.rmtree` (0 left); all 97 paths from `git ls-files '*.rs'` touched **individually** from git's own listing (literal paths, no shell wildcard, no unexpanded variable); then `cargo test --offline` |
| build identity | `Compiling hof-rs v0.1.0 (F:\moonbit-hof-rs)` on **line 1** of `gate_run.log`, followed by `Finished \`test\` profile [unoptimized + debuginfo] target(s) in 57.27s` |
| interruption | **none** — the forced-rebuild run completed in a single (background) command, so the log carries both the `Compiling` line and the final totals; the literal exit code is 0 |

The pre-change baseline was reproduced on this exact revision by replacing the three changed files with
their `HEAD` blobs (`git show`, read-only — **not** `git checkout --`), running the suite, and restoring
each file from a byte backup: `sha256` back to `8ff8b643…` / `dc14fc38…` / `27aaf1db…` and byte
equality `True` for all three.

## 7. Forbidden-zone self-check

| item | reading | basis |
|---|---|---|
| `runs/**` writes | **0** files newer than the boundary `1790954845`; **7117** walked; newest `runs/smoke-t15/evidence/COPY_MANIFEST.txt` (pre-existing) | `selfcheck.py`, single `os.walk` |
| `.workspace/**` writes | **0** newer; **743** walked; newest `.workspace/fresh-t15/.godot/.gdignore` (pre-existing) | same scan |
| `PRD-mario.md` | `4c81c3a9…5c3a`, **unchanged** | `sha256` |
| `DECISIONS.md` / `REQUIREMENTS.md` | `245befb7…a76` / `298a9489…`, **unchanged** — `DECISIONS.md` was **not** modified | `sha256` |
| `Cargo.toml` / `Cargo.lock` | `e0c4992b…` / `d98fa915…`, **unchanged**; **no dependency added** | `sha256` |
| `TASK-DR82-REPORT.md` | `ee881850…`, 46,014 B — untouched by every change, only by plants that were restored byte-exactly | `sha256` + byte comparison |
| engine | binary 194,216,960 B `08483088…e9e6a`; nested repo HEAD `fc63af77…` with an empty `git status --porcelain` | `sha256` + `git -C godot-mcp/godot status` |
| push | `HEAD == origin/master == f6ea2d1c…`; nothing staged, committed or pushed by this batch; the three changed files are uncommitted working-tree modifications | `git rev-parse`, `git status` |
| line endings | the three changed files are **CR = 0 / CRLF = 0** (pure LF) | byte census |
| repository status | only the three intended files modified; the four untracked root scratch files (`l.json`, `p2.json`, `pv.json`, `r.json`) pre-date this batch | `git status --porcelain` |
| the suite's own sidecar write | `tests/round_artifacts_sidecar.rs` rewrites `TASK-SMOKE-T10-evidence/analysis/redaction_defect.redacted.txt` byte-identically on every run; `git status` shows no diff for it | `git status` |
| `rm -rf` / `git checkout --` / unexpanded-variable paths | **none**; restores came from Python byte backups with `sha256` + byte comparison; all helper scripts live outside the repository | plant and gate scripts |

## 8. Residual risks — measured vs inferred

**Measured** (reproducible from this batch's own instruments): the pre-change baseline 599/0/7 listing
606 exit 0 and the byte-exact swap and restore; the delivered gate 602/0/7 listing 609 exit 0 with fmt
exit 0, 122 fingerprint directories removed, 97 literal `.rs` paths touched, and the `Compiling` line and
`Finished 57.27s` in one log; the six plants' reds at their published lines and their byte-exact
restores; zero writes past the boundary under `runs/**` and `.workspace/**`; every frozen hash
unchanged; pure LF; nothing pushed; the frozen spawn-drop arithmetic (23.925201416016 px, 0.1849 s,
about 11.1 frames against a 32-frame cap).

**Inferred** (no engine ran): that each repeated probe really advances the game two physics frames, so
16 attempts are ~32 frames of settling time; that the extra node-property reads the jump step now makes
before its probe do not disturb real physics; that a coin in the jump's apex is collected on the press in
the shape the fixture models.

**Can a real round still find the jump undriven? Yes**, in three shapes, and all three fail closed with
`JUMP_NOT_DRIVEN` and no reading:

1. a level that spawns the player unsupported, or whose drop is longer than the 16 two-frame attempts
   (~32 frames, ~0.53 s of game time). The wait now covers the frozen 11.1-frame drop with roughly 3×
   margin, but it is a finite cap by design: a much longer drop is still refused, honestly;
2. a probe the engine answers with a moving `y` for float-noise or physics-tick reasons, or with no
   usable samples;
3. a channel that refuses the jump injection before the probe has classified it.

What is **removed by construction** is the DR-84-era shape in which the battery's own interaction drive
and channel probe walked the player off a floor whose goal sat near its edge before the jump was pressed.

**Can any coin still be counted before it is observed?** Only where the harness says so explicitly. If
no `Coins:` counter is readable before the jump, the step records `COIN_BASELINE_UNREADABLE` and the
interaction window reports `COIN_COUNTER_UNREADABLE`; no transition is claimed, so nothing is silent.
Because the jump step and the observing window use the same scene tree, the same candidate enumeration
and the same prefix rule, a counter the observing window can read is a counter the jump step reads
first. The one gap left is a HUD whose counter becomes readable **later in the run than the baseline
read** — not modelled by the frozen level, not covered by a test, and recorded here rather than asserted
away.

**Not attempted, by the task's own constraints:** no real round, no engine, no network; the
hardware checks the DR-84 acceptance asked for (a real `raw/input_jump.json` carrying a two-frame probe
with flat `y` before the injection, and a `jump_reading` with `shows_an_arc = true`) remain for a round
batch.
