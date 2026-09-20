//! Role view construction: every role gets its own directory tree so that
//! "who may write what" is a property of the filesystem layout.

use std::path::Path;

use walkdir::WalkDir;

use crate::runtime::policy::is_excluded;

/// Recursively copy `src` into `dst`, skipping excluded relative paths.
pub fn copy_tree(src: &Path, dst: &Path, excludes: &[String]) -> anyhow::Result<()> {
    if !src.exists() {
        return Ok(());
    }
    for entry in WalkDir::new(src).follow_links(false) {
        let entry = entry?;
        let rel = entry
            .path()
            .strip_prefix(src)
            .unwrap_or(entry.path())
            .components()
            .map(|component| component.as_os_str().to_string_lossy().into_owned())
            .collect::<Vec<_>>()
            .join("/");
        if rel.is_empty() || is_excluded(&rel, excludes) {
            continue;
        }
        let target = dst.join(&rel);
        if entry.file_type().is_dir() {
            std::fs::create_dir_all(&target)?;
        } else if entry.file_type().is_file() {
            if let Some(parent) = target.parent() {
                std::fs::create_dir_all(parent)?;
            }
            std::fs::copy(entry.path(), &target)?;
        }
    }
    Ok(())
}
