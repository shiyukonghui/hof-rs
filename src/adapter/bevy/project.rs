//! `BevyAdapter` as the round's [`ProjectAdapter`] (the build-time boundary) —
//! what `A₀` looks like, what the deterministic battery is, and who publishes
//! the game route to the roles.
//!
//! The split with `mod.rs`'s `GameAdapter` implementation is the design's
//! (DESIGN-DETAIL §1): `GameAdapter` is the *runtime capability* surface (build,
//! launch, read, inject, stop), and `ProjectAdapter` is the *project boundary*
//! the harness runtime knows (`initialize`, the battery, the gate steps, the
//! playbook, the round's game session).  This module is the second half, and it
//! is deliberately thin: everything expensive lives in [`super::round`], which
//! is where the records and the evidence come from.
//!
//! Two contract details are worth stating because they are easy to get wrong:
//!
//! * **The two gate steps keep the harness's own ids** (`editor_errors_baseline`,
//!   `play_scene_ready`).  They are not editor vocabulary any more; they are the
//!   two facts `adapter::evaluate_launchable` reads — "the candidate has no
//!   project-level defect" and "the candidate boots and answers" — and reusing
//!   the existing gate is what DESIGN-DETAIL §1 requires.
//! * **`BuildPolicy` is pinned to the lockfile the scaffold ships**, so the first
//!   build of a fresh `A₀` is already comparable with its own evidence
//!   (DESIGN-DETAIL §5).  A workspace whose lockfile cannot be read is pinned to
//!   nothing and says so, rather than comparing against an empty string.

use std::path::{Path, PathBuf};

use crate::adapter::bevy::contract::{check_game_crate_name, GAME_CRATE};
use crate::adapter::bevy::round::{self, FOREIGN_PROCESS_STDERR, SESSION_TIMEOUT};
use crate::adapter::bevy::{build, scaffold, BevyAdapter};
use crate::adapter::{BatteryRecord, DoctorItem, GameAdapter, Project, ProjectAdapter};
use crate::model::{ExecKind, ExecRecord, Role};
use crate::tools::endpoint::{GameEndpointRecord, SOURCE_ENGINE_DEFAULT};
use crate::tools::ToolChannel;

/// The tools the Bevy surface exposes to a role, in the order a `TOOLS.md`
/// reader sees them: the eight semantic tools (which the round's evidence comes
/// from) and the generic BRP verbs a role may use directly.
pub fn bevy_tool_names(role: Role) -> Vec<String> {
    let mut names: Vec<String> = crate::adapter::mcp::semantic::semantic_tool_names()
        .iter()
        .map(|name| (*name).to_string())
        .collect();
    names.extend(
        crate::adapter::mcp::generic::brp_method_names()
            .iter()
            .map(|name| (*name).to_string()),
    );
    match role {
        // The Planner owns no tool at all (DR-7 / §5.4): it reads the task and
        // writes a plan.
        Role::Planner => Vec::new(),
        Role::Developer => names,
        // The QA role keeps the observation surface and the read-only verbs; the
        // matrix is enforced by `tools::policy`, and this list is what is
        // advertised to it.
        Role::Tester => names
            .into_iter()
            .filter(|name| crate::tools::policy::tool_allowed(role, name))
            .collect(),
    }
}

/// The Tester's playbook: how the evidence this adapter produced is read, and
/// what "not observed" means.  It is injected into the Tester's view, so it has
/// to name real paths and real tools.
pub fn evidence_playbook() -> String {
    String::from(
        "## Evidence playbook (Bevy 0.19.1)\n\n\
         The game runs **inside its own process** and answers on `http://127.0.0.1:15702/` through \
         Bevy Remote Protocol. The runtime starts it before your window and stops it when the \
         round ends, and it is running the **frozen candidate**, so a call you make now is evidence \
         about the artifact you are judging.\n\n\
         ### What the battery already observed\n\n\
         - `.hoh/deterministic/battery.json` — one entry per step: `step_id`, the PRD ids it \
           `supports` (`P1..P5`), `ok`, and the observation text.\n\
         - `.hoh/deterministic/raw/e3_movement.json`, `raw/e3_coin_counter.json`, \
           `raw/e3_win_flag.json`, `raw/e3_jump_arc.json`, `raw/e3_grounded.json` — each holds the \
           criterion's observation, its readings, and the **verbatim** `bevy_*` requests and BRP \
           replies behind it.\n\
         - `.hoh/deterministic/raw/e3_movement_left.json`, `raw/e3_movement_release.json`, \
           `raw/e3_win_position.json`, `raw/e3_grounded_payload.json` — the four steps that were \
           missing in the first real round: the negative direction, the stop after `move_dir = 0`, \
           a transform sample at the win frame, and a `Grounded` payload read on its own.\n\
         - `.hoh/deterministic/raw/editor_errors_baseline.json` and `raw/play_scene_ready.json` — \
           the build and the launch: times, the frozen feature hash, the endpoint and the pid.\n\
         - `.hoh/deterministic/mcp-errors.jsonl` — every failed call, one JSON object per line.\n\n\
         `ok = false` means the evidence is **unavailable**: a claim that depends on it is a \
         `gap`, never `verified`.\n\n\
         ### Your own calls\n\n\
         You may call the semantic tools yourself, one call at a time:\n\n\
         - `bevy_player_transform` -> `{x, y, frame}`\n\
         - `bevy_grounded` -> `{grounded, frame}`\n\
         - `bevy_coin_counter` -> `{coins, frame}`\n\
         - `bevy_win_flag` -> `{won, frame}`\n\
         - `bevy_inject_move {dir: -1|0|1, level: true}` / `bevy_inject_jump {press: bool}`\n\
         - `bevy_wait_frames {n}` -> `{frame_after}`\n\
         - `bevy_health` -> `{alive, stderr_tail}`\n\n\
         Every reply carries the **game's own** frame counter (`hof_game::contract::FrameCounter`), \
         never a count of your polls. A jump is only a jump when the sampled heights rise **and** \
         fall; a monotone fall is not a jump, and `Grounded` must read true *before* the take-off \
         or the jump has no semantic basis.\n\n\
         ### The two rules\n\n\
         1. **A criterion you did not observe is a `gap`, never `verified`.** Carry the battery's \
            `not observed:` reasons forward verbatim.\n\
         2. **Never write a script that asserts your own success.** Evidence is the raw tool call \
            and its reply, recorded by the adapter under `.hoh/deterministic/raw/` — not a summary \
            you composed.\n",
    )
}

/// The `bevy.*` doctor items.
///
/// A workspace that has not been scaffolded yet is **not** a failure: `hoh init`
/// is the step that creates `A₀`, and the doctor runs before `run`'s own
/// `initialize`.  A workspace that *has* a `Cargo.toml` and gets it wrong is a
/// real defect and fails, because that is the case the contract check exists for.
pub fn doctor_items(workspace: &Path) -> Vec<DoctorItem> {
    let mut items = Vec::new();
    let manifest = workspace.join("Cargo.toml");
    match std::fs::read_to_string(&manifest) {
        Ok(text) => match check_game_crate_name(&text) {
            Ok(()) => items.push(DoctorItem {
                name: "bevy.game_crate".to_string(),
                ok: true,
                detail: format!(
                    "{} names the frozen crate `{GAME_CRATE}`",
                    manifest.display()
                ),
            }),
            Err(error) => items.push(DoctorItem {
                name: "bevy.game_crate".to_string(),
                ok: false,
                detail: error.to_string(),
            }),
        },
        Err(error) => items.push(DoctorItem {
            name: "bevy.game_crate".to_string(),
            ok: true,
            detail: format!(
                "{}: {error}; no Bevy project is scaffolded here yet (`hoh init` creates A0)",
                manifest.display()
            ),
        }),
    }
    let lockfile = workspace.join("Cargo.lock");
    match std::fs::read(&lockfile) {
        Ok(bytes) => items.push(DoctorItem {
            name: "bevy.lockfile".to_string(),
            ok: true,
            detail: format!(
                "{} sha256 {}",
                lockfile.display(),
                crate::runtime::policy::sha256_hex(&bytes)
            ),
        }),
        Err(error) => items.push(DoctorItem {
            name: "bevy.lockfile".to_string(),
            ok: true,
            detail: format!(
                "{}: {error}; the scaffold ships one, so a workspace without it has not been \
                 initialised yet",
                lockfile.display()
            ),
        }),
    }
    items.push(DoctorItem {
        name: "bevy.contract".to_string(),
        ok: true,
        detail: format!(
            "{} frozen semantic surface(s); contract sha256 {}; endpoint {}",
            crate::adapter::bevy::contract::CONTRACT.len(),
            crate::adapter::bevy::contract::contract_sha256(),
            crate::adapter::bevy::brp::endpoint()
        ),
    });
    items
}

/// The two `{prefix}` values a round's build policy uses: the frozen lockfile
/// pin, and a **shared persistent target directory** outside the workspace
/// (DESIGN-DETAIL §5: a warm build is ~12 s and a feature drift makes it ~236 s;
/// a target directory inside the workspace would also be an artifact the
/// Developer's tree hash had to exclude).
pub fn round_build_policy(workspace: &Path) -> build::BuildPolicy {
    let target = target_dir_for(workspace);
    build::BuildPolicy::pinned_if_available(workspace, Some(target))
}

/// The shared target directory a round builds into.
///
/// `HOF_BEVY_TARGET_DIR` wins; otherwise it is `<workspace>/../hof-bevy-shared-target`,
/// i.e. next to the project rather than inside it.  Never inside the workspace:
/// the workspace is the Developer's cwd and its hash is the artifact identity.
pub fn target_dir_for(workspace: &Path) -> PathBuf {
    if let Ok(explicit) = std::env::var("HOF_BEVY_TARGET_DIR") {
        if !explicit.trim().is_empty() {
            return PathBuf::from(explicit);
        }
    }
    let parent = workspace.parent().unwrap_or(workspace);
    parent.join("hof-bevy-shared-target")
}

#[async_trait::async_trait]
impl ProjectAdapter for BevyAdapter {
    /// `hoh init`: write the observation scaffold, keeping whatever is already
    /// there (see [`scaffold`]).
    fn initialize(&self, workspace: &Path) -> anyhow::Result<()> {
        scaffold::initialize(workspace)?;
        Ok(())
    }

    /// Caches only (DR-11): the target directory is a build cache, not an
    /// artifact.  It is deliberately **not** the workspace's own `target/`
    /// spelling alone — a round builds into a shared directory outside the
    /// workspace, and this entry covers a workspace that was built in place.
    fn cache_excludes(&self) -> Vec<String> {
        vec!["target".to_string()]
    }

    /// The deterministic pre-check: the candidate is a Bevy project that declares
    /// the frozen contract.
    ///
    /// It is **structural on purpose**.  The expensive half — `cargo build` and
    /// the headless launch — is `evidence_battery`'s, and running it twice per
    /// round would double a cost measured in minutes for no extra evidence.
    async fn build_check(
        &self,
        workspace: &Path,
        _tools: &dyn ToolChannel,
    ) -> anyhow::Result<Vec<ExecRecord>> {
        let manifest = workspace.join("Cargo.toml");
        let text = std::fs::read_to_string(&manifest)?;
        check_game_crate_name(&text)?;
        use crate::adapter::bevy::build::SourceContractPaths;
        let declared = SourceContractPaths::declared_for(workspace, GAME_CRATE)?;
        crate::adapter::bevy::contract::check_declared_contract_paths(
            &declared,
            &format!(
                "the game source under `{}`",
                workspace.join("src").display()
            ),
        )?;
        Ok(vec![ExecRecord {
            kind: ExecKind::Build,
            path: Some(".hoh/deterministic/build.json".to_string()),
            observation: format!(
                "the candidate is the frozen crate `{GAME_CRATE}` and declares {} of {} contract \
                 type path(s)",
                declared.len(),
                crate::adapter::bevy::contract::CONTRACT.len()
            ),
            candidate_id: String::new(),
        }])
    }

    /// DR-17: the real battery — build, launch headless, drive the five E3
    /// observations, stop, and write `runs/bevy-<round>/`.
    ///
    /// A task-level failure (no build, no endpoint, a dead game) is folded into
    /// the records as a red gate step with the verbatim reason, so the runtime
    /// can run its repair retry and then report the gate honestly.
    async fn evidence_battery(
        &self,
        workspace: &Path,
        _tools: &dyn ToolChannel,
    ) -> anyhow::Result<Vec<BatteryRecord>> {
        let mut peer = self.round_peer();
        let report = round::run(&mut peer, workspace);
        // The Tester reads the **workspace's** copy: its view is a copy of the
        // project, so `runs/bevy-<round>/` (which lives beside the repository's
        // other runs) is not in front of it.  The adapter contract is that the
        // raw payloads land under `<workspace>/.hoh/deterministic/raw/`; a
        // failure to write them is recorded, never swallowed.
        if let Err(error) = round::write_workspace_payloads(workspace, &report) {
            let mut records = report.records.clone();
            if let Some(record) = records
                .iter_mut()
                .find(|record| record.step_id == "editor_errors_baseline")
            {
                record.record.observation = format!(
                    "{}; the workspace evidence could not be written ({}), so the Tester has \
                     nothing to cite and must treat the battery's evidence as unavailable: {error}",
                    record.record.observation,
                    workspace.join(".hoh/deterministic").display()
                );
                record.ok = false;
            }
            return Ok(records);
        }
        Ok(report.records)
    }

    /// DR-70 ①: start the round's game session — one build, one headless launch,
    /// one published route that covers the Developer's and the Tester's windows.
    async fn start_round_game(
        &self,
        workspace: &Path,
        tools: &dyn ToolChannel,
    ) -> anyhow::Result<Option<GameEndpointRecord>> {
        let mut peer = self.round_peer();
        let prepared = peer.prepare(&Project::at(workspace.to_path_buf()))?;
        let game = peer.start(&prepared)?;
        let record = GameEndpointRecord {
            endpoint: peer.endpoint().to_string(),
            port: crate::tools::endpoint::port_of_endpoint(peer.endpoint()),
            source: SOURCE_ENGINE_DEFAULT.to_string(),
            pid: Some(game.pid),
        };
        // Install first, publish second (DR-71 ①): the route becomes visible to a
        // role's separate process only after this process has confirmed the game
        // answers — `start` returns only once the endpoint has.
        tools.register_game_endpoint(record.clone()).await?;
        if let Ok(mut slot) = self.round_game.lock() {
            *slot = peer.take_process();
        }
        Ok(Some(record))
    }

    /// DR-70 ①: stop it.  Called on **every** exit path of a round.
    async fn stop_round_game(&self, tools: &dyn ToolChannel) -> anyhow::Result<()> {
        let process = self.round_game.lock().ok().and_then(|mut slot| slot.take());
        if let Some(process) = process {
            // The stop report is the process's own; it is recorded in the round's
            // `launch.json` by the battery that started that game, and a failure
            // here cannot un-stop a game.
            let _ = process.stop();
        }
        tools.clear_game_endpoint().await;
        Ok(())
    }

    /// DR-78 ②: publish the route of a game a **role** announced.
    ///
    /// The Bevy tool surface has no "start a game" verb — the round starts the
    /// game itself in `start_round_game` — so in the normal flow this is never
    /// called and correctly answers `Ok(None)`.  When a reply *does* announce an
    /// endpoint (`endpoint` or `mcp_port`, the two shapes the announced record
    /// has), the readiness poll runs against **that** endpoint and publication
    /// happens only after it answers, so an unconfirmed game can never leave a
    /// route behind.
    async fn publish_role_started_game_route(
        &self,
        tools: &dyn ToolChannel,
        _role: Role,
        announced: &serde_json::Value,
    ) -> anyhow::Result<Option<GameEndpointRecord>> {
        let endpoint = announced
            .get("endpoint")
            .and_then(serde_json::Value::as_str)
            .map(ToOwned::to_owned)
            .or_else(|| {
                announced
                    .get("mcp_port")
                    .and_then(serde_json::Value::as_u64)
                    .map(|port| crate::tools::endpoint::endpoint_for_port(port as u16))
            });
        let Some(endpoint) = endpoint else {
            // Nothing was announced: this adapter has no role-driven start, and
            // publishing the adapter's own endpoint here would be inventing a
            // fact about a game nobody started.
            return Ok(None);
        };
        let record = GameEndpointRecord {
            endpoint: endpoint.clone(),
            port: crate::tools::endpoint::port_of_endpoint(&endpoint),
            source: SOURCE_ENGINE_DEFAULT.to_string(),
            pid: announced
                .get("pid")
                .and_then(serde_json::Value::as_u64)
                .map(|pid| pid as u32),
        };
        tools.install_game_endpoint(record.clone()).await?;
        round::wait_for_endpoint(
            &endpoint,
            std::time::Duration::from_millis(
                crate::adapter::bevy::build::ENDPOINT_READY_BUDGET_MILLIS,
            ),
            crate::adapter::bevy::brp::READY_POLL_INTERVAL,
        )
        .map_err(|reason| {
            anyhow::anyhow!(
                "the announced game on {endpoint} never became ready, so its route stays \
                 unpublished and no later process can reach it: {reason}"
            )
        })?;
        tools.publish_game_endpoint().await?;
        Ok(Some(record))
    }

    /// DR-37: is the Developer's artifact at least usable?  For a Bevy round the
    /// artifact is the project, and "usable" means: the frozen crate name, the
    /// frozen manifest, the frozen lockfile, and every frozen contract path.
    fn developer_artifact_valid(&self, workspace: &Path) -> bool {
        self.developer_artifact_defects(workspace).is_empty()
    }

    /// DR-86 ②: the verbatim defects behind the answer above.
    fn developer_artifact_defects(&self, workspace: &Path) -> Vec<String> {
        let mut defects = Vec::new();
        let manifest = workspace.join("Cargo.toml");
        match std::fs::read_to_string(&manifest) {
            Ok(text) => match check_game_crate_name(&text) {
                Ok(()) => {}
                Err(error) => defects.push(error.to_string()),
            },
            Err(error) => defects.push(format!(
                "`{}` could not be read: {error}",
                manifest.display()
            )),
        }
        if build::lockfile_sha256(&workspace.join("Cargo.lock")).is_err() {
            defects.push(format!(
                "`{}` is missing: the build contract freezes the lockfile (DESIGN-DETAIL §5) and \
                 the scaffold from `hoh init` ships one",
                workspace.join("Cargo.lock").display()
            ));
        }
        match build::SourceContractPaths::declared_for(workspace, GAME_CRATE)
            .map_err(|error| error.to_string())
        {
            Ok(declared) => {
                if let Err(error) = crate::adapter::bevy::contract::check_declared_contract_paths(
                    &declared,
                    "the game source",
                ) {
                    defects.push(error.to_string());
                }
            }
            Err(error) => defects.push(error),
        }
        defects
    }

    fn evidence_playbook(&self) -> String {
        evidence_playbook()
    }

    fn tool_policy(&self, role: Role) -> Vec<String> {
        bevy_tool_names(role)
    }

    /// DR-44: Bevy is not a separate engine **binary** — it is compiled into the
    /// game — so there is no engine identity to probe and no `engine_identity`
    /// gate step.  The identity that matters (which binary produced this
    /// evidence) is the game binary, and the round records it in `launch.json`
    /// and hashes the lockfile that produced it.
    fn engine_kind(&self) -> &'static str {
        crate::adapter::engine::ENGINE_KIND_BEVY
    }

    /// Round-1 write-path batch: the round's shared build directory, so a role's
    /// own `cargo build --offline` is a **warm** rebuild instead of a second
    /// cold tree inside the project.
    fn build_target_dir(&self) -> Option<PathBuf> {
        Some(target_dir_for(&self.workspace))
    }

    fn doctor(&self, workspace: &Path) -> anyhow::Result<Vec<DoctorItem>> {
        Ok(doctor_items(workspace))
    }
}

/// The MCP session a **role's** separate process uses: the adapter's own
/// `GameAdapter` machinery is not reachable from another process, so a role
/// builds a session against the published endpoint.
pub fn role_session(endpoint: &str, pid: Option<u32>) -> round::Session {
    let mut session = round::Session::new(endpoint, SESSION_TIMEOUT);
    if let Some(pid) = pid {
        session.install_process(pid, FOREIGN_PROCESS_STDERR.to_string());
    }
    session
}

/// The evidence root a round writes to, when the caller has a configured runs
/// directory.
pub fn evidence_root_of(runs_dir: &Path) -> PathBuf {
    runs_dir
        .parent()
        .map(Path::to_path_buf)
        .unwrap_or_else(|| PathBuf::from("."))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::adapter::bevy::contract::CONTRACT;

    #[test]
    fn the_tester_is_advertised_the_observation_surface_and_the_planner_nothing() {
        let developer = bevy_tool_names(Role::Developer);
        assert!(developer.contains(&"bevy_coin_counter".to_string()));
        assert!(developer.contains(&"world.query".to_string()));
        let tester = bevy_tool_names(Role::Tester);
        for tool in [
            "bevy_player_transform",
            "bevy_grounded",
            "bevy_coin_counter",
            "bevy_win_flag",
            "bevy_wait_frames",
            "bevy_health",
            "bevy_inject_move",
            "bevy_inject_jump",
        ] {
            assert!(
                tester.contains(&tool.to_string()),
                "the Tester needs `{tool}`"
            );
        }
        assert!(bevy_tool_names(Role::Planner).is_empty());
    }

    #[test]
    fn the_playbook_names_the_real_paths_and_the_not_observed_rule() {
        let playbook = evidence_playbook();
        for needed in [
            "bevy_coin_counter",
            ".hoh/deterministic/raw/",
            "not observed",
            "frame",
            "monotone fall",
        ] {
            assert!(
                playbook.contains(needed),
                "the playbook must mention `{needed}`"
            );
        }
        // The Tester reads a **view of the workspace**, so the round directory
        // beside the repository's other runs is not in front of it: the playbook
        // must never send it to a path it cannot open.
        assert!(
            !playbook.contains("runs/bevy-"),
            "the playbook must not cite the repository-side round directory:\n{playbook}"
        );
    }

    #[test]
    fn the_round_build_policy_is_pinned_when_the_scaffold_is_there_and_never_builds_inside_the_workspace(
    ) {
        let directory = tempfile::tempdir().expect("a temporary workspace");
        let workspace = directory.path().join("game");
        scaffold::initialize(&workspace).expect("the scaffold");
        let policy = round_build_policy(&workspace);
        assert!(policy.is_locked(), "the scaffold ships a lockfile");
        let target = policy
            .target_dir
            .clone()
            .expect("a shared target directory");
        assert!(
            !target.starts_with(&workspace),
            "the target directory must not be inside the artifact: {}",
            target.display()
        );
        assert!(policy.offline, "a round never builds with the network on");

        let empty = tempfile::tempdir().expect("a temporary workspace");
        assert!(
            !round_build_policy(empty.path()).is_locked(),
            "a workspace with no lockfile is explicitly unpinned, never pinned to an empty string"
        );
    }

    #[test]
    fn the_doctor_items_do_not_fail_an_unscaffolded_workspace_but_do_fail_a_wrong_crate() {
        let directory = tempfile::tempdir().expect("a temporary workspace");
        let items = doctor_items(directory.path());
        assert!(items.iter().all(|item| item.ok), "{items:?}");
        assert!(items.iter().any(|item| item.detail.contains("hoh init")));
        std::fs::write(
            directory.path().join("Cargo.toml"),
            "[package]\nname = \"some_other_game\"\n",
        )
        .unwrap();
        let items = doctor_items(directory.path());
        assert!(
            items.iter().any(|item| !item.ok),
            "a differently named crate is a real defect: {items:?}"
        );
    }

    #[test]
    fn the_artifact_defects_name_each_missing_contract_path() {
        let directory = tempfile::tempdir().expect("a temporary workspace");
        let workspace = directory.path();
        std::fs::write(
            workspace.join("Cargo.toml"),
            "[package]\nname = \"hof_game\"\n",
        )
        .unwrap();
        std::fs::create_dir_all(workspace.join("src")).unwrap();
        std::fs::write(workspace.join("src/main.rs"), "fn main() {}\n").unwrap();
        let defects = BevyAdapter::at(workspace).developer_artifact_defects(workspace);
        let joined = defects.join(" | ");
        assert!(joined.contains("Cargo.lock"), "{joined}");
        assert!(
            joined.contains("Grounded"),
            "every missing path is named: {joined}"
        );
        assert_eq!(
            defects.len(),
            2,
            "the lockfile and the contract paths, nothing invented: {joined}"
        );
        assert_eq!(CONTRACT.len(), 8);
    }
}
