@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "F:\moonbit-hof-rs\godot-mcp\tools\run_game_session.ps1" -Game missilecommand -RunTag mc-task103-r1 -EditorPort 9962 -GamePort 9963 -Session "F:\moonbit-hof-rs\godot-mcp\tools\sessions\missilecommand\session.json"
echo RUN_EXIT=%ERRORLEVEL%
