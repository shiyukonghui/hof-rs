@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "F:\moonbit-hof-rs\godot-mcp\tools\run_game_session.ps1" -Game snake -RunTag snake-task106-r1 -EditorPort 9930 -GamePort 9931
echo RUN_EXIT=%ERRORLEVEL%
