#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-147 C6b: make the SHIPPED pytest suite itself go red, through real pytest.

A transient conftest.py (created in tools/tests/ and deleted immediately after)
monkeypatches `read_matrix()` to return a copy with the section-1.1 TOTAL bumped.
The real test file is NOT edited; its sha256 is compared before and after.
"""
import io, os, subprocess, sys, hashlib

CONFTEST = os.path.abspath("tools/tests/conftest.py")
TRACKED = [
    "recovery/TEST-CASES.md",
    "tools/tests/test_matrix_self_consistency.py",
]

CONFTEST_TEXT = u'''# transient TASK-147 acceptance harness -- removed immediately after the run
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_matrix_self_consistency as _msc

_real_read_matrix = _msc.read_matrix


def _read_matrix_mutated():
    text = _real_read_matrix()
    return _msc.TOTAL_RE.sub(
        lambda m: u"| **\\u5408\\u8ba1** | **%d** | |" % (int(m.group(1)) + 1),
        text, count=1)


_msc.read_matrix = _read_matrix_mutated
'''


def digest(path):
    return hashlib.sha256(io.open(path, "rb").read()).hexdigest()


before = {p: digest(p) for p in TRACKED}
print("sha256 before:", before)

assert not os.path.exists(CONFTEST), "a real conftest.py exists; refusing to touch it"
io.open(CONFTEST, "w", encoding="utf-8").write(CONFTEST_TEXT)
try:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest",
         "tools/tests/test_matrix_self_consistency.py", "-q", "--no-header",
         "-p", "no:cacheprovider"],
        cwd=os.path.abspath("."), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = proc.stdout.decode("utf-8", "replace")
    print("\n--- pytest with the matrix's TOTAL bumped in memory ---")
    sys.stdout.write(out[-2500:])
    print("exit code:", proc.returncode)
finally:
    os.remove(CONFTEST)

after = {p: digest(p) for p in TRACKED}
print("\nsha256 after :", after)
print("untouched    :", before == after)
print("conftest removed:", not os.path.exists(CONFTEST))

print("\n--- and the pristine run, for comparison ---")
proc2 = subprocess.run(
    [sys.executable, "-m", "pytest",
     "tools/tests/test_matrix_self_consistency.py", "-q", "--no-header",
     "-p", "no:cacheprovider"],
    cwd=os.path.abspath("."), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
sys.stdout.write(proc2.stdout.decode("utf-8", "replace")[-800:])
print("exit code:", proc2.returncode)
