//! The game's behaviour: a horizontal move, one coin, one goal, a jump, and the
//! ground state that gives the jump a semantic basis (PRD §2 P1..P5).
//!
//! The numbers below are the level's design, not the contract: a Developer is
//! expected to change them (and this file) as the round's increment.  Only the
//! type paths in [`crate::contract`] are frozen.
//!
//! Two properties are deliberate because the observation battery depends on
//! them:
//!
//! * **`move_dir` is a held level.**  The velocity is derived from it every
//!   frame, so writing `0` stops the player immediately and no inertia drifts
//!   (PRD P1).  Clearing it every frame is what SPIKE-1 measured as a 2 px move
//!   over 0.4 s.
//! * **The jump's edge is consumed by the game.**  `jump_pressed` is a level, so
//!   the game latches it: one press is one jump, and holding it does not bounce.

use bevy::prelude::*;

use crate::contract::{CoinCounter, FrameCounter, Grounded, InputIntent, Player, WinFlag};

/// The ground plane's height.  Also the player's starting height.
pub const GROUND_Y: f32 = -200.0;
/// Horizontal speed, in pixels per second.
pub const MOVE_SPEED: f32 = 200.0;
/// The upwards impulse, in pixels per second.
pub const JUMP_SPEED: f32 = 300.0;
/// Downwards acceleration, in pixels per second squared.
pub const GRAVITY: f32 = 1200.0;
/// Where the coin sits on the x axis.
pub const COIN_X: f32 = 60.0;
/// Where the goal sits on the x axis.
pub const GOAL_X: f32 = 100.0;
/// The largest timestep one frame may integrate, so a slow first frame cannot
/// teleport the player past the coin or the goal.
pub const MAX_STEP_SECONDS: f32 = 1.0 / 30.0;

/// The player's velocity.  Private to the game; nothing observes it.
#[derive(Component, Debug, Default)]
struct Velocity {
    x: f32,
    y: f32,
}

/// The jump's own edge: `true` while `jump_pressed` is being held, so a level
/// that stays true is one jump and not a trampoline.
#[derive(Component, Debug, Default)]
struct JumpLatch(bool);

pub fn add(app: &mut App) {
    app.add_systems(Startup, spawn_scene);
    app.add_systems(
        Update,
        (
            count_frames,
            apply_input,
            integrate,
            collect_coin_and_win,
        )
            .chain(),
    );
}

fn spawn_scene(mut commands: Commands) {
    // The player: the frozen marker, an engine `Transform`, the ground state and
    // the game's own private components.
    commands.spawn((
        Player,
        Transform::from_xyz(0.0, GROUND_Y, 0.0),
        Grounded::default(),
        Velocity::default(),
        JumpLatch::default(),
    ));
}

/// The game's own clock (D297 (b)): every semantic tool reports this value as
/// `frame`.
fn count_frames(mut counter: ResMut<FrameCounter>) {
    counter.frames = counter.frames.saturating_add(1);
}

/// Turn the held intent into velocity, and consume the jump's edge.
fn apply_input(
    intent: Res<InputIntent>,
    mut player: Query<(&mut Velocity, &mut Grounded, &mut JumpLatch), With<Player>>,
) {
    for (mut velocity, mut grounded, mut latch) in &mut player {
        velocity.x = MOVE_SPEED * intent.move_dir as f32;
        if intent.jump_pressed && grounded.on_ground && !latch.0 {
            velocity.y = JUMP_SPEED;
            grounded.on_ground = false;
        }
        latch.0 = intent.jump_pressed;
    }
}

/// Integrate one frame of motion and settle on the ground.
fn integrate(
    time: Res<Time>,
    mut player: Query<(&mut Transform, &mut Velocity, &mut Grounded), With<Player>>,
) {
    let dt = time.delta_secs().min(MAX_STEP_SECONDS);
    for (mut transform, mut velocity, mut grounded) in &mut player {
        transform.translation.x += velocity.x * dt;
        velocity.y -= GRAVITY * dt;
        transform.translation.y += velocity.y * dt;
        if transform.translation.y <= GROUND_Y {
            transform.translation.y = GROUND_Y;
            velocity.y = 0.0;
            grounded.on_ground = true;
        } else {
            grounded.on_ground = false;
        }
    }
}

/// One coin, collected once; one goal, which latches the win flag (PRD P2, P3).
fn collect_coin_and_win(
    mut coins: ResMut<CoinCounter>,
    mut win: ResMut<WinFlag>,
    player: Query<&Transform, With<Player>>,
) {
    for transform in &player {
        if coins.coins == 0 && transform.translation.x >= COIN_X {
            coins.coins += 1;
        }
        if transform.translation.x >= GOAL_X {
            win.won = true;
        }
    }
}
