//! Reproducing the headline numbers **from the repository**.
//!
//! The acceptance that passed (`.spec/bevy/ACCEPTANCE-ACCOUNTING.md`, R-2)
//! recorded the batch's largest residual risk: "every cost conclusion rests on
//! `runs/**` (11.898 GiB, gitignored). A clone, a CI run or another machine
//! cannot re-run the accounting tests or reproduce any number." The round-1
//! PRD-coverage batch answers that by committing the parts the conclusions rest
//! on (`evidence/`, 118 files / 4,771,139 bytes) and by pinning them here.
//!
//! Every test below reads **only** committed files. A test that needs the
//! machine's own recordings would be a test that cannot run from a clone, and
//! that is the defect this file exists to close.
//!
//! `evidence/index.json` is the index: for each headline number, which
//! committed files reproduce it and by what command. One test below checks that
//! the index's file list is entirely present, so the index cannot drift into
//! naming a file nobody committed.

use std::collections::BTreeSet;
use std::path::{Path, PathBuf};

use hof_rs::harness::write_audit::{audit_trajectory, replay_directive_step_budget};
use hof_rs::model::PrdSurfaceCoverage;
use serde_json::Value;

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
}

fn committed(relative: &str) -> PathBuf {
    let path = repo_root().join(relative.replace('/', std::path::MAIN_SEPARATOR_STR));
    assert!(
        path.is_file(),
        "the committed evidence corpus must contain `{relative}`: {} is not a file",
        path.display()
    );
    path
}

fn json(relative: &str) -> Value {
    let path = committed(relative);
    let bytes = std::fs::read(&path).unwrap_or_else(|error| panic!("{}: {error}", path.display()));
    serde_json::from_slice(&bytes).unwrap_or_else(|error| panic!("{}: {error}", path.display()))
}

fn audit(relative: &str) -> hof_rs::harness::write_audit::Audit {
    audit_trajectory(&json(relative))
}

const COST: &[(&str, u64, usize)] = &[
    // (committed file, total tokens, recorded calls)
    (
        "evidence/cost/livecost1-iter-1.developer.attempt1.json",
        3_651_120,
        150,
    ),
    (
        "evidence/cost/round4-iter-1.developer.attempt1.json",
        2_626_195,
        69,
    ),
    (
        "evidence/cost/round4-iter-2.developer.attempt1.json",
        13_091_431,
        125,
    ),
    (
        "evidence/cost/round4-iter-3.developer.attempt1.json",
        5_223_211,
        102,
    ),
];

/// The four committed trajectories are the recorded ones, and they reproduce
/// the cost headline the whole project rests on.
#[test]
fn the_committed_cost_corpus_is_the_recorded_one() {
    let mut total_bytes = 0u64;
    for (path, tokens, calls) in COST {
        let bytes = std::fs::metadata(committed(path)).unwrap().len();
        total_bytes += bytes;
        let audit = audit(path);
        assert_eq!(audit.recorded_calls(), *calls, "{path}");
        assert_eq!(audit.total_tokens, *tokens, "{path}");
    }
    // The report's own figure: 4,166,273 bytes.  (The task statement that
    // commissioned this batch said 4,166,773; the files say 4,166,273, and the
    // files are the authority.  `.spec/bevy/WRITE-ACCOUNTING-REPORT.md` already
    // records the smaller number.)
    assert_eq!(total_bytes, 4_166_273, "the four trajectories' own bytes");

    let live = audit("evidence/cost/livecost1-iter-1.developer.attempt1.json");
    let target = 1_500_000u64;
    assert!(
        live.total_tokens > target,
        "the criterion is not met: {} > {target}",
        live.total_tokens
    );
    let ratio = live.total_tokens as f64 / target as f64;
    assert!(
        (ratio - 2.4341).abs() < 0.0001,
        "3,651,120 / 1,500,000 = {ratio}, reported as 2.434"
    );
}

/// The corrected write profiles, from the committed corpus alone.
#[test]
fn the_committed_cost_corpus_reproduces_the_write_profiles() {
    let live = audit("evidence/cost/livecost1-iter-1.developer.attempt1.json");
    assert_eq!(live.directive_write_calls(), vec![6, 14, 17, 19, 43]);
    assert_eq!(live.project_write_calls(), vec![6, 14, 17, 19, 43, 44, 95]);
    assert_eq!(
        live.failed_project_writes(),
        vec![(139, "src\\game.rs".to_string(), 1)]
    );
    assert_eq!(live.last_project_write(), Some(95));

    let third = audit("evidence/cost/round4-iter-3.developer.attempt1.json");
    assert_eq!(
        third.project_write_calls(),
        vec![6, 8, 75, 81, 85, 87, 91, 94, 98]
    );

    // The two bands, and the corrected global floor (defect D-1).
    let last_under = (1..=60u64)
        .map(|k| replay_directive_step_budget(&live, k))
        .filter(|replay| {
            replay
                .aborted_at_call
                .is_some_and(|_| replay.cumulative_tokens_at_abort < 1_500_000)
        })
        .map(|replay| replay.budget)
        .max()
        .expect("some K ends the live call under the target");
    assert_eq!(last_under, 37);

    let third_safe = replay_directive_step_budget(&third, 43);
    assert_eq!(third_safe.aborted_at_call, None);

    let fifty_one = replay_directive_step_budget(&live, 51);
    assert_eq!(fifty_one.aborted_at_call, Some(95));
    let fifty_two = replay_directive_step_budget(&live, 52);
    assert_eq!(fifty_two.aborted_at_call, Some(96));
    assert!(fifty_two.project_writes_after_the_end.is_empty());
    assert!(
        last_under < 52,
        "the bands do not overlap, and the corrected accounting makes them {last_under} < 43 < 52"
    );
}

/// The **battery step records** the coverage figure is a function of.
///
/// The committed `battery.json` is the runtime's own record of the last pass.
/// Reading it is how the coverage figure is re-derived without the harness: a
/// reader with this file and `src/adapter/bevy/prd_surfaces.rs` has everything.
fn recorded_steps() -> Vec<(String, bool)> {
    let value = json("evidence/observation/round4/deterministic/battery.json");
    let records = match &value {
        // The runtime writes the `Vec<BatteryRecord>` shape.
        Value::Array(records) => records.clone(),
        // `round::write_workspace_payloads` writes `{ "steps": [...] }`.
        Value::Object(map) => map
            .get("steps")
            .and_then(Value::as_array)
            .cloned()
            .unwrap_or_default(),
        _ => Vec::new(),
    };
    assert!(
        !records.is_empty(),
        "the committed battery.json must carry the step records"
    );
    records
        .iter()
        .map(|record| {
            (
                record["step_id"]
                    .as_str()
                    .expect("a recorded step_id")
                    .to_string(),
                record["ok"].as_bool().expect("a recorded ok flag"),
            )
        })
        .collect()
}

/// The recorded round-4 evidence, scored against the **frozen registry**.
///
/// This is criterion (2) of the batch, made executable: the figure is a function
/// of `PRD_SURFACES` and of the battery's own records — never of what the Tester
/// claimed — so the recorded round scores 13/19 with two named gaps, and the two
/// gaps are exactly the surfaces the round predates the new step by.
#[test]
fn the_recorded_round_four_evidence_scores_against_the_registry() {
    let steps = recorded_steps();
    let ids: Vec<&str> = steps.iter().map(|(id, _)| id.as_str()).collect();
    assert_eq!(
        ids,
        vec![
            "editor_errors_baseline",
            "play_scene_ready",
            "e3_movement",
            "e3_coin_counter",
            "e3_win_flag",
            "e3_jump_arc",
            "e3_grounded",
            "e3_movement_left",
            "e3_movement_release",
            "e3_win_position",
            "e3_grounded_payload",
        ],
        "the round predates e3_process_liveness; nine E3 steps and two gate steps"
    );
    assert!(
        steps.iter().all(|(_, ok)| *ok),
        "every recorded step observed: {steps:?}"
    );

    let coverage = hof_rs::adapter::bevy::prd_surfaces::decide(&steps);
    assert_eq!(coverage.total, 19, "the frozen registry's size");
    assert_eq!(coverage.verified, 13, "{}", summary(&coverage));
    assert_eq!(coverage.gap, 2, "{}", summary(&coverage));
    assert_eq!(coverage.unobservable, 4, "{}", summary(&coverage));
    assert_eq!(coverage.decidable(), 15);

    let gaps: Vec<&str> = coverage
        .items
        .iter()
        .filter(|item| item.status == hof_rs::model::SurfaceStatus::Gap)
        .map(|item| item.id.as_str())
        .collect();
    assert_eq!(
        gaps,
        vec!["Q-startup", "B2.1"],
        "the two surfaces the recorded round cannot decide, both named rather than missing"
    );
    for item in &coverage.items {
        if item.status == hof_rs::model::SurfaceStatus::Unobservable {
            assert!(
                item.reason
                    .as_deref()
                    .is_some_and(|reason| reason.len() > 40),
                "`{}` is an explicit named gap, not a blank: {:?}",
                item.id,
                item.reason
            );
        }
    }
}

/// A round that runs the **ten-step** battery scores the same registry with no
/// gap: the two the recorded round could not decide are decided by
/// `e3_process_liveness`.
#[test]
fn the_full_battery_scores_the_registry() {
    let mut steps: Vec<(String, bool)> = vec![
        ("editor_errors_baseline".to_string(), true),
        ("play_scene_ready".to_string(), true),
    ];
    for (step, _, _) in hof_rs::adapter::bevy::round::E3_STEPS {
        steps.push(((*step).to_string(), true));
    }
    let coverage = hof_rs::adapter::bevy::prd_surfaces::decide(&steps);
    assert_eq!(coverage.total, 19);
    assert_eq!(coverage.verified, 15, "{}", summary(&coverage));
    assert_eq!(coverage.gap, 0, "{}", summary(&coverage));
    assert_eq!(coverage.unobservable, 4, "{}", summary(&coverage));
    assert_eq!(
        coverage.verified_share_of_decidable().map(|v| v.round()),
        Some(100.0),
        "everything decidable is verified"
    );

    // And the two gaps the recorded round reported are closed by real ids.
    for (step, supports, name) in hof_rs::adapter::bevy::round::E3_STEPS {
        if *step == "e3_process_liveness" {
            assert_eq!(*supports, "Q-startup");
            assert_eq!(*name, "liveness");
            let item = coverage
                .items
                .iter()
                .find(|item| item.id == "Q-startup")
                .unwrap();
            assert!(item.evidence.contains("e3_process_liveness"), "{item:?}");
            let frame_counter = coverage
                .items
                .iter()
                .find(|item| item.id == "B2.1")
                .unwrap();
            assert!(
                frame_counter.evidence.contains("e3_process_liveness"),
                "{frame_counter:?}"
            );
        }
    }
}

fn summary(coverage: &PrdSurfaceCoverage) -> String {
    coverage
        .items
        .iter()
        .map(|item| format!("{}={}", item.id, item.status.as_str()))
        .collect::<Vec<_>>()
        .join(" ")
}

/// The raw call files: one **semantic tool call per file**, its BRP sub-requests
/// issued as separate JSON-RPC exchanges rather than as one batch.
///
/// This is the evidence behind the registry's `C4` entry. SPIKE-2 measured that
/// a JSON-RPC batch is not frame-atomic, so the PRD forbids using one as a
/// consistency snapshot; the harness's own thin MCP layer issues one request per
/// call, and the committed recordings show it in a way that does not need the
/// code: every sub-request of one semantic call carries that **call's own
/// sequence id**, repeated, and a JSON-RPC batch may not carry two requests with
/// the same id.
#[test]
fn the_committed_raw_calls_are_single_jsonrpc_requests() {
    let directory = repo_root().join("evidence/observation/round4/round/calls");
    let mut files: Vec<PathBuf> = std::fs::read_dir(&directory)
        .unwrap_or_else(|error| panic!("{}: {error}", directory.display()))
        .filter_map(Result::ok)
        .map(|entry| entry.path())
        .filter(|path| path.extension().is_some_and(|ext| ext == "json"))
        .collect();
    files.sort();
    assert_eq!(files.len(), 57, "the committed call files");

    let mut tools: BTreeSet<String> = BTreeSet::new();
    let mut widest = 0usize;
    for path in &files {
        let name = path
            .file_name()
            .map(|name| name.to_string_lossy().into_owned())
            .unwrap_or_default();
        let sequence: u64 = name
            .split('-')
            .next()
            .and_then(|digits| digits.parse().ok())
            .unwrap_or_else(|| panic!("{name}: the file name must lead with the call sequence"));
        let record = serde_json::from_slice::<Value>(&std::fs::read(path).unwrap())
            .unwrap_or_else(|error| panic!("{}: {error}", path.display()));
        assert!(
            !record.is_array(),
            "{}: the top level is a JSON-RPC batch, which C4 forbids",
            path.display()
        );
        let requests = record
            .get("requests")
            .and_then(Value::as_array)
            .unwrap_or_else(|| panic!("{name}: no recorded `requests`"));
        let responses = record
            .get("responses")
            .and_then(Value::as_array)
            .unwrap_or_else(|| panic!("{name}: no recorded `responses`"));
        assert!(!requests.is_empty(), "{name}: an empty request list");
        assert_eq!(
            requests.len(),
            responses.len(),
            "{name}: every sub-request has its own reply"
        );
        widest = widest.max(requests.len());
        let mut ids: BTreeSet<u64> = BTreeSet::new();
        for request in requests {
            assert!(
                !request.is_array(),
                "{name}: a batch reached the wire, which C4 forbids: {request}"
            );
            assert!(
                request.get("method").and_then(Value::as_str).is_some(),
                "{name}: a sub-request names no method: {request}"
            );
            ids.insert(
                request["id"]
                    .as_u64()
                    .unwrap_or_else(|| panic!("{name}: a sub-request has no id")),
            );
        }
        for response in responses {
            assert!(
                !response.is_array(),
                "{name}: a batch reply reached the wire, which C4 forbids"
            );
            assert!(
                response.get("id").is_some(),
                "{name}: a sub-reply has no id: {response}"
            );
        }
        assert_eq!(
            ids,
            BTreeSet::from([sequence]),
            "{name}: the sub-requests share the call's own sequence id, so they are separate \
             exchanges — two requests with the same id cannot be one batch"
        );
        if let Some(tool) = record
            .get("semantic_tool")
            .and_then(Value::as_str)
            .map(str::to_string)
            .or_else(|| {
                name.strip_suffix(".json")
                    .and_then(|stem| stem.split_once('-').map(|(_, tool)| tool.to_string()))
            })
        {
            tools.insert(tool);
        }
    }
    assert!(
        widest > 1,
        "at least one semantic call fans out into several BRP sub-requests"
    );
    assert!(
        tools.contains("bevy_grounded") && tools.contains("bevy_wait_frames"),
        "the recorded calls really are semantic-tool calls: {tools:?}"
    );
}

/// The figure the registry replaces, kept visible: the round-4 Tester's own
/// claim counts, whose denominator is the number of claims the Tester wrote.
#[test]
fn the_recorded_tester_figures_are_the_self_referential_ones() {
    for (iteration, verified, gaps) in [
        ("iter-1", 6, vec!["P2B", "S1"]),
        ("iter-2", 6, vec!["S1", "P3-goal-x"]),
        ("iter-3", 6, vec!["P3-goal-x", "S1-deterministic-step"]),
    ] {
        let result = json(&format!(
            "evidence/observation/round4/{iteration}/result.json"
        ));
        let coverage = &result["prd_coverage"];
        assert_eq!(
            coverage["verified"],
            serde_json::json!(verified),
            "{iteration}"
        );
        assert_eq!(
            coverage["gap_ids"]
                .as_array()
                .map(|ids| ids.iter().filter_map(Value::as_str).collect::<Vec<_>>()),
            Some(gaps.clone()),
            "{iteration}"
        );
        assert_eq!(
            coverage["gap"],
            serde_json::json!(gaps.len()),
            "{iteration}"
        );
        // `total` is not recorded; the round's own line says 6/8, and 8 is
        // `verified + gap` — the Tester's own claim count, which is the defect.
        assert_eq!(
            verified + gaps.len(),
            8,
            "{iteration}: the round's published denominator was the Tester's 8 claims"
        );
    }
}

/// The index names only files that are really committed, and every headline it
/// lists carries a command.
#[test]
fn the_evidence_index_names_committed_files_and_commands() {
    let index = json("evidence/index.json");
    let headlines = index["headlines"]
        .as_array()
        .expect("the index has a headline list");
    assert!(
        headlines.len() >= 15,
        "the index must cover the headline numbers: {} entries",
        headlines.len()
    );
    let mut checked = 0;
    for headline in headlines {
        let id = headline["id"].as_str().expect("every headline has an id");
        assert!(
            headline["command"]
                .as_str()
                .is_some_and(|command| !command.trim().is_empty()),
            "{id}: a headline with no reproduction command is not an index entry"
        );
        let files = headline["files"]
            .as_array()
            .unwrap_or_else(|| panic!("{id}: no files"));
        assert!(!files.is_empty(), "{id}: no files");
        for file in files {
            let relative = file.as_str().expect("a path string");
            let path = repo_root().join(relative.replace('/', std::path::MAIN_SEPARATOR_STR));
            assert!(
                path.exists(),
                "{id}: the index names `{relative}`, which is not committed"
            );
            checked += 1;
        }
    }
    assert!(checked >= 20, "every headline file is checked: {checked}");

    // The summary must match the directory that is really here - and the walk
    // counts **three** figures, not one, because they are three different
    // numbers about three different things:
    //
    //   * the corpus (118 files / 4,771,139 bytes) - the six data groups the
    //     index's `corpus` block and every cost/observation conclusion rest on;
    //   * the excluded files (4 files / 27,829 bytes) - `index.json`,
    //     `README.md` and the two `evidence/tools/*.py`, which the corpus
    //     deliberately leaves out;
    //   * the directory (122 files / 4,798,968 bytes) - everything under
    //     `evidence/`, which is the two added together.
    //
    // Before this test asserted all three, the exclusions were silently
    // `continue`d: a one-byte edit to any non-corpus file under `evidence/`
    // moved the directory total stated in `evidence/README.md` and the gate
    // stayed green (risk R-A1 of `.spec/bevy/ACCEPTANCE-TOTALS.md`).
    let mut files = 0u64;
    let mut bytes = 0u64;
    let mut excluded_files = 0u64;
    let mut excluded_bytes = 0u64;
    let mut stack = vec![repo_root().join("evidence")];
    while let Some(directory) = stack.pop() {
        for entry in std::fs::read_dir(&directory)
            .into_iter()
            .flatten()
            .flatten()
        {
            let path = entry.path();
            if path.is_dir() {
                stack.push(path);
                continue;
            }
            let name = entry.file_name().to_string_lossy().into_owned();
            let size = entry.metadata().map(|meta| meta.len()).unwrap_or(0);
            if path.parent() == Some(Path::new(&repo_root().join("evidence")))
                && (name == "index.json" || name == "README.md")
            {
                excluded_files += 1;
                excluded_bytes += size;
                continue;
            }
            if name == "build_evidence.py" || name == "keyscan.py" {
                excluded_files += 1;
                excluded_bytes += size;
                continue;
            }
            files += 1;
            bytes += size;
        }
    }
    let directory_files = files + excluded_files;
    let directory_bytes = bytes + excluded_bytes;
    assert_eq!(
        index["corpus"]["files"].as_u64(),
        Some(files),
        "the index's file count must be the corpus that is here"
    );
    assert_eq!(
        index["corpus"]["bytes"].as_u64(),
        Some(bytes),
        "the index's byte count must be the corpus that is here"
    );
    // Each of the three figures, named in its own failure message, so a failure
    // says which one moved rather than only that "a total" is wrong.
    assert_eq!(
        (files, bytes),
        (118, 4_771_139),
        "the corpus total (the six data groups, i.e. every committed file under `evidence/` \
         except index.json, README.md and the two evidence/tools/*.py): {files} files / \
         {bytes} bytes"
    );
    assert_eq!(
        (excluded_files, excluded_bytes),
        (4, 27_829),
        "the excluded-files total (index.json + README.md + tools/build_evidence.py + \
         tools/keyscan.py, which the corpus leaves out): {excluded_files} files / \
         {excluded_bytes} bytes"
    );
    assert_eq!(
        (directory_files, directory_bytes),
        (122, 4_798_968),
        "the directory total (everything under `evidence/`, the corpus plus the excluded \
         files): {directory_files} files / {directory_bytes} bytes"
    );
    assert_eq!(
        directory_files,
        files + excluded_files,
        "the directory total must be the corpus plus the excluded files"
    );
    assert_eq!(
        directory_bytes,
        bytes + excluded_bytes,
        "the directory byte total must be the corpus plus the excluded files"
    );
    // The directory total is also stated **by hand** in `evidence/README.md`; pin
    // the statement as well, so the number it prints cannot drift away from the
    // bytes on disk without the gate noticing.
    let readme = std::fs::read_to_string(committed("evidence/README.md"))
        .expect("evidence/README.md is committed and readable");
    assert!(
        readme.contains("122 files / 4,798,968 bytes"),
        "evidence/README.md must state the directory total this test measured \
         ({directory_files} files / {directory_bytes} bytes)"
    );
    let groups = index["corpus"]["groups"]
        .as_array()
        .expect("the index lists the groups");
    let group_bytes: u64 = groups
        .iter()
        .map(|group| group["bytes"].as_u64().unwrap_or(0))
        .sum();
    assert_eq!(
        group_bytes, bytes,
        "the groups must add up to the corpus: {group_bytes} vs {bytes}"
    );

    // And the honest boundary travels with it.
    let not_reproducible = index["not_reproducible_from_the_repository"]
        .as_array()
        .expect("the index states what it cannot reproduce");
    assert!(
        not_reproducible.len() >= 4,
        "the index must state which conclusions stay unreproducible"
    );
    for entry in not_reproducible {
        assert!(
            entry["why"].as_str().is_some_and(|why| why.len() > 40),
            "an unreproducible entry needs its reason: {entry}"
        );
    }
}
