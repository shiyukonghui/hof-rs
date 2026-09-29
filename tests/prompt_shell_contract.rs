//! DR-66 ⑤ — the two string-containment assertions that were **structurally
//! always green**, turned into executable contracts.
//!
//! `smoke-t7`'s Developer gave up ~30 % of its step budget to shell dialect
//! errors while `cargo test` stayed green, because the only thing the suite
//! checked was that certain substrings were present in the prompt text:
//!
//! * `tests/artifact_hygiene.rs:112-115` asserted
//!   `prompt.contains("$HOH_SCRATCH_DIR")`;
//! * `tests/developer_contract.rs:57-74` asserted
//!   `godot_dev.contains("$HOH_HOH_BIN tools call")`.
//!
//! Neither executes anything.  A needle that cannot run is still a needle.  The
//! tests below take the same claims and make them **executable**: they extract
//! the harness paths out of the delivered text, render them for the real shell,
//! and drive a real `LocalEnvironment` — the type the runtime hands the role
//! (`src/harness/mini.rs:53-62`).
//!
//! This file owns the dynamic half; the two original tests now assert on the
//! *delivered* text (`tests/common/mod.rs::delivered_prompt` /
//! `delivered_skill`) so their static half can no longer be satisfied by
//! template source.

mod common;

use std::collections::BTreeMap;
use std::path::{Path, PathBuf};

use hof_rs::prompts;
use hof_rs::runtime::invoke::render_prompt_with_budget_and_shell;
use hof_rs::runtime::shell::ShellFlavor;
use mini_swe_agent::{Action, Environment, LocalEnvironment};
use serde_json::Value;

// ---------------------------------------------------------------------------
// Fixture: a real role shell
// ---------------------------------------------------------------------------

fn role_env(view: &Path) -> BTreeMap<String, String> {
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
    env
}

async fn run(view: &Path, command: &str) -> (String, i32) {
    let environment = LocalEnvironment::new(mini_swe_agent::environments::LocalEnvironmentConfig {
        cwd: view.to_string_lossy().into_owned(),
        env: role_env(view)
            .into_iter()
            .map(|(key, value)| (key, Value::String(value)))
            .collect(),
        timeout: 60,
    });
    let output = environment
        .execute(&Action::new(command), None, Some(60))
        .await
        .expect("the environment must return an Output");
    (output.output, output.returncode)
}

fn view_with_scratch() -> (tempfile::TempDir, PathBuf) {
    let temp = tempfile::tempdir().unwrap();
    let view = temp.path().join("view");
    std::fs::create_dir_all(view.join(".hoh/scratch")).unwrap();
    (temp, view)
}

/// Create the `--args-file` targets a command names, resolving `$VAR`/`%VAR%`
/// against the role environment.  A token that does not resolve is skipped, so
/// a test can never create a stray directory in the repository root.
fn materialize_args_files(command: &str, view: &Path) {
    let env = role_env(view);
    let tokens: Vec<&str> = command.split_whitespace().collect();
    for window in tokens.windows(2) {
        if window[0] != "--args-file" {
            continue;
        }
        let raw = window[1].trim_matches('"');
        let Some(path) = resolve_path(raw, &env, view) else {
            continue;
        };
        std::fs::create_dir_all(path.parent().unwrap_or(view)).unwrap();
        std::fs::write(&path, b"{}").unwrap();
    }
}

fn resolve_path(raw: &str, env: &BTreeMap<String, String>, view: &Path) -> Option<PathBuf> {
    let mut resolved = raw.to_string();
    for (name, value) in env {
        resolved = resolved.replace(&format!("${name}"), value);
        resolved = resolved.replace(&format!("%{name}%"), value);
    }
    if resolved.starts_with('$') || resolved.starts_with('%') {
        return None;
    }
    let path = PathBuf::from(&resolved);
    Some(if path.is_absolute() {
        path
    } else {
        view.join(path)
    })
}

/// Everything between the ```` ``` ```` fences, in order.
fn fenced_blocks(text: &str) -> Vec<String> {
    let mut blocks = Vec::new();
    let mut current: Vec<&str> = Vec::new();
    let mut inside = false;
    for line in text.lines() {
        if line.trim_start().starts_with("```") {
            if inside {
                blocks.push(current.join("\n"));
                current.clear();
            }
            inside = !inside;
            continue;
        }
        if inside {
            current.push(line);
        }
    }
    blocks
}

/// The shell variable the *host* shell expands for `HOH_SCRATCH_DIR`.
fn scratch_var() -> String {
    ShellFlavor::HOST.var("HOH_SCRATCH_DIR")
}

// ---------------------------------------------------------------------------
// ① the scratch-discipline contract is executable
// ---------------------------------------------------------------------------

/// `[scratch-discipline]` tells the Developer to write temporary files under
/// `HOH_SCRATCH_DIR` "inside `.hoh/`, which is excluded from the artifact hash".
///
/// Static form (kept in `tests/artifact_hygiene.rs`): the delivered text names
/// the variable.  Executable form (here): a writer spelled with **that very
/// token** creates a file, and the file lands in the hash-excluded scratch
/// directory — the property the prompt promises.
#[tokio::test]
async fn the_scratch_discipline_the_prompts_state_really_works() {
    let (_temp, view) = view_with_scratch();
    let developer = delivered(hof_rs::prompts::DEVELOPER_PROMPT);
    let scratch = scratch_var();

    assert!(
        developer.contains(&scratch),
        "developer.md must name the scratch directory as `{scratch}` in the delivered text"
    );
    assert!(
        developer.contains(".hoh/"),
        "developer.md must state that the scratch directory is inside `.hoh/`"
    );

    // Drive the promise: write through the variable the prompt names.
    let command = if cfg!(windows) {
        // `echo <text> > "%HOH_SCRATCH_DIR%\marker.txt"`
        format!("echo dr66-scratch > \"{scratch}\\\\marker.txt\"")
    } else {
        format!("printf '%s' dr66-scratch > \"{scratch}/marker.txt\"")
    };
    let (output, returncode) = run(&view, &command).await;
    assert_eq!(
        returncode, 0,
        "the writer the prompt describes must run: {command:?}\n{output}"
    );

    let landed = view.join(".hoh/scratch/marker.txt");
    let stray = view.join("marker.txt");
    assert!(
        landed.is_file(),
        "the scratch writer must land inside the `.hoh/scratch` directory, not {stray:?}"
    );
    assert!(
        !stray.exists(),
        "nothing may land in the project root: the file belongs under `.hoh/scratch`"
    );
    // And the promise about the hash is true for that location: `.hoh` is in
    // the runtime's always-excluded set.
    let excludes = hof_rs::runtime::policy::HashExcludes::new(
        hof_rs::config::load_config(&[])
            .unwrap()
            .adapter
            .godot
            .cache_excludes,
    )
    .merged();
    assert!(
        hof_rs::runtime::policy::is_excluded(".hoh/scratch/marker.txt", &excludes),
        "`.hoh/scratch/**` must be excluded from the artifact hash, excludes={excludes:?}"
    );
}

/// The same discipline as written in the skills.  The recipes use the variable
/// inside quotes, so the claim is: the quoted form is what the shell expands.
#[tokio::test]
async fn the_skill_scratch_writer_runs_and_lands_under_scratch() {
    let (_temp, view) = view_with_scratch();
    let dev_skill = delivered_skill("godot-dev.md");
    let scratch = scratch_var();

    let block = fenced_blocks(&dev_skill)
        .into_iter()
        .find(|block| block.contains(&scratch) && block.contains("errors.json"))
        .unwrap_or_else(|| {
            panic!("the skill must show a quoted scratch writer using {scratch}:\n{dev_skill}")
        });
    // Take only the "good" line; the block also shows a deliberately bad one.
    let good = block
        .lines()
        .find(|line| line.contains(&scratch) && line.contains("errors.json"))
        .expect("the good example line")
        .trim();

    let (output, returncode) = run(&view, good).await;
    assert_eq!(
        returncode, 0,
        "the skill's own scratch recipe must run: {good:?}\n{output}"
    );
    assert!(
        view.join(".hoh/scratch/errors.json").is_file(),
        "`{good}` must create `.hoh/scratch/errors.json`, not a stray file"
    );
    assert!(
        !view.join("errors.json").exists(),
        "the recipe must not drop `errors.json` into the project root"
    );
}

// ---------------------------------------------------------------------------
// ② the recipe-book contract is executable
// ---------------------------------------------------------------------------

/// `godot-dev.md` is a recipe book: its commands must be runnable in the role's
/// real shell.
///
/// Static form (kept in `tests/developer_contract.rs`): the delivered text
/// contains `%HOH_HOH_BIN% tools call` (Windows) or `$HOH_HOH_BIN tools call`.
/// Executable form (here): the **first** concrete recipe line is extracted, a
/// stub binary is put at the path the runtime publishes as `HOH_HOH_BIN`, and
/// the line is executed in a real `LocalEnvironment`.  The stub records its
/// argument list, so the marker proves that this command — not a rewritten
/// copy of it — started the binary.
#[tokio::test]
async fn the_recipe_books_first_concrete_command_runs_in_the_role_shell() {
    let (_temp, view) = view_with_scratch();
    let bin = stub_binary(&view);

    let dev_skill = delivered_skill("godot-dev.md");
    let (command, tool) = first_concrete_recipe(&dev_skill);
    assert!(
        command.contains(&tool),
        "the extracted command must name the tool it was extracted for: {command:?}"
    );
    materialize_args_files(&command, &view);

    let nonce = "dr66-recipe-nonce";
    let command = format!("{command} -- {nonce}");
    let mut environment = role_env(&view);
    environment.insert("HOH_HOH_BIN".into(), bin.to_string_lossy().into_owned());
    let (output, returncode) = run_env(&view, &command, environment).await;

    assert_eq!(
        returncode, 0,
        "the recipe book's command must run in the role's real shell: {command:?}\n{output}"
    );
    let marker = std::fs::read_to_string(view.join(".hoh/scratch/recipe.txt")).unwrap_or_default();
    assert!(
        marker.contains(&tool),
        "the stub must have been started by this exact line; it recorded {marker:?}"
    );
    assert!(
        marker.contains(nonce),
        "the stub must have received the whole argument list; it recorded {marker:?}"
    );
}

/// The first `HOH_HOH_BIN … tools call <tool> … --args-file …` line in the
/// skill's fenced blocks, with no angle-bracket fill-in left.
fn first_concrete_recipe(skill: &str) -> (String, String) {
    for block in fenced_blocks(skill) {
        for line in block.lines() {
            let line = line.trim();
            if !line.contains("tools call") || line.contains('<') || line.contains('>') {
                continue;
            }
            if !line.starts_with("%HOH_") && !line.starts_with("$HOH_") {
                continue;
            }
            let tokens: Vec<&str> = line.split_whitespace().collect();
            let Some(index) = tokens.iter().position(|token| *token == "call") else {
                continue;
            };
            let Some(tool) = tokens.get(index + 1) else {
                continue;
            };
            return (line.to_string(), tool.to_string());
        }
    }
    panic!("godot-dev.md has no concrete `tools call` recipe");
}

// ---------------------------------------------------------------------------
// helpers
// ---------------------------------------------------------------------------

fn delivered(template: &str) -> String {
    render_prompt_with_budget_and_shell(
        template,
        1,
        &hof_rs::config::AgentLimits::default(),
        ShellFlavor::HOST,
    )
}

fn delivered_skill(name: &str) -> String {
    prompts::skill_document(name, ShellFlavor::HOST)
        .unwrap_or_else(|| panic!("skill {name} is not embedded"))
}

/// A real `HOH_HOH_BIN`: a `.cmd` on Windows (cmd cannot start an extensionless
/// shebang script) and a `sh` script elsewhere.  It records its arguments.
fn stub_binary(view: &Path) -> PathBuf {
    let name = if cfg!(windows) {
        "hoh_stub.cmd"
    } else {
        "hoh_stub.sh"
    };
    let path = view.join(".hoh/stub").join(name);
    std::fs::create_dir_all(path.parent().unwrap()).unwrap();
    let body = if cfg!(windows) {
        "@echo off\r\necho %* > \"%HOH_SCRATCH_DIR%\\recipe.txt\"\r\n"
    } else {
        "#!/bin/sh\nprintf '%s' \"$*\" > \"$HOH_SCRATCH_DIR/recipe.txt\"\n"
    };
    std::fs::write(&path, body).unwrap();
    path
}

async fn run_env(view: &Path, command: &str, env: BTreeMap<String, String>) -> (String, i32) {
    let environment = LocalEnvironment::new(mini_swe_agent::environments::LocalEnvironmentConfig {
        cwd: view.to_string_lossy().into_owned(),
        env: env
            .into_iter()
            .map(|(key, value)| (key, Value::String(value)))
            .collect(),
        timeout: 60,
    });
    let output = environment
        .execute(&Action::new(command), None, Some(60))
        .await
        .expect("the environment must return an Output");
    (output.output, output.returncode)
}
