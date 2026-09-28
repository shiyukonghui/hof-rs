//! DR-40 — `hoh init`: preparing `A₀` without the editor or the model.
//!
//! `--fresh-workspace` used to be reachable only through `hoh run`, which runs
//! the doctor pre-check first — a circular dependency: emptying and rebuilding
//! `A₀` needs the editor closed, but the run refuses to start without 9877
//! online.  `hoh init` is the way out, and it must never touch MCP, the model
//! endpoint or a secret.
//!
//! Everything here runs offline: the model base URL and the MCP endpoint are
//! pointed at a closed port, and the API-key variables are removed from the
//! child's environment.

use std::path::{Path, PathBuf};
use std::process::{Command, Output};

fn binary() -> PathBuf {
    PathBuf::from(env!("CARGO_BIN_EXE_hoh"))
}

fn manifest() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
}

/// Run `hoh` with the network-dependent probes pointed at a closed local port
/// and no model secret in the environment.
fn hoh(args: &[&str]) -> Output {
    Command::new(binary())
        .args(args)
        .current_dir(manifest())
        .env_remove("HOH_MODEL_API_KEY")
        .env_remove("OPENAI_API_KEY")
        .output()
        .expect("the hoh binary must be runnable")
}

fn write(path: &Path, content: &str) {
    if let Some(parent) = path.parent() {
        std::fs::create_dir_all(parent).unwrap();
    }
    std::fs::write(path, content).unwrap();
}

/// `-c` overrides that keep every probe off the real endpoints.
fn offline_overrides() -> Vec<String> {
    vec![
        "model.base_url=http://127.0.0.1:1/v1".to_string(),
        "tools.endpoint=http://127.0.0.1:1/mcp".to_string(),
        // DR-44: these tests must not execute an engine binary either.
        "adapter.godot.editor_binary=".to_string(),
    ]
}

/// Append every override as `-c <override>` and hand back the argv.
fn argv(args: &[String]) -> Vec<String> {
    let mut argv = args.to_vec();
    for override_spec in offline_overrides() {
        argv.push("-c".to_string());
        argv.push(override_spec);
    }
    argv
}

fn run(args: &[String]) -> Output {
    let owned = argv(args);
    let borrowed: Vec<&str> = owned.iter().map(String::as_str).collect();
    hoh(&borrowed)
}

/// DR-40 ①/②: no MCP, no model endpoint, no key — `hoh init --fresh-workspace`
/// still rebuilds `A₀` and enables the MCP plugin.
#[test]
fn init_rebuilds_a0_without_mcp_or_a_model_endpoint() {
    let temp = tempfile::tempdir().unwrap();
    let workspace = temp.path().join("workspace");
    write(&workspace.join("leftover.txt"), "from an older attempt\n");
    write(
        &workspace.join("project.godot"),
        "; stale\nconfig_version=5\n",
    );
    let args = vec![
        "init".to_string(),
        "--fresh-workspace".to_string(),
        "--project".to_string(),
        workspace.display().to_string(),
    ];
    let output = run(&args);
    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);
    assert_eq!(
        output.status.code(),
        Some(0),
        "`hoh init` must succeed offline; stdout: {stdout} stderr: {stderr}"
    );
    assert!(
        !workspace.join("leftover.txt").exists(),
        "--fresh-workspace must empty the workspace first"
    );
    let project = std::fs::read_to_string(workspace.join("project.godot"))
        .expect("init must write project.godot");
    // DR-41 (supersedes DR-4): the rebuilt A0 must NOT enable the retired
    // GDExtension channel; the MCP channel is the engine's native module (C4).
    assert!(
        !project.contains("[editor_plugins]"),
        "the rebuilt A0 must not enable an editor plugin (DR-41): {project}"
    );
    assert!(
        !project.contains("res://addons/godot_mcp_rs"),
        "the retired plugin must not be named anywhere (DR-41): {project}"
    );
    assert!(
        !workspace.join("addons/godot_mcp_rs").exists(),
        "no bundled addon may be installed (DR-41)"
    );
    assert!(
        !workspace.join("ADDON_MISSING.txt").exists(),
        "there is no addon to miss any more (DR-41)"
    );
    assert!(
        workspace.join("scenes/main.tscn").is_file(),
        "A0 must contain the minimal project"
    );
}

/// DR-40 ③: a non-empty workspace without `--force-init` is a *usage* situation
/// reported as "adapter unavailable" (exit 4) — and nothing is touched.
#[test]
fn init_refuses_a_non_empty_workspace_without_force() {
    let temp = tempfile::tempdir().unwrap();
    let workspace = temp.path().join("workspace");
    write(&workspace.join("keep.txt"), "precious\n");

    let args = vec![
        "init".to_string(),
        "--project".to_string(),
        workspace.display().to_string(),
    ];
    let output = run(&args);
    assert_eq!(
        output.status.code(),
        Some(4),
        "an unusable adapter is exit 4; stderr: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert_eq!(
        std::fs::read_to_string(workspace.join("keep.txt")).unwrap(),
        "precious\n",
        "a refused init must not modify the workspace"
    );
    assert!(
        !workspace.join("project.godot").exists(),
        "a refused init must not scaffold anything"
    );
}

/// DR-53 (DEF-2): an `[editor_plugins]` section whose `enabled` line is **not**
/// a `PackedStringArray(...)` (here `enabled=true`) must not be modified at all,
/// and `hoh init` must say why instead of silently deleting the section.  The
/// pre-DR-53 code read a parse failure as "the list became empty" and rewrote
/// the file down to `config_version=5\n\n`.
#[test]
fn init_leaves_a_malformed_enabled_line_untouched_and_says_why() {
    let temp = tempfile::tempdir().unwrap();
    let workspace = temp.path().join("workspace");
    let text = "config_version=5\n\n[application]\n\nconfig/name=\"x\"\n\n[editor_plugins]\n\n\
                enabled=true\n\n[rendering]\n\nrenderer/rendering_method=\"gl_compatibility\"\n";
    write(&workspace.join("project.godot"), text);

    let args = vec![
        "init".to_string(),
        "--project".to_string(),
        workspace.display().to_string(),
    ];
    let output = run(&args);
    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);
    assert_eq!(
        output.status.code(),
        Some(0),
        "a malformed plugin list is not a fatal error; stdout: {stdout} stderr: {stderr}"
    );
    assert_eq!(
        std::fs::read_to_string(workspace.join("project.godot")).unwrap(),
        text,
        "the file must be byte-identical (DR-53)"
    );
    assert!(
        format!("{stdout}{stderr}").contains("PackedStringArray"),
        "the reason must say what could not be parsed; stdout: {stdout} stderr: {stderr}"
    );
    assert!(
        format!("{stdout}{stderr}").contains("left untouched"),
        "the reason must say the file was not modified; stdout: {stdout} stderr: {stderr}"
    );
}

/// DR-40: `hoh init --force-init` is the documented way through, and it works
/// offline too.
#[test]
fn init_force_over_a_non_empty_workspace_scaffolds() {
    let temp = tempfile::tempdir().unwrap();
    let workspace = temp.path().join("workspace");
    write(&workspace.join("keep.txt"), "precious\n");
    let args = vec![
        "init".to_string(),
        "--force-init".to_string(),
        "--project".to_string(),
        workspace.display().to_string(),
    ];
    let output = run(&args);
    assert_eq!(
        output.status.code(),
        Some(0),
        "stderr: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert!(workspace.join("project.godot").is_file());
    assert!(
        workspace.join("keep.txt").is_file(),
        "--force-init scaffolds over the directory, it does not empty it"
    );
}

/// DR-40: `hoh run --fresh-workspace` prepares `A₀` **before** the doctor
/// pre-check, and a doctor failure keeps the rebuilt `A₀` (no rollback).
#[test]
fn run_fresh_workspace_keeps_the_rebuilt_a0_when_doctor_fails() {
    let temp = tempfile::tempdir().unwrap();
    let workspace = temp.path().join("workspace");
    write(&workspace.join("leftover.txt"), "from an older attempt\n");
    let args = vec![
        "run".to_string(),
        "--fresh-workspace".to_string(),
        "--iterations".to_string(),
        "1".to_string(),
        "--project".to_string(),
        workspace.display().to_string(),
    ];
    let output = run(&args);
    assert_eq!(
        output.status.code(),
        Some(4),
        "the doctor pre-check must still refuse to run: stdout: {}",
        String::from_utf8_lossy(&output.stdout)
    );
    assert!(
        !workspace.join("leftover.txt").exists(),
        "the workspace must have been rebuilt before the doctor ran"
    );
    assert!(
        workspace.join("project.godot").is_file(),
        "a doctor failure must NOT roll the rebuilt A0 back (DR-40)"
    );
}
