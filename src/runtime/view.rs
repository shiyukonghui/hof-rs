//! Role view construction: every role gets its own directory tree so that
//! "who may write what" is a property of the filesystem layout.

use std::path::{Path, PathBuf};

use walkdir::WalkDir;

use crate::runtime::policy::is_excluded;

/// A directory tree handed to one role as its working directory.
#[derive(Clone, Debug, Default)]
pub struct ViewSpec {
    /// View root (becomes the role's `cwd`).
    pub root: PathBuf,
    /// Directory copied into `root` (`None` = empty view).
    pub source: Option<PathBuf>,
    /// Top-level path prefixes excluded while copying.
    pub excludes: Vec<String>,
    /// DR-3: extra relative paths/prefixes excluded from the *view only*.
    /// They never reach `hash_tree` or the snapshot exclude set, so excluding
    /// something here does not hide it from the R2/R3 write-detection.
    pub private_excludes: Vec<String>,
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
        let mut excludes = spec.excludes.clone();
        for item in &spec.private_excludes {
            let normalized = item.replace('\\', "/");
            if !normalized.is_empty() && !excludes.contains(&normalized) {
                excludes.push(normalized);
            }
        }
        copy_tree(source, &spec.root, &excludes)?;
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

/// DR-36: copy an evidence tree into the frozen candidate view and report every
/// file above `max_bytes`.
///
/// `smoke-t5` produced a real 4246-byte screenshot under
/// `<workspace>/.hoh/evidence/` that the candidate view never copied, so the
/// Tester recorded a **true** artifact as missing (gap G19).  The rule here is
/// deliberately "copy first, report second": an oversized file is never
/// silently skipped, it is copied and its size is published as
/// `evidence_too_large`.
///
/// Returns `(relative path, byte size)` for every oversized file, sorted.
pub fn copy_evidence(src: &Path, dst: &Path, max_bytes: u64) -> anyhow::Result<Vec<(String, u64)>> {
    let mut oversized = Vec::new();
    if !src.exists() {
        return Ok(oversized);
    }
    for entry in WalkDir::new(src).follow_links(false) {
        let entry = entry?;
        if !entry.file_type().is_file() {
            continue;
        }
        let rel = entry
            .path()
            .strip_prefix(src)
            .unwrap_or(entry.path())
            .components()
            .map(|component| component.as_os_str().to_string_lossy().into_owned())
            .collect::<Vec<_>>()
            .join("/");
        if rel.is_empty() {
            continue;
        }
        let target = dst.join(&rel);
        if let Some(parent) = target.parent() {
            std::fs::create_dir_all(parent)?;
        }
        std::fs::copy(entry.path(), &target)?;
        let size = entry.metadata().map(|meta| meta.len()).unwrap_or(0);
        if size > max_bytes {
            oversized.push((rel, size));
        }
    }
    oversized.sort();
    Ok(oversized)
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
            ..ViewSpec::default()
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
            ..ViewSpec::default()
        };
        build_view(&spec).unwrap();
        write(&root.join("leftover.tmp"), "garbage\n");
        build_view(&spec).unwrap();
        assert!(!root.join("leftover.tmp").exists());
        assert_eq!(list_tree(&root).unwrap().len(), 2);
    }

    /// DR-3: `private_excludes` removes a path from every copied view, but the
    /// file stays part of the artifact identity (`hash_tree`).
    #[test]
    fn private_excludes_are_not_copied_but_still_hashed() {
        let temp = tempfile::tempdir().unwrap();
        let source = temp.path().join("source");
        write(&source.join("project.godot"), "config_version=5\n");
        write(&source.join("tests/secret.json"), "{\"hidden\":true}\n");
        write(&source.join("tests/public.json"), "{}\n");

        let root = temp.path().join("view");
        build_view(&ViewSpec {
            root: root.clone(),
            source: Some(source.clone()),
            excludes: vec![],
            private_excludes: vec!["tests/secret.json".to_string()],
            inputs: vec![],
        })
        .unwrap();

        let files = list_tree(&root).unwrap();
        assert_eq!(
            files,
            vec!["project.godot".to_string(), "tests/public.json".to_string()],
            "the private file must not be copied into the view"
        );

        // The exclusion is view-only: the hash still covers the private file.
        let manifest = crate::runtime::policy::tree_manifest(&source, &[]).unwrap();
        assert!(manifest.contains_key("tests/secret.json"));
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
            ..ViewSpec::default()
        })
        .unwrap();
        assert_eq!(
            list_tree(&root).unwrap(),
            vec![".hoh/evidence.json".to_string()]
        );
    }

    /// DR-36: every evidence file is copied, and the oversized ones are
    /// reported (sorted) instead of being skipped.
    #[test]
    fn copy_evidence_copies_everything_and_reports_the_oversized() {
        let temp = tempfile::tempdir().unwrap();
        let source = temp.path().join("evidence");
        write(&source.join("frame-00.png"), "0123456789");
        write(&source.join("replay/long.json"), "0123456789abcdef");
        write(&source.join("small.json"), "01");

        let destination = temp.path().join("candidate/.hoh/evidence");
        let oversized = copy_evidence(&source, &destination, 4).unwrap();
        assert_eq!(
            oversized,
            vec![
                ("frame-00.png".to_string(), 10),
                ("replay/long.json".to_string(), 16),
            ],
            "the oversized files are reported with their real size, sorted"
        );
        assert_eq!(
            std::fs::read_to_string(destination.join("frame-00.png")).unwrap(),
            "0123456789",
            "an oversized file is still copied"
        );
        assert!(destination.join("replay/long.json").is_file());
        assert!(destination.join("small.json").is_file());

        // A workspace without evidence is not an error.
        assert!(copy_evidence(&temp.path().join("missing"), &destination, 4)
            .unwrap()
            .is_empty());
    }
}
