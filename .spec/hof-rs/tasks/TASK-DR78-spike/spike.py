"""TASK-DR78 section 1 -- the isolation spike for F-T11-2 ("why did the
interaction window not advance?").

Offline, read-only.  It reads the frozen payloads of `runs/smoke-t11` and the
frozen game sources; it writes nothing under `runs/**` and starts nothing.

The round report's own causal story ("the window made zero
`editor_simulate_input_action` calls") is *tested here and refuted* by the same
round's `input_channel_probe.json`, so the spike deliberately starts from the
readings rather than from that sentence.
"""

import json
import os
import re
import sys

# The output must be valid UTF-8 on disk (the T11A-3 defect was a derived
# artifact that was not), so it is written by Python rather than by a console
# redirect, which mangles non-ASCII bytes on this host.
if len(sys.argv) > 1:
    sys.stdout = open(sys.argv[1], "w", encoding="utf-8", newline="\n")

REPO = r"F:\moonbit-hof-rs"
CAND = os.path.join(REPO, r"runs\smoke-t11\iter-1\candidate")
RAW = os.path.join(CAND, r".hoh\deterministic\raw")
EVID = os.path.join(CAND, r".hoh\evidence")


def load(name):
    with open(os.path.join(RAW, name), encoding="utf-8") as handle:
        return json.load(handle)


def inner(call):
    payload = call.get("payload") or {}
    content = payload.get("content")
    if not isinstance(content, list) or not content:
        return None
    text = content[0].get("text")
    try:
        return json.loads(text)
    except Exception:
        return None


def samples(doc, index):
    parsed = inner(doc["calls"][index])
    return [(s["frame"], s["position"]["x"], s["position"]["y"]) for s in parsed["samples"]]


def rule(title):
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


# ---------------------------------------------------------------------------
rule("A. every game-process input event, in arrival order (press/release bookkeeping)")
# ---------------------------------------------------------------------------
probe = load("input_channel_probe.json")
replay = load("input_replay.json")
inter = load("interaction_evidence.json")

for name, doc in [
    ("input_channel_probe.json", probe),
    ("input_replay.json", replay),
    ("interaction_evidence.json", inter),
]:
    print("--", name)
    for index, call in enumerate(doc["calls"]):
        tool = call.get("tool")
        if tool == "running_game_play_input_recording":
            for event in call["args"]["events"]:
                print("   call %2d  GAME      %-9s pressed=%-5s  label=%s"
                      % (index, event.get("action"), event.get("pressed"), call.get("label")))
        elif tool == "editor_simulate_input_action":
            print("   call %2d  EDITOR    %-9s pressed=%-5s  label=%s   (target=%s)"
                  % (index, call["args"].get("action"), call["args"].get("pressed"),
                     call.get("label"), (inner(call) or {}).get("target")))

# ---------------------------------------------------------------------------
rule("B. the raw series, and the arithmetic of the handover")
# ---------------------------------------------------------------------------
pr = samples(probe, 6)
print("input_channel_probe  move_right frames: n=%d first=%r last=%r"
      % (len(pr), pr[0], pr[-1]))
print("    editor_simulate_input_action calls in that file: %d"
      % sum(1 for c in probe["calls"] if c.get("tool") == "editor_simulate_input_action"))
print("    => a recording-only injection moved the player %.9f px over %d frames"
      % (pr[-1][1] - pr[0][1], len(pr) - 1))

rl = samples(replay, 43)
d_per_frame = (rl[0][1] - rl[-1][1]) / (len(rl) - 1)
print("input_replay  move_left window: n=%d first=%r last=%r" % (len(rl), rl[0], rl[-1]))
print("    per-frame leftward speed = %.9f px (matches 220 px/s at 60 Hz)" % d_per_frame)

rm = samples(replay, 7)
xs = [s[1] for s in rm]
print("input_replay  move_right window: first=%.12f last=%.12f" % (xs[0], xs[-1]))
print("    contains x=225.000045776367 ? %s ; contains x=400 (Coin1) ? %s"
      % (any(abs(x - 225.000045776367) < 0.5 for x in xs), any(380.0 <= x <= 420.0 for x in xs)))

ib = samples(inter, 8)
unique = sorted(set(s[1] for s in ib))
print("interaction   batch1: n=%d unique_x=%d x=%r" % (len(ib), len(unique), unique))

gap = rl[-1][1] - ib[0][1]
print()
print("HANDOVER: last input_replay sample x=%.12f -> first interaction sample x=%.12f"
      % (rl[-1][1], ib[0][1]))
print("    gap = %.12f px = %.6f frames of full-speed leftward travel"
      % (gap, gap / d_per_frame))
print("    (the interaction window's own calls 0..7 ran in that interval; the only")
print("     game-process input event inside it is interaction call 5)")

# ---------------------------------------------------------------------------
rule("C. the discriminator: what the game itself says about the window")
# ---------------------------------------------------------------------------
node_assert = load("node_and_collision_assertions.json")
player = inner(node_assert["calls"][0])
props = player["properties"]
print("step 9 (after the interaction window) running_game_get_node_properties Player:")
for key in ("facing", "velocity", "position", "input_axis"):
    if key in props:
        print("    %-10s = %r" % (key, props[key]))
print()
print("player.gd (frozen candidate):")
src = open(os.path.join(CAND, "scripts", "player.gd"), encoding="utf-8").read()
for line in src.splitlines():
    if "get_axis" in line or "facing" in line or "velocity.x" in line:
        print("    " + line.strip())

# ---------------------------------------------------------------------------
rule("D. the counterexample checks")
# ---------------------------------------------------------------------------
print("D1  'could not move' (the channel is incapable): REFUTED by section B --")
print("    input_channel_probe made 0 editor_simulate_input_action calls and still")
print("    moved the player from %.12f to %.12f." % (pr[0][1], pr[-1][1]))
print()
print("D2  'could not move' (the level blocks the player near x=225): REFUTED --")
print("    the input_replay move_right window's own series runs %.12f -> %.12f and"
      % (xs[0], xs[-1]))
print("    passes straight through x=225 on the way; nothing stops the player there.")
print()
print("D3  'the window sampled a different object': REFUTED --")
print("    both windows sample node_path=%r (the probe's %r)."
      % (inner(inter["calls"][8])["node_path"], inner(probe["calls"][6])["node_path"]))
print()
print("D4  'the observation window never delivered the action': NOT SUPPORTED --")
for index in (5, 11, 17):
    parsed = inner(inter["calls"][index])
    print("    call %2d play_input_recording -> %r" % (index, parsed))

# ---------------------------------------------------------------------------
rule("E. F-T11-3: which frame still has the coin in it")
# ---------------------------------------------------------------------------
from PIL import Image  # noqa: E402

print("yellow pixels per frozen frame (ColorRect 1,0.85,0.1 at 24x24 = 576 px):")
frames = sorted(os.listdir(EVID))
for name in frames:
    image = Image.open(os.path.join(EVID, name)).convert("RGB")
    yellow = sum(1 for p in image.getdata() if p[0] > 240 and 200 < p[1] < 235 and p[2] < 60)
    print("    %-34s %4d yellow pixel(s)" % (name, yellow))

before = Image.open(os.path.join(EVID, "replay-interaction-before.png")).convert("RGB")
after = Image.open(os.path.join(EVID, "replay-interaction-after.png")).convert("RGB")
diff = sum(1 for a, b in zip(before.getdata(), after.getdata()) if a != b)
print()
print("interaction before/after differing pixels: %d of %d" % (diff, before.width * before.height))

# ---------------------------------------------------------------------------
rule("F. where the leak is left, in the source that produced these payloads")
# ---------------------------------------------------------------------------
src = open(os.path.join(REPO, "src", "adapter", "godot.rs"), encoding="utf-8").read()
lines = src.splitlines()
print("input_replay's window loop: the release happens at the START of the **next**")
print("window, so the last window has no successor to clear for it:")
for match in re.finditer(r"for \(label, action, frames, expect_movement\) in \[", src):
    line = src[: match.start()].count("\n") + 1
    for offset in range(line - 1, line + 26):
        print("    godot.rs:%-6d %s" % (offset + 1, lines[offset]))
print()
print("...and nothing releases an action **after** the loop, so `move_left` (the last")
print("window's action, pressed at input_replay call 39) is still held when the next")
print("battery step runs.")
