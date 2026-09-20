//! R1/R2/R3/R5/R9/R11 — the runtime semantics that the whole project exists
//! to make auditable: independence of the three role calls, the single-writer
//! rule, the two-channel state rule, the per-iteration record, and the public
//! information boundary.

mod common;

use common::*;
use hof_rs::errors::{as_hof_error, HofError};
use hof_rs::model::{Ablation, ContractViolation, Role};
use hof_rs::runtime::policy::{hash_tree, tool_allowed, tree_manifest};
use hof_rs::runtime::run_loop::MCP_SCOPE_WARNING;
use hof_rs::runtime::view::list_tree;

fn workspace_of(root: &std::path::Path) -> std::path::PathBuf {
    root.join("workspace")
}

fn run_dir(root: &std::path::Path) -> std::path::PathBuf {
    root.join("runs/run-1")
}

#[tokio::test]
async fn three_independent_invocations() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let (result, records) = run_scenario(
        root,
        1,
        happy_script(),
        Ablation::default(),
        FakeAdapter::new(),
    )
    .await;
    result.expect("the happy path must complete");

    assert_eq!(records.len(), 3, "exactly three invocations are expected");
    assert_eq!(
        records.iter().map(|record| record.role).collect::<Vec<_>>(),
        vec![Role::Planner, Role::Developer, Role::Tester]
    );

    for record in &records {
        assert_eq!(
            record.env.get("HOH_ROLE").map(String::as_str),
            Some(record.role.as_str()),
            "every invocation must carry its own role"
        );
    }

    // Zero state sharing: the three calls run in different directories.
    assert_eq!(records[1].cwd, workspace_of(root));
    assert_ne!(records[0].cwd, records[1].cwd);
    assert_ne!(records[2].cwd, records[0].cwd);
    assert_ne!(records[2].cwd, records[1].cwd);

    // Planner and Tester work on copies, never on the real artifact.
    assert!(records[0].cwd.ends_with("planner-view"));
    assert!(records[2].cwd.ends_with("candidate"));
}

#[tokio::test]
async fn planner_cannot_write_artifact() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let workspace = workspace_of(root);
    let script = vec![
        FakeStep::new(Role::Planner)
            .writing(".hoh/plan.md", OK_PLAN)
            .outside(workspace.join("scripts/hacked.gd"), "extends Node\n"),
        FakeStep::new(Role::Developer).writing("project.godot", "config_version=5\n"),
        FakeStep::new(Role::Tester)
            .writing(".hoh/evidence/move.json", "{}\n")
            .writing(".hoh/evidence.json", &ok_evidence(1, "")),
    ];
    let (result, _) = run_scenario(root, 1, script, Ablation::default(), FakeAdapter::new()).await;

    let error = result.expect_err("planning must not be able to write the artifact");
    let hof = as_hof_error(&error).expect("typed error");
    match hof {
        HofError::Contract { violation, .. } => {
            assert_eq!(*violation, ContractViolation::ReadOnlyRoleWroteArtifact);
        }
        other => panic!("unexpected error: {other:?}"),
    }

    let result_json: serde_json::Value =
        serde_json::from_str(&read(&run_dir(root).join("iter-1/result.json"))).unwrap();
    assert_eq!(result_json["ok"], serde_json::json!(false));
    assert_eq!(result_json["failed_role"], serde_json::json!("planner"));
    // DR-2: the violation names the file the planner wrote.
    assert_eq!(
        result_json["evidence_diff"]["added"],
        serde_json::json!(["scripts/hacked.gd"])
    );
}

#[tokio::test]
async fn developer_is_only_writer() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let (result, records) = run_scenario(
        root,
        1,
        happy_script(),
        Ablation::default(),
        FakeAdapter::new(),
    )
    .await;
    let summary = result.expect("the happy path must complete");

    // The Developer stage is the only stage allowed to change the artifact, and
    // the resulting hash is what the runtime records as A_t.
    let workspace = workspace_of(root);
    let excludes = hof_rs::runtime::policy::HashExcludes::new(["cache".to_string()]).merged();
    let final_hash = hash_tree(&workspace, &excludes).unwrap();
    assert_eq!(
        summary.final_version_id.as_deref(),
        Some(final_hash.as_str())
    );
    assert_eq!(records[1].cwd, workspace);

    let index: serde_json::Value =
        serde_json::from_str(&read(&run_dir(root).join("versions/index.json"))).unwrap();
    let versions = index["versions"].as_array().unwrap();
    assert_eq!(
        versions.len(),
        2,
        "A0 init snapshot plus one developer version"
    );
    assert_eq!(versions[0]["role"], serde_json::json!("init"));
    assert_eq!(versions[0]["iteration"], serde_json::json!(0));
    assert_eq!(versions[1]["role"], serde_json::json!("developer"));
    assert_eq!(versions[1]["iteration"], serde_json::json!(1));
    assert_eq!(versions[1]["version_id"], serde_json::json!(final_hash));
}

#[tokio::test]
async fn no_third_state_channel() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let marker = "UNIQUE_D1_MARKER";
    let plan_one = format!(
        "## Project Planner Priorities\n### Priority Order\n1. **{marker}** - first iteration\n\
         ### Preservation Gate\n- launches\n### Acceptance Gate\n- moves\n"
    );
    let script = vec![
        FakeStep::new(Role::Planner).writing(".hoh/plan.md", &plan_one),
        FakeStep::new(Role::Developer).writing("project.godot", "config_version=5\n"),
        FakeStep::new(Role::Tester)
            .writing(".hoh/evidence/move.json", "{}\n")
            .writing(".hoh/evidence.json", &ok_evidence(1, "")),
        FakeStep::new(Role::Planner).writing(".hoh/plan.md", OK_PLAN),
        FakeStep::new(Role::Developer).writing("scripts/player.gd", "extends Node\n"),
        FakeStep::new(Role::Tester)
            .writing(".hoh/evidence/move.json", "{}\n")
            .writing(".hoh/evidence.json", &ok_evidence(2, "")),
    ];
    let (result, records) =
        run_scenario(root, 2, script, Ablation::default(), FakeAdapter::new()).await;
    result.expect("two iterations must complete");

    let second_planner = records
        .iter()
        .find(|record| record.role == Role::Planner && record.iteration == 2)
        .expect("iteration 2 must invoke the planner");

    // D_t is shared inside one iteration only: it must not leak forward.
    assert!(
        !second_planner.task_prompt.contains(marker),
        "the previous development document leaked into the next planner task"
    );
    assert!(
        !second_planner.system_prompt.contains(marker),
        "the previous development document leaked into the next planner system prompt"
    );
    for (path, content) in &second_planner.files {
        assert!(
            !content.contains(marker),
            "the previous development document leaked into planner view file {path}"
        );
    }

    // The prompt states the boundary explicitly (prompt-side guarantee of R5).
    assert!(second_planner
        .system_prompt
        .contains("Do not request or reconstruct the previous development document"));
}

#[tokio::test]
async fn records_all_artifacts() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let (result, _) = run_scenario(
        root,
        1,
        happy_script(),
        Ablation::default(),
        FakeAdapter::new(),
    )
    .await;
    result.expect("the happy path must complete");

    let iter_dir = run_dir(root).join("iter-1");
    for name in [
        "plan.md",
        "evidence.json",
        "qa_report.md",
        "usage.json",
        "result.json",
    ] {
        assert!(
            iter_dir.join(name).is_file(),
            "missing iter artifact {name}"
        );
    }

    let traj: Vec<String> = std::fs::read_dir(iter_dir.join("traj"))
        .expect("traj dir")
        .map(|entry| entry.unwrap().file_name().to_string_lossy().into_owned())
        .collect();
    for role in ["planner", "developer", "tester"] {
        assert!(
            traj.iter()
                .any(|name| name.starts_with(role) && name.ends_with(".json")),
            "missing trajectory for {role}: {traj:?}"
        );
    }

    let logs = std::fs::read_dir(iter_dir.join("logs")).expect("logs dir");
    assert!(logs.count() >= 1, "at least one process log is expected");

    let meta: serde_json::Value =
        serde_json::from_str(&read(&run_dir(root).join("meta.json"))).unwrap();
    let spec = hof_rs::config::load_spec(&root.join("spec.md")).unwrap();
    assert_eq!(meta["spec"]["sha256"], serde_json::json!(spec.sha256));

    let usage: serde_json::Value =
        serde_json::from_str(&read(&iter_dir.join("usage.json"))).unwrap();
    assert_eq!(usage.as_array().unwrap().len(), 3);

    let result_json: serde_json::Value =
        serde_json::from_str(&read(&iter_dir.join("result.json"))).unwrap();
    assert_eq!(result_json["ok"], serde_json::json!(true));

    // The materialized evidence is the bound bundle, not the raw submission.
    let evidence: serde_json::Value =
        serde_json::from_str(&read(&iter_dir.join("evidence.json"))).unwrap();
    let candidate_id = result_json["candidate_id"].as_str().unwrap();
    assert_eq!(
        evidence["verified_records"][0]["execution_records"][0]["candidate_id"],
        serde_json::json!(candidate_id)
    );
}

#[tokio::test]
async fn no_private_information_in_views() {
    const HIDDEN: &str = "HIDDEN_TEST_MARKER";
    const PRIVATE: &str = "PRIVATE_SCORE_MARKER";
    const RUBRIC: &str = "SECRET_RUBRIC_MARKER";

    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();

    // A private rubric living outside the project must never reach any view.
    write(&root.join("private_rubric.json"), RUBRIC);
    // Files that exist inside the project itself: they may be copied as project
    // content, but they must never be injected into a prompt or into `.hoh/`.
    {
        let mut cfg = test_config(root, 1);
        cfg.runtime.spec = root.join("spec.md");
    }
    write(
        &workspace_of(root).join("tests/secret.json"),
        &format!("{{\"hidden\": \"{HIDDEN}\"}}"),
    );
    write(
        &workspace_of(root).join("runs/private.json"),
        &format!("{{\"score\": \"{PRIVATE}\"}}"),
    );

    let (result, records) = run_scenario(
        root,
        1,
        happy_script(),
        Ablation::default(),
        FakeAdapter::new(),
    )
    .await;
    result.expect("the happy path must complete");

    for record in &records {
        for prompt in [&record.system_prompt, &record.task_prompt] {
            for marker in [HIDDEN, PRIVATE, RUBRIC] {
                assert!(
                    !prompt.contains(marker),
                    "private marker {marker} leaked into a {:?} prompt",
                    record.role
                );
            }
        }
        for (path, content) in &record.files {
            assert!(
                !content.contains(RUBRIC),
                "the private rubric leaked into view file {path}"
            );
            if path.starts_with(".hoh/") {
                for marker in [HIDDEN, PRIVATE, RUBRIC] {
                    assert!(
                        !content.contains(marker),
                        "private marker {marker} leaked into injected input {path}"
                    );
                }
            }
        }
    }

    // Tool side of R11/R13: the Tester may not mutate anything.
    assert!(!tool_allowed(Role::Tester, "add_node"));
    assert!(!tool_allowed(Role::Tester, "execute_editor_script"));
    assert!(!tool_allowed(Role::Planner, "get_editor_errors"));
}

/// DR-3: `runtime.private_excludes` removes a path from the copied role views
/// only — the artifact identity (`hash_tree`) still covers it, so R2/R3
/// write-detection is not weakened.
#[tokio::test]
async fn private_excludes_stay_out_of_views_but_inside_the_identity() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let workspace = workspace_of(root);
    write(&workspace.join("tests/secret.json"), "{\"hidden\":true}\n");
    write(&workspace.join("tests/public.json"), "{}\n");

    let (result, records) = run_scenario_with_private_excludes(
        root,
        1,
        happy_script(),
        Ablation::default(),
        FakeAdapter::new(),
        vec!["tests/secret.json".to_string()],
    )
    .await;
    result.expect("the happy path must complete with private excludes configured");

    for view in ["planner-view", "candidate"] {
        let files = list_tree(&run_dir(root).join(format!("iter-1/{view}"))).unwrap();
        assert!(
            !files.contains(&"tests/secret.json".to_string()),
            "the private file leaked into the {view}: {files:?}"
        );
        assert!(
            files.contains(&"tests/public.json".to_string()),
            "only the configured path may be withheld from {view}: {files:?}"
        );
    }

    // The Developer works on the real workspace, which is not a copy.
    let developer = records
        .iter()
        .find(|record| record.role == Role::Developer)
        .expect("the developer stage runs");
    assert!(developer.files.contains_key("tests/secret.json"));

    // The exclusion must not reach `hash_tree`: removing the file changes A_t.
    let excludes = hof_rs::runtime::policy::HashExcludes::new(["cache".to_string()]).merged();
    let manifest = tree_manifest(&workspace, &excludes).unwrap();
    assert!(manifest.contains_key("tests/secret.json"));
    let before = hash_tree(&workspace, &excludes).unwrap();
    std::fs::remove_file(workspace.join("tests/secret.json")).unwrap();
    let after = hash_tree(&workspace, &excludes).unwrap();
    assert_ne!(
        before, after,
        "the private file must still be part of the artifact identity"
    );
}

/// DR-6: the D7 scope limitation is restated in every iteration `result.json`.
#[tokio::test]
async fn every_result_json_carries_the_scope_warning() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let (result, _) = run_scenario(
        root,
        1,
        happy_script(),
        Ablation::default(),
        FakeAdapter::new(),
    )
    .await;
    result.expect("the happy path must complete");

    let result_json: serde_json::Value =
        serde_json::from_str(&read(&run_dir(root).join("iter-1/result.json"))).unwrap();
    let warnings: Vec<String> = result_json["warnings"]
        .as_array()
        .expect("result.json warnings")
        .iter()
        .map(|value| value.as_str().unwrap_or_default().to_string())
        .collect();
    assert!(
        warnings.iter().any(|warning| warning == MCP_SCOPE_WARNING),
        "every result.json must repeat the MCP scope warning: {warnings:?}"
    );
}
