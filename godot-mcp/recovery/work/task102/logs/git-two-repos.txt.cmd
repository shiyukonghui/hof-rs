@echo off
cd /d "F:\moonbit-hof-rs"
echo === MAIN REPO (branch, HEAD) ===
git rev-parse --abbrev-ref HEAD
git rev-parse HEAD
echo === MAIN REPO git log --oneline -8 ===
git log --oneline -8
echo === MAIN REPO git status --short ===
git status --short
echo
cd /d "F:\moonbit-hof-rs\godot-mcp\godot"
echo === ENGINE REPO (branch, HEAD) ===
git rev-parse --abbrev-ref HEAD
git rev-parse HEAD
echo === ENGINE REPO remote ===
git rev-parse refs/remotes/origin/feature/mcp-server-module-rebuild
echo === ENGINE REPO git log --oneline -8 ===
git log --oneline -8
echo === ENGINE REPO git status --short ===
git status --short
echo === ENGINE REPO diff vs the build anchor ===
git diff --name-only --no-renames 2385fe2fb..HEAD
