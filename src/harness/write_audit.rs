//! Durable **write accounting** over recorded Developer trajectories.
//!
//! ## Why this exists
//!
//! The round-6 batch measured one live Developer call and reported *which calls
//! changed a project file*.  Its detector counted only `HOH_WRITE_FILE`
//! directives, so every project file changed by a **shell command** was
//! invisible — and the resulting number ("the last change was call 44; calls
//! 45–150 changed nothing") was false for the very call it described.  The next
//! acceptance refuted it (`.spec/bevy/ACCEPTANCE-LIVE-COST.md`, defect A-3) with
//! a script kept outside the repository, so the account could not be re-run from
//! the tree.  This module is the replacement.
//!
//! ## What it answers
//!
//! For each recorded model call: **did this call write a file inside the
//! project?**  It decides from the recording alone — no model call, no shell, no
//! engine — from three signals:
//!
//! * the `HOH_WRITE_FILE` directives, classified by the *real* parser
//!   ([`crate::harness::directive::parse_directive`]), so a directive the harness
//!   refused is never counted as a write (round-4 iteration 3's call 72 is
//!   exactly that case);
//! * the shell commands, decided from the **recorded command text** — the verb
//!   and the destination operand it gives — with literal variable assignments
//!   (`$p='src\game.rs'`, `p = 'src/game.rs'`) resolved;
//! * the scripts a command runs, when the recording contains the script's own
//!   text: the write is attributed to the call that *ran* the script.  This is
//!   how both recorded rounds edited `src/game.rs` for most of their calls.
//!
//! The scope rule is the guard's own: a path under `.hoh/`, `.git/` or
//! `target/` is not project progress ([`crate::harness::guard::ArtifactKind`]).
//!
//! ## What it refuses to decide
//!
//! A command can name a write whose destination the recording never binds (a
//! variable assigned from another variable, a path built at run time): that is
//! reported through [`NamedWrite::target`] as `None`, never guessed.  A guarded
//! script can run and change nothing (a `-replace` pattern that does not match,
//! an `assert` that throws): the recording's own `<returncode>` decides that, and
//! [`Outcome::Failed`] says so.  Byte-level identity of the written content is
//! never claimed — see [`Outcome::Ok`].
//!
//! Two limits are worth stating because they bound the numbers the module
//! produces.  It classifies from the **recorded command text**, so a verb it does
//! not know (a hand-rolled writer, `Set-ItemProperty`, a `git` command that
//! rewrites a tracked file) is not seen at all; and it cannot attribute a write
//! whose destination is computed at run time.  Both are reported as *undecided*
//! only when a known verb has an unbound destination — an unknown verb is
//! silent, which is the conservative direction for a *safety* question (it can
//! only under-report work that a budget would cut) and the unsafe direction for a
//! *cost* question.  The trajectories carry no such case; the acceptance's own
//! detector has the same blind spot.
//!
//! ## The withdrawn step budget
//!
//! [`replay_directive_step_budget`] replays the rule of the **withdrawn**
//! round-6 step budget, whose whole safety case was that it "lost no write".  It
//! exists so that case can be re-run against the corrected accounting
//! ([`Audit::project_writes_after`]), and it is **measurement only**: no
//! configuration key, no guard field and no production call site implements it,
//! because its own replay showed it cuts recorded work.  Nothing here changes
//! what the harness runs.

use std::collections::BTreeMap;

use serde_json::Value;

use crate::harness::directive::{parse_directive, Directive};
use crate::harness::guard::ArtifactKind;

/// Where a written path sits relative to the guard's hash-excluded set.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Scope {
    /// Inside the project: a project write.
    Project,
    /// Under `.hoh/`, `.git/` or `target/`: scratch or cache, not progress.
    Excluded,
}

/// Is this path a project path, by the guard's own rule?
///
/// It delegates to [`ArtifactKind::ProjectFile`] so the accounting and the guard
/// cannot drift apart: a test that decides for itself which paths are progress
/// can prove anything.
pub fn scope_of(path: &str) -> Scope {
    let trimmed = path
        .trim()
        .trim_matches(|c| c == '\'' || c == '"' || c == '`');
    if ArtifactKind::ProjectFile.counts(trimmed) {
        Scope::Project
    } else {
        Scope::Excluded
    }
}

/// What produced a project write.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum WriteSource {
    /// A `HOH_WRITE_FILE` directive.  The harness performs this write itself.
    Directive,
    /// A shell command whose own text names the destination.
    Shell,
    /// A shell command that ran a recorded script which writes the destination.
    Script { script: String },
}

/// What the recording says happened to the write.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Outcome {
    /// The recorded result was success.  For a directive that means the harness
    /// wrote the file; for a shell command that means the command **ran and
    /// reported success**.  Whether the written bytes differ from the bytes
    /// already there is not decided here and is not claimed.
    Ok,
    /// The recorded result carries this non-zero return code: the command
    /// failed, so it did not write.  A PowerShell parse error and a script's own
    /// `throw` both land here.
    Failed(i32),
    /// The recording does not carry a result for this action.
    NotRecorded,
}

/// One write of a file inside the project.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ProjectWrite {
    pub call: usize,
    pub path: String,
    pub source: WriteSource,
    pub outcome: Outcome,
}

/// Everything one model call's recorded actions wrote.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct CallWrites {
    /// 1-based model-call index, in recording order — the step unit the guard and
    /// `agent.step_limit` use.
    pub call: usize,
    /// Provider-reported `usage.total_tokens` for this call.
    pub total_tokens: u64,
    /// Running total through this call, so a budget replay can price an abort.
    pub cumulative_tokens: u64,
    /// Every successful write directive's path, project or not.  This is the
    /// timeline the *shipped guard* can see; the corpus contains project edits
    /// that never appear in it.
    pub directive_writes: Vec<String>,
    /// Writes of files inside the project that the recording says landed.
    pub project_writes: Vec<ProjectWrite>,
    /// Project writes the recording says **failed** — the attempt is real, the
    /// change is not.
    pub project_writes_failed: Vec<ProjectWrite>,
    /// Actions whose effect the recording does not settle: a directive the
    /// harness refused as malformed, or a write whose destination operand is not
    /// resolvable.  Reported, never counted.
    pub undecided: Vec<String>,
}

impl CallWrites {
    /// Did this call write a project file that the recording says landed?
    pub fn changed_project_file(&self) -> bool {
        !self.project_writes.is_empty()
    }
}

/// The whole accounting of one recorded role call.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Audit {
    pub calls: Vec<CallWrites>,
    /// Sum of the calls' recorded totals.
    pub total_tokens: u64,
}

impl Audit {
    pub fn recorded_calls(&self) -> usize {
        self.calls.len()
    }

    /// Every call whose recorded actions wrote the project.
    pub fn project_write_calls(&self) -> Vec<usize> {
        self.calls
            .iter()
            .filter(|call| call.changed_project_file())
            .map(|call| call.call)
            .collect()
    }

    /// Every call carrying a successful write directive, of any path.
    pub fn directive_write_calls(&self) -> Vec<usize> {
        self.calls
            .iter()
            .filter(|call| !call.directive_writes.is_empty())
            .map(|call| call.call)
            .collect()
    }

    /// Every failed project-write attempt: `(call, path, return code)`.
    pub fn failed_project_writes(&self) -> Vec<(usize, String, i32)> {
        self.calls
            .iter()
            .flat_map(|call| {
                call.project_writes_failed
                    .iter()
                    .filter_map(|write| match write.outcome {
                        Outcome::Failed(code) => Some((call.call, write.path.clone(), code)),
                        _ => None,
                    })
            })
            .collect()
    }

    /// Every action the recording does not settle: `(call, reason)`.
    pub fn undecided(&self) -> Vec<(usize, String)> {
        self.calls
            .iter()
            .flat_map(|call| {
                call.undecided
                    .iter()
                    .map(|reason| (call.call, reason.clone()))
            })
            .collect()
    }

    pub fn last_project_write(&self) -> Option<usize> {
        self.project_write_calls().into_iter().next_back()
    }

    /// The longest run of calls without a project write, as
    /// `(before, after, calls_between)`.  `before` is `0` for the opening run and
    /// `after` is `recorded_calls + 1` for the closing one, so the two ends are
    /// reported rather than dropped.
    pub fn longest_project_write_free_window(&self) -> Option<(usize, usize, usize)> {
        let mut bounds = vec![0usize];
        bounds.extend(self.project_write_calls());
        bounds.push(self.recorded_calls() + 1);
        bounds
            .windows(2)
            .map(|pair| (pair[0], pair[1], pair[1] - pair[0] - 1))
            .max_by_key(|window| window.2)
    }

    /// Project writes that would be cut if the call ended at `call`.
    pub fn project_writes_after(&self, call: usize) -> Vec<&ProjectWrite> {
        self.calls
            .iter()
            .filter(|entry| entry.call > call)
            .flat_map(|entry| entry.project_writes.iter())
            .collect()
    }

    /// Every distinct project path any call wrote.
    pub fn paths_written(&self) -> Vec<String> {
        let mut paths: Vec<String> = self
            .calls
            .iter()
            .flat_map(|call| call.project_writes.iter().map(|write| write.path.clone()))
            .collect();
        paths.sort();
        paths.dedup();
        paths
    }
}

/// One destination a recorded command names, with the verb that names it.
///
/// `target` is `None` when the command names a write but the recording does not
/// bind its destination; the caller must report that, not guess it.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct NamedWrite {
    pub verb: String,
    pub target: Option<String>,
    /// The recorded script whose text names the write, when the command only ran
    /// that script.
    pub script: Option<String>,
}

impl NamedWrite {
    fn direct(verb: &str, target: Option<String>) -> Self {
        Self {
            verb: verb.to_string(),
            target,
            script: None,
        }
    }
}

/// The command's own text, with literal `$name = 'value'` assignments resolved.
///
/// Only a literal assignment is resolved.  A value built from another variable
/// or from an expression stays unresolved on purpose: guessing it is how a
/// measurement stops being a measurement.
pub fn shell_substitute(text: &str) -> String {
    substitute(text, &literal_bindings(text, true))
}

/// The command's own text, with literal `name = 'value'` assignments resolved.
///
/// This is the Python shape (`p = 'src/game.rs'`).  Bare identifiers are only
/// replaced as whole words, so an assignment cannot rewrite a larger name.
pub fn python_substitute(text: &str) -> String {
    substitute(text, &literal_bindings(text, false))
}

/// Every write the command's text names, shell or Python.
pub fn named_writes(command: &str) -> Vec<NamedWrite> {
    let mut out = shell_named_writes(command);
    out.extend(python_named_writes(command));
    out
}

/// The recorded script a command runs, if it names one, normalised.
pub fn script_run(command: &str) -> Option<String> {
    for segment in split_segments(&shell_substitute(command)) {
        let tokens = tokenize(&segment);
        for (index, token) in tokens.iter().enumerate() {
            let lowered = token.to_ascii_lowercase();
            if index == 0 || !(lowered.ends_with(".ps1") || lowered.ends_with(".py")) {
                continue;
            }
            let previous = tokens[index - 1].to_ascii_lowercase();
            let previous = previous.rsplit(['/', '\\']).next().unwrap_or("");
            if matches!(
                previous,
                "python" | "python3" | "py" | "-file" | "powershell" | "pwsh"
            ) {
                return Some(normalise_script(token));
            }
        }
    }
    None
}

/// Measurement only: replay the **withdrawn** round-6 step budget's rule.
///
/// The rule, read from the withdrawn implementation's own code: one model call is
/// one step; once the call has written its declared artifact, an action that is
/// not a write directive is refused when `call - last_write > k`; a successful
/// write directive restarts the run and a write action is never refused.
/// `k == 0` is the shipping behaviour (off).
///
/// It is here so the withdrawn lever's own safety claim — "it loses no write" —
/// can be re-run against the corrected accounting instead of against a loop that
/// stops at the abort.  **It implements nothing the harness runs.**
pub fn replay_directive_step_budget(audit: &Audit, k: u64) -> BudgetReplay {
    let mut last_write = 0u64;
    let mut artifact_written = false;
    let mut aborted_at = None;
    let mut tokens_at_abort = 0;
    for call in &audit.calls {
        let step = call.call as u64;
        for path in &call.directive_writes {
            last_write = step;
            if scope_of(path) == Scope::Project {
                artifact_written = true;
            }
        }
        if k != 0 && artifact_written && aborted_at.is_none() && step - last_write > k {
            aborted_at = Some(call.call);
            tokens_at_abort = call.cumulative_tokens;
        }
    }
    // The timelines come from the whole recording, never from the loop: a loop
    // that stops at the abort can only ever report an empty "after".
    let (directive_after, project_after) = match aborted_at {
        Some(call) => (
            audit
                .directive_write_calls()
                .into_iter()
                .filter(|index| *index > call)
                .collect(),
            audit
                .project_writes_after(call)
                .into_iter()
                .map(|write| write.call)
                .collect(),
        ),
        None => (Vec::new(), Vec::new()),
    };
    BudgetReplay {
        budget: k,
        aborted_at_call: aborted_at,
        cumulative_tokens_at_abort: tokens_at_abort,
        directive_writes_after_the_end: directive_after,
        project_writes_after_the_end: project_after,
    }
}

/// What one replay of the withdrawn step budget did to a recording.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct BudgetReplay {
    pub budget: u64,
    pub aborted_at_call: Option<usize>,
    pub cumulative_tokens_at_abort: u64,
    pub directive_writes_after_the_end: Vec<usize>,
    pub project_writes_after_the_end: Vec<usize>,
}

/// The accounting of one recorded trajectory, read from the trajectory's JSON.
///
/// The actions come from `extra.actions` — the text the harness actually
/// executed.  `tool_calls[*].function.arguments` is **not** a safe source: the
/// round-5 fold replaces a superseded payload with a note plus a truncated
/// preview, so a large write directive parses as malformed there and its action
/// disappears.  The recorded results are paired by `tool_call_id`.
pub fn audit_trajectory(trajectory: &Value) -> Audit {
    let messages = trajectory["messages"]
        .as_array()
        .cloned()
        .unwrap_or_default();
    let mut results: BTreeMap<String, Option<i32>> = BTreeMap::new();
    for message in &messages {
        if let Some(id) = message["tool_call_id"].as_str() {
            let content = message["content"].as_str().unwrap_or("");
            results.insert(id.to_string(), returncode(content));
        }
    }

    let mut calls = Vec::new();
    let mut cumulative = 0u64;
    let mut scripts: BTreeMap<String, String> = BTreeMap::new();
    for message in &messages {
        let usage = &message["extra"]["response"]["usage"];
        let Some(prompt) = usage["prompt_tokens"].as_u64() else {
            continue;
        };
        let total = usage["total_tokens"]
            .as_u64()
            .unwrap_or(prompt + usage["completion_tokens"].as_u64().unwrap_or(0));
        cumulative += total;
        let mut entry = CallWrites {
            call: calls.len() + 1,
            total_tokens: total,
            cumulative_tokens: cumulative,
            directive_writes: Vec::new(),
            project_writes: Vec::new(),
            project_writes_failed: Vec::new(),
            undecided: Vec::new(),
        };
        let actions = message["extra"]["actions"]
            .as_array()
            .map(Vec::as_slice)
            .unwrap_or(&[]);
        for action in actions {
            let command = action["command"].as_str().unwrap_or("");
            let id = action["tool_call_id"].as_str().unwrap_or("");
            let outcome = match results.get(id) {
                Some(Some(0)) => Outcome::Ok,
                Some(Some(code)) => Outcome::Failed(*code),
                _ => Outcome::NotRecorded,
            };
            account_action(&mut entry, command, outcome, &mut scripts);
        }
        calls.push(entry);
    }
    Audit {
        calls,
        total_tokens: cumulative,
    }
}

/// Account for one recorded action.
fn account_action(
    entry: &mut CallWrites,
    command: &str,
    outcome: Outcome,
    scripts: &mut BTreeMap<String, String>,
) {
    match parse_directive(command) {
        Directive::Write { path, content } => {
            entry.directive_writes.push(path.clone());
            if path.to_ascii_lowercase().ends_with(".ps1")
                || path.to_ascii_lowercase().ends_with(".py")
            {
                scripts.insert(normalise_script(&path), content);
            }
            if scope_of(&path) == Scope::Project {
                push_write(entry, path, WriteSource::Directive, outcome);
            }
            return;
        }
        Directive::Read { .. } => return,
        Directive::Malformed { .. } => {
            // The harness answered with the help text; nothing was executed, and
            // the command must not be scanned as if it had been.
            entry.undecided.push(format!(
                "a directive the harness refused as malformed: {}",
                first_line(command)
            ));
            return;
        }
        Directive::Shell => {}
    }

    let mut named = named_writes(command);
    if let Some(script) = script_run(command) {
        if let Some(content) = scripts.get(&script) {
            let inner = if script.ends_with(".py") {
                python_named_writes(content)
            } else {
                shell_named_writes(content)
            };
            named.extend(inner.into_iter().map(|mut write| {
                write.script = Some(script.clone());
                write
            }));
        }
    }
    record_named(entry, named, outcome, command);
}

fn push_write(entry: &mut CallWrites, path: String, source: WriteSource, outcome: Outcome) {
    let write = ProjectWrite {
        call: entry.call,
        path,
        source,
        outcome,
    };
    if matches!(outcome, Outcome::Failed(_)) {
        entry.project_writes_failed.push(write);
    } else {
        entry.project_writes.push(write);
    }
}

fn record_named(entry: &mut CallWrites, named: Vec<NamedWrite>, outcome: Outcome, command: &str) {
    for write in named {
        let Some(target) = write.target.clone() else {
            entry.undecided.push(format!(
                "`{}` names a write whose destination the recording does not bind: {}",
                write.verb,
                first_line(command)
            ));
            continue;
        };
        if scope_of(&target) != Scope::Project {
            continue;
        }
        let path = target
            .trim()
            .trim_matches(|c| c == '\'' || c == '"' || c == '`')
            .to_string();
        let source = match write.script {
            Some(script) => WriteSource::Script { script },
            None => WriteSource::Shell,
        };
        push_write(entry, path, source, outcome);
    }
}

/// The return code the harness recorded for an action, from its own result text.
fn returncode(content: &str) -> Option<i32> {
    let start = content.find("<returncode>")? + "<returncode>".len();
    let rest = &content[start..];
    let end = rest.find("</returncode>")?;
    rest[..end].trim().parse().ok()
}

fn first_line(command: &str) -> String {
    let line = command.lines().next().unwrap_or("").trim();
    let mut text: String = line.chars().take(120).collect();
    if line.chars().count() > 120 {
        text.push('…');
    }
    text
}

/// Split a shell command into the units a shell would run separately.
///
/// `&&`, `||`, `|`, `&`, `;` and newlines.  This is a documented heuristic, not a
/// shell parser: a separator inside a quoted string splits too, which can only
/// make the accounting *more* conservative (a split fragment rarely names a write
/// verb and a destination on its own).
fn split_segments(text: &str) -> Vec<String> {
    let chars: Vec<char> = text.chars().collect();
    let mut segments = Vec::new();
    let mut current = String::new();
    let mut index = 0;
    while index < chars.len() {
        let ch = chars[index];
        if ch == '&' || ch == '|' {
            segments.push(std::mem::take(&mut current));
            index += 1;
            if index < chars.len() && (chars[index] == '&' || chars[index] == '|') {
                index += 1;
            }
            continue;
        }
        if ch == ';' || ch == '\n' {
            segments.push(std::mem::take(&mut current));
            index += 1;
            continue;
        }
        current.push(ch);
        index += 1;
    }
    segments.push(current);
    segments
}

/// Split one segment into tokens, treating a quoted run as one token.
fn tokenize(segment: &str) -> Vec<String> {
    let mut tokens = Vec::new();
    let mut current = String::new();
    let mut quote: Option<char> = None;
    for ch in segment.chars() {
        match quote {
            Some(open) if ch == open => quote = None,
            Some(_) => current.push(ch),
            None if ch == '\'' || ch == '"' => quote = Some(ch),
            None if ch.is_whitespace() => {
                if !current.is_empty() {
                    tokens.push(std::mem::take(&mut current));
                }
            }
            None => current.push(ch),
        }
    }
    if !current.is_empty() {
        tokens.push(current);
    }
    tokens
}

/// The verb a segment names, and the token it sits at.
fn segment_verb(tokens: &[String]) -> Option<(Verb, usize)> {
    if let Some(verb) = verb_of(&tokens[0]) {
        return Some((verb, 0));
    }
    let head = tokens[0].to_ascii_lowercase();
    let head = head
        .rsplit(['/', '\\'])
        .next()
        .unwrap_or("")
        .trim_end_matches(".exe");
    if matches!(head, "powershell" | "pwsh" | "cmd" | "call" | "bash" | "sh") {
        for (index, token) in tokens.iter().enumerate().skip(1) {
            if let Some(verb) = verb_of(token) {
                return Some((verb, index));
            }
        }
    }
    None
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum Verb {
    /// `Set-Content`, `Add-Content`, `Out-File`: the destination is the first
    /// operand.
    WriteCmdlet,
    /// `copy`, `xcopy`, `robocopy`: the destination is the **last** operand.
    Copy,
    /// `move`, `ren`, `Move-Item`, `Rename-Item`: the destination is the last.
    Move,
    /// `del`, `Remove-Item`: every operand is deleted, so every operand changes.
    Delete,
    /// `New-Item`, `md`: every operand is created.
    Make,
}

fn verb_of(token: &str) -> Option<Verb> {
    let lowered = token
        .trim_matches(|c| c == '\'' || c == '"')
        .to_ascii_lowercase();
    let lowered = lowered.rsplit(['/', '\\']).next().unwrap_or("");
    let lowered = lowered.trim_end_matches(".exe");
    match lowered {
        "set-content" | "add-content" | "out-file" | "tee-object" => Some(Verb::WriteCmdlet),
        "copy" | "xcopy" | "robocopy" | "copy-item" => Some(Verb::Copy),
        "move" | "move-item" | "mv" | "ren" | "rename" | "rename-item" => Some(Verb::Move),
        "del" | "erase" | "rd" | "rmdir" | "remove-item" | "rm" => Some(Verb::Delete),
        "md" | "mkdir" | "new-item" => Some(Verb::Make),
        _ => None,
    }
}

/// The operands after the verb, dropping flags and the values of flags that take
/// one.  A `-Path <value>` flag contributes its value, because that *is* the
/// destination.
fn operands(tokens: &[String], from: usize) -> Vec<String> {
    let mut out = Vec::new();
    let mut index = from + 1;
    while index < tokens.len() {
        let lowered = tokens[index].to_ascii_lowercase();
        if matches!(
            lowered.as_str(),
            "-path" | "-filepath" | "-literalpath" | "/path"
        ) {
            if index + 1 < tokens.len() {
                out.push(tokens[index + 1].clone());
                index += 2;
                continue;
            }
            index += 1;
            continue;
        }
        if lowered.starts_with('-') || lowered.starts_with('/') {
            if flag_takes_value(&lowered) && index + 1 < tokens.len() {
                index += 2;
            } else {
                index += 1;
            }
            continue;
        }
        out.push(tokens[index].clone());
        index += 1;
    }
    out
}

fn flag_takes_value(flag: &str) -> bool {
    matches!(
        flag,
        "-encoding"
            | "-value"
            | "-name"
            | "-filter"
            | "-include"
            | "-exclude"
            | "-delimiter"
            | "-stream"
            | "-itemtype"
            | "-erroraction"
            | "-width"
            | "-separator"
            | "-compressionlevel"
    )
}

/// Does this token look like a file path we can attribute a write to?
fn looks_like_path(token: &str) -> bool {
    let token = token
        .trim()
        .trim_matches(|c| c == '\'' || c == '"' || c == '`');
    if token.is_empty() || token.starts_with('-') || token.starts_with('$') {
        return false;
    }
    let lowered = token.to_ascii_lowercase();
    if matches!(lowered.as_str(), "nul" | "con" | "prn" | "&1" | "&2") {
        return false;
    }
    if token.contains('/') || token.contains('\\') || token.starts_with('.') {
        return true;
    }
    const EXTENSIONS: [&str; 17] = [
        "rs", "toml", "json", "jsonl", "md", "py", "ps1", "txt", "lock", "log", "out", "err",
        "yaml", "yml", "cfg", "ini", "csv",
    ];
    match token.rsplit_once('.') {
        Some((_, extension)) => EXTENSIONS.contains(&extension.to_ascii_lowercase().as_str()),
        None => false,
    }
}

/// Every write a shell command's text names.
fn shell_named_writes(command: &str) -> Vec<NamedWrite> {
    shell_named_writes_depth(command, 0)
}

/// The interpreter forms whose payload must be looked at separately.
///
/// A quoted `powershell -Command "Set-Content x y"` arrives as three tokens, the
/// last of them the whole payload; the payload is recursed into so a
/// single-command `-Command` string is not a blind spot.
fn interpreter_payload(tokens: &[String]) -> Option<String> {
    let head = tokens[0].to_ascii_lowercase();
    let head = head
        .rsplit(['/', '\\'])
        .next()
        .unwrap_or("")
        .trim_end_matches(".exe");
    if !matches!(head, "powershell" | "pwsh" | "cmd" | "call" | "bash" | "sh") {
        return None;
    }
    for (index, token) in tokens.iter().enumerate().skip(1) {
        let lowered = token.to_ascii_lowercase();
        if matches!(lowered.as_str(), "-command" | "-c" | "/c" | "/k" | "-file") {
            if lowered == "-file" {
                return None;
            }
            let payload = tokens[index + 1..].join(" ");
            if !payload.trim().is_empty() {
                return Some(payload);
            }
            return None;
        }
    }
    None
}

fn shell_named_writes_depth(command: &str, depth: usize) -> Vec<NamedWrite> {
    let substituted = shell_substitute(command);
    let mut out = Vec::new();
    for segment in split_segments(&substituted) {
        out.extend(io_file_writes(&segment));
        out.extend(redirect_writes(&segment));
        let tokens = tokenize(&segment);
        if tokens.is_empty() {
            continue;
        }
        if depth < 3 {
            if let Some(payload) = interpreter_payload(&tokens) {
                out.extend(shell_named_writes_depth(&payload, depth + 1));
            }
        }
        let Some((verb, index)) = segment_verb(&tokens) else {
            continue;
        };
        let found: Vec<String> = operands(&tokens, index)
            .into_iter()
            .filter(|token| looks_like_path(token))
            .collect();
        match verb {
            Verb::WriteCmdlet => {
                out.push(NamedWrite::direct("write-cmdlet", found.first().cloned()))
            }
            Verb::Copy => out.push(NamedWrite::direct("copy", found.last().cloned())),
            Verb::Move => out.push(NamedWrite::direct("move", found.last().cloned())),
            Verb::Delete => {
                for operand in found {
                    out.push(NamedWrite::direct("delete", Some(operand)));
                }
            }
            Verb::Make => {
                for operand in found {
                    out.push(NamedWrite::direct("make", Some(operand)));
                }
            }
        }
    }
    out
}

/// `[IO.File]::WriteAllText($p, $t)` — the first argument is the destination.
fn io_file_writes(segment: &str) -> Vec<NamedWrite> {
    let Some(marker) = segment.find("::WriteAll") else {
        return Vec::new();
    };
    let rest = &segment[marker..];
    let Some(open) = rest.find('(') else {
        return Vec::new();
    };
    let mut depth = 0;
    let mut end = rest.len();
    for (offset, ch) in rest[open..].char_indices() {
        match ch {
            '(' => depth += 1,
            ')' => {
                depth -= 1;
                if depth == 0 {
                    end = open + offset;
                    break;
                }
            }
            _ => {}
        }
    }
    let arguments = &rest[open + 1..end];
    let first = arguments.split(',').next().unwrap_or("").trim().to_string();
    vec![NamedWrite::direct("io.file.writeall", Some(first))]
}

/// `> path` and `>> path` redirections (a `nul` sink is not a file).
fn redirect_writes(segment: &str) -> Vec<NamedWrite> {
    let chars: Vec<char> = segment.chars().collect();
    let mut out = Vec::new();
    let mut index = 0;
    while index < chars.len() {
        if chars[index] != '>' {
            index += 1;
            continue;
        }
        index += 1;
        if index < chars.len() && chars[index] == '>' {
            index += 1;
        }
        if index < chars.len() && chars[index] == '&' {
            continue;
        }
        while index < chars.len() && chars[index].is_whitespace() {
            index += 1;
        }
        let mut target = String::new();
        while index < chars.len()
            && !chars[index].is_whitespace()
            && !matches!(chars[index], '&' | '|' | ';')
        {
            target.push(chars[index]);
            index += 1;
        }
        let target = target.trim_matches(|c| c == '\'' || c == '"' || c == '`');
        if looks_like_path(target) {
            out.push(NamedWrite::direct("redirect", Some(target.to_string())));
        }
    }
    out
}

/// Python writes whose destination the text names: `open(path, 'w'…)`.
fn python_named_writes(command: &str) -> Vec<NamedWrite> {
    let substituted = python_substitute(command);
    let chars: Vec<char> = substituted.chars().collect();
    let mut out = Vec::new();
    let mut index = 0;
    while index < chars.len() {
        if !starts_with_open_paren(&chars, index) || !is_word_boundary(&chars, index) {
            index += 1;
            continue;
        }
        let mut depth = 0;
        let mut end = chars.len();
        for offset in index..chars.len() {
            match chars[offset] {
                '(' => depth += 1,
                ')' => {
                    depth -= 1;
                    if depth == 0 {
                        end = offset;
                        break;
                    }
                }
                _ => {}
            }
        }
        let arguments: String = chars[index + 5..end].iter().collect();
        let parts = split_top_level(&arguments);
        if parts.len() >= 2 {
            let mode = parts[1].trim().trim_matches(|c| c == '\'' || c == '"');
            let mode = mode.to_ascii_lowercase();
            if mode.contains('w') || mode.contains('a') || mode.contains('+') {
                out.push(NamedWrite::direct(
                    "python.open",
                    Some(parts[0].trim().to_string()),
                ));
            }
        }
        index = end.saturating_add(1);
    }
    out
}

/// Does the text at char index `index` start with `open(`?
///
/// It is written over chars rather than over bytes because the recorded
/// commands carry non-ASCII text (em dashes in a role's own prose), and an
/// index derived from one must never be used as a byte offset.
fn starts_with_open_paren(chars: &[char], index: usize) -> bool {
    let open = ['o', 'p', 'e', 'n', '('];
    chars.len() >= index + open.len() && chars[index..index + open.len()] == open
}

fn is_word_boundary(chars: &[char], index: usize) -> bool {
    if index == 0 {
        return true;
    }
    !(chars[index - 1].is_alphanumeric() || chars[index - 1] == '_')
}

fn split_top_level(arguments: &str) -> Vec<&str> {
    let mut parts = Vec::new();
    let mut depth = 0;
    let mut quote: Option<char> = None;
    let mut start = 0;
    for (offset, ch) in arguments.char_indices() {
        match quote {
            Some(open) if ch == open => quote = None,
            Some(_) => {}
            None if ch == '\'' || ch == '"' => quote = Some(ch),
            None if ch == '(' || ch == '[' || ch == '{' => depth += 1,
            None if ch == ')' || ch == ']' || ch == '}' => depth -= 1,
            None if ch == ',' && depth == 0 => {
                parts.push(&arguments[start..offset]);
                start = offset + 1;
            }
            None => {}
        }
    }
    parts.push(&arguments[start..]);
    parts
}

/// Literal `name = 'value'` / `$name = 'value'` bindings found in the text.
fn literal_bindings(text: &str, dollars: bool) -> BTreeMap<String, String> {
    let chars: Vec<char> = text.chars().collect();
    let mut bindings = BTreeMap::new();
    let mut index = 0;
    while index < chars.len() {
        let starts_name = if dollars {
            chars[index] == '$'
        } else {
            (chars[index].is_alphabetic() || chars[index] == '_')
                && (index == 0
                    || !(chars[index - 1].is_alphanumeric()
                        || chars[index - 1] == '_'
                        || chars[index - 1] == '$'))
        };
        if !starts_name {
            index += 1;
            continue;
        }
        let name_start = if dollars { index + 1 } else { index };
        let mut cursor = name_start;
        while cursor < chars.len() && (chars[cursor].is_alphanumeric() || chars[cursor] == '_') {
            cursor += 1;
        }
        if cursor == name_start {
            index += 1;
            continue;
        }
        let name: String = chars[name_start..cursor].iter().collect();
        let mut probe = cursor;
        while probe < chars.len() && chars[probe] == ' ' {
            probe += 1;
        }
        if probe >= chars.len() || chars[probe] != '=' {
            index = cursor;
            continue;
        }
        probe += 1;
        while probe < chars.len() && chars[probe] == ' ' {
            probe += 1;
        }
        if probe >= chars.len() || (chars[probe] != '\'' && chars[probe] != '"') {
            index = cursor;
            continue;
        }
        let quote = chars[probe];
        let value_start = probe + 1;
        let mut value_end = value_start;
        while value_end < chars.len() && chars[value_end] != quote {
            value_end += 1;
        }
        if value_end < chars.len() {
            bindings.insert(name, chars[value_start..value_end].iter().collect());
        }
        index = value_end + 1;
    }
    bindings
}

fn substitute(text: &str, bindings: &BTreeMap<String, String>) -> String {
    if bindings.is_empty() {
        return text.to_string();
    }
    let chars: Vec<char> = text.chars().collect();
    let mut out = String::new();
    let mut index = 0;
    while index < chars.len() {
        let dollars = chars[index] == '$';
        let name_start = if dollars { index + 1 } else { index };
        let mut cursor = name_start;
        while cursor < chars.len() && (chars[cursor].is_alphanumeric() || chars[cursor] == '_') {
            cursor += 1;
        }
        if cursor > name_start {
            let name: String = chars[name_start..cursor].iter().collect();
            if let Some(value) = bindings.get(&name) {
                let boundary = dollars
                    || index == 0
                    || !(chars[index - 1].is_alphanumeric() || chars[index - 1] == '_');
                if boundary {
                    out.push_str(value);
                    index = cursor;
                    continue;
                }
            }
        }
        out.push(chars[index]);
        index += 1;
    }
    out
}

/// The key a recorded script is looked up under, independent of `\` vs `/`.
fn normalise_script(path: &str) -> String {
    let normalised = path.trim().trim_matches(|c| c == '\'' || c == '"');
    let normalised = normalised.replace('\\', "/");
    normalised.trim_start_matches("./").to_ascii_lowercase()
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    /// The accounting rule itself: a path under `.hoh/`, `.git/` or `target/` is
    /// not project progress, and the guard's own rule is the one used.
    #[test]
    fn the_scope_rule_is_the_guards_own() {
        for path in ["src/game.rs", "src\\game.rs", "./src/main.rs", "Cargo.toml"] {
            assert_eq!(scope_of(path), Scope::Project, "{path}");
        }
        for path in [
            ".hoh/scratch/tweak.ps1",
            ".hoh\\scratch\\tweak.ps1",
            "./.hoh/scratch/args/health.json",
            ".git/HEAD",
            "target/debug/hoh.exe",
        ] {
            assert_eq!(scope_of(path), Scope::Excluded, "{path}");
        }
    }

    /// A PowerShell write whose destination is a literal-bound variable.  This is
    /// the exact shape of the live call's call 95: without resolving `$p` the
    /// accounting sees no write at all, which is the defect being fixed.
    #[test]
    fn a_powershell_write_through_a_literal_variable_is_seen() {
        let command = "powershell -NoProfile -Command \"$p='src\\game.rs'; $c=Get-Content -Raw -Encoding UTF8 $p; Set-Content -NoNewline -Encoding UTF8 $p $c\"";
        let writes = shell_named_writes(command);
        assert_eq!(
            writes,
            vec![NamedWrite::direct(
                "write-cmdlet",
                Some("src\\game.rs".to_string())
            )],
            "{writes:?}"
        );
    }

    /// A copy *out of* the project writes the excluded destination, not the
    /// source.  A detector that counts every path a command mentions reports the
    /// live call's calls 65 and 103 as project writes; the accounting must not.
    #[test]
    fn a_copy_out_of_the_project_is_not_a_project_write() {
        let writes = shell_named_writes(
            "copy /Y src\\game.rs .hoh\\scratch\\game_a.rs >nul & copy /Y src\\contract.rs .hoh\\scratch\\c.rs >nul",
        );
        assert_eq!(writes.len(), 2, "{writes:?}");
        for write in &writes {
            assert_eq!(
                scope_of(write.target.as_deref().unwrap_or_default()),
                Scope::Excluded,
                "{write:?}"
            );
        }
    }

    /// The Python shape both recorded rounds used to edit `src/game.rs`.
    #[test]
    fn a_python_script_write_is_seen_and_a_read_only_open_is_not() {
        let script = "p = 'src/game.rs'\ns = open(p, encoding='utf-8').read()\nopen(p, 'w', encoding='utf-8').write(s)\n";
        let writes = python_named_writes(script);
        assert_eq!(
            writes,
            vec![NamedWrite::direct(
                "python.open",
                Some("src/game.rs".to_string())
            )],
            "{writes:?}"
        );
    }

    /// An unresolved destination is reported, never guessed — including one
    /// behind a quoted `powershell -Command` payload.
    #[test]
    fn an_unbound_destination_is_reported_and_not_counted() {
        assert_eq!(
            shell_named_writes("Set-Content $out $c"),
            vec![NamedWrite::direct("write-cmdlet", None)]
        );
        let quoted = shell_named_writes("powershell -Command \"Set-Content $out $c\"");
        assert_eq!(quoted, vec![NamedWrite::direct("write-cmdlet", None)]);
    }

    /// A directive the harness refused executed nothing, so it is undecided
    /// rather than a write — round-4 iteration 3's call 72.
    #[test]
    fn a_malformed_directive_is_undecided_not_a_write() {
        let trajectory = json!({
            "messages": [
                {"role": "assistant", "extra": {"response": {"usage": {"prompt_tokens": 10, "total_tokens": 20}},
                 "actions": [{"command": "HOH_WRITE_FILE .hoh/scratch/t.ps1\n$p='src\\game.rs'\n[IO.File]::WriteAllText($p,$t)\npowershell -File .hoh\\scratch\\t.ps1", "tool_call_id": "a"}]}},
                {"role": "tool", "tool_call_id": "a", "content": "<returncode>1</returncode>\n<output>is not closed</output>"}
            ]
        });
        let audit = audit_trajectory(&trajectory);
        assert_eq!(audit.recorded_calls(), 1);
        assert!(audit.calls[0].project_writes.is_empty());
        assert!(audit.calls[0].directive_writes.is_empty());
        assert_eq!(audit.undecided().len(), 1, "{:?}", audit.undecided());
    }

    /// A shell write whose recorded result is a failure did not change the file.
    #[test]
    fn a_failed_shell_write_is_recorded_as_an_attempt_not_a_change() {
        let trajectory = json!({
            "messages": [
                {"role": "assistant", "extra": {"response": {"usage": {"prompt_tokens": 10, "total_tokens": 20}},
                 "actions": [{"command": "powershell -Command \"$p='src\\game.rs'; Set-Content $p $c\"", "tool_call_id": "a"}]}},
                {"role": "tool", "tool_call_id": "a", "content": "<returncode>1</returncode>\n<output>ParserError</output>"}
            ]
        });
        let audit = audit_trajectory(&trajectory);
        assert_eq!(audit.project_write_calls(), Vec::<usize>::new());
        assert_eq!(
            audit.failed_project_writes(),
            vec![(1, "src\\game.rs".to_string(), 1)]
        );
    }

    /// The script is attributed to the call that ran it, and the write it makes
    /// is not visible in its command line at all.
    #[test]
    fn a_script_run_is_attributed_to_the_call_that_ran_it() {
        let trajectory = json!({
            "messages": [
                {"role": "assistant", "extra": {"response": {"usage": {"prompt_tokens": 10, "total_tokens": 20}},
                 "actions": [{"command": "HOH_WRITE_FILE .hoh/scratch/t.ps1\n$p='src\\game.rs'\n[IO.File]::WriteAllText($p, $t)\nHOH_END_WRITE_FILE", "tool_call_id": "a"}]}},
                {"role": "tool", "tool_call_id": "a", "content": "<returncode>0</returncode>\n<output>wrote 100 byte(s)</output>"},
                {"role": "assistant", "extra": {"response": {"usage": {"prompt_tokens": 10, "total_tokens": 30}},
                 "actions": [{"command": "powershell -NoProfile -ExecutionPolicy Bypass -File .hoh\\scratch\\t.ps1", "tool_call_id": "b"}]}},
                {"role": "tool", "tool_call_id": "b", "content": "<returncode>0</returncode>\n<output>ok bytes=42</output>"}
            ]
        });
        let audit = audit_trajectory(&trajectory);
        assert_eq!(audit.project_write_calls(), vec![2]);
        assert_eq!(
            audit.calls[1].project_writes[0].source,
            WriteSource::Script {
                script: ".hoh/scratch/t.ps1".to_string()
            }
        );
    }

    /// The withdrawn budget's own replay must not inherit the degeneracy the
    /// acceptance found: the "writes after the end" lists come from the whole
    /// recording, not from a loop that stops at the abort.
    #[test]
    fn the_replay_reports_writes_after_the_abort_from_the_whole_recording() {
        let trajectory = json!({
            "messages": [
                {"role": "assistant", "extra": {"response": {"usage": {"prompt_tokens": 10, "total_tokens": 10}},
                 "actions": [{"command": "HOH_WRITE_FILE src/game.rs\nx\nHOH_END_WRITE_FILE", "tool_call_id": "a"}]}},
                {"role": "tool", "tool_call_id": "a", "content": "<returncode>0</returncode>\n<output>wrote 1 byte(s)</output>"},
                {"role": "assistant", "extra": {"response": {"usage": {"prompt_tokens": 10, "total_tokens": 20}},
                 "actions": [{"command": "type src/game.rs", "tool_call_id": "b"}]}},
                {"role": "tool", "tool_call_id": "b", "content": "<returncode>0</returncode>\n<output>x</output>"},
                {"role": "assistant", "extra": {"response": {"usage": {"prompt_tokens": 10, "total_tokens": 30}},
                 "actions": [{"command": "dir /b", "tool_call_id": "c"}]}},
                {"role": "tool", "tool_call_id": "c", "content": "<returncode>0</returncode>\n<output>x</output>"},
                {"role": "assistant", "extra": {"response": {"usage": {"prompt_tokens": 10, "total_tokens": 40}},
                 "actions": [{"command": "HOH_WRITE_FILE .hoh/scratch/n.md\ny\nHOH_END_WRITE_FILE", "tool_call_id": "d"}]}},
                {"role": "tool", "tool_call_id": "d", "content": "<returncode>0</returncode>\n<output>wrote 1 byte(s)</output>"},
                {"role": "assistant", "extra": {"response": {"usage": {"prompt_tokens": 10, "total_tokens": 50}},
                 "actions": [{"command": "powershell -Command \"$p='src/game.rs'; Set-Content $p $c\"", "tool_call_id": "e"}]}},
                {"role": "tool", "tool_call_id": "e", "content": "<returncode>0</returncode>\n<output>ok</output>"}
            ]
        });
        let audit = audit_trajectory(&trajectory);
        assert_eq!(audit.directive_write_calls(), vec![1, 4]);
        assert_eq!(audit.project_write_calls(), vec![1, 5]);
        // K = 1: the call after the write at 1 and one more call without a write
        // is refused, so the abort lands on call 3.
        let replay = replay_directive_step_budget(&audit, 1);
        assert_eq!(replay.aborted_at_call, Some(3));
        assert_eq!(replay.cumulative_tokens_at_abort, 60);
        assert_eq!(replay.directive_writes_after_the_end, vec![4]);
        assert_eq!(replay.project_writes_after_the_end, vec![5]);
    }

    /// The two ends of the recording are windows too.
    #[test]
    fn the_longest_project_write_free_window_includes_both_ends() {
        let trajectory = json!({
            "messages": [
                {"role": "assistant", "extra": {"response": {"usage": {"prompt_tokens": 1, "total_tokens": 1}},
                 "actions": [{"command": "HOH_WRITE_FILE src/a.rs\nx\nHOH_END_WRITE_FILE", "tool_call_id": "a"}]}},
                {"role": "tool", "tool_call_id": "a", "content": "<returncode>0</returncode>\n<output>wrote 1 byte(s)</output>"},
                {"role": "assistant", "extra": {"response": {"usage": {"prompt_tokens": 1, "total_tokens": 1}},
                 "actions": [{"command": "type src/a.rs", "tool_call_id": "b"}]}},
                {"role": "tool", "tool_call_id": "b", "content": "<returncode>0</returncode>\n<output>x</output>"},
                {"role": "assistant", "extra": {"response": {"usage": {"prompt_tokens": 1, "total_tokens": 1}},
                 "actions": [{"command": "type src/a.rs", "tool_call_id": "c"}]}},
                {"role": "tool", "tool_call_id": "c", "content": "<returncode>0</returncode>\n<output>x</output>"}
            ]
        });
        let audit = audit_trajectory(&trajectory);
        assert_eq!(audit.longest_project_write_free_window(), Some((1, 4, 2)));
    }
}
