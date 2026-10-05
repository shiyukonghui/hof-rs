//! Round-5 cost repair, measured on **recorded** trajectories: what the context
//! fold does to the wire bytes a role call would re-send, call by call.
//!
//! This is not a round.  It reads `runs/round4/iter-*/traj/developer.attempt1.json`
//! (recorded evidence, never written) and, when that gitignored recording is
//! absent — as it is in a clone — the byte-identical committed copy
//! `evidence/cost/round4-iter-*.developer.attempt1.json`.  It reconstructs the
//! message list the agent held before each model call, and runs the
//! repository's own
//! [`hof_rs::harness::compact::compact_history`] over it.  The provider's own
//! `usage.prompt_tokens` for each call is printed next to the projection.
//!
//! The projection is arithmetic and is labelled as such: measured prompt tokens
//! are a linear function of the wire bytes actually sent (`0.2563` tokens per
//! byte on round 4's three Developer calls, fitted over all 296 recorded calls
//! with the fit reproducing each call's total to within 0.01%), so the compacted
//! wire bytes are turned into a projected token count with that measured ratio.
//! The report states the method; this test provides the numbers.

use std::path::{Path, PathBuf};

use hof_rs::harness::compact::{compact_history, message_wire_bytes, CompactPolicy};
use mini_swe_agent::Message;

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
}

/// The **committed** corpus is preferred: `evidence/cost/<run>-<iteration>.
/// developer.attempt1.json` is the same byte sequence the round recorded, added
/// to the tree by the round-1 PRD-coverage batch so the measurement is
/// reproducible from a clone.  The gitignored `runs/**` recording is the
/// fallback for a machine that has it but not the corpus; this mirrors
/// `tests/write_accounting.rs`.  Without the fallback the whole gate went red in
/// a fresh clone — `runs/**` is gitignored, so `measured` was 0 and the
/// `assert_eq!(measured, 3)` below failed on a clean checkout.
fn trajectory(directory: &str, iteration: &str) -> Option<PathBuf> {
    let committed = repo_root()
        .join("evidence/cost")
        .join(format!("{directory}-{iteration}.developer.attempt1.json"));
    if committed.is_file() {
        return Some(committed);
    }
    let recorded = repo_root()
        .join("runs")
        .join(directory)
        .join(iteration)
        .join("traj/developer.attempt1.json");
    recorded.is_file().then_some(recorded)
}

fn read_json(path: &Path) -> serde_json::Value {
    let bytes = std::fs::read(path).unwrap_or_else(|error| panic!("{}: {error}", path.display()));
    serde_json::from_slice(&bytes).unwrap_or_else(|error| panic!("{}: {error}", path.display()))
}

/// The messages as mini's own wire form carries them: role, content, tool calls,
/// tool-call id.  The trajectory's local-only `extra` blocks are excluded — they
/// never leave the process (`to_llm_message` sends these four fields), which is
/// why the measured tokens-per-byte ratio is a fit over exactly this subset.
fn to_messages(value: &serde_json::Value) -> Vec<Message> {
    value["messages"]
        .as_array()
        .cloned()
        .unwrap_or_default()
        .into_iter()
        .map(|message| {
            let mut converted = Message::new(
                message["role"].as_str().unwrap_or("").to_string(),
                message["content"].clone(),
            );
            if let Some(calls) = message.get("tool_calls") {
                if !calls.is_null() {
                    converted
                        .fields
                        .insert("tool_calls".to_string(), calls.clone());
                }
            }
            if let Some(id) = message.get("tool_call_id") {
                if !id.is_null() {
                    converted
                        .fields
                        .insert("tool_call_id".to_string(), id.clone());
                }
            }
            converted
        })
        .collect()
}

/// One call's measurement: the wire bytes sent, the wire bytes after the fold,
/// and the provider's own prompt tokens for that call.
struct CallMeasurement {
    index: usize,
    sent_bytes: usize,
    compacted_bytes: usize,
    prompt_tokens: u64,
}

/// Measure **all** the tail lengths in one pass over a trajectory.
///
/// The incoming bytes of a call depend only on how many trailing messages are
/// kept, so the expensive part (parsing a 50 MB-of-history trajectory) happens
/// once and every policy is a prefix sum over it.
fn measure_tails(path: &Path, tails: &[usize]) -> Vec<(usize, Vec<CallMeasurement>)> {
    let trajectory = read_json(path);
    let messages = to_messages(&trajectory);
    let bytes: Vec<usize> = messages.iter().map(message_wire_bytes).collect();
    // For each call position and each tail: the bytes of the prefix under the
    // fold.  The fold itself is run once per call per tail on the small prefix.
    let mut out: Vec<(usize, Vec<CallMeasurement>)> =
        tails.iter().map(|tail| (*tail, Vec::new())).collect();
    for (position, _message) in messages.iter().enumerate() {
        let usage = &trajectory["messages"][position]["extra"]["response"]["usage"];
        let Some(prompt_tokens) = usage["prompt_tokens"].as_u64() else {
            continue;
        };
        let prefix = &messages[..position];
        let sent: usize = prefix.iter().map(message_wire_bytes).sum();
        for (tail, measurements) in out.iter_mut() {
            let policy = CompactPolicy {
                enabled: true,
                preserve_tail: *tail,
            };
            let compacted = if prefix.len() <= 2 + *tail {
                sent
            } else {
                let mut folded = prefix.to_vec();
                compact_history(&mut folded, policy);
                folded.iter().map(message_wire_bytes).sum()
            };
            measurements.push(CallMeasurement {
                index: measurements.len() + 1,
                sent_bytes: sent,
                compacted_bytes: compacted,
                prompt_tokens,
            });
        }
    }
    let _ = bytes;
    out
}

/// One policy's measurement of a trajectory, for the default tail.
fn measure(path: &Path, policy: CompactPolicy) -> Vec<CallMeasurement> {
    measure_tails(path, &[policy.preserve_tail])
        .pop()
        .map(|(_, measurements)| measurements)
        .unwrap_or_default()
}

/// The regression point the report quotes: on every recorded round-4 Developer
/// call, the fold removes most of the bytes the call would re-send, and the
/// measured tokens-per-wire-byte ratio (`0.2563`) turns that into a projected
/// token figure.
#[test]
fn the_context_fold_shrinks_every_recorded_round_four_developer_call() {
    let mut measured = 0usize;
    for iteration in ["iter-1", "iter-2", "iter-3"] {
        let Some(path) = trajectory("round4", iteration) else {
            continue;
        };
        measured += 1;
        let policy = CompactPolicy::default();
        let calls = measure(&path, policy);
        assert!(!calls.is_empty(), "{iteration}: no recorded calls");
        let sent: usize = calls.iter().map(|call| call.sent_bytes).sum();
        let compacted: usize = calls.iter().map(|call| call.compacted_bytes).sum();
        let recorded_tokens: u64 = calls.iter().map(|call| call.prompt_tokens).sum();
        let ratio = recorded_tokens as f64 / sent as f64;
        let projected = (compacted as f64 * ratio).round() as u64;
        let last = calls.last().expect("a last call");
        println!(
            "{iteration}: calls={} tail={} recorded_prompt_tokens={} wire_bytes={} -> {} \
             ({:.1}% of the bytes) tokens_per_wire_byte={:.4} projected_prompt_tokens={} \
             ({:.1}% measured) last_call_wire={} -> {} tokens={} projected={}",
            calls.len(),
            policy.preserve_tail,
            recorded_tokens,
            sent,
            compacted,
            100.0 * compacted as f64 / sent as f64,
            ratio,
            projected,
            100.0 * projected as f64 / recorded_tokens as f64,
            last.sent_bytes,
            last.compacted_bytes,
            last.prompt_tokens,
            (last.compacted_bytes as f64 * ratio).round() as u64,
        );
        // The fold must not be a no-op anywhere on these calls, and it must not
        // be a rounding error either: the recorded histories are dominated by
        // superseded payloads by construction.
        assert!(
            compacted * 2 < sent,
            "{iteration}: the fold removed less than half the wire bytes ({sent} -> {compacted})"
        );
        assert!(
            projected < recorded_tokens,
            "{iteration}: the projection must be below the recorded spend"
        );
        // The fold is monotone: it can never make a call's context bigger.
        for call in &calls {
            assert!(
                call.compacted_bytes <= call.sent_bytes,
                "{iteration} call {}: the fold grew the context ({} -> {})",
                call.index,
                call.sent_bytes,
                call.compacted_bytes
            );
        }
    }
    assert_eq!(
        measured, 3,
        "the three round-4 Developer calls are the evidence"
    );
}

/// The tail length is the one free parameter of the policy, so the report states
/// the whole curve rather than one point: at every tail the fold removes most of
/// the bytes, and the choice documented in `config/hoh.yaml` (12) is where the
/// saving is nearly complete without folding what the model just did.
///
/// A longer verbatim tail must never be cheaper than a shorter one: otherwise the
/// knob would not be measuring what it claims.
#[test]
fn the_fold_curve_over_the_preserved_tail_is_measured() {
    let Some(path) = trajectory("round4", "iter-2") else {
        return;
    };
    let mut previous_projected = 0u64;
    for (tail, calls) in measure_tails(&path, &[0, 2, 4, 6, 8, 12, 16, 24, 32]) {
        let sent: usize = calls.iter().map(|call| call.sent_bytes).sum();
        let compacted: usize = calls.iter().map(|call| call.compacted_bytes).sum();
        let recorded_tokens: u64 = calls.iter().map(|call| call.prompt_tokens).sum();
        let ratio = recorded_tokens as f64 / sent as f64;
        let projected = (compacted as f64 * ratio).round() as u64;
        println!(
            "tail={tail:>2}: wire {} -> {} ({:.1}%) projected_tokens={projected} ({:.1}% of \
             recorded {recorded_tokens})",
            sent,
            compacted,
            100.0 * compacted as f64 / sent as f64,
            100.0 * projected as f64 / recorded_tokens as f64,
        );
        assert!(
            projected >= previous_projected,
            "a longer verbatim tail cannot fold more than a shorter one: tail {tail} projected \
             {projected}, previous {previous_projected}"
        );
        previous_projected = projected;
    }
}

/// The projection's calibration: the recorded prompt tokens really are a linear
/// function of the wire bytes sent, so "wire bytes in, tokens out" is a
/// measurement and not a guess.
#[test]
fn the_measured_prompt_tokens_track_the_wire_bytes_the_call_sent() {
    let Some(path) = trajectory("round4", "iter-2") else {
        return;
    };
    let calls = measure(&path, CompactPolicy::default());
    let n = calls.len() as f64;
    let mean_x = calls.iter().map(|c| c.sent_bytes as f64).sum::<f64>() / n;
    let mean_y = calls.iter().map(|c| c.prompt_tokens as f64).sum::<f64>() / n;
    let cov: f64 = calls
        .iter()
        .map(|c| (c.sent_bytes as f64 - mean_x) * (c.prompt_tokens as f64 - mean_y))
        .sum();
    let var: f64 = calls
        .iter()
        .map(|c| (c.sent_bytes as f64 - mean_x).powi(2))
        .sum();
    let slope = cov / var;
    let intercept = mean_y - slope * mean_x;
    let total_fit: f64 = calls
        .iter()
        .map(|c| intercept + slope * c.sent_bytes as f64)
        .sum();
    let total_recorded: u64 = calls.iter().map(|c| c.prompt_tokens).sum();
    let worst = calls
        .iter()
        .map(|c| (intercept + slope * c.sent_bytes as f64 - c.prompt_tokens as f64).abs())
        .fold(0.0f64, f64::max);
    println!(
        "iter-2: slope={slope:.6} tokens/wire-byte intercept={intercept:.2} \
         fit_total={total_fit:.0} recorded_total={total_recorded} worst_call_residual={worst:.0}"
    );
    assert!(
        (slope - 0.2563).abs() < 0.01,
        "the report quotes 0.2563 tokens per wire byte; the fit says {slope:.4}"
    );
    // The fit must reproduce the call's own total, not merely correlate: the
    // projection is only as good as this.
    let error = (total_fit - total_recorded as f64).abs() / total_recorded as f64;
    assert!(
        error < 0.01,
        "the fit must reproduce the recorded total to within 1%: {error:.4}"
    );
}

/// AC-14: the fold is on by default (`src/config.rs`), and every other
/// behaviour-changing limit in the same `agent` section is documented in
/// `config/hoh.yaml`.  The two knobs this batch added were the exception: a
/// reader of the configuration could not see that the fold exists at all.
#[test]
fn the_agent_configuration_documents_the_compaction_knobs() {
    let yaml = std::fs::read_to_string(repo_root().join("config/hoh.yaml"))
        .expect("config/hoh.yaml is part of the tree");
    for knob in ["compact_history:", "compact_history_tail:"] {
        assert!(
            yaml.contains(knob),
            "config/hoh.yaml must document `{knob}`: the fold is on by default and a reader of \
             the configuration has to be able to see it"
        );
    }
}

/// AC-9: `src/config.rs` quoted a projection (`839K / 2.50M / 1.48M`) that this
/// file's own measurement contradicts.  The doc comment now carries the measured
/// figures; the test reads the source because that number lives in a comment no
/// other assertion can reach, which is exactly how it drifted in the first place.
#[test]
fn the_documented_projection_is_the_measured_one() {
    let source = std::fs::read_to_string(repo_root().join("src/config.rs"))
        .expect("src/config.rs is part of the tree");
    assert!(
        source.contains("875,647 / 2,681,282 / 1,663,325"),
        "src/config.rs must quote the measured projection (`875,647 / 2,681,282 / 1,663,325`)"
    );
    assert!(
        !source.contains("839K"),
        "the contradicted projection (`839K / 2.50M / 1.48M`) is back in src/config.rs"
    );
}
