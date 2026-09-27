using Godot;

namespace pong;

/// <summary>
/// The Pong ball.
///
/// <para><c>Velocity</c> is an <c>[Export]</c> on purpose: an exported field is a
/// real Godot property, so it can be read and written by the MCP tools
/// (<c>running_game_get_node_properties</c> / <c>running_game_set_node_property</c>)
/// and by the GDScript test executor. Without that, "the ball moved because we
/// changed its velocity" would not be provable from a trace.</para>
/// </summary>
public partial class Ball : ColorRect
{
    public const float Size = 16.0f;

    /// <summary>Pixels per second. Turns immediately when set from outside.</summary>
    [Export] public Vector2 Velocity = new Vector2(280.0f, 180.0f);
}
