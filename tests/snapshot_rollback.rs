//! R10 — content-addressed snapshots, version index, and rollback.
//!
//! The version store never depends on git: `version_id` is the sha256 of the
//! hashed tree, and the hash function is shared with the permission checks
//! (`hof_rs::runtime::policy::hash_tree`), so the two can never drift apart.

use std::fs;
use std::path::Path;

use hof_rs::runtime::policy::hash_tree;
use hof_rs::runtime::snapshot::VersionStore;

const EXCLUDES: &[&str] = &[".hoh", ".git", "cache"];

fn excludes() -> Vec<String> {
    EXCLUDES.iter().map(|item| item.to_string()).collect()
}

fn write(path: &Path, content: &str) {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).expect("mkdir");
    }
    fs::write(path, content).expect("write");
}

fn seed(workspace: &Path) {
    write(&workspace.join("project.godot"), "config_version=5\n");
    write(&workspace.join("scripts/player.gd"), "extends Node\n");
    write(&workspace.join("scenes/main.tscn"), "[gd_scene]\n");
    // Excluded trees must never influence the version id.
    write(&workspace.join(".hoh/plan.md"), "iteration 1\n");
    write(&workspace.join("cache/tmp.bin"), "cache\n");
}

#[test]
fn snapshot_is_content_addressed() {
    let temp = tempfile::tempdir().expect("tempdir");
    let workspace = temp.path().join("workspace");
    seed(&workspace);
    let store = VersionStore::new(temp.path().join("versions"));

    let first = store
        .snapshot(&workspace, &excludes(), 1, "developer")
        .unwrap();
    let second = store
        .snapshot(&workspace, &excludes(), 1, "developer")
        .unwrap();
    assert_eq!(first.version_id, second.version_id);
    assert_eq!(first.candidate_id, first.version_id);
    assert_eq!(
        first.version_id,
        hash_tree(&workspace, &excludes()).unwrap()
    );

    // Touching only an excluded tree must not change the identity.
    write(&workspace.join(".hoh/plan.md"), "iteration 2\n");
    let third = store
        .snapshot(&workspace, &excludes(), 1, "developer")
        .unwrap();
    assert_eq!(third.version_id, first.version_id);

    // One changed byte must change the identity.
    write(&workspace.join("scripts/player.gd"), "extends Node2D\n");
    let fourth = store
        .snapshot(&workspace, &excludes(), 1, "developer")
        .unwrap();
    assert_ne!(fourth.version_id, first.version_id);

    let index = store.read_index().unwrap();
    let ids: Vec<&str> = index
        .iter()
        .map(|entry| entry.version_id.as_str())
        .collect();
    assert!(ids.contains(&first.version_id.as_str()));
    assert!(ids.contains(&fourth.version_id.as_str()));
    assert_eq!(fourth.parent.as_deref(), Some(third.version_id.as_str()));
}

#[test]
fn rollback_restores_exact_tree() {
    let temp = tempfile::tempdir().expect("tempdir");
    let workspace = temp.path().join("workspace");
    seed(&workspace);
    let store = VersionStore::new(temp.path().join("versions"));

    let entry = store
        .snapshot(&workspace, &excludes(), 1, "developer")
        .unwrap();

    // Simulate a large regression: edit, delete and add files.
    write(
        &workspace.join("scripts/player.gd"),
        "extends Node2D\n# broken\n",
    );
    fs::remove_file(workspace.join("scenes/main.tscn")).unwrap();
    write(&workspace.join("scripts/enemy.gd"), "extends Node\n");
    fs::remove_dir_all(workspace.join("scripts")).ok();
    write(
        &workspace.join("scripts/player.gd"),
        "extends Node2D\n# broken\n",
    );
    assert_ne!(
        hash_tree(&workspace, &excludes()).unwrap(),
        entry.version_id
    );

    // The excluded tree survives a rollback untouched.
    write(&workspace.join(".hoh/plan.md"), "keep me\n");

    store
        .rollback(&workspace, &excludes(), &entry.version_id)
        .expect("rollback must succeed");

    assert_eq!(
        hash_tree(&workspace, &excludes()).unwrap(),
        entry.version_id
    );
    assert_eq!(
        fs::read_to_string(workspace.join("scripts/player.gd")).unwrap(),
        "extends Node\n"
    );
    assert_eq!(
        fs::read_to_string(workspace.join("scenes/main.tscn")).unwrap(),
        "[gd_scene]\n"
    );
    assert!(!workspace.join("scripts/enemy.gd").exists());
    assert_eq!(
        fs::read_to_string(workspace.join(".hoh/plan.md")).unwrap(),
        "keep me\n"
    );
}

#[test]
fn rollback_detects_corruption() {
    let temp = tempfile::tempdir().expect("tempdir");
    let workspace = temp.path().join("workspace");
    seed(&workspace);
    let store = VersionStore::new(temp.path().join("versions"));

    let entry = store
        .snapshot(&workspace, &excludes(), 1, "developer")
        .unwrap();
    write(
        &store.root.join(&entry.version_id).join("scripts/player.gd"),
        "extends NodeX\n",
    );

    let error = store
        .rollback(&workspace, &excludes(), &entry.version_id)
        .expect_err("a tampered snapshot must not be restored silently");
    assert!(
        error.to_string().contains("hash"),
        "unexpected error: {error}"
    );
}
