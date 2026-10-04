//! Subcommand implementations.  Kept separate from `cli.rs` so the clap
//! surface stays declarative and the `hoh` binary entry point stays tiny.

use std::path::{Path, PathBuf};
use std::sync::Arc;

use serde_json::{json, Value};

use crate::adapter::{DoctorItem, ProjectAdapter, TestAdapter};
use crate::cli::{
    config_specs, parse_ablation, DoctorArgs, InitArgs, RollbackArgs, RunArgs, SpecHashArgs,
    StatusArgs, SubmitArgs, ToolsArgs, ToolsCommand,
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
        .unwrap_or_else(|| PathBuf::from(".spec/bevy/PRD.md"));
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
            // DR-69 ①: this process is not the run.  The run publishes the game
            // route it registered (`HOH_GAME_ROUTE`), and without adopting it a
            // `running_game_*` tool can never be reached from here — which is
            // what `smoke-t9` measured (exit 5 with the game running).
            bridge::adopt_published_game_route(&channel, None);
            let reply = bridge::tools_call_with_reply(&channel, role, &call.tool, args).await?;
            // DR-78 ② (F-T11-1): a role that plays its **own** scene is starting
            // a game the runtime does not know about, so this process — not the
            // runtime battery — is the publisher of the route that game
            // announced.  `smoke-t11` measured the gap: `editor_play_scene`
            // answered pid 4784 while `runs/smoke-t11/game_endpoint.json` still
            // named the dead pid 33536, and every later `running_game_*` call from
            // that shell was refused.
            //
            // The publish happens **before** the reply is printed: a role told
            // "the scene is playing" would otherwise reach for
            // `running_game_*` with an unwritten route.  A failure is a hard
            // error, never a silent reuse of the old route, and the failing path
            // withdraws the route so the refusal a role meets later is DR-43's
            // explicit `game_endpoint_unavailable` — never the editor endpoint.
            if call.tool == bridge::GAME_START_TOOL {
                if let Some(announced) = reply.answered() {
                    let adapter = build_adapter(&config)?;
                    adapter
                        .publish_role_started_game_route(&channel, role, announced)
                        .await
                        .map_err(|error| {
                            HofError::External(format!(
                                "`{}` started a game whose route could not be published, so no \
                                 later `running_game_*` call could reach it and the previous route \
                                 must not stand in for it (DR-43): {error}",
                                call.tool
                            ))
                        })?;
                }
            }
            match &reply {
                bridge::ToolCallReply::Denied(payload) => println!("{payload}"),
                bridge::ToolCallReply::Answered(payload) => {
                    println!("{}", serde_json::to_string_pretty(payload)?)
                }
            }
            Ok(reply.exit_code())
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

    // 2. Model identity (C9/C10/C11, DR-14).
    match crate::config::assert_model_identity(&config.model) {
        Ok(()) => items.push(DoctorItem {
            name: "model.identity".to_string(),
            ok: true,
            detail: format!(
                "config `{}` -> wire `{}`",
                config.model_name(),
                config.wire_model_name()
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

    // 5b. DR-44: the engine binary and its version.  The version string is
    //     recorded **verbatim** and never asserted (C12: a version bump must not
    //     require a code change).  An adapter that drives no engine binary has
    //     nothing to report here.
    if let Some(binary) = adapter.engine_binary() {
        let mut env_config = mini_swe_agent::environments::LocalEnvironmentConfig::default();
        env_config.cwd = workspace.to_string_lossy().into_owned();
        env_config.timeout = crate::adapter::engine::PROBE_TIMEOUT_SECONDS;
        let environment = mini_swe_agent::environments::LocalEnvironment::new(env_config);
        items.extend(crate::adapter::engine::doctor_items(&environment, &binary).await);
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

/// DR-15: the minimal chat request must be authenticated (`Authorization:
/// Bearer <resolved api_key>`) and the **response** `model` field must equal
/// the configured `wire_model_name` (C9 double-lock).  The key is never echoed
/// into the detail text.
fn chat_probe(config: &HohConfig) -> DoctorItem {
    let url = format!(
        "{}/chat/completions",
        config.base_url().trim_end_matches('/')
    );
    let wire = config.wire_model_name();
    let Some(api_key) = config.resolved_api_key() else {
        // C11: a remote OpenAI-compatible endpoint is unusable without a key,
        // so this is a real failure — unlike `model.resident` (C12).
        return DoctorItem {
            name: "model.chat".to_string(),
            ok: false,
            detail: format!(
                "{url}: no api key resolved; set HOH_MODEL_API_KEY or OPENAI_API_KEY (C11)"
            ),
        };
    };
    let body = json!({
        "model": wire,
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 1
    });
    let agent = ureq::AgentBuilder::new()
        .timeout(std::time::Duration::from_secs(30))
        .build();
    match agent
        .post(&url)
        .set("Content-Type", "application/json")
        .set("Authorization", &format!("Bearer {api_key}"))
        .send_json(body)
    {
        Ok(response) => {
            let value: Value = response.into_json().unwrap_or(Value::Null);
            let model = value.get("model").and_then(Value::as_str).unwrap_or("");
            if model == wire {
                DoctorItem {
                    name: "model.chat".to_string(),
                    ok: true,
                    detail: format!("{url} answered with model `{model}`"),
                }
            } else {
                DoctorItem {
                    name: "model.chat".to_string(),
                    ok: false,
                    detail: format!("{url} answered with model `{model}` instead of `{wire}`"),
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

/// DR-15/C12: `model.resident` inspects LM Studio's `/api/v0/models`, which is
/// vendor specific.  It therefore only runs against a loopback endpoint; every
/// other case (remote host, missing API, unreachable endpoint) is reported as
/// `ok = true` with an explicit `skipped:` detail, so it can never block a run.
fn models_probe(config: &HohConfig) -> DoctorItem {
    let host = base_url_host(config.base_url());
    if !is_loopback_host(&host) {
        return DoctorItem {
            name: "model.resident".to_string(),
            ok: true,
            detail: format!(
                "skipped: host `{host}` is not loopback; `/api/v0/models` is LM Studio specific (C12)"
            ),
        };
    }

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
            // DR-15: the duplicate rule is derived from configuration, not from
            // a hard-coded vendor id: a loaded entry whose id equals the
            // `wire_model_name` with its vendor prefix stripped is a second,
            // VRAM-doubling instance (D6).  An unprefixed wire name has no
            // distinct bare form, so no duplicate check applies.
            match bare_model_name(config.wire_model_name()) {
                Some(bare) if loaded.iter().any(|id| id == bare) => DoctorItem {
                    name: "model.resident".to_string(),
                    ok: false,
                    detail: format!(
                        "a bare `{bare}` instance is loaded ({loaded:?}); unload it in LM Studio, \
                         it doubles VRAM (D6)"
                    ),
                },
                _ => DoctorItem {
                    name: "model.resident".to_string(),
                    ok: true,
                    detail: format!("loaded: {loaded:?}"),
                },
            }
        }
        Err(error) => DoctorItem {
            name: "model.resident".to_string(),
            ok: true,
            detail: format!("skipped: {url}: {error}"),
        },
    }
}

/// The host component of a base URL, lower-cased, without userinfo/port.
fn base_url_host(base_url: &str) -> String {
    let rest = base_url
        .split_once("://")
        .map(|(_, rest)| rest)
        .unwrap_or(base_url);
    let authority = rest
        .split(['/', '?', '#'])
        .next()
        .unwrap_or("")
        .rsplit('@')
        .next()
        .unwrap_or("");
    let host = if let Some(inner) = authority.strip_prefix('[') {
        inner.split_once(']').map(|(host, _)| host).unwrap_or(inner)
    } else {
        authority.split(':').next().unwrap_or("")
    };
    host.to_ascii_lowercase()
}

fn is_loopback_host(host: &str) -> bool {
    matches!(host, "127.0.0.1" | "localhost" | "::1")
}

/// `vendor/model` -> `Some("model")`; an unprefixed name -> `None`.
fn bare_model_name(wire_model_name: &str) -> Option<&str> {
    wire_model_name
        .rsplit_once('/')
        .map(|(_, bare)| bare)
        .filter(|bare| !bare.is_empty() && *bare != wire_model_name)
}

// ---------------------------------------------------------------------------
// init (DR-40)
// ---------------------------------------------------------------------------

/// DR-40: what `hoh init` promises about its dependencies.
pub const INIT_DETAIL: &str = "initialize ran; no MCP, no model endpoint and no key were required";

/// DR-40: prepare `A₀` — and nothing else.
///
/// The `--fresh-workspace` + doctor circular dependency is resolved here: this
/// path deliberately does **not** build a harness, does **not** create a tool
/// channel, and does **not** resolve an API key, so it works with the editor
/// closed and the model unreachable.  A workspace the adapter cannot initialize
/// is reported as an unavailable external dependency (exit 4, §8).
pub async fn init(args: InitArgs) -> anyhow::Result<i32> {
    let mut specs = config_specs(&args.config_spec);
    specs.push(format!("adapter.kind={}", args.adapter));
    if let Some(project) = &args.project {
        specs.push(format!("runtime.workspace={}", project.display()));
    }
    let config = load_config(&specs)?;
    let adapter = build_adapter_kind(&args.adapter, &config, args.force_init)?;
    let workspace = config.runtime.workspace.clone();

    let outcome = if args.fresh_workspace {
        crate::runtime::start_state::fresh_workspace(&workspace, &*adapter)
    } else {
        adapter.initialize(&workspace)
    };
    match outcome {
        Ok(()) => {
            println!(
                "init: A0 ready at {} ({}{})",
                workspace.display(),
                if args.fresh_workspace {
                    "workspace emptied, "
                } else {
                    ""
                },
                INIT_DETAIL
            );
            Ok(0)
        }
        Err(error) => {
            // §8: "the adapter is not available" is exit 4, not a harness error.
            Err(HofError::External(format!(
                "could not initialize {}: {error}",
                workspace.display()
            ))
            .into())
        }
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

/// Render the doctor table.  Kept separate from printing so the exact report
/// text is testable without touching the network (DR-6).
pub fn format_doctor(items: &[DoctorItem]) -> String {
    let mut text = String::new();
    for item in items {
        text.push_str(&format!(
            "[{}] {}: {}\n",
            if item.ok { "ok" } else { "FAIL" },
            item.name,
            item.detail
        ));
    }
    text
}

fn print_doctor(items: &[DoctorItem]) {
    print!("{}", format_doctor(items));
}

// ---------------------------------------------------------------------------
// run
// ---------------------------------------------------------------------------

fn build_adapter(config: &HohConfig) -> anyhow::Result<Box<dyn ProjectAdapter>> {
    build_adapter_kind(&config.adapter.kind, config, false)
}

fn build_adapter_kind(
    kind: &str,
    _config: &HohConfig,
    _force_init: bool,
) -> anyhow::Result<Box<dyn ProjectAdapter>> {
    match kind {
        "test" => Ok(Box::new(TestAdapter::new())),
        other => Err(HofError::Config(format!("unknown adapter `{other}` (expected test)")).into()),
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
    // DR-16: resolve the secret and put it into the HoH process environment
    // **before** any agent exists.  mini's `resolve_api_key` then picks it up
    // through its own fallback, so the key never enters the model JSON nor a
    // role's `LocalEnvironment` env map (mini serializes both into the
    // trajectory).
    let _ = crate::config::export_model_api_key(&config);
    let ablation = parse_ablation(&args.ablate)?;
    let adapter = build_adapter_kind(&args.adapter, &config, args.force_init)?;
    let workspace = config.runtime.workspace.clone();

    let spec = load_spec(&config.runtime.spec)?;
    let run_id = args.run_id.clone().unwrap_or_else(default_run_id);
    let run_dir = config.runtime.runs_dir.join(&run_id);
    if args.fresh_workspace && args.reset_workspace {
        return Err(HofError::Config(
            "--fresh-workspace and --reset-workspace are mutually exclusive".to_string(),
        )
        .into());
    }

    // DR-40: `--fresh-workspace` first, doctor second.  Emptying and rebuilding
    // `A₀` must be possible with the editor closed, so the doctor pre-check (which
    // requires 9877) can no longer stand in front of it.  A doctor failure keeps
    // the rebuilt `A₀`: it is *not* rolled back.
    let fresh_prepared = if args.fresh_workspace {
        crate::runtime::start_state::fresh_workspace(&workspace, &*adapter)?;
        true
    } else {
        false
    };

    // §8: the doctor pre-check is mandatory and must run before anything else.
    let items = doctor_checks(&config, &*adapter, &workspace).await?;
    print_doctor(&items);
    if !items.iter().all(|item| item.ok) {
        eprintln!(
            "hoh run: pre-flight checks failed; the run was not started{}",
            if fresh_prepared {
                " (the rebuilt A0 was kept)"
            } else {
                ""
            }
        );
        return Ok(4);
    }

    // DR-21: `--reset-workspace` needs this run's existing `A₀` snapshot, so an
    // existing run directory is expected for that mode only.
    if run_dir.exists() && !args.reset_workspace {
        return Err(HofError::Config(format!(
            "run directory {} already exists; pass --resume (not implemented in v1)",
            run_dir.display()
        ))
        .into());
    }

    // DR-21: prepare the starting point.  Both modes validate before they
    // touch anything, and both are restricted to the configured workspace.
    let start_state = if fresh_prepared {
        crate::runtime::start_state::StartState::fresh()
    } else if args.reset_workspace {
        let excludes = HashExcludes::new(adapter.cache_excludes()).merged();
        let version_id =
            crate::runtime::start_state::reset_workspace(&workspace, &run_dir, &excludes)?;
        crate::runtime::start_state::StartState::reset(version_id)
    } else {
        crate::runtime::start_state::StartState::as_is()
    };

    let harness = crate::harness::MiniHarness::new();
    let tools: Arc<dyn ToolChannel> = if args.adapter == "test" {
        Arc::new(crate::tools::ShellOnlyChannel)
    } else {
        Arc::new(bridge::channel_for(&config))
    };
    // DR-73 ③(b): hand the round directory to the **process exit** record before
    // any role runs, so the third reading (the code the process really returns)
    // lands beside the two `finalize_run` writes.  Exported, not passed: the exit
    // code is decided at the process boundary, and `ExitCode` carries no number.
    std::env::set_var(RUN_DIR_ENV, &run_dir);
    let orchestrator = Orchestrator {
        harness: Box::new(harness),
        adapter,
        tools,
        cfg: config,
        ablation,
        force_init: args.force_init,
        start_state,
    };

    // DR-67 (DEF-2): the failed path must **persist what the process reports**.
    //
    // DR-66's `?` propagated the round's error and skipped `finalize_run`
    // entirely, so `runs/<id>/exit_code` and `meta.json.exit_code` were never
    // written for exactly the rounds that failed — the DR-27 contract ("a
    // launcher reads these two files") only held for successful rounds.
    //
    // `cli_impl::run` itself cannot be exercised offline: the mandatory doctor
    // pre-check performs a model/chat probe (`doctor_checks` items 3 and 4), and
    // this batch may not touch the network.  Forcing the finalisation into the
    // same function as the round, as it was, leaves it provable only by reading
    // the source — so the round runs in [`run_round_in`] and the finalisation
    // lives here, on the caller's error path, where a test can drive it with the
    // real `anyhow::Error`.  Every real failure of `run_loop::run` reaches this
    // branch, because `run_loop` creates the run directory before any role runs.
    // DR-69 (DR-67 DEF-A): the branch is not written here any more -- it lives
    // in [`run_round_and_finalize`], where an offline test can execute it.  The
    // defect was that the *only* caller of `failed_run_summary` + `finalize_run`
    // was this function, whose mandatory doctor pre-check needs the model
    // endpoint, so no test could reach it.
    let summary = run_round_and_finalize(orchestrator, &spec, &run_id, &run_dir).await?;
    println!(
        "run {} finished: {} iteration(s), final version {:?}, total tokens {:?}",
        summary.run_id,
        summary.iterations_completed,
        summary.final_version_id,
        summary.total_usage.total_tokens
    );
    // DR-39: one unmistakable line, so "the loop was green" can never be read as
    // "the product is done".
    println!("{}", format_prd_coverage_line(&summary.prd_coverage));
    // DR-27: 6 = the loop completed but the frozen artifact is not launchable.
    finalize_run(&run_dir, &summary)
}

/// DR-39: the end-of-run summary line.  It states the two axes explicitly
/// because they disagree exactly when it matters: `smoke-t5` finished with
/// `gate ok` and `0/17` verified.
pub fn format_prd_coverage_line(coverage: &crate::model::PrdCoverage) -> String {
    if coverage.total_is_known() {
        format!(
            "prd coverage: {}/{} verified (harness/gate describe the runtime contract, not the \
             product)",
            coverage.verified,
            coverage.total()
        )
    } else {
        format!(
            "prd coverage: {}/{} verified (total=derived from the Tester's claims; harness/gate \
             describe the runtime contract, not the product)",
            coverage.verified,
            coverage.total()
        )
    }
}

/// DR-27: the exit code of a completed run, derived from the artifact gate.
///
/// `0` means "the loop completed **and** the artifact is usable"; `6` means the
/// loop completed but `artifact_gate.launchable == false`.  A gate that never
/// applied (an adapter without gate steps) cannot produce `6`.
///
/// DR-66 ④: this function judges the **artifact** only, and it is deliberately
/// left as it was so its meaning stays narrow and its historical callers keep
/// their exact semantics.  The round's own verdict goes through
/// [`run_exit_code_for`], which uses it for the artifact axis and adds the
/// contract axis — otherwise a round the runtime itself failed (the Developer
/// produced no engineering write) would still be launched as success.
pub fn run_exit_code(gate: &crate::model::ArtifactGate) -> i32 {
    if gate.applicable && !gate.launchable {
        6
    } else {
        0
    }
}

/// DR-67 (DEF-2): the round half of [`run`], split out so the **failure
/// finalisation** can be driven by a test.
///
/// This function only runs the loop; it decides nothing about exit codes.  The
/// caller turns an `Err` into a persisted verdict, which is the behaviour the
/// independent acceptance found missing: `run_loop::run` returns `Err` for the
/// E1-class failure, so a finalisation living *inside* the same function as the
/// round is skipped precisely when it is needed.
pub async fn run_round_in(
    orchestrator: run_loop::Orchestrator,
    spec: &crate::model::Spec,
    run_id: &str,
) -> anyhow::Result<run_loop::RunSummary> {
    run_loop::run(&orchestrator, spec, run_id).await
}

/// DR-69 (DR-67 DEF-A): the round **and** its failure finalisation, in one
/// callable function.
///
/// DR-67 made the persistence correct but left its single call site
/// (`cli_impl::run`'s `match`) with no executable coverage: that function
/// performs the mandatory doctor probe, which needs the model endpoint, so an
/// offline test can never reach the branch that persists a failed round's
/// verdict -- and deleting the branch would have reopened DEF-2 silently.  The
/// branch lives here now, and `tests/e1_increment.rs` drives it with a real
/// round that really fails.
///
/// Best effort on the write: a filesystem failure while recording the verdict
/// must never replace the round's own error.  Idempotent, so re-running a failed
/// round rewrites the same numbers.
pub async fn run_round_and_finalize(
    orchestrator: run_loop::Orchestrator,
    spec: &crate::model::Spec,
    run_id: &str,
    run_dir: &Path,
) -> anyhow::Result<run_loop::RunSummary> {
    match run_round_in(orchestrator, spec, run_id).await {
        Ok(summary) => Ok(summary),
        Err(error) => {
            let failed = run_loop::failed_run_summary(run_id, &error);
            let _ = finalize_run(run_dir, &failed);
            Err(error)
        }
    }
}

/// DR-66 ④: the **round's** exit code.
///
/// `2` — the contract-violation class (`HofError::Contract`, `src/errors.rs`) —
/// when the runtime did not complete the round successfully, which is the state
/// a zero-engineering-write Developer leaves behind; otherwise the artifact
/// verdict of DR-27 (`0` usable, `6` unlaunchable).  This is the fix for the
/// measured false green: `smoke-t7`'s iteration ended with `ok = true`,
/// `artifact_gate.launchable = true` and `exit_code = 0` while the Developer had
/// produced no increment at all.
///
/// DR-67 (DEF-2): the order is now (1) the failure code carried by the summary,
/// (2) the `!ok` contract class, (3) the artifact gate.  Branch (1) is the one
/// the production failure path uses, so this function is a single decision point
/// for "what code does this run end with" instead of a partial view of a
/// hand-built object.
pub fn run_exit_code_for(summary: &run_loop::RunSummary) -> i32 {
    if let Some(code) = summary.failure_exit_code {
        // The real error's own class, so the persisted number cannot drift away
        // from `hoh::errors::exit_code_of`'s answer for the same failure.
        return code;
    }
    if !summary.ok {
        // The same class as every other contract violation, derived from the
        // violation itself so the number can never drift away from it.
        crate::errors::HofError::contract(crate::model::ContractViolation::NoEngineeringWrite)
            .exit_code()
    } else {
        run_exit_code(&summary.artifact_gate)
    }
}

/// DR-73 ③(b) / D280(b): the name of the round-directory artifact that carries
/// the **process** exit code.
///
/// Until this batch the round's exit code was readable in two places only —
/// `runs/<id>/exit_code` (the bare number) and `meta.json.exit_code` — and the
/// third reading ("the process really exited 0") lived in whatever wrapper script
/// launched `hoh`.  `TASK-SMOKE-T10-ACCEPTANCE.md` T10A-4 shows what that costs:
/// the wrapper's `ROUND_EXIT=0` line was never frozen, so a third of the claim
/// could not be checked from the artifacts at all.  This file is written from the
/// **value the process is about to return**, so all three readings are
/// artifact-backed.
pub const PROCESS_EXIT_CODE_FILE: &str = "process_exit_code";

/// DR-73 ③(b): the environment variable through which a round's directory is
/// handed to the **process exit** record.
///
/// `cli_impl::run` sets it once the directory is known (before any role runs), and
/// the process entry point reads it after the round returned, so the reading is
/// recorded where the code is decided and against the directory the round really
/// used.  The name follows the harness's own `HOH_*` family; it is registered in
/// [`crate::runtime::secrets::HARNESS_ENV_VARS`], so its value is redacted
/// anywhere it could reach an artifact.
pub const RUN_DIR_ENV: &str = "HOH_RUN_DIR";

/// DR-73 ③(b): persist the process exit code for the round named by
/// [`RUN_DIR_ENV`], if this process is a round at all.
///
/// Best effort: a missing variable (every command except `run`), an empty one, or
/// a filesystem failure all leave the code untouched.
///
/// **What is recorded is the round's own artifact-backed verdict, not a second
/// computation.**  `finalize_run` has already turned the summary into the single
/// decision point `run_exit_code_for(summary)` and persisted it as
/// `runs/<id>/exit_code`; this reads that number back and mirrors it, so the two
/// artifacts cannot drift and the process code (which `main_entry` derives from
/// the same `dispatch` result) is the third reading of one number.  The
/// alternative — recomputing from a summary that is no longer in scope at the
/// process boundary — is exactly the "two computations that can disagree" shape
/// this batch exists to remove.  A round that never reached `finalize_run` has no
/// `exit_code` file and nothing to record, which is honest: there is no third
/// reading to back up.
pub fn record_process_exit_code_from_env() {
    let Ok(run_dir) = std::env::var(RUN_DIR_ENV) else {
        return;
    };
    if run_dir.trim().is_empty() {
        return;
    }
    let path = Path::new(&run_dir).join("exit_code");
    if let Ok(raw) = std::fs::read_to_string(&path) {
        if let Ok(code) = raw.trim().parse::<i32>() {
            let _ = write_process_exit_code(Path::new(&run_dir), code);
        }
    }
}

/// DR-73 ③(b): the process exit code one completed round ends with.
///
/// This is the single computation the process entry point and the persisted
/// artifact both go through: [`finalize_run`] stores `run_exit_code_for(summary)`
/// as the round's own verdict, and `src/main.rs` hands the same function's answer
/// to [`write_process_exit_code`] before returning it.  A test can therefore
/// check the two artifacts against each other without a live round.
pub fn process_exit_code_for(summary: &run_loop::RunSummary) -> i32 {
    run_exit_code_for(summary)
}

/// DR-73 ③(b): persist the process exit code itself.
///
/// Best effort on the write, like the failure finalisation in
/// [`run_round_and_finalize`]: failing to record the reading must never change
/// the exit code the process returns.  The value is written as the same
/// `<code>\n` byte shape `runs/<id>/exit_code` uses, so the three readings can be
/// compared byte for byte.
pub fn write_process_exit_code(run_dir: &Path, code: i32) -> std::io::Result<()> {
    std::fs::write(run_dir.join(PROCESS_EXIT_CODE_FILE), format!("{code}\n"))
}

/// DR-27: persist the run's exit code twice — as a bare number in
/// `runs/<id>/exit_code` (launchers cannot rely on `Start-Process -PassThru`
/// under redirection) and as `meta.json.exit_code`.  DR-73 ③(b) adds the third
/// reading, the process code itself, in [`write_process_exit_code`].
pub fn finalize_run(run_dir: &Path, summary: &run_loop::RunSummary) -> anyhow::Result<i32> {
    let code = run_exit_code_for(summary);
    std::fs::write(run_dir.join("exit_code"), format!("{code}\n"))?;

    let meta_path = run_dir.join("meta.json");
    if let Ok(raw) = std::fs::read_to_string(&meta_path) {
        if let Ok(mut meta) = serde_json::from_str::<Value>(&raw) {
            if let Some(object) = meta.as_object_mut() {
                object.insert("exit_code".to_string(), json!(code));
                if let Ok(gate) = serde_json::to_value(&summary.artifact_gate) {
                    object.insert("artifact_gate".to_string(), gate);
                }
                let mut serialized = serde_json::to_string_pretty(&meta)?;
                if !serialized.ends_with('\n') {
                    serialized.push('\n');
                }
                std::fs::write(&meta_path, serialized)?;
            }
        }
    }
    Ok(code)
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
    if !runs_dir.is_dir() {
        return Err(HofError::RunNotFound(format!(
            "the runs directory {} does not exist",
            runs_dir.display()
        ))
        .into());
    }
    let run_id = match args.run_id {
        Some(run_id) => run_id,
        None => latest_run_id(&runs_dir)?,
    };
    let run_dir = runs_dir.join(&run_id);
    if !run_dir.is_dir() {
        return Err(HofError::RunNotFound(format!("no such run: {}", run_dir.display())).into());
    }

    // DR-8: an iteration whose usage is unknown must never be summed as zero.
    let mut known_tokens: u64 = 0;
    let mut known_entries: usize = 0;
    let mut unknown_iterations: usize = 0;
    println!("# run {run_id}");
    let mut iterations: Vec<PathBuf> = std::fs::read_dir(&run_dir)
        .map_err(|error| {
            HofError::RunNotFound(format!("could not read {}: {error}", run_dir.display()))
        })?
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
            .and_then(|raw| serde_json::from_str::<Value>(&raw).ok())
            .map(|value| crate::runtime::usage::usage_summary_of(&value))
            .unwrap_or_default();
        let mut iteration_unknown = false;
        for entry in &usage {
            let known = entry
                .get("usage_known")
                .and_then(Value::as_bool)
                .unwrap_or(true);
            match entry.get("total_tokens").and_then(Value::as_u64) {
                Some(tokens) if known => {
                    known_tokens += tokens;
                    known_entries += 1;
                }
                _ => iteration_unknown = true,
            }
        }
        if iteration_unknown {
            unknown_iterations += 1;
        }
        // DR-27: "did the loop complete?" (harness) and "is the artifact
        // usable?" (gate) are two different columns, never one green `ok`.
        let harness = if result.get("ok").and_then(Value::as_bool).unwrap_or(false) {
            "ok"
        } else {
            "fail"
        };
        // DR-68 ⑦: applicability is read first.  A result whose gate was never
        // evaluated (`applicable = false`) answered nothing, so it is `unknown`
        // — never `ok`.  `smoke-t8`'s failed round persisted exactly that shape
        // (`applicable: false, launchable: true`) and this column printed `ok`.
        let gate = match (
            result
                .pointer("/artifact_gate/applicable")
                .and_then(Value::as_bool),
            result
                .pointer("/artifact_gate/launchable")
                .and_then(Value::as_bool),
        ) {
            (Some(false), _) => "unknown",
            (_, Some(true)) => "ok",
            (_, Some(false)) => "fail",
            _ => "unknown",
        };
        // DR-39: `gate ok` and `prd=…` are different claims.  The PRD column is
        // derived from the Tester's own `E_t`, never judged by the runtime.
        let coverage: crate::model::PrdCoverage = result
            .get("prd_coverage")
            .and_then(|value| serde_json::from_value(value.clone()).ok())
            .unwrap_or_default();
        let prd = coverage.label();
        println!(
            "{:<8} harness={:<5} gate={:<8} {} ok={:<5} reason={:<20} candidate={} roles={}",
            iter_dir
                .file_name()
                .map(|name| name.to_string_lossy().into_owned())
                .unwrap_or_default(),
            harness,
            gate,
            prd,
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
    if unknown_iterations == 0 {
        println!("total tokens: {known_tokens}");
    } else {
        let base = if known_entries == 0 {
            "unknown".to_string()
        } else {
            known_tokens.to_string()
        };
        println!("total tokens: {base} ({unknown_iterations} iteration unknown)");
    }
    Ok(0)
}

fn latest_run_id(runs_dir: &Path) -> anyhow::Result<String> {
    let mut ids: Vec<String> = std::fs::read_dir(runs_dir)
        .map_err(|error| {
            HofError::RunNotFound(format!("could not read {}: {error}", runs_dir.display()))
        })?
        .filter_map(|entry| entry.ok())
        .filter(|entry| entry.path().is_dir())
        .map(|entry| entry.file_name().to_string_lossy().into_owned())
        .collect();
    ids.sort();
    ids.pop().ok_or_else(|| {
        HofError::RunNotFound(format!("no runs found under {}", runs_dir.display())).into()
    })
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
    // The rollback command has no project adapter to ask (it runs against the
    // run's own snapshots), so the exclusion set is the runtime's always-excluded
    // pair (`.hoh`, `.git`) and nothing else: an unconfigured cache prefix must
    // never silently hide a real artifact from the rollback.  The configuration
    // is still loaded, so a broken `hoh.yaml` is reported here as everywhere else.
    let _ = load_with(&[])?;
    let excludes = HashExcludes::default().merged();

    let store = VersionStore::new(runs_dir.join(&args.run_id).join("versions"));
    if !store.root.join(&args.to).is_dir() {
        // DR-8: a missing version is a usage error (exit 2), not a harness
        // failure (exit 5).
        return Err(HofError::VersionNotFound(format!(
            "version `{}` has no snapshot under {}",
            args.to,
            store.root.display()
        ))
        .into());
    }
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

    #[test]
    fn base_url_host_parsing_is_generic() {
        assert_eq!(base_url_host("http://127.0.0.1:1234/v1"), "127.0.0.1");
        assert_eq!(base_url_host("http://localhost/v1"), "localhost");
        assert_eq!(base_url_host("http://[::1]:1234/v1"), "::1");
        assert_eq!(
            base_url_host("https://user:pass@Remote.Example.COM:8443/v1"),
            "remote.example.com"
        );
        assert_eq!(base_url_host("https://api.example.com"), "api.example.com");
        assert!(is_loopback_host("127.0.0.1") && is_loopback_host("localhost"));
        assert!(!is_loopback_host("192.168.1.10"));
        assert!(!is_loopback_host("remote.invalid"));
    }

    #[test]
    fn bare_model_name_strips_only_a_vendor_prefix() {
        assert_eq!(bare_model_name("vendor/some-model"), Some("some-model"));
        assert_eq!(bare_model_name("deepseek-v4.1-flash"), None);
        assert_eq!(bare_model_name("vendor/"), None);
    }
}
