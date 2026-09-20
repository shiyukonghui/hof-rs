//! Token usage extraction (R12, D2).
//!
//! mini persists the full `ChatResponse` under `Message.extra["response"]`, so
//! usage can be recovered from the trajectory without patching the harness.
//! When a provider returns no usage block the runtime must say `unknown`
//! instead of reporting zeros.

use std::path::Path;

use serde_json::Value;

use crate::model::{Role, Usage};

fn field(usage: &Value, key: &str) -> Option<u64> {
    usage.get(key).and_then(Value::as_u64)
}

fn accumulate(target: &mut Option<u64>, value: Option<u64>) {
    if let Some(value) = value {
        *target = Some(target.unwrap_or(0) + value);
    }
}

/// One provider usage block, normalized to the five token fields.
struct UsageBlock {
    prompt: Option<u64>,
    completion: Option<u64>,
    total: Option<u64>,
    cache_hit: Option<u64>,
    cache_miss: Option<u64>,
}

/// Read one usage block, refilling `total_tokens` from prompt+completion when
/// the provider omitted it.
fn read_usage_block(usage: &Value) -> UsageBlock {
    let prompt = field(usage, "prompt_tokens");
    let completion = field(usage, "completion_tokens");
    let total = field(usage, "total_tokens").or_else(|| match (prompt, completion) {
        (Some(prompt), Some(completion)) => Some(prompt + completion),
        _ => None,
    });
    UsageBlock {
        prompt,
        completion,
        total,
        cache_hit: field(usage, "prompt_cache_hit_tokens")
            .or_else(|| field(usage, "cache_hit_tokens")),
        cache_miss: field(usage, "prompt_cache_miss_tokens")
            .or_else(|| field(usage, "cache_miss_tokens")),
    }
}

/// Extract aggregated usage from a mini trajectory file.
pub fn extract_usage(trajectory: &Path, role: Role, iteration: u32) -> anyhow::Result<Usage> {
    let raw = std::fs::read_to_string(trajectory).map_err(|error| {
        anyhow::anyhow!(
            "could not read trajectory {}: {error}",
            trajectory.display()
        )
    })?;
    let value: Value = serde_json::from_str(&raw).map_err(|error| {
        anyhow::anyhow!(
            "could not parse trajectory {}: {error}",
            trajectory.display()
        )
    })?;

    let mut usage = Usage {
        role: role.as_str().to_string(),
        iteration,
        ..Usage::default()
    };

    let messages = value
        .get("messages")
        .and_then(Value::as_array)
        .cloned()
        .unwrap_or_default();

    for message in &messages {
        let Some(response) = message.get("extra").and_then(|extra| extra.get("response")) else {
            continue;
        };
        usage.calls += 1;
        let Some(block) = response.get("usage").filter(|usage| !usage.is_null()) else {
            continue;
        };
        usage.usage_known = true;
        let block = read_usage_block(block);
        accumulate(&mut usage.prompt_tokens, block.prompt);
        accumulate(&mut usage.completion_tokens, block.completion);
        accumulate(&mut usage.total_tokens, block.total);
        accumulate(&mut usage.cache_hit_tokens, block.cache_hit);
        accumulate(&mut usage.cache_miss_tokens, block.cache_miss);
    }

    if !usage.usage_known {
        usage.prompt_tokens = None;
        usage.completion_tokens = None;
        usage.total_tokens = None;
        usage.cache_hit_tokens = None;
        usage.cache_miss_tokens = None;
    }
    Ok(usage)
}

/// Merge `other` into `accumulator`; missing fields stay missing.
pub fn merge_usage(accumulator: &mut Usage, other: &Usage) {
    accumulator.calls += other.calls;
    accumulate(&mut accumulator.prompt_tokens, other.prompt_tokens);
    accumulate(&mut accumulator.completion_tokens, other.completion_tokens);
    accumulate(&mut accumulator.total_tokens, other.total_tokens);
    accumulate(&mut accumulator.cache_hit_tokens, other.cache_hit_tokens);
    accumulate(&mut accumulator.cache_miss_tokens, other.cache_miss_tokens);
    accumulator.usage_known = accumulator.usage_known || other.usage_known;
}

/// Sum the usage of every attempt trajectory matching `traj/<role>.attempt*.json`.
pub fn usage_from_attempts(traj_dir: &Path, role: Role, iteration: u32) -> anyhow::Result<Usage> {
    let mut merged = Usage {
        role: role.as_str().to_string(),
        iteration,
        ..Usage::default()
    };
    let mut paths: Vec<std::path::PathBuf> = Vec::new();
    if traj_dir.is_dir() {
        for entry in std::fs::read_dir(traj_dir)? {
            let entry = entry?;
            let name = entry.file_name().to_string_lossy().into_owned();
            if name.starts_with(&format!("{}.attempt", role.as_str())) && name.ends_with(".json") {
                paths.push(entry.path());
            }
        }
    }
    paths.sort();
    for path in paths {
        let usage = extract_usage(&path, role, iteration)?;
        merge_usage(&mut merged, &usage);
    }
    Ok(merged)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn total_is_refilled_only_when_both_parts_exist() {
        let UsageBlock { total, .. } = read_usage_block(&serde_json::json!({
            "prompt_tokens": 10,
            "completion_tokens": 5
        }));
        assert_eq!(total, Some(15));
        let UsageBlock { total, .. } =
            read_usage_block(&serde_json::json!({ "prompt_tokens": 10 }));
        assert_eq!(total, None);
    }
}
