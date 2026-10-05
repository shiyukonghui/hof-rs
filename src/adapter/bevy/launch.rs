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

/// Round-2 repair: the variable that carries this launch's **per-launch nonce**.
///
/// Round 2's defect was that a stale game kept answering 15702 while a new one
/// bound the same port (Windows `SO_REUSEADDR`), so readiness proved only
/// *reachability*: the battery read the A0 scaffold's frame counter and reported
/// it as the candidate's behaviour.  A readiness check that proves identity
/// needs a value that belongs to **this** launch and cannot be served by a
/// process that was started before it.  This variable carries that value into
/// the game; `HOF_GAME_PROCESS_NONCE` is the game's copy of it.  Both names are
/// pinned against the scaffold by a test, because two string literals in two
/// crates are the only thing keeping them together.
pub const PROCESS_NONCE_ENV: &str = "HOF_GAME_PROCESS_NONCE";

/// The nonce every launch generates, when the caller did not fix one.
///
/// A UUIDv4 is 122 random bits: a stale process cannot guess the next launch's
/// nonce, so a value that comes back different is proof that the answering
/// process is not the one this launch started.  It is generated **in this
/// process**, before the spawn, so it exists before anything can answer.
pub fn new_process_nonce() -> String {
    uuid::Uuid::new_v4().to_string()
}

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
    /// Round-2 repair: the per-launch nonce the game must publish back.  A round
    /// always leaves this `None` and [`start_game`] generates one; a test fixes
    /// it so the competing listener's wrong answer is a known value.
    pub nonce: Option<String>,
    /// Round-2 repair: the ledger of pids this round has launched.  When it is
    /// set, a pid recorded there that is still alive is **reaped and verified
    /// dead before the port is used again**.
    pub ledger: Option<PathBuf>,
    /// Round-2 repair: the directory the launched image is copied into, so the
    /// shared target stays writable while the game runs.  `None` runs the built
    /// binary in place.
    pub stage_dir: Option<PathBuf>,
    /// Round-2 repair: whether the endpoint must be proven **free** before the
    /// spawn.  A round always leaves this `true`: a listener that already holds
    /// the endpoint is reported at once, which is the clearer failure.  A test
    /// sets it to `false` to drive the **nonce** defence instead — the two
    /// defences are complementary, so both must be exercisable in the gate.
    pub require_free_endpoint: bool,
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
            nonce: None,
            ledger: None,
            stage_dir: None,
            require_free_endpoint: true,
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
    /// Round-2 repair: another process already holds the endpoint, so this
    /// launch cannot be the one that answers it.  Windows' `SO_REUSEADDR` lets
    /// that happen silently; refusing here is what turns it into a fact.
    #[error(
        "port {port} is already in use by pid {holder:?}: a launch cannot bind the endpoint while \
         another process answers it, so this pass would observe that process and not this one"
    )]
    EndpointBusy { port: u16, holder: Option<u32> },
    /// Round-2 repair: the endpoint answered, but the value it serves is not the
    /// nonce this launch published — i.e. the answering process is not the one
    /// this launch started.
    #[error(
        "the endpoint on {endpoint} answered with process nonce {answered:?}, not the nonce \
         {expected:?} this launch published (pid {pid}): the answering process is not the one this \
         round started, so no observation through it describes this pass's game"
    )]
    IdentityMismatch {
        endpoint: String,
        expected: String,
        answered: Option<String>,
        pid: u32,
    },
    #[error(
        "the per-launch nonce could not be read from the endpoint on {endpoint}: {reason} — \
         readiness proves identity, and a game that does not publish the contract's \
         `ProcessNonce` cannot be told apart from a stale session"
    )]
    IdentityUnavailable { endpoint: String, reason: String },
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
    /// Round-2 repair: the per-launch nonce this process was started with, i.e.
    /// the value readiness proved the answering process serves.
    nonce: String,
    /// Round-5 repair (defect RA-4): **what the wire served back** at readiness.
    ///
    /// It is the nonce `world.get_resources` of the contract's `ProcessNonce`
    /// returned for this launch, recorded verbatim next to the value that was put
    /// into the child's environment.  Without it, `identity.verified` could only
    /// say "a launch happened"; with it, the record says *this process answered
    /// with this nonce*.
    answered_nonce: Option<String>,
    /// The file that was actually executed (the staged copy when staging is on),
    /// recorded so "which file ran?" is answerable.
    launch_image: PathBuf,
    /// The ledger this launch was written into, when one was configured.
    ledger: Option<PathBuf>,
    /// What the pre-launch sweep over that ledger did.
    reap: ReapReport,
}

impl GameProcess {
    pub fn pid(&self) -> u32 {
        self.pid
    }

    /// The per-launch nonce readiness verified against the answering process.
    pub fn nonce(&self) -> &str {
        &self.nonce
    }

    /// The nonce the endpoint actually served back at readiness, when readiness
    /// completed.  `None` means the launch never got that far.
    pub fn answered_nonce(&self) -> Option<&str> {
        self.answered_nonce.as_deref()
    }

    /// The file that was executed (a staged copy, when the round stages).
    pub fn launch_image(&self) -> &Path {
        &self.launch_image
    }

    /// What the pre-launch sweep over this round's ledger did.
    pub fn reap_report(&self) -> &ReapReport {
        &self.reap
    }

    /// The ledger this launch was recorded in, when one was configured.
    pub fn ledger(&self) -> Option<&Path> {
        self.ledger.as_deref()
    }

    /// The pid the OS reports as `LISTEN`ing on this process's endpoint, when it
    /// can be read.  This is the second, independent reading of "who answers":
    /// the nonce proves which process answered, this names the process the OS
    /// believes listens, and the two are recorded side by side.
    pub fn answering_pid(&self) -> Option<u32> {
        if !self.endpoint.contains("://") {
            return None;
        }
        let port = self.endpoint.rsplit(':').next()?.trim_end_matches('/');
        port.parse::<u16>().ok().and_then(listener_pid)
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

/// Start the game and wait until **the game this call started** answers (or
/// fail trying).
///
/// `stderr` is filled by a single reader thread; see the module docs for why.
///
/// Round-2 repair.  The order below is the fix and is not reorderable:
///
/// 1. **the nonce is generated here**, before anything is spawned, so it exists
///    before any process can answer;
/// 2. a pid this round recorded as launched and that is **still alive** is
///    reaped, and its death is verified;
/// 3. the endpoint is proven **free** — a listener that already holds it means
///    this launch cannot be the one that answers;
/// 4. the image is staged out of the shared target (task 2: a role's
///    `cargo build` must stay able to replace the built binary while a game is
///    running);
/// 5. only then is the process spawned, with the nonce in its environment;
/// 6. readiness is `rpc.discover` **and** the nonce the wire serves back.
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
    let nonce = config.nonce.clone().unwrap_or_else(new_process_nonce);

    // (2) Nothing this round launched may still be holding the endpoint.
    let mut reap = ReapReport::default();
    if let Some(ledger) = config.ledger.as_deref() {
        reap = reap_ledger(ledger);
        if let Some(reason) = reap.failure.clone() {
            return Err(LaunchError::IdentityUnavailable {
                endpoint: config.endpoint(),
                reason: format!(
                    "a process this round launched could not be reaped before the next launch: \
                     {reason}"
                ),
            });
        }
    }

    // (3) An endpoint that is already in use is not this launch's endpoint.
    let port = port_of_endpoint(&config.endpoint());
    if config.require_free_endpoint {
        if let Some(port) = port {
            if let Some(holder) = listener_pid(port) {
                return Err(LaunchError::EndpointBusy {
                    port,
                    holder: Some(holder),
                });
            }
            if !port_is_free(port) {
                return Err(LaunchError::EndpointBusy { port, holder: None });
            }
        }
    }

    // (4) The image is staged out of the build directory before it is run.
    let launch_image = match config.stage_dir.as_deref() {
        Some(directory) => {
            // A per-launch directory under the configured root: two passes must
            // never write the same image while one of them is running it.
            let per_launch = directory.join(uuid::Uuid::new_v4().to_string());
            match stage_image(binary, &per_launch) {
                Ok(image) => image,
                Err(error) => {
                    return Err(LaunchError::Spawn {
                        path: binary.display().to_string(),
                        message: format!(
                            "the launch image could not be staged into {}: {error}",
                            per_launch.display()
                        ),
                    })
                }
            }
        }
        None => binary.to_path_buf(),
    };
    let mut command = Command::new(&launch_image);
    command
        .stdin(Stdio::piped())
        .stdout(Stdio::null())
        .stderr(Stdio::piped());
    if let Some(directory) = launch_image.parent() {
        // Bevy resolves asset paths relative to the working directory, and a
        // game built by cargo normally runs from its manifest directory.  The
        // binary's own directory is the closest thing to that which the launcher
        // can know, so it is the default and the round records it.
        command.current_dir(directory);
    }
    if config.headless {
        command.env(config.headless_env, config.headless_value);
    }
    // (5) The per-launch nonce travels in the environment, so the game can
    // publish it without the launcher having to rewrite the game's source.
    command.env(PROCESS_NONCE_ENV, &nonce);
    for (name, value) in &config.env {
        command.env(name, value);
    }
    let mut child = command.spawn().map_err(|error| LaunchError::Spawn {
        path: launch_image.display().to_string(),
        message: error.to_string(),
    })?;
    let pid = child.id();
    // The line is written here, immediately after the spawn, because it carries
    // the pid and the pid does not exist one line earlier (defect RA-1: the note
    // used to claim this happened before the spawn, which was never true).  It is
    // still written before readiness, so a crash between here and the first
    // successful probe leaves the next launch able to find and reap the pid.
    if let Some(ledger) = config.ledger.as_deref() {
        let _ = append_ledger(
            ledger,
            &ledger_entry(pid, &config.endpoint(), &nonce, &launch_image),
        );
    }
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
        nonce,
        answered_nonce: None,
        launch_image: launch_image.clone(),
        ledger: config.ledger.clone(),
        reap,
    };
    loop {
        if client.discover().is_ok() {
            // (6) Reachability is not identity.  A stale process answers
            // `rpc.discover` exactly like the new one; the nonce is what tells
            // them apart, and a value that does not match is a refusal, never a
            // reading attributed to this pass's game.
            match read_process_nonce(&client) {
                Ok(answered) if Some(&answered) == Some(&process.nonce) => {
                    // Defect RA-4: the read-back is a fact, so it is recorded.
                    process.answered_nonce = Some(answered);
                    return Ok(process);
                }
                Ok(answered) => {
                    let expected = process.nonce.clone();
                    let _ = stop_process(&mut process);
                    return Err(LaunchError::IdentityMismatch {
                        endpoint: process.endpoint.clone(),
                        expected,
                        answered: Some(answered),
                        pid,
                    });
                }
                Err(reason) => {
                    let _ = stop_process(&mut process);
                    return Err(LaunchError::IdentityUnavailable {
                        endpoint: process.endpoint.clone(),
                        reason,
                    });
                }
            }
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

/// Read the contract's `ProcessNonce` off the wire, or say why not.
///
/// The contract shape is a string field `value` inside the resource document
/// (`ProcessNonce { value: String }`), which is the same shape the other
/// resource surfaces use (`CoinCounter { coins }`, `FrameCounter { frames }`).
/// A bare string is accepted too, because the wire is the engine's and both
/// spellings are a string.
pub fn read_process_nonce(client: &BrpClient) -> Result<String, String> {
    let response = client
        .call(
            "world.get_resources",
            Some(serde_json::json!({
                "resource": crate::adapter::bevy::contract::contract_path("process_nonce")
            })),
        )
        .map_err(|error| format!("the nonce read failed: {error}"))?;
    let value = response.get("value").ok_or_else(|| {
        format!("the nonce reply has no `value` field (got {response}); the contract's `ProcessNonce` was not registered in the game")
    })?;
    if let Some(text) = value.as_str() {
        return Ok(text.to_string());
    }
    if let Some(text) = value.get("value").and_then(serde_json::Value::as_str) {
        return Ok(text.to_string());
    }
    Err(format!(
        "`{}` carries no string nonce (got {value}); a game without the contract's `ProcessNonce` \
         cannot be told apart from a stale session",
        crate::adapter::bevy::contract::contract_path("process_nonce")
    ))
}

/// The port an endpoint string names, when it names one.
pub fn port_of_endpoint(endpoint: &str) -> Option<u16> {
    let rest = endpoint.split("://").nth(1)?;
    let authority = rest.split('/').next()?;
    let port = authority.rsplit(':').next()?;
    port.parse::<u16>().ok()
}

/// Can this process bind the port?  `true` means nothing holds it.
///
/// The bind is attempted and released immediately; `SO_REUSEADDR` is **not**
/// requested, which is what makes a holder visible here even on Windows.
pub fn port_is_free(port: u16) -> bool {
    std::net::TcpListener::bind((brp::BRP_HOST, port)).is_ok()
}

/// The pid currently `LISTEN`ing on a port, read from the OS's own TCP table.
///
/// It is a second, independent reading of "who answers this port": the nonce
/// proves which process *answered*, and this names the process the OS believes
/// *listens*.  A disagreement between the two is itself a finding, which is why
/// both are recorded rather than one replacing the other.
pub fn listener_pid(port: u16) -> Option<u32> {
    let output = std::process::Command::new("netstat")
        .args(["-ano", "-p", "tcp"])
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::null())
        .output()
        .ok()?;
    let table = String::from_utf8_lossy(&output.stdout).into_owned();
    crate::adapter::engine::parse_listener_pid(&table, port)
}

/// Verify that a pid is gone, polling until the grace expires.
pub fn wait_for_pid_death(pid: u32, grace: Duration) -> bool {
    let started = Instant::now();
    while started.elapsed() < grace {
        if !platform::process_is_running(pid) {
            return true;
        }
        std::thread::sleep(Duration::from_millis(25));
    }
    !platform::process_is_running(pid)
}

/// Kill a pid and **verify** that it died.  On Windows the kill takes the whole
/// tree, because a Bevy game can be re-launched by a wrapper and `Child::kill`
/// only reaches the direct child.
pub fn kill_pid_and_verify(pid: u32, grace: Duration) -> Result<(), String> {
    if !platform::process_is_running(pid) {
        return Ok(());
    }
    #[cfg(windows)]
    {
        let _ = std::process::Command::new("taskkill")
            .args(["/F", "/T", "/PID", &pid.to_string()])
            .stdin(Stdio::null())
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .status();
    }
    #[cfg(not(windows))]
    {
        let _ = std::process::Command::new("kill")
            .args(["-9", &pid.to_string()])
            .stdin(Stdio::null())
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .status();
    }
    if wait_for_pid_death(pid, grace) {
        Ok(())
    } else {
        Err(format!(
            "pid {pid} is still alive {} ms after it was killed",
            grace.as_millis()
        ))
    }
}

/// What one reap sweep over a launch ledger did.
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct ReapReport {
    /// The pids the ledger named, in the order it named them.
    pub recorded: Vec<u32>,
    /// The pids that were still alive and were killed.
    pub reaped: Vec<u32>,
    /// The reason a live pid could not be reaped, when one could not.
    pub failure: Option<String>,
    /// The pid that still listens on the ledger's port, when one does.
    pub listener: Option<u32>,
}

/// Reap every pid the ledger records that is still alive.
///
/// The ledger is the round's own record of what **it** launched
/// (`launch-ledger.jsonl`, one launch per line, written immediately after the
/// spawn and before readiness), so a pid in it is a pid this round started:
/// killing it is not "killing a process by name", it is stopping the round's own
/// previous session.  A pid not in the ledger is never touched.
pub fn reap_ledger(ledger: &Path) -> ReapReport {
    let mut report = ReapReport::default();
    let Ok(text) = std::fs::read_to_string(ledger) else {
        return report;
    };
    for line in text.lines() {
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        let Ok(entry) = serde_json::from_str::<serde_json::Value>(line) else {
            continue;
        };
        if let Some(port) = entry.get("port").and_then(serde_json::Value::as_u64) {
            let port = port as u16;
            if let Some(holder) = listener_pid(port) {
                report.listener = Some(holder);
            }
        }
        let Some(pid) = entry.get("pid").and_then(serde_json::Value::as_u64) else {
            continue;
        };
        let pid = pid as u32;
        if pid == 0 || report.recorded.contains(&pid) {
            continue;
        }
        report.recorded.push(pid);
        if !platform::process_is_running(pid) {
            continue;
        }
        report.reaped.push(pid);
        if let Err(reason) = kill_pid_and_verify(pid, DEFAULT_TERMINATION_GRACE) {
            report.failure = Some(reason);
            return report;
        }
    }
    report
}

/// Append one launch to the ledger.
///
/// **The ordering is forced by the data, and the old note claiming otherwise was
/// wrong** (defect RA-1 of `.spec/bevy/ACCEPTANCE-ROUNDS.md`, now fixed here):
/// the line carries the child's pid, and `Child::id()` does not exist before
/// `spawn` returns, so this is written **immediately after the spawn** — before
/// anything can wait on the child, but not before it exists.  What *is* created
/// before the spawn is the nonce (`start_game` step 1), which is why the identity
/// proof survives: a process started earlier cannot know a UUIDv4 this launch
/// generated and passed only through this child's environment, whatever the
/// ledger's own line order is.
pub fn append_ledger(ledger: &Path, entry: &serde_json::Value) -> std::io::Result<()> {
    if let Some(parent) = ledger.parent() {
        std::fs::create_dir_all(parent)?;
    }
    let mut line = serde_json::to_string(entry).unwrap_or_default();
    line.push('\n');
    std::fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(ledger)?
        .write_all(line.as_bytes())
}

/// The ledger line for one launch: the facts a later sweep needs to find and
/// verify the process again.
///
/// It is written **after** the spawn (see [`append_ledger`]) because it can only
/// exist once the child has a pid; it is written before readiness, so a crash
/// between the spawn and a successful readiness still leaves the pid on record
/// for the next launch's sweep to find and reap.
pub fn ledger_entry(
    pid: u32,
    endpoint: &str,
    nonce: &str,
    launch_image: &Path,
) -> serde_json::Value {
    serde_json::json!({
        "pid": pid,
        "endpoint": endpoint,
        "port": port_of_endpoint(endpoint),
        "nonce": nonce,
        "launch_image": launch_image.display().to_string(),
        "launched_at_seconds": std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|duration| duration.as_secs())
            .unwrap_or(0),
        "note": "written by the harness immediately after the spawn (the pid cannot exist before \
                 it) and before readiness; the nonce on this line was generated before the spawn \
                 and travels only in this child's environment. A live pid on this line is this \
                 round's own previous session and is reaped before the next launch",
    })
}

/// Copy the built binary to a per-launch image outside the build directory and
/// return that path.
///
/// Task 2, and it is a measured fact rather than a precaution: a Windows
/// executable that is **running** cannot be opened for writing, but it can be
/// deleted, so `cargo` fails with
/// `failed to remove file … hof_game.exe (os error 5, Access is denied)` when it
/// tries to replace the binary the round's own game is running from.  Round 2
/// measured the workaround at about eight of the Developer's calls.  Running a
/// staged copy means the file `cargo` must replace is never the file that is
/// running.
///
/// The staged name is the same file name, because Bevy's asset resolution and
/// the game's own idea of its executable both key off it.
pub fn stage_image(binary: &Path, directory: &Path) -> std::io::Result<PathBuf> {
    std::fs::create_dir_all(directory)?;
    let name = binary.file_name().ok_or_else(|| {
        std::io::Error::new(
            std::io::ErrorKind::InvalidInput,
            format!("`{}` has no file name", binary.display()),
        )
    })?;
    let image = directory.join(name);
    std::fs::copy(binary, &image)?;
    Ok(image)
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

/// Start a stand-in script **directly**, so a test can hold a real pid it did not
/// go through the launcher for.  It uses the same stdin/stdout/stderr plumbing as
/// the launcher, minus the readiness probe.
///
/// Round-4 repair: it is a `pub(crate)` function rather than a helper inside this
/// file's test module, because the round-game slot and the round-stop sweep are
/// pinned in `mod.rs`'s tests and both need a real process to mean anything.
#[cfg(test)]
pub(crate) fn launch_stand_in(script: &Path) -> GameProcess {
    let mut command = Command::new(script);
    command
        .stdin(Stdio::piped())
        .stdout(Stdio::null())
        .stderr(Stdio::piped());
    if let Some(directory) = script.parent() {
        command.current_dir(directory);
    }
    let child = command.spawn().expect("the stand-in starts");
    let pid = child.id();
    GameProcess {
        child,
        pid,
        headless: true,
        endpoint: String::new(),
        stderr: Arc::new(Mutex::new(String::new())),
        asked_to_exit: AtomicBool::new(false),
        termination_grace: Duration::from_millis(500),
        nonce: String::new(),
        answered_nonce: None,
        launch_image: script.to_path_buf(),
        ledger: None,
        reap: ReapReport::default(),
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

    /// Round-2 repair: a listener that is **already answering on the endpoint**
    /// is not this pass's process, and the launcher must refuse to launch rather
    /// than let it answer the readiness poll.  The plant is a real competing
    /// listener that answers `rpc.discover` exactly as BRP does.
    #[test]
    fn a_competing_listener_on_the_endpoint_refuses_the_launch() {
        let directory = tempfile::tempdir().expect("a temporary directory");
        let binary = a_silent_long_lived_process(directory.path());
        let competitor = FakeEndpoint::competing("something-else-entirely");
        let config = LaunchConfig {
            endpoint_override: Some(competitor.endpoint()),
            ready_budget: Duration::from_millis(400),
            ready_interval: Duration::from_millis(40),
            probe_timeout: Duration::from_millis(60),
            termination_grace: Duration::from_millis(300),
            nonce: Some("this-pass".to_string()),
            ..LaunchConfig::default()
        };
        let started = Instant::now();
        let error = start_game(&binary, &config, Arc::new(Mutex::new(String::new()))).unwrap_err();
        match &error {
            LaunchError::EndpointBusy { port, .. } => {
                assert_eq!(*port, competitor.port(), "the busy port is the endpoint's");
            }
            other => panic!("expected the busy endpoint to refuse the launch, got {other:?}"),
        }
        // It refused because something was listening, not because it waited out
        // the readiness budget.
        assert!(
            started.elapsed() < Duration::from_millis(300),
            "the busy endpoint was reported without waiting for the readiness budget: {:?}",
            started.elapsed()
        );
    }

    /// The identity half of the same defect, in the shape it really has: the
    /// endpoint is **free when the launch starts**, and the stale process
    /// answers afterwards (it was busy, or it lost the race for the port and the
    /// new process bound it silently — Windows `SO_REUSEADDR`).  Readiness must
    /// then fail on the nonce mismatch instead of accepting a reply that came
    /// from a process this launch did not start.
    #[test]
    fn a_listener_that_serves_a_different_nonce_fails_readiness() {
        let directory = tempfile::tempdir().expect("a temporary directory");
        let binary = a_silent_long_lived_process(directory.path());
        let competing = FakeEndpoint::silent("the-previous-session");
        let config = LaunchConfig {
            endpoint_override: Some(competing.endpoint()),
            ready_budget: Duration::from_millis(3_000),
            ready_interval: Duration::from_millis(40),
            probe_timeout: Duration::from_millis(1_000),
            termination_grace: Duration::from_millis(300),
            nonce: Some("this-pass".to_string()),
            // The identity defence is what is under test here, so the free-port
            // preflight is deliberately disabled and the competing listener is
            // allowed to hold the port.
            require_free_endpoint: false,
            ..LaunchConfig::default()
        };
        // The gate opens a moment after the launch has passed its preflight: the
        // answering process exists, but it is not this pass's process.
        let opener = std::thread::spawn(move || {
            std::thread::sleep(Duration::from_millis(60));
            competing.release();
            competing
        });
        let error = start_game(&binary, &config, Arc::new(Mutex::new(String::new()))).unwrap_err();
        let competing = opener.join().expect("the gate thread finishes");
        match &error {
            LaunchError::IdentityMismatch {
                expected,
                answered,
                pid,
                ..
            } => {
                assert_eq!(expected, "this-pass");
                assert_eq!(answered.as_deref(), Some("the-previous-session"));
                assert!(*pid > 0, "the launch names the process it started");
            }
            other => panic!("expected the nonce mismatch to fail readiness, got {other:?}"),
        }
        assert!(
            competing.is_listening(),
            "the competing listener is what the test named: {competing:?}"
        );
    }

    /// The positive control: the endpoint is free, and the listener that answers
    /// serves the nonce this launch published — so readiness succeeds and the
    /// process is returned.  Without this, "readiness checks identity" could be
    /// satisfied by a check that always refuses.
    #[test]
    fn a_listener_that_serves_the_launch_nonce_is_accepted() {
        let directory = tempfile::tempdir().expect("a temporary directory");
        let binary = a_silent_long_lived_process(directory.path());
        // A port that is free at launch time and is then answered by a listener
        // this launch started: the harness spawns the process, and (in this
        // double) the stand-in answers the endpoint with the agreed nonce.
        let port = super::brp::fake::refused_port();
        let agreed = FakeEndpoint::on_port(port, "this-pass");
        let config = LaunchConfig {
            endpoint_override: Some(agreed.endpoint()),
            ready_budget: Duration::from_millis(1_500),
            ready_interval: Duration::from_millis(40),
            probe_timeout: Duration::from_millis(300),
            termination_grace: Duration::from_millis(300),
            nonce: Some("this-pass".to_string()),
            require_free_endpoint: false,
            ..LaunchConfig::default()
        };
        let offender = agreed.endpoint();
        let process = start_game(&binary, &config, Arc::new(Mutex::new(String::new())))
            .unwrap_or_else(|error| panic!("the agreeing listener on {offender}: {error:?}"));
        assert!(process.pid() > 0);
        assert_eq!(process.endpoint(), config.endpoint());
        assert_eq!(process.nonce(), "this-pass");
        let stop = process.stop();
        assert!(stop.is_ok(), "{stop:?}");
    }

    /// A real loopback listener that answers **exactly like BRP** for the two
    /// methods the launcher uses, and serves the process-nonce value it was
    /// built with.
    ///
    /// It exists so the competing-listener defect can be produced in the default
    /// gate with no engine, no GPU and no model: `rpc.discover` answers a
    /// well-formed document, and `world.get_resources` of the contract's nonce
    /// path answers `{"value": {"value": <nonce>}}` — the shape the contract's
    /// `ProcessNonce.value` string has on the wire.
    struct FakeEndpoint {
        addr: std::net::SocketAddr,
        nonce: String,
        stop: Arc<AtomicBool>,
        /// Whether requests are answered at once.  It is a knob because the two
        /// defences need two shapes: a listener that is already answering is
        /// held off by the free-port preflight, while one that answers **after**
        /// the preflight has to be caught by the nonce.
        answering: Arc<AtomicBool>,
        handle: Option<std::thread::JoinHandle<()>>,
    }

    impl std::fmt::Debug for FakeEndpoint {
        fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
            formatter
                .debug_struct("FakeEndpoint")
                .field("addr", &self.addr)
                .field("nonce", &"<redacted: not printed>")
                .finish_non_exhaustive()
        }
    }

    impl FakeEndpoint {
        /// A fake that binds **exactly this port**, which the caller has already
        /// verified is free: the shape of "the port was free at launch, and
        /// something is answering it now".
        fn on_port(port: u16, nonce: &str) -> Self {
            let mut attempts = 0u32;
            let listener = loop {
                match std::net::TcpListener::bind(("127.0.0.1", port)) {
                    Ok(listener) => break listener,
                    Err(error) => {
                        attempts += 1;
                        if attempts > 200 {
                            panic!("port {port} could not be taken by the double: {error}");
                        }
                        std::thread::sleep(Duration::from_millis(10));
                    }
                }
            };
            let addr = listener.local_addr().expect("a bound address");
            Self::serve(listener, addr, nonce)
        }

        /// The accept loop every constructor uses: one `Content-Length`-framed
        /// HTTP request in, one BRP-shaped reply out.
        fn serve(listener: std::net::TcpListener, addr: std::net::SocketAddr, nonce: &str) -> Self {
            let stop = Arc::new(AtomicBool::new(false));
            let answering = Arc::new(AtomicBool::new(true));
            let handle = {
                let stop = Arc::clone(&stop);
                let answering = Arc::clone(&answering);
                let nonce = nonce.to_string();
                std::thread::spawn(move || {
                    listener
                        .set_nonblocking(true)
                        .expect("the double listener is nonblocking");
                    while !stop.load(Ordering::SeqCst) {
                        match listener.accept() {
                            Ok((mut stream, _)) => {
                                if !answering.load(Ordering::SeqCst) {
                                    let deadline = Instant::now() + Duration::from_millis(400);
                                    while !answering.load(Ordering::SeqCst)
                                        && Instant::now() < deadline
                                    {
                                        std::thread::sleep(Duration::from_millis(5));
                                    }
                                }
                                let request = read_http_request(&mut stream);
                                let body = answer(&request, &nonce);
                                let _ = stream.write_all(
                                    format!(
                                        "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\
                                         Content-Length: {}\r\nConnection: close\r\n\r\n{}",
                                        body.len(),
                                        body
                                    )
                                    .as_bytes(),
                                );
                                let _ = stream.flush();
                            }
                            Err(error) if error.kind() == std::io::ErrorKind::WouldBlock => {
                                std::thread::sleep(Duration::from_millis(2));
                            }
                            Err(_) => break,
                        }
                    }
                })
            };
            Self {
                addr,
                nonce: nonce.to_string(),
                stop,
                answering,
                handle: Some(handle),
            }
        }
    }

    impl FakeEndpoint {
        /// A fake on a port of the operating system's choosing.
        fn competing(nonce: &str) -> Self {
            let listener = std::net::TcpListener::bind("127.0.0.1:0").expect("a loopback port");
            let addr = listener.local_addr().expect("a bound address");
            Self::serve(listener, addr, nonce)
        }

        /// A fake that holds the port but answers nothing until `release` is
        /// called — the shape of a stale listener that is busy when the next
        /// launch's preflight runs.
        fn silent(nonce: &str) -> Self {
            let fake = Self::competing(nonce);
            fake.answering.store(false, Ordering::SeqCst);
            fake
        }

        fn release(&self) {
            self.answering.store(true, Ordering::SeqCst);
        }

        fn endpoint(&self) -> String {
            format!("http://{}/", self.addr)
        }

        fn port(&self) -> u16 {
            self.addr.port()
        }

        /// Has the fake answered at least one request?
        fn is_listening(&self) -> bool {
            // The listener is what matters: it holds the port for the whole test.
            self.addr.port() != 0 && !self.stop.load(Ordering::SeqCst)
        }

        /// The nonce this fake serves, for a test that wants to name it.
        #[allow(dead_code)]
        fn nonce(&self) -> &str {
            &self.nonce
        }
    }

    impl Drop for FakeEndpoint {
        fn drop(&mut self) {
            self.stop.store(true, Ordering::SeqCst);
            if let Some(handle) = self.handle.take() {
                let _ = handle.join();
            }
        }
    }

    /// One `Content-Length`-framed HTTP request, read off a blocking stream.
    fn read_http_request(stream: &mut std::net::TcpStream) -> String {
        stream
            .set_read_timeout(Some(Duration::from_millis(500)))
            .expect("a read timeout");
        let mut buffer = Vec::new();
        let mut chunk = [0u8; 1024];
        let mut header_end = None;
        while header_end.is_none() {
            match stream.read(&mut chunk) {
                Ok(0) | Err(_) => break,
                Ok(read) => {
                    buffer.extend_from_slice(&chunk[..read]);
                    header_end = buffer
                        .windows(4)
                        .position(|window| window == b"\r\n\r\n")
                        .map(|position| position + 4);
                }
            }
        }
        let Some(header_end) = header_end else {
            return String::new();
        };
        let headers = String::from_utf8_lossy(&buffer[..header_end]).to_string();
        let length = headers
            .lines()
            .find_map(|line| {
                let (name, value) = line.split_once(':')?;
                name.eq_ignore_ascii_case("content-length")
                    .then(|| value.trim().parse::<usize>().ok())
                    .flatten()
            })
            .unwrap_or(0);
        let mut body = buffer[header_end..].to_vec();
        while body.len() < length {
            match stream.read(&mut chunk) {
                Ok(0) | Err(_) => break,
                Ok(read) => body.extend_from_slice(&chunk[..read]),
            }
        }
        String::from_utf8_lossy(&body).into_owned()
    }

    /// The fake BRP answer for one request body.
    fn answer(request: &str, nonce: &str) -> String {
        use serde_json::{json, Value};
        let parsed: Value = serde_json::from_str(request).unwrap_or(Value::Null);
        let id = parsed.get("id").cloned().unwrap_or(Value::Null);
        let method = parsed.get("method").and_then(Value::as_str).unwrap_or("");
        let value = match method {
            "rpc.discover" => json!({"tools": []}),
            "world.get_resources" => {
                let path = parsed
                    .get("params")
                    .and_then(|params| params.get("resource"))
                    .and_then(Value::as_str)
                    .unwrap_or("");
                if path == crate::adapter::bevy::contract::contract_path("process_nonce") {
                    // The contract's shape: a `value` string inside the reply's
                    // `value` object.
                    json!({"value": {"value": nonce}})
                } else {
                    json!({"value": {"frames": 1}})
                }
            }
            _ => Value::Null,
        };
        json!({"jsonrpc": "2.0", "id": id, "result": value}).to_string()
    }

    /// Round-2 repair: a pid this round recorded in its ledger is **reaped** —
    /// killed and verified dead — before the next launch, and a pid the ledger
    /// never named is left alone.  This is the "reap the previous session" half
    /// of the repair, and it is the half `stop_round_game` cannot be trusted to
    /// have done.
    #[test]
    fn a_pid_this_round_recorded_is_reaped_before_the_next_launch() {
        let directory = tempfile::tempdir().expect("a temporary directory");
        // A marker the reaped process holds (its working directory), so "it died"
        // is checkable even after the process table entry is gone.
        let marker = directory.path().join("marker");
        std::fs::create_dir_all(&marker).expect("a marker directory");
        let script = directory.path().join("recorded.cmd");
        std::fs::write(
            &script,
            "@echo off\r\ncd /d \"%~dp0marker\"\r\n:loop\r\nping -n 30 127.0.0.1 >nul\r\ngoto loop\r\n",
        )
        .expect("a stand-in");
        let recorded = launch_stand_in(&script);
        let pid = recorded.pid();
        assert!(
            super::platform::process_is_running(pid),
            "the recorded stand-in must be alive for this test to mean anything"
        );

        let ledger = directory.path().join("launch-ledger.jsonl");
        append_ledger(
            &ledger,
            &ledger_entry(
                pid,
                &format!("http://127.0.0.1:{}/", super::brp::fake::refused_port()),
                "recorded",
                &script,
            ),
        )
        .expect("the ledger is writable");
        // A second line with a pid that does not exist: "nothing to do".
        append_ledger(
            &ledger,
            &ledger_entry(
                4_000_000_000,
                &format!("http://127.0.0.1:{}/", super::brp::fake::refused_port()),
                "dead",
                &script,
            ),
        )
        .expect("the ledger is writable");

        let report = reap_ledger(&ledger);
        assert!(
            report.reaped.contains(&pid),
            "the recorded pid must be reaped: {report:?}"
        );
        assert!(
            !super::platform::process_is_running(pid),
            "reaping must verify the death, not merely ask for it"
        );
        std::thread::sleep(Duration::from_millis(100));
        assert!(
            std::fs::remove_dir(&marker).is_ok(),
            "the reaped process must really be gone (its working directory is free)"
        );
        drop(recorded);
    }

    /// Defect RA-1, pinned.  The note used to claim the ledger line was written
    /// **before the spawn**, which cannot be true: the line carries the child's
    /// pid and the pid does not exist until `spawn` returns.  The proof that the
    /// ledger is not forgeable rests on the **nonce**, which really is created
    /// before the spawn and travels only in the child's environment — so the
    /// record must state that ordering and not the one that was never true.
    ///
    /// The test asserts both halves: the nonce a launch generates is fixed before
    /// any process exists, and the line the harness writes for that pid says
    /// plainly that it was written after the spawn.
    #[test]
    fn the_ledger_line_is_written_after_the_spawn_and_says_so() {
        let directory = tempfile::tempdir().expect("a temporary directory");
        let ledger = directory.path().join("launch-ledger.jsonl");

        // 1. Before any process: the nonce, which is the ordering that carries the
        //    identity proof.
        let nonce = new_process_nonce();
        assert!(!nonce.trim().is_empty(), "a launch always carries a nonce");

        // 2. A real child, so the pid in the line really exists.
        let mut child = std::process::Command::new("cmd")
            .args(["/C", "ping -n 30 127.0.0.1 >nul"])
            .stdin(Stdio::null())
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn()
            .expect("a stand-in child");
        let pid = child.id();
        let entry = ledger_entry(
            pid,
            "http://127.0.0.1:15702/",
            &nonce,
            Path::new("game.exe"),
        );
        append_ledger(&ledger, &entry).expect("the ledger is writable");

        let text = std::fs::read_to_string(&ledger).expect("the ledger");
        let line: serde_json::Value =
            serde_json::from_str(text.lines().next().expect("one line")).expect("a JSON line");
        assert_eq!(line["pid"].as_u64(), Some(pid as u64));
        assert_eq!(line["nonce"].as_str(), Some(nonce.as_str()));
        let note = line["note"].as_str().expect("the line's own note");
        assert!(
            note.contains("immediately after the spawn"),
            "the note must state the ordering the code really has: {note}"
        );
        assert!(
            !note.contains("before the spawn;"),
            "the note must not claim the line predates a pid that cannot exist: {note}"
        );
        assert!(
            note.contains("generated before the spawn"),
            "and it must still name the value that really is created before the spawn: {note}"
        );

        let _ = child.kill();
        let _ = child.wait();
    }

    /// The control for the test above: a live process the ledger never named is
    /// **not** touched.  "Reap the previous session" must never become "kill
    /// whatever is listed".
    #[test]
    fn a_pid_the_ledger_never_named_is_left_alone() {
        let directory = tempfile::tempdir().expect("a temporary directory");
        let outside = directory.path().join("unrelated.cmd");
        std::fs::write(&outside, "@echo off\r\nping -n 30 127.0.0.1 >nul\r\n")
            .expect("an unrelated stand-in");
        let unrelated = launch_stand_in(&outside);
        let pid = unrelated.pid();
        assert!(super::platform::process_is_running(pid));

        let ledger = directory.path().join("launch-ledger.jsonl");
        append_ledger(
            &ledger,
            &ledger_entry(
                4_000_000_001,
                &format!("http://127.0.0.1:{}/", super::brp::fake::refused_port()),
                "someone-else",
                &outside,
            ),
        )
        .expect("the ledger is writable");

        let report = reap_ledger(&ledger);
        assert!(
            report.reaped.is_empty(),
            "nothing recorded is alive, so nothing may be reaped: {report:?}"
        );
        assert!(
            unrelated.is_running(),
            "the unrelated process is not this round's and must not be touched"
        );
        let _ = unrelated.stop();
    }

    /// Task 2: the process runs a **staged copy** of the binary, so the built
    /// binary in the shared target is never the file that is running — which is
    /// what makes a role's `cargo build` able to replace it while the game runs.
    #[test]
    fn the_launched_image_is_a_staged_copy_and_the_built_binary_is_left_alone() {
        let directory = tempfile::tempdir().expect("a temporary directory");
        let built = directory.path().join("built");
        std::fs::create_dir_all(&built).expect("a built directory");
        let binary = a_silent_long_lived_process(&built);
        let before = std::fs::read(&binary).expect("the built bytes");
        let before_modified = std::fs::metadata(&binary)
            .and_then(|metadata| metadata.modified())
            .expect("a modified time");

        let stage = directory.path().join("launch-image");
        let port = super::brp::fake::refused_port();
        let agreed = FakeEndpoint::on_port(port, "this-pass");
        let config = LaunchConfig {
            endpoint_override: Some(agreed.endpoint()),
            ready_budget: Duration::from_millis(1_500),
            ready_interval: Duration::from_millis(40),
            probe_timeout: Duration::from_millis(300),
            termination_grace: Duration::from_millis(300),
            nonce: Some("this-pass".to_string()),
            require_free_endpoint: false,
            stage_dir: Some(stage.clone()),
            ..LaunchConfig::default()
        };
        let process = start_game(&binary, &config, Arc::new(Mutex::new(String::new())))
            .expect("the agreeing listener is this process's");
        assert!(
            process.launch_image().starts_with(&stage),
            "the executed file must be the staged copy: {}",
            process.launch_image().display()
        );
        assert_eq!(
            std::fs::read(process.launch_image()).expect("the staged bytes"),
            before,
            "the staged copy is the built binary, byte for byte"
        );
        assert_eq!(
            std::fs::metadata(&binary)
                .and_then(|metadata| metadata.modified())
                .ok(),
            Some(before_modified),
            "the built binary must be untouched: a role's build replaces it"
        );
        // The built binary can be replaced **while the game runs**, which is the
        // whole point: this is the write cargo performs at link time.
        std::fs::write(&binary, b"replaced while the game was running")
            .expect("the built binary must be writable while the game runs");
        let _ = process.stop();
    }

    /// Start a stand-in script **directly**, so a test can hold a real pid it
    /// did not go through the launcher for: the "a process this round never
    /// recorded" case.  It is the same helper `mod.rs`'s tests use.
    fn launch_stand_in(script: &Path) -> GameProcess {
        super::launch_stand_in(script)
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
