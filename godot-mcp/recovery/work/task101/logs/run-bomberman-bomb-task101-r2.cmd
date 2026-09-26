@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "F:\moonbit-hof-rs\godot-mcp\tools\run_game_session.ps1" -Game bomberman -RunTag bomb-task101-r2 -EditorPort 9946 -GamePort 9947
echo RUN_EXIT=%ERRORLEVEL%
