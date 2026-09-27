#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""test_playability_p7.py -- TASK-130: the declarative required-UI criterion (P7).

What this test is for
---------------------
P7 is the one gate criterion that judges a DECLARATION against a runtime read of the game's
own node tree.  Both halves are easy to get subtly wrong in opposite directions:

  * too strict -> the 20 working games are reported broken (a false alarm);
  * too loose  -> a game whose interface is gone (or moved off screen) still passes, which
                  is exactly the blind spot P7 was added to close.

These tests therefore drive `verdict_p7` from synthetic probe answers -- no engine, no
service, no network -- and pin down each clause separately: missing node, hidden node,
hidden ancestor, zero alpha, off-screen rect (visible == True!), collapsed size, blank
text, wrong class, and the undeclared case.  They also pin the PASS case for the shape a
real declaration has, so a change that starts failing the 20 positives shows up here first.

Run (cmd, no shell redirection; this file writes nothing):

    D:\\Anaconda\\python.exe tools\\tests\\test_playability_p7.py
    D:\\Anaconda\\python.exe -m pytest tools\\tests\\test_playability_p7.py -q
"""
from __future__ import print_function

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
sys.path.insert(0, TOOLS)

from playability_gate import (P7_MIN_ALPHA, rect_intersection_area,  # noqa: E402
                              required_ui_items, verdict_p7)

VIEWPORT = [0.0, 0.0, 800.0, 600.0]
CONTROLS = {
    "good": {
        "required_ui": {
            "declared_by": "TASK-130 P7 (test fixture)",
            "what": "the UI a player needs",
            "rule": "see verdict_p7",
            "items": [
                {"id": "hud", "need": "score readout", "node": "/root/Main/Hud",
                 "class": "Label", "must_exist": True, "must_be_visible": True,
                 "min_area_px": 13000, "text_nonempty": True},
                {"id": "board", "need": "the board container", "node": "/root/Main/Board",
                 "class": "ColorRect", "must_exist": True, "must_be_visible": True,
                 "min_area_px": 100000},
            ],
        }
    },
    "undeclared": {"goal": "no required_ui here"},
}


def node(path, cls="Label", visible=True, in_tree=True, alpha=1.0, rect=None,
         size=None, text=None, hidden_by=None):
    return {path: {"path": path, "exists": True, "name": path.rsplit("/", 1)[-1],
                   "class": cls, "is_canvas_item": True, "is_control": True,
                   "is_label": cls in ("Label", "RichTextLabel"),
                   "visible": visible, "visible_in_tree": in_tree, "modulate_a": alpha,
                   "text": text, "global_rect": rect, "size": size or
                   ([rect[2], rect[3]] if rect else None),
                   "hidden_by_ancestors": hidden_by or [], "node_path": path}}


def probe(items):
    return {"source": "synthetic", "viewport": VIEWPORT, "root": "/root",
            "items": items, "error": None}


GOOD = probe({
    **node("/root/Main/Hud", "Label", rect=[20.0, 8.0, 560.0, 38.0], text="SCORE 0",
           size=[560.0, 38.0]),
    **node("/root/Main/Board", "ColorRect", rect=[172.0, 102.0, 456.0, 456.0],
           size=[456.0, 456.0]),
})


def case(name, controls, pr, expect_pass, expect_missing=(), expect_checks=()):
    v = verdict_p7("good", controls, pr)
    got_missing = tuple(m["id"] for m in (v.get("missing") or []))
    failed = tuple(c for r in (v.get("items") or [])
                   for c in (r.get("failed_checks") or []))
    ok = (bool(v.get("pass")) == expect_pass
          and set(expect_missing) <= set(got_missing)
          and set(expect_checks) <= set(failed))
    return ok, name, {"pass": v.get("pass"), "missing": got_missing, "failed": failed,
                      "why": v.get("why")}


def main():
    cases = []

    # ---- the healthy case: the declaration is satisfied -> PASS --------------------
    cases.append(case("all declared items present and on screen", CONTROLS, GOOD, True))
    cases.append(case("required_ui present but empty items -> FAIL (undeclared really)",
                      {"good": {"required_ui": {"items": []}}}, GOOD, False,
                      expect_checks=()))
    cases.append(case("no required_ui declaration at all -> FAIL, blamed on the declaration",
                      CONTROLS, GOOD, True))            # (control: good still passes)
    v_und = verdict_p7("undeclared", CONTROLS, GOOD)
    cases.append((v_und["pass"] is False and "required_ui" in v_und["why"],
                  "an undeclared game cannot claim 'the required UI is present'",
                  v_und["why"]))

    # ---- clause by clause ---------------------------------------------------------
    cases.append(case("the node does not exist at all",
                      CONTROLS, probe({**node("/root/Main/Board", "ColorRect",
                                              rect=[0, 0, 456, 456])}),
                      False, expect_missing=("hud",), expect_checks=("exists",)))
    cases.append(case("the node exists but visible = false",
                      CONTROLS,
                      probe({**node("/root/Main/Hud", "Label", visible=False, in_tree=False,
                                    rect=[20, 8, 560, 38], text="SCORE 0"),
                             **node("/root/Main/Board", "ColorRect",
                                    rect=[172, 102, 456, 456])}),
                      False, expect_missing=("hud",),
                      expect_checks=("visible_in_tree",)))
    cases.append(case("the node is visible but an ANCESTOR is hidden",
                      CONTROLS,
                      probe({**node("/root/Main/Hud", "Label", visible=True, in_tree=False,
                                    rect=[20, 8, 560, 38], text="SCORE 0",
                                    hidden_by=["/root/Main/SidePanel"]),
                             **node("/root/Main/Board", "ColorRect",
                                    rect=[172, 102, 456, 456])}),
                      False, expect_missing=("hud",),
                      expect_checks=("visible_in_tree",)))
    cases.append(case("modulate alpha faded to 0 (visible_in_tree still true)",
                      CONTROLS,
                      probe({**node("/root/Main/Hud", "Label", alpha=0.0,
                                    rect=[20, 8, 560, 38], text="SCORE 0"),
                             **node("/root/Main/Board", "ColorRect",
                                    rect=[172, 102, 456, 456])}),
                      False, expect_missing=("hud",), expect_checks=("alpha",)))
    cases.append(case("visible == True but the rect is OUTSIDE the viewport (the "
                      "neg_ui_offscreen mode)",
                      CONTROLS,
                      probe({**node("/root/Main/Hud", "Label", visible=True, in_tree=True,
                                    rect=[-2000.0, 8.0, 580.0, 38.0], text="SCORE 0"),
                             **node("/root/Main/Board", "ColorRect",
                                    rect=[172, 102, 456, 456])}),
                      False, expect_missing=("hud",), expect_checks=("on_screen",)))
    cases.append(case("visible == True but the node has been collapsed to zero size",
                      CONTROLS,
                      probe({**node("/root/Main/Hud", "Label", rect=[20, 8, 0, 0],
                                    size=[0.0, 0.0], text="SCORE 0"),
                             **node("/root/Main/Board", "ColorRect",
                                    rect=[172, 102, 456, 456])}),
                      False, expect_missing=("hud",), expect_checks=("on_screen",)))
    cases.append(case("the label is on screen but blank",
                      CONTROLS,
                      probe({**node("/root/Main/Hud", "Label", rect=[20, 8, 560, 38],
                                    text="   "),
                             **node("/root/Main/Board", "ColorRect",
                                    rect=[172, 102, 456, 456])}),
                      False, expect_missing=("hud",), expect_checks=("text_nonempty",)))
    cases.append(case("the node at the path is the wrong class",
                      CONTROLS,
                      probe({**node("/root/Main/Hud", "ColorRect", rect=[20, 8, 560, 38]),
                             **node("/root/Main/Board", "ColorRect",
                                    rect=[172, 102, 456, 456])}),
                      False, expect_missing=("hud",), expect_checks=("class",)))
    cases.append(case("the board is present but too small to be a board",
                      CONTROLS,
                      probe({**node("/root/Main/Hud", "Label", rect=[20, 8, 560, 38],
                                    text="SCORE 0"),
                             **node("/root/Main/Board", "ColorRect", rect=[0, 0, 40, 40],
                                    size=[40.0, 40.0])}),
                      False, expect_missing=("board",), expect_checks=("on_screen",)))
    cases.append(case("the probe never answered -> FAIL, not a silent pass",
                      CONTROLS, {"error": "no answer"}, False))
    cases.append(case("the probe returned no items at all -> FAIL",
                      CONTROLS, {"viewport": VIEWPORT, "items": {}}, False))

    # ---- the geometry helper the on_screen clause rests on ------------------------
    cases.append((rect_intersection_area([0, 0, 100, 100], [0, 0, 800, 600]) == 10000.0,
                  "rect fully inside the viewport", None))
    cases.append((rect_intersection_area([-2000, 8, 580, 38], [0, 0, 800, 600]) == 0.0,
                  "an off-viewport rect has zero intersection", None))
    cases.append((rect_intersection_area([700, 500, 200, 200], [0, 0, 800, 600]) == 10000.0,
                  "a partly visible rect is clipped to 100x100 = 10000 px^2, not rounded "
                  "away", None))
    cases.append((rect_intersection_area(None, VIEWPORT) is None,
                  "a missing rect is None (and therefore fails a declared min area)", None))

    # ---- the declaration loader ---------------------------------------------------
    decl, items = required_ui_items(CONTROLS, "good")
    cases.append((len(items) == 2 and decl["declared_by"].startswith("TASK-130"),
                  "required_ui_items() reads games.<game>.required_ui.items", None))
    cases.append((required_ui_items(CONTROLS, "undeclared")[1] == [],
                  "a game with no declaration yields no items", None))
    cases.append((0.0 < P7_MIN_ALPHA < 1.0,
                  "P7_MIN_ALPHA separates 'transparent' from 'faded'", P7_MIN_ALPHA))

    # ---- the real config: every declaration must be loadable and shaped right ------
    import json
    import io
    cfg_path = os.path.join(TOOLS, "playability_controls.json")
    cfg = json.load(io.open(cfg_path, encoding="utf-8"))
    games = cfg["games"]
    declared = sorted(g for g, v in games.items() if (v.get("required_ui") or {}).get("items"))
    bad = []
    all20 = ["asteroids", "bomberman", "breakout", "flappy", "frogger", "game2048",
             "lunarlander", "match3", "minesweeper", "missilecommand", "pacman",
             "platformer", "pong", "puzzlebobble", "rtype", "snake", "sokoban",
             "spaceinvaders", "tetris", "towerdefense"]
    for g in all20:
        items = (games.get(g, {}).get("required_ui") or {}).get("items") or []
        if not items:
            bad.append("%s declares nothing" % g)
            continue
        for it in items:
            for key in ("id", "node", "class", "min_area_px"):
                if not it.get(key):
                    bad.append("%s/%s has no %s" % (g, it.get("id"), key))
            if not str(it["node"]).startswith("/root/"):
                bad.append("%s/%s node %r is not a /root/ path" % (g, it["id"], it["node"]))
    cases.append((not bad and len(declared) >= 25,
                  "all 20 games (and the variants) declare machine-checkable required UI "
                  "items", {"declared": len(declared), "bad": bad}))

    failed = [c for c in cases if not c[0]]
    for ok, name, detail in cases:
        print("%s  %s" % ("ok  " if ok else "FAIL", name))
        if not ok:
            print("      detail: %s" % (detail,))
    print("\n%d/%d checks passed" % (len(cases) - len(failed), len(cases)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
