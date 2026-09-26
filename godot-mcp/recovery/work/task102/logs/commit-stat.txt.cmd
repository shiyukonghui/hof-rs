@echo off
cd /d "F:\moonbit-hof-rs"
git show --stat --oneline HEAD | findstr /C:"files changed"
git show --stat --oneline HEAD | find /c /v ""
