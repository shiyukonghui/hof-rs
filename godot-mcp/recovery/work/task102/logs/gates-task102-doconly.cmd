@echo off
cd /d "F:\moonbit-hof-rs\godot-mcp"
powershell -NoProfile -ExecutionPolicy Bypass -File "F:\moonbit-hof-rs\godot-mcp\tools\run_gates.ps1" -Tag task102-doconly
echo GATES_EXIT=%ERRORLEVEL%
