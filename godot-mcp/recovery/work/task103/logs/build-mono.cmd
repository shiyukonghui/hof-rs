@echo off
cd /d "F:\moonbit-hof-rs\godot-mcp\godot"
modules\mcp_server\scripts\mcp057_build_mono.cmd
echo BUILD_EXIT=%ERRORLEVEL%
