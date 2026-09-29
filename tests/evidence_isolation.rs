//! DR-59 — the deterministic evidence area is **per-round isolated**.
//!
//! `smoke-t7` started with `smoke-t6`'s evidence still sitting in
//! `.workspace/mario/.hoh/deterministic/**`, and the Developer really read it:
//! `runs/smoke-t7/iter-1/traj/developer.attempt1.json` `.messages[54]` quotes
//! `pid 108432`, `(UNAVAILABLE: the editor is not clean)` and the
//! `os error 10061` connection failure — all of them the **previous** round's
//! verdicts.  A stale "the editor is not clean" is exactly the kind of claim
//! that can steer the Developer of the next round.
//!
//! So a new round must move the previous round's evidence out of the live read
//! path (`.hoh/deterministic/**`) before any role runs, and it must keep it:
//! moved aside under the repository's existing `*.stale-<ts>` convention, never
//! silently deleted.
//!
//! The observation point below is the harness record of the role invocation:
//! `FakeHarness` snapshots the **whole** invocation cwd (every file, with its
//! bytes) at the moment the role is called, so it sees exactly what the model's
//! tools could have reached at that instant.

mod common;

use std::collections::BTreeMap;

use common::{happy_script, run_scenario, write, FakeAdapter, InvocationRecord};
use hof_rs::model::{Ablation, Role};

/// The live read path every prompt and every raw path names.
const LIVE_DIR: &str = ".hoh/deterministic/";
/// The repository's DR-49 "this was superseded" suffix, applied to the
/// directory this time.
const QUARANTINE_PREFIX: &str = ".hoh/deterministic.stale-";

/// Verbatim excerpt of what `smoke-t6` left behind — the text `smoke-t7`'s
/// Developer actually read in `.messages[54]`.
const PREVIOUS_ROUND_BATTERY: &str = concat!(
    "{\"step_id\":\"editor_errors_baseline\",\"supports\":[\"N1\",\"N3\"],",
    "\"record\":{\"observation\":\"editor reported 1 error(s):",
    " {\\\"count\\\":1,\\\"errors\\\":[\\\"[MCP] capture=off\\\"],\\\"pid\\\":108432,",
    "\\\"port\\\":9877,\\\"process\\\":\\\"editor\\\"}",
    " (UNAVAILABLE: the editor is not clean)\"},\"ok\":false}\n"
);

/// The `smoke-t6` transport failure, from the same stale round.
const PREVIOUS_ROUND_PROBE: &str = concat!(
    "{\"note\":\"Connection Failed: Connect error: (os error 10061)\",",
    "\"step\":\"input_channel_probe\"}\n"
);

/// Seed the workspace exactly the way the previous round left it on disk.
fn seed_previous_round(workspace: &std::path::Path) {
    write(
        &workspace.join(".hoh/deterministic/battery.json"),
        PREVIOUS_ROUND_BATTERY,
    );
    write(
        &workspace.join(".hoh/deterministic/raw/input_channel_probe.json"),
        PREVIOUS_ROUND_PROBE,
    );
}

/// The Developer's own view of its invocation cwd: `relative path -> bytes`.
fn developer_view(records: &[InvocationRecord]) -> BTreeMap<String, String> {
    records
        .iter()
        .find(|record| record.role == Role::Developer)
        .unwrap_or_else(|| {
            panic!(
                "the script never invoked the Developer: {:?}",
                records.iter().map(|r| r.role).collect::<Vec<_>>()
            )
        })
        .files
        .clone()
}

fn keys_matching<'a>(
    files: &'a BTreeMap<String, String>,
    prefix: &str,
) -> Vec<&'a String> {
    files.keys().filter(|key| key.starts_with(prefix)).collect()
}

/// DR-59: a round that starts over a previous round's evidence must not be able
/// to read it, and must not destroy it.
#[tokio::test]
async fn a_new_round_cannot_read_the_previous_round_evidence() {
    let temp = tempfile::tempdir().expect("tempdir");
    let root = temp.path();
    let workspace = root.join("workspace");
    seed_previous_round(&workspace);

    let (result, records) = run_scenario(
        root,
        1,
        happy_script(),
        Ablation::default(),
        FakeAdapter::new(),
    )
    .await;
    result.expect("the round itself must still run");

    let files = developer_view(&records);

    // (1) Isolation: at the instant the Developer is called, nothing is
    // readable under the live deterministic evidence path.
    let live = keys_matching(&files, LIVE_DIR);
    assert!(
        live.is_empty(),
        "DR-59: the previous round's evidence is still on the live read path \
         ({LIVE_DIR}): {live:?}"
    );

    // (2) Preservation: the same bytes were moved aside, not silently deleted.
    let moved = keys_matching(&files, QUARANTINE_PREFIX);
    assert!(
        !moved.is_empty(),
        "DR-59: the previous round's evidence was destroyed instead of being \
         moved aside under `{QUARANTINE_PREFIX}*`"
    );
    assert!(
        moved
            .iter()
            .any(|key| key.ends_with("/battery.json")
                && files.get(*key).map(String::as_str) == Some(PREVIOUS_ROUND_BATTERY)),
        "DR-59: the previous round's battery.json was not preserved byte-for-byte \
         under the quarantine name; moved entries: {moved:?}"
    );
    assert!(
        moved.iter().any(|key| key.ends_with("/raw/input_channel_probe.json")
            && files.get(*key).map(String::as_str) == Some(PREVIOUS_ROUND_PROBE)),
        "DR-59: the previous round's raw probe payload was not preserved \
         byte-for-byte under the quarantine name; moved entries: {moved:?}"
    );
}

/// DR-59: the counter-direction.  A clean round start has nothing to quarantine
/// and must not litter the workspace with an empty `*.stale-*` sibling — the
/// isolation is a decision about the state on disk, not an unconditional sweep.
#[tokio::test]
async fn a_clean_round_start_quarantines_nothing() {
    let temp = tempfile::tempdir().expect("tempdir");
    let root = temp.path();

    let (result, records) = run_scenario(
        root,
        1,
        happy_script(),
        Ablation::default(),
        FakeAdapter::new(),
    )
    .await;
    result.expect("the round itself must still run");

    let files = developer_view(&records);
    let quarantined = keys_matching(&files, QUARANTINE_PREFIX);
    assert!(
        quarantined.is_empty(),
        "DR-59: a clean round start must not create a quarantine entry: {quarantined:?}"
    );
}
