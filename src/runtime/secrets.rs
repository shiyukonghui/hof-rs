//! DR-19: the model secret must never reach a role subprocess, and anything
//! that leaks into `runs/<id>/**` is erased before it becomes an artifact.
//!
//! Root cause found by the first real smoke run: mini's `LocalEnvironment`
//! inherits the parent environment and only overrides the keys it is given, so
//! a role running `cmd /c set HOH` could echo the credential into its
//! trajectory and the model context.  Two defences are implemented here:
//!
//! 1. every role environment explicitly sets the known secret variables to the
//!    empty string, blocking the inheritance; and
//! 2. after every role call the run directory is scanned for the known secret
//!    values and rewritten with `<redacted>`.
//!
//! DR-72 ②: in-place rewriting is now the **exception**, not the rule.  D276
//! decided that "redact by rewriting the evidence in place" has damaged three
//! rounds (DR-69 merged a record and changed line endings, DR-70 published a
//! wrong byte count, this batch's own round left a trajectory unparseable).  The
//! policy is therefore explicit: a path inside a **frozen** area (see
//! [`SealedAreas`]) is never rewritten — its redacted form is produced as a
//! generated copy next to it, and the original keeps every byte.  Only the
//! live, role-produced scratch that no consumer parses is rewritten in place,
//! and even there the assignment splice refuses to write a file whose JSON no
//! longer parses.
//!
//! DR-72 ①: the assignment scan used to locate the end of an unquoted value
//! with `find([';', '\n', '\r'])`.  Rust's `'\n'` is a **physical** newline,
//! while a JSON string's newline is the two characters `\` + `n`; the scan
//! therefore ran past an escape that was still inside the string, and the
//! replacement deleted the rest of the string, its closing quote and the
//! comma.  That is exactly how `runs/smoke-t10/iter-1/traj/tester.attempt1.json`
//! became invalid JSON at char 412862.  The scan is now **escape-aware**,
//! records the exact byte spans it replaced, and a JSON splice is only applied
//! when the result still parses.
//!
//! DR-74 ①③: the DR-72 predicate was still wrong in the shape the real
//! trajectories actually use.  Every Windows path there is written with
//! **doubled** backslashes, so `…\\runs…` made the predicate fire on the second
//! byte of the pair: it deleted one backslash, the surviving `\r` decoded to a
//! carriage return, and the rest of the path stayed visible.  An escape now
//! starts only at a backslash preceded by an **even** run, escape awareness is
//! limited to JSON, and every real escape family (`\t`, `\uXXXX`, `\"`, …) ends
//! the value rather than running it to the physical line end (where the splice
//! would be refused and the assignment rule silently dropped).

use std::collections::BTreeMap;
use std::path::{Path, PathBuf};

use walkdir::WalkDir;

use crate::config::{HohConfig, REDACTED};

/// Every environment variable that may carry the model credential.
pub const SECRET_ENV_VARS: &[&str] = &[
    "HOH_MODEL_API_KEY",
    "OPENAI_API_KEY",
    "LITELLM_API_KEY",
    "MSWEA_MODEL_API_KEY",
];

/// DR-72 (dispatcher addition 1): the **harness** variables whose *values* are
/// environment disclosure even though they carry no credential.
///
/// A round's report claimed that its controlled evidence directory held no
/// environment dump, while an analysis product still carried
/// `HOH_ARTIFACT_DIR=…`, `HOH_HOH_BIN=…` and a `PATH` tail containing a user
/// name.  No key value ever leaked, so this is a disclosure-accuracy rule, not
/// a credential rule — and it deliberately catches a **path containing a user
/// name**, not only credential-shaped values.
///
/// `PATH`/`Path` are here because the user name that actually leaked travelled
/// in a `PATH` tail.  Both spellings are covered, because `cmd` prints `Path`
/// while a POSIX shell prints `PATH`; nothing else uses either spelling as an
/// assignment in a project file.
///
/// DR-79 ④: `DSH_TERM_CMD` is the **harness's own command line**.  `smoke-t13`'s
/// role shells inherited it, `env | grep -i hoh` matched it (it names the harness
/// and the staging directory) and the line was frozen into
/// `planner.attempt1.json`, `developer.attempt1.json` and their redacted
/// sidecars, naming `config/model.secret.env` along the way.  It carries no
/// credential, but it records where the credential lives, which is the same
/// disclosure class as the `HOH_*` family above and deliberately read by the
/// DR-69 rule.  Its value is a whole command line, so it is terminated by
/// [`COMMAND_LINE_VARS`] rather than by the generic path rule.
pub const HARNESS_ENV_VARS: &[&str] = &[
    "HOH_ARTIFACT_DIR",
    "HOH_GAME_ROUTE",
    "HOH_HOH_BIN",
    "HOH_ITERATION",
    "HOH_ROLE",
    "HOH_RUN_DIR",
    "HOH_RUN_ID",
    "HOH_SCRATCH_DIR",
    "HOH_TOOLS_ENDPOINT",
    "HOH_VIEW_DIR",
    "HOH_SECRET_PATH",
    "DSH_TERM_CMD",
    "PATH",
    "Path",
];

/// The overrides that must be present in *every* role environment so a child
/// shell cannot inherit a live credential.
pub fn blocked_env() -> BTreeMap<String, String> {
    SECRET_ENV_VARS
        .iter()
        .map(|name| (name.to_string(), String::new()))
        .collect()
}

/// The secret values this process knows about: the resolved configuration key
/// plus any value currently present in a known variable.
///
/// Values shorter than 6 characters are ignored: redacting them would corrupt
/// unrelated text without any security benefit.
pub fn known_secrets(cfg: &HohConfig) -> Vec<String> {
    let mut secrets: Vec<String> = Vec::new();
    if let Some(resolved) = cfg.resolved_api_key() {
        secrets.push(resolved);
    }
    for name in SECRET_ENV_VARS {
        if let Ok(value) = std::env::var(name) {
            secrets.push(value.trim().to_string());
        }
    }
    secrets.retain(|value| value.chars().count() >= 6);
    secrets.sort();
    secrets.dedup();
    secrets
}

/// DR-72 ①: one replaced byte span, recorded in the **input** coordinate space.
///
/// The span is what makes the invariant auditable: every byte of the input
/// outside `[start, end)` must appear unchanged in the output, and the output
/// must be exactly the input with those spans replaced.  A caller can therefore
/// reconstruct the output from the input and the spans, byte for byte.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct RedactionSpan {
    /// The variable whose assignment (or value) was replaced.
    pub name: String,
    /// First replaced byte in the input.
    pub start: usize,
    /// One past the last replaced byte in the input.
    pub end: usize,
    /// The text that took the span's place.
    pub replacement: String,
}

/// One redaction pass over a piece of text: the original, the generated result
/// and the spans that connect them.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct RedactionReport {
    /// The exact text that was read.
    pub original: String,
    /// The text after the scan ran.
    pub redacted: String,
    /// The replaced spans, in ascending order and non-overlapping.
    pub spans: Vec<RedactionSpan>,
    /// DR-72 ③ (option c): the splice would have produced text that is no
    /// longer valid JSON, so it was **refused** and `redacted == original`.
    /// The refusal is explicit rather than silent.
    pub refused: Option<String>,
}

impl RedactionReport {
    pub fn changed(&self) -> bool {
        self.redacted != self.original
    }
}

/// DR-74 ②: the variables whose **entire** value is one sensitive value.
///
/// A `;`-separated `PATH` is a single environment value that discloses a whole
/// list of directories; the user name that actually leaked travelled in its
/// **tail** (only the first element was redacted).  Segment-by-segment redaction
/// would need one span per element for the same assignment and would still leave
/// the delimiters and element count readable; treating the whole value as
/// sensitive is the rule the other assignments already follow ("the variable's
/// value is the sensitive thing") and cannot miss an element.  `Path` is the
/// spelling `cmd` prints.
pub const WHOLE_VALUE_VARS: &[&str] = &["PATH", "Path"];

/// DR-79 ④: variables whose value is an entire **command line**.
///
/// A command line is neither a path nor a quoted value.  It carries quoted
/// arguments (written `\"` in a JSON dump), `;`/`&&` separators and `>>`
/// redirections, so the generic rule — which stops at `;` and at the first
/// `\"` — leaves the tail of the line visible.  The DR-79 fixture is exactly
/// that: the `model.secret.env` argument sits after both the first `;` and the
/// first `\"`.  A command line therefore ends only at the **logical line
/// boundary**: a physical `\n`/`\r`, the JSON `\n`/`\r` escape, or the closing
/// quote of the containing JSON string.  Everything in between — separators,
/// quotes, doubled backslashes — is one sensitive value.
///
/// Only the harness's own `DSH_TERM_CMD` is in this set; `PATH` keeps its own
/// (whole-value) rule, whose `;`-separated elements are still one value but
/// whose JSON terminator is an escape.
pub const COMMAND_LINE_VARS: &[&str] = &["DSH_TERM_CMD"];

/// DR-74 ①: how many backslashes immediately precede `index`?
///
/// Used for the two "is this byte escaped?" questions: an escape starts only at a
/// backslash preceded by an **even** run, and a `"` ends a JSON string only when
/// it is preceded by an **even** run.
fn preceding_backslashes(bytes: &[u8], index: usize) -> usize {
    let mut count = 0usize;
    let mut cursor = index;
    while cursor > 0 && bytes[cursor - 1] == b'\\' {
        count += 1;
        cursor -= 1;
    }
    count
}

/// DR-74 ①: does an escape sequence begin at `index`?
///
/// Only a backslash that is **not itself escaped** starts an escape, i.e. one
/// preceded by an even number of backslashes.  The JSON encoder writes a literal
/// backslash as `\\`, so a Windows path component named `runs` arrives as
/// `…\\runs…`; the DR-72 predicate fired on the **second** byte of that pair
/// (a backslash followed by `r`), deleted one backslash, and let the surviving
/// `\r` decode back to a carriage return.
fn escape_starts_at(bytes: &[u8], index: usize) -> bool {
    bytes.get(index) == Some(&b'\\') && preceding_backslashes(bytes, index) % 2 == 0
}

/// DR-72 ① / DR-74 ①③: the terminator that ends an unquoted value.
///
/// * `;` — unless the variable is one of [`WHOLE_VALUE_VARS`], whose whole value
///   is sensitive (DR-74 ②);
/// * a physical `\n`/`\r` — the plain-text dump's line ending;
/// * **inside JSON**, an unescaped backslash that does not begin the literal
///   escape `\\`: every real escape (`\n`, `\r`, `\t`, `\uXXXX`, `\"`, …) ends the
///   value, while an escaped backslash (a path separator) does not (DR-74 ①③);
/// * **inside JSON**, an unescaped `"` — the closing quote of the containing
///   string, which is the end of the value when the assignment is the last thing
///   in it.
///
/// Escape awareness is deliberately limited to JSON: in a plain-text dump (`set`
/// output) a backslash is just a byte, and treating `\r` in `\repo` as an escape
/// is what cut the value short and left a user name visible (DR-74 ②).
///
/// **The terminator is not consumed** ([`assignment_value_end`] returns its
/// index), so the escape's own bytes survive and the string keeps its closing
/// quote, its comma and the field after it.  The damage DR-72 stopped came from
/// the opposite mistake: the scan ran **past** the escape to the physical line
/// ending, leaving a physical newline inside an unterminated string — that, not
/// the deletion of a backslash, is what produced the control character.
fn is_value_terminator(bytes: &[u8], index: usize, json: bool, whole_value: bool) -> bool {
    match bytes[index] {
        b'\n' | b'\r' => true,
        b';' => !whole_value,
        b'"' if json => preceding_backslashes(bytes, index) % 2 == 0,
        b'\\' if json => escape_starts_at(bytes, index) && bytes.get(index + 1) != Some(&b'\\'),
        _ => false,
    }
}

/// DR-72 ①: does `raw` look like JSON at all?  Used to decide whether the
/// post-splice parseability check (option c) applies.  The decision is made on
/// the first non-space byte.
fn looks_like_json(raw: &str) -> bool {
    matches!(raw.trim_start().chars().next(), Some('{') | Some('['))
}

/// DR-72 ①/③: replace every secret **assignment** (`NAME=<value>`) and report
/// the exact spans, without ever guessing past a JSON escape.
///
/// DR-69: erase the assignment, not only the secret's value.  The round that
/// exposed that never leaked a key: the Developer ran `set | findstr /i "HOH"`,
/// and the harness's own `DSH_TERM_CMD` was written into the trajectory and
/// then into a committed evidence file as
/// `export HOH_MODEL_API_KEY="$(cat /c/Users/.../keyval.txt)"; ...`.  No file
/// contained the credential, but every file recorded **where it lives**.  A
/// value-substitution scan cannot see that: the dangling reference contains no
/// secret.  The variable name is the thing that must not survive, so the whole
/// assignment is replaced.
///
/// The scan keeps three facts at once:
/// * the cursor advances past each replacement, so a match cannot be re-found
///   inside its own replacement text;
/// * a `"`-quoted value ends at the closing quote, which is **not** consumed
///   (the DR-69 shape `NAME="$(cat …)"`);
/// * an unquoted value ends at [`is_value_terminator`], which stops on any real
///   JSON escape and on the string's closing quote, so an escape is never
///   mistaken for the end of the physical line and no backslash is ever deleted;
/// * the whole value of a [`WHOLE_VALUE_VARS`] variable (a `;`-separated `PATH`)
///   is inside one span, so its tail cannot leak a user name (DR-74 ②).
pub fn redact_secret_assignments_traced(text: &str) -> RedactionReport {
    let report = splice_assignments(text);
    // DR-72 ③ (option c): validate before accepting.  A splice that breaks a
    // JSON document is refused outright, because an unparseable trajectory is
    // exactly the damage this batch exists to stop.
    if report.changed() && looks_like_json(text) {
        if let Err(error) = serde_json::from_str::<serde_json::Value>(&report.redacted) {
            return RedactionReport {
                original: text.to_string(),
                redacted: text.to_string(),
                spans: Vec::new(),
                refused: Some(format!(
                    "the secret-assignment splice was refused because the result is no longer \
                     valid JSON ({error}); the original text is left byte-for-byte unchanged"
                )),
            };
        }
    }
    report
}

/// DR-72 ①: the splice itself, with no policy applied.
///
/// DR-81 ③: the span guard is a real interval-overlap test, and a candidate that
/// contains a recorded span absorbs it.  The previous "starts before the largest
/// span end seen so far" test let one late occurrence of an early-scanned name
/// hide every earlier occurrence of every later-scanned one, which is how a
/// repeated environment dump kept whole variable families raw in `smoke-t14`.
fn splice_assignments(text: &str) -> RedactionReport {
    let json = looks_like_json(text);
    let mut spans: Vec<RedactionSpan> = Vec::new();
    for name in SECRET_ENV_VARS
        .iter()
        .copied()
        .chain(HARNESS_ENV_VARS.iter().copied())
    {
        let needle = format!("{name}=");
        let mut cursor = 0usize;
        while let Some(found) = text[cursor..].find(needle.as_str()) {
            let start = cursor + found;
            let value_start = start + needle.len();
            let value_end = assignment_value_end(
                text,
                value_start,
                json,
                WHOLE_VALUE_VARS.contains(&name),
                COMMAND_LINE_VARS.contains(&name),
            );
            // DR-81 ③: a **real interval overlap** test, not a global
            // "begins before the largest end seen so far" test.
            //
            // The old guard `start < span.end` was the whole mechanism of the
            // `smoke-t14` disclosure: the trajectory repeated its environment
            // dump four times, one `OPENAI_API_KEY=` occurrence sat late in the
            // file (286080-286095), and because `OPENAI_API_KEY` is scanned
            // before the whole `HOH_*`/`DSH_TERM_CMD`/`PATH` family, **every
            // earlier occurrence of every later-scanned name** was reported
            // `SKIP(overlap)` against it and survived raw.
            //
            // The test is now the interval intersection `[start, value_end) ∩
            // span ≠ ∅`, and a candidate that **contains** a recorded span
            // absorbs it: the recorded span's replacement only covered part of
            // this value, so keeping it would leave the candidate's own tail
            // raw.  That is exactly the shape a `DSH_TERM_CMD` line takes when
            // its command line carries an `HOH_ROLE=<value>` argument — the
            // `HOH_ROLE` span is recorded first (it is earlier in
            // `HARNESS_ENV_VARS`) and the whole command line must still be
            // replaced.  A candidate that merely lies *inside* an already
            // recorded span is left alone, exactly as before: that span already
            // replaces it, and the DR-73/DR-74 frozen sample pins the surviving
            // tail of that shape as a documented cost.
            let absorbed: Vec<usize> = spans
                .iter()
                .enumerate()
                .filter(|(_, span)| {
                    start <= span.start && span.end <= value_end && start < span.end
                })
                .map(|(index, _)| index)
                .collect();
            if !absorbed.is_empty() {
                let kept: Vec<RedactionSpan> = spans
                    .iter()
                    .enumerate()
                    .filter(|(index, _)| !absorbed.contains(index))
                    .map(|(_, span)| span.clone())
                    .collect();
                spans = kept;
                spans.push(RedactionSpan {
                    name: name.to_string(),
                    start,
                    end: value_end,
                    replacement: format!("{needle}{REDACTED}"),
                });
            } else if !spans
                .iter()
                .any(|span| start < span.end && span.start < value_end)
            {
                spans.push(RedactionSpan {
                    name: name.to_string(),
                    start,
                    end: value_end,
                    replacement: format!("{needle}{REDACTED}"),
                });
            }
            cursor = value_end.max(start + needle.len());
        }
    }
    spans.sort_by_key(|span| span.start);
    let mut redacted = String::with_capacity(text.len());
    let mut position = 0usize;
    for span in &spans {
        if span.start < position {
            continue;
        }
        redacted.push_str(&text[position..span.start]);
        redacted.push_str(&span.replacement);
        position = span.end;
    }
    redacted.push_str(&text[position..]);
    RedactionReport {
        original: text.to_string(),
        redacted,
        spans,
        refused: None,
    }
}

/// DR-79 ④: where a **command-line** value ends.
///
/// Only the logical line boundary ends it:
/// * a physical `\n` or `\r` (a plain-text `set`/`env` dump prints one variable
///   per line);
/// * in JSON, the `\n`/`\r` **escape** the encoder writes for that physical
///   line ending;
/// * in JSON, an unescaped closing quote of the containing string.
///
/// Deliberately **not** a terminator: `;`, `&&`, `|`, `>>`, a `\"` quoted
/// argument, or a `\\` path separator.  The DR-79 fixture puts
/// `config/model.secret.env` after both the first `;` and the first `\"`, so
/// every one of those had to stop being a boundary for this variable.
fn command_line_value_ends_at(bytes: &[u8], index: usize, json: bool) -> bool {
    match bytes[index] {
        b'\n' | b'\r' => true,
        b'"' if json => preceding_backslashes(bytes, index) % 2 == 0,
        b'\\' if json => {
            escape_starts_at(bytes, index)
                && matches!(bytes.get(index + 1), Some(b'n') | Some(b'r'))
        }
        _ => false,
    }
}

/// DR-72 ① / DR-74 ①③: where an unquoted value ends.
///
/// Inside a JSON string (which is where a trajectory records an environment
/// dump) the scan stops at every real escape and at the closing quote, so the
/// escape's own bytes survive and the string's closing quote and the comma after
/// it are never eaten.  Escape awareness is limited to JSON: in a plain-text dump
/// a backslash is just a byte (DR-74 ②).
///
/// `whole_value` marks a variable whose entire value is sensitive
/// ([`WHOLE_VALUE_VARS`]): its `;`-separated elements are all inside the span.
///
/// `command_line` marks a variable whose value is a whole command line
/// ([`COMMAND_LINE_VARS`], DR-79 ④).  That value is bounded by nothing but the
/// logical line end, so it is computed before — and independently of — the
/// quoted-value and generic rules below.
fn assignment_value_end(
    text: &str,
    value_start: usize,
    json: bool,
    whole_value: bool,
    command_line: bool,
) -> usize {
    let bytes = text.as_bytes();
    if command_line {
        let mut index = value_start;
        while index < bytes.len() {
            if command_line_value_ends_at(bytes, index, json) {
                // The terminator is not consumed, exactly as everywhere else.
                return index;
            }
            index += 1;
        }
        return text.len();
    }
    if bytes.get(value_start) == Some(&b'"') {
        // The DR-69 `NAME="$(cat …)"` shape: the value ends at the closing
        // quote, which is *not* consumed — that keeps any bytes the two rules
        // share (a quote is never a JSON escape) out of the replaced span.
        let mut index = value_start + 1;
        while index < bytes.len() {
            match bytes[index] {
                b'\\' => index += 2,
                b'"' => return index,
                _ => index += 1,
            }
        }
        return text.len();
    }
    if json && bytes.get(value_start) == Some(&b'\\') && bytes.get(value_start + 1) == Some(&b'"') {
        // DR-74 ③: the same DR-69 shape as a JSON encoder writes it
        // (`NAME=\"$(cat …)\"`): the value is quoted, so it ends at the closing
        // escaped quote, which is not consumed.
        let mut index = value_start + 2;
        while index < bytes.len() {
            if bytes[index] == b'\\'
                && bytes.get(index + 1) == Some(&b'"')
                && preceding_backslashes(bytes, index) % 2 == 0
            {
                return index;
            }
            if bytes[index] == b'\\' {
                index += 2;
                continue;
            }
            index += 1;
        }
        return text.len();
    }
    let mut index = value_start;
    while index < bytes.len() {
        if is_value_terminator(bytes, index, json, whole_value) {
            // The terminator is **not** consumed.  For an escape that is the
            // whole point: its two bytes survive, so the JSON string stays
            // closed, keeps its comma and keeps the field after it.
            return index;
        }
        index += 1;
    }
    text.len()
}

/// DR-69/DR-72: [`redact_secret_assignments_traced`] without the span report.
pub fn redact_secret_assignments(text: &str) -> String {
    redact_secret_assignments_traced(text).redacted
}

/// DR-72 ①: the audit helper the invariant test uses — does `report` describe a
/// pure splice of its input?
///
/// Returns `Some(0)` when the output is exactly the input with the reported
/// spans replaced, i.e. when every byte outside the spans is unchanged.  The
/// number is the count of outside-span bytes that differ from the input, so a
/// caller can assert it is zero; `None` means the report is internally
/// inconsistent (an out-of-range or overlapping span) and therefore useless as
/// evidence.
pub fn bytes_changed_outside_spans(report: &RedactionReport) -> Option<usize> {
    let original = report.original.as_bytes();
    let mut rebuilt: Vec<u8> = Vec::with_capacity(report.redacted.len());
    let mut position = 0usize;
    for span in &report.spans {
        if span.start < position || span.end > original.len() || span.start > span.end {
            return None;
        }
        rebuilt.extend_from_slice(&original[position..span.start]);
        rebuilt.extend_from_slice(span.replacement.as_bytes());
        position = span.end;
    }
    rebuilt.extend_from_slice(&original[position..]);
    if rebuilt != report.redacted.as_bytes() {
        return None;
    }
    // The reconstruction above *is* the proof that the output differs from the
    // input only inside the spans: it was built from the input's outside-span
    // bytes and the replacements, and it equals the output byte for byte.
    Some(0)
}

/// DR-72 ②: the areas of a run directory whose bytes are **frozen evidence**.
///
/// D276: "in-place rewriting of evidence has damaged three rounds".  A path
/// under one of these prefixes is never written by a redaction pass; when a
/// secret or a harness value is found there, a **generated copy** is written
/// next to the original (`<name>.redacted.<ext>`) and the original keeps every
/// byte.  The runtime applies the mark before the role that reads the area
/// runs, and the tests assert the property directly.
#[derive(Clone, Debug, Default)]
pub struct SealedAreas {
    roots: Vec<PathBuf>,
}

impl SealedAreas {
    pub fn new(roots: impl IntoIterator<Item = PathBuf>) -> Self {
        Self {
            roots: roots.into_iter().collect(),
        }
    }

    pub fn is_empty(&self) -> bool {
        self.roots.is_empty()
    }

    /// Is `path` inside a sealed area?  The comparison is lexical and
    /// component-wise, so `…/candidate-evil` never matches `…/candidate`.
    pub fn contains(&self, path: &Path) -> bool {
        self.roots
            .iter()
            .any(|root| path == root || path.starts_with(root))
    }
}

/// DR-72 ②: what one pass over a tree did.
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct TreeRedactionReport {
    /// Files whose bytes were rewritten in place (never a sealed file).
    pub rewritten: Vec<PathBuf>,
    /// Frozen files whose redacted form was generated as a copy.
    pub copies: Vec<PathBuf>,
    /// Files where a splice was refused because it would break JSON.
    pub refusals: Vec<(PathBuf, String)>,
}

impl TreeRedactionReport {
    /// The number of files a caller should report as "scrubbed" (DR-19's
    /// `secret_redactions`): every rewritten file and every generated copy.
    pub fn hits(&self) -> u64 {
        (self.rewritten.len() + self.copies.len()) as u64
    }

    pub fn is_empty(&self) -> bool {
        self.rewritten.is_empty() && self.copies.is_empty() && self.refusals.is_empty()
    }

    /// Every path this pass created or rewrote, for a report that names them.
    pub fn touched(&self) -> Vec<PathBuf> {
        self.rewritten
            .iter()
            .chain(self.copies.iter())
            .cloned()
            .collect()
    }
}

/// DR-72 ②: the suffix a generated redacted copy carries.
pub const REDACTED_COPY_SUFFIX: &str = ".redacted";

/// DR-72 ②: the generated copy's path for `path` (`foo.json` ->
/// `foo.redacted.json`).
pub fn redacted_copy_path(path: &Path) -> PathBuf {
    let name = path
        .file_name()
        .map(|name| name.to_string_lossy().into_owned())
        .unwrap_or_else(|| "artifact".to_string());
    let copy = match name.rsplit_once('.') {
        Some((stem, extension)) if !stem.is_empty() => {
            format!("{stem}{REDACTED_COPY_SUFFIX}.{extension}")
        }
        _ => format!("{name}{REDACTED_COPY_SUFFIX}"),
    };
    path.with_file_name(copy)
}

/// DR-72 ②: scrub `text` for both rules and report what changed.
///
/// * the secret **assignments** are replaced first (DR-72 ①) — that is the
///   maximal span, so a value inside one is already gone and cannot produce an
///   overlapping second span;
/// * then the known secret **values** anywhere outside those spans are replaced
///   (DR-19);
/// * a splice that would break JSON is refused and reported (DR-72 ③).
///
/// Every span is recorded in the **input** coordinate space and the spans never
/// overlap, so [`bytes_changed_outside_spans`] is a meaningful audit of the whole
/// pass: the output is exactly the input with those spans replaced.
pub fn scrub_text(text: &str, secrets: &[String]) -> RedactionReport {
    let assignment = redact_secret_assignments_traced(text);
    // DR-72 ③: validate **before accepting the assignment splice**.  When the
    // input is JSON and the assignment rule would leave it unparseable, the
    // assignment spans are dropped and the refusal is reported; the value rule is
    // still safe, because substituting a literal credential can never change the
    // structure of a document.
    let (assignment_spans, refused) = match (&assignment.refused, looks_like_json(text)) {
        (Some(problem), true) => (Vec::new(), Some(problem.clone())),
        _ => (assignment.spans.clone(), None),
    };
    let mut spans = assignment_spans;
    for secret in secrets {
        if secret.is_empty() {
            continue;
        }
        let mut cursor = 0usize;
        while let Some(found) = text[cursor..].find(secret.as_str()) {
            let start = cursor + found;
            let end = start + secret.len();
            if overlaps(&spans, start, end) {
                cursor = end;
                continue;
            }
            spans.push(RedactionSpan {
                name: "value".to_string(),
                start,
                end,
                replacement: REDACTED.to_string(),
            });
            cursor = end;
        }
    }
    spans.sort_by_key(|span| span.start);
    let redacted = splice_spans(text, &spans);
    // A JSON input whose *value* redaction somehow broke it is still refused: the
    // structural guarantee has to hold for every splice, not only for the
    // assignment rule.
    if refused.is_none() && looks_like_json(text) && redacted != text {
        if let Err(error) = serde_json::from_str::<serde_json::Value>(&redacted) {
            return RedactionReport {
                original: text.to_string(),
                redacted: text.to_string(),
                spans: Vec::new(),
                refused: Some(format!(
                    "the redaction was refused because the result is no longer valid JSON \
                     ({error}); the original text is left byte-for-byte unchanged"
                )),
            };
        }
    }
    RedactionReport {
        original: text.to_string(),
        redacted,
        spans,
        refused,
    }
}

/// DR-72 ②: does `[start, end)` overlap one of `spans`?
fn overlaps(spans: &[RedactionSpan], start: usize, end: usize) -> bool {
    spans
        .iter()
        .any(|span| start < span.end && span.start < end)
}

/// DR-72 ①: build the output by replacing `spans` in `text`.
fn splice_spans(text: &str, spans: &[RedactionSpan]) -> String {
    let mut out = String::with_capacity(text.len());
    let mut position = 0usize;
    for span in spans {
        if span.start < position || span.end > text.len() {
            continue;
        }
        out.push_str(&text[position..span.start]);
        out.push_str(&span.replacement);
        position = span.end;
    }
    out.push_str(&text[position..]);
    out
}

/// DR-72 (dispatcher addition 1): is `text` free of every known secret value
/// and of every assignment to a known or harness variable?
pub fn scrub_is_clean(text: &str, secrets: &[String]) -> bool {
    if secrets
        .iter()
        .any(|secret| !secret.is_empty() && text.contains(secret.as_str()))
    {
        return false;
    }
    !redact_secret_assignments_traced(text).changed()
}

/// DR-19/DR-72: scan every file under `root` and erase both the known secret
/// values and every secret/harness assignment.
///
/// A file inside `sealed` is **never written**: its redacted form is generated
/// as `<name>.redacted.<ext>` next to it (DR-72 ②).  Returns the pass report.
pub fn redact_tree_traced(
    root: &Path,
    secrets: &[String],
    sealed: &SealedAreas,
) -> anyhow::Result<TreeRedactionReport> {
    // DR-69: the assignment rule needs no secret value, so the scan runs even
    // when no credential is configured -- the credential's *location* is what
    // leaked in `smoke-t9`, and that leak has nothing to do with whether this
    // process can resolve the key itself.
    let mut report = TreeRedactionReport::default();
    if !root.exists() {
        return Ok(report);
    }
    for entry in WalkDir::new(root).follow_links(false) {
        let entry = entry?;
        if !entry.file_type().is_file() {
            continue;
        }
        let path = entry.path().to_path_buf();
        // The generated copies are derived artifacts, not sources: scanning
        // them again would keep producing `x.redacted.redacted.json`.
        if path
            .file_name()
            .map(|name| name.to_string_lossy().contains(REDACTED_COPY_SUFFIX))
            .unwrap_or(false)
        {
            continue;
        }
        let bytes = std::fs::read(&path)?;
        // Secrets are ASCII-ish credentials; a non-UTF-8 file cannot contain a
        // literal textual key that the model could echo.
        let Ok(text) = String::from_utf8(bytes) else {
            continue;
        };
        let scrubbed = scrub_text(&text, secrets);
        if let Some(problem) = &scrubbed.refused {
            // The refusal is always reported, even when the value rule still had
            // something to do: a silent refusal would be the old failure mode.
            report.refusals.push((path.clone(), problem.clone()));
        }
        if !scrubbed.changed() {
            continue;
        }
        if sealed.contains(&path) {
            let copy = redacted_copy_path(&path);
            std::fs::write(&copy, scrubbed.redacted.as_bytes())?;
            report.copies.push(copy);
        } else {
            std::fs::write(&path, scrubbed.redacted.as_bytes())?;
            report.rewritten.push(path);
        }
    }
    Ok(report)
}

/// DR-19/DR-72: [`redact_tree_traced`] with no sealed area, returning the DR-19
/// hit count (files rewritten, plus frozen files whose copy was generated).
pub fn redact_tree(root: &Path, secrets: &[String]) -> anyhow::Result<u64> {
    Ok(redact_tree_traced(root, secrets, &SealedAreas::default())?.hits())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn reassemble(report: &RedactionReport) -> String {
        let mut out = String::new();
        let mut position = 0usize;
        for span in &report.spans {
            out.push_str(&report.original[position..span.start]);
            out.push_str(&span.replacement);
            position = span.end;
        }
        out.push_str(&report.original[position..]);
        out
    }

    #[test]
    fn blocked_env_covers_every_known_variable() {
        let env = blocked_env();
        assert_eq!(env.len(), SECRET_ENV_VARS.len());
        for name in SECRET_ENV_VARS {
            assert_eq!(env.get(*name).map(String::as_str), Some(""));
        }
    }

    /// DR-69: an environment dump must not record where the credential lives.
    #[test]
    fn an_environment_dump_does_not_leak_the_credential_channel() {
        let dumped = "cd /f/x; export HOH_MODEL_API_KEY=\"$(cat /c/Users/u/AppData/Local/\
                      Temp/t9/keyval.txt)\"; set HOH=1";
        let redacted = redact_secret_assignments(dumped);
        assert!(
            !redacted.contains("keyval.txt"),
            "the key file's path must not survive: {redacted}"
        );
        assert!(
            redacted.contains(&format!("HOH_MODEL_API_KEY={REDACTED}")),
            "{redacted}"
        );
        // The bare `cmd` spelling (`set NAME=value`) is the same leak.
        let redacted = redact_secret_assignments("set OPENAI_API_KEY=abc123; echo hi");
        assert!(!redacted.contains("abc123"), "{redacted}");
        assert!(redacted.contains("echo hi"), "{redacted}");
        // Text that assigns nothing is untouched, byte for byte.
        assert_eq!(redact_secret_assignments("echo hello\n"), "echo hello\n");
    }

    /// DR-72 ①: the adversarial shape.  The assignment sits inside a JSON string
    /// and the value is followed by a JSON-escaped newline, i.e. the two
    /// characters `\` + `n` — not a physical line ending.  The old scanner ran
    /// to the end of the physical line, deleted the rest of the string, its
    /// closing quote and the comma, and left the round's trajectory unparseable.
    #[test]
    fn an_assignment_inside_a_json_string_survives_an_escaped_newline() {
        let original =
            "{\n  \"content\": \"<output>\\nHOH_MODEL_API_KEY=<value>\\n</output>\",\n  \
                        \"extra\": {\"returncode\": 0}\n}\n";
        serde_json::from_str::<serde_json::Value>(original)
            .expect("the fixture must be valid JSON before the scan");
        assert!(
            original.contains("HOH_MODEL_API_KEY=<value>\\n"),
            "the fixture must place the escape directly after the value: {original}"
        );

        let report = redact_secret_assignments_traced(original);
        assert!(
            report.refused.is_none(),
            "the splice must be accepted for this shape: {:?}",
            report.refused
        );
        assert!(
            report.changed(),
            "the assignment really is in the text: {original}"
        );
        // The invariant: still valid JSON, unchanged outside the spans, and the
        // spans reassemble the output exactly.
        serde_json::from_str::<serde_json::Value>(&report.redacted).unwrap_or_else(|error| {
            panic!(
                "the redacted trajectory must still parse ({error}); got:\n{}",
                report.redacted
            )
        });
        assert_eq!(
            bytes_changed_outside_spans(&report),
            Some(0),
            "every byte outside the reported spans must be identical"
        );
        assert_eq!(reassemble(&report), report.redacted);
        assert!(
            !report.redacted.contains("<value>"),
            "the value must be gone: {}",
            report.redacted
        );
        // The consequence the old code destroyed: the closing quote, the comma
        // and the following field are still there.
        let value: serde_json::Value = serde_json::from_str(&report.redacted).expect("json");
        assert_eq!(value["extra"]["returncode"], 0);
        assert!(value["content"]
            .as_str()
            .expect("content is a string")
            .ends_with("</output>"));
    }

    /// DR-72 ① / DR-74 ①: a Windows path in a JSON string is written with
    /// **doubled** backslashes (`C:\\Users\\u`), so a scan that stopped at the
    /// second byte of such a pair would cut the value in half and delete one
    /// backslash — turning the surviving `\` + `r`/`n` into a real JSON escape.
    ///
    /// The fixture is the **real encoding**: doubled path separators and a real
    /// `\` + `n` escape that ends the assignment's logical line.  The value also
    /// crosses a `;`, so the terminator that decides it is the escape, not the
    /// semicolon (the DR-72 test this replaces was decided by a `;` before any
    /// escape was consulted — DR-74 ④).
    #[test]
    fn a_windows_path_value_is_not_mistaken_for_an_escape() {
        let original = "{\"env\": \"PATH=C:\\\\Users\\\\u\\\\node_modules\\\\.bin;C:\\\\stand-in\\\\bin\\\\runs\\\\run-1\\nnext\"}\n";
        serde_json::from_str::<serde_json::Value>(original).expect("the fixture is valid JSON");
        assert!(
            original.contains("\\\\runs"),
            "the fixture must carry the doubled-backslash `runs` component: {original}"
        );

        let report = redact_secret_assignments_traced(original);
        assert!(
            report.changed(),
            "the assignment must be replaced: {report:?}"
        );
        assert!(
            report.refused.is_none(),
            "a bounded value must never be refused: {:?}",
            report.refused
        );
        assert_eq!(report.spans.len(), 1, "{report:?}");
        // Non-vacuity of the escape predicate: the span must end **on the escape**
        // (`\` + `n`), i.e. the scan really consulted it rather than a `;`.
        let end = report.spans[0].end;
        let bytes = original.as_bytes();
        assert_eq!(
            (bytes[end], bytes.get(end + 1)),
            (b'\\', Some(&b'n')),
            "the value must end at the real escape, not at a semicolon: {:?}",
            &original[report.spans[0].start..end + 2]
        );

        let value: serde_json::Value =
            serde_json::from_str(&report.redacted).expect("still valid JSON");
        let env = value["env"].as_str().expect("env is a string");
        assert_eq!(
            env,
            format!("PATH={REDACTED}\nnext"),
            "the whole path value must be gone and only the field after the escape must survive"
        );
        assert_eq!(
            bytes_changed_outside_spans(&report),
            Some(0),
            "the repair must be a pure splice"
        );
    }

    /// DR-74 ①: the headline defect, in the **real encoding** of a trajectory.
    ///
    /// Every Windows path in `runs/<id>/iter-*/traj/*.json` is written with
    /// doubled backslashes, and the assignment's logical line ends with a real
    /// `\` + `n` escape.  The DR-72 predicate fired on the **second** byte of the
    /// `\\runs` pair: it deleted one backslash, the surviving `\` + `r` decoded to
    /// a carriage return, and the rest of the path stayed visible while the JSON
    /// validation gate could not refuse it (the result still parsed).  This test
    /// asserts the three facts the acceptance demanded: no CR/LF is **injected**,
    /// no path tail survives, and every byte outside the reported span is
    /// unchanged.
    #[test]
    fn a_doubled_backslash_path_does_not_inject_a_control_character() {
        // Real encoding: `\\` for every path separator, one real `\n` escape.
        let original = "{\"env\": \"HOH_GAME_ROUTE=F:\\\\moonbit-hof-rs\\\\runs\\\\smoke-t10\\\\iter-1\\\\node_modules\\\\pkg\\\\index.js\\nHOH_HOH_BIN=F:\\\\moonbit-hof-rs\\\\target\\\\release\\\\hoh.exe\\n</output>\"}\n";
        let parsed: serde_json::Value =
            serde_json::from_str(original).expect("the fixture is valid JSON");
        let before = parsed["env"].as_str().expect("env").to_string();
        assert!(
            original.contains("\\\\runs\\\\smoke-t10") && original.contains("\\\\node_modules"),
            "the fixture must use the real doubled-backslash encoding: {original}"
        );

        let report = redact_secret_assignments_traced(original);
        assert!(report.changed(), "{report:?}");
        assert!(
            report.refused.is_none(),
            "the real shape must be bounded, not refused: {:?}",
            report.refused
        );
        let output: serde_json::Value =
            serde_json::from_str(&report.redacted).expect("still valid JSON");
        let after = output["env"].as_str().expect("env").to_string();

        // (i) no control character is injected: the decoded value carries exactly
        // the line breaks it carried before, no more.
        assert_eq!(
            after.matches('\r').count(),
            before.matches('\r').count(),
            "a carriage return was injected into the decoded value: {after:?}"
        );
        assert_eq!(
            after.matches('\n').count(),
            before.matches('\n').count(),
            "a newline was injected into the decoded value: {after:?}"
        );
        assert!(!after.contains('\r'), "{after:?}");
        // (ii) no path tail survives.
        assert!(
            after.starts_with(&format!("HOH_GAME_ROUTE={REDACTED}")),
            "the assignment must be replaced: {after:?}"
        );
        for tail in ["runs", "smoke-t10", "node_modules", "moonbit-hof-rs\\runs"] {
            assert!(
                !after.contains(tail),
                "the path tail `{tail}` survived: {after:?}"
            );
        }
        // The field after the escape is untouched.
        assert!(after.ends_with("</output>"), "{after:?}");
        // (iii) zero bytes changed outside the reported span.
        assert_eq!(
            bytes_changed_outside_spans(&report),
            Some(0),
            "the repair must be a pure splice"
        );

        // The acceptance's exact p14 shape: the value is the last thing in the
        // JSON string, so the **unescaped closing quote** must bound it — a
        // bounded value, not a refusal, and the tail is gone.
        let quoted =
            "{\"env\": \"HOH_ARTIFACT_DIR=F:\\\\moonbit-hof-rs\\\\runs\\\\smoke-t10\\\\iter-1\"}";
        let report = redact_secret_assignments_traced(quoted);
        assert!(
            report.refused.is_none(),
            "the closing-quote shape must be bounded, not refused: {:?}",
            report.refused
        );
        let value: serde_json::Value =
            serde_json::from_str(&report.redacted).expect("still valid JSON");
        let env = value["env"].as_str().expect("env is a string");
        assert_eq!(
            env,
            format!("HOH_ARTIFACT_DIR={REDACTED}"),
            "the whole value must be replaced, with no path tail and no injected control character"
        );
        assert!(!env.contains('\r') && !env.contains('\n'), "{env:?}");
        assert_eq!(bytes_changed_outside_spans(&report), Some(0));
    }

    /// DR-74 ②: a user name in a **later** element of a `;`-separated `PATH` is
    /// the same disclosure as one in the first element.  The whole `PATH` value is
    /// treated as one sensitive value (see [`assignment_value_end`]).
    #[test]
    fn a_user_name_in_a_semicolon_separated_path_tail_is_redacted() {
        let original = "PATH=C:\\Windows\\system32;C:\\Program Files\\nodejs;C:\\Users\\wyl\\AppData\\Roaming\\npm\n";
        let report = redact_secret_assignments_traced(original);
        assert!(report.changed(), "{report:?}");
        assert!(
            !report.redacted.contains("wyl"),
            "the user name must not survive anywhere in the value: {}",
            report.redacted
        );
        assert!(
            !report.redacted.contains("C:\\Users"),
            "every `;`-separated element is part of the same sensitive value: {}",
            report.redacted
        );
        assert!(
            report.redacted.contains(&format!("PATH={REDACTED}")),
            "{}",
            report.redacted
        );
    }

    /// DR-74 ②: a plain-text dump is **not** JSON, so backslashes in it are not
    /// escapes.  The DR-72 predicate read the `\r` of `\repo`/`\runs` as an escape
    /// and stopped there — a regression against the old scanner, which ran to the
    /// physical line end and removed the whole value, user name included.
    #[test]
    fn a_path_with_a_backslash_r_component_still_redacts_the_user_name() {
        let original = "HOH_ARTIFACT_DIR=F:\\repo\\Users\\wyl\\runs\\run-1\n";
        let report = redact_secret_assignments_traced(original);
        assert!(report.changed(), "{report:?}");
        assert!(
            !report.redacted.contains("wyl") && !report.redacted.contains("Users"),
            "the whole plain-text value must go, as the pre-DR-72 scanner did: {}",
            report.redacted
        );
        assert_eq!(
            report.redacted,
            format!("HOH_ARTIFACT_DIR={REDACTED}\n"),
            "only the physical line ending may bound the value in plain text"
        );
    }

    /// DR-74 ③: an escape family other than `\n`/`\r` (`\t`, `\"`, `\uXXXX`) must
    /// not silently drop the assignment rule.  The DR-72 scanner ran such a value
    /// to the physical line end, produced invalid JSON and **refused**, leaving
    /// `NAME=` in the evidence for a perfectly legitimate JSON file.  Any escape
    /// that is not the literal-backslash escape `\\` now ends the value.
    #[test]
    fn other_json_escape_families_do_not_drop_the_assignment_redaction() {
        let secret = "test-key-not-a-secret";
        let cases = [
            (
                "\\t",
                "{\"a\": \"HOH_MODEL_API_KEY=test-key-not-a-secret\\tX\"}\n",
            ),
            (
                "\\\"",
                "{\"a\": \"HOH_MODEL_API_KEY=test-key-not-a-secret\\\"X\"}\n",
            ),
            (
                "\\uXXXX",
                "{\"a\": \"HOH_MODEL_API_KEY=test-key-not-a-secret\\u0041X\"}\n",
            ),
        ];
        for (label, original) in cases {
            serde_json::from_str::<serde_json::Value>(original)
                .unwrap_or_else(|error| panic!("the {label} fixture must be valid JSON: {error}"));
            let report = redact_secret_assignments_traced(original);
            assert!(
                report.refused.is_none(),
                "the {label} family must be handled, not refused: {:?}",
                report.refused
            );
            assert!(report.changed(), "the {label} family must be redacted");
            let value: serde_json::Value = serde_json::from_str(&report.redacted)
                .unwrap_or_else(|error| panic!("the {label} splice must stay valid JSON: {error}"));
            let text = value["a"].as_str().expect("a");
            assert!(
                !text.contains(secret),
                "the {label} family left the credential value visible: {text}"
            );
            assert!(
                text.starts_with(&format!("HOH_MODEL_API_KEY={REDACTED}")),
                "the {label} family left the assignment name visible: {text}"
            );
            assert!(
                text.ends_with('X'),
                "the {label} family must not eat what followed the escape: {text}"
            );
            assert_eq!(
                bytes_changed_outside_spans(&report),
                Some(0),
                "the {label} splice must be pure"
            );
        }
    }

    /// DR-72 ①: what followed the assignment **inside the same JSON string**
    /// survives — which is exactly what the old scan destroyed.  The value is a
    /// plain token (no backslash in it at all), so the escape right after it is
    /// unambiguously the end of the field, and everything after the escape must
    /// still be there.
    #[test]
    fn what_followed_the_assignment_in_the_same_string_survives() {
        let original = "{\"d\": \"HOH_ARTIFACT_DIR=plain\\ntail text stays\"}\n";
        serde_json::from_str::<serde_json::Value>(original).expect("the fixture is valid JSON");
        let report = redact_secret_assignments_traced(original);
        assert!(report.changed(), "{report:?}");
        assert!(report.refused.is_none(), "{:?}", report.refused);
        let value: serde_json::Value = serde_json::from_str(&report.redacted).expect("valid JSON");
        let dump = value["d"].as_str().expect("d is a string");
        assert!(
            dump.starts_with("HOH_ARTIFACT_DIR=<redacted>"),
            "the assignment itself must be gone: {dump}"
        );
        // The bytes after the escape are still there — that is the repair.  The
        // closing quote and anything after the string in the document are intact
        // too, which is what `from_str` above has already proved.
        assert!(
            dump.ends_with("\ntail text stays"),
            "everything after the escape must survive: {dump:?}"
        );
        assert_eq!(
            bytes_changed_outside_spans(&report),
            Some(0),
            "the repair must still be a pure splice"
        );
    }

    /// DR-72 ③: when the splice cannot produce valid JSON the original wins and
    /// the refusal is explicit — silence would be the old failure mode.
    #[test]
    fn a_splice_that_would_break_json_is_refused_and_reported() {
        // A physical newline inside a JSON string is already invalid JSON, so
        // the splice would delete the string's tail.  The gate must refuse.
        let broken = "{\n  \"content\": \"line one\nHOH_MODEL_API_KEY=<value>\"\n}\n";
        assert!(
            serde_json::from_str::<serde_json::Value>(broken).is_err(),
            "the fixture is the invalid shape on purpose"
        );
        let report = redact_secret_assignments_traced(broken);
        assert!(
            report.refused.is_some(),
            "the splice must be refused for an already-invalid document"
        );
        assert_eq!(
            report.redacted, broken,
            "a refused splice must leave the text byte-for-byte unchanged"
        );
    }

    /// DR-69: the file-level scan applies both rules, and reports one hit per
    /// changed file.
    #[test]
    fn the_tree_scan_redacts_an_assignment_without_a_known_value() {
        let temp = tempfile::tempdir().unwrap();
        std::fs::write(
            temp.path().join("dump.txt"),
            "export HOH_MODEL_API_KEY=\"$(cat /secret/path/keyval.txt)\";\n",
        )
        .unwrap();
        let hits = redact_tree(temp.path(), &[]).expect("the scan runs without secrets");
        assert_eq!(hits, 1);
        let text = std::fs::read_to_string(temp.path().join("dump.txt")).unwrap();
        assert!(!text.contains("keyval.txt"), "{text}");
    }

    #[test]
    fn redaction_rewrites_only_files_that_contain_a_secret() {
        let temp = tempfile::tempdir().unwrap();
        std::fs::write(temp.path().join("clean.txt"), "nothing to see\n").unwrap();
        std::fs::write(
            temp.path().join("leak.txt"),
            "token=test-key-not-a-secret\n",
        )
        .unwrap();

        let hits = redact_tree(temp.path(), &[String::from("test-key-not-a-secret")]).unwrap();
        assert_eq!(hits, 1);
        assert_eq!(
            std::fs::read_to_string(temp.path().join("clean.txt")).unwrap(),
            "nothing to see\n"
        );
        let leak = std::fs::read_to_string(temp.path().join("leak.txt")).unwrap();
        assert!(leak.contains(REDACTED), "{leak}");
        assert!(!leak.contains("test-key-not-a-secret"), "{leak}");
    }

    /// DR-72 ②: a sealed file keeps every byte; the redacted form is generated
    /// as a **copy**.
    #[test]
    fn a_sealed_file_is_never_rewritten_in_place() {
        let temp = tempfile::tempdir().unwrap();
        let frozen = temp.path().join("candidate");
        std::fs::create_dir_all(&frozen).unwrap();
        let victim = frozen.join("env.json");
        let original = "{\"dump\": \"HOH_ARTIFACT_DIR=C:\\\\tmp\\\\run\\n\"}\n";
        std::fs::write(&victim, original).unwrap();
        std::fs::write(temp.path().join("live.txt"), "HOH_HOH_BIN=C:\\x\\hoh.exe\n").unwrap();

        let sealed = SealedAreas::new([frozen.clone()]);
        let report = redact_tree_traced(temp.path(), &[], &sealed).expect("scan");

        assert_eq!(
            std::fs::read_to_string(&victim).unwrap(),
            original,
            "a sealed file must be byte-identical after the pass"
        );
        let copy = redacted_copy_path(&victim);
        assert!(copy.is_file(), "the generated copy must exist: {copy:?}");
        let copied = std::fs::read_to_string(&copy).unwrap();
        assert!(!copied.contains("C:\\\\tmp\\\\run"), "copy: {copied}");
        assert!(report.copies.contains(&copy), "{report:?}");
        assert!(!report.rewritten.contains(&victim), "{report:?}");
        // The live file is not sealed, so it is rewritten.
        assert!(
            report.rewritten.contains(&temp.path().join("live.txt")),
            "{report:?}"
        );
    }

    /// DR-72 (dispatcher addition 1): a harness variable's value is disclosure
    /// even without a credential, and the rule must catch a path that carries a
    /// user name.
    #[test]
    fn a_harness_value_with_a_user_name_is_redacted() {
        let text = "HOH_ARTIFACT_DIR=F:\\repo\\runs\\smoke-t10\\iter-1\\candidate\\.hoh\n\
                    PATH=C:\\Users\\wyl\\node_modules\\.bin;C:\\Windows\n";
        let report = redact_secret_assignments_traced(text);
        assert!(report.changed(), "the harness assignment must be replaced");
        assert!(
            !report.redacted.contains("wyl"),
            "the user name must not survive: {}",
            report.redacted
        );
    }

    /// DR-73 ③(c) / D280(c): the **carriage-return boundary, pinned**.
    ///
    /// In a plain-text dump a `\r` is a physical line ending, so the assignment
    /// scanner stops there — the terminator is not consumed and whatever follows
    /// on the same physical line survives.  That is the recorded cost DR-72
    /// disclosed and DR-73 was told to **accept and pin, not widen**: if a value
    /// that can survive this boundary ever turns up, the whole fix has to be
    /// redone.  The test therefore fixes the exact boundary, the exact span, and
    /// the exact surviving tail, so a change to the rule has to change this test
    /// on purpose.
    #[test]
    fn a_plain_text_cr_ends_the_value_and_the_carried_rest_is_a_pinned_cost() {
        let text = "HOH_ARTIFACT_DIR=C:\\repo\\runs\\smoke-t10\rTAIL-INVITATION\n";

        let report = redact_secret_assignments_traced(text);
        assert!(
            report.changed(),
            "the assignment must be replaced: {report:?}"
        );
        assert!(report.refused.is_none(), "{:?}", report.refused);

        // The boundary is the physical carriage return, and it is **not**
        // consumed: the scan's span ends exactly on it.
        assert_eq!(report.spans.len(), 1, "{:?}", report.spans);
        let span = &report.spans[0];
        assert_eq!(span.name, "HOH_ARTIFACT_DIR");
        assert_eq!(
            span.end,
            text.find('\r').expect("the fixture carries a CR"),
            "the span must end on the carriage return, not past it"
        );
        assert_eq!(span.replacement, format!("HOH_ARTIFACT_DIR={REDACTED}"));

        // The tail after the CR survives verbatim — the recorded cost.
        assert_eq!(
            report.redacted,
            format!("HOH_ARTIFACT_DIR={REDACTED}\rTAIL-INVITATION\n")
        );
        assert_eq!(
            bytes_changed_outside_spans(&report),
            Some(0),
            "the pin is a pure splice: nothing outside the span may change"
        );
        // The **next line** is still scanned, so the cost cannot be read as
        // "the rest of the dump is unprotected".
        let following = redact_secret_assignments("HOH_ITERATION=1\rHOH_ARTIFACT_DIR=C:\\repo\n");
        assert!(
            !following.contains("C:\\repo"),
            "the line after the CR must still be redacted: {following:?}"
        );
    }

    /// DR-73 ③(c): the same boundary inside a **JSON** string is a `\` + `r`
    /// escape, which is a real escape family and therefore ends the value — the
    /// two shapes must not be confused, because only the plain-text one carries
    /// the "value may survive" cost.
    #[test]
    fn a_json_escaped_carriage_return_ends_the_value_without_a_surviving_tail() {
        let text = "{\"env\":\"HOH_ARTIFACT_DIR=C:\\\\repo\\\\runs\\rtail stays\"}\n";
        serde_json::from_str::<serde_json::Value>(text).expect("the fixture is valid JSON");
        let report = redact_secret_assignments_traced(text);
        assert!(report.refused.is_none(), "{:?}", report.refused);
        let value: serde_json::Value = serde_json::from_str(&report.redacted).expect("valid JSON");
        let dump = value["env"].as_str().expect("env is a string");
        assert!(
            dump.starts_with(&format!("HOH_ARTIFACT_DIR={REDACTED}")),
            "the assignment must be gone: {dump:?}"
        );
        assert!(
            dump.ends_with("tail stays"),
            "the escape and everything after it must survive: {dump:?}"
        );
    }

    #[test]
    fn the_generated_copy_name_keeps_the_extension() {
        assert_eq!(
            redacted_copy_path(Path::new("a/b/env.json")),
            PathBuf::from("a/b/env.redacted.json")
        );
        assert_eq!(
            redacted_copy_path(Path::new("a/b/notes")),
            PathBuf::from("a/b/notes.redacted")
        );
    }

    /// DR-79 ④: the harness's own command line is disclosure even though it is
    /// not a credential.
    ///
    /// `smoke-t13` inherited `DSH_TERM_CMD` into every role shell; a role ran
    /// `env | grep -i hoh`, the whole command line matched (it names the harness
    /// and the staging directory), and it was frozen into
    /// `planner.attempt1.json` / `developer.attempt1.json` and their redacted
    /// sidecars — naming `config/model.secret.env` on the way.  The key's value
    /// never leaked; where it lives did.
    #[test]
    fn a_harness_command_line_does_not_leak_the_secret_file_it_names() {
        let line = "DSH_TERM_CMD=cd /f/moonbit-hof-rs && nohup python \
                    \"F:\\staging\\run_cmd.py\" \"F:\\moonbit-hof-rs\" \
                    config/model.secret.env target/release/hoh.exe run --iterations 1\n\
                    next line stays\n";
        let report = redact_secret_assignments_traced(line);
        assert!(
            report.changed(),
            "the harness command line must be redacted: {report:?}"
        );
        assert!(report.refused.is_none(), "{:?}", report.refused);
        assert!(
            !report.redacted.contains("model.secret.env"),
            "the secret file's name must not survive: {}",
            report.redacted
        );
        assert!(
            !report.redacted.contains("run_cmd.py") && !report.redacted.contains("hoh.exe"),
            "the whole command line is one value: {}",
            report.redacted
        );
        assert_eq!(
            report.redacted,
            format!("DSH_TERM_CMD={REDACTED}\nnext line stays\n"),
            "the physical newline bounds the command line and the next line survives"
        );
        assert_eq!(bytes_changed_outside_spans(&report), Some(0));
    }

    /// DR-81 ③: the repeated-dump plant the acceptance used as its minimal
    /// control.  A `DSH_TERM_CMD=` line early in the text, followed by an
    /// `OPENAI_API_KEY=` line later, used to leave the command line **raw** —
    /// `OPENAI_API_KEY` is scanned before `DSH_TERM_CMD`, and its late span
    /// blocked every earlier candidate of every later-scanned name.  Deleting the
    /// one later line changed the outcome, which is what proved the failure was
    /// positional rather than content-dependent.
    #[test]
    fn a_late_occurrence_of_an_early_scanned_name_does_not_hide_an_earlier_candidate() {
        let with_late = "DSH_TERM_CMD=cd /f/x && python run.py --out x.txt\n\
                         tail\n\
                         filler\n\
                         OPENAI_API_KEY=sk-late\n\
                         more\n";
        let without_late = "DSH_TERM_CMD=cd /f/x && python run.py --out x.txt\n\
                            tail\n\
                            filler\n\
                            more\n";
        for (label, text) in [
            ("with the late OPENAI_API_KEY line", with_late),
            ("without it", without_late),
        ] {
            let report = redact_secret_assignments_traced(text);
            assert!(
                report
                    .redacted
                    .starts_with(&format!("DSH_TERM_CMD={REDACTED}\n")),
                "the command line must be redacted {label}: {:?}",
                report.redacted
            );
            assert!(
                !report.redacted.contains("run.py"),
                "the command line's value must be gone {label}: {:?}",
                report.redacted
            );
            assert_eq!(bytes_changed_outside_spans(&report), Some(0), "{label}");
        }
    }

    /// DR-81 ③: a candidate that **contains** a recorded span absorbs it.  The
    /// `HOH_ROLE=` assignment is scanned before `DSH_TERM_CMD` (it is earlier in
    /// `HARNESS_ENV_VARS`), so the recorded span covers only the middle of the
    /// command line; if the wider candidate were skipped, the command line's head
    /// and tail would survive raw.
    #[test]
    fn a_command_line_containing_an_assignment_absorbs_it() {
        let text = "DSH_TERM_CMD=cd /f/x && HOH_ROLE=developer run.py --out x.txt\nnext stays\n";
        let report = redact_secret_assignments_traced(text);
        assert!(
            !report.redacted.contains("developer") && !report.redacted.contains("run.py"),
            "the whole command line must be one value: {:?}",
            report.redacted
        );
        assert_eq!(
            report.redacted,
            format!("DSH_TERM_CMD={REDACTED}\nnext stays\n"),
            "the absorbed span must not leave a raw tail"
        );
        assert_eq!(bytes_changed_outside_spans(&report), Some(0));
        assert_eq!(
            report.spans.len(),
            1,
            "the absorbed span is replaced by the wider candidate: {:?}",
            report.spans
        );
    }

    /// DR-79 ④: the shape that actually reached the artifacts — a JSON string
    /// whose command line carries escaped quotes and doubled backslashes and ends
    /// at the `\n` escape of the dump line.  The generic escape rule reads the
    /// `\"` of a quoted argument as the end of the value, so the command-line
    /// rule needs its own terminator; the value must still be a **pure splice**
    /// and the surrounding JSON must still parse.
    #[test]
    fn the_real_json_command_line_shape_redacts_the_whole_value() {
        let original = serde_json::to_string(&serde_json::json!({
            "content": "<output>\n\
                        DSH_TERM_CMD=cd /f/moonbit-hof-rs && nohup python \"F:\\staging\\run_cmd.py\" \"F:\\moonbit-hof-rs\" config/model.secret.env target/release/hoh.exe run --iterations 1\n\
                        </output>"
        }))
        .unwrap();
        serde_json::from_str::<serde_json::Value>(&original).expect("the fixture is valid JSON");
        let report = redact_secret_assignments_traced(&original);
        assert!(report.changed(), "{report:?}");
        assert!(
            report.refused.is_none(),
            "the bounded value must not be refused: {:?}",
            report.refused
        );
        let value: serde_json::Value =
            serde_json::from_str(&report.redacted).expect("the splice stays valid JSON");
        let dump = value["content"].as_str().expect("content");
        assert!(
            dump.starts_with(&format!("<output>\nDSH_TERM_CMD={REDACTED}")),
            "the assignment must be replaced: {dump:?}"
        );
        assert!(
            !dump.contains("model.secret.env") && !dump.contains("run_cmd.py"),
            "no part of the command line may survive: {dump:?}"
        );
        assert!(
            dump.ends_with("\n</output>"),
            "everything after the logical line must survive: {dump:?}"
        );
        assert_eq!(bytes_changed_outside_spans(&report), Some(0));
    }
}
