#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-147 C: adversarial proof that the self-consistency checkers really go red.

Read-only: the tracked matrix is never written.  Every mutation happens in memory
on a COPY loaded from disk, exactly like the shipped guard does.
"""
import io, os, sys, collections

sys.path.insert(0, os.path.abspath("tools/tests"))
import test_matrix_self_consistency as msc

good = msc.read_matrix()
print("== baseline on the real file ==")
print("  check_statistics complaints :", msc.check_statistics(good))
print("  check_references complaints :", msc.check_references(good))
print("  declared_statistics         :", msc.declared_statistics(good))
print("  count_body_rows             :", msc.count_body_rows(good))


def show(label, complaints):
    print("\n-- %s --" % label)
    print("   n complaints = %d" % len(complaints))
    for c in complaints[:4]:
        print("   * %s" % c)
    assert complaints, "VACUOUS: %s produced NO complaint" % label


# --- break 1: section 1.1 TOTAL bumped by one (statistics) ---
show("break 1: section 1.1 TOTAL 788 -> 789", msc.check_statistics(msc._bump_total(good)))

# --- break 2: one numbered row deleted (statistics AND references) ---
show("break 2a: one TC-PY row dropped", msc.check_statistics(msc._drop_one_py_row(good)))
show("break 2b: one TC-PY row dropped (references)", msc.check_references(msc._drop_one_py_row(good)))

# --- break 3: first pytest row renamed to a test that does not exist ---
show("break 3: first TC-PY pytest row -> test_task146_deliberately_missing",
     msc.check_references(msc._rename_first_pytest_row(good)))

# --- break 4 (mine): a single FAMILY declaration bumped, rest untouched ---
mut = good.replace(u"| `TC-ENG-NNN` | 159 |", u"| `TC-ENG-NNN` | 158 |", 1)
assert mut != good, "family-declaration mutation did not apply"
show("break 4: only TC-ENG declared 159 -> 158", msc.check_statistics(mut))

# --- break 5 (mine): a printed-case row renamed so it is printed by nobody ---
import re
pat = re.compile(r"^(\| TC-PY-test_playability_p7\.py:)([^|\s]+)", re.M)
m = pat.search(good)
assert m, "no p7 printed row found"
mut5 = good[:m.start(2)] + "no such printed case" + good[m.end(2):]
show("break 5: a p7 printed-case row renamed", msc.check_references(mut5))

# --- break 6 (mine): expand the TOTAL cell without touching the declaration rows ---
mut6 = msc.TOTAL_RE.sub(lambda mm: u"| **\u5408\u8ba1** | **%d** | |" % (int(mm.group(1)) + 7),
                        good, count=1)
show("break 6: TOTAL +7 (family cells left alone)", msc.check_statistics(mut6))

# --- break 7 (mine): a pytest FILE that is absent from the matrix entirely ---
#   drop *all* rows of one pytest file -> both checkers must complain
mut7 = u"\n".join(l for l in good.splitlines()
                  if not l.startswith("| TC-PY-test_matrix_self_consistency.py:"))
mut7 += u"\n"
show("break 7a: all 3 self-consistency rows removed", msc.check_statistics(mut7))
show("break 7b: all 3 self-consistency rows removed (references)", msc.check_references(mut7))

# --- break 8: only one family declared, the others deleted from section 1.1 ---
mut8 = re.sub(r"^\|\s*`TC-(TOOL|GATE|M1|ENG|CONS)-[^`]*`\s*\|\s*\d+[^\n]*\n", "", good, flags=re.M)
show("break 8: five of six family declaration rows deleted", msc.check_statistics(mut8))
print("\nmut8 declaration block:", msc.declared_statistics(mut8))
