# -*- coding: utf-8 -*-
"""task088: append the 2c-7 section to REBUILT-2C-MANIFEST.md (UTF-8, no shell
redirection, no PowerShell encoding round trip).

usage: python append_manifest.py
"""
from __future__ import print_function
import io

MANIFEST = r"H:\rebuild\godot\modules\mcp_server\docs\reports\REBUILT-2C-MANIFEST.md"

SECTION = u"""
---

# REBUILT-2C MANIFEST — 2c-7 (`H:\\rebuild\\godot`, branch `feature/mcp-server-module-rebuild`)

* Task: TASK-088 — the mono axis, the acceptance battery, the contract's missing
  override records, and the traceability capability.
* Start HEAD: `675df5ef27`. Method unchanged: recorded text is replayed at its
  recorded position; anything written instead is wrapped in
  `[REBUILT-2C low-confidence: verify] … [/REBUILT-2C]` in the file and listed
  below with its basis and its behaviour risk.
* Tooling: `C:\\Users\\wyl\\AppData\\Local\\Temp\\mcp-recovery\\work\\task088\\`
  (`ev.py`, `recon_sk.py`, `cov.py`, `ovdiff.py`, `cmp_live.py`, `meta6.py`,
  `add_overrides.py`, `patch_accept_m1.py`, `del_stale_objs.py`, `cov.py`,
  `verify_gen_expr.py`, `find_map_path2.py`, `mk_csharp_proj.py`,
  `mcp088_live_evidence.ps1`).

## G-1. A correction to the 2c-6 section: `seq=1030` is not unique

The 2c-6 section says case0's recorded text is `events-edit seq=1030
t=1790321324515`, and the 2c-6 batch's graft failed with 17 parse errors. The
cause is now measured: **`seq` is only unique inside one session file**, and
TWO rows carry `seq=1030`:

| `seq` | `time` | path | what it is |
|---|---|---|---|
| 1030 | 1790155671555 | `tools/editor_shader_write.h` | a C++ comment rewrite |
| 1030 | 1790321324515 | `scripts/accept_m1.ps1` | the block that adds `case0_repo_exit_code_propagation` |

The 2c-6 graft took the `editor_shader_write.h` row (a C++ banner) and spliced it
into the `.ps1` — which is why the graft could not parse, and why the all-windows
union carried `editor_shader_write.cpp`'s banner at line 556. Selecting on
`(path, seq, time)` yields the correct text, which replays cleanly.
**Ruling: the 2c-6 "not rebuilt" entry for case0 is superseded; case0 is
replayed verbatim in this batch** (`work/task088/patch_accept_m1.py`).

## G-2. Written (marked), with basis and risk

| # | file | what was written | why it could not be replayed | basis | behaviour risk |
|---|---|---|---|---|---|
| 1 | `mcp_jsonrpc.cpp` | `dispatch`: `trace.id_json = id_json; trace.method = method;`; `_dispatch_tools_call`: `r_trace.tool = tool_name;`; the `tools/list` branch: `trace.is_tools_list = true; trace.tool_count = get_visible_tool_count(...)` | TASK-085 ruling (C) already recorded that `dispatch` is written, not replayed: the only recorded definition (rev388:311) takes four parameters and predates the trace, so no recording carries these lines | **measured defect**: a real session (`live/trace-editor.jsonl`) produced call lines with `"method":""`, `"id":null`, no `tool`, no `args`, while the capture line beside them named the tool. The field list and the read conditions are fixed by `mcp_trace.h:132-182` and `mcp_trace.cpp:322-346` | **none on the wire** — the four fields feed the trace line only (`Recorder::_build_line`); a process with `--mcp-trace` off builds no line at all. Risk is that a trace-consuming test asserts an exact line; the module suite was re-run green (G-5) |
| 2 | `scripts/gen_renamed_contract.py` | six `DESCRIPTION_OVERRIDES` records (`validate_script`, `reload_plugin`, `set_input_action`, `add_autoload`, `remove_autoload`, `set_project_setting`), each `value` = the text the server publishes; `play_scene`'s `value` replaced with the published text; `RECORDED_MAP_PATH` and `_meta.map_path` switched to it | the recordings carry no contract body; `events-write` has 0 rows for `docs/tools_list.renamed.json`, so the records could not be replayed | **measured**: the live 154-tool `tools/list` body (`live/editor-tools-list.json`) compared against the contract leaves exactly 10 disagreeing tools (7 descriptions, 3 inputSchemas); `work/task088/cmp_editor.txt` holds every pair. The 6 appended texts are `<contract text> + " " + …` (verified), the shared 400-byte sentence is the recorded TASK-043 constant (`scripts/mcp043_description_evidence.ps1:50`) and the same sentence stands verbatim in the five C++ literals. `RECORDED_MAP_PATH` is replayed from `events-termdump.jsonl` (nine rows, e.g. 228/569/1127) next to the same `map_sha256` this tree has | **medium, declared**: the 7 descriptions now match the wire byte for byte; the 3 inputSchema disagreements were left alone (see G-3). `_meta.overrides` 26 → 32; the pinned 36 is NOT reached and the 4-record shortfall is declared, not invented |
| 3 | `scripts/accept_m1.ps1` | (a) `Compare-ToolListToFixture` rewritten to take the per-endpoint expectation and compare **every** tool's name + description verbatim, plus the name set in both directions; (b) `Get-EndpointExpectation` derives editor/game from the 6 manifests + rename map and cross-checks the union against the contract count; (c) `case1`'s `tools == 2` → the derived count; (d) `guard_user_port_9877` inverted to the 9877-retired invariant; (e) `case0`/`case20` replayed; (f) `case20`'s `$ToolNames.Count` → the derived count | (a)–(d) are positively-wrong M1-era expectations with a recorded later generation on the other side; (e) is recorded text; (f) is the same stale literal as (c) | **measured**: `editor=154, game=73, implemented union=177` is what the derivation prints and what the live registry serves; the 9877 guard's `pid_before=-1 pid_after=-1` is the measured fact. The two cases replay `events-edit seq=858` (t=1790015088330, `old`→`new` = 240→3061 B) and `seq=1030` (t=1790321324515, 77→1998 B) | **none for the gate**: it went 16/20 → 19/22 → **22/22**, and no assertion was deleted — the comparison got *wider*. A declared `inputSchema` deviation is honoured only when it really differs (G-3) |
| 4 | `docs/scripts/_tmp_gen_b3_b5.py` | the stale literal `(171 entries)` and the same literal in `source.excluded` are now derived (`% len(contract_names)`) | the file is a `_tmp_` scratch generator kept as evidence; the literal is prose in a `source` dict | **measured**: the two expressions evaluated against the real contract print `177` and no scanned number remains on either line (`work/task088/verify_gen_expr.txt`, RESULT: PASS) | **none**: `check_hardcoded_counts.py` 1 unclassified line → **0**. The generator itself cannot run end to end today (its SPEC predates the six ADDED_TOOLS) — pre-existing, and the repaired lines are unit-tested directly instead |
| 5 | `scripts/mcp_trace_ledger.py` | **new**: one traceability row per tool call (id / tool / args / start+end / duration / result / capture verdict / pixel diff / declared file-side gap) | new file, nothing to replay | the field model comes from `mcp_trace.h`/`mcp_capture.h` and is stated in `docs/reports/MCP-TRACEABILITY.md` | **none**: read-only reader; not in any gate's scan path except `check_hardcoded_counts.py`, which it passes |
| 6 | `docs/reports/MCP-TRACEABILITY.md` | **new**: the traceability model, the verdict rules, the failure taxonomy, and the live-demo paths | new document | the live session of G-4 | **none**: documentation |

## G-3. The three `inputSchema` disagreements are NOT missing records

The 2c-6 section expected the pinned `_meta.overrides = 36` to be explained by 10
missing records. The measured comparison gives 10 *disagreeing tools*, but they
are not 10 missing records:

* 7 descriptions → 6 new records + 1 existing record (`play_scene`) whose value
  was an earlier revision of the same rewrite. `_meta.overrides` therefore moves
  26 → **32**, not 36.
* 3 inputSchemas (`simulate_sequence`, `find_signal_connections`,
  `get_test_report`) → the generator **already** declares all three as
  `SCHEMA_OVERRIDES`, i.e. the contract deliberately carries a schema the
  implementation does not publish. The C++ confirms it: the rich event-item
  schema of `editor_simulate_input_sequence` appears in no `.cpp`
  (`grep 可粘贴样例 tools/*.cpp` = 0 hits).

So `accept_m1`'s widened comparison excuses an `inputSchema` disagreement **only**
when the contract itself declares an override of kind `inputSchema` for that
tool, and it prints how many were honoured. Measured on the editor endpoint:
**3**, named in the evidence line. The exclusion list is read out of
`_meta.overrides`, not hand-written, so it cannot grow silently.

**Declared risk:** the contract is *richer* than the implementation for those
three tools. That is the contract's own declared deviation and was left as it
is; making the implementation publish the richer schema is the opposite
direction and is **not** done here.

## G-4. Live traceability session (item 5 evidence)

`work/task088/mcp088_live_evidence.ps1`, windowed (a headless process has no
framebuffer and every capture would be `unavailable`). Editor on 9888, game on
9889, both with `--mcp-trace` + `--mcp-capture=every_call` +
`--mcp-capture-dir` (absolute) and `--mcp-capture-viewport=2d`.

| artefact | path (under `work/task088/live/`) | measured |
|---|---|---|
| editor trace | `trace-editor.jsonl` | 10 lines |
| game trace | `trace-game.jsonl` | 7 lines |
| editor shots | `shots-editor/` | 8 PNG, 78 036 B each, 2978×1793 (full raster, `scale=1`) |
| game shots | `shots-game/` | 6 PNG, 12 266 B each |
| editor `tools/list` body | `editor-tools-list.json` | 46 810 B, 154 tools |
| ledger | `ledger-editor.txt` / `.json` | produced by `scripts/mcp_trace_ledger.py` |

## G-5. Route notes worth keeping

* **`Start-Process -Wait` waits for the descendant tree.** MSBuild keeps reuse
  nodes alive for 15 minutes after a successful build, so a *finished*
  `build_assemblies.py` looked hung (0 CPU, log not growing). It was stopped on
  that misreading and then re-run to completion (exit 0, 50.7 s). All task-088
  launchers now use `WaitForExit()` — wait for `cmd.exe` only.
* **`%ERRORLEVEL%` in one `cmd /c` line is expanded at parse time**, so every
  gate echoed `[exitcode]=0` regardless. The launchers now run `cmd /v:on /c`
  and echo `!ERRORLEVEL!`.
* **PowerShell 5.1 mangles embedded quotes in native arguments.** Passing a JSON
  string to `curl.exe --data-binary` produced `-32700 Parse error` on every
  call; the body now goes through a file (`@file`).
"""
