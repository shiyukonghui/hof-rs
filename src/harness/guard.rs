//! The environment wrapper that makes the write path first-class and the grind
//! impossible (round-1 write-path batch).
//!
//! Three jobs, all at the one boundary where a role's action becomes an
//! observation:
//!
//! 1. **The write/read path.**  A command that [`crate::harness::directive`]
//!    recognises is executed in Rust — no shell parses the content — and a
//!    command that is not a directive is handed to the real environment
//!    (`cmd.exe`) unchanged.  This is the fix for round 1's 140-call Developer:
//!    the content never meets `cmd.exe`, so `"`, `%`, `(`, `)`, `$`, `\` and raw
//!    newlines round-trip byte-for-byte.
//!
//! 2. **Fail fast on a repeated failing action.**  Round 1's tripwire was mini's
//!    `max_consecutive_format_errors`, which counts *consecutive* format errors
//!    and is reset by any success — so an agent that occasionally succeeded could
//!    retry the same broken command forever.  This wrapper counts failures **per
//!    action**: the same command failing
//!    `agent.max_action_failures` times aborts the call, whatever happened in
//!    between.
//!
//! 3. **A budget on producing the artifact.**  A role that has not written its
//!    declared artifact within `agent.artifact_write_budget_seconds` is aborted
//!    with a first-class status instead of being left to grind.  (The token half
//!    of the same budget cannot be measured inside the environment — usage is
//!    known only after the model call returns — so it is enforced by the runtime
//!    on the recorded attempt; see `crate::runtime::write_failure`.)
//!
//! An abort is **our own judgement, not the external agent's**: the error
//! carries [`FAIL_FAST_MARKER`], and `crate::harness::mini` turns it into a
//! normal `RoleOutcome` whose `exit_status` is one of the two first-class
//! statuses below.  Without that, the round would only ever have an external
//! agent's string and no harness-side fact.

use std::collections::BTreeMap;
use std::path::{Component, Path, PathBuf};
use std::sync::Mutex;
use std::time::{Duration, Instant};

use mini_swe_agent::{Action, Environment, Output, Result as MiniResult};
use serde_json::{json, Value};

use crate::harness::directive::{self, Directive};

/// The sentinel every fail-fast error carries.  `MiniHarness` recognises it and
/// converts the abort into a first-class [`crate::runtime::role::RoleOutcome`]
/// instead of a harness error.
pub const FAIL_FAST_MARKER: &str = "HOH_FAIL_FAST";

/// The same action failed `agent.max_action_failures` times.
///
/// Round-2 repair (cost batch): the same first-class status also covers the
/// **successful** grind — the same action succeeding with the same result
/// `agent.max_repeated_actions` times.  Both say one thing the runtime must act
/// on: this action is not making progress.  The `FailFast` variant carries which
/// of the two it was, so the abort message is exact.
pub const REPEATED_ACTION_STATUS: &str = "RepeatedActionError";
/// The role did not write its declared artifact inside
/// `agent.artifact_write_budget_seconds`.
pub const ARTIFACT_BUDGET_STATUS: &str = "ArtifactBudgetExceeded";
/// The call exhausted the step budget **that was in force at the moment it asked
/// for the next step** (round-4 repair).
///
/// It is deliberately not mini's `LimitsExceeded`.  Round 3 proved that the two
/// are different facts: mini's status means "the flat `step_limit` this call was
/// constructed with ran out", and a flat limit cannot follow progress.  This
/// status means "the guard re-read the live budget at the point of enforcement
/// and it was exhausted", which is the property the cost repair claimed and did
/// not have.  The runtime treats it as a limit (`runtime::invoke::is_limits_exceeded`
/// and `runtime::write_failure::is_failure_status` both accept it).
pub const STEP_BUDGET_STATUS: &str = "StepBudgetExceeded";

/// One call's step count, shared between the model (which makes the steps) and
/// the guard (which enforces the budget on them).
///
/// **A step is one model call** — mini's own `n_calls`, and therefore the unit
/// `agent.step_limit` is written in and the unit the prompt's "at most N steps"
/// means.  Round 4's first attempt counted *actions* instead, and that is a real,
/// measured mislabelling rather than a technicality: iteration 3's Developer call
/// emitted 44 actions across 30 model calls (14 of its 30 responses carried two
/// actions), so a budget the prompt stated as 43 cut it after 30 model calls.  A
/// number in the prompt that is not the number enforced is the round-3 defect in
/// a new place, so the counter lives where the model calls are made.
#[derive(Clone, Debug, Default)]
pub struct StepCounter {
    value: std::sync::Arc<std::sync::atomic::AtomicU64>,
}

impl StepCounter {
    pub fn new() -> Self {
        Self::default()
    }

    /// Count one model call, and answer the new total.
    pub fn increment(&self) -> u64 {
        self.value.fetch_add(1, std::sync::atomic::Ordering::SeqCst) + 1
    }

    /// How many model calls have been made.
    pub fn value(&self) -> u64 {
        self.value.load(std::sync::atomic::Ordering::SeqCst)
    }
}

/// The one-line usage text returned when a directive is malformed.
pub fn directive_help() -> String {
    format!(
        "the write path is a directive, not a shell command:\n\n\
         {write} <relative path>\n<the file's exact content>\n{end}\n\n\
         {read} <relative path>\n\n\
         The header must be the first line of the command, the content is everything \
         after it, and the final line is exactly `{end}`.  Nothing else parses the \
         content, so quotes, `%`, `$`, `(`, `)`, `\\` and newlines are all literal.",
        write = directive::WRITE_MARKER,
        read = directive::READ_MARKER,
        end = directive::END_MARKER,
    )
}

/// Why an abort happened, as a value (so it is testable without an agent).
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum FailFast {
    RepeatedAction {
        command: String,
        failures: u32,
    },
    /// Round-2 repair (cost batch): the same action kept **succeeding** in one
    /// call.  Round 2's Developer ended iteration 1 with about seventy calls of
    /// one verification loop, every one of them `returncode 0`; the per-action
    /// counter could not see it because it only counted failures, and a
    /// *consecutive* counter could not see it either because the loop spelled
    /// itself with several filters.  The count is therefore the action's successes
    /// **in one stretch between counted writes** (round-4 repair): a write of the
    /// declared artifact is progress and restarts it, because counting across one
    /// cannot tell "this call is not producing" from "this call is editing and
    /// rebuilding".
    RepeatedSuccess {
        command: String,
        /// How many times this action succeeded in the stretch that tripped it.
        repeats: u32,
        /// A short fingerprint of the last result, so the abort message says
        /// *what* came back without replaying it.
        output_digest: String,
    },
    ArtifactBudget {
        elapsed_seconds: u64,
        budget_seconds: u64,
    },
    /// Round-4 repair: the call asked for a step it no longer had.  The two
    /// numbers are the live ones, so the record says which budget was exceeded
    /// **and** which step the call was on.
    StepBudget {
        /// How many steps the call had already executed.
        steps: u64,
        /// The live budget in force when the next step was refused.  It is read
        /// from [`WriteGuardEnvironment::effective_step_budget`], which consults
        /// whether the call has written its artifact — so a write inside the call
        /// raises it.
        budget: u64,
    },
}

impl FailFast {
    /// The first-class exit status the runtime records for this abort.
    pub fn status(&self) -> &'static str {
        match self {
            // Both repeat shapes are one status: the runtime acts on them
            // identically, and a second status would be a second thing every
            // consumer had to learn.
            FailFast::RepeatedAction { .. } | FailFast::RepeatedSuccess { .. } => {
                REPEATED_ACTION_STATUS
            }
            FailFast::ArtifactBudget { .. } => ARTIFACT_BUDGET_STATUS,
            FailFast::StepBudget { .. } => STEP_BUDGET_STATUS,
        }
    }

    /// The error message, prefixed with [`FAIL_FAST_MARKER`] and the status, so
    /// the harness can both tell our abort apart from an infrastructure failure
    /// and recover the first-class status from the text alone.
    pub fn message(&self) -> String {
        match self {
            FailFast::RepeatedAction { command, failures } => format!(
                "{FAIL_FAST_MARKER} {REPEATED_ACTION_STATUS}: the same action failed {failures} \
                 time(s) (`agent.max_action_failures`); the action is:\n{}\nStop repeating it. If \
                 you cannot make it succeed, write the artifact you already have and end the call \
                 with the completion protocol.",
                brief(command)
            ),
            FailFast::RepeatedSuccess {
                command,
                repeats,
                output_digest,
            } => format!(
                "{FAIL_FAST_MARKER} {REPEATED_ACTION_STATUS}: the same action succeeded {repeats} \
                 times since this call last wrote the artifact it declares (last output \
                 {output_digest}) (`agent.max_repeated_actions`, re-read here, at the point of \
                 enforcement); the action is:\n{}\nIt is not making progress: choose a different \
                 action, or write the artifact you have and end the call with the completion \
                 protocol.",
                brief(command)
            ),
            FailFast::ArtifactBudget {
                elapsed_seconds,
                budget_seconds,
            } => format!(
                "{FAIL_FAST_MARKER} {ARTIFACT_BUDGET_STATUS}: {elapsed_seconds} s elapsed without \
                 a write to the project, over the {budget_seconds} s artifact-write budget \
                 (`agent.artifact_write_budget_seconds`). Stop exploring: write the artifact now \
                 with the `{}` directive and end the call.",
                directive::WRITE_MARKER
            ),
            FailFast::StepBudget { steps, budget } => format!(
                "{FAIL_FAST_MARKER} {STEP_BUDGET_STATUS}: this call has made {steps} model call(s) \
                 and its live step budget is {budget} (`agent.steps_per_artifact`, re-read here, at \
                 the point of enforcement). The budget rises the moment the call writes the artifact \
                 it declares. Write the artifact you already have and end the call with the \
                 completion protocol, or make progress and continue."
            ),
        }
    }
}

/// The first-class status a fail-fast error message carries, if it is one.
///
/// This is the recovery half of the sentinel: `MiniHarness` receives mini's
/// opaque `AgentError::Other`, and the status must survive that boundary so the
/// round records **our** judgement rather than the external agent's string.
pub fn fail_fast_status(message: &str) -> Option<&'static str> {
    let marker = message.find(FAIL_FAST_MARKER)?;
    let rest = &message[marker + FAIL_FAST_MARKER.len()..];
    for status in [
        REPEATED_ACTION_STATUS,
        ARTIFACT_BUDGET_STATUS,
        STEP_BUDGET_STATUS,
    ] {
        if rest.trim_start().starts_with(status) {
            return Some(status);
        }
    }
    None
}

/// The first line of a command, so an abort message stays readable.
fn brief(command: &str) -> String {
    let first = command.lines().next().unwrap_or("").trim();
    let mut text: String = first.chars().take(200).collect();
    if first.chars().count() > 200 {
        text.push('…');
    }
    text
}

/// The mutable state of one role call.
#[derive(Debug)]
struct GuardState {
    /// Failures per action signature.  A success of the *same* signature clears
    /// it; nothing else does, which is the difference from "consecutive".
    failures: BTreeMap<String, u32>,
    /// Round-2 repair (cost batch): how many times each action has **succeeded**
    /// in this call.  Unlike [`GuardState::failures`], this counter is never
    /// cleared by another action: an action that runs four times early and four
    /// times late is still eight runs of the same action, which is exactly the
    /// shape round 2's verification loop had (about seventy calls of one loop,
    /// spelled with several filters so that no *consecutive* counter saw it).
    ///
    /// Round-4 repair: it **is** cleared by a successful write of the role's
    /// declared artifact.  The counter answers "is this call making progress?",
    /// and a write is progress; counting across one makes a legitimate
    /// edit/rebuild cadence (round 2's iteration 2, and all three round-3
    /// Developer calls) look like the grind this counter exists to catch.  See
    /// [`WriteGuardEnvironment::record_success`].
    /// Round-4 repair: the model-call count lives in the shared [`StepCounter`],
    /// not here.  This struct counts what the environment itself observes — the
    /// failures and the successes of actions, and whether the artifact was written
    /// — and deliberately no longer counts "steps": an action is not a step, and
    /// two units for one number is how the first attempt was mislabelled.
    successes: BTreeMap<String, u32>,
    /// The first successful write of a **project** file (not `.hoh/**`, not a
    /// cache) — the artifact the budget is about.
    artifact_written: bool,
    /// A successful write of any file, for the record.
    writes: u64,
}

impl GuardState {
    fn new() -> Self {
        Self {
            failures: BTreeMap::new(),
            successes: BTreeMap::new(),
            artifact_written: false,
            writes: 0,
        }
    }
}

/// A short, stable fingerprint of a tool result, so "the same result again" is a
/// value rather than a comparison of unbounded text.
fn output_digest(output: &str) -> String {
    let bytes = output.as_bytes();
    format!(
        "{} ({} byte(s))",
        &crate::runtime::policy::sha256_hex(bytes)[..12],
        bytes.len()
    )
}

/// Round-2 repair (cost batch), rewritten by the round-4 repair: state the step
/// budget the call is **really held to**, without promising anything the guard
/// does not do.
///
/// Round 3's defect was not only that the number was frozen — it was that the
/// note lied about its own rule.  It said "the first successful project write
/// removes the gate" while the frozen 43 was checked by mini before the call
/// started, and the same prompt's body said 150.  The three numbers are now said
/// once each, and each one is true:
///
/// * `flat_step_limit` is the **ceiling** — the number the body's "at most N
///   steps" refers to, and mini's own backstop;
/// * `gated_step_limit` is the budget **in force at this moment**, read from the
///   same live source the guard enforces against;
/// * the rule that moves from one to the other is stated as a rule, because the
///   guard re-reads it at every step (see
///   [`WriteGuardEnvironment::step_budget_exceeded`]).
///
/// A prompt that states no budget is returned unchanged, exactly as before.
pub fn state_the_effective_budget(
    prompt: &str,
    gated_step_limit: u64,
    flat_step_limit: u64,
    wrap_up_steps: u64,
) -> String {
    if !states_a_budget(prompt) {
        return prompt.to_string();
    }
    let note = if flat_step_limit == 0 {
        format!(
            "\n\n[budget] No step limit is configured for this call, so none is enforced here; the \
             wrap-up discipline the instructions describe is not step-bounded. If that is not what \
             this call should run under, the configuration (`agent.step_limit`) is the place to say \
             so.\n"
        )
    } else if gated_step_limit >= flat_step_limit {
        format!(
            "\n\n[budget] This call's enforced step budget is {gated_step_limit}, the flat limit in \
             the instructions above; no progress gate is configured for it. The limit is re-read at \
             every step, and the wrap-up discipline begins {wrap_up_steps} steps before it.\n"
        )
    } else {
        format!(
            "\n\n[budget] The flat limit in the instructions above ({flat_step_limit}) is this \
             call's ceiling. Until this call writes the artifact it declares, the budget actually \
             enforced on it is {gated_step_limit}; the first successful project write raises it to \
             {flat_step_limit}. That limit is re-read at every step, so the raise takes effect \
             inside this call. The wrap-up discipline begins {wrap_up_steps} steps before the limit \
             in force.\n"
        )
    };
    format!("{prompt}{note}")
}

/// Round-2 repair (cost batch): does this rendered prompt state a step budget?
///
/// The `[budget]` note is only appended to a prompt that talks about a budget,
/// so a prompt for a role that has none cannot grow a number it does not use.
pub fn states_a_budget(prompt: &str) -> bool {
    prompt.contains("step budget")
}

/// Round-2 repair (cost batch): the key a recorded command is counted under.
///
/// It exists so the recorded round-2 trajectories can be **measured** against the
/// live tripwire instead of the tripwire being asserted to work: the test that
/// projects what the abort would have saved must use the same identity the guard
/// uses.  The normalisation folds away spellings that do not change the action —
/// an absolute `cd /d … &&` prefix, a trailing `& echo NAME=%ERRORLEVEL%`
/// marker, a `| more`/`| findstr …` filter, and runs of whitespace — while
/// keeping everything that does (a different flag, a different path, a different
/// subcommand).
///
/// It is deliberately conservative: folding too little only makes the tripwire
/// quieter, while folding too much would abort work that was making progress.
pub fn repeated_action_key(command: &str) -> String {
    let mut text = command.trim().to_string();
    // An absolute `cd /d <path> &&` prefix: the same command in the same
    // directory, spelled two ways.
    if let Some(rest) = strip_ci_prefix(&text, "cd /d ") {
        if let Some(position) = rest.find("&&") {
            text = rest[position + 2..].trim().to_string();
        }
    }
    // A trailing exit-code marker (`& echo BUILD_EXIT=%ERRORLEVEL%`).
    if let Some(position) = find_ci(&text, "& echo ") {
        let tail = &text[position + "& echo ".len()..];
        if tail.to_ascii_uppercase().contains("ERRORLEVEL") {
            text = text[..position].trim().to_string();
        }
    }
    // Trailing output filters, repeatedly (`| more`, `| findstr …`, and — round-4
    // repair — `| tail -N`, `| head -N`).  A filter changes how much of the
    // output is shown; it does not change the action, and leaving `tail` out made
    // the tripwire blind to the exact grind shape it exists for: round 3's
    // iteration 1 spelled nine identical builds as `… 2>&1 | tail -20`,
    // `… 2>&1 | tail -5 &` and `… 2>&1 | tail -3 &`, which the old key counted
    // as three actions of three.
    loop {
        let Some(position) = text.rfind('|') else {
            break;
        };
        let tail = text[position + 1..].trim().to_ascii_lowercase();
        let head = tail.split_whitespace().next().unwrap_or("");
        let is_filter = matches!(head, "more" | "tail" | "head" | "find" | "findstr");
        if !is_filter {
            break;
        }
        text = text[..position].trim().to_string();
    }
    // Trailing shell redirections, repeatedly (`2>&1`, `>nul`, `<nul`, a lone
    // trailing `&`).  Evidence: round 2's iteration 2 spelled its 14 legitimate
    // rebuilds `cargo build --offline 2>&1` and round 3's `cargo build --offline`,
    // and the two spellings are the same action.
    loop {
        let folded = fold_one_redirect(&text);
        if folded == text {
            break;
        }
        text = folded;
    }
    text.split_whitespace().collect::<Vec<_>>().join(" ")
}

/// Strip one trailing shell redirection (or one lone trailing `&`), if present.
///
/// It is a suffix match over a closed list, not a shell parser: anything it does
/// not recognise is left exactly as it was, because folding too little only makes
/// the tripwire quieter while folding too much would abort work that was making
/// progress.
fn fold_one_redirect(text: &str) -> String {
    let trimmed = text.trim_end();
    let lowered = trimmed.to_ascii_lowercase();
    let mut candidates: Vec<String> = Vec::new();
    for stream in ["", "1", "2"] {
        for target in ["1", "2"] {
            candidates.push(format!("{stream}>&{target}"));
        }
        for operator in ['>', '<'] {
            candidates.push(format!("{stream}{operator}nul"));
            candidates.push(format!("{stream}{operator}nul:"));
        }
    }
    candidates.push("&".to_string());
    // Longest first, so `2>&1` is folded as one redirection rather than the lone
    // `&` inside it.
    candidates.sort_by_key(|candidate| std::cmp::Reverse(candidate.len()));
    for candidate in candidates {
        if lowered.ends_with(&candidate) {
            return trimmed[..trimmed.len() - candidate.len()]
                .trim_end()
                .to_string();
        }
    }
    trimmed.to_string()
}

/// `strip_prefix`, case-insensitively (Rust has no such method).
fn strip_ci_prefix<'a>(text: &'a str, prefix: &str) -> Option<&'a str> {
    if text.len() >= prefix.len() && text[..prefix.len()].eq_ignore_ascii_case(prefix) {
        Some(&text[prefix.len()..])
    } else {
        None
    }
}

/// `find`, case-insensitively.
fn find_ci(text: &str, needle: &str) -> Option<usize> {
    let haystack = text.to_ascii_lowercase();
    haystack.find(&needle.to_ascii_lowercase())
}

/// What counts as "the artifact this role declared" for the write budget.
///
/// The Developer's artifact is the **project**; a write under `.hoh/**` is
/// scratch and does not count as an increment (that is the `no_engineering_write`
/// rule).  The Planner's and the Tester's artifacts (`.hoh/plan.md`,
/// `.hoh/evidence.json`) live under `.hoh/**` by construction, so for them any
/// write counts — otherwise their budget could never be disarmed and a role that
/// had already written its artifact would be aborted for not writing one.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ArtifactKind {
    /// A file inside the project, outside the hash-excluded paths.
    ProjectFile,
    /// Any file the role can write.
    AnyFile,
}

impl ArtifactKind {
    /// The kind that matches `role`'s declared artifact.
    pub fn for_role(role: crate::model::Role) -> Self {
        match role {
            crate::model::Role::Developer => ArtifactKind::ProjectFile,
            crate::model::Role::Planner | crate::model::Role::Tester => ArtifactKind::AnyFile,
        }
    }

    /// Does a successful write to `path` count as this role's artifact?
    ///
    /// It is public because the recorded-evidence tests must measure the
    /// repeated-action counter with the **same** rule the guard applies: a test
    /// that decides for itself which writes are progress can prove anything.
    pub fn counts(self, path: &str) -> bool {
        match self {
            ArtifactKind::ProjectFile => !is_excluded_path(path),
            ArtifactKind::AnyFile => true,
        }
    }
}

/// The environment a role runs against: the real shell plus the two guards.
pub struct WriteGuardEnvironment {
    inner: Box<dyn Environment>,
    cwd: PathBuf,
    max_action_failures: u32,
    /// Round-2 repair (cost batch): how many successes of one action are
    /// tolerated in a call before the call is aborted.  0 disables it.
    max_repeated_actions: u32,
    /// Round-2 repair (cost batch): the flat step budget, and the gates that
    /// make it respond to progress.  See
    /// [`crate::config::AgentLimits::effective_step_limit`].
    step_limit: u64,
    wrap_up_steps: u64,
    steps_per_artifact: u64,
    artifact_budget: Option<Duration>,
    artifact_kind: ArtifactKind,
    /// Round-4 repair: the **shared model-call counter**.
    ///
    /// A step is a model call (mini's `n_calls`), so the number the budget is
    /// enforced against must be counted where the model calls happen — see
    /// [`StepCounter`].  When no counter is shared the step budget is **inert**
    /// rather than measured in a second unit: counting actions here is exactly the
    /// mislabelling round 4's first attempt was cut by, and a guard that silently
    /// switched units would reproduce it.
    step_counter: Option<StepCounter>,
    started: Instant,
    state: Mutex<GuardState>,
}

impl WriteGuardEnvironment {
    pub fn new(
        inner: Box<dyn Environment>,
        cwd: PathBuf,
        max_action_failures: u32,
        artifact_budget_seconds: u64,
    ) -> Self {
        Self::with_artifact_kind(
            inner,
            cwd,
            max_action_failures,
            artifact_budget_seconds,
            ArtifactKind::ProjectFile,
        )
    }

    pub fn with_artifact_kind(
        inner: Box<dyn Environment>,
        cwd: PathBuf,
        max_action_failures: u32,
        artifact_budget_seconds: u64,
        artifact_kind: ArtifactKind,
    ) -> Self {
        // A construction that does not name the new limits keeps the old
        // behaviour exactly: no repeated-success tripwire, no progress gate.
        Self::with_limits(
            inner,
            cwd,
            max_action_failures,
            artifact_budget_seconds,
            artifact_kind,
            0,
            0,
            0,
            0,
        )
    }

    /// Round-2 repair (cost batch): the full construction, with the repeated-
    /// success tripwire and the progress-responsive step budget.
    #[allow(clippy::too_many_arguments)]
    pub fn with_limits(
        inner: Box<dyn Environment>,
        cwd: PathBuf,
        max_action_failures: u32,
        artifact_budget_seconds: u64,
        artifact_kind: ArtifactKind,
        max_repeated_actions: u64,
        step_limit: u64,
        wrap_up_steps: u64,
        steps_per_artifact: u64,
    ) -> Self {
        Self {
            inner,
            cwd,
            max_action_failures,
            max_repeated_actions: max_repeated_actions as u32,
            step_limit,
            wrap_up_steps,
            steps_per_artifact,
            artifact_budget: if artifact_budget_seconds == 0 {
                None
            } else {
                Some(Duration::from_secs(artifact_budget_seconds))
            },
            artifact_kind,
            step_counter: None,
            started: Instant::now(),
            state: Mutex::new(GuardState::new()),
        }
    }

    /// Round-4 repair: measure this call's steps by the **model calls** it makes
    /// (the shared [`StepCounter`]), not by the actions those calls emit.
    ///
    /// The distinction is not academic: round 4's first attempt counted actions,
    /// and a Developer call whose responses carried two actions at a time was cut
    /// after 30 model calls against a budget the prompt stated as 43.  mini's
    /// `n_calls` — and therefore `agent.step_limit` — counts model calls, and this
    /// is what makes the enforced number and the stated number the same number.
    pub fn sharing_steps(mut self, counter: StepCounter) -> Self {
        self.step_counter = Some(counter);
        self
    }

    /// Round-2 repair (cost batch): the step budget this call may really use,
    /// given whether it has written its artifact yet.
    pub fn effective_step_budget(&self) -> u64 {
        let limits = crate::config::AgentLimits {
            step_limit: self.step_limit,
            wrap_up_steps: self.wrap_up_steps,
            steps_per_artifact: self.steps_per_artifact,
            ..crate::config::AgentLimits::default()
        };
        limits.effective_step_limit(self.artifact_written())
    }

    /// Round-4 repair: how many steps this call has taken — the **model calls**
    /// the shared [`StepCounter`] counted.  `0` when no counter is shared, which
    /// is also why [`WriteGuardEnvironment::step_budget_exceeded`] is inert then.
    pub fn steps(&self) -> u64 {
        self.step_counter
            .as_ref()
            .map(StepCounter::value)
            .unwrap_or(0)
    }

    /// Round-4 repair: the one place the step budget is **enforced**, and it
    /// reads the live value every time it is asked.
    ///
    /// Round 3's defect is exactly the difference between this function and the
    /// old one: `mini_swe_agent::DefaultAgent::check_limits` reads
    /// `AgentConfig::step_limit`, which is fixed when the agent is constructed —
    /// before the call has done anything — so a write *inside* the call could
    /// never raise it, and all three round-3 Developer calls were cut at the
    /// unwritten 43 while their own prompt told them a write would lift it.
    /// Asking here means every step sees the current answer.
    ///
    /// The rule mirrors mini's own: **exactly `budget` model calls are allowed**,
    /// and the actions of the next one are refused with [`STEP_BUDGET_STATUS`].
    /// (`steps > budget` rather than `>=` is what makes it "exactly": the count is
    /// read after the model call has been made but before its actions run, so the
    /// budget-th call still does its work.  The budget-plus-one call is billed and
    /// then aborted, which is one call later than mini's own interrupt and is the
    /// price of enforcing the live value where the work happens.)
    ///
    /// `step_limit == 0` disables the guard's half entirely, because that is what
    /// mini's zero means ("no limit"); the flat ceiling mini itself holds is
    /// unchanged.
    fn step_budget_exceeded(&self) -> Option<FailFast> {
        if self.step_limit == 0 {
            return None;
        }
        // No model call has been counted, so there is no step number to enforce.
        self.step_counter.as_ref()?;
        let budget = self.effective_step_budget().min(self.step_limit);
        let steps = self.steps();
        if steps > budget {
            Some(FailFast::StepBudget { steps, budget })
        } else {
            None
        }
    }

    /// Has this call made a project write yet?
    pub fn artifact_written(&self) -> bool {
        self.state
            .lock()
            .map(|state| state.artifact_written)
            .unwrap_or(false)
    }

    /// How many directive writes succeeded.
    pub fn writes(&self) -> u64 {
        self.state.lock().map(|state| state.writes).unwrap_or(0)
    }

    fn record_success(&self, command: &str, output: &str) -> Option<FailFast> {
        let mut state = self.state.lock().ok()?;
        state.failures.remove(command);
        if self.max_repeated_actions == 0 {
            return None;
        }
        let digest = output_digest(output);
        let key = repeated_action_key(command);
        let count = {
            let entry = state.successes.entry(key).or_insert(0u32);
            *entry += 1;
            *entry
        };
        if count < self.max_repeated_actions {
            return None;
        }
        // One action may not run the whole call: the abort names the action, how
        // many times it ran, and the last result, so the record says what the
        // grind was.
        state.successes.clear();
        Some(FailFast::RepeatedSuccess {
            command: command.to_string(),
            repeats: count,
            output_digest: digest,
        })
    }

    fn record_failure(&self, command: &str) -> Option<FailFast> {
        if self.max_action_failures == 0 {
            return None;
        }
        let mut state = self.state.lock().ok()?;
        let entry = state.failures.entry(command.to_string()).or_insert(0u32);
        *entry += 1;
        let failures = *entry;
        if failures >= self.max_action_failures {
            // Bound the map: an agent that has just been aborted does not need
            // its per-command history any more.
            state.failures.clear();
            Some(FailFast::RepeatedAction {
                command: command.to_string(),
                failures,
            })
        } else {
            None
        }
    }

    fn budget_exceeded(&self) -> Option<FailFast> {
        let budget = self.artifact_budget?;
        let written = self.artifact_written();
        if written {
            return None;
        }
        let elapsed = self.started.elapsed();
        if elapsed >= budget {
            Some(FailFast::ArtifactBudget {
                elapsed_seconds: elapsed.as_secs(),
                budget_seconds: budget.as_secs(),
            })
        } else {
            None
        }
    }

    /// Resolve a directive's path against the role's working directory.
    ///
    /// Only relative paths are accepted, and no `..` component is permitted, so
    /// a directive cannot be used to write outside the view the role owns.  It
    /// is deliberately *not* a policy layer (the Tester's `.hoh/**`-only rule
    /// stays the hash assertion's job); it is a path-safety layer.
    fn resolve(&self, path: &str) -> anyhow::Result<PathBuf> {
        let candidate = Path::new(path);
        if candidate.is_absolute() {
            anyhow::bail!(
                "`{path}` is absolute; a directive path is relative to the working directory"
            );
        }
        for component in candidate.components() {
            if matches!(component, Component::ParentDir) {
                anyhow::bail!("`{path}` escapes the working directory with `..`");
            }
        }
        if path.trim().is_empty() {
            anyhow::bail!("the directive gave an empty path");
        }
        Ok(self.cwd.join(candidate))
    }

    fn execute_write(&self, path: &str, content: &str) -> Output {
        let resolved = match self.resolve(path) {
            Ok(resolved) => resolved,
            Err(error) => return Output::success(error.to_string(), 1),
        };
        if let Some(parent) = resolved.parent() {
            if let Err(error) = std::fs::create_dir_all(parent) {
                return Output::success(
                    format!("could not create {}: {error}", parent.display()),
                    1,
                );
            }
        }
        match std::fs::write(&resolved, content.as_bytes()) {
            Ok(()) => {
                let counts = self.artifact_kind.counts(path);
                if let Ok(mut state) = self.state.lock() {
                    state.writes += 1;
                    if counts {
                        state.artifact_written = true;
                        // Round-4 repair: a write of the artifact is progress, so
                        // the repeated-action counter — which answers "is this
                        // call getting anywhere?" — starts again.  Counting
                        // across a write made a legitimate edit/rebuild cadence
                        // indistinguishable from a grind (see `GuardState::successes`).
                        state.successes.clear();
                    }
                }
                let mut output =
                    Output::success(format!("wrote {} byte(s) to {}", content.len(), path), 0);
                output
                    .extra
                    .insert("hoh_write_path".to_string(), json!(path));
                output
                    .extra
                    .insert("hoh_write_bytes".to_string(), json!(content.len()));
                output
            }
            Err(error) => Output::success(format!("could not write {path}: {error}"), 1),
        }
    }

    fn execute_read(&self, path: &str) -> Output {
        let resolved = match self.resolve(path) {
            Ok(resolved) => resolved,
            Err(error) => return Output::success(error.to_string(), 1),
        };
        match std::fs::read(&resolved) {
            Ok(bytes) => {
                // The bytes are what they are; a file that is not valid UTF-8 is
                // reported as such rather than silently mangled.
                match String::from_utf8(bytes) {
                    Ok(text) => Output::success(text, 0),
                    Err(error) => Output::success(
                        format!(
                            "{} is not UTF-8 text ({} byte(s)): {}",
                            path,
                            error.as_bytes().len(),
                            error.utf8_error()
                        ),
                        1,
                    ),
                }
            }
            Err(error) => Output::success(format!("could not read {path}: {error}"), 1),
        }
    }
}

/// Is this path under a runtime-excluded or cache directory (not an artifact)?
fn is_excluded_path(path: &str) -> bool {
    let normalized = path.replace('\\', "/");
    let normalized = normalized.trim_start_matches("./");
    ["\\.hoh/", "\\.git/", "target/", ".hoh/", ".git/"]
        .iter()
        .any(|prefix| normalized.starts_with(prefix))
}

#[async_trait::async_trait]
impl Environment for WriteGuardEnvironment {
    async fn execute(
        &self,
        action: &Action,
        cwd: Option<&str>,
        timeout: Option<u64>,
    ) -> MiniResult<Output> {
        // Round-4 repair: the budget is checked **here**, at the point of
        // enforcement, against the live value — not once, before the call.  It is
        // the model-call count, so it is the same number for a directive and for a
        // shell command: a step is a model call, and its action is what is refused.
        if let Some(fail_fast) = self.step_budget_exceeded() {
            return Err(mini_swe_agent::AgentError::other(anyhow::anyhow!(
                "{}",
                fail_fast.message()
            )));
        }

        match directive::parse_directive(&action.command) {
            Directive::Write { path, content } => {
                return Ok(self.execute_write(&path, &content));
            }
            Directive::Read { path } => {
                return Ok(self.execute_read(&path));
            }
            Directive::Malformed { reason } => {
                return Ok(Output::success(
                    format!("{reason}\n\n{}", directive_help()),
                    1,
                ));
            }
            Directive::Shell => {}
        }

        let output = self.inner.execute(action, cwd, timeout).await?;
        if output.returncode == 0 {
            if let Some(fail_fast) = self.record_success(&action.command, &output.output) {
                return Err(mini_swe_agent::AgentError::other(anyhow::anyhow!(
                    "{}",
                    fail_fast.message()
                )));
            }
        } else if let Some(fail_fast) = self.record_failure(&action.command) {
            return Err(mini_swe_agent::AgentError::other(anyhow::anyhow!(
                "{}",
                fail_fast.message()
            )));
        }
        if let Some(fail_fast) = self.budget_exceeded() {
            return Err(mini_swe_agent::AgentError::other(anyhow::anyhow!(
                "{}",
                fail_fast.message()
            )));
        }
        Ok(output)
    }

    fn get_template_vars(&self) -> Value {
        self.inner.get_template_vars()
    }

    fn serialize(&self) -> Value {
        self.inner.serialize()
    }

    fn cleanup(&self) -> anyhow::Result<()> {
        self.inner.cleanup()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::harness::directive::render_write;

    /// A stand-in for the real shell: records the commands it was asked to run
    /// and answers with a scripted return code and output.
    struct FakeShell {
        seen: std::sync::Arc<Mutex<Vec<String>>>,
        returncode: i32,
        output: String,
    }

    impl FakeShell {
        fn new(returncode: i32) -> Self {
            Self {
                seen: std::sync::Arc::new(Mutex::new(Vec::new())),
                returncode,
                output: "shell output".to_string(),
            }
        }

        /// The same shell, with a set output: a test can drive the output the
        /// counter sees without changing the action.
        #[allow(dead_code)]
        fn with_output(mut self, output: &str) -> Self {
            self.output = output.to_string();
            self
        }
    }

    #[async_trait::async_trait]
    impl Environment for FakeShell {
        async fn execute(
            &self,
            action: &Action,
            _cwd: Option<&str>,
            _timeout: Option<u64>,
        ) -> MiniResult<Output> {
            self.seen
                .lock()
                .expect("the fake shell")
                .push(action.command.clone());
            Ok(Output::success(self.output.clone(), self.returncode))
        }
        fn get_template_vars(&self) -> Value {
            Value::Null
        }
        fn serialize(&self) -> Value {
            Value::Null
        }
        fn cleanup(&self) -> anyhow::Result<()> {
            Ok(())
        }
    }

    fn guard(root: &Path, failures: u32, budget: u64) -> WriteGuardEnvironment {
        guard_with(root, 0, failures, budget)
    }

    fn guard_with(
        root: &Path,
        shell_returncode: i32,
        failures: u32,
        budget: u64,
    ) -> WriteGuardEnvironment {
        WriteGuardEnvironment::new(
            Box::new(FakeShell::new(shell_returncode)),
            root.to_path_buf(),
            failures,
            budget,
        )
    }

    fn run(command: &str, root: &Path) -> Output {
        let environment = guard(root, 3, 0);
        futures_lite_block_on(async {
            environment
                .execute(&Action::new(command), None, None)
                .await
                .expect("the guard runs")
        })
    }

    /// A tiny executor for the tests: the guard is async only because mini's
    /// trait is, and blocking on it keeps the tests readable.
    fn futures_lite_block_on<F: std::future::Future>(future: F) -> F::Output {
        tokio::runtime::Builder::new_current_thread()
            .enable_all()
            .build()
            .expect("a test runtime")
            .block_on(future)
    }

    /// Round-2 repair (cost batch): the grind shape round 2 measured is invisible
    /// to every older counter — the Developer ended iteration 1 with ~70 calls of
    /// one verification loop, and **every one of them succeeded**.
    /// `max_action_failures` only counts failures and
    /// `max_consecutive_format_errors` only format errors, so this is the
    /// counter that sees it.
    ///
    /// The count is the action's successes in one stretch between counted writes,
    /// **not** a consecutive run: round 2's loop spelled itself with several
    /// filters (`| more`, `| findstr …`, `& echo …=%ERRORLEVEL%`, and `| tail -N`,
    /// which only the round-4 key folds), so a consecutive counter would have seen
    /// runs of at most a few and never fired.  Other actions in between do not
    /// reset it, and the test uses that: the abort still fires when a different
    /// command is interleaved.
    #[test]
    fn the_same_successful_action_repeated_to_its_cap_aborts_the_call() {
        let directory = tempfile::tempdir().expect("a temporary directory");
        let shell = FakeShell::new(0);
        let environment = WriteGuardEnvironment::with_limits(
            Box::new(shell),
            directory.path().to_path_buf(),
            3,
            0,
            ArtifactKind::ProjectFile,
            3,
            150,
            25,
            8,
        );
        futures_lite_block_on(async {
            for attempt in 1..=2 {
                let output = environment
                    .execute(&Action::new("cargo build --offline"), None, None)
                    .await
                    .unwrap_or_else(|error| panic!("attempt {attempt} must run: {error}"));
                assert_eq!(output.returncode, 0);
            }
            // A *different* action in between: the counter is per action, so it
            // neither clears nor advances this one.
            environment
                .execute(&Action::new("cargo check --offline"), None, None)
                .await
                .expect("a different action runs");
            let error = environment
                .execute(&Action::new("cargo build --offline"), None, None)
                .await
                .expect_err("the third run of one action is the abort");
            let message = error.to_string();
            assert!(
                message.contains(FAIL_FAST_MARKER) && message.contains(REPEATED_ACTION_STATUS),
                "{message}"
            );
            assert!(message.contains("cargo build --offline"), "{message}");
            assert!(
                message.contains("succeeded 3 times since this call last wrote"),
                "the abort must say what happened: {message}"
            );
            assert!(
                fail_fast_status(&message) == Some(REPEATED_ACTION_STATUS),
                "{message}"
            );
        });
    }

    /// The control for the test above: **different** actions, each run once, are
    /// progress and must never trip the counter — however many of them there are.
    #[test]
    fn many_different_actions_never_abort() {
        let directory = tempfile::tempdir().expect("a temporary directory");
        let environment = WriteGuardEnvironment::with_limits(
            Box::new(FakeShell::new(0)),
            directory.path().to_path_buf(),
            3,
            0,
            ArtifactKind::ProjectFile,
            3,
            150,
            25,
            8,
        );
        futures_lite_block_on(async {
            for attempt in 1..=20 {
                environment
                    .execute(
                        &Action::new(format!(
                            "cargo build --offline --message-format short {attempt}"
                        )),
                        None,
                        None,
                    )
                    .await
                    .unwrap_or_else(|error| {
                        panic!("attempt {attempt} is a new action and is progress: {error}")
                    });
            }
        });
    }

    /// Round-2 repair (cost batch): a call that never writes is held to a budget
    /// that responds to that fact, and the **first** write buys the whole flat
    /// limit back.
    #[test]
    fn the_step_budget_is_gated_until_the_call_writes_its_artifact() {
        let directory = tempfile::tempdir().expect("a temporary directory");
        let environment = WriteGuardEnvironment::with_limits(
            Box::new(FakeShell::new(0)),
            directory.path().to_path_buf(),
            3,
            0,
            ArtifactKind::ProjectFile,
            0,
            150,
            25,
            8,
        );
        assert_eq!(
            environment.effective_step_budget(),
            25 + 150 / 8,
            "a call that has written nothing gets the wrap-up band plus a step per write it has \
             not made"
        );
        futures_lite_block_on(async {
            let output = environment
                .execute(
                    &Action::new("HOH_WRITE_FILE src/game.rs\nfn main() {}\nHOH_END_WRITE_FILE"),
                    None,
                    None,
                )
                .await
                .expect("the write succeeds");
            assert_eq!(output.returncode, 0);
        });
        assert_eq!(
            environment.effective_step_budget(),
            150,
            "the first project write removes the gate"
        );
    }

    /// The control: `steps_per_artifact = 0` disables the gate, so the flat
    /// limit is exactly what it was before the repair.
    #[test]
    fn a_disabled_progress_gate_leaves_the_flat_step_limit_alone() {
        let directory = tempfile::tempdir().expect("a temporary directory");
        let environment = WriteGuardEnvironment::with_limits(
            Box::new(FakeShell::new(0)),
            directory.path().to_path_buf(),
            3,
            0,
            ArtifactKind::ProjectFile,
            0,
            150,
            25,
            0,
        );
        assert_eq!(environment.effective_step_budget(), 150);
    }

    /// Round-4 repair: the prompt grows **one** budget note, it names the ceiling
    /// and the budget in force separately, and it promises only what the guard
    /// re-reads at every step.  Round 3's failing prompt said "the first
    /// successful project write removes the gate" while the frozen 43 could not
    /// move; this test is the assertion that the note and the enforcement now say
    /// the same thing.
    #[test]
    fn the_effective_budget_is_stated_in_the_prompt_exactly_once() {
        let prompt = "You run under a step budget of 150.";
        let stated = state_the_effective_budget(prompt, 43, 150, 25);
        assert!(
            stated.starts_with(prompt),
            "the prompt is extended, not rewritten"
        );
        assert!(stated.contains("ceiling"), "{stated}");
        assert!(stated.contains("150"), "{stated}");
        assert!(stated.contains("43"), "{stated}");
        assert!(
            stated.contains("re-read at every step"),
            "the note must state the rule the guard really follows: {stated}"
        );
        assert!(stated.contains("wrap-up discipline begins 25"), "{stated}");
        assert_eq!(stated.matches("[budget]").count(), 1, "{stated}");

        // A prompt that states no budget grows nothing.
        let silent = "This prompt states no budget.";
        assert_eq!(state_the_effective_budget(silent, 43, 150, 25), silent);

        // No gate configured: the two numbers are the same and the note must not
        // promise a raise that cannot happen.
        let ungated = state_the_effective_budget(prompt, 150, 150, 25);
        assert!(ungated.contains("enforced step budget is 150"), "{ungated}");
        assert!(!ungated.contains("raises it"), "{ungated}");
    }

    /// Round-4 repair — the defect round 3 measured: the budget is enforced at
    /// the point of work, in the unit the prompt states.  A call that has written
    /// nothing is held to `wrap_up + step_limit / steps_per_artifact` **model
    /// calls**; the actions of the next call are refused; and a write inside the
    /// call raises the budget immediately, so the same call runs on.
    ///
    /// The unit matters and is measured: round 4's first attempt counted actions,
    /// and a Developer call emitting two actions per response was cut after 30
    /// model calls against a stated 43.
    #[test]
    fn the_step_budget_is_re_read_where_it_is_enforced() {
        let directory = tempfile::tempdir().expect("a temporary directory");
        // (a) A call that writes nothing is refused the step **after** its live
        // budget, whatever "43" happened to be when it started.
        let frozen = WriteGuardEnvironment::with_limits(
            Box::new(FakeShell::new(0)),
            directory.path().to_path_buf(),
            0,
            0,
            ArtifactKind::ProjectFile,
            0,
            150,
            25,
            8,
        )
        .sharing_steps(StepCounter::new());
        let gated = 25 + 150 / 8;
        assert_eq!(frozen.effective_step_budget(), gated);
        let frozen_counter = frozen.step_counter.clone().expect("an attached counter");
        futures_lite_block_on(async {
            for call in 1..=gated {
                frozen_counter.increment();
                frozen
                    .execute(&Action::new(format!("echo call {call}")), None, None)
                    .await
                    .unwrap_or_else(|error| panic!("call {call} is inside the budget: {error}"));
            }
            frozen_counter.increment();
            let error = frozen
                .execute(&Action::new("echo one call too many"), None, None)
                .await
                .expect_err("the call after the live budget must be refused");
            let message = error.to_string();
            assert!(
                message.contains(FAIL_FAST_MARKER) && message.contains(STEP_BUDGET_STATUS),
                "{message}"
            );
            assert!(message.contains("live step budget"), "{message}");
        });
        assert_eq!(
            frozen.steps(),
            gated + 1,
            "the budget-plus-one call is billed, then its action is refused"
        );
        // And the counter is the only unit: without one the guard has no step
        // number at all and must not invent one out of its actions.
        let no_counter = WriteGuardEnvironment::with_limits(
            Box::new(FakeShell::new(0)),
            directory.path().to_path_buf(),
            0,
            0,
            ArtifactKind::ProjectFile,
            0,
            150,
            25,
            8,
        );
        futures_lite_block_on(async {
            for step in 1..=200 {
                no_counter
                    .execute(&Action::new(format!("echo unbudgeted {step}")), None, None)
                    .await
                    .unwrap_or_else(|error| {
                        panic!("with no model-call count there is no step budget: {error}")
                    });
            }
        });

        // (b) With a model attached the count is the **model calls**, which is the
        // number the prompt states and mini's own unit.  A response that carries
        // several actions must not consume several steps: that mismatch cut round
        // 4's first attempt after 30 model calls against a stated budget of 43.
        let counted = WriteGuardEnvironment::with_limits(
            Box::new(FakeShell::new(0)),
            directory.path().to_path_buf(),
            0,
            0,
            ArtifactKind::ProjectFile,
            0,
            150,
            25,
            8,
        )
        .sharing_steps(StepCounter::new());
        let counter = counted.step_counter.clone().expect("an attached counter");
        futures_lite_block_on(async {
            for call in 1..=gated {
                counter.increment();
                // Two actions on this one model call.
                for action in 1..=2 {
                    counted
                        .execute(
                            &Action::new(format!("echo call {call} action {action}")),
                            None,
                            None,
                        )
                        .await
                        .unwrap_or_else(|error| {
                            panic!("call {call} is inside the budget: {error}")
                        });
                }
            }
            assert_eq!(
                counted.steps(),
                gated,
                "the count is model calls, not the actions they carried"
            );
            counter.increment();
            let error = counted
                .execute(&Action::new("echo one call too many"), None, None)
                .await
                .expect_err("the call after the live budget must be refused");
            assert!(error.to_string().contains(STEP_BUDGET_STATUS), "{error}");
        });

        // (c) The write raises the live budget **inside the call**, so the steps
        // after it are allowed even though the call has already reached the
        // unwritten budget.  This is the property round 3's implementation did
        // not have.
        let writer = WriteGuardEnvironment::with_limits(
            Box::new(FakeShell::new(0)),
            directory.path().to_path_buf(),
            0,
            0,
            ArtifactKind::ProjectFile,
            0,
            150,
            25,
            8,
        )
        .sharing_steps(StepCounter::new());
        let write_counter = writer.step_counter.clone().expect("an attached counter");
        futures_lite_block_on(async {
            for step in 1..gated {
                write_counter.increment();
                writer
                    .execute(&Action::new(format!("echo step {step}")), None, None)
                    .await
                    .unwrap_or_else(|error| panic!("step {step} is inside the budget: {error}"));
            }
            write_counter.increment();
            let write = writer
                .execute(
                    &Action::new("HOH_WRITE_FILE src/game.rs\nfn main() {}\nHOH_END_WRITE_FILE"),
                    None,
                    None,
                )
                .await
                .expect("the write is inside the unwritten budget");
            assert_eq!(write.returncode, 0, "{}", write.output);
            assert_eq!(
                writer.effective_step_budget(),
                150,
                "the write inside the call must raise the live budget"
            );
            for step in 1..=20 {
                write_counter.increment();
                writer
                    .execute(
                        &Action::new(format!("echo past the old cap {step}")),
                        None,
                        None,
                    )
                    .await
                    .unwrap_or_else(|error| {
                        panic!("the raised budget must be what is enforced: {error}")
                    });
            }
        });
        assert_eq!(writer.steps(), gated + 20);
    }

    /// The control for the test above: `step_limit = 0` means "no limit" in
    /// mini's own terms, and the guard's half must be disabled with it rather
    /// than inventing a budget out of `wrap_up_steps`.
    #[test]
    fn a_zero_step_limit_disables_the_guard_half_of_the_budget() {
        let directory = tempfile::tempdir().expect("a temporary directory");
        let environment = WriteGuardEnvironment::with_limits(
            Box::new(FakeShell::new(0)),
            directory.path().to_path_buf(),
            0,
            0,
            ArtifactKind::ProjectFile,
            0,
            0,
            25,
            8,
        );
        futures_lite_block_on(async {
            for step in 1..=60 {
                environment
                    .execute(&Action::new(format!("echo step {step}")), None, None)
                    .await
                    .unwrap_or_else(|error| panic!("step {step} must not be budgeted: {error}"));
            }
        });
    }

    /// Round-4 repair: the repeated-action counter answers "is this call making
    /// progress?", so a write of the declared artifact restarts it.  Without
    /// this, the legitimate edit/rebuild cadence of every recorded Developer call
    /// (round 2's iteration 2 and all three round-3 calls) accumulates toward a
    /// cap that exists to catch a call which is not producing anything.
    #[test]
    fn a_write_of_the_artifact_restarts_the_repeated_action_counter() {
        let directory = tempfile::tempdir().expect("a temporary directory");
        let environment = WriteGuardEnvironment::with_limits(
            Box::new(FakeShell::new(0)),
            directory.path().to_path_buf(),
            0,
            0,
            ArtifactKind::ProjectFile,
            3,
            150,
            25,
            8,
        );
        futures_lite_block_on(async {
            for attempt in 1..=2 {
                environment
                    .execute(&Action::new("cargo build --offline"), None, None)
                    .await
                    .unwrap_or_else(|error| panic!("build {attempt}: {error}"));
            }
            environment
                .execute(
                    &Action::new("HOH_WRITE_FILE src/game.rs\nfn main() {}\nHOH_END_WRITE_FILE"),
                    None,
                    None,
                )
                .await
                .expect("the write");
            for attempt in 1..=2 {
                environment
                    .execute(&Action::new("cargo build --offline"), None, None)
                    .await
                    .unwrap_or_else(|error| {
                        panic!("build {attempt} after the write must be progress: {error}")
                    });
            }
            let error = environment
                .execute(&Action::new("cargo build --offline"), None, None)
                .await
                .expect_err("the third build after the write is the abort");
            assert!(
                error
                    .to_string()
                    .contains("succeeded 3 times since this call last wrote"),
                "{error}"
            );
        });
    }

    /// The control: a **scratch** write is not progress, so it must not restart
    /// the counter — otherwise a call could evade the tripwire by littering
    /// `.hoh/scratch`.
    #[test]
    fn a_scratch_write_does_not_restart_the_repeated_action_counter() {
        let directory = tempfile::tempdir().expect("a temporary directory");
        let environment = WriteGuardEnvironment::with_limits(
            Box::new(FakeShell::new(0)),
            directory.path().to_path_buf(),
            0,
            0,
            ArtifactKind::ProjectFile,
            3,
            150,
            25,
            8,
        );
        futures_lite_block_on(async {
            for attempt in 1..=2 {
                environment
                    .execute(&Action::new("cargo build --offline"), None, None)
                    .await
                    .unwrap_or_else(|error| panic!("build {attempt}: {error}"));
            }
            environment
                .execute(
                    &Action::new(&render_write(".hoh/scratch/probe.txt", "n")),
                    None,
                    None,
                )
                .await
                .expect("the scratch write");
            let error = environment
                .execute(&Action::new("cargo build --offline"), None, None)
                .await
                .expect_err("the third build is still the abort");
            assert!(
                error.to_string().contains(REPEATED_ACTION_STATUS),
                "{error}"
            );
        });
    }

    /// Round-4 repair: the action key must fold spellings that do not change the
    /// action.  Round 3's iteration 1 spelled the same build three ways with
    /// `| tail -N`, and the old key counted each spelling separately — the reason
    /// the tripwire never came near its cap on a real call.
    #[test]
    fn the_same_action_spelled_with_a_filter_or_a_redirection_is_one_action() {
        for spelling in [
            "cargo build --offline",
            "cargo build --offline 2>&1",
            "cargo build --offline 2>&1 | tail -5 &",
            "cargo build --offline 2>&1 | tail -20",
            "cargo build --offline | findstr error",
            "cargo build --offline | more",
            "cargo build --offline >nul",
            "cd /d C:\\proj && cargo build --offline 2>&1 & echo BUILD_EXIT=%ERRORLEVEL%",
        ] {
            assert_eq!(
                repeated_action_key(spelling),
                "cargo build --offline",
                "`{spelling}` must fold to the action it is"
            );
        }
        // The control: a different flag or subcommand is a different action.
        assert_ne!(
            repeated_action_key("cargo build --offline"),
            repeated_action_key("cargo build --release")
        );
        assert_ne!(
            repeated_action_key("cargo build --offline"),
            repeated_action_key("cargo test --offline")
        );
    }

    #[test]
    fn a_write_directive_writes_the_file_byte_for_byte() {
        let directory = tempfile::tempdir().expect("a temporary view");
        let content = "fn main() {\n    let s = \"100% $HOME (x) C:\\\\y\";\n}\n";
        let output = run(&render_write("src/game.rs", content), directory.path());
        assert_eq!(output.returncode, 0, "{}", output.output);
        let written = std::fs::read(directory.path().join("src/game.rs")).expect("the file");
        assert_eq!(written, content.as_bytes());
        assert!(output.output.contains("wrote"));
    }

    #[test]
    fn a_read_directive_returns_the_bytes_unchanged() {
        let directory = tempfile::tempdir().expect("a temporary view");
        std::fs::create_dir_all(directory.path().join(".hoh")).unwrap();
        let content = "a\r\nb%c$d\\e(f)\"g\"\r\n";
        std::fs::write(directory.path().join(".hoh/plan.md"), content).unwrap();
        let output = run("HOH_READ_FILE .hoh/plan.md", directory.path());
        assert_eq!(output.returncode, 0);
        assert_eq!(output.output, content);
    }

    #[test]
    fn a_directive_never_reaches_the_shell() {
        let directory = tempfile::tempdir().expect("a temporary view");
        let shell = FakeShell::new(0);
        let seen = std::sync::Arc::clone(&shell.seen);
        let environment =
            WriteGuardEnvironment::new(Box::new(shell), directory.path().to_path_buf(), 3, 0);
        futures_lite_block_on(async {
            environment
                .execute(&Action::new(&render_write("a.txt", "here\n")), None, None)
                .await
                .expect("the write");
            environment
                .execute(&Action::new("HOH_READ_FILE a.txt"), None, None)
                .await
                .expect("the read");
            environment
                .execute(&Action::new("cargo build --offline"), None, None)
                .await
                .expect("an ordinary command");
        });
        assert_eq!(
            seen.lock().expect("the shell log").as_slice(),
            ["cargo build --offline"],
            "the shell must see every non-directive and no directive"
        );
    }

    #[test]
    fn a_write_outside_the_view_is_refused_and_nothing_is_written() {
        let directory = tempfile::tempdir().expect("a temporary view");
        for path in ["../escape.rs", "C:\\absolute.rs", "..\\up.rs"] {
            let output = run(&render_write(path, "x"), directory.path());
            assert_eq!(output.returncode, 1, "{path} must be refused");
            assert!(output.output.contains("working directory"), "{path}");
        }
        assert!(!directory
            .path()
            .parent()
            .unwrap()
            .join("escape.rs")
            .exists());
    }

    #[test]
    fn a_malformed_directive_is_explained_and_never_run() {
        let directory = tempfile::tempdir().expect("a temporary view");
        let output = run("HOH_WRITE_FILE a.rs\nunterminated", directory.path());
        assert_eq!(output.returncode, 1);
        assert!(
            output.output.contains("HOH_END_WRITE_FILE"),
            "{}",
            output.output
        );
        assert!(output.output.contains("not closed"), "{}", output.output);
    }

    #[test]
    fn a_project_write_marks_the_artifact_and_a_scratch_write_does_not() {
        let directory = tempfile::tempdir().expect("a temporary view");
        let environment = guard(directory.path(), 3, 0);
        futures_lite_block_on(async {
            environment
                .execute(
                    &Action::new(&render_write(".hoh/scratch/probe.txt", "n")),
                    None,
                    None,
                )
                .await
                .expect("the scratch write");
        });
        assert!(
            !environment.artifact_written(),
            "scratch is not the artifact"
        );
        futures_lite_block_on(async {
            environment
                .execute(&Action::new(&render_write("src/game.rs", "n")), None, None)
                .await
                .expect("the project write");
        });
        assert!(environment.artifact_written());
        assert_eq!(environment.writes(), 2);
    }

    /// The Planner's and the Tester's artifacts live under `.hoh/**`, so for them
    /// a `.hoh` write **is** the artifact.  Without this, their budget could never
    /// be disarmed and a role that had already written its plan would be aborted
    /// for not writing one.
    #[test]
    fn a_planner_or_tester_artifact_disarms_the_budget_through_hoh() {
        let directory = tempfile::tempdir().expect("a temporary view");
        let environment = WriteGuardEnvironment::with_artifact_kind(
            Box::new(FakeShell::new(0)),
            directory.path().to_path_buf(),
            3,
            1,
            ArtifactKind::AnyFile,
        );
        futures_lite_block_on(async {
            environment
                .execute(
                    &Action::new(&render_write(".hoh/plan.md", "# plan\n")),
                    None,
                    None,
                )
                .await
                .expect("the plan write");
        });
        assert!(environment.artifact_written());
        std::thread::sleep(Duration::from_millis(1_050));
        assert!(environment.budget_exceeded().is_none());
        // The Developer's kind is the project, decided from the role itself.
        assert_eq!(
            ArtifactKind::for_role(crate::model::Role::Developer),
            ArtifactKind::ProjectFile
        );
        assert_eq!(
            ArtifactKind::for_role(crate::model::Role::Planner),
            ArtifactKind::AnyFile
        );
        assert_eq!(
            ArtifactKind::for_role(crate::model::Role::Tester),
            ArtifactKind::AnyFile
        );
    }

    #[test]
    fn the_same_failing_action_aborts_the_call_per_action_not_consecutively() {
        let directory = tempfile::tempdir().expect("a temporary view");
        // The shell fails, and there is a *successful* action interleaved — which
        // is exactly what reset mini's consecutive-format-error tripwire.
        let environment = guard_with(directory.path(), 1, 3, 0);
        let failing = Action::new("cat .hoh/TASK.md");
        let ok = guard_with(directory.path(), 0, 3, 0);
        let outcome = futures_lite_block_on(async {
            let mut last = Ok(());
            for _ in 0..3 {
                last = environment.execute(&failing, None, None).await.map(|_| ());
                let _ = ok.execute(&Action::new("echo hi"), None, None).await;
            }
            last
        });
        let error = outcome.expect_err("the third failure of one action must abort");
        assert!(error.to_string().contains(FAIL_FAST_MARKER), "{error}");
        assert!(error.to_string().contains("cat .hoh/TASK.md"), "{error}");
        assert_eq!(
            fail_fast_status(&error.to_string()),
            Some(REPEATED_ACTION_STATUS)
        );
    }

    #[test]
    fn a_success_of_the_same_action_clears_its_own_counter() {
        let directory = tempfile::tempdir().expect("a temporary view");
        let environment = guard(directory.path(), 2, 0);
        let flaky = Action::new("flaky command");
        futures_lite_block_on(async {
            // The fake shell always succeeds, so a success must clear the counter
            // even after a failure was recorded by the same command.
            environment
                .state
                .lock()
                .unwrap()
                .failures
                .insert("flaky command".to_string(), 1);
            environment
                .execute(&flaky, None, None)
                .await
                .expect("a success must not abort");
        });
        assert!(!environment
            .state
            .lock()
            .unwrap()
            .failures
            .contains_key("flaky command"));
    }

    #[test]
    fn the_artifact_budget_aborts_a_call_that_never_writes() {
        let directory = tempfile::tempdir().expect("a temporary view");
        // Zero means "no budget", and a project write disarms it.
        let unbudgeted = guard_with(directory.path(), 0, 3, 0);
        assert!(unbudgeted.budget_exceeded().is_none());

        let environment = guard_with(directory.path(), 0, 3, 1);
        std::thread::sleep(Duration::from_millis(1_050));
        let error = futures_lite_block_on(async {
            environment
                .execute(&Action::new("cargo build --offline"), None, None)
                .await
                .map(|_| ())
                .expect_err("the budget must abort the call")
        });
        assert!(error.to_string().contains(FAIL_FAST_MARKER), "{error}");
        assert_eq!(
            fail_fast_status(&error.to_string()),
            Some(ARTIFACT_BUDGET_STATUS)
        );
        assert!(
            error.to_string().contains("artifact-write budget"),
            "{error}"
        );
        assert!(error.to_string().contains("HOH_WRITE_FILE"), "{error}");
    }

    #[test]
    fn a_project_write_disarms_the_artifact_budget() {
        let directory = tempfile::tempdir().expect("a temporary view");
        let environment = guard_with(directory.path(), 0, 3, 1);
        futures_lite_block_on(async {
            environment
                .execute(&Action::new(&render_write("src/game.rs", "x")), None, None)
                .await
                .expect("the write");
        });
        std::thread::sleep(Duration::from_millis(1_050));
        assert!(environment.budget_exceeded().is_none());
    }

    /// The sentinel is the only channel the status has across mini's opaque
    /// `AgentError`, so its recovery must be exact.
    #[test]
    fn the_fail_fast_status_is_recoverable_from_the_message_alone() {
        let repeated = FailFast::RepeatedAction {
            command: "cat x".to_string(),
            failures: 3,
        };
        assert_eq!(
            fail_fast_status(&repeated.message()),
            Some(REPEATED_ACTION_STATUS)
        );
        let budget = FailFast::ArtifactBudget {
            elapsed_seconds: 61,
            budget_seconds: 60,
        };
        assert_eq!(
            fail_fast_status(&budget.message()),
            Some(ARTIFACT_BUDGET_STATUS)
        );
        assert_eq!(fail_fast_status("llm-connector chat request failed"), None);
        assert_eq!(
            fail_fast_status("a command that mentions HOH_FAIL_FAST"),
            None
        );
    }
}
