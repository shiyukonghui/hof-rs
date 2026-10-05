//! The frozen PRD's **surfaces**, with stable ids and a decider for each.
//!
//! ## Why this module exists
//!
//! Round 4's `hoh run` ended with `prd coverage: 6/8 verified`.  The acceptance
//! (`.spec/bevy/ACCEPTANCE-ROUNDS.md` RA-5) established that the `8` was **the
//! Tester's own claim count**: `PrdCoverage::total()` falls back to
//! `verified + gap` whenever no claim id is an `F1..F17` id, and no round-4
//! claim id was one.  So the figure said "the Tester wrote eight claims and
//! verified six", it said nothing about the PRD, and it could not be compared
//! with round 3's `7/8` — a different Tester wrote a different eight.
//!
//! This module is the repair.  The denominator is [`PRD_SURFACES`]: a
//! compile-time constant list of the frozen `PRD.md`'s own requirement surfaces.
//! Two rounds produce a comparable figure because the denominator cannot move;
//! a Tester who writes two claims, or twenty, does not change it.
//!
//! ## What "stable" means here
//!
//! Every entry carries an [`anchor`](PrdSurface::anchor): a literal substring
//! that must occur in the frozen `.spec/bevy/PRD.md`.  The document may only be
//! extended *below* its seal (`PRD.md` 附录 B2), so an anchor is a durable
//! pointer into frozen text, and a test recomputes the whole set against the
//! file.  A surface id that no longer has its anchor is a red test, not a
//! silently smaller denominator.
//!
//! ## The three deciders, and why none of them is the Tester
//!
//! * [`Decider::Steps`] — the harness's **deterministic battery** decides it.
//!   The named step ids must all have run and observed (`ok = true`, which the
//!   battery only sets when the observation was really made: a read that failed
//!   inside a phase is `ok = false` with a `not observed` reason, never a pass).
//! * [`Decider::Invariant`] — a frozen constant or seal **in this repository**
//!   decides it, recomputed by the test named in the evidence.  These are
//!   properties of the toolchain and of the frozen documents, not observations
//!   of a game, and the evidence string says so.
//! * [`Decider::Unobservable`] — the harness cannot decide it.  It is reported
//!   as an explicit, **named** gap with its reason, which is the point: a
//!   surface nobody claims must not be able to look like a surface that passed.
//!
//! ## What this module is not
//!
//! It does not replace the Tester's claims.  `PrdCoverage` keeps deriving
//! `verified`/`gap` from the Tester's own lists, and the run line keeps
//! publishing that figure with its own honest label.  What changes is which of
//! the two figures is the headline.

use crate::model::{PrdSurfaceCoverage, PrdSurfaceVerdict, SurfaceStatus};

/// How a surface is decided.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Decider {
    /// Verified iff every named battery **step id** ran and observed.
    Steps(&'static [&'static str]),
    /// Decided by a frozen constant, seal or committed evidence file in this
    /// repository; the string names the mechanism and the test that recomputes
    /// it.  No game behaviour is involved.
    Invariant(&'static str),
    /// The harness cannot decide it from its own evidence.  The string is the
    /// reason, and it is published verbatim.
    Unobservable(&'static str),
}

/// One surface of the frozen PRD.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct PrdSurface {
    /// The stable id.  `P1..P5` and `C1..C6` are the document's own labels;
    /// `Q-*` ids the four §4 clauses the document bolds; `B2.*` ids 附录 B2's
    /// four subsections.
    pub id: &'static str,
    /// A literal that must occur in the frozen `.spec/bevy/PRD.md`.
    pub anchor: &'static str,
    /// The requirement, quoted from the frozen document rather than restated.
    pub title: &'static str,
    pub decider: Decider,
}

/// The frozen registry, in document order: §2, §3, §4, 附录 B2.
///
/// `ids()` is checked against [`EXPECTED_IDS`] by a test, so adding, renaming or
/// dropping a surface is a red test and never a quiet change to the denominator.
pub const PRD_SURFACES: &[PrdSurface] = &[
    PrdSurface {
        id: "P1",
        anchor: "| **P1** |",
        title: "the player moves left and right under injected input, and releasing the input \
                stops it (no residual drift)",
        decider: Decider::Steps(&[
            "e3_movement",
            "e3_movement_left",
            "e3_movement_release",
        ]),
    },
    PrdSurface {
        id: "P2",
        anchor: "| **P2** |",
        title: "coins exist and a contact raises the coin count from 0",
        decider: Decider::Steps(&["e3_coin_counter"]),
    },
    PrdSurface {
        id: "P3",
        anchor: "| **P3** |",
        title: "reaching the goal flips the win flag false -> true, one way, never back",
        decider: Decider::Steps(&["e3_win_flag", "e3_win_position"]),
    },
    PrdSurface {
        id: "P4",
        anchor: "| **P4** |",
        title: "the player jumps: rise first, then fall, then back to the ground",
        decider: Decider::Steps(&["e3_jump_arc"]),
    },
    PrdSurface {
        id: "P5",
        anchor: "| **P5** |",
        title: "the ground state is readable: true on the ground, false while airborne",
        decider: Decider::Steps(&["e3_grounded", "e3_grounded_payload"]),
    },
    PrdSurface {
        id: "C1",
        anchor: "**C1 插件与特性**",
        title: "`bevy_remote` + `RemotePlugin` + `RemoteHttpPlugin` + `ScheduleRunnerPlugin`, one \
                binary with the runtime no-window switch",
        decider: Decider::Steps(&["editor_errors_baseline", "play_scene_ready"]),
    },
    PrdSurface {
        id: "C2",
        anchor: "**C2 可反射语义面",
        title: "the frozen reflectable semantic surfaces exist at their frozen type paths",
        // `editor_errors_baseline` is the step whose own observation names the
        // contract type paths it compared against the frozen list; a candidate
        // that declares fewer never produces an `ok` build step at all.
        decider: Decider::Steps(&["editor_errors_baseline"]),
    },
    PrdSurface {
        id: "C3",
        anchor: "**C3 注入语义**",
        title: "the injection surface is level-triggered and the game clears the edge itself",
        decider: Decider::Steps(&["e3_movement", "e3_movement_release"]),
    },
    PrdSurface {
        id: "C4",
        anchor: "**C4 一致性**",
        title: "semantic reads are per call; no JSON-RPC batch is used as a consistency snapshot",
        decider: Decider::Invariant(
            "the thin MCP layer sends exactly one JSON-RPC request per call — \
             src/adapter/mcp/server.rs has no batch path and crate::adapter::brp issues one \
             request per read — and every recorded raw call file under \
             evidence/observation/round4/deterministic/raw/ carries a single request, which \
             tests/evidence_reproduction.rs recomputes",
        ),
    },
    PrdSurface {
        id: "C5",
        anchor: "**C5 状态不得藏在不可反射处**",
        title: "key state must not live only in a non-reflectable engine resource",
        decider: Decider::Unobservable(
            "the harness can prove that every criterion's evidence comes from a registered \
             reflectable surface (that is C2), but it cannot enumerate a game's internal state \
             to prove no key state lives outside one; that would be a claim about source that no \
             frozen surface exposes. Not closed by this batch, and named rather than omitted",
        ),
    },
    PrdSurface {
        id: "C6",
        anchor: "**C6 无截图要求**",
        title: "the PRD requires no screenshot capability",
        decider: Decider::Unobservable(
            "a NON-requirement: §3-C6 states that screenshots are not required, so no observation \
             of a game can satisfy it and none should try. It is a scope statement about the \
             frozen document; the document's own seal is what would change it",
        ),
    },
    PrdSurface {
        id: "Q-scale",
        anchor: "**玩法规模**",
        title: "one small level is enough; no multi-level, no art assets, geometry primitives are \
                acceptable",
        decider: Decider::Unobservable(
            "the harness observes behaviour through reflectable state; no frozen surface describes \
             a scene's geometry, its level count or whether art assets were used, so 'the scale \
             is small enough' is not decidable in-process",
        ),
    },
    PrdSurface {
        id: "Q-startup",
        anchor: "**启动**",
        title: "in headless mode the process must keep running for at least one round budget and \
                must not exit by itself",
        decider: Decider::Steps(&["play_scene_ready", "e3_process_liveness"]),
    },
    PrdSurface {
        id: "Q-not-required",
        anchor: "**不要求**",
        title: "audio, menus, saves, multiplayer and a level editor are out of scope",
        decider: Decider::Unobservable(
            "a NON-requirement: §4 lists what is not required, and the absence of a feature is not \
             positively observable by a harness that can only read state the game declares",
        ),
    },
    PrdSurface {
        id: "Q-perf",
        anchor: "**性能**",
        title: "in headless mode the logic frame rate is high enough to separate a jump's rise \
                from its fall within tens of frames",
        decider: Decider::Steps(&["e3_jump_arc"]),
    },
    PrdSurface {
        id: "B2.1",
        anchor: "## B2.1 第七个可反射语义面：游戏帧计数（D297 (b)）",
        title: "the game exposes its own frame counter and a reading's `frame` reports it, never \
                the adapter's observation ordinal",
        decider: Decider::Steps(&["e3_process_liveness"]),
    },
    PrdSurface {
        id: "B2.2",
        anchor: "## B2.2 游戏侧 crate 名与契约模块（D297 (a)）",
        title: "the game crate is the frozen `hof_game` and its contract module is \
                `hof_game::contract`",
        // `BevyAdapter::prepare` refuses a differently-named crate before the
        // build step can run, so an `ok` build step carries this with it.
        decider: Decider::Steps(&["editor_errors_baseline"]),
    },
    PrdSurface {
        id: "B2.3",
        anchor: "## B2.3 语义层返回形状进入工具清单（D297 (c)）",
        title: "every semantic verb's return shape appears as an `outputSchema` in `tools/list` \
                and counts toward `TOOL_LIST_SHA256`",
        decider: Decider::Invariant(
            "crate::adapter::mcp::TOOL_LIST_SHA256 is the pinned hash of the whole tool list, \
             output schemas included; tests/tool_discovery.rs recomputes it from this tree, so a \
             return shape that changed without re-freezing is a red test",
        ),
    },
    PrdSurface {
        id: "B2.4",
        anchor: "## B2.4 未变项",
        title: "附录 B2 changes none of P1..P5 or C1..C6",
        decider: Decider::Invariant(
            "the append-only seal: src/adapter/bevy/prd.rs pins the SHA-256 of every byte above \
             the seal marker, and tests/bevy_adapter_b2.rs::the_prd_sealed_prefix_is_byte_identical \
             fails if a rewrite moves it",
        ),
    },
];

/// The registry's ids in order — the denominator, spelled out.
///
/// A test compares it with [`PRD_SURFACES`], so the denominator cannot change
/// without a red test naming the change.
pub const EXPECTED_IDS: &[&str] = &[
    "P1",
    "P2",
    "P3",
    "P4",
    "P5",
    "C1",
    "C2",
    "C3",
    "C4",
    "C5",
    "C6",
    "Q-scale",
    "Q-startup",
    "Q-not-required",
    "Q-perf",
    "B2.1",
    "B2.2",
    "B2.3",
    "B2.4",
];

/// The two ids the round-4 Tester authored that are **not** PRD surfaces, kept
/// with their disposition so a reader can find them by the name that was
/// published.
///
/// * `P3-goal-x` asked for the **goal entity's own world position** as
///   reflectable state.  The frozen contract (§3-C2, and 附录 B2.1) declares
///   eight surfaces and none of them is a goal; adding one would be a contract
///   change, which this batch has no authority to make.  What the harness can
///   observe is the *player's* position at the win frame
///   (`e3_win_position`), which locates the win in the world; that is what
///   decides `P3` above.  The residual is therefore an
///   [`SurfaceStatus::Unobservable`] item *outside* the PRD denominator, and it
///   is reported as such rather than dropped.
/// * `S1-deterministic-step` asked for a persisted late-round liveness step under
///   `.hoh/deterministic/raw/`.  That one **is** observable and **is** closed by
///   this batch: the `e3_process_liveness` battery step reads the game's own
///   frame counter, waits, reads it again, requires the frame count to advance by
///   the number asked for, and persists `raw/e3_process_liveness.json`.  It is
///   what decides `Q-startup` and `B2.1`.
pub const RESIDUALS: &[(&str, &str)] = &[
    (
        "P3-goal-x",
        "not a PRD surface: the goal entity's own position is not one of the eight frozen \
         contract surfaces, and adding a ninth is a contract change. The harness observes the \
         player's world position at the win frame instead, which is what decides P3",
    ),
    (
        "S1-deterministic-step",
        "closed by the e3_process_liveness battery step, which decides Q-startup and B2.1",
    ),
];

/// Decide every registry item from the **battery's own step outcomes**.
///
/// `steps` is the `(step_id, ok)` list one battery pass records.  A `Steps`
/// decider is `Verified` only when every named step is present **and** `ok`; an
/// absent step is a `gap` naming it, never a pass.  Nothing here reads the
/// Tester's claims, so the same battery produces the same figure in every round.
pub fn decide(steps: &[(String, bool)]) -> PrdSurfaceCoverage {
    let mut items = Vec::with_capacity(PRD_SURFACES.len());
    for surface in PRD_SURFACES {
        items.push(decide_one(surface, steps));
    }
    let count = |status: SurfaceStatus| items.iter().filter(|item| item.status == status).count();
    PrdSurfaceCoverage {
        total: items.len(),
        verified: count(SurfaceStatus::Verified),
        gap: count(SurfaceStatus::Gap),
        unobservable: count(SurfaceStatus::Unobservable),
        items,
    }
}

fn decide_one(surface: &PrdSurface, steps: &[(String, bool)]) -> PrdSurfaceVerdict {
    let verdict =
        |status: SurfaceStatus, evidence: String, reason: Option<String>| PrdSurfaceVerdict {
            id: surface.id.to_string(),
            status,
            evidence,
            reason,
        };
    match surface.decider {
        Decider::Steps(required) => {
            let mut missing: Vec<&str> = Vec::new();
            let mut failed: Vec<&str> = Vec::new();
            for name in required {
                match steps.iter().find(|(step, _)| step == name) {
                    None => missing.push(name),
                    Some((_, false)) => failed.push(name),
                    Some((_, true)) => {}
                }
            }
            if !missing.is_empty() {
                return verdict(
                    SurfaceStatus::Gap,
                    format!("battery step(s): {}", required.join(", ")),
                    Some(format!(
                        "the battery pass recorded no step `{}`, so the harness did not observe \
                         this surface",
                        missing.join("`, `")
                    )),
                );
            }
            if !failed.is_empty() {
                return verdict(
                    SurfaceStatus::Gap,
                    format!("battery step(s): {}", required.join(", ")),
                    Some(format!(
                        "the battery ran step(s) `{}` and they did not observe this surface \
                         (`ok = false`; the step's own reason is in the round's evidence)",
                        failed.join("`, `")
                    )),
                );
            }
            verdict(
                SurfaceStatus::Verified,
                format!("battery step(s): {}", required.join(", ")),
                None,
            )
        }
        Decider::Invariant(mechanism) => verdict(
            SurfaceStatus::Verified,
            format!("frozen invariant: {mechanism}"),
            None,
        ),
        Decider::Unobservable(reason) => verdict(
            SurfaceStatus::Unobservable,
            "not decidable from the harness's own evidence".to_string(),
            Some(reason.to_string()),
        ),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn all_ok() -> Vec<(String, bool)> {
        let mut steps: Vec<(String, bool)> = vec![
            ("editor_errors_baseline".to_string(), true),
            ("play_scene_ready".to_string(), true),
        ];
        for (step, _, _) in crate::adapter::bevy::round::E3_STEPS {
            steps.push(((*step).to_string(), true));
        }
        steps
    }

    #[test]
    fn every_step_a_decider_names_is_a_battery_step() {
        for surface in PRD_SURFACES {
            let Decider::Steps(required) = surface.decider else {
                continue;
            };
            for name in required {
                assert!(
                    crate::adapter::bevy::round::E3_STEPS
                        .iter()
                        .any(|(step, _, _)| step == name)
                        || *name == crate::adapter::bevy::round::BUILT_STEP_ID
                        || *name == crate::adapter::bevy::round::READY_STEP_ID,
                    "surface `{}` names a battery step `{name}` the battery does not run",
                    surface.id
                );
            }
        }
    }

    #[test]
    fn a_full_battery_pass_verifies_every_decidable_surface() {
        let coverage = decide(&all_ok());
        assert_eq!(coverage.total, PRD_SURFACES.len());
        for item in &coverage.items {
            let expected = match PRD_SURFACES
                .iter()
                .find(|surface| surface.id == item.id)
                .map(|surface| surface.decider)
            {
                Some(Decider::Unobservable(_)) => SurfaceStatus::Unobservable,
                _ => SurfaceStatus::Verified,
            };
            assert_eq!(item.status, expected, "{}: {}", item.id, item.evidence);
        }
        assert!(coverage.verified + coverage.gap + coverage.unobservable == coverage.total);
    }

    #[test]
    fn an_unobserved_step_is_a_gap_named_by_id_and_never_a_pass() {
        let mut steps = all_ok();
        steps
            .iter_mut()
            .find(|(step, _)| step == "e3_process_liveness")
            .unwrap()
            .1 = false;
        let coverage = decide(&steps);
        for id in ["Q-startup", "B2.1"] {
            let item = coverage.items.iter().find(|item| item.id == id).unwrap();
            assert_eq!(item.status, SurfaceStatus::Gap, "{id}");
            assert!(
                item.reason
                    .as_deref()
                    .unwrap_or_default()
                    .contains("e3_process_liveness"),
                "{id}: {:?}",
                item.reason
            );
        }
        // Everything else is untouched: one step cannot move another surface.
        assert!(coverage
            .items
            .iter()
            .find(|item| item.id == "P4")
            .unwrap()
            .is_verified());
    }

    #[test]
    fn a_step_the_pass_never_recorded_is_a_gap_that_names_it() {
        let coverage = decide(&[]);
        assert_eq!(
            coverage.unobservable, 4,
            "the four named non-decidable surfaces"
        );
        assert_eq!(coverage.verified, 3, "only the frozen invariants hold");
        let item = coverage.items.iter().find(|item| item.id == "P2").unwrap();
        assert_eq!(item.status, SurfaceStatus::Gap);
        assert!(item
            .reason
            .as_deref()
            .unwrap()
            .contains("no step `e3_coin_counter`"));
    }

    #[test]
    fn the_denominator_is_the_registry_and_never_the_callers_counts() {
        let coverage = decide(&all_ok());
        assert_eq!(
            coverage
                .items
                .iter()
                .map(|item| item.id.as_str())
                .collect::<Vec<_>>(),
            EXPECTED_IDS.to_vec()
        );
    }
}
