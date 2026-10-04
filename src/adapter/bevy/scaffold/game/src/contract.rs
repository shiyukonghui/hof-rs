//! The frozen reflectable contract (PRD §3-C2, DESIGN-DETAIL §3).
//!
//! Every type below is part of the observation surface: its **fully qualified
//! path including this crate's name** (`hof_game::contract::…`) is what the
//! adapter's semantic tools address, so renaming one of them is a contract
//! change, not a refactor.  Each type is declared once and registered with
//! [`register`], which `main` calls before the app runs.
//!
//! The seven surfaces:
//!
//! | surface | type | reflection |
//! |---|---|---|
//! | player marker | `Player` | `Component` |
//! | player position | `bevy_transform::components::transform::Transform` | engine-registered |
//! | ground state | `Grounded` | `Component` |
//! | coin count | `CoinCounter` | `Resource` |
//! | win flag | `WinFlag` | `Resource` |
//! | game frame counter | `FrameCounter` | `Resource` |
//! | input intent | `InputIntent` | `Resource` |
//!
//! `Transform` is Bevy's own and is registered by the engine, so it is not
//! declared here — the adapter adds it to the contract on that basis.

use bevy::prelude::*;

/// The runtime switch that runs the same binary with no window and no GPU
/// (`PRD.md` §3-C1).  The launcher sets it; a round is **always** headless
/// (SPIKE-2 measured 4.0 FPS windowed, which is too slow to see a jump arc).
pub const HEADLESS_ENV: &str = "HOF_GAME_HEADLESS";

/// Locates the player entity.  `world.query` filters on this path.
#[derive(Component, Reflect, Debug, Default)]
#[reflect(Component)]
pub struct Player;

/// The ground state.  Criterion ⑤ reads this *before* the take-off, so a jump
/// has a semantic basis instead of a guess from a y-coordinate.
#[derive(Component, Reflect, Debug, Clone, Copy)]
#[reflect(Component)]
pub struct Grounded {
    pub on_ground: bool,
}

impl Default for Grounded {
    fn default() -> Self {
        Self { on_ground: true }
    }
}

/// How many coins the player has collected.  `target` is informational; the
/// counter itself starts at 0 (PRD P2).
#[derive(Resource, Reflect, Debug, Clone, Copy)]
#[reflect(Resource)]
pub struct CoinCounter {
    pub coins: i64,
    pub target: i64,
}

impl Default for CoinCounter {
    fn default() -> Self {
        Self {
            coins: 0,
            target: 1,
        }
    }
}

/// The win flag: false until the goal is reached, and **one-way** (PRD P3).
#[derive(Resource, Reflect, Debug, Clone, Copy, Default)]
#[reflect(Resource)]
pub struct WinFlag {
    pub won: bool,
}

/// The game's own frame counter (D297 (b)): incremented by the game every
/// frame.  Every value a semantic tool returns carries this number as its
/// `frame`, so a claim about "the game advanced" is a claim about the game, not
/// about how often the adapter polled.
#[derive(Resource, Reflect, Debug, Clone, Copy, Default)]
#[reflect(Resource)]
pub struct FrameCounter {
    pub frames: u64,
}

/// The injection surface (PRD §3-C3).  It is a **level-triggered** resource:
/// `move_dir` stays where it was written until it is overwritten, while the
/// jump's edge is consumed by the game itself (`game::apply_input` latches
/// `jump_pressed`), so holding a direction really moves the player instead of
/// moving for a single frame.
#[derive(Resource, Reflect, Debug, Clone, Copy, Default)]
#[reflect(Resource)]
pub struct InputIntent {
    pub move_dir: i32,
    pub jump_pressed: bool,
}

/// Register every game-declared surface.  The adapter's contract check reads the
/// `register_type::<…>` declarations out of this crate's source, so this
/// function is what makes the check pass.
pub fn register(app: &mut App) {
    app.register_type::<Player>()
        .register_type::<Grounded>()
        .register_type::<CoinCounter>()
        .register_type::<WinFlag>()
        .register_type::<FrameCounter>()
        .register_type::<InputIntent>();
}
