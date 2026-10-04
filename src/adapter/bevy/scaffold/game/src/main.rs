//! `hof_game` — the scaffolded Bevy 0.19.1 game.
//!
//! This file is the **same binary in both modes** (PRD §3-C1): with
//! `HOF_GAME_HEADLESS` set it runs with no window and no render world, and
//! without it, it opens one real window.  Every round of the pipeline runs it
//! headless, because SPIKE-2 measured windowed mode at 4.0 FPS on this machine,
//! which is far too slow to observe a jump arc.
//!
//! Three facts from the spike reports are load-bearing here and must not be
//! "tidied away":
//!
//! 1. **`ScheduleRunnerPlugin` is mandatory in headless mode.**  Without it the
//!    app runs one frame and exits with code 0, and the BRP endpoint is never
//!    bound (SPIKE-2 C7).
//! 2. **`WgpuSettings { backends: None }` means "no render world at all"**, not
//!    "an empty one": Bevy never adds `ExtractPlugin`, so port 15703 does not
//!    exist.  The adapter depends on 15702 only.
//! 3. **The observation surface is declared, not inferred.**  `RemotePlugin` +
//!    `RemoteHttpPlugin` open 15702 on loopback with no authentication, which is
//!    why this build exists for development and CI only.

use std::time::Duration;

use bevy::app::ScheduleRunnerPlugin;
use bevy::prelude::*;
use bevy::remote::{http::RemoteHttpPlugin, RemotePlugin};
use bevy::render::{settings::WgpuSettings, RenderPlugin};
use bevy::window::ExitCondition;
use bevy::winit::WinitPlugin;

mod contract;
mod game;

fn main() {
    let headless = headless_requested();

    let mut window_plugin = WindowPlugin::default();
    let render_plugin = if headless {
        window_plugin.primary_window = None;
        window_plugin.exit_condition = ExitCondition::DontExit;
        window_plugin.close_when_requested = false;
        RenderPlugin {
            render_creation: WgpuSettings {
                backends: None,
                ..default()
            }
            .into(),
            ..default()
        }
    } else {
        RenderPlugin::default()
    };
    let builder = DefaultPlugins.set(window_plugin).set(render_plugin);

    let mut app = App::new();
    if headless {
        app.add_plugins(builder.build().disable::<WinitPlugin>());
        // Without this the process would run a single frame and exit.
        app.add_plugins(ScheduleRunnerPlugin::run_loop(Duration::from_secs_f64(
            1.0 / 60.0,
        )));
    } else {
        app.add_plugins(builder);
    }

    // The observation surface.  Same binary, both modes.
    app.add_plugins((RemotePlugin::default(), RemoteHttpPlugin::default()));

    app.init_resource::<contract::CoinCounter>()
        .init_resource::<contract::WinFlag>()
        .init_resource::<contract::FrameCounter>()
        .init_resource::<contract::InputIntent>();
    contract::register(&mut app);
    game::add(&mut app);

    watch_stdin();
    app.run();
}

/// The runtime switch: set (to anything but `0`) means headless.
fn headless_requested() -> bool {
    match std::env::var(contract::HEADLESS_ENV) {
        Ok(value) => value != "0",
        Err(_) => false,
    }
}

/// Exit the process when the launcher writes `quit` on stdin.
///
/// The launcher asks politely before it kills, and a game that ignored the line
/// would pay the full termination grace on every stop.  This is deliberately a
/// raw thread rather than a Bevy event: it must work in both the windowed and
/// the headless configuration, and it needs nothing from the ECS.
fn watch_stdin() {
    use std::io::BufRead;
    std::thread::spawn(|| {
        let stdin = std::io::stdin();
        for line in stdin.lock().lines() {
            match line {
                Ok(line) if line.trim() == "quit" => std::process::exit(0),
                Ok(_) => {}
                // EOF: the launcher closed the pipe without asking us to stop.
                Err(_) => break,
            }
        }
    });
}
