#!/bin/sh
# hoh-acceptance-lib.sh — DR-75 shared acceptance-ledger logic.  KEEP LF LINE ENDINGS.
#
# Sourced by `.githooks/pre-push` (the mechanical push gate) and by
# `scripts/accept-commit.sh` (the writer/verifier).  It is the single source of
# truth for the ledger's location, its record syntax and its validity rules, so
# the gate and the writer can never drift apart.
#
# Ledger: <absolute git dir>/hoh-accepted-commits.txt
#
#   accepted <sha> <report.md> <verdict> <stamp> [note]
#     sha      40 lowercase hex characters
#     report   repo-root-relative path of the acceptance report, ending in .md
#              and carrying the ACCEPTANCE token in its file name (DR-81 ⑤)
#     verdict  exactly `pass`; only an independent passing acceptance authorises a push
#     stamp    YYYY-MM-DDTHH:MM:SSZ (UTC)
#     note     optional free-form trailing text
#
# Comment lines start with `#`; blank lines are ignored; fields are separated by
# whitespace runs.  Any other non-blank line makes the ledger invalid, and an
# invalid ledger refuses *every* push (fail closed).
#
# `set -f` is not decoration: record lines and pre-push protocol lines are split
# with unquoted expansion, and untrusted text must never glob-expand into a
# filesystem listing.

set -u
set -f

HOH_LEDGER_FILE=hoh-accepted-commits.txt

# Sets HOH_GIT_DIR and HOH_LEDGER.  Non-zero when the git directory cannot be
# resolved (not inside a repository).
hoh_resolve_ledger() {
    HOH_GIT_DIR=$(git rev-parse --absolute-git-dir 2>/dev/null) || return 1
    [ -n "$HOH_GIT_DIR" ] || return 1
    HOH_LEDGER=$HOH_GIT_DIR/$HOH_LEDGER_FILE
    return 0
}

# True (0) when $1 is a 40-character lowercase hex object name.
hoh_is_sha() {
    [ ${#1} -eq 40 ] || return 1
    case $1 in
        *[!0-9a-f]*) return 1 ;;
    esac
    return 0
}

# True (0) when $1 is `YYYY-MM-DDTHH:MM:SSZ`.
hoh_is_stamp() {
    case $1 in
        [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z) return 0 ;;
    esac
    return 1
}

# True (0) when $1 is a plausible repo-root-relative **acceptance artifact** path.
#
# DR-81 ⑤: a tracked `.md` was not enough.  `smoke-t14`'s own report commit
# (`03ee2e3`) was marked against `TASK-SMOKE-T14-REPORT.md` — the audited object
# itself — and reached `origin/master` before any independent acceptance existed.
# The marking source must therefore be an acceptance artifact: the final path
# component must carry the literal token `ACCEPTANCE`.  A round report
# (`*-REPORT.md`) cannot contain it, and neither can any other object under
# audit, so the audited thing can never authorise its own push.
HOH_ACCEPTANCE_TOKEN=ACCEPTANCE
hoh_is_acceptance_report() {
    case $1 in
        ''|/*|*\\*|.) return 1 ;;
        */*.md) ;;
        *) return 1 ;;
    esac
    case ${1##*/} in
        *"$HOH_ACCEPTANCE_TOKEN"*) return 0 ;;
    esac
    return 1
}

# Validates one record line ($1).  Sets HOH_RECORD_ERROR and, when valid,
# HOH_RECORD_SHA / HOH_RECORD_REPORT / HOH_RECORD_VERDICT / HOH_RECORD_STAMP.
hoh_check_record() {
    HOH_RECORD_ERROR=
    HOH_RECORD_SHA=
    HOH_RECORD_REPORT=
    HOH_RECORD_VERDICT=
    HOH_RECORD_STAMP=
    set -- $1
    [ $# -ge 5 ] || {
        HOH_RECORD_ERROR='expected at least 5 fields (accepted <sha> <report.md> <verdict> <stamp> [note])'
        return 1
    }
    HOH_RECORD_KIND=$1
    HOH_RECORD_SHA=$2
    HOH_RECORD_REPORT=$3
    HOH_RECORD_VERDICT=$4
    HOH_RECORD_STAMP=$5
    [ "$HOH_RECORD_KIND" = accepted ] || {
        HOH_RECORD_ERROR="unknown record kind \`$HOH_RECORD_KIND\` (only \`accepted\` is defined)"
        return 1
    }
    hoh_is_sha "$HOH_RECORD_SHA" || {
        HOH_RECORD_ERROR="\`$HOH_RECORD_SHA\` is not a 40-character lowercase hex commit id"
        return 1
    }
    hoh_is_acceptance_report "$HOH_RECORD_REPORT" || {
        HOH_RECORD_ERROR="\`$HOH_RECORD_REPORT\` is not an acceptance artifact: the marking source must be a repo-root-relative \`.md\` file whose name contains \`$HOH_ACCEPTANCE_TOKEN\` (e.g. \`...-ACCEPTANCE.md\`); a round report (\`*-REPORT.md\`) or the audited object itself may not authorise its own push"
        return 1
    }
    [ "$HOH_RECORD_VERDICT" = pass ] || {
        HOH_RECORD_ERROR="verdict \`$HOH_RECORD_VERDICT\` authorises nothing; only \`pass\` does"
        return 1
    }
    hoh_is_stamp "$HOH_RECORD_STAMP" || {
        HOH_RECORD_ERROR="\`$HOH_RECORD_STAMP\` is not a YYYY-MM-DDTHH:MM:SSZ timestamp"
        return 1
    }
    return 0
}

# Validates the whole ledger.  Sets HOH_LEDGER_RECORDS, HOH_ACCEPTED (a
# space-padded list of accepted shas) and HOH_LEDGER_ERROR.  Non-zero when the
# ledger is missing, unreadable or carries any malformed record line.
hoh_validate_ledger() {
    HOH_LEDGER_RECORDS=0
    HOH_ACCEPTED=' '
    HOH_LEDGER_ERROR=
    HOH_LEDGER_LINE=0
    if [ ! -e "$HOH_LEDGER" ]; then
        HOH_LEDGER_ERROR="missing ($HOH_LEDGER)"
        return 1
    fi
    if [ ! -f "$HOH_LEDGER" ]; then
        HOH_LEDGER_ERROR="not a regular file ($HOH_LEDGER)"
        return 1
    fi
    if [ ! -r "$HOH_LEDGER" ]; then
        HOH_LEDGER_ERROR="unreadable ($HOH_LEDGER)"
        return 1
    fi
    while IFS= read -r hoh_line || [ -n "${hoh_line:-}" ]; do
        HOH_LEDGER_LINE=$((HOH_LEDGER_LINE + 1))
        case $hoh_line in
            ''|'#'*) continue ;;
        esac
        hoh_check_record "$hoh_line" || {
            HOH_LEDGER_ERROR="line $HOH_LEDGER_LINE is malformed: $HOH_RECORD_ERROR (raw: $hoh_line)"
            return 1
        }
        HOH_LEDGER_RECORDS=$((HOH_LEDGER_RECORDS + 1))
        HOH_ACCEPTED=$HOH_ACCEPTED$HOH_RECORD_SHA' '
    done < "$HOH_LEDGER"
    return 0
}

# True (0) when commit $1 carries a `pass` record in the validated ledger.
hoh_is_accepted() {
    hoh_is_sha "$1" || return 1
    case $HOH_ACCEPTED in
        *" $1 "*) return 0 ;;
    esac
    return 1
}

# Finds the record for commit $1 (no output; sets HOH_FOUND, HOH_FOUND_REPORT,
# HOH_FOUND_STAMP).  Non-zero when there is none.
hoh_find_record() {
    HOH_FOUND=
    HOH_FOUND_REPORT=
    HOH_FOUND_STAMP=
    while IFS= read -r hoh_line || [ -n "${hoh_line:-}" ]; do
        case $hoh_line in
            ''|'#'*) continue ;;
        esac
        hoh_check_record "$hoh_line" || continue
        if [ "$HOH_RECORD_SHA" = "$1" ]; then
            HOH_FOUND=$hoh_line
            HOH_FOUND_REPORT=$HOH_RECORD_REPORT
            HOH_FOUND_STAMP=$HOH_RECORD_STAMP
            return 0
        fi
    done < "$HOH_LEDGER"
    return 1
}

# The first line of report $1 that names a verdict — the report side of the
# commit -> report -> push cross-check.  Empty when there is none.
hoh_report_verdict_line() {
    [ -f "$1" ] || return 1
    grep -m 1 -i verdict "$1" 2>/dev/null
}

hoh_stamp_now() {
    date -u +%Y-%m-%dT%H:%M:%SZ
}
