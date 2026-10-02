//! DR-21 — a clean `A₀` and a reproducible starting point.
//!
//! The first smoke run was polluted by two earlier attempts (`.workspace/mario`
//! already contained `Player`/`Goal`/`HUD` nodes and `mcp/` scratch files), so
//! iterations were not comparable.  `--fresh-workspace` rebuilds `A₀`; the
//! cleanup is constrained to the configured workspace directory and must never
//! delete the wrong tree.

mod common;

use std::sync::{Arc, Mutex};

use common::*;
use hof_rs::adapter::{GodotAdapter, ProjectAdapter};
use hof_rs::config::GodotConfig;
use hof_rs::harness::Harness;
use hof_rs::model::{Ablation, Role};
use hof_rs::runtime::role::{RoleInvocation, RoleOutcome};
use hof_rs::runtime::start_state::{fresh_workspace, reset_workspace, StartState, StartStateMode};
use hof_rs::runtime::view::list_tree;
use serde_json::Value;

fn adapter(_addon: &std::path::Path) -> GodotAdapter {
    GodotAdapter::new(
        GodotConfig {
            editor_binary: std::path::PathBuf::new(),
            cache_excludes: vec![".godot".to_string()],
            main_scene: "res://scenes/main.tscn".to_string(),
        },
        true,
    )
}

/// `(relative path, content)` of every file under `root`, ignoring `.hoh`.
fn snapshot_files(root: &std::path::Path) -> Vec<(String, String)> {
    list_tree(root)
        .unwrap()
        .into_iter()
        .filter(|path| !path.starts_with(".hoh/") && path != ".hoh")
        .map(|path| {
            let content = std::fs::read_to_string(root.join(&path)).unwrap_or_default();
            (path, content)
        })
        .collect()
}

/// DR-21 ①: after `--fresh-workspace` the workspace equals the `A₀` product.
#[test]
fn fresh_workspace_rebuilds_exactly_the_initialize_product() {
    let temp = tempfile::tempdir().unwrap();
    let addon = temp.path().join("addon");
    std::fs::create_dir_all(&addon).unwrap();
    std::fs::write(addon.join("plugin.cfg"), "[plugin]\n").unwrap();

    let workspace = temp.path().join("mario");
    let reference = temp.path().join("reference");
    adapter(&addon).initialize(&workspace).unwrap();
    adapter(&addon).initialize(&reference).unwrap();

    // Pollution from earlier attempts, exactly like the real `.workspace/mario`.
    std::fs::create_dir_all(workspace.join("scripts")).unwrap();
    std::fs::write(workspace.join("scripts/player.gd"), "").unwrap();
    std::fs::create_dir_all(workspace.join("mcp")).unwrap();
    std::fs::write(workspace.join("mcp/a_x.json"), "{}\n").unwrap();
    std::fs::create_dir_all(workspace.join("Player/Goal")).unwrap();

    fresh_workspace(&workspace, &adapter(&addon)).expect("fresh workspace");

    assert_eq!(
        snapshot_files(&workspace),
        snapshot_files(&reference),
        "the freshly built workspace must equal the initialize product"
    );
    assert!(!workspace.join("scripts/player.gd").is_file());
    assert!(!workspace.join("mcp").exists());
}

/// DR-81 ④: `--fresh-workspace` removes the **whole** `.godot` cache tree, and
/// the `A₀` scaffold never recreates it.
///
/// That is the mechanism behind `smoke-t14`'s exit 6: the book's order points the
/// editor at the project **before** the run, so the running editor holds a handle
/// to a `.godot/editor/` directory the purge has just removed and its next cache
/// write fails with `Cannot create file 'res://.godot/editor/filesystem_cache10'`
/// — a line that names nothing in the produced project.  The gate must classify
/// that as editor infrastructure (DR-81 ①); this test pins the precondition so
/// the classification is not folklore.
#[test]
fn fresh_workspace_removes_the_editor_cache_and_initialize_never_rebuilds_it() {
    let temp = tempfile::tempdir().unwrap();
    let addon = temp.path().join("addon");
    std::fs::create_dir_all(&addon).unwrap();
    let workspace = temp.path().join("fresh-t14");
    adapter(&addon).initialize(&workspace).unwrap();

    // The state every round starts in: the editor has already imported the
    // project and written its caches.
    std::fs::create_dir_all(workspace.join(".godot/editor")).unwrap();
    std::fs::write(
        workspace.join(".godot/editor/filesystem_cache10"),
        "cache\n",
    )
    .unwrap();
    std::fs::create_dir_all(workspace.join(".godot/imported")).unwrap();

    fresh_workspace(&workspace, &adapter(&addon)).expect("fresh workspace");

    assert!(
        !workspace.join(".godot").exists(),
        "the purge removes the whole `.godot` tree, not only the workspace entries"
    );
    // The scaffold rebuilds `project.godot`/`scenes`/`scripts` and nothing else,
    // so the cache directory the editor had open is simply gone.
    assert!(!workspace.join(".godot/editor").exists());
    assert!(workspace.join("project.godot").is_file());
}

/// DR-21 safety: a missing or non-directory workspace is refused, never purged.
#[test]
fn fresh_workspace_refuses_to_guess() {
    let temp = tempfile::tempdir().unwrap();
    let addon = temp.path().join("addon");

    let missing = temp.path().join("no-such-workspace");
    let error = fresh_workspace(&missing, &adapter(&addon)).expect_err("missing workspace");
    assert!(error.to_string().contains("does not exist"), "{error}");

    let file = temp.path().join("a-file");
    std::fs::write(&file, "not a directory\n").unwrap();
    let error = fresh_workspace(&file, &adapter(&addon)).expect_err("not a directory");
    assert!(error.to_string().contains("not a directory"), "{error}");
    assert!(file.is_file(), "the file must survive the refusal");
}

/// DR-21 safety: a symlink inside the workspace is removed, not followed.
#[test]
fn fresh_workspace_does_not_follow_symlinks_out_of_the_workspace() {
    let temp = tempfile::tempdir().unwrap();
    let addon = temp.path().join("addon");
    let workspace = temp.path().join("mario");
    let outside = temp.path().join("outside");
    std::fs::create_dir_all(&outside).unwrap();
    std::fs::write(outside.join("precious.txt"), "do not delete me\n").unwrap();
    adapter(&addon).initialize(&workspace).unwrap();

    #[cfg(unix)]
    let linked = std::os::unix::fs::symlink(&outside, workspace.join("escape")).is_ok();
    #[cfg(windows)]
    let linked = std::os::windows::fs::symlink_dir(&outside, workspace.join("escape")).is_ok();
    if !linked {
        // Creating a symlink needs privileges on Windows; the guard is still
        // exercised by the "outside stays untouched" assertion below.
        eprintln!("skipping symlink case: could not create a directory symlink");
    }

    fresh_workspace(&workspace, &adapter(&addon)).expect("fresh workspace");
    assert!(
        outside.join("precious.txt").is_file(),
        "the symlink target must never be deleted"
    );
}

/// DR-21 ③: `--reset-workspace` without an `A₀` snapshot fails instead of
/// touching the workspace.
#[test]
fn reset_without_an_a0_snapshot_is_a_typed_error() {
    let temp = tempfile::tempdir().unwrap();
    let workspace = temp.path().join("workspace");
    let run_dir = temp.path().join("runs/run-1");
    std::fs::create_dir_all(&workspace).unwrap();
    std::fs::write(workspace.join("keep.txt"), "untouched\n").unwrap();
    std::fs::create_dir_all(run_dir.join("versions")).unwrap();
    std::fs::write(
        run_dir.join("versions/index.json"),
        r#"{"schema":1,"versions":[]}"#,
    )
    .unwrap();

    let error = reset_workspace(&workspace, &run_dir, &[]).expect_err("no A0 -> error");
    assert!(
        error.to_string().contains("A0") || error.to_string().contains("A₀"),
        "{error}"
    );
    assert_eq!(
        std::fs::read_to_string(workspace.join("keep.txt")).unwrap(),
        "untouched\n",
        "a failed reset must not modify the workspace"
    );
}

/// A harness wrapper that records whether the `A₀` snapshot already existed
/// when a role was invoked.
struct CheckingHarness {
    inner: FakeHarness,
    run_dir: std::path::PathBuf,
    observed: Arc<Mutex<Vec<bool>>>,
}

#[async_trait::async_trait]
impl Harness for CheckingHarness {
    async fn invoke(&self, inv: &RoleInvocation) -> anyhow::Result<RoleOutcome> {
        let index = std::fs::read_to_string(self.run_dir.join("versions/index.json"))
            .ok()
            .and_then(|raw| serde_json::from_str::<Value>(&raw).ok());
        let a0 = index
            .and_then(|value| {
                value["versions"]
                    .as_array()
                    .map(|versions| versions.to_vec())
            })
            .unwrap_or_default()
            .into_iter()
            .find(|entry| entry["iteration"] == 0 && entry["role"] == "init");
        let ready = match &a0 {
            Some(entry) => entry["version_id"]
                .as_str()
                .map(|id| self.run_dir.join("versions").join(id).is_dir())
                .unwrap_or(false),
            None => false,
        };
        self.observed.lock().unwrap().push(ready);
        self.inner.invoke(inv).await
    }
}

/// DR-21 ②: the `A₀` snapshot exists before any role is invoked and its
/// `version_id` is in `index.json`.
#[tokio::test]
async fn a0_snapshot_exists_before_the_first_role_call() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let mut cfg = test_config(root, 1);
    cfg.runtime.spec = root.join("spec.md");
    let spec = write_spec(root);
    let run_dir = cfg.runtime.runs_dir.join("run-1");
    let observed: Arc<Mutex<Vec<bool>>> = Arc::new(Mutex::new(Vec::new()));
    let harness = CheckingHarness {
        inner: FakeHarness::new(happy_script()),
        run_dir: run_dir.clone(),
        observed: observed.clone(),
    };

    let orchestrator = hof_rs::runtime::run_loop::Orchestrator {
        harness: Box::new(harness),
        adapter: Box::new(FakeAdapter::new()),
        tools: Arc::new(FakeToolChannel::new()),
        cfg,
        ablation: Ablation::default(),
        force_init: true,
        start_state: StartState::as_is(),
    };
    hof_rs::runtime::run_loop::run(&orchestrator, &spec, "run-1")
        .await
        .expect("the happy path must complete");

    let observed = observed.lock().unwrap().clone();
    assert_eq!(observed.len(), 3, "three role invocations");
    assert!(
        observed.iter().all(|ready| *ready),
        "the A0 snapshot must exist before every role call: {observed:?}"
    );

    let index: Value = serde_json::from_str(&read(&run_dir.join("versions/index.json"))).unwrap();
    let a0 = &index["versions"][0];
    assert_eq!(a0["iteration"], serde_json::json!(0));
    assert_eq!(a0["role"], serde_json::json!("init"));
    let version_id = a0["version_id"].as_str().unwrap();
    assert!(run_dir.join("versions").join(version_id).is_dir());

    let meta: Value = serde_json::from_str(&read(&run_dir.join("meta.json"))).unwrap();
    assert_eq!(meta["start_state"]["mode"], serde_json::json!("as_is"));
    assert!(meta["start_state"]["version_id"].is_null());
}

/// `meta.json.start_state` reports a fresh start.
#[tokio::test]
async fn meta_reports_the_fresh_start_state() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let mut cfg = test_config(root, 1);
    cfg.runtime.spec = root.join("spec.md");
    let spec = write_spec(root);
    let run_dir = cfg.runtime.runs_dir.join("run-1");

    let orchestrator = hof_rs::runtime::run_loop::Orchestrator {
        harness: Box::new(FakeHarness::new(happy_script())),
        adapter: Box::new(FakeAdapter::new()),
        tools: Arc::new(FakeToolChannel::new()),
        cfg,
        ablation: Ablation::default(),
        force_init: true,
        start_state: StartState {
            mode: StartStateMode::Fresh,
            version_id: None,
        },
    };
    hof_rs::runtime::run_loop::run(&orchestrator, &spec, "run-1")
        .await
        .expect("the happy path must complete");

    let meta: Value = serde_json::from_str(&read(&run_dir.join("meta.json"))).unwrap();
    assert_eq!(meta["start_state"]["mode"], serde_json::json!("fresh"));
}

/// The start-state enum keeps the frozen wire spelling.
#[test]
fn start_state_modes_serialize_as_documented() {
    for (mode, expected) in [
        (StartStateMode::Fresh, "fresh"),
        (StartStateMode::Reset, "reset"),
        (StartStateMode::AsIs, "as_is"),
    ] {
        let value = serde_json::to_value(StartState {
            mode,
            version_id: None,
        })
        .unwrap();
        assert_eq!(value["mode"], serde_json::json!(expected));
    }
    assert_eq!(Role::Planner.as_str(), "planner");
}
