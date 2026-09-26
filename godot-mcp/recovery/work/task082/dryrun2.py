# -*- coding: utf-8 -*-
"""Dry-run 2: replicate the real patch and dump the broken region (no write)."""
import ast, re

GEN = r'H:\rebuild\godot\modules\mcp_server\scripts\gen_renamed_contract.py'
RPT = r'H:\rebuild\godot\modules\mcp_server\docs\reports\REPORT-076-small-items.md'
CPP = r'H:\rebuild\godot\modules\mcp_server\tools\editor_tilemap_write.cpp'
OUT = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task082\dryrun2.txt'
log = []
def w(s=''):
    log.append(str(s))

rpt = open(RPT, 'rb').read().decode('utf-8').split('\n')
scene_full = [l.lstrip()[1:].lstrip() for l in rpt if l.lstrip().startswith('> 获取当前编辑场景的完整场景树')][0]
ORIG_SCENE = '获取当前编辑场景的完整场景树'
SCENE_SENT = scene_full[len(ORIG_SCENE) + 1:]
cpp = open(CPP, 'rb').read().decode('utf-8')
cell_full = re.search(r'editor_set_tilemap_cell", String::utf8\(R"desc\((.*?)\)desc"\)\)', cpp, re.S).group(1)
ORIG_CELL = '设置瓦片地图单元格'
TILE_SENT = cell_full[len(ORIG_CELL) + 1:]
ORIG_RECT = '填充瓦片地图矩形区域'

src = open(GEN, 'rb').read().decode('utf-8')
DUP_START = '    # TASK-024 E-10: the new optional `mcp_port` argument. A schema override\n'
DUP_END = '    # TASK-024a E-10: the new optional `mcp_port` argument.'
i = src.find(DUP_START); j = src.find(DUP_END)
new = src[:i] + src[j:]

LITERALS = '''
# v1.22 (TASK-076 section A.1): the two append-only boundary sentences, as
# module-level literals so the two tilemap entries cannot drift apart - the same
# device as `NODE_PATH_RULE_SENTENCE` (v1.19) and `_T059_SECTION_WRITE` (v1.18).
#
# Reconstructed byte-exactly (TASK-082): the scene-tree sentence is the one
# REPORT-076 section 1.2 records together with the "42 -> 898" byte count, and
# the tilemap sentence is the one carried verbatim by the C++ literals in
# `tools/editor_tilemap_write.cpp:532/:538`, which the same table records as
# "27 -> 717" and "30 -> 720".  Both byte counts reproduce exactly, so the text
# below is the artefact's text and not a paraphrase.
SCENE_TREE_ADDRESSABILITY_SENTENCE = (
    %(scene)r
)

TILEMAP_ATLAS_GAP_SENTENCE = (
    %(tile)s
)

# The measured facts both tilemap `reason` fields cite (REPORT-076 section 1.3
# (ii), measured in REPORT-075 section 6 D5).
_T076_TILEMAP_GAP_REASON = (
    "依据 REPORT-075 §6 D5 / REPORT-076 §1.3(ii)：project_create_resource"
    "{path:res://tiles/empty_tileset.tres,type:TileSet} 返回 "
    "{\\"properties_set\\":[],…,\\"type\\":\\"TileSet\\"}；赋值前 has_tile_set:false, source_count:0, sources:[]；"
    "editor_add_resource_to_node_property{tile_set} 与 editor_set_node_property{tile_set} 都成功；"
    "赋值后 has_tile_set:true, source_count:0（E8 的“赋值没落地”被证伪）；"
    "editor_set_tilemap_cell{source_id:0,…} 返回 -32602 "
    "\\"The TileSet of this TileMapLayer has no source 0; it has: no source at all (add a TileSetAtlasSource first)\\" "
    "并带 data.suggestion。缺口 = 无任何工具能创建/填充 TileSetAtlasSource，故按能力缺口记账、不改行为。"
    "范围裁决：缺口句只挂在两个写工具上——editor_get_tilemap_info/_used_cells/_cell 与 "
    "editor_remove_all_tilemap_cells 不要求 source 存在、也不会因此失败，挂上去只会噪音化真正的调用方。"
)

'''

literals_block = LITERALS % {'scene': SCENE_SENT, 'tile': TILE_SENT}
w('literals_block lines=%d' % literals_block.count('\n'))
w('literals_block chars=%d' % len(literals_block))

anchor = 'DESCRIPTION_OVERRIDES = {\n'
new = new.replace(anchor, literals_block + anchor, 1)
w('DESCRIPTION_OVERRIDES now at line %d' % (new[:new.find('DESCRIPTION_OVERRIDES = {')].count('\n') + 1))

ENTRIES = '''    # v1.22 (TASK-076 section A.1): the two boundaries TASK-075's D4/D5 measured
    # and REPORT-076 section 1 implemented.  All three records are append-only
    # (`mode` stays the default), so the original wording stays first and
    # verbatim; the `startswith(<original> + " ")` guard above enforces that.
    "get_scene_tree": {
        "reason": (
            "TASK-076 \u00a7A.1 / REPORT-076 \u00a71.3(i)，依据 REPORT-075 \u00a75 D4 的最小复现"
            "（scripts/mcp075_d4_staleness.ps1，9/9 PASS）：player.tscn 无子节点、main.tscn 实例化它后 "
            "Player 子节点数 = 0、Player/Anim 报 -32001；打开 player.tscn 加入 AnimationPlayer \\"Anim\\" 保存后"
            "磁盘确实含 Anim，回到 main.tscn 仍为 0/-32001，新建同文件实例同样为 0，"
            "而游戏进程（从磁盘加载）/World/Player/{Body,Art,Anim} 齐全；机制是编辑器把 PackedScene 缓存成实例快照。"
            "会话内的绕法 editor_add_node{parent_path:'Player'} 之后 Player/Anim 可寻址且 editor_connect_signal 成功"
            "（connected:true, persisted:true）。「不是各工具口径不一」的出处：属性写与信号工具都经同一个 "
            "MCPTools::find_node（tools/tool_helpers.cpp:1417），同一路径结论一致；round-5 的"
            "「属性写工具到得了 Anim」来自另一上下文（先 editor_open_scene res://scenes/player.tscn，"
            "再写 path:'Anim'，那是被编辑场景根的直接子节点，不是外层场景里实例下的路径）。"
            "裁决是不改 find_node（穿越缓存会改变所有编辑器工具语义、并让读取产生写副作用），只声明边界。"
        ),
        "value": "%(orig_scene)s " + SCENE_TREE_ADDRESSABILITY_SENTENCE,
    },
    # TASK-076 section 1.2(ii): one shared sentence, two entries - they cannot
    # drift apart because both read the literal below.
    "tilemap_set_cell": {
        "reason": _T076_TILEMAP_GAP_REASON,
        "value": "%(orig_cell)s " + TILEMAP_ATLAS_GAP_SENTENCE,
    },
    "tilemap_fill_rect": {
        "reason": _T076_TILEMAP_GAP_REASON,
        "value": "%(orig_rect)s " + TILEMAP_ATLAS_GAP_SENTENCE,
    },
}
'''
entries_block = ENTRIES % {'orig_scene': ORIG_SCENE, 'orig_cell': ORIG_CELL, 'orig_rect': ORIG_RECT}
close_anchor = '    },\n}\n# v1.5: a schema override replaces the whole `inputSchema` object'
w('close_anchor count=%d' % new.count(close_anchor))
new = new.replace(close_anchor, '    },\n' + entries_block + '# v1.5: a schema override replaces the whole `inputSchema` object', 1)

nl = new.split('\n')
w('total lines=%d' % len(nl))
try:
    compile(new, GEN, 'exec')
    w('COMPILE OK')
except SyntaxError as e:
    w('SYNTAX ERROR line %s: %s' % (e.lineno, e.msg))
    w('--- context ---')
    for n in range(max(1, e.lineno - 12), min(len(nl), e.lineno + 4) + 1):
        w('%5d: %s' % (n, nl[n - 1][:160]))

open(OUT, 'w', encoding='utf-8').write('\n'.join(log))
print('written', OUT)
