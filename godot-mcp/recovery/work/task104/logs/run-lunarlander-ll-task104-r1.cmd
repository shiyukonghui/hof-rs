@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "F:\moonbit-hof-rs\godot-mcp\tools\run_game_session.ps1" -Game lunarlander -RunTag ll-task104-r1 -EditorPort 9968 -GamePort 9969
echo RUN_EXIT=%ERRORLEVEL%
