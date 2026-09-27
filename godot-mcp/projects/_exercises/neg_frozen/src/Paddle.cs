using Godot;

namespace breakout;

/// <summary>
/// The Breakout paddle.
///
/// <para><c>Speed</c> / <c>MinX</c> / <c>MaxX</c> are <c>[Export]</c> for the
/// same reason as in Pong: the MCP driver has to be able to prove that what it
/// reads back is what moved the paddle. The paddle moves on X (Breakout) where
/// Pong's moved on Y, so the clamps are named for the axis they clamp.</para>
/// </summary>
public partial class Paddle : ColorRect
{
    public const float Width = 96.0f;
    public const float Height = 16.0f;

    /// <summary>Pixels per second while the bound action is held.</summary>
    [Export] public float Speed = 520.0f;

    /// <summary>Left end of the allowed travel (inclusive).</summary>
    [Export] public float MinX = 8.0f;

    /// <summary>Right end of the allowed travel (inclusive).</summary>
    [Export] public float MaxX = 696.0f;

    /// <summary>
    /// Moves the paddle by <paramref name="direction"/> (-1 left, +1 right) for
    /// one step. The unit of motion is explicit so an injected one-shot press and
    /// a human held key are the same thing.
    /// </summary>
    public void Step(float direction, float delta)
    {
        var p = Position;
        p.X = Mathf.Clamp(p.X + direction * Speed * delta, MinX, MaxX);
        Position = p;
    }
}
