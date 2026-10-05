//! Cost repair: the bounded-context loop.
//!
//! The measurement the whole batch starts from (`.spec/bevy/COST-REPORT.md`,
//! and `TRUST-REPORT.md` §4 before it): a role call's prompt **is** the
//! accumulated history, re-sent on every model call.  Over the three round-4
//! Developer calls the wire bytes of call *k* are `sum of every message sent
//! before call k`, so the spend grows quadratically in the call count:
//!
//! | recorded round-4 Developer call | model calls | prompt tokens | last prompt |
//! |---|---|---|---|
//! | iter-1 | 69 | 2,544,563 | 46,801 |
//! | iter-2 | 125 | 12,765,478 | 161,566 |
//! | iter-3 | 102 | 5,137,090 | 66,002 |
//!
//! The *content* of that history is dominated by superseded payloads: a tool
//! call whose `arguments` carry the whole of `src/game.rs` (22–32 KB, recorded),
//! and a tool result that dumped a file or an evidence JSON.  Once an action has
//! run, its argument text and its full output have already been consumed — the
//! file is on disk, the fact is in the model's own next action — and re-sending
//! them to the provider on every later call buys nothing.
//!
//! This module is that repair, and it is deliberately *only* that:
//!
//! * the **system prompt** and the **task prompt** are never touched;
//! * the **last `preserve_tail` messages** are never touched, so the model
//!   always sees what it just did without a fold;
//! * everything older is folded to a **digest plus a first line**, and the fold
//!   says what it removed (bytes, and that the full text is not being re-sent);
//! * the fold is applied to the agent's own history, so what is recorded in the
//!   trajectory is exactly what was sent — there is no second, hidden context.
//!
//! The loop is copied from `mini_swe_agent::DefaultAgent::run` (all the pieces
//! it uses are public) rather than patched into the vendored crate: the fold has
//! to happen **between** the steps, where the history lives.

use mini_swe_agent::{AgentError, DefaultAgent, Message, Model, Output};
use serde_json::{json, Value};

use crate::harness::guard::StepCounter;
use crate::runtime::policy::sha256_hex;

/// How much of a folded payload's own text is kept.
const KEPT_HEAD: usize = 200;
/// How much of a folded tool call's command is kept (enough for the loop to see
/// `cargo build --offline`, `HOH_WRITE_FILE src/game.rs`, …).
const KEPT_COMMAND: usize = 160;
/// Arguments shorter than this are not worth folding.
const FOLD_FLOOR: usize = 512;

/// The policy one call runs under.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct CompactPolicy {
    /// Whether the fold runs at all.  `false` is the old behaviour exactly.
    pub enabled: bool,
    /// How many trailing messages are always sent verbatim.
    pub preserve_tail: usize,
}

impl Default for CompactPolicy {
    fn default() -> Self {
        Self {
            enabled: true,
            preserve_tail: crate::config::DEFAULT_COMPACT_HISTORY_TAIL,
        }
    }
}

/// What the fold did to one call's history, as a value the round can record.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct CompactStats {
    /// Messages folded away (payload replaced by its digest).
    pub folded_messages: usize,
    /// Bytes those messages carried before the fold.
    pub bytes_before: usize,
    /// Bytes the same messages carry after it.
    pub bytes_after: usize,
}

impl CompactStats {
    /// Bytes removed by the fold.
    pub fn bytes_removed(&self) -> usize {
        self.bytes_before.saturating_sub(self.bytes_after)
    }

    /// Did anything change?
    pub fn folded_anything(&self) -> bool {
        self.folded_messages > 0
    }

    /// The same stats merged over several folds (one call folds at many steps).
    ///
    /// `bytes_before`/`bytes_after` are summed over folds, so the ratio is the
    /// ratio of everything the fold ever replaced, not of a single snapshot.
    pub fn merged(self, other: Self) -> Self {
        Self {
            folded_messages: self.folded_messages + other.folded_messages,
            bytes_before: self.bytes_before + other.bytes_before,
            bytes_after: self.bytes_after + other.bytes_after,
        }
    }
}

/// The wire size of one message: what the provider is charged for it.
///
/// It is the same subset `mini_swe_agent`'s `to_llm_message` sends (role,
/// content, tool calls, tool-call id) — the trajectory's local-only `extra`
/// blocks are deliberately excluded, because the measured `0.2563` tokens per
/// byte is a fit over exactly this subset and the `extra` blocks never leave the
/// process.
pub fn message_wire_bytes(message: &Message) -> usize {
    let value = json!({
        "role": message.role,
        "content": message.content,
        "tool_calls": message.fields.get("tool_calls"),
        "tool_call_id": message.fields.get("tool_call_id").or_else(|| message.fields.get("tool_call_ids")),
    });
    serde_json::to_string(&value)
        .map(|text| text.len())
        .unwrap_or(0)
}

/// The `<output>…</output>` body of a tool observation, when it has one.
fn output_body(content: &str) -> &str {
    match (content.find("<output>"), content.rfind("</output>")) {
        (Some(start), Some(end)) if end > start => &content[start + "<output>".len()..end],
        _ => content,
    }
}

/// The first non-empty line of a payload, bounded and quoted.
fn head_line(text: &str) -> String {
    let line = text
        .lines()
        .map(str::trim)
        .find(|line| !line.is_empty())
        .unwrap_or("");
    let mut head: String = line.chars().take(KEPT_HEAD).collect();
    if line.chars().count() > KEPT_HEAD {
        head.push('…');
    }
    head
}

/// The `command` inside a tool call's JSON `arguments`, when it has one.
fn command_of(arguments: &str) -> Option<String> {
    let parsed: Value = serde_json::from_str(arguments).ok()?;
    parsed
        .get("command")
        .or_else(|| parsed.get("cmd"))
        .and_then(Value::as_str)
        .map(str::to_string)
}

/// A digest prefix plus a byte count: what "this payload was here" reduces to.
fn digest_note(bytes: &str) -> String {
    format!(
        "{} ({} byte(s))",
        &sha256_hex(bytes.as_bytes())[..12],
        bytes.len()
    )
}

/// Fold one superseded message, or leave it alone.
///
/// * an `assistant` tool call keeps its `tool_calls` shape and its call ids and
///   replaces only the argument text, because the provider validates the
///   call/result pairing;
/// * a `tool` observation keeps its `<returncode>` and replaces the payload;
/// * anything else is returned unchanged.
fn fold_message(message: &mut Message) -> bool {
    if message.role == "tool" {
        let Some(original) = message.content.as_str().map(str::to_string) else {
            return false;
        };
        if original.len() < FOLD_FLOOR {
            return false;
        }
        let body = output_body(&original).to_string();
        let returncode = original
            .split_once("<returncode>")
            .and_then(|(_, rest)| rest.split_once("</returncode>"))
            .map(|(code, _)| code.trim().to_string())
            .unwrap_or_else(|| "unknown".to_string());
        let folded = format!(
            "<returncode>{returncode}</returncode>\n<output>\n\
             [hoh: superseded observation folded — this payload was already consumed when the step \
             ran, so it is not re-sent; sha256/bytes {}. first line: {}]\n</output>\n",
            digest_note(&body),
            head_line(&body),
        );
        if folded.len() >= original.len() {
            return false;
        }
        message.content = Value::String(folded);
        return true;
    }
    let Some(calls) = message
        .fields
        .get_mut("tool_calls")
        .and_then(Value::as_array_mut)
    else {
        return false;
    };
    let mut changed = false;
    for call in calls.iter_mut() {
        // The command is read before the `function` object is borrowed mutably:
        // the two live in the same call object.
        let command = call
            .get("command")
            .and_then(Value::as_str)
            .map(str::to_string);
        let Some(function) = call.get_mut("function").and_then(Value::as_object_mut) else {
            continue;
        };
        let Some(arguments) = function.get("arguments").and_then(Value::as_str) else {
            continue;
        };
        if arguments.len() < FOLD_FLOOR {
            continue;
        }
        let command = command_of(arguments).or(command).unwrap_or_default();
        let mut head: String = command.chars().take(KEPT_COMMAND).collect();
        if command.chars().count() > KEPT_COMMAND {
            head.push('…');
        }
        let folded = json!({
            "command": head,
            "[hoh]": format!(
                "superseded tool call folded: {} of arguments were sent and acted on when this \
                 step ran; the full text is not re-sent",
                digest_note(arguments)
            ),
        })
        .to_string();
        if folded.len() >= arguments.len() {
            continue;
        }
        function.insert("arguments".to_string(), Value::String(folded));
        changed = true;
    }
    changed
}

/// Fold every superseded message in `messages` under `policy`.
///
/// The first two messages (the system prompt and the task) and the last
/// `policy.preserve_tail` are never touched.
pub fn compact_history(messages: &mut [Message], policy: CompactPolicy) -> CompactStats {
    let mut stats = CompactStats::default();
    if !policy.enabled || messages.len() <= 2 + policy.preserve_tail {
        return stats;
    }
    let end = messages.len() - policy.preserve_tail;
    for message in messages.iter_mut().take(end).skip(2) {
        let before = message_wire_bytes(message);
        if !fold_message(message) {
            continue;
        }
        let after = message_wire_bytes(message);
        stats.folded_messages += 1;
        stats.bytes_before += before;
        stats.bytes_after += after;
    }
    stats
}

/// The steps one call took, readable from outside the loop.
#[derive(Clone, Debug, Default)]
pub struct CallProgress {
    pub steps: StepCounter,
    /// The fold's cumulative effect over the call.
    pub compacted: std::sync::Arc<std::sync::Mutex<CompactStats>>,
}

/// A model that counts the steps one call takes, so the guard and the prompt
/// keep agreeing on what a step is.
///
/// Round-5 repair (AC-8): it does **not** fold.  The fold runs in
/// [`run_compacting_agent`] on the agent's own `messages`, before each step, so
/// what the provider is sent and what `save()` records are the same history.
/// The version this replaces folded a local `messages.to_vec()` and passed that
/// to the provider, while `DefaultAgent::query` pushed the *unfolded* response
/// into the stored history — so the trajectory did not record what was sent,
/// which is the opposite of what this module, `DECISIONS.md` and the cost report
/// all claim.
struct CountingModel {
    inner: Box<dyn Model>,
    progress: CallProgress,
}

#[async_trait::async_trait]
impl Model for CountingModel {
    fn model_name(&self) -> &str {
        self.inner.model_name()
    }

    async fn query(
        &self,
        messages: &[Message],
        kwargs: Option<Value>,
    ) -> mini_swe_agent::Result<Message> {
        self.progress.steps.increment();
        self.inner.query(messages, kwargs).await
    }

    fn format_message(&self, message: Message) -> mini_swe_agent::Result<Message> {
        self.inner.format_message(message)
    }

    fn format_observation_messages(
        &self,
        message: &Message,
        outputs: &[Output],
        template_vars: &Value,
    ) -> mini_swe_agent::Result<Vec<Message>> {
        self.inner
            .format_observation_messages(message, outputs, template_vars)
    }

    fn get_template_vars(&self) -> Value {
        self.inner.get_template_vars()
    }

    fn serialize(&self) -> Value {
        self.inner.serialize()
    }
}

/// A model that is never called: it only holds the slot while the real one is
/// taken out to be wrapped.
struct UnusedModel;

#[async_trait::async_trait]
impl Model for UnusedModel {
    fn model_name(&self) -> &str {
        "unused"
    }

    async fn query(
        &self,
        _messages: &[Message],
        _kwargs: Option<Value>,
    ) -> mini_swe_agent::Result<Message> {
        Err(AgentError::other(anyhow::anyhow!(
            "the compacting loop asked the placeholder model for a response"
        )))
    }

    fn format_observation_messages(
        &self,
        _message: &Message,
        _outputs: &[Output],
        _template_vars: &Value,
    ) -> mini_swe_agent::Result<Vec<Message>> {
        Err(AgentError::other(anyhow::anyhow!(
            "the compacting loop asked the placeholder model to format an observation"
        )))
    }

    fn get_template_vars(&self) -> Value {
        Value::Null
    }

    fn serialize(&self) -> Value {
        Value::Null
    }
}

/// What one `run_compacting_agent` produced.
pub struct LoopOutcome {
    /// `Some(status)` when the harness's own fail-fast abort ended the call.
    pub fail_fast: Option<String>,
    /// What the last message's own `exit_status` says.
    pub exit_status: String,
    pub submission: String,
    pub steps: u64,
    pub compacted: CompactStats,
}

/// Run one role call under the compacting loop.
///
/// The control flow mirrors `mini_swe_agent::DefaultAgent::run`: fold the
/// agent's **own** history before each step (AC-8), save the trajectory after
/// every step (so a crash still leaves a usable record), stop on an `exit`
/// message, and turn the harness's own fail-fast abort into a value rather than
/// an error.
///
/// The fold is applied to `agent.messages` itself — the `Vec` that
/// `DefaultAgent::query` hands to the model and that `save()` serialises — so
/// there is no second, hidden context: the trajectory records exactly what was
/// sent.  Folding a local copy instead (the previous shape) left the stored
/// history unfolded and an auditor unable to recompute what the provider was
/// charged for.
pub async fn run_compacting_agent(
    mut agent: DefaultAgent,
    progress: CallProgress,
    policy: CompactPolicy,
    task: &str,
    kwargs: Option<Value>,
) -> Result<LoopOutcome, AgentError> {
    agent
        .extra_template_vars
        .insert("task".to_string(), Value::String(task.to_string()));
    if let Some(Value::Object(kwargs)) = kwargs {
        for (key, value) in kwargs {
            agent.extra_template_vars.insert(key, value);
        }
    }
    agent.messages.clear();
    let system = agent.model.format_message(Message::system(
        agent.render_template(&agent.config.system_template, None)?,
    ))?;
    let instance = agent.model.format_message(Message::user(
        agent.render_template(&agent.config.instance_template, None)?,
    ))?;
    agent.add_messages(vec![system, instance]);
    let model = std::mem::replace(&mut agent.model, Box::new(UnusedModel));
    let model = CountingModel {
        inner: model,
        progress: progress.clone(),
    };
    agent.model = Box::new(model);

    let mut fail_fast = None;
    loop {
        // AC-8: fold the history this call will send, in the place the call keeps
        // it, before the step reads it.  `compact_history` never touches the
        // system prompt, the task or the last `preserve_tail` messages, and it
        // declines any fold that would not be smaller, so a step it has already
        // folded is left alone.
        let stats = compact_history(&mut agent.messages, policy);
        if stats.folded_anything() {
            if let Ok(mut total) = progress.compacted.lock() {
                *total = total.merged(stats);
            }
        }
        match agent.step().await {
            Ok(_) => {
                agent.n_consecutive_format_errors = 0;
            }
            Err(AgentError::Format(error)) => {
                let billed = error
                    .messages
                    .first()
                    .and_then(|message| message.extra_value("cost"))
                    .and_then(Value::as_f64)
                    .unwrap_or(0.0);
                agent.cost += billed;
                agent.n_consecutive_format_errors += 1;
                if agent.config.max_consecutive_format_errors > 0
                    && agent.n_consecutive_format_errors
                        >= agent.config.max_consecutive_format_errors
                {
                    let mut messages = error.messages;
                    messages.push(Message::exit_message(
                        "RepeatedFormatError",
                        "RepeatedFormatError",
                        "",
                    ));
                    agent.add_messages(messages);
                } else {
                    agent.add_messages(error.messages);
                }
            }
            Err(AgentError::Interrupt(interrupt)) => {
                agent.add_messages(interrupt.messages);
            }
            Err(AgentError::Other(error)) => {
                agent.handle_uncaught_exception(&error);
                if let Some(path) = agent.config.output_path.clone() {
                    let _ = agent.save(Some(path.as_path()), &[]);
                }
                match crate::harness::guard::fail_fast_status(&error.to_string()) {
                    Some(status) => {
                        // The harness's own judgement: record it and end the
                        // call, exactly as `MiniHarness` does.
                        fail_fast = Some(status.to_string());
                        break;
                    }
                    None => return Err(AgentError::Other(error)),
                }
            }
        }

        if let Some(path) = agent.config.output_path.clone() {
            let _ = agent.save(Some(path.as_path()), &[]);
        }

        if agent
            .messages
            .last()
            .map(|message| message.role == "exit")
            .unwrap_or(false)
        {
            break;
        }
    }

    let last = agent.messages.last();
    let exit_status = match &fail_fast {
        Some(status) => status.clone(),
        None => last
            .map(|message| message.exit_status().to_string())
            .unwrap_or_default(),
    };
    Ok(LoopOutcome {
        fail_fast,
        exit_status,
        submission: last
            .map(|message| message.submission().to_string())
            .unwrap_or_default(),
        steps: progress.steps.value(),
        compacted: progress
            .compacted
            .lock()
            .map(|stats| *stats)
            .unwrap_or_default(),
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn tool_message(body: &str) -> Message {
        let mut message = Message::new(
            "tool",
            format!("<returncode>0</returncode>\n<output>\n{body}\n</output>\n"),
        );
        message.set_extra("tool_call_id", json!("call-1"));
        message
    }

    fn assistant_write(path: &str, content: &str) -> Message {
        let command = crate::harness::directive::render_write(path, content);
        let mut message = Message::new("assistant", "");
        message.fields.insert(
            "tool_calls".to_string(),
            json!([{
                "id": "call-1",
                "type": "function",
                "function": {
                    "name": "bash",
                    "arguments": json!({"command": command}).to_string(),
                }
            }]),
        );
        message
    }

    fn history() -> Vec<Message> {
        let mut messages = vec![
            Message::system("# Role: Developer\n\n[shell]\n".repeat(4)),
            Message::user("Iteration 2: implement this iteration's plan."),
        ];
        // A superseded tool call carrying a whole source file, and its result.
        messages.push(assistant_write(
            "src/game.rs",
            &"fn main() {}\n".repeat(900),
        ));
        messages.push(tool_message(&"compiling hof_game\n".repeat(400)));
        // A read whose answer has been consumed.
        messages.push(assistant_write("HOH_READ_FILE .hoh/plan.md", ""));
        messages.push(tool_message(&"plan line\n".repeat(200)));
        for step in 0..8 {
            messages.push(Message::assistant(format!("step {step}")));
            messages.push(tool_message(&format!("answer {step}")));
        }
        messages
    }

    /// The system prompt and the task prompt are never fold candidates: they are
    /// not superseded, they are the call's own definition.
    #[test]
    fn the_system_prompt_and_the_task_are_never_folded() {
        let mut messages = history();
        let before = (messages[0].clone(), messages[1].clone());
        let stats = compact_history(
            &mut messages,
            CompactPolicy {
                enabled: true,
                preserve_tail: 2,
            },
        );
        assert!(stats.folded_messages > 0, "{stats:?}");
        assert_eq!(messages[0].role, before.0.role);
        assert_eq!(
            message_wire_bytes(&messages[0]),
            message_wire_bytes(&before.0),
            "the system prompt is never touched"
        );
        assert_eq!(
            message_wire_bytes(&messages[1]),
            message_wire_bytes(&before.1),
            "the task prompt is never touched"
        );
    }

    /// The tail is always verbatim: the model must see what it just did.
    #[test]
    fn the_preserved_tail_is_sent_verbatim() {
        let mut messages = history();
        let tail = 6usize;
        let before: Vec<usize> = messages
            .iter()
            .rev()
            .take(tail)
            .map(message_wire_bytes)
            .collect();
        compact_history(
            &mut messages,
            CompactPolicy {
                enabled: true,
                preserve_tail: tail,
            },
        );
        let after: Vec<usize> = messages
            .iter()
            .rev()
            .take(tail)
            .map(message_wire_bytes)
            .collect();
        assert_eq!(before, after, "the tail is byte-identical after the fold");
    }

    /// The fold removes most of what a superseded history carries, and what it
    /// keeps says what it removed.
    #[test]
    fn folding_a_superseded_history_removes_most_of_its_bytes() {
        let mut messages = history();
        let before: usize = messages.iter().map(message_wire_bytes).sum();
        let stats = compact_history(&mut messages, CompactPolicy::default());
        let after: usize = messages.iter().map(message_wire_bytes).sum();
        assert!(
            after * 4 < before,
            "the recorded history is dominated by superseded payloads: {before} -> {after}"
        );
        assert_eq!(stats.bytes_before - stats.bytes_after, before - after);
        let folded = messages[3].content.as_str().unwrap();
        assert!(folded.contains("superseded observation folded"), "{folded}");
        assert!(
            folded.contains("byte(s)"),
            "the fold states what it removed: {folded}"
        );
        let call = &messages[2].fields["tool_calls"][0]["function"]["arguments"];
        let folded_call = call.as_str().unwrap();
        assert!(
            folded_call.contains("superseded tool call folded"),
            "{folded_call}"
        );
        assert!(
            folded_call.contains("HOH_WRITE_FILE src/game.rs"),
            "the command itself stays, so the model can still see what it did: {folded_call}"
        );
        assert_eq!(
            messages[2].fields["tool_calls"][0]["id"],
            json!("call-1"),
            "the call id survives, so the call/result pairing is still valid"
        );
    }

    /// The control: `enabled: false` is the old behaviour exactly.
    #[test]
    fn a_disabled_fold_changes_nothing() {
        let mut messages = history();
        let before: Vec<usize> = messages.iter().map(message_wire_bytes).collect();
        let stats = compact_history(
            &mut messages,
            CompactPolicy {
                enabled: false,
                preserve_tail: 0,
            },
        );
        assert_eq!(stats, CompactStats::default());
        let after: Vec<usize> = messages.iter().map(message_wire_bytes).collect();
        assert_eq!(before, after);
    }

    /// Small payloads are left alone: a fold that replaced a short observation
    /// with a longer note would grow the prompt, which is the opposite of the job.
    #[test]
    fn a_small_payload_is_never_grown() {
        let mut messages = vec![
            Message::system("s"),
            Message::user("u"),
            Message::assistant("a"),
            tool_message("ok"),
            Message::assistant("b"),
            tool_message("again"),
        ];
        let before: Vec<usize> = messages.iter().map(message_wire_bytes).collect();
        compact_history(&mut messages, CompactPolicy::default());
        let after: Vec<usize> = messages.iter().map(message_wire_bytes).collect();
        assert_eq!(before, after);
    }

    // ------------------------------------------------------------------
    // AC-8: the fold lands on the history the agent stores.
    //
    // The claim at the top of this module — "the fold is applied to the agent's
    // own history, so what is recorded in the trajectory is exactly what was
    // sent; there is no second, hidden context" — is pinned here by running the
    // real loop with a stub model and a stub environment: no model, no network,
    // no engine.  The stub model records every message list it is handed, and the
    // loop's own `save()` writes the stored history to a real file, so the two can
    // be compared byte for byte.
    // ------------------------------------------------------------------

    /// A body that is definitely over `FOLD_FLOOR`, with the marker on a line the
    /// fold does **not** keep (only the first line survives), so "the raw payload
    /// is gone" is checkable.
    const RAW_MARKER: &str = "SECRET-UNFOLDED-PAYLOAD";

    fn raw_observation() -> String {
        format!("compiling hof_game\n{}\n", RAW_MARKER.repeat(80))
    }

    /// Hands the loop a scripted action and a big observation, and records every
    /// message list the provider would have been sent.
    struct RecordingModel {
        received: std::sync::Arc<std::sync::Mutex<Vec<Vec<Message>>>>,
        calls: std::sync::atomic::AtomicUsize,
    }

    #[async_trait::async_trait]
    impl Model for RecordingModel {
        fn model_name(&self) -> &str {
            "recording-stub"
        }

        async fn query(
            &self,
            messages: &[Message],
            _kwargs: Option<Value>,
        ) -> mini_swe_agent::Result<Message> {
            self.received
                .lock()
                .expect("received lock")
                .push(messages.to_vec());
            let call = self.calls.fetch_add(1, std::sync::atomic::Ordering::SeqCst) + 1;
            if call >= 4 {
                return Ok(Message::exit_message("Submitted", "done", "done"));
            }
            let mut message = Message::assistant(format!("step {call}"));
            message.set_extra("actions", json!([{"command": format!("echo {call}")}]));
            Ok(message)
        }

        fn format_observation_messages(
            &self,
            _message: &Message,
            outputs: &[Output],
            _template_vars: &Value,
        ) -> mini_swe_agent::Result<Vec<Message>> {
            // No action ran (an `exit` message), so there is no observation: a
            // stub that answered here would append a tool message *after* the
            // exit and the loop would never see it end.
            if outputs.is_empty() {
                return Ok(Vec::new());
            }
            Ok(vec![tool_message(&raw_observation())])
        }

        fn get_template_vars(&self) -> Value {
            json!({})
        }

        fn serialize(&self) -> Value {
            // An empty object, not `null`: `DefaultAgent::serialize` merges the
            // model's and the environment's values over its own object, and
            // `json_merge` returns the *patch* when it is not an object — a stub
            // that answered `null` would make the whole trajectory `null`.
            json!({})
        }
    }

    /// A shell that answers nothing with nothing: the loop never runs a command.
    struct StubEnvironment;

    #[async_trait::async_trait]
    impl mini_swe_agent::Environment for StubEnvironment {
        async fn execute(
            &self,
            _action: &mini_swe_agent::Action,
            _cwd: Option<&str>,
            _timeout: Option<u64>,
        ) -> mini_swe_agent::Result<Output> {
            Ok(Output::success("", 0))
        }

        fn get_template_vars(&self) -> Value {
            json!({})
        }

        fn serialize(&self) -> Value {
            json!({})
        }
    }

    fn agent_with(model: RecordingModel, trajectory: &std::path::Path) -> DefaultAgent {
        let config = mini_swe_agent::AgentConfig {
            system_template: "stub system prompt".to_string(),
            instance_template: "stub task".to_string(),
            step_limit: 0,
            cost_limit: 0.0,
            wall_time_limit_seconds: 0,
            max_consecutive_format_errors: 0,
            output_path: Some(trajectory.to_path_buf()),
            mode: mini_swe_agent::AgentMode::Yolo,
            whitelist_actions: Vec::new(),
            confirm_exit: false,
        };
        DefaultAgent::new(Box::new(model), Box::new(StubEnvironment), config)
    }

    /// The regression AC-8 names: the trajectory the loop saves **is** the history
    /// the last provider call was handed, and the raw superseded payload is not in
    /// it.  Folding a local copy (the pre-repair shape) fails both halves: the file
    /// keeps the raw bytes and the last call's list no longer matches the stored
    /// one.
    #[tokio::test]
    async fn the_stored_trajectory_is_the_history_that_was_sent() {
        let temp = tempfile::tempdir().expect("tempdir");
        let trajectory = temp.path().join("traj/developer.attempt1.json");
        let received = std::sync::Arc::new(std::sync::Mutex::new(Vec::new()));
        let model = RecordingModel {
            received: received.clone(),
            calls: std::sync::atomic::AtomicUsize::new(0),
        };
        let agent = agent_with(model, &trajectory);
        let outcome = run_compacting_agent(
            agent,
            CallProgress::default(),
            CompactPolicy {
                enabled: true,
                preserve_tail: 1,
            },
            "stub task",
            None,
        )
        .await
        .expect("the loop runs");
        assert_eq!(outcome.exit_status, "Submitted");
        assert!(
            outcome.compacted.folded_messages >= 2,
            "the loop must have folded the superseded observations: {:?}",
            outcome.compacted
        );

        let saved = std::fs::read_to_string(&trajectory).expect("the loop saves after every step");
        let stored: Value = serde_json::from_str(&saved).expect("trajectory json");
        let stored: Vec<Message> = serde_json::from_value(stored["messages"].clone())
            .expect("trajectory messages deserialize as the messages that were sent");

        // Four provider calls: three produced an observation, and the last of
        // those three is inside `preserve_tail = 1`, so exactly one observation
        // is legitimately still verbatim.  The other two are superseded and must
        // have been folded in the **stored** history, not merely in a copy.
        let verbatim: Vec<usize> = stored
            .iter()
            .enumerate()
            .filter(|(_, message)| {
                message
                    .content
                    .as_str()
                    .is_some_and(|text| text.contains(RAW_MARKER))
            })
            .map(|(index, _)| index)
            .collect();
        assert_eq!(
            verbatim.len(),
            1,
            "exactly the preserved tail observation may still be verbatim; the stored trajectory \
             kept {verbatim:?} raw (AC-8: the fold did not land on the agent's own history)"
        );
        let folded: usize = stored
            .iter()
            .filter(|message| {
                message
                    .content
                    .as_str()
                    .is_some_and(|text| text.contains("superseded observation folded"))
            })
            .count();
        assert_eq!(
            folded, 2,
            "the two superseded observations must carry the fold's own note in the stored history"
        );

        // The claim being checked, exactly: the last provider call's list and the
        // prefix of the stored history are the same history.
        let sent = received.lock().expect("received lock");
        let last = sent.last().expect("at least one provider call");
        assert!(stored.len() > last.len(), "the exit message is appended");
        for (index, message) in last.iter().enumerate() {
            assert_eq!(
                message_wire_bytes(&stored[index]),
                message_wire_bytes(message),
                "message {index}: the trajectory must record exactly what was sent"
            );
        }
    }
}
