//! Role prompts and skills, embedded at compile time so the binary stays
//! self-contained.
//!
//! The prompts contain `{{iteration}}` placeholders which the runtime
//! substitutes *before* the text is handed to the harness; the harness in turn
//! passes the finished text as a template variable value, never as template
//! source.

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

pub fn planner_task(iteration: u32) -> String {
    format!(
        "Iteration {iteration}: produce the development document for this iteration.\n\n\
         1. Read the public specification at `.hoh/TASK.md`.\n\
         2. Read the evidence bundle at `.hoh/evidence.json` (empty on iteration 1).\n\
         3. Read the document scaffold at `.hoh/SCAFFOLD.md`.\n\
         4. Select at most three priorities: blockers and regressions first.\n\
         5. Write `.hoh/plan.md` and submit it with \
         `$HOH_HOH_BIN submit --role planner --file .hoh/plan.md`.\n\n\
         Do not implement, edit or test production code. Do not write any other file."
    )
}

pub fn developer_task(iteration: u32) -> String {
    format!(
        "Iteration {iteration}: implement this iteration's plan in the current working directory.\n\n\
         1. Read `.hoh/TASK.md` (the public specification).\n\
         2. Read `.hoh/plan.md` (this iteration's priorities and gates).\n\
         3. Read `.hoh/EVIDENCE_HISTORY.md` (previously verified and unresolved behaviour).\n\
         4. Fix build/runtime blockers first, then implement the priorities in order.\n\
         5. Use `$HOH_HOH_BIN tools call <tool> --args-file <path>` for editor operations.\n\
         6. Keep the project launchable at all times; validate each change with a quick check.\n\n\
         Do not call `submit`. The artifact is the project itself."
    )
}

pub fn tester_task(iteration: u32) -> String {
    format!(
        "Iteration {iteration}: independently verify the frozen candidate in the current working \
         directory.\n\n\
         1. Read `.hoh/TASK.md` (the public specification).\n\
         2. Read `.hoh/plan.md` (priorities and acceptance gate for this iteration).\n\
         3. Read `.hoh/deterministic/*.json` (deterministic build/boot records).\n\
         4. Read `.hoh/EVIDENCE_PLAYBOOK.md` and `.hoh/TOOLS.md`.\n\
         5. Derive checkable claims, collect public execution records, and write \
         `.hoh/evidence.json` plus `.hoh/qa_report.md`.\n\
         6. Submit with `$HOH_HOH_BIN submit --role tester --file .hoh/evidence.json`.\n\n\
         Never modify production code or any file outside `.hoh/`. Unobservable behaviour is a \
         gap, not a pass."
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
