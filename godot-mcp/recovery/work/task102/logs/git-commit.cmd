@echo off
cd /d "F:\moonbit-hof-rs"
git add -A
git commit -F "F:\moonbit-hof-rs\godot-mcp\recovery\work\task102\commit-message-report.txt"
echo COMMIT_EXIT=%ERRORLEVEL%
