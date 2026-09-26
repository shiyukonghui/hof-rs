@echo off
setlocal
set PROJ=F:\moonbit-hof-rs\godot-mcp\projects\pong
echo === dotnet build (offline: NuGet.config clears all sources, only the fork nupkgs) ===
cd /d %PROJ%
echo --- effective package sources ---
dotnet nuget list source --configfile "%PROJ%\NuGet.config"
echo --- build ---
dotnet build "%PROJ%\pong.csproj" -c Debug --nologo
echo DOTNET_BUILD_EXIT=%ERRORLEVEL%
echo --- output assembly ---
if exist "%PROJ%\.godot\mono\temp\bin\Debug" dir /b "%PROJ%\.godot\mono\temp\bin\Debug"
exit /b 0
