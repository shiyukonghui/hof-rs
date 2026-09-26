# REBUILD-2A-MANIFEST

TASK-079 — **rebuild stage 2a** on C:.  Assembled `rebuild\godot`, inventoried it, listed
every gap against the TASK-078 staging payloads, and parse-checked every `.py` / `.ps1` in the
result.  This stage **moves and counts only**: no scons build, no gate run, no module source
rewritten, no patch applied to the tree.

* generated: `2026-09-25 23:55:47`
* staging root: `staging\` (TASK-078: 2,276 staged files / 20,595,326 B)
* rebuild root: `rebuild\`
* baseline: `%TEMP%\audit002\tree` (09-22 full engine snapshot, no `.git`)
* safety: **zero writes to F:**; every write under `C:\Users\wyl\AppData\Local\Temp\mcp-recovery\`;
  no shell redirection anywhere (all writers are `Set-Content` / `Out-File -FilePath` /
  `[IO.File]::WriteAllText` / Python `io.open(...,'w')`).

## 1. Assembly result

### 1.1 `rebuild\godot` by top-level directory

| dir | files | bytes |
|---|---:|---:|
| `graphify-out` | 4019 | 467523048 |
| `bin` | 4 | 180590549 |
| `editor` | 1828 | 179497526 |
| `thirdparty` | 4883 | 149234026 |
| `doc` | 837 | 104680422 |
| `modules` | 3849 | 29195444 |
| `(root)` | 47 | 18481496 |
| `servers` | 619 | 12609607 |
| `scene` | 847 | 12553572 |
| `core` | 482 | 9118837 |
| `platform` | 873 | 8699281 |
| `drivers` | 254 | 5554440 |
| `tests` | 249 | 3901403 |
| `misc` | 400 | 2988940 |
| `main` | 15 | 396207 |
| `docs` | 6 | 130026 |
| `.github` | 26 | 76422 |
| **TOTAL** | **19238** | **1185231246** |

### 1.2 What the layout is

```text
rebuild\
  godot\                          the reconstruction tree (engine baseline + mcp_server module)
    SConstruct, core\, editor\, modules\, platform\, scene\, servers\, drivers\,
    main\, misc\, tests\, thirdparty\, doc\, bin\ (binaries only),
    modules\mcp_server\**          module source + scripts + docs + evidence
    docs\reports\**                repo-root reports (also present in the baseline)
  _low-confidence\                 LOW-confidence payloads, NOT part of the tree
  _excluded\                       non-repo scratch captured from a .git/ folder
  _refs\legacy-174\                the legacy 174-tool contract input (read-only from F:)
  patches\                         the three engine patches, verbatim
  ENGINE-PATCHES-TO-REAPPLY.md     how to replay those three patches
```

### 1.3 Baseline copy accounting

| item | files | bytes |
|---|---:|---:|
| copied from `%TEMP%\audit002\tree` | 18603 | 1175248680 |
| **deliberately not copied** (`bin\obj` scons objects + `__pycache__`) | 3168 | 2750916297 |

`bin\obj` is 2.75 GB of regenerable object files and `__pycache__` is Python bytecode; the task
is "usable rebuild tree", so they are excluded **explicitly and visibly** rather than silently.
The four `bin\` files that matter — `godot.windows.editor.x86_64.exe` (180,286,464 B),
`godot.windows.editor.x86_64.console.exe`, `.exp`, `.lib` — **are** copied, so the tree has a
runnable (stale, pre-patch, non-mono) editor available.

### 1.4 Landing summary

| class | count | destination |
|---|---:|---|
| module payloads, HIGH/MEDIUM confidence | 661 | `rebuild\godot\modules\mcp_server\**` |
| non-module payloads landed (repo-root extras + docs) | 11 | `rebuild\godot\**` |
| LOW confidence payloads | 41 | `rebuild\_low-confidence\**` |
| captured `.git/` scratch | 1 | `rebuild\_excluded\**` |
| staged payloads deliberately **not** overlaid | 191 | (staging only) |
| staged payloads that are out-of-repo / have no bytes | 1410 | (staging only) |

`rebuild\_low-confidence` inventory:

| dir | files | bytes |
|---|---:|---:|
| `modules` | 40 | 1956907 |
| `core` | 1 | 29340 |
| `platform` | 1 | 7335 |
| `(root)` | 1 | 2288 |

## 2. Is the baseline usable, and is it pre-patch?

| key file | present | bytes | sha256 |
|---|---|---:|---|
| `SConstruct` | yes | 53702 | `ad7e48e81c7a2a70bb12ecaaa321c77a9d584c161557f3c8e27c533cbb7b8254` |
| `core/config/project_settings.cpp` | yes | 75556 | `c76f85acfb214ddadf16cd08742eec5c73a20d6753843bcb33f5e552f745886c` |
| `core/config/project_settings.h` | yes | 13295 | `1e4e7d6e24b559f6c27e6f6b02f21de68967bea0c226d25f4f6680a660a2d994` |
| `editor/editor_node.cpp` | yes | 389353 | `8110094827f6d7da6209ad2e1c7f371f96f63307255300630b78803c70cd2321` |
| `modules/mono/csharp_script.cpp` | yes | 86199 | `842199675aa4775830508b10d209bde494edd66786114776627548d41177d0db` |
| `modules/mono/csharp_script.h` | yes | 20978 | `41fe4bdf644b6cdf1621d18ffcecb6deaa8447225764909e233630a5553cc5cd` |
| `modules/gdscript/gdscript.cpp` | yes | 87346 | `111476844f3ef7b01e63034c56695c745cbeedb79a53158b6566ba93f373b39e` |
| `platform/windows/os_windows.cpp` | yes | 95612 | `92d107f08a985453bd9ce693cd285a47245fae9e13db883ea9c67684e281d7e0` |
| `modules/mcp_server/register_types.cpp` | yes | 4353 | `d323913162162807f972b7d10f64433ee2701b96b51453296e05331ac8d27910` |

* `platform\windows\**`: **69 files / 1225933 B** — the whole Windows platform layer is present.
  (The 09-22 baseline measured 71 files there; the two-file difference is the `__pycache__`
  bytecode that this assembly drops on purpose — see §1.3.)
* whole tree: **19238 files / 1185231246 B** (engine + module + docs assets).
* the baseline is a *full* engine snapshot: `core` 482 files, `editor` 1,828, `scene` 847,
  `thirdparty` 4,883, `modules` 3,849 (mostly the 09-22 copy of the mcp_server module, which the
  staged payloads then overlay).

### 2.1 Is it already patched?  **No.**

| symbol | introduced by | occurrences in the baseline |
|---|---|---:|
| `is_source_newer_than_assembly` | patch 1 (`5f3e7fb441`) | 0 |
| `update_settings_section_text` | patch 2 (`96f631addb`) | 0 |
| `save_custom_section` | patch 2 (`96f631addb`) | 0 |
| `save_preserving_text` | patch 3 (`2f85141a74`) | 0 |

A full-text scan of the five patched engine files found **zero** occurrences of any patch symbol,
and `git apply --check` accepts all three patches (patch 3 only after patch 2 — see
`ENGINE-PATCHES-TO-REAPPLY.md` §5). So the baseline is the **pre-patch upstream state** and is
the correct pre-image for the replay.  The only `mcp_server` mentions in the baseline are the
09-22 module directory itself (46 files) and its build wiring — not the three patches.

## 3. Known hard gaps (the five named in the task)

| # | path | status | source | evidence | impact | recommended recovery |
|---|---|---|---|---|---|---|
| 1 | `modules\mcp_server\tests\test_mcp_server.h` | LOW confidence -> `rebuild\_low-confidence\modules\mcp_server\tests\test_mcp_server.h` | `staging\modules\mcp_server\tests\test_mcp_server.h` | the whole doctest harness: 9,626 lines, 431,976 B staged vs 1,392 lines / 66,392 B in the baseline; the replay had **456 failed edits** over 793 edit events and read coverage is 46.9% | the module cannot be built with tests, and `scons tests=yes` / gate 3 (doctest) cannot run; it is the single largest verification asset | re-extract from the transcripts with the edit chain anchored on the LAST complete read of the file, or replay `git show 96f631addb/2f85141a74 -- modules/mcp_server/tests/test_mcp_server.h` hunks (the three engine commits carry their module-side doctests); re-run 9,626 lines against gate 3 to prove it |
| 2 | `modules\mcp_server\docs\DESIGN-DETAIL.md` | LOW confidence -> `rebuild\_low-confidence\modules\mcp_server\docs\DESIGN-DETAIL.md` | `staging\modules\mcp_server\docs\DESIGN-DETAIL.md` | 84,486 B staged vs 31,531 B in the baseline; **50 failed edits** and no complete read; the staged file is complete-looking (coverage 100%, tail present) but 50 edits could not be replayed | documentation only — does not block compilation or the gates, but it is the design record for the whole module | re-run the read-window merge with the 50 failing edits dropped and re-checked against the report anchors (REPORT-067/075 reference its sections) |
| 3 | `modules\mcp_server\tools\registration.cpp` | LOW confidence -> `rebuild\_low-confidence\modules\mcp_server\tools\registration.cpp` | `staging\modules\mcp_server\tools\registration.cpp` | 17,014 B / 293 lines staged vs 2,580 B / 39 lines in the baseline; **42 failed edits**, coverage 100%, tail present | **blocks compilation**: the module needs the current registration.cpp (the registry of ~176 tools); the baseline copy is a 09-22 fossil | re-extract **before anything else** — without it the module does not compile |
| 4 | `modules\mcp_server\scripts\accept_m1.ps1` | MEDIUM confidence -> `rebuild\godot\modules\mcp_server\scripts\accept_m1.ps1` | `staging\modules\mcp_server\scripts\accept_m1.ps1` | 57,469 B staged (79.9% coverage, interior lines missing), **10 PowerShell parse errors** starting at line 644 (`MissingCatchOrFinally`) | gate 5 (accept_m1 x2, 22/22 inventory) cannot run | fix the 10 parse errors by hand from the surrounding read windows (the errors are localized, e.g. a `try` without `catch`) |
| 5 | `modules\mcp_server\scripts\gen_renamed_contract.py` | LOW confidence -> `rebuild\_low-confidence\modules\mcp_server\scripts\gen_renamed_contract.py` | `staging\modules\mcp_server\scripts\gen_renamed_contract.py` | 118,449 B staged, 75% coverage, tail partial, **47 failed edits**; the generator version constant is stuck at the old value | blocks regeneration of `tools_list.renamed.json`, which RECOVERY-PLAN §4.2 requires to be generated rather than copied | regenerate from `tools_list.renamed.json` history or re-run the generator after it is restored |

Status column: `已落` = present in the tree; `低置信` = parked in `_low-confidence`; `缺失` = not
landed at all.  All five are either `低置信` (four) or `已落` but broken (one).

### 3.1 What `rebuild\godot` actually holds at those five paths right now

This is the practical consequence of the confidence rule: where the baseline had a copy, the
tree holds the **09-22 fossil**; the current content is parked in `_low-confidence`.  A builder
must replace these files before compiling — do not mistake a present-but-old file for a good one.

| path | bytes in the tree | origin | bytes in `_low-confidence` | verbatim |
|---|---:|---|---:|---|
| `modules\mcp_server\tests\test_mcp_server.h` | 66392 | audit002 baseline fossil (09-22) | 431976 | **must be replaced before the build** |
| `modules\mcp_server\docs\DESIGN-DETAIL.md` | 31531 | audit002 baseline fossil (09-22) | 84486 | **must be replaced before the build** |
| `modules\mcp_server\tools\registration.cpp` | 2580 | audit002 baseline fossil (09-22) | 17014 | **must be replaced before the build** |
| `modules\mcp_server\scripts\accept_m1.ps1` | 57469 | staged payload, **overwrote the baseline copy** | absent | **must be replaced before the build** |
| `modules\mcp_server\scripts\gen_renamed_contract.py` | 21390 | audit002 baseline fossil (09-22) | 118449 | **must be replaced before the build** |

## 4. Gap table — every LOW-confidence payload (43 rows = 41 LOW payloads + 2 truncated docs variants kept for audit)

| path | status | source | conf | cov% | tail | failed edits | impact | suggestion |
|---|---|---|---|---:|---|---:|---|---|---|
| `core\config\project_settings.cpp` | 低置信 | `staging\core\config\project_settings.cpp` | low | 32.6 | yes | 10 | engine-side fragment — **not needed**, the baseline copy is authoritative | re-extract / re-validate |
| `methods.py` | 低置信 | `staging\methods.py` | low | 3.6 | yes | 0 | engine-side fragment — **not needed**, the baseline copy is authoritative | re-extract / re-validate |
| `modules\mcp_server\docs\DESIGN-DETAIL.md` | 低置信 | `staging\modules\mcp_server\docs\DESIGN-DETAIL.md` | low | 100.0 | no | 50 | documentation — no build impact | re-extract / re-validate |
| `modules\mcp_server\docs\reports\REPORT-009-b1-closure-running-game-read-scene.md` | 低置信 | `staging\modules\mcp_server\docs\reports\REPORT-009-b1-closure-running-game-read-scene.md` | low | 96.6 | partial-only | 16 | documentation — no build impact | re-extract / re-validate |
| `modules\mcp_server\docs\reports\REPORT-036-b5-navigation-theme-export-android.md` | 低置信 | `staging\modules\mcp_server\docs\reports\REPORT-036-b5-navigation-theme-export-android.md` | low | 8.4 | no | 1 | documentation — no build impact | re-extract / re-validate |
| `modules\mcp_server\docs\scripts\check_tool_groups.py` | 低置信 | `staging\modules\mcp_server\docs\scripts\check_tool_groups.py` | low | 35.3 | no | 1 | documentation — no build impact | re-extract / re-validate |
| `modules\mcp_server\docs\scripts\template.md` | 低置信 | `staging\modules\mcp_server\docs\scripts\template.md` | low | 11.8 | partial-only | 19 | documentation — no build impact | re-extract / re-validate |
| `modules\mcp_server\docs\tool-groups-added.json` | 低置信 | `staging\modules\mcp_server\docs\tool-groups-added.json` | low | 28.3 | no | 4 | documentation — no build impact | re-extract / re-validate |
| `modules\mcp_server\docs\tool-groups-b5.json` | 低置信 | `staging\modules\mcp_server\docs\tool-groups-b5.json` | low | 100.0 | no | 16 | documentation — no build impact | re-extract / re-validate |
| `modules\mcp_server\docs\tool-rename-map.json` | 低置信 | `staging\modules\mcp_server\docs\tool-rename-map.json` | mid(truncated) | None | yes | None | documentation — no build impact | re-extract / re-validate |
| `modules\mcp_server\docs\tools_list.renamed.json` | 低置信 | `staging\modules\mcp_server\docs\tools_list.renamed.json` | mid(truncated) | None | yes | None | documentation — no build impact | re-extract / re-validate |
| `modules\mcp_server\mcp_capture.h` | 低置信 | `staging\modules\mcp_server\mcp_capture.h` | low | 8.8 | no | 1 | engine-side fragment — **not needed**, the baseline copy is authoritative | re-extract / re-validate |
| `modules\mcp_server\mcp_jsonrpc.cpp` | 低置信 | `staging\modules\mcp_server\mcp_jsonrpc.cpp` | low | 40.6 | no | 1 | engine-side fragment — **not needed**, the baseline copy is authoritative | re-extract / re-validate |
| `modules\mcp_server\scripts\check_narrowing_points.py` | 低置信 | `staging\modules\mcp_server\scripts\check_narrowing_points.py` | low | 61.5 | yes | 20 | gate/evidence script — blocks that gate only | re-extract / re-validate |
| `modules\mcp_server\scripts\gen_renamed_contract.py` | 低置信 | `staging\modules\mcp_server\scripts\gen_renamed_contract.py` | low | 75.0 | partial-only | 47 | gate/evidence script — blocks that gate only | re-extract / re-validate |
| `modules\mcp_server\scripts\mcp010_b2_observation_evidence.ps1` | 低置信 | `staging\modules\mcp_server\scripts\mcp010_b2_observation_evidence.ps1` | low | 41.6 | no | 2 | gate/evidence script — blocks that gate only | re-extract / re-validate |
| `modules\mcp_server\scripts\mcp018_b3_closure_evidence.ps1` | 低置信 | `staging\modules\mcp_server\scripts\mcp018_b3_closure_evidence.ps1` | low | 44.6 | no | 3 | gate/evidence script — blocks that gate only | re-extract / re-validate |
| `modules\mcp_server\scripts\mcp019_b4_evidence.ps1` | 低置信 | `staging\modules\mcp_server\scripts\mcp019_b4_evidence.ps1` | low | 61.1 | yes | 11 | gate/evidence script — blocks that gate only | re-extract / re-validate |
| `modules\mcp_server\scripts\mcp023_narrowing_guardrail_evidence.ps1` | 低置信 | `staging\modules\mcp_server\scripts\mcp023_narrowing_guardrail_evidence.ps1` | low | 20.5 | partial-only | 15 | gate/evidence script — blocks that gate only | re-extract / re-validate |
| `modules\mcp_server\scripts\mcp024b_ergonomics_batch2_evidence.ps1` | 低置信 | `staging\modules\mcp_server\scripts\mcp024b_ergonomics_batch2_evidence.ps1` | low | 11.4 | no | 1 | gate/evidence script — blocks that gate only | re-extract / re-validate |
| `modules\mcp_server\scripts\mcp025_e3_writeside_evidence.ps1` | 低置信 | `staging\modules\mcp_server\scripts\mcp025_e3_writeside_evidence.ps1` | low | 54.9 | no | 1 | gate/evidence script — blocks that gate only | re-extract / re-validate |
| `modules\mcp_server\scripts\mcp026_e9_e6_evidence.ps1` | 低置信 | `staging\modules\mcp_server\scripts\mcp026_e9_e6_evidence.ps1` | low | 13.9 | no | 1 | gate/evidence script — blocks that gate only | re-extract / re-validate |
| `modules\mcp_server\scripts\mcp031_gate6_coverage_probes.ps1` | 低置信 | `staging\modules\mcp_server\scripts\mcp031_gate6_coverage_probes.ps1` | low | 32.4 | no | 9 | gate/evidence script — blocks that gate only | re-extract / re-validate |
| `modules\mcp_server\scripts\mcp059_contract_pre_post.py` | 低置信 | `staging\modules\mcp_server\scripts\mcp059_contract_pre_post.py` | low | 53.2 | no | 2 | gate/evidence script — blocks that gate only | re-extract / re-validate |
| `modules\mcp_server\scripts\mcp066b_run.ps1` | 低置信 | `staging\modules\mcp_server\scripts\mcp066b_run.ps1` | low | 27.1 | no | 1 | gate/evidence script — blocks that gate only | re-extract / re-validate |
| `modules\mcp_server\scripts\mcp068_live.ps1` | 低置信 | `staging\modules\mcp_server\scripts\mcp068_live.ps1` | low | 22.6 | no | 1 | gate/evidence script — blocks that gate only | re-extract / re-validate |
| `modules\mcp_server\tests\test_mcp_server.h` | 低置信 | `staging\modules\mcp_server\tests\test_mcp_server.h` | low | 46.9 | no | 456 | module source/test — **blocks the build or the gates** | re-extract / re-validate |
| `modules\mcp_server\tools\editor_animation_tree_write.cpp` | 低置信 | `staging\modules\mcp_server\tools\editor_animation_tree_write.cpp` | low | 13.7 | no | 4 | module source/test — **blocks the build or the gates** | re-extract / re-validate |
| `modules\mcp_server\tools\editor_control_layout_write.cpp` | 低置信 | `staging\modules\mcp_server\tools\editor_control_layout_write.cpp` | low | 34.2 | no | 1 | module source/test — **blocks the build or the gates** | re-extract / re-validate |
| `modules\mcp_server\tools\editor_node_read.cpp` | 低置信 | `staging\modules\mcp_server\tools\editor_node_read.cpp` | low | 64.1 | yes | 14 | module source/test — **blocks the build or the gates** | re-extract / re-validate |
| `modules\mcp_server\tools\editor_playback.cpp` | 低置信 | `staging\modules\mcp_server\tools\editor_playback.cpp` | low | 100.0 | no | 20 | module source/test — **blocks the build or the gates** | re-extract / re-validate |
| `modules\mcp_server\tools\editor_read_scene_inspector.cpp` | 低置信 | `staging\modules\mcp_server\tools\editor_read_scene_inspector.cpp` | low | 55.1 | no | 7 | module source/test — **blocks the build or the gates** | re-extract / re-validate |
| `modules\mcp_server\tools\editor_write_scene_editor.cpp` | 低置信 | `staging\modules\mcp_server\tools\editor_write_scene_editor.cpp` | low | 61.1 | yes | 32 | module source/test — **blocks the build or the gates** | re-extract / re-validate |
| `modules\mcp_server\tools\project_read_analysis.cpp` | 低置信 | `staging\modules\mcp_server\tools\project_read_analysis.cpp` | low | 46.5 | no | 1 | module source/test — **blocks the build or the gates** | re-extract / re-validate |
| `modules\mcp_server\tools\project_read_template.cpp` | 低置信 | `staging\modules\mcp_server\tools\project_read_template.cpp` | low | 51.5 | yes | 12 | module source/test — **blocks the build or the gates** | re-extract / re-validate |
| `modules\mcp_server\tools\project_write_resource_scene.cpp` | 低置信 | `staging\modules\mcp_server\tools\project_write_resource_scene.cpp` | low | 62.2 | yes | 26 | module source/test — **blocks the build or the gates** | re-extract / re-validate |
| `modules\mcp_server\tools\registration.cpp` | 低置信 | `staging\modules\mcp_server\tools\registration.cpp` | low | 100.0 | no | 42 | module source/test — **blocks the build or the gates** | re-extract / re-validate |
| `modules\mcp_server\tools\running_game_assertion.cpp` | 低置信 | `staging\modules\mcp_server\tools\running_game_assertion.cpp` | low | 40.7 | no | 2 | module source/test — **blocks the build or the gates** | re-extract / re-validate |
| `modules\mcp_server\tools\running_game_node_write.cpp` | 低置信 | `staging\modules\mcp_server\tools\running_game_node_write.cpp` | low | 91.6 | yes | 12 | module source/test — **blocks the build or the gates** | re-extract / re-validate |
| `modules\mcp_server\tools\running_game_observation.cpp` | 低置信 | `staging\modules\mcp_server\tools\running_game_observation.cpp` | low | 52.4 | no | 1 | module source/test — **blocks the build or the gates** | re-extract / re-validate |
| `modules\mcp_server\tools\tool_helpers.cpp` | 低置信 | `staging\modules\mcp_server\tools\tool_helpers.cpp` | low | 49.1 | no | 3 | module source/test — **blocks the build or the gates** | re-extract / re-validate |
| `modules\mono\build_scripts\build_assemblies.py` | 低置信 | `staging\modules\mono\build_scripts\build_assemblies.py` | low | 82.8 | partial-only | 0 | engine-side fragment — **not needed**, the baseline copy is authoritative | re-extract / re-validate |
| `platform\windows\detect.py` | 低置信 | `staging\platform\windows\detect.py` | low | 17.2 | yes | 0 | engine-side fragment — **not needed**, the baseline copy is authoritative | re-extract / re-validate |

### 4.1 Complete-looking payloads that were ruled LOW — **re-validate these first**

These four have 100% read coverage and a present tail, yet were classified LOW because their
edit replay failed; if the failed edits were cosmetic, the parked copy may already be the right
file.  This is the **highest-value re-check of stage 2b.**

| path | cov% | tail | failed edits | why it matters |
|---|---:|---|---:|---|
| `modules\mcp_server\tools\registration.cpp` | 100.0 | no | 42 | **build blocker** |
| `modules\mcp_server\tools\editor_playback.cpp` | 100.0 | no | 20 | module source |
| `modules\mcp_server\docs\DESIGN-DETAIL.md` | 100.0 | no | 50 | design record |
| `modules\mcp_server\docs\tool-groups-b5.json` | 100.0 | no | 16 | gate 1 / group port input |

### 4.2 Engine fragments that were deliberately NOT overlaid (N=191)

These are staged paths whose repository copy **already exists in the baseline**.  The staged
payload is a *read window*, i.e. a fragment, while the baseline holds the complete file;
overlaying would have regressed the tree.  They are listed here so the decision is auditable.

| staged path | staged bytes | baseline bytes | relation |
|---|---:|---:|---|
| `.gitattributes` | 597 | 598 | byte-identical modulo the final newline (staging has LF-normalized EOLs) |
| `build-m0.cmd` | 461 | 462 | byte-identical modulo the final newline (staging has LF-normalized EOLs) |
| `core\SCsub` | 10010 | 10011 | byte-identical modulo the final newline (staging has LF-normalized EOLs) |
| `core\io\resource_uid.h` | 4375 | 4376 | byte-identical modulo the final newline (staging has LF-normalized EOLs) |
| `core\io\stream_peer_tcp.cpp` | 5761 | 5762 | byte-identical modulo the final newline (staging has LF-normalized EOLs) |
| `core\io\tcp_server.cpp` | 3546 | 3547 | byte-identical modulo the final newline (staging has LF-normalized EOLs) |
| `core\string\print_string.h` | 3565 | 3566 | byte-identical modulo the final newline (staging has LF-normalized EOLs) |
| `drivers\png\resource_saver_png.cpp` | 4223 | 4224 | byte-identical modulo the final newline (staging has LF-normalized EOLs) |
| `editor\editor_log.h` | 6402 | 6403 | byte-identical modulo the final newline (staging has LF-normalized EOLs) |
| `editor\export\android_sdk_manager.h` | 5640 | 5641 | byte-identical modulo the final newline (staging has LF-normalized EOLs) |
| `editor\run\editor_run.cpp` | 12589 | 12590 | byte-identical modulo the final newline (staging has LF-normalized EOLs) |
| `editor\run\editor_run.h` | 3705 | 3706 | byte-identical modulo the final newline (staging has LF-normalized EOLs) |
| `editor\run\editor_run_bar.h` | 5420 | 5421 | byte-identical modulo the final newline (staging has LF-normalized EOLs) |
| `install-deps-m0.cmd` | 726 | 727 | byte-identical modulo the final newline (staging has LF-normalized EOLs) |
| `misc\scripts\install_accesskit.py` | 1534 | 1535 | byte-identical modulo the final newline (staging has LF-normalized EOLs) |
| `misc\scripts\install_d3d12_sdk_windows.py` | 6310 | 6311 | byte-identical modulo the final newline (staging has LF-normalized EOLs) |
| `modules\SCsub` | 1905 | 1906 | byte-identical modulo the final newline (staging has LF-normalized EOLs) |
| `modules\gdscript\tests\scripts\project.godot` | 406 | 407 | byte-identical modulo the final newline (staging has LF-normalized EOLs) |
| `modules\gdscript\tests\scripts\runtime\features\call_native_static_method.out` | 36 | 37 | byte-identical modulo the final newline (staging has LF-normalized EOLs) |
| `modules\mono\editor\Godot.NET.Sdk\Godot.NET.Sdk\Sdk\Sdk.props` | 7316 | 7317 | byte-identical modulo the final newline (staging has LF-normalized EOLs) |
| `modules\mono\editor\GodotTools\GodotTools.ProjectEditor\ProjectGenerator.cs` | 2098 | 2099 | byte-identical modulo the final newline (staging has LF-normalized EOLs) |
| `modules\mono\editor\GodotTools\GodotTools\Build\BuildInfo.cs` | 3204 | 3205 | byte-identical modulo the final newline (staging has LF-normalized EOLs) |
| `modules\mono\editor\GodotTools\GodotTools\Build\BuildManager.cs` | 13347 | 13348 | byte-identical modulo the final newline (staging has LF-normalized EOLs) |
| `modules\mono\editor\editor_internal_calls.cpp` | 12207 | 12208 | byte-identical modulo the final newline (staging has LF-normalized EOLs) |
| `modules\mono\utils\path_utils.cpp` | 7775 | 7776 | byte-identical modulo the final newline (staging has LF-normalized EOLs) |
| `scene\3d\navigation\navigation_region_3d.h` | 4574 | 4575 | byte-identical modulo the final newline (staging has LF-normalized EOLs) |
| `scene\animation\animation_tree.h` | 23976 | 23977 | byte-identical modulo the final newline (staging has LF-normalized EOLs) |
| `scene\resources\curve.h` | 15722 | 15723 | byte-identical modulo the final newline (staging has LF-normalized EOLs) |
| `tests\test_main.cpp` | 13015 | 13016 | byte-identical modulo the final newline (staging has LF-normalized EOLs) |
| `version.py` | 158 | 159 | byte-identical modulo the final newline (staging has LF-normalized EOLs) |
| `modules\mono\editor\Godot.NET.Sdk\Godot.NET.Sdk\Godot.NET.Sdk.csproj` | 1863 | 1910 | complete read; differs from the baseline by **BOM/CRLF only** (content identical line for line), -47 B |
| `modules\mono\editor\Godot.NET.Sdk\Godot.SourceGenerators\Godot.SourceGenerators.csproj` | 1868 | 1912 | complete read; differs from the baseline by **BOM/CRLF only** (content identical line for line), -44 B |
| `build-m0-attempt1.log` | 1053 | 1069 | complete read; **build-log drift** between 09-22 and 09-25 (artifact, no impact), -16 B |
| `install-deps-m0.log` | 2955 | 3000 | complete read; **build-log drift** between 09-22 and 09-25 (artifact, no impact), -45 B |
| `COPYRIGHT.txt` | 543 | 100327 | staging is a **partial read**, -99784 B vs the baseline |
| `SConstruct` | 6296 | 53702 | staging is a **partial read**, -47406 B vs the baseline |
| `core\config\engine.cpp` | 871 | 13405 | staging is a **partial read**, -12534 B vs the baseline |
| `core\config\project_settings.h` | 10449 | 13295 | staging is a **partial read**, -2846 B vs the baseline |
| `core\core_bind.cpp` | 4093 | 94920 | staging is a **partial read**, -90827 B vs the baseline |
| `core\core_bind.h` | 1530 | 27646 | staging is a **partial read**, -26116 B vs the baseline |
| `core\crypto\crypto_core.h` | 1347 | 4600 | staging is a **partial read**, -3253 B vs the baseline |
| `core\error\error_list.h` | 2427 | 4676 | staging is a **partial read**, -2249 B vs the baseline |
| `core\error\error_macros.cpp` | 4080 | 10628 | staging is a **partial read**, -6548 B vs the baseline |
| `core\input\input.cpp` | 17629 | 86190 | staging is a **partial read**, -68561 B vs the baseline |
| `core\input\input_enums.h` | 1094 | 4846 | staging is a **partial read**, -3752 B vs the baseline |
| `core\input\input_event.cpp` | 1755 | 67601 | staging is a **partial read**, -65846 B vs the baseline |
| `core\input\input_map.cpp` | 14006 | 42494 | staging is a **partial read**, -28488 B vs the baseline |
| `core\io\config_file.cpp` | 6305 | 10889 | staging is a **partial read**, -4584 B vs the baseline |
| `core\io\dir_access.cpp` | 6214 | 22414 | staging is a **partial read**, -16200 B vs the baseline |
| `core\io\dir_access.h` | 2549 | 7456 | staging is a **partial read**, -4907 B vs the baseline |
| `core\io\file_access.cpp` | 4362 | 37715 | staging is a **partial read**, -33353 B vs the baseline |
| `core\io\image.cpp` | 27741 | 168859 | staging is a **partial read**, -141118 B vs the baseline |
| `core\io\image.h` | 5941 | 22050 | staging is a **partial read**, -16109 B vs the baseline |
| `core\io\json.cpp` | 5911 | 41135 | staging is a **partial read**, -35224 B vs the baseline |
| `core\io\json.h` | 873 | 4810 | staging is a **partial read**, -3937 B vs the baseline |
| `core\io\logger.cpp` | 2295 | 8895 | staging is a **partial read**, -6600 B vs the baseline |
| `core\io\resource.h` | 820 | 8901 | staging is a **partial read**, -8081 B vs the baseline |
| `core\io\resource_format_binary.cpp` | 358 | 71691 | staging is a **partial read**, -71333 B vs the baseline |
| `core\io\resource_importer.cpp` | 836 | 18402 | staging is a **partial read**, -17566 B vs the baseline |
| `core\io\resource_loader.cpp` | 1371 | 59269 | staging is a **partial read**, -57898 B vs the baseline |
| `core\io\resource_loader.h` | 3046 | 15009 | staging is a **partial read**, -11963 B vs the baseline |
| `core\io\resource_saver.cpp` | 2339 | 10077 | staging is a **partial read**, -7738 B vs the baseline |
| `core\io\resource_uid.cpp` | 1894 | 14531 | staging is a **partial read**, -12637 B vs the baseline |
| `core\io\socket_server.cpp` | 1347 | 3581 | staging is a **partial read**, -2234 B vs the baseline |
| `core\io\socket_server.h` | 850 | 3084 | staging is a **partial read**, -2234 B vs the baseline |
| `core\io\stream_peer_socket.cpp` | 1337 | 6859 | staging is a **partial read**, -5522 B vs the baseline |
| `core\io\stream_peer_socket.h` | 1252 | 3856 | staging is a **partial read**, -2604 B vs the baseline |
| `core\io\stream_peer_tcp.h` | 624 | 2858 | staging is a **partial read**, -2234 B vs the baseline |
| `core\io\tcp_server.h` | 485 | 2719 | staging is a **partial read**, -2234 B vs the baseline |
| `core\math\color.cpp` | 3744 | 13807 | staging is a **partial read**, -10063 B vs the baseline |
| `core\math\math_defs.h` | 502 | 5992 | staging is a **partial read**, -5490 B vs the baseline |
| `core\object\callable_mp.h` | 4620 | 10456 | staging is a **partial read**, -5836 B vs the baseline |
| `core\object\class_db.cpp` | 7474 | 72657 | staging is a **partial read**, -65183 B vs the baseline |
| `core\object\editor_language.h` | 1865 | 10774 | staging is a **partial read**, -8909 B vs the baseline |
| `core\object\gdtype.cpp` | 1852 | 10154 | staging is a **partial read**, -8302 B vs the baseline |
| `core\object\message_queue.cpp` | 2273 | 14914 | staging is a **partial read**, -12641 B vs the baseline |
| `core\object\object.cpp` | 32067 | 79088 | staging is a **partial read**, -47021 B vs the baseline |
| `core\object\object.h` | 14072 | 48292 | staging is a **partial read**, -34220 B vs the baseline |
| `core\object\object_id.h` | 1309 | 3624 | staging is a **partial read**, -2315 B vs the baseline |
| `core\object\property_info.h` | 4459 | 9824 | staging is a **partial read**, -5365 B vs the baseline |
| `core\object\ref_counted.h` | 1092 | 7386 | staging is a **partial read**, -6294 B vs the baseline |
| `core\object\script_instance.cpp` | 1037 | 3725 | staging is a **partial read**, -2688 B vs the baseline |
| `core\object\script_language.cpp` | 5114 | 25501 | staging is a **partial read**, -20387 B vs the baseline |
| `core\object\script_language.h` | 5322 | 16780 | staging is a **partial read**, -11458 B vs the baseline |
| `core\os\keyboard.cpp` | 1513 | 16397 | staging is a **partial read**, -14884 B vs the baseline |
| `core\os\main_loop.cpp` | 1411 | 3645 | staging is a **partial read**, -2234 B vs the baseline |
| `core\os\os.cpp` | 991 | 22754 | staging is a **partial read**, -21763 B vs the baseline |
| `core\os\process_id.h` | 61 | 2295 | staging is a **partial read**, -2234 B vs the baseline |
| `core\string\node_path.cpp` | 1784 | 12350 | staging is a **partial read**, -10566 B vs the baseline |
| `core\string\ustring.cpp` | 14215 | 141112 | staging is a **partial read**, -126897 B vs the baseline |
| `core\templates\safe_refcount.h` | 2311 | 7746 | staging is a **partial read**, -5435 B vs the baseline |
| `core\templates\vector.h` | 2598 | 11720 | staging is a **partial read**, -9122 B vs the baseline |
| `core\variant\binder_common.h` | 1425 | 32593 | staging is a **partial read**, -31168 B vs the baseline |
| `core\variant\callable.cpp` | 2961 | 17058 | staging is a **partial read**, -14097 B vs the baseline |
| `core\variant\callable.h` | 3065 | 8607 | staging is a **partial read**, -5542 B vs the baseline |
| `core\variant\callable_bind.h` | 2842 | 5232 | staging is a **partial read**, -2390 B vs the baseline |
| `core\variant\variant.cpp` | 25077 | 96152 | staging is a **partial read**, -71075 B vs the baseline |
| `core\variant\variant.h` | 2166 | 35262 | staging is a **partial read**, -33096 B vs the baseline |
| `core\variant\variant_op.cpp` | 642 | 94750 | staging is a **partial read**, -94108 B vs the baseline |
| `core\variant\variant_parser.cpp` | 13422 | 71686 | staging is a **partial read**, -58264 B vs the baseline |
| `core\variant\variant_setget.cpp` | 10104 | 64043 | staging is a **partial read**, -53939 B vs the baseline |
| `core\variant\variant_utility.cpp` | 3591 | 67064 | staging is a **partial read**, -63473 B vs the baseline |
| `core\version.h` | 4865 | 5777 | staging is a **partial read**, -912 B vs the baseline |
| `drivers\gles3\storage\texture_storage.cpp` | 721 | 148425 | staging is a **partial read**, -147704 B vs the baseline |
| `drivers\png\png_driver_common.cpp` | 4521 | 7760 | staging is a **partial read**, -3239 B vs the baseline |
| `drivers\unix\dir_access_unix.cpp` | 1472 | 18169 | staging is a **partial read**, -16697 B vs the baseline |
| `drivers\windows\dir_access_windows.cpp` | 6980 | 17989 | staging is a **partial read**, -11009 B vs the baseline |
| `drivers\windows\file_access_windows.cpp` | 1626 | 21974 | staging is a **partial read**, -20348 B vs the baseline |
| `drivers\windows\file_access_windows_pipe.cpp` | 3221 | 5519 | staging is a **partial read**, -2298 B vs the baseline |
| `drivers\windows\net_socket_winsock.cpp` | 308 | 18880 | staging is a **partial read**, -18572 B vs the baseline |
| `editor\SCsub` | 1260 | 3423 | staging is a **partial read**, -2163 B vs the baseline |
| `editor\editor_data.h` | 2097 | 13891 | staging is a **partial read**, -11794 B vs the baseline |
| `editor\editor_interface.cpp` | 2556 | 41104 | staging is a **partial read**, -38548 B vs the baseline |
| `editor\editor_interface.h` | 4391 | 9308 | staging is a **partial read**, -4917 B vs the baseline |
| `editor\editor_log.cpp` | 12094 | 23505 | staging is a **partial read**, -11411 B vs the baseline |
| `editor\editor_node.cpp` | 27932 | 389353 | staging is a **partial read**, -361421 B vs the baseline |
| `editor\editor_node.h` | 1701 | 38939 | staging is a **partial read**, -37238 B vs the baseline |
| `editor\export\android_sdk_manager.cpp` | 8007 | 33160 | staging is a **partial read**, -25153 B vs the baseline |
| `editor\export\editor_export.cpp` | 810 | 19363 | staging is a **partial read**, -18553 B vs the baseline |
| `editor\export\editor_export.h` | 1814 | 4839 | staging is a **partial read**, -3025 B vs the baseline |
| `editor\file_system\editor_file_system.cpp` | 2451 | 128067 | staging is a **partial read**, -125616 B vs the baseline |
| `editor\project_manager\project_list.cpp` | 2653 | 59826 | staging is a **partial read**, -57173 B vs the baseline |
| `editor\run\editor_run_bar.cpp` | 4952 | 31705 | staging is a **partial read**, -26753 B vs the baseline |
| `editor\script\script_editor_plugin.cpp` | 1837 | 162046 | staging is a **partial read**, -160209 B vs the baseline |
| `editor\settings\editor_settings.cpp` | 1636 | 124344 | staging is a **partial read**, -122708 B vs the baseline |
| `editor\settings\project_settings_editor.cpp` | 2185 | 35485 | staging is a **partial read**, -33300 B vs the baseline |
| `main\main.cpp` | 30590 | 213308 | staging is a **partial read**, -182718 B vs the baseline |
| `main\main.h` | 708 | 4462 | staging is a **partial read**, -3754 B vs the baseline |
| `main\performance.cpp` | 2662 | 26713 | staging is a **partial read**, -24051 B vs the baseline |
| `modules\gdscript\gdscript.cpp` | 15093 | 87346 | staging is a **partial read**, -72253 B vs the baseline |
| `modules\gdscript\gdscript_compiler.cpp` | 5467 | 132782 | staging is a **partial read**, -127315 B vs the baseline |
| `modules\gdscript\gdscript_parser.cpp` | 4464 | 230230 | staging is a **partial read**, -225766 B vs the baseline |
| `modules\gdscript\gdscript_resource_format.cpp` | 691 | 7560 | staging is a **partial read**, -6869 B vs the baseline |
| `modules\gdscript\register_types.cpp` | 1551 | 8785 | staging is a **partial read**, -7234 B vs the baseline |
| `modules\mono\csharp_script.cpp` | 12973 | 86199 | staging is a **partial read**, -73226 B vs the baseline |
| `modules\mono\csharp_script.h` | 10026 | 20978 | staging is a **partial read**, -10952 B vs the baseline |
| `modules\mono\csharp_script_resource_format.cpp` | 2737 | 6538 | staging is a **partial read**, -3801 B vs the baseline |
| `modules\mono\editor\Godot.NET.Sdk\Godot.SourceGenerators\ScriptPathAttributeGenerator.cs` | 2815 | 8165 | staging is a **partial read**, -5350 B vs the baseline |
| `modules\mono\editor\GodotTools\GodotTools\Build\BuildSystem.cs` | 4401 | 14721 | staging is a **partial read**, -10320 B vs the baseline |
| `modules\mono\editor\bindings_generator.cpp` | 1690 | 196869 | staging is a **partial read**, -195179 B vs the baseline |
| `modules\mono\glue\GodotSharp\GodotSharp\Core\Bridge\ScriptManagerBridge.cs` | 2993 | 52426 | staging is a **partial read**, -49433 B vs the baseline |
| `modules\mono\godotsharp_dirs.cpp` | 4872 | 9597 | staging is a **partial read**, -4725 B vs the baseline |
| `modules\mono\mono_gd\gd_mono.cpp` | 3827 | 29959 | staging is a **partial read**, -26132 B vs the baseline |
| `modules\navigation_3d\3d\godot_navigation_server_3d.cpp` | 3639 | 49607 | staging is a **partial read**, -45968 B vs the baseline |
| `modules\navigation_3d\3d\nav_mesh_generator_3d.cpp` | 7405 | 25911 | staging is a **partial read**, -18506 B vs the baseline |
| `modules\tilemap\tile_map_layer.h` | 4651 | 23754 | staging is a **partial read**, -19103 B vs the baseline |
| `platform\windows\console_wrapper_windows.cpp` | 2373 | 7062 | staging is a **partial read**, -4689 B vs the baseline |
| `platform\windows\os_windows.cpp` | 5916 | 95612 | staging is a **partial read**, -89696 B vs the baseline |
| `scene\2d\gpu_particles_2d.cpp` | 671 | 41176 | staging is a **partial read**, -40505 B vs the baseline |
| `scene\2d\physics\collision_shape_2d.cpp` | 791 | 12770 | staging is a **partial read**, -11979 B vs the baseline |
| `scene\3d\camera_3d.cpp` | 2320 | 32852 | staging is a **partial read**, -30532 B vs the baseline |
| `scene\3d\mesh_instance_3d.cpp` | 2417 | 36881 | staging is a **partial read**, -34464 B vs the baseline |
| `scene\3d\navigation\navigation_region_3d.cpp` | 3295 | 29084 | staging is a **partial read**, -25789 B vs the baseline |
| `scene\animation\animation_blend_tree.cpp` | 1732 | 75170 | staging is a **partial read**, -73438 B vs the baseline |
| `scene\animation\animation_blend_tree.h` | 3062 | 18886 | staging is a **partial read**, -15824 B vs the baseline |
| `scene\animation\animation_mixer.cpp` | 3825 | 97269 | staging is a **partial read**, -93444 B vs the baseline |
| `scene\animation\animation_node_state_machine.cpp` | 3512 | 75810 | staging is a **partial read**, -72298 B vs the baseline |
| `scene\animation\animation_node_state_machine.h` | 5253 | 15008 | staging is a **partial read**, -9755 B vs the baseline |
| `scene\animation\animation_tree.cpp` | 5595 | 43184 | staging is a **partial read**, -37589 B vs the baseline |
| `scene\gui\control.cpp` | 8597 | 190439 | staging is a **partial read**, -181842 B vs the baseline |
| `scene\gui\rich_text_label.cpp` | 722 | 297390 | staging is a **partial read**, -296668 B vs the baseline |
| `scene\main\node.cpp` | 13159 | 132086 | staging is a **partial read**, -118927 B vs the baseline |
| `scene\main\node.h` | 518 | 37851 | staging is a **partial read**, -37333 B vs the baseline |
| `scene\main\scene_tree.cpp` | 10331 | 75974 | staging is a **partial read**, -65643 B vs the baseline |
| `scene\main\viewport.cpp` | 1028 | 201763 | staging is a **partial read**, -200735 B vs the baseline |
| `scene\resources\animation.cpp` | 3443 | 224493 | staging is a **partial read**, -221050 B vs the baseline |
| `scene\resources\animation.h` | 3112 | 28470 | staging is a **partial read**, -25358 B vs the baseline |
| `scene\resources\animation_library.h` | 1226 | 3587 | staging is a **partial read**, -2361 B vs the baseline |
| `scene\resources\compressed_texture_resource_format.cpp` | 937 | 5593 | staging is a **partial read**, -4656 B vs the baseline |
| `scene\resources\curve.cpp` | 549 | 76893 | staging is a **partial read**, -76344 B vs the baseline |
| `scene\resources\gradient.cpp` | 2848 | 8174 | staging is a **partial read**, -5326 B vs the baseline |
| `scene\resources\material.cpp` | 9609 | 155748 | staging is a **partial read**, -146139 B vs the baseline |
| `scene\resources\packed_scene.cpp` | 1911 | 87951 | staging is a **partial read**, -86040 B vs the baseline |
| `scene\resources\particle_process_material.h` | 4347 | 19420 | staging is a **partial read**, -15073 B vs the baseline |
| `scene\resources\resource_format_text.cpp` | 7532 | 67768 | staging is a **partial read**, -60236 B vs the baseline |
| `scene\resources\style_box.h` | 1394 | 3628 | staging is a **partial read**, -2234 B vs the baseline |
| `scene\resources\style_box_flat.cpp` | 2161 | 33819 | staging is a **partial read**, -31658 B vs the baseline |
| `scene\resources\style_box_flat.h` | 2330 | 4658 | staging is a **partial read**, -2328 B vs the baseline |
| `scene\resources\theme.cpp` | 14926 | 67544 | staging is a **partial read**, -52618 B vs the baseline |
| `servers\audio\audio_bus_layout.h` | 681 | 2915 | staging is a **partial read**, -2234 B vs the baseline |
| `servers\audio\audio_server.cpp` | 9684 | 67591 | staging is a **partial read**, -57907 B vs the baseline |
| `servers\display\display_server_headless.cpp` | 1367 | 3601 | staging is a **partial read**, -2234 B vs the baseline |
| `servers\movie_writer\movie_writer_pngwav.cpp` | 918 | 6265 | staging is a **partial read**, -5347 B vs the baseline |
| `servers\server_wrap_mt_common.h` | 479 | 29322 | staging is a **partial read**, -28843 B vs the baseline |
| `tests\core\io\test_config_file.cpp` | 1141 | 6729 | staging is a **partial read**, -5588 B vs the baseline |
| `tests\core\io\test_image.cpp` | 1492 | 20497 | staging is a **partial read**, -19005 B vs the baseline |
| `tests\core\io\test_logger.cpp` | 2323 | 7030 | staging is a **partial read**, -4707 B vs the baseline |
| `tests\test_macros.h` | 4048 | 9958 | staging is a **partial read**, -5910 B vs the baseline |
| `thirdparty\README.md` | 557 | 41154 | staging is a **partial read**, -40597 B vs the baseline |
| `thirdparty\doctest\doctest.h` | 1229 | 323308 | staging is a **partial read**, -322079 B vs the baseline |
| `thirdparty\libpng\pngwrite.c` | 1055 | 78819 | staging is a **partial read**, -77764 B vs the baseline |

Totals: **30** fragments are effectively identical to the baseline (only the final newline / CRLF-vs-LF difference), **2** are complete reads differing only by BOM/CRLF + BOM-bearing files, **2** are complete reads whose content is a build log, and **157** are partial reads strictly smaller than the baseline copy.
In no case is a staged fragment larger than the baseline file, so no staged engine fragment
could be a newer complete revision; and except for the two build logs, no skipped engine
fragment carries content the baseline lacks.

#### EOL-normalisation finding (important for later byte-exact work)

The staging pipeline stored text with **LF** endings and no BOM, while the baseline files carry
**CRLF** and (for the .NET SDK files) a **UTF-8 BOM**.  Example:

| file | staged | baseline |
|---|---|---|
| `modules\mono\editor\Godot.NET.Sdk\Godot.NET.Sdk\Godot.NET.Sdk.csproj` | 1,863 B, 42 LF, no BOM | 1,910 B, 43 CRLF, BOM |
| `core\SCsub` | 10,010 B, 295 LF | 10,011 B, 296 LF |

After stripping the BOM and normalising EOLs the two `.csproj` files are **identical line for
line**, so the ~44-47 B deltas are BOM+CRLF, not content.  Therefore any byte-level diff between
`rebuild\godot` and a future restored tree will show the same artifacts — compare content, not
raw bytes, unless the EOLs are first re-normalised.  This is also why `.gitattributes` matters
here (see the module evidence doc `GIT-EOL-NORMALIZATION.md`).

### 4.3 Staged paths with no payload (N=1410 = 1406 out-of-repo + 4 in-repo)

Out-of-repo payloads are excluded by design; the in-repo ones are the real gaps:

| path | status | reason |
|---|---|---|
| `modules\mcp_server\scripts\mcp063_product_defects_eviditedu.ps1` | 缺失 | no staged payload (wrote=false) |
| `modules\mcp_server\tests\test_mcp_server.tscn` | 缺失 | no staged payload (wrote=false) |
| `modules\mcp_server\tools\__up__\__up__\__up__\modules\mcp_server\scripts\mcp070_mono_csharp_evidence.ps1` | 缺失 | no staged payload (wrote=false) |
| `modules\mcp_server\tools\__up__\tests\test_mcp_server.h` | 缺失 | no staged payload (wrote=false) |

(1406 further paths are `__external\...`, i.e. out-of-repo payloads for other projects; they stay
in `staging\` and are not part of this tree by definition.)

## 5. Known module files that were never staged (N=516)

TASK-078 left `work\module-listing-missing.txt`: paths that appear in the captured module
listing but have **no** staged payload.  Everything below is **evidence or cache**, not source —
no `tools\*.cpp/h`, no `scripts\*.ps1/py` in this list:

| extension | count |
|---|---:|
| `.json` | 377 |
| `.log` | 108 |
| `.txt` | 20 |
| `.pyc` | 4 |
| `.md` | 4 |
| `.jsonl` | 1 |
| `.patch` | 1 |
| `.rewritten` | 1 |

| group | count | example |
|---|---:|---|
| `modules\mcp_server\docs\reports\evidence\racing` | 173 | `modules\mcp_server\docs\reports\evidence\racing\0012-editor_add_nodes_batch.response.json` |
| `modules\mcp_server\docs\reports\evidence\task051` | 162 | `modules\mcp_server\docs\reports\evidence\task051\green\final-sweep.txt` |
| `modules\mcp_server\docs\reports\evidence\task041` | 48 | `modules\mcp_server\docs\reports\evidence\task041\index.md` |
| `modules\mcp_server\docs\reports\evidence\task043` | 45 | `modules\mcp_server\docs\reports\evidence\task043\contract\contract-diff.json` |
| `modules\mcp_server\docs\reports\evidence\task042` | 42 | `modules\mcp_server\docs\reports\evidence\task042\gates\gate1_contract_subset.log` |
| `modules\mcp_server\docs\reports\evidence\task040` | 33 | `modules\mcp_server\docs\reports\evidence\task040\green\a02_add_resource_on_missing_property.response.json` |
| `modules\mcp_server\docs\reports\evidence\task050` | 7 | `modules\mcp_server\docs\reports\evidence\task050\green\e01_chain_create_cs.request.json` |
| `modules\mcp_server\scripts\__pycache__` | 3 | `modules\mcp_server\scripts\__pycache__\check_narrowing_points.cpython-39.pyc` |
| `modules\mcp_server\__pycache__` | 1 | `modules\mcp_server\__pycache__\config.cpython-39.pyc` |
| `modules\mcp_server\docs\reports\evidence\task050rts` | 1 | `modules\mcp_server\docs\reports\evidence\task050rts\evidence\task051\green\editor-tools_list.response.json` |
| `modules\mcp_server\tor_add_nodes_batch.request.json` | 1 | `modules\mcp_server\tor_add_nodes_batch.request.json` |

Caveat: that listing was captured from a terminal dump that was itself truncated
(`work\module-listing-raw.txt` ends with "Omitted 14,352 bytes" — some of the paths below are
themselves cut mid-name), so **516 is a lower bound**, not the complete set of unstaged module
files.

Full list in the appendix below.

## 6. Parseability spot check

Every `.py` in the tree was put through `ast.parse`; every `.ps1` through
`[System.Management.Automation.Language.Parser]::ParseFile` (parse only, never executed).

| area | `.py` total | `.py` ok | `.py` failed | `.ps1` total | `.ps1` with errors |
|---|---:|---:|---:|---:|---:|
| `rebuild\godot` | 228 | 228 | 0 | 129 | 6 |
| `rebuild\_low-confidence` | 7 | 4 | 3 | 10 | 2 |
| `staging\` (TASK-078 set, for comparison) | 458 | 455 | 3 | 433 | 10 |

### 6.1 Comparison with the TASK-078 numbers

| check | TASK-078 recorded | reproduced now | verdict |
|---|---|---|---|
| `.py` | 453 pass / 3 fail | **455 / 3** over 458 candidates | 3 failures match exactly; the "453" is 2 lower than a straight sweep of the same index — unexplained 2-file delta, see below |
| `.ps1` | 433 parsed / 10 errors | **433 / 10** | exact match |

The same three `.py` files fail in every sweep:

| file | line | error |
|---|---:|---|
| `methods.py` (staging) | 60 | SyntaxError: EOF while scanning triple-quoted string literal |
| `modules\mono\build_scripts\build_assemblies.py` (staging) | 74 | IndentationError: unindent does not match any outer indentation level |
| `platform\windows\detect.py` (staging) | 1 | IndentationError: unexpected indent |

All three are **engine-side** partial reads (`methods.py` at the repo root,
`modules\mono\build_scripts\build_assemblies.py`, `platform\windows\detect.py`) — which is
exactly why they were parked in `_low-confidence`.  In `rebuild\godot` the baseline provides the
complete original of all three, so **`rebuild\godot` has 0 `.py` failures**.

The 2-file delta: a sweep of the current `reconstruction.jsonl` yields 458 `.py` paths, all of
which exist in staging (455 ok + 3 syntax errors).  The TASK-078 headline "453 pass" sums to
456, i.e. two files that were counted differently then (most likely `missing` at the time) — the
index has since been regenerated.  No file is hidden by this; the per-file failure list above is
the authoritative statement.  Flagged rather than papered over.

### 6.2 `.ps1` failures in `rebuild\godot` (6 of 129)

| file | errors | first error | line |
|---|---:|---|---:|
| `modules\mcp_server\docs\reports\evidence\task060\trace-recovered\scripts\mcp060_lib.ps1` | 2 | MissingEndCurlyBrace:Missing closing '}' in statement block or type definition. | 175 |
| `modules\mcp_server\scripts\accept_m1.ps1` | 10 | MissingCatchOrFinally:The Try statement is missing its Catch or Finally block. | 644 |
| `modules\mcp_server\scripts\mcp022_unified_narrowing_gate_evidence.ps1` | 6 | MissingExpressionAfterToken:Missing expression after ','. | 557 |
| `modules\mcp_server\scripts\mcp027_object_shape_and_paths_evidence.ps1` | 3 | MissingEndCurlyBrace:Missing closing '}' in statement block or type definition. | 312 |
| `modules\mcp_server\scripts\mcp053_added_tools_evidence.ps1` | 6 | ExpectedValueExpression:You must provide a value expression following the '-and' operator. | 260 |
| `modules\mcp_server\scripts\mcp067_live.ps1` | 1 | MissingEndCurlyBrace:Missing closing '}' in statement block or type definition. | 95 |

All six are staged MID-confidence payloads with interior lines missing (coverage 51-84%), which
is precisely why they do not parse.  The two LOW-confidence `.ps1` failures are in
`_low-confidence` and therefore not in the tree:

* `modules\mcp_server\scripts\mcp019_b4_evidence.ps1` — 1 errors, first at line 182: MissingEndCurlyBrace:Missing closing '}' in statement block or type definition.
* `modules\mcp_server\scripts\mcp023_narrowing_guardrail_evidence.ps1` — 8 errors, first at line 7: UnexpectedToken:Unexpected token ')' in expression or statement.

## 7. Not-landed inventory (未落地清单)

| class | count | where it is | why |
|---|---:|---|---|
| LOW-confidence payloads moved to `_low-confidence` (41) + 2 truncated docs variants kept for audit | 43 | `rebuild\_low-confidence\` | confidence rule: must not pollute the tree |
| `.git/` scratch file | 1 | `rebuild\_excluded\` | not repository content |
| staged fragments not overlaid (baseline already complete) | 191 | `staging\` | overlaying would regress a complete file |
| out-of-repo payloads | 1406 | `staging\__external\` | belong to other projects, not this tree |
| indexed paths with no payload | 39 | (nothing anywhere) | the transcripts never contained usable bytes |
| `__history` versions | 4,543 | `staging\__history\` | kept in staging by instruction |
| `__candidates` alternative reconstructions | 296 | `staging\__candidates\` | kept in staging |
| `bin\obj` + `__pycache__` | 3168 | (only in the audit002 baseline) | regenerable build artifacts |

## 8. The docs/contract assets (rule 4)

| repo path | source | bytes | sha256 | stale? | note |
|---|---|---:|---|---|---|
| `modules\mcp_server\docs\tools_list.renamed.json` | `%TEMP%\mcp044-module-backup\mcp_server\docs\tools_list.renamed.json` | 118032 | `443f1df2e9a3c5b0a2ad1c4ce532a4cfb6f33d22d0401a02448a0ca0bede914f` | **YES** | staging copy is a truncated read-epoch (20.3% coverage, tail missing) -> full copy taken from the TASK-044 module backup. _meta lists 171 tools, NOT the final 176; RECOVERY-PLAN 4.2 requires regeneration by scripts/gen_renamed_contract.py, do not trust this copy. |
| `modules\mcp_server\docs\tool-rename-map.json` | `%TEMP%\mcp044-module-backup\mcp_server\docs\tool-rename-map.json` | 70917 | `2f552719f6a23fe328df0a2944c6048824c1b2a750aebc0fe2cabbcd3529c2bd` | no | staging copy is a truncated read-epoch (14.8% coverage, tail missing) -> full copy from the TASK-044 module backup; sha256 matches _meta.map_sha256 of the tools_list.renamed.json contracts, so this is the last known good map. |
| `_refs\legacy-174\tools_list.json` | `F:\moonbit-hof-rs\tests\fixtures\mcp\tools_list.json` | 48749 | `8f8051c4c0f8941089f0b21a193cef7c51fa7c41d7e312b1463ea8593f313c54` | no | READ-ONLY from the intact outer repo F:\moonbit-hof-rs; 174 tools; its sha256 equals _meta.generated_from_sha256 of the renamed contract, i.e. this is the legacy 174-tool generator input. |

The two truncated staging variants of the docs assets were kept (in `_low-confidence`) for audit
instead of being deleted.  Note that `modules\mcp_server\docs\tools_list.renamed.json` in the
tree is a **171-tool** copy from the TASK-044 backup, not the final contract:
RECOVERY-PLAN §4.2 requires it to be regenerated, and the legacy generator input (174 tools,
sha256 `8f8051c4c0f8941089f0b21a193cef7c51fa7c41d7e312b1463ea8593f313c54`) is parked at
`rebuild\_refs\legacy-174\tools_list.json` — that file was read from **F: read-only**, it was
not written to F:.

## 9. Reproduce this result

```powershell
$R = "C:\Users\wyl\AppData\Local\Temp\mcp-recovery"
python "$R\scripts\assemble_rebuild_2a.py"      # baseline copy + overlay (idempotent, resume-safe)
python "$R\scripts\parse_check_rebuild_py.py"   # ast.parse over every .py
&      "$R\scripts\parse_check_rebuild_ps1.ps1" # PowerShell parser over every .ps1
&      "$R\scripts\patch_dryrun2.ps1"           # ordered patch dry run in an isolated sandbox
python "$R\scripts\gen_manifest.py"             # this document
```

Evidence files: `work\assembly-stats.json`, `work\parse-py.json`,
`work\parse-ps1-rebuild.json`, `work\patch-info.json`, `work\fcheck-pre.txt`,
`work\fcheck-post.txt`, `work\drift-detail.txt`.

## 10. What stage 2b must fix, in priority order

1. `modules\mcp_server\tools\registration.cpp` — build blocker; start from the complete-looking LOW copy and re-check the 42 failed edits.
2. `modules\mcp_server\tests\test_mcp_server.h` — the gate-3 harness (9,626 lines).
3. `modules\mcp_server\scripts\gen_renamed_contract.py` — needed to regenerate the contract.
4. `modules\mcp_server\scripts\accept_m1.ps1` — 10 parse errors, gate 5.
5. The other LOW module sources (`tool_helpers.cpp`, `editor_write_scene_editor.cpp`, `project_write_resource_scene.cpp`, `running_game_*`, `editor_playback.cpp`, …).
6. `docs\DESIGN-DETAIL.md` and the remaining LOW docs/JSON.
7. Re-apply the three engine patches (see `ENGINE-PATCHES-TO-REAPPLY.md`), then build.
8. Re-normalise EOLs before any byte-exact comparison with a restored tree.

## Appendix A — staged paths that appear in the module listing but were never staged

```text
modules\mcp_server\__pycache__\config.cpython-39.pyc
modules\mcp_server\docs\reports\evidence\racing\0012-editor_add_nodes_batch.response.json
modules\mcp_server\docs\reports\evidence\racing\0012-editor_setup_collision_shape.request.json
modules\mcp_server\docs\reports\evidence\racing\0012-editor_setup_collision_shape.response.json
modules\mcp_server\docs\reports\evidence\racing\0012-project_validate_script.request.json
modules\mcp_server\docs\reports\evidence\racing\0012-project_validate_script.response.json
modules\mcp_server\docs\reports\evidence\racing\0012-running_game_get_node_properties.request.json
modules\mcp_server\docs\reports\evidence\racing\0012-running_game_get_node_properties.response.json
modules\mcp_server\docs\reports\evidence\racing\0012-running_game_run_test_scenario.request.json
modules\mcp_server\docs\reports\evidence\racing\0012-running_game_run_test_scenario.response.json
modules\mcp_server\docs\reports\evidence\racing\0013-editor_setup_collision_shape.request.json
modules\mcp_server\docs\reports\evidence\racing\0013-editor_setup_collision_shape.response.json
modules\mcp_server\docs\reports\evidence\racing\0013-project_validate_script.request.json
modules\mcp_server\docs\reports\evidence\racing\0013-project_validate_script.response.json
modules\mcp_server\docs\reports\evidence\racing\0014-editor_setup_collision_shape.request.json
modules\mcp_server\docs\reports\evidence\racing\0014-editor_setup_collision_shape.response.json
modules\mcp_server\docs\reports\evidence\racing\0014-project_validate_script.request.json
modules\mcp_server\docs\reports\evidence\racing\0014-project_validate_script.response.json
modules\mcp_server\docs\reports\evidence\racing\0014-running_game_get_autoload_node.request.json
modules\mcp_server\docs\reports\evidence\racing\0014-running_game_get_autoload_node.response.json
modules\mcp_server\docs\reports\evidence\racing\0014-running_game_get_node_properties.request.json
modules\mcp_server\docs\reports\evidence\racing\0014-running_game_get_node_properties.response.json
modules\mcp_server\docs\reports\evidence\racing\0014-running_game_run_test_scenario.request.json
modules\mcp_server\docs\reports\evidence\racing\0014-running_game_run_test_scenario.response.json
modules\mcp_server\docs\reports\evidence\racing\0015-running_game_find_nearby_nodes.request.json
modules\mcp_server\docs\reports\evidence\racing\0015-running_game_find_nearby_nodes.response.json
modules\mcp_server\docs\reports\evidence\racing\0015-running_game_get_node_properties.request.json
modules\mcp_server\docs\reports\evidence\racing\0015-running_game_get_node_properties.response.json
modules\mcp_server\docs\reports\evidence\racing\0015-running_game_get_node_property_samples.request.json
modules\mcp_server\docs\reports\evidence\racing\0015-running_game_get_node_property_samples.response.json
modules\mcp_server\docs\reports\evidence\racing\0016-running_game_run_test_scenario.request.json
modules\mcp_server\docs\reports\evidence\racing\0016-running_game_run_test_scenario.response.json
modules\mcp_server\docs\reports\evidence\racing\0016-running_game_set_node_property.request.json
modules\mcp_server\docs\reports\evidence\racing\0016-running_game_set_node_property.response.json
modules\mcp_server\docs\reports\evidence\racing\0016-running_game_simulate_button_click_by_text.request.json
modules\mcp_server\docs\reports\evidence\racing\0016-running_game_simulate_button_click_by_text.response.json
modules\mcp_server\docs\reports\evidence\racing\0017-running_game_get_node_properties.request.json
modules\mcp_server\docs\reports\evidence\racing\0017-running_game_get_node_properties.response.json
modules\mcp_server\docs\reports\evidence\racing\0017-running_game_move_player_to_target.request.json
modules\mcp_server\docs\reports\evidence\racing\0017-running_game_move_player_to_target.response.json
modules\mcp_server\docs\reports\evidence\racing\0017-running_game_run_test_scenario.request.json
modules\mcp_server\docs\reports\evidence\racing\0017-running_game_run_test_scenario.response.json
modules\mcp_server\docs\reports\evidence\racing\0018-running_game_get_node_properties.request.json
modules\mcp_server\docs\reports\evidence\racing\0018-running_game_get_node_properties.response.json
modules\mcp_server\docs\reports\evidence\racing\0018-running_game_get_node_property_samples.request.json
modules\mcp_server\docs\reports\evidence\racing\0018-running_game_get_node_property_samples.response.json
modules\mcp_server\docs\reports\evidence\racing\0019-editor_connect_signal.request.json
modules\mcp_server\docs\reports\evidence\racing\0019-editor_connect_signal.response.json
modules\mcp_server\docs\reports\evidence\racing\0019-running_game_run_test_scenario.request.json
modules\mcp_server\docs\reports\evidence\racing\0019-running_game_run_test_scenario.response.json
modules\mcp_server\docs\reports\evidence\racing\0020-editor_connect_signal.request.json
modules\mcp_server\docs\reports\evidence\racing\0020-editor_connect_signal.response.json
modules\mcp_server\docs\reports\evidence\racing\0020-running_game_get_node_properties.request.json
modules\mcp_server\docs\reports\evidence\racing\0020-running_game_get_node_properties.response.json
modules\mcp_server\docs\reports\evidence\racing\0021-editor_connect_signal.request.json
modules\mcp_server\docs\reports\evidence\racing\0021-editor_connect_signal.response.json
modules\mcp_server\docs\reports\evidence\racing\0021-running_game_get_node_properties.request.json
modules\mcp_server\docs\reports\evidence\racing\0021-running_game_get_node_properties.response.json
modules\mcp_server\docs\reports\evidence\racing\0022-editor_connect_signal.request.json
modules\mcp_server\docs\reports\evidence\racing\0022-editor_connect_signal.response.json
modules\mcp_server\docs\reports\evidence\racing\0022-running_game_run_test_scenario.request.json
modules\mcp_server\docs\reports\evidence\racing\0022-running_game_run_test_scenario.response.json
modules\mcp_server\docs\reports\evidence\racing\0023-editor_list_signal_connections.request.json
modules\mcp_server\docs\reports\evidence\racing\0023-editor_list_signal_connections.response.json
modules\mcp_server\docs\reports\evidence\racing\0023-running_game_get_node_properties.request.json
modules\mcp_server\docs\reports\evidence\racing\0023-running_game_get_node_properties.response.json
modules\mcp_server\docs\reports\evidence\racing\0024-editor_list_signal_connections.request.json
modules\mcp_server\docs\reports\evidence\racing\0024-editor_list_signal_connections.response.json
modules\mcp_server\docs\reports\evidence\racing\0024-editor_simulate_key.request.json
modules\mcp_server\docs\reports\evidence\racing\0024-editor_simulate_key.response.json
modules\mcp_server\docs\reports\evidence\racing\0025-editor_analyze_signal_flow.request.json
modules\mcp_server\docs\reports\evidence\racing\0025-editor_analyze_signal_flow.response.json
modules\mcp_server\docs\reports\evidence\racing\0025-editor_simulate_input_action.request.json
modules\mcp_server\docs\reports\evidence\racing\0025-editor_simulate_input_action.response.json
modules\mcp_server\docs\reports\evidence\racing\0025-running_game_run_test_scenario.request.json
modules\mcp_server\docs\reports\evidence\racing\0025-running_game_run_test_scenario.response.json
modules\mcp_server\docs\reports\evidence\racing\0026-editor_analyze_screenshot_diff.request.json
modules\mcp_server\docs\reports\evidence\racing\0026-editor_analyze_screenshot_diff.response.json
modules\mcp_server\docs\reports\evidence\racing\0026-editor_simulate_input_sequence.request.json
modules\mcp_server\docs\reports\evidence\racing\0026-editor_simulate_input_sequence.response.json
modules\mcp_server\docs\reports\evidence\racing\0027-editor_analyze_screenshot_diff.request.json
modules\mcp_server\docs\reports\evidence\racing\0027-editor_analyze_screenshot_diff.response.json
modules\mcp_server\docs\reports\evidence\racing\0028-editor_analyze_screenshot_diff.request.json
modules\mcp_server\docs\reports\evidence\racing\0028-editor_analyze_screenshot_diff.response.json
modules\mcp_server\docs\reports\evidence\racing\0028-project_read_scene_file_content.request.json
modules\mcp_server\docs\reports\evidence\racing\0028-project_read_scene_file_content.response.json
modules\mcp_server\docs\reports\evidence\racing\0029-running_game_run_test_scenario.request.json
modules\mcp_server\docs\reports\evidence\racing\0029-running_game_run_test_scenario.response.json
modules\mcp_server\docs\reports\evidence\racing\0030-running_game_run_test_scenario.request.json
modules\mcp_server\docs\reports\evidence\racing\0030-running_game_run_test_scenario.response.json
modules\mcp_server\docs\reports\evidence\racing\0031-project_validate_script.request.json
modules\mcp_server\docs\reports\evidence\racing\0031-project_validate_script.response.json
modules\mcp_server\docs\reports\evidence\racing\0032-editor_setup_collision_shape.request.json
modules\mcp_server\docs\reports\evidence\racing\0032-editor_setup_collision_shape.response.json
modules\mcp_server\docs\reports\evidence\racing\0032-running_game_run_test_scenario.request.json
modules\mcp_server\docs\reports\evidence\racing\0032-running_game_run_test_scenario.response.json
modules\mcp_server\docs\reports\evidence\racing\0033-editor_setup_collision_shape.request.json
modules\mcp_server\docs\reports\evidence\racing\0033-editor_setup_collision_shape.response.json
modules\mcp_server\docs\reports\evidence\racing\0033-project_validate_script.request.json
modules\mcp_server\docs\reports\evidence\racing\0033-project_validate_script.response.json
modules\mcp_server\docs\reports\evidence\racing\0033-running_game_run_test_scenario.request.json
modules\mcp_server\docs\reports\evidence\racing\0033-running_game_run_test_scenario.response.json
modules\mcp_server\docs\reports\evidence\racing\0034-editor_setup_collision_shape.request.json
modules\mcp_server\docs\reports\evidence\racing\0034-editor_setup_collision_shape.response.json
modules\mcp_server\docs\reports\evidence\racing\0034-project_read_scene_file_content.request.json
modules\mcp_server\docs\reports\evidence\racing\0034-project_read_scene_file_content.response.json
modules\mcp_server\docs\reports\evidence\racing\0034-running_game_capture_screenshot.request.json
modules\mcp_server\docs\reports\evidence\racing\0034-running_game_capture_screenshot.response.json
modules\mcp_server\docs\reports\evidence\racing\0035-editor_setup_collision_shape.request.json
modules\mcp_server\docs\reports\evidence\racing\0035-editor_setup_collision_shape.response.json
modules\mcp_server\docs\reports\evidence\racing\0036-editor_setup_collision_shape.request.json
modules\mcp_server\docs\reports\evidence\racing\0036-editor_setup_collision_shape.response.json
modules\mcp_server\docs\reports\evidence\racing\0036-project_read_scene_file_content.request.json
modules\mcp_server\docs\reports\evidence\racing\0036-project_read_scene_file_content.response.json
modules\mcp_server\docs\reports\evidence\racing\0036-running_game_run_test_scenario.request.json
modules\mcp_server\docs\reports\evidence\racing\0036-running_game_run_test_scenario.response.json
modules\mcp_server\docs\reports\evidence\racing\0037-editor_setup_collision_shape.request.json
modules\mcp_server\docs\reports\evidence\racing\0037-editor_setup_collision_shape.response.json
modules\mcp_server\docs\reports\evidence\racing\0037-running_game_capture_screenshot.request.json
modules\mcp_server\docs\reports\evidence\racing\0037-running_game_capture_screenshot.response.json
modules\mcp_server\docs\reports\evidence\racing\0038-running_game_capture_frames.request.json
modules\mcp_server\docs\reports\evidence\racing\0038-running_game_capture_frames.response.json
modules\mcp_server\docs\reports\evidence\racing\0039-running_game_run_test_scenario.request.json
modules\mcp_server\docs\reports\evidence\racing\0039-running_game_run_test_scenario.response.json
modules\mcp_server\docs\reports\evidence\racing\0040-editor_analyze_screenshot_diff.request.json
modules\mcp_server\docs\reports\evidence\racing\0040-editor_analyze_screenshot_diff.response.json
modules\mcp_server\docs\reports\evidence\racing\0041-editor_capture_screenshot.request.json
modules\mcp_server\docs\reports\evidence\racing\0041-editor_capture_screenshot.response.json
modules\mcp_server\docs\reports\evidence\racing\0043-running_game_run_test_scenario.request.json
modules\mcp_server\docs\reports\evidence\racing\0043-running_game_run_test_scenario.response.json
modules\mcp_server\docs\reports\evidence\racing\0045-editor_connect_signal.request.json
modules\mcp_server\docs\reports\evidence\racing\0045-editor_connect_signal.response.json
modules\mcp_server\docs\reports\evidence\racing\0045-running_game_run_test_scenario.request.json
modules\mcp_server\docs\reports\evidence\racing\0045-running_game_run_test_scenario.response.json
modules\mcp_server\docs\reports\evidence\racing\0046-editor_connect_signal.request.json
modules\mcp_server\docs\reports\evidence\racing\0046-editor_connect_signal.response.json
modules\mcp_server\docs\reports\evidence\racing\0047-editor_connect_signal.request.json
modules\mcp_server\docs\reports\evidence\racing\0047-editor_connect_signal.response.json
modules\mcp_server\docs\reports\evidence\racing\0047-running_game_run_test_scenario.request.json
modules\mcp_server\docs\reports\evidence\racing\0047-running_game_run_test_scenario.response.json
modules\mcp_server\docs\reports\evidence\racing\0048-editor_connect_signal.request.json
modules\mcp_server\docs\reports\evidence\racing\0048-editor_connect_signal.response.json
modules\mcp_server\docs\reports\evidence\racing\0049-editor_connect_signal.request.json
modules\mcp_server\docs\reports\evidence\racing\0049-editor_connect_signal.response.json
modules\mcp_server\docs\reports\evidence\racing\0050-editor_list_signal_connections.request.json
modules\mcp_server\docs\reports\evidence\racing\0050-editor_list_signal_connections.response.json
modules\mcp_server\docs\reports\evidence\racing\0051-editor_analyze_signal_flow.request.json
modules\mcp_server\docs\reports\evidence\racing\0051-editor_analyze_signal_flow.response.json
modules\mcp_server\docs\reports\evidence\racing\0052-editor_analyze_signal_flow.request.json
modules\mcp_server\docs\reports\evidence\racing\0052-editor_analyze_signal_flow.response.json
modules\mcp_server\docs\reports\evidence\racing\0061-editor_add_resource_to_node_property.request.json
modules\mcp_server\docs\reports\evidence\racing\0061-editor_add_resource_to_node_property.response.json
modules\mcp_server\docs\reports\evidence\racing\0075-editor_add_input_action.request.json
modules\mcp_server\docs\reports\evidence\racing\0075-editor_add_input_action.response.json
modules\mcp_server\docs\reports\evidence\racing\0076-editor_add_input_action.request.json
modules\mcp_server\docs\reports\evidence\racing\0076-editor_add_input_action.response.json
modules\mcp_server\docs\reports\evidence\racing\0079-project_read_scene_file_content.request.json
modules\mcp_server\docs\reports\evidence\racing\0079-project_read_scene_file_content.response.json
modules\mcp_server\docs\reports\evidence\racing\ac-1-dotnet-build.log
modules\mcp_server\docs\reports\evidence\racing\ac-1-scene-content-from-tool.txt
modules\mcp_server\docs\reports\evidence\racing\ac-4-continuity-metrics.txt
modules\mcp_server\docs\reports\evidence\racing\ac-4-samples-car.json
modules\mcp_server\docs\reports\evidence\racing\ac-5-samples-laptimer-negative.json
modules\mcp_server\docs\reports\evidence\racing\ac-5-samples-laptimer-positive.json
modules\mcp_server\docs\reports\evidence\racing\ac-6-capture-signals.json
modules\mcp_server\docs\reports\evidence\racing\ac-7-screenshot-diff.json
modules\mcp_server\docs\reports\evidence\racing\ac-8-car-property-list.json
modules\mcp_server\docs\reports\evidence\racing\ac-9-tools-list-comparison.txt
modules\mcp_server\docs\reports\evidence\racing\ac-9-tools_list-editor.json
modules\mcp_server\docs\reports\evidence\racing\ac-9-tools_list-game.json
modules\mcp_server\docs\reports\evidence\racing\ac-metrics.txt
modules\mcp_server\docs\reports\evidence\racing\call-log.jsonl
modules\mcp_server\docs\reports\evidence\racing\e-1-headless-game.out.log
modules\mcp_server\docs\reports\evidence\racing\evidence-index.json
modules\mcp_server\docs\reports\evidence\task040\green\a02_add_resource_on_missing_property.response.json
modules\mcp_server\docs\reports\evidence\task040\green\a03_add_resource_wrong_category.response.json
modules\mcp_server\docs\reports\evidence\task040\green\a08_connect_signal.response.json
modules\mcp_server\docs\reports\evidence\task040\green\a10_save_scene_with_connection.response.json
modules\mcp_server\docs\reports\evidence\task040\green\accept_m1-comparison.txt
modules\mcp_server\docs\reports\evidence\task040\green\accept_m1_run1.log
modules\mcp_server\docs\reports\evidence\task040\green\accept_m1_run2.log
modules\mcp_server\docs\reports\evidence\task040\green\b01_list_connections_after_restart.response.json
modules\mcp_server\docs\reports\evidence\task040\green\b03_disconnect_signal.response.json
modules\mcp_server\docs\reports\evidence\task040\green\c01_game_read_missing_name.response.json
modules\mcp_server\docs\reports\evidence\task040\green\c05_game_read_batch.response.json
modules\mcp_server\docs\reports\evidence\task040\green\gate1_editor_node_write.log
modules\mcp_server\docs\reports\evidence\task040\green\gate1_editor_write_scene_editor.log
modules\mcp_server\docs\reports\evidence\task040\green\gate1_running_game_observation.log
modules\mcp_server\docs\reports\evidence\task040\green\gate2_fix.log
modules\mcp_server\docs\reports\evidence\task040\green\gate3_final.log
modules\mcp_server\docs\reports\evidence\task040\green\gate4_final.log
modules\mcp_server\docs\reports\evidence\task040\green\gate6c.log
modules\mcp_server\docs\reports\evidence\task040\green\probe-checks.json
modules\mcp_server\docs\reports\evidence\task040\green\r02_connect_start_button.response.json
modules\mcp_server\docs\reports\evidence\task040\green\r09_read_scene_file.response.json
modules\mcp_server\docs\reports\evidence\task040\green\r15_read_flag_fired.response.json
modules\mcp_server\docs\reports\evidence\task040\green\racing-checks.json
modules\mcp_server\docs\reports\evidence\task040\green\racing-regression.log
modules\mcp_server\docs\reports\evidence\task040\readme.md
modules\mcp_server\docs\reports\evidence\task040\red\a02_add_resource_on_missing_property.response.json
modules\mcp_server\docs\reports\evidence\task040\red\a03_add_resource_wrong_category.response.json
modules\mcp_server\docs\reports\evidence\task040\red\a08_connect_signal.response.json
modules\mcp_server\docs\reports\evidence\task040\red\a10_save_scene_with_connection.response.json
modules\mcp_server\docs\reports\evidence\task040\red\b01_list_connections_after_restart.response.json
modules\mcp_server\docs\reports\evidence\task040\red\c01_game_read_missing_name.response.json
modules\mcp_server\docs\reports\evidence\task040\red\doctest-red.log
modules\mcp_server\docs\reports\evidence\task040\regression-attribution.txt
modules\mcp_server\docs\reports\evidence\task041\index.md
modules\mcp_server\docs\reports\evidence\task041\inputmap\b02_list_before.request.json
modules\mcp_server\docs\reports\evidence\task041\inputmap\b02_list_before.response.json
modules\mcp_server\docs\reports\evidence\task041\inputmap\b03_add_input_action.request.json
modules\mcp_server\docs\reports\evidence\task041\inputmap\b03_add_input_action.response.json
modules\mcp_server\docs\reports\evidence\task041\inputmap\b10_add_again.request.json
modules\mcp_server\docs\reports\evidence\task041\inputmap\b10_add_again.response.json
modules\mcp_server\docs\reports\evidence\task041\inputmap\b11_add_without_key.request.json
modules\mcp_server\docs\reports\evidence\task041\inputmap\b11_add_without_key.response.json
modules\mcp_server\docs\reports\evidence\task041\inputmap\b12_add_dotted_name.request.json
modules\mcp_server\docs\reports\evidence\task041\inputmap\b12_add_dotted_name.response.json
modules\mcp_server\docs\reports\evidence\task041\inputmap\b13_list_after.request.json
modules\mcp_server\docs\reports\evidence\task041\inputmap\b13_list_after.response.json
modules\mcp_server\docs\reports\evidence\task041\inputmap\c01_play_scene.request.json
modules\mcp_server\docs\reports\evidence\task041\inputmap\c01_play_scene.response.json
modules\mcp_server\docs\reports\evidence\task041\inputmap\c03_game_has_action.request.json
modules\mcp_server\docs\reports\evidence\task041\inputmap\c03_game_has_action.response.json
modules\mcp_server\docs\reports\evidence\task041\inputmap\c04_game_action_event_count.request.json
modules\mcp_server\docs\reports\evidence\task041\inputmap\c04_game_action_event_count.response.json
modules\mcp_server\docs\reports\evidence\task041\inputmap\c05_game_does_not_have_the_rejected_name.request.json
modules\mcp_server\docs\reports\evidence\task041\inputmap\c05_game_does_not_have_the_rejected_name.response.json
modules\mcp_server\docs\reports\evidence\task041\inputmap\c06_stop_scene.request.json
modules\mcp_server\docs\reports\evidence\task041\inputmap\c06_stop_scene.response.json
modules\mcp_server\docs\reports\evidence\task041\inputmap\checks.json
modules\mcp_server\docs\reports\evidence\task041\inputmap\d02_direct_game_has_action.request.json
modules\mcp_server\docs\reports\evidence\task041\inputmap\d02_direct_game_has_action.response.json
modules\mcp_server\docs\reports\evidence\task041\inputmap\d03_direct_game_event_count.request.json
modules\mcp_server\docs\reports\evidence\task041\inputmap\d03_direct_game_event_count.response.json
modules\mcp_server\docs\reports\evidence\task041\inputmap\d04_direct_game_rejected_name_absent.request.json
modules\mcp_server\docs\reports\evidence\task041\inputmap\d04_direct_game_rejected_name_absent.response.json
modules\mcp_server\docs\reports\evidence\task041\inputmap\e02_editor2_list.request.json
modules\mcp_server\docs\reports\evidence\task041\inputmap\e02_editor2_list.response.json
modules\mcp_server\docs\reports\evidence\task041\inputmap\status-51550.json
modules\mcp_server\docs\reports\evidence\task041\inputmap\status-9888.json
modules\mcp_server\docs\reports\evidence\task041\inputmap\status-9889.json
modules\mcp_server\docs\reports\evidence\task041\inputmap\z4_add_builtin_ui_accept.request.json
modules\mcp_server\docs\reports\evidence\task041\inputmap\z4_add_builtin_ui_accept.response.json
modules\mcp_server\docs\reports\evidence\task041\logs\doctest-green-inputmap.log
modules\mcp_server\docs\reports\evidence\task041\logs\doctest-green-task041.log
modules\mcp_server\docs\reports\evidence\task041\logs\doctest-red-behaviour.log
modules\mcp_server\docs\reports\evidence\task041\logs\gate-battery-summary.txt
modules\mcp_server\docs\reports\evidence\task041\logs\gate1-contract-subset.log
modules\mcp_server\docs\reports\evidence\task041\logs\gate2-wire-evidence.log
modules\mcp_server\docs\reports\evidence\task041\logs\gate3-module-doctest.log
modules\mcp_server\docs\reports\evidence\task041\logs\gate4-full-doctest.log
modules\mcp_server\docs\reports\evidence\task041\logs\gate6a-narrowing.log
modules\mcp_server\docs\reports\evidence\task041\logs\gate6b-narrowing-coverage.log
modules\mcp_server\docs\reports\evidence\task041\logs\gate6c-coverage-probes.log
modules\mcp_server\docs\reports\evidence\task042\gates\gate1_contract_subset.log
modules\mcp_server\docs\reports\evidence\task042\gates\gate2_rewrite_and_honesty_evidence.log
modules\mcp_server\docs\reports\evidence\task042\gates\gate2b_port_guard_probes.log
modules\mcp_server\docs\reports\evidence\task042\gates\gate2c_task041_evidence.log
modules\mcp_server\docs\reports\evidence\task042\gates\gate3_module_doctest.log
modules\mcp_server\docs\reports\evidence\task042\gates\gate4_full_doctest.log
modules\mcp_server\docs\reports\evidence\task042\gates\gate5_accept_run1.log
modules\mcp_server\docs\reports\evidence\task042\gates\gate5_accept_run2.log
modules\mcp_server\docs\reports\evidence\task042\gates\gate6a_narrowing.log
modules\mcp_server\docs\reports\evidence\task042\gates\gate6b_narrowing_coverage.log
modules\mcp_server\docs\reports\evidence\task042\gates\gate6c_coverage_probes.log
modules\mcp_server\docs\reports\evidence\task042\gates\gates-console.log
modules\mcp_server\docs\reports\evidence\task042\gates\regress_mcp032.log
modules\mcp_server\docs\reports\evidence\task042\gates\regress_mcp033.log
modules\mcp_server\docs\reports\evidence\task042\gates\regress_mcp034.log
modules\mcp_server\docs\reports\evidence\task042\gates\regress_mcp035.log
modules\mcp_server\docs\reports\evidence\task042\gates\regress_mcp036.log
modules\mcp_server\docs\reports\evidence\task042\gates\regress_mcp040_probes.log
modules\mcp_server\docs\reports\evidence\task042\gates\regress_mcp040_racing.log
modules\mcp_server\docs\reports\evidence\task042\gates\regress_probe037.log
modules\mcp_server\docs\reports\evidence\task042\gates\summary.txt
modules\mcp_server\docs\reports\evidence\task042\index.md
modules\mcp_server\docs\reports\evidence\task042\logs\green-a.log
modules\mcp_server\docs\reports\evidence\task042\logs\green-b2.log
modules\mcp_server\docs\reports\evidence\task042\logs\red-a.log
modules\mcp_server\docs\reports\evidence\task042\probes\mcp042-port-guard-checks.json
modules\mcp_server\docs\reports\evidence\task042\rewrite\a20_add_action.request.json
modules\mcp_server\docs\reports\evidence\task042\rewrite\a20_add_action.response.json
modules\mcp_server\docs\reports\evidence\task042\rewrite\a27_add_again.request.json
modules\mcp_server\docs\reports\evidence\task042\rewrite\a27_add_again.response.json
modules\mcp_server\docs\reports\evidence\task042\rewrite\a29_add_builtin_ui_accept.request.json
modules\mcp_server\docs\reports\evidence\task042\rewrite\a29_add_builtin_ui_accept.response.json
modules\mcp_server\docs\reports\evidence\task042\rewrite\b11_game_has_spliced_action.request.json
modules\mcp_server\docs\reports\evidence\task042\rewrite\b11_game_has_spliced_action.response.json
modules\mcp_server\docs\reports\evidence\task042\rewrite\b12_game_spliced_event_count.request.json
modules\mcp_server\docs\reports\evidence\task042\rewrite\b12_game_spliced_event_count.response.json
modules\mcp_server\docs\reports\evidence\task042\rewrite\b13_game_preexisting_action.request.json
modules\mcp_server\docs\reports\evidence\task042\rewrite\b13_game_preexisting_action.response.json
modules\mcp_server\docs\reports\evidence\task042\rewrite\mcp042-rewrite-summary.json
modules\mcp_server\docs\reports\evidence\task042\rewrite\project-godot-rewrite-diff.txt
modules\mcp_server\docs\reports\evidence\task042\rewrite\status-9888.json
modules\mcp_server\docs\reports\evidence\task042\rewrite\status-9889.json
modules\mcp_server\docs\reports\evidence\task043\contract\contract-diff.json
modules\mcp_server\docs\reports\evidence\task043\contract\groups.txt
modules\mcp_server\docs\reports\evidence\task043\contract\registration-literals.json
modules\mcp_server\docs\reports\evidence\task043\contract\survey.txt
modules\mcp_server\docs\reports\evidence\task043\contract\tools-diff-numstat.txt
modules\mcp_server\docs\reports\evidence\task043\contract\tools-diff-shape.json
modules\mcp_server\docs\reports\evidence\task043\contract\tools-diff-u0.patch
modules\mcp_server\docs\reports\evidence\task043\contract\tools_list.after.json
modules\mcp_server\docs\reports\evidence\task043\contract\tools_list.before.json
modules\mcp_server\docs\reports\evidence\task043\gates\gate1a_contract_group_editor_write_scene_editor.log
modules\mcp_server\docs\reports\evidence\task043\gates\gate1b_contract_group_project_setting_write.log
modules\mcp_server\docs\reports\evidence\task043\gates\gate1c_contract_group_project_autoload_write.log
modules\mcp_server\docs\reports\evidence\task043\gates\gate1d_contract_group_editor_input_simulation.log
modules\mcp_server\docs\reports\evidence\task043\gates\gate2a_description_evidence.log
modules\mcp_server\docs\reports\evidence\task043\gates\gate2b_reload_plugin_probe.log
modules\mcp_server\docs\reports\evidence\task043\gates\gate2c_probe037_d2d1r1r2.log
modules\mcp_server\docs\reports\evidence\task043\gates\gate2d_rewrite_evidence.log
modules\mcp_server\docs\reports\evidence\task043\gates\gate2e_task041_evidence.log
modules\mcp_server\docs\reports\evidence\task043\gates\gate2f_port_guard_probes.log
modules\mcp_server\docs\reports\evidence\task043\gates\gate2f_snapshot_before_contract.log
modules\mcp_server\docs\reports\evidence\task043\gates\gate2g_contract_diff.log
modules\mcp_server\docs\reports\evidence\task043\gates\gate2h_registration_literals.log
modules\mcp_server\docs\reports\evidence\task043\gates\gate2i_group_lookup.log
modules\mcp_server\docs\reports\evidence\task043\gates\gate3_module_doctest.log
modules\mcp_server\docs\reports\evidence\task043\gates\gate4_full_doctest.log
modules\mcp_server\docs\reports\evidence\task043\gates\gate5_accept_run1.log
modules\mcp_server\docs\reports\evidence\task043\gates\gate5_accept_run2.log
modules\mcp_server\docs\reports\evidence\task043\gates\gate6a_narrowing.log
modules\mcp_server\docs\reports\evidence\task043\gates\gate6b_narrowing_coverage.log
modules\mcp_server\docs\reports\evidence\task043\gates\gate6c_coverage_probes.log
modules\mcp_server\docs\reports\evidence\task043\gates\regress_mcp032.log
modules\mcp_server\docs\reports\evidence\task043\gates\regress_mcp033.log
modules\mcp_server\docs\reports\evidence\task043\gates\regress_mcp034.log
modules\mcp_server\docs\reports\evidence\task043\gates\regress_mcp035.log
modules\mcp_server\docs\reports\evidence\task043\gates\regress_mcp036.log
modules\mcp_server\docs\reports\evidence\task043\gates\regress_mcp040_probes.log
modules\mcp_server\docs\reports\evidence\task043\gates\regress_mcp040_racing.log
modules\mcp_server\docs\reports\evidence\task043\gates\summary.txt
modules\mcp_server\docs\reports\evidence\task043\index.md
modules\mcp_server\docs\reports\evidence\task043\live\mcp043-description-checks.json
modules\mcp_server\docs\reports\evidence\task043\live\tools_list.response.json
modules\mcp_server\docs\reports\evidence\task043\reload\mcp043-reload-probe-checks.json
modules\mcp_server\docs\reports\evidence\task043\reload\p20_reload_plugin.response.json
modules\mcp_server\docs\reports\evidence\task043\reload\p25_reload_again.response.json
modules\mcp_server\docs\reports\evidence\task043\reload\project.godot.rewritten
modules\mcp_server\docs\reports\evidence\task050\green\e01_chain_create_cs.request.json
modules\mcp_server\docs\reports\evidence\task050\green\e01_chain_create_cs.response.json
modules\mcp_server\docs\reports\evidence\task050\green\e02_chain_read_cs.request.json
modules\mcp_server\docs\reports\evidence\task050\green\e02_chain_read_cs.response.json
modules\mcp_server\docs\reports\evidence\task050\green\e03_n2_validate_cs.request.json
modules\mcp_server\docs\reports\evidence\task050\green\e03_n2_validate_cs.response.json
modules\mcp_server\docs\reports\evidence\task050\green\e04_validate_gd_valid.request.json
modules\mcp_server\docs\reports\evidence\task050rts\evidence\task051\green\editor-tools_list.response.json
modules\mcp_server\docs\reports\evidence\task051\green\final-sweep.txt
modules\mcp_server\docs\reports\evidence\task051\green\g01_o5_input_with_pressed.request.json
modules\mcp_server\docs\reports\evidence\task051\green\g01_o5_input_with_pressed.response.json
modules\mcp_server\docs\reports\evidence\task051\green\g02_o5_input_release.request.json
modules\mcp_server\docs\reports\evidence\task051\green\g02_o5_input_release.response.json
modules\mcp_server\docs\reports\evidence\task051\green\game-tools_list.request.json
modules\mcp_server\docs\reports\evidence\task051\green\game-tools_list.response.json
modules\mcp_server\docs\reports\evidence\task051\green\gate1\editor_input_simulation.log
modules\mcp_server\docs\reports\evidence\task051\green\gate1\editor_node_batch_write.log
modules\mcp_server\docs\reports\evidence\task051\green\gate1\editor_node_read.log
modules\mcp_server\docs\reports\evidence\task051\green\gate1\editor_playback.log
modules\mcp_server\docs\reports\evidence\task051\green\gate1\running_game_test_execution.log
modules\mcp_server\docs\reports\evidence\task051\green\gate1\summary.txt
modules\mcp_server\docs\reports\evidence\task051\green\gate1_postcommit_editor_playback.log
modules\mcp_server\docs\reports\evidence\task051\green\gate1_union.log
modules\mcp_server\docs\reports\evidence\task051\green\gate3_first_attempt_failures.log
modules\mcp_server\docs\reports\evidence\task051\green\gate3_module_doctests.log
modules\mcp_server\docs\reports\evidence\task051\green\gate3_postcommit_rebuild.log
modules\mcp_server\docs\reports\evidence\task051\green\gate4_full_engine_tests.log
modules\mcp_server\docs\reports\evidence\task051\green\gate4_postcommit_rebuild.log
modules\mcp_server\docs\reports\evidence\task051\green\gate5a_accept_m1_run1.log
modules\mcp_server\docs\reports\evidence\task051\green\gate5b_accept_m1_run2.log
modules\mcp_server\docs\reports\evidence\task051\green\gate6a_narrowing_points.log
modules\mcp_server\docs\reports\evidence\task051\green\gate6b_narrowing_coverage.log
modules\mcp_server\docs\reports\evidence\task051\green\gate6c_gate6_coverage_probes.log
modules\mcp_server\docs\reports\evidence\task051\green\regression\gate6c_coverage_probes.log
modules\mcp_server\docs\reports\evidence\task051\green\regression\regress_mcp010_b2_observation.log
modules\mcp_server\docs\reports\evidence\task051\green\regression\regress_mcp019_b4.log
modules\mcp_server\docs\reports\evidence\task051\green\regression\regress_mcp027_object_shape_and_paths.log
modules\mcp_server\docs\reports\evidence\task051\green\regression\regress_mcp041_gates.log
modules\mcp_server\docs\reports\evidence\task051\green\regression\regress_mcp042_gates.log
modules\mcp_server\docs\reports\evidence\task051\green\regression\regress_mcp043_gates.log
modules\mcp_server\docs\reports\evidence\task051\green\regression\regress_mcp044_capture_diff_image.log
modules\mcp_server\docs\reports\evidence\task051\green\regression\regress_mcp044_capture_editor.log
modules\mcp_server\docs\reports\evidence\task051\green\regression\regress_mcp044_capture_game.log
modules\mcp_server\docs\reports\evidence\task051\green\regression\regress_mcp044_capture_headless.log
modules\mcp_server\docs\reports\evidence\task051\green\regression\regress_mcp045_pixel_compare_cost.log
modules\mcp_server\docs\reports\evidence\task051\green\regression\regress_mcp046_capture_encode_cost.log
modules\mcp_server\docs\reports\evidence\task051\green\regression\regress_mcp050_contract_diff.log
modules\mcp_server\docs\reports\evidence\task051\green\regression\regress_mcp050_parameter_guidance.log
modules\mcp_server\docs\reports\evidence\task051\green\regression\summary-batteries.txt
modules\mcp_server\docs\reports\evidence\task051\green\regression\summary-capture.txt
modules\mcp_server\docs\reports\evidence\task051\green\regression\summary-individual.txt
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\e01_chain_create_cs.request.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\e01_chain_create_cs.response.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\e02_chain_read_cs.request.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\e02_chain_read_cs.response.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\e03_n2_validate_cs.request.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\e03_n2_validate_cs.response.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\e04_validate_gd_valid.request.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\e04_validate_gd_valid.response.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\e05_validate_gd_broken.request.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\e05_validate_gd_broken.response.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\e06_validate_missing_param.request.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\e06_validate_missing_param.response.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\e07_validate_missing_file.request.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\e07_validate_missing_file.response.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\e08_missing_required_immediate.request.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\e08_missing_required_immediate.response.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\e09_missing_required_two.request.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\e09_missing_required_two.response.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\e10_missing_required_deferred.request.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\e10_missing_required_deferred.response.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\e11_empty_required_deferred.request.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\e11_empty_required_deferred.response.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\e12_nested_missing_type.request.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\e12_nested_missing_type.response.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\e13_nested_type_error.request.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\e13_nested_type_error.response.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\e14_type_error_top.request.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\e14_type_error_top.response.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\e15_unknown_parameter.request.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\e15_unknown_parameter.response.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\e16_empty_required_value.request.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\e16_empty_required_value.response.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\e17_open_scene.request.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\e17_open_scene.response.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\e17b_batch_own_suggestion.request.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\e17b_batch_own_suggestion.response.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\e18_enum_value.request.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\e18_enum_value.response.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\e19_unknown_tool.request.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\e19_unknown_tool.response.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\e20_chain_read_cs_after.request.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\e20_chain_read_cs_after.response.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\g01_missing_required_immediate.request.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\g01_missing_required_immediate.response.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\g02_missing_required_deferred.request.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\g02_missing_required_deferred.response.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\g03_empty_required_deferred.request.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\g03_empty_required_deferred.response.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\g04_nested_enum_error.request.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\g04_nested_enum_error.response.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\g05_nested_missing_type.request.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\g05_nested_missing_type.response.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\g06_nested_type_mismatch.request.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\g06_nested_type_mismatch.response.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\g07_bare_array_nested.request.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\g07_bare_array_nested.response.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\g08_game_type_error.request.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\g08_game_type_error.response.json
modules\mcp_server\docs\reports\evidence\task051\green\regression\task050-evidence-rerun\summary.json
modules\mcp_server\docs\reports\evidence\task051\green\run.log
modules\mcp_server\docs\reports\evidence\task051\green\summary-gates.txt
modules\mcp_server\docs\reports\evidence\task051\green\summary.json
modules\mcp_server\docs\reports\evidence\task051\green\wire-verbatim-check.txt
modules\mcp_server\docs\reports\evidence\task051\red\e01_open_scene.request.json
modules\mcp_server\docs\reports\evidence\task051\red\e01_open_scene.response.json
modules\mcp_server\docs\reports\evidence\task051\red\e02_o9_default_scope.request.json
modules\mcp_server\docs\reports\evidence\task051\red\e02_o9_default_scope.response.json
modules\mcp_server\docs\reports\evidence\task051\red\e03_o9_scope_user.request.json
modules\mcp_server\docs\reports\evidence\task051\red\e03_o9_scope_user.response.json
modules\mcp_server\docs\reports\evidence\task051\red\e04_o9_scope_internal.request.json
modules\mcp_server\docs\reports\evidence\task051\red\e04_o9_scope_internal.response.json
modules\mcp_server\docs\reports\evidence\task051\red\e05_o9_scope_bogus.request.json
modules\mcp_server\docs\reports\evidence\task051\red\e05_o9_scope_bogus.response.json
modules\mcp_server\docs\reports\evidence\task051\red\e06_o9_signal_name_filter.request.json
modules\mcp_server\docs\reports\evidence\task051\red\e06_o9_signal_name_filter.response.json
modules\mcp_server\docs\reports\evidence\task051\red\e07_o9_scope_and_filter.request.json
modules\mcp_server\docs\reports\evidence\task051\red\e07_o9_scope_and_filter.response.json
modules\mcp_server\docs\reports\evidence\task051\red\e08_c3_default_mode_refuses.request.json
modules\mcp_server\docs\reports\evidence\task051\red\e08_c3_default_mode_refuses.response.json
modules\mcp_server\docs\reports\evidence\task051\red\e09_c3_same_batch_parent.request.json
modules\mcp_server\docs\reports\evidence\task051\red\e09_c3_same_batch_parent.response.json
modules\mcp_server\docs\reports\evidence\task051\red\e10_c3_chain_get_scene_tree.request.json
modules\mcp_server\docs\reports\evidence\task051\red\e10_c3_chain_get_scene_tree.response.json
modules\mcp_server\docs\reports\evidence\task051\red\e11_c3_chain_get_properties.request.json
modules\mcp_server\docs\reports\evidence\task051\red\e11_c3_chain_get_properties.response.json
modules\mcp_server\docs\reports\evidence\task051\red\e12_c3_forward_reference.request.json
modules\mcp_server\docs\reports\evidence\task051\red\e12_c3_forward_reference.response.json
modules\mcp_server\docs\reports\evidence\task051\red\e13_c3_duplicate_name.request.json
modules\mcp_server\docs\reports\evidence\task051\red\e13_c3_duplicate_name.response.json
modules\mcp_server\docs\reports\evidence\task051\red\e14_c3_unknown_parent.request.json
modules\mcp_server\docs\reports\evidence\task051\red\e14_c3_unknown_parent.response.json
modules\mcp_server\docs\reports\evidence\task051\red\e15_o4_events_missing_type.request.json
modules\mcp_server\docs\reports\evidence\task051\red\e15_o4_events_missing_type.response.json
modules\mcp_server\docs\reports\evidence\task051\red\e16_o4_events_with_type.request.json
modules\mcp_server\docs\reports\evidence\task051\red\e16_o4_events_with_type.response.json
modules\mcp_server\docs\reports\evidence\task051\red\e17_m3_headless_type_error.request.json
modules\mcp_server\docs\reports\evidence\task051\red\e17_m3_headless_type_error.response.json
modules\mcp_server\docs\reports\evidence\task051\red\e18_m3_port_in_extra_args.request.json
modules\mcp_server\docs\reports\evidence\task051\red\e18_m3_port_in_extra_args.response.json
modules\mcp_server\docs\reports\evidence\task051\red\e19_m3_extra_args_type.request.json
modules\mcp_server\docs\reports\evidence\task051\red\e19_m3_extra_args_type.response.json
modules\mcp_server\docs\reports\evidence\task051\red\e20_m3_headless_launch.request.json
modules\mcp_server\docs\reports\evidence\task051\red\e20_m3_headless_launch.response.json
modules\mcp_server\docs\reports\evidence\task051\red\e21_m3_stop_scene.request.json
modules\mcp_server\docs\reports\evidence\task051\red\e21_m3_stop_scene.response.json
modules\mcp_server\docs\reports\evidence\task051\red\e22_m3_headless_dedup.request.json
modules\mcp_server\docs\reports\evidence\task051\red\e22_m3_headless_dedup.response.json
modules\mcp_server\docs\reports\evidence\task051\red\e23_m3_stop_scene.request.json
modules\mcp_server\docs\reports\evidence\task051\red\e23_m3_stop_scene.response.json
modules\mcp_server\docs\reports\evidence\task051\red\editor-tools_list.request.json
modules\mcp_server\docs\reports\evidence\task051\red\editor-tools_list.response.json
modules\mcp_server\docs\reports\evidence\task051\red\g01_o5_input_with_pressed.request.json
modules\mcp_server\docs\reports\evidence\task051\red\g01_o5_input_with_pressed.response.json
modules\mcp_server\docs\reports\evidence\task051\red\g02_o5_input_release.request.json
modules\mcp_server\docs\reports\evidence\task051\red\g02_o5_input_release.response.json
modules\mcp_server\docs\reports\evidence\task051\red\game-tools_list.request.json
modules\mcp_server\docs\reports\evidence\task051\red\game-tools_list.response.json
modules\mcp_server\docs\reports\evidence\task051\red\run.log
modules\mcp_server\docs\reports\evidence\task051\red\summary.json
modules\mcp_server\scripts\__pycache__\check_narrowing_points.cpython-39.pyc
modules\mcp_server\scripts\__pycache__\gen_b2_game_schema.cpython-39.pyc
modules\mcp_server\scripts\__pycache__\gen_renamed_contract.cpython-39.pyc
modules\mcp_server\tor_add_nodes_batch.request.json
```
