#!/usr/bin/env python3
# ===========================================================================
#  modules/mcp_server/scripts/check_narrowing_points.py
#
#  TASK-023 section 3 - the **structural narrowing-point guardrail** (GDR-24).
#
#  Why this exists
#  ---------------
#  The same defect ("a JSON number the target slot cannot hold is silently
#  copied as `inf`/`0`/a wrapped int, next to a success") has now appeared in
#  four shapes, and every fix was a *shape* fix:
#
#      1. a packed container's **element**           (TASK-021 A-2)
#      2. a composite value's **component**          (TASK-021 A-4)
#      3. a plain **scalar** property member         (TASK-022 D-4)
#      4. a **dedicated setter** path                 (TASK-023 D-7)
#
#  Shape 4 existed because the gate lived inside `coerce_to_property_type`,
#  i.e. inside the `Object::set()` property-write path. Any code that computed
#  a `Vector3`/`Color` from JSON and then called `Camera3D::set_global_position`
#  or `Environment::set_bg_color` bypassed it completely.
#
#  The rule this script enforces (GDR-24)
#  -------------------------------------
#  **Every narrowing point that one of the declared spellings below matches must
#  be annotated, at the point itself, with `// MCP-NARROWING: <id>` saying
#  either which gate judged the value first, or why no caller value can reach
#  it.** A new narrowing point written in a declared spelling without an
#  annotation fails this check.
#
#  TASK-031 (M4d audit D2): the claim is now **bounded**, not unbounded
#  ------------------------------------------------------------------
#  Until TASK-031 the sentence above read "**every** narrowing point in the
#  module's tool sources", and that was false: the scanner knew only six literal
#  spellings, and M4d measured five equivalent spellings that walked straight
#  through it (all five: exit 0, the point invisible in the report):
#
#      const real_t x = 1.0e300;           implicit, out-of-range literal
#      static_cast<float>(1e300)           explicit `static_cast`
#      ::Color(1e300, 0, 0, 1)             qualified constructor
#      Vector3{1e300, 0, 0}                list-initialisation
#      Color <newline> (1e300, 0, 0, 1)    constructor split across lines
#
#  `docs/DESIGN-DETAIL.md` section 22.3b therefore forbids the unbounded
#  phrasing and requires the coverage to be (1) **declared** by the scanner
#  (`--coverage`) and (2) **probed**: one "insert -> exit 1" probe per declared
#  spelling. The probes live in `scripts/mcp031_gate6_coverage_probes.ps1`.
#
#  What this scanner does **not** cover (the declared boundary, section 22.3b)
#  ---------------------------------------------------------------------------
#   * **Implicit narrowing of a runtime `double` into `real_t`/`float`**
#     (`real_t x = some_double;`, `Color(some_double, ...)`). That needs type
#     information a textual scanner does not have. A compiler-level check would
#     see it, but it cannot be scoped to this module: the module's translation
#     units include engine headers that are themselves full of C4244 (measured
#     in REPORT-031 section 2), and SConstruct disables that warning globally
#     with the comment "unavoidable at this scale". This class therefore stays a
#     **code-review + behaviour-evidence** obligation (22.3b rules 2 and 4).
#   * **Integer narrowings** (`(int)`, `(uint8_t)`, `Vector2i`, packed ints):
#     deliberately out of scope since TASK-023 (see PATTERNS below).
#   * A narrowing whose expression is in **no declared spelling** - e.g. an
#     out-of-range literal handed to a `float` *parameter*, or a compound
#     constant expression (`real_t x = 1e300 / 2.0;`).
#
#  Rule 22.3b(2): a green run of this gate is **one of three** legs - machine
#  check + code review + behaviour evidence - never the sole proof that no new
#  silent narrowing was added.
#
#  How to run
#  ----------
#      python modules/mcp_server/scripts/check_narrowing_points.py
#          check (exit 0 = all points annotated, 1 = at least one is not)
#      python .../check_narrowing_points.py --list
#          print every point found, with its marker and this list's reason
#      python .../check_narrowing_points.py --coverage
#          print the **declared** spelling set and the declared non-coverage
#          (section 22.3b) - machine-readable form under `--json`
#      python .../check_narrowing_points.py --json
#          machine-readable form of the same report
#
#  Adding a legitimate narrowing point
#  -----------------------------------
#  1. put `// MCP-NARROWING: <ID>` on the line itself (or in the comment block
#     directly above it) with one sentence saying what judged the value first;
#  2. add the point to `PINNED` below, under its marker id, **appended to that
#     marker's own list** (the list position is the occurrence order);
#  3. if it needed a guard, that guard is `MCPTools::value_fits_slot`, called
#     before the narrowing - never a new shape-specific comparison.
#
#  A **stale** entry (a pinned marker with fewer occurrences in the file than
#  the list has entries) is also a failure: it means the list no longer
#  describes the code.
#
#  Indexing: (file, marker id, occurrence order inside the file)
#  ------------------------------------------------------------
#  A pin is matched by **(file, marker id, the n-th occurrence of that marker
#  inside that file)** - never by line number. Moving a narrowing point, or
#  inserting/removing unrelated lines above it, therefore only produces a
#  `moved` note; *adding* an unannotated point, or renaming/removing a marker,
#  is what fails.
#
#  **TASK-025 correction.** Until TASK-025 this docstring (and the `PINNED`
#  comment below, and REPORT-023's deviation item 4) *claimed* the marker+order
#  identity while `report()` really looked the pin up as
#  `PINNED[file][point["line"]]` - a line key. The practical consequence was the
#  opposite of the claim: **any** unrelated edit above a pinned point answered
#  `UNLISTED` (a false red) and every batch had to re-pin by hand (TASK-024b had
#  to renumber `tools/tool_helpers.cpp` 851 -> 986). TASK-025 replaced the data
#  structure and the lookup with the marker identity they always described; the
#  `line` field is now **documentation only** and drift is reported as a note.
#  The three failure conditions are unchanged (unannotated point / unknown
#  marker / stale entry) and are demonstrated in
#  `scripts/mcp025_gate6_index_experiments.ps1`.
# ===========================================================================

import argparse
import json
import math
import os
import re
import struct
import sys

MODULE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCAN_DIR = os.path.join(MODULE_ROOT, "tools")

# ---------------------------------------------------------------------------
# PATTERNS: the **declared** spelling set of this gate (TASK-031 / 22.3b rule 1)
#
# Before TASK-031 this was six bare regexes; M4d then showed that `::Color(`,
# `Color{`, `static_cast<float>`, an out-of-range literal and a constructor
# split across lines are equivalent spellings it did not know. It now declares:
#
#   * explicit casts: C-style `(real_t)`/`(float)` (with optional inner spaces),
#     `static_cast<real_t>`/`static_cast<float>`, and the functional spellings
#     `real_t(...)`/`float(...)` (which are casts, not declarations: the
#     lookahead rejects `float (*fn)()`);
#   * the four composite constructors in **every** spelling that is unambiguous
#     without types: `Color( ... )`, `Color{ ... }`, `Color name{ ... }`,
#     `Color name = { ... }`, optionally `::`-qualified, matched against the
#     whole file so a constructor split across lines is still one point; plus
#     `Color name( ... )` **when its argument list holds a literal that does not
#     fit a 32-bit float** (the spelling is lexically ambiguous with a function
#     declaration returning that type, so it is only reported on the value);
#   * the **implicit** spelling, but only where it is decidable without types:
#     `real_t`/`float` initialised from a literal whose 32-bit copy loses the
#     value completely (overflow to `inf`, or a non-zero underflow to `0`),
#     mirroring `MCPTools::value_fits_slot`; plus the `= (double)...` spelling.
#
# `(int)`/`(uint8_t)` casts are deliberately **out of scope** (see the docstring
# and REPORT-023's scope statement): they are overwhelmingly enum-formatting and
# error-code casts, so including them would bury the list; the two *value*
# surfaces of that family (`PackedInt32Array`/`PackedByteArray` elements and
# `Vector2i` components) are inside `coerce_to_property_type`/the component
# table and covered by GDR-22.
#
# Every entry here must have an "insert -> exit 1" probe in
# `scripts/mcp031_gate6_coverage_probes.ps1`; `--coverage` prints the set.
_PATTERN_IDS = {}


def _pattern(pattern_id, regex, spelling, checker=None, dynamic=False):
    entry = {
        "id": pattern_id,
        "regex": re.compile(regex),
        "spelling": spelling,
        "checker": checker,
        # TASK-033: a spelling whose regex cannot be written down without knowing
        # the file (a `typedef` alias name). `scan()` expands it per file, and
        # `--coverage` still prints the declared spelling.
        "dynamic": dynamic,
    }
    _PATTERN_IDS[pattern_id] = entry
    return entry


_ALIAS_TYPEDEF = re.compile(r"\btypedef\s+(?:real_t|float)\s+([A-Za-z_]\w*)\s*;")
_ALIAS_USING = re.compile(r"\busing\s+([A-Za-z_]\w*)\s*=\s*(?:real_t|float)\s*;")


def _alias_declarations(code_text):
    """The names this file declared as an alias of `real_t`/`float`.

    The collection is deliberately **per file** and textual: resolving a type
    name to its underlying type needs a symbol table, so an alias declared in a
    header (or in another translation unit) stays a declared boundary instead of
    being guessed at (see `NOT_COVERED`).
    """
    names = set()
    for match in _ALIAS_TYPEDEF.finditer(code_text):
        names.add(match.group(1))
    for match in _ALIAS_USING.finditer(code_text):
        names.add(match.group(1))
    return names


def _alias_declarator_regex(alias):
    """The declarator spelling for one alias name, same shape as `lit_float_range`."""
    return re.compile(
        r"\b%s\s+[A-Za-z_]\w*\s*(?:\[\s*[^\]]*\]\s*)?(?:=\s*|\{\s*|\()\s*\(?\s*([-+]?%s)\s*\)?"
        % (re.escape(alias), _FLOAT_LITERAL))


# A decimal (or `.5`-style) floating literal with an optional `f`/`l` suffix,
# plus the C++17 **hexadecimal** spelling (`0x1p1000f`). TASK-033 (M4e D-M4e-1)
# added the hex alternative after the M4e re-audit found `float x = 0x1p1000f;`
# invisible to the scanner: it is the same 32-bit float narrowing, spelled with a
# hexadecimal significand and a binary exponent.
_FLOAT_LITERAL = (
    r"(?:[0-9]+\.[0-9]*(?:[eE][+-]?[0-9]+)?"
    r"|[0-9]+[eE][+-]?[0-9]+"
    r"|\.[0-9]+(?:[eE][+-]?[0-9]+)?"
    r"|0[xX][0-9a-fA-F]+(?:\.[0-9a-fA-F]*)?[pP][+-]?[0-9]+)[fFlL]?"
)


def _literal_does_not_fit_float(text):
    """True when a floating literal's 32-bit copy loses the value completely.

    Overflow to `inf`, or a non-zero value underflowing to `0` - the same
    criterion as `MCPTools::value_fits_slot`'s `FLOAT32`/`REAL_T` branch
    (`tools/tool_helpers.cpp`). Precision loss that still keeps the value
    finite (e.g. `1.1`) is ordinary `float` usage and is **not** reported.
    A hexadecimal literal (`0x1p1000`) is read with `float.fromhex`, the parser
    that spells the same grammar the compiler does.
    """
    if text[-1:] in ("f", "F", "l", "L"):
        text = text[:-1]
    try:
        if text[:2].lower() == "0x":
            value = float.fromhex(text)
        else:
            value = float(text)
    except (ValueError, OverflowError):
        # `float.fromhex` raises OverflowError for an exponent no double can
        # hold, which is itself "it does not fit a 32-bit float".
        return True
    try:
        narrowed = struct.unpack("<f", struct.pack("<f", value))[0]
    except OverflowError:
        return True  # |value| > FLT_MAX: the 32-bit copy is +/-inf
    if math.isinf(narrowed) or math.isnan(narrowed):
        return True
    return value != 0.0 and narrowed == 0.0


def _literal_loses_its_value(match):
    """`_literal_does_not_fit_float` for a pattern whose group(1) is the literal."""
    return _literal_does_not_fit_float(match.group(1))


def _arguments_lose_a_value(match):
    """True when a declared object's direct-init list holds such a literal.

    Group(1) is the argument list of `Type name( ... )`. A function declaration
    returning the same type is harmless here because its parameters are not bare
    floating literals, and an in-range default value is not reported.
    """
    return any(_literal_does_not_fit_float(found.group(0)) for found in re.finditer(_FLOAT_LITERAL, match.group(1)))


PATTERNS = [
    _pattern("cast_real_t", r"\(\s*real_t\s*\)", "(real_t)"),
    _pattern("cast_float", r"\(\s*float\s*\)", "(float)"),
    _pattern("cast_static_real_t", r"static_cast\s*<\s*real_t\s*>", "static_cast<real_t>"),
    _pattern("cast_static_float", r"static_cast\s*<\s*float\s*>", "static_cast<float>"),
    _pattern("cast_func_real_t", r"(?<![\w:<])real_t\s*\((?!\s*[*&])", "real_t( ... ) (functional cast)"),
    _pattern("cast_func_float", r"(?<![\w:<])float\s*\((?!\s*[*&])", "float( ... ) (functional cast)"),
]

for _type in ("Color", "Vector2", "Vector3", "Vector4"):
    PATTERNS.append(_pattern(
        "ctor_" + _type.lower(),
        r"(?<![\w>:])(?:::)?%s\b(?:\s*[({]|\s+[A-Za-z_]\w*\s*(?:\{|=\s*\{))" % _type,
        "%s( ... ) / %s{ ... } / %s name{ ... } / %s name = { ... } (optional `::`, may span lines)" % (_type, _type, _type, _type),
    ))
    PATTERNS.append(_pattern(
        "ctor_" + _type.lower() + "_arg_literal",
        r"(?<![\w>:])(?:::)?%s\s+[A-Za-z_]\w*\s*\(([^()]*)\)" % _type,
        "%s name( ... ) whose argument list holds a literal that does not fit a 32-bit float" % _type,
        _arguments_lose_a_value,
    ))

PATTERNS.append(_pattern(
    "lit_float_range",
    r"\b(?:real_t|float)\s+[A-Za-z_]\w*\s*(?:\[\s*[^\]]*\]\s*)?(?:=\s*)?(?:\{\s*|\()?\s*\(?\s*([-+]?%s)\s*\)?" % _FLOAT_LITERAL,
    "real_t/float NAME[ [n] ] [=] [ { | ( ] [ ( | - | + ] <literal that does not fit a 32-bit float> [ ) ]",
    _literal_loses_its_value,
))

# TASK-033 (M4e D-M4e-1): a **typedef / using alias** of `real_t`/`float` - the
# fifth spelling the M4e re-audit found invisible. The alias set is a *textual*
# one and is collected per file (`_alias_declarations`), because a type name can
# only be resolved to its underlying type with a symbol table; an alias declared
# in another translation unit is therefore a declared boundary (see
# `NOT_COVERED`). `dynamic` tells `scan()` to build one declarator regex per
# name this file declared, instead of using the entry's own placeholder regex.
PATTERNS.append(_pattern(
    "lit_real_t_alias",
    r"\btypedef\s+(?:real_t|float)\s+[A-Za-z_]\w*\s*;|\busing\s+[A-Za-z_]\w*\s*=\s*(?:real_t|float)\s*;",
    "NAME declared by `typedef real_t|float NAME;` or `using NAME = real_t|float;` in the same file, then `NAME x = | { | ( [(-|+] <literal that does not fit a 32-bit float>`",
    _literal_loses_its_value,
    dynamic=True,
))

PATTERNS.append(_pattern(
    "dbl_cast_into_float",
    r"\b(?:real_t|float)\s+[A-Za-z_]\w*\s*(?:=\s*|\{\s*|\()\s*\(double\)",
    "real_t/float NAME = | { | ( (double) ...",
))

# The declared boundary (22.3b rule 1), printed by `--coverage`.
NOT_COVERED = [
    "implicit narrowing of a runtime double into real_t/float (`real_t x = some_double;`, `Color(some_double, ...)`, `Vector2 v(x, y)` after the components arrived as doubles) - needs types; a compiler check would see it but cannot be scoped to this module (REPORT-031 section 2)",
    "a float/real_t value that only *becomes* out of range through an expression (`real_t x = 1e300 / 2.0;`, a constructor argument that is a variable or a call)",
    "integer narrowings (`(int)`, `(uint8_t)`, `Vector2i`, packed ints) - out of scope since TASK-023",
    "a `typedef`/`using` alias of real_t/float declared in **another file** (a header, or a second translation unit): the alias set is collected per file, so `typedef float f32;` in one file and `f32 x = 1e300;` in another is still invisible. Resolving a type name to its underlying type needs a symbol table, not a scanner (TASK-033 covers the same-file spelling, `lit_real_t_alias`)",
    "anything outside `tools/**` (the module's other sources and the engine are not scanned)",
]

MARKER = re.compile(r"MCP-NARROWING:\s*([A-Za-z0-9_-]+)")

# ---------------------------------------------------------------------------
# PINNED: file -> {marker id -> [pin, pin, ...]}
#
# The **list position** is the pin's identity: it is the n-th occurrence of
# that marker inside that file, in source order. `line` is documentation (it is
# printed by `--list` and reported as a `moved` note when it drifts); it is
# never the lookup key.
#
# The line numbers below were current at TASK-025; they are expected to drift.
#
# status is one of
#   "gated"    - a `value_fits_slot` call judges the value before this narrowing
#   "pregated" - the value was already judged at an earlier step of the same
#                function (a component table / a coercion that ran first)
#   "safe"     - no caller value can reach the narrowing at all
#   "gate"     - this narrowing IS the gate implementation
# ---------------------------------------------------------------------------
def _pin(marker, line, status, reason):
    return {"id": marker, "line": line, "status": status, "reason": reason}


PINNED = {
    "tools/editor_input_simulation.cpp": {
        # 258, 260, 270, 272, 274, 288 (as of TASK-025)
        "G24-EDITOR-INPUT-EVENT-BUILD": [
            _pin("G24-EDITOR-INPUT-EVENT-BUILD", 258, "gated", "`_number_fits_event` in `_tool_simulate_mouse_click` / `_tool_simulate_mouse_move` / `_build_sequence_event` judges x/y before the event is built"),
            _pin("G24-EDITOR-INPUT-EVENT-BUILD", 260, "gated", "see the pin above (same helper, the global position)"),
            _pin("G24-EDITOR-INPUT-EVENT-BUILD", 270, "gated", "see the pin above (`_make_mouse_motion_event`)"),
            _pin("G24-EDITOR-INPUT-EVENT-BUILD", 272, "gated", "see the pin above"),
            _pin("G24-EDITOR-INPUT-EVENT-BUILD", 274, "gated", "see the pin above (the relative motion)"),
            _pin("G24-EDITOR-INPUT-EVENT-BUILD", 288, "gated", "`_number_fits_event(Variant(strength))` in `_tool_simulate_input_action` and in the sequence ACTION branch runs before `_make_action_event`"),
        ],
    },
    "tools/editor_node_setup.cpp": {
        # 150 (as of TASK-025)
        "G24-ENV-COLOR-COMPONENT": [
            _pin("G24-ENV-COLOR-COMPONENT", 150, "gated", "`color_from_json` runs `value_fits_slot(FLOAT32)` on every present r/g/b component before the `Color` is built"),
        ],
    },
    "tools/editor_testing_read.cpp": {
        # 412, 415 (as of TASK-025)
        "G24-DIFF-PIXEL-CHANGED": [
            _pin("G24-DIFF-PIXEL-CHANGED", 445, "safe", "`CLAMP(max_diff / 255.0, 0.3, 1.0)` is the function's own computed value, bounded to [0.3, 1.0]; no caller value reaches it"),
        ],
        "G24-DIFF-PIXEL-UNCHANGED": [
            _pin("G24-DIFF-PIXEL-UNCHANGED", 415, "safe", "`a.r * 0.3` is a product of two values the engine already stores as 32-bit floats; no caller value reaches it"),
        ],
    },
    "tools/editor_write_scene_editor.cpp": {
        # 176, 781 (as of TASK-025)
        "G24-CAMERA-COMPONENT": [
            _pin("G24-CAMERA-COMPONENT", 176, "gated", "`vector3_from_json` judged every present component with `value_fits_slot(FLOAT32)` in the loop above"),
        ],
        "G24-CAMERA-FOV": [
            _pin("G24-CAMERA-FOV", 781, "gated", "the `has_fov` block runs `value_fits_slot(FLOAT32)` on `fov` before `set_fov`"),
        ],
    },
    "tools/project_read_template.cpp": {
        # 95, 98 (as of TASK-025)
        "G24-VIEWPORT-SIZE": [
            _pin("G24-VIEWPORT-SIZE", 95, "safe", "widening: a `Vector2i` component (`int`) into a `Vector2` component (`real_t`); the source is the engine's own viewport size"),
            _pin("G24-VIEWPORT-SIZE", 98, "safe", "the zero-vector fallback of the same function"),
        ],
    },
    "tools/project_write_resource_scene.cpp": {
        # 183 (as of TASK-026: the pin moved from 147 when the two resource
        # writers gained the `_resource_property_value` shaping step above it)
        "G24-RESOURCE-SET-WIDTH": [
            _pin("G24-RESOURCE-SET-WIDTH", 190, "safe", "the comparison's own width; the requested side reached this function through the `REAL_T` gate of `coerce_to_property_type`, so the cast cannot lose a value that was accepted"),
        ],
    },
    "tools/running_game_input.cpp": {
        # 345, 425, 448, 458, 501 (as of TASK-025)
        "G24-GAME-INPUT-VECTOR2": [
            _pin("G24-GAME-INPUT-VECTOR2", 345, "gated", "`_event_vector2` runs `_event_number_fits` (FLOAT32) on x and y immediately above"),
        ],
        "G24-GAME-INPUT-DEFAULT": [
            _pin("G24-GAME-INPUT-DEFAULT", 425, "safe", "`Vector2()` is the zero-vector default of `_event_vector2`; the numbers a caller does send go through the gated dictionary branch"),
            _pin("G24-GAME-INPUT-DEFAULT", 448, "safe", "see the pin above"),
            _pin("G24-GAME-INPUT-DEFAULT", 458, "safe", "see the pin above (`relative`)"),
        ],
        "G24-GAME-INPUT-ACTION-STRENGTH": [
            _pin("G24-GAME-INPUT-ACTION-STRENGTH", 501, "gated", "`_event_number_fits(Variant(strength))` in the ACTION branch runs before the cast"),
        ],
    },
    "tools/running_game_node_write.cpp": {
        # 128, 142, 161, 171, 173, 221 (as of TASK-028: all six moved by one line
        # when the `_path_member_slot` / `split_property_path` block was inserted
        # above them; TASK-025's note still applies - under the identity index a
        # moved line is a note, not a re-pin, but the list is kept exact here).
        "G24-NW-COMPONENTS": [
            _pin("G24-NW-COMPONENTS", 128, "pregated", "every object reaching `vector_from_dictionary` was rebuilt by `_check_components` (`coerce_to_property_type` + `_component_fits_slot`); the casts cannot narrow an unfit value"),
            _pin("G24-NW-COMPONENTS", 142, "pregated", "see the pin above"),
            _pin("G24-NW-COMPONENTS", 161, "pregated", "see the pin above (`Vector4`, TASK-021 A-3)"),
            _pin("G24-NW-COMPONENTS", 171, "pregated", "see the pin above; the `Color` slot is `COMPONENT_WIDTH_FLOAT32` (GDR-24), not `REAL_T`"),
            _pin("G24-NW-COMPONENTS", 173, "pregated", "see the `Color` pin above (the `a` component, on the continuation line)"),
            _pin("G24-NW-COMPONENTS", 262, "pregated", "TASK-033 (B5 batch 1): the four `Quaternion` members, added with `serialize_variant`'s `{x,y,z,w}` read shape and `vector_component_hint`/`_vector_components` (COMPONENT_WIDTH_REAL - `core/math/quaternion.h` declares `real_t x, y, z, w`). Every component was rebuilt by `_check_components` first, so the four casts cannot narrow an unfit value"),
        ],
        # The TASK-025 E-3 rect case: one source line carrying four `(real_t)`
        # casts (the two `Vector2` halves of a `Rect2`).
        "G24-NW-RECT-COMPONENTS": [
            _pin("G24-NW-RECT-COMPONENTS", 221, "pregated", "TASK-025: every component was rebuilt by `_check_components` with the `REAL_T` slot (`Rect2` stores `real_t` members, `core/math/rect2.h`) before this fold; the `Rect2i` twin's `(int)` casts are out of this scan's pattern set and are pinned by the same marker comment in the source"),
        ],
        # TASK-037 D2 (self-audit): the node-write family's read-back comparison,
        # the sibling of `G24-RESOURCE-SET-WIDTH` in
        # `tools/project_write_resource_scene.cpp`. Two casts on two lines:
        # `request_image` (what the write submitted, at the member's width) and
        # `matches` (the comparison itself). Both are the comparison's **own**
        # width, and the requested side arrived here through
        # `coerce_to_property_type(..., ValueSlot::FROM_TARGET_TYPE)`, i.e. the
        # `REAL_T` gate for a `FLOAT` target (`prepare_node_property_value`), so
        # no value the gate accepted can be narrowed away here. Comparing doubles
        # instead would report every single-precision write as "the engine stored
        # something else" (`(double)(float)0.1 != 0.1`), which is the false
        # positive the resource writer's marker documents.
        "G24-NW-SET-WIDTH": [
            _pin("G24-NW-SET-WIDTH", 1075, "safe", "the comparison's own width; the requested side passed the `REAL_T` gate of `coerce_to_property_type` in `prepare_node_property_value` before this line, so the cast cannot lose an accepted value (TASK-037 D2, mirrors G24-RESOURCE-SET-WIDTH)"),
            _pin("G24-NW-SET-WIDTH", 1077, "safe", "the second cast of the same comparison (`matches`), see the pin above"),
        ],
    },
    "tools/running_game_read_scene.cpp": {
        # 182, 264, 318 (as of TASK-025)
        "G24-NODE-POSITION-FALLBACK": [
            _pin("G24-NODE-POSITION-FALLBACK", 182, "safe", "the deliberate `(0,0)` fallback for a node with no 2D position property (documented divergence); no caller value"),
        ],
        "G24-GAME-FIND-NEARBY-TARGET": [
            _pin("G24-GAME-FIND-NEARBY-TARGET", 264, "gated", "`value_fits_slot(FLOAT32)` on `position.x`/`position.y` immediately above"),
        ],
        "G24-GAME-FIND-NEARBY-RADIUS": [
            _pin("G24-GAME-FIND-NEARBY-RADIUS", 318, "gated", "`value_fits_slot(FLOAT32)` on `radius` above"),
        ],
    },
    "tools/running_game_test_execution.cpp": {
        # 123 (as of TASK-025)
        "G24-GAME-SCENARIO-STRENGTH": [
            _pin("G24-GAME-SCENARIO-STRENGTH", 123, "gated", "`_build_scenario_events` judges `steps[i].strength` in the whole-scenario pass that runs before any step is injected"),
        ],
    },
    # TASK-036 (B5 batch 4): the two style-box argument preconditions. `Color()`
    # here is the zero-colour default the validator needs to have *some* value in
    # its out parameter; it is never the value that reaches a `StyleBoxFlat`, so
    # no caller number can narrow through it.
    "tools/project_theme_write.cpp": {
        "G24-THEME-STYLEBOX-DEFAULT": [
            _pin("G24-THEME-STYLEBOX-DEFAULT", 403, "safe", "the zero-colour default of the `bg_color` argument check; the parsed value is what reaches the style box"),
            _pin("G24-THEME-STYLEBOX-DEFAULT", 407, "safe", "the zero-colour default of the `border_color` argument check; the parsed value is what reaches the style box"),
        ],
    },
    # TASK-036 (B5 batch 4): `running_game_move_player_to_target`. One marker for
    # the file's whole movement arithmetic; the two points that really narrow an
    # incoming number are the `(real_t)speed` casts, and the handler judges
    # `speed` with `value_fits_slot(REAL_T)` before the task exists. Everything
    # else is a `real_t -> real_t` copy, a widening, or a distance between
    # already-`real_t` members. The pins are in source order (occurrence order).
    "tools/running_game_navigation_write.cpp": {
        "G24-MOVE-VECTOR": [
            _pin("G24-MOVE-VECTOR", 165, "safe", "the zero-vector default of `node_position`; no caller value"),
            _pin("G24-MOVE-VECTOR", 169, "safe", "widening a `real_t` `Vector2` into a `Vector3`"),
            _pin("G24-MOVE-VECTOR", 171, "safe", "the no-position fallback of `node_position`"),
            _pin("G24-MOVE-VECTOR", 183, "safe", "`real_t -> real_t` narrowing of an already-`real_t` `Vector3` component"),
            _pin("G24-MOVE-VECTOR", 276, "safe", "derived from the already-gated `Vector3` target"),
            _pin("G24-MOVE-VECTOR", 287, "safe", "widening the already-gated 2D target into the shared `Vector3` form"),
            _pin("G24-MOVE-VECTOR", 322, "pregated", "`read_component` ran `value_fits_slot(REAL_T)` on x/y/z"),
            _pin("G24-MOVE-VECTOR", 323, "pregated", "`read_component` ran `value_fits_slot(REAL_T)` on x/y"),
            _pin("G24-MOVE-VECTOR", 414, "safe", "a distance between `real_t` `Vector3` members"),
            _pin("G24-MOVE-VECTOR", 415, "safe", "a distance between `real_t` `Vector2` components"),
            _pin("G24-MOVE-VECTOR", 448, "safe", "`real_t` components of a step the gate already bounded"),
            _pin("G24-MOVE-VECTOR", 453, "gated", "`direction` is a normalized `real_t` vector and `speed` passed `value_fits_slot(REAL_T)` in the handler"),
            _pin("G24-MOVE-VECTOR", 457, "gated", "same as the point above, with the tick delta clamped to <= 0.1 s"),
            _pin("G24-MOVE-VECTOR", 459, "safe", "`real_t` components of a step the gate already bounded"),
            _pin("G24-MOVE-VECTOR", 461, "safe", "`real_t` components of a step the gate already bounded"),
            _pin("G24-MOVE-VECTOR", 470, "safe", "a look-at rotation computed from the already-gated target"),
            _pin("G24-MOVE-VECTOR", 502, "safe", "widening the agent's own `Vector2` path point"),
            _pin("G24-MOVE-VECTOR", 515, "safe", "a distance between `real_t` `Vector3` members"),
            _pin("G24-MOVE-VECTOR", 516, "safe", "a distance between `real_t` `Vector2` components"),
            _pin("G24-MOVE-VECTOR", 532, "safe", "a distance between `real_t` `Vector3` members"),
            _pin("G24-MOVE-VECTOR", 533, "safe", "a distance between `real_t` `Vector2` components"),
            _pin("G24-MOVE-VECTOR", 564, "safe", "a distance between `real_t` `Vector3` members"),
            _pin("G24-MOVE-VECTOR", 565, "safe", "a distance between `real_t` `Vector2` components"),
            _pin("G24-MOVE-VECTOR", 591, "safe", "a distance between `real_t` `Vector3` members"),
            _pin("G24-MOVE-VECTOR", 592, "safe", "a distance between `real_t` `Vector2` components"),
            _pin("G24-MOVE-VECTOR", 733, "safe", "promoting the already-gated 2D target into the shared `Vector3` form"),
            _pin("G24-MOVE-VECTOR", 750, "safe", "`real_t -> real_t` narrowing of the already-gated target"),
            _pin("G24-MOVE-VECTOR", 826, "safe", "`real_t -> real_t` narrowing of the already-gated positions"),
            _pin("G24-MOVE-VECTOR", 828, "safe", "widening the server's own `Vector2` path point"),
        ],
    },
    # TASK-033 (B5 batch 1): the three new files of the animation family. Each
    # point is the pre-gated copy of a caller value into a `real_t` slot, and the
    # `value_fits_slot` call that judged it is named in the reason (DESIGN-DETAIL
    # section 22.3b rule 4: a new narrowing point names the gate it passes).
    "tools/editor_animation_write.cpp": {
        # 347 (as of TASK-033)
        "G24-ANIM-EASING": [
            _pin("G24-ANIM-EASING", 347, "gated", "`value_fits_slot(p_easing, REAL_T)` in `set_animation_keyframe_on` runs immediately above, so this copy is an `Animation::track_insert_key` argument that cannot narrow an unfit value"),
        ],
    },
    "tools/editor_animation_tree_write.cpp": {
        # 288, 516 (as of TASK-033)
        "G24-ANIM-POSITION": [
            _pin("G24-ANIM-POSITION", 288, "gated", "both components passed `value_fits_slot(REAL_T)` (`position_x`, `position_y`) immediately above; the two casts build the `Vector2` `AnimationNodeStateMachine::add_node` takes"),
            _pin("G24-ANIM-POSITION", 516, "gated", "the same two `value_fits_slot(REAL_T)` calls above the `set_blend_tree_node_on` position, which is the `Vector2` `AnimationNodeBlendTree::add_node` takes"),
        ],
    },
    "tools/tool_helpers.cpp": {
        # `MCPTools::editor_log_lines` was added above it). This entry is the one
        # TASK-024b had to renumber by hand (851 -> 986) because the old lookup
        # was line-keyed; since TASK-025 it would have kept matching without the
        # edit, and the same is true of this one. 1051 -> 1136 for TASK-027 (the
        # OBJECT write helper was added above it).
        "G24-THE-GATE": [
            _pin("G24-THE-GATE", 1136, "gate", "this `(float)` copy is the judgement itself (the result is compared against `value`); calling the gate here would recurse"),
        ],
    },
}


def _code_text(lines):
    """The file's code, with comments and string/char literals blanked out.

    Character positions are preserved exactly: every blanked byte becomes a
    space and every newline stays a newline, so a match offset maps back to its
    line number (and the printed source line) byte-for-byte. Block comments
    (`/* ... */`) are tracked across lines - the module's tool sources start
    with a 2000-line licence banner, so a line scanner that only knew `//`
    would be reading prose as code. This replaced the old per-line `_code_only`
    because TASK-031 must also see a construct that **spans lines**.
    """
    out_lines = []
    in_string = None
    in_block = False
    for line in lines:
        out = []
        i = 0
        while i < len(line):
            c = line[i]
            if in_block:
                if line.startswith("*/", i):
                    in_block = False
                    out.append("  ")
                    i += 2
                    continue
                out.append(" ")
                i += 1
                continue
            if in_string:
                if c == "\\":
                    out.append("  ")
                    i += 2
                    continue
                if c == in_string:
                    in_string = None
                out.append(" ")
                i += 1
                continue
            if line.startswith("/*", i):
                in_block = True
                out.append("  ")
                i += 2
                continue
            if line.startswith("//", i):
                out.append(" " * (len(line) - i))
                i = len(line)
                continue
            if c == '"' or c == "'":
                in_string = c
                out.append(" ")
                i += 1
                continue
            out.append(c)
            i += 1
        out_lines.append("".join(out))
    return "\n".join(out_lines)


def _marker_at(lines, index):
    """The marker id on line `index` (0-based) or in the comment block above it."""
    if MARKER.search(lines[index]):
        return MARKER.search(lines[index]).group(1)
    j = index - 1
    while j >= 0:
        stripped = lines[j].strip()
        if stripped.startswith("//"):
            m = MARKER.search(lines[j])
            if m:
                return m.group(1)
            j -= 1
            continue
        if stripped == "":
            return None
        return None
    return None


def scan():
    """Every narrowing point in `tools/`, as a list of dicts.

    A **point is a line**: one line of source becomes one point carrying every
    declared spelling that matched starting on it (a `(real_t)` cast on a line
    that also constructs a `Color` is one reviewable point, not two). That keeps
    the identity used by `PINNED` - (file, marker id, occurrence in file) -
    independent of how many patterns matched.
    """
    points = []
    for root, dirs, files in os.walk(SCAN_DIR):
        dirs.sort()
        for name in sorted(files):
            if not name.endswith((".cpp", ".h")):
                continue
            path = os.path.join(root, name)
            rel = os.path.relpath(path, MODULE_ROOT).replace(os.sep, "/")
            with open(path, encoding="utf-8", errors="replace") as handle:
                lines = handle.read().split("\n")
            code_text = _code_text(lines)
            matched = {}
            for pattern in PATTERNS:
                if pattern["dynamic"]:
                    # TASK-033: the alias spelling - one declarator regex per name
                    # this file declared (`_alias_declarations`).
                    for alias in sorted(_alias_declarations(code_text)):
                        for match in _alias_declarator_regex(alias).finditer(code_text):
                            checker = pattern["checker"]
                            if checker is not None and not checker(match):
                                continue
                            line = code_text.count("\n", 0, match.start()) + 1
                            matched.setdefault(line, set()).add(pattern["id"])
                    continue
                for match in pattern["regex"].finditer(code_text):
                    checker = pattern["checker"]
                    if checker is not None and not checker(match):
                        continue
                    line = code_text.count("\n", 0, match.start()) + 1
                    matched.setdefault(line, set()).add(pattern["id"])
            for line in sorted(matched):
                points.append({
                    "file": rel,
                    "line": line,
                    "patterns": sorted(matched[line]),
                    "marker": _marker_at(lines, line - 1),
                    "text": lines[line - 1].strip(),
                })
    return points


def _self_check():
    """The list must be internally consistent: a marker key names its own pins."""
    problems = []
    for file, markers in sorted(PINNED.items()):
        for marker, pins in sorted(markers.items()):
            for index, pin in enumerate(pins):
                if pin["id"] != marker:
                    problems.append("%s: entry #%d of marker '%s' carries id '%s'" % (file, index, marker, pin["id"]))
    if problems:
        raise RuntimeError("PINNED is inconsistent:\n  " + "\n  ".join(problems))


def report(points):
    """Compare the scan against `PINNED`.

    A pin is identified by **(file, marker id, occurrence order inside the
    file)**, never by line number: moving a narrowing point, or inserting lines
    above it, is a refactor, while a *new* point is what this gate exists to
    catch. The pinned line number is kept as documentation and reported as a
    `moved` note when it drifts, so the list is still reviewable, but drift
    alone does not fail the check.

    The three failure conditions:
      * `unannotated` - a narrowing point with no `// MCP-NARROWING:` marker;
      * `unlisted`    - a marked point whose (file, marker id, occurrence) has no
                        pin, including the case of *more* occurrences in the
                        file than the list registers;
      * `stale`       - a pinned (file, marker id) with fewer occurrences in the
                        file than the list registers (the point is gone, or its
                        marker was renamed).
    """
    _self_check()

    unannotated = []
    unlisted = []
    moved = []
    stale = []

    matched = {}
    for point in points:
        file = point["file"]
        marker = point["marker"]
        if marker is None:
            unannotated.append(point)
            # Kept in both lists, as before TASK-025: an unmarked point is a
            # failure under either name and the report should say so plainly.
            unlisted.append(point)
            continue
        pins = PINNED.get(file, {}).get(marker)
        if pins is None:
            unlisted.append(point)
            continue
        occurrence = matched.get((file, marker), 0)
        if occurrence >= len(pins):
            # More occurrences of this marker than the list registers: the
            # extra point has no pin of its own.
            unlisted.append(point)
            continue
        pin = pins[occurrence]
        point["pin"] = pin
        matched[(file, marker)] = occurrence + 1
        if pin["line"] != point["line"]:
            moved.append({
                "file": file,
                "marker": marker,
                "occurrence": occurrence,
                "pinned_line": pin["line"],
                "line": point["line"],
            })

    # A pinned (file, marker) with no (or too few) matching points is stale.
    for file, markers in sorted(PINNED.items()):
        for marker, pins in sorted(markers.items()):
            found = matched.get((file, marker), 0)
            if found < len(pins):
                stale.append({"file": file, "marker": marker, "pinned_count": len(pins), "found_count": found})

    return {
        "scanned": len(points),
        "files": sorted({p["file"] for p in points}),
        "pinned": sum(len(pins) for markers in PINNED.values() for pins in markers.values()),
        "unannotated": unannotated,
        "unlisted": unlisted,
        "moved": moved,
        "stale": stale,
        "points": points,
        "coverage": coverage(),
    }


def coverage():
    """The declared spelling set and the declared non-coverage (22.3b rule 1)."""
    return {
        "note": "The guarantee of this gate is limited to this spelling set (DESIGN-DETAIL section 22.3b).",
        "scan_target": "modules/mcp_server/tools/**/*.{cpp,h}, code only (comments, block comments and string/char literals blanked)",
        "spellings": [{"id": p["id"], "spelling": p["spelling"]} for p in PATTERNS],
        "not_covered": list(NOT_COVERED),
        "probe_regression": "scripts/mcp031_gate6_coverage_probes.ps1 (one insert -> exit 1 probe per spelling)",
        "guarantee_position": "one of three legs - machine check + code review (a new write path must name the gate it passes) + behaviour evidence (the M4 wrong-value matrix); a green run here is never the sole proof (22.3b rule 2)",
    }


def _pin_of(point):
    """The pin a scanned point resolved to, or None (set by `report`)."""
    return point.get("pin")


def _print_coverage():
    declared = coverage()
    print("declared narrowing-point coverage (GDR-24 / TASK-031 / DESIGN-DETAIL section 22.3b)")
    print("  scan target : %s" % declared["scan_target"])
    print("  declared narrowing spellings (%d):" % len(PATTERNS))
    for pattern in PATTERNS:
        print("    %-20s %s" % (pattern["id"], pattern["spelling"]))
    print("  declared NOT covered (the boundary this gate must not be paraphrased beyond):")
    for item in declared["not_covered"]:
        print("    - %s" % _wrap_ascii(item, "      "))
    print("  probe regression : %s" % declared["probe_regression"])
    print("  guarantee        : %s" % _wrap_ascii(declared["guarantee_position"], "                     "))


def _wrap_ascii(text, indent="                    ", width=112):
    """The report is consumed through ASCII-only wrappers; keep the lines flat."""
    words = text.split(" ")
    lines = []
    current = ""
    for word in words:
        if current and len(current) + 1 + len(word) > width:
            lines.append(current)
            current = word
        else:
            current = (current + " " + word).strip()
    if current:
        lines.append(current)
    return ("\n" + indent).join(lines)


def _print_result(result):
    print("narrowing-point guardrail (GDR-24 / TASK-023; TASK-031: declared spelling coverage)")
    print("  module root : %s" % MODULE_ROOT)
    print("  scanned     : %d narrowing point(s) in %d file(s)" % (result["scanned"], len(result["files"])))
    print("  pinned      : %d" % result["pinned"])
    print("  coverage    : %d declared spelling(s) (see `--coverage`); the guarantee is bounded by that set" % len(PATTERNS))

    for point in result["points"]:
        pin = _pin_of(point)
        status = pin["status"] if pin else "UNLISTED"
        marker = point["marker"] or "UNMARKED"
        print("  [%-8s] %s:%d  %s  %s" % (status, point["file"], point["line"], marker, point["text"][:80]))

    ok = True
    if result["unannotated"]:
        ok = False
        print("\nFAIL: %d narrowing point(s) carry no `// MCP-NARROWING:` marker:" % len(result["unannotated"]))
        for point in result["unannotated"]:
            print("  %s:%d  %s" % (point["file"], point["line"], point["text"]))
    if result["unlisted"]:
        ok = False
        print("\nFAIL: %d narrowing point(s) have no pin at their (file, marker id, occurrence):" % len(result["unlisted"]))
        for point in result["unlisted"]:
            print("  %s:%d  marker=%s  %s" % (point["file"], point["line"], point["marker"], point["text"]))
    if result["stale"]:
        ok = False
        print("\nFAIL: %d pinned marker(s) have no matching narrowing point any more:" % len(result["stale"]))
        for entry in result["stale"]:
            print("  %s  marker=%s  pinned=%d found=%d" % (entry["file"], entry["marker"], entry["pinned_count"], entry["found_count"]))
    if result["moved"]:
        print("\nnote: %d pinned line number(s) drifted (the pin is by marker id + occurrence, so this is not a failure; update the list when convenient):" % len(result["moved"]))
        for entry in result["moved"]:
            print("  %s  marker=%s  occurrence=%d  pinned_line=%s  now=%s" % (entry["file"], entry["marker"], entry["occurrence"], entry["pinned_line"], entry["line"]))

    if ok:
        print("\nPASS: every narrowing point of the module that one of the declared spellings")
        print("      matches is annotated and pinned; the declared set is bounded and probed")
        print("      (`--coverage`; TASK-031 / DESIGN-DETAIL section 22.3b), a new point in one of")
        print("      those spellings fails this check whether or not unrelated lines moved, and a")
        print("      vanished marker fails as a stale entry.")
    return ok


def main():
    parser = argparse.ArgumentParser(description="check the module's narrowing points (GDR-24)")
    parser.add_argument("--list", action="store_true", help="print every point with its pin and reason")
    parser.add_argument("--coverage", action="store_true", help="print the declared spelling set and the declared non-coverage (section 22.3b)")
    parser.add_argument("--json", action="store_true", help="print the report as JSON")
    args = parser.parse_args()

    if args.coverage and not args.json:
        _print_coverage()
        return 0

    points = scan()
    result = report(points)

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if _is_ok(result) else 1
    if args.list:
        _print_result(result)
        for file, markers in sorted(PINNED.items()):
            for marker, pins in sorted(markers.items()):
                for index, pin in enumerate(pins):
                    print("  PIN %s  marker=%s  occurrence=%d  line(comment)=%d [%s] %s" % (file, marker, index, pin["line"], pin["status"], pin["reason"]))
        return 0 if _is_ok(result) else 1
    return 0 if _print_result(result) else 1


def _is_ok(result):
    return not (result["unannotated"] or result["unlisted"] or result["stale"])


if __name__ == "__main__":
    sys.exit(main())
