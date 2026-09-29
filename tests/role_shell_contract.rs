//! DR-66 ② — the **prompt↔real-shell contract**, as an executable test.
//!
//! `smoke-t7`'s Developer burned 25–30 % of its 150-step budget before its
//! first successful `hoh tools call`: the prompts, the generated `TOOLS.md`,
//! the skills and the evidence playbook all instructed the role in **POSIX**
//! syntax (`$HOH_HOH_BIN tools call …`), while the role's real shell on Windows
//! is `cmd.exe` (mini `rust/src/environments/local.rs:66-76`).  The trajectory
//! records the result verbatim (`messages[76]`):
//!
//! ```text
//! '$HOH_HOH_BIN" tools call editor_get_errors --args-file "$HOH_SCRATCH_DIR' is not
//! recognized as an internal or external command, operable program or batch file.
//! ```
//!
//! The pre-DR-66 tests could not see this: `tests/artifact_hygiene.rs:112-115`
//! and `tests/developer_contract.rs:57-74` only assert that a *substring* is
//! present, so they stay green no matter what that substring does when the role
//! actually runs it.
//!
//! This test closes the gap by **extracting a command from the delivered prompt
//! text and executing it in a real `LocalEnvironment`** — the same type and the
//! same configuration shape (`src/harness/mini.rs:53-62`) the runtime uses.
//!
//! ## The extraction rule (explicit, so the test cannot drift)
//!
//! 1. The command source is the role's **delivered** text: the rendered system
//!    prompt, the rendered task prompt, and the two skill bodies as they are
//!    injected into the role view (`src/runtime/run_loop.rs` `write_inputs`).
//! 2. Only fenced code blocks (```` ``` ````) are scanned; a candidate command
//!    is a line whose first token, after leading whitespace, is a `{{HOH_*}}`
//!    placeholder (the templates name every harness path through one) and whose
//!    text contains `tools call`.
//! 3. A candidate is **skipped** when it still carries an angle-bracket
//!    fill-in (`<tool_name>`, `<name>`): those are syntax templates, not
//!    commands, and substituting guessed values would be a different claim.
//! 4. `{{HOH_*}}` placeholders resolve to the value `role_env` gives for that
//!    name, rendered in the target shell's variable syntax.  On Windows that is
//!    `%HOH_HOH_BIN%` (cmd), on POSIX `$HOH_HOH_BIN` (sh).
//! 5. A `--args-file <path>` argument is materialized with `{}`, because the
//!    stub never reads it; its presence is what the command line asserts.
//!
//! ## The per-platform expectation
//!
//! * The **host** rendering must yield a command that exits 0 and writes the
//!   marker: on Windows that is the `%HOH_*%` form, on POSIX the `$HOH_*` form.
//! * The **cross** rendering is the control that proves the test is not hollow:
//!   on Windows the POSIX form must fail (cmd dialect), on POSIX the cmd form
//!   must fail.  The failure text is asserted to be the shell's own dialect
//!   error, not a missing-file error from the stub, so a broken fixture cannot
//!   masquerade as a correct RED.

mod common;

use std::collections::BTreeMap;
use std::path::{Path, PathBuf};

use hof_rs::adapter::ProjectAdapter;
use hof_rs::config::{AgentLimits, GodotConfig};
use hof_rs::prompts;
use hof_rs::runtime::invoke::render_prompt_with_budget_and_shell;
use hof_rs::runtime::shell::{self, ShellFlavor};
use mini_swe_agent::{Action, Environment, LocalEnvironment};
use serde_json::Value;

// ---------------------------------------------------------------------------
// Fixture
// ---------------------------------------------------------------------------

/// The `HOH_*` environment the runtime hands a role (same shape as
/// `src/runtime/invoke.rs::role_env`).
fn fixture_env(view: &Path) -> BTreeMap<String, String> {
    let artifact = view.join(".hoh");
    let mut env = BTreeMap::new();
    env.insert("HOH_VIEW_DIR".into(), view.to_string_lossy().into_owned());
    env.insert(
        "HOH_ARTIFACT_DIR".into(),
        artifact.to_string_lossy().into_owned(),
    );
    env.insert(
        "HOH_SCRATCH_DIR".into(),
        artifact.join("scratch").to_string_lossy().into_owned(),
    );
    env.insert("HOH_HOH_BIN".into(), stub_path(view));
    env
}

/// The stub `HOH_HOH_BIN`: a real file the shell can start.  On Windows a
/// `.cmd` (cmd.exe cannot start an extensionless shebang script), on POSIX a
/// `sh` script.  It writes the nonce it was given, so a marker can only exist
/// if *this* command line really ran.
fn stub_path(view: &Path) -> String {
    let name = if cfg!(windows) { "hoh_stub.cmd" } else { "hoh_stub.sh" };
    view.join(".hoh").join("stub").join(name).to_string_lossy().into_owned()
}

fn write_stub(view: &Path) -> PathBuf {
    let path = PathBuf::from(stub_path(view));
    std::fs::create_dir_all(path.parent().unwrap()).unwrap();
    let body = if cfg!(windows) {
        "@echo off\r\necho %* > \"%HOH_SCRATCH_DIR%\\marker.txt\"\r\n"
    } else {
        "#!/bin/sh\nprintf '%s' \"$*\" > \"$HOH_SCRATCH_DIR/marker.txt\"\n"
    };
    std::fs::write(&path, body).unwrap();
    path
}

fn marker_path(view: &Path) -> PathBuf {
    view.join(".hoh/scratch/marker.txt")
}

fn new_environment(view: &Path) -> LocalEnvironment {
    LocalEnvironment::new(mini_swe_agent::environments::LocalEnvironmentConfig {
        cwd: view.to_string_lossy().into_owned(),
        env: fixture_env(view)
            .into_iter()
            .map(|(key, value)| (key, Value::String(value)))
            .collect(),
        timeout: 60,
    })
}

// ---------------------------------------------------------------------------
// The delivered documents (exactly what a role is handed)
// ---------------------------------------------------------------------------

/// `(label, delivered text)` for the developer role: the system prompt and the
/// task prompt as `run_loop.rs` renders them, plus the skills and the evidence
/// playbook it writes into the role view.
fn developer_documents(flavor: ShellFlavor) -> Vec<(String, String)> {
    let limits = AgentLimits::default();
    let mut documents = Vec::new();
    for (label, template) in [
        ("developer.md", prompts::DEVELOPER_PROMPT),
        ("planner.md", prompts::PLANNER_PROMPT),
        ("tester.md", prompts::TESTER_PROMPT),
    ] {
        documents.push((
            label.to_string(),
            render_prompt_with_budget_and_shell(template, 1, &limits, flavor),
        ));
    }
    documents.push((
        "developer_task".to_string(),
        prompts::developer_task_with_shell(1, flavor),
    ));
    documents.push((
        "planner_task".to_string(),
        prompts::planner_task_with_shell(1, flavor),
    ));
    documents.push((
        "tester_task".to_string(),
        prompts::tester_task_with_shell(1, flavor),
    ));
    documents.extend(prompts::skill_documents(flavor));
    let adapter = hof_rs::adapter::godot::GodotAdapter::new(
        GodotConfig {
            editor_binary: PathBuf::new(),
            cache_excludes: vec![".godot".into()],
            main_scene: "res://scenes/main.tscn".into(),
        },
        true,
    );
    documents.push((
        "evidence_playbook".to_string(),
        shell::render_command_vars(&adapter.evidence_playbook(), flavor),
    ));
    documents
}

/// Rule §2/§3: the first command-shaped line that carries no angle-bracket
/// fill-in, from the first document that has one, in delivery order.
fn extract_command(documents: &[(String, String)]) -> (String, String) {
    for (label, text) in documents {
        for line in fenced_lines(text) {
            let trimmed = line.trim();
            let Some(first) = trimmed.split_whitespace().next() else {
                continue;
            };
            if !first.starts_with("%HOH_") && !first.starts_with("$HOH_") {
                continue;
            }
            if !trimmed.contains("tools call") {
                continue;
            }
            if trimmed.contains('<') || trimmed.contains('>') {
                continue;
            }
            return (label.clone(), trimmed.to_string());
        }
    }
    panic!("no extractable `tools call` command in any delivered document");
}

/// Lines inside fenced code blocks only.
fn fenced_lines(text: &str) -> Vec<&str> {
    let mut lines = Vec::new();
    let mut inside = false;
    for line in text.lines() {
        if line.trim_start().starts_with("```") {
            inside = !inside;
            continue;
        }
        if inside {
            lines.push(line);
        }
    }
    lines
}

// ---------------------------------------------------------------------------
// Execution
// ---------------------------------------------------------------------------

/// Materialize a `--args-file` target (rule §5) so the command line is runnable.
///
/// The path is resolved against the role environment first: a token that does
/// not resolve (a foreign-dialect spelling) is skipped, so this helper can never
/// create a stray `$HOH_ARTIFACT_DIR` directory in the repository root.
fn materialize_args_files(command: &str, view: &Path) {
    let env = fixture_env(view);
    let tokens: Vec<&str> = command.split_whitespace().collect();
    for window in tokens.windows(2) {
        if window[0] != "--args-file" {
            continue;
        }
        let raw = window[1].trim_matches('"');
        let mut resolved = raw.to_string();
        for (name, value) in &env {
            resolved = resolved.replace(&format!("${name}"), value);
            resolved = resolved.replace(&format!("%{name}%"), value);
        }
        if resolved.starts_with('$') || resolved.starts_with('%') {
            continue;
        }
        let path = PathBuf::from(&resolved);
        let path = if path.is_absolute() { path } else { view.join(path) };
        std::fs::create_dir_all(path.parent().unwrap_or(view)).unwrap();
        std::fs::write(&path, b"{}").unwrap();
    }
}

/// Run one extracted command line in a real `LocalEnvironment`.
async fn run_extracted(view: &Path, command: &str) -> (String, i32) {
    materialize_args_files(command, view);
    let environment = new_environment(view);
    let action = Action::new(command);
    let output = environment
        .execute(&action, None, Some(60))
        .await
        .expect("the environment must return an Output");
    (output.output, output.returncode)
}

// ---------------------------------------------------------------------------
// ① the host rendering really runs (the RED gate on Windows)
// ---------------------------------------------------------------------------

/// The delivered command executed in the role's real shell must exit 0 and
/// leave the marker.
///
/// **Expected RED before the DR-66 fix, on Windows**: the delivered line begins
/// `$HOH_HOH_BIN` and cmd answers `'$HOH_HOH_BIN" tools call …' is not
/// recognized as an internal or external command` (recorded verbatim in
/// `smoke-t7`'s developer trajectory, `messages[76]`).
#[tokio::test]
async fn the_command_the_prompt_hands_the_developer_runs_in_the_real_shell() {
    let temp = tempfile::tempdir().unwrap();
    let view = temp.path().join("view");
    std::fs::create_dir_all(view.join(".hoh/scratch")).unwrap();
    write_stub(&view);

    let documents = developer_documents(ShellFlavor::HOST);
    let (label, command) = extract_command(&documents);

    let nonce = "dr66-host-nonce";
    // The stub records its whole argument list, so the nonce goes right where
    // the tool name would be: the marker can only carry it if this exact
    // command line started this exact stub.
    let command = command.replace("tools call ", &format!("tools call {nonce} "));
    let (output, returncode) = run_extracted(&view, &command).await;

    assert_eq!(
        returncode, 0,
        "the command the prompt gives the developer [{label}] must run in the role's real shell \
         ({command:?}); the shell answered: {output}"
    );
    let marker = std::fs::read_to_string(marker_path(&view)).unwrap_or_default();
    assert!(
        marker.contains(nonce),
        "HOH_HOH_BIN must really have been executed by the delivered command line; the stub \
         recorded {marker:?}"
    );
}

// ---------------------------------------------------------------------------
// ② the cross-platform control proves the test is not hollow
// ---------------------------------------------------------------------------

/// The *other* platform's syntax must fail, and fail as a **shell dialect**
/// error — otherwise the fixture (not the syntax) is what broke.
#[tokio::test]
async fn the_other_platforms_syntax_fails_in_the_roles_real_shell() {
    let temp = tempfile::tempdir().unwrap();
    let view = temp.path().join("view");
    std::fs::create_dir_all(view.join(".hoh/scratch")).unwrap();
    write_stub(&view);

    let foreign = match ShellFlavor::HOST {
        ShellFlavor::Windows => ShellFlavor::Posix,
        ShellFlavor::Posix => ShellFlavor::Windows,
    };
    let documents = developer_documents(foreign);
    let (label, command) = extract_command(&documents);
    let (output, returncode) = run_extracted(&view, &command).await;

    assert_ne!(
        returncode, 0,
        "the {foreign:?} form [{label}] must not succeed in the {host:?} shell: {command:?}\n{output}",
        host = ShellFlavor::HOST
    );
    assert!(
        !marker_path(&view).exists(),
        "the foreign form must not have started the stub; output: {output}"
    );
    // The failing command must be the *syntax*, not a missing stub or a bad
    // path.  This assertion is what makes the RED auditable from the test itself:
    // on Windows it is the cmd analogue of `smoke-t7`'s recorded
    // `'$HOH_HOH_BIN" tools call …' is not recognized as an internal or external command`.
    assert!(
        output.contains("HOH_HOH_BIN"),
        "the dialect error must name the variable that could not be expanded: {output}"
    );
    assert!(
        returncode != 0 && !output.trim().is_empty(),
        "the dialect error must be real shell output, not silently swallowed: rc={returncode} \
         out={output:?}"
    );
}

/// The delayed, non-hollow control: the *host-correct* spelling of the very
/// same command must succeed even though the document offered the foreign one.
/// This separates "the fixture is broken" from "the syntax is wrong".
#[tokio::test]
async fn the_platform_correct_form_succeeds_where_the_foreign_one_is_offered() {
    let temp = tempfile::tempdir().unwrap();
    let view = temp.path().join("view");
    std::fs::create_dir_all(view.join(".hoh/scratch")).unwrap();
    write_stub(&view);

    let foreign = match ShellFlavor::HOST {
        ShellFlavor::Windows => ShellFlavor::Posix,
        ShellFlavor::Posix => ShellFlavor::Windows,
    };
    let documents = developer_documents(foreign);
    let (label, foreign_command) = extract_command(&documents);
    // The *same* command, spelled for the real shell.
    let host_command = shell::rewrite_var_dialect(&foreign_command, ShellFlavor::HOST);

    let nonce = "dr66-control-nonce";
    let host_command = host_command.replace("tools call ", &format!("tools call {nonce} "));
    let (output, returncode) = run_extracted(&view, &host_command).await;

    assert_ne!(
        foreign_command, host_command,
        "the {foreign:?} document must actually offer a different spelling [{label}]; otherwise \
         this control proves nothing"
    );
    assert_eq!(
        returncode, 0,
        "the control must succeed, otherwise the RED above proves nothing: {host_command:?}\n{output}"
    );
    let marker = std::fs::read_to_string(marker_path(&view)).unwrap_or_default();
    assert!(
        marker.contains(nonce),
        "the control must really start the stub; it recorded {marker:?}"
    );
}

// ---------------------------------------------------------------------------
// ③ no delivered document may still carry a raw placeholder
// ---------------------------------------------------------------------------

/// A `{{HOH_*}}` left in delivered text would reach the role as template
/// syntax — and, worse, a line that begins with one is exactly the shape this
/// test's rule looks for.  Either way the contract is broken.
#[test]
fn no_delivered_document_carries_an_unrendered_shell_placeholder() {
    for (label, text) in developer_documents(ShellFlavor::HOST) {
        assert!(
            !shell::contains_unresolved_command_var(&text),
            "{label} still carries a `{{{{HOH_*}}}}` template in delivered text"
        );
    }
}

/// The full delivery set of `TOOLS.md` must be platform-correct too: it is
/// generated for a role, not for the host of whoever built the binary.
#[test]
fn the_generated_tools_index_uses_the_target_shell_syntax() {
    let schemas = hof_rs::tools::index::embedded_tool_schemas();
    for (flavor, marker) in [
        (ShellFlavor::Windows, "%HOH_HOH_BIN%"),
        (ShellFlavor::Posix, "$HOH_HOH_BIN"),
    ] {
        let rendered = hof_rs::tools::index::render_tools_markdown_for(
            hof_rs::model::Role::Developer,
            &schemas,
            flavor,
        );
        assert!(
            rendered.contains(marker),
            "TOOLS.md for {flavor:?} must spell the binary as {marker}"
        );
        let wrong = if flavor == ShellFlavor::Windows {
            "$HOH_HOH_BIN"
        } else {
            "%HOH_HOH_BIN%"
        };
        assert!(
            !rendered.contains(wrong),
            "TOOLS.md for {flavor:?} must not spell the binary as {wrong}"
        );
        assert!(!shell::contains_unresolved_command_var(&rendered));
    }
}
