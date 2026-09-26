@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "F:\moonbit-hof-rs\godot-mcp\tools\run_game_session.ps1" -Game towerdefense -RunTag td-task103-r3 -EditorPort 9960 -GamePort 9961 -Session "F:\moonbit-hof-rs\godot-mcp\tools\sessions\towerdefense\session.json"
echo RUN_EXIT=%ERRORLEVEL%
