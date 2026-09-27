#!/usr/bin/env python3
# TASK-109 step 5c: extract ONE game straight out of a shipped zip part and run it.
# This proves the packaged artifact itself (not just the dist/ tree) is runnable.
import os
import subprocess
import sys
import zipfile

ROOT = r"F:\moonbit-hof-rs\godot-mcp"
DIST = os.path.join(ROOT, "dist")
WORK = os.path.join(ROOT, "recovery", "work", "task109")
ZIP = os.path.join(DIST, "godot-mcp-20games-exe-20260927-0927-part2of2.zip")
GAME = "pong"
PKG = "godot-mcp-20games-exe-20260927-0927-part2of2"
DEST = os.path.join(WORK, "unzip-test")

if os.path.isdir(DEST):
    import shutil
    shutil.rmtree(DEST)
os.makedirs(DEST, exist_ok=True)

prefix = "%s/games/%s/" % (PKG, GAME)
extracted = []
with zipfile.ZipFile(ZIP) as zf:
    for n in zf.namelist():
        if n.startswith(prefix) and not n.endswith("/"):
            zf.extract(n, DEST)
            extracted.append(n)

game_dir = os.path.join(DEST, PKG, "games", GAME)
print("extracted %d files for %s into %s" % (len(extracted), GAME, game_dir))
print("files:")
for n in sorted(extracted):
    print("   " + n.split("/games/%s/" % GAME)[1])

exe = os.path.join(game_dir, GAME + ".exe")
print("\nexe exists: %s" % os.path.isfile(exe))

psi = subprocess.run(
    [exe, "--headless", "--quit-after", "120"],
    cwd=game_dir,
    capture_output=True,
    timeout=180,
)
out = psi.stdout.decode("utf-8", "replace")
err = psi.stderr.decode("utf-8", "replace")
print("\n--- exit code: %d" % psi.returncode)
print("--- stdout ---")
print(out)
print("--- stderr (%d bytes) ---" % len(err))
print(err)

ready = any("READY" in ln for ln in out.splitlines())
listen_false = "role=game configured_port=0 source=default listen=false" in out
print("\nREADY line present        : %s" % ready)
print("listen=false line present : %s" % listen_false)
ok = (psi.returncode == 0) and ready and listen_false
print("\nZIP-EXTRACT-RUN VERDICT: %s" % ("PASS" if ok else "FAIL"))

# keep the evidence even after the (large) extraction is deleted
log_path = os.path.join(WORK, "zip-extract-run.txt")
with open(log_path, "w", encoding="utf-8") as fh:
    fh.write("TASK-109 -- extract one game OUT OF THE SHIPPED ZIP and run it\n")
    fh.write("zip   : %s\n" % ZIP)
    fh.write("game  : %s\n" % GAME)
    fh.write("files extracted: %d\n\n" % len(extracted))
    fh.write("command: %s --headless --quit-after 120\n" % exe)
    fh.write("cwd    : %s\n\n" % game_dir)
    fh.write("exit code                : %d\n" % psi.returncode)
    fh.write("READY line present       : %s\n" % ready)
    fh.write("listen=false line present: %s\n" % listen_false)
    fh.write("stderr bytes             : %d\n\n" % len(err))
    fh.write("--- stdout ---\n%s\n" % out)
    fh.write("--- stderr ---\n%s\n" % err)
    fh.write("\nZIP-EXTRACT-RUN VERDICT: %s\n" % ("PASS" if ok else "FAIL"))
print("evidence written to %s" % log_path)
sys.exit(0 if ok else 1)
