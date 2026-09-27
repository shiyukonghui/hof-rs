using Godot;

namespace tetris;

/// <summary>
/// Tetris — the fourth C# game of the godot-mcp series (TASK-096, DECISIONS.md D138).
///
/// <para><b>Shape table.</b> Seven kinds, four rotation states each, every state written
/// as four cells in a 4x4 box. Rotations are <i>authored</i>, not computed: a computed
/// rotation needs a kick table to be correct, and a kick table is a design decision a
/// 600-line game should not be making silently.</para>
///
/// <para><b>Why the table is a separate file.</b> The session that builds this game
/// writes each file with its own <c>project_create_script</c> call, so "the shape table
/// arrived through one MCP call and the game through another" is visible in the trace.</para>
/// </summary>
public static class Tetromino
{
    /// <summary>The piece kinds, in the order the state's <c>PieceKind</c> uses them.</summary>
    public const int KindCount = 7;

    /// <summary>Number of authored rotation states per kind.</summary>
    public const int RotationCount = 4;

    /// <summary>Cell colour per kind: I O T S Z J L.</summary>
    public static readonly Color[] Colors =
    {
        new Color(0.35f, 0.85f, 0.95f, 1f), // I  cyan
        new Color(0.95f, 0.85f, 0.30f, 1f), // O  yellow
        new Color(0.70f, 0.40f, 0.90f, 1f), // T  purple
        new Color(0.35f, 0.90f, 0.45f, 1f), // S  green
        new Color(0.95f, 0.35f, 0.35f, 1f), // Z  red
        new Color(0.35f, 0.50f, 0.95f, 1f), // J  blue
        new Color(0.95f, 0.60f, 0.25f, 1f), // L  orange
    };

    /// <summary>Short names, for the readback strings.</summary>
    public static readonly string[] Names = { "I", "O", "T", "S", "Z", "J", "L" };

    // kind -> rotation -> 4 cells (x, y) inside a 4x4 box. y grows downward.
    private static readonly int[][][] Shapes =
    {
        // I
        new[]
        {
            new[] { 0, 1, 1, 1, 2, 1, 3, 1 },
            new[] { 2, 0, 2, 1, 2, 2, 2, 3 },
            new[] { 0, 2, 1, 2, 2, 2, 3, 2 },
            new[] { 1, 0, 1, 1, 1, 2, 1, 3 },
        },
        // O
        new[]
        {
            new[] { 1, 0, 2, 0, 1, 1, 2, 1 },
            new[] { 1, 0, 2, 0, 1, 1, 2, 1 },
            new[] { 1, 0, 2, 0, 1, 1, 2, 1 },
            new[] { 1, 0, 2, 0, 1, 1, 2, 1 },
        },
        // T
        new[]
        {
            new[] { 1, 0, 0, 1, 1, 1, 2, 1 },
            new[] { 1, 0, 1, 1, 2, 1, 1, 2 },
            new[] { 0, 1, 1, 1, 2, 1, 1, 2 },
            new[] { 1, 0, 0, 1, 1, 1, 1, 2 },
        },
        // S
        new[]
        {
            new[] { 1, 0, 2, 0, 0, 1, 1, 1 },
            new[] { 1, 0, 1, 1, 2, 1, 2, 2 },
            new[] { 1, 1, 2, 1, 0, 2, 1, 2 },
            new[] { 0, 0, 0, 1, 1, 1, 1, 2 },
        },
        // Z
        new[]
        {
            new[] { 0, 0, 1, 0, 1, 1, 2, 1 },
            new[] { 2, 0, 1, 1, 2, 1, 1, 2 },
            new[] { 0, 1, 1, 1, 1, 2, 2, 2 },
            new[] { 1, 0, 0, 1, 1, 1, 0, 2 },
        },
        // J
        new[]
        {
            new[] { 0, 0, 0, 1, 1, 1, 2, 1 },
            new[] { 1, 0, 2, 0, 1, 1, 1, 2 },
            new[] { 0, 1, 1, 1, 2, 1, 2, 2 },
            new[] { 1, 0, 1, 1, 0, 2, 1, 2 },
        },
        // L
        new[]
        {
            new[] { 2, 0, 0, 1, 1, 1, 2, 1 },
            new[] { 1, 0, 1, 1, 1, 2, 2, 2 },
            new[] { 0, 1, 1, 1, 2, 1, 0, 2 },
            new[] { 0, 0, 1, 0, 1, 1, 1, 2 },
        },
    };

    /// <summary>Writes the four cells of one rotation state into <paramref name="into"/> (length 8).</summary>
    public static void Cells(int kind, int rot, int[] into)
    {
        var shape = Shapes[((kind % KindCount) + KindCount) % KindCount][((rot % RotationCount) + RotationCount) % RotationCount];
        for (var i = 0; i < 8; i++)
        {
            into[i] = shape[i];
        }
    }
}
