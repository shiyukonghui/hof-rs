#!/bin/sh
set -e
cd "/mnt/f/moonbit-hof-rs/godot-mcp/godot" || exit 9
export LC_ALL=C.UTF-8

git add modules/mcp_server/scripts/mcp029_clear_default_evidence.ps1
git commit -q -m "evid: read the pre-override wording from the engine baseline (TASK-154)

mcp029_clear_default_evidence.ps1 bound its old-description source to the
hof-rs working file F:\\moonbit-hof-rs\\tests\\fixtures\\mcp\\tools_list.json.
That file is outside this repository and hof-rs commit db2eed7 has since
re-captured it to the 177-tool four-channel shape, so the constant could only
ever yield an empty prefix. It now reads docs/rename-baseline-tools-list.json
through the same \$PSScriptRoot-derived pattern check_rename_map.py (TASK-152)
and gen_renamed_contract.py (TASK-153) use.

The substitution is byte-identical: the engine baseline is the whole-file
equal of the hof-rs fixture blob 543b49b2 (48749 B, sha256 8f8051c4) this
script always intended, so the two descriptions it compares against are
unchanged. Evidence: recovery/work/task154/equivalence_check.ps1."

git add modules/mcp_server/scripts/mcp032_d3_d4_d6_evidence.ps1
git commit -q -m "evid: drop the cross-repo fixture path and the user port from mcp032 (TASK-154)

mcp032_d3_d4_d6_evidence.ps1 read its pre-override wording from the hof-rs
working file and carried the decision maker's editor port for a six-way
classification of that port's state. Both are removed:

* the old-description source is now docs/rename-baseline-tools-list.json, the
  engine-internal baseline TASK-152/TASK-153 already read; the baseline is
  byte-identical to the hof-rs blob this script always intended (543b49b2,
  48749 B, sha256 8f8051c4), so what the script evidences is unchanged;
* the port is now refused outright: a requested test port outside {9888, 9889}
  exits 4 before any process starts, and the port literal is refused in the
  launch context. The mcp_port_guard.ps1 dot-source and its pid bookkeeping
  go with it; they are replaced by test_ports_only and test_ports_released,
  which describe what this script itself did.

Neither script is on the ten-gate path, so no gate's criterion changes."

git add modules/mcp_server/docs/MCP-SERVER-HANDOVER.md
git commit -q -m "docs: record _meta.generated_from as history, not current input (TASK-154)

Adds the handover note that docs/tools_list.renamed.json's
_meta.generated_from names the hof-rs fixture the artifact was generated from
(commit 54200f0d77, 2026-09-26) and is a provenance record, not a statement
about the generator's current input - which reads the engine baseline since
TASK-153. The frozen artifact is NOT regenerated: its blob (3b1b191d),
154272 bytes and sha256 (fd00c75e) are unchanged.

Also records the two evidence scripts' de-coupling and its byte-identical
equivalence evidence."

git log --oneline -4
git status --porcelain
