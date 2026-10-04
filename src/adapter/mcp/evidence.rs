//! The round-evidence layout (DESIGN-DETAIL §6).
//!
//! ```text
//! runs/bevy-<round>/
//!   meta.json                 # exit code, segments, contract/feature/lock hashes
//!   build.log                 # build time and the `Compiling` evidence
//!   launch.json               # headless switch, port, start→ready time
//!   calls/<seq>-<tool>.json   # every MCP→BRP call, raw, with seq + timestamp
//!   readings/<semantic>.json  # the criteria's readings
//!   gate.json                 # the gate verdict and its reasons
//!   qa/                       # the Tester's report and snapshot hashes
//! ```
//!
//! Two hard rules from the requirements are enforced by the code, not by
//! convention:
//!
//! * **`runs/**` is written only under the round's own directory.**  Every
//!   function here takes the repository (or workspace) root as an argument and
//!   returns a path *below* `runs/bevy-<round>/`; the round name is validated
//!   (no separators, no `.`/`..`), so no caller can name its way out.  The test
//!   `writing_a_round_never_touches_the_repository_runs_directory` writes into a
//!   temporary directory and asserts the repository's `runs/` is unchanged.
//! * **Every call is one file with its own sequence number and timestamp**,
//!   because criterion E3's evidence must be the raw MCP→BRP exchange and not a
//!   model-authored summary.

use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

use serde_json::{json, Value};

use crate::adapter::AdapterError;

/// The round directory prefix.
pub const ROUND_DIR_PREFIX: &str = "bevy-";
/// `meta.json`.
pub const META_FILE: &str = "meta.json";
/// `build.log`.
pub const BUILD_LOG_FILE: &str = "build.log";
/// `launch.json`.
pub const LAUNCH_FILE: &str = "launch.json";
/// `gate.json`.
pub const GATE_FILE: &str = "gate.json";
/// The per-call directory.
pub const CALLS_DIR: &str = "calls";
/// The per-reading directory.
pub const READINGS_DIR: &str = "readings";
/// The Tester's directory.
pub const QA_DIR: &str = "qa";

/// The §6 layout's names, so a rename shows up as a test failure.
pub const LAYOUT: &[&str] = &[
    "meta.json",
    "build.log",
    "launch.json",
    "calls/",
    "readings/",
    "gate.json",
    "qa/",
];

/// The three hashes every round records.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct RoundHashes {
    pub contract_sha256: String,
    pub feature_sha256: String,
    pub lock_sha256: String,
}

impl RoundHashes {
    /// The hashes of the current frozen contract/feature set, plus a lockfile
    /// measured from disk (an unreadable lockfile is reported, never hashed as
    /// empty).
    pub fn measure(lockfile: &Path) -> Result<Self, AdapterError> {
        Ok(Self {
            contract_sha256: crate::adapter::bevy::contract::contract_sha256(),
            feature_sha256: crate::adapter::bevy::build::feature_set_sha256(),
            lock_sha256: crate::adapter::bevy::build::lockfile_sha256(lockfile)?,
        })
    }
}

/// Validate a round name.  It becomes a directory component, so anything that
/// could escape the `runs/` root is refused instead of sanitised silently.
pub fn round_name(round: &str) -> Result<String, AdapterError> {
    if round.is_empty()
        || round == "."
        || round == ".."
        || !round
            .chars()
            .all(|c| c.is_ascii_alphanumeric() || c == '-' || c == '_' || c == '.')
    {
        return Err(AdapterError::Malformed(format!(
            "`{round}` is not a usable round name (allowed: ASCII letters, digits, `-`, `_`, `.`)"
        )));
    }
    Ok(format!("{ROUND_DIR_PREFIX}{round}"))
}

/// The round's own directory: `<root>/runs/bevy-<round>`.
pub fn round_dir(root: &Path, round: &str) -> Result<PathBuf, AdapterError> {
    Ok(root.join("runs").join(round_name(round)?))
}

/// A tool name turned into one path component: `world.get_components+watch`
/// keeps its dots and plus, anything else becomes `_`.
pub fn sanitize_tool_name(tool: &str) -> String {
    let sanitized: String = tool
        .chars()
        .map(|c| {
            if c.is_ascii_alphanumeric() || matches!(c, '.' | '-' | '_' | '+') {
                c
            } else {
                '_'
            }
        })
        .collect();
    if sanitized.is_empty() {
        "_".to_string()
    } else {
        sanitized
    }
}

/// `calls/<seq:04>-<tool>.json`.
pub fn call_rel_path(seq: u64, tool: &str) -> String {
    format!("{CALLS_DIR}/{seq:04}-{}.json", sanitize_tool_name(tool))
}

/// `readings/<surface>.json`.
pub fn reading_rel_path(surface: &str) -> String {
    format!("{READINGS_DIR}/{}.json", sanitize_tool_name(surface))
}

/// The current wall-clock time in milliseconds, or 0 if the clock is before the
/// epoch (a clock problem must not panic an evidence writer).
pub fn now_millis() -> u128 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|elapsed| elapsed.as_millis())
        .unwrap_or(0)
}

/// `meta.json`: the exit code, the measured segments, and the three hashes that
/// say which contract/feature set/lockfile this round belongs to.
pub fn meta_json(
    round: &str,
    hashes: &RoundHashes,
    exit_code: Option<i32>,
    segments: &Value,
) -> Value {
    json!({
        "round": round,
        "exit_code": exit_code,
        "segments": segments,
        "contract_sha256": hashes.contract_sha256,
        "feature_sha256": hashes.feature_sha256,
        "lock_sha256": hashes.lock_sha256,
    })
}

/// One MCP→BRP call, raw.
///
/// It is `Serialize` because the battery's observations embed the raw calls: a
/// reading's evidence has to be written out with its document, or the claim "the
/// wire carried this" would depend on the process that made the call still being
/// alive.  It is deliberately **not** `Deserialize`: `layer` is a `&'static str`
/// (it is one of exactly two values), and reading a `String` back into a static
/// is not the same value — a round's evidence is written and inspected, never
/// silently rehydrated into a call record.
#[derive(Clone, Debug, PartialEq, serde::Serialize)]
pub struct CallEvidence {
    /// 1-based call ordinal inside the round.
    pub seq: u64,
    pub tool: String,
    /// `generic` or `semantic`.
    pub layer: &'static str,
    /// The BRP verbs this call issued, in order (never empty for a read).
    pub brp_methods: Vec<String>,
    /// The raw requests, one per BRP call.
    pub requests: Vec<Value>,
    /// The raw responses, one per BRP call.
    pub responses: Vec<Value>,
    /// The tool's result, when it produced one.
    pub result: Option<Value>,
    /// `{"kind":…,"code":…,"message":…}` when the call failed.
    pub error: Option<Value>,
    pub timestamp_ms: u128,
}

impl CallEvidence {
    pub fn ok(&self) -> bool {
        self.error.is_none()
    }

    /// The evidence file's relative path inside the round directory.
    pub fn rel_path(&self) -> String {
        call_rel_path(self.seq, &self.tool)
    }

    /// The file's contents: the raw exchange plus its identity.
    pub fn to_json(&self) -> Value {
        json!({
            "seq": self.seq,
            "tool": self.tool,
            "layer": self.layer,
            "timestamp_ms": self.timestamp_ms,
            "brp_methods": self.brp_methods,
            "requests": self.requests,
            "responses": self.responses,
            "ok": self.ok(),
            "result": self.result,
            "error": self.error,
        })
    }
}

/// Everything one round writes.
#[derive(Clone, Debug)]
pub struct RoundEvidence {
    pub round: String,
    pub hashes: RoundHashes,
    pub exit_code: Option<i32>,
    pub segments: Value,
    pub build_log: String,
    pub launch: Value,
    pub calls: Vec<CallEvidence>,
    /// `(surface, reading)` pairs, written as `readings/<surface>.json`.
    pub readings: Vec<(String, Value)>,
    pub gate: Option<Value>,
}

impl RoundEvidence {
    pub fn new(round: impl Into<String>, hashes: RoundHashes) -> Self {
        Self {
            round: round.into(),
            hashes,
            exit_code: None,
            segments: json!({}),
            build_log: String::new(),
            launch: json!({}),
            calls: Vec::new(),
            readings: Vec::new(),
            gate: None,
        }
    }
}

/// Write one round under `<root>/runs/bevy-<round>/`, creating the directory
/// (and the `calls/`, `readings/`, `qa/` subdirectories).  Returns the round
/// directory it wrote.
pub fn write_round(root: &Path, evidence: &RoundEvidence) -> std::io::Result<PathBuf> {
    let directory = round_dir(root, &evidence.round).map_err(|error| {
        std::io::Error::new(std::io::ErrorKind::InvalidInput, error.to_string())
    })?;
    // A round's directory belongs to **that round**.  `calls/`, `readings/` and
    // the Tester's `qa/` are regenerated wholesale on every write, so a second
    // write of the same round — a re-run, or a battery pass after a repair —
    // cannot leave an earlier write's files behind to be read as this one's
    // evidence.  (Without this, a re-run with fewer calls kept the previous
    // run's `calls/<seq>-<tool>.json` files, and two different tools then shared
    // one sequence number in the directory: exactly the kind of evidence a judge
    // must be able to trust.)
    for sub in [CALLS_DIR, READINGS_DIR, QA_DIR] {
        let path = directory.join(sub);
        if path.exists() {
            std::fs::remove_dir_all(&path)?;
        }
    }
    std::fs::create_dir_all(directory.join(CALLS_DIR))?;
    std::fs::create_dir_all(directory.join(READINGS_DIR))?;
    std::fs::create_dir_all(directory.join(QA_DIR))?;

    write_json(
        &directory.join(META_FILE),
        &meta_json(
            &evidence.round,
            &evidence.hashes,
            evidence.exit_code,
            &evidence.segments,
        ),
    )?;
    std::fs::write(directory.join(BUILD_LOG_FILE), &evidence.build_log)?;
    write_json(&directory.join(LAUNCH_FILE), &evidence.launch)?;
    write_json(
        &directory.join(GATE_FILE),
        &evidence
            .gate
            .clone()
            .unwrap_or_else(|| json!({"applicable": false, "launchable": false, "reasons": []})),
    )?;
    for call in &evidence.calls {
        write_json(&directory.join(call.rel_path()), &call.to_json())?;
    }
    for (surface, reading) in &evidence.readings {
        write_json(&directory.join(reading_rel_path(surface)), reading)?;
    }
    Ok(directory)
}

fn write_json(path: &Path, value: &Value) -> std::io::Result<()> {
    std::fs::write(path, serde_json::to_string_pretty(value)?)
}

/// Every file below a directory, relative and sorted.  Used by the guard test
/// that proves a write into a temporary root cannot touch the repository.
#[cfg(test)]
fn list_tree(root: &Path) -> Vec<String> {
    let mut found = Vec::new();
    let mut stack = vec![root.to_path_buf()];
    while let Some(directory) = stack.pop() {
        let Ok(entries) = std::fs::read_dir(&directory) else {
            continue;
        };
        for entry in entries.flatten() {
            let path = entry.path();
            let relative = path
                .strip_prefix(root)
                .unwrap_or(&path)
                .display()
                .to_string()
                .replace('\\', "/");
            if path.is_dir() {
                found.push(format!("{relative}/"));
                stack.push(path);
            } else {
                found.push(format!(
                    "{relative}:{}",
                    entry.metadata().map(|meta| meta.len()).unwrap_or(0)
                ));
            }
        }
    }
    found.sort();
    found
}

#[cfg(test)]
mod tests {
    use super::*;

    fn hashes() -> RoundHashes {
        RoundHashes {
            contract_sha256: "c".repeat(64),
            feature_sha256: "f".repeat(64),
            lock_sha256: "l".repeat(64),
        }
    }

    fn sample(round: &str) -> RoundEvidence {
        let mut evidence = RoundEvidence::new(round, hashes());
        evidence.exit_code = Some(0);
        evidence.segments = json!({"build_millis": 12_000, "extra": "kept verbatim"});
        evidence.build_log = "Compiling hof_game v0.1.0\n".to_string();
        evidence.launch = json!({"headless": true, "port": 15702, "ready_millis": 620});
        evidence.gate = Some(json!({"applicable": true, "launchable": true, "reasons": []}));
        evidence.calls.push(CallEvidence {
            seq: 1,
            tool: "world.get_components+watch".to_string(),
            layer: "generic",
            brp_methods: vec!["world.get_components+watch".to_string()],
            requests: vec![json!({"method": "world.get_components+watch"})],
            responses: vec![json!({"components": {}})],
            result: Some(json!({"components": {}})),
            error: None,
            timestamp_ms: 1_791_000_000_000,
        });
        evidence.calls.push(CallEvidence {
            seq: 2,
            tool: "bevy_coin_counter".to_string(),
            layer: "semantic",
            brp_methods: vec!["world.get_resources".to_string()],
            requests: vec![json!({"resource": "hof_game::contract::CoinCounter"})],
            responses: vec![json!({"value": {"coins": 1}})],
            result: Some(json!({"coins": 1, "frame": 30})),
            error: None,
            timestamp_ms: 1_791_000_000_001,
        });
        evidence.readings.push((
            "coin_counter".to_string(),
            json!({"kind": "CoinCounter", "failed": false, "value": {"coins": 1}, "frame": 30}),
        ));
        evidence
    }

    #[test]
    fn a_second_write_of_the_same_round_leaves_no_stale_evidence() {
        // The property a judge depends on: the round directory says exactly what
        // *this* round observed.  A re-run that made fewer calls must not keep
        // the earlier run's files — otherwise two exchanges share one sequence
        // number in `calls/`.
        let directory = tempfile::tempdir().expect("a temporary root");
        let root = directory.path();
        let first = sample("round-x");
        write_round(root, &first).expect("the first write");
        std::fs::write(root.join("runs/bevy-round-x/qa/note.txt"), "stale\n").unwrap();
        let mut second = sample("round-x");
        second.calls.truncate(1);
        second.readings.clear();
        let written = write_round(root, &second).expect("the second write");
        let calls: Vec<String> = std::fs::read_dir(written.join("calls"))
            .unwrap()
            .flatten()
            .map(|entry| entry.file_name().to_string_lossy().into_owned())
            .collect();
        assert_eq!(
            calls,
            vec!["0001-world.get_components+watch.json".to_string()],
            "only this write's calls may be present"
        );
        assert!(
            !written.join("qa/note.txt").exists(),
            "the Tester's directory is regenerated, not appended to"
        );
        assert_eq!(
            std::fs::read_dir(written.join("readings")).unwrap().count(),
            0,
            "a write with no readings leaves none behind"
        );
    }

    #[test]
    fn the_layout_is_the_designs_six_names() {
        assert_eq!(
            LAYOUT,
            &[
                "meta.json",
                "build.log",
                "launch.json",
                "calls/",
                "readings/",
                "gate.json",
                "qa/"
            ]
        );
    }

    #[test]
    fn a_round_writes_exactly_the_layout_and_nothing_else() {
        let root = tempfile::tempdir().unwrap();
        let directory = write_round(root.path(), &sample("r7")).unwrap();
        assert_eq!(directory, root.path().join("runs").join("bevy-r7"));
        let files = list_tree(&directory);
        let names: Vec<&str> = files
            .iter()
            .map(|entry| entry.split(':').next().unwrap_or(entry))
            .collect();
        assert!(names.contains(&"meta.json"));
        assert!(names.contains(&"build.log"));
        assert!(names.contains(&"launch.json"));
        assert!(names.contains(&"gate.json"));
        assert!(names.contains(&"calls/"));
        assert!(names.contains(&"readings/"));
        assert!(names.contains(&"qa/"));
        assert!(names.contains(&"calls/0001-world.get_components+watch.json"));
        assert!(names.contains(&"calls/0002-bevy_coin_counter.json"));
        assert!(names.contains(&"readings/coin_counter.json"));
        assert_eq!(
            names
                .iter()
                .filter(|name| !name.ends_with('/'))
                .filter(|name| !name.starts_with("calls/") && !name.starts_with("readings/"))
                .count(),
            4,
            "exactly meta/build.log/launch/gate at the top: {names:?}"
        );
    }

    #[test]
    fn meta_json_carries_the_exit_code_the_segments_and_the_three_hashes() {
        let meta = meta_json("r7", &hashes(), Some(0), &json!({"build_millis": 12000}));
        assert_eq!(meta["round"], json!("r7"));
        assert_eq!(meta["exit_code"], json!(0));
        assert_eq!(meta["segments"]["build_millis"], json!(12000));
        assert_eq!(meta["contract_sha256"], json!("c".repeat(64)));
        assert_eq!(meta["feature_sha256"], json!("f".repeat(64)));
        assert_eq!(meta["lock_sha256"], json!("l".repeat(64)));
    }

    #[test]
    fn every_call_gets_one_file_with_its_sequence_and_timestamp() {
        let root = tempfile::tempdir().unwrap();
        let directory = write_round(root.path(), &sample("r8")).unwrap();
        let first: Value = serde_json::from_str(
            &std::fs::read_to_string(directory.join("calls/0001-world.get_components+watch.json"))
                .unwrap(),
        )
        .unwrap();
        assert_eq!(first["seq"], json!(1));
        assert_eq!(first["layer"], json!("generic"));
        assert_eq!(first["timestamp_ms"], json!(1_791_000_000_000u64));
        assert_eq!(first["ok"], json!(true));
        assert_eq!(first["brp_methods"], json!(["world.get_components+watch"]));
        assert_eq!(
            first["requests"][0]["method"],
            json!("world.get_components+watch")
        );
    }

    #[test]
    fn a_failed_call_records_its_error_and_is_not_ok() {
        let mut evidence = sample("r9");
        evidence.calls.push(CallEvidence {
            seq: 3,
            tool: "bevy_health".to_string(),
            layer: "semantic",
            brp_methods: Vec::new(),
            requests: Vec::new(),
            responses: Vec::new(),
            result: None,
            error: Some(json!({"kind": "no_game_process", "message": "no process is registered"})),
            timestamp_ms: 1,
        });
        let root = tempfile::tempdir().unwrap();
        let directory = write_round(root.path(), &evidence).unwrap();
        let written: Value = serde_json::from_str(
            &std::fs::read_to_string(directory.join("calls/0003-bevy_health.json")).unwrap(),
        )
        .unwrap();
        assert_eq!(written["ok"], json!(false));
        assert_eq!(written["error"]["kind"], json!("no_game_process"));
        assert_eq!(written["result"], Value::Null);
    }

    #[test]
    fn a_round_name_cannot_escape_the_runs_directory() {
        for bad in ["", ".", "..", "a/b", "a\\b", "r1;rm", "r 1"] {
            assert!(round_name(bad).is_err(), "`{bad}` must be refused");
        }
        let root = Path::new("F:/root");
        let inside = round_dir(root, "r1").unwrap();
        assert_eq!(inside, Path::new("F:/root/runs/bevy-r1"));
        assert!(inside.starts_with(root.join("runs")));
        assert_eq!(round_name("r1.2").unwrap(), "bevy-r1.2");
    }

    #[test]
    fn tool_names_are_sanitized_into_one_path_component() {
        assert_eq!(
            sanitize_tool_name("world.get_components+watch"),
            "world.get_components+watch"
        );
        assert_eq!(sanitize_tool_name("bevy_coin_counter"), "bevy_coin_counter");
        assert_eq!(sanitize_tool_name("../../etc/passwd"), ".._.._etc_passwd");
        assert_eq!(sanitize_tool_name(""), "_");
        // The sanitised name may still contain dots (the verb names need them),
        // but it can never be a path: it stays one component inside `calls/`.
        let traversal = call_rel_path(4, "../../x");
        assert_eq!(
            Path::new(&traversal).parent(),
            Some(Path::new(CALLS_DIR)),
            "{traversal}"
        );
        assert_eq!(Path::new(&traversal).components().count(), 2, "{traversal}");
        assert_eq!(
            call_rel_path(4, "rpc.discover"),
            "calls/0004-rpc.discover.json"
        );
    }

    #[test]
    fn a_round_written_into_temporary_space_never_touches_the_repository_runs_directory() {
        let repository_runs = Path::new(env!("CARGO_MANIFEST_DIR")).join("runs");
        let before = list_tree(&repository_runs);
        let root = tempfile::tempdir().unwrap();
        let directory = write_round(root.path(), &sample("guard")).unwrap();
        let after = list_tree(&repository_runs);
        assert_eq!(before, after, "a round write leaked into the repository");
        assert!(
            directory.starts_with(root.path()),
            "the round must live under the root it was given"
        );
        assert!(!directory.starts_with(&repository_runs));
    }

    #[test]
    fn the_hashes_are_measured_from_the_frozen_sources() {
        let root = tempfile::tempdir().unwrap();
        let lock = root.path().join("Cargo.lock");
        std::fs::write(&lock, b"# lock\n").unwrap();
        let measured = RoundHashes::measure(&lock).unwrap();
        assert_eq!(
            measured.contract_sha256,
            crate::adapter::bevy::contract::contract_sha256()
        );
        assert_eq!(
            measured.feature_sha256,
            crate::adapter::bevy::build::feature_set_sha256()
        );
        assert_eq!(
            measured.lock_sha256,
            crate::runtime::policy::sha256_hex(b"# lock\n")
        );
        assert!(RoundHashes::measure(&root.path().join("absent.lock")).is_err());
    }

    #[test]
    fn the_evidence_module_only_ever_writes_below_the_root_it_is_given() {
        // The forbidden-zone self-check.  `runs/` may only be joined onto a root
        // the caller passed in, so the module's production code must have exactly
        // one such join, inside `round_dir`, and no absolute path of its own.
        let source = include_str!("evidence.rs");
        let (production, tests) = source
            .split_once("mod tests {")
            .expect("this module has its test module");
        assert!(
            !tests.is_empty(),
            "the split must find the test module, not the production code"
        );
        assert_eq!(
            production.matches("join(\"runs\")").count(),
            1,
            "the only `runs/` join must be the one in `round_dir`"
        );
        let drive = format!("{}:\\", 'F');
        assert!(
            !production.contains(&drive),
            "an absolute build-machine path must never be hard-coded"
        );
    }
}
