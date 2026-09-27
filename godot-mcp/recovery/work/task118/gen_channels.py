#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-118 section A: author `tools/tool_channels.json`.

Every one of the 177 contract tools gets ONE authoritative evidence channel:

    file_effect   the tool's contract artifact is a file on disk
    pixel_effect  the tool's contract artifact is the rendered frame/viewport
    editor_state  the tool's contract artifact is in-process state (the editor's
                  own GUI/plugin/filesystem state, or the running game's runtime
                  state) that neither a file nor a screenshot records; it can only
                  be read back by ANOTHER independent call whose payload carries
                  the written value verbatim (the `expect` mechanism)
    payload       the tool is a query: its own answer IS the measurement

The channel is the axis the TASK-118 decision added: `达标` is now judged on the
declared channel with content-level evidence, instead of on whichever of
pixel/file happened to move. The `(channel, subject)` pair below is the
declaration; `tool_coverage.py` loads this file, refuses to run when it does not
cover the contract exactly, and prints both the channel and this basis in
TOOL-COVERAGE.md. Re-running this script reproduces the JSON byte for byte.
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def _find_root(start):
    cur = start
    while True:
        if os.path.isfile(os.path.join(cur, "tools", "tool_coverage.py")):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            raise SystemExit("cannot find the godot-mcp root above %s" % start)
        cur = parent


ROOT = _find_root(HERE)
OUT = os.path.join(ROOT, "tools", "tool_channels.json")

FILE = "file_effect"
PIXEL = "pixel_effect"
STATE = "editor_state"
PAYLOAD = "payload"

# channel -> (subject, why this channel and not another)
GROUPS = {
    FILE: (
        "a file on disk（它在盘上留下的产物）",
        "契约写的是盘上的产物：它落盘之后可以被任何一次 project_read_* / project_get_filesystem_tree 重新读到，"
        "所以权威证据是文件本身，不是回包里的成功字样，也不是编辑器画面。",
    ),
    PIXEL: (
        "渲染出来的画面/视口（像素）",
        "契约改变的是被渲染的画面：编辑器视口或运行中游戏的帧，ledger 的 ok_effect_observed（截图前后真的变了像素）"
        "就是这条通道的内容级证据，回包里的成功字样不算。",
    ),
    STATE: (
        "进程内的存在态（编辑器 GUI/插件/文件系统，或运行期游戏的内存态）",
        "契约改变的状态既不在盘上、也不（在这个工程的视口里）可靠地反映成像素：它是编辑器进程自己的 GUI / 插件 / "
        "文件系统状态，或运行中游戏进程的内存态。这条通道只接受**另一次独立读调用**在自己的回包里**逐字**包含被写入的值的证据"
        "（会话 manifest 的 witness_read + expect，本工具会回到 trace 里再核一次）；写工具自己的回包不算。",
    ),
    PAYLOAD: (
        "它自己回包里的测量结果",
        "契约是查询：回包本身就是测量结果，不存在「另一次调用」可等（TASK-111 的 READ_VERBS 规则）。"
        "内容级证据 = ok=true 且回包是实质载荷。",
    ),
}

# tool -> (channel, subject-override or None)
TOOLS = [
    # ---- project queries -----------------------------------------------------
    ("project_get_info", PAYLOAD, "项目元信息"),
    ("project_get_filesystem_tree", PAYLOAD, "项目文件树"),
    ("project_search_file_names", PAYLOAD, "按文件名搜索的结果"),
    ("project_search_file_contents", PAYLOAD, "按内容搜索的结果"),
    ("project_get_settings", PAYLOAD, "ProjectSettings 的当前值"),
    ("project_convert_uid_to_path", PAYLOAD, "uid→path 的换算结果"),
    ("project_convert_path_to_uid", PAYLOAD, "path→uid 的换算结果"),
    ("project_read_scene_file_content", PAYLOAD, "场景文件的文本"),
    ("project_get_scene_exports", PAYLOAD, "场景的导出清单"),
    ("project_list_scripts", PAYLOAD, "脚本清单"),
    ("project_read_script", PAYLOAD, "脚本文件的文本"),
    ("project_validate_script", PAYLOAD, "校验判词"),
    ("project_find_files_referencing_symbol", PAYLOAD, "引用检索的结果"),
    ("project_get_scene_dependencies", PAYLOAD, "场景依赖清单"),
    ("project_read_resource", PAYLOAD, "资源文件的文本"),
    ("project_get_resource_preview", PAYLOAD, "资源预览"),
    ("project_get_export_info", PAYLOAD, "导出信息"),
    ("project_list_export_presets", PAYLOAD, "预设清单"),
    ("project_read_shader", PAYLOAD, "shader 源码文本"),
    ("project_get_shader_params", PAYLOAD, "shader 参数表"),
    ("project_get_theme_info", PAYLOAD, "主题（Theme）内容"),
    ("project_find_unused_resources", PAYLOAD, "未使用资源清单"),
    ("project_analyze_scene_complexity", PAYLOAD, "复杂度分析结果"),
    ("project_find_script_references", PAYLOAD, "脚本引用清单"),
    ("project_detect_circular_dependencies", PAYLOAD, "环依赖判词"),
    ("project_get_statistics", PAYLOAD, "项目统计"),
    ("project_validate_scripts", PAYLOAD, "批量校验判词"),
    ("project_read_text_file", PAYLOAD, "任意文本文件的字节"),
    ("project_get_android_preset_info", PAYLOAD, "Android 预设信息（本机没有 Android 预设，只测到缺失）"),

    # ---- editor queries ------------------------------------------------------
    ("editor_get_scene_tree", PAYLOAD, "编辑场景的树"),
    ("editor_get_node_properties", PAYLOAD, "节点属性值"),
    ("editor_get_node_groups", PAYLOAD, "节点的 groups 列表"),
    ("editor_find_nodes_in_group", PAYLOAD, "按组检索的结果"),
    ("editor_get_selection", PAYLOAD, "编辑器自己的 EditorSelection"),
    ("editor_get_errors", PAYLOAD, "错误列表"),
    ("editor_get_output_log", PAYLOAD, "编辑器 Output 面板的日志行"),
    ("editor_get_node_signals", PAYLOAD, "节点的信号表"),
    ("editor_analyze_screenshot_diff", PAYLOAD, "两图差异的数值判词"),
    ("editor_get_viewport_3d_camera", PAYLOAD, "编辑器 3D 视口相机参数"),
    ("editor_get_performance_monitors", PAYLOAD, "性能监视器的采样"),
    ("editor_get_open_scripts", PAYLOAD, "打开的脚本文档"),
    ("editor_get_input_actions", PAYLOAD, "InputMap 动作表"),
    ("editor_find_nodes_by_type", PAYLOAD, "按类型检索的结果"),
    ("editor_list_signal_connections", PAYLOAD, "场景的连接表"),
    ("editor_list_animations", PAYLOAD, "动画库清单"),
    ("editor_get_animation_info", PAYLOAD, "动画的轨道/关键帧"),
    ("editor_get_tilemap_info", PAYLOAD, "TileMap/GridMap 信息"),
    ("editor_get_tilemap_used_cells", PAYLOAD, "已用格子坐标"),
    ("editor_get_tilemap_cell", PAYLOAD, "单个格子的值"),
    ("editor_get_physics_layers", PAYLOAD, "物理层掩码"),
    ("editor_get_collision_info", PAYLOAD, "碰撞体信息"),
    ("editor_get_audio_info", PAYLOAD, "音频节点信息"),
    ("editor_get_audio_bus_layout", PAYLOAD, "总线布局"),
    ("editor_get_animation_tree_structure", PAYLOAD, "AnimationTree 结构"),
    ("editor_get_navigation_info", PAYLOAD, "导航区域/代理信息"),
    ("editor_get_particle_info", PAYLOAD, "粒子系统信息"),
    ("editor_analyze_signal_flow", PAYLOAD, "信号流向分析"),
    ("editor_get_test_report", PAYLOAD, "游戏进程持久化的测试报告 / 本进程累加器"),
    ("editor_execute_gdscript", PAYLOAD, "被求值的表达式返回值"),

    # ---- game queries --------------------------------------------------------
    ("running_game_get_scene_tree", PAYLOAD, "运行中游戏的场景树"),
    ("running_game_get_node_properties", PAYLOAD, "运行期节点属性值"),
    ("running_game_get_node_property_samples", PAYLOAD, "属性随时间的采样"),
    ("running_game_execute_gdscript", PAYLOAD, "游戏进程里被求值的返回值"),
    ("running_game_capture_frames", PAYLOAD, "连续帧的载荷"),
    ("running_game_capture_screenshot", PAYLOAD, "帧截图载荷（回包里的 base64 图）"),
    ("running_game_capture_signal_emissions", PAYLOAD, "信号发射记录"),
    ("running_game_find_nodes_by_script", PAYLOAD, "按脚本检索的结果"),
    ("running_game_get_autoload_node", PAYLOAD, "autoload 节点查询"),
    ("running_game_get_node_properties_batch", PAYLOAD, "批量属性值"),
    ("running_game_find_ui_elements", PAYLOAD, "UI 元素清单"),
    ("running_game_find_node_when_available", PAYLOAD, "等到的节点（{\"found\":true,...} 就是测量结果）"),
    ("running_game_find_nearby_nodes", PAYLOAD, "附近节点清单"),
    ("running_game_assert_node_state", PAYLOAD, "断言判词（assert 动词：判词即证据）"),
    ("running_game_assert_screen_text", PAYLOAD, "断言判词（assert 动词：判词即证据）"),
    ("os_list_android_devices", PAYLOAD, "adb devices -l 的解析结果（本机 adb 在、设备为空）"),

    # ---- files on disk -------------------------------------------------------
    ("project_set_setting", FILE, "project.godot 的设置项"),
    ("project_delete_scene_file", FILE, "被删掉的 .tscn"),
    ("project_create_scene_file", FILE, "新建的 .tscn"),
    ("project_create_script", FILE, "新建的脚本文件"),
    ("project_edit_script", FILE, "被改写的脚本文件"),
    ("project_add_autoload", FILE, "project.godot 的 autoload 段"),
    ("project_remove_autoload", FILE, "project.godot 的 autoload 段"),
    ("project_edit_resource", FILE, "被改写的 .tres"),
    ("project_create_resource", FILE, "新建的 .tres"),
    ("project_create_shader", FILE, "新建的 .gdshader"),
    ("project_edit_shader", FILE, "被改写的 .gdshader"),
    ("project_create_theme", FILE, "新建的 .tres 主题"),
    ("project_set_theme_color", FILE, "主题资源里的颜色项"),
    ("project_set_theme_constant", FILE, "主题资源里的常量项"),
    ("project_set_theme_font_size", FILE, "主题资源里的字号项"),
    ("project_set_theme_stylebox", FILE, "主题资源里的 StyleBox 项"),
    ("project_set_node_property_across_scenes", FILE, "一批 .tscn 文件里的节点属性"),
    ("project_write_text_file", FILE, "被写出的文本文件"),
    ("project_build_csharp", FILE, "dotnet build 产生的程序集"),
    ("editor_add_input_action", FILE, "project.godot 的 InputMap 段"),
    ("editor_save_scene", FILE, "被保存的 .tscn"),
    ("editor_capture_screenshot", FILE, "落盘的 PNG 截图"),

    # ---- editor viewport edits (pixel_effect is the observed channel) --------
    ("editor_open_scene", PIXEL, "编辑器视口里换了一整个场景"),
    ("editor_add_node", PIXEL, "编辑场景里新增的节点（视口可见）"),
    ("editor_delete_node", PIXEL, "编辑场景里被删的节点（视口可见）"),
    ("editor_set_node_property", PIXEL, "节点属性（视口可见的那些）"),
    ("editor_duplicate_node", PIXEL, "复制出来的节点（视口可见）"),
    ("editor_reparent_node", PIXEL, "节点的父级改变（视口位置随之变）"),
    ("editor_add_resource_to_node_property", PIXEL, "挂到节点属性上的资源（视口可见）"),
    ("editor_set_anchor_preset", PIXEL, "Control 的锚点（视口布局随之变）"),
    ("editor_set_node_property_batch", PIXEL, "一批节点的属性（视口可见）"),
    ("editor_add_nodes_batch", PIXEL, "批量新增的节点（视口可见）"),
    ("editor_set_tilemap_cell", PIXEL, "TileMap 格子（视口画出来了）"),
    ("editor_set_tilemap_cells_in_rect", PIXEL, "TileMap 矩形区域（视口画出来了）"),
    ("editor_remove_all_tilemap_cells", PIXEL, "清空后的 TileMap（视口画出来了）"),
    ("editor_set_shader_material", PIXEL, "材质/shader 挂载（视口着色随之变）"),
    ("editor_set_shader_param", PIXEL, "shader uniform（视口着色随之变）"),
    ("editor_add_raycast", PIXEL, "射线探测节点（视口可见）"),
    ("editor_setup_collision_shape", PIXEL, "碰撞形状（视口可见）"),
    ("editor_bake_navigation_mesh", PIXEL, "烘焙出的导航网格（视口可见）"),
    ("editor_set_particle_material", PIXEL, "粒子材质（视口可见）"),
    ("editor_set_particle_color_gradient", PIXEL, "粒子渐变（视口可见）"),
    ("editor_set_particle_preset", PIXEL, "粒子预设（视口可见）"),
    ("editor_set_node_property_updates", PIXEL, "逐帧属性更新（视口随之变）"),
    ("running_game_set_node_property", PIXEL, "运行中节点的属性（画面随之变）"),
    ("running_game_play_input_recording", PIXEL, "回放按键驱动出的画面"),
    ("running_game_move_player_to_target", PIXEL, "玩家被移到的位置（画面随之变）"),
    ("running_game_simulate_button_click_by_text", PIXEL, "点击按钮引发的画面变化"),
    ("running_game_run_test_scenario", PIXEL, "场景脚本跑出的画面/状态"),
    ("running_game_run_stress_test", PIXEL, "压力测试跑出的画面/状态"),

    # ---- in-process state that only a read-back can witness ------------------
    ("editor_play_scene", STATE, "编辑器的运行条状态（EditorInterface.is_playing_scene()）"),
    ("editor_stop_scene", STATE, "编辑器的运行条状态（EditorInterface.is_playing_scene()）"),
    ("editor_add_scene_instance", STATE, "内存里活场景树上的实例节点"),
    ("editor_rename_node", STATE, "内存里活场景的节点名"),
    ("editor_connect_signal", STATE, "内存里活场景的连接表"),
    ("editor_disconnect_signal", STATE, "内存里活场景的连接表"),
    ("editor_set_node_groups", STATE, "内存里活场景节点的 groups"),
    ("editor_set_node_selection", STATE, "编辑器自己的 EditorSelection"),
    ("editor_remove_node_selection", STATE, "编辑器自己的 EditorSelection"),
    ("editor_remove_output_log", STATE, "编辑器 Output 面板的日志缓冲"),
    ("editor_reload_plugin", STATE, "editor_plugins/enabled 里的 addon 与插件实例"),
    ("editor_rescan_project_filesystem", STATE, "编辑器 FileSystem dock 的扫描结果"),
    ("editor_set_auto_dismiss_dialogs", STATE, "编辑器对话框自动关闭开关（本引擎没有这个进程级开关，provider 恒为 -32000）"),
    ("editor_set_viewport_3d_camera", STATE, "编辑器 3D 视口相机"),
    ("editor_set_node_script", STATE, "节点挂载的脚本（Node.get_script().resource_path）"),
    ("editor_set_node_script_batch", STATE, "一批节点挂载的脚本（Node.get_script().resource_path）"),
    ("editor_add_gridmap", STATE, "内存里活场景树上的 GridMap 节点"),
    ("editor_set_physics_layers", STATE, "节点的 collision_layer/mask"),
    ("editor_setup_physics_body", STATE, "内存里活场景树上的物理体节点"),
    ("editor_add_mesh_instance", STATE, "内存里活场景树上的 MeshInstance3D"),
    ("editor_setup_camera_3d", STATE, "内存里活场景树上的 Camera3D"),
    ("editor_setup_lighting", STATE, "内存里活场景树上的 Light3D"),
    ("editor_set_material_3d", STATE, "节点的 surface override material"),
    ("editor_setup_world_environment", STATE, "内存里活场景树上的 WorldEnvironment"),
    ("editor_add_audio_player", STATE, "内存里活场景树上的音频节点"),
    ("editor_add_audio_bus", STATE, "内存里的音频总线布局（AudioServer）"),
    ("editor_set_audio_bus_property", STATE, "内存里的音频总线布局（AudioServer）"),
    ("editor_add_audio_bus_effect", STATE, "内存里的音频总线效果链（AudioServer）"),
    ("editor_set_control_theme", STATE, "Control 节点挂载的 Theme"),
    ("editor_create_animation", STATE, "动画库里的动画（AnimationPlayer）"),
    ("editor_add_animation_track", STATE, "动画的轨道表（Animation）"),
    ("editor_set_animation_keyframe", STATE, "动画的关键帧（Animation）"),
    ("editor_remove_animation", STATE, "动画库里的动画（AnimationPlayer）"),
    ("editor_create_animation_tree", STATE, "内存里活场景树上的 AnimationTree"),
    ("editor_add_state_machine_state", STATE, "AnimationTree 状态机里的状态"),
    ("editor_remove_state_machine_state", STATE, "AnimationTree 状态机里的状态"),
    ("editor_add_state_machine_transition", STATE, "AnimationTree 状态机里的迁移"),
    ("editor_remove_state_machine_transition", STATE, "AnimationTree 状态机里的迁移"),
    ("editor_set_blend_tree_node", STATE, "AnimationTree 的混合树节点"),
    ("editor_set_animation_tree_parameter", STATE, "AnimationTree 的参数表"),
    ("editor_setup_navigation_region", STATE, "内存里活场景树上的 NavigationRegion"),
    ("editor_setup_navigation_agent", STATE, "内存里活场景树上的 NavigationAgent"),
    ("editor_set_navigation_layers", STATE, "导航层掩码"),
    ("editor_create_particles", STATE, "内存里活场景树上的粒子系统"),
    ("running_game_create_input_recording", STATE, "运行期游戏的输入录制缓冲（由 stop 的回包逐字读回）"),
    ("running_game_stop_input_recording", STATE, "运行期游戏的输入录制缓冲（回包里的 event_count/events）"),

    # ---- scope-excluded, declared anyway so the register can name a channel --
    ("editor_simulate_key", STATE, "编辑器进程自己的输入队列（D59/GDR-21 范围排除：本循环不驱动编辑器输入）"),
    ("editor_simulate_mouse_click", STATE, "编辑器进程自己的输入队列（D59/GDR-21 范围排除）"),
    ("editor_simulate_mouse_move", STATE, "编辑器进程自己的输入队列（D59/GDR-21 范围排除）"),
    ("editor_simulate_input_action", STATE, "编辑器进程自己的输入队列（D59/GDR-21 范围排除）"),
    ("editor_simulate_input_sequence", STATE, "编辑器进程自己的输入队列（D59/GDR-21 范围排除）"),

    # ---- needs an external device -------------------------------------------
    ("os_deploy_to_android_device", PAYLOAD, "部署报告（效果落在外接设备上；本机只能测到它的拒绝分支）"),
]


def main():
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import tool_coverage as tc  # noqa: E402

    names = tc.contract_tools(ROOT)
    declared = {}
    for tool, channel, subject in TOOLS:
        if tool in declared:
            raise SystemExit("duplicate declaration: %s" % tool)
        declared[tool] = (channel, subject)
    missing = [n for n in names if n not in declared]
    extra = [n for n in declared if n not in names]
    if missing or extra:
        raise SystemExit("channel table does not match the contract: missing=%s extra=%s"
                         % (missing, extra))

    out = {
        "_comment": "TASK-118 section A: the authoritative evidence channel of every contract tool. "
                    "Generated by recovery/work/task118/gen_channels.py; tool_coverage.py refuses to run "
                    "when this file does not cover the contract exactly, and prints channel + basis per tool.",
        "_channels": {
            FILE: "盘上的文件；内容级证据 = ledger 的 ok_file_effect_observed",
            PIXEL: "渲染出的画面/视口；内容级证据 = ledger 的 ok_effect_observed",
            STATE: "进程内的存在态；内容级证据 = 会话 manifest 的 witness_read + 内容级 expect（另一次独立读调用"
                   "逐字包含被写的值），本工具回到 trace 里复核；写工具自己的回包不算",
            PAYLOAD: "查询类：ok=true 且回包是实质载荷",
        },
        "declared_at": "TASK-118",
        "total": len(names),
        "channels": {},
    }
    for tool, channel, subject in sorted(TOOLS, key=lambda t: t[0]):
        group_subject, group_why = GROUPS[channel]
        out["channels"][tool] = {
            "channel": channel,
            "subject": subject,
            "basis": "%s：%s。判定依据：%s" % (channel, subject, group_why),
        }
    counts = {}
    for entry in out["channels"].values():
        counts[entry["channel"]] = counts.get(entry["channel"], 0) + 1
    out["channel_counts"] = counts

    with io.open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(out, ensure_ascii=False, indent=1, sort_keys=False))
        fh.write("\n")
    print("wrote %s: %d tools %s" % (OUT, len(names), counts))


if __name__ == "__main__":
    main()
