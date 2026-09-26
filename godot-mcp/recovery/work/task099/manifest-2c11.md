
---

# REBUILT-2C MANIFEST — 2c-11 (TASK-099)

* Task: TASK-099 — (A) the 8th and 9th C# games (Frogger, Flappy Bird), written through MCP
  calls only; (B) `tools\run_gates.ps1` learns to recognise a purely non-compiling (doc-only)
  submission instead of running the ten gates for no information; (C) the `--import` shutdown
  access violation, live once more, probed again under control.
* **`modules\mcp_server` was not touched.** In the engine repo
  `git diff --name-only --no-renames 2385fe2fb..HEAD` is two `.md` files
  (`docs\reports\MCP-TRACEABILITY.md`, `docs\reports\REBUILT-2C-MANIFEST.md`) and
  `git status --porcelain` is empty, before and after this task. Both variants are still the
  TASK-097 builds (`4.8.dev.mono.custom_build.2385fe2fb` / `4.8.dev.custom_build.2385fe2fb`),
  so **nothing was rebuilt and the two binaries are byte-for-byte what TASK-097 gated**.
  The module's own anchor judge answers `ANCHOR_STRUCTURAL_EQUIVALENT` for that pair
  (`diff_count=2 safe_count=2 red_count=0`).

## L-1. 2c-11-a: the gate runner's educational preflight — outside the engine tree

| # | file | what changed | why it cannot affect either variant |
|---|---|---|---|
| 1 | `tools\run_gates.ps1` (main repo `F:\moonbit-hof-rs\godot-mcp\tools\`, **not** part of the engine repo) | a preflight in front of the ten gates. It dot-sources `modules\mcp_server\scripts\check_engine_anchor.ps1` — **one classifier, not a second copy of the whitelist** — takes the anchor from the built binary's own `--version` unless `-Anchor`/`-VersionText` override it, adds `git status --porcelain --untracked-files=all` to the committed range, and when nothing in either is a compile input prints `ANCHOR_STRUCTURAL_EQUIVALENT`, the criterion, the non-compiling file list, `GATES_SKIPPED=1` and exits 0 **without running a gate**. Any compile input (committed or in the working tree) means `VERDICT=RUN_GATES` and the ten gates run exactly as before. `-RunGates` forces that path; `-PreflightOnly` stops after the verdict | it is a PowerShell script in the **main** repository. The engine repo's `git status` is empty before and after, so this change is not in `2385fe2fb..HEAD`, cannot reach a `.cpp`/`.h`, and cannot change either binary — there is nothing to rebuild. It is registered here because this manifest is where the gate apparatus of the module is recorded (the 2c-8 section already lists `run_gates.ps1` among the module-adjacent tooling) |

Measured, three cases (logs `recovery\work\task099\logs\`, runs `runs\gates\`):

| case | preflight verdict | gates |
|---|---|---|
| **doc-only submission**: anchor `2385fe2fb` (the binary's own `--version`) against HEAD `0fbd5ec4c`, diff = the two `.md` files | `VERDICT=ANCHOR_STRUCTURAL_EQUIVALENT`, `WORKING_TREE_RED=0 WORKING_TREE_SAFE=0 COMMITTED_DIFF_SAFE=2`, `NONCOMPILING_COUNT=2` (both paths printed), `RESULT=SKIP_REBUILD`, `GATES_SKIPPED=1`, **exit 0** | none ran and none could add information: the diff cannot change compiled behaviour (`runs\gates\task099-doconly\summary.txt`) |
| **one compile input in the working tree**: an untracked `modules\mcp_server\tools\task099_preflight_probe_b.cpp`, created for this measurement and removed immediately afterwards | `VERDICT=RUN_GATES`, `REASON="the engine working tree carries 1 compile input(s) that are not in any built binary"`, `GATES_SKIPPED=0` | **`g01`..`g10` all `exit=0`**, including `g09` `ANCHOR_STRUCTURAL_EQUIVALENT` and `g10 accept_m1` **`22/22 cases passed`** (`runs\gates\task099-compileinput\summary.txt`) |
| **control for the committed-diff branch**: `-Anchor 95aa1d8984 -PreflightOnly`, whose diff to HEAD carries four `.cpp/.h` files | `VERDICT=RUN_GATES` with `ANCHOR_STALE_COMPILED` naming `test_mcp_server.h`, `editor_node_batch_write.{cpp,h}`, `editor_write_scene_editor.cpp` | preflight only (no gate run in this measurement) |

The preflight also closes ledger item **G-1** at the root: the stale hard-coded `-VersionText`
default (`4.8.dev.mono.custom_build.8604fcf9e`, the TASK-090 anchor) is gone; gate 9 now always
judges the binary that is actually on disk.

## L-2. 2c-11-b: the `--import` shutdown access violation

* **Live occurrence #3**: the first import of the brand-new `projects\frogger`
  (`runs\frogger\frog-task099-r1\import.stdout.txt` / `import.stderr.txt`) —
  `IMPORT_EXIT=-1073741819`, stderr exactly
  `ERROR: Parameter "singleton" is null. / at: EditorNode::is_cmdline_mode (editor\editor_node.cpp:6750)`,
  reached `[ DONE ] loading_editor_layout`, 23 stdout lines, i.e. **after the import finished**.
* **Control**: the very next session's import of the equally brand-new `projects\flappy` was
  `exit=0`. So "brand-new project" alone is not the discriminator.
* Controlled probe `recovery\work\task099\import_crash_probe2.ps1`: fresh copies of
  `projects\frogger` (no `.godot`/`bin`/`obj`), the **default port 9877** the real driver uses,
  fresh vs warm, with and without CPU burners — results and counts in
  `recovery\work\task099\logs\importprobe*`.
* **The engine was not edited.** The ledger's rule is "no root cause, no speculative change"
  and the task's own escape hatch is "if it cannot be reproduced on demand, only instrument and
  count". No instrumentation was added either, because the three discriminators the ledger
  lists all require an engine rebuild and would have been built on a hypothesis the probe
  could not confirm — see `runs\gates` / the task report for the counts actually obtained.
