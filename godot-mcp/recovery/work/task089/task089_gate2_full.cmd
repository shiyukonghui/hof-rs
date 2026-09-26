@echo off
REM task089 gate 2: the whole engine doctest suite, launched from cmd (iron rule 4).
cd /d H:\rebuild\godot
bin\godot.windows.editor.x86_64.mono.console.exe --headless --test
set "RC=%ERRORLEVEL%"
echo GATE2_FULL_DOCTEST_EXIT=%RC%
exit /b %RC%
