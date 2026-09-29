#!/usr/bin/env bash
# Independent acceptance: plant -> generator must fail non-zero -> byte-exact restore.
set -u
ENG=/f/moonbit-hof-rs/godot-mcp/godot
W=/f/moonbit-hof-rs/godot-mcp/recovery/work/task153-accept
cd "$ENG" || exit 99

B=modules/mcp_server/docs/rename-baseline-tools-list.json
M=modules/mcp_server/docs/tool-rename-map.json
G=modules/mcp_server/scripts/gen_renamed_contract.py
A=modules/mcp_server/docs/tools_list.renamed.json

snapshot() {
  echo "--- git status --porcelain ---"; git status --porcelain
  echo "--- git diff --stat ---"; git diff --stat
  echo "--- hash-object vs HEAD blob ---"
  for f in $B $M $G $A; do
    printf "%-70s work=%s head=%s\n" "$f" "$(git hash-object "$f")" "$(git rev-parse HEAD:"$f")"
  done
}

PID="$1"
TARGET="$B"
case "$PID" in A*) TARGET="$B";; B*) TARGET="$M";; esac

echo "######## $PID #######"
echo "=== PRE-STATE (must be clean) ==="
snapshot
echo
echo "=== PLANT $PID ==="
python "$W/my_plants.py" "$PID"
echo "PLANT_EXIT=$?"
echo
echo "=== PLANTED STATE ==="
git status --porcelain
stat -c "planted bytes=%s" "$TARGET"
sha256sum "$TARGET"
echo
echo "=== GENERATOR (all defaults, scratch --out) ==="
rm -f "$W/$PID-should-not-exist.json"
python "$G" --out "$W/$PID-should-not-exist.json"
GEN_EXIT=$?
echo "GEN_EXIT=$GEN_EXIT"
if [ -e "$W/$PID-should-not-exist.json" ]; then
  echo "OUTPUT_WRITTEN=True"
else
  echo "OUTPUT_WRITTEN=False"
fi
echo
echo "=== RESTORE (git checkout -- $TARGET) ==="
git checkout -- "$TARGET"
echo "restore exit=$?"
echo
echo "=== POST-STATE (must be clean, blobs must match HEAD) ==="
snapshot
echo "post bytes=$(stat -c %s $TARGET)"
sha256sum "$TARGET"
echo "######## $PID done #######"
