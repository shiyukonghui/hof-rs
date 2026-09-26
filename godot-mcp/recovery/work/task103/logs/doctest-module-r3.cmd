@echo off
cd /d "F:\moonbit-hof-rs\godot-mcp\godot"
"F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.console.exe" --headless --test --test-case=[MCPServer]*
echo ENGINE_EXIT=%ERRORLEVEL%
