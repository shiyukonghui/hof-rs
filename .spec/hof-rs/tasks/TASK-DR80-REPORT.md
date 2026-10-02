```json
{
  "task": "TASK-DR80",
  "kind": "wrap-up batch: clear the OA-2 root temporaries, annotate the OA-4 engine-string discrepancy additively, correct the DR-79 erratum's two probe byte figures and one stale index hash, and make the append-only rule mechanical (offline; no engine; no round; runs/** read-only)",
  "adjudicated_by": "implementation subagent, no upstream context; every number below was produced by its own read-only commands or by the gate run recorded here",
  "repo_state_at_close": {
    "head": "c2780bc391c25dfd4243583947879f47f5a2df3e",
    "origin_master": "8ddbad3f4db43c28be158c17ad0678fe4d77857c",
    "pushed": false,
    "staged_files": [],
    "git_status_porcelain": [
      " M .spec/hof-rs/REQUIREMENTS.md",
      " M .spec/hof-rs/tasks/TASK-SMOKE-T13-REPORT.md",
      "?? tests/append_only_guard.rs",
      "?? .spec/hof-rs/tasks/TASK-DR80-REPORT.md"
    ],
    "git_status_note": "this report is itself the fourth porcelain entry; the list above was captured by the gate before the report existed and the report line is appended for completeness",
    "git_diff_name_status": [
      "M\t.spec/hof-rs/REQUIREMENTS.md",
      "M\t.spec/hof-rs/tasks/TASK-SMOKE-T13-REPORT.md"
    ],
    "deleted_or_renamed_tracked": [],
    "committed_by_this_batch": false,
    "commit_note": "this batch did not commit: every earlier implementer batch closed with its work uncommitted and the dispatcher committed afterwards (DR-79's work was committed as ec90c19 together with D293 and the acceptance), so committing here would break that split. HEAD is still c2780bc and origin/master is still 8ddbad3f."
  },
  "item1_root_temporaries": {
    "what": "the three untracked root files the T13 round wrote out of tree (OA-2), recorded and then removed with three explicit os.remove calls -- no rm -rf, no wildcard, no recursive delete",
    "before": [
      {
        "path": ".tmp_coin.json",
        "exists": true,
        "bytes": 108,
        "sha256": "ce741bfa7e5c5f46ad23c324a239ff570610b5d61e27ab4db51e0475c8ffaa89",
        "content": "{\"path\":\"Coin1\",\"properties\":[\"monitoring\",\"monitorable\",\"collision_layer\",\"collision_mask\",\"position\"]}  \r\n",
        "mtime_unix": 1790887948.9697561,
        "git_porcelain": "?? .tmp_coin.json"
      },
      {
        "path": ".tmp_goal.json",
        "exists": true,
        "bytes": 68,
        "sha256": "47ebe914185d422997e8f948cf2e742c9ab1c4327fd27c60bb268365e3446b07",
        "content": "{\"path\":\"Goal\",\"properties\":[\"reached\",\"monitoring\",\"position\"]}  \r\n",
        "mtime_unix": 1790887949.0608892,
        "git_porcelain": "?? .tmp_goal.json"
      },
      {
        "path": ".tmp_hud.json",
        "exists": true,
        "bytes": 46,
        "sha256": "ec3876325a2f6bd96f26449246705597caeeb4b995edf84ce9eeebe532725fa2",
        "content": "{\"path\":\"HUD/Coins\",\"properties\":[\"text\"]}  \r\n",
        "mtime_unix": 1790887949.123736,
        "git_porcelain": "?? .tmp_hud.json"
      }
    ],
    "removed": [
      ".tmp_coin.json",
      ".tmp_goal.json",
      ".tmp_hud.json"
    ],
    "after": [
      {
        "path": ".tmp_coin.json",
        "exists": false
      },
      {
        "path": ".tmp_goal.json",
        "exists": false
      },
      {
        "path": ".tmp_hud.json",
        "exists": false
      }
    ],
    "git_status_before": [
      "?? .tmp_coin.json",
      "?? .tmp_goal.json",
      "?? .tmp_hud.json"
    ],
    "git_status_after": [],
    "disclosure_note": "the existence of the three files is already on record in DECISIONS.md D293, in the T13 report's E-6 erratum and in runs/smoke-t13/iter-1/result.json out_of_tree_writes, so deleting them destroys no unique evidence"
  },
  "item2_requirements_note": {
    "document": ".spec/hof-rs/REQUIREMENTS.md",
    "original_sentence_kept_verbatim": true,
    "original_sentence": "实测版本串 `4.8.dev.mono.custom_build.ba1587c71`（构建于 anchor `ba1587c71`）",
    "c3_row_untouched": "REQUIREMENTS.md line 58 is a byte-identical prefix of the 20,904-byte file that existed before this batch; the REQ seal below is computed over the bytes before the appended heading and is 20,910 bytes because the append is preceded by `\\n---\\n\\n`",
    "measured_engine_string": "4.8.dev.mono.custom_build.035edfce7",
    "engine_binary": {
      "sha256": "08483088a4a2772841cd3b4c916b2d45b3cb6255656cf3951598a86fce7e9e6a",
      "size_bytes": 194216960,
      "mtime_unix": 1790641862
    },
    "explanation": "the discrepancy is not a typo: the engine binary was replaced before smoke-t7 (T6 build ba1587c71 / sha 25d29eb4 / 194,207,744 B -> T7+ build 035edfce7 / sha 08483088 / 194,216,960 B, per TASK-SMOKE-T7-REPORT.md line 387) and C3 was not updated then; the objective text itself (OBJECTIVE-COMPLETION.md line 11) names 035edfce7, and every round book marks the --version string as the criterion",
    "append_evidence": {
      "target": ".spec/hof-rs/REQUIREMENTS.md",
      "before_bytes": 20904,
      "before_sha256": "5ba8d91418ddfe320f222c94e72abf201075586fe69bac2c33c90f9946bc90b1",
      "appended_bytes": 5587,
      "appended_sha256": "038d4bf52222fda4841640257578304b1633041af70b1d2164e9e476ba75ef10",
      "after_bytes": 26491,
      "after_sha256": "298a948929a434a91b9088f4d566b7e387d0cfeb270f86a79d88b006821e0e54",
      "prefix_identical": true,
      "after_crlf": 0,
      "after_lf": 315,
      "heading_offset": 20910,
      "prefix_len_before_heading": 20910,
      "prefix_sha_before_heading": "7b551ca08c4c5abf15a95cb8edcc4977ce8d03c649654ab4a5ab01f649cae5ae"
    },
    "evidence_files": [
      "runs/smoke-t11/meta.json",
      "runs/smoke-t12/meta.json",
      "runs/smoke-t13/meta.json",
      "runs/smoke-t11/evidence/round/prerun_state.txt"
    ],
    "still_stale_same_family": [
      ".spec/hof-rs/DESIGN-DETAIL.md lines 1508, 1587",
      ".spec/hof-rs/tasks/TASK-DR41-IMPL.md lines 39, 140"
    ]
  },
  "item3_probe_byte_figures": {
    "wrong_sentence": "TASK-SMOKE-T13-REPORT.md line 1548 (DR-79 erratum E-1): `tools/list`（25,908 B 回包）与 `running_game_get_scene_tree`（816 B）",
    "reply_payloads": {
      "tools_list": {
        "bytes": 31202,
        "sha256": "980830d3008d07005266e9757b6dc98ef9e5637e0f635be6ee5d59694d042519"
      },
      "scene_tree": {
        "bytes": 589,
        "sha256": "7b80dcbe985349419701caa391b0e55725c9816e4163bd65cb92c66ba09e7d85"
      }
    },
    "file_sizes": {
      "tools_list": {
        "bytes": 31360,
        "sha256": "246a442369259a5db9dce89a82f697d3dd9a8cacd8d6f384436c25049360164b"
      },
      "scene_tree": {
        "bytes": 816,
        "sha256": "302ac4ef6bfca3d29b1f5d9d12a4b19f954dae42fedfacc10fefa443fa8aebb6"
      }
    },
    "between_markers": {
      "tools_list": 31204,
      "scene_tree": 591
    },
    "third_number_warning": "the capture wraps each reply in `---- raw reply begin ----` / `---- raw reply end ----` with one leading and one trailing LF, so three different counts are all true and must not be mixed: file 31,360 / 816, span between markers 31,204 / 591, reply payload 31,202 / 589",
    "does_25908_match_anything": {
      "under_runs_smoke_t13": [],
      "under_all_of_runs": [
        "runs/playability/PlayJev-src/demo/replays/2048/playjev-0.8b-sft_all1_d1_5012.js"
      ],
      "verdict": "25,908 B matches no artifact of this round and neither reading of either probe; the only 25,908-byte file anywhere under runs/** belongs to an unrelated data tree (runs/playability/...), which is stated rather than generalised away"
    },
    "append_evidence": {
      "target": ".spec/hof-rs/tasks/TASK-SMOKE-T13-REPORT.md",
      "before_bytes": 134079,
      "before_sha256": "c60b5ed9f36004453726a34595ee6a22df71f7f6f69f666c6b3183f47e267638",
      "appended_bytes": 9532,
      "appended_sha256": "237683171bde439b6f4d50808b626101dc4925d3deaef299069671839225f7e1",
      "after_bytes": 143611,
      "after_sha256": "4f32174f6d332cd57e7bffb7def94876c355c7e7fd62147f28ab0a8cbd5c7755",
      "prefix_identical": true,
      "after_crlf": 0,
      "after_lf": 1973,
      "dr80_heading_offset": 134085,
      "seal_len": 134085,
      "seal_sha256": "2f2a2418bc3d0785ec47235da7c868ee64f590e73b38f3e3c7619696d74945a9",
      "dr79_heading_offset": 107709,
      "dr79_prefix_sha256": "9bbe81c8360d481ef01528f99467cd1253921ff713980336da05a32e3ea9fd36"
    }
  },
  "item4_index_hash": {
    "wrong_row": "TASK-SMOKE-T13-REPORT.md line 1485: `cite_check.txt` | 18189 | `4bbce1a00a26101c`",
    "partially_corrected_by": "DR-79 erratum E-4e (line 1691) fixed the size to 18,401 and explicitly left the sha unchecked",
    "correct": {
      "bytes": 18401,
      "sha256": "21f071f5e0c7ef5ee7374848293f2297f3270207a6bf046b88d97fd506ab455a"
    },
    "recompute_command": "python -c \"import hashlib;b=open('runs/smoke-t13/evidence/analysis/cite_check.txt','rb').read();print(len(b), hashlib.sha256(b).hexdigest())\""
  },
  "guard": {
    "file": "tests/append_only_guard.rs",
    "file_sha256": "e6d0df069ae23396111d1e7b8ac7307256f77d3beb48b0013b9212519b7ad3a9",
    "file_bytes": 19372,
    "tests": 6,
    "pins": {
      "t13_pre_dr79_erratum": {
        "heading": "# 附：DR-79 勘误（**追加式**，2026-10-02）",
        "prefix_bytes": 107709,
        "prefix_sha256": "9bbe81c8360d481ef01528f99467cd1253921ff713980336da05a32e3ea9fd36"
      },
      "t13_pre_dr80_correction": {
        "heading": "# 附：DR-80 更正（**追加式**，2026-10-02）",
        "prefix_bytes": 134085,
        "prefix_sha256": "2f2a2418bc3d0785ec47235da7c868ee64f590e73b38f3e3c7619696d74945a9"
      },
      "t13_machine_readable_block": {
        "bytes": 34699,
        "sha256": "36e34d0d0436920605fb3f06065c1c8e4303bbf90b92a499d5e37f6f8d6c3c9f",
        "identity": "byte-equal to runs/smoke-t13/evidence/analysis/machine_block.json"
      },
      "dr73_pre_correction_ledger": {
        "heading": "## 12. DR-76 更正台账（**superseded 标注**，2026-10-01 由 DR-76 追加）",
        "prefix_bytes": 48811,
        "prefix_sha256": "db0a5a7a5c2086b46250582748fd08a27c7764d5f935922655acc4658da1543c",
        "surviving_markers": [
          "<!-- DR-77-COMMIT-QUOTE-BEGIN -->",
          "<!-- DR-77-COMMIT-QUOTE-END -->",
          "<!-- DR-77-INCORRECT-QUOTE-BEGIN -->",
          "<!-- DR-77-INCORRECT-QUOTE-END -->"
        ]
      },
      "requirements_pre_dr80_note": {
        "heading": "# DR-80 注（追加式，2026-10-02）",
        "prefix_bytes": 20910,
        "prefix_sha256": "7b551ca08c4c5abf15a95cb8edcc4977ce8d03c649654ab4a5ab01f649cae5ae",
        "also_asserts": "C3's sentence is present verbatim and the measured string 035edfce7 is named"
      }
    },
    "test_names": [
      "the_t13_report_prefix_before_the_dr79_erratum_is_frozen",
      "the_t13_report_prefix_before_the_dr80_correction_is_frozen",
      "the_t13_machine_readable_block_is_byte_frozen",
      "the_dr73_report_prefix_before_its_correction_ledger_is_frozen",
      "the_requirements_document_keeps_c3_and_carries_the_dr80_note",
      "the_seal_checks_redden_on_temporary_copies"
    ],
    "first_red": "written before either append: 2 failed / 4 passed -- the requirements note test and the DR-80 seal test were red because the documents did not yet carry the appended material; after the two appends and the pin update the same six tests are green",
    "design": "a marker that owns a whole line, a byte-prefix length+sha256 seal, and (for the round report) an independent line-anchored json-block length+sha256 pin, so appending after the seal is allowed while any edit at or before it is red"
  },
  "plants": {
    "report_plants_on_temporary_copies": {
      "method": "three copies of the three documents under C:/Users/wyl/AppData/Local/Temp/dr80/plants-<stamp>/, each mutated differently, compiled with `CARGO_MANIFEST_DIR=<copy> rustc --test tests/append_only_guard.rs` and run; the real reports were never written and their sha256 is identical before and after the campaign",
      "real_files_unchanged": true,
      "control": {
        "mutant_sha256": "4f32174f6d332cd57e7bffb7def94876c355c7e7fd62147f28ab0a8cbd5c7755",
        "mutant_bytes": 143611,
        "test_binary_exit": 0,
        "failed_tests": [],
        "passed_tests": [
          "the_dr73_report_prefix_before_its_correction_ledger_is_frozen",
          "the_requirements_document_keeps_c3_and_carries_the_dr80_note",
          "the_seal_checks_redden_on_temporary_copies",
          "the_t13_machine_readable_block_is_byte_frozen",
          "the_t13_report_prefix_before_the_dr79_erratum_is_frozen",
          "the_t13_report_prefix_before_the_dr80_correction_is_frozen"
        ],
        "test_result": [
          "test result: ok. 6 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.05s"
        ]
      },
      "in_place_edit": {
        "mutant_sha256": "25af9e04c47a846eeb100ada35383d7d714e5edb4d274c7565c9f8383e22140d",
        "mutant_bytes": 143611,
        "test_binary_exit": 101,
        "failed_tests": [
          "the_seal_checks_redden_on_temporary_copies",
          "the_t13_report_prefix_before_the_dr79_erratum_is_frozen",
          "the_t13_report_prefix_before_the_dr80_correction_is_frozen"
        ],
        "passed_tests": [
          "the_dr73_report_prefix_before_its_correction_ledger_is_frozen",
          "the_requirements_document_keeps_c3_and_carries_the_dr80_note",
          "the_t13_machine_readable_block_is_byte_frozen"
        ],
        "test_result": [
          "test result: FAILED. 3 passed; 3 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.07s"
        ]
      },
      "line_deletion": {
        "mutant_sha256": "fcafb1573b36f37298eb564b4fc70d0d0c1b6cd63ccc9af46e274b3b8b1a0ecb",
        "mutant_bytes": 143549,
        "test_binary_exit": 101,
        "failed_tests": [
          "the_seal_checks_redden_on_temporary_copies",
          "the_t13_report_prefix_before_the_dr79_erratum_is_frozen",
          "the_t13_report_prefix_before_the_dr80_correction_is_frozen"
        ],
        "passed_tests": [
          "the_dr73_report_prefix_before_its_correction_ledger_is_frozen",
          "the_requirements_document_keeps_c3_and_carries_the_dr80_note",
          "the_t13_machine_readable_block_is_byte_frozen"
        ],
        "test_result": [
          "test result: FAILED. 3 passed; 3 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.04s"
        ]
      },
      "machine_block_edit": {
        "mutant_sha256": "85ad090b33a9555bd767d8857e5d8c87d82ee5a287011ddf0618a4f602b6f77e",
        "mutant_bytes": 143611,
        "test_binary_exit": 101,
        "failed_tests": [
          "the_seal_checks_redden_on_temporary_copies",
          "the_t13_machine_readable_block_is_byte_frozen",
          "the_t13_report_prefix_before_the_dr79_erratum_is_frozen",
          "the_t13_report_prefix_before_the_dr80_correction_is_frozen"
        ],
        "passed_tests": [
          "the_dr73_report_prefix_before_its_correction_ledger_is_frozen",
          "the_requirements_document_keeps_c3_and_carries_the_dr80_note"
        ],
        "test_result": [
          "test result: FAILED. 2 passed; 4 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.05s"
        ]
      },
      "reading": "each mutant drives the guard test binary to exit 101; the block edit is the only one that additionally reddens `the_t13_machine_readable_block_is_byte_frozen`, while the two outside-block mutants leave that test green -- so the block pin is a separate check, not the prefix check counted twice"
    },
    "code_plants_with_byte_exact_restore": {
      "method": "the guard test file itself was mutated, `cargo test --test append_only_guard` was run, and the original bytes were written back and re-hashed",
      "original_sha256": "e6d0df069ae23396111d1e7b8ac7307256f77d3beb48b0013b9212519b7ad3a9",
      "plants": [
        {
          "plant": "P-A: a wrong machine-block pin must redden the block test",
          "planted_sha256": "d85c46314e001e776c4278e3124900954378de829ac369d00279b3a7fa747bac",
          "exit_code": 101,
          "failed_tests": [
            "the_seal_checks_redden_on_temporary_copies",
            "the_t13_machine_readable_block_is_byte_frozen"
          ],
          "expected_test_red": true,
          "restored_sha256": "e6d0df069ae23396111d1e7b8ac7307256f77d3beb48b0013b9212519b7ad3a9",
          "restored_byte_exact": true
        },
        {
          "plant": "P-B: a wrong DR-73 seal length must redden the DR-73 test",
          "planted_sha256": "ec081022c0ecc834139c7f77b139b50105c20c005feb45b243a76c1b91ba6e9b",
          "exit_code": 101,
          "failed_tests": [
            "the_dr73_report_prefix_before_its_correction_ledger_is_frozen"
          ],
          "expected_test_red": true,
          "restored_sha256": "e6d0df069ae23396111d1e7b8ac7307256f77d3beb48b0013b9212519b7ad3a9",
          "restored_byte_exact": true
        },
        {
          "plant": "P-C: a blinded seal check must redden the non-vacuity test",
          "planted_sha256": "234a50957d1171b6a9f190cefae2da626df4474c47b1346feb6276dc5d9b451d",
          "exit_code": 101,
          "failed_tests": [
            "the_seal_checks_redden_on_temporary_copies"
          ],
          "expected_test_red": true,
          "restored_sha256": "e6d0df069ae23396111d1e7b8ac7307256f77d3beb48b0013b9212519b7ad3a9",
          "restored_byte_exact": true
        }
      ]
    }
  },
  "gate": {
    "baseline": {
      "suites": 59,
      "passed": 554,
      "failed": 0,
      "ignored": 7,
      "listed": 561,
      "exit_code": 0,
      "seconds": 1026.9
    },
    "final": {
      "suites": 60,
      "passed": 560,
      "failed": 0,
      "ignored": 7,
      "listed": 567,
      "exit_code": 0,
      "seconds": 979.1
    },
    "baseline_method": "reproduced, not assumed: tests/append_only_guard.rs was renamed to a non-.rs name inside tests/ (cargo auto-discovers tests/*.rs only), the stale target/debug/.fingerprint/hof-rs-* directories were removed with Python's glob and shutil.rmtree, and the suite was run; the file was then restored and its sha256 re-verified",
    "baseline_file_restored_byte_exact": true,
    "final_method": "fingerprints cleared again, then all 96 tracked *.rs files touched one at a time from `git ls-files '*.rs'` (no shell wildcard), so the rebuild was forced per file",
    "fingerprints_cleared": [
      61,
      60
    ],
    "tracked_rs_touched": 96,
    "fmt": {
      "exit_code": 0,
      "stdout": "",
      "stderr": ""
    },
    "ignored_count_baseline": 7,
    "ignored_count_final": 7,
    "removed_tests": 0,
    "added_test_names": [
      "append_only_guard::the_t13_report_prefix_before_the_dr79_erratum_is_frozen",
      "append_only_guard::the_t13_report_prefix_before_the_dr80_correction_is_frozen",
      "append_only_guard::the_t13_machine_readable_block_is_byte_frozen",
      "append_only_guard::the_dr73_report_prefix_before_its_correction_ledger_is_frozen",
      "append_only_guard::the_requirements_document_keeps_c3_and_carries_the_dr80_note",
      "append_only_guard::the_seal_checks_redden_on_temporary_copies"
    ],
    "arithmetic": "final 560 passed / 567 listed = baseline 554 / 561 + exactly the six new tests; 7 ignored before and after"
  },
  "zone_selfcheck": {
    "runs_newest_mtime": 1790889780.483188,
    "runs_newest_path": "runs/smoke-t13/evidence/analysis/cite_check.txt",
    "runs_files": 6586,
    "runs_written_by_this_batch": false,
    "workspace_newest_mtime": 1790888643.0617301,
    "workspace_newest_path": ".workspace/fresh-t13/.godot/editor/editor_layout.cfg",
    "workspace_files": 492,
    "workspace_written_by_this_batch": false,
    "godot_mcp_newest_mtime": 1790650641.240421,
    "nested_engine_head": "fc63af77c33368c4a1bb839c95d19750554f63a3",
    "nested_engine_porcelain_lines": 0,
    "frozen_files": {
      "prd_mario_sha256": "4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a",
      "decisions_sha256": "5621b2eaf8cbb36a81d4ed3d4257605c703bbfff0e137c698fcc7fd78e593e69",
      "cargo_toml_sha256": "e0c4992bd828729b8514f9cf694925687b726157d45463a636390081a3dadba1",
      "cargo_lock_sha256": "d98fa91565ec72ae998fd9f6fd3838286e287e4baf8020c5114a1e2ac0bfdb36"
    },
    "frozen_expected": {
      "prd_mario_sha256": "4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a",
      "decisions_sha256": "5621b2eaf8cbb36a81d4ed3d4257605c703bbfff0e137c698fcc7fd78e593e69"
    },
    "new_dependencies": false,
    "cargo_toml_unchanged": true,
    "cargo_lock_unchanged": true,
    "repo_temporary_files_left_behind": [],
    "tracked_rs_line_endings": {
      "lf": 88,
      "crlf": 8,
      "mixed": 0,
      "tracked": 96
    },
    "new_test_file_line_endings": {
      "crlf": 0,
      "lf": 485
    },
    "pre_existing_tracked_oddity_untouched": "%DST% (7 tracked files from 51f9987, 2026-10-01 16:03) remains exactly as it was",
    "forbidden_operations": {
      "rm_rf_used": false,
      "unexpanded_variable_path_built": false,
      "powershell_raw_read_write_pair_used": false,
      "line_endings_rewritten": false,
      "pushed": false
    }
  },
  "touched_documents": {
    ".spec/hof-rs/tasks/TASK-SMOKE-T13-REPORT.md": {
      "bytes": 143611,
      "sha256": "4f32174f6d332cd57e7bffb7def94876c355c7e7fd62147f28ab0a8cbd5c7755",
      "crlf": 0,
      "lf": 1973
    },
    ".spec/hof-rs/REQUIREMENTS.md": {
      "bytes": 26491,
      "sha256": "298a948929a434a91b9088f4d566b7e387d0cfeb270f86a79d88b006821e0e54",
      "crlf": 0,
      "lf": 315
    },
    ".spec/hof-rs/tasks/TASK-DR73-REPORT.md": {
      "bytes": 55277,
      "sha256": "5dcaac4a60b0558c1d42e6117b738eb1979af5493e7eaaea36dcdbaf3ee1b495",
      "crlf": 0,
      "lf": 738
    },
    "tests/append_only_guard.rs": {
      "bytes": 19372,
      "sha256": "e6d0df069ae23396111d1e7b8ac7307256f77d3beb48b0013b9212519b7ad3a9",
      "crlf": 0,
      "lf": 485
    }
  },
  "risks": [
    "The guard pins the two reports and the requirements document at their current bytes. Any future additive correction must add a new seal constant above the new heading and extend the table in TASK-SMOKE-T13-REPORT.md F-4; a naive append without updating the constants is fine (the seal is before the newest heading) but a new correction heading placed before an existing seal would redden the guard.",
    "The seal is a byte prefix, so it cannot distinguish a rewritten line ending from a rewritten character inside the sealed region -- both are red, which is the intent, but the failure message only reports a sha256 mismatch.",
    "TASK-DR79-REPORT.md line 36 still carries the wrong `25,908 B reply` figure (out of the task book's scope, registered in F-3), and DESIGN-DETAIL.md lines 1508/1587 plus TASK-DR41-IMPL.md lines 39/140 still record the superseded ba1587c71 engine string.",
    "The frozen analysis product runs/smoke-t13/evidence/analysis/round_facts.txt line 160 still says verified-only 10 / gap-only 13 (D-4); runs/** is read-only here, so it stays.",
    "The three temp-copy plants also redden the non-vacuity test, because that test requires the read to satisfy the guard before it is asked to reject mutants; in a mutated tree it fails for that prior reason. The mutated environment is not the repository, so this is disclosed rather than repaired.",
    "The guard reads the working tree, not a git object, so it protects against edits from now on; it cannot detect a rewrite that happened before its pins were computed."
  ],
  "unverified": [
    "No engine was started, no round was run, no MCP or model endpoint was called, and the network was not used (hard constraint); every reading above is a read-only recomputation of frozen artifacts or a local build/test run.",
    "The engine binary's own --version output was not re-executed here: the measured string is taken from the frozen round records (meta.json and prerun_state.txt), which the task book itself names as the evidence files.",
    "The writes to runs/** are checked by mtime (newest 1790889780 = 2026-10-02 05:23:00, hours before this batch started) rather than by a filesystem audit trail; a write that preserved every mtime would not be visible.",
    "The pins were computed by the same agent that wrote them, so the guard's correctness rests on the recomputable commands quoted in the report and in the appended sections, not on an independent reviewer's reproduction."
  ],
  "honest_disclosure": [
    "The three report plants were performed on temporary copies, not on the real reports: the task book forbids modifying the real reports, so a literal byte-exact restore on them was not available. The real reports' sha256 is identical before and after the campaign, and the code plants do carry the byte-exact restore evidence.",
    "The first run of the non-vacuity test failed for a wrong reason (my selector looked for a `| C1 ` row that the report does not have); it was fixed to select the first markdown table row, and the red-then-green history of the other five tests is unaffected.",
    "The guard was not the first artefact written: the pins for the two pre-existing seals were computed before the appends, but the DR-80 seal and the requirements seal could only be computed after their documents were appended, so those two constants were updated once after the appends -- an honest departure from strict test-first that the red run above records.",
    "This batch did not commit, did not stage and did not push; the working tree carries the two modified documents, the newly appended material and the new untracked test file.",
    "No `rm -rf` was used anywhere. The only recursive removal was Python's shutil.rmtree over an enumerated glob of target/debug/.fingerprint/hof-rs-* (61 then 60 directories), which is what the task book prescribes; the three root temporaries were removed with three explicit os.remove calls."
  ]
}
```

<!-- TASK-DR80-REPORT self-check: the json block above is produced by
     json.dumps(obj, ensure_ascii=False, indent=2), written to disk, and read back with a fence-aware
     json.loads; the read-back result is printed in the self-check line after this comment. -->

# TASK-DR80-REPORT — 收尾批：清残留、修文档串差异、更正勘误里两个错数与旧哈希、加**机械化的"仅追加"守卫**

> 实现子代理报告（无上游对话上下文）。**离线**：不起引擎、不跑真机轮、不联网；`runs/**` 与 `.workspace/**`
> **零写入**（含"写过再删"）。脚本与临时产物全部在**仓外**
> `C:\Users\wyl\AppData\Local\Temp\dr80\**`。**未对任何路径用 `rm -rf`**；**未从未展开变量构造路径**；
> 未用 PowerShell 的 `Get-Content -Raw`+`Set-Content`；**未整文件重写行尾**；未 stage、未 commit、未 push。

## 0. 结论

五项全部落地：① 仓根三个 `.tmp_*.json` 先取证再删除（双向证据）；② `REQUIREMENTS.md` 追加"DR-80 注"，
C3 原句逐字保留并标注 `superseded`；③ DR-79 勘误里两个错数按"**回包载荷** / **文件大小**"分开更正；
④ 证据索引行的旧哈希更正并给复算命令；⑤ 新增 `tests/append_only_guard.rs`，把"仅追加"从纪律变成**机械守卫**，
并用 3 处**临时副本**植入（就地改写 / 删行 / 块内改写）各自让该测试**红**，另有 3 处代码植入逐字节回退。

**门**：`cargo test --offline` **exit 0**；**基线自行复现** = **554 / 0 / 7**（59 套件，`--list` **561**）；
**终态** = **560 / 0 / 7**（60 套件，`--list` **567**）——差值恰好是新增的 6 条测试；**无测试名被删**；
`ignored` **7 → 7 不变**；`cargo fmt --check` **exit 0 且无输出**；逐文件 touch **96** 个 `git ls-files '*.rs'`。

## 1. ① 仓根三个残留文件：删除前摘要 + 删除后不存在

T13 轮 Developer 越界写入的 `.tmp_coin.json` / `.tmp_goal.json` / `.tmp_hud.json`
（`result.json.out_of_tree_writes` 逐字列过，`DECISIONS.md` D293 与 T13 报告 E-6 均有留档）。

**删除前（内容摘要 + sha256 + size + mtime）**：

| 路径 | 字节 | sha256 | mtime（unix） | 内容 |
|---|---|---|---|---|
| `.tmp_coin.json` | 108 | `ce741bfa7e5c5f46ad23c324a239ff570610b5d61e27ab4db51e0475c8ffaa89` | 1790887948.9698 | `{"path":"Coin1","properties":["monitoring","monitorable","collision_layer","collision_mask","position"]}  \r\n` |
| `.tmp_goal.json` | 68 | `47ebe914185d422997e8f948cf2e742c9ab1c4327fd27c60bb268365e3446b07` | 1790887949.0609 | `{"path":"Goal","properties":["reached","monitoring","position"]}  \r\n` |
| `.tmp_hud.json` | 46 | `ec3876325a2f6bd96f26449246705597caeeb4b995edf84ce9eeebe532725fa2` | 1790887949.1237 | `{"path":"HUD/Coins","properties":["text"]}  \r\n` |

**删除方式**：三个**显式** `os.remove(...)`（Python），**不是** `rm -rf`、**不是**通配符、**不是**递归删除。
**删除后**：`ls` 三个路径全部 `No such file or directory`；`exists=False` ×3；
`git status --porcelain -uall` **输出为空**（此前是三行 `??`）。
**安全性**：删除没有销毁唯一证据——三文件的存在事实已在 `DECISIONS.md D293`、T13 报告 E-6 勘误与
`runs/smoke-t13/iter-1/result.json` 的 `out_of_tree_writes` 中留档，且本报告把 sha256 与内容一并冻结。

## 2. ② `REQUIREMENTS.md` 的引擎串差异：追加式注明

**原句（C3，第 58 行）逐字保留、一字未改**，只在文末追加 `# DR-80 注（追加式，2026-10-02）`：

- 追加**前** 20,904 B / `5ba8d91418ddfe320f222c94e72abf201075586fe69bac2c33c90f9946bc90b1`；
- 追加 **5,587 B**；追加**后** 26,491 B / `298a948929a434a91b9088f4d566b7e387d0cfeb270f86a79d88b006821e0e54`；
- **`after[:before] == before` 为 True**（纯 `ab` 模式追加，旧字节不可能移动）；行尾统计 `crlf=0 / lf=315`；
- 注的 heading 起于字节 **20,910**（前 6 字节是 `\n---\n\n`），该前缀 sha256 =
  `7b551ca08c4c5abf15a95cb8edcc4977ce8d03c649654ab4a5ab01f649cae5ae` —— 这就是守卫的 REQ seal。

注里写明的事实：C3 的 `4.8.dev.mono.custom_build.ba1587c71` 与 **t11/t12/t13 三轮实测的
`4.8.dev.mono.custom_build.035edfce7`** 不一致；**差异不是笔误**——引擎二进制在 T7 之前被换过
（T6 `ba1587c71` / sha `25d29eb4…` / 194,207,744 B → T7 起 `035edfce7` / sha `08483088…` / 194,216,960 B，
逐字见 `TASK-SMOKE-T7-REPORT.md` 第 387 行「变了：换到含 TASK-151 修复的构建」），C3 当时没有随之更新；
证据文件是三轮 `meta.json` 的 `.engine.version_string` 与 `runs/smoke-t11/evidence/round/prerun_state.txt`
第 20/21/23/24 行；**判据(1) 以实测串 `035edfce7` 为准**（目标原文 `OBJECTIVE-COMPLETION.md` 第 11 行点的就是该串，
每轮任务书也把 `--version` 串标为判据、sha256 只作记录）。同族的 `DESIGN-DETAIL.md:1508/1587`、
`TASK-DR41-IMPL.md:39/140` 只在注里**登记**，本批按任务书**不改**。

## 3. ③④ DR-79 勘误的两处更正（追加式，旧值保留并标注）

追加节为 `TASK-SMOKE-T13-REPORT.md` 的 `# 附：DR-80 更正（**追加式**，2026-10-02）`，
追加前 134,079 B / `c60b5ed9f36004453726a34595ee6a22df71f7f6f69f666c6b3183f47e267638`，
追加 **9,532 B**，追加后 143,611 B；**`after[:before] == before` 为 True**；行尾 `crlf=0 / lf=1973`。

**③ 两个错数**（原句 = 第 1548 行，逐字引用并标 `incorrect`，原文保留）：
「`tools/list`（25,908 B 回包）与 `running_game_get_scene_tree`（816 B…）」。更正后的**分开两栏**：

| 探针 | 回包载荷 | 载荷 sha256（前 16） | 文件大小 | 文件 sha256（前 16） |
|---|---|---|---|---|
| `tools/list` | **31,202 B** | `980830d3008d0700` | **31,360 B** | `246a442369259a5d` |
| `running_game_get_scene_tree` | **589 B** | `7b80dcbe98534941` | **816 B** | `302ac4ef6bfca3d2` |

即：**816 是 scene-tree 探针的文件大小，不是它的回包载荷**；**25,908 不匹配本轮任何工件**（`runs/smoke-t13`
268 个文件里无此大小者）。为不把范围说过头，我另扫了**整个 `runs/**`**：唯一的 25,908 字节文件是
`runs/playability/PlayJev-src/demo/replays/2048/playjev-0.8b-sft_all1_d1_5012.js`——另一棵数据树里的无关文件。
追加节同时记录了**第三个口径**：两标记之间的原始区间是 **31,204 / 591 B**（含捕获脚本写的一个前导与一个尾随 LF），
去换行后才是载荷 **31,202 / 589 B**，三者各有所指、不可混用。

**④ 旧哈希**（原句 = 第 1485 行 `| cite_check.txt | 18189 | 4bbce1a00a26101c |`，标 `incorrect`；
E-4e 只改了大小、明文承认哈希"未能核对"）：

`runs/smoke-t13/evidence/analysis/cite_check.txt` = **18,401 B** /
`sha256 = 21f071f5e0c7ef5ee7374848293f2297f3270207a6bf046b88d97fd506ab455a`。
复算：`python -c "import hashlib;b=open('runs/smoke-t13/evidence/analysis/cite_check.txt','rb').read();print(len(b), hashlib.sha256(b).hexdigest())"`。
追加节另登记 **D-4**（冻结件 `round_facts.txt:160` 仍写 10/13）与 **TASK-DR79-REPORT.md:36** 的同源错数——
两者都**不在**本批可写范围，登记不改。

## 4. ⑤ `tests/append_only_guard.rs`：机械化的"仅追加"守卫

先例（`tests/byte_claims.rs` 钉 DR-70 报告、`tests/dr77_evidence_tightening.rs` 钉 DR-73 报告）被推广为
**通用的仅追加性质检查**。守卫对每个文档断言：**勘误/更正 heading 必须作为整行存在**；
**该 heading 之前的字节前缀与钉住的长度 + sha256 一致**；本报告另有**独立的** ```json 机器可读块长度/sha256 钉；
DR-73 的四个 `DR-77-*` 标记必须存活；`REQUIREMENTS.md` 的 C3 原句必须逐字存活且注里给出实测串。

六条测试与钉值：

| 测试 | 文档 | 钉 |
|---|---|---|
| `the_t13_report_prefix_before_the_dr79_erratum_is_frozen` | T13 | `# 附：DR-79 勘误（…）` 前 **107,709 B** / `9bbe81c8360d481e…` |
| `the_t13_report_prefix_before_the_dr80_correction_is_frozen` | T13 | `# 附：DR-80 更正（…）` 前 **134,085 B** / `2f2a2418bc3d0785…` |
| `the_t13_machine_readable_block_is_byte_frozen` | T13 | 块 **34,699 B** / `36e34d0d04369206…`（= `machine_block.json`） |
| `the_dr73_report_prefix_before_its_correction_ledger_is_frozen` | DR-73 | `## 12. DR-76 更正台账（…）` 前 **48,811 B** / `db0a5a7a5c2086b4…` |
| `the_requirements_document_keeps_c3_and_carries_the_dr80_note` | REQUIREMENTS | heading 前 **20,910 B** / `7b551ca08c4c5abf…` + C3 原句 + `035edfce7` |
| `the_seal_checks_redden_on_temporary_copies` | — | 在**临时副本**上造三种篡改并断言守卫拒绝 |

**先红（真先红，非植入红）**：测试先写、文档后改。首次运行 `cargo test --offline --test append_only_guard`
即 **FAILED：4 passed; 2 failed**：红的是
`the_requirements_document_keeps_c3_and_carries_the_dr80_note`（注尚不存在）与
`the_t13_report_prefix_before_the_dr80_correction_is_frozen`（DR-80 heading 尚不存在）；
两条既有 seal 与块钉当时即绿（它们钉的是**已经存在**的字节）。两次追加完成后（并把 DR-80/REQ 两个 seal 常量
按追加后的真实前缀回填），六条全绿。

## 5. 植入证明

### 5.1 三处**报告**植入（在临时副本上做，真实报告零改动）

对 `TASK-SMOKE-T13-REPORT.md` 的三份**临时副本**（`C:\…\Temp\dr80\plants-<stamp>\<name>\`）分别做：
① 就地改写一个字节（第 1446 字节的 `|` → `!`）；② 删掉一行（第 1446–1507 字节的 62 字节表行）；
③ 改写机器可读块内的一个字节（偏移 66,781 的 `{` → `[`）。用
`CARGO_MANIFEST_DIR=<副本> rustc --edition 2021 --test tests/append_only_guard.rs` 编译**同一份测试源码**并运行：

| 副本 | 变异 sha256（前 8） | 测试二进制 exit | 红的测试 |
|---|---|---|---|
| **对照组（未变异）** | `4f32174f` | **0**（6 passed） | 无 |
| ① 就地改写 | `25af9e04` | **101**（3 passed / 3 failed） | 两条 seal + 非空洞性 |
| ② 删行 | `fcafb157` | **101**（3 passed / 3 failed） | 两条 seal + 非空洞性 |
| ③ 块内改写 | `85ad090b` | **101**（2 passed / 4 failed） | **块钉** + 两条 seal + 非空洞性 |

⇒ 三种篡改**各自**让守卫红（③ 额外让块测试红，①② 不惊动块测试——说明块钉是**独立**检查）。
**真实报告零改动**：`T13 / DR-73 / REQUIREMENTS` 三份真件的 sha256 在整场植入**前后完全相同**
（`4f32174f…` / `5dcaac4a…` / `298a9489…`）。

### 5.2 三处**代码**植入（真实文件 + 逐字节回退）

对守卫测试自身做植入、跑 `cargo test --offline --test append_only_guard`、回写并复核 sha256：

| 植入 | 破坏形式 | exit | 变红的测试 | 回退 |
|---|---|---|---|---|
| P-A | 把块钉的 sha256 首字符改错 | 101 | `the_t13_machine_readable_block_is_byte_frozen`（+ 非空洞性） | 逐字节一致 |
| P-B | 把 DR-73 seal 长度 `48_811` → `48_810` | 101 | `the_dr73_report_prefix_before_its_correction_ledger_is_frozen` | 逐字节一致 |
| P-C | 让 `seal_violations` 立刻返回空（守卫被蒙） | 101 | `the_seal_checks_redden_on_temporary_copies` | 逐字节一致 |

三次回退后的文件 sha256 均为 `e6d0df069ae23396111d1e7b8ac7307256f77d3beb48b0013b9212519b7ad3a9`（与植入前相同）。
⇒ 守卫的每一条钉都是**承重**的，且非空洞性测试能识破"被蒙住的守卫"。

## 6. 门

**基线（自行复现，不是假设）**：把 `tests/append_only_guard.rs` 临时改名成非 `.rs`（cargo 只自动发现 `tests/*.rs`），
用 Python 的 `glob` + `shutil.rmtree` 清掉 **61** 个 `target/debug/.fingerprint/hof-rs-*`，跑全套：

```
59 套件 · 554 passed / 0 failed / 7 ignored · EXIT=0 · --list 561
```

随后把文件按字节恢复（sha256 复核一致）。**终态**：再次清 **60** 个 fingerprint 目录，**逐文件** touch
`git ls-files '*.rs'` 的 **96** 个文件（逐条 `os.utime`，**无通配符**），跑全套：

```
60 套件 · 560 passed / 0 failed / 7 ignored · EXIT=0 · --list 567 · 979 s
cargo fmt --check → exit 0，stdout 为空
```

算术自洽：**567 − 561 = 6 = 560 − 554**，即新增的 6 条测试；`ignored` **7 → 7**；
`git diff --name-status` 只有两个 `M`（`.spec` 两份文档），**无 D、无 R**，**没有测试名被删**；
`git diff --cached --name-only` 为空（未 stage）。

## 7. 禁区自查

| 项 | 读法 | 结论 |
|---|---|---|
| `runs/**` 零写入 | 6,586 个文件中最新 mtime = `1790889780`（2026-10-02 05:23:00，`cite_check.txt`），早于本批开工（07:56） | 未动 |
| `.workspace/**` 零写入 | 492 个文件中最新 = `1790888643`（04:24:03） | 未动 |
| `godot-mcp/**` 零写入 | 最新 mtime = `1790650641`（2026-09-29）；嵌套仓 `porcelain` **0 行**，HEAD `fc63af77…` | 未动 |
| `PRD-mario.md` 逐字节冻结 | `4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a` | 未动 |
| `DECISIONS.md` 未改 | `5621b2eaf8cbb36a81d4ed3d4257605c703bbfff0e137c698fcc7fd78e593e69`（= 验收记录的值） | 未动 |
| Cargo / 依赖 | `Cargo.toml` / `Cargo.lock` 不在 diff 内；未加依赖 | 未动 |
| 未推送 | `HEAD = c2780bc391c25dfd4243583947879f47f5a2df3e`，`origin/master = 8ddbad3f…`（与开工相同），`git diff --cached` 空 | 未推送、未 stage |
| 仓内无新增临时物 | `git status -uall` 只有两份 `M` 与两个 `??`（本批的两个交付物：`tests/append_only_guard.rs` 与本报告） | 干净 |
| 行尾 | 96 个 tracked `.rs`：**88 LF / 8 CRLF / 0 mixed**（与 DR-79 记录相同）；新测试文件 **485 LF / 0 CRLF**；三个文档 **0 CRLF** | 未重写行尾 |
| 危险操作 | 全程无 `rm -rf`；无未展开变量构造路径；未用 PowerShell raw 读写对；唯一递归删除是 `glob('…/hof-rs-*')` → `shutil.rmtree`（61/60 个目录，任务书指定的做法） | 合规 |
| 既有异物 | `%DST%/`（7 个**被跟踪**文件，来自提交 `51f9987`，mtime 2026-10-01 16:03）为**本批之前**就存在的历史遗留，本批**未动** | 未动 |

## 8. 遗留风险与未验证项

- **守卫的实现边界**：seal 是"某 heading 之前的字节前缀"，所以它**允许在 seal 之后追加**，也**不能**区分
  "改写了一个字符"与"改写了行尾"（都报 sha256 不符）；`TASK-DR79-REPORT.md:36`、`DESIGN-DETAIL.md:1508/1587`、
  `TASK-DR41-IMPL.md:39/140` 与冻结件 `round_facts.txt:160` 仍是同族陈旧读数（都**不在**本批可写范围）。
- **未验证**：未启动引擎、未跑轮、未联网、未调 MCP/模型端点；引擎 `--version` 未在本批重跑（实测串取自冻结轮次记录）；
  `runs/**` 的"零写入"由 mtime 判据支撑（能保留全部 mtime 的写入不可见）；三处报告植入发生在**临时副本**上，
  真件未被触碰，因此本批**没有**"真件植入 + 真件逐字节回退"这一形态的证据（代码植入有 3 处逐字节回退）。
- **本批未提交**：HEAD 仍是 `c2780bc`；按前几批的先例（DR-79 的成果由调度者随 D293 与验收一起提交为 `ec90c19`），
  提交由调度者决定。

## 9. 诚实披露

1. **植入与"真先红"分开算**：② 的"注不存在"与 ⑤ 的"DR-80 heading 不存在"两次红是**真先红**
   （测试先写、文档后改）；三处临时副本植入与三处代码植入是**植入红**，不冒充先红。
2. **非空洞性测试第一次红是"选错行"**：它最初按 `| C1 ` 找删除目标，而 T13 报告没有这种行，于是失败原因不对；
   改为"第一行 markdown 表行"后通过了三种植入的拒绝断言。这条未被掩盖地记在这里。
3. **两个 seal 常量是追加后回填的**：DR-79 与 DR-73 的 seal 在任何改动之前就钉好（那两条测试当时即绿），
   但 DR-80 seal 与 REQ seal 只能在追加发生、前缀长度确定后才计算——严格 TDD 在这一点上让步，如实登记。
4. **临时副本的三个变异也弄红了非空洞性测试**：因为该测试要求"未篡改的读必须通过守卫"，在变异树里它先因这条
   前提失败；变异树不是仓库，这一点如实说明而不修补。
5. **三处报告植入未落在真件上**：任务书要求"在临时副本上做，不得改动真实报告"，我照此执行，代价是
   这批没有"真件逐字节回退"的报告类证据；作为补偿，真件 sha256 在整场前后**逐一比对相同**。
6. **未 commit / 未 stage / 未 push**；`%DST%/` 等既有异物一律未动。

<!-- read-back self-check, appended after the parse -->
SELF-CHECK: json_fences=1 json.loads=PASS round_trip_equal=True keys=16 bytes=26045 baseline=554/0/7 final=560/0/7 listed=561->567 fmt_exit=0 items=5
