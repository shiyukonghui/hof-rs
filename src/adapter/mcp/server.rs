//! The thin MCP server: both tool layers bound to one BRP endpoint
//! (DESIGN-OVERVIEW §1, DESIGN-DETAIL §2, §7).
//!
//! What this layer does, and what it deliberately does not:
//!
//! * **It is a pass-through with a spine.**  A generic call sends the caller's
//!   arguments as the JSON-RPC `params`, unmodified; a semantic call goes
//!   through [`semantic::plan`].  Nothing here invents a value.
//! * **It validates before it sends.**  Every call is checked against the tool's
//!   mechanically generated schema, so a typo is an explicit refusal
//!   (`invalid_arguments`) instead of a BRP error the model has to interpret.
//! * **It is a whitelist.**  Only the 31 frozen names are callable; there is no
//!   "call any verb" door, because the design freezes the tool list.
//! * **It never batches.**  A semantic read is a sequence of single
//!   [`BrpClient::call`]s (SPIKE-2 C4: a batch is not frame-atomic).
//! * **It classifies failures.**  DESIGN-DETAIL §7 needs the gate to tell an
//!   infrastructure failure (the endpoint never came up) from a project defect
//!   (the contract type is missing), and `-32601` from both (that is *our*
//!   adapter addressing a method that does not exist — SPIKE-1 §6.3).
//! * **It binds evidence and redacts it.**  Every call becomes one
//!   [`CallEvidence`] with its sequence number, timestamp, raw request and raw
//!   reply, passed through the [`Redactor`] hook when it is recorded.
//!
//! **The frame is the game's, not ours** (D297 (b)).  Every reading and every
//! injection reports the value of the game's own reflectable frame counter
//! (`hof_game::contract::FrameCounter`), read through BRP — never the number of
//! times the adapter happened to poll.  The distinction is the whole point: a
//! jump criterion that says "rising **and** falling steps" is a claim about the
//! game advancing its own frames, and an observation ordinal cannot support it.
//! `bevy_wait_frames` therefore **waits for N frames of the game** (polling the
//! counter to a deadline, so the wall-clock frame rate does not have to be
//! trusted), and every branch that cannot read the counter answers with an
//! error instead of inventing a number.

use serde_json::{json, Value};

use crate::adapter::bevy::brp::{self, BrpClient, BrpError};
use crate::adapter::mcp::evidence::{now_millis, CallEvidence};
use crate::adapter::mcp::{find_tool, semantic, validate_input, Layer, ToolSpec};
use crate::adapter::AdapterError;

/// The game frame period the waiter advances on **when a live frame counter is
/// unavailable**: SPIKE-2 measured 60.3 FPS in the headless configuration, and
/// the design budgets frames, not seconds.  See [`FrameWaiter`].
pub const GAME_FRAME_MILLIS: u64 = 16;
/// How long `bevy_wait_frames` may spend waiting for the game's own counter to
/// advance, per requested frame.  Generous relative to the measured 60.3 FPS, so
/// a loaded machine still advances, while a stalled game still fails the call
/// instead of hanging the round.
pub const FRAME_WAIT_BUDGET_PER_FRAME_MILLIS: u64 = 250;
/// The floor on that budget, so a one-frame wait on a 4 FPS window-mode game
/// still has a chance to observe an advance.
pub const FRAME_WAIT_BUDGET_FLOOR_MILLIS: u64 = 2_000;
/// The longest `bevy_wait_frames` will ever block.
pub const FRAME_WAIT_BUDGET_CEILING_MILLIS: u64 = 60_000;
/// How long `bevy_wait_frames` sleeps between polls of the frame counter.
pub const FRAME_POLL_INTERVAL_MILLIS: u64 = 5;

/// The redaction hook (DESIGN-OVERVIEW §1 `server.rs`: 「脱敏挂钩」).  It is a
/// trait so the runtime can install the harness's secret scrubbing without this
/// module depending on the secrets configuration.
pub trait Redactor: Send + Sync {
    fn redact(&self, text: &str) -> String;
}

/// Record everything verbatim.  The default, used when no secret set is known.
#[derive(Clone, Copy, Debug, Default)]
pub struct NoRedaction;

impl Redactor for NoRedaction {
    fn redact(&self, text: &str) -> String {
        text.to_string()
    }
}

/// Scrub secret-looking assignments with the harness's existing redaction.
#[derive(Clone, Copy, Debug, Default)]
pub struct SecretRedaction;

impl Redactor for SecretRedaction {
    fn redact(&self, text: &str) -> String {
        crate::runtime::secrets::redact_secret_assignments(text)
    }
}

/// How `bevy_wait_frames` waits.  A trait, so a test can assert the *number of
/// frames* asked for without spending wall-clock time.
pub trait FrameWaiter: Send + Sync {
    fn wait(&self, frames: u32);
}

/// Sleep `frames * GAME_FRAME_MILLIS`.
#[derive(Clone, Copy, Debug)]
pub struct WallClockWaiter {
    pub frame_millis: u64,
}

impl Default for WallClockWaiter {
    fn default() -> Self {
        Self {
            frame_millis: GAME_FRAME_MILLIS,
        }
    }
}

impl FrameWaiter for WallClockWaiter {
    fn wait(&self, frames: u32) {
        std::thread::sleep(std::time::Duration::from_millis(
            u64::from(frames) * self.frame_millis,
        ));
    }
}

/// A classified tool failure.  `kind` is the vocabulary the gate reads
/// (`infrastructure_failure` never counts as a project defect; `contract_violation`
/// always does).
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ToolError {
    pub kind: &'static str,
    /// The verbatim JSON-RPC code, when there was one.
    pub code: Option<i64>,
    pub message: String,
}

impl ToolError {
    pub fn new(kind: &'static str, message: impl Into<String>) -> Self {
        Self {
            kind,
            code: None,
            message: message.into(),
        }
    }

    pub fn to_json(&self) -> Value {
        json!({"kind": self.kind, "code": self.code, "message": self.message})
    }
}

/// One tool call's outcome, with everything the evidence needs.
#[derive(Clone, Debug, PartialEq)]
pub struct ToolCall {
    pub seq: u64,
    pub tool: String,
    pub layer: Layer,
    pub brp_methods: Vec<String>,
    pub requests: Vec<Value>,
    pub responses: Vec<Value>,
    pub result: Option<Value>,
    pub error: Option<ToolError>,
}

impl ToolCall {
    fn refused(seq: u64, tool: &str, layer: Layer, error: ToolError) -> Self {
        Self {
            seq,
            tool: tool.to_string(),
            layer,
            brp_methods: Vec::new(),
            requests: Vec::new(),
            responses: Vec::new(),
            result: None,
            error: Some(error),
        }
    }

    pub fn ok(&self) -> bool {
        self.error.is_none()
    }

    /// The evidence record, redacted on the way in.
    pub fn to_evidence(&self, redactor: &dyn Redactor, timestamp_ms: u128) -> CallEvidence {
        CallEvidence {
            seq: self.seq,
            tool: self.tool.clone(),
            layer: self.layer.as_str(),
            brp_methods: self.brp_methods.clone(),
            requests: self
                .requests
                .iter()
                .map(|value| redact_value(redactor, value))
                .collect(),
            responses: self
                .responses
                .iter()
                .map(|value| redact_value(redactor, value))
                .collect(),
            result: self
                .result
                .clone()
                .map(|value| redact_value(redactor, &value)),
            error: self
                .error
                .as_ref()
                .map(|error| redact_value(redactor, &error.to_json())),
            timestamp_ms,
        }
    }
}

/// A game process the server knows about, for `bevy_health`.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct GameProcess {
    pub pid: u32,
    pub stderr_tail: String,
}

/// Both tool layers over one BRP endpoint.
pub struct BevyMcpServer {
    client: BrpClient,
    process: Option<GameProcess>,
    next_seq: u64,
    /// The **last game frame observed** through the contract's
    /// `FrameCounter` resource.  It is a cache of a measurement, never a count
    /// of our own calls (D297 (b)): it starts at `None`, meaning "not observed
    /// yet", and a reading taken before any successful counter read is an
    /// error rather than a zero.
    game_frame: Option<u64>,
    redactor: Box<dyn Redactor>,
    waiter: Box<dyn FrameWaiter>,
}

impl std::fmt::Debug for BevyMcpServer {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("BevyMcpServer")
            .field("endpoint", &self.client.endpoint())
            .field("process", &self.process)
            .field("next_seq", &self.next_seq)
            .field("game_frame", &self.game_frame)
            .finish()
    }
}

impl BevyMcpServer {
    pub fn new(client: BrpClient) -> Self {
        Self {
            client,
            process: None,
            next_seq: 0,
            game_frame: None,
            redactor: Box::new(NoRedaction),
            waiter: Box::new(WallClockWaiter::default()),
        }
    }

    pub fn with_redactor(mut self, redactor: Box<dyn Redactor>) -> Self {
        self.redactor = redactor;
        self
    }

    pub fn with_waiter(mut self, waiter: Box<dyn FrameWaiter>) -> Self {
        self.waiter = waiter;
        self
    }

    pub fn endpoint(&self) -> &str {
        self.client.endpoint()
    }

    /// Tell the server which process `bevy_health` should report on.
    pub fn install_process(&mut self, process: GameProcess) {
        self.process = Some(process);
    }

    pub fn clear_process(&mut self) {
        self.process = None;
    }

    /// The last game frame observed through the contract's frame counter, or
    /// `None` when it has never been read.  It is **not** an observation
    /// ordinal: the server has no such counter any more (D297 (b)).
    pub fn game_frame(&self) -> Option<u64> {
        self.game_frame
    }

    /// Read the game's own frame counter, one BRP call (never a batch).
    ///
    /// The counter is a resource under the frozen crate
    /// (`hof_game::contract::FrameCounter`, field `frames`), so a game that does
    /// not register it is a **contract violation** — the E3 criteria are
    /// undecidable without it — and a reply that is not an integer frame is
    /// `malformed_reply`.  Neither is ever turned into a zero.
    pub fn read_game_frame(&self) -> Result<u64, ToolError> {
        let step = semantic::frame_read_plan();
        let document = self
            .client
            .call_document(
                self.client.next_id(),
                step.method,
                Some(step.params.clone()),
            )
            .map_err(|error| classify(&semantic::classify_brp_error(&error)))?;
        let result = brp::read_document(&document, self.client.endpoint())
            .map_err(|error| classify(&semantic::classify_brp_error(&error)))?;
        semantic::project_game_frame(&result).map_err(|error| classify(&error))
    }

    /// Update the cached game frame from one reading.  The cache is only ever
    /// written from a measurement, so `None` means "never observed".
    fn remember_game_frame(&mut self, frame: u64) {
        self.game_frame = Some(frame);
    }

    /// The frozen `tools/list` payload.
    pub fn tools_list(&self) -> Value {
        crate::adapter::mcp::tool_list()
    }

    /// Look up a tool and validate the arguments.  Split out so both `call` and
    /// tests can use the same gate.
    pub fn resolve(&self, tool: &str, args: &Value) -> Result<ToolSpec, ToolError> {
        let spec = find_tool(tool).ok_or_else(|| {
            ToolError::new(
                "unknown_tool",
                format!(
                    "`{tool}` is not in the frozen tool surface ({} generic BRP verbs + {} \
                     semantic tools); call `tools/list` for the exact names",
                    crate::adapter::mcp::generic::BRP_VERBS.len(),
                    crate::adapter::mcp::semantic::SEMANTIC_TOOL_SPECS.len()
                ),
            )
        })?;
        validate_input(&spec.input_schema(), args)
            .map_err(|message| ToolError::new("invalid_arguments", message))?;
        Ok(spec)
    }

    /// One tool call.  Never panics: every failure path is a [`ToolError`].
    pub fn call(&mut self, tool: &str, args: Value) -> ToolCall {
        self.next_seq += 1;
        let seq = self.next_seq;
        let spec = match self.resolve(tool, &args) {
            Ok(spec) => spec,
            Err(error) => {
                let layer = find_tool(tool)
                    .map(|spec| spec.layer)
                    .unwrap_or(Layer::Generic);
                return ToolCall::refused(seq, tool, layer, error);
            }
        };
        match spec.layer {
            Layer::Generic => self.call_generic(seq, &spec, args),
            Layer::Semantic => {
                let call = self.call_semantic(seq, &spec, &args);
                // Remember the frame the game was on, when the call managed to
                // read it: the cache is a measurement, so it is only ever
                // updated from one.
                if let Some(Value::Number(number)) =
                    call.result.as_ref().and_then(|value| value.get("frame"))
                {
                    if let Some(frame) = number.as_u64() {
                        self.game_frame = Some(frame);
                    }
                }
                call
            }
        }
    }

    /// One tool call plus its evidence record.
    pub fn call_with_evidence(&mut self, tool: &str, args: Value) -> (ToolCall, CallEvidence) {
        let call = self.call(tool, args);
        let evidence = call.to_evidence(&*self.redactor, now_millis());
        (call, evidence)
    }

    fn call_generic(&mut self, seq: u64, spec: &ToolSpec, args: Value) -> ToolCall {
        let method = spec.method.unwrap_or(spec.name);
        // Pass-through, with one mechanical rule: an empty argument object means
        // "no params at all", because BRP's `Option<Params>` distinguishes
        // `None` (e.g. `world.list_components` = every registered component)
        // from `Some({})` (a missing required field, i.e. an error).
        let empty = args
            .as_object()
            .map(|object| object.is_empty())
            .unwrap_or(true);
        let params = if empty { None } else { Some(args.clone()) };
        let request = brp::request_body(seq, method, params.clone());
        let mut call = ToolCall {
            seq,
            tool: spec.name.to_string(),
            layer: Layer::Generic,
            brp_methods: vec![method.to_string()],
            requests: vec![request],
            responses: Vec::new(),
            result: None,
            error: None,
        };
        match self.client.call_document(seq, method, params) {
            Ok(document) => {
                call.responses.push(document.clone());
                match brp::read_document(&document, self.client.endpoint()) {
                    Ok(result) => {
                        call.result = Some(result);
                        call
                    }
                    Err(error) => {
                        call.error = Some(classify(&semantic::classify_brp_error(&error)));
                        call
                    }
                }
            }
            Err(error) => {
                call.error = Some(classify(&semantic::classify_brp_error(&error)));
                call
            }
        }
    }

    fn call_semantic(&mut self, seq: u64, spec: &ToolSpec, args: &Value) -> ToolCall {
        let tool = spec.name;
        let mut call = ToolCall {
            seq,
            tool: tool.to_string(),
            layer: Layer::Semantic,
            brp_methods: Vec::new(),
            requests: Vec::new(),
            responses: Vec::new(),
            result: None,
            error: None,
        };

        // Process health is not ECS state at all, and it needs no frame.
        if tool == "bevy_health" {
            return match &self.process {
                Some(process) => {
                    call.result = Some(json!({
                        "alive": true,
                        "stderr_tail": process.stderr_tail,
                    }));
                    call
                }
                None => {
                    call.error = Some(ToolError::new(
                        "no_game_process",
                        "no game process is registered with this server, so its health is unknown \
                         (an unknown process is never reported as alive)",
                    ));
                    call
                }
            };
        }

        // EVERY other semantic call reports the GAME's frame (D297 (b)), so the
        // counter is read first, one call at a time, and a counter that cannot be
        // read is an error rather than a made-up number.  The read goes through
        // the same recording path as the plan's steps, so a reading's evidence
        // contains the counter call that produced its `frame`.
        let frame = match self
            .exec_step(&mut call, seq, &semantic::frame_read_plan())
            .and_then(|result| {
                semantic::project_game_frame(&result).map_err(|error| classify(&error))
            }) {
            Ok(frame) => {
                self.remember_game_frame(frame);
                frame
            }
            Err(error) => {
                call.error = Some(error);
                return call;
            }
        };

        if tool == "bevy_wait_frames" {
            // Frame advance waits for the game itself to move, then reports
            // where the game got to.
            let frames = args.get("n").and_then(Value::as_u64).unwrap_or(0) as u32;
            return match self.wait_game_frames(frames, &mut call, seq) {
                Ok(after) => {
                    call.result = Some(json!({"frame_after": after}));
                    call
                }
                Err(error) => {
                    call.error = Some(error);
                    call
                }
            };
        }

        let plan = match semantic::plan(tool, args) {
            Ok(plan) => plan,
            Err(error) => {
                call.error = Some(classify(&error));
                return call;
            }
        };
        // The surface's replies only (the frame counter's was consumed above and
        // `frame` is the value read from it, so it cannot be a stale cache).
        let mut surface_results: Vec<Value> = Vec::new();
        for step in &plan {
            match self.exec_step(&mut call, seq, step) {
                Ok(value) => surface_results.push(value),
                Err(error) => {
                    call.error = Some(error);
                    return call;
                }
            }
        }
        match semantic::project(tool, &surface_results, frame) {
            Ok(result) => {
                call.result = Some(result);
                call
            }
            Err(error) => {
                call.error = Some(classify(&error));
                call
            }
        }
    }

    /// Run one BRP step and record it the way the evidence needs it: the method,
    /// the request document, and the raw reply, all in the tool call.
    ///
    /// Recording happens here rather than at the call sites so that no call can
    /// reach the wire without appearing in the evidence — including the frame
    /// counter read, which is what makes `frame` auditable.
    fn exec_step(
        &self,
        call: &mut ToolCall,
        seq: u64,
        step: &semantic::BrpStep,
    ) -> Result<Value, ToolError> {
        call.brp_methods.push(step.method.to_string());
        call.requests.push(brp::request_body(
            seq,
            step.method,
            Some(step.params.clone()),
        ));
        let document = self
            .client
            .call_document(seq, step.method, Some(step.params.clone()))
            .map_err(|error| classify(&semantic::classify_brp_error(&error)))?;
        let result = brp::read_document(&document, self.client.endpoint())
            .map_err(|error| classify(&semantic::classify_brp_error(&error)))?;
        call.responses.push(document);
        Ok(result)
    }

    /// Wait for the game's own frame counter to advance by `frames`, polling to
    /// a deadline derived from the measured headless frame rate.
    ///
    /// [`FrameWaiter`] is still used first: it is the seam that lets a test spend
    /// no wall-clock time.  What changed with D297 (b) is that the *number* the
    /// waiter is asked for is not the answer — the answer is the counter's value
    /// after the wait, and a counter that fails to advance inside the budget is
    /// an explicit failure instead of a silently stale frame.
    fn wait_game_frames(
        &mut self,
        frames: u32,
        call: &mut ToolCall,
        seq: u64,
    ) -> Result<u64, ToolError> {
        let step = semantic::frame_read_plan();
        let started = semantic::project_game_frame(&self.exec_step(call, seq, &step)?)
            .map_err(|error| classify(&error))?;
        self.game_frame = Some(started);
        self.waiter.wait(frames);
        let budget_millis = (u64::from(frames) * FRAME_WAIT_BUDGET_PER_FRAME_MILLIS).clamp(
            FRAME_WAIT_BUDGET_FLOOR_MILLIS,
            FRAME_WAIT_BUDGET_CEILING_MILLIS,
        );
        let deadline = std::time::Instant::now() + std::time::Duration::from_millis(budget_millis);
        let target = started.saturating_add(u64::from(frames));
        loop {
            let observed = semantic::project_game_frame(&self.exec_step(call, seq, &step)?)
                .map_err(|error| classify(&error))?;
            self.game_frame = Some(observed);
            if frames == 0 || observed >= target {
                return Ok(observed);
            }
            if std::time::Instant::now() >= deadline {
                return Err(ToolError::new(
                    "frame_wait_timeout",
                    format!(
                        "the game's frame counter stayed at {observed} (wanted {target}) for \
                         {budget_millis} ms: the game is not advancing its own frames, so a \
                         reading cannot claim it moved"
                    ),
                ));
            }
            std::thread::sleep(std::time::Duration::from_millis(FRAME_POLL_INTERVAL_MILLIS));
        }
    }
}

/// Map an [`AdapterError`] onto the gate vocabulary.
pub fn classify(error: &AdapterError) -> ToolError {
    let (kind, code): (&'static str, Option<i64>) = match error {
        AdapterError::ContractViolation(_) => ("contract_violation", None),
        AdapterError::BuildBudgetExceeded { .. } => ("build_budget_exceeded", None),
        AdapterError::EndpointTimeout { .. } => ("infrastructure_failure", None),
        AdapterError::Transport { .. } => ("transport", None),
        AdapterError::Rpc { code, .. } if *code == -32601 => ("adapter_bug", Some(-32601)),
        AdapterError::Rpc { code, .. } => ("brp_error", Some(*code)),
        AdapterError::Malformed(_) => ("malformed_reply", None),
        AdapterError::Unsupported { .. } => ("unsupported", None),
    };
    ToolError {
        kind,
        code,
        message: error.to_string(),
    }
}

/// Redact every string inside a JSON value, keeping the document's shape.
pub fn redact_value(redactor: &dyn Redactor, value: &Value) -> Value {
    match value {
        Value::String(text) => Value::String(redactor.redact(text)),
        Value::Array(items) => Value::Array(
            items
                .iter()
                .map(|item| redact_value(redactor, item))
                .collect(),
        ),
        Value::Object(map) => Value::Object(
            map.iter()
                .map(|(key, value)| (key.clone(), redact_value(redactor, value)))
                .collect(),
        ),
        other => other.clone(),
    }
}

/// A `BrpError` on its own (without the semantic layer's contract mapping).
pub fn classify_brp(error: &BrpError) -> ToolError {
    classify(&semantic::classify_brp_error(error))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::adapter::bevy::brp::fake::{self, FakeBrp, Reply};
    use std::sync::Arc;
    use std::time::Duration;

    fn server(script: Vec<Reply>) -> (FakeBrp, BevyMcpServer) {
        let fake = FakeBrp::spawn(script);
        let client = BrpClient::new(fake.endpoint(), Duration::from_millis(1_000));
        (fake, BevyMcpServer::new(client))
    }

    /// Put the request's own id into the given document, so a fake speaks the
    /// correlation the client now enforces (D2).
    fn id_echo(document: Value) -> Reply {
        Reply::From(Arc::new(move |request: &str, _prior: &[String]| {
            let id = serde_json::from_str::<Value>(request)
                .ok()
                .and_then(|parsed| parsed.get("id").cloned())
                .unwrap_or(Value::Null);
            let mut document = document.clone();
            if let Some(object) = document.as_object_mut() {
                if !object.contains_key("id") {
                    object.insert("id".to_string(), id);
                }
            }
            Reply::Json(document)
        }))
    }

    fn ok_reply(result: Value) -> Reply {
        id_echo(json!({"jsonrpc": "2.0", "result": result}))
    }

    fn error_reply(code: i64, message: &str) -> Reply {
        id_echo(json!({"jsonrpc": "2.0", "error": {"code": code, "message": message}}))
    }

    /// A fake that answers **everything** with one result, including the game's
    /// frame counter.  Used by the tests whose subject is not the frame.
    fn everything_fake(result: Value) -> (FakeBrp, BevyMcpServer) {
        server(vec![ok_reply(result)])
    }

    /// A fake that answers the frame counter deterministically and routes
    /// `world.query` through `answer` (received request, prior requests), so a
    /// semantic read can be pinned without scripting every call by hand.
    ///
    /// A `world.get_resources` of anything other than the frame counter is
    /// answered with a fixed `{"value": …}` shape, which is what the resource
    /// projections consume.
    fn frame_fake(
        answer: impl Fn(&Value, &[Value]) -> Value + Send + Sync + 'static,
    ) -> (FakeBrp, BevyMcpServer) {
        let reply = Reply::From(Arc::new(move |request: &str, prior: &[String]| {
            let parsed: Value = serde_json::from_str(request).expect("a JSON request body");
            let prior: Vec<Value> = prior
                .iter()
                .filter_map(|body| serde_json::from_str(body).ok())
                .collect();
            if parsed["method"] == json!("world.get_resources") {
                if parsed["params"]["resource"] == json!(semantic::FRAME_COUNTER_PATH) {
                    return fake::frame_counter_reply();
                }
                // The other resources the layer reads (coin counter, win flag).
                // `answer` may supply the resource value; when it does not, the
                // projection is exercised with an empty resource instead.
                let value = answer(&parsed, &prior);
                if value.get("value").is_some() {
                    return id_echo(json!({"jsonrpc": "2.0", "result": value}));
                }
                return id_echo(json!({"jsonrpc": "2.0", "result": {"value": {}}}));
            }
            id_echo(json!({"jsonrpc": "2.0", "result": answer(&parsed, &prior)}))
        }));
        server(vec![reply])
    }

    /// The frame the fake will report on the `n`th counter read (it starts at 1).
    fn fake_frame(n: usize) -> u64 {
        n as u64
    }

    /// The parsed request bodies the fake received for one BRP method, in order.
    fn requests_for(fake: &FakeBrp, method: &str) -> Vec<Value> {
        fake.parsed_requests()
            .into_iter()
            .filter(|request| request["method"] == json!(method))
            .collect()
    }

    #[test]
    fn an_unknown_tool_is_refused_by_name() {
        let (_fake, mut server) = server(vec![ok_reply(json!({}))]);
        let call = server.call("entity_query", json!({}));
        let error = call.error.unwrap();
        assert_eq!(error.kind, "unknown_tool");
        assert!(error.message.contains("entity_query"), "{}", error.message);
        assert_eq!(call.seq, 1);
        assert!(
            call.brp_methods.is_empty(),
            "a refused call must not reach BRP"
        );
    }

    #[test]
    fn a_typo_in_a_parameter_is_refused_before_the_wire() {
        let (fake, mut server) = server(vec![ok_reply(json!({}))]);
        let call = server.call("world.get_resources", json!({"resource_type": "x"}));
        let error = call.error.unwrap();
        assert_eq!(error.kind, "invalid_arguments");
        assert!(error
            .message
            .contains("missing required parameter `resource`"));
        assert_eq!(
            fake.request_count(),
            0,
            "validation happens before the request"
        );
    }

    #[test]
    fn a_generic_call_passes_the_arguments_through_verbatim() {
        let (fake, mut server) = server(vec![ok_reply(json!({"components": {}}))]);
        let args = json!({"entity": 4294966889u64, "components": ["bevy_transform::components::transform::Transform"], "strict": true});
        let call = server.call("world.get_components", args.clone());
        assert!(call.ok(), "{:?}", call.error);
        assert_eq!(call.layer, Layer::Generic);
        assert_eq!(call.brp_methods, vec!["world.get_components"]);
        let seen: Value = serde_json::from_str(&fake.requests()[0]).unwrap();
        assert_eq!(seen["method"], json!("world.get_components"));
        assert_eq!(
            seen["params"], args,
            "no re-shaping, no reordering of meaning"
        );
        assert_eq!(seen["jsonrpc"], json!("2.0"));
    }

    #[test]
    fn an_empty_argument_object_means_no_params_at_all() {
        // `world.list_components` without params lists every registered
        // component; with `{}` BRP would refuse it for a missing `entity`.
        let (fake, mut server) = server(vec![ok_reply(json!(["a::B"]))]);
        let call = server.call("world.list_components", json!({}));
        assert!(call.ok(), "{:?}", call.error);
        let seen: Value = serde_json::from_str(&fake.requests()[0]).unwrap();
        assert!(
            seen.get("params").is_none(),
            "params must be absent: {seen}"
        );
        assert_eq!(seen["method"], json!("world.list_components"));
    }

    #[test]
    fn a_semantic_read_asks_for_the_component_it_projects() {
        let (fake, mut server) = frame_fake(
            |_request, _prior| json!([{"entity": 7, "components": {semantic::GROUNDED_PATH: {"on_ground": true}}}]),
        );
        let call = server.call("bevy_grounded", json!({}));
        assert!(call.ok(), "{:?}", call.error);
        let queries = requests_for(&fake, "world.query");
        assert_eq!(queries.len(), 1, "one surface read, one query");
        let seen = &queries[0];
        assert_eq!(
            seen["params"]["filter"]["with"],
            json!([semantic::PLAYER_PATH])
        );
        assert_eq!(
            seen["params"]["data"]["components"][0],
            json!(semantic::GROUNDED_PATH),
            "the read must ask for the component it projects",
        );
        assert_eq!(
            call.brp_methods,
            vec!["world.get_resources", "world.query"],
            "the frame counter's read is recorded as part of the call"
        );
    }

    /// D297 (b): the frame a reading reports is the GAME's, read from the
    /// contract's counter — the server keeps no observation ordinal at all, so
    /// the only way this number can appear is by reading the game.
    #[test]
    fn a_reading_reports_the_games_own_frame_not_an_observation_ordinal() {
        let (fake, mut server) = frame_fake(
            |_request, _prior| json!([{"entity": 7, "components": {semantic::GROUNDED_PATH: {"on_ground": true}}}]),
        );
        // Three reads: the counter is read once per semantic call, so the third
        // call reports the third counter value, not the third call's own number.
        let first = server.call("bevy_grounded", json!({}));
        let second = server.call("bevy_grounded", json!({}));
        let third = server.call("bevy_grounded", json!({}));
        assert_eq!(first.result.unwrap()["frame"], json!(fake_frame(1)));
        assert_eq!(third.result.unwrap()["frame"], json!(fake_frame(3)));
        let _ = second;
        assert_eq!(server.game_frame(), Some(fake_frame(3)));
        // And the counter read really happened, one call per reading.
        let counter_reads = fake
            .parsed_requests()
            .iter()
            .filter(|request| {
                request["method"] == json!("world.get_resources")
                    && request["params"]["resource"] == json!(semantic::FRAME_COUNTER_PATH)
            })
            .count();
        assert_eq!(counter_reads, 3, "one counter read per semantic call");
    }

    #[test]
    fn a_missing_frame_counter_is_a_contract_violation_not_a_zero() {
        let (fake, mut server) = server(vec![error_reply(
            -23502,
            "Unknown resource type: hof_game::contract::FrameCounter",
        )]);
        let call = server.call("bevy_grounded", json!({}));
        let error = call.error.unwrap();
        assert_eq!(error.kind, "contract_violation");
        assert!(error.message.contains("FrameCounter"), "{}", error.message);
        assert_eq!(fake.request_count(), 1);
        assert_eq!(server.game_frame(), None);
    }

    #[test]
    fn a_frame_counter_that_is_not_an_integer_is_malformed() {
        let (_fake, mut server) = server(vec![ok_reply(json!({"value": "soon"}))]);
        let call = server.call("bevy_grounded", json!({}));
        assert_eq!(call.error.unwrap().kind, "malformed_reply");
        assert_eq!(server.game_frame(), None);
    }

    #[test]
    fn a_batch_is_never_sent_even_for_a_multi_step_future() {
        // The property is structural, but it is checked on the wire as well: one
        // HTTP request per BRP call, each body a single object.
        let (fake, mut server) = frame_fake(
            |_request, _prior| json!([{"entity": 7, "components": {semantic::TRANSFORM_PATH: {"translation": [1.0, 2.0, 0.0]}}}]),
        );
        let call = server.call("bevy_player_transform", json!({}));
        assert!(call.ok(), "{:?}", call.error);
        for body in fake.requests() {
            let parsed: Value = serde_json::from_str(&body).unwrap();
            assert!(parsed.is_object(), "a batch body was sent: {body}");
        }
        assert_eq!(fake.read_failures(), Vec::<String>::new());
        for request in &call.requests {
            assert!(request.is_object());
        }
    }

    #[test]
    fn an_injection_writes_the_contract_field_and_reports_acceptance() {
        let (fake, mut server) = frame_fake(|_request, _prior| Value::Null);
        let call = server.call("bevy_inject_move", json!({"dir": 1, "level": true}));
        assert!(call.ok(), "{:?}", call.error);
        assert_eq!(
            call.result,
            Some(json!({"accepted": true, "frame": fake_frame(1)}))
        );
        let seen = requests_for(&fake, "world.mutate_resources")
            .into_iter()
            .next()
            .expect("the injection reached the wire");
        assert_eq!(seen["method"], json!("world.mutate_resources"));
        assert_eq!(
            seen["params"]["resource"],
            json!(semantic::INPUT_INTENT_PATH)
        );
        assert_eq!(seen["params"]["path"], json!("move_dir"));
        assert_eq!(seen["params"]["value"], json!(1));
    }

    #[test]
    fn an_injection_with_the_wrong_level_is_refused_by_the_schema() {
        let (_fake, mut server) = everything_fake(Value::Null);
        let call = server.call("bevy_inject_move", json!({"dir": 1, "level": false}));
        assert_eq!(call.error.unwrap().kind, "invalid_arguments");
        let call = server.call("bevy_inject_move", json!({"dir": 9, "level": true}));
        assert_eq!(call.error.unwrap().kind, "invalid_arguments");
    }

    #[test]
    fn an_unregistered_contract_type_is_a_contract_violation_not_a_zero() {
        // The frame counter answers (it is the game under test's first call);
        // the coin counter is the surface the game failed to register.
        let reply = Reply::From(Arc::new(|request: &str, _prior: &[String]| {
            let parsed: Value = serde_json::from_str(request).expect("a JSON request body");
            if parsed["params"]["resource"] == json!(semantic::FRAME_COUNTER_PATH) {
                return fake::frame_counter_reply();
            }
            error_reply(
                -23502,
                "Unknown resource type: hof_game::contract::CoinCounter",
            )
        }));
        let (_fake, mut server) = server(vec![reply]);
        let call = server.call("bevy_coin_counter", json!({}));
        let error = call.error.unwrap();
        assert_eq!(error.kind, "contract_violation");
        assert_eq!(error.code, None);
        assert!(error.message.contains("CoinCounter"), "{}", error.message);
    }

    #[test]
    fn a_method_not_found_is_an_adapter_bug_not_a_project_defect() {
        let (_fake, mut server) =
            server(vec![error_reply(-32601, "Method `world.nope` not found")]);
        let call = server.call("world.nope", json!({}));
        // Unknown tool, first: the whitelist refuses before any request.
        assert_eq!(call.error.unwrap().kind, "unknown_tool");
        let error = classify_brp(&BrpError::Rpc {
            code: -32601,
            message: "Method `world.nope` not found".to_string(),
        });
        assert_eq!(error.kind, "adapter_bug");
        assert_eq!(error.code, Some(-32601));
    }

    #[test]
    fn an_endpoint_that_never_answers_is_an_infrastructure_failure() {
        let error = classify(&AdapterError::EndpointTimeout {
            endpoint: "http://127.0.0.1:15702/".to_string(),
            budget_millis: 30_000,
        });
        assert_eq!(error.kind, "infrastructure_failure");
        let transport = classify(&AdapterError::Transport {
            endpoint: "http://127.0.0.1:15702/".to_string(),
            message: "Connection refused".to_string(),
        });
        assert_eq!(transport.kind, "transport");
    }

    #[test]
    fn frame_advance_waits_for_the_games_counter_and_reports_where_it_got_to() {
        #[derive(Clone, Default)]
        struct RecordingWaiter(std::sync::Arc<std::sync::Mutex<Vec<u32>>>);
        impl FrameWaiter for RecordingWaiter {
            fn wait(&self, frames: u32) {
                self.0.lock().unwrap().push(frames);
            }
        }
        let waiter = RecordingWaiter::default();
        let seen = waiter.clone();
        let (fake, server) = server(FakeBrp::frame_counter_script());
        let mut server = server.with_waiter(Box::new(waiter));
        let call = server.call("bevy_wait_frames", json!({"n": 3}));
        assert!(call.ok(), "{:?}", call.error);
        // The answer is the game's counter value on the poll that found it had
        // advanced far enough — never `start + 3` computed by the adapter.  The
        // fake advances one frame per counter read, so the only numbers that may
        // appear are real counter readings.
        let frame_after = call.result.unwrap()["frame_after"].as_u64().unwrap();
        let readings: Vec<u64> = call
            .responses
            .iter()
            .filter_map(|document| document["result"]["value"]["frames"].as_u64())
            .collect();
        assert!(
            readings.len() > 1,
            "the counter must be polled, not assumed: {readings:?}"
        );
        assert_eq!(
            frame_after,
            *readings.last().expect("a counter reading"),
            "the reported frame is the last counter reading"
        );
        assert!(
            frame_after >= readings[0] + 3,
            "the game must have advanced by the 3 requested frames: {readings:?}"
        );
        assert_eq!(*seen.0.lock().unwrap(), vec![3]);
        // Every counter read that produced the answer is in the evidence.
        assert_eq!(call.brp_methods.len(), readings.len());
        assert_eq!(
            requests_for(&fake, "world.get_resources").len(),
            readings.len()
        );
    }

    #[test]
    fn a_counter_that_never_moves_fails_the_frame_wait_explicitly() {
        // A frozen counter: the fake knows one frame and always answers it, so
        // the deadline is reached and the wait reports why instead of reporting
        // a frame the game never reached.
        let frozen = Reply::From(Arc::new(|request: &str, _prior: &[String]| {
            let id = serde_json::from_str::<Value>(request)
                .ok()
                .and_then(|parsed| parsed.get("id").cloned())
                .unwrap_or(Value::Null);
            Reply::Json(json!({"jsonrpc": "2.0", "id": id, "result": {"value": {"frames": 7}}}))
        }));
        let (_fake, mut server) = server(vec![frozen]);
        let call = server.call("bevy_wait_frames", json!({"n": 2}));
        let error = call.error.unwrap();
        assert_eq!(error.kind, "frame_wait_timeout");
        assert!(error.message.contains("stayed at 7"), "{}", error.message);
    }

    #[test]
    fn health_without_a_registered_process_is_unknown_not_alive() {
        let (_fake, mut server) = everything_fake(Value::Null);
        let call = server.call("bevy_health", json!({}));
        assert_eq!(call.error.unwrap().kind, "no_game_process");
        server.install_process(GameProcess {
            pid: 4711,
            stderr_tail: "panicked at src/main.rs".to_string(),
        });
        let call = server.call("bevy_health", json!({}));
        assert_eq!(
            call.result,
            Some(json!({"alive": true, "stderr_tail": "panicked at src/main.rs"}))
        );
        server.clear_process();
        assert_eq!(
            server.call("bevy_health", json!({})).error.unwrap().kind,
            "no_game_process"
        );
    }

    #[test]
    fn the_tool_list_is_the_frozen_surface() {
        let (_fake, server) = everything_fake(Value::Null);
        let list = server.tools_list();
        let names: Vec<&str> = list["tools"]
            .as_array()
            .unwrap()
            .iter()
            .map(|tool| tool["name"].as_str().unwrap())
            .collect();
        assert_eq!(names.len(), 31);
        assert_eq!(names[0], "rpc.discover");
        assert_eq!(names[22], "schedule.graph");
        assert_eq!(names[23], "bevy_player_transform");
        assert_eq!(names[30], "bevy_health");
        assert_eq!(
            list["tools"][0]["inputSchema"]["additionalProperties"],
            json!(false)
        );
        // D297 (c): the semantic layer's return shapes are in the list, and the
        // generic layer's are not (BRP owns those shapes).
        assert!(
            list["tools"][0].get("outputSchema").is_none(),
            "a generic pass-through tool must not restate BRP's output shape"
        );
        for index in 23..31 {
            let tool = &list["tools"][index];
            assert_eq!(
                tool["outputSchema"]["additionalProperties"],
                json!(false),
                "{} must publish its frozen output shape",
                tool["name"]
            );
        }
        assert_eq!(
            list["tools"][23]["outputSchema"]["required"],
            json!(["x", "y", "frame"])
        );
        assert_eq!(
            list["tools"][30]["outputSchema"]["required"],
            json!(["alive", "stderr_tail"])
        );
    }

    #[test]
    fn every_call_gets_its_own_sequence_and_evidence_record() {
        let (_fake, mut server) = frame_fake(|_request, _prior| json!({"value": {"coins": 2}}));
        let (first, first_evidence) = server.call_with_evidence("bevy_coin_counter", json!({}));
        let (second, second_evidence) = server.call_with_evidence("bevy_coin_counter", json!({}));
        assert_eq!(first.seq, 1);
        assert_eq!(second.seq, 2);
        assert_eq!(
            first_evidence.rel_path(),
            "calls/0001-bevy_coin_counter.json"
        );
        assert_eq!(
            second_evidence.rel_path(),
            "calls/0002-bevy_coin_counter.json"
        );
        assert_eq!(first_evidence.layer, "semantic");
        assert_eq!(
            first_evidence.brp_methods,
            vec!["world.get_resources", "world.get_resources"]
        );
        // Every raw call of one reading is recorded, in order: the game-frame
        // counter that produced `frame`, then the surface itself.  A reading
        // without its raw documents is not E3 evidence.
        assert_eq!(first_evidence.requests.len(), 2);
        assert_eq!(
            first_evidence.requests[0]["params"]["resource"],
            json!(semantic::FRAME_COUNTER_PATH),
            "the counter read comes first and is recorded"
        );
        assert_eq!(
            first_evidence.requests[1]["params"]["resource"],
            json!(semantic::COIN_COUNTER_PATH)
        );
        assert_eq!(
            first_evidence.responses[1]["result"]["value"]["coins"],
            json!(2),
            "the raw reply of the surface call"
        );
        assert_eq!(
            first_evidence.responses[0]["result"]["value"]["frames"],
            json!(fake_frame(1)),
            "the raw reply of the frame call"
        );
        assert_eq!(
            first_evidence.result,
            Some(json!({"coins": 2, "frame": fake_frame(1)}))
        );
        assert!(first_evidence.timestamp_ms > 0);
        assert!(first_evidence.ok());
        let json = first_evidence.to_json();
        assert_eq!(json["seq"], json!(1));
        assert_eq!(json["ok"], json!(true));
    }

    #[test]
    fn the_redaction_hook_is_applied_to_evidence() {
        #[derive(Default)]
        struct Secret(&'static str);
        impl Redactor for Secret {
            fn redact(&self, text: &str) -> String {
                text.replace(self.0, "[redacted]")
            }
        }
        let fake = FakeBrp::spawn(vec![ok_reply(json!({"value": {"won": true}}))]);
        let client = BrpClient::new(fake.endpoint(), Duration::from_millis(1_000));
        // A resource path carrying a secret-looking token is the cheapest way to
        // put a string into the evidence; the refusal message quotes it back.
        let mut server = BevyMcpServer::new(client).with_redactor(Box::new(Secret("SUPERSECRET")));
        let (_call, evidence) =
            server.call_with_evidence("bevy_win_flag", json!({"SUPERSECRET": "x"}));
        assert!(evidence.error.is_some());
        let text = crate::adapter::bevy::contract::canonical_json(&evidence.to_json());
        assert!(!text.contains("SUPERSECRET"), "{text}");
        assert!(text.contains("[redacted]"), "{text}");
    }

    #[test]
    fn the_default_redaction_changes_nothing() {
        let redactor = NoRedaction;
        assert_eq!(redactor.redact("token=abc"), "token=abc");
        let value = json!({"a": ["b", {"c": "d"}]});
        assert_eq!(redact_value(&redactor, &value), value);
    }

    #[test]
    fn the_secret_redactor_scrubs_assignments() {
        let redactor = SecretRedaction;
        let redacted = redactor.redact("OPENAI_API_KEY=abcdef0123456789");
        assert!(!redacted.contains("abcdef0123456789"), "{redacted}");
    }
}
