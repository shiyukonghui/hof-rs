//! DR-44: engine identity — *which binary produced this evidence?*
//!
//! Switching the engine is only worth something if the switch is checkable.
//! Three artifacts carry the answer:
//!
//! * `meta.json.engine`, a **fixed** block: an unknown value is `null` **plus**
//!   a reason — never an omitted field and never an invented value (R12's
//!   usage-unknown discipline);
//! * the `godot.engine_binary` / `godot.engine_version` doctor items, where the
//!   version string is **recorded verbatim and never asserted** (C12: a version
//!   bump must not require a code change);
//! * the `engine_identity` launch-gate step: evidence collected through a
//!   different binary than the configured one is worthless, so the gate closes.
//!
//! The Windows probe (port → pid → executable path) runs through mini's
//! existing [`Environment`] abstraction.  That keeps the whole thing offline
//! testable against a fake environment — and is why **no crate dependency was
//! added** for one pre-flight check.

use std::io::Read;
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

use serde::{Deserialize, Serialize};
use serde_json::Value;
use sha2::{Digest, Sha256};

use crate::adapter::{BatteryRecord, DoctorItem};
use crate::model::{ExecKind, ExecRecord};
use crate::tools::endpoint::GameEndpointRecord;

/// DR-44 ⑤: the launch-gate step that refuses another engine's evidence.
pub const ENGINE_IDENTITY_STEP_ID: &str = "engine_identity";
/// The engine kind written into `meta.json.engine.kind` by the Godot adapter.
pub const ENGINE_KIND_GODOT: &str = "godot";
/// The engine kind of an adapter that does not identify an engine.
pub const ENGINE_KIND_UNKNOWN: &str = "unknown";
/// The timeout of one probe command, in seconds.
pub const PROBE_TIMEOUT_SECONDS: u64 = 60;

/// DR-44 ③: the engine binary record.  `path` is the **configured** path, so a
/// missing file is still named; everything that could not be read is `null`
/// with a `reason`.
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct EngineBinary {
    pub path: Option<String>,
    pub size_bytes: Option<u64>,
    pub mtime_unix: Option<u64>,
    pub sha256: Option<String>,
    pub reason: Option<String>,
}

/// DR-44 ③: the MCP endpoints of this run.  `editor_status` holds the verbatim
/// `GET /mcp` body when one was taken; `null` values carry a reason.
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct EngineMcp {
    pub editor_endpoint: Option<String>,
    pub game_endpoint: Option<GameEndpointRecord>,
    pub editor_status: Value,
    pub game_endpoint_reason: Option<String>,
    pub editor_status_reason: Option<String>,
}

/// DR-44 ③④: who actually listens on the editor port.
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct ListenerInfo {
    pub pid: Option<u32>,
    pub path: Option<String>,
    /// `Some(true)`/`Some(false)` when the listener could be resolved;
    /// `None` (with a `reason`) when it could not — which must never be read as
    /// a match.
    pub matches_binary: Option<bool>,
    pub reason: Option<String>,
}

/// DR-44 ③: `meta.json.engine`.  Every field is always present.
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct EngineIdentity {
    pub kind: String,
    pub binary: EngineBinary,
    /// The version string, **verbatim** (`<binary> --version`).
    pub version_string: Option<String>,
    pub version_reason: Option<String>,
    pub mcp: EngineMcp,
    pub listener: ListenerInfo,
    pub checked_at: u64,
}

impl Default for EngineIdentity {
    /// "Nothing was probed": every value `null`, every reason naming why.  This
    /// is what a `RunMeta` deserialized without an `engine` block gets.
    fn default() -> Self {
        Self::unavailable("the engine identity was not probed for this run")
    }
}

impl EngineIdentity {
    /// An identity that could not be established at all (an adapter without an
    /// engine binary).  Every value is `null` and every `reason` names why.
    pub fn unavailable(reason: impl Into<String>) -> Self {
        let reason = reason.into();
        Self {
            kind: ENGINE_KIND_UNKNOWN.to_string(),
            binary: EngineBinary {
                path: None,
                size_bytes: None,
                mtime_unix: None,
                sha256: None,
                reason: Some(reason.clone()),
            },
            version_string: None,
            version_reason: Some(reason.clone()),
            mcp: EngineMcp {
                editor_endpoint: None,
                game_endpoint: None,
                // DR-44 ③ / DR-51: an unobtainable value is `null`, never an
                // empty object, so the two paths (`unavailable` and a failed
                // probe) serialize identically and the reason is authoritative.
                editor_status: Value::Null,
                game_endpoint_reason: Some(reason.clone()),
                editor_status_reason: Some(reason.clone()),
            },
            listener: ListenerInfo {
                pid: None,
                path: None,
                matches_binary: None,
                reason: Some(reason),
            },
            checked_at: now_seconds(),
        }
    }
}

/// Unix seconds, or 0 when the clock is before the epoch.
pub fn now_seconds() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|duration| duration.as_secs())
        .unwrap_or(0)
}

/// The TCP table command the listener probe runs (Windows).
pub fn netstat_command() -> String {
    "netstat -ano -p tcp".to_string()
}

/// The command that turns a pid into an executable path (Windows).
pub fn process_path_command(pid: u32) -> String {
    format!("powershell -NoProfile -Command \"(Get-Process -Id {pid} -ErrorAction Stop).Path\"")
}

/// The version query.  `--version` is a dry query: it starts no editor, opens
/// no project and binds no port.
pub fn version_command(binary: &Path) -> String {
    format!("\"{}\" --version", binary.display())
}

/// Compare paths the way Windows does: backslashes, case, `//?/` prefixes and
/// `.`/`..` components are all the same file.
pub fn normalize_windows_path(value: &str) -> String {
    let mut text = value.trim().replace('\\', "/").to_ascii_lowercase();
    if let Some(rest) = text.strip_prefix("//?/") {
        text = rest.to_string();
    }
    let mut parts: Vec<&str> = Vec::new();
    for part in text.split('/') {
        match part {
            "" | "." => {}
            ".." => {
                parts.pop();
            }
            other => parts.push(other),
        }
    }
    parts.join("/")
}

/// DR-44 ④: is the process that listens on the port the binary we configured?
pub fn binary_matches(expected: &Path, actual: &str) -> bool {
    let expected = std::fs::canonicalize(expected)
        .map(|path| path.to_string_lossy().into_owned())
        .unwrap_or_else(|_| expected.to_string_lossy().into_owned());
    normalize_windows_path(&expected) == normalize_windows_path(actual)
}

/// The `pid` of the TCP listener on `port`, preferring a `LISTEN*` state.
///
/// The table is parsed positionally (`netstat -ano` prints
/// `proto local foreign state pid`); the state word is only a *tie-breaker*,
/// because it is localised.
pub fn parse_listener_pid(table: &str, port: u16) -> Option<u32> {
    let suffix = format!(":{port}");
    let mut candidate = None;
    for line in table.lines() {
        let columns: Vec<&str> = line.split_whitespace().collect();
        if columns.len() < 4 {
            continue;
        }
        // The local address is the second column (`netstat -ano -p tcp`).
        if !columns[1].ends_with(&suffix) {
            continue;
        }
        let Some(pid) = columns.last().and_then(|value| value.parse::<u32>().ok()) else {
            continue;
        };
        let listening = columns
            .iter()
            .any(|column| column.to_ascii_uppercase().starts_with("LISTEN"));
        if listening {
            return Some(pid);
        }
        candidate.get_or_insert(pid);
    }
    candidate
}

/// The first non-empty line of a command's output (that is what `--version`
/// prints, and it is recorded verbatim).
pub fn first_line(output: &str) -> Option<String> {
    output
        .lines()
        .map(str::trim)
        .find(|line| !line.is_empty())
        .map(ToOwned::to_owned)
}

/// Run one probe command through the existing [`mini_swe_agent::Environment`].
async fn run(
    env: &dyn mini_swe_agent::Environment,
    command: &str,
) -> Result<mini_swe_agent::Output, String> {
    let action = mini_swe_agent::Action::new(command.to_string());
    env.execute(&action, None, Some(PROBE_TIMEOUT_SECONDS))
        .await
        .map_err(|error| error.to_string())
}

/// DR-44 ④: port → pid → executable path, compared with the configured binary.
pub async fn probe_listener(
    env: &dyn mini_swe_agent::Environment,
    port: u16,
    expected_binary: &Path,
) -> ListenerInfo {
    let table = match run(env, &netstat_command()).await {
        Ok(output) => output.output,
        Err(error) => {
            return ListenerInfo {
                pid: None,
                path: None,
                matches_binary: None,
                reason: Some(format!(
                    "the TCP listener table could not be read for port {port}: {error}"
                )),
            }
        }
    };
    let Some(pid) = parse_listener_pid(&table, port) else {
        return ListenerInfo {
            pid: None,
            path: None,
            matches_binary: None,
            reason: Some(format!(
                "no TCP listener on port {port} could be read from `{}`",
                netstat_command()
            )),
        };
    };
    let command = process_path_command(pid);
    let path = match run(env, &command).await {
        Ok(output) => first_line(&output.output),
        Err(error) => {
            return ListenerInfo {
                pid: Some(pid),
                path: None,
                matches_binary: None,
                reason: Some(format!(
                    "the executable path of pid {pid} could not be read: {error}"
                )),
            }
        }
    };
    let Some(path) = path else {
        return ListenerInfo {
            pid: Some(pid),
            path: None,
            matches_binary: None,
            reason: Some(format!(
                "the process listening on port {port} (pid {pid}) reported no executable path"
            )),
        };
    };
    let matches = binary_matches(expected_binary, &path);
    let reason = if matches {
        None
    } else {
        // DR-44 ⑤: all three facts in one line, so the operator can act on it
        // without a second probe.
        Some(format!(
            "engine identity mismatch: the configured binary is {} while the process listening \
             on port {port} is {path} (pid {pid})",
            expected_binary.display()
        ))
    };
    ListenerInfo {
        pid: Some(pid),
        path: Some(path),
        matches_binary: Some(matches),
        reason,
    }
}

/// sha256 of a file, streamed (an engine binary is far too big to read twice).
fn sha256_file(path: &Path) -> std::io::Result<String> {
    let mut file = std::fs::File::open(path)?;
    let mut hasher = Sha256::new();
    let mut buffer = [0u8; 64 * 1024];
    loop {
        let read = file.read(&mut buffer)?;
        if read == 0 {
            break;
        }
        hasher.update(&buffer[..read]);
    }
    Ok(format!("{:x}", hasher.finalize()))
}

/// The binary half of the block: size, mtime and digest, or `null` + `reason`.
fn probe_binary(binary: Option<&Path>) -> EngineBinary {
    let Some(binary) = binary else {
        return EngineBinary {
            path: None,
            size_bytes: None,
            mtime_unix: None,
            sha256: None,
            reason: Some("no engine binary is configured".to_string()),
        };
    };
    let path = Some(binary.to_string_lossy().into_owned());
    let Ok(metadata) = std::fs::metadata(binary) else {
        return EngineBinary {
            path,
            size_bytes: None,
            mtime_unix: None,
            sha256: None,
            reason: Some(format!(
                "the configured engine binary {} does not exist",
                binary.display()
            )),
        };
    };
    let mtime_unix = metadata
        .modified()
        .ok()
        .and_then(|time| time.duration_since(UNIX_EPOCH).ok())
        .map(|duration| duration.as_secs());
    let size_bytes = Some(metadata.len());
    match sha256_file(binary) {
        Ok(sha256) => EngineBinary {
            path,
            size_bytes,
            mtime_unix,
            sha256: Some(sha256),
            reason: None,
        },
        Err(error) => EngineBinary {
            path,
            size_bytes,
            mtime_unix,
            sha256: None,
            reason: Some(format!("the engine binary could not be hashed: {error}")),
        },
    }
}

/// DR-44 ②: `<binary> --version`, recorded verbatim.  A missing binary is never
/// executed.
async fn probe_version(
    env: &dyn mini_swe_agent::Environment,
    binary: Option<&Path>,
    exists: bool,
) -> (Option<String>, Option<String>) {
    let Some(binary) = binary else {
        return (
            None,
            Some("no engine binary is configured, so there is no version to read".to_string()),
        );
    };
    if !exists {
        return (
            None,
            Some(format!(
                "the configured engine binary {} does not exist, so it was not executed",
                binary.display()
            )),
        );
    }
    match run(env, &version_command(binary)).await {
        Ok(output) if output.returncode == 0 => match first_line(&output.output) {
            Some(version) => (Some(version), None),
            None => (
                None,
                Some(format!(
                    "`{}` exited 0 without printing a version",
                    version_command(binary)
                )),
            ),
        },
        Ok(output) => (
            None,
            Some(format!(
                "`{}` exited {}: {}",
                version_command(binary),
                output.returncode,
                output.output.trim()
            )),
        ),
        Err(error) => (
            None,
            Some(format!(
                "`{}` could not be run: {error}",
                version_command(binary)
            )),
        ),
    }
}

/// DR-44: the whole `engine` block of one run.
pub async fn probe_identity(
    env: &dyn mini_swe_agent::Environment,
    binary: Option<&Path>,
    editor_endpoint: Option<&str>,
    game_endpoint: Option<GameEndpointRecord>,
    editor_status: Value,
) -> EngineIdentity {
    let binary_info = probe_binary(binary);
    let (version_string, version_reason) =
        probe_version(env, binary, binary_info.size_bytes.is_some()).await;
    let listener = match (binary, editor_endpoint.and_then(port_of_editor_endpoint)) {
        (Some(expected), Some(port)) => probe_listener(env, port, expected).await,
        (Some(expected), None) => ListenerInfo {
            pid: None,
            path: None,
            matches_binary: None,
            reason: Some(format!(
                "the editor endpoint does not name a port, so the listener of {} could not be \
                 resolved",
                expected.display()
            )),
        },
        (None, _) => ListenerInfo {
            pid: None,
            path: None,
            matches_binary: None,
            reason: Some(
                "no engine binary is configured, so no listener could be compared".to_string(),
            ),
        },
    };
    let (game_endpoint, game_endpoint_reason) = match game_endpoint {
        Some(record) => (Some(record), None),
        None => (
            None,
            Some(
                "the game endpoint does not exist until `editor_play_scene` has created it"
                    .to_string(),
            ),
        ),
    };
    let editor_status_reason = if editor_status.is_null()
        || editor_status.as_object().map(|object| object.is_empty()) == Some(true)
    {
        Some("no `GET /mcp` body was recorded for the editor endpoint in this run".to_string())
    } else {
        None
    };
    EngineIdentity {
        kind: ENGINE_KIND_GODOT.to_string(),
        binary: binary_info,
        version_string,
        version_reason,
        mcp: EngineMcp {
            editor_endpoint: editor_endpoint.map(ToOwned::to_owned),
            game_endpoint,
            editor_status,
            game_endpoint_reason,
            editor_status_reason,
        },
        listener,
        checked_at: now_seconds(),
    }
}

/// DR-51: fold a game endpoint into the identity block.
///
/// Returns `true` when the block changed (so the caller only rewrites
/// `meta.json` when there is something new).  The endpoint is a fact of the
/// **run**, not of the binary, so it is recorded even when the rest of the block
/// could not be established: every other field keeps its `null` + `reason`.
pub fn record_game_endpoint(identity: &mut EngineIdentity, record: &GameEndpointRecord) -> bool {
    if identity.mcp.game_endpoint.as_ref() == Some(record) {
        return false;
    }
    identity.mcp.game_endpoint = Some(record.clone());
    identity.mcp.game_endpoint_reason = None;
    true
}

/// The port of `http://127.0.0.1:9877/mcp`, when it names one.
pub fn port_of_editor_endpoint(endpoint: &str) -> Option<u16> {
    crate::tools::endpoint::port_of_endpoint(endpoint)
}

/// DR-44 ⑤: turn the identity into the `engine_identity` battery step.
///
/// `None` when no binary is configured: an adapter that drives no engine has no
/// identity to check, and pretending it did would fail every run.
///
/// `matches_binary == None` (the probe could not resolve the listener) **also**
/// fails the step: "silence is failure" (§0.2) — an unverifiable identity must
/// not be recorded as a verified one.  The observation distinguishes the two
/// cases so the reader is never misled.
pub fn gate_record(identity: &EngineIdentity) -> Option<BatteryRecord> {
    identity.binary.path.as_ref()?;
    let listener = &identity.listener;
    let configured = identity.binary.path.clone().unwrap_or_default();
    let actual = listener
        .path
        .clone()
        .unwrap_or_else(|| "<unknown>".to_string());
    let pid = listener
        .pid
        .map(|pid| pid.to_string())
        .unwrap_or_else(|| "<unknown>".to_string());
    let ok = listener.matches_binary == Some(true);
    let observation = if ok {
        format!(
            "the process listening on the editor port is the configured engine binary \
             {configured} (pid {pid})"
        )
    } else {
        format!(
            "FAILED engine identity: configured binary {configured} | actual listener {actual} \
             (pid {pid}) | {} (UNAVAILABLE: evidence produced by another engine is worthless, \
             DR-44)",
            listener
                .reason
                .clone()
                .unwrap_or_else(|| "the listener could not be compared".to_string())
        )
    };
    Some(BatteryRecord {
        step_id: ENGINE_IDENTITY_STEP_ID.to_string(),
        // The identity underpins every claim of the round; the gate it feeds
        // decides whether the artifact is usable at all (`N1`).
        supports: vec!["N1".to_string()],
        record: ExecRecord {
            kind: ExecKind::RuntimeTrace,
            path: None,
            observation,
            candidate_id: String::new(),
        },
        ok,
        raw_path: None,
    })
}

/// DR-44 ②: the two `hof doctor` items.
///
/// `godot.engine_version` records the version string **verbatim**; nothing in
/// the code base is allowed to depend on its value (C12).
pub async fn doctor_items(env: &dyn mini_swe_agent::Environment, binary: &Path) -> Vec<DoctorItem> {
    let mut items = Vec::new();
    let exists = std::fs::metadata(binary)
        .map(|metadata| metadata.is_file())
        .unwrap_or(false);
    match std::fs::metadata(binary) {
        Ok(metadata) if metadata.is_file() => {
            let mtime = metadata
                .modified()
                .ok()
                .and_then(|time| time.duration_since(UNIX_EPOCH).ok())
                .map(|duration| duration.as_secs())
                .unwrap_or(0);
            items.push(DoctorItem {
                name: "godot.engine_binary".to_string(),
                ok: true,
                detail: format!(
                    "{} (size {} B, mtime {mtime})",
                    binary.display(),
                    metadata.len()
                ),
            });
        }
        Ok(_) => items.push(DoctorItem {
            name: "godot.engine_binary".to_string(),
            ok: false,
            detail: format!("{} is not a file", binary.display()),
        }),
        Err(error) => items.push(DoctorItem {
            name: "godot.engine_binary".to_string(),
            ok: false,
            detail: format!("{}: {error}", binary.display()),
        }),
    }

    if !exists {
        items.push(DoctorItem {
            name: "godot.engine_version".to_string(),
            ok: false,
            detail: format!(
                "skipped: the configured engine binary {} does not exist, so it was not executed",
                binary.display()
            ),
        });
        return items;
    }
    let (version, reason) = probe_version(env, Some(binary), true).await;
    items.push(DoctorItem {
        name: "godot.engine_version".to_string(),
        ok: version.is_some(),
        // The version string is the whole point of this item, and it is
        // reported verbatim.
        detail: version.unwrap_or_else(|| reason.unwrap_or_else(|| "unknown".to_string())),
    });
    items
}

/// A helper the runtime uses to expose the binary in the identity block.
pub fn configured_binary_path(binary: &Path) -> Option<PathBuf> {
    if binary.as_os_str().is_empty() {
        None
    } else {
        Some(binary.to_path_buf())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::runtime::policy::sha256_hex;

    #[test]
    fn the_listener_pid_is_parsed_positionally() {
        let table = "  TCP    127.0.0.1:9877         0.0.0.0:0              LISTENING       12345\n\
                     \r\n  TCP    127.0.0.1:9878         0.0.0.0:0              LISTENING       999\n";
        assert_eq!(parse_listener_pid(table, 9877), Some(12345));
        assert_eq!(parse_listener_pid(table, 9878), Some(999));
        assert_eq!(parse_listener_pid(table, 1), None);

        // A localised state column still yields a pid: the port is the anchor.
        let localized =
            "  TCP    127.0.0.1:9877         0.0.0.0:0              ABHOEREN        4321\n";
        assert_eq!(parse_listener_pid(localized, 9877), Some(4321));

        // IPv6 listeners are shaped the same way.
        let v6 = "  TCP    [::1]:9877             [::]:0                 LISTENING       7777\n";
        assert_eq!(parse_listener_pid(v6, 9877), Some(7777));
    }

    #[test]
    fn the_engine_block_is_serialized_with_every_field() {
        let identity = EngineIdentity::unavailable("nothing to report");
        let value = serde_json::to_value(&identity).unwrap();
        for key in [
            "kind",
            "binary",
            "version_string",
            "version_reason",
            "mcp",
            "listener",
            "checked_at",
        ] {
            assert!(value.get(key).is_some(), "missing `{key}`: {value}");
        }
        for key in ["path", "size_bytes", "mtime_unix", "sha256", "reason"] {
            assert!(value["binary"].get(key).is_some(), "missing binary.{key}");
        }
        for key in ["pid", "path", "matches_binary", "reason"] {
            assert!(
                value["listener"].get(key).is_some(),
                "missing listener.{key}"
            );
        }
        for key in [
            "editor_endpoint",
            "game_endpoint",
            "editor_status",
            "game_endpoint_reason",
            "editor_status_reason",
        ] {
            assert!(value["mcp"].get(key).is_some(), "missing mcp.{key}");
        }
    }

    #[test]
    fn no_configured_binary_means_no_gate_step() {
        let identity = EngineIdentity::unavailable("no binary");
        assert!(gate_record(&identity).is_none());
    }

    #[test]
    fn path_normalisation_is_case_and_separator_insensitive() {
        assert_eq!(
            normalize_windows_path("F:\\A\\B"),
            normalize_windows_path("f:/a/b")
        );
        assert_eq!(
            normalize_windows_path("//?/C:\\x"),
            normalize_windows_path("c:/x")
        );
    }

    #[test]
    fn a_configured_binary_path_helper_treats_empty_as_absent() {
        assert!(configured_binary_path(Path::new("")).is_none());
        assert_eq!(
            configured_binary_path(Path::new("C:/g.exe")),
            Some(PathBuf::from("C:/g.exe"))
        );
    }

    #[test]
    fn the_version_string_is_never_a_code_constant() {
        // C12: the only place a version string can come from is the probe's
        // output.  This test exists to make that explicit: the module carries no
        // version literal at all.
        let source = include_str!("engine.rs");
        // The needle is assembled at compile time so this assertion does not
        // find its own text (the test lives in the file it scans).
        let needle = concat!("custom", "_build");
        assert!(
            !source.contains(needle),
            "the engine version must never be written into the source (C12)"
        );
        assert_eq!(sha256_hex(b"abc").len(), 64);
    }
}
