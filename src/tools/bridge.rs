//! `hoh tools` / `hoh submit`: the thin CLI bridge the agents call through
//! mini's shell action (OPEN-2, §5.3).

use std::path::{Path, PathBuf};

use serde_json::{json, Value};

use crate::config::HohConfig;
use crate::errors::HofError;
use crate::model::{parse_plan, validate_evidence, validate_evidence_shape, validate_plan, Role};
use crate::tools::policy::denial_payload;
use crate::tools::{McpChannel, ToolChannel};

/// Resolve the acting role from `--role`, falling back to `$HOH_ROLE`.
pub fn resolve_role(explicit: Option<&str>) -> anyhow::Result<Role> {
    let raw = explicit
        .map(ToOwned::to_owned)
        .or_else(|| std::env::var("HOH_ROLE").ok())
        .ok_or_else(|| HofError::Config("no role given and HOH_ROLE is not set".to_string()))?;
    Role::parse(&raw).ok_or_else(|| {
        HofError::Config(format!(
            "unknown role `{raw}` (expected planner|developer|tester)"
        ))
        .into()
    })
}

/// DR-20: resolve a path against the current directory without requiring it to
/// exist (as `canonicalize` would).  The error message for a missing file must
/// name the path the bridge actually looked for, so a relative `--args-file`
/// from a different working directory is diagnosable.
pub fn absolutize(path: &Path) -> PathBuf {
    if path.is_absolute() {
        return path.to_path_buf();
    }
    match std::env::current_dir() {
        Ok(cwd) => cwd.join(path),
        Err(_) => path.to_path_buf(),
    }
}

/// Tool arguments: `--args` (inline JSON) or `--args-file` (preferred on
/// Windows, where shell quoting mangles JSON).
///
/// DR-25: a **relative** `--args-file` is resolved against
/// `HOH_ARTIFACT_DIR`, not against the shell's working directory — the role
/// shell may run from anywhere, and `smoke-t2` lost two Tester calls to
/// `os error 3` because of exactly that mismatch.
pub fn parse_args(inline: Option<&str>, args_file: Option<&Path>) -> anyhow::Result<Value> {
    let artifact_dir = std::env::var("HOH_ARTIFACT_DIR").ok().map(PathBuf::from);
    parse_args_in(inline, args_file, artifact_dir.as_deref())
}

/// [`parse_args`] with an explicit artifact directory (pure, unit-testable).
pub fn parse_args_in(
    inline: Option<&str>,
    args_file: Option<&Path>,
    artifact_dir: Option<&Path>,
) -> anyhow::Result<Value> {
    if let Some(path) = args_file {
        let absolute = resolve_args_file(path, artifact_dir);
        let raw = std::fs::read_to_string(&absolute).map_err(|error| {
            anyhow::anyhow!(
                "could not read --args-file {} (resolved against {}: `{}`): {error}",
                path.display(),
                if path.is_absolute() {
                    "an absolute path"
                } else if artifact_dir.is_some() {
                    "HOH_ARTIFACT_DIR"
                } else {
                    "the current directory"
                },
                absolute.display()
            )
        })?;
        return serde_json::from_str(&raw).map_err(|error| {
            anyhow::anyhow!(
                "--args-file {} is not valid JSON: {error}",
                absolute.display()
            )
        });
    }
    match inline {
        Some(raw) => serde_json::from_str(raw)
            .map_err(|error| anyhow::anyhow!("--args is not valid JSON: {error}")),
        None => Ok(json!({})),
    }
}

/// DR-25: resolve a relative `--args-file` against `HOH_ARTIFACT_DIR`.
pub fn resolve_args_file(path: &Path, artifact_dir: Option<&Path>) -> PathBuf {
    if path.is_absolute() {
        return path.to_path_buf();
    }
    match artifact_dir {
        Some(dir) => dir.join(path),
        None => absolutize(path),
    }
}

/// Lexically normalize a path (`a/./b` -> `a/b`, `a/../b` -> `b`) so two
/// spellings of the same target compare equal.
pub fn normalize(path: &Path) -> PathBuf {
    use std::path::Component;
    let mut out = PathBuf::new();
    for component in path.components() {
        match component {
            Component::CurDir => {}
            Component::ParentDir => {
                if !out.pop() {
                    out.push("..");
                }
            }
            other => out.push(other.as_os_str()),
        }
    }
    out
}

/// DR-25: the canonical artifact path of a role (`<view>/.hoh/<name>`).
pub fn canonical_artifact(role: Role, artifact_dir: &Path) -> PathBuf {
    artifact_dir.join(match role {
        Role::Planner => "plan.md",
        Role::Tester => "evidence.json",
        Role::Developer => "developer.md",
    })
}

/// Build the MCP-backed tool channel for a config.
pub fn channel_for(config: &HohConfig) -> McpChannel {
    McpChannel::new(
        config.tools.endpoint.clone(),
        config.tools.timeout_seconds,
        config.tools.max_retries,
    )
}

/// `hoh tools call <tool>`: deny first, then call.
pub async fn tools_call(
    channel: &dyn ToolChannel,
    role: Role,
    tool: &str,
    args: Value,
) -> anyhow::Result<i32> {
    if !channel.allowed(role, tool) {
        println!("{}", denial_payload(role, tool));
        return Ok(2);
    }
    let result = channel.call(role, tool, args).await?;
    println!("{}", serde_json::to_string_pretty(&result.payload)?);
    Ok(0)
}

/// `hoh submit --role <planner|tester> --file <path>`.
///
/// DR-25: `--file` is resolved against `HOH_ARTIFACT_DIR` when relative, and the
/// resolved target must be **byte-for-byte** the role's canonical artifact path.
/// A relative `HOH_ARTIFACT_DIR` (the `smoke-t2` bug: the plan landed in a
/// nested `runs/<id>/iter-1/planner-view/runs/...` path) is refused outright
/// instead of silently nesting.
pub fn submit(role: Role, file: &Path) -> anyhow::Result<i32> {
    if role == Role::Developer {
        eprintln!("{}", denial_payload(role, "submit"));
        let payload = json!({
            "ok": false,
            "error": "tool_not_permitted",
            "role": "developer",
            "tool": "submit",
            "hint": "The Developer has no submitted artifact: the artifact is the project itself."
        });
        println!("{payload}");
        return Ok(2);
    }

    let artifact_dir = artifact_dir()?;
    let expected = canonical_artifact(role, &artifact_dir);
    // The target of the write is always the canonical path; it must be an
    // absolute, already-correct path or the whole "who wrote what" model is
    // built on sand.
    if !expected.is_absolute() {
        println!(
            "{}",
            serde_json::to_string_pretty(&json!({
                "ok": false,
                "error": "artifact_path_violation",
                "reason": "HOH_ARTIFACT_DIR must be an absolute path (DR-25)",
                "expected": std::env::current_dir()
                    .map(|cwd| normalize(&cwd.join(&expected)).to_string_lossy().into_owned())
                    .unwrap_or_else(|_| expected.to_string_lossy().into_owned()),
                "actual": expected.to_string_lossy(),
            }))?
        );
        return Ok(2);
    }

    // Resolve the source the same way every other path is resolved here.
    let resolved = if file.is_absolute() {
        normalize(file)
    } else {
        normalize(&artifact_dir.join(file))
    };
    if !file.is_absolute() && resolved != normalize(&expected) {
        println!(
            "{}",
            serde_json::to_string_pretty(&json!({
                "ok": false,
                "error": "artifact_path_violation",
                "reason": "a relative --file is resolved against HOH_ARTIFACT_DIR and must name \
                           the role's canonical artifact",
                "expected": normalize(&expected).to_string_lossy(),
                "actual": resolved.to_string_lossy(),
            }))?
        );
        return Ok(2);
    }

    let raw = std::fs::read_to_string(&resolved)
        .map_err(|error| anyhow::anyhow!("could not read {}: {error}", resolved.display()))?;

    let issues = match role {
        Role::Planner => {
            let doc = parse_plan(&raw, 0, resolved.clone());
            validate_plan(&doc).err()
        }
        Role::Tester => match serde_json::from_str::<Value>(&raw) {
            Err(error) => Some(vec![crate::model::SchemaIssue::new(
                crate::model::IssueCode::Json,
                format!("evidence is not valid JSON: {error}"),
            )]),
            Ok(value) => {
                let shape = validate_evidence_shape(&value);
                if !shape.is_empty() {
                    Some(shape)
                } else {
                    match serde_json::from_value::<crate::model::EvidenceBundle>(value) {
                        Err(error) => Some(vec![crate::model::SchemaIssue::new(
                            crate::model::IssueCode::Json,
                            format!("evidence does not match the required structure: {error}"),
                        )]),
                        Ok(bundle) => {
                            let mut issues =
                                validate_evidence(&bundle, "").err().unwrap_or_default();
                            // The inner gate also checks that every referenced
                            // file exists under the view root (§4.3, §4.6).
                            let view_root = artifact_dir
                                .parent()
                                .map(PathBuf::from)
                                .unwrap_or_else(|| PathBuf::from("."));
                            issues
                                .extend(crate::runtime::evidence::check_paths(&bundle, &view_root));
                            if issues.is_empty() {
                                None
                            } else {
                                Some(issues)
                            }
                        }
                    }
                }
            }
        },
        Role::Developer => unreachable!(),
    };

    if let Some(issues) = issues {
        println!(
            "{}",
            serde_json::to_string_pretty(&json!({"ok": false, "issues": issues}))?
        );
        return Ok(3);
    }

    std::fs::create_dir_all(&artifact_dir)?;
    write_atomic(&expected, raw.as_bytes())?;
    println!(
        "{}",
        serde_json::to_string_pretty(&json!({"ok": true, "written": expected.to_string_lossy()}))?
    );
    Ok(0)
}

fn artifact_dir() -> anyhow::Result<PathBuf> {
    std::env::var("HOH_ARTIFACT_DIR")
        .map(PathBuf::from)
        .map_err(|_| {
            HofError::Config(
                "HOH_ARTIFACT_DIR is not set; run inside a role view or pass the role environment"
                    .to_string(),
            )
            .into()
        })
}

/// Atomically replace a file so a crash never leaves a half-written artifact.
pub fn write_atomic(path: &Path, bytes: &[u8]) -> anyhow::Result<()> {
    if let Some(parent) = path.parent() {
        std::fs::create_dir_all(parent)?;
    }
    let temp = path.with_extension("tmp-submit");
    std::fs::write(&temp, bytes)?;
    if path.exists() {
        std::fs::remove_file(path)?;
    }
    std::fs::rename(&temp, path)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn args_file_wins_over_inline() {
        let temp = tempfile::tempdir().unwrap();
        let path = temp.path().join("args.json");
        std::fs::write(&path, r#"{"node_path": "/root/Main/Player"}"#).unwrap();
        let value = parse_args(Some("{}"), Some(&path)).unwrap();
        assert_eq!(value["node_path"], json!("/root/Main/Player"));
    }

    #[test]
    fn args_default_to_an_empty_object() {
        assert_eq!(parse_args(None, None).unwrap(), json!({}));
        assert!(parse_args(Some("not json"), None).is_err());
    }
}
