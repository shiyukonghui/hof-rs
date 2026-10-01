#!/usr/bin/env python3
"""DR-76 — derive the interaction fixtures from the frozen `smoke-t10` payloads.

Why this exists (DR-73 acceptance A1/O1): the previous batch's interaction test
fixture **invented** a `text` member on the HUD `Label` nodes of
`running_game_get_scene_tree`.  The real engine never sends one — every one of the
10 frozen scene-tree payloads from five rounds carries exactly `name`, `path` and
`type` — so the test was green against a tree shape that cannot occur, and the
window it exercised always answered `COIN_COUNTER_UNREADABLE` on real hardware.
A fixture that hand-writes the engine's payload shape is exactly what failed.  The
fixtures below are therefore *derived from the frozen bytes*, and this script is
the derivation.

Read-only: nothing under `runs/**` is written, not even a temporary file.

Run from the repository root:

    python scripts/derive_dr76_fixtures.py

Outputs (all under `tests/fixtures/dr76/`):

  scene_tree_smoke_t10.json                  byte-for-byte copy of
      runs/smoke-t10/iter-1/candidate/.hoh/deterministic/raw/scene_tree.json
  hud_labels_smoke_t10.json                  byte-for-byte copy of
      runs/smoke-t10/iter-1/candidate/.hoh/evidence/hud-labels.json
  interaction_position_samples_smoke_t10.json
      the reduced `Player.position` x-series of the four `input_replay` windows,
      lifted out of
      runs/smoke-t10/iter-1/candidate/.hoh/deterministic/raw/input_replay.json
      (the raw file is 148 KB; the four windows' samples are 160 numbers), plus
      the goal geometry the frozen scene declares.
  MANIFEST.json                              sources, sha256 of the copies, and
      this command.
"""

from __future__ import annotations

import hashlib
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANDIDATE = os.path.join(
    REPO, "runs", "smoke-t10", "iter-1", "candidate", ".hoh"
)
RAW = os.path.join(CANDIDATE, "deterministic", "raw")
OUT = os.path.join(REPO, "tests", "fixtures", "dr76")

SCENE_TREE = os.path.join(RAW, "scene_tree.json")
HUD_LABELS = os.path.join(CANDIDATE, "evidence", "hud-labels.json")
INPUT_REPLAY = os.path.join(RAW, "input_replay.json")

DERIVATION = "python scripts/derive_dr76_fixtures.py"


def sha256(path: str) -> str:
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def copy_bytes(source: str, target: str) -> None:
    """A byte-for-byte copy: the fixture *is* the frozen payload."""
    with open(source, "rb") as handle:
        payload = handle.read()
    with open(target, "wb") as handle:
        handle.write(payload)


def inner_text(call: dict) -> dict:
    return json.loads(call["payload"]["content"][0]["text"])


def position_windows() -> list:
    raw = json.load(open(INPUT_REPLAY, encoding="utf-8"))
    windows = []
    for call in raw["calls"]:
        if call.get("tool") != "running_game_get_node_property_samples":
            continue
        args = call.get("args") or {}
        if "position" not in (args.get("properties") or []):
            continue
        inner = inner_text(call)
        xs = [
            sample["position"]["x"]
            for sample in inner.get("samples", [])
            if "position" in sample
        ]
        if not xs:
            continue
        windows.append(
            {
                "label": call.get("label"),
                "node_path": args.get("node_path") or inner.get("node_path"),
                "frame_count": inner.get("frame_count"),
                "xs": xs,
            }
        )
    assert windows, "the frozen input_replay carries no position samples"
    return windows


def goal_geometry() -> dict:
    raw = json.load(open(SCENE_TREE, encoding="utf-8"))
    tree = json.loads(raw["calls"][0]["payload"]["content"][0]["text"])["tree"]

    found = {}

    def walk(node):
        if node.get("name") in ("Goal", "Ground"):
            found[node["name"]] = {
                "path": node.get("path"),
                "type": node.get("type"),
            }
        for child in node.get("children", []):
            walk(child)

    walk(tree)
    assert "Goal" in found, "the frozen scene tree must declare the Goal node"
    return found


def main() -> None:
    os.makedirs(OUT, exist_ok=True)

    scene_out = os.path.join(OUT, "scene_tree_smoke_t10.json")
    hud_out = os.path.join(OUT, "hud_labels_smoke_t10.json")
    copy_bytes(SCENE_TREE, scene_out)
    copy_bytes(HUD_LABELS, hud_out)

    windows = position_windows()
    samples = {
        "source": "runs/smoke-t10/iter-1/candidate/.hoh/deterministic/raw/input_replay.json",
        "derivation": DERIVATION,
        "note": (
            "The reduced Player.position x-series of the four input_replay windows, in "
            "call order, exactly as the frozen payload carries them.  Only the surrounding "
            "call envelopes were dropped; every number is the engine's own float."
        ),
        "goal_geometry": goal_geometry(),
        "windows": windows,
    }
    samples_out = os.path.join(OUT, "interaction_position_samples_smoke_t10.json")
    with open(samples_out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(samples, ensure_ascii=False, indent=2))
        handle.write("\n")

    manifest = {
        "batch": "DR-76",
        "captured_by": "TASK-SMOKE-T10 (runs/smoke-t10), the round whose pickup and win were never observed",
        "derivation": DERIVATION,
        "note": (
            "runs/** is read-only evidence.  These fixtures are the frozen input the DR-76 "
            "tests are driven from, so the interaction window is corrected against the "
            "engine's real payload shapes instead of a hand-written idea of them "
            "(the DR-73 A1/O1 defect).  scene_tree_smoke_t10.json and "
            "hud_labels_smoke_t10.json are byte-for-byte copies; the position-sample file is "
            "a reduction whose every number is the frozen float.  tests/dr76_payload_shapes.rs "
            "checks the copies' sha256 and the real shape."
        ),
        "files": [
            {
                "fixture": "scene_tree_smoke_t10.json",
                "source": "runs/smoke-t10/iter-1/candidate/.hoh/deterministic/raw/scene_tree.json",
                "sha256": sha256(scene_out),
                "copy": "byte-for-byte",
            },
            {
                "fixture": "hud_labels_smoke_t10.json",
                "source": "runs/smoke-t10/iter-1/candidate/.hoh/evidence/hud-labels.json",
                "sha256": sha256(hud_out),
                "copy": "byte-for-byte",
            },
            {
                "fixture": "interaction_position_samples_smoke_t10.json",
                "source": "runs/smoke-t10/iter-1/candidate/.hoh/deterministic/raw/input_replay.json",
                "sha256": sha256(samples_out),
                "copy": "reduced (four windows' position samples + goal geometry)",
            },
        ],
    }
    with open(os.path.join(OUT, "MANIFEST.json"), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(manifest, ensure_ascii=False, indent=2))
        handle.write("\n")

    print(f"wrote {len(manifest['files'])} fixtures under {OUT}")
    for entry in manifest["files"]:
        print(f"  {entry['fixture']}  {entry['sha256']}  ({entry['copy']})")


if __name__ == "__main__":
    main()
