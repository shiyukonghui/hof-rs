# -*- coding: utf-8 -*-
"""TASK-138 §1.C.3: the RUN ARTIFACT INDEX.

Why this exists
---------------
`runs/**` is ignored by `.gitignore` (line 43), so every number a report quotes from a run
exists only on the machine that produced it.  ACCEPTANCE-TASK-137 pointed at the consequence
(its risk R4) and TASK-138 §1.C.3 asks for the fix: an index of the KEY artefacts -- path +
sha256 + size + the command that produced it -- that IS committed, so a later reader can
check that the file they are being shown is the file the conclusion was drawn from.

What it indexes
---------------
Per run directory (`<prefix>/<game>/<backend>/`):
    player.json      the run's summary / verdict
    steps.jsonl      the per-step records
    frames.json      the frame metadata list
    demo.png         the per-step demo sheet
    filmstrip.png    every frame in one image
    gate.json        when the run directory is a gate output
and, per run directory, one entry per captured frame under `frames/` and one per state
under `states/` (sizes + sha256 + the fact that they exist).

The generating command is taken from the sweep result files this batch wrote
(`t138_results_*.json`, each entry carries its `cmd`), and from the TASK-136 ledger
(`t136_commands.jsonl`) as a fallback: the ledger is the record of what was really run.

Iron rule 1: no shell redirection; this tool writes with Python handles.

Usage (cmd, through the TASK-136 ledger wrapper):
    D:\\Anaconda\\python.exe tools\\playtest_artifact_index.py --roots t138-scripted t138-jev-v3
"""
from __future__ import print_function

import hashlib
import io
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
# this file lives in `godot-mcp/tools/`, so the module root is one level up (TASK-138 §1.C.3
# put it here, out of `runs/model-player/_scripts/`, so that the tool itself is COMMITTED --
# `runs/**` is ignored)
ROOT = os.path.abspath(os.path.join(HERE, ".."))
RUNS = os.path.join(ROOT, "runs", "model-player")
OUT_JSON = os.path.join(RUNS, "_index", "ARTIFACTS-TASK-138.json")
OUT_MD = os.path.join(RUNS, "_index", "ARTIFACTS-TASK-138.md")
LEDGER = os.path.join(RUNS, "_scripts", "t136_commands.jsonl")

KEY_FILES = ("player.json", "steps.jsonl", "frames.json", "demo.png", "filmstrip.png",
             "gate.json", "summary.txt", "session.json", "filmstrip.json")


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(p):
    return os.path.relpath(p, ROOT).replace("\\", "/")


def load_commands():
    """Every command this series recorded, newest last, plus the sweep cmd fields."""
    cmds = []
    for name in ("t138_results_scripted.json", "t138_results_model.json"):
        p = os.path.join(HERE, name)
        if not os.path.isfile(p):
            continue
        for e in json.load(io.open(p, encoding="utf-8")):
            cmds.append({"game": e.get("game"), "argv": e.get("cmd"),
                         "source": "%s (sweep driver)" % name,
                         "stdout": e.get("stdout")})
    if os.path.isfile(LEDGER):
        for line in io.open(LEDGER, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except ValueError:
                continue
            cmds.append({"argv": e.get("argv"), "ts": e.get("ts"), "cwd": e.get("cwd"),
                         "source": "t136_commands.jsonl"})
    return cmds


def commands_for(cmds, game, prefix):
    """The recorded commands that mention this game and this run prefix."""
    out = []
    for c in cmds:
        argv = c.get("argv") or []
        joined = " ".join(str(a) for a in argv)
        if game in joined and (prefix in joined or c.get("source", "").startswith("t138_")):
            out.append({"argv": argv, "ts": c.get("ts"), "source": c.get("source"),
                        "stdout": c.get("stdout"), "cwd": c.get("cwd")})
    # de-duplicate identical argv sets
    seen, uniq = set(), []
    for c in out:
        k = json.dumps(c["argv"], ensure_ascii=False)
        if k in seen:
            continue
        seen.add(k)
        uniq.append(c)
    return uniq


def run_dirs(roots):
    for prefix in roots:
        base = os.path.join(RUNS, prefix)
        if not os.path.isdir(base):
            continue
        for game in sorted(os.listdir(base)):
            gp = os.path.join(base, game)
            if not os.path.isdir(gp):
                continue
            for backend in sorted(os.listdir(gp)):
                bp = os.path.join(gp, backend)
                if os.path.isdir(bp) and os.path.isfile(os.path.join(bp, "player.json")):
                    yield prefix, game, backend, bp


def index_run(prefix, game, backend, d, cmds, full=False):
    entry = {"prefix": prefix, "game": game, "backend": backend, "dir": rel(d),
             "commands": commands_for(cmds, game, prefix), "files": [], "counts": {},
             "subtree_digest": {}}
    for fname in os.listdir(d):
        p = os.path.join(d, fname)
        if not os.path.isfile(p):
            continue
        if fname not in KEY_FILES and not fname.endswith((".jsonl", ".json", ".md", ".txt")):
            continue
        entry["files"].append({"name": fname, "path": rel(p), "bytes": os.path.getsize(p),
                               "sha256": sha256_file(p)})
    entry["files"].sort(key=lambda f: f["name"])
    for sub in ("frames", "states", "calls"):
        sp = os.path.join(d, sub)
        if not os.path.isdir(sp):
            continue
        rows = []
        for name in sorted(os.listdir(sp)):
            fp = os.path.join(sp, name)
            if not os.path.isfile(fp):
                continue
            rows.append({"path": rel(fp), "bytes": os.path.getsize(fp),
                         "sha256": sha256_file(fp)})
        entry["counts"][sub] = len(rows)
        if full:
            entry["files"].extend(rows)
        else:
            # a per-directory DIGEST instead of thousands of per-file rows: the digest is
            # sha256 over "<relpath> <sha256> <bytes>\n" for every file in the directory, so
            # adding, removing or changing any single file changes it.  A reader who needs a
            # single file re-runs this tool with --full.
            h = hashlib.sha256()
            for r in rows:
                h.update(("%s %s %d\n" % (r["path"], r["sha256"], r["bytes"])).encode("utf-8"))
            entry["subtree_digest"][sub] = {
                "files": len(rows),
                "bytes": sum(r["bytes"] for r in rows),
                "digest": h.hexdigest(),
                "digest_what": ("sha256 over `\"<repo-relative path> <file sha256> <bytes>\\n\"` "
                                "for every file under this directory, in sorted order"),
            }
    pj = os.path.join(d, "player.json")
    if os.path.isfile(pj):
        s = json.load(io.open(pj, encoding="utf-8"))
        entry["verdict"] = s.get("verdict")
        entry["counts_as_pass"] = s.get("counts_as_pass")
        entry["strict_verdict"] = s.get("strict_verdict")
        entry["baseline_verdict"] = s.get("baseline_verdict")
        entry["game_side_verdict"] = s.get("game_side_verdict")
        entry["injected_steps"] = s.get("injected_steps")
        entry["changed_steps_of_accepted"] = s.get("changed_steps_of_accepted")
        entry["accepted_and_changed_rate"] = s.get("accepted_and_changed_rate")
        fa = s.get("frame_alignment") or {}
        entry["frame_alignment"] = {"reading": fa.get("reading"),
                                    "matched_step_count": fa.get("matched_step_count"),
                                    "step_count": fa.get("step_count"),
                                    "all_matched": fa.get("all_matched")}
        entry["ack_missing_count"] = (s.get("ack_missing") or {}).get("count")
    return entry


def main(argv):
    roots = ["t138-scripted", "t138-jev-v3"]
    if "--roots" in argv:
        roots = argv[argv.index("--roots") + 1:]
        roots = [r for r in roots if not r.startswith("-")]
    out_json = OUT_JSON
    out_md = OUT_MD
    if "--out-json" in argv:
        out_json = argv[argv.index("--out-json") + 1]
    if "--out-md" in argv:
        out_md = argv[argv.index("--out-md") + 1]
    cmds = load_commands()
    full = "--full" in argv
    entries = []
    for prefix, game, backend, d in run_dirs(roots):
        entries.append(index_run(prefix, game, backend, d, cmds, full=full))
    doc = {
        "task": "TASK-138",
        "when": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "why": ("TASK-138 §1.C.3: `runs/**` is ignored by `.gitignore` (line 43), so this "
                "index is the committed record of WHICH file each conclusion rests on: path + "
                "sha256 + size + the command that produced it.  Verify with "
                "`certutil -hashfile <path> SHA256` or this same script."),
        "repo_root": ROOT,
        "ignored_rule": "godot-mcp/runs/  (.gitignore line 43) and runs/ (line 12)",
        "roots": roots,
        "mode": ("full (every frame/state/call file listed)" if full
                 else "compact (key files per run + one subtree digest per frames/states/calls)"),
        "run_count": len(entries),
        "file_count": sum(len(e["files"]) for e in entries),
        "how_to_recheck": (
            "D:\\Anaconda\\python.exe runs\\model-player\\_scripts\\t138_artifact_index.py "
            "--roots %s" % " ".join(roots)),
        "runs": entries,
    }
    if not os.path.isdir(os.path.dirname(out_json)):
        os.makedirs(os.path.dirname(out_json))
    with io.open(out_json, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(doc, ensure_ascii=False, indent=1))
    lines = ["# ARTIFACTS-TASK-138 — 关键产物清单（路径 + sha256 + 大小 + 生成命令）", "",
             "> 为什么入库：`runs/**` 被 `.gitignore` 忽略（第 12 行 `runs/`、第 43 行",
             "> `godot-mcp/runs/`），报告引用的每个 run 产物只存在于本机。本文件把**关键产物**",
             "> 的 sha256 / 大小 / 生成命令**提交进仓**，使结论在 `runs/**` 不入库的前提下仍可事后核验。",
             ">",
             "> 复算：`certutil -hashfile <path> SHA256`，或重跑本清单的生成器",
             "> （命令见本文件表头的 §复算）。", "",
             "* 生成时刻：`%s`" % doc["when"],
             "* run 目录数：**%d**；索引文件数：**%d**" % (doc["run_count"], doc["file_count"]),
             "* 复算命令：`%s`" % doc["how_to_recheck"], ""]
    for e in entries:
        lines.append("## %s / %s / %s" % (e["prefix"], e["game"], e["backend"]))
        lines.append("")
        lines.append("* 目录：`%s`" % e["dir"])
        lines.append("* verdict：`%s`（counts_as_pass=%s，strict=%s，baseline=%s，game_side=%s）"
                     % (e.get("verdict"), e.get("counts_as_pass"), e.get("strict_verdict"),
                        e.get("baseline_verdict"), e.get("game_side_verdict")))
        lines.append("* 注入/接受后变化/rate：%s / %s / %s"
                     % (e.get("injected_steps"), e.get("changed_steps_of_accepted"),
                        e.get("accepted_and_changed_rate")))
        fa = e.get("frame_alignment") or {}
        lines.append("* 两窗对齐：%s（matched %s/%s，all_matched=%s）"
                     % (fa.get("reading"), fa.get("matched_step_count"),
                        fa.get("step_count"), fa.get("all_matched")))
        lines.append("* ack 缺失步数：%s" % e.get("ack_missing_count"))
        lines.append("* 生成命令：")
        for c in e["commands"]:
            lines.append("  * `%s`%s" % (" ".join(str(a) for a in (c.get("argv") or [])),
                                         ("  <- %s" % c.get("source")) if c.get("source")
                                         else ""))
        lines.append("")
        lines.append("| 文件 | 大小(B) | sha256 |")
        lines.append("|---|---|---|")
        for f in e["files"]:
            lines.append("| `%s` | %d | `%s` |" % (f["path"], f["bytes"], f["sha256"]))
        for sub, dig in sorted((e.get("subtree_digest") or {}).items()):
            lines.append("| `%s/**`（%d 个文件，%d B）| — | `%s` |"
                         % (sub, dig["files"], dig["bytes"], dig["digest"]))
        lines.append("")
    with io.open(out_md, "w", encoding="utf-8") as fh:
        fh.write(u"\n".join(lines))
    print("indexed %d run(s), %d file(s)" % (doc["run_count"], doc["file_count"]))
    print("wrote %s" % out_json)
    print("wrote %s" % out_md)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
