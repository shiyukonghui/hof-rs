#!/usr/bin/env python3
"""TASK-114 -- dual-parse / policy checker for the SAC toolkit in dist\\tools\\.

Rule check (hard constraints given to this task):
  * no shell redirection anywhere in the toolkit's own commands  (not applicable to file content)
  * the diagnose script must be READ-ONLY: only Get-* / read cmdlets
  * the unblock script must only ever call Unblock-File, and only behind -Apply
  * nothing may write the registry / change SAC / SmartScreen / Defender / WDAC
  * the .ps1 files must be pure ASCII so Windows PowerShell 5.1 parses them
    identically regardless of code page / BOM

This script is the PYTHON half of the "Python + PS 5.1 dual parse" rule. The PS 5.1 half
is the [Parser]::ParseFile check run separately and recorded in the task report.

Exit code 0 = all checks pass, 1 = at least one check failed.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))  # godot-mcp
TOOLS = os.path.join(ROOT, "dist", "tools")
README = os.path.join(ROOT, "dist", "README-SAC.md")

DIAGNOSE = os.path.join(TOOLS, "sac_diagnose.ps1")
UNBLOCK = os.path.join(TOOLS, "unblock_package.ps1")

# Anything that could change the machine. None of these may appear as executable code.
FORBIDDEN_ANYWHERE = [
    "Set-ItemProperty",
    "New-ItemProperty",
    "Remove-ItemProperty",
    "Clear-ItemProperty",
    "Rename-ItemProperty",
    "Set-MpPreference",
    "Add-MpPreference",
    "Set-CimInstance",
    "Invoke-CimMethod",
    "bcdedit",
    "gpupdate",
    "Set-ExecutionPolicy",
    "New-Item ",
    "Remove-Item ",
    "Move-Item ",
    "Rename-Item ",
    "Set-Content",
    "Add-Content",
    "Out-File",
    "Remove-ItemProperty",
    "Stop-Service",
    "Set-Service",
    "Start-Process",
    "reg add",
    "reg delete",
    "reg import",
    "netsh ",
    "schtasks",
    "takeown",
    "icacls",
]

# The diagnose script must not even mention Unblock-File as code.
FORBIDDEN_IN_DIAGNOSE = FORBIDDEN_ANYWHERE + ["Unblock-File"]

results = []
ok = True


def check(name, passed, detail):
    global ok
    if not passed:
        ok = False
    results.append({"check": name, "pass": bool(passed), "detail": detail})
    print(("PASS " if passed else "FAIL ") + name + "  -- " + detail)


def strip_comments_and_strings(src):
    """Very small PowerShell 'code only' reducer.

    Removes <# ... #> block comments, # line comments, and the bodies of quoted
    strings, so that a forbidden token appearing only in help text / a message is
    not reported as executable code. Good enough for this audit.
    """
    out = []
    i = 0
    n = len(src)
    while i < n:
        if src.startswith("<#", i):
            j = src.find("#>", i + 2)
            i = n if j < 0 else j + 2
        elif src[i] == "#":
            j = src.find("\n", i)
            i = n if j < 0 else j
        elif src[i] == "'":
            j = src.find("'", i + 1)
            i = n if j < 0 else j + 1
        elif src[i] == '"':
            j = i + 1
            while j < n:
                if src[j] == "`":
                    j += 2
                    continue
                if src[j] == '"':
                    break
                j += 1
            i = n if j >= n else j + 1
        else:
            out.append(src[i])
            i += 1
    return "".join(out)


def read_bytes(path):
    with open(path, "rb") as fh:
        return fh.read()


# ------------------------------------------------------------------ 1. existence
for path in (DIAGNOSE, UNBLOCK, README):
    check("exists: " + os.path.basename(path), os.path.isfile(path), path)

if not all(os.path.isfile(p) for p in (DIAGNOSE, UNBLOCK, README)):
    print(json.dumps(results, indent=2, ensure_ascii=False))
    sys.exit(1)

# ------------------------------------------------------------------ 2. ASCII only
for path in (DIAGNOSE, UNBLOCK):
    raw = read_bytes(path)
    try:
        raw.decode("ascii")
        check("ascii-only: " + os.path.basename(path), True, "%d bytes, 0 non-ASCII" % len(raw))
    except UnicodeDecodeError as exc:
        check("ascii-only: " + os.path.basename(path), False, str(exc))
        continue
    check(
        "no-BOM: " + os.path.basename(path),
        not raw.startswith(b"\xef\xbb\xbf"),
        "first bytes = %r" % raw[:4],
    )

# ------------------------------------------------------------------ 3. forbidden tokens
diag_src = read_bytes(DIAGNOSE).decode("ascii", "replace")
diag_code = strip_comments_and_strings(diag_src)
hits = [t for t in FORBIDDEN_IN_DIAGNOSE if t in diag_code]
check(
    "sac_diagnose.ps1 is read-only",
    not hits,
    "no write/security-mutating cmdlet in executable code" if not hits else "FOUND: %s" % hits,
)

unb_src = read_bytes(UNBLOCK).decode("ascii", "replace")
unb_code = strip_comments_and_strings(unb_src)
hits = [t for t in FORBIDDEN_ANYWHERE if t in unb_code]
check(
    "unblock_package.ps1 touches nothing but Unblock-File",
    not hits,
    "no forbidden cmdlet in executable code" if not hits else "FOUND: %s" % hits,
)

# Unblock-File must be gated behind -Apply.
gate = "if ($Apply -and $motwCount -gt 0)"
idx_gate = unb_code.find(gate)
idx_unb = unb_code.find("Unblock-File")
check(
    "Unblock-File is gated behind -Apply",
    idx_gate >= 0 and idx_unb > idx_gate,
    "gate at %d, Unblock-File at %d" % (idx_gate, idx_unb),
)

# The diagnose script must not call Unblock-File in executable code either.
check(
    "sac_diagnose.ps1 never calls Unblock-File",
    "Unblock-File" not in diag_code,
    "not present in executable code (the help text may still name it)"
    if "Unblock-File" not in diag_code
    else "FOUND in executable code",
)

# ------------------------------------------------------------------ 4. README has no auto-fix code
readme = open(README, encoding="utf-8").read()
reg_writes = ["reg add", "reg delete", "Set-ItemProperty", "New-ItemProperty", "Set-MpPreference"]
negations = ["\u274c", "\u4e0d\u4fee\u6539", "\u4e0d\u505a"]  # cross mark, "does not modify", "does not do"
bad_context = []
for tok in reg_writes:
    start = 0
    while True:
        idx = readme.find(tok, start)
        if idx < 0:
            break
        window = readme[max(0, idx - 220):idx]
        if not any(neg in window for neg in negations):
            bad_context.append((tok, idx, readme[max(0, idx - 80):idx].replace("\n", " | ")))
        start = idx + 1
# A registry-write token is only acceptable inside an explicit "we do NOT do this" list.
check(
    "README-SAC.md has no registry-write command outside a negation list",
    not bad_context,
    "0 occurrences"
    if not any(t in readme for t in reg_writes)
    else "all occurrences sit next to an explicit negation (x / '\u4e0d\u4fee\u6539' / '\u4e0d\u505a')"
    if not bad_context
    else "UNGUARDED: %s" % bad_context,
)

# The three exits must all be documented.
for needle, label in [
    ("关闭", "exit 1: turn SAC off"),
    ("代码签名证书", "exit 2: reputable code signing certificate"),
    ("Sandbox", "exit 3: run in a SAC-off machine / VM / Windows Sandbox"),
    ("不可逆", "the irreversibility warning"),
]:
    check("README documents " + label, needle in readme, "found" if needle in readme else "MISSING")

# ------------------------------------------------------------------ summary
print("")
print(json.dumps({"ok": ok, "checks": len(results), "failed": [r for r in results if not r["pass"]]}, indent=2, ensure_ascii=False))
sys.exit(0 if ok else 1)
