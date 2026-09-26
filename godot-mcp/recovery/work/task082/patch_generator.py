# -*- coding: utf-8 -*-
"""TASK-082 item 3: repair scripts/gen_renamed_contract.py.

Two edits, both evidenced:
  (a) delete the DUPLICATE `play_scene` key in SCHEMA_OVERRIDES (the first of the
      two literal keys; Python keeps the last, so removing the first is
      behaviour-preserving - pure dead-block removal);
  (b) add the three TASK-076A append-only DESCRIPTION_OVERRIDES records
      (get_scene_tree / tilemap_set_cell / tilemap_fill_rect) whose text is
      recovered byte-exactly:
        * SCENE_TREE_ADDRESSABILITY_SENTENCE, 855 B, from REPORT-076 line 55,
          cross-checked by the recorded 42 -> 898 byte count;
        * TILEMAP_ATLAS_GAP_SENTENCE, 689 B, from the C++ literal in
          tools/editor_tilemap_write.cpp:532, cross-checked by 27 -> 717 and
          30 -> 720.
"""
import ast, hashlib, os, re, sys

GEN = r'H:\rebuild\godot\modules\mcp_server\scripts\gen_renamed_contract.py'
RPT = r'H:\rebuild\godot\modules\mcp_server\docs\reports\REPORT-076-small-items.md'
CPP = r'H:\rebuild\godot\modules\mcp_server\tools\editor_tilemap_write.cpp'
LOG = r'C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task082\gen-patch.txt'

log = []
def w(s=''):
    log.append(str(s))
    print(s)

def sha(b):
    return hashlib.sha256(b).hexdigest()

# ---------------------------------------------------------------- recover text
# scene-tree sentence
rpt = open(RPT, 'rb').read().decode('utf-8').split('\n')
cands = [l.lstrip()[1:].lstrip() for l in rpt if l.lstrip().startswith('> 获取当前编辑场景的完整场景树')]
assert len(cands) == 1, 'expected exactly one report blockquote, got %d' % len(cands)
scene_full = cands[0]
ORIG_SCENE = '获取当前编辑场景的完整场景树'
assert scene_full.startswith(ORIG_SCENE + ' ')
assert len(scene_full.encode('utf-8')) == 898, 'scene full != 898 B'
SCENE_SENT = scene_full[len(ORIG_SCENE) + 1:]
assert len(SCENE_SENT.encode('utf-8')) == 855, 'scene sentence != 855 B'

# tilemap sentence from the C++ raw string literal
cpp = open(CPP, 'rb').read().decode('utf-8')
m = re.search(r'editor_set_tilemap_cell", String::utf8\(R"desc\((.*?)\)desc"\)\)', cpp, re.S)
assert m, 'tilemap C++ literal not found'
cell_full = m.group(1)
ORIG_CELL = '设置瓦片地图单元格'
assert cell_full.startswith(ORIG_CELL + ' ')
assert len(cell_full.encode('utf-8')) == 717, 'cell full != 717 B'
TILE_SENT = cell_full[len(ORIG_CELL) + 1:]
assert len(TILE_SENT.encode('utf-8')) == 689, 'tilemap sentence != 689 B'

m2 = re.search(r'editor_set_tilemap_cells_in_rect", String::utf8\(R"desc\((.*?)\)desc"\)\)', cpp, re.S)
rect_full = m2.group(1)
ORIG_RECT = '填充瓦片地图矩形区域'
assert rect_full == ORIG_RECT + ' ' + TILE_SENT, 'rect literal is not ORIG + shared sentence'
assert len(rect_full.encode('utf-8')) == 720, 'rect full != 720 B'

w('recovered: SCENE_TREE_ADDRESSABILITY_SENTENCE=%d B  TILEMAP_ATLAS_GAP_SENTENCE=%d B'
  % (len(SCENE_SENT.encode('utf-8')), len(TILE_SENT.encode('utf-8'))))
w('  scene full=898 B, cell full=717 B, rect full=720 B (all match REPORT-076 1.2)')

src = open(GEN, 'rb').read().decode('utf-8')
before_sha = sha(src.encode('utf-8'))
w('')
w('gen before: bytes=%d sha256=%s' % (len(src.encode('utf-8')), before_sha))

# ------------------------------------------------------- (a) drop the dup block
DUP_START = '    # TASK-024 E-10: the new optional `mcp_port` argument. A schema override\n'
DUP_END = '    # TASK-024a E-10: the new optional `mcp_port` argument.'
i = src.find(DUP_START)
j = src.find(DUP_END)
assert i != -1 and j != -1 and i < j, 'duplicate play_scene anchors not found'
removed = src[i:j]
assert removed.count('"play_scene": {') == 1, 'the removed span must contain exactly one play_scene key'
new = src[:i] + src[j:]
w('')
w('(a) removed %d bytes (%d lines) = the FIRST `play_scene` schema block (dead: the later key wins)'
  % (len(removed.encode('utf-8')), removed.count('\n')))

# ------------------------------------------------- (b) add the three records
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
    %(tile)r
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

anchor = 'DESCRIPTION_OVERRIDES = {\n'
assert new.count(anchor) == 1, 'DESCRIPTION_OVERRIDES anchor not unique'
new = new.replace(anchor, literals_block + anchor, 1)
w('(b1) inserted the two sentence literals + _T076_TILEMAP_GAP_REASON before DESCRIPTION_OVERRIDES')

ENTRIES = '''    # v1.22 (TASK-076 section A.1): the two boundaries TASK-075's D4/D5 measured
    # and REPORT-076 section 1 implemented.  All three records are append-only
    # (`mode` stays the default), so the original wording stays first and
    # verbatim; the `startswith(<original> + " ")` guard above enforces that.
    "get_scene_tree": {
        "reason": (
            "TASK-076 §A.1 / REPORT-076 §1.3(i)，依据 REPORT-075 §5 D4 的最小复现"
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
assert new.count(close_anchor) == 1, 'DESCRIPTION_OVERRIDES close anchor not unique'
new = new.replace(close_anchor, '    },\n' + entries_block + '# v1.5: a schema override replaces the whole `inputSchema` object', 1)
w('(b2) appended the three DESCRIPTION_OVERRIDES records')

# ------------------------------------------------------------------- validate
compile(new, GEN, 'exec')
ast.parse(new)
tree = ast.parse(new)
seen = {}
for node in tree.body:
    if isinstance(node, ast.Assign):
        for tgt in node.targets:
            if isinstance(tgt, ast.Name) and tgt.id.endswith('OVERRIDES'):
                raw = [k.value for k in node.value.keys if isinstance(k, ast.Constant)]
                dup = [x for x in set(raw) if raw.count(x) > 1]
                seen[tgt.id] = (len(raw), len(set(raw)), dup)
                w('  %s: raw=%d distinct=%d dups=%s' % (tgt.id, len(raw), len(set(raw)), dup or 'NONE'))
                assert not dup, 'duplicate key survives'
assert 'play_scene' not in seen['SCHEMA_OVERRIDES'][2]

data = open(GEN, 'wb').read() if False else None
with open(GEN, 'wb') as fh:
    fh.write(new.encode('utf-8'))
after = open(GEN, 'rb').read()
w('')
w('gen after : bytes=%d sha256=%s' % (len(after), sha(after)))
w('delta bytes=%d' % (len(after) - len(src.encode('utf-8'))))
w('CR count after=%d (must be 0)' % after.count(b'\r'))

open(LOG, 'w', encoding='utf-8').write('\n'.join(log))
print('OK ->', LOG)
