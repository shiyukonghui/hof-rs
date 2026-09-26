#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-103: register the module change in `REBUILT-2C-MANIFEST.md` as section 2c-12.

Append-only, written by a Python writer (iron rule 1). The section is the register
of what changed, with its basis, its shape impact and its rollback point - the 2c-10
section (`TASK-097`) is the model it follows.
"""

import io
import os
import sys

MANIFEST = r"F:\moonbit-hof-rs\godot-mcp\godot\modules\mcp_server\docs\reports\REBUILT-2C-MANIFEST.md"

SECTION = """
---

# REBUILT-2C MANIFEST — 2c-12 (TASK-103)

* Task: TASK-103 — (A) tool defect **X-1** fixed at its root: a GDScript body that
  compiles and then fails **while it runs** is a structured refusal now
  (`-32000` + `data.script_error` + `data.suggestion`) instead of an `ok` with a
  `null` result, and a successful body that returned no value carries a `note`;
  (B) the 16th and 17th C# games (Tower Defense, Missile Command), written through
  MCP calls only; (C) both variants rebuilt at the module commit, the ten gates
  green with their real exit codes, `accept_m1` 22/22, the engine repository pushed
  to the fork.
* **Module commit: `1c7f5c07a1`.** Both variants were rebuilt **at that commit**,
  so the compiled anchor is real and not a stale one:
  `4.8.dev.mono.custom_build.1c7f5c07a` / `4.8.dev.custom_build.1c7f5c07a`.
* Start HEAD: `e041cae270`.
* Method: 2c-3..2c-9 replayed recorded text because the module's own bytes had been
  lost; 2c-10 and 2c-11 registered written work. This section registers written work
  too, and therefore carries no `[REBUILT-2C low-confidence: verify]` marker.

## M-1. Written: the runtime-error contract of `running_game_execute_gdscript` (item A)

The defect (TASK-102, ledger item **X-1**; `runs/match3/m3-task102-r1/g115-runtime-overlay.json`):
the body called `main.addChild(c)` — the C# spelling of the method — on a C#
`Node2D`. GDScript compiled it (the call is dynamically dispatched), the VM aborted
the frame at that line, and `Callable::callp` answered `CallError::CALL_OK` with the
return type's default. The tool therefore answered

    {"result":null,"result_type":"Nil"}

inside an `ok`, with **no** error code, **no** message and **no** suggestion, while
the engine's stderr carried the whole
`SCRIPT ERROR: Invalid call. Nonexistent function 'addChild' in base 'Node2D (Match3Game.cs)'.`
line. The cost was measured: the next frame was byte-identical and the scene tree had
no `ProbeOverlay`, so `ok` was the only signal in the answer — and it pointed the
wrong way. X-1's whole cost was that `ok` could not be told apart from "the body
really ran and its effect is simply not visible here".

| # | file | what was written | basis | behaviour risk |
|---|---|---|---|---|
| 1 | `tools/tool_helpers.h` | `struct GDScriptRuntimeReport` (error seen / in the generated body / diagnostic / function / script path / generated line / caller line / error count / bounded messages) and `call_gdscript_capturing(const Callable &, const String &p_generated_script_path, int p_body_start_line, Variant &, Callable::CallError &)`, with the engine route, the window and the two boundaries written out | the same `add_error_handler` hook the parse capture already uses (`tool_helpers.cpp`, TASK-063 (d)); the runtime site is `modules/gdscript/gdscript_vm.cpp:3988`, so no new module-to-module dependency is created | none by itself: two declarations and a struct; the only shared-code change is one added `#include "core/variant/callable.h"` |
| 2 | `tools/tool_helpers.cpp` | the capture itself: a handler that accepts **`ERR_HANDLER_SCRIPT` only** (so a body's own deliberate `push_error()`, which is `ERR_HANDLER_ERROR`, cannot turn a successful call into a refusal), prefers the diagnostic reported **inside the generated body**, records every one of them (bounded at 12), and maps the engine's generated line back to a line of the caller's own `code` with the same `p_body_start_line` arithmetic the parse capture uses | `_err_print_error(err_func, err_file, err_line, err_text, false, ERR_HANDLER_SCRIPT)` at `gdscript_vm.cpp:3988`; the window is exactly one `Callable::callp` on the main thread, so every such error in it happened because of that call | **the intended change**: those errors stop being invisible to the caller; the engine's own printing is untouched (the handler list is walked *after* the default printing, `core/error/error_macros.cpp:125-141`) |
| 3 | `tools/running_game_script_execution.cpp` | the wiring: `runtime = MCPTools::call_gdscript_capturing(...)` on **both** execution paths (the mounted `Node` and the `RefCounted` fallback), the `-32000` refusal with `data.script_error` + `data.suggestion`, the `note` on a successful `null`/`Nil` result, the reconstructed script identity, and the contract comment in the file's header | the code `project_text_write.cpp` established for "well formed but this run failed", and GDR-14's requirement that `-32000` carries `data.suggestion` | the success shape is **unchanged** for every call that already answered a value; the null case **grows** a `note` key |
| 4 | `scripts/gen_renamed_contract.py` | the **append-only** `DESCRIPTION_OVERRIDES` entry for `execute_game_script`: TASK-090's sentence stays first, verbatim, and the runtime contract is appended after it; the `reason` records the defect, the code choice and the note | the generator's own append-only rule (v1.2) — the original wording cannot be lost, and the `mode=replace` escape hatch is not needed because nothing in the old text is false | none: a description may only say more |
| 5 | `docs/tools_list.renamed.json` | regenerated (`python scripts/gen_renamed_contract.py`), **never hand-edited** | the generator is the only writer of this file | none by itself; the C++ literal is kept in step by item 6 |
| 6 | `tools/running_game_script_execution.cpp` (generated span) | the registration literal regenerated with `python scripts/gen_b2_game_schema.py --group running_game_script_execution --in-place ...` | the literal is a byte-exact copy of the contract entry | the byte-exactness is asserted before the build by `recovery\\work\\task103\\check_literal.py` and after it by gate 4 |
| 7 | `tests/test_mcp_server.h` | one new test case pinning the three situations apart (parse failure `-32602`; runtime error `-32000` with its line mapping and every `data.script_error` key; success with a value and success without one, the latter carrying the `note`), the `push_error()` control that must **not** become a refusal, the auditable `script_path == body_script_path` comparison, and the TASK-090 mount case's failure path changed from "the documented boundary" to "the structured refusal" | the defect's own three shapes, measured on the wire | module case count 156 → 157 |

### The two decisions inside item A, and why

* **`-32000`, not `-32602` and not `-32603`.** `-32602` (`invalid_params`) means the
  *argument* was malformed; the body **compiled** — the engine accepted every line
  of it — so using it would tell a caller to fix syntax that is fine. `-32603`
  (`internal`) means *this module* is broken; the caller's code is what failed and
  the module correctly observed that it did. `-32000` (`MCP_ERR_TOOL_STATE`, GDR-14)
  is the existing convention for "the call is well formed but the state blocks it",
  it is what `not_implemented` and `no_scene` already answer, and GDR-14 requires it
  to carry `data.suggestion`. The reasoning is in the source next to the refusal, so
  the next reader does not have to reconstruct it.
* **The script identity is reconstructed, not read.** `Script::get_path()` is
  `Resource::get_path()`, which answers the **path cache** (`core/io/resource.cpp:118-120`)
  and is empty for a script that was never loaded from a resource — measured: the
  runtime error named `gdscript://-9223371484028730203.gd` while `get_path()`
  answered `""`. The path the engine really uses is `GDScript::path`, which a
  pathless `GDScript` makes out of its own instance id
  (`modules/gdscript/gdscript.cpp:1337`) and `GDScriptFunction::source` is set from
  it (`gdscript_compiler.cpp:3291`), so the module reconstructs exactly that string
  from the same object. `data.script_error` carries **both** strings
  (`script_path` and `body_script_path`), so the comparison `in_generated_body`
  makes is auditable from the answer itself.

### The two boundaries that remain, stated rather than assumed

* **No column.** The engine hands an error handler a line and never a column
  (`core/error/error_macros.h:63-77`), so `data.script_error.column` is `null` and
  the parse capture's `parse_error_column` stays `null` too. This is a property of
  the hook, not a decision that could have gone the other way.
* **A release template reports nothing.** Both VM error sites are inside
  `#ifdef DEBUG_ENABLED`, and every build this module's gates run is
  `target=editor` (`SConstruct:550/566-569`), so the hook is compiled in here. On a
  `target=template_release` build the VM prints nothing and this capture would
  answer "no error seen". That boundary is written into the tool's own comment
  rather than left for a future debugger to rediscover.

## M-2. Not changed: the editor executor

`editor_execute_gdscript` shares the source builder and the parse capture with the
game executor, but **not** this runtime capture. TASK-103's scope was the tool X-1
names (`running_game_execute_gdscript`), and the helper was hoisted into
`tool_helpers.{h,cpp}` precisely so that a later task that wants the editor half can
wire it in one line instead of writing a second copy of the rule. Registering the
boundary here is what keeps "the editor endpoint still answers the pre-TASK-103 way"
from being a surprise.

## M-3. The measured evidence of item A

* **The minimal same-batch reproduction.** One six-call session
  (`recovery\\work\\task103\\sessions\\session-x1.json`, generated by
  `make_session_x1.py`, whose failing body is the *verbatim* `args` string of
  `m3-task102-r1`'s `g115` call) was run **unchanged** twice:
  * before — `runs/match3/task103-x1-before/g01-failing-addchild.json`:
    `{"result":null,"result_type":"Nil"}` inside an `ok`, `error_code: 0`, no
    message, no `error_data_json` on the trace line; the scene tree right after it
    had no `ProbeOverlay`; the engine's stderr carried the `SCRIPT ERROR` line.
  * after — `runs/match3/task103-x1-after/g01-failing-addchild.json`: **`-32000`**
    with `data.script_error` (`message` = the engine's own text, `line` = 7 of
    `code`, `generated_line` = 10, `function` = `_mcp_execute`, `script_path` =
    `gdscript://-9223371989626911104.gd`, `in_generated_body` = true,
    `error_count` = 1, `column` = null, `messages` = the same text) and a
    `data.suggestion`; the trace call line carries `error_code: -32000`,
    `error_message` and the whole `error_data_json`.
* **The controls in the same batch.** `g03` (the same eight lines with
  `add_child`) answered `"overlay added"` **in both runs**, so the fix does not
  over-report; `g05` (a body with no `return`) answered `null` **plus the note**
  after the fix; `g06` (a body that does not parse) answered `-32602` with a
  byte-identical `parse_error` payload in both runs; and the engine's stderr still
  carries the `SCRIPT ERROR` line after the fix, because the handler is purely
  additive.
* **Doctests.** `bin\\godot.windows.editor.x86_64.mono.console.exe --headless --test
  --test-case=[MCPServer]*` → **157 cases, 157 passed, 0 failed**; the full engine
  suite → **1583 cases, 1583 passed, 0 failed** (gates 1 and 2).
* **The contract's six shape quantities are unchanged** — `count=177`,
  `added_count=6`, `generator_version=1.22.0`, editor-visible **154**,
  game-visible **73**, and **idempotent** (two consecutive generator runs both exit
  0 and leave the same bytes). The file grew 151 367 B / `64ddce9f…` →
  153 330 B / `bd68e804…` and `_meta.overrides` stayed **34**: the change is an
  existing override's text, not a new entry. Gate 4's live subset check confirms
  editor **154** / game **73** against a real editor and a real game process.

## M-4. The gates of item C, with their real exit codes

`runs\\gates\\task103\\summary.txt` (log `recovery\\work\\task103\\logs\\gates-task103.txt`),
run with `-RunGates` so the doc-only preflight could not skip them:

| gate | command | exit |
|---|---|---|
| g01 | mono binary `--headless --test --test-case=[MCPServer]*` (157/157 cases) | **0** |
| g02 | mono binary `--headless --test` (1583/1583 cases) | **0** |
| g03 | `check_tool_groups.py` (`TOOL-GROUPS CHECK PASS`, 5681 B, sha256 `b83d79d3…`) | **0** |
| g04 | `check_contract_subset.ps1` (`3/3 checks passed`; editor 154 / game 73) | **0** |
| g05 | `check_rename_map.py` (`RESULT: PASS`) | **0** |
| g06 | `check_tautologies.py` (`TAUTOLOGY CHECK PASS`, every hit pinned) | **0** |
| g07 | `check_exit_propagation.py --probes` | **0** |
| g08 | `check_hardcoded_counts.py` (116 occurrences, 0 unclassified) | **0** |
| g09 | `check_engine_anchor.ps1 -VersionText 4.8.dev.mono.custom_build.1c7f5c07a` (`ANCHOR_EQUAL`, diff_count 0) | **0** |
| g10 | `accept_m1.ps1` (`22/22 cases passed`) | **0** |

Both variants were rebuilt **before** the gates and at the module commit, so the
binary g01/g02/g04/g09/g10 ran on is the one the commit produced:
`4.8.dev.mono.custom_build.1c7f5c07a` and `4.8.dev.custom_build.1c7f5c07a`.

## M-5. Iron rules, as they were actually followed

* No shell redirection anywhere: every log in this task is written by
  `Start-Process -RedirectStandardOutput/-RedirectStandardError` (`capture.ps1`,
  `capture_ps.ps1`, `run_one.ps1`, `build_variant.ps1`, `run_engine.ps1`,
  `git_commit.ps1`, `new_game_run.ps1`), every text file by a Python writer or the
  editor tool.
* No destructive command ran: the only removal is `Remove-Item` on **named,
  absolute** paths inside `recovery\\work\\task103\\logs\\` (the per-run log files
  each helper overwrites) and the two game projects were **moved**, never deleted —
  `reset_game_project.ps1` writes a full sha256 manifest (`hash_tree.py`) before
  `Move-Item`, into `recovery\\work\\task103\\archive\\`.
* Every build and every engine start went through `cmd.exe` (`build_variant.ps1`,
  `run_one.ps1`, `run_engine.ps1`), and both variants were built **serially** (D62).
* One port pair per run, processes and ports checked before each start
  (`9949/9950`-class pairs were not reused; TASK-103 used `9958/9959` for the X-1
  pair, `9960/9961` for Tower Defense and `9962/9963` for Missile Command, with a
  `tasklist` + `netstat` sweep before each).
* Every session file was read by **both** the Python checker
  (`check_session.py`) and PowerShell 5.1 (`check_session_ps.ps1`) before a single
  engine was started.
* The project archives carry their sha256 manifests
  (`recovery\\work\\task103\\archive\\*.manifest.json`), written **before** the move.
"""


def main():
    with io.open(MANIFEST, encoding="utf-8", newline="") as handle:
        text = handle.read()
    if "2c-12 (TASK-103)" in text:
        sys.exit("FATAL: the 2c-12 section is already registered")
    if not text.endswith("\n"):
        text += "\n"
    text += SECTION
    with io.open(MANIFEST, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    print("appended the 2c-12 section to %s (%d bytes)" % (MANIFEST, len(text.encode("utf-8"))))


if __name__ == "__main__":
    main()
