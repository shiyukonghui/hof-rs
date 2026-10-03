//! The build contract (DESIGN-DETAIL §5): the frozen feature set, the frozen
//! budgets, and the lockfile hash every round records.
//!
//! Bevy is a compiled engine, so a round's cost *is* a build cost, and the
//! measured facts (SPIKE-1 §3.5, SPIKE-2 §0.2) are sharp:
//!
//! * a shared, persistent target directory turns a 5 minute cold build into a
//!   ~12–18 s warm one;
//! * **only while the feature set is frozen** — a feature-set change in the
//!   same directory recompiled `bevy`/`bevy_internal` and cost **236 s**;
//! * the lockfile must not move inside a round, and a move is not "a failure"
//!   but "this round is not comparable", which is why the hash is carried in
//!   `meta.json` instead of being a hard stop.
//!
//! The full `prepare()` implementation (running cargo, measuring, restoring the
//! budget) is the next batch's; what is frozen here is the *contract* those
//! numbers belong to, so a later implementation cannot quietly change them.

use std::path::Path;

use serde_json::json;

use crate::adapter::AdapterError;

/// The pinned Bevy version (D296: 0.19.1).
pub const BEVY_VERSION: &str = "0.19.1";

/// The frozen Bevy feature set.  `bevy_remote` is the observation surface
/// (SPIKE-1 §1.4); everything else is Bevy's default set, which the PRD's
/// dependency line leaves on.
pub const FROZEN_FEATURES: &[&str] = &["bevy_remote"];

/// Whether Bevy's default features stay enabled.  Turning them off is route B in
/// SPIKE-2 (no `bevy_winit` in the dependency graph at all) and would remove
/// `Sprite`/`Camera2d` from the game's source — a different contract, not a
/// performance tweak.
pub const FROZEN_DEFAULT_FEATURES: bool = true;

/// The budget upper bounds (DESIGN-DETAIL §5, SPIKE-2 §10-7).
pub const COLD_BUILD_BUDGET_MILLIS: u64 = 600_000;
pub const WARM_BUILD_BUDGET_MILLIS: u64 = 120_000;
pub const ROUND_BUDGET_MILLIS: u64 = 300_000;
pub const ENDPOINT_READY_BUDGET_MILLIS: u64 = 30_000;

/// The frozen feature set's hash, recorded in `meta.json.feature_sha256`.  A
/// drift here is what makes a warm build 236 s instead of 12 s, so it is
/// measured per round rather than assumed.
pub fn feature_set_sha256() -> String {
    crate::runtime::policy::sha256_hex(
        crate::adapter::bevy::contract::canonical_json(&feature_set_value()).as_bytes(),
    )
}

/// The pinned feature-set hash literal (see [`feature_set_sha256`]).  A drift in
/// the feature set is what turns a warm 12 s build into a 236 s rebuild, so the
/// hash is recorded per round and pinned here.
pub const FEATURE_SET_SHA256: &str =
    "d6a90ba39e67b9e05fd28d97cc570dc989a03e8ec7a15ba93d077d5fe95d1f96";

/// `sha256` of a `Cargo.lock`'s bytes, or an explicit task-level failure when it
/// cannot be read (an unreadable lockfile is not a lockfile that did not drift).
pub fn lockfile_sha256(path: &Path) -> Result<String, AdapterError> {
    let bytes = std::fs::read(path).map_err(|error| {
        AdapterError::Malformed(format!("`{}` could not be read: {error}", path.display()))
    })?;
    Ok(crate::runtime::policy::sha256_hex(&bytes))
}

/// DESIGN-DETAIL §5: the lockfile must not change inside a round.  Drift is
/// reported, not repaired.
pub fn lockfile_matches(expected_sha256: &str, path: &Path) -> Result<(), AdapterError> {
    let actual = lockfile_sha256(path)?;
    if actual == expected_sha256 {
        return Ok(());
    }
    Err(AdapterError::Malformed(format!(
        "the lockfile changed inside the round: expected {expected_sha256}, measured {actual} — \
         this round is not comparable with its predecessors"
    )))
}

/// The three budget bounds a completed build is judged against.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct BuildBudget {
    pub cold_millis: u64,
    pub warm_millis: u64,
    pub round_millis: u64,
}

impl Default for BuildBudget {
    fn default() -> Self {
        Self {
            cold_millis: COLD_BUILD_BUDGET_MILLIS,
            warm_millis: WARM_BUILD_BUDGET_MILLIS,
            round_millis: ROUND_BUDGET_MILLIS,
        }
    }
}

impl BuildBudget {
    /// `warm == true` writes a round that reused the persistent target
    /// directory, so the warm bound applies.
    pub fn exceeded(&self, elapsed_millis: u64, warm: bool) -> Option<u64> {
        let bound = if warm {
            self.warm_millis
        } else {
            self.cold_millis
        };
        (elapsed_millis > bound).then_some(bound)
    }
}

/// The feature-set document the hash is taken over.  It is a value, not a
/// comment, so changing a feature necessarily changes the hash.
pub fn feature_set_value() -> serde_json::Value {
    json!({
        "bevy": BEVY_VERSION,
        "default_features": FROZEN_DEFAULT_FEATURES,
        "features": FROZEN_FEATURES,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn the_budgets_are_the_designs_numbers() {
        assert_eq!(COLD_BUILD_BUDGET_MILLIS, 600_000);
        assert_eq!(WARM_BUILD_BUDGET_MILLIS, 120_000);
        assert_eq!(ROUND_BUDGET_MILLIS, 300_000);
        assert_eq!(ENDPOINT_READY_BUDGET_MILLIS, 30_000);
        assert_eq!(BEVY_VERSION, "0.19.1");
    }

    #[test]
    fn a_warm_overrun_is_judged_against_the_warm_bound() {
        let budget = BuildBudget::default();
        assert_eq!(budget.exceeded(100_000, true), None);
        assert_eq!(budget.exceeded(100_000, false), None);
        assert_eq!(budget.exceeded(150_000, true), Some(120_000));
        assert_eq!(budget.exceeded(150_000, false), None);
        assert_eq!(budget.exceeded(700_000, false), Some(600_000));
    }

    #[test]
    fn the_feature_hash_is_pinned_and_moves_with_the_feature_set() {
        assert_eq!(feature_set_sha256(), FEATURE_SET_SHA256);
        let value = feature_set_value();
        assert_eq!(
            canonical(&value),
            r#"{"bevy":"0.19.1","default_features":true,"features":["bevy_remote"]}"#
        );
    }

    #[test]
    fn a_lockfile_drift_is_reported_verbatim() {
        let dir = tempfile::tempdir().unwrap();
        let lock = dir.path().join("Cargo.lock");
        std::fs::write(&lock, b"# locked\n").unwrap();
        let hash = lockfile_sha256(&lock).unwrap();
        assert!(lockfile_matches(&hash, &lock).is_ok());
        std::fs::write(&lock, b"# drifted\n").unwrap();
        let error = lockfile_matches(&hash, &lock).unwrap_err();
        assert!(error.to_string().contains("not comparable"), "{error}");
    }

    #[test]
    fn an_unreadable_lockfile_is_an_error_not_an_empty_hash() {
        let error = lockfile_sha256(Path::new("no-such-lockfile-anywhere.lock")).unwrap_err();
        assert!(error.to_string().contains("could not be read"), "{error}");
    }

    fn canonical(value: &serde_json::Value) -> String {
        crate::adapter::bevy::contract::canonical_json(value)
    }
}
