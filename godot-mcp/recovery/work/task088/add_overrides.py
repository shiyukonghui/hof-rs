# -*- coding: utf-8 -*-
"""task088 (4): register the override records the tree is missing.

Evidence (all measured, see work/task088/cmp_editor.txt):
  * work/task088/live/editor-tools-list.json - the live editor endpoint's full
    154-tool `tools/list` body, captured from a real session;
  * work/task088/session log of the game endpoint (73 tools).
Comparing them against `docs/tools_list.renamed.json` leaves exactly TEN tools
where the published text and the contract disagree: 7 descriptions and 3
inputSchemas. The three inputSchemas are NOT missing records - the generator
already declares `simulate_sequence`, `find_signal_connections` and
`get_test_report` as deliberate schema deviations. The seven descriptions are:
one existing record (`play_scene`, whose recorded value is an earlier revision
of the same override) and six tools with no record at all.

This script
  * appends the six missing DESCRIPTION_OVERRIDES records, each `value` being
    the text the server actually publishes (json.dumps'ed, so the literal is
    exactly the measured bytes) and each `reason` naming the evidence and
    carrying the marker, and
  * rewrites the existing `play_scene` record's `value` to the published text.

usage: python add_overrides.py [--apply]
"""
from __future__ import print_function
import io, json, os, sys

REPO = r"H:\rebuild\godot"
GEN = os.path.join(REPO, "modules", "mcp_server", "scripts", "gen_renamed_contract.py")
WORK = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task088"
LIVE = os.path.join(WORK, "live", "editor-tools-list.json")
CONTRACT = os.path.join(REPO, "modules", "mcp_server", "docs", "tools_list.renamed.json")
MARK = "[REBUILT-2C low-confidence: verify]"

NEW_NAMES = [
    "project_validate_script",
    "editor_reload_plugin",
    "editor_add_input_action",
    "project_add_autoload",
    "project_remove_autoload",
    "project_set_setting",
]

# The override tables are keyed by the FIXTURE name (`entry["old_name"]`), not by
# the wire name - a ported tool is looked up by what it was called before the
# rename. Resolved through docs/tool-rename-map.json.
OLD_NAME = {
    "project_validate_script": "validate_script",
    "editor_reload_plugin": "reload_plugin",
    "editor_add_input_action": "set_input_action",
    "project_add_autoload": "add_autoload",
    "project_remove_autoload": "remove_autoload",
    "project_set_setting": "set_project_setting",
    "editor_play_scene": "play_scene",
}

# The exact bytes of the shared TASK-043 sentence, read from the recording
# (`scripts/mcp043_description_evidence.ps1:50` carries the same $Sentence).
SENTENCE = ("When this call saves, it rewrites the entire project.godot with the engine's own "
            "whole-file writer (the engine has no partial-publish API), so every hand-written "
            "comment in that file is lost: the remaining settings are re-emitted verbatim and a "
            "repeated identical call changes no bytes (idempotent), and because the comments "
            "cannot be kept, back the file up yourself before calling if you need them.")


def live_tools():
    body = json.load(io.open(LIVE, encoding="utf-8-sig"))
    return dict((t["name"], t) for t in body["result"]["tools"])


def contract_tools():
    body = json.load(io.open(CONTRACT, encoding="utf-8"))
    return dict((t["name"], t) for t in body["result"]["tools"])


def reason_for(name, contract_text, live_text):
    if name == "project_validate_script":
        body = ("TASK-088 第 4 项（逻辑重建，依据=实测发布文本）：契约此前只写“验证脚本语法”，"
                "而服务端实际发布的描述在原文之后追加了 TASK-055 的 `.cs` 裁决说明"
                "（`valid` 只在本进程已加载的程序集确实是该源文件的构建时才为 true；"
                "`valid: false` 必须伴随 `project_build_csharp` 记录的编译诊断；"
                "两者都不是的文件以 -32000 的 'not compiled' 拒绝）。"
                "追加句取自 154 条 `tools/list` 实测响应（work/task088/live/editor-tools-list.json），"
                "原文逐字保留在句首。")
    elif name in ("project_add_autoload", "project_remove_autoload", "project_set_setting",
                  "editor_add_input_action", "editor_reload_plugin"):
        body = ("TASK-088 第 4 项（逻辑重建，依据=实测发布文本 + 已录制常量）：服务端在这 5 个工具的描述里"
                "追加了 TASK-043 的整文件写入诚实声明（`project.godot` 由引擎的整文件写入器重写、"
                "手写注释会丢失、同一调用重复执行不改变字节）。该句逐字取自录制证据 "
                "`scripts/mcp043_description_evidence.ps1:50` 的 `$Sentence`，而这 5 个工具确实在 C++ 里逐字带有它"
                "（`tools/editor_input_simulation.cpp:1244`、`tools/editor_write_scene_editor.cpp:1026`、"
                "`tools/project_autoload_write.cpp:256/263`、`tools/project_setting_write.cpp:293`）。"
                "原文逐字保留在句首。")
    else:
        body = "TASK-088 第 4 项（逻辑重建，依据=实测发布文本）。"
    return body


def main():
    apply = "--apply" in sys.argv
    live = live_tools()
    fixed = contract_tools()
    src = io.open(GEN, encoding="utf-8").read()
    log = []

    # --- 1. the six new description records ---------------------------------
    entries = []
    for name in NEW_NAMES:
        value = live[name]["description"]
        original = fixed[name]["description"]
        if not value.startswith(original + " "):
            raise SystemExit("REFUSED: the live text of %s is not '<contract text> + \" \" + ...'" % name)
        entries.append((
            "    # %s TASK-088 item 4: registered from the measured published text.\n"
            "    %s: {\n"
            "        \"reason\": (\n"
            "            %s\n"
            "            %s\n"
            "        ),\n"
            "        \"value\": %s,\n"
            "    }," % (
                MARK, json.dumps(OLD_NAME[name], ensure_ascii=False),
                json.dumps(MARK + " " + reason_for(name, original, value), ensure_ascii=False),
                json.dumps("TASK-088 依据：work/task088/live/editor-tools-list.json（实测 154 条 tools/list）"
                           "与 work/task088/cmp_editor.txt（逐工具差异）；被替换的原文逐字为："
                           + original, ensure_ascii=False),
                json.dumps(value, ensure_ascii=False),
            )))

    # Insert the new records just before the line that closes
    # DESCRIPTION_OVERRIDES: the closing `}` is the one immediately followed by
    # the v1.5 comment that introduces SCHEMA_OVERRIDES.
    close_anchor = "\n}\n# v1.5: a schema override replaces the whole `inputSchema` object"
    close = src.find(close_anchor)
    if close < 0:
        raise SystemExit("REFUSED: cannot find the end of DESCRIPTION_OVERRIDES")
    block = "\n".join(entries) + "\n"
    src = src[:close] + "\n" + block + src[close + 1:]
    log.append("  added %d DESCRIPTION_OVERRIDES record(s)" % len(entries))

    # --- 2. the play_scene value -------------------------------------------
    old_play = fixed["editor_play_scene"]["description"]
    new_play = live["editor_play_scene"]["description"]
    n = src.count(json.dumps(old_play, ensure_ascii=False))
    if n != 1:
        raise SystemExit("REFUSED: the current play_scene value occurs %d time(s) in the generator, expected 1" % n)
    src = src.replace(json.dumps(old_play, ensure_ascii=False), json.dumps(new_play, ensure_ascii=False), 1)
    log.append("  play_scene (key %s): value replaced with the published text" % OLD_NAME["editor_play_scene"])
    # and note it in that record's reason
    play_reason_tail = "被替换的原文（逐字保留以便审计）："
    if play_reason_tail not in src:
        raise SystemExit("REFUSED: cannot find the play_scene reason tail")
    src = src.replace(
        "            \"故追加一句判别点；原文逐字保留在句首。\"",
        "            \"故追加一句判别点；原文逐字保留在句首。\"\n"
        "            \"" + MARK + " TASK-088 第 4 项：本记录的 value 已改为服务端实际发布的文本\"\n"
        "            \"（实测 work/task088/live/editor-tools-list.json），因为录制里这条记录是同一改写的更早一版；\"\n"
        "            \"TASK-024 的原判据保留，文本细节以实测为准。\"",
        1)
    log.append("  play_scene: reason extended with the TASK-088 note")

    print("\n".join(log))
    if not apply:
        print("DRY RUN (pass --apply to write %s)" % GEN)
        return 0
    io.open(GEN, "w", encoding="utf-8", newline="\n").write(src)
    print("wrote %s (%d bytes)" % (GEN, len(src.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
