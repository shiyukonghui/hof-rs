using Godot;

namespace pong;

/// <summary>
/// A Pong paddle.
///
/// <para><c>Speed</c> / <c>MinY</c> / <c>MaxY</c> are <c>[Export]</c> for the same
/// reason as <see cref="Ball.Velocity"/>: the MCP driver has to be able to prove
/// that what it changed is what moved the paddle.</para>
/// </summary>
public partial class Paddle : ColorRect
{
    public const float Width = 16.0f;
    public const float Height = 100.0f;

    /// <summary>Pixels per second while the bound action is held.</summary>
    [Export] public float Speed = 520.0f;

    /// <summary>Top of the allowed travel (inclusive), in the PlayField's space.</summary>
    [Export] public float MinY = 8.0f;

    /// <summary>Bottom of the allowed travel (inclusive).</summary>
    [Export] public float MaxY = 452.0f;

    /// <summary>
    /// Moves the paddle by <paramref name="direction"/> (-1 up, +1 down) for one
    /// frame. Kept as a plain method so the unit of motion is explicit.
    /// </summary>
    public void Step(float direction, float delta)
    {
        var p = Position;
        p.Y = Mathf.Clamp(p.Y + direction * Speed * delta, MinY, MaxY);
        Position = p;
    }
}
