//! Subcommand implementations.  Kept separate from `cli.rs` so the clap
//! surface stays declarative and the `hoh` binary entry point stays tiny.

use std::path::{Path, PathBuf};
use std::sync::Arc;

use serde_json::{json, Value};

use crate::adapter::{DoctorItem, GodotAdapter, ProjectAdapter, TestAdapter};
use crate::cli::{
    config_specs, parse_ablation, DoctorArgs, RollbackArgs, RunArgs, SpecHashArgs, StatusArgs,
    SubmitArgs, ToolsArgs, ToolsCommand,
};
use crate::config::{load_config, load_spec, HohConfig};
use crate::errors::HofError;
use crate::model::Role;
use crate::runtime::policy::{hash_tree, HashExcludes};
use crate::runtime::run_loop::{self, Orchestrator};
use crate::runtime::snapshot::VersionStore;
use crate::tools::bridge;
use crate::tools::ToolChannel;

pub async fn spec_hash(args: SpecHashArgs) -> anyhow::Result<i32> {
    let path = args
        .spec
        .unwrap_or_else(|| PathBuf::from(".spec/hof-rs/PRD-mario.md"));
    let spec = load_spec(&path)?;
    println!("{}", spec.sha256);
    Ok(0)
}

// ---------------------------------------------------------------------------
// tools
// ---------------------------------------------------------------------------

pub async fn tools(args: ToolsArgs) -> anyhow::Result<i32> {
    match args.command {
        ToolsCommand::Call(call) => {
            let role = bridge::resolve_role(call.role.as_deref())?;
            // The policy check must happen before any configuration or network
            // access: a denied tool is refused even if Godot is offline.
            if !crate::tools::policy::tool_allowed(role, &call.tool) {
                println!(
                    "{}",
                    serde_json::to_string_pretty(&crate::tools::policy::denial_payload(
                        role, &call.tool
                    ))?
                );
                return Ok(2);
            }
            let config = load_with(&call.config_spec)?;
            let args = bridge::parse_args(call.args.as_deref(), call.args_file.as_deref())?;
            let channel = bridge::channel_for(&config);
            bridge::tools_call(&channel, role, &call.tool, args).await
        }
        ToolsCommand::List(list) => {
            let role = bridge::resolve_role(list.role.as_deref())?;
            let config = load_with(&list.config_spec)?;
            let channel = bridge::channel_for(&config);
            let mut names: Vec<String> = channel
                .client()
                .list_tools()?
                .into_iter()
                .filter(|tool| channel.allowed(role, tool))
                .collect();
            names.sort();
            for name in names {
                println!("{name}");
            }
            Ok(0)
        }
        ToolsCommand::Describe(describe) => {
            let config = load_with(&describe.config_spec)?;
            let channel = bridge::channel_for(&config);
            let description = channel.client().describe(&describe.tool)?;
            println!("{}", serde_json::to_string_pretty(&description)?);
            Ok(0)
        }
    }
}

// ---------------------------------------------------------------------------
// submit
// ---------------------------------------------------------------------------

pub async fn submit(args: SubmitArgs) -> anyhow::Result<i32> {
    let role = Role::parse(&args.role).ok_or_else(|| {
        HofError::Config(format!(
            "unknown role `{}` (expected planner|developer|tester)",
            args.role
        ))
    })?;
    bridge::submit(role, &args.file)
}

// ---------------------------------------------------------------------------
// doctor
// ---------------------------------------------------------------------------

/// The six doctor checks of §8.  Every one must pass before a run starts.
pub async fn doctor_checks(
    config: &HohConfig,
    adapter: &dyn ProjectAdapter,
    workspace: &Path,
) -> anyhow::Result<Vec<DoctorItem>> {
    let mut items = Vec::new();

    // 1. The frozen spec exists and is non-empty.
    match std::fs::read(&config.runtime.spec) {
        Ok(bytes) if !bytes.is_empty() => items.push(DoctorItem {
            name: "spec".to_string(),
            ok: true,
            detail: format!(
                "{} (sha256 {})",
                config.runtime.spec.display(),
                crate::runtime::policy::sha256_hex(&bytes)
            ),
        }),
        Ok(_) => items.push(DoctorItem {
            name: "spec".to_string(),
            ok: false,
            detail: format!("{} is empty", config.runtime.spec.display()),
        }),
        Err(error) => items.push(DoctorItem {
            name: "spec".to_string(),
            ok: false,
            detail: format!("{}: {error}", config.runtime.spec.display()),
        }),
    }

    // 2. Model identity (C9/C10).
    match crate::config::assert_model_identity(&config.model) {
        Ok(()) => items.push(DoctorItem {
            name: "model.identity".to_string(),
            ok: true,
            detail: format!(
                "config `{}` -> wire `{}`",
                config.model_name(),
                crate::config::WIRE_MODEL_NAME
            ),
        }),
        Err(error) => items.push(DoctorItem {
            name: "model.identity".to_string(),
            ok: false,
            detail: error.to_string(),
        }),
    }

    // 3. A minimal chat request must answer with the canonical model id.
    items.push(chat_probe(config));
    // 4. LM Studio must not have a second resident instance (D6).
    items.push(models_probe(config));

    // 5. Adapter checks.
    match adapter.doctor(workspace) {
        Ok(adapter_items) => items.extend(adapter_items),
        Err(error) => items.push(DoctorItem {
            name: "adapter".to_string(),
            ok: false,
            detail: error.to_string(),
        }),
    }

    // 6. The MCP tool server must be reachable and expose at least one tool.
    let channel = bridge::channel_for(config);
    match channel.client().list_tools() {
        Ok(tools) if !tools.is_empty() => items.push(DoctorItem {
            name: "tools.mcp".to_string(),
            ok: true,
            detail: format!(
                "{} tools available at {}",
                tools.len(),
                config.tools.endpoint
            ),
        }),
        Ok(_) => items.push(DoctorItem {
            name: "tools.mcp".to_string(),
            ok: false,
            detail: format!("{} exposed no tools", config.tools.endpoint),
        }),
        Err(error) => items.push(DoctorItem {
            name: "tools.mcp".to_string(),
            ok: false,
            detail: error.to_string(),
        }),
    }

    Ok(items)
}

fn chat_probe(config: &HohConfig) -> DoctorItem {
    let url = format!(
        "{}/chat/completions",
        config.base_url().trim_end_matches('/')
    );
    let body = json!({
        "model": crate::config::WIRE_MODEL_NAME,
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 1
    });
    let agent = ureq::AgentBuilder::new()
        .timeout(std::time::Duration::from_secs(30))
        .build();
    match agent
        .post(&url)
        .set("Content-Type", "application/json")
        .send_json(body)
    {
        Ok(response) => {
            let value: Value = response.into_json().unwrap_or(Value::Null);
            let model = value.get("model").and_then(Value::as_str).unwrap_or("");
            if model == crate::config::WIRE_MODEL_NAME {
                DoctorItem {
                    name: "model.chat".to_string(),
                    ok: true,
                    detail: format!("{url} answered with model `{model}`"),
                }
            } else {
                DoctorItem {
                    name: "model.chat".to_string(),
                    ok: false,
                    detail: format!(
                        "{url} answered with model `{model}` instead of `{}`",
                        crate::config::WIRE_MODEL_NAME
                    ),
                }
            }
        }
        Err(error) => DoctorItem {
            name: "model.chat".to_string(),
            ok: false,
            detail: format!("{url}: {error}"),
        },
    }
}

fn models_probe(config: &HohConfig) -> DoctorItem {
    let root = config
        .base_url()
        .trim_end_matches('/')
        .trim_end_matches("/v1")
        .trim_end_matches('/');
    let url = format!("{root}/api/v0/models");
    let agent = ureq::AgentBuilder::new()
        .timeout(std::time::Duration::from_secs(15))
        .build();
    match agent.get(&url).call() {
        Ok(response) => {
            let value: Value = response.into_json().unwrap_or(Value::Null);
            let entries = value
                .get("data")
                .and_then(Value::as_array)
                .cloned()
                .unwrap_or_default();
            let loaded: Vec<String> = entries
                .iter()
                .filter(|entry| entry.get("state").and_then(Value::as_str) == Some("loaded"))
                .filter_map(|entry| entry.get("id").and_then(Value::as_str))
                .map(ToOwned::to_owned)
                .collect();
            let stripped = loaded.iter().any(|id| id == "qwen3.8-27b");
            if stripped {
                DoctorItem {
                    name: "model.resident".to_string(),
                    ok: false,
                    detail: format!(
                        "a bare `qwen3.8-27b` instance is loaded ({loaded:?}); unload it in LM \
                         Studio, it doubles VRAM (D6)"
                    ),
                }
            } else {
                DoctorItem {
                    name: "model.resident".to_string(),
                    ok: true,
                    detail: format!("loaded: {loaded:?}"),
                }
            }
        }
        Err(error) => DoctorItem {
            name: "model.resident".to_string(),
            ok: false,
            detail: format!("{url}: {error}"),
        },
    }
}

pub async fn doctor(args: DoctorArgs) -> anyhow::Result<i32> {
    let mut specs = config_specs(&args.config_spec);
    specs.push(format!("adapter.kind={}", args.adapter));
    if let Some(project) = &args.project {
        specs.push(format!("runtime.workspace={}", project.display()));
    }
    let config = load_config(&specs)?;
    let adapter = build_adapter(&config)?;
    let workspace = config.runtime.workspace.clone();
    let items = doctor_checks(&config, &*adapter, &workspace).await?;
    print_doctor(&items);
    if items.iter().all(|item| item.ok) {
        Ok(0)
    } else {
        Ok(4)
    }
}

fn print_doctor(items: &[DoctorItem]) {
    for item in items {
        println!(
            "[{}] {}: {}",
            if item.ok { "ok" } else { "FAIL" },
            item.name,
            item.detail
        );
    }
}

// ---------------------------------------------------------------------------
// run
// ---------------------------------------------------------------------------

fn build_adapter(config: &HohConfig) -> anyhow::Result<Box<dyn ProjectAdapter>> {
    build_adapter_kind(&config.adapter.kind, config, false)
}

fn build_adapter_kind(
    kind: &str,
    config: &HohConfig,
    force_init: bool,
) -> anyhow::Result<Box<dyn ProjectAdapter>> {
    match kind {
        "godot" | "godot_mcp" => Ok(Box::new(GodotAdapter::new(
            config.adapter.godot.clone(),
            force_init,
        ))),
        "test" => Ok(Box::new(TestAdapter::new())),
        other => {
            Err(HofError::Config(format!("unknown adapter `{other}` (expected godot|test)")).into())
        }
    }
}

pub async fn run(args: RunArgs) -> anyhow::Result<i32> {
    if args.resume {
        return Err(HofError::ResumeNotImplemented.into());
    }

    let mut specs = config_specs(&args.config_spec);
    specs.push(format!("adapter.kind={}", args.adapter));
    specs.push(format!("runtime.iterations={}", args.iterations));
    specs.push(format!(
        "runtime.max_schema_retries={}",
        args.max_schema_retries
    ));
    if let Some(spec) = &args.spec {
        specs.push(format!("runtime.spec={}", spec.display()));
    }
    if let Some(project) = &args.project {
        specs.push(format!("runtime.workspace={}", project.display()));
    }
    let config = load_config(&specs)?;
    let ablation = parse_ablation(&args.ablate)?;
    let adapter = build_adapter_kind(&args.adapter, &config, args.force_init)?;
    let workspace = config.runtime.workspace.clone();

    // §8: the doctor pre-check is mandatory and must run before anything else.
    let items = doctor_checks(&config, &*adapter, &workspace).await?;
    print_doctor(&items);
    if !items.iter().all(|item| item.ok) {
        eprintln!("hoh run: pre-flight checks failed; the run was not started");
        return Ok(4);
    }

    let spec = load_spec(&config.runtime.spec)?;
    let run_id = args.run_id.clone().unwrap_or_else(default_run_id);
    let run_dir = config.runtime.runs_dir.join(&run_id);
    if run_dir.exists() {
        return Err(HofError::Config(format!(
            "run directory {} already exists; pass --resume (not implemented in v1)",
            run_dir.display()
        ))
        .into());
    }

    let harness = crate::harness::MiniHarness::new();
    let tools: Arc<dyn ToolChannel> = if args.adapter == "test" {
        Arc::new(crate::tools::ShellOnlyChannel)
    } else {
        Arc::new(bridge::channel_for(&config))
    };
    let orchestrator = Orchestrator {
        harness: Box::new(harness),
        adapter,
        tools,
        cfg: config,
        ablation,
        force_init: args.force_init,
    };

    let summary = run_loop::run(&orchestrator, &spec, &run_id).await?;
    println!(
        "run {} finished: {} iteration(s), final version {:?}, total tokens {:?}",
        summary.run_id,
        summary.iterations_completed,
        summary.final_version_id,
        summary.total_usage.total_tokens
    );
    Ok(0)
}

/// `<UTC yyyymmdd-HHMMSS>-<uuid4 first 8>`.
fn default_run_id() -> String {
    let now = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|duration| duration.as_secs())
        .unwrap_or(0);
    let stamp = format_utc(now);
    let uuid = uuid::Uuid::new_v4().simple().to_string();
    format!("{stamp}-{}", &uuid[..8])
}

/// Minimal UTC formatter (no chrono dependency): `yyyymmdd-HHMMSS`.
fn format_utc(seconds: u64) -> String {
    let days = seconds / 86_400;
    let rem = seconds % 86_400;
    let (hour, minute, second) = (rem / 3600, (rem % 3600) / 60, rem % 60);
    let (year, month, day) = civil_from_days(days as i64);
    format!("{year:04}{month:02}{day:02}-{hour:02}{minute:02}{second:02}")
}

/// Howard Hinnant's `civil_from_days`.
fn civil_from_days(days: i64) -> (i64, u32, u32) {
    let z = days + 719_468;
    let era = if z >= 0 { z } else { z - 146_096 } / 146_097;
    let doe = z - era * 146_097;
    let yoe = (doe - doe / 1460 + doe / 36_524 - doe / 146_096) / 365;
    let y = yoe + era * 400;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let d = doy - (153 * mp + 2) / 5 + 1;
    let m = if mp < 10 { mp + 3 } else { mp - 9 };
    (if m <= 2 { y + 1 } else { y }, m as u32, d as u32)
}

// ---------------------------------------------------------------------------
// status / rollback
// ---------------------------------------------------------------------------

pub async fn status(args: StatusArgs) -> anyhow::Result<i32> {
    let runs_dir = args
        .runs_dir
        .or_else(|| std::env::var("HOH_RUNS_DIR").ok().map(PathBuf::from))
        .unwrap_or_else(|| PathBuf::from("runs"));
    let run_id = match args.run_id {
        Some(run_id) => run_id,
        None => latest_run_id(&runs_dir)?,
    };
    let run_dir = runs_dir.join(&run_id);
    if !run_dir.is_dir() {
        return Err(HofError::Config(format!("no such run: {}", run_dir.display())).into());
    }

    let mut total_tokens: u64 = 0;
    println!("# run {run_id}");
    let mut iterations: Vec<PathBuf> = std::fs::read_dir(&run_dir)?
        .filter_map(|entry| entry.ok().map(|entry| entry.path()))
        .filter(|path| {
            path.file_name()
                .map(|name| name.to_string_lossy().starts_with("iter-"))
                .unwrap_or(false)
        })
        .collect();
    iterations.sort();
    for iter_dir in iterations {
        let result: Value = std::fs::read_to_string(iter_dir.join("result.json"))
            .ok()
            .and_then(|raw| serde_json::from_str(&raw).ok())
            .unwrap_or(Value::Null);
        let usage: Vec<Value> = std::fs::read_to_string(iter_dir.join("usage.json"))
            .ok()
            .and_then(|raw| serde_json::from_str(&raw).ok())
            .unwrap_or_default();
        for entry in &usage {
            total_tokens += entry
                .get("total_tokens")
                .and_then(Value::as_u64)
                .unwrap_or(0);
        }
        println!(
            "{:<8} ok={:<5} reason={:<20} candidate={} roles={}",
            iter_dir
                .file_name()
                .map(|name| name.to_string_lossy().into_owned())
                .unwrap_or_default(),
            result.get("ok").and_then(Value::as_bool).unwrap_or(false),
            result
                .get("reason")
                .and_then(Value::as_str)
                .unwrap_or("unknown"),
            result
                .get("candidate_id")
                .and_then(Value::as_str)
                .unwrap_or("-"),
            usage.len()
        );
    }
    println!("total tokens: {total_tokens}");
    Ok(0)
}

fn latest_run_id(runs_dir: &Path) -> anyhow::Result<String> {
    let mut ids: Vec<String> = std::fs::read_dir(runs_dir)
        .map_err(|error| anyhow::anyhow!("could not read {}: {error}", runs_dir.display()))?
        .filter_map(|entry| entry.ok())
        .filter(|entry| entry.path().is_dir())
        .map(|entry| entry.file_name().to_string_lossy().into_owned())
        .collect();
    ids.sort();
    ids.pop()
        .ok_or_else(|| anyhow::anyhow!("no runs found under {}", runs_dir.display()))
}

pub async fn rollback(args: RollbackArgs) -> anyhow::Result<i32> {
    let runs_dir = args
        .runs_dir
        .or_else(|| std::env::var("HOH_RUNS_DIR").ok().map(PathBuf::from))
        .unwrap_or_else(|| PathBuf::from("runs"));
    let workspace = args
        .project
        .or_else(|| std::env::var("HOH_WORKSPACE").ok().map(PathBuf::from))
        .unwrap_or_else(|| PathBuf::from(".workspace/mario"));
    let config = load_with(&[])?;
    let excludes = HashExcludes::new(config.adapter.godot.cache_excludes.clone()).merged();

    let store = VersionStore::new(runs_dir.join(&args.run_id).join("versions"));
    store.rollback(&workspace, &excludes, &args.to)?;
    let hash = hash_tree(&workspace, &excludes)?;
    println!("{hash}");
    Ok(0)
}

// ---------------------------------------------------------------------------
// helpers
// ---------------------------------------------------------------------------

/// Helper shared by the subcommands that need a loaded config.
pub fn load_with(overrides: &[String]) -> anyhow::Result<HohConfig> {
    load_config(&config_specs(overrides))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn run_id_components_are_well_formed() {
        assert_eq!(format_utc(0), "19700101-000000");
        let stamp = format_utc(1_700_000_000);
        assert_eq!(stamp.len(), 15);
        assert_eq!(&stamp[8..9], "-");
    }

    #[test]
    fn unknown_adapter_is_rejected() {
        let config = load_config(&[]).unwrap();
        assert!(build_adapter_kind("nope", &config, false).is_err());
    }
}
