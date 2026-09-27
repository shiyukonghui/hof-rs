#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_coverage_session.py -- build the TASK-110 coverage exercise sessions.

The coverage ledger needs sessions whose *purpose* is coverage: every target tool
is called at least five times, at least one call is meant to be effective and at
least one is a boundary (a failing call where a failure is constructible, or a
documented edge input where it is not).

This generator is the single source of truth for those sessions: it writes
`tools/sessions/_exercises/<batch>/session.json` (the format
`tools/run_game_session.ps1` replays) plus a machine-readable manifest
`<batch>-manifest.json` next to it that records, per call, its tag, tool and
intent (`ok` / `probe` / `edge`). The manifest is what makes the batch
checkable - the trace alone cannot tell "this call was the boundary probe" from
"this call happened to be the fifth one".

Usage:
    python tools/gen_coverage_session.py --batch c1
    python tools/gen_coverage_session.py --batch c1 --print-summary
"""
import argparse
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

SCRIPT = "res://src/PongGame.cs"
BALL = "res://src/Ball.cs"
PADDLE = "res://src/Paddle.cs"
SCENE = "res://scenes/main.tscn"
MISSING = "res://src/NoSuchFile.cs"
SHADERS = ["res://shaders/ex1.gdshader", "res://shaders/ex2.gdshader",
           "res://shaders/ex3.gdshader", "res://shaders/ex4.gdshader",
           "res://shaders/ex5.gdshader"]
THEMES = ["res://themes/ex1.tres", "res://themes/ex2.tres", "res://themes/ex3.tres",
          "res://themes/ex4.tres", "res://themes/ex5.tres"]
RESOURCES = ["res://resources/ex1.tres", "res://resources/ex2.tres", "res://resources/ex3.tres",
             "res://resources/ex4.tres", "res://resources/ex5.tres"]
SCENES_NEW = ["res://scenes/ex_s1.tscn", "res://scenes/ex_s2.tscn", "res://scenes/ex_s3.tscn",
              "res://scenes/ex_s4.tscn", "res://scenes/ex_s5.tscn"]
SCRIPTS_NEW = ["res://src/ex_c1_1.cs", "res://src/ex_c1_2.cs", "res://src/ex_c1_3.cs",
               "res://src/ex_c1_4.cs", "res://src/ex_c1_5.cs"]
TEXTS_NEW = ["res://notes_ex1.cfg", "res://notes_ex2.cfg", "res://notes_ex3.cfg",
             "res://notes_ex4.cfg", "res://notes_ex5.cfg"]
AUTOLOADS = ["ExA1", "ExA2", "ExA3", "ExA4", "ExA5"]

SHADER_CODE = ("shader_type canvas_item;\n"
               "uniform float speed = 1.0;\n"
               "uniform vec4 tint : source_color = vec4(1.0, 0.5, 0.5, 1.0);\n"
               "void fragment() { COLOR = tint * 0.5; }\n")
CS_CLASS = ("using Godot;\n\n"
            "public partial class %s : Node\n"
            "{\n"
            "    public override void _Ready() { }\n"
            "}\n")


class Builder(object):
    def __init__(self, batch, project):
        self.batch = batch
        self.project = project
        self.calls = []
        self.manifest = []
        self.seq = 0

    def add(self, tool, port, args, intent, note=None, tag_hint=None):
        self.seq += 1
        kind = intent if tag_hint is None else tag_hint
        tag = "%s-%03d-%s-%s" % (self.batch, self.seq, tool, kind)
        call = {"tag": tag, "port": port, "tool": tool, "arguments": args}
        if note:
            call["note"] = note
        self.calls.append(call)
        self.manifest.append({"tag": tag, "tool": tool, "port": port, "intent": intent,
                              "note": note or ""})
        return tag

    def setup(self, tool, port, args, note=""):
        """A call that exists only to make the targets measurable (never a target).

        The tag still says `ok` (a setup call is an ordinary successful call, and
        its tag must stay stable across a re-generation); only the manifest's
        `intent` marks it, which is what keeps the verifier from judging it.
        """
        self.add(tool, port, args, "setup", note, tag_hint="ok")

    def tool(self, tool, oks, probe, port="editor", probe_intent="probe",
             ok_note="", probe_note=""):
        """Five effective-intended calls plus one boundary/probe call."""
        assert len(oks) >= 5, tool
        for i, args in enumerate(oks[:5], 1):
            self.add(tool, port, args, "ok", ("%s call %d/5. %s" % (tool, i, ok_note)).strip())
        self.add(tool, port, probe, probe_intent, ("%s boundary: %s" % (tool, probe_note)).strip())

    def sleep(self, port, ms, note):
        self.calls.append({"sleep_ms": ms, "port": port, "note": note})

    def doc(self, header):
        return {"_comment": header, "game": self.project.replace("/", "_"),
                "import": True, "calls": self.calls}


# ---------------------------------------------------------------------------
# c1 -- the 40 project_* tools that the 20-game loop never called.
# ---------------------------------------------------------------------------
def build_c1():
    b = Builder("c1", "_exercises/ex_files")

    # --- Phase A: create what the readers below need -----------------------
    b.tool("project_create_shader",
           [{"path": p, "shader_type": "shader_type canvas_item;"} for p in SHADERS],
           {"path": "res://scenes/main.tscn", "shader_type": "shader_type canvas_item;"},
           ok_note="new .gdshader", probe_note="a .tscn path is not a shader destination")

    b.tool("project_edit_shader",
           [{"path": p, "code": SHADER_CODE} for p in SHADERS],
           {"path": "res://shaders/absent.gdshader", "code": SHADER_CODE},
           ok_note="write code with two uniforms", probe_note="path does not exist")

    b.tool("project_create_theme",
           [{"path": p, "name": "ExTheme%d" % (i + 1)} for i, p in enumerate(THEMES)],
           {"path": THEMES[0], "name": "Dup"},
           ok_note="new Theme resource", probe_note="the theme already exists")

    b.tool("project_create_resource",
           [{"path": RESOURCES[0], "type": "Gradient"},
            {"path": RESOURCES[1], "type": "Curve"},
            {"path": RESOURCES[2], "type": "Gradient"},
            {"path": RESOURCES[3], "type": "Curve"},
            {"path": RESOURCES[4], "type": "Resource"}],
           {"path": "res://resources/ex_bad.tres", "type": "NoSuchResourceType"},
           ok_note="new .tres", probe_note="unknown resource type")

    b.tool("project_create_scene_file",
           [{"path": p, "root_type": "Node2D", "root_name": "ExRoot%d" % (i + 1)}
            for i, p in enumerate(SCENES_NEW)],
           {"path": "res://scenes/main.tscn"},
           ok_note="new .tscn", probe_note="the scene already exists")

    b.tool("project_create_script",
           [{"path": p, "content": CS_CLASS % ("ExC1%d" % (i + 1))}
            for i, p in enumerate(SCRIPTS_NEW)],
           {"path": SCRIPT, "content": CS_CLASS % "PongGame"},
           ok_note="new C# script", probe_note="the script already exists (no overwrite)")

    b.tool("project_write_text_file",
           [{"path": TEXTS_NEW[0], "content": "hello ex1\n", "overwrite": True},
            {"path": TEXTS_NEW[1], "content": "hello ex2\n"},
            {"path": TEXTS_NEW[2], "content": "hello ex3\n"},
            {"path": TEXTS_NEW[3], "content": "hello ex4\n", "overwrite": True},
            {"path": TEXTS_NEW[4], "content": "hello ex5\n"}],
           {"path": SCENE, "content": "not a scene"},
           ok_note="plain text file", probe_note="a .tscn destination is refused (use the scene tools)")

    # --- Phase B: the readers and analysers --------------------------------
    b.tool("project_get_info", [{}, {}, {}, {}, {}], {"bogus_argument": 1},
           probe_note="out-of-contract argument accepted or rejected? both are recorded")

    b.tool("project_get_settings",
           [{}, {"prefix": "application"}, {"prefix": "display"}, {"prefix": "dotnet"},
            {"include_default": True}],
           {"prefix": 12345},
           probe_note="prefix is typed string, not int")

    b.tool("project_get_statistics",
           [{}, {"path": "res://src"}, {"path": "res://scenes"}, {"include_addons": True},
            {"path": "res://"}],
           {"path": "res://no_such_dir"},
           probe_note="path does not exist")

    b.tool("project_get_filesystem_tree",
           [{}, {"max_depth": 1}, {"max_depth": 2}, {"path": "res://src"}, {"path": "res://scenes"}],
           {"path": "res://no_such_dir"},
           probe_note="path does not exist")

    b.tool("project_list_scripts", [{}, {}, {}, {}, {}], {"bogus_argument": 1},
           probe_note="out-of-contract argument accepted or rejected?")

    b.tool("project_find_unused_resources",
           [{}, {"path": "res://src"}, {"path": "res://scenes"}, {"include_addons": True},
            {"path": "res://"}],
           {"path": "res://no_such_dir"},
           probe_note="path does not exist")

    b.tool("project_detect_circular_dependencies",
           [{}, {"path": "res://scenes"}, {"path": "res://src"}, {"include_addons": True},
            {"path": "res://"}],
           {"path": "res://no_such_dir"},
           probe_note="path does not exist")

    b.tool("project_search_file_names",
           [{"pattern": "*.cs"}, {"pattern": "main"}, {"pattern": "*.tscn"}, {"pattern": "Ball"},
            {"pattern": "*.uid"}],
           {"pattern": ""},
           probe_note="empty pattern (contract edge: matches everything or is refused)")

    b.tool("project_search_file_contents",
           [{"pattern": "class"}, {"pattern": "PongGame"}, {"pattern": "_Ready"},
            {"pattern": "velocity", "file_pattern": "*.cs"}, {"pattern": "extends"}],
           {"pattern": ""},
           probe_note="empty pattern (contract edge)")

    b.tool("project_find_files_referencing_symbol",
           [{"pattern": "res://src/Ball.cs"}, {"pattern": "PongGame"}, {"pattern": "Ball"},
            {"pattern": "uid://"}, {"pattern": "Main"}],
           {"pattern": ""},
           probe_note="empty pattern (contract edge)")

    b.tool("project_find_script_references",
           [{"query": "res://src/Ball.cs"}, {"query": "PongGame"}, {"query": "Paddle"},
            {"query": "Ball", "include_addons": True}, {"query": "res://src/Paddle.cs"}],
           {"query": "res://src/NoSuch.cs"},
           probe_note="script path does not exist")

    b.tool("project_read_script",
           [{"path": SCRIPT}, {"path": BALL}, {"path": PADDLE}, {"path": SCRIPT}, {"path": BALL}],
           {"path": MISSING},
           probe_note="path does not exist")

    b.tool("project_read_text_file",
           [{"path": SCRIPT}, {"path": "res://pong.csproj"}, {"path": "res://NuGet.config"},
            {"path": "res://README.md"}, {"path": "res://export_presets.cfg"}],
           {"path": MISSING},
           probe_note="path does not exist")

    b.tool("project_read_shader", [{"path": p} for p in SHADERS],
           {"path": "res://shaders/absent.gdshader"},
           probe_note="shader does not exist")

    b.tool("project_get_shader_params", [{"path": p} for p in SHADERS],
           {"path": "res://shaders/absent.gdshader"},
           probe_note="shader does not exist")

    b.tool("project_read_scene_file_content",
           [{"path": SCENE}] + [{"path": p} for p in SCENES_NEW[:4]],
           {"path": "res://scenes/absent.tscn"},
           probe_note="scene does not exist")

    b.tool("project_get_scene_dependencies",
           [{"path": SCENE}] + [{"path": p} for p in SCENES_NEW[:4]],
           {"path": "res://scenes/absent.tscn"},
           probe_note="scene does not exist")

    b.tool("project_get_scene_exports",
           [{"path": SCENE}] + [{"path": p} for p in SCENES_NEW[:4]],
           {"path": "res://scenes/absent.tscn"},
           probe_note="scene does not exist")

    b.tool("project_analyze_scene_complexity",
           [{}, {"path": SCENE}, {"path": SCENES_NEW[0]}, {"path": SCENES_NEW[1]},
            {"path": SCENES_NEW[2]}],
           {"path": "res://scenes/absent.tscn"},
           probe_note="scene does not exist")

    b.tool("project_read_resource", [{"path": p} for p in RESOURCES],
           {"path": "res://resources/absent.tres"},
           probe_note="resource does not exist")

    b.tool("project_get_theme_info", [{"theme_path": p} for p in THEMES],
           {"theme_path": "res://themes/absent.tres"},
           probe_note="theme does not exist")

    b.tool("project_get_resource_preview",
           [{"path": SCENE}, {"path": THEMES[0]}, {"path": THEMES[1]}, {"path": RESOURCES[0]},
            {"path": RESOURCES[1]}],
           {"path": "res://resources/absent.tres"},
           probe_note="resource does not exist")

    b.tool("project_convert_path_to_uid",
           [{"path": SCENE}, {"path": SCRIPT}, {"path": BALL}, {"path": PADDLE},
            {"path": "res://pong.csproj"}],
           {"path": "res://no/such/file.cs"},
           probe_intent="edge",
           probe_note="documented edge: an unregistered path answers uid=\"\" and does NOT error")

    b.tool("project_convert_uid_to_path",
           [{"uid": "uid://dkqi2elfc51wh"}, {"uid": "uid://bo6p3rkt7rbe7"},
            {"uid": "uid://dhfj67vumndol"}, {"uid": "uid://c3c3aa5aswx3x"},
            {"uid": "uid://dkqi2elfc51wh"}],
           {"uid": "not-a-uid"},
           probe_note="the uid text is malformed (contract says parameter error)")

    b.tool("project_validate_script",
           [{"path": SCRIPT}, {"path": BALL}, {"path": PADDLE}, {"path": SCRIPTS_NEW[0]},
            {"path": SCRIPTS_NEW[1]}],
           {"path": MISSING},
           probe_note="path does not exist")

    # --- Phase C: the writers over what phase A created --------------------
    b.tool("project_set_theme_color",
           [{"theme_path": THEMES[i], "node_type": "Button", "color_name": "font_color",
             "color": {"r": 0.1 * i, "g": 0.2, "b": 0.3, "a": 1.0}} for i in range(5)],
           {"theme_path": "res://themes/absent.tres", "node_type": "Button",
            "color_name": "font_color", "color": {"r": 1, "g": 0, "b": 0, "a": 1}},
           probe_note="theme does not exist")

    b.tool("project_set_theme_constant",
           [{"theme_path": THEMES[i], "node_type": "Button", "constant_name": "h_separation",
             "value": i} for i in range(5)],
           {"theme_path": "res://themes/absent.tres", "node_type": "Button",
            "constant_name": "h_separation", "value": 1},
           probe_note="theme does not exist")

    b.tool("project_set_theme_font_size",
           [{"theme_path": THEMES[i], "node_type": "Button", "font_size_name": "font_size",
             "size": 12 + i} for i in range(5)],
           {"theme_path": "res://themes/absent.tres", "node_type": "Button",
            "font_size_name": "font_size", "size": 12},
           probe_note="theme does not exist")

    b.tool("project_set_theme_stylebox",
           [{"theme_path": THEMES[i], "node_type": "Panel", "stylebox_name": "panel",
             "bg_color": "#%02x2233" % (0x10 * i), "border_width": 1 + i,
             "corner_radius": i} for i in range(5)],
           {"theme_path": "res://themes/absent.tres", "node_type": "Panel",
            "stylebox_name": "panel", "bg_color": "#112233"},
           probe_note="theme does not exist")

    b.tool("project_edit_resource",
           [{"path": RESOURCES[i], "properties": {"resource_name": "ExRes%d" % (i + 1)}}
            for i in range(5)],
           {"path": "res://resources/absent.tres", "properties": {"resource_name": "x"}},
           probe_note="resource does not exist")

    b.tool("project_set_setting",
           [{"key": "application/config/description", "value": "ex_files exercise project %d" % i}
            for i in range(5)],
           {"key": "", "value": 1},
           probe_note="empty setting key")

    b.tool("project_add_autoload",
           [{"name": AUTOLOADS[i], "path": SCRIPTS_NEW[i]} for i in range(5)],
           {"name": "ExBad", "path": MISSING},
           probe_note="script path does not exist")

    b.tool("project_remove_autoload",
           [{"name": n} for n in AUTOLOADS],
           {"name": "NoSuchAutoload"},
           probe_note="autoload is not registered")

    b.tool("project_set_node_property_across_scenes",
           [{"type": "ColorRect", "property": "color",
             "value": {"r": 0.05 * i, "g": 0.1, "b": 0.2, "a": 1.0},
             "dry_run": True, "path_filter": "res://scenes"} for i in range(4)]
           + [{"type": "ColorRect", "property": "color", "value": {"r": 0.0, "g": 0.1, "b": 0.2, "a": 1.0},
               "dry_run": False, "path_filter": "res://scenes", "force": False}],
           {"type": "ColorRect", "property": "no_such_property", "value": 1,
            "path_filter": "res://scenes"},
           probe_note="property does not exist on the type")

    # --- Phase D: delete what phase B no longer needs ----------------------
    b.tool("project_delete_scene_file", [{"path": p} for p in SCENES_NEW],
           {"path": "res://scenes/absent.tscn"},
           probe_note="scene does not exist")

    header = ("TASK-110 batch c1 -- the 40 project_* contract tools that the 20-game loop never "
              "called. Every tool gets 5 effective-intended calls plus 1 boundary/probe call. "
              "Editor endpoint only: project_* is scope=both and the editor endpoint is the one "
              "the loop uses for project work.")
    return b.doc(header), b.manifest


# ---------------------------------------------------------------------------
# c1b -- the repair batch for c1's eight gate failures.
#
# c1 left eight tools short of the gate, each for a *root-caused* reason that the
# session itself can fix (they are not tool defects):
#   * project_validate_script  - the copied project had no built assembly, so the
#     tool correctly refused ("not compiled is not does not compile"): build first.
#   * project_get_resource_preview - every asset in the project is a scene/theme/
#     gradient/curve, and the tool only previews image-capable resources: seed PNGs.
#   * project_search_file_names / _contents / project_find_script_references /
#     project_set_node_property_across_scenes - the probe used an input the tool
#     tolerates (an empty pattern; a query that merely matches nothing), so no
#     failure was produced: probe the *directory* argument instead.
#   * project_find_files_referencing_symbol - has no path argument at all, so probe
#     the declared type of `pattern`.
#   * project_set_node_property_across_scenes - the created scenes hold only a
#     Node2D root, and the tool refuses (force=false) to touch the open scene, so
#     no scene matched a ColorRect write: write a property Node2D really has.
#   * project_create_script (bonus tool) - its probe succeeded, so it has no
#     boundary evidence: probe a directory that does not exist.
# ---------------------------------------------------------------------------
def build_c1b():
    b = Builder("c1b", "_exercises/ex_files")

    b.add("project_build_csharp", "editor",
          {"configuration": "Debug", "timeout_ms": 300000, "rescan": True}, "setup",
          "c1b precondition: project_validate_script needs a loaded assembly",
          tag_hint="ok")

    b.tool("project_validate_script",
           [{"path": SCRIPT}, {"path": BALL}, {"path": PADDLE}, {"path": SCRIPTS_NEW[0]},
            {"path": SCRIPTS_NEW[1]}],
           {"path": MISSING},
           ok_note="now that the assembly is loaded these get a real verdict",
           probe_note="path does not exist")

    b.tool("project_get_resource_preview",
           [{"path": "res://assets/seed%d.png" % (i + 1)} for i in range(5)],
           {"path": "res://assets/absent.png"},
           ok_note="a texture is the resource class this tool can preview",
           probe_note="asset does not exist")

    b.tool("project_search_file_names",
           [{"path": "res://src", "pattern": "Ball"}, {"path": "res://scenes", "pattern": "main"},
            {"pattern": "notes"}, {"path": "res://src", "pattern": ".cs"},
            {"path": "res://assets", "pattern": ".png"}],
           {"path": "res://no_such_dir", "pattern": "x"},
           ok_note="filename substring search (globs like *.cs match nothing by contract)",
           probe_note="search path does not exist")

    b.tool("project_search_file_contents",
           [{"pattern": "class", "path": "res://src"}, {"pattern": "ColorRect", "path": "res://scenes"},
            {"pattern": "PongGame", "path": "res://src"},
            {"pattern": "text", "path": "res://scenes", "file_pattern": "*.tscn"},
            {"pattern": "shader_type", "path": "res://shaders"}],
           {"pattern": "class", "path": "res://no_such_dir"},
           ok_note="path-scoped content search", probe_note="search path does not exist")

    b.tool("project_find_files_referencing_symbol",
           [{"pattern": "PongGame"}, {"pattern": "res://src/Ball.cs"}, {"pattern": "Ball"},
            {"pattern": "uid://"}, {"pattern": "Main"}],
           {"pattern": 123},
           ok_note="the tool has no path argument, so its only boundary is a typed one",
           probe_note="pattern is typed string, not int")

    b.tool("project_find_script_references",
           [{"query": "Ball", "path": "res://src"}, {"query": "PongGame", "path": "res://src"},
            {"query": "res://src/Paddle.cs", "path": "res://scenes"}, {"query": "Ball"},
            {"query": "Paddle", "path": "res://src"}],
           {"query": "Ball", "path": "res://no_such_dir"},
           ok_note="path-scoped reference search", probe_note="search path does not exist")

    b.tool("project_set_node_property_across_scenes",
           [{"type": "Node2D", "property": "visible", "value": True, "dry_run": True,
             "path_filter": "res://scenes"},
            {"type": "Node2D", "property": "visible", "value": True, "dry_run": True,
             "path_filter": "res://scenes"},
            {"type": "Node2D", "property": "visible", "value": True, "dry_run": True,
             "path_filter": "res://scenes"},
            {"type": "Node2D", "property": "visible", "value": True, "dry_run": True,
             "path_filter": "res://scenes"},
            {"type": "Node2D", "property": "visible", "value": True, "dry_run": False,
             "path_filter": "res://scenes"}],
           {"type": "Node2D", "property": "visible", "value": True,
            "path_filter": "res://no_such_dir"},
           ok_note="the created scenes hold a Node2D root, which has `visible`",
           probe_note="path filter does not match a real directory")

    b.tool("project_create_script",
           [{"path": p, "content": CS_CLASS % ("ExC1b%d" % (i + 1))}
            for i, p in enumerate(["res://src/ex_c1b_1.cs", "res://src/ex_c1b_2.cs",
                                   "res://src/ex_c1b_3.cs", "res://src/ex_c1b_4.cs",
                                   "res://src/ex_c1b_5.cs"])],
           {"path": "res://no_such_dir/x.cs", "content": CS_CLASS % "ExBad"},
           ok_note="new C# script", probe_note="destination directory does not exist")

    header = ("TASK-110 batch c1b -- closes c1's eight gate failures. Same project, same target "
              "list; each failure's root cause is named in this file's header and fixed in the "
              "session rather than papered over in the ledger.")
    return b.doc(header), b.manifest


# ---------------------------------------------------------------------------
# c23 -- families (2) editor read/inspect and (3) running_game query.
#
# The setup phase is what makes the reads meaningful: a scene with a Timer and a
# Button (so signal readers have real connections), a StaticBody2D with a
# collision shape (so collision/physics readers have a subject), node groups, a
# C# autoload and a built assembly. The game phase then has something to query.
# ---------------------------------------------------------------------------
EX_AUTO_CS = ("using Godot;\n\n"
              "public partial class ExAuto : Node\n"
              "{\n"
              "    public int Ticks { get; private set; }\n"
              "    public override void _Ready() { Ticks = 0; }\n"
              "}\n")
EX_BUTTON_CS = ("using Godot;\n\n"
                "public partial class ExButton : Button\n"
                "{\n"
                "    public override void _Ready() { Pressed += OnPressed; }\n\n"
                "    private void OnPressed()\n"
                "    {\n"
                "        var bg = GetNodeOrNull<ColorRect>(\"../Background\");\n"
                "        if (bg != null) { bg.Color = new Color(1.0f, 0.0f, 0.0f, 1.0f); }\n"
                "    }\n"
                "}\n")


def build_c23():
    b = Builder("c23", "_exercises/ex_scene")

    # --- setup: editor side ------------------------------------------------
    b.setup("editor_open_scene", "editor", {"path": SCENE}, "the scene every reader addresses")
    b.setup("project_create_script", "editor", {"path": "res://src/ExAuto.cs", "content": EX_AUTO_CS},
            "autoload subject for running_game_get_autoload_node")
    b.setup("project_create_script", "editor", {"path": "res://src/ExButton.cs", "content": EX_BUTTON_CS},
            "the button whose click must change pixels")
    b.setup("editor_add_nodes_batch", "editor", {"nodes": [
        {"type": "Timer", "name": "Tick", "parent_path": ".",
         "properties": {"wait_time": 0.25, "autostart": True}},
        {"type": "Button", "name": "ClickMe", "parent_path": ".",
         "properties": {"text": "ClickMe", "offset_left": 320.0, "offset_top": 520.0,
                        "offset_right": 480.0, "offset_bottom": 560.0}},
        {"type": "StaticBody2D", "name": "Body", "parent_path": "."},
        {"type": "Label", "name": "Hint", "parent_path": ".",
         "properties": {"text": "hint", "offset_left": 20.0, "offset_top": 560.0,
                        "offset_right": 300.0, "offset_bottom": 590.0}}]},
        "signal source, UI subject, physics subject")
    b.setup("editor_setup_collision_shape", "editor",
            {"node_path": "Body", "shape_type": "RectangleShape2D",
             "shape_params": {"size": {"x": 64, "y": 64}}}, "collision subject")
    b.setup("editor_set_node_script_batch", "editor",
            {"node_paths": ["ClickMe"], "script_path": "res://src/ExButton.cs"},
            "attach the click handler")
    b.setup("editor_set_node_groups", "editor", {"node_path": "Ball", "groups": ["ex_balls", "ex_all"]},
            "a group to find")
    b.setup("editor_set_node_groups", "editor", {"node_path": "ClickMe", "groups": ["ex_ui"]},
            "a group to find")
    b.setup("editor_connect_signal", "editor",
            {"source_path": "ClickMe", "signal": "pressed", "target_path": "Main",
             "method": "_on_clickme_pressed"}, "a connection for the signal readers")
    b.setup("editor_connect_signal", "editor",
            {"source_path": "Tick", "signal": "timeout", "target_path": "Main",
             "method": "_on_tick_timeout"}, "a second connection, different signal")
    b.setup("project_add_autoload", "editor", {"name": "ExAuto", "path": "res://src/ExAuto.cs"},
            "autoload subject")
    b.setup("project_build_csharp", "editor",
            {"configuration": "Debug", "timeout_ms": 300000, "rescan": True},
            "the C# scripts must compile before the game endpoint can run them")
    b.setup("editor_save_scene", "editor", {}, "persist the scene the game endpoint will load")

    # --- family (2): editor read / inspect ---------------------------------
    b.tool("editor_find_nodes_by_type",
           [{"type": "ColorRect"}, {"type": "Label"}, {"type": "Node2D"}, {"type": "Button"},
            {"type": "Timer"}],
           {"type": 123}, probe_note="type is typed string, not int")
    b.tool("editor_find_nodes_in_group",
           [{"group": "ex_balls"}, {"group": "ex_all"}, {"group": "ex_ui"}, {"group": "ex_all"},
            {"group": "ex_ui"}],
           {"group": ""}, probe_note="empty group name")
    b.tool("editor_get_collision_info",
           [{"node_path": "Body"}, {}, {"node_path": "BodyShape"}, {"node_path": "Ball"},
            {"node_path": "Main"}],
           {"node_path": "NoSuchNode"}, probe_note="node does not exist")
    b.tool("editor_get_input_actions", [{}, {}, {}, {}, {}], {"bogus_argument": 1},
           probe_note="out-of-contract argument")
    b.tool("editor_get_node_groups",
           [{"node_path": "Ball"}, {"node_path": "ClickMe"}, {"node_path": "Main"},
            {"node_path": "PaddleLeft"}, {"node_path": "Tick"}],
           {"node_path": "NoSuchNode"}, probe_note="node does not exist")
    b.tool("editor_get_node_signals",
           [{"node_path": "ClickMe"}, {"node_path": "Tick"}, {"node_path": "Main"},
            {"node_path": "Ball"}, {"node_path": "Body"}],
           {"node_path": "NoSuchNode"}, probe_note="node does not exist")
    b.tool("editor_get_physics_layers",
           [{"node_path": "Body"}, {"node_path": "Body"}, {"node_path": "Main"},
            {"node_path": "Ball"}, {"node_path": "Body"}],
           {"node_path": "NoSuchNode"}, probe_note="node does not exist")
    b.tool("editor_list_signal_connections",
           [{}, {"node_path": "ClickMe"}, {"signal_name": "pressed"}, {"scope": "user"},
            {"scope": "internal"}],
           {"scope": "bogus"}, probe_note="scope is an enum of all/user/internal")
    b.tool("editor_analyze_signal_flow",
           [{}, {"node_path": "ClickMe"}, {"node_path": "Main"}, {"node_path": "Tick"},
            {"node_path": ""}],
           {"node_path": "NoSuchNode"}, probe_note="node does not exist")
    b.tool("editor_get_open_scripts", [{}, {}, {}, {}, {}], {"bogus_argument": 1},
           probe_note="out-of-contract argument")
    b.tool("editor_get_output_log",
           [{"max_lines": 10}, {"max_lines": 50}, {"filter": "error"}, {"filter": "scene"}, {}],
           {"max_lines": -1}, probe_note="negative max_lines")
    b.tool("editor_get_selection",
           [{}, {"top_only": True}, {}, {"top_only": False}, {}], {"bogus_argument": 1},
           probe_note="out-of-contract argument")
    b.tool("editor_get_performance_monitors", [{}, {}, {}, {}, {}], {"bogus_argument": 1},
           probe_note="out-of-contract argument")
    b.tool("editor_execute_gdscript",
           [{"code": "return 1 + 1"},
            {"code": "return EditorInterface.get_edited_scene_root().name"},
            {"code": "return Engine.get_version_info()[\"major\"]"},
            {"code": "return ProjectSettings.get_setting(\"application/config/name\")"},
            {"code": "return Performance.get_monitor(Performance.TIME_FPS)"}],
           {"code": "this is not valid gdscript at all ("},
           probe_note="unparseable GDScript")
    b.tool("editor_get_scene_tree",
           [{}, {"max_depth": 1}, {"max_depth": 2}, {}, {"max_depth": 3}],
           {"max_depth": -2}, probe_note="max_depth below the contract's -1 floor")
    b.tool("editor_get_node_properties",
           [{"path": "Ball"}, {"path": "Main"}, {"path": "Background"},
            {"path": "Ball", "properties": ["position", "color"]}, {"path": "ClickMe"}],
           {"path": "NoSuchNode"}, probe_note="node does not exist")

    # --- family (3): running_game query (game endpoint) ---------------------
    g = "game"
    b.tool("running_game_find_nearby_nodes",
           [{"position": {"x": 400, "y": 270}, "radius": 120},
            {"position": {"x": 400, "y": 270}, "radius": 1000},
            {"position": {"x": 0, "y": 0}, "radius": 100},
            {"position": {"x": 400, "y": 270}, "radius": 200, "type_filter": "ColorRect"},
            {"position": {"x": 400, "y": 270}, "radius": 200, "group_filter": "ex_balls"}],
           {"position": "not-a-vector"}, port=g, probe_note="position is typed object, not string")
    b.tool("running_game_find_nodes_by_script",
           [{"script": "res://src/Ball.cs"}, {"script": "res://src/Ball.cs", "properties": ["position"]},
            {"script": "res://src/Paddle.cs"}, {"script": "res://src/ExButton.cs"},
            {"script": "res://src/PongGame.cs"}],
           {"script": 123}, port=g, probe_note="script is typed string, not int")
    b.tool("running_game_find_ui_elements",
           [{}, {"type_filter": "Label"}, {"type_filter": "Button"}, {"type_filter": "ColorRect"}, {}],
           {"bogus_argument": 1}, port=g, probe_note="out-of-contract argument")
    b.tool("running_game_get_autoload_node",
           [{"name": "ExAuto"}, {"name": "ExAuto", "properties": ["name"]}, {"name": "ExAuto"},
            {"name": "ExAuto"}, {"name": "ExAuto"}],
           {"name": "NoSuchAuto"}, port=g, probe_note="autoload is not registered")
    b.tool("running_game_get_node_properties_batch",
           [{"nodes": [{"node_path": "Ball"}]},
            {"nodes": [{"node_path": "Ball", "properties": ["position"]},
                       {"node_path": "PaddleLeft", "properties": ["position"]}]},
            {"nodes": [{"node_path": "Main"}]},
            {"nodes": [{"node_path": "ClickMe", "properties": ["text", "position"]}]},
            {"nodes": [{"node_path": "Ball"}, {"node_path": "PaddleRight"}]}],
           {"nodes": [{"node_path": "NoSuchNode"}]}, port=g, probe_note="node does not exist")
    b.tool("running_game_get_node_properties",
           [{"node_path": "Ball"}, {"node_path": "Ball", "properties": ["position"]},
            {"node_path": "Main"}, {"node_path": "ClickMe"}, {"node_path": "Background"}],
           {"node_path": "NoSuchNode"}, port=g, probe_note="node does not exist")
    b.tool("running_game_capture_frames",
           [{"count": 2, "frame_interval": 5}, {"count": 5}, {"count": 3, "half_resolution": False},
            {"count": 2}, {"count": 4, "frame_interval": 2}],
           {"count": -1}, port=g, probe_note="negative frame count")
    b.tool("running_game_capture_signal_emissions",
           [{"node_paths": ["Tick"], "duration_ms": 300},
            {"node_paths": ["ClickMe"], "duration_ms": 300},
            {"node_paths": ["Main"], "duration_ms": 300},
            {"node_paths": ["Tick"], "signal_filter": ["timeout"], "duration_ms": 500},
            {"node_paths": ["Ball"], "duration_ms": 300}],
           {"node_paths": ["NoSuchNode"], "duration_ms": 200}, port=g,
           probe_note="node does not exist")
    b.tool("running_game_simulate_button_click_by_text",
           [{"text": "ClickMe"}, {"text": "ClickMe"}, {"text": "ClickMe"}, {"text": "lickMe"},
            {"text": "ClickMe"}],
           {"text": "NoSuchButtonText"}, port=g, probe_note="no button carries this text")

    header = ("TASK-110 batch c23 -- families (2) editor read/inspect and (3) running_game query. "
              "Editor phase: build the scene the readers need, then read it. Game phase: query the "
              "same scene while it runs, with a C# click handler whose pixel change is real.")
    return b.doc(header), b.manifest


# ---------------------------------------------------------------------------
# c1c -- the second repair batch, for the two tools c1b still could not close.
#
#   * project_validate_script: c1b built the assembly *inside* the same editor
#     process, and the tool then refused on purpose ("not compiled is not does
#     not compile": the loaded assembly predates the build). A NEW editor process
#     loads the assembly at startup, so the same five calls now get a verdict.
#   * project_set_node_property_across_scenes: c1 deleted the five scenes it had
#     created, so nothing was left to write; recreate them and write a value that
#     actually differs from the default (visible=false), because the open scene is
#     declined with force=false.
#   * project_create_script (bonus): its two probes so far succeeded (it creates
#     directories and is idempotent), so the boundary is the declared type.
# ---------------------------------------------------------------------------
def build_c1c():
    b = Builder("c1c", "_exercises/ex_files")

    b.tool("project_create_scene_file",
           [{"path": p, "root_type": "Node2D", "root_name": "ExRoot%d" % (i + 1)}
            for i, p in enumerate(SCENES_NEW)],
           {"path": "res://scenes/main.tscn"},
           ok_note="recreate the scenes c1 deleted, so the across-scenes writer has targets",
           probe_note="the scene already exists")

    b.tool("project_set_node_property_across_scenes",
           [{"type": "Node2D", "property": "visible", "value": False, "dry_run": True,
             "path_filter": "res://scenes"} for _ in range(4)]
           + [{"type": "Node2D", "property": "visible", "value": False, "dry_run": False,
               "path_filter": "res://scenes"}],
           {"type": 123, "property": "visible", "value": False, "path_filter": "res://scenes"},
           ok_note="visible=false differs from the default, so a real write changes bytes",
           probe_note="type is typed string, not int")

    b.tool("project_validate_script",
           [{"path": SCRIPT}, {"path": BALL}, {"path": PADDLE}, {"path": SCRIPTS_NEW[0]},
            {"path": SCRIPTS_NEW[1]}],
           {"path": MISSING},
           ok_note="this editor process started after c1b's build, so the assembly is loaded",
           probe_note="path does not exist")

    b.tool("project_create_script",
           [{"path": p, "content": CS_CLASS % ("ExC1c%d" % (i + 1))}
            for i, p in enumerate(["res://src/ex_c1c_1.cs", "res://src/ex_c1c_2.cs",
                                   "res://src/ex_c1c_3.cs", "res://src/ex_c1c_4.cs",
                                   "res://src/ex_c1c_5.cs"])],
           {"path": 123, "content": CS_CLASS % "ExBad"},
           ok_note="new C# script", probe_note="path is typed string, not int")

    header = ("TASK-110 batch c1c -- closes the last two family-1 gate failures (plus the bonus "
              "tool's boundary). Root causes in the header above.")
    return b.doc(header), b.manifest


BATCHES = {
    "c1": (build_c1, "_exercises/ex_files"),
    "c1b": (build_c1b, "_exercises/ex_files"),
    "c1c": (build_c1c, "_exercises/ex_files"),
    "c23": (build_c23, "_exercises/ex_scene"),
}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate a coverage exercise session.")
    parser.add_argument("--batch", required=True, choices=sorted(BATCHES))
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args(argv)

    builder_fn, project = BATCHES[args.batch]
    doc, manifest = builder_fn()
    out_dir = os.path.join(ROOT, "tools", "sessions", project)
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    session_path = os.path.join(out_dir, "%s-session.json" % args.batch)
    manifest_path = os.path.join(out_dir, "%s-manifest.json" % args.batch)
    with io.open(session_path, "w", encoding="utf-8", newline="\n") as h:
        h.write(json.dumps(doc, ensure_ascii=False, indent=2) + "\n")
    with io.open(manifest_path, "w", encoding="utf-8", newline="\n") as h:
        h.write(json.dumps({"batch": args.batch, "project": project, "calls": manifest},
                           ensure_ascii=False, indent=2) + "\n")

    by_tool = {}
    for item in manifest:
        by_tool.setdefault(item["tool"], []).append(item["intent"])
    print("batch %s: %d calls, %d tools, project %s"
          % (args.batch, len(manifest), len(by_tool), project))
    for tool in sorted(by_tool):
        intents = by_tool[tool]
        print("  %-42s n=%d ok=%d probe=%d edge=%d"
              % (tool, len(intents), intents.count("ok"), intents.count("probe"), intents.count("edge")))
    print("wrote %s\nwrote %s" % (session_path, manifest_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
