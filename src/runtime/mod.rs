//! The deterministic runtime: views, permission enforcement, schema gates,
//! evidence binding, snapshots, records and the main loop.

pub mod engine_identity;
pub mod evidence;
/// DR-86 ④: restoring a frozen view a role wrote into, without deleting the
/// role's bytes.
pub mod frozen_view;
pub mod hygiene;
/// DR-86 ①: detecting a delivered fragment or a foreign shell escape.
pub mod integrity;
pub mod invoke;
pub mod policy;
pub mod project_map;
pub mod record;
pub mod role;
pub mod run_loop;
pub mod schema;
pub mod secrets;
/// DR-66: the shell a role's commands run in, and the syntax of the documents
/// that describe them.
pub mod shell;
pub mod snapshot;
pub mod start_state;
pub mod usage;
pub mod view;
