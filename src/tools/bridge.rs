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

/// Tool arguments: `--args` (inline JSON) or `--args-file` (preferred on
/// Windows, where shell quoting mangles JSON).
pub fn parse_args(inline: Option<&str>, args_file: Option<&Path>) -> anyhow::Result<Value> {
    if let Some(path) = args_file {
        let raw = std::fs::read_to_string(path).map_err(|error| {
            anyhow::anyhow!("could not read --args-file {}: {error}", path.display())
        })?;
        return serde_json::from_str(&raw)
            .map_err(|error| anyhow::anyhow!("--args-file is not valid JSON: {error}"));
    }
    match inline {
        Some(raw) => serde_json::from_str(raw)
            .map_err(|error| anyhow::anyhow!("--args is not valid JSON: {error}")),
        None => Ok(json!({})),
    }
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

    let raw = std::fs::read_to_string(file)
        .map_err(|error| anyhow::anyhow!("could not read {}: {error}", file.display()))?;

    let issues = match role {
        Role::Planner => {
            let doc = parse_plan(&raw, 0, file.to_path_buf());
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
                        Ok(bundle) => validate_evidence(&bundle, "").err(),
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

    let artifact_dir = artifact_dir()?;
    std::fs::create_dir_all(&artifact_dir)?;
    let target = artifact_dir.join(match role {
        Role::Planner => "plan.md",
        Role::Tester => "evidence.json",
        Role::Developer => unreachable!(),
    });
    write_atomic(&target, raw.as_bytes())?;
    println!(
        "{}",
        serde_json::to_string_pretty(&json!({"ok": true, "written": target.to_string_lossy()}))?
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
