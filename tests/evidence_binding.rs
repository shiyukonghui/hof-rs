//! R4/R7 — evidence binding: verified/gap partition, candidate stamping, and
//! the counter-examples that must never pass.
//!
//! The run-loop level counter-examples (`rejects_contaminated_candidate`,
//! `rejects_workspace_drift`, `rejects_direct_real_workspace_write`) live in
//! this file as well; `bind` is the pure half of the same contract.

mod common;

use std::path::Path;

use common::*;
use hof_rs::errors::{as_hof_error, HofError};
use hof_rs::model::{Ablation, ContractViolation, EvidenceBundle, IssueCode, Role};
use hof_rs::runtime::evidence::bind;
use hof_rs::runtime::policy::{hash_tree, tree_manifest, HashExcludes};
use hof_rs::runtime::schema::gate_evidence;

fn load_fixture(name: &str) -> EvidenceBundle {
    let raw = std::fs::read_to_string(format!("tests/fixtures/{name}")).expect("fixture");
    serde_json::from_str(&raw).expect("fixture must deserialize")
}

fn codes(issues: &[hof_rs::model::SchemaIssue]) -> Vec<IssueCode> {
    issues.iter().map(|issue| issue.code).collect()
}

fn fixture_view(temp: &Path, with_evidence_file: bool) -> std::path::PathBuf {
    let view = temp.join("candidate");
    std::fs::create_dir_all(view.join(".hoh/evidence")).unwrap();
    if with_evidence_file {
        std::fs::write(view.join(".hoh/evidence/move.json"), "{\"ok\":true}").unwrap();
    }
    view
}

#[test]
fn bind_stamps_candidate_and_preserves_text() {
    let temp = tempfile::tempdir().unwrap();
    let view = fixture_view(temp.path(), true);
    let mut bundle = load_fixture("evidence_ok.json");
    let before: Vec<String> = bundle
        .verified_records
        .iter()
        .chain(bundle.gap_records.iter())
        .map(|record| record.claim.clone())
        .collect();

    bind(&mut bundle, "cand-1", &view).expect("binding must succeed");

    for record in bundle
        .verified_records
        .iter()
        .chain(bundle.gap_records.iter())
    {
        for exec in &record.execution_records {
            assert_eq!(exec.candidate_id, "cand-1");
        }
    }
    let after: Vec<String> = bundle
        .verified_records
        .iter()
        .chain(bundle.gap_records.iter())
        .map(|record| record.claim.clone())
        .collect();
    // The runtime must never rewrite the Tester's assessment.
    assert_eq!(before, after);
    assert!(bundle
        .gap_records
        .iter()
        .all(|record| record.player_impact.is_some() && record.recommended_update.is_some()));
}

#[test]
fn verified_gap_partition() {
    // {verified} ∩ {gap} == ∅ is a hard error.
    let duplicate = load_fixture("evidence_dup_claim.json");
    let issues = hof_rs::model::validate_evidence(&duplicate, "cand").unwrap_err();
    assert!(codes(&issues).contains(&IssueCode::DuplicateClaimId));

    // A gap claim without guidance is a hard error.
    let mut missing_guidance = load_fixture("evidence_ok.json");
    missing_guidance.gap_records[0].recommended_update = None;
    let issues = hof_rs::model::validate_evidence(&missing_guidance, "cand").unwrap_err();
    assert!(codes(&issues).contains(&IssueCode::GapMissingGuidance));

    // A verified claim without execution records is a hard error.
    let mut unsupported = load_fixture("evidence_ok.json");
    unsupported.verified_records[0].execution_records.clear();
    let issues = hof_rs::model::validate_evidence(&unsupported, "cand").unwrap_err();
    assert!(codes(&issues).contains(&IssueCode::UnsupportedVerified));

    // The well-formed fixture passes both the pure validation and binding.
    let temp = tempfile::tempdir().unwrap();
    let view = fixture_view(temp.path(), true);
    let mut ok = load_fixture("evidence_ok.json");
    assert!(hof_rs::model::validate_evidence(&ok, "cand").is_ok());
    assert!(bind(&mut ok, "cand", &view).is_ok());
}

#[test]
fn rejects_dangling_evidence() {
    let temp = tempfile::tempdir().unwrap();
    // The referenced screenshot is deliberately absent from the candidate view.
    let view = fixture_view(temp.path(), false);
    let mut bundle = load_fixture("evidence_dangling.json");

    let issues = bind(&mut bundle, "cand", &view).unwrap_err();
    assert!(codes(&issues).contains(&IssueCode::DanglingEvidence));
}

#[test]
fn rejects_candidate_mismatch() {
    let temp = tempfile::tempdir().unwrap();
    let view = fixture_view(temp.path(), true);
    let mut bundle = load_fixture("evidence_ok.json");
    bundle.verified_records[0].execution_records[0].candidate_id = "other-candidate".to_string();

    let issues = bind(&mut bundle, "cand", &view).unwrap_err();
    assert!(codes(&issues).contains(&IssueCode::CandidateMismatch));
}

#[test]
fn rejects_absolute_path_evidence_outside_the_view() {
    // §4.6: an absolute path is never resolved against the view root; the
    // record is rejected unless it is a relative path inside the candidate.
    let temp = tempfile::tempdir().unwrap();
    let view = fixture_view(temp.path(), true);
    let mut bundle = load_fixture("evidence_ok.json");
    bundle.verified_records[0].execution_records[0].path =
        Some("C:/Windows/not-in-the-view.png".to_string());

    let issues = bind(&mut bundle, "cand", &view).unwrap_err();
    assert!(codes(&issues).contains(&IssueCode::DanglingEvidence));
}

/// DR-10 (blocker A1): a `..` component is rejected even when the target file
/// really exists, because it escapes the candidate view root.
#[test]
fn rejects_parent_dir_traversal() {
    let temp = tempfile::tempdir().unwrap();
    let view = fixture_view(temp.path(), true);
    // The file exists, but outside the view root: existence alone must not pass.
    std::fs::write(temp.path().join("outside_secret.txt"), "secret\n").unwrap();

    for escaped in ["../outside_secret.txt", ".hoh/../../outside_secret.txt"] {
        let mut bundle = load_fixture("evidence_ok.json");
        bundle.verified_records[0].execution_records[0].path = Some(escaped.to_string());
        let issues = bind(&mut bundle, "cand", &view)
            .expect_err("a parent-dir traversal must never be accepted");
        assert!(
            codes(&issues).contains(&IssueCode::DanglingEvidence),
            "expected DanglingEvidence for `{escaped}`, got {:?}",
            codes(&issues)
        );
    }

    // A symlink pointing outside the view root is rejected by the
    // canonicalize prefix assertion (skipped when the OS refuses to create it).
    #[cfg(windows)]
    let link = std::os::windows::fs::symlink_file(
        temp.path().join("outside_secret.txt"),
        view.join("link.txt"),
    );
    #[cfg(not(windows))]
    let link = std::os::unix::fs::symlink(
        temp.path().join("outside_secret.txt"),
        view.join("link.txt"),
    );
    if link.is_ok() {
        let mut bundle = load_fixture("evidence_ok.json");
        bundle.verified_records[0].execution_records[0].path = Some("link.txt".to_string());
        let issues = bind(&mut bundle, "cand", &view).expect_err("a symlink escape must be denied");
        assert!(codes(&issues).contains(&IssueCode::DanglingEvidence));
    }
}

#[tokio::test]
async fn gate_evidence_accepts_a_bound_candidate() {
    let temp = tempfile::tempdir().unwrap();
    let view = fixture_view(temp.path(), true);
    let traj = temp.path().join("traj");
    let harness = FakeHarness::new(vec![
        FakeStep::new(Role::Tester).writing(".hoh/evidence.json", &ok_evidence(1, ""))
    ]);
    let model = serde_json::json!({"model_name": "openai/qwen/qwen3.8-27b"});
    let base = role_invocation(
        &view,
        Role::Tester,
        1,
        &traj.join("tester.attempt1.json"),
        model,
    );

    let bundle = gate_evidence(&harness, &base, "cand-1", 2)
        .await
        .expect("valid evidence must pass the gate");
    assert_eq!(bundle.verified_records.len(), 1);
    assert_eq!(bundle.gap_records.len(), 1);
    assert_eq!(
        bundle.verified_records[0].execution_records[0].candidate_id,
        "cand-1"
    );
}

// ---------------------------------------------------------------------------
// R4 at run-loop level: the QA candidate is frozen, and the real artifact is
// checked around the QA stage as well (the copy alone cannot stop an absolute
// path write).
// ---------------------------------------------------------------------------

fn result_json(root: &Path) -> serde_json::Value {
    let path = root.join("runs/run-1/iter-1/result.json");
    serde_json::from_str(&std::fs::read_to_string(path).expect("result.json")).expect("json")
}

fn assert_contract(error: &anyhow::Error, expected: ContractViolation) {
    let hof = as_hof_error(error).expect("typed error");
    match hof {
        HofError::Contract { violation, .. } => assert_eq!(*violation, expected),
        other => panic!("unexpected error: {other:?}"),
    }
}

/// R4 at run-loop level: **the write is rejected, and the round is still judged.**
///
/// D295(b) settled what "rejected" means.  DR-86 ④ briefly made this scenario end
/// `ok=true` because the runtime restored the view and reported it; that let a
/// compliance criterion pass on a *repaired* violation, and `REQUIREMENTS.md`
/// R4/R13 say a QA write into the frozen snapshot is a rejection, so the round
/// **fails** again (`reason=contract_violation`).  What DR-86 ④ keeps is the end
/// of the real dead end: the write is still detected
/// (`qa_contaminated_candidate_restored` names it, with the difference list), the
/// frozen bytes come back from the `A_t` snapshot, the bytes the role wrote are
/// preserved as evidence instead of being deleted, and the gate verdict the
/// battery already produced travels with the failure rather than being replaced by
/// a `not_applicable` stub.
#[tokio::test]
async fn rejects_contaminated_candidate() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let script = vec![
        FakeStep::new(Role::Planner).writing(".hoh/plan.md", OK_PLAN),
        FakeStep::new(Role::Developer).writing("project.godot", "config_version=5\n"),
        FakeStep::new(Role::Tester)
            .writing(".hoh/evidence/move.json", "{}\n")
            .writing("scripts/cheat.gd", "extends Node\n")
            .writing(".hoh/evidence.json", &ok_evidence(1, "")),
    ];
    let (result, _) = run_scenario(root, 1, script, Ablation::default(), FakeAdapter::new()).await;
    let error = result.expect_err("R4/R13: a Tester write into the frozen view must be rejected");
    assert_contract(&error, ContractViolation::QaContaminatedCandidate);

    let result_json = result_json(root);
    assert_eq!(result_json["ok"], serde_json::json!(false));
    assert_eq!(result_json["failed_role"], serde_json::json!("tester"));
    assert_eq!(
        result_json["reason"],
        serde_json::json!("contract_violation")
    );
    let warnings = result_json["warnings"].as_array().unwrap().clone();
    assert!(
        warnings
            .iter()
            .any(|warning| warning == "qa_contaminated_candidate_restored"),
        "the write must still be reported as a contamination: {warnings:?}"
    );
    // DR-2: contaminating the copy is reported with the file that did it.
    let log = std::fs::read_to_string(root.join("runs/run-1/warnings.log")).unwrap_or_default();
    assert!(
        log.contains("added=[\"scripts/cheat.gd\"]"),
        "the difference list must name the file that did it: {log}"
    );
    // The frozen view is byte-frozen again, and the bytes the Tester wrote are
    // preserved — not deleted.
    assert!(
        !root
            .join("runs/run-1/iter-1/candidate/scripts/cheat.gd")
            .exists(),
        "the frozen candidate must not keep the write"
    );
    assert_eq!(
        std::fs::read_to_string(
            root.join("runs/run-1/iter-1/tester-writes/candidate/scripts/cheat.gd")
        )
        .unwrap(),
        "extends Node\n"
    );
    // The verdict the battery produced is not thrown away.
    assert!(
        result_json["artifact_gate"]["reasons"]
            .as_array()
            .map(|reasons| reasons
                .iter()
                .filter_map(|reason| reason.as_str())
                .all(|reason| !reason.contains("no artifact gate was produced")))
            .unwrap_or(true),
        "the verdict must be the one the battery produced, not the failure stub: {result_json}"
    );
    assert!(
        !result_json["battery_passes"]
            .as_array()
            .map(|passes| passes.is_empty())
            .unwrap_or(true),
        "the battery that produced the verdict must be in the record: {result_json}"
    );
}

/// DR-1: the deterministic stage runs on the real workspace *before* the
/// freeze, so anything it changes is part of `A_t` — and must not be reported
/// as pre-QA drift.
#[tokio::test]
async fn deterministic_stage_changes_are_part_of_candidate_identity() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let workspace = root.join("workspace");
    let adapter = FakeAdapter::new().with_drift(
        workspace.clone(),
        "scripts/deep/editor_side_effect.gd",
        "# produced by the deterministic build/exec stage\n",
    );
    let (result, _) = run_scenario(root, 1, happy_script(), Ablation::default(), adapter).await;
    let summary =
        result.expect("DR-1: a deterministic-stage change is legitimate, not a violation");

    let excludes = HashExcludes::new(["cache".to_string()]).merged();
    let frozen = hash_tree(&workspace, &excludes).unwrap();
    assert_eq!(
        summary.final_version_id.as_deref(),
        Some(frozen.as_str()),
        "A_t must be the post-deterministic hash"
    );

    let result_json = result_json(root);
    assert_eq!(result_json["ok"], serde_json::json!(true));
    assert_eq!(result_json["candidate_id"], serde_json::json!(frozen));
    let warnings = result_json["warnings"].as_array().unwrap().clone();
    assert!(
        !warnings
            .iter()
            .any(|warning| warning == "workspace_drift_before_qa"),
        "the deterministic change must not be reported as drift: {warnings:?}"
    );

    // The change is inside the artifact identity and inside the frozen copy.
    let manifest = tree_manifest(&workspace, &excludes).unwrap();
    assert!(manifest.contains_key("scripts/deep/editor_side_effect.gd"));
    assert!(root
        .join("runs/run-1/iter-1/candidate/scripts/deep/editor_side_effect.gd")
        .is_file());
}

/// The pre-QA safety net still exists: a change that happens *after* the freeze
/// is a hard failure (DR-1 keeps the assertion).
#[tokio::test]
async fn rejects_workspace_drift() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    // `evidence_playbook` is read by the runtime after A_t was frozen, which is
    // the only deterministic post-freeze window the loop exposes.
    let adapter = FakeAdapter::new().with_post_freeze_drift(
        root.join("workspace"),
        "drifted.gd",
        "# the editor project moved under the QA candidate\n",
    );
    let (result, _) = run_scenario(root, 1, happy_script(), Ablation::default(), adapter).await;
    let error = result.expect_err("QA must be rejected when the artifact drifted");
    assert_contract(&error, ContractViolation::WorkspaceDriftBeforeQa);

    let result_json = result_json(root);
    assert_eq!(result_json["failed_role"], serde_json::json!("tester"));
    // DR-2: the violation names the file that changed.
    assert_eq!(
        result_json["evidence_diff"]["added"],
        serde_json::json!(["drifted.gd"])
    );
}

/// DR-2 / FIX-4: a contract violation must carry a concrete difference list, not
/// just "the hashes differ".
///
/// The write is moved to the **Planner** on purpose.  A Tester write to a frozen
/// view is a violation too (DR-86 ④ detects and restores it, D295(b) keeps the
/// round rejected), but the Planner's write is the one the guard does not repair,
/// so it is the case that proves every violation still publishes the file-level
/// diff it always did.
#[tokio::test]
async fn contract_violation_reports_a_concrete_diff() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let deep = root.join("workspace/scripts/deep/nested/player.gd");
    write(&deep, "extends Node\n# baseline\n");

    let script = vec![
        FakeStep::new(Role::Planner)
            .writing(".hoh/plan.md", OK_PLAN)
            // A single deep file is rewritten through an absolute path: the
            // view isolation cannot stop this, the hash assertion must.
            .outside(deep.clone(), "extends Node\n# hacked by the planner\n"),
        FakeStep::new(Role::Developer).writing("project.godot", "config_version=5\n"),
        FakeStep::new(Role::Tester)
            .writing(".hoh/evidence/move.json", "{}\n")
            .writing(".hoh/evidence.json", &ok_evidence(1, "")),
    ];
    let (result, _) = run_scenario(root, 1, script, Ablation::default(), FakeAdapter::new()).await;
    let error = result.expect_err("a read-only role must not rewrite the real artifact");
    assert_contract(&error, ContractViolation::ReadOnlyRoleWroteArtifact);

    let result_json = result_json(root);
    assert_eq!(
        result_json["reason"],
        serde_json::json!("contract_violation")
    );
    assert_eq!(
        result_json["evidence_diff"]["modified"],
        serde_json::json!(["scripts/deep/nested/player.gd"]),
        "the diff must name exactly the deep file that was rewritten: {result_json}"
    );
    assert_eq!(result_json["evidence_diff"]["added"], serde_json::json!([]));
    assert_eq!(
        result_json["evidence_diff"]["removed"],
        serde_json::json!([])
    );
}

/// R4: the real artifact is checked around QA too (the copy alone cannot stop an
/// absolute-path write).
///
/// D295(b): the write is still detected, the artifact is still protected (the
/// workspace is put back to the frozen bytes and the file the Tester wrote is
/// preserved under `tester-writes/workspace/`), and the round now **rejects** —
/// the same R4/R13 semantics as the candidate view.  The verdict the battery
/// produced still travels with the failure.
#[tokio::test]
async fn rejects_direct_real_workspace_write() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let script = vec![
        FakeStep::new(Role::Planner).writing(".hoh/plan.md", OK_PLAN),
        FakeStep::new(Role::Developer).writing("project.godot", "config_version=5\n"),
        FakeStep::new(Role::Tester)
            .writing(".hoh/evidence/move.json", "{}\n")
            .writing(".hoh/evidence.json", &ok_evidence(1, ""))
            .outside(
                root.join("workspace/scripts/hacked_by_tester.gd"),
                "extends Node\n",
            ),
    ];
    let (result, _) = run_scenario(root, 1, script, Ablation::default(), FakeAdapter::new()).await;
    let error = result.expect_err("R4: a Tester write into the real artifact must be rejected");
    assert_contract(&error, ContractViolation::ReadOnlyRoleWroteArtifact);

    let result_json = result_json(root);
    assert_eq!(result_json["ok"], serde_json::json!(false));
    assert_eq!(result_json["failed_role"], serde_json::json!("tester"));
    assert_eq!(
        result_json["reason"],
        serde_json::json!("contract_violation")
    );
    let warnings = result_json["warnings"].as_array().unwrap().clone();
    assert!(
        warnings
            .iter()
            .any(|warning| warning == "qa_contaminated_workspace_restored"),
        "the write must still be reported as a contamination: {warnings:?}"
    );
    assert!(
        !root.join("workspace/scripts/hacked_by_tester.gd").exists(),
        "the real artifact must not keep the write"
    );
    assert_eq!(
        std::fs::read_to_string(
            root.join("runs/run-1/iter-1/tester-writes/workspace/scripts/hacked_by_tester.gd")
        )
        .unwrap(),
        "extends Node\n",
        "the bytes the role wrote are preserved as evidence"
    );
    // The verdict the battery produced is not thrown away.
    assert!(
        result_json["artifact_gate"]["reasons"]
            .as_array()
            .map(|reasons| reasons
                .iter()
                .filter_map(|reason| reason.as_str())
                .all(|reason| !reason.contains("no artifact gate was produced")))
            .unwrap_or(true),
        "the verdict must be the one the battery produced, not the failure stub: {result_json}"
    );
    assert!(
        !result_json["battery_passes"]
            .as_array()
            .map(|passes| passes.is_empty())
            .unwrap_or(true),
        "the battery that produced the verdict must be in the record: {result_json}"
    );
    assert!(
        warnings
            .iter()
            .any(|warning| warning == "read_only_role_wrote_artifact"),
        "the violation code must be recorded alongside the restore token: {warnings:?}"
    );
}

// ---------------------------------------------------------------------------
// D295(b) / DR-88 ④: the two readings E5 must never confuse
// ---------------------------------------------------------------------------

/// The tokens E5 requires to be **absent** (see `godot_smoke`'s
/// `e5_qa_did_not_modify_the_artifact`), read with the same rule the criterion
/// uses.  It is here so the distinction the criterion rests on is pinned by a test
/// that runs offline, in the ordinary suite, instead of only by an `#[ignore]`d
/// reading of a round that needs an engine.
///
/// Two prefixes, because there are two ways a round can record a role write into
/// the frozen view: `qa_contaminated_*` for a write the artifact hash can see
/// (restored from the snapshot), and `qa_wrote_cache_*` for a write through the
/// adapter's configured cache excludes, which the hash deliberately does not
/// cover and which the separate watch observes.
fn qa_write_warnings(result: &serde_json::Value) -> Vec<String> {
    result["warnings"]
        .as_array()
        .map(|items| {
            items
                .iter()
                .filter_map(|item| item.as_str())
                .filter(|warning| {
                    warning.starts_with("qa_contaminated_")
                        || warning.starts_with("qa_wrote_cache_")
                })
                .map(str::to_string)
                .collect()
        })
        .unwrap_or_default()
}

/// A clean round and a contaminated-and-repaired round must not read the same.
///
/// Both end with the candidate view byte-identical to `A_t` — that is exactly why
/// the hash alone cannot separate them — so the reading has two *independent*
/// discriminators, and this test pins both transitions:
///
/// * a round where no role wrote: `ok=true`, no `qa_contaminated_*` warning;
/// * a round where the Tester wrote and the runtime restored: `ok=false` (the
///   violation is rejected, D295(b)) and the warning is present.
///
/// A future edit that made a contamination end `ok=true` again, or that dropped
/// the warning from the record, reddens this test whichever side it breaks.
#[tokio::test]
async fn a_repaired_contamination_can_never_read_as_a_clean_round() {
    // (a) the clean round: the reading sees nothing to object to.
    let clean_temp = tempfile::tempdir().unwrap();
    let (clean_result, _) = run_scenario(
        clean_temp.path(),
        1,
        happy_script(),
        Ablation::default(),
        FakeAdapter::new(),
    )
    .await;
    clean_result.expect("a round with no QA write completes");
    let clean = result_json(clean_temp.path());
    assert_eq!(clean["ok"], serde_json::json!(true));
    assert!(
        qa_write_warnings(&clean).is_empty(),
        "a clean round must carry no write warning: {:?}",
        qa_write_warnings(&clean)
    );

    // (b) the contaminated round: rejected, and the warning names the write.
    let dirty_temp = tempfile::tempdir().unwrap();
    let script = vec![
        FakeStep::new(Role::Planner).writing(".hoh/plan.md", OK_PLAN),
        FakeStep::new(Role::Developer).writing("project.godot", "config_version=5\n"),
        FakeStep::new(Role::Tester)
            .writing(".hoh/evidence/move.json", "{}\n")
            .writing("scripts/cheat.gd", "extends Node\n")
            .writing(".hoh/evidence.json", &ok_evidence(1, "")),
    ];
    let (dirty_result, _) = run_scenario(
        dirty_temp.path(),
        1,
        script,
        Ablation::default(),
        FakeAdapter::new(),
    )
    .await;
    dirty_result.expect_err("the contaminated round must be rejected");
    let dirty = result_json(dirty_temp.path());
    assert_eq!(dirty["ok"], serde_json::json!(false));
    assert!(
        qa_write_warnings(&dirty).contains(&"qa_contaminated_candidate_restored".to_string()),
        "the repaired contamination must be visible in the record: {:?}",
        qa_write_warnings(&dirty)
    );

    // The two results differ in the criterion's own reading, even though both
    // trees are byte-identical to the frozen candidate.
    assert_ne!(
        (clean["ok"].clone(), qa_write_warnings(&clean)),
        (dirty["ok"].clone(), qa_write_warnings(&dirty))
    );
}

/// DR-88 ④: a write the artifact hash **cannot** see must not be readable as a
/// clean round either.
///
/// The adapter's configured cache excludes (`.godot`, `.import` here, and in
/// `config/hoh.yaml`) are outside `hash_tree` by design: R10 requires the
/// `version_id` to stay stable, so they must not enter the identity.  That made
/// them a blind spot — the DR-87 acceptance built a round that ended `ok=true`
/// with live Tester bytes in `.godot/` and E5 could not tell.  The runtime now
/// watches those directories separately; the round is rejected exactly as for a
/// hashed write, the criterion's reading requires the token to be absent, and
/// the bytes are preserved as evidence.
#[tokio::test]
async fn a_write_through_the_configured_cache_excludes_can_never_read_as_a_clean_round() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    let adapter = FakeAdapter {
        excludes: vec![".godot".to_string(), ".import".to_string()],
        ..FakeAdapter::new()
    };
    let script = vec![
        FakeStep::new(Role::Planner).writing(".hoh/plan.md", OK_PLAN),
        FakeStep::new(Role::Developer).writing("project.godot", "config_version=5\n"),
        FakeStep::new(Role::Tester)
            .writing(".godot/cheat.bin", "live tester bytes\n")
            .writing(".hoh/evidence/move.json", "{}\n")
            .writing(".hoh/evidence.json", &ok_evidence(1, "")),
    ];
    let (result, _) = run_scenario(root, 1, script, Ablation::default(), adapter).await;
    let error = result.expect_err("a write into the frozen view must be rejected");
    assert_contract(&error, ContractViolation::QaContaminatedCandidate);

    let json = result_json(root);
    assert_eq!(json["ok"], serde_json::json!(false));
    assert_eq!(json["failed_role"], serde_json::json!("tester"));
    assert_eq!(json["reason"], serde_json::json!("contract_violation"));
    assert!(
        qa_write_warnings(&json).contains(&"qa_wrote_cache_candidate".to_string()),
        "the excluded-path write must be named: {:?}",
        qa_write_warnings(&json)
    );
    // The evidence: the bytes are preserved, and the view is left as it was
    // found, even though there is no frozen snapshot byte for an excluded path.
    assert_eq!(
        std::fs::read_to_string(
            root.join("runs/run-1/iter-1/tester-writes/cache-candidate/.godot/cheat.bin")
        )
        .unwrap(),
        "live tester bytes\n"
    );
    assert!(
        !root
            .join("runs/run-1/iter-1/candidate/.godot/cheat.bin")
            .exists(),
        "the write must not survive in the frozen view"
    );
    // The verdict the battery produced is still not thrown away.
    assert!(
        json["artifact_gate"]["reasons"]
            .as_array()
            .map(|reasons| reasons
                .iter()
                .filter_map(|reason| reason.as_str())
                .all(|reason| !reason.contains("no artifact gate was produced")))
            .unwrap_or(true),
        "the verdict must be the one the battery produced: {json}"
    );
}
