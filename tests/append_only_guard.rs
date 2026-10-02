//! DR-80 ⑤ — the **mechanical append-only guard**.
//!
//! The DR-79 erratum established the rule (`DECISIONS.md` D289): a correction to a
//! historical report may only be **appended** — the original bytes stay verbatim, the
//! machine-readable block and every evidence string stay untouched, and a superseded
//! number keeps its old value next to an explicit `incorrect`/`superseded` marker.
//!
//! DR-79's own acceptance proved the rule is checkable: a reviewer who compares the
//! working file's prefix against the committed blob, and the `json` block against the
//! round's own `machine_block.json`, catches an in-place edit, a deleted line and a
//! block edit.  But D-3 found that **nothing in the repository does that check** — it
//! was discipline, not a gate, and `grep` over `*.rs`/`*.py` found no reference to the
//! corrected report at all.
//!
//! This file is that gate.  Precedent: `tests/byte_claims.rs` pins
//! `TASK-DR70-REPORT.md` and `tests/dr77_evidence_tightening.rs` pins
//! `TASK-DR73-REPORT.md`; this guard generalises the idea to the append-only property
//! itself and covers the two reports that carry errata (`TASK-SMOKE-T13-REPORT.md`
//! grew the DR-79 error and the DR-80 correction; `TASK-DR73-REPORT.md` grew the
//! DR-76 correction ledger and the DR-77 clearance) plus the frozen requirements
//! document, whose C3 sentence may never be rewritten.
//!
//! What each guard asserts, per document:
//!
//!  * the correction/erratum heading is present **as a whole line** (a quotation of
//!    the heading inside prose does not satisfy it);
//!  * the bytes *before* that heading hash to a pinned length and sha256 — so an
//!    in-place edit, a deleted line, a reordered paragraph, a rewritten line ending or
//!    a truncated file before the seal is red, while appending after the seal is not;
//!  * for the round report, the line-anchored ```json machine-readable block inside
//!    the sealed prefix hashes to a pinned length and sha256 as well, so a tamper
//!    inside the block is named by its own test rather than only by the prefix.
//!
//! Every pin below was computed from the frozen bytes by the commands quoted in
//! `.spec/hof-rs/tasks/TASK-DR80-REPORT.md`; the pins are the mechanism, and a wrong
//! pin fails loudly rather than passing vacuously.
//!
//! The three plants that prove the guard is not vacuous run in
//! `the_seal_checks_redden_on_temporary_copies`: an in-place edit, a deleted line and
//! an edit inside the machine-readable block, each applied to a **temporary copy** in
//! the OS temp directory — the real reports are read-only to this file by construction.

use std::path::PathBuf;

use sha2::{Digest, Sha256};

/// The reproducibility report: it carries the DR-79 erratum and the DR-80 correction.
const T13_REPORT: &str = ".spec/hof-rs/tasks/TASK-SMOKE-T13-REPORT.md";
/// The E3-clearance report: it carries the DR-76 correction ledger and DR-77 §12.1.
const DR73_REPORT: &str = ".spec/hof-rs/tasks/TASK-DR73-REPORT.md";
/// The frozen requirements document: its C3 sentence may never be rewritten.
const REQUIREMENTS: &str = ".spec/hof-rs/REQUIREMENTS.md";

/// The DR-79 erratum heading: the seal of the report **as it stood before the first
/// erratum**.  Everything before it is the round's own text and may not move.
const T13_ERRATUM_HEADING: &str = "# 附：DR-79 勘误（**追加式**，2026-10-02）";
const T13_PRE_ERRATUM_BYTES: usize = 107_709;
const T13_PRE_ERRATUM_SHA256: &str =
    "9bbe81c8360d481ef01528f99467cd1253921ff713980336da05a32e3ea9fd36";

/// The DR-80 correction heading: the seal of the report **including the DR-79
/// erratum**, so the erratum's own numbers are frozen too and only a further append is
/// permitted.
const T13_DR80_HEADING: &str = "# 附：DR-80 更正（**追加式**，2026-10-02）";
const T13_PRE_DR80_BYTES: usize = 134_085;
const T13_PRE_DR80_SHA256: &str =
    "2f2a2418bc3d0785ec47235da7c868ee64f590e73b38f3e3c7619696d74945a9";

/// The line-anchored ```json machine-readable block of the T13 report, byte-identical
/// to `runs/smoke-t13/evidence/analysis/machine_block.json` (34,699 B / `36e34d0d…`).
const T13_BLOCK_BYTES: usize = 34_699;
const T13_BLOCK_SHA256: &str = "36e34d0d0436920605fb3f06065c1c8e4303bbf90b92a499d5e37f6f8d6c3c9f";

/// The DR-76 correction ledger heading: the seal of `TASK-DR73-REPORT.md` before any
/// correction was appended.
const DR73_LEDGER_HEADING: &str =
    "## 12. DR-76 更正台账（**superseded 标注**，2026-10-01 由 DR-76 追加）";
const DR73_PRE_LEDGER_BYTES: usize = 48_811;
const DR73_PRE_LEDGER_SHA256: &str =
    "db0a5a7a5c2086b46250582748fd08a27c7764d5f935922655acc4658da1543c";
/// The DR-77 markers that must survive inside the DR-73 record (DR-77 ① pinned them
/// for `tests/dr77_evidence_tightening.rs`; the append-only guard must not lose them).
const DR73_DR77_MARKERS: [&str; 4] = [
    "<!-- DR-77-COMMIT-QUOTE-BEGIN -->",
    "<!-- DR-77-COMMIT-QUOTE-END -->",
    "<!-- DR-77-INCORRECT-QUOTE-BEGIN -->",
    "<!-- DR-77-INCORRECT-QUOTE-END -->",
];

/// The DR-80 annotation appended to the requirements document.  Everything before its
/// heading — including the C3 row verbatim — is sealed.
const REQ_DR80_HEADING: &str = "# DR-80 注（追加式，2026-10-02）";
const REQ_PRE_DR80_BYTES: usize = 20_910;
const REQ_PRE_DR80_SHA256: &str =
    "7b551ca08c4c5abf15a95cb8edcc4977ce8d03c649654ab4a5ab01f649cae5ae";

/// The C3 sentence, byte-for-byte, that may never be rewritten (only annotated).
const C3_SENTENCE: &str =
    "实测版本串 `4.8.dev.mono.custom_build.ba1587c71`（构建于 anchor `ba1587c71`）";
/// The string every real round actually measures (T11/T12/T13 `meta.json`).
const MEASURED_ENGINE_VERSION: &str = "4.8.dev.mono.custom_build.035edfce7";

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
}

fn read(relative: &str) -> Vec<u8> {
    let path = repo_root().join(relative);
    std::fs::read(&path)
        .unwrap_or_else(|error| panic!("`{}` must be readable: {error}", path.display()))
}

fn sha256_hex(bytes: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(bytes);
    let digest = hasher.finalize();
    digest.iter().map(|byte| format!("{byte:02x}")).collect()
}

/// The first occurrence of `needle` in `haystack`, as a byte offset.
fn find_bytes(haystack: &[u8], needle: &[u8]) -> Option<usize> {
    if needle.is_empty() || haystack.len() < needle.len() {
        return None;
    }
    (0..=haystack.len() - needle.len())
        .find(|start| &haystack[*start..*start + needle.len()] == needle)
}

/// The offset of a marker that **owns a whole line**, so a quotation of the heading
/// inside prose cannot be mistaken for the seal.
fn whole_line_offset(bytes: &[u8], marker: &str) -> Result<usize, String> {
    let needle = marker.as_bytes();
    let mut from = 0usize;
    while let Some(relative) = find_bytes(&bytes[from..], needle) {
        let at = from + relative;
        let line_start = at == 0 || bytes[at - 1] == b'\n';
        let end = at + needle.len();
        let line_end = end == bytes.len() || bytes[end] == b'\n' || bytes[end] == b'\r';
        if line_start && line_end {
            return Ok(at);
        }
        from = at + 1;
    }
    Err(format!("the whole-line marker `{marker}` is absent"))
}

/// `(start, end)` for every line, where `end` excludes the terminating `\n`.
fn line_spans(bytes: &[u8]) -> Vec<(usize, usize)> {
    let mut spans = Vec::new();
    let mut start = 0usize;
    for (index, byte) in bytes.iter().enumerate() {
        if *byte == b'\n' {
            spans.push((start, index));
            start = index + 1;
        }
    }
    if start < bytes.len() {
        spans.push((start, bytes.len()));
    }
    spans
}

/// The single line-anchored ```json fenced block, as `(content_start, content_end)`.
fn fenced_json_block(bytes: &[u8]) -> Result<(usize, usize), String> {
    let spans = line_spans(bytes);
    let trimmed = |span: (usize, usize)| -> Vec<u8> {
        let mut line = &bytes[span.0..span.1];
        while let Some((last, rest)) = line.split_last() {
            if *last == b'\r' {
                line = rest;
            } else {
                break;
            }
        }
        line.to_vec()
    };
    let mut open: Option<(usize, usize)> = None;
    let mut found = 0usize;
    for span in &spans {
        if trimmed(*span) == b"```json" {
            if open.is_none() {
                open = Some(*span);
                found += 1;
            } else {
                return Err("more than one ```json opening fence".to_string());
            }
        }
    }
    if found == 0 {
        return Err("no line-anchored ```json opening fence".to_string());
    }
    let (open_start, open_end) = open.expect("checked above");
    if open_end >= bytes.len() {
        return Err("the ```json opening fence is the last line".to_string());
    }
    let content_start = open_end + 1;
    let close = spans
        .iter()
        .find(|span| span.0 > open_start && trimmed(**span) == b"```")
        .ok_or_else(|| "no closing ``` fence after the opening fence".to_string())?;
    Ok((content_start, close.0))
}

/// The violations of an append-only seal, empty when the document is intact.
///
/// The seal is the byte prefix that ends where `marker` begins: it must still be there,
/// and its length and sha256 must equal the pinned values.  A file that merely *starts*
/// correctly but is shorter than the seal is a violation too.
fn seal_violations(
    relative: &str,
    marker: &str,
    pin_bytes: usize,
    pin_sha: &str,
    bytes: &[u8],
) -> Vec<String> {
    let mut violations = Vec::new();
    let offset = match whole_line_offset(bytes, marker) {
        Ok(offset) => offset,
        Err(problem) => {
            violations.push(format!("{relative}: {problem}"));
            return violations;
        }
    };
    if offset != pin_bytes {
        violations.push(format!(
            "{relative}: the seal `{marker}` begins at byte {offset}, but the pinned prefix ends at \
             {pin_bytes}; text before the correction was edited, deleted or shifted"
        ));
        return violations;
    }
    let actual = sha256_hex(&bytes[..offset]);
    if actual != pin_sha {
        violations.push(format!(
            "{relative}: the {offset} bytes before the correction hash to {actual}, not the pinned \
             {pin_sha}; the frozen prefix was rewritten in place (append-only is violated)"
        ));
    }
    violations
}

/// The violations of the frozen machine-readable block, empty when it is intact.
fn block_violations(relative: &str, pin_bytes: usize, pin_sha: &str, bytes: &[u8]) -> Vec<String> {
    let mut violations = Vec::new();
    let (start, end) = match fenced_json_block(bytes) {
        Ok(block) => block,
        Err(problem) => {
            violations.push(format!("{relative}: {problem}"));
            return violations;
        }
    };
    let block = &bytes[start..end];
    if block.len() != pin_bytes {
        violations.push(format!(
            "{relative}: the ```json block is {} bytes, not the pinned {pin_bytes}",
            block.len()
        ));
    }
    let actual = sha256_hex(block);
    if actual != pin_sha {
        violations.push(format!(
            "{relative}: the ```json block hashes to {actual}, not the pinned {pin_sha}; the \
             machine-readable record was edited"
        ));
    }
    violations
}

fn assert_no_violations(violations: Vec<String>) {
    assert!(
        violations.is_empty(),
        "the append-only guard found {} violation(s):\n{}",
        violations.len(),
        violations.join("\n")
    );
}

/// The report as it stood **before the first erratum** is frozen: the DR-79 heading
/// must own a whole line and the 107,709 bytes before it must hash to `9bbe81c8…`.
/// This is the test that an in-place edit or a deleted line in the round's own text
/// reddens.
#[test]
fn the_t13_report_prefix_before_the_dr79_erratum_is_frozen() {
    let bytes = read(T13_REPORT);
    assert_no_violations(seal_violations(
        T13_REPORT,
        T13_ERRATUM_HEADING,
        T13_PRE_ERRATUM_BYTES,
        T13_PRE_ERRATUM_SHA256,
        &bytes,
    ));
}

/// The report **including the DR-79 erratum** is frozen as well: the DR-80 correction
/// may only sit after the DR-80 heading, so the erratum's own numbers cannot be
/// rewritten either.
#[test]
fn the_t13_report_prefix_before_the_dr80_correction_is_frozen() {
    let bytes = read(T13_REPORT);
    assert_no_violations(seal_violations(
        T13_REPORT,
        T13_DR80_HEADING,
        T13_PRE_DR80_BYTES,
        T13_PRE_DR80_SHA256,
        &bytes,
    ));
}

/// The machine-readable block is pinned in its own right, so a tamper inside it is
/// named by its own test even though the prefix seal would also catch it.
#[test]
fn the_t13_machine_readable_block_is_byte_frozen() {
    let bytes = read(T13_REPORT);
    assert_no_violations(block_violations(
        T13_REPORT,
        T13_BLOCK_BYTES,
        T13_BLOCK_SHA256,
        &bytes,
    ));
}

/// `TASK-DR73-REPORT.md` keeps its correction ledger and its DR-77 markers, and the
/// bytes before the ledger heading are frozen.
#[test]
fn the_dr73_report_prefix_before_its_correction_ledger_is_frozen() {
    let bytes = read(DR73_REPORT);
    assert_no_violations(seal_violations(
        DR73_REPORT,
        DR73_LEDGER_HEADING,
        DR73_PRE_LEDGER_BYTES,
        DR73_PRE_LEDGER_SHA256,
        &bytes,
    ));
    let text = String::from_utf8_lossy(&bytes);
    for marker in DR73_DR77_MARKERS {
        assert!(
            text.contains(marker),
            "{DR73_REPORT}: the DR-77 marker `{marker}` must survive; the record keeps the wrong \
             quotation next to the true one"
        );
    }
}

/// The requirements document keeps C3 **verbatim** and carries the append-only DR-80
/// note that names the measured engine string, with everything before the note sealed.
#[test]
fn the_requirements_document_keeps_c3_and_carries_the_dr80_note() {
    let bytes = read(REQUIREMENTS);
    let text = String::from_utf8_lossy(&bytes);
    assert!(
        text.contains(C3_SENTENCE),
        "{REQUIREMENTS}: the C3 sentence must stay verbatim (it may only be annotated, never \
         rewritten): `{C3_SENTENCE}`"
    );
    assert!(
        whole_line_offset(&bytes, REQ_DR80_HEADING).is_ok(),
        "{REQUIREMENTS}: the append-only DR-80 note must be present as a whole-line heading \
         `{REQ_DR80_HEADING}`"
    );
    assert!(
        text.contains(MEASURED_ENGINE_VERSION),
        "{REQUIREMENTS}: the DR-80 note must name the measured engine string \
         `{MEASURED_ENGINE_VERSION}` (every round's meta.json records it)"
    );
    assert_no_violations(seal_violations(
        REQUIREMENTS,
        REQ_DR80_HEADING,
        REQ_PRE_DR80_BYTES,
        REQ_PRE_DR80_SHA256,
        &bytes,
    ));
}

/// Non-vacuity: the three tamper shapes really do produce violations, on **temporary
/// copies**, and the real reports are not touched by this test.
///
/// * an in-place edit of one byte in the frozen prefix;
/// * a deleted line in the frozen prefix;
/// * an in-place edit inside the machine-readable block.
#[test]
fn the_seal_checks_redden_on_temporary_copies() {
    let pristine = read(T13_REPORT);
    let before_sha = sha256_hex(&pristine);

    let temp = std::env::temp_dir().join(format!("hoh-append-only-guard-{}", std::process::id()));
    std::fs::create_dir_all(&temp).expect("the temporary directory must be creatable");

    // ① an in-place edit: the first `|` of the report becomes `!`
    let mut in_place = pristine.clone();
    let pipe = in_place
        .iter()
        .position(|byte| *byte == b'|')
        .expect("the report carries tables");
    in_place[pipe] = b'!';
    // ② a deleted line: drop the first table row, which lives in the frozen prefix
    let mut deleted = pristine.clone();
    let spans = line_spans(&pristine);
    let victim = spans
        .iter()
        .find(|span| pristine[span.0..span.1].starts_with(b"| "))
        .map(|span| *span)
        .expect("the report carries a markdown table");
    deleted.drain(victim.0..victim.1 + 1);
    // ③ an edit inside the machine-readable block: flip one byte of the pinned block
    let mut block_edit = pristine.clone();
    let (start, end) = fenced_json_block(&pristine).expect("the report carries its json block");
    let mut at = start;
    while at < end && block_edit[at] == b' ' {
        at += 1;
    }
    block_edit[at] = if block_edit[at] == b'{' { b'[' } else { b'{' };

    let cases: [(&str, &Vec<u8>); 3] = [
        ("in_place", &in_place),
        ("deleted_line", &deleted),
        ("block_edit", &block_edit),
    ];

    let mut results = Vec::new();
    for (name, mutant) in cases {
        let path = temp.join(format!("{name}.md"));
        std::fs::write(&path, mutant).expect("the temporary copy must be writable");
        let copy = std::fs::read(&path).expect("the temporary copy must be readable");
        assert_eq!(
            &copy, mutant,
            "the temporary copy must round-trip byte for byte"
        );
        let seal = seal_violations(
            T13_REPORT,
            T13_ERRATUM_HEADING,
            T13_PRE_ERRATUM_BYTES,
            T13_PRE_ERRATUM_SHA256,
            &copy,
        );
        let block = block_violations(T13_REPORT, T13_BLOCK_BYTES, T13_BLOCK_SHA256, &copy);
        results.push((name, seal.len(), block.len()));
        std::fs::remove_file(&path).expect("the temporary copy must be removable");
    }
    let _ = std::fs::remove_dir(&temp);

    // The pristine bytes must satisfy both guards, or the mutants prove nothing.
    assert!(
        seal_violations(
            T13_REPORT,
            T13_ERRATUM_HEADING,
            T13_PRE_ERRATUM_BYTES,
            T13_PRE_ERRATUM_SHA256,
            &pristine
        )
        .is_empty()
            && block_violations(T13_REPORT, T13_BLOCK_BYTES, T13_BLOCK_SHA256, &pristine)
                .is_empty(),
        "the guard must accept the pristine report before it is asked to reject mutants"
    );
    let mut report = Vec::new();
    for (name, seal, block) in &results {
        report.push(format!("{name}: seal={seal} block={block}"));
    }
    assert!(
        results.iter().all(|(_, seal, _)| *seal > 0),
        "every mutant must trip the prefix seal:\n{}",
        report.join("\n")
    );
    assert!(
        results[2].2 > 0,
        "the block edit must trip the machine-readable block guard:\n{}",
        report.join("\n")
    );
    // The first two mutants are outside the block on purpose: the block guard must
    // stay quiet for them, so the two guards are shown to be independent checks
    // rather than one check counted twice.
    assert_eq!(
        (results[0].2, results[1].2),
        (0, 0),
        "an edit or a deletion outside the block must not be reported as a block edit:\n{}",
        report.join("\n")
    );

    // The real report is read-only to this test: its bytes are unchanged.
    let after = read(T13_REPORT);
    assert_eq!(
        before_sha,
        sha256_hex(&after),
        "the real report must not be modified by this test"
    );
}
