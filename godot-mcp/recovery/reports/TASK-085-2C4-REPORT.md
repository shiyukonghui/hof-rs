# TASK-085 (2c-4) — event-log recovery to a green compile and the first runnable exe

* Repository: `H:\rebuild\godot`, branch `feature/mcp-server-module-rebuild`
* Start HEAD: `a26cf4fd83` (== `origin/feature/mcp-server-module-rebuild` at start)
* End HEAD: `de7e93d06a`, **pushed** (`git status -sb`: branch in sync with origin)
* Scratch/tooling: `C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task085\`
* Logs: `C:\Users\wyl\AppData\Local\Temp\mcp-recovery\logs\task085_*`
* Manifest: `modules/mcp_server/docs/reports/REBUILT-2C-MANIFEST.md` § 2c-4

---

## 1. The one-line answer

The module now **compiles with 0 errors** and the editor links: `scons platform=windows
target=editor tests=no -j8 -k` → **exit 0**, `bin\godot.windows.editor.x86_64.exe` (179 007 488 B).
With `tests=yes -j8 -k` → **exit 0** (exe 193 225 216 B).

The exe **runs**: `--version` → exit 0, `4.8.dev.custom_build.2227486b5`.

The test suite **runs but does not pass**: `[doctest] test cases: 111 | 90 passed | 21 failed |
1461 skipped`, `assertions: 4370 | 4099 passed | 271 failed`, exit **1**, one case SIGSEGV.

## 2. Error trajectory (same counter, `recount84.py`)

| step | build | error lines | files |
|---|---|---:|---:|
| TASK-084 end | `tests=no` | 191 | 10 |
| after `tool_registry.cpp` replay | `tests=no` | 160 | 9 |
| step 1 commit `9b28eacb72` | `tests=no` | 37 | 3 |
| step 2 commit `f7a20136e1` | `tests=no` | **0** | 0 (5 undefined symbols at link) |
| step 3 commit `2227486b50` | `tests=no` | **0** | **exit 0** |
| first `tests=yes` | `tests=yes` | 80 | 1 |
| step 4 commit `081f95e65f` | `tests=yes` | **0** | **exit 0** |

Raw logs: `task085_build_r1..r12.*`, `task085_build_tests..tests7.*`.

## 3. Method (unchanged from TASK-084, extended)

`events-read.jsonl` gives absolute-line windows; `events-write.jsonl` gives whole recorded files;
`events-edit.jsonl` gives every edit's full OLD/NEW. Two facts decided the work:

* **Edits record failures too.** `result` starting with `The file ... has been updated` means
  applied; anything starting with `Error:` was refused (file not read, `old_string` not found,
  matched N times, `ReplaceFileW EIO`). Filtering the failures removed every phantom "break".
* **The newest revision is not the newest `totalLines`.** For `editor_write_scene_editor.cpp`
  rev1184 is an *early* revision; the real target is rev1099 (latest by `time`). All bases here
  were chosen by `time`, not by line count.

## 4. What was landed (per file)

Restored **verbatim** from recordings (detail in the manifest § 2c-4):

* `tool_registry.cpp` — strict replay, 914 lines, 0 break points, braces balanced.
* `tools/running_game_frame_observation.cpp` (735 = rev735), `tools/running_game_node_write.cpp`
  (1281 = rev1281), `tools/running_game_test_execution.cpp` (949 = rev949) — exact target lengths.
* `tools/project_write_resource_scene.cpp` — `_tool_create_scene_file` (rev697 379–459),
  `_tool_delete_scene_file` (rev775 446–490), `_property_table` +
  `MCPTools::resource_bag_name_is_addressable` (replay), the `_require_properties` forward
  declaration.
* `tools/editor_write_scene_editor.cpp` — the `_tool_set_viewport_3d_camera` body (rev1088 +
  rev1046, anchor-aligned).
* `tools/editor_node_write.cpp` — 6 call sites to the hoisted helper spellings.
* `tools/project_validate_scripts.cpp` — `_is_script_extension` body, single registration.
* `mcp_jsonrpc.cpp` — `_immediate`, `_tag`, `_effective_timeout`, `_dispatch_tools_call`,
  `handle`, `dispatch`, `build_result_raw`, `build_error_raw`.
* `tools/tool_helpers.cpp` — `schema_with_integer_defaults` re-inserted.
* `tools/project.cpp` / `tools/project.h` — **deleted** through the guarded `remove_legacy.py`
  (absolute paths, sha256 pre-check, manifest printed first). Dead pre-TASK-002-B1 unit: both tools
  live in `project_read_template.cpp`, `register_project_tools` is called from nowhere, and the
  handlers use the removed `String &` signature plus the now-private `register_tool`.

Written fragments — each marked `// [REBUILT-2C low-confidence: verify]` and registered in the
manifest: the 13 lines closing `_write_resource_properties`'s `is_label == nullptr` branch, the
10-line `MCPTools::write_resource_properties` adapter, `return schema;` closing
`schema_with_integer_defaults`, `dispatch`'s `p_trace` plumbing (8 `_tag` wraps), and the 13-line
hole in `_dispatch_tools_call`.

## 5. Ruling (B) — duplicates, later generation kept

| file | discarded | kept |
|---|---|---|
| `tools/tool_helpers.cpp` | gen-0 `VECTOR4`/`VECTOR4I` at 171–193 and gen-2 `PACKED_*` at 390–515 | the generation now at 254–320 (`events-edit seq=853`, rev2487 t=1790147836781 lines 184–213) |
| `tools/running_game_node_write.cpp` | the earlier `_node_path_for_result` | the later one |
| `tests/test_mcp_server.h` | 9133–9487 — the five `editor_read_scene_inspector` TEST_CASEs at 19/26 tools | 2941–3583 — the same five at 48/76 tools, the counts the current registration produces |

## 6. Runtime evidence (real exit codes, real counts)

Command shape: `Start-Process H:\rebuild\godot\bin\godot.windows.editor.x86_64.exe -ArgumentList <args>
-WorkingDirectory H:\rebuild\godot -RedirectStandardOutput/-RedirectStandardError -Wait -PassThru`.

| # | artifact | args | exit | wall | result |
|---|---|---|---:|---:|---|
| 5a | `bin\godot.windows.editor.x86_64.exe` (2227486b5, 179 007 488 B) | `--version` | **0** | 1.1 s | stderr: `4.8.dev.custom_build.2227486b5` |
| 5b | `bin\godot.windows.editor.x86_64.exe` (081f95e65f, 193 225 216 B) | `--headless --test --test-case=[MCPServer]*` | **1** | 5.1 s | 111 cases / 90 passed / **21 failed** / 1461 skipped; 4370 assertions / 4099 passed / **271 failed** |

`bin\godot.windows.editor.x86_64.console.exe` also exists (300 544 B).

**The 21 failing cases** (doctest prints the name of each failing case):

```
the shared registration entry point registers the group
tools of later batches are not registered
tools/list is byte-identical across consecutive calls
the project_read_analysis group is registered for both processes
TASK-024b E-1/G-2: a uid-bearing ext_resource keeps its type and its res:// path
the analysis tools never write to the project
the editor_read_scene_inspector group is editor-only
editor_get_errors reports the ERROR lines of the log tail
editor_get_output_log filters the tail case sensitively
the log tools declare their source and their process, and answer honestly when nothing is readable
the editor UI inspectors refuse cleanly without an editor UI
the edited-scene inspectors need an open scene and validate their arguments
the project_write_resource_scene tools are registered as mutating both-scope tools
project_edit_resource rewrites an existing resource and skips unknown properties
project_edit_resource reports no change and validates its arguments
the editor_write_scene_editor group is editor-only and complete
the running_game_read_scene group is game-only
the running_game_observation group is game-only and complete
the running_game_observation tools validate their arguments and need a running game
the TASK-012 game groups are game-only and the editor groups are editor-only
the replay tool validates every event before it waits for a frame
```

Failure character, from the log (`test_mcp_server.h`):

* 156 distinct failing assertion sites, 271 failing assertions.
* The two biggest clusters are `test_mcp_server.h:6241/6242` (×17 each —
  `CHECK((int)error["code"] == -32602)` sees **-32601**) and `:2982/2983` (×7 each).
  `-32601` = `METHOD_NOT_FOUND`, i.e. the tool the test names is not in the table: several groups
  the third-generation registry should carry are still absent or carry the earlier table size.
* `:6278 CHECK(valid.deferred)` and `:6279 REQUIRE(valid.task != nullptr)` — the deferred channel
  returns no task.
* `:6219 FATAL ERROR: test case CRASHED: SIGSEGV` — one case crashes.
* stderr carries engine-exit noise only (`Unreferenced static string`, `PagedAllocator` pages,
  leaked RID allocations), which the crash explains.

## 7. Iron rules — evidence

| rule | evidence |
|---|---|
| **never touch `F:`** | `F:\moonbit-hof-rs\DECISIONS.md` — 537 251 B, `LastWriteTimeUtc 2026-09-25T15:11:18.8118814Z`, sha256 `114B2A8218E35DF8E998FA4329D99F97D6037987E19FBA4A324B567C009CF323`; `Get-PSDrive F` used 922 841 124 864 / free 392 138 186 752 — **all four identical to the pre-flight values** |
| **no shell redirection** | every build and every Godot run used `scons_run.ps1` / `run_godot.ps1`, which wrap `Start-Process … -RedirectStandardOutput <abs> -RedirectStandardError <abs> -Wait -PassThru` from `cmd.exe` |
| **destructive commands refused by default** | the only deletion (`tools/project.cpp`, `tools/project.h`) went through `remove_legacy.py`: absolute paths, sha256 pinned pre-flight (`59edd2481de80cee…`, `24e9afbf1019910f…`), manifest printed before the unlink, `throw` on wildcard or `..` |
| **builds launched from cmd** | `scons_run.ps1` runs `Start-Process cmd.exe /c … -WorkingDirectory H:\rebuild\godot` |
| **only `H:` and `C:…\mcp-recovery\` written** | `git -c core.quotepath=false status --short` is **empty**; all scratch lives under `work\task085\` |

## 8. `git log --oneline -8`

```
de7e93d06a modules/mcp_server: task085 (2c-4) - REBUILT-2C manifest, section 2c-4 (ruling B duplicates, ruling C written fragments, verbatim restorations, reproduce)
081f95e65f modules/mcp_server: task085 (2c-4) step4 - build 2 (tests=yes) is GREEN
2227486b50 modules/mcp_server: task085 (2c-4) step3 - build 1 is GREEN (0 errors, 0 link errors, exe produced)
f7a20136e1 modules/mcp_server: task085 (2c-4) step2 - compilation green; 37 -> 0 compile errors
9b28eacb72 modules/mcp_server: task085 (2c-4) step1 - replay the recorded write+edit chain; 191 -> 37 error lines, 10 -> 3 files
a26cf4fd83 modules/mcp_server: task084 (2c-3) - restore the recorded TASK-051/TASK-063 blocks and align hoisted call sites; 444 -> 191 error lines, 20 -> 10 files
be6aa88c8c modules/mcp_server: task083 build evidence - 1357 -> 448 error lines, 43 -> 21 files; module still RED
a9208962fb modules/mcp_server: task083 - reconcile the three stale call sites in editor_animation_tree_write.cpp
```

## 9. `git status --short`

```
(empty — working tree clean; branch in sync with origin/feature/mcp-server-module-rebuild)
```

## 10. Honest shortfalls

* **Tests do not pass.** 21 of 111 cases fail and one crashes. Every failing case is a *behaviour*
  gap, not a compile gap: the recordings for the third-generation registry and the deferred
  channel are incomplete, so several groups are registered with the earlier table and `-32601`
  replaces the expected refusals. This is exactly the class of loss TASK-083/084 reported as
  "content that exists in no recorded write or edit".
* Line-count deltas against the newest recorded revision remain, and are *not* all repair-able
  from the log: `project_write_resource_scene.cpp` 836 vs rev852, `editor_write_scene_editor.cpp`
  1081 vs rev1099, `tool_helpers.cpp` 3480 vs rev3479.
* Five fragments were **written**, not replayed. They are marked in code and listed in § 4 /
  the manifest. Two of them (`dispatch`'s trace plumbing, the `_dispatch_tools_call` 13-line hole)
  sit on the deferred path that the failing tests exercise — they are the first places to look if
  the deferred-channel failures are to be explained.
* `tests/test_mcp_server.h` is 9 164 lines after dropping the earlier duplicate block; the recorded
  newest revision is larger, so the header still has unrecovered content.
