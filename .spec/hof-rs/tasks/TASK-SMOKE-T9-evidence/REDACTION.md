# Redaction record — the committed environment dump (DR-69)

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
