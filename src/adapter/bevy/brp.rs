//! The BRP client: JSON-RPC 2.0 over HTTP/1.1 on **15702 only** (DESIGN-DETAIL
//! §5, §7).
//!
//! Four facts from the spikes shape this file, and each one is enforced rather
//! than documented:
//!
//! 1. **HTTP always answers 200**, with the error inside the body
//!    (`{"error":{"code":-32601,…}}`).  A client that judges success by the
//!    status code turns every protocol failure into a success (SPIKE-1 §0.4-5),
//!    so [`BrpClient::call`] parses the body and treats a non-null `error` as a
//!    tool error.
//! 2. **Two endpoints exist**; 15703 is the render world's and only exists when
//!    a render world does (SPIKE-2 §0.1: with `backends: None` there is no
//!    render world at all).  [`BRP_PORT`] is 15702 and there is no API here that
//!    can address another port except by explicitly constructing a client.
//! 3. **A batch is not frame-atomic** (SPIKE-2 C4: one batch of 24 identical
//!    `world.get_resources` calls returned both `coins:1` and `coins:2`), so
//!    this client has **no batch API at all**: [`BrpClient::call`] takes one
//!    method, and [`request_body`] can only build one request object.
//! 4. **Readiness is polled, never slept for** (SPIKE-1 §3.4): debug startup was
//!   3.1 s idle and 6.6 s under load, so [`BrpClient::wait_ready`] polls
//!    `rpc.discover` until the budget (30 s, DESIGN-DETAIL §4) runs out and then
//!    reports `EndpointTimeout` — an *infrastructure* failure, not a defect.

use std::time::{Duration, Instant};

use serde_json::{json, Value};

/// The main-world endpoint port.  Pinned: the render world's 15703 is never used.
pub const BRP_PORT: u16 = 15702;
/// The BRP host.  Loopback only — BRP has no authentication and no TLS.
pub const BRP_HOST: &str = "127.0.0.1";
/// DESIGN-DETAIL §4: readiness poll interval.
pub const READY_POLL_INTERVAL: Duration = Duration::from_millis(500);
/// DESIGN-DETAIL §5: readiness budget.
pub const ENDPOINT_READY_BUDGET: Duration = Duration::from_secs(30);
/// The `rpc.discover` method name.
pub const RPC_DISCOVER: &str = "rpc.discover";
/// SPIKE-1 §1.2: the 23 methods every default BRP endpoint exposes.
pub const BRP_METHOD_COUNT: usize = 23;

/// The endpoint string for the pinned port.
pub fn endpoint() -> String {
    format!("http://{BRP_HOST}:{BRP_PORT}/")
}

/// A BRP failure, classified.  The classes are what the gate reads: a transport
/// or timeout failure is infrastructure, a contract-violation code is a project
/// defect, and `-32601` is neither (it means *our* adapter addressed a method
/// that does not exist — SPIKE-1 §6.3).
#[derive(Clone, Debug, PartialEq, Eq, thiserror::Error)]
pub enum BrpError {
    /// The connection itself failed (refused, closed, timed out).
    #[error("BRP transport failure to {endpoint}: {message}")]
    Transport { endpoint: String, message: String },
    /// A request that did not answer inside the client timeout.
    #[error("BRP request to {endpoint} timed out after {millis} ms")]
    Timeout { endpoint: String, millis: u64 },
    /// HTTP answered with a status that is not 2xx.  BRP itself always answers
    /// 200, so this is a proxy or a different server — an error either way.
    #[error("BRP answered HTTP {status} from {endpoint}: {body}")]
    HttpStatus {
        endpoint: String,
        status: u16,
        body: String,
    },
    /// HTTP 200 with an `error` object in the body: the protocol's real failure
    /// channel.
    #[error("BRP JSON-RPC error {code}: {message}")]
    Rpc { code: i64, message: String },
    /// The body was not a JSON-RPC document.
    #[error("BRP reply from {endpoint} was malformed: {message}")]
    Malformed { endpoint: String, message: String },
    /// The endpoint never became ready inside the budget (DESIGN-DETAIL §7).
    #[error("BRP endpoint {endpoint} was not ready within {budget_millis} ms")]
    EndpointTimeout {
        endpoint: String,
        budget_millis: u64,
    },
    /// The client was asked for something the protocol cannot express (a batch,
    /// a missing method, a non-object payload).
    #[error("invalid BRP request: {0}")]
    InvalidRequest(String),
}

impl BrpError {
    /// The JSON-RPC code, when there is one.
    pub fn code(&self) -> Option<i64> {
        match self {
            BrpError::Rpc { code, .. } => Some(*code),
            _ => None,
        }
    }

    /// SPIKE-1 §6.3: `-32601` means the adapter named a method the engine does
    /// not have, i.e. an adapter bug rather than a game defect.
    pub fn is_method_not_found(&self) -> bool {
        self.code() == Some(-32601)
    }

    /// Is this an infrastructure failure (the game never got a chance to be
    /// judged)?  DESIGN-DETAIL §7 requires the gate to classify those
    /// separately from project defects.
    pub fn is_infrastructure(&self) -> bool {
        matches!(
            self,
            BrpError::Transport { .. }
                | BrpError::Timeout { .. }
                | BrpError::EndpointTimeout { .. }
        )
    }

    /// Is this a "the game did not declare what the PRD requires" failure?
    pub fn is_contract_violation(&self) -> bool {
        match self.code() {
            Some(code) => crate::adapter::bevy::contract::CONTRACT_VIOLATION_CODES.contains(&code),
            None => false,
        }
    }
}

/// The one request document this client can build: a single JSON-RPC 2.0 call.
///
/// It is deliberately shaped so a batch is unrepresentable — there is no variant
/// of this function that produces an array.
pub fn request_body(id: u64, method: &str, params: Option<Value>) -> Value {
    let mut body = json!({"jsonrpc": "2.0", "id": id, "method": method});
    if let Some(params) = params {
        body["params"] = params;
    }
    body
}

/// Split one reply body: a non-null `error` is a tool error; otherwise the
/// `result` is returned.
pub fn read_reply(body: &str, endpoint: &str) -> Result<Value, BrpError> {
    let value: Value = serde_json::from_str(body).map_err(|error| BrpError::Malformed {
        endpoint: endpoint.to_string(),
        message: format!("not JSON: {error}"),
    })?;
    read_document(&value, endpoint)
}

/// The same reading, on an already-parsed document.
///
/// It is the single enforcement point for the shape of a reply, and it is
/// deliberately strict (the B1 acceptance's D1): a reply must be a **JSON-RPC
/// document** — an object carrying either a non-null `error` or a `result`
/// member.  Valid JSON that is not such a document (a number, a string, `null`,
/// an empty object, an object with neither member) is `Malformed`, never a
/// successful `null`: "the peer answered something else" and "the call returned
/// null" are different facts, and only one of them is a success.
///
/// A batch reply (an array) is refused outright: this client never batches, so
/// receiving one means something else answered.
///
/// `expected_id` is the id of the request that is waiting for this reply (the
/// B1 acceptance's D2).  A reply whose `id` is someone else's is `Malformed`:
/// accepting it would report another call's result under this call's name.
pub fn read_document_for(
    value: &Value,
    endpoint: &str,
    expected_id: Option<u64>,
) -> Result<Value, BrpError> {
    let malformed = |message: String| BrpError::Malformed {
        endpoint: endpoint.to_string(),
        message,
    };
    if let Value::Array(_) = value {
        return Err(malformed(
            "a batch reply (array) is not acceptable: this client never batches".to_string(),
        ));
    }
    let object = match value.as_object() {
        Some(object) => object,
        None => {
            return Err(malformed(format!(
                "a JSON-RPC reply must be an object with `result` or `error`, got {value}"
            )));
        }
    };
    if let Some(expected) = expected_id {
        match object.get("id") {
            Some(actual) => {
                if actual.as_u64() != Some(expected) {
                    return Err(malformed(format!(
                        "the reply carries id {actual} but request {expected} is waiting: a reply to \
                         another call is never this call's result"
                    )));
                }
            }
            // B2-9: a reply that carries **no** `id` member at all is not
            // correlated either.  Accepting it would let any uncorrelated
            // document answer any pending request — the same class as a stale
            // id, and the same reason D2 exists.
            None => {
                return Err(malformed(format!(
                    "the reply carries no `id` member but request {expected} is waiting: an \
                     uncorrelated reply is never this call's result"
                )));
            }
        }
    }
    if let Some(error) = object.get("error") {
        if !error.is_null() {
            let code = error.get("code").and_then(Value::as_i64).unwrap_or(0);
            let message = error
                .get("message")
                .and_then(Value::as_str)
                .unwrap_or("unknown BRP error")
                .to_string();
            return Err(BrpError::Rpc { code, message });
        }
    }
    match object.get("result") {
        Some(result) => Ok(result.clone()),
        None => Err(malformed(
            "the reply is a JSON object but carries neither a `result` nor a non-null `error`"
                .to_string(),
        )),
    }
}

/// [`read_document_for`] without an id to correlate against (used where the
/// caller already matched the id, or is reading a recorded document).
pub fn read_document(value: &Value, endpoint: &str) -> Result<Value, BrpError> {
    read_document_for(value, endpoint, None)
}

/// A blocking BRP client.  One instance talks to one endpoint.
#[derive(Clone, Debug)]
pub struct BrpClient {
    endpoint: String,
    timeout: Duration,
    next_id: std::sync::Arc<std::sync::atomic::AtomicU64>,
}

impl BrpClient {
    pub fn new(endpoint: impl Into<String>, timeout: Duration) -> Self {
        Self {
            endpoint: endpoint.into(),
            timeout,
            next_id: std::sync::Arc::new(std::sync::atomic::AtomicU64::new(1)),
        }
    }

    /// A client for the pinned local endpoint.
    pub fn local(timeout: Duration) -> Self {
        Self::new(endpoint(), timeout)
    }

    pub fn endpoint(&self) -> &str {
        &self.endpoint
    }

    pub fn timeout(&self) -> Duration {
        self.timeout
    }

    /// One JSON-RPC call.  `params` is passed through verbatim (SPIKE-1 §0.4-2:
    /// the adapter must not re-shape values).
    pub fn call(&self, method: &str, params: Option<Value>) -> Result<Value, BrpError> {
        let id = self.next_id();
        let document = self.call_document(id, method, params)?;
        // The reply is correlated with *this* request before it is read: a stale
        // or out-of-order document must not become this call's result (D2).
        read_document_for(&document, &self.endpoint, Some(id))
    }

    /// The next JSON-RPC id (per request, so evidence can correlate).
    pub fn next_id(&self) -> u64 {
        self.next_id
            .fetch_add(1, std::sync::atomic::Ordering::SeqCst)
    }

    /// One request, returned as the **whole JSON-RPC document** — what the
    /// evidence records, so a reader sees the reply the engine actually sent
    /// (including an `error` object) rather than only the result that was
    /// extracted from it.
    pub fn call_document(
        &self,
        id: u64,
        method: &str,
        params: Option<Value>,
    ) -> Result<Value, BrpError> {
        if method.is_empty() {
            return Err(BrpError::InvalidRequest(
                "the method name must not be empty".to_string(),
            ));
        }
        if let Some(Value::Array(_)) = params {
            return Err(BrpError::InvalidRequest(
                "params must be an object: a batch is not frame-atomic (SPIKE-2 C4) and this \
                 client never sends one"
                    .to_string(),
            ));
        }
        let body = request_body(id, method, params);
        let text = self.post(&body)?;
        let document: Value = serde_json::from_str(&text).map_err(|error| BrpError::Malformed {
            endpoint: self.endpoint.clone(),
            message: format!("not JSON: {error}"),
        })?;
        // Correlate here as well, because this is also the evidence path: a
        // document that belongs to another request must never be recorded as the
        // answer to this one (D2).
        read_document_for(&document, &self.endpoint, Some(id))?;
        Ok(document)
    }

    /// `rpc.discover` — the method the readiness poll uses (SPIKE-1 §1.2).
    pub fn discover(&self) -> Result<Value, BrpError> {
        self.call(RPC_DISCOVER, None)
    }

    /// Poll `rpc.discover` until it answers, or the budget runs out.
    ///
    /// Every failure is retried until the budget expires: a not-yet-bound port, a
    /// half-open connection and an error body are all "not ready".  The timeout
    /// is reported with the budget it was given, because the gate has to be able
    /// to say *why* a round was infrastructure-failed.
    pub fn wait_ready(&self, budget: Duration, interval: Duration) -> Result<Value, BrpError> {
        let started = Instant::now();
        let deadline = started + budget;
        loop {
            match self.discover() {
                Ok(document) => return Ok(document),
                // Any answer other than "ready" is retried until the budget is
                // spent; the budget is what the caller must reason about, so the
                // timeout below is the failure that is reported.
                Err(_) => {}
            }
            if Instant::now() >= deadline {
                return Err(BrpError::EndpointTimeout {
                    endpoint: self.endpoint.clone(),
                    budget_millis: budget.as_millis() as u64,
                });
            }
            let remaining = deadline.saturating_duration_since(Instant::now());
            std::thread::sleep(interval.min(remaining));
        }
    }

    /// The one HTTP round trip.  `ureq` is blocking by design (the harness's
    /// tool bridge is a short-lived process), so this method is not async.
    fn post(&self, body: &Value) -> Result<String, BrpError> {
        let started = Instant::now();
        let agent = ureq::AgentBuilder::new().timeout(self.timeout).build();
        match agent
            .post(&self.endpoint)
            .set("Content-Type", "application/json")
            .send_string(&body.to_string())
        {
            Ok(response) => response.into_string().map_err(|error| BrpError::Malformed {
                endpoint: self.endpoint.clone(),
                message: format!("the body could not be read: {error}"),
            }),
            Err(ureq::Error::Status(status, response)) => {
                let body = response.into_string().unwrap_or_default();
                Err(BrpError::HttpStatus {
                    endpoint: self.endpoint.clone(),
                    status,
                    body,
                })
            }
            Err(ureq::Error::Transport(transport)) => {
                let message = transport
                    .message()
                    .unwrap_or("transport failure")
                    .to_string();
                let millis = self.timeout.as_millis() as u64;
                // `ureq` has no dedicated timeout kind: a read timeout arrives as
                // a generic IO failure whose message may be empty, while a
                // refused connection is `ConnectionFailed`.  Classify on the kind
                // first (a refused connection can spend seconds in the OS connect
                // call, so "it waited a long time" alone would mislabel it), then
                // on the message and the measured wait.
                let timed_out = match transport.kind() {
                    ureq::ErrorKind::ConnectionFailed | ureq::ErrorKind::Dns => false,
                    _ => {
                        message.to_ascii_lowercase().contains("timed out")
                            || message.to_ascii_lowercase().contains("timeout")
                            || started.elapsed() >= self.timeout
                    }
                };
                if timed_out {
                    Err(BrpError::Timeout {
                        endpoint: self.endpoint.clone(),
                        millis,
                    })
                } else {
                    Err(BrpError::Transport {
                        endpoint: self.endpoint.clone(),
                        message,
                    })
                }
            }
        }
    }
}

/// The in-process fake BRP server.
///
/// It is deliberately the *only* way the client is tested for transport
/// behaviour: no engine, no network, no port 15702.  It speaks just enough
/// HTTP/1.1 (`Content-Length` request bodies, `Connection: close` replies) for
/// `ureq` to be a real client.  It is `#[cfg(test)]`, so the battery's
/// end-to-end test lives in this crate's test module rather than in `tests/`
/// (which cannot see a crate-private double).
#[cfg(test)]
pub(crate) mod fake {
    use std::io::{Read, Write};
    use std::net::{TcpListener, TcpStream};
    use std::sync::atomic::{AtomicBool, Ordering};
    use std::sync::{Arc, Mutex};
    use std::thread::{self, JoinHandle};
    use std::time::Duration;

    /// What the server answers with, in order; the last entry repeats forever so
    /// a poll loop cannot run out of script.
    #[derive(Clone)]
    pub enum Reply {
        /// HTTP 200 with this JSON body.
        Json(serde_json::Value),
        /// HTTP 200 with this raw body (used for malformed JSON).
        Raw200(String),
        /// This HTTP status with this body.
        Status(u16, String),
        /// Wait, then answer with the inner reply.
        DelayThen(Duration, Box<Reply>),
        /// Compute the reply from the request body and the bodies that arrived
        /// before it.  This exists so a server can answer several *different*
        /// BRP methods deterministically — for example a frame counter's
        /// `world.get_resources` next to a `world.query` of the player.
        From(Arc<dyn Fn(&str, &[String]) -> Reply + Send + Sync>),
    }

    impl std::fmt::Debug for Reply {
        fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
            match self {
                Reply::Json(value) => write!(formatter, "Json({value})"),
                Reply::Raw200(body) => write!(formatter, "Raw200({body})"),
                Reply::Status(status, body) => write!(formatter, "Status({status}, {body})"),
                Reply::DelayThen(delay, inner) => {
                    write!(formatter, "DelayThen({delay:?}, {inner:?})")
                }
                Reply::From(_) => write!(formatter, "From(<fn>)"),
            }
        }
    }

    impl Reply {
        fn render(self, request: &str, prior: &[String]) -> (u16, String) {
            match self {
                Reply::Json(value) => (200, value.to_string()),
                Reply::Raw200(body) => (200, body),
                Reply::Status(status, body) => (status, body),
                Reply::DelayThen(delay, inner) => {
                    thread::sleep(delay);
                    inner.render(request, prior)
                }
                Reply::From(build) => build(request, prior).render(request, prior),
            }
        }
    }

    pub struct FakeBrp {
        addr: std::net::SocketAddr,
        stop: Arc<AtomicBool>,
        requests: Arc<Mutex<Vec<String>>>,
        failures: Arc<Mutex<Vec<String>>>,
        /// How many accepted streams were actually put back to blocking.  It is
        /// the observability that makes the D3 repair **pinned**: removing the
        /// `set_nonblocking(false)` call leaves this at zero and the named test
        /// goes red, instead of the repair disappearing unnoticed (B2-2/B2-11).
        blocking_restores: Arc<Mutex<usize>>,
        handle: Option<JoinHandle<()>>,
    }

    impl FakeBrp {
        /// Start the server with a reply script.
        pub fn spawn(script: Vec<Reply>) -> Self {
            let listener = TcpListener::bind("127.0.0.1:0").expect("a free loopback port");
            listener
                .set_nonblocking(true)
                .expect("the fake listener is nonblocking");
            let addr = listener.local_addr().expect("a bound address");
            let stop = Arc::new(AtomicBool::new(false));
            let requests = Arc::new(Mutex::new(Vec::new()));
            let failures = Arc::new(Mutex::new(Vec::new()));
            let blocking_restores = Arc::new(Mutex::new(0usize));
            let handle = {
                let stop = Arc::clone(&stop);
                let requests = Arc::clone(&requests);
                let failures = Arc::clone(&failures);
                let blocking_restores = Arc::clone(&blocking_restores);
                thread::spawn(move || {
                    let mut served = 0usize;
                    while !stop.load(Ordering::SeqCst) {
                        match listener.accept() {
                            Ok((stream, _)) => {
                                // The listener is non-blocking so the accept loop
                                // can be stopped; the accepted stream must be put
                                // back to blocking, or the client's first read
                                // becomes a race and the server can answer a
                                // request it never read (B1 acceptance D3).  The
                                // successful restore is **recorded**, so the
                                // repair is observable rather than merely present.
                                if stream.set_nonblocking(false).is_err() {
                                    if let Ok(mut seen) = failures.lock() {
                                        seen.push("the accepted stream stayed non-blocking".into());
                                    }
                                    continue;
                                }
                                if let Ok(mut count) = blocking_restores.lock() {
                                    *count += 1;
                                }
                                // A request read that fails is **not** answered as
                                // if it had arrived: the failure is recorded and
                                // the server replies with an explicit JSON-RPC
                                // error carrying the reason, so a test that reads
                                // an empty body fails loudly instead of racing.
                                let body = match read_request(stream.try_clone().expect("a clone"))
                                {
                                    Ok(body) => body,
                                    Err(reason) => {
                                        if let Ok(mut seen) = failures.lock() {
                                            seen.push(reason.clone());
                                        }
                                        let (status, text) = Reply::Json(serde_json::json!({
                                            "jsonrpc": "2.0",
                                            "id": serde_json::Value::Null,
                                            "error": {
                                                "code": -32700,
                                                "message": format!(
                                                    "the fake BRP server could not read this                                                      request: {reason}"
                                                ),
                                            },
                                        }))
                                        .render("", &[]);
                                        let _ = write_reply(stream, status, &text);
                                        continue;
                                    }
                                };
                                let prior = {
                                    let mut seen = requests.lock().expect("the request log");
                                    let prior = seen.clone();
                                    seen.push(body.clone());
                                    prior
                                };
                                let reply = script
                                    .get(served)
                                    .or_else(|| script.last())
                                    .cloned()
                                    .unwrap_or(Reply::Raw200(
                                        "{\"jsonrpc\":\"2.0\",\"id\":0,\"result\":null}"
                                            .to_string(),
                                    ));
                                served += 1;
                                let (status, text) = reply.render(&body, &prior);
                                let _ = write_reply(stream, status, &text);
                            }
                            Err(error) if error.kind() == std::io::ErrorKind::WouldBlock => {
                                thread::sleep(Duration::from_millis(2));
                            }
                            Err(_) => break,
                        }
                    }
                })
            };
            Self {
                addr,
                stop,
                requests,
                failures,
                blocking_restores,
                handle: Some(handle),
            }
        }

        /// A single normal reply.
        pub fn replying(value: serde_json::Value) -> Self {
            Self::spawn(vec![Reply::Json(value)])
        }

        pub fn endpoint(&self) -> String {
            format!("http://{}/", self.addr)
        }

        /// Every request body the server received, in arrival order.
        pub fn requests(&self) -> Vec<String> {
            self.requests
                .lock()
                .map(|seen| seen.clone())
                .unwrap_or_default()
        }

        pub fn request_count(&self) -> usize {
            self.requests().len()
        }

        /// Every request whose read failed.  A test asserts this is empty, which
        /// is what makes the double deterministic instead of probabilistic: the
        /// server cannot answer a request it did not read.
        pub fn read_failures(&self) -> Vec<String> {
            self.failures
                .lock()
                .map(|seen| seen.clone())
                .unwrap_or_default()
        }

        /// How many accepted streams were put back to blocking.  It is `0` if
        /// the accept loop ever answers without restoring blocking behaviour —
        /// which is exactly what makes the D3 repair observable (B2-2/B2-11).
        pub fn blocking_restores(&self) -> usize {
            self.blocking_restores
                .lock()
                .map(|count| *count)
                .unwrap_or(0)
        }

        /// The bodies of the requests received so far, parsed.
        pub fn parsed_requests(&self) -> Vec<serde_json::Value> {
            self.requests()
                .iter()
                .filter_map(|body| serde_json::from_str(body).ok())
                .collect()
        }

        /// A script that answers the game's frame counter, and nothing else.
        pub fn frame_counter_script() -> Vec<Reply> {
            vec![frame_counter_reply()]
        }
    }

    impl Drop for FakeBrp {
        fn drop(&mut self) {
            self.stop.store(true, Ordering::SeqCst);
            if let Some(handle) = self.handle.take() {
                let _ = handle.join();
            }
        }
    }

    /// A port that is definitely not listening: bind it, note it, close it.
    pub fn refused_port() -> u16 {
        let listener = TcpListener::bind("127.0.0.1:0").expect("a free loopback port");
        let port = listener.local_addr().expect("a bound address").port();
        drop(listener);
        port
    }

    /// How long the whole request read may take before it is a failure.
    pub const REQUEST_READ_DEADLINE: Duration = Duration::from_secs(5);

    /// Read one complete HTTP/1.1 request.  **Any** problem is an `Err` with the
    /// reason: an incomplete header, a body shorter than `Content-Length`, a
    /// closed connection, or the deadline.  Nothing here turns a failure into an
    /// empty request body (B1 acceptance D3).
    ///
    /// `WouldBlock` is retried to the deadline rather than treated as a result:
    /// the timeout on a socket and a moment of scheduling look identical at this
    /// layer, and only time can tell them apart.
    pub fn read_request(mut stream: TcpStream) -> Result<String, String> {
        stream
            .set_read_timeout(Some(Duration::from_millis(200)))
            .map_err(|error| format!("the read timeout could not be set: {error}"))?;
        let started = std::time::Instant::now();
        let mut buffer = Vec::new();
        let mut chunk = [0u8; 4096];
        let header_end = loop {
            match stream.read(&mut chunk) {
                Ok(0) if !buffer.is_empty() => {
                    return Err("the connection closed inside the request headers".to_string());
                }
                Ok(0) => {
                    return Err("the connection closed before any request byte arrived".to_string());
                }
                Ok(read) => buffer.extend_from_slice(&chunk[..read]),
                Err(error) if error.kind() == std::io::ErrorKind::WouldBlock => {}
                Err(error) if error.kind() == std::io::ErrorKind::TimedOut => {}
                Err(error) if error.kind() == std::io::ErrorKind::Interrupted => {}
                Err(error) => return Err(format!("the request read failed: {error}")),
            }
            if let Some(position) = find_header_end(&buffer) {
                break position;
            }
            if started.elapsed() >= REQUEST_READ_DEADLINE {
                return Err(format!(
                    "no complete request header arrived within {:?}",
                    REQUEST_READ_DEADLINE
                ));
            }
        };
        let headers = String::from_utf8_lossy(&buffer[..header_end]).to_string();
        let length = match content_length(&headers) {
            Some(length) => length,
            None if carries_a_body(&headers) => {
                return Err("the request declares no Content-Length".to_string());
            }
            None => 0,
        };
        let mut body = buffer[header_end + 4..].to_vec();
        while body.len() < length {
            match stream.read(&mut chunk) {
                Ok(0) => {
                    return Err(format!(
                        "the connection closed after {} of {} body bytes",
                        body.len(),
                        length
                    ));
                }
                Ok(read) => body.extend_from_slice(&chunk[..read]),
                Err(error) if error.kind() == std::io::ErrorKind::WouldBlock => {}
                Err(error) if error.kind() == std::io::ErrorKind::TimedOut => {}
                Err(error) if error.kind() == std::io::ErrorKind::Interrupted => {}
                Err(error) => return Err(format!("the body read failed: {error}")),
            }
            if body.len() < length && started.elapsed() >= REQUEST_READ_DEADLINE {
                return Err(format!(
                    "the body stalled at {} of {} bytes after {:?}",
                    body.len(),
                    length,
                    REQUEST_READ_DEADLINE
                ));
            }
        }
        Ok(String::from_utf8_lossy(&body).to_string())
    }

    fn find_header_end(buffer: &[u8]) -> Option<usize> {
        buffer.windows(4).position(|window| window == b"\r\n\r\n")
    }

    /// The `Content-Length` of a request, if it declares one.
    ///
    /// The request line (`POST / HTTP/1.1`) has no colon, and an earlier version
    /// of this scan returned `None` for the *whole function* on the first
    /// colon-less line — so every body was read as zero bytes and the fake
    /// answered requests it had never read.  Skipping colon-less lines is the
    /// fix, and it is the mechanism behind the B1 acceptance's D3.
    pub(crate) fn content_length(headers: &str) -> Option<usize> {
        for line in headers.lines() {
            let Some((name, value)) = line.split_once(':') else {
                continue;
            };
            if name.eq_ignore_ascii_case("content-length") {
                return value.trim().parse().ok();
            }
        }
        None
    }

    /// `true` when the request is a body-carrying method this fake must read
    /// fully.  A `POST` with no `Content-Length` is a failed read, not a request
    /// with an empty body.
    pub(crate) fn carries_a_body(headers: &str) -> bool {
        headers
            .lines()
            .next()
            .map(|line| {
                let line = line.trim_start();
                line.starts_with("POST") || line.starts_with("PUT") || line.starts_with("PATCH")
            })
            .unwrap_or(false)
    }

    fn write_reply(mut stream: TcpStream, status: u16, body: &str) -> std::io::Result<()> {
        let response = format!(
            "HTTP/1.1 {status} OK\r\nContent-Type: application/json\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{body}",
            body.len()
        );
        stream.write_all(response.as_bytes())?;
        stream.flush()
    }

    /// The synchronous body of [`Reply::From`] that answers the game's frame
    /// counter, so the same deterministic clock is available to every test that
    /// needs a game which advances its own frames.
    ///
    /// The value advances by one per **counter read**, determined solely by the
    /// requests the server has already seen, so it is independent of scheduling:
    /// two runs of the same test see the same frame sequence.  A real game
    /// advances with wall time; this only has to be deterministic.
    fn frame_counter_answer(request: &str, prior: &[String]) -> Reply {
        let is_counter_read = |body: &str| {
            serde_json::from_str::<serde_json::Value>(body)
                .ok()
                .map(|parsed| {
                    parsed.get("method").and_then(|method| method.as_str())
                        == Some("world.get_resources")
                        && parsed
                            .get("params")
                            .and_then(|params| params.get("resource"))
                            .and_then(|resource| resource.as_str())
                            == Some("hof_game::contract::FrameCounter")
                })
                .unwrap_or(false)
        };
        let reads = prior.iter().filter(|body| is_counter_read(body)).count() + 1;
        let id = serde_json::from_str::<serde_json::Value>(request)
            .ok()
            .and_then(|parsed| parsed.get("id").cloned())
            .unwrap_or(serde_json::Value::Null);
        Reply::Json(serde_json::json!({
            "jsonrpc": "2.0",
            "id": id,
            "result": {"value": {"frames": reads}},
        }))
    }

    /// A reply script for a fake that answers **only** the frame counter, using
    /// [`frame_counter_answer`].  `FakeBrp::frame_counter_script()` is the
    /// convenient form.
    pub fn frame_counter_reply() -> Reply {
        Reply::From(Arc::new(frame_counter_answer))
    }
}

#[cfg(test)]
mod tests {
    use super::fake::{refused_port, FakeBrp, Reply};
    use super::*;
    use serde_json::json;
    use std::io::Write;

    fn client(server: &FakeBrp) -> BrpClient {
        BrpClient::new(server.endpoint(), Duration::from_millis(1_000))
    }

    /// A reply body that carries **the id of the request it answers**, taken off
    /// the wire.  This is what a real JSON-RPC peer does, and since the client
    /// now correlates ids (D2) the test doubles have to as well.
    ///
    /// The reply is built by inserting the request's id into the given document,
    /// so a test can still hand in a document with a deliberately wrong id by
    /// setting the `id` key itself.
    fn id_echo(document: serde_json::Value) -> Reply {
        Reply::From(std::sync::Arc::new(
            move |request: &str, _prior: &[String]| {
                let id = serde_json::from_str::<serde_json::Value>(request)
                    .ok()
                    .and_then(|parsed| parsed.get("id").cloned())
                    .unwrap_or(serde_json::Value::Null);
                let mut document = document.clone();
                if let Some(object) = document.as_object_mut() {
                    if !object.contains_key("id") {
                        object.insert("id".to_string(), id);
                    }
                }
                Reply::Json(document)
            },
        ))
    }

    /// A normal success reply, correlated with the request.
    fn ok_reply(result: serde_json::Value) -> Reply {
        id_echo(json!({"jsonrpc": "2.0", "result": result}))
    }

    /// A JSON-RPC error reply, correlated with the request.
    fn error_reply(code: i64, message: &str) -> Reply {
        id_echo(json!({"jsonrpc": "2.0", "error": {"code": code, "message": message}}))
    }

    fn reply_document(body: &str) -> serde_json::Value {
        serde_json::from_str(body).expect("a JSON reply body")
    }

    #[test]
    fn a_normal_reply_comes_back_as_its_result() {
        let server = FakeBrp::replying(reply_document(
            r#"{"jsonrpc":"2.0","id":1,"result":{"ok":true}}"#,
        ));
        let value = client(&server).call("world.list_resources", None).unwrap();
        assert_eq!(value, json!({"ok": true}));
    }

    #[test]
    fn a_null_error_with_a_result_is_a_success() {
        let server = FakeBrp::replying(reply_document(
            r#"{"jsonrpc":"2.0","id":1,"error":null,"result":[]}"#,
        ));
        let value = client(&server)
            .call("world.query", Some(json!({})))
            .unwrap();
        assert_eq!(value, json!([]));
    }

    #[test]
    fn an_error_body_under_http_200_is_a_tool_error() {
        let server = FakeBrp::replying(reply_document(
            r#"{"jsonrpc":"2.0","id":1,"error":{"code":-32601,"message":"Method `world.screenshot` not found"}}"#,
        ));
        let error = client(&server).call("world.screenshot", None).unwrap_err();
        assert_eq!(error.code(), Some(-32601));
        assert!(error.is_method_not_found());
        assert!(error.to_string().contains("not found"), "{error}");
        // The status was 200: judging success by the status code would have
        // turned this refusal into a result.
        assert!(!error.is_infrastructure());
    }

    #[test]
    fn a_resource_that_is_not_present_is_a_contract_violation() {
        let server = FakeBrp::replying(reply_document(
            r#"{"jsonrpc":"2.0","id":1,"error":{"code":-23502,"message":"Unknown resource type: hof_game::contract::WinFlag"}}"#,
        ));
        let error = client(&server)
            .call("world.get_resources", Some(json!({"resource": "x"})))
            .unwrap_err();
        assert!(error.is_contract_violation());
        assert!(!error.is_infrastructure());
    }

    #[test]
    fn a_slow_reply_that_exceeds_the_timeout_is_a_timeout() {
        let server = FakeBrp::spawn(vec![Reply::DelayThen(
            Duration::from_millis(1_500),
            Box::new(ok_reply(json!(1))),
        )]);
        let quick = BrpClient::new(server.endpoint(), Duration::from_millis(250));
        let error = quick.call("rpc.discover", None).unwrap_err();
        assert!(
            matches!(error, BrpError::Timeout { .. }),
            "expected a timeout, got {error:?}"
        );
        assert!(error.is_infrastructure());
    }

    #[test]
    fn a_refused_connection_is_a_transport_failure() {
        let port = refused_port();
        let client = BrpClient::new(
            format!("http://127.0.0.1:{port}/"),
            Duration::from_millis(500),
        );
        let error = client.call("rpc.discover", None).unwrap_err();
        assert!(
            matches!(error, BrpError::Transport { .. }),
            "expected a transport failure, got {error:?}"
        );
        assert!(error.is_infrastructure());
    }

    #[test]
    fn a_malformed_body_is_a_malformed_reply() {
        let server = FakeBrp::spawn(vec![Reply::Raw200("{ this is not json".to_string())]);
        let error = client(&server).call("rpc.discover", None).unwrap_err();
        assert!(
            matches!(error, BrpError::Malformed { .. }),
            "expected a malformed reply, got {error:?}"
        );
        assert!(
            !error.is_infrastructure(),
            "a bad body is not an infrastructure failure"
        );
    }

    #[test]
    fn a_batch_reply_is_refused_rather_than_read() {
        let body = json!([{"jsonrpc": "2.0", "id": 1, "result": 1}]).to_string();
        let error = read_reply(&body, "http://127.0.0.1:1/").unwrap_err();
        assert!(matches!(error, BrpError::Malformed { .. }));
    }

    #[test]
    fn a_non_200_status_is_an_error_even_though_brp_always_answers_200() {
        let server = FakeBrp::spawn(vec![Reply::Status(500, "boom".to_string())]);
        let error = client(&server).call("rpc.discover", None).unwrap_err();
        match error {
            BrpError::HttpStatus { status, body, .. } => {
                assert_eq!(status, 500);
                assert_eq!(body, "boom");
            }
            other => panic!("expected an HTTP status error, got {other:?}"),
        }
    }

    #[test]
    fn readiness_polls_until_discover_answers() {
        let server = FakeBrp::spawn(vec![
            error_reply(-32601, "not ready"),
            ok_reply(json!({"openrpc": "1.3.2", "methodCount": 23})),
        ]);
        let value = client(&server)
            .wait_ready(Duration::from_secs(2), Duration::from_millis(10))
            .unwrap();
        assert_eq!(value["methodCount"], json!(23));
        assert!(
            server.request_count() >= 2,
            "readiness must poll, not sleep: {} request(s)",
            server.request_count()
        );
    }

    #[test]
    fn readiness_gives_up_with_the_budget_it_was_given() {
        let port = refused_port();
        let client = BrpClient::new(
            format!("http://127.0.0.1:{port}/"),
            Duration::from_millis(200),
        );
        let started = Instant::now();
        let error = client
            .wait_ready(Duration::from_millis(300), Duration::from_millis(20))
            .unwrap_err();
        assert!(
            matches!(
                error,
                BrpError::EndpointTimeout {
                    budget_millis: 300,
                    ..
                }
            ),
            "expected an endpoint timeout with its budget, got {error:?}"
        );
        assert!(started.elapsed() >= Duration::from_millis(250));
    }

    #[test]
    fn the_request_body_is_one_object_with_one_method() {
        let body = request_body(7, "world.get_components", Some(json!({"entity": 42})));
        assert_eq!(body["jsonrpc"], json!("2.0"));
        assert_eq!(body["id"], json!(7));
        assert_eq!(body["method"], json!("world.get_components"));
        assert_eq!(body["params"], json!({"entity": 42}));
        assert!(body.is_object(), "a batch (array) must be unrepresentable");
    }

    #[test]
    fn the_client_puts_exactly_that_object_on_the_wire() {
        let server = FakeBrp::spawn(vec![ok_reply(
            json!({"servers": [{"url": "127.0.0.1:15702"}]}),
        )]);
        let params = json!({"entity": 4294966889u64, "components": ["a::b::C"], "strict": true});
        let _ = client(&server)
            .call("world.get_components", Some(params.clone()))
            .unwrap();
        let seen = server.requests();
        assert_eq!(seen.len(), 1);
        let parsed: Value = serde_json::from_str(&seen[0]).unwrap();
        assert!(parsed.is_object());
        assert_eq!(parsed["method"], json!("world.get_components"));
        assert_eq!(
            parsed["params"], params,
            "params are passed through verbatim"
        );
        assert!(
            seen[0].trim_start().starts_with('{'),
            "the raw body must be a single request object: {}",
            seen[0]
        );
    }

    #[test]
    fn the_client_refuses_a_list_valued_params_payload() {
        let client = BrpClient::new(endpoint(), Duration::from_millis(50));
        let error = client
            .call(
                "world.query",
                Some(json!([{"method": "a"}, {"method": "b"}])),
            )
            .unwrap_err();
        assert!(matches!(error, BrpError::InvalidRequest(_)), "{error:?}");
    }

    #[test]
    fn every_request_carries_its_own_id_and_the_raw_document_is_available() {
        let fake = FakeBrp::spawn(vec![ok_reply(json!(1))]);
        let client = client(&fake);
        client.call("rpc.discover", None).unwrap();
        client.call("rpc.discover", None).unwrap();
        let ids: Vec<u64> = fake
            .requests()
            .iter()
            .map(|body| {
                serde_json::from_str::<Value>(body).unwrap()["id"]
                    .as_u64()
                    .unwrap()
            })
            .collect();
        assert_eq!(ids, vec![1, 2], "each request has its own correlation id");

        // `call_document` hands back the document itself, so evidence can record
        // what the engine sent instead of a re-rendered summary.  The fake echoes
        // the id it was sent, so request 99 answers as 99.
        let document = client.call_document(99, "rpc.discover", None).unwrap();
        assert_eq!(document["result"], json!(1));
        let last: Value = serde_json::from_str(fake.requests().last().unwrap()).unwrap();
        assert_eq!(
            last["id"],
            json!(99),
            "the caller decides the correlation id"
        );
    }

    // ---- B1 acceptance D1/D2: the reply must be a JSON-RPC document ----

    #[test]
    fn valid_json_that_is_not_a_json_rpc_document_is_malformed() {
        for body in ["42", "\"ok\"", "{}", "null", "{\"jsonrpc\":\"2.0\"}"] {
            let error = read_reply(body, "http://127.0.0.1:1/").unwrap_err();
            assert!(
                matches!(error, BrpError::Malformed { .. }),
                "`{body}` must be Malformed, got {error:?}"
            );
            assert!(
                !error.is_infrastructure(),
                "a bad body is not infrastructure"
            );
        }
        // A document with a null result is a success, which is the case the
        // strict shape rule must not break.
        assert_eq!(
            read_reply(
                "{\"jsonrpc\":\"2.0\",\"result\":null}",
                "http://127.0.0.1:1/"
            )
            .unwrap(),
            Value::Null
        );
        // An `error` member on its own is a JSON-RPC failure, not malformed.
        assert!(matches!(
            read_reply(
                "{\"error\":{\"code\":-1,\"message\":\"x\"}}",
                "http://127.0.0.1:1/"
            ),
            Err(BrpError::Rpc { .. })
        ));
    }

    #[test]
    fn a_reply_whose_id_is_not_the_requests_is_refused() {
        let document = json!({"jsonrpc": "2.0", "id": 7, "result": {"which": "someone else"}});
        let error = read_document_for(&document, "http://127.0.0.1:1/", Some(8)).unwrap_err();
        assert!(matches!(error, BrpError::Malformed { .. }), "{error:?}");
        assert!(error.to_string().contains("waiting"), "{error}");
        // The matching id is accepted...
        assert_eq!(
            read_document_for(&document, "http://127.0.0.1:1/", Some(7)).unwrap(),
            json!({"which": "someone else"})
        );
        // ...and a caller that passes no id (reading a recorded document) is not
        // forced to invent one.
        assert!(read_document_for(&document, "http://127.0.0.1:1/", None).is_ok());
        // A non-numeric id cannot match a request.
        let string_id = json!({"jsonrpc": "2.0", "id": "7", "result": 1});
        assert!(read_document_for(&string_id, "http://127.0.0.1:1/", Some(7)).is_err());
    }

    /// B2-9: a reply that carries **no** `id` member is not correlated either.
    /// Accepting it lets any document answer any pending request.
    #[test]
    fn a_reply_with_no_id_member_is_refused_when_an_id_is_expected() {
        let no_id = json!({"jsonrpc": "2.0", "result": 1});
        let error = read_document_for(&no_id, "http://127.0.0.1:1/", Some(9)).unwrap_err();
        assert!(matches!(error, BrpError::Malformed { .. }), "{error:?}");
        assert!(error.to_string().contains("no `id`"), "{error}");
        assert!(
            error.to_string().contains("waiting"),
            "the refusal must say which request was waiting: {error}"
        );
        // A caller with no id to correlate against (reading a recorded
        // document) is still allowed to read it.
        assert_eq!(
            read_document_for(&no_id, "http://127.0.0.1:1/", None).unwrap(),
            json!(1)
        );
    }

    /// B2-2 / B2-11: the D3 timing repair is now **observable through the
    /// in-process fake itself**.  The fake records every accepted stream it put
    /// back to blocking, so deleting `set_nonblocking(false)` from the accept
    /// loop leaves this at zero and this test goes red — the defect the
    /// acceptance could not pin with the `RawServer` defined inside
    /// `tests/bevy_adapter_b2.rs`.
    #[test]
    fn the_fake_restores_blocking_on_every_accepted_stream() {
        let server = FakeBrp::spawn(vec![ok_reply(json!(1))]);
        let value = client(&server).call("rpc.discover", None).unwrap();
        assert_eq!(value, json!(1));
        assert_eq!(
            server.read_failures(),
            Vec::<String>::new(),
            "no request read failed"
        );
        assert!(
            server.blocking_restores() >= 1,
            "the accepted stream must have been put back to blocking"
        );
    }

    // ---- B1 acceptance D3: the fake is deterministic ----

    #[test]
    fn the_fake_content_length_scan_skips_the_request_line() {
        // The colon-less request line used to abort the whole scan, so every body
        // was read as zero bytes.  That is the mechanism behind D3.
        let headers = "POST / HTTP/1.1\r\nHost: 127.0.0.1\r\nContent-Length: 42\r\n";
        assert_eq!(fake::content_length(headers), Some(42));
        assert_eq!(
            fake::content_length("GET / HTTP/1.1\r\nHost: x\r\n"),
            None,
            "a request without the header has no length"
        );
        assert!(
            !fake::carries_a_body("GET / HTTP/1.1\r\n"),
            "a GET may legitimately carry no body"
        );
        assert!(fake::carries_a_body("POST / HTTP/1.1\r\n"));
    }

    /// A request whose body never arrives must **fail**, not become an empty
    /// request that the fake then answers.
    #[test]
    fn a_request_whose_body_never_arrives_is_a_failed_read() {
        let listener = std::net::TcpListener::bind("127.0.0.1:0").expect("a port");
        let addr = listener.local_addr().expect("an address");
        let server = std::thread::spawn(move || {
            let (stream, _) = listener.accept().expect("a connection");
            fake::read_request(stream)
        });
        let mut client = std::net::TcpStream::connect(addr).expect("a connection");
        // Promise ten bytes and send two, then close.
        client
            .write_all(b"POST / HTTP/1.1\r\nHost: x\r\nContent-Length: 10\r\n\r\n{}")
            .expect("a partial request");
        client.flush().expect("flush");
        drop(client);
        let result = server.join().expect("the reader finishes");
        let error = result.expect_err("a short body must not be read as a request");
        assert!(
            error.contains("closed") || error.contains("stalled"),
            "the failure must name the reason: {error}"
        );
    }

    /// A request with a `POST` line and no `Content-Length` is refused rather
    /// than treated as bodyless.
    #[test]
    fn a_post_without_a_content_length_is_a_failed_read() {
        let listener = std::net::TcpListener::bind("127.0.0.1:0").expect("a port");
        let addr = listener.local_addr().expect("an address");
        let server = std::thread::spawn(move || {
            let (stream, _) = listener.accept().expect("a connection");
            fake::read_request(stream)
        });
        let mut client = std::net::TcpStream::connect(addr).expect("a connection");
        client
            .write_all(b"POST / HTTP/1.1\r\nHost: x\r\n\r\n")
            .expect("a request without a length");
        client.flush().expect("flush");
        drop(client);
        let error = server
            .join()
            .expect("the reader finishes")
            .expect_err("a POST without a length is not readable");
        assert!(error.contains("Content-Length"), "{error}");
    }

    #[test]
    fn the_fake_accepts_a_well_formed_request_and_records_it_whole() {
        let server = FakeBrp::replying(
            // A reply the client will accept: it carries the id it was sent.
            serde_json::from_str(r#"{"jsonrpc":"2.0","id":0,"result":1}"#).expect("a document"),
        );
        // The recorded reply's id does not matter here; the fake echoes the
        // request's id for `id_echo` scripts, and this test only checks reading.
        let listener_client = BrpClient::new(server.endpoint(), Duration::from_millis(500));
        let _ = listener_client.call("rpc.discover", Some(json!({"probe": true})));
        let seen = server.requests();
        assert_eq!(seen.len(), 1, "one request, read whole");
        let parsed: Value = serde_json::from_str(&seen[0]).expect("a complete body");
        assert_eq!(parsed["method"], json!("rpc.discover"));
        assert_eq!(parsed["params"], json!({"probe": true}));
        assert_eq!(
            server.read_failures(),
            Vec::<String>::new(),
            "no read failed"
        );
    }

    #[test]
    fn the_pinned_endpoint_is_15702() {
        assert_eq!(endpoint(), "http://127.0.0.1:15702/");
        assert_eq!(
            BrpClient::local(Duration::from_millis(10)).endpoint(),
            endpoint()
        );
        assert_ne!(BRP_PORT, 15703);
    }
}
