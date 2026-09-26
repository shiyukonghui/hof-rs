@echo off
cd /d "F:\moonbit-hof-rs\godot-mcp\godot"
"F:\moonbit-hof-rs\godot-mcp\godot\bin\godot.windows.editor.x86_64.mono.console.exe" --path "F:\moonbit-hof-rs\godot-mcp\projects\snake" --mcp-port=9889 --mcp-trace="F:\moonbit-hof-rs\godot-mcp\recovery\work\task093\diag-render\trace-game.jsonl" --mcp-capture=every_call --mcp-capture-dir="F:\moonbit-hof-rs\godot-mcp\recovery\work\task093\diag-render\shots" --mcp-capture-viewport=2d
