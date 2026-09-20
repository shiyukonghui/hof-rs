//! Role view construction: every role gets its own directory tree so that
//! "who may write what" is a property of the filesystem layout.

use std::path::{Path, PathBuf};

use walkdir::WalkDir;

use crate::runtime::policy::is_excluded;

/// A directory tree handed to one role as its working directory.
#[derive(Clone, Debug)]
pub struct ViewSpec {
    /// View root (becomes the role's `cwd`).
    pub root: PathBuf,
    /// Directory copied into `root` (`None` = empty view).
    pub source: Option<PathBuf>,
    /// Top-level path prefixes excluded while copying.
    pub excludes: Vec<String>,
    /// `(relative path, content)` pairs written into `root` after copying.
    pub inputs: Vec<(String, String)>,
}

/// Build a view.  Idempotent: an existing view is emptied first (the root
/// itself is preserved).
pub fn build_view(spec: &ViewSpec) -> anyhow::Result<()> {
    if spec.root.exists() {
        std::fs::remove_dir_all(&spec.root).map_err(|error| {
            anyhow::anyhow!("could not clear view {}: {error}", spec.root.display())
        })?;
    }
    std::fs::create_dir_all(&spec.root)?;
    if let Some(source) = &spec.source {
        copy_tree(source, &spec.root, &spec.excludes)?;
    }
    write_inputs(&spec.root, &spec.inputs)
}

/// Write `(relative path, content)` inputs under `root`, creating parents.
pub fn write_inputs(root: &Path, inputs: &[(String, String)]) -> anyhow::Result<()> {
    for (rel, content) in inputs {
        let path = root.join(rel.replace('\\', "/"));
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent)?;
        }
        std::fs::write(&path, content)?;
    }
    Ok(())
}

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

/// Sorted list of relative paths present in a view (used by tests and logs).
pub fn list_tree(root: &Path) -> anyhow::Result<Vec<String>> {
    let mut items = Vec::new();
    if root.exists() {
        for entry in WalkDir::new(root).follow_links(false) {
            let entry = entry?;
            if entry.file_type().is_file() {
                let rel = entry
                    .path()
                    .strip_prefix(root)
                    .unwrap_or(entry.path())
                    .components()
                    .map(|component| component.as_os_str().to_string_lossy().into_owned())
                    .collect::<Vec<_>>()
                    .join("/");
                items.push(rel);
            }
        }
    }
    items.sort();
    Ok(items)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn write(path: &Path, content: &str) {
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent).unwrap();
        }
        std::fs::write(path, content).unwrap();
    }

    #[test]
    fn build_view_copies_source_and_injects_inputs() {
        let temp = tempfile::tempdir().unwrap();
        let source = temp.path().join("source");
        write(&source.join("project.godot"), "config_version=5\n");
        write(&source.join(".hoh/plan.md"), "stale plan\n");
        write(&source.join("cache/blob.bin"), "cache\n");

        let root = temp.path().join("view");
        build_view(&ViewSpec {
            root: root.clone(),
            source: Some(source.clone()),
            excludes: vec!["cache".to_string(), ".hoh".to_string(), ".git".to_string()],
            inputs: vec![(".hoh/TASK.md".to_string(), "spec\n".to_string())],
        })
        .unwrap();

        let files = list_tree(&root).unwrap();
        assert_eq!(
            files,
            vec![".hoh/TASK.md".to_string(), "project.godot".to_string()]
        );
        assert_eq!(
            std::fs::read_to_string(root.join(".hoh/TASK.md")).unwrap(),
            "spec\n"
        );
    }

    #[test]
    fn build_view_is_idempotent_and_clears_stale_files() {
        let temp = tempfile::tempdir().unwrap();
        let source = temp.path().join("source");
        write(&source.join("project.godot"), "config_version=5\n");
        let root = temp.path().join("view");
        let spec = ViewSpec {
            root: root.clone(),
            source: Some(source),
            excludes: vec![],
            inputs: vec![(".hoh/TASK.md".to_string(), "spec\n".to_string())],
        };
        build_view(&spec).unwrap();
        write(&root.join("leftover.tmp"), "garbage\n");
        build_view(&spec).unwrap();
        assert!(!root.join("leftover.tmp").exists());
        assert_eq!(list_tree(&root).unwrap().len(), 2);
    }

    #[test]
    fn build_view_without_source_is_an_empty_scaffold() {
        let temp = tempfile::tempdir().unwrap();
        let root = temp.path().join("view");
        build_view(&ViewSpec {
            root: root.clone(),
            source: None,
            excludes: vec![],
            inputs: vec![(".hoh/evidence.json".to_string(), "{}\n".to_string())],
        })
        .unwrap();
        assert_eq!(
            list_tree(&root).unwrap(),
            vec![".hoh/evidence.json".to_string()]
        );
    }
}
