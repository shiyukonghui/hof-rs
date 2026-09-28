#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""test_matrix_self_consistency.py -- `recovery/TEST-CASES.md` must agree with itself.

WHY THIS EXISTS (TASK-146, durable fix for the TASK-145 blocker)
----------------------------------------------------------------
The use-case matrix `recovery/TEST-CASES.md` publishes a per-family count table
in its section 1.1 (`TC-TOOL-*` 177, `TC-GATE-gNN` 10, `TC-M1-*` 22,
`TC-ENG-NNN` 159, `TC-PY-*` N, `TC-CONS-*` 13, and a TOTAL). That table is a
CLAIM about the body of the same file. TASK-144 edited the claim (TC-PY 400 ->
404, total 781 -> 785) but never added the four rows it was counting, and it
renamed two `test_coverage_batch_consistency.py` tests without updating the two
matrix rows that name them. TASK-145 measured the disagreement and returned
`verdict = fail`; nothing in the repo could have caught it, because the numbers
were only ever checked by eye.

This file makes the claim EXECUTABLE:

  * `check_statistics()` re-counts the numbered rows OF THE BODY (a row is a
    markdown table line whose first cell starts with `TC-<FAMILY>-`) and
    compares every family and the total against section 1.1 -- any mismatch is
    a complaint, and the pytest test over it fails;
  * `check_references()` re-resolves every `TC-PY-*` row's named test against
    the repository, according to how the row says the name is produced:
        pytest  -> the file really has `def <name>(`,
        script check -> the file really has a `["<name>"]` key,
        printed case -> running the file really prints `<name>`;
    plus: a pytest file's number of `def test_*` functions must equal its
    number of pytest rows (so adding a test without a row is red too);
  * the third test is the non-vacuity guard: it feeds deliberately inconsistent
    matrix TEXT through the same checkers and demands that they complain. If a
    checker ever degrades into a no-op, that test -- not the doc -- goes red.

Both checkers take the matrix text as an argument (they do not secretly re-read
the file), which is what makes the guard above possible.

Run:
    D:\\Anaconda\\python.exe -m pytest tools\\tests\\test_matrix_self_consistency.py -q
    D:\\Anaconda\\python.exe tools\\tests\\test_matrix_self_consistency.py
"""
from __future__ import print_function

import html
import io
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS_DIR)
MATRIX = os.path.join(ROOT, "recovery", "TEST-CASES.md")

# The families section 1.1 is required to account for, in table order.
FAMILIES = ("TC-TOOL", "TC-GATE", "TC-M1", "TC-ENG", "TC-PY", "TC-CONS")

# A numbered row: the first cell of a markdown table row is `TC-<FAMILY>-...`.
ROW_RE = re.compile(r"^\|\s*(TC-[A-Z0-9]+)-")
# A section-1.1 declaration row: | `TC-PY-*` | 407 | ... |
DECL_RE = re.compile(r"^\|\s*`(TC-[A-Z0-9]+)-[^`]*`\s*\|\s*\*{0,2}(\d+)")
# The section-1.1 total row: | **合计** | **788** | |
TOTAL_RE = re.compile(u"^\\|\\s*\\*\\*\u5408\u8ba1\\*\\*\\s*\\|\\s*\\*\\*(\\d+)\\*\\*", re.M)
# TC-PY ids are `TC-PY-<file>:<name>` (the file basename never contains ':').
PY_ID_RE = re.compile(r"^TC-PY-([^:]+):(.*)$")


def read_matrix():
    with io.open(MATRIX, "r", encoding="utf-8") as handle:
        return handle.read()


def _unescape(text):
    """The matrix HTML-escapes `->`/`<`/`&` (it is also rendered as HTML)."""
    return html.unescape(text)


def count_body_rows(text):
    """{family: n} for the numbered rows of the matrix body."""
    counts = dict((f, 0) for f in FAMILIES)
    for line in text.splitlines():
        match = ROW_RE.match(line)
        if match and match.group(1) in counts:
            counts[match.group(1)] += 1
    return counts


def declared_statistics(text):
    """({family: n}, total) as declared by the section 1.1 table."""
    declared, total = {}, None
    inside = False
    for line in text.splitlines():
        if line.strip().startswith("### 1.1"):
            inside = True
            continue
        if inside and line.strip().startswith("### "):
            break
        if not inside:
            continue
        match = DECL_RE.match(line)
        if match:
            declared[match.group(1)] = int(match.group(2))
        match = TOTAL_RE.match(line)
        if match:
            total = int(match.group(1))
    return declared, total


def tc_py_rows(text):
    """[{line, id, src, name, note}] for every `TC-PY-*` row of the body."""
    rows = []
    for lineno, line in enumerate(text.splitlines(), 1):
        stripped = line.rstrip()
        if not stripped.startswith("| TC-PY-"):
            continue
        cells = [c.strip() for c in stripped.split("|")]
        ident = cells[1]
        src = cells[2].strip("`")
        note = cells[-2]
        match = PY_ID_RE.match(ident)
        rows.append({
            "line": lineno,
            "id": ident,
            "src": src,
            "name": match.group(2) if match else "",
            "note": note,
        })
    return rows


def kind_of(note):
    if u"pytest 条目" in note:
        return "pytest"
    if u"脚本内 check" in note:
        return "script_check"
    if u"自打印的 case 名" in note:
        return "printed"
    return "unknown"


# ---------------------------------------------------------------------------
# checker 1: the section 1.1 numbers must equal the body's numbered rows
# ---------------------------------------------------------------------------
def check_statistics(text):
    """Complaints about section 1.1 disagreeing with the body of the file."""
    complaints = []
    body = count_body_rows(text)
    declared, total = declared_statistics(text)
    for family in FAMILIES:
        want = declared.get(family)
        got = body.get(family, 0)
        if want is None:
            complaints.append("section 1.1 declares no `%s-*` row" % family)
        elif want != got:
            complaints.append(
                "`%s-*`: section 1.1 says %d, the body has %d numbered row(s)"
                % (family, want, got))
    body_total = sum(body.values())
    if total is None:
        complaints.append("section 1.1 has no TOTAL row")
    elif total != body_total:
        complaints.append("TOTAL: section 1.1 says %d, the body has %d row(s)"
                          % (total, body_total))
    return complaints


# ---------------------------------------------------------------------------
# checker 2: every TC-PY row must name something that really exists
# ---------------------------------------------------------------------------
_PRINTED_CACHE = {}


def printed_case_names(rel_path):
    """The case names the given file really prints, by running it."""
    if rel_path in _PRINTED_CACHE:
        return _PRINTED_CACHE[rel_path]
    path = os.path.join(ROOT, rel_path.replace("/", os.sep))
    proc = subprocess.run([sys.executable, path], cwd=ROOT,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = proc.stdout.decode("utf-8", "replace")
    names = []
    base = os.path.basename(rel_path)
    for line in output.splitlines():
        if base == "test_playability_p7.py":
            # print("%s  %s" % ("ok  " if ok else "FAIL", name))
            if line.startswith("ok  ") or line.startswith("FAIL"):
                names.append(line[6:].rstrip())
        elif base == "test_playability_model_player.py":
            # print("%-58s %s" % (name[:58], "OK" if ok else "MISMATCH"))
            tail = line[59:] if len(line) > 59 else ""
            if len(line) >= 58 and (tail.startswith("OK") or tail.startswith("MISMATCH")):
                names.append(line[:58].rstrip())
    _PRINTED_CACHE[rel_path] = (names, proc.returncode)
    return _PRINTED_CACHE[rel_path]


def check_references(text):
    """Complaints about `TC-PY-*` rows naming tests that do not exist."""
    complaints = []
    rows = tc_py_rows(text)
    by_src = {}
    for row in rows:
        by_src.setdefault(row["src"], []).append(row)
    for src in sorted(by_src):
        group = by_src[src]
        kinds = {}
        for row in group:
            kinds.setdefault(kind_of(row["note"]), []).append(row)
        path = os.path.join(ROOT, src.replace("/", os.sep))
        if not os.path.exists(path):
            complaints.append("%s: %d TC-PY row(s) name a file that does not exist"
                              % (src, len(group)))
            continue
        with io.open(path, "r", encoding="utf-8") as handle:
            source = handle.read()

        defined = re.findall(r"^def test_[A-Za-z0-9_]*\(", source, re.M)
        pytest_rows = kinds.get("pytest", [])
        if len(defined) != len(pytest_rows):
            complaints.append(
                "%s: %d `def test_*` function(s) but %d pytest row(s) in the matrix"
                % (src, len(defined), len(pytest_rows)))

        for row in pytest_rows:
            if not re.search(r"^def %s\(" % re.escape(_unescape(row["name"])),
                             source, re.M):
                complaints.append(
                    "line %d: no `def %s(` in %s"
                    % (row["line"], row["name"], src))

        for row in kinds.get("script_check", []):
            key = '["%s"]' % _unescape(row["name"])
            if key not in source:
                complaints.append(
                    "line %d: no %s key in %s" % (row["line"], key, src))

        for row in kinds.get("unknown", []):
            complaints.append("line %d: unrecognised TC-PY note %r"
                              % (row["line"], row["note"]))

        if kinds.get("printed"):
            names, code = printed_case_names(src)
            if code != 0 or not names:
                complaints.append(
                    "%s: running it printed no case names (exit %s)" % (src, code))
                continue
            printed = set(_unescape(n) for n in names)
            for row in kinds["printed"]:
                if _unescape(row["name"]) not in printed:
                    complaints.append(
                        "line %d: `%s` is not printed by %s"
                        % (row["line"], row["name"], src))
    return complaints


# ---------------------------------------------------------------------------
# deliberately inconsistent inputs, for the non-vacuity guard
# ---------------------------------------------------------------------------
def _bump_total(text):
    """A copy whose section-1.1 TOTAL is one too high."""
    return TOTAL_RE.sub(lambda m: u"| **\u5408\u8ba1** | **%d** | |" % (int(m.group(1)) + 1),
                        text, count=1)


def _rename_first_pytest_row(text):
    """A copy whose first TC-PY row names a test that cannot exist."""
    match = re.search(r"^(\| TC-PY-)([^:|\s]+:)([^|\s]+)", text, re.M)
    if not match:
        raise AssertionError("no TC-PY row to mutate")
    start, end = match.span(3)
    return text[:start] + "test_task146_deliberately_missing" + text[end:]


def _drop_one_py_row(text):
    """A copy with one TC-PY numbered row deleted from the body."""
    match = re.search(r"^\| TC-PY-[^\n]*\n", text, re.M)
    if not match:
        raise AssertionError("no TC-PY row to drop")
    return text[:match.start()] + text[match.end():]


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------
def test_the_matrix_section_1_1_statistics_equal_its_own_rows():
    complaints = check_statistics(read_matrix())
    assert complaints == [], (
        "recovery/TEST-CASES.md section 1.1 disagrees with its own numbered rows:\n  "
        + "\n  ".join(complaints))


def test_every_tc_py_row_names_a_test_that_really_exists():
    complaints = check_references(read_matrix())
    assert complaints == [], (
        "recovery/TEST-CASES.md names tests that do not exist (or is missing rows "
        "for tests that do):\n  " + "\n  ".join(complaints))


def test_the_matrix_checker_goes_red_on_a_deliberately_inconsistent_matrix():
    """Non-vacuity guard: the checkers above must actually be able to complain."""
    good = read_matrix()
    assert check_statistics(good) == []
    assert check_references(good) == []
    assert check_statistics(_bump_total(good)), \
        "a TOTAL one too high did not make check_statistics() complain"
    assert check_statistics(_drop_one_py_row(good)), \
        "dropping a numbered row did not make check_statistics() complain"
    assert check_references(_rename_first_pytest_row(good)), \
        "a renamed pytest row did not make check_references() complain"
    assert check_references(_drop_one_py_row(good)), \
        "dropping a numbered row did not make check_references() complain"


def main():
    cases = []
    good = read_matrix()
    stat = check_statistics(good)
    cases.append(("section 1.1 statistics == the body's numbered rows",
                  stat == [], stat[:6]))
    decl, total = declared_statistics(good)
    body = count_body_rows(good)
    cases.append(("section 1.1 is present and complete",
                  set(decl) == set(FAMILIES) and total is not None,
                  {"declared": decl, "total": total, "body": body}))
    refs = check_references(good)
    cases.append(("every TC-PY row names a test that exists",
                  refs == [], refs[:6]))
    cases.append(("the statistics checker goes red on a bad TOTAL",
                  bool(check_statistics(_bump_total(good))), None))
    cases.append(("the statistics checker goes red on a dropped row",
                  bool(check_statistics(_drop_one_py_row(good))), None))
    cases.append(("the reference checker goes red on a renamed row",
                  bool(check_references(_rename_first_pytest_row(good))), None))
    failed = [c for c in cases if not c[1]]
    for name, ok, detail in cases:
        print("%s  %s" % ("ok  " if ok else "FAIL", name))
        if not ok:
            print("      detail: %s" % (detail,))
    print("\n%d/%d checks passed" % (len(cases) - len(failed), len(cases)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
