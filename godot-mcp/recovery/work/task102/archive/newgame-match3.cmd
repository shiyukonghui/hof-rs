@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "F:\moonbit-hof-rs\godot-mcp\tools\new_game.ps1" -Name match3 -Class Match3Game
echo NEWGAME_EXIT=%ERRORLEVEL%
