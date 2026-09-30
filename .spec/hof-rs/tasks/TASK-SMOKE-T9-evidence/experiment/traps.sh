#!/usr/bin/env bash
# Three false-green traps (read-only), SMOKE-T9
set -u
cd /f/moonbit-hof-rs
echo "==== TRAP 1: git diff on a non-existent pathspec ===="
echo "--- git diff --stat -- definitely/not/a/real/path ---"
out=$(git diff --stat -- definitely/not/a/real/path 2>&1); rc=$?
echo "stdout+stderr=[$out] exit=$rc"
echo
echo "==== TRAP 2: cmd eats ^ (rev^ queries must be in bash) ===="
PATHSPEC=".spec/hof-rs/tasks/TASK-SMOKE-T9.md"
echo "bash : git cat-file -e HEAD^:$PATHSPEC ->"
git cat-file -e "HEAD^:$PATHSPEC" 2>/dev/null; echo "  exit=$?"
echo "bash : git cat-file -e HEAD:$PATHSPEC ->"
git cat-file -e "HEAD:$PATHSPEC" 2>/dev/null; echo "  exit=$?"
echo "control (both revisions have DECISIONS.md):"
git cat-file -e "HEAD^:DECISIONS.md" 2>/dev/null; echo "  bash HEAD^:DECISIONS.md exit=$?"
git cat-file -e "HEAD:DECISIONS.md" 2>/dev/null; echo "  bash HEAD:DECISIONS.md exit=$?"
echo "control (path in neither):"
git cat-file -e "HEAD^:definitely/not/here" 2>/dev/null; echo "  bash exit=$?"
echo "--- now through cmd (^ is eaten) ---"
cmd //c "git cat-file -e HEAD^:$PATHSPEC" 2>/dev/null; echo "  cmd exit=$?"
cmd //c "git cat-file -e HEAD:$PATHSPEC" 2>/dev/null; echo "  cmd exit=$?"
echo
echo "==== TRAP 3: outer repo does not track the engine tree ===="
echo "outer ls-files godot-mcp        = $(git ls-files godot-mcp | wc -l)"
echo "outer ls-files godot-mcp/godot  = $(git ls-files godot-mcp/godot | wc -l)"
git check-ignore -v godot-mcp/godot 2>&1 || echo "(not ignored)"
echo "git diff --stat -- godot-mcp/godot/bin ->"
out=$(git diff --stat -- godot-mcp/godot/bin 2>&1); rc=$?
echo "  [$out] exit=$rc"
echo "nested HEAD = $(git -C godot-mcp/godot rev-parse HEAD)"
echo "nested status --porcelain -uall lines = $(git -C godot-mcp/godot status --porcelain -uall | wc -l)"
echo
echo "==== TRAP 3b: runs/** is gitignored too ===="
git check-ignore -v runs/smoke-t9/meta.json 2>&1 || echo "(not ignored)"
