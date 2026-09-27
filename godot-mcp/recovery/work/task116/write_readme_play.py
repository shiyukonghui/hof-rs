#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""TASK-116 fix D5: give every game a `## 玩法` section, generated from its own InputMap.

The defect: 19 of the 20 games document nothing.  The only place the controls exist
is `project.godot`'s `[input]` section, which a player never reads, so "how do I
play this" has no answer on disk.  The gate checks the README against the InputMap
mechanically (P5), so this generator is written to be *incapable* of lying: every
row it emits comes from the parsed `[input]` block, and the capability wording comes
from `tools/playability_controls.json`, which is the same table P6 verifies against
the running game.

Rows are ordered by the capability table (the order a player needs them), and any
declared action the table does not name is listed afterwards and marked as a
test/auxiliary action, because that is what it is.
"""

import io
import os
import re
import sys

ROOT = r"F:\moonbit-hof-rs\godot-mcp"
PROJECTS = os.path.join(ROOT, "projects")
TOOLS = os.path.join(ROOT, "tools")
sys.path.insert(0, TOOLS)
import playability_gate as pg  # noqa: E402

FENCE = "## 玩法"


def read(path):
    for enc in ("utf-8", "utf-8-sig"):
        try:
            return io.open(path, encoding=enc).read()
        except Exception:
            continue
    return None


def build_section(game):
    proj = pg.parse_project(game)
    controls = pg.load_controls().get(game) or {}
    caps = controls.get("capabilities") or []
    viewport = proj["declared_viewport"] or [800, 600]
    lines = [FENCE, ""]
    goal = controls.get("goal")
    lines.append("%d×%d。%s" % (viewport[0], viewport[1],
                                ("目标：%s。" % goal) if goal else ""))
    lines.append("")
    lines.append("| 操作 | 动作名 | 键 |")
    lines.append("|---|---|---|")
    seen = set()
    for cap in caps:
        action = cap.get("action")
        if not action or action not in proj["actions"]:
            continue
        keys = proj["actions"][action]["keys"]
        lines.append("| %s | `%s` | %s |" % (cap.get("need"), action,
                                             " / ".join("`%s`" % k for k in keys) or "—"))
        seen.add(action)
    extra = [a for a in proj["actions_declared"] if a not in seen]
    if extra:
        lines.append("")
        lines.append("仅测试/辅助用的动作（无头测试推进局面用，玩家不需要按）：")
        lines.append("")
        lines.append("| 动作名 | 键 |")
        lines.append("|---|---|")
        for a in extra:
            keys = proj["actions"][a]["keys"]
            lines.append("| `%s` | %s |" % (a, " / ".join("`%s`" % k for k in keys) or "—"))
    lines.append("")
    lines.append("> 动作名就是 `project.godot` 的 `[input]` 里的名字，可用 "
                 "`running_game_capture_screenshot` + `Input.action_press` 由 MCP 端点精确复现；")
    lines.append("> 可玩性门（`tools/playability_gate.py`）会逐条注入这些键，并要求**确实出现可归因的状态或像素变化**。")
    lines.append("")
    return "\n".join(lines)


def main(apply):
    games = sorted(d for d in os.listdir(PROJECTS)
                   if os.path.isdir(os.path.join(PROJECTS, d))
                   and not d.startswith("_") and not d.startswith("mcp"))
    for g in games:
        path = os.path.join(PROJECTS, g, "README.md")
        txt = read(path)
        if txt is None:
            print("!! %s: README.md missing" % g)
            continue
        section = build_section(g)
        m = re.search(r"^##\s*玩法.*?(?=^##\s|\Z)", txt, re.M | re.S)
        if m:
            if g == "pong":
                print("keep %s: its 玩法 section is the hand-written original" % g)
                continue
            new = txt[:m.start()] + section + "\n" + txt[m.end():]
            how = "replaced"
        else:
            anchor = re.search(r"^##\s*构建", txt, re.M)
            if not anchor:
                print("!! %s: no '## 构建' anchor and no 玩法 section" % g)
                continue
            new = txt[:anchor.start()] + section + "\n" + txt[anchor.start():]
            how = "inserted"
        if apply:
            with io.open(path, "w", encoding="utf-8", newline="") as fh:
                fh.write(new)
            print("%s %s (%d actions, %d rows)" % (how, g, len(pg.parse_project(g)["actions_declared"]),
                                                   len(pg.parse_project(g)["actions_declared"])))
        else:
            print("would %s %s:\n%s" % (how, g, section))
    return 0


if __name__ == "__main__":
    sys.exit(main("--apply" in sys.argv))
