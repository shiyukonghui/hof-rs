#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-144 item C: a stronger negative-evidence attempt for the two U2 tools.

U2 (TASK-143) registered `editor_simulate_mouse_click` and
`editor_simulate_mouse_move` as the only two contract tools with NO observed
failure of any kind: 0 calls in the corpus (`scope_excluded`, D59 / GDR-21), no
live probe, no engine test case that even names them for an illegal-input
assertion.

TASK-143's live probe left them `not_probed` under the rule "write-class tool
with no required argument: an illegal input cannot be constructed without
risking a real mutation". That rule is right about *value* probes and wrong
about *name* probes, and this script uses the difference:

  * `tool_registry.cpp:857-866` runs `_reject_unknown_arguments()` BEFORE
    `def->handler(...)` (`:880`), and `editor_input_simulation.cpp:1172/1201`
    registers `editor_simulate_mouse_click` / `editor_simulate_mouse_move` with
    the properties {button,pressed,x,y} / {x,y} (no `required`). A call whose
    argument bag carries ONLY an undeclared member name is therefore refused by
    the registry with `-32602 Unknown parameter ...` and the handler - the code
    that would inject a real editor input event (`mutating(true)`) - never runs.

So this is a probe of the *argument gate*, not of the tool's behaviour, and it
cannot move a mouse. The request is asserted to carry exactly one undeclared key
and no declared key, and the recorded response is checked to be a `-32602`
`Unknown parameter` refusal; an `ok` answer would abort the run instead of being
written up as evidence.

It starts the EDITOR endpoint only, on ONE private high port (default 9919), and
terminates it in `finally`. Output goes to `probe-u2.json` through a Python file
handle (never a shell redirect).

Usage:  python recovery/work/task144/probe_u2.py [--port 9919]
"""
import argparse
import importlib.util
import io
import json
import os
import socket
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
HARNESS = os.path.join(ROOT, "recovery", "work", "task143", "probe.py")
TARGETS = ["editor_simulate_mouse_click", "editor_simulate_mouse_move"]
UNDECLARED = "mcp144_undeclared_probe"

spec = importlib.util.spec_from_file_location("task143_probe", HARNESS)
harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(harness)


def port_free(port):
    s = socket.socket()
    try:
        s.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9919)
    ap.add_argument("--out", default=os.path.join(HERE, "probe-u2.json"))
    args = ap.parse_args()

    if not port_free(args.port):
        sys.stderr.write("probe_u2: port %d is already in use\n" % args.port)
        return 2

    scratch = os.path.join(harness.tempfile.gettempdir(), "task144-probe")
    project = os.path.join(scratch, "editor")
    logdir = os.path.join(scratch, "logs")
    for d in (project, logdir):
        if not os.path.isdir(d):
            os.makedirs(d)

    report = {"port": args.port, "exe": harness.EXE, "scratch": scratch,
              "probe_kind": "undeclared_argument_name (refused by the registry's "
                            "unknown-argument gate, before any handler runs)",
              "targets": TARGETS, "undeclared_argument": UNDECLARED,
              "tools": {}, "harness": {}}

    engine = None
    try:
        harness.ensure_project(project, "TASK144 Probe Editor", False)
        # The import is a temporary editor process of its own: it is given the
        # same private port so it never touches the default 9877 (the user's
        # editor port, which accept_m1's guard watches).
        iout = os.path.join(logdir, "import-editor.out.txt")
        ierr = os.path.join(logdir, "import-editor.err.txt")
        with io.open(iout, "wb") as o, io.open(ierr, "wb") as e:
            p = subprocess.Popen([harness.EXE, "--headless", "--path", project,
                                  "--import", "--mcp-port=%d" % args.port],
                                 stdout=o, stderr=e, cwd=harness.ENGINE)
            try:
                p.wait(timeout=300)
                report["harness"]["import"] = (p.returncode == 0)
            except subprocess.TimeoutExpired:
                p.kill()
                report["harness"]["import"] = False
        with io.open(iout, "r", encoding="utf-8", errors="replace") as h:
            report["harness"]["import_listen"] = [
                ln.strip() for ln in h if ln.startswith("[MCP] listening")]
        engine = harness.start_engine(
            ["--headless", "--verbose", "-e", "--path", project,
             "--mcp-port=%d" % args.port],
            logdir, "editor")
        report["harness"]["port_up"] = harness.wait_for_port(args.port, 180)
        if not report["harness"]["port_up"]:
            raise RuntimeError("editor endpoint never came up on %d" % args.port)
        mcp = harness.Mcp(args.port)
        report["harness"]["status"] = mcp.status_probe()[:400]

        status, text = mcp.request(json.dumps(
            {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}))
        try:
            parsed = json.loads(text)
        except ValueError:
            parsed = None
        names = []
        if isinstance(parsed, dict) and isinstance(parsed.get("result"), dict):
            names = [t.get("name") for t in parsed["result"].get("tools") or []]
        report["harness"]["tools_list_count"] = len(names)
        report["harness"]["both_targets_registered"] = all(t in names for t in TARGETS)

        for name in TARGETS:
            entry = {"request_arguments": {UNDECLARED: 1}}
            assert list(entry["request_arguments"]) == [UNDECLARED], "the probe must send "
            status, text, parsed = mcp.call(name, entry["request_arguments"])
            entry["http_status"] = status
            entry["response_excerpt"] = (text or "")[:500]
            if isinstance(parsed, dict) and isinstance(parsed.get("error"), dict):
                entry["error_code"] = parsed["error"].get("code")
                entry["error_message"] = parsed["error"].get("message")
                entry["error_data"] = parsed["error"].get("data")
                entry["response_kind"] = "jsonrpc_error"
            elif isinstance(parsed, dict) and parsed.get("result") is not None:
                entry["response_kind"] = "result"
            else:
                entry["response_kind"] = "unparsable"
            if entry["response_kind"] != "jsonrpc_error":
                raise AssertionError("%s answered %s: the registry gate did not refuse "
                                     "it - refusing to record this as evidence"
                                     % (name, entry["response_kind"]))
            entry["verdict"] = ("refused_-32602" if entry["error_code"] == -32602
                                else "other_error")
            report["tools"][name] = entry
    except Exception as exc:
        report["harness"]["fatal"] = "%s: %s" % (type(exc).__name__, exc)
    finally:
        harness.stop_engine(engine)

    with io.open(args.out, "w", encoding="utf-8", newline="\n") as h:
        h.write(json.dumps(report, ensure_ascii=False, indent=1) + "\n")
    print("wrote %s" % args.out)
    print("harness: %s" % json.dumps({k: v for k, v in report["harness"].items()
                                      if k != "status"}, ensure_ascii=False))
    for name in TARGETS:
        e = report["tools"].get(name) or {}
        print("%-32s %s code=%s message=%s"
              % (name, e.get("verdict"), e.get("error_code"), e.get("error_message")))
    return 0 if all((report["tools"].get(t) or {}).get("verdict") == "refused_-32602"
                    for t in TARGETS) else 1


if __name__ == "__main__":
    sys.exit(main())
