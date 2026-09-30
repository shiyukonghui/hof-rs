# TASK-DR72-EVIDENCE — controlled evidence for the DR-72 batch

This directory holds the raw outputs quoted by `TASK-DR72-REPORT.md`.  It is the
batch's **controlled evidence area**: nothing under `runs/**` was written (or even
temporarily created) while producing it.

| file | what it is |
|---|---|
| `REDACTION-POLICY.md` | the ② policy and the two generated-copy examples |
| `samples/env.original.txt` | the redaction sample's declared **input** |
| `samples/env.redacted.txt` | the same sample as the production pass leaves it |
| `samples/env.spans.txt` | the exact byte spans that pass replaced |

**Disclosure rule (dispatcher addition 1).** No file here contains a real
environment value: every harness path is a stand-in, no path carries a user name,
and the credential is the literal `test-key-not-a-secret` placeholder.  The batch
enforces this with
`tests/frozen_evidence.rs::the_batch_evidence_products_carry_no_environment_values`,
which scans this directory for harness assignment values, for `PATH`-style values
and for any drive-letter path that contains a user directory — **a path carrying a
user name counts as disclosure even though it carries no credential**.

`samples/env.original.txt` is the one file allowed to spell an assignment out: it
is the declared input of the redaction under test, and without it the sample
could not demonstrate that the pass removes anything.  It is synthetic: the
values are `F:\stand-in\…` and `C:\stand-in\…`.

The one finding that this rule does **not** silently repair is the already
committed `TASK-SMOKE-T10-evidence/analysis/redaction_defect.txt`.  It carries a
harness assignment and a drive-letter user PATH tail from the round it analyses.
Its bytes are the frozen evidence of the very defect it documents, so the batch
reports it (see the report's §5) instead of rewriting it.
