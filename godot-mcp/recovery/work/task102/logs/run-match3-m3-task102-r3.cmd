@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "F:\moonbit-hof-rs\godot-mcp\tools\run_game_session.ps1" -Game match3 -RunTag m3-task102-r3 -EditorPort 9942 -GamePort 9943
echo RUN_EXIT=%ERRORLEVEL%
