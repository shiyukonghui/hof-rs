//! hof-rs: the Harness-of-Harness runtime.
//!
//! Layering (see `DESIGN-OVERVIEW.md` §2): a deterministic [`runtime`]
//! orchestrates three roles, each of which is one independent call through the
//! [`harness`] boundary; project specifics live behind the adapter boundary and
//! tool access is funnelled through a role-scoped tool channel.

pub mod cli;
pub mod cli_impl;
pub mod config;
pub mod errors;
pub mod model;
pub mod runtime;

pub use mini_swe_agent;
