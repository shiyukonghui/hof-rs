//! `hoh.yaml` loading, CLI overrides, and the C9/C10 model identity assertion.

use std::path::PathBuf;

use serde::{Deserialize, Serialize};
use serde_json::Value;

use crate::errors::HofError;
use crate::model::Spec;

pub const DEFAULT_CONFIG_SPEC: &str = "config/hoh.yaml";
/// The exact on-the-wire model id (C9) and the exact provider string (C10).
pub const REQUIRED_MODEL_NAME: &str = "openai/qwen/qwen3.8-27b";
pub const REQUIRED_PROVIDER: &str = "openai_compatible";
pub const WIRE_MODEL_NAME: &str = "qwen/qwen3.8-27b";

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct AgentLimits {
    pub step_limit: u64,
    pub cost_limit: f64,
    pub wall_time_limit_seconds: u64,
    pub max_consecutive_format_errors: u64,
    pub command_timeout_seconds: u64,
}

impl Default for AgentLimits {
    fn default() -> Self {
        Self {
            step_limit: 60,
            cost_limit: 0.0,
            wall_time_limit_seconds: 3600,
            max_consecutive_format_errors: 3,
            command_timeout_seconds: 180,
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
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct GodotConfig {
    pub addon_source: PathBuf,
    #[serde(default)]
    pub cache_excludes: Vec<String>,
    #[serde(default = "default_main_scene")]
    pub main_scene: String,
}

fn default_main_scene() -> String {
    "res://scenes/main.tscn".to_string()
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct AdapterConfig {
    pub kind: String,
    pub godot: GodotConfig,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ToolsConfig {
    pub endpoint: String,
    pub timeout_seconds: u64,
    pub max_retries: u32,
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

    pub fn model_identity(&self) -> String {
        format!(
            "{}|{}|{}",
            self.model_name(),
            self.provider(),
            WIRE_MODEL_NAME
        )
    }
}

/// Assert the frozen model identity (C9/C10).
pub fn assert_model_identity(model: &Value) -> Result<(), HofError> {
    let model_name = model
        .get("model_name")
        .and_then(Value::as_str)
        .unwrap_or("")
        .to_string();
    let provider = model
        .get("provider")
        .and_then(Value::as_str)
        .unwrap_or("")
        .to_string();
    if model_name != REQUIRED_MODEL_NAME || provider != REQUIRED_PROVIDER {
        return Err(HofError::ModelIdentityViolation {
            model_name,
            provider,
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
        assert_eq!(config.model_name(), REQUIRED_MODEL_NAME);
        assert_eq!(config.provider(), REQUIRED_PROVIDER);
        assert_eq!(config.agent.cost_limit, 0.0);
        assert_eq!(config.runtime.iterations, 3);
    }

    #[test]
    fn model_fields_are_passed_through_untouched() {
        let config = load_config(&[]).expect("default config must load");
        assert_eq!(
            config.model.get("model_name").and_then(Value::as_str),
            Some(REQUIRED_MODEL_NAME)
        );
        assert_eq!(
            config.model.get("service_name").and_then(Value::as_str),
            Some("openai_compatible")
        );
    }

    #[test]
    fn rejects_model_name_without_prefix() {
        let error = load_config(&overrides(&["model.model_name=qwen/qwen3.8-27b"]))
            .expect_err("stripped model id must be rejected");
        let hof = crate::errors::as_hof_error(&error).expect("typed error");
        assert!(matches!(hof, HofError::ModelIdentityViolation { .. }));
        assert_eq!(hof.exit_code(), 2);
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
}
