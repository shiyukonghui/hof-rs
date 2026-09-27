@echo off
REM TASK-116: rebuild only the three games that received the refusal/restart counters.
setlocal
cd /d F:\moonbit-hof-rs\godot-mcp\projects
set FAILED=0
for %%G in (flappy frogger pacman) do (
  echo === %%G
  cd /d F:\moonbit-hof-rs\godot-mcp\projects\%%G
  dotnet build -v quiet -nologo
  if errorlevel 1 ( echo BUILD_FAILED %%G & set FAILED=1 ) else ( echo BUILD_OK %%G )
)
echo FAILED=%FAILED%
endlocal
