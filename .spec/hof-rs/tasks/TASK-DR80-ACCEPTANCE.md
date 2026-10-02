```json
{
  "task": "TASK-DR80-ACCEPTANCE",
  "kind": "independent acceptance of the wrap-up batch (offline; no engine; no round; runs/** read-only)",
  "adjudicated_by": "fresh, independent acceptance subagent with no upstream context; TASK-DR80-REPORT.md used only as a lead; every figure below was produced by my own read-only commands, my own tamper copies outside the repository, or my own full gate runs",
  "reviewed": [
    "TASK-DR80.md (the five items)",
    "TASK-DR80-REPORT.md (lead only)",
    "OBJECTIVE-ACCEPTANCE.md",
    "TASK-DR79-ACCEPTANCE.md",
    "DECISIONS.md D289 / D293"
  ],
  "repo_state_at_review": {
    "head": "3e727b97aa968b05fc715132a288324082679a3c",
    "head_subject": "fix(dr80): clear the leftover temporaries, annotate the stale engine string, correct two erratum figures and add the append-only guard",
    "head_committed_by": "the dispatcher after the implementer closed (commit date 2026-10-02 08:56:31 +0800, author starsliving, 4 files, 1419 insertions / 0 deletions); the report's recorded head c2780bc is the pre-commit state and is accurate as a close-time snapshot",
    "origin_master": "8ddbad3f4db43c28be158c17ad0678fe4d77857c",
    "ahead": 5,
    "working_tree": "clean (git status --porcelain -uall empty) at review start, so every committed blob equals the working file I verified",
    "nested_engine_head": "fc63af77c33368c4a1bb839c95d19750554f63a3",
    "nested_engine_porcelain_lines": 0
  },
  "verdict": "pass",
  "verdict_scope": "All five task items and all six job areas of the acceptance brief are independently reproduced. The three root temporaries are gone with pre-removal capture whose digests recompute from the captured content and whose mtimes match an earlier independent record; the REQUIREMENTS note is a pure append whose causal claim (the engine binary really was replaced between smoke-t6 and smoke-t7, with size and hash changing) I verified from eight rounds' meta.json and the on-disk binary; the two erratum corrections state the payload and file figures separately with digests that recompute, the 25,908 claim holds for the round's artifacts, and the wrong values survive marked incorrect; the guard's every pin recomputes and my three plants on copies redden it as claimed, while the real reports' hashes are unchanged; the gate reproduces 560/0/7 with the baseline 554/0/7 obtained by parking the new test, +6/-0 listing, ignored 7 to 7, fmt clean. Three non-blocking defects and six risks are recorded; none contradicts a substantive claim.",
  "criteria": [
    {
      "id": "ITEM1-REMOVALS-GONE",
      "pass": true,
      "evidence": ".tmp_coin.json / .tmp_goal.json / .tmp_hud.json do not exist (ls -> 'No such file or directory'; os.path.exists False x3). git status --porcelain -uall is now empty (the report's close-time tree showed exactly three ?? lines). runs/smoke-t13/iter-1/result.json.out_of_tree_writes still lists exactly those three names, and both the T13 report and DECISIONS.md D293 keep the fact, so no unique evidence was destroyed."
    },
    {
      "id": "ITEM1-DIGESTS-PRE-REMOVAL",
      "pass": true,
      "evidence": "Each recorded digest recomputes from the recorded content byte-for-byte: sha256 of the 108-byte '{\"path\":\"Coin1\",...}  \\r\\n' = ce741bfa7e5c5f46ad23c324a239ff570610b5d61e27ab4db51e0475c8ffaa89; the 68-byte Goal file = 47ebe914185d422997e8f948cf2e742c9ab1c4327fd27c60bb268365e3446b07; the 46-byte HUD file = ec3876325a2f6bd96f26449246705597caeeb4b995edf84ce9eeebe532725fa2; recorded byte counts also match. The recorded mtimes 1790887948.9697561 / 1790887949.0608892 / 1790887949.123736 = 2026-10-02 04:52:28.970 / 29.061 / 29.124 (+0800) equal, to the millisecond, the mtimes TASK-DR79-ACCEPTANCE.md line 105 recorded hours earlier while the files still existed on disk. Content and mtime could only have been captured while the files existed, so the capture is pre-removal."
    },
    {
      "id": "ITEM1-NO-COLLATERAL",
      "pass": true,
      "evidence": "commit 3e727b9 touches exactly 4 files (2 M, 2 A), 1419 insertions / 0 deletions; git diff --name-status c2780bc..HEAD shows no D and no R; all 6967 tracked files exist (missing_tracked = []); the root listing is otherwise unchanged (%DST%, .gitattributes, .githooks, .gitignore, .spec, .workspace, the two PDF/OCR artefacts, Cargo.lock, Cargo.toml, DECISIONS.md, config, godot-mcp, runs, scripts, src, target, tests) and contains no .tmp*/*.bak file; the tracked %DST% oddity (7 files from 51f9987) is intact. Nothing else in the repository changed as a result of the removal."
    },
    {
      "id": "ITEM2-APPEND-ONLY-AND-SUPERSEDED",
      "pass": true,
      "evidence": "git diff c2780bc..HEAD -- REQUIREMENTS.md = 85 insertions / 0 deletions. Byte level: the pre-batch blob (20,904 B / 5ba8d91418ddfe320f222c94e72abf201075586fe69bac2c33c90f9946bc90b1, identical at c2780bc and ec90c19) is a byte-identical prefix of the current 26,491 B file; the append is 5,587 B (sha 038d4bf52222fda4...) beginning with the fixed six bytes '\\n---\\n\\n'; the heading '# DR-80 注（追加式，2026-10-02）' owns a whole line at offset 20,910 whose prefix sha256 = 7b551ca08c4c5abf15a95cb8edcc4977ce8d03c649654ab4a5ab01f649cae5ae (the guard's REQ seal); crlf 0 / lf 315. C3's sentence exists verbatim in the parent and still in the file, and the note marks it superseded x3 and incorrect x3 while never rewriting it."
    },
    {
      "id": "ITEM2-CAUSALITY-ENGINE-REPLACED",
      "pass": true,
      "evidence": "The stale string is not a typo: the binary really was replaced. runs/smoke-t6/meta.json engine.binary = {sha256 25d29eb4fbaf48c00911bcb18b491d5a7305542e00557e70a05f185b935bb468, size_bytes 194207744, mtime_unix 1790572931} with version_string 4.8.dev.mono.custom_build.ba1587c71; runs/smoke-t7/meta.json = {sha256 08483088a4a2772841cd3b4c916b2d45b3cb6255656cf3951598a86fce7e9e6a, size_bytes 194216960, mtime_unix 1790641862} with 4.8.dev.mono.custom_build.035edfce7; smoke-t8..t13 all equal smoke-t7. The binary on disk now is 194,216,960 B / 08483088... / mtime 1790641862.53, i.e. the current one. TASK-SMOKE-T7-REPORT.md line 387 records the identical change in prose, and runs/smoke-t11/evidence/round/prerun_state.txt lines 20/21/23/24 carry SIZE=194216960, MTIME_UNIX=1790641862, SHA256=08483088..., VERSION_STRING=035edfce7. git -C godot-mcp/godot merge-base --is-ancestor 035edfce7 HEAD exits 0. The note's explanation is right, and the primary record is the round meta.json - stronger than the line it cites."
    },
    {
      "id": "ITEM3-PAYLOAD-VS-FILE-SIZES",
      "pass": true,
      "evidence": "My own decomposition of the two round-author captures: the bytes between the two marker lines are 31,204 / 591 B; stripping the capture's one leading and one trailing LF gives the reply payload 31,202 B / sha256 980830d3008d07005266e9757b6dc98ef9e5637e0f635be6ee5d59694d042519 and 589 B / 7b80dcbe985349419701caa391b0e55725c9816e4163bd65cb92c66ba09e7d85 (the stripped head is '{\"id\":1,...}', so this is the JSON payload); the files are 31,360 B / 246a442369259a5db9dce89a82f697d3dd9a8cacd8d6f384436c25049360164b and 816 B / 302ac4ef6bfca3d29b1f5d9d12a4b19f954dae42fedfacc10fefa443fa8aebb6. The appended F-1 table states exactly these four figures with exactly these digests, names file / between-markers / payload as three separate calibres, and keeps line 1548 verbatim marked incorrect."
    },
    {
      "id": "ITEM3-THE-25908-CLAIM",
      "pass": true,
      "evidence": "25,908 matches no artifact of that round: my own os.walk over all 6,586 files under runs/smoke-t13 returns [] for size 25,908, and it is neither probe's file size (31,360 / 816) nor payload (31,202 / 589). The report does not overclaim: its repo-wide scan finds exactly one 25,908-byte file, runs/playability/PlayJev-src/demo/replays/2048/playjev-0.8b-sft_all1_d1_5012.js, which my own scan reproduces exactly, and the report names it as an unrelated data tree rather than generalising."
    },
    {
      "id": "ITEM3-CORRECTED-HASH",
      "pass": true,
      "evidence": "sha256(runs/smoke-t13/evidence/analysis/cite_check.txt) = 21f071f5e0c7ef5ee7374848293f2297f3270207a6bf046b88d97fd506ab455a at 18,401 B, exactly the value F-2 states; the old prefix 4bbce1a00a26101c does not match (startswith -> False). Line 1485 still reads '| ... cite_check.txt | 18189 | 4bbce1a00a26101c |' verbatim and F-2 quotes it and marks it incorrect, noting that DR-79's E-4e had repaired only the size column and explicitly left the hash unchecked."
    },
    {
      "id": "GUARD-SEALS-ALL-PINS",
      "pass": true,
      "evidence": "tests/append_only_guard.rs (19,372 B / e6d0df069ae23396111d1e7b8ac7307256f77d3beb48b0013b9212519b7ad3a9, 485 LF / 0 CRLF, 6 #[test]) seals, and I recomputed every pin from the frozen bytes: T13 before-DR79 prefix 107,709 B / 9bbe81c8360d481ef01528f99467cd1253921ff713980336da05a32e3ea9fd36; T13 before-DR80 prefix 134,085 B / 2f2a2418bc3d0785ec47235da7c868ee64f590e73b38f3e3c7619696d74945a9; T13 line-anchored ```json block 34,699 B / 36e34d0d0436920605fb3f06065c1c8e4303bbf90b92a499d5e37f6f8d6c3c9f, byte-equal to runs/smoke-t13/evidence/analysis/machine_block.json (fences at lines 741/1408); DR-73 before-ledger prefix 48,811 B / db0a5a7a5c2086b46250582748fd08a27c7764d5f935922655acc4658da1543c plus all four DR-77-* markers surviving; REQUIREMENTS before-note prefix 20,910 B / 7b551ca08c4c5abf15a95cb8edcc4977ce8d03c649654ab4a5ab01f649cae5ae, C3 verbatim, and the measured 035edfce7 named. DR-73 and REQUIREMENTS have no round json block, so T13 is the only covered corrected report with a block to pin."
    },
    {
      "id": "GUARD-PLANTS-REPRODUCED",
      "pass": true,
      "evidence": "My own three plants on copies under C:/Users/wyl/AppData/Local/Temp/dr80acc/plants (never in the repository), each compiled with CARGO_MANIFEST_DIR set to that copy and run: control (pristine copies) 6 passed, exit 0; in-place edit (byte 60,000 -> 'Q', inside the prefix, outside the block) exit 101, red = the two T13 seal tests + the non-vacuity test, block test green; line deletion (the '---' line at bytes 107,704-107,708) exit 101, same red set; block edit (offset 66,781, '{' -> '[') exit 101, red = block test + both seal tests + non-vacuity (4 failed / 2 passed). So each tamper shape reddens the guard, and the block pin is a separate check, not the prefix check counted twice. I also recomputed the report's exact three mutants byte-for-byte and their sha256 equal the report's values (25af9e04c47a846eeb100ada35383d7d714e5edb4d274c7565c9f8383e22140d; fcafb1573b36f37298eb564b4fc70d0d0c1b6cd63ccc9af46e274b3b8b1a0ecb; 85ad090b33a9555bd767d8857e5d8c87d82ee5a287011ddf0618a4f602b6f77e)."
    },
    {
      "id": "GUARD-REAL-FILES-UNCHANGED",
      "pass": true,
      "evidence": "The three real documents' sha256 are identical before and after my whole campaign and after both full gate suites: TASK-SMOKE-T13-REPORT.md 4f32174f6d332cd57e7bffb7def94876c355c7e7fd62147f28ab0a8cbd5c7755, TASK-DR73-REPORT.md 5dcaac4a60b0558c1d42e6117b738eb1979af5493e7eaaea36dcdbaf3ee1b495, REQUIREMENTS.md 298a948929a434a91b9088f4d566b7e387d0cfeb270f86a79d88b006821e0e54. The guard's own non-vacuity test writes its mutants under std::env::temp_dir() and re-reads the real report, asserting its hash is unchanged."
    },
    {
      "id": "GUARD-TEST-FIRST-CAVEAT",
      "pass": true,
      "evidence": "The disclosed departure is real but weaker than disclosed: the two newest seal constants are fully derivable BEFORE the appends as sha256(parent blob + the fixed six bytes '\\n---\\n\\n'). From the c2780bc blobs alone I computed 134,085 / 2f2a2418bc3d0785... for T13 and 20,910 / 7b551ca08c4c5abf... for REQUIREMENTS - exactly the pinned values. What genuinely depended on the append is the heading-existence assertion (the DR-80 heading and the DR-80 note did not exist), so the first red was an assertion red, not a compile error. The disclosure is honest in direction and the residual is small."
    },
    {
      "id": "GATE-FINAL",
      "pass": true,
      "evidence": "My own cargo test --offline at HEAD 3e727b9 (offline, no engine, no round): 60 suites, 560 passed / 0 failed / 7 ignored, exit 0, 950.8 s; zero FAILED and zero error lines in stdout/stderr; cargo test --offline -- --list yields 567 names; cargo fmt --check exits 0 with empty stdout and empty stderr. The six new names are present."
    },
    {
      "id": "GATE-BASELINE-REPRODUCED-BY-PARKING",
      "pass": true,
      "evidence": "Baseline reproduced, not trusted: I renamed tests/append_only_guard.rs to a non-.rs name inside tests/ (cargo auto-discovers tests/*.rs only) and ran the full suite - 59 suites, 554 passed / 0 failed / 7 ignored, exit 0, 975.4 s, --list 561; then restored the file and its sha256 is e6d0df069ae23396111d1e7b8ac7307256f77d3beb48b0013b9212519b7ad3a9 both before the park and after the restore (restored_byte_exact = True). Sorted listing diff: exactly the six new names added, zero removed; ignored 7 -> 7; 561 -> 567 and 554 -> 560 are arithmetically consistent. No test name was removed."
    },
    {
      "id": "HYGIENE-ZONES",
      "pass": true,
      "evidence": "runs/** newest mtime 1790889780.483188 (runs/smoke-t13/evidence/analysis/cite_check.txt = 2026-10-02 05:23:00 +0800, hours before the batch) with 6,586 files - identical before and after both of my full suite runs; .workspace/** newest mtime 1790888643.0617301 (.workspace/fresh-t13/.godot/editor/editor_layout.cfg, 04:24:03) with 492 files - identical before and after. Neither zone was written by the batch or by this acceptance."
    },
    {
      "id": "HYGIENE-FROZEN-AND-NOT-PUSHED",
      "pass": true,
      "evidence": "PRD-mario.md, DECISIONS.md, Cargo.toml and Cargo.lock are byte-equal to their HEAD blobs (4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a; 5621b2eaf8cbb36a81d4ed3d4257605c703bbfff0e137c698fcc7fd78e593e69; e0c4992bd828729b8514f9cf694925687b726157d45463a636390081a3dadba1; d98fa91565ec72ae998fd9f6fd3838286e287e4baf8020c5114a1e2ac0bfdb36); the DR-80 commit range contains no change to Cargo.toml/Cargo.lock (no new dependency) and none to DECISIONS.md; the nested engine repo HEAD is fc63af77... with empty porcelain; origin/master is still 8ddbad3f... and git diff --cached is empty (nothing pushed, nothing staged); the root has no .tmp/.bak residue; tracked *.rs are 89 LF / 8 CRLF / 0 mixed (96 before the new file became tracked, +1 = the new 485-LF file), so no line-ending rewrite. The only untracked file after my work is this report."
    },
    {
      "id": "REPORT-MACHINE-BLOCK-ROUND-TRIP",
      "pass": true,
      "evidence": "TASK-DR80-REPORT.md carries exactly one line-anchored ```json block; json.loads succeeds and yields 16 top-level keys; json.dumps(obj, ensure_ascii=False, indent=2) reproduces the block exactly once its single terminating LF is removed (26,045 of 26,046 bytes), matching the file's own SELF-CHECK line 'round_trip_equal=True ... bytes=26045'. Every field I could recompute (repo state, both append_evidence triples, the engine identity, the probe figures, the guard pins and test names, the gate readings, the touched_documents hashes) matches my independent measurements; the two fields that no longer match the repository (head c2780bc vs 3e727b9, tracked .rs 96 vs 97) are the disclosed post-close commit, not drift of the reviewed bytes."
    },
    {
      "id": "REPORT-UNVERIFIED-LIST-ADJUDICATED",
      "pass": true,
      "evidence": "Its four unverified items stand or are now closed: (1) offline/no-engine/no-round holds for me too; (2) the engine --version was not re-executed - I also did not, by constraint, but the string is corroborated by eight rounds' meta.json plus prerun_state.txt plus the on-disk binary identity; (3) runs/** zero-write rests on mtimes - I reproduced the reading and my own runs left it byte-identical; (4) 'the pins were computed by the same agent' is closed by this acceptance, which recomputed every pin and every plant independently. Its same-family registrations are accurate: DESIGN-DETAIL.md:1508/1587 and TASK-DR41-IMPL.md:39/140 still carry ba1587c71; TASK-DR79-REPORT.md:36 still carries 25908/816 as a reply figure; runs/smoke-t13/evidence/analysis/round_facts.txt:160 still says verified-only 10 / gap-only 13."
    }
  ],
  "defects": [
    {
      "id": "A-1",
      "severity": "info",
      "what": "The new material presents a paraphrase as a quotation. F-3 of the appended DR-80 section (TASK-SMOKE-T13-REPORT.md:1939) and risks[2] of TASK-DR80-REPORT.md say TASK-DR79-REPORT.md line 36 writes 'tools/list (25,908 B reply)'. Line 36 actually writes '回包 25908/816 B'. The substantive registration - the wrong 25,908 figure still lives at that line as a reply reading - is correct; only the quoted form is not verbatim, in a batch whose theme is exact quotation.",
      "reproduction": "sed -n '36p' .spec/hof-rs/tasks/TASK-DR79-REPORT.md   # shows 回包 25908/816 B, not 'tools/list (25,908 B reply)'"
    },
    {
      "id": "A-2",
      "severity": "low",
      "what": "Scope of the mechanical guard: it seals TASK-SMOKE-T13-REPORT.md, TASK-DR73-REPORT.md and REQUIREMENTS.md (plus TASK-DR70/DR-71 via tests/byte_claims.rs and TASK-DR73 via tests/dr77_evidence_tightening.rs). Other historically corrected documents remain unsealed: TASK-SMOKE-T8-REPORT.md (DR-68 in-place correction declaration), TASK-SMOKE-T10-ACCEPTANCE.md (erratum block appended by DR-76), TASK-DR76-REPORT.md, TASK-DR57-REPORT.md, TASK-SMOKE-T10-REPORT.md, TASK-DR77-ACCEPTANCE.md. This satisfies the task book's explicit minimum ('at least TASK-SMOKE-T13-REPORT.md and TASK-DR73-REPORT.md') but falls short of the acceptance brief's phrase 'every corrected report'.",
      "reproduction": "grep -rn 'SMOKE-T8-REPORT\\|SMOKE-T10-ACCEPTANCE\\|DR76-REPORT\\|DR57-REPORT\\|DR77-ACCEPTANCE' tests/*.rs   # no seal; only DR70/DR71 (byte_claims.rs), DR73 (dr77_evidence_tightening.rs + append_only_guard.rs), T13 and REQUIREMENTS (append_only_guard.rs)"
    },
    {
      "id": "A-3",
      "severity": "info",
      "what": "honest_disclosure item 3 of TASK-DR80-REPORT.md says the DR-80 seal and the requirements seal 'could only be computed after their documents were appended'. Both are in fact derivable in advance from the parent blob plus the fixed six-byte separator, so the departure from strict test-first is narrower than disclosed; the genuine residual is that the heading-existence assertions were red until the append.",
      "reproduction": "python -c \"import hashlib,subprocess;pre=subprocess.run(['git','show','c2780bc:.spec/hof-rs/tasks/TASK-SMOKE-T13-REPORT.md'],capture_output=True).stdout;print(20904*(0)+len(pre)+6, hashlib.sha256(pre+b'\\n---\\n\\n').hexdigest())\"  # 134085 2f2a2418... = the pinned DR-80 seal"
    }
  ],
  "risks": [
    "The guard reads the working tree, not a git object, and its authority is only as strong as the pinned constants: a rewrite performed before the seal was computed, or a rewrite accompanied by an updated constant, is invisible to it, and an append placed after the newest seal is unprotected until a new constant is added. Its failure text reports only a sha256 mismatch, so an EOL rewrite and a character rewrite are indistinguishable (both red, which is the intent).",
    "Only the T13 report's json block is pinned. The DR-73 ledger content and the appended corrective sections of T13 and REQUIREMENTS are protected only by the next seal, and TASK-DR80-REPORT.md's own machine block (and every future acceptance report) has no pin at all.",
    "The registered same-family stale readings stay frozen by design: TASK-DR79-REPORT.md:36 (25908/816), runs/smoke-t13/evidence/analysis/round_facts.txt:160 (10/13), DESIGN-DETAIL.md:1508/1587 and TASK-DR41-IMPL.md:39/140 (ba1587c71). A reader of those frozen files still gets the superseded values.",
    "The removal method ('three explicit os.remove calls, no rm -rf, no wildcard, no recursion') and the 'runs/** zero writes' claim are effect-verified only: I can prove no tracked or root file is missing and that the newest runs/** mtime predates the batch, but a write that preserved every mtime would be invisible and the implementer's command history is not an artifact I can read.",
    "The DR-80 report's machine block is now stale in two fields relative to the repository (head c2780bc -> 3e727b9, tracked *.rs 96 -> 97) because the dispatcher committed after close, as the report itself anticipated. The reviewed bytes are not in question (working tree == HEAD), but a future reader comparing the block against HEAD will see two mismatches.",
    "The legacy reproduction command quoted in TASK-DR79-ACCEPTANCE.md D-1 (line 113) uses rstrip and prints 31,203 / 590, not the 31,202 / 589 it asserts; the DR-80 correction uses strip and is the correct reading. The wrong legacy command is still frozen in the DR-79 acceptance and could mislead a re-checker."
  ],
  "unverified": [
    "The implementer's deletion commands themselves (no rm -rf, no wildcard, no unexpanded-variable path): not observable from the repository; only the effects (exactly the three named files gone, no collateral) are verified.",
    "The three code plants P-A/P-B/P-C (mutating tests/append_only_guard.rs and restoring it byte-exactly): I did not re-run them; I verified the file's sha256 is e6d0df06... and that it is the committed blob, and I re-ran the report/mutant plants instead.",
    "The implementer's fingerprint clearing (61 then 60 directories) and the per-file touch of 96 tracked *.rs: not re-run. I reproduced the baseline by the mandated parking method instead, which yields the same 554/0/7 / 561.",
    "The full godot-mcp/** newest-mtime reading (1790650641.240421) was not reproduced; I inspected only godot-mcp/godot/bin (newest 1790641863.43) and the nested repository status (HEAD fc63af77..., porcelain empty), so an mtime-preserving or ignored-file write elsewhere in the engine tree would not be caught by me.",
    "The engine binary's own --version output was not re-executed (hard constraint: no engine); the 035edfce7 string rests on the frozen round records and on the on-disk binary's size/sha256/mtime agreeing with those records.",
    "No filesystem audit trail exists for runs/** and .workspace/**: my zero-write finding is the equality of the newest mtime and the file count before and after, which a write that preserved every mtime would defeat."
  ],
  "not_checked": [
    "No engine was started, no round was run, no MCP or model endpoint was called and the network was not used (hard constraint).",
    "I did not modify any real historical report, any workspace directory, PRD-mario.md, DECISIONS.md or godot-mcp/**; every tamper experiment ran on copies under C:/Users/wyl/AppData/Local/Temp/dr80acc/ outside the repository, I used no rm -rf on any path, constructed no path from an unexpanded variable, and staged/pushed nothing.",
    "I did not verify the other rows of the 59-row T13 evidence index (I verified cite_check.txt and machine_block.json, the two rows this batch touches).",
    "I did not re-derive E1..E6, the A0/A1 tree digests, the ten read-only baselines, or the tool census - all out of this batch's scope.",
    "I did not diff the *.redacted.json sidecars against their originals, and did not audit the 177 tool schemas or the Rust runtime beyond the paths named here (tests/append_only_guard.rs and the evidence files)."
  ],
  "plants_and_counterexamples": [
    "Guard plant, control (pristine copies of T13 / DR-73 / REQUIREMENTS, CARGO_MANIFEST_DIR = the copy): 6 passed, exit 0.",
    "Guard plant A, in-place edit of the T13 copy at byte 60,000 (inside the sealed prefix, outside the block): exit 101; red = the_seal_checks_redden_on_temporary_copies, the_t13_report_prefix_before_the_dr79_erratum_is_frozen, the_t13_report_prefix_before_the_dr80_correction_is_frozen; the block test stayed green.",
    "Guard plant B, deletion of the '---' line at bytes 107,704-107,708 of the T13 copy: exit 101; same red set, block test green.",
    "Guard plant C, edit inside the T13 machine-readable block at offset 66,781 ('{' -> '['): exit 101; red = block test + both seal tests + non-vacuity (2 passed / 4 failed) - so the block pin is independent.",
    "Exact-mutant reproduction: recomputing the report's three declared mutants from the real bytes gives sha256 25af9e04c47a846eeb100ada35383d7d714e5edb4d274c7565c9f8383e22140d (offset 1446, '|' -> '!'), fcafb1573b36f37298eb564b4fc70d0d0c1b6cd63ccc9af46e274b3b8b1a0ecb (delete bytes 1446:1508, 62 B -> 143,549 B) and 85ad090b33a9555bd767d8857e5d8c87d82ee5a287011ddf0618a4f602b6f77e (offset 66,781) - all three equal the report's recorded values.",
    "Marker-newline counterexample: the capture region between '---- raw reply begin ----' and '---- raw reply end ----' is 31,204 / 591 B; rstrip gives 31,203 / 590; strip gives 31,202 / 589 with sha 980830d3... / 7b80dcbe.... Running the legacy command quoted in TASK-DR79-ACCEPTANCE.md verbatim prints 31360 31203 and 816 590, so that acceptance's asserted 31,202 / 589 is unreachable by its own command; the DR-80 correction's strip-based reading is the right one.",
    "Derivability counterexample to honest_disclosure 3: sha256(c2780bc blob + '\\n---\\n\\n') = 2f2a2418... at 134,085 B for T13 and 7b551ca0... at 20,910 B for REQUIREMENTS, i.e. the two 'after the append' constants were computable before the append.",
    "cite_check counterexample: sha256 = 21f071f5e0c7ef5e... at 18,401 B; startswith('4bbce1a00a26101c') is False, so the index row's hash column was stale while its size column had been repaired.",
    "25,908 search: [] over the 6,586 files under runs/smoke-t13; exactly one hit over all of runs/** (runs/playability/PlayJev-src/demo/replays/2048/playjev-0.8b-sft_all1_d1_5012.js), matching the report's stated non-generalisation.",
    "Machine-block round trip: json.loads -> 16 keys; json.dumps(ensure_ascii=False, indent=2) == the block minus its single terminating LF (26,045 / 26,046 bytes); the T13 report's block is byte-equal to machine_block.json (34,699 B / 36e34d0d...) with fences at lines 741 and 1408.",
    "Removal-evidence counterexample attempt: I tried to falsify the pre-removal capture by recomputing the recorded digests from the recorded content - they match exactly - and by comparing the recorded mtimes with TASK-DR79-ACCEPTANCE.md's independent milliseconds-earlier record (04:52:28.970 / 29.061 / 29.124) - also exact. The capture cannot have been made after deletion.",
    "Gate listing counterexample: the sorted --list sets differ by exactly the six new names and nothing else (561 -> 567, removed = []), so no test was renamed out of existence as a way to reach the new count."
  ]
}
```

# TASK-DR80-ACCEPTANCE — 独立验收（收尾批：清残留 / 文档串注 / 两处更正 / 仅追加守卫）

> 验收人：**全新、独立的验收子代理**，无上游上下文。`TASK-DR80-REPORT.md` **只当线索**，所有读数由我自己复算。
> **离线**：未起引擎、未跑轮、未联网、未调 MCP/模型端点；`runs/**` 与 `.workspace/**` **零写入**（含"写过再删"）。
> **未对任何路径用 `rm -rf`**；**未从未展开变量构造路径**；未 stage、未 commit、未 push；
> 未改任何真实历史报告、`DECISIONS.md`、`PRD-mario.md`、`godot-mcp/**`、任何工作区。
> 篡改实验全部在**仓外** `C:\Users\wyl\AppData\Local\Temp\dr80acc\**` 的**副本**上做。
> 唯一写入的仓库文件是**本报告本身**。机器可读块由 `json.dumps(..., ensure_ascii=False, indent=2)` 生成，
> 落盘前先 `json.loads` 回读、落盘后再回读一次（自证行见文末）。

## 0. 裁决

**verdict = pass**（18 条判据全 pass；3 条缺陷：**1 low + 2 info**；6 条风险；6 条未验证）。

**一句话**：五项全部独立复现——三个残留文件确实先取证后删除且无连带损失；`REQUIREMENTS.md` 的注是纯追加且
**因果解释正确**（引擎二进制在 T6→T7 之间真被换过，size/hash 同步变化，我用 8 轮 `meta.json` 复算）；
勘误的两个错数按"回包载荷 / 文件大小"分开更正且摘要全部复算一致、25,908 在本轮工件里确实不存在；
守卫的每一条钉我都重算过，**我自己做的三处副本植入各自让它红**，真件哈希前后不变；
门 **560/0/7**、基线用"停用新测试"自行复现为 **554/0/7**、`--list` 561→567 恰好 +6/−0、`ignored` 7→7、`fmt` 干净。
三条缺陷都不推翻任何实质结论。

**状态提示**：实现者报告记录的 HEAD 是 `c2780bc`（收尾时点），调度者随后把它提交为 **`3e727b9`**
（4 文件、1419 insertions / 0 deletions，含本报告所在批次的两份文档与新测试）；`origin/master` 仍是 `8ddbad3f`，
本地领先 5。我在 `3e727b9` 上、工作树干净的状态下验收，因此**提交内容与实现者交付的字节相同**。

## 1. 逐项证据表（我的命令与读数）

| # | 任务项 | 我的判据 | 我的读数 | 结论 |
|---|---|---|---|---|
| ① | 三个残留文件已删 | `ls` / `os.path.exists` | 三者均 `No such file or directory`；`git status -uall` 为空；`result.json.out_of_tree_writes` 仍逐字列出三者 | pass |
| ① | 摘要在删除**之前**记录 | 由记录内容反算 sha256 + 与 DR-79 验收的 mtime 交叉 | `ce741bfa…`/108、`47ebe914…`/68、`ec387632…`/46 **全部由记录内容逐一算出且相等**；mtime `…948.9698/949.0609/949.1237` = 04:52:28.970/29.061/29.124，与 `TASK-DR79-ACCEPTANCE.md:105` 独立记录的毫秒值**逐位相同** | pass |
| ① | 删除无连带损失 | 提交差异 + 被跟踪文件存在性 + 根目录清单 | `3e727b9` 只动 4 文件（2 M / 2 A）、**0 删除**；`c2780bc..HEAD` 无 D 无 R；6967 个被跟踪文件**无一缺失**；`%DST%`（7 文件）完好；根目录无 `.tmp*`/`.bak` | pass |
| ② | 原句逐字保留并标 superseded | 与父 blob 逐字节比 + 标记计数 | 父 blob（20,904 B / `5ba8d914…`）是当前 26,491 B 文件的**逐字节前缀**；C3 原句在父件与现件中均逐字存在；注中 `superseded` ×3、`incorrect` ×3 | pass |
| ② | 注是纯追加、前缀逐字节相同 | diff 行数 + 字节前缀 + seal | `85 insertions / 0 deletions`；追加 5,587 B 起于固定 6 字节 `\n---\n\n`；heading 起于 **20,910**，其前缀 sha `7b551ca0…`（=守卫 REQ seal）；`crlf 0 / lf 315` | pass |
| ② | **因果解释正确** | 8 轮 `meta.json` + 在盘二进制 | T6：`ba1587c71` / sha `25d29eb4…` / **194,207,744** / mtime `1790572931`；T7..T13：`035edfce7` / sha `08483088…` / **194,216,960** / mtime `1790641862`；在盘二进制 = `194216960` / `08483088…` / mtime `1790641862.53`；`prerun_state.txt` 20/21/23/24 行逐字一致；`T7-REPORT.md:387` 文字记录同一替换；`035edfce7` 是嵌套仓 HEAD 的祖先（exit 0） | pass |
| ③ | 回包载荷 / 文件大小分开更正 | 我自己解两标记 | 区间 **31,204 / 591**；`strip` 后载荷 **31,202 / `980830d3…`** 与 **589 / `7b80dcbe…`**（去换行后头部即 `{"id":1,…}`）；文件 **31,360 / `246a4423…`** 与 **816 / `302ac4ef…`**；F-1 表四值四摘要**逐一相同**，并明说三种口径不可混用 | pass |
| ③ | 「25,908 不匹配本轮任何工件」 | 我自己扫 `runs/**` | `runs/smoke-t13` 全部 **6,586** 个文件里 **无** 25,908 B 者；扫全 `runs/**` **恰好一个**：`runs/playability/PlayJev-src/…/playjev-0.8b-sft_all1_d1_5012.js`，与报告所述**完全一致**且报告明确不去泛化 | pass |
| ④ | 修正哈希与文件相符 | 我重算 | `cite_check.txt` = **18,401 B / `21f071f5e0c7ef5e7374848293f2297f3270207a6bf046b88d97fd506ab455a`**；旧前缀 `4bbce1a00a26101c` 不匹配（False） | pass |
| ④ | 错值存活且标 incorrect | 直接读原行 | 第 1548 行仍是 "25,908 B 回包 … 816 B"，第 1485 行仍是 "18189 / `4bbce1a00a26101c`"；F-1/F-2 分别逐字引用并标 `incorrect` | pass |
| ⑤ | 守卫钉住各前缀与块 | 读源码 + 重算每一条钉 | 19,372 B / `e6d0df06…`，485 LF / 0 CRLF，6 条 `#[test]`；T13 双 seal 107,709/`9bbe81c8…`、134,085/`2f2a2418…`；块 34,699/`36e34d0d…`（= `machine_block.json`，围栏 741/1408）；DR-73 seal 48,811/`db0a5a7a…` + 四个 `DR-77-*` 标记存活；REQ seal 20,910/`7b551ca0…` + C3 逐字 + `035edfce7`。**全部重算一致** | pass |
| ⑤ | 三种植入各自红 | 我自己的副本 + 我自己的变异 | 对照 6 passed/exit 0；就地改写 exit 101（两 seal + 非空洞红、块测试绿）；删行 exit 101（同上）；块内改写 exit 101（**块测试另红**，4 failed / 2 passed） | pass |
| ⑤ | 真报告未被碰 | 活动前后哈希 | T13 `4f32174f…`、DR-73 `5dcaac4a…`、REQ `298a9489…` 在整场植入与两轮全套**前后完全相同** | pass |
| 门 | 终态 `cargo test --offline` | 我自己跑 | **60 套件，560 passed / 0 failed / 7 ignored，exit 0，950.8 s**；`--list` **567**；无 `FAILED`/`error` 行 | pass |
| 门 | 基线自行复现 | 停用新测试（改名）后跑 | **59 套件，554 / 0 / 7，exit 0，975.4 s**；`--list` **561**；随后逐字节恢复（sha 前后均 `e6d0df06…`）；排序 diff **恰好新增 6 名、删除 0** | pass |
| 门 | `fmt` | `cargo fmt --check` | exit 0，stdout 与 stderr **均为空** | pass |
| 禁区 | zones / frozen / push | 只读检查 | `runs/**` 最新 mtime `1790889780.483188`（05:23，早于本批）且 6586 文件、`.workspace` 最新 `1790888643.0617301` 且 492 文件——**我两轮全套前后完全相同**；PRD/DECISIONS/Cargo.toml/Cargo.lock **逐字节等于 HEAD**；嵌套仓 `fc63af77…` porcelain 空；`origin/master` 未变、`--cached` 空；无新依赖；无行尾重写（89 LF / 8 CRLF / 0 mixed） | pass |
| 报告 | 机器可读块 | 栅栏感知 `json.loads` + 重序列化 | 1 个块、**16 顶层键**；`json.dumps(ensure_ascii=False, indent=2)` 去掉尾部单个 LF 后**逐字节复现**（26,045/26,046），与自证行 `bytes=26045` 一致 | pass |

## 2. 我自己做的植入与反例（全部在仓外副本上）

1. **守卫对照**：三份真件的**原始副本** → 6 passed / exit 0。
2. **就地改写**：T13 副本 **偏移 60,000** 改一个字节 → exit 101；红 = `the_seal_checks_redden_on_temporary_copies` +
   两条 T13 seal；**块测试仍绿**（证明块钉不是前缀钉的重复计数）。
3. **删行**：删掉偏移 **107,704–107,708** 的 `---` 行 → exit 101；同一组红。
4. **块内改写**：偏移 **66,781** 的 `{` → `[` → exit 101；**额外**让
   `the_t13_machine_readable_block_is_byte_frozen` 红（2 passed / 4 failed）。
5. **精确复现报告声称的三个变异 sha**：偏移 1446 的 `|`→`!` = `25af9e04…`（143,611 B）；
   删 1446:1508 共 62 B = `fcafb157…`（143,549 B）；偏移 66,781 = `85ad090b…`——**三者与报告记录逐字符相同**。
6. **换行反例（找到一处旧记录的口径错误）**：两标记之间的原始区间是 **31,204 / 591**；`rstrip` 得 **31,203 / 590**；
   `strip` 得 **31,202 / 589**（`980830d3…` / `7b80dcbe…`）。把 `TASK-DR79-ACCEPTANCE.md` D-1 里的复现命令**逐字运行**，
   打印的是 `31360 31203` 与 `816 590` —— **与该验收自己断言的 31,202 / 589 差 1 字节**。
   故 DR-80 用 `strip` 写出的 31,202 / 589 才是正确读数（该错属上一批，记录为风险/反例，不是本批缺陷）。
7. **对"两个 seal 只可能在追加后计算"的反例**：由 `c2780bc` 的父 blob 加固定 6 字节分隔符即可预先算出
   T13 seal = 134,085 / `2f2a2418…`、REQ seal = 20,910 / `7b551ca0…` ⇒ 诚实披露③把约束说过头了（见缺陷 A-3）。
8. **哈希反例**：`cite_check.txt` 重算 = `21f071f5…`；`startswith('4bbce1a00a26101c')` = **False**。
9. **"25,908"范围反例**：本轮 6,586 文件零命中；全 `runs/**` 恰好一个无关文件。
10. **删除前取证的证伪尝试**：试图用"记录内容反算"与"与更早独立记录的 mtime 比对"两条路推翻"先取证后删除"，
    两条路都**支持**报告 ⇒ 无法证伪；且文件已不存在，记录只可能来自删除之前。
11. **门净增反例**：排序后的 `--list` 集合差 = 恰好 6 个新名、**删除 0**，排除"删测试腾名额"这类假净增。

## 3. 独立判断

1. **本次收尾批的五项都真落地，且都在原始工件上可复算。** 尤其②的因果解释不是辩解而是**事实**：
   我从 T6/T7..T13 的 `meta.json` 直接读到二进制 sha/size/mtime 与版本串**同步变化**，在盘二进制又与现行记录一致——
   这比报告引用的 `TASK-SMOKE-T7-REPORT.md:387` 更强。C3 的旧串确实只是"换引擎前的真机读数"。
2. **勘误更正的定义比上一批更精确。** DR-80 把"回包载荷 / 区间 / 文件大小"三种口径拆开并对每种给摘要，
   正是上一批 D-1 的根因（口径混用）；两个新数字与我的独立复算完全一致。25,908 的否认限定在"本轮工件"，
   并主动交代全仓唯一的同尺寸文件，这是**不把范围说过头**的写法。
3. **守卫是真的机械化，且不是空洞断言。** 每一条钉我都重算；三种篡改形状各自红；块钉与两条前缀钉互相独立；
   被"蒙住"的守卫由非空洞性测试兜住（报告 P-C 的思路）。真件在我自己的实验前后哈希不变。
4. **对"仅追加"的边界要诚实**：守卫保护的是"从现在起不再变"，它读工作树而非 git 对象，**无法发现先于钉值的改动**，
   也**无法发现"改动 + 同步改钉值"**；最新 seal 之后追加的部分在加新钉之前不受保护。这些都被报告披露，
   我赞同其定性——但它意味着"机械守卫"不是"可验证历史"，只是"此后不可静默改写"。
5. **门是真实的**：我用与实现者不同的方法（只停用新测试，不清 fingerprint、不逐文件 touch）复现出**同一个基线 554/0/7 / 561**，
   终态 560/0/7 / 567，净差恰好 6，`ignored` 不变，无测试名被删，`fmt` 干净且无输出。⇒ 门读数不依赖实现者自述。
6. **三条缺陷都不推翻结论**：A-1 是把转述当引文（实质登记正确）；A-2 是守卫覆盖面小于"每份被更正过的报告"
   （满足任务书"至少"要求，不满足验收简令的字面表述）；A-3 是诚实披露把约束夸大了一点点（方向是好的）。

## 4. 未验证项与理由

- **实现者的删除命令本身**（无 `rm -rf`、无通配符、无未展开变量）：仓内没有可读的命令历史；我只能验证效果
  （只有那三个具名文件消失、无连带损失）。这一条**不可直接验证**。
- **三处代码植入 P-A/P-B/P-C**（改 `tests/append_only_guard.rs` 再逐字节回退）：我未重跑；我验证了该文件的
  sha256 = `e6d0df06…` 且等于已提交 blob，并改用**报告副本植入 + 精确变异哈希复算**来独立承重。
- **清 fingerprint（61/60）与逐文件 touch 96 个 `.rs`**：未复跑。我按要求用**停用新测试**的方法复现基线，
  两者得到同一读数；但实现者这条路径本身未被观察。
- **`godot-mcp/**` 全树最新 mtime `1790650641.240421`**：未复现（全树遍历代价过大）。我只查了
  `godot-mcp/godot/bin`（最新 `1790641863.43`）与嵌套仓 `porcelain` 空；引擎树内被忽略文件的写入不在我的覆盖内。
- **引擎自身的 `--version` 未重跑**（硬约束：离线、不起引擎）。`035edfce7` 依赖冻结轮次记录与在盘二进制的
  size/sha/mtime 一致性。
- **"保留全部 mtime 的写入"不可见**：`runs/**` 与 `.workspace/**` 的零写入由"最新 mtime + 文件数前后相等"支撑，
  没有文件系统审计轨迹。

## 5. 我故意没查的

- 未起引擎、未跑轮、未联网、未调 MCP/模型端点（硬约束）。
- 未改任何真实历史报告、任何工作区、`PRD-mario.md`、`DECISIONS.md`、`godot-mcp/**`；所有篡改在仓外副本上做；
  未对任何路径用 `rm -rf`；未从未展开变量构造路径；未 stage、未 commit、未 push。
- 未核对 T13 证据索引的其余 57 行（只核了本批触及的 `cite_check.txt` 与 `machine_block.json` 两行）。
- 未重推 E1..E6、A0/A1 树摘要、十条只读基线、工具普查。
- 未逐对 diff `*.redacted.json` sidecar，未审 177 个工具 schema 与点到之外的 Rust 运行时。

## 6. 对报告自身"未验证清单"与同族陈旧登记的裁决

| 报告的说法 | 我的裁决 |
|---|---|
| 未起引擎/未跑轮/未联网 | **成立**（我也是） |
| 引擎 `--version` 未重跑 | **成立**；但 8 轮 `meta.json` + `prerun_state.txt` + 在盘二进制三方一致，身份判据可接受 |
| `runs/**` 零写入由 mtime 判据 | **成立且已复现**；我两轮全套前后读数完全相同 |
| 三个钉由同一实现者计算 | **已由本次验收关闭**：每一条钉、每个变异我都独立重算 |
| 同族陈旧：`DESIGN-DETAIL.md:1508/1587`、`TASK-DR41-IMPL.md:39/140` 仍是 `ba1587c71` | **登记准确**（我逐行读过） |
| 同族陈旧：`TASK-DR79-REPORT.md:36` 仍是 25,908/816 | **实质准确**，但**引文形式不准确**（该行写 `回包 25908/816 B`，见 A-1） |
| 同族陈旧：冻结件 `round_facts.txt:160` 仍写 10/13 | **准确**（我读过） |

## 7. 给下一批的建议

1. **修 A-1**：把 F-3/risks[2] 里那句引号改成逐字引用（`回包 25908/816 B`）或明确标为转述——追加式。
2. **扩大守卫覆盖面（A-2）**：给 `TASK-SMOKE-T8-REPORT.md`、`TASK-SMOKE-T10-ACCEPTANCE.md`、`TASK-DR76-REPORT.md`
   也各钉一条"勘误 heading 之前的字节前缀 seal"（其它报告若收益低可只登记）。顺带给**本批报告自己的机器块**
   加一条钉，使"验收报告一旦被就地改写"也能被机械发现。
3. **给守卫补一条"钉值 > 0/非空"的自检**：目前"改钉值 + 改文件"这对攻击不可测；至少把钉值与该文件在 git 中的
   历史 blob 做一次交叉断言（例如读 `git show` 与 seal 前缀比对），把"此后不可静默改写"升级为"与历史一致"。
4. **裁定 `TASK-DR79-ACCEPTANCE.md` D-1 的复现命令**（`rstrip` → `strip`）：它是冻结文本，按 D289 只能追加更正。
5. **登记 `TASK-DR80-REPORT.md` 机器块的两处状态漂移**（head `c2780bc` → `3e727b9`、tracked `.rs` 96 → 97），
   或在下一份报告里显式写明"该块是收尾时点快照"。
6. 若之后还要"清同族陈旧"，建议一次显式划定范围（`DESIGN-DETAIL.md`、`TASK-DR41-IMPL.md`、`DR79-REPORT.md:36`、
   冻结件 `round_facts.txt:160`），避免每次都靠"登记不改"累积。

<!-- TASK-DR80-ACCEPTANCE self-check: one line-anchored ```json block; produced by json.dumps(obj, ensure_ascii=False, indent=2); json.loads before writing and after writing both PASS; round_trip_equal=True top_keys=13 block_utf8_bytes=26858 verdict=pass criteria=18 defects=3 risks=6 unverified=6 -->
