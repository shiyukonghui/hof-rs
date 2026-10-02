# `.githooks/` — the DR-75 acceptance push gate

The repository's hard rule is that **nothing is pushed before an independent
acceptance passes**.  On 2026-10-01 at 08:13:18 that rule was broken by a
`git pull` and a `git push` four seconds apart, executed by an unknown actor
(`DECISIONS.md` D283/D284): git's reflog carries no actor identity, so no one
could be named.  The rule is therefore now **mechanical**: a versioned `pre-push`
hook refuses to push any commit that has not been recorded as accepted, so the
gate does not depend on *who* runs `git push`.

## What is here

| file | role |
|---|---|
| `pre-push` | the gate: parses git's pre-push stdin protocol and refuses any commit in the pushed range without an `accepted … pass` record |
| `hoh-acceptance-lib.sh` | the single source of truth for the ledger's path, record syntax and validity rules; sourced by the gate and by `scripts/accept-commit.sh` |
| `README.md` | this file: how to arm it, how to mark, and what it cannot do |

The ledger itself is **local machine state** and is not versioned:

```
<absolute git dir>/hoh-accepted-commits.txt
```

```
accepted <40-hex-commit> <report.md> pass <YYYY-MM-DDTHH:MM:SSZ> [note]
```

Why a local file rather than a versioned list or `git notes`? A *versioned*
ledger cannot authorise its own tip — the commit recording "X was accepted" would
itself be unrecorded, and closing that gap needs an exemption, which is how gates
rot.  Keeping it in the git directory also makes a missing or corrupt ledger an
unambiguous, fail-closed condition.  The cost (it does not travel with a clone)
is one of the limits below.

## How to enable

```sh
scripts/install-hooks.sh
```

That sets `core.hooksPath` to this checkout's absolute `.githooks` directory, and
it is idempotent: running it again prints `already installed` and changes nothing.
`scripts/install-hooks.sh --uninstall` is the rollback.

**One-line proof that it is really in effect:**

```sh
git config --get core.hooksPath      # must print <this checkout>/.githooks
```

and the gate really bites when that command is silent while a push carries an
unaccepted commit.  A functional check that needs no remote:

```sh
printf 'refs/heads/master %s refs/heads/master %s\n' "$(git rev-parse HEAD)" "$(git rev-parse HEAD)" | .githooks/pre-push origin .
```

It exits non-zero and prints `REFUSED` while `HEAD` has no acceptance record.

## How to mark a commit after an acceptance passes

```sh
scripts/accept-commit.sh mark <sha> .spec/hof-rs/tasks/TASK-XX-ACCEPTANCE.md pass
scripts/accept-commit.sh list      # what is recorded
scripts/accept-commit.sh show <sha>  # the record next to the report's own verdict line
scripts/accept-commit.sh verify    # the ledger is structurally valid
```

Only `pass` may be recorded, the report must be a tracked `.md` file (so
*commit → report → push* can be cross-checked from git history), and marking the
same commit twice with the same report is a no-op.

**DR-81 ⑤ — the marking source must be an acceptance artifact.**  The file name
must contain `ACCEPTANCE` (e.g. `TASK-XX-ACCEPTANCE.md`), and both the writer and
the gate enforce it.  A round report (`*-REPORT.md`) or the audited object itself
may not authorise its own push: `smoke-t14`'s report commit `03ee2e3` was marked
against `TASK-SMOKE-T14-REPORT.md` and reached `origin/master` at 10:43:21,
before any independent acceptance existed.  A ledger carrying such a record is
not usable, so the gate refuses *every* push until it is corrected.

In a fresh clone the ledger is empty, so the first push is refused until the
acceptances of the commits being pushed are re-recorded.

## Capability limits — read these before trusting the gate

1. **The hook is local.** It exists in this working copy only, so pushing from
   another clone or another machine does not go through this gate at all.
2. **`git push --no-verify` bypasses it.** The flag is a documented hole, not an
   authorisation: the gate is mechanical discipline, not a cryptographic
   guarantee, and it cannot stop anyone who decides to route around it.
3. **Real enforcement belongs on the server side** (GitHub branch
   protection/rulesets, least-privilege deploy keys). That is the recommended
   fix for an actor you cannot control; this repository deliberately does **not**
   change any remote setting.

## Line endings

`pre-push`, `hoh-acceptance-lib.sh` and the scripts in `scripts/` are shell
programs, so their line endings are part of their correctness; `.gitattributes`
pins them with `-text`.  Measured here: the system gitconfig on this machine
(`C:/Program Files/Git/etc/gitconfig`) sets `core.autocrlf=true`, which would
otherwise rewrite them to CRLF on checkout for anyone with the same setting.

## Refusal text

Every refusal names the commits, the marker source, how to record an acceptance,
and the warning that `--no-verify` is a documented hole.  A refusal is always
non-zero, and a *push that cannot be evaluated* (an unknown remote base, an
unreadable ledger, a malformed protocol line) is refused rather than allowed.
