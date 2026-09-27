@echo off
rem TASK-109 step 3a: GodotTools' export path requires <name>.sln next to <name>.csproj
rem (BuildManager uses GodotSharpDirs.ProjectSlnPath). The games only ship a .csproj,
rem so the .sln files are ADDED here as build files. No game source is modified.
setlocal
set ROOT=F:\moonbit-hof-rs\godot-mcp\projects
for %%g in (asteroids bomberman breakout flappy frogger game2048 lunarlander match3 minesweeper missilecommand pacman platformer pong puzzlebobble rtype snake sokoban spaceinvaders tetris towerdefense) do (
  pushd "%ROOT%\%%g"
  if exist "%%g.slnx" del /q "%%g.slnx"
  if exist "%%g.sln" del /q "%%g.sln"
  dotnet new sln --format sln --name %%g --output . >nul 2>&1
  dotnet sln %%g.sln add %%g.csproj >nul 2>&1
  if exist "%%g.sln" (echo SLN %%g OK) else (echo SLN %%g FAILED)
  popd
)
echo SLN-DONE
