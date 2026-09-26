@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "F:\moonbit-hof-rs\godot-mcp\tools\run_game_session.ps1" -Game platformer -RunTag plat-task102-r2 -EditorPort 9940 -GamePort 9941
echo RUN_EXIT=%ERRORLEVEL%
