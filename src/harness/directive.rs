//! The roles' **first-class write and read path** (round-1 write-path batch).
//!
//! Round 1's Developer spent 140 model calls, ~54 minutes and ~10.4M prompt
//! tokens on one attempt, and ended with the external agent's
//! `RepeatedFormatError`, because the only way it could create a source file was
//! to emit file content **inside a shell command line** — and its shell is
//! `cmd.exe`, not POSIX `sh`.  Multi-line Rust through `cmd.exe` is hostile
//! (`(`, `)`, `"`, `%`, `^` and newlines all mean something to it), so the
//! content was truncated, the file was reduced to 0 bytes at one point, and the
//! role ground against the shell instead of writing the file it had already
//! designed.
//!
//! This module defines a **directive** the harness recognises *before* the
//! command reaches `cmd.exe`:
//!
//! ```text
//! HOH_WRITE_FILE src/game.rs
//! use bevy::prelude::*;
//! fn main() {
//!     println!("100% \"done\" (really) $HOME C:\\x");
//! }
//! HOH_END_WRITE_FILE
//! ```
//!
//! and its read counterpart:
//!
//! ```text
//! HOH_READ_FILE .hoh/plan.md
//! ```
//!
//! [`crate::harness::guard::WriteGuardEnvironment`] intercepts these in the
//! [`mini_swe_agent::Environment`] the agent runs against and performs the
//! write/read in Rust, so **no shell parses the content at all**.  Everything in
//! this module is pure string work, so the round-trip property — multi-line
//! content carrying quotes, parentheses, percent signs, dollar signs and
//! backslashes comes back byte-for-byte — is testable without a shell, a model
//! or a game.
//!
//! ## Why a directive and not a "cmd recipe"
//!
//! DR-66 rendered the role's *variable syntax* for the real shell, which fixed
//! the `$HOH_HOH_BIN` half of the defect.  It cannot fix this half: `cmd.exe`
//! has no escape for a literal `%`, no heredoc, and no way to carry a raw
//! newline inside an argument, so *any* recipe that puts a whole source file on
//! a `cmd.exe` command line has to survive the same parser that ate round 1.
//! Intercepting the command is the only byte-exact path, and it is a first-class
//! tool surface rather than an improvised recipe.

/// The first line of a write directive: `HOH_WRITE_FILE <path>`.
pub const WRITE_MARKER: &str = "HOH_WRITE_FILE";
/// The first line of a read directive: `HOH_READ_FILE <path>`.
pub const READ_MARKER: &str = "HOH_READ_FILE";
/// The line that closes a write directive's content.
pub const END_MARKER: &str = "HOH_END_WRITE_FILE";

/// What one role action is.
///
/// `Shell` is every command that is not a directive: it is handed to
/// `cmd.exe` unchanged, exactly as before.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Directive {
    /// Write `content` to `path`, byte for byte.
    Write { path: String, content: String },
    /// Read `path` and return its bytes.
    Read { path: String },
    /// A recognised marker whose shape is wrong.  It must **not** reach the
    /// shell: `cmd.exe` would answer `'HOH_WRITE_FILE' is not recognized`, which
    /// tells the model nothing about what it got wrong.
    Malformed { reason: String },
    /// Not a directive.
    Shell,
}

/// The canonical text of a write directive.
///
/// This is the exact form the prompts document and the tests round-trip.  When
/// `content` ends with a newline (the normal case for a source file) the
/// terminator sits on a line of its own; when it does not, the terminator
/// follows the last byte directly, which is what makes a file with no trailing
/// newline expressible.
pub fn render_write(path: &str, content: &str) -> String {
    format!("{WRITE_MARKER} {path}\n{content}{END_MARKER}")
}

/// The canonical text of a read directive.
pub fn render_read(path: &str) -> String {
    format!("{READ_MARKER} {path}")
}

/// The command with its leading blank lines/indentation removed.
///
/// A directive is recognised from the *first non-blank* text; everything after
/// the header line is content and is never trimmed.
fn anchored(command: &str) -> &str {
    command.trim_start_matches(|c: char| c.is_whitespace() || c == '\u{feff}')
}

/// The parsed first line of a directive: `(marker, argument)`.
fn first_line(anchored: &str) -> (&str, Option<&str>) {
    let line_end = anchored.find('\n').unwrap_or(anchored.len());
    let first = anchored[..line_end].trim_end_matches('\r');
    let mut parts = first.splitn(2, char::is_whitespace);
    let marker = parts.next().unwrap_or("");
    let argument = parts.next().map(str::trim).filter(|rest| !rest.is_empty());
    (marker, argument)
}

/// Parse one role action into a [`Directive`].
pub fn parse_directive(command: &str) -> Directive {
    let anchored = anchored(command);
    let (marker, argument) = first_line(anchored);
    if marker.eq_ignore_ascii_case(READ_MARKER) {
        return match argument {
            Some(path) => Directive::Read {
                path: path.to_string(),
            },
            None => Directive::Malformed {
                reason: format!(
                    "`{READ_MARKER}` needs a path on the same line, e.g. `{READ_MARKER} src/game.rs`"
                ),
            },
        };
    }
    if !marker.eq_ignore_ascii_case(WRITE_MARKER) {
        return Directive::Shell;
    }
    let Some(path) = argument else {
        return Directive::Malformed {
            reason: format!(
                "`{WRITE_MARKER}` needs a path on the same line, e.g. `{WRITE_MARKER} src/game.rs`"
            ),
        };
    };
    let Some(header_end) = anchored.find('\n') else {
        return Directive::Malformed {
            reason: format!(
                "`{WRITE_MARKER} {path}` has no content: the file's text follows on the next line, \
                 and the directive is closed by a final line `{END_MARKER}`"
            ),
        };
    };
    let body = &anchored[header_end + 1..];
    // The directive **ends** with the terminator: `render_write` always appends
    // it, trailing whitespace/newlines after it are tolerated, and nothing may
    // follow.  Taking the final `HOH_END_WRITE_FILE` (rather than the first)
    // means a role may legitimately write a file whose own text mentions the
    // marker.
    let trimmed = body.trim_end_matches(['\n', '\r', ' ', '\t']);
    let start = trimmed.len().saturating_sub(END_MARKER.len());
    let closed = trimmed
        .get(start..)
        .map(|tail| tail.eq_ignore_ascii_case(END_MARKER))
        .unwrap_or(false);
    if !closed {
        return Directive::Malformed {
            reason: unclosed(path),
        };
    }
    Directive::Write {
        path: path.to_string(),
        content: body[..start].to_string(),
    }
}

/// The one malformed-write reason, so every caller states the same rule.
fn unclosed(path: &str) -> String {
    format!(
        "`{WRITE_MARKER} {path}` is not closed: end the content with a final line that is exactly \
         `{END_MARKER}`, with nothing after it"
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    /// The hostile-content property the batch exists for: multi-line text with
    /// quotes, parentheses, percent signs, dollar signs and backslashes must come
    /// back **byte for byte**.
    #[test]
    fn hostile_multiline_content_round_trips_byte_for_byte() {
        let content = "use bevy::prelude::*;\n\
                       fn main() {\n\
                       \x20   let pct = 100 % 3; // \"percent\"\n\
                       \x20   let money = \"$HOME and %PATH% and 100%%\";\n\
                       \x20   let path = \"C:\\\\Users\\\\wyl\\\\(x)\";\n\
                       \x20   let (a, b) = (1, 2);\n\
                       }\n";
        let command = render_write("src/game.rs", content);
        match parse_directive(&command) {
            Directive::Write { path, content: got } => {
                assert_eq!(path, "src/game.rs");
                assert_eq!(got, content, "byte-exact round trip");
                assert_eq!(got.as_bytes(), content.as_bytes());
            }
            other => panic!("parsed as {other:?}"),
        }
    }

    /// Every byte value that is legal UTF-8 must survive inside a directive,
    /// including the ones `cmd.exe` reserves.
    #[test]
    fn a_directive_is_not_a_shell_command_and_has_no_reserved_characters() {
        for hostile in [
            "a & b | c",
            "echo > nul < in",
            "100% %PATH% %%",
            "$VAR ${x} `tick`",
            "a\"b'c",
            "(a) (b)",
            "^ caret ^^",
            "back\\slash\\end",
            "line1\r\nline2\r\n",
            "",
            "no trailing newline",
        ] {
            let command = render_write("p.rs", hostile);
            assert_eq!(
                parse_directive(&command),
                Directive::Write {
                    path: "p.rs".to_string(),
                    content: hostile.to_string(),
                },
                "content {hostile:?}"
            );
        }
    }

    #[test]
    fn a_write_with_no_trailing_newline_still_ends_at_the_marker() {
        let command = render_write("a.txt", "abc");
        assert_eq!(command, "HOH_WRITE_FILE a.txt\nabcHOH_END_WRITE_FILE");
        assert_eq!(
            parse_directive(&command),
            Directive::Write {
                path: "a.txt".to_string(),
                content: "abc".to_string()
            }
        );
    }

    #[test]
    fn an_empty_file_is_a_write_and_not_a_shell_command() {
        assert_eq!(
            parse_directive(&render_write("empty.rs", "")),
            Directive::Write {
                path: "empty.rs".to_string(),
                content: String::new()
            }
        );
    }

    #[test]
    fn the_read_directive_carries_its_path() {
        assert_eq!(
            parse_directive(&render_read(".hoh/plan.md")),
            Directive::Read {
                path: ".hoh/plan.md".to_string()
            }
        );
        assert!(matches!(
            parse_directive("HOH_READ_FILE"),
            Directive::Malformed { .. }
        ));
    }

    #[test]
    fn an_unterminated_write_is_malformed_never_truncated_content() {
        let directive = parse_directive("HOH_WRITE_FILE src/game.rs\nfn main() {}\n");
        match directive {
            Directive::Malformed { reason } => {
                assert!(reason.contains("not closed"), "{reason}");
            }
            other => panic!("an unfinished write must not be guessed at: {other:?}"),
        }
        let no_body = parse_directive("HOH_WRITE_FILE src/game.rs");
        assert!(matches!(no_body, Directive::Malformed { .. }));
    }

    /// Anything that is not a directive is still a shell command, unchanged.
    #[test]
    fn ordinary_commands_are_left_alone() {
        for command in [
            "cargo build --offline",
            "dir /b",
            "%HOH_HOH_BIN% tools call bevy_grounded --args-file a.json",
            "call %HOH_HOH_BIN% submit --role planner --file plan.md",
            "",
            "   \n  ",
        ] {
            assert_eq!(parse_directive(command), Directive::Shell, "{command:?}");
        }
    }

    #[test]
    fn the_marker_is_recognised_case_insensitively_and_after_blank_lines() {
        let command = "\n\nhoh_write_file a.txt\nx\nhoh_end_write_file";
        assert_eq!(
            parse_directive(command),
            Directive::Write {
                path: "a.txt".to_string(),
                content: "x\n".to_string()
            }
        );
    }
}
