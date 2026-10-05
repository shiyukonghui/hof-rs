//! DR-57 — the **request-counting** test for "zero requests after the endpoint is
//! declared dead".
//!
//! ## Why this file exists (the defect it closes)
//!
//! DR-55 promised that once a game endpoint has been declared dead, every later
//! call issues **zero** requests and zero retries.  The batch that implemented it
//! argued for that from `EndpointLiveness.consecutive_transport_failures` staying
//! at 2 — "the count stops growing, so no request was sent".  That argument is
//! **circular**: `EndpointLiveness::observe` returns immediately once
//! `unavailable` is set (`src/tools/endpoint.rs`), so the counter is *frozen by
//! construction*.  The independent acceptance of that batch (DEF-1) planted
//! "still send one request after death" and the implementer's own test stayed
//! **green**; only the verifier's hand-written counting test went red.
//!
//! ## Where the counter sits, and why that is not circular
//!
//! The counter here is **not** inside the production code and **not** on any path
//! the liveness gate can short-circuit.  It is the TCP **accept count of a live
//! loopback double**: the double counts every connection the kernel hands it, and
//! a connection can only exist because a real HTTP attempt reached the endpoint.
//! The socket layer is *below* `McpChannel::call_with_meta`, below the
//! `liveness.unavailable` early return and below `McpClient::post` — so a request
//! sent after the verdict is counted no matter which production line sends it.
//! The count is taken from the endpoint's side, so nothing in the implementation
//! can decide to skip it.
//!
//! The invariant the test asserts is exactly the DR-55 promise:
//!
//! > after the endpoint is declared dead, the accept count does not move,
//!
//! and it is measured non-vacuously: the very same double counts the `2` real
//! connections that killed the endpoint, so "0 additional" is a measured zero,
//! not an unobserved one.  If a later call sends even **one** request — with or
//! without retries — the double accepts it and the test fails.
//!
//! Everything here is offline: one loopback port the kernel assigns
//! (`127.0.0.1:0`), no Godot, no engine port, no network.

mod common;

use std::io::{Read, Write};
use std::net::{SocketAddr, TcpListener, TcpStream};
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Arc;
use std::thread::JoinHandle;
use std::time::Duration;

use hof_rs::model::Role;
use hof_rs::tools::endpoint::{GameEndpointRecord, SOURCE_AUTO_FREE_PORT};
use hof_rs::tools::reliable::{call_with_retries, McpFailure};
use hof_rs::tools::{McpChannel, ToolChannel};
use serde_json::{json, Value};

/// The two behaviours the double can be switched between.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum Mode {
    /// Accept, count, then close without answering a byte: the client sees a
    /// transport-layer failure (the `smoke-t6` "status line never arrived"
    /// shape).  This is what kills the endpoint.
    DropWithoutAnswering,
    /// Answer every request with a valid JSON-RPC `result`.
    Answer,
}

impl Mode {
    fn as_usize(self) -> usize {
        match self {
            Mode::DropWithoutAnswering => 0,
            Mode::Answer => 1,
        }
    }

    fn from_usize(value: usize) -> Self {
        match value {
            1 => Mode::Answer,
            _ => Mode::DropWithoutAnswering,
        }
    }
}

/// A live loopback JSON-RPC endpoint that **counts connections at accept time**.
///
/// The count is incremented in the accept path itself, immediately after the
/// "stop" flag is read, so it cannot be skipped by any application-level
/// decision — including DR-55's early return.  The listener runs in
/// non-blocking-with-timeout mode and is stopped with a flag (never by a
/// self-connect), so `accepted` counts **only** connections a caller opened.
struct CountingJsonRpc {
    addr: SocketAddr,
    /// Connections accepted from a caller.
    accepted: Arc<AtomicUsize>,
    mode: Arc<AtomicUsize>,
    stop_signal: Arc<AtomicUsize>,
    handle: Option<JoinHandle<()>>,
}

impl CountingJsonRpc {
    fn start() -> Self {
        let listener = TcpListener::bind("127.0.0.1:0").expect("loopback listener");
        let addr = listener.local_addr().unwrap();
        // A non-blocking accept loop with a 2 ms back-off is how the loop notices
        // the stop flag: it never needs a wake-up connection, which would
        // otherwise be counted as a request.
        listener
            .set_nonblocking(true)
            .expect("a non-blocking listener");
        let accepted = Arc::new(AtomicUsize::new(0));
        let mode = Arc::new(AtomicUsize::new(0));
        let stop_signal = Arc::new(AtomicUsize::new(0));
        let thread_accepted = accepted.clone();
        let thread_mode = mode.clone();
        let thread_stop = stop_signal.clone();
        let handle = std::thread::spawn(move || {
            while thread_stop.load(Ordering::SeqCst) == 0 {
                match common::accept_blocking(&listener) {
                    Some(stream) => {
                        // THE COUNTER: one real connection reached this endpoint.
                        thread_accepted.fetch_add(1, Ordering::SeqCst);
                        if Mode::from_usize(thread_mode.load(Ordering::SeqCst))
                            == Mode::DropWithoutAnswering
                        {
                            drop(stream);
                        } else {
                            serve_one(stream);
                        }
                    }
                    None => {
                        if thread_stop.load(Ordering::SeqCst) != 0 {
                            break;
                        }
                        std::thread::sleep(Duration::from_millis(2));
                    }
                }
            }
        });
        Self {
            addr,
            accepted,
            mode,
            stop_signal,
            handle: Some(handle),
        }
    }

    fn url(&self) -> String {
        format!("http://{}/mcp", self.addr)
    }

    fn port(&self) -> u16 {
        self.addr.port()
    }

    /// How many connections a caller has actually opened to this endpoint.
    fn accepted(&self) -> usize {
        self.accepted.load(Ordering::SeqCst)
    }

    fn set_mode(&self, mode: Mode) {
        self.mode.store(mode.as_usize(), Ordering::SeqCst);
    }

    /// Set the stop flag and join the accept loop.  No connection is created, so
    /// the counter is untouched.
    fn stop(&mut self) {
        self.stop_signal.store(1, Ordering::SeqCst);
        if let Some(handle) = self.handle.take() {
            let _ = handle.join();
        }
    }
}

impl Drop for CountingJsonRpc {
    fn drop(&mut self) {
        self.stop();
    }
}

/// A minimal HTTP/1.1 JSON-RPC responder: read one request, answer with a
/// `result`, close.  One connection, one request — never a long-lived session, so
/// every attempt is a countable connection.
fn serve_one(mut stream: TcpStream) {
    let _ = stream.set_read_timeout(Some(Duration::from_secs(5)));
    let mut buffer = Vec::new();
    let mut chunk = [0u8; 4096];
    loop {
        let read = match stream.read(&mut chunk) {
            Ok(0) => return,
            Ok(read) => read,
            Err(_) => return,
        };
        buffer.extend_from_slice(&chunk[..read]);
        let Some(header_end) = find(&buffer, b"\r\n\r\n") else {
            continue;
        };
        let headers = String::from_utf8_lossy(&buffer[..header_end]).to_string();
        let length = headers
            .lines()
            .find_map(|line| {
                let (name, value) = line.split_once(':')?;
                name.eq_ignore_ascii_case("content-length")
                    .then(|| value.trim().parse::<usize>().unwrap_or(0))
            })
            .unwrap_or(0);
        if buffer.len() < header_end + 4 + length {
            continue;
        }
        let body = String::from_utf8_lossy(&buffer[header_end + 4..header_end + 4 + length]);
        let request: Value = serde_json::from_str(&body).unwrap_or(json!({}));
        let id = request.get("id").cloned().unwrap_or(json!(1));
        let reply = json!({"jsonrpc": "2.0", "id": id, "result": {"tree": {"name": "Main"}}});
        let payload = reply.to_string();
        let response = format!(
            "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}",
            payload.len(),
            payload
        );
        let _ = stream.write_all(response.as_bytes());
        let _ = stream.flush();
        return;
    }
}

fn find(haystack: &[u8], needle: &[u8]) -> Option<usize> {
    haystack
        .windows(needle.len())
        .position(|window| window == needle)
}

/// A loopback port that was bound and then closed: a channel constructor needs an
/// editor endpoint, and this test never calls it.
fn a_closed_loopback_endpoint() -> String {
    let listener = TcpListener::bind("127.0.0.1:0").expect("loopback listener");
    let port = listener.local_addr().unwrap().port();
    drop(listener);
    format!("http://127.0.0.1:{port}/mcp")
}

fn game_record(endpoint: String, port: u16) -> GameEndpointRecord {
    GameEndpointRecord {
        endpoint,
        port: Some(port),
        source: SOURCE_AUTO_FREE_PORT.to_string(),
        pid: Some(4242),
        nonce: None,
        answering_pid: None,
        verified: None,
    }
}

/// One call with a **zero-delay** ring, so the test measures request counts, not
/// wall time.
async fn call_game(
    channel: &McpChannel,
    tool: &str,
    max_retries: u32,
) -> Result<Value, McpFailure> {
    call_with_retries(
        channel,
        Role::Developer,
        tool,
        json!({}),
        max_retries,
        0,
        None,
    )
    .await
}

/// DR-57 / DR-55 ⑤ — **counting** proof that a dead endpoint sends nothing.
///
/// The counter is the loopback double's accept count, i.e. the layer that really
/// issues the HTTP attempt, below every early return in the production code.  The
/// test therefore distinguishes the two things DR-55's old test could not:
///
/// * "zero requests after death" (the design) — the count does not move; and
/// * "zero *retries* after death but one request still sent" (the DEF-1 plant) —
///   the count moves, and this test goes red.
///
/// It also fails when the dead-endpoint guard is removed entirely: with a retry
/// budget of 3, each call opens one countable connection per attempt.
#[tokio::test]
async fn a_dead_endpoint_sends_zero_requests_to_the_transport_layer() {
    let editor_endpoint = a_closed_loopback_endpoint();

    let double = CountingJsonRpc::start();
    double.set_mode(Mode::DropWithoutAnswering);
    let game_endpoint = double.url();

    // DR-55's own setup: a game client that does *not* retry internally, so each
    // attempt is exactly one countable connection.
    let channel = McpChannel::new(editor_endpoint, 5, 0);
    channel
        .register_game_endpoint(game_record(game_endpoint.clone(), double.port()))
        .await
        .expect("registration");

    // ---- Kill the endpoint with real transport failures ---------------------
    // Two consecutive transport failures mark it unavailable (the threshold).
    for round in 1..=2 {
        let failure = call_game(&channel, "running_game_get_scene_tree", 0)
            .await
            .expect_err("a black-holing endpoint cannot answer");
        assert_eq!(
            failure.attempts, 1,
            "round {round}: the failure must be a real one-attempt transport failure"
        );
    }
    let state = channel
        .endpoint_state(&game_endpoint)
        .expect("the game endpoint has a recorded state");
    assert!(
        state.unavailable,
        "two consecutive transport failures must kill the endpoint: {state:?}"
    );

    // The measurement's **own non-vacuity control**: the double really did accept
    // the two connections that killed it.  A counter that cannot move would make
    // the assertion below meaningless.
    let accepted_at_death = double.accepted();
    assert_eq!(
        accepted_at_death, 2,
        "the double must have counted the two connections that killed the endpoint; \
         a counter that never moves cannot prove anything"
    );

    // ---- Later calls must issue ZERO requests -------------------------------
    // The endpoint is switched to a **fully healthy** answerer.  Nothing but the
    // liveness verdict stops a request from being sent now: if one were sent, the
    // healthy double would answer the call successfully, and the connection would
    // be counted.  A budget of 3 extra retries changes nothing.
    double.set_mode(Mode::Answer);

    for call in 1..=3 {
        let failure = call_game(&channel, "running_game_get_node_property_samples", 3)
            .await
            .expect_err("a dead endpoint stays dead, even with a healthy peer");
        let observation = failure.observation();
        assert!(
            observation.contains("UNAVAILABLE")
                && observation.contains("game_endpoint_unavailable"),
            "call {call}: the dead endpoint must answer its typed refusal: {observation}"
        );
        assert_eq!(
            failure.attempts, 1,
            "call {call}: a dead endpoint is refused once, never retried: {observation}"
        );
    }

    // THE assertion: the transport layer that really issues the HTTP attempt saw
    // **no** new connection.  This is a measured zero, not an unobserved one.
    assert_eq!(
        double.accepted(),
        accepted_at_death,
        "ZERO requests may reach the transport layer after the endpoint is declared dead, \
         but the live double accepted {} new connection(s)",
        double.accepted() - accepted_at_death
    );

    // The frozen streak is *reported*, not used as evidence: the assertion above
    // is the evidence.  (Keeping it documents why the old test's "count does not
    // grow" argument was circular.)
    let state = channel.endpoint_state(&game_endpoint).unwrap();
    assert_eq!(state.consecutive_transport_failures, 2, "{state:?}");

    // ---- Control: the counter CAN move again once the endpoint is re-armed ---
    // Re-registering the same address re-arms the route (DR-55); the very next
    // call must reach the (now healthy) double and therefore move the count.  This
    // proves the zero above came from the verdict, not from a broken counter.
    channel
        .register_game_endpoint(game_record(game_endpoint.clone(), double.port()))
        .await
        .expect("re-registration");
    channel
        .call(Role::Developer, "running_game_get_scene_tree", json!({}))
        .await
        .expect("the re-armed endpoint is healthy and must answer");
    assert_eq!(
        double.accepted(),
        accepted_at_death + 1,
        "after re-arming, one more call must produce exactly one more counted connection"
    );
}
