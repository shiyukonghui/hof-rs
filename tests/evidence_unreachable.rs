//! DR-61 — the previous round's evidence must be **structurally unreachable**.
//!
//! DR-59 moved the previous round's `.hoh/deterministic/**` aside, but the
//! quarantine landed at `.hoh/deterministic.stale-<ts>/` — still **inside** the
//! role's working directory. Independent acceptance (DR-59 acceptance report,
//! DEF-1) measured with its own probe that a wildcard read still reaches those
//! bytes:
//!
//! ```text
//! PROBE-A stale marker still reachable from the Developer cwd at:
//! [".hoh/deterministic.stale-1790684826/battery.json",
//!  ".hoh/deterministic.stale-1790684826/raw/input_channel_probe.json"]
//! ```
//!
//! and DEF-2 measured that `.hoh/evidence/**` is never isolated at all and that
//! `view::copy_evidence` copies every file under it — the stale ones included —
//! straight into the Tester's frozen candidate view.
//!
//! The invariant this file fixes is deliberately stated as a **filesystem walk**
//! (`ls .hoh/**`), not as "the prompt-named path is empty": the point of DR-61 is
//! that a *traversal* of the working directory must not reach the previous
//! round's evidence either.
//!
//! Every marker below is a unique string, so "the walk reached it" can only mean
//! the seed itself: the round's own fresh artifacts (which legitimately do live
//! under `.hoh/` while the round runs) can never match byte-for-byte.

mod common;

use std::collections::BTreeMap;
use std::path::{Path, PathBuf};
use std::sync::Arc;

use common::{
    happy_script, test_config, write, write_spec, FakeAdapter, FakeHarness, FakeToolChannel,
    InvocationRecord,
};
use hof_rs::model::{Ablation, Role};

/// The previous round's evidence, seeded exactly where a finished round leaves
/// it on disk — including the two paths the independent probe measured.
const SEEDS: &[(&str, &str)] = &[
    (
        ".hoh/deterministic/battery.json",
        "DR-61 previous-round deterministic battery: pid 108432 (UNAVAILABLE: the editor is not clean)\n",
    ),
    (
        ".hoh/deterministic/raw/input_channel_probe.json",
        "DR-61 previous-round raw probe: Connection Failed: (os error 10061)\n",
    ),
    (
        ".hoh/evidence/frame-00.png",
        "DR-61 previous-round evidence frame-00.png (the 4246-byte smoke-t6 PNG)\n",
    ),
    (
        ".hoh/evidence/replay/round-one.json",
        "DR-61 previous-round evidence replay payload\n",
    ),
    (
        ".hoh/args/probe.json",
        "DR-61 previous-round MCP argument payload\n",
    ),
    (
        ".hoh/scratch/gtools.txt",
        "DR-61 previous-round scratch probe output\n",
    ),
    (
        ".hoh/evidence.json",
        "DR-61 previous-round evidence bundle\n",
    ),
    // The remaining `.hoh` siblings a real workspace carries (measured against
    // the `smoke-t7` pre-run inventory and `.workspace/mario/.hoh`).  These are
    // the ones this batch deliberately does *not* quarantine, because the round
    // rewrites them with its own content before the role that reads them runs
    // (`write_inputs(&workspace, …)`, `run_loop.rs:672-697`).  They are seeded
    // anyway: "measured as overwritten" is a claim this test now checks instead
    // of asserting.
    (".hoh/TASK.md", "DR-61 previous-round task text\n"),
    (".hoh/plan.md", "DR-61 previous-round plan\n"),
    (".hoh/TOOLS.md", "DR-61 previous-round tool index\n"),
    (
        ".hoh/EVIDENCE_HISTORY.md",
        "DR-61 previous-round evidence history\n",
    ),
    (".hoh/PROJECT_MAP.md", "DR-61 previous-round project map\n"),
    (".hoh/SCAFFOLD.md", "DR-61 previous-round scaffold\n"),
    (
        ".hoh/skills/godot-dev.md",
        "DR-61 previous-round developer skill\n",
    ),
    (
        ".hoh/skills/godot-testing.md",
        "DR-61 previous-round testing skill\n",
    ),
];

/// The previous round's evidence harvest in the candidate-view scenario
/// (DEF-2): what the acceptance probe seeded before opening the new round.
const PREVIOUS_EVIDENCE_PNG: &str = "DR-61 previous-round frame-00.png: 4246 bytes of smoke-t6\n";
const PREVIOUS_EVIDENCE_REPLAY: &str = "DR-61 previous-round replay: round-one payload\n";

fn seed_previous_round(workspace: &Path) {
    for (relative, content) in SEEDS {
        write(&workspace.join(relative), content);
    }
}

/// A recursive walk of `root` — literally what `ls .hoh/**` / a directory walk
/// does — returning `relative path -> bytes`.
fn walk(root: &Path) -> BTreeMap<String, Vec<u8>> {
    let mut files = BTreeMap::new();
    if !root.exists() {
        return files;
    }
    for entry in walkdir::WalkDir::new(root).follow_links(false) {
        let Ok(entry) = entry else { continue };
        if !entry.file_type().is_file() {
            continue;
        }
        let relative = entry
            .path()
            .strip_prefix(root)
            .unwrap_or(entry.path())
            .components()
            .map(|component| component.as_os_str().to_string_lossy().into_owned())
            .collect::<Vec<_>>()
            .join("/");
        let bytes = std::fs::read(entry.path()).unwrap_or_default();
        files.insert(relative, bytes);
    }
    files
}

/// Every walked path whose bytes are exactly this seed.
fn reaches<'a>(walked: &'a BTreeMap<String, Vec<u8>>, seed: &str) -> Vec<&'a String> {
    walked
        .iter()
        .filter(|(_, bytes)| bytes.as_slice() == seed.as_bytes())
        .map(|(path, _)| path)
        .collect()
}

fn developer_view(records: &[InvocationRecord]) -> BTreeMap<String, String> {
    records
        .iter()
        .find(|record| record.role == Role::Developer)
        .expect("the script always invokes the Developer")
        .files
        .clone()
}

fn role_view(records: &[InvocationRecord], role: Role) -> BTreeMap<String, String> {
    records
        .iter()
        .find(|record| record.role == role)
        .unwrap_or_else(|| panic!("the script always invokes {role:?}"))
        .files
        .clone()
}

/// One whole round with an explicit run id, over the shared workspace.
async fn run_round(root: &Path, run_id: &str) -> Vec<InvocationRecord> {
    let mut cfg = test_config(root, 1);
    cfg.runtime.spec = root.join("spec.md");
    let spec = write_spec(root);
    let harness = FakeHarness::new(happy_script());
    let observer = harness.clone();
    let orchestrator = hof_rs::runtime::run_loop::Orchestrator {
        harness: Box::new(harness),
        adapter: Box::new(FakeAdapter::new()),
        tools: Arc::new(FakeToolChannel::new()),
        cfg,
        ablation: Ablation::default(),
        force_init: true,
        start_state: hof_rs::runtime::start_state::StartState::as_is(),
    };
    hof_rs::runtime::run_loop::run(&orchestrator, &spec, run_id)
        .await
        .expect("the round itself must still run");
    observer.records()
}

fn quarantine_dir(root: &Path, run_id: &str) -> PathBuf {
    root.join("runs").join(run_id).join("quarantine")
}

/// DR-61 (the regression invariant): after a round opens over a polluted
/// workspace, a wildcard/directory walk of `.hoh` must not reach one byte of the
/// previous round's evidence — and the bytes must still exist, outside the role's
/// working directory, because the move is never a delete.
#[tokio::test]
async fn a_wildcard_walk_of_hoh_cannot_reach_the_previous_rounds_evidence() {
    let temp = tempfile::tempdir().expect("tempdir");
    let root = temp.path();
    let workspace = root.join("workspace");
    seed_previous_round(&workspace);

    let records = run_round(root, "run-1").await;

    // (1) The invariant, measured as a real filesystem walk of the role's cwd.
    let hoh = walk(&workspace.join(".hoh"));
    for (relative, seed) in SEEDS {
        let hits = reaches(&hoh, seed);
        assert!(
            hits.is_empty(),
            "DR-61: the wildcard walk of `.hoh` still reaches the previous round's \
             {relative} at {hits:?}; reached keys: {:?}",
            hoh.keys().collect::<Vec<_>>()
        );
    }
    // The same walk must not see the quarantine either: it is not a `.hoh`
    // sibling any more.
    let stale: Vec<&String> = hoh.keys().filter(|key| key.contains(".stale-")).collect();
    assert!(
        stale.is_empty(),
        "DR-61: a superseded `.stale-*` entry is still a walkable path inside the \
         role's cwd: {stale:?}"
    );

    // (1b) The role's working directory *is* the workspace, so walk all of it:
    // moving the quarantine to a sibling of `.hoh` inside the cwd would leave it
    // reachable (and would even be copied into the role views, which only
    // exclude `.hoh`/`.git`).
    let cwd = walk(&workspace);
    for (relative, seed) in SEEDS {
        let hits = reaches(&cwd, seed);
        assert!(
            hits.is_empty(),
            "DR-61: a walk of the role's cwd still reaches the previous round's \
             {relative} at {hits:?}"
        );
    }
    let cwd_stale: Vec<&String> = cwd.keys().filter(|key| key.contains(".stale-")).collect();
    assert!(
        cwd_stale.is_empty(),
        "DR-61: the quarantine is still inside the role's working directory: {cwd_stale:?}"
    );

    // (2) The Developer's own view of its cwd at invocation time agrees.
    let files = developer_view(&records);
    for (relative, seed) in SEEDS {
        assert!(
            !files
                .keys()
                .filter(|key| key.starts_with(".hoh/"))
                .any(|key| files.get(key).map(String::as_str) == Some(*seed)),
            "DR-61: the Developer's cwd still carries the previous round's {relative}"
        );
    }

    // (2b) The Planner is invoked *before* the round writes anything into the
    // workspace, so its view is where a stale `.hoh` sibling would land first.
    let planner = role_view(&records, Role::Planner);
    for (relative, seed) in SEEDS {
        assert!(
            !planner.values().any(|content| content.as_str() == *seed),
            "DR-61: the Planner's view still carries the previous round's {relative}"
        );
    }

    // (3) Preservation: every seed survives, byte-for-byte, outside the cwd.
    let quarantine = quarantine_dir(root, "run-1");
    assert!(
        !quarantine.starts_with(&workspace),
        "DR-61: the quarantine must live outside the role's working directory: {}",
        quarantine.display()
    );
    let kept = walk(&quarantine);
    for (relative, seed) in SEEDS {
        let hits = reaches(&kept, seed);
        assert_eq!(
            hits.len(),
            1,
            "DR-61: the previous round's {relative} must be preserved exactly once \
             under {} (found {hits:?}); kept entries: {:?}",
            quarantine.display(),
            kept.keys().collect::<Vec<_>>()
        );
    }
}

/// DR-61 / DEF-2 (the candidate view): the Tester evaluates a **frozen
/// candidate**, so a previous round's evidence file must never be copied into it.
/// The shape is the faithful one: round one really leaves evidence behind, the
/// previous round's evidence harvest is then on disk (the acceptance probe's
/// `frame-00.png`), and round two opens.
#[tokio::test]
async fn the_tester_candidate_view_never_carries_the_previous_rounds_evidence() {
    let temp = tempfile::tempdir().expect("tempdir");
    let root = temp.path();
    let workspace = root.join("workspace");

    run_round(root, "run-1").await;
    let left_behind = workspace.join(".hoh/deterministic/build.json");
    assert!(
        left_behind.is_file(),
        "round one must really have left deterministic evidence behind: {left_behind:?}"
    );
    write(
        &workspace.join(".hoh/evidence/frame-00.png"),
        PREVIOUS_EVIDENCE_PNG,
    );
    write(
        &workspace.join(".hoh/evidence/replay/round-one.json"),
        PREVIOUS_EVIDENCE_REPLAY,
    );

    let second = run_round(root, "run-2").await;

    let tester = role_view(&second, Role::Tester);
    assert!(
        !tester.contains_key(".hoh/evidence/frame-00.png"),
        "DR-61/DEF-2: the previous round's frame-00.png is still in the frozen \
         candidate view: {:?}",
        tester
            .keys()
            .filter(|key| key.starts_with(".hoh/evidence/"))
            .collect::<Vec<_>>()
    );
    for marker in [PREVIOUS_EVIDENCE_PNG, PREVIOUS_EVIDENCE_REPLAY] {
        assert!(
            !tester.values().any(|content| content.as_str() == marker),
            "DR-61/DEF-2: the frozen candidate view still carries the previous \
             round's evidence bytes"
        );
    }
    // The copy machinery is still alive: this round's own deterministic evidence
    // reaches the candidate exactly as DR-36 requires.
    assert!(
        tester.keys().any(|key| key.starts_with(".hoh/deterministic/")),
        "DR-61: this round's own deterministic evidence must still be copied into \
         the candidate: {:?}",
        tester.keys().collect::<Vec<_>>()
    );

    // And the previous round's bytes were moved out of the cwd, not deleted.
    let kept = walk(&quarantine_dir(root, "run-2"));
    for (relative, marker) in [
        (".hoh/evidence/frame-00.png", PREVIOUS_EVIDENCE_PNG),
        (
            ".hoh/evidence/replay/round-one.json",
            PREVIOUS_EVIDENCE_REPLAY,
        ),
    ] {
        assert_eq!(
            reaches(&kept, marker).len(),
            1,
            "DR-61: {relative} must be preserved under the quarantine, not deleted"
        );
    }
    assert!(
        reaches(&walk(&workspace.join(".hoh")), PREVIOUS_EVIDENCE_PNG).is_empty(),
        "DR-61: the previous round's PNG is still reachable inside the cwd"
    );
}

/// DR-61 counter-direction: a clean round start has nothing to isolate and must
/// not litter the run directory with an empty quarantine.
#[tokio::test]
async fn a_clean_round_start_creates_no_quarantine_directory() {
    let temp = tempfile::tempdir().expect("tempdir");
    let root = temp.path();

    run_round(root, "run-1").await;

    assert!(
        !quarantine_dir(root, "run-1").exists(),
        "DR-61: a clean round start must not create a quarantine directory"
    );
}
