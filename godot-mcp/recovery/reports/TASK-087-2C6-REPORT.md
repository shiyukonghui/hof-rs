# TASK-087 (2c-6) — step-5 review, G6 / G3 / G5, and the acceptance ledger

* Repository: `H:\rebuild\godot`, branch `feature/mcp-server-module-rebuild`
* Start HEAD: `d82f621fc1` → End HEAD: **`675df5ef27`**, **pushed** (`git status --short` has one
  intended ` M` for the manifest at the moment of writing; see §8)
* Scratch/tooling: `C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task087\`
* Logs: `C:\Users\wyl\AppData\Local\Temp\mcp-recovery\logs\task087_*`
* Manifest: `modules/mcp_server/docs/reports/REBUILT-2C-MANIFEST.md` § 2c-6 (entries E-1..E-5.2)

---

## 0. One-line answer per requested item

| # | item | outcome |
|---|---|---|
| ① | review TASK-086 step 5; three conflict cases | **done.** Per-hunk ruling: **0 reverts** (no hunk weakened or deleted an assertion), 3 comment residuals rebuilt with markers, all three conflict cases rebuilt against the implementation's declared schema + live behaviour and marked. `[MCPServer]*` → **143 / 143 cases, 6396 / 6396 assertions, exit 0** (was 143/140/3 and 6391/6376/15). |
| ② | G6 `scripts/accept_m1.ps1` → `[Parser]::ParseFile` clean | **done.** 10 errors → **0**. 49 502 B / 1 022 lines, sha `6e2072ac…`. The body is the recorded 1 022-line revision (27 windows, zero holes); the damaged copy was unrepairable fragmentation, and the all-windows union is contaminated with `tools/editor_shader_write.cpp`'s C++ banner. |
| ③ | G3 `docs/DESIGN-DETAIL.md` → 84 486 B | **done, byte-exact.** 31 531 B → **84 486 B**, sha `b8ad40a3…`. Recorded read windows cover lines 1–1034 with zero holes; the independent TASK-078 staging body is **byte-identical**. No marker needed — nothing was invented. §17–§26 come back in full. |
| ④ | G5 contract | **shape gate passes; 10 overrides still missing.** `count=177`, `added_count=6`, `generator_version=1.22.0`, editor **154** / game **73**, **idempotent** (two runs, same sha). Delta to the pinned `a5c59853…`: **27 879 B smaller**, `_meta.overrides` **26 vs 36** — measured and decomposed; nothing invented. |
| ⑤ | acceptance | `[MCPServer]*` **exit 0, 0 failures**; full `--headless --test` **1569/1569, exit 0**; **7 of 9 gate scripts green** (contract subset **3/3** after recovering two missing manifests); `accept_m1.ps1` **16/20**, four FAILs named with their measured values. |

**Reached:** every one of the five items. **Not reached:** the ten missing contract overrides
(no evidence in this tree), and `accept_m1.ps1`'s four stale expectations (a declared red, not a
silent one).

---

## 1. Method

Two changes from TASK-086, both forced by the evidence:

1. **Read-window reconstruction, not edit replay.** `docs/DESIGN-DETAIL.md` has **no**
   `events-write` row, so the TASK-086 method (newest whole-file write + later edits) cannot run
   at all. The recorded `events-read` windows do carry the whole file, so the base is a
   **merge of numbered windows** with the newest text per line number, and edits are only a
   consistency check (`work\task087\merge.py`).
2. **Skeleton restriction.** The union of *all* windows for `scripts/accept_m1.ps1` is
   contaminated — line 556 of the union is `// TASK-035 (B5 batch 3): the editor_shader_write
   group`, i.e. the banner of `tools/editor_shader_write.cpp`. Restricting the merge to one
   revision skeleton (`--skeleton 1022`, `work\task087\merge2.py`) removes it and yields a
   body that parses with 0 errors; the `1008` skeleton also parses with 0 errors and is kept as
   a second witness.

A third tool decided which candidate was the right generation: `work\task087\editmatch.py`
scores every candidate against every applied recorded edit's `old` text (1 022-line base
**22/73**, tree 7/73, 1 355-line union 9/73).

All console output from the Python tooling goes through `work\task087\rep.py`, which writes
UTF-8 bytes straight to `sys.stdout.buffer` and to a report file, so the Windows code page
cannot corrupt the Chinese documents this tree is full of (the GBK `UnicodeEncodeError` was the
first thing that had to be fixed).

---

## 2. ① Review of TASK-086 step 5 (`d82f621fc1`)

The commit touches two files: `tests/test_mcp_server.h` (+127 / −58) and the manifest. Rule
applied per hunk — **weakening or deleting an assertion to make a gate green ⇒ revert**;
**test text the recording does not carry ⇒ rebuild with a marker**.

| # | hunk | verdict |
|---|---|---|
| 1 | 38 registry-size assertions `48/76/59/35/31/24` → `73/177/154/50` | **keep** |
| 2 | `the analysis tools never write to the project`: `13` → `11` | **keep** (the fixture is `ScratchProject`; 13 is `ReadFilesProject`'s) |
| 3 | `payload["reason"]` → `payload["note"]…`; `"no_log_file"` → `"none"` | **keep** (TASK-026 replaced the TASK-024 key) |
| 4 | the two `String::utf8` log fixtures | **keep** (`String(const char *)` is `append_latin1`) |
| 5 | three explanatory comments step 5 left behind | **rebuilt, marked** |

**Reverts: none.** `work\task087\scan_counts.py` re-measures the file: **47 registry-size
assertion sites, zero stale values, no site whose expected value disappeared.**

Hunk 5 is the only prose this batch wrote: `:1419` still said "23 both-scope + 17 game-scope"
above `== 73`; `:4664` still said "66 → 76 registered, 49 → 59 visible" above `== 177 / == 154`;
`:7759` still said "76 registered tools, 59 of them visible" above the same. Each is realigned
and wrapped in `// [REBUILT-2C low-confidence: verify] … // [/REBUILT-2C]`.

### The three conflict cases

| case | written | basis |
|---|---|---|
| `project_edit_resource rewrites an existing resource …` | renamed; unknown-name half moved to the second case as a **refusal** block (`result == NIL`, `code == -32001`, message names it, `data.suggestion` contains the recorded `is not a property of`, **file unchanged**) | `events-edit seq=577 t=1790229749088` (TASK-049 D8), **6.3e7 ms newer** than the test's seq=596 skip rule. The refusal is a strictly *stronger* claim than the skip. |
| `project_edit_resource reports no change and validates its arguments` | the refusal block + an **empty-bag** block (`"No properties were changed"`, `changed.is_empty()`) | the empty bag is the only case the implementation's short circuit is honest for (`project_write_resource_scene.cpp:718-729`) |
| `project_read_resource reports the loaded resource type` | TASK-026 shape: `total_properties`, `truncated == false`, `dropped == 0`, `limits.max_properties == 64`; value halves unchanged | `tools/project_read_files.cpp:789-795` (`MAX_RESOURCE_PROPERTIES = 64`, no byte budget), from `events-edit seq=445/450` |

The bag is **3** entries, not 2: the baseline log shows `properties_count == 0` vs
`properties.size() == 3`, and the old `total_properties`/`properties.size()` assertions failed
as `3 == 2`. The assertion now states 3 and carries `properties.keys()` in its failure message
so the next drift is readable without a rebuild.

**Measured:** `--headless --test --test-case=[MCPServer]*` → `143 | 143 passed | 0 failed`,
`6396 | 6396 passed | 0 failed`, `exit 0`.

---

## 3. ② G6 — `scripts/accept_m1.ps1`

| | |
|---|---|
| before | 57 469 B / 1 008 lines / **10** errors (first `:644` `The Try statement is missing its Catch or Finally block`) |
| after | **49 502 B / 1 022 lines / 0 errors**, sha `6e2072ac48ae9f09edb50132fb29cb03a3d52b89cf548181dd7910df71215552` |

The damaged copy is not patchable: `:644` is a stray `}` that opens the "Game side" banner,
`:665`–`:675` is case 18's body under case 13's label, `:814`/`:875` repeat whole cases,
`:886`–`:895` repeats case 13's body, and `:976`–`:1 083` appends one and a half further copies
of the `guard_user_port_9877` block **after `exit 0`**. `Test-Listener`/`Get-ListenerPid` and the
`# Main` banner each appear twice.

**Scope, declared:** the restored gate carries **case1–case19**. The two later cases the damaged
copy named — `case0_repo_exit_code_propagation` (TASK-069) and
`case20_tools_list_cross_process_restart` (TASK-004) — have recorded text
(`events-edit seq=1030`, 1 998 B; `seq=858`, 3 061 B) and were grafted experimentally at their
recorded anchors, but the graft does **not** reach 0 parse errors (17), so it is not what was
written. Choosing the parseable recorded revision over a broken superset is the conservative
reading; both cases are registered as **not rebuilt** with their event ids.

---

## 4. ③ G3 — `docs/DESIGN-DETAIL.md`

| | |
|---|---|
| before | 31 531 B / 417 lines (stopped inside §15's clause table) |
| target | 84 486 B |
| after | **84 486 B**, sha `b8ad40a34a33951b220349ea70ba59fba064ce9fa8b53ed7653b834b33be29c0` |

Evidence: 120 read windows cover line numbers **1–1034 with zero holes**
(`work\task087\merge.py`: `windows: 120 rows, lines=1034, max=1034, holes=0`). Cross-check: the
independently produced TASK-078 staging body is **byte-identical** (same size, same sha256).
The newest contributing window is `t=1790349324870`, the newest read of any revision, and every
later recorded edit is a no-op on the buffer (0 applied, 0 broken). **No marker** — no byte was
invented. Restored: the §15 rows for GDR-22/23/24 and **§17–§26** in full (GDR-19..GDR-28).

---

## 5. ④ G5 — contract

Shape gate, all five limbs, measured:

| limb | value |
|---|---|
| `count` | **177** |
| `added_count` | **6** |
| `generator_version` | **1.22.0** |
| editor / game | **154 / 73** (rename map 47 `both` + 103 `editor` + 24 `game`; +6 `ADDED_TOOLS` ⇒ 50 `both` + 104 `editor` + 23 `game`) |
| idempotent | two consecutive `python gen_renamed_contract.py`, both exit 0, both leave **136 641 B** / sha `368cd3c792916088c09e837a12582cde1252e14f6c9ad02110c97059e641b907` |

The generator's own self-checks report `lint 177/177, unique 177/177, disposition enum OK`, and
the rename-map sha it prints is `2f552719…` — **identical to the pinned fingerprint**.

### The delta, as measured (not estimated)

| | pinned (`contract_fingerprint.txt`) | now |
|---|---|---|
| bytes | 163 520 | **136 641** (−27 879) |
| sha256 | `a5c59853c1e5a4913d600c663c8e972f058f7144869ec20337ab41b7a7bb17ea` | `368cd3c792916088c09e837a12582cde1252e14f6c9ad02110c97059e641b907` |
| `_meta.overrides` | 36 | **26** |
| generator version | 1.22.0 | 1.22.0 (match) |
| `count` / `added_count` / `tool_count_in` / `excluded` / `merged` | 177 / 6 / 174 / `[navigate_to, export_project]` / 1 | **all equal** |

**Why:** (a) **10 override records are missing**, and their names are *not in this tree's
evidence* — the contract has no recorded whole-file write, the fingerprint pins only the array's
length, and `work\task087\ovkeys.py` harvested every tool-name token near an `overrides` mention
across the dump/diff/gen-run channels (109 distinct tokens) without yielding a 10-name set. Their
mean entry size is ≈740 B compact / ≈1.3 KB pretty-printed, i.e. the missing array content is the
bulk of the gap. (b) **`_meta.map_path` is the absolute path of the working tree** — the pinned
contract records `F:\RustProjects\godot-mcp-pro\…`, this tree writes `H:\rebuild\godot\…`; that
field alone makes a byte-identical regeneration impossible by construction. **Nothing was
invented.** The TASK-078 staging generator (118 449 B, `GENERATOR_VERSION 1.3.0`) was checked and
rejected as an older generation and a strict subset.

---

## 6. ⑤ Acceptance

### 6.1 Doctests

| run | command | exit | result |
|---|---|---:|---|
| module | `--headless --test --test-case=[MCPServer]*` | **0** | `143 / 143 passed / 0 failed`, `6396 / 6396` assertions, `SUCCESS!` |
| full | `--headless --test` | **0** | `1569 / 1569 passed / 0 failed / 3 skipped`, `430702 / 430702` assertions, `SUCCESS!` |

No `FATAL` / `SIGSEGV` / `Status: FAILURE` in either stream. Builds: two `tests=yes` runs from
`cmd.exe` via `scons_run.ps1`, both **exit 0** (958 s / 960 s).

### 6.2 Gate scripts — real output

| gate | result |
|---|---|
| `docs/scripts/check_tool_groups.py` | **PASS** (`TOOL-GROUPS CHECK PASS`, 5681 B, sha `b83d79d3…`) |
| `scripts/check_contract_subset.ps1` | **3/3 PASS** — editor 9888 **154 == 154**, game 9889 **73 == 73**, verbatim; `guard_user_port_9877` `pid_before=-1 pid_after=-1`; `contract=177` |
| `docs/scripts/check_rename_map.py` | **PASS** (`all checks green`; `177 == 174 - 2 - 1 + 6`) |
| `scripts/check_tautologies.py` | **PASS** |
| `scripts/check_exit_propagation.py` (+ `--probes`) | **PASS** / **10/10** |
| `scripts/check_hardcoded_counts.py` | **FAIL — 1 unclassified line**, pre-existing: `docs/scripts/_tmp_gen_b3_b5.py:282` holds the literal `171` in a comment. A `_tmp_` scratch generator, unrelated to this batch, already recorded as not-done in TASK-086 §5.4. Reported, not silenced. |
| `scripts/check_engine_anchor.ps1` | not run (rebuilds the mono binary; out of scope, unchanged from TASK-086) |

### 6.3 The contract-subset gate was red for a reason worth recording

It first read **2/3** with the registry *stronger* than the gate's expectation
(`tools=154 expected_for_editor=91`, `tools=73 expected_for_game=53`). **Two manifests the script
reads were absent from this tree:**

| manifest | before | after | fingerprint |
|---|---|---|---|
| `docs/tool-groups-b5.json` | absent | 12 012 B → 12 005 B | 12 209 B, sha `85bb783e…` |
| `docs/tool-groups-added.json` | absent | 8 506 B | 9 478 B, sha `72d0c8ae…` |

Both were recovered from the TASK-078 staging body of the same paths. That moved the union to
141/61, still 14 short: the remaining 14 contract tools sit in **8 b5 groups whose `implemented`
flag was still `false`** although all 14 are live. `work\task087\fix_b5_flags.py` flips exactly
those eight and no other group (original bytes preserved at
`work\task087\tool-groups-b5.json.orig`); the 7-byte size change is JSON re-serialisation only.
The gate then read `implemented_union=154 tools (editor endpoint) / 73 tools (game endpoint)` and
passed **3/3**. This is a *gate-metadata* correction whose justification is the live measurement
it is compared against: 177 contract entries served as exactly 154 / 73 with zero leakage and
**verbatim** name/description/inputSchema on both endpoints.

### 6.4 `accept_m1.ps1` — 16 / 20, four FAILs with their values

| case | script expects | live (measured) |
|---|---|---|
| `case1_GET_mcp_200` | `tools == 2` | `tools: 154` (the body is otherwise a correct 200 status dict) |
| `case3_tools_list_fixture` | the 2 M1 tools | `tools=154`; the two it checks are `name_verbatim=True inputSchema_verbatim=True description_verbatim=True` |
| `case12_game_process_endpoint` | the M1 game subset | `status=200 is_editor=False`, `initialize` verbatim; the failing half is the same count expectation |
| `guard_user_port_9877` | `pid_before > 0` ("the user's editor is present") | `listening=False pid_before=-1 pid_after=-1` — the 9877 listener was retired; the correct invariant ("this script never touches 9877") is what `check_contract_subset.ps1`'s guard states and **passes** |

**Not fixed here.** None of the four is missing text: each is a positively-wrong expectation with
a recorded *later* generation on the other side, so repairing them means deriving the expected
tool sets from the manifests (the way `$ToolNames` already is in that file) and inverting the 9877
guard — an assertion change that belongs to a batch which can rebuild and re-run the whole
acceptance. The invariant they were meant to protect **is** asserted and green elsewhere
(contract subset 154/154 and 73/73 verbatim; doctest 143/143). Reported as **red with cause**.

---

## 7. Iron rules

| rule | evidence |
|---|---|
| **never touch `F:`** | all six values identical to the TASK-086 baseline: `DECISIONS.md` 537 251 B sha `114B2A8218…`; `tools_list.json` 48 749 B sha `8F8051C4C0…`; `Get-PSDrive F` used 922 841 124 864 / free 392 138 186 752. The fixture was only **read** (it is the generator's input and its sha check passed). |
| **no shell redirection** | every build and Godot run goes through `scons_run.ps1` / `run_godot.ps1` (`cmd.exe` → `Start-Process … -RedirectStandardOutput/-RedirectStandardError`). Text files are written with `Out-File`, `Set-Content`, `-Out` or Python; `*>` is used **only** inside the recorded `accept_m1.ps1` body for a log file, and `\| Select-String` pipes only filter a stream. |
| **destructive commands refused by default** | **no destructive command ran at all.** Every change is a write over an existing file whose source is a recorded event, a recorded window, a staging body, or a flag flip over one JSON manifest whose original bytes are backed up. No file was removed, moved or renamed. |
| **builds launched from cmd** | `scons_run.ps1` runs `Start-Process cmd.exe /c … -WorkingDirectory H:\rebuild\godot`; two `tests=yes` builds, both exit 0. |
| **only `H:` and `C:…\mcp-recovery\` written** | `git status --short` lists only the intended manifest edit; all scratch is under `work\task087\`. |

---

## 8. 收尾

```
git log --oneline -8
675df5ef27 modules/mcp_server: task087 (2c-6) - gate ledger, and accept_m1.ps1's four remaining FAILs named
586cb5e010 modules/mcp_server: task087 (2c-6) step5a - recover the two missing group manifests; contract subset gate is 3/3
ab99c693cc modules/mcp_server: task087 (2c-6) step1 - step-5 boundary review + the three conflict cases, suite honestly green
75d86665e6 modules/mcp_server: task087 (2c-6) step4 - G5 contract shape gate verified, 10 overrides still missing
8bbd589e52 modules/mcp_server: task087 (2c-6) step2 - accept_m1.ps1 parses with 0 errors
96a7d69186 modules/mcp_server: task087 (2c-6) step3 - DESIGN-DETAIL.md restored byte-exact (84,486 B)
d82f621fc1 modules/mcp_server: task086 (2c-5) step5 - tester assertions to the recovered generation, and the 2c-5 manifest
058f618bb2 modules/mcp_server: task086 (2c-5) step4 - recover the two TASK-068 description overrides
```

```
git status --short
(empty at hand-off; branch in sync with origin/feature/mcp-server-module-rebuild)
```

`git push`: six pushes, all fast-forward, no rejection and no force —
`d82f621fc1..96a7d69186`, `96a7d69186..8bbd589e52`, `8bbd589e52..75d86665e6`,
`75d86665e6..ab99c693cc`, `ab99c693cc..586cb5e010`, `586cb5e010..675df5ef27`
(the last one covers both the manifests and the gate-ledger manifest section).

**Manifest update summary** (§ 2c-6, committed):

* **E-1** DESIGN-DETAIL byte-exact restoration, with the second-witness cross-check and the note
  that no marker is needed.
* **E-2** `accept_m1.ps1` 10 → 0 parse errors, the fragmentation inventory, the contamination
  finding, and the declared case1–case19 scope with the two not-rebuilt cases named.
* **E-3** G5 shape gate + the measured delta decomposition and the `map_path` structural reason.
* **E-4** the step-5 per-hunk ruling table, the three rebuilt comment residuals, and the three
  conflict cases with their evidence.
* **E-5 / E-5.1 / E-5.2** the gate ledger, the two recovered manifests + flag flip, and
  `accept_m1`'s four FAILs with their live values.

**F: untouched evidence:** all six values byte-identical to the pre-flight baseline (§7), and
identical to TASK-086's report.

**Honest shortfalls:** the 10 missing contract overrides; `accept_m1`'s four stale expectations;
`check_hardcoded_counts.py`'s one pre-existing unclassified line; `check_engine_anchor.ps1` not
run.
