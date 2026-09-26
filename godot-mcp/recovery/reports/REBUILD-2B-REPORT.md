# REBUILD-2B-REPORT — TASK-080

Stage 2b on `C:\Users\wyl\AppData\Local\Temp\mcp-recovery\rebuild\godot\`.
Patch replay + contract regeneration + the two named hard gaps.  No scons, no module semantics.
All writes under `C:\Users\wyl\AppData\Local\Temp\mcp-recovery\`; **zero writes to F:**; no shell
redirection anywhere (only `Set-Content` / `[IO.File]::WriteAll*` / Python `open(...,'wb')`).
Raw run logs: `rebuild\work2b\patch-run.txt`, `gen-runs-2b.txt`, `parse-ps1-2b.json`,
`parse-py-2b.json`, `parse_py_run.py`, `sweep.py` output.

---

## 0. Safety compliance

| rule | evidence |
|---|---|
| no writes to F: | pre-state and post-state `Get-ChildItem F:\moonbit-hof-rs` identical (same 16 entries, same lengths incl. `DECISIONS.md` 537,251 B, `Cargo.lock` 53,741 B); `F:\RustProjects\godot-mcp-pro\code\godot` still `children=0`, `LastWriteTimeUtc=09/25/2026 15:19:49` (unchanged); `Get-PSDrive F` Used=922,772,578,304 / Free=392,206,733,312 both times; the only F: access was `Get-FileHash` / `Get-Content` (read-only) on `tests\fixtures\mcp\tools_list.json`, re-hashed at the end as `8f8051c4c0f8941089f0b21a193cef7c51fa7c41d7e312b1463ea8593f313c54` |
| no shell redirection | patch run used `git apply` directly; all logs via `[IO.File]::WriteAllLines`; generator stdout captured with `2>&1 \| Where-Object` **inside** a pipeline (no redirection operator to a file) — file writes are Python `open(...,'wb')` / `[IO.File]::WriteAllText` |
| destructive-command gate | exactly one deletion was issued in this run: `Remove-Item -Recurse -Force` on the probe sandbox `C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\gitapply-probe`, whose target was a literal non-empty absolute path under the allowed root, printed in the same command, holding **copies** only (it was re-created from `rebuild\godot` in the same command). No wildcard / `..` / empty target was ever formed. No file in `rebuild\godot` was deleted; the three files replaced in the tree were copied aside first (§5). All other writes were `Set-Content` / `Out-File`-equivalent / `[IO.File]::WriteAll*` / Python `open(...,'wb')` |

## 1. ① Engine patches — applied for real, 0 / 0 / 0

Commands (verbatim, from `rebuild\godot`):

```
git -C <godot> apply -p1 --whitespace=nowarn --check  rebuild\patches\patch1-...diff   -> exit 0
git -C <godot> apply -p1 --whitespace=nowarn --check  rebuild\patches\patch2-...diff   -> exit 0
git -C <godot> apply -p1 --whitespace=nowarn --check  rebuild\patches\patch3-...diff   -> exit 1  (EXPECTED)
git -C <godot> apply -p1 --whitespace=nowarn          rebuild\patches\patch1-...diff   -> exit 0
git -C <godot> apply -p1 --whitespace=nowarn          rebuild\patches\patch2-...diff   -> exit 0
git -C <godot> apply -p1 --whitespace=nowarn          rebuild\patches\patch3-...diff   -> exit 0
```

`--check` on patch 3 fails **only** because its context carries patch 2's
`save_custom_section()` (the same expected failure recorded in
`ENGINE-PATCHES-TO-REAPPLY.md` §5 row 3):

```
error: patch failed: core/config/project_settings.cpp:1679
error: core/config/project_settings.cpp: patch does not apply
error: patch failed: core/config/project_settings.h:136
error: core/config/project_settings.h: patch does not apply
```

Patch artifact hashes re-verified against `rebuild\patches\SHA256SUMS.txt`:

| patch | bytes | sha256 |
|---|---:|---|
| 1 `5f3e7fb441` | 5,303 | `6b0ee95c2abde614a4ec0ed2e6e4b7eb00ee39a75ebddf3906737d43cda02353` |
| 2 `96f631addb` | 23,683 | `70decff99a232fd5866f37cd8bd952ffa40afee8801d2bfc1eaa4b5be46b4c4c` |
| 3 `2f85141a74` | 20,309 | `41867b2962fce8c764da13fe9812c8c67a2bba22c16be5923c0c53206a5fae7e` |

### 1.1 Post-state vs the recorded "after patch3" values — **all five match byte for byte**

| file | post bytes | post sha256 | recorded bytes / sha256 (§5 of the patch doc) | match |
|---|---:|---|---|---|
| `core/config/project_settings.cpp` | 102,533 | `e9c4f6fb143afcdd63939574e0067a4aff929ff47d2893b996da218415d05f68` | 102,533 / `e9c4f6fb…d05f68` | **yes** |
| `core/config/project_settings.h` | 19,002 | `b8491ca81d1a8f8cdb986325812948e74406904614a0503704184452e19b7d79` | 19,002 / `b8491ca8…9b7d79` | **yes** |
| `editor/editor_node.cpp` | 400,247 | `699bfc817f99ce25cd45678cb3213dea203b49e1a85c4f4f54f7d1b597647ec8` | 400,247 / `699bfc81…647ec8` | **yes** |
| `modules/mono/csharp_script.cpp` | 89,504 | `7fef858f8f51a177390f1a878591a4567943ce2b78965b599e47b04b85975eb8` | 89,504 / `7fef858f…975eb8` | **yes** |
| `modules/mono/csharp_script.h` | 22,687 | `499bdbc4e2e8340125bc88e79065826da5753ee07da7070bf4ba58952ae16f0b` | 22,687 / `499bdbc4…ae16f0b` | **yes** |

The pre-image was also verified before touching anything: all five pristine shas equal the
`REBUILD-2A-MANIFEST.md` §2 baseline column (e.g. `project_settings.cpp` 75,556 B /
`c76f85ac…f745886c`), confirming the tree was still the pre-patch upstream state.

### 1.2 Symbols really appeared (§6 criterion)

Plain substring counts, measured on the patched tree:

| file | `is_source_newer_than_assembly` | `update_settings_section_text` | `save_custom_section` | `save_preserving_text` | §6 expects |
|---|---:|---:|---:|---:|---|
| `core/config/project_settings.cpp` | 0 | 4 | 6 | 5 | 0/4/6/5 |
| `core/config/project_settings.h` | 0 | 2 | 5 | 2 | 0/2/5/2 |
| `editor/editor_node.cpp` | 0 | 0 | 0 | 2 | 0/0/0/2 |
| `modules/mono/csharp_script.cpp` | 2 | 0 | 0 | 0 | 2/0/0/0 |
| `modules/mono/csharp_script.h` | 1 | 0 | 0 | 0 | 1/0/0/0 |

**Verdict ①: pass, no anomaly.** (Two independent checks agree: sha equality and symbol counts.)

## 2. ② Contract rebuild — target 177: **metadata/counts reproduced exactly, content sha NOT reproduced**

### 2.1 What was done

1. **Version constant corrected** — the only recoverable generator
   (`staging\modules\mcp_server\scripts\gen_renamed_contract.py`, byte-identical to the
   `_low-confidence` copy, sha256 `48703c644f1a7ee221a11cd35904054dd0bd35b5a2e37367e0e5fdca48d47d56`)
   carried `GENERATOR_VERSION = "1.3.0"` at line 500 while its own docstring already documents
   **v1.22**.  Changed that single line to `GENERATOR_VERSION = "1.22.0"`; nothing else touched.
   The result was promoted into the tree (fossil `21,390 B` preserved as
   `rebuild\work2b\gen_renamed_contract.py.fossil-2a`):
   `modules\mcp_server\scripts\gen_renamed_contract.py` = 118,450 B /
   `1fcbb4893dcb9177e8158b303b5d2b3e3aa03ad41ededafd95718a2c2939ba34`.
2. **Re-ran the generator** with the recorded inputs:
   `--old-contract F:\moonbit-hof-rs\tests\fixtures\mcp\tools_list.json` (read-only; sha256
   `8f8051c4c0f8941089f0b21a193cef7c51fa7c41d7e312b1463ea8593f313c54`, byte-identical to
   `rebuild\_refs\legacy-174\tools_list.json`), `--map` =
   `docs\tool-rename-map.json` (`2f552719f6a23fe328df0a2944c6048824c1b2a750aebc0fe2cabbcd3529c2bd`,
   matches the recorded `_meta.map_sha256`), `--out docs\tools_list.renamed.json`.
   Exit 0, self-checks `OK (lint 177/177, unique 177/177, disposition enum OK)`.
3. **Idempotence**: run twice back to back, same bytes and same sha both times.

### 2.2 Verification against the recorded TASK-076A numbers

| criterion | required | measured | verdict |
|---|---|---|---|
| `_meta.count` | 177 | **177** | pass |
| `_meta.added_count` | 6 | **6** (`project_build_csharp`, `project_write_text_file`, `project_validate_scripts`, `editor_set_node_script_batch`, `editor_set_node_property_updates`, `project_read_text_file`) | pass |
| `_meta.generator_version` | 1.22.0 | **1.22.0** | pass (after the constant fix) |
| editor endpoint | 154 | **154** (104 `editor_*` + 48 `project_*` + 2 `os_*`) | pass |
| game endpoint | 73 | **73** (23 `running_game_*` + 48 `project_*` + 2 `os_*`) | pass |
| idempotence | two runs, same sha | run1 = run2 = `078433de71db6a6da9190e4e9434dbed0376139c88fe19638b4251aff55d8b5c`, 129,016 B | pass |
| contract sha256 | `a5c59853c1e5a4913d600c663c8e972f058f7144869ec20337ab41b7a7bb17ea` (163,520 B) | `078433de71db6a6da9190e4e9434dbed0376139c88fe19638b4251aff55d8b5c` (129,016 B) | **MISMATCH, reported as-is** |

### 2.3 Why the sha does not match — concrete, measured difference

The generator that produced `a5c59853…` is **not** the generator that survived reconstruction.
The promoted copy is a *corrupt partial*: its own docstring documents v1.1…v1.22, but its data
tables are damaged, so the generator cannot emit 36 override records.

* `_meta.overrides` length: target **36** (recorded: `overrides 33 -> 36`); actual **21**.
* The 21 fired records are visibly **duplicated**: `play_scene` ×2, `replay_recording` ×2,
  `find_signal_connections` ×2 in the fired list, and `SCHEMA_OVERRIDES` contains
  `play_scene` and `find_signal_connections` twice each — reconstruction duplicated blocks.
* The three TASK-076A append-only records (`editor_get_scene_tree`,
  `editor_set_tilemap_cell`, `editor_set_tilemap_cells_in_rect` — described verbatim in the
  recorded commit message) are **absent from `DESCRIPTION_OVERRIDES`**; the recorded
  "generator 1.21.0 -> 1.22.0" step cannot be replayed because its 1.21.0 input does not exist.
* Consequently the emitted file is 129,016 B against the target's 163,520 B — **34,504 B short**,
  which is roughly the missing override records plus the damaged body.
* A line-level merge of all 115 transcript read windows for this file covers 2,279 of 2,309 lines
  with one 30-line hole and interleaved copies of several historical revisions; a naive merge
  splices revisions together (e.g. `GENERATOR_VERSION = "1.8.0"` lands on line 155 and
  `"1.16.0"` on line 337), so a recovered-by-merge file would be a Frankenstein, not the
  v1.22.0 artifact.  The full contract JSON is likewise unrecoverable: its read windows cover
  only 937 of a 4,174-line revision; no `read`/`write` payload carries the whole file.

**Verdict ②: partial.**  `count` / `added_count` / `generator_version` / 154 / 73 / idempotence
are all reproduced exactly from the recorded inputs, but the byte content cannot be reproduced
and the recorded sha `a5c59853…` is **not** reached.  Not faked: the promoted generator is the
best recoverable text with a one-line, recorded correction; it is flagged incomplete in the tree.

## 3. ③ Hard gaps

### 3.1 `tools\registration.cpp` — **structural completeness established, promoted**

| item | value |
|---|---|
| tree before | 2,580 B / 39 lines / `df7fed14622303ca554dd776a4ab554015e57c904f8196eed19c0c10a534e6bc` (the 09-22 fossil) |
| payload (`_low-confidence`) | 17,014 B / 294 lines / `abc9096343cedd82e972c5a6527599bd34c8ddc797a9f6a49ea21877c4182dea` |
| tree after (promoted) | 17,014 B / 294 lines / `abc9096343cedd82e972c5a6527599bd34c8ddc797a9f6a49ea21877c4182dea` |
| fossil preserved | `rebuild\work2b\registration.cpp.fossil-2a` |

Structural completeness evidence (script `rebuild\work2b\check_reg3.py`):

* 64 `#include`s (64 unique) and 63 `register_*_tools(r_registry)` calls (63 unique).
* every call has exactly one matching include; the only include without a call is
  `registration.h` (the header, correct).
* all 63 referenced group headers **exist** in `modules\mcp_server\tools\` (0 missing).
* the file is byte-complete (last line `}` at 294, no truncation marker, LF-only, 0 CR).

**Honest limit on the "177 literals" half of the task:** this file contains **no tool-name
literals at all** — it registers *group* functions (the literals live in the per-group
`tools\*.h/.cpp`, most of which are not recoverable payloads).  A per-name comparison of
"registration literals vs the 177 contract entries" is therefore **not constructible from this
file**; what the file does prove is that the wiring is internally complete and consistent
(63 groups, include/call bijection, all headers present).  Per-name coverage stays unproven
until the module builds (2c) or the group files are recovered.  This is a real limitation of
the payload, not of the file.

### 3.2 `scripts\accept_m1.ps1` — **not fixed; root cause measured (payload is internally corrupt)**

Current tree copy = payload copy = 57,469 B / 1,083 lines /
`10ba8a79f1c537d71edd5d30162ec58382ec5cf0f6b54b65060d2163098c7a01`.  Parse errors (10) with
exact locations:

| line | error |
|---:|---|
| 644 | `MissingCatchOrFinally` — a stray `}` where the `case12_game_process_endpoint` block opener should be |
| 888 | `MissingEqualsInHashLiteral` — the `evidence = (...)` hash literal of the case13 copy is never closed |
| 978, 987 | `UnexpectedToken }` |
| 1028 | `UnexpectedToken }` + `UnexpectedToken {` |
| 1031 | `UnexpectedToken elseif` + `UnexpectedToken {` |
| 1034 | `UnexpectedToken else` |
| 1043 | `UnexpectedToken }` |

Root cause, measured by comparing the file with every transcript read window
(`rebuild\work2b\merge_accept*.py`, `analyze_accept.py`):

* The reconstruction **dropped interior blocks and duplicated others**.  `Invoke-Case` sites
  appear 10 times but only 8 distinct cases exist, and `case12_game_process_endpoint` occurs at
  **lines 725 and 814**, `case13_game_without_port` at **665 and 876**.
* The byte-identical tail block (lines 976-1083, sha256 of the block
  `5fa4d069daf62b66ae39f12c5c62e8f5f649c8348259ee314bf355e4832ecb62`) also occurs at
  1028-1083 and earlier — i.e. the SUMMARY + `guard_user_port_9877` + `gate_scope_declared`
  tail is present **three** times.
* The region that the file cannot supply (the original `case12` opener + the missing
  `# Game side` block) is in lines 240-689 of the final revision (1,355 lines), for which the
  transcript holds **no read window at all** — only lines 1-60, 120-239, 690-769, 1300-1355
  were ever read.
* Two *attempted* repairs were built, applied to a copy, parsed, and **reverted**:
  * cut the phantom `}` (644) + the duplicated tail → 3 errors remained (lines 357, 659, 887);
  * rebuild the whole file from the merged read windows (1,355 lines, 73,345 B) → 7 errors.
  Neither reached `[Parser]::ParseFile` clean, so the payload copy was **restored**
  (byte-identical, `10ba8a79…`) rather than shipping a guess.

**What cannot be restored from the payload:** the `case12_game_process_endpoint` block opener,
the `# Game side` block, the closing brace of the duplicated `case13` hash literal, and the
proper ordering/de-duplication of the SUMMARY tail.  Per the task's own rule
("不得为了让解析通过而删功能"), no functionality was deleted to force a clean parse: the file
stays as recovered and is reported as broken.

## 4. Parseability re-check against the 2a numbers

| area | 2a recorded | 2b reproduced | verdict |
|---|---|---|---|
| `rebuild\godot` `.py` | 228 total / 228 ok / 0 failed | **228 / 228 ok / 0 failed** | exact match |
| `rebuild\godot` `.ps1` | 129 total / 6 with errors | **129 / 6 with errors** | exact match |

The same six `.ps1` files fail (the promotions did not change the file set):

| file | errors | first error @line |
|---|---:|---|
| `modules\mcp_server\docs\reports\evidence\task060\trace-recovered\scripts\mcp060_lib.ps1` | 2 | `MissingEndCurlyBrace@175` |
| `modules\mcp_server\scripts\accept_m1.ps1` | 10 | `MissingCatchOrFinally@644` |
| `modules\mcp_server\scripts\mcp022_unified_narrowing_gate_evidence.ps1` | 6 | `MissingExpressionAfterToken@557` |
| `modules\mcp_server\scripts\mcp027_object_shape_and_paths_evidence.ps1` | 3 | `MissingEndCurlyBrace@312` |
| `modules\mcp_server\scripts\mcp053_added_tools_evidence.ps1` | 6 | `ExpectedValueExpression@260` |
| `modules\mcp_server\scripts\mcp067_live.ps1` | 1 | `MissingEndCurlyBrace@95` |

Method: `[System.Management.Automation.Language.Parser]::ParseFile` per file (parse only, never
executed) — script `rebuild\work2b\parse_ps1.ps1`, results `parse-ps1-2b.json`; `.py` via
`ast.parse` — `parse-py-2b.json`.  No module source semantics were changed by this stage; the
two promoted files are (a) the recovered `registration.cpp` and (b) the recovered generator with
its one recorded constant corrected.

## 5. Artifact ledger

| artefact | path | bytes | sha256 |
|---|---|---:|---|
| patched `core/config/project_settings.cpp` | `rebuild\godot\...` | 102,533 | `e9c4f6fb143afcdd63939574e0067a4aff929ff47d2893b996da218415d05f68` |
| patched `core/config/project_settings.h` | `rebuild\godot\...` | 19,002 | `b8491ca81d1a8f8cdb986325812948e74406904614a0503704184452e19b7d79` |
| patched `editor/editor_node.cpp` | `rebuild\godot\...` | 400,247 | `699bfc817f99ce25cd45678cb3213dea203b49e1a85c4f4f54f7d1b597647ec8` |
| patched `modules/mono/csharp_script.cpp` | `rebuild\godot\...` | 89,504 | `7fef858f8f51a177390f1a878591a4567943ce2b78965b599e47b04b85975eb8` |
| patched `modules/mono/csharp_script.h` | `rebuild\godot\...` | 22,687 | `499bdbc4e2e8340125bc88e79065826da5753ee07da7070bf4ba58952ae16f0b` |
| promoted `modules/mcp_server/tools/registration.cpp` | `rebuild\godot\...` | 17,014 | `abc9096343cedd82e972c5a6527599bd34c8ddc797a9f6a49ea21877c4182dea` |
| promoted `modules/mcp_server/scripts/gen_renamed_contract.py` | `rebuild\godot\...` | 118,450 | `1fcbb4893dcb9177e8158b303b5d2b3e3aa03ad41ededafd95718a2c2939ba34` |
| regenerated `modules/mcp_server/docs/tools_list.renamed.json` | `rebuild\godot\...` | 129,016 | `078433de71db6a6da9190e4e9434dbed0376139c88fe19638b4251aff55d8b5c` |
| fossil backup `registration.cpp` | `rebuild\work2b\registration.cpp.fossil-2a` | 2,580 | `df7fed14622303ca554dd776a4ab554015e57c904f8196eed19c0c10a534e6bc` |
| fossil backup `gen_renamed_contract.py` | `rebuild\work2b\gen_renamed_contract.py.fossil-2a` | 21,390 | `179959e408eb16c8f85324670e945567028ff87fbe0d10ea731072a87eba7496` |
| payload backup `accept_m1.ps1` | `rebuild\work2b\accept_m1.ps1.before-repair` | 57,469 | `10ba8a79f1c537d71edd5d30162ec58382ec5cf0f6b54b65060d2163098c7a01` |

## 6. Decision-relevant summary

1. **Patches: done** — 0/0/0, post-state byte-identical to the recorded sandbox, all four
   symbols present with the exact §6 counts.
2. **Contract: 177 with the exact metadata, but not the recorded bytes.**  The surviving
   generator is a corrupt partial (21 of 36 override records, duplicated blocks); the recorded
   sha `a5c59853…` is unreachable from any recoverable payload.  The tree now holds a
   *generated* (not copied) 177-entry contract, `generator_version = 1.22.0`, correct
   `added_count`, and the measured 154 / 73 endpoint split — flagged incomplete.
3. **`registration.cpp`: promoted** — 294 lines, 63 group calls with a bijection to their
   includes, every referenced header present.  It cannot prove the 177 literals (it has none).
4. **`accept_m1.ps1`: still 10 parse errors** — the payload has whole blocks missing and whole
   blocks triplicated; the missing region was never read in any transcript.  No functionality
   was deleted to fake a clean parse.
5. **F: untouched** (pre/post evidence in §0); no scons was run; no module semantics changed.
