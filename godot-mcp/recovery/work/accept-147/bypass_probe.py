#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-147 C7: prove the bypass -- a NEW pytest file with no matrix rows escapes BOTH checkers.

Transiently creates tools/tests/test_accept147_bypass_probe.py, runs the shipped
checkers, then removes the file and re-verifies the tracked files are untouched.
"""
import io, os, sys, hashlib

sys.path.insert(0, os.path.abspath("tools/tests"))
import test_matrix_self_consistency as msc

PROBE = os.path.abspath("tools/tests/test_accept147_bypass_probe.py")
TRACKED = ["recovery/TEST-CASES.md", "tools/tests/test_matrix_self_consistency.py"]


def digest(path):
    return hashlib.sha256(io.open(path, "rb").read()).hexdigest()


before = {p: digest(p) for p in TRACKED}
print("sha256 before:", before)

io.open(PROBE, "w", encoding="utf-8").write(
    "# transient TASK-147 acceptance probe\n"
    "def test_a_brand_new_suite_nobody_added_to_the_matrix():\n"
    "    assert True\n")
try:
    good = msc.read_matrix()
    st = msc.check_statistics(good)
    rf = msc.check_references(good)
    print("\nwith a new pytest file present that has ZERO matrix rows:")
    print("  check_statistics complaints :", st)
    print("  check_references complaints :", rf)
    print("  body row counts             :", msc.count_body_rows(good))
    print("  => both checkers green while pytest would collect one more test:",
          st == [] and rf == [])
finally:
    os.remove(PROBE)

after = {p: digest(p) for p in TRACKED}
print("\nsha256 after :", after)
print("untouched    :", before == after)
print("probe exists :", os.path.exists(PROBE))
