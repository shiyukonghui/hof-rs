#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-103 iron rule 5: parse a session file with Python before any engine starts.

Checks, in this order:

  * it is valid UTF-8 JSON (the parse the driver's `ConvertFrom-Json` will also do);
  * it has a `calls` array and every entry has a `port`, a `tag` unique in the file
    and either a `tool` or a `method`;
  * every `content_file` a call names resolves, relative to the session file's own
    directory (which is what `run_game_session.ps1` does with it);
  * `running_game_execute_gdscript` calls carry a non-empty `code` string.
"""

import io
import json
import os
import sys


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: check_session.py <session.json>")
    path = os.path.abspath(sys.argv[1])
    session_dir = os.path.dirname(path)
    with io.open(path, "rb") as handle:
        raw = handle.read()
    doc = json.loads(raw.decode("utf-8"))
    calls = doc.get("calls")
    if not isinstance(calls, list):
        sys.exit("FAIL: no 'calls' array")
    tags = set()
    failures = []
    editor = 0
    game = 0
    for index, call in enumerate(calls):
        tag = call.get("tag")
        if not tag:
            failures.append("call %d has no tag" % index)
            continue
        if tag in tags:
            failures.append("duplicate tag %s" % tag)
        tags.add(tag)
        port = call.get("port")
        if port not in ("editor", "game"):
            if "sleep_ms" in call:
                continue
            failures.append("%s: port %r" % (tag, port))
            continue
        if port == "editor":
            editor += 1
        else:
            game += 1
        if "tool" not in call and "method" not in call:
            failures.append("%s: neither tool nor method" % tag)
        arguments = call.get("arguments")
        if isinstance(arguments, dict) and "content_file" in arguments:
            target = os.path.join(session_dir, arguments["content_file"])
            if not os.path.isfile(target):
                failures.append("%s: content_file not found: %s" % (tag, target))
        if call.get("tool") == "running_game_execute_gdscript":
            code = arguments.get("code") if isinstance(arguments, dict) else None
            if not isinstance(code, str) or not code.strip():
                failures.append("%s: 'code' is not a non-empty string" % tag)
    print("file      : %s" % path)
    print("bytes     : %d" % len(raw))
    print("calls     : %d (editor %d / game %d)" % (len(calls), editor, game))
    print("utf8 json : OK")
    if failures:
        for item in failures:
            print("FAIL: %s" % item)
        sys.exit(1)
    print("CHECK_SESSION OK")


if __name__ == "__main__":
    main()
