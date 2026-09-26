@echo off
set MAIN=F:\moonbit-hof-rs
set ENG=F:\moonbit-hof-rs\godot-mcp\godot
echo ===MAIN rev-parse HEAD===
git -C "%MAIN%" rev-parse HEAD
echo ===MAIN log --oneline -8===
git -C "%MAIN%" log --oneline -8
echo ===MAIN status --short===
git -C "%MAIN%" status --short
echo ===ENG rev-parse HEAD===
git -C "%ENG%" rev-parse HEAD
echo ===ENG rev-parse origin ref===
git -C "%ENG%" rev-parse refs/remotes/origin/feature/mcp-server-module-rebuild
echo ===ENG log --oneline -8===
git -C "%ENG%" log --oneline -8
echo ===ENG status --short===
git -C "%ENG%" status --short
echo ===PROCESSES===
tasklist /FI "IMAGENAME eq godot*"
echo ===PORTS 9958-9975===
netstat -ano | findstr /r ":99[5-7][0-9] "
echo ===PORTS_DONE===
echo SNAPSHOT_EXIT=%ERRORLEVEL%
