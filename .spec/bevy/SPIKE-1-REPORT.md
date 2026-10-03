# SPIKE-1 报告：Bevy 0.19.1 + Bevy Remote Protocol（BRP）作为运行时观测面

- 日期：2026-10-03
- 执行者：spike 子代理（无先验上下文，单人执行，不委派）
- 范围：只回答三个问题（BRP 真实动词面 / 构建与启动预算 / 远端插件对被测游戏的强加）
- 本仓库改动：**只新增本文件**。仓库 `Cargo.toml`、`Cargo.lock`、`src/**`、`tests/**`、
  `DECISIONS.md`、`.spec/hof-rs/**`、`runs/**`、冻结规范、任何 workspace 目录：**一字未改**
  （证据：§C.0）。所有构建与探测都在仓外 `F:\bevy-spike\` 进行。
- 证据文件（仓外，可复跑）：`F:\bevy-spike\probe-debug.json`、`probe2-debug.json`、
  `probe3-debug.json`、`ports-debug.json`、`probe-release.json`、`shot-debug.json`、
  `startup-{debug,release}-noload.json`、`shot\shot.png`、`ws/Cargo.lock`、
  `py/*.py`（全部脚本）、`src-probe/`（解包后的 crate 源码）。

> **English TL;DR (for skimming)**
> 1. BRP on Bevy 0.19.1 is **23 JSON-RPC methods over plain HTTP/1.1, no auth, no TLS, no CORS**,
>    two loopback ports (15702 main world / 15703 render world). **There is no screenshot verb and
>    no input-injection verb.** Input injection *is* achievable purely over BRP because
>    `world.trigger_event` / `world.write_message` / `world.mutate_resources` exist — but only if
>    **the game itself declares a reflectable intent surface**. Screenshots require the game to add a
>    custom BRP method (verified working, ~15 lines).
> 2. Cold debug build of a minimal Bevy 0.19.1 + `bevy_remote` app: **304 s** (562 crates, 186 MB
>    exe). Warm, same-feature one-line rebuild: **~18 s**. Cold release build: **452 s** (91 MB exe).
>    A shared warm target dir is what turns 5 min into 18 s — but only if the feature set is frozen
>    (a feature-set change in the same dir cost 236 s).
> 3. Minimal transport diff = **1 cargo feature + 3 lines**. Semantic observability additionally
>    requires `#[reflect]` + `register_type` on the marker/state/input surface and a stable type-path
>    contract. The PRD must require this explicitly.

---

## 0. 结论（先看这段）

### 0.1 一句话裁决

**BRP 这条路线可以承载观测需求，但「观测需求」必须拆成两半分别落地：**

- **只读/写入 ECS 的一半**（移动、计数、胜负位、跳跃弧线、反射式输入注入）：**BRP 原生动词足够**，
  不需要写任何自定义方法。已在本机活体进程上逐条实测通过（§4）。
- **不属于 ECS 的一半**（**像素/截图**、以及"玩家踩在地面上"这种**语义**）：**BRP 原生做不到**，
  必须由**被测游戏自己配合**：
  - 截图：游戏内加一个自定义 BRP 方法（`RemotePlugin::with_method_main`）桥接 Bevy 自带的
    `Screenshot`，**已实测可用**（§5、§3.7）。
  - 「站在地上」：不是引擎概念，必须由游戏声明一个 `Grounded` 之类的可反射标记/状态位，
    否则工具只能拿到"y 坐标等于地面高度"的**代理量**，语义留在人类/模型脑子里而不在工具里。

因此 **PRD 必须写进两条硬性要求**（否则适配器无解）：
1. 被测游戏必须暴露一个**可反射的语义契约**（玩家标记组件、计数器资源、胜利位资源、
   地面状态、输入意图类型），并且这份契约的**类型路径**进入冻结范围；
2. 若视觉证据是验收项，游戏必须提供一个**截图用自定义 BRP 方法**（或等价物）。

### 0.2 与我们五个行为的对照（诚实版）

| 目标行为 | 纯 BRP 能否见证 | 实测证据 | 需要游戏配合什么 |
|---|---|---|---|
| 玩家移动 | **能** | `x: 1.65 → 94.15`，两种注入方式各测一遍 | 只需可反射 `Transform`（Bevy 自带已注册）+ 一个玩家标记 |
| 金币计数跳变 | **能** | `coins 1 → 2`（`target=2`） | 计数器必须是**已注册的可反射资源/组件**（引擎资源默认大多不可反射，见 §0.4-3、§4.2） |
| 胜利位跳变 | **能** | `won false → true` | 同上 |
| 跳跃上-下弧线 | **能**，但有采样率上限 | 15 个上升样本 + 15 个下降样本，峰值 −103.5、地面 −200.0 | 若用轮询，采样率受 HTTP 往返限制（实测 ~25–50 Hz）；SSE `+watch` 可到游戏帧率 |
| 玩家正站在地面上 | **不能直接**（只能读代理量） | `Grounded { on_ground: true }` 读得到；但这是**游戏自己声明的** | **必须**由游戏暴露 `Grounded` 等价物，否则只能读 y 值靠约定推断 |

### 0.3 输入注入：关键但反直觉的结论

BRP **没有**任何键鼠/输入动词（`world.send_input`、`world.press_key`、`input.press_key` 全部返回
`-32601 Method not found`，实测）。但 **BRP 有更通用的注入通道且实测可用**：

| 通道 | 需要游戏做什么 | 实测结果 |
|---|---|---|
| `world.mutate_resources`（写资源字段） | 一个可反射资源，字段是"意图" | ✅ 驱动玩家移动、起跳 |
| `world.trigger_event`（触发观察者事件） | `#[derive(Event, Reflect)] #[reflect(Event)]` + `register_type` + 一个 observer | ✅ 命名域事件 `MoveRequest { x }` 触发后玩家真的动了；`JumpRequest` 触发后真的跳了 |
| `world.write_message` | `#[derive(Message, Reflect)] #[reflect(Message)]` + `register_type` | ⚠️ 只验到"类型不存在时的报错"，没跑通真实报文（§F） |
| `world.insert_components` | 无额外要求 | ✅ 插入/替换组件成功 |

**由此得到一条会写进 PRD 的设计约束**：注入面必须是**电平触发（level-triggered）**的持续量
（`move_x` 保持到被覆盖），只有动作类意图（跳）才用**边沿触发**且**由游戏自己清除该边沿**。
原因：一次 BRP 写只落在一个（或少数几个）帧上；如果游戏每帧把注入值清零，那么
"写一次 `move_x=1.0` 再隔 0.4 秒采样"的移动量只有 2–3 像素，行为不可观测。本 spike 第一版
游戏逻辑就是踩了这个坑（每帧清零 → 0.4 s 只走了 ~2 px），改成电平触发后同一操作走了 ~92 px。

### 0.4 需要现在就告诉 PRD 的其它后果

1. **类型路径就是契约**。BRP 全部用 `bevy_transform::components::transform::Transform` 这样的
   **全限定类型路径**寻址，路径里带**crate 名**。所以游戏 crate 改名、模块改名、组件改名，
   都会静默打断所有工具。契约必须冻结这些字符串。
2. **读形状 ≠ 写形状，且不能自作聪明做 schema 重映射**。实测：`Transform` **读**出来是
   `{"translation":[x,y,z],"rotation":[x,y,z,w],"scale":[x,y,z]}`；**写**也接受同样的数组形式；
   但写成嵌套 map（`{"translation":{"x":…}}`）会被拒（`invalid type: map, expected a sequence of
   4 f32 values`）。而 `world.mutate_components` 的 `path` 用的是**反射字段名**
   （`translation.x` 可用），用**JSON 数组下标**（`translation[0]`）会报错。结论：
   **适配器必须做 pass-through 往返，不允许按自己的 schema 重新拼装**。
3. **引擎自带资源大多不可反射**：`world.list_resources` 只列出 44 个，而 `bevy_time::time::Time`
   这种最常用的资源竟然**不在**其中（`Unknown resource type`）。可观测面**不会白送**。
4. **两个端点，不是一**个。`RemoteHttpPlugin` 在 `bevy_render` 存在时会**再开一个 15703**，
   面向 render 子世界，方法名一模一样、世界完全不同（实测）。适配器必须**钉死 15702**，
   否则"查得到但查不到实体"这种幽灵 bug 会长期存在（对应 Godot 时代的 DR-43 双端点问题）。
5. **HTTP 永远返回 200**。错误在 body 里（`-32601` 等），不会用 HTTP 状态码。任何"看状态码判成败"
   的适配器写法都会把全部错误当成功。

---

## 1. （Q1）BRP 在 Bevy 0.19.1 上的真实动词面

### 1.1 证据来源与方法（不是博客）

| 来源 | 具体物 | 说明 |
|---|---|---|
| crates.io 元数据 | `https://crates.io/api/v1/crates/bevy/0.19.1` | 确认 0.19.1 存在（2026-08-13 发布）、MSRV `1.95.0`、172 个 feature |
| 0.19.1 crate 源码 | `bevy_remote-0.19.1/src/{lib.rs,builtin_methods.rs,http.rs,schemas/*}` | 动词注册表、HTTP 传输、观察者/监听实现 |
| 0.19.1 crate 源码 | `bevy_ecs-0.19.1/src/reflect/{event,message,resource}.rs` | 反射事件/消息/资源与资源的"资源实体"模型 |
| 0.19.1 crate 源码 | `bevy_internal-0.19.1/Cargo.toml.orig` | feature 传递关系 |
| 0.19.1 crate 源码 | `bevy_render-0.19.1/src/view/window/screenshot.rs` | 截图 API（游戏内可达、BRP 不可达） |
| **活体进程实测** | `rpc.discover` on 127.0.0.1:15702 / 15703 | 23 个方法的权威清单（§4.1） |
| 负例实测 | 对 13 个"想象中的动词"逐个调用 | 全部 `-32601`（§4.9） |

### 1.2 完整动词表（23 个，实测 `rpc.discover`，`openrpc: 1.3.2`）

| # | 方法 | 类别 | 读/写什么 | 边界与实测备注 |
|---|---|---|---|---|
| 1 | `rpc.discover` | 元 | 返回 OpenRPC 文档（方法名、server url） | 活体探活的最佳手段；`servers` 里给出的 url 就是当前端口 |
| 2 | `world.get_components` | 读 | 单实体的指定若干组件值 | 需全限定类型路径；`strict` 控制"组件不存在"是报错还是放进 `errors` |
| 3 | `world.query` | 读 | 按 `with`/`without` 过滤实体，返回实体 id + 组件值；`option:"all"` 返回该实体全部可反射组件 | **没有**分页/上限/排序/空间/数值比较过滤；返回整个匹配集；实测 `result` 是**数组** |
| 4 | `world.list_components` | 元 | 不传参 = 全部已注册组件类型路径；传 `entity` = 该实体上的组件名 | 实测 312 个组件、玩家实体 16 个组件 |
| 5 | `world.get_components+watch` | 读（流） | 单实体上"上一 tick 变化/移除"的组件 | **SSE**（`text/event-stream`）；实测连续 60 帧；`None` 时不发帧 |
| 6 | `world.list_components+watch` | 读（流） | 单实体上"新增/移除"的组件名 | 同上，SSE |
| 7 | `world.get_resources` | 读 | 一个资源的完整值 | 想读"计数/胜利位"就靠它 |
| 8 | `world.list_resources` | 元 | 全部**已注册可反射**资源类型路径 | 实测只有 44 个；`Time` 不在其中 |
| 9 | `world.insert_resources` | 写 | 插入/整体替换一个资源 | 可用于把计数器拨到任意值（作弊式布置测试态） |
| 10 | `world.mutate_resources` | 写 | 按反射路径写资源**单个字段** | 注入面的主力（实测驱动移动/起跳） |
| 11 | `world.remove_resources` | 写 | 删除资源 | 破坏性，慎用 |
| 12 | `world.insert_components` | 写 | 往实体插入/替换组件（map 形式） | 实测给点亮的实体插 `Player {}` 成功 |
| 13 | `world.remove_components` | 写 | 删除实体的若干组件 | — |
| 14 | `world.mutate_components` | 写 | 按反射路径写组件单字段 | `translation.x` ✅ / `translation[0]` ❌（路径用字段名不用下标） |
| 15 | `world.spawn_entity` | 写 | 新建实体并带初始组件，返回实体 id | 实测成功；**内层数学类型必须用数组形式** |
| 16 | `world.despawn_entity` | 写 | 删除实体 | 实测成功 |
| 17 | `world.reparent_entities` | 写 | 设置/清除父子关系 | 未活体实测（源码头注释提到自环错误码 `-23404`） |
| 18 | `world.trigger_event` | 写 | 用 JSON 负载触发一个**观察者事件** | ✅ 实测：驱动游戏 observer 真的改变行为 |
| 19 | `world.write_message` | 写 | 写入一个**缓冲消息（Message）** | ⚠️ 只验到错误路径（§F） |
| 20 | `world.observe+watch` | 读（流） | 注册全局/实体作用域观察者并**流式回传事件负载** | 命名域事件 ✅（收到 `[{"x":1.0}]`）；**单元结构体事件收不到任何帧**（复现，未定位，§F） |
| 21 | `registry.schema` | 元 | 全部已注册类型的 JSON Schema（可按 crate 过滤） | 实测 45 个类型；`componentInfo.storageType` 等元数据都在 → 可用来生成类型化工具面 |
| 22 | `schedule.list` | 元 | 15 个调度标签 + 空/不可用标签 | `RemoteLast` 出现在 `unavailable_schedule_labels`，说明远端处理挂在 `Last` 之后 |
| 23 | `schedule.graph` | 元 | 某调度的系统依赖图 | 实测返回 `dependency`/`hierarchy`（系统 id 数字，需配合其他信息解读） |

**不存在（且我逐个实测确认为 `-32601`）**：任何截图/录屏动词；任何键鼠/手柄输入动词；
任何"等一帧/推进时间"动词；任何日志读取动词；任何窗口/分辨率动词；任何文件/资源动词；
`world.get_entity` / `world.list_entities` / `world.set_component` 等想当然的名字。

### 1.3 传输、认证、并发、扩展

| 维度 | 事实（源码 + 实测） |
|---|---|
| 协议 | JSON-RPC 2.0。`"jsonrpc":"2.0"` **必填**，缺了会得到 `-32600 missing field jsonrpc` |
| 传输 | HTTP/1.1（hyper + smol-hyper + async-io），`POST` 到根路径 `/`。**没有 WebSocket** |
| 批量 | 支持 JSON 数组批量请求，返回数组（实测两条批量均成功） |
| 流式 | `+watch` 方法回 `text/event-stream`，帧格式 `data: {json}\n\n`；**批量里不能含流式方法**（源码显式报 `INVALID_REQUEST`） |
| 端点 | 默认 `127.0.0.1:15702`（主世界）+ `127.0.0.1:15703`（render 子世界，`bevy_render` 存在时） |
| 认证 | **完全没有**。源码里没有任何 auth/token/secret 逻辑；不校验 Origin；不发 CORS 头（要自己用 `RemoteHttpPlugin::with_header` 加） |
| 响应头 | `Content-Type: application/json`（流式为 `text/event-stream`） |
| 错误模型 | 一律 HTTP 200 + body 里的 `error{code,message}`；码表：`-32700/-32600/-32601/-32602/-32603`（JSON-RPC 标准）+ `-23401 ENTITY_NOT_FOUND`、`-23402 COMPONENT_ERROR`、`-23403 COMPONENT_NOT_PRESENT`、`-23404 SELF_REPARENT`、`-23501 RESOURCE_ERROR`、`-23502 RESOURCE_NOT_PRESENT` |
| 调度位置 | 主世界的 `RemoteLast`（插在 `Last` 之后）每帧跑一次：先处理新请求，再轮询所有 `+watch` 请求 → **流式采样率 = 游戏帧率** |
| 扩展点 | `RemotePlugin::with_method_main/with_method_render`、`with_watching_method_main/…`（处理器签名 `fn(In<Option<Value>>, …) -> BrpResult`，可获得 `&mut World` 独占访问）；也可运行期改 `RemoteMethods` 资源 |
| 序列化 | 由 `bevy_reflect` 的 `ReflectSerializer`/`TypedReflectDeserializer` 决定：**自定义命名域结构体 = JSON 对象；glam 数学类型 = JSON 数组**。全程不做 schema 校验，只有类型内部一致性 |

### 1.4 开启方式（精确到 feature）

```toml
# 被测游戏 Cargo.toml
bevy = { version = "0.19.1", features = ["bevy_remote"] }
```
```rust
use bevy::remote::{RemotePlugin, http::RemoteHttpPlugin};
app.add_plugins(RemotePlugin::default())
   .add_plugins(RemoteHttpPlugin::default());
```

- `bevy` feature `bevy_remote` → `bevy_internal/bevy_remote` → `dep:bevy_remote` + `serialize`；
  非 wasm 目标上 `bevy_remote` 用 **默认 feature（含 `http`）**，所以 HTTP 传输自动带上
  （证据：`bevy_internal-0.19.1/Cargo.toml.orig:557,584`）。
- ⚠️ **陷阱**：`bevy` 自身的 `http` / `https` feature **不是** BRP 传输，而是
  `bevy_asset?/http`（资产加载）。开错 feature 会得到"编译通过但没有端口"的假成功。
- ⚠️ `RemotePlugin` **不会**被 `DefaultPlugins` 自动加入（grep 全 `bevy_internal/src` 无引用），
  必须显式 `add_plugins`；端口是由 `RemoteHttpPlugin` 开的（源码结论，未做"只加 RemotePlugin"的
  对照实验 → §F）。

---

## 2. （Q3）远端插件对被测游戏的强加：最小可观测 diff

### 2.1 传输层最小 diff（= 3 行 + 1 个 feature）

`plain/src/main.rs` → `observed/src/main.rs` 的全部差异：

```diff
+#[path = "../../shared/game.rs"]
+mod game;
+
+use bevy::remote::{RemotePlugin, http::RemoteHttpPlugin};
+
 fn main() {
-    game::build_app().run();
+    let mut app = game::build_app();
+    app.add_plugins(RemotePlugin::default())
+        .add_plugins(RemoteHttpPlugin::default());
+    app.run();
 }
```
（`plain` 与 `observed` 共用同一个 `game.rs`，所以上面的差异就是**全部**差异；
可用 `diff -u ws/plain/src/main.rs ws/observed/src/main.rs` 复现。）

### 2.2 语义可观测层：BRP 本身不提供，必须由游戏声明

实测得到的最小"语义面"清单（每一条都对应工具能不能看懂）：

| 面 | 最小声明 | 不做的后果 |
|---|---|---|
| 玩家标记 | `#[derive(Component, Reflect)] #[reflect(Component)] struct Player;` + `register_type::<Player>()` | 工具无法区分玩家和地面/金币，只能靠几何猜 |
| 地面状态 | `#[reflect(Component)] struct Grounded { on_ground: bool }` | "站在地上"只能靠 y 值代理量 |
| 计数器 | `#[derive(Resource, Reflect)] #[reflect(Resource)] struct CoinCounter { coins, target }` + `register_type` | `world.get_resources` 报 `Unknown resource type` |
| 胜利位 | 同上 | 同上 |
| 注入面 | 电平触发资源 `SpikeInput { move_x, jump_pressed }`（`#[reflect(Resource)]`），**或** `#[derive(Event, Reflect)] #[reflect(Event)]` 的意图事件 + observer | 无输入注入通道（BRP 没有输入动词） |
| （可选）截图 | 自定义 BRP 方法桥接 `Screenshot` | 拿到不了一帧画面 |

`#[reflect(Resource)]` 之所以够用：`bevy_ecs-0.19.1/src/reflect/resource.rs:39` 在注册
`ReflectResource` 时**同时注册了 `ReflectComponent`**，而 BRP 读资源走的是"资源实体"上的
`ReflectComponent` 路径（`builtin_methods.rs:628-636`）。这一点与 0.18 及以前不同，是本代特有细节。

### 2.3 只应存在于 dev/run 构建

**应该**：`bevy_remote` 打开一个**无认证的本地端口**。生产/发布构建不应带它。做法：给产物工程一个
专用 cargo feature（如 `observability`），只在 harness 轮次里启用，功能块用
`#[cfg(feature = "observability")]` 包住；**不要**用 `#[cfg(debug_assertions)]`，因为
release 也可能被 harness 用来跑构建预算或视觉证据（§3.3），那样观测面会消失。

代价（必须写进契约）：feature 是**编译指纹的一部分**。用同一个共享 target 目录时，
"开观测 feature 的构建"和"不开的构建"会各自触发大范围重编译（实测 §3.2：236 s）。

### 2.4 对即将写的 PRD 的硬性后果（我会坚持的条目）

1. **游戏必须声明并冻结语义契约**：玩家标记 / 计数器资源 / 胜利位资源 / 地面状态 /
   输入意图类型的**全限定类型路径**，写入产物工程的清单文件（或由自定义 BRP 方法
   `game.describe` 返回）。适配器不允许"猜类型路径"。
2. **注入面必须电平触发**，边沿由游戏自己清（§0.3）。
3. **若验收含视觉证据，必须实现 `game.screenshot`**（自定义 BRP 方法，实测可行）。
4. **观测量必须落到"被注册的可反射类型"上**，不允许把关键状态藏在不可反射的引擎资源里。
5. **`A_0` 需要预置观测脚手架**（feature + 插件 + `register_type` + 注入面 + 契约清单），
   否则"从空工程出发"的开发者必须自己发明一套词汇，工具面无从对齐。
6. 时间语义：BRP 采样是墙钟 + 每帧处理；跳跃弧线这类连续性判据要么固定步长
   （`Time<Fixed>`），要么用容差断言。本 spike **没有**验证确定性（§F）。

---

## 3. （Q2）构建与启动预算：实测数字

> 主机：Windows，Git Bash；`rustc 1.98.0 (88d9e12ae 2026-08-18)`、`cargo 1.98.0 (797e8a9bc
> 2026-08-05)`、`rustup 1.29.0`、toolchain `stable-x86_64-pc-windows-msvc`。
> Bevy 0.19.1 自报 MSRV `1.95.0` → **本机工具链满足**。
> cargo 走 `~/.cargo/config.toml` 里的 **rsproxy.cn 稀疏镜像**（`replace-with = 'rsproxy-sparse'`）。
> 网络只用于抓 crate；**没有任何构建脚本从网上下东西**。

### 3.0 复现用命令（含字面退出码）

| # | 命令（工作目录 `F:\bevy-spike\ws`，除注明外） | 退出码 | 结果 |
|---|---|---|---|
| 1 | `rustc --version; cargo --version; rustup toolchain list` | 0 | 见上 |
| 2 | `curl -A "spike/1.0" https://crates.io/api/v1/crates/bevy/0.19.1` | 0 | 确认 0.19.1 存在、MSRV 1.95.0 |
| 3 | `python py/fetch_crate.py bevy_remote 0.19.1`（及 `bevy_ecs`/`bevy_render`/`bevy_internal`） | 0 | 解包 0.19.1 源码到 `src-probe/` |
| 4 | `cargo generate-lockfile` | 0（**注**：该次为管道后 `$?`，取到的是 `tail` 的码；见 §F.13） | 锁定 **562 packages**，9 s |
| 5 | `bash build_timed.sh <target> fetch` | **0** | 冷抓取 **38 s** |
| 6 | `bash build_timed.sh <target> build -p spike_observed` | **0** | 冷 debug 构建 **304 s** |
| 7 | `bash build_timed.sh <target> build -p spike_plain`（同一 target） | **0** | **236 s**（feature 集不同 → 重编 4 个 crate） |
| 8 | 改 `shared/game.rs` 一行 → `bash build_timed.sh <target> build -p spike_observed` | **0** | 增量 **18 s**（cargo 报 18.28 s） |
| 9 | 再加事件类型 → 同一命令 | **0** | 增量 **19 s**（cargo 报 17.92 s） |
| 10 | `python py/brp_probe.py <exe> --out … --log …` | **0** | 12 个相位全部跑完，游戏进程全程存活 |
| 11 | `python py/brp_probe2.py <exe> <out>` | **0** | 写形状/注入/路径 全部拿到 |
| 12 | `python py/brp_probe3.py <exe> <out>` | **0** | `observe+watch` 语义（复数事件帧已验证） |
| 13 | `python py/ports_probe.py <exe> <out>` | **0** | 15702/15703 双端点确认 |
| 14 | `python py/startup_time.py <exe> 3` | **0** | 启动耗时（含并发负载，见下） |
| 15 | 早期一次 `python py/brp_probe.py ...`（脚本 bug） | **1** | `AttributeError: 'list' object has no attribute 'get'` —— 我当时误以为 `world.query` 返回 `{entities:[…]}`，实测返回**数组**；此错误本身是一条有用证据 |
| 16 | 同脚本一次 300 s 上限 | **124** | `timeout` 杀掉；原因是我的采样循环在 app 未崩溃时被 5 s/请求的超时拖长，**不是**被测程序挂死 |
| 17 | `bash build_timed.sh <target> build --release -p spike_observed` | **0** | release 冷构建 **452 s** |
| 18 | `bash build_timed.sh <target> build -p spike_observed_shot` | **0** | 增量 **20.75 s** |
| 19 | `python py/shot_probe.py <exe> <out>` | **0** | `game.screenshot` 可用，PNG 落盘 |
| 20 | `python py/startup_time.py <exe> 5`（debug / release 各一次） | **0** | 3104.7 ms / 2249.4 ms（均值） |

### 3.1 依赖解析（精确版本 + 锁文件指纹）

- `Cargo.lock`：**564 个 `[[package]]` 条目**，515 个唯一 crate 名，**49 个多版本条目**（36 个名字有多版本）。
  （cargo 自己打印的是 `Locking 562 packages`；与锁文件 564 个条目差 2，未深究 —— 见 §7-17。
  下表以**锁文件条目数**为准。）
- 锁文件 `sha256 = 27f4ce8008ae542268cdc1c6b507da41c7d8a291adfcdcef052b2e36a025d534`，
  大小 `153255` 字节（**此哈希在加入 `observed_shot` 成员后会变，见 §3.6**）。
- Bevy 家族：**67 个 `bevy*` crate，全部 0.19.1**（含 `bevy_remote 0.19.1`）。
- 关键传递依赖：`wgpu 29.0.4`、`naga 29.0.4`、`winit 0.30.13`、`glam 0.32.1`、
  `image 0.25.10`、`serde 1.0.229`、`serde_json 1.0.151`、`hyper 1.11.1`、`smol-hyper 0.1.1`、
  `async-io 2.6.0`、`tokio 1.53.1`、`rodio 0.22.2`、`alsa 0.11.0`、`windows 0.62.2`、
  `windows-sys 0.61.2`（0.45/0.52/0.59/0.60/0.61 五版本并存）、`objc2 0.6.4`。
- **必须来自网络的东西**：562 个 crate 的下载（走 rsproxy.cn 镜像）与索引刷新，合计 **38 s**。
  除此之外没有网络依赖（Bevy 自带字体等资产已 vendored）。
- 依赖引入评估：**全部是 Bevy 官方 crate**，无需第三方选型；`bevy_remote` 即 Bevy 仓库自带
  （MIT OR Apache-2.0），无额外许可证风险。

### 3.2 构建耗时与产物尺寸

| 指标 | 实测 | 备注 |
|---|---|---|
| 冷 `cargo fetch` | **38 s** | 562 crate |
| 冷 debug 构建（`bevy` 默认 feature + `bevy_remote`） | **304 s**（cargo 自报 `Finished dev … in 5m 04s`） | 单次，无并发负载 |
| 冷 debug 二构（同 target，换 feature 集） | **236 s** | 只重编 4 个 crate，但都是巨型 crate（`bevy_gizmos_render`/`bevy_internal`/`bevy`）+ 链接 |
| 暖增量（同 profile 同 feature，改一行应用代码） | **18.28 s** / **17.92 s**（两次样本） | 只重编 app crate + 链接 186 MB 可执行文件 |
| debug 可执行文件 | **186,567,680 B（177.9 MiB）** | `spike_observed.exe` |
| debug 可执行文件（无观测 feature） | **173,028,864 B（165.0 MiB）** | `spike_plain.exe` |
| **观测面带来的二进制增量** | **13,539,328 B（12.9 MiB，+7.8 %）** | 即 `bevy_remote` 的代码体积 |
| 冷 release 构建（`--release`，与 debug 共用 target） | **452 s**（7m 30s） | 产出 91.1 MiB |
| release 可执行文件 | **95,541,248 B（91.1 MiB）** | debug 的 51.2 % |
| 暖增量（新增一个观测脚手架 crate `observed_shot`） | **20.75 s** | 新 crate 编译 + 链接 |
| 启动→远端端点可用（debug，无负载，5 次均值） | **3104.7 ms** | 中位 3183.1；见 §3.4 |
| 启动→远端端点可用（release，无负载，5 次均值） | **2249.4 ms** | 极差仅 43 ms |

> 观察：冷构建的 5 分钟里，真正的大头是 67 个 Bevy crate 的 codegen；而**单 crate 增量**里
> 大头是 MSVC `link.exe` 把 186 MB 的可执行文件链出来。两者是不同的瓶颈，优化手段也不同。

### 3.3 release 数字（已实测）

| 指标 | 实测 | 备注 |
|---|---|---|
| 冷 release 构建（`cargo build --release -p spike_observed`，与 debug 共用同一 target 目录） | **452 s**（cargo 自报 `Finished release [optimized] … in 7m 30s`） | 退出码 0；日志里可见 67 个 bevy crate 全部走优化编译 |
| release 可执行文件 | **95,541,248 B（91.1 MiB）** | 是 debug 体积的 **51.2 %** |
| release 下的行为等价性 | **一致** | 同一套 12 相位探测在 release 二进制上重跑：23 个方法、跳跃峰值 −103.52、计数 1→2、`won false→true`、SSE 60 帧、13 个伪动词全拒、进程全程存活 —— 与 debug 逐项相同 |
| release 启动→端点就绪 | **2249.4 ms**（均值，5 次；2228.4–2271.4，极差 43 ms） | 比 debug 的 3104.7 ms 快约 28 % |
| debug 启动→端点就绪（无负载，5 次） | **3104.7 ms**（均值；2701.7–3240.1；中位 3183.1） | 见 §3.4 |

### 3.4 进程启动 → 远端端点可用

测量方法：子进程启动计时；每 20 ms `POST rpc.discover`（超时 0.5 s），首次拿到 JSON 即停表。
端口是 `RemoteHttpPlugin` 在 `Startup` 之后由 `IoTaskPool` 起协程绑定，所以这个数包含
Bevy 初始化 + 窗口创建 + 首帧渲染。

| 条件 | 实测（debug 构建，无并发负载） |
|---|---|
| 5 次 | **3240.1 / 3219.9 / 3178.5 / 2701.7 / 3183.1 ms** → 均值 3104.7，中位 3183.1 |
| 探针脚本内计时（另一脚本） | 3187.3 / 3633.8 / 3349.9 ms |
| **有并发 cargo release 构建时** | **5433.3 / 5433.3 / 5497.5 / 6600.1 ms** |

→ 结论：**debug 启动约 3.1 s，release 约 2.25 s**；有并发负载时可翻倍到 6.6 s。
适配器契约必须把"等待端点就绪"做成**轮询 + 超时（建议 30 s）**、对负载不敏感，
不能写死 sleep。release 的 5 次样本极差仅 43 ms，说明**无负载时这个量非常稳**。

### 3.5 共享暖 target 目录是否改变图景：改变，但有两个前提

| 策略 | 一轮成本 | 说明 |
|---|---|---|
| 每轮全新 target（无缓存） | **~5 分钟** | 不可接受的每轮预算 |
| 共享 target + **feature 集固定** + 只改应用代码 | **~18 秒** | 这是可接受的每轮预算 |
| 共享 target 但 feature 集漂移 | **~4 分钟** | 实测 236 s：`bevy`/`bevy_internal` 等被重编 |
| 每轮改依赖（`Cargo.toml` 变动） | 视改动而定，最坏回到冷构建 | 必须靠锁文件 + 禁止轮间改依赖来避免 |

### 3.6 锁文件变更登记（加 `observed_shot` 之后）

| 时点 | `Cargo.lock` sha256 | `[[package]]` 条目 | 唯一 crate 名 |
|---|---|---|---|
| 仅 bevy + bevy_remote（§3.1 主测量） | `27f4ce8008ae542268cdc1c6b507da41c7d8a291adfcdcef052b2e36a025d534` | 564 | 515 |
| 加入 `observed_shot`（+ 直接依赖 `serde_json`） | `de0104b5ee0b3b3574b3e7e5c8969712dfcc37bb84fdf5a6b20a5d6769a4777a` | 565 | 516 |

差异**只有**新成员 `spike_observed_shot v0.1.0` 一个条目；`serde_json` 早在锁文件里
（`1.0.151`，由 bevy 传递引入），**没有任何已解析版本发生变化**（36 个多版本 crate 名单不变）。
→ 契约含义：**"新增一个直接依赖"不一定要改版本，但一定会改锁文件哈希**。因此"锁文件哈希漂移
即判本轮不可比"这条规则必须配套一个**白名单**（例如允许"仅新增本地成员、无版本变化"的漂移），
否则每加一个观测脚手架 crate 都会误判。

### 3.7 后补测量汇总（release / 截图 / 启动）

1. **release 构建**：452 s，产物 95,541,248 B（§3.3）。
2. **release 行为等价**：与 debug 逐项一致（§3.3）。
3. **`game.screenshot` 自定义 BRP 方法**：构建 **20.75 s**（新 crate + 链接），编译一次通过。
   活体实测（§5）：
   - `rpc.discover` 方法数 **23 → 24**，出现 `game.screenshot`；
   - `POST game.screenshot {"path":"F:\\bevy-spike\\shot\\shot.png"}` → `{async:true, requested:…}`；
   - **1307.3 ms** 后文件出现，**33,246 B，1920×1080 真 PNG**（`\x89PNG\r\n\x1a\n`，IHDR 1920×1080），
     画面内容为深色背景 + 蓝色玩家方块 + 三枚黄色金币 —— **是真实的一帧游戏画面**，不是空图；
   - 不传 `path` 时落盘到工作目录的 `screenshot.png`（成功）；
   - `path` 传非字符串（`123`）时**静默回退到默认路径，不报错**（适配器必须自己在参数层校验）。

---

## 4. （证据）关键实测摘录

### 4.1 `rpc.discover`（活体，端口 15702）

```json
{"openrpc":"1.3.2","info":{"title":"Bevy Remote Protocol","version":"0.19.1"},
 "servers":[{"name":"Server","url":"127.0.0.1:15702"}],
 "methodCount":23}
```

### 4.2 按语义标记找玩家并读组件

请求 `world.query`：`{"data":{"components":["bevy_transform::components::transform::Transform"]},
"filter":{"with":["spike_observed::game::Player"]}}` → 找到 `entity=4294966889`。

`world.get_components` 回读：

```json
{"components":{
  "bevy_transform::components::transform::Transform":
     {"rotation":[0.0,0.0,0.0,1.0],"scale":[1.0,1.0,1.0],"translation":[0.0,-200.0,0.0]},
  "spike_observed::game::Grounded":{"on_ground":true},
  "spike_observed::game::Player":{},
  "spike_observed::game::Velocity":{"x":0.0,"y":0.0}},
 "errors":{}}
```

注意同一个响应里 **glam 类型是数组、自定义结构体是对象**。

### 4.3 移动（`world.mutate_resources` 注入，电平触发）

写 `SpikeInput.move_x = 1.0` 后连续 20 次采样 `Transform.translation.x`：

```
1.65, 7.50, 13.34, 17.54, 20.84, 26.69, 31.65, 37.51, 41.73, 44.97,
49.18, 54.15, 58.32, 62.55, 65.85, 71.67, 77.54, 82.53, 88.33, 94.15
```
→ 单调递增，0.42 s 内位移 ~92 px。**行为可被纯 BRP 见证。**

### 4.4 跳跃弧线（`world.mutate_resources` 注入 `jump_pressed`）

100 次采样（HTTP 轮询，~30 Hz），`TRANSFORM.translation.y`：

```
14.5ms -194.23 | 76.6ms -170.75 | 139.2ms -150.68 | 222.8ms -129.49 | 326.7ms -111.87
416.9ms -104.42 | 452.2ms -103.52 (峰值) | 513.6ms -104.61 | 632.2ms -116.27
757.2ms -142.31 | … | 2944.6ms -200.00 (回到地面)
```
统计：**15 个上升步 + 15 个下降步**，min −200.0（地面），max −103.52（峰值）。**真实的先升后降弧线。**

`world.get_components+watch`（SSE）在移动期间**连续吐出 60 帧**、`content_type: text/event-stream`、
未提前断开 → 高频采样它也行，且采样率等于游戏帧率。

### 4.5 计数与胜利位跳变

```
t=27.7ms   x=151.97  CoinCounter{coins:1,target:2}  WinFlag{won:false}
t=1061.5ms x=276.04  CoinCounter{coins:2,target:2}  WinFlag{won:true}
```
→ 两个跳变都被 BRP 直接读到。前置条件：它们是**已注册可反射资源**。

### 4.6 事件注入（BRP 原生，无需自定义方法）

- `world.trigger_event {"event":"spike_observed::game::JumpRequest","value":{}}` → `result: null`，
  随后 100 次采样真的看到跳跃弧线（§4.4 同款形状）。
- `world.trigger_event {"event":"…::MoveRequest","value":{"x":1.0}}` → x 从 201.67 涨到 270.85。
- 负载写错时错误信息友好：`MoveRequest is invalid: unknown field 'nope', expected one of 'x'`。

### 4.7 写形状对照实验（`world.spawn_entity`）

| 负载形状 | 结果 |
|---|---|
| `{Transform:{translation:[1,2,0],rotation:[0,0,0,1],scale:[1,1,1]}}` | ✅ 成功，返回 entity |
| `[[1,2,0],[0,0,0,1],[1,1,1]]`（外层也当序列） | ✅ 成功 |
| `{Transform:{translation:{x:1,y:2,z:0},rotation:{…},scale:{…}}}` | ❌ `invalid type: map, expected a sequence of 4 f32 values` |
| `{Player:{}}`（只带自定义组件） | ✅ 成功 |

`world.mutate_components`：`path="translation.x"` ✅ ；`path="translation"` + 数组值 ✅ ；
`path="translation[0]"` ❌ `Expected index access to access a list, found a struct instead`。

### 4.8 两个端点（同一进程、同一套方法名）

```
tcp 127.0.0.1:15702 LISTENING  pid=45908   rpc.discover → 23 methods, servers=[127.0.0.1:15702]
tcp 127.0.0.1:15703 LISTENING  pid=45908   rpc.discover → 23 methods, servers=[127.0.0.1:15703]
```
（仅回环地址，无认证。）

### 4.9 负例：BRP 没有的东西

对以下方法逐个 POST，全部 `{"code":-32601,"message":"Method `X` not found"}`，HTTP 200：
`world.take_screenshot`、`world.screenshot`、`screenshot.capture`、`world.send_input`、
`world.inject_input`、`world.press_key`、`input.press_key`、`world.get_entity`、
`world.set_component`、`world.exists`、`world.spawn`、`world.despawn`、`world.entity_info`。

其它边界：
- 缺 `jsonrpc` → `-32600 missing field jsonrpc`
- 非 JSON body → `-32600 expected value at line 1 column 1`
- 空 body / `GET /` → `-32600 EOF while parsing a value`（**GET 也被受理**，仍返回 200）
- 批量请求 ✅ 返回数组
- 未知事件/消息类型 → `-23501 Unknown event type/message type: …`

---

## 5. （Q1 后半）截图与自定义方法：**已实测可行**

`bevy_remote 0.19.1` 里 **`screenshot` 一词零命中**（对整个 crate 源码 grep）。但扩展点足够：

```rust
// 游戏侧，约 15 行
pub fn screenshot_handler(In(params): In<Option<Value>>, world: &mut World) -> BrpResult {
    let path = params.as_ref().and_then(|p| p.get("path")).and_then(|v| v.as_str())
        .unwrap_or("screenshot.png").to_string();
    world.spawn(Screenshot::primary_window()).observe(save_to_disk(path.clone()));
    Ok(json!({"requested": path, "async": true}))
}
// main.rs
app.add_plugins(RemotePlugin::default()
    .with_method_main("game.screenshot", screenshot_handler));
```

实测（`spike_observed_shot`）：

- `rpc.discover` 方法数 **23 → 24**，新方法 `game.screenshot` 出现；
- 调用后 **PNG 文件真的落盘**（见 §3.7 的产物与尺寸证据）；
- 证据图（仓外，可直接打开看）：`F:\bevy-spike\shot\shot.png` —— 1920×1080，
  深色背景 + 蓝色玩家方块 + 三枚黄色金币，是**真实一帧游戏画面**；
- Bevy 的截图是**异步**的（渲染器要先呈现一帧），所以方法只能"下单"，适配器需要"轮询文件"。

附带成本：自定义方法需要 `serde_json` 成为**直接依赖**（返回 `BrpResult = Result<Value, BrpError>`），
`BrpError`/`BrpResult` 从 `bevy::remote` 再导出。这条要写进契约。

---

## 6. （Q2/Q3）给适配器契约的具体建议

### 6.1 构建预算（建议直接抄进契约）

| 条目 | 建议值 | 依据 |
|---|---|---|
| 冷构建（无缓存，debug，含观测 feature） | **≤ 600 s**（实测 304 s，留 2×） | §3.2 |
| 暖构建（共享 target、feature 冻结、只改游戏源码） | **≤ 90 s**（实测 18–21 s，留 4–5×） | §3.2 |
| 单轮总预算（构建 + 启动 + 交互 + 观测） | **≤ 180 s** | 18 s + 3.1 s + 余量 |
| 启动→端点就绪等待 | 轮询，间隔 20–50 ms，**超时 30 s**，禁止写死 sleep | §3.4（debug 3.1 s / release 2.25 s；负载下 6.6 s） |
| release 构建 | **452 s / 91 MiB**，**不建议**放进每轮预算；只在需要性能或视觉证据时用 | §3.3 |

### 6.2 缓存策略（建议直接抄进契约）

1. **一个项目一个持久 target 目录**，放在 workspace 外（如 `%LOCALAPPDATA%\hof-bevy\<project>-target`
   或 `.workspace/.cargo-target`），**跨轮复用**；不要每轮删。
2. **冻结 feature 集**：观测量全部走一个名为 `observability`（名字可换）的 cargo feature，
   轮次之间**不得**开关或增删其它 bevy feature。任何 feature 漂移都会把 18 s 变成 236 s。
3. **锁文件入库并冻结**：`Cargo.lock` 必须随产物保留；冷构建后登记 sha256，轮次间校验。
   漂移默认视为"这一轮不可比"，但需配一个**白名单**：允许"仅新增本地成员 crate、
   无任何已解析版本变化"的漂移（实测这种漂移一定会改哈希，详见 §3.6）。
4. **轮 0 预热**：正式 T=1 之前先对 `A_0` 跑一次 `cargo build`，把 67 个 Bevy crate 的产物
   固化进缓存；这样第 1 轮的预算也是 ~18 s 而不是 5 min。
5. **不要轮间改 `Cargo.toml` 依赖**。允许的改动限于游戏源码。
6. **可选加速（未验证）**：本机存在 `lld-link`（scoop llvm）与 `rust-lld`；把
   `-C linker=lld-link` 作为 opt-in 很可能显著缩短链接，但本 spike **没有测**（§7-1）。
   要用就先做对照实验，别直接写进契约。

### 6.3 工具清单形状（建议）

**不要**照搬 Godot 时代 177 个工具。分两层，且**必须 pass-through**：

**A. 通用层（1:1 映射 BRP 原生动词，机械可生成，不发明语义）**

| 工具 | 底层 | 备注 |
|---|---|---|
| `brp.discover` | `rpc.discover` | 启动时自检、断言方法数 |
| `entity_query` | `world.query` | 直接透传 `data`/`filter`/`strict` |
| `entity_get` | `world.get_components` | 透传 |
| `entity_watch` / `entity_unwatch` | `world.get_components+watch` | SSE 长连接；注意 bounded(8) 通道风险（§7-5） |
| `entity_list_components` | `world.list_components` | — |
| `resource_get` / `resource_list` / `resource_mutate` | `world.get_resources` / `world.list_resources` / `world.mutate_resources` | 透传路径与值 |
| `entity_insert` / `entity_remove` / `entity_spawn` / `entity_despawn` | 同名 BRP 方法 | 透传，**不做形状转换** |
| `registry_schema` | `registry.schema` | 用于生成/校验类型化工具 |
| `schedule_list` / `schedule_graph` | 同名 | 排障用 |

**B. 语义层（绑定"冻结的游戏契约"，数量应少于 10）**

| 工具 | 实现方式 | 依据 |
|---|---|---|
| `game.describe` | 自定义 BRP 方法（或读取产物内清单文件）返回类型路径契约 | §2.4-1 |
| `game.player_state` | `world.get_components(player, [Transform, Grounded, Velocity])` | 语义标记 |
| `game.score` | `world.get_resources(CoinCounter)` | — |
| `game.win_state` | `world.get_resources(WinFlag)` | — |
| `game.inject_move` / `game.inject_jump` | `world.mutate_resources`（电平）或 `world.trigger_event`（意图事件） | §0.3 |
| `game.track_jump_arc` | `entity_watch`（Transform）或高频轮询 | §4.4 |
| `game.screenshot` | 游戏侧自定义 BRP 方法 | §5 |
| `game.wait_until` | 适配器本地实现（轮询 + 超时），**不是** BRP 动词 | §1.2 |

契约硬性条目：
- 端口**钉死 15702**；15703 只能在明确需要 render 世界时使用（§4.8）。
- 判成败**只看 body**（HTTP 恒为 200）；错误码需分类（`-32601` 视为适配器 bug 而非游戏 bug）。
- 值**原样往返**，禁止 schema 重映射（§0.4-2）。
- 进程 stdout/stderr 必须由 harness 捕获（BRP **没有**日志动词，游戏崩溃/恐慌只能从进程侧看到）。
- 观测量必须能"未注册/不存在"地失败并**显式记为 gap**，不允许静默当 0。

---

## 7. （F）我**没能**确定的东西（诚实清单）

1. **`lld-link` 的加速幅度**：本机有 `lld-link` / `rust-lld`，但换链接器会改变 `RUSTFLAGS`
   指纹 → 全量重编，我没时间为它再做一次 5 分钟对照。
2. **release 构建耗时与体积**：**已测**（452 s / 95,541,248 B，§3.3），且 release 行为已验证等价。
   **仍未测**的是 release 的**暖增量**（只改了 debug 的增量）与"release 是否值得进每轮预算"
   （每轮 7.5 分钟显然不值）。
3. **release（优化）构建的行为等价性**：**已测**，与 debug 逐项一致（§3.3）。
4. **`world.observe+watch` 对"单元结构体事件"收不到任何帧**：命名域事件正常（收到
   `[{"x":1.0}]`），单元结构体 `JumpRequest` 复现为空流且**无 warning、无 panic、进程存活**，
   根因未定位（源码里 `.get(&event).expect("event keyed by its type path")` 是可疑点，
   但我没有把假设做成实验）。**建议：注入面一律用有命名字段的事件。**
5. **`+watch` 慢消费者风险**：源码 `http.rs:409` 用 `bounded(8)` + `try_send`，而
   `lib.rs:1537-1540` 在 `try_send` 失败时直接 `close()` 通道。也就是说**消费慢于游戏帧率时，
   流会被静默关闭**。我只测了跟得上的快消费者（60 帧无异常），**没有**构造慢消费者反例。
6. **启动耗时的样本量**：**已补测**（debug 无负载 5 次均值 3104.7 ms，中位 3183.1 ms；
   release 无负载 5 次均值 2249.4 ms，极差 43 ms）。**未测**的是"有并发负载时的分布"
   （只有 4 个样本，5433–6600 ms）。
7. **headless（无窗口）路径**：我在游戏里写了 `SPIKE_HEADLESS=1` 分支（`primary_window: None`），
   但**从未运行**；所以在无显示器的 CI 上能不能跑、端口能不能起、性能如何，均未知。
8. **跨平台**：只在 Windows MSVC 上测。macOS/Linux 的构建时间、链接器、启动时间未测。
9. **`world.write_message` 的真实通路**：只验证了"未知消息类型 → -23501"，没跑通真实 Message。
10. **`world.reparent_entities`、`schedule.graph` 的语义**：一个未实测，一个只看到原始图数据。
11. **注入与游戏自身系统的竞争/时序**：BRP 请求在每帧 `RemoteLast` 处理，写入是否可能被同帧
    游戏系统覆盖、是否会丢 tick，未做确定性实验。
12. **"只加 `RemotePlugin` 不加 `RemoteHttpPlugin` 是否真的不开端口"**：这是**源码结论**，
    我没做对照实验。
13. **命令退出码的一处瑕疵**：`cargo generate-lockfile` 那次的 `EXITCODE=0` 来自管道末端的
    `tail`，不是 cargo 本身（`build_timed.sh` 之后的测量都正确捕获了 cargo 的 rc）。
    如实记录，不改写。
14. **确定性/可复现性**：同一轮的行为（跳跃弧线形状、启动耗时）在不同次运行之间是否逐位可复现，
    未验证；也没有把物理改成固定步长来消除帧率依赖。
15. **CI/无 GPU 环境**：本机有 GPU 与窗口会话；软渲染（llvmpipe/WARP）路径未测。
16. **仓库基线 `git status`**：我在开工时没有先抓一份基线（失误）。收尾时实测仓库
    **无任何 tracked 文件改动**（§C.0），且未追踪文件只有 4 个在我开工前 `ls` 里就已存在的 JSON，
    外加交付物 `.spec/bevy/`。
17. **依赖包计数口径**：cargo 说 `Locking 562 packages`，锁文件里有 **564** 个 `[[package]]` 条目
    （唯一名 515）。差 2 的原因未查（可能是 cargo 对 workspace 成员/被 patch 条目的计数口径）。
    引用数字时请注明用的是哪一个口径。

---

## 附录 C：证据与数字索引

### C.0 仓库未被触碰（收尾实测）

```
$ git status --porcelain            # 仓根 F:\moonbit-hof-rs，收尾实测（含本报告）
?? .spec/bevy/
?? l.json
?? p2.json
?? pv.json
?? r.json
$ git status --porcelain | wc -l
5
$ git diff HEAD --stat -- Cargo.toml Cargo.lock DECISIONS.md src tests godot-mcp config scripts
(空)
$ git diff --stat
(空)
$ sha256sum Cargo.lock Cargo.toml
d98fa91565ec72ae998fd9f6fd3838286e287e4baf8020c5114a1e2ac0bfdb36 *Cargo.lock
e0c4992bd828729b8514f9cf694925687b726157d45463a636390081a3dadba1 *Cargo.toml
```
- 唯一的**新增**条目是 `?? .spec/bevy/`，即本报告（交付物本身）。
- 那 4 个未追踪 JSON **在我开工时的第一次 `ls` 就已存在**（同一份清单），非本次产生。
- **tracked 文件零改动**：`git diff` / `git diff HEAD` 均为空，`Cargo.lock`/`Cargo.toml` 哈希未变。
- 除 `.spec/bevy/` 外，本次没有往仓库写入任何文件。所有构建产物、脚本、探测输出、解包源码
  都在 `F:\bevy-spike\`。
- 清理纪律：本次**没有对任何路径执行 `rm -rf`**（只有一次 `os.remove` 删除我自己产出的
  `F:\bevy-spike\shot\shot.png`，以及 `rm -f` 删除我自己产出的探测 JSON/日志）；
  **没有执行过 `git checkout --`**。

### C.1 复跑入口（全部在仓外）

```
F:\bevy-spike\
  py\fetch_crate.py          下载并解包任意 crate@version 源码
  py\lock_summary2.py        Cargo.lock 版本/多版本统计
  py\brp_probe.py            12 相位活体探测（发现→查询→资源→移动→跳跃→流→计数→反例→传输→调度→生成实体）
  py\brp_probe2.py           写形状 / mutate 路径 / 事件注入 / observe+watch
  py\brp_probe3.py           observe+watch 语义专测
  py\ports_probe.py          15702 / 15703 双端点
  py\shot_probe.py           game.screenshot 自定义方法的活体验证
  py\startup_time.py         启动→端点就绪 N 次计时
  ws\build_timed.sh          带字面退出码与墙钟的 cargo 包装
  ws\{plain,observed,observed_shot}\  三个可执行目标
  ws\shared\{game.rs,screenshot.rs}   共享游戏逻辑 / 截图自定义方法
  ws\Cargo.lock              sha256 27f4ce80…（加 observed_shot 成员后 → de0104b5…，见 §3.6）
  src-probe\bevy_*{remote,ecs,render,internal}-0.19.1\  权威源码
  probe-debug.json / probe2-debug.json / probe3-debug.json / ports-debug.json /
  probe-release.json / shot-debug.json / startup-{debug,release}-noload.json
  shot\shot.png              自定义方法产出的真实一帧（1920×1080）
```

### C.2 版本与工具链

```
rustc 1.98.0 (88d9e12ae 2026-08-18)
cargo 1.98.0 (797e8a9bc 2026-08-05)
rustup 1.29.0；toolchains: stable(默认)/nightly/nightly-2026-04-03/1.93.0 (x86_64-pc-windows-msvc)
bevy 0.19.1 自报 rust_version = 1.95.0
```

### C.3 关键源码位置（便于复核）

| 事实 | 位置 |
|---|---|
| 23 个默认方法注册 | `bevy_remote-0.19.1/src/lib.rs:672-788`（`add_default_methods`） |
| 方法名常量 | `bevy_remote-0.19.1/src/builtin_methods.rs:45-111` |
| HTTP 传输 / SSE / 默认端口 | `bevy_remote-0.19.1/src/http.rs:49-57, 304-430` |
| `+watch` 轮询（每帧）与通道关闭 | `bevy_remote-0.19.1/src/lib.rs:1527-1543`；`http.rs:407-409` |
| 错误码表 | `bevy_remote-0.19.1/src/lib.rs:1387-1425` |
| `#[reflect(Resource)]` 同时注册 ReflectComponent | `bevy_ecs-0.19.1/src/reflect/resource.rs:33-40` |
| `ReflectEvent` / `#[reflect(Event)]` 生成观察者 | `bevy_ecs-0.19.1/src/reflect/event.rs:125-142` |
| 资源以"资源实体"存在 | `bevy_ecs-0.19.1/src/world/mod.rs:264, 2089` |
| 截图 API（游戏内可达） | `bevy_render-0.19.1/src/view/window/screenshot.rs:47-134` |
| `bevy_remote` 的 feature 传递 | `bevy_internal-0.19.1/Cargo.toml.orig:338, 557-560, 583-585` |
