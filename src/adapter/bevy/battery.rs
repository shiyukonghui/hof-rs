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
/// How many frames to wait after a possible coin/goal contact.
pub const CONTACT_SETTLE_FRAMES: u32 = 8;
/// How many contact rounds the coin/win phase runs.
pub const CONTACT_ROUNDS: usize = 4;
/// How long a jump's press is held, in frames.
pub const JUMP_HOLD_FRAMES: u32 = 2;
/// How many polls the arc is sampled for.
pub const ARC_POLLS: u32 = 18;
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

/// The five observations.
#[derive(Clone, Debug, PartialEq, Serialize)]
pub struct E3Observations {
    pub movement: Observation,
    pub coins: Observation,
    pub win: Observation,
    pub jump: Observation,
    pub grounded: Observation,
    /// `None` when the battery ran; `Some(reason)` when it could not run at all
    /// (in which case every observation is "not observed").
    pub aborted: Option<String>,
}

impl E3Observations {
    /// Every observation that was not made, with the reason.  This is what a
    /// Tester must consume instead of inventing proof.
    pub fn gaps(&self) -> Vec<(&'static str, String)> {
        let named: [(&'static str, &Observation); 5] = [
            ("movement", &self.movement),
            ("coins", &self.coins),
            ("win", &self.win),
            ("jump", &self.jump),
            ("grounded", &self.grounded),
        ];
        let mut gaps = Vec::new();
        if let Some(reason) = &self.aborted {
            for (name, _) in named {
                gaps.push((name, format!("not observed: the battery aborted: {reason}")));
            }
            return gaps;
        }
        for (name, observation) in named {
            if !observation.observed {
                gaps.push((
                    name,
                    observation
                        .failure
                        .clone()
                        .unwrap_or_else(|| "not observed".to_string()),
                ));
            }
        }
        gaps
    }

    /// All five criteria met.
    pub fn passed(&self) -> bool {
        self.aborted.is_none()
            && self.movement.observed
            && self.coins.observed
            && self.win.observed
            && self.jump.observed
            && self.grounded.observed
    }

    /// The evidence of every observation, flattened in the frozen order.
    pub fn all_calls(&self) -> Vec<CallEvidence> {
        let mut calls = Vec::new();
        for observation in [
            &self.movement,
            &self.coins,
            &self.win,
            &self.jump,
            &self.grounded,
        ] {
            calls.extend(observation.calls.iter().cloned());
        }
        calls
    }

    /// The readings of one surface, in observation order.
    pub fn readings_of(&self, kind: SemanticKind) -> Vec<&Reading> {
        let mut readings = Vec::new();
        for observation in [
            &self.movement,
            &self.coins,
            &self.win,
            &self.jump,
            &self.grounded,
        ] {
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
        let mark = |observation: &Observation| if observation.observed { "ok" } else { "RED" };
        format!(
            "E3 movement={} coins={} win={} jump={} grounded={}",
            mark(&self.movement),
            mark(&self.coins),
            mark(&self.win),
            mark(&self.jump),
            mark(&self.grounded)
        )
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
                aborted: None,
            },
            baseline_coins: None,
            baseline_won: None,
            baseline_grounded: None,
            baseline_transform: None,
        }
    }

    /// Run all five phases.  A task-level failure from a read/inject/wait aborts
    /// the battery with the reason; it never panics and never invents a value.
    pub fn run(mut self) -> anyhow::Result<E3Observations> {
        if let Err(error) = self.run_inner() {
            // A task-level failure is not evidence about the game — the round
            // could not be observed at all — so it is recorded as an abort, not
            // as five failed criteria.
            let reason = error.to_string();
            let calls = self.driver.take_evidence();
            self.observations.aborted = Some(reason.clone());
            self.observations.movement = Observation::not_observed(reason.clone(), calls);
            self.observations.coins =
                Observation::not_observed(reason.clone(), self.driver.take_evidence());
            self.observations.win =
                Observation::not_observed(reason.clone(), self.driver.take_evidence());
            self.observations.jump =
                Observation::not_observed(reason.clone(), self.driver.take_evidence());
            self.observations.grounded =
                Observation::not_observed(reason, self.driver.take_evidence());
        }
        Ok(self.observations)
    }

    fn run_inner(&mut self) -> anyhow::Result<()> {
        self.phase_baselines()?;
        self.phase_movement()?;
        self.phase_coins_and_win()?;
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
        let won = self.driver.read(SemanticKind::WinFlag)?;
        if !won.failed {
            self.baseline_won = won.value.get("won").and_then(Value::as_bool);
        }
        let transform = self.driver.read(SemanticKind::PlayerTransform)?;
        if !transform.failed {
            self.baseline_transform = Some(transform.clone());
        }
        calls.extend(self.driver.take_evidence());
        let failure = grounded_before_takeoff(&grounded_flags).err();
        self.observations.grounded = Observation {
            observed: failure.is_none(),
            failure,
            readings: grounded_readings,
            arc: None,
            calls,
        };
        let _ = transform;
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

    /// ② coins and ③ the win flag: hold right and watch both.
    fn phase_coins_and_win(&mut self) -> anyhow::Result<()> {
        let mut calls = self.begin();
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
                flags.push(
                    flag.value
                        .get("won")
                        .and_then(Value::as_bool)
                        .unwrap_or(false),
                );
            }
            readings.push(flag);
        }
        let _ = self.driver.inject(&Intent::Move { dir: 0 }, true)?;
        let _ = self.driver.wait_frames(SETTLE_FRAMES)?;
        calls.extend(self.driver.take_evidence());

        let coin_failure = coin_gap
            .map(|reason| format!("{NOT_OBSERVED_PREFIX}: {reason}"))
            .or_else(|| coins_increased(&counts).err());
        let win_failure = win_gap
            .map(|reason| format!("{NOT_OBSERVED_PREFIX}: {reason}"))
            .or_else(|| win_became_true(&flags).err());
        // The same phase reads both surfaces, so both observations keep the same
        // raw calls; the readings are split by surface so a reader can see which
        // call produced which number.
        self.observations.coins = Observation {
            observed: coin_failure.is_none(),
            failure: coin_failure,
            readings: readings
                .iter()
                .filter(|reading| reading.kind == SemanticKind::CoinCounter)
                .cloned()
                .collect(),
            arc: None,
            calls: calls.clone(),
        };
        self.observations.win = Observation {
            observed: win_failure.is_none(),
            failure: win_failure,
            readings: readings
                .into_iter()
                .filter(|reading| reading.kind == SemanticKind::WinFlag)
                .collect(),
            arc: None,
            calls,
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
        for _ in 0..ARC_POLLS {
            let sample = self.driver.read(SemanticKind::PlayerTransform)?;
            sampler.push(&sample);
            readings.push(sample);
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
        assert_eq!(set.gaps().len(), 5, "an aborted battery gapped all five");
        for (name, reason) in set.gaps() {
            assert!(reason.contains("the game process died"), "{name}: {reason}");
        }
    }
}
