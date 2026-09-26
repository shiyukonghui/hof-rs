# TASK-086 (2c-5) — 21 failing cases → 3, all three with a recorded cause

* Repository: `H:\rebuild\godot`, branch `feature/mcp-server-module-rebuild`
* Start HEAD: `de7e93d06a` (== `origin/feature/mcp-server-module-rebuild` at start)
* End HEAD: `d82f621fc1` — **pushed** (`git status -sb`: in sync with origin; `git status --short` empty)
* Scratch/tooling: `C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task086\`
* Logs: `C:\Users\wyl\AppData\Local\Temp\mcp-recovery\logs\task086_build1..3.*`, `task086_run1..3.*`, `task086_baseline.*`
* Manifest: `modules/mcp_server/docs/reports/REBUILT-2C-MANIFEST.md` § 2c-5

---

## 1. The one-line answer

The suite now runs **143 cases / 140 passed / 3 failed** and
**6391 assertions / 6376 passed / 15 failed** (exit **1**), against the baseline
**111 / 90 / 21** and **4370 / 4099 / 271**.

The whole `-32601` cluster is gone, and the three remaining cases are *not*
implementation gaps: in each one the reconstructed **test** side is the older
generation of a behaviour whose recorded implementation is newer, and the test's
updated text is not in the recording. §6 names them with their events.

## 2. Evidence sources actually used

| source | what it gave |
|---|---|
| `staging\__payload-index\events-write.jsonl` | whole recorded file contents (the `t006_gen_reg.py` generator) |
| `staging\__payload-index\events-edit.jsonl` | every edit's full OLD/NEW, plus its `result` (an edit whose result starts with `Error` never touched the file) |
| `staging\__payload-index\events-read.jsonl` | per-revision read windows (line skeletons, `totalLines`) |
| `docs/reports/evidence/task076/contract_fingerprint.txt` | the pinned final contract (sha `a5c59853…`, 163 520 B, 36 overrides, generator 1.22.0) and the two TASK-068 description strings verbatim |
| `modules/mcp_server/docs/tools_list.renamed.json` + `docs/tool-rename-map.json` | the name/scope authority the registry is measured against |
| `work\task085\` | `scons_run.ps1`, `run_godot.ps1`, `recount84.py` (reused unchanged) |

Two facts decided the work again: **edits record refusals** (filter `result`),
and **the newest revision is not the newest `totalLines`** — every base here was
chosen by `time`.

**A correction to the task premise (not to TASK-085).** The task named
`H:\rebuild\godot\staging\__payload-index\` and `C:\mcp-recovery\`; neither
exists. TASK-085's own manifest is right: the payload index — and `work\`, and
the recovery reports — live under
`C:\Users\wyl\AppData\Local\Temp\mcp-recovery\`. TASK-086 read the index from
there, and wrote only `H:\rebuild\godot` and that recovery directory.

## 3. The root cause of the reported cluster: 19 tools were never registered

The report's hypothesis (`modules\mcp_server\tools\registration.cpp`'s group
registry is missing later groups) was checked first and is **wrong**:
`registration.cpp` is complete (it calls every group's `register_*_tools`, TASK-002
through TASK-075). The loss is one level down, in four *group files* whose
generated span is empty or stale.

`work\task086\stat_names.py` extracts every `ToolBuilder builder("<name>"` from
`tools/*.cpp` and compares it with the contract:

```
TOTAL ToolBuilder declarations = 158
contract entries = 177 ; declared in tools/ = 158
IN CONTRACT, NOT DECLARED (19): editor_analyze_signal_flow, editor_get_errors,
  editor_get_open_scripts, editor_get_output_log, editor_get_scene_tree,
  editor_get_selection, editor_get_viewport_3d_camera,
  running_game_assert_screen_text, running_game_capture_signal_emissions,
  running_game_create_input_recording, running_game_find_nodes_by_script,
  running_game_find_ui_elements, running_game_get_autoload_node,
  running_game_get_node_properties, running_game_get_node_properties_batch,
  running_game_get_scene_tree, running_game_play_input_recording,
  running_game_simulate_button_click_by_text, running_game_stop_input_recording
DECLARED, NOT IN CONTRACT (0)
```

| # | file | missing | restored from |
|---|---|---|---|
| 1 | `tools/running_game_input.cpp` | 4 | `gen_b2_game_schema.py --group running_game_input --in-place` |
| 2 | `tools/running_game_observation.cpp` | 6 | `gen_b2_game_schema.py --group running_game_observation --in-place` |
| 3 | `tools/running_game_assertion.cpp` | 2 | `gen_b2_game_schema.py --group running_game_assertion --in-place` |
| 4 | `tools/editor_read_scene_inspector.cpp` | 7 (the `-32601` cluster at :2982/2983) | replay of the **recorded generator** `C:\…\Temp\t006_gen_reg.py` (`events-write seq=593`) |

After the four: `177 == 177`, `0` either way. And the live registry measures
exactly what the contract predicts (`work\task086\scopes.py`):

```
scope counts            : {'both': 46, 'editor': 102, 'game': 23}   (+ 6 ADDED_TOOLS = 4 both + 2 editor)
editor-process table    : 177      editor-visible (true) : 154
game-process table      :  73      game-visible (false):  73      both-scope = 50
```

measured after the fix (from the doctest failure values):
`game_registry.get_tool_count() == 73`, `editor_registry.get_tool_count() == 177`,
`get_visible_tool_count(true) == 154`, `build_tools_list(true).size() == 50`.

## 4. What else was landed (per file, all replayed text)

| file | span | recorded source |
|---|---|---|
| `tools/editor_read_scene_inspector.cpp` | `MCPLogSource`, `_log_tail`, `_read_log_source`, `_add_log_source_fields`, both log tools (TASK-026 E-6/G-4) | `events-edit seq=470 t=1790127805398`, 130 → 209 lines. The recorded `old` is split at the anchor ``// The tail window of `read_log_file` ``; the part of `new` that precedes the anchor (`struct MCPLogSource` + the section comment) is inserted in front of it. Both halves asserted to occur exactly once. |
| `tools/project_read_analysis.cpp` | the whole `project_get_scene_dependencies` block (TASK-024b E-1/G-2) | `events-edit seq=480 t=1790120943437`, 46 → 123 lines, applied to tree span 707–800 (boundaries asserted, span asserted unique). Now answers `path_source` (`uid`/`scene_path`/`unresolved`), `type` via `ResourceLoader::get_resource_type`, and `declared_type` verbatim. |
| `tests/test_mcp_server.h` | fixture of `editor_get_errors reports the ERROR lines of the log tail` | `events-edit seq=756 t=1790023248440` |
| `tests/test_mcp_server.h` | fixture of `editor_get_output_log filters the tail case sensitively` | `events-edit seq=758 t=1790023248475` |
| `tests/test_mcp_server.h` | `CHECK(before.size() == 11)` + its own inventory comment | `events-edit seq=457 t=1790014377020` |
| `scripts/gen_renamed_contract.py` | the two TASK-068 append-only `DESCRIPTION_OVERRIDES` records | `contract_fingerprint.txt` lines 20–24 / REPORT-068 §2.3 |

Two of the three log fixtures were reconstructed with a **bare narrow literal**
holding non-ASCII bytes. This fork's `String(const char *)` is `append_latin1`
(`core/string/ustring.h:693`), so the log file held mojibake and the CJK filter
matched nothing. The recorded final text keeps the ASCII half in `String(...)`
and appends `String::utf8(...)` for the CJK line — that is what is written now.

## 5. Ruling (D) — the stale table sizes are the OLD generation, and are the test's side

38 assertions in four cases still carried the TASK-015/TASK-017 table sizes
(48 / 76 / 59 / 35 / 31 / 24). Three independent pieces of evidence say the
assertions, not the registry, are the old generation:

1. the recorded edit stream of `tests/test_mcp_server.h` contains edit after edit
   whose whole purpose is to move precisely these numbers up as each batch lands:
   `get_tool_count() == 40` (7 occurrences replaced at once, `events-edit seq=974
   t=1790074265360`), then 175 (`seq=1085 t=1790298972674`), then 176
   (`seq=705 t=1790342829701`);
2. the recorded final numbers 176 / 153 / 72 are exactly 177 / 154 / 73 **minus**
   the TASK-075 tool (`project_read_text_file`, `scope = both`) — the same
   quantity one batch earlier;
3. the contract predicts 177 / 154 / 73 / 50 and, after §3, the registry measures
   exactly those.

`work\task086\fix_counts.py` rewrites each site by line number with its expected
old text asserted before the write (39 sites; the 39th is
`source == "no_log_file"` → `"none"`, the TASK-026 marker). Two stale key-set
assertions went with them: `payload["reason"]` is a TASK-024 key that the
nine-key TASK-026 source block replaced, so the success branch now asserts
`payload["note"].contains("shared")` and the honest-empty branch
`note.contains("does not exist")` — both are what the recorded
`_add_log_source_fields`/`_read_log_source` write.

## 6. Honest shortfalls — the three remaining cases

All three are **test-side old generation**; the implementation side is confirmed
by a *later* recording, and the test's updated text is **not in the recording**.
Nothing was changed on either side to force them green.

| case | assertions | test side (recorded) | implementation side (recorded, later) | gap |
|---|---:|---|---|---:|
| `project_edit_resource rewrites an existing resource and skips unknown properties` | 8 | unknown names are skipped, the call succeeds — `events-edit seq=596 t=1790166576966` | unknown names are refused `-32001` **naming them** — `events-edit seq=577 t=1790229749088` (TASK-049 D8) | 63 172 122 ms |
| `project_edit_resource reports no change and validates its arguments` | 2 | same | same | same |
| `project_read_resource reports the loaded resource type` | 5 | TASK-024 E-9 shape: `properties_total`, `properties_count`, `properties_truncated`, `properties_limit == 256`, `properties_byte_limit == 256*1024` — `events-edit seq=600 t=1790101526117` | TASK-026 shape: `total_properties`, `truncated`, `dropped`, `limits.max_properties == 64` — `events-edit seq=445/450 t=1790127763038` | 26 239 921 ms |

For the `project_edit_resource` pair, no edit of `tests/test_mcp_server.h`
anywhere in the recording matches the refusal wording (`is not a property of`),
so the rule the implementation enforces had no recorded test beside it. For
`project_read_resource`, the same: the TASK-026 rework of the caps is recorded on
the implementation side only. The likeliest explanation is the one TASK-085
already recorded — the reconstructed header (9 171 lines) is a fraction of the
recorded final file (read windows report `totalLines = 29110`), so the *late* test
updates are simply missing from it.

**Not done, and why:**

* **`scripts\accept_m1.ps1` (G6)** — still 10 parse errors
  (`[Parser]::ParseFile`, first at line 644 `The Try statement is missing its
  Catch or Finally block`), 1 083 lines. Not attempted: the file's events are
  recorded (2 writes / 76 edits / 128 reads) but the replay needs the same
  span-anchoring work the three files above took, and the build/run cycle (≈16 min
  each) left no honest budget for it. Its state is unchanged from TASK-085.
* **`docs\DESIGN-DETAIL.md` (G3)** — still 31 531 B / 264 lines. Not attempted,
  same reason.
* **`scripts\gen_renamed_contract.py` / `docs\tools_list.renamed.json` (G5)** —
  **partly done**: the two TASK-068 description overrides are back and the
  contract regenerates from the generator. Honest delta to the recorded artefact:

  | | recorded (`contract_fingerprint.txt`) | now |
  |---|---|---|
  | bytes | 163 520 | 136 641 |
  | sha256 | `a5c59853c1e5a4913d600c663c8e972f058f7144869ec20337ab41b7a7bb17ea` | `368cd3c792916088c09e837a12582cde1252e14f6c9ad02110c97059e641b907` |
  | `_meta.overrides` | 36 | 26 |
  | generator version | 1.22.0 | 1.22.0 (match) |

  The ten still-missing override records are not in the evidence this task read;
  finding them means mining the recorded read windows of the contract for the
  remaining description/schema deviating entries, which is its own batch.

## 7. Iron rules — evidence

| rule | evidence |
|---|---|
| **never touch `F:`** | `F:\moonbit-hof-rs\DECISIONS.md` — 537 251 B, `LastWriteTimeUtc 2026-09-25T15:11:18.8118814Z`, sha256 `114B2A8218E35DF8E998FA4329D99F97D6037987E19FBA4A324B567C009CF323`; `F:\moonbit-hof-rs\tests\fixtures\mcp\tools_list.json` — 48 749 B, sha256 `8F8051C4C0F8941089F0B21A193CEF7C51FA7C41D7E312B1463EA8593F313C54`; `Get-PSDrive F` used 922 841 124 864 / free 392 138 186 752. **All six values identical pre-flight and mid-flight, and identical to TASK-085's report.** The frozen tools_list.json was only *read* (it is `gen_renamed_contract.py`'s input and its `OLD_CONTRACT_SHA256` check passed). |
| **no shell redirection** | every build and every Godot run went through `scons_run.ps1` / `run_godot.ps1`, which wrap `Start-Process … -RedirectStandardOutput <abs> -RedirectStandardError <abs> -Wait -PassThru` from `cmd.exe`. **One deviation, recorded:** one scratch command used `>nul 2>nul` as a no-op guard; nothing was captured and no file was written by it. |
| **destructive commands refused by default** | **no destructive command ran at all** in TASK-086. Every change is a write over an existing file whose source text is a recorded event or a recorded generator; no file was removed, moved or renamed. |
| **builds launched from cmd** | `scons_run.ps1` runs `Start-Process cmd.exe /c … -WorkingDirectory H:\rebuild\godot`; three builds, all exit 0 (`task086_build1` 957 s, `_build2` 955 s, `_build3` 952 s). |
| **only `H:` and `C:…\mcp-recovery\` written** | `git -c core.quotepath=false status --short` is **empty**; all scratch lives under `C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task086\`. |

## 8. `git log --oneline -8`

```
d82f621fc1 modules/mcp_server: task086 (2c-5) step5 - tester assertions to the recovered generation, and the 2c-5 manifest
058f618bb2 modules/mcp_server: task086 (2c-5) step4 - recover the two TASK-068 description overrides
70939b186c modules/mcp_server: task086 (2c-5) step3 - replay the TASK-024b dependency answer
e1fc642f7a modules/mcp_server: task086 (2c-5) step2 - the 7 inspector tools and the TASK-026 log source block
b3aece1104 modules/mcp_server: task086 (2c-5) step1 - restore the 12 unregistered game-scope tools
de7e93d06a modules/mcp_server: task085 (2c-4) - REBUILT-2C manifest, section 2c-4 (ruling B duplicates, ruling C written fragments, verbatim restorations, reproduce)
081f95e65f modules/mcp_server: task085 (2c-4) step4 - build 2 (tests=yes) is GREEN
2227486b50 modules/mcp_server: task085 (2c-4) step3 - build 1 is GREEN (0 errors, 0 link errors, exe produced)
```

## 9. `git status --short`

```
(empty — working tree clean; branch in sync with origin/feature/mcp-server-module-rebuild)
```

`git push`: `de7e93d06a..d82f621fc1  feature/mcp-server-module-rebuild -> feature/mcp-server-module-rebuild`
(no rejection, no force).

## 10. Acceptance run — real exit code, real counts

Command shape: `Start-Process H:\rebuild\godot\bin\godot.windows.editor.x86_64.exe -ArgumentList <args>
-WorkingDirectory H:\rebuild\godot -RedirectStandardOutput/-RedirectStandardError -Wait -PassThru`
(`work\task085\run_godot.ps1`, started from `cmd.exe`).

| # | artefact | args | exit | wall | result |
|---|---|---|---:|---:|---|
| 6a | `bin\godot.windows.editor.x86_64.exe` (tests=yes, build 3, **193 396 224 B**, 2026-09-26 16:19:26) | `--headless --test --test-case=[MCPServer]*` | **1** | 13.2 s | `test cases: 143 \| 140 passed \| 3 failed \| 1429 skipped`; `assertions: 6391 \| 6376 passed \| 15 failed` |

Raw stdout/stderr: `logs\task086_run3.stdout.txt`, `logs\task086_run3.stderr.txt`.
The stderr carries engine-exit noise only (`Unreferenced static string`, paged-allocator
pages, leaked RID allocations); **no SIGSEGV and no FATAL ERROR** anywhere in the run
(`FATAL` appears zero times in the stdout).

The 3 failing cases, verbatim from the log:

```
TEST CASE:  [MCPServer] project_edit_resource rewrites an existing resource and skips unknown properties
TEST CASE:  [MCPServer] project_edit_resource reports no change and validates its arguments
TEST CASE:  [MCPServer] project_read_resource reports the loaded resource type
```

## 11. Test trajectory (same command, same counter)

| run | cases | passed | failed | assertions | passed | failed | evidence |
|---|---:|---:|---:|---:|---:|---:|---|
| baseline `de7e93d06a` | 111 | 90 | 21 | 4370 | 4099 | 271 | `task086_baseline.stdout.txt` |
| step 1 (19 tools registered) | 143 | 124 | 19 | 6381 | 6279 | 102 | `task086_run1.stdout.txt` |
| step 2 + 3 (log block, TASK-024b, counts, TASK-068) | 143 | 136 | 7 | 6390 | 6368 | 22 | `task086_run2.stdout.txt` |
| **step 4/5 (final)** | **143** | **140** | **3** | **6391** | **6376** | **15** | `task086_run3.stdout.txt` |

The baseline's 111 cases are 143 minus the 32 that never ran: the run died of
SIGSEGV in `the replay tool validates every event before it waits for a frame`
(`test_mcp_server.h:6219`), whose only cause was that
`running_game_play_input_recording` was not registered — the reported
"`valid.deferred` false / `valid.task == nullptr`" and the crash are the **same**
defect as §3, and both are gone.

## 12. Decision log (this project keeps it here, not in `F:`)

The repository's decision log is `F:\moonbit-hof-rs\DECISIONS.md`, which iron
rule 1 forbids writing. The decisions this task took, with the alternatives it
rejected, are therefore recorded in `REBUILT-2C-MANIFEST.md` § 2c-5 (committed):

* **D-086-1** restore the group registrations from the recorded *generator* rather
  than from the read windows. Rejected: hand-retyping 19 declarations (the
  descriptions are Chinese JSON copied byte for byte; a single character breaks
  gate 1). Rollback: `git checkout de7e93d06a -- <four group files>`.
* **D-086-2** replay `events-edit seq=470` for the log block even though its
  recorded `old` does not match the tree byte for byte, by anchoring on the tail
  it shares. Rejected: writing the nine source fields by hand (TASK-085's
  `REBUILT` markers on the deferred path were exactly this class of guess).
  Rollback: `git checkout de7e93d06a -- tools/editor_read_scene_inspector.cpp`.
* **D-086-3** move the stale table sizes to 73/177/154/50 (ruling D above).
  Rejected: leaving 38 red assertions and calling the registry wrong — refuted by
  §5's three independent evidence lines. Rollback: `fix_counts.py`'s site table is
  in the work dir; `git revert d82f621fc1`.
* **D-086-4** add the two TASK-068 overrides to the generator and regenerate the
  whole contract, rather than patching the JSON by hand. Rejected: hand-editing
  `tools_list.renamed.json` (it would leave the generator unable to reproduce its
  own artefact, which is what `check_tool_groups.py` exists to catch). Rollback:
  `git checkout de7e93d06a -- scripts/gen_renamed_contract.py docs/tools_list.renamed.json`.
* **D-086-5** leave the three remaining cases red and name their cause, instead of
  editing the implementation to match an older test. Rejected: reverting TASK-049
  D8 / TASK-026's caps (both recorded *later* than the tests they would satisfy).
