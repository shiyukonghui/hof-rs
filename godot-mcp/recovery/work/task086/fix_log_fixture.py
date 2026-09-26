# -*- coding: utf-8 -*-
"""Replace fixed line spans of the test header with the recorded `new` of two
edits (seq=756 and seq=758, TASK-006 section 3.3), so the two log fixtures carry
their non-ASCII line as a C++ hex-escaped literal instead of a narrow literal
that `String(const char *)` decodes as Latin-1.
"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"
TARGET = r"H:\rebuild\godot\modules\mcp_server\tests\test_mcp_server.h"
SUB = "tests\\test_mcp_server.h"


def load_new(seq):
    with io.open(os.path.join(IDX, "events-edit.jsonl"), "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if str(r.get("seq")) == str(seq) and SUB in (r.get("path") or "").replace("/", "\\").lower():
                return r
    raise SystemExit("FATAL: no edit seq=%s for %s" % (seq, SUB))


text = io.open(TARGET, encoding="utf-8").read()
lines = text.split("\n")

# (start_line, end_line, seq) - 1-based, inclusive; the last line is `CHECK(log.ok);`
SPANS = [(3119, 3128, 756), (3213, 3220, 758)]

for start, end, seq in sorted(SPANS, reverse=True):
    row = load_new(seq)
    new = row.get("new") or ""
    block = "\n".join(lines[start - 1:end])
    if lines[start - 1] != 'TEST_CASE("[MCPServer] %s") {' % (
            "editor_get_errors reports the ERROR lines of the log tail" if seq == 756
            else "editor_get_output_log filters the tail case sensitively"):
        raise SystemExit("FATAL: line %d is not the expected TEST_CASE" % start)
    if lines[end - 1].strip() != "CHECK(log.ok);":
        raise SystemExit("FATAL: line %d is not `CHECK(log.ok);`" % end)
    print("span %d-%d -> recorded seq=%s : %d -> %d lines" % (start, end, seq, end - start + 1, len(new.split("\n"))))
    lines[start - 1:end] = new.split("\n")

out = "\n".join(lines)
io.open(TARGET, "w", encoding="utf-8", newline="").write(out)
print("rewrote %s (%d -> %d bytes)" % (TARGET, len(text), len(out)))
