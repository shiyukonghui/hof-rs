# Redaction record — the committed environment dump (DR-69, **corrected by DR-70**)

> **CORRECTION (DR-70, 2026-09-30).** Everything below this box is the DR-69 text,
> **preserved verbatim** because it is the defective self-report that DR-69's own
> acceptance (D2) measured against.  It is **wrong on two counts** and the
> correction is recorded here rather than by silently rewriting it.
>
> **What DR-69 actually did to the bytes.** Its rule matched
> `HOH_MODEL_API_KEY=` and then ran to the **next `"`**.  The record it matched is
> *already truncated mid-token* — the dump cut the value off at `…/AppD`, so the
> assignment's closing quote is not on that line.  The match therefore ran
> **through the line break and into the next record**
> (`s008 rc=0 | dir /b -p; echo "`), replacing 54 bytes with a 30-byte marker:
>
> | fact | original (`dc9d350`, also `3adab37^`) | after DR-69 (`3adab37`) | after DR-70 |
> |---|---|---|---|
> | committed blob bytes | 52200 | 52176 (−24) | 52205 (+5) |
> | LF | 184 | **183** | 184 |
> | CR (working tree, `core.autocrlf=true`) | 0 | **183** | 0 |
> | records | 184 | **183** (`s008` merged) | 184 |
> | `dir /b -p` present | 1 | **0** | 1 |
>
> So the old sentence "*53 bytes* were removed. **Nothing else in the file was
> touched**" is **false**: the committed blob lost 24 bytes, one record boundary
> and the `dir /b -p` command — which is the `-p` defect's own evidence — were
> destroyed, and the working tree gained 183 CR bytes that the blob does not have.
> (The acceptance's `52200 → 52359` is the *working-tree* pair: `52176 + 183 CR`).
>
> **What DR-70 did instead.** `git show dc9d350:<path>` was restored
> **byte-for-byte**, and then exactly **one** byte run was replaced: the truncated
> credential-assignment value `$(cat /c/Users/wyl/AppD` (25 bytes) became
> `<redacted-key-path-by-DR-69>` (30 bytes).  No other byte differs — no line
> ending, no record boundary, no `dir /b -p`.  `.gitattributes` now pins
> `.spec/hof-rs/tasks/TASK-SMOKE-T9-evidence/**` to `-text`, so a checkout cannot
> silently convert these bytes to CRLF again (DR-58 does the same for its
> fixtures).  `tests/frozen_evidence.rs` asserts the record count, the pure-LF
> line endings, the preserved `-p` record and the absence of the credential
> channel.
>
> The chunk below is the **superseded** text.  It is not deleted: a redaction
> record whose numbers were wrong is itself part of the audit trail.

---

## Superseded DR-69 text (retained verbatim, marked corrected)

**What was redacted.** `experiment/dev1_commands.txt` is a command-level dump of
the `smoke-t9` Developer's shell.  Step `s008` ran `set | findstr /i "HOH"`, so
the harness's own launcher variable `DSH_TERM_CMD` was written into the file (and
into the round's trajectory), and that variable's value is an assignment to
`HOH_MODEL_API_KEY`.

**The change.** The *value* of that assignment was replaced with
`<redacted-key-path-by-DR-69>`; **53 bytes** were removed.  Nothing else in the
file was touched.  No plaintext credential was ever present — the acceptance of
the round verified that independently — but the assignment recorded the
credential's channel, which is exactly what a committed evidence artifact must
not carry.

**Why this is the fix and not a rewrite of history.** The production rule now
does the same thing automatically: `runtime::secrets::redact_secret_assignments`
replaces the assignment to any known credential variable in every file under
`runs/<id>/**` after each role call, independent of whether this process can
resolve the key itself.  This record exists because the bytes in this directory
were frozen **before** that rule existed.

**Residual (not changed here, deliberately).**
`TASK-SMOKE-T9-ACCEPTANCE.md` and `TASK-SMOKE-T9-REPORT.md` still name the key
file's temp path as part of *disclosing* this defect.  Editing a frozen
acceptance report to remove the evidence of its own defect would destroy the
audit trail, so the scheduler decides whether those disclosures should also be
redacted.  `runs/smoke-t9/**` was **not** touched: it is read-only evidence.
