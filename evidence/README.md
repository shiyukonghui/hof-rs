# `evidence/` — the committed corpus the cost and observation conclusions rest on

Every cost figure in `.spec/bevy/LIVE-COST-REPORT.md`, `COST-REPORT.md`,
`FIX-REPORT.md`, `ROUND-4-REPORT-COMPLETE.md`, `WRITE-ACCOUNTING-REPORT.md` and
`COVERAGE-EVIDENCE-REPORT.md`, and every observation figure in
`COVERAGE-EVIDENCE-REPORT.md`, is derived from the recorded material under
`runs/**` — and `runs/` is **gitignored**. The acceptance that passed
(`.spec/bevy/ACCEPTANCE-ACCOUNTING.md`, R-2) recorded that as the batch's
largest residual risk: "a clone, a CI run or another machine cannot re-run the
accounting tests or reproduce any number".

The full tree is far too large to commit — it is **11,229 files /
12,775,066,006 bytes / 11.898 GiB** — but the parts the conclusions actually
rest on are not. This directory is those parts.

## What is here

| group | files | bytes | what it is |
|---|---|---|---|
| `cost/` | 4 | 4,166,273 | the four recorded Developer trajectories the cost analysis reads, byte-identical to their `runs/**` originals |
| `observation/round4/deterministic/` | 37 | 222,299 | the workspace-side battery evidence (`.hoh/deterministic/**`): one record per step, the verbatim payload behind each criterion, `mcp-errors.jsonl` |
| `observation/round4/round/` | 70 | 326,506 | the round's own evidence directory (`runs/bevy-round4/**`): 57 raw MCP→BRP call files, the readings, the gate, the launch facts, the launch ledger |
| `observation/round4/iter-{1,2,3}/` | 6 | 53,776 | each iteration's `result.json` and the Tester's `evidence.json` |
| `observation/round4/meta.json` | 1 | 2,285 | the round's own `meta.json` |
| **total** | **118** | **4,771,139** | **4.55 MiB** |

`index.json` is the machine-readable index: for each headline number, the
committed files that reproduce it and the command that does it. It also states
which conclusions **cannot** be reproduced from the repository, and why.

## How it was produced

`tools/build_evidence.py` copied the files listed above from their recorded
locations:

* `F:/moonbit-hof-rs/runs/{livecost1,round4}/…` (gitignored recordings);
* `F:/hof-bevy-r4-run/workspace/.hoh/deterministic/…` (the round's workspace,
  outside the repository).

Before writing each destination it ran `tools/keyscan.py`, a transcription of
`src/runtime/secrets.rs`'s key-shape rule
(`key_shaped_tokens` / `looks_key_shaped`), and **refused** any file that
matched. All 118 committed files are clean: no key-shaped token and no
key-shaped assignment. The scan fingerprints findings and never prints a value.

## How to use it

```text
cargo test --offline --test evidence_reproduction   # re-derives the headline numbers
cargo test --offline --test write_accounting        # the write accounting, now from evidence/cost/
cargo test --offline --test prd_coverage            # the frozen surface registry and the denominator
```

`tests/write_accounting.rs` prefers `evidence/cost/` and falls back to the
machine's own `runs/**` recordings, so it runs both from a clone and on the
machine that recorded the rounds.

## What is deliberately not here

The trajectories of the other roles, the other rounds and the five round-4
attempts; the built binaries and target caches; the model's full prose. None of
them changes a headline number, and all of them are under the gitignored
`runs/**` or outside the repository. `index.json`'s
`not_reproducible_from_the_repository` list is the honest boundary of what this
corpus buys.
