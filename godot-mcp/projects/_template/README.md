# `_template` — 可复用的 C# 游戏工程模板

Godot .NET 工程骨架（`Godot.NET.Sdk/4.8.0-dev`，`net8.0`），**离线可构建**。

## 生成一个新游戏

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File F:\moonbit-hof-rs\godot-mcp\tools\new_game.ps1 -Name snake
```

会在 `godot-mcp\projects\snake\` 生成一份实例化好的工程（`__NAME__` → `snake`，`__CLASS__` → `SnakeGame`）。

## 离线构建

```cmd
cd /d F:\moonbit-hof-rs\godot-mcp\projects\snake
dotnet build
```

`NuGet.config` 把包源清空后只指向本仓 `godot-mcp\godot\bin\GodotSharp\Tools\nupkgs`
（引擎克隆自带的 SDK/API 包），因此**不需要网络**。输出落在 `.godot\mono\temp\bin\Debug\`，
正是引擎加载程序集的位置。

## 占位符

| 记号 | 含义 |
|---|---|
| `__NAME__` | 工程名（小写，= 程序集名 = `<name>.csproj` 的文件名） |
| `__CLASS__` | 根脚本的 C# 类名（PascalCase） |

> `_template` 自己**不是**一个可打开的 Godot 工程（文件名里带占位符），
> 请不要直接用它起引擎；用 `new_game.ps1` 生成实例。
