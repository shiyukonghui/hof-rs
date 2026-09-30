//! DR-69 ③ — an aborted attempt's evidence is preserved **before** it is
//! cleared.
//!
//! `smoke-t9`' attempt A died with `llm-connector chat request failed`; the
//! retry required deleting the round's own `runs/smoke-t9` directory, and the
//! 16.4 MB trajectory inside it became unrecoverable.  The runtime has the same
//! shape one level down: DR-24 rebuilds `.hoh/deterministic` from scratch for
//! every battery pass, so the first pass's raw payloads were destroyed the
//! moment a repair started the second pass.
//!
//! The order is fixed: save first, then clean.  Nothing is deleted that is not
//! already somewhere else.

use hof_rs::runtime::run_loop::preserve_then_clear;

#[test]
fn an_aborted_attempt_is_moved_aside_before_its_directory_is_cleared() {
    let temp = tempfile::tempdir().unwrap();
    let dir = temp.path().join("workspace/.hoh/deterministic");
    std::fs::create_dir_all(dir.join("raw")).unwrap();
    std::fs::write(dir.join("battery.json"), "{\"step\":\"pass-1\"}").unwrap();
    std::fs::write(dir.join("raw/input_replay.json"), "{\"ok\":true}").unwrap();

    let root = temp.path().join("runs/run-1/quarantine");
    let preserved = preserve_then_clear(&dir, &root, "deterministic-pass-1")
        .expect("a non-empty attempt must be preserved");

    assert!(
        !dir.exists(),
        "the caller asked for the directory to be cleared"
    );
    assert_eq!(
        std::fs::read_to_string(preserved.join("battery.json")).unwrap(),
        "{\"step\":\"pass-1\"}",
        "the evidence must survive byte for byte under the preserved path"
    );
    assert_eq!(
        std::fs::read_to_string(preserved.join("raw/input_replay.json")).unwrap(),
        "{\"ok\":true}"
    );
    assert!(
        preserved.starts_with(&root),
        "the preserved bytes must live under the controlled root: {}",
        preserved.display()
    );
    let name = preserved
        .file_name()
        .unwrap()
        .to_string_lossy()
        .into_owned();
    assert!(
        name.starts_with("deterministic-pass-1.stale-"),
        "the preserved directory must be named and timestamped: {name}"
    );
}

#[test]
fn an_empty_or_missing_attempt_is_not_preserved() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path().join("quarantine");

    // Missing: nothing to do.
    assert!(preserve_then_clear(&temp.path().join("nope"), &root, "x").is_none());

    // Empty: there is no evidence to keep, and the directory still goes away.
    let empty = temp.path().join("empty");
    std::fs::create_dir_all(&empty).unwrap();
    assert!(preserve_then_clear(&empty, &root, "x").is_none());
    assert!(!empty.exists());
    assert!(
        !root.exists(),
        "an empty attempt must not create a quarantine"
    );
}
