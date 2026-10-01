//! DR-77 — the three clearances the DR-76 acceptance asked for **before** a real
//! round, because all three are about *what the evidence will be read to mean*:
//!
//! ① `TASK-DR73-REPORT.md` §12 row 8 quoted `4deefc8`'s commit message with a
//!    sentence the commit message does not contain ("…no ground past x≈3800…").
//!    The claim being refuted is real and still inside the commit message ("the
//!    goal sat at x=6400 past the end of the traversable ground"), so the ledger
//!    has to quote the real bytes and keep the wrong quotation marked as wrong.
//! ② `coverage_shortfall_px` was written onto both verdict lines, but the tests
//!    only asserted a substring the **drive** line alone could satisfy, so the
//!    field could be deleted from the verdict line with no red.  The value is now
//!    pinned to the verdict line itself, as the last field of that line.
//! ③ `WIN_UNREACHABLE_GEOMETRICALLY` promised a geometric proof while the
//!    evidence is "holding `move_right` did not advance the player with budget
//!    unspent" — nothing about a jump, because the window never jumps.  The
//!    delivered token is renamed to say only what was measured, and the
//!    limitation is stated where the token appears.
//!
//! The two observations under test are frozen in `tests/fixtures/dr77/` — the
//! DR-76 fixture channel's own output for the two non-winning levels, captured
//! before this batch touched the token.  `tests/evidence_battery.rs` re-runs those
//! levels and compares the live record against those bytes, so the fixture cannot
//! drift away from what the window really writes.

use std::path::PathBuf;
use std::process::Command;

const LEDGER: &str = ".spec/hof-rs/tasks/TASK-DR73-REPORT.md";
const SKILL: &str = "src/prompts/skills/godot-dev.md";
const BLOCKED_FIXTURE: &str = "tests/fixtures/dr77/blocked_observation.txt";
const COVERAGE_FIXTURE: &str = "tests/fixtures/dr77/coverage_observation.txt";

/// The commit whose message carries the false geometric claim.
const FALSE_CLAIM_COMMIT: &str = "4deefc8";
/// The renamed verdict: a drive that stopped advancing with budget left.
const BLOCKED_VERDICT: &str = "WIN_BLOCKED_UNDER_MOVE_RIGHT";
/// The name DR-76 shipped, which promised a proof the window cannot make.
const SUPERSEDED_TOKEN: &str = "WIN_UNREACHABLE_GEOMETRICALLY";
/// The true sentence from the commit, at the commit message's own line breaks:
/// pinning it here is what makes a joined or paraphrased quotation red.
const TRUE_QUOTE_LINES: [&str; 4] = [
    "Diagnosis (layer A): the produced project never delivered a collected coin or a",
    "reachable win, and nothing in the round asked whether it had.  move_right swept",
    "both coins in smoke-t10 while the HUD stayed at Coins: 0, and the goal sat at",
    "x=6400 past the end of the traversable ground.  The tool contract already could",
];
/// The old, fabricated quotation, which has to stay in the record marked wrong.
const WRONG_QUOTE_MARKER: &str = "no ground past x≈3800";

const QUOTE_BEGIN: &str = "<!-- DR-77-COMMIT-QUOTE-BEGIN -->";
const QUOTE_END: &str = "<!-- DR-77-COMMIT-QUOTE-END -->";
const INCORRECT_BEGIN: &str = "<!-- DR-77-INCORRECT-QUOTE-BEGIN -->";
const INCORRECT_END: &str = "<!-- DR-77-INCORRECT-QUOTE-END -->";

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
}

fn read(relative: &str) -> String {
    let path = repo_root().join(relative);
    std::fs::read_to_string(&path)
        .unwrap_or_else(|error| panic!("`{}` must be readable: {error}", path.display()))
}

/// A frozen observation with its line endings normalised: the fixture is LF, and
/// this check does not depend on which ending the checkout gave it.
fn read_observation(relative: &str) -> String {
    read(relative).replace("\r\n", "\n").trim().to_string()
}

/// The commit message exactly as `git show --format=%B -s <rev>` prints it.
///
/// `%B` is the raw body: no re-wrapping, no re-indentation, and the message's own
/// hard line breaks are preserved — which is the point, because a quotation that
/// silently re-flows the sentence is not a quotation of these bytes.
fn commit_message(rev: &str) -> String {
    let output = Command::new("git")
        .arg("-C")
        .arg(repo_root())
        .arg("show")
        .arg("--format=%B")
        .arg("-s")
        .arg(rev)
        .output()
        .unwrap_or_else(|error| {
            panic!(
                "`git show --format=%B -s {rev}` must be runnable so the ledger's quotation can \
                 be checked against the commit: {error}"
            )
        });
    assert!(
        output.status.success(),
        "`git show --format=%B -s {rev}` failed, so the quoted commit message cannot be \
         verified: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    String::from_utf8(output.stdout).expect("the commit message is UTF-8")
}

fn between(text: &str, begin: &str, end: &str) -> String {
    let rest = text
        .split_once(begin)
        .unwrap_or_else(|| panic!("the ledger must carry the `{begin}` marker"))
        .1;
    rest.split_once(end)
        .unwrap_or_else(|| panic!("the ledger must carry the `{end}` marker"))
        .0
        .to_string()
}

/// The message with the renderer's line continuations folded away, so a claim about
/// the message's own wording is not a claim about Rust's string-literal indentation.
fn collapsed(text: &str) -> String {
    text.replace("\n", " ")
        .split_whitespace()
        .collect::<Vec<_>>()
        .join(" ")
}

/// The one line of an observation that carries `token` — the verdict line, which
/// is what the assertions have to pin (the drive line carries the values too).
fn verdict_line<'a>(observation: &'a str, token: &str) -> &'a str {
    observation
        .split("; ")
        .find(|part| collapsed(part).contains(token))
        .unwrap_or_else(|| {
            panic!("the recorded observation must carry the `{token}` line:\n{observation}")
        })
}

/// ① The ledger quotes the commit message **verbatim**: every line the ledger
/// claims to quote must be a line of `git show --format=%B -s 4deefc8` after
/// trimming the blockquote marker — and the old, wrong quotation must stay in the
/// record marked as incorrect rather than being quietly replaced.
#[test]
fn the_ledger_quotes_the_false_claim_commit_verbatim() {
    let ledger = read(LEDGER).replace("\r\n", "\n");
    let message = commit_message(FALSE_CLAIM_COMMIT).replace("\r\n", "\n");

    let claimed = between(&ledger, QUOTE_BEGIN, QUOTE_END);
    assert!(
        !claimed.trim().is_empty(),
        "the ledger must quote the commit message between `{QUOTE_BEGIN}` and `{QUOTE_END}`"
    );

    // Pin the true sentence in the test as well, so a ledger that "fixes" the
    // quotation by quoting some *other* real sentence is red too.
    for line in TRUE_QUOTE_LINES {
        assert!(
            message.lines().any(|actual| actual.trim() == line),
            "the fixture's expectation has come apart from the commit itself; `{line}` is not a \
             line of `git show --format=%B -s {FALSE_CLAIM_COMMIT}`:\n--- message ---\n{message}"
        );
    }

    let mut quoted_lines = 0usize;
    for quoted in claimed.lines() {
        let stripped = quoted.trim().trim_start_matches('>').trim();
        // A fenced code block around the quotation is formatting, not content.
        if stripped.is_empty() || stripped.starts_with("```") {
            continue;
        }
        quoted_lines += 1;
        assert!(
            message.lines().any(|actual| actual.trim() == stripped),
            "the ledger's quotation of `{FALSE_CLAIM_COMMIT}` is not verbatim: the line\n  \
             {stripped:?}\ndoes not occur in the commit message.  A reader has to be able to check \
             the retraction against the commit itself.\n--- message ---\n{message}"
        );
    }
    assert!(
        quoted_lines >= TRUE_QUOTE_LINES.len(),
        "the quotation carries {quoted_lines} line(s); the diagnostic sentence it is meant to \
         preserve spans {} lines of the commit message",
        TRUE_QUOTE_LINES.len()
    );

    let incorrect = between(&ledger, INCORRECT_BEGIN, INCORRECT_END);
    let incorrect_lower = incorrect.to_lowercase();
    assert!(
        incorrect.contains(WRONG_QUOTE_MARKER),
        "the wrong quotation must stay in the record (not be silently replaced) so the correction \
         is auditable:\n{incorrect}"
    );
    assert!(
        incorrect_lower.contains("incorrect") && incorrect_lower.contains("superseded"),
        "the wrong quotation must be marked incorrect and superseded:\n{incorrect}"
    );
    assert!(
        !incorrect.contains(TRUE_QUOTE_LINES[3]),
        "the block marked incorrect must hold the *wrong* quotation, not the true sentence: \
         the wrong quotation is what makes the correction auditable:\n{incorrect}"
    );
    assert!(
        !message
            .lines()
            .any(|actual| actual.trim() == WRONG_QUOTE_MARKER),
        "the fixture's expectation has come apart from the commit: `{WRONG_QUOTE_MARKER}` is not \
         a line of `git show --format=%B -s {FALSE_CLAIM_COMMIT}`, so this test would be checking \
         the wrong thing:\n--- message ---\n{message}"
    );
    // …and the record must still say the claim it refutes is real.
    assert!(
        ledger.contains("past the end of the traversable ground"),
        "the correction must state the false claim the commit message really makes"
    );
}

/// ② The shortfall is pinned **on the blocked verdict line**: the last field of
/// that line is the concrete number, so deleting the field from the verdict line
/// reddens this test even while the drive line still carries it.
#[test]
fn the_blocked_verdict_line_carries_its_own_shortfall() {
    let observation = read_observation(BLOCKED_FIXTURE);
    let verdict = verdict_line(&observation, BLOCKED_VERDICT);
    assert!(
        !verdict.contains("drove `"),
        "the pinned line must be the verdict, not the drive line:\n{verdict}"
    );
    let expected = "coverage_shortfall_px=Some(5240.0)";
    let pinned = collapsed(&observation);
    assert!(
        pinned.contains(BLOCKED_VERDICT),
        "the observation must carry a `{BLOCKED_VERDICT}` line, not only the drive line:\n\
         {observation}"
    );
    // The drive line renders `player max x=..., coverage_shortfall_px=...` too, so the
    // pin starts at wording only the verdict line carries (`still unspent; `).
    let needle = "still unspent; player max x=Some(1160.0), goal.position=Some(Object {\"x\": Number(6400.0), \
                 \"y\": Number(280.0)}), ";
    let tail = needle.replace("\n", " ") + expected;
    assert!(
        pinned.contains(&tail),
        "the `{BLOCKED_VERDICT}` line itself must carry `{expected}` as its own concrete value: a \
         `contains` over the whole observation is also satisfied by the drive line:\n{observation}"
    );
    assert_eq!(pinned, collapsed(&read_observation(BLOCKED_FIXTURE)));
}

/// ②b The coverage verdict is pinned the same way, with its own fixture value.
#[test]
fn the_coverage_verdict_line_carries_its_own_shortfall() {
    let observation = read_observation(COVERAGE_FIXTURE);
    let verdict = verdict_line(&observation, "WIN_UNREACHED_WITHIN_BUDGET");
    assert!(
        !verdict.contains("drove `"),
        "the pinned line must be the verdict, not the drive line:\n{verdict}"
    );
    let expected = "coverage_shortfall_px=Some(1340.0)";
    let pinned = collapsed(&observation);
    assert!(
        pinned.contains("WIN_UNREACHED_WITHIN_BUDGET"),
        "the observation must carry the coverage verdict line, not only the drive line:\n\
         {observation}"
    );
    // `stayed false; ` is the coverage verdict's own wording.
    // The renderer breaks the message across source lines; joining them gives exactly one
    // space per source newline, which is what the record contains (folding with
    // `split_whitespace` would eat the space inside `..., \"y\"`).
    let needle = "stayed false; player max x=Some(28660.0), goal.position=Some(Object {\"x\": Number(30000.0), \
                 \"y\": Number(280.0)}), ";
    let tail = needle.replace("\n", " ") + expected;
    assert!(
        pinned.contains(&tail),
        "the coverage verdict line itself must carry `{expected}` as its own concrete value:\n\
         {observation}"
    );
    assert_eq!(pinned, collapsed(&read_observation(COVERAGE_FIXTURE)));
}

/// ②c The blocked pin has to be false when the field is deleted **from the verdict
/// line**, even though the drive line still carries it.
///
/// Editing the frozen fixture to show this would be editing the evidence, so the
/// proof is a mutation of the string the pin reads: delete the shortfall from the
/// run that begins at the verdict's own token (the verdict line), leave the drive
/// line's copy alone, and require the pin's predicate to be false.
#[test]
fn the_blocked_pin_reddens_when_the_field_is_deleted_from_the_verdict_line() {
    let observation = read_observation(BLOCKED_FIXTURE);
    let pinned = collapsed(&observation);
    let expected = "coverage_shortfall_px=Some(5240.0)";
    let needle = "still unspent; player max x=Some(1160.0), goal.position=Some(Object {\"x\": \
                 Number(6400.0), \"y\": Number(280.0)}), ";
    let tail = needle.replace("\n", " ") + expected;
    assert!(
        pinned.contains(&tail),
        "the unmutated read must satisfy the pin"
    );

    let verdict_at = pinned
        .find(BLOCKED_VERDICT)
        .expect("the verdict line is in the read");
    let (before, after) = pinned.split_at(verdict_at);
    let mutant = before.to_string()
        + &after.replacen(expected, &expected.replace("Some(5240.0)", "None"), 1);
    // The drive line's own copy is still there: the mutation is verdict-local.
    assert_eq!(
        mutant.matches("coverage_shortfall_px=None").count(),
        1,
        "the mutant must differ from the read exactly on the verdict line"
    );
    assert!(
        !mutant.contains(&tail),
        "the pin must be false when the field is gone from the verdict line, even though the \
         drive line still carries it"
    );
}

/// ③ The token must not promise more than the window measured.
///
/// The delivered token is `WIN_BLOCKED_UNDER_MOVE_RIGHT` — blocked *under this
/// movement action*.  The window only ever holds `move_right`, so the limitation
/// (a jump, or any other input, is not ruled out) has to be stated where the
/// token is read, not only in a report's risk list.
#[test]
fn the_blocked_token_is_named_for_what_the_window_measured() {
    let skill = read(SKILL).replace("\r\n", "\n");

    assert!(
        skill.contains(BLOCKED_VERDICT),
        "the delivered skill must name the renamed verdict `{BLOCKED_VERDICT}`"
    );
    // The old name may stay only where it is *mapped* to the new one: it may
    // never be presented on its own as the live verdict again.
    for paragraph in skill.split("\n\n") {
        if !paragraph.contains(SUPERSEDED_TOKEN) {
            continue;
        }
        assert!(
            paragraph.contains(BLOCKED_VERDICT),
            "the old token `{SUPERSEDED_TOKEN}` may survive only inside a statement that maps it \
             to `{BLOCKED_VERDICT}`; this paragraph still presents it as a verdict of its own:\n\
             {paragraph}"
        );
    }
    // The paragraph that states the limit may not be the one that merely maps the
    // old name: this searches for the verdict **plus** the bounded reading.
    let scope = skill
        .split("\n\n")
        .find(|paragraph| {
            paragraph.contains(BLOCKED_VERDICT)
                && paragraph.to_lowercase().contains("move_right")
                && paragraph.to_lowercase().contains("jump")
        })
        .unwrap_or_else(|| {
            panic!(
                "the renamed token must stand next to its movement-direction limit in the \
                 delivered skill:\n{skill}"
            )
        });
    let scope_lower = scope.to_lowercase();
    assert!(
        scope_lower.contains("move_right") && scope_lower.contains("jump"),
        "the paragraph that carries `{BLOCKED_VERDICT}` must state the limit in the same breath: \
         it is about holding `move_right`, and it does not rule out a jump:\n{scope}"
    );
}

/// ③b The mapping from the old name has to survive, so earlier rounds' records
/// (which carry `WIN_UNREACHABLE_GEOMETRICALLY`) stay readable.
#[test]
fn the_old_token_keeps_a_mapping_to_the_renamed_one() {
    let ledger = read(LEDGER).replace("\r\n", "\n");
    let mapping = ledger
        .split("\n\n")
        // Mapping rows are table rows; prose that *discusses* the old name is not
        // a mapping, so it cannot satisfy this.
        .find(|paragraph| {
            paragraph.lines().any(|line| {
                line.trim_start().starts_with('|')
                    && line.contains(SUPERSEDED_TOKEN)
                    && line.contains(BLOCKED_VERDICT)
            })
        })
        .unwrap_or_else(|| {
            panic!(
                "the ledger must map the old token `{SUPERSEDED_TOKEN}` to `{BLOCKED_VERDICT}` in \
                 its §12 ledger table so historical records stay readable"
            )
        });
    assert!(
        mapping.contains(BLOCKED_VERDICT),
        "the mapping row must name the new token:\n{mapping}"
    );
}
