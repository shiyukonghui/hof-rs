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


# ---------------------------------------------------------------------------
# TASK-111 batch c4 -- the 20 "reachable but never covered" write tools plus the
# 5 rows whose evidence was incomplete, on a fresh exercise project.
#
# The twenty are exactly the list TASK-110 section E left for this batch:
#   * node lifecycle (8): add_node, add_scene_instance, add_raycast,
#     add_resource_to_node_property, duplicate_node, rename_node, reparent_node,
#     disconnect_signal;
#   * the 3 setup-only tools that only ever ran 2-4 times in c23:
#     connect_signal, set_node_groups, setup_collision_shape;
#   * property / group / script writes (3): set_node_property_batch,
#     set_node_property_updates, set_node_script;
#   * physics / theme / anchor (4): setup_physics_body, set_physics_layers,
#     set_control_theme, set_anchor_preset;
#   * shader wiring (2): set_shader_material, set_shader_param.
# plus the five evidence rows: editor_get_output_log and editor_get_scene_tree
# (they had 12 effective calls but zero failing ones -> a type probe is the
# boundary), and running_game_get_node_properties_batch (same), and the two
# running_game_capture_* rows the ledger judged ineffective (the rule
# clarification lives in tools/tool_coverage.py, not here).
# ---------------------------------------------------------------------------
C4_SCRIPT = "res://src/ExC4.cs"
C4_SHADER = "res://shaders/c4.gdshader"
C4_THEME = "res://themes/c4.tres"
C4_SUB = "res://scenes/c4_sub.tscn"

C4_SHADER_CODE = ("shader_type canvas_item;\n"
                  "uniform float speed = 1.0;\n"
                  "uniform vec4 tint : source_color = vec4(1.0, 0.5, 0.5, 1.0);\n"
                  "void fragment() { COLOR = tint * 0.5; }\n")

C4_CS = ("using Godot;\n\n"
         "public partial class ExC4 : Node\n"
         "{\n"
         "    public override void _Ready() { }\n"
         "}\n")

C4_MOVE = [("Dup1", "Ren1"), ("Dup2", "Ren2"), ("Dup3", "Ren3"),
           ("Dup4", "Ren4"), ("Dup5", "Ren5")]

C4_TEMP_CONNECTS = [
    ("MidLine", "visibility_changed", "_d1"),
    ("WinLabel", "visibility_changed", "_d2"),
    ("ScoreRight", "visibility_changed", "_d3"),
    ("PaddleLeft", "visibility_changed", "_d4"),
    ("PaddleRight", "visibility_changed", "_d5"),
]


def build_c4():
    b = Builder("c4", "_exercises/ex_write")

    # --- setup: the subjects every writer below addresses -------------------
    b.setup("editor_open_scene", "editor", {"path": SCENE}, "the scene every writer addresses")
    b.setup("project_create_script", "editor", {"path": C4_SCRIPT, "content": C4_CS},
            "the script editor_set_node_script attaches")
    b.setup("project_create_shader", "editor", {"path": C4_SHADER, "shader_type": C4_SHADER_CODE},
            "a canvas_item shader (the tool keeps only the directive line)")
    b.setup("project_edit_shader", "editor", {"path": C4_SHADER, "code": C4_SHADER_CODE},
            "write the full source, so the two uniforms editor_set_shader_param addresses exist")
    b.setup("project_create_theme", "editor", {"path": C4_THEME, "name": "C4Theme"},
            "the theme editor_set_control_theme applies")
    b.setup("project_create_scene_file", "editor",
            {"path": C4_SUB, "root_type": "Node2D", "root_name": "SubRoot"},
            "the scene editor_add_scene_instance instantiates")
    b.setup("editor_add_nodes_batch", "editor", {"resolve_within_batch": True, "nodes": [
        {"type": "Node2D", "name": "Host", "parent_path": "."},
        {"type": "Node2D", "name": "ChildA", "parent_path": "Host"},
        {"type": "Node2D", "name": "ChildB", "parent_path": "Host"},
        {"type": "StaticBody2D", "name": "BodyA", "parent_path": "."},
        {"type": "StaticBody2D", "name": "BodyB", "parent_path": "."},
        {"type": "Control", "name": "Panel", "parent_path": ".",
         "properties": {"offset_left": 40.0, "offset_top": 40.0,
                        "offset_right": 240.0, "offset_bottom": 160.0}},
        {"type": "Timer", "name": "Tick", "parent_path": ".",
         "properties": {"wait_time": 0.2, "autostart": True}}]},
        "parents, physics bodies, a Control and a Timer")
    b.setup("editor_setup_collision_shape", "editor",
            {"node_path": "BodyA", "shape_type": "RectangleShape2D",
             "shape_params": {"size": {"x": 32, "y": 32}}},
            "a CollisionShape2D whose `shape` editor_add_resource_to_node_property can replace")
    b.setup("editor_connect_signal", "editor",
            {"source_path": "Tick", "signal": "timeout", "target_path": "Main",
             "method": "_on_c4_tick"}, "a connection for editor_disconnect_signal? no: kept")
    for src, sig, method in C4_TEMP_CONNECTS:
        b.setup("editor_connect_signal", "editor",
                {"source_path": src, "signal": sig, "target_path": "Main", "method": method},
                "connections editor_disconnect_signal will really remove")

    # --- node lifecycle -----------------------------------------------------
    b.tool("editor_add_node",
           [{"type": "Node2D", "name": "C4Node1", "parent_path": "."},
            {"type": "Label", "name": "C4Lbl", "parent_path": ".",
             "properties": {"text": "c4", "offset_left": 20.0, "offset_top": 20.0,
                            "offset_right": 120.0, "offset_bottom": 60.0}},
            {"type": "Node2D", "name": "C4Node2", "parent_path": "."},
            {"type": "ColorRect", "name": "C4Rect", "parent_path": ".",
             "properties": {"offset_left": 60.0, "offset_top": 300.0,
                            "offset_right": 160.0, "offset_bottom": 400.0}},
            {"type": "Timer", "name": "C4Timer", "parent_path": ".",
             "properties": {"wait_time": 0.1}}],
           {"name": "C4NoType"},
           ok_note="five new nodes of three classes",
           probe_note="`type` is required by the contract")

    b.tool("editor_add_scene_instance",
           [{"scene_path": C4_SUB, "name": "Sub%d" % i, "parent_path": "."}
            for i in range(1, 6)],
           {"scene_path": "res://scenes/no_such_scene.tscn", "name": "SubX"},
           ok_note="five instances of the created sub-scene",
           probe_note="scene_path does not exist")

    b.tool("editor_add_raycast",
           [{"dimension": "2d", "name": "Ray2D1", "parent_path": "."},
            {"dimension": "2d", "name": "Ray2D2", "parent_path": "BodyA"},
            {"dimension": "2d", "name": "Ray2D3", "parent_path": "Host"},
            {"name": "Ray2D4", "parent_path": "."},
            {"dimension": "2d", "name": "Ray2D5", "parent_path": "Host"}],
           {"name": "RayBad", "parent_path": "NoSuchParent"},
           ok_note="2D raycasts under Node2D parents",
           probe_note="parent_path does not exist")
    b.add("editor_add_raycast", "editor", {"dimension": "4d", "name": "Ray4d"}, "ok",
          "DEFECT REPRO (registration D-T111-1): an unknown 'dimension' is not refused - "
          "the implementation is `dimension == \"2d\" ? RayCast2D : RayCast3D`, so '4d' silently "
          "builds a RayCast3D instead of answering -32602")

    b.tool("editor_add_resource_to_node_property",
           [{"node_path": "BodyA/CollisionShape2D", "property": "shape",
             "resource_type": "CircleShape2D", "resource_properties": {"radius": 12.0}},
            {"node_path": "BodyA/CollisionShape2D", "property": "shape",
             "resource_type": "RectangleShape2D"},
            {"node_path": "BodyA/CollisionShape2D", "property": "shape",
             "resource_type": "CircleShape2D", "resource_properties": {"radius": 30.0}},
            {"node_path": "BodyA/CollisionShape2D", "property": "shape",
             "resource_type": "RectangleShape2D"},
            {"node_path": "BodyA/CollisionShape2D", "property": "shape",
             "resource_type": "CircleShape2D", "resource_properties": {"radius": 8.0}}],
           {"node_path": "BodyA/CollisionShape2D", "property": "shape",
            "resource_type": "NotARealResourceClass"},
           ok_note="a fresh shape resource becomes a sub-resource of the edited scene",
           probe_note="resource_type is not a Resource class")
    b.add("editor_add_resource_to_node_property", "editor",
          {"node_path": "BodyA/CollisionShape2D", "property": "shape",
           "resource_type": "RectangleShape2D", "resource_properties": {"size": {"x": 48, "y": 48}}},
          "ok",
          "DEFECT REPRO (registration D-T111-2): the tool's own refusal names this exact shape as the "
          "one to send ('a JSON object naming its components for a vector'), yet the call site "
          "(editor_write_scene_editor.cpp:725) never runs shape_vector_from_json, so Dictionary -> "
          "Vector2 is refused with -32602")

    b.tool("editor_duplicate_node",
           [{"path": "C4Node1", "new_name": "Dup1"}, {"path": "C4Lbl", "new_name": "Dup2"},
            {"path": "C4Timer", "new_name": "Dup3"}, {"path": "C4Rect", "new_name": "Dup4"},
            {"path": "Panel", "new_name": "Dup5"}],
           {"path": "NoSuchNode"},
           ok_note="five duplicates with explicit names",
           probe_note="source node does not exist")

    b.tool("editor_rename_node",
           [{"path": old, "name": new} for old, new in C4_MOVE],
           {"path": "NoSuchNode", "name": "X"},
           ok_note="the five duplicates get their final names",
           probe_note="node does not exist")

    b.tool("editor_reparent_node",
           [{"path": "Ren1", "new_parent": "Host"},
            {"path": "Ren3", "new_parent": "Host"},
            {"path": "C4Node2", "new_parent": "Sub1"},
            {"path": "BodyA/Ray2D2", "new_parent": "Host"},
            {"path": "C4Rect", "new_parent": "Panel"}],
           {"path": "Ren2", "new_parent": "NoSuchParent"},
           ok_note="five real moves between existing parents",
           probe_note="new_parent does not exist (Ren2 stays at the scene root)")

    # --- property / group / script writes -----------------------------------
    b.tool("editor_set_node_property_batch",
           [{"node_type": "ColorRect", "property": "color",
             "value": {"r": 0.2, "g": 0.3, "b": 0.9, "a": 1.0}},
            {"node_type": "Label", "property": "text", "value": "batch"},
            {"node_type": "Node2D", "property": "z_index", "value": 3},
            {"node_type": "Timer", "property": "wait_time", "value": 0.5},
            {"node_type": "Control", "property": "modulate",
             "value": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 0.5}}],
           {"node_type": 123, "property": "visible", "value": True},
           ok_note="one write per class present in the scene",
           probe_note="node_type is typed string, not int")

    b.tool("editor_set_node_property_updates",
           [{"updates": [{"path": "Ren2", "property": "text", "value": "upd1"}]},
            {"updates": [{"path": "Panel/C4Rect", "property": "color",
                          "value": {"r": 0.9, "g": 0.2, "b": 0.2, "a": 1.0}},
                         {"path": "Ren2", "property": "visible", "value": True}]},
            {"updates": [{"path": "Tick", "property": "wait_time", "value": 0.75}],
             "stop_on_error": True},
            {"updates": [{"path": "Panel", "property": "modulate",
                          "value": {"r": 0.5, "g": 0.5, "b": 1.0, "a": 1.0}}]},
            {"updates": [{"path": "C4Node1", "property": "position",
                          "value": {"x": 120.0, "y": 64.0}}]}],
           {"updates": "not-an-array"},
           ok_note="five multi-update batches, one of them with stop_on_error",
           probe_note="updates is typed array, not string")

    b.tool("editor_set_node_script",
           [{"node_path": "C4Node1", "script_path": C4_SCRIPT},
            {"node_path": "Ren2", "script_path": C4_SCRIPT},
            {"node_path": "Ren4", "script_path": C4_SCRIPT},
            {"node_path": "Ray2D1", "script_path": C4_SCRIPT},
            {"node_path": "Ray2D4", "script_path": C4_SCRIPT}],
           {"node_path": "C4Node1", "script_path": "res://src/no_such_script.cs"},
           ok_note="the created script attached to five different nodes",
           probe_note="script_path does not exist")

    b.tool("editor_set_node_groups",
           [{"node_path": "Ball", "groups": ["ex_balls", "ex_all"]},
            {"node_path": "Panel/C4Rect", "groups": ["ex_ui"]},
            {"node_path": "Panel", "groups": ["ex_ui", "ex_panel"]},
            {"node_path": "Host", "groups": ["ex_host"]},
            {"node_path": "Tick", "groups": ["ex_timer", "ex_host"]}],
           {"node_path": "NoSuchNode", "groups": ["ex_all"]},
           ok_note="groups applied to five different nodes",
           probe_note="node does not exist")

    b.setup("editor_set_node_groups", "editor", {"node_path": "Ball", "groups": ["ex_balls"]},
            "a second, shrinking write so `removed` is exercised too")

    # --- physics / theme / anchor -------------------------------------------
    b.tool("editor_setup_physics_body",
           [{"body_type": "RigidBody2D", "name": "PB1", "parent_path": "."},
            {"body_type": "StaticBody2D", "name": "PB2", "parent_path": "."},
            {"body_type": "CharacterBody2D", "name": "PB3", "parent_path": "Host"},
            {"body_type": "AnimatableBody2D", "name": "PB4", "parent_path": "."},
            {"body_type": "RigidBody2D", "name": "PB5", "parent_path": "Host"}],
           {"body_type": "NotABodyClass", "name": "PBX"},
           ok_note="four PhysicsBody2D-derived classes (Area2D is refused: it is not a PhysicsBody2D)",
           probe_note="body_type is not a Node class")

    b.tool("editor_setup_collision_shape",
           [{"node_path": "PB1", "shape_type": "RectangleShape2D",
             "shape_params": {"size": {"x": 24, "y": 24}}},
            {"node_path": "PB2", "shape_type": "CircleShape2D",
             "shape_params": {"radius": 16.0}},
            {"node_path": "Host/PB3", "shape_type": "RectangleShape2D",
             "shape_params": {"size": {"x": 10, "y": 40}}},
            {"node_path": "PB4", "shape_type": "CircleShape2D",
             "shape_params": {"radius": 8.0}},
            {"node_path": "Host/PB5", "shape_type": "RectangleShape2D",
             "shape_params": {"size": {"x": 12, "y": 12}}}],
           {"node_path": "PB1", "shape_type": "TriangleShape2D"},
           ok_note="a collision shape per body, two shape classes",
           probe_note="shape_type is outside the supported set")

    b.tool("editor_set_physics_layers",
           [{"node_path": "PB1", "layers": 1},
            {"node_path": "PB2", "layers": 2},
            {"node_path": "Host/PB3", "layers": 3, "layer_type": "collision"},
            {"node_path": "PB1", "layers": 4, "layer_type": "mask"},
            {"node_path": "PB2", "layers": 8, "layer_type": "mask"}],
           {"node_path": "PB1", "layers": -1},
           ok_note="both layer members on three bodies",
           probe_note="layers is negative, outside the uint32 mask range")

    b.tool("editor_set_control_theme",
           [{"node_path": "Panel", "theme_path": C4_THEME},
            {"node_path": "C4Lbl", "theme_path": C4_THEME},
            {"node_path": "ScoreLeft", "theme_path": C4_THEME},
            {"node_path": "WinLabel", "theme_path": C4_THEME},
            {"node_path": "PaddleLeft", "theme_path": C4_THEME}],
           {"node_path": "Panel", "theme_path": "res://themes/no_such_theme.tres"},
           ok_note="the created theme applied to five Controls",
           probe_note="theme_path does not exist")

    b.tool("editor_set_anchor_preset",
           [{"node_path": "Panel", "preset": "top_left"},
            {"node_path": "C4Lbl", "preset": "center"},
            {"node_path": "ScoreLeft", "preset": "top_left"},
            {"node_path": "WinLabel", "preset": "bottom_wide"},
            {"node_path": "PaddleRight", "preset": "center_right"}],
           {"node_path": "Panel", "preset": "no_such_preset"},
           ok_note="five documented preset names",
           probe_note="preset is not in the contract's closed set")

    # --- shader wiring ------------------------------------------------------
    b.tool("editor_set_shader_material",
           [{"node_path": "Background", "shader_path": C4_SHADER},
            {"node_path": "Panel/C4Rect", "shader_path": C4_SHADER},
            {"node_path": "PaddleLeft", "shader_path": C4_SHADER},
            {"node_path": "Panel", "shader_path": C4_SHADER},
            {"node_path": "Ball", "shader_path": C4_SHADER}],
           {"node_path": "Background", "shader_path": "res://shaders/no_such_shader.gdshader"},
           ok_note="a ShaderMaterial on five CanvasItems",
           probe_note="shader_path does not exist")

    b.tool("editor_set_shader_param",
           [{"node_path": "Background", "param": "speed", "value": 2.5},
            {"node_path": "Background", "param": "tint",
             "value": {"r": 1.0, "g": 0.0, "b": 0.0, "a": 1.0}},
            {"node_path": "Panel/C4Rect", "param": "speed", "value": 7.0},
            {"node_path": "PaddleLeft", "param": "speed", "value": 0.25},
            {"node_path": "Panel", "param": "tint",
             "value": {"r": 0.0, "g": 1.0, "b": 0.0, "a": 1.0}}],
           {"node_path": "Background", "param": "no_such_uniform", "value": 1.0},
           ok_note="both uniforms of the applied shader",
           probe_note="the shader has no uniform of that name")

    # --- evidence completion for family (2) rows ----------------------------
    b.tool("editor_get_output_log",
           [{"max_lines": 10}, {"max_lines": 100}, {"filter": "scene"},
            {"filter": "error"}, {"max_lines": 5}],
           {"max_lines": "ten"},
           ok_note="read the editor log several ways",
           probe_note="max_lines is typed integer; the TASK-110 negative probe was accepted")

    b.tool("editor_get_scene_tree",
           [{}, {"max_depth": 1}, {"max_depth": 2}, {}, {"max_depth": 3}],
           {"max_depth": "deep"},
           ok_note="walk the tree the writes above produced",
           probe_note="max_depth is typed integer; the TASK-110 -2 probe was accepted")

    # Read-backs for the writers whose effect the 2D viewport cannot show. The
    # ledger's `scene_effect` is a screenshot diff of the editor viewport, so a
    # rename, a script attachment, a group change or a physics-layer mask reads
    # as "unchanged" there even though the engine really holds the new value.
    # These calls put the engine's own answer on the trace, so the batch has a
    # second, independent witness for "it really took effect" instead of a
    # silently relaxed rule.
    b.setup("editor_get_node_properties", "editor",
            {"path": "Host/Ren1", "properties": ["name"]}, "read-back: the rename really applied")
    b.setup("editor_get_node_properties", "editor",
            {"path": "PB1", "properties": ["collision_layer", "collision_mask"]},
            "read-back: the physics layer mask really applied")
    b.setup("editor_get_node_properties", "editor",
            {"path": "Tick", "properties": ["wait_time"]},
            "read-back: the multi-update write really applied")
    b.setup("editor_get_node_properties", "editor",
            {"path": "C4Node1", "properties": ["script"]},
            "read-back: the script attachment really applied")
    b.setup("editor_get_scene_tree", "editor", {"max_depth": 3},
            "read-back: the add/duplicate/reparent structure really is there")
    b.setup("editor_get_node_groups", "editor", {"node_path": "Host"},
            "read-back: the group assignment really applied")

    b.setup("editor_save_scene", "editor", {}, "persist every write before the game endpoint loads it")
    b.setup("project_build_csharp", "editor",
            {"configuration": "Debug", "timeout_ms": 300000, "rescan": True},
            "the attached C# script must compile before the game endpoint runs")

    # --- game phase: the three running_game evidence rows -------------------
    b.tool("running_game_capture_frames",
           [{"count": 2, "frame_interval": 5}, {"count": 5}, {"count": 3, "half_resolution": False},
            {"count": 2}, {"count": 4, "frame_interval": 2}],
           {"count": -1}, port="game", probe_note="negative frame count")
    b.tool("running_game_capture_signal_emissions",
           [{"node_paths": ["Tick"], "duration_ms": 600},
            {"node_paths": ["Tick", "Main"], "duration_ms": 600},
            {"node_paths": ["Main"], "duration_ms": 300},
            {"node_paths": ["Tick"], "signal_filter": ["timeout"], "duration_ms": 900},
            {"node_paths": ["Tick"], "duration_ms": 600}],
           {"node_paths": ["NoSuchNode"], "duration_ms": 200}, port="game",
           probe_note="node does not exist")
    b.tool("running_game_get_node_properties_batch",
           [{"nodes": [{"node_path": "Ball"}]},
            {"nodes": [{"node_path": "Ball", "properties": ["position"]},
                       {"node_path": "PaddleLeft", "properties": ["position"]}]},
            {"nodes": [{"node_path": "Main"}]},
            {"nodes": [{"node_path": "ScoreLeft", "properties": ["text", "position"]}]},
            {"nodes": [{"node_path": "Ball"}, {"node_path": "PaddleRight"}]}],
           {"nodes": "Ball"}, port="game",
           probe_note="nodes is typed array; the TASK-110 probe used a merely-absent node")

    header = ("TASK-111 batch c4 -- the twenty reachable-but-uncovered editor writers plus the five "
              "evidence rows TASK-110 left open. Every boundary probe is a typed-argument violation "
              "or a missing subject, never a luck-dependent input.")
    return b.doc(header), b.manifest


# ---------------------------------------------------------------------------
# TASK-111 batch h1 -- the H1 family (3D content pipeline), seven tools.
#
# TASK-108 registered H1 as structurally unreachable because the 20-game corpus
# is 2D. That claim is about the corpus. The exercise project ships a Node3D
# scene with a mesh-bearing MeshInstance3D, which is the only precondition the
# family actually has.
# ---------------------------------------------------------------------------
H1_SCENE = "res://scenes/probe3d.tscn"
H1_MATERIAL = "res://assets/mat3d.tres"


def build_h1():
    b = Builder("h1", "_exercises/ex_3d")

    b.setup("project_create_resource", "editor",
            {"path": H1_MATERIAL, "type": "StandardMaterial3D",
             "properties": {"albedo_color": {"r": 0.9, "g": 0.2, "b": 0.2, "a": 1.0}}},
            "the material editor_set_material_3d assigns")
    b.setup("editor_open_scene", "editor", {"path": H1_SCENE},
            "Node3D root + one MeshInstance3D carrying a BoxMesh")

    b.tool("editor_add_mesh_instance",
           [{"name": "MeshA", "parent_path": "."},
            {"name": "MeshB", "parent_path": "."},
            {"name": "MeshC", "parent_path": "Body"},
            {"name": "MeshD", "parent_path": "."},
            {"name": "MeshE", "parent_path": "Body"}],
           {"name": "MeshX", "parent_path": "NoSuchParent"},
           ok_note="five MeshInstance3D nodes under two Node3D parents",
           probe_note="parent_path does not exist")

    b.tool("editor_set_material_3d",
           [{"node_path": "Body", "material_path": H1_MATERIAL},
            {"node_path": "Body", "material_path": H1_MATERIAL, "material_slot": 0},
            {"node_path": "MeshA", "material_path": H1_MATERIAL},
            {"node_path": "MeshC", "material_path": H1_MATERIAL},
            {"node_path": "Body", "material_path": H1_MATERIAL, "material_slot": 0}],
           {"node_path": "Body", "material_path": "res://assets/no_such_material.tres"},
           ok_note="the created material into the one surface Body has",
           probe_note="material_path does not exist")

    b.tool("editor_setup_camera_3d",
           [{"node_path": "."}, {"node_path": "."}, {"node_path": "Body"},
            {"node_path": "MeshA"}, {"node_path": "MeshB"}],
           {"node_path": "NoSuchNode"},
           ok_note="creates a Camera3D on a Node3D parent, and re-marks an existing one current",
           probe_note="node_path does not exist")

    b.tool("editor_set_viewport_3d_camera",
           [{"position": {"x": 0.0, "y": 2.0, "z": 5.0}},
            {"fov": 60.0},
            {"rotation_degrees": {"x": -20.0, "y": 0.0, "z": 0.0}},
            {"look_at": {"x": 0.0, "y": 0.0, "z": 0.0}},
            {"position": {"x": 1.0, "y": 1.0, "z": 1.0}, "fov": 75.0}],
           {"fov": "wide"}, probe_note="fov is typed number, not string")

    b.tool("editor_get_viewport_3d_camera",
           [{}, {}, {}, {}, {}],
           {"bogus_argument": 1}, probe_note="out-of-contract argument")

    b.tool("editor_setup_lighting",
           [{"light_type": "directional"},
            {"light_type": "omni", "parent_path": "."},
            {"light_type": "spot"},
            {"light_type": "directional", "parent_path": "Body"},
            {"light_type": "omni", "parent_path": "MeshA"}],
           {"light_type": "lava"}, probe_note="light_type is outside the supported set")

    b.tool("editor_setup_world_environment",
           [{},
            {"bg_color": {"r": 0.1, "g": 0.1, "b": 0.2}},
            {"ambient_color": {"r": 0.4, "g": 0.4, "b": 0.4}},
            {"bg_color": {"r": 0.2, "g": 0.0, "b": 0.0},
             "ambient_color": {"r": 0.1, "g": 0.1, "b": 0.1}},
            {}],
           {"bg_color": "red"}, probe_note="bg_color is typed object, not string")

    b.setup("editor_save_scene", "editor", {}, "persist the 3D scene the family built")

    header = ("TASK-111 batch h1 -- the H1 family (3D content pipeline) against a project that "
              "ships a Node3D scene. Refutes the 'structurally unreachable' inference with a real "
              "scene rather than a corpus argument; see tools/tool_coverage_unreachable.json.")
    return b.doc(header), b.manifest


# ---------------------------------------------------------------------------
# TASK-111 batch h3 -- the H3 family (TileMap / GridMap), seven tools.
#
# The write half of this family is the one TASK-108 called out as "declared
# impossible by the contract itself": editor_set_tilemap_cell's description says
# the caller must supply a TileSet that already holds a TileSetAtlasSource. The
# exercise project supplies exactly that (assets/tileset.tres + scenes/grid.tscn,
# both produced by projects/_exercises/ex_grid/mk_probe.gd), which is the
# precondition the description names - so the family becomes measurable without
# any engine change.
# ---------------------------------------------------------------------------
H3_SCENE = "res://scenes/grid.tscn"
H3_MESHLIB = "res://assets/meshlib.tres"


def build_h3():
    b = Builder("h3", "_exercises/ex_grid")

    b.setup("editor_open_scene", "editor", {"path": H3_SCENE},
            "Node2D root + TileMapLayer whose TileSet holds a TileSetAtlasSource (source 0)")

    b.tool("editor_add_gridmap",
           [{"mesh_library_path": H3_MESHLIB, "name": "GM1", "parent_path": "."},
            {"mesh_library_path": H3_MESHLIB, "name": "GM2", "parent_path": "."},
            {"mesh_library_path": H3_MESHLIB, "name": "GM3", "parent_path": "."},
            {"mesh_library_path": H3_MESHLIB, "name": "GM4", "parent_path": "."},
            {"mesh_library_path": H3_MESHLIB, "name": "GM5", "parent_path": "."}],
           {"mesh_library_path": "res://assets/no_such_library.tres", "name": "GMX"},
           ok_note="five GridMaps backed by the created MeshLibrary",
           probe_note="mesh_library_path does not exist")

    b.tool("editor_set_tilemap_cell",
           [{"node_path": "Tiles", "source_id": 0, "x": 0, "y": 0,
             "atlas_coords": {"x": 0, "y": 0}},
            {"node_path": "Tiles", "source_id": 0, "x": 2, "y": 2,
             "atlas_coords": {"x": 0, "y": 0}},
            {"node_path": "Tiles", "source_id": 0, "x": 4, "y": 4,
             "atlas_coords": {"x": 0, "y": 0}},
            {"node_path": "Tiles", "source_id": 0, "x": 6, "y": 6,
             "atlas_coords": {"x": 0, "y": 0}},
            {"node_path": "Tiles", "source_id": 0, "x": 8, "y": 8,
             "atlas_coords": {"x": 0, "y": 0}}],
           {"node_path": "Tiles", "source_id": 7, "x": 0, "y": 0,
            "atlas_coords": {"x": 0, "y": 0}},
           ok_note="five cells written through the project-provided atlas source",
           probe_note="the TileSet has no source with that id (-32602, as the description says)")

    b.tool("editor_set_tilemap_cells_in_rect",
           [{"node_path": "Tiles", "source_id": 0, "rect": {"x": 0, "y": 0, "width": 4, "height": 4},
             "atlas_coords": {"x": 0, "y": 0}},
            {"node_path": "Tiles", "source_id": 0, "rect": {"x": 10, "y": 10, "width": 2, "height": 2},
             "atlas_coords": {"x": 0, "y": 0}},
            {"node_path": "Tiles", "source_id": 0, "rect": {"x": 20, "y": 20, "width": 1, "height": 3},
             "atlas_coords": {"x": 0, "y": 0}},
            {"node_path": "Tiles", "source_id": 0, "rect": {"x": 30, "y": 30, "width": 3, "height": 1},
             "atlas_coords": {"x": 0, "y": 0}},
            {"node_path": "Tiles", "source_id": 0, "rect": {"x": 40, "y": 40, "width": 2, "height": 2},
             "atlas_coords": {"x": 0, "y": 0}}],
           {"node_path": "Tiles", "source_id": 9,
            "rect": {"x": 0, "y": 0, "width": 2, "height": 2},
            "atlas_coords": {"x": 0, "y": 0}},
           ok_note="five rectangles filled through the same source",
           probe_note="no source with that id")

    b.tool("editor_get_tilemap_info",
           [{"node_path": "Tiles"}, {"node_path": "Tiles"}, {"node_path": "Tiles"},
            {"node_path": "Tiles"}, {"node_path": "Tiles"}],
           {"node_path": "NoSuchNode"},
           ok_note="read back the layer that now holds cells",
           probe_note="node does not exist")

    b.tool("editor_get_tilemap_used_cells",
           [{"node_path": "Tiles"}, {"node_path": "Tiles"}, {"node_path": "Tiles"},
            {"node_path": "Tiles"}, {"node_path": "Tiles"}],
           {"node_path": "NoSuchNode"},
           ok_note="the cells written above are really there",
           probe_note="node does not exist")

    b.tool("editor_get_tilemap_cell",
           [{"node_path": "Tiles", "x": 0, "y": 0},
            {"node_path": "Tiles", "x": 2, "y": 2},
            {"node_path": "Tiles", "x": 10, "y": 10},
            {"node_path": "Tiles", "x": 30, "y": 30},
            {"node_path": "Tiles", "x": 40, "y": 40}],
           {"node_path": "Tiles", "x": "zero", "y": 0},
           ok_note="five occupied cells read one by one",
           probe_note="x is typed integer, not string")

    # remove_all needs a non-empty map each time to be effective, so the writer is
    # interleaved: clear -> put one cell back -> clear -> ... Five clears, five
    # real changes, one boundary probe.
    b.add("editor_remove_all_tilemap_cells", "editor", {"node_path": "Tiles"}, "ok",
          "clear #1 (the map holds 5 singles + 4+4+3+3+4 rect cells)")
    for i in range(4):
        b.add("editor_set_tilemap_cell", "editor",
              {"node_path": "Tiles", "source_id": 0, "x": 50 + i, "y": 50,
               "atlas_coords": {"x": 0, "y": 0}}, "ok",
              "re-seed one cell so the next clear is a real change")
        b.add("editor_remove_all_tilemap_cells", "editor", {"node_path": "Tiles"}, "ok",
              "clear #%d" % (i + 2))
    b.add("editor_remove_all_tilemap_cells", "editor", {"node_path": "NoSuchNode"},
          "probe", "node does not exist")

    b.setup("editor_save_scene", "editor", {}, "persist the tile edits")

    header = ("TASK-111 batch h3 -- the H3 family (TileMap / GridMap) against a project that ships "
              "a TileSet with a TileSetAtlasSource and a MeshLibrary. The write half was registered "
              "unreachable on the strength of the tool's own description; this batch supplies what "
              "that description names as the caller's precondition.")
    return b.doc(header), b.manifest


# ---------------------------------------------------------------------------
# TASK-111 batch h2 -- the H2 family (AnimationPlayer / AnimationTree /
# StateMachine), fourteen tools.
#
# Registered unreachable because no game drives motion through an AnimationPlayer.
# The precondition is one AnimationPlayer with a default library plus one node for
# a track to address; the exercise project ships both (mk_probe.gd).
#
# The state machine lives on the AnimationTree created by
# editor_create_animation_tree (its root is an AnimationNodeStateMachine), and the
# blend-tree half needs a state that holds an AnimationNodeBlendTree - which is
# what the "BT" state and the Blend2 node inside it provide. The parameter names
# are the engine's own `parameters/<state>/<param>` (AnimationTree::
# _update_properties_for_node), so `BT/B1/blend_amount` and `Idle/backward` are
# the addresses the tool looks up.
# ---------------------------------------------------------------------------
H2_SCENE = "res://scenes/anim.tscn"
H2_STATES = [("Idle", "Anim1"), ("Walk", "Anim2"), ("Run", "Anim3"),
             ("Jump", "Anim1"), ("Fall", "Anim2")]
H2_SETUP_TRANSITIONS = [("Idle", "Walk"), ("Walk", "Run"), ("Run", "Jump"),
                        ("Jump", "Fall"), ("Fall", "Idle")]
H2_TARGET_TRANSITIONS = [("Idle", "Jump"), ("Walk", "Fall"), ("Run", "Idle"),
                         ("Jump", "Walk"), ("Fall", "Run")]


def build_h2():
    b = Builder("h2", "_exercises/ex_anim")

    b.setup("editor_open_scene", "editor", {"path": H2_SCENE},
            "Node2D root + AnimationPlayer (default library) + a Node2D track target")

    b.tool("editor_create_animation",
           [{"node_path": "Player", "name": "Anim1", "length": 1.0},
            {"node_path": "Player", "name": "Anim2", "length": 2.0},
            {"node_path": "Player", "name": "Anim3", "length": 0.5},
            {"node_path": "Player", "name": "Anim4", "length": 1.5},
            {"node_path": "Player", "name": "Anim5", "length": 3.0}],
           {"node_path": "Player", "name": "BadAnim", "length": -1.0},
           ok_note="five animations in the default library",
           probe_note="a negative length is refused by the tool before the engine sees it")
    for i in (6, 7, 8):
        b.setup("editor_create_animation", "editor",
                {"node_path": "Player", "name": "Anim%d" % i, "length": 1.0},
                "an animation editor_remove_animation will really remove")

    b.tool("editor_add_animation_track",
           [{"node_path": "Player", "animation": "Anim1", "track_path": "Target:position",
             "track_type": "value"},
            {"node_path": "Player", "animation": "Anim1", "track_path": "Target:scale",
             "track_type": "value", "update_mode": "continuous"},
            {"node_path": "Player", "animation": "Anim1", "track_path": "Target:rotation",
             "track_type": "value"},
            {"node_path": "Player", "animation": "Anim2", "track_path": "Target:position",
             "track_type": "value"},
            {"node_path": "Player", "animation": "Anim3", "track_path": "Target:position",
             "track_type": "value", "update_mode": "discrete"}],
           {"node_path": "Player", "animation": "Anim1", "track_path": "Target:position",
            "track_type": "bogus"},
           ok_note="three tracks on Anim1 (one with an explicit update_mode), one each on Anim2/Anim3",
           probe_note="track_type is outside the engine's track-type set")

    b.tool("editor_set_animation_keyframe",
           [{"node_path": "Player", "animation": "Anim1", "track_index": 0, "time": 0.0,
             "value": {"x": 0.0, "y": 0.0}},
            {"node_path": "Player", "animation": "Anim1", "track_index": 0, "time": 1.0,
             "value": {"x": 100.0, "y": 0.0}, "easing": 2.0},
            {"node_path": "Player", "animation": "Anim1", "track_index": 1, "time": 0.5,
             "value": {"x": 2.0, "y": 2.0}},
            {"node_path": "Player", "animation": "Anim1", "track_index": 2, "time": 0.25,
             "value": 1.5},
            {"node_path": "Player", "animation": "Anim2", "track_index": 0, "time": 0.0,
             "value": {"x": 0.0, "y": 0.0}}],
           {"node_path": "Player", "animation": "Anim1", "track_index": 99, "time": 0.5,
            "value": {"x": 0.0, "y": 0.0}},
           ok_note="keys on three different tracks, one with a non-default easing",
           probe_note="track_index is outside the animation's track range")

    b.tool("editor_list_animations",
           [{"node_path": "Player"}, {"node_path": "Player"}, {"node_path": "Player"},
            {"node_path": "Player"}, {"node_path": "Player"}],
           {"node_path": "NoSuchNode"},
           ok_note="the library as the engine holds it",
           probe_note="node does not exist")

    b.tool("editor_get_animation_info",
           [{"node_path": "Player", "animation": "Anim1"},
            {"node_path": "Player", "animation": "Anim2"},
            {"node_path": "Player", "animation": "Anim3"},
            {"node_path": "Player", "animation": "Anim1"},
            {"node_path": "Player", "animation": "Anim2"}],
           {"node_path": "Player", "animation": "NoSuchAnim"},
           ok_note="read back the tracks and keys written above",
           probe_note="animation does not exist")

    b.tool("editor_create_animation_tree",
           [{"node_path": ".", "name": "AT%d" % i, "animation_player_path": "Player"}
            for i in range(1, 6)],
           {"node_path": ".", "name": "ATX", "animation_player_path": "NoSuchPlayer"},
           ok_note="five AnimationTrees whose animation_player NodePath is resolved by the engine",
           probe_note="animation_player_path does not exist")

    b.tool("editor_add_state_machine_state",
           [{"node_path": "AT1", "state_name": name, "state_type": "animation", "animation": anim}
            for name, anim in H2_STATES],
           {"node_path": "AT1", "state_name": "BadState", "state_type": "bogus"},
           ok_note="five animation states on AT1",
           probe_note="state_type is outside the set the tool accepts")
    # The blend-tree state and the removable extras are beyond the helper's five,
    # so they are added one by one (the helper deliberately keeps only the first
    # five so a target's `ok` count stays exactly five).
    b.add("editor_add_state_machine_state", "editor",
          {"node_path": "AT1", "state_name": "BT", "state_type": "blend_tree"}, "ok",
          "the state editor_set_blend_tree_node writes into")
    for i in range(5):
        b.add("editor_add_state_machine_state", "editor",
              {"node_path": "AT4", "state_name": "Extra%d" % i, "state_type": "animation",
               "animation": "Anim1"}, "ok",
              "a state editor_remove_state_machine_state will really remove")

    for a, c in H2_SETUP_TRANSITIONS:
        b.setup("editor_add_state_machine_transition", "editor",
                {"node_path": "AT1", "from_state": a, "to_state": c},
                "a transition editor_remove_state_machine_transition will really remove")

    b.tool("editor_add_state_machine_transition",
           [{"node_path": "AT1", "from_state": a, "to_state": c} for a, c in H2_TARGET_TRANSITIONS],
           {"node_path": "AT1", "from_state": "NoSuchState", "to_state": "Walk"},
           ok_note="five ordered pairs the setup phase did not already connect",
           probe_note="from_state is not a state of the machine")

    b.tool("editor_remove_state_machine_transition",
           [{"node_path": "AT1", "from_state": a, "to_state": c} for a, c in H2_SETUP_TRANSITIONS],
           {"node_path": "AT1", "from_state": "Idle", "to_state": "Fall"},
           ok_note="the five setup transitions, removed by the pair that names them",
           probe_note="that ordered pair was never connected")

    b.tool("editor_remove_state_machine_state",
           [{"node_path": "AT4", "state_name": "Extra%d" % i} for i in range(5)],
           {"node_path": "AT1", "state_name": "NoSuchState"},
           ok_note="the five extra states on AT4",
           probe_note="state does not exist")

    b.tool("editor_set_blend_tree_node",
           [{"node_path": "AT1", "blend_tree_state": "BT", "bt_node_name": "B1",
             "bt_node_type": "Blend2"},
            {"node_path": "AT1", "blend_tree_state": "BT", "bt_node_name": "A1",
             "bt_node_type": "Animation", "animation": "Anim1"},
            {"node_path": "AT1", "blend_tree_state": "BT", "bt_node_name": "A2",
             "bt_node_type": "Animation", "animation": "Anim2"},
            {"node_path": "AT1", "blend_tree_state": "BT", "bt_node_name": "N1",
             "bt_node_type": "OneShot"},
            {"node_path": "AT1", "blend_tree_state": "BT", "bt_node_name": "T1",
             "bt_node_type": "TimeScale"}],
           {"node_path": "AT1", "blend_tree_state": "NoSuchState", "bt_node_name": "X",
            "bt_node_type": "Blend2"},
           ok_note="a Blend2, two Animation leaves and two utility nodes inside the BT state",
           probe_note="blend_tree_state is not a state of the machine")

    b.tool("editor_set_animation_tree_parameter",
           [{"node_path": "AT1", "parameter": "BT/B1/blend_amount", "value": 0.5},
            {"node_path": "AT1", "parameter": "Idle/backward", "value": True},
            {"node_path": "AT1", "parameter": "BT/B1/blend_amount", "value": 0.25},
            {"node_path": "AT1", "parameter": "Walk/backward", "value": True},
            {"node_path": "AT1", "parameter": "Run/backward", "value": False}],
           {"node_path": "AT1", "parameter": "no_such_parameter", "value": 1.0},
           ok_note="the tree's own parameters/<state>/<param> addresses, both a float and a bool",
           probe_note="the tree's property list has no such parameter")

    b.tool("editor_get_animation_tree_structure",
           [{"node_path": "AT1"}, {"node_path": "AT2"}, {"node_path": "AT3"},
            {"node_path": "AT4"}, {"node_path": "AT5"}],
           {"node_path": "NoSuchTree"},
           ok_note="the state machine, the blend tree and the parameters read back",
           probe_note="node does not exist")

    b.tool("editor_remove_animation",
           [{"node_path": "Player", "name": name} for name in
            ["Anim4", "Anim5", "Anim6", "Anim7", "Anim8"]],
           {"node_path": "Player", "name": "NoSuchAnim"},
           ok_note="two animations created as targets and three created only to be removed",
           probe_note="animation does not exist")

    b.setup("editor_save_scene", "editor", {}, "persist the animations and the trees")

    header = ("TASK-111 batch h2 -- the H2 family (animation / AnimationTree / state machine) "
              "against a project that ships an AnimationPlayer with a default library. The blend-tree "
              "half needs a blend_tree state, which the same session creates before writing into it.")
    return b.doc(header), b.manifest


# ---------------------------------------------------------------------------
# TASK-111 batch c5 -- `editor_disconnect_signal`, the one node-lifecycle tool
# the c4 list names but c4 itself never called.
#
# A disconnect needs a connection that is really there, so the setup phase makes
# five (each on a different source, so no pair is a duplicate) and the target
# phase removes exactly those five, then reads the source back to show the user
# connection is gone.
# ---------------------------------------------------------------------------
C5_CONNECTS = [
    ("Ball", "visibility_changed", "_d1"),
    ("PaddleLeft", "visibility_changed", "_d2"),
    ("ScoreLeft", "visibility_changed", "_d3"),
    ("WinLabel", "visibility_changed", "_d4"),
    ("MidLine", "visibility_changed", "_d5"),
]


def build_c5():
    b = Builder("c5", "_exercises/ex_write6")

    b.setup("editor_open_scene", "editor", {"path": SCENE}, "the scene holding the signal sources")
    for src, sig, method in C5_CONNECTS:
        b.setup("editor_connect_signal", "editor",
                {"source_path": src, "signal": sig, "target_path": "Main", "method": method},
                "a real connection for editor_disconnect_signal to remove")

    b.tool("editor_disconnect_signal",
           [{"source_path": src, "signal": sig, "target_path": "Main", "method": method}
            for src, sig, method in C5_CONNECTS],
           {"source_path": "Ball", "signal": "visibility_changed", "target_path": "Main",
            "method": "_never_connected"},
           ok_note="the five connections the setup phase made, removed by the pair that names them",
           probe_note="that method was never connected from that signal")

    b.setup("editor_list_signal_connections", "editor",
            {"node_path": "Ball", "scope": "user"},
            "read-back: Ball has no user connection left")

    header = ("TASK-111 batch c5 -- closes the one node-lifecycle tool c4's own list named but did "
              "not call. Connect five, disconnect five, read one source back.")
    return b.doc(header), b.manifest


BATCHES = {
    "c1": (build_c1, "_exercises/ex_files"),
    "c1b": (build_c1b, "_exercises/ex_files"),
    "c1c": (build_c1c, "_exercises/ex_files"),
    "c23": (build_c23, "_exercises/ex_scene"),
    "c4": (build_c4, "_exercises/ex_write"),
    "c5": (build_c5, "_exercises/ex_write6"),
    "h1": (build_h1, "_exercises/ex_3d"),
    "h2": (build_h2, "_exercises/ex_anim"),
    "h3": (build_h3, "_exercises/ex_grid"),
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
