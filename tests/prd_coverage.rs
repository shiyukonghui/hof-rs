//! DR-39 — `gate ok` is not "the product is good".
//!
//! `smoke-t5` ended with `exit 0` and `artifact_gate.launchable = true` while
//! `F1..F17` were all gaps and the game was unplayable.  The exit code stays
//! about the runtime contract, so the PRD coverage has to be published next to
//! it: `result.json.prd_coverage`, a `prd=` column in `hoh status`, and one
//! summary line at the end of `hoh run`.
//!
//! The runtime only **derives** these numbers from the Tester's own
//! `verified_records`/`gap_records` — it never judges a claim.

mod common;

use common::*;
use hof_rs::model::{Ablation, PrdCoverage, Role};
use serde_json::{json, Value};

/// A schema-valid evidence bundle with `verified` verified and `gap` gap
/// claims, all citing one real file of the candidate view.
fn coverage_evidence(verified: usize, gap: usize) -> String {
    let exec = |id: &str| {
        serde_json::json!([{
            "type": "assert",
            "path": ".hoh/evidence/coverage.json",
            "observation": format!("observation for {id}"),
            "candidate_id": ""
        }])
    };
    let verified_records: Vec<Value> = (1..=verified)
        .map(|index| {
            let id = format!("F{index}");
            serde_json::json!({
                "claim_id": id,
                "claim": format!("claim {id}"),
                "execution_records": exec(&id),
                "status": "verified"
            })
        })
        .collect();
    // Unique ids: the verified block owns F1..Fn.
    let gap_records: Vec<Value> = (0..gap)
        .map(|index| {
            let id = format!("G{index}");
            serde_json::json!({
                "claim_id": id,
                "claim": format!("claim {id}"),
                "execution_records": [],
                "status": "gap",
                "player_impact": "the player cannot proceed",
                "recommended_update": "implement it"
            })
        })
        .collect();
    serde_json::json!({
        "iteration": 1,
        "qa_status": "fail",
        "verified_records": verified_records,
        "gap_records": gap_records,
        "planner_handoff": {
            "preservation_constraints": [],
            "update_targets": [],
            "validation_requirements": []
        }
    })
    .to_string()
}

/// DR-39 ①: 8 verified / 22 gap — exactly the `smoke-t5` shape.
#[tokio::test]
async fn result_json_publishes_the_prd_coverage() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let script = vec![
        FakeStep::new(Role::Planner).writing(".hoh/plan.md", OK_PLAN),
        FakeStep::new(Role::Developer).writing("project.godot", "config_version=5\n"),
        FakeStep::new(Role::Tester)
            .writing(".hoh/evidence/coverage.json", "{}\n")
            .writing(".hoh/evidence.json", &coverage_evidence(8, 22)),
    ];
    let (result, _) = run_scenario(root, 1, script, Ablation::default(), FakeAdapter::new()).await;
    result.expect("the round must complete");

    let json: Value =
        serde_json::from_str(&read(&root.join("runs/run-1/iter-1/result.json"))).unwrap();
    let coverage = &json["prd_coverage"];
    assert_eq!(
        coverage["verified"], json!(8),
        "prd_coverage must be derived from E_t: {coverage}"
    );
    assert_eq!(coverage["gap"], json!(22), "{coverage}");
    assert_eq!(
        coverage["verified_ids"].as_array().map(Vec::len),
        Some(8),
        "the verified ids must be listed: {coverage}"
    );
    assert_eq!(
        coverage["gap_ids"].as_array().map(Vec::len),
        Some(22),
        "the gap ids must be listed: {coverage}"
    );
    // DR-39: the exit-code semantics do not change.
    assert_eq!(json["ok"], Value::Bool(true));
}

/// The derived total: the PRD has 17 functional requirements, so any `F<n>` id
/// pins the denominator to 17 instead of "however many claims the Tester wrote".
#[test]
fn the_prd_total_is_seventeen_when_functional_ids_are_present() {
    let coverage = PrdCoverage {
        verified: 8,
        gap: 22,
        verified_ids: (1..=8).map(|index| format!("F{index}")).collect(),
        gap_ids: (9..=17).map(|index| format!("F{index}")).collect(),
    };
    assert_eq!(coverage.total(), 17);
    assert!(coverage.total_is_known());

    let ad_hoc = PrdCoverage {
        verified: 1,
        gap: 2,
        verified_ids: vec!["alpha".to_string()],
        gap_ids: vec!["beta".to_string(), "gamma".to_string()],
    };
    assert_eq!(ad_hoc.total(), 3, "verified + gap when nothing maps to F1..F17");
    assert!(!ad_hoc.total_is_known());
}

/// DR-39 ③: `hoh run` must end with one unmistakable line.
#[test]
fn the_run_summary_line_states_the_prd_coverage() {
    let coverage = PrdCoverage {
        verified: 0,
        gap: 17,
        verified_ids: Vec::new(),
        gap_ids: (1..=17).map(|index| format!("F{index}")).collect(),
    };
    let line = hof_rs::cli_impl::format_prd_coverage_line(&coverage);
    assert!(
        line.contains("prd coverage: 0/17 verified"),
        "the end-of-run summary must be literal: {line}"
    );
    assert!(
        line.contains("harness") && line.contains("gate"),
        "the summary must keep `gate ok` and `PRD coverage` apart: {line}"
    );

    let ad_hoc = PrdCoverage {
        verified: 2,
        gap: 1,
        verified_ids: vec!["a".to_string()],
        gap_ids: vec!["b".to_string(), "c".to_string()],
    };
    let line = hof_rs::cli_impl::format_prd_coverage_line(&ad_hoc);
    assert!(
        line.contains("prd coverage: 2/3 verified") && line.contains("derived"),
        "an unknown denominator must be labelled: {line}"
    );
}
