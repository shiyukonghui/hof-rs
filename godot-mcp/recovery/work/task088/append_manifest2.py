# -*- coding: utf-8 -*-
"""task088: append the G-6 gate ledger + iron rules to the manifest.

usage: python append_manifest2.py
"""
from __future__ import print_function
import io

MANIFEST = r"H:\rebuild\godot\modules\mcp_server\docs\reports\REBUILT-2C-MANIFEST.md"

SECTION = u"""
## G-6. Gate ledger (task-088, real output)

All nine gates green. The doctests and the anchor verdict were re-taken **after**
the batch was committed, on a mono binary rebuilt at the new HEAD
(`e4b025519a`), so the anchor is `ANCHOR_EQUAL` and not
`STRUCTURAL_EQUIVALENT`:

| # | gate | command | result |
|---|---|---|---|
| 1 | module doctest | `bin\\godot.windows.editor.x86_64.mono.console.exe --headless --test --test-case=[MCPServer]*` | **exit 0** — `143 / 143 passed / 0 failed`, `6396 / 6396` assertions, `SUCCESS!` |
| 2 | full engine doctest | the same binary, `--headless --test` | **exit 0** — `1569 / 1569 passed / 0 failed / 3 skipped`, `430709 / 430709` assertions, `SUCCESS!` |
| 3 | group manifest | `docs/scripts/check_tool_groups.py` | **exit 0** — `TOOL-GROUPS CHECK PASS`, 5681 B, sha `b83d79d3…` |
| 4 | contract subset (live) | `scripts/check_contract_subset.ps1` | **exit 0** — `3/3 checks passed`; editor 9888 `tools=154`, game 9889 `tools=73`, `guard_user_port_9877` PASS; `implemented_union=154 / 73` |
| 5 | rename map | `docs/scripts/check_rename_map.py` | **exit 0** — `RESULT: PASS (all checks green)`; `177 == 174 - 2 - 1 + 6` |
| 6 | tautologies | `scripts/check_tautologies.py` | **exit 0** — `TAUTOLOGY CHECK PASS` |
| 7 | exit-code propagation | `scripts/check_exit_propagation.py --probes` | **exit 0** — `PROBES: 10/10` |
| 8 | hardcoded counts | `scripts/check_hardcoded_counts.py` | **exit 0** — `UNCLASSIFIED = 0` (**was the one red gate**) |
| 9 | engine anchor | `scripts/check_engine_anchor.ps1 -VersionText '4.8.dev.mono.custom_build.e4b025519'` | **exit 0** — `VERDICT=ANCHOR_EQUAL  ANCHOR=e4b025519  HEAD=e4b025519  RESULT PASS` |
| + | M1 acceptance | `scripts/accept_m1.ps1` | **exit 0** — `22/22 cases passed` (**was 16/20**) |
| + | traceability demo | `mcp088_live_evidence.ps1` + `scripts/mcp_trace_ledger.py` | editor `calls=4`, `ok_effect_observed=1 / ok_no_effect_observed=3`, `facts_complete 4/4` |

**The plain (non-mono) binary is NOT at HEAD.** `check_engine_anchor.ps1
-VersionText '4.8.dev.custom_build.75d86665e'` answers
`ANCHOR_STALE_COMPILED` with exactly one red file,
`modules/mcp_server/tests/test_mcp_server.h`. That binary was left as it was
(rebuilding it is a second full non-mono build); the *test* evidence for HEAD is
therefore the mono binary of gates 1/2, and the `accept_m1` / contract-subset
evidence describes HEAD's served registry because the only compile input that
differs is the test header.

## G-7. Iron rules

* Only `H:\\rebuild\\godot` and `C:\\Users\\wyl\\AppData\\Local\\Temp\\mcp-recovery\\`
  were written. The gates' own scratch went to
  `…\\mcp-recovery\\tmp\\` because `TEMP`/`TMP` were pointed there for those runs.
* `F:` was **never** written. `DECISIONS.md` 537 251 B sha
  `114B2A8218E35DF8E998FA4329D99F97D6037987E19FBA4A324B567C009CF323` and
  `tests\\fixtures\\mcp\\tools_list.json` 48 749 B sha
  `8F8051C4C0F8941089F0B21A193CEF7C51FA7C41D7E312B1463EA8593F313C54` are
  byte-identical to the pre-flight values (the fixture is the generator's input
  and was only read).
* No shell redirection anywhere: every log is written by
  `Start-Process -RedirectStandardOutput/-RedirectStandardError`, every text file
  by `Set-Content`, `-NoNewline`, `Out-File`-free Python, or the `write` tool.
* Destructive commands: one guarded deletion ran
  (`work/task088/del_stale_objs.py` — three absolute paths under the single
  whitelisted prefix `H:\\rebuild\\godot\\bin\\obj\\`, the exact four paths the
  tracked `mcp057_build_mono.cmd` names, manifest printed before removal, dry run
  first, no wildcard and no `..`). Nothing else was removed, moved or renamed.
* Builds and engine runs start from `cmd.exe` (iron rule 4): `scons_run.ps1`,
  `run_mono.ps1`, `run_cmd.ps1`, all with `WaitForExit()` and `/v:on`.
"""


def main():
    text = io.open(MANIFEST, encoding="utf-8").read()
    if "G-6. Gate ledger (task-088" in text:
        print("already appended")
        return 0
    io.open(MANIFEST, "a", encoding="utf-8", newline="\n").write(SECTION)
    print("appended %d bytes" % len(SECTION.encode("utf-8")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
