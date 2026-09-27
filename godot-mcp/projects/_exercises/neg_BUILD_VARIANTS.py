#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""neg_BUILD_VARIANTS.py -- TASK-129 D-D: build the declarative negative variants.

What this is
------------
Four failure modes, each a COPY of a real project under `projects/_exercises/neg_*`, with
exactly ONE declaration changed in the copy's `scenes/main.tscn` -- no C# is edited and
nothing is rebuilt, so the variant is a real build of a real game that fails in a declared
way.  `projects/<game>/` is never written to (iron rule 2).

Why a .tscn patch is the right instrument here
----------------------------------------------
These games already export the switch that turns the failure on/off in their own scene:
`PollInput` is an `[Export] public bool` on 16 of the 20 games, and it is serialised into
the scene file.  A copy with `PollInput = false` therefore reproduces **exactly** the
pre-fix failure TASK-128 measured in the exported artifacts, while a `process_mode = 4`
or `visible = false` line produces a failure the engine itself defines.

The four modes
--------------
1. neg_input_dead    (minesweeper) `PollInput = false` on the root: the game never reads
                     the InputMap, so every key is a no-op.  Expected: P2/P5/P6 FAIL,
                     P1/P3 PASS (the autonomous auto-reveal clock keeps running).
2. neg_black_screen  (snake)       `visible = false` on the root: the game runs and its
                     state moves, but nothing reaches the screen.  Expected: P1 FAIL,
                     P2..P6 PASS -- the pure "not rendering" mode.
3. neg_frozen        (breakout)    `process_mode = 4` (DISABLED) on the root: rendering
                     continues (`Engine.get_frames_drawn()` still advances) while nothing
                     in the game advances.  Expected: P3 FAIL, and P2 fails with it.
4. neg_hud_missing   (tetris)      `visible = false` on the HUD nodes only: the game field
                     is intact and playable, the interface is gone.  Expected: NO machine
                     criterion catches it -- P1..P6 all PASS -- which is the gate's blind
                     spot and the reason a VISION backend is worth wiring in.  Declared as
                     an expectation, measured in the report.

Reproduce (from godot-mcp, cmd, no shell redirection):
    D:\\Anaconda\\python.exe projects\\_exercises\\neg_BUILD_VARIANTS.py
    D:\\Anaconda\\python.exe projects\\_exercises\\neg_BUILD_VARIANTS.py --verify
"""

from __future__ import print_function

import argparse
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECTS = os.path.dirname(HERE)
ROOT = os.path.dirname(PROJECTS)
ENGINE = os.path.join(ROOT, "godot", "bin", "godot.windows.editor.x86_64.mono.console.exe")

# name -> what to copy, and the ONE declaration that is added to a node block of main.tscn
VARIANTS = {
    "neg_input_dead": {
        "source": "minesweeper",
        "failure_mode": "input disconnected (the game never reads the InputMap)",
        "node": "Main",
        "properties": [("PollInput", "false")],
        "construction": (
            "copy of projects/minesweeper; its root script exports `[Export] public bool "
            "PollInput` and gates its ONLY input path on it (`_Process` -> `if (PollInput) "
            "HandleInput();`, MinesweeperGame.cs:566).  Setting `PollInput = false` in the "
            "copy's main.tscn therefore disables every declared action without touching a "
            "line of C# -- byte-for-byte the failure TASK-128 measured in the pre-fix "
            "exports (`PollInput=false`).  The autonomous `AutoReveal` clock is NOT gated "
            "on PollInput, so the game keeps ticking and painting."),
        "expected": {
            "P1": "PASS (the board is drawn)",
            "P2": "FAIL (no declared action changes state or pixels)",
            "P3": "PASS (the autonomous clock still advances the board)",
            "P4": "PASS",
            "P5": "FAIL (the documented controls do nothing)",
            "P6": "FAIL (no capability is delivered)",
            "gate": "not_playable",
        },
    },
    "neg_black_screen": {
        "source": "snake",
        "failure_mode": "not rendering / blank window (the scene is never drawn)",
        "node": "Main",
        "properties": [("visible", "false")],
        "construction": (
            "copy of projects/snake with `visible = false` on the root Node2D of "
            "main.tscn.  The engine keeps running the game (its state still moves, the "
            "loop still counts frames) but nothing is rasterised into the window except "
            "the viewport's clear colour -- the 'blank render' mode, produced by the "
            "engine's own visibility rule rather than by repainting a PNG."),
        "expected": {
            "P1": "FAIL (a single flat colour: 0 content pixels)",
            "P2": "PASS (state still changes on input, the pixel channel is not needed)",
            "P3": "PASS (state moves autonomously)",
            "P4": "PASS",
            "P5": "PASS (the InputMap and the README still agree)",
            "P6": "PASS (the capabilities still move their observables)",
            "gate": "not_playable",
        },
    },
    "neg_frozen": {
        "source": "breakout",
        "failure_mode": "frozen (frames do not advance the game)",
        "node": "Main",
        "properties": [("process_mode", "4")],
        "construction": (
            "copy of projects/breakout with `process_mode = 4` (PROCESS_MODE_DISABLED) on "
            "the root Node2D of main.tscn.  `_Process`/`_PhysicsProcess`/input handling of "
            "that subtree are switched off, while the renderer keeps submitting the window "
            "(`Engine.get_frames_drawn()` still advances).  This is the 'frozen but the "
            "process is alive' mode that P3 exists for."),
        "expected": {
            "P1": "PASS (the initial frame is still drawn)",
            "P2": "FAIL (nothing can respond)",
            "P3": "FAIL (frames_drawn advances but no state and no pixel changes)",
            "P4": "PASS (the process is alive, no dialog)",
            "P5": "FAIL (the documented controls do nothing)",
            "P6": "FAIL (no capability is delivered)",
            "gate": "not_playable",
        },
    },
    "neg_hud_missing": {
        "source": "tetris",
        "failure_mode": "UI/controls missing (the HUD is removed)",
        "node": ["SidePanel", "PanelEdge", "HudLabel"],
        "properties": [("visible", "false")],
        "construction": (
            "copy of projects/tetris with `visible = false` on the three HUD nodes of "
            "main.tscn (`SidePanel`, `PanelEdge`, `HudLabel` -- together 240x480 px of the "
            "800x600 window).  The playfield, the piece logic and the InputMap are "
            "untouched: this is 'the interface is gone, the game is not'."),
        "expected": {
            "P1": "PASS by measurement (the remaining field still exceeds the content "
                  "threshold) -- the HUD is 24% of the window but not all of it",
            "P2": "PASS",
            "P3": "PASS",
            "P4": "PASS",
            "P5": "PASS (P5 is about the InputMap and the README, not about pixels)",
            "P6": "PASS",
            "gate": "playable -- DECLARED AS A BLIND SPOT: no machine criterion we "
                    "implemented asks whether the interface a player needs is on screen.  "
                    "The variant is kept as a real frame a VISION model can be asked about.",
        },
    },
}

SCENE_REL = os.path.join("scenes", "main.tscn")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_text(path):
    with io.open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def write_text(path, text):
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def patch_scene(text, node, properties):
    """Append `key = value` lines to the `[node name="node" ...]` block.  Idempotent."""
    lines = text.split("\n")
    starts = [i for i, ln in enumerate(lines) if ln.startswith("[")]
    changed = []
    for idx, start in enumerate(starts):
        header = lines[start]
        end = starts[idx + 1] if idx + 1 < len(starts) else len(lines)
        if not header.startswith("[node ") or ('name="%s"' % node) not in header:
            continue
        body = lines[start + 1:end]
        for key, value in properties:
            line = "%s = %s" % (key, value)
            if any(b.strip() == line for b in body):
                changed.append({"node": node, "property": key, "value": value,
                                "already_present": True})
                continue
            # drop a previous value of the same key, then append (moves the line to the end)
            body = [b for b in body if not b.strip().startswith(key + " =")]
            while body and not body[-1].strip():
                body.pop()
            body.append(line)
            changed.append({"node": node, "property": key, "value": value,
                            "already_present": False})
        lines[start + 1:end] = body + [""]
        break
    else:
        raise RuntimeError("node %r not found in the scene" % node)
    return "\n".join(lines), changed


def copy_project(source, dest):
    if os.path.isdir(dest):
        return "kept"
    shutil.copytree(os.path.join(PROJECTS, source), dest)
    return "copied"


def build(verify=False):
    results = []
    for name, spec in sorted(VARIANTS.items()):
        dest = os.path.join(HERE, name)
        action = copy_project(spec["source"], dest)
        scene = os.path.join(dest, SCENE_REL)
        original_sha = sha256_file(scene)
        text = read_text(scene)
        nodes = spec["node"] if isinstance(spec["node"], list) else [spec["node"]]
        patches = []
        for node in nodes:
            text, ch = patch_scene(text, node, spec["properties"])
            patches.extend(ch)
        write_text(scene, text)
        after_sha = sha256_file(scene)

        # the copy's own C# must still be byte-identical to the real project's
        src_cs = os.path.join(PROJECTS, spec["source"], "src")
        dst_cs = os.path.join(dest, "src")
        cs_same = True
        for fn in sorted(os.listdir(src_cs)):
            a = os.path.join(src_cs, fn)
            b = os.path.join(dst_cs, fn)
            if os.path.isfile(a) and (not os.path.isfile(b) or sha256_file(a) != sha256_file(b)):
                cs_same = False

        manifest = {
            "task": "TASK-129 D-D",
            "variant": name,
            "failure_mode": spec["failure_mode"],
            "source_project": spec["source"],
            "construction": spec["construction"],
            "patch": {"file": SCENE_REL, "edits": patches,
                      "scene_sha256_before_patch": original_sha,
                      "scene_sha256_after_patch": after_sha,
                      "csharp_sources_copied_unchanged": cs_same},
            "expected_gate_criteria": spec["expected"],
            "engine": ENGINE,
            "runnable_with": (
                "python tools/playability_gate.py --exercise %s --games %s "
                "--agent=jev --visual-agent=playjev --out-root runs/playability/negatives"
                % (name, name)),
            "no_build_needed": ("the .tscn declaration is read at load time and no C# is "
                                "changed, so the copied .NET assembly is still the source "
                                "project's -- verified by csharp_sources_copied_unchanged"),
            "projects_dir_untouched": True,
        }
        write_text(os.path.join(dest, "variant.json"),
                   json.dumps(manifest, ensure_ascii=False, indent=1, sort_keys=False))

        entry = {"variant": name, "copy": action, "scene_sha256_before": original_sha,
                 "scene_sha256_after": after_sha, "patches": patches,
                 "csharp_unchanged": cs_same}
        if verify:
            entry["headless"] = verify_headless(dest)
        results.append(entry)
        print("[%s] %s -> %s" % (name, action, dest))
        for ch in patches:
            print("    %s.%s = %s%s" % (ch["node"], ch["property"], ch["value"],
                                        "   (already present)" if ch["already_present"] else ""))
    return results


def verify_headless(project):
    """`--headless --quit-after 60`: does the variant even come up?  Exit code + tail."""
    if not os.path.isfile(ENGINE):
        return {"ran": False, "why": "engine missing: %s" % ENGINE}
    cmd = [ENGINE, "--headless", "--path", project, "--quit-after", "60"]
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           cwd=os.path.join(ROOT, "godot"), timeout=180)
    except Exception as e:  # noqa: BLE001
        return {"ran": False, "why": "%s: %s" % (type(e).__name__, e)}
    out = (p.stdout or b"").decode("utf-8", "replace")
    return {"ran": True, "exit_code": p.returncode, "cmd": " ".join(cmd),
            "tail": out[-1200:]}


def main(argv=None):
    ap = argparse.ArgumentParser(description="build the TASK-129 negative variants")
    ap.add_argument("--verify", action="store_true",
                    help="also run each variant with --headless --quit-after 60")
    ap.add_argument("--out", default=os.path.join(ROOT, "runs", "playability",
                                                  "negatives", "variants-build.json"))
    args = ap.parse_args(argv)
    results = build(verify=args.verify)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with io.open(args.out, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"task": "TASK-129 D-D", "variants": results},
                            ensure_ascii=False, indent=1))
    print("written: %s" % os.path.abspath(args.out))
    if args.verify:
        for r in results:
            h = r.get("headless") or {}
            print("  %-16s headless exit=%s" % (r["variant"], h.get("exit_code")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
