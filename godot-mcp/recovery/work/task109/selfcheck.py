#!/usr/bin/env python3
# TASK-109 step 5b: self-check the produced zip parts.
#
# Checks, per part:
#   [0] MANIFEST.txt parses; its entry count matches the zip's file entries
#   [1] every zip entry lives under exactly one top-level folder
#   [2] manifest vs zip completeness (both directions)
#   [3] spot-check: extract >=5 files and re-hash them against MANIFEST
#   [4] zip sha256 recorded
# And across all parts:
#   [5] exactly the 20 expected games, none missing, none extra
#   [6] every game has .exe + .pck + data_<game>_windows_x86_64/
import hashlib
import io
import json
import os
import sys
import tempfile
import zipfile

ROOT = r"F:\moonbit-hof-rs\godot-mcp"
DIST = os.path.join(ROOT, "dist")
WORK = os.path.join(ROOT, "recovery", "work", "task109")

EXPECT = [
    "asteroids", "bomberman", "breakout", "flappy", "frogger", "game2048",
    "lunarlander", "match3", "minesweeper", "missilecommand", "pacman",
    "platformer", "pong", "puzzlebobble", "rtype", "snake", "sokoban",
    "spaceinvaders", "tetris", "towerdefense",
]


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_manifest(text):
    entries = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("  ")
        if len(parts) != 3:
            continue
        digest, size, path = parts
        entries[path] = (digest, int(size))
    return entries


def main():
    with open(os.path.join(WORK, "package-results.json"), "r", encoding="utf-8") as fh:
        archives = json.load(fh)

    out = []
    all_games = []
    failures = []
    total_files = 0
    total_zip_bytes = 0

    for a in archives:
        zpath = a["zip"]
        pkgname = a["name"][:-4]
        out.append("=" * 78)
        out.append("PART %d  %s" % (a["part"], a["name"]))
        out.append("=" * 78)

        # zip sha256
        zsha = sha_file(zpath)
        zsz = os.path.getsize(zpath)
        total_zip_bytes += zsz
        out.append("zip bytes  : %d" % zsz)
        out.append("zip sha256 : %s" % zsha)
        ok = zsha == a["zip_sha256"] and zsz == a["zip_bytes"]
        out.append("matches package-results.json : %s" % ("YES" if ok else "NO"))
        if not ok:
            failures.append("part %d: zip sha/size mismatch vs package-results.json" % a["part"])

        with zipfile.ZipFile(zpath, "r") as zf:
            names = zf.namelist()
            files = [n for n in names if not n.endswith("/")]
            total_files += len(files)
            out.append("zip entries (files): %d" % len(files))

            # [1] single top-level folder
            tops = sorted({n.split("/")[0] for n in names})
            out.append("top-level folders  : %s" % tops)
            if tops != [pkgname]:
                failures.append("part %d: unexpected top-level folders %s" % (a["part"], tops))

            # [0] manifest
            mtext = zf.read("%s/MANIFEST.txt" % pkgname).decode("utf-8")
            man = parse_manifest(mtext)
            out.append("MANIFEST entries   : %d" % len(man))

            zip_rel = {n[len(pkgname) + 1:] for n in files}
            man_keys = set(man.keys())
            payload_zip = {p for p in zip_rel if p not in ("MANIFEST.txt", "README.md", "RUN-CHECK.txt")}
            only_zip = sorted(payload_zip - man_keys)
            only_man = sorted(man_keys - payload_zip)
            out.append("in zip not in manifest : %d %s" % (len(only_zip), only_zip[:5]))
            out.append("in manifest not in zip : %d %s" % (len(only_man), only_man[:5]))
            if only_zip or only_man:
                failures.append("part %d: manifest/zip mismatch" % a["part"])

            # [2] games present in this part
            part_games = sorted({p.split("/")[1] for p in payload_zip if p.startswith("games/")})
            all_games.extend(part_games)
            out.append("games in part      : %d %s" % (len(part_games), part_games))
            if part_games != sorted(a["games"]):
                failures.append("part %d: games differ from plan" % a["part"])

            # [6] each game has exe + pck + data dir
            for g in part_games:
                need = [
                    "games/%s/%s.exe" % (g, g),
                    "games/%s/%s.pck" % (g, g),
                ]
                for n in need:
                    if n not in man_keys:
                        failures.append("part %d: %s missing" % (a["part"], n))
                prefix = "games/%s/data_%s_windows_x86_64/" % (g, g)
                data_n = [p for p in man_keys if p.startswith(prefix)]
                if len(data_n) < 100:
                    failures.append("part %d: %s has only %d data files" % (a["part"], g, len(data_n)))
                if not any(p.endswith("%s.dll" % g) for p in data_n):
                    failures.append("part %d: %s data dir has no %s.dll" % (a["part"], g, g))

            # [3] spot-check extraction + re-hash
            out.append("-" * 78)
            out.append("spot-check: extract and re-hash")
            out.append("-" * 78)
            cands = []
            for g in part_games[:2]:
                cands.append("games/%s/%s.exe" % (g, g))
                cands.append("games/%s/%s.pck" % (g, g))
                cands.append("games/%s/data_%s_windows_x86_64/%s.dll" % (g, g, g))
            cands.append("MANIFEST.txt")
            cands.append("README.md")
            cands.append("RUN-CHECK.txt")
            checked = 0
            for rel in cands:
                if rel not in man:
                    continue
                data = zf.read("%s/%s" % (pkgname, rel))
                got = sha_bytes(data)
                exp_d, exp_s = man[rel]
                good = (got == exp_d and len(data) == exp_s)
                out.append("%-4s %s" % ("OK" if good else "BAD", rel))
                out.append("       extracted bytes=%d sha256=%s" % (len(data), got))
                if not good:
                    failures.append("part %d: spot-check failed for %s" % (a["part"], rel))
                checked += 1
            out.append("spot-checked files : %d" % checked)
            if checked < 5:
                failures.append("part %d: only %d spot-checked files" % (a["part"], checked))

            # README / RUN-CHECK non-empty and Chinese README
            rd = zf.read("%s/README.md" % pkgname).decode("utf-8")
            rc = zf.read("%s/RUN-CHECK.txt" % pkgname).decode("utf-8")
            out.append("README.md bytes    : %d" % len(rd.encode("utf-8")))
            out.append("RUN-CHECK.txt bytes: %d" % len(rc.encode("utf-8")))
            if "双击" not in rd:
                failures.append("part %d: README.md missing the double-click section" % a["part"])
            if "ROLE" in rc:
                pass
            if ("PASS" not in rc) or ("20 / 20" not in rc):
                failures.append("part %d: RUN-CHECK.txt lacks the per-game PASS summary" % a["part"])
        out.append("")

    out.append("=" * 78)
    out.append("CROSS-PART VERDICT")
    out.append("=" * 78)
    uniq = sorted(set(all_games))
    out.append("games found across parts: %d" % len(uniq))
    out.append("expected                : %d" % len(EXPECT))
    missing = [g for g in EXPECT if g not in uniq]
    extra = [g for g in uniq if g not in EXPECT]
    dupes = sorted({g for g in all_games if all_games.count(g) > 1})
    out.append("missing : %s" % (missing or "none"))
    out.append("extra   : %s" % (extra or "none"))
    out.append("dupes   : %s" % (dupes or "none"))
    if missing:
        failures.append("missing games: %s" % missing)
    if extra:
        failures.append("unexpected games: %s" % extra)
    if dupes:
        failures.append("games in more than one part: %s" % dupes)
    if len(uniq) != 20:
        failures.append("expected exactly 20 games, found %d" % len(uniq))

    out.append("total payload files across parts: %d" % total_files)
    out.append("total zip bytes                 : %d (%.2f GB)" % (total_zip_bytes, total_zip_bytes / 1073741824.0))
    out.append("")
    if failures:
        out.append("SELF-CHECK VERDICT: FAIL")
        for f in failures:
            out.append("  - %s" % f)
    else:
        out.append("SELF-CHECK VERDICT: PASS")
        out.append("  20/20 games present, none missing, none duplicated;")
        out.append("  MANIFEST matches the zip in both directions;")
        out.append("  extracted spot-check files re-hash to the manifest values.")
    out.append("")
    text = "\n".join(out)
    print(text)
    with open(os.path.join(WORK, "selfcheck.txt"), "w", encoding="utf-8") as fh:
        fh.write(text)
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
