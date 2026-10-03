//! DR-86 ①: **is the text a role delivered a whole document, or a fragment?**
//!
//! `smoke-t16`'s round of record produced a 20-byte `scenes/main.tscn` whose
//! content is `visible = false)  \r\n`, and a `scripts/main.gd` carrying five
//! literal `\$` sequences.  Both were written by a POSIX command line handed to
//! `cmd.exe`: a parenthesised command group whose `)` sat inside the coordinates
//! `Vector2(4000, 40)` closed the group before the redirect, so the redirect
//! captured only the tail of the line, and the shell's backslash-escaping
//! survived into a language in which `\$` is not a valid escape.
//!
//! **The class, not the file.**  The check here never looks for the twenty bytes
//! of that scene or the identifier `main.tscn`.  It asks two questions that any
//! truncating shell construction must answer badly, for *any* delivered file of
//! an audited format:
//!
//! 1. **Is the whole document there?**  A Godot text resource (`.tscn`/`.tres`)
//!    is a sequence of bracketed sections.  A file with no `[section ...]`
//!    header cannot be a document a writer meant to deliver — only the surviving
//!    tail of one — and a file whose brackets/parentheses/braces do not balance
//!    (outside quoted spans and the reader's own line comment) was cut, or
//!    overwritten by a fragment that carries the closer of the construct that cut
//!    it.  That is exactly the `)` of the shell group in `visible = false)  `.
//! 2. **Is the text written in the language it claims?**  A GDScript line
//!    containing `\` followed by a character that is not a GDScript escape is
//!    not something a writer of GDScript emits; it is the residue of an escape
//!    another shell had already consumed (or failed to consume).  The table of
//!    legal escapes below is the whole rule — the needle is the *class*
//!    "illegal escape", computed from the language's own escape alphabet.
//!
//!    **A comment is not executable content**, so it is not scanned for this
//!    class.  GDScript's grammar discards a comment at the lexer, exactly as it
//!    discards whitespace: the text in one cannot be a parse error and cannot
//!    carry a foreign escape *into the program*.  A Windows path written in a
//!    comment (`# see C:\Users\dev\project`) is therefore legitimate text, and
//!    treating its `\U` as shell residue would refuse a whole project that has
//!    no defect at all — the one failure mode a gate check must never have.
//!    "Where a comment starts" is decided by the same scanner that blanks string
//!    literals ([`scan_line`]), so it has exactly one implementation — but **which
//!    character starts one is the reader's rule, per extension**, never one global
//!    guess (see [`line_comment`]).  This engine build has two readers over the
//!    audited set:
//!
//!    * `.gd` is read by `GDScriptTokenizer`, whose comment is `#` alone
//!      (`case '#'`, `modules/gdscript/gdscript_tokenizer.cpp`), and whose `;` is a
//!      **`SEMICOLON`** token (`";", // SEMICOLON` in its own token list) — a
//!      statement separator, i.e. executable content.  A `;` therefore opens no
//!      comment in a script: what follows it is code again, and a literal it opens
//!      is still judged.
//!    * `.tscn`/`.tres` are read by `VariantParser` (`scene/resources/
//!      resource_format_text.cpp` calls `VariantParser::parse_tag` /
//!      `parse_tag_assign_eof`), and **its** line comment is `;`: `get_token`'s
//!      `case ';'` reads to the end of the line (`core/variant/variant_parser.cpp`),
//!      and `parse_tag_assign_eof` repeats it.  A scene or resource whose `;`
//!      comment holds an apostrophe, a lone quote or an unmatched parenthesis is a
//!      document the reader accepts, so both whole-document rules must skip that
//!      comment — reading it as code reddens a project with no defect.
//!    * In a resource `#` is **not** a comment: the same `get_token` answers
//!      `case '#'` with a **colour** token (it consumes hexadecimal digits after
//!      the `#`), and the writer never emits one outside a string —
//!      `VariantWriter::write` serialises a `Color` as `Color(r, g, b, a)`, never
//!      as `#rrggbb`.  Modelling `#` as a resource comment would be a false
//!      premise in the **permissive** direction, so it is not modelled.
//!
//!    A quoted *string* is deliberately **not** skipped.  A string is real
//!    executable content: GDScript **does** process escapes inside a non-raw
//!    literal — the tokenizer's `switch (code)` accepts `a b f n r t v ' " \`
//!    and the `\u`/`\U` forms, and answers `Invalid escape in string.` for
//!    everything else — so a foreign escape **can** sit inside a string, and
//!    exempting strings would blind this rule to that class.  That is the whole
//!    reason; an earlier revision of this comment gave a different one and it was
//!    **false**, so it is corrected here rather than repeated.  The round of
//!    record's `\$` residues did **not** land inside string literals: they are
//!    five unquoted expressions on lines 8–12 of `scripts/main.gd`
//!    (`@onready var coins_label: Label = \$HUD/Coins` and four siblings), and no
//!    quote character sits on any of those lines (frozen copy
//!    `runs/smoke-t16/iter-1/candidate/scripts/main.gd`), so a rule that skipped
//!    string literals would still have caught all five.  The residue class that
//!    has to be reachable *inside* a literal is the one the tokenizer's own
//!    escape processing creates (`"#\q"`, `"a\q\"`, `'#\q'`, …), not those bytes.
//!
//!    The earlier claim that a GDScript string "must close on its own line" is
//!    **false** in the other direction too — our engine build's tokenizer scans a
//!    string past a newline, a `\` directly before a newline is an explicit
//!    continuation, and triple-quoted literals span lines by definition
//!    (`modules/gdscript/gdscript_tokenizer.cpp`, `GDScriptTokenizer::string()`).
//!    The scanner therefore carries the open literal from line to line instead
//!    of assuming one line is one literal.  Because a carried literal would
//!    otherwise silence the rest of the file, a literal still open at the end of
//!    the text is itself reported as a fragment (see [`unterminated_literal`]):
//!    both readers refuse such a document outright, so it cannot be a whole one.
//!
//!    A **raw** string (`r"..."`, `r'''...'''`) is the one literal that
//!    processes no escapes at all — the tokenizer takes a backslash in one as a
//!    literal character — so a Windows path inside a raw string is legitimate
//!    text too and is not scanned for this class either.  That is the language's
//!    rule, not an exception for paths.
//!
//! The audit is deliberately conservative: it only looks at the artifact
//! extensions whose grammar mandates a whole document, and it reports a
//! *finding* rather than editing anything.  Nothing here rewrites, repairs or
//! deletes a delivered byte — the caller decides, and a real project defect must
//! still reach the artifact gate (E2 is never relaxed).

use std::path::Path;

use walkdir::WalkDir;

use crate::runtime::policy::is_excluded;

/// The extensions whose grammar requires a whole document.  Everything else
/// (`.md`, `.json`, `.txt`, a screenshot, …) is out of scope: a fragment of a
/// JSON document is a different, already-checked failure class.
pub const AUDITED_EXTENSIONS: &[&str] = &["tscn", "tres", "gd"];

/// The character that opens a **line comment** for one audited extension, or
/// `None` when the extension's reader has no line comment at all.
///
/// This is the reader's own rule, taken from the engine source, and it is
/// deliberately per extension rather than one global guess:
///
/// * `.gd` → `#`.  `GDScriptTokenizer`'s comment case is `case '#'`
///   (`modules/gdscript/gdscript_tokenizer.cpp`, `GDScriptTokenizerText::
///   _skip_whitespace`), and its token list has a distinct `SEMICOLON` entry for
///   `";"`, so a `;` is a statement separator and not a comment.
/// * `.tscn`/`.tres` → `;`.  `VariantParser::get_token`'s `case ';'` discards the
///   rest of the line, and `VariantParser::parse_tag_assign_eof` does the same
///   (`core/variant/variant_parser.cpp`); both readers of a text resource go
///   through them (`scene/resources/resource_format_text.cpp`,
///   `VariantParser::parse_tag` / `parse_tag_assign_eof`).
///
/// A resource has no `#` comment: in the same `get_token`, `case '#'` builds a
/// **colour** token.  Treating `#` as a resource comment would be a false premise
/// in the permissive direction, so it is not modelled here.
fn line_comment(extension: &str) -> Option<char> {
    match extension {
        "gd" => Some('#'),
        "tscn" | "tres" => Some(';'),
        _ => None,
    }
}

/// The characters a GDScript `\` may legally precede **inside a non-raw string**.
///
/// The list is the escape alphabet of this repository's own engine build
/// (`modules/gdscript/gdscript_tokenizer.cpp`, the `switch (code)` in
/// `GDScriptTokenizer::string()`): `a b f n r t v ' " \` are the single-character
/// escapes.  `u` and `U` are not listed because they consume exactly four and
/// six hexadecimal digits respectively and are checked by
/// [`unicode_escape_digits`]; a backslash directly before a newline is not
/// listed either because its validity depends on where it sits (it continues a
/// string, and it is the statement continuation in code).
///
/// `/` and the digits `0..=7` are deliberately **absent**: the tokenizer's
/// `default:` branch answers `Invalid escape in string.` for both, so a script
/// that uses them is not GDScript either.
///
/// `'\\r'` here is the **character** carriage return, not the letter `r` (which
/// is listed too).  The tokenizer has a `case '\r':` that accepts a backslash
/// followed by a lone CR — when the next character is not a newline it adds the
/// character and keeps the escape valid — so refusing that shape would refuse
/// text the engine build accepts (`modules/gdscript/gdscript_tokenizer.cpp`,
/// `GDScriptTokenizer::string()`).
const GDSCRIPT_ESCAPES: &[char] = &['a', 'b', 'f', 'n', 'r', 't', 'v', '\'', '"', '\\', '\r'];

/// How many hexadecimal digits `\u` / `\U` must be followed by.
fn unicode_escape_digits(escape: char) -> Option<usize> {
    match escape {
        'u' => Some(4),
        'U' => Some(6),
        _ => None,
    }
}

/// One string literal that is still open at the end of the line that opened it.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
struct OpenString {
    quote: char,
    triple: bool,
    raw: bool,
}

/// The lexer state one line hands to the next.
///
/// A string literal is **not** required to close on its own line: this engine's
/// tokenizer keeps scanning a literal past a newline, `\` directly before a
/// newline is an explicit continuation, and a triple-quoted literal spans lines
/// by definition.  Carrying the open literal across lines is what the language
/// does — and it is what lets the rule tell a `#` **inside** a continued string
/// from one that really opens a comment.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
struct LexerState {
    open: Option<OpenString>,
    /// 1-based line on which `open` was opened; only meaningful while it is
    /// `Some`, and it is what makes an unterminated literal reportable at all.
    opened_line: usize,
}

/// What one line looks like to the two rules that consume it.
struct LineScan {
    /// The line with every string literal and comment character blanked to a
    /// space, so a delimiter or a backslash inside one is never counted as code.
    /// Same character count as the input, so line and column stay aligned.
    code: String,
    /// The first escape the language cannot have produced: its column, and the
    /// ASCII-safe rendering of the two characters.
    invalid_escape: Option<(usize, String)>,
}

/// Record the first invalid escape of a line; later ones add nothing.
fn note_invalid(invalid: &mut Option<(usize, String)>, column: usize, escape: char) {
    if invalid.is_none() {
        *invalid = Some((column, format!("\\{}", escape.escape_default())));
    }
}

/// How many of the `count` characters starting at `start` are hexadecimal digits?
///
/// The tokenizer consumes each valid digit and, on the first character that is
/// **not** one, pushes `Invalid hexadecimal digit in unicode escape sequence.`
/// and stops **without advancing** past it — so the caller must leave that
/// character to the outer scan (it is what still lets a closing quote close the
/// literal on the same line).
fn hex_digit_run(chars: &[char], start: usize, count: usize) -> usize {
    (0..count)
        .take_while(|offset| {
            chars
                .get(start + offset)
                .is_some_and(|ch| ch.is_ascii_hexdigit())
        })
        .count()
}

/// Is the quote at `quote_at` the opening quote of a **raw** string literal?
///
/// The tokenizer takes `r` as the raw marker only when the `r` begins a token
/// (`c == 'r' && (_peek() == '"' || _peek() == '\'')`), so an `r` that is the
/// tail of an identifier (`for`, `bar`) does not make the literal raw.
fn has_raw_prefix(chars: &[char], quote_at: usize) -> bool {
    if quote_at == 0 || chars[quote_at - 1] != 'r' {
        return false;
    }
    if quote_at < 2 {
        return true;
    }
    let before = chars[quote_at - 2];
    !(before == '_' || before.is_alphanumeric())
}

/// Scan one line, consuming and updating the carried string state.
///
/// The scan is character-by-character because only a real lexer can tell a
/// comment marker from the same character inside a quoted string: the tokenizer
/// scans a string literal as a unit, so a marker inside one opens no comment,
/// while a marker outside one discards the rest of the line.
///
/// `comment` is the marker **this file's reader** uses (see [`line_comment`]):
/// `#` for a `.gd`, `;` for a `.tscn`/`.tres`.  Passing the extension's own rule
/// in is what keeps a `;` from silencing a script and a `#` from silencing a
/// resource.
///
/// `line_number` is 1-based and is recorded on the state when a literal opens, so
/// a literal left open at the end of the text can name its own opening line.
fn scan_line(
    line: &str,
    line_number: usize,
    comment: Option<char>,
    state: &mut LexerState,
) -> LineScan {
    let chars: Vec<char> = line.chars().collect();
    let count = chars.len();
    let mut code = vec![' '; count];
    let mut invalid: Option<(usize, String)> = None;
    let mut index = 0usize;

    while index < count {
        if let Some(open) = state.open {
            let ch = chars[index];
            if open.triple
                && ch == open.quote
                && index + 2 < count
                && chars[index + 1] == open.quote
                && chars[index + 2] == open.quote
            {
                // `"""` / `'''` closes the triple-quoted literal.
                state.open = None;
                index += 3;
                continue;
            }
            if !open.triple && ch == open.quote {
                state.open = None;
                index += 1;
                continue;
            }
            if ch == '\\' {
                if index + 1 >= count {
                    // `\` directly before the end of the line continues the
                    // literal on the next line; the state therefore stays open.
                    index = count;
                    continue;
                }
                if open.raw {
                    // A raw literal processes no escapes: the backslash and the
                    // character after it are both content.
                    index += 2;
                    continue;
                }
                let next = chars[index + 1];
                match unicode_escape_digits(next) {
                    Some(digits) => {
                        let available = hex_digit_run(&chars, index + 2, digits);
                        if available < digits {
                            note_invalid(&mut invalid, index, next);
                        }
                        index += 2 + available;
                    }
                    None => {
                        if !GDSCRIPT_ESCAPES.contains(&next) {
                            note_invalid(&mut invalid, index, next);
                        }
                        index += 2;
                    }
                }
                continue;
            }
            index += 1;
            continue;
        }

        let ch = chars[index];
        if Some(ch) == comment {
            // The reader discards the rest of the line: it is not code.
            index = count;
            continue;
        }
        if ch == '"' || ch == '\'' {
            let raw = has_raw_prefix(&chars, index);
            let triple = index + 2 < count && chars[index + 1] == ch && chars[index + 2] == ch;
            state.open = Some(OpenString {
                quote: ch,
                triple,
                raw,
            });
            state.opened_line = line_number;
            index += if triple { 3 } else { 1 };
            continue;
        }
        if ch == '\\' {
            // In code the tokenizer accepts a backslash only as a line
            // continuation: `\` must be the line's last character.  Anything
            // else is `Expected new line after "\\"` — including a backslash
            // whose very next character is the `#` that opens a comment, which
            // is therefore residue and not a comment marker.
            if index + 1 < count {
                note_invalid(&mut invalid, index, chars[index + 1]);
            }
            index += 2;
            continue;
        }
        code[index] = ch;
        index += 1;
    }

    LineScan {
        code: code.into_iter().collect(),
        invalid_escape: invalid,
    }
}

/// The first place the file's `()[]{}` depth leaves zero, if any.
///
/// Returns `(line, character, depth)` where `depth` is negative for an extra
/// closer (the truncation signature of a shell command group) and the final
/// depth at end of file when it never went negative.
///
/// `comment` is the reader's own line-comment marker for this extension (see
/// [`line_comment`]), so a delimiter inside a `.tscn`'s `;` comment is not
/// counted as code — the class the DR-88 acceptance measured as a false red.
fn unbalanced_delimiter(text: &str, comment: Option<char>) -> Option<(usize, char, i64)> {
    let mut depth: i64 = 0;
    let mut last_line = 1usize;
    let mut state = LexerState::default();
    for (index, raw) in text.lines().enumerate() {
        let line = index + 1;
        last_line = line;
        for ch in scan_line(raw, line, comment, &mut state).code.chars() {
            match ch {
                '(' | '[' | '{' => depth += 1,
                ')' | ']' | '}' => {
                    depth -= 1;
                    if depth < 0 {
                        return Some((line, ch, depth));
                    }
                }
                _ => {}
            }
        }
    }
    if depth != 0 {
        return Some((last_line, ' ', depth));
    }
    None
}

/// The first `\` followed by a character GDScript cannot escape, in code only.
///
/// Only the part of each line that is not a comment is scanned (see
/// [`scan_line`] and [`line_comment`]): a comment is discarded by the language's
/// lexer, so no escape inside one can reach the program.  Strings are scanned —
/// they are content — except for raw literals, which process no escapes at all.
fn first_invalid_escape(text: &str, comment: Option<char>) -> Option<(usize, String)> {
    let mut state = LexerState::default();
    for (index, raw) in text.lines().enumerate() {
        if let Some((_, escape)) = scan_line(raw, index + 1, comment, &mut state).invalid_escape {
            return Some((index + 1, escape));
        }
    }
    None
}

/// The literal this text still has open at its end, if any: the line it was
/// opened on and the literal itself.
///
/// This is the reading that keeps a carried literal from **masking** the rest of
/// the file.  A document whose last line leaves a literal open cannot be a whole
/// document at all, because both readers of the two audited languages refuse it
/// outright:
///
/// * `GDScriptTokenizer::string()` answers `Unterminated string.` when it reaches
///   the end of its input with the literal still open — including after the
///   `\`-at-end-of-line continuation (`modules/gdscript/gdscript_tokenizer.cpp`);
/// * the text-resource reader answers `Unterminated string` when the character it
///   reads is the stream's terminator (`core/variant/variant_parser.cpp`, the
///   `'\"'` branch, `if (ch == 0)`), and its `\u`/`\U` loop answers the same at
///   `:322-326`.
///
/// So an unterminated literal is not a local blemish hidden inside a string: it
/// is the surviving **prefix** of a longer write, which is the class this whole
/// module exists to catch.  It is deliberately reported from the carried scan
/// (the same one the other rules use) rather than from a second, per-line
/// delimiter scan: a per-line scan would have to assume that a resource string
/// closes on its own line, and the reader above accepts a newline inside one, so
/// that assumption would manufacture a false red on a legitimate multi-line
/// string holding a `)` — the exact failure mode this check must never have.
///
/// `comment` is the reader's own marker (see [`line_comment`]), so a quote inside
/// a `.tscn`'s `;` comment opens nothing: the comment is discarded exactly as the
/// reader discards it.
fn unterminated_literal(text: &str, comment: Option<char>) -> Option<(usize, OpenString)> {
    let mut state = LexerState::default();
    for (index, raw) in text.lines().enumerate() {
        scan_line(raw, index + 1, comment, &mut state);
    }
    state.open.map(|open| (state.opened_line, open))
}

/// What is wrong with a delivered text file.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum IntegrityKind {
    /// The file is a fragment: no document opener, or unbalanced delimiters.
    TruncatedFragment,
    /// The file carries an escape the target language does not have.
    ShellEscapeResidue,
}

impl IntegrityKind {
    /// The stable warning token (also the prefix of the finding line).
    pub fn token(self) -> &'static str {
        match self {
            IntegrityKind::TruncatedFragment => "artifact_write_truncated",
            IntegrityKind::ShellEscapeResidue => "artifact_shell_residue",
        }
    }
}

/// One reason a delivered file cannot be a whole document.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct IntegrityFinding {
    /// POSIX relative path inside the audited tree.
    pub path: String,
    pub kind: IntegrityKind,
    /// 1-based line the finding was taken from.
    pub line: usize,
    /// The verbatim, ASCII-safe reason.
    pub detail: String,
}

impl IntegrityFinding {
    /// The one-line form handed to a role, a warning and the gate.
    pub fn render(&self) -> String {
        format!(
            "{}:{}: {}: {}",
            self.path,
            self.line,
            self.kind.token(),
            self.detail
        )
    }
}

/// The extension of a POSIX relative path, lowercased.
fn extension_of(path: &str) -> String {
    path.rsplit('.').next().unwrap_or("").to_ascii_lowercase()
}

/// Audit one delivered text file by its relative path and content.
pub fn audit_text(path: &str, text: &str) -> Vec<IntegrityFinding> {
    let extension = extension_of(path);
    if !AUDITED_EXTENSIONS.contains(&extension.as_str()) {
        return Vec::new();
    }
    // The reader's own comment rule for **this** extension.  Both rules below are
    // handed the same marker, so they cannot disagree about where a comment starts.
    let comment = line_comment(&extension);
    let mut findings = Vec::new();

    // The whole-document question comes first and is asked of every audited
    // format: a text that ends inside a literal is not a document either reader
    // accepts, so no later rule may be allowed to read it as one.
    if let Some((line, open)) = unterminated_literal(text, comment) {
        let quote = match (open.triple, open.quote) {
            (true, '"') => "\"\"\"",
            (true, _) => "'''",
            (false, '"') => "\"",
            (false, _) => "'",
        };
        findings.push(IntegrityFinding {
            path: path.to_string(),
            kind: IntegrityKind::TruncatedFragment,
            line,
            detail: format!(
                "the text ends with the {quote} literal opened on this line still open: a whole \
                 document closes every literal it opens — the GDScript tokenizer answers \
                 `Unterminated string.` at the end of its input and the text-resource reader \
                 answers `Unterminated string` for the stream terminator — so this is the \
                 surviving prefix of a longer write, not a document a writer delivered"
            ),
        });
    }

    if extension == "tscn" || extension == "tres" {
        let has_section = text.lines().any(|raw| {
            let trimmed = raw.trim();
            trimmed.starts_with('[') && trimmed[1..].contains(']')
        });
        if !has_section {
            findings.push(IntegrityFinding {
                path: path.to_string(),
                kind: IntegrityKind::TruncatedFragment,
                line: 1,
                detail: "the delivered text carries no `[section ...]` header, so it cannot be a \
                         whole Godot text resource: a `.tscn`/`.tres` document always opens with \
                         one, and text without one is the surviving fragment of a longer write"
                    .to_string(),
            });
        }
        if let Some((line, ch, depth)) = unbalanced_delimiter(text, comment) {
            findings.push(IntegrityFinding {
                path: path.to_string(),
                kind: IntegrityKind::TruncatedFragment,
                line,
                detail: format!(
                    "the file's `()[]{{}}` depth is {depth} at this point (offending character \
                     `{ch}`): a whole document balances its delimiters, so an unbalanced closer \
                     is the tail of a write that was cut before its opener (a shell command \
                     group closed by a `)` inside the content does exactly this)"
                ),
            });
        }
        // The escape rule is a **GDScript** rule and is deliberately not applied
        // to a text resource: the resource reader takes a backslash followed by
        // any character literally (`core/variant/variant_parser.cpp`, the
        // `default:` branch of its escape `switch`), so a scene string has no
        // "foreign escape" class.  Only the whole-document rules apply here.
    }

    if extension == "gd" {
        if let Some((line, escape)) = first_invalid_escape(text, comment) {
            findings.push(IntegrityFinding {
                path: path.to_string(),
                kind: IntegrityKind::ShellEscapeResidue,
                line,
                detail: format!(
                    "the text carries the escape `{escape}`, which GDScript does not define: the \
                     backslash is the residue of another shell's escaping rather than content a \
                     GDScript writer emits (legal escapes are \
                     `\\n \\t \\r \\a \\b \\f \\v \\' \\\" \\\\`, the unicode forms \
                     `\\uXXXX` and `\\UXXXXXX` with their full digit count, and a backslash at \
                     the very end of a line)"
                ),
            });
        }
    }

    findings
}

/// Audit every delivered text file under `root`, in sorted path order.
///
/// The walk uses the runtime's own exclusion rule, so `.hoh/**`, `.git/**` and
/// the adapter's caches — none of which are the delivered product — are never
/// audited.
pub fn audit_tree(root: &Path, excludes: &[String]) -> anyhow::Result<Vec<IntegrityFinding>> {
    let mut findings = Vec::new();
    if !root.exists() {
        return Ok(findings);
    }
    for entry in WalkDir::new(root).follow_links(false) {
        let entry = entry?;
        if !entry.file_type().is_file() {
            continue;
        }
        let relative = entry
            .path()
            .strip_prefix(root)
            .unwrap_or(entry.path())
            .components()
            .map(|component| component.as_os_str().to_string_lossy().into_owned())
            .collect::<Vec<_>>()
            .join("/");
        if relative.is_empty() || is_excluded(&relative, excludes) {
            continue;
        }
        let Ok(text) = std::fs::read_to_string(entry.path()) else {
            continue;
        };
        findings.extend(audit_text(&relative, &text));
    }
    findings.sort_by(|a, b| {
        (a.path.as_str(), a.line, a.kind.token()).cmp(&(b.path.as_str(), b.line, b.kind.token()))
    });
    Ok(findings)
}

#[cfg(test)]
mod tests {
    use super::*;

    /// The class this check exists for: a scene whose content is the tail of a
    /// line that a parenthesised shell group cut.  The fixture is deliberately
    /// *not* the round's own bytes — a different fragment of the same shape must
    /// be caught too, or the check pins one file instead of one class.
    #[test]
    fn a_fragment_of_a_line_is_not_a_scene_document() {
        let findings = audit_text("scenes/level.tscn", "name = 12, y)  \r\n");
        assert!(
            findings
                .iter()
                .any(|finding| finding.kind == IntegrityKind::TruncatedFragment),
            "{findings:?}"
        );
        assert_eq!(findings[0].kind.token(), "artifact_write_truncated");
    }

    /// A whole scene — header, node, resource reference, a quoted string
    /// containing a parenthesis — is accepted, so the check is not a blanket
    /// refusal of `.tscn`.
    #[test]
    fn a_whole_scene_document_is_accepted() {
        let scene = "[gd_scene load_steps=2 format=3]\n\n\
                     [ext_resource type=\"Script\" path=\"res://scripts/player.gd\" id=\"1\"]\n\n\
                     [node name=\"Main\" type=\"Node2D\"]\n\
                     label = \"Coins: 0 (x)\"\n\
                     script = ExtResource(\"1\")\n";
        assert_eq!(audit_text("scenes/main.tscn", scene), Vec::new());
    }

    /// A scene cut before its closers is a fragment in the other direction: the
    /// opener survives, so this is not the header rule — it is the balance rule.
    #[test]
    fn a_scene_cut_before_its_closing_brackets_is_a_fragment() {
        let findings = audit_text(
            "scenes/main.tscn",
            "[gd_scene format=3]\n[node name=\"Main\"\n",
        );
        assert!(
            findings
                .iter()
                .any(|finding| finding.kind == IntegrityKind::TruncatedFragment),
            "{findings:?}"
        );
    }

    /// The second class of the same failure: an escape another shell consumed.
    /// Again the needle is the class — `\n` and `\t` stay legal.
    #[test]
    fn a_foreign_shell_escape_is_residue_and_a_legal_escape_is_not() {
        let residue = audit_text("scripts/player.gd", "var label = \\$HUD/Coins\n");
        assert_eq!(residue.len(), 1, "{residue:?}");
        assert_eq!(residue[0].kind, IntegrityKind::ShellEscapeResidue);
        assert_eq!(residue[0].kind.token(), "artifact_shell_residue");
        assert_eq!(residue[0].line, 1);

        let legal = "extends Node\n\nfunc _ready() -> void:\n\tprint(\"a\\tb\")\n";
        assert_eq!(audit_text("scripts/player.gd", legal), Vec::new());
    }

    /// A delimiter inside a string literal or a comment is not code.
    ///
    /// DR-90 ①: the comment marker here is `;`, because that is the marker the
    /// **text-resource reader** uses (`core/variant/variant_parser.cpp`,
    /// `VariantParser::get_token`'s `case ';'`).  The fixture said `#` before
    /// DR-90; `#` is not a comment in a resource at all — the same function reads
    /// it as a colour token — so the old fixture was asserting a false premise.
    #[test]
    fn delimiters_inside_literals_and_comments_are_not_counted() {
        let scene = "[gd_scene format=3]\n\n[node name=\"Main\" type=\"Node2D\"]\n\
                     text = \"unbalanced ) here\"\n; a comment with ]\n";
        assert_eq!(audit_text("scenes/main.tscn", scene), Vec::new());
    }

    /// DR-87 ①: **a comment is not executable content**, so a Windows path in
    /// one is legitimate text and must not be read as shell residue.
    ///
    /// The whole file is a complete, valid GDScript document: refusing it would
    /// close the gate on a project with no defect.  The comment carries several
    /// foreign escapes at once (`\U`, `\t`, `\g`), and a quoted string carries a
    /// legal one (`\n`), so the rule is "skip the comment", not "skip this one
    /// string".  A trailing comment after real code and a comment whose `#`
    /// follows a string are both exercised.
    #[test]
    fn a_windows_path_in_a_comment_is_not_a_foreign_escape() {
        let script = "# see C:\\Users\\dev\\project for the layout\n\
                      extends Node\n\n\
                      # D:\\tools\\godot\\bin\n\
                      func _ready() -> void:\n\
                      \tprint(\"ready\\n\")  # C:\\tmp\\log.txt\n";
        assert_eq!(audit_text("scripts/notes.gd", script), Vec::new());
    }

    /// The converse of [`Self::a_windows_path_in_a_comment_is_not_a_foreign_escape`]:
    /// a foreign escape **in executable code** is still caught, so skipping
    /// comments did not turn the rule off.
    ///
    /// The residue lands in four positions of a real program — a top-level
    /// statement, inside a quoted string, before a trailing comment, and behind a
    /// `#` that a string opened — and each is a finding in its own right.
    #[test]
    fn a_foreign_escape_in_code_is_still_caught() {
        let statement = audit_text("scripts/level.gd", "var path = \\Users\\dev\n");
        assert_eq!(statement.len(), 1, "{statement:?}");
        assert_eq!(statement[0].kind, IntegrityKind::ShellEscapeResidue);
        assert_eq!(statement[0].line, 1);

        // A residue **inside** a literal is still caught: that class is the
        // reason strings are scanned (the corrected justification rests on it,
        // not on the round of record's bytes, which are unquoted code).
        let in_string = audit_text("scripts/main.gd", "var label = \"\\$HUD/Coins\"\n");
        assert_eq!(in_string.len(), 1, "{in_string:?}");
        assert_eq!(in_string[0].kind, IntegrityKind::ShellEscapeResidue);

        // Code before a comment is still code: `\z` is not an escape, so it is
        // residue even though a `#` later on the same line opens a comment.
        let before_a_comment = audit_text("scripts/notes.gd", "var tag = \\z # a comment\n");
        assert_eq!(before_a_comment.len(), 1, "{before_a_comment:?}");
        assert_eq!(before_a_comment[0].line, 1);

        // A string's `#` opens no comment, so the residue behind it is seen.
        let hash_in_a_string = audit_text("scripts/notes.gd", "var url = \"#x\" + \\y \n");
        assert_eq!(hash_in_a_string.len(), 1, "{hash_in_a_string:?}");
    }

    /// Formats outside the audited set are never judged: a fragment of a `.md`
    /// or a `.json` is a different failure class with its own gates.
    #[test]
    fn only_the_audited_extensions_are_looked_at() {
        assert_eq!(audit_text("notes.md", "visible = false)  \n"), Vec::new());
        assert_eq!(audit_text("data.json", "{\n"), Vec::new());
        assert_eq!(audit_text("scripts/player.gd.txt", "\\$x\n"), Vec::new());
    }

    /// DR-88 ①: a **raw** string literal processes no escapes at all, so a path
    /// with backslashes inside one is legitimate GDScript and must not be
    /// refused.  The rule is the language's own (`GDScriptTokenizer::string()`:
    /// for an `r`-prefixed literal a backslash is a literal character), not an
    /// exception carved out for this one path.
    #[test]
    fn a_raw_string_processes_no_escapes() {
        let windows_path = audit_text(
            "scripts/paths.gd",
            "extends Node\n\nvar p = r\"C:\\Users\\dev\\project\"\n",
        );
        assert_eq!(windows_path, Vec::new(), "{windows_path:?}");

        let raw_triple = audit_text(
            "scripts/regex.gd",
            "var re = r\"\"\"\\d+ \\U0001F600 # not a comment\nsecond line\"\"\"\n",
        );
        assert_eq!(raw_triple, Vec::new(), "{raw_triple:?}");

        // The converse: the same bytes **outside** a raw literal are still
        // residue, so recognising raw literals did not switch the rule off.
        let converse = audit_text("scripts/paths.gd", "var p = \"C:\\Users\\dev\\project\"\n");
        assert_eq!(converse.len(), 1, "{converse:?}");
        assert_eq!(converse[0].kind, IntegrityKind::ShellEscapeResidue);

        // An identifier that merely ends in `r` is not a raw-string marker.
        let not_raw = audit_text("scripts/notes.gd", "var cur = \"C:\\Users\\dev\"\n");
        assert_eq!(not_raw.len(), 1, "{not_raw:?}");
    }

    /// DR-88 ①: the escape table is the language's own, and the language defines
    /// `\UXXXXXX` as well as `\uXXXX`.  The unicode forms must also be
    /// **complete**: a `\u`/`\U` without its full run of hexadecimal digits is
    /// the malformed shape the tokenizer answers with
    /// `Invalid hexadecimal digit in unicode escape sequence`.
    #[test]
    fn the_escape_table_is_the_languages_own() {
        assert_eq!(
            audit_text("scripts/emoji.gd", "var e = \"\\U0001F600\"\n"),
            Vec::new()
        );
        assert_eq!(
            audit_text("scripts/emoji.gd", "var e = \"\\u0041\"\n"),
            Vec::new()
        );

        let short_upper = audit_text("scripts/emoji.gd", "var e = \"\\U0001F\"\n");
        assert_eq!(short_upper.len(), 1, "{short_upper:?}");
        let hexless = audit_text("scripts/emoji.gd", "var e = \"\\uZZZZ\"\n");
        assert_eq!(hexless.len(), 1, "{hexless:?}");

        // `/` and the octal digits are not GDScript escapes either: the
        // tokenizer's `default:` branch rejects them, so a file that carries
        // them is not GDScript.
        for shape in ["var a = \"a\\/b\"\n", "var a = \"\\0\"\n"] {
            let findings = audit_text("scripts/notes.gd", shape);
            assert_eq!(findings.len(), 1, "{shape}: {findings:?}");
            assert_eq!(findings[0].kind, IntegrityKind::ShellEscapeResidue);
        }
    }

    /// DR-88 ③: a backslash whose very next character is the `#` that opens a
    /// comment is still **code**.  The tokenizer accepts a backslash in code
    /// only as a line continuation (`Expected new line after "\\"` otherwise),
    /// so this is a foreign escape, not a comment marker.
    #[test]
    fn a_backslash_before_a_comment_marker_is_still_code() {
        let findings = audit_text("scripts/notes.gd", "var a = 1 + \\#c\n");
        assert_eq!(findings.len(), 1, "{findings:?}");
        assert_eq!(findings[0].kind, IntegrityKind::ShellEscapeResidue);
        assert_eq!(findings[0].line, 1);
    }

    /// DR-88 ②/③: a string literal that a trailing `\` continues onto the next
    /// line is **still a string**, so a `#` at the start of that next line opens
    /// no comment and a foreign escape behind it is residue.  This is the rule
    /// the old "a string must close on its own line" claim got wrong.
    #[test]
    fn a_continued_string_keeps_its_hash_inside_the_string() {
        let findings = audit_text("scripts/notes.gd", "var s = \"abc\\\n#c\\q\"\n");
        assert_eq!(findings.len(), 1, "{findings:?}");
        assert_eq!(findings[0].kind, IntegrityKind::ShellEscapeResidue);
        assert_eq!(findings[0].line, 2);

        // The converse: a legal escape on that continued line stays clean.
        assert_eq!(
            audit_text("scripts/notes.gd", "var s = \"abc\\\n#c\\n\"\n"),
            Vec::new()
        );
    }

    /// DR-88 ②: a triple-quoted literal really spans lines, so a line inside it
    /// that *looks* like a comment is string content and its escapes are judged
    /// as string escapes.
    #[test]
    fn a_triple_quoted_literal_spans_lines_and_keeps_its_escapes() {
        let legal = audit_text(
            "scripts/notes.gd",
            "var text = \"\"\"first\n# not a comment, it is line two\\n\"\"\"\n",
        );
        assert_eq!(legal, Vec::new(), "{legal:?}");

        let foreign = audit_text(
            "scripts/notes.gd",
            "var text = \"\"\"first\n# not a comment\\q\"\"\"\n",
        );
        assert_eq!(foreign.len(), 1, "{foreign:?}");
        assert_eq!(foreign[0].line, 2);
    }

    /// DR-88 ③: the escape rule is a **GDScript** rule.  A `.tscn` string is
    /// read by the resource parser, whose string branch takes a backslash
    /// followed by *any* character literally (`core/variant/variant_parser.cpp`,
    /// the `default:` branch of its escape `switch`), so there is no "foreign
    /// escape" class to catch there.  This test pins that **declaration** rather
    /// than leaving the omission implicit.
    #[test]
    fn a_scene_string_may_hold_a_backslash() {
        let scene =
            "[gd_scene format=3]\n\n[node name=\"Main\" type=\"Node2D\"]\nnote = \"C:\\Users\\dev\"\n";
        assert_eq!(audit_text("scenes/main.tscn", scene), Vec::new());
    }

    /// The DR-87 acceptance's counterexample table, judged by the rule as it now
    /// stands.  `L*` are legitimate scripts (clean) and `X*` are foreign or
    /// malformed escapes in code (one finding each), except the two the batch
    /// **declares**: `X2` is the language's own line continuation, and `X8` is a
    /// scene string, which has no escape alphabet at all (see
    /// [`Self::a_scene_string_may_hold_a_backslash`]).
    #[test]
    fn the_acceptance_counterexamples_are_all_judged() {
        let cases: &[(&str, &str, &str, usize)] = &[
            // --- legitimate GDScript / scenes: nothing to report ---
            ("L1 comment-with-windows-path", "scripts/a.gd",
             "# see C:\\Users\\dev\\project for the layout\nextends Node\n", 0),
            ("L2 raw-string-windows-path", "scripts/a.gd",
             "extends Node\n\nvar p = r\"C:\\Users\\dev\\project\"\n", 0),
            ("L3 legal-\\U-unicode-escape", "scripts/a.gd", "var e = \"\\U0001F600\"\n", 0),
            ("L4 legal-\\u-unicode-escape", "scripts/a.gd", "var e = \"\\u0041\"\n", 0),
            ("L5 hash-in-string-then-comment", "scripts/a.gd", "var s = \"#x\" # note\n", 0),
            ("L6 triple-quoted-with-comment-looking-line", "scripts/a.gd",
             "var t = \"\"\"a\n# b\n\"\"\"\n", 0),
            ("L7 legal-line-continuation", "scripts/a.gd", "var t = \"a\\\nb\"\n", 0),
            ("L8 whole-scene-with-comment-path", "scenes/s.tscn",
             "[gd_scene format=3]\n# C:\\Users\\dev\n[node name=\"Main\" type=\"Node2D\"]\n", 0),
            ("L9 own: raw triple with foreign-looking escapes", "scripts/a.gd",
             "var re = r'''\\d \\U0001F600 # x\nmore'''\n", 0),
            // --- foreign / malformed escapes in code: one finding each ---
            ("X1 backslash-before-comment-marker", "scripts/a.gd", "var a = 1 + \\#c\n", 1),
            ("X3 malformed-\\u-without-hex", "scripts/a.gd", "var s = \"\\uZZZZ\"\n", 1),
            ("X4 escape-in-string-that-contains-a-hash", "scripts/a.gd", "var s = \"#\\q\"\n", 1),
            ("X5 escape-in-second-string-after-hash-string", "scripts/a.gd",
             "var a = \"#\" + \"\\q\"\n", 1),
            ("X6 escape-immediately-before-line-continuation", "scripts/a.gd",
             "var s = \"a\\q\\\nb\"\n", 1),
            ("X7 escape-in-single-quoted-string-with-hash", "scripts/a.gd", "var s = '#\\q'\n", 1),
            ("X9 escape-in-a-string-continued-across-a-hash-line", "scripts/a.gd",
             "var s = \"abc\\\n#c\\q\"\n", 1),
            ("X10 escaped-quote-keeps-string-open", "scripts/a.gd", "var s = \"a\\\"\\q\"\n", 1),
            // --- declared out of scope, with the rule that says so ---
            ("X2 foreign-escape-as-last-code-char (declared legal: line continuation)",
             "scripts/a.gd", "var path = C:\\\n", 0),
            ("X8 foreign-escape-in-tscn-string (declared: no escape alphabet)",
             "scenes/s.tscn",
             "[gd_scene format=3]\n[node name=\"Main\" type=\"Node2D\"]\nnote = \"C:\\Users\\dev\"\n",
             0),
        ];
        for (name, path, content, expected) in cases {
            let findings = audit_text(path, content);
            assert_eq!(
                findings.len(),
                *expected,
                "{name}: expected {expected} finding(s), got {findings:?}"
            );
            if *expected == 1 {
                assert_eq!(
                    findings[0].kind,
                    IntegrityKind::ShellEscapeResidue,
                    "{name}"
                );
            }
        }
    }

    /// DR-89 ①: the DR-88 carry made an unterminated literal a **mask** over the
    /// rest of the file, so a `.tscn`/`.tres` tail behind an unterminated quote —
    /// which the parent revision `ab95c65` caught with its per-line scan — went
    /// from one finding to zero, and an unterminated **raw** literal hid a later
    /// `\q` the same way.  A literal still open at the end of the text is now
    /// reported as the fragment it is, which restores those findings without
    /// re-introducing the per-line assumption that would red a legitimate
    /// multi-line resource string.
    #[test]
    fn an_unterminated_literal_is_a_fragment_not_a_whole_document() {
        for (name, path, text) in [
            (
                "tscn tail behind an unterminated quote",
                "scenes/s.tscn",
                "[gd_scene format=3]\nname = \"abc\nvisible = false)  \n",
            ),
            (
                "tscn name field only",
                "scenes/s.tscn",
                "[gd_scene format=3]\nname = \"abc\n",
            ),
            (
                "tres tail behind an unterminated quote",
                "res/r.tres",
                "[gd_resource type=\"Resource\" format=3]\nname = \"abc\nvalue = 1)  \n",
            ),
            (
                "unterminated raw literal over a later residue",
                "scripts/a.gd",
                "var s = r\"abc\nvar p = \\q\n",
            ),
            (
                "unterminated plain literal at end of text",
                "scripts/a.gd",
                "var s = \"abc\n",
            ),
            (
                "unterminated triple-quoted literal at end of text",
                "scripts/a.gd",
                "var s = \"\"\"abc\n",
            ),
        ] {
            let findings = audit_text(path, text);
            assert_eq!(findings.len(), 1, "{name}: {findings:?}");
            assert_eq!(findings[0].kind, IntegrityKind::TruncatedFragment, "{name}");
            assert_eq!(
                findings[0].kind.token(),
                "artifact_write_truncated",
                "{name}"
            );
        }

        // The converse: a literal that closes — on its own line, after a
        // continuation, or as a triple-quoted block — is not a fragment, and a
        // **resource** string holding a `)` on a later line is legitimate (the
        // reader accepts a newline inside one, which is why the restored finding
        // comes from the carried scan and not from a per-line delimiter scan).
        for (name, path, text) in [
            ("closes on its own line", "scripts/a.gd", "var s = \"abc\"\n"),
            (
                "closes after a continuation",
                "scripts/a.gd",
                "var s = \"a\\\nb\"\n",
            ),
            (
                "triple closes later",
                "scripts/a.gd",
                "var s = \"\"\"a\nb\"\"\"\n",
            ),
            ("a raw literal closes", "scripts/a.gd", "var s = r\"a\\b\"\n"),
            (
                "resource string spans lines and closes",
                "scenes/s.tscn",
                "[gd_scene format=3]\n[node name=\"Main\" type=\"Node2D\"]\ntext = \"line1\nline2)\"\n",
            ),
        ] {
            assert_eq!(audit_text(path, text), Vec::new(), "{name}");
        }
    }

    /// DR-89 ④: the tokenizer's `case '\r':` accepts a backslash followed by a
    /// **lone** carriage return inside a string — when the next character is not
    /// a newline it adds the character and keeps the escape valid — so the audit
    /// used to refuse text the engine build accepts.  The escape alphabet now
    /// carries the CR character itself (not just the letter `r`).
    #[test]
    fn a_lone_carriage_return_after_a_backslash_is_the_languages_own_escape() {
        assert_eq!(
            audit_text("scripts/a.gd", "var s = \"a\\\rb\"\n"),
            Vec::new(),
            "a lone CR after a backslash inside a string is accepted by the tokenizer"
        );

        // The converse: adding the CR entry did not turn the escape rule off.
        let foreign = audit_text("scripts/a.gd", "var s = \"a\\qb\"\n");
        assert_eq!(foreign.len(), 1, "{foreign:?}");
        assert_eq!(foreign[0].kind, IntegrityKind::ShellEscapeResidue);
    }

    /// DR-89 ②: the corrected justification must rest on the artifact.  The round
    /// of record's five `\$` residues are **code**, not string content: they are
    /// lines 8–12 of the frozen copy
    /// `runs/smoke-t16/iter-1/candidate/scripts/main.gd`, transcribed here with
    /// no quote character on any of them.  A rule that skipped string literals
    /// would still have caught all five, so those bytes are not the reason the
    /// audit scans strings; the escape-processing class **inside** a literal is.
    #[test]
    fn the_round_of_records_residues_are_unquoted_expressions() {
        let lines = [
            "@onready var coins_label: Label = \\$HUD/Coins\n",
            "@onready var lives_label: Label = \\$HUD/Lives\n",
            "@onready var time_label: Label = \\$HUD/Time\n",
            "@onready var victory_label: Label = \\$HUD/Victory\n",
            "@onready var player: CharacterBody2D = \\$Player\n",
        ];
        for line in lines {
            assert!(
                !line.contains('"') && !line.contains('\''),
                "the residue line carries no quote: {line}"
            );
            let findings = audit_text("scripts/main.gd", line);
            assert_eq!(findings.len(), 1, "{line}: {findings:?}");
            assert_eq!(findings[0].kind, IntegrityKind::ShellEscapeResidue);
            assert_eq!(findings[0].line, 1);
        }
    }

    /// DR-90 ①: **the text-resource reader's own line comment is `;`**, and a
    /// legitimate scene or resource whose comment holds an apostrophe, a lone
    /// quote or an unmatched parenthesis is not a fragment.
    ///
    /// The rule comes from the engine, not from convenience: `VariantParser::
    /// get_token`'s `case ';'` discards the rest of the line, and
    /// `VariantParser::parse_tag_assign_eof` does the same
    /// (`core/variant/variant_parser.cpp`); `.tscn`/`.tres` are read through those
    /// functions (`scene/resources/resource_format_text.cpp`).  Both whole-document
    /// rules are exercised here — the apostrophe would otherwise open a phantom
    /// literal carried to the end of the text, and the `(` would otherwise be
    /// counted by the balance rule (the false positive the DR-88 acceptance
    /// reproduced as `DR89A-2`).
    #[test]
    fn a_semicolon_comment_is_the_text_resources_own_comment() {
        // `(name, path, text, why)` — every one is a document the reader accepts.
        let clean: &[(&str, &str, &str, &str)] = &[
            (
                "scene comment with an apostrophe",
                "scenes/s.tscn",
                "[gd_scene format=3]\n; don't move the node\n[node name=\"Main\" type=\"Node2D\"]\n",
                "the apostrophe is inside the reader's comment",
            ),
            (
                "scene comment with a single quote",
                "scenes/s.tscn",
                "[gd_scene format=3]\n; a lone ' apostrophe\n[node name=\"Main\" type=\"Node2D\"]\n",
                "one unpaired quote is inside the comment",
            ),
            (
                "scene comment with an unmatched parenthesis",
                "scenes/s.tscn",
                "[gd_scene format=3]\n; depth ( left open\n[node name=\"Main\" type=\"Node2D\"]\n",
                "the balance rule must not count a delimiter inside the comment",
            ),
            (
                "resource comment with an apostrophe",
                "res/r.tres",
                "[gd_resource type=\"Resource\" format=3]\n; don't move the resource\n[resource]\n",
                "the .tres reader is the same VariantParser",
            ),
            (
                "resource comment with a single quote",
                "res/r.tres",
                "[gd_resource type=\"Resource\" format=3]\n; a lone ' apostrophe\n[resource]\n",
                "the .tres twin of the scene case",
            ),
            (
                "resource comment with an unmatched parenthesis",
                "res/r.tres",
                "[gd_resource type=\"Resource\" format=3]\n; depth ( left open\n[resource]\n",
                "the pre-existing false positive DR89A-2, closed for .tres too",
            ),
            (
                "control: a plain comment",
                "scenes/s.tscn",
                "[gd_scene format=3]\n; plain comment\n[node name=\"Main\" type=\"Node2D\"]\n",
                "the control the acceptance measured as 0 at every revision",
            ),
            (
                "control: paired quotes and a closer in one comment",
                "scenes/s.tscn",
                "[gd_scene format=3]\n; \"paired\" quotes and a )\n[node name=\"Main\" type=\"Node2D\"]\n",
                "an unbalanced closer inside the comment is not code either",
            ),
            (
                "control: the resource twin of the paired-quote comment",
                "res/r.tres",
                "[gd_resource type=\"Resource\" format=3]\n; \"paired\" quotes and a )\n[resource]\n",
                "the same shape in a .tres",
            ),
            (
                "all three shapes in one scene comment",
                "scenes/s.tscn",
                "[gd_scene format=3]\n; don't ' ( all three\n[node name=\"Main\" type=\"Node2D\"]\n",
                "the three failing shapes are one reader rule, not three fixes",
            ),
            (
                "all three shapes in one resource comment",
                "res/r.tres",
                "[gd_resource type=\"Resource\" format=3]\n; don't ' ( all three\n[resource]\n",
                "and the .tres twin",
            ),
        ];
        for (name, path, text, why) in clean {
            let findings = audit_text(path, text);
            assert_eq!(findings, Vec::new(), "{name} ({why}): {findings:?}");
        }

        // The converse: skipping the comment did not blind the whole-document
        // rules.  A fragment that follows the comment is still a fragment, and a
        // fragment whose tail is the comment's own line is still caught by the
        // rule that reads *after* the skipped comment.
        let behind = audit_text(
            "scenes/s.tscn",
            "[gd_scene format=3]\n; don't touch\nname = \"abc\n",
        );
        assert_eq!(behind.len(), 1, "{behind:?}");
        assert_eq!(behind[0].kind, IntegrityKind::TruncatedFragment);
        assert_eq!(behind[0].line, 3);

        let closer_after = audit_text(
            "scenes/s.tscn",
            "[gd_scene format=3]\n; a ( b\nvisible = false)  \n",
        );
        assert_eq!(closer_after.len(), 1, "{closer_after:?}");
        assert_eq!(closer_after[0].kind, IntegrityKind::TruncatedFragment);
        assert_eq!(closer_after[0].line, 3);

        let resource_behind = audit_text(
            "res/r.tres",
            "[gd_resource type=\"Resource\" format=3]\n; don't ' (\nname = \"x\n",
        );
        assert_eq!(resource_behind.len(), 1, "{resource_behind:?}");
        assert_eq!(resource_behind[0].kind, IntegrityKind::TruncatedFragment);
        assert_eq!(resource_behind[0].line, 3);
    }

    /// DR-90 ②: the `;` rule is the **resource** reader's, not a global one.
    ///
    /// A GDScript `;` is a `SEMICOLON` token (`modules/gdscript/
    /// gdscript_tokenizer.cpp`, the token list's `";", // SEMICOLON`), i.e. a
    /// statement separator and executable content, while GDScript's comment is
    /// `#` alone (`case '#'` in `GDScriptTokenizerText::_skip_whitespace`).  So a
    /// `;` must never silence a `.gd` line: making it global would hide a real
    /// fragment behind it, which is the permissive direction this audit must not
    /// take.
    #[test]
    fn a_semicolon_is_not_a_comment_in_gdscript() {
        // GDScript's own comment still works, and still holds an apostrophe safely.
        assert_eq!(
            audit_text("scripts/a.gd", "var a = 1; # don't\n"),
            Vec::new()
        );
        assert_eq!(
            audit_text("scripts/a.gd", "var a = 1; var b = 2\n"),
            Vec::new()
        );

        // What follows a `;` is code, so a literal opened there is judged.
        let cut = audit_text("scripts/a.gd", "var a = 1; var s = 'abc\n");
        assert_eq!(cut.len(), 1, "{cut:?}");
        assert_eq!(cut[0].kind, IntegrityKind::TruncatedFragment);
        assert_eq!(cut[0].line, 1);

        // A `;` line in a resource *is* a comment: the same bytes are read by the
        // extension's own reader, not by a global rule.
        assert_eq!(
            audit_text(
                "scenes/s.tscn",
                "[gd_scene format=3]\n; a lone ' quote\n[node name=\"Main\" type=\"Node2D\"]\n",
            ),
            Vec::new()
        );
    }

    /// DR-90 ③: a comment marker inside a **string** opens no comment, and a
    /// comment marker inside an unterminated literal is content — the scanner
    /// consumes a literal as a unit, exactly as both readers do.
    #[test]
    fn a_comment_marker_inside_a_string_opens_no_comment() {
        // `;` inside a `.tscn` string is content, so the `(` is not counted.
        assert_eq!(
            audit_text(
                "scenes/s.tscn",
                "[gd_scene format=3]\ntext = \"; see foo(bar\"\n",
            ),
            Vec::new()
        );
        // ... and a `#` inside a string is content in a `.gd` too, which is why
        // the foreign escape behind it is still seen.
        let behind_a_hash = audit_text("scripts/a.gd", "var s = \"# \\q\"\n");
        assert_eq!(behind_a_hash.len(), 1, "{behind_a_hash:?}");
        assert_eq!(behind_a_hash[0].kind, IntegrityKind::ShellEscapeResidue);

        // A `;` or `#` inside an **unterminated** literal is content as well: the
        // literal is still reported as the fragment it is.
        for (path, text) in [
            ("scenes/s.tscn", "[gd_scene format=3]\ntext = \"abc ; \n"),
            ("scenes/s.tscn", "[gd_scene format=3]\ntext = \"abc # \n"),
        ] {
            let findings = audit_text(path, text);
            assert_eq!(findings.len(), 1, "{text}: {findings:?}");
            assert_eq!(findings[0].kind, IntegrityKind::TruncatedFragment);
            assert_eq!(findings[0].line, 2, "{text}");
        }
    }

    /// DR-90 ④: the divergence this fix must **not** hide.
    ///
    /// In a text resource `#` is not a comment.  `VariantParser::get_token`'s
    /// `case '#'` answers with a **colour** token, and the writer never emits one
    /// outside a string (`VariantWriter::write` serialises a `Color` as
    /// `Color(r, g, b, a)`, `core/variant/variant_parser.cpp`).  Modelling `#` as a
    /// resource comment would be a false premise in the permissive direction, so
    /// the rest of such a line stays code for both rules.  This is a deliberate
    /// tightening: it is measured, and its cost is named in the DR-90 report.
    #[test]
    fn a_hash_is_not_a_comment_in_a_text_resource() {
        let bracketed = audit_text(
            "scenes/s.tscn",
            "[gd_scene format=3]\n[node name=\"Main\" type=\"Node2D\"]\n# a comment with ]\n",
        );
        assert_eq!(bracketed.len(), 1, "{bracketed:?}");
        assert_eq!(bracketed[0].kind, IntegrityKind::TruncatedFragment);
        assert_eq!(bracketed[0].line, 3);

        // A `#` line in a scene that carries no delimiter and no quote is still
        // clean, so the tightening is about content, not about the byte.
        assert_eq!(
            audit_text(
                "scenes/s.tscn",
                "[gd_scene format=3]\n# C:\\Users\\dev\n[node name=\"Main\" type=\"Node2D\"]\n",
            ),
            Vec::new()
        );
        // And in a `.gd` the same byte really is a comment (the per-extension
        // rule cuts both ways).
        assert_eq!(
            audit_text("scripts/a.gd", "# a path ] C:\\Users\\dev\n"),
            Vec::new()
        );
    }
}
