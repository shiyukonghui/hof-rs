//! DR-28 — artifact hygiene.
//!
//! `smoke-t2`'s `A_1` contained `scripts/_probe.gd`, `_t.txt`, `tmp_args.json`
//! and `_pyout.txt`, all of which became part of the candidate identity.  The
//! runtime now reports them (`artifact_hygiene.suspicious_files`) and the
//! prompts/skills confine every temporary file to `$HOH_SCRATCH_DIR`.

mod common;

use common::*;
use hof_rs::model::Ablation;
use serde_json::Value;

fn suspicious(root: &std::path::Path) -> Vec<String> {
    let json: Value =
        serde_json::from_str(&read(&root.join("runs/run-1/iter-1/result.json"))).unwrap();
    json["artifact_hygiene"]["suspicious_files"]
        .as_array()
        .unwrap_or_else(|| panic!("artifact_hygiene.suspicious_files must be an array: {json}"))
        .iter()
        .map(|value| value.as_str().unwrap_or_default().to_string())
        .collect()
}

// ---------------------------------------------------------------------------
// ① probe files inside the frozen A_t are reported
// ---------------------------------------------------------------------------

#[tokio::test]
async fn probe_files_inside_the_frozen_artifact_are_reported() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let script = vec![
        FakeStep::new(hof_rs::model::Role::Planner).writing(".hoh/plan.md", OK_PLAN),
        FakeStep::new(hof_rs::model::Role::Developer)
            .writing("project.godot", "config_version=5\n")
            .writing("scripts/_probe.gd", "extends Node\n")
            .writing("tmp_x.json", "{}\n"),
        FakeStep::new(hof_rs::model::Role::Tester)
            .writing(".hoh/evidence/move.json", "{}\n")
            .writing(".hoh/evidence.json", &ok_evidence(1, "")),
    ];
    let (result, _) = run_scenario(root, 1, script, Ablation::default(), FakeAdapter::new()).await;
    result.expect("litter is a report, not a failure");

    let found = suspicious(root);
    assert!(
        found.contains(&"scripts/_probe.gd".to_string()),
        "the probe script must be reported with its relative path: {found:?}"
    );
    assert!(
        found.contains(&"tmp_x.json".to_string()),
        "the probe json must be reported with its relative path: {found:?}"
    );
    // Report-only: the file is still there for the Planner to clean up.
    assert!(root.join("workspace/scripts/_probe.gd").is_file());
}

#[tokio::test]
async fn a_clean_artifact_reports_no_suspicious_files() {
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
    assert_eq!(
        suspicious(root),
        Vec::<String>::new(),
        "a clean project must not be flagged"
    );
}

#[tokio::test]
async fn files_under_the_scratch_directory_are_never_flagged() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let script = vec![
        FakeStep::new(hof_rs::model::Role::Planner).writing(".hoh/plan.md", OK_PLAN),
        FakeStep::new(hof_rs::model::Role::Developer)
            .writing("project.godot", "config_version=5\n")
            .writing(".hoh/scratch/_probe.gd", "extends Node\n")
            .writing(".hoh/scratch/tmp_args.json", "{}\n"),
        FakeStep::new(hof_rs::model::Role::Tester)
            .writing(".hoh/evidence/move.json", "{}\n")
            .writing(".hoh/evidence.json", &ok_evidence(1, "")),
    ];
    let (result, _) = run_scenario(root, 1, script, Ablation::default(), FakeAdapter::new()).await;
    result.expect("the happy path must complete");
    assert!(
        suspicious(root).is_empty(),
        "the scratch directory is hash-excluded and must never be flagged"
    );
}

// ---------------------------------------------------------------------------
// ③ the scratch constraint reaches the roles
// ---------------------------------------------------------------------------

#[test]
fn prompts_and_skills_confine_temporary_files_to_the_scratch_dir() {
    // DR-66: the claim is about what a role is *told*, so the delivered text is
    // what gets asserted — the raw template still carries `{{HOH_SCRATCH_DIR}}`.
    for (name, prompt) in [
        (
            "planner.md",
            delivered_prompt(hof_rs::prompts::PLANNER_PROMPT),
        ),
        (
            "developer.md",
            delivered_prompt(hof_rs::prompts::DEVELOPER_PROMPT),
        ),
        (
            "tester.md",
            delivered_prompt(hof_rs::prompts::TESTER_PROMPT),
        ),
    ] {
        assert!(
            prompt.contains(&scratch_var()),
            "{name} must name the scratch directory in its real shell syntax"
        );
        assert!(
            prompt.contains("tmp_") && prompt.contains(".bak"),
            "{name} must name the forbidden litter patterns"
        );
        // The old assertion was a bare `contains("$HOH_SCRATCH_DIR")`; on a cmd
        // shell that string expands to nothing, so it could be present and the
        // instruction still be unrunnable.  Pin the syntax to the host.
        if cfg!(windows) {
            assert!(
                !prompt.contains("$HOH_SCRATCH_DIR"),
                "{name} still hands the role a POSIX variable reference"
            );
        }
    }
    for (name, content) in [
        ("godot-dev.md", delivered_skill("godot-dev.md")),
        ("godot-testing.md", delivered_skill("godot-testing.md")),
    ] {
        assert!(
            content.contains("HOH_SCRATCH_DIR"),
            "skill {name} must explain where temporary files go"
        );
    }
}

/// `%HOH_SCRATCH_DIR%` on Windows, `$HOH_SCRATCH_DIR` elsewhere.
fn scratch_var() -> String {
    hof_rs::runtime::shell::ShellFlavor::HOST.var("HOH_SCRATCH_DIR")
}
