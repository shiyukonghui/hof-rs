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
| `iter-*/traj/**`, `iter-*/candidate/**`, `iter-*/planner-view/**`, `versions/**`, `quarantine/**` | **generated copy** `<name>.redacted.<ext>`; the original keeps every byte | these are what a consumer parses or cites: the runtime reads trajectories back for usage and enrichment, the Tester cites the frozen candidate, and the acceptance names trajectories as E1's evidence form |
| anything else the run wrote (its own logs, `result.json`, `meta.json`, working-tree files) | in-place rewrite, and only when the result still parses as JSON | nothing parses them, and DR-19 still requires the credential's *location* not to survive anywhere under `runs/<id>` |

`SealedAreas` is the mechanism; `run_loop::frozen_evidence_roots` builds the list
from the run-directory layout.  A refusal — a splice that would break a JSON
document — is recorded in the pass report and written into `warnings.log`, never
applied silently.

## 3. The two forms, verbatim

`samples/env.original.txt` is the input (stand-in values, so this directory
carries no disclosure).  `samples/env.redacted.txt` is what a **frozen** file's
generated copy looks like.  Note what survives:

* the JSON escape `\n` — the old scan deleted its backslash, which is what turned
  a valid string into a control character inside a string;
* the field that followed the assignment in the same JSON string, and its closing
  quote and comma;
* every byte outside the replaced span, which
  `hof_rs::runtime::secrets::bytes_changed_outside_spans` reports as `0`.
