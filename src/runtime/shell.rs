//! DR-66 ① — the shell a role's commands actually run in, and the syntax the
//! documents that describe those commands must use.
//!
//! `smoke-t7` measured the mismatch: the prompts, the generated `.hoh/TOOLS.md`,
//! the skills and the evidence playbook all wrote `$HOH_HOH_BIN tools call …`
//! (POSIX), while mini's `LocalEnvironment` starts **`cmd.exe`** on Windows
//! (`mini-swe-agent-rust-mini/rust/src/environments/local.rs:66-76`).  The
//! role's first successful tool call came only after ~30 % of its budget, 115
//! of 150 steps were spent wrapping the command in `bash -c`, and the literal
//! error `'$HOH_HOH_BIN" tools call …' is not recognized …` is in the recorded
//! trajectory.
//!
//! DR-66 chose **platform rendering** (option (a) of the task book) over
//! changing the role's shell (option (b)): `LocalEnvironment` lives in the
//! engine-side `F:/RustProjects/mini-swe-agent-rust-mini` checkout, which is
//! outside this repository, and swapping the shell would also change the
//! behaviour of every command the roles already get right (cmd builtins,
//! backslash paths, `%…%` in the existing recipes).  The rendered form and the
//! executed form now come from one function — [`render_var`] — and
//! `tests/role_shell_contract.rs` executes the rendered command in a real
//! `LocalEnvironment`.
//!
//! Templates in `src/prompts/**`, the playbook and `TOOLS.md` never write a
//! shell variable directly: they write `{{HOH_NAME}}`, and every delivery path
//! renders it through this module.

/// The two shell dialects the runtime can target.
///
/// `Windows` is cmd.exe: a variable reference is `%NAME%`.  `Posix` is `sh`:
/// a variable reference is `$NAME`.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ShellFlavor {
    Windows,
    Posix,
}

impl ShellFlavor {
    /// The shell of the machine this binary runs on.
    ///
    /// This is the same condition mini picks its shell with, so a document
    /// rendered for [`ShellFlavor::HOST`] is a document the role can execute.
    #[cfg(windows)]
    pub const HOST: ShellFlavor = ShellFlavor::Windows;
    /// The shell of the machine this binary runs on (see the Windows variant).
    #[cfg(not(windows))]
    pub const HOST: ShellFlavor = ShellFlavor::Posix;

    /// How `name` is written so the shell expands it.
    pub fn var(self, name: &str) -> String {
        match self {
            ShellFlavor::Windows => format!("%{name}%"),
            ShellFlavor::Posix => format!("${name}"),
        }
    }
}

/// Every `HOH_*` variable a delivered document may name through a placeholder.
///
/// The `HOH_*` **file names** (`.hoh/TOOLS.md`, `HOH_HOH_BIN tools call`) are
/// not shell variables and must not be rewritten; the distinction is that a
/// *variable reference* is the whole token `` `{{HOH_X}}` `` (backticked, or the
/// command's first word), which is what the templates and [`render_command_vars`]
/// agree on.
pub const COMMAND_VARS: &[&str] = &[
    "HOH_HOH_BIN",
    "HOH_ARTIFACT_DIR",
    "HOH_SCRATCH_DIR",
    "HOH_VIEW_DIR",
    "HOH_RUN_DIR",
];

/// Render one reference to `name` for `flavor`.
pub fn render_var(name: &str, flavor: ShellFlavor) -> String {
    flavor.var(name)
}

/// Rewrite every shell-variable placeholder in a document for `flavor`.
///
/// This is the **delivery** step: it runs after ordinary `{{…}}` substitution,
/// and the result is what a role reads.  It is deliberately a pure string
/// function so it can be applied to a prompt, a skill, a playbook or a
/// generated `TOOLS.md` — and asserted on — without a harness in the loop.
pub fn render_command_vars(document: &str, flavor: ShellFlavor) -> String {
    let mut rendered = document.to_string();
    for name in COMMAND_VARS {
        rendered = rendered.replace(&placeholder(name), &render_var(name, flavor));
    }
    rendered
}

/// Does this delivered document still carry a raw shell placeholder?
///
/// A leftover placeholder reaching a role is a contract failure on its own: it
/// is not a runnable command, and the extraction rule in
/// `tests/role_shell_contract.rs` keys on exactly that token shape.
pub fn contains_unresolved_command_var(document: &str) -> bool {
    COMMAND_VARS
        .iter()
        .any(|name| document.contains(&placeholder(name)))
}

/// Rewrite a **rendered** command from one shell's variable dialect into the
/// other's.
///
/// Unlike [`render_command_vars`] (which turns `{{HOH_*}}` templates into a
/// dialect), this converts an already-delivered command: every `$NAME` becomes
/// `%NAME%` for [`ShellFlavor::Windows`] and the reverse for
/// [`ShellFlavor::Posix`].  `tests/role_shell_contract.rs` uses it for its
/// control — "the platform-correct spelling of this very command succeeds" —
/// so the test can prove its fixture works without silently extracting a
/// different command.
pub fn rewrite_var_dialect(command: &str, flavor: ShellFlavor) -> String {
    let mut out = command.to_string();
    for name in COMMAND_VARS {
        out = match flavor {
            ShellFlavor::Windows => out.replace(&format!("${name}"), &format!("%{name}%")),
            ShellFlavor::Posix => out.replace(&format!("%{name}%"), &format!("${name}")),
        };
    }
    out
}

/// The placeholder a template writes for `name`.
fn placeholder(name: &str) -> String {
    format!("{{{{{name}}}}}")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn the_windows_flavor_is_percent_and_the_posix_flavor_is_dollar() {
        assert_eq!(ShellFlavor::Windows.var("HOH_HOH_BIN"), "%HOH_HOH_BIN%");
        assert_eq!(ShellFlavor::Posix.var("HOH_HOH_BIN"), "$HOH_HOH_BIN");
    }

    #[test]
    fn rendering_replaces_every_placeholder_and_leaves_no_template_behind() {
        let template = "call `{{HOH_HOH_BIN}} tools call x --args-file {{HOH_ARTIFACT_DIR}}/a.json`";
        let windows = render_command_vars(template, ShellFlavor::Windows);
        assert_eq!(
            windows,
            "call `%HOH_HOH_BIN% tools call x --args-file %HOH_ARTIFACT_DIR%/a.json`"
        );
        assert!(!contains_unresolved_command_var(&windows));
        let posix = render_command_vars(template, ShellFlavor::Posix);
        assert_eq!(
            posix,
            "call `$HOH_HOH_BIN tools call x --args-file $HOH_ARTIFACT_DIR/a.json`"
        );
        assert!(!contains_unresolved_command_var(&posix));
    }

    #[test]
    fn the_host_flavor_matches_the_platform() {
        if cfg!(windows) {
            assert_eq!(ShellFlavor::HOST, ShellFlavor::Windows);
            assert_eq!(render_var("HOH_VIEW_DIR", ShellFlavor::HOST), "%HOH_VIEW_DIR%");
        } else {
            assert_eq!(ShellFlavor::HOST, ShellFlavor::Posix);
            assert_eq!(render_var("HOH_VIEW_DIR", ShellFlavor::HOST), "$HOH_VIEW_DIR");
        }
    }

    #[test]
    fn a_rendered_command_can_be_rewritten_into_the_other_dialect() {
        let posix = "$HOH_HOH_BIN tools call x --args-file $HOH_ARTIFACT_DIR/args/a.json";
        let windows = rewrite_var_dialect(posix, ShellFlavor::Windows);
        assert_eq!(
            windows,
            "%HOH_HOH_BIN% tools call x --args-file %HOH_ARTIFACT_DIR%/args/a.json"
        );
        assert_eq!(rewrite_var_dialect(&windows, ShellFlavor::Posix), posix);
    }
}
