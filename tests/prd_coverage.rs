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
        coverage["verified"],
        json!(8),
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
        ..Default::default()
    };
    assert_eq!(coverage.total(), 17);
    assert!(coverage.total_is_known());

    let ad_hoc = PrdCoverage {
        verified: 1,
        gap: 2,
        verified_ids: vec!["alpha".to_string()],
        gap_ids: vec!["beta".to_string(), "gamma".to_string()],
        ..Default::default()
    };
    assert_eq!(
        ad_hoc.total(),
        3,
        "verified + gap when nothing maps to F1..F17"
    );
    assert!(!ad_hoc.total_is_known());
}

/// DR-39 ③: `hoh run` must end with one unmistakable line.
///
/// Round-5 repair (defect RA-5): the derived form must say what its denominator
/// **is**.  Round 4 printed `prd coverage: 6/8` and the acceptance could only
/// establish what the 8 meant by reading the harness source.
///
/// Round-1 PRD-coverage batch: the line's **headline** is now the frozen PRD
/// surface figure, whose denominator is a compile-time constant, and the
/// Tester-derived figure travels on the same line labelled as what it is.  Both
/// properties the round-5 test pinned are still pinned, plus the one this batch
/// exists for: the headline denominator is the registry's count and does not
/// move when the Tester writes different claims.
#[test]
fn the_run_summary_line_states_the_prd_coverage() {
    let coverage = PrdCoverage {
        verified: 0,
        gap: 17,
        verified_ids: Vec::new(),
        gap_ids: (1..=17).map(|index| format!("F{index}")).collect(),
        ..Default::default()
    };
    let line = hof_rs::cli_impl::format_prd_coverage_line(&coverage);
    assert!(
        line.contains("frozen PRD surfaces"),
        "the end-of-run summary must name its denominator: {line}"
    );
    assert!(
        line.contains("F1..F17 claim count is 0/17"),
        "a known denominator is the PRD's own count and must say so: {line}"
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
        ..Default::default()
    };
    let line = hof_rs::cli_impl::format_prd_coverage_line(&ad_hoc);
    assert!(
        line.contains("prd coverage: 0/0"),
        "a run with no battery still states the surface figure it has: {line}"
    );
    for needle in [
        "OWN claim count",
        "NOT the PRD",
        "not comparable",
        "2 verified",
        "1 gap",
    ] {
        assert!(
            line.contains(needle),
            "an unknown denominator must be labelled with `{needle}`: {line}"
        );
    }
}

/// The defect this batch exists for: **the Tester cannot move the denominator.**
///
/// Round 4's `6/8` was `verified + gap` over whatever the Tester wrote, so round
/// 3's `7/8` and round 4's `6/8` were not comparable
/// (`.spec/bevy/ACCEPTANCE-ROUNDS.md` RA-5, "self-referential and not
/// comparable between rounds").  Two Tester bundles with different shapes must
/// produce the same frozen-registry denominator — otherwise nothing has been
/// repaired — and the harness's own battery must be what decides the items.
#[test]
fn the_surface_denominator_does_not_move_with_the_testers_claims() {
    use hof_rs::adapter::bevy::prd_surfaces::{decide, EXPECTED_IDS, PRD_SURFACES};
    use hof_rs::model::{EvidenceBundle, PrdCoverage, SurfaceStatus};

    // Two testers, two very different claim lists — round 3's shape and round
    // 4's shape, reduced to what the derivation sees.  Built as JSON so the
    // fixture is exactly the shape `hoh` reads, not a struct the test keeps in
    // step by hand.
    let bundle = |verified: &[&str], gaps: &[&str]| -> EvidenceBundle {
        let record = |id: &str, status: &str| {
            let mut value = serde_json::json!({
                "claim_id": id,
                "claim": format!("claim {id}"),
                "execution_records": [],
                "status": status,
            });
            if status == "gap" {
                value["player_impact"] = json!("the player cannot proceed");
                value["recommended_update"] = json!("implement it");
            }
            value
        };
        serde_json::from_value(json!({
            "iteration": 1,
            "qa_status": "fail",
            "verified_records": verified.iter().map(|id| record(id, "verified")).collect::<Vec<_>>(),
            "gap_records": gaps.iter().map(|id| record(id, "gap")).collect::<Vec<_>>(),
            "planner_handoff": {
                "preservation_constraints": [],
                "update_targets": [],
                "validation_requirements": [],
            },
        }))
        .expect("the fixture is a schema-valid evidence bundle")
    };
    let round_three_bundle = bundle(
        &["C1-launch", "P1-move-right", "P2-coins"],
        &["G-transport", "P5-grounded"],
    );
    let round_four_bundle = bundle(
        &["P1", "P2", "P3", "P4", "P5", "S1"],
        &["P3-goal-x", "S1-deterministic-step"],
    );
    let round_three = PrdCoverage::from_bundle(&round_three_bundle);
    let round_four = PrdCoverage::from_bundle(&round_four_bundle);
    assert_ne!(
        (round_three.verified, round_three.gap),
        (round_four.verified, round_four.gap),
        "the two rounds really do differ in what the Tester wrote"
    );

    // The battery's own evidence decides the surfaces, so a full pass gives the
    // same figure for both rounds.
    let mut steps: Vec<(String, bool)> = vec![
        ("editor_errors_baseline".to_string(), true),
        ("play_scene_ready".to_string(), true),
    ];
    for (step, _, _) in hof_rs::adapter::bevy::round::E3_STEPS {
        steps.push(((*step).to_string(), true));
    }
    let coverage = decide(&steps);
    for prd in [&round_three, &round_four] {
        let with_surfaces = prd.clone().with_surfaces(coverage.clone());
        assert_eq!(
            with_surfaces.surfaces.total,
            PRD_SURFACES.len(),
            "the denominator is the registry"
        );
        assert_eq!(
            with_surfaces.surfaces.items.len(),
            EXPECTED_IDS.len(),
            "one verdict per registry item"
        );
    }
    // And the two Tester figures are still published, separately.
    assert_eq!(round_three.total(), 5, "round 3's own claim count");
    assert_eq!(round_four.total(), 8, "round 4's own claim count");

    let item = |id: &str| {
        coverage
            .items
            .iter()
            .find(|item| item.id == id)
            .unwrap_or_else(|| panic!("`{id}` is in the registry"))
    };
    assert_eq!(item("P3").status, SurfaceStatus::Verified);
    assert!(
        item("P3").evidence.contains("e3_win_flag"),
        "{}",
        item("P3").evidence
    );
    assert!(
        item("C5").status == SurfaceStatus::Unobservable
            && item("C5")
                .reason
                .as_deref()
                .unwrap_or("")
                .contains("enumerate"),
        "a surface the harness cannot decide is a named gap: {:?}",
        item("C5")
    );
}

/// The registry is anchored to the **frozen** document: every id names a literal
/// that is in `.spec/bevy/PRD.md`, and the id set is exactly the frozen one.
///
/// This is what makes "stable" mean something.  A surface id whose anchor left
/// the document is a red test, not a quietly smaller denominator; and because
/// the PRD may only be extended below its seal, an anchor that is present today
/// cannot be removed by a legal edit.
#[test]
fn the_prd_surface_registry_is_anchored_to_the_frozen_prd() {
    use hof_rs::adapter::bevy::prd_surfaces::{EXPECTED_IDS, PRD_SURFACES};

    let path = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join(".spec/bevy/PRD.md");
    let text = std::fs::read_to_string(&path)
        .unwrap_or_else(|error| panic!("the frozen PRD must be readable: {error}"));
    for surface in PRD_SURFACES {
        assert!(
            text.contains(surface.anchor),
            "PRD surface `{}` is anchored to `{}`, which is not in {}",
            surface.id,
            surface.anchor,
            path.display()
        );
    }
    assert_eq!(
        PRD_SURFACES
            .iter()
            .map(|surface| surface.id)
            .collect::<Vec<_>>(),
        EXPECTED_IDS.to_vec(),
        "the denominator is spelled out in EXPECTED_IDS and must not drift"
    );
    let mut ids: Vec<&str> = EXPECTED_IDS.to_vec();
    ids.sort_unstable();
    let mut unique = ids.clone();
    unique.dedup();
    assert_eq!(ids, unique, "registry ids are unique");
}
