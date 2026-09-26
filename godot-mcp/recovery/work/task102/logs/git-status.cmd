@echo off
cd /d "F:\moonbit-hof-rs"
git status --porcelain=v1
echo STATUS_EXIT=%ERRORLEVEL%
echo ---COUNT---
git status --porcelain=v1 | find /c /v ""
