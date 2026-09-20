//! Shared offline test doubles: a scripted harness, a scripted adapter and a
//! recording tool channel.  Everything here is deterministic and network-free.
#![allow(dead_code)]

use std::collections::BTreeMap;
use std::path::{Path, PathBuf};
use std::sync::{Arc, Mutex};

use hof_rs::adapter::{DoctorItem, ProjectAdapter};
use hof_rs::config::{AgentLimits, HohConfig};
use hof_rs::harness::Harness;
use hof_rs::model::{ExecKind, ExecRecord, Role, Usage};
use hof_rs::runtime::role::{RoleInvocation, RoleOutcome};
use hof_rs::tools::{ToolChannel, ToolResult};
use serde_json::Value;

// ---------------------------------------------------------------------------
// Scripted harness
// ---------------------------------------------------------------------------

/// Token numbers used to synthesize a trajectory usage block.
#[derive(Clone, Debug)]
pub struct UsageFixture {
    pub prompt: u64,
    pub completion: u64,
}

impl UsageFixture {
    pub fn new(prompt: u64, completion: u64) -> Self {
        Self { prompt, completion }
    }
}

#[derive(Clone, Debug)]
pub struct FakeStep {
    pub role: Role,
    /// `(path relative to the invocation cwd, content)`.
    pub writes: Vec<(String, String)>,
    pub exit_status: String,
    pub submission: String,
    pub usage: Option<UsageFixture>,
    /// Escape hatch used to build the "the role wrote outside its view"
    /// counter-examples (R2/R4).
    pub write_outside_view: Option<(PathBuf, String)>,
    pub sleep_ms: u64,
}

impl FakeStep {
    pub fn new(role: Role) -> Self {
        Self {
            role,
            writes: Vec::new(),
            exit_status: "Submitted".to_string(),
            submission: "done".to_string(),
            usage: Some(UsageFixture::new(10, 5)),
            write_outside_view: None,
            sleep_ms: 0,
        }
    }

    pub fn writing(mut self, rel: &str, content: &str) -> Self {
        self.writes.push((rel.to_string(), content.to_string()));
        self
    }

    pub fn outside(mut self, path: PathBuf, content: &str) -> Self {
        self.write_outside_view = Some((path, content.to_string()));
        self
    }

    pub fn without_usage(mut self) -> Self {
        self.usage = None;
        self
    }
}

/// Full record of one `Harness::invoke` call (R8 compares these byte-for-byte).
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct InvocationRecord {
    pub role: Role,
    pub iteration: u32,
    pub cwd: PathBuf,
    pub env: BTreeMap<String, String>,
    pub system_prompt: String,
    pub task_prompt: String,
    pub retry_context: Option<String>,
    pub model: String,
    pub limits: String,
    /// Sorted `relative path -> content` of the invocation cwd.
    pub files: BTreeMap<String, String>,
}

impl InvocationRecord {
    /// Everything except the cwd's file contents (used by the ablation tests to
    /// prove that only the intended input changed).
    pub fn without_files(&self) -> InvocationRecord {
        InvocationRecord {
            files: BTreeMap::new(),
            ..self.clone()
        }
    }
}

#[derive(Clone, Debug)]
pub struct FakeHarness {
    pub script: Arc<Vec<FakeStep>>,
    pub log: Arc<Mutex<Vec<InvocationRecord>>>,
    cursor: Arc<Mutex<usize>>,
}

impl FakeHarness {
    pub fn new(script: Vec<FakeStep>) -> Self {
        Self {
            script: Arc::new(script),
            log: Arc::new(Mutex::new(Vec::new())),
            cursor: Arc::new(Mutex::new(0)),
        }
    }

    pub fn records(&self) -> Vec<InvocationRecord> {
        self.log.lock().expect("log lock").clone()
    }

    pub fn roles(&self) -> Vec<Role> {
        self.records()
            .into_iter()
            .map(|record| record.role)
            .collect()
    }
}

fn read_files(root: &Path) -> BTreeMap<String, String> {
    let mut files = BTreeMap::new();
    if !root.exists() {
        return files;
    }
    for entry in walkdir::WalkDir::new(root).follow_links(false) {
        let Ok(entry) = entry else { continue };
        if !entry.file_type().is_file() {
            continue;
        }
        let rel = entry
            .path()
            .strip_prefix(root)
            .unwrap_or(entry.path())
            .components()
            .map(|component| component.as_os_str().to_string_lossy().into_owned())
            .collect::<Vec<_>>()
            .join("/");
        if rel.starts_with(".git/") {
            continue;
        }
        let content = std::fs::read(entry.path()).unwrap_or_default();
        files.insert(rel, String::from_utf8_lossy(&content).into_owned());
    }
    files
}

fn trajectory_json(usage: Option<&UsageFixture>) -> String {
    let usage_block = match usage {
        Some(fixture) => serde_json::json!({
            "prompt_tokens": fixture.prompt,
            "completion_tokens": fixture.completion,
            "total_tokens": fixture.prompt + fixture.completion,
            "prompt_cache_hit_tokens": 1,
            "prompt_cache_miss_tokens": 2
        }),
        None => Value::Null,
    };
    let mut response = serde_json::json!({
        "id": "chatcmpl-fake",
        "object": "chat.completion",
        "created": 0,
        "model": "qwen/qwen3.8-27b",
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": ""},
            "finish_reason": "tool_calls"
        }],
        "content": ""
    });
    if !usage_block.is_null() {
        response["usage"] = usage_block;
    }
    serde_json::json!({
        "info": {"exit_status": "Submitted", "submission": "done"},
        "messages": [
            {"role": "system", "content": "sys"},
            {"role": "assistant", "content": "", "extra": {"actions": [], "response": response}},
            {"role": "exit", "content": "done"}
        ],
        "trajectory_format": "mini-swe-agent-1.1"
    })
    .to_string()
}

#[async_trait::async_trait]
impl Harness for FakeHarness {
    async fn invoke(&self, inv: &RoleInvocation) -> anyhow::Result<RoleOutcome> {
        let record = InvocationRecord {
            role: inv.role,
            iteration: inv.iteration,
            cwd: inv.cwd.clone(),
            env: inv.env.clone(),
            system_prompt: inv.system_prompt.clone(),
            task_prompt: inv.task_prompt.clone(),
            retry_context: inv.retry_context.clone(),
            model: serde_json::to_string(&inv.model).unwrap_or_default(),
            limits: format!("{:?}", inv.limits),
            files: read_files(&inv.cwd),
        };
        self.log.lock().expect("log lock").push(record);

        let index = {
            let mut cursor = self.cursor.lock().expect("cursor lock");
            let index = *cursor;
            *cursor += 1;
            index
        };
        let step = self
            .script
            .get(index)
            .unwrap_or_else(|| panic!("FakeHarness ran out of steps at call #{index}"))
            .clone();
        if step.role != inv.role {
            let actual: Vec<&str> = self.records().iter().map(|r| r.role.as_str()).collect();
            panic!(
                "FakeHarness step #{index} expects {:?} but the runtime asked for {:?}; actual \
                 sequence so far: {:?}",
                step.role, inv.role, actual
            );
        }

        for (rel, content) in &step.writes {
            let path = inv.cwd.join(rel.replace('\\', "/"));
            if let Some(parent) = path.parent() {
                std::fs::create_dir_all(parent)?;
            }
            std::fs::write(&path, content)?;
        }
        if let Some((path, content)) = &step.write_outside_view {
            if let Some(parent) = path.parent() {
                std::fs::create_dir_all(parent)?;
            }
            std::fs::write(path, content)?;
        }
        if step.sleep_ms > 0 {
            tokio::time::sleep(std::time::Duration::from_millis(step.sleep_ms)).await;
        }

        if let Some(parent) = inv.trajectory_path.parent() {
            std::fs::create_dir_all(parent)?;
        }
        std::fs::write(&inv.trajectory_path, trajectory_json(step.usage.as_ref()))?;

        let usage = match &step.usage {
            Some(fixture) => Usage {
                role: inv.role.as_str().to_string(),
                iteration: inv.iteration,
                calls: 1,
                prompt_tokens: Some(fixture.prompt),
                completion_tokens: Some(fixture.completion),
                total_tokens: Some(fixture.prompt + fixture.completion),
                cache_hit_tokens: Some(1),
                cache_miss_tokens: Some(2),
                usage_known: true,
            },
            None => Usage {
                role: inv.role.as_str().to_string(),
                iteration: inv.iteration,
                usage_known: false,
                ..Usage::default()
            },
        };

        Ok(RoleOutcome {
            role: inv.role,
            iteration: inv.iteration,
            attempts: 1,
            exit_status: step.exit_status.clone(),
            submission: step.submission.clone(),
            trajectory_path: inv.trajectory_path.clone(),
            usage,
            duration_ms: step.sleep_ms,
        })
    }
}

// ---------------------------------------------------------------------------
// Scripted adapter
// ---------------------------------------------------------------------------

#[derive(Debug, Default)]
pub struct FakeAdapter {
    pub build_records: Vec<ExecRecord>,
    /// `(workspace, relative path, content)` written during `build_check` to
    /// simulate editor-side changes to the real project (DR-1: these are part
    /// of `A_t`, not drift).
    pub drift: Option<(PathBuf, String, String)>,
    /// `(workspace, relative path, content)` written from `evidence_playbook`,
    /// which the runtime calls *after* `A_t` was frozen: this is the only
    /// deterministic way to exercise the `WorkspaceDriftBeforeQa` safety net.
    pub drift_after_freeze: Option<(PathBuf, String, String)>,
    pub excludes: Vec<String>,
}

impl FakeAdapter {
    pub fn new() -> Self {
        Self {
            build_records: vec![fixed_build_record()],
            drift: None,
            drift_after_freeze: None,
            excludes: vec!["cache".to_string()],
        }
    }

    pub fn with_drift(mut self, workspace: PathBuf, rel: &str, content: &str) -> Self {
        self.drift = Some((workspace, rel.to_string(), content.to_string()));
        self
    }

    pub fn with_post_freeze_drift(mut self, workspace: PathBuf, rel: &str, content: &str) -> Self {
        self.drift_after_freeze = Some((workspace, rel.to_string(), content.to_string()));
        self
    }
}

pub fn fixed_build_record() -> ExecRecord {
    ExecRecord {
        kind: ExecKind::Build,
        path: Some(".hoh/deterministic/build.json".to_string()),
        observation: "fake adapter: build check ok".to_string(),
        candidate_id: String::new(),
    }
}

#[async_trait::async_trait]
impl ProjectAdapter for FakeAdapter {
    fn initialize(&self, workspace: &Path) -> anyhow::Result<()> {
        std::fs::create_dir_all(workspace)?;
        Ok(())
    }

    fn cache_excludes(&self) -> Vec<String> {
        self.excludes.clone()
    }

    async fn build_check(
        &self,
        workspace: &Path,
        _tools: &dyn ToolChannel,
    ) -> anyhow::Result<Vec<ExecRecord>> {
        if let Some((workspace, rel, content)) = &self.drift {
            let target = workspace.join(rel);
            if let Some(parent) = target.parent() {
                std::fs::create_dir_all(parent)?;
            }
            std::fs::write(&target, content)?;
        }
        // DR-1: the deterministic stage writes into the real workspace; the
        // runtime copies these records into the frozen candidate view.
        let dir = workspace.join(".hoh/deterministic");
        std::fs::create_dir_all(&dir)?;
        std::fs::write(
            dir.join("build.json"),
            serde_json::to_string_pretty(&self.build_records[0])?,
        )?;
        Ok(self.build_records.clone())
    }

    fn evidence_playbook(&self) -> String {
        // Called by the runtime *after* the freeze: the deterministic hook for
        // the pre-QA drift safety net.
        if let Some((workspace, rel, content)) = &self.drift_after_freeze {
            let target = workspace.join(rel);
            if let Some(parent) = target.parent() {
                std::fs::create_dir_all(parent).expect("drift parent");
            }
            std::fs::write(&target, content).expect("drift write");
        }
        "## Evidence playbook (fake)\n".to_string()
    }

    fn tool_policy(&self, _role: Role) -> Vec<String> {
        vec!["get_editor_errors".to_string()]
    }

    fn doctor(&self, _workspace: &Path) -> anyhow::Result<Vec<DoctorItem>> {
        Ok(vec![DoctorItem {
            name: "fake".to_string(),
            ok: true,
            detail: "ok".to_string(),
        }])
    }
}

// ---------------------------------------------------------------------------
// Recording tool channel
// ---------------------------------------------------------------------------

#[derive(Debug, Default)]
pub struct FakeToolChannel {
    pub calls: Mutex<Vec<(Role, String, Value)>>,
}

impl FakeToolChannel {
    pub fn new() -> Self {
        Self::default()
    }
}

#[async_trait::async_trait]
impl ToolChannel for FakeToolChannel {
    fn allowed(&self, role: Role, tool: &str) -> bool {
        hof_rs::runtime::policy::tool_allowed(role, tool)
    }

    fn index_markdown(&self, role: Role) -> String {
        format!("# Tools for {}\n\n- get_editor_errors\n", role.as_str())
    }

    async fn call(&self, role: Role, tool: &str, args: Value) -> anyhow::Result<ToolResult> {
        self.calls
            .lock()
            .expect("call lock")
            .push((role, tool.to_string(), args.clone()));
        Ok(ToolResult {
            ok: true,
            payload: serde_json::json!({"tool": tool, "args": args, "role": role.as_str()}),
        })
    }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

pub fn test_config(root: &Path, iterations: u32) -> HohConfig {
    let mut config = hof_rs::config::load_config(&[]).expect("config");
    config.runtime.iterations = iterations;
    config.runtime.workspace = root.join("workspace");
    config.runtime.runs_dir = root.join("runs");
    config.runtime.max_schema_retries = 2;
    config
}

pub fn limits() -> AgentLimits {
    AgentLimits::default()
}

/// The public specification text used by the offline scenarios.
pub const SPEC_TEXT: &str =
    "# Spec\n\nA Mario-like 2D platformer. The player must move and jump.\n";

pub fn write_spec(root: &Path) -> hof_rs::model::Spec {
    let path = root.join("spec.md");
    write(&path, SPEC_TEXT);
    hof_rs::config::load_spec(&path).expect("spec")
}

/// Run one complete offline scenario: `FakeHarness` + `FakeAdapter` +
/// recording tool channel, no network, no Godot, no LM Studio.
pub async fn run_scenario(
    root: &Path,
    iterations: u32,
    script: Vec<FakeStep>,
    ablation: hof_rs::model::Ablation,
    adapter: FakeAdapter,
) -> (
    anyhow::Result<hof_rs::runtime::run_loop::RunSummary>,
    Vec<InvocationRecord>,
) {
    run_scenario_inner(root, iterations, script, ablation, adapter, Vec::new()).await
}

/// Same scenario with DR-3 `runtime.private_excludes` configured.
pub async fn run_scenario_with_private_excludes(
    root: &Path,
    iterations: u32,
    script: Vec<FakeStep>,
    ablation: hof_rs::model::Ablation,
    adapter: FakeAdapter,
    private_excludes: Vec<String>,
) -> (
    anyhow::Result<hof_rs::runtime::run_loop::RunSummary>,
    Vec<InvocationRecord>,
) {
    run_scenario_inner(
        root,
        iterations,
        script,
        ablation,
        adapter,
        private_excludes,
    )
    .await
}

async fn run_scenario_inner(
    root: &Path,
    iterations: u32,
    script: Vec<FakeStep>,
    ablation: hof_rs::model::Ablation,
    adapter: FakeAdapter,
    private_excludes: Vec<String>,
) -> (
    anyhow::Result<hof_rs::runtime::run_loop::RunSummary>,
    Vec<InvocationRecord>,
) {
    let mut cfg = test_config(root, iterations);
    cfg.runtime.spec = root.join("spec.md");
    cfg.runtime.private_excludes = private_excludes;
    let spec = write_spec(root);
    let harness = FakeHarness::new(script);
    let observer = harness.clone();
    let orchestrator = hof_rs::runtime::run_loop::Orchestrator {
        harness: Box::new(harness),
        adapter: Box::new(adapter),
        tools: Arc::new(FakeToolChannel::new()),
        cfg,
        ablation,
        force_init: true,
    };
    let result = hof_rs::runtime::run_loop::run(&orchestrator, &spec, "run-1").await;
    (result, observer.records())
}

/// A one-iteration script for the common case.
pub fn happy_script() -> Vec<FakeStep> {
    vec![
        FakeStep::new(Role::Planner).writing(".hoh/plan.md", OK_PLAN),
        FakeStep::new(Role::Developer).writing("project.godot", "config_version=5\n"),
        FakeStep::new(Role::Tester)
            .writing(".hoh/evidence/move.json", "{\"moved\":true}\n")
            .writing(".hoh/evidence.json", &ok_evidence(1, "")),
    ]
}

/// Minimal `RoleInvocation` for gate-level tests.
pub fn role_invocation(
    cwd: &Path,
    role: Role,
    iteration: u32,
    trajectory: &Path,
    model: Value,
) -> RoleInvocation {
    RoleInvocation {
        role,
        iteration,
        system_prompt: format!("system prompt for {}", role.as_str()),
        task_prompt: format!("task prompt for {}", role.as_str()),
        cwd: cwd.to_path_buf(),
        env: BTreeMap::new(),
        limits: limits(),
        model,
        trajectory_path: trajectory.to_path_buf(),
        retry_context: None,
    }
}

pub fn write(path: &Path, content: &str) {
    if let Some(parent) = path.parent() {
        std::fs::create_dir_all(parent).expect("mkdir");
    }
    std::fs::write(path, content).expect("write");
}

pub fn read(path: &Path) -> String {
    std::fs::read_to_string(path).expect("read")
}

pub const OK_PLAN: &str = "## Project Planner Priorities\n\
### Priority Order\n\
1. **Movement** - the player moves left and right\n\
### Preservation Gate\n\
- the project still launches\n\
### Acceptance Gate\n\
- simulate left/right and observe displacement\n";

pub const BAD_PLAN: &str = "I think we should add movement.\n";

pub fn ok_evidence(iteration: u32, candidate_placeholder: &str) -> String {
    format!(
        r#"{{
  "iteration": {iteration},
  "qa_status": "partial",
  "verified_records": [
    {{
      "claim_id": "F1",
      "claim": "player moves right",
      "execution_records": [
        {{
          "type": "assert",
          "path": ".hoh/evidence/move.json",
          "observation": "position.x increased from 0 to 32",
          "candidate_id": "{candidate_placeholder}"
        }}
      ],
      "status": "verified"
    }}
  ],
  "gap_records": [
    {{
      "claim_id": "F2",
      "claim": "player jumps",
      "execution_records": [],
      "status": "gap",
      "player_impact": "the player cannot reach the upper platform",
      "recommended_update": "add jump input handling"
    }}
  ],
  "planner_handoff": {{
    "preservation_constraints": ["keep the project launchable"],
    "update_targets": ["jump input"],
    "validation_requirements": ["simulate jump and observe y displacement"]
  }}
}}
"#
    )
}

pub fn bad_evidence() -> String {
    r#"{
  "iteration": 1,
  "qa_status": "pass",
  "verified_records": [],
  "gap_records": [],
  "planner_handoff": {
    "preservation_constraints": [],
    "update_targets": [],
    "validation_requirements": []
  }
}
"#
    .to_string()
}
