@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "F:\moonbit-hof-rs\godot-mcp\tools\run_game_session.ps1" -Game sokoban -RunTag soko-task101-r2 -EditorPort 9944 -GamePort 9945
echo RUN_EXIT=%ERRORLEVEL%
