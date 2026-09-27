using Godot;

namespace breakout;

/// <summary>
/// One brick of the Breakout wall — the second C# game of the godot-mcp series
/// (TASK-093, DECISIONS.md D138).
///
/// <para><c>Alive</c> is an <c>[Export]</c> on purpose, exactly like
/// <c>Ball.Velocity</c> in Pong: "the brick is gone" has to be a real Godot
/// property so <c>running_game_get_node_properties</c> can read it back,
/// <c>running_game_assert_node_state</c> can pin it, and the ledger can judge
/// the call that changed it. Nothing observable lives in a private field.</para>
/// </summary>
public partial class Brick : ColorRect
{
    /// <summary>False once the ball has taken this brick out.</summary>
    [Export] public bool Alive = true;

    /// <summary>Points this brick is worth; the root sums them.</summary>
    [Export] public int Points = 10;

    /// <summary>Takes the brick out: it leaves the visible field but stays a node.</summary>
    public void Destroy()
    {
        Alive = false;
        Visible = false;
        // Keep the rect so the wall geometry stays inspectable from a trace; only
        // the pixels go away.
        GD.Print($"BREAKOUT_BRICK_DESTROYED name={Name} points={Points}");
    }
}
