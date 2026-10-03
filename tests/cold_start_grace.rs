//! DR-86 ② — the running-game family tolerates a transient transport failure.
//!
//! The round of record marked its game endpoint unavailable after **two**
//! consecutive transport failures *inside the readiness poll that followed
//! `editor_play_scene`*, so the first `running_game_*` call of the round was never
//! sent, every later semantic call was refused with `attempt(s)=0`, and the round
//! produced zero behaviour readings: the third criterion was unjudgeable rather
//! than failed.
//!
//! The property pinned here: inside a readiness window, an endpoint that has
//! **never answered** tolerates a bounded streak instead of two; when the bound is
//! spent it is marked unavailable with the true count and the same refusal text,
//! so an endpoint that truly never answers still gets the honest failure.  Outside
//! such a window the DR-55 two-strike rule is unchanged.

mod common;

use common::*;
use hof_rs::model::Role;
use hof_rs::tools::endpoint::{GameEndpointRecord, SOURCE_AUTO_FREE_PORT};
use hof_rs::tools::endpoint::{COLD_START_DEATH_THRESHOLD, ENDPOINT_DEATH_THRESHOLD};
use hof_rs::tools::reliable::{call_with_retries, wait_for_ready_matching};
use hof_rs::tools::{McpChannel, ToolChannel};
use serde_json::json;

/// A loopback endpoint nothing is listening on: every attempt is a real transport
/// failure, and the port cannot become live during the test.
fn a_closed_loopback_endpoint() -> (String, u16) {
    let listener = std::net::TcpListener::bind("127.0.0.1:0").expect("loopback listener");
    let port = listener.local_addr().expect("bound address").port();
    drop(listener);
    (format!("http://127.0.0.1:{port}/mcp"), port)
}

fn game_record(endpoint: String, port: u16) -> GameEndpointRecord {
    GameEndpointRecord {
        endpoint,
        port: Some(port),
        source: SOURCE_AUTO_FREE_PORT.to_string(),
        pid: Some(std::process::id()),
    }
}

async fn armed_game_channel() -> (McpChannel, String) {
    let (editor_endpoint, _) = a_closed_loopback_endpoint();
    let (game_endpoint, game_port) = a_closed_loopback_endpoint();
    let channel = McpChannel::new(editor_endpoint, 5, 0);
    channel
        .register_game_endpoint(game_record(game_endpoint.clone(), game_port))
        .await
        .expect("registration");
    channel.arm_cold_start_grace("running_game_get_scene_tree", true);
    (channel, game_endpoint)
}

async fn one_attempt(channel: &McpChannel, tool: &str) -> hof_rs::tools::reliable::McpFailure {
    call_with_retries(channel, Role::Developer, tool, json!({}), 0, 0, None)
        .await
        .expect_err("the closed endpoint cannot answer")
}

/// Inside a readiness window, the two failures that killed the round of record
/// are no longer a verdict; the bound is real, and the honest failure is kept
/// with the true count.
#[tokio::test]
async fn a_readiness_window_tolerates_a_bounded_cold_start_streak() {
    let (channel, game_endpoint) = armed_game_channel().await;
    assert!(
        COLD_START_DEATH_THRESHOLD > ENDPOINT_DEATH_THRESHOLD,
        "the cold-start bound must be strictly wider than the DR-55 verdict"
    );

    // Exactly the streak that killed the round of record: two consecutive
    // transport failures, both really sent (not refused).
    for attempt in 1..=ENDPOINT_DEATH_THRESHOLD {
        let failure = one_attempt(&channel, "running_game_get_scene_tree").await;
        assert!(
            !failure.endpoint_verdict,
            "attempt {attempt} must really be sent, not refused: {failure:?}"
        );
        let state = channel.endpoint_state(&game_endpoint).expect("state");
        assert!(
            !state.unavailable,
            "attempt {attempt}: a readiness wait must not declare a never-answered endpoint \
             dead before its bound — these are the two failures the round of record died on: \
             {state:?}"
        );
        assert_eq!(state.consecutive_transport_failures, attempt);
        assert_eq!(state.successes, 0);
    }

    // Up to the bound minus one: still alive.
    for attempt in (ENDPOINT_DEATH_THRESHOLD + 1)..COLD_START_DEATH_THRESHOLD {
        one_attempt(&channel, "running_game_get_scene_tree").await;
        let state = channel.endpoint_state(&game_endpoint).expect("state");
        assert!(!state.unavailable, "attempt {attempt}: {state:?}");
        assert_eq!(state.consecutive_transport_failures, attempt);
    }

    // The bound-th failure is a verdict, with the real number of failures in it.
    let failure = one_attempt(&channel, "running_game_get_scene_tree").await;
    assert!(!failure.endpoint_verdict, "{failure:?}");
    let state = channel.endpoint_state(&game_endpoint).expect("state");
    assert!(
        state.unavailable,
        "the bound must still be a bound: {state:?}"
    );
    assert_eq!(
        state.transport_failures_at_mark, COLD_START_DEATH_THRESHOLD,
        "the verdict must record how many failures killed it: {state:?}"
    );

    // Every later call is refused with zero attempts, exactly as before.
    let refusal = one_attempt(&channel, "running_game_get_scene_tree").await;
    assert!(refusal.endpoint_verdict, "{refusal:?}");
    assert!(
        refusal.message.contains("game_endpoint_unavailable")
            && refusal.message.contains(&format!(
                "{COLD_START_DEATH_THRESHOLD} consecutive transport failures"
            )),
        "the honest refusal must survive: {}",
        refusal.message
    );
}

/// Outside a readiness window the DR-55 rule is untouched: two strikes and the
/// endpoint is dead, which is what stops a round burning its budget on a game
/// that has already stopped answering.
#[tokio::test]
async fn outside_a_readiness_window_the_two_strike_rule_is_unchanged() {
    let (editor_endpoint, _) = a_closed_loopback_endpoint();
    let (game_endpoint, game_port) = a_closed_loopback_endpoint();
    let channel = McpChannel::new(editor_endpoint, 5, 0);
    channel
        .register_game_endpoint(game_record(game_endpoint.clone(), game_port))
        .await
        .expect("registration");

    for attempt in 1..ENDPOINT_DEATH_THRESHOLD {
        one_attempt(&channel, "running_game_get_scene_tree").await;
        let state = channel.endpoint_state(&game_endpoint).expect("state");
        assert!(!state.unavailable, "attempt {attempt}: {state:?}");
    }
    one_attempt(&channel, "running_game_get_scene_tree").await;
    let state = channel.endpoint_state(&game_endpoint).expect("state");
    assert!(state.unavailable, "{state:?}");
    assert_eq!(state.transport_failures_at_mark, ENDPOINT_DEATH_THRESHOLD);
}

/// The readiness poll is what opens the window, and it closes it again on its own
/// exit path — a call outside the wait must never inherit the tolerance.
#[tokio::test]
async fn the_readiness_poll_arms_and_closes_the_window() {
    let channel = FakeToolChannel::new();
    let outcome = wait_for_ready_matching(
        &channel,
        Role::Developer,
        "running_game_get_scene_tree",
        json!({}),
        0,
        0,
        None,
        |_| Ok(1),
    )
    .await;

    // The double answers successfully, so the poll stops on its first attempt —
    // and the window was still opened before it and closed after it.
    assert!(outcome.ok, "{outcome:?}");
    assert_eq!(
        channel.grace_calls(),
        vec![
            ("running_game_get_scene_tree".to_string(), true),
            ("running_game_get_scene_tree".to_string(), false),
        ],
        "the poll must open the cold-start window and close it on every exit path"
    );
}

/// The window is armed on the endpoint the call will really use, and the state
/// record says so — which is how a reader tells a readiness wait apart from an
/// ordinary call in the evidence.
#[tokio::test]
async fn the_window_is_armed_on_the_endpoint_the_call_uses() {
    let (channel, game_endpoint) = armed_game_channel().await;
    let state = channel.endpoint_state(&game_endpoint).expect("state");
    assert!(state.cold_start_grace, "{state:?}");
    assert_eq!(state.successes, 0);

    channel.arm_cold_start_grace("running_game_get_scene_tree", false);
    let state = channel.endpoint_state(&game_endpoint).expect("state");
    assert!(!state.cold_start_grace, "{state:?}");
}
