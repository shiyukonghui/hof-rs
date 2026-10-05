//! DR-43: the two MCP endpoints of the new contract.
//!
//! The engine's native MCP module serves `editor_*`, `project_*` and `os_*` on
//! the editor endpoint (9877).  The **running game is a separate process with
//! its own endpoint**: `editor_play_scene` starts it with an injected
//! `--mcp-port` and reports `endpoint` / `mcp_port` / `mcp_port_source` / `pid`
//! in its reply.  `running_game_*` tools exist **only** there.
//!
//! Routing is therefore a property of the tool name, and it is decided in one
//! place so the tool channel and the adapter cannot disagree.

use serde::{Deserialize, Serialize};

use std::path::{Path, PathBuf};

/// The channel a tool belongs to, derived from its name.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ToolScope {
    /// `editor_*`, `project_*`, `os_*` — served by the editor endpoint.
    Editor,
    /// `running_game_*` — served only by the game endpoint.
    Game,
}

/// The game channel's prefix (DR-42/DR-43).
pub const GAME_CHANNEL_PREFIX: &str = "running_game_";

/// The JSON-RPC path of the MCP module.
pub const MCP_PATH: &str = "/mcp";

/// DR-43: `mcp_port_source` when the port was passed as an explicit argument.
pub const SOURCE_ARGUMENT: &str = "argument";
/// DR-43: `mcp_port_source` when the engine picked a free port itself.
pub const SOURCE_AUTO_FREE_PORT: &str = "auto_free_port";
/// Recorded when the server announces a port but not its provenance.  Writing
/// one of the two documented values instead would be inventing a fact.
pub const SOURCE_UNDECLARED: &str = "undeclared";
/// Recorded when the endpoint is the **engine's own default** on its documented
/// loopback port, with nothing asked for and nothing negotiated: Bevy's
/// `RemoteHttpPlugin::default()` binds 15702 for the main world (SPIKE-2 §0.4),
/// so a Bevy round does not choose a port at all.  It is a third documented
/// value rather than `undeclared` because the provenance *is* known.
pub const SOURCE_ENGINE_DEFAULT: &str = "engine_default";

/// Round-4 repair: the provenance of a record that came from a launch whose
/// answering process was proved by the per-launch nonce.  It is a distinct value
/// rather than `engine_default` because the two claims are different: the port is
/// the engine's default in both cases, but only this one was *verified*.
pub const SOURCE_LAUNCH_VERIFIED: &str = "launch_verified";

/// The endpoint a tool of this name must be sent to.
pub fn scope_of(tool: &str) -> ToolScope {
    if tool.starts_with(GAME_CHANNEL_PREFIX) {
        ToolScope::Game
    } else {
        ToolScope::Editor
    }
}

/// `http://127.0.0.1:<port>/mcp` — the documented loopback form.
pub fn endpoint_for_port(port: u16) -> String {
    format!("http://127.0.0.1:{port}{MCP_PATH}")
}

/// The port of a loopback endpoint, when it carries one explicitly.
pub fn port_of_endpoint(endpoint: &str) -> Option<u16> {
    let authority = endpoint
        .split_once("://")
        .map(|(_, rest)| rest)
        .unwrap_or(endpoint);
    let authority = authority.split('/').next().unwrap_or(authority);
    let (_, port) = authority.rsplit_once(':')?;
    port.parse().ok()
}

/// DR-43: what `editor_play_scene` announced about the game endpoint.
///
/// Round-4 repair: the last three fields are the **proof** half, and they are
/// optional so every existing record serialises exactly as it did before.  Round
/// 3's `meta.json` named a pid that was neither the final battery's nor alive at
/// the end, while only the battery's own `launch.json` carried a proved answering
/// process — the run's metadata had a pid and no way to tell whether it meant
/// anything.  A record written by a launch that proved identity now carries the
/// per-launch nonce it proved and the OS's own reading of the listener, so the
/// run's metadata names a process identity that was **verified** rather than
/// hoped for.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct GameEndpointRecord {
    /// The JSON-RPC URL of the running game.
    pub endpoint: String,
    /// The injected port, when it can be determined.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub port: Option<u16>,
    /// `argument` | `auto_free_port` | `undeclared` (see [`SOURCE_UNDECLARED`]);
    /// since the round-4 repair also [`SOURCE_LAUNCH_VERIFIED`].
    pub source: String,
    /// The game process id, when the engine reported one.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub pid: Option<u32>,
    /// Round-4 repair: the per-launch nonce readiness proved the answering
    /// process serves, when this record came from a launch that proved one.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub nonce: Option<String>,
    /// Round-4 repair: the pid the operating system's own TCP table named as the
    /// listener when readiness finished.  It is the independent, non-tautological
    /// half of the identity proof.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub answering_pid: Option<u32>,
    /// Round-4 repair: `Some(true)` only when readiness refused every reply whose
    /// `ProcessNonce` was not this launch's nonce; `None` when the record came
    /// from a path that proved nothing (a role-announced endpoint, a double).
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub verified: Option<bool>,
}

/// DR-69 ①: the file name a run publishes its game route under.
///
/// The route a run registers lives in that run's process memory, but the roles
/// reach it only through the `hoh tools call` **CLI bridge**, which is a fresh
/// process every time (`src/cli_impl.rs:53` → `bridge::channel_for`).  Road (A)
/// of `TASK-DR69.md` makes the route resolvable across processes: the run
/// publishes the record to this file next to its other artifacts, and a later
/// process adopts it.
pub const GAME_ROUTE_FILE: &str = "game_endpoint.json";

/// DR-69 ①: the environment variable that tells a role process where the run
/// published its game route (`<run dir>/game_endpoint.json`).
pub const GAME_ROUTE_ENV: &str = "HOH_GAME_ROUTE";

/// DR-69 ①: the published route's path inside a run directory.
pub fn game_route_path(run_dir: &Path) -> PathBuf {
    run_dir.join(GAME_ROUTE_FILE)
}

/// DR-69 ①: publish `record` so another process can resolve the game route.
///
/// Written through a temporary file and renamed, so a reader never sees a
/// half-written record.  The caller decides whether a failure is fatal — since
/// DR-71 ① that caller treats it as one, so the temporary file is cleaned up
/// instead of being left next to the route a later attempt would use.
pub fn publish_game_route(path: &Path, record: &GameEndpointRecord) -> std::io::Result<()> {
    if let Some(parent) = path.parent() {
        std::fs::create_dir_all(parent)?;
    }
    let serialized = serde_json::to_string(record).unwrap_or_else(|_| "{}".to_string());
    let temp = path.with_extension("json.tmp-publish");
    let published = (|| -> std::io::Result<()> {
        std::fs::write(&temp, serialized.as_bytes())?;
        if path.exists() {
            std::fs::remove_file(path)?;
        }
        std::fs::rename(&temp, path)
    })();
    if published.is_err() {
        let _ = std::fs::remove_file(&temp);
    }
    published
}

/// DR-69 ①: read a published route, or `None` when nothing is published.
///
/// An unreadable or malformed file is `None`, never a guess: the alternative
/// (sending a `running_game_*` call to an invented port) is exactly what DR-43
/// forbids.
pub fn load_game_route(path: &Path) -> Option<GameEndpointRecord> {
    let raw = std::fs::read_to_string(path).ok()?;
    serde_json::from_str(&raw).ok()
}

/// DR-69 ①: withdraw the published route, so no later process can reach a port
/// whose game has stopped (DR-43's guarantee, one process wider).
pub fn withdraw_game_route(path: &Path) {
    let _ = std::fs::remove_file(path);
}

// ---------------------------------------------------------------------------
// DR-70 ②: a published route is **checked** before it is adopted
// ---------------------------------------------------------------------------

/// DR-70 ②: how old a published record may be before adoption refuses it.
///
/// The window is generous on purpose — a long Developer or Tester phase must not
/// invalidate a live route — so expiry is the **weakest** of the three checks.
/// It exists for the one case the other two cannot see: a leftover file whose
/// port has since been taken by another server and whose pid has since been
/// reused.
pub const ROUTE_MAX_AGE_SECONDS: u64 = 6 * 60 * 60;

/// DR-70 ②: why a published route was **not** adopted.
///
/// The variant is recorded on the channel and travels into the refusal text, so
/// a role that reaches a stale route is told *why* instead of being handed the
/// generic "nothing registered yet" message — and, above all, instead of being
/// handed a transport failure.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum RouteRefusal {
    /// The record is older than [`ROUTE_MAX_AGE_SECONDS`].
    Expired {
        age_seconds: u64,
        max_age_seconds: u64,
    },
    /// The record names a game process that is not running.
    OwnerGone { pid: u32 },
    /// The destination refused the connection.
    Unreachable { endpoint: String },
}

impl RouteRefusal {
    /// The stable, human-readable reason recorded on the channel.
    pub fn reason(&self) -> String {
        match self {
            RouteRefusal::Expired {
                age_seconds,
                max_age_seconds,
            } => format!(
                "the published record is {age_seconds}s old, past the {max_age_seconds}s \
                 freshness window, so it cannot be this round's route"
            ),
            RouteRefusal::OwnerGone { pid } => format!(
                "the game process the record names is not running (pid {pid}), so the route \
                 belongs to an earlier round"
            ),
            RouteRefusal::Unreachable { endpoint } => format!(
                "nothing accepts a connection at {endpoint} (the destination refused it), so \
                 the published route points at a stopped game"
            ),
        }
    }
}

impl std::fmt::Display for RouteRefusal {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter.write_str(&self.reason())
    }
}

/// DR-70 ②: is `pid` a live process on this machine?
///
/// `pid` is **recorded by the engine**, not owned by this crate, so it is a
/// hint: a pid that cannot be validated (see the fallback below) is not treated
/// as proof that the route is stale.  A pid that *is* observed to be gone,
/// however, is decisive — that is the whole point of the check.
///
/// Windows: `OpenProcess` + `GetExitCodeProcess` through three hand-written
/// `kernel32` declarations.  One boolean does not justify a new dependency, and
/// shelling out to `tasklist` would make every `hoh tools call` depend on a
/// locale-bearing subprocess.
///
/// Unix: `kill(pid, 0)` — the portable existence probe.
///
/// Everywhere else the answer is "cannot tell", which never manufactures a
/// refusal.
pub fn process_is_alive(pid: u32) -> bool {
    if pid == 0 {
        return false;
    }
    process_liveness::is_alive(pid)
}

#[cfg(windows)]
mod process_liveness {
    use std::ffi::c_void;

    #[link(name = "kernel32")]
    extern "system" {
        fn OpenProcess(desired_access: u32, inherit_handle: i32, process_id: u32) -> *mut c_void;
        fn GetExitCodeProcess(process: *mut c_void, exit_code: *mut u32) -> i32;
        fn CloseHandle(object: *mut c_void) -> i32;
    }

    /// `PROCESS_QUERY_LIMITED_INFORMATION`: enough to read the exit code, and
    /// less privileged than the full query right.
    const QUERY_LIMITED_INFORMATION: u32 = 0x1000;
    /// Windows reports a running process with this exit code.
    const STILL_ACTIVE: u32 = 259;

    pub fn is_alive(pid: u32) -> bool {
        // SAFETY: the three signatures are the documented `kernel32` ones; the
        // handle is closed on every path that opened it, and no memory is
        // borrowed from the caller.
        unsafe {
            let handle = OpenProcess(QUERY_LIMITED_INFORMATION, 0, pid);
            if handle.is_null() {
                return false;
            }
            let mut exit_code = 0u32;
            let read = GetExitCodeProcess(handle, &mut exit_code);
            CloseHandle(handle);
            read != 0 && exit_code == STILL_ACTIVE
        }
    }
}

#[cfg(unix)]
mod process_liveness {
    extern "C" {
        fn kill(pid: i32, signal: i32) -> i32;
    }

    pub fn is_alive(pid: u32) -> bool {
        if pid > i32::MAX as u32 {
            return false;
        }
        // SAFETY: `kill` with signal 0 performs error checking only and never
        // delivers a signal; the pid is range-checked above.
        unsafe { kill(pid as i32, 0) == 0 }
    }
}

#[cfg(not(any(windows, unix)))]
mod process_liveness {
    /// No portable probe here: refusing on a guess would be worse than the
    /// staleness this check exists to catch.
    pub fn is_alive(_pid: u32) -> bool {
        true
    }
}

/// The `host:port` authority of an endpoint URL, when it carries one.
fn endpoint_authority(endpoint: &str) -> Option<&str> {
    let rest = endpoint
        .split_once("://")
        .map(|(_, rest)| rest)
        .unwrap_or(endpoint);
    let authority = rest.split('/').next().unwrap_or(rest);
    (!authority.is_empty()).then_some(authority)
}

/// DR-70 ②: does the destination **explicitly refuse** a connection?
///
/// Only `ConnectionRefused` counts, and only for a **loopback** destination.
/// Two deliberate limits:
///
/// * A non-loopback authority is never probed.  The documented endpoint form is
///   loopback (`endpoint_for_port`), and off-loopback a refused connect can hang
///   for the operating system's whole SYN timeout — an inconclusive probe must
///   not become a refusal.
/// * Every other error (timeout, resolution failure, permission) is "cannot
///   tell": inventing a refusal out of it would take a working route away from a
///   role.
///
/// The call is a plain blocking `connect`.  On this platform
/// `TcpStream::connect_timeout` reports a **refused loopback connect as
/// `TimedOut`** (measured: `kind=TimedOut raw=None`), so it cannot see the
/// distinction this check exists for; the blocking form reports
/// `ConnectionRefused` (measured: `raw=Some(10061)`, about two seconds, which is
/// the wait the transport failure would have cost anyway).
fn destination_refuses_connections(endpoint: &str) -> bool {
    use std::net::ToSocketAddrs;

    let Some(authority) = endpoint_authority(endpoint) else {
        return false;
    };
    let Ok(addresses) = authority.to_socket_addrs() else {
        return false;
    };
    for address in addresses {
        if !address.ip().is_loopback() {
            continue;
        }
        match std::net::TcpStream::connect(address) {
            Ok(_) => return false,
            Err(error) if error.kind() == std::io::ErrorKind::ConnectionRefused => return true,
            Err(_) => return false,
        }
    }
    false
}

/// DR-70 ②: the age of a published record, in seconds, when it can be measured.
///
/// An unreadable timestamp is `None`, i.e. "cannot tell": a file system that
/// will not report an mtime must not turn into a refusal.
fn route_age_seconds(path: &Path) -> Option<u64> {
    let modified = std::fs::metadata(path).ok()?.modified().ok()?;
    std::time::SystemTime::now()
        .duration_since(modified)
        .ok()
        .map(|age| age.as_secs())
}

/// DR-70 ②: may this published route be adopted?
///
/// Three questions, in the order that produces the most specific answer:
/// **is the record fresh**, **is the game process it names still running**, and
/// **does anything still answer there**.  The caller refuses the route (and keeps
/// DR-43's explicit `game_endpoint_unavailable`) when this returns `Err`.
///
/// What this deliberately does **not** establish: that the endpoint is *this*
/// round's game rather than a different live MCP server that happens to sit at
/// the same address with a live pid.  That is the trust boundary DR-69's R4
/// already names, and it is not closable from a file a role can write.
pub fn validate_published_route(
    path: &Path,
    record: &GameEndpointRecord,
) -> Result<(), RouteRefusal> {
    if let Some(age) = route_age_seconds(path) {
        if age > ROUTE_MAX_AGE_SECONDS {
            return Err(RouteRefusal::Expired {
                age_seconds: age,
                max_age_seconds: ROUTE_MAX_AGE_SECONDS,
            });
        }
    }
    if let Some(pid) = record.pid {
        if !process_is_alive(pid) {
            return Err(RouteRefusal::OwnerGone { pid });
        }
    }
    if destination_refuses_connections(&record.endpoint) {
        return Err(RouteRefusal::Unreachable {
            endpoint: record.endpoint.clone(),
        });
    }
    Ok(())
}

/// DR-55: how many **consecutive transport-layer failures** kill an endpoint.
/// Two, not one: the first failure is still retried as before (a hiccup must not
/// cost a whole round), but a second consecutive one is a verdict.  `smoke-t6`
/// burned about 12 minutes re-attempting a game endpoint that had already
/// stopped answering at the transport layer.
///
/// DR-86 ②: this threshold applies to an endpoint that has **answered at least
/// once**, or that is not inside a readiness window.  See
/// [`COLD_START_DEATH_THRESHOLD`].
pub const ENDPOINT_DEATH_THRESHOLD: u32 = 2;

/// DR-86 ②: how many consecutive transport failures a **never-answered** endpoint
/// tolerates *inside a readiness window*.
///
/// The round of record marked its game endpoint unavailable after **two**
/// transport failures before any `running_game_*` call had succeeded, so every
/// later semantic call was refused with `attempt(s)=0` and the round produced
/// zero behaviour readings: the criterion was unjudgeable rather than failed, and
/// the very evidence the round existed to collect was destroyed by a mechanism
/// whose only job is to notice that a *starting* process is not listening yet.
///
/// A readiness poll is exactly the pattern that means "this process is starting":
/// `editor_play_scene` answered `playing=true`, and the poll that followed is not
/// a verdict about a dead server, it is a wait for a listener that has not bound
/// its port yet.  While such a window is open and the endpoint has never
/// answered, an endpoint tolerates this many consecutive transport failures
/// instead of two.
///
/// The bound is derived, not invented: the documented readiness poll interval is
/// [`crate::tools::reliable::READY_POLL_INTERVAL_MS`] (500 ms), so six failures
/// are three seconds of half-second polls — the window in which a game process
/// that really is starting opens its MCP listener.  It is still a **bound**: a
/// seventh consecutive failure marks the endpoint unavailable, with the true
/// count in `transport_failures_at_mark`, and the refusal keeps saying
/// `game_endpoint_unavailable`.  A transient failure therefore costs a retry; an
/// endpoint that truly never answers still gets the honest failure it deserves.
pub const COLD_START_DEATH_THRESHOLD: u32 = 6;

/// DR-55: the liveness verdict of one endpoint, as a **stable evidence field**.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum EndpointState {
    /// Still being attempted; the streak is below the threshold.
    Alive,
    /// Killed by [`ENDPOINT_DEATH_THRESHOLD`] consecutive transport failures.
    /// Every later call is refused immediately with `UNAVAILABLE`.
    Unavailable,
}

impl Default for EndpointState {
    fn default() -> Self {
        Self::Alive
    }
}

impl EndpointState {
    pub fn code(self) -> &'static str {
        match self {
            EndpointState::Alive => "alive",
            EndpointState::Unavailable => "unavailable",
        }
    }
}

/// DR-55: the recorded liveness of one endpoint.
///
/// The field names are the contract: `endpoint`, `state`, `unavailable`,
/// `consecutive_transport_failures` and `transport_failures_at_mark`.  A consumer
/// must be able to tell "the endpoint was declared dead" from "the tool answered
/// with a business error" without reading prose.
///
/// DR-86 ② adds two evidence fields (both `serde(default)`, so a record written
/// before this change still parses): `successes` — the endpoint answered this
/// many times, so `0` names "it never answered" — and `cold_start_grace`, whether
/// the current window is a readiness wait in which
/// [`COLD_START_DEATH_THRESHOLD`] replaces [`ENDPOINT_DEATH_THRESHOLD`].
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct EndpointLiveness {
    /// The endpoint this verdict is about (its JSON-RPC URL).
    pub endpoint: String,
    /// The stable verdict field.
    pub state: EndpointState,
    /// Whether this endpoint may not be attempted again.
    pub unavailable: bool,
    /// The current run of consecutive transport failures.  A success resets it;
    /// a business error never touches it (DR-56's classification decides).
    pub consecutive_transport_failures: u32,
    /// The streak at the moment the endpoint was marked unavailable, so the
    /// record can always answer "how many failures killed it?".
    pub transport_failures_at_mark: u32,
    /// DR-86 ②: how many times this endpoint has answered.  `0` means the
    /// endpoint has never produced a single answer in this session.
    #[serde(default)]
    pub successes: u32,
    /// DR-86 ②: whether a readiness window is open for this endpoint.
    #[serde(default)]
    pub cold_start_grace: bool,
}

impl EndpointLiveness {
    pub fn new(endpoint: impl Into<String>) -> Self {
        Self {
            endpoint: endpoint.into(),
            state: EndpointState::Alive,
            unavailable: false,
            consecutive_transport_failures: 0,
            transport_failures_at_mark: 0,
            successes: 0,
            cold_start_grace: false,
        }
    }

    /// DR-86 ②: open or close the readiness window for this endpoint.
    pub fn arm_cold_start_grace(&mut self, armed: bool) {
        self.cold_start_grace = armed;
    }

    /// DR-86 ②: how many consecutive transport failures this endpoint tolerates
    /// right now.
    ///
    /// A readiness window on an endpoint that has **never answered** is the one
    /// case in which two failures are not a verdict; everywhere else the DR-55
    /// threshold is unchanged.
    pub fn death_threshold(&self) -> u32 {
        if self.cold_start_grace && self.successes == 0 {
            COLD_START_DEATH_THRESHOLD
        } else {
            ENDPOINT_DEATH_THRESHOLD
        }
    }

    /// Fold one observed call outcome into the state.
    ///
    /// `outcome` is `Ok(())` for any answer — including a JSON-RPC **business
    /// error**, which is an answer, not a transport failure — and `Err(())` for a
    /// transport-layer failure.
    ///
    /// A dead endpoint stays dead and its counter is frozen: the record must say
    /// how many failures killed it, and later refusals are not failures of the
    /// endpoint (nothing was sent).
    pub fn observe(&mut self, outcome: Result<(), ()>) {
        if self.unavailable {
            return;
        }
        match outcome {
            Ok(()) => {
                self.consecutive_transport_failures = 0;
                // DR-86 ②: an answer is what "before its first successful call"
                // is measured against, so it is recorded rather than inferred.
                self.successes += 1;
            }
            Err(()) => {
                self.consecutive_transport_failures += 1;
                if self.consecutive_transport_failures >= self.death_threshold() {
                    self.state = EndpointState::Unavailable;
                    self.unavailable = true;
                    self.transport_failures_at_mark = self.consecutive_transport_failures;
                }
            }
        }
    }

    /// The refusal every later call to a dead endpoint gets.  `UNAVAILABLE` and
    /// the stable field name are both present, so a judge can never read this as
    /// a clean or a business failure.
    pub fn refusal(&self, tool: &str) -> String {
        format!(
            "FAILED tool={tool} attempt(s)=0 code=n/a message=game_endpoint_unavailable: the \
             endpoint {endpoint} was marked {state} after {failures} consecutive transport \
             failures; no request was sent and no retry was made (UNAVAILABLE: this evidence \
             could not be collected) endpoint_state={json}",
            endpoint = self.endpoint,
            state = self.state.code(),
            failures = self.transport_failures_at_mark,
            json = serde_json::to_string(self).unwrap_or_else(|_| "{}".to_string()),
        )
    }
}

/// DR-55: the endpoint a failed call was sent to, when the failure is a
/// transport one.
pub fn transport_endpoint(error: &anyhow::Error) -> Option<String> {
    error
        .downcast_ref::<crate::tools::mcp::McpTransportError>()
        .map(|transport| transport.endpoint.clone())
}

/// DR-55: the refusal a dead endpoint answers with — a typed marker so the
/// retry ring and the readiness poll can recognise "no request was sent" from
/// "the server answered with an error" without parsing a message.
#[derive(Clone, Debug, PartialEq, Eq, thiserror::Error)]
#[error("{message}")]
pub struct McpEndpointUnavailableError {
    /// The verbatim refusal text (it carries `UNAVAILABLE`, the endpoint, the
    /// state and the failure count).
    pub message: String,
    /// The endpoint that was declared unavailable.
    pub endpoint: String,
    /// The recorded liveness verdict at the moment of the refusal.
    pub liveness: EndpointLiveness,
}

impl McpEndpointUnavailableError {
    pub fn new(liveness: EndpointLiveness, tool: &str) -> Self {
        Self {
            message: liveness.refusal(tool),
            endpoint: liveness.endpoint.clone(),
            liveness,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// DR-86 ②: inside a readiness window, an endpoint that has **never
    /// answered** tolerates a bounded streak instead of dying on the second
    /// failure — and when the bound is spent it dies with the true count, so the
    /// honest failure is kept.
    #[test]
    fn a_cold_start_grace_tolerates_a_bounded_streak_and_keeps_the_honest_mark() {
        let mut liveness = EndpointLiveness::new("http://127.0.0.1:63803/mcp");
        liveness.arm_cold_start_grace(true);
        assert_eq!(liveness.successes, 0);
        assert_eq!(liveness.death_threshold(), COLD_START_DEATH_THRESHOLD);

        // The failures the round of record died on are no longer a verdict.
        liveness.observe(Err(()));
        liveness.observe(Err(()));
        assert!(
            !liveness.unavailable,
            "two transport failures inside a readiness window must not kill an endpoint that \
             has never answered: {liveness:?}"
        );
        assert_eq!(liveness.consecutive_transport_failures, 2);

        // Up to the bound minus one: still alive.
        for _ in 2..(COLD_START_DEATH_THRESHOLD - 1) {
            liveness.observe(Err(()));
        }
        assert!(!liveness.unavailable, "{liveness:?}");
        assert_eq!(
            liveness.consecutive_transport_failures,
            COLD_START_DEATH_THRESHOLD - 1
        );

        // The bound-th failure: the bound is real, and the mark records how many
        // failures killed it rather than the old constant.
        liveness.observe(Err(()));
        assert!(liveness.unavailable, "{liveness:?}");
        assert_eq!(
            liveness.transport_failures_at_mark,
            COLD_START_DEATH_THRESHOLD
        );
        assert!(liveness
            .refusal("running_game_get_scene_tree")
            .contains(&format!(
                "{} consecutive transport failures",
                COLD_START_DEATH_THRESHOLD
            )));
    }

    /// DR-86 ②: the grace is scoped to "before its first successful call".
    /// Once the endpoint has answered, the DR-55 two-strike rule is back.
    #[test]
    fn an_endpoint_that_has_answered_is_back_under_the_two_strike_rule() {
        let mut liveness = EndpointLiveness::new("http://127.0.0.1:1/mcp");
        liveness.arm_cold_start_grace(true);
        liveness.observe(Ok(()));
        assert_eq!(liveness.successes, 1);
        assert_eq!(liveness.death_threshold(), ENDPOINT_DEATH_THRESHOLD);

        liveness.observe(Err(()));
        assert!(!liveness.unavailable);
        liveness.observe(Err(()));
        assert!(
            liveness.unavailable,
            "an endpoint that has answered keeps the DR-55 verdict: {liveness:?}"
        );
        assert_eq!(liveness.transport_failures_at_mark, 2);
    }

    /// DR-86 ②: the two evidence fields survive a round trip, and the record
    /// stays readable when they are absent (an older record).
    #[test]
    fn the_cold_start_fields_are_additive_and_default_off() {
        let cold = EndpointLiveness::new("http://127.0.0.1:1/mcp");
        assert!(!cold.cold_start_grace);
        assert_eq!(cold.successes, 0);
        let encoded = serde_json::to_value(&cold).expect("serializable");
        assert_eq!(encoded["cold_start_grace"], serde_json::json!(false));
        assert_eq!(encoded["successes"], serde_json::json!(0));

        let legacy = r#"{"endpoint":"http://127.0.0.1:2/mcp","state":"alive","unavailable":false,
                         "consecutive_transport_failures":1,"transport_failures_at_mark":0}"#;
        let parsed: EndpointLiveness =
            serde_json::from_str(legacy).expect("an older record parses");
        assert_eq!(parsed.consecutive_transport_failures, 1);
        assert_eq!(parsed.successes, 0);
        assert!(!parsed.cold_start_grace);
    }

    /// DR-55: two consecutive transport failures kill the endpoint; a success
    /// resets the streak; a business error is not a transport failure at all.
    #[test]
    fn the_liveness_state_counts_consecutive_transport_failures_only() {
        let mut liveness = EndpointLiveness::new("http://127.0.0.1:1/mcp");
        assert!(!liveness.unavailable);
        assert_eq!(liveness.consecutive_transport_failures, 0);

        // One transport failure: not dead (the first failure still retries).
        liveness.observe(Err(()));
        assert_eq!(liveness.consecutive_transport_failures, 1);
        assert!(!liveness.unavailable);

        // A success resets the streak.
        liveness.observe(Ok(()));
        assert_eq!(liveness.consecutive_transport_failures, 0);

        // Business errors are answers: `Ok` in this fold, they never count.
        for _ in 0..5 {
            liveness.observe(Ok(()));
        }
        assert_eq!(liveness.consecutive_transport_failures, 0);
        assert!(!liveness.unavailable);

        // Two consecutive failures: dead, and the mark records the count.
        liveness.observe(Err(()));
        liveness.observe(Err(()));
        assert!(liveness.unavailable);
        assert_eq!(liveness.transport_failures_at_mark, 2);
        assert_eq!(liveness.state.code(), "unavailable");

        // A dead endpoint stays dead and its mark is frozen.
        liveness.observe(Err(()));
        liveness.observe(Err(()));
        assert_eq!(liveness.transport_failures_at_mark, 2);
        assert_eq!(liveness.consecutive_transport_failures, 2);
    }

    /// DR-55: the refusal text carries the stable field name and the count, so a
    /// reader can tell when the endpoint died and how many failures it took.
    #[test]
    fn the_refusal_names_the_state_and_the_failure_count() {
        let mut liveness = EndpointLiveness::new("http://127.0.0.1:65333/mcp");
        liveness.observe(Err(()));
        liveness.observe(Err(()));
        let text = liveness.refusal("running_game_get_node_property_samples");
        assert!(text.contains("UNAVAILABLE"), "{text}");
        assert!(text.contains("game_endpoint_unavailable"), "{text}");
        assert!(text.contains("endpoint_state"), "{text}");
        assert!(text.contains("2 consecutive transport failures"), "{text}");
        assert!(text.contains("attempt(s)=0"), "{text}");
        assert!(
            text.contains("running_game_get_node_property_samples"),
            "{text}"
        );
    }

    #[test]
    fn the_scope_comes_from_the_channel_prefix() {
        assert_eq!(scope_of("editor_get_errors"), ToolScope::Editor);
        assert_eq!(scope_of("project_get_info"), ToolScope::Editor);
        assert_eq!(scope_of("os_deploy_to_android_device"), ToolScope::Editor);
        assert_eq!(scope_of("running_game_get_scene_tree"), ToolScope::Game);
        // Anything unrecognised stays on the editor endpoint: that endpoint is
        // the one a caller can always be told about.
        assert_eq!(scope_of("not_a_tool"), ToolScope::Editor);
    }

    #[test]
    fn the_loopback_endpoint_round_trips_through_its_port() {
        assert_eq!(endpoint_for_port(9877), "http://127.0.0.1:9877/mcp");
        assert_eq!(port_of_endpoint("http://127.0.0.1:9877/mcp"), Some(9877));
        assert_eq!(port_of_endpoint("127.0.0.1:9999/mcp"), Some(9999));
        assert_eq!(port_of_endpoint("http://127.0.0.1/mcp"), None);
    }

    /// DR-70 ②: a bound-then-released loopback port refuses connections, and the
    /// probe must *see* that — it is the only check that can catch a route whose
    /// pid is still alive but whose game is gone.
    #[test]
    fn a_released_loopback_port_is_recognised_as_refusing_connections() {
        let listener = std::net::TcpListener::bind("127.0.0.1:0").expect("loopback listener");
        let port = listener.local_addr().expect("bound address").port();
        drop(listener);
        assert!(
            destination_refuses_connections(&endpoint_for_port(port)),
            "the destination on port {port} refuses connections; the probe must report it \
             rather than treating the route as adoptable"
        );
    }

    /// DR-70 ②: a destination that answers is *not* refused, and neither is one
    /// the probe cannot conclude about — an inconclusive probe must never take a
    /// working route away from a role.
    #[test]
    fn an_answering_or_unjudgeable_destination_is_not_refused() {
        let listener = std::net::TcpListener::bind("127.0.0.1:0").expect("loopback listener");
        let port = listener.local_addr().expect("bound address").port();
        assert!(!destination_refuses_connections(&endpoint_for_port(port)));
        drop(listener);

        // No port at all: cannot be judged, so it is not reported as a refusal.
        assert!(!destination_refuses_connections("http://127.0.0.1/mcp"));
        assert!(!destination_refuses_connections("not a url"));
    }

    /// DR-70 ②: the liveness probe answers `true` for a process that is running
    /// (this one) and `false` for a pid that cannot be running.
    #[test]
    fn the_process_liveness_probe_separates_a_live_pid_from_a_gone_one() {
        assert!(
            process_is_alive(std::process::id()),
            "the test process is running, so its own pid must read as alive"
        );
        assert!(!process_is_alive(0), "pid 0 is not a live process");

        // A reaped child's pid is gone (Windows may reuse pids eventually, but
        // not before this assertion runs).
        let mut child = std::process::Command::new(std::env::current_exe().expect("test exe"))
            .arg("--help")
            .stdout(std::process::Stdio::null())
            .stderr(std::process::Stdio::null())
            .spawn()
            .expect("the test binary must be runnable");
        let pid = child.id();
        let _ = child.wait();
        assert!(
            !process_is_alive(pid),
            "pid {pid} belonged to a reaped child, so it must read as gone"
        );
    }

    /// DR-70 ②: the refusal text names the reason, so a role is told *why* the
    /// published route was not used.
    #[test]
    fn a_refusal_states_which_check_failed() {
        let expired = RouteRefusal::Expired {
            age_seconds: 100,
            max_age_seconds: 50,
        };
        assert!(expired.reason().contains("100"));
        let gone = RouteRefusal::OwnerGone { pid: 4242 };
        assert!(gone.reason().contains("4242"));
        let unreachable = RouteRefusal::Unreachable {
            endpoint: "http://127.0.0.1:1/mcp".to_string(),
        };
        assert!(unreachable.reason().contains("127.0.0.1:1"));
    }
}
