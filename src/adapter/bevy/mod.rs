//! The Bevy 0.19.1 adapter tree (DESIGN-OVERVIEW §1).
//!
//! This batch lands the pieces the design fixes independently of a running
//! engine — the reflectable contract, the BRP client, the two-layer tool
//! surface and the round-evidence layout.  `BevyAdapter` itself (build/launch
//! orchestration, `DESIGN-OVERVIEW`'s `mod.rs` responsibility) is deliberately
//! **not** here yet: it needs a real game to drive and belongs to the next
//! batch.

pub mod brp;
pub mod build;
pub mod contract;
