@echo off
cd /d "F:\moonbit-hof-rs"
git add -A
git commit -F "F:\moonbit-hof-rs\godot-mcp\recovery\work\task103\commit-message-final3.txt"
echo GIT_EXIT=%ERRORLEVEL%
git log --oneline -3
git status --short
