# TASK-094 — D-1 (the frozen viewport readback) located and bounded, the pixel-evidence question answered, D-2 fixed and measured

* Executor: game/tool engineer (this session, **write access, no further delegation**)
* Main repo: `F:\moonbit-hof-rs` (branch `master`, no remote)
* Engine repo: `F:\moonbit-hof-rs\godot-mcp\godot` (branch `feature/mcp-server-module-rebuild`,
  remote `git@github.com:shiyukonghui/godot.git`)
* Scripts / logs / intermediates: `godot-mcp\recovery\work\task094\`
* Time: 2026-09-27, 01:00–03:10

---

## 0. Verdicts, one line each

| Section | Requirement | Verdict | Evidence |
|---|---|---|---|
| **A①** | Locate D-1, give a reproducible minimal counter-example | **Done.** Minimal counter-example: set `Background.color` to blue → red → green (the property really changes; read back in-process) and take one screenshot after each: **three byte-identical PNGs, and all three show the *original* dark background**. Reproduces with `--mcp-capture=off`, i.e. without the capture engine | `recovery\work\task094\sessions\repro2\session.json`; `runs\snake\task094-probe{3,4,5,9}` |
| **A②** | Fix it (module defect → change the module; environment/driver → evidence why it is not our code) | **Not our code — and not fixable from `modules/mcp_server`.** The images are frozen *inside the engine*: `Viewport::get_texture()->get_image()` returns the process's **first rendered frame** forever, while `Engine.get_frames_drawn()` advances and the renderer's own per-frame counts track the scene (objects 57 → 157 after adding 100 `ColorRect`s). The same binary bytes and the **same session file** produced 10/29 non-zero capture lines at 00:14:47 and 0/29 at 02:00 | §A3, §A4 |
| **A③** | After the fix: same-session pixel diff non-zero and consistent with an independent recomputation; before/after side by side | **Not achievable in this environment.** Every readback path in the process returns frame 1, so a "fixed" pixel diff cannot be produced. The before/after pair is recorded instead, and the recomputation is *not* dressed up as agreement | §A5, §B |
| **A④** | If engine/environment: a bypass, pinned with evidence | **Four bypasses tried, all fail**: `--rendering-driver opengl3`, `--rendering-driver d3d12`, `RenderingServer.force_draw(true, 0.0)` + `force_sync()`, and the OS-level window grab (`CopyFromScreen` and `PrintWindow`). The OS-level grabs are shown to be *unusable* independently of D-1 (two different engines give the same grab bytes) | §A5 |
| **B** | Backfill the pixel-diff column for Breakout / Snake (and recheck Pong) | **Blocked by D-1.** The replayed runs are on disk with their real `changed_pixels=0`; the column stays 0 and points at D-1 — **no "recomputed == reported" claim is made**, because both sides are the same frozen picture | §B |
| **C** | D-2: test brittleness or real defect; if brittle, make the wait deterministic; one solo + one parallel measurement | **Test brittleness — fixed.** The predicate asked for *≥ 20 frames per 1000 ms*, a throughput requirement. Replaced by "frame_count strictly increasing 6 samples in a row at 250 ms" — readiness, not speed. **Solo: 22/22, exit 0, 50.8 s. Under 8 CPU burners on 16 vCPU: 22/22, exit 0, 55.3 s** | §C, `runs\gates\task094-alone\`, `runs\gates\task094-load2\` |
| **D** | 4th game (Tetris) if A–C are done and there is room | **Not started.** A–C consumed the whole budget; D-1 alone took ~70 minutes including four eliminated bypasses | §D |
| **E** | Rebuild both variants if the module changed, ten gates green with real exit codes, `accept_m1` 22/22; push the engine repo; commit the main repo; report both `git log`/`git status`; report honestly where it stopped | Ten gates are in `runs\gates\task094\` (§E1). The only engine-repo change is a **PowerShell script** (`accept_m1.ps1`), which no object file depends on — **no compiled byte changed, so no rebuild was run**; that decision and its consequence for gate 9 are stated in §E1 rather than hidden. Pong/accept numbers below | §E |

---

## A. D-1: the frozen viewport readback

### A1 The minimal counter-example (fixed picture content, deterministic)

`recovery\work\task094\sessions\repro2\session.json` — four moves, no dependence on whether the
game survives:

```
y01-blue   running_game_set_node_property  Background.color = (0,0,1,1)   -> blue
y02-shot   running_game_capture_screenshot user://repro-a.png
y03-red    running_game_set_node_property  Background.color = (1,0,0,1)   -> red
y04-shot   running_game_capture_screenshot user://repro-b.png
y05-green  running_game_set_node_property  Background.color = (0,1,0,1)   -> green
y06-shot   running_game_capture_screenshot user://repro-c.png
y07-read   execute_gdscript: return the real property and a readback checksum
```

Measured (`--mcp-capture=off`, unique port 9891, all Godot processes killed first, no bind warning):

```
y07: background_color=(0.0, 1.0, 0.0, 1.0)     <- the scene really is green
repro-a.png  bytes=3111  sha256=D5C3A72ABA6F525C
repro-b.png  bytes=3111  sha256=D5C3A72ABA6F525C
repro-c.png  bytes=3111  sha256=D5C3A72ABA6F525C
A_vs_B_DIFFERENT = False   A_vs_C_DIFFERENT = False   B_vs_C_DIFFERENT = False
D1_VERDICT=PRESENT (the readback is stale)
```
`recovery\work\task094\freshness\snake-clean-nocapture\`

The three pictures do not merely equal each other: they show the **original dark background**, i.e.
the process's first rendered frame. So it is not "the change was not visible", it is "the readback
never moves again".

**The same defect with the node tree as the witness** (`runs\snake\task094-probe4`, snake running
right, not paused):

| instant | `head` | `SnakeSeg00.position` (real node) | readback fingerprint | green samples |
|---|---|---|---|---|
| t1 | 6,10 | (144, 240) | 558211402 | 144 |
| t2 | 11,10 | (264, 240) | 558211402 | 144 |
| t3 | 16,10 | (384, 240) | 558211402 | 144 |

The node that is drawn moved **240 px to the right** between the first and the last sample
(`over=false`, `ticks` 4 → 9 → 14) and the readback is byte-identical at every instant.
`probe3` (paused board) and `probe5` (cached `Viewport::texture_rid` vs a fresh
`RenderingServer.viewport_get_texture()` call, same checksum) give the same answer.

### A2 Why the TASK-093 evidence was partly an artefact — and why D-1 is real anyway

`recovery\work\task093\diag_render.ps1` (the script that "reproduced" D-1) runs the **snake** game
and takes its first screenshot 6 s after startup. The snake starts at head `5,10` moving right and
hits the wall after **19 ticks = 1.5 s**. `SNAKE_WALL head=25,10 ... ticks=19` is in every engine
log. So that script photographed a **finished, static board** and called it a stale readback. The
same trap caught my first window test: the first grab was at t≈4 s, long after the board froze.

D-1 is nevertheless real and is *not* that artefact:
* probe3/probe4 compare the fingerprint **and the live node position in the same instant**, on a
  board that is alive (`over=false`);
* the `repro2` counter-example changes a plain `ColorRect` that no game script writes and reads the
  property back green, while the picture still shows the dark background;
* `--mcp-capture=off` removes the capture engine from the process entirely and it still reproduces.

### A3 What is *not* the cause — each one measured

| # | Hypothesis | Test | Result |
|---|---|---|---|
| 1 | The game logic is not running | `execute_gdscript` reads `HeadX/HeadY/Ticks`, `SnakeSeg00.position`, `Background.color` | it changes; `over=false` |
| 2 | The frame loop is not running | `Engine.get_frames_drawn()` / `get_process_frames()` | 933 → 1311 → 1325 → 1338 (≈144/s), both equal |
| 3 | `Main::iteration` skips `RenderingServer::draw()` (`wants_present=false`) | window state via Win32: `IsIconic=False`, `IsWindowVisible=True`, rect 822x656; `DisplayServer.window_get_mode()=0` | not minimised → `can_any_window_draw()` is true → `draw()` runs (`main\main.cpp:5081`) |
| 4 | `draw_viewports` skips the root viewport | `Performance.RENDER_TOTAL_OBJECTS_IN_FRAME` before/after adding 100 `ColorRect`s | **57 → 157**, prims 114 → 314 — the renderer sees the new nodes (`runs\snake\task094-probe9`) |
| 5 | The readback texture RID is stale | `RenderingServer.viewport_get_texture(get_viewport().get_viewport_rid())` compared with the cached `Viewport::texture_rid` | same RID, same checksum |
| 6 | It is the headless/dummy renderer | `DisplayServer` is `windows`, `Vulkan 1.4.351 Forward+ NVIDIA RTX 4090` | a real framebuffer |
| 7 | It is the capture engine's per-frame read | `--mcp-capture=off` (no capture engine at all) | still frozen |
| 8 | It is the rendering driver | vulkan / opengl3 / d3d12 | all three frozen (three different first-frame PNGs: `D5C3A72A…`, `11D1ABB9…`, `D5C3A72A…`) |
| 9 | It needs a forced frame | `RenderingServer.force_sync()` + `RenderingServer.force_draw(true, 0.0)` inside the tool call, then read | unchanged, while `fd` grew to 12327 |
| 10 | It is our code | the window-content probe with the **stock Godot 4.7.1 mono** on the same project | see A4 |
| 11 | It is a dead/finished board (the TASK-093 misreading) | all of the above use a live board or a plain `ColorRect` | excluded |
| 12 | The GPU/driver is hung | `nvidia-smi` (0 % util, P8, 37 °C, no MIG/ECC error), Windows System log for `nvlddmkm`/TDR in the last 8 h | nothing |

### A4 It is the machine, not the module — the two decisive comparisons

**(a) Same bytes, same session, different answer 1 h 45 min apart.**
The engine binary `godot.windows.editor.x86_64.mono.console.exe` has `LastWriteTime
2026-09-27 00:09:30` and was not rebuilt, touched or replaced since (checked before and after).
Replaying the **unmodified** `tools\sessions\pong\session.json`:

| run | when | capture lines | non-zero | distinct PNGs (game) |
|---|---|---|---|---|
| `runs\pong\pong-task092` (TASK-092) | 00:14:47 | 29 | **10** (`512, 314, 92, 122, 3200, 3200, 512, 512, 96, 3200`) | 16 |
| `runs\pong\task094-pong-ab` (this task) | 02:00 | 29 | **0** | 1 |

The editor side regressed the same way (4 distinct → 1). Nothing in `modules/mcp_server` changed
between the two runs (`git status --short` in the engine repo was empty until this task's script
edit).

**(b) The plain run with no MCP involvement at all.** `diag_stockwindow.ps1` starts
`godot --path <snake>` with *no* `--mcp-*` switch, waits for the window, and grabs it. Four grabs
over ~1.2 s are byte-identical. The same fixture with the **stock Godot 4.7.1 mono official build**
gives the *same* grab bytes, and both engines' stdout shows the game running to `SNAKE_WALL … ticks=19`.

That second test also **invalidates the OS-level window probe as evidence**: two different engine
builds cannot produce byte-identical desktop captures over a live window, so `CopyFromScreen`
(and `PrintWindow`, which returns yet another constant image) are reading a frozen composition
surface in this session. The same limitation explains why the desktop always looked frozen: it
says nothing about the app.

**Conclusion.** The picture side of this machine is in a state where the engine's CPU-side
accounting runs (frames drawn, objects drawn, game ticks) but the frame never becomes readable
again through *any* in-process path, and the only out-of-process path (the desktop) is frozen as
well. Every in-process readback goes through
`TextureStorage::texture_2d_get` → `RenderingDevice::texture_get_data`
(`servers\rendering\rendering_device.cpp:2737`) → `draw_graph.add_texture_get_data(...)` →
`_flush_and_stall_for_all_frames()` — a mechanism the module does not own and cannot reach. The
module's own contribution to the path is one line: `viewport->get_texture()->get_image()`
(`mcp_capture.cpp:300-301`, `tools\tool_helpers.cpp:2925-2926`), which is also what
`ViewportTexture::get_image()` (`scene\main\viewport.cpp:201`) is defined as.

### A5 Bypasses tried — all fail, on the record

| bypass | how | result |
|---|---|---|
| switch the rendering driver | `--rendering-driver opengl3` / `d3d12` | frozen (`recovery\work\task094\freshness\snake-driver-opengl3`, `snake-clean-d3d12`) |
| force one whole drawing frame | `RenderingServer.force_sync()` then `force_draw(true, 0.0)`, then read | frozen (`runs\snake\task094-probe7`) |
| read via the render target's *current* texture instead of the cached one | `RenderingServer.texture_2d_get(RenderingServer.viewport_get_texture(vp_rid))` | same texture, same stale bytes (`runs\snake\task094-probe5`) |
| read the window from outside the process | `CopyFromScreen` and `PrintWindow(PW_RENDERFULLCONTENT)` on the window rect | unusable — the same bytes for two different engines (A4b) |

There is **no bypass that yields pixel evidence on this machine right now**. Saying otherwise would
be the "should work" transcription the task forbids.

---

## B. Pixel evidence — blocked, not faked

The replayed sessions and their real numbers are kept:

| game | run | capture lines | non-zero | distinct PNGs | `GAME-LOOP-LOG.md` pixel-diff column |
|---|---|---|---|---|---|
| Pong | `runs\pong\task094-pong-ab` | 29 | 0 | 1 | still 0 — points at D-1 |
| Snake | `runs\snake\task094-probe9`, `runs\snake\task093-r6` | 6 / 29 | 0 | 1 | still 0 — points at D-1 |
| Breakout | `runs\breakout\breakout-task093-r7` | 34 | 0 | 1 | still 0 — points at D-1 |

Breakout and Snake were **not** re-replayed end-to-end in this task: the minimal counter-example
(A1) reproduces D-1 with `--mcp-capture=off` on the snake project in 30 s, so a full replay would
only add more zeroes. The column therefore stays at its TASK-093 value and the D-1 note stays with
it. The old PNGs from TASK-092 still recompute to non-zero (512/314/3200/…): those files are on
disk and were verified to be mutually different, so the earlier positive result was real and the
current one is a regression of the machine's state, not of the pictures.

---

## C. D-2 — `accept_m1.ps1` was load-sensitive; fixed and measured

### C1 The predicate

`modules/mcp_server/scripts/accept_m1.ps1`, `Wait-ForStablePump`:

```powershell
# before
if ($null -ne $previous -and ($frames - $previous) -ge 20) { $consecutive++ } else { $consecutive = 0 }
if ($consecutive -ge 3) { return $true }
Start-Sleep -Milliseconds 1000
```
"at least 20 frames between two samples one second apart, three times in a row" — a **throughput**
requirement. On a loaded 16-vCPU box the editor pump is alive but slower than 20 fps, so the
function burned its whole 180 s deadline, printed
`WARNING: the pump never looked steady, running the cases anyway`, and the cases then ran against a
pump that was still settling → `case1_GET_mcp_200 status=0 body=` and `Wait` exceptions → **5/22**
(TASK-093's `task093b`).

```powershell
# after
if ($null -ne $previous) {
    if ($frames -gt $previous) { $increases++ } else { $increases = 0 }
    if ($increases -ge 6) { return $true }
}
Start-Sleep -Milliseconds 250
```
Readiness is "the loop advances", not "the loop is fast": six consecutive strictly increasing
`frame_count` samples, 250 ms apart (≈1.5 s of uninterrupted progress at *any* frame rate, down to
1 fps). Same 180 s deadline, and it still says so loudly when it cannot be met.

### C2 The two measurements (real exit codes, nothing else on the machine)

| run | load | wall | result | artifact |
|---|---|---|---|---|
| alone | none | **50.8 s** | `22/22 cases passed`, `GATE_EXIT=0` | `runs\gates\task094-alone\g10.stdout.txt` |
| under load | 8 CPU burners (16 logical CPUs) | **55.3 s** | `22/22 cases passed`, `GATE_EXIT=0` | `runs\gates\task094-load2\g10.stdout.txt` |
| under load | `dotnet build --no-incremental` of the Breakout project | **41.5 s** | `22/22 cases passed`, `GATE_EXIT=0` | `runs\gates\task094-load\g10.stdout.txt` |

No `WARNING: the main loop never advanced` line appears in any of the three. `case12/13/14` and
`guard_user_port_9877` pass in all of them (they also passed in TASK-093's failing rounds, which is
why TASK-093 already suspected load rather than the bind logic).

> Honest note: the third row's load had already finished when the run started (the build is short);
> it is reported as a *short overlapping load*, not as a heavy one. Rows 1 and 2 are the
> solo/parallel pair the task asks for.

---

## D. The 4th game (Tetris) — not started

No line was added to `GAME-LOOP-LOG.md`. D-1's location took ~70 minutes (twelve eliminated
hypotheses, four failed bypasses, several contaminated runs that had to be thrown away — including
one where a **leftover Godot process from an earlier run still held port 9889** and answered the
tool calls, which is why every probe from 01:21 on was re-run with a unique port and a process
check afterwards). With the pixel-evidence path still broken, a fourth game would only add another
`pixel-diff = 0` row.

---

## E. Gates, commits, both repositories

### E1 The ten gates (`runs\gates\task094\`) — g01..g10 **all `exit=0`**

Run with `tools\run_gates.ps1 -Tag task094 -VersionText 4.8.dev.mono.custom_build.cf554ef58`
(engine HEAD was still `cf554ef58c` at the time of the run; gate 9 needs the *compiled* anchor, see
G-1 in TASK-093's report). Per-gate `exit=` lines and the tails are in `summary.txt`:

| # | gate | verdict (`exit=0`) |
|---|---|---|
| 1 | module doctests `--test-case=[MCPServer]*` | `155/155 passed`, `6613/6613 assertions`, `SUCCESS!` |
| 2 | full doctests `--headless --test` | `1581/1581 passed / 3 skipped`, `430926/430926 assertions`, `SUCCESS!` |
| 3 | group manifest | `TOOL-GROUPS CHECK PASS` |
| 4 | contract subset (live) | `3/3 checks passed` (editor 9888, game 9889, `guard_user_port_9877`) |
| 5 | rename map | `RESULT: PASS (all checks green)` |
| 6 | tautologies | `TAUTOLOGY CHECK PASS` |
| 7 | exit-code propagation | `PROBES: 10/10` |
| 8 | hardcoded counts | `RESULT: PASS`（`UNCLASSIFIED = 0`） |
| 9 | engine anchor | `ANCHOR_JUDGE VERDICT=ANCHOR_EQUAL`; `diff_count=0 safe_count=0 red_count=0`; `RESULT PASS` |
| 10 | `accept_m1` | `22/22 cases passed` (wall 46.7 s) |

**On the rebuild question.** The only engine-repo change in this task is
`modules/mcp_server/scripts/accept_m1.ps1` — a PowerShell script that is not compiled into either
variant (`git status --short` in the engine repo lists exactly that one file, before the commit). No
object file depends on it, so a rebuild would reproduce byte-identical binaries and prove nothing;
it was deliberately not run, and that is stated here rather than presented as "rebuilt and green".
The consequence is the known gate-9 behaviour: the compiled version string stays `cf554ef58` while
the engine HEAD moves to `8b9dd9a72b`, so gate 9 is `ANCHOR_EQUAL` for the anchor `cf554ef58`
*before* the commit (which is what was measured) and `ANCHOR_STALE_COMPILED` after it — the same
self-correction TASK-092 recorded.

### E2 Commits

**Engine repo `F:\moonbit-hof-rs\godot-mcp\godot`** — one commit, **pushed to the fork**:

```
8b9dd9a72b modules/mcp_server: task094 - D-2 is a load-sensitive readiness predicate, not a defect: the accept_m1 wait now asks the main loop to advance (frame_count strictly increasing six samples in a row) instead of asking it to be faster than 20 fps, so the suite is 22/22 solo and 22/22 under eight CPU burners
cf554ef58c modules/mcp_server: task092 (B2/B3/B4) step2 - a deferred call's file effects and its capture are collected at completion, the two missing doctests exist, and the frame cost is a clamped median of a window
87fbf82f4b modules/mcp_server: task092 (B1) step1 - an over-bound payload is written whole to a sidecar the line can be checked against, and the ledger re-hashes it
382549f63e modules/mcp_server: task090 (2c-9) step6 - the round-8 record: the traceability section and the gate ledger
8604fcf9e2 modules/mcp_server: task090 (2c-9) step5 - the description change is declared in the generator, so the contract stays reproducible
eee58538a1 modules/mcp_server: task090 (2c-9) step4 - a deferred call's own body reaches its trace line too
cac01b5f9f modules/mcp_server: task090 (2c-9) step3 - the round-8 fixes: the InputMap fact, the scenario flags, the frame-based deadline
a455a87bea modules/mcp_server: task090 (2c-9) step2 - D-3: the game executor reaches the running scene tree
```

`git status --short`: **empty**.
`git rev-parse HEAD` == `refs/remotes/origin/feature/mcp-server-module-rebuild`
== `8b9dd9a72be43c90e875d2c765ca673ba59a9492` (`cf554ef58c..8b9dd9a72b HEAD -> feature/mcp-server-module-rebuild`).

**Main repo `F:\moonbit-hof-rs`** (branch `master`, no remote) — two commits:

```
b42e233 docs(godot-mcp): TASK-094 - D142 in the decision log (D-1 attributed to the machine's picture pipeline and the twelve hypotheses eliminated, D-2 judged as test brittleness and its readiness predicate fixed), with the ten gate exit codes and the three accept_m1 measurements
f65fe78 docs(godot-mcp): TASK-094 - D-1 is the machine's picture pipeline, not the module: the minimal counter-example (blue/red/green background, three identical PNGs that still show the dark background, with the property read back as green), the twelve eliminated hypotheses, the same-session A/B that answers 10/29 non-zero at 00:14 and 0/29 at 02:00 on unchanged binary bytes, and the four bypasses that all fail; the pixel-diff column stays at its real 0 because no fix can be produced from inside this process
5f47949 docs(godot-mcp): TASK-093 - the report carries the two commit ids of this task and the final gate ledger
ae0b791 docs(godot-mcp): TASK-093 - the report and its evidence: eight game-side defects with before/after runs, the ten gates green, and the one environment defect that blocks pixel evidence
97167e4 feat(godot-mcp): TASK-093 - the 2nd and 3rd C# games (Breakout, Snake), every byte of them written by MCP calls, plus the cross-round GAME-LOOP-LOG
fed0135 docs(godot-mcp): TASK-092 - the summary table carries the same two measurement points as the body, so the report cannot be read two ways
64df60b docs(godot-mcp): TASK-092 - the report's main-repo log is a snapshot with an explicit boundary, so a doc-only follow-up cannot make it stale
9a9b1f3 docs(godot-mcp): TASK-092 - the tracked/ignored numbers are stated for both measurement points, and the largest tracked artifact is named instead of hiding inside a total
```

`git status --short`: **empty (0 lines)**. `f65fe78` carries `GAME-LOOP-LOG.md` (D-1 re-attributed,
D-2 marked fixed with both measurements), `README.md` (both defects rewritten), the report and the
239-file / 1.7 MB `recovery\work\task094\` evidence set. It also contains the one incidental file the
Pong replay touched, `projects\pong\scenes\main.tscn` (the engine rewrites `unique_id`s when a scene
is re-saved; semantics identical — same note as TASK-092's).

### E3 Where this task stopped — stated plainly

* **A** located and bounded; **no fix exists that can be made from inside `modules/mcp_server`**.
* **B** blocked by A; the pixel-diff columns keep their real `0` and point at D-1.
* **C** fixed and measured solo *and* under load.
* **D** not started (Tetris is not in the ledger).
* **E** ten gates green with real exit codes; engine repo committed and pushed; main repo committed;
  both `git status` empty. The rebuild was deliberately skipped and why is written down above.

---

## F. Files produced by this task

```
recovery\work\task094\
  diag_window.ps1            window state + the two screenshots of the first probe
  diag_freshness.ps1         the minimal counter-example, -Driver / -Capture / -Session / -Port
  diag_screen.ps1            OS-level window grab vs the tool's screenshot (shows the grab is stale)
  diag_stockwindow.ps1       a plain run of any engine with no MCP at all (the stock-4.7.1 control)
  sessions\repro\session.json     move SnakeSeg00 by 552 px, three screenshots
  sessions\repro2\session.json    Background.color blue -> red -> green  (the minimal counter-example)
  sessions\probe\session.json     frame counters, window mode, readback, force_draw
  sessions\probe3..probe9\        paused board / live node position / cached-vs-fresh RID /
                                  force_draw / 100 added nodes (renderer liveness)
  freshness\                  the reproducer's runs (clean, opengl3, d3d12)
  screen\, stock\             the window-grab control runs
runs\snake\task094-probe*
runs\pong\task094-pong-ab\   the TASK-092 session replayed (0/29)
runs\gates\task094-alone\, task094-load\, task094-load2\
```

The residual engine defect is not in `modules/mcp_server`; it is in the machine's picture pipeline
and is recorded in `GAME-LOOP-LOG.md` D-1 with these pointers, so the next round starts from the
counter-example instead of from a finished snake board.
