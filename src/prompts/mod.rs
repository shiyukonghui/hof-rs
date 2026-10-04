//! Role prompts and skills, embedded at compile time so the binary stays
//! self-contained.
//!
//! The prompts contain `{{iteration}}` placeholders which the runtime
//! substitutes *before* the text is handed to the harness; the harness in turn
//! passes the finished text as a template variable value, never as template
//! source.
//!
//! DR-66: the documents below never spell a *shell variable* literally.  They
//! write `{{HOH_NAME}}`, and every delivery path turns it into the target
//! shell's syntax (`%HOH_NAME%` for cmd, `$HOH_NAME` for sh) through
//! [`crate::runtime::shell`].  `tests/role_shell_contract.rs` extracts a command
//! from the delivered text and executes it in a real `LocalEnvironment`.
//!
//! DR-68 ⑤: a template written **inside a `format!` literal** must be escaped as
//! `{{{{HOH_NAME}}}}`.  `{{HOH_NAME}}` is folded to the single-brace form
//! `{HOH_NAME}` by `format!` *before* [`shell::render_command_vars`] runs, and
//! that renderer only matches the double-brace form, so the role would receive a
//! placeholder nothing resolves (`smoke-t8` shipped exactly that in the three
//! task prompts and in the `TOOLS.md` header).  `assert_fully_rendered` and the
//! shell contract test now reject both spellings.

use crate::runtime::shell::{self, ShellFlavor};

pub const PLANNER_PROMPT: &str = include_str!("planner.md");
pub const DEVELOPER_PROMPT: &str = include_str!("developer.md");
pub const TESTER_PROMPT: &str = include_str!("tester.md");

/// The `{{shell_truth}}` placeholder every role prompt carries.
///
/// Round-1 write-path batch.  The role's shell is `cmd.exe`, and round 1's
/// Developer spent 140 calls, ~54 minutes and ~10.4M tokens fighting it: it
/// emitted `cat .hoh/TASK.md; echo "=====PLAN====="; cat .hoh/plan.md` (POSIX
/// syntax, `;` chaining, `cat`) into a shell that has none of those, and then
/// tried to write multi-line Rust through `bash -c` heredocs and `echo`
/// appends.  The harness already knew the shell (`crate::runtime::shell`,
/// DR-66) — the *prompt* never said so plainly, so this text does.
///
/// It is delivered through a placeholder rather than copied into three files so
/// the three role prompts cannot drift apart, and it is rendered for the target
/// shell so the same document is executable on both platforms.
pub const SHELL_TRUTH_PLACEHOLDER: &str = "{{shell_truth}}";

/// The shell-truth section for `flavor`.
pub fn shell_truth(flavor: ShellFlavor) -> String {
    match flavor {
        ShellFlavor::Windows => SHELL_TRUTH_WINDOWS.to_string(),
        ShellFlavor::Posix => SHELL_TRUTH_POSIX.to_string(),
    }
}

/// The Windows (cmd.exe) form of the shell truth.
const SHELL_TRUTH_WINDOWS: &str = "[shell]\n\
     Your shell is **`cmd.exe`**, not POSIX `sh`. This is a hard requirement, not \
     style: a real round burned 140 model calls and 54 minutes on it, and ended with a \
     format failure instead of a written file.\n\
     \n\
     - **Variables are `%NAME%`.** `$HOH_HOH_BIN` is not expanded; the line then fails \
     with `'$HOH_HOH_BIN\" …' is not recognized as an internal or external command`.\n\
     - **Chaining is `&&`**, never `;`. `;` is exposed as a separate command and the \
     rest of the line runs even when the first part failed.\n\
     - **Only double quotes group.** Single quotes are literal characters: \
     `a 'b c'` passes three arguments.\n\
     - **`cat` does not exist.** Use `type <file>` or the read directive below.\n\
     - **Forbidden command shapes** (each of them failed in a recorded round): \
     `cat <file>`; `a; b`; `bash -c \"…\"`; a heredoc (`<< EOF`); an inline \
     interpreter one-liner with real newlines inside the string; and `echo … >> file` \
     used to build a multi-line file one line at a time.\n\
     \n\
     **To write a file, use the write directive.** The harness executes it itself, so no \
     shell parses the content and every character is literal — quotes, `%`, `$`, `(`, \
     `)`, `\\` and newlines included. It is a bash command whose whole text is:\n\
     \n\
     ```text\n\
     HOH_WRITE_FILE src/game.rs\n\
     <the file's exact content, as many lines as you like>\n\
     HOH_END_WRITE_FILE\n\
     ```\n\
     \n\
     The first line names the path (relative to the working directory), the content is \
     everything after it, and the last line is exactly `HOH_END_WRITE_FILE`. Write the \
     **whole** file in one directive; never assemble a source file with `echo` appends. \
     A directive that is missing its closing line is refused with an explanation rather \
     than half-written.\n\
     \n\
     **To read a file, use the read directive** (or `type`):\n\
     \n\
     ```text\n\
     HOH_READ_FILE .hoh/plan.md\n\
     ```\n\
     \n\
     Tool calls are ordinary shell commands, with the argument file written by a \
     directive first:\n\
     \n\
     ```text\n\
     {{HOH_HOH_BIN}} tools call bevy_grounded --args-file {{HOH_ARTIFACT_DIR}}/args/grounded.json\n\
     ```\n";

/// The POSIX form of the same section.
const SHELL_TRUTH_POSIX: &str = "[shell]\n\
     Your shell is **POSIX `sh`**.\n\
     \n\
     - **Variables are `$NAME`** (so `$HOH_HOH_BIN`, not `%HOH_HOH_BIN%`).\n\
     - **Chaining is `;` or `&&`.**\n\
     - **Single quotes are literal**, so they group too.\n\
     - **`cat` exists**, and so do heredocs.\n\
     \n\
     **To write a file, use the write directive anyway.** It is executed by the harness \
     itself, so no shell parses the content and every character is literal:\n\
     \n\
     ```text\n\
     HOH_WRITE_FILE src/game.rs\n\
     <the file's exact content, as many lines as you like>\n\
     HOH_END_WRITE_FILE\n\
     ```\n\
     \n\
     The first line names the path (relative to the working directory), the content is \
     everything after it, and the last line is exactly `HOH_END_WRITE_FILE`. Write the \
     **whole** file in one directive.\n\
     \n\
     **To read a file, use the read directive** (or `cat`):\n\
     \n\
     ```text\n\
     HOH_READ_FILE .hoh/plan.md\n\
     ```\n\
     \n\
     Tool calls are ordinary shell commands:\n\
     \n\
     ```text\n\
     {{HOH_HOH_BIN}} tools call bevy_grounded --args-file {{HOH_ARTIFACT_DIR}}/args/grounded.json\n\
     ```\n";

pub const SKILL_GODOT_DEV: &str = include_str!("skills/godot-dev.md");
pub const SKILL_GODOT_TESTING: &str = include_str!("skills/godot-testing.md");
/// The Bevy 0.19.1 recipes (DR-96).  The Godot documents are kept because they
/// are the *previous* engine's materials and the tests that pin their shell
/// contract still hold; the role prompts point a Bevy round at these two.
pub const SKILL_BEVY_DEV: &str = include_str!("skills/bevy-dev.md");
pub const SKILL_BEVY_TESTING: &str = include_str!("skills/bevy-testing.md");

/// `(file name, content)` pairs injected as `.hoh/skills/*.md`.
///
/// The order matters: the shell-contract test extracts the first executable
/// `tools call` recipe in delivery order, so the previous engine's book stays
/// first and the Bevy books follow it.
pub fn skills() -> Vec<(&'static str, &'static str)> {
    vec![
        ("godot-dev.md", SKILL_GODOT_DEV),
        ("godot-testing.md", SKILL_GODOT_TESTING),
        ("bevy-dev.md", SKILL_BEVY_DEV),
        ("bevy-testing.md", SKILL_BEVY_TESTING),
    ]
}

/// DR-66 ①: one skill body as it is injected, or `None` when the name is not
/// embedded.
pub fn skill_document(name: &str, flavor: ShellFlavor) -> Option<String> {
    skills()
        .into_iter()
        .find(|(file, _)| *file == name)
        .map(|(_, body)| shell::render_command_vars(body, flavor))
}

/// DR-66 ①: the skills as they are actually injected — `skills()` with the
/// shell placeholders resolved for `flavor`.  This is the only form a role ever
/// reads; the raw bodies above are templates.
pub fn skill_documents(flavor: ShellFlavor) -> Vec<(String, String)> {
    skills()
        .into_iter()
        .map(|(name, body)| (name.to_string(), shell::render_command_vars(body, flavor)))
        .collect()
}

pub fn planner_task(iteration: u32) -> String {
    planner_task_with_shell(iteration, ShellFlavor::HOST)
}

/// DR-66 ①: the planner task with an explicit target shell.  Task prompts are
/// delivered verbatim (nothing re-renders them), so a POSIX call spelled into a
/// cmd shell is unusable — the same defect the developer task had.
pub fn planner_task_with_shell(iteration: u32, flavor: ShellFlavor) -> String {
    shell::render_command_vars(
        &format!(
            "Iteration {iteration}: produce the development document for this iteration.\n\n\
             1. Read the public specification at `.hoh/TASK.md`.\n\
             2. Read the evidence bundle at `.hoh/evidence.json` (empty on iteration 1).\n\
             3. Read the document scaffold at `.hoh/SCAFFOLD.md`.\n\
             4. Select at most three priorities: blockers and regressions first. The\n\
             acceptance gate must cover the whole playable loop the specification names —\n\
             movement and jumping are not enough: name the coin count (`CoinCounter.coins`\n\
             must go from 0 to a positive number) and the win flag (`WinFlag.won` must become\n\
             true at a place the player can actually reach).\n\
             5. Write `.hoh/plan.md` with the `HOH_WRITE_FILE .hoh/plan.md` directive (your\n\
             system prompt shows its exact shape), then submit it with \
             `{{{{HOH_HOH_BIN}}}} submit --role planner --file plan.md`.\n\n\
             Do not implement, edit or test production code. Do not write any other file."
        ),
        flavor,
    )
}

pub fn developer_task(iteration: u32) -> String {
    developer_task_with_shell(iteration, ShellFlavor::HOST)
}

/// DR-66 ①: the developer task with an explicit target shell (see
/// [`planner_task_with_shell`]).
pub fn developer_task_with_shell(iteration: u32, flavor: ShellFlavor) -> String {
    shell::render_command_vars(
        &format!(
            "Iteration {iteration}: implement this iteration's plan in the current working directory.\n\n\
             1. Read `.hoh/TASK.md` (the public specification).\n\
             2. Read `.hoh/plan.md` (this iteration's priorities and gates).\n\
             3. Read `.hoh/EVIDENCE_HISTORY.md` (previously verified and unresolved behaviour).\n\
             4. Fix build/runtime blockers first, then implement the priorities in order.\n\
             5. Use `{{{{HOH_HOH_BIN}}}} tools call <tool> --args-file <path>` for tool calls\n\
             (`bevy_*` semantic tools and the generic `world.*` verbs; the schemas are in\n\
             `.hoh/TOOLS.md`, and `.hoh/skills/bevy-dev.md` has the recipes). The project is a\n\
             Bevy 0.19.1 crate named `hof_game`: keep `cargo build --offline` at exit code 0,\n\
             and keep the frozen contract surfaces in `src/contract.rs` registered.\n\
             6. Keep the project launchable at all times; validate each change with a quick check.\n\
             7. Write a real file in the project early (see [budget] in your system prompt): a\n\
             round whose only writes went to `{{{{HOH_SCRATCH_DIR}}}}` produces no candidate\n\
             increment and is recorded as `no_engineering_write`. Use the `HOH_WRITE_FILE`\n\
             directive for every source write — your system prompt shows its exact shape, and\n\
             it is the only path that carries multi-line Rust through this shell unchanged.\n\n\
             Do not call `submit`. The artifact is the project itself."
        ),
        flavor,
    )
}

pub fn tester_task(iteration: u32) -> String {
    tester_task_with_shell(iteration, ShellFlavor::HOST)
}

/// DR-66 ①: the tester task with an explicit target shell (see
/// [`planner_task_with_shell`]).
pub fn tester_task_with_shell(iteration: u32, flavor: ShellFlavor) -> String {
    shell::render_command_vars(
        &format!(
            "Iteration {iteration}: independently verify the frozen candidate in the current working \
             directory.\n\n\
             1. Read `.hoh/TASK.md` (the public specification).\n\
             2. Read `.hoh/plan.md` (priorities and acceptance gate for this iteration).\n\
             3. Read `.hoh/deterministic/*.json` (deterministic build/boot records).\n\
             4. Read `.hoh/EVIDENCE_PLAYBOOK.md` and `.hoh/TOOLS.md`.\n\
             5. Derive checkable claims, collect public execution records, and write \
             `.hoh/evidence.json` plus `.hoh/qa_report.md` with the `HOH_WRITE_FILE`\n\
             directive (your system prompt shows its exact shape).\n\
             6. Submit with `{{{{HOH_HOH_BIN}}}} submit --role tester --file evidence.json`.\n\n\
             Never modify production code or any file outside `.hoh/`. Unobservable behaviour is a \
             gap, not a pass."
        ),
        flavor,
    )
}

/// The document scaffold handed to the Planner.
pub const SCAFFOLD: &str = "# Development document scaffold\n\n\
     Fill exactly these three sections (see `.hoh/plan.md` contract):\n\n\
     ## Project Planner Priorities\n\
     ### Priority Order\n\
     1. **<name>** - <action and observable outcome>\n\
     ### Preservation Gate\n\
     - <working functionality / evidence that must not regress>\n\
     ### Acceptance Gate\n\
     - <smallest end-to-end validation>\n";
