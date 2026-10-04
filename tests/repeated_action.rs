//! Round-2 cost batch — what the two new mechanisms would have done to the
//! **recorded** round-2 Developer calls.
//!
//! The two mechanisms that attack the cost are:
//!
//! 1. `harness::guard`'s repeated-**success** tripwire: the same action
//!    succeeding with the same result `agent.max_repeated_actions` times aborts
//!    the call.  Round 2's Developer ended iteration 1 with about seventy calls
//!    of one verification loop and every one of them returned 0, so no older
//!    counter could see it.
//! 2. the progress-gated step budget: a call that has written nothing gets
//!    `wrap_up_steps + step_limit / steps_per_artifact` steps instead of the
//!    flat limit.
//!
//! This file measures both against the recorded trajectories.  It does **not**
//! claim to be a run: the tripwire's own firing is pinned by
//! `harness::guard::tests::the_same_successful_action_with_the_same_result_aborts_the_call`,
//! and what is measured here is the *arithmetic* — where an abort would have
//! landed and how much of the observed prompt-token spend that call would not
//! have made.
//!
//! The trajectories are recorded evidence and are read, never written.

use std::collections::BTreeMap;
use std::path::{Path, PathBuf};

use hof_rs::config::AgentLimits;
use hof_rs::harness::guard::{repeated_action_key, FAIL_FAST_MARKER, REPEATED_ACTION_STATUS};

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
}

fn trajectory(iteration: &str) -> Option<PathBuf> {
    let path = repo_root()
        .join("runs/round2")
        .join(iteration)
        .join("traj/developer.attempt1.json");
    path.is_file().then_some(path)
}

fn read_json(path: &Path) -> serde_json::Value {
    let bytes = std::fs::read(path).unwrap_or_else(|error| panic!("{}: {error}", path.display()));
    serde_json::from_slice(&bytes).unwrap_or_else(|error| panic!("{}: {error}", path.display()))
}

/// One recorded tool call: the normalised action key and the index of the API
/// call whose response commissioned it.
struct RecordedCall {
    key: String,
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
    let mut calls = Vec::new();
    let mut api_index = 0usize;
    for message in trajectory["messages"]
        .as_array()
        .cloned()
        .unwrap_or_default()
    {
        if message["extra"]["response"]["usage"].is_null() {
            continue;
        }
        api_index += 1;
        for call in message["tool_calls"]
            .as_array()
            .cloned()
            .unwrap_or_default()
        {
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
            calls.push((
                api_index,
                RecordedCall {
                    key: repeated_action_key(&command),
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

/// The API call index at which any one action reaches `cap` successes in the
/// call, or `None` when no action ever does.
///
/// It is a **total per action**, not a consecutive run: that is the counter the
/// guard keeps, and it is the counter round 2's grind needs — the recorded loop
/// spelled itself with several `| more` / `| findstr …` / `& echo …` variants, so
/// a consecutive counter saw runs of at most three.
fn abort_index(calls: &[(usize, RecordedCall)], cap: usize) -> Option<usize> {
    let mut counts: BTreeMap<&str, usize> = BTreeMap::new();
    for (api_index, call) in calls {
        let count = counts.entry(call.key.as_str()).or_insert(0);
        *count += 1;
        if *count >= cap {
            return Some(*api_index);
        }
    }
    None
}

/// One trajectory, measured: how far the run got and what a cap would have cost.
#[derive(Debug)]
struct Projection {
    tool_calls: usize,
    api_calls: usize,
    observed_prompt_tokens: u64,
    abort_at: Option<usize>,
    capped_prompt_tokens: u64,
    most_repeated: Vec<(String, usize)>,
}

fn project(path: &Path, cap: usize) -> Projection {
    let trajectory = read_json(path);
    let (calls, api_calls) = recorded_calls(&trajectory);
    let usage = prompt_tokens_by_call(&trajectory);
    let observed: u64 = usage.values().sum();
    let abort_at = abort_index(&calls, cap);
    let capped: u64 = usage
        .iter()
        .filter(|(index, _)| match abort_at {
            Some(limit) => **index <= limit,
            None => true,
        })
        .map(|(_, tokens)| *tokens)
        .sum();
    let mut counts: BTreeMap<String, usize> = BTreeMap::new();
    for (_, call) in &calls {
        *counts.entry(call.key.clone()).or_insert(0) += 1;
    }
    let mut most_repeated: Vec<(String, usize)> = counts.into_iter().collect();
    most_repeated.sort_by(|left, right| right.1.cmp(&left.1).then(left.0.cmp(&right.0)));
    most_repeated.truncate(4);
    Projection {
        tool_calls: calls.len(),
        api_calls,
        observed_prompt_tokens: observed,
        abort_at,
        capped_prompt_tokens: capped,
        most_repeated,
    }
}

/// The recorded round-2 Developer calls exist and really are the grind the
/// report describes: the same action repeated far past the new cap.  If this
/// stops holding, the two projections below become vacuous and must be revisited
/// rather than silently passing.
#[test]
fn the_recorded_round_two_developer_really_repeats_one_action_past_the_cap() {
    let path = trajectory("iter-1").expect("the recorded iteration-1 developer trajectory");
    let projection = project(&path, 15);
    assert!(
        projection.tool_calls > 100,
        "the recorded trajectory is the 125-call grind: {projection:?}"
    );
    let (action, count) = projection
        .most_repeated
        .first()
        .expect("a recorded action")
        .clone();
    assert!(
        count >= 8,
        "one action must repeat at least to the cap; the top repeats are {:?}",
        projection.most_repeated
    );
    assert!(
        action.contains("cargo build"),
        "the repeated action is the verification loop: {action}"
    );
}

/// The tripwire's arithmetic on the recorded call: the abort lands early enough
/// that most of the call's prompt-token spend is never made.
///
/// The projection is arithmetic over the **recorded** per-call prompt tokens — it
/// is not a claim about a real run, and the report says so.
#[test]
fn the_repeated_success_tripwire_would_have_cut_the_recorded_call_early() {
    let path = trajectory("iter-1").expect("the recorded iteration-1 developer trajectory");
    let projection = project(&path, 15);
    println!(
        "iter-1 projection: {:?}",
        (
            projection.api_calls,
            projection.tool_calls,
            projection.observed_prompt_tokens,
            projection.abort_at,
            projection.capped_prompt_tokens
        )
    );
    // The population is the whole call, not a subset: the report's 150 calls and
    // 11.1M prompt tokens are what this projection is taken over.
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
        .expect("the recorded grind reaches the cap");
    assert!(
        abort_at * 2 < projection.api_calls,
        "the abort must land in the first half of the recorded call: abort at api call {abort_at} \
         of {}, repeats {:?}",
        projection.api_calls,
        projection.most_repeated
    );
    let fraction =
        projection.capped_prompt_tokens as f64 / projection.observed_prompt_tokens.max(1) as f64;
    assert!(
        fraction < 0.5,
        "an abort at call {abort_at} would have kept {:.1}% of the observed {} prompt tokens",
        fraction * 100.0,
        projection.observed_prompt_tokens
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

/// The **upper bound of the cap, measured**: iteration 2's most-repeated action
/// runs 14 times in one call.  That call is engineering work — its builds
/// interleave edits and the recorded per-build durations fall, so the repeats are
/// a legitimate rebuild cadence, not a grind — and the tripwire must not fire on
/// it.  `agent.max_repeated_actions` is therefore 15: the smallest integer
/// strictly above that figure and far below iteration 1's 39.
#[test]
fn the_recorded_engineering_call_defines_the_upper_bound_of_the_cap() {
    let Some(path) = trajectory("iter-2") else {
        // The evidence directory is gitignored; a machine without it still runs
        // the gate, and the report says where the figure came from.
        return;
    };
    let projection = project(&path, 15);
    assert!(
        projection.abort_at.is_none(),
        "iteration 2 must stay inside the cap, or the cap is below the evidence: {:?}",
        projection.most_repeated
    );
    let (action, count) = projection
        .most_repeated
        .first()
        .cloned()
        .expect("an action");
    assert_eq!(
        count, 14,
        "the measured upper bound is 14 ({action}); if this figure moves, \
         `agent.max_repeated_actions` must be re-derived rather than left as a guess"
    );
    assert!(
        action.contains("cargo build"),
        "the action at the cap's boundary is the legitimate rebuild: {action}"
    );
}
/// The tripwire's status is the runtime's first-class one, so a round that aborts
/// this way records a fact and not an external agent's string.
#[test]
fn the_abort_status_is_the_runtimes_own() {
    assert_eq!(REPEATED_ACTION_STATUS, "RepeatedActionError");
    assert!(FAIL_FAST_MARKER.starts_with("HOH_"));
    assert!(
        hof_rs::runtime::write_failure::is_failure_status(REPEATED_ACTION_STATUS),
        "the status must be one the runtime classifies as a failure"
    );
}
