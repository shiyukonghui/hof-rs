//! R8 — the three ablation switches.  Each one closes exactly one
//! cross-iteration input, and nothing else may change.  The scenarios run in
//! the *same* directory with the same run id, so the recorded invocations can
//! be compared byte-for-byte (including absolute paths).

mod common;

use std::collections::BTreeSet;

use common::*;
use hof_rs::model::{Ablation, Role};

const D1_PLAN: &str = "## Project Planner Priorities\n\
### Priority Order\n\
1. **D1Marker** - get the project running\n\
### Preservation Gate\n\
- the project still launches\n\
### Acceptance Gate\n\
- the scene opens\n";

fn full_script() -> Vec<FakeStep> {
    vec![
        FakeStep::new(Role::Planner).writing(".hoh/plan.md", D1_PLAN),
        FakeStep::new(Role::Developer).writing("project.godot", "config_version=5\n"),
        FakeStep::new(Role::Tester)
            .writing(".hoh/evidence/move.json", "{}\n")
            .writing(".hoh/evidence.json", &ok_evidence(1, "")),
        FakeStep::new(Role::Planner).writing(".hoh/plan.md", OK_PLAN),
        FakeStep::new(Role::Developer).writing("scripts/player.gd", "extends Node\n"),
        FakeStep::new(Role::Tester)
            .writing(".hoh/evidence/move.json", "{}\n")
            .writing(".hoh/evidence.json", &ok_evidence(2, "")),
    ]
}

fn script_without_second_planner() -> Vec<FakeStep> {
    let mut script = full_script();
    script.remove(3);
    script
}

fn reset(root: &std::path::Path) {
    for name in ["runs", "workspace"] {
        let _ = std::fs::remove_dir_all(root.join(name));
    }
}

/// Relative paths whose content differs between two invocations.
fn file_diff(a: &InvocationRecord, b: &InvocationRecord) -> Vec<String> {
    let keys: BTreeSet<&String> = a.files.keys().chain(b.files.keys()).collect();
    keys.into_iter()
        .filter(|key| a.files.get(*key) != b.files.get(*key))
        .cloned()
        .collect()
}

fn assert_only_files_differ(a: &InvocationRecord, b: &InvocationRecord) {
    assert_eq!(
        a.without_files(),
        b.without_files(),
        "only the file inputs of one switch may change (role {:?} iteration {})",
        a.role,
        a.iteration
    );
}

#[tokio::test]
async fn plan_update_off_only_changes_plan() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();

    let (baseline, base_records) = run_scenario(
        root,
        2,
        full_script(),
        Ablation::default(),
        FakeAdapter::new(),
    )
    .await;
    baseline.expect("baseline run");
    reset(root);

    let plan_off = Ablation {
        plan_update: false,
        ..Ablation::default()
    };
    let (ablated, off_records) = run_scenario(
        root,
        2,
        script_without_second_planner(),
        plan_off,
        FakeAdapter::new(),
    )
    .await;
    ablated.expect("ablated run");

    // D_t is reused, so the Planner is not called at all for t > 1.
    assert_eq!(base_records.len(), 6);
    assert_eq!(off_records.len(), 5);
    assert!(!off_records
        .iter()
        .any(|record| record.role == Role::Planner && record.iteration == 2));

    let baseline_others: Vec<&InvocationRecord> = base_records
        .iter()
        .filter(|record| !(record.role == Role::Planner && record.iteration == 2))
        .collect();
    for (expected, actual) in baseline_others.iter().zip(off_records.iter()) {
        assert_only_files_differ(expected, actual);
        let diff = file_diff(expected, actual);
        if actual.iteration == 2 {
            // The single changed input is the reused plan document; it is
            // injected into both the Developer view and the QA candidate.
            assert_eq!(diff, vec![".hoh/plan.md".to_string()]);
            assert_eq!(expected.files[".hoh/plan.md"], OK_PLAN);
            assert_eq!(actual.files[".hoh/plan.md"], D1_PLAN);
        } else {
            assert!(diff.is_empty(), "unexpected input change: {diff:?}");
        }
    }
}

#[tokio::test]
async fn evidence_off_only_changes_evidence() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();

    let (baseline, base_records) = run_scenario(
        root,
        2,
        full_script(),
        Ablation::default(),
        FakeAdapter::new(),
    )
    .await;
    baseline.expect("baseline run");
    reset(root);

    let evidence_off = Ablation {
        evidence_feedback: false,
        ..Ablation::default()
    };
    let (ablated, off_records) =
        run_scenario(root, 2, full_script(), evidence_off, FakeAdapter::new()).await;
    ablated.expect("ablated run");

    assert_eq!(base_records.len(), 6);
    assert_eq!(off_records.len(), 6);

    for (expected, actual) in base_records.iter().zip(off_records.iter()) {
        assert_only_files_differ(expected, actual);
        let diff = file_diff(expected, actual);
        if actual.role == Role::Planner && actual.iteration == 2 {
            // The Planner sees an empty evidence bundle instead of E_1.
            assert_eq!(diff, vec![".hoh/evidence.json".to_string()]);
            let baseline_evidence: serde_json::Value =
                serde_json::from_str(&expected.files[".hoh/evidence.json"]).unwrap();
            let ablated_evidence: serde_json::Value =
                serde_json::from_str(&actual.files[".hoh/evidence.json"]).unwrap();
            assert_eq!(
                baseline_evidence["verified_records"]
                    .as_array()
                    .unwrap()
                    .len(),
                1
            );
            assert!(ablated_evidence["verified_records"]
                .as_array()
                .unwrap()
                .is_empty());
            assert!(ablated_evidence["gap_records"]
                .as_array()
                .unwrap()
                .is_empty());
            assert_eq!(ablated_evidence["qa_status"], serde_json::json!("partial"));
        } else {
            assert!(diff.is_empty(), "unexpected input change: {diff:?}");
        }
    }

    // The Tester still runs and warm-start is untouched.
    assert!(off_records
        .iter()
        .any(|record| record.role == Role::Tester && record.iteration == 2));
}

#[tokio::test]
async fn warm_start_off_only_changes_source() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();

    let (baseline, base_records) = run_scenario(
        root,
        2,
        full_script(),
        Ablation::default(),
        FakeAdapter::new(),
    )
    .await;
    baseline.expect("baseline run");
    reset(root);

    let warm_off = Ablation {
        warm_start: false,
        ..Ablation::default()
    };
    let (ablated, off_records) =
        run_scenario(root, 2, full_script(), warm_off, FakeAdapter::new()).await;
    ablated.expect("ablated run");

    assert_eq!(base_records.len(), 6);
    assert_eq!(off_records.len(), 6);

    for (expected, actual) in base_records.iter().zip(off_records.iter()) {
        // Prompts, environment and limits are untouched: only the source of
        // the view changes.
        assert_only_files_differ(expected, actual);
        let diff = file_diff(expected, actual);
        if actual.iteration == 1 {
            assert!(diff.is_empty(), "iteration 1 must be identical: {diff:?}");
        } else {
            assert!(
                !diff.is_empty(),
                "{:?} iteration 2 must start from A0 instead of A1",
                actual.role
            );
        }
    }

    // The regression is visible in the artifact itself: the warm-started run
    // keeps project.godot, the ablated one starts over from empty A0.
    let developer_two = off_records
        .iter()
        .find(|record| record.role == Role::Developer && record.iteration == 2)
        .unwrap();
    assert!(!developer_two.files.contains_key("project.godot"));
    let baseline_developer_two = base_records
        .iter()
        .find(|record| record.role == Role::Developer && record.iteration == 2)
        .unwrap();
    assert!(baseline_developer_two.files.contains_key("project.godot"));
}
