//! DR-86 ④: a **frozen view is never a place a role can leave a write behind**.
//!
//! `smoke-t16`'s first round ended with `result.json ok=false
//! failed_role=tester reason=contract_violation` (`qa_contaminated_candidate`)
//! and **no artifact gate at all**, because the Tester changed directory into the
//! frozen candidate view, wrote POSIX shell there, and `cmd.exe` created two
//! stray files (`({type`, `Coins`) in the project tree instead of failing.  The
//! runtime detected exactly that — `hash_tree(candidate)` before and after QA —
//! and turned the round into a contract violation, so the very evidence the round
//! existed to produce (the product's own gate verdict) was never written.
//!
//! The guard here keeps the detection, and removes the dead end.  When a role
//! writes into a view that was frozen from an immutable snapshot, the runtime
//! **restores the frozen bytes from that snapshot** (which is why the snapshot is
//! the authority, not a copy), and preserves every stray byte as evidence rather
//! than deleting it.  The round then fails **with** the artifact gate verdict the
//! battery already produced, instead of discarding that verdict and publishing a
//! `not_applicable` stub.
//!
//! **Why the round still fails.**  `REQUIREMENTS.md` R4/R13 make a QA write into
//! the frozen snapshot a rejection, and a criterion measures compliance, not
//! repairability (D295(b)).  Restoration and preservation are what make the
//! violation *auditable*; they are not a repair, and the round is judged
//! non-compliant (`ok=false`, `reason=contract_violation`) even when every byte
//! came back.  `result.json.warnings` carries `qa_contaminated_<view>_restored`,
//! and the separate watch over the adapter's configured cache excludes carries
//! `qa_wrote_cache_<view>`, so the two cases differ in `ok` *and* in those
//! warnings.  What "no role wrote" can be read from is that **whole** reading:
//! the artifact hash covers only the non-excluded paths, so equality of
//! `hash_tree` by itself proves compliance over the hashed set and nothing more.
//!
//! Two hard rules make this a guard rather than a launder:
//!
//! * **Nothing is deleted.**  An added path is *moved* to the caller's evidence
//!   directory with its bytes intact, and a modified path is *copied* there
//!   before the frozen bytes go back; a removed path is replaced by the frozen
//!   snapshot's own bytes (its contaminated bytes no longer exist to be kept).
//!   The report of what was moved is returned so the caller can record it
//!   verbatim.
//! * **Restoration is verified, not assumed.**  The caller re-hashes the view
//!   afterwards and must equal the frozen identity; a restoration that cannot be
//!   completed is reported in [`RestoreReport::failures`] and the caller fails
//!   loudly instead of publishing a view it cannot vouch for.

use std::collections::BTreeMap;
use std::path::Path;

use crate::runtime::policy::{diff_manifests, tree_manifest};

/// Where a stray byte went, and how big it was.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PreservedWrite {
    /// POSIX relative path inside the frozen view.
    pub path: String,
    pub bytes: u64,
}

/// What [`restore_frozen_view`] did.
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct RestoreReport {
    /// Paths whose frozen bytes were copied back (modified or removed).
    pub restored: Vec<String>,
    /// Paths a role added, moved out of the view with their bytes preserved.
    pub preserved: Vec<PreservedWrite>,
    /// The `hash_tree` inputs/subtractions this report was computed from.
    pub added: Vec<String>,
    pub modified: Vec<String>,
    pub removed: Vec<String>,
    /// Anything that could not be put back; non-empty means the caller must fail.
    pub failures: Vec<String>,
}

impl RestoreReport {
    /// Did the view change at all?
    pub fn is_empty(&self) -> bool {
        self.added.is_empty() && self.modified.is_empty() && self.removed.is_empty()
    }

    /// One verbatim line per difference, for a warning and for the record.
    pub fn render(&self) -> String {
        let mut text = format!(
            "added={:?} modified={:?} removed={:?} restored={} preserved={} failures={:?}",
            self.added,
            self.modified,
            self.removed,
            self.restored.len(),
            self.preserved.len(),
            self.failures
        );
        for entry in &self.preserved {
            text.push_str(&format!(
                "; preserved {} ({} byte(s))",
                entry.path, entry.bytes
            ));
        }
        text
    }
}

/// Copy `source` over `destination`, creating parents, and report a failure
/// instead of panicking when the bytes cannot be put back.
fn restore_file(source: &Path, destination: &Path) -> std::io::Result<()> {
    if let Some(parent) = destination.parent() {
        std::fs::create_dir_all(parent)?;
    }
    with_retries(|| std::fs::copy(source, destination).map(|_| ()))?;
    Ok(())
}

/// DR-86 ④: how many times a file operation of this guard is retried before a
/// transient failure becomes a verdict.
///
/// A rename or a copy can fail transiently on Windows: a just-written file may
/// still be held open by another handle (an indexer, a scanner) for a moment, and
/// a suite under load makes that more likely.  A transient failure here must
/// **not** turn into "this round cannot be judged", because that is the very
/// outcome this guard exists to remove; it is retried a bounded number of times
/// with a short pause, and only a persistent failure becomes a `failures` entry.
const FILE_OPERATION_ATTEMPTS: u32 = 10;
const FILE_OPERATION_PAUSE_MS: u64 = 25;

/// Run `operation` until it succeeds or the bounded attempt budget is spent.
fn with_retries<T>(mut operation: impl FnMut() -> std::io::Result<T>) -> std::io::Result<T> {
    let mut last: Option<std::io::Error> = None;
    for attempt in 0..FILE_OPERATION_ATTEMPTS {
        match operation() {
            Ok(value) => return Ok(value),
            Err(error) => {
                last = Some(error);
                if attempt + 1 < FILE_OPERATION_ATTEMPTS {
                    std::thread::sleep(std::time::Duration::from_millis(FILE_OPERATION_PAUSE_MS));
                }
            }
        }
    }
    Err(last
        .unwrap_or_else(|| std::io::Error::new(std::io::ErrorKind::Other, "no attempt was made")))
}

/// Move a stray file out of the frozen view, preserving its bytes.
///
/// A rename is preferred (same volume, atomic); a copy + remove is the fallback.
/// A move that cannot be completed is a failure the caller must see: the file
/// would otherwise stay inside the frozen view.
fn preserve_file(from: &Path, to: &Path) -> std::io::Result<u64> {
    if let Some(parent) = to.parent() {
        std::fs::create_dir_all(parent)?;
    }
    let bytes = std::fs::metadata(from).map(|meta| meta.len()).unwrap_or(0);
    if with_retries(|| std::fs::rename(from, to)).is_ok() {
        return Ok(bytes);
    }
    // The rename never succeeded; the fallback is retried on its own so a
    // transient failure of either half cannot leave the file in the view.
    with_retries(|| std::fs::copy(from, to).map(|_| ()))?;
    with_retries(|| std::fs::remove_file(from))?;
    Ok(bytes)
}

/// Put `root` back to the bytes `frozen` holds, preserving every role write.
///
/// `before` is the manifest of `root` **as it was when it was frozen** (the
/// caller already takes it for the contract check); `excludes` is the runtime's
/// own exclusion list, so `.hoh/**` — the Tester's legitimate submission area —
/// is never touched by this guard.
pub fn restore_frozen_view(
    root: &Path,
    frozen: &Path,
    before: &BTreeMap<String, String>,
    excludes: &[String],
    preserve_root: &Path,
) -> anyhow::Result<RestoreReport> {
    let after = tree_manifest(root, excludes)?;
    let diff = diff_manifests(before, &after);
    let mut report = RestoreReport {
        added: diff.added.clone(),
        modified: diff.modified.clone(),
        removed: diff.removed.clone(),
        ..RestoreReport::default()
    };

    for relative in diff.added {
        let from = root.join(&relative);
        let to = preserve_root.join(&relative);
        match preserve_file(&from, &to) {
            Ok(bytes) => report.preserved.push(PreservedWrite {
                path: relative,
                bytes,
            }),
            Err(error) => report.failures.push(format!(
                "{relative}: a file a role added could not be moved out of the frozen view \
                 ({error}); it is still inside the view and its bytes were not preserved"
            )),
        }
    }

    // A modified file is preserved **before** its frozen bytes go back: the
    // contaminated bytes are evidence of what the role wrote, and restoring over
    // them without a copy would destroy that evidence.
    for relative in &diff.modified {
        let contaminated = root.join(relative);
        let preserved = preserve_root.join(relative);
        if let Some(parent) = preserved.parent() {
            if std::fs::create_dir_all(parent).is_err() {
                report.failures.push(format!(
                    "{relative}: the preserved-write directory could not be created"
                ));
                continue;
            }
        }
        match std::fs::copy(&contaminated, &preserved) {
            Ok(bytes) => report.preserved.push(PreservedWrite {
                path: relative.clone(),
                bytes,
            }),
            Err(error) => report.failures.push(format!(
                "{relative}: the bytes a role wrote could not be preserved before the frozen \
                 bytes were restored ({error})"
            )),
        }
    }

    for relative in diff.modified.iter().chain(diff.removed.iter()) {
        let from = frozen.join(&relative);
        let to = root.join(&relative);
        if !from.is_file() {
            report.failures.push(format!(
                "{relative}: the frozen snapshot has no file to restore from ({}), so the \
                 contaminated byte cannot be replaced",
                from.display()
            ));
            continue;
        }
        match restore_file(&from, &to) {
            Ok(()) => report.restored.push(relative.clone()),
            Err(error) => report.failures.push(format!(
                "{relative}: the frozen bytes could not be copied back ({error})"
            )),
        }
    }

    report.restored.sort();
    Ok(report)
}

/// Is `root` back to exactly the bytes `before` describes?
pub fn matches_manifest(
    root: &Path,
    before: &BTreeMap<String, String>,
    excludes: &[String],
) -> anyhow::Result<bool> {
    Ok(tree_manifest(root, excludes)? == *before)
}

/// Preserve the bytes a role wrote into a view's **excluded cache
/// directories**, so a write the artifact identity cannot see still leaves
/// evidence and can still be judged.
///
/// The cache directories are outside `hash_tree`'s frozen identity by design
/// (R10 keeps `version_id` stable), so — unlike [`restore_frozen_view`] — there
/// is no snapshot byte to copy over a modified path and nothing to replace a
/// removed one with.  What this can do is make the write **auditable**, which is
/// the property the criterion needs: an added path is *moved* out of the view
/// (leaving the view as it was found), and a modified path's contaminated bytes
/// are *copied* aside.  Every failure is returned, never swallowed.
pub fn preserve_excluded_writes(
    root: &Path,
    preserve_root: &Path,
    diff: &crate::model::EvidenceDiff,
) -> Vec<String> {
    let mut failures = Vec::new();

    for relative in &diff.added {
        let from = root.join(relative);
        let to = preserve_root.join(relative);
        if let Err(error) = preserve_file(&from, &to) {
            failures.push(format!(
                "{relative}: a file a role added inside an excluded cache directory could not be \
                 moved out of the frozen view ({error}); it is still inside the view and its \
                 bytes were not preserved"
            ));
        }
    }

    for relative in &diff.modified {
        let from = root.join(relative);
        let to = preserve_root.join(relative);
        if let Some(parent) = to.parent() {
            if std::fs::create_dir_all(parent).is_err() {
                failures.push(format!(
                    "{relative}: the preserved-write directory could not be created"
                ));
                continue;
            }
        }
        if let Err(error) = std::fs::copy(&from, &to) {
            failures.push(format!(
                "{relative}: the bytes a role wrote inside an excluded cache directory could not \
                 be preserved ({error}); there is no frozen snapshot byte for an excluded path, \
                 so nothing can be restored over them"
            ));
        }
    }

    failures
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;

    fn write(root: &Path, relative: &str, content: &str) {
        let path = root.join(relative);
        std::fs::create_dir_all(path.parent().unwrap()).unwrap();
        std::fs::write(path, content).unwrap();
    }

    fn fixture() -> (tempfile::TempDir, PathBuf, PathBuf) {
        let temp = tempfile::tempdir().unwrap();
        let frozen = temp.path().join("frozen");
        write(&frozen, "project.godot", "config_version=5\n");
        write(&frozen, "scenes/main.tscn", "[gd_scene format=3]\n");
        write(&frozen, "scripts/player.gd", "extends Node\n");
        let view = temp.path().join("candidate");
        crate::runtime::view::copy_tree(&frozen, &view, &[]).unwrap();
        (temp, frozen, view)
    }

    /// DR-87 ⑤: the file-operation retry helper is **exercised**, not assumed.
    ///
    /// A transient Windows sharing violation must not become "the round cannot be
    /// judged"; the helper retries a bounded number of times and only then reports
    /// the error.  The failure is injected by a closure — no scheduler, no timing
    /// and no second process — so this test is deterministic: a rejected operation
    /// is re-attempted and its eventual success is returned, a permanently failing
    /// one gives up (bounded, and it is an error, not a silent success), and a
    /// first-attempt success is not retried at all.
    #[test]
    fn a_transient_file_operation_failure_is_retried_to_success() {
        let mut calls = 0u32;
        let value = with_retries(|| {
            calls += 1;
            if calls < 3 {
                Err(std::io::Error::new(
                    std::io::ErrorKind::PermissionDenied,
                    "transient",
                ))
            } else {
                Ok(calls)
            }
        })
        .expect("the operation eventually succeeds");
        assert_eq!(value, 3, "the successful attempt's value is returned");
        assert_eq!(calls, 3, "the failing attempts were really retried");

        let mut forever = 0u32;
        let error = with_retries(|| {
            forever += 1;
            Err::<(), _>(std::io::Error::new(
                std::io::ErrorKind::PermissionDenied,
                "stuck",
            ))
        })
        .expect_err("a persistent failure must stay an error");
        assert_eq!(error.kind(), std::io::ErrorKind::PermissionDenied);
        assert_eq!(
            forever, FILE_OPERATION_ATTEMPTS,
            "the retry budget is bounded exactly by the constant"
        );

        let mut once = 0u32;
        let value = with_retries(|| {
            once += 1;
            Ok(once)
        })
        .unwrap();
        assert_eq!(value, 1);
        assert_eq!(once, 1, "a success needs no second attempt");
    }

    /// The exact `smoke-t16` first-round shape: the Tester adds a stray file and
    /// rewrites a project file.  Both facts survive (the stray bytes are moved
    /// out, not deleted) and the view is back to the frozen identity, so the
    /// round can reach its gate verdict instead of dying on the violation.
    #[test]
    fn a_stray_write_is_preserved_and_the_frozen_bytes_are_restored() {
        let (temp, frozen, view) = fixture();
        let excludes = crate::runtime::policy::HashExcludes::default().merged();
        let before = tree_manifest(&view, &excludes).unwrap();

        write(&view, "({type", "");
        write(&view, "Coins", "2288\r\n");
        write(&view, "scenes/main.tscn", "visible = false)  \r\n");

        let preserve = temp.path().join("iter-1/tester-writes");
        let report = restore_frozen_view(&view, &frozen, &before, &excludes, &preserve).unwrap();

        assert!(report.failures.is_empty(), "{report:?}");
        assert_eq!(
            report.added,
            vec!["({type".to_string(), "Coins".to_string()]
        );
        assert_eq!(report.modified, vec!["scenes/main.tscn".to_string()]);
        assert!(
            matches_manifest(&view, &before, &excludes).unwrap(),
            "the frozen view must be byte-identical again: {report:?}"
        );
        assert_eq!(
            std::fs::read_to_string(view.join("scenes/main.tscn")).unwrap(),
            "[gd_scene format=3]\n",
            "the modified file must hold the frozen bytes again"
        );
        assert_eq!(
            std::fs::read_to_string(preserve.join("Coins")).unwrap(),
            "2288\r\n",
            "the stray bytes must be preserved, never deleted"
        );
        assert_eq!(report.preserved.len(), 3, "{report:?}");
        assert_eq!(
            std::fs::read_to_string(preserve.join("scenes/main.tscn")).unwrap(),
            "visible = false)  \r\n",
            "the bytes a role wrote over a frozen file are evidence too and must be kept"
        );
        assert_eq!(
            report
                .preserved
                .iter()
                .find(|entry| entry.path == "Coins")
                .map(|entry| entry.bytes),
            Some(6)
        );
    }

    /// A deleted frozen file is restored from the snapshot too, and the `.hoh`
    /// submission area — the Tester's legitimate output — is out of scope.
    #[test]
    fn a_deleted_file_is_restored_and_the_submission_area_is_never_touched() {
        let (temp, frozen, view) = fixture();
        let excludes = crate::runtime::policy::HashExcludes::default().merged();
        let before = tree_manifest(&view, &excludes).unwrap();

        std::fs::remove_file(view.join("scripts/player.gd")).unwrap();
        write(&view, ".hoh/evidence.json", "{\"qa_status\":\"fail\"}\n");

        let preserve = temp.path().join("tester-writes");
        let report = restore_frozen_view(&view, &frozen, &before, &excludes, &preserve).unwrap();

        assert!(report.failures.is_empty(), "{report:?}");
        assert_eq!(report.removed, vec!["scripts/player.gd".to_string()]);
        assert!(report.added.is_empty(), "`.hoh` is excluded: {report:?}");
        assert!(matches_manifest(&view, &before, &excludes).unwrap());
        assert_eq!(
            std::fs::read_to_string(view.join(".hoh/evidence.json")).unwrap(),
            "{\"qa_status\":\"fail\"}\n",
            "the Tester's own artifact must survive the guard"
        );
        assert!(
            !preserve.exists(),
            "nothing was added, so nothing was moved"
        );
    }

    /// Restoration is verified, not assumed: when the frozen snapshot cannot
    /// supply the byte, the guard says so and the caller can fail loudly.
    #[test]
    fn an_unrestorable_path_is_reported_as_a_failure() {
        let (temp, _frozen, view) = fixture();
        let excludes = crate::runtime::policy::HashExcludes::default().merged();
        let before = tree_manifest(&view, &excludes).unwrap();
        write(&view, "scenes/main.tscn", "fragment)  \n");

        let missing = temp.path().join("no-snapshot-here");
        let report = restore_frozen_view(
            &view,
            &missing,
            &before,
            &excludes,
            &temp.path().join("tester-writes"),
        )
        .unwrap();

        assert_eq!(report.failures.len(), 1, "{report:?}");
        assert!(report.failures[0].contains("scenes/main.tscn"));
        assert!(!matches_manifest(&view, &before, &excludes).unwrap());
    }

    /// DR-88 ④: a write into a directory the artifact identity excludes is still
    /// preserved as evidence — an added path is moved out of the view and a
    /// modified one's bytes are copied aside — so no reading can report "a role
    /// wrote nothing" while those bytes are on disk.  A failure is returned, not
    /// swallowed.
    #[test]
    fn excluded_cache_writes_are_preserved_never_swallowed() {
        let (temp, _frozen, view) = fixture();
        write(&view, ".godot/cheat.bin", "live tester bytes\n");
        write(&view, ".import/cache.bin", "changed cache\n");
        let diff = crate::model::EvidenceDiff {
            added: vec![".godot/cheat.bin".to_string()],
            modified: vec![".import/cache.bin".to_string()],
            removed: Vec::new(),
        };

        let preserve = temp.path().join("tester-writes/cache-candidate");
        let failures = preserve_excluded_writes(&view, &preserve, &diff);
        assert!(failures.is_empty(), "{failures:?}");
        assert_eq!(
            std::fs::read_to_string(preserve.join(".godot/cheat.bin")).unwrap(),
            "live tester bytes\n"
        );
        assert!(
            !view.join(".godot/cheat.bin").exists(),
            "an added cache write must be moved out of the view"
        );
        assert_eq!(
            std::fs::read_to_string(preserve.join(".import/cache.bin")).unwrap(),
            "changed cache\n"
        );

        // A preservation that cannot complete is a failure the caller must see.
        let unwritable = temp.path().join("no/such/parent");
        let only_added = crate::model::EvidenceDiff {
            added: vec!["a/b/c.bin".to_string()],
            ..Default::default()
        };
        let failures = preserve_excluded_writes(&view, &unwritable, &only_added);
        assert_eq!(failures.len(), 1, "{failures:?}");
    }
}
