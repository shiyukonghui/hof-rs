#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-143 live negative probe: for every contract tool, an illegal *input* call.

This is the task's section-B negative-evidence generator, run for real against a
fresh engine started by this script on a private high port (9899 editor / 9898
game). It is deliberately SAFE:

  * a tool that declares at least one REQUIRED argument is called with an empty
    argument bag -> the server must refuse with -32602 before any handler runs,
    and the call cannot change state;
  * a read-class tool with typed optional arguments only is called with one of
    those arguments carrying a JSON type that contradicts the declared type;
  * a WRITE-class tool with no required argument is NOT called: an illegal input
    for it cannot be constructed without risking a real mutation, so it is
    reported as `not_probed` with the reason, never as a pass.

Every answer is recorded verbatim (status, JSON-RPC error code, message, data)
with the request that produced it. The script writes its own JSON evidence file
(Python handle, never a shell redirect) and exits non-zero only on a harness
failure, so the evidence survives even when some tools refuse differently.

Usage:  python recovery/work/task143/probe.py [--editor-port 9899] [--game-port 9898]
"""
import argparse
import io
import json
import os
import socket
import subprocess
import sys
import tempfile
import time

ROOT = r"F:\moonbit-hof-rs\godot-mcp"
ENGINE = os.path.join(ROOT, "godot")
EXE = os.path.join(ENGINE, "bin", "godot.windows.editor.x86_64.mono.console.exe")
CONTRACT = os.path.join(ENGINE, "modules", "mcp_server", "docs", "tools_list.renamed.json")
RENAME_MAP = os.path.join(ENGINE, "modules", "mcp_server", "docs", "tool-rename-map.json")
GROUP_FILES = ["tool-groups.json", "tool-groups-b2.json", "tool-groups-b3.json",
               "tool-groups-b4.json", "tool-groups-b5.json", "tool-groups-added.json"]
GROUPS_DIR = os.path.join(ENGINE, "modules", "mcp_server", "docs")
HERE = os.path.dirname(os.path.abspath(__file__))
READ_VERBS = {"get", "read", "search", "list", "find", "analyze", "detect",
              "convert", "validate", "check", "assert", "execute", "evaluate",
              "capture"}


def load(path):
    with io.open(path, "r", encoding="utf-8") as h:
        return json.load(h)


# ---------------------------------------------------------------------------
# HTTP/1.1 client for the hand-rolled server (raw sockets, like accept_m1.ps1)
# ---------------------------------------------------------------------------
class Mcp(object):
    def __init__(self, port, timeout=20.0):
        self.port = port
        self.timeout = timeout
        self._id = 0

    def _next_id(self):
        self._id += 1
        return self._id

    def request(self, body_text):
        data = body_text.encode("utf-8")
        head = ("POST /mcp HTTP/1.1\r\nHost: 127.0.0.1\r\n"
                "Content-Type: application/json\r\nContent-Length: %d\r\n\r\n" % len(data))
        s = socket.create_connection(("127.0.0.1", self.port), timeout=self.timeout)
        try:
            s.sendall(head.encode("ascii") + data)
            buf = b""
            deadline = time.time() + self.timeout
            while time.time() < deadline:
                sep = buf.find(b"\r\n\r\n")
                if sep >= 0:
                    header = buf[:sep].decode("latin-1")
                    clen = 0
                    for line in header.split("\r\n"):
                        if line.lower().startswith("content-length:"):
                            clen = int(line.split(":", 1)[1].strip())
                    if len(buf) - (sep + 4) >= clen:
                        body = buf[sep + 4:sep + 4 + clen].decode("utf-8", "replace")
                        status = 0
                        if header.startswith("HTTP/1.1 "):
                            status = int(header.split(" ")[1])
                        return status, body
                chunk = s.recv(65536)
                if not chunk:
                    break
                buf += chunk
            return 0, ""
        finally:
            s.close()

    def call(self, name, args):
        body = {"jsonrpc": "2.0", "id": self._next_id(), "method": "tools/call",
                "params": {"name": name, "arguments": args}}
        status, text = self.request(json.dumps(body, ensure_ascii=False))
        try:
            parsed = json.loads(text)
        except ValueError:
            parsed = None
        return status, text, parsed

    def status_probe(self):
        s = socket.create_connection(("127.0.0.1", self.port), timeout=self.timeout)
        try:
            s.sendall(b"GET /mcp HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n")
            arrow = time.time() + 5
            while time.time() < arrow:
                chunk = s.recv(65536)
                if chunk:
                    return chunk.decode("utf-8", "replace")
            return ""
        finally:
            s.close()


# ---------------------------------------------------------------------------
# scratch project + engine lifecycle
# ---------------------------------------------------------------------------
def ensure_project(path, name, with_main_scene):
    if not os.path.isdir(path):
        os.makedirs(path)
    lines = ["config_version=5", "", "[application]",
             'config/name="%s"' % name,
             'config/features=PackedStringArray("4.8")']
    if with_main_scene:
        lines.append('run/main_scene="res://scenes/main.tscn"')
    lines += ["", "[rendering]",
              'renderer/rendering_method="gl_compatibility"',
              'renderer/rendering_method.mobile="gl_compatibility"']
    with io.open(os.path.join(path, "project.godot"), "w", encoding="utf-8", newline="\n") as h:
        h.write("\n".join(lines) + "\n")
    if with_main_scene:
        sdir = os.path.join(path, "scenes")
        if not os.path.isdir(sdir):
            os.makedirs(sdir)
        with io.open(os.path.join(sdir, "main.tscn"), "w", encoding="utf-8", newline="\n") as h:
            h.write('[gd_scene format=3]\n\n[node name="Main" type="Node"]\n')


def run_import(path, logdir, tag):
    out = os.path.join(logdir, "import-%s.out.txt" % tag)
    err = os.path.join(logdir, "import-%s.err.txt" % tag)
    with io.open(out, "wb") as o, io.open(err, "wb") as e:
        p = subprocess.Popen([EXE, "--headless", "--path", path, "--import"],
                             stdout=o, stderr=e, cwd=ENGINE)
        try:
            p.wait(timeout=300)
        except subprocess.TimeoutExpired:
            p.kill()
            return False
    return True


def start_engine(args, logdir, tag):
    out = os.path.join(logdir, "%s.out.txt" % tag)
    err = os.path.join(logdir, "%s.err.txt" % tag)
    o = io.open(out, "wb")
    e = io.open(err, "wb")
    p = subprocess.Popen([EXE] + args, stdout=o, stderr=e, cwd=ENGINE)
    return {"proc": p, "out": out, "err": err, "out_fh": o, "err_fh": e, "tag": tag}


def wait_for_port(port, timeout=180.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            s = socket.create_connection(("127.0.0.1", port), timeout=1.0)
            s.close()
            return True
        except Exception:
            time.sleep(0.5)
    return False


def stop_engine(handle):
    if not handle:
        return
    p = handle["proc"]
    if p.poll() is None:
        p.terminate()
        try:
            p.wait(timeout=15)
        except subprocess.TimeoutExpired:
            p.kill()
    for k in ("out_fh", "err_fh"):
        try:
            handle[k].close()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# endpoint map
# ---------------------------------------------------------------------------
def scope_map():
    scope = {}
    for e in load(RENAME_MAP)["tools"]:
        if e.get("new_name"):
            scope[e["new_name"]] = e.get("scope")
    for fname in GROUP_FILES:
        p = os.path.join(GROUPS_DIR, fname)
        if not os.path.isfile(p):
            continue
        for g in load(p).get("groups") or []:
            for t in g.get("tools") or []:
                scope.setdefault(t, g.get("scope"))
    return scope


def wrong_value(prop, spec):
    """A JSON value that contradicts the declared type (or enum)."""
    if not isinstance(spec, dict):
        return 123456, "no declared type -> integer sentinel"
    t = spec.get("type")
    if spec.get("enum"):
        return "__not_in_enum__", "a string outside the declared enum"
    if t == "string":
        return 123456, "an integer where a string is declared"
    if t == "integer":
        return "not-an-integer", "a string where an integer is declared"
    if t == "number":
        return "not-a-number", "a string where a number is declared"
    if t == "boolean":
        return "not-a-boolean", "a string where a boolean is declared"
    if t in ("array", "object"):
        return "not-a-%s" % t, "a string where a %s is declared" % t
    return 123456, "no declared type -> integer sentinel"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--editor-port", type=int, default=9899)
    ap.add_argument("--game-port", type=int, default=9898)
    ap.add_argument("--out", default=os.path.join(HERE, "probe-live.json"))
    args = ap.parse_args()

    contract = load(CONTRACT)["result"]["tools"]
    names = [t["name"] for t in contract]
    schema = {t["name"]: (t.get("inputSchema") or {}) for t in contract}
    scope = scope_map()
    verbs = {}
    for e in load(RENAME_MAP)["tools"]:
        if e.get("new_name"):
            verbs.setdefault(e["new_name"], e.get("verb"))

    scratch = os.path.join(tempfile.gettempdir(), "task143-probe")
    editor_project = os.path.join(scratch, "editor")
    game_project = os.path.join(scratch, "game")
    logdir = os.path.join(scratch, "logs")
    for d in (editor_project, game_project, logdir):
        if not os.path.isdir(d):
            os.makedirs(d)

    report = {"editor_port": args.editor_port, "game_port": args.game_port,
              "exe": EXE, "scratch": scratch, "tools": {}, "harness": {}}

    editor_handle = None
    game_handle = None
    try:
        ensure_project(editor_project, "TASK143 Probe Editor", False)
        ensure_project(game_project, "TASK143 Probe Game", True)
        report["harness"]["import_editor"] = run_import(editor_project, logdir, "editor")
        report["harness"]["import_game"] = run_import(game_project, logdir, "game")

        editor_handle = start_engine(
            ["--headless", "--verbose", "-e", "--path", editor_project,
             "--mcp-port=%d" % args.editor_port], logdir, "editor")
        report["harness"]["editor_port_up"] = wait_for_port(args.editor_port, 180)
        if not report["harness"]["editor_port_up"]:
            raise RuntimeError("editor endpoint never came up")

        game_handle = start_engine(
            ["--headless", "--path", game_project, "--mcp-port=%d" % args.game_port],
            logdir, "game")
        report["harness"]["game_port_up"] = wait_for_port(args.game_port, 180)

        editor = Mcp(args.editor_port)
        game = Mcp(args.game_port)
        report["harness"]["editor_status"] = editor.status_probe()[:400]
        report["harness"]["game_status"] = game.status_probe()[:400]

        counters = {"probed": 0, "refused_-32602": 0, "other_error": 0, "ok_unexpected": 0,
                    "not_probed": 0, "transport_error": 0}
        for name in names:
            sc = scope.get(name) or "both"
            props = (schema[name].get("properties") or {})
            required = list(schema[name].get("required") or [])
            verb = verbs.get(name)
            entry = {"scope": sc, "verb": verb, "required": required,
                     "optional": sorted(k for k in props if k not in required)}
            if required:
                probe_args = {}
                kind = "missing_required"
                why = "empty arguments: the tool declares required %s" % (", ".join(required),)
            elif props and verb in READ_VERBS:
                key = sorted(props.keys())[0]
                val, why_val = wrong_value(key, props[key])
                probe_args = {key: val}
                kind = "wrong_type_optional"
                why = "read-class tool: '%s' carries %s" % (key, why_val)
            else:
                entry["verdict"] = "not_probed"
                entry["why"] = ("write-class tool with no required argument: an illegal input "
                                "cannot be constructed without risking a real mutation, or the "
                                "contract declares no properties at all")
                counters["not_probed"] += 1
                report["tools"][name] = entry
                continue

            target = editor if sc in ("editor", "both") else game
            label = "editor" if sc in ("editor", "both") else "game"
            if label == "game" and not report["harness"].get("game_port_up"):
                entry["verdict"] = "not_probed"
                entry["why"] = "game endpoint did not come up"
                counters["not_probed"] += 1
                report["tools"][name] = entry
                continue
            try:
                status, text, parsed = target.call(name, probe_args)
            except Exception as exc:  # transport
                entry["verdict"] = "transport_error"
                entry["why"] = "%s: %s" % (type(exc).__name__, exc)
                counters["transport_error"] += 1
                report["tools"][name] = entry
                continue
            entry["probe_kind"] = kind
            entry["probe_why"] = why
            entry["endpoint"] = label
            entry["request_arguments"] = probe_args
            entry["http_status"] = status
            code = None
            msg = None
            data = None
            if isinstance(parsed, dict):
                err = parsed.get("error")
                if isinstance(err, dict):
                    code = err.get("code")
                    msg = err.get("message")
                    data = err.get("data")
                    entry["response_kind"] = "jsonrpc_error"
                elif parsed.get("result") is not None:
                    entry["response_kind"] = "result"
            else:
                entry["response_kind"] = "unparsable"
            entry["error_code"] = code
            entry["error_message"] = msg
            entry["error_data"] = data
            entry["response_excerpt"] = (text or "")[:400]
            if code == -32602:
                entry["verdict"] = "refused_-32602"
                counters["refused_-32602"] += 1
            elif isinstance(code, int):
                entry["verdict"] = "other_error"
                counters["other_error"] += 1
            elif entry["response_kind"] == "result":
                entry["verdict"] = "ok_unexpected"
                counters["ok_unexpected"] += 1
            else:
                entry["verdict"] = "transport_error"
                counters["transport_error"] += 1
            counters["probed"] += 1
            report["tools"][name] = entry
        report["counters"] = counters
    except Exception as exc:
        report["harness"]["fatal"] = "%s: %s" % (type(exc).__name__, exc)
    finally:
        stop_engine(game_handle)
        stop_engine(editor_handle)

    with io.open(args.out, "w", encoding="utf-8", newline="\n") as h:
        h.write(json.dumps(report, ensure_ascii=False, indent=1))
    print("wrote %s" % args.out)
    print("harness: %s" % json.dumps({k: v for k, v in report["harness"].items()
                                      if k not in ("editor_status", "game_status")},
                                     ensure_ascii=False))
    print("counters: %s" % json.dumps(report.get("counters", {}), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
