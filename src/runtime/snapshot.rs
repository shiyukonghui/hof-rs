//! `VersionStore`: content-addressed snapshots, a version index and rollback.
//!
//! The store never depends on git.  `version_id` is exactly
//! [`crate::runtime::policy::hash_tree`] of the workspace, i.e. the same value
//! the runtime uses as `candidate_id` — there is deliberately only one hashing
//! implementation in this crate.

use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

use serde::{Deserialize, Serialize};

use crate::runtime::policy::hash_tree;
use crate::runtime::view::copy_tree;

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct VersionEntry {
    pub version_id: String,
    pub candidate_id: String,
    pub iteration: u32,
    pub role: String,
    pub verified: bool,
    pub parent: Option<String>,
    pub created_at: u64,
    pub note: String,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
struct VersionIndex {
    schema: u32,
    versions: Vec<VersionEntry>,
}

impl Default for VersionIndex {
    fn default() -> Self {
        Self {
            schema: 1,
            versions: Vec::new(),
        }
    }
}

#[derive(Clone, Debug)]
pub struct VersionStore {
    pub root: PathBuf,
}

fn now_seconds() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|duration| duration.as_secs())
        .unwrap_or(0)
}

impl VersionStore {
    pub fn new(root: impl Into<PathBuf>) -> Self {
        Self { root: root.into() }
    }

    pub fn index_path(&self) -> PathBuf {
        self.root.join("index.json")
    }

    /// Snapshot the tree; returns the recorded entry.  Copying is skipped when
    /// the content-addressed directory already exists.
    pub fn snapshot(
        &self,
        workspace: &Path,
        excludes: &[String],
        iteration: u32,
        note: &str,
    ) -> anyhow::Result<VersionEntry> {
        self.snapshot_role(workspace, excludes, iteration, "", note)
    }

    /// Same as [`VersionStore::snapshot`] but records the producing role.
    pub fn snapshot_role(
        &self,
        workspace: &Path,
        excludes: &[String],
        iteration: u32,
        role: &str,
        note: &str,
    ) -> anyhow::Result<VersionEntry> {
        let version_id = hash_tree(workspace, excludes)?;
        let target = self.root.join(&version_id);
        if !target.is_dir() {
            std::fs::create_dir_all(&target)?;
            copy_tree(workspace, &target, excludes)?;
        }
        let existing = self.read_index()?;
        let entry = VersionEntry {
            version_id: version_id.clone(),
            candidate_id: version_id,
            iteration,
            role: role.to_string(),
            verified: false,
            parent: existing.last().map(|item| item.version_id.clone()),
            created_at: now_seconds(),
            note: note.to_string(),
        };
        self.append_index(&entry)?;
        Ok(entry)
    }

    pub fn append_index(&self, entry: &VersionEntry) -> anyhow::Result<()> {
        std::fs::create_dir_all(&self.root)?;
        let mut versions = self.read_index()?;
        versions.push(entry.clone());
        let index = VersionIndex {
            schema: 1,
            versions,
        };
        let serialized = serde_json::to_string_pretty(&index)?;
        write_atomic(&self.index_path(), serialized.as_bytes())
    }

    pub fn read_index(&self) -> anyhow::Result<Vec<VersionEntry>> {
        let path = self.index_path();
        if !path.exists() {
            return Ok(Vec::new());
        }
        let raw = std::fs::read_to_string(&path)?;
        if raw.trim().is_empty() {
            return Ok(Vec::new());
        }
        let index: VersionIndex = serde_json::from_str(&raw)?;
        Ok(index.versions)
    }

    /// Restore `workspace` to the snapshot named by `version_id`, then verify
    /// that the restored tree hashes back to that id.
    pub fn rollback(
        &self,
        workspace: &Path,
        excludes: &[String],
        version_id: &str,
    ) -> anyhow::Result<()> {
        let source = self.root.join(version_id);
        if !source.is_dir() {
            anyhow::bail!(
                "version `{version_id}` has no snapshot at {}",
                source.display()
            );
        }
        std::fs::create_dir_all(workspace)?;
        purge_covered(workspace, "", excludes)?;
        copy_tree(&source, workspace, excludes)?;
        let restored = hash_tree(workspace, excludes)?;
        if restored != version_id {
            anyhow::bail!(
                "rollback hash mismatch: restored tree hashes to {restored} but the requested \
                 version is {version_id}"
            );
        }
        Ok(())
    }
}

/// Delete every entry of `root` that is covered by the hash (i.e. everything
/// that is not excluded), keeping the excluded trees intact.
fn purge_covered(root: &Path, prefix: &str, excludes: &[String]) -> anyhow::Result<()> {
    let entries = match std::fs::read_dir(root) {
        Ok(entries) => entries,
        Err(_) => return Ok(()),
    };
    for entry in entries {
        let entry = entry?;
        let name = entry.file_name().to_string_lossy().into_owned();
        let rel = if prefix.is_empty() {
            name.clone()
        } else {
            format!("{prefix}/{name}")
        };
        if crate::runtime::policy::is_excluded(&rel, excludes) {
            continue;
        }
        let path = entry.path();
        if entry.file_type()?.is_dir() {
            purge_covered(&path, &rel, excludes)?;
            if std::fs::read_dir(&path)?.next().is_none() {
                std::fs::remove_dir(&path)?;
            }
        } else {
            std::fs::remove_file(&path)?;
        }
    }
    Ok(())
}

/// Write via a temporary file plus rename so a crash never leaves a truncated
/// index behind.
pub fn write_atomic(path: &Path, bytes: &[u8]) -> anyhow::Result<()> {
    if let Some(parent) = path.parent() {
        std::fs::create_dir_all(parent)?;
    }
    let temp = path.with_extension("tmp-write");
    std::fs::write(&temp, bytes)?;
    if path.exists() {
        std::fs::remove_file(path)?;
    }
    std::fs::rename(&temp, path)?;
    Ok(())
}
