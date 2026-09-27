#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-118 sections C+D: update the unreachable register.

* H7 `still_out` (the five `editor_simulate_*`) is restated as a SCOPE EXCLUSION
  (D59 / GDR-21), with the source lines the scope decision rests on and the
  condition under which it becomes measurable - and it is kept in its own bucket
  so the register can print `scope-excluded` and `unreachable` as separate counts.
* H8 `external_device` (the three Android tools) gets the TASK-118 measurement
  instead of an assumption: adb IS installed (off-PATH), `adb devices -l` is
  empty, no project in this repository has an Android preset, and the c7 run
  called all three (os_list_android_devices reached 达标 with a real empty device
  list; the other two only have their refusal branch).
* the three are added to `reclassified` (add-only, idempotent) so the ledger's
  drift view stops reporting them as un-reviewed drift.

Run it twice: the second run must print `added 0` for everything.
"""
import io
import json
import os

ROOT = r"F:\moonbit-hof-rs\godot-mcp"
PATH = os.path.join(ROOT, "tools", "tool_coverage_unreachable.json")
RUN = "runs/_exercises/ex_grid/c7-task118"

STILL_OUT = {
    "tools": ["editor_simulate_key", "editor_simulate_mouse_click", "editor_simulate_mouse_move",
              "editor_simulate_input_action", "editor_simulate_input_sequence"],
    "bucket": "scope-excluded",
    "why": "Not `unreachable`: these five are compiled into this build and registered on the editor "
           "endpoint, and in a real editor the thing they need always exists (`Input` is created by "
           "`Main::setup2` in every engine process). What they cannot do is drive the GAME: they inject "
           "into the EDITOR process' own input queue via `Input::get_singleton()->parse_input_event()`, "
           "and D59 / GDR-21 put driving the editor's own input outside this loop's scope on purpose - "
           "the loop drives the game through the game endpoint's `running_game_*` input tools instead.",
    "source_lines": "godot/modules/mcp_server/tools/editor_input_simulation.cpp:53-112 (the file head "
                    "comment states the injection target and the scope rule) and :121-144 (the "
                    "preconditions the tool checks before it injects)",
    "evidence": "TASK-115 measured the family and TASK-118 keeps it out deliberately: 0 calls in the whole "
                "corpus (mode=all-runs, 111 runs / 180 traces / 8712 tools/call). The five are the only "
                "0-call tools left after TASK-118.",
    "measurable_when": "when a batch exists whose subject is the EDITOR's own input observation: an "
                       "Editorial-side plugin (or `editor_execute_gdscript` counting `Input` events) after "
                       "an `editor_simulate_*` injection, with the batch stating that the game endpoint must "
                       "see nothing. Under the current ledger rules such a batch buys counts and boundaries, "
                       "not a tier.",
}

EXTERNAL_DEVICE = {
    "tools": ["os_list_android_devices", "os_deploy_to_android_device", "project_get_android_preset_info"],
    "bucket": "needs-an-external-device",
    "why": "Not `unreachable`: the code path exists and is compiled. TASK-118 replaced TASK-114/115's "
           "assumption with a measurement and found the machine is one step further along than assumed - "
           "the Android SDK IS installed, just not where the engine looks by default and not on PATH - and "
           "what is really missing is a DEVICE and an ANDROID EXPORT PRESET.",
    "measured_on_this_machine": {
        "adb_exe": "C:\\Program Files (x86)\\Android\\android-sdk\\platform-tools\\adb.exe",
        "adb_version": "Android Debug Bridge version 1.0.41 / Version 36.0.0-13206524 (measured: "
                       "`adb.exe version`, exit 0)",
        "adb_on_path": "NO - `where adb` exits 1; ANDROID_HOME / ANDROID_SDK_ROOT are unset; the only "
                       "Android-flavoured environment variable is JAVA_HOME=C:\\Program Files (x86)\\Android"
                       "\\openjdk\\jdk-17.0.12",
        "devices": "`adb devices -l` answers `List of devices attached` with an EMPTY list (the adb daemon "
                   "was started by that command; no device and no emulator is present)",
        "presets": "no project under projects/** has a platform=\"Android\" preset: every export_presets.cfg "
                   "in the repository carries Windows Desktop (and ex_export a Web) preset only",
        "export_templates": "%APPDATA%\\Godot\\export_templates holds the 4.8.dev Windows templates only "
                            "(TASK-115 measured this); no Android template is installed",
    },
    "run_evidence": {
        "run": RUN,
        "os_list_android_devices": "5 ok calls + 1 boundary; the answer is "
                                   "{\"adb_path\":\"adb\",\"adb_present\":false,\"count\":0,\"devices\":[],"
                                   "\"message\":\"adb ran and reported no connected device ...\"} - the tool "
                                   "really ran adb (this run prepended the SDK platform-tools to ITS OWN "
                                   "process PATH; nothing machine-wide was changed) and really reported an "
                                   "empty device list. Status: 达标 on the declared `payload` channel.",
        "project_get_android_preset_info": "5 calls, every one refused with -32000 'Add an Android preset in "
                                           "the editor (Project > Export > Add... > Android); this project has "
                                           "1 preset', plus a -32001 boundary for a preset name that does not "
                                           "exist. No ok payload exists on this machine.",
        "os_deploy_to_android_device": "5 calls refused with -32001 (the named preset does not exist; "
                                       "skip_export=true kept the export child process out of it) plus a "
                                       "-32602 boundary from the parameter rule. The deploy path itself was "
                                       "never reached: it needs an Android preset AND a device.",
    },
    "measurable_when": "an Android platform preset is added to an exercise project (Project > Export > "
                       "Add... > Android) AND a device or emulator is attached and authorised. Then "
                       "`os_list_android_devices` shows the serial, `project_get_android_preset_info` "
                       "answers a preset record, and `os_deploy_to_android_device` can walk export -> adb "
                       "install -> launch. Until then os_deploy_to_android_device and "
                       "project_get_android_preset_info keep their refusal branch only, and are reported as "
                       "`计数达标缺证据` on their declared `payload` channel - not as unreachable.",
}

RECLASSIFIED = [
    {
        "tool": "os_list_android_devices",
        "from": "H8",
        "why": "TASK-118 measured it instead of assuming: the Android SDK is installed off-PATH, the run "
               "started adb and the tool answered a real empty device list (count=0, devices=[]), which is "
               "an ok substantive payload on its declared `payload` channel. 5 ok calls + 1 boundary -> 达标.",
        "evidence": RUN,
        "batch": "c7",
        "task": "TASK-118",
        "register_note": "the H8 entry said the loop's endpoint is the desktop editor and this tool needs "
                         "`adb` plus a connected device; the first half is wrong on this machine (adb is "
                         "present) and the second half is what the empty list measures.",
    },
    {
        "tool": "project_get_android_preset_info",
        "from": "H8",
        "why": "TASK-118 called it 6 times: every call is refused because no project in this repository has "
               "an Android preset. That is a measured boundary, not an unreachable claim, so it moves out of "
               "the register's unreachable set and into `categories.H8.external_device`.",
        "evidence": RUN,
        "batch": "c7",
        "task": "TASK-118",
        "register_note": "still needs an Android preset to reach its ok branch.",
    },
    {
        "tool": "os_deploy_to_android_device",
        "from": "H8",
        "why": "TASK-118 called it 6 times with skip_export=true: every call is refused before the export "
               "child process starts (no such preset, then the parameter rule). Measured boundary only; the "
               "deploy path needs an Android preset and a device.",
        "evidence": RUN,
        "batch": "c7",
        "task": "TASK-118",
        "register_note": "the run deliberately never reached the export/install/launch phases; a device is "
                         "required for that.",
    },
]


def load():
    with io.open(PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def save(doc):
    with io.open(PATH, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(doc, ensure_ascii=False, indent=1))
        fh.write("\n")


def main():
    doc = load()
    h7 = doc["categories"]["H7"]
    added = []
    if h7.get("still_out", {}).get("bucket") != "scope-excluded":
        h7["still_out"] = dict(STILL_OUT)
        added.append("H7.still_out")
    if h7.get("still_out") != STILL_OUT:
        h7["still_out"] = dict(STILL_OUT)
        added.append("H7.still_out(refreshed)")
    h8 = doc["categories"]["H8"]
    if h8.get("external_device") != EXTERNAL_DEVICE:
        h8["external_device"] = dict(EXTERNAL_DEVICE)
        added.append("H8.external_device(refreshed)")
    if h8.get("external_device", {}).get("bucket") != "needs-an-external-device":
        added.append("H8.external_device.bucket")

    # scope-excluded vs unreachable must be countable separately.
    doc["scope_excluded"] = {
        "comment": "TASK-118 section C: tools excluded by SCOPE (D59 / GDR-21), reported separately from "
                   "`unreachable` so the two can never be added together by accident.",
        "tools": STILL_OUT["tools"],
        "count": len(STILL_OUT["tools"]),
        "register_category": "H7",
    }
    doc["needs_an_external_device"] = {
        "comment": "TASK-118 section D: tools whose code path exists but whose subject is outside this "
                   "machine (a device, an Android preset). Measured, not inferred.",
        "tools": EXTERNAL_DEVICE["tools"],
        "count": len(EXTERNAL_DEVICE["tools"]),
        "register_category": "H8",
        "measured_run": RUN,
    }

    existing = {r["tool"]: i for i, r in enumerate(doc.get("reclassified") or [])}
    for item in RECLASSIFIED:
        if item["tool"] in existing:
            idx = existing[item["tool"]]
            if doc["reclassified"][idx] != item:
                doc["reclassified"][idx] = dict(item)
                added.append("reclassified:%s(refreshed)" % item["tool"])
            continue
        doc.setdefault("reclassified", []).append(dict(item))
        existing[item["tool"]] = len(doc["reclassified"]) - 1
        added.append("reclassified:%s" % item["tool"])
    doc["reclassified_count"] = len(doc.get("reclassified") or [])
    doc["_task118_note"] = (
        "TASK-118: `scope-excluded` (5 editor_simulate_*, D59/GDR-21) and `needs-an-external-device` "
        "(3 Android tools, measured) are separate top-level buckets; the five simulate tools are NOT "
        "unreachable and the three Android tools are NOT unreachable either. Members: %d, reclassified: %d."
        % (len(doc.get("members") or []), doc["reclassified_count"]))
    save(doc)
    print("added/refreshed: %s" % added)
    print("members=%d reclassified=%d scope_excluded=%d external_device=%d"
          % (len(doc.get("members") or []), doc["reclassified_count"], doc["scope_excluded"]["count"],
             doc["needs_an_external_device"]["count"]))


if __name__ == "__main__":
    main()
