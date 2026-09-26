using Godot;

namespace snake;

/// <summary>
/// SnakeGame — the root script of snake.
/// Generated from godot-mcp\projects\_template (TASK-091 / DECISIONS.md D138).
///
/// Every game in this folder is C#, and every game is expected to be drivable
/// from the MCP endpoints: put the observable state on named nodes and expose
/// named methods, so a trace can prove what a call actually changed.
/// </summary>
public partial class SnakeGame : Node2D
{
    /// <summary>Printed once at startup; the test driver greps for it.</summary>
    public override void _Ready()
    {
        GD.Print($"snake_READY name={Name} node={GetPath()}");
    }
}
