@echo off
REM task090: import + headless smoke test of the round-8 project (cmd, iron rule 4).
cd /d H:\rebuild\godot
set "ENG=bin\godot.windows.editor.x86_64.mono.console.exe"
echo ===== import =====
"%ENG%" --headless --path H:\rebuild\projects\mcpplay8 --import
echo IMPORT_EXIT=%ERRORLEVEL%
echo ===== smoke (headless, 60 frames) =====
"%ENG%" --headless --path H:\rebuild\projects\mcpplay8 --quit-after 60
echo SMOKE_EXIT=%ERRORLEVEL%
exit /b 0
