//! Round-1 write-path batch — the write/read path, **executed through the real
//! wrapper stack and the real shell**.
//!
//! The unit tests in `src/harness/{directive,guard}.rs` prove the parsing and the
//! file contents; they deliberately do not prove that a role's action really
//! reaches the guard, or that a non-directive command still reaches `cmd.exe`.
//! This file closes that gap by putting the same three layers the runtime puts
//! between a role and the machine —
//!
//! ```text
//! LocalEnvironment (cmd.exe)  ->  CappedEnvironment  ->  WriteGuardEnvironment
//! ```
//!
//! — in front of a **real** `cmd.exe` and executing the exact text the prompts
//! document.
//!
//! ## The before/after evidence for the recipe
//!
//! Round 1's Developer emitted POSIX shell while the shell was `cmd.exe`
//! (`cat .hoh/TASK.md; echo "=====PLAN====="; cat .hoh/plan.md` is recorded
//! verbatim in `runs/round1b/iter-1/traj/developer.attempt1.json`).  The test
//! [`the_posix_read_path_fails_and_the_documented_one_works`] runs both forms
//! through the same real shell, so "the old form failed and the new form works"
//! is executed rather than asserted from a comment.

use std::collections::BTreeMap;
use std::path::Path;

use hof_rs::harness::cap::CappedEnvironment;
use hof_rs::harness::directive::{render_read, render_write};
use hof_rs::harness::guard::{ArtifactKind, WriteGuardEnvironment};
use mini_swe_agent::environments::LocalEnvironmentConfig;
use mini_swe_agent::{Action, Environment, LocalEnvironment};
use serde_json::Value;

/// The three layers the runtime builds, around a **real** `cmd.exe`/`sh`.
fn role_environment(view: &Path, env: &BTreeMap<String, String>) -> Box<dyn Environment> {
    let local = LocalEnvironment::new(LocalEnvironmentConfig {
        cwd: view.to_string_lossy().into_owned(),
        env: env
            .iter()
            .map(|(key, value)| (key.clone(), Value::String(value.clone())))
            .collect(),
        timeout: 300,
    });
    let capped = CappedEnvironment::new(Box::new(local), 64 * 1024);
    Box::new(WriteGuardEnvironment::with_artifact_kind(
        Box::new(capped),
        view.to_path_buf(),
        3,
        0,
        ArtifactKind::AnyFile,
    ))
}

async fn run(view: &Path, env: &BTreeMap<String, String>, command: &str) -> (String, i32) {
    let environment = role_environment(view, env);
    let output = environment
        .execute(&Action::new(command), None, Some(300))
        .await
        .expect("the environment returns an Output");
    (output.output, output.returncode)
}

fn no_env() -> BTreeMap<String, String> {
    BTreeMap::new()
}

/// The hostile content the round could not carry: every character the old path
/// had to escape, in one multi-line Rust file.
const HOSTILE: &str = "use bevy::prelude::*;\n\
                       fn main() {\n\
                       \x20   let pct = 100 % 3;            // a percent sign\n\
                       \x20   let env = \"$HOME and %PATH% and 100%%\";\n\
                       \x20   let path = \"C:\\\\Users\\\\wyl\\\\(x)\";\n\
                       \x20   let (a, b) = (1, 2);\n\
                       \x20   println!(\"{a} {b} {pct} {env} {path}\");\n\
                       }\n";

/// A write directive executed through the whole stack lands **byte for byte**.
#[tokio::test]
async fn the_documented_write_directive_round_trips_through_the_real_shell() {
    let temp = tempfile::tempdir().unwrap();
    let view = temp.path();
    let (output, code) = run(view, &no_env(), &render_write("src/game.rs", HOSTILE)).await;
    assert_eq!(code, 0, "the directive must succeed: {output}");
    assert!(output.contains("wrote"), "{output}");

    let written = std::fs::read(view.join("src/game.rs")).expect("the file must exist");
    assert_eq!(
        written,
        HOSTILE.as_bytes(),
        "the content must survive byte for byte; got {}",
        String::from_utf8_lossy(&written)
    );
}

/// The read directive returns the same bytes it wrote, including CRLF and the
/// hostile characters.
#[tokio::test]
async fn the_documented_read_directive_returns_the_bytes_unchanged() {
    let temp = tempfile::tempdir().unwrap();
    let view = temp.path();
    let content = "line1\r\nline2 %PATH% $HOME (a) \\b \"q\"\r\n";
    std::fs::create_dir_all(view.join(".hoh")).unwrap();
    std::fs::write(view.join(".hoh/plan.md"), content).unwrap();

    let (output, code) = run(view, &no_env(), &render_read(".hoh/plan.md")).await;
    assert_eq!(code, 0, "{output}");
    assert_eq!(output, content, "the read must be byte-exact");
}

/// Before/after, executed: the shell shapes that ate round 1 fail here, and the
/// documented path does not.
///
/// Two of them are **deterministic properties of `cmd.exe`**, not of this
/// machine's `PATH`:
///
/// * `;` is not a command separator — `echo one; echo two` prints the literal
///   text, so the `cat a; cat b` a role writes never runs `b`;
/// * `%NAME%` is expanded inside content, so a file written through `echo`
///   cannot carry a literal `%`.
///
/// `cat` itself is deliberately **not** asserted to be missing: on a machine
/// whose `PATH` includes Git's `usr/bin`, `cat.exe` resolves and works.  That is
/// exactly the trap — the same command line succeeds or fails depending on the
/// environment, which is why the harness must not depend on it.  The round-1
/// recording is pinned separately by
/// [`the_recorded_round_one_trajectory_really_carried_these_shapes`].
#[tokio::test]
async fn the_shell_shapes_that_ate_round_one_are_replaced_by_the_directives() {
    let temp = tempfile::tempdir().unwrap();
    let view = temp.path();

    if cfg!(windows) {
        // No `;` chaining: the second command is never run.
        let (chained, code) = run(view, &no_env(), "echo one; echo two").await;
        assert_eq!(code, 0, "{chained}");
        assert!(
            chained.contains("one; echo two"),
            "cmd.exe must treat `;` as literal text, not as a separator: {chained:?}"
        );

        // `%` is expanded before the program sees it: a file written through the
        // shell cannot carry a literal percent.
        let (expanded, code) = run(view, &no_env(), "echo 100%PATH% > via_shell.txt").await;
        assert_eq!(code, 0, "{expanded}");
        let via_shell = std::fs::read_to_string(view.join("via_shell.txt")).unwrap();
        assert!(
            !via_shell.contains("100%PATH%"),
            "the shell must have expanded `%PATH%`; it wrote {via_shell:?}"
        );

        // The directive writes the same text literally.
        let (written, code) = run(
            view,
            &no_env(),
            &render_write("via_directive.txt", "100%PATH% (x) \\ $HOME\n"),
        )
        .await;
        assert_eq!(code, 0, "{written}");
        assert_eq!(
            std::fs::read_to_string(view.join("via_directive.txt")).unwrap(),
            "100%PATH% (x) \\ $HOME\n"
        );
    }

    // The documented read path works on both platforms.
    std::fs::create_dir_all(view.join(".hoh")).unwrap();
    std::fs::write(view.join(".hoh/TASK.md"), "the public specification\n").unwrap();
    let (after, code) = run(view, &no_env(), &render_read(".hoh/TASK.md")).await;
    assert_eq!(code, 0, "{after}");
    assert_eq!(after, "the public specification\n");
}

/// The **before** evidence is the round-1 recording itself.
///
/// The Developer really emitted POSIX shell at its `cmd.exe`; this pins the
/// recorded fact the recipe replaces, and it does not depend on what this
/// machine's `PATH` happens to resolve.  Only the presence of the shape is
/// asserted — the trajectory is never printed, because a recorded trajectory is
/// not a place to copy text out of.
#[test]
fn the_recorded_round_one_trajectory_really_carried_these_shapes() {
    let path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("runs/round1b/iter-1/traj/developer.attempt1.json");
    let raw = match std::fs::read_to_string(&path) {
        Ok(raw) => raw,
        Err(error) => panic!(
            "the round-1 recording this batch is evidence about must be readable at {}: {error}",
            path.display()
        ),
    };
    for shape in ["cat .hoh/TASK.md", "cat .hoh/plan.md", "=====PLAN====="] {
        assert!(
            raw.contains(shape),
            "the recording must show the POSIX shape `{shape}` that round 1 emitted"
        );
    }
    // …and it must NOT show the write directive: the path this batch adds did not
    // exist when the round ran, which is why the round fought the shell instead.
    assert!(
        !raw.contains("HOH_WRITE_FILE"),
        "the recording must predate the write directive"
    );
}

/// The guard must not swallow the shell: an ordinary command still runs, and
/// still reaches `cmd.exe`.
#[tokio::test]
async fn an_ordinary_command_still_reaches_the_real_shell() {
    let temp = tempfile::tempdir().unwrap();
    let view = temp.path();
    let (output, code) = run(view, &no_env(), "echo hoh-shell-probe").await;
    assert_eq!(code, 0, "{output}");
    assert!(
        output.contains("hoh-shell-probe"),
        "the shell's own output must come back: {output}"
    );
}

/// The environment's own variable, not the harness's: `HOH_ARTIFACT_DIR` reaches
/// the shell through the same map `role_env` builds, so a directive path and a
/// shell path are the same path.
#[tokio::test]
async fn the_directive_and_the_shell_agree_on_the_working_directory() {
    let temp = tempfile::tempdir().unwrap();
    let view = temp.path();
    std::fs::create_dir_all(view.join(".hoh/scratch")).unwrap();
    let mut env = BTreeMap::new();
    env.insert(
        "HOH_SCRATCH_DIR".to_string(),
        view.join(".hoh/scratch").to_string_lossy().into_owned(),
    );
    let (output, code) = run(
        view,
        &env,
        &render_write(".hoh/scratch/probe.txt", "written by the directive\n"),
    )
    .await;
    assert_eq!(code, 0, "{output}");
    let (listing, code) = run(view, &env, "dir /b .hoh\\scratch").await;
    assert_eq!(code, 0, "{listing}");
    assert!(listing.contains("probe.txt"), "{listing}");
    assert_eq!(
        std::fs::read_to_string(view.join(".hoh/scratch/probe.txt")).unwrap(),
        "written by the directive\n"
    );
}

/// Round-1 write-path batch, the target directory: with `CARGO_TARGET_DIR` in the
/// role's environment, a `cargo build --offline` from the project builds into the
/// shared cache and leaves **no `target/` inside the project** — the second, 8.5
/// GB tree round 1 measured.
///
/// The crate here is a trivial one (the offline suite may not compile Bevy), so
/// the absolute seconds are not the round's; what it proves is the mechanism the
/// runtime exports, on this machine, with this cargo.
#[tokio::test]
async fn the_exported_target_directory_is_where_the_build_really_goes() {
    let temp = tempfile::tempdir().unwrap();
    let project = temp.path().join("project");
    let cache = temp.path().join("shared-target");
    std::fs::create_dir_all(project.join("src")).unwrap();
    std::fs::write(
        project.join("Cargo.toml"),
        "[package]\nname = \"hoh_target_probe\"\nversion = \"0.0.0\"\nedition = \"2021\"\n",
    )
    .unwrap();
    std::fs::write(project.join("src/main.rs"), "fn main() {}\n").unwrap();

    let mut env = BTreeMap::new();
    env.insert(
        "CARGO_TARGET_DIR".to_string(),
        cache.to_string_lossy().into_owned(),
    );
    let (output, code) = run(&project, &env, "cargo build --offline").await;
    assert_eq!(
        code, 0,
        "the probe crate must build offline into the shared cache: {output}"
    );
    assert!(
        cache.is_dir(),
        "the build must have used CARGO_TARGET_DIR: {}",
        cache.display()
    );
    assert!(
        !project.join("target").exists(),
        "the build must not create a second target tree inside the project: {}",
        project.join("target").display()
    );

    // …and a rebuild after a source edit reuses it: the same directory grows no
    // second copy, and the build succeeds again.
    std::fs::write(project.join("src/main.rs"), "fn main() { let _ = 1; }\n").unwrap();
    let (output, code) = run(&project, &env, "cargo build --offline").await;
    assert_eq!(code, 0, "the warm rebuild must succeed: {output}");
    assert!(!project.join("target").exists());
}

/// The control for the test above: with `CARGO_TARGET_DIR` cleared, cargo builds
/// into the project — which is exactly what round 1's Developer did, and why the
/// round carried a second, ~8.5 GB target tree.
///
/// The variable is cleared with `set CARGO_TARGET_DIR=` because the **test
/// process** inherits the gate's own `CARGO_TARGET_DIR`; without that, the
/// control would pass for the wrong reason.
#[tokio::test]
async fn without_the_export_the_build_lands_inside_the_project() {
    let temp = tempfile::tempdir().unwrap();
    let project = temp.path().join("project");
    std::fs::create_dir_all(project.join("src")).unwrap();
    std::fs::write(
        project.join("Cargo.toml"),
        "[package]\nname = \"hoh_no_target_probe\"\nversion = \"0.0.0\"\nedition = \"2021\"\n",
    )
    .unwrap();
    std::fs::write(project.join("src/main.rs"), "fn main() {}\n").unwrap();

    let cleared = if cfg!(windows) {
        // The quoted form is the one that really clears the variable: the
        // unquoted `set X= && …` sets it to a single space.
        "set \"CARGO_TARGET_DIR=\" && cargo build --offline"
    } else {
        "unset CARGO_TARGET_DIR; cargo build --offline"
    };
    let (output, code) = run(&project, &no_env(), cleared).await;
    assert_eq!(code, 0, "{output}");
    assert!(
        project.join("target").is_dir(),
        "without the export cargo builds inside the project — the round-1 shape"
    );
}
