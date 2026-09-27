@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "F:\moonbit-hof-rs\godot-mcp\tools\new_game.ps1" -Name snake -Class SnakeGame
echo NEWGAME_EXIT=%ERRORLEVEL%
