//! Single role invocation plumbing: environment variables, trajectory parent
//! directory creation, and prompt rendering guards.

use std::collections::BTreeMap;
use std::path::Path;

use crate::config::HohConfig;
use crate::harness::Harness;
use crate::model::Role;
use crate::runtime::role::{RoleInvocation, RoleOutcome};

/// DR-25: resolve a path to an absolute one without requiring it to exist.
/// `smoke-t2` handed a *relative* `HOH_ARTIFACT_DIR` to a shell whose cwd was
/// already the view root, and `hoh submit` nested the whole run path inside it.
pub fn absolute_path(path: &Path) -> std::path::PathBuf {
    if path.is_absolute() {
        return path.to_path_buf();
    }
    std::env::current_dir()
        .map(|cwd| cwd.join(path))
        .unwrap_or_else(|_| path.to_path_buf())
}

/// Build the `HOH_*` environment handed to the agent's shell (§4.2.5).
///
/// DR-25: **every path-shaped variable is absolute.**  A role may be started
/// from any working directory, so a relative base silently changes meaning.
///
/// Round-1 write-path batch: `target_dir` is the adapter's shared build cache
/// (`ProjectAdapter::build_target_dir`).  Round 1's Developer ran
/// `cargo build --offline` with nothing exported, so cargo built a *second*,
/// full target tree inside the project — ~8.5 GB and a ~5-minute cold build
/// against a 180-second command timeout — instead of reusing the warm one the
/// adapter already builds into.  It is exported as both `HOH_TARGET_DIR` (the
/// harness's own name, for the prompt text) and `CARGO_TARGET_DIR` (the name
/// cargo itself reads).
pub fn role_env(
    cfg: &HohConfig,
    run_id: &str,
    role: Role,
    iteration: u32,
    cwd: &Path,
    target_dir: Option<&Path>,
) -> BTreeMap<String, String> {
    let mut env: BTreeMap<String, String> = BTreeMap::new();
    env.insert("HOH_ROLE".to_string(), role.as_str().to_string());
    env.insert("HOH_RUN_ID".to_string(), run_id.to_string());
    env.insert("HOH_ITERATION".to_string(), iteration.to_string());

    let view = absolute_path(cwd);
    let artifact_dir = view.join(".hoh");
    // DR-28: scratch files live here and nowhere else; `.hoh` is excluded from
    // hashing and snapshots, so probes can never enter the candidate identity.
    let scratch_dir = artifact_dir.join("scratch");
    env.insert(
        "HOH_VIEW_DIR".to_string(),
        view.to_string_lossy().into_owned(),
    );
    env.insert(
        "HOH_ARTIFACT_DIR".to_string(),
        artifact_dir.to_string_lossy().into_owned(),
    );
    env.insert(
        "HOH_SCRATCH_DIR".to_string(),
        scratch_dir.to_string_lossy().into_owned(),
    );
    env.insert(
        "HOH_RUN_DIR".to_string(),
        absolute_path(&cfg.runtime.runs_dir.join(run_id))
            .to_string_lossy()
            .into_owned(),
    );
    env.insert(
        "HOH_WORKSPACE".to_string(),
        absolute_path(&cfg.runtime.workspace)
            .to_string_lossy()
            .into_owned(),
    );
    env.insert("HOH_TOOLS_ENDPOINT".to_string(), cfg.tools.endpoint.clone());
    // DR-69 ①: where this run publishes its game endpoint, so a role's own
    // `hoh tools call` process can resolve `running_game_*` at all.  Absolute
    // like every other path-shaped variable here.
    env.insert(
        crate::tools::endpoint::GAME_ROUTE_ENV.to_string(),
        absolute_path(&crate::tools::endpoint::game_route_path(
            &cfg.runtime.runs_dir.join(run_id),
        ))
        .to_string_lossy()
        .into_owned(),
    );
    env.insert("HOH_TOOLS_POLICY".to_string(), role.as_str().to_string());
    if let Some(target) = target_dir {
        let absolute = absolute_path(target);
        let value = absolute.to_string_lossy().into_owned();
        env.insert("HOH_TARGET_DIR".to_string(), value.clone());
        // The name cargo itself reads, so `cargo build --offline` inside the
        // role's shell reuses the adapter's warm directory without the role
        // having to pass `--target-dir`.
        env.insert("CARGO_TARGET_DIR".to_string(), value);
    }
    env.insert(
        "HOH_HOH_BIN".to_string(),
        std::env::current_exe()
            .map(|path| path.to_string_lossy().into_owned())
            .unwrap_or_default(),
    );
    // DR-19: mini's `LocalEnvironment` inherits the parent environment and only
    // overrides the keys it is handed, so a live credential in the HoH process
    // would be readable from the child shell.  Writing an explicit empty string
    // blocks the inheritance (the keys are written even when they do not exist,
    // which costs nothing).
    for (name, value) in crate::runtime::secrets::blocked_env() {
        env.insert(name, value);
    }
    env
}

/// Invoke the harness once, guaranteeing the trajectory directory (and the
/// DR-25/DR-28 scratch directory) exists first so a crash in step 1 still
/// leaves a trajectory behind.
pub async fn invoke_once(
    harness: &dyn Harness,
    inv: &RoleInvocation,
) -> anyhow::Result<RoleOutcome> {
    if let Some(parent) = inv.trajectory_path.parent() {
        std::fs::create_dir_all(parent)?;
    }
    std::fs::create_dir_all(inv.cwd.join(".hoh/scratch"))?;
    harness.invoke(inv).await
}

/// Substitute the loop variables of a role prompt.
pub fn render_prompt(template: &str, iteration: u32) -> String {
    render_prompt_for_shell(
        template,
        iteration,
        crate::runtime::shell::ShellFlavor::HOST,
    )
}

/// Round-1 write-path batch: the same substitution for an explicit target shell.
///
/// `{{shell_truth}}` is a whole section — the shell's dialect, the forbidden
/// command shapes, and the write/read directives — so the three role prompts
/// cannot drift apart in what they tell a role about its shell.  It is inserted
/// here, before `{{HOH_*}}` placeholders are resolved, because the section
/// itself spells the binary as `{{HOH_HOH_BIN}}`.
///
/// Retry batch: `{{completion_protocol}}` is the same device for the one
/// instruction that decides whether a role call ends or retries
/// ([`crate::prompts::COMPLETION_PROTOCOL`]).  It carries no `{{HOH_*}}`
/// placeholder, so its position in the chain is not load-bearing; it is kept
/// beside `{{shell_truth}}` because both are shared sections.
fn render_prompt_for_shell(
    template: &str,
    iteration: u32,
    flavor: crate::runtime::shell::ShellFlavor,
) -> String {
    template
        .replace("{{iteration}}", &iteration.to_string())
        .replace("{{ plan.md }}", ".hoh/plan.md")
        .replace(
            crate::prompts::COMPLETION_PROTOCOL_PLACEHOLDER,
            crate::prompts::COMPLETION_PROTOCOL,
        )
        .replace(
            crate::prompts::SHELL_TRUTH_PLACEHOLDER,
            &crate::prompts::shell_truth(flavor),
        )
}

/// DR-18: same substitution, plus the concrete step budget the role is running
/// under.  The numbers are rendered into the prompt so the wrap-up discipline
/// is never a vague instruction.
///
/// DR-66: the shell-variable placeholders are rendered for [`ShellFlavor::HOST`]
/// as well, because the delivered prompt is executed by the role's real shell
/// and nothing downstream re-renders it.
pub fn render_prompt_with_budget(
    template: &str,
    iteration: u32,
    limits: &crate::config::AgentLimits,
) -> String {
    render_prompt_with_budget_and_shell(
        template,
        iteration,
        limits,
        crate::runtime::shell::ShellFlavor::HOST,
    )
}

/// DR-66 ①: [`render_prompt_with_budget`] with an explicit target shell, so the
/// platform-specific form is testable without changing the host.
///
/// The order is load-bearing: every `{{…}}` placeholder is substituted first
/// (the budget numbers, the iteration, the DR-66 write deadline) and only then
/// are the `{{HOH_*}}` command placeholders turned into the shell's variable
/// syntax — [`assert_fully_rendered`] rejects a prompt that still carries
/// template syntax, so a missed placeholder cannot reach a role.
pub fn render_prompt_with_budget_and_shell(
    template: &str,
    iteration: u32,
    limits: &crate::config::AgentLimits,
    flavor: crate::runtime::shell::ShellFlavor,
) -> String {
    let rendered = render_prompt_for_shell(template, iteration, flavor)
        .replace("{{step_limit}}", &limits.step_limit.to_string())
        .replace("{{wrap_up_steps}}", &limits.wrap_up_steps.to_string())
        .replace(
            "{{write_deadline_steps}}",
            &crate::runtime::run_loop::developer_write_deadline(limits).to_string(),
        );
    crate::runtime::shell::render_command_vars(&rendered, flavor)
}

/// DR-18: the retry context handed to a wrap-up retry.  It forbids further
/// exploration, because the previous call already proved it cannot finish
/// inside its budget.
///
/// DR-86 ②: this constant is only the *instruction* half.  A retry that can
/// write the artifact is invoked with [`wrap_up_context`], which appends the
/// verbatim defect list; the bare constant is kept because it is the frozen
/// wording other records quote.
pub const WRAP_UP_RETRY_CONTEXT: &str =
    "STEP BUDGET EXHAUSTED. Your previous call ended with `LimitsExceeded` before it produced a \
     valid artifact. This is a small, final call: write the required artifact NOW, in a valid \
     form, and submit it. Do not explore, do not run experiments, do not start new work. A \
     minimal contract-valid artifact is the only acceptable outcome.";

/// DR-86 ②: the diagnostic half of a wrap-up retry, next to the instruction.
///
/// `smoke-t16`'s decisive corruption was written by the wrap-up retry whose
/// prompt carried **no diagnostic at all** ("write the required artifact NOW"),
/// while the repair retry that ran later received a verbatim failure list.  A
/// retry cannot fix what it is not told, so every write-capable retry now
/// carries the same class of evidence: the exact defects the runtime measured,
/// or an explicit statement that it measured none.
///
/// This is deliberately a *report*, never a repair: it quotes what is wrong and
/// forbids nothing the instruction above already forbids.
pub fn wrap_up_context(diagnostics: &[String]) -> String {
    let mut text = String::from(WRAP_UP_RETRY_CONTEXT);
    text.push_str("\n\n");
    if diagnostics.is_empty() {
        text.push_str(
            "WHAT IS WRONG (verbatim): the runtime's own checks recorded no quotable defect — it \
             could not establish that the artifact is usable, and no per-file reason was \
             measured. Do not go looking for one and do not re-explore the project: rewrite the \
             whole artifact you meant to deliver, in one write, and submit it.",
        );
    } else {
        text.push_str(
            "WHAT IS WRONG (verbatim, from the runtime's own checks of the artifact you must \
             rewrite):\n",
        );
        for item in diagnostics {
            text.push_str(&format!("- {item}\n"));
        }
        text.push_str(
            "Rewrite the **whole** file a defect names; do not patch the fragment you can see and \
             do not re-emit only one line.",
        );
    }
    text
}

/// Is this the exit status of a call that ran out of budget?
pub fn is_limits_exceeded(exit_status: &str) -> bool {
    // Round-4 repair: `StepBudgetExceeded` is the guard's own step-budget abort —
    // the live budget was exhausted at the step.  It is a limit in every sense
    // the wrap-up logic asks about, so it is accepted here; keeping a distinct
    // status is what lets a round say *which* budget ran out (mini's frozen
    // `step_limit` vs the guard's progress-responsive one).
    exit_status.eq_ignore_ascii_case("LimitsExceeded")
        || exit_status.eq_ignore_ascii_case(crate::harness::guard::STEP_BUDGET_STATUS)
}

/// The harness only ever receives fully rendered text: leftover jinja syntax
/// would be re-parsed as a template and silently change the prompt.
///
/// DR-68 ⑤: the check also covers **unresolved shell placeholders in both brace
/// forms**.  `{{`/`{%` only catches the template writer's own syntax; a
/// `format!` literal that wrote `{{HOH_X}}` collapses it to `{HOH_X}`, which is
/// not jinja, not a `{{HOH_*}}` template, and not resolvable by anything — so it
/// used to reach the role in the three task prompts and in the `TOOLS.md`
/// header (`smoke-t8`, 42 occurrences).  A prompt that still carries one is not
/// a prompt a role can execute, so refusing it here is the same contract, one
/// brace form wider.
pub fn assert_fully_rendered(label: &str, prompt: &str) -> anyhow::Result<()> {
    if prompt.contains("{{") || prompt.contains("{%") {
        anyhow::bail!(
            "{label} still contains template syntax after rendering; role text must be passed as \
             template variable values, never as template source"
        );
    }
    if crate::runtime::shell::contains_unresolved_command_var(prompt) {
        anyhow::bail!(
            "{label} still contains an unresolved shell placeholder after rendering; a `{{{{HOH_*}}}}` \
             template spelled inside a `format!` literal collapses to the single-brace form and no \
             renderer resolves it"
        );
    }
    Ok(())
}

/// Path of the attempt trajectory for one role.
pub fn attempt_trajectory(traj_dir: &Path, role: Role, attempt: u32) -> std::path::PathBuf {
    traj_dir.join(format!("{}.attempt{}.json", role.as_str(), attempt))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn render_prompt_replaces_iteration_and_leaves_no_jinja() {
        let rendered = render_prompt("iteration {{iteration}} of the loop", 3);
        assert_eq!(rendered, "iteration 3 of the loop");
        assert!(assert_fully_rendered("system", &rendered).is_ok());
        assert!(assert_fully_rendered("system", "{{oops}}").is_err());
    }

    /// DR-68 ⑤: the single-brace form is not jinja, so the old `{{`/`{%` check
    /// let it through; the completeness assertion must refuse it too.
    #[test]
    fn a_single_brace_shell_placeholder_is_not_fully_rendered() {
        assert!(assert_fully_rendered("system", "call %HOH_HOH_BIN% tools call x").is_ok());
        let error = assert_fully_rendered("system", "call {HOH_HOH_BIN} tools call x")
            .expect_err("the folded single-brace form is not a rendered prompt");
        assert!(
            error.to_string().contains("unresolved shell placeholder"),
            "{error}"
        );
        assert!(assert_fully_rendered("system", "{{HOH_HOH_BIN}} tools call x").is_err());
    }

    /// DR-86 ②: the wrap-up retry carries the instruction **and** the defect
    /// list; the bare constant is not the whole prompt any more.
    #[test]
    fn a_wrap_up_retry_carries_the_verbatim_defect_list() {
        let none = wrap_up_context(&[]);
        assert!(none.starts_with(WRAP_UP_RETRY_CONTEXT), "{none}");
        assert!(
            none.contains("no quotable defect"),
            "an empty diagnostic must be stated, not silently omitted: {none}"
        );

        let diagnostics = vec![
            "scenes/main.tscn: the delivered text is 20 byte(s) and carries no `[node ...]` \
             declaration"
                .to_string(),
        ];
        let text = wrap_up_context(&diagnostics);
        assert!(text.starts_with(WRAP_UP_RETRY_CONTEXT), "{text}");
        assert!(
            text.contains(diagnostics[0].as_str()),
            "the retry must quote the defect the runtime measured: {text}"
        );
        assert!(
            text.contains("Rewrite the **whole** file"),
            "the retry must ask for a whole write, not a patch: {text}"
        );
    }

    #[test]
    fn role_env_carries_every_required_variable() {
        let cfg = crate::config::load_config(&[]).unwrap();
        let cwd = std::path::PathBuf::from("F:/tmp/view");
        let env = role_env(&cfg, "run-1", Role::Tester, 2, &cwd, None);
        for key in [
            "HOH_ROLE",
            "HOH_RUN_ID",
            "HOH_ITERATION",
            "HOH_ARTIFACT_DIR",
            "HOH_TOOLS_ENDPOINT",
            "HOH_TOOLS_POLICY",
            "HOH_HOH_BIN",
            crate::tools::endpoint::GAME_ROUTE_ENV,
        ] {
            assert!(env.contains_key(key), "missing {key}");
        }
        assert_eq!(env.get("HOH_ROLE").unwrap(), "tester");
        assert_eq!(env.get("HOH_ITERATION").unwrap(), "2");
        assert!(env.get("HOH_ARTIFACT_DIR").unwrap().ends_with(".hoh"));
        // DR-69 ①: the route file is absolute and lives in this run's directory.
        let route = env.get(crate::tools::endpoint::GAME_ROUTE_ENV).unwrap();
        assert!(
            route.ends_with(crate::tools::endpoint::GAME_ROUTE_FILE),
            "{route}"
        );
        assert!(!std::path::Path::new(route).is_relative(), "{route}");
    }

    /// Round-1 write-path batch: the adapter's warm build cache must reach the
    /// role's shell, absolute, under both the harness's name and cargo's.
    #[test]
    fn role_env_exports_the_adapters_target_directory() {
        let cfg = crate::config::load_config(&[]).unwrap();
        let cwd = std::path::PathBuf::from("F:/tmp/view");
        let target = std::path::PathBuf::from("F:/tmp/workspace/../hof-bevy-shared-target");
        let env = role_env(&cfg, "run-1", Role::Developer, 1, &cwd, Some(&target));
        let exported = env.get("CARGO_TARGET_DIR").expect("cargo's variable");
        assert_eq!(env.get("HOH_TARGET_DIR"), Some(exported));
        assert!(
            !std::path::Path::new(exported).is_relative(),
            "the target directory must be absolute: {exported}"
        );
        assert!(exported.ends_with("hof-bevy-shared-target"), "{exported}");

        // An adapter with no target directory exports neither name: inventing a
        // value would make cargo build somewhere nobody measured.
        let none = role_env(&cfg, "run-1", Role::Developer, 1, &cwd, None);
        assert!(!none.contains_key("CARGO_TARGET_DIR"));
        assert!(!none.contains_key("HOH_TARGET_DIR"));
    }
}
