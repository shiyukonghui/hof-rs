//! `EvidenceBinder`: candidate identity stamping and the file-existence half of
//! the evidence contract (`DESIGN-DETAIL.md` §4.6).
//!
//! The runtime stamps `candidate_id` and checks that every referenced file
//! really exists inside the candidate view.  It never rewrites the Tester's
//! claims, statuses or observations — the implementer is not allowed to grade
//! its own work, and neither is the runtime.

use std::path::{Component, Path};

use crate::model::{is_absolute_like, resolve_record_path, EvidenceBundle, IssueCode, SchemaIssue};

/// A record path must be a plain relative path inside the view root.  A `..`
/// component is rejected outright: together with the canonicalize prefix
/// assertion below it closes the blocker where `../outside_secret.txt` passed
/// merely because the target file happened to exist (DR-10 / A1).
fn has_parent_dir(path: &str) -> bool {
    Path::new(&path.replace('\\', "/"))
        .components()
        .any(|component| component == Component::ParentDir)
}

/// File-existence half of the contract, usable on its own (the `hoh submit`
/// inner gate has no candidate identity yet, but it does have the view root).
///
/// Three independent gates, all of which must pass (DR-10):
/// 1. no absolute path (POSIX `/`, Windows drive letter);
/// 2. no `..` component;
/// 3. the resolved path must exist *and*, after `canonicalize`, still live under
///    `canonicalize(view_root)` — which also rejects symlink escapes.
pub fn check_paths(bundle: &EvidenceBundle, view_root: &Path) -> Vec<SchemaIssue> {
    let mut issues = Vec::new();
    let canonical_root = view_root.canonicalize();
    for record in bundle
        .verified_records
        .iter()
        .chain(bundle.gap_records.iter())
    {
        for exec in &record.execution_records {
            let Some(path) = exec.path.as_deref() else {
                continue;
            };
            let normalized = path.replace('\\', "/");
            if is_absolute_like(&normalized) {
                issues.push(SchemaIssue::new(
                    IssueCode::DanglingEvidence,
                    format!(
                        "execution record of claim `{}` uses the absolute path `{path}`; evidence \
                         paths must be relative to the candidate view root",
                        record.claim_id
                    ),
                ));
                continue;
            }
            if has_parent_dir(path) {
                issues.push(SchemaIssue::new(
                    IssueCode::DanglingEvidence,
                    format!(
                        "execution record of claim `{}` uses `{path}`, which escapes the candidate \
                         view root through a `..` component",
                        record.claim_id
                    ),
                ));
                continue;
            }
            let resolved = resolve_record_path(view_root, path);
            if !resolved.is_file() {
                issues.push(SchemaIssue::new(
                    IssueCode::DanglingEvidence,
                    format!(
                        "execution record of claim `{}` references `{path}` which does not exist \
                         at {}",
                        record.claim_id,
                        resolved.display()
                    ),
                ));
                continue;
            }
            // Existence is not enough: the file must resolve *inside* the view.
            let inside = match (&canonical_root, resolved.canonicalize()) {
                (Ok(root), Ok(target)) => target.starts_with(root),
                _ => false,
            };
            if !inside {
                issues.push(SchemaIssue::new(
                    IssueCode::DanglingEvidence,
                    format!(
                        "execution record of claim `{}` references `{path}`, which resolves to {} \
                         outside the candidate view root {}",
                        record.claim_id,
                        resolved.display(),
                        view_root.display()
                    ),
                ));
            }
        }
    }
    issues
}

/// Validate + stamp every execution record against the candidate identity.
pub fn bind(
    bundle: &mut EvidenceBundle,
    candidate_id: &str,
    view_root: &Path,
) -> Result<(), Vec<SchemaIssue>> {
    let mut issues = check_paths(bundle, view_root);

    for record in bundle
        .verified_records
        .iter_mut()
        .chain(bundle.gap_records.iter_mut())
    {
        for exec in record.execution_records.iter_mut() {
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
