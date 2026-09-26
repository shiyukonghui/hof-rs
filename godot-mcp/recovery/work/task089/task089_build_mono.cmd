@echo off
REM task089: the mono editor build, launched from cmd (iron rule 4).
REM The caller redirects stdout/stderr with Start-Process -RedirectStandardOutput.
cd /d H:\rebuild\godot
echo ===== task089 mono build START %DATE% %TIME% =====
echo SCONS: D:\Anaconda\Scripts\scons.exe
"D:\Anaconda\Scripts\scons.exe" platform=windows target=editor module_mono_enabled=yes tests=yes -j8 -k
set "RC=%ERRORLEVEL%"
echo ===== task089 mono build END %DATE% %TIME% =====
echo TASK089_BUILD_EXIT=%RC%
exit /b %RC%
