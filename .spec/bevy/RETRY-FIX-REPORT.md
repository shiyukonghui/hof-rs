```json
{
  "schema": "hof-rs / bevy developer-format-error retry fix, measured offline over the committed cost corpus",
  "produced_at": "2026-10-06",
  "branch": "bevy-core",
  "head_at_start": "9d3f488",
  "offline": true,
  "round_run": false,
  "model_call_made": false,
  "engine_started": false,
  "committed": false,
  "pushed": false,
  "corpus": "evidence/cost/*.developer.attempt1.json (read-only; byte-unchanged)",
  "failure_shapes": {
    "distinct_shapes_found": 1,
    "shape": {
      "assistant_finish_reason": "stop",
      "assistant_message_tool_calls": null,
      "assistant_message_content": "non-empty list of {type:text} parts, 1431-2969 characters",
      "validation_that_rejected_it": "mini-swe-agent parse_toolcall_actions, ApiMode::ToolCalls (F:/RustProjects/mini-swe-agent-rust-mini/rust/src/models/mod.rs:139-153), reached from src/harness/mini.rs (from_value_with_mode(..., ApiMode::ToolCalls))",
      "error_text": "No tool calls found in the response. Every response MUST include at least one tool call.",
      "error_message_interrupt_type": "FormatError",
      "cost_of_one_occurrence": "one whole extra model call; mini attaches the failed call's `usage` to the FormatError message and run_compacting_agent adds it to the history (src/harness/compact.rs:441-463)"
    },
    "instances_total": 38,
    "instances_quoting_the_completion_marker": 29,
    "instances_without_the_marker": 9,
    "shapes_left_unfixed": [],
    "why_there_is_only_one_shape": "Across all 38 retry turns of round4-iter-1/2/3 the (finish_reason, tool_calls, content) triple takes exactly one value: stop / null / prose.  There is no `length` finish reason, no empty tool_calls array, no unparsable tool-call arguments, no unknown tool name and no missing `command` argument; `bash` is the only tool in the whole corpus (59 / 122 / 108 successful calls).  The folded livecost1-iter-1 recording contains zero retry turns.",
    "literal_failing_shape": "round4-iter-1, message index 61 (the format-error turn): the model's whole response is one prose report whose last two lines are `... it was started before these edits.` then a blank line then `COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT` — with no tool call.  Message index 58 ends `... all six of my physics/level unit tests pass.` with the marker inline earlier in the text; index 71 cites it mid-sentence.  All 20/10/8 retry turns are this, at every point the role believed it was finished (\"Iteration 1 complete.\", \"Everything is verified. Final state:\", \"I'm done. Final state verified:\")."
  },
  "root_cause": {
    "statement": "The three role prompts instructed the role to `end your run with the completion protocol COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT`.  The marker is only an exit as the FIRST LINE OF A COMMAND'S OUTPUT (mini-swe-agent-rust-mini/rust/src/environments/local.rs:118-128), and this harness runs the model in ApiMode::ToolCalls, where a reply with no tool call is an AgentError::Format.  The prompts never said *run this command*, so a role that obeyed them literally produced exactly the rejected shape — every time it believed it was finished.  9 of the 38 turns are the same report without the marker at all, so the defect has two halves: an unexecutable protocol spelling, and no positive requirement that every response carry a tool call.",
    "site": [
      "src/prompts/developer.md [output-contract] (the recorded defect: no 'command', and no 'a reply with no tool call is not a legal end' sentence that planner.md and tester.md did carry)",
      "src/prompts/planner.md [completion] and src/prompts/tester.md [completion] (named 'that command' but never spelled an executable one)"
    ],
    "prompt_was_followed_not_ignored": "evidence: 29/38 retry bodies quote the marker verbatim; 0/4 recordings contain any bash command mentioning the marker (checked over every recorded tool call), i.e. no role ever ran it"
  },
  "tests": {
    "file": "tests/prompt_shell_contract.rs",
    "added": [
      "every_role_prompt_states_that_a_reply_needs_a_tool_call",
      "the_documented_completion_command_really_ends_a_role_call"
    ],
    "removed_or_weakened": [],
    "red": {
      "command": "cargo test --offline --test prompt_shell_contract",
      "literal_exit_code": 101,
      "summary": "5 passed; 2 failed; 0 ignored; 0 measured; 0 filtered out",
      "failure_messages": [
        "every_role_prompt_states_that_a_reply_needs_a_tool_call: panicked at tests\\prompt_shell_contract.rs:484: planner.md does not state the positive output requirement: with no tool call the reply is rejected as a format error, and the recorded developer calls paid for that (20/10/8 turns over the three unfolded recordings)",
        "the_documented_completion_command_really_ends_a_role_call: panicked at tests\\prompt_shell_contract.rs:464: planner.md names `COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT` only in prose: it documents no executable command whose output starts with the marker ... A prompt must show the command to run."
      ],
      "confirmed_reason": "both failures are the claimed assertion, not a compile or setup error: the same command compiled and ran 5 other tests green in the same invocation"
    },
    "green": {
      "command": "cargo test --offline --test prompt_shell_contract",
      "literal_exit_code": 0,
      "summary": "7 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out"
    }
  },
  "change": {
    "kind": "make the request easier to answer correctly — an explicit, executable output requirement; no validation was relaxed",
    "files": [
      "src/prompts/mod.rs: new pub const COMPLETION_PROTOCOL_PLACEHOLDER ({{completion_protocol}}) and pub const COMPLETION_PROTOCOL, one shared shell-neutral [completion] section",
      "src/runtime/invoke.rs: render_prompt_for_shell substitutes {{completion_protocol}} (the single path every delivered prompt takes)",
      "src/prompts/developer.md, src/prompts/planner.md, src/prompts/tester.md: their [completion]/[output-contract] instruction replaced by {{completion_protocol}}"
    ],
    "delivered_section_requires": [
      "every response must carry at least one tool call; prose only *with* a call",
      "the only legal exit is a command whose first line of output is the marker and whose exit code is 0",
      "the command to run, in a fenced block: echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT",
      "explicitly: writing the marker into a reply instead of running it does not end the call"
    ],
    "why_a_shared_placeholder": "SHELL_TRUTH_PLACEHOLDER's own rationale in src/prompts/mod.rs: the three role prompts must not drift apart in the instruction that decides whether their calls end or retry",
    "validation_unchanged": "parse_toolcall_actions, the format-error template, max_consecutive_format_errors, the guard and the fail-fast paths are all untouched; the external mini-swe-agent crate was not modified"
  },
  "rejected_alternative": {
    "option": "repair the response instead of discarding it — when a prose-only reply's last line is the completion marker, synthesise the echo command (or treat the reply as the Submitted interrupt) rather than returning AgentError::Format",
    "why_rejected": [
      "it is exactly the validation that protects the pipeline: accepting a no-tool-call reply as an action means any prose-only reply becomes an action, and 9 of the 38 recorded turns carry no marker at all",
      "the only interception point is mini's parse_actions inside an external path dependency (F:/RustProjects/mini-swe-agent-rust-mini), outside this repository's branch discipline",
      "the instruction, not the model's obedience, is the defect: the recorded role did what its prompt said"
    ]
  },
  "measurement": {
    "method": "read every message carrying extra.response.usage in evidence/cost/*.developer.attempt1.json; a model call is one such message (assistant = parsed, user/FormatError = rejected); retry turns are the FormatError ones; their cost is the recorded usage.prompt_tokens of that very call.  Reconstructed totals reproduce hoh.usage exactly (2,544,563 / 12,765,478 / 5,137,090 / 3,537,843 prompt tokens over 69 / 125 / 102 / 150 calls).  Tokens-per-wire-byte recalibrated here (0.259864 / 0.256903 / 0.262988 / 0.338006) reproduces the frozen spike's 0.25712 / 0.25527 / 0.260054 / 0.323468 to within rounding.",
    "before": {
      "round4-iter-1": {"calls": 69, "prompt_tokens": 2544563, "retry_turns": 20, "retry_prompt_tokens": 876566, "retry_share_of_prompt": 0.34449, "retry_bodies_quoting_the_marker": 17, "retry_turn_call_numbers": [25, 27, 32, 33, 35, 37, 38, 41, 46, 48, 50, 52, 53, 56, 58, 59, 61, 62, 66, 67]},
      "round4-iter-2": {"calls": 125, "prompt_tokens": 12765478, "retry_turns": 10, "retry_prompt_tokens": 1486702, "retry_share_of_prompt": 0.11646, "retry_bodies_quoting_the_marker": 7, "retry_turn_call_numbers": [58, 85, 87, 91, 92, 95, 115, 120, 122, 123]},
      "round4-iter-3": {"calls": 102, "prompt_tokens": 5137090, "retry_turns": 8, "retry_prompt_tokens": 416910, "retry_share_of_prompt": 0.08116, "retry_bodies_quoting_the_marker": 5, "retry_turn_call_numbers": [30, 47, 49, 56, 58, 61, 64, 66]},
      "livecost1-iter-1": {"calls": 150, "prompt_tokens": 3537843, "retry_turns": 0, "retry_prompt_tokens": 0, "retry_share_of_prompt": 0.0, "retry_bodies_quoting_the_marker": 0, "retry_turn_call_numbers": []}
    },
    "after": {
      "round4-iter-1": {"retry_turns": 0, "retry_prompt_tokens": 0},
      "round4-iter-2": {"retry_turns": 0, "retry_prompt_tokens": 0},
      "round4-iter-3": {"retry_turns": 0, "retry_prompt_tokens": 0},
      "livecost1-iter-1": {"retry_turns": 0, "retry_prompt_tokens": 0},
      "basis": "projected from the recordings, not measured live: the shape the prompts asked for no longer exists, so the turns that were rejected for producing it cannot be produced.  No round and no model call were run, so this is the only available form of the after figure."
    },
    "what_the_after_figure_does_and_does_not_include": {
      "not_included": "the turn itself.  Under the fix the role still makes one turn at that moment; before, that turn was rejected and billed, after, the same turn runs the documented command and ends the call.  So 876,566 / 1,486,702 / 416,910 tokens are NOT saved by the fix — they move from 'a rejected turn' to 'the legal completion turn'.",
      "included_cascade_projected": {
        "what": "the FormatError history message each rejected turn inserted, which every later call re-sent; repriced at each recording's own tokens-per-wire-byte ratio",
        "round4-iter-1": 889649,
        "round4-iter-2": 1494510,
        "round4-iter-3": 428655,
        "livecost1-iter-1": 0,
        "floor_if_the_rejected_calls_were_simply_not_sent": {"round4-iter-1": 1667997, "round4-iter-2": 11278776, "round4-iter-3": 4720180, "livecost1-iter-1": 3537843}
      },
      "direction_not_quantified": "each recording's first rejected turn is at call 25 / 58 / 30 of 69 / 125 / 102, and the model's own prose at that moment says it is finished; if it runs the command there, every later call disappears and the call ends with exit_status Submitted (which is_failure_status() does not treat as a failure).  That is the largest term and the one only a live Developer call can measure: the recorded prompts cost 2,544,563 / 12,765,478 / 5,137,090 and calls 25..69 / 58..125 / 30..102 alone are 1,964,960 / 9,812,332 / 4,059,147 of it."
    }
  },
  "gate": {
    "command": "cargo test --offline",
    "literal_exit_code": 0,
    "passed": 802,
    "failed": 0,
    "ignored": 6,
    "listed": 808,
    "test_result_lines": 60,
    "compiler_warning_lines": 0,
    "baseline_on_the_untouched_tree_same_build_dir": {"literal_exit_code": 0, "passed": 800, "failed": 0, "ignored": 6, "listed": 806, "test_result_lines": 60, "compiler_warning_lines": 0},
    "delta": "exactly the two new tests: 800 -> 802 passed, 806 -> 808 listed; nothing removed or weakened",
    "fmt_command": "cargo fmt --all --check",
    "fmt_literal_exit_code": 0,
    "fmt_output_bytes": 0,
    "list_command": "cargo test --offline -- --list",
    "list_exit_code": 0,
    "list_count": 808,
    "list_ignored_command": "cargo test --offline -- --list --ignored",
    "list_ignored_exit_code": 0,
    "list_ignored_count": 6,
    "reruns": "no timing-sensitive failure occurred; the gate returned exit 0 on its first run (0 failed).  It was run a second time after DECISIONS.md and this report were added, because this reporting change makes new files under .spec/bevy/ visible to the tests that scan .spec/**: exit 0, 802 passed / 0 failed / 6 ignored / 808 listed, 0 compiler warnings, byte-identical counts to the first run",
    "gate_rerun_after_this_report_was_written": {"command": "cargo test --offline", "literal_exit_code": 0, "passed": 802, "failed": 0, "ignored": 6, "listed": 808, "compiler_warning_lines": 0, "fmt_literal_exit_code": 0},
    "build_dir": "D:/retry-fix-target (this batch's own; the repository's own target/ was not used)",
    "free_disk_before": "F: 9.1 G available (100% used, other batches' build dirs); the build was placed on D:, 82 G available",
    "working_tree_before_gate": "the six files this batch changed (src/prompts/developer.md, src/prompts/mod.rs, src/prompts/planner.md, src/prompts/tester.md, src/runtime/invoke.rs, tests/prompt_shell_contract.rs); the working tree also carries DECISIONS.md (17 insertions, 0 deletions) and this report"
  },
  "verified_myself": [
    "every before-figure is read out of the committed recordings, not from the spike: the per-call usage reconstruction reproduces hoh.usage.prompt_tokens/completion_tokens and hoh.usage.calls exactly for all four recordings",
    "the single failure shape was checked over all 38 turns for finish_reason, presence of tool_calls, content type and length, fenced blocks, and embedded JSON",
    "the root cause was checked against the mechanism: mini's check_finished (first output line + returncode 0), the harness's ApiMode::ToolCalls, and the absence of any bash command mentioning the marker in all four recordings",
    "the fix's command was executed in a real LocalEnvironment by the new test and had to produce InterruptKind::Submitted",
    "the whole gate, the untouched-tree baseline, fmt, and both --list forms were run in this batch's own build directory"
  ],
  "could_not_verify": [
    "that a live Developer call now issues the command instead of the prose.  No round and no model call were run, so the after column is a projection from the recordings — the same limitation the frozen spike records about every one of its levers.",
    "that the role ends the call at the first moment it believes it is finished.  Its recorded prose says so, but the fix also makes that intent *executable*, and only a live call can show whether the role takes it.  This is the largest single effect and it is unmeasured.",
    "that the same defect is absent in the Planner and the Tester.  Only Developer trajectories are in the corpus; the Planner/Tester prompts carried a 'a reply with no tool call is not a legal end either' sentence the Developer prompt did not, but the corpus cannot show whether they retried."
  ],
  "single_most_important_thing": "A retry fix is a *prompt* fix here, and its measured half is small while its unmeasured half is large: the rejected turns cost 876,566 / 1,486,702 / 416,910 prompt tokens (34.4% / 11.6% / 8.1%) and the history cascade they leave costs 889,649 / 1,494,510 / 428,655, but each recording's FIRST rejected turn is at call 25 / 58 / 30 of 69 / 125 / 102 — so if a live Developer now runs `echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT` where it previously wrote prose, the call ends there and the real saving is the tail (1,964,960 / 9,812,332 / 4,059,147 prompt tokens), not the retry turns.  The next batch must measure that live, and must watch for the risk it carries: the Developer prompt always intended the role to decide when it is finished, and making that decision executable could end Developer calls earlier with weaker artifacts."
}
```

# RETRY-FIX-REPORT — the Developer format-error retry, its cause, and its removal at the source

**Scope.** Offline work over files that already exist: `evidence/cost/*.developer.attempt1.json`, the
prompts under `src/prompts/`, the render path in `src/runtime/invoke.rs`, and the mini-swe-agent crate
at `F:/RustProjects/mini-swe-agent-rust-mini` (read only). **No round was run, no model call was made,
no engine was started, no network was used.** Nothing under `evidence/**`, `runs/**`, `config/**`, the
registry, the battery, the liveness step, `.gitattributes` or any frozen document was touched. Six
files changed, all listed in the gate block above. Nothing was committed or pushed. The helper scripts
live outside the repository at `F:/retry-fix/`.

## 1. The failure, reproduced from the recordings

There is **one** shape, and it is the same shape in all 38 retry turns of the three unfolded
recordings:

| | value | how it was checked |
|---|---|---|
| `finish_reason` | `"stop"` | every `choices[0].finish_reason` of every retry turn |
| `message.tool_calls` | `null` | the key is absent — not an empty array |
| `message.content` | a non-empty list of `{type:"text"}` parts, 1,431–2,969 characters | all 38 |
| quoted `COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT` | 29 of 38 | substring of the prose body |
| fenced blocks / embedded `"command"` JSON | 0 of 38 | checked explicitly, so "the model wrote the call as text" is ruled out |

The validation that rejected it is mini's `parse_toolcall_actions`
(`mini-swe-agent-rust-mini/rust/src/models/mod.rs:139-153`), reached because
`src/harness/mini.rs` builds the model in `ApiMode::ToolCalls`. The rejection text is verbatim:

> `No tool calls found in the response. Every response MUST include at least one tool call.`

and it is delivered to the role as a `user` message with `interrupt_type: "FormatError"`.

The literal shape, from `round4-iter-1` message index 61 — the model's entire response is a report
whose last lines are:

```
… Live-game observation is left to the Tester and the deterministic battery, which run after my
call on this frozen candidate; I could not confirm the running session itself, as it was started
before these edits.

COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT
```

with `tool_calls: null`. Message index 58 ends `… all six of my physics/level unit tests pass.` and
cites the marker earlier in the same paragraph; 71 cites it mid-sentence. Every one of them opens
"Iteration 1 complete.", "Everything is verified. Final state:", "I'm done. Final state verified:" —
the report a role writes when it believes the call is over.

**What I fixed and what I left.** I fixed the whole class: all 38 turns. 29 of them name the marker
and are therefore directly explained by the prompt's wording; the other 9 are the identical report
without the marker, and what reaches them is the second half of the fix (the positive requirement
that a response carry a tool call), not the command spelling. There is no shape I am leaving.

## 2. The test that fails, then passes

`tests/prompt_shell_contract.rs`, two tests, both red before any production edit:

```
$ cargo test --offline --test prompt_shell_contract        # RED
test result: FAILED. 5 passed; 2 failed; 0 ignored; 0 measured; 0 filtered out
literal exit code: 101

 - every_role_prompt_states_that_a_reply_needs_a_tool_call
     panicked at tests\prompt_shell_contract.rs:484:
     planner.md does not state the positive output requirement: with no tool call the reply is
     rejected as a format error, and the recorded developer calls paid for that
     (20/10/8 turns over the three unfolded recordings)

 - the_documented_completion_command_really_ends_a_role_call
     panicked at tests\prompt_shell_contract.rs:464:
     planner.md names `COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT` only in prose: it documents no
     executable command whose output starts with the marker …
```

Neither failure is a compile or setup error: the same invocation compiled and ran five other tests
green, and the second test's helper is a deliberate panic naming the missing command.

```
$ cargo test --offline --test prompt_shell_contract        # GREEN
test result: ok. 7 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out
literal exit code: 0
```

The second test is the one that matters. It does not assert a string: it lifts the command out of
each **delivered** prompt, executes it in a real `LocalEnvironment`, and requires the
`InterruptKind::Submitted` flow interrupt — the same interrupt `run_compacting_agent` turns into
`exit_status: "Submitted"` and a clean end of the call. The existing
`only_a_first_line_completion_protocol_ends_a_role_call` keeps the mechanism pinned, and its control
(a command that merely looks like work is not a legal end) is untouched.

## 3. The change, and the alternative I rejected

The three prompts said *"end your run with the completion protocol
`COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT`"* and never said **run this command**. The marker exits a
call only as the first line of a command's output
(`mini-swe-agent-rust-mini/rust/src/environments/local.rs:118-128`), and under `ApiMode::ToolCalls`
a reply with no tool call is a format error. A role that obeyed the prompt literally produced the
rejected shape **every time it believed it was finished** — and never once ran the marker
(`0/4` recordings contain any bash command mentioning it).

I chose the smallest repair that addresses the instruction rather than the symptom: one shared
`[completion]` section, delivered through a new `{{completion_protocol}}` placeholder substituted in
`render_prompt_for_shell` — the single path every delivered prompt takes — stating (a) that **every
response must carry at least one tool call**, prose only *with* one; (b) that the only legal exit is
a command whose first line of output is the marker with exit code 0; and (c) the command itself, in a
fenced block: `echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT`. A placeholder rather than three copies
follows the file's own stated reason for `{{shell_truth}}`: the three prompts must not drift apart in
the instruction that decides whether their calls end or retry.

**The alternative I rejected** was to *repair the response instead of discarding it*: when a
prose-only reply ends with the marker, synthesise the `echo` action — or treat it as the `Submitted`
interrupt — rather than returning `AgentError::Format`. I rejected it on three grounds, and the first
is the decisive one: it **is** the validation that protects the pipeline. Accepting a no-tool-call
reply as an action means any prose-only reply becomes an action, and 9 of the recorded 38 carry no
marker at all. Second, the only interception point is `parse_actions` inside an external path
dependency outside this repository's branch discipline. Third, the defect is in the instruction, not
in the model's obedience — the recorded role did what its prompt said.

**Nothing that matters was weakened.** `parse_toolcall_actions`, the format-error template,
`max_consecutive_format_errors`, the guard and every fail-fast path are untouched; the mini crate was
not modified; no existing test was removed, renamed or relaxed.

## 4. What I measured, and what I could only project

From the recordings, per call, using each call's own `extra.response.usage` (the reconstruction
reproduces `hoh.usage` exactly for all four recordings):

| recording | calls | prompt tokens | retry turns before | prompt tokens at those turns | share | marker-quoting | retry turns after |
|---|---|---|---|---|---|---|---|
| round4-iter-1 | 69 | 2,544,563 | **20** | **876,566** | 34.45 % | 17 | **0** |
| round4-iter-2 | 125 | 12,765,478 | **10** | **1,486,702** | 11.65 % | 7 | **0** |
| round4-iter-3 | 102 | 5,137,090 | **8** | **416,910** | 8.12 % | 5 | **0** |
| livecost1-iter-1 | 150 | 3,537,843 | 0 | 0 | 0 % | 0 | 0 |

This reproduces the frozen spike's lever-4 figures exactly (20/10/8/0 and
876,566 / 1,486,702 / 416,910).

I want to be precise about what those numbers do **not** say, because it would be easy to oversell
them. Under the fix the role still makes **one turn** at each of those moments; before, that turn was
rejected and billed, after, the same turn runs the documented command. So the 876,566 / 1,486,702 /
416,910 tokens are **not saved** — they move from "a rejected turn" to "the legal completion turn".
What stops being spent is the `FormatError` history message each rejected turn inserted and every
later call re-sent: **889,649 / 1,494,510 / 428,655** tokens, projected at each recording's own
tokens-per-wire-byte ratio.

The larger term is a direction I cannot quantify offline. Each recording's *first* rejected turn is
at call **25 / 58 / 30** of 69 / 125 / 102, and the prose at that moment says the role is finished. If
a live role runs the command there, the call ends immediately — `exit_status: "Submitted"`, which
`is_failure_status()` does not treat as a failure — and every later call disappears. Calls 25..69 /
58..125 / 30..102 alone are **1,964,960 / 9,812,332 / 4,059,147** prompt tokens. That is the number
worth having, and it is the one that needs a live Developer call. No round and no model call were run
here, so I report it as the direction of the change, not as a measurement.

## 5. The gate

| check | command | literal exit code | result |
|---|---|---|---|
| gate | `cargo test --offline` | **0** | 802 passed / 0 failed / 6 ignored / 808 listed, 60 test-result lines, 0 compiler warnings |
| baseline, untouched tree, same build dir | `cargo test --offline` | **0** | 800 passed / 0 failed / 6 ignored / 806 listed, 60 test-result lines, 0 compiler warnings |
| fmt | `cargo fmt --all --check` | **0** | 0 bytes of output |
| list | `cargo test --offline -- --list` | **0** | 808 listed |
| list ignored | `cargo test --offline -- --list --ignored` | **0** | 6 ignored |

The delta is exactly the two new tests. Nothing failed on a timing-sensitive test, so there is no
flake to report. Because this reporting change itself adds files under `.spec/bevy/` — which several
tests scan — the gate was run a **second** time after `DECISIONS.md` and this report were written:
exit **0**, 802 / 0 / 6 / 808, 0 compiler warnings, and the per-target counts byte-identical to the
first run; only the `finished in …` timings differ. Disk was checked before building: `F:` had 9.1 G
free and 100 % used, so this batch built in its own directory on `D:` (82 G free) —
`D:/retry-fix-target`, one test process at a time.

## 6. What I verified, what I could not, and the one thing that matters next

**Verified myself.** Every before-figure is read out of the committed recordings, and the
reconstruction reproduces `hoh.usage` exactly for all four. The single failure shape was checked
across all 38 turns for finish reason, tool-call presence, content type and length, fenced blocks and
embedded JSON. The root cause was checked against the real mechanism — `check_finished`, the
harness's `ApiMode::ToolCalls`, and the absence of any marker command in every recorded tool call.
The fix's command is *executed* by the new test in a real `LocalEnvironment`. The gate, the
untouched-tree baseline, fmt and both `--list` forms were run here.

**Not verified.** That a live Developer call now issues the command instead of the prose — the after
column is a projection, exactly as every lever in the frozen spike is. That the role ends the call at
the first moment it believes it is finished: its recorded prose says so, but only a live call can
show it, and that is the largest single effect. And whether the Planner and the Tester retried the
same way: only Developer trajectories are in the corpus, though their prompts did carry the "a reply
with no tool call is not a legal end either" sentence the Developer prompt lacked.

**The single most important thing for the next batch.** This retry fix is a prompt fix, and it is
**not yet a cost measurement** — it is a cost *hypothesis with a measured trigger*. The measured half
(876,566 / 1,486,702 / 416,910 tokens of rejected turns, plus 889,649 / 1,494,510 / 428,655 of cascade)
is small; the unmeasured half (1,964,960 / 9,812,332 / 4,059,147 tokens of tail beyond the first
rejected turn) is where the criterion is won or lost. Measure it with a live Developer call, and watch
the risk it carries: the Developer prompt always intended the role to decide when it is finished, and
making that decision executable could end Developer calls earlier with weaker artifacts. The round
result already has the fields to catch that — `exit_status: "Submitted"`, the artifact write, and
`artifact_valid` — so the live experiment should read those, not just the token total.
