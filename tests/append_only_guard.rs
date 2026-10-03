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
/// DR-82 ③: the implementation report whose "**a running** editor does not rebuild
/// `.godot`" claim `smoke-t15` weakened.  Its correction is append-only too.
const DR81_REPORT: &str = ".spec/hof-rs/tasks/TASK-DR81-REPORT.md";
/// DR-82 ③: the seal of `TASK-DR81-REPORT.md` **before the DR-82 correction**.
///
/// The 41,045 bytes are byte-identical to `7834f2d7…8efc8`, the value
/// `TASK-DR81-ACCEPTANCE.md` recorded as `report_sha256_at_review` — i.e. the
/// frozen prefix is exactly the revision the independent acceptance reviewed, so
/// this pin also fixes what the correction supersedes.
const DR81_DR82_HEADING: &str =
    "# 附：DR-82 ③ 更正（**追加式**，2026-10-02）——“已在运行的编辑器不会重建 `.godot`”被实测削弱";
/// DR-82 ④ (A-3): the second appended correction, for the report's internal
/// contradiction about the real acceptance ledger.
const DR81_A3_HEADING: &str =
    "# 附：DR-82 ④（A-3）更正（**追加式**，2026-10-02）——修订报告在「真实台账」一处**自相矛盾**";
const DR81_PRE_DR82_BYTES: usize = 41_045;
const DR81_PRE_DR82_SHA256: &str =
    "7834f2d71d970d5a27b95c6fcc5a339525616c3a08bfe23dbf20e9ac8048efc8";
/// The frozen requirements document: its C3 sentence may never be rewritten.
const REQUIREMENTS: &str = ".spec/hof-rs/REQUIREMENTS.md";
/// DR-84: the implementation report whose item 2 published a **key count** as a
/// census of the redaction.  The DR-82 acceptance reclassified that as report
/// prose (DR82A-1) and the DR-83 acceptance recorded it as still open (DR83A-1);
/// DR-84 closes it in the appended region below this heading.
const DR82_REPORT: &str = ".spec/hof-rs/tasks/TASK-DR82-REPORT.md";
const DR82_DR84_HEADING: &str =
    "# 附：DR-84 更正（**追加式**，2026-10-02）——第 2 项的键计数不是「取值已处理」的证据";
/// DR-85: the **seal marker** of the DR-82 report's frozen prefix — the correction
/// heading *with the line terminator the append starts with*.
///
/// The frozen revision is 44,184 bytes and ends with `\n`; the correction was
/// appended as `\n# 附：DR-84 …`, so the heading's own `#` sits at offset 44,185
/// and the sealed prefix `bytes[..44_184]` is exactly the revision
/// `TASK-DR84-ACCEPTANCE.md` reviewed (`319397fd…e406`).  `whole_line_offset` finds
/// a marker at the offset where the marker *begins*, so the marker used for the
/// seal carries that leading terminator: it is the first byte the correction
/// contributed, and it makes the pinned length the reviewed revision's own length
/// rather than one byte more.  The heading is still separately asserted as a
/// whole line ([`DR82_DR84_HEADING`]).
const DR82_DR84_SEAL: &str =
    "\n# 附：DR-84 更正（**追加式**，2026-10-02）——第 2 项的键计数不是「取值已处理」的证据";
/// DR-85: the frozen prefix of `TASK-DR82-REPORT.md` — the revision before the
/// DR-84 correction, byte for byte.
const DR82_PRE_DR84_BYTES: usize = 44_184;
const DR82_PRE_DR84_SHA256: &str =
    "319397fdb369ea95c63e2eac7d4eaacd25b7825e73313e9afe863f5eb1a8e406";

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
/// DR-89 ⑤: the annotation that brings E5's **text** level with the reading the
/// code has enforced since DR-88.  It is appended after the DR-80 note, so the
/// 20,910-byte sealed prefix (E5's own row inside it) cannot move.
const REQ_DR89_HEADING: &str =
    "# DR-89 注（追加式，2026-10-03）——E5 的读数已强于该行文本；追加不改封印前缀";

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

/// DR-82 ③: the `.godot` mechanism claim in `TASK-DR81-REPORT.md` was weakened by
/// `smoke-t15`'s measurement, so the correction had to be appended to the report
/// that carries the claim — and appending is only meaningful if the bytes above
/// the correction cannot move afterwards.
///
/// The sealed prefix is the revision `TASK-DR81-ACCEPTANCE.md` reviewed
/// (`7834f2d7…8efc8`, 41,045 B); this test reddens on an in-place edit, a deleted
/// line or a reordered paragraph in the report's own text, while the DR-82
/// erratum after the heading is free to grow.
#[test]
fn the_dr81_report_prefix_before_the_dr82_correction_is_frozen() {
    let bytes = read(DR81_REPORT);
    assert_no_violations(seal_violations(
        DR81_REPORT,
        DR81_DR82_HEADING,
        DR81_PRE_DR82_BYTES,
        DR81_PRE_DR82_SHA256,
        &bytes,
    ));
    let text = String::from_utf8_lossy(&bytes);
    // The corrected claim must be *present* as well: the seal proves nothing if the
    // erratum was deleted (the offset check would then fail first, but a reader of
    // this test should see the intent).
    assert!(
        text.contains(DR81_DR82_HEADING),
        "{DR81_REPORT}: the DR-82 correction heading must own a whole line"
    );
    assert!(
        text.contains("smoke-t15") && text.contains("filesystem_cache10"),
        "{DR81_REPORT}: the correction must name the measurement it rests on"
    );
    // DR-82 ④ (A-3): the second appended correction — the report's internal
    // contradiction about the real ledger — must live in the same append-only
    // region, so it is covered by the same seal.
    assert!(
        text.contains(DR81_A3_HEADING),
        "{DR81_REPORT}: the A-3 correction must name the contradiction it resolves"
    );
    assert!(
        text.contains("OK: 48 record(s)"),
        "{DR81_REPORT}: the A-3 correction must carry the reading it measured"
    );
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

/// DR-89 ⑤: the E5 row's **text** still claims only hash equality, while the code
/// has enforced more since DR-88 (a cache-file write inside the frozen candidate
/// view rejects the round).  The annotation that levels them is an **append**: the
/// 20,910-byte sealed prefix — E5's own row inside it — stays byte-for-byte, and
/// the note names both the enforced reading and the one residual it cannot close
/// (the workspace-side excluded paths, unwatched on purpose, D294).
#[test]
fn the_requirements_e5_row_carries_its_dr89_annotation_and_the_seal_still_holds() {
    let bytes = read(REQUIREMENTS);
    assert_no_violations(seal_violations(
        REQUIREMENTS,
        REQ_DR80_HEADING,
        REQ_PRE_DR80_BYTES,
        REQ_PRE_DR80_SHA256,
        &bytes,
    ));
    let offset = whole_line_offset(&bytes, REQ_DR89_HEADING).unwrap_or_else(|problem| {
        panic!("{REQUIREMENTS}: the DR-89 note heading must own a whole line: {problem}")
    });
    assert!(
        offset > REQ_PRE_DR80_BYTES,
        "{REQUIREMENTS}: the DR-89 note must sit after the sealed prefix, never inside it"
    );
    let text = String::from_utf8_lossy(&bytes);
    assert!(
        text[..offset].contains("| E5 | QA 未修改 A_1（快照 hash 前后一致） | 快照 hash 对比 |"),
        "{REQUIREMENTS}: the sealed E5 row must survive verbatim above the note"
    );
    let note = &text[offset..];
    for required in [
        "qa_wrote_cache_",
        "qa_contaminated_",
        "QaContaminatedCandidate",
        "hash_tree",
        "候选视图",
        "工作区",
        "7b551ca0",
    ] {
        assert!(
            note.contains(required),
            "{REQUIREMENTS}: the DR-89 note must carry `{required}`; a reader of the sealed row \
             must be able to see what the code now enforces and what it still cannot see"
        );
    }

    // Non-vacuity, on **in-memory** copies: an edit of the row itself trips the
    // seal, while an append stays permitted.  The real document is never written.
    let row = find_bytes(&bytes, "| E5 |".as_bytes()).expect("the sealed E5 row must be present");
    let mut mutant = bytes.clone();
    mutant[row + 2] = b'X';
    assert!(
        !seal_violations(
            REQUIREMENTS,
            REQ_DR80_HEADING,
            REQ_PRE_DR80_BYTES,
            REQ_PRE_DR80_SHA256,
            &mutant
        )
        .is_empty(),
        "an edit inside the sealed prefix must trip the requirements seal"
    );
    let mut appended = bytes.clone();
    appended.extend_from_slice(b"\nmore annotation\n");
    assert!(
        seal_violations(
            REQUIREMENTS,
            REQ_DR80_HEADING,
            REQ_PRE_DR80_BYTES,
            REQ_PRE_DR80_SHA256,
            &appended
        )
        .is_empty(),
        "appending after the sealed prefix must stay permitted"
    );
    assert_eq!(
        sha256_hex(&bytes),
        sha256_hex(&read(REQUIREMENTS)),
        "the real document must not be modified by this test"
    );
}

/// DR-84: the census claim in `TASK-DR82-REPORT.md` carries its qualifier.
///
/// The DR-82 batch published `real_file_census.names_as_keys_per_file = 16` with
/// two counting methods that both count **key occurrences**.  A key count is
/// identical before and after a redaction that preserves the key and replaces only
/// the value, so it cannot evidence that a value was handled (DR82A-1, still open
/// as DR83A-1).  The correction is appended below this heading — never edited into
/// the report's own text — and it must name both the reason and the raw sidecars
/// that remain.
#[test]
fn the_dr82_census_claim_carries_its_dr84_qualifier() {
    let bytes = read(DR82_REPORT);
    let offset = whole_line_offset(&bytes, DR82_DR84_HEADING).unwrap_or_else(|problem| {
        panic!("{DR82_REPORT}: the DR-84 correction heading must own a whole line: {problem}")
    });
    // DR-85: the prefix really is sealed.  Before this, the pin checked only the
    // heading's whole-line-ness and three substrings, so an in-place edit of a
    // value inside the report's machine-readable block, or of any prose byte above
    // the heading, stayed green (DR84A-1).  `seal_violations` is the helper every
    // other seal in this file uses; it pins the byte length **and** the sha256 of
    // the bytes before the correction.
    assert_no_violations(seal_violations(
        DR82_REPORT,
        DR82_DR84_SEAL,
        DR82_PRE_DR84_BYTES,
        DR82_PRE_DR84_SHA256,
        &bytes,
    ));
    assert_eq!(
        whole_line_offset(&bytes, DR82_DR84_SEAL),
        Ok(DR82_PRE_DR84_BYTES),
        "the correction — with the blank separator line it starts with — must begin exactly where \
         the reviewed revision ends ({DR82_PRE_DR84_BYTES} bytes)"
    );
    assert_eq!(
        offset,
        DR82_PRE_DR84_BYTES + 1,
        "the heading's own `#` follows the blank separator line, so it sits one byte past the \
         sealed prefix"
    );
    let text = String::from_utf8_lossy(&bytes);
    let correction = &text[offset..];
    for required in ["names_as_keys_per_file", "键计数", "raw=0", "sidecar"] {
        assert!(
            correction.contains(required),
            "{DR82_REPORT}: the appended correction must carry `{required}`; a reader of the \
             original claim must be able to see why a key count is not handling evidence"
        );
    }
    // The claim itself is still readable above the correction — the correction is an
    // append, not a rewrite.  (The seal above is what proves it was not rewritten;
    // this assertion names the intent.)
    assert!(
        text[..offset].contains("names_as_keys_per_file"),
        "{DR82_REPORT}: the appended correction must not be a replacement for the claim"
    );
}

/// DR-85: the DR-82 seal is **not vacuous** — the two plants the DR-84 acceptance
/// used to expose the gap redden it now, on in-memory copies of the real bytes.
///
/// The first mutant edits a value **inside the machine-readable block** (the block
/// is part of the sealed prefix, so the prefix hash names it); the second edits an
/// unrelated prose byte in the prefix.  Both stayed green under the old pin and
/// both trip `seal_violations` now.  The real report is never written.
#[test]
fn the_dr82_seal_reddens_on_a_block_edit_and_a_prose_edit() {
    let pristine = read(DR82_REPORT);
    assert!(
        seal_violations(
            DR82_REPORT,
            DR82_DR84_SEAL,
            DR82_PRE_DR84_BYTES,
            DR82_PRE_DR84_SHA256,
            &pristine
        )
        .is_empty(),
        "the guard must accept the pristine report before it is asked to reject mutants"
    );

    // ① a value inside the report's machine-readable block.  The block sits inside
    //    the sealed prefix; the fixture edits the `16` of the census claim.
    let needle = b"\"names_as_keys_per_file\": 16";
    let at = find_bytes(&pristine, needle)
        .unwrap_or_else(|| panic!("{DR82_REPORT}: the block claim must be present"));
    let mut block_edit = pristine.clone();
    let digit = at + needle.len() - 1;
    block_edit[digit] = b'7';

    // ② an unrelated prose byte in the prefix.
    let prose = "逐名普查".as_bytes();
    let prose_at = find_bytes(&pristine, prose)
        .unwrap_or_else(|| panic!("{DR82_REPORT}: the prose under test must be present"));
    let mut prose_edit = pristine.clone();
    prose_edit[prose_at] = b'X';

    for (what, mutant) in [("a block edit", &block_edit), ("a prose edit", &prose_edit)] {
        assert_ne!(&pristine, mutant, "{what} must really change a byte");
        let violations = seal_violations(
            DR82_REPORT,
            DR82_DR84_SEAL,
            DR82_PRE_DR84_BYTES,
            DR82_PRE_DR84_SHA256,
            mutant,
        );
        assert!(
            !violations.is_empty(),
            "{what} inside the sealed prefix must trip the DR-82 seal (DR84A-1)"
        );
    }

    // The real report is read-only to this test: its bytes are unchanged.
    assert_eq!(
        sha256_hex(&pristine),
        sha256_hex(&read(DR82_REPORT)),
        "the real report must not be modified by this test"
    );
}

/// DR-86 ⑤: the round report whose facts an independent acceptance failed, and
/// whose correction may only be appended.
///
/// `TASK-SMOKE-T16-ACCEPTANCE.md` confirmed the round's product conclusion and
/// failed the report on factual discipline: it denied the quarantine directory
/// that exists, mis-stated the gate's first pass, published a wrong round-1 `A_1`
/// identity, and claimed three stray files were deleted before archiving.  The
/// correction (DR-86) is appended below this heading; everything above it — the
/// wrong sentences included — is sealed byte-for-byte, and the machine-readable
/// block is pinned in its own right.
const T16_REPORT: &str = ".spec/hof-rs/tasks/TASK-SMOKE-T16-REPORT.md";
/// The seal: the heading with the line terminator the append starts with, so the
/// pinned length is the reviewed revision's own length (77,319 B / `ee9d175d…`,
/// the `reviewed_report_sha256` of the acceptance).
const T16_DR86_SEAL: &str = "\n# 附：DR-86 追加式更正（2026-10-03）——独立验收指出的四处事实错误";
const T16_DR86_HEADING: &str = "# 附：DR-86 追加式更正（2026-10-03）——独立验收指出的四处事实错误";
const T16_PRE_DR86_BYTES: usize = 77_319;
const T16_PRE_DR86_SHA256: &str =
    "ee9d175da22f7cf18c31570e31c4dfd807f3afaed7ccc0faf634e0b31381c6f9";
/// The report's own ```json block, byte-identical to the round's
/// `machine_block_t16.json` (`06af46d5…`, 25,686 B).
const T16_BLOCK_BYTES: usize = 25_686;
const T16_BLOCK_SHA256: &str = "06af46d5dfb05cf3c867b1c52a3828fd48ef5a254e894134c202c485b210b0ad";

/// DR-86 ⑤: the correction is an append — the review revision is sealed, the
/// machine-readable block is untouched, and the correction states the four
/// readings that supersede the wrong ones.
#[test]
fn the_t16_report_keeps_its_review_revision_and_carries_the_dr86_correction() {
    let bytes = read(T16_REPORT);
    assert_no_violations(seal_violations(
        T16_REPORT,
        T16_DR86_SEAL,
        T16_PRE_DR86_BYTES,
        T16_PRE_DR86_SHA256,
        &bytes,
    ));
    assert_no_violations(block_violations(
        T16_REPORT,
        T16_BLOCK_BYTES,
        T16_BLOCK_SHA256,
        &bytes,
    ));
    let offset = whole_line_offset(&bytes, T16_DR86_SEAL).unwrap_or_else(|problem| {
        panic!("{T16_REPORT}: the DR-86 correction heading must own a whole line: {problem}")
    });
    assert_eq!(
        whole_line_offset(&bytes, T16_DR86_HEADING),
        Ok(T16_PRE_DR86_BYTES + 1),
        "the heading's own `#` must sit one byte past the sealed revision"
    );

    let text = String::from_utf8_lossy(&bytes);
    let correction = &text[offset..];
    for required in [
        // ① the quarantine directory the report denied.
        "deterministic-pass-1.stale-1790975400",
        // ② the first pass's real window.
        "project_defects_new=0",
        "editor_infrastructure_failures=5",
        // ③ the round-1 artifact identity the report got wrong.
        "11 文件 / 7646 B",
        // ④ the archive contradicts the deletion claim.
        "No deletion happens here",
        // the seal the correction itself publishes.
        "ee9d175d",
    ] {
        assert!(
            correction.contains(required),
            "{T16_REPORT}: the appended correction must carry `{required}`"
        );
    }
    // The wrong statements are still readable above the correction: this is an
    // append, not a rewrite, and the seal above is what proves it.
    for wrong in ["quarantine/ 不存在", "533c417d"] {
        assert!(
            text[..offset].contains(wrong),
            "{T16_REPORT}: the superseded statement `{wrong}` must survive above the correction"
        );
    }
    assert!(
        correction.contains("quarantine/ 不存在"),
        "{T16_REPORT}: the correction must quote the statement it corrects"
    );
}

/// Non-vacuity: the DR-86 seal reddens on an edit above it and on a block edit,
/// on **in-memory copies** — the real report is never written by this test.
#[test]
fn the_t16_seal_reddens_on_an_edit_above_it() {
    let pristine = read(T16_REPORT);
    assert!(
        seal_violations(
            T16_REPORT,
            T16_DR86_SEAL,
            T16_PRE_DR86_BYTES,
            T16_PRE_DR86_SHA256,
            &pristine
        )
        .is_empty(),
        "the guard must accept the pristine report before it is asked to reject a mutant"
    );

    // An in-place edit of one prose byte inside the sealed prefix.
    let needle = "quarantine".as_bytes();
    let at = find_bytes(&pristine, needle).expect("the report discusses the quarantine directory");
    let mut mutant = pristine.clone();
    mutant[at] = b'X';
    assert!(
        !seal_violations(
            T16_REPORT,
            T16_DR86_SEAL,
            T16_PRE_DR86_BYTES,
            T16_PRE_DR86_SHA256,
            &mutant
        )
        .is_empty(),
        "an edit above the correction must trip the seal"
    );

    // Appending after the heading stays permitted: the seal is a prefix.
    let mut appended = pristine.clone();
    appended.extend_from_slice(b"\nmore correction\n");
    assert!(
        seal_violations(
            T16_REPORT,
            T16_DR86_SEAL,
            T16_PRE_DR86_BYTES,
            T16_PRE_DR86_SHA256,
            &appended
        )
        .is_empty(),
        "appending inside the correction region must stay permitted"
    );

    assert_eq!(
        sha256_hex(&pristine),
        sha256_hex(&read(T16_REPORT)),
        "the real report must not be modified by this test"
    );
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

/// DR-90 ⑥: the DR-88 report's false clause must survive **only as a labelled
/// quotation** — the correction-discipline decision, made mechanical.
///
/// DR-89 corrected `TASK-DR88-REPORT.md` **in place** (one line, `+1/-1`) although
/// D289's discipline for a historical report is append-only, and the DR-89
/// acceptance recorded that as `DR89A-3`.  DR-90's decision (in
/// `TASK-DR90-REPORT.md`) is that the in-place form is the **better** state here
/// rather than a violation to be reverted, because DR-89's own accepted criterion
/// `C7` requires that *no file still asserts* the clause: restoring the original
/// line — the append-only form — would put a live false assertion back into a
/// repository file.  D289's purpose is met instead: no claim vanished silently
/// (the clause survives verbatim as a quotation), the wrong text stays readable,
/// and the reader is told which reading is wrong.
///
/// This test is the pin for that decision.  It does not freeze the file — an
/// append or a further labelled quotation is permitted — it freezes the
/// **property**: every line that carries the clause must carry the label that
/// marks it false, the clause must be present (so deleting the quotation cannot
/// satisfy the guard vacuously), and the DR-89 correction must name itself.
const DR88_REPORT: &str = ".spec/hof-rs/tasks/TASK-DR88-REPORT.md";
/// The clause whose truth DR-88 asserted and DR-89 disproved (the round of
/// record's five `\$` residues are unquoted code, not string content).
const DR88_FALSE_CLAUSE: &str = "T16 那一轮的 `\\$` 残渣正落在字符串里";
/// The labels that mark that clause false, on the same line.
const DR88_FALSE_LABELS: [&str; 3] = ["不成立", "已由 DR-89 更正", "**假**"];
/// The sentence that must remain, so the guard is not satisfied by deleting the
/// quotation together with its label.
const DR88_CORRECTION_SENTENCE: &str = "**本报告原先在此处写的证据是假的：**";

/// The 1-based lines that carry the false clause **without** a label that marks it
/// false on the same line.  An empty result is the property under test.
fn unlabelled_false_clause_lines(bytes: &[u8]) -> Vec<usize> {
    let text = String::from_utf8_lossy(bytes);
    let mut found = Vec::new();
    for (index, line) in text.split('\n').enumerate() {
        if line.contains(DR88_FALSE_CLAUSE)
            && !DR88_FALSE_LABELS.iter().any(|label| line.contains(label))
        {
            found.push(index + 1);
        }
    }
    found
}

/// DR-90 ⑥: the pin.  Every occurrence of the clause is labelled false, the
/// quotation and the sentence that labels it are still present, and the check is
/// shown to be load-bearing on an **in-memory** copy — the real report is never
/// written by this test.
#[test]
fn the_dr88_false_clause_survives_only_as_a_labelled_quotation() {
    let bytes = read(DR88_REPORT);
    let text = String::from_utf8_lossy(&bytes);

    // ① the clause is still readable — the correction is a correction, not a
    //    deletion of the record.
    assert!(
        text.contains(DR88_FALSE_CLAUSE),
        "{DR88_REPORT}: the false clause must survive as the quotation the correction is about"
    );
    // ② ... and it is labelled false, with the sentence that says so.
    assert!(
        text.contains(DR88_CORRECTION_SENTENCE),
        "{DR88_REPORT}: the quotation must carry the sentence that marks it false"
    );
    for label in ["不成立", "已由 DR-89 更正", "DR88A-1"] {
        assert!(
            text.contains(label),
            "{DR88_REPORT}: the correction must carry `{label}`"
        );
    }
    // ③ the property: no line asserts the clause unlabelled.
    let violations = unlabelled_false_clause_lines(&bytes);
    assert!(
        violations.is_empty(),
        "{DR88_REPORT}: line(s) {violations:?} assert the false clause without marking it false; the \
         in-place correction is only acceptable while the clause survives **as a labelled \
         quotation** (DR89A-3 / D289)"
    );

    // ④ non-vacuity, on an in-memory copy: strip the labels from the clause's own
    //    line — which is what restoring the original 52d73d3 wording does — and the
    //    predicate must find it.  No historical bytes are needed for that: the
    //    property under test is "labelled", so removing the label is the mutant.
    let mut stripped = String::new();
    let mut changed = false;
    for (index, line) in text.split('\n').enumerate() {
        let _ = index;
        if !stripped.is_empty() {
            stripped.push('\n');
        }
        if line.contains(DR88_FALSE_CLAUSE) {
            let mut bare = line.to_string();
            for label in DR88_FALSE_LABELS {
                bare = bare.replace(label, "");
            }
            if bare != line {
                changed = true;
            }
            stripped.push_str(&bare);
        } else {
            stripped.push_str(line);
        }
    }
    assert!(
        changed,
        "{DR88_REPORT}: the clause's line must actually carry a label for the mutant to mean anything"
    );
    let mutant = unlabelled_false_clause_lines(stripped.as_bytes());
    assert!(
        !mutant.is_empty(),
        "the guard is vacuous: stripping the label from the clause's own line must be reported \
         (that line is exactly what the append-only form would put back)"
    );

    // ⑤ the real report is read-only to this test.
    assert_eq!(
        sha256_hex(&bytes),
        sha256_hex(&read(DR88_REPORT)),
        "the real report must not be modified by this test"
    );
}
