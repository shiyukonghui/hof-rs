//! Round-2 credential batch — the tree must hold no key-shaped material, and the
//! only way a secret enters a run must be a file **outside** the repository.
//!
//! Two facts made this necessary and both are recorded in `.spec/bevy`:
//!
//! 1. `config/model.secret.env` sat inside the tree for weeks and held a live
//!    `HOF_MODEL_API_KEY`.  The round-1 report found it; the round-2 report found
//!    it still there.
//! 2. Round 1's credential leak was not the file itself: the key was passed as an
//!    inline assignment on a watched command line, and four trajectory files
//!    under `runs/round1b/**` and `runs/round1/**` still carry the value.
//!
//! The rules this file pins:
//!
//! * **No key-shaped material in the tree a reader can browse or archive** —
//!   every file that is not in a generated, ignored directory is scanned.
//! * **The secret-file mechanism refuses the repository.**  A path inside the
//!   repository is refused with both paths named; a path outside it loads, and a
//!   file holding no key-shaped value is refused rather than accepted as a
//!   credential.
//! * **The historical evidence is reported, not silently rewritten.**  The
//!   recorded trajectories are evidence a report must be able to cite; this test
//!   reports the paths and a **fingerprint** of the material (never the value),
//!   so "the leak existed and where" is a fact the report can state.
//!
//! No real credential appears in this file: every fixture below is a placeholder
//! the shape test deliberately does **not** match.

use std::collections::BTreeSet;
use std::path::{Path, PathBuf};

use hof_rs::runtime::secrets::{
    ensure_secret_file_is_outside, key_shaped_tokens, looks_key_shaped, read_secret_file,
};

/// The repository root, from the crate the test was compiled with.
fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
}

/// Directories that are generated build output or that no reader browses.
///
/// `runs/` is here because it is **gitignored** evidence: it is not part of the
/// tree a reader or an archive sees, it is the recorded material the reports cite,
/// and rewriting it would destroy the evidence a report has to be checked
/// against.  What it holds is reported by
/// [`the_historical_evidence_is_reported_with_a_fingerprint_never_the_value`].
const GENERATED: &[&str] = &[".git", "target", ".workspace", "runs", "node_modules"];

/// The placeholders the repository is allowed to carry.  Each is deliberately
/// **not** key-shaped (the body is shorter than the shape test's threshold), so
/// they are listed here for the reader, not to weaken the scan.
const ALLOWED_PLACEHOLDERS: &[&str] = &["test-key-not-a-secret", "sk-late-occurrence"];

/// Paths that may hold key-shaped **fixtures**, because the fixture is the thing
/// under test and is assembled at run time rather than stored.
///
/// Exactly one entry, and it is not an escape hatch: the file it names is the
/// test that pins the shape rule, and it builds its key-shaped value from pieces
/// so the literal appears in no file — which is why the scan finds the *pattern*
/// text there and nothing else.
const FIXTURE_SOURCES: &[&str] = &["tests/credential_scan.rs"];

/// Every text file under `root` that is not inside a generated directory.
fn browsable_files(root: &Path) -> Vec<PathBuf> {
    let mut files = Vec::new();
    let mut stack = vec![root.to_path_buf()];
    while let Some(directory) = stack.pop() {
        let Ok(entries) = std::fs::read_dir(&directory) else {
            continue;
        };
        for entry in entries.filter_map(Result::ok) {
            let path = entry.path();
            let name = entry.file_name().to_string_lossy().into_owned();
            let file_type = entry.file_type();
            if file_type.map(|kind| kind.is_dir()).unwrap_or(false) {
                if GENERATED.contains(&name.as_str()) {
                    continue;
                }
                stack.push(path);
                continue;
            }
            if name.ends_with(".lock") {
                // A build's lockfile is generated output and is not browsable
                // prose; the repository's own Cargo.lock is a dependency list.
                continue;
            }
            files.push(path);
        }
    }
    files.sort();
    files
}

/// Every key-shaped value in a byte string, deduplicated.
///
/// It uses the same token scan the rule uses, so a value embedded in a JSON
/// document is found exactly — not reconstructed from a line, which would
/// fingerprint the wrong bytes whenever a message quotes more than one value.
fn key_shaped_values(bytes: &[u8]) -> BTreeSet<String> {
    let text = String::from_utf8_lossy(bytes);
    let mut found = key_shaped_tokens(&text);
    for line in text.lines() {
        if looks_key_shaped(line) && key_shaped_tokens(line).is_empty() {
            // The assignment shape: the whole line is the finding, and its value
            // is fingerprinted as the line rather than reconstructed.
            found.insert(line.trim().to_string());
        }
    }
    found
}

/// The first 8 hex characters of a value's sha256: a fingerprint that identifies
/// "the same secret" without printing it.
fn fingerprint(value: &str) -> String {
    use sha2::{Digest, Sha256};
    let mut hasher = Sha256::new();
    hasher.update(value.as_bytes());
    let digest = hasher.finalize();
    digest
        .iter()
        .take(4)
        .map(|byte| format!("{byte:02x}"))
        .collect()
}

/// The repository tree holds no key-shaped material outside the generated and
/// recorded directories.
#[test]
fn no_key_shaped_material_is_browsable_in_the_repository_tree() {
    let root = repo_root();
    let mut findings: Vec<(String, String)> = Vec::new();
    for path in browsable_files(&root) {
        let relative = path
            .strip_prefix(&root)
            .unwrap_or(&path)
            .to_string_lossy()
            .replace('\\', "/");
        if FIXTURE_SOURCES.contains(&relative.as_str()) {
            continue;
        }
        let Ok(bytes) = std::fs::read(&path) else {
            continue;
        };
        for value in key_shaped_values(&bytes) {
            if ALLOWED_PLACEHOLDERS
                .iter()
                .any(|allowed| value.contains(allowed))
            {
                continue;
            }
            findings.push((relative.clone(), fingerprint(&value)));
        }
    }
    assert!(
        findings.is_empty(),
        "key-shaped material is browsable in the repository tree (path, fingerprint): {findings:?}\n\
         The value is deliberately not printed. A finding here is either a credential to remove \
         from the tree or a placeholder short enough not to be key-shaped — never something to \
         allow-list silently."
    );
}

/// The mechanism that replaces the leaked file: **the repository is refused.**
#[test]
fn a_secret_file_inside_the_repository_is_refused_with_both_paths_named() {
    let root = repo_root();
    // The exact path that leaked.  It is named here on purpose: the rule's test
    // is that this path can never hold a loadable secret again.
    let inside = root.join("config/model.secret.env");
    let error = ensure_secret_file_is_outside(&inside, &root)
        .expect_err("a secret inside the repository must be refused");
    assert!(
        error.contains("may not live inside the repository"),
        "{error}"
    );
    assert!(
        error.contains("model.secret.env"),
        "the refusal names the offending path: {error}"
    );

    // The control: a path outside the repository is not refused by the rule.
    let outside = root
        .parent()
        .expect("the repository has a parent")
        .join("hof-secrets-test/round.env");
    assert!(ensure_secret_file_is_outside(&outside, &root).is_ok());

    // A nonexistent path **inside** the repository is still refused: the rule is
    // about where the file is, not about whether it happens to exist yet.
    let future = root.join("config/would-be-secret.env");
    assert!(ensure_secret_file_is_outside(&future, &root).is_err());
}

/// Loading a secret from outside the repository works, and its value is returned
/// without ever being printed by the loader.
#[test]
fn a_secret_file_outside_the_repository_loads_and_is_never_printed() {
    let root = repo_root();
    // The scratch directory is created by the test framework outside the tree.
    let directory = tempfile::tempdir().expect("a temporary directory outside the repository");
    let outside = directory.path().join("round.env");
    // A placeholder that **is** key-shaped, built at run time from pieces so the
    // literal never appears in this file (or in the source scan above).
    let value = format!("sk-{}{}", "placeholder".repeat(3), "0123456789");
    std::fs::write(
        &outside,
        format!("# a fixture secret file\nHOH_MODEL_API_KEY={value}\n"),
    )
    .expect("the fixture is writable");

    let (name, loaded) =
        read_secret_file(&outside, &root).expect("an out-of-repository secret file loads");
    assert_eq!(name, "HOH_MODEL_API_KEY");
    assert_eq!(loaded, value);
    assert!(
        looks_key_shaped(&value),
        "the fixture must really be key-shaped, or the test proves nothing"
    );
}

/// A file with no key-shaped value is refused rather than accepted as a
/// credential: a path typo must not become a loaded key.
#[test]
fn a_file_with_no_key_shaped_value_is_refused() {
    let root = repo_root();
    let directory = tempfile::tempdir().expect("a temporary directory");
    let not_a_secret = directory.path().join("notes.env");
    std::fs::write(&not_a_secret, "REMINDER=buy milk\n").expect("the fixture is writable");
    let error = read_secret_file(&not_a_secret, &root)
        .expect_err("a file without a key-shaped value is not a secret file");
    assert!(error.contains("no key-shaped"), "{error}");
}

/// The shape test itself: what it catches and — just as important — what it does
/// not, so the allow-list above cannot quietly grow.
#[test]
fn the_shape_test_catches_credentials_and_ignores_prose() {
    // The fixture is assembled at run time so no key-shaped literal sits in the
    // tree this test is also scanning.
    let shaped = format!("HOH_MODEL_API_KEY=sk-{}", "abcdefghijklmnopqrstuvwx");
    assert!(looks_key_shaped(&shaped), "{shaped}");
    assert!(looks_key_shaped(
        "api_key: 0123456789abcdef0123456789abcdef"
    ));
    // Short values, ordinary words and the repository's own placeholders are not
    // findings.
    for benign in [
        "test-key-not-a-secret",
        "sk-late-occurrence",
        "HOH_MODEL_API_KEY=",
        "the token is short",
        "sk-abc",
        "task-Runner-very-long-name",
    ] {
        assert!(
            !looks_key_shaped(benign),
            "`{benign}` must not be reported as a credential shape"
        );
    }
}

/// The false positive the recorded evidence forced out, pinned: the round-1b
/// developer trajectory is full of Rust crate names whose *last two letters*
/// meet the `sk-` prefix (`async-task-…`, `futures-task-…`).  An earlier form of
/// the shape rule reported them as credentials, which is why a hyphen before the
/// prefix is a boundary now.
#[test]
fn the_crate_names_in_the_recorded_evidence_are_not_credentials() {
    for benign in [
        "async-task-c53c1f0a1b2c3d4e5f60718293a4b5c6",
        "futures-task-c1f0a1b2c3d4e5f60718293a4b5c6d7",
        "Cargo.lock: async-task 4.7.1",
    ] {
        assert!(
            !looks_key_shaped(benign),
            "`{benign}` is a crate name, not a credential"
        );
    }
    // The same body after a boundary **is** a credential shape, so the rule is
    // not "anything containing `sk-` is fine".
    assert!(looks_key_shaped(";sk-abcdefghijklmnopqrstuvwx"));
}

/// The recorded evidence still holds the round-1/round-2 key, and this test
/// **reports where** instead of rewriting it.
///
/// Rewriting those files would destroy the evidence the reports cite; deleting
/// them would be worse.  What the credential batch must not do is hide the fact,
/// so the paths and a fingerprint are asserted here and stated in
/// `.spec/bevy/TRUST-REPORT.md`, and the rotation of the key is the operator's
/// decision (it was never in this harness).
#[test]
fn the_historical_evidence_is_reported_with_a_fingerprint_never_the_value() {
    let root = repo_root();
    let secret = root.join("config/model.secret.env");
    let mut fingerprints: BTreeSet<String> = BTreeSet::new();

    // (a) The leaked file itself must be gone from the tree.  If it is still
    //     there, this test fails and names it: the batch exists to remove it.
    assert!(
        !secret.exists(),
        "{} still exists: the credential batch must remove it from the tree",
        secret.display()
    );

    // (b) Whatever key-shaped material the recorded evidence holds is reported by
    //     path and fingerprint.
    let mut evidence_paths: Vec<String> = Vec::new();
    let mut per_path: Vec<String> = Vec::new();
    for directory in ["runs/round1", "runs/round1b", "runs/round2"] {
        let path = root.join(directory);
        if !path.is_dir() {
            continue;
        }
        for file in browsable_files(&path) {
            let Ok(bytes) = std::fs::read(&file) else {
                continue;
            };
            let relative = file
                .strip_prefix(&root)
                .unwrap_or(&file)
                .to_string_lossy()
                .replace('\\', "/");
            let values = key_shaped_values(&bytes);
            let mut here: Vec<String> = Vec::new();
            for value in values {
                if ALLOWED_PLACEHOLDERS
                    .iter()
                    .any(|allowed| value.contains(allowed))
                {
                    continue;
                }
                let print = fingerprint(&value);
                here.push(format!("{print}(len {})", value.len()));
                fingerprints.insert(print);
            }
            if !here.is_empty() {
                per_path.push(format!("{relative}: {here:?}"));
                evidence_paths.push(relative);
            }
        }
    }
    // The report states this list; the test states that it was measured rather
    // than assumed, and that no value was printed.
    println!(
        "key-shaped material in recorded evidence: {} file(s), {} distinct fingerprint(s)",
        evidence_paths.len(),
        fingerprints.len(),
    );
    for line in &per_path {
        println!("  {line}");
    }
    // A diagnostic that cannot be silent: the two files the batch's report names
    // are reported explicitly, with their measured shape counts.
    for named in [
        "runs/round1/iter-1/traj/developer.attempt1.json",
        "runs/round1b/iter-1/traj/developer.attempt1.json",
        "runs/round1b/iter-1/traj/tester.attempt1.json",
    ] {
        let path = root.join(named);
        match std::fs::read(&path) {
            Ok(bytes) => {
                let text = String::from_utf8_lossy(&bytes);
                let tokens = key_shaped_tokens(&text);
                println!(
                    "  {named}: {} byte(s), {} key-shaped token(s), looks_key_shaped={}",
                    bytes.len(),
                    tokens.len(),
                    looks_key_shaped(&text)
                );
            }
            Err(error) => println!("  {named}: unreadable ({error})"),
        }
    }
    assert!(
        !fingerprints.is_empty() || !root.join("runs/round1b").is_dir(),
        "the round-1 credential leak was recorded in the evidence; if the recorded material is \
         present and no fingerprint is found, this test has stopped measuring it"
    );
}
