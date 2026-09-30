#!/usr/bin/env bash
cd /f/moonbit-hof-rs || exit 9
echo "=== TRAP 1: nonexistent pathspec ==="
git diff --stat -- definitely/not/a/real/path
echo "trap1 exit=$?"
echo "=== TRAP 2: rev^ in bash ==="
git cat-file -e 'fe129a1^:.spec/hof-rs/tasks/TASK-DR68-ACCEPTANCE.md'; echo "bash fe129a1^:DR68ACC exit=$?"
git cat-file -e 'fe129a1:.spec/hof-rs/tasks/TASK-DR68-ACCEPTANCE.md'; echo "bash fe129a1:DR68ACC exit=$?"
git cat-file -e 'HEAD^:DECISIONS.md'; echo "bash HEAD^:DECISIONS exit=$?"
git cat-file -e 'HEAD:DECISIONS.md'; echo "bash HEAD:DECISIONS exit=$?"
git cat-file -e 'fe129a1^:definitely/not/here'; echo "bash fe129a1^:nothere exit=$?"
echo "=== TRAP 3: engine tree untracked by outer ==="
echo "outer ls-files godot-mcp = $(git ls-files godot-mcp | wc -l)"
echo "outer ls-files godot-mcp/godot = $(git ls-files godot-mcp/godot | wc -l)"
git check-ignore -v godot-mcp/godot
git diff --stat -- godot-mcp/godot/bin
echo "enginebin diff exit=$?"
git check-ignore -v runs/smoke-t10/meta.json
echo "=== nested engine ==="
echo "nested HEAD = $(git -C godot-mcp/godot rev-parse HEAD)"
echo "nested porcelain lines = $(git -C godot-mcp/godot status --porcelain -uall | wc -l)"
