# TASK-DR90-REPORT — honour the text-resource reader's own `;` comment per extension, keep every restored truncation finding, settle the correction discipline, and publish a complete gate

- Role: **fresh implementation subagent**, no upstream conversation context. The task prompt is the
  complete authority; every number below was measured by me, not transcribed from a report.
- Landing point: `F:\moonbit-hof-rs`; start HEAD `7a8e04784ba019646878452cbf376e9dffbbaedc`
  (`origin/master` still `55a075194505e0f4a6d3e913a41e29880ea302e4`, **ahead 15**, **nothing pushed**).
- **The dispatcher committed the batch while this report was being finished.** After the two source
  files and the first revision of this report existed, the dispatcher landed
  `85b3d35 fix(dr90): honour the resource format line comment in the truncation audit, per extension`
  (parent `7a8e047`, author `starsliving`, `2026-10-03 23:44:13 +0800`, three files: the two sources
  and this report). The committed blobs are **identical** to this batch's measured working files —
  `git hash-object` = `git rev-parse HEAD:<f>` = `aa840bb4113535207a3d4d373245ed5d87f9272d` for
  `src/runtime/integrity.rs` and `e03a17be62c1e16944cc572bfc3e7ed880805484` for
  `tests/append_only_guard.rs` — so nothing that was measured changed. `origin/master` is still
  `55a0751…` (**ahead 16**): **nothing was pushed**, and **I** staged, committed and pushed nothing.
  The committed copy of this report is the first assembly (42,693 B / `a05d63d6…`); the working file
  is the corrected one (42,708 B / `ebc2832f…`), differing by exactly one line (an `H6` label fix),
  which is the deliverable.
- **Offline**: no engine started/restarted/driven, no round run, no network. **Nothing under `runs/**`
  was written** and no workspace directory was written; no game was hand-written.
- **Untouched, by the task's own constraint**: `DECISIONS.md` (byte-identical, `9f95f26e…`), the
  frozen specification `.spec/hof-rs/PRD-mario.md` (`4c81c3a9…`) and the sealed
  `.spec/hof-rs/REQUIREMENTS.md` (`4982bf1c…`, 28,690 B), the engine tree `godot-mcp/**`
  (porcelain 0 bytes), the legacy adapter `src/adapter/godot.rs` (`27fda15a…`),
  `Cargo.toml`/`Cargo.lock` (no dependency added), `config/hoh.yaml`, and
  `.spec/hof-rs/tasks/TASK-DR88-REPORT.md` (`e6b949ef…`, 27,589 B). Because `DECISIONS.md` is a
  forbidden zone here, the two decisions this batch makes are recorded in **section 10** of this
  report instead, with the constraint named.
- Scratch and every helper script, log, revision copy and probe live **outside the repository** in
  `C:\Users\wyl\AppData\Local\Temp\t16dr90-impl\` (`setup.py`, `gate90.py`, `probe90.py`,
  `table90.py`, `plants90.py`, `evidence90.py`, `census_check.py`, `linecheck.py`,
  `probe/zzz_probe90.rs`). **No `rm -rf` anywhere** — removals are Python `glob` + `shutil.rmtree`
  on a path that is printed and asserted first. **No `git checkout --`.** No path was built from an
  unexpanded variable. Every edit and every restore is followed by an explicit `os.utime` (forward)
  and by a byte-equality assert against the snapshot.
- Files changed: **exactly two** — `src/runtime/integrity.rs` (+364/-31) and
  `tests/append_only_guard.rs` (+122). No test was removed; five were added.

---

## 1. The rules I modelled, each with the engine source that justifies it

The defect was one false premise: the audit's scanner treated `#` as a comment for **every** audited
extension. The engine has two readers over that set and they disagree, so the fix is a **per-extension
comment rule** threaded through all three consumers (`scan_line`, and through it both the
unterminated-literal rule and the delimiter-balance rule).

`src/runtime/integrity.rs:134`:

```rust
fn line_comment(extension: &str) -> Option<char> {
    match extension {
        "gd" => Some('#'),
        "tscn" | "tres" => Some(';'),
        _ => None,
    }
}
```

| # | Rule | Engine source I read | Line range |
|---|---|---|---|
| R1 | In a `.tscn`/`.tres`, `;` opens a **line comment**: the rest of the line is discarded | `godot-mcp/godot/core/variant/variant_parser.cpp`, `VariantParser::get_token`, `case ';':` reads `get_char()` until `'\n'` (or EOF) and then `break`s out of the token switch | `:215-229` |
| R2 | The same rule in the resource **tag/assign** reader | same file, `VariantParser::parse_tag_assign_eof`: `if (c == ';') { //comment` loops to `'\n'` then `continue` | `:1787-1799` |
| R3 | `.tscn`/`.tres` really are read through those two functions | `godot-mcp/godot/scene/resources/resource_format_text.cpp` calls `VariantParser::parse_tag` / `parse_tag_assign_eof` for the scene header, the sub-resource tags and the per-node property loop | `:285`, `:377`, `:395`, `:518`, `:625`, `:755` |
| R4 | In a `.gd`, `#` — and **only** `#` — opens a comment | `godot-mcp/godot/modules/gdscript/gdscript_tokenizer.cpp`, `GDScriptTokenizerText::_skip_whitespace`, `case '#':` advances to `'\n'` | `:1344` |
| R5 | In a `.gd`, `;` is **not** a comment: it is a `SEMICOLON` token, i.e. a statement separator | same file, the token-name table's own entry `";", // SEMICOLON,` | `:134` |
| R6 | In a `.tscn`/`.tres`, `#` is **not** a comment: it starts a **colour** token | `core/variant/variant_parser.cpp`, `VariantParser::get_token`, `case '#':` builds a `Color` from the hexadecimal digit run and `saved`s the first non-hex character | `:242-262` |
| R7 | ... and the writer never emits a bare `#` in a resource, so R6's reading cannot red an engine-written document | same file, `VariantWriter::write`, `p_store_string_func(..., "Color(" + rtos_fix(c.r…) + ", " + … + ")")` — a `Color` is written as `Color(r, g, b, a)`, never as `#rrggbb` | `:2017` |

Blob hashes of the cited sources, read from the engine tree's own git
(`git -C godot-mcp/godot rev-parse HEAD:<path>`), engine HEAD
`fc63af77c33368c4a1bb839c95d19750554f63a3`:

| file | blob | size |
|---|---|---|
| `core/variant/variant_parser.cpp` | `1531a6fc24713fc1d1f8b6bd932d23e569cf75d9` | 71,686 B |
| `scene/resources/resource_format_text.cpp` | `3ac84e5d63a578f99c659fe5022f64d790c4f720` | 67,768 B |
| `modules/gdscript/gdscript_tokenizer.cpp` | `5af727afcf5be28cf145794fb505b36fd23577ef` | 44,000 B |

`variant_parser.cpp` and `gdscript_tokenizer.cpp` are the same blobs the DR-88 acceptance read; the
resource-format file is the new citation this batch rests R3 on.

### Why R5/R6 exist in the model rather than only R1

The task asked for the behaviour to be "right for each audited extension rather than globally", and
the source says the two readers disagree in **both** directions:

* making `;` a comment globally (instead of per extension) would blind the audit on a `.gd` — R5 says
  a statement separator is executable content, and a literal opened after it must still be judged.
  `a_semicolon_is_not_a_comment_in_gdscript` pins that, and plant **P2** reddens it.
* keeping `#` as a comment in a resource (the pre-DR-90 behaviour) contradicts R6 and is a false
  premise in the **permissive** direction: it lets a `#`-bearing line hide a delimiter or an
  unterminated literal from both rules. `a_hash_is_not_a_comment_in_a_text_resource` pins the
  corrected reading, plant **P3** reddens it, and the cost is measured in section 5 (A11/A19/A25).

### What the two rules now share

Both whole-document rules consume the same marker, so they cannot disagree: `audit_text` computes
`let comment = line_comment(&extension);` once (`:513`) and passes it to
`unterminated_literal(text, comment)` (`:519`), `unbalanced_delimiter(text, comment)` (`:556`) and
`first_invalid_escape(text, comment)` (`:577`). Inside `scan_line` the marker test is
`if Some(ch) == comment` (`:330`). The doc comments were rewritten to state the per-extension rule
and to cite R1–R7 rather than repeating the old global `#` claim.

---

## 2. The measurement, four points, one isolated target directory each

Probe `probe/zzz_probe90.rs` calls the **production** `audit_text` and is a **reporter**, never an
assertor, so the same file is valid in every revision. Each revision is a `git archive` export to its
own out-of-repo directory with its **own `CARGO_TARGET_DIR`** (the shared-target stale-binary trap has
bitten twice). The four points:

| point | revision | `integrity.rs` blob | probe log |
|---|---|---|---|
| parent | `ab95c65` (before DR-88) | `ddaf39af0d002834b0bfef7537c721a29aceab79` | `logs/rev-parent.probe.txt` |
| DR-88 | `52d73d3` | `3c956965d738a915ac9cb5fa6c4635452959ed80` | `logs/rev-dr88.probe.txt` |
| DR-89 | `7a8e047` (HEAD; `8b69db3:src/runtime/integrity.rs` is the **same** blob `57736af9…`, proven with `git diff --stat 8b69db3 7a8e047 -- src/runtime/integrity.rs` empty) | `57736af9602a63817f6e6ebb7ab5a17cbd47dd54` | `logs/rev-head.probe.txt` |
| DR-90 | the uncommitted working tree (`git archive HEAD` + the working `integrity.rs` and `append_only_guard.rs`) | `b77daa8b3c928ce8116bb79549b37d02310ae3527a72f65a90196caa57e76db1` | `logs/rev-wt.probe.txt` |

**Stale-binary discriminators, asserted by `table90.py`, not trusted**: `L2` must be `1/0/0/0`,
`C25` `0/0/1/1`, `G3` `0/0/1/0`, `C1` `1/1/0/0`, `N1` `1/0/0/0` — **5/5 hold**. The four raw probe logs
are not identical, and every case's source bytes hash the same across the four points (so the same
68 cases really were measured everywhere). 68 cases, `python table90.py` → `DISCRIMINATORS_OK 5/5`.

### 2.1 The truncation findings the DR-89 batch restored, and that this batch keeps

| case | shape | parent `ab95c65` | DR-88 `52d73d3` | DR-89 `7a8e047` | **DR-90 worktree** |
|---|---|---|---|---|---|
| B2 | `.gd` unterminated **raw** literal over a later `\q` | **1** shell@2 | 0 | **1** trunc@1 | **1** trunc@1 |
| B3 | `.tscn` tail behind an unterminated quote | **1** trunc@3 | 0 | **1** trunc@2 | **1** trunc@2 |
| B3b | `.tscn` `name = "abc` only | 0 | 0 | **1** trunc@2 | **1** trunc@2 |
| B5 | `.tres` tail behind an unterminated quote | **1** trunc@3 | 0 | **1** trunc@2 | **1** trunc@2 |
| B5b | `.tres` `name = "x` + `name = 12, y)  ` | **1** trunc@3 | 0 | **1** trunc@2 | **1** trunc@2 |
| C25 | `.gd` cut inside a string | 0 | 0 | **1** trunc@1 | **1** trunc@1 |
| C26 | `.gd` cut inside a raw literal | 0 | 0 | **1** trunc@1 | **1** trunc@1 |
| C27 | `.gd` cut inside a triple literal | 0 | 0 | **1** trunc@1 | **1** trunc@1 |

Every one of the eight is present at the DR-90 worktree with the **same kind and the same line** as
at DR-89. The five the DR-88 carry had lost (`B2/B3/B3b/B5/B5b`) and the three DR-88 never reported
(`C25/C26/C27`) are all intact, so honouring the `;` comment cost the truncation guard nothing — which
is the property the task made the headline.

### 2.2 The false positives, before and after

| id | shape (all legitimate; the engine accepts them) | parent | DR-88 | DR-89 | **DR-90** |
|---|---|---|---|---|---|
| G3 | `.tscn` `; don't touch` | 0 | 0 | **1** trunc@2 | **0** |
| G2 | `.tres` `; don't touch` | 0 | 0 | **1** trunc@2 | **0** |
| N2 | `.tscn` `; see "unclosed in a comment` | 0 | 0 | **1** trunc@3 | **0** |
| N4 | `.tscn` `; don't call foo(bar` | 0 | 0 | **1** trunc@2 | **0** |
| G5 | `.tscn` `; see foo(bar` | **1** trunc@3 | **1** trunc@3 | **1** trunc@3 | **0** |
| H3 | `.tscn` `; depth ( left open` | **1** | **1** | **1** | **0** |
| H6 | `.tres` `; depth ( left open` (resource twin of H3) | **1** | **1** | **1** | **0** |
| H8 | `.tscn` `; "paired" quotes and a )` | **1** | **1** | **1** | **0** |
| H10 | `.tres` `; "paired" quotes and a )` | **1** | **1** | **1** | **0** |

`G3/G2/N2/N4` are the **defect the last batch introduced** (`DR89A-1`): 1 only at DR-89. `G5/H3/H6/H8/H10`
are the older balance-rule defect (`DR89A-2`): 1 at **all three** earlier revisions. One rule closes
both, exactly as the acceptance advised.

Not regressed: `L2` (raw Windows path), `L3` (`\U0001F600`), `L9` (raw triple with `\d/\U/#`), `N1`
(a legitimate multi-line resource string holding `)`) and `C1` (lone CR after `\`) are **0** at DR-89
and DR-90. The intended tightenings are untouched: `X3/X4/X6/X7/X9/X10` each `1`, `B1` `2`
(trunc@1 + shell@2), `B7/B8` `0`, `R1` `1`.

### 2.3 The complete four-point table (68 cases)

Every case below was measured at all four points; identical `src` hashes across points mean the same
bytes were fed to each revision. `trunc` = `artifact_write_truncated`, `shell` =
`artifact_shell_residue`; `@n` is the finding's line.

| case | parent ab95c65 | DR-88 52d73d3 | DR-89 7a8e047 | DR-90 worktree |
|---|---|---|---|---|
| B2 | **1** (artifact_shell_residue@2) | 0 | **1** (artifact_write_truncated@1) | **1** (artifact_write_truncated@1) |
| B3 | **1** (artifact_write_truncated@3) | 0 | **1** (artifact_write_truncated@2) | **1** (artifact_write_truncated@2) |
| B3b | 0 | 0 | **1** (artifact_write_truncated@2) | **1** (artifact_write_truncated@2) |
| B5 | **1** (artifact_write_truncated@3) | 0 | **1** (artifact_write_truncated@2) | **1** (artifact_write_truncated@2) |
| B5b | **1** (artifact_write_truncated@3) | 0 | **1** (artifact_write_truncated@2) | **1** (artifact_write_truncated@2) |
| C25 | 0 | 0 | **1** (artifact_write_truncated@1) | **1** (artifact_write_truncated@1) |
| C26 | 0 | 0 | **1** (artifact_write_truncated@1) | **1** (artifact_write_truncated@1) |
| C27 | 0 | 0 | **1** (artifact_write_truncated@1) | **1** (artifact_write_truncated@1) |
| C1 | **1** (artifact_shell_residue@1) | **1** (artifact_shell_residue@1) | 0 | 0 |
| L2 | **1** (artifact_shell_residue@3) | 0 | 0 | 0 |
| L3 | **1** (artifact_shell_residue@1) | 0 | 0 | 0 |
| L9 | **1** (artifact_shell_residue@1) | 0 | 0 | 0 |
| N1 | **1** (artifact_write_truncated@4) | 0 | 0 | 0 |
| X3 | 0 | **1** (artifact_shell_residue@1) | **1** (artifact_shell_residue@1) | **1** (artifact_shell_residue@1) |
| X4 | **1** (artifact_shell_residue@1) | **1** (artifact_shell_residue@1) | **1** (artifact_shell_residue@1) | **1** (artifact_shell_residue@1) |
| X6 | **1** (artifact_shell_residue@1) | **1** (artifact_shell_residue@1) | **1** (artifact_shell_residue@1) | **1** (artifact_shell_residue@1) |
| X7 | **1** (artifact_shell_residue@1) | **1** (artifact_shell_residue@1) | **1** (artifact_shell_residue@1) | **1** (artifact_shell_residue@1) |
| X10 | **1** (artifact_shell_residue@1) | **1** (artifact_shell_residue@1) | **1** (artifact_shell_residue@1) | **1** (artifact_shell_residue@1) |
| X9 | 0 | **1** (artifact_shell_residue@2) | **1** (artifact_shell_residue@2) | **1** (artifact_shell_residue@2) |
| B1 | **1** (artifact_shell_residue@2) | **1** (artifact_shell_residue@2) | **2** (artifact_write_truncated@1, artifact_shell_residue@2) | **2** (artifact_write_truncated@1, artifact_shell_residue@2) |
| B7 | 0 | 0 | 0 | 0 |
| B8 | 0 | 0 | 0 | 0 |
| D4 | **1** (artifact_write_truncated@3) | **1** (artifact_write_truncated@3) | **1** (artifact_write_truncated@3) | **1** (artifact_write_truncated@2) |
| R1 | **1** (artifact_shell_residue@1) | **1** (artifact_shell_residue@1) | **1** (artifact_shell_residue@1) | **1** (artifact_shell_residue@1) |
| G3 | 0 | 0 | **1** (artifact_write_truncated@2) | 0 |
| G2 | 0 | 0 | **1** (artifact_write_truncated@2) | 0 |
| N2 | 0 | 0 | **1** (artifact_write_truncated@3) | 0 |
| N4 | 0 | 0 | **1** (artifact_write_truncated@2) | 0 |
| G5 | **1** (artifact_write_truncated@3) | **1** (artifact_write_truncated@3) | **1** (artifact_write_truncated@3) | 0 |
| N3 | 0 | 0 | 0 | 0 |
| N6 | 0 | 0 | 0 | 0 |
| G4 | 0 | 0 | 0 | 0 |
| G1 | 0 | 0 | 0 | 0 |
| H1 | 0 | 0 | **1** (artifact_write_truncated@2) | 0 |
| H2 | 0 | 0 | **1** (artifact_write_truncated@2) | 0 |
| H3 | **1** (artifact_write_truncated@3) | **1** (artifact_write_truncated@3) | **1** (artifact_write_truncated@3) | 0 |
| H4 | 0 | 0 | **1** (artifact_write_truncated@2) | 0 |
| H5 | 0 | 0 | **1** (artifact_write_truncated@2) | 0 |
| H6 | **1** (artifact_write_truncated@3) | **1** (artifact_write_truncated@3) | **1** (artifact_write_truncated@3) | 0 |
| H7 | 0 | 0 | 0 | 0 |
| H8 | **1** (artifact_write_truncated@2) | **1** (artifact_write_truncated@2) | **1** (artifact_write_truncated@2) | 0 |
| H9 | 0 | 0 | 0 | 0 |
| H10 | **1** (artifact_write_truncated@2) | **1** (artifact_write_truncated@2) | **1** (artifact_write_truncated@2) | 0 |
| H11 | 0 | 0 | 0 | 0 |
| H12 | **1** (artifact_write_truncated@3) | **1** (artifact_write_truncated@3) | **1** (artifact_write_truncated@3) | 0 |
| H13 | **1** (artifact_write_truncated@3) | **1** (artifact_write_truncated@3) | **1** (artifact_write_truncated@3) | 0 |
| A2 | 0 | 0 | 0 | 0 |
| A3 | 0 | 0 | 0 | 0 |
| A4 | 0 | 0 | 0 | 0 |
| A5 | 0 | 0 | **1** (artifact_write_truncated@2) | **1** (artifact_write_truncated@3) |
| A6 | 0 | 0 | 0 | **1** (artifact_write_truncated@3) |
| A7 | 0 | 0 | 0 | 0 |
| A8 | **1** (artifact_shell_residue@1) | **1** (artifact_shell_residue@1) | **1** (artifact_shell_residue@1) | **1** (artifact_shell_residue@1) |
| A9 | 0 | 0 | 0 | 0 |
| A10 | 0 | 0 | **1** (artifact_write_truncated@1) | **1** (artifact_write_truncated@1) |
| A11 | 0 | 0 | 0 | **1** (artifact_write_truncated@3) |
| A12 | 0 | 0 | 0 | 0 |
| A14 | 0 | 0 | 0 | 0 |
| A16 | 0 | 0 | **1** (artifact_write_truncated@2) | **1** (artifact_write_truncated@2) |
| A17 | 0 | 0 | **1** (artifact_write_truncated@2) | **1** (artifact_write_truncated@2) |
| A18 | **1** (artifact_write_truncated@3) | **1** (artifact_write_truncated@3) | **2** (artifact_write_truncated@3, artifact_write_truncated@3) | **1** (artifact_write_truncated@3) |
| A19 | 0 | 0 | 0 | **1** (artifact_write_truncated@2) |
| A25 | 0 | 0 | 0 | **1** (artifact_write_truncated@2) |
| A20 | **1** (artifact_write_truncated@2) | **1** (artifact_write_truncated@2) | **1** (artifact_write_truncated@2) | 0 |
| A21 | **1** (artifact_write_truncated@2) | **1** (artifact_write_truncated@2) | **1** (artifact_write_truncated@2) | 0 |
| A22 | **1** (artifact_write_truncated@2) | **1** (artifact_write_truncated@2) | **1** (artifact_write_truncated@2) | 0 |
| A24 | **1** (artifact_write_truncated@2) | **1** (artifact_write_truncated@2) | **1** (artifact_write_truncated@2) | **1** (artifact_write_truncated@2) |
| A26 | 0 | 0 | 0 | 0 |

---

## 3. My own legitimate files and their controls

The task asked for a scene comment holding an apostrophe, one holding a single quote, one holding an
unmatched parenthesis, **and a resource file with the same three**, alongside plain and paired-quote
controls. All thirteen are in the probe as `H*`, and the same shapes are pinned by the in-repo test
`runtime::integrity::tests::a_semicolon_comment_is_the_text_resources_own_comment`
(`src/runtime/integrity.rs:1096`), so the fix is a gate, not a probe-only result.

| id | file | its `;` comment holds | parent | DR-88 | DR-89 | **DR-90** | control for |
|---|---|---|---|---|---|---|---|
| H1 | `scenes/s.tscn` | `don't move the node` (apostrophe) | 0 | 0 | **1** | **0** | `DR89A-1` |
| H2 | `scenes/s.tscn` | `a lone ' apostrophe` (single quote) | 0 | 0 | **1** | **0** | `DR89A-1` |
| H3 | `scenes/s.tscn` | `depth ( left open` (unmatched `(`) | **1** | **1** | **1** | **0** | `DR89A-2` |
| H4 | `res/r.tres` | apostrophe | 0 | 0 | **1** | **0** | `DR89A-1`, resource twin |
| H5 | `res/r.tres` | single quote | 0 | 0 | **1** | **0** | `DR89A-1`, resource twin |
| H6 | `res/r.tres` | unmatched `(` | **1** | **1** | **1** | **0** | `DR89A-2`, resource twin |
| H7 | `scenes/s.tscn` | plain comment | 0 | 0 | 0 | **0** | negative control |
| H8 | `scenes/s.tscn` | `"paired" quotes and a )` | **1** | **1** | **1** | **0** | the balance rule on a paired-quote comment |
| H9 | `res/r.tres` | plain comment | 0 | 0 | 0 | **0** | negative control |
| H10 | `res/r.tres` | `"paired" quotes and a )` | **1** | **1** | **1** | **0** | resource twin of H8 |
| H11 | `scripts/a.gd` | `var a = 1; var b = 2` (no comment at all) | 0 | 0 | 0 | **0** | `;` in a script is code, not a comment |
| H12 | `scenes/s.tscn` | all three shapes in one comment | **1** | **1** | **1** | **0** | one rule, not three fixes |
| H13 | `res/r.tres` | all three shapes in one comment | **1** | **1** | **1** | **0** | and its twin |

The converse (also pinned in the same test): skipping the comment did **not** blind the guard —
`; don't touch` followed by `name = "abc` is still `1` trunc@3 at DR-90 (was trunc@2 at DR-89, where
the phantom literal was the finding), `; a ( b` followed by `visible = false)  ` is `1` trunc@3 at
DR-90 (was **0** at DR-89, so this is a **strengthening**), and the `.tres` twin is `1` trunc@3.

---

## 4. The gate: complete, with the literal exit code

Both runs used the repository's own `target/`, cleared the same `hof-rs-*` fingerprint set with Python
`glob`+`shutil.rmtree` (every path printed before removal) and touched **each** tracked `.rs` file
individually from `git ls-files "*.rs"`. Both raw logs are the evidence path; the driver's narration
is a different file. `summarize()` is a pure function of one raw log and is asserted idempotent
in-process.

| reading | baseline (HEAD `7a8e047`) | final (this batch) |
|---|---|---|
| fingerprint dirs hit / removed | `hof-rs-*` / **63** | same / **63** |
| tracked `.rs` touched individually | **101** | **101** |
| `cargo fmt --all --check` | `FMT_EXIT=0` (no output) | `FMT_EXIT=0` (no output) |
| `cargo test --offline -- --list` | `LIST_EXIT=0`, `LIST_TESTS=655`, `LIST_BENCH=0` | `LIST_EXIT=0`, `LIST_TESTS=660`, `LIST_BENCH=0` |
| forced rebuild proven | `COMPILING_IN_LIST=1` | `COMPILING_IN_LIST=1` |
| **literal `cargo test --offline` exit code** | **`LITERAL_CARGO_TEST_EXIT=0`** | **`LITERAL_CARGO_TEST_EXIT=0`** |
| summary (pure function of the raw log) | `SUITES=62 PASSED=648 FAILED=0 IGNORED=7` `RED_SUITES=0` | `SUITES=62 PASSED=653 FAILED=0 IGNORED=7` `RED_SUITES=0` |
| `passed + ignored == --list` | `648 + 7 = 655` ✓ | `653 + 7 = 660` ✓ |
| full run reused the `--list` binaries | `COMPILING_HOF_RS_IN_FULL_RUN=0` | `COMPILING_HOF_RS_IN_FULL_RUN=0` |
| process check before / after | `PROCS_BEFORE=NONE` / `PROCS_AFTER=NONE` | `PROCS_BEFORE=NONE` / `PROCS_AFTER=NONE` |

Both runs were taken with the tree at `7a8e047` plus this batch's two uncommitted edits — the same
bytes the dispatcher then committed as `85b3d35`. The commit's blobs are byte-identical to the files
the gate compiled (`aa840bb4…` / `e03a17be…`), so the readings bind the committed revision too.

**The baseline I reproduced myself is exactly the figure the task named** (literal exit 0 / 648
passed / 0 failed / 7 ignored / `--list` 655 / `fmt` 0), and the final run is **above** it:
`653 = 648 + 5` and `660 = 655 + 5`.

- **No test removed**: name-set diff over the two `--list` raw logs — `REMOVED = []`, `ADDED =
  ["runtime::integrity::tests::a_comment_marker_inside_a_string_opens_no_comment",
  "runtime::integrity::tests::a_hash_is_not_a_comment_in_a_text_resource",
  "runtime::integrity::tests::a_semicolon_comment_is_the_text_resources_own_comment",
  "runtime::integrity::tests::a_semicolon_is_not_a_comment_in_gdscript",
  "the_dr88_false_clause_survives_only_as_a_labelled_quotation"]` — the five additions are exactly
  this batch's five new tests. **No test was renamed or deleted.**
- **Ignored count unchanged**: line-start `#[ignore` attributes over the 101 tracked `.rs` files =
  **7** at HEAD and **7** now, matching `IGNORED=7` from the run.
- **Forced rebuild is real**: the first cargo call after clearing fingerprints printed
  `Compiling hof-rs v0.1.0 (F:\moonbit-hof-rs)`, and the full run then reused those binaries
  (`COMPILING_HOF_RS_IN_FULL_RUN=0`) — so the 653 tests ran on binaries built from this tree.
- **No second test process of mine**: `tasklist` filtered for `cargo`/`rustc`/`hof_rs` printed
  `NONE` immediately before the fingerprint clear and immediately after the full run.

**One test fixture was corrected, not removed.** `delimiters_inside_literals_and_comments_are_not_counted`
(`src/runtime/integrity.rs`) used a `.tscn` whose comment was written `# a comment with ]`. Under R6
that line is not a resource comment, so the fixture asserted a false premise; it now uses `; a comment
with ]`, the reader's own marker, keeping the test's intent ("a delimiter inside a literal or a comment
is not code") while making it true. This is a fixture correction with an engine citation, not a
weakening: the name-set diff above shows the test still exists and no test disappeared. It is
**declared here** because it is a change to a test.

---

## 5. Attacking my own change

I built twenty-two attack shapes in the probe (`A*`) and measured each at all four points; several more
attack results follow from the `H*` rows already given. The audit now **misses** two shapes and
**newly reports** three; each is closed or declared below with its measurement.

### 5.1 Closed

1. **The comment marker is itself inside a string.** `A2` = `.tscn` `text = "; see foo(bar"` → **0**
   at every point; `A7` = `.tscn` `text = "; ] ( unbalanced"` → **0**. The scanner consumes the
   literal as a unit before it looks for a marker, so the marker is content. `A26` = `.gd`
   `# a comment ] ( ) with C:\Users\dev` → **0** (the `#` really is that reader's comment). And the
   sharp converse: `A16` = `.tscn` `text = "abc ; ` and `A17` = `.tscn` `text = "abc # ` are **1**
   trunc@2 at DR-90 — a marker inside an **unterminated** literal does not hide the fragment.
   Pinned by `a_comment_marker_inside_a_string_opens_no_comment`.
2. **A comment must not swallow a real fragment behind it.** `A5` = `.tscn` `; don't` then
   `name = "abc` is **1** trunc@3 at DR-90 (DR-89 reported trunc@2 for the phantom literal, so the
   count survives but is now the *right* finding); the `.tres` twin `A18` is **1** trunc@3 at DR-90
   and was **2** at DR-89 (the same truncation reported twice, once by the balance rule and once by
   the literal rule). `A6` = `.tscn` `; a ( b` then `visible = false)  ` is **1** at DR-90 and was
   **0** at DR-89 — a genuine improvement, because DR-89's `(` and `)` cancelled in the depth count.
   `A10` = `.gd` `var a = 1; var s = 'abc` is **1** trunc@1 at DR-90 (was 0 at parent and DR-88):
   a `;` in a script is code, so a literal opened after it is judged. The control `A24` =
   `.tscn` `name = ab)  ` (no `;`) is **1** at every point, so the balance rule was not switched off.
3. **A `;` at EOF is not silently ignored where the language says it is code.** `A9` =
   `.gd` `var a = 1; # don't` → **0** and `A26` → **0**: the per-extension rule cuts both ways.

### 5.2 Declared, with the measurement — the audit now misses these

1. **A file cut in the middle of a `;` comment.** `G5` (the acceptance's own case; my probe id is the
   same shape) = `.tscn` `[gd_scene format=3]` + `; see foo(bar` + a node: **1** at parent, DR-88 and
   DR-89, **0** at DR-90. The `(` is inside the
   reader's line comment, so the reader does not see it either. **This cannot be closed, and must not
   be**: the very same bytes are `DR89A-2`, which the last acceptance measured as a false positive a
   gate check must never produce and told this batch to remove. A comment has no closing delimiter, so
   "the writer's comment continued past EOF" and "the comment is complete at EOF" are byte-identical
   inputs. `A20` = `.tscn` `name = a;b)  `, `A21` = `.tscn` `name = a;b( ` and `A22` = the `.tres`
   twin are the same class (1 → 0), and `A24` is the control that shows the loss is exactly the
   `;`-bearing line and not the balance rule.
2. **A file that ends immediately after a comment marker.** `A3` = `.tscn` ending `…Node2D"]\n;` and
   `A4` = the same with a trailing newline are **0 at every revision**, so this batch changes nothing
   there, and the reason is the same one: a line comment has no terminator to be missing. Declared,
   not closable, with the measurement.

### 5.3 Declared, with the measurement — the audit now newly reports these (a tightening)

Treating `#` faithfully (R6) means a `.tscn`/`.tres` line whose `#` carries a delimiter or an
unterminated quote is now code for both rules:

| id | shape | parent | DR-88 | DR-89 | **DR-90** |
|---|---|---|---|---|---|
| A11 | `.tscn` `# a comment with ]` | 0 | 0 | 0 | **1** trunc@3 |
| A19 | `.tscn` `# it's` (the line is the whole body) | 0 | 0 | 0 | **1** trunc@2 |
| A25 | `.tres` `# it's` then `[resource]` | 0 | 0 | 0 | **1** trunc@2 |
| A12 | `.tscn` `# C:\Users\dev` and nothing else on the line | 0 | 0 | 0 | **0** |

The cost is bounded by R7: `VariantWriter::write` never emits a bare `#` outside a string, so no
engine-written scene can be reddened by this, and `A12` shows that a `#` line carrying no delimiter
and no quote is still clean. A `#` line is, at worst, the reader's colour token or junk the tag
assigner discards; both readings cost at most a cosmetically odd hand-written `.tscn`. This is the
only direction in which the change is stricter rather than looser, and it is named in the residual
table (section 11) rather than left as a side effect.

### 5.4 Honest note on one case whose kind and line moved without the count changing

`D4` = `.tscn` `# it's` + `visible = false)  ` reads **1** at all four points, but at DR-90 the finding
is trunc@2 (the literal the `'` opens, still open at EOF) instead of trunc@3 (the stray `)` counted by
the balance rule). The count is preserved; the rule that produces it changed, because `#` is no longer
treated as a comment there. It is listed here so the move is not mistaken for a silent change: the
same class of honest boundary the DR-89 report recorded for `B3/B5`.

---

## 6. Correction discipline: the in-place DR-88 correction, decided

**The question.** The DR-89 batch corrected the false clause in `.spec/hof-rs/tasks/TASK-DR88-REPORT.md`
**in place** (one line, `+1/-1`, `git diff 52d73d3 8b69db3 --` shows it), where D289's discipline for a
historical report is *append-only*, and the DR-89 acceptance recorded that as `DR89A-3`.

**Decision: the labelled-quotation form is acceptable here, and I did not revert it.** The reasoning,
in the order that decides it:

1. **DR-89's own accepted criterion `C7` forbids the append-only resolution in this file.** `C7` reads
   *"no file anywhere still asserts it"* — the clause whose truth DR-88 got wrong. Restoring the
   original line, which is what "move it to an append" literally means, would put a live false
   assertion back into a repository file; the appended erratum would then have to argue with the body
   of the same report. The two rules point in opposite directions, and `C7` is the one an acceptance
   actually measured.
2. **D289's purpose, which is what the rule exists for, is met.** Its text (`DECISIONS.md:11019-11021`)
   is that a correction must not lose the original claim, must not touch a machine-readable block or an
   evidence string, must keep the original readable and labelled, and must be declared. Here the
   clause survives **verbatim** inside the very sentence that labels it false
   (`「T16 那一轮的 \`\$\` 残渣正落在字符串里」**不成立**（已由 DR-89 更正，DR88A-1）`), the file carries no
   seal, pin, `json` block or evidence string, and `TASK-DR89-REPORT.md` §3 declares the edit. Nothing
   vanished silently.
3. **It is now enforced, not merely argued.** A decision that only lives in a report decays; a gate
   does not. This batch adds
   `tests/append_only_guard.rs::the_dr88_false_clause_survives_only_as_a_labelled_quotation`
   (`:971`), which asserts on the **real** bytes that (a) the false clause is still present, (b) the
   sentence that marks it false is present together with `不成立`, `已由 DR-89 更正` and `DR88A-1`,
   and (c) **every line carrying the clause carries a false-label on that same line**. Its non-vacuity
   is proven in-memory by stripping the labels from the clause's own line, and plant **P5** proves it
   on the real bytes (strip the label pair → exit 101 → restore byte-identical to `e6b949ef…` →
   control green). The guard deliberately does **not** freeze the file: a further append, or a further
   labelled quotation, stays permitted — exactly what an append-only discipline would allow.
4. **No sealed prefix was touched**, because there is nothing to touch: `TASK-DR88-REPORT.md` is
   27,589 B / `e6b949ef…`, byte-identical to the revision this batch started from, and the only
   pin-like documents in the tree (`REQUIREMENTS.md`'s 20,910-byte DR-80 seal, the T13/T16/T81/T82
   seals) are untouched — the whole `tests/append_only_guard.rs` suite including all of those seals is
   green in the final run.

The pin is therefore the "pin" the task asked for; the file itself is unchanged.

---

## 7. The plants

Five controlled plants (`plants90.py`, log `logs/plants.log`). Each makes **one** literal substitution
(the driver asserts the needle occurs exactly once), runs **only** the test that pins the property, and
restores the file from a byte snapshot. The restore run doubles as the next plant's "before" control,
so every plant has a green control before **and** after. The mtime is always set **forward** after an
edit and after a restore (a backward mtime once made a planted run read as green).

| plant | file | one substitution | test it pins | control → planted → restore → control |
|---|---|---|---|---|
| P1 | `src/runtime/integrity.rs` | `"tscn" \| "tres" => Some(';'),` → `… => None,` | `a_semicolon_comment_is_the_text_resources_own_comment` | 0 → **101** → identical (`b77daa8b…`) → 0 |
| P2 | `src/runtime/integrity.rs` | `"gd" => Some('#'),` → `"gd" => Some(';'),` | `a_semicolon_is_not_a_comment_in_gdscript` | 0 → **101** → identical → 0 |
| P3 | `src/runtime/integrity.rs` | `if Some(ch) == comment {` → `… \|\| ch == '#' {` | `a_hash_is_not_a_comment_in_a_text_resource` | 0 → **101** → identical → 0 |
| P4 | `src/runtime/integrity.rs` | `unterminated_literal(text, comment)` → `None::<(usize, OpenString)>` | `an_unterminated_literal_is_a_fragment_not_a_whole_document` | 0 → **101** → identical → 0 |
| P5 | `.spec/hof-rs/tasks/TASK-DR88-REPORT.md` | `」**不成立**（已由 DR-89 更正，DR88A-1）` → `」。` | `the_dr88_false_clause_survives_only_as_a_labelled_quotation` | 0 → **101** → identical (`e6b949ef…`) → 0 |

`PLANTS THAT DID NOT BEHAVE: []`, `PLANTS_COUNT 5`. P1–P4 each printed `Compiling hof-rs v`, so no
stale binary was used; every one of them reddens a test this batch wrote, so the new rules are
load-bearing. **P5's `compiled=True` is explained honestly**: a markdown file cannot trigger a
compile — the flag is from the *previous* plant's restore, which bumped `integrity.rs`'s mtime. P5's
own change is a runtime file read, and its reddening is caused by the file's bytes, not by a rebuild.
`Final` sha256 after all five plants: `integrity.rs b77daa8b…`, `append_only_guard.rs 51b08762…`,
`TASK-DR88-REPORT.md e6b949ef…` — all equal to the snapshots taken before the first plant.

---

## 8. Forbidden-zone self-check

| item | reading | verdict |
|---|---|---|
| `runs/**` | **7,341** files (the same 7,341 as the baseline reading; `.git`-excluding walk gives 7,312, and the 29-file difference is `runs/playability/PlayJev-src/.git`, measured by `census_check.py`); newest mtime `2026-10-03T05:47:27` = `runs/smoke-t16/evidence/round/evidence_refresh.txt` | **not written** — identical to the pre-batch reading |
| `.workspace/**` | **851** files; newest mtime `2026-10-03T16:44:24` = `.workspace/fresh-t16/.godot/scene_groups_cache.cfg` (epoch `1791017064.884`) | **not written** — hours before this session's first write, and the same value the DR-89 batch recorded |
| frozen specification `.spec/hof-rs/PRD-mario.md` | `4c81c3a9…`, 5,375 B | unchanged |
| `DECISIONS.md` | `9f95f26e…`, 1,243,889 B | unchanged (forbidden zone, honoured) |
| `.spec/hof-rs/REQUIREMENTS.md` | `4982bf1c…`, 28,690 B | unchanged; the 20,910-byte DR-80 seal was never touched |
| `Cargo.toml` / `Cargo.lock` | `e0c4992b…` / `d98fa915…` | unchanged; no dependency added |
| `config/hoh.yaml` | `835b6b0e…` | unchanged |
| legacy adapter `src/adapter/godot.rs` | `27fda15a…`, 333,482 B | unchanged |
| engine tree `godot-mcp/**` | `git -C godot-mcp/godot status --porcelain` = **0 bytes** (engine HEAD `fc63af77…`) | untouched |
| `.spec/hof-rs/tasks/TASK-DR88-REPORT.md` | `e6b949ef…`, 27,589 B | unchanged |
| git | start HEAD `7a8e047…`; now `HEAD 85b3d35…` (the dispatcher's commit of this batch) with `origin/master 55a0751…`, **ahead 16**; `git status --porcelain` = ` M .spec/hof-rs/tasks/TASK-DR90-REPORT.md` (this report's corrected working copy) + the four pre-existing untracked leftovers `l.json`/`p2.json`/`pv.json`/`r.json` | **I staged, committed and pushed nothing**; the dispatcher committed the two source files (blobs identical to the measured bytes), and **nothing was pushed** |
| line endings | `integrity.rs` 61,842 B / CR=0 / LF=1,305; `append_only_guard.rs` 44,195 B / CR=0 / LF=1,042 | pure LF, matching the tracked blobs |
| dangerous actions | no `rm -rf` (fingerprint clearing is Python `glob`+`shutil.rmtree` on printed, asserted paths inside `target/`); no `git checkout --`; no path built from an unexpanded variable | clean |
| network / engine | no network, no engine started or driven, no round run, no game hand-written | clean |
| other forbidden changes | no criterion, no jump-honesty rule, no artifact-gate classification, no rejecting semantics for a contaminated candidate, no test removed, `ignored` still 7 | clean |

---

## 9. Residual risks — measured vs inferred

### 9.1 Measured (this batch, offline)

1. `DR89A-1` closed: `G3/G2/N2/N4` and my `H1/H2/H4/H5/H12/H13` are 1 at DR-89 and 0 at DR-90.
2. `DR89A-2` closed: `G5/H3/H6/H8/H10` were 1 at parent, DR-88 **and** DR-89, and are 0 at DR-90.
3. Every restored truncation finding survives with the same kind and line: `B2/B3/B3b/B5/B5b` and
   `C25/C26/C27` (section 2.1).
4. No regression in the earlier false-positive closures (`L2/L3/L9/N1/C1` = 0) or in the intended
   tightenings (`X3/X4/X6/X7/X9/X10` = 1, `B1` = 2, `R1` = 1).
5. The converse holds: `A5`/`A6`/`A18`/`A10` show the guard still catches a fragment behind a comment,
   and `A24` shows the balance rule still fires without a `;`.
6. The `#`-divergence tightening is measured: `A11/A19/A25` 0 → 1, `A12` stays 0.
7. Gate: literal `cargo test --offline` exit **0**; **653 / 0 / 7**; 62 suites; `--list` 660; `fmt` 0;
   63 fingerprints cleared; 101 tracked `.rs` touched; `REMOVED=[]`; `ADDED` = exactly the five new
   tests; `#[ignore]` 7 in both revisions; no second test process before or after.
8. Five plants, control-green / exit-101 / byte-exact restore / control-green, `[:]`.
9. The correction-discipline pin is load-bearing on the real bytes (P5) and non-vacuous in memory.
10. Forbidden zones: `runs/**` 7,341 files with an unmoved newest mtime; `.workspace/**` 851 files
    with an unmoved newest mtime; engine tree porcelain 0 bytes.

### 9.2 Inferred (not measured here)

1. **Real-round behaviour.** No engine and no round were run, so "a legitimately delivered `.tscn`
   with a `;` comment is now accepted by the audit and still rejected by the gate if it is a fragment"
   is a mechanism reading off the injected `audit_text`, not an observation of a round. The same holds
   for whether an engine-written product ever carries a `;` comment (engine writers do not comment).
2. **A bare `#` in a real product.** R7 (the writer emits `Color(r, g, b, a)`) makes it implausible,
   but I did not audit any real corpus; the tightening in section 5.3 is source-backed, not
   corpus-backed.
3. **A real `.gd` that uses `;` as if it were a comment.** R5 says such a file is not GDScript, and
   `A10` catches a fragment behind it; whether a role ever emits that shape is inferred.
4. **Whether the label-stripping mutant is exactly the original `52d73d3` line.** I measured the
   original line's length (345 B) and that it contains exactly one occurrence of the clause
   (`dr88_lines.py`), and the pin's mutant removes every DR-88 label from that line; I did not embed
   the historical bytes in the test, because a test cannot read git history. The property under test —
   "the clause is labelled on its own line" — is what the mutant exercises.
5. **The 7 `#[ignore]`d real-engine tests** and any hardware round: not runnable offline.

### 9.3 Deliberately left open (declared, with measurements)

| id | content | disposition |
|---|---|---|
| DR89A-1 | the `;` comment's apostrophe/quote false red | **closed** |
| DR89A-2 | the `;` comment's delimiter false red | **closed** |
| DR89A-3 | the in-place DR-88 correction | **decided and pinned** (section 6); the file is unchanged |
| new | a file cut **inside** a `;` comment / ending at `;` is not reported (`G5`, `A3`, `A4`, `A20`, `A21`, `A22`) | **declared**: the same bytes are the false positive that had to go; a comment has no closing delimiter (section 5.2) |
| new | a resource line whose `#` carries a delimiter or a quote is now reported (`A11/A19/A25`) | **declared tightening**, source-backed by R6/R7 (section 5.3) |
| new | `audit_text`'s `#`-in-a-resource divergence is now named and test-pinned instead of silent | the divergence is now *correct* in both rules; the model no longer contradicts the reader |

---

## 10. The two decisions this batch makes (and why they are not in `DECISIONS.md`)

The task makes `DECISIONS.md` a forbidden zone, so the decision log entries live here; the file is
byte-identical to the revision I started from (`9f95f26e…`, 1,243,889 B), and no other tracked file
was touched.

**D-A — the comment rule is the reader's rule, per extension.** Trigger: `DR89A-1`/`DR89A-2`. Options
considered: (1) add `;` to the one global comment character — rejected, because a `.gd` `;` is a
`SEMICOLON` token (R5) and making it global blinds the script rule; (2) keep `#` for resources and add
`;` — rejected, because `#` in a resource is the colour token (R6) and treating it as a comment is a
false premise in the permissive direction; (3) **chosen**: `line_comment(extension)` returns `#` for
`gd` and `;` for `tscn`/`tres`, threaded into all three consumers. Consequence: the fixture of
`delimiters_inside_literals_and_comments_are_not_counted` moved from `#` to `;` to stop asserting a
false premise; the `#` direction became a measured tightening. Rollback point: `src/runtime/integrity.rs`
at `9b203999…` and `tests/append_only_guard.rs` at `556faf44…`, both snapshotted before the first edit.

**D-B — the in-place DR-88 correction stands as a labelled quotation, enforced by a new pin.** Trigger:
`DR89A-3`. Options considered: (1) restore the original line and append an erratum — rejected, it
re-asserts a false claim in a repository file and contradicts the accepted `C7`; (2) leave the file and
say nothing more — rejected, a decision that is not checked decays; (3) **chosen**: leave the file
byte-identical and add `the_dr88_false_clause_survives_only_as_a_labelled_quotation`, which forbids an
**unlabelled** occurrence anywhere in the file while permitting appends. Rollback point: the removal of
one `#[test]` plus three constants; no other file changes.

---

## 11. What I did not do

- No engine started/restarted/driven; no round run; no network; no game hand-written.
- Nothing written under `runs/**` or any workspace directory.
- `DECISIONS.md`, the frozen specification, the engine tree, the legacy adapter, `Cargo.toml`/
  `Cargo.lock`, `config/hoh.yaml` and `TASK-DR88-REPORT.md` untouched.
- No test removed or renamed; no criterion, jump-honesty rule, artifact-gate classification or
  rejecting semantics changed; `#[ignore]` still 7.
- Nothing staged, committed or pushed **by me**; the pre-push gate was not run against the remote. The
  dispatcher committed the two source files and the first revision of this report as `85b3d35` while
  the report was being finished (section 0); `origin/master` is unmoved, so nothing was pushed.
- Inside the repository I only: edited the two files above, cleared 63 gitignored
  `target/debug/.fingerprint/hof-rs-*` directories (each path printed before removal), touched the
  mtimes of 101 tracked `.rs` files individually, and wrote this report. The probe, the revision
  copies, the logs and every helper script live outside the repository.
