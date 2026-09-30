//! DR-19: the model secret must never reach a role subprocess, and anything
//! that leaks into `runs/<id>/**` is erased before it becomes an artifact.
//!
//! Root cause found by the first real smoke run: mini's `LocalEnvironment`
//! inherits the parent environment and only overrides the keys it is given, so
//! a role running `cmd /c set HOH` could echo the credential into its
//! trajectory and the model context.  Two defences are implemented here:
//!
//! 1. every role environment explicitly sets the known secret variables to the
//!    empty string, blocking the inheritance; and
//! 2. after every role call the run directory is scanned for the known secret
//!    values and rewritten with `<redacted>`.

use std::collections::BTreeMap;
use std::path::Path;

use walkdir::WalkDir;

use crate::config::{HohConfig, REDACTED};

/// Every environment variable that may carry the model credential.
pub const SECRET_ENV_VARS: &[&str] = &[
    "HOH_MODEL_API_KEY",
    "OPENAI_API_KEY",
    "LITELLM_API_KEY",
    "MSWEA_MODEL_API_KEY",
];

/// The overrides that must be present in *every* role environment so a child
/// shell cannot inherit a live credential.
pub fn blocked_env() -> BTreeMap<String, String> {
    SECRET_ENV_VARS
        .iter()
        .map(|name| (name.to_string(), String::new()))
        .collect()
}

/// The secret values this process knows about: the resolved configuration key
/// plus any value currently present in a known variable.
///
/// Values shorter than 6 characters are ignored: redacting them would corrupt
/// unrelated text without any security benefit.
pub fn known_secrets(cfg: &HohConfig) -> Vec<String> {
    let mut secrets: Vec<String> = Vec::new();
    if let Some(resolved) = cfg.resolved_api_key() {
        secrets.push(resolved);
    }
    for name in SECRET_ENV_VARS {
        if let Ok(value) = std::env::var(name) {
            secrets.push(value.trim().to_string());
        }
    }
    secrets.retain(|value| value.chars().count() >= 6);
    secrets.sort();
    secrets.dedup();
    secrets
}

/// DR-69: erase the **assignment** to a known secret variable, not only the
/// secret's value.
///
/// The round that exposed this never leaked a key: the Developer ran
/// `set | findstr /i "HOH"`, and the harness's own `DSH_TERM_CMD` was written
/// into the trajectory and then into a committed evidence file as
/// `export HOH_MODEL_API_KEY="$(cat /c/Users/.../keyval.txt)"; ...`.  No file
/// contained the credential, but every file recorded **where it lives**.  A
/// value-substitution scan cannot see that: the dangling reference contains no
/// secret.  The variable name is the thing that must not survive, so the whole
/// assignment is replaced.
pub fn redact_secret_assignments(text: &str) -> String {
    let mut out = text.to_string();
    for name in SECRET_ENV_VARS {
        let needle = format!("{name}=");
        let mut search_from = 0usize;
        loop {
            let Some(found) = out[search_from..].find(needle.as_str()) else {
                break;
            };
            let start = search_from + found;
            let value_start = start + needle.len();
            let value_end = if out.as_bytes().get(value_start) == Some(&b'"') {
                match out[value_start + 1..].find('"') {
                    Some(relative) => value_start + 1 + relative + 1,
                    None => out.len(),
                }
            } else {
                out[value_start..]
                    .find([';', '\n', '\r'])
                    .map(|relative| value_start + relative)
                    .unwrap_or(out.len())
            };
            let replacement = format!("{needle}{REDACTED}");
            out.replace_range(start..value_end, &replacement);
            search_from = start + replacement.len();
        }
    }
    out
}

/// Scan every file under `root` and replace every occurrence of a known secret
/// with `<redacted>`.
///
/// Returns the number of **files** that contained at least one secret.  The
/// secret value itself is never printed.
pub fn redact_tree(root: &Path, secrets: &[String]) -> anyhow::Result<u64> {
    // DR-69: the assignment rule needs no secret value, so the scan runs even
    // when no credential is configured -- the credential's *location* is what
    // leaked in `smoke-t9`, and that leak has nothing to do with whether this
    // process can resolve the key itself.
    if !root.exists() {
        return Ok(0);
    }
    let mut hits = 0u64;
    for entry in WalkDir::new(root).follow_links(false) {
        let entry = entry?;
        if !entry.file_type().is_file() {
            continue;
        }
        let bytes = std::fs::read(entry.path())?;
        // Secrets are ASCII-ish credentials; a non-UTF-8 file cannot contain a
        // literal textual key that the model could echo.
        let Ok(text) = String::from_utf8(bytes) else {
            continue;
        };
        let before = text.clone();
        let mut redacted = text;
        for secret in secrets {
            if redacted.contains(secret.as_str()) {
                redacted = redacted.replace(secret.as_str(), REDACTED);
            }
        }
        // DR-69: and the assignment itself, whatever the value was.
        redacted = redact_secret_assignments(&redacted);
        let changed = redacted != before;
        if changed {
            std::fs::write(entry.path(), redacted.as_bytes())?;
            hits += 1;
        }
    }
    Ok(hits)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn blocked_env_covers_every_known_variable() {
        let env = blocked_env();
        assert_eq!(env.len(), SECRET_ENV_VARS.len());
        for name in SECRET_ENV_VARS {
            assert_eq!(env.get(*name).map(String::as_str), Some(""));
        }
    }

    /// DR-69: an environment dump must not record where the credential lives.
    #[test]
    fn an_environment_dump_does_not_leak_the_credential_channel() {
        let dumped = "cd /f/x; export HOH_MODEL_API_KEY=\"$(cat /c/Users/u/AppData/Local/\
                      Temp/t9/keyval.txt)\"; set HOH=1";
        let redacted = redact_secret_assignments(dumped);
        assert!(
            !redacted.contains("keyval.txt"),
            "the key file's path must not survive: {redacted}"
        );
        assert!(
            redacted.contains(&format!("HOH_MODEL_API_KEY={REDACTED}")),
            "{redacted}"
        );
        // The bare `cmd` spelling (`set NAME=value`) is the same leak.
        let redacted = redact_secret_assignments("set OPENAI_API_KEY=abc123; echo hi");
        assert!(!redacted.contains("abc123"), "{redacted}");
        assert!(redacted.contains("echo hi"), "{redacted}");
        // Text that assigns nothing is untouched, byte for byte.
        assert_eq!(redact_secret_assignments("echo hello\n"), "echo hello\n");
    }

    /// DR-69: the file-level scan applies both rules, and reports one hit per
    /// changed file.
    #[test]
    fn the_tree_scan_redacts_an_assignment_without_a_known_value() {
        let temp = tempfile::tempdir().unwrap();
        std::fs::write(
            temp.path().join("dump.txt"),
            "export HOH_MODEL_API_KEY=\"$(cat /secret/path/keyval.txt)\";\n",
        )
        .unwrap();
        let hits = redact_tree(temp.path(), &[]).expect("the scan runs without secrets");
        assert_eq!(hits, 1);
        let text = std::fs::read_to_string(temp.path().join("dump.txt")).unwrap();
        assert!(!text.contains("keyval.txt"), "{text}");
    }

    #[test]
    fn redaction_rewrites_only_files_that_contain_a_secret() {
        let temp = tempfile::tempdir().unwrap();
        std::fs::write(temp.path().join("clean.txt"), "nothing to see\n").unwrap();
        std::fs::write(
            temp.path().join("leak.txt"),
            "token=test-key-not-a-secret\n",
        )
        .unwrap();

        let hits = redact_tree(temp.path(), &[String::from("test-key-not-a-secret")]).unwrap();
        assert_eq!(hits, 1);
        assert_eq!(
            std::fs::read_to_string(temp.path().join("clean.txt")).unwrap(),
            "nothing to see\n"
        );
        let leak = std::fs::read_to_string(temp.path().join("leak.txt")).unwrap();
        assert!(leak.contains(REDACTED), "{leak}");
        assert!(!leak.contains("test-key-not-a-secret"), "{leak}");
    }
}
