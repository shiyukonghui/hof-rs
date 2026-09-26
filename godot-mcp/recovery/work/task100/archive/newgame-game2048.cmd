@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "F:\moonbit-hof-rs\godot-mcp\tools\new_game.ps1" -Name game2048 -Class Game2048Game
echo NEWGAME_EXIT=%ERRORLEVEL%
