//! `EvidenceBinder`: candidate identity stamping and the file-existence half of
//! the evidence contract (`DESIGN-DETAIL.md` §4.6).
//!
//! The runtime stamps `candidate_id` and checks that every referenced file
//! really exists inside the candidate view.  It never rewrites the Tester's
//! claims, statuses or observations — the implementer is not allowed to grade
//! its own work, and neither is the runtime.

use std::path::Path;

use crate::model::{is_absolute_like, resolve_record_path, EvidenceBundle, IssueCode, SchemaIssue};

/// Validate + stamp every execution record against the candidate identity.
pub fn bind(
    bundle: &mut EvidenceBundle,
    candidate_id: &str,
    view_root: &Path,
) -> Result<(), Vec<SchemaIssue>> {
    let mut issues = Vec::new();

    for record in bundle
        .verified_records
        .iter_mut()
        .chain(bundle.gap_records.iter_mut())
    {
        for exec in record.execution_records.iter_mut() {
            if let Some(path) = exec.path.clone() {
                let normalized = path.replace('\\', "/");
                if is_absolute_like(&normalized) {
                    issues.push(SchemaIssue::new(
                        IssueCode::DanglingEvidence,
                        format!(
                            "execution record of claim `{}` uses the absolute path `{path}`; \
                             evidence paths must be relative to the candidate view root",
                            record.claim_id
                        ),
                    ));
                } else {
                    let resolved = resolve_record_path(view_root, &path);
                    if !resolved.is_file() {
                        issues.push(SchemaIssue::new(
                            IssueCode::DanglingEvidence,
                            format!(
                                "execution record of claim `{}` references `{path}` which does not \
                                 exist at {}",
                                record.claim_id,
                                resolved.display()
                            ),
                        ));
                    }
                }
            }

            if exec.candidate_id.is_empty() {
                exec.candidate_id = candidate_id.to_string();
            } else if exec.candidate_id != candidate_id {
                issues.push(SchemaIssue::new(
                    IssueCode::CandidateMismatch,
                    format!(
                        "execution record of claim `{}` claims candidate `{}` but the runtime \
                         candidate is `{candidate_id}`",
                        record.claim_id, exec.candidate_id
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

/// Materialize an evidence bundle as pretty JSON with LF line endings.
pub fn write_evidence(path: &Path, bundle: &EvidenceBundle) -> anyhow::Result<()> {
    let mut serialized = serde_json::to_string_pretty(bundle)?;
    if !serialized.ends_with('\n') {
        serialized.push('\n');
    }
    let normalized = serialized.replace("\r\n", "\n");
    if let Some(parent) = path.parent() {
        std::fs::create_dir_all(parent)?;
    }
    std::fs::write(path, normalized)?;
    Ok(())
}
