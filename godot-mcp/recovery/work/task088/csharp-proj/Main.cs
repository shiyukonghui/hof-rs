using Godot;

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
