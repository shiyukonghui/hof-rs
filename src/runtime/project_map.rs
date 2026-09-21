//! DR-26: `PROJECT_MAP.md` — progressive disclosure for the Developer.
//!
//! `smoke-t2` spent most of its budget exploring: the Developer had no concise
//! index of what the artifact already contained, so it read the harness sources
//! and the external MCP server to orient itself.  The map is a cheap, complete
//! answer to "what is in here?": top-level entries with their sizes plus the
//! handful of key files (project settings, scenes, scripts).

use std::path::Path;

use walkdir::WalkDir;

use crate::runtime::policy::is_excluded;

fn relativize(root: &Path, path: &Path) -> String {
    path.strip_prefix(root)
        .unwrap_or(path)
        .components()
        .map(|component| component.as_os_str().to_string_lossy().into_owned())
        .collect::<Vec<_>>()
        .join("/")
}

/// `(file count, total bytes)` of a directory subtree, honouring the excludes.
fn directory_totals(root: &Path, excludes: &[String]) -> (usize, u64) {
    let mut files = 0usize;
    let mut bytes = 0u64;
    for entry in WalkDir::new(root).follow_links(false).into_iter().flatten() {
        if !entry.file_type().is_file() {
            continue;
        }
        let relative = relativize(root, entry.path());
        if is_excluded(&relative, excludes) {
            continue;
        }
        files += 1;
        bytes += entry.metadata().map(|meta| meta.len()).unwrap_or(0);
    }
    (files, bytes)
}

/// DR-26: render the map of the artifact as it stands before this iteration.
pub fn render_project_map(
    root: &Path,
    excludes: &[String],
    iteration: u32,
    warm_start: bool,
) -> String {
    let label = if iteration <= 1 {
        "A0".to_string()
    } else if warm_start {
        format!("A{}", iteration - 1)
    } else {
        format!("A{} (warm_start=false: the developer starts from A0)", 0)
    };
    let mut text = format!(
        "# Project map ({label})\n\n\
         This is the artifact as it stands before your changes. Inspect this map instead of \
         exploring the filesystem: it already tells you what exists and how big it is.\n\n\
         ## Top level\n\n"
    );

    let mut entries: Vec<(String, bool, u64, usize)> = Vec::new();
    match std::fs::read_dir(root) {
        Ok(reader) => {
            for entry in reader.flatten() {
                let name = entry.file_name().to_string_lossy().into_owned();
                if is_excluded(&name, excludes) {
                    continue;
                }
                let path = entry.path();
                let metadata = match entry.metadata() {
                    Ok(metadata) => metadata,
                    Err(_) => continue,
                };
                if metadata.is_dir() {
                    let (files, bytes) = directory_totals(&path, excludes);
                    entries.push((name, true, bytes, files));
                } else {
                    entries.push((name, false, metadata.len(), 1));
                }
            }
        }
        Err(error) => text.push_str(&format!("(the project root is unreadable: {error})\n")),
    }
    entries.sort();
    if entries.is_empty() {
        text.push_str("- (empty)\n");
    }
    for (name, is_dir, bytes, files) in &entries {
        if *is_dir {
            text.push_str(&format!(
                "- `{name}/` — directory, {files} file(s), {bytes} bytes\n"
            ));
        } else {
            text.push_str(&format!("- `{name}` — file, {bytes} bytes\n"));
        }
    }

    text.push_str("\n## Key files\n\n");
    let mut keys: Vec<(String, u64)> = Vec::new();
    for entry in WalkDir::new(root).follow_links(false).into_iter().flatten() {
        if !entry.file_type().is_file() {
            continue;
        }
        let relative = relativize(root, entry.path());
        if is_excluded(&relative, excludes) {
            continue;
        }
        let name = relative.rsplit('/').next().unwrap_or("");
        let is_key = relative == "project.godot"
            || name.ends_with(".tscn")
            || name.ends_with(".gd")
            || relative == "ADDON_MISSING.txt";
        if is_key {
            keys.push((
                relative,
                entry.metadata().map(|meta| meta.len()).unwrap_or(0),
            ));
        }
    }
    keys.sort();
    if keys.is_empty() {
        text.push_str("- (no project settings, scene or script yet)\n");
    }
    for (path, bytes) in keys {
        text.push_str(&format!("- `{path}` ({bytes} bytes)\n"));
    }
    text.push_str(
        "\n> Read only the files you actually need. Do not read `src/**`, `.spec/**`, `tests/**`, \
         `.git/**` or the external MCP checkout: the tool schema you need is in `.hoh/TOOLS.md`.\n",
    );
    text
}
