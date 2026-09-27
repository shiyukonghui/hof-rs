#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-117 step C self-check: prove the two zips really contain the 20 re-exported
playable games, that MANIFEST matches the archive in both directions, that a sample
of extracted files re-hashes to the recorded values, and that the new documentation
(per-game `## 玩法`, per-game playability verdict) is actually inside the zips."""
import hashlib
import io
import json
import os
import re
import sys
import zipfile

ROOT = r"F:\moonbit-hof-rs\godot-mcp"
DIST = os.path.join(ROOT, "dist")
WORK = os.path.join(ROOT, "recovery", "work", "task117")
TMP = os.path.join(WORK, "unzip-test")

GAMES = [
    "asteroids", "bomberman", "breakout", "flappy", "frogger", "game2048",
    "lunarlander", "match3", "minesweeper", "missilecommand", "pacman",
    "platformer", "pong", "puzzlebobble", "rtype", "snake", "sokoban",
    "spaceinvaders", "tetris", "towerdefense",
]

OUT = []


def say(s=""):
    OUT.append(s)
    print(s, flush=True)


def sha256_and_size(path):
    h = hashlib.sha256()
    total = 0
    with open(path, "rb") as fh:
        while True:
            c = fh.read(1 << 20)
            if not c:
                break
            total += len(c)
            h.update(c)
    return h.hexdigest(), total


def parse_manifest(text):
    m = {}
    for line in text.splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 2)
        if len(parts) != 3:
            continue
        digest, size, rel = parts
        m[rel] = (digest, int(size))
    return m


def main():
    results = json.load(io.open(os.path.join(WORK, "package-results.json"), encoding="utf-8-sig"))
    checks = []

    def check(name, ok, detail=""):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})
        say("  [%s] %s%s" % ("OK" if ok else "FAIL", name, (" -- " + detail) if detail else ""))

    all_games_seen = []
    per_zip = {}

    say("=== TASK-117 package self-check ===")
    for rec in results:
        zpath = rec["zip"]
        say("")
        say("--- %s" % os.path.basename(zpath))
        zsha, zsz = sha256_and_size(zpath)
        say("  zip bytes=%d sha256=%s" % (zsz, zsha))
        check("%s: sha256/size match package-results" % rec["name"],
              zsha == rec["zip_sha256"] and zsz == rec["zip_bytes"],
              "recorded %d/%s" % (rec["zip_bytes"], rec["zip_sha256"]))

        with zipfile.ZipFile(zpath) as zf:
            names = zf.namelist()
            tops = sorted(set(n.split("/")[0] for n in names))
            check("%s: single top-level dir" % rec["name"], len(tops) == 1, str(tops))
            top = tops[0]
            readme = zf.read("%s/README.md" % top).decode("utf-8")
            manifest = zf.read("%s/MANIFEST.txt" % top).decode("utf-8")
            runcheck = zf.read("%s/RUN-CHECK.txt" % top).decode("utf-8")
            man = parse_manifest(manifest)
            # payload entries only
            payload = set(n[len(top) + 1:] for n in names if n.startswith(top + "/games/"))
            say("  entries=%d payload=%d manifest=%d" % (len(names), len(payload), len(man)))
            check("%s: in zip not in manifest" % rec["name"], len(payload - set(man)) == 0,
                  str(sorted(payload - set(man))[:5]))
            check("%s: in manifest not in zip" % rec["name"], len(set(man) - payload) == 0,
                  str(sorted(set(man) - payload)[:5]))

            games_here = sorted(set(p.split("/")[1] for p in payload if p.startswith("games/")))
            per_zip[rec["name"]] = games_here
            all_games_seen.extend(games_here)
            check("%s: %d games as declared" % (rec["name"], len(rec["games"])),
                  games_here == sorted(rec["games"]),
                  "zip=%s declared=%s" % (games_here, sorted(rec["games"])))

            # per-game completeness
            bad = []
            for g in games_here:
                need = ["games/%s/%s.exe" % (g, g), "games/%s/%s.pck" % (g, g)]
                for n in need:
                    if n not in payload:
                        bad.append(n)
                data = [p for p in payload if p.startswith("games/%s/data_%s_windows_x86_64/" % (g, g))]
                if len(data) < 100:
                    bad.append("games/%s/data_*: only %d files" % (g, len(data)))
                if "games/%s/data_%s_windows_x86_64/%s.dll" % (g, g, g) not in payload:
                    bad.append("games/%s/.../%s.dll missing" % (g, g))
                if "games/%s/data_%s_windows_x86_64/coreclr.dll" % (g, g) not in payload:
                    bad.append("games/%s/.../coreclr.dll missing" % (g,))
            check("%s: every game has exe+pck+data dir" % rec["name"], not bad, str(bad[:5]))

            # documentation
            missing_play = [g for g in games_here if ("## 玩法 — %s" % g) not in readme]
            check("%s: README has a per-game '## 玩法' section" % rec["name"],
                  not missing_play, "missing: %s" % missing_play)
            check("%s: README documents double-click" % rec["name"], "双击" in readme)
            check("%s: RUN-CHECK has per-game playability verdict" % rec["name"],
                  all(g in runcheck for g in games_here) and "playability" in runcheck)
            verdicts = re.findall(r"^(\w+)\s+(\S+)\s+\S+\s+\S+\s+(playable|not_playable|MISSING)",
                                  runcheck, re.M)
            check("%s: RUN-CHECK rows=%d" % (rec["name"], len(verdicts)),
                  len(verdicts) == len(GAMES))

            # sample re-hash: exe + pck + game dll of 3 games per part
            sample_games = [games_here[0], games_here[len(games_here) // 2], games_here[-1]]
            if os.path.isdir(TMP):
                import shutil
                shutil.rmtree(TMP)
            os.makedirs(TMP)
            okc = 0
            tot = 0
            for g in sample_games:
                for rel in ("games/%s/%s.exe" % (g, g), "games/%s/%s.pck" % (g, g),
                            "games/%s/data_%s_windows_x86_64/%s.dll" % (g, g, g)):
                    if rel not in man:
                        continue
                    tot += 1
                    dest = os.path.join(TMP, rel.replace("/", os.sep))
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    with zf.open("%s/%s" % (top, rel)) as src, open(dest, "wb") as dst:
                        dst.write(src.read())
                    d, sz = sha256_and_size(dest)
                    if d == man[rel][0] and sz == man[rel][1]:
                        okc += 1
            check("%s: extracted samples re-hash == MANIFEST (%d/%d)" % (rec["name"], okc, tot),
                  okc == tot)

    say("")
    say("--- cross-part")
    dupes = [g for g in set(all_games_seen) if all_games_seen.count(g) > 1]
    check("20 distinct games across the parts", len(set(all_games_seen)) == 20,
          "seen=%d" % len(set(all_games_seen)))
    check("no game in two parts", not dupes, str(dupes))
    check("all 20 expected games present", sorted(set(all_games_seen)) == sorted(GAMES),
          "missing=%s extra=%s" % (sorted(set(GAMES) - set(all_games_seen)),
                                   sorted(set(all_games_seen) - set(GAMES))))

    passed = sum(1 for c in checks if c["ok"])
    say("")
    say("SELF-CHECK VERDICT: %s (%d/%d checks)" % (
        "PASS" if passed == len(checks) else "FAIL", passed, len(checks)))
    with io.open(os.path.join(WORK, "selfcheck.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(OUT) + "\n")
    with io.open(os.path.join(WORK, "selfcheck.json"), "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"checks": checks, "passed": passed, "total": len(checks),
                             "verdict": "PASS" if passed == len(checks) else "FAIL"},
                            indent=1, ensure_ascii=False))
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
