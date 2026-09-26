@echo off
REM task089 gate 1: module doctest, launched from cmd (iron rule 4).
cd /d H:\rebuild\godot
bin\godot.windows.editor.x86_64.mono.console.exe --headless --test "--test-case=[MCPServer]*"
set "RC=%ERRORLEVEL%"
echo GATE1_MODULE_DOCTEST_EXIT=%RC%
exit /b %RC%
