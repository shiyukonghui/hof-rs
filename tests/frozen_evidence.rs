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
    let path =
        repo_root().join(".spec/hof-rs/tasks/TASK-SMOKE-T9-evidence/experiment/dev1_commands.txt");
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
    let records = bytes
        .split(|byte| *byte == b'\n')
        .filter(|l| !l.is_empty())
        .count();
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
    // is `$(cat /c/Users/<user>/AppD` with no closing paren and no closing quote, and
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

// ---------------------------------------------------------------------------
// DR-72 ②: a redaction pass must not rewrite frozen evidence in place
// ---------------------------------------------------------------------------

/// DR-72 ②: the frozen, read-by-the-round rule, asserted directly.
///
/// D276: "in-place rewriting of evidence has damaged three rounds" — DR-69 moved
/// a record boundary, DR-70 published a wrong byte count, and this batch's own
/// round left `runs/smoke-t10/iter-1/traj/tester.attempt1.json` unparseable.  The
/// decision is therefore: a frozen file is **never** rewritten; when something in
/// it must be redacted, the redacted form is generated as a copy next to it
/// (`<name>.redacted.<ext>`) and the original keeps every byte.
///
/// The areas used here are the run-directory layout the runtime produces, plus
/// `planner-view` (which a caller may seal; the runtime does **not**, because
/// DR-19 requires a role's own dump to be erased in place — see
/// `run_loop::frozen_evidence_roots`).  The mechanism is the same either way, and
/// the assertion is about the mechanism.
#[test]
fn a_redaction_pass_leaves_frozen_evidence_byte_identical() {
    use hof_rs::runtime::secrets::{
        redact_tree_traced, redacted_copy_path, scrub_is_clean, SealedAreas,
    };

    let temp = tempfile::tempdir().expect("tempdir");
    let run_dir = temp.path().join("runs/run-1");
    // The five frozen areas, exactly as the runtime lays them out.  The files are
    // valid JSON documents with an escaped newline (the DR-72 ① shape) and a
    // harness value whose path carries a user name (dispatcher addition 1).
    let frozen_paths = [
        "versions/aaaa/env.json",
        "iter-1/planner-view/env.json",
        "iter-1/candidate/.hoh/evidence.json",
        "iter-1/traj/tester.attempt1.json",
        "quarantine/.hoh.stale-1/deterministic/raw/x.json",
    ];
    // A stand-in credential and a harness value: both are things a pass exists to
    // remove, so the test proves the *mechanism* rather than "nothing matched".
    let secret = "test-key-not-a-secret";
    let frozen_text = format!(
        "{{\"dump\": \"HOH_MODEL_API_KEY={secret}\\nHOH_ARTIFACT_DIR=F:\\\\stand-in\\\\runs\\\\run-1\"}}\n"
    );
    serde_json::from_str::<serde_json::Value>(&frozen_text).expect(
        "the frozen fixture must be valid JSON, so the pass is not refused for the wrong reason",
    );
    for relative in frozen_paths {
        let path = run_dir.join(relative);
        std::fs::create_dir_all(path.parent().unwrap()).expect("frozen parent");
        std::fs::write(&path, &frozen_text).expect("frozen file");
    }
    // One live file, outside every frozen area: this one may be rewritten.
    let live = run_dir.join("warnings.log");
    std::fs::write(&live, format!("leaked {secret}\n")).expect("live file");

    let sealed = SealedAreas::new(
        ["versions", "quarantine"]
            .iter()
            .map(|name| run_dir.join(name))
            .chain(
                ["planner-view", "candidate", "traj"]
                    .iter()
                    .map(|name| run_dir.join("iter-1").join(name)),
            ),
    );

    let report = redact_tree_traced(&run_dir, &[secret.to_string()], &sealed).expect("sweep");

    for relative in frozen_paths {
        let path = run_dir.join(relative);
        assert_eq!(
            std::fs::read_to_string(&path).expect("frozen file still readable"),
            frozen_text,
            "{relative} is frozen evidence and must be byte-identical after the pass"
        );
        let copy = redacted_copy_path(&path);
        assert!(
            copy.is_file(),
            "{relative} carried a secret, so a generated copy must exist at {copy:?}"
        );
        let copied = std::fs::read_to_string(&copy).expect("copy readable");
        assert!(
            scrub_is_clean(&copied, &[secret.to_string()]),
            "the generated copy must actually be clean: {copied}"
        );
        assert!(
            !copied.contains("F:\\\\stand-in") && !copied.contains(secret),
            "the copy must not carry the credential or the harness value: {copied}"
        );
        assert!(
            report.copies.contains(&copy),
            "the pass must report the generated copy: {report:?}"
        );
        assert!(
            !report.rewritten.contains(&path),
            "a frozen file must never appear in `rewritten`: {report:?}"
        );
    }
    // Non-vacuity: the pass really did remove something, and a live file is still
    // eligible for an in-place rewrite.
    assert_eq!(
        report.hits(),
        frozen_paths.len() as u64 + 1,
        "five frozen copies plus one live rewrite: {report:?}"
    );
    assert!(
        report.rewritten.contains(&live),
        "the live file is not frozen and must be rewritten in place: {report:?}"
    );
    let live_text = std::fs::read_to_string(&live).expect("live readable");
    assert!(
        !live_text.contains(secret),
        "the live rewrite must remove the credential: {live_text}"
    );
}

// ---------------------------------------------------------------------------
// DR-72 (dispatcher addition 1): the controlled evidence must carry no
// environment **values**, not merely no credential values
// ---------------------------------------------------------------------------

/// The files under `.spec/hof-rs/tasks/*-evidence/**` are analysis products a
/// human reviews.  The SMOKE-T10 round's report claimed the controlled directory
/// held no environment dump; an independent verifier found `HOH_ARTIFACT_DIR`,
/// `HOH_HOH_BIN` and a `PATH` tail containing a user name in
/// `TASK-SMOKE-T10-evidence/analysis/redaction_defect.txt`.
///
/// **Honest caveat, encoded here:** the thing that leaked is a *path containing a
/// user name*, so a credential-shaped scan would have missed it.  This test
/// enforces the stronger rule for every file this batch generated; the one
/// already-committed SMOKE-T10 analysis product is reported as a **live finding**
/// by `TASK-DR72-REPORT.md` rather than silently rewritten, because its bytes are
/// the frozen evidence of the very defect it documents.
#[test]
fn the_batch_evidence_products_carry_no_environment_values() {
    let root = repo_root().join(".spec/hof-rs/tasks");
    assert!(root.is_dir(), "the controlled evidence root must exist");

    // The exact disclosure the verifier found.  A **path carrying a user name**
    // is the one the round missed, so it is checked separately and applies to
    // every product; the `HOH_*=` form is checked on the generated (JSON/report)
    // products, because the *input* sample has to spell the assignment out for
    // the redaction under test to have something to remove.
    let user_path_needles = ["C:\\Users\\", "C:\\\\Users\\\\"];
    let environment_needles = [
        "HOH_ARTIFACT_DIR=",
        "HOH_HOH_BIN=",
        "HOH_GAME_ROUTE=",
        "HOH_SCRATCH_DIR=",
    ];

    let mut products = 0usize;
    let mut user_paths: Vec<String> = Vec::new();
    let mut environment_values: Vec<String> = Vec::new();
    collect_evidence_files(
        &root,
        &root,
        &mut products,
        &mut user_paths,
        &user_path_needles,
    );
    collect_evidence_files(
        &root,
        &root,
        &mut products,
        &mut environment_values,
        &environment_needles,
    );
    assert!(
        products > 0,
        "the test must actually look at evidence products; it found none under {root:?}"
    );
    assert!(
        user_paths.is_empty(),
        "a DR-72 product carries a path with a user name — this is the disclosure the credential \
         scan missed (dispatcher addition 1): {user_paths:?}"
    );
    // The generated products must not carry an environment assignment either.
    // One directory is exempt **and the exemption is stated in its own README**:
    // `samples/` is the redaction sample, so by construction it shows the
    // assignment before the pass and the replacement after it.  Its values are
    // synthetic stand-ins.
    let generated: Vec<String> = environment_values
        .into_iter()
        .filter(|relative| !relative.contains("samples/"))
        .collect();
    assert!(
        generated.is_empty(),
        "a generated DR-72 product carries an environment value (dispatcher addition 1): {generated:?}"
    );
}

/// Regenerate `samples/env.redacted.txt` with the **production** pass, so the
/// committed sample is an artifact rather than a hand edit.
///
/// It is a test because it needs the production code, but it is not part of the
/// suite's verdict: the gate's `ignored` count must not grow (`TASK-DR72.md` §3),
/// so it runs only when the sample is deliberately regenerated:
///
/// ```text
/// cargo test --offline --test frozen_evidence -- --exact \
///     the_redacted_sample_is_regenerable_from_the_production_pass
/// ```
#[test]
fn the_redacted_sample_is_regenerable_from_the_production_pass() {
    let root = repo_root().join(".spec/hof-rs/tasks/TASK-DR72-evidence/samples");
    let input = std::fs::read_to_string(root.join("env.original.txt")).expect("sample input");
    let report =
        hof_rs::runtime::secrets::scrub_text(&input, &["test-key-not-a-secret".to_string()]);
    assert!(
        report.changed(),
        "the sample must demonstrate a redaction: {report:?}"
    );
    assert!(report.refused.is_none(), "{:?}", report.refused);
    assert_eq!(
        hof_rs::runtime::secrets::bytes_changed_outside_spans(&report),
        Some(0),
        "the sample must be a pure splice"
    );
    serde_json::from_str::<serde_json::Value>(&report.redacted)
        .expect("the redacted sample must still be valid JSON");

    // Publish what this run produced into the crate's own `target/` (never into
    // the tracked evidence), so a mismatch is one `cp` away from being fixed
    // without hand-editing an escape.
    let out = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("target/dr72-redaction-sample");
    std::fs::create_dir_all(&out).expect("out dir");
    std::fs::write(out.join("env.redacted.txt"), &report.redacted).expect("write redacted");
    let spans = report
        .spans
        .iter()
        .map(|span| {
            format!(
                "{} [{}..{}) -> {}",
                span.name, span.start, span.end, span.replacement
            )
        })
        .collect::<Vec<_>>()
        .join("\n");
    std::fs::write(out.join("env.spans.txt"), &spans).expect("write spans");

    let committed = std::fs::read_to_string(root.join("env.redacted.txt")).expect("sample output");
    assert_eq!(
        committed,
        report.redacted,
        "the committed sample must be exactly what the production pass produces; copy {} over it \
         (or report the difference) — see the batch report's disclosure section",
        out.join("env.redacted.txt").display()
    );
    let committed_spans = std::fs::read_to_string(root.join("env.spans.txt")).expect("span report");
    assert_eq!(
        committed_spans,
        spans,
        "the committed span report must match the pass exactly; copy {} over it",
        out.join("env.spans.txt").display()
    );
}

/// Walk `root` for **this batch's** evidence products and flag any that carry an
/// environment value.
///
/// The relative path is taken against the **top** (`base`), not against the
/// directory currently being read, so the scope test below can see
/// `TASK-DR72-evidence/README.md` rather than just `README.md`.
fn collect_evidence_files(
    base: &std::path::Path,
    directory: &std::path::Path,
    products: &mut usize,
    offenders: &mut Vec<String>,
    needles: &[&str],
) {
    let Ok(entries) = std::fs::read_dir(directory) else {
        return;
    };
    for entry in entries.filter_map(Result::ok) {
        let path = entry.path();
        if path.is_dir() {
            collect_evidence_files(base, &path, products, offenders, needles);
            continue;
        }
        let relative = path
            .strip_prefix(base)
            .unwrap_or(&path)
            .to_string_lossy()
            .replace('\\', "/");
        // In scope: a **controlled evidence directory** of this batch.
        if !relative.contains("DR72-evidence") {
            continue;
        }
        // Out of scope, on purpose: nothing else.  The smoke-t10 analysis
        // product that documents the original defect lives under a different
        // directory, and is reported (never rewritten) by the batch report.
        *products += 1;
        let Ok(text) = std::fs::read_to_string(&path) else {
            continue;
        };
        if needles.iter().any(|needle| text.contains(needle)) {
            offenders.push(relative);
        }
    }
}
