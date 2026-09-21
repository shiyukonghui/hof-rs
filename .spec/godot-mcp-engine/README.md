# 已迁移：引擎内置 MCP 模块的规范工件

**本目录的引擎侧规范工件已搬到 Godot fork 仓库，与代码同居**（用户裁决，见 `DECISIONS.md` D40）：

```
F:\RustProjects\godot-mcp-pro\code\godot\modules\mcp_server\
  README.md                模块说明、构建/测试命令、状态
  docs\REQUIREMENTS.md     目标、约束、假设、里程碑
  docs\DESIGN-OVERVIEW.md  架构分层、被否决的备选、风险
  docs\DESIGN-DETAIL.md    GDR-1..GDR-15 规范性条款、M1 范围与验收用例、工具批次、hof-rs 集成契约
  docs\ACCEPTANCE.md       M0 / M1 独立验收记录（含未验证边界与已知偏差）
```

## 为什么这样分

| 内容 | 位置 | 理由 |
|---|---|---|
| 引擎模块的规范与验收工件 | **fork `modules/mcp_server/docs/`** | 与代码同居，fork 内自洽；改代码与改规范在同一提交里可见 |
| 跨项目决策日志 `DECISIONS.md` | **本仓库（hof-rs）** | 记录的是 hof-rs 与引擎模块**共同**的决策树（D30 起为引擎方向、D35–D39 为 M1 实现/验收裁决），拆开会让「为什么长这样」失去单一来源 |
| 命名工件（`tool-rename-map.json`、`TOOL-NAMING.md`） | **fork `modules/mcp_server/docs/`** | 与工具实现同居；生成与消费都在引擎侧 |

> 本目录保留一个存根是为了让 `DECISIONS.md` 里的历史路径引用仍然可解析；
> 目录内若短暂出现命名工件（生成中），完成后会一并搬到 fork。
