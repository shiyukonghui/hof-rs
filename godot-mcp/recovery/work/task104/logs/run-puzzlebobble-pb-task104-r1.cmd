@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "F:\moonbit-hof-rs\godot-mcp\tools\run_game_session.ps1" -Game puzzlebobble -RunTag pb-task104-r1 -EditorPort 9966 -GamePort 9967
echo RUN_EXIT=%ERRORLEVEL%
