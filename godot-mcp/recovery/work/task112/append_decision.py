#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Append the TASK-112 decision (D157) to F:\\moonbit-hof-rs\\DECISIONS.md."""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
TARGET = os.path.join(ROOT, "DECISIONS.md")

ENTRY = u"""

## D157 — TASK-112：三条引擎缺陷全部修在根上（含阻塞级 D-T111-1 的 UID 重指）＋ 台账新增「证据档位」梯子（pixel_effect/file_effect > readback > count_only，witness 由 manifest 声明、由 trace 复核）＋ 契约 1 条 schema override（`editor_add_raycast.dimension` 闭集）

* 触发问题：TASK-111（D156）登记的**三条引擎侧缺陷**，其中 D-T111-1 是**阻塞级静默损坏**，且上一轮把「这些写工具的真实生效需要一个非像素见证」的口径决策留给了本轮。决策者裁定：三条全部修，档位口径采纳。
* 考虑的选项（含被否决者及理由）：
  * **D-T111-1 修法**（三选一）：①**发布后重指路径与 UID（采纳）**；②让临时文件名不可注册（否决：`ResourceFormatSaver::recognize_path()` 要求扩展名保持最后一段（`tool_helpers.h:139-146` 已把这条测过），所以临时名只能在 `res://` 下带可识别扩展名，`ResourceSaver` 一定会为它取 UID）；③绕开 `ResourceSaver`（`FileAccess` 直写）（否决：那等于让本模块自己实现 Godot 的文本/二进制序列化格式，与「不重复造轮子」和既有单一发布原语相冲突）。
  * **修复落点**：放进**模块唯一的发布原语** `publish_file_atomically()`（一次覆盖场景/资源/主题三类 `ResourceSaver` 写者），而不是逐个写者的 adapter——否决逐点修法：那是同一处缺陷的四个副本。
  * **「重指」怎么找到那个 UID**：`ResourceLoader::get_resource_uid()` 只在 `is_editor_hint()` 下读文件头（`resource_loader.cpp:1412-1426`），`ResourceUID::get_path_id()` 只在**非**编辑器进程可用（`main.cpp:2255-2257` 才开反向缓存），两条路各有一半场景失效 → 采纳「先读文件头、失败再读临时名的映射」的两段式，两条都在注释里写了引擎依据。
  * **持久化由谁做**：不自己调 `update_cache()`，而是把 **引擎自己那次调用**（`EditorNode::_resource_saved` → `EditorFileSystem::update_file`）对准目标路径——台账/缓存簿记仍归引擎一处。
  * **D-T111-2 修法**：不再在工具里手写第二份 bag 循环，改用本模块**已导出**的 `MCPTools::write_resource_properties`（TASK-049 导出时写明就是为复用/doctest）；顺带把该工具的回答补上兄弟工具已有的 `properties_set` / `ignored` / `ignored_count` / `changed` 四个读回字段（**行为面增量，已在此声明**）。
  * **D-T111-3 契约面**：**改**（`SCHEMA_OVERRIDES["add_raycast"]`，`mode=replace`，`enum:["2d","3d"]`，生成器 1.22.0 → 1.23.0，`_meta.overrides` +1）。理由：同一份契约的其它闭集（`editor_set_node_selection.mode`、`run_test_scenario.steps[].type`）都已声明 enum，而调用方从 `tools/list` 无法得知 `"4d"` 非法——这正是「契约是调用方唯一能读到的说明」这条原则的适用面。
  * **doctest 的落点**：`RectangleShape2D` 不能在 doctest 里 `memnew`（`Main::test_setup()` 初始化了物理服务器**管理器**却没 `initialize_server()`，而 `Shape2D()` 构造要 `PhysicsServer2D::get_singleton()->shape_create()`；实测 SIGSEGV）→ 改用同为 `Resource` 且**不需要服务器**的 `StyleBoxFlat`（`shadow_offset` 是 Vector2、`bg_color` 是 Color），把同一输入形状钉住；缺陷**实测**的那个 `RectangleShape2D.size` 拼写由练习工程在线上跑覆盖，报告里如实区分。
* 做法与结果（全部真实退出码）：
  * **D-T111-1**：`publish_file_atomically()` 成功后调用新的 `MCPTools::retarget_published_uid(p_path)`，把「保存回调为临时名登记的 UID」搬到真正存在的目标路径上；doctest 先在缓存里复现编辑器那次登记（`add_id(uid, scratch)`），再走真实原子发布，断言 `get_id_path(uid) == 目标` 且**该路径真的存在**，并把引用该 UID 的场景 `ResourceLoader::load()` 回来。修前 doctest 红（`…mcp-tmp.tres` 指向不存在的文件），修后 159/159 全绿。
  * **D-T111-2**：`editor_add_resource_to_node_property` 的 `resource_properties` 现在走 `MCPTools::write_resource_properties`，`{"x":48,"y":48}` 这类矢量/颜色组件对象被折成真值；doctest 同时钉住「组件填不进槽位仍是 `-32602`」（宽度门没有被放宽）。
  * **D-T111-3**：`dimension` 成为闭集（`2d`/`3d`），非法值是 `-32602` + 注册层附带的 `data.suggestion`，且判定**早于**编辑器守卫（所以 game 进程与 doctest 都能看到它）；契约同步声明 `enum`，`check_contract_subset` 在十道门里逐字核过。
  * **证据档位（B）**：`tools/tool_coverage.py` 每个工具落一档 `pixel_effect > file_effect > readback > count_only`（0 次另记 `no_calls`）。`readback` 分两种 kind：`witness_read`（写类工具，见证读调用**必须写在会话 manifest 的 `readback` 数组里**，再由台账回到该 run 的 trace **复核**：见证调用要在、要 `ok=true`、要有实质载荷）与 `own_payload`（读类动词，回包即测量）。**写工具自己响应里的成功字样不算 readback**。本轮声明 22 条、复核通过 20 条、**被拒 2 条**（`editor_add_gridmap←editor_get_scene_tree`、`editor_connect_signal←editor_list_signal_connections` 在该 run 里没有合格见证）——拒绝是机制在工作的证据，不是被藏起来的失败。档位分布：`pixel_effect` 27 / `file_effect` 24 / `readback` 77（57 own_payload + 20 witness_read）/ `count_only` 9 / `no_calls` 40，合计 177。
  * **全语料数字**：本轮**不新增 run**（C 段未做，见下），所以出现/达标/零次仍是 137 / 92 / 40；变的是**证据档位**：45 条「计数达标缺证据」现在逐条给出档位（29 → 9 条 `count_only`，其余 20 条判为 `readback`）。
* 预期影响与回滚点：
  * D-T111-1 的影响面是**所有经原子发布写出的 `res://` 资源/场景/主题**；修好之后「用工具造资源 → 挂到节点 → 保存场景 → 重新加载」这条最自然的序列不再产出加载失败，而 `.godot/uid_cache.bin` 里不再留下指向 `*.mcp-tmp.*` 的条目。
  * D-T111-2 把「此前被拒的输入」变成成功，属**行为面变更**；D-T111-2 的答案新增四个字段同样如此。两者都在本条目与报告里显式声明。
  * D-T111-3 改了契约（177 条不变，`_meta.overrides` +1，生成器 1.23.0）；任何按旧 schema 生成调用方代码的下游都只是**多**了一个 enum，不破坏既有取值。
  * **C 段（H4 导航 / H5 音频 / H9 录放 / H6 粒子）本轮未做**：预算全部用在本轮的三条引擎缺陷 + 两变体重建 + 十道门 + 档位口径上。它们仍留在不可达登记表里，方法沿用 TASK-111（先建练习工程证伪整族）。这不是结论，是待办。
  * 回滚点：主仓侧 `git revert <TASK-112 提交>`（台账/档位/声明/报告）；引擎侧 `git revert <模块提交>` 并重建两变体（契约 override 与模块同仓）。`projects/` 的 20 款正式工程与 `runs/` 只读未动。
"""


def main():
    with io.open(TARGET, "r", encoding="utf-8") as handle:
        text = handle.read()
    if "## D157 —" in text:
        print("D157 already present; nothing written")
        return 1
    with io.open(TARGET, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(ENTRY)
    print("appended D157 (%d chars)" % len(ENTRY))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
