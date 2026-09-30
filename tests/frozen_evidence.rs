//! DR-70 ⑤: the frozen `smoke-t9` command dump is **evidence**, and evidence has
//! to keep the bytes that carry its meaning.
//!
//! `3adab37` (DR-69) redacted the credential assignment a role's environment dump
//! left in `experiment/dev1_commands.txt` — but it did so with a rule that ran
//! from `HOH_MODEL_API_KEY=` to the **next `"`**, and the original record is
//! *already truncated mid-token*: the value it was matching was cut off at
//! `…/AppD` and the assignment's closing quote never appears on that line.  The
//! redaction therefore swallowed the line break and the head of the *next*
//! record, and with it the `dir /b -p` command — which is the `-p` defect's own
//! evidence.  The file went 183 records instead of 184.
//!
//! These assertions are about meaning, not about a magic number: record
//! boundaries, line endings, the preserved `-p` record, and the absence of the
//! credential channel.

use std::path::PathBuf;

// The credential-assignment value, replaced **in place** by DR-70: everything
// else in the file is the byte-identical original (see `REDACTION.md`).
const REDACTION_MARKER: &str = "<redacted-key-path-by-DR-69>";

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
}

fn command_dump() -> (PathBuf, Vec<u8>) {
    let path = repo_root().join(".spec/hof-rs/tasks/TASK-SMOKE-T9-evidence/experiment/dev1_commands.txt");
    let bytes = std::fs::read(&path)
        .unwrap_or_else(|error| panic!("the frozen command dump must exist at {path:?}: {error}"));
    (path, bytes)
}

/// The file the round wrote is a **pure-LF** dump of one record per line.  Git's
/// `core.autocrlf` would rewrite every line ending on checkout, which is exactly
/// how DR-69's numbers came apart: the committed blob and the working tree
/// disagreed.  `.gitattributes` pins this tree to no conversion.
#[test]
fn the_frozen_command_dump_keeps_its_line_endings_and_record_count() {
    let (path, bytes) = command_dump();

    let carriage_returns = bytes.iter().filter(|byte| **byte == b'\r').count();
    assert_eq!(
        carriage_returns, 0,
        "{path:?} must stay pure LF: a rewrite that inserts CR destroys the byte identity of \
         every record (DR-70 ⑤)"
    );

    let newlines = bytes.iter().filter(|byte| **byte == b'\n').count();
    let records = bytes.split(|byte| *byte == b'\n').filter(|l| !l.is_empty()).count();
    assert_eq!(
        newlines, 184,
        "{path:?} must keep all 184 line terminators; the DR-69 redaction ate one (DR-70 ⑤)"
    );
    assert_eq!(
        records, 184,
        "{path:?} must keep all 184 records; the DR-69 redaction merged two `s008` records \
         (DR-70 ⑤)"
    );
}

/// `dir /b -p` is not noise: it is the command whose output shows the stray `-p`
/// directory, i.e. the evidence for the defect the round was investigating.
#[test]
fn the_frozen_command_dump_keeps_the_record_that_documents_the_p_directory() {
    let (path, bytes) = command_dump();
    let text = String::from_utf8_lossy(&bytes);

    assert_eq!(
        text.matches("dir /b -p").count(),
        1,
        "{path:?} must keep the `dir /b -p` record: it is the `-p` defect's own evidence, and the \
         DR-69 redaction deleted it (DR-70 ⑤)"
    );
    for record in [
        "s008 rc=0 | set | findstr /i \"HOH\"",
        "s008 rc=0 | dir /b -p;",
    ] {
        assert!(
            text.contains(record),
            "{path:?} must still carry both halves of the `s008` record family: missing `{record}`"
        );
    }
}

/// The one thing that *had* to change: the assignment must not carry the
/// credential channel any more.  The replacement is surgical — the surrounding
/// bytes (including the line break that ends the truncated value) are the
/// original ones.
#[test]
fn the_frozen_command_dump_carries_no_credential_channel() {
    let (path, bytes) = command_dump();
    let text = String::from_utf8_lossy(&bytes);

    // The frozen record is **already truncated mid-token**: the value it carries
    // is `$(cat /c/Users/wyl/AppD` with no closing paren and no closing quote, and
    // the record ends there.  DR-70 replaced exactly that byte run, so the record
    // line still ends where the original one ended.
    let assignment = text
        .lines()
        .find(|line| line.contains("HOH_MODEL_API_KEY"))
        .unwrap_or_else(|| panic!("{path:?} must still carry the `s008` assignment record"));
    assert!(
        assignment.ends_with(&format!("HOH_MODEL_API_KEY=\"{REDACTION_MARKER}")),
        "the truncated assignment value must be replaced in place, without moving the record \
         boundary: {assignment}"
    );
    assert!(
        !text.contains("HOH_MODEL_API_KEY=\"$(cat"),
        "{path:?} must not carry the key-reading command substitution (DR-70 ⑤)"
    );

    // The DR-19 rule's own source of truth for "a known credential": no resolved
    // secret may appear in frozen evidence.  The check is conditional only in the
    // sense that a checkout without a configured credential has nothing to scan
    // for — the assertion above still pins the assignment itself.
    let config = hof_rs::config::load_config(&[]).expect("the shipped configuration must load");
    let secrets = hof_rs::runtime::secrets::known_secrets(&config);
    for secret in &secrets {
        assert!(
            !secret.is_empty() && !text.contains(secret.as_str()),
            "{path:?} must not contain a resolved credential value (DR-70 ⑤)"
        );
    }
}
