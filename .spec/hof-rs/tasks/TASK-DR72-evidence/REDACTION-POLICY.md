# DR-72 ② — the redaction policy, and the two forms it produces

## 1. The decision

**In-place rewriting of evidence is forbidden.**  `DECISIONS.md` D276 records
that it produced three separate injuries:

1. **DR-69** — the assignment scan ran past a value that was already truncated
   mid-token, swallowed the line break and the head of the next record, and
   merged two records (`TASK-SMOKE-T9-evidence/experiment/dev1_commands.txt` went
   183 records instead of 184);
2. **DR-70** — a byte count was published from a file that had since been
   rewritten, so the number no longer described the bytes on disk;
3. **this batch's round** — `runs/smoke-t10/iter-1/traj/tester.attempt1.json`,
   left unparseable at byte 412862 because the scan mistook a JSON escape for the
   end of the physical line.

## 2. What replaced it

Two forms, and which one applies is decided by the path, not by the caller:

| area | form | why |
|---|---|---|
| `iter-*/traj/**`, `iter-*/candidate/**`, `versions/**`, `quarantine/**` | **generated copy** `<name>.redacted.<ext>`; the original keeps every byte | these are what a consumer parses or cites: the runtime reads trajectories back for usage and enrichment, the Tester cites the frozen candidate, and the acceptance names trajectories as E1's evidence form |
| `iter-*/planner-view/**` | **in-place rewrite**, and only when the result still parses as JSON | DR-19 still requires the credential's *location* not to survive anywhere under `runs/<id>`, a role writes its own environment dump into its own view, and **nothing parses planner-view** (the exception documented in `run_loop::frozen_evidence_roots` and pinned by `secret_isolation.rs::a_leaked_secret_is_erased_and_counted`).  DR-74 ⑥(D4): this row previously listed planner-view in the generated-copy row above, contradicting the shipped code |
| anything else the run wrote (its own logs, `result.json`, `meta.json`, working-tree files) | in-place rewrite, and only when the result still parses as JSON | nothing parses them, and DR-19 still requires the credential's *location* not to survive anywhere under `runs/<id>` |

`SealedAreas` is the mechanism; `run_loop::frozen_evidence_roots` builds the list
from the run-directory layout.  A refusal — a splice that would break a JSON
document — is recorded in the pass report and written into `warnings.log`, never
applied silently.

**Superseded wording (DR-74 ⑥/D4), kept here so a reader can see what changed.**
The DR-72 table's generated-copy row read:

> `iter-*/traj/**`, `iter-*/candidate/**`, `iter-*/planner-view/**`,
> `versions/**`, `quarantine/**` — **generated copy**; the original keeps every
> byte

which contradicts the shipped code (`frozen_evidence_roots` deliberately does not
seal `iter-*/planner-view`).  The corrected table above is authoritative; the same
correction is applied to the `record.rs::iteration_directories` comment.

## 3. The two forms, verbatim

`samples/env.original.txt` is the input (stand-in values, so this directory
carries no disclosure).  `samples/env.redacted.txt` is what a **frozen** file's
generated copy looks like.  Note what survives:

* the JSON escape `\n` — the scan stops **at** the escape without consuming it,
  so the escape's two bytes survive and the string stays closed.  **Rationale
  corrected by DR-74 ⑥(D5).**  The superseded wording was:

  > the old scan deleted its backslash, which is what turned a valid string into
  > a control character inside a string;

  That is false on its own terms: deleting one byte of a valid escape produces a
  *different* escape, and the historical control character came from the opposite
  mistake — the scan ran past the escape to the physical line ending and left a
  **physical newline inside an unterminated string**.  The reason not to consume
  the terminator is **content fidelity** (the escape survives, and so do the
  closing quote, the comma and the field after it).  Probe: the same input spliced
  with the span ending at the backslash, at the backslash + 1 and at backslash + 2
  all parsed, and none left a control character in the string.
* the field that followed the assignment in the same JSON string, and its closing
  quote and comma;
* every byte outside the replaced span, which
  `hof_rs::runtime::secrets::bytes_changed_outside_spans` reports as `0`.

**DR-74 ①③ correction to the sample — by addition, not by rewriting.**  The
superseded encoding claim was that `samples/env.original.txt` is the sample's
input; that file is **authored, frozen sample evidence** and DR-74 leaves every
byte of it untouched (editing evidence in place is exactly what this policy
forbids).  The DR-72 sample writes its line separators as `\\` + `n` (an escaped
backslash followed by `n`), an encoding no trajectory uses — which is why the
committed `env.redacted.txt` had shown the DR-72 ① defect: the harness assignment
was replaced by `<redacted>` and then immediately followed by a decoded carriage
return and the path tail `epo\runs\…`.  The corrected form is contributed as the
**new pair `samples/env-real.*`**, written in the **real encoding** measured from
`runs/smoke-t10/iter-1/traj/tester.attempt1.json` (doubled backslashes for every
Windows path separator, a real `\` + `n` escape ending each dump line).  Both
pairs' `*.redacted.txt` / `*.spans.txt` are regenerated from the production pass
by `frozen_evidence.rs::the_redacted_sample_is_regenerable_from_the_production_pass`,
which compares them byte for byte.
(`env.redacted.txt` shows one span, `HOH_ARTIFACT_DIR [53..172)`: the DR-69 rule
ends an assignment at `;`, so `;C:\stand-in\bin` survives for *that* input; the
real-encoding pair shows the intended shape — two spans, no carriage return,
`</output>` intact.  This `;`-tail bound is also stated in the DR-74 report.)
