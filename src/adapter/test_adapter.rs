//! `TestAdapter`: a project-type stand-in for the offline test suite.
//!
//! It never touches the network, Godot, or the MCP server, yet it exercises the
//! exact same runtime path as the Godot adapter.

use std::path::Path;

use crate::adapter::{DoctorItem, ProjectAdapter};
use crate::model::{ExecKind, ExecRecord, Role};
use crate::tools::ToolChannel;

/// Fixed observation string asserted by the offline tests.
pub const TEST_BUILD_OBSERVATION: &str = "test adapter: build check ok";
/// Fixed evidence playbook returned for the Tester view.
pub const TEST_PLAYBOOK: &str = "## Evidence playbook (test adapter)\n\nRecord one exec record.\n";

#[derive(Debug, Default)]
pub struct TestAdapter {
    /// When set, `build_check` writes this file (simulating an editor-side
    /// change to the real project) before returning.
    pub drift: Option<(std::path::PathBuf, String, String)>,
}

impl TestAdapter {
    pub fn new() -> Self {
        Self::default()
    }
}

#[async_trait::async_trait]
impl ProjectAdapter for TestAdapter {
    fn initialize(&self, workspace: &Path) -> anyhow::Result<()> {
        std::fs::create_dir_all(workspace)?;
        std::fs::write(workspace.join("marker.txt"), "hof-rs test adapter\n")?;
        Ok(())
    }

    fn cache_excludes(&self) -> Vec<String> {
        vec!["cache".to_string()]
    }

    async fn build_check(
        &self,
        candidate_view: &Path,
        _tools: &dyn ToolChannel,
    ) -> anyhow::Result<Vec<ExecRecord>> {
        if let Some((workspace, rel, content)) = &self.drift {
            let target = workspace.join(rel);
            if let Some(parent) = target.parent() {
                std::fs::create_dir_all(parent)?;
            }
            std::fs::write(&target, content)?;
        }
        // Deterministic records are materialized under the candidate view so
        // the Tester can reference them by relative path.
        let dir = candidate_view.join(".hoh/deterministic");
        std::fs::create_dir_all(&dir)?;
        let record = ExecRecord {
            kind: ExecKind::Build,
            path: Some(".hoh/deterministic/build.json".to_string()),
            observation: TEST_BUILD_OBSERVATION.to_string(),
            candidate_id: String::new(),
        };
        std::fs::write(
            dir.join("build.json"),
            serde_json::to_string_pretty(&record)?,
        )?;
        Ok(vec![record])
    }

    fn evidence_playbook(&self) -> String {
        TEST_PLAYBOOK.to_string()
    }

    fn tool_policy(&self, role: Role) -> Vec<String> {
        match role {
            Role::Developer => vec!["get_editor_errors".to_string(), "add_node".to_string()],
            Role::Tester => vec![
                "get_editor_errors".to_string(),
                "assert_node_state".to_string(),
            ],
            Role::Planner => Vec::new(),
        }
    }

    fn doctor(&self, workspace: &Path) -> anyhow::Result<Vec<DoctorItem>> {
        Ok(vec![DoctorItem {
            name: "test-adapter".to_string(),
            ok: true,
            detail: format!("workspace {}", workspace.display()),
        }])
    }
}
