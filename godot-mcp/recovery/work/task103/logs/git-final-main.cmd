@echo off
setlocal enabledelayedexpansion
echo ===== MAIN REPO F:\moonbit-hof-rs
cd /d "F:\moonbit-hof-rs"
echo --- rev-parse HEAD & git rev-parse HEAD
echo --- log --oneline -8 & git log --oneline -8
echo --- status --short & git status --short
echo ===== ENGINE REPO F:\moonbit-hof-rs\godot-mcp\godot
cd /d "F:\moonbit-hof-rs\godot-mcp\godot"
echo --- rev-parse HEAD & git rev-parse HEAD
echo --- rev-parse refs/remotes/origin/feature/mcp-server-module-rebuild & git rev-parse refs/remotes/origin/feature/mcp-server-module-rebuild
echo --- log --oneline -8 & git log --oneline -8
echo --- status --short & git status --short
echo --- branch & git rev-parse --abbrev-ref HEAD
echo SNAPSHOT_EXIT=%ERRORLEVEL%
