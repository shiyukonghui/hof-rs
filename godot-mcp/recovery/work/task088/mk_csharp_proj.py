# -*- coding: utf-8 -*-
"""task088 (1): write a minimal Godot C# project fixture.

Lives under the scratch root (H:/C: only). The project consumes Godot.NET.Sdk
from the engine's own local package source, so `dotnet build` needs no network.

usage: python mk_csharp_proj.py
"""
from __future__ import print_function
import io, os, sys

ROOT = r"H:\rebuild\godot"
PROJ = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task088\csharp-proj"
NAME = "Mcp088Csharp"
NUPKGS = os.path.join(ROOT, "bin", "GodotSharp", "Tools", "nupkgs")


def w(rel, text):
    p = os.path.join(PROJ, rel)
    d = os.path.dirname(p)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    io.open(p, "w", encoding="utf-8", newline="\n").write(text)
    print("  wrote %s (%d bytes)" % (p, len(text.encode("utf-8"))))


def main():
    if not os.path.isdir(NUPKGS):
        raise SystemExit("FATAL: local package source missing: %s" % NUPKGS)
    print("local package source: %s" % NUPKGS)
    print("local packages:")
    for n in sorted(os.listdir(NUPKGS)):
        if n.endswith(".nupkg"):
            print("  " + n)

    w("project.godot", """config_version=5

[application]

config/name="Mcp088Csharp"
run/main_scene="res://main.tscn"
config/features=PackedStringArray("4.8")

[dotnet]

project/assembly_name="Mcp088Csharp"
""")

    w("NuGet.config", """<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <packageSources>
    <clear />
    <add key="Godot" value="%s" />
  </packageSources>
</configuration>
""" % NUPKGS)

    w(NAME + ".csproj", """<Project Sdk="Godot.NET.Sdk/4.8.0-dev">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <EnableDynamicLoading>true</EnableDynamicLoading>
    <RootNamespace>Mcp088Csharp</RootNamespace>
  </PropertyGroup>
</Project>
""")

    w("Main.cs", """using Godot;

// TASK-088 (1): the smallest thing that proves the C# axis is live end to end.
// The marker line it prints is what the runner greps for: if the assembly had
// not been built and loaded, no Godot process could print it.
public partial class Main : Node
{
    public override void _Ready()
    {
        var info = Engine.GetVersionInfo();
        string version = info.ContainsKey("string") ? (string)info["string"] : "<unknown>";
        GD.Print("MCP088_CSHARP_READY version=" + version + " answer=" + Answer());
        GetTree().Quit();
    }

    private static int Answer()
    {
        return 42;
    }
}
""")

    w("main.tscn", """[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://Main.cs" id="1_main"]

[node name="Main" type="Node"]
script = ExtResource("1_main")
""")
    print("fixture root: %s" % PROJ)
    return 0


if __name__ == "__main__":
    sys.exit(main())
