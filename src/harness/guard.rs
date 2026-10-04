//! The environment wrapper that makes the write path first-class and the grind
//! impossible (round-1 write-path batch).
//!
//! Three jobs, all at the one boundary where a role's action becomes an
//! observation:
//!
//! 1. **The write/read path.**  A command that [`crate::harness::directive`]
//!    recognises is executed in Rust — no shell parses the content — and a
//!    command that is not a directive is handed to the real environment
//!    (`cmd.exe`) unchanged.  This is the fix for round 1's 140-call Developer:
//!    the content never meets `cmd.exe`, so `"`, `%`, `(`, `)`, `$`, `\` and raw
//!    newlines round-trip byte-for-byte.
//!
//! 2. **Fail fast on a repeated failing action.**  Round 1's tripwire was mini's
//!    `max_consecutive_format_errors`, which counts *consecutive* format errors
//!    and is reset by any success — so an agent that occasionally succeeded could
//!    retry the same broken command forever.  This wrapper counts failures **per
//!    action**: the same command failing
//!    `agent.max_action_failures` times aborts the call, whatever happened in
//!    between.
//!
//! 3. **A budget on producing the artifact.**  A role that has not written its
//!    declared artifact within `agent.artifact_write_budget_seconds` is aborted
//!    with a first-class status instead of being left to grind.  (The token half
//!    of the same budget cannot be measured inside the environment — usage is
//!    known only after the model call returns — so it is enforced by the runtime
//!    on the recorded attempt; see `crate::runtime::write_failure`.)
//!
//! An abort is **our own judgement, not the external agent's**: the error
//! carries [`FAIL_FAST_MARKER`], and `crate::harness::mini` turns it into a
//! normal `RoleOutcome` whose `exit_status` is one of the two first-class
//! statuses below.  Without that, the round would only ever have an external
//! agent's string and no harness-side fact.

use std::collections::BTreeMap;
use std::path::{Component, Path, PathBuf};
use std::sync::Mutex;
use std::time::{Duration, Instant};

use mini_swe_agent::{Action, Environment, Output, Result as MiniResult};
use serde_json::{json, Value};

use crate::harness::directive::{self, Directive};

/// The sentinel every fail-fast error carries.  `MiniHarness` recognises it and
/// converts the abort into a first-class [`crate::runtime::role::RoleOutcome`]
/// instead of a harness error.
pub const FAIL_FAST_MARKER: &str = "HOH_FAIL_FAST";

/// The same action failed `agent.max_action_failures` times.
pub const REPEATED_ACTION_STATUS: &str = "RepeatedActionError";
/// The role did not write its declared artifact inside
/// `agent.artifact_write_budget_seconds`.
pub const ARTIFACT_BUDGET_STATUS: &str = "ArtifactBudgetExceeded";

/// The one-line usage text returned when a directive is malformed.
pub fn directive_help() -> String {
    format!(
        "the write path is a directive, not a shell command:\n\n\
         {write} <relative path>\n<the file's exact content>\n{end}\n\n\
         {read} <relative path>\n\n\
         The header must be the first line of the command, the content is everything \
         after it, and the final line is exactly `{end}`.  Nothing else parses the \
         content, so quotes, `%`, `$`, `(`, `)`, `\\` and newlines are all literal.",
        write = directive::WRITE_MARKER,
        read = directive::READ_MARKER,
        end = directive::END_MARKER,
    )
}

/// Why an abort happened, as a value (so it is testable without an agent).
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum FailFast {
    RepeatedAction {
        command: String,
        failures: u32,
    },
    ArtifactBudget {
        elapsed_seconds: u64,
        budget_seconds: u64,
    },
}

impl FailFast {
    /// The first-class exit status the runtime records for this abort.
    pub fn status(&self) -> &'static str {
        match self {
            FailFast::RepeatedAction { .. } => REPEATED_ACTION_STATUS,
            FailFast::ArtifactBudget { .. } => ARTIFACT_BUDGET_STATUS,
        }
    }

    /// The error message, prefixed with [`FAIL_FAST_MARKER`] and the status, so
    /// the harness can both tell our abort apart from an infrastructure failure
    /// and recover the first-class status from the text alone.
    pub fn message(&self) -> String {
        match self {
            FailFast::RepeatedAction { command, failures } => format!(
                "{FAIL_FAST_MARKER} {REPEATED_ACTION_STATUS}: the same action failed {failures} \
                 time(s) (`agent.max_action_failures`); the action is:\n{}\nStop repeating it. If \
                 you cannot make it succeed, write the artifact you already have and end the call \
                 with the completion protocol.",
                brief(command)
            ),
            FailFast::ArtifactBudget {
                elapsed_seconds,
                budget_seconds,
            } => format!(
                "{FAIL_FAST_MARKER} {ARTIFACT_BUDGET_STATUS}: {elapsed_seconds} s elapsed without \
                 a write to the project, over the {budget_seconds} s artifact-write budget \
                 (`agent.artifact_write_budget_seconds`). Stop exploring: write the artifact now \
                 with the `{}` directive and end the call.",
                directive::WRITE_MARKER
            ),
        }
    }
}

/// The first-class status a fail-fast error message carries, if it is one.
///
/// This is the recovery half of the sentinel: `MiniHarness` receives mini's
/// opaque `AgentError::Other`, and the status must survive that boundary so the
/// round records **our** judgement rather than the external agent's string.
pub fn fail_fast_status(message: &str) -> Option<&'static str> {
    let marker = message.find(FAIL_FAST_MARKER)?;
    let rest = &message[marker + FAIL_FAST_MARKER.len()..];
    for status in [REPEATED_ACTION_STATUS, ARTIFACT_BUDGET_STATUS] {
        if rest.trim_start().starts_with(status) {
            return Some(status);
        }
    }
    None
}

/// The first line of a command, so an abort message stays readable.
fn brief(command: &str) -> String {
    let first = command.lines().next().unwrap_or("").trim();
    let mut text: String = first.chars().take(200).collect();
    if first.chars().count() > 200 {
        text.push('…');
    }
    text
}

/// The mutable state of one role call.
#[derive(Debug)]
struct GuardState {
    /// Failures per action signature.  A success of the *same* signature clears
    /// it; nothing else does, which is the difference from "consecutive".
    failures: BTreeMap<String, u32>,
    /// The first successful write of a **project** file (not `.hoh/**`, not a
    /// cache) — the artifact the budget is about.
    artifact_written: bool,
    /// A successful write of any file, for the record.
    writes: u64,
}

/// What counts as "the artifact this role declared" for the write budget.
///
/// The Developer's artifact is the **project**; a write under `.hoh/**` is
/// scratch and does not count as an increment (that is the `no_engineering_write`
/// rule).  The Planner's and the Tester's artifacts (`.hoh/plan.md`,
/// `.hoh/evidence.json`) live under `.hoh/**` by construction, so for them any
/// write counts — otherwise their budget could never be disarmed and a role that
/// had already written its artifact would be aborted for not writing one.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ArtifactKind {
    /// A file inside the project, outside the hash-excluded paths.
    ProjectFile,
    /// Any file the role can write.
    AnyFile,
}

impl ArtifactKind {
    /// The kind that matches `role`'s declared artifact.
    pub fn for_role(role: crate::model::Role) -> Self {
        match role {
            crate::model::Role::Developer => ArtifactKind::ProjectFile,
            crate::model::Role::Planner | crate::model::Role::Tester => ArtifactKind::AnyFile,
        }
    }
}

/// The environment a role runs against: the real shell plus the two guards.
pub struct WriteGuardEnvironment {
    inner: Box<dyn Environment>,
    cwd: PathBuf,
    max_action_failures: u32,
    artifact_budget: Option<Duration>,
    artifact_kind: ArtifactKind,
    started: Instant,
    state: Mutex<GuardState>,
}

impl WriteGuardEnvironment {
    pub fn new(
        inner: Box<dyn Environment>,
        cwd: PathBuf,
        max_action_failures: u32,
        artifact_budget_seconds: u64,
    ) -> Self {
        Self::with_artifact_kind(
            inner,
            cwd,
            max_action_failures,
            artifact_budget_seconds,
            ArtifactKind::ProjectFile,
        )
    }

    pub fn with_artifact_kind(
        inner: Box<dyn Environment>,
        cwd: PathBuf,
        max_action_failures: u32,
        artifact_budget_seconds: u64,
        artifact_kind: ArtifactKind,
    ) -> Self {
        Self {
            inner,
            cwd,
            max_action_failures,
            artifact_budget: if artifact_budget_seconds == 0 {
                None
            } else {
                Some(Duration::from_secs(artifact_budget_seconds))
            },
            artifact_kind,
            started: Instant::now(),
            state: Mutex::new(GuardState {
                failures: BTreeMap::new(),
                artifact_written: false,
                writes: 0,
            }),
        }
    }

    /// Has this call made a project write yet?
    pub fn artifact_written(&self) -> bool {
        self.state
            .lock()
            .map(|state| state.artifact_written)
            .unwrap_or(false)
    }

    /// How many directive writes succeeded.
    pub fn writes(&self) -> u64 {
        self.state.lock().map(|state| state.writes).unwrap_or(0)
    }

    fn record_success(&self, command: &str) -> Option<FailFast> {
        let mut state = self.state.lock().ok()?;
        state.failures.remove(command);
        None
    }

    fn record_failure(&self, command: &str) -> Option<FailFast> {
        if self.max_action_failures == 0 {
            return None;
        }
        let mut state = self.state.lock().ok()?;
        let entry = state.failures.entry(command.to_string()).or_insert(0u32);
        *entry += 1;
        let failures = *entry;
        if failures >= self.max_action_failures {
            // Bound the map: an agent that has just been aborted does not need
            // its per-command history any more.
            state.failures.clear();
            Some(FailFast::RepeatedAction {
                command: command.to_string(),
                failures,
            })
        } else {
            None
        }
    }

    fn budget_exceeded(&self) -> Option<FailFast> {
        let budget = self.artifact_budget?;
        let written = self.artifact_written();
        if written {
            return None;
        }
        let elapsed = self.started.elapsed();
        if elapsed >= budget {
            Some(FailFast::ArtifactBudget {
                elapsed_seconds: elapsed.as_secs(),
                budget_seconds: budget.as_secs(),
            })
        } else {
            None
        }
    }

    /// Resolve a directive's path against the role's working directory.
    ///
    /// Only relative paths are accepted, and no `..` component is permitted, so
    /// a directive cannot be used to write outside the view the role owns.  It
    /// is deliberately *not* a policy layer (the Tester's `.hoh/**`-only rule
    /// stays the hash assertion's job); it is a path-safety layer.
    fn resolve(&self, path: &str) -> anyhow::Result<PathBuf> {
        let candidate = Path::new(path);
        if candidate.is_absolute() {
            anyhow::bail!(
                "`{path}` is absolute; a directive path is relative to the working directory"
            );
        }
        for component in candidate.components() {
            if matches!(component, Component::ParentDir) {
                anyhow::bail!("`{path}` escapes the working directory with `..`");
            }
        }
        if path.trim().is_empty() {
            anyhow::bail!("the directive gave an empty path");
        }
        Ok(self.cwd.join(candidate))
    }

    fn execute_write(&self, path: &str, content: &str) -> Output {
        let resolved = match self.resolve(path) {
            Ok(resolved) => resolved,
            Err(error) => return Output::success(error.to_string(), 1),
        };
        if let Some(parent) = resolved.parent() {
            if let Err(error) = std::fs::create_dir_all(parent) {
                return Output::success(
                    format!("could not create {}: {error}", parent.display()),
                    1,
                );
            }
        }
        match std::fs::write(&resolved, content.as_bytes()) {
            Ok(()) => {
                let counts = match self.artifact_kind {
                    ArtifactKind::ProjectFile => !is_excluded_path(path),
                    ArtifactKind::AnyFile => true,
                };
                if let Ok(mut state) = self.state.lock() {
                    state.writes += 1;
                    if counts {
                        state.artifact_written = true;
                    }
                }
                let mut output =
                    Output::success(format!("wrote {} byte(s) to {}", content.len(), path), 0);
                output
                    .extra
                    .insert("hoh_write_path".to_string(), json!(path));
                output
                    .extra
                    .insert("hoh_write_bytes".to_string(), json!(content.len()));
                output
            }
            Err(error) => Output::success(format!("could not write {path}: {error}"), 1),
        }
    }

    fn execute_read(&self, path: &str) -> Output {
        let resolved = match self.resolve(path) {
            Ok(resolved) => resolved,
            Err(error) => return Output::success(error.to_string(), 1),
        };
        match std::fs::read(&resolved) {
            Ok(bytes) => {
                // The bytes are what they are; a file that is not valid UTF-8 is
                // reported as such rather than silently mangled.
                match String::from_utf8(bytes) {
                    Ok(text) => Output::success(text, 0),
                    Err(error) => Output::success(
                        format!(
                            "{} is not UTF-8 text ({} byte(s)): {}",
                            path,
                            error.as_bytes().len(),
                            error.utf8_error()
                        ),
                        1,
                    ),
                }
            }
            Err(error) => Output::success(format!("could not read {path}: {error}"), 1),
        }
    }
}

/// Is this path under a runtime-excluded or cache directory (not an artifact)?
fn is_excluded_path(path: &str) -> bool {
    let normalized = path.replace('\\', "/");
    let normalized = normalized.trim_start_matches("./");
    ["\\.hoh/", "\\.git/", "target/", ".hoh/", ".git/"]
        .iter()
        .any(|prefix| normalized.starts_with(prefix))
}

#[async_trait::async_trait]
impl Environment for WriteGuardEnvironment {
    async fn execute(
        &self,
        action: &Action,
        cwd: Option<&str>,
        timeout: Option<u64>,
    ) -> MiniResult<Output> {
        match directive::parse_directive(&action.command) {
            Directive::Write { path, content } => return Ok(self.execute_write(&path, &content)),
            Directive::Read { path } => return Ok(self.execute_read(&path)),
            Directive::Malformed { reason } => {
                return Ok(Output::success(
                    format!("{reason}\n\n{}", directive_help()),
                    1,
                ))
            }
            Directive::Shell => {}
        }

        let output = self.inner.execute(action, cwd, timeout).await?;
        if output.returncode == 0 {
            let _ = self.record_success(&action.command);
        } else if let Some(fail_fast) = self.record_failure(&action.command) {
            return Err(mini_swe_agent::AgentError::other(anyhow::anyhow!(
                "{}",
                fail_fast.message()
            )));
        }
        if let Some(fail_fast) = self.budget_exceeded() {
            return Err(mini_swe_agent::AgentError::other(anyhow::anyhow!(
                "{}",
                fail_fast.message()
            )));
        }
        Ok(output)
    }

    fn get_template_vars(&self) -> Value {
        self.inner.get_template_vars()
    }

    fn serialize(&self) -> Value {
        self.inner.serialize()
    }

    fn cleanup(&self) -> anyhow::Result<()> {
        self.inner.cleanup()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::harness::directive::render_write;

    /// A stand-in for the real shell: records the commands it was asked to run
    /// and answers with a scripted return code.
    struct FakeShell {
        seen: std::sync::Arc<Mutex<Vec<String>>>,
        returncode: i32,
    }

    impl FakeShell {
        fn new(returncode: i32) -> Self {
            Self {
                seen: std::sync::Arc::new(Mutex::new(Vec::new())),
                returncode,
            }
        }
    }

    #[async_trait::async_trait]
    impl Environment for FakeShell {
        async fn execute(
            &self,
            action: &Action,
            _cwd: Option<&str>,
            _timeout: Option<u64>,
        ) -> MiniResult<Output> {
            self.seen
                .lock()
                .expect("the fake shell")
                .push(action.command.clone());
            Ok(Output::success("shell output", self.returncode))
        }
        fn get_template_vars(&self) -> Value {
            Value::Null
        }
        fn serialize(&self) -> Value {
            Value::Null
        }
        fn cleanup(&self) -> anyhow::Result<()> {
            Ok(())
        }
    }

    fn guard(root: &Path, failures: u32, budget: u64) -> WriteGuardEnvironment {
        guard_with(root, 0, failures, budget)
    }

    fn guard_with(
        root: &Path,
        shell_returncode: i32,
        failures: u32,
        budget: u64,
    ) -> WriteGuardEnvironment {
        WriteGuardEnvironment::new(
            Box::new(FakeShell::new(shell_returncode)),
            root.to_path_buf(),
            failures,
            budget,
        )
    }

    fn run(command: &str, root: &Path) -> Output {
        let environment = guard(root, 3, 0);
        futures_lite_block_on(async {
            environment
                .execute(&Action::new(command), None, None)
                .await
                .expect("the guard runs")
        })
    }

    /// A tiny executor for the tests: the guard is async only because mini's
    /// trait is, and blocking on it keeps the tests readable.
    fn futures_lite_block_on<F: std::future::Future>(future: F) -> F::Output {
        tokio::runtime::Builder::new_current_thread()
            .enable_all()
            .build()
            .expect("a test runtime")
            .block_on(future)
    }

    #[test]
    fn a_write_directive_writes_the_file_byte_for_byte() {
        let directory = tempfile::tempdir().expect("a temporary view");
        let content = "fn main() {\n    let s = \"100% $HOME (x) C:\\\\y\";\n}\n";
        let output = run(&render_write("src/game.rs", content), directory.path());
        assert_eq!(output.returncode, 0, "{}", output.output);
        let written = std::fs::read(directory.path().join("src/game.rs")).expect("the file");
        assert_eq!(written, content.as_bytes());
        assert!(output.output.contains("wrote"));
    }

    #[test]
    fn a_read_directive_returns_the_bytes_unchanged() {
        let directory = tempfile::tempdir().expect("a temporary view");
        std::fs::create_dir_all(directory.path().join(".hoh")).unwrap();
        let content = "a\r\nb%c$d\\e(f)\"g\"\r\n";
        std::fs::write(directory.path().join(".hoh/plan.md"), content).unwrap();
        let output = run("HOH_READ_FILE .hoh/plan.md", directory.path());
        assert_eq!(output.returncode, 0);
        assert_eq!(output.output, content);
    }

    #[test]
    fn a_directive_never_reaches_the_shell() {
        let directory = tempfile::tempdir().expect("a temporary view");
        let shell = FakeShell::new(0);
        let seen = std::sync::Arc::clone(&shell.seen);
        let environment =
            WriteGuardEnvironment::new(Box::new(shell), directory.path().to_path_buf(), 3, 0);
        futures_lite_block_on(async {
            environment
                .execute(&Action::new(&render_write("a.txt", "here\n")), None, None)
                .await
                .expect("the write");
            environment
                .execute(&Action::new("HOH_READ_FILE a.txt"), None, None)
                .await
                .expect("the read");
            environment
                .execute(&Action::new("cargo build --offline"), None, None)
                .await
                .expect("an ordinary command");
        });
        assert_eq!(
            seen.lock().expect("the shell log").as_slice(),
            ["cargo build --offline"],
            "the shell must see every non-directive and no directive"
        );
    }

    #[test]
    fn a_write_outside_the_view_is_refused_and_nothing_is_written() {
        let directory = tempfile::tempdir().expect("a temporary view");
        for path in ["../escape.rs", "C:\\absolute.rs", "..\\up.rs"] {
            let output = run(&render_write(path, "x"), directory.path());
            assert_eq!(output.returncode, 1, "{path} must be refused");
            assert!(output.output.contains("working directory"), "{path}");
        }
        assert!(!directory
            .path()
            .parent()
            .unwrap()
            .join("escape.rs")
            .exists());
    }

    #[test]
    fn a_malformed_directive_is_explained_and_never_run() {
        let directory = tempfile::tempdir().expect("a temporary view");
        let output = run("HOH_WRITE_FILE a.rs\nunterminated", directory.path());
        assert_eq!(output.returncode, 1);
        assert!(
            output.output.contains("HOH_END_WRITE_FILE"),
            "{}",
            output.output
        );
        assert!(output.output.contains("not closed"), "{}", output.output);
    }

    #[test]
    fn a_project_write_marks_the_artifact_and_a_scratch_write_does_not() {
        let directory = tempfile::tempdir().expect("a temporary view");
        let environment = guard(directory.path(), 3, 0);
        futures_lite_block_on(async {
            environment
                .execute(
                    &Action::new(&render_write(".hoh/scratch/probe.txt", "n")),
                    None,
                    None,
                )
                .await
                .expect("the scratch write");
        });
        assert!(
            !environment.artifact_written(),
            "scratch is not the artifact"
        );
        futures_lite_block_on(async {
            environment
                .execute(&Action::new(&render_write("src/game.rs", "n")), None, None)
                .await
                .expect("the project write");
        });
        assert!(environment.artifact_written());
        assert_eq!(environment.writes(), 2);
    }

    /// The Planner's and the Tester's artifacts live under `.hoh/**`, so for them
    /// a `.hoh` write **is** the artifact.  Without this, their budget could never
    /// be disarmed and a role that had already written its plan would be aborted
    /// for not writing one.
    #[test]
    fn a_planner_or_tester_artifact_disarms_the_budget_through_hoh() {
        let directory = tempfile::tempdir().expect("a temporary view");
        let environment = WriteGuardEnvironment::with_artifact_kind(
            Box::new(FakeShell::new(0)),
            directory.path().to_path_buf(),
            3,
            1,
            ArtifactKind::AnyFile,
        );
        futures_lite_block_on(async {
            environment
                .execute(
                    &Action::new(&render_write(".hoh/plan.md", "# plan\n")),
                    None,
                    None,
                )
                .await
                .expect("the plan write");
        });
        assert!(environment.artifact_written());
        std::thread::sleep(Duration::from_millis(1_050));
        assert!(environment.budget_exceeded().is_none());
        // The Developer's kind is the project, decided from the role itself.
        assert_eq!(
            ArtifactKind::for_role(crate::model::Role::Developer),
            ArtifactKind::ProjectFile
        );
        assert_eq!(
            ArtifactKind::for_role(crate::model::Role::Planner),
            ArtifactKind::AnyFile
        );
        assert_eq!(
            ArtifactKind::for_role(crate::model::Role::Tester),
            ArtifactKind::AnyFile
        );
    }

    #[test]
    fn the_same_failing_action_aborts_the_call_per_action_not_consecutively() {
        let directory = tempfile::tempdir().expect("a temporary view");
        // The shell fails, and there is a *successful* action interleaved — which
        // is exactly what reset mini's consecutive-format-error tripwire.
        let environment = guard_with(directory.path(), 1, 3, 0);
        let failing = Action::new("cat .hoh/TASK.md");
        let ok = guard_with(directory.path(), 0, 3, 0);
        let outcome = futures_lite_block_on(async {
            let mut last = Ok(());
            for _ in 0..3 {
                last = environment.execute(&failing, None, None).await.map(|_| ());
                let _ = ok.execute(&Action::new("echo hi"), None, None).await;
            }
            last
        });
        let error = outcome.expect_err("the third failure of one action must abort");
        assert!(error.to_string().contains(FAIL_FAST_MARKER), "{error}");
        assert!(error.to_string().contains("cat .hoh/TASK.md"), "{error}");
        assert_eq!(
            fail_fast_status(&error.to_string()),
            Some(REPEATED_ACTION_STATUS)
        );
    }

    #[test]
    fn a_success_of_the_same_action_clears_its_own_counter() {
        let directory = tempfile::tempdir().expect("a temporary view");
        let environment = guard(directory.path(), 2, 0);
        let flaky = Action::new("flaky command");
        futures_lite_block_on(async {
            // The fake shell always succeeds, so a success must clear the counter
            // even after a failure was recorded by the same command.
            environment
                .state
                .lock()
                .unwrap()
                .failures
                .insert("flaky command".to_string(), 1);
            environment
                .execute(&flaky, None, None)
                .await
                .expect("a success must not abort");
        });
        assert!(!environment
            .state
            .lock()
            .unwrap()
            .failures
            .contains_key("flaky command"));
    }

    #[test]
    fn the_artifact_budget_aborts_a_call_that_never_writes() {
        let directory = tempfile::tempdir().expect("a temporary view");
        // Zero means "no budget", and a project write disarms it.
        let unbudgeted = guard_with(directory.path(), 0, 3, 0);
        assert!(unbudgeted.budget_exceeded().is_none());

        let environment = guard_with(directory.path(), 0, 3, 1);
        std::thread::sleep(Duration::from_millis(1_050));
        let error = futures_lite_block_on(async {
            environment
                .execute(&Action::new("cargo build --offline"), None, None)
                .await
                .map(|_| ())
                .expect_err("the budget must abort the call")
        });
        assert!(error.to_string().contains(FAIL_FAST_MARKER), "{error}");
        assert_eq!(
            fail_fast_status(&error.to_string()),
            Some(ARTIFACT_BUDGET_STATUS)
        );
        assert!(
            error.to_string().contains("artifact-write budget"),
            "{error}"
        );
        assert!(error.to_string().contains("HOH_WRITE_FILE"), "{error}");
    }

    #[test]
    fn a_project_write_disarms_the_artifact_budget() {
        let directory = tempfile::tempdir().expect("a temporary view");
        let environment = guard_with(directory.path(), 0, 3, 1);
        futures_lite_block_on(async {
            environment
                .execute(&Action::new(&render_write("src/game.rs", "x")), None, None)
                .await
                .expect("the write");
        });
        std::thread::sleep(Duration::from_millis(1_050));
        assert!(environment.budget_exceeded().is_none());
    }

    /// The sentinel is the only channel the status has across mini's opaque
    /// `AgentError`, so its recovery must be exact.
    #[test]
    fn the_fail_fast_status_is_recoverable_from_the_message_alone() {
        let repeated = FailFast::RepeatedAction {
            command: "cat x".to_string(),
            failures: 3,
        };
        assert_eq!(
            fail_fast_status(&repeated.message()),
            Some(REPEATED_ACTION_STATUS)
        );
        let budget = FailFast::ArtifactBudget {
            elapsed_seconds: 61,
            budget_seconds: 60,
        };
        assert_eq!(
            fail_fast_status(&budget.message()),
            Some(ARTIFACT_BUDGET_STATUS)
        );
        assert_eq!(fail_fast_status("llm-connector chat request failed"), None);
        assert_eq!(
            fail_fast_status("a command that mentions HOH_FAIL_FAST"),
            None
        );
    }
}
