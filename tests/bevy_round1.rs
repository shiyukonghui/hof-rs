//! **The real end-to-end round**: build the scaffolded Bevy game, launch it
//! headless through the adapter, and drive the five E3 behaviours through the
//! semantic tools — with every raw request/response kept as evidence under
//! `runs/bevy-round1/**` (DESIGN-DETAIL §6).
//!
//! Two properties of this test are the point of it:
//!
//! * **Nothing here asserts its own success.**  The assertions read the evidence
//!   the *adapter* wrote — `meta.json`, `gate.json`, `launch.json`,
//!   `readings/e3-observations.json` and `calls/**` — so a green test means the
//!   files say the behaviours were observed, not that a script decided so.
//! * **The negative control is a real process too.**  A second workspace is built
//!   from the same scaffold with the jump replaced by a downward impulse and the
//!   ground removed, and the *same* battery must report the jump criterion **red**
//!   with the monotone-fall reason.  "A monotone fall must fail" is therefore
//!   demonstrated on a real game, not only on a fixture.
//!
//! It is `#[ignore]`d because it needs a real Bevy build (minutes) and a real
//! headless launch; DESIGN-DETAIL §8.5 says exactly that about integration tests:
//! not in the default gate, but present and runnable where there is an
//! environment.
//!
//! ```text
//! cargo test --offline --test bevy_round1 -- --ignored --nocapture
//! ```
//!
//! **What this does not prove.**  The game it drives is the `hoh init` scaffold —
//! the observation scaffold the spike reports require `A₀` to carry — and **not**
//! a game a Developer role wrote, because no model credential was available in
//! this batch.  The evidence is labelled accordingly (`qa/pointer.json` names the
//! round; this file's name is the label) and the round report says so.

use std::path::{Path, PathBuf};
use std::time::Instant;

use serde_json::{json, Value};

use hof_rs::adapter::bevy::brp;
use hof_rs::adapter::bevy::build::{feature_set_sha256, lockfile_sha256};
use hof_rs::adapter::bevy::contract::contract_sha256;
use hof_rs::adapter::bevy::launch::LaunchConfig;
use hof_rs::adapter::bevy::project::{evidence_root_of, round_build_policy};
use hof_rs::adapter::bevy::{scaffold, BevyAdapter, BevyAdapterConfig};
use hof_rs::adapter::ProjectAdapter;
use hof_rs::runtime::policy::sha256_hex;
use hof_rs::tools::ShellOnlyChannel;

/// The round this file writes its evidence under.
const ROUND: &str = "round1";
/// The negative control's round.
const NEGATIVE_ROUND: &str = "round1-negative-control";

/// The scratch root, outside the repository.  The two workspaces are siblings so
/// they share one persistent target directory (`<parent>/hof-bevy-shared-target`,
/// DESIGN-DETAIL §5).
fn scratch_root() -> PathBuf {
    std::env::var("HOF_ROUND_SCRATCH")
        .map(PathBuf::from)
        .unwrap_or_else(|_| PathBuf::from("F:/hof-bevy-round1"))
}

/// The repository root: where `runs/bevy-<round>/` is written.
fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
}

fn adapter_for(workspace: &Path, round: &str) -> BevyAdapter {
    BevyAdapter::at(workspace.to_path_buf()).with_config(BevyAdapterConfig {
        build_policy: round_build_policy(workspace),
        launch: LaunchConfig::default(),
        round: round.to_string(),
        write_evidence: true,
        evidence_root: evidence_root_of(&repo_root().join("runs")),
    })
}

fn read_json(path: &Path) -> Value {
    let raw = std::fs::read_to_string(path)
        .unwrap_or_else(|error| panic!("{} could not be read: {error}", path.display()));
    serde_json::from_str(&raw)
        .unwrap_or_else(|error| panic!("{} is not JSON: {error}", path.display()))
}

fn round_dir(root: &Path, round: &str) -> PathBuf {
    root.join("runs").join(format!("bevy-{round}"))
}

/// The five criteria, as the evidence file states them, plus the call ids.
fn observation_summary(observations: &Value) -> Value {
    let mut summary = serde_json::Map::new();
    for key in ["movement", "coins", "win", "jump", "grounded"] {
        let observation = &observations[key];
        let calls: Vec<u64> = observation["calls"]
            .as_array()
            .map(|calls| {
                calls
                    .iter()
                    .filter_map(|call| call["seq"].as_u64())
                    .collect()
            })
            .unwrap_or_default();
        summary.insert(
            key.to_string(),
            json!({
                "observed": observation["observed"],
                "failure": observation["failure"],
                "calls": calls,
                "readings": observation["readings"]
                    .as_array()
                    .map(|readings| readings.len())
                    .unwrap_or(0),
            }),
        );
    }
    summary.insert(
        "arc".to_string(),
        json!({
            "rising": observations["jump"]["arc"]["rising"],
            "falling": observations["jump"]["arc"]["falling"],
            "peak": observations["jump"]["arc"]["peak"],
            "first": observations["jump"]["arc"]["first"],
            "samples": observations["jump"]["arc"]["samples"]
                .as_array()
                .map(|samples| samples.len())
                .unwrap_or(0),
        }),
    );
    Value::Object(summary)
}

#[tokio::test]
#[ignore = "needs a real Bevy build (minutes) and a headless launch; never in the default gate"]
async fn the_five_behaviours_are_observed_on_a_real_bevy_game_process() {
    let scratch = scratch_root();
    let repo = repo_root();
    let workspace = scratch.join("workspace");
    println!("workspace : {}", workspace.display());
    println!("evidence  : {}", round_dir(&repo, ROUND).display());

    // ---- `hoh init` --------------------------------------------------------
    let adapter = adapter_for(&workspace, ROUND);
    let initialized = Instant::now();
    adapter
        .initialize(&workspace)
        .expect("the scaffold must be written");
    println!(
        "initialize: {} ms; files {}",
        initialized.elapsed().as_millis(),
        scaffold::SCAFFOLD_FILES.len()
    );
    assert!(
        scaffold::all_present(&workspace),
        "`hoh init` must leave a complete A0"
    );
    for rel in scaffold::SCAFFOLD_FILES {
        let on_disk = std::fs::read_to_string(workspace.join(rel)).expect("a scaffold file");
        assert_eq!(
            on_disk,
            scaffold::contents(rel).expect("the scaffold's bytes"),
            "`{rel}` is not the scaffold this repository reviewed"
        );
    }

    // ---- the deterministic battery: build, launch, observe, stop ----------
    //
    // The scaffold's own bytes are written again before the build.  A shared
    // target directory holds one `debug/hof_game.exe` for every package that
    // built into it, and cargo may consider a unit fresh without checking that
    // another unit has overwritten its output; rewriting the source moves its
    // mtime, which forces *this* artifact's build.  The digest the round records
    // in `launch.json` is what makes "which artifact ran?" checkable afterwards.
    for rel in ["src/main.rs", "src/contract.rs", "src/game.rs"] {
        std::fs::write(
            workspace.join(rel),
            scaffold::contents(rel).expect("the scaffold's bytes"),
        )
        .expect("the scaffold source");
    }
    let started = Instant::now();
    let records = adapter
        .evidence_battery(&workspace, &ShellOnlyChannel)
        .await
        .expect("the battery answers for every step");
    let battery_millis = started.elapsed().as_millis() as u64;

    let step = |id: &str| {
        records
            .iter()
            .find(|record| record.step_id == id)
            .unwrap_or_else(|| {
                panic!(
                    "no `{id}` record: {:?}",
                    records.iter().map(|r| &r.step_id).collect::<Vec<_>>()
                )
            })
    };
    for id in [
        "editor_errors_baseline",
        "play_scene_ready",
        "e3_movement",
        "e3_coin_counter",
        "e3_win_flag",
        "e3_jump_arc",
        "e3_grounded",
    ] {
        let record = step(id);
        println!("step {id}: ok={} {}", record.ok, record.record.observation);
    }
    assert!(
        step("editor_errors_baseline").ok,
        "the candidate must build cleanly: {}",
        step("editor_errors_baseline").record.observation
    );
    assert!(
        step("play_scene_ready").ok,
        "the game must boot and answer: {}",
        step("play_scene_ready").record.observation
    );

    // ---- the evidence the adapter wrote -----------------------------------
    let directory = round_dir(&repo, ROUND);
    let meta = read_json(&directory.join("meta.json"));
    let gate = read_json(&directory.join("gate.json"));
    let launch = read_json(&directory.join("launch.json"));
    let observations = read_json(&directory.join("readings/e3-observations.json"));
    let summary = observation_summary(&observations);

    assert_eq!(
        meta["contract_sha256"],
        json!(contract_sha256()),
        "the round must record the frozen contract hash"
    );
    assert_eq!(
        meta["feature_sha256"],
        json!(feature_set_sha256()),
        "the round must record the frozen feature set"
    );
    assert_eq!(
        meta["lock_sha256"],
        json!(lockfile_sha256(&workspace.join("Cargo.lock")).expect("a lockfile")),
        "the round must record the lockfile it built"
    );
    assert_eq!(
        gate["launchable"],
        json!(true),
        "the gate must be green: {gate}"
    );
    assert_eq!(launch["headless"], json!(true), "the round runs headless");
    assert_eq!(
        launch["endpoint"],
        json!(brp::endpoint()),
        "the round depends on the pinned main-world endpoint only"
    );
    assert!(
        launch["stop"]["exit_code"].is_number(),
        "the stop must report the process's own exit code: {launch}"
    );

    // The five criteria, in the order the design fixes them.
    assert_eq!(
        observations["movement"]["observed"],
        json!(true),
        "①: {}",
        observations["movement"]["failure"]
    );
    assert_eq!(
        observations["coins"]["observed"],
        json!(true),
        "②: {}",
        observations["coins"]["failure"]
    );
    assert_eq!(
        observations["win"]["observed"],
        json!(true),
        "③: {}",
        observations["win"]["failure"]
    );
    assert_eq!(
        observations["jump"]["observed"],
        json!(true),
        "④: {}",
        observations["jump"]["failure"]
    );
    assert_eq!(
        observations["grounded"]["observed"],
        json!(true),
        "⑤: {}",
        observations["grounded"]["failure"]
    );
    let arc = &observations["jump"]["arc"];
    let rising = arc["rising"].as_u64().unwrap_or(0);
    let falling = arc["falling"].as_u64().unwrap_or(0);
    let peak = arc["peak"].as_f64().unwrap_or(f64::MIN);
    let first = arc["first"].as_f64().unwrap_or(f64::MAX);
    assert!(rising > 0 && falling > 0, "④ needs both directions: {arc}");
    assert!(
        peak > first,
        "④ needs a peak above the take-off height: {arc}"
    );
    // The coin counter and the win flag start where the PRD says they start.
    let coin_readings: Vec<Value> = observations["coins"]["readings"]
        .as_array()
        .cloned()
        .unwrap_or_default()
        .into_iter()
        .filter_map(|reading| reading["value"]["coins"].as_i64())
        .map(|coins| json!(coins))
        .collect();
    assert_eq!(
        coin_readings.first(),
        Some(&json!(0)),
        "② the counter must start at 0: {coin_readings:?}"
    );
    assert!(
        coin_readings
            .iter()
            .any(|coins| coins.as_i64().unwrap_or(0) > 0),
        "② the counter must rise: {coin_readings:?}"
    );

    // Every reading is one raw call, and every call is one JSON-RPC object.
    let mut call_files = 0usize;
    let mut call_seqs: Vec<u64> = Vec::new();
    for entry in std::fs::read_dir(directory.join("calls")).expect("the calls directory") {
        let path = entry.expect("an entry").path();
        let call = read_json(&path);
        call_files += 1;
        call_seqs.push(call["seq"].as_u64().unwrap_or(0));
        assert!(
            call["requests"].as_array().map(|r| !r.is_empty()) == Some(true),
            "{} carries no raw request",
            path.display()
        );
        for request in call["requests"].as_array().cloned().unwrap_or_default() {
            assert!(
                request.is_object(),
                "a batch body is not allowed: {request}"
            );
        }
    }
    call_seqs.sort_unstable();
    assert!(
        call_files > 20,
        "the five criteria need many raw calls, got {call_files}"
    );
    assert_eq!(
        call_seqs,
        (1..=call_files as u64).collect::<Vec<u64>>(),
        "the call sequence numbers must be dense and ordered"
    );

    println!(
        "{}",
        serde_json::to_string_pretty(&json!({
            "round": ROUND,
            "game": "the hoh init scaffold (no model ran: see the module docs)",
            "evidence_directory": directory.display().to_string(),
            "battery_millis": battery_millis,
            "segments": meta["segments"],
            "gate": gate,
            "launch": launch,
            "observations": summary,
            "calls": call_files,
        }))
        .expect("a JSON summary")
    );

    // ---- the negative control: the same workspace, a game that only falls ---
    //
    // The control runs in the **same** workspace as the positive round, with
    // `src/game.rs` temporarily replaced.  Two sibling workspaces sharing one
    // persistent target directory would both produce `debug/hof_game.exe`, and
    // cargo considers a unit fresh without checking that *another* unit has
    // overwritten its output — which is exactly how the first attempt at this
    // control launched a stale binary (see ROUND-1-REPORT.md).  Patching in
    // place keeps one package unit, so the binary that runs is the binary that
    // was just built.  The scaffold is restored afterwards and the patched bytes
    // are kept outside the repository for audit.
    let game = workspace.join("src/game.rs");
    let template = scaffold::contents("src/game.rs").expect("the scaffold's game source");
    let patched = template.replace(
        "Transform::from_xyz(0.0, GROUND_Y, 0.0)",
        "Transform::from_xyz(0.0, GROUND_Y + 1_000_000.0, 0.0)",
    );
    let negative_adapter = adapter_for(&workspace, NEGATIVE_ROUND);
    assert_ne!(
        patched, template,
        "the negative control must really change the game"
    );
    assert!(
        patched.contains("GROUND_Y + 1_000_000.0"),
        "the player must spawn in the air so the arc only descends"
    );
    let counter_example = scratch.join("negative-src").join("game.rs");
    std::fs::create_dir_all(counter_example.parent().expect("a parent")).expect("the audit dir");
    std::fs::write(&counter_example, &patched).expect("the counter-example copy");
    println!(
        "negative control source: {} sha256 {}",
        counter_example.display(),
        sha256_hex(patched.as_bytes())
    );
    std::fs::write(&game, &patched).expect("the patched game");

    let negative_records = negative_adapter
        .evidence_battery(&workspace, &ShellOnlyChannel)
        .await
        .expect("the negative battery answers for every step");
    let negative_observations =
        read_json(&round_dir(&repo, NEGATIVE_ROUND).join("readings/e3-observations.json"));
    let jump = &negative_observations["jump"];
    let failure = jump["failure"].as_str().unwrap_or("");
    let falling = jump["arc"]["falling"].as_u64().unwrap_or(0);
    println!(
        "negative control: jump observed={} rising={} falling={falling} failure={failure}",
        jump["observed"], jump["arc"]["rising"]
    );
    assert_eq!(
        jump["observed"],
        json!(false),
        "a monotone fall must not be reported as a jump: {jump}"
    );
    assert!(
        falling > 0,
        "the negative control must really fall, or the control is vacuous: {jump}"
    );
    assert_eq!(
        jump["arc"]["rising"],
        json!(0),
        "a monotone fall has no rising step: {jump}"
    );
    assert!(
        failure.contains("never rises") || failure.contains("monotone fall"),
        "the red must be the monotone-fall criterion: {failure}"
    );
    let negative_step = negative_records
        .iter()
        .find(|record| record.step_id == "e3_jump_arc")
        .expect("the negative control has a jump record");
    assert!(!negative_step.ok, "the negative control's jump step is red");
    // The two rounds ran two *different* binaries: the digest in `launch.json`
    // is what makes "the artifact produced these observations" checkable, and it
    // is the guard against the stale-artifact trap this control first fell into.
    let positive_binary = read_json(&round_dir(&repo, ROUND).join("launch.json"))["binary"]
        ["sha256"]
        .as_str()
        .unwrap_or("")
        .to_string();
    let negative_binary = read_json(&round_dir(&repo, NEGATIVE_ROUND).join("launch.json"))
        ["binary"]["sha256"]
        .as_str()
        .unwrap_or("")
        .to_string();
    assert_eq!(
        positive_binary.len(),
        64,
        "the positive binary must be hashed"
    );
    assert_eq!(
        negative_binary.len(),
        64,
        "the control binary must be hashed"
    );
    assert_ne!(
        positive_binary, negative_binary,
        "the control must have run a different binary than the round"
    );
    // The positive round's gate is untouched by the control: the two rounds
    // wrote two directories.
    assert_eq!(
        read_json(&round_dir(&repo, ROUND).join("gate.json"))["launchable"],
        json!(true),
        "the positive round's gate must survive the control"
    );
    println!(
        "negative control evidence: {}",
        round_dir(&repo, NEGATIVE_ROUND).display()
    );

    // ---- restore A0 --------------------------------------------------------
    std::fs::write(&game, template).expect("the scaffold is restored");
    assert_eq!(
        std::fs::read_to_string(&game).expect("the restored source"),
        scaffold::contents("src/game.rs").expect("the scaffold's bytes"),
        "the workspace must be left as `hoh init` wrote it"
    );
}
