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
//! DR-61 tightened the *where*: the DR-59 quarantine landed at
//! `.hoh/deterministic.stale-<ts>/`, still inside the role's working directory,
//! so a wildcard walk (`ls .hoh`) still reached it (independent acceptance
//! DEF-1).  The bytes now move to `runs/<run_id>/quarantine/**`, which no role's
//! cwd contains — so these tests assert both the empty live path **and** the
//! absence of any `.stale-*` entry from the view, with the preserved bytes read
//! from disk instead.
//!
//! The observation point below is the harness record of the role invocation:
//! `FakeHarness` snapshots the **whole** invocation cwd (every file, with its
//! bytes) at the moment the role is called, so it sees exactly what the model's
//! tools could have reached at that instant.

mod common;

use std::collections::BTreeMap;
use std::path::{Path, PathBuf};
use std::sync::Arc;

use common::{
    happy_script, run_scenario, test_config, write, write_spec, FakeAdapter, FakeHarness, FakeStep,
    FakeToolChannel, InvocationRecord,
};
use hof_rs::model::{Ablation, Role};

/// The live read path every prompt and every raw path names.
const LIVE_DIR: &str = ".hoh/deterministic/";
/// The repository's DR-49 "this was superseded" suffix.  DR-61 moved the
/// quarantine **outside** the role's working directory, so this marker must not
/// appear anywhere in a role's view any more.
const STALE_MARKER: &str = ".stale-";

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

fn keys_matching<'a>(files: &'a BTreeMap<String, String>, prefix: &str) -> Vec<&'a String> {
    files.keys().filter(|key| key.starts_with(prefix)).collect()
}

/// Keys whose path contains `needle` (the DR-49 `.stale-` marker is a suffix,
/// not a prefix).
fn keys_containing<'a>(files: &'a BTreeMap<String, String>, needle: &str) -> Vec<&'a String> {
    files.keys().filter(|key| key.contains(needle)).collect()
}

/// DR-61: `relative path -> bytes` of everything under a directory on disk.
fn walk(root: &Path) -> BTreeMap<String, String> {
    let mut files = BTreeMap::new();
    if !root.exists() {
        return files;
    }
    for entry in walkdir::WalkDir::new(root).follow_links(false) {
        let Ok(entry) = entry else { continue };
        if !entry.file_type().is_file() {
            continue;
        }
        let relative = entry
            .path()
            .strip_prefix(root)
            .unwrap_or(entry.path())
            .components()
            .map(|component| component.as_os_str().to_string_lossy().into_owned())
            .collect::<Vec<_>>()
            .join("/");
        files.insert(
            relative,
            std::fs::read_to_string(entry.path()).unwrap_or_default(),
        );
    }
    files
}

/// DR-61: the run's quarantine directory — outside the workspace.
fn quarantine_dir(root: &Path, run_id: &str) -> PathBuf {
    root.join("runs").join(run_id).join("quarantine")
}

/// The bytes preserved under a run's quarantine for a given suffix: the moved
/// entry is `quarantine/deterministic.stale-<ts>/battery.json`, so lookups are
/// by suffix, not by exact key.
fn kept_bytes<'a>(kept: &'a BTreeMap<String, String>, suffix: &str) -> Option<&'a String> {
    kept.iter()
        .find(|(path, _)| path.ends_with(suffix))
        .map(|(_, bytes)| bytes)
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

    // (2) Preservation: the same bytes were moved aside, not silently deleted —
    // and DR-61 moved them **out of the role's cwd**, so no view entry carries
    // the DR-49 marker any more.
    let marked = keys_containing(&files, STALE_MARKER);
    assert!(
        marked.is_empty(),
        "DR-61: a superseded `.stale-*` path is still inside the Developer's cwd: {marked:?}"
    );
    let kept = walk(&quarantine_dir(root, "run-1"));
    assert_eq!(
        kept_bytes(&kept, "battery.json").map(String::as_str),
        Some(PREVIOUS_ROUND_BATTERY),
        "DR-61: the previous round's battery.json was not preserved byte-for-byte \
         under the run's quarantine; kept entries: {:?}",
        kept.keys().collect::<Vec<_>>()
    );
    assert_eq!(
        kept_bytes(&kept, "input_channel_probe.json").map(String::as_str),
        Some(PREVIOUS_ROUND_PROBE),
        "DR-61: the previous round's raw probe payload was not preserved \
         byte-for-byte under the run's quarantine; kept entries: {:?}",
        kept.keys().collect::<Vec<_>>()
    );
    assert!(
        !quarantine_dir(root, "run-1").starts_with(&workspace),
        "DR-61: the quarantine must live outside the role's working directory"
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
    let quarantined = keys_containing(&files, STALE_MARKER);
    assert!(
        quarantined.is_empty(),
        "DR-61: a clean round start must not create a quarantine entry in the cwd: \
         {quarantined:?}"
    );
    assert!(
        !quarantine_dir(root, "run-1").exists(),
        "DR-61: a clean round start must not create an empty quarantine directory"
    );
}

/// One whole round with an explicit run id — the shape of
/// `common::run_scenario`, but two of them share one workspace here.
async fn run_round(root: &Path, run_id: &str, script: Vec<FakeStep>) -> Vec<InvocationRecord> {
    let mut cfg = test_config(root, 1);
    cfg.runtime.spec = root.join("spec.md");
    let spec = write_spec(root);
    let harness = FakeHarness::new(script);
    let observer = harness.clone();
    let orchestrator = hof_rs::runtime::run_loop::Orchestrator {
        harness: Box::new(harness),
        adapter: Box::new(FakeAdapter::new()),
        tools: Arc::new(FakeToolChannel::new()),
        cfg,
        ablation: Ablation::default(),
        force_init: true,
        start_state: hof_rs::runtime::start_state::StartState::as_is(),
    };
    hof_rs::runtime::run_loop::run(&orchestrator, &spec, run_id)
        .await
        .expect("the round must run");
    observer.records()
}

/// DR-59: the faithful reproduction of `smoke-t6` → `smoke-t7`.  Two rounds run
/// back to back over one workspace; round two must not be able to read the
/// evidence round one left on disk.
#[tokio::test]
async fn round_two_cannot_read_round_one_evidence() {
    let temp = tempfile::tempdir().expect("tempdir");
    let root = temp.path();
    let workspace = root.join("workspace");

    run_round(root, "run-1", happy_script()).await;
    // Round one really did leave deterministic evidence behind: that is the
    // precondition the leak needs.
    let left_behind = workspace.join(".hoh/deterministic/build.json");
    assert!(
        left_behind.is_file(),
        "round one must have produced deterministic evidence for this test to mean \
         anything: {left_behind:?}"
    );

    // DR-67: round two must also be a *real* round.  `happy_script` writes the
    // same `project.godot` bytes in both rounds, so without this the Developer
    // stage of round two changes nothing and the new zero-increment gate fails
    // it — which would make this test fail for a reason unrelated to evidence
    // isolation.  Changing the project first gives round two a genuine increment
    // (its Developer write is then a real change), so the isolation invariant is
    // measured on a round that actually did something: a strengthening of the
    // fixture, not a relaxation of it.
    write(
        &workspace.join("project.godot"),
        "config_version=5\n# run-two\n",
    );
    assert_eq!(
        std::fs::read_to_string(workspace.join("project.godot")).unwrap(),
        "config_version=5\n# run-two\n",
        "the fixture must hand round two different project bytes"
    );

    let second = run_round(root, "run-2", happy_script()).await;
    let files = developer_view(&second);

    let live = keys_matching(&files, LIVE_DIR);
    assert!(
        live.is_empty(),
        "DR-59: round two's Developer can still read round one's evidence: {live:?}"
    );
    let marked = keys_containing(&files, STALE_MARKER);
    assert!(
        marked.is_empty(),
        "DR-61: round one's quarantine is still walkable inside round two's cwd: {marked:?}"
    );
    let kept = walk(&quarantine_dir(root, "run-2"));
    assert!(
        kept.values()
            .any(|content| content.contains("fake adapter: build check ok")),
        "DR-59: round one's evidence must be moved aside intact, not deleted; kept \
         entries: {:?}",
        kept.keys().collect::<Vec<_>>()
    );
}
