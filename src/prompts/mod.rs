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

pub const SKILL_GODOT_DEV: &str = include_str!("skills/godot-dev.md");
pub const SKILL_GODOT_TESTING: &str = include_str!("skills/godot-testing.md");

/// `(file name, content)` pairs injected as `.hoh/skills/*.md`.
pub fn skills() -> Vec<(&'static str, &'static str)> {
    vec![
        ("godot-dev.md", SKILL_GODOT_DEV),
        ("godot-testing.md", SKILL_GODOT_TESTING),
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
             movement and jumping are not enough: name the collectible pickup (the HUD\n\
             coin counter must move) and the win condition (the goal's exported `reached`\n\
             flag must become true and the player must be able to walk there).\n\
             5. Write `.hoh/plan.md` and submit it with \
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
             5. Use `{{{{HOH_HOH_BIN}}}} tools call <tool> --args-file <path>` for editor operations.\n\
             6. Keep the project launchable at all times; validate each change with a quick check.\n\
             7. Write a real file in the project early (see [budget] in your system prompt): a\n\
             round whose only writes went to `{{{{HOH_SCRATCH_DIR}}}}` produces no candidate\n\
             increment and is recorded as `no_engineering_write`.\n\n\
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
             `.hoh/evidence.json` plus `.hoh/qa_report.md`.\n\
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
