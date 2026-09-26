@echo off
REM task090 gate 1: module doctests (launched from cmd, iron rule 4).
cd /d H:\rebuild\godot
"bin\godot.windows.editor.x86_64.mono.console.exe" --headless --test --test-case=[MCPServer]*
set "RC=%ERRORLEVEL%"
echo TASK090_GATE1_EXIT=%RC%
exit /b %RC%
