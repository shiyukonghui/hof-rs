//! The E3 observation battery: the five behaviours that must be seen **inside
//! the game process** (`REQUIREMENTS.md` §6-E3, §9; `PRD.md` §2, §5).
//!
//! ```text
//! ① injected input changes the player's position
//! ② the coin counter goes 0 -> N
//! ③ the win flag goes false -> true
//! ④ a jump has BOTH rising and falling steps (a monotone fall is not a jump)
//! ⑤ `Grounded` reads true before the take-off
//! ```
//!
//! Three rules are structural here, not conventions:
//!
//! * **Every observation keeps its raw calls.**  A verdict is a [`Reading`] or a
//!   [`FrameSample`] plus the [`CallEvidence`] of the BRP exchanges that produced
//!   it, so "the model observed X" is checkable against "the wire carried Y".
//! * **"Not observed" is never "observed false".**  A read that failed makes its
//!   observation fail *with a reason* and leaves the value absent; a read that
//!   succeeded and returned `false` is a good observation that the criterion's
//!   expectation was not met.  E6's honesty requirement is only enforceable if
//!   those are different values.
//! * **Motion is judged on the game's own frames.**  Every reading carries the
//!   game's frame-counter value (D297 (b)), so an arc is a sequence of
//!   `(frame, y)` pairs from the game and a monotone fall is rejected on the
//!   game's terms.
//!
//! The battery never injects an edge it does not clear: the input surface is
//! **level-triggered** (PRD C3), and every phase ends by writing `0`/`false`
//! back, so a later phase cannot be explained by an earlier phase's intent.

use serde::Serialize;
use serde_json::Value;

use crate::adapter::mcp::evidence::CallEvidence;
use crate::adapter::mcp::server::BevyMcpServer;
use crate::adapter::{Intent, Reading, SemanticKind};

/// How many frames to let the game settle before a baseline read.
pub const SETTLE_FRAMES: u32 = 4;
/// How many frames of the injected input the movement check waits for.
pub const MOVE_FRAMES: u32 = 12;
/// Round-1 write-path batch: how many frames the leftward injection is held for.
pub const LEFT_FRAMES: u32 = 12;
/// Round-1 write-path batch: how many frames a released input is watched for
/// residual motion.
pub const RELEASE_FRAMES: u32 = 8;
/// How many frames to wait after a possible coin/goal contact.
pub const CONTACT_SETTLE_FRAMES: u32 = 8;
/// How many contact rounds the coin/win phase runs.
pub const CONTACT_ROUNDS: usize = 4;
/// How long a jump's press is held, in frames.
pub const JUMP_HOLD_FRAMES: u32 = 2;
/// The most polls one arc is sampled for.  The loop normally stops earlier (see
/// `phase_jump`): this is the cap, not the length.
pub const ARC_POLLS: u32 = 32;
/// The fewest samples an arc may be declared complete after.
pub const ARC_MIN_SAMPLES: usize = 6;
/// The smallest displacement that counts as motion, in the game's own units.
pub const MOTION_EPSILON: f64 = 1e-6;

/// What one phase of the battery is allowed to do.
///
/// It exists so the same battery can be handed a real game or an in-process
/// fake, and so the phases are testable without an engine.
pub trait BatteryDriver {
    /// One semantic read of one surface.
    fn read(&mut self, kind: SemanticKind) -> anyhow::Result<Reading>;
    /// Hold an intent (level-triggered; the game clears the edge).
    fn inject(
        &mut self,
        intent: &Intent,
        level: bool,
    ) -> anyhow::Result<crate::adapter::InjectionReport>;
    /// Wait for `n` frames **of the game**.
    fn wait_frames(&mut self, n: u32) -> anyhow::Result<crate::adapter::FrameMark>;
    /// The raw calls made since the last time this was called.
    fn take_evidence(&mut self) -> Vec<CallEvidence>;
}

/// One `(game frame, value)` sample of a semantic surface.
#[derive(Clone, Debug, PartialEq, Serialize)]
pub struct FrameSample {
    /// The game's own frame, as the reading reported it.
    pub frame: u64,
    pub value: Value,
}

/// A vertical arc, reconstructed from the game's own frame numbers.
///
/// `rising` and `falling` count the **strictly** rising/falling steps between
/// consecutive samples.  A jump needs both, and the peak must be above the
/// take-off height.  A monotone fall (`rising == 0`) is explicitly not a jump:
/// that is the reading which was red in the Godot-era criterion, and it must
/// stay red.
#[derive(Clone, Debug, PartialEq, Serialize)]
pub struct JumpArc {
    pub peak: f64,
    pub first: f64,
    pub rising: usize,
    pub falling: usize,
    pub samples: Vec<FrameSample>,
}

impl JumpArc {
    /// Classify an arc from `(frame, y)` samples.
    pub fn classify(samples: &[FrameSample]) -> (Option<Self>, Option<String>) {
        if samples.len() < 3 {
            return (
                None,
                Some(format!(
                    "the arc has {} sample(s); at least 3 are needed to see a direction change",
                    samples.len()
                )),
            );
        }
        let mut ys = Vec::with_capacity(samples.len());
        for sample in samples {
            let Some(y) = sample.value.as_f64() else {
                return (
                    None,
                    Some(format!(
                        "a sample at frame {} is not a number: {}",
                        sample.frame, sample.value
                    )),
                );
            };
            ys.push(y);
        }
        let first = ys[0];
        let mut peak = ys[0];
        let mut rising = 0usize;
        let mut falling = 0usize;
        for window in ys.windows(2) {
            if window[1] > window[0] {
                rising += 1;
            } else if window[1] < window[0] {
                falling += 1;
            }
            if window[1] > peak {
                peak = window[1];
            }
        }
        (
            Some(JumpArc {
                peak,
                first,
                rising,
                falling,
                samples: samples.to_vec(),
            }),
            None,
        )
    }

    /// The criterion ④ verdict, with the reason when it fails.
    pub fn verdict(&self) -> Result<(), String> {
        if self.rising == 0 {
            return Err(format!(
                "the arc never rises (rise=0, fall={}): a monotone fall is not a jump",
                self.falling
            ));
        }
        if self.falling == 0 {
            return Err(format!(
                "the arc never falls (rise={}): the jump never came down",
                self.rising
            ));
        }
        if self.peak <= self.first {
            return Err(format!(
                "the peak ({}) is not above the take-off height ({})",
                self.peak, self.first
            ));
        }
        Ok(())
    }
}

/// One criterion's outcome: whether it was **observed at all**, what it read,
/// and — when it was not observed, or was observed and did not hold — why.
#[derive(Clone, Debug, PartialEq, Serialize)]
pub struct Observation {
    /// `true` only when the criterion's expectation was met by observations that
    /// actually happened.
    pub observed: bool,
    /// `Some(reason)` when the criterion does not hold.  The reason says which of
    /// the two cases it is ("was not observed, because …" vs "read false").
    pub failure: Option<String>,
    pub readings: Vec<Reading>,
    pub arc: Option<JumpArc>,
    /// The raw BRP calls that produced this observation, in order.
    pub calls: Vec<CallEvidence>,
}

/// The prefix every "this was never observed" reason carries.  It is a constant
/// because [`Observation::was_measured`] reads it: an observation whose failure
/// begins here was **not measured**, even if some of its reads happened to
/// succeed before the surface vanished (B2-7).
pub const NOT_OBSERVED_PREFIX: &str = "not observed";

impl Observation {
    pub fn not_observed(reason: impl Into<String>, calls: Vec<CallEvidence>) -> Self {
        Self {
            observed: false,
            failure: Some(format!("{}: {}", NOT_OBSERVED_PREFIX, reason.into())),
            readings: Vec::new(),
            arc: None,
            calls,
        }
    }

    /// `true` when the reads happened (possibly reading the expectation as false)
    /// as opposed to never happening.
    ///
    /// A failed read inside a phase turns the whole observation into "not
    /// observed" (B2-7): the surface vanished, so the criterion was not
    /// measured, and reporting that as a measured failure ("the counter never
    /// rose above 0") would be the false-green class this harness exists to
    /// prevent.  The failure's own prefix is therefore authoritative.
    pub fn was_measured(&self) -> bool {
        if self
            .failure
            .as_deref()
            .is_some_and(|failure| failure.starts_with(NOT_OBSERVED_PREFIX))
        {
            return false;
        }
        !self.readings.is_empty() || self.arc.is_some()
    }

    /// Did a read fail, and is that why this observation is not met?
    pub fn was_unobservable(&self) -> bool {
        !self.was_measured()
    }
}

/// The nine observations.
///
/// The first five are the original E3 criteria; the last four are the **missing
/// battery steps** round 1's Tester recorded as gaps (`P1-left`, `P1-release`,
/// `P3-position`, `P5-gate`), so a reported gap now names a behaviour the
/// battery really did not measure rather than one it never asked about.
#[derive(Clone, Debug, PartialEq, Serialize)]
pub struct E3Observations {
    pub movement: Observation,
    pub coins: Observation,
    pub win: Observation,
    pub jump: Observation,
    pub grounded: Observation,
    /// P1-left: injecting `move_dir = -1` moves `x` in the **negative**
    /// direction.  One direction is not a movement contract.
    pub movement_left: Observation,
    /// P1-release: after `move_dir = 0`, `x` stops changing — the release rule
    /// the Developer's own definition of done states ("writing `0` stops it (no
    /// residual velocity)").
    pub movement_release: Observation,
    /// P3-position: a `PlayerTransform` sample taken at the frame the win flag
    /// turned true, so a win is located in the world and not only in a boolean.
    pub win_position: Observation,
    /// P5-gate: a `Grounded` **payload** that stands on its own — the semantic
    /// field, read at rest, as its own observation rather than as the jump's
    /// supporting basis.
    pub grounded_payload: Observation,
    /// `None` when the battery ran; `Some(reason)` when it could not run at all
    /// (in which case every observation is "not observed").
    pub aborted: Option<String>,
}

/// Every named observation, in the order the round records them.
///
/// It is one list so `gaps`, `passed`, `all_calls`, `readings_of`,
/// `summary_line` and `round::battery_records` cannot drift apart when a
/// criterion is added: a criterion that is missing from this list is missing
/// from every one of them, which is the failure the round-1 gaps exposed.
pub const NAMED_OBSERVATIONS: &[(&str, &str)] = &[
    ("movement", "e3_movement"),
    ("coins", "e3_coin_counter"),
    ("win", "e3_win_flag"),
    ("jump", "e3_jump_arc"),
    ("grounded", "e3_grounded"),
    ("movement_left", "e3_movement_left"),
    ("movement_release", "e3_movement_release"),
    ("win_position", "e3_win_position"),
    ("grounded_payload", "e3_grounded_payload"),
];

impl E3Observations {
    /// The observation behind a name from [`NAMED_OBSERVATIONS`].
    pub fn named(&self, name: &str) -> Option<&Observation> {
        Some(match name {
            "movement" => &self.movement,
            "coins" => &self.coins,
            "win" => &self.win,
            "jump" => &self.jump,
            "grounded" => &self.grounded,
            "movement_left" => &self.movement_left,
            "movement_release" => &self.movement_release,
            "win_position" => &self.win_position,
            "grounded_payload" => &self.grounded_payload,
            _ => return None,
        })
    }

    /// Every observation, in [`NAMED_OBSERVATIONS`] order.
    pub fn all_observations(&self) -> Vec<&Observation> {
        NAMED_OBSERVATIONS
            .iter()
            .filter_map(|(name, _)| self.named(name))
            .collect()
    }

    /// Every observation that was not made, with the reason.  This is what a
    /// Tester must consume instead of inventing proof.
    pub fn gaps(&self) -> Vec<(&'static str, String)> {
        let mut gaps = Vec::new();
        if let Some(reason) = &self.aborted {
            for (name, _) in NAMED_OBSERVATIONS {
                gaps.push((
                    *name,
                    format!("not observed: the battery aborted: {reason}"),
                ));
            }
            return gaps;
        }
        for (name, _) in NAMED_OBSERVATIONS {
            let Some(observation) = self.named(name) else {
                continue;
            };
            if !observation.observed {
                gaps.push((
                    *name,
                    observation
                        .failure
                        .clone()
                        .unwrap_or_else(|| "not observed".to_string()),
                ));
            }
        }
        gaps
    }

    /// All nine criteria met.
    pub fn passed(&self) -> bool {
        self.aborted.is_none()
            && self
                .all_observations()
                .iter()
                .all(|observation| observation.observed)
    }

    /// The evidence of every observation, flattened in the frozen order.
    pub fn all_calls(&self) -> Vec<CallEvidence> {
        let mut calls: Vec<CallEvidence> = Vec::new();
        // One raw call is one file in `calls/`, whatever it proves.  The
        // pre-injection baseline window is carried by **two** observations (the
        // coin counter's "it started at 0" and the win flag's "it started
        // false"), so the same call can be listed twice; the evidence directory
        // is keyed by sequence number, and a duplicate would mean two files for
        // one exchange.
        let mut seen: std::collections::BTreeSet<u64> = std::collections::BTreeSet::new();
        for observation in self.all_observations() {
            for call in &observation.calls {
                if seen.insert(call.seq) {
                    calls.push(call.clone());
                }
            }
        }
        calls.sort_by_key(|call| call.seq);
        calls
    }

    /// The readings of one surface, in observation order.
    pub fn readings_of(&self, kind: SemanticKind) -> Vec<&Reading> {
        let mut readings = Vec::new();
        for observation in self.all_observations() {
            readings.extend(
                observation
                    .readings
                    .iter()
                    .filter(|reading| reading.kind == kind),
            );
        }
        readings
    }

    /// A one-line summary, for the round's `readings/` file and the report.
    pub fn summary_line(&self) -> String {
        if let Some(reason) = &self.aborted {
            return format!("E3 ABORTED: {reason}");
        }
        let marks: Vec<String> = NAMED_OBSERVATIONS
            .iter()
            .map(|(name, _)| {
                let mark = self
                    .named(name)
                    .map(|observation| if observation.observed { "ok" } else { "RED" })
                    .unwrap_or("MISSING");
                format!("{name}={mark}")
            })
            .collect();
        format!("E3 {}", marks.join(" "))
    }
}

/// The battery as a value: the driver, the observations collected so far, and
/// the evidence window.
pub struct BatteryRun<'a> {
    driver: &'a mut dyn BatteryDriver,
    pub observations: E3Observations,
    /// The readings taken **before any input was injected**.  PRD P2 requires
    /// the coin count to *start* at 0 and P3 requires the win flag to start
    /// `false`, so the baseline has to be observed before the movement phase can
    /// collect anything; reading it afterwards would be reading a different
    /// question.
    baseline_coins: Option<i64>,
    baseline_won: Option<bool>,
    baseline_grounded: Option<bool>,
    baseline_transform: Option<Reading>,
    /// The baseline readings themselves, and the raw calls that produced them.
    ///
    /// They are carried into the coin/win observations so that "the counter
    /// started at 0" and "the flag started false" are visible **in the
    /// observation that asserts them**, next to the call that read them — the
    /// criterion is computed from the pre-injection value, and evidence a reader
    /// cannot find is evidence a reader cannot check.
    baseline_coin_reading: Option<Reading>,
    baseline_win_reading: Option<Reading>,
    baseline_calls: Vec<CallEvidence>,
    /// P3-position: the `WinFlag` reading that first reported `true`.
    win_flag_reading: Option<Reading>,
    /// P3-position: the `PlayerTransform` read immediately after that frame.
    win_position_reading: Option<Reading>,
}

impl<'a> BatteryRun<'a> {
    pub fn new(driver: &'a mut dyn BatteryDriver) -> Self {
        Self {
            driver,
            observations: E3Observations {
                movement: Observation::not_observed("the battery has not run", Vec::new()),
                coins: Observation::not_observed("the battery has not run", Vec::new()),
                win: Observation::not_observed("the battery has not run", Vec::new()),
                jump: Observation::not_observed("the battery has not run", Vec::new()),
                grounded: Observation::not_observed("the battery has not run", Vec::new()),
                movement_left: Observation::not_observed("the battery has not run", Vec::new()),
                movement_release: Observation::not_observed("the battery has not run", Vec::new()),
                win_position: Observation::not_observed("the battery has not run", Vec::new()),
                grounded_payload: Observation::not_observed("the battery has not run", Vec::new()),
                aborted: None,
            },
            baseline_coins: None,
            baseline_won: None,
            baseline_grounded: None,
            baseline_transform: None,
            baseline_coin_reading: None,
            baseline_win_reading: None,
            baseline_calls: Vec::new(),
            win_flag_reading: None,
            win_position_reading: None,
        }
    }

    /// Run every phase.  A task-level failure from a read/inject/wait aborts
    /// the battery with the reason; it never panics and never invents a value.
    pub fn run(mut self) -> anyhow::Result<E3Observations> {
        if let Err(error) = self.run_inner() {
            // A task-level failure is not evidence about the game — the round
            // could not be observed at all — so it is recorded as an abort, not
            // as nine failed criteria.
            let reason = error.to_string();
            self.observations.aborted = Some(reason.clone());
            for (name, _) in NAMED_OBSERVATIONS {
                let call = self.driver.take_evidence();
                let observation = Observation::not_observed(reason.clone(), call);
                match *name {
                    "movement" => self.observations.movement = observation,
                    "coins" => self.observations.coins = observation,
                    "win" => self.observations.win = observation,
                    "jump" => self.observations.jump = observation,
                    "grounded" => self.observations.grounded = observation,
                    "movement_left" => self.observations.movement_left = observation,
                    "movement_release" => self.observations.movement_release = observation,
                    "win_position" => self.observations.win_position = observation,
                    "grounded_payload" => self.observations.grounded_payload = observation,
                    _ => {}
                }
            }
        }
        Ok(self.observations)
    }

    fn run_inner(&mut self) -> anyhow::Result<()> {
        self.phase_baselines()?;
        self.phase_movement()?;
        // The left/release checks run **after** the coin/win phase on purpose:
        // they move the player backwards, and the coin/win phase's reachability
        // depends on how far right the player can get.  Measuring a stop must not
        // cost the round its win.
        self.phase_coins_and_win()?;
        self.phase_movement_left_and_release()?;
        self.phase_jump()?;
        Ok(())
    }

    /// The window of raw calls an observation owns.
    fn begin(&mut self) -> Vec<CallEvidence> {
        let _ = self.driver.take_evidence();
        Vec::new()
    }

    /// The baselines, read **before any input is injected**: the ground state
    /// (criterion ⑤'s semantic basis), the coin count (P2 says it starts at 0),
    /// the win flag (P3 says it starts `false`) and the position P1 measures from.
    fn phase_baselines(&mut self) -> anyhow::Result<()> {
        let mut calls = self.begin();
        let mut grounded_readings = Vec::new();
        let mut grounded_flags = Vec::new();
        for _ in 0..2 {
            let reading = self.driver.read(SemanticKind::Grounded)?;
            if !reading.failed {
                grounded_flags.push(
                    reading
                        .value
                        .get("grounded")
                        .and_then(Value::as_bool)
                        .unwrap_or(false),
                );
                self.baseline_grounded = Some(
                    self.baseline_grounded.unwrap_or(true)
                        && grounded_flags[grounded_flags.len() - 1],
                );
            }
            grounded_readings.push(reading);
            let _ = self.driver.wait_frames(SETTLE_FRAMES)?;
        }
        let coins = self.driver.read(SemanticKind::CoinCounter)?;
        if !coins.failed {
            self.baseline_coins = coins.value.get("coins").and_then(Value::as_i64);
        }
        self.baseline_coin_reading = Some(coins);
        let won = self.driver.read(SemanticKind::WinFlag)?;
        if !won.failed {
            self.baseline_won = won.value.get("won").and_then(Value::as_bool);
        }
        self.baseline_win_reading = Some(won);
        let transform = self.driver.read(SemanticKind::PlayerTransform)?;
        if !transform.failed {
            self.baseline_transform = Some(transform.clone());
        }
        calls.extend(self.driver.take_evidence());
        // The baseline window's raw calls travel with the coin/win observations
        // (see `phase_coins_and_win`): the criterion is computed from these
        // readings, so they are part of that observation's evidence.
        self.baseline_calls = calls.clone();
        let failure = grounded_before_takeoff(&grounded_flags).err();
        self.observations.grounded = Observation {
            observed: failure.is_none(),
            failure,
            readings: grounded_readings,
            arc: None,
            calls,
        };
        let _ = transform;

        // P5-gate (round-1 write-path batch): the **payload** of a `Grounded`
        // read, at rest, as an observation of its own.  It used to exist only as
        // the jump criterion's supporting basis, so a reader could not tell
        // "the surface carries a `grounded` boolean the harness can read" from
        // "the jump happened to have a basis".  Its own evidence window is opened
        // here, so the calls behind it are exactly the calls that produced it.
        let mut payload_calls = self.begin();
        let payload = self.driver.read(SemanticKind::Grounded)?;
        payload_calls.extend(self.driver.take_evidence());
        let payload_failure = if payload.failed {
            Some(format!("{NOT_OBSERVED_PREFIX}: {}", read_gap(&payload)))
        } else if payload
            .value
            .get("grounded")
            .and_then(Value::as_bool)
            .is_none()
        {
            Some(format!(
                "the `Grounded` payload carried no boolean `grounded` field, so the surface does \
                 not stand on its own: {}",
                payload.value
            ))
        } else {
            None
        };
        self.observations.grounded_payload = Observation {
            observed: payload_failure.is_none(),
            failure: payload_failure,
            readings: vec![payload],
            arc: None,
            calls: payload_calls,
        };
        Ok(())
    }

    /// ① movement: baseline, hold a direction, read again.
    fn phase_movement(&mut self) -> anyhow::Result<()> {
        let mut calls = self.begin();
        // The baseline was read before any input was injected; re-reading it here
        // would be measuring a game the previous phase had already moved.
        let before = match self.baseline_transform.clone() {
            Some(reading) => reading,
            None => self.driver.read(SemanticKind::PlayerTransform)?,
        };
        let _ = self.driver.inject(&Intent::Move { dir: 1 }, true)?;
        let _ = self.driver.wait_frames(MOVE_FRAMES)?;
        let after = self.driver.read(SemanticKind::PlayerTransform)?;
        // Clear the level: the next phase must not be moved by this one's intent.
        let _ = self.driver.inject(&Intent::Move { dir: 0 }, true)?;
        let _ = self.driver.wait_frames(SETTLE_FRAMES)?;
        calls.extend(self.driver.take_evidence());
        let failure = movement_changed(&before, &after).err();
        self.observations.movement = Observation {
            observed: failure.is_none(),
            failure,
            readings: vec![before, after],
            arc: None,
            calls,
        };
        Ok(())
    }

    /// P1-left and P1-release (round-1 write-path batch): the two movement facts
    /// one direction cannot prove.
    ///
    /// Round 1's Tester recorded both as gaps (`P1-left`, `P1-release`) because
    /// the battery only ever injected `move_dir = 1` and never checked that
    /// writing `0` stops the player — while the Developer's own definition of
    /// done promises exactly that ("writing `0` stops it (no residual
    /// velocity)").  A one-directional movement check can be satisfied by a game
    /// that only ever moves right and never stops; these two steps cannot.
    fn phase_movement_left_and_release(&mut self) -> anyhow::Result<()> {
        // ---- P1-left: the negative direction really moves the player ----
        let mut calls = self.begin();
        let before = self.driver.read(SemanticKind::PlayerTransform)?;
        let _ = self.driver.inject(&Intent::Move { dir: -1 }, true)?;
        let _ = self.driver.wait_frames(LEFT_FRAMES)?;
        let after = self.driver.read(SemanticKind::PlayerTransform)?;
        // Clear the level again: the release check below must see a game that
        // was told to stop, not one still coasting on this intent.
        let _ = self.driver.inject(&Intent::Move { dir: 0 }, true)?;
        let _ = self.driver.wait_frames(SETTLE_FRAMES)?;
        calls.extend(self.driver.take_evidence());
        let failure = leftward_movement(&before, &after).err();
        self.observations.movement_left = Observation {
            observed: failure.is_none(),
            failure,
            readings: vec![before, after],
            arc: None,
            calls,
        };

        // ---- P1-release: writing `0` stops it ----
        let mut calls = self.begin();
        let settled = self.driver.read(SemanticKind::PlayerTransform)?;
        let _ = self.driver.wait_frames(RELEASE_FRAMES)?;
        let later = self.driver.read(SemanticKind::PlayerTransform)?;
        calls.extend(self.driver.take_evidence());
        let failure = released_stops(&settled, &later).err();
        self.observations.movement_release = Observation {
            observed: failure.is_none(),
            failure,
            readings: vec![settled, later],
            arc: None,
            calls,
        };
        Ok(())
    }

    /// ② coins and ③ the win flag: hold right and watch both.
    fn phase_coins_and_win(&mut self) -> anyhow::Result<()> {
        // The evidence window opens here; the baseline window's records are
        // prepended below, so a reader sees the pre-injection reading first.
        let _ = self.begin();
        let mut readings = Vec::new();
        let mut counts = Vec::new();
        let mut flags = Vec::new();
        // A failed read in this phase means the surface vanished while the
        // criterion was being measured, so the observation becomes "not
        // observed" rather than a measured failure (B2-7).  The two are
        // different facts and the gate must be able to tell them apart.
        let mut coin_gap: Option<String> = None;
        let mut win_gap: Option<String> = None;

        // The baseline readings come from before any input was injected.
        let base = self.driver.read(SemanticKind::CoinCounter)?;
        if base.failed {
            coin_gap.get_or_insert_with(|| read_gap(&base));
        } else if let Some(baseline) = self.baseline_coins {
            counts.push(baseline);
        } else {
            counts.push(base.value.get("coins").and_then(Value::as_i64).unwrap_or(0));
        }
        readings.push(base);
        let win_base = self.driver.read(SemanticKind::WinFlag)?;
        if win_base.failed {
            win_gap.get_or_insert_with(|| read_gap(&win_base));
        } else if let Some(baseline) = self.baseline_won {
            flags.push(baseline);
        } else {
            flags.push(
                win_base
                    .value
                    .get("won")
                    .and_then(Value::as_bool)
                    .unwrap_or(false),
            );
        }
        readings.push(win_base);

        let _ = self.driver.inject(&Intent::Move { dir: 1 }, true)?;
        for _ in 0..CONTACT_ROUNDS {
            let _ = self.driver.wait_frames(CONTACT_SETTLE_FRAMES)?;
            let coins = self.driver.read(SemanticKind::CoinCounter)?;
            if coins.failed {
                coin_gap.get_or_insert_with(|| read_gap(&coins));
            } else {
                counts.push(
                    coins
                        .value
                        .get("coins")
                        .and_then(Value::as_i64)
                        .unwrap_or(0),
                );
            }
            readings.push(coins);
            let flag = self.driver.read(SemanticKind::WinFlag)?;
            if flag.failed {
                win_gap.get_or_insert_with(|| read_gap(&flag));
            } else {
                let won = flag
                    .value
                    .get("won")
                    .and_then(Value::as_bool)
                    .unwrap_or(false);
                flags.push(won);
                // P3-position (round-1 write-path batch): the frame the win flag
                // first read `true` is located in the world immediately, before
                // the next settle window can move the player further.  The
                // transform read is a *second call* — a BRP batch is not
                // frame-atomic (SPIKE-2 C4), so "at the win frame" can honestly
                // mean "the first transform read at or after that frame", and the
                // criterion says exactly that.
                if won && self.win_flag_reading.is_none() {
                    self.win_flag_reading = Some(flag.clone());
                    let at_win = self.driver.read(SemanticKind::PlayerTransform)?;
                    self.win_position_reading = Some(at_win.clone());
                    readings.push(at_win);
                }
            }
            readings.push(flag);
        }
        let _ = self.driver.inject(&Intent::Move { dir: 0 }, true)?;
        let _ = self.driver.wait_frames(SETTLE_FRAMES)?;
        let phase_calls = self.driver.take_evidence();
        // The pre-injection baseline comes first: a reader of
        // `readings/<surface>.json` sees "0" / "false" before the readings that
        // followed the injection, which is exactly what P2/P3 claim.
        let mut all_readings: Vec<Reading> = Vec::new();
        if let Some(reading) = self.baseline_coin_reading.clone() {
            all_readings.push(reading);
        }
        if let Some(reading) = self.baseline_win_reading.clone() {
            all_readings.push(reading);
        }
        all_readings.extend(readings);
        let mut calls = self.baseline_calls.clone();
        calls.extend(phase_calls);

        let coin_failure = coin_gap
            .map(|reason| format!("{NOT_OBSERVED_PREFIX}: {reason}"))
            .or_else(|| coins_increased(&counts).err());
        let win_failure = win_gap
            .clone()
            .map(|reason| format!("{NOT_OBSERVED_PREFIX}: {reason}"))
            .or_else(|| win_became_true(&flags).err());
        // The same phase reads both surfaces, so both observations keep the same
        // raw calls; the readings are split by surface so a reader can see which
        // call produced which number.
        self.observations.coins = Observation {
            observed: coin_failure.is_none(),
            failure: coin_failure,
            readings: all_readings
                .iter()
                .filter(|reading| reading.kind == SemanticKind::CoinCounter)
                .cloned()
                .collect(),
            arc: None,
            calls: calls.clone(),
        };
        // P3-position: the win, located in the world.  It shares the phase's own
        // evidence window, because the transform read that answers it happened
        // inside that window.
        let win_position_calls = calls.clone();
        self.observations.win = Observation {
            observed: win_failure.is_none(),
            failure: win_failure,
            readings: all_readings
                .into_iter()
                .filter(|reading| reading.kind == SemanticKind::WinFlag)
                .collect(),
            arc: None,
            calls,
        };

        // P3-position: the win, located in the world.
        let (win_position_readings, win_position_failure) =
            match (&self.win_flag_reading, &self.win_position_reading) {
                (Some(flag), Some(position)) => {
                    let failure = win_position_at(flag.frame, position).err();
                    (vec![flag.clone(), position.clone()], failure)
                }
                (Some(flag), None) => (
                    vec![flag.clone()],
                    Some(format!(
                        "not observed: the win flag turned true at game frame {} but no transform \
                         sample followed it",
                        flag.frame
                    )),
                ),
                (None, _) => {
                    let failure = match win_gap {
                        Some(reason) => format!(
                            "{NOT_OBSERVED_PREFIX}: the win frame could not be established: \
                             {reason}"
                        ),
                        None => "not observed: the win flag never turned true, so there is no win \
                                 frame to sample the position at"
                            .to_string(),
                    };
                    (Vec::new(), Some(failure))
                }
            };
        self.observations.win_position = Observation {
            observed: win_position_failure.is_none(),
            failure: win_position_failure,
            readings: win_position_readings,
            arc: None,
            calls: win_position_calls,
        };
        Ok(())
    }

    /// ④ the jump arc, and the ground state immediately before take-off.
    fn phase_jump(&mut self) -> anyhow::Result<()> {
        let mut calls = self.begin();
        let mut readings = Vec::new();
        let pre = self.driver.read(SemanticKind::Grounded)?;
        let grounded_at_takeoff = !pre.failed
            && pre
                .value
                .get("grounded")
                .and_then(Value::as_bool)
                .unwrap_or(false);
        readings.push(pre);
        // ⑤ is also satisfied by the baseline (which was read before the take-off)
        // even when the game has left the ground by the time this phase runs.
        // That is the stronger evidence, so it decides: the phase's own reading
        // is kept as evidence but does not overturn a `true` baseline (B2-8 —
        // before this, the branch existed as a comment and the phase reading
        // always won).
        let grounded_evidence = grounded_at_takeoff || self.baseline_grounded == Some(true);
        let takeoff = self.driver.read(SemanticKind::PlayerTransform)?;
        let start_frame = takeoff.frame;
        readings.push(takeoff.clone());
        let _ = self.driver.inject(&Intent::Jump { press: true }, true)?;
        let _ = self.driver.wait_frames(JUMP_HOLD_FRAMES)?;
        let _ = self.driver.inject(&Intent::Jump { press: false }, true)?;
        let mut sampler = ArcSampler::new();
        sampler.push(&takeoff);
        // ---- the arc -------------------------------------------------------
        //
        // Every BRP call costs about one **game frame** — the server answers from
        // the app's update loop, and the round's own evidence measured 16.8 ms
        // per call, i.e. 1.0 frame at 60 FPS — so a sample of two calls is
        // already ~2 frames apart.  An extra `wait_frames(1)` (which itself costs
        // one or two calls) would triple that, and the earlier version's evidence
        // showed exactly that: consecutive samples 5 frames apart, a 30-frame
        // jump sampled around its peak, and a pass on a single rising step.  So
        // the arc is sampled as fast as the transport allows, and the loop stops
        // when the arc has **completed** — the player rose and came back to the
        // take-off height — so a longer jump is followed rather than truncated.
        //
        // The frame in every sample is still the game's own counter, which is
        // what makes the arc a sequence of game frames rather than of polls.
        let takeoff_height = takeoff.value.get("y").and_then(Value::as_f64);
        let mut rose = false;
        for _ in 0..ARC_POLLS {
            let sample = self.driver.read(SemanticKind::PlayerTransform)?;
            let height = sample.value.get("y").and_then(Value::as_f64);
            let complete = match (takeoff_height, height) {
                (Some(first), Some(height)) => {
                    if height > first + MOTION_EPSILON {
                        rose = true;
                    }
                    rose && height <= first + MOTION_EPSILON
                }
                _ => false,
            };
            sampler.push(&sample);
            readings.push(sample);
            if complete && readings.len() >= ARC_MIN_SAMPLES {
                break;
            }
        }
        calls.extend(self.driver.take_evidence());

        let (arc, classify_failure) = JumpArc::classify(&sampler.samples);
        let failure = classify_failure.or_else(|| arc.as_ref().and_then(|arc| arc.verdict().err()));
        // Criterion ⑤ is about the frame *before* take-off.  When neither the
        // baseline nor the phase read saw the ground, the jump has no semantic
        // basis and the failure says so.
        if !grounded_evidence {
            let note = format!(
                "`Grounded` read false immediately before take-off (game frame {start_frame}), so \
                 the jump has no semantic basis"
            );
            let existing = self.observations.grounded.failure.clone();
            self.observations.grounded.observed = false;
            self.observations.grounded.failure = Some(match existing {
                Some(existing) => format!("{existing}; {note}"),
                None => note,
            });
        }
        self.observations.jump = Observation {
            observed: failure.is_none(),
            failure,
            readings,
            arc,
            calls,
        };
        Ok(())
    }
}

/// The frame counter of the game vs. the game frame.
///
/// The arc is sampled **per game frame**, not per wall-clock interval, because
/// criterion ④ is a statement about the game's frame advance (D297 (b)).
pub struct ArcSampler {
    /// The frame the previous sample was taken at; `None` before the first.
    pub last_frame: Option<u64>,
    pub samples: Vec<FrameSample>,
}

impl ArcSampler {
    pub fn new() -> Self {
        Self {
            last_frame: None,
            samples: Vec::new(),
        }
    }

    /// Record one reading.  Returns `true` when it produced a new sample (i.e.
    /// the game had advanced since the previous one).
    pub fn push(&mut self, reading: &Reading) -> bool {
        if reading.failed {
            return false;
        }
        if self.last_frame == Some(reading.frame) {
            return false;
        }
        let Some(y) = reading.value.get("y").cloned() else {
            return false;
        };
        self.last_frame = Some(reading.frame);
        self.samples.push(FrameSample {
            frame: reading.frame,
            value: y,
        });
        true
    }
}

impl Default for ArcSampler {
    fn default() -> Self {
        Self::new()
    }
}

/// The movement criterion: the position after holding a direction differs from
/// the position before it by more than [`MOTION_EPSILON`].
///
/// **Not observed** (a failed read) is reported as such; a successful read whose
/// `x` did not move is a measured failure.
pub fn movement_changed(before: &Reading, after: &Reading) -> Result<f64, String> {
    if before.failed {
        return Err(format!(
            "not observed: the baseline position could not be read ({})",
            before
                .reason
                .clone()
                .unwrap_or_else(|| "no reason given".to_string())
        ));
    }
    if after.failed {
        return Err(format!(
            "not observed: the position after the injected input could not be read ({})",
            after
                .reason
                .clone()
                .unwrap_or_else(|| "no reason given".to_string())
        ));
    }
    let (Some(x0), Some(x1)) = (
        before.value.get("x").and_then(Value::as_f64),
        after.value.get("x").and_then(Value::as_f64),
    ) else {
        return Err("the position reading did not carry an `x` coordinate".to_string());
    };
    let delta = x1 - x0;
    if !delta.is_finite() {
        return Err(format!("the position delta is not finite: {delta}"));
    }
    if delta.abs() <= MOTION_EPSILON {
        return Err(format!(
            "injecting the input changed `x` by {delta} (from {x0} to {x1}), which is not motion"
        ));
    }
    Ok(delta)
}

/// P1-left (round-1 write-path batch): injecting `move_dir = -1` must move `x`
/// in the **negative** direction.
///
/// It is the mirror of [`movement_changed`] and it is deliberately not "the
/// position changed": a game that only ever moves right — or that treats `-1`
/// as `+1` — would pass a change check and fail this one.
pub fn leftward_movement(before: &Reading, after: &Reading) -> Result<f64, String> {
    if before.failed {
        return Err(format!(
            "not observed: the position before the leftward injection could not be read ({})",
            before
                .reason
                .clone()
                .unwrap_or_else(|| "no reason given".to_string())
        ));
    }
    if after.failed {
        return Err(format!(
            "not observed: the position after the leftward injection could not be read ({})",
            after
                .reason
                .clone()
                .unwrap_or_else(|| "no reason given".to_string())
        ));
    }
    let (Some(x0), Some(x1)) = (
        before.value.get("x").and_then(Value::as_f64),
        after.value.get("x").and_then(Value::as_f64),
    ) else {
        return Err("the position reading did not carry an `x` coordinate".to_string());
    };
    let delta = x1 - x0;
    if !delta.is_finite() {
        return Err(format!("the position delta is not finite: {delta}"));
    }
    if delta >= -MOTION_EPSILON {
        return Err(format!(
            "injecting `move_dir = -1` changed `x` by {delta} (from {x0} to {x1}), which is not \
             leftward motion"
        ));
    }
    Ok(delta)
}

/// P1-release (round-1 write-path batch): after `move_dir = 0`, `x` must stop
/// changing — the Developer's own definition of done promises "writing `0` stops
/// it (no residual velocity)".
///
/// The window is [`RELEASE_FRAMES`] of the game's own frames, sampled at both
/// ends, so a game that coasts can be told apart from one that stops.
pub fn released_stops(settled: &Reading, later: &Reading) -> Result<(), String> {
    if settled.failed {
        return Err(format!(
            "not observed: the position after the release could not be read ({})",
            settled
                .reason
                .clone()
                .unwrap_or_else(|| "no reason given".to_string())
        ));
    }
    if later.failed {
        return Err(format!(
            "not observed: the position later in the release window could not be read ({})",
            later
                .reason
                .clone()
                .unwrap_or_else(|| "no reason given".to_string())
        ));
    }
    let (Some(x0), Some(x1)) = (
        settled.value.get("x").and_then(Value::as_f64),
        later.value.get("x").and_then(Value::as_f64),
    ) else {
        return Err("the position reading did not carry an `x` coordinate".to_string());
    };
    let delta = x1 - x0;
    if !delta.is_finite() {
        return Err(format!("the position delta is not finite: {delta}"));
    }
    if delta.abs() > MOTION_EPSILON {
        return Err(format!(
            "the player still moved {delta} px (from {x0} to {x1}) after `move_dir = 0` was \
             written, so writing 0 does not stop it"
        ));
    }
    Ok(())
}

/// P3-position (round-1 write-path batch): a transform sample taken **at or
/// after** the frame the win flag turned true.
///
/// "At or after" is the honest form: a BRP batch is not frame-atomic (SPIKE-2
/// C4), so the transform is a second call and the game advances between them.
/// The criterion is that the win is located in the world at the frame it
/// happened, not that the two calls shared a frame.
pub fn win_position_at(win_frame: u64, position: &Reading) -> Result<(), String> {
    if position.failed {
        return Err(format!(
            "not observed: no transform sample followed the win frame ({})",
            position
                .reason
                .clone()
                .unwrap_or_else(|| "no reason given".to_string())
        ));
    }
    if position.value.get("x").and_then(Value::as_f64).is_none() {
        return Err("the transform sample at the win frame carried no `x` coordinate".to_string());
    }
    if position.frame < win_frame {
        return Err(format!(
            "the transform sample is from game frame {}, before the win frame {win_frame}",
            position.frame
        ));
    }
    Ok(())
}

/// The coin criterion: from `0` to at least one coin, without ever going back.
pub fn coins_increased(counts: &[i64]) -> Result<(i64, i64), String> {
    let Some(&first) = counts.first() else {
        return Err("not observed: no coin reading succeeded".to_string());
    };
    let Some(&last) = counts.last() else {
        return Err("not observed: no coin reading succeeded".to_string());
    };
    if first != 0 {
        return Err(format!(
            "the coin counter started at {first}, not 0 (PRD P2 requires the count to start at 0)"
        ));
    }
    if last <= 0 {
        return Err(format!(
            "the coin counter never rose above 0 (last reading {last})"
        ));
    }
    for window in counts.windows(2) {
        if window[1] < window[0] {
            return Err(format!(
                "the coin counter went backwards, {} then {}",
                window[0], window[1]
            ));
        }
    }
    Ok((first, last))
}

/// The win criterion: `false` first, `true` at the end, and never back.
pub fn win_became_true(flags: &[bool]) -> Result<(), String> {
    let Some(&first) = flags.first() else {
        return Err("not observed: no win-flag reading succeeded".to_string());
    };
    let Some(&last) = flags.last() else {
        return Err("not observed: no win-flag reading succeeded".to_string());
    };
    if first {
        return Err("the win flag was already true before the goal was reached".to_string());
    }
    if !last {
        return Err(format!(
            "the win flag never became true ({} readings, all false)",
            flags.len()
        ));
    }
    for window in flags.windows(2) {
        if window[0] && !window[1] {
            return Err(
                "the win flag went back to false (PRD P3 requires it to be one-way)".to_string(),
            );
        }
    }
    Ok(())
}

/// Why a read could not be observed, in the form an observation's failure uses.
fn read_gap(reading: &Reading) -> String {
    format!(
        "the `{}` read failed ({})",
        reading.kind.tool(),
        reading
            .reason
            .clone()
            .unwrap_or_else(|| "no reason given".to_string())
    )
}

/// The grounded criterion: `true` **before** the take-off, read as a semantic
/// fact rather than inferred from a coordinate.
pub fn grounded_before_takeoff(grounded: &[bool]) -> Result<(), String> {
    if grounded.is_empty() {
        return Err("not observed: no grounded reading before the take-off succeeded".to_string());
    }
    if grounded.iter().all(|value| !*value) {
        return Err(
            "`Grounded` read false before the take-off, so the jump has no semantic basis"
                .to_string(),
        );
    }
    Ok(())
}

/// Read the `y` of a player-transform reading, or say why not.
pub fn y_of(reading: &Reading) -> Result<f64, String> {
    if reading.failed {
        return Err(reading
            .reason
            .clone()
            .unwrap_or_else(|| "the reading was not observed".to_string()));
    }
    reading
        .value
        .get("y")
        .and_then(Value::as_f64)
        .ok_or_else(|| "the position reading did not carry a `y` coordinate".to_string())
}

/// Write this battery's evidence into a round directory:
/// `readings/e3-*.json` plus one `calls/<seq>-<tool>.json` per raw call.
///
/// It is exposed here (rather than hidden in the adapter) so the same function
/// writes the fake-driven round in the tests; every caller passes the root it
/// wants written below, and the repository's `runs/` is never implied.
pub fn write_observations(
    root: &std::path::Path,
    round: &str,
    observations: &E3Observations,
    server: &BevyMcpServer,
) -> Result<Vec<std::path::PathBuf>, String> {
    let directory =
        crate::adapter::mcp::evidence::round_dir(root, round).map_err(|error| error.to_string())?;
    let readings = directory.join(crate::adapter::mcp::evidence::READINGS_DIR);
    std::fs::create_dir_all(&readings).map_err(|error| error.to_string())?;
    let mut written = Vec::new();
    let summary = observations.summary_line();
    let path = readings.join("e3-summary.txt");
    std::fs::write(&path, format!("{summary}\n")).map_err(|error| error.to_string())?;
    written.push(path);
    let path = readings.join("e3-observations.json");
    std::fs::write(
        &path,
        serde_json::to_string_pretty(observations).map_err(|error| error.to_string())?,
    )
    .map_err(|error| error.to_string())?;
    written.push(path);
    // Every raw call keeps the same sequence numbers the server assigned, so the
    // `calls/` files and the observations refer to each other.
    for call in observations.all_calls() {
        let path = directory.join(call.rel_path());
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent).map_err(|error| error.to_string())?;
        }
        std::fs::write(
            &path,
            serde_json::to_string_pretty(&call.to_json()).map_err(|error| error.to_string())?,
        )
        .map_err(|error| error.to_string())?;
        written.push(path);
    }
    let _ = server;
    Ok(written)
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    fn observed(kind: SemanticKind, frame: u64, value: Value) -> Reading {
        Reading::observed(kind, frame, value)
    }

    fn position(frame: u64, x: f64, y: f64) -> Reading {
        observed(
            SemanticKind::PlayerTransform,
            frame,
            json!({"x": x, "y": y, "frame": frame}),
        )
    }

    #[test]
    fn movement_is_judged_on_the_position_not_on_the_call_count() {
        let before = position(1, 0.0, -200.0);
        let after = position(13, 92.0, -200.0);
        assert_eq!(movement_changed(&before, &after).unwrap(), 92.0);
        let still = position(13, 0.0, -200.0);
        assert!(movement_changed(&before, &still).is_err());
        let backward = position(13, -5.0, -200.0);
        assert!(movement_changed(&before, &backward).is_ok());
        let noise = position(13, 1e-9, -200.0);
        assert!(
            movement_changed(&before, &noise).is_err(),
            "floating-point noise is not motion"
        );
    }

    #[test]
    fn a_missing_read_is_not_a_zero_movement() {
        let before = Reading::not_observed(SemanticKind::PlayerTransform, 0, "no player entity");
        let after = position(13, 92.0, -200.0);
        let error = movement_changed(&before, &after).unwrap_err();
        assert!(error.starts_with("not observed:"), "{error}");
        assert!(error.contains("no player entity"), "{error}");
    }

    /// P1-left: the negative direction is its own criterion.  A game that only
    /// moves right, or that treats `-1` as `+1`, passes `movement_changed` and
    /// must fail this one.
    #[test]
    fn leftward_movement_is_the_negative_direction_and_not_merely_a_change() {
        let before = position(1, 0.0, -200.0);
        assert!(leftward_movement(&before, &position(13, -92.0, -200.0)).is_ok());
        let wrong_way = leftward_movement(&before, &position(13, 92.0, -200.0)).unwrap_err();
        assert!(wrong_way.contains("not"), "{wrong_way}");
        let still = leftward_movement(&before, &position(13, 0.0, -200.0)).unwrap_err();
        assert!(still.contains("leftward"), "{still}");
        let noise = leftward_movement(&before, &position(13, -1e-9, -200.0)).unwrap_err();
        assert!(noise.contains("leftward"), "{noise}");
        let missing = Reading::not_observed(SemanticKind::PlayerTransform, 0, "no player entity");
        assert!(leftward_movement(&missing, &position(13, -1.0, 0.0))
            .unwrap_err()
            .starts_with("not observed:"));
    }

    /// P1-release: writing `0` must stop the player, and "still moved a little"
    /// is a measured failure rather than a rounding detail.
    #[test]
    fn a_released_input_must_actually_stop_the_player() {
        assert!(released_stops(&position(40, 10.0, -200.0), &position(48, 10.0, -200.0)).is_ok());
        let coasting =
            released_stops(&position(40, 10.0, -200.0), &position(48, 26.0, -200.0)).unwrap_err();
        assert!(coasting.contains("does not stop it"), "{coasting}");
        assert!(
            released_stops(
                &position(40, 10.0, -200.0),
                &position(48, 10.0 + 1e-9, -200.0)
            )
            .is_ok(),
            "floating-point noise is not residual velocity"
        );
        let missing = Reading::not_observed(SemanticKind::PlayerTransform, 0, "no player entity");
        assert!(released_stops(&missing, &position(48, 10.0, -200.0))
            .unwrap_err()
            .starts_with("not observed:"));
    }

    /// P3-position: the win is located in the world at (or after) its frame, and
    /// a sample from *before* the win is refused rather than accepted as "near".
    #[test]
    fn the_win_position_must_be_at_or_after_the_win_frame() {
        let position = observed(
            SemanticKind::PlayerTransform,
            90,
            json!({"x": 72.0, "y": -200.0, "frame": 90}),
        );
        assert!(win_position_at(88, &position).is_ok());
        assert!(win_position_at(90, &position).is_ok());
        let too_early = win_position_at(91, &position).unwrap_err();
        assert!(too_early.contains("before the win frame"), "{too_early}");
        let no_x = observed(SemanticKind::PlayerTransform, 90, json!({"y": -200.0}));
        assert!(win_position_at(90, &no_x).unwrap_err().contains("no `x`"));
        let missing = Reading::not_observed(SemanticKind::PlayerTransform, 0, "no player entity");
        assert!(win_position_at(90, &missing)
            .unwrap_err()
            .starts_with("not observed:"));
    }

    #[test]
    fn the_coins_must_start_at_zero_and_rise() {
        assert_eq!(coins_increased(&[0, 0, 1]).unwrap(), (0, 1));
        assert_eq!(coins_increased(&[0, 1, 2, 3]).unwrap(), (0, 3));
        assert!(coins_increased(&[1, 2]).is_err());
        assert!(coins_increased(&[0, 0, 0]).is_err());
        assert!(coins_increased(&[0, 2, 1]).is_err());
        assert!(coins_increased(&[]).unwrap_err().contains("not observed"));
    }

    #[test]
    fn the_win_flag_must_be_false_then_true_and_one_way() {
        assert!(win_became_true(&[false, false, true]).is_ok());
        assert!(win_became_true(&[true]).is_err(), "already true");
        assert!(win_became_true(&[false, false]).is_err(), "never true");
        assert!(win_became_true(&[false, true, false]).is_err(), "went back");
        assert!(win_became_true(&[]).unwrap_err().contains("not observed"));
    }

    #[test]
    fn the_jump_needs_a_rise_and_a_fall() {
        let arc = vec![
            FrameSample {
                frame: 1,
                value: json!(-200.0),
            },
            FrameSample {
                frame: 2,
                value: json!(-180.0),
            },
            FrameSample {
                frame: 3,
                value: json!(-150.0),
            },
            FrameSample {
                frame: 4,
                value: json!(-180.0),
            },
            FrameSample {
                frame: 5,
                value: json!(-200.0),
            },
        ];
        let (arc, why) = JumpArc::classify(&arc);
        assert!(why.is_none(), "{why:?}");
        let arc = arc.unwrap();
        assert_eq!(arc.rising, 2);
        assert_eq!(arc.falling, 2);
        assert_eq!(arc.peak, -150.0);
        assert!(arc.verdict().is_ok());
    }

    #[test]
    fn a_monotone_fall_is_not_a_jump() {
        // This is the reading that was red in the Godot-era criterion; it must
        // stay red, and it must say why.
        let samples: Vec<FrameSample> = [-100.0, -110.0, -130.0, -160.0, -200.0]
            .iter()
            .enumerate()
            .map(|(index, y)| FrameSample {
                frame: index as u64 + 1,
                value: json!(y),
            })
            .collect();
        let (arc, why) = JumpArc::classify(&samples);
        assert!(why.is_none());
        let error = arc.unwrap().verdict().unwrap_err();
        assert!(error.contains("monotone fall"), "{error}");
    }

    #[test]
    fn a_rise_without_a_fall_is_not_a_jump_either() {
        let samples: Vec<FrameSample> = [-200.0, -180.0, -150.0, -120.0]
            .iter()
            .enumerate()
            .map(|(index, y)| FrameSample {
                frame: index as u64 + 1,
                value: json!(y),
            })
            .collect();
        let error = JumpArc::classify(&samples)
            .0
            .unwrap()
            .verdict()
            .unwrap_err();
        assert!(error.contains("never falls"), "{error}");
    }

    #[test]
    fn an_arc_needs_enough_samples_and_numeric_heights() {
        let short = vec![FrameSample {
            frame: 1,
            value: json!(-200.0),
        }];
        let (arc, why) = JumpArc::classify(&short);
        assert!(arc.is_none());
        assert!(why.unwrap().contains("at least 3"));
        let bad = vec![
            FrameSample {
                frame: 1,
                value: json!(-200.0),
            },
            FrameSample {
                frame: 2,
                value: json!("high"),
            },
            FrameSample {
                frame: 3,
                value: json!(-200.0),
            },
        ];
        let (arc, why) = JumpArc::classify(&bad);
        assert!(arc.is_none());
        assert!(why.unwrap().contains("not a number"));
    }

    #[test]
    fn the_grounded_basis_is_a_read_and_not_an_inference() {
        assert!(grounded_before_takeoff(&[true]).is_ok());
        assert!(grounded_before_takeoff(&[true, false, true]).is_ok());
        let error = grounded_before_takeoff(&[false, false]).unwrap_err();
        assert!(error.contains("no semantic basis"), "{error}");
        let error = grounded_before_takeoff(&[]).unwrap_err();
        assert!(error.contains("not observed"), "{error}");
    }

    #[test]
    fn the_arc_sampler_keeps_one_sample_per_game_frame() {
        let mut sampler = ArcSampler::new();
        assert!(sampler.push(&position(1, 0.0, -200.0)));
        assert!(!sampler.push(&position(1, 0.0, -200.0)));
        assert!(sampler.push(&position(2, 0.0, -199.5)));
        assert!(!sampler.push(&observed(
            SemanticKind::PlayerTransform,
            3,
            json!({"x": 1.0})
        )));
        assert!(!sampler.push(&Reading::not_observed(
            SemanticKind::PlayerTransform,
            4,
            "no player"
        )));
        assert_eq!(sampler.samples.len(), 2);
        assert_eq!(sampler.samples[1].frame, 2);
    }

    #[test]
    fn a_failed_criterion_is_not_an_unobserved_criterion() {
        let measured = Observation {
            observed: false,
            failure: Some("the arc never rises".to_string()),
            readings: vec![position(1, 0.0, -200.0)],
            arc: None,
            calls: Vec::new(),
        };
        assert!(measured.was_measured());
        assert!(!measured.was_unobservable());
        let unobserved = Observation::not_observed("the endpoint never answered", Vec::new());
        assert!(!unobserved.was_measured());
        assert!(unobserved.was_unobservable());
        assert!(unobserved.failure.unwrap().starts_with("not observed:"));
    }

    /// A driver whose reads come from per-kind scripts, with the last entry
    /// repeating.  It exists so the two honesty defects (B2-7 and B2-8) are
    /// pinned in the default gate without an engine: the phases are driven
    /// exactly as a game would drive them, and only the answer changes.
    struct ScriptedReads {
        grounded: Vec<Reading>,
        coins: Vec<Reading>,
        win: Vec<Reading>,
        transform: Vec<Reading>,
        grounded_at: usize,
        coins_at: usize,
        win_at: usize,
        transform_at: usize,
    }

    impl ScriptedReads {
        fn new(
            grounded: Vec<Reading>,
            coins: Vec<Reading>,
            win: Vec<Reading>,
            transform: Vec<Reading>,
        ) -> Self {
            Self {
                grounded,
                coins,
                win,
                transform,
                grounded_at: 0,
                coins_at: 0,
                win_at: 0,
                transform_at: 0,
            }
        }

        fn advance(script: &[Reading], at: &mut usize) -> Reading {
            let index = (*at).min(script.len().saturating_sub(1));
            *at += 1;
            script[index].clone()
        }
    }

    impl BatteryDriver for ScriptedReads {
        fn read(&mut self, kind: SemanticKind) -> anyhow::Result<Reading> {
            Ok(match kind {
                SemanticKind::Grounded => Self::advance(&self.grounded, &mut self.grounded_at),
                SemanticKind::CoinCounter => Self::advance(&self.coins, &mut self.coins_at),
                SemanticKind::WinFlag => Self::advance(&self.win, &mut self.win_at),
                SemanticKind::PlayerTransform => {
                    Self::advance(&self.transform, &mut self.transform_at)
                }
            })
        }

        fn inject(
            &mut self,
            _intent: &Intent,
            _level: bool,
        ) -> anyhow::Result<crate::adapter::InjectionReport> {
            Ok(crate::adapter::InjectionReport::accepted(0))
        }

        fn wait_frames(&mut self, n: u32) -> anyhow::Result<crate::adapter::FrameMark> {
            Ok(crate::adapter::FrameMark {
                requested: n,
                frame: 0,
            })
        }

        fn take_evidence(&mut self) -> Vec<CallEvidence> {
            Vec::new()
        }
    }

    fn grounded_obs(frame: u64, value: bool) -> Reading {
        observed(
            SemanticKind::Grounded,
            frame,
            json!({"grounded": value, "frame": frame}),
        )
    }

    fn coins_obs(frame: u64, value: i64) -> Reading {
        observed(
            SemanticKind::CoinCounter,
            frame,
            json!({"coins": value, "frame": frame}),
        )
    }

    fn win_obs(frame: u64, value: bool) -> Reading {
        observed(
            SemanticKind::WinFlag,
            frame,
            json!({"won": value, "frame": frame}),
        )
    }

    fn gone(kind: SemanticKind, reason: &str) -> Reading {
        Reading::not_observed(kind, 0, reason.to_string())
    }

    fn never_grounded() -> Vec<Reading> {
        vec![
            grounded_obs(1, true),
            grounded_obs(5, true),
            grounded_obs(9, false),
        ]
    }

    fn no_coin() -> (Vec<Reading>, Vec<Reading>) {
        (
            vec![
                coins_obs(1, 0),
                coins_obs(5, 0),
                coins_obs(9, 0),
                coins_obs(13, 0),
            ],
            vec![
                win_obs(1, false),
                win_obs(5, false),
                win_obs(9, false),
                win_obs(13, false),
            ],
        )
    }

    /// B2-7: a surface that disappears mid-phase is **not observed**, not a
    /// measured failure.  Reading "the counter never rose above 0" when the
    /// counter could not be read at all is the false-green class this harness
    /// exists to prevent.
    #[test]
    fn a_vanished_surface_is_not_a_measured_failure() {
        let (coins, win) = no_coin();
        let mut coins = coins;
        coins.push(gone(SemanticKind::CoinCounter, "the resource vanished"));
        let mut driver = ScriptedReads::new(
            never_grounded(),
            coins,
            win,
            vec![position(1, 0.0, -200.0), position(5, 0.0, -200.0)],
        );
        let observations = BatteryRun::new(&mut driver)
            .run()
            .expect("the battery runs");
        let coins = &observations.coins;
        assert!(!coins.observed);
        let failure = coins.failure.clone().expect("a failure reason");
        assert!(
            failure.starts_with("not observed"),
            "a vanished surface is not a measured failure: {failure}"
        );
        assert!(failure.contains("vanished"), "{failure}");
        assert!(
            !coins.was_measured(),
            "the criterion was not measured: {failure}"
        );
        assert!(coins.was_unobservable());
    }

    /// B2-7, the other direction: a surface that is read and answers `false`
    /// stays a **measured** failure, so the fix cannot turn every failure into
    /// "not observed".
    #[test]
    fn a_read_that_answers_false_is_still_a_measured_failure() {
        let (coins, win) = no_coin();
        let mut driver = ScriptedReads::new(
            never_grounded(),
            coins,
            win,
            vec![position(1, 0.0, -200.0), position(5, 0.0, -200.0)],
        );
        let observations = BatteryRun::new(&mut driver)
            .run()
            .expect("the battery runs");
        let coins = &observations.coins;
        assert!(!coins.observed);
        let failure = coins.failure.clone().expect("a failure reason");
        assert!(
            !failure.starts_with("not observed"),
            "a measured failure must not be relabelled: {failure}"
        );
        assert!(coins.was_measured());
        assert!(!coins.was_unobservable());
    }

    /// B2-8: when the phase's own `Grounded` read is false but the
    /// pre-injection baseline read true, the baseline is the stronger evidence
    /// and criterion ⑤ holds.  The dead branch used to let the phase read win
    /// regardless.
    #[test]
    fn the_pre_injection_baseline_decides_the_grounded_criterion() {
        let (coins, win) = no_coin();
        let mut driver = ScriptedReads::new(
            // baseline: two true reads; the jump phase's own read is false.
            vec![
                grounded_obs(1, true),
                grounded_obs(5, true),
                grounded_obs(9, false),
            ],
            coins,
            win,
            vec![position(1, 0.0, -200.0)],
        );
        let observations = BatteryRun::new(&mut driver)
            .run()
            .expect("the battery runs");
        assert!(
            observations.grounded.observed,
            "the baseline read the ground before the take-off: {:?}",
            observations.grounded.failure
        );
        assert!(observations.grounded.failure.is_none());

        // Control: neither the baseline nor the phase read saw the ground.
        let (coins, win) = no_coin();
        let mut driver = ScriptedReads::new(
            vec![
                grounded_obs(1, false),
                grounded_obs(5, false),
                grounded_obs(9, false),
            ],
            coins,
            win,
            vec![position(1, 0.0, -200.0)],
        );
        let observations = BatteryRun::new(&mut driver)
            .run()
            .expect("the battery runs");
        let failure = observations
            .grounded
            .failure
            .clone()
            .expect("no ground state before take-off");
        assert!(!observations.grounded.observed);
        assert!(failure.contains("no semantic basis"), "{failure}");
        assert!(
            failure.contains("immediately before take-off"),
            "the phase's own reading is still reported: {failure}"
        );
    }

    #[test]
    fn the_observation_set_reports_every_gap_and_only_passes_when_all_five_do() {
        let done = || Observation {
            observed: true,
            failure: None,
            readings: Vec::new(),
            arc: None,
            calls: Vec::new(),
        };
        let mut set = E3Observations {
            movement: done(),
            coins: done(),
            win: done(),
            jump: done(),
            grounded: done(),
            movement_left: done(),
            movement_release: done(),
            win_position: done(),
            grounded_payload: done(),
            aborted: None,
        };
        assert!(set.passed());
        assert!(set.gaps().is_empty());
        set.coins = Observation {
            observed: false,
            failure: Some("the counter never rose above 0".to_string()),
            readings: Vec::new(),
            arc: None,
            calls: Vec::new(),
        };
        assert!(!set.passed());
        assert_eq!(set.gaps().len(), 1);
        set.aborted = Some("the game process died".to_string());
        assert_eq!(set.gaps().len(), 9, "an aborted battery gapped all nine");
        for (name, reason) in set.gaps() {
            assert!(reason.contains("the game process died"), "{name}: {reason}");
        }
    }
}
