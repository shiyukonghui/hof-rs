# TASK-DR72-EVIDENCE — controlled evidence for the DR-72 batch

This directory holds the raw outputs quoted by `TASK-DR72-REPORT.md`.  It is the
batch's **controlled evidence area**: nothing under `runs/**` was written (or even
temporarily created) while producing it.

| file | what it is |
|---|---|
| `REDACTION-POLICY.md` | the ② policy and the two generated-copy examples |
| `samples/env.original.txt` | the redaction sample's declared **input** (authored, frozen; DR-74 does not edit it) |
| `samples/env.redacted.txt` | the same sample as the production pass leaves it |
| `samples/env.spans.txt` | the exact byte spans that pass replaced |
| `samples/env-real.original.txt` | **DR-74 addition**: the same sample written in the **real encoding** measured from `runs/smoke-t10/iter-1/traj/tester.attempt1.json` (doubled path backslashes + real `\` + `n` escapes) |
| `samples/env-real.redacted.txt` | the real-encoding sample as the production pass leaves it |
| `samples/env-real.spans.txt` | its exact spans (`HOH_ARTIFACT_DIR [51..124)`, `PATH [126..187)`) |

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

**DR-74 ⑥ correction — by addition, not by rewriting.**  The DR-72 sample's line
separators were written as an escaped backslash followed by `n`, an encoding no
trajectory uses.  `samples/env.original.txt` is **authored sample evidence** and
keeps every byte; the real encoding is contributed as the **new pair
`env-real.*`**, so the original (and the DR-72 report's reference to it) stays
readable while the corrected encoding is a separate, freshly generated artifact.
Both pairs' outputs (`*.redacted.txt`, `*.spans.txt`) are regenerated from the
production pass by
`tests/frozen_evidence.rs::the_redacted_sample_is_regenerable_from_the_production_pass`
(which compares them byte for byte and leaves the freshly produced copies in
`target/dr72-redaction-sample/`).  The regenerated `env.redacted.txt` now carries
one span, `HOH_ARTIFACT_DIR [53..172)`: the DR-69 rule ends an assignment at `;`,
so for this input the `;` after `…bin` bounds it and `;C:\stand-in\bin` survives —
the real-encoding pair is the one that shows the intended shape (two spans, both
`<redacted>`, `</output>` intact, no carriage return).

The one finding that this rule does **not** silently repair is the already
committed `TASK-SMOKE-T10-evidence/analysis/redaction_defect.txt`.  It carries a
harness assignment and a drive-letter user PATH tail from the round it analyses.
Its bytes are the frozen evidence of the very defect it documents, so the batch
reports it (see the report's §5) instead of rewriting it.
