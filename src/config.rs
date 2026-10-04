//! `hoh.yaml` loading, CLI overrides, and the config-driven model identity
//! assertion (C9/C10/C11, DR-14/DR-16).
//!
//! Model identity is **configuration driven**: this module never knows a
//! concrete model name.  `model.wire_model_name` declares the exact string the
//! request body must carry, and the identity assertion only checks generic
//! invariants (explicit provider, non-empty names, no secret in the file).

use std::path::PathBuf;

use serde::{Deserialize, Serialize};
use serde_json::Value;

use crate::errors::HofError;
use crate::model::Spec;

pub const DEFAULT_CONFIG_SPEC: &str = "config/hoh.yaml";
/// The variable a round exports so a **role's separate process** can find the
/// configuration file.
///
/// DR-96: a role's shell runs in the *project* directory — which for a real
/// round is a fresh project outside the repository — so the relative
/// `config/hoh.yaml` of [`DEFAULT_CONFIG_SPEC`] cannot resolve there, and every
/// `hoh tools call` a role makes fails with `could not find config file for
/// config/hoh.yaml`.  The round therefore exports the absolute path it loaded,
/// which the role's shell inherits.
pub const CONFIG_FILE_ENV: &str = "HOH_CONFIG_FILE";
/// The only provider string that is accepted (C10).
pub const REQUIRED_PROVIDER: &str = "openai_compatible";
/// Environment variables consulted for the model secret, in priority order
/// (C11/DR-15).  `HOH_MODEL_API_KEY` wins so the operator can point HoH at a
/// separate credential without disturbing `OPENAI_API_KEY`.
pub const API_KEY_ENV_VARS: &[&str] = &["HOH_MODEL_API_KEY", "OPENAI_API_KEY"];
/// The variable mini's own `resolve_api_key` falls back to for
/// `openai_compatible` models.  DR-16 exports the resolved secret here instead
/// of ever writing it into a recorded structure.
pub const MINI_API_KEY_ENV: &str = "OPENAI_API_KEY";
/// Placeholder written wherever a secret would otherwise be serialized.
pub const REDACTED: &str = "<redacted>";

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct AgentLimits {
    pub step_limit: u64,
    /// DR-18: when the remaining step budget drops to this threshold the role
    /// must first write a contract-valid artifact skeleton and only then keep
    /// improving it.  Also the budget ceiling of a wrap-up retry.
    #[serde(default = "default_wrap_up_steps")]
    pub wrap_up_steps: u64,
    /// DR-24: the budget of the one-shot targeted repair call issued when the
    /// pre-freeze launchable gate fails.
    #[serde(default = "default_repair_steps")]
    pub repair_steps: u64,
    pub cost_limit: f64,
    pub wall_time_limit_seconds: u64,
    pub max_consecutive_format_errors: u64,
    pub command_timeout_seconds: u64,
    /// DR-69 ③: the ceiling on one tool result, in bytes.  A result above it is
    /// truncated with an explicit annotation and never replayed in full
    /// (`smoke-t9`' attempt A died on a 15,570,803-byte result).
    #[serde(default = "default_max_tool_output_bytes")]
    pub max_tool_output_bytes: u64,
    /// Round-1 write-path batch: the **per-action** failure tripwire.
    ///
    /// `max_consecutive_format_errors` counts three *consecutive* format errors
    /// and is reset by any success, so round 1's Developer — which sometimes
    /// succeeded — could retry the same broken command forever.  This counts
    /// failures of one action and is cleared only when **that action** succeeds.
    #[serde(default = "default_max_action_failures")]
    pub max_action_failures: u64,
    /// Round-1 write-path batch: the wall-clock budget for producing the
    /// artifact this role declares.  A call that has not written a project file
    /// (or `.hoh/evidence.json`, per role) within it is aborted with the
    /// first-class `ArtifactBudgetExceeded` status.
    #[serde(default = "default_artifact_write_budget_seconds")]
    pub artifact_write_budget_seconds: u64,
    /// Round-1 write-path batch: the token half of the same budget.  Usage is
    /// known only after a model call returns, so this one is enforced by the
    /// runtime on the recorded attempt (`crate::runtime::write_failure`), not
    /// live inside the environment.
    #[serde(default = "default_artifact_write_budget_tokens")]
    pub artifact_write_budget_tokens: u64,
}

/// Round-1 write-path batch: three failures of one action is enough to conclude
/// the action cannot succeed — round 1 repeated its file-writing attempts 140
/// times.
fn default_max_action_failures() -> u64 {
    3
}

/// Round-1 write-path batch: 900 s (15 min) is roughly a quarter of round 1's
/// 54.4-minute Developer call and comfortably above every measured *successful*
/// write path (the Planner wrote its plan in 72 s; the Developer's first real
/// write was minutes in), so it can only fire on a grind.
fn default_artifact_write_budget_seconds() -> u64 {
    900
}

/// Round-1 write-path batch: 1,500,000 tokens is about a seventh of round 1's
/// 10.4M-token Developer attempt and six model calls at its measured ~74k
/// tokens per call average — wide enough for a real design-and-write, narrow
/// enough that one file cannot cost 10M tokens again.
fn default_artifact_write_budget_tokens() -> u64 {
    1_500_000
}

/// DR-69 ③: 64 KiB — see [`crate::harness::cap::DEFAULT_MAX_TOOL_OUTPUT_BYTES`].
fn default_max_tool_output_bytes() -> u64 {
    crate::harness::cap::DEFAULT_MAX_TOOL_OUTPUT_BYTES as u64
}

fn default_wrap_up_steps() -> u64 {
    25
}

fn default_repair_steps() -> u64 {
    60
}

impl Default for AgentLimits {
    fn default() -> Self {
        Self {
            // DR-18: 60 was proven insufficient by the first real smoke run
            // (5/5 calls ended in `LimitsExceeded`).
            step_limit: 150,
            wrap_up_steps: default_wrap_up_steps(),
            repair_steps: default_repair_steps(),
            cost_limit: 0.0,
            wall_time_limit_seconds: 3600,
            max_consecutive_format_errors: 3,
            command_timeout_seconds: 180,
            max_tool_output_bytes: default_max_tool_output_bytes(),
            max_action_failures: default_max_action_failures(),
            artifact_write_budget_seconds: default_artifact_write_budget_seconds(),
            artifact_write_budget_tokens: default_artifact_write_budget_tokens(),
        }
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct RuntimeConfig {
    pub iterations: u32,
    pub max_schema_retries: u32,
    pub workspace: PathBuf,
    pub runs_dir: PathBuf,
    pub spec: PathBuf,
    /// DR-3: relative paths/prefixes that must never be copied into a role view.
    /// They deliberately do **not** extend the `hash_tree`/snapshot exclude set,
    /// so R2/R3 write-detection is not weakened.
    #[serde(default)]
    pub private_excludes: Vec<String>,
    /// DR-25: the "HoH working directory" scanned for out-of-tree writes.  It
    /// defaults to the process working directory (the repository root of a real
    /// run); tests point it at a temporary directory.
    #[serde(default)]
    pub out_of_tree_root: Option<PathBuf>,
    /// DR-36: the per-file size ceiling applied while copying
    /// `.hoh/evidence/**` into the frozen candidate view.  A file above it is
    /// **still copied** and reported (`evidence_too_large`), never dropped.
    #[serde(default = "default_max_evidence_bytes")]
    pub max_evidence_bytes: u64,
}

/// DR-36: 8 MiB — generous enough for a screenshot or a short replay, small
/// enough that a runaway recording is still made visible in `warnings`.
fn default_max_evidence_bytes() -> u64 {
    8 * 1024 * 1024
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct AdapterConfig {
    pub kind: String,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ToolsConfig {
    pub endpoint: String,
    pub timeout_seconds: u64,
    pub max_retries: u32,
    /// DR-20: how long `editor_play_scene` may take to become observable (the
    /// `running_game_get_scene_tree` readiness poll) before the step is recorded as a
    /// failure.  Defaults to 30 seconds when the key is absent.
    #[serde(default = "default_ready_timeout_seconds")]
    pub ready_timeout_seconds: u64,
    /// DR-29: how many read-only `project_get_info` probes one call may spend
    /// re-correlating a lagging JSON-RPC response before
    /// `HofError::McpResponseDesync` is returned.  Defaults to 4.
    #[serde(default = "default_max_sync_retries")]
    pub max_sync_retries: u32,
}

fn default_ready_timeout_seconds() -> u64 {
    30
}

fn default_max_sync_retries() -> u32 {
    crate::tools::mcp::DEFAULT_MAX_SYNC_RETRIES
}

/// The full runtime configuration.  `model` is passed through to mini
/// untouched: this layer must never rewrite a model field.
#[derive(Clone, Debug)]
pub struct HohConfig {
    pub model: Value,
    pub agent: AgentLimits,
    pub runtime: RuntimeConfig,
    pub adapter: AdapterConfig,
    pub tools: ToolsConfig,
}

impl HohConfig {
    pub fn model_name(&self) -> &str {
        self.model
            .get("model_name")
            .and_then(Value::as_str)
            .unwrap_or("")
    }

    /// DR-14: the exact string the request body must carry.  Declared in
    /// configuration, consumed by both the offline double-lock test and the
    /// online `hoh doctor` probe — never hard-coded in `src/**`.
    pub fn wire_model_name(&self) -> &str {
        wire_model_name_of(&self.model)
    }

    pub fn provider(&self) -> &str {
        self.model
            .get("provider")
            .and_then(Value::as_str)
            .unwrap_or("")
    }

    pub fn base_url(&self) -> &str {
        self.model
            .get("base_url")
            .and_then(Value::as_str)
            .unwrap_or("")
    }

    /// C11: `model.api_key` (never non-empty after the identity assertion) →
    /// `HOH_MODEL_API_KEY` → `OPENAI_API_KEY` → `None`.
    pub fn resolved_api_key(&self) -> Option<String> {
        resolve_api_key_with(&self.model, |name| std::env::var(name).ok())
    }

    /// The model section with every secret removed.  Used for `meta.json` and
    /// anywhere else the configuration is persisted (DR-16).
    pub fn redacted_model(&self) -> Value {
        redact_model_value(&self.model)
    }

    pub fn model_identity(&self) -> String {
        format!(
            "{}|{}|{}",
            self.model_name(),
            self.provider(),
            self.wire_model_name()
        )
    }
}

/// DR-14: read the declared wire identity out of a raw model section.  Shared
/// by `HohConfig::wire_model_name`, `hoh doctor` and the harness so there is a
/// single definition of "what the request body must carry".
pub fn wire_model_name_of(model: &Value) -> &str {
    model
        .get("wire_model_name")
        .and_then(Value::as_str)
        .unwrap_or("")
}

/// Secret resolution, parameterised over the environment lookup so the
/// priority order is testable without touching process-global state.
pub fn resolve_api_key_with<F>(model: &Value, get_env: F) -> Option<String>
where
    F: Fn(&str) -> Option<String>,
{
    let explicit = model
        .get("api_key")
        .and_then(Value::as_str)
        .map(str::trim)
        .filter(|value| !value.is_empty());
    if let Some(explicit) = explicit {
        return Some(explicit.to_string());
    }
    API_KEY_ENV_VARS
        .iter()
        .find_map(|name| get_env(name).map(|value| value.trim().to_string()))
        .filter(|value| !value.is_empty())
}

/// DR-16: replace `api_key` with `null` in a model section (and in the
/// `model` sub-object when a whole config object is handed in).  Pure: the
/// caller keeps its own copy.
pub fn redact_model_value(value: &Value) -> Value {
    let mut redacted = value.clone();
    if let Some(object) = redacted.as_object_mut() {
        if object.contains_key("api_key") {
            object.insert("api_key".to_string(), Value::Null);
        }
        if let Some(model) = object.get_mut("model").and_then(Value::as_object_mut) {
            if model.contains_key("api_key") {
                model.insert("api_key".to_string(), Value::Null);
            }
        }
    }
    redacted
}

/// DR-16 (recommended, zero-leak design): the secret lives **only** in the HoH
/// process environment.  Before any agent is built, the resolved key is
/// exported as `OPENAI_API_KEY` so mini's own `resolve_api_key` fallback picks
/// it up.  It is never written into the model JSON nor into a role's
/// `LocalEnvironment` env map, because mini serializes both into the
/// trajectory.
pub fn export_model_api_key(config: &HohConfig) -> Option<String> {
    let resolved = config.resolved_api_key()?;
    if std::env::var(MINI_API_KEY_ENV).ok().as_deref() != Some(resolved.as_str()) {
        std::env::set_var(MINI_API_KEY_ENV, &resolved);
    }
    Some(resolved)
}

/// Assert the generic model identity invariants (C9/C10/C11, DR-14).
///
/// This function deliberately knows **no** concrete model name: `wire_model_name`
/// is the declaration, and it is the offline/online probes that verify the
/// actual wire traffic against it.
pub fn assert_model_identity(model: &Value) -> Result<(), HofError> {
    let model_name = model
        .get("model_name")
        .and_then(Value::as_str)
        .unwrap_or("")
        .trim()
        .to_string();
    let provider = model
        .get("provider")
        .and_then(Value::as_str)
        .map(str::trim)
        .unwrap_or("")
        .to_string();
    let wire_model_name = model
        .get("wire_model_name")
        .and_then(Value::as_str)
        .unwrap_or("")
        .trim()
        .to_string();

    if provider != REQUIRED_PROVIDER {
        return Err(HofError::ModelIdentityViolation {
            reason: "model.provider must be explicit (C10)".to_string(),
            expected: REQUIRED_PROVIDER.to_string(),
            actual: provider,
        });
    }
    if model_name.is_empty() {
        return Err(HofError::ModelIdentityViolation {
            reason: "model.model_name must be non-empty (DR-14)".to_string(),
            expected: "a non-empty model_name".to_string(),
            actual: model_name,
        });
    }
    if wire_model_name.is_empty() {
        return Err(HofError::ModelIdentityViolation {
            reason: "model.wire_model_name must be non-empty (DR-14)".to_string(),
            expected: "a non-empty wire_model_name".to_string(),
            actual: wire_model_name,
        });
    }
    // C11: the secret must come from the environment.  A non-empty value here
    // would be persisted into `meta.json` and the trajectory, so it is a hard
    // configuration error rather than a warning.
    if let Some(explicit) = model
        .get("api_key")
        .and_then(Value::as_str)
        .filter(|value| !value.trim().is_empty())
    {
        return Err(HofError::ModelIdentityViolation {
            reason: "model.api_key must be empty; keys are read from HOH_MODEL_API_KEY or \
                     OPENAI_API_KEY and never stored in the configuration (C11/DR-16)"
                .to_string(),
            expected: format!("<empty> ({})", API_KEY_ENV_VARS.join(" | ")),
            actual: format!("<redacted: {} char(s)>", explicit.trim().chars().count()),
        });
    }
    Ok(())
}

/// Load the configuration from an ordered list of specs.
///
/// `specs[0]` defaults to `config/hoh.yaml` when the list is empty, and later
/// specs win (`recursive_merge`), which is how `-c key=value` overrides work.
pub fn load_config(specs: &[String]) -> anyhow::Result<HohConfig> {
    let mut all: Vec<Value> = Vec::new();
    if specs.is_empty() {
        all.push(mini_swe_agent::get_config_from_spec(DEFAULT_CONFIG_SPEC)?);
    } else {
        for spec in specs {
            all.push(mini_swe_agent::get_config_from_spec(spec)?);
        }
    }
    let merged = mini_swe_agent::recursive_merge(all);

    let model = merged.get("model").cloned().unwrap_or(Value::Null);
    assert_model_identity(&model)?;

    let agent: AgentLimits = take_section(&merged, "agent")?;
    let runtime: RuntimeConfig = take_section(&merged, "runtime")?;
    let adapter: AdapterConfig = take_section(&merged, "adapter")?;
    let tools: ToolsConfig = take_section(&merged, "tools")?;

    Ok(HohConfig {
        model,
        agent,
        runtime,
        adapter,
        tools,
    })
}

fn take_section<T: serde::de::DeserializeOwned>(merged: &Value, key: &str) -> anyhow::Result<T> {
    let section = merged
        .get(key)
        .cloned()
        .ok_or_else(|| anyhow::anyhow!("configuration section `{key}` is missing"))?;
    serde_json::from_value(section)
        .map_err(|error| anyhow::anyhow!("invalid configuration section `{key}`: {error}"))
}

/// Compute the frozen-spec record (path + sha256 of the raw bytes).
pub fn load_spec(path: &std::path::Path) -> anyhow::Result<Spec> {
    let bytes = std::fs::read(path)
        .map_err(|error| anyhow::anyhow!("could not read spec {}: {error}", path.display()))?;
    Ok(Spec {
        path: path.to_path_buf(),
        sha256: crate::runtime::policy::sha256_hex(&bytes),
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn overrides(pairs: &[&str]) -> Vec<String> {
        let mut specs = vec![DEFAULT_CONFIG_SPEC.to_string()];
        specs.extend(pairs.iter().map(|pair| pair.to_string()));
        specs
    }

    #[test]
    fn loads_default_config() {
        let config = load_config(&[]).expect("default config must load");
        // DR-14: the expected wire name is whatever the configuration declares.
        assert!(!config.model_name().is_empty());
        assert!(!config.wire_model_name().is_empty());
        assert_eq!(
            config.model.get("wire_model_name").and_then(Value::as_str),
            Some(config.wire_model_name())
        );
        assert_eq!(config.provider(), REQUIRED_PROVIDER);
        assert_eq!(config.agent.cost_limit, 0.0);
        assert_eq!(config.runtime.iterations, 3);
        assert!(config.runtime.private_excludes.is_empty());
    }

    #[test]
    fn model_fields_are_passed_through_untouched() {
        let file = mini_swe_agent::get_config_from_spec(DEFAULT_CONFIG_SPEC).expect("config file");
        let config = load_config(&[]).expect("default config must load");
        // DR-14: `wire_model_name` must stay in the model JSON handed to mini
        // (mini ignores the unknown field via `#[serde(flatten)] extra`) and
        // must never be used to rewrite `model_name`.
        assert_eq!(
            config.model.get("wire_model_name").and_then(Value::as_str),
            file["model"].get("wire_model_name").and_then(Value::as_str)
        );
        assert_eq!(
            config.model.get("model_name").and_then(Value::as_str),
            file["model"].get("model_name").and_then(Value::as_str)
        );
        assert_eq!(
            config.model.get("service_name").and_then(Value::as_str),
            Some("openai_compatible")
        );
    }

    #[test]
    fn rejects_a_non_empty_config_api_key() {
        let error = load_config(&overrides(&["model.api_key=should-not-be-here"]))
            .expect_err("a config api_key must be rejected (C11)");
        let hof = crate::errors::as_hof_error(&error).expect("typed error");
        assert!(matches!(hof, HofError::ModelIdentityViolation { .. }));
        assert_eq!(hof.exit_code(), 2);
        assert!(!error.to_string().contains("should-not-be-here"));
    }

    #[test]
    fn rejects_a_blank_wire_model_name() {
        let error = load_config(&overrides(&["model.wire_model_name="]))
            .expect_err("an empty wire_model_name must be rejected (DR-14)");
        assert!(matches!(
            crate::errors::as_hof_error(&error),
            Some(HofError::ModelIdentityViolation { .. })
        ));
    }

    #[test]
    fn rejects_missing_provider() {
        let error = load_config(&overrides(&["model.provider=aliyun"]))
            .expect_err("implicit provider must be rejected");
        assert!(matches!(
            crate::errors::as_hof_error(&error),
            Some(HofError::ModelIdentityViolation { .. })
        ));
    }

    #[test]
    fn cli_overrides_win() {
        let config = load_config(&overrides(&[
            "model.base_url=http://127.0.0.1:9999/v1",
            "runtime.iterations=1",
        ]))
        .expect("override config must load");
        assert_eq!(config.base_url(), "http://127.0.0.1:9999/v1");
        assert_eq!(config.runtime.iterations, 1);
    }

    /// C11/DR-15: `model.api_key` (non-empty) → `HOH_MODEL_API_KEY` →
    /// `OPENAI_API_KEY` → `None`.  Parameterised so no process env is touched.
    #[test]
    fn api_key_resolution_follows_the_documented_priority() {
        let env = |pairs: &[(&str, &str)]| {
            let pairs: Vec<(String, String)> = pairs
                .iter()
                .map(|(k, v)| (k.to_string(), v.to_string()))
                .collect();
            move |name: &str| {
                pairs
                    .iter()
                    .find(|(key, _)| key == name)
                    .map(|(_, value)| value.clone())
            }
        };

        let model = serde_json::json!({"model_name": "m", "api_key": "explicit"});
        assert_eq!(
            resolve_api_key_with(&model, env(&[("OPENAI_API_KEY", "env")])),
            Some("explicit".to_string())
        );

        let model = serde_json::json!({"model_name": "m", "api_key": ""});
        assert_eq!(
            resolve_api_key_with(
                &model,
                env(&[("HOH_MODEL_API_KEY", "hoh"), ("OPENAI_API_KEY", "env")])
            ),
            Some("hoh".to_string())
        );
        assert_eq!(
            resolve_api_key_with(&model, env(&[("OPENAI_API_KEY", "env")])),
            Some("env".to_string())
        );
        assert_eq!(resolve_api_key_with(&model, env(&[])), None);
        // Blank values never count as a resolved key.
        assert_eq!(
            resolve_api_key_with(
                &model,
                env(&[("HOH_MODEL_API_KEY", "   "), ("OPENAI_API_KEY", "")])
            ),
            None
        );
    }

    /// DR-16: a redacted model section carries no secret, and redaction is pure.
    #[test]
    fn redaction_removes_the_secret_without_mutating_the_original() {
        let model = serde_json::json!({"model_name": "m", "api_key": "leaky-secret"});
        let redacted = redact_model_value(&model);
        assert!(redacted.get("api_key").unwrap().is_null());
        assert_eq!(
            model.get("api_key").and_then(Value::as_str),
            Some("leaky-secret"),
            "redaction must not mutate the caller's value"
        );
    }
}
