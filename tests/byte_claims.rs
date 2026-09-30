//! DR-71 ④: every byte claim in the frozen-evidence record is **computed**.
//!
//! "Self-report vs byte fact" is the defect class that failed DR-69 and then DR-70
//! again, inside DR-70's own correction: `REDACTION.md` said the redaction replaced
//! 54 bytes with a 30-byte marker and that DR-70's own substitution was 25 -> 30,
//! while the measured spans are 52 -> 28 and 23 -> 28.  Hand-written numbers next to
//! bytes a command can measure are the mechanism, so this test closes the class:
//!
//!  * `scripts/byte_claims.py` **computes** the facts (from the two git blobs and the
//!    working tree) and writes the generated block into both documents;
//!  * this test recomputes every value independently, in Rust, and requires the
//!    blocks to agree key by key and in order — so a hand-edited number is red;
//!  * the corrected regions may not carry a hand-written byte count at all;
//!  * the superseded wording is still present and still annotated.
//!
//! Environment: `git` must be on `PATH` and the blobs `dc9d350` / `3adab37` must be
//! reachable — the historical byte facts cannot be recomputed from the working tree
//! alone.  The test fails loudly rather than skipping if either is missing, so it can
//! never pass vacuously.

use std::path::PathBuf;
use std::process::Command;

const DUMP: &str = ".spec/hof-rs/tasks/TASK-SMOKE-T9-evidence/experiment/dev1_commands.txt";
const ORIGINAL_BLOB: &str = "dc9d350";
const DR69_BLOB: &str = "3adab37";

const REDACTION: &str = ".spec/hof-rs/tasks/TASK-SMOKE-T9-evidence/REDACTION.md";
const REPORT: &str = ".spec/hof-rs/tasks/TASK-DR70-REPORT.md";
/// The DR-71 report is a report too: it may not state a byte count of its own
/// either, which is why it carries the same generated block and the same
/// no-hand-written-numbers region as the two records it corrects.
const DR71_REPORT: &str = ".spec/hof-rs/tasks/TASK-DR71-REPORT.md";
const DOCUMENTS: [&str; 3] = [REDACTION, REPORT, DR71_REPORT];

const BEGIN: &str = "<!-- DR-71-BYTE-CLAIMS-BEGIN -->";
const END: &str = "<!-- DR-71-BYTE-CLAIMS-END -->";
const CORRECTED_BEGIN: &str = "<!-- DR-71-CORRECTED-BEGIN -->";
const CORRECTED_END: &str = "<!-- DR-71-CORRECTED-END -->";

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
}

/// The committed bytes of `path` at `rev` — never the working tree.
fn git_blob(rev: &str, path: &str) -> Vec<u8> {
    let output = Command::new("git")
        .arg("-C")
        .arg(repo_root())
        .arg("show")
        .arg(format!("{rev}:{path}"))
        .output()
        .unwrap_or_else(|error| {
            panic!(
                "`git` must be runnable to recompute the historical byte facts (DR-71 ④): {error}"
            )
        });
    assert!(
        output.status.success(),
        "`git show {rev}:{path}` failed, so the byte facts cannot be recomputed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    output.stdout
}

fn records(data: &[u8]) -> usize {
    data.split(|byte| *byte == b'\n')
        .filter(|line| line.iter().any(|byte| !byte.is_ascii_whitespace()))
        .count()
}

fn dir_b_p(data: &[u8]) -> usize {
    data.windows("dir /b -p".len())
        .filter(|window| *window == b"dir /b -p")
        .count()
}

/// The single replaced run: `(removed, inserted)` from the longest common prefix
/// and suffix.
fn substitution(older: &[u8], newer: &[u8]) -> (usize, usize) {
    let limit = older.len().min(newer.len());
    let mut head = 0;
    while head < limit && older[head] == newer[head] {
        head += 1;
    }
    let mut tail = 0;
    while tail < limit - head && older[older.len() - 1 - tail] == newer[newer.len() - 1 - tail] {
        tail += 1;
    }
    (older.len() - head - tail, newer.len() - head - tail)
}

/// Every fact the generated block claims, in the order the generator writes them.
fn computed_facts() -> Vec<(String, String)> {
    let original = git_blob(ORIGINAL_BLOB, DUMP);
    let dr69 = git_blob(DR69_BLOB, DUMP);
    let current = std::fs::read(repo_root().join(DUMP)).expect("the evidence file must exist");
    let (dr69_removed, dr69_inserted) = substitution(&original, &dr69);
    let (work_removed, work_inserted) = substitution(&original, &current);

    let entry = |key: &str, value: String| (key.to_string(), value);
    vec![
        entry("path", DUMP.to_string()),
        entry("original_blob", ORIGINAL_BLOB.to_string()),
        entry("original_bytes", original.len().to_string()),
        entry(
            "original_cr",
            original
                .iter()
                .filter(|byte| **byte == b'\r')
                .count()
                .to_string(),
        ),
        entry(
            "original_lf",
            original
                .iter()
                .filter(|byte| **byte == b'\n')
                .count()
                .to_string(),
        ),
        entry("original_records", records(&original).to_string()),
        entry("original_dir_b_p", dir_b_p(&original).to_string()),
        entry("dr69_blob", DR69_BLOB.to_string()),
        entry("dr69_bytes", dr69.len().to_string()),
        entry(
            "dr69_delta_bytes",
            (dr69.len() as i64 - original.len() as i64).to_string(),
        ),
        entry(
            "dr69_lf",
            dr69.iter()
                .filter(|byte| **byte == b'\n')
                .count()
                .to_string(),
        ),
        entry(
            "dr69_cr",
            dr69.iter()
                .filter(|byte| **byte == b'\r')
                .count()
                .to_string(),
        ),
        entry("dr69_records", records(&dr69).to_string()),
        entry("dr69_dir_b_p", dir_b_p(&dr69).to_string()),
        entry("dr69_replaced_bytes", dr69_removed.to_string()),
        entry("dr69_marker_bytes", dr69_inserted.to_string()),
        entry("worktree_bytes", current.len().to_string()),
        entry(
            "worktree_delta_bytes",
            (current.len() as i64 - original.len() as i64).to_string(),
        ),
        entry(
            "worktree_cr",
            current
                .iter()
                .filter(|byte| **byte == b'\r')
                .count()
                .to_string(),
        ),
        entry(
            "worktree_lf",
            current
                .iter()
                .filter(|byte| **byte == b'\n')
                .count()
                .to_string(),
        ),
        entry("worktree_records", records(&current).to_string()),
        entry("worktree_dir_b_p", dir_b_p(&current).to_string()),
        entry("worktree_replaced_bytes", work_removed.to_string()),
        entry("worktree_marker_bytes", work_inserted.to_string()),
    ]
}

/// The document as text, with line endings normalized for structure scanning.
fn document_text(relative: &str) -> String {
    let raw = std::fs::read(repo_root().join(relative))
        .unwrap_or_else(|error| panic!("{relative} must exist: {error}"));
    String::from_utf8_lossy(&raw).replace("\r\n", "\n")
}

/// The region between two markers that each **own a whole line**.
///
/// Line-anchored on purpose: a report may quote a marker inside prose or inside a
/// pasted `--emit` sample, and such a quotation must not be mistaken for the
/// generated block (that mistake cost this batch one repair).
fn region(text: &str, begin: &str, end: &str) -> Option<String> {
    let mut block: Vec<&str> = Vec::new();
    let mut inside = false;
    for line in text.lines() {
        if !inside {
            if line.trim() == begin {
                inside = true;
            }
            continue;
        }
        if line.trim() == end {
            return Some(block.join("\n"));
        }
        block.push(line);
    }
    None
}

/// `key = value` claim lines of a generated block, in file order.
fn claim_lines(block: &str) -> Vec<(String, String)> {
    block
        .lines()
        .filter_map(|line| {
            let line = line.trim();
            if line.is_empty() {
                return None;
            }
            line.split_once(" = ")
                .map(|(key, value)| (key.trim().to_string(), value.trim().to_string()))
        })
        .collect()
}

/// A generated block must carry exactly one non-claim line (its "do not edit by
/// hand" header naming the generator), so the block cannot grow prose claims.
fn assert_block_shape(relative: &str, block: &str) {
    let headers: Vec<&str> = block
        .lines()
        .map(str::trim)
        .filter(|line| !line.is_empty() && !line.contains(" = "))
        .collect();
    assert_eq!(
        headers.len(),
        1,
        "{relative}: a generated block carries exactly one header line, found {headers:?}"
    );
    assert!(
        headers[0].contains("scripts/byte_claims.py"),
        "{relative}: the header must name the generating command: {}",
        headers[0]
    );
}

#[test]
fn the_generated_byte_claims_match_the_computed_facts() {
    let expected = computed_facts();
    for relative in DOCUMENTS {
        let text = document_text(relative);
        let block = region(&text, BEGIN, END)
            .unwrap_or_else(|| panic!("{relative} must contain a generated byte-claims block"));
        assert_block_shape(relative, &block);
        let actual = claim_lines(&block);
        assert_eq!(
            actual, expected,
            "{relative}: the generated claims must equal the recomputed facts, key by key and in \
             order.  Regenerate with `python scripts/byte_claims.py --write`; never edit a number \
             by hand (DR-71 ④)."
        );
    }
}

/// The corrected values must be *reachable* from the generated block, and the region
/// that states the correction must not carry a hand-written byte count.
#[test]
fn the_corrected_record_states_no_hand_written_byte_count() {
    for relative in DOCUMENTS {
        let text = document_text(relative);
        let corrected = region(&text, CORRECTED_BEGIN, CORRECTED_END).unwrap_or_else(|| {
            panic!("{relative} must carry a DR-71 corrected region between the markers")
        });
        for key in [
            "dr69_replaced_bytes",
            "dr69_marker_bytes",
            "worktree_replaced_bytes",
            "worktree_marker_bytes",
        ] {
            assert!(
                corrected.contains(key),
                "{relative}: the corrected region must name the generated key `{key}` it relies \
                 on, so the correction points at computed values instead of restating them"
            );
        }
        let hand_written = hand_written_byte_counts(&corrected);
        assert!(
            hand_written.is_empty(),
            "{relative}: the corrected region must not state byte counts of its own (found \
             {hand_written:?}); byte claims belong to the generated block (DR-71 ④)"
        );
    }
}

/// The superseded wording — the wrong numbers — must still be present and annotated,
/// not silently rewritten away.
#[test]
fn the_superseded_byte_counts_are_preserved_and_annotated() {
    let redaction = document_text(REDACTION);
    for legacy in [
        // DR-70's own (wrong) prose, preserved.
        "replacing 54 bytes with a 30-byte marker",
        "(25 bytes) became",
        // DR-69's superseded sentence, preserved verbatim under its heading.
        "**53 bytes** were removed",
    ] {
        assert!(
            redaction.contains(legacy),
            "REDACTION.md must keep the superseded wording verbatim: `{legacy}`"
        );
    }
    assert!(
        redaction.contains("DR-71: both figures are wrong"),
        "REDACTION.md must annotate the superseded figures as corrected, in place"
    );

    let report = document_text(REPORT);
    for legacy in ["(25 B)", "30 B"] {
        assert!(
            report.contains(legacy),
            "TASK-DR70-REPORT.md must keep its superseded wording verbatim: `{legacy}`"
        );
    }
    assert!(
        report.contains("DR-71 更正"),
        "TASK-DR70-REPORT.md must annotate the superseded figures as corrected"
    );
}

/// `<number>` followed by a byte unit, e.g. `52 bytes`, `(25 B)`, `28 字节`.
fn hand_written_byte_counts(text: &str) -> Vec<String> {
    let lower = text.to_lowercase();
    let bytes = lower.as_bytes();
    let mut found = Vec::new();
    let mut index = 0;
    while index < bytes.len() {
        if !bytes[index].is_ascii_digit() {
            index += 1;
            continue;
        }
        let start = index;
        while index < bytes.len() && bytes[index].is_ascii_digit() {
            index += 1;
        }
        let number = lower[start..index].to_string();
        let mut probe = index;
        if probe < bytes.len() && bytes[probe] == b'-' {
            probe += 1;
        }
        while probe < bytes.len() && bytes[probe] == b' ' {
            probe += 1;
        }
        let rest: String = lower[probe..].chars().take(4).collect();
        let is_bytes = rest.starts_with("byte") || rest.starts_with("字节");
        let is_short = rest.starts_with('b')
            && rest[1..]
                .chars()
                .next()
                .map(|next| !next.is_ascii_alphanumeric())
                .unwrap_or(true);
        if is_bytes || is_short {
            found.push(number);
        }
    }
    found
}

/// Non-vacuity: the detector really recognises a hand-written claim, and really
/// ignores a key name and a decision id.
#[test]
fn the_hand_written_claim_detector_works() {
    assert_eq!(
        hand_written_byte_counts("replacing 54 bytes with a 30-byte marker"),
        vec!["54".to_string(), "30".to_string()]
    );
    assert_eq!(
        hand_written_byte_counts("the value (25 B) and 28 字节"),
        vec!["25".to_string(), "28".to_string()]
    );
    assert!(
        hand_written_byte_counts("`dr69_replaced_bytes` and `worktree_marker_bytes` and DR-71")
            .is_empty(),
        "a generated key name and a decision id are not byte claims"
    );
    // The runner numerals of the real region must not trip it either.
    assert!(hand_written_byte_counts("DR-69 与 DR-70，§3.5，`52`/`28`").is_empty());
}
