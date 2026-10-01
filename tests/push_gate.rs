//! DR-75 ④: the mechanical acceptance push gate, exercised **offline**.
//!
//! The repository's hard rule is that nothing is pushed before an independent
//! acceptance passes.  DR-75 turns that rule into a versioned `pre-push` hook that
//! refuses any commit without a `pass` record in the acceptance ledger, so the
//! enforcement no longer depends on who runs `git push`.
//!
//! This file drives the *real* git flow against a throwaway **bare** repository that
//! stands in for `origin`.  Nothing here touches the real remote, the network, Godot,
//! a model endpoint, `runs/**` or any path inside the repository: every sandbox is a
//! `tempfile::TempDir`.  The hook is the versioned `.githooks/pre-push` of this very
//! checkout, reached through `core.hooksPath` exactly as the installer sets it.
//!
//! Required cases (task book §1 ④):
//!   1. unmarked ⇒ refused ................ `an_unmarked_push_is_refused_with_actionable_text`
//!   2. marked ⇒ allowed .................. `a_marked_push_succeeds`
//!   3. already-on-the-remote not rechecked  `commits_already_on_the_remote_are_not_rechecked`
//!      (+ the no-op push) ................ `a_push_with_nothing_new_is_allowed`
//!   4. fail closed ....................... `a_missing_marker_source_refuses_every_push`,
//!                                          `a_corrupt_marker_source_refuses_every_push`
//!   5. `--no-verify` is a known limit .... `the_bypass_flag_is_a_recorded_known_limit`
//!   6. one unmarked commit in a range .... `one_unmarked_commit_in_a_multi_commit_range_refuses`
//!
//! plus the boundaries the book requires to be handled explicitly (ref deletion, a
//! brand-new remote branch, an unknown remote object), the marker mechanism, the
//! idempotent installer, the LF invariant and the gate/writer differential.

use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::{Command, Output, Stdio};

const HOOK: &str = ".githooks/pre-push";
const LIB: &str = ".githooks/hoh-acceptance-lib.sh";
const INSTALLER: &str = "scripts/install-hooks.sh";
const MARKER: &str = "scripts/accept-commit.sh";
const LEDGER_FILE: &str = "hoh-accepted-commits.txt";
const REPORT: &str = ".spec/hof-rs/tasks/TASK-DR75-TEST-ACCEPTANCE.md";
const REPORT_BODY: &str = "# TASK-DR75 test acceptance\n\nverdict: pass\n";
const ZERO: &str = "0000000000000000000000000000000000000000";

/// Environment variables that would silently redirect a git command somewhere else.
/// They are removed from every child so a sandbox can only ever act on itself.
const LEAKY: [&str; 9] = [
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_COMMON_DIR",
    "GIT_PREFIX",
    "GIT_CONFIG_PARAMETERS",
    "GIT_CONFIG_COUNT",
];

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
}

/// git wants `/`-separated paths on every platform here, and it never helps to
/// hand a Windows path with backslashes to a bundled `sh`.
fn slash(path: &Path) -> String {
    path.to_string_lossy().replace('\\', "/")
}

fn command(program: &str, cwd: &Path) -> Command {
    let mut command = Command::new(program);
    command.current_dir(cwd);
    for key in LEAKY {
        command.env_remove(key);
    }
    command
}

/// git with the host's global configuration neutralised: this checkout's system
/// gitconfig sets `core.autocrlf=true`, which is irrelevant to the gate but would
/// otherwise rewrite sandbox files behind the assertions.
fn git_command(cwd: &Path) -> Command {
    let mut command = command("git", cwd);
    command.args([
        "-c",
        "core.autocrlf=false",
        "-c",
        "core.safecrlf=false",
        "-c",
        "commit.gpgsign=false",
        "-c",
        "tag.gpgsign=false",
    ]);
    command
}

fn text(output: &Output) -> String {
    format!(
        "{}{}",
        String::from_utf8_lossy(&output.stdout),
        String::from_utf8_lossy(&output.stderr)
    )
}

fn succeeded(output: &Output, what: &str) -> String {
    assert!(
        output.status.success(),
        "{what} must succeed, but exited {:?}:\n{}",
        output.status.code(),
        text(output)
    );
    String::from_utf8_lossy(&output.stdout).trim().to_string()
}

fn assert_mentions(haystack: &str, needle: &str, context: &str) {
    assert!(
        haystack.contains(needle),
        "{context}: expected the output to mention `{needle}`, but it was:\n{haystack}"
    );
}

/// A throwaway bare repository standing in for `origin`, plus the working clone
/// that pushes into it.
struct Sandbox {
    // Kept alive for the whole test: dropping it removes every sandbox path.
    _temp: tempfile::TempDir,
    work: PathBuf,
    bare: PathBuf,
}

impl Sandbox {
    /// A bare `origin.git` and a `work` repository with one remote and a local
    /// identity.  The gate is *not* installed yet.
    fn new() -> Sandbox {
        let temp = tempfile::tempdir().expect("a temporary directory outside the repository");
        let root = temp.path().to_path_buf();
        let work = root.join("work");
        let bare = root.join("origin.git");
        std::fs::create_dir_all(&work).expect("the working clone directory");
        let sandbox = Sandbox {
            _temp: temp,
            work,
            bare,
        };
        sandbox
            .git_raw_at(&root, &["init", "-q", "--bare", &slash(&sandbox.bare)])
            .pipe("git init --bare");
        sandbox.git(&["init", "-q", "-b", "master"]).pipe("git init");
        sandbox
            .git(&["config", "user.name", "DR-75 test"])
            .pipe("git config user.name");
        sandbox
            .git(&["config", "user.email", "dr75@example.invalid"])
            .pipe("git config user.email");
        sandbox
            .git(&["remote", "add", "origin", &slash(&sandbox.bare)])
            .pipe("git remote add origin");
        sandbox
    }

    fn git_raw_at(&self, cwd: &Path, args: &[&str]) -> Output {
        git_command(cwd).args(args).output().expect("git is runnable")
    }

    /// git in the working clone.
    fn git(&self, args: &[&str]) -> Output {
        self.git_raw_at(&self.work, args)
    }

    fn ok(&self, args: &[&str]) -> String {
        succeeded(&self.git(args), &format!("git {}", args.join(" ")))
    }

    fn bare_ok(&self, args: &[&str]) -> String {
        succeeded(
            &self.git_raw_at(&self.bare, args),
            &format!("git -C origin.git {}", args.join(" ")),
        )
    }

    fn write(&self, relative: &str, contents: &str) {
        let path = self.work.join(relative);
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent).expect("the report directory");
        }
        std::fs::write(&path, contents).expect("the file");
    }

    fn commit_all(&self, message: &str) -> String {
        self.ok(&["add", "-A"]);
        self.ok(&["commit", "-q", "-m", message]);
        self.head()
    }

    fn commit_empty(&self, message: &str) -> String {
        self.ok(&["commit", "-q", "--allow-empty", "-m", message]);
        self.head()
    }

    /// Writes a tracked report and commits it — the marker requires the report it
    /// records to be versioned, so this is the only way to make a committable mark.
    fn commit_report(&self, message: &str) -> String {
        self.write(REPORT, REPORT_BODY);
        self.commit_all(message)
    }

    fn head(&self) -> String {
        self.ok(&["rev-parse", "HEAD"])
    }

    /// Runs the repository's versioned installer in the sandbox (no argument: the
    /// documented default, i.e. the `.githooks` directory of this checkout).
    fn install(&self) -> Output {
        command("sh", &self.work)
            .arg(slash(&repo_root().join(INSTALLER)))
            .output()
            .expect("sh is runnable")
    }

    fn uninstall(&self) -> Output {
        command("sh", &self.work)
            .arg(slash(&repo_root().join(INSTALLER)))
            .arg("--uninstall")
            .output()
            .expect("sh is runnable")
    }

    /// Runs the repository's marker writer in the sandbox.
    fn accept(&self, args: &[&str]) -> Output {
        command("sh", &self.work)
            .arg(slash(&repo_root().join(MARKER)))
            .args(args)
            .output()
            .expect("sh is runnable")
    }

    /// Runs the held hook by hand with a synthetic stdin, exactly as git would.
    fn hook_by_hand(&self, stdin: &str) -> Output {
        let mut child = command("sh", &self.work)
            .arg(slash(&repo_root().join(HOOK)))
            .arg("origin")
            .arg(slash(&self.bare))
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .expect("the hook is runnable with sh");
        // A hook that refuses before it reads stdin closes the pipe; a broken pipe
        // here is not a test failure (the payload is already in the pipe buffer).
        let _ = child
            .stdin
            .as_mut()
            .expect("piped stdin")
            .write_all(stdin.as_bytes());
        child.wait_with_output().expect("the hook terminated")
    }

    fn push(&self, args: &[&str]) -> Output {
        let mut full = vec!["push"];
        full.extend_from_slice(args);
        self.git(&full)
    }

    fn ledger_path(&self) -> PathBuf {
        self.work.join(".git").join(LEDGER_FILE)
    }

    fn ledger_text(&self) -> String {
        std::fs::read_to_string(self.ledger_path()).unwrap_or_default()
    }
}

/// Convenience so a `Command`'s `Output` can be checked inline.
trait Pipes {
    fn pipe(&self, what: &str) -> String;
}

impl Pipes for Output {
    fn pipe(&self, what: &str) -> String {
        succeeded(self, what)
    }
}

/// `pre-push` line for `sha` pushed to `ref`, with `remote_sha` already advertised.
fn line(local_sha: &str, remote_sha: &str) -> String {
    format!("refs/heads/master {local_sha} refs/heads/master {remote_sha}\n")
}

fn is_stamp(token: &str) -> bool {
    let bytes = token.as_bytes();
    bytes.len() == 20
        && bytes[4] == b'-'
        && bytes[7] == b'-'
        && bytes[10] == b'T'
        && bytes[13] == b':'
        && bytes[16] == b':'
        && bytes[19] == b'Z'
        && bytes
            .iter()
            .enumerate()
            .all(|(index, byte)| matches!(index, 4 | 7 | 10 | 13 | 16 | 19) || byte.is_ascii_digit())
}

// ---------------------------------------------------------------------------
// 1. unmarked ⇒ refused, with actionable text
// ---------------------------------------------------------------------------

#[test]
fn an_unmarked_push_is_refused_with_actionable_text() {
    let sandbox = Sandbox::new();
    // A working gate with an empty (valid) ledger: the refusal must be about the
    // commit, not about a broken marker source.
    sandbox.accept(&["init"]).pipe("accept-commit init");
    let sha = sandbox.commit_empty("a change nobody accepted");

    let output = sandbox.push(&["origin", "master"]);
    assert!(
        !output.status.success(),
        "an unmarked commit must not reach the remote:\n{}",
        text(&output)
    );
    let message = text(&output);
    assert_mentions(&message, "REFUSED", "unmarked push");
    assert_mentions(&message, "hoh pre-push gate", "unmarked push");
    assert_mentions(&message, &sha, "unmarked push must name the commit it refused");
    assert_mentions(
        &message,
        "a change nobody accepted",
        "unmarked push must name the subject so a human can tell what was blocked",
    );
    assert_mentions(
        &message,
        "scripts/accept-commit.sh mark",
        "the refusal must say how to mark the commit",
    );
    assert_mentions(
        &message,
        "--no-verify",
        "the refusal must warn that the bypass flag is not an authorisation",
    );
    assert_mentions(
        &message,
        LEDGER_FILE,
        "the refusal must name the marker source it read",
    );
    // Nothing was pushed.
    let remote = sandbox.git_raw_at(&sandbox.bare, &["rev-parse", "--verify", "master"]);
    assert!(
        !remote.status.success(),
        "the refused push must not have created master on the remote"
    );
}

// ---------------------------------------------------------------------------
// 2. marked ⇒ allowed
// ---------------------------------------------------------------------------

#[test]
fn a_marked_push_succeeds() {
    let sandbox = Sandbox::new();
    sandbox.accept(&["init"]).pipe("accept-commit init");
    let sha = sandbox.commit_report("the acceptance report for the batch");

    sandbox
        .accept(&["mark", &sha, REPORT, "pass"])
        .pipe("accept-commit mark");
    let output = sandbox.push(&["origin", "master"]);
    assert!(
        output.status.success(),
        "a commit with a passing acceptance record must be pushed:\n{}",
        text(&output)
    );

    assert_eq!(
        sandbox.bare_ok(&["rev-parse", "master"]),
        sha,
        "the remote must carry exactly the marked commit"
    );
    let ledger = sandbox.ledger_text();
    assert!(
        ledger.contains(&format!("accepted {sha} {REPORT} pass ")),
        "the ledger must record the commit, its report and the verdict:\n{ledger}"
    );
}

// ---------------------------------------------------------------------------
// 3. commits already on the remote are not re-checked
// ---------------------------------------------------------------------------

#[test]
fn commits_already_on_the_remote_are_not_rechecked() {
    let sandbox = Sandbox::new();
    sandbox.accept(&["init"]).pipe("accept-commit init");

    // History that predates the gate: pushed on purpose with the documented hole.
    let before = sandbox.commit_empty("seeded history outside the pushed range");
    sandbox
        .push(&["--no-verify", "origin", "master"])
        .pipe("the seeding push with --no-verify");

    let report_commit = sandbox.commit_report("the acceptance report");
    let after = sandbox.commit_empty("the change that must be authorised");
    sandbox
        .accept(&["mark", &report_commit, REPORT, "pass"])
        .pipe("mark the report commit");

    // `before` is unmarked but already on the remote: only the new range is judged.
    let refused = sandbox.push(&["origin", "master"]);
    assert!(
        !refused.status.success(),
        "the unmarked commit in the pushed range must be refused:\n{}",
        text(&refused)
    );
    let message = text(&refused);
    assert_mentions(&message, &after, "the refusal must name the new unmarked commit");
    assert!(
        !message.contains(&before),
        "a commit already contained by the remote must not be named again:\n{message}"
    );

    sandbox
        .accept(&["mark", &after, REPORT, "pass"])
        .pipe("mark the new commit");
    sandbox
        .push(&["origin", "master"])
        .pipe("the push once the range is authorised");
    assert_eq!(sandbox.bare_ok(&["rev-parse", "master"]), after);
}

#[test]
fn a_push_with_nothing_new_is_allowed() {
    let sandbox = Sandbox::new();
    sandbox.accept(&["init"]).pipe("accept-commit init");
    let sha = sandbox.commit_report("the acceptance report");
    sandbox
        .accept(&["mark", &sha, REPORT, "pass"])
        .pipe("mark");
    sandbox.push(&["origin", "master"]).pipe("the first push");

    let again = sandbox.push(&["origin", "master"]);
    assert!(
        again.status.success(),
        "a no-op push must not be refused:\n{}",
        text(&again)
    );
    assert!(
        !text(&again).contains("REFUSED"),
        "a no-op push must not print a refusal:\n{}",
        text(&again)
    );
}

// ---------------------------------------------------------------------------
// 4. fail closed on the marker source
// ---------------------------------------------------------------------------

#[test]
fn a_missing_marker_source_refuses_every_push() {
    let sandbox = Sandbox::new();
    let sha = sandbox.commit_empty("a change with no ledger at all");
    assert!(
        !sandbox.ledger_path().exists(),
        "the sandbox must start without a ledger"
    );

    let output = sandbox.push(&["origin", "master"]);
    assert!(
        !output.status.success(),
        "a missing marker source must refuse the push:\n{}",
        text(&output)
    );
    let message = text(&output);
    assert_mentions(&message, "REFUSED", "missing marker source");
    assert_mentions(&message, "marker source", "missing marker source");
    assert_mentions(&message, "missing", "the reason must say the source is missing");
    assert_mentions(&message, LEDGER_FILE, "the reason must name the missing path");
    assert_mentions(&message, &sha, "the changed commit is still worth naming");
}

#[test]
fn a_corrupt_marker_source_refuses_every_push() {
    let sandbox = Sandbox::new();
    sandbox.accept(&["init"]).pipe("accept-commit init");
    let sha = sandbox.commit_empty("a change behind a corrupt ledger");
    let mut ledger = sandbox.ledger_text();
    ledger.push_str("this line is not a record\n");
    std::fs::write(sandbox.ledger_path(), ledger).expect("the corrupt ledger");

    let output = sandbox.push(&["origin", "master"]);
    assert!(
        !output.status.success(),
        "a corrupt marker source must refuse the push:\n{}",
        text(&output)
    );
    let message = text(&output);
    assert_mentions(&message, "REFUSED", "corrupt marker source");
    assert_mentions(&message, "marker source", "corrupt marker source");
    assert_mentions(
        &message,
        "this line is not a record",
        "the reason must quote the offending line",
    );
    assert_mentions(
        &message,
        &sha,
        "the push is refused whichever commit was being carried",
    );
}

// ---------------------------------------------------------------------------
// 5. `--no-verify` is a documented known limit, recorded as such
// ---------------------------------------------------------------------------

#[test]
fn the_bypass_flag_is_a_recorded_known_limit() {
    let sandbox = Sandbox::new();
    let sha = sandbox.commit_empty("a change pushed through the documented hole");

    // The gate really does bite without the flag...
    let refused = sandbox.push(&["origin", "master"]);
    assert!(
        !refused.status.success(),
        "the gate must refuse the same push without the flag:\n{}",
        text(&refused)
    );

    // ...and the flag really does bypass it.  This is recorded as a known limit of
    // a local hook, not as a failure of the gate.
    let bypassed = sandbox.push(&["--no-verify", "origin", "master"]);
    assert!(
        bypassed.status.success(),
        "the bypass flag is expected to work; if it stopped working the documented \
         limit would need updating:\n{}",
        text(&bypassed)
    );
    assert_eq!(
        sandbox.bare_ok(&["rev-parse", "master"]),
        sha,
        "the bypassed push really landed on the remote"
    );
    assert!(
        !sandbox.ledger_text().contains(&sha),
        "the bypass must leave no acceptance record behind: the ledger is evidence, \
         not a receipt of the push"
    );
}

// ---------------------------------------------------------------------------
// 6. one unmarked commit in a range refuses the whole push
// ---------------------------------------------------------------------------

#[test]
fn one_unmarked_commit_in_a_multi_commit_range_refuses_the_whole_push() {
    let sandbox = Sandbox::new();
    sandbox.accept(&["init"]).pipe("accept-commit init");
    let first = sandbox.commit_report("the acceptance report");
    let second = sandbox.commit_empty("the first accepted change");
    let third = sandbox.commit_empty("the second change, not accepted yet");
    sandbox
        .accept(&["mark", &first, REPORT, "pass"])
        .pipe("mark the report commit");
    sandbox
        .accept(&["mark", &second, REPORT, "pass"])
        .pipe("mark the first change");

    let output = sandbox.push(&["origin", "master"]);
    assert!(
        !output.status.success(),
        "one unmarked commit must refuse the whole push:\n{}",
        text(&output)
    );
    let message = text(&output);
    assert_mentions(&message, &third, "the refusal must name the unmarked commit");
    assert!(
        !message.contains(&second),
        "the accepted commit must not be named as a problem:\n{message}"
    );
    // All-or-nothing: the accepted prefix must not have leaked to the remote.
    let remote = sandbox.git_raw_at(&sandbox.bare, &["rev-parse", "--verify", "master"]);
    assert!(
        !remote.status.success(),
        "a refused push must be all-or-nothing; the remote must still be empty"
    );

    sandbox
        .accept(&["mark", &third, REPORT, "pass"])
        .pipe("mark the last commit");
    sandbox.push(&["origin", "master"]).pipe("the fully accepted push");
    assert_eq!(sandbox.bare_ok(&["rev-parse", "master"]), third);
}

// ---------------------------------------------------------------------------
// boundaries the book requires to be handled explicitly
// ---------------------------------------------------------------------------

#[test]
fn deleting_a_remote_branch_is_allowed_and_carries_no_commit_check() {
    let sandbox = Sandbox::new();
    // A valid but empty ledger: the gate is armed, nothing is accepted.
    sandbox.accept(&["init"]).pipe("accept-commit init");
    sandbox.commit_empty("history the sandbox needs");
    sandbox
        .push(&["--no-verify", "origin", "master"])
        .pipe("seed master");
    sandbox
        .push(&["--no-verify", "origin", "master:refs/heads/old"])
        .pipe("seed the branch to delete");
    sandbox.bare_ok(&["rev-parse", "--verify", "refs/heads/old"]);

    let output = sandbox.push(&["origin", "--delete", "old"]);
    assert!(
        output.status.success(),
        "deleting a branch carries no new commit and must be allowed:\n{}",
        text(&output)
    );
    assert_mentions(
        &text(&output),
        "delete",
        "the hook must say it treated the deletion as such",
    );
    let gone = sandbox.git_raw_at(&sandbox.bare, &["rev-parse", "--verify", "refs/heads/old"]);
    assert!(!gone.status.success(), "the branch must really be deleted");
}

#[test]
fn a_new_remote_branch_checks_every_commit_it_adds() {
    let sandbox = Sandbox::new();
    sandbox.accept(&["init"]).pipe("accept-commit init");
    let base = sandbox.commit_report("the acceptance report");
    sandbox
        .accept(&["mark", &base, REPORT, "pass"])
        .pipe("mark the base");
    sandbox.push(&["origin", "master"]).pipe("publish the base");
    let added = sandbox.commit_empty("a new branch's change, not accepted");

    let refused = sandbox.push(&["origin", "master:refs/heads/feature"]);
    assert!(
        !refused.status.success(),
        "a brand-new remote branch must have its commits checked:\n{}",
        text(&refused)
    );
    assert_mentions(
        &text(&refused),
        &added,
        "the new-branch refusal must name the commit",
    );

    sandbox
        .accept(&["mark", &added, REPORT, "pass"])
        .pipe("mark the new branch's commit");
    sandbox
        .push(&["origin", "master:refs/heads/feature"])
        .pipe("publish the accepted branch");
    assert_eq!(sandbox.bare_ok(&["rev-parse", "refs/heads/feature"]), added);
}

#[test]
fn an_unknown_remote_object_refuses_instead_of_skipping() {
    let sandbox = Sandbox::new();
    sandbox.accept(&["init"]).pipe("accept-commit init");
    let local = sandbox.commit_empty("a change whose remote base is unknown here");

    // The remote advertised a tip this clone does not have, so the range cannot be
    // computed.  Anything that cannot be evaluated must be refused.
    let output = sandbox.hook_by_hand(&line(
        &local,
        "1111111111111111111111111111111111111111",
    ));
    assert!(
        !output.status.success(),
        "an unevaluable range must refuse:\n{}",
        text(&output)
    );
    let message = text(&output);
    assert_mentions(&message, "REFUSED", "unknown remote object");
    assert_mentions(
        &message,
        "fetch",
        "the refusal must tell the operator how to make the range evaluable",
    );
}

// ---------------------------------------------------------------------------
// the marker mechanism: commit → report → push must be cross-checkable
// ---------------------------------------------------------------------------

#[test]
fn the_ledger_records_the_report_path_and_the_pass_verdict() {
    let sandbox = Sandbox::new();
    sandbox.accept(&["init"]).pipe("accept-commit init");
    let sha = sandbox.commit_report("commit the acceptance report");
    sandbox
        .accept(&["mark", &sha, REPORT, "pass", "DR-75", "test", "batch"])
        .pipe("accept-commit mark");

    let ledger = sandbox.ledger_text();
    let records: Vec<&str> = ledger
        .lines()
        .filter(|line| !line.trim().is_empty() && !line.trim_start().starts_with('#'))
        .collect();
    assert_eq!(records.len(), 1, "exactly one record was written:\n{ledger}");
    let fields: Vec<&str> = records[0].split_whitespace().collect();
    assert_eq!(fields[0], "accepted", "the record kind: {ledger}");
    assert_eq!(fields[1], sha, "the record names the commit: {ledger}");
    assert_eq!(fields[2], REPORT, "the record names the report: {ledger}");
    assert_eq!(fields[3], "pass", "the record carries the verdict: {ledger}");
    assert!(
        is_stamp(fields[4]),
        "the record carries an ISO-8601 UTC stamp, got `{}`:\n{ledger}",
        fields[4]
    );
    assert!(
        records[0].ends_with("DR-75 test batch"),
        "the optional note is preserved: {ledger}"
    );

    // Cross-check 1: the report it cites is versioned and reachable from the commit.
    let tracked = sandbox.ok(&["ls-files", "--error-unmatch", REPORT]);
    assert!(tracked.contains(REPORT), "the report must be tracked: {tracked}");
    assert_eq!(
        sandbox.ok(&["log", "-1", "--format=%s", "--", REPORT]),
        "commit the acceptance report",
        "the report's own commit must be findable from the record"
    );
    // Cross-check 2: `show` prints the record next to the report's own verdict line.
    let shown = sandbox.accept(&["show", &sha]);
    let shown = succeeded(&shown, "accept-commit show");
    assert_mentions(&shown, &sha, "show");
    assert_mentions(&shown, REPORT, "show must name the report");
    assert_mentions(
        &shown,
        "verdict: pass",
        "show must quote the cited report's verdict line for the cross-check",
    );
}

#[test]
fn the_marker_refuses_a_missing_report_and_a_non_pass_verdict() {
    let sandbox = Sandbox::new();
    sandbox.accept(&["init"]).pipe("accept-commit init");
    let sha = sandbox.commit_report("the acceptance report");

    let missing = sandbox.accept(&["mark", &sha, ".spec/does-not-exist.md", "pass"]);
    assert!(
        !missing.status.success(),
        "recording a report that does not exist must fail:\n{}",
        text(&missing)
    );
    assert_mentions(&text(&missing), "does not exist", "missing report");

    let failing = sandbox.accept(&["mark", &sha, REPORT, "fail"]);
    assert!(
        !failing.status.success(),
        "a `fail` verdict must never authorise a push:\n{}",
        text(&failing)
    );
    assert_mentions(
        &text(&failing),
        "pass",
        "the refusal must say that only `pass` authorises a push",
    );

    let shouted = sandbox.accept(&["mark", &sha, REPORT, "PASS"]);
    assert!(
        !shouted.status.success(),
        "verdicts are exact; `PASS` is not `pass`:\n{}",
        text(&shouted)
    );

    let not_a_commit = sandbox.accept(&["mark", "not-a-commit", REPORT, "pass"]);
    assert!(
        !not_a_commit.status.success(),
        "a non-commit must be refused:\n{}",
        text(&not_a_commit)
    );

    // None of the refusals may have written a record.
    let verify = succeeded(&sandbox.accept(&["verify"]), "accept-commit verify");
    assert_mentions(&verify, "0 record", "no record may have been written");
    assert!(
        !sandbox.ledger_text().contains(&sha),
        "a refused mark must not leave a record:\n{}",
        sandbox.ledger_text()
    );

    // And the good record still goes in.
    sandbox
        .accept(&["mark", &sha, REPORT, "pass"])
        .pipe("the valid mark");
    let again = sandbox.accept(&["mark", &sha, REPORT, "pass"]);
    let again_text = succeeded(&again, "marking the same record twice");
    assert_mentions(&again_text, "already", "marking must be idempotent");
    assert_eq!(
        sandbox
            .ledger_text()
            .lines()
            .filter(|line| line.starts_with("accepted "))
            .count(),
        1,
        "marking twice must not duplicate the record:\n{}",
        sandbox.ledger_text()
    );
}

// ---------------------------------------------------------------------------
// the installer
// ---------------------------------------------------------------------------

#[test]
fn the_install_step_is_idempotent_and_arms_the_gate() {
    let sandbox = Sandbox::new();
    let expected = slash(&repo_root().join(".githooks"));

    let first = succeeded(&sandbox.install(), "the first install");
    assert_eq!(
        sandbox.ok(&["config", "--get", "core.hooksPath"]),
        expected,
        "the install must point the hooks path at the versioned directory"
    );
    assert_mentions(&first, &expected, "the install must report what it set");

    let second = succeeded(&sandbox.install(), "the second install");
    assert_eq!(
        sandbox.ok(&["config", "--get", "core.hooksPath"]),
        expected,
        "a second install must not change the value"
    );
    assert_mentions(
        &second,
        "already",
        "a second install must say there was nothing to do",
    );

    // The rollback the docs promise.
    succeeded(&sandbox.uninstall(), "the uninstall");
    assert!(
        !sandbox
            .git(&["config", "--get", "core.hooksPath"])
            .status
            .success(),
        "uninstall must remove the setting"
    );
    succeeded(&sandbox.install(), "reinstalling after the uninstall");
    assert_eq!(
        sandbox.ok(&["config", "--get", "core.hooksPath"]),
        expected
    );

    // And the installed gate really bites in this sandbox.
    sandbox.commit_empty("a change behind the installed gate");
    let refused = sandbox.push(&["origin", "master"]);
    assert!(
        !refused.status.success(),
        "after the install the gate must refuse an unaccepted push:\n{}",
        text(&refused)
    );
}

#[test]
fn the_installer_refuses_a_checkout_without_the_versioned_hooks() {
    // A copy of the installer whose sibling `.githooks` does not exist: it must fail
    // loudly rather than arm a directory with no hook in it.
    let sandbox = Sandbox::new();
    let lonely = sandbox.work.join("lonely-scripts");
    std::fs::create_dir_all(&lonely).expect("the lonely directory");
    std::fs::copy(
        repo_root().join(INSTALLER),
        lonely.join("install-hooks.sh"),
    )
    .expect("a copy of the installer");

    let output = command("sh", &sandbox.work)
        .arg(slash(&lonely.join("install-hooks.sh")))
        .output()
        .expect("sh is runnable");
    assert!(
        !output.status.success(),
        "an installer without its hooks must fail:\n{}",
        text(&output)
    );
    assert_mentions(&text(&output), "pre-push", "the failure must name what is missing");
    assert!(
        !sandbox
            .git(&["config", "--get", "core.hooksPath"])
            .status
            .success(),
        "a failed install must not have armed anything"
    );
}

// ---------------------------------------------------------------------------
// the LF invariant and the attributes pin
// ---------------------------------------------------------------------------

#[test]
fn the_shell_artifacts_keep_lf_line_endings_and_a_shebang() {
    for relative in [HOOK, LIB, INSTALLER, MARKER] {
        let bytes = std::fs::read(repo_root().join(relative))
            .unwrap_or_else(|error| panic!("{relative} must exist: {error}"));
        assert!(
            !bytes.contains(&b'\r'),
            "{relative} must be pure LF: a carriage return is the high-risk trap this \
             batch exists to pin"
        );
        assert!(
            bytes.starts_with(b"#!/bin/sh\n"),
            "{relative} must start with exactly `#!/bin/sh` followed by LF"
        );
        assert!(bytes.len() > 32, "{relative} must carry real content");
    }

    // The attributes pin is what keeps a `core.autocrlf=true` checkout (the system
    // gitconfig on this machine) from rewriting them.
    for relative in [HOOK, LIB, INSTALLER, MARKER] {
        let attrs = repo_root()
            .pipe_git(&["check-attr", "text", "--", relative]);
        assert!(
            attrs.ends_with("text: unset"),
            "{relative} must be pinned with `-text` in .gitattributes, got: {attrs}"
        );
    }
}

/// Runs git read-only in the repository under test itself.
trait RepoGit {
    fn pipe_git(&self, args: &[&str]) -> String;
}

impl RepoGit for PathBuf {
    fn pipe_git(&self, args: &[&str]) -> String {
        let output = git_command(self)
            .args(args)
            .output()
            .expect("git is runnable in the repository");
        succeeded(&output, &format!("git {}", args.join(" ")))
    }
}

// ---------------------------------------------------------------------------
// the hook speaks the pre-push protocol, and the gate and the writer agree
// ---------------------------------------------------------------------------

#[test]
fn the_hook_can_be_run_by_hand_on_a_synthetic_ref_line() {
    let sandbox = Sandbox::new();
    sandbox.accept(&["init"]).pipe("accept-commit init");
    let accepted = sandbox.commit_report("the acceptance report");
    sandbox
        .accept(&["mark", &accepted, REPORT, "pass"])
        .pipe("mark");

    // A commit that is accepted, an unchanged remote: allowed.
    let allowed = sandbox.hook_by_hand(&line(&accepted, &accepted));
    assert!(
        allowed.status.success(),
        "an accepted, no-op ref line must pass:\n{}",
        text(&allowed)
    );
    assert_mentions(
        &text(&allowed),
        "accepted -",
        "the hook reports what it checked on success",
    );

    // A deletion (`local sha` all zero) is explicitly allowed.
    let deletion = sandbox.hook_by_hand(&line(ZERO, &accepted));
    assert!(
        deletion.status.success(),
        "a deletion line must be allowed:\n{}",
        text(&deletion)
    );
    assert_mentions(
        &text(&deletion),
        "deletion",
        "the hook must say it recognised the deletion",
    );

    // No refs at all: nothing to authorise.
    let empty = sandbox.hook_by_hand("");
    assert!(
        empty.status.success(),
        "an empty protocol must not fail:\n{}",
        text(&empty)
    );

    // A malformed protocol line is refused rather than ignored.
    let malformed = sandbox.hook_by_hand("refs/heads/master\n");
    assert!(
        !malformed.status.success(),
        "a protocol line that is not four fields must be refused:\n{}",
        text(&malformed)
    );
    assert_mentions(
        &text(&malformed),
        "protocol",
        "the refusal must say the protocol line was malformed",
    );
}

#[test]
fn the_gate_and_the_writer_agree_on_ledger_validity() {
    let sandbox = Sandbox::new();
    sandbox.accept(&["init"]).pipe("accept-commit init");
    let marked = sandbox.commit_report("the acceptance report");
    let other = sandbox.commit_empty("a commit that is never marked");
    let stamp = "2026-10-01T00:00:00Z";
    let upper = marked.to_uppercase();
    let short = &marked[..39];

    let corpus: Vec<(String, bool)> = vec![
        (format!("accepted {marked} {REPORT} pass {stamp}"), true),
        (
            format!("accepted\t{marked}\t{REPORT}\tpass\t{stamp}"),
            true,
        ),
        (String::new(), true),
        ("# a comment line is not a record".to_string(), true),
        (format!("accepted {short} {REPORT} pass {stamp}"), false),
        (format!("accepted {upper} {REPORT} pass {stamp}"), false),
        (format!("accepted {marked} {REPORT} fail {stamp}"), false),
        (format!("accepted {marked} {REPORT} pass 2026-10-01"), false),
        (format!("acceptd {marked} {REPORT} pass {stamp}"), false),
        (format!("accepted {marked} report.md pass {stamp}"), false),
        (format!("accepted {marked} {REPORT} pass"), false),
    ];

    let header = sandbox
        .ledger_text()
        .lines()
        .filter(|line| line.starts_with('#'))
        .collect::<Vec<_>>()
        .join("\n");
    for (record, expected_valid) in &corpus {
        std::fs::write(sandbox.ledger_path(), format!("{header}\n{record}\n"))
            .expect("the corpus ledger");

        let verify = sandbox.accept(&["verify"]);
        let writer_says_valid = verify.status.success();

        let hook = sandbox.hook_by_hand(&line(&other, ZERO));
        let hook_message = text(&hook);
        // The gate reports an unusable ledger with a distinct phrase; a valid ledger
        // gets as far as judging `other`, which is unmarked.
        let gate_says_valid = !hook_message.contains("is not usable");

        assert_eq!(
            writer_says_valid, *expected_valid,
            "the writer's verdict on `{record}`:\n{}",
            text(&verify)
        );
        assert_eq!(
            gate_says_valid, writer_says_valid,
            "the gate and the writer must agree on `{record}`; verify said {writer_says_valid} \
             and the gate said {gate_says_valid}:\n{hook_message}"
        );
    }
}
