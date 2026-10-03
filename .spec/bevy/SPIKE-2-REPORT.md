# SPIKE-2 报告：Bevy 0.19.1 在无显示 / 无 GPU 环境下的可行性与代价

- 日期：2026-10-03
- 执行者：spike 子代理（无先验上下文，单人执行，不委派实现）
- 上游依据：`.spec/bevy/SPIKE-1-REPORT.md`（BRP 动词面 / 构建预算 / 观测面强加）、
  `.spec/bevy/REQUIREMENTS.md` §4.5、§5-A2、§9（用户要求「现在就补 spike」）
- 回答的问题：(1) 无显示无 GPU 能否跑起来、确切 feature 与配置是什么；(2) BRP 在 headless 下
  哪些端点存在、`rpc.discover` 返回什么、「钉死 15702」是否还成立；(3) 五个观测是否仍成立；
  (4) headless 的构建/启动代价；(5) 需求该承诺、延后还是排除 headless。
- 本仓库改动：**只新增本文件**。仓内 `Cargo.toml`、`Cargo.lock`、`src/**`、`tests/**`、
  `DECISIONS.md`、`.spec/hof-rs/**`、`runs/**`、冻结规范、任何 workspace 目录 **一字未改**
  （证据见 §C.0）。所有构建、脚本、探测输出都在仓外 `F:\bevy-spike2\`。
- 证据文件（仓外，可复跑）：`F:\bevy-spike2\py\*.py`（全部脚本）、`out\*.json`（全部探测结果）、
  `out\*_stdout.log`（游戏进程 stdout）、`ws_render\`、`ws_norender\`（两个 workspace）、
  `target-render\`、`target-norender\`（两个 target 目录）、`build_timed.sh`。

> **English TL;DR (for skimming)**
> 1. **Yes, Bevy 0.19.1 runs with no window and no GPU adapter.** Verified with three independent
>    levers: (a) `RenderPlugin { render_creation: WgpuSettings { backends: None, .. } }` — this makes
>    `RenderPlugin` *not create a render world at all* (`bevy_render/src/settings.rs:270-273` returns
>    `false` from `create_render`, so `ExtractPlugin` is never added); (b) `WinitPlugin` disabled
>    (or `primary_window: None`); (c) optional `default-features = false`. Poisoning wgpu
>    (`WGPU_BACKEND=zzz` → empty backend set) kills the windowed/GPU configs with exit code **101**
>    (`Unable to find a GPU!` at `bevy_render/src/renderer/mod.rs:286`) while the headless configs
>    run normally — that is the controlled proof of GPU independence.
> 2. **A headless app must be given a runner, or it exits after exactly one frame.** Without
>    `ScheduleRunnerPlugin` the process exits with **code 0** and the BRP endpoint never answers
>    (measured, C7).
> 3. **Endpoint topology: 15703 exists iff a render world exists.** With `backends: None` there is no
>    render world, so **only 15702 is opened**; the same happens with `default-features = false`.
>    With `primary_window: None` but a real adapter, **both** ports still open. `rpc.discover` reports
>    **23 methods and `servers: 127.0.0.1:15702` in every configuration**.
>    **Our "pin 15702, ignore 15703" rule survives headless unchanged** — 15702 always exists. What
>    must become conditional is any statement about 15703 *existing*.
> 4. **All five observations still work headless** (movement, counter transition, win flag, rise-then-fall
>    jump arc, readable `Grounded`) — in the no-GPU and no-render configs, measured with the same probe
>    and the same type paths. The one configuration where the jump arc **fails** is the *windowed* one,
>    at **4.0 FPS** on this machine.
> 5. **Cost:** headless is *faster* everywhere. Cold build 302 s → **251 s** (`default-features = false`;
>    only −17 %, because `bevy_remote` unconditionally depends on `bevy_dev_tools`, which pulls the whole
>    render stack); warm 16–19 s → **12 s**; start-to-endpoint 2755 ms → **620 ms** (4.4×); exe
>    178.1 MiB → **57.5 MiB**; loaded modules 106 → **10** (and **zero** display/GPU DLLs).
> 6. **Recommendation: promise headless now, as a runtime switch on the same binary** (measured, C6):
>    windowed on a dev box, windowless + GPU-free on CI, one artifact, one source. Cost: three
>    conditional plugin choices in `main()` plus a schedule runner. The PRD must additionally state
>    that in headless mode there is **no render world** (so no 15703, no screenshots) and that game
>    semantics must not live in render-side components.
> 7. **New contract hazard discovered:** a JSON-RPC **batch is not frame-atomic** — one batch of 24
>    identical `world.get_resources` calls came back with two different values (`coins: 1` and
>    `coins: 2`) in the same response (C4, 1 of 6 batches). Never use a batch as a consistent snapshot.

---

## 0. 裁决（先看这段）

### 0.1 一句话裁决

**headless 不是「能不能」的问题，而是「要哪一种」的问题。** 实测存在三种真正可用的无窗口配置，
它们的差别只有一个：**是否存在渲染世界（RenderApp）**。

| 编号 | 配置 | 需要窗口 | 需要 GPU 适配器 | 渲染世界 / 15703 | 能否截图 |
|---|---|---|---|---|---|
| **C1** | `DefaultPlugins`（对照） | 是 | **是** | 有 / **有** | 是（SPIKE-1 已验证） |
| **C2** | `primary_window: None`，保留 winit | 否（0 个窗口） | **是** | 有 / **有** | 是 |
| **C3** | 无窗口 + 关 `WinitPlugin` + `backends: None` | 否（**0 个窗口**） | **否** | **无** / **无** | **否** |
| **C4** | `bevy` 开 `default-features = false` | 否（**0 个窗口**） | **否** | **无** / **无** | **否** |
| C5 | C1 + `WinitSettings::continuous()`（诊断用） | 是 | 是 | 有 / 有 | 是 |
| **C6** | **同一二进制，启动时按 `SPIKE2_HEADLESS` 在 C1 / C3 之间切换** | 可选 | 可选 | 随模式 | 仅窗口模式 |
| C7 | C3 但不加 `ScheduleRunnerPlugin`（负例） | 否 | 否 | 无 / 无 | 否（**跑一帧就退出**） |

### 0.2 五问逐条回答

| 问题 | 答案 |
|---|---|
| **Q1 无显示无 GPU 能否跑** | **能**。C3/C4 在 `WGPU_BACKEND=zzz`（无可用后端）下照常运行；C1/C2 在同一环境下以退出码 **101** 崩溃。C3/C4 的进程**零窗口**、模块表里没有 `vulkan-1/dxgi/d3d12/opengl32`（C4 连 `user32.dll` 都没有）。**必须**给 runner，否则跑一帧退出（C7 实测退出码 0）。 |
| **Q2 BRP headless 与端点** | 四种配置的 `rpc.discover` 都是 **23 个方法**、`info.version = 0.19.1`、`servers = [127.0.0.1:15702]`。**15703 当且仅当存在渲染世界时存在**：C1 ✅、C2 ✅、C3 ❌、C4 ❌。**「钉死 15702」这条规则在 headless 下不需要改**（15702 恒在）；需要改成条件式的是「15703 存在」这个描述。 |
| **Q3 五个观测** | **C2/C3/C4 全部通过**（含最能出问题的跳跃弧线与 `Grounded`）。**唯一失败的是 C1（窗口模式）**，因为它在这台机器上只有 **4.0 FPS**，跳跃弧线只采到 6 个点（rise=0 / fall=2）。 |
| **Q4 代价** | headless **全面更快**：冷构建 251 s（−17 %）、暖构建 12 s（−33 %）、启动→端点 620 ms（−77 %）、exe 57.5 MiB（−68 %）、加载模块 10（−90 %）。代价是**没有渲染世界**（无 15703、无截图），且**源码里不能依赖 render 类型**（C4）。 |
| **Q5 建议** | **现在就承诺 headless**，但用 **C6 形态**（同一二进制 + 运行时开关）而不是两个产物；契约里把它定义为「无窗口、无 GPU 适配器、无渲染世界」的一种运行模式。详见 §5。 |

### 0.3 对 `REQUIREMENTS.md` 两条待裁决项的落地

`REQUIREMENTS.md` §9 把两条规则标为「待 SPIKE-2 裁决」。裁决如下：

1. **§4.5「固定 15702（主世界），不使用 15703」——保留，且不需要改写为条件式**。
   理由是 **15702 在所有四种配置里都存在且语义相同**（主世界、23 个方法、同一套类型路径）。
   headless 只是让 15703 *消失*，而我们的规则本来就是「不用它」。
   **建议补一句**（不是替换）：「15703 仅在存在渲染世界时存在；适配器在任何配置下都不得依赖其存在，
   也不得把 15703 的缺失当作错误。」
2. **§5 A2「运行环境有 GPU、能开窗口」——可以删掉，但必须换成更精确的两条**：
   - 「游戏必须能在**无窗口 + 无 GPU 适配器**的配置下运行并接受 BRP 请求」（C3 或 C6-B 形态，实测可行）；
   - 「该配置下**没有渲染世界**，因此没有 15703、没有截图；任何需要渲染世界的判据必须在契约里显式声明为
     『仅窗口模式可用』」。

### 0.4 三个必须写进契约的新事实（SPIKE-1 没有的）

1. **`WgpuSettings { backends: None }` 的语义比名字更彻底**：它不是「空渲染世界」，而是**根本不创建渲染世界**。
   源码：`bevy_render-0.19.1/src/settings.rs:270-273`（`let Some(backends) = render_creation.backends else { return false }`）
   → `bevy_render-0.19.1/src/lib.rs:359-365`（只有返回 true 才 `add_plugins(ExtractPlugin)`）。
   没有 `ExtractPlugin` 就没有 `RenderApp` 子应用，于是
   `bevy_remote-0.19.1/src/http.rs:146`（`let Some(render_app) = app.get_sub_app_mut(RenderApp) else { return }`）
   直接返回 → 15703 不开。**这条推理链同时被源码和 C3 的实测（`15703 tcp_open=false`）证实。**
2. **没有 runner 的 headless app 跑一帧就退出**（退出码 0，端点从未应答）。必须
   `ScheduleRunnerPlugin::run_loop(1/60)`；Bevy 自己的 `examples/app/without_winit.rs` 也这么写。
3. **JSON-RPC batch 不是帧原子的**。契约里禁止用 batch 做「一致性快照」。

---

## 1. （Q1）无显示、无 GPU 到底能不能跑

### 1.1 需要的确切 feature / 配置（两条路线，都已实测编译并运行）

**路线 A —— 保留渲染特性，运行时切换到 headless（推荐，对应 C3/C6-B）**

依赖行与 SPIKE-1 的普通工程**完全相同**，不需要改 `Cargo.toml`：

```toml
bevy = { version = "0.19.1", features = ["bevy_remote"] }
```

`main()` 里的 headless 分支（逐字可编译，实测通过）：

```rust
use bevy::app::ScheduleRunnerPlugin;
use bevy::prelude::*;
use bevy::remote::{RemotePlugin, http::RemoteHttpPlugin};
use bevy::render::{RenderPlugin, settings::WgpuSettings};
use bevy::window::ExitCondition;
use bevy::winit::WinitPlugin;
use std::time::Duration;

let headless = /* 例如 env::var("GAME_HEADLESS").is_ok() */;

let mut window_plugin = WindowPlugin::default();
let render_plugin = if headless {
    window_plugin.primary_window = None;
    window_plugin.exit_condition = ExitCondition::DontExit;
    window_plugin.close_when_requested = false;
    RenderPlugin { render_creation: WgpuSettings { backends: None, ..default() }.into(), ..default() }
} else {
    RenderPlugin::default()
};

let builder = DefaultPlugins.set(window_plugin).set(render_plugin);
if headless {
    app.add_plugins(builder.build().disable::<WinitPlugin>());
    app.add_plugins(ScheduleRunnerPlugin::run_loop(Duration::from_secs_f64(1.0 / 60.0)));
} else {
    app.add_plugins(builder);
}
```

这一路线的价值：**同一份游戏源码既能开窗渲染，也能无 GPU 跑**。`Sprite` / `Camera2d` 仍然写得出、
仍然编译得进，只是在 headless 下成为惰性数据。**实测（C6）**：不带环境变量 → 1 个真窗口 + 15703；
带 `SPIKE2_HEADLESS=1` → **0 个窗口** + **无 15703** + 启动 1672 ms（vs 3119 ms）+ 跳跃弧线可用。

**路线 B —— 连窗口/渲染特性都从依赖图里去掉（对应 C4）**

```toml
bevy = { version = "0.19.1", default-features = false,
         features = ["std", "multi_threaded", "bevy_remote", "default_app"] }
```

```rust
// bevy_window 关闭 ⇒ DefaultPlugins 自带 ScheduleRunnerPlugin（default_plugins.rs:19-20），
// 但仍然建议显式 set，以免将来 feature 漂移
app.add_plugins(DefaultPlugins.set(ScheduleRunnerPlugin::run_loop(Duration::from_secs_f64(1.0/60.0))));
```

- `default_app` 是 Bevy 0.19.1 官方定义的「无渲染基线」特性集合
  （`bevy-0.19.1/Cargo.toml.orig:172-179`：`async_executor` / `bevy_asset` / `bevy_log` /
  `bevy_state` / `reflect_auto_register`）。
- 这一路线下 **`bevy_winit` 与 `winit` 完全不在依赖图里**（实测 `cargo tree`：`winit` = false），
  进程只加载 **10 个模块**、**没有任何显示/GPU DLL**。
- **代价**：`Sprite` / `Camera2d` / `Window` 这些类型**不存在**，游戏源码**编译不过**（不是运行时问题）。
  所以路线 B 只适合「CI 专用产物」或「游戏状态机完全不碰渲染类型」的写法。

**不需要软件适配器**。C3/C4 都不向 wgpu 请求 adapter，因此 llvmpipe / WARP / `force_fallback_adapter`
全都不需要（这一条与「有渲染世界但机器没 GPU」是两回事——后者本 spike **没有**测，见 §6-3）。

### 1.2 实测：退出码、存活、事件循环

| 编号 | 命令（工作目录 `F:\bevy-spike2`） | 退出码 | 结果 |
|---|---|---|---|
| 1 | `bash build_timed.sh ws_render target-render build -p c1_windowed` | **0** | 冷构建 302 s |
| 2 | `bash build_timed.sh ws_norender target-norender build -p c4_norender` | **0** | 冷构建 251 s |
| 3 | `python py/probe.py target-render/debug/c3_nogpu.exe …` | **0** | 存活；端点 1701 ms；**0 窗口**；15703 不存在 |
| 4 | `python py/probe.py target-norender/debug/c4_norender.exe …` | **0** | 存活；端点 591 ms；**0 窗口**；15703 不存在 |
| 5 | `python py/probe.py target-render/debug/c7_norunner.exe …`（经管道，脚本自身退出码未单独捕获） | —（**子进程 rc=0**） | 游戏进程 **提前退出，rc=0**，`ready_ms=None` → **跑一帧就退出，端点从未应答** |
| 6 | `WGPU_BACKEND=zzz python py/probe.py …c1_windowed.exe…` | **0** | 子进程 **rc=101**（panic） |
| 7 | `WGPU_BACKEND=zzz python py/probe.py …c2_windowless.exe…` | **0** | 子进程 **rc=101** |
| 8 | `WGPU_BACKEND=zzz python py/probe.py …c3_nogpu.exe…` | **0** | 正常存活、端点 1693 ms |
| 9 | `WGPU_BACKEND=zzz python py/probe.py …c4_norender.exe…` | **0** | 正常存活、端点 586 ms |
| 10 | `python py/modules.py …`（C1 / C3 / C4） | **0** | 模块数 106 / 50 / 10 |
| 11 | `python py/fps.py …`（C1 / C2 / C3 / C4 / C5） | **0** | 4.0 / 60.3 / 59.0 / 59.0 / **4.0** FPS |

**「事件循环」的确切答案**：headless 下 **没有 winit 事件循环**（C3 关了插件、C4 连 `winit` crate
都不在依赖图里），存活靠的是 `ScheduleRunnerPlugin` 的循环——它是一个 `loop { run_frame(); sleep(1/60) }`。
**不给它就立刻退出**（C7：rc=0，一帧之后进程结束，BRP 端点从未绑定）。

### 1.3 GPU 依赖的对照实验（这是「无 GPU」的硬证据）

本机有 RTX 4090，无法物理拔掉。所以用了受控的「毒化」实验：

- `wgpu-types-29.0.4/src/backend.rs:182-204`：`Backends::from_env()` 读 `WGPU_BACKEND`，
  **无法识别的字符串会被忽略并返回空后端集**；而 `WgpuSettings::default()` 是
  `Some(Backends::from_env().unwrap_or(default_backends))`（`bevy_render/src/settings.rs:84`）。
- 因此 `WGPU_BACKEND=zzz` ⇒ 后端集为空 ⇒ wgpu 找不到任何 adapter ⇒
  `bevy_render/src/renderer/mod.rs:286` 的 `expect(GPU_NOT_FOUND_ERROR_MESSAGE)` 触发 panic。

实测（同一台机器、同一时刻、同一批二进制）：

```
$ WGPU_BACKEND=zzz python py/probe.py target-render/debug/c1_windowed.exe ...
[19:50:04] process EXITED EARLY rc=101
$ tail -c 400 out/poison-c1_windowed_stdout.log
thread 'main' (15296) panicked at ...\bevy_render-0.19.1\src\renderer\mod.rs:286:36:
Unable to find a GPU! Make sure you have installed required drivers!

$ WGPU_BACKEND=zzz python py/probe.py target-render/debug/c3_nogpu.exe ...
[19:50:07] endpoint 15702 ready after 1693.1 ms (4 polls)
[19:50:07] windows: []
[19:50:07] 15702 methods=23 ; 15703 tcp_open=False

$ WGPU_BACKEND=zzz python py/probe.py target-norender/debug/c4_norender.exe ...
[19:50:09] endpoint 15702 ready after 586.2 ms (2 polls)
```

结论：**C3/C4 完全不需要 GPU 适配器；C1/C2 需要**。这是同一台机器上的受控对照，不是推断。

### 1.4 「无显示」的证据与它的边界

| 证据 | C1 | C2 | C3 | C4 |
|---|---|---|---|---|
| `EnumWindows` 找到的该进程窗口 | `c1_windowed`(真窗口) + winit 消息窗 + IME | 只有 winit 消息窗 + IME | **无** | **无** |
| 加载模块数 | 106 | 未测 | 50 | **10** |
| 模块里的显示/GPU DLL | `user32, GDI32, vulkan-1, dxgi, dxcore, nvoglv64, d3d12, opengl32` | 未测 | `user32, GDI32` | **（一个都没有）** |
| `winit` 是否在依赖图 | 是 | 是 | 编译进链接但 `WinitPlugin` 被 disable | **否**（`cargo tree` 证实） |

**边界（诚实）**：本机始终有桌面会话（Windows 11 Pro，有显示器）。我**没有**在 session 0 /
无桌面的 Windows 服务 / 无 X11 的 Linux 容器里跑过。因此「C3/C4 不调用 winit」是**结构性证据**
（`winit` 不在 C4 的依赖图里；C3 把它 disable 了），不是「在无显示环境里跑过」的**实测证据**。
这一条列入 §6-1。

---

## 2. （Q2）BRP 在 headless 下与端点拓扑

### 2.1 四种配置的 `rpc.discover`（活体实测）

| 配置 | 15702 方法数 | `info.version` | `servers` | 15703 `tcp_open` | 15703 方法数 |
|---|---|---|---|---|---|
| C1 窗口+GPU | **23** | 0.19.1 | `[{name:Server, url:127.0.0.1:15702}]` | **true** | 23（`servers.url = 127.0.0.1:15703`） |
| C2 无窗+GPU | **23** | 0.19.1 | 同上 | **true** | 23 |
| C3 无窗+无 GPU（`backends: None`） | **23** | 0.19.1 | 同上 | **false** | — |
| C4 `default-features = false` | **23** | 0.19.1 | 同上 | **false** | — |
| C6-A 同二进制·窗口模式 | 23 | 0.19.1 | 同上 | **true** | 23 |
| C6-B 同二进制·headless 模式 | 23 | 0.19.1 | 同上 | **false** | — |
| 毒化 C1 / C2 | —（进程 panic，rc=101） | — | — | — | — |
| 毒化 C3 / C4 | 23 | 0.19.1 | 同上 | false | — |

→ **主世界端点在每种配置里都是同一套 23 个方法**（与 SPIKE-1 的动词表逐字相同，没有因为
headless 而少任何一个动词）。`rpc.discover` 里 `servers` 报的是**该端点自己的端口**，这一点在
headless 下也一样（15702 报 15702）。

### 2.2 为什么 15703 会消失：源码级因果链（可复核）

```
bevy_render-0.19.1/src/settings.rs:270-273
    RenderCreation::Automatic(rc) => { let Some(backends) = rc.backends else { return false }; … }
bevy_render-0.19.1/src/lib.rs:359-365
    if insert_future_resources(&self.render_creation, app.world_mut()) {
        // We only create the render world and set up extraction if we have a rendering backend available.
        app.add_plugins(ExtractPlugin { … });
    };
bevy_remote-0.19.1/src/http.rs:142-160
    #[cfg(feature = "bevy_render")]
    { let Some(render_app) = app.get_sub_app_mut(RenderApp) else { return; };
      render_app.insert_resource(HostPort(self.render_port)) … }
```

即：**`backends: None` ⇒ 不建 RenderApp ⇒ 不注册渲染端点的 HTTP server ⇒ 15703 不存在**。
`bevy_remote` 自己的 `bevy_render` cargo feature 在 `bevy_internal` 里是**无条件打开**的
（`bevy_internal-0.19.1/Cargo.toml.orig:557-560`），所以 C4 那种「无渲染特性」的构建里这段代码
**照样编译进去**，只是因为拿不到 `RenderApp` 而提前 return。

### 2.3 规则裁决

> **原文**（`REQUIREMENTS.md` §4.5）：「固定 15702（主世界），不使用 15703」

**结论：这条规则原样保留，不需要条件式。** 依据：
1. 15702 在**全部**配置中恒存在（含毒化后的 C3/C4）；
2. 它的方法集、类型路径、错误码在 headless 下**没有任何变化**；
3. 15703 在 headless 下不存在，而规则本来就是「不碰它」——不碰一个不存在的端口与不碰一个存在的端口，
   对适配器是同一件事。

**唯一需要修改的是对 15703 的「描述性文字」**（若契约里写了「会开两个端口」）。建议措辞：

> 主世界端点恒为 `127.0.0.1:15702`。渲染世界端点 `127.0.0.1:15703` **仅在存在渲染世界时**存在
> （即 `RenderPlugin` 带着可用 wgpu 后端运行时）。适配器不得依赖 15703 的存在性，也不得把它的缺失
> 当作错误；任何需要 15703 的能力必须在契约中显式标注为「仅窗口模式」。

---

## 3. （Q3）五个观测在 headless 下是否仍然成立

### 3.1 结果总表

| 观测 | C1 窗口 | C2 无窗+GPU | C3 无窗+无GPU | C4 无无渲染 | C6-B 同二进制 headless |
|---|---|---|---|---|---|
| ① 注入输入后玩家位移 | ✅ 但 30 px/帧（4 FPS） | ✅ 0→120.0（0.42 s） | ✅ 0→116.4 | ✅ 0→93.7 | ✅ 0→111.9 |
| ② 计数跳变 | **未能分辨**（见 §3.4） | ✅ **0→1** | ✅ **0→1** | ✅ **0→1** | ✅（探针里 1→2） |
| ③ 胜利位 false→true | ✅（探针里已为 true） | ✅ **false→true** | ✅ **false→true** | ✅ **false→true** | ✅ |
| ④ 跳跃先升后降 | ❌ **rise=0 / fall=2** | ✅ **rise=12 / fall=13** | ✅ **rise=12 / fall=12** | ✅ **rise=16 / fall=18** | ✅ rise=11 / fall=13 |
| ⑤ 起跳前可读 `Grounded` | ✅ `{on_ground: true}` | ✅ | ✅ | ✅ | ✅（落地后仍为 true） |

「② 计数跳变」与「③ 胜利位」的权威证据来自 `py/transition.py`：先用 BRP 把状态**拨到已知值**
（`CoinCounter.coins = 0`、`CoinCounter.target = 1`、`WinFlag.won = false`、玩家 `translation.x = -350`），
再注入 `move_x = 1.0`，然后用**单次 batch** 同时读 counter / win / transform，直到 `won == true`。

C3 的原始时间线（`out/transition-c3_nogpu.json::timeline_tail`）：

```json
[{"ms":136.7,"x":-333.59,"coins":{"coins":0,"target":1},"win":{"won":false}},
 {"ms":221.8,"x":-323.37,"coins":{"coins":0,"target":1},"win":{"won":false}},
 {"ms":306.8,"x":-313.19,"coins":{"coins":1,"target":1},"win":{"won":true}}]
```

C2 / C3 / C4 都拿到了同形状的 **`coins 0,0,0 → 1`** 与 **`win false,false,false → true`**，
而且是在**同一行**（同一次 batch）里同时发生的。

### 3.2 跳跃弧线（最可能出问题的一条，实测没出问题）

```
C3（无窗 + 无 GPU 适配器）samples=26  rise=12  fall=12  start=-193.06  peak=-105.66 (441.5 ms)  end=-200.00
   [16.9,-193.06] [51.1,-180.04] [101.4,-162.75] [152.5,-147.58] [186.8,-138.70] [203.2,-134.73]
   [236.9,-127.52] [254.1,-124.26] [305.2,-116.03] [339.4,-111.89] [373.5,-108.76] [407.4,-106.68]
   [441.5,-105.66] [492.3,-106.07] … → -200.00

C4（default-features = false）samples=36  rise=16  fall=18  start=-193.11  peak=-105.53 (458.4 ms)  end=-200.00

C2（无窗 + 真 GPU 适配器）samples=27  rise=12  fall=13  start=-186.72  peak=-105.50 (466.8 ms)  end=-200.00
```

峰值都在 −105.5 附近、地面 −200.0、上升段与下降段都 > 0 —— 与 SPIKE-1 窗口模式的
（峰值 −103.5、地面 −200.0、15 升 + 15 降）**在容差内一致**。

### 3.3 `Grounded` 语义在 headless 下依然可读

- 起跳前：`spike2_core::game::Grounded { on_ground: true }`，四种配置全部为真；
- 落地后：仍为 `{ on_ground: true }`；
- 它完全由游戏的 `physics` 系统维护，与渲染世界无关 —— 这也说明「接地语义」**不需要渲染**，
  但**必须由游戏暴露**（与 SPIKE-1 的结论一致）。

### 3.4 唯一失败的一条：**窗口模式的 4 FPS**（这条比 headless 更值得注意）

在**所有**窗口配置（C1、C5、C6-A）上实测：

```
$ python py/fps.py target-render/debug/c1_windowed.exe --tag c1
  "watch_seconds": 3.0, "watch_frames": 12, "watch_fps": 4.0
$ python py/fps.py … c2_windowless.exe      → 60.33 FPS
$ python py/fps.py … c3_nogpu.exe           → 59.0  FPS
$ python py/fps.py … c4_norender.exe        → 59.0  FPS
$ python py/fps.py … c5_winit_continuous.exe→  4.0  FPS   ← WinitSettings::continuous() 无效
```

- 请求往返时间同样分裂：C1 **259.5 ms**（n=25，248.6–267.1）vs C2 **23.9 ms** / C3 **20.9 ms** / C4 **18.3 ms**。
- C1 的移动采样是 `30.0, 60.0, 90.0, …`（严格每帧 30 px = 0.25 s × 120 px/s）——
  这正是 Bevy `Time<Virtual>` 的 `max_delta`（250 ms）被**截断**的痕迹，说明真实帧周期 ≥ 250 ms。
- C5 用 `WinitSettings::continuous()` 得到**同样的 4.0 FPS**（`bevy_winit/src/winit_config.rs:13-59`
  的四种模式都试不掉），所以**不是** winit 的更新策略；最可能是窗口被终端遮挡后
  合成器/驱动对 `present()` 的节流（**未进一步隔离，见 §6-6**）。
- 后果：**窗口模式下 4 Hz 的采样根本分辨不出 40 ms 的计数跳变**（C1 与 C6-A 的 ② 都因此「未能分辨」），
  跳跃弧线只剩 6 个点（`rise=0 / fall=2`），**E3-④ 会红**。

> 这一条对产品决策很重要：**「有 GPU、能开窗口」并不等于「能观测」**。SPIKE-1 在窗口模式下
> 测到 ~25–50 Hz 采样，很可能是那次窗口恰好在前台；本 spike 的窗口在终端后面，直接掉到 4 Hz。
> 也就是说，即使机器有 GPU，**窗口模式也是不可靠的观测面**，而 headless（C2/C3/C4）稳定在
> 59–60 FPS 且与窗口是否可见无关。

---

## 4. （Q4）headless 的代价：构建、启动、体积、模块

### 4.1 构建耗时（同机、同工具链、同 rsproxy 镜像，逐条实测）

| 指标 | C1–C3（默认特性 + `bevy_remote`） | C4（`default-features = false`） | 对比 |
|---|---|---|---|
| 冷 debug 构建（全新 target 目录） | **302 s**（cargo 自报 5m01s） | **251 s**（cargo 自报 4m10s） | **−17 %（−51 s）** |
| 暖构建（改 `spike2_core/src/game.rs` 一行注释 → 重建 lib + 二进制） | **16 s / 19 s**（两个样本） | **12 s** | **−33 %** |
| 暖构建（同 feature 集、新建另一个二进制 crate） | 17 s / 18 s / 21 s | — | 与 SPIKE-1 的 18 s 一致 |
| 依赖 crate 数（`cargo tree -e normal`，去重） | **346** | **286** | −60 |
| `Cargo.lock` 条目 / bevy 家族 | **567** / 67（全部 0.19.1） | **428** / 53 | −139 / −14 |

**与 SPIKE-1 的对比**：SPIKE-1 冷构建 **304 s**、暖 **18.28 s**、启动 **3104.7 ms**。
本 spike 的默认特性冷构建 **302 s**（复现一致，±1 %）；暖 **16–19 s**（一致）。
**headless（C4）把冷构建降到 251 s、暖降到 12 s。**

**为什么只省 17 %（重要）**：`bevy_remote` **无条件依赖 `bevy_dev_tools`**
（`bevy_remote-0.19.1/Cargo.toml.orig:28-30`），而 `bevy_dev_tools` 的默认特性把
`bevy_pbr` / `bevy_sprite_render` / `bevy_ui_render` / `bevy_core_pipeline` 全部拉了进来。
实测 `cargo tree -p c4_norender`：

```
C4 tree contains bevy_render        True
C4 tree contains wgpu               True
C4 tree contains naga               True
C4 tree contains bevy_pbr           True
C4 tree contains bevy_sprite_render True
C4 tree contains bevy_dev_tools     True
C4 tree contains bevy_window        True      ← 作为传递依赖被编译，但 bevy_internal 的 bevy_window feature 是关的
C4 tree contains bevy_winit         False
C4 tree contains winit              False
```

→ **只要开 BRP，就一定会编译整个渲染栈**（wgpu/naga/pbr）。这是「开观测面」的固定成本，
和 headless 与否无关。**能被 headless 省掉的只有 winit / 窗口 / 音频 / glTF / gizmos / UI 等外围。**

### 4.2 启动 → 远端端点可用（每配置 3 次，无并发负载，探测间隔 20 ms）

| 配置 | 样本（ms） | 均值 | 相对 C1 |
|---|---|---|---|
| C1 窗口+GPU | 3105.4 / 2937.3 / 2222.4 | **2755.0** | 1.00× |
| C2 无窗+GPU | 2329.3 / 2283.1 / 2255.7 | **2289.4** | 0.83× |
| C3 无窗+无 GPU | 1691.2 / 1654.7 / 1701.2 | **1682.4** | 0.61× |
| C4 `default-features=false` | 655.6 / 599.6 / 605.3 | **620.2** | **0.23×（4.4 倍快）** |
| C6-B 同二进制 headless | 1672.3（单次） | — | 0.61× |

对照 SPIKE-1：debug **3104.7 ms**、release **2249.4 ms**（5 次均值）。
→ C1 与 SPIKE-1 的 debug 基线同量级；**C4 比 SPIKE-1 的 release 还快 3.6 倍**。

### 4.3 体积与进程足迹

| 指标 | C1 / C2 / C3 / C5 / C6 | C4 |
|---|---|---|
| debug 可执行文件 | C1 186,760,192 / C2 186,770,944 / C3 186,783,232 / C5 186,764,800 B（均 **178.1 MiB**；C6 未单独量，同量级） | **60,328,960 B（57.5 MiB）**，−68 % |
| 进程加载模块数 | 106（C1）/ 50（C3） | **10** |
| 显示/GPU 相关 DLL | `user32, GDI32, vulkan-1, dxgi, dxcore, nvoglv64, d3d12, opengl32` | **无** |

（SPIKE-1 的对照：debug 186,567,680 B / release 95,541,248 B。）

### 4.4 构建预算建议（可直接抄进适配器契约）

| 条目 | SPIKE-1 建议 | SPIKE-2 修正建议 |
|---|---|---|
| 冷构建（无缓存，debug，含观测 feature） | ≤ 600 s | **保持 ≤ 600 s**（实测 302 s）；headless 专用产物实测 251 s |
| 暖构建（共享 target、feature 冻结、只改游戏源码） | ≤ 90 s | **保持 ≤ 90 s**（实测 16–19 s；headless 12 s） |
| 启动→端点就绪等待 | 轮询 20–50 ms，超时 30 s | **保持**；但按模式给期望值：窗口 ~2.8 s / 无窗有 GPU ~2.3 s / 无 GPU ~1.7 s / 无渲染 ~0.6 s |
| **headless 模式专属预算** | — | 冷 ≤ 500 s、暖 ≤ 60 s、启动→端点 ≤ 5 s（实测 251 / 12 / 0.62 s，留足余量） |

### 4.5 新发现：JSON-RPC batch **不是帧原子的**

`py/batch_atomicity.py` 在一次 batch 里发 **24 个完全相同的 `world.get_resources(CoinCounter)`**，
在计数跳变期间反复发：

```
C4: batches_observed=6, non_atomic_batches=1
    examples_with_multiple_values:
      [{"distinct": [{"coins":1,"target":2}, {"coins":2,"target":2}], "n_distinct": 2}]
C3: batches_observed=6, non_atomic_batches=0
```

**同一个 batch 的响应里同时出现了 `coins: 1` 和 `coins: 2`**，这是 batch 被拆到两帧处理的**直接证据**
（`bevy_remote-0.19.1/src/lib.rs:1478` 的 `while let Ok(message) = …try_recv()` 只排空**当前已在邮箱里**
的消息；HTTP 侧逐条投递时可能跨帧）。
C2/C3 的探针里出现过 `coins=1 && won=true` 的「不可能状态」，正是同一原因。

**契约含义**：适配器**不能**用 batch 当一致性快照；需要跨量一致性时，要么用游戏侧自定义方法一次返回，
要么接受帧间偏移并在判据里写明容差。6 次里出现 1 次，足以**否证「batch 原子」**，但**不足以量化概率**。

---

## 5. （Q5）建议：现在就承诺 headless（用同一二进制的运行时开关）

### 5.1 三个选项与它们的代价

| 选项 | 契约代价 | CI 代价 | 我的判断 |
|---|---|---|---|
| **A. 现在承诺（推荐）** | PRD 必须写：一种明确的「无窗口 + 无 GPU」运行模式；该模式下**没有渲染世界**（无 15703、无截图）；游戏语义不得只存在于渲染侧组件里。适配器契约增加一个 `headless` 运行配置项 + 一套启动预算。 | **可以跑在无 GPU、无桌面的 runner 上**（C4 只加载 10 个模块、不碰任何显示/GPU DLL；C3 也有实测），启动 0.62–1.7 s，60 FPS。 | ✅ **选它** |
| B. 延后（只承诺有窗有 GPU） | 契约短一点，但**将来补 headless 是重新设计**：一旦游戏把状态放进 `Sprite`/渲染系统或依赖 `+watch` 的帧率，改成 `backends: None` 就会丢渲染世界（不是「加个 feature」能补的）。 | 必须有带 GPU + 桌面会话的 runner；且**窗口模式在本机实测只有 4 FPS**，观测本身就不可靠。 | ❌ |
| C. 明确排除 | 契约最简单；但要在 PRD 里显式声明「本适配器不支持无 GPU 环境」，并且 CI 必须买/租 GPU runner 且保持会话交互。 | 最贵，且仍然解决不了 4 FPS 的采样问题。 | ❌ |

### 5.2 推荐的契约落点（逐条，可直接抄）

1. **运行模式**：适配器契约声明两种运行模式 —— `windowed`（默认，开发/演示）与 `headless`
   （CI/观测）。**同一二进制**通过环境变量或启动参数切换（C6 已实测这种形态可行）。
2. **headless 的定义（精确）**：无窗口（`primary_window: None`）、不建 winit 事件循环、
   **不请求 wgpu 适配器**（`WgpuSettings { backends: None }`）、**不存在渲染世界**、
   不存在 15703、不支持截图。
3. **runner 是必需项**：headless 模式必须显式添加 `ScheduleRunnerPlugin::run_loop(1/60)`
   （或以其它方式保证循环）；否则进程跑一帧就以退出码 0 结束（实测 C7）。
   契约里写成硬性要求，并让适配器把「启动后 5 s 内端点未就绪且进程已退出」判为**配置缺陷**，
   而不是游戏缺陷。
4. **观测量必须与渲染解耦**：E3 的五个观测所需的类型（`Player` / `Transform` / `Velocity` /
   `Grounded` / `CoinCounter` / `WinFlag` / 注入面）**必须在无渲染世界时依然存在且可读**
   （实测四种配置全部成立）。PRD 要禁止把计数器/胜利位/接地状态放进渲染系统或渲染侧组件。
5. **不要用 batch 做一致性快照**（§4.5）；需要跨量一致时用游戏侧自定义 BRP 方法。
6. **端点规则**：主世界恒为 15702；不依赖 15703 的存在性；需要 15703 的能力显式标注为「仅 windowed」。
7. **采样率下限**：观测契约应声明「游戏循环 ≥ 30 Hz 且与窗口可见性无关」。
   windowed 模式实测 4 FPS（窗口被遮挡时），因此**建议 CI 一律用 headless**。
8. **构建预算**：见 §4.4；headless 产物另设更紧的预算。

### 5.3 落地成本（诚实）

- 游戏侧：`main()` 里加一个模式分支（约 20 行，见 §1.1），依赖行**不用改**（路线 A）。
- 适配器侧：多一条启动路径、多一套期望值（启动耗时、端点集合）、以及「headless 下 15703 不存在」
  这一条断言；并与 SPIK-E1 的「窗口模式亦可用」路径共存。
- PRD 侧：新增一节「运行模式」，并把「不支持无 GPU」从非目标里删掉。
- CI：无 GPU 的 runner 可用；**不需要**软件渲染器。

---

## 6. （F）我**没能**确定的东西（诚实清单）

1. **真正的「无显示」环境**（Windows session 0 / 无桌面的服务 / 无 X11 的容器）：**没有实测**。
   本机始终有桌面会话。C4 的证据是结构性的（`winit` 不在依赖图、加载模块里没有 `user32`），
   C3 是运行时性的（`WinitPlugin` 被 disable），但都不等于「在无显示环境里跑过」。
2. **跨平台**：只在 Windows 11 + MSVC + rustc 1.98.0 上测。Linux/macOS 的 `default_platform`
   特性（x11/wayland）与 headless 的组合未测。
3. **软件适配器（WARP / llvmpipe）**：未测。C3/C4 不需要它；但「**有**渲染世界而机器**没有** GPU」
   这条路（例如需要截图的无 GPU 机器）完全没验证过。
4. **能否在无适配器的情况下造出一个「空的渲染世界」**：看起来**不可能**——
   `create_render` 在 `backends: None` 时返回 false，`ExtractPlugin` 不会被加入。我没尝试
   `backends: Some(Backends::empty())` 这种「非 None 但空」的写法（源码推断它会走 adapter 请求
   并 panic，但未实测）。
5. **`backends: None` 之后能否再切回渲染**：没测。按源码看同一进程内不可逆。
6. **窗口模式 4 FPS 的确切原因**：`WinitSettings::continuous()` 无效（C5），前台化窗口无效
   （`SetForegroundWindow` 后仍是 ~240 ms），C2 在**同一个渲染世界**下却是 60 FPS，
   所以不是渲染负载。剩下「被遮挡窗口的 present 节流 / 驱动行为」这一假设**未隔离**。
7. **batch 非原子的概率**：6 次里 1 次（C4），样本太小，**不能量化**，只能否证「原子」。
8. **release 模式的 headless 数字**：没测（只测了 debug）。
9. **确定性**：跳跃弧线的形状在不同次运行间是否逐位可复现没测（SPIKE-1 也留了这条）。
10. **`game.screenshot` 在 headless 下**：按构造**不可能**（没有 RenderApp），因此没有尝试。
11. **feature 统一的作用域**：我把「无渲染」配置放在**独立 workspace**里测，避免 workspace 内
    feature 合并污染。若把 C4 风格成员与渲染成员放进同一个 workspace，数字可能不同（未测）。
12. **`bevy_dev_tools` 能否被绕过**：`bevy_remote` 对它的依赖**不是可选的**
    （`Cargo.toml.orig:28`，非 optional），所以「精简 BRP 的依赖」在当前版本做不到（只有源码打补丁）。
13. **无 runner 时的退出路径**：只测到 rc=0 且端点未起；没有细看它是在哪个 stage 结束的。
14. **`SPIKE2_HEADLESS` 之外的开关形态**（cargo feature / 命令行参数）：只测了环境变量。
15. **多窗口 / 多相机**在 headless 下的行为：没测（本 spike 只有 1 个相机、0 个窗口）。

---

## 附录 A：复跑入口与命令（全部在仓外 `F:\bevy-spike2\`）

```
build_timed.sh                 带字面退出码与墙钟的 cargo 包装（用法：bash build_timed.sh <workdir> <target-dir> <cargo args…>）

ws_render\                     保留渲染特性的 workspace（C1/C2/C3/C5/C6/C7）
  Cargo.toml                   members = spike2_core, c1_windowed, c2_windowless, c3_nogpu,
                               c5_winit_continuous, c6_switchable, c7_norunner
  Cargo.lock                   sha256 284bf2ccb45f3c141ce3562a0114cf2b1d982aee8b752225cf1bcb727adb3af7
                               （153563 B，567 个 [[package]]，67 个 bevy 家族，全部 0.19.1）
  spike2_core\                 渲染无关的游戏内核（lib），类型路径 spike2_core::game::*
  c1_windowed\                 C1 对照：DefaultPlugins + BRP，真窗口 + 真 GPU
  c2_windowless\               C2：primary_window=None，WinitPlugin 保留
  c3_nogpu\                    C3：primary_window=None + disable::<WinitPlugin>() + backends:None + ScheduleRunner(1/60)
  c5_winit_continuous\         C5：C1 + WinitSettings::continuous()（诊断 4 FPS 用）
  c6_switchable\               C6：一个二进制，SPIKE2_HEADLESS=1 时切到 C3 形态
  c7_norunner\                 C7：C3 去掉 ScheduleRunnerPlugin（负例）
ws_norender\                   default-features=false 的独立 workspace（C4）
  Cargo.lock                   sha256 6293b032f5b07cbbf821d027cc74a4d5180d0dc7b11d53d60e0b0ffda7c30fcb
                               （115023 B，428 个 [[package]]，53 个 bevy 家族）
  spike2_core\                 与 ws_render 逐字节相同的 game.rs（sha256 见下）
  c4_norender\                 C4：default_app + bevy_remote + ScheduleRunner(1/60)，无 winit/render 插件
target-render\ target-norender\  两个独立 target 目录（冷构建数字来自它们第一次构建）

py\probe.py <exe> --out <json> --log <log> --tag <t>   五观测 + 端点 + 窗口 + 延迟 + 事件注入（一个脚本全测）
py\startup.py <exe> <runs> <json> --tag <t>            启动→端点就绪 N 次计时
py\fps.py <exe> <json> --tag <t>                       SSE 数帧 / FrameCount 探测，测真实帧率
py\latency.py <exe> <json> --tag <t> --n N             rpc.discover 与 get_components 往返分布
py\modules.py <exe> <json> --tag <t>                   进程加载模块表（GPU/显示 DLL 证据）
py\transition.py <exe> <json> --tag <t>                用 BRP 拨状态 + 确定性计数/胜利位跳变
py\batch_atomicity.py <exe> <json> --tag <t>           同 batch 多次读同一资源的原子性反例
py\focus_latency.py <exe> <json> --tag <t>             前台化窗口是否改善帧率（否）
py\summarise.py / timeline_check.py / arcs.py / stats.py / final_stats.py / print_startup.py / c6_check.py
                                                       结果汇总

out\c1_windowed.json c2_windowless.json c3_nogpu.json c4_norender.json
    poison-c1_windowed.json poison-c2_windowless.json poison-c3_nogpu.json poison-c4.json
    c6_windowed.json c6_headless.json c7_norunner.json
    transition-{c1_windowed,c2_windowless,c3_nogpu,c4}.json
    batch-c3_nogpu.json batch-c4_norender.json
    fps-{c1,c2,c3,c4,c5}.json  latency-c1.json  focus-c1.json
    modules-{c1_windowed,c3_nogpu,c4}.json  startup-{c1_windowed,c2_windowless,c3_nogpu,c4}.json
    *_stdout.log                                       游戏进程 stdout（含 panic 的原始文本）
```

**关键复跑命令（含字面退出码）**

| # | 命令 | 退出码 | 结果 |
|---|---|---|---|
| 1 | `bash build_timed.sh ws_render target-render build -p c1_windowed` | **0** | 冷 302 s |
| 2 | `bash build_timed.sh ws_norender target-norender build -p c4_norender` | **0** | 冷 251 s |
| 3 | `python py/probe.py target-render/debug/c3_nogpu.exe --out out/c3_nogpu.json --log out/c3_nogpu.log --tag c3_nogpu` | **0** | 0 窗口、15703=false、五观测通过 |
| 4 | `WGPU_BACKEND=zzz python py/probe.py target-render/debug/c1_windowed.exe …` | **0**（子进程 **101**） | `Unable to find a GPU!` |
| 5 | `WGPU_BACKEND=zzz python py/probe.py target-norender/debug/c4_norender.exe …` | **0** | 正常运行 |
| 6 | `python py/probe.py target-render/debug/c7_norunner.exe …` | —（经管道未捕获脚本码；**子进程 0**） | 一帧后退出，端点未起 |
| 7 | `python py/fps.py target-render/debug/c1_windowed.exe …` | **0** | 4.0 FPS |

**版本与工具链**（与 SPIKE-1 同一台机器）
```
Windows 11 Pro (kernel 26100)，AMD Ryzen 7 5800X3D (8c/16t)，127.9 GiB RAM，NVIDIA RTX 4090
rustc 1.98.0 (88d9e12ae 2026-08-18)；cargo 1.98.0 (797e8a9bc 2026-08-05)
cargo 走 ~/.cargo/config.toml 的 rsproxy.cn 稀疏镜像；linker = link.exe
bevy 解析结果：0.19.1（两个 workspace 的 Cargo.lock 都是 0.19.1，无其它版本）
关键传递依赖（与 SPIKE-1 相同）：wgpu 29.0.4, naga 29.0.4, winit 0.30.13, glam 0.32.1,
hyper 1.11.1, smol-hyper 0.1.1, bevy_remote 0.19.1
```

## 附录 B：关键源码位置（便于复核）

| 事实 | 位置 |
|---|---|
| `backends: None` ⇒ `create_render` 返回 false | `bevy_render-0.19.1/src/settings.rs:270-273` |
| 只有渲染可用才 `add_plugins(ExtractPlugin)`（⇒ 才有 RenderApp） | `bevy_render-0.19.1/src/lib.rs:359-365` |
| 有 RenderApp 才注册渲染端点（15703） | `bevy_remote-0.19.1/src/http.rs:142-160`（`:146` 的 `else { return }`） |
| `bevy_remote` 无条件依赖 `bevy_dev_tools` | `bevy_remote-0.19.1/Cargo.toml.orig:28-30` |
| `bevy_remote` 的 `bevy_render` 由 bevy_internal 无条件打开 | `bevy_internal-0.19.1/Cargo.toml.orig:557-560` |
| `bevy_window` 关闭时 `DefaultPlugins` 自带 `ScheduleRunnerPlugin` | `bevy_internal-0.19.1/src/default_plugins.rs:19-20` |
| `MinimalPlugins` 的内容 | `bevy_internal-0.19.1/src/default_plugins.rs:161-170` |
| `default_app` = 官方「无渲染基线」特性集 | `bevy-0.19.1/Cargo.toml.orig:172-179` |
| `DefaultPlugins` 自动包含 `TransformPlugin`/`TimePlugin` | `bevy_internal-0.19.1/src/default_plugins.rs:5-13` |
| 找不到 adapter 的 panic 与消息 | `bevy_render-0.19.1/src/renderer/mod.rs:142-144, 286` |
| 未知 `WGPU_BACKEND` ⇒ 空后端集（毒化实验的基础） | `wgpu-types-29.0.4/src/backend.rs:156-159, 182-204` |
| `WgpuSettings::default()` 读 `WGPU_BACKEND` | `bevy_render-0.19.1/src/settings.rs:84` |
| `WinitSettings` 的四种模式（`continuous` 也救不了 4 FPS） | `bevy_winit-0.19.1/src/winit_config.rs:13-59` |
| Bevy 自己的 headless 配方（窗口+无渲染器） | `bevy-0.19.1/examples/app/no_renderer.rs` |
| Bevy 自己的「无 winit 只跑一次」示例 | `bevy-0.19.1/examples/app/without_winit.rs` |
| Bevy 自己的 headless 示例 | `bevy-0.19.1/examples/app/headless.rs` |
| batch 逐条排空邮箱（非帧原子的根因） | `bevy_remote-0.19.1/src/lib.rs:1478`（`process_remote_requests`） |

## 附录 C：仓库未被触碰（收尾实测）

```
$ cd /f/moonbit-hof-rs
$ git status --porcelain
?? .spec/bevy/
?? l.json
?? p2.json
?? pv.json
?? r.json

$ git diff --stat
(空)
$ git rev-parse HEAD
5bfcee3d47055bbef3ac26c496ae3e33908702de
$ sha256sum Cargo.toml Cargo.lock DECISIONS.md
e0c4992bd828729b8514f9cf694925687b726157d45463a636390081a3dadba1 *Cargo.toml
d98fa91565ec72ae998fd9f6fd3838286e287e4baf8020c5114a1e2ac0bfdb36 *Cargo.lock
9f95f26e90ee6d05c6c5161af55e6c818c9ada0e75fee4479e5155b3d42843e8 *DECISIONS.md
```

- 与 SPIKE-1 收尾时**逐字相同**：同样 5 个未跟踪条目（`.spec/bevy/` 是交付物目录，4 个 JSON 在
  SPIKE-1 开工前就存在），tracked 文件零改动，`Cargo.toml`/`Cargo.lock` 哈希与 SPIKE-1 记录一致。
- 本次**只往仓库新增本文件**。所有构建、脚本、探测输出、workspace 都在 `F:\bevy-spike2\`。
- 清理纪律：**没有对任何路径执行 `rm -rf`**（本次也没有删除任何目录）；
  **没有执行过 `git checkout --`**。

## 附录 D：本报告里的「实测」与「推断」分界

**实测（有原始 JSON/日志与退出码）**：四配置与 C6 两模式的 `rpc.discover` 方法数/端口/窗口数/存活；
15703 的有无；五观测的采样序列；毒化实验的 rc=101 与正常存活；C7 的一帧退出；构建耗时（冷/暖）；
启动计时；exe 体积；加载模块表；帧率（SSE 数帧）；请求往返分布；batch 非原子反例；确定性转场。

**源码推断（读代码得出、与实测一致但未单独做反例）**：15703 消失的因果链
（`settings.rs:270` → `lib.rs:359` → `http.rs:146`）；`bevy_remote → bevy_dev_tools → bevy_pbr` 的构建成本；
`WinitSettings` 默认值；`default_app` 的内容；`ExtractPlugin` 负责创建 RenderApp。

**未测（已列入 §6）**：真无桌面环境、跨平台、软件适配器、release headless、确定性、
feature 统一作用域、4 FPS 的确切机理、batch 非原子的概率。
