"""task089 F1: make running_game_execute_gdscript use the module's ONE GDScript
source builder and the module's ONE reload-diagnostic capture.

Before: the game-side executor carried its own copy of the builder
(`_split_code_lines` / `_space_indent_unit` / `_build_source`, byte-identical
logic to the hoisted `build_execute_gdscript_source`) and called the bare
`Script::reload()`, so a real parse error was answered as
"Parameter 'code' does not compile: Parse error" and the engine's own
diagnostic - the only thing that says WHICH line and WHY - stayed on stderr.

After: the same helpers `editor_execute_gdscript` already uses
(`build_execute_gdscript_source` + `reload_gdscript_capturing` +
`gdscript_reload_failure_text` + `data.parse_error`), so a body that does not
compile names the line of the caller's own code on both endpoints.

Run with --apply; without it, only the planned replacement is printed.
"""
from __future__ import print_function
import io
import sys

PATH = r"H:\rebuild\godot\modules\mcp_server\tools\running_game_script_execution.cpp"

START_MARK = "// The method the generated script exposes."
END_MARK = "static Variant _tool_execute_gdscript(const Dictionary &p_args, MCPToolError &r_error) {"

REPLACEMENT = """// ---------------------------------------------------------------------------
// TASK-089 (F1): the source builder and the reload-diagnostic capture are the
// module's hoisted ones (`tool_helpers.h`), not a second copy here.
//
// Before this, the game-side executor carried its own `_build_source` (byte for
// byte the same layout rules as `build_execute_gdscript_source`) and called the
// bare `Script::reload()`. A body that really does not compile therefore
// answered "Parameter 'code' does not compile: Parse error" and the engine's own
// diagnostic - the only thing that names the line and the reason - was printed
// to stderr and lost. Measured on the round-7 session:
//
//   code = `var m = get_node("/root/Main"); return m.move_player(150.0)`
//   answer: -32602 "Parameter 'code' does not compile: Parse error"
//   stderr: "SCRIPT ERROR: Parse Error: Function \\"get_node()\\" not found in
//            base self." at gdscript://...:4
//
// The editor endpoint (`editor_execute_gdscript`, TASK-063 d) already answered
// the same failure with the line and the message, so the two endpoints described
// one parse error two different ways. They share the definition now.
// ---------------------------------------------------------------------------

"""


def main():
    apply = "--apply" in sys.argv
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()

    start = text.index(START_MARK)
    end = text.index(END_MARK)
    print("replacing %d chars (offset %d..%d)" % (end - start, start, end))
    print("---- first 200 chars of the removed block ----")
    print(text[start:start + 200])
    print("---- last 200 chars of the removed block ----")
    print(text[end - 200:end])

    new_text = text[:start] + REPLACEMENT + text[end:]

    # (2) the compile block: the shared builder + the capturing reload.
    old_compile = """\tscript->set_source_code(_build_source(code));
\tconst Error reload_error = script->reload();
\tif (reload_error != OK || !script->can_instantiate()) {
\t\t// The engine has already printed the parser's own diagnostics (with the
\t\t// line of the *generated* source) to stderr; the message here carries
\t\t// the verdict the caller can act on.
\t\tr_error = MCPToolError::invalid_params(vformat("Parameter 'code' does not compile: %s",
\t\t\t\tVariantUtilityFunctions::error_string(reload_error)));
\t\treturn Variant();
\t}
"""
    new_compile = """\t// TASK-089 (F1): the shared builder (a `.cs`-free, module-level definition) and
\t// the shared capture. `p_tool_script = false`: a *game* process is never the
\t// editor, and `@tool` is what the editor executor needs, not this one.
\tString generated_source;
\tint body_start_line = 0;
\tbuild_execute_gdscript_source(code, false, generated_source, &body_start_line);
\tscript->set_source_code(generated_source);
\t// TASK-063 (d) / TASK-089 (F1): `reload()` alone answers a bare `Error`; the
\t// capture reads the line and the message the engine itself reports
\t// (`_err_print_error("GDScript::reload", ..., <line>, ...)`) and
\t// `body_start_line` turns that generated line into a line of `code`.
\tconst GDScriptReloadReport reload = reload_gdscript_capturing(script.ptr(), body_start_line);
\tif (reload.error != OK) {
\t\tr_error = MCPToolError::invalid_params(gdscript_reload_failure_text(reload));
\t\tif (reload.diagnostic_seen) {
\t\t\t// The same facts, machine-readable: the line of `code` (null when the
\t\t\t// engine's line is inside this tool's own wrapper), the line the engine
\t\t\t// named in the generated source, and every diagnostic it printed.
\t\t\tDictionary diagnostics;
\t\t\tdiagnostics["line"] = reload.in_caller_code ? Variant((int64_t)reload.caller_line) : Variant();
\t\t\tdiagnostics["generated_line"] = (int64_t)reload.generated_line;
\t\t\tdiagnostics["in_caller_code"] = reload.in_caller_code;
\t\t\tdiagnostics["message"] = reload.diagnostic;
\t\t\tArray messages;
\t\t\tfor (int i = 0; i < reload.messages.size(); i++) {
\t\t\t\tmessages.push_back(reload.messages[i]);
\t\t\t}
\t\t\tdiagnostics["messages"] = messages;
\t\t\tDictionary data;
\t\t\tdata["parse_error"] = diagnostics;
\t\t\t// The engine hands a handler a line, never a column.
\t\t\tdata["parse_error_column"] = Variant();
\t\t\tr_error.data = data;
\t\t}
\t\treturn Variant();
\t}
\tif (!script->can_instantiate()) {
\t\tr_error = MCPToolError::invalid_params(
\t\t\t\t"Parameter 'code' compiled but produced a GDScript this process cannot instantiate");
\t\treturn Variant();
\t}
"""
    if old_compile not in new_text:
        raise SystemExit("REFUSED: the compile block was not found verbatim")
    new_text = new_text.replace(old_compile, new_compile, 1)

    if 'MCP_EXECUTE_METHOD' in new_text:
        new_text = new_text.replace('StringName(MCP_EXECUTE_METHOD)', 'StringName(execute_gdscript_method_name())')
    if 'MCP_EXECUTE_METHOD' in new_text:
        raise SystemExit("REFUSED: MCP_EXECUTE_METHOD is still referenced")

    if not apply:
        print("DRY RUN (pass --apply to write)")
        return 0
    with io.open(PATH, "w", encoding="utf-8", newline="") as handle:
        handle.write(new_text)
    print("written %s (%d chars)" % (PATH, len(new_text)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
