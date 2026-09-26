@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "F:\moonbit-hof-rs\godot-mcp\tools\run_game_session.ps1" -Game match3 -RunTag task103-x1-after -EditorPort 9958 -GamePort 9959 -Session "F:\moonbit-hof-rs\godot-mcp\recovery\work\task103\sessions\session-x1.json"
echo RUN_EXIT=%ERRORLEVEL%
