//! The `A₀` scaffold `hoh init` writes for a Bevy project (PRD §3-C1, §3-C2).
//!
//! SPIKE-1 §2.4-5 is the reason this module exists at all: "a developer starting
//! from an empty project would have to invent the vocabulary the tools address",
//! so `A₀` has to carry the **observation scaffold** — the `bevy_remote` feature,
//! the two plugins, the schedule runner (without it the process exits after one
//! frame and never binds its endpoint), the runtime headless switch, and the
//! seven reflectable contract surfaces the semantic layer addresses by fully
//! qualified path.
//!
//! The files themselves live next to this module under `scaffold/game/**` and
//! are embedded with `include_str!`, so there is exactly **one** copy of the
//! game: the one `hoh init` writes is byte-for-byte the one this repository
//! reviews and tests.
//!
//! Two properties are load-bearing:
//!
//! * **Idempotent and non-destructive.**  A file that already exists is kept —
//!   verbatim — because `initialize` also runs at the start of every round
//!   (`run_loop::run_inner`), and overwriting there would silently undo the
//!   Developer's increment.
//! * **The lockfile ships with `A₀`.**  The build contract freezes `Cargo.lock`
//!   (DESIGN-DETAIL §5) and `BevyAdapter::prepare` refuses to build without one,
//!   so a scaffold that let cargo create it on the first build would make the
//!   round's first build incomparable with its own evidence.  `Cargo.lock` is
//!   therefore part of the scaffold.

use std::path::{Path, PathBuf};

/// The scaffold's files, relative to the project root, in the order they are
/// written.  The list is the contract of `hoh init`.
pub const SCAFFOLD_FILES: &[&str] = &[
    "Cargo.toml",
    "Cargo.lock",
    "src/main.rs",
    "src/contract.rs",
    "src/game.rs",
];

/// `/target` is a build cache, never a project artifact (DR-11).
pub const GITIGNORE: &str = "/target\n";

/// The bytes of one scaffold file.
pub fn contents(rel: &str) -> Option<&'static str> {
    match rel {
        "Cargo.toml" => Some(include_str!("scaffold/game/Cargo.toml")),
        "Cargo.lock" => Some(include_str!("scaffold/game/Cargo.lock")),
        "src/main.rs" => Some(include_str!("scaffold/game/src/main.rs")),
        "src/contract.rs" => Some(include_str!("scaffold/game/src/contract.rs")),
        "src/game.rs" => Some(include_str!("scaffold/game/src/game.rs")),
        _ => None,
    }
}

/// Every `.rs` file of the scaffold, concatenated: what the adapter's
/// contract-path reader sees when it reads the game's own source.
pub fn game_source() -> String {
    let mut text = String::new();
    for rel in ["src/main.rs", "src/contract.rs", "src/game.rs"] {
        if let Some(source) = contents(rel) {
            text.push_str(source);
            text.push('\n');
        }
    }
    text
}

/// The scaffold files that are **absent** from a workspace.  `hoh init` writes
/// exactly these and nothing else.
pub fn missing(workspace: &Path) -> Vec<&'static str> {
    SCAFFOLD_FILES
        .iter()
        .copied()
        .filter(|rel| !workspace.join(rel).is_file())
        .collect()
}

/// Is every scaffold file present?  `false` means `hoh init` still has work to
/// do; it says nothing about whether the files are the scaffold's bytes.
pub fn all_present(workspace: &Path) -> bool {
    missing(workspace).is_empty()
}

/// Write `A₀` into `workspace`: every missing scaffold file, plus `.gitignore`.
///
/// Existing files are **kept**, so this is safe to call on every round.  Returns
/// the paths that were created, in order — the round records them instead of
/// guessing what `initialize` did.
pub fn initialize(workspace: &Path) -> anyhow::Result<Vec<PathBuf>> {
    std::fs::create_dir_all(workspace)?;
    let mut written = Vec::new();
    for rel in SCAFFOLD_FILES {
        let target = workspace.join(rel);
        if target.is_file() {
            continue;
        }
        let Some(bytes) = contents(rel) else {
            anyhow::bail!("the scaffold declares `{rel}` but carries no bytes for it");
        };
        if let Some(parent) = target.parent() {
            std::fs::create_dir_all(parent)?;
        }
        std::fs::write(&target, bytes)?;
        written.push(target);
    }
    let gitignore = workspace.join(".gitignore");
    if !gitignore.is_file() {
        std::fs::write(&gitignore, GITIGNORE)?;
        written.push(gitignore);
    }
    Ok(written)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::adapter::bevy::build::{BEVY_VERSION, FROZEN_FEATURES};
    use crate::adapter::bevy::contract::{
        check_declared_contract_paths, check_game_crate_name, CONTRACT,
    };
    use crate::adapter::bevy::launch::HEADLESS_ENV;

    #[test]
    fn the_scaffold_declares_every_frozen_contract_path() {
        let declared =
            crate::adapter::bevy::build::SourceContractPaths::declared_paths_in(&game_source());
        check_declared_contract_paths(&declared, "the scaffold's own source")
            .expect("A0 must declare every frozen contract path");
        assert_eq!(declared.len(), CONTRACT.len());
    }

    #[test]
    fn the_scaffold_is_the_frozen_crate_with_the_frozen_feature_set() {
        check_game_crate_name(contents("Cargo.toml").expect("a manifest"))
            .expect("the scaffold must be named hof_game");
        let manifest = contents("Cargo.toml").unwrap();
        assert!(
            manifest.contains(&format!("version = \"{BEVY_VERSION}\"")),
            "the pinned Bevy version must be in the manifest: {manifest}"
        );
        for feature in FROZEN_FEATURES {
            assert!(
                manifest.contains(&format!("\"{feature}\"")),
                "the frozen feature `{feature}` must be enabled: {manifest}"
            );
        }
        // The feature set is what the adapter hashes; a drift here would make the
        // scaffold unbuildable by `prepare` without saying why.
        assert!(
            manifest.contains("features = [\"bevy_remote\"]"),
            "{manifest}"
        );
    }

    #[test]
    fn the_scaffold_carries_the_plugins_the_runner_and_the_headless_switch() {
        let main = contents("src/main.rs").expect("a main");
        for needed in [
            "RemotePlugin::default()",
            "RemoteHttpPlugin::default()",
            "ScheduleRunnerPlugin::run_loop",
            "backends: None",
            "disable::<WinitPlugin>()",
        ] {
            assert!(main.contains(needed), "`{needed}` is missing from main.rs");
        }
        // The switch the launcher sets is the switch the game reads: two string
        // literals in two crates, so a pin is the only thing that keeps them
        // together.
        assert!(
            contents("src/contract.rs")
                .unwrap()
                .contains(&format!("\"{HEADLESS_ENV}\"")),
            "the game must read `{HEADLESS_ENV}`, the variable the launcher sets"
        );
    }

    #[test]
    fn the_scaffold_spawns_the_player_before_the_first_observation() {
        let source = game_source();
        assert!(
            source.contains("commands.spawn(("),
            "the scene must spawn a player"
        );
        assert!(
            source.contains("Player,"),
            "the spawned entity carries the frozen marker"
        );
        assert!(
            source.contains("Grounded::default()"),
            "the spawned entity carries the ground state"
        );
        // The frame counter is the game's own clock: nothing else may be the
        // source of a reading's `frame`.
        assert!(source.contains("counter.frames = counter.frames.saturating_add(1);"));
    }

    #[test]
    fn initialize_writes_the_missing_files_and_keeps_what_is_there() {
        let directory = tempfile::tempdir().expect("a temporary workspace");
        let workspace = directory.path();
        let written = initialize(workspace).expect("the scaffold is written");
        assert_eq!(
            written.len(),
            SCAFFOLD_FILES.len() + 1,
            "files plus .gitignore"
        );
        assert!(all_present(workspace));
        for rel in SCAFFOLD_FILES {
            let on_disk = std::fs::read_to_string(workspace.join(rel)).expect("a written file");
            assert_eq!(
                on_disk,
                contents(rel).expect("the scaffold's bytes"),
                "`{rel}` was not written verbatim"
            );
        }
        // A second call writes nothing...
        assert_eq!(
            initialize(workspace).expect("idempotent"),
            Vec::<PathBuf>::new()
        );
        // ...and a file the developer edited survives it.
        std::fs::write(workspace.join("src/game.rs"), "// the developer was here\n").unwrap();
        std::fs::remove_file(workspace.join("Cargo.toml")).unwrap();
        let written = initialize(workspace).expect("a repair pass");
        assert_eq!(written, vec![workspace.join("Cargo.toml")]);
        assert_eq!(
            std::fs::read_to_string(workspace.join("src/game.rs")).unwrap(),
            "// the developer was here\n",
            "initialize must never overwrite a developer's increment"
        );
    }

    #[test]
    fn initialize_creates_only_paths_below_the_workspace_it_is_given() {
        let directory = tempfile::tempdir().expect("a temporary workspace");
        let workspace = directory.path().join("nested").join("game");
        let written = initialize(&workspace).expect("the scaffold is written");
        for path in written {
            assert!(
                path.starts_with(&workspace),
                "{} escaped the workspace",
                path.display()
            );
        }
    }

    #[test]
    fn the_scaffold_lockfile_is_a_lockfile() {
        let lock = contents("Cargo.lock").expect("a lockfile");
        assert!(
            lock.contains("name = \"bevy\""),
            "the lockfile must lock bevy itself"
        );
        assert!(
            lock.matches("[[package]]").count() > 100,
            "a resolved Bevy graph is hundreds of packages, got {}",
            lock.matches("[[package]]").count()
        );
        assert!(
            lock.contains("version = 4"),
            "the lockfile must be the format this cargo writes"
        );
    }
}
