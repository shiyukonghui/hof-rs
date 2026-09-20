//! The tool policy table (§5.4).
//!
//! The canonical matrix lives in [`crate::runtime::policy::tool_matrix`] so the
//! runtime's permission checks and the tool channel can never disagree; this
//! module is the public face used by the CLI bridge and the tests.

pub use crate::runtime::policy::denial_reason;
pub use crate::runtime::policy::tool_matrix::{
    is_mutating, is_tester_allowed, tool_allowed, PLANNER_DENY_PREFIXES,
};

use crate::model::Role;

/// The structured rejection body printed by `hoh tools call` (exit 2).
pub fn denial_payload(role: Role, tool: &str) -> serde_json::Value {
    serde_json::json!({
        "ok": false,
        "error": "tool_not_permitted",
        "role": role.as_str(),
        "tool": tool,
        "hint": denial_reason(role, tool),
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::model::Role;

    #[test]
    fn developer_may_use_everything() {
        assert!(tool_allowed(Role::Developer, "add_node"));
        assert!(tool_allowed(Role::Developer, "totally_unknown_tool"));
    }

    #[test]
    fn planner_may_use_nothing() {
        assert!(!tool_allowed(Role::Planner, "get_editor_errors"));
        assert!(!tool_allowed(Role::Planner, "add_node"));
        assert_eq!(PLANNER_DENY_PREFIXES, &["*"]);
    }

    #[test]
    fn tester_is_default_deny() {
        assert!(tool_allowed(Role::Tester, "get_editor_errors"));
        assert!(tool_allowed(Role::Tester, "simulate_sequence"));
        assert!(!tool_allowed(Role::Tester, "some_new_mcp_tool"));
        assert!(!tool_allowed(Role::Tester, "execute_game_script"));
    }

    #[test]
    fn denial_payload_has_the_documented_shape() {
        let payload = denial_payload(Role::Tester, "add_node");
        assert_eq!(payload["ok"], serde_json::json!(false));
        assert_eq!(payload["error"], serde_json::json!("tool_not_permitted"));
        assert_eq!(payload["role"], serde_json::json!("tester"));
        assert_eq!(payload["tool"], serde_json::json!("add_node"));
    }
}
