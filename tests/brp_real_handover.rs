//! Round-4 repair — the transport gap, reproduced against a **real** Bevy game.
//!
//! Round 3's coverage was seven of eight PRD items; the gap was `G-transport`:
//! the first sequenced battery call of passes 2 and 3 failed with
//! `BRP transport failure to http://127.0.0.1:15702/: transport failure` at frame
//! zero, before anything was read, while pass 1 (the round's first launch) was
//! clean on its first call.
//!
//! This file starts the real game twice through the harness's own launcher, with
//! one BRP client created **before** the first launch — exactly how a round's
//! observing client is created — and asks one question: does the first call made
//! after the **second** process is up, through that same client, fail at the
//! transport layer?
//!
//! It is `#[ignore]`d because it needs a real Bevy build (minutes, hundreds of
//! megabytes) and a headless launch, so it is never in the default gate:
//!
//! ```text
//! HOF_BEVY_GAME_IMAGE=<path to hof_game.exe> cargo test --offline \
//!     --test brp_real_handover -- --ignored --nocapture
//! ```
//!
//! A run with no `HOF_BEVY_GAME_IMAGE` is a no-op that says so; it never
//! silently passes as if it had measured something.

use std::path::PathBuf;
use std::sync::{Arc, Mutex};
use std::time::Duration;

use hof_rs::adapter::bevy::brp::{self, BrpClient};
use hof_rs::adapter::bevy::launch::{start_game, LaunchConfig};
use hof_rs::adapter::bevy::BevyAdapter;
use hof_rs::adapter::{GameAdapter, Prepared};

fn image() -> Option<PathBuf> {
    let path = std::env::var("HOF_BEVY_GAME_IMAGE").ok()?;
    let path = PathBuf::from(path);
    path.is_file().then_some(path)
}

fn frame_counter_call(client: &BrpClient) -> Result<u64, String> {
    client
        .call(
            "world.get_resources",
            Some(serde_json::json!({"resource": "hof_game::contract::FrameCounter"})),
        )
        .map(|value| {
            value
                .get("value")
                .and_then(|inner| inner.get("frames"))
                .and_then(serde_json::Value::as_u64)
                .unwrap_or(0)
        })
        .map_err(|error| error.to_string())
}

/// Stop any game a test started, even when the test panics.
///
/// A failing assertion in one of these tests must not leave a live game holding
/// 15702 — that is the round-3 defect this batch closes, and a test suite that
/// produced it while proving it closed would be its own counter-example.
struct Reaper {
    pids: Mutex<Vec<u32>>,
}

impl Reaper {
    fn new() -> Self {
        Self {
            pids: Mutex::new(Vec::new()),
        }
    }

    fn watch(&self, pid: u32) {
        if let Ok(mut pids) = self.pids.lock() {
            pids.push(pid);
        }
    }

    fn disarm(&self, pid: u32) {
        if let Ok(mut pids) = self.pids.lock() {
            pids.retain(|watched| *watched != pid);
        }
    }
}

impl Drop for Reaper {
    fn drop(&mut self) {
        let Ok(mut pids) = self.pids.lock() else {
            return;
        };
        for pid in pids.drain(..) {
            if hof_rs::tools::endpoint::process_is_alive(pid) {
                let _ =
                    hof_rs::adapter::bevy::launch::kill_pid_and_verify(pid, Duration::from_secs(2));
            }
        }
    }
}

/// One client, two processes: the round-3 shape.
///
/// The assertion is deliberately the **observation**, not a wish: if the first
/// call after the second launch succeeds, this test reports that the round-3
/// failure did not reproduce through this route, and the gap stays open rather
/// than being declared fixed.
#[test]
#[ignore = "needs a real Bevy build (HOF_BEVY_GAME_IMAGE) and two headless launches"]
fn the_round_three_transport_failure_reproduces_through_one_client() {
    let Some(image) = image() else {
        println!("no HOF_BEVY_GAME_IMAGE: nothing was measured");
        return;
    };
    let reaper = Reaper::new();
    let directory = tempfile::tempdir().expect("a temporary directory");
    let ledger = directory.path().join("launch-ledger.jsonl");
    let config = LaunchConfig {
        ledger: Some(ledger.clone()),
        stage_dir: None,
        ..LaunchConfig::default()
    };
    let stderr = Arc::new(Mutex::new(String::new()));

    // The observing client exists before the first process, as the adapter's does.
    let client = BrpClient::new(brp::endpoint(), Duration::from_secs(5));

    let first = start_game(&image, &config, Arc::clone(&stderr)).expect("the first launch");
    let first_pid = first.pid();
    reaper.watch(first_pid);
    let first_call = frame_counter_call(&client);
    println!("first process pid {first_pid}: call -> {first_call:?}");
    assert!(
        first_call.is_ok(),
        "the first process answers: {first_call:?}"
    );
    let first_stop = first.stop().expect("the first process stops");
    reaper.disarm(first_pid);
    println!("first process stopped: {first_stop:?}");

    // A different process on the same endpoint: the previous one is gone.
    let second = start_game(&image, &config, Arc::clone(&stderr)).expect("the second launch");
    let second_call = frame_counter_call(&client);
    println!(
        "second process pid {}: first call through the SAME client -> {second_call:?}",
        second.pid()
    );
    let third_call = frame_counter_call(&client);
    println!("second process: second call -> {third_call:?}");
    let _ = second.stop();

    assert!(
        third_call.is_ok(),
        "the second process must answer on the retry, or this is not the round-3 shape"
    );
    if second_call.is_err() {
        println!(
            "REPRODUCED: the first call after the process boundary failed with {:?}",
            second_call.unwrap_err()
        );
    } else {
        println!(
            "NOT REPRODUCED: one client crossed the process boundary without a transport failure \
             (a caller must not read this as proof the round-3 gap is fixed)"
        );
    }
}

/// The repair, at the level the adapter applies it: a client rebuilt for the new
/// process answers on its **first** call.
#[test]
#[ignore = "needs a real Bevy build (HOF_BEVY_GAME_IMAGE) and two headless launches"]
fn a_client_rebuilt_for_the_new_process_answers_on_its_first_call() {
    let Some(image) = image() else {
        println!("no HOF_BEVY_GAME_IMAGE: nothing was measured");
        return;
    };
    let directory = tempfile::tempdir().expect("a temporary directory");
    let ledger = directory.path().join("launch-ledger.jsonl");
    let config = LaunchConfig {
        ledger: Some(ledger.clone()),
        stage_dir: None,
        ..LaunchConfig::default()
    };
    let stderr = Arc::new(Mutex::new(String::new()));

    let stale = BrpClient::new(brp::endpoint(), Duration::from_secs(5));
    let reaper = Reaper::new();
    let first = start_game(&image, &config, Arc::clone(&stderr)).expect("the first launch");
    let first_pid = first.pid();
    reaper.watch(first_pid);
    assert!(
        frame_counter_call(&stale).is_ok(),
        "the first process answers"
    );
    let _ = first.stop().expect("the first process stops");
    reaper.disarm(first_pid);

    let fresh = BrpClient::new(brp::endpoint(), Duration::from_secs(5));
    let second = start_game(&image, &config, Arc::clone(&stderr)).expect("the second launch");
    let second_pid = second.pid();
    reaper.watch(second_pid);
    let call = frame_counter_call(&fresh);
    println!(
        "second process pid {}: first call through a REBUILT client -> {call:?}",
        second.pid()
    );
    let _ = second.stop();
    reaper.disarm(second_pid);
    assert!(
        call.is_ok(),
        "a client built for this process must answer on its first call: {call:?}"
    );
}

/// The adapter half of the same rule, end to end against the real game: every
/// `start` rebinds the observing client, so the adapter's own client can never be
/// the one that carries a dead process's socket into the next process's window.
///
/// This is the pin for [`BevyAdapter::client_generation`]: the counter is not an
/// intention, it is read after two real launches.
#[test]
#[ignore = "needs a real Bevy build (HOF_BEVY_GAME_IMAGE) and two headless launches"]
fn the_adapter_rebinds_its_observing_client_at_every_launch() {
    let Some(image) = image() else {
        println!("no HOF_BEVY_GAME_IMAGE: nothing was measured");
        return;
    };
    let directory = tempfile::tempdir().expect("a temporary directory");
    // A build policy with a target directory, because that is what makes the
    // launch **ledger** exist — the round's own record of every process it
    // started, which is what the stop sweep reads.
    let mut adapter =
        BevyAdapter::at(directory.path()).with_config(hof_rs::adapter::bevy::BevyAdapterConfig {
            build_policy: hof_rs::adapter::bevy::build::BuildPolicy {
                target_dir: Some(directory.path().join("target")),
                ..hof_rs::adapter::bevy::build::BuildPolicy::default()
            },
            evidence_root: directory.path().to_path_buf(),
            round: "handover".to_string(),
            ..hof_rs::adapter::bevy::BevyAdapterConfig::default()
        });
    let prepared = Prepared {
        workspace: directory.path().to_path_buf(),
        artifact: Some(image),
        build_millis: 0,
        detail: "an already-built image, supplied for this test".to_string(),
    };
    assert_eq!(adapter.client_generation(), 0, "before any launch");
    let reaper = Reaper::new();
    let first = adapter.start(&prepared).expect("the first launch");
    let first_pid = first.pid;
    reaper.watch(first_pid);
    assert_eq!(
        adapter.client_generation(),
        1,
        "a launch is a process boundary: the observing client is rebuilt"
    );
    assert!(
        adapter.verified_game_endpoint().is_some(),
        "the launch's identity is recorded where the run's metadata can name it"
    );
    let _ = adapter.stop(first).expect("the first stop");
    reaper.disarm(first_pid);

    let second = adapter.start(&prepared).expect("the second launch");
    reaper.watch(second.pid);
    assert_eq!(
        adapter.client_generation(),
        2,
        "the second process gets its own client"
    );
    let reading = adapter.read(hof_rs::adapter::SemanticKind::CoinCounter);
    match reading {
        Ok(reading) => println!("second process first read: failed={}", reading.failed),
        Err(error) => println!("second process first read failed: {error}"),
    }
    let second_pid = second.pid;
    let _ = adapter.stop(second).expect("the second stop");
    reaper.disarm(second_pid);
    let report = adapter.reap_round_processes();
    println!("round-stop sweep: {report:?}");
    assert_eq!(
        report.recorded.len(),
        2,
        "both launches must be on the round's ledger: {report:?}"
    );
    assert!(
        report.verified_dead(),
        "every process this adapter launched must be verified dead: {report:?}"
    );
    assert!(
        report.evidence.is_file(),
        "the sweep writes its own evidence: {report:?}"
    );
}
