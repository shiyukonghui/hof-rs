@echo off
REM TASK-116: rebuild every game's C# assembly after the playability fixes.
REM iron rule 3: builds are launched from cmd. One dotnet build per game, output
REM captured to the game's runs\playability\<game>\build.log by python-free `>`
REM is NOT allowed (iron rule 1), so the log is written by dotnet itself via
REM --no-incremental / console redirection is avoided: we simply print and read
REM the exit codes below.
setlocal enabledelayedexpansion
cd /d F:\moonbit-hof-rs\godot-mcp\projects
set FAILED=0
for %%G in (asteroids bomberman breakout flappy frogger game2048 lunarlander match3 minesweeper missilecommand pacman platformer pong puzzlebobble rtype snake sokoban spaceinvaders tetris towerdefense) do (
  echo === %%G
  cd /d F:\moonbit-hof-rs\godot-mcp\projects\%%G
  dotnet build -v quiet -nologo
  if errorlevel 1 (
    echo BUILD_FAILED %%G
    set FAILED=1
  ) else (
    echo BUILD_OK %%G
  )
)
echo FAILED=%FAILED%
endlocal
