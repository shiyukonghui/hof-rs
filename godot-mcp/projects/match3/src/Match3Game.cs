using Godot;
using System.Collections.Generic;
using System.Text;

namespace match3;

/// <summary>
/// Match-3 -- the fifteenth C# game of the godot-mcp series (TASK-102, DECISIONS.md D138).
///
/// <para><b>Design rule</b> (inherited from the fourteen games before it): every fact the evidence
/// model needs is a real Godot property on the root node -- <see cref="Board"/>,
/// <see cref="BoardHash"/>, <see cref="Moves"/>, <see cref="RejectedMoves"/>, <see cref="Score"/>,
/// <see cref="LastChain"/>, <see cref="MaxChain"/>, <see cref="LastCleared"/>,
/// <see cref="TotalCleared"/>, <see cref="Refills"/>, <see cref="Won"/>, <see cref="GameOver"/>,
/// <see cref="Elapsed"/>, <see cref="Ticks"/>. A session asserts these with
/// <c>running_game_assert_node_state</c>; it never parses a log line.</para>
///
/// <para><b>A pure function of a board and a seed.</b> The whole world is
/// <see cref="ForceTestState"/> (the 8x8 board, the seed, the score) plus the swaps a session makes.
/// Nothing moves on its own: <see cref="AutoClock"/> is 0 and <see cref="PollInput"/> is false by
/// default. The refill gems come from a linear congruential generator
/// (<c>seed = (seed * 1103515245 + 12345) mod 2^31</c>, colour <c>= (seed &gt;&gt; 16) % Colours</c>),
/// so the board after a cascade is exactly reproducible -- by this payload and by a second
/// implementation of the same rule in Python.</para>
///
/// <para><b>Frame-rate independence (the F-1 lesson).</b> The auto clock is a FLOAT ACCUMULATOR
/// (<c>_autoAccum += delta * AutoClock</c>), never <c>(int)(delta * rate)</c>. Two producers, two
/// properties: <see cref="LastAutoSteps"/> is what the clock applied on the last frame and
/// <see cref="LastHookSteps"/> is what the last <see cref="AutoStep"/> CALL applied. 2048's r1 run
/// (TASK-100, defect G1) proved a single property read by both producers reads the wrong number.
/// <see cref="Elapsed"/> is a monotonic float second counter that is never truncated.</para>
///
/// <para><b>Rules.</b> <see cref="Swap"/> exchanges two orthogonally adjacent cells. If the swap
/// makes no line of three or more it is REFUSED: <see cref="RejectedMoves"/> grows and the board is
/// put back exactly as it was. Otherwise the swap is applied and the cascade resolves: every line of
/// three or more is cleared, the gems above fall into the gaps, fresh gems are generated from the top,
/// and the whole thing repeats while the new board still has a line (a chain). Chain n scores
/// <c>10 * cleared * n</c>, so a cascade is worth more than the sum of its clears.
/// <see cref="Target"/> points ends the game in a win; running out of <see cref="MovesLimit"/> moves
/// without reaching it ends it as a loss.</para>
///
/// <para><b>All gems are runtime-created.</b> <see cref="_Ready"/> builds one <c>ColorRect</c> per
/// cell (8x8); the scene file carries only the three static nodes (Background, Hud, Status). That
/// keeps the edited scene small, keeps it immune to the D-3 duplicate-name trap, and makes "a node
/// created at run time really is drawn" part of this game's own evidence.</para>
/// </summary>
public partial class Match3Game : Node2D
{
    // --- the grid ---------------------------------------------------------------
    /// <summary>Columns of the board.</summary>
    [Export] public int Cols = 8;

    /// <summary>Rows of the board.</summary>
    [Export] public int Rows = 8;

    /// <summary>How many different gems exist.</summary>
    [Export] public int Colors = 6;

    /// <summary>Side of one cell in pixels.</summary>
    [Export] public int Cell = 56;

    /// <summary>Left edge of the board in pixels.</summary>
    [Export] public int OriginX = 176;

    /// <summary>Top edge of the board in pixels.</summary>
    [Export] public int OriginY = 76;

    /// <summary>Index of the level currently loaded (the board catalogues are not used; kept for parity).</summary>
    [Export] public int LevelIndex = 0;

    /// <summary>Points one cleared gem is worth (times the chain index).</summary>
    [Export] public int PointsPerGem = 10;

    /// <summary>Score at which the board is cleared.</summary>
    [Export] public int Target = 500;

    /// <summary>Moves available before the game is lost.</summary>
    [Export] public int MovesLimit = 30;

    // --- observable state, all of it a real Godot property ----------------------
    /// <summary>The board as <c>"row/row/..."</c>, one digit per cell, 0..Colours-1.</summary>
    [Export] public string Board = "";

    /// <summary>A stable hash of the board -- a sample can watch it change.</summary>
    [Export] public int BoardHash = 0;

    /// <summary>The seed the refill generator is at right now.</summary>
    [Export] public int Seed = 12345;

    /// <summary>Gems generated from the top so far.</summary>
    [Export] public int Refills = 0;

    /// <summary>Swaps accepted (a swap that made a line).</summary>
    [Export] public int Moves = 0;

    /// <summary>Swaps refused: no line, not adjacent, out of bounds, or a finished game.</summary>
    [Export] public int RejectedMoves = 0;

    /// <summary>Points: 10 per cleared gem, times the chain index it was cleared in.</summary>
    [Export] public int Score = 0;

    /// <summary>Gems cleared by the most recent cascade.</summary>
    [Export] public int LastCleared = 0;

    /// <summary>Gems cleared over the whole game.</summary>
    [Export] public int TotalCleared = 0;

    /// <summary>Links of the most recent cascade (1 = a plain match, 3 = two follow-on waves).</summary>
    [Export] public int LastChain = 0;

    /// <summary>The longest cascade of the game.</summary>
    [Export] public int MaxChain = 0;

    /// <summary>Cascades resolved over the whole game (one per accepted swap).</summary>
    [Export] public int Cascades = 0;

    /// <summary>The most recent swap as <c>"r1,c1&gt;r2,c2"</c>.</summary>
    [Export] public string LastSwap = "";

    /// <summary>True when the score reached the target.</summary>
    [Export] public bool Won = false;

    /// <summary>True when the board ended, by the target or by running out of moves.</summary>
    [Export] public bool GameOver = false;

    /// <summary>Row the last <see cref="ProbeCell"/> looked at.</summary>
    [Export] public int ProbeRow = -1;

    /// <summary>Column the last <see cref="ProbeCell"/> looked at.</summary>
    [Export] public int ProbeCol = -1;

    /// <summary>Gem colour at the probed cell, -1 for empty.</summary>
    [Export] public int ProbeValue = -1;

    /// <summary>A readable name for the probed cell.</summary>
    [Export] public string ProbeState = "";

    /// <summary>Seconds since the last reset: a monotonic FLOAT accumulator, never truncated.</summary>
    [Export] public float Elapsed = 0.0f;

    /// <summary>Auto steps per second; 0 keeps the board still (the default).</summary>
    [Export] public float AutoClock = 0.0f;

    /// <summary>Steps the auto clock has applied over the whole game.</summary>
    [Export] public int AutoTicks = 0;

    /// <summary>Steps the auto clock applied on the LAST frame (0 while the clock is off).</summary>
    [Export] public int LastAutoSteps = 0;

    /// <summary>
    /// Steps the LAST <see cref="AutoStep"/> CALL applied. Its own property, and the clock never
    /// writes it: 2048's r1 run (TASK-100, defect G1) found that one property used by two producers
    /// reads 0 by the time the assertion runs, because the next frame's clock pass overwrites it.
    /// Two producers, two properties.
    /// </summary>
    [Export] public int LastHookSteps = 0;

    /// <summary>When true the game reads its player's keyboard. The test driver switches this
    /// OFF explicitly (<see cref="SetPollInput"/>, <see cref="ForceTestState"/>) when it needs
    /// a frozen, deterministic state; the deterministic defaults live in AutoClock / AutoPlay /
    /// DriftSpeed, not here (TASK-116 defect D1).</summary>
    [Export] public bool PollInput = true;

    /// <summary>Auto moves that arrived through the declared input action.</summary>
    [Export] public int InputMoves = 0;

    /// <summary>Board row the player's keyboard cursor is on (TASK-116 D3). Drawn into the HUD
    /// (`CURSOR r,c`) so the player can see where a swap would happen.</summary>
    [Export] public int CursorRow = 0;

    /// <summary>Board column the player's keyboard cursor is on (TASK-116 D3).</summary>
    [Export] public int CursorCol = 0;

    /// <summary>Cursor moves and swaps that arrived through the declared input actions.</summary>
    [Export] public int InputCursors = 0;

    /// <summary>Swaps that arrived through the declared `m3_swap` action.</summary>
    [Export] public int InputSwaps = 0;

    /// <summary>Of those, the ones the game refused (no line of three) -- a refusal still proves
    /// the key was read, which is what the playability gate asks about.</summary>
    [Export] public int InputRejectedSwaps = 0;

    /// <summary>Frames processed since the last reset.</summary>
    [Export] public int Ticks = 0;

    /// <summary>What the last hook did -- the readback string a session quotes.</summary>
    [Export] public string LastEvent = "";

    // --- private model ---------------------------------------------------------
    private int[] _cell = new int[1];
    private readonly List<ColorRect> _cellRect = new List<ColorRect>();
    private Label _hud;
    private Label _status;
    private float _autoAccum;
    private bool _prevMove;
    private bool _prevUp;
    private bool _prevDown;
    private bool _prevLeft;
    private bool _prevRight;
    private bool _prevSwap;
    private readonly List<int> _matches = new List<int>();

    private static readonly Color[] Palette =
    {
        new Color(0.95f, 0.30f, 0.35f), // 0 red
        new Color(0.30f, 0.80f, 0.40f), // 1 green
        new Color(0.35f, 0.55f, 0.95f), // 2 blue
        new Color(0.98f, 0.78f, 0.25f), // 3 yellow
        new Color(0.75f, 0.40f, 0.90f), // 4 purple
        new Color(0.30f, 0.85f, 0.85f), // 5 cyan
    };

    private int Idx(int row, int col)
    {
        return row * Cols + col;
    }

    private bool InBounds(int row, int col)
    {
        return row >= 0 && row < Rows && col >= 0 && col < Cols;
    }

    public override void _Ready()
    {
        _hud = GetNodeOrNull<Label>("Hud");
        _status = GetNodeOrNull<Label>("Status");
        BuildBoard();
        ResetCounters();
        CreateNodes();
        Recompute();
        ApplyBoard();
        UpdateHud();
        GD.Print($"MATCH3_READY cols={Cols} rows={Rows} colors={Colors} target={Target} "
                 + $"move_limit={MovesLimit} seed={Seed} auto={AutoClock} poll={PollInput}");
    }

    // --- the board --------------------------------------------------------------
    private void BuildBoard()
    {
        var total = Cols * Rows;
        _cell = new int[total];
        // The default board is generated from the seed too, so it is reproducible: a session
        // normally pins its own with ForceTestState.
        Seed = 12345;
        for (var i = 0; i < total; i++)
        {
            _cell[i] = NextGem();
        }
        // A generated board may already contain lines; clear them without scoring so the default
        // board starts quiet.
        var guard = 0;
        while (FindMatches() > 0 && guard < 64)
        {
            foreach (var index in _matches)
            {
                _cell[index] = -1;
            }
            Collapse();
            guard++;
        }
    }

    private int NextGem()
    {
        unchecked
        {
            Seed = (int)(((long)Seed * 1103515245 + 12345) & 0x7FFFFFFF);
        }
        return (Seed >> 16) % Colors;
    }

    /// <summary>
    /// Fills <see cref="_matches"/> with every cell that is part of a horizontal or vertical run of
    /// three or more equal gems, and returns the count.
    /// </summary>
    private int FindMatches()
    {
        _matches.Clear();
        var flag = new bool[Cols * Rows];
        // horizontal runs
        for (var r = 0; r < Rows; r++)
        {
            var c = 0;
            while (c < Cols)
            {
                var value = _cell[Idx(r, c)];
                var run = 1;
                while (c + run < Cols && _cell[Idx(r, c + run)] == value)
                {
                    run++;
                }
                if (value >= 0 && run >= 3)
                {
                    for (var k = 0; k < run; k++)
                    {
                        flag[Idx(r, c + k)] = true;
                    }
                }
                c += run;
            }
        }
        // vertical runs
        for (var c = 0; c < Cols; c++)
        {
            var r = 0;
            while (r < Rows)
            {
                var value = _cell[Idx(r, c)];
                var run = 1;
                while (r + run < Rows && _cell[Idx(r + run, c)] == value)
                {
                    run++;
                }
                if (value >= 0 && run >= 3)
                {
                    for (var k = 0; k < run; k++)
                    {
                        flag[Idx(r + k, c)] = true;
                    }
                }
                r += run;
            }
        }
        for (var i = 0; i < flag.Length; i++)
        {
            if (flag[i])
            {
                _matches.Add(i);
            }
        }
        return _matches.Count;
    }

    /// <summary>Lets the gems above every gap fall down, then fills the top gaps with fresh gems.</summary>
    private void Collapse()
    {
        for (var c = 0; c < Cols; c++)
        {
            var write = Rows - 1;
            for (var r = Rows - 1; r >= 0; r--)
            {
                var value = _cell[Idx(r, c)];
                if (value >= 0)
                {
                    _cell[Idx(write, c)] = value;
                    if (write != r)
                    {
                        _cell[Idx(r, c)] = -1;
                    }
                    write--;
                }
            }
            for (var r = write; r >= 0; r--)
            {
                _cell[Idx(r, c)] = NextGem();
                Refills++;
            }
        }
    }

    /// <summary>Runs the cascade out: clear, fall, refill, repeat. Returns the chain length.</summary>
    private int ResolveCascade()
    {
        var chain = 0;
        var cleared = 0;
        var guard = 0;
        while (FindMatches() > 0 && guard < 64)
        {
            guard++;
            chain++;
            var count = _matches.Count;
            cleared += count;
            // one line of three is worth a line of three; the chain index multiplies it
            Score += PointsPerGem * count * chain;
            foreach (var index in _matches)
            {
                _cell[index] = -1;
            }
            Collapse();
        }
        LastChain = chain;
        LastCleared = cleared;
        TotalCleared += cleared;
        if (chain > MaxChain)
        {
            MaxChain = chain;
        }
        if (chain > 0)
        {
            Cascades++;
        }
        return chain;
    }

    private void Recompute()
    {
        var sb = new StringBuilder();
        var hash = 17;
        unchecked
        {
            for (var r = 0; r < Rows; r++)
            {
                for (var c = 0; c < Cols; c++)
                {
                    var v = _cell[Idx(r, c)];
                    sb.Append(v < 0 ? '-' : (char)('0' + v));
                    hash = hash * 31 + (v + 1);
                }
                if (r + 1 < Rows)
                {
                    sb.Append('/');
                }
            }
        }
        Board = sb.ToString();
        BoardHash = hash;
        Won = Score >= Target;
        GameOver = Won || Moves >= MovesLimit;
    }

    // --- rendering --------------------------------------------------------------
    private void ApplyBoard()
    {
        for (var r = 0; r < Rows; r++)
        {
            for (var c = 0; c < Cols; c++)
            {
                var index = Idx(r, c);
                if (index >= _cellRect.Count)
                {
                    continue;
                }
                var rect = _cellRect[index];
                if (rect == null || !IsInstanceValid(rect))
                {
                    continue;
                }
                var value = _cell[index];
                rect.Visible = value >= 0;
                if (value >= 0)
                {
                    rect.Color = Palette[value % Palette.Length];
                }
            }
        }
    }

    private void UpdateHud()
    {
        if (_hud != null)
        {
            _hud.Text = $"TARGET {Target}  SCORE {Score}  MOVES {Moves}/{MovesLimit}  "
                        + $"CHAIN {LastChain}  CLEARED {TotalCleared}  "
                        + $"CURSOR {CursorRow},{CursorCol}";
            // TASK-116 (D3): the cursor is part of the HUD on purpose. The board is drawn with
            // _Draw and a selection rectangle would be invisible against it; putting the cursor
            // in the text line is the smallest change that makes it *visible to the player*.
        }
        if (_status != null)
        {
            if (Won)
            {
                _status.Text = "TARGET REACHED";
            }
            else if (GameOver)
            {
                _status.Text = "OUT OF MOVES";
            }
            else
            {
                _status.Text = "MATCH AND CLEAR";
            }
        }
    }

    private ColorRect NewCell(int r, int c)
    {
        var rect = new ColorRect();
        rect.Name = $"Gem_{r}_{c}";
        rect.Position = new Vector2(OriginX + c * Cell + 3, OriginY + r * Cell + 3);
        rect.Size = new Vector2(Cell - 6, Cell - 6);
        AddChild(rect);
        return rect;
    }

    private void CreateNodes()
    {
        // RemoveChild BEFORE QueueFree: a node queued for deletion still holds its name for the rest
        // of the frame, and re-adding a child with the same name makes the engine rename the new one
        // to "@ColorRect@N" (the Pac-Man lesson from TASK-098, the same trap D-3 was about).
        foreach (var rect in _cellRect)
        {
            if (rect != null && IsInstanceValid(rect))
            {
                RemoveChild(rect);
                rect.QueueFree();
            }
        }
        _cellRect.Clear();
        for (var r = 0; r < Rows; r++)
        {
            for (var c = 0; c < Cols; c++)
            {
                _cellRect.Add(NewCell(r, c));
            }
        }
    }

    // --- hooks the session drives ----------------------------------------------

    private bool MakesLine(int r1, int c1, int r2, int c2)
    {
        var a = _cell[Idx(r1, c1)];
        _cell[Idx(r1, c1)] = _cell[Idx(r2, c2)];
        _cell[Idx(r2, c2)] = a;
        var found = FindMatches() > 0;
        a = _cell[Idx(r1, c1)];
        _cell[Idx(r1, c1)] = _cell[Idx(r2, c2)];
        _cell[Idx(r2, c2)] = a;
        return found;
    }

    /// <summary>
    /// Exchanges two orthogonally adjacent cells. A swap that makes no line of three is refused and
    /// the board is put back exactly as it was; otherwise the cascade resolves.
    /// </summary>
    public string Swap(int r1, int c1, int r2, int c2)
    {
        if (!InBounds(r1, c1) || !InBounds(r2, c2))
        {
            RejectedMoves++;
            LastEvent = $"rejected reason=out_of_bounds from={r1},{c1} to={r2},{c2} "
                        + $"rejected={RejectedMoves}";
            return LastEvent;
        }
        if (System.Math.Abs(r1 - r2) + System.Math.Abs(c1 - c2) != 1)
        {
            RejectedMoves++;
            LastEvent = $"rejected reason=not_adjacent from={r1},{c1} to={r2},{c2} "
                        + $"rejected={RejectedMoves}";
            return LastEvent;
        }
        if (GameOver)
        {
            RejectedMoves++;
            LastEvent = $"rejected reason=game_over from={r1},{c1} to={r2},{c2} won={Won} "
                        + $"moves={Moves} rejected={RejectedMoves}";
            return LastEvent;
        }
        var a = _cell[Idx(r1, c1)];
        var b = _cell[Idx(r2, c2)];
        _cell[Idx(r1, c1)] = b;
        _cell[Idx(r2, c2)] = a;
        if (FindMatches() == 0)
        {
            // put it back, byte for byte
            _cell[Idx(r1, c1)] = a;
            _cell[Idx(r2, c2)] = b;
            RejectedMoves++;
            LastEvent = $"rejected reason=no_match from={r1},{c1} to={r2},{c2} "
                        + $"rejected={RejectedMoves}";
            return LastEvent;
        }
        Moves++;
        LastSwap = $"{r1},{c1}>{r2},{c2}";
        var chain = ResolveCascade();
        Recompute();
        ApplyBoard();
        UpdateHud();
        LastEvent = $"swap from={r1},{c1} to={r2},{c2} chain={chain} cleared={LastCleared} "
                    + $"score={Score} moves={Moves} over={GameOver} won={Won}";
        return LastEvent;
    }

    /// <summary>
    /// Applies up to <paramref name="steps"/> deterministic auto moves: each step takes the FIRST
    /// legal swap in row-major order (right, then down) and plays it. Its own property,
    /// <see cref="LastHookSteps"/>, is the frame-rate independent delta.
    /// </summary>
    public string AutoStep(int steps)
    {
        var applied = 0;
        for (var t = 0; t < steps; t++)
        {
            if (GameOver)
            {
                break;
            }
            var found = false;
            for (var r = 0; r < Rows && !found; r++)
            {
                for (var c = 0; c < Cols && !found; c++)
                {
                    if (c + 1 < Cols && MakesLine(r, c, r, c + 1))
                    {
                        Swap(r, c, r, c + 1);
                        found = true;
                    }
                    else if (r + 1 < Rows && MakesLine(r, c, r + 1, c))
                    {
                        Swap(r, c, r + 1, c);
                        found = true;
                    }
                }
            }
            if (!found)
            {
                break;
            }
            applied++;
        }
        LastHookSteps = applied;
        LastEvent = $"autostep requested={steps} applied={applied} moves={Moves} score={Score} "
                    + $"over={GameOver}";
        return LastEvent;
    }

    /// <summary>Records the gem at one cell into the Probe* properties, so an assert can name it.</summary>
    public string ProbeCell(int row, int col)
    {
        ProbeRow = row;
        ProbeCol = col;
        if (!InBounds(row, col))
        {
            ProbeValue = -1;
            ProbeState = "outside";
        }
        else
        {
            ProbeValue = _cell[Idx(row, col)];
            ProbeState = ProbeValue < 0 ? "empty" : $"gem{ProbeValue}";
        }
        LastEvent = $"probe at={row},{col} value={ProbeValue} state={ProbeState}";
        return LastEvent;
    }

    /// <summary>Steps per second; 0 keeps the board still (the default).</summary>
    public string SetAutoClock(float perSecond)
    {
        AutoClock = perSecond;
        _autoAccum = 0.0f;
        LastAutoSteps = 0;
        LastEvent = $"auto_clock={AutoClock}";
        GD.Print($"MATCH3_AUTO auto={AutoClock}");
        return LastEvent;
    }

    /// <summary>Switches the declared-input polling on or off (the default is off).</summary>
    public string SetPollInput(bool enabled)
    {
        PollInput = enabled;
        ResetEdgeDetectors();
        LastEvent = $"poll_input={PollInput}";
        return LastEvent;
    }

    /// <summary>Forgets the press-edge state of every declared action, so a key that is still
    /// held when polling is switched on does not fire as a fresh press.</summary>
    private void ResetEdgeDetectors()
    {
        _prevMove = false;
        _prevUp = false;
        _prevDown = false;
        _prevLeft = false;
        _prevRight = false;
        _prevSwap = false;
    }

    private void HandleInput()
    {
        var move = Input.IsActionPressed("m3_auto_move");
        // Press edges only: a key a scenario injected and never released performs exactly one action
        // instead of repeating at the frame rate.
        if (move && !_prevMove && !GameOver)
        {
            var before = Moves;
            AutoStep(1);
            if (Moves > before)
            {
                InputMoves++;
            }
        }
        _prevMove = move;
        // TASK-116 (defect D3/D4): `m3_left` and `m3_right` were declared and never read, and
        // there was no way to choose *which* gems to swap at all -- the only "move" was the
        // random AutoStep above. The cursor plus Space is the smallest honest control scheme:
        // W/A/S/D place the cursor, Space swaps the cursor's gem with its right neighbour.
        MoveCursor("m3_up", -1, 0, ref _prevUp);
        MoveCursor("m3_down", 1, 0, ref _prevDown);
        MoveCursor("m3_left", 0, -1, ref _prevLeft);
        MoveCursor("m3_right", 0, 1, ref _prevRight);
        var swap = Input.IsActionPressed("m3_swap");
        if (swap && !_prevSwap && !GameOver)
        {
            var before = Moves;
            Swap(CursorRow, CursorCol, CursorRow, CursorCol + 1);
            InputSwaps++;
            if (Moves == before)
            {
                InputRejectedSwaps++;
            }
        }
        _prevSwap = swap;
    }

    /// <summary>One keyboard cursor step, on the press edge, clamped to the board.</summary>
    private void MoveCursor(string action, int dRow, int dCol, ref bool previous)
    {
        var held = Input.IsActionPressed(action);
        if (held && !previous && !GameOver)
        {
            CursorRow = System.Math.Max(0, System.Math.Min(Rows - 1, CursorRow + dRow));
            CursorCol = System.Math.Max(0, System.Math.Min(Cols - 1, CursorCol + dCol));
            InputCursors++;
        }
        previous = held;
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
                AutoStep(1);
                applied++;
                if (GameOver)
                {
                    break;
                }
            }
            AutoTicks += applied;
            LastAutoSteps = applied;
        }
        else
        {
            LastAutoSteps = 0;
        }
    }

    /// <summary>The board as a readable one-liner plus every exported fact.</summary>
    public string Dump()
    {
        return $"board={Board} cols={Cols} rows={Rows} colors={Colors} target={Target} "
               + $"move_limit={MovesLimit} seed={Seed} refills={Refills} moves={Moves} "
               + $"rejected={RejectedMoves} score={Score} last_cleared={LastCleared} "
               + $"total_cleared={TotalCleared} last_chain={LastChain} max_chain={MaxChain} "
               + $"cascades={Cascades} last_swap={LastSwap} board_hash={BoardHash} won={Won} "
               + $"over={GameOver} probe={ProbeRow},{ProbeCol}:{ProbeState} auto={AutoClock} "
               + $"auto_ticks={AutoTicks} last_auto={LastAutoSteps} last_hook={LastHookSteps} "
               + $"input_moves={InputMoves} elapsed={Elapsed:F3} ticks={Ticks} last={LastEvent}";
    }

    /// <summary>
    /// Writes the whole deterministic board in one call: <c>"board=&lt;rows separated by /&gt;"</c>
    /// (one digit per cell, 0..Colours-1, '-' for empty) plus optional <c>;seed=N</c>,
    /// <c>;score=N</c>, <c>;moves=N</c>, <c>;target=N</c> and <c>;movelimit=N</c>.
    ///
    /// <para>The auto clock and input polling are switched OFF first, so a session's aim and the next
    /// readback are the same fact. A test that wants motion calls <see cref="SetAutoClock"/> or
    /// <see cref="AutoStep"/> itself -- which is why "the cascade ends on this board" can never be an
    /// accident of timing.</para>
    /// </summary>
    public string ForceTestState(string spec)
    {
        var boardArg = "";
        var seedArg = "";
        var scoreArg = "";
        var movesArg = "";
        var targetArg = "";
        var limitArg = "";
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
                    boardArg = kv[1];
                    break;
                case "seed":
                    seedArg = kv[1];
                    break;
                case "score":
                    scoreArg = kv[1];
                    break;
                case "moves":
                    movesArg = kv[1];
                    break;
                case "target":
                    targetArg = kv[1];
                    break;
                case "movelimit":
                    limitArg = kv[1];
                    break;
            }
        }
        if (targetArg.Length > 0)
        {
            Target = int.Parse(targetArg);
        }
        if (limitArg.Length > 0)
        {
            MovesLimit = int.Parse(limitArg);
        }
        if (boardArg.Length > 0)
        {
            var raw = boardArg.Split('/');
            Rows = raw.Length;
            Cols = 0;
            foreach (var line in raw)
            {
                if (line.Length > Cols)
                {
                    Cols = line.Length;
                }
            }
            _cell = new int[Cols * Rows];
            for (var r = 0; r < Rows; r++)
            {
                var line = raw[r];
                for (var c = 0; c < Cols; c++)
                {
                    var ch = c < line.Length ? line[c] : '-';
                    if (ch >= '0' && ch <= '9')
                    {
                        _cell[Idx(r, c)] = ch - '0';
                    }
                    else if (ch == '-')
                    {
                        _cell[Idx(r, c)] = -1;
                    }
                    else
                    {
                        _cell[Idx(r, c)] = 0;
                    }
                }
            }
            // the nodes are rebuilt below, and the counters are zeroed below, so a force with a board
            // and a force without one take the same path
        }
        CreateNodes();
        ResetCounters();
        if (seedArg.Length > 0)
        {
            Seed = int.Parse(seedArg);
        }
        if (scoreArg.Length > 0)
        {
            Score = int.Parse(scoreArg);
        }
        if (movesArg.Length > 0)
        {
            Moves = int.Parse(movesArg);
        }
        AutoClock = 0.0f;
        AutoTicks = 0;
        LastAutoSteps = 0;
        LastHookSteps = 0;
        _autoAccum = 0.0f;
        PollInput = false;
        InputMoves = 0;
        ResetEdgeDetectors();
        Recompute();
        ApplyBoard();
        UpdateHud();
        LastEvent = $"forced moves={Moves} score={Score} seed={Seed} over={GameOver} won={Won}";
        return LastEvent;
    }

    private void ResetCounters()
    {
        Refills = 0;
        Moves = 0;
        RejectedMoves = 0;
        Score = 0;
        LastCleared = 0;
        TotalCleared = 0;
        LastChain = 0;
        MaxChain = 0;
        Cascades = 0;
        LastSwap = "";
        Won = false;
        GameOver = false;
        ProbeRow = -1;
        ProbeCol = -1;
        ProbeValue = -1;
        ProbeState = "";
        AutoClock = 0.0f;
        AutoTicks = 0;
        LastAutoSteps = 0;
        LastHookSteps = 0;
        _autoAccum = 0.0f;
        // TASK-116 D1: was `PollInput = false;` -- that is what
        // switched player input off again right after _Ready() ran.
        // The deterministic entry point is ForceTestState / SetPollInput.
        InputMoves = 0;
        // TASK-116 D3: start the cursor in the middle of the board. A cursor parked at (0,0)
        // makes "up" and "left" clamp to nothing on the very first press, which is both a bad
        // first impression for a player and an untestable capability.
        CursorRow = Rows / 2;
        CursorCol = Cols / 2;
        InputCursors = 0;
        InputSwaps = 0;
        InputRejectedSwaps = 0;
        ResetEdgeDetectors();
        Ticks = 0;
        LastEvent = "reset";
    }
}
