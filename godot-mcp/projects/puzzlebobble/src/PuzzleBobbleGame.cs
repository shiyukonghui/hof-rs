using Godot;
using System.Collections.Generic;
using System.Text;

namespace puzzlebobble;

/// <summary>
/// Puzzle Bobble -- the nineteenth C# game of the godot-mcp series (TASK-104, DECISIONS.md D152).
///
/// <para><b>Design rule</b> (inherited from the eighteen games before it): every fact the evidence
/// model needs is a real Godot property on the root node -- <see cref="Board"/>,
/// <see cref="BoardHash"/>, <see cref="BubblesInUse"/>, <see cref="ShooterCol"/>,
/// <see cref="ShooterColor"/>, <see cref="NextColor"/>, <see cref="AngleIndex"/>,
/// <see cref="ProjCol"/>, <see cref="ProjRow"/>, <see cref="Score"/>, <see cref="Shots"/>,
/// <see cref="TotalCleared"/>, <see cref="TotalDropped"/>, <see cref="LastChain"/>,
/// <see cref="LastCleared"/>, <see cref="LastDropped"/>, <see cref="LastAttachCol"/>,
/// <see cref="LastAttachRow"/>, <see cref="Failed"/>, <see cref="Won"/>,
/// <see cref="GameOver"/>, <see cref="Steps"/>, <see cref="Elapsed"/>, <see cref="Ticks"/>. A
/// session asserts these with <c>running_game_assert_node_state</c>; it never parses a log line.</para>
///
/// <para><b>Integer, and therefore recomputable.</b> There is no float in the simulation. The board
/// is a <see cref="Cols"/> x <see cref="Rows"/> grid of colour indices (-1 is empty), the shot
/// travels one CELL per step along one of five integer directions
/// <c>(+/-2,-1) (+/-1,-1) (0,-1)</c> and reflects off the side walls, the initial board is filled
/// by the same linear congruential generator the earlier games use
/// (<c>seed = (seed*1103515245 + 12345) mod 2^31</c>, <c>(seed&gt;&gt;16) % Colors</c>) and then
/// stabilised so no run of three exists, and every score term is an integer product. The whole run
/// is reproduced exactly by the Python second implementation in
/// <c>recovery\work\task104\make_session_puzzlebobble.py</c> -- whose outputs are the session's
/// assertion literals, including the initial board and its hash.</para>
///
/// <para><b>The three requested mechanics, as rules:</b></para>
/// <list type="number">
/// <item><b>Same-colour three-in-a-row</b> (<see cref="FindGroup"/>): the group of 4-neighbours of the
/// same colour that contains the attachment cell clears when it has three or more members.</item>
/// <item><b>Detached bubbles fall</b> (<see cref="Resolve"/>): a bubble that is no longer connected
/// to the ceiling row falls out of the playfield and is removed; each one is worth
/// <see cref="DropScore"/> times the chain index.</item>
/// <item><b>Cascades</b>: the fall is processed in GENERATIONS -- only the floating bubbles that have
/// nothing under them fall at a time -- so a floating stack falls one layer per generation and every
/// generation raises <see cref="LastChain"/> and the score multiplier. A pinned two-cell tower
/// therefore produces a chain of three.</item>
/// </list>
///
/// <para><b>The failure line</b> (<see cref="FailRow"/>): after a shot is resolved, any bubble resting
/// at or below that row ends the game as a loss.</para>
///
/// <para><b>Frame-rate independence (the F-1 lesson).</b> The auto clock is a FLOAT ACCUMULATOR
/// (<c>_autoAccum += delta * AutoClock</c>). Two producers, two properties:
/// <see cref="LastAutoSteps"/> belongs to the clock and <see cref="LastHookSteps"/> to the
/// <see cref="StepFrames"/> hook. <see cref="Elapsed"/> is a monotonic float second counter that is
/// never truncated.</para>
/// </summary>
public partial class PuzzleBobbleGame : Node2D
{
    // --- the grid ----------------------------------------------------------------
    /// <summary>Columns of the playfield.</summary>
    [Export] public int Cols = 8;

    /// <summary>Rows of the playfield. Row 0 is the ceiling.</summary>
    [Export] public int Rows = 12;

    /// <summary>Side of one board cell in pixels.</summary>
    [Export] public int Cell = 40;

    /// <summary>Left edge of the playfield in pixels.</summary>
    [Export] public int GridOffsetX = 240;

    /// <summary>Top edge of the playfield in pixels.</summary>
    [Export] public int GridOffsetY = 56;

    /// <summary>How many colours a bubble can have.</summary>
    [Export] public int Colors = 6;

    /// <summary>Board rows filled at the start of a game (rows 0 .. FillRows-1).</summary>
    [Export] public int FillRows = 4;

    /// <summary>The seed the initial board is generated from.</summary>
    [Export] public int InitSeed = 20251040;

    /// <summary>A bubble resting at or below this row loses the game.</summary>
    [Export] public int FailRow = 10;

    /// <summary>Points per cleared bubble, times the chain index.</summary>
    [Export] public int ClearScore = 10;

    /// <summary>Points per fallen bubble, times the chain index.</summary>
    [Export] public int DropScore = 20;

    // --- observable state, all of it a real Godot property ------------------------
    /// <summary>The board: <see cref="Rows"/> rows of <see cref="Cols"/> characters joined by <c>/</c>; <c>.</c> is empty.</summary>
    [Export] public string Board = "";

    /// <summary>Multiply-31 hash of the board (row major, colour index + 1 so empty is 0).</summary>
    [Export] public int BoardHash = 0;

    /// <summary>Bubbles on the board right now.</summary>
    [Export] public int BubblesInUse = 0;

    /// <summary>The column the shooter sits under.</summary>
    [Export] public int ShooterCol = 4;

    /// <summary>Colour of the next shot.</summary>
    [Export] public int ShooterColor = 0;

    /// <summary>Colour after that.</summary>
    [Export] public int NextColor = 1;

    /// <summary>Index into the five integer aim directions (0 is steepest left, 2 is straight up).</summary>
    [Export] public int AngleIndex = 2;

    /// <summary>True while a shot is in the air.</summary>
    [Export] public bool ProjActive = false;

    /// <summary>Column of the shot in the air.</summary>
    [Export] public int ProjCol = -1;

    /// <summary>Row of the shot in the air.</summary>
    [Export] public int ProjRow = -1;

    /// <summary>Colour of the shot in the air.</summary>
    [Export] public int ProjColor = -1;

    /// <summary>Points.</summary>
    [Export] public int Score = 0;

    /// <summary>Shots fired over the whole game.</summary>
    [Export] public int Shots = 0;

    /// <summary>Bubbles cleared by matching, over the whole game.</summary>
    [Export] public int TotalCleared = 0;

    /// <summary>Bubbles that fell out of the playfield, over the whole game.</summary>
    [Export] public int TotalDropped = 0;

    /// <summary>Chain length of the last shot: 1 for the match itself plus one per fall generation.</summary>
    [Export] public int LastChain = 0;

    /// <summary>Bubbles the last shot cleared by matching.</summary>
    [Export] public int LastCleared = 0;

    /// <summary>Bubbles the last shot dropped.</summary>
    [Export] public int LastDropped = 0;

    /// <summary>Column the last shot attached to (-1 when the last shot matched nothing).</summary>
    [Export] public int LastAttachCol = -1;

    /// <summary>Row the last shot attached to (-1 when the last shot matched nothing).</summary>
    [Export] public int LastAttachRow = -1;

    /// <summary>True when a bubble reached the failure line.</summary>
    [Export] public bool Failed = false;

    /// <summary>True when the board was emptied.</summary>
    [Export] public bool Won = false;

    /// <summary>True when the game ended, either way.</summary>
    [Export] public bool GameOver = false;

    /// <summary>Aim calls that changed the angle.</summary>
    [Export] public int Moves = 0;

    /// <summary>Aim and shoot calls the rules refused.</summary>
    [Export] public int RejectedMoves = 0;

    /// <summary>Simulation steps taken (one per fixed tick; see <see cref="StepFrames"/>).</summary>
    [Export] public int Steps = 0;

    /// <summary>Seconds since the last reset: a monotonic FLOAT accumulator, never truncated.</summary>
    [Export] public float Elapsed = 0.0f;

    /// <summary>Frames processed since the last reset.</summary>
    [Export] public int Ticks = 0;

    /// <summary>Auto steps per second; 0 keeps the world still (the default).</summary>
    [Export] public float AutoClock = 0.0f;

    /// <summary>Steps the auto clock has applied over the whole game.</summary>
    [Export] public int AutoTicks = 0;

    /// <summary>Steps the auto clock applied on the LAST frame (0 while the clock is off).</summary>
    [Export] public int LastAutoSteps = 0;

    /// <summary>
    /// Steps the LAST <see cref="StepFrames"/> CALL applied. Its own property, and the clock never
    /// writes it (2048's r1 run, TASK-100 defect G1). Two producers, two properties.
    /// </summary>
    [Export] public int LastHookSteps = 0;

    /// <summary>Column the last <see cref="Probe"/> looked at.</summary>
    [Export] public int ProbeCol = -1;

    /// <summary>Row the last <see cref="Probe"/> looked at.</summary>
    [Export] public int ProbeRow = -1;

    /// <summary>Colour of the probed cell, -1 when it is empty.</summary>
    [Export] public int ProbeValue = -1;

    /// <summary>A readable name for the probed cell: outside / projectile / occupied / shooter / empty.</summary>
    [Export] public string ProbeState = "";

    /// <summary>When true the game reads its player's keyboard. The test driver switches this
    /// OFF explicitly (<see cref="SetPollInput"/>, <see cref="ForceTestState"/>) when it needs
    /// a frozen, deterministic state; the deterministic defaults live in AutoClock / AutoPlay /
    /// DriftSpeed, not here (TASK-116 defect D1).</summary>
    [Export] public bool PollInput = true;

    /// <summary>Shots that arrived through the declared input action.</summary>
    [Export] public int InputShots = 0;

    /// <summary>Aim steps that arrived through the declared pb_left / pb_right actions (TASK-116 D3).</summary>
    [Export] public int InputAims = 0;

    /// <summary>What the last hook did -- the readback string a session quotes.</summary>
    [Export] public string LastEvent = "";

    // --- private model -------------------------------------------------------------
    private int[] _board;
    private Label _hud;
    private Label _status;
    private readonly List<ColorRect> _cells = new List<ColorRect>();
    private readonly List<ColorRect> _decor = new List<ColorRect>();
    private ColorRect _projectile;
    private ColorRect _shooterSprite;
    private ColorRect _nextSprite;
    private readonly List<ColorRect> _aimDots = new List<ColorRect>();
    private float _autoAccum;
    private bool _prevShoot;
    private bool _prevAimLeft;
    private bool _prevAimRight;
    private const int MaxChain = 24;
    private const int AimDotCount = 6;
    private static readonly int[] AngleDc = { -2, -1, 0, 1, 2 };
    private static readonly int[] AngleDr = { -1, -1, -1, -1, -1 };
    private static readonly Color[] Palette =
    {
        new Color(0.95f, 0.30f, 0.35f),
        new Color(0.35f, 0.65f, 0.98f),
        new Color(0.40f, 0.90f, 0.45f),
        new Color(0.98f, 0.85f, 0.30f),
        new Color(0.75f, 0.45f, 0.95f),
        new Color(0.35f, 0.92f, 0.90f),
    };

    private static int NextSeed(int seed)
    {
        return (int)(((long)seed * 1103515245L + 12345L) & 0x7FFFFFFFL);
    }

    private int Idx(int col, int row)
    {
        return row * Cols + col;
    }

    private bool InGrid(int col, int row)
    {
        return col >= 0 && col < Cols && row >= 0 && row < Rows;
    }

    private bool Occupied(int col, int row)
    {
        return InGrid(col, row) && _board[Idx(col, row)] >= 0;
    }

    private int ColorAt(int col, int row)
    {
        return InGrid(col, row) ? _board[Idx(col, row)] : -1;
    }

    // --- the board ----------------------------------------------------------------

    /// <summary>Fills rows 0 .. <see cref="FillRows"/>-1 from the LCG, then removes every run of three.</summary>
    private void BuildInitialBoard()
    {
        _board = new int[Cols * Rows];
        for (var i = 0; i < _board.Length; i++)
        {
            _board[i] = -1;
        }
        var seed = InitSeed;
        for (var row = 0; row < FillRows; row++)
        {
            for (var col = 0; col < Cols; col++)
            {
                seed = NextSeed(seed);
                _board[Idx(col, row)] = (seed >> 16) % Colors;
            }
        }
        // Stabilise: a cell that completes a horizontal or vertical run of three is
        // bumped to the next colour until it completes none. Deterministic, and the
        // same loop runs in the Python second implementation.
        for (var row = 0; row < FillRows; row++)
        {
            for (var col = 0; col < Cols; col++)
            {
                var index = Idx(col, row);
                for (var attempt = 0; attempt < Colors; attempt++)
                {
                    var value = _board[index];
                    var bad = false;
                    if (col >= 2 && _board[index - 1] == value && _board[index - 2] == value)
                    {
                        bad = true;
                    }
                    if (row >= 2 && _board[index - Cols] == value && _board[index - 2 * Cols] == value)
                    {
                        bad = true;
                    }
                    if (!bad)
                    {
                        break;
                    }
                    _board[index] = (value + 1) % Colors;
                }
            }
        }
    }

    private void Recompute()
    {
        var builder = new StringBuilder();
        var hash = 0;
        var used = 0;
        for (var row = 0; row < Rows; row++)
        {
            if (row > 0)
            {
                builder.Append('/');
            }
            for (var col = 0; col < Cols; col++)
            {
                var value = _board[Idx(col, row)];
                builder.Append(value < 0 ? '.' : (char)('0' + value));
                hash = unchecked(hash * 31 + (value + 1));
                if (value >= 0)
                {
                    used++;
                }
            }
        }
        Board = builder.ToString();
        BoardHash = hash;
        BubblesInUse = used;
    }

    // --- the rules -----------------------------------------------------------------

    /// <summary>The 4-connected same-colour group that contains one cell (empty when the cell is empty).</summary>
    private List<int> FindGroup(int col, int row)
    {
        var result = new List<int>();
        if (!Occupied(col, row))
        {
            return result;
        }
        var color = ColorAt(col, row);
        var seen = new HashSet<int>();
        var stack = new Stack<int>();
        var start = Idx(col, row);
        stack.Push(start);
        seen.Add(start);
        int[] dc = { 1, -1, 0, 0 };
        int[] dr = { 0, 0, 1, -1 };
        while (stack.Count > 0)
        {
            var cell = stack.Pop();
            result.Add(cell);
            var cc = cell % Cols;
            var cr = cell / Cols;
            for (var k = 0; k < 4; k++)
            {
                var nc = cc + dc[k];
                var nr = cr + dr[k];
                if (!InGrid(nc, nr) || ColorAt(nc, nr) != color)
                {
                    continue;
                }
                var next = Idx(nc, nr);
                if (seen.Add(next))
                {
                    stack.Push(next);
                }
            }
        }
        return result;
    }

    /// <summary>Every occupied cell that is not connected to the ceiling row.</summary>
    private List<int> FloatingCells()
    {
        var reachable = new HashSet<int>();
        var stack = new Stack<int>();
        for (var col = 0; col < Cols; col++)
        {
            if (Occupied(col, 0))
            {
                var cell = Idx(col, 0);
                reachable.Add(cell);
                stack.Push(cell);
            }
        }
        int[] dc = { 1, -1, 0, 0 };
        int[] dr = { 0, 0, 1, -1 };
        while (stack.Count > 0)
        {
            var cell = stack.Pop();
            var cc = cell % Cols;
            var cr = cell / Cols;
            for (var k = 0; k < 4; k++)
            {
                var nc = cc + dc[k];
                var nr = cr + dr[k];
                if (!InGrid(nc, nr) || !Occupied(nc, nr))
                {
                    continue;
                }
                var next = Idx(nc, nr);
                if (reachable.Add(next))
                {
                    stack.Push(next);
                }
            }
        }
        var floating = new List<int>();
        for (var i = 0; i < _board.Length; i++)
        {
            if (_board[i] >= 0 && !reachable.Contains(i))
            {
                floating.Add(i);
            }
        }
        return floating;
    }

    /// <summary>
    /// Clears the attached group when it has three or more members, then lets every
    /// disconnected bubble fall -- one GENERATION at a time, each raising the chain.
    /// </summary>
    private void Resolve(int col, int row)
    {
        var chain = 0;
        var cleared = 0;
        var dropped = 0;
        var group = FindGroup(col, row);
        if (group.Count < 3)
        {
            LastChain = 0;
            LastCleared = 0;
            LastDropped = 0;
            LastAttachCol = col;
            LastAttachRow = row;
            LastEvent = $"attached at={col},{row} color={ColorAt(col, row)} chain=0 cleared=0 dropped=0";
            return;
        }
        chain = 1;
        cleared += group.Count;
        Score += group.Count * ClearScore * chain;
        foreach (var cell in group)
        {
            _board[cell] = -1;
        }
        var guard = 0;
        while (chain < MaxChain && guard++ < MaxChain)
        {
            var floating = FloatingCells();
            if (floating.Count == 0)
            {
                break;
            }
            // Only the bubbles that have nothing under them fall this generation; a
            // floating tower therefore falls one layer per generation.
            var layer = new List<int>();
            foreach (var cell in floating)
            {
                var cc = cell % Cols;
                var cr = cell / Cols;
                if (!Occupied(cc, cr + 1))
                {
                    layer.Add(cell);
                }
            }
            if (layer.Count == 0)
            {
                layer = floating;
            }
            chain++;
            dropped += layer.Count;
            Score += layer.Count * DropScore * chain;
            foreach (var cell in layer)
            {
                _board[cell] = -1;
            }
        }
        TotalCleared += cleared;
        TotalDropped += dropped;
        LastChain = chain;
        LastCleared = cleared;
        LastDropped = dropped;
        LastAttachCol = col;
        LastAttachRow = row;
        LastEvent = $"cleared at={col},{row} chain={chain} cleared={cleared} dropped={dropped} score={Score}";
    }

    /// <summary>Ends the game when a bubble rests at or below the failure line, and detects the win.</summary>
    private void CheckEnd()
    {
        if (GameOver)
        {
            return;
        }
        var lowest = -1;
        for (var row = 0; row < Rows; row++)
        {
            for (var col = 0; col < Cols; col++)
            {
                if (_board[Idx(col, row)] >= 0 && row > lowest)
                {
                    lowest = row;
                }
            }
        }
        if (lowest >= FailRow)
        {
            Failed = true;
            GameOver = true;
            Won = false;
            LastEvent = $"failed lowest_row={lowest} fail_row={FailRow} score={Score}";
            return;
        }
        if (lowest < 0)
        {
            Won = true;
            GameOver = true;
            LastEvent = $"cleared_board steps={Steps} shots={Shots} score={Score}";
        }
    }

    /// <summary>One fixed simulation step: the shot advances one cell, or attaches.</summary>
    private void Tick()
    {
        if (GameOver)
        {
            return;
        }
        Steps++;
        if (!ProjActive)
        {
            LastEvent = $"idle steps={Steps} shots={Shots}";
            return;
        }
        var dc = AngleDc[AngleIndex];
        var dr = AngleDr[AngleIndex];
        var nx = ProjCol + dc;
        var ny = ProjRow + dr;
        if (nx < 0 || nx >= Cols)
        {
            // the side wall reflects the shot
            dc = -dc;
            nx = ProjCol + dc;
        }
        if (ny < 0 || Occupied(nx, ny))
        {
            Attach();
            return;
        }
        ProjCol = nx;
        ProjRow = ny;
        LastEvent = $"flight at={ProjCol},{ProjRow} color={ProjColor} steps={Steps}";
    }

    /// <summary>Puts the shot on the board, resolves the match and the fall, then checks the end.</summary>
    private void Attach()
    {
        var col = ProjCol;
        var row = ProjRow;
        if (row < 0)
        {
            row = 0;
        }
        if (Occupied(col, row))
        {
            // the cell it came to rest on is taken: walk down until one is free
            var probe = row;
            while (probe < Rows && Occupied(col, probe))
            {
                probe++;
            }
            if (probe >= Rows)
            {
                ProjActive = false;
                LastEvent = $"rejected reason=no_room at={col},{row}";
                return;
            }
            row = probe;
        }
        _board[Idx(col, row)] = ProjColor;
        ProjActive = false;
        ProjCol = -1;
        ProjRow = -1;
        Resolve(col, row);
        CheckEnd();
        // the next bubble in the queue becomes the current one
        ShooterColor = NextColor;
        NextColor = (NextColor + 1) % Colors;
    }

    // --- nodes ---------------------------------------------------------------------

    private void FreeGenerated()
    {
        foreach (var list in new[] { _cells, _decor })
        {
            foreach (var node in list)
            {
                if (GodotObject.IsInstanceValid(node))
                {
                    node.GetParent()?.RemoveChild(node);
                    node.QueueFree();
                }
            }
            list.Clear();
        }
        foreach (var node in new[] { _projectile, _shooterSprite, _nextSprite })
        {
            if (node != null && GodotObject.IsInstanceValid(node))
            {
                node.GetParent()?.RemoveChild(node);
                node.QueueFree();
            }
        }
        _projectile = null;
        _shooterSprite = null;
        _nextSprite = null;
        foreach (var node in _aimDots)
        {
            if (GodotObject.IsInstanceValid(node))
            {
                node.GetParent()?.RemoveChild(node);
                node.QueueFree();
            }
        }
        _aimDots.Clear();
    }

    /// <summary>Builds the grid sprites, the failure line, the shooter and the projectile (all runtime-created).</summary>
    private void CreateNodes()
    {
        _hud = GetNodeOrNull<Label>("Hud");
        _status = GetNodeOrNull<Label>("Status");
        FreeGenerated();
        for (var row = 0; row < Rows; row++)
        {
            for (var col = 0; col < Cols; col++)
            {
                var rect = new ColorRect
                {
                    Name = $"Bubble_{row}_{col}",
                    Position = new Vector2(GridOffsetX + col * Cell + 2, GridOffsetY + row * Cell + 2),
                    Size = new Vector2(Cell - 4, Cell - 4),
                    Color = new Color(0.15f, 0.15f, 0.20f),
                    Visible = false,
                };
                AddChild(rect);
                _cells.Add(rect);
            }
        }
        var line = new ColorRect
        {
            Name = "FailLine",
            Position = new Vector2(GridOffsetX, GridOffsetY + FailRow * Cell),
            Size = new Vector2(Cols * Cell, 3),
            Color = new Color(0.90f, 0.25f, 0.25f, 0.85f),
        };
        AddChild(line);
        _decor.Add(line);
        var cellBar = new ColorRect
        {
            Name = "ShooterBar",
            Position = new Vector2(GridOffsetX, GridOffsetY + Rows * Cell),
            Size = new Vector2(Cols * Cell, 6),
            Color = new Color(0.35f, 0.38f, 0.45f),
        };
        AddChild(cellBar);
        _decor.Add(cellBar);
        _shooterSprite = new ColorRect
        {
            Name = "Shooter",
            Position = new Vector2(GridOffsetX + ShooterCol * Cell + 8, GridOffsetY + Rows * Cell + 14),
            Size = new Vector2(Cell - 16, Cell - 16),
            Color = Palette[ShooterColor % Palette.Length],
        };
        AddChild(_shooterSprite);
        _nextSprite = new ColorRect
        {
            Name = "NextBubble",
            Position = new Vector2(GridOffsetX + Cols * Cell + 16, GridOffsetY + Rows * Cell + 14),
            Size = new Vector2(Cell - 16, Cell - 16),
            Color = Palette[NextColor % Palette.Length],
        };
        AddChild(_nextSprite);
        _projectile = new ColorRect
        {
            Name = "Projectile",
            Position = new Vector2(GridOffsetX + 8, GridOffsetY + 8),
            Size = new Vector2(Cell - 16, Cell - 16),
            Color = Palette[0],
            Visible = false,
        };
        AddChild(_projectile);
        // TASK-133 §1.A.4: the AIM INDICATOR. `pb_left`/`pb_right` only changed the
        // `AngleIndex` property, so a player could not see where the shot would go and a
        // pixel diff over an aim press was exactly 0 (recorded in TASK-131: P2 red, the
        // criterion deliberately NOT relaxed). These dots trace the same integer ray
        // `Tick()` walks -- same `AngleDc`/`AngleDr` table, same side-wall reflection --
        // so what is drawn is what a fired bubble actually does, not an approximation.
        for (var i = 0; i < AimDotCount; i++)
        {
            var dot = new ColorRect
            {
                Name = $"AimDot{i}",
                Size = new Vector2(14, 14),
                Color = new Color(1.0f, 1.0f, 1.0f, 0.55f),
                Visible = false,
            };
            AddChild(dot);
            _aimDots.Add(dot);
        }
    }

    /// <summary>
    /// The grid cells the next shot would occupy, in order, starting one step away from
    /// the shooter -- the same walk <see cref="Tick"/> performs (one cell per step, side
    /// walls reflect) with no projectile state written.
    /// </summary>
    private List<int> AimPath()
    {
        var outPath = new List<int>();
        if (GameOver || ProjActive)
        {
            return outPath;
        }
        var dc = AngleDc[AngleIndex];
        var dr = AngleDr[AngleIndex];
        var col = ShooterCol;
        var row = Rows - 1;
        for (var step = 0; step < AimDotCount; step++)
        {
            col += dc;
            row += dr;
            if (col < 0 || col >= Cols)
            {
                dc = -dc;
                col += 2 * dc;
            }
            if (row < 0 || Occupied(col, row))
            {
                break;
            }
            outPath.Add(Idx(col, row));
        }
        return outPath;
    }

    /// <summary>
    /// Paints the aim dots (or hides them while a shot is in the air / the game is over).
    /// Called from <see cref="ApplyBoard"/>, so an aim change is on screen in the same
    /// frame the property changed.
    /// </summary>
    private void ApplyAimIndicator()
    {
        var path = AimPath();
        for (var i = 0; i < _aimDots.Count; i++)
        {
            var dot = _aimDots[i];
            if (dot == null || !GodotObject.IsInstanceValid(dot))
            {
                continue;
            }
            if (i >= path.Count)
            {
                dot.Visible = false;
                continue;
            }
            var col = path[i] % Cols;
            var row = path[i] / Cols;
            dot.Position = new Vector2(GridOffsetX + col * Cell + 13, GridOffsetY + row * Cell + 13);
            dot.Color = new Color(Palette[ShooterColor % Palette.Length].R,
                                  Palette[ShooterColor % Palette.Length].G,
                                  Palette[ShooterColor % Palette.Length].B, 0.75f);
            dot.Visible = true;
        }
    }

    /// <summary>Puts every sprite where the model says it is, and rewrites the HUD.</summary>
    private void ApplyBoard()
    {
        for (var row = 0; row < Rows; row++)
        {
            for (var col = 0; col < Cols; col++)
            {
                var index = Idx(col, row);
                var rect = _cells[index];
                var value = _board[index];
                rect.Visible = value >= 0;
                if (value >= 0)
                {
                    rect.Color = Palette[value % Palette.Length];
                }
            }
        }
        if (_projectile != null)
        {
            _projectile.Visible = ProjActive;
            if (ProjActive)
            {
                _projectile.Position = new Vector2(GridOffsetX + ProjCol * Cell + 8,
                                                   GridOffsetY + ProjRow * Cell + 8);
                _projectile.Color = Palette[ProjColor % Palette.Length];
            }
        }
        if (_shooterSprite != null)
        {
            _shooterSprite.Color = Palette[ShooterColor % Palette.Length];
            _shooterSprite.Position = new Vector2(GridOffsetX + ShooterCol * Cell + 8,
                                                  GridOffsetY + Rows * Cell + 14);
        }
        if (_nextSprite != null)
        {
            _nextSprite.Color = Palette[NextColor % Palette.Length];
        }
        ApplyAimIndicator();
        if (_hud != null)
        {
            _hud.Text = $"SHOT {Shots}  COLOR {ShooterColor}  NEXT {NextColor}  ANGLE {AngleIndex}  "
                        + $"BUBBLES {BubblesInUse}  CLEARED {TotalCleared}  DROPPED {TotalDropped}  SCORE {Score}";
        }
        if (_status != null)
        {
            _status.Text = GameOver ? (Won ? "BOARD CLEARED" : "FAIL LINE REACHED") : "AIM AND FIRE";
        }
    }

    public override void _Ready()
    {
        BuildInitialBoard();
        CreateNodes();
        Recompute();
        ApplyBoard();
        GD.Print($"PUZZLEBOBBLE_READY name={Name} board_hash={BoardHash} bubbles={BubblesInUse}");
    }

    private void ResetCounters()
    {
        BuildInitialBoard();
        Score = 0;
        Shots = 0;
        TotalCleared = 0;
        TotalDropped = 0;
        LastChain = 0;
        LastCleared = 0;
        LastDropped = 0;
        LastAttachCol = -1;
        LastAttachRow = -1;
        Failed = false;
        Won = false;
        GameOver = false;
        ShooterCol = Cols / 2;
        ShooterColor = 0;
        NextColor = 1 % Colors;
        AngleIndex = 2;
        ProjActive = false;
        ProjCol = -1;
        ProjRow = -1;
        ProjColor = -1;
        Moves = 0;
        RejectedMoves = 0;
        Steps = 0;
        Elapsed = 0.0f;
        Ticks = 0;
        AutoClock = 0.0f;
        AutoTicks = 0;
        LastAutoSteps = 0;
        LastHookSteps = 0;
        _autoAccum = 0.0f;
        // TASK-116 D1: was `PollInput = false;` -- that is what
        // switched player input off again right after _Ready() ran.
        // The deterministic entry point is ForceTestState / SetPollInput.
        InputShots = 0;
        _prevShoot = false;
        ProbeCol = -1;
        ProbeRow = -1;
        ProbeValue = -1;
        ProbeState = "";
        LastEvent = "reset";
    }

    // --- the public surface a session drives -----------------------------------------

    /// <summary>
    /// Runs <paramref name="steps"/> fixed simulation steps. The hook, and the only frame-rate
    /// independent way to advance the world: <see cref="LastHookSteps"/> is its own property.
    /// </summary>
    public string StepFrames(int steps)
    {
        var applied = 0;
        for (var i = 0; i < steps; i++)
        {
            if (GameOver)
            {
                break;
            }
            Tick();
            applied++;
        }
        LastHookSteps = applied;
        Recompute();
        ApplyBoard();
        LastEvent = $"stepframes requested={steps} applied={applied} steps={Steps} in_flight={ProjActive} "
                    + $"proj={ProjCol},{ProjRow} bubbles={BubblesInUse} score={Score} chain={LastChain} "
                    + $"cleared={TotalCleared} dropped={TotalDropped} over={GameOver} won={Won} failed={Failed}";
        return LastEvent;
    }

    /// <summary>
    /// Sets one of the five integer aim directions, clamped to the table.
    ///
    /// <para><b>TASK-133 §1.A.4: the aim is now VISIBLE, and it WRAPS.</b> Two changes,
    /// both required by the measured defect (<c>pb_left</c>/<c>pb_right</c> changed only
    /// the <c>AngleIndex</c> property, pixel diff 0):</para>
    ///
    /// <list type="number">
    /// <item>the call repaints (<see cref="ApplyBoard"/> -> <see cref="ApplyAimIndicator"/>),
    /// so the aim dots move on the frame the angle changed instead of waiting for the next
    /// shot -- a player can see where the bubble will go, which is the whole point of an
    /// aim control;</item>
    /// <item>the five-entry table is a CYCLE: aiming left at the steepest-left entry
    /// wraps to the steepest-right one (and vice versa) instead of being silently dropped.
    /// The old clamp recorded such a press as a refusal and moved nothing, which meant the
    /// control had a dead stop at each end and the usability gate correctly saw a
    /// meta-only action. <see cref="Aim"/> called with an out-of-range index still clamps
    /// (that is the programmatic hook's contract); the keyboard path walks the cycle.</item>
    /// </list>
    /// </summary>
    public string Aim(int index)
    {
        if (GameOver)
        {
            RejectedMoves++;
            LastEvent = $"rejected reason=game_over aim={index}";
            return LastEvent;
        }
        // a relative step (the keyboard path's press edge) crosses the ends; an absolute
        // index is clamped exactly as before
        var stepped = index < 0 || index >= AngleDc.Length;
        var value = index;
        if (value < 0)
        {
            value = AngleDc.Length - 1;
        }
        if (value >= AngleDc.Length)
        {
            value = 0;
        }
        if (value == AngleIndex && !stepped)
        {
            RejectedMoves++;
            LastEvent = $"rejected reason=same_angle aim={index}";
            return LastEvent;
        }
        AngleIndex = value;
        Moves++;
        Recompute();
        ApplyBoard();
        LastEvent = $"aim={AngleIndex} dc={AngleDc[AngleIndex]} dr={AngleDr[AngleIndex]}";
        return LastEvent;
    }

    /// <summary>Fires the shooter's bubble: it starts in the shooter's cell and moves one cell per step.</summary>
    public string Shoot()
    {
        if (GameOver)
        {
            RejectedMoves++;
            LastEvent = $"rejected reason=game_over shots={Shots}";
            return LastEvent;
        }
        if (ProjActive)
        {
            RejectedMoves++;
            LastEvent = $"rejected reason=in_flight at={ProjCol},{ProjRow} shots={Shots}";
            return LastEvent;
        }
        ProjActive = true;
        ProjColor = ShooterColor;
        ProjCol = ShooterCol;
        ProjRow = Rows - 1;
        Shots++;
        LastChain = 0;
        LastCleared = 0;
        LastDropped = 0;
        LastAttachCol = -1;
        LastAttachRow = -1;
        Recompute();
        ApplyBoard();
        LastEvent = $"shot color={ProjColor} from={ProjCol},{ProjRow} angle={AngleIndex} shots={Shots}";
        return LastEvent;
    }

    /// <summary>Records what stands on one board cell into the Probe* properties, so an assert can name it.</summary>
    public string Probe(int col, int row)
    {
        ProbeCol = col;
        ProbeRow = row;
        ProbeValue = -1;
        if (!InGrid(col, row))
        {
            ProbeState = "outside";
        }
        else if (ProjActive && ProjCol == col && ProjRow == row)
        {
            ProbeState = "projectile";
            ProbeValue = ProjColor;
        }
        else if (_board[Idx(col, row)] >= 0)
        {
            ProbeState = "occupied";
            ProbeValue = _board[Idx(col, row)];
        }
        else if (col == ShooterCol && row == Rows - 1)
        {
            ProbeState = "shooter";
        }
        else
        {
            ProbeState = "empty";
        }
        LastEvent = $"probe at={col},{row} state={ProbeState} value={ProbeValue}";
        return LastEvent;
    }

    /// <summary>Steps per second; 0 keeps the world still (the default).</summary>
    public string SetAutoClock(float perSecond)
    {
        AutoClock = perSecond;
        _autoAccum = 0.0f;
        LastAutoSteps = 0;
        LastEvent = $"auto_clock={AutoClock}";
        GD.Print($"PUZZLEBOBBLE_AUTO auto={AutoClock}");
        return LastEvent;
    }

    /// <summary>Switches the declared-input polling on or off (the default is off).</summary>
    public string SetPollInput(bool enabled)
    {
        PollInput = enabled;
        _prevShoot = false;
        _prevAimLeft = false;
        _prevAimRight = false;
        LastEvent = $"poll_input={PollInput}";
        return LastEvent;
    }

    private void HandleInput()
    {
        var shoot = Input.IsActionPressed("pb_shoot");
        // Press edges only: a key a scenario injected and never released fires exactly one shot.
        if (shoot && !_prevShoot && !GameOver && !ProjActive)
        {
            Shoot();
            InputShots++;
        }
        _prevShoot = shoot;
        // TASK-116 (defect D3): without aim there is no game -- the shooter had no way to
        // choose a direction, so every bubble flew at the same angle. Press edges again, so
        // a held key walks the five-entry aim table one step at a time instead of jumping.
        var aimLeft = Input.IsActionPressed("pb_left");
        if (aimLeft && !_prevAimLeft && !GameOver)
        {
            Aim(AngleIndex - 1);
            InputAims++;
        }
        _prevAimLeft = aimLeft;
        var aimRight = Input.IsActionPressed("pb_right");
        if (aimRight && !_prevAimRight && !GameOver)
        {
            Aim(AngleIndex + 1);
            InputAims++;
        }
        _prevAimRight = aimRight;
    }

    public override void _Process(double delta)
    {
        var dt = (float)delta;
        Ticks++;
        Elapsed += dt; // a float accumulator: this clock is never truncated
        if (GameOver)
        {
            LastAutoSteps = 0;
            return;
        }
        if (PollInput)
        {
            HandleInput();
        }
        if (AutoClock > 0.0f)
        {
            _autoAccum += dt * AutoClock; // F-1's fix: accumulate, never (int)(delta * rate)
            var applied = 0;
            var guard = 0;
            while (_autoAccum >= 1.0f && guard < 8)
            {
                _autoAccum -= 1.0f;
                guard++;
                Tick();
                applied++;
                if (GameOver)
                {
                    break;
                }
            }
            AutoTicks += applied;
            LastAutoSteps = applied;
            if (applied > 0)
            {
                // The clock deliberately does NOT touch LastHookSteps (the G1 lesson).
                Recompute();
                ApplyBoard();
            }
        }
        else
        {
            LastAutoSteps = 0;
        }
    }

    /// <summary>Every exported fact on one line.</summary>
    public string Dump()
    {
        return $"cols={Cols} rows={Rows} cell={Cell} colors={Colors} fail_row={FailRow} "
               + $"fill_rows={FillRows} seed={InitSeed} board={Board} board_hash={BoardHash} "
               + $"bubbles={BubblesInUse} shooter={ShooterCol} color={ShooterColor} next={NextColor} "
               + $"angle={AngleIndex} proj_active={ProjActive} proj={ProjCol},{ProjRow} "
               + $"proj_color={ProjColor} score={Score} shots={Shots} cleared={TotalCleared} "
               + $"dropped={TotalDropped} last_chain={LastChain} last_cleared={LastCleared} "
               + $"last_dropped={LastDropped} attach={LastAttachCol},{LastAttachRow} failed={Failed} "
               + $"won={Won} over={GameOver} moves={Moves} rejected={RejectedMoves} steps={Steps} "
               + $"auto={AutoClock} auto_ticks={AutoTicks} last_auto={LastAutoSteps} "
               + $"last_hook={LastHookSteps} input_shots={InputShots} elapsed={Elapsed:F3} "
               + $"ticks={Ticks} last={LastEvent}";
    }

    /// <summary>
    /// Writes the whole deterministic state in one call. Recognised keys (semicolon separated,
    /// <c>key=value</c>):
    ///
    /// <list type="bullet">
    /// <item><c>board=...</c> -- <see cref="Rows"/> rows of <see cref="Cols"/> characters joined by
    /// <c>|</c>, <c>.</c> for empty and a digit for a colour. This is what makes every rule test a
    /// statement about a board the session itself chose.</item>
    /// <item><c>color=N</c>, <c>next=N</c>, <c>angle=N</c>, <c>score=N</c>.</item>
    /// </list>
    ///
    /// <para>The auto clock and input polling are switched OFF first, so a session's aim and the next
    /// readback are the same fact (TASK-103's TD-1 lesson: every test段 starts from its own force).</para>
    /// </summary>
    public string ForceTestState(string spec)
    {
        ResetCounters();
        foreach (var part in spec.Split(';'))
        {
            var kv = part.Split(new[] { '=' }, 2);
            if (kv.Length != 2)
            {
                continue;
            }
            switch (kv[0])
            {
                case "board":
                    if (kv[1].Length > 0)
                    {
                        for (var i = 0; i < _board.Length; i++)
                        {
                            _board[i] = -1;
                        }
                        var rows = kv[1].Split('|');
                        for (var row = 0; row < rows.Length && row < Rows; row++)
                        {
                            var text = rows[row];
                            for (var col = 0; col < text.Length && col < Cols; col++)
                            {
                                var ch = text[col];
                                _board[Idx(col, row)] = ch == '.' ? -1 : ch - '0';
                            }
                        }
                    }
                    break;
                case "color":
                    ShooterColor = int.Parse(kv[1]);
                    break;
                case "next":
                    NextColor = int.Parse(kv[1]);
                    break;
                case "angle":
                    var angle = int.Parse(kv[1]);
                    AngleIndex = angle < 0 ? 0 : angle >= AngleDc.Length ? AngleDc.Length - 1 : angle;
                    break;
                case "score":
                    Score = int.Parse(kv[1]);
                    break;
            }
        }
        Recompute();
        ApplyBoard();
        LastEvent = $"forced bubbles={BubblesInUse} board_hash={BoardHash} color={ShooterColor} "
                    + $"next={NextColor} angle={AngleIndex} score={Score}";
        return LastEvent;
    }
}
