#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-146 B7 -- prove that tools/tests/test_matrix_self_consistency.py really
goes RED when recovery/TEST-CASES.md is deliberately made inconsistent, then
restore the file and prove its sha256 is unchanged.

Nothing here uses shell redirection: every artifact is written through a Python
file handle, and pytest is invoked via subprocess with stdout captured.

Writes: recovery/work/task146/red-proof.json  (raw pytest output for each case)
"""
from __future__ import print_function

import hashlib
import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
MATRIX = os.path.join(REPO, "recovery", "TEST-CASES.md")
TEST = os.path.join(REPO, "tools", "tests", "test_matrix_self_consistency.py")
OUT = os.path.join(HERE, "red-proof.json")
PYTEST = [sys.executable, "-m", "pytest",
          os.path.join("tools", "tests", "test_matrix_self_consistency.py"),
          "-q", "--no-header", "-p", "no:cacheprovider"]


def sha256(path):
    digest = hashlib.sha256()
    with io.open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def read(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def write(path, text):
    with io.open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def run_pytest():
    proc = subprocess.run(PYTEST, cwd=REPO, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def mutate_statistics(text):
    """Section 1.1 TOTAL 788 -> 789 (the exact TASK-144 defect shape)."""
    before = u"| **\u5408\u8ba1** | **788** | |"
    assert before in text, "TOTAL row not found"
    return text.replace(before, u"| **\u5408\u8ba1** | **789** | |", 1)


def mutate_reference(text):
    """Point one matrix row at a test name that does not exist."""
    before = "TC-PY-test_contract_forms.py:test_the_contract_carries_177_tools"
    assert before in text, "row not found"
    return text.replace(
        before, "TC-PY-test_contract_forms.py:test_task146_deliberately_missing", 1)


def mutate_row_count(text):
    """Delete one numbered row (the defect shape: a row count that is too low)."""
    marker = "| TC-PY-test_coverage_batch_consistency.py:test_the_manifests_exist |"
    lines = text.splitlines(True)
    kept = [ln for ln in lines if not ln.startswith(marker)]
    assert len(kept) == len(lines) - 1, "row not found"
    return "".join(kept)


CASES = (
    ("A_statistics_total_and_body_disagree", mutate_statistics,
     "section 1.1 TOTAL says 789 while the body has 788 rows"),
    ("B_a_row_names_a_test_that_does_not_exist", mutate_reference,
     "one TC-PY row names test_task146_deliberately_missing"),
    ("C_one_numbered_row_was_removed", mutate_row_count,
     "a TC-PY row was deleted from the body"),
)


def main():
    original = read(MATRIX)
    hash_before = sha256(MATRIX)
    results = []
    try:
        for name, mutate, what in CASES:
            mutated = mutate(original)
            assert mutated != original
            write(MATRIX, mutated)
            code, output = run_pytest()
            results.append({"case": name, "mutation": what,
                            "exit": code, "red": code != 0, "output": output})
            print("=== %s (%s)" % (name, what))
            print(output.rstrip())
            print("")
    finally:
        write(MATRIX, original)

    hash_after = sha256(MATRIX)
    # the restored file must also be green again
    code_green, output_green = run_pytest()
    payload = {
        "matrix": MATRIX,
        "sha256_before_demos": hash_before,
        "sha256_after_restore": hash_after,
        "sha256_unchanged": hash_before == hash_after,
        "restored_pytest_exit": code_green,
        "restored_pytest_output": output_green,
        "cases": results,
    }
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")

    print("sha256 before demos : %s" % hash_before)
    print("sha256 after restore: %s" % hash_after)
    print("UNCHANGED=%s" % (hash_before == hash_after))
    print("restored suite exit=%d" % code_green)
    print(output_green.rstrip())
    print("evidence: %s" % OUT)
    all_red = all(c["red"] for c in results)
    print("ALL_DEMOS_WENT_RED=%s" % all_red)
    return 0 if (all_red and hash_before == hash_after and code_green == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
