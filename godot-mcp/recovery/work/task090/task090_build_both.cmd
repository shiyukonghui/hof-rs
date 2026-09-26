@echo off
REM task090: the MONO and then the PLAIN editor builds at the same HEAD, serial
REM (bin\obj is shared, so the two must not run at the same time), launched from
REM cmd (iron rule 4). The caller redirects with Start-Process.
cd /d H:\rebuild\godot
echo ===== task090 mono build START %DATE% %TIME% =====
"D:\Anaconda\Scripts\scons.exe" platform=windows target=editor module_mono_enabled=yes tests=yes -j8 -k
set "RC1=%ERRORLEVEL%"
echo TASK090_MONO_EXIT=%RC1%
echo ===== task090 plain build START %DATE% %TIME% =====
"D:\Anaconda\Scripts\scons.exe" platform=windows target=editor module_mono_enabled=no tests=yes -j8 -k
set "RC2=%ERRORLEVEL%"
echo TASK090_PLAIN_EXIT=%RC2%
echo ===== task090 both builds END %DATE% %TIME% =====
exit /b %RC2%
