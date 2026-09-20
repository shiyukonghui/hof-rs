//! Data model of the Harness-of-Harness runtime plus its pure invariants.
//!
//! Every public type and serde field name in this module is frozen by
//! `DESIGN-DETAIL.md` §2: the JSON written to disk has exactly these keys.

use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};

/// The three workflow roles.  Every invocation is a fresh harness call.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Role {
    Planner,
    Developer,
    Tester,
}

impl Role {
    pub fn as_str(self) -> &'static str {
        match self {
            Role::Planner => "planner",
            Role::Developer => "developer",
            Role::Tester => "tester",
        }
    }

    /// Canonical artifact path (relative to the role view root) that the role
    /// submits through `hoh submit`.  Developer has no submittable artifact.
    pub fn artifact_rel_path(self) -> &'static str {
        match self {
            Role::Planner => ".hoh/plan.md",
            Role::Tester => ".hoh/evidence.json",
            Role::Developer => "",
        }
    }

    pub fn parse(value: &str) -> Option<Role> {
        match value.trim().to_ascii_lowercase().as_str() {
            "planner" => Some(Role::Planner),
            "developer" => Some(Role::Developer),
            "tester" | "qa" => Some(Role::Tester),
            _ => None,
        }
    }
}

/// The public specification S, recorded by hash so a frozen S is auditable.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct Spec {
    pub path: PathBuf,
    pub sha256: String,
}

/// Ablation switches (R8).  Each one changes exactly one cross-iteration input.
#[derive(Clone, Copy, Debug, Serialize, Deserialize)]
pub struct Ablation {
    pub plan_update: bool,
    pub evidence_feedback: bool,
    pub warm_start: bool,
}

impl Default for Ablation {
    fn default() -> Self {
        Self {
            plan_update: true,
            evidence_feedback: true,
            warm_start: true,
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ExecKind {
    Screenshot,
    Replay,
    RuntimeTrace,
    Assert,
    Build,
    Log,
}

/// One public execution record referenced by a claim.  `path` is relative to
/// the candidate view root and uses POSIX separators.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ExecRecord {
    #[serde(rename = "type")]
    pub kind: ExecKind,
    pub path: Option<String>,
    pub observation: String,
    #[serde(default)]
    pub candidate_id: String,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ClaimStatus {
    Verified,
    Gap,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ClaimRecord {
    pub claim_id: String,
    pub claim: String,
    pub execution_records: Vec<ExecRecord>,
    pub status: ClaimStatus,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub player_impact: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub recommended_update: Option<String>,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum QaStatus {
    Pass,
    Partial,
    Fail,
}

/// Planner handoff carried inside `E_t` (paper Listing 1 field names).
#[derive(Clone, Debug, Serialize, Deserialize, Default)]
pub struct PlannerHandoff {
    pub preservation_constraints: Vec<String>,
    pub update_targets: Vec<String>,
    pub validation_requirements: Vec<String>,
}

/// `E_t`: the evidence bundle produced by the Tester.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct EvidenceBundle {
    pub iteration: u32,
    pub qa_status: QaStatus,
    pub verified_records: Vec<ClaimRecord>,
    pub gap_records: Vec<ClaimRecord>,
    pub planner_handoff: PlannerHandoff,
}

/// `D_t`: the development document produced by the Planner.
#[derive(Clone, Debug)]
pub struct DevelopmentDoc {
    pub iteration: u32,
    pub path: PathBuf,
    pub raw: String,
    pub priorities: Vec<String>,
    pub preservation_gate: Vec<String>,
    pub acceptance_gate: Vec<String>,
}

/// Per-call token usage (R12).  `usage_known == false` must never be reported
/// as zeroed tokens: the token fields stay `None`.
#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub struct Usage {
    pub role: String,
    pub iteration: u32,
    pub calls: u64,
    pub prompt_tokens: Option<u64>,
    pub completion_tokens: Option<u64>,
    pub total_tokens: Option<u64>,
    pub cache_hit_tokens: Option<u64>,
    pub cache_miss_tokens: Option<u64>,
    pub usage_known: bool,
}

/// `A_t`: the artifact state after the Developer stage.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ArtifactState {
    pub workspace: PathBuf,
    pub version_id: String,
    pub candidate_id: String,
    pub parent_version_id: Option<String>,
}

/// Contract violations detected by the runtime (never silently ignored).
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ContractViolation {
    /// Planner/Tester wrote to the real artifact.
    ReadOnlyRoleWroteArtifact,
    /// Tester wrote inside the frozen candidate copy.
    QaContaminatedCandidate,
    /// The real workspace no longer matches `A_t.candidate_id` before QA.
    WorkspaceDriftBeforeQa,
    /// Evidence claims a candidate identity that does not match.
    CandidateIdMismatch,
    /// Plan update is forbidden by the ablation switch.
    PlanUpdateForbidden,
    /// Warning only: the Developer produced no change.
    NoProgress,
}

impl ContractViolation {
    pub fn code(self) -> &'static str {
        match self {
            ContractViolation::ReadOnlyRoleWroteArtifact => "read_only_role_wrote_artifact",
            ContractViolation::QaContaminatedCandidate => "qa_contaminated_candidate",
            ContractViolation::WorkspaceDriftBeforeQa => "workspace_drift_before_qa",
            ContractViolation::CandidateIdMismatch => "candidate_id_mismatch",
            ContractViolation::PlanUpdateForbidden => "plan_update_forbidden",
            ContractViolation::NoProgress => "no_progress",
        }
    }
}

/// Machine-checkable schema problem.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct SchemaIssue {
    pub code: IssueCode,
    pub message: String,
}

impl SchemaIssue {
    pub fn new(code: IssueCode, message: impl Into<String>) -> Self {
        Self {
            code,
            message: message.into(),
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum IssueCode {
    Json,
    MissingField,
    MissingSection,
    EmptyGate,
    DuplicateClaimId,
    EmptyClaimList,
    UnsupportedVerified,
    GapMissingGuidance,
    DanglingEvidence,
    CandidateMismatch,
}

impl IssueCode {
    pub fn as_str(self) -> &'static str {
        match self {
            IssueCode::Json => "json",
            IssueCode::MissingField => "missing_field",
            IssueCode::MissingSection => "missing_section",
            IssueCode::EmptyGate => "empty_gate",
            IssueCode::DuplicateClaimId => "duplicate_claim_id",
            IssueCode::EmptyClaimList => "empty_claim_list",
            IssueCode::UnsupportedVerified => "unsupported_verified",
            IssueCode::GapMissingGuidance => "gap_missing_guidance",
            IssueCode::DanglingEvidence => "dangling_evidence",
            IssueCode::CandidateMismatch => "candidate_mismatch",
        }
    }
}

/// The empty evidence bundle used when `evidence_feedback` is ablated.
pub fn empty_evidence(iteration: u32) -> EvidenceBundle {
    EvidenceBundle {
        iteration,
        qa_status: QaStatus::Partial,
        verified_records: Vec::new(),
        gap_records: Vec::new(),
        planner_handoff: PlannerHandoff::default(),
    }
}

pub const PLAN_SKELETON: &str = "## Project Planner Priorities\n\
### Priority Order\n\
1. **<name>** - <action and observable outcome>\n\
### Preservation Gate\n\
- <working functionality / evidence that must not regress>\n\
### Acceptance Gate\n\
- <smallest end-to-end validation>\n";

pub const EVIDENCE_SKELETON: &str = r#"{
  "iteration": <iteration>,
  "qa_status": "pass|partial|fail",
  "verified_records": [
    {
      "claim_id": "<id>",
      "claim": "<checkable claim derived from the public spec>",
      "execution_records": [
        {"type": "screenshot|replay|runtime_trace|assert|build|log", "path": ".hoh/evidence/<file>", "observation": "<verbatim observation>"}
      ],
      "status": "verified"
    }
  ],
  "gap_records": [
    {
      "claim_id": "<id>",
      "claim": "<unmet or unobservable requirement>",
      "execution_records": [],
      "status": "gap",
      "player_impact": "<what the player loses>",
      "recommended_update": "<smallest next step>"
    }
  ],
  "planner_handoff": {
    "preservation_constraints": [],
    "update_targets": [],
    "validation_requirements": []
  }
}
"#;

// ---------------------------------------------------------------------------
// Plan parsing / validation
// ---------------------------------------------------------------------------

fn section_body<'a>(raw: &'a str, heading: &str) -> Option<Vec<&'a str>> {
    let mut lines = raw.lines();
    let mut body: Vec<&'a str> = Vec::new();
    let mut inside = false;
    for line in lines.by_ref() {
        if line.trim_end() == heading {
            inside = true;
            continue;
        }
        if inside {
            if line.starts_with("### ") || line.starts_with("## ") {
                break;
            }
            body.push(line);
        }
    }
    if inside {
        Some(body)
    } else {
        None
    }
}

/// Parse a plan document into its structured fields (no validation).
pub fn parse_plan(raw: &str, iteration: u32, path: PathBuf) -> DevelopmentDoc {
    let numbered = |body: &[&str]| -> Vec<String> {
        body.iter()
            .filter_map(|line| {
                let trimmed = line.trim();
                let mut chars = trimmed.chars();
                let digits: String = chars.clone().take_while(|c| c.is_ascii_digit()).collect();
                if digits.is_empty() {
                    return None;
                }
                let rest: String = chars.by_ref().skip(digits.len()).collect();
                let rest = rest.trim_start_matches('.').trim_start();
                Some(rest.to_string())
            })
            .filter(|item| !item.is_empty())
            .collect()
    };
    let bulleted = |body: &[&str]| -> Vec<String> {
        body.iter()
            .filter_map(|line| {
                let trimmed = line.trim();
                trimmed
                    .strip_prefix("- ")
                    .map(|item| item.trim().to_string())
            })
            .filter(|item| !item.is_empty())
            .collect()
    };

    let priorities = section_body(raw, "### Priority Order")
        .map(|body| numbered(&body))
        .unwrap_or_default();
    let preservation_gate = section_body(raw, "### Preservation Gate")
        .map(|body| bulleted(&body))
        .unwrap_or_default();
    let acceptance_gate = section_body(raw, "### Acceptance Gate")
        .map(|body| bulleted(&body))
        .unwrap_or_default();

    DevelopmentDoc {
        iteration,
        path,
        raw: raw.to_string(),
        priorities,
        preservation_gate,
        acceptance_gate,
    }
}

/// Validate the plan invariants (`DESIGN-DETAIL.md` §2.1).
pub fn validate_plan(doc: &DevelopmentDoc) -> Result<(), Vec<SchemaIssue>> {
    let mut issues = Vec::new();
    if !doc.raw.contains("## Project Planner Priorities") {
        issues.push(SchemaIssue::new(
            IssueCode::MissingSection,
            "plan is missing the required heading `## Project Planner Priorities`",
        ));
    }
    if !doc.raw.contains("### Priority Order") {
        issues.push(SchemaIssue::new(
            IssueCode::MissingSection,
            "plan is missing the required heading `### Priority Order`",
        ));
    } else if doc.priorities.is_empty() {
        issues.push(SchemaIssue::new(
            IssueCode::EmptyGate,
            "`### Priority Order` must contain at least one numbered priority",
        ));
    }
    if !doc.raw.contains("### Preservation Gate") {
        issues.push(SchemaIssue::new(
            IssueCode::MissingSection,
            "plan is missing the required heading `### Preservation Gate`",
        ));
    } else if doc.preservation_gate.is_empty() {
        issues.push(SchemaIssue::new(
            IssueCode::EmptyGate,
            "`### Preservation Gate` must contain at least one `- ` item",
        ));
    }
    if !doc.raw.contains("### Acceptance Gate") {
        issues.push(SchemaIssue::new(
            IssueCode::MissingSection,
            "plan is missing the required heading `### Acceptance Gate`",
        ));
    } else if doc.acceptance_gate.is_empty() {
        issues.push(SchemaIssue::new(
            IssueCode::EmptyGate,
            "`### Acceptance Gate` must contain at least one `- ` item",
        ));
    }
    if doc.priorities.len() > 3 {
        issues.push(SchemaIssue::new(
            IssueCode::EmptyGate,
            format!(
                "planning-policy limit exceeded: {} priorities selected, at most 3 are allowed",
                doc.priorities.len()
            ),
        ));
    }
    if issues.is_empty() {
        Ok(())
    } else {
        Err(issues)
    }
}

// ---------------------------------------------------------------------------
// Evidence validation
// ---------------------------------------------------------------------------

/// Shape check on the raw JSON before typed deserialization.  This is what
/// turns a missing `planner_handoff` into `MissingField` instead of a generic
/// serde failure.
pub fn validate_evidence_shape(value: &serde_json::Value) -> Vec<SchemaIssue> {
    let mut issues = Vec::new();
    let Some(object) = value.as_object() else {
        issues.push(SchemaIssue::new(
            IssueCode::Json,
            "evidence bundle must be a JSON object",
        ));
        return issues;
    };
    for key in [
        "iteration",
        "qa_status",
        "verified_records",
        "gap_records",
        "planner_handoff",
    ] {
        if !object.contains_key(key) {
            issues.push(SchemaIssue::new(
                IssueCode::MissingField,
                format!("evidence bundle is missing the required field `{key}`"),
            ));
        }
    }
    if let Some(handoff) = object.get("planner_handoff") {
        match handoff.as_object() {
            Some(handoff) => {
                for key in [
                    "preservation_constraints",
                    "update_targets",
                    "validation_requirements",
                ] {
                    if !handoff.contains_key(key) {
                        issues.push(SchemaIssue::new(
                            IssueCode::MissingField,
                            format!("`planner_handoff` is missing the required field `{key}`"),
                        ));
                    }
                }
            }
            None => issues.push(SchemaIssue::new(
                IssueCode::MissingField,
                "`planner_handoff` must be an object",
            )),
        }
    }
    issues
}

/// Validate the evidence invariants (`DESIGN-DETAIL.md` §2.1).
///
/// File existence of `execution_records[*].path` needs the candidate view root
/// and is therefore enforced by [`crate::runtime::evidence::bind`].
pub fn validate_evidence(
    bundle: &EvidenceBundle,
    candidate_id: &str,
) -> Result<(), Vec<SchemaIssue>> {
    let mut issues = Vec::new();

    let mut seen: Vec<&str> = Vec::new();
    for record in bundle
        .verified_records
        .iter()
        .chain(bundle.gap_records.iter())
    {
        if seen.contains(&record.claim_id.as_str()) {
            issues.push(SchemaIssue::new(
                IssueCode::DuplicateClaimId,
                format!("claim_id `{}` appears more than once", record.claim_id),
            ));
        }
        seen.push(record.claim_id.as_str());
    }

    if bundle.verified_records.is_empty() && bundle.gap_records.is_empty() {
        issues.push(SchemaIssue::new(
            IssueCode::EmptyClaimList,
            "evidence must contain at least one verified or gap claim",
        ));
    }

    for record in &bundle.verified_records {
        if record.status != ClaimStatus::Verified {
            issues.push(SchemaIssue::new(
                IssueCode::Json,
                format!(
                    "claim `{}` is listed in `verified_records` but its status is not `verified`",
                    record.claim_id
                ),
            ));
        }
        if record.execution_records.is_empty() {
            issues.push(SchemaIssue::new(
                IssueCode::UnsupportedVerified,
                format!(
                    "claim `{}` is verified but has no execution_records",
                    record.claim_id
                ),
            ));
        }
    }

    for record in &bundle.gap_records {
        if record.status != ClaimStatus::Gap {
            issues.push(SchemaIssue::new(
                IssueCode::Json,
                format!(
                    "claim `{}` is listed in `gap_records` but its status is not `gap`",
                    record.claim_id
                ),
            ));
        }
        let missing_impact = record
            .player_impact
            .as_deref()
            .map(str::trim)
            .unwrap_or("")
            .is_empty();
        let missing_update = record
            .recommended_update
            .as_deref()
            .map(str::trim)
            .unwrap_or("")
            .is_empty();
        if missing_impact || missing_update {
            issues.push(SchemaIssue::new(
                IssueCode::GapMissingGuidance,
                format!(
                    "gap claim `{}` must carry non-empty `player_impact` and `recommended_update`",
                    record.claim_id
                ),
            ));
        }
    }

    for record in bundle
        .verified_records
        .iter()
        .chain(bundle.gap_records.iter())
    {
        for exec in &record.execution_records {
            if !exec.candidate_id.is_empty() && exec.candidate_id != candidate_id {
                issues.push(SchemaIssue::new(
                    IssueCode::CandidateMismatch,
                    format!(
                        "execution record of claim `{}` claims candidate `{}` but the runtime candidate is `{}`",
                        record.claim_id, exec.candidate_id, candidate_id
                    ),
                ));
            }
        }
    }

    if issues.is_empty() {
        Ok(())
    } else {
        Err(issues)
    }
}

/// Convenience: does this path look absolute (POSIX or Windows drive)?
pub fn is_absolute_like(path: &str) -> bool {
    if path.starts_with('/') || path.starts_with('\\') {
        return true;
    }
    let bytes = path.as_bytes();
    bytes.len() >= 2 && bytes[0].is_ascii_alphabetic() && bytes[1] == b':'
}

/// Resolve a record path relative to the candidate view root.
pub fn resolve_record_path(view_root: &Path, path: &str) -> PathBuf {
    let normalized = path.replace('\\', "/");
    view_root.join(normalized)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn claim(id: &str, status: ClaimStatus) -> ClaimRecord {
        ClaimRecord {
            claim_id: id.to_string(),
            claim: format!("claim {id}"),
            execution_records: vec![],
            status,
            player_impact: None,
            recommended_update: None,
        }
    }

    fn verified(id: &str) -> ClaimRecord {
        ClaimRecord {
            execution_records: vec![ExecRecord {
                kind: ExecKind::Assert,
                path: None,
                observation: "ok".to_string(),
                candidate_id: String::new(),
            }],
            ..claim(id, ClaimStatus::Verified)
        }
    }

    fn gap(id: &str) -> ClaimRecord {
        ClaimRecord {
            player_impact: Some("player cannot jump".to_string()),
            recommended_update: Some("implement jump".to_string()),
            ..claim(id, ClaimStatus::Gap)
        }
    }

    fn bundle(verified_records: Vec<ClaimRecord>, gap_records: Vec<ClaimRecord>) -> EvidenceBundle {
        EvidenceBundle {
            iteration: 1,
            qa_status: QaStatus::Partial,
            verified_records,
            gap_records,
            planner_handoff: PlannerHandoff::default(),
        }
    }

    fn codes(err: Vec<SchemaIssue>) -> Vec<IssueCode> {
        err.into_iter().map(|issue| issue.code).collect()
    }

    const OK_PLAN: &str = "## Project Planner Priorities\n\
### Priority Order\n\
1. **Movement** - player moves left and right\n\
2. **Jump** - player jumps and lands\n\
### Preservation Gate\n\
- the project still launches\n\
### Acceptance Gate\n\
- simulate left/right and observe displacement\n";

    #[test]
    fn plan_accepts_well_formed_document() {
        let doc = parse_plan(OK_PLAN, 1, PathBuf::from("plan.md"));
        assert_eq!(doc.priorities.len(), 2);
        assert_eq!(doc.preservation_gate.len(), 1);
        assert_eq!(doc.acceptance_gate.len(), 1);
        assert!(validate_plan(&doc).is_ok());
    }

    #[test]
    fn plan_rejects_missing_section() {
        let raw = OK_PLAN.replace("## Project Planner Priorities", "## Priorities");
        let doc = parse_plan(&raw, 1, PathBuf::from("plan.md"));
        assert_eq!(
            codes(validate_plan(&doc).unwrap_err()),
            vec![IssueCode::MissingSection]
        );
    }

    #[test]
    fn plan_rejects_empty_gate() {
        let raw = OK_PLAN.replace("- the project still launches\n", "");
        let doc = parse_plan(&raw, 1, PathBuf::from("plan.md"));
        assert_eq!(
            codes(validate_plan(&doc).unwrap_err()),
            vec![IssueCode::EmptyGate]
        );
    }

    #[test]
    fn plan_rejects_empty_priority_order() {
        let raw = "## Project Planner Priorities\n\
### Priority Order\n\
### Preservation Gate\n\
- the project still launches\n\
### Acceptance Gate\n\
- simulate left/right and observe displacement\n";
        let doc = parse_plan(raw, 1, PathBuf::from("plan.md"));
        assert_eq!(
            codes(validate_plan(&doc).unwrap_err()),
            vec![IssueCode::EmptyGate]
        );
    }

    #[test]
    fn plan_rejects_more_than_three_priorities() {
        let mut raw = String::from("## Project Planner Priorities\n### Priority Order\n");
        for index in 0..4 {
            raw.push_str(&format!("{}. **P{index}** - thing\n", index + 1));
        }
        raw.push_str("### Preservation Gate\n- a\n### Acceptance Gate\n- b\n");
        let doc = parse_plan(&raw, 1, PathBuf::from("plan.md"));
        let issues = validate_plan(&doc).unwrap_err();
        assert!(issues[0].message.contains("planning-policy"));
        assert_eq!(codes(issues), vec![IssueCode::EmptyGate]);
    }

    #[test]
    fn evidence_accepts_partition() {
        let bundle = bundle(vec![verified("c1")], vec![gap("c2")]);
        assert!(validate_evidence(&bundle, "cand").is_ok());
    }

    #[test]
    fn evidence_rejects_duplicate_claim_id() {
        let bundle = bundle(vec![verified("c1")], vec![gap("c1")]);
        assert_eq!(
            codes(validate_evidence(&bundle, "cand").unwrap_err()),
            vec![IssueCode::DuplicateClaimId]
        );
    }

    #[test]
    fn evidence_rejects_empty_claim_list() {
        let bundle = bundle(vec![], vec![]);
        assert_eq!(
            codes(validate_evidence(&bundle, "cand").unwrap_err()),
            vec![IssueCode::EmptyClaimList]
        );
    }

    #[test]
    fn evidence_rejects_status_mismatch() {
        let bundle = bundle(vec![claim("c1", ClaimStatus::Gap)], vec![]);
        let issues = validate_evidence(&bundle, "cand").unwrap_err();
        assert!(issues.iter().any(|issue| issue.code == IssueCode::Json));
        assert!(issues
            .iter()
            .any(|issue| issue.code == IssueCode::UnsupportedVerified));
    }

    #[test]
    fn evidence_rejects_unsupported_verified() {
        let bundle = bundle(vec![claim("c1", ClaimStatus::Verified)], vec![]);
        assert_eq!(
            codes(validate_evidence(&bundle, "cand").unwrap_err()),
            vec![IssueCode::UnsupportedVerified]
        );
    }

    #[test]
    fn evidence_rejects_gap_without_guidance() {
        let mut record = gap("c1");
        record.recommended_update = Some("   ".to_string());
        let bundle = bundle(vec![], vec![record]);
        assert_eq!(
            codes(validate_evidence(&bundle, "cand").unwrap_err()),
            vec![IssueCode::GapMissingGuidance]
        );
    }

    #[test]
    fn evidence_rejects_candidate_mismatch() {
        let mut record = verified("c1");
        record.execution_records[0].candidate_id = "other".to_string();
        let bundle = bundle(vec![record], vec![]);
        assert_eq!(
            codes(validate_evidence(&bundle, "cand").unwrap_err()),
            vec![IssueCode::CandidateMismatch]
        );
    }

    #[test]
    fn evidence_shape_reports_missing_handoff() {
        let value: serde_json::Value = serde_json::json!({
            "iteration": 1,
            "qa_status": "pass",
            "verified_records": [],
            "gap_records": []
        });
        assert_eq!(
            codes(validate_evidence_shape(&value)),
            vec![IssueCode::MissingField]
        );

        let value: serde_json::Value = serde_json::json!({
            "iteration": 1,
            "qa_status": "pass",
            "verified_records": [],
            "gap_records": [],
            "planner_handoff": {"update_targets": []}
        });
        assert_eq!(
            codes(validate_evidence_shape(&value)),
            vec![IssueCode::MissingField, IssueCode::MissingField]
        );
    }

    #[test]
    fn absolute_like_detection_matches_posix_and_drive() {
        assert!(is_absolute_like("/tmp/x"));
        assert!(is_absolute_like("C:/tmp/x"));
        assert!(is_absolute_like("D:\\tmp\\x"));
        assert!(!is_absolute_like(".hoh/evidence/x.png"));
        assert!(!is_absolute_like("scripts/player.gd"));
    }
}
