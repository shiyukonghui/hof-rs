using Godot;

namespace snake;

/// <summary>
/// The food pellet.
///
/// <para><c>CellX</c> / <c>CellY</c> are <c>[Export]</c> so a session can pin the
/// pellet deliberately in front of the head: <c>running_game_set_node_property</c>
/// writes it, the next step consumes it, and the growth that follows is a fact
/// with a before/after rather than a hope.</para>
/// </summary>
public partial class Food : ColorRect
{
    public const int CellSize = 24;

    /// <summary>Grid column of the pellet.</summary>
    [Export] public int CellX = 0;

    /// <summary>Grid row of the pellet.</summary>
    [Export] public int CellY = 0;

    public void Move(int col, int row)
    {
        CellX = col;
        CellY = row;
        Visible = true;
        Position = new Vector2(col * CellSize, row * CellSize);
    }
}
