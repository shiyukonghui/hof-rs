@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "F:\moonbit-hof-rs\godot-mcp\tools\run_game_session.ps1" -Game rtype -RunTag rt-task104-r1 -EditorPort 9964 -GamePort 9965
echo RUN_EXIT=%ERRORLEVEL%
