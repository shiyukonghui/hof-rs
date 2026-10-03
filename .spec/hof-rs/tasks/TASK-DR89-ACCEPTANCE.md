# TASK-DR89-ACCEPTANCE - independent acceptance of the DR-89 batch

```json
{
  "task": "TASK-DR89-ACCEPTANCE",
  "kind": "independent acceptance of the DR-89 batch; offline - no engine started/driven, no round run, no network, nothing staged/committed/pushed, nothing written under runs/** or any workspace directory",
  "acceptance_time": "2026-10-03 21:22-22:35 (+0800)",
  "reviewed_batch_commit": "8b69db3ba898c40bff59dce7b02fce3760837579",
  "reviewed_batch_parent": "3c0cdf7f670122aad5efdfaf0b4379e45cbcc764",
  "tree_head_when_report_written": "50747c155e75473f41c6c230f26ab908bb62f02e",
  "origin_master": "55a075194505e0f4a6d3e913a41e29880ea302e4",
  "verdict": "fail",
  "verdict_scope": "The dispatched work is substantially real and largely reproduced by me independently: the truncation regression is fixed without the per-line delimiter scan (all report numbers reproduce on my own three-point probe, B2/B3/B3b/B5/B5b/C25/C26/C27 0/0/1 and C1 1/1/0), the false justification is gone and the pin transcribes the frozen lines byte-exactly, the workspace residual is declared with its reasoning, the criteria annotation is a pure append (26,491-byte prefix byte-identical, seal 20,910 B / 7b551ca0... unmoved), and four of my own plants (P4/P5/P6/P7) redden and restore byte-identically. The verdict is fail on one measured regression that the batch introduced and did not declare: the new 'a literal still open at the end of the text' rule does not honour the text-resource reader's own line comment, so a legitimate .tscn/.tres file whose ';' comment contains an apostrophe or a single quote is now reported as artifact_write_truncated (measured 0 at ab95c65, 0 at 52d73d3, 1 at 8b69db3). That is the exact failure mode integrity.rs says a gate check must never have - a false red on a document the engine accepts. A second, pre-existing false positive of the same shape (a delimiter inside a ';' comment) is measured at all three revisions and is not the batch's doing. Separately, my own full-gate run was killed by the session boundary at 46 of 62 suites and I did not restart it, so the literal cargo test exit code and the 648-passed reading are not independently reproduced; everything else in the gate that can be read from the completed raw logs is consistent.",
  "criteria": [
    {
      "id": "C1-three-point-regression",
      "pass": true,
      "evidence": "My own probe (tests/zzz_probe89.rs, out-of-repo copies of the three revisions, one isolated CARGO_TARGET_DIR each, all three probe runs exit 0) reproduces every number in TASK-DR89-REPORT.md section 2.1 exactly: B2 1/0/1, B3 1/0/1, B3b 0/0/1, B5 1/0/1, B5b 1/0/1, C25 0/0/1, C26 0/0/1, C27 0/0/1, C1 1/1/0, L2 1/0/0, L3 1/0/0, L9 1/0/0, N1 1/0/0, X3 0/1/1, X4/X6/X7/X10 1/1/1, X9 0/1/1, B1 1/1/2 (artifact_write_truncated@1 + artifact_shell_residue@2), B7 0/0/0, B8 0/0/0, D4 1/1/1, R1 1/1/1. Kinds and lines match the report too (B2 trunc@1, B3 trunc@2, B5/B5b trunc@2, C25/C26/C27 trunc@1). Stale-binary discriminators are asserted: L2 parent must be 1 (it is) and DR-88/DR-89 must be 0 (they are), C25 parent must be 0 and DR-89 1 (it is); the three raw logs are not byte-identical."
    },
    {
      "id": "C2-own-truncation-cases",
      "pass": true,
      "evidence": "Twelve of my own truncation shapes (none on the report's list) are all caught at 8b69db3 and all read 0 at ab95c65 and 52d73d3: M1 raw literal left open with a tail (trunc@2); M2 scene cut inside a quoted value (trunc@3); M3 two opens one close (trunc@1); M4 final line only whitespace (trunc@1); M5 single-quoted literal left open (trunc@1); M6 blank final line (trunc@1); M7 raw triple left open (trunc@1); M8 .tres cut inside a quoted value (trunc@2); M9 comment then an open literal (trunc@2); M10 no trailing newline at EOF (trunc@1); M11 backslash at EOF inside a string (trunc@1); M12 a triple with only two closing quotes (trunc@1)."
    },
    {
      "id": "C3-previous-false-positives-still-clean",
      "pass": true,
      "evidence": "The three false positives DR-88 existed to remove are still 0 at 8b69db3 under my own probe: L2 (r\"C:\\Users\\dev\\project\") 1/0/0, L3 (\"\\U0001F600\") 1/0/0, L9 (raw triple with \\d/\\U/#) 1/0/0. My own legitimate examples are also clean: G1 (apostrophe + Windows path in a .gd comment) 0; G4 (two quotes in a ';' comment) 0; G6 (apostrophe inside a .tscn string) 0; G7 (escaped quote then # inside a string) 0; G8 (code line-continuation backslash) 0; G9 (single-quoted string holding a double quote) 0; G10 (\\r escape) 0; G12 (triple-quoted with # and ')' inside) 0; G13 (unpaired quote in a .gd comment) 0; G14 (\\u0041) 0; G11 (legitimate .tscn multi-line string holding ')') 1 at the parent, 0 at DR-88 and DR-89. The one exception is the new ';'-comment shape, reported as DR89A-1."
    },
    {
      "id": "C4-new-semicolon-comment-false-positive",
      "pass": false,
      "evidence": "Measured 0/0/1 with my own probe. A legitimate text resource whose ';' comment contains an apostrophe or one quote is reported as artifact_write_truncated at 8b69db3 only: G3 [gd_scene format=3] / '; don't touch' / [node ...] -> 1 (trunc@2); G2 the .tres twin -> 1 (trunc@2); N2 '; see \"unclosed in a comment' -> 1 (trunc@2); N4 '; don't call foo(bar' -> 1 (trunc@2). Controls G3-like without a quote (N3 plain ';' comment) and N6 (two apostrophes, which happen to pair) read 0. The engine accepts these documents: VariantParser::get_token treats ';' as a line comment (godot-mcp/godot/core/variant/variant_parser.cpp:215-229) and parse_tag_assign_eof does the same at :1787-1799, and .tscn/.tres are parsed through VariantParser (godot-mcp/godot/scene/resources/resource_format_text.cpp:518, :625, :755). The audit's scan_line knows only '#' as a comment for every audited extension, so the apostrophe opens a literal that is carried to the end of the text and is reported as a fragment."
    },
    {
      "id": "C5-pre-existing-semicolon-delimiter-false-positive",
      "pass": false,
      "evidence": "Measured 1/1/1: G5 '[gd_scene format=3] / ; see foo(bar / [node ...]' is reported as artifact_write_truncated@3 at ab95c65, 52d73d3 and 8b69db3. The '(' is inside the reader's line comment, so the balance rule's reading is wrong at every revision - it is a pre-existing defect of the balance rule, not a DR-89 regression. Same root cause as DR89A-1 (the audit does not model ';')."
    },
    {
      "id": "C6-rejected-road-per-line-scan",
      "pass": true,
      "evidence": "The claim is source-backed and reproduced. core/variant/variant_parser.cpp:277-296 - the string branch loops on get_char() and errors only on ch == 0 (or on '\\'+0), breaking on '\"'; a newline is ordinary content. The stream is a raw byte stream (StreamFile::_read_buffer :74-89 reads through f->get_buffer with no line split). So a per-line delimiter scan would red a legitimate multi-line resource string, and it did: N1 and G11 (a .tscn string opened on one line and closed on a later one, holding ')') both read 1 at the parent ab95c65, which had the per-line scan, and 0 at 52d73d3 and 8b69db3. Declining the per-line road was right."
    },
    {
      "id": "C7-corrected-justification",
      "pass": true,
      "evidence": "Frozen artifact runs/smoke-t16/iter-1/candidate/scripts/main.gd is 1,192 bytes, pure LF; lines 8-12 are five '@onready var ... = \\$HUD/...' expressions, each with exactly one '\\$' and no '\"' or \"'\" on the line (checked byte by byte). The new pin runtime::integrity::tests::the_round_of_records_residues_are_unquoted_expressions transcribes those five lines and my script confirms each transcribed string equals the artifact line byte-for-byte. The false assertion is gone from src/runtime/integrity.rs (the module doc now states explicitly that the residues did NOT land inside string literals) and from the test comment (the in-string probe is now an actually quoted 'var label = \"\\$HUD/Coins\"'). In TASK-DR88-REPORT.md the false sentence survives only as the verbatim quotation the correction is about, labelled false; no file anywhere still asserts it."
    },
    {
      "id": "C8-workspace-residual-declared",
      "pass": true,
      "evidence": "Declared with its reasoning, not silently dropped: TASK-DR89-REPORT.md section 4 names the half DR-88 left out (the same configured cache excludes stay unwatched on the real workspace side), gives the reason not to extend the watch (the workspace has a non-role writer, the user's long-running editor, D294), and states the consequence for E5. It is repeated in the report's residual table (section 11.3, DR88A-3) and in the appended REQUIREMENTS annotation. I confirmed the reasoning's factual half myself: .workspace/** holds 851 files with newest mtime 2026-10-03T16:44:24 (.workspace/fresh-t16/.godot/scene_groups_cache.cfg), hours before the batch's first write, and runs/** is untouched (7,341 files, newest 2026-10-03T05:47:27)."
    },
    {
      "id": "C9-criteria-annotation-is-a-pure-append",
      "pass": true,
      "evidence": "Measured from the bytes: REQUIREMENTS.md is 28,690 B / sha256 4982bf1c...; the revision before the batch (3c0cdf7:.spec/hof-rs/REQUIREMENTS.md) is 26,491 B / sha256 298a9489... and is byte-identical to the current file's first 26,491 bytes, so the annotation is 2,199 appended bytes and nothing above it moved. The DR-80 seal still reads offset 20,910 with prefix sha256 7b551ca08c4c5abf15a95cb8edcc4977ce8d03c649654ab4a5ab01f649cae5ae (the pinned value), the E5 row is still at offset 12,619 inside the sealed prefix, and the DR-89 heading owns a whole line at offset 26,492 after the seal. The new pin is load-bearing on the real bytes: my plant P7 flipped one byte at offset 100 of a copy's REQUIREMENTS.md and the test went 0 -> 101, restored byte-identically (sha back to 4982bf1c...), control 0."
    },
    {
      "id": "C10a-gate-list-format-removal-ignored-rebuild",
      "pass": true,
      "evidence": "From the raw logs of my own gate run in the repository: after clearing 63 printed target/debug/.fingerprint/hof-rs-* directories and touching 101 tracked .rs files individually, cargo test --offline -- --list wrote 655 test entries and 0 benches, contains 'Compiling hof-rs' (forced rebuild proven: the wrap-up says '0 tests, 0 benchmarks' with no error line), against the baseline 3c0cdf7's own list of 651. Name-set diff over the two --list logs: REMOVED = [] and ADDED = exactly the four tests the report lists (an_unterminated_literal_is_a_fragment_not_a_whole_document, a_lone_carriage_return_after_a_backslash_is_the_languages_own_escape, the_round_of_records_residues_are_unquoted_expressions, the_requirements_e5_row_carries_its_dr89_annotation_and_the_seal_still_holds). Line-start #[ignore] attributes: 7 in the current tree and 7 at 3c0cdf7, both over 101 tracked .rs files. cargo fmt --all --check exit 0 with no output. 655 = 648 passed + 7 ignored is consistent."
    },
    {
      "id": "C10b-gate-full-run-literal-exit-code",
      "pass": false,
      "evidence": "NOT reproduced. My own full `cargo test --offline` in the repository was killed by the session boundary after 46 of 62 suites (raw log ends inside tests/round_game_window.rs at 2026-10-03T21:55:22); the parent process died before it could record subprocess.returncode, so I hold no literal exit code and no complete passed count. On the 46 suites that did finish: 551 passed / 0 failed / 7 ignored / 0 red suites. The 14 integration targets never reached are runtime_semantics, schema_gate, secret_hygiene, secret_isolation, snapshot_rollback, start_state, tool_discovery, tool_output_ceiling, tool_parameter_contract, tool_vocabulary, tools_policy, usage_extraction, wrap_up_budget, write_integrity. I did not restart the run (the dispatcher instructed me not to start a new long test run), so the DR-89 report's literal exit 0 / 648 passed stays a lead, not evidence I produced."
    },
    {
      "id": "C11-nothing-weakened-no-forbidden-zone",
      "pass": true,
      "evidence": "The batch commit 8b69db3 changes exactly 5 files (its own report, src/runtime/integrity.rs, tests/append_only_guard.rs, .spec/hof-rs/REQUIREMENTS.md, .spec/hof-rs/tasks/TASK-DR88-REPORT.md) - no criterion, jump rule, artifact-gate classification or rejecting semantics file is among them. Hashes measured now, all unchanged: PRD-mario.md 4c81c3a99..., Cargo.toml e0c4992b..., Cargo.lock d98fa915... (no dependency added), config/hoh.yaml 835b6b0e..., src/adapter/godot.rs 27fda15a..., DECISIONS.md 9f95f26e... / 1,243,889 B. The engine tree godot-mcp/godot is at fc63af77... with git status --porcelain empty (0 bytes). runs/** (7,341 files, newest 05:47:27) and .workspace/** (851 files, newest 16:44:24) predate the batch. git status --porcelain shows only the four pre-existing untracked leftovers l.json/p2.json/pv.json/r.json; origin/master is still 55a0751 (ahead 14, nothing pushed). Inside the repository I only cleared gitignored target fingerprints, touched .rs mtimes and wrote this report."
    },
    {
      "id": "C12-plants",
      "pass": true,
      "evidence": "Four plants re-run by me on the out-of-repo copy of 8b69db3, each with a byte assert before planting, one literal substitution, an explicitly bumped mtime, a proof that cargo recompiled hof-rs in the run under test, and a byte-exact restore: P4 unterminated_literal(text) -> None::<(usize, OpenString)>: 0 / 101 / restore identical (9b203999...) / 0; P5 remove the CR entry from GDSCRIPT_ESCAPES: 0 / 101 / 9b203999... / 0; P6 if index + 1 < count -> && chars[index + 1] != '$': 0 / 101 / 9b203999... / 0; P7 flip byte 100 of REQUIREMENTS.md: 0 / 101 / 4982bf1c... / 0. PLANTS THAT DID NOT BEHAVE: []. My first driver read P4 as 'planted 0' and skipped P5 on a bad needle; that was my own stale-mtime trap (I set the mtime to a value captured before the control compile), recorded here rather than hidden."
    },
    {
      "id": "C13-machine-block-parses-and-round-trips",
      "pass": true,
      "evidence": "The T16 round report's line-anchored json block (.spec/hof-rs/tasks/TASK-SMOKE-T16-REPORT.md) extracts to 25,686 bytes / sha256 06af46d5dfb05cf3c867b1c52a3828fd48ef5a254e894134c202c485b210b0ad (the pinned value), parses with json.loads, and json.dumps(obj, ensure_ascii=False, indent=2) reproduces the 25,685 content bytes exactly, equal on parse-back. The T16 seal is unmoved: prefix 77,319 B / sha256 ee9d175da22f7cf18c31570e31c4dfd807f3afaed7ccc0faf634e0b31381c6f9, both matching tests/append_only_guard.rs."
    },
    {
      "id": "C14-residual-list-adjudicated-measured-vs-inferred",
      "pass": true,
      "evidence": "The report's residual split is honest. Measured by me: the three-point regression and its restorations, the false positives and tightenings, the CR closure, the annotation seal, the four plants, the latter's tool accident, and the .workspace non-role-writer reading. Correctly labelled inferred: real-round behaviour (no engine), whether a legitimate cache rebuild would be rejected, whether the new fragment findings ever fire on real products, hex-digit-run fidelity against the real tokenizer, and whether a workspace-cache write ever happens. The report itself closes DR88A-1/2/4/5 and declares DR88A-3; I agree with all five classifications. Its DR87A-6 reading (63 fingerprints) I reproduce as 63 here."
    }
  ],
  "defects": [
    {
      "id": "DR89A-1",
      "severity": "medium",
      "what": "The new unterminated-literal rule does not honour the text-resource reader's own line comment. scan_line treats '#' as the only comment for every audited extension, while .tscn/.tres use ';' (VariantParser::get_token :215, parse_tag_assign_eof :1787). So a legitimate resource whose ';' comment contains an apostrophe or a single quote opens a phantom literal that is carried to the end of the text, and the document is reported as artifact_write_truncated. This is a false red on a document the engine accepts - the failure mode integrity.rs:36 says a gate check must never have. The batch introduced it: 0 at ab95c65, 0 at 52d73d3, 1 at 8b69db3, and it is not in the report's residual list.",
      "reproduction": "My probe tests/zzz_probe89.rs against the production audit_text on out-of-repo copies of ab95c65/52d73d3/8b69db3. Case G3: audit_text(\"scenes/s.tscn\", \"[gd_scene format=3]\\n; don't touch\\n[node name=\\\"Main\\\" type=\\\"Node2D\\\"]\\n\") = 0/0/1 (1 artifact_write_truncated at line 2 at 8b69db3). Case G2 (.tres twin) 0/0/1; N2 ('; see \"unclosed in a comment') 0/0/1; N4 ('; don't call foo(bar') 0/0/1. Controls N3 (plain ';' comment) 0/0/0 and N6 (two apostrophes) 0/0/0. Engine side: godot-mcp/godot/core/variant/variant_parser.cpp:215-229 and :1787-1799 skip ';' to end of line; godot-mcp/godot/scene/resources/resource_format_text.cpp:518/:625/:755 parse scenes through VariantParser."
    },
    {
      "id": "DR89A-2",
      "severity": "low",
      "what": "Pre-existing, same root cause, not introduced by DR-89: the delimiter-balance rule counts an opener inside a ';' comment as code. A legitimate text resource with '; see foo(bar' is reported as artifact_write_truncated.",
      "reproduction": "Case G5: audit_text(\"scenes/s.tscn\", \"[gd_scene format=3]\\n; see foo(bar\\n[node name=\\\"Main\\\" type=\\\"Node2D\\\"]\\n\") = 1/1/1 (artifact_write_truncated@3) at ab95c65, 52d73d3 and 8b69db3. The '(' is inside the reader's line comment (variant_parser.cpp:1787)."
    },
    {
      "id": "DR89A-3",
      "severity": "low",
      "what": "Process note, declared by the batch rather than hidden: TASK-DR88-REPORT.md - a historical report - was corrected by replacing one line in place instead of appending (git diff 52d73d3 8b69db3 -- that file is +1/-1). D289 says a correction to a historical report may only be appended. Mitigations: the DR-88 acceptance had itself advised deleting that clause, the false sentence survives as a verbatim quotation above the correction, the file carries no seal/pin, and TASK-DR89-REPORT.md section 3 declares the edit.",
      "reproduction": "cd F:\\moonbit-hof-rs && git diff 52d73d3 8b69db3 -- .spec/hof-rs/tasks/TASK-DR88-REPORT.md"
    }
  ],
  "risks": [
    "The gate is only half-reproduced by me (C10b): the literal exit code and the 648-passed reading are the report's, not mine. A re-run, or a run of the 14 named targets, is cheap and should close it.",
    "The ';'-comment defect means the new rule can refuse a project with no defect whenever a delivered .tscn/.tres carries a comment with a quote or an apostrophe. Engine-written scenes do not comment, so the likelihood is low, but the consequence is a false red and the class is exactly the one the module promises never to produce.",
    "The audit models '#' as a comment in .tscn/.tres, where the reader treats '#' as a colour token. No legitimate document is red by this today (a '#' outside a string is a parse error in a resource), but the divergence should be named if ';' is fixed.",
    "HEAD moved during the acceptance: 50747c1 (docs(bevy): add the product requirements) landed after 8b69db3 and adds only .spec/bevy/PRD.md. I verified the whole DR-89 surface (integrity.rs, append_only_guard.rs, REQUIREMENTS.md, both reports) is byte-identical at 8b69db3 and at HEAD, so the acceptance still binds; but an acceptance should not run over a moving tree.",
    "My gate cleared 63 gitignored target/debug/.fingerprint/hof-rs-* directories and touched 101 tracked .rs mtimes inside the repository; no content and no tracked status changed (git status is the four pre-existing untracked leftovers)."
  ],
  "unverified": [
    "The literal `cargo test --offline` exit code and the complete passed/failed/ignored counts: my own full run was killed at 46/62 suites (551 passed / 0 failed / 7 ignored / 0 red) and I did not restart it. The 14 unreached targets are listed under C10b.",
    "Any engine-side behaviour: no engine was started, restarted, driven or run; the ';'-comment argument rests on the engine's source (variant_parser.cpp, resource_format_text.cpp), not on a running interpreter.",
    "The #[ignore]d real-engine tests (7) and any hardware round: not runnable offline.",
    "Whether a real editor start rebuilds .godot inside the candidate view: inferred from the mechanism, not observed.",
    "The batch's own session logs (gate raw logs, plant log): I reproduced my own measurements instead.",
    "Whether a malformed \\u inside a .tscn string (declared in the batch) ever appears in a real product: source-backed only."
  ],
  "what_i_did_not_check": [
    "No round, no engine, no network, nothing staged/committed/pushed.",
    "I modified no report, no frozen specification, no DECISIONS.md and nothing under godot-mcp/**. Inside the repository I only cleared gitignored target fingerprints, touched .rs mtimes, and wrote this file.",
    "The DR-87 acceptance's other claims and anything under godot-mcp/** beyond gdscript_tokenizer.cpp, variant_parser.cpp and resource_format_text.cpp.",
    "The #[ignore]d real-engine tests, the MCP server module, and the tool-discovery surface."
  ],
  "advice_for_the_next_batch": [
    "Honour the text-resource reader's own line comment: give scan_line (or its caller) the per-extension comment rule, so ';' starts a comment in .tscn/.tres exactly as '#' does in .gd (VariantParser::get_token :215, parse_tag_assign_eof :1787). That closes both DR89A-1 (the apostrophe/quote false red, now measured 0/0/1) and DR89A-2 (the delimiter false red, 1/1/1) with one rule, while keeping every truncation finding this batch restored - pin it with a .tscn and a .tres case whose ';' comment holds an apostrophe, a lone quote and an unmatched '(', and with the converse that a quote in a ';' comment no longer swallows a real fragment behind it.",
    "Do not revert the carried-literal design to a per-line delimiter scan: the reader accepts a newline inside a resource string (variant_parser.cpp:277-296), and the parent's per-line scan measurably redded a legitimate multi-line .tscn string holding ')' (my N1/G11 = 1 at ab95c65, 0 since).",
    "Close the gate yourself in one clean run and publish the literal exit code taken with no second test process running; if the time budget is short, the 14 unreached targets named in C10b are the only ones missing.",
    "Keep the four new pins (P4/P5/P6/P7) as the batch left them - all four redden their own test and restore byte-identically - and keep setting the mtime forward, not backward, after a plant/restore (a backward mtime made my first driver read a planted run as green).",
    "Record the ';' fix as a new decision entry with the engine citations, and note in TASK-DR88-REPORT.md's neighbourhood that its one-line in-place correction (DR89A-3) is the deliberate exception the DR-88 acceptance asked for."
  ]
}
```

## 0. Role, revision and scope

- **Fresh, independent acceptance subagent.** No upstream conversation context, no inherited conclusion. `TASK-DR89-REPORT.md` was read as a lead only; every number below was re-measured by me.
- Reviewed batch: `8b69db3ba898c40bff59dce7b02fce3760837579` (parent `3c0cdf7f670122aad5efdfaf0b4379e45cbcc764`, `origin/master` still `55a075194505e0f4a6d3e913a41e29880ea302e4`, ahead 14, nothing pushed).
- **The tree moved under me mid-acceptance**: `50747c1 docs(bevy): add the product requirements ...` landed after the batch. It adds only `.spec/bevy/PRD.md`; I verified `git rev-parse 8b69db3:<f>` == `git rev-parse HEAD:<f>` for `src/runtime/integrity.rs`, `tests/append_only_guard.rs`, `.spec/hof-rs/REQUIREMENTS.md` and both reports, so the accepted surface is unchanged.
- **Offline**: no engine started/restarted/driven, no round, no network, nothing staged/committed/pushed, nothing written under `runs/**` or any workspace.
- My scratch, the three out-of-repo revision copies, the baseline copy, the probe, the plants and every log live under `C:\Users\wyl\AppData\Local\Temp\t16acc-dr89\`. No `rm -rf` anywhere (only Python `shutil.rmtree` on a printed, asserted path in the scratch), no `git checkout --`, no path built from an unexpanded variable, `os.utime` after every write/restore with a byte-equality assert.
- The machine block above was produced by `json.dumps(..., ensure_ascii=False, indent=2)`, `json.loads`-parsed back and compared equal **before** the file was written (assembly script `C:\Users\wyl\AppData\Local\Temp\t16acc-dr89\assemble.py`).

**Verdict: fail** - on one measured, undeclared regression (`DR89A-1`, a legitimate `.tscn`/`.tres` `;` comment containing a quote or apostrophe is now reported as `artifact_write_truncated`), plus the pre-existing `DR89A-2` of the same shape and one gate criterion I could not reproduce.

## 1. Per-item table

| # | Dispatched job | My independent reading | Verdict |
|---|---|---|---|
| 1 | **The regression (headline)** | Three-point probe on isolated copies of `ab95c65`/`52d73d3`/`8b69db3`: every number in report section 2.1 reproduced exactly (`B2 1/0/1`, `B3 1/0/1`, `B3b 0/0/1`, `B5 1/0/1`, `B5b 1/0/1`, `C25/C26/C27 0/0/1`, `C1 1/1/0`, `L2/L3/L9/N1 1/0/0`, `X3 0/1/1`, `X4/X6/X7/X10 1/1/1`, `X9 0/1/1`, `B1 1/1/2`, `B7/B8 0/0/0`, `D4 1/1/1`, `R1 1/1/1`). Twelve of my own truncation shapes all caught (`M1`-`M12`). Stale-binary discriminators asserted. | **Pass** |
| 2 | **The rejected road** | `variant_parser.cpp:277-296` has no newline terminator (`ch == 0` only) over a raw byte stream (`:74-89`); the parent's per-line scan redded a legitimate multi-line resource string holding `)` (`N1`/`G11` = 1 at `ab95c65`, 0 since). Declining per-line was right. | **Pass** |
| 3 | **The corrected justification** | Frozen `scripts/main.gd` lines 8-12 are five unquoted `\$` expressions (1,192 B, pure LF, no quote byte); the pin transcribes them byte-for-byte; the false assertion is gone from code, report and test comment (the report keeps it only as the labelled quotation). | **Pass** |
| 4 | **The declaration and the annotation** | Workspace residual declared with reasoning and consequence (report section 4, residual table, criteria note). Annotation is a pure append: prefix 26,491 B / `298a9489...` byte-identical, seal 20,910 B / `7b551ca0...` unmoved, DR-89 heading at 26,492, +2,199 B. Plant `P7` reddens the pin on the real bytes and restores byte-identically. | **Pass** |
| 5 | **The gate** | `--list` 655 vs baseline 651, `REMOVED=[]`/`ADDED=4` (exactly the listed four), `#[ignore]` 7 in both, `cargo fmt --all --check` exit 0, forced rebuild proven (`Compiling hof-rs` in the `--list` call after clearing 63 printed fingerprints and touching 101 tracked `.rs`). **But the full run was killed at 46/62 suites and I did not restart it**: no literal exit code, no complete count (partial: 551/0/7/0 red). | **Partial - C10a pass, C10b fail** |
| 6 | **Nothing weakened / forbidden zone** | Commit touches 5 files, none of them a criterion, jump rule, gate classification or rejecting-semantics file; `PRD-mario.md`, `Cargo.toml`/`Cargo.lock`, `config/hoh.yaml`, `src/adapter/godot.rs`, `DECISIONS.md` byte-unchanged (no dependency added); engine tree clean; `runs/**` and `.workspace/**` untouched; nothing pushed; T16 machine block parses and round-trips. | **Pass** |
| 7 | **My own plants** | `P4`/`P5`/`P6`/`P7`: control 0 / planted 101 / restore byte-identical / control 0, with `Compiling hof-rs` proof in every run. `PLANTS THAT DID NOT BEHAVE: []`. | **Pass** |

## 2. The three-point measurement I reproduced

Probe `tests/zzz_probe89.rs` calls the production `audit_text`; each revision is a `git archive` export to an out-of-repo directory with its **own** `CARGO_TARGET_DIR` (the shared-target trap the report itself records). `integrity.rs` in each copy is byte-identical to the commit blob. Discriminators: `L2` parent must be 1 and DR-88/DR-89 0 (they are), `C25` parent 0 and DR-89 1 (it is), and the three raw logs are not byte-identical.

| case | shape | `ab95c65` | `52d73d3` | `8b69db3` | DR-89 kind@line |
|---|---|---|---|---|---|
| **B2** | unterminated raw literal over a later `\q` | 1 | 0 | **1** | trunc@1 |
| **B3** | `.tscn` tail behind an unterminated quote | 1 | 0 | **1** | trunc@2 |
| **B3b** | `.tscn` `name = "abc` only | 0 | 0 | **1** | trunc@2 |
| **B5** | `.tres` tail behind an unterminated quote | 1 | 0 | **1** | trunc@2 |
| **B5b** | `.tres` `name = "x` + `name = 12, y)  ` | 1 | 0 | **1** | trunc@2 |
| **C25** | `.gd` cut inside a string | 0 | 0 | **1** | trunc@1 |
| **C26** | `.gd` cut inside a raw literal | 0 | 0 | **1** | trunc@1 |
| **C27** | `.gd` cut inside a triple literal | 0 | 0 | **1** | trunc@1 |
| **C1** | `\` + lone CR inside a string | 1 | 1 | **0** | - |
| **L2** | raw string Windows path | 1 | 0 | **0** | - |
| **L3** | legal `\U0001F600` | 1 | 0 | **0** | - |
| **L9** | raw triple with `\d`/`\U`/`#` | 1 | 0 | **0** | - |
| **N1** | legal `.tscn` multi-line string holding `)` | 1 | 0 | **0** | - |
| **X3** | `\uZZZZ` | 0 | 1 | **1** | shell@1 |
| **X4/X6/X7/X10** | foreign escape in strings | 1 | 1 | **1** | shell@1 |
| **X9** | continued string, next line `#` | 0 | 1 | **1** | shell@2 |
| **B1** | unterminated plain literal + later `\q` | 1 | 1 | **2** | trunc@1 + shell@2 |
| **B7/B8** | quotes/escapes in `.gd` comments | 0 | 0 | **0** | - |
| **D4** | `.tscn` comment apostrophe + unbalanced closer | 1 | 1 | **1** | trunc@3 |
| **R1** | one of the round's five lines | 1 | 1 | **1** | shell@1 |

## 3. My own plants and counterexamples

### 3.1 Truncation cases the report does not list (all caught at `8b69db3`, all 0 at both earlier revisions)

| id | shape | reading |
|---|---|---|
| M1 | `.gd` raw literal left open with a tail after it | trunc@2 |
| M2 | `.tscn` cut inside a quoted value | trunc@3 |
| M3 | two opens, one close (`"x" + "y`) | trunc@1 |
| M4 | final line only whitespace after an open literal | trunc@1 |
| M5 | single-quoted literal left open | trunc@1 |
| M6 | blank final line after an open literal | trunc@1 |
| M7 | raw triple left open | trunc@1 |
| M8 | `.tres` cut inside a quoted value | trunc@2 |
| M9 | comment, then an open literal on the next line | trunc@2 |
| M10 | no trailing newline at EOF | trunc@1 |
| M11 | backslash at EOF inside a string | trunc@1 |
| M12 | triple with only two closing quotes | trunc@1 |

### 3.2 Legitimate examples (the false-positive hunt)

Clean at all three revisions: `G1` apostrophe + `C:\Users\dev` in a `.gd` comment; `G4` two quotes in a `;` comment; `G6` apostrophe inside a `.tscn` string; `G7` `\"` then `#` inside a string; `G8` code line-continuation `\`; `G9` single-quoted string holding `"`; `G10` `\r` escape; `G12` triple-quoted with `#` and `)` inside; `G13` unpaired `"` in a `.gd` comment; `G14` `\u0041`; `N3` plain `;` comment; `N6` two apostrophes in a `;` comment.
False positive removed by DR-88 and still clean: `L2`/`L3`/`L9` and `G11` (multi-line resource string holding `)`), all 1 at the parent and 0 since.

**New false positive, introduced by this batch (DR89A-1), measured 0/0/1:**

| id | shape | `ab95c65` | `52d73d3` | `8b69db3` |
|---|---|---|---|---|
| G3 | `[gd_scene format=3]` / `; don't touch` / `[node ...]` | 0 | 0 | **1** (trunc@2) |
| G2 | `.tres` twin | 0 | 0 | **1** (trunc@2) |
| N2 | `; see "unclosed in a comment` | 0 | 0 | **1** (trunc@2) |
| N4 | `; don't call foo(bar` | 0 | 0 | **1** (trunc@2) |

**Pre-existing false positive (DR89A-2), measured 1/1/1:** `G5` `; see foo(bar` -> `trunc@3` at every revision (the `(` is inside the reader's line comment).

Why the engine accepts these: `VariantParser::get_token` skips `;` to end of line (`variant_parser.cpp:215-229`), `parse_tag_assign_eof` does the same (`:1787-1799`), and `.tscn`/`.tres` are parsed through `VariantParser` (`resource_format_text.cpp:518`, `:625`, `:755`). The audit's `scan_line` knows only `#`, so the apostrophe opens a phantom literal that is carried to EOF and reported as a fragment.

### 3.3 Plants

| plant | change (on the out-of-repo copy) | control -> planted -> restore -> control |
|---|---|---|
| P4 | `unterminated_literal(text)` -> `None::<(usize, OpenString)>` | 0 -> **101** -> identical (`9b203999...`) -> 0 |
| P5 | remove the CR entry from `GDSCRIPT_ESCAPES` | 0 -> **101** -> identical -> 0 |
| P6 | `if index + 1 < count {` -> `&& chars[index + 1] != '$'` | 0 -> **101** -> identical -> 0 |
| P7 | flip byte 100 of `REQUIREMENTS.md` | 0 -> **101** -> identical (`4982bf1c...`) -> 0 |

Every run printed `Compiling hof-rs`, so no stale binary. `PLANTS THAT DID NOT BEHAVE: []`.

## 4. Independent judgement

- **The regression is genuinely fixed, and by the right road.** The five lost findings are back, the never-reported `C25/C26/C27` are closed, and the per-line delimiter scan was correctly refused: it rests on a false premise about the resource reader (`variant_parser.cpp:277-296`) and measurably redded a legitimate multi-line `.tscn` string (`N1`/`G11`).
- **The corrected justification is now true.** The round's residues really are unquoted code; the pin is byte-exact; the false clause survives only as a labelled quotation. The language half of the argument (escapes are processed inside a non-raw literal) is what actually carries the decision, and it is source-backed.
- **The append discipline held where it mattered.** The criteria document grew by exactly 2,199 bytes with a byte-identical 26,491-byte prefix and an unmoved 20,910-byte seal; the new pin is load-bearing on the real bytes.
- **But the new rule is not comment-aware, and that is a real false red.** The module's own doc says a check must never refuse a project that has no defect; `; don't` in a `.tscn` now does exactly that. The batch's own tests never exercise a `;` comment, so the suite is green over it.
- **The gate's list/format/removal properties hold; its full-run count does not.** `655 = 648 + 7` is consistent with the report, the name-set diff shows no removal and exactly the four additions, `#[ignore]` is 7 in both revisions, and `fmt` is clean - but my own full run died at 46/62 suites and I have no literal exit code to publish.

## 5. What I could not verify

- The `cargo test --offline` literal exit code and the complete count (run killed at 46/62 suites, 551/0/7/0 red; not restarted on instruction). The 14 unreached targets: `runtime_semantics`, `schema_gate`, `secret_hygiene`, `secret_isolation`, `snapshot_rollback`, `start_state`, `tool_discovery`, `tool_output_ceiling`, `tool_parameter_contract`, `tool_vocabulary`, `tools_policy`, `usage_extraction`, `wrap_up_budget`, `write_integrity`.
- Anything engine-side as a running process; the `;` argument is source-backed only.
- The `#[ignore]`d hardware tests and any real round.
- Whether a real editor rebuilds `.godot` inside the candidate view, and whether a real product ever carries a `;` comment.
- The batch's own raw logs; I re-measured instead.

## 6. What I did not do

- No round, no engine, no network, nothing staged/committed/pushed.
- I wrote nothing under `runs/**` or any workspace; inside the repository I only cleared 63 gitignored `target/debug/.fingerprint/hof-rs-*` directories, touched 101 tracked `.rs` mtimes (after the `--list` rebuild `git status --porcelain` is still just the four pre-existing untracked leftovers) and wrote this report. No report, frozen specification, `DECISIONS.md` or `godot-mcp/**` was modified.
- I did not re-check the DR-87 acceptance's other claims, or `godot-mcp/**` beyond `gdscript_tokenizer.cpp`, `variant_parser.cpp` and `resource_format_text.cpp`.

## 7. Advice for the next batch

1. **Model the resource reader's own comment.** Give `scan_line` (or its caller) the per-extension rule so `;` opens a comment in `.tscn`/`.tres` exactly as `#` does in `.gd` (`variant_parser.cpp:215`, `:1787`). One rule closes DR89A-1 and DR89A-2. Pin it with a `.tscn` and a `.tres` whose `;` comment holds an apostrophe, a lone quote and an unmatched `(`, plus the converse that a quote inside a `;` comment no longer swallows a real fragment behind it.
2. **Keep every truncation finding this batch restored** - a literal still open at EOF stays a fragment; do not reintroduce a per-line scan.
3. **Close the gate in one clean run** and publish the literal exit code taken with no second test process running; if the budget is short, the 14 targets named above are all that is missing.
4. **Keep the four plants** and keep bumping mtimes forward after a plant/restore (a backward mtime made my first driver read a planted run as green - the same stale-binary class the batch recorded).
5. **Record the `;` fix as a decision** with the engine citations, and note the one-line in-place correction of `TASK-DR88-REPORT.md` as the deliberate, declared exception the DR-88 acceptance asked for.
