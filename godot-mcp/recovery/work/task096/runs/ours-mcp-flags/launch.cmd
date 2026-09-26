@echo off
cd /d "F:\moonbit-hof-rs\godot-mcp\godot\bin"
"F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.console.exe" --path "F:\moonbit-hof-rs\godot-mcp\recovery\work\task096\probe" --mcp-port=9897 --mcp-trace=F:\moonbit-hof-rs\godot-mcp\recovery\work\task096\runs\ours-mcp-flags\trace.jsonl --mcp-capture=every_call --mcp-capture-dir=F:\moonbit-hof-rs\godot-mcp\recovery\work\task096\runs\ours-mcp-flags\shots --mcp-capture-viewport=2d
echo PROBE_EXIT=%ERRORLEVEL%
