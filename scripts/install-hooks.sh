#!/bin/sh
# install-hooks.sh — DR-75 idempotent arming of the acceptance push gate.
#
# A versioned hook only takes effect when git is told to look for hooks in the
# versioned directory, so `core.hooksPath` must point at the `.githooks` of the
# checkout that contains this script.  This command sets that, and running it
# again is a no-op.  KEEP LF LINE ENDINGS.
#
#   scripts/install-hooks.sh              # arm the repository you are standing in
#   scripts/install-hooks.sh <hooks-dir>  # arm it with a different hooks directory
#   scripts/install-hooks.sh --uninstall  # roll back in one command
#
# It changes only this repository's local git config.  It never touches a remote
# setting, and it never contacts the network.

set -u
set -f

usage() {
    cat <<'EOF'
usage: install-hooks.sh [<hooks-dir>]
       install-hooks.sh --uninstall
       install-hooks.sh --help

Arms the DR-75 acceptance push gate in the repository you are standing in by
setting core.hooksPath to the versioned hooks directory of this checkout
(default: the `.githooks` directory next to this script).  Idempotent.
EOF
}

HOH_SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || {
    printf '%s\n' "install-hooks: cannot resolve the script directory" >&2
    exit 1
}
HOH_HOOKS_DIR=$HOH_SCRIPT_DIR/../.githooks
HOH_UNINSTALL=0

while [ $# -gt 0 ]; do
    case $1 in
        --uninstall) HOH_UNINSTALL=1 ;;
        -h|--help) usage; exit 0 ;;
        -*) printf '%s\n' "install-hooks: unknown option \`$1\`" >&2; usage >&2; exit 2 ;;
        *) HOH_HOOKS_DIR=$1 ;;
    esac
    shift
done

if ! git rev-parse --git-dir >/dev/null 2>&1; then
    printf '%s\n' "install-hooks: not inside a git repository; run this in the repository you want to arm" >&2
    exit 1
fi

if [ "$HOH_UNINSTALL" -eq 1 ]; then
    if git config --get core.hooksPath >/dev/null 2>&1; then
        git config --unset core.hooksPath || {
            printf '%s\n' "install-hooks: \`git config --unset core.hooksPath\` failed" >&2
            exit 1
        }
        printf '%s\n' "install-hooks: removed core.hooksPath - the push gate is no longer armed here"
    else
        printf '%s\n' "install-hooks: core.hooksPath was not set; nothing to remove"
    fi
    exit 0
fi

# `pwd -W` is Git for Windows' native-path spelling; elsewhere `pwd` is already
# the right thing.  git has to be handed a path it can look hooks up in.
HOH_HOOKS_ABS=$(CDPATH= cd -- "$HOH_HOOKS_DIR" 2>/dev/null && { pwd -W 2>/dev/null || pwd; })
if [ -z "${HOH_HOOKS_ABS:-}" ]; then
    printf '%s\n' "install-hooks: hooks directory \`$HOH_HOOKS_DIR\` does not exist" >&2
    exit 1
fi

for HOH_REQUIRED in pre-push hoh-acceptance-lib.sh; do
    if [ ! -r "$HOH_HOOKS_ABS/$HOH_REQUIRED" ]; then
        printf '%s\n' "install-hooks: $HOH_HOOKS_ABS/$HOH_REQUIRED is missing or unreadable" >&2
        printf '%s\n' "install-hooks: refusing to arm the gate with an incomplete hooks directory" >&2
        exit 1
    fi
done

HOH_CURRENT=$(git config --get core.hooksPath 2>/dev/null) || HOH_CURRENT=
if [ "$HOH_CURRENT" = "$HOH_HOOKS_ABS" ]; then
    printf '%s\n' "install-hooks: already installed: core.hooksPath = $HOH_HOOKS_ABS"
    printf '%s\n' "install-hooks: nothing to do (this command is idempotent)"
    exit 0
fi

git config core.hooksPath "$HOH_HOOKS_ABS" || {
    printf '%s\n' "install-hooks: \`git config core.hooksPath $HOH_HOOKS_ABS\` failed" >&2
    exit 1
}

printf '%s\n' "install-hooks: core.hooksPath: ${HOH_CURRENT:-<unset>} -> $HOH_HOOKS_ABS"
printf '%s\n' "install-hooks: every push made here now passes through $HOH_HOOKS_ABS/pre-push"
printf '%s\n' "install-hooks: verify with: git config --get core.hooksPath"
printf '%s\n' "install-hooks: this is a local, bypassable control - see .githooks/README.md for its limits"
