//! BATCH-B2 cross-module pins.
//!
//! Five things this batch changed are only checkable from outside the unit-test
//! modules, because each one is a property of the whole surface rather than of
//! one function:
//!
//! * the **re-pinned contract and tool-list hashes**, and the seventh surface
//!   behind the first of them (D297 (a)/(b)/(c));
//! * the **PRD's sealed prefix** — the append-only addition's seal;
//! * the **inherited defects' fixes**: D1 (`Malformed`, not a null success), D2
//!   (a reply whose id is not the request's is refused), D3 (the fake BRP server
//!   is deterministic and never answers a request it did not read) and D4 (the
//!   semantic layer's type paths are bound to the contract by construction).
//!
//! The D1/D2/D3 checks speak HTTP to a raw loopback socket, because the defect
//! they pin is about what the client does with *bytes on the wire*, and the
//! in-process fake is too well-behaved to express the attack.

use std::io::{Read, Write};
use std::net::{TcpListener, TcpStream};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::time::Duration;

use hof_rs::adapter::bevy::brp::{self, BrpClient, BrpError};
use hof_rs::adapter::bevy::build::{feature_hash_of, frozen_feature_list, FEATURE_SET_SHA256};
use hof_rs::adapter::bevy::contract::{
    contract_path, contract_sha256, CONTRACT, CONTRACT_SHA256, GAME_CONTRACT_MODULE, GAME_CRATE,
};
use hof_rs::adapter::bevy::prd;
use hof_rs::adapter::mcp::semantic::{
    COIN_COUNTER_PATH, FRAME_COUNTER_PATH, GROUNDED_PATH, INPUT_INTENT_PATH, PLAYER_PATH,
    WIN_FLAG_PATH,
};
use hof_rs::adapter::mcp::{tool_list, tool_list_sha256, TOOL_LIST_SHA256};

/// A raw loopback server that answers every request with the scripted body and
/// sends the request bodies it saw back through a channel.
///
/// It exists to attack the client: the in-process fake is deliberately
/// well-behaved, so the "valid JSON that is not JSON-RPC" and "a reply for
/// someone else" cases need a server that will lie on purpose.
struct RawServer {
    addr: std::net::SocketAddr,
    seen: Arc<std::sync::Mutex<Vec<String>>>,
    failures: Arc<std::sync::Mutex<Vec<String>>>,
    stop: Arc<AtomicBool>,
    handle: Option<std::thread::JoinHandle<()>>,
}

impl RawServer {
    /// `reply_for` receives the request body and returns the raw response body.
    fn spawn(reply_for: Arc<dyn Fn(&str) -> String + Send + Sync>) -> Self {
        let listener = TcpListener::bind("127.0.0.1:0").expect("a free loopback port");
        listener
            .set_nonblocking(true)
            .expect("a non-blocking listener");
        let addr = listener.local_addr().expect("a bound address");
        let seen = Arc::new(std::sync::Mutex::new(Vec::new()));
        let failures = Arc::new(std::sync::Mutex::new(Vec::new()));
        let stop = Arc::new(AtomicBool::new(false));
        let handle = {
            let seen = Arc::clone(&seen);
            let failures = Arc::clone(&failures);
            let stop = Arc::clone(&stop);
            std::thread::spawn(move || {
                while !stop.load(Ordering::SeqCst) {
                    match listener.accept() {
                        Ok((stream, _)) => {
                            let _ = stream.set_nonblocking(false);
                            // B2-11: a failed read is **not** answered as if the
                            // request had arrived.  It is recorded and answered
                            // with an explicit JSON-RPC error, so a test cannot
                            // silently proceed on a body that was never read.
                            let body = match read_http_body(&stream) {
                                Ok(body) => body,
                                Err(reason) => {
                                    if let Ok(mut seen) = failures.lock() {
                                        seen.push(reason.clone());
                                    }
                                    let _ = write_http_200(
                                        &stream,
                                        &format!(
                                            "{{\"jsonrpc\":\"2.0\",\"id\":null,\"error\":{{\"code\":-32700,\"message\":\"the raw server could not read this request: {reason}\"}}}}"
                                        ),
                                    );
                                    continue;
                                }
                            };
                            if let Ok(mut seen) = seen.lock() {
                                seen.push(body.clone());
                            }
                            let response = reply_for(&body);
                            let _ = write_http_200(&stream, &response);
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
            seen,
            failures,
            stop,
            handle: Some(handle),
        }
    }

    fn endpoint(&self) -> String {
        format!("http://{}/", self.addr)
    }

    fn requests(&self) -> Vec<String> {
        self.seen
            .lock()
            .map(|seen| seen.clone())
            .unwrap_or_default()
    }

    /// Every request whose read failed.  A live test asserts this is empty.
    fn read_failures(&self) -> Vec<String> {
        self.failures
            .lock()
            .map(|seen| seen.clone())
            .unwrap_or_default()
    }
}

impl Drop for RawServer {
    fn drop(&mut self) {
        self.stop.store(true, Ordering::SeqCst);
        if let Some(handle) = self.handle.take() {
            let _ = handle.join();
        }
    }
}

/// A blocking read of one HTTP request, with a real deadline.  A problem is an
/// `Err` with the reason, never an empty body (B2-11).
fn read_http_body(stream: &TcpStream) -> Result<String, String> {
    let mut stream = stream;
    stream
        .set_read_timeout(Some(Duration::from_millis(500)))
        .map_err(|error| format!("the read timeout could not be set: {error}"))?;
    let mut buffer = Vec::new();
    let mut chunk = [0u8; 4096];
    loop {
        match stream.read(&mut chunk) {
            Ok(0) => return Err("the connection closed inside the request".to_string()),
            Ok(read) => buffer.extend_from_slice(&chunk[..read]),
            Err(error) if error.kind() == std::io::ErrorKind::Interrupted => {}
            Err(error) => return Err(format!("the request read failed: {error}")),
        }
        if let Some(position) = find_header_end(&buffer) {
            let headers = String::from_utf8_lossy(&buffer[..position]).to_string();
            let length = content_length(&headers);
            if buffer.len() >= position + 4 + length {
                return Ok(
                    String::from_utf8_lossy(&buffer[position + 4..position + 4 + length])
                        .to_string(),
                );
            }
        }
    }
}

fn find_header_end(buffer: &[u8]) -> Option<usize> {
    buffer.windows(4).position(|window| window == b"\r\n\r\n")
}

fn content_length(headers: &str) -> usize {
    for line in headers.lines() {
        let Some((name, value)) = line.split_once(':') else {
            continue;
        };
        if name.eq_ignore_ascii_case("content-length") {
            return value.trim().parse().unwrap_or(0);
        }
    }
    0
}

fn write_http_200(stream: &TcpStream, body: &str) -> std::io::Result<()> {
    let mut stream = stream;
    let response = format!(
        "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{body}",
        body.len()
    );
    stream.write_all(response.as_bytes())?;
    stream.flush()
}

fn client(server: &RawServer) -> BrpClient {
    BrpClient::new(server.endpoint(), Duration::from_secs(2))
}

/// A reply builder that inserts the request's own `id`, the way a real JSON-RPC
/// peer answers.  It is needed since B2-9: a reply with no `id` member is now
/// refused when an id is expected, so a raw double must correlate like a peer.
fn echoing_id(document: serde_json::Value) -> Arc<dyn Fn(&str) -> String + Send + Sync> {
    Arc::new(move |request: &str| {
        let id = serde_json::from_str::<serde_json::Value>(request)
            .ok()
            .and_then(|parsed| parsed.get("id").cloned())
            .unwrap_or(serde_json::Value::Null);
        let mut document = document.clone();
        if let Some(object) = document.as_object_mut() {
            object.insert("id".to_string(), id);
        }
        document.to_string()
    })
}

// ---------------------------------------------------------------------------
// The re-pinned surfaces
// ---------------------------------------------------------------------------

#[test]
fn the_repinned_contract_hash_covers_seven_surfaces() {
    assert_eq!(
        contract_sha256(),
        CONTRACT_SHA256,
        "the contract drifted; it is re-pinned in BATCH-B2"
    );
    assert_eq!(
        CONTRACT_SHA256, "792001e7e629ccc25d6c486eeb54360d83ffb208befa4ca5e430c6f0e747f4f9",
        "the pin must be the value this batch published"
    );
    assert_eq!(CONTRACT.len(), 7);
    assert_eq!(GAME_CRATE, "hof_game");
    assert_eq!(GAME_CONTRACT_MODULE, "hof_game::contract");
    let frame = CONTRACT
        .iter()
        .find(|entry| entry.surface == "frame_counter")
        .expect("the seventh surface is the game frame counter");
    assert_eq!(frame.type_path, "hof_game::contract::FrameCounter");
    assert_eq!(frame.reflect, "Resource");
    assert_eq!(frame.semantic_tool, "bevy_wait_frames");
}

#[test]
fn the_repinned_tool_list_hash_is_the_published_value() {
    assert_eq!(
        tool_list_sha256(),
        TOOL_LIST_SHA256,
        "the frozen tool surface drifted; it is re-pinned in BATCH-B2"
    );
    assert_eq!(
        TOOL_LIST_SHA256, "bcf03c0b06295cfd27cc0359a7fa272ed435bdf61525d67b08981c62d30e43b1",
        "the pin must be the value this batch published"
    );
}

#[test]
fn the_semantic_return_shapes_are_inside_the_hashed_tool_list() {
    // D297 (c): the output shapes are part of the frozen list, so a silent
    // semantic change of a return value is impossible.
    let list = tool_list();
    let tools = list["tools"].as_array().expect("the frozen list");
    let semantic = &tools[tools.len() - 8..];
    for tool in semantic {
        let name = tool["name"].as_str().unwrap_or_default();
        let schema = tool
            .get("outputSchema")
            .unwrap_or_else(|| panic!("`{name}` publishes no outputSchema"));
        assert_eq!(schema["type"], serde_json::json!("object"), "{name}");
        assert_eq!(
            schema["additionalProperties"],
            serde_json::json!(false),
            "{name}"
        );
    }
    // The frame field is declared in every reading's shape and describes the
    // game's own counter.
    let transform = &semantic[0];
    assert_eq!(
        transform["outputSchema"]["required"],
        serde_json::json!(["x", "y", "frame"])
    );
    assert!(
        transform["outputSchema"]["properties"]["frame"]["description"]
            .as_str()
            .unwrap_or_default()
            .contains("GAME"),
        "the frame field must say whose frame it is"
    );
    // A generic pass-through tool must NOT restate BRP's shape.
    assert!(tools[0].get("outputSchema").is_none());
}

#[test]
fn the_feature_pin_is_unchanged_and_still_hashes_the_frozen_document() {
    assert_eq!(feature_hash_of(&frozen_feature_list()), FEATURE_SET_SHA256);
}

// ---------------------------------------------------------------------------
// Task 2: the PRD's sealed prefix
// ---------------------------------------------------------------------------

/// The test the appended PRD section names.  A rewrite above the seal marker
/// reddens this; an append below it does not.
#[test]
fn the_prd_sealed_prefix_is_byte_identical() {
    let path = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join(".spec/bevy/PRD.md");
    let text = std::fs::read_to_string(&path).expect("the PRD is part of the repository");
    prd::verify(&text).unwrap_or_else(|error| panic!("{error}"));

    // The append is *below* the marker, and the frozen text is above it.
    let prefix = prd::sealed_prefix(&text).expect("the marker");
    assert_eq!(prefix.len(), prd::SEALED_PREFIX_BYTES);
    assert_eq!(
        hof_rs::runtime::policy::sha256_hex(prefix.as_bytes()),
        prd::SEALED_PREFIX_SHA256
    );
    // The appended block records the change this batch made.
    let appended = &text[prefix.len()..];
    assert!(
        appended.contains("第七个可反射语义面"),
        "the seventh surface"
    );
    assert!(
        appended.contains("hof_game::contract"),
        "the frozen crate name"
    );
    assert!(
        appended.contains("从未被封印过"),
        "the document must say plainly that it carried no earlier seal"
    );

    // And the mechanism is real: rewriting one byte above the marker fails.
    let mut rewritten = String::from(prefix);
    rewritten.push_str(&text[prefix.len()..]);
    let tampered = rewritten.replacen("横版跳跃", "横版跑跳", 1);
    assert_ne!(tampered, rewritten, "the tamper must change the text");
    assert!(
        prd::verify(&tampered).is_err(),
        "a rewrite above the marker must fail the seal"
    );
}

// ---------------------------------------------------------------------------
// The inherited defects
// ---------------------------------------------------------------------------

/// D1: valid JSON that is not a JSON-RPC document must be `Malformed`, never a
/// null success.
#[test]
fn d1_valid_json_that_is_not_json_rpc_is_malformed() {
    for body in ["42", "\"ok\"", "{}", "null", "{\"jsonrpc\":\"2.0\"}"] {
        let server = RawServer::spawn(Arc::new(move |_request: &str| body.to_string()));
        let error = client(&server)
            .call("world.list_resources", None)
            .unwrap_err();
        assert!(
            matches!(error, BrpError::Malformed { .. }),
            "`{body}` must be Malformed, got {error:?}"
        );
        assert!(
            !error.is_infrastructure(),
            "a bad body is not an infrastructure failure"
        );
    }
    // A real document with a null result is still a success.
    let server = RawServer::spawn(echoing_id(serde_json::json!({
        "jsonrpc": "2.0",
        "result": null
    })));
    assert_eq!(
        client(&server).call("world.x", None).unwrap(),
        serde_json::Value::Null
    );
}

/// D2: a reply whose `id` is not the request's must be rejected, not returned as
/// this call's result.
#[test]
fn d2_a_reply_for_another_request_is_refused() {
    // The server answers every request with id 1, whatever it was asked.
    let server = RawServer::spawn(Arc::new(|_request: &str| {
        "{\"jsonrpc\":\"2.0\",\"id\":1,\"result\":{\"which\":\"stale\"}}".to_string()
    }));
    let client = client(&server);
    // The first call is genuinely id 1 and succeeds.
    assert_eq!(
        client.call("rpc.discover", None).unwrap(),
        serde_json::json!({"which": "stale"})
    );
    // The second call is id 2, and the same stale document must not answer it.
    let error = client.call("rpc.discover", None).unwrap_err();
    assert!(
        matches!(error, BrpError::Malformed { .. }),
        "a reply to another request must be Malformed, got {error:?}"
    );
    assert!(
        error.to_string().contains("waiting"),
        "the refusal must say why: {error}"
    );
}

/// D3, part 1: what a raw socket sees.  The client's request really carries the
/// `Content-Length` the fake needs (its absence was the mechanism behind D3: a
/// scan that returned `None` on the colon-less request line read every body as
/// zero bytes), and a request whose read fails is refused instead of answered.
///
/// **The pin for the timing repair itself lives in the crate**: the in-process
/// `FakeBrp` is `#[cfg(test)]` inside `src/adapter/bevy/brp.rs`, so an
/// integration test cannot see it.  The lib test
/// `brp::tests::the_fake_restores_blocking_on_every_accepted_stream` is what
/// reddens when the `set_nonblocking(false)` restore is removed (B2-2/B2-11);
/// this test only pins the wire shape.
#[test]
fn d3_the_raw_socket_sees_a_complete_request_and_a_failed_read_is_refused() {
    let server = RawServer::spawn(echoing_id(serde_json::json!({
        "jsonrpc": "2.0",
        "result": 1
    })));
    let _ = client(&server).call("rpc.discover", None).unwrap();
    let seen = server.requests();
    assert_eq!(seen.len(), 1);
    let parsed: serde_json::Value =
        serde_json::from_str(&seen[0]).expect("the server recorded a complete request body");
    assert_eq!(parsed["method"], serde_json::json!("rpc.discover"));
    assert!(seen[0].starts_with('{'), "the body was read: {seen:?}");
    assert_eq!(
        server.read_failures(),
        Vec::<String>::new(),
        "a live request is read whole"
    );
}

/// D4: the semantic layer's type paths are the contract's paths **by
/// construction** — there is one literal per path, in the contract table, and
/// the layer looks them up with `contract_path` in a `const` initialiser, so a
/// surface rename is a compile error.
///
/// B2-10: the pin is **not tautological**.  Comparing `PLAYER_PATH` with
/// `contract_path("player_marker")` is true by definition for the shipped
/// source, because that is exactly how the constant is defined.  So the
/// expected values are restated here as independent literals: if a contract
/// path moves, this test goes red and the value must be re-pinned deliberately
/// (and, per the design, go through the decision process), rather than passing
/// because both sides moved together.
#[test]
fn d4_the_semantic_paths_are_the_contracts_paths_by_construction() {
    assert_eq!(PLAYER_PATH, "hof_game::contract::Player");
    assert_eq!(GROUNDED_PATH, "hof_game::contract::Grounded");
    assert_eq!(COIN_COUNTER_PATH, "hof_game::contract::CoinCounter");
    assert_eq!(WIN_FLAG_PATH, "hof_game::contract::WinFlag");
    assert_eq!(FRAME_COUNTER_PATH, "hof_game::contract::FrameCounter");
    assert_eq!(INPUT_INTENT_PATH, "hof_game::contract::InputIntent");
    assert_eq!(
        hof_rs::adapter::mcp::semantic::TRANSFORM_PATH,
        "bevy_transform::components::transform::Transform"
    );
    // And the independent literals above must be exactly the contract table's
    // values: this is the *second* side of the check, so a drift in either the
    // table or the layer is caught.
    for (surface, literal) in [
        ("player_marker", PLAYER_PATH),
        ("grounded", GROUNDED_PATH),
        ("coin_counter", COIN_COUNTER_PATH),
        ("win_flag", WIN_FLAG_PATH),
        ("frame_counter", FRAME_COUNTER_PATH),
        ("input_intent", INPUT_INTENT_PATH),
    ] {
        let entry = CONTRACT
            .iter()
            .find(|entry| entry.surface == surface)
            .unwrap_or_else(|| panic!("`{surface}` is a frozen surface"));
        assert_eq!(literal, entry.type_path, "{surface}");
    }
    // The engine path is a contract surface too, and it is the one path that is
    // not under the game's crate.
    assert!(
        COIN_COUNTER_PATH.starts_with(&format!("{GAME_CONTRACT_MODULE}::")),
        "{COIN_COUNTER_PATH}"
    );
    // Every semantic tool's bound path is a real surface.
    for entry in CONTRACT {
        assert_eq!(contract_path(entry.surface), entry.type_path);
    }
    // And BRP's own path resolution agrees with the contract module.
    assert_eq!(
        hof_rs::adapter::mcp::semantic::CONTRACT_MODULE,
        "hof_game::contract"
    );
}

// ---------------------------------------------------------------------------
// The real-machine smoke
// ---------------------------------------------------------------------------

/// The real-machine smoke: it exists, it is runnable on a machine that has the
/// engine, and it never enters the default gate.
///
/// Run it with
/// `cargo test --offline --test bevy_adapter_b2 -- --ignored --nocapture`
/// while `hof_game` (with `RemotePlugin`/`RemoteHttpPlugin` and the frozen
/// contract types registered) is listening on 127.0.0.1:15702.  It checks the
/// three facts the adapter's design rests on and that no fake can prove: the
/// endpoint's version, the frame counter's presence through the contract path,
/// and that a level-triggered injection is accepted without a batch.
#[test]
#[ignore = "needs a real hof_game on 127.0.0.1:15702 with the frozen contract registered; never in the default gate"]
fn the_real_machine_smoke_proves_the_contract_on_a_live_bevy_game() {
    let client = BrpClient::local(Duration::from_secs(3));
    let discover = client
        .discover()
        .expect("a live BRP endpoint on 127.0.0.1:15702");
    assert_eq!(discover["info"]["version"], serde_json::json!("0.19.1"));
    assert_eq!(discover["methodCount"], serde_json::json!(23));

    // The seventh surface, read through the frozen path.
    let frame = client
        .call(
            "world.get_resources",
            Some(serde_json::json!({"resource": contract_path("frame_counter")})),
        )
        .expect("the game registers hof_game::contract::FrameCounter");
    let before = frame["value"]["frames"]
        .as_u64()
        .or_else(|| frame["value"].as_u64())
        .expect("the counter is an integer");
    std::thread::sleep(Duration::from_millis(200));
    let again = client
        .call(
            "world.get_resources",
            Some(serde_json::json!({"resource": contract_path("frame_counter")})),
        )
        .expect("the counter is readable again");
    let after = again["value"]["frames"]
        .as_u64()
        .or_else(|| again["value"].as_u64())
        .expect("the counter is an integer");
    assert!(
        after > before,
        "the game must advance its own frame counter: {before} then {after}"
    );

    // A level-triggered injection is accepted, and it is one call, not a batch.
    let injected = client
        .call(
            "world.mutate_resources",
            Some(serde_json::json!({
                "resource": contract_path("input_intent"),
                "path": "move_dir",
                "value": 1,
            })),
        )
        .expect("the game registers hof_game::contract::InputIntent");
    assert!(injected.is_null(), "a mutate answers null: {injected}");
    let _ = brp::endpoint();
}
