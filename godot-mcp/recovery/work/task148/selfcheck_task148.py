#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-148 step C.7: self-check the produced release volume(s).

This is the TASK-148 equivalent of recovery/work/task109/selfcheck.py, extended with the
checks TASK-148 asks for explicitly: 款数 / 文件数 / 总字节数 against the manifest, and the
per-game exe/pck digests against the export records.

Checks, per volume:
  [0] zip sha256 + byte size match package-results.json
  [1] exactly one top-level folder, named after the volume
  [2] MANIFEST parses; entry count / total bytes match its own header
  [3] MANIFEST vs zip completeness in BOTH directions
  [4] spot-check: extract >= 5 files and re-hash them against MANIFEST
  [5] README.md / RUN-CHECK.txt present and carrying the required summary text
And across volumes:
  [6] exactly the 20 expected games, none missing, none extra, none duplicated
  [7] every game has .exe + .pck + data_<game>_windows_x86_64/ with the game's own .dll
  [8] every game's exe/pck sha256 matches the export record (recovery/work/task148)
No shell redirection: this script only prints and writes its own report file.
"""
import hashlib
import json
import os
import sys
import zipfile

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = r"F:\moonbit-hof-rs\godot-mcp"
DIST = os.path.join(ROOT, "dist")
WORK = os.path.join(ROOT, "recovery", "work", "task148")

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
    """-> (entries dict path->(digest,size,part), declared file count, declared bytes,
           declared part)."""
    entries = {}
    count = None
    total = None
    part = None
    for line in text.splitlines():
        line = line.rstrip("\n")
        if line.startswith("# 文件数:"):
            body = line.split(":", 1)[1].strip()
            count = int(body.split("总字节:")[0].strip().replace("文件数:", "").strip())
            total = int(body.split("总字节:")[1].strip())
        elif line.startswith("# 分卷:"):
            part = line.split(":", 1)[1].strip()
        elif not line.strip() or line.startswith("#"):
            continue
        else:
            parts = line.split("  ")
            if len(parts) != 4:
                continue
            digest, size, p, path = parts
            entries[path] = (digest, int(size), p)
    return entries, count, total, part


def main():
    with open(os.path.join(WORK, "package-results.json"), "r", encoding="utf-8") as fh:
        archives = json.load(fh)
    with open(os.path.join(WORK, "export-results.json"), "r", encoding="utf-8-sig") as fh:
        export = {r["game"]: r for r in json.load(fh)}
    with open(os.path.join(WORK, "smoke-results.json"), "r", encoding="utf-8-sig") as fh:
        smoke = json.load(fh)

    out = []
    failures = []
    all_games = []
    total_files = 0
    total_zip_bytes = 0
    total_payload_bytes = 0

    for a in archives:
        zpath = a["zip"]
        pkgname = a["pkgname"]
        out.append("=" * 78)
        out.append("VOLUME %d/%d  %s" % (a["part"], len(archives), a["name"]))
        out.append("=" * 78)

        zsha = sha_file(zpath)
        zsz = os.path.getsize(zpath)
        total_zip_bytes += zsz
        ok = (zsha == a["zip_sha256"] and zsz == a["zip_bytes"])
        out.append("zip path   : %s" % zpath)
        out.append("zip bytes  : %d  (%.3f GB)" % (zsz, zsz / 1073741824.0))
        out.append("zip sha256 : %s" % zsha)
        out.append("matches package-results.json : %s" % ("YES" if ok else "NO"))
        if not ok:
            failures.append("volume %d: zip sha/size mismatch vs package-results.json" % a["part"])

        # sidecars
        for key in ("manifest_sidecar", "sha256_sidecar"):
            sp = a[key]
            out.append("%-16s : %s (%s)" % (key, sp, "present" if os.path.exists(sp) else "MISSING"))
            if not os.path.exists(sp):
                failures.append("volume %d: %s missing" % (a["part"], key))

        with zipfile.ZipFile(zpath, "r") as zf:
            names = zf.namelist()
            files = [n for n in names if not n.endswith("/")]
            total_files += len(files)
            out.append("zip entries (files): %d" % len(files))

            tops = sorted({n.split("/")[0] for n in names})
            out.append("top-level folders  : %s" % tops)
            if tops != [pkgname]:
                failures.append("volume %d: unexpected top-level folders %s" % (a["part"], tops))

            mtext = zf.read("%s/MANIFEST.txt" % pkgname).decode("utf-8")
            man, mcount, mbytes, mpart = parse_manifest(mtext)
            real_bytes = sum(v[1] for v in man.values())
            out.append("MANIFEST header    : 文件数=%s 总字节=%s 分卷=%s" % (mcount, mbytes, mpart))
            out.append("MANIFEST parsed    : entries=%d bytes=%d" % (len(man), real_bytes))
            total_payload_bytes += real_bytes
            if mcount != len(man) or mbytes != real_bytes:
                failures.append("volume %d: manifest header disagrees with its own lines" % a["part"])
            if mpart != pkgname:
                failures.append("volume %d: manifest header names the wrong volume" % a["part"])

            zip_rel = {n[len(pkgname) + 1:] for n in files}
            extras = {"MANIFEST.txt", "README.md", "RUN-CHECK.txt"}
            payload_zip = {p for p in zip_rel if p not in extras}
            payload_zip.discard("MANIFEST.txt")
            only_zip = sorted(payload_zip - set(man.keys()))
            only_man = sorted(set(man.keys()) - payload_zip)
            out.append("in zip not in manifest : %d %s" % (len(only_zip), only_zip[:5]))
            out.append("in manifest not in zip : %d %s" % (len(only_man), only_man[:5]))
            if only_zip or only_man:
                failures.append("volume %d: manifest/zip mismatch" % a["part"])

            part_games = sorted({p.split("/")[1] for p in payload_zip if p.startswith("games/")})
            all_games.extend(part_games)
            out.append("games in volume    : %d %s" % (len(part_games), part_games))
            if part_games != sorted(a["games"]):
                failures.append("volume %d: games differ from plan" % a["part"])

            # [7] per game structure + [8] digest cross-check against the export records
            out.append("-" * 78)
            out.append("per-game structure and digest cross-check (vs export-results.json)")
            out.append("-" * 78)
            out.append("%-15s %-10s %-10s %-6s %-6s %s" %
                       ("game", "exe_bytes", "pck_bytes", "data_n", "exe_sha", "verdict"))
            for g in part_games:
                need = ["games/%s/%s.exe" % (g, g), "games/%s/%s.pck" % (g, g)]
                missing = [n for n in need if n not in man]
                prefix = "games/%s/data_%s_windows_x86_64/" % (g, g)
                data_n = [p for p in man if p.startswith(prefix)]
                has_dll = any(p.endswith("/%s.dll" % g) for p in data_n)
                verdict = "OK"
                if missing:
                    verdict = "MISSING " + ",".join(missing)
                    failures.append("volume %d: %s missing payload file(s) %s" % (a["part"], g, missing))
                if len(data_n) < 100:
                    verdict = "data files only %d" % len(data_n)
                    failures.append("volume %d: %s has only %d data files" % (a["part"], g, len(data_n)))
                if not has_dll:
                    verdict = "no %s.dll" % g
                    failures.append("volume %d: %s data dir has no %s.dll" % (a["part"], g, g))
                exe_key = "games/%s/%s.exe" % (g, g)
                pck_key = "games/%s/%s.pck" % (g, g)
                exe_bytes = man.get(exe_key, ("", 0, ""))[1]
                pck_bytes = man.get(pck_key, ("", 0, ""))[1]
                e = export.get(g)
                sha_ok = "n/a"
                if e:
                    same_exe = (man.get(exe_key, ("", 0, ""))[0] == e["exe_sha256"] and
                                exe_bytes == e["exe_bytes"])
                    same_pck = (man.get(pck_key, ("", 0, ""))[0] == e["pck_sha256"] and
                                pck_bytes == e["pck_bytes"])
                    sha_ok = "OK" if (same_exe and same_pck) else "MISMATCH"
                    if sha_ok == "MISMATCH":
                        failures.append("volume %d: %s exe/pck digest differs from the export record"
                                        % (a["part"], g))
                    if verdict == "OK":
                        verdict = sha_ok
                out.append("%-15s %-10d %-10d %-6d %-6s %s" %
                           (g, exe_bytes, pck_bytes, len(data_n), sha_ok, verdict))

            # [4] spot check
            out.append("-" * 78)
            out.append("spot-check: extract and re-hash")
            out.append("-" * 78)
            cands = []
            for g in part_games[:2]:
                cands.append("games/%s/%s.exe" % (g, g))
                cands.append("games/%s/%s.pck" % (g, g))
                cands.append("games/%s/data_%s_windows_x86_64/%s.dll" % (g, g, g))
            if len(part_games) > 2:
                g = part_games[-1]
                cands.append("games/%s/%s.exe" % (g, g))
            cands += ["MANIFEST.txt", "README.md", "RUN-CHECK.txt"]
            checked = 0
            for rel in cands:
                data = zf.read("%s/%s" % (pkgname, rel))
                got = sha_bytes(data)
                if rel in man:
                    exp_d, exp_s, _ = man[rel]
                    good = (got == exp_d and len(data) == exp_s)
                    out.append("%-4s %-70s bytes=%d" % ("OK" if good else "BAD", rel, len(data)))
                    if not good:
                        failures.append("volume %d: spot-check failed for %s" % (a["part"], rel))
                else:
                    out.append("%-4s %-70s bytes=%d (not in MANIFEST by design)"
                               % ("--", rel, len(data)))
                checked += 1
            out.append("spot-checked files : %d" % checked)
            if checked < 5:
                failures.append("volume %d: only %d spot-checked files" % (a["part"], checked))

            rd = zf.read("%s/README.md" % pkgname).decode("utf-8")
            rc = zf.read("%s/RUN-CHECK.txt" % pkgname).decode("utf-8")
            out.append("README.md bytes    : %d" % len(rd.encode("utf-8")))
            out.append("RUN-CHECK.txt bytes: %d" % len(rc.encode("utf-8")))
            if "双击" not in rd:
                failures.append("volume %d: README.md missing the double-click section" % a["part"])
            if ("冒烟汇总" not in rc) or ("20 / 20" not in rc):
                failures.append("volume %d: RUN-CHECK.txt lacks the 20/20 smoke summary" % a["part"])
        out.append("")

    out.append("=" * 78)
    out.append("CROSS-VOLUME VERDICT")
    out.append("=" * 78)
    uniq = sorted(set(all_games))
    dupes = sorted({g for g in all_games if all_games.count(g) > 1})
    missing = [g for g in EXPECT if g not in uniq]
    extra = [g for g in uniq if g not in EXPECT]
    out.append("games found across volumes: %d" % len(uniq))
    out.append("expected                  : %d" % len(EXPECT))
    out.append("missing : %s" % (missing or "none"))
    out.append("extra   : %s" % (extra or "none"))
    out.append("dupes   : %s" % (dupes or "none"))
    if missing:
        failures.append("missing games: %s" % missing)
    if extra:
        failures.append("unexpected games: %s" % extra)
    if dupes:
        failures.append("games in more than one volume: %s" % dupes)
    if len(uniq) != 20:
        failures.append("expected exactly 20 games, found %d" % len(uniq))

    out.append("")
    out.append("total payload files across volumes : %d" % total_files)
    out.append("total payload bytes across volumes : %d (%.3f GB)" % (total_payload_bytes, total_payload_bytes / 1073741824.0))
    out.append("total zip bytes across volumes     : %d (%.3f GB)" % (total_zip_bytes, total_zip_bytes / 1073741824.0))

    # export-record totals must agree with the packaged payload
    exp_files = sum(1 + 1 + e["data_files"] for e in export.values())
    exp_bytes = sum(e["exe_bytes"] + e["pck_bytes"] + e["data_bytes"] for e in export.values())
    out.append("export records: files=%d bytes=%d (%.3f GB)" % (exp_files, exp_bytes, exp_bytes / 1073741824.0))
    # +3 per volume for README/MANIFEST/RUN-CHECK
    expect_zip_files = exp_files + 3 * len(archives)
    out.append("expected zip file entries         : %d" % expect_zip_files)
    if total_files != expect_zip_files:
        failures.append("packaged file count %d != expected %d" % (total_files, expect_zip_files))
    if total_payload_bytes != exp_bytes:
        failures.append("packaged payload bytes %d != export record bytes %d"
                        % (total_payload_bytes, exp_bytes))

    smoke_pass = sum(1 for r in smoke["results"] if r.get("pass"))
    out.append("")
    out.append("smoke test: %d / 20 passed (alive >= 3 s and main window)" % smoke_pass)
    out.append("orphan processes at end: game=[%s] godot=[%s]" % (
        smoke["orphans"]["orphan_game_processes"], smoke["orphans"]["orphan_godot_processes"]))

    out.append("")
    if failures:
        out.append("SELF-CHECK VERDICT: FAIL")
        for f in failures:
            out.append("  - %s" % f)
    else:
        out.append("SELF-CHECK VERDICT: PASS")
        out.append("  20/20 games present, none missing, none duplicated, none extra;")
        out.append("  MANIFEST matches the zip in both directions and its own header;")
        out.append("  every game's exe/pck digest matches the export record;")
        out.append("  extracted spot-check files re-hash to the manifest values.")
    out.append("")
    text = "\n".join(out)
    print(text)
    with open(os.path.join(WORK, "selfcheck.txt"), "w", encoding="utf-8") as fh:
        fh.write(text)
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
