@echo off
setlocal
set SRC=H:\rebuild\projects
set DST=F:\moonbit-hof-rs\godot-mcp\projects
echo === COPY PROJECTS ===
echo SRC=%SRC%
echo DST=%DST%
robocopy "%SRC%" "%DST%" /E /COPY:DAT /DCOPY:DAT /R:1 /W:1 /NFL /NDL /NP /MT:8
set RC=%ERRORLEVEL%
echo ROBOCOPY_EXIT=%RC%
if %RC% GEQ 8 exit /b 1
exit /b 0
