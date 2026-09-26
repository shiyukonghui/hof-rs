@echo off
cd /d "F:\moonbit-hof-rs\godot-mcp\godot"
modules\mcp_server\scripts\build_local.cmd -Force
echo BUILD_EXIT=%ERRORLEVEL%
