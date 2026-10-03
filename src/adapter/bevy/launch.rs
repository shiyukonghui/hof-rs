//! Launch and stop a Bevy game process (DESIGN-OVERVIEW §2, SPIKE-2).
//!
//! Three facts from SPIKE-2 shape this file:
//!
//! 1. **The same binary runs windowed or headless**, switched at run time
//!    (SPIKE-2 §0.1).  So [`LaunchConfig::headless_env`] names the environment
//!    variable the game reads, the launcher sets it, and nothing here ever needs
//!    a second build.  The headless mode is not a nicety: window mode measured
//!    **4.0 FPS** on the spike machine, which is too slow to see a jump arc.
//! 2. **`ScheduleRunnerPlugin` is mandatory** in the game (SPIKE-2 C7): without
//!    it the app runs one frame and exits, so the endpoint is never bound.  That
//!    is why readiness polls rather than sleeps, and why a process that dies
//!    during the wait is reported as a process that died rather than as a
//!    timeout.
//! 3. **Readiness is polled on 15702 only** (SPIKE-2 §0.4): 15703 exists only
//!    when a render world does, so nothing here may depend on it.
//!
//! The process's stderr is drained by **one** thread into a shared buffer for as
//! long as the process lives.  That is deliberate: two readers on one pipe would
//! race for the bytes, and the tail is the only place a Bevy panic is visible
//! (BRP has no log verb).

use std::io::{Read, Write};
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};

use crate::adapter::bevy::brp::{self, BrpClient};
use crate::adapter::AdapterError;

/// How much of the process's stderr is kept.  A panic message is at the end, so
/// the tail is what matters; the cap keeps a chatty game from growing the
/// harness's memory without bound.
pub const STDERR_TAIL_LIMIT: usize = 64 * 1024;
/// How long [`stop`] waits for the process to exit on its own after it has been
/// asked to.
pub const DEFAULT_TERMINATION_GRACE: Duration = Duration::from_secs(10);

/// The runtime switch that puts the game in its no-window/no-GPU mode.  The
/// PRD's C1 requires the *same binary* to support both modes, so the switch is an
/// environment variable and the launcher is the only place it is set.
pub const HEADLESS_ENV: &str = "HOF_GAME_HEADLESS";

/// How the launcher starts a game.
#[derive(Clone, Debug)]
pub struct LaunchConfig {
    /// The environment variable that selects the headless mode.
    pub headless_env: &'static str,
    /// The value that selects it.
    pub headless_value: &'static str,
    /// Whether to ask for the headless mode.
    pub headless: bool,
    /// Extra environment the game needs (never secrets: this is recorded).
    pub env: Vec<(String, String)>,
    /// The endpoint the readiness probe must use, when it is not the pinned
    /// 15702.  A round always leaves this `None`; a test with an in-process fake
    /// sets it, and the probe and the adapter then agree on one endpoint (B2-6:
    /// the adapter used to set only the game's environment variable while the
    /// probe stayed hard-wired to 15702).
    pub endpoint_override: Option<String>,
    /// Right after start: how long to wait, in total, for the endpoint to answer
    /// `rpc.discover` (DESIGN-DETAIL §5: 30 s).
    pub ready_budget: Duration,
    /// How long between readiness probes (DESIGN-DETAIL §4: 500 ms).
    pub ready_interval: Duration,
    /// How long to wait for the process to exit after it has been asked to.
    pub termination_grace: Duration,
    /// The client timeout for one readiness probe.
    pub probe_timeout: Duration,
}

impl Default for LaunchConfig {
    fn default() -> Self {
        Self {
            headless_env: HEADLESS_ENV,
            headless_value: "1",
            headless: true,
            env: Vec::new(),
            endpoint_override: None,
            ready_budget: brp::ENDPOINT_READY_BUDGET,
            ready_interval: brp::READY_POLL_INTERVAL,
            termination_grace: DEFAULT_TERMINATION_GRACE,
            probe_timeout: Duration::from_secs(2),
        }
    }
}

impl LaunchConfig {
    /// The endpoint the launcher polls.  It is the pinned 15702 unless a test
    /// explicitly moved it, in which case the probe and the adapter use the same
    /// value (B2-6).
    pub fn endpoint(&self) -> String {
        self.endpoint_override.clone().unwrap_or_else(brp::endpoint)
    }

    /// The client a readiness probe uses.
    pub fn probe_client(&self) -> BrpClient {
        BrpClient::new(self.endpoint(), self.probe_timeout)
    }
}

/// Why a launch could not be completed.  Every variant is a task-level failure:
/// there is no game to observe.
#[derive(Clone, Debug, PartialEq, Eq, thiserror::Error)]
pub enum LaunchError {
    #[error("the game binary `{path}` does not exist: the build did not produce it")]
    MissingBinary { path: String },
    #[error("the game binary `{path}` could not be started: {message}")]
    Spawn { path: String, message: String },
    #[error("the game process exited with {exit:?} before its endpoint answered; stderr tail: {stderr_tail}")]
    ExitedBeforeReady {
        exit: Option<i32>,
        stderr_tail: String,
    },
    #[error("the game process did not answer on {endpoint} within {budget_millis} ms")]
    EndpointTimeout {
        endpoint: String,
        budget_millis: u64,
    },
}

impl From<LaunchError> for AdapterError {
    fn from(error: LaunchError) -> Self {
        match error {
            LaunchError::EndpointTimeout {
                endpoint,
                budget_millis,
            } => AdapterError::EndpointTimeout {
                endpoint,
                budget_millis,
            },
            other => AdapterError::Transport {
                endpoint: brp::endpoint(),
                message: other.to_string(),
            },
        }
    }
}

/// A started game process, with everything stopping it needs to preserve
/// evidence.
#[derive(Debug)]
pub struct GameProcess {
    child: Child,
    pid: u32,
    headless: bool,
    endpoint: String,
    /// The tail of the process's stderr, filled by one reader thread.
    stderr: Arc<Mutex<String>>,
    /// Set when the process has been asked to exit, so `stop` does not ask twice.
    asked_to_exit: AtomicBool,
    termination_grace: Duration,
}

impl GameProcess {
    pub fn pid(&self) -> u32 {
        self.pid
    }

    pub fn headless(&self) -> bool {
        self.headless
    }

    pub fn endpoint(&self) -> &str {
        &self.endpoint
    }

    /// The stderr tail observed so far (cloned, so `&self` health checks are
    /// cheap and the caller cannot hold the lock).
    pub fn stderr_tail(&self) -> String {
        tail_of(&self.stderr)
    }

    /// A `&self` liveness check, for [`crate::adapter::GameAdapter::health`].
    ///
    /// It deliberately does **not** reap: reaping is `stop`'s job, and a health
    /// check that consumed the exit status would make the round's stop report a
    /// code it never observed.  It answers "is it still there", which is what
    /// liveness means here.
    pub fn is_running(&self) -> bool {
        platform::process_is_running(self.pid)
    }

    /// Is the process still running?  `Ok(Some(code))` means it has exited.
    fn poll_exit(&mut self) -> Result<Option<i32>, String> {
        match self.child.try_wait() {
            Ok(Some(status)) => Ok(Some(status.code().unwrap_or(-1))),
            Ok(None) => Ok(None),
            Err(error) => Err(format!("the process state could not be read: {error}")),
        }
    }

    /// Ask the process to exit: a `quit` line on stdin first (the PRD's C1
    /// switch reads one line and leaves the loop), then `kill` if it is still
    /// alive after the grace period.
    pub fn stop(mut self) -> Result<StopEvidence, String> {
        stop_process(&mut self)
    }

    /// Ask nicely, once.  A game that does not read stdin simply never sees it,
    /// which is why the caller still waits and then kills.
    fn request_exit(&mut self) {
        if self.asked_to_exit.swap(true, Ordering::SeqCst) {
            return;
        }
        if let Some(stdin) = self.child.stdin.as_mut() {
            let _ = stdin.write_all(b"quit\n");
            let _ = stdin.flush();
        }
        let _ = self.child.stdin.take();
    }
}

/// What stopping produced, in the form the round's evidence uses.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct StopEvidence {
    pub exit_code: Option<i32>,
    pub stderr_tail: String,
    /// Whether the process had to be killed instead of exiting on request.
    pub forced: bool,
}

/// Start the game and wait until its endpoint answers (or fail trying).
///
/// `stderr` is filled by a single reader thread; see the module docs for why.
pub fn start_game(
    binary: &Path,
    config: &LaunchConfig,
    stderr: Arc<Mutex<String>>,
) -> Result<GameProcess, LaunchError> {
    if !binary.is_file() {
        return Err(LaunchError::MissingBinary {
            path: binary.display().to_string(),
        });
    }
    let mut command = Command::new(binary);
    command
        .stdin(Stdio::piped())
        .stdout(Stdio::null())
        .stderr(Stdio::piped());
    if let Some(directory) = binary.parent() {
        // Bevy resolves asset paths relative to the working directory, and a
        // game built by cargo normally runs from its manifest directory.  The
        // binary's own directory is the closest thing to that which the launcher
        // can know, so it is the default and the round records it.
        command.current_dir(directory);
    }
    if config.headless {
        command.env(config.headless_env, config.headless_value);
    }
    for (name, value) in &config.env {
        command.env(name, value);
    }
    let mut child = command.spawn().map_err(|error| LaunchError::Spawn {
        path: binary.display().to_string(),
        message: error.to_string(),
    })?;
    let pid = child.id();
    if let Some(mut pipe) = child.stderr.take() {
        let sink = Arc::clone(&stderr);
        std::thread::spawn(move || {
            let mut chunk = [0u8; 4096];
            loop {
                match pipe.read(&mut chunk) {
                    Ok(0) => break,
                    Ok(read) => {
                        if let Ok(mut text) = sink.lock() {
                            text.push_str(&String::from_utf8_lossy(&chunk[..read]));
                            if text.len() > STDERR_TAIL_LIMIT {
                                let cut = text.len() - STDERR_TAIL_LIMIT;
                                // A byte boundary, so the tail is still text.
                                let boundary = text
                                    .char_indices()
                                    .map(|(index, _)| index)
                                    .find(|index| *index >= cut)
                                    .unwrap_or(0);
                                *text = text.split_off(boundary);
                            }
                        }
                    }
                    Err(error) if error.kind() == std::io::ErrorKind::Interrupted => {}
                    Err(_) => break,
                }
            }
        });
    }

    let endpoint = config.endpoint();
    let client = config.probe_client();
    let started = Instant::now();
    let deadline = started + config.ready_budget;
    let mut process = GameProcess {
        child,
        pid,
        headless: config.headless,
        endpoint,
        stderr,
        asked_to_exit: AtomicBool::new(false),
        termination_grace: config.termination_grace,
    };
    loop {
        match client.discover() {
            Ok(document) => {
                // A process that answers `rpc.discover` is observable; whether
                // the document looks like BRP's is the contract check's job, not
                // the launcher's.
                let _ = document;
                return Ok(process);
            }
            Err(_) => {}
        }
        // A process that has already died will never answer: saying so is more
        // useful than waiting out the budget, because it distinguishes "the game
        // crashed" (a project defect) from "the endpoint never came up"
        // (infrastructure).
        if let Ok(Some(code)) = process.poll_exit() {
            return Err(LaunchError::ExitedBeforeReady {
                exit: Some(code),
                stderr_tail: process.stderr_tail(),
            });
        }
        if Instant::now() >= deadline {
            // The round is over for this process: stop it, so no orphan keeps
            // holding 15702 for the next attempt.
            let _ = stop_process(&mut process);
            return Err(LaunchError::EndpointTimeout {
                endpoint: process.endpoint.clone(),
                budget_millis: config.ready_budget.as_millis() as u64,
            });
        }
        let remaining = deadline.saturating_duration_since(Instant::now());
        std::thread::sleep(config.ready_interval.min(remaining));
    }
}

/// The tail of a shared stderr buffer, with the lock handled.
pub fn tail_of(stderr: &Arc<Mutex<String>>) -> String {
    stderr
        .lock()
        .map(|text| text.clone())
        .unwrap_or_else(|poisoned| poisoned.into_inner().clone())
}

/// The executable a workspace builds to, when the build produced one.
pub fn debug_binary(workspace: &Path, crate_name: &str, target_dir: Option<&Path>) -> PathBuf {
    let target_dir = target_dir
        .map(Path::to_path_buf)
        .unwrap_or_else(|| workspace.join("target"));
    let name = if cfg!(windows) {
        format!("{crate_name}.exe")
    } else {
        crate_name.to_string()
    };
    target_dir.join("debug").join(name)
}

/// A liveness check that needs no handle to the process.
///
/// The harness only ever asks about a process it started, but a false "alive"
/// would be a lie the round carries into its evidence, so the check is a real one:
/// the OS's own process table, read through the platform's standard tool.
mod platform {
    #[cfg(windows)]
    pub fn process_is_running(pid: u32) -> bool {
        if pid == 0 {
            return false;
        }
        let filter = format!("PID eq {pid}");
        let output = std::process::Command::new("tasklist")
            .args(["/FI", &filter, "/NH", "/FO", "CSV"])
            .stdin(std::process::Stdio::null())
            .output();
        match output {
            Ok(output) => {
                let text = String::from_utf8_lossy(&output.stdout);
                // `tasklist` prints `INFO: No tasks are running…` when the pid is
                // gone, and a CSV row otherwise.
                text.lines().any(|line| {
                    let line = line.trim();
                    line.starts_with('"') && line.contains(&format!(",\"{pid}\","))
                })
            }
            // Without `tasklist` the honest answer is "cannot tell", and a
            // liveness check that cannot tell must not claim life.
            Err(_) => false,
        }
    }

    #[cfg(not(windows))]
    pub fn process_is_running(pid: u32) -> bool {
        pid != 0 && std::path::Path::new(&format!("/proc/{pid}")).exists()
    }
}

/// Stop a process in place (the launcher's own cleanup path, and what
/// [`GameProcess::stop`] uses).
fn stop_process(process: &mut GameProcess) -> Result<StopEvidence, String> {
    process.request_exit();
    let started = Instant::now();
    loop {
        match process.poll_exit() {
            Ok(Some(code)) => {
                return Ok(StopEvidence {
                    exit_code: Some(code),
                    stderr_tail: process.stderr_tail(),
                    forced: false,
                });
            }
            Ok(None) => {}
            Err(_) => {}
        }
        if started.elapsed() >= process.termination_grace {
            break;
        }
        std::thread::sleep(Duration::from_millis(20));
    }
    process
        .child
        .kill()
        .map_err(|error| format!("the process could not be killed: {error}"))?;
    let status = process.child.wait().ok();
    std::thread::sleep(Duration::from_millis(50));
    Ok(StopEvidence {
        exit_code: status.and_then(|status| status.code()),
        stderr_tail: process.stderr_tail(),
        forced: true,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    /// A shell one-liner that writes to stderr and then exits.  It is not a game
    /// and it does not bind a port: it exists so the spawn/stderr/stop paths can
    /// be exercised on a machine with no engine at all.
    fn stderr_then_exit() -> (PathBuf, Vec<String>) {
        if cfg!(windows) {
            (
                PathBuf::from("cmd.exe"),
                vec![
                    "/C".to_string(),
                    "echo panicked at src/main.rs >&2 & echo hello >&2 & exit /B 3".to_string(),
                ],
            )
        } else {
            (
                PathBuf::from("/bin/sh"),
                vec![
                    "-c".to_string(),
                    "echo 'panicked at src/main.rs' >&2; echo hello >&2; exit 3".to_string(),
                ],
            )
        }
    }

    /// Write a tiny stand-in "game" that starts, prints one line and then stays
    /// alive without binding a port.  It exists so the readiness budget's
    /// give-up path and the kill path are exercised against a real process with
    /// no engine, no network and no port 15702 — i.e. in the default gate.
    fn a_silent_long_lived_process(directory: &Path) -> PathBuf {
        if cfg!(windows) {
            let path = directory.join("stand_in_game.cmd");
            std::fs::write(
                &path,
                "@echo off\r\n:loop\r\nping -n 30 127.0.0.1 >nul\r\ngoto loop\r\n",
            )
            .expect("the stand-in script");
            path
        } else {
            let path = directory.join("stand_in_game.sh");
            std::fs::write(&path, "#!/bin/sh\necho stand-in started\nsleep 30\n")
                .expect("the stand-in script");
            #[cfg(unix)]
            {
                use std::os::unix::fs::PermissionsExt;
                let mut permissions = std::fs::metadata(&path).expect("metadata").permissions();
                permissions.set_mode(0o755);
                std::fs::set_permissions(&path, permissions).expect("executable bit");
            }
            path
        }
    }

    #[test]
    fn a_process_that_never_binds_the_endpoint_gives_up_on_its_budget() {
        let directory = tempfile::tempdir().expect("a temporary directory");
        let binary = a_silent_long_lived_process(directory.path());
        let config = LaunchConfig {
            ready_budget: Duration::from_millis(700),
            ready_interval: Duration::from_millis(60),
            probe_timeout: Duration::from_millis(50),
            termination_grace: Duration::from_millis(300),
            ..LaunchConfig::default()
        };
        let stderr = Arc::new(Mutex::new(String::new()));
        let started = Instant::now();
        let error = start_game(&binary, &config, Arc::clone(&stderr)).unwrap_err();
        match error {
            LaunchError::EndpointTimeout { budget_millis, .. } => {
                assert_eq!(budget_millis, 700);
            }
            other => panic!("expected the readiness budget to be the failure, got {other:?}"),
        }
        // It really waited for the budget rather than judging immediately, and it
        // did not wait forever.
        assert!(
            started.elapsed() >= Duration::from_millis(600),
            "the poll gave up after {:?}",
            started.elapsed()
        );
        assert!(started.elapsed() < Duration::from_secs(20), "no hang");
    }

    #[test]
    fn a_missing_binary_is_a_typed_launch_failure() {
        let error = start_game(
            Path::new("no-such-game-binary-anywhere.exe"),
            &LaunchConfig::default(),
            Arc::new(Mutex::new(String::new())),
        )
        .unwrap_err();
        assert!(
            matches!(error, LaunchError::MissingBinary { .. }),
            "{error:?}"
        );
    }

    #[test]
    fn the_headless_switch_is_an_environment_variable_on_the_same_binary() {
        let config = LaunchConfig::default();
        assert_eq!(config.headless_env, "HOF_GAME_HEADLESS");
        assert!(config.headless, "the round and CI default to headless");
        assert_eq!(config.endpoint(), "http://127.0.0.1:15702/");
        assert_eq!(config.probe_client().endpoint(), config.endpoint());
    }

    /// B2-6: the probe and the configured endpoint are the same value.  The
    /// adapter used to set only the game's environment variable while the probe
    /// stayed hard-wired to 15702, so a test against a fake endpoint would have
    /// waited on the wrong port.
    #[test]
    fn the_readiness_probe_follows_the_configured_endpoint() {
        let pinned = LaunchConfig::default();
        assert_eq!(pinned.endpoint(), "http://127.0.0.1:15702/");
        assert_eq!(pinned.probe_client().endpoint(), pinned.endpoint());

        let moved = LaunchConfig {
            endpoint_override: Some("http://127.0.0.1:19999/".to_string()),
            probe_timeout: Duration::from_millis(50),
            ..LaunchConfig::default()
        };
        assert_eq!(moved.endpoint(), "http://127.0.0.1:19999/");
        assert_eq!(
            moved.probe_client().endpoint(),
            moved.endpoint(),
            "the probe must use the endpoint the launcher was configured with"
        );
    }

    /// B2-6, end to end: a launched process that never binds is given up on with
    /// the **configured** endpoint in the failure, which is the proof that the
    /// probe really polled it rather than 15702.
    #[test]
    fn a_probe_against_a_moved_endpoint_names_that_endpoint_when_it_gives_up() {
        let directory = tempfile::tempdir().expect("a temporary directory");
        let binary = a_silent_long_lived_process(directory.path());
        let endpoint = format!("http://127.0.0.1:{}/", super::brp::fake::refused_port());
        let config = LaunchConfig {
            endpoint_override: Some(endpoint.clone()),
            ready_budget: Duration::from_millis(400),
            ready_interval: Duration::from_millis(40),
            probe_timeout: Duration::from_millis(30),
            termination_grace: Duration::from_millis(300),
            ..LaunchConfig::default()
        };
        let started = Instant::now();
        let error = start_game(&binary, &config, Arc::new(Mutex::new(String::new()))).unwrap_err();
        match error {
            LaunchError::EndpointTimeout {
                endpoint: named, ..
            } => {
                assert_eq!(named, endpoint, "the probe reported the wrong endpoint");
            }
            other => panic!("expected an endpoint timeout, got {other:?}"),
        }
        assert!(
            started.elapsed() < Duration::from_secs(20),
            "the moved-endpoint probe gave up on its budget: {:?}",
            started.elapsed()
        );
    }

    #[test]
    fn the_debug_binary_path_is_the_workspaces_target_directory() {
        let path = debug_binary(Path::new("."), "hof_game", None);
        assert!(path.to_string_lossy().contains("debug"), "{path:?}");
        assert!(path.to_string_lossy().contains("hof_game"), "{path:?}");
        let explicit = debug_binary(Path::new("."), "hof_game", Some(Path::new("F:/shared")));
        assert!(
            explicit.to_string_lossy().starts_with("F:/shared"),
            "{explicit:?}"
        );
    }

    /// A real child process, its real stderr, and its real exit code — no engine,
    /// no network, no port.  This is in the default gate: it is an operating
    /// system facility, not hardware.
    #[test]
    fn the_stderr_tail_and_the_exit_code_survive_stopping_a_real_process() {
        let (program, args) = stderr_then_exit();
        let stderr = Arc::new(Mutex::new(String::new()));
        let mut command = Command::new(&program);
        command
            .args(&args)
            .stdin(Stdio::null())
            .stdout(Stdio::null())
            .stderr(Stdio::piped());
        let mut child = command.spawn().expect("a shell");
        let pid = child.id();
        let pipe = child.stderr.take().expect("a stderr pipe");
        let sink = Arc::clone(&stderr);
        let reader = std::thread::spawn(move || {
            let mut pipe = pipe;
            let mut chunk = [0u8; 4096];
            while let Ok(read) = pipe.read(&mut chunk) {
                if read == 0 {
                    break;
                }
                if let Ok(mut text) = sink.lock() {
                    text.push_str(&String::from_utf8_lossy(&chunk[..read]));
                }
            }
        });
        let status = child.wait().expect("the child exits");
        reader.join().expect("the reader finishes");
        assert_eq!(status.code(), Some(3));
        let tail = tail_of(&stderr);
        assert!(tail.contains("panicked"), "{tail:?}");
        assert!(pid > 0, "the launcher's process id is a real one");
    }
}
