#!/bin/sh
# accept-commit.sh — DR-75 marker writer/verifier for the acceptance push gate.
#
# The ledger is deliberately *local machine state* inside the git directory:
#
#     <absolute git dir>/hoh-accepted-commits.txt
#
# Why not a versioned file in the tree?  Because a versioned ledger cannot
# authorise its own tip: the commit that recorded "X was accepted" would itself
# be unrecorded, and every attempt to fix that needs an exemption.  Exemptions
# are how gates rot.  The cost of this choice is stated in .githooks/README.md:
# the ledger does not travel with a clone, so a fresh clone must re-record the
# acceptances of the commits it intends to push.
#
# KEEP LF LINE ENDINGS.  The record format and the validity rules live in
# .githooks/hoh-acceptance-lib.sh, shared with the hook itself.
#
#   accept-commit.sh init
#   accept-commit.sh mark <commit> <report.md> pass [note...]
#   accept-commit.sh list
#   accept-commit.sh show <commit>
#   accept-commit.sh verify

set -u
set -f

usage() {
    cat >&2 <<'EOF'
usage: accept-commit.sh init
       accept-commit.sh mark <commit> <report.md> pass [note...]
       accept-commit.sh list
       accept-commit.sh show <commit>
       accept-commit.sh verify

`mark` writes one `accepted <sha> <report.md> pass <stamp> [note]` record after
an independent acceptance has passed.  Only `pass` authorises a push.  The
marking source must be an acceptance artifact: its file name must contain
`ACCEPTANCE` (DR-81 ⑤), so a round report or the audited object itself can never
authorise its own push.
EOF
}

HOH_SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || {
    printf '%s\n' "accept-commit: cannot resolve the script directory" >&2
    exit 1
}
HOH_LIB=$HOH_SCRIPT_DIR/../.githooks/hoh-acceptance-lib.sh
if [ ! -r "$HOH_LIB" ]; then
    printf '%s\n' "accept-commit: $HOH_LIB is missing or unreadable; refusing to act (fail closed)" >&2
    exit 1
fi
. "$HOH_LIB"

hoh_die() {
    printf '%s\n' "accept-commit: $1" >&2
    exit 1
}

hoh_require_repository() {
    hoh_resolve_ledger || hoh_die 'not inside a git repository (cannot resolve the git directory)'
}

# Idempotent creation of the ledger with its header.  The header is documentation,
# not data: a comment line never authorises anything.
hoh_create_ledger() {
    [ -e "$HOH_LEDGER" ] && return 0
    printf '%s\n' \
        '# hoh accepted-commits ledger (DR-75).  Written by scripts/accept-commit.sh; read by .githooks/pre-push.' \
        '# record: accepted <40-hex-commit> <report.md> pass <YYYY-MM-DDTHH:MM:SSZ> [note]' \
        '# Only an independent acceptance whose verdict is pass authorises a push.  Do not hand-edit this file.' \
        > "$HOH_LEDGER" || hoh_die "cannot create $HOH_LEDGER"
    printf '%s\n' "accept-commit: created $HOH_LEDGER"
}

hoh_report_commit_line() {
    git log -1 --format='%h %s' -- "$1" 2>/dev/null
}

case ${1:-} in
    init)
        hoh_require_repository
        hoh_create_ledger
        hoh_validate_ledger || hoh_die "the ledger is not usable: $HOH_LEDGER_ERROR"
        printf '%s\n' "accept-commit: $HOH_LEDGER_RECORDS record(s); ledger: $HOH_LEDGER"
        if [ "$HOH_LEDGER_RECORDS" -eq 0 ]; then
            printf '%s\n' "accept-commit: no commit is marked yet, so every push is refused until one is"
        fi
        ;;

    mark)
        [ $# -ge 4 ] || { usage; exit 2; }
        hoh_require_repository
        HOH_COMMIT=$2
        HOH_REPORT=$3
        HOH_VERDICT=$4
        shift 4
        HOH_NOTE=
        for HOH_ARG in "$@"; do
            if [ -z "$HOH_NOTE" ]; then HOH_NOTE=$HOH_ARG; else HOH_NOTE=$HOH_NOTE' '$HOH_ARG; fi
        done

        [ "$HOH_VERDICT" = pass ] || hoh_die "verdict \`$HOH_VERDICT\` authorises nothing; only \`pass\` does.  A failed or unverified acceptance must never be recorded as accepted."
        # DR-81 ⑤: the marking source must be an **acceptance artifact**, never the
        # audited object itself.  `smoke-t14`'s report commit was marked against
        # its own `*-REPORT.md` and reached the remote before its acceptance.
        hoh_is_acceptance_report "$HOH_REPORT" || hoh_die "the marking source \`$HOH_REPORT\` is not an acceptance artifact.  It must be a repo-root-relative \`.md\` file whose name contains \`ACCEPTANCE\` (e.g. \`.spec/hof-rs/tasks/TASK-XX-ACCEPTANCE.md\`); a round report (\`*-REPORT.md\`) or the audited object itself may not authorise its own push."
        HOH_SHA=$(git rev-parse --verify --quiet "$HOH_COMMIT^{commit}" 2>/dev/null)
        [ -n "$HOH_SHA" ] || hoh_die "\`$HOH_COMMIT\` is not a commit in this repository"
        hoh_is_sha "$HOH_SHA" || hoh_die "resolved \`$HOH_COMMIT\` to \`$HOH_SHA\`, which is not a 40-character lowercase hex id"
        [ -f "$HOH_REPORT" ] || hoh_die "the report \`$HOH_REPORT\` does not exist relative to $PWD"
        [ -s "$HOH_REPORT" ] || hoh_die "the report \`$HOH_REPORT\` is empty"
        git ls-files --error-unmatch -- "$HOH_REPORT" >/dev/null 2>&1 \
            || hoh_die "the report \`$HOH_REPORT\` is not tracked by git; commit it first so the record can be cross-checked"

        hoh_create_ledger
        hoh_validate_ledger || hoh_die "the ledger is not usable: $HOH_LEDGER_ERROR"

        if hoh_find_record "$HOH_SHA"; then
            case $HOH_FOUND in
                "accepted $HOH_SHA $HOH_REPORT pass "*)
                    printf '%s\n' "accept-commit: already recorded for $HOH_SHA: $HOH_FOUND"
                    exit 0
                    ;;
                *)
                    hoh_die "$HOH_SHA is already recorded against a different record: $HOH_FOUND"
                    ;;
            esac
        fi

        HOH_LINE="accepted $HOH_SHA $HOH_REPORT pass $(hoh_stamp_now)"
        [ -n "$HOH_NOTE" ] && HOH_LINE="$HOH_LINE $HOH_NOTE"
        hoh_check_record "$HOH_LINE" || hoh_die "refusing to write a record I cannot validate: $HOH_RECORD_ERROR"
        printf '%s\n' "$HOH_LINE" >> "$HOH_LEDGER" || hoh_die "cannot append to $HOH_LEDGER"
        printf '%s\n' "accept-commit: recorded $HOH_LINE"
        printf '%s\n' "accept-commit: ledger: $HOH_LEDGER"
        ;;

    list)
        hoh_require_repository
        [ -e "$HOH_LEDGER" ] || hoh_die "no ledger at $HOH_LEDGER (nothing is recorded)"
        hoh_validate_ledger || hoh_die "the ledger is not usable: $HOH_LEDGER_ERROR"
        printf '%s\n' "accept-commit: ledger: $HOH_LEDGER ($HOH_LEDGER_RECORDS record(s))"
        while IFS= read -r hoh_line || [ -n "${hoh_line:-}" ]; do
            case $hoh_line in
                ''|'#'*) continue ;;
            esac
            printf '%s\n' "$hoh_line"
        done < "$HOH_LEDGER"
        ;;

    show)
        [ $# -ge 2 ] || { usage; exit 2; }
        hoh_require_repository
        HOH_SHA=$(git rev-parse --verify --quiet "$2^{commit}" 2>/dev/null)
        [ -n "$HOH_SHA" ] || hoh_die "\`$2\` is not a commit in this repository"
        [ -e "$HOH_LEDGER" ] || hoh_die "no ledger at $HOH_LEDGER (nothing is recorded)"
        hoh_validate_ledger || hoh_die "the ledger is not usable: $HOH_LEDGER_ERROR"
        hoh_find_record "$HOH_SHA" || hoh_die "no acceptance record for $HOH_SHA"
        printf '%s\n' "record: $HOH_FOUND"
        printf '%s\n' "report: $HOH_FOUND_REPORT"
        if [ -f "$HOH_FOUND_REPORT" ]; then
            printf '%s\n' "report verdict line: $(hoh_report_verdict_line "$HOH_FOUND_REPORT")"
        else
            printf '%s\n' "report verdict line: (the cited report is not in this checkout)"
        fi
        HOH_REPORT_COMMIT=$(hoh_report_commit_line "$HOH_FOUND_REPORT")
        if [ -n "$HOH_REPORT_COMMIT" ]; then
            printf '%s\n' "report commit: $HOH_REPORT_COMMIT"
        else
            printf '%s\n' "report commit: (the cited report has no commits here)"
        fi
        ;;

    verify)
        hoh_require_repository
        if ! hoh_validate_ledger; then
            printf '%s\n' "accept-commit: INVALID: $HOH_LEDGER_ERROR" >&2
            printf '%s\n' "accept-commit: ledger: $HOH_LEDGER" >&2
            exit 1
        fi
        printf '%s\n' "accept-commit: OK: $HOH_LEDGER_RECORDS record(s); ledger: $HOH_LEDGER"
        if [ "$HOH_LEDGER_RECORDS" -eq 0 ]; then
            printf '%s\n' "accept-commit: note: no commit is marked yet, so every push is refused"
        fi
        ;;

    *)
        usage
        exit 2
        ;;
esac
