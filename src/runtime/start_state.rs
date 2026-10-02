//! DR-21: a clean, reproducible starting point.
//!
//! The first smoke run inherited a workspace polluted by two earlier attempts,
//! so iterations were not comparable.  `--fresh-workspace` rebuilds `A₀` from
//! `initialize`; `--reset-workspace` restores this run's `A₀` snapshot.
//!
//! The cleanup is deliberately paranoid: it may only touch the **configured**
//! workspace directory, that directory must exist and be a directory, and
//! symlinks are removed rather than followed — a failure must be an error, not
//! a deleted wrong tree.

use std::path::Path;

use serde::{Deserialize, Serialize};

use crate::adapter::ProjectAdapter;
use crate::errors::HofError;
use crate::runtime::snapshot::VersionStore;

/// How the workspace was prepared for this run.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum StartStateMode {
    /// The workspace was emptied and `initialize` rebuilt `A₀`.
    Fresh,
    /// The workspace was rolled back to this run's `A₀` snapshot.
    Reset,
    /// The workspace was used as it was found.
    AsIs,
}

/// `meta.json.start_state` (DR-21).
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct StartState {
    pub mode: StartStateMode,
    pub version_id: Option<String>,
}

impl StartState {
    pub fn as_is() -> Self {
        Self {
            mode: StartStateMode::AsIs,
            version_id: None,
        }
    }

    pub fn fresh() -> Self {
        Self {
            mode: StartStateMode::Fresh,
            version_id: None,
        }
    }

    pub fn reset(version_id: String) -> Self {
        Self {
            mode: StartStateMode::Reset,
            version_id: Some(version_id),
        }
    }
}

impl Default for StartState {
    fn default() -> Self {
        Self::as_is()
    }
}

/// Assert that `workspace` is a real directory that may be emptied.
///
/// A missing path is an error rather than "already empty": silently creating a
/// directory would make `--fresh-workspace` impossible to tell apart from a
/// typo, and `remove_dir_all` on an unexpected path is exactly the failure mode
/// this guard exists to prevent.
fn assert_purgeable(workspace: &Path) -> anyhow::Result<()> {
    let metadata = std::fs::symlink_metadata(workspace).map_err(|error| {
        HofError::Config(format!(
            "--fresh-workspace: the configured workspace {} does not exist ({error}); create it \
             first, or omit the flag",
            workspace.display()
        ))
    })?;
    if metadata.file_type().is_symlink() {
        return Err(HofError::Config(format!(
            "--fresh-workspace: refusing to purge {} because it is a symlink",
            workspace.display()
        ))
        .into());
    }
    if !metadata.is_dir() {
        return Err(HofError::Config(format!(
            "--fresh-workspace: refusing to purge {} because it is not a directory",
            workspace.display()
        ))
        .into());
    }
    Ok(())
}

/// Remove every entry of `workspace` without following symlinks.
fn purge_contents(workspace: &Path) -> anyhow::Result<()> {
    for entry in std::fs::read_dir(workspace)? {
        let entry = entry?;
        let path = entry.path();
        let metadata = std::fs::symlink_metadata(&path)?;
        if metadata.file_type().is_symlink() {
            // Remove the link itself, never the target.  On Windows a
            // directory symlink must be removed with `remove_dir`.
            #[cfg(windows)]
            if path.is_dir() {
                std::fs::remove_dir(&path)?;
                continue;
            }
            std::fs::remove_file(&path)?;
        } else if metadata.is_file() {
            std::fs::remove_file(&path)?;
        } else if metadata.is_dir() {
            // `remove_dir_all` removes nested symlinks instead of traversing
            // them, so the target of a link can never be deleted here.
            std::fs::remove_dir_all(&path)?;
        }
    }
    Ok(())
}

/// DR-21 `--fresh-workspace`: empty the workspace and rebuild `A₀`.
///
/// DR-81 ④ — the measured precondition: [`purge_contents`] removes **every**
/// entry, including the whole `.godot/` cache tree, and `adapter.initialize`
/// rebuilds only the `A₀` product (`project.godot`, `scenes/`, `scripts/`) — it
/// never recreates `.godot/`.  Godot creates that tree when it (re)imports a
/// project at startup, so if the editor was already pointed at this workspace
/// (which is the order the smoke books mandate: empty directory → `init` → point
/// the editor → `run`) then a `--fresh-workspace` run deletes the directory the
/// running editor holds open, and its next cache write answers
/// `Cannot create file 'res://.godot/editor/filesystem_cache10'. Check user
/// write permissions.` (`smoke-t14`).
///
/// The precondition is therefore: **either restart/close the editor after a
/// `--fresh-workspace` purge, or expect that one editor-infrastructure line on
/// the editor it left running.**  The line names nothing in the produced project
/// and is classified as editor infrastructure by the launch gate (DR-81 ①), so it
/// must not freeze an otherwise clean project.
pub fn fresh_workspace(workspace: &Path, adapter: &dyn ProjectAdapter) -> anyhow::Result<()> {
    assert_purgeable(workspace)?;
    purge_contents(workspace)?;
    adapter.initialize(workspace)
}

/// DR-21 `--reset-workspace`: roll the workspace back to this run's `A₀`.
///
/// The snapshot is looked up **before** anything is touched, so a run without
/// an `A₀` fails without modifying the workspace.
pub fn reset_workspace(
    workspace: &Path,
    run_dir: &Path,
    excludes: &[String],
) -> anyhow::Result<String> {
    let store = VersionStore::new(run_dir.join("versions"));
    let a0 = store
        .read_index()?
        .into_iter()
        .find(|entry| entry.iteration == 0 && entry.role == "init")
        .ok_or_else(|| {
            HofError::Config(format!(
                "--reset-workspace: run {} has no A0 snapshot under {}; nothing was changed",
                run_dir.display(),
                store.root.display()
            ))
        })?;
    if !store.root.join(&a0.version_id).is_dir() {
        return Err(HofError::Config(format!(
            "--reset-workspace: the A0 snapshot {} is missing from {}; nothing was changed",
            a0.version_id,
            store.root.display()
        ))
        .into());
    }
    store.rollback(workspace, excludes, &a0.version_id)?;
    Ok(a0.version_id)
}
