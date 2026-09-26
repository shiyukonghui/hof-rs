using Godot;

namespace snake;

/// <summary>
/// One body segment of the snake.
///
/// <para>Like every observable in this series, the grid cell is a real Godot
/// property set through <see cref="Place"/>: the MCP trace can read
/// <c>position</c> back from the node and a pixel diff can corroborate it.
/// <c>Order</c> is the segment's index from the head, so a trace can tell a
/// grown snake from a moved one.</para>
/// </summary>
public partial class SnakeSegment : ColorRect
{
    public const int CellSize = 24;

    /// <summary>Index from the head (0 = the head).</summary>
    [Export] public int Order = 0;

    /// <summary>Whether this pool member is currently part of the snake.</summary>
    [Export] public bool InUse = false;

    public void Place(int col, int row, int order)
    {
        Order = order;
        InUse = true;
        Visible = true;
        Position = new Vector2(col * CellSize, row * CellSize);
    }

    public void Retire()
    {
        InUse = false;
        Visible = false;
    }
}
