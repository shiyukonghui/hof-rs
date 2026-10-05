"""Build the committed evidence corpus for the PRD-coverage batch.

Copies, from the gitignored recordings into `evidence/`, exactly the bytes the
cost and observation conclusions rest on:

  * the four recorded Developer trajectories the cost analysis reads;
  * the round-4 Tester material (result.json, evidence.json, meta.json);
  * the round-4 deterministic battery evidence (`.hoh/deterministic/**`).

Every destination is key-scanned with the repository's own shape rule BEFORE it
is copied; a key-shaped file is refused and reported by path, never copied and
never printed.
"""
import hashlib
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from keyscan import looks_key_shaped, key_shaped_tokens  # noqa: E402

REPO = r"F:/moonbit-hof-rs"
RUNS = os.path.join(REPO, "runs")
WORKSPACE_DETERMINISTIC = r"F:/hof-bevy-r4-run/workspace/.hoh/deterministic"
OUT = os.path.join(REPO, "evidence")

MOVES = []


def plan(source, destination):
    MOVES.append((source, destination))


# ---- the cost corpus -------------------------------------------------------
TRAJECTORIES = [
    ("livecost1-iter-1", "livecost1/iter-1/traj/developer.attempt1.json"),
    ("round4-iter-1", "round4/iter-1/traj/developer.attempt1.json"),
    ("round4-iter-2", "round4/iter-2/traj/developer.attempt1.json"),
    ("round4-iter-3", "round4/iter-3/traj/developer.attempt1.json"),
]
for name, relative in TRAJECTORIES:
    plan(
        os.path.join(RUNS, relative.replace("/", os.sep)),
        os.path.join(OUT, "cost", name + ".developer.attempt1.json"),
    )

# ---- the observation corpus ------------------------------------------------
R4 = os.path.join(RUNS, "round4")
plan(os.path.join(R4, "meta.json"), os.path.join(OUT, "observation/round4/meta.json"))
for iteration in ["iter-1", "iter-2", "iter-3"]:
    for name in ["result.json", "evidence.json"]:
        plan(
            os.path.join(R4, iteration, name),
            os.path.join(OUT, "observation/round4", iteration, name),
        )
for root, _dirs, files in os.walk(WORKSPACE_DETERMINISTIC):
    for name in sorted(files):
        source = os.path.join(root, name)
        relative = os.path.relpath(source, WORKSPACE_DETERMINISTIC).replace("\\", "/")
        plan(source, os.path.join(OUT, "observation/round4/deterministic", relative))

# The round's own evidence directory: the raw MCP->BRP calls behind every E3
# observation, the readings the round recorded, the gate and the launch facts.
ROUND_EVIDENCE = os.path.join(RUNS, "bevy-round4")
for relative in [
    "gate.json",
    "meta.json",
    "launch.json",
    "launch-ledger.jsonl",
    "round-stop.json",
    "build.log",
    "qa/pointer.json",
    "qa/e3-summary.txt",
]:
    plan(
        os.path.join(ROUND_EVIDENCE, relative.replace("/", os.sep)),
        os.path.join(OUT, "observation/round4/round", relative),
    )
for sub in ["calls", "readings"]:
    root = os.path.join(ROUND_EVIDENCE, sub)
    for name in sorted(os.listdir(root)):
        plan(
            os.path.join(root, name),
            os.path.join(OUT, "observation/round4/round", sub, name),
        )


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    applied = []
    refused = []
    total = 0
    for source, destination in MOVES:
        if not os.path.isfile(source):
            print("MISSING SOURCE", source)
            continue
        with open(source, "rb") as handle:
            raw = handle.read()
        text = raw.decode("utf-8", "replace")
        if key_shaped_tokens(text):
            refused.append((source, "key-shaped token"))
            continue
        if looks_key_shaped(text):
            refused.append((source, "key-shaped assignment"))
            continue
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        with open(destination, "wb") as handle:
            handle.write(raw)
        applied.append(
            {
                "source": source.replace("\\", "/"),
                "destination": os.path.relpath(destination, REPO).replace("\\", "/"),
                "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
        )
        total += len(raw)
    print("copied %d file(s), %d byte(s)" % (len(applied), total))
    for entry in refused:
        print("REFUSED (key-shaped): %s (%s)" % entry)
    with open(r"F:/hof-cov-work/evidence_manifest.json", "w", encoding="utf-8") as handle:
        json.dump(applied, handle, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
