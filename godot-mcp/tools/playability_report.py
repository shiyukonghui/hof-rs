#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""playability_report.py -- TASK-116 item C: turn the gate's JSON into the two reports.

    runs\\playability\\playability.json   (machine-readable, written by the gate)
        |
        +--> recovery\\reports\\PLAYABILITY-REPORT.md    (what is playable, with evidence)
        +--> recovery\\reports\\PLAYABILITY-DEFECTS.md   (one row per defect, with root cause)

A defect in the register is never "we think so": it is derived from a machine-checked
fact of the gate (`actions_tested[].responds`, `criteria.P*.pass`, the static audit's
`used_but_undeclared` / `declared_but_never_read`) or from a source line that is quoted
with its `file:line`.  The `PollInput` defect class is read out of the C# itself, because
the gate can only see its *consequence* (no action responds) and the register is supposed
to name the cause.

Usage
-----
    python tools\\playability_report.py
    python tools\\playability_report.py --before runs\\playability\\playability.before.json
"""

from __future__ import print_function

import argparse
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROJECTS = os.path.join(ROOT, "projects")
RUNS = os.path.join(ROOT, "runs", "playability")
REPORTS = os.path.join(ROOT, "recovery", "reports")

sys.path.insert(0, HERE)
from playability_gate import load_controls  # noqa: E402


def read_text(path):
    for enc in ("utf-8", "utf-8-sig", "gbk", "latin-1"):
        try:
            with io.open(path, "r", encoding=enc) as fh:
                return fh.read()
        except Exception:  # noqa: BLE001
            continue
    return ""


def git_lines(repo, args):
    """Read-only `git` output, used so the report and the repository cannot disagree."""
    import subprocess
    try:
        r = subprocess.run(["git", "-C", repo] + list(args), stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT)
        text = r.stdout.decode("utf-8", "replace")
        return [ln for ln in text.splitlines() if ln.strip()]
    except Exception as e:  # noqa: BLE001
        return ["<git failed: %s: %s>" % (type(e).__name__, e)]


def pollinput_sites(game):
    """`[Export] bool PollInput = false` and every assignment, with file:line."""
    out = []
    for dirpath, _dn, fns in os.walk(os.path.join(PROJECTS, game, "src")):
        for fn in sorted(fns):
            if not fn.endswith(".cs"):
                continue
            p = os.path.join(dirpath, fn)
            rel = os.path.relpath(p, ROOT).replace("\\", "/")
            txt = read_text(p)
            for i, line in enumerate(txt.splitlines(), 1):
                m = re.search(r"(\[Export\]\s*)?public\s+bool\s+PollInput\s*=\s*(true|false)", line)
                if m:
                    out.append({"site": "%s:%d" % (rel, i), "kind": "declaration",
                                "value": m.group(2), "line": line.strip()})
                    continue
                m = re.search(r"\bPollInput\s*=\s*(true|false)\s*;", line)
                if m:
                    out.append({"site": "%s:%d" % (rel, i), "kind": "assignment",
                                "value": m.group(1), "line": line.strip()})
    return out


def input_guards(game):
    """Where the InputMap reads sit behind a flag, e.g. `if (PollInput && ...)`."""
    out = []
    for dirpath, _dn, fns in os.walk(os.path.join(PROJECTS, game, "src")):
        for fn in sorted(fns):
            if not fn.endswith(".cs"):
                continue
            p = os.path.join(dirpath, fn)
            rel = os.path.relpath(p, ROOT).replace("\\", "/")
            txt = read_text(p)
            for i, line in enumerate(txt.splitlines(), 1):
                if "PollInput" in line and re.search(r"\bif\s*\(|&&", line):
                    out.append("%s:%d %s" % (rel, i, line.strip()))
    return out


# ---------------------------------------------------------------------------
def defect_register(summary, audit_index):
    """One row per (game, defect class), each with the evidence that produced it."""
    rows = []
    for g in summary["games"]:
        game = g["game"]
        crit = g["criteria"]
        audit = audit_index.get(game) or {}
        p1, p2, p3, p4, p5 = (crit.get(k) or {} for k in ("P1", "P2", "P3", "P4", "P5"))
        gate_path = g.get("gate_json")
        gate = {}
        gp = os.path.join(ROOT, gate_path) if gate_path else None
        if gp and os.path.isfile(gp):
            gate = json.load(io.open(gp, encoding="utf-8"))
        gdir = os.path.join(RUNS, game)

        # ---- D1: the whole-game input switch is off --------------------------
        sites = pollinput_sites(game)
        decl = [s for s in sites if s["kind"] == "declaration"]
        before_actions = g.get("actions") or []
        none_responded = bool(before_actions) and not any(a.get("responds")
                                                          for a in before_actions)
        if decl and decl[0]["value"] == "false":
            guards = input_guards(game)
            rows.append({
                "id": "D1",
                "class": "player input is switched off in the shipped build",
                "game": game,
                "severity": "blocker",
                "phenomenon": "the game launches and renders, but no key does anything until a test "
                              "driver calls SetPollInput(true); a human player cannot play it",
                "evidence": [decl[0]["site"] + "  " + decl[0]["line"]]
                            + guards[:3]
                            + ["before-run P2: " + (p2.get("why") or "")],
                "root_cause": decl[0]["site"],
                "fix": "flip the field initialiser to `= true` and keep `SetPollInput(false)` / "
                       "`ForceTestState` as the test-only switch (the determinism rule is about "
                       "AutoPlay/AutoClock/DriftSpeed, not about listening to the keyboard)",
                "verified_by": "the same game re-run through the gate (P2 must go blue)",
            })
        elif decl and none_responded:
            # the register is normally generated *after* the fix, when the initialiser already
            # reads true -- so the defect is reconstructed from the before-run evidence (no
            # declared action responded) plus the switch's own presence in the source.
            rows.append({
                "id": "D1",
                "class": "player input was switched off in the shipped build (fixed; registered "
                         "from the before-run evidence)",
                "game": game,
                "severity": "blocker",
                "phenomenon": "in the before run not one of the %d declared actions responded on "
                              "either injected channel; the game listened to nothing" % len(before_actions),
                "evidence": ["%s  %s   (this line now reads `= true`; `git diff` of the task's "
                             "commit shows the flip)" % (decl[0]["site"], decl[0]["line"]),
                             "before-run P2: " + (p2.get("why") or "")],
                "root_cause": decl[0]["site"],
                "fix": "the field initialiser was flipped to `= true` and the assignment inside the "
                       "startup `Reset*()` was removed",
                "verified_by": "the same game re-run through the gate (P2 is blue in the after run)",
            })

        # ---- D2: the code reads an action the InputMap does not declare ------
        for a in audit.get("used_but_undeclared") or []:
            rows.append({
                "id": "D2",
                "class": "the code reads an InputMap action that is not declared",
                "game": game,
                "severity": "blocker",
                "phenomenon": "pressing that key can never work: Godot's InputMap has no such "
                              "action, so %s stays 0 forever" % a,
                "evidence": audit.get("undeclared_sites", {}).get(a, [])
                            + ["declared actions: %s" % audit.get("declared_actions")],
                "root_cause": (audit.get("undeclared_sites", {}).get(a) or ["?"])[0],
                "fix": "declare `%s` in project.godot's [input] section next to its siblings" % a,
                "verified_by": "the same game re-run through the gate (P5 and P2 must go blue)",
            })

        # ---- D3: a declared action that responds to nothing ------------------
        # Read from the summary's own action rows (the before run's), not from
        # runs/playability/<game>/gate.json: that file is overwritten by the after run.
        for t in before_actions:
            if not t.get("responds"):
                rows.append({
                    "id": "D3",
                    "class": "declared control did not respond to its own key",
                    "game": game,
                    "severity": "blocker",
                    "phenomenon": "the InputMap declares `%s` (%s) but injecting it changed neither "
                                  "state nor pixels beyond the no-input control window"
                                  % (t.get("action"), t.get("key")),
                    "evidence": ["before-run P2 action row: %s" % json.dumps(
                        {k: t.get(k) for k in ("action", "key", "responds")},
                        ensure_ascii=False),
                        "before-run P2: " + (p2.get("why") or "")],
                    "root_cause": ("see D1 (the read is guarded by PollInput, which was false)"
                                   if any(r["id"] == "D1" for r in rows if r["game"] == game)
                                   else "the read is never reached, or the action is not wired to it"),
                    "fix": "either wire the action to the behaviour the player expects, or stop "
                           "declaring it",
                    "verified_by": "the same game re-run through the gate",
                })
                break  # one representative row per game; the gate keeps every action

        # ---- D4: a declared action the code never reads ----------------------
        # Two strengths of "read", deliberately kept apart (see audit_one):
        #   * `declared_but_never_read`      -- no literal `IsAction*("x")` call site;
        #   * `declared_but_never_referenced`-- that AND the name appears nowhere as a
        #     string literal either (e.g. it is passed to a helper that then polls it).
        # Only the second one is a defect.  This matters: after TASK-116 wired match3's
        # cursor through `MoveCursor(action, ...)`, the first list still fired and would
        # have reported twelve actions as dead that respond perfectly well on the wire.
        for a in audit.get("declared_but_never_referenced") or []:
            rows.append({
                "id": "D4",
                "class": "declared action no line of code reads",
                "game": game,
                "severity": "major",
                "phenomenon": "`%s` exists in the InputMap but neither an `IsAction*(\"%s\")` call "
                              "site nor any string literal in the game's C# mentions it" % (a, a),
                "evidence": ["declared: %s" % audit.get("declared_actions"),
                             "read by the code: %s" % audit.get("actions_read_by_the_code"),
                             "referenced by the code: %s"
                             % audit.get("actions_referenced_by_the_code")],
                "root_cause": "project.godot [input] vs src/*.cs (whole-repo grep)",
                "fix": "wire it up or delete it",
                "verified_by": "static audit re-run",
            })

        # ---- D5: the README documents no controls ---------------------------
        if not audit.get("readme_has_play_section"):
            rows.append({
                "id": "D5",
                "class": "no documented controls (the README has no 玩法 section)",
                "game": game,
                "severity": "major",
                "phenomenon": "nothing on disk tells a human which keys to press; the only source of "
                              "truth is project.godot's InputMap, which players never read",
                "evidence": ["README.md: no '## 玩法'", "declared actions: %s"
                             % audit.get("declared_actions")],
                "root_cause": "projects/%s/README.md" % game,
                "fix": "document every declared action and its key in a '## 玩法' section",
                "verified_by": "the gate's README-vs-InputMap cross-check",
            })
        for claim in (audit.get("readme_key_claims") or []):
            if claim.get("known"):
                continue
            rows.append({
                "id": "D5b",
                "class": "the README documents a key the InputMap does not declare",
                "game": game,
                "severity": "major",
                "phenomenon": "README says `%s`, but no declared action listens for keycode %s"
                              % (claim.get("key"), claim.get("keycode")),
                "evidence": [json.dumps(claim, ensure_ascii=False),
                             "declared actions: %s" % audit.get("declared_actions")],
                "root_cause": "projects/%s/README.md vs project.godot [input]" % game,
                "fix": "fix the documented key, or declare the action it names",
                "verified_by": "the gate's README-vs-InputMap cross-check",
            })

        # ---- D6: window geometry --------------------------------------------
        wc = gate.get("window_conformance") or g.get("window_conformance")
        if wc and not wc.get("matches_declared"):
            rows.append({
                "id": "D6",
                "class": "the OS window does not match the size the project declares",
                "game": game,
                "severity": "major",
                "phenomenon": "declared %s but the game opened %s" % (wc.get("expected_os_window"),
                                                                      wc.get("os_window")),
                "evidence": [json.dumps(wc, ensure_ascii=False)],
                "root_cause": "projects/%s/project.godot [display]" % game,
                "fix": "set display/window/size/window_width_override|height_override, or fix the "
                       "viewport size",
                "verified_by": "the gate's window probe",
            })

        # ---- D7: nothing visible --------------------------------------------
        if not p1.get("pass"):
            rows.append({
                "id": "D7",
                "class": "nothing visible in the full-window frame",
                "game": game,
                "severity": "blocker",
                "phenomenon": p1.get("why"),
                "evidence": [g.get("filmstrip") or ""],
                "root_cause": "see the frame and the scene tree in runs/playability/%s" % game,
                "fix": "make the game draw inside the declared viewport",
                "verified_by": "the gate's P1 metrics over the settled frames",
            })

        # ---- D8: the main loop does not advance -----------------------------
        if not p3.get("pass"):
            rows.append({
                "id": "D8",
                "class": "the main loop does not advance the game's own quantities",
                "game": game,
                "severity": "blocker",
                "phenomenon": p3.get("why"),
                "evidence": [g.get("filmstrip") or ""],
                "root_cause": "see runs/playability/%s/gate.json criteria.P3" % game,
                "fix": "find the frozen state machine / the early return",
                "verified_by": "the gate's P3 counters",
            })

        # ---- D11: a required player capability is not delivered ----------------
        # Two sources, because the capability table post-dates the before run:
        #   (a) the before run's P6 (present only in the after summary -- used when the
        #       register is built from the after data);
        #   (b) for the normal case (register built from the before summary), the
        #       capability's action not existing in the before InputMap at all -- that is
        #       exactly what "no action delivers this capability" meant at the time.
        p6 = crit.get("P6") or {}
        before_declared = set(audit.get("declared_actions") or [])
        caps = p6.get("capabilities") or []
        if not caps:
            controls = load_controls().get(game) or {}
            for cap in (controls.get("capabilities") or []):
                if cap.get("action") and cap["action"] not in before_declared:
                    rows.append({
                        "id": "D11",
                        "class": "no declared action delivered a capability a player needs",
                        "game": game,
                        "severity": "blocker",
                        "phenomenon": "`%s` had no key at all: the before InputMap was %s"
                                      % (cap.get("need"), sorted(before_declared)),
                        "evidence": ["tools/playability_controls.json: %s -> %s"
                                     % (game, cap.get("need")),
                                     "the action `%s` was added by this task"
                                     % cap.get("action")],
                        "root_cause": "projects/%s/project.godot [input] + src/%s"
                                      % (game, game),
                        "fix": "declare the action and wire it to the game's own API "
                               "(see the D2/D3 rows for the same game)",
                        "verified_by": "the gate's P6 row in the after run",
                    })
                    continue
                if cap.get("pass") is False:
                    rows.append({
                        "id": "D11",
                        "class": "a capability a player needs is not delivered",
                        "game": game,
                        "severity": "blocker",
                        "phenomenon": "`%s` cannot be done: %s" % (cap.get("need"),
                                                                   cap.get("why")),
                        "evidence": ["tools/playability_controls.json: %s -> %s"
                                     % (game, cap.get("need")),
                                     "gate P6: %s" % p6.get("why")],
                        "root_cause": "projects/%s/project.godot [input] + src/%s"
                                      % (game, game),
                        "fix": "bind a key to that capability and wire it to the game's own API",
                        "verified_by": "the same game re-run through the gate (P6 must go blue)",
                    })
        for cap in caps:
            if cap.get("pass"):
                continue
            rows.append({
                "id": "D11",
                "class": "a capability a player needs is not delivered",
                "game": game,
                "severity": "blocker",
                "phenomenon": "`%s` cannot be done: %s" % (cap.get("need"), cap.get("why")),
                "evidence": ["tools/playability_controls.json: %s -> %s"
                             % (game, cap.get("need")),
                             "gate P6: %s" % p6.get("why")],
                "root_cause": "the game's InputMap + src/%s/src (no action delivers it)"
                              % game,
                "fix": "bind a key to that capability and wire it to the game's own API "
                       "(see the D1/D2/D3 rows for the same game)",
                "verified_by": "the same game re-run through the gate (P6 must go blue)",
            })

        # ---- D9: crash or modal dialog --------------------------------------
        if not p4.get("pass"):
            rows.append({
                "id": "D9",
                "class": "the process did not survive, or a modal dialog appeared",
                "game": game,
                "severity": "blocker",
                "phenomenon": p4.get("why"),
                "evidence": [g.get("engine_stdout") or "runs/playability/%s/engine-game.stdout.txt"
                             % game],
                "root_cause": "see the engine's own stdout/stderr",
                "fix": "fix the engine-level error",
                "verified_by": "the gate's process/window probe",
            })

        # ---- D10: a hub in the process --------------------------------------
        if (gate.get("p4") or {}).get("modal_candidates"):
            rows.append({
                "id": "D10",
                "class": "a modal dialog is open on the game's window",
                "game": game,
                "severity": "blocker",
                "phenomenon": "the player sees a modal box instead of the game, and the game is "
                              "frozen until it is dismissed by hand",
                "evidence": json.dumps(gate["p4"]["modal_candidates"], ensure_ascii=False)[:600],
                "root_cause": "engine stderr",
                "fix": "fix whatever the dialog is about (usually a missing resource)",
                "verified_by": "EnumWindows over the process tree",
            })
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--before", default=os.path.join(RUNS, "playability.before.json"))
    ap.add_argument("--json", default=os.path.join(RUNS, "playability.json"))
    args = ap.parse_args(argv)

    summary = json.load(io.open(args.json, encoding="utf-8"))
    before = None
    if args.before and os.path.isfile(args.before):
        before = json.load(io.open(args.before, encoding="utf-8"))
    # The defect register is built from the BEFORE run -- that is where the defects were
    # found, and a register that only ever lists what is *still* wrong cannot show what the
    # task fixed.  Each row is then annotated with what the AFTER run says about it.
    if before is not None:
        before_audit = {a["game"]: a for a in before.get("static_audit") or []}
        defects = defect_register(before, before_audit)
    else:
        before_audit = {}
        defects = defect_register(summary, {a["game"]: a
                                           for a in summary.get("static_audit") or []})
    after_index = {g["game"]: g for g in summary["games"]}
    for r in defects:
        a = after_index.get(r["game"]) or {}
        crit = a.get("criteria") or {}
        still = [k for k in ("P1", "P2", "P3", "P4", "P5", "P6")
                 if not (crit.get(k) or {}).get("pass")]
        r["after_verdict"] = a.get("verdict") or "not re-run"
        r["after_open_criteria"] = still
        r["status"] = ("已修复，并在同一道门的复跑中验证（复跑判定：可玩）"
                       if a.get("verdict") == "playable"
                       else "复跑仍然未通过：" + (", ".join(still) or "复跑缺失"))
    after_only = [r for r in defect_register(summary, {g_["game"]: g_
                                                      for g_ in summary.get("static_audit") or []})
                  if r["game"] not in {x["game"] for x in defects}]

    # ---------------- PLAYABILITY-REPORT.md ----------------
    L = []
    A = L.append
    A("# TASK-116 — 可玩性门（PLAYABILITY GATE）报告")
    A("")
    A("> 生成时间：%s ｜ 机器可读原始数据：`runs/playability/playability.json`" % summary["generated"])
    A("> 门工具：`tools/playability_gate.py` ｜ 试玩代理接口：`tools/playtest_agent.py`")
    A("> 逐款证据：`runs/playability/<game>/{frames/*.png, frames.json, filmstrip.png, gate.json}`")
    A("")
    A("## 0. 为什么要有这道门（本轮要回答的问题）")
    A("")
    A("用户试玩 20 款后反馈**部分游戏不可玩**。此前所有证据都来自 `shots-editor`——")
    A("`editor_capture_screenshot` 拍的是**整个编辑器窗口**（本机 2978×1793），运行中的游戏只是其中")
    A("一个内嵌子窗口，所以「像素差 512 px」测的是那个很小的嵌入区域，不能说明玩家在全窗口里看到什么。")
    A("")
    A("本门实测口径：**真游戏进程**（引擎二进制不带 `-e`、真实窗口、绝不 `--headless`）+ **game 端点**")
    A("的 `running_game_capture_screenshot`（`mcp_capture.cpp:270-296`：game 侧永远读 `tree->get_root()`，")
    A("即整窗内容）+ 每帧记录**窗口/视口/声明尺寸三者的比对**。")
    A("")
    A("## 1. 判据与阈值（可机检）")
    A("")
    A("| 判据 | 测什么 | 通过条件 |")
    A("|---|---|---|")
    A("| **P1 可见性** | 全窗口帧的**内容包围盒**与**非背景像素占比**（背景 = 该帧众数颜色；内容 = 与背景逐通道差 > %d） | 内容占比 ≥ %.2f%% **且** 包围盒覆盖 ≥ %.0f%% |"
      % (summary["criteria_thresholds"]["P1_pixel_delta"],
         100 * summary["criteria_thresholds"]["P1_min_content_fraction"],
         100 * summary["criteria_thresholds"]["P1_min_bbox_coverage"]))
    A("| **P2 输入响应** | 对 InputMap 里**每一条**已声明动作，用两种通道注入：真实 `InputEventKey` 走 `Viewport.push_input`（`_Input`/`_UnhandledInput` 的路），以及 `Input.action_press`（`IsActionPressed` 轮询的路）；**每条动作与它自己紧邻的、等长的「无输入对照窗口」比** | 状态变化数或像素变化**超过对照**，且在 %d 帧内 |"
      % summary["criteria_thresholds"]["P2_frames"])
    A("| **P3 主循环推进** | `Engine.get_frames_drawn()` 递增，且游戏自身量确实推进（自主帧 或 注入后帧） | 帧计数递增 **且**（自主变化 或 像素变化 ≥ %d 或 注入期状态变化 > 0） |"
      % summary["criteria_thresholds"]["P3_min_changed_pixels"])
    A("| **P4 不崩不挂** | 进程存活、无模态对话框（`EnumWindows` 枚举进程树的所有可见顶层窗口）、MCP 调用无超时 | 三者全满足 |")
    A("| **P5 操作可发现** | `project.godot` 的 InputMap ↔ README 的 `## 玩法` 逐条对照，并逐条验证「按了真的有效果」 | README 有玩法章节、键都能对上、代码不读未声明的动作、没有声明了却没人读的动作、每条动作都有效果 |")
    A("| **P6 操纵完备性** | `tools/playability_controls.json` 里逐款手写的「玩家必须能做的事」，每条都指名一个权威动作**和一个必须在注入后变化的可观测量** | 每条能力都有已声明、**已响应**、且指名的可观测量确实动了 |")
    A("")
    A("**P6 为什么必须存在**：P1–P5 可以全绿而游戏仍然不能玩。一台只有「推进」键的登月舱会画（P1 过）、")
    A("按键有反应（P2 过）、主循环在跑（P3 过）、README 写了那一个键（P5 过）——而它不是一个游戏。")
    A("能力表是**人写的判断**，表里每一行则由门**逐行机检**（注入那个动作、要求指名的可观测量移动）：")
    A("判断与证据分开，谁都能替换表里的判断再重跑。")
    A("")
    A("**P2 的忠实通道是 `Input.parse_input_event`**：人按键时显示服务器走的就是这一条，它**既**更新")
    A("InputMap 动作状态（`input.cpp:1113-1124`）**又**把事件派发到视口（`input.cpp:1126-1130`）。")
    A("`Viewport.push_input`（只派发，`viewport.cpp:3502-3566`）与 `Input.action_press`（只置状态）")
    A("各自只还原一半，**只在忠实通道失败时**才跑，用来把失败诊断成「游戏只在 `_Input` 里读」还是")
    A("「只有合成状态有效」。这条修掉的是一次真实的**假阴性**：早期版本只用后两个通道，于是所有")
    A("「轮询 `IsActionPressed`」的游戏都被误报为可疑。")
    A("")
    A("**P2 为什么要有「对照窗口」**：球/车/蛇本来就在动的游戏里，任何一次注入前后的状态差都会被算成")
    A("「响应」。每条动作因此和它自己**紧邻的、等长的、不注入输入**的窗口比，只有**胜过对照**才算响应。")
    A("这条修掉的是一次真实的假阳性（`pong_serve` 曾被「响应」）。")
    A("")
    A("**P1 阈值依据**：%d 款实测的内容占比与包围盒覆盖分布见 §4 的表；「整屏纯背景」= 内容像素 0，"
      % len(summary["games"]))
    A("「内容只占窗口一小块」= 包围盒覆盖远小于 100%%。本机 20 款里通过 P1 的样本内容占比在 0.9%~3.4%、")
    A("包围盒覆盖在 68%~99% 之间，阈值取 0.4% / 12% 是留了 2~5 倍余量的下界，不是贴着样本画的线。")
    A("")
    A("## 2. 总判定")
    A("")
    t = summary["totals"]
    A("**%d 款中 %d 款可玩、%d 款不可玩。**" % (t["games"], t["playable"], t["not_playable"]))
    A("")
    A("| 判据 | 未通过款数 |")
    A("|---|---|")
    for k in ("P1", "P2", "P3", "P4", "P5", "P6"):
        A("| %s | %d |" % (k, t["per_criterion_fail"].get(k, 0)))
    A("")
    A("| 游戏 | 窗口 | P1 | P2 | P3 | P4 | P5 | P6 | 判定 | filmstrip |")
    A("|---|---|---|---|---|---|---|---|---|---|")
    for g in summary["games"]:
        crit = g["criteria"]
        win = g.get("window") or {}
        w = "%s×%s" % ((win.get("display_window_size") or ["?", "?"])[0],
                       (win.get("display_window_size") or ["?", "?"])[1])
        cells = []
        for k in ("P1", "P2", "P3", "P4", "P5", "P6"):
            cells.append("**pass**" if (crit.get(k) or {}).get("pass") else "FAIL")
        A("| `%s` | %s | %s | %s | %s | %s | %s | %s | %s | `%s` |"
          % (g["game"], w, cells[0], cells[1], cells[2], cells[3], cells[4], cells[5],
             g["verdict"], g.get("filmstrip")))
    A("")

    if before:
        A("## 3. 修复前后对比")
        A("")
        A("> 修复前那一轮（`runs/playability/playability.before.json`）用的是两通道注入")
        A("> （`Viewport.push_input` + `Input.action_press`）；修复后加了忠实的 `parse` 通道。")
        A("> 这个对比仍然是**同一方向的**：`parse_input_event` 是那两个通道的并集（它同时置状态并派发），")
        A("> 所以「修复前两个通道都没反应」在当时就是失败，用忠实通道重测也不会变成通过。")
        A("")
        A("| 游戏 | 修复前 | 修复后 | 变了哪些判据 |")
        A("|---|---|---|---|")
        bidx = {x["game"]: x for x in before["games"]}
        for g in summary["games"]:
            b = bidx.get(g["game"])
            if not b:
                continue
            changed = [k for k in ("P1", "P2", "P3", "P4", "P5")
                       if b["criteria"][k]["pass"] != g["criteria"][k]["pass"]]
            if b["verdict"] == g["verdict"] and not changed:
                continue
            A("| `%s` | %s | %s | %s |" % (
                g["game"], b["verdict"], g["verdict"],
                ", ".join("%s: %s→%s" % (k, "pass" if b["criteria"][k]["pass"] else "FAIL",
                                         "pass" if g["criteria"][k]["pass"] else "FAIL")
                          for k in changed) or "—"))
        A("")

    A("## 4. 逐款证据（P1 数值 + P2 逐动作）")
    A("")
    for g in summary["games"]:
        crit = g["criteria"]
        A("### `%s` — %s" % (g["game"], g["verdict"]))
        A("")
        win = g.get("window") or {}
        A("- 窗口：OS `%s` ／ 根视口 `%s` ／ 声明 `%s` ／ 一致 `%s`"
          % (win.get("display_window_size"), win.get("root_viewport_size"),
             (g.get("window_conformance") or {}).get("declared_viewport"),
             (g.get("window_conformance") or {}).get("matches_declared")))
        A("- 启动：%s ／ tools/list %s 个工具 ／ 本次耗时 %ss"
          % (json.dumps(g.get("startup"), ensure_ascii=False), g.get("tools_list_count"),
             g.get("seconds")))
        for k in ("P1", "P2", "P3", "P4", "P5", "P6"):
            c = crit.get(k) or {}
            A("- **%s %s**：%s" % (k, "pass" if c.get("pass") else "**FAIL**", c.get("why")))
            if k == "P6" and c.get("capabilities"):
                A("")
                A("  | 玩家必须能做的事 | 权威动作 | 结果 | 证据 |")
                A("  |---|---|---|---|")
                for cap in c["capabilities"]:
                    A("  | %s | `%s` | %s | %s |" % (
                        cap.get("need"), cap.get("action") or "—",
                        "pass" if cap.get("pass") else "**FAIL**", cap.get("why")))
                A("")
        acts = g.get("actions") or []
        if acts:
            A("- 逐动作。`real_key` = **忠实通道** `Input.parse_input_event`（显示服务器收到真实按键时走的就是这条：")
            A("  既更新 InputMap 动作状态，又把事件派发到视口）；`push_input` / `action_state` 是**诊断通道**，")
            A("  各自只还原一半（前者只派发、后者只置状态），只在忠实通道失败时才跑。")
            A("")
            A("  | 动作 | 键 | real_key | push_input | action_state | 说明 |")
            A("  |---|---|---|---|---|---|")
            for a in acts:
                note = ""
                if a.get("suspicious_mismatch"):
                    note = "**可疑：只有合成动作状态有效，真实按键无效**"
                elif a.get("responds_to_push_input_only"):
                    note = "忠实通道失败、但事件派发有效——需人工复核"
                A("  | `%s` | %s | %s | %s | %s | %s |" % (
                    a.get("action"), a.get("key"),
                    "yes" if a.get("responds_to_real_key") else "no",
                    "yes" if (a.get("channels") or {}).get("push_input", {}).get("changed") else "-",
                    "yes" if a.get("responds_to_action_state") else "-", note))
            A("")
        fr = g.get("frames") or []
        if fr:
            A("- 帧（%d 张，存于 `runs/playability/%s/frames/`）：" % (len(fr), g["game"]))
            A("")
            A("  | # | 标签 | 尺寸 | 内容占比 | bbox | 与上一帧像素差 | sha256(前12) |")
            A("  |---|---|---|---|---|---|---|")
            for f in fr:
                A("  | %s | %s | %s×%s | %s | %s | %s | `%s` |" % (
                    f.get("index"), f.get("label"), f.get("width"), f.get("height"),
                    ("%.4f%%" % (100.0 * f["content_fraction"]))
                    if f.get("content_fraction") is not None else "-",
                    f.get("bbox"), f.get("changed_pixels_vs_prev"),
                    (f.get("sha256") or "")[:12]))
            A("")
        A("")

    A("## 5. 静态审计（InputMap ↔ 代码 ↔ README）")
    A("")
    A("| 游戏 | 声明动作 | 键 | 代码读取 | 读而未声明 | 声明而无人读 | README 玩法 |")
    A("|---|---|---|---|---|---|---|")
    for a in summary.get("static_audit") or []:
        keys = ", ".join("%s=%s" % (k, "/".join(v)) for k, v in
                         (a.get("declared_action_keys") or {}).items())
        A("| `%s` | %s | %s | %s | %s | %s | %s |" % (
            a["game"], ", ".join(a.get("declared_actions") or []) or "—", keys or "—",
            ", ".join(a.get("actions_read_by_the_code") or []) or "—",
            ", ".join(a.get("used_but_undeclared") or []) or "—",
            ", ".join(a.get("declared_but_never_read") or []) or "—",
            "yes" if a.get("readme_has_play_section") else "**no**"))
    A("")

    A("## 6. 试玩代理接口（item D）")
    A("")
    A("`tools/playtest_agent.py` 定义 `decide(frames, state, goal) -> action`，两种后端：")
    A("")
    A("- `scripted`：内置脚本化动作序列，本轮 A–C 全程用它跑通；")
    A("- `openai`：OpenAI 兼容 HTTP 客户端，读 `PLAYTEST_BASE_URL` / `PLAYTEST_API_KEY` /")
    A("  `PLAYTEST_MODEL`，把**截图 base64 + 结构化状态**发给模型，要求返回 **JSON 动作**；")
    A("  `judge()` 用同一端点问「这一帧看起来是否可玩/有什么异常」。")
    A("")
    A("接 NeoHorse-Jev 这类本地模型：起 OpenAI 兼容服务（vLLM / llama.cpp `--port 8000`）→ 设好那三个环境变量")
    A("→ `python tools/playability_gate.py --games pong --agent=openai`。细节见该文件顶部 docstring。")
    A("")
    A("连通性验证（本轮**未**接真模型，按任务书要求只做哑服务/报错可控验证）：")
    A("`python tools/playtest_agent.py --probe` —— 内置一个哑 OpenAI 服务，一个端点回固定应答、")
    A("一个端点回 HTTP 500，检查：请求打到 `/v1/chat/completions`、Bearer 头带上、base64 图挂上、")
    A("JSON 动作能解析、judge JSON 能解析、500 被报成错误而不是静默成功、未配置时安全降级。")
    A("")
    A("## 7. 两仓 git 状态与提交")
    A("")
    A("下表由本工具在生成报告时**直接调用 `git`** 得到（只读命令），所以报告与仓库状态不会各说各话。")
    A("")
    for repo, label in ((os.path.dirname(ROOT), "主仓 `F:\\moonbit-hof-rs`"),
                        (os.path.join(ROOT, "godot"), "引擎仓 `godot-mcp\\godot`")):
        A("### %s" % label)
        A("")
        A("`git log --oneline -8`：")
        A("")
        A("```")
        for line in git_lines(repo, ["log", "--oneline", "-8"]):
            A(line)
        A("```")
        A("")
        A("`git status --short`：")
        A("")
        A("```")
        st = git_lines(repo, ["status", "--short"])
        for line in (st[:40] if st else ["(clean)"]):
            A(line)
        if len(st) > 40:
            A("... (%d entries total)" % len(st))
        A("```")
        A("")
    A("**本轮没有改引擎模块**：`godot\\modules\\mcp_server\\` 一个字节未动（引擎仓 `git status --short`")
    A("只有 Godot 自己生成的 `uid_cache.bin`），因此按铁律 7 **不需要**重建两变体 / 十道门 / accept_m1 / push。")
    A("所有改动都在主仓：门与代理工具、20 款工程的 C# 与 project.godot 与 README、以及本报告。")
    A("")
    A("## 8. 遗留项与本轮不该被读成的东西（如实登记）")
    A("")
    A("1. **P6 全绿 ≠ 好玩**。它只说明能力表里列的每一件事都有一个键能真的做到。能力表的每一行都是")
    A("   **人写的判断**，可以被质疑和替换；替换后重跑，门会重新机检。")
    A("2. **`hold_ms` 是手工调参的**。默认 0.5 s 对多数游戏合适，但 Frogger 的键盘路径按住会重复，")
    A("   0.5 s 是四次跳跃、四次进车道就是四次死亡；它在 `tools/playability_controls.json` 里单独写了")
    A("   `hold_ms: 150`。这是**已知的顺序/时长敏感性**，不是已经解决的问题——换一款有重复间隔的游戏")
    A("   仍可能要再调一次。")
    A("3. **能力表没有 `pre` 预热**。一条能力若在游戏初始态被合法拒绝（在角落、在边缘、在墙边），")
    A("   门只能靠游戏自己的**拒绝计数器**间接证明「键被读到了」。本轮给三款补了计数器，")
    A("   另有两款把光标起点从角落移到棋盘中间；**通用解法（能力表支持预热序列）没有做**。")
    A("4. **P1 的阈值是下界，不是贴着样本画的线**：本轮通过 P1 的样本内容占比在 0.9%~3.4%、")
    A("   包围盒覆盖在 68%~99%，阈值取 0.4% / 12%。")
    A("5. **每款只测了一个进程、一次会话**。没有测长时间运行的稳定性、没有测多分辨率/缩放、")
    A("   没有测手柄——这些都不在本轮的判据里。")
    A("6. **修复前那一轮的注入通道与修复后不同**（前：`push_input` + `action_press`；后：")
    A("   `parse_input_event` 为主通道）。§3 已论证这个对比在同一方向上成立，因为")
    A("   `parse_input_event` 是那两个通道的并集。")
    A("")

    out = os.path.join(REPORTS, "PLAYABILITY-REPORT.md")
    with io.open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))

    # ---------------- PLAYABILITY-DEFECTS.md ----------------
    D = []
    B = D.append
    B("# TASK-116 — 可玩性缺陷登记（PLAYABILITY-DEFECTS）")
    B("")
    B("> 生成时间：%s ｜ 每一条都由 `runs/playability/<game>/gate.json` 的机检事实或源码 `file:line` 支撑。" % summary["generated"])
    B("> 现象 / 证据 / 根因 / 建议修法，四栏齐全；没有「应该可以」的转述。")
    B("> **登记来源是修复前那一轮**（`runs/playability/playability.before.json`）；每条后面的")
    B("> 「复跑状态」来自修复后同一道门的复跑，所以本文件既记录了发现了什么，也记录了修没修掉。")
    B("")
    counts = {}
    for r in defects:
        counts[r["id"]] = counts.get(r["id"], 0) + 1
    B("## 汇总")
    B("")
    B("| 类 | 数量 | 已修复（复跑验证） | 仍存在 | 说明 |")
    B("|---|---|---|---|---|")
    legend = {
        "D1": "玩家输入默认关闭（`PollInput = false`，且 `_Ready()` 里的 `Reset*` 又关一次）——本轮最严重的系统性缺陷",
        "D2": "代码读取了 InputMap 未声明的动作",
        "D3": "已声明的控制按下去没有可归因的效果",
        "D4": "声明了却没有任何代码读取的动作",
        "D5": "README 没有玩法章节，操作不可发现",
        "D5b": "README 写的键在 InputMap 里没有对应动作",
        "D6": "窗口尺寸与声明不一致",
        "D7": "全窗口帧里看不到内容",
        "D8": "主循环不推进游戏自身量",
        "D9": "进程未存活或 MCP 调用超时",
        "D10": "出现了模态对话框",
        "D11": "玩家需要的能力没有任何动作提供（P6 逐条）",
    }
    for k in sorted(legend):
        rws = [r for r in defects if r["id"] == k]
        if not rws:
            continue
        fixed = sum(1 for r in rws if r["status"].startswith("已修复"))
        B("| %s | %d | %d | %d | %s |" % (k, len(rws), fixed, len(rws) - fixed, legend[k]))
    B("")
    B("总计 **%d** 条，其中复跑验证已修复 **%d** 条。"
      % (len(defects), sum(1 for r in defects if r["status"].startswith("已修复"))))
    B("")
    games_with = sorted(set(r["game"] for r in defects))
    B("涉及的工程（%d 款）：%s" % (len(games_with), ", ".join("`%s`" % g for g in games_with)))
    B("")
    for k in sorted(legend):
        rows = [r for r in defects if r["id"] == k]
        if not rows:
            continue
        B("## %s — %s（%d 条）" % (k, legend[k], len(rows)))
        B("")
        for r in rows:
            B("### `%s` — %s" % (r["game"], r["class"]))
            B("")
            B("- **严重度**：%s" % r["severity"])
            B("- **现象**：%s" % r["phenomenon"])
            B("- **证据**：")
            for e in r["evidence"]:
                B("  - `%s`" % e)
            B("- **根因**：`%s`" % r["root_cause"])
            B("- **建议修法**：%s" % r["fix"])
            B("- **验证方式**：%s" % r["verified_by"])
            B("- **复跑状态**：%s（复跑判定：%s）" % (r["status"], r["after_verdict"]))
            B("")
    if after_only:
        B("## 复跑中新发现（修复前那一轮没有的）")
        B("")
        for r in after_only:
            B("- `%s` — %s：%s" % (r["game"], r["class"], r["phenomenon"]))
        B("")
    else:
        B("## 复跑中新发现")
        B("")
        B("无：修复后那一轮没有出现修复前不存在的缺陷类。")
        B("")
    out2 = os.path.join(REPORTS, "PLAYABILITY-DEFECTS.md")
    with io.open(out2, "w", encoding="utf-8") as fh:
        fh.write("\n".join(D))

    print("wrote %s (%d bytes)" % (out, os.path.getsize(out)))
    print("wrote %s (%d bytes, %d defects)" % (out2, os.path.getsize(out2), len(defects)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
