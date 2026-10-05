//! Round-2 cost batch, re-measured by the round-4 repair — what the
//! repeated-success tripwire and the progress-gated step budget would have done
//! to the **recorded** Developer calls.
//!
//! The two mechanisms that attack the cost are:
//!
//! 1. `harness::guard`'s repeated-**success** tripwire: the same action
//!    succeeding `agent.max_repeated_actions` times **since the call last wrote
//!    the artifact it declares** aborts the call.  Round 2's Developer ended
//!    iteration 1 with about seventy calls of one verification loop and every one
//!    of them returned 0, so no older counter could see it.
//! 2. the progress-gated step budget: a call that has written nothing gets
//!    `wrap_up_steps + step_limit / steps_per_artifact` steps, and the guard
//!    re-reads that value at every step (round-4 repair: it used to be frozen
//!    into the agent before the call started).
//!
//! This file measures both against the recorded trajectories.  It does **not**
//! claim to be a run: the tripwire's own firing is pinned by
//! `harness::guard::tests::the_same_successful_action_repeated_to_its_cap_aborts_the_call`
//! and the live budget by
//! `harness::guard::tests::the_step_budget_is_re_read_where_it_is_enforced`.
//!
//! The round-4 repair changed two things about the measurement, and both are
//! stated with their numbers rather than asserted:
//!
//! * the **action key** now folds trailing output filters (`| tail -N` as well as
//!   `| more` / `| findstr …`) and trailing redirections (`2>&1`, `>nul`).  Round
//!   3's iteration 1 spelled nine identical builds three ways and the old key
//!   counted them 3 + 3 + 3;
//! * the counter **restarts on a counted project write**, because a counter that
//!   runs across one cannot tell "this call is not producing" from "this call is
//!   editing and rebuilding" — round 2's iteration 2 (14 → 15 repeats, a
//!   legitimate cadence) and all three round-3 Developer calls are the evidence.
//!
//! The trajectories are recorded evidence and are read, never written.

use std::collections::BTreeMap;
use std::path::{Path, PathBuf};

use hof_rs::config::AgentLimits;
use hof_rs::harness::directive::{self, Directive};
use hof_rs::harness::guard::{
    output_digest, repeated_action_key, ArtifactKind, FAIL_FAST_MARKER, REPEATED_ACTION_STATUS,
    STEP_BUDGET_STATUS,
};
use hof_rs::model::Role;

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
}

fn trajectory(directory: &str, iteration: &str) -> Option<PathBuf> {
    let path = repo_root()
        .join("runs")
        .join(directory)
        .join(iteration)
        .join("traj/developer.attempt1.json");
    path.is_file().then_some(path)
}

fn read_json(path: &Path) -> serde_json::Value {
    let bytes = std::fs::read(path).unwrap_or_else(|error| panic!("{}: {error}", path.display()));
    serde_json::from_slice(&bytes).unwrap_or_else(|error| panic!("{}: {error}", path.display()))
}

/// One recorded tool call: the normalised action key, whether it is a
/// successful write of the role's declared artifact, and a fingerprint of the
/// result the action produced.
struct RecordedCall {
    key: String,
    /// A directive write to a path the guard counts as the Developer's artifact.
    /// The rule is the guard's own ([`ArtifactKind::counts`]), not a copy: a test
    /// that decides for itself which writes are progress can prove anything.
    is_artifact_write: bool,
    /// The **guard's own** fingerprint of the result the action produced
    /// ([`hof_rs::harness::guard::output_digest`] of the observation's
    /// `<output>` body — the string `record_success` is handed).  The round-5
    /// tripwire counts a repetition only when this is **unchanged**.
    ///
    /// AC-13: this used to be the observation's byte *length*, which counts two
    /// different results of equal length as identical; the guard does not.
    observation_digest: String,
    succeeded: bool,
}

/// The `<output>…</output>` body a tool observation carries, which is the string
/// the guard digests (`WriteGuardEnvironment` passes `Output::output`, and the
/// trajectory stores it wrapped).
fn observation_body(content: &str) -> &str {
    match (content.find("<output>"), content.rfind("</output>")) {
        (Some(start), Some(end)) if end > start => &content[start + "<output>".len()..end],
        _ => content,
    }
}

/// Every tool call in a recorded trajectory, in order, paired with the **API
/// call index** it was issued on.
///
/// Two facts about the recorded format are load-bearing, and both were measured
/// rather than assumed (see `.spec/bevy/TRUST-REPORT.md`): a message carrying a
/// `usage` block is a **model call** (in the recorded ApiMode::ToolCalls
/// trajectories the tool-call messages are `assistant` and the tool-free
/// responses are `user`, but the runtime's own usage extractor counts every
/// message with a usage block, so that is the population this test uses), and a
/// tool call is issued **on** such a message.  The index used to look up a
/// prompt-token cost and the index used to decide where an abort lands are
/// therefore the same coordinate space.
fn recorded_calls(trajectory: &serde_json::Value) -> (Vec<(usize, RecordedCall)>, usize) {
    let kind = ArtifactKind::for_role(Role::Developer);
    let mut calls = Vec::new();
    let mut api_index = 0usize;
    for (position, message) in trajectory["messages"]
        .as_array()
        .cloned()
        .unwrap_or_default()
        .into_iter()
        .enumerate()
    {
        if message["extra"]["response"]["usage"].is_null() {
            continue;
        }
        api_index += 1;
        let actions = message["tool_calls"]
            .as_array()
            .cloned()
            .unwrap_or_default();
        // The observations that follow this response, one per action, in order.
        let all = trajectory["messages"]
            .as_array()
            .cloned()
            .unwrap_or_default();
        let mut observations: Vec<String> = Vec::new();
        for next in all.iter().skip(position + 1) {
            if next["role"] != "tool" || observations.len() >= actions.len() {
                break;
            }
            observations.push(next["content"].as_str().unwrap_or("").to_string());
        }
        for (index, call) in actions.iter().enumerate() {
            let arguments = call["function"]["arguments"]
                .as_str()
                .or_else(|| call["arguments"].as_str())
                .unwrap_or("");
            let command = serde_json::from_str::<serde_json::Value>(arguments)
                .ok()
                .and_then(|parsed| {
                    parsed
                        .get("command")
                        .or_else(|| parsed.get("cmd"))
                        .and_then(|value| value.as_str())
                        .map(ToOwned::to_owned)
                })
                .unwrap_or_else(|| arguments.to_string());
            let is_artifact_write = match directive::parse_directive(&command) {
                Directive::Write { path, .. } => kind.counts(&path),
                _ => false,
            };
            let observation = observations.get(index).cloned().unwrap_or_default();
            let succeeded = observation
                .split_once("<returncode>")
                .and_then(|(_, rest)| rest.split_once("</returncode>"))
                .and_then(|(code, _)| code.trim().parse::<i32>().ok())
                == Some(0);
            calls.push((
                api_index,
                RecordedCall {
                    key: repeated_action_key(&command),
                    is_artifact_write,
                    observation_digest: output_digest(observation_body(&observation)),
                    succeeded,
                },
            ));
        }
    }
    (calls, api_index)
}

/// The prompt-token cost of each recorded API call, indexed from 1.
fn prompt_tokens_by_call(trajectory: &serde_json::Value) -> BTreeMap<usize, u64> {
    let mut map = BTreeMap::new();
    let mut api_index = 0usize;
    for message in trajectory["messages"]
        .as_array()
        .cloned()
        .unwrap_or_default()
    {
        let usage = &message["extra"]["response"]["usage"];
        if let Some(tokens) = usage["prompt_tokens"].as_u64() {
            api_index += 1;
            map.insert(api_index, tokens);
        }
    }
    map
}

/// The highest count any one action reaches **in any window since a counted
/// project write**, and the API call index at which it first reaches `cap`.
///
/// The count is a total per action within a window, not a consecutive run: round
/// 2's loop spelled itself with several `| more` / `| findstr …` / `& echo …`
/// variants, so a consecutive counter saw runs of at most three.  The window
/// restarts at every counted write — that is the guard's round-4 rule.
///
/// The figure returned is the **maximum over all the windows**, not the last
/// one's: a call that grinds, gets cleared by a write and then ends quietly must
/// not be measured as "1 repeat".  (That was a real defect in this file's first
/// round-4 form: round 2's iteration 1 printed a window maximum of 1 while its
/// own `abort_at` said a window had reached the cap — two figures from one
/// measurement that disagreed.)
fn repeats_since_last_write(
    calls: &[(usize, RecordedCall)],
    cap: usize,
) -> (Vec<(String, usize)>, Option<usize>) {
    let mut counts: BTreeMap<&str, usize> = BTreeMap::new();
    let mut best: BTreeMap<String, usize> = BTreeMap::new();
    let mut abort_at = None;
    for (api_index, call) in calls {
        if call.is_artifact_write {
            counts.clear();
            continue;
        }
        let count = {
            let entry = counts.entry(call.key.as_str()).or_insert(0);
            *entry += 1;
            *entry
        };
        let entry = best.entry(call.key.clone()).or_insert(0);
        *entry = (*entry).max(count);
        if count >= cap && abort_at.is_none() {
            abort_at = Some(*api_index);
        }
    }
    (top_repeats(&best), abort_at)
}

/// The round-5 tripwire's own count: one action's consecutive successes whose
/// **result was byte-identical**, since the call last wrote its artifact.
///
/// It is the same window as [`repeats_since_last_write`] with the round-5 rule
/// applied, so the difference between the two columns is exactly what the
/// semantics change bought.  The comparison is the guard's own
/// [`output_digest`] (AC-13), not a byte-length proxy.
fn identical_repeats_since_last_write(
    calls: &[(usize, RecordedCall)],
    cap: usize,
) -> (Vec<(String, usize)>, Option<usize>) {
    let mut runs: BTreeMap<String, (String, usize)> = BTreeMap::new();
    let mut best: BTreeMap<String, usize> = BTreeMap::new();
    let mut abort_at = None;
    for (api_index, call) in calls {
        if call.is_artifact_write {
            runs.clear();
            continue;
        }
        if !call.succeeded {
            continue;
        }
        let run = runs
            .entry(call.key.clone())
            .or_insert((String::new(), 0usize));
        run.1 = if run.0 == call.observation_digest {
            run.1 + 1
        } else {
            1
        };
        run.0 = call.observation_digest.clone();
        let count = run.1;
        let entry = best.entry(call.key.clone()).or_insert(0);
        *entry = (*entry).max(count);
        if count >= cap && abort_at.is_none() {
            abort_at = Some(*api_index);
        }
    }
    (top_repeats(&best), abort_at)
}

/// The same count **without** the restart, so the difference the round-4 repair
/// makes is a measured number rather than a claim.
fn repeats_in_the_whole_call(calls: &[(usize, RecordedCall)]) -> Vec<(String, usize)> {
    let mut counts: BTreeMap<String, usize> = BTreeMap::new();
    for (_, call) in calls {
        *counts.entry(call.key.clone()).or_insert(0) += 1;
    }
    top_repeats(&counts)
}

fn top_repeats(counts: &BTreeMap<String, usize>) -> Vec<(String, usize)> {
    let mut top: Vec<(String, usize)> = counts
        .iter()
        .map(|(key, count)| (key.clone(), *count))
        .collect();
    top.sort_by(|left, right| right.1.cmp(&left.1).then(left.0.cmp(&right.0)));
    top.truncate(4);
    top
}

/// One trajectory, measured: how far the run got and what a cap would have cost.
#[derive(Debug)]
struct Projection {
    tool_calls: usize,
    api_calls: usize,
    counted_writes: usize,
    observed_prompt_tokens: u64,
    abort_at: Option<usize>,
    capped_prompt_tokens: u64,
    /// The highest count one action reached in any post-write window.
    most_repeated_window: Vec<(String, usize)>,
    most_repeated_whole_call: Vec<(String, usize)>,
    /// Round-5: the same window counted by **identical results only**.
    most_identical_window: Vec<(String, usize)>,
    identical_abort_at: Option<usize>,
    identical_capped_prompt_tokens: u64,
}

fn project(path: &Path, cap: usize) -> Projection {
    let trajectory = read_json(path);
    let (calls, api_calls) = recorded_calls(&trajectory);
    let usage = prompt_tokens_by_call(&trajectory);
    let observed: u64 = usage.values().sum();
    let (most_repeated_window, abort_at) = repeats_since_last_write(&calls, cap);
    let (most_identical_window, identical_abort_at) =
        identical_repeats_since_last_write(&calls, cap);
    let capped: u64 = usage
        .iter()
        .filter(|(index, _)| match abort_at {
            Some(limit) => **index <= limit,
            None => true,
        })
        .map(|(_, tokens)| *tokens)
        .sum();
    let identical_capped: u64 = usage
        .iter()
        .filter(|(index, _)| match identical_abort_at {
            Some(limit) => **index <= limit,
            None => true,
        })
        .map(|(_, tokens)| *tokens)
        .sum();
    Projection {
        tool_calls: calls.len(),
        api_calls,
        counted_writes: calls
            .iter()
            .filter(|(_, call)| call.is_artifact_write)
            .count(),
        observed_prompt_tokens: observed,
        abort_at,
        capped_prompt_tokens: capped,
        most_repeated_window,
        most_repeated_whole_call: repeats_in_the_whole_call(&calls),
        most_identical_window,
        identical_abort_at,
        identical_capped_prompt_tokens: identical_capped,
    }
}

/// The recorded round-2 Developer calls exist and really are the grind the
/// report describes: the same action repeated far past the new cap.  If this
/// stops holding, the projections below become vacuous and must be revisited
/// rather than silently passing.
#[test]
fn the_recorded_round_two_developer_really_repeats_one_action_past_the_cap() {
    let path =
        trajectory("round2", "iter-1").expect("the recorded iteration-1 developer trajectory");
    let projection = project(&path, 15);
    assert!(
        projection.tool_calls > 100,
        "the recorded trajectory is the 125-call grind: {projection:?}"
    );
    let (action, count) = projection
        .most_repeated_whole_call
        .first()
        .expect("a recorded action")
        .clone();
    assert!(
        count >= 8,
        "one action must repeat at least to the cap; the top repeats are {:?}",
        projection.most_repeated_whole_call
    );
    assert!(
        action.contains("cargo build"),
        "the repeated action is the verification loop: {action}"
    );
}

/// Round-4 measured the tripwire's window count on the recorded grind; round 5
/// re-measured the same window under the rule that tripwire now implements (a
/// repetition is only a repetition when the **result is unchanged**).  Both
/// numbers are pinned, because the difference between them is the whole reason
/// the semantics changed: the recorded loop's results kept changing, so what the
/// old counter called 22 repeats the new one correctly calls a run of measurements.
///
/// The projection is arithmetic over the recorded per-call prompt tokens, not a
/// claim about a real run, and the arithmetic is printed so the report can quote
/// it.
#[test]
fn the_repeated_success_tripwire_fires_on_the_recorded_grind() {
    let path =
        trajectory("round2", "iter-1").expect("the recorded iteration-1 developer trajectory");
    let projection = project(&path, 15);
    println!(
        "iter-1: api_calls={} tool_calls={} observed_prompt_tokens={} window_max={:?} \
         whole_max={:?} abort_at={:?} capped_prompt_tokens={} identical_max={:?} \
         identical_abort_at={:?} identical_capped={}",
        projection.api_calls,
        projection.tool_calls,
        projection.observed_prompt_tokens,
        projection.most_repeated_window.first(),
        projection.most_repeated_whole_call.first(),
        projection.abort_at,
        projection.capped_prompt_tokens,
        projection.most_identical_window.first(),
        projection.identical_abort_at,
        projection.identical_capped_prompt_tokens,
    );
    // Round-5: the same window under the rule the tripwire now implements.  The
    // recorded loop's results change on every run (`cargo build` prints a
    // different "Finished in" line), so the honest count of *identical* results is
    // 2 — and that is why the old rule fired on work that was still producing
    // something, and why it no longer does.  The curve's two real firing shapes
    // (a command repeated with one unchanged answer) are pinned by the guard's
    // own tests, which is where a rule belongs.
    assert!(
        projection
            .most_identical_window
            .first()
            .map(|(_, count)| *count)
            .unwrap_or(0)
            <= 2,
        "the recorded grind's results were not byte-identical, so the round-5 counter must not \
         count them as repetitions: {:?}",
        projection.most_identical_window
    );
    assert!(
        projection.identical_abort_at.is_none(),
        "and it must therefore not have aborted that call: {projection:?}"
    );
    assert_eq!(
        projection.api_calls, 150,
        "iteration 1 recorded 150 model calls: {projection:?}"
    );
    assert_eq!(
        projection.observed_prompt_tokens, 11_108_856,
        "the recorded iteration-1 prompt spend is the report's 11,108,856"
    );
    let abort_at = projection
        .abort_at
        .expect("the recorded grind reaches the cap in the window after its last write");
    // The two counts, pinned.  The window figure (22) is the one the guard keeps
    // and the one the cap of 15 is derived against; the whole-call figure (54) is
    // what the same folded key would count without the write-restart, and it is
    // the reason the restart is a choice rather than an accounting fix.
    assert_eq!(
        projection
            .most_repeated_window
            .first()
            .map(|(_, count)| *count),
        Some(22),
        "the post-write window maximum is the measured 22: {:?}",
        projection.most_repeated_window
    );
    assert_eq!(
        projection
            .most_repeated_whole_call
            .first()
            .map(|(_, count)| *count),
        Some(54),
        "the whole-call maximum under the folded key is the measured 54: {:?}",
        projection.most_repeated_whole_call
    );
    let fraction =
        projection.capped_prompt_tokens as f64 / projection.observed_prompt_tokens.max(1) as f64;
    // The bound is the **measured** one and it is deliberately not loose: the
    // round-4 counter fires late (the recorded labour is front-loaded with real
    // edits, and the counter restarts at every one), so the honest statement is
    // "it fires, and it keeps most of the call".  A bound of "less than 95%"
    // would pass even if the mechanism saved nothing, which is the failure mode
    // this project exists to avoid.  Setting the window here means a future
    // change to the key or the window must re-derive the number.
    assert!(
        (0.75..0.80).contains(&fraction),
        "an abort at call {abort_at} of {} would have kept {:.1}% of the observed {} prompt tokens \
         ({:.0} of them); the round-4 arithmetic says 75-80%, and a different figure means the \
         counter moved and this projection must be re-read rather than relaxed",
        projection.api_calls,
        fraction * 100.0,
        projection.observed_prompt_tokens,
        projection.capped_prompt_tokens as f64
    );
}

/// Round-4's own Developer calls, measured with the repository's key: what the
/// abort of criterion `C10` actually counted, and whether the repeats it saw
/// were *identical repeats* (an unproductive loop) or repeats whose result
/// changed (a build/test cycle that was still producing information).
#[test]
fn the_round_four_developer_repeats_are_measured_and_not_assumed() {
    let mut measured = 0usize;
    for iteration in ["iter-1", "iter-2", "iter-3"] {
        let Some(path) = trajectory("round4", iteration) else {
            continue;
        };
        measured += 1;
        let projection = project(&path, 15);
        println!(
            "{iteration}: api_calls={} tool_calls={} writes={} window_max={:?} whole_max={:?} \
             abort_at={:?} capped={} identical_max={:?} identical_abort_at={:?} identical_capped={}",
            projection.api_calls,
            projection.tool_calls,
            projection.counted_writes,
            projection.most_repeated_window.first(),
            projection.most_repeated_whole_call.first(),
            projection.abort_at,
            projection.capped_prompt_tokens,
            projection.most_identical_window.first(),
            projection.identical_abort_at,
            projection.identical_capped_prompt_tokens,
        );
        assert!(
            projection.api_calls > 40,
            "{iteration} is one of the recorded Developer calls: {projection:?}"
        );
    }
    assert_eq!(
        measured, 3,
        "the three round-4 Developer calls are the evidence"
    );
}

/// The progress gate's arithmetic is a fact about the configuration, and it is
/// what makes a call that has written nothing unable to spend 150 steps.
#[test]
fn the_progress_gate_shortens_a_call_that_has_written_nothing() {
    let limits = AgentLimits::default();
    assert_eq!(limits.step_limit, 150);
    assert_eq!(limits.wrap_up_steps, 25);
    assert_eq!(limits.steps_per_artifact, 8);
    assert_eq!(limits.effective_step_limit(false), 43);
    assert_eq!(limits.effective_step_limit(true), 150);
}

/// The **upper bound of the cap, measured**: on the one recorded call the
/// tripwire must not hurt — round 2's iteration 2, whose builds interleave edits
/// and whose last build the artifact survived — the same action reaches **7** in a
/// post-write window.  `agent.max_repeated_actions = 15` is therefore more than
/// twice that figure, and it is far below the grind's **22** (measured by the same
/// key over the same windows; `ROUND-2-REPORT.md`'s 14 and the old whole-call 39
/// are what the old, narrower action key measured, and the round-4 key counts 22
/// in a window and 54 over the whole call — the numbers this test pins).
#[test]
fn the_recorded_engineering_call_defines_the_upper_bound_of_the_cap() {
    let Some(path) = trajectory("round2", "iter-2") else {
        // The evidence directory is gitignored; a machine without it still runs
        // the gate, and the report says where the figure came from.
        return;
    };
    let projection = project(&path, 15);
    println!(
        "iter-2: api_calls={} tool_calls={} window_max={:?} whole_max={:?} abort_at={:?}",
        projection.api_calls,
        projection.tool_calls,
        projection.most_repeated_window.first(),
        projection.most_repeated_whole_call.first(),
        projection.abort_at
    );
    assert!(
        projection.abort_at.is_none(),
        "iteration 2 must stay inside the cap, or the cap is below the evidence: {:?}",
        projection.most_repeated_window
    );
    let (action, count) = projection
        .most_repeated_window
        .first()
        .cloned()
        .expect("an action");
    assert_eq!(
        count, 7,
        "the measured upper bound in any post-write window is 7 ({action}); if this figure moves, \
         `agent.max_repeated_actions` must be re-derived rather than left as a guess"
    );
    assert!(
        action.contains("cargo build"),
        "the action at the cap's boundary is the legitimate rebuild: {action}"
    );
}

/// Round 3 is the round the tripwire was silent in, and this is **why**, in the
/// round-4 measurement.  The test prints the two maxima per call — the
/// current-window (the counter the guard keeps) and the whole-call (the counter
/// the old, narrower key kept) — because the difference between them is the whole
/// argument for the round-4 accounting, and a report that quotes one of them must
/// be able to see which one it is quoting.
///
/// What the numbers say, and what the report repeats: the old key left
/// `| tail -N` out of its fold, so round 3's iteration 1 — **15** `cargo build`
/// tool calls in **12 distinct spellings**, 14 of them carrying a `| tail`
/// filter — was counted as several small actions of three.  Folding it makes the
/// whole-call figure 15, exactly the cap; the write-restart keeps the counter the
/// guard enforces at the much smaller window maximum (5), which is why the
/// tripwire stayed silent in round 3 and why "silent" is the honest reading of
/// that number rather than a success.
#[test]
fn the_round_three_developer_calls_were_below_the_cap_for_a_measured_reason() {
    let mut measured = 0usize;
    for iteration in ["iter-1", "iter-2", "iter-3"] {
        let Some(path) = trajectory("round3", iteration) else {
            continue;
        };
        measured += 1;
        let projection = project(&path, 15);
        println!(
            "{iteration}: api_calls={} tool_calls={} window_max={:?} whole_max={:?} abort_at={:?}",
            projection.api_calls,
            projection.tool_calls,
            projection.most_repeated_window.first(),
            projection.most_repeated_whole_call.first(),
            projection.abort_at
        );
        assert_eq!(projection.api_calls, 43, "{iteration}: {projection:?}");
        assert!(
            projection.abort_at.is_none(),
            "{iteration} must stay inside the cap: {:?}",
            projection.most_repeated_window
        );
        let (_, window) = projection
            .most_repeated_window
            .first()
            .cloned()
            .expect("an action");
        let (_, whole) = projection
            .most_repeated_whole_call
            .first()
            .cloned()
            .expect("an action");
        assert!(
            window <= 5,
            "{iteration}: the post-write window maximum must be at most 5, got {window}"
        );
        assert!(
            whole <= 15,
            "{iteration}: the whole-call maximum under the folded key must be at most 15 — the cap \
             itself, which iteration 1 reaches exactly — got {whole}"
        );
    }
    if measured > 0 {
        assert_eq!(
            measured, 3,
            "the three round-3 Developer calls are the evidence"
        );
    }
}

/// AC-13: the round-5 counter compares the guard's **own digest**, not the
/// observation's byte length.  Two results of equal length but different bytes
/// are two different results — the proxy this test used before counted them as
/// one.  The control is written so the length proxy cannot pass it.
#[test]
fn the_round_five_counter_compares_the_guards_digest_not_the_length() {
    let call = |key: &str, observation: &str| {
        (
            1usize,
            RecordedCall {
                key: key.to_string(),
                is_artifact_write: false,
                observation_digest: output_digest(observation_body(observation)),
                succeeded: true,
            },
        )
    };
    let wrap = |body: &str| format!("<returncode>0</returncode>\n<output>\n{body}\n</output>\n");
    let alpha = wrap("alpha");
    let bravo = wrap("bravo");
    assert_eq!(
        alpha.len(),
        bravo.len(),
        "the control is only a control at equal byte length"
    );
    assert_ne!(
        output_digest(observation_body(&alpha)),
        output_digest(observation_body(&bravo)),
        "equal byte length is not equal content"
    );

    // Same length, different bytes: two runs of one, so no abort at a cap of 2.
    let calls = vec![
        call("cargo build --offline", &alpha),
        call("cargo build --offline", &bravo),
    ];
    let (best, abort) = identical_repeats_since_last_write(&calls, 2);
    assert_eq!(
        best.first().map(|(_, count)| *count),
        Some(1),
        "different results of equal length must not be counted as a repetition: {best:?}"
    );
    assert_eq!(abort, None, "and they must never reach the cap");

    // The same result twice is a repetition, and it aborts at the cap.
    let calls = vec![
        call("cargo build --offline", &alpha),
        call("cargo build --offline", &alpha),
    ];
    let (best, abort) = identical_repeats_since_last_write(&calls, 2);
    assert_eq!(best.first().map(|(_, count)| *count), Some(2), "{best:?}");
    assert_eq!(abort, Some(1), "the identical run reaches the cap");
}

/// The two aborts are the runtime's first-class statuses, so a round that ends
/// either way records a fact and not an external agent's string — and the
/// runtime's own limit classification must accept both.
#[test]
fn the_abort_statuses_are_the_runtimes_own() {
    assert_eq!(REPEATED_ACTION_STATUS, "RepeatedActionError");
    assert_eq!(STEP_BUDGET_STATUS, "StepBudgetExceeded");
    assert!(FAIL_FAST_MARKER.starts_with("HOH_"));
    for status in [REPEATED_ACTION_STATUS, STEP_BUDGET_STATUS] {
        assert!(
            hof_rs::runtime::write_failure::is_failure_status(status),
            "`{status}` must be one the runtime classifies as a failure"
        );
    }
    assert!(
        hof_rs::runtime::invoke::is_limits_exceeded(STEP_BUDGET_STATUS),
        "the guard's step-budget abort is a limit, and the wrap-up logic asks that question"
    );
    assert!(!hof_rs::runtime::invoke::is_limits_exceeded("Submitted"));
}
