//! The **corrected write accounting** of the recorded Developer calls, measured
//! through [`hof_rs::harness::write_audit`].
//!
//! This is the durable replacement for the detector the round-6 live-cost batch
//! used.  That one counted `HOH_WRITE_FILE` directives only, so it could not see
//! the project files the roles change with a **shell command**, and it reported
//! the live call's last project change as call 44 when the recording contains a
//! successful PowerShell `Set-Content` on `src\game.rs` at call 95.  The next
//! acceptance refuted the number (`.spec/bevy/ACCEPTANCE-LIVE-COST.md`, A-3) and
//! could only do it with a script outside the repository, so the account could
//! not be re-run from the tree.  These tests are that account, in the tree.
//!
//! **Where the evidence is.**  Every figure here comes from the raw recorded
//! trajectories under `runs/`, which the repository **does not track**
//! (`runs/` is in `.gitignore`): `runs/livecost1/iter-1/traj/developer.attempt1.json`
//! and `runs/round4/iter-{1,2,3}/traj/developer.attempt1.json`.  The tests
//! therefore require the evidence to be present and name the missing path if it
//! is not — a silent pass on a machine without the recordings would be worse
//! than a failure.  `tests/context_compaction.rs` already depends on the same
//! recordings the same way.
//!
//! Nothing here runs a round, a model call or a shell command: the accounting is
//! decided from the recorded action text and the recorded `<returncode>`.
//!
//! ## What these tests reproduce from the acceptance, and what they do not
//!
//! Reproduced exactly:
//!
//! * the ten write directives the withdrawn budget cuts in round-4 iteration 3
//!   at K = 32 — calls 50, 70, 73, 74, 80, 84, 86, 90, 93, 97;
//! * the abort calls and their token totals at K = 32 (live 76 / 1,357,530;
//!   round4-iter-1 51 / 1,790,635; round4-iter-2 never; round4-iter-3 39 /
//!   1,604,038);
//! * round4-iter-3's directive-write timeline and its 43-call window (6 → 50);
//! * the live call's write-free distance after its last **directive** write (43).
//!
//! Corrected, with the recorded return code as the reason (the acceptance could
//! not decide these and said so):
//!
//! * round-4 iteration 3's call 22, reported as a real `src/game.rs` edit, is
//!   recorded as **failed** (`<returncode>1</returncode>`, `json pattern
//!   missing`): the script threw before its `[IO.File]::WriteAllText`.  Call 8
//!   succeeded and *is* a real edit.
//! * the live call's call 139, reported as a project-file write, is recorded as
//!   **failed** (`<returncode>1</returncode>`, `Missing closing ')' in
//!   expression`): PowerShell never parsed it.
//! * the acceptance's live-call window (43 → 150, 107 calls) is the *directive*
//!   window; the corrected project timeline ends at call **95**, so the last
//!   stretch with no project write is 95 → 150 (55 calls).
//! * the writes the withdrawn budget cuts in iteration 3 are not only the ten
//!   directives: they include **seven real `src/game.rs` edits** (calls 75, 81,
//!   85, 87, 91, 94, 98) made by scripts the role wrote into `.hoh/scratch/`.
//!   The acceptance could not see those, because the write is inside the script,
//!   not on the command line that runs it.

use std::path::PathBuf;

use hof_rs::harness::write_audit::{
    audit_trajectory, replay_directive_step_budget, scope_of, Audit, Outcome, Scope, WriteSource,
};
use serde_json::Value;

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
}

fn trajectory(relative: &str) -> PathBuf {
    let path = repo_root().join("runs").join(relative);
    assert!(
        path.is_file(),
        "the recorded evidence this accounting is measured on is not in the tree: {}\n\
         `runs/` is gitignored, so a checkout without the recordings cannot run this test.  \
         Copy the recordings there rather than deleting the test: the numbers in \
         .spec/bevy/WRITE-ACCOUNTING-REPORT.md are these numbers.",
        path.display()
    );
    path
}

fn audit_of(relative: &str) -> Audit {
    let path = trajectory(relative);
    let bytes = std::fs::read(&path).unwrap_or_else(|error| panic!("{}: {error}", path.display()));
    let value: Value = serde_json::from_slice(&bytes)
        .unwrap_or_else(|error| panic!("{}: {error}", path.display()));
    audit_trajectory(&value)
}

const DEVELOPER: &str = "traj/developer.attempt1.json";

/// The live call: the one Developer call that was actually run.
///
/// The round-6 report said "the last change to a project file was call 44; calls
/// 45–150 changed no project file".  That is false, and this is the corrected
/// profile: one more write directive at 17 into `.hoh`, four shell writes into
/// the project (17, 44, 95, and a failed 139), and no project write after 95.
#[test]
fn the_live_calls_write_profile_is_the_corrected_one() {
    let audit = audit_of(&format!("livecost1/iter-1/{DEVELOPER}"));
    assert_eq!(audit.recorded_calls(), 150);
    assert_eq!(audit.total_tokens, 3_651_120);

    // The guard's own signal: successful write directives, of any path.
    assert_eq!(audit.directive_write_calls(), vec![6, 14, 17, 19, 43]);

    // The corrected signal: every call that wrote a project file.
    assert_eq!(
        audit.project_write_calls(),
        vec![6, 14, 17, 19, 43, 44, 95],
        "the live call's project writes, including the shell writes the old detector could not see"
    );
    assert_eq!(audit.last_project_write(), Some(95));

    // The two the acceptance reported as further project writes, with the
    // recorded result deciding whether they changed anything.
    let failed = audit.failed_project_writes();
    assert_eq!(
        failed,
        vec![(139, "src\\game.rs".to_string(), 1)],
        "call 139's PowerShell never parsed (`Missing closing ')' in expression`), so it did not write"
    );
    let sources: Vec<&WriteSource> = audit
        .calls
        .iter()
        .flat_map(|call| call.project_writes.iter().map(|write| &write.source))
        .collect();
    assert!(
        sources
            .iter()
            .any(|source| matches!(source, WriteSource::Shell)),
        "the live call's project writes include shell writes: {sources:?}"
    );

    // The corrected write-free stretch: previous claim 106 calls after call 44;
    // the truth is 55 calls after call 95 (and 106 calls after 44 did happen, but
    // they are not write-free).
    assert_eq!(
        audit.longest_project_write_free_window(),
        Some((95, 151, 55)),
        "the longest stretch with no project write starts at the call-95 write"
    );
}

/// Round-4 iteration 3: the run the withdrawn budget cuts.  Both signals are
/// needed — the directive timeline the guard can see, and the project timeline it
/// cannot.
#[test]
fn the_recorded_iteration_three_write_timeline_is_the_corrected_one() {
    let audit = audit_of(&format!("round4/iter-3/{DEVELOPER}"));
    assert_eq!(audit.recorded_calls(), 102);
    assert_eq!(audit.total_tokens, 5_223_211);

    assert_eq!(
        audit.directive_write_calls(),
        vec![6, 50, 70, 73, 74, 80, 84, 86, 90, 93, 97],
        "the guard-visible timeline; the window 6 -> 50 is 43 calls"
    );
    assert_eq!(
        audit.project_write_calls(),
        vec![6, 8, 75, 81, 85, 87, 91, 94, 98],
        "the project timeline: one directive, one direct shell write, seven script-driven edits"
    );

    // Call 22 (reported by the acceptance as a real edit) and call 69 threw
    // before their `[IO.File]::WriteAllText`.
    assert_eq!(
        audit.failed_project_writes(),
        vec![
            (22, "src\\game.rs".to_string(), 1),
            (69, "src\\game.rs".to_string(), 1)
        ]
    );
    // Call 72 emitted a directive whose closing marker was not last, so the
    // harness answered with the help text and executed nothing — neither the
    // script write nor the command that would have run it.
    let undecided = audit.undecided();
    assert_eq!(undecided.len(), 1, "{undecided:?}");
    assert_eq!(undecided[0].0, 72);
    assert_eq!(
        audit.calls.iter().filter(|call| call.call == 72).count(),
        1,
        "call 72 exists in the recording"
    );

    assert_eq!(
        audit.longest_project_write_free_window(),
        Some((8, 75, 66)),
        "66 calls pass between the call-8 edit and the next project write"
    );
    assert_eq!(
        audit.paths_written(),
        vec!["src/game.rs".to_string(), "src\\game.rs".to_string()]
    );
}

/// Round-4 iterations 1 and 2, for the corpus view: iteration 1 is all
/// directives; iteration 2 is mostly directives plus the four Python-script edits
/// that the directive-only view cannot see.
#[test]
fn the_other_two_recorded_iterations_are_accounted_the_same_way() {
    let first = audit_of(&format!("round4/iter-1/{DEVELOPER}"));
    assert_eq!(first.recorded_calls(), 69);
    assert_eq!(first.total_tokens, 2_626_195);
    assert_eq!(
        first.project_write_calls(),
        vec![7, 8, 9, 13, 14, 18],
        "iteration 1 writes only through directives, so both signals agree"
    );
    assert!(first.failed_project_writes().is_empty());

    let second = audit_of(&format!("round4/iter-2/{DEVELOPER}"));
    assert_eq!(second.recorded_calls(), 125);
    assert_eq!(second.total_tokens, 13_091_431);
    assert_eq!(
        second.project_write_calls(),
        vec![
            33, 35, 36, 37, 42, 44, 46, 55, 65, 67, 72, 98, 100, 107, 110
        ],
        "iteration 2's last four project writes are script-driven and invisible to a directive-only view"
    );
    for call in [98, 100, 107, 110] {
        let entry = second
            .calls
            .iter()
            .find(|entry| entry.call == call)
            .expect("the call is in the recording");
        assert!(
            entry.project_writes.iter().any(|write| matches!(
                &write.source,
                WriteSource::Script { script } if script.ends_with(".py")
            )),
            "call {call} is a Python script run: {entry:?}"
        );
    }
    // A heredoc (`python - <<"PY"`) that `cmd.exe` cannot run: the attempt is
    // recorded, the change is not.
    assert_eq!(
        second.failed_project_writes(),
        vec![(68, "src/game.rs".to_string(), 1)]
    );
}

/// The withdrawn budget's own safety claim, re-run against the corrected
/// accounting.  Its headline was "zero recorded writes lost"; the recording has
/// ten cut write directives and seven cut project edits.
#[test]
fn the_withdrawn_budget_at_k_32_cuts_ten_directives_and_seven_project_edits() {
    let third = audit_of(&format!("round4/iter-3/{DEVELOPER}"));
    let replay = replay_directive_step_budget(&third, 32);
    assert_eq!(replay.aborted_at_call, Some(39));
    assert_eq!(replay.cumulative_tokens_at_abort, 1_604_038);
    assert_eq!(
        replay.directive_writes_after_the_end,
        vec![50, 70, 73, 74, 80, 84, 86, 90, 93, 97],
        "the ten write directives the round-6 JSON reported as an empty list"
    );
    assert_eq!(
        replay.project_writes_after_the_end,
        vec![75, 81, 85, 87, 91, 94, 98],
        "seven real src/game.rs edits, each run by a .hoh/scratch script the role wrote first"
    );

    let live =
        replay_directive_step_budget(&audit_of(&format!("livecost1/iter-1/{DEVELOPER}")), 32);
    assert_eq!(live.aborted_at_call, Some(76));
    assert_eq!(live.cumulative_tokens_at_abort, 1_357_530);
    assert_eq!(live.directive_writes_after_the_end, Vec::<usize>::new());
    assert_eq!(
        live.project_writes_after_the_end,
        vec![95],
        "the live call loses its call-95 project write even though every directive predates the abort"
    );

    let first = replay_directive_step_budget(&audit_of(&format!("round4/iter-1/{DEVELOPER}")), 32);
    assert_eq!(first.aborted_at_call, Some(51));
    assert_eq!(first.cumulative_tokens_at_abort, 1_790_635);
    assert!(first.project_writes_after_the_end.is_empty());

    let second = replay_directive_step_budget(&audit_of(&format!("round4/iter-2/{DEVELOPER}")), 32);
    assert_eq!(second.aborted_at_call, None, "iteration 2 never fires");
}

/// The two bands, as a property of the recording rather than a sentence.
///
/// To reach the cost criterion the rule must end the live call at or before call
/// 81 (`K <= 37`); to cut nothing it must not fire before round-4 iteration 3's
/// call 50 (`K >= 43`).  `37 < 43`, so no value of K does both — and with the
/// corrected accounting the cut side is worse than the round-6 report said.
#[test]
fn the_two_bands_do_not_overlap() {
    let live = audit_of(&format!("livecost1/iter-1/{DEVELOPER}"));
    let reachable = (1..=60)
        .map(|k| replay_directive_step_budget(&live, k))
        .filter_map(|replay| {
            replay
                .aborted_at_call
                .map(|call| (replay.budget, call, replay.cumulative_tokens_at_abort))
        })
        .collect::<Vec<_>>();
    let last_under_target = reachable
        .iter()
        .filter(|(_k, _call, tokens)| *tokens < 1_500_000)
        .map(|(k, _call, _tokens)| *k)
        .max()
        .expect("some K ends the live call under the criterion");
    assert_eq!(
        last_under_target, 37,
        "the cost band's edge: K = 37 ends the live call at call 81 for 1,484,934 tokens"
    );
    assert_eq!(
        reachable
            .iter()
            .find(|(k, _call, _tokens)| *k == 37)
            .map(|(_k, call, tokens)| (*call, *tokens)),
        Some((81, 1_484_934)),
        "the last cumulative total under the target is call 81"
    );

    let third = audit_of(&format!("round4/iter-3/{DEVELOPER}"));
    for k in 1..=42 {
        let replay = replay_directive_step_budget(&third, k);
        assert!(
            replay.aborted_at_call.is_some(),
            "K = {k} must fire in iteration 3 (it fires below 43)"
        );
        assert!(
            !replay.project_writes_after_the_end.is_empty(),
            "K = {k} cuts real src/game.rs edits, so the safety band starts at 43"
        );
    }
    let safe = replay_directive_step_budget(&third, 43);
    assert_eq!(safe.aborted_at_call, None);
    assert!(safe.directive_writes_after_the_end.is_empty());
    assert!(safe.project_writes_after_the_end.is_empty());

    assert!(
        last_under_target < 43,
        "the two bands do not overlap: {last_under_target} < 43"
    );
}

/// The detector's own unit surface, exercised through the public helpers on the
/// exact command shapes the recordings contain, so a regression in the parser is
/// caught without the recordings.
#[test]
fn the_command_shapes_the_recordings_contain_are_classified_as_the_recording_says() {
    // A directive the harness executed.
    assert_eq!(scope_of("src/game.rs"), Scope::Project);
    assert_eq!(scope_of(".hoh/scratch/tweak9.ps1"), Scope::Excluded);

    // The two shapes that hid the live call's late writes: a PowerShell
    // `Set-Content` through a variable, and one with the destination written out.
    for command in [
        "powershell -NoProfile -Command \"$p='src\\game.rs'; $c=Get-Content -Raw -Encoding UTF8 $p; Set-Content -NoNewline -Encoding UTF8 $p $c\"",
        "powershell -NoProfile -Command \"(Get-Content -Raw src\\game.rs) -replace 'a','b' | Set-Content -NoNewline src\\game.rs\"",
    ] {
        let writes = hof_rs::harness::write_audit::named_writes(command);
        assert!(
            writes.iter().any(|write| {
                write.target.as_deref().map(scope_of) == Some(Scope::Project)
            }),
            "{command} -> {writes:?}"
        );
    }

    // A copy *into* `.hoh/` mentions a project path as its source and writes
    // nothing in the project; the live call's calls 65 and 103 are these.
    let copies = hof_rs::harness::write_audit::named_writes(
        "copy /Y src\\game.rs .hoh\\scratch\\game_a.rs >nul & copy /Y src\\contract.rs .hoh\\scratch\\c.rs >nul",
    );
    assert!(!copies.is_empty());
    for write in &copies {
        assert_eq!(
            scope_of(write.target.as_deref().unwrap_or_default()),
            Scope::Excluded,
            "{write:?}"
        );
    }

    // A destination the recording never binds is undecided, not guessed.
    let unbound = hof_rs::harness::write_audit::named_writes("Set-Content $out $c");
    assert_eq!(unbound.len(), 1);
    assert_eq!(unbound[0].target, None);

    // `Outcome` is what the recording says, and nothing else.
    assert_eq!(Outcome::Failed(1), Outcome::Failed(1));
    assert_ne!(Outcome::Failed(1), Outcome::Ok);
}
