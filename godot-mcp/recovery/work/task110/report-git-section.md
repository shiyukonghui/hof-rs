
---

## G. 提交后的两仓逐字复核

**边界说明**：本节是 TASK-110 主仓提交 `5f66cb2` **之后**那一刻的两仓状态；此后若再有纯文档追加（包括携带本节的那次），只会让主仓 `git log` 顶部多出文档提交，不会改变下面两组事实（引擎仓 HEAD/远端、主仓已跟踪改动为 0）。

### G1. 引擎仓（`F:\moonbit-hof-rs\godot-mcp\godot`，分支 `feature/mcp-server-module-rebuild`）

```
$ git log --oneline -3
3fdabe2d9a fix(godot-mcp): TASK-110 - editor_list_signal_connections' registered schema regains `scope`, the one member that made the TASK-051 narrowing unreachable
1f9d0cb1c9 modules/mcp_server: task103 - REBUILT-2C-MANIFEST gains the 2c-12 section: ...
1c7f5c07a1 modules/mcp_server: task103 (X-1) - ...

$ git status --short
(空)

$ git rev-parse HEAD origin/feature/mcp-server-module-rebuild
3fdabe2d9af5b482dc95ccb00ce63a0943601991
3fdabe2d9af5b482dc95ccb00ce63a0943601991
```

push 的真实输出（`git push origin feature/mcp-server-module-rebuild`）：

```
To github.com:shiyukonghui/godot.git
   1f9d0cb1c9..3fdabe2d9a  feature/mcp-server-module-rebuild -> feature/mcp-server-module-rebuild
```

即：**模块改动已提交并已 push，工作树干净，HEAD 与远端逐位相同。**

### G2. 主仓（`F:\moonbit-hof-rs`，分支 `master`）

```
$ git log --oneline -2
5f66cb2 feat(godot-mcp): TASK-110 - the coverage loop's first batch: ...
d5e9240 TASK-109: 20 C# games exported as runnable Windows exe + 2-part package (D154)

$ git status --short
 M godot-mcp/recovery/work/task104/logs/git-housekeeping.err.txt
 M godot-mcp/recovery/work/task104/logs/git-housekeeping.out.txt
?? godot-mcp/dist/
?? godot-mcp/recovery/reports/ACCEPTANCE-TASK-107.md
```

**这 4 条都不是本任务产生的**，本任务**没有**把它们纳入提交：两条 `task104` 日志是 TASK-104 收尾提交时的既有工作树状态，`dist/` 与 `ACCEPTANCE-TASK-107.md` 是 TASK-107/109 的产物。本任务自己的产物**全部已入库**（180 文件 / +29 771 行），`runs/` 按 `.gitignore` 第 43 行的既有政策不入库。

### G3. 跑后的进程与端口检查（铁律 4）

```
$ netstat -ano | findstr 9888 9889 9877     ->  NO_LISTENERS   （无任何监听者）
$ tasklist  | findstr /I godot              ->  NO_GODOT_PROC  （无残留引擎进程）
```

本轮 5 次运行（smoke / c1 / c1b / c1c / c23 / c23-after）全部用同一对端口 **9888 / 9889**，每次跑前都先确认这两端口无监听、无 `godot` 进程；用户端口 **9877** 全程未被占用（`g04` 的 `guard_user_port_9877` 也在门里独立核过）。
