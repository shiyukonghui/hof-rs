//! DR-55 — a game endpoint that has stopped answering must fail **fast**.
//!
//! `smoke-t6` burned about 12 minutes on `input_replay` and
//! `node_and_collision_assertions`: the game process had already stopped
//! answering at the transport layer (status line never arrived, then connection
//! refused), and every later `running_game_*` call was still attempted — and
//! retried — against the corpse.
//!
//! The rule: two **consecutive transport-layer failures** on one endpoint mark
//! it unavailable for the rest of the session; from then on every call to it
//! returns `UNAVAILABLE` immediately, with **zero** attempts and zero waiting.
//! A first failure does not kill the endpoint, and a business error never counts
//! toward the streak (DR-56's classification is what makes that distinction).
//!
//! Everything here is offline: the endpoints are loopback doubles, and the dead
//! one is a loopback port that was bound and closed.

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

/// A loopback port that was bound and then closed: connecting to it is refused
/// **immediately**, which is exactly the `10061` the game endpoint produced
/// after it died.
fn a_closed_loopback_endpoint() -> (String, u16) {
    let listener = TcpListener::bind("127.0.0.1:0").expect("loopback listener");
    let port = listener.local_addr().unwrap().port();
    drop(listener);
    (format!("http://127.0.0.1:{port}/mcp"), port)
}

/// A loopback JSON-RPC double that answers exactly the scripted replies, counts
/// the requests it served, and can be switched to business errors on demand.
///
/// The listener is non-blocking only so this accept loop can poll `shutdown`
/// with a 2 ms back-off; `Drop` wakes it with one connection.  The socket is
/// put back into **blocking** mode before it is served — see the comment at
/// that call.  `serve` below is a blocking reader and must be allowed to wait
/// for the client's request.
struct ScriptedMcp {
    addr: SocketAddr,
    served: Arc<AtomicUsize>,
    /// DR-55: when set, every reply is a JSON-RPC **business** error (an answer,
    /// not a transport failure) instead of a success.
    business_error: Arc<AtomicUsize>,
    shutdown: Arc<AtomicUsize>,
    handle: Option<JoinHandle<()>>,
}

impl ScriptedMcp {
    fn start() -> Self {
        let listener = TcpListener::bind("127.0.0.1:0").expect("loopback listener");
        let addr = listener.local_addr().unwrap();
        listener
            .set_nonblocking(true)
            .expect("a non-blocking listener");
        let served = Arc::new(AtomicUsize::new(0));
        let business_error = Arc::new(AtomicUsize::new(0));
        let shutdown = Arc::new(AtomicUsize::new(0));
        let thread_served = served.clone();
        let thread_business = business_error.clone();
        let thread_shutdown = shutdown.clone();
        let handle = std::thread::spawn(move || {
            while thread_shutdown.load(Ordering::SeqCst) == 0 {
                match listener.accept() {
                    Ok((stream, _)) => {
                        thread_served.fetch_add(1, Ordering::SeqCst);
                        // DR-60: state the mode instead of inheriting the
                        // listener's non-blocking flag — `serve` below is a
                        // blocking reader.
                        stream
                            .set_nonblocking(false)
                            .expect("an accepted stream must block on reads");
                        serve(stream, thread_business.load(Ordering::SeqCst) != 0);
                    }
                    Err(error) if error.kind() == std::io::ErrorKind::WouldBlock => {
                        std::thread::sleep(Duration::from_millis(2));
                    }
                    Err(_) => break,
                }
            }
        });
        Self {
            addr,
            served,
            business_error,
            shutdown,
            handle: Some(handle),
        }
    }

    fn url(&self) -> String {
        format!("http://{}/mcp", self.addr)
    }

    fn port(&self) -> u16 {
        self.addr.port()
    }

    fn served(&self) -> usize {
        self.served.load(Ordering::SeqCst)
    }

    /// Answer every later call with a JSON-RPC business error.
    fn answer_with_business_errors(&self) {
        self.business_error.store(1, Ordering::SeqCst);
    }
}

impl Drop for ScriptedMcp {
    fn drop(&mut self) {
        self.shutdown.store(1, Ordering::SeqCst);
        let _ = TcpStream::connect(self.addr);
        if let Some(handle) = self.handle.take() {
            let _ = handle.join();
        }
    }
}

/// Serve one JSON-RPC request.  The reply is always a successful `result` — the
/// business-error case is produced by the *dead* endpoint tests instead, so this
/// double only has to be honest about being alive.
fn serve(mut stream: TcpStream, business_error: bool) {
    let mut buffer = Vec::new();
    let mut chunk = [0u8; 4096];
    loop {
        let read = match stream.read(&mut chunk) {
            Ok(0) => break,
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
        let reply = if business_error {
            json!({"jsonrpc": "2.0", "id": id, "error": {"code": -32602, "message": "Invalid params: refused"}})
        } else {
            json!({"jsonrpc": "2.0", "id": id, "result": {"tree": {"name": "Main"}}})
        };
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

fn game_record(endpoint: String, port: u16) -> GameEndpointRecord {
    GameEndpointRecord {
        endpoint,
        port: Some(port),
        source: SOURCE_AUTO_FREE_PORT.to_string(),
        pid: Some(4242),
    }
}

/// One call with a **zero delay** ring so the test measures attempt counts, not
/// wall time.  `max_retries = 3` gives the ring room to retry; the point of the
/// assertions is that it does not use it once the endpoint is dead.
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

/// DR-55 ①: the second consecutive transport failure kills the endpoint, and
/// every later `running_game_*` call is refused **immediately**.
///
/// The budget of 3 retries is the measurement: the first call is allowed to use
/// both failures, and after that the ring must be short-circuited by the channel
/// so the fourth attempt never happens.
#[tokio::test]
async fn two_transport_failures_kill_the_endpoint_and_later_calls_do_not_retry() {
    let (editor_endpoint, _) = a_closed_loopback_endpoint();
    let (game_endpoint, game_port) = a_closed_loopback_endpoint();
    let channel = McpChannel::new(editor_endpoint, 5, 0);
    channel
        .register_game_endpoint(game_record(game_endpoint.clone(), game_port))
        .await
        .expect("registration");

    // 1) The first call spends its two budgeted attempts, and the second
    //    consecutive transport failure kills the endpoint.
    let failure = call_game(&channel, "running_game_get_scene_tree", 1)
        .await
        .expect_err("a dead endpoint cannot answer");
    assert!(
        failure.observation().contains("UNAVAILABLE"),
        "the failure must be recorded as unavailable: {}",
        failure.observation()
    );
    let state = channel
        .endpoint_state(&game_endpoint)
        .expect("the game endpoint has a recorded state");
    assert!(
        state.unavailable,
        "two consecutive transport failures must kill the endpoint: {state:?}"
    );
    assert_eq!(state.consecutive_transport_failures, 2, "{state:?}");
    assert_eq!(
        state.transport_failures_at_mark, 2,
        "the verdict must record how many failures killed it: {state:?}"
    );

    // 2) Every later call is refused with **zero** attempts: a budget of 3 extra
    //    retries changes nothing, and the ring is not even entered.
    for _ in 0..3 {
        let failure = call_game(&channel, "running_game_get_node_property_samples", 3)
            .await
            .expect_err("the endpoint stays dead");
        let observation = failure.observation();
        assert!(
            observation.contains("UNAVAILABLE"),
            "a dead endpoint must answer UNAVAILABLE: {observation}"
        );
        assert!(
            observation.contains("game_endpoint_unavailable"),
            "the verdict must be named, not paraphrased: {observation}"
        );
        assert!(
            observation.contains("endpoint_state"),
            "the stable state field must travel with the failure: {observation}"
        );
        assert_eq!(
            failure.attempts, 1,
            "a dead endpoint is attempted exactly once, never retried: {observation}"
        );
    }

    // The strike count does not move while the endpoint is already dead.
    let state = channel.endpoint_state(&game_endpoint).unwrap();
    assert_eq!(state.consecutive_transport_failures, 2, "{state:?}");
}

/// DR-55 ②: a **first** transport failure does not kill the endpoint — the
/// design is "two strikes", not "one strike".
#[tokio::test]
async fn a_single_transport_failure_does_not_kill_the_endpoint() {
    let (editor_endpoint, _) = a_closed_loopback_endpoint();
    let (game_endpoint, game_port) = a_closed_loopback_endpoint();
    let channel = McpChannel::new(editor_endpoint, 5, 0);
    channel
        .register_game_endpoint(game_record(game_endpoint.clone(), game_port))
        .await
        .expect("registration");

    // Exactly one attempt: `max_retries = 0`.
    let failure = call_game(&channel, "running_game_get_scene_tree", 0)
        .await
        .expect_err("the endpoint is not answering");
    assert_eq!(failure.attempts, 1);
    let state = channel.endpoint_state(&game_endpoint).unwrap();
    assert_eq!(state.consecutive_transport_failures, 1, "{state:?}");
    assert!(
        !state.unavailable,
        "one failure is not a verdict — the first failure must still retry: {state:?}"
    );
}

/// DR-55 ③: a **business** error never counts toward the streak.
///
/// A live endpoint answers `-32602` three times; if business errors counted, the
/// endpoint would be declared dead after the second.  It must stay alive with a
/// zero streak, and a later real transport failure must still be the *first*
/// one.  This is the DR-55/DR-56 seam.
#[tokio::test]
async fn business_errors_never_count_toward_the_streak() {
    let (editor_endpoint, _) = a_closed_loopback_endpoint();
    let double = ScriptedMcp::start();
    let game_endpoint = double.url();
    let game_port = double.port();
    let channel = McpChannel::new(editor_endpoint, 5, 0);
    channel
        .register_game_endpoint(game_record(game_endpoint.clone(), game_port))
        .await
        .expect("registration");

    // A live endpoint answers: the streak is reset to zero.
    call_game(&channel, "running_game_get_scene_tree", 0)
        .await
        .expect("the live endpoint answers");
    assert_eq!(double.served(), 1);
    let state = channel.endpoint_state(&game_endpoint).unwrap();
    assert_eq!(state.consecutive_transport_failures, 0, "{state:?}");
    assert!(!state.unavailable, "{state:?}");

    // Three JSON-RPC business errors in a row.  Each one must be a **real**
    // business error (a code, not a transport failure).
    double.answer_with_business_errors();
    for round in 1..=3 {
        let failure = call_game(&channel, "running_game_get_scene_tree", 0)
            .await
            .expect_err("the endpoint answers with a business error");
        assert_eq!(
            failure.code,
            Some(-32602),
            "round {round} must really be a business error, not a transport failure: {failure:?}"
        );
        assert_eq!(failure.attempts, 1, "a business error is attempted once");
        let state = channel.endpoint_state(&game_endpoint).unwrap();
        assert_eq!(
            state.consecutive_transport_failures, 0,
            "round {round}: a business error is an answer and must not count: {state:?}"
        );
        assert!(
            !state.unavailable,
            "round {round}: three business errors are not a dead endpoint: {state:?}"
        );
    }
    assert_eq!(
        double.served(),
        4,
        "all four calls really reached the endpoint"
    );

    // The endpoint dies.  One real transport failure leaves the streak at 1 —
    // which is only possible if the three business errors above added nothing.
    drop(double);
    let failure = call_game(&channel, "running_game_get_scene_tree", 0)
        .await
        .expect_err("the endpoint is gone");
    assert_eq!(failure.attempts, 1);
    let state = channel.endpoint_state(&game_endpoint).unwrap();
    assert_eq!(
        state.consecutive_transport_failures, 1,
        "the business errors must have added nothing, so this is still the first: {state:?}"
    );
    assert!(
        !state.unavailable,
        "one transport failure is never a verdict: {state:?}"
    );
}

/// DR-55 ④: registering a fresh game endpoint re-arms the routing.
///
/// `editor_stop_scene` clears the route and a later `editor_play_scene` presents
/// a **new** endpoint; a verdict about the old address must not leak onto the
/// new one.
#[tokio::test]
async fn registering_a_new_endpoint_re_arms_the_route() {
    let (editor_endpoint, _) = a_closed_loopback_endpoint();
    let (dead_endpoint, dead_port) = a_closed_loopback_endpoint();
    let channel = McpChannel::new(editor_endpoint, 5, 0);
    channel
        .register_game_endpoint(game_record(dead_endpoint.clone(), dead_port))
        .await
        .expect("registration");

    call_game(&channel, "running_game_get_scene_tree", 1)
        .await
        .expect_err("the dead endpoint cannot answer");
    assert!(
        channel
            .endpoint_state(&dead_endpoint)
            .map(|state| state.unavailable)
            .unwrap_or(false),
        "the first endpoint must be marked dead"
    );

    let live = ScriptedMcp::start();
    let live_endpoint = live.url();
    channel
        .register_game_endpoint(game_record(live_endpoint.clone(), live.port()))
        .await
        .expect("re-registration");
    channel
        .call(Role::Developer, "running_game_get_scene_tree", json!({}))
        .await
        .expect("the new endpoint is alive and must be used");
    assert_eq!(live.served(), 1);
    let state = channel.endpoint_state(&live_endpoint).unwrap();
    assert!(
        !state.unavailable,
        "the new endpoint must not inherit the old verdict: {state:?}"
    );
}

/// DR-55 ⑤: the editor endpoint's own channel is unaffected by game-endpoint
/// state — the two liveness records are per address.
#[tokio::test]
async fn the_editor_endpoint_state_is_separate() {
    let editor = ScriptedMcp::start();
    let editor_endpoint = editor.url();
    let (game_endpoint, game_port) = a_closed_loopback_endpoint();
    let channel = McpChannel::new(editor_endpoint.clone(), 5, 0);
    channel
        .register_game_endpoint(game_record(game_endpoint.clone(), game_port))
        .await
        .expect("registration");

    call_game(&channel, "running_game_get_scene_tree", 1)
        .await
        .expect_err("the game endpoint is dead");
    assert!(channel.endpoint_state(&game_endpoint).unwrap().unavailable);

    // The editor is alive and keeps working, and it is not marked dead.
    channel
        .call(Role::Developer, "editor_get_errors", json!({}))
        .await
        .expect("the editor endpoint is alive");
    let editor_state = channel
        .endpoint_state(&editor_endpoint)
        .expect("the editor endpoint has a recorded state");
    assert!(!editor_state.unavailable, "{editor_state:?}");
    assert_eq!(editor_state.consecutive_transport_failures, 0);
}

/// DR-55: the state is a **stable field name** in the evidence, not prose — the
/// `endpoint_state` object carries the same facts a record consumer needs.
#[tokio::test]
async fn the_endpoint_state_is_a_stable_evidence_field() {
    let (editor_endpoint, _) = a_closed_loopback_endpoint();
    let (game_endpoint, game_port) = a_closed_loopback_endpoint();
    let channel = McpChannel::new(editor_endpoint, 5, 0);
    channel
        .register_game_endpoint(game_record(game_endpoint.clone(), game_port))
        .await
        .expect("registration");

    call_game(&channel, "running_game_get_scene_tree", 1)
        .await
        .expect_err("the endpoint is dead");

    let state = channel.endpoint_state(&game_endpoint).unwrap();
    let encoded = serde_json::to_value(&state).expect("the state is serializable");
    assert_eq!(encoded["endpoint"], json!(game_endpoint));
    assert_eq!(encoded["unavailable"], json!(true));
    assert_eq!(encoded["consecutive_transport_failures"], json!(2));
    assert_eq!(encoded["transport_failures_at_mark"], json!(2));
    assert_eq!(encoded["state"], json!("unavailable"));
}

/// DR-55: `wait_for_game_ready` must observe the same verdict, so a readiness
/// poll against a dead endpoint stops instead of polling to its deadline.
#[tokio::test]
async fn a_dead_endpoint_stops_the_readiness_poll() {
    let (editor_endpoint, _) = a_closed_loopback_endpoint();
    let (game_endpoint, game_port) = a_closed_loopback_endpoint();
    let channel = McpChannel::new(editor_endpoint, 5, 0);
    channel
        .register_game_endpoint(game_record(game_endpoint.clone(), game_port))
        .await
        .expect("registration");

    // Kill it first.
    call_game(&channel, "running_game_get_scene_tree", 1)
        .await
        .expect_err("the endpoint is dead");

    let started = std::time::Instant::now();
    let outcome = hof_rs::tools::reliable::wait_for_game_ready(
        &channel,
        Role::Developer,
        "running_game_get_scene_tree",
        json!({}),
        /* timeout */ 30,
        /* poll interval */ 5,
        None,
    )
    .await;
    assert!(!outcome.ok, "a dead endpoint cannot become ready");
    assert!(
        started.elapsed() < Duration::from_secs(5),
        "the poll must stop immediately, not burn its 30 s budget: {:?}",
        started.elapsed()
    );
    assert_eq!(outcome.attempts, 1, "one refusal, no polling");
    let failure = outcome.failure.expect("the refusal is recorded");
    assert!(
        failure.observation().contains("UNAVAILABLE"),
        "{}",
        failure.observation()
    );
}
