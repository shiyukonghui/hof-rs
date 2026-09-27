using Godot;
using System.Collections.Generic;
using System.Text;

namespace game2048;

/// <summary>
/// 2048 -- the tenth C# game of the godot-mcp series (TASK-100, DECISIONS.md D138).
///
/// <para><b>Design rule</b> (inherited from Pong / Breakout / Snake / Tetris / Space Invaders /
/// Asteroids / Pac-Man / Frogger / Flappy Bird): every fact the evidence model needs is a real
/// Godot property on the root node -- <see cref="Score"/>, <see cref="MaxTile"/>, <see cref="MoveCount"/>,
/// <see cref="MovesAccepted"/>, <see cref="MovesRejected"/>, <see cref="TotalMerges"/>,
/// <see cref="LastMoveMoved"/>, <see cref="LastMoveGain"/>, <see cref="LastMoveMerges"/>,
/// <see cref="GridHash"/>, <see cref="GridString"/>, <see cref="CanMoveAny"/>, <see cref="Won"/>,
/// <see cref="GameOver"/>, <see cref="AutoSteps"/>, <see cref="LastAutoSteps"/>,
/// <see cref="Elapsed"/>, <see cref="Ticks"/>. A session asserts these with
/// <c>running_game_assert_node_state</c>; it never parses a log line.</para>
///
/// <para><b>Determinism rule.</b> Nothing moves on its own. <see cref="AutoPlay"/> is 0 by default
/// and <see cref="PollInput"/> is false by default; a board is pinned with ONE
/// <see cref="ForceTestState"/> call. Every move is reachable through a fixed hook
/// (<see cref="Move"/>, <see cref="AutoStep"/>), so "a tile merged" can never be an accident of
/// frame timing.</para>
///
/// <para><b>Frame-rate independence (the F-1 lesson).</b> The auto-play clock is a FLOAT ACCUMULATOR
/// (<c>_autoAccum += delta * AutoPlay</c>), never <c>(int)(delta * rate)</c>: the truncating form is
/// what left the Flappy Bird world standing still at 144 fps (TASK-099 F-1). The two quantities a
/// sample reads are <see cref="LastAutoSteps"/> (moves the clock applied on the last frame) and
/// <see cref="LastHookSteps"/> (moves the last <see cref="AutoStep"/> call applied -- two producers,
/// two properties, which is a defect r1 of this game caught) plus <see cref="Elapsed"/> (a monotonic
/// float second counter that is never truncated).</para>
///
/// <para><b>The board is a 4x4 grid of unknown numbers.</b> An empty cell is value 0; a move slides
/// and merges in one of four directions; the score gains the value of every tile a merge creates;
/// two equal neighbours merge into their sum. A move that changes nothing is ILLEGAL and is refused
/// with no board change at all (<see cref="MovesRejected"/> counts it). Reaching
/// <see cref="TargetTile"/> sets <see cref="Won"/>; a board with no legal move left sets
/// <see cref="GameOver"/>.</para>
///
/// <para><b>All sixteen tiles are runtime-created.</b> <see cref="_Ready"/> builds one
/// <c>ColorRect</c> and one <c>Label</c> per cell; the scene file carries only the three static
/// nodes (Background, Hud, Status). That keeps the edited scene small, keeps it immune to the D-3
/// duplicate-name trap, and makes "a node created at run time really is drawn" part of this game's
/// own evidence.</para>
/// </summary>
public partial class Game2048Game : Node2D
{
    // --- the grid ---------------------------------------------------------------
    /// <summary>Columns of the board (2048 is 4x4).</summary>
    [Export] public int Cols = 4;

    /// <summary>Rows of the board.</summary>
    [Export] public int Rows = 4;

    /// <summary>Size of one cell in pixels.</summary>
    [Export] public int Cell = 110;

    /// <summary>Left edge of the board in pixels.</summary>
    [Export] public int OriginX = 180;

    /// <summary>Top edge of the board in pixels.</summary>
    [Export] public int OriginY = 110;

    /// <summary>The tile value that wins the game.</summary>
    [Export] public int TargetTile = 2048;

    // --- observable state, all of it a real Godot property ----------------------
    /// <summary>Points gained by merges so far.</summary>
    [Export] public int Score = 0;

    /// <summary>The largest tile on the board right now.</summary>
    [Export] public int MaxTile = 0;

    /// <summary>How many cells carry a non-zero value.</summary>
    [Export] public int TilesInUse = 0;

    /// <summary>How many cells are empty.</summary>
    [Export] public int EmptyCells = 16;

    /// <summary>Moves that changed the board.</summary>
    [Export] public int MoveCount = 0;

    /// <summary>Accepted moves (a synonym of <see cref="MoveCount"/>, kept as its own fact).</summary>
    [Export] public int MovesAccepted = 0;

    /// <summary>Refused moves: the direction changed nothing, or the game was already over.</summary>
    [Export] public int MovesRejected = 0;

    /// <summary>Merges over the whole game.</summary>
    [Export] public int TotalMerges = 0;

    /// <summary>Direction of the last requested move.</summary>
    [Export] public int LastMoveDir = -1;

    /// <summary>True when the last requested move actually changed the board.</summary>
    [Export] public bool LastMoveMoved = false;

    /// <summary>Merges the last accepted move made.</summary>
    [Export] public int LastMoveMerges = 0;

    /// <summary>Points the last accepted move gained.</summary>
    [Export] public int LastMoveGain = 0;

    /// <summary>True when no legal move is left (a full board with no equal neighbours).</summary>
    [Export] public bool GameOver = false;

    /// <summary>True when a tile reached <see cref="TargetTile"/>.</summary>
    [Export] public bool Won = false;

    /// <summary>True when at least one direction would change the board.</summary>
    [Export] public bool CanMoveAny = true;

    /// <summary>A stable hash of the sixteen cell values -- a multi-frame sample can watch it change.</summary>
    [Export] public int GridHash = 0;

    /// <summary>The board as rows separated by '/', cells by ',' -- the exact layout an assert names.</summary>
    [Export] public string GridString = "";

    /// <summary>Seconds since the last reset: a monotonic FLOAT accumulator, never truncated.</summary>
    [Export] public float Elapsed = 0.0f;

    /// <summary>Auto-play moves per second; 0 keeps the board still (the default).</summary>
    [Export] public float AutoPlay = 0.0f;

    /// <summary>Moves the auto-play clock has applied over the whole game.</summary>
    [Export] public int AutoSteps = 0;

    /// <summary>Moves the auto-play clock applied on the LAST frame (0 while the clock is off).</summary>
    [Export] public int LastAutoSteps = 0;

    /// <summary>
    /// Moves the LAST <see cref="AutoStep"/> CALL took. Its own property, and the clock never
    /// writes it: a run found (r1 of this game, TASK-100) that a single property used by both
    /// producers reads 0 by the time the assertion runs, because the next frame's clock pass
    /// overwrites it. Two producers, two properties.
    /// </summary>
    [Export] public int LastHookSteps = 0;

    /// <summary>
    /// When true an accepted move also drops a NEW tile (the real 2048 rule).
    ///
    /// <para><b>TASK-135 §1.A.3: default ON.</b> It used to be off, and the measured
    /// consequence was that the board stopped growing after the opening deal: the scripted
    /// arm slid the same single tile left and right for every step (`SCORE 4 MOVES 3 MAX 4`
    /// with one `4` on the board, TASK-134 §1.4c), so the game's own goal -- reach 2048 --
    /// was unreachable by construction. A 2048 in which no tile is ever dealt again is not
    /// a hard 2048, it is not 2048.</para>
    ///
    /// <para><b>The tile is dealt like the real game deals it</b> (a uniformly chosen EMPTY
    /// cell, value 2 or 4), and it is drawn from a seeded xorshift
    /// (<see cref="SpawnSeed"/>) so a recorded run is still reproducible bit for bit --
    /// the same reason the opening deal uses fixed cells. The pinned-cell hook
    /// (<see cref="SpawnPinned"/>, set by <c>ForceTestState("spawn=r,c,v")</c>) is kept for
    /// the sessions that need "this move deals exactly this tile at exactly this cell";
    /// <c>ForceTestState</c> still switches both off first, exactly as its contract says.
    /// </para>
    /// </summary>
    [Export] public bool AutoSpawn = true;

    /// <summary>
    /// When true the post-move deal lands at the PINNED cell (<see cref="SpawnRow"/>,
    /// <see cref="SpawnCol"/>/<see cref="SpawnValue"/>) instead of a real empty cell.
    /// Off by default; only <c>ForceTestState("spawn=...")</c> turns it on.
    /// </summary>
    [Export] public bool SpawnPinned = false;

    /// <summary>
    /// Seed of the post-move deal's xorshift. A fixed default keeps a recorded run
    /// reproducible; a session may set it to deal a different (still deterministic) board.
    /// </summary>
    [Export] public int SpawnSeed = 20260928;

    /// <summary>Row the deterministic spawn drops at.</summary>
    [Export] public int SpawnRow = 0;

    /// <summary>Column the deterministic spawn drops at.</summary>
    [Export] public int SpawnCol = 0;

    /// <summary>Value the deterministic spawn drops.</summary>
    [Export] public int SpawnValue = 2;

    /// <summary>Tiles dealt by the post-move spawn over the whole game (TASK-135).</summary>
    [Export] public int SpawnedTiles = 0;

    /// <summary>When true the game reads its player's keyboard. The test driver switches this
    /// OFF explicitly (<see cref="SetPollInput"/>, <see cref="ForceTestState"/>) when it needs
    /// a frozen, deterministic state; the deterministic defaults live in AutoClock / AutoPlay /
    /// DriftSpeed, not here (TASK-116 defect D1).</summary>
    [Export] public bool PollInput = true;

    /// <summary>Moves that arrived through the declared input actions.</summary>
    [Export] public int InputMoves = 0;

    /// <summary>Frames processed since the last reset.</summary>
    [Export] public int Ticks = 0;

    /// <summary>What the last hook did -- the readback string a session quotes.</summary>
    [Export] public string LastEvent = "";

    // --- private model ---------------------------------------------------------
    private int[] _grid = new int[16];
    private readonly ColorRect[] _tileRect = new ColorRect[16];
    private readonly Label[] _tileLabel = new Label[16];
    private ColorRect _board;
    private Label _hud;
    private Label _status;
    private float _autoAccum;
    private int _autoPhase;
    /// <summary>xorshift state for the post-move deal (TASK-135); reset from <see cref="SpawnSeed"/>.</summary>
    private uint _spawnState;
    private bool _prevUp;
    private bool _prevRight;
    private bool _prevDown;
    private bool _prevLeft;

    /// <summary>The deterministic auto-play direction order: left, up, right, down.</summary>
    private static readonly int[] AutoCycle = { 3, 0, 1, 2 };

    private int Idx(int row, int col)
    {
        return row * Cols + col;
    }

    public override void _Ready()
    {
        _hud = GetNodeOrNull<Label>("Hud");
        _status = GetNodeOrNull<Label>("Status");
        CreateNodes();
        ResetBoard();
        SpawnOpeningTiles();
        Recompute();
        ApplyTiles();
        UpdateHud();
        GD.Print($"GAME2048_READY cols={Cols} rows={Rows} tiles={TilesInUse} max={MaxTile} "
                 + $"score={Score} grid={GridString} auto={AutoPlay} poll={PollInput}");
    }

    /// <summary>
    /// The two tiles 2048 deals at the start of a game (TASK-133 §1.A.2).
    ///
    /// <para><b>The defect this removes.</b> `_Ready` only reset the empty board, so a
    /// fresh process showed a 4x4 field of empty cells: `GridString` was all zeros,
    /// `TilesInUse=0`, and all four declared directions answered
    /// `rejected reason=no_change`. The usability gate's P2/P3 turned red for exactly
    /// that (TASK-131), and no model-player run could ever do anything: an empty board
    /// has no legal move by definition, so the game was unplayable rather than merely
    /// hard.</para>
    ///
    /// <para><b>The rule.</b> 2048 deals TWO tiles at the start (the real game deals 2s;
    /// that is the rule this implements), and they are placed at fixed cells rather than
    /// drawn from a random generator -- the game's own determinism rule ("nothing moves
    /// on its own ... a board is pinned with ONE ForceTestState call") must hold for the
    /// opening deal too, so a replayed session and a screenshot compare bit-for-bit.
    /// `_Ready` therefore always starts from the SAME board:
    /// <c>0,0,0,0/0,0,0,0/0,2,2,0/0,0,0,0</c>.</para>
    ///
    /// <para><b>Why this placement.</b> Two 2s side by side in the middle row are movable
    /// in all four directions and merge in two of them, so every declared action has a
    /// legal first move: left/right merge them into a 4 (a real merge and a real score
    /// gain), up/down drop them to the top/bottom row. The board is 75% empty, so the
    /// opening is a normal 2048 opening rather than a puzzle.</para>
    /// </summary>
    private void SpawnOpeningTiles()
    {
        var row = Rows / 2;
        var col = Cols / 2;
        SetCell(row, col - 1, 2);
        SetCell(row, col, 2);
        LastEvent = $"opening_deal tiles={TilesInUse} grid={GridString} can_move={CanMoveAny}";
    }

    private ColorRect MakeRect(string name, Vector2 position, Vector2 size, Color color)
    {
        var node = new ColorRect();
        node.Name = name;
        node.Position = position;
        node.Size = size;
        node.Color = color;
        AddChild(node);
        return node;
    }

    private Label MakeLabel(string name, Vector2 position, Vector2 size)
    {
        var node = new Label();
        node.Name = name;
        node.Position = position;
        node.Size = size;
        node.HorizontalAlignment = HorizontalAlignment.Center;
        node.VerticalAlignment = VerticalAlignment.Center;
        node.AddThemeFontSizeOverride("font_size", 34);
        AddChild(node);
        return node;
    }

    /// <summary>Builds the board frame and the sixteen runtime tiles. Called once.</summary>
    private void CreateNodes()
    {
        if (_board == null || !IsInstanceValid(_board))
        {
            _board = MakeRect("Board", new Vector2(OriginX - 8, OriginY - 8),
                              new Vector2(Cols * Cell + 16, Rows * Cell + 16),
                              new Color(0.13f, 0.13f, 0.16f));
        }
        for (var r = 0; r < Rows; r++)
        {
            for (var c = 0; c < Cols; c++)
            {
                var i = Idx(r, c);
                var at = new Vector2(OriginX + c * Cell + 4, OriginY + r * Cell + 4);
                var size = new Vector2(Cell - 8, Cell - 8);
                _tileRect[i] = MakeRect($"Tile_{r}_{c}", at, size, new Color(0.20f, 0.20f, 0.24f));
                _tileLabel[i] = MakeLabel($"Val_{r}_{c}", at, size);
            }
        }
    }

    private static Color TileColor(int value)
    {
        switch (value)
        {
            case 0: return new Color(0.20f, 0.20f, 0.24f);
            case 2: return new Color(0.90f, 0.86f, 0.78f);
            case 4: return new Color(0.93f, 0.80f, 0.55f);
            case 8: return new Color(0.95f, 0.60f, 0.30f);
            case 16: return new Color(0.95f, 0.45f, 0.22f);
            case 32: return new Color(0.93f, 0.32f, 0.26f);
            case 64: return new Color(0.88f, 0.20f, 0.18f);
            case 128: return new Color(0.85f, 0.72f, 0.25f);
            case 256: return new Color(0.82f, 0.68f, 0.20f);
            case 512: return new Color(0.78f, 0.64f, 0.15f);
            case 1024: return new Color(0.55f, 0.80f, 0.35f);
            case 2048: return new Color(0.35f, 0.90f, 0.45f);
            default: return new Color(0.30f, 0.70f, 0.95f);
        }
    }

    private void ResetBoard()
    {
        for (var i = 0; i < _grid.Length; i++)
        {
            _grid[i] = 0;
        }
        Score = 0;
        MaxTile = 0;
        MoveCount = 0;
        MovesAccepted = 0;
        MovesRejected = 0;
        TotalMerges = 0;
        LastMoveDir = -1;
        LastMoveMoved = false;
        LastMoveMerges = 0;
        LastMoveGain = 0;
        GameOver = false;
        Won = false;
        AutoPlay = 0.0f;
        AutoSteps = 0;
        LastAutoSteps = 0;
        LastHookSteps = 0;
        _autoAccum = 0.0f;
        _autoPhase = 0;
        // TASK-135 §1.A.3: a live game deals a new tile after every accepted move; the
        // pinned-cell stand-in is what a session opts into through `ForceTestState`.
        AutoSpawn = true;
        SpawnPinned = false;
        SpawnRow = 0;
        SpawnCol = 0;
        SpawnValue = 2;
        SpawnedTiles = 0;
        _spawnState = unchecked((uint)SpawnSeed);
        // TASK-116 D1: was `PollInput = false;` -- that is what
        // switched player input off again right after _Ready() ran.
        // The deterministic entry point is ForceTestState / SetPollInput.
        InputMoves = 0;
        _prevUp = _prevRight = _prevDown = _prevLeft = false;
        Ticks = 0;
    }

    /// <summary>Recomputes every derived fact: counts, the hash, the legal-move predicate, the verdicts.</summary>
    private void Recompute()
    {
        var used = 0;
        var max = 0;
        var hash = 17;
        var sb = new StringBuilder();
        for (var r = 0; r < Rows; r++)
        {
            for (var c = 0; c < Cols; c++)
            {
                var v = _grid[Idx(r, c)];
                if (v != 0)
                {
                    used++;
                    if (v > max)
                    {
                        max = v;
                    }
                }
                unchecked
                {
                    hash = hash * 31 + v;
                }
                sb.Append(v);
                if (c + 1 < Cols)
                {
                    sb.Append(',');
                }
            }
            if (r + 1 < Rows)
            {
                sb.Append('/');
            }
        }
        TilesInUse = used;
        EmptyCells = Rows * Cols - used;
        MaxTile = max;
        GridHash = hash;
        GridString = sb.ToString();
        CanMoveAny = HasMove();
        GameOver = !CanMoveAny;
        Won = max >= TargetTile;
    }

    /// <summary>True when some direction would change the board.</summary>
    private bool HasMove()
    {
        for (var r = 0; r < Rows; r++)
        {
            for (var c = 0; c < Cols; c++)
            {
                if (_grid[Idx(r, c)] == 0)
                {
                    return true;
                }
                if (c + 1 < Cols && _grid[Idx(r, c)] == _grid[Idx(r, c + 1)])
                {
                    return true;
                }
                if (r + 1 < Rows && _grid[Idx(r, c)] == _grid[Idx(r + 1, c)])
                {
                    return true;
                }
            }
        }
        return false;
    }

    private void ApplyTiles()
    {
        for (var r = 0; r < Rows; r++)
        {
            for (var c = 0; c < Cols; c++)
            {
                var i = Idx(r, c);
                if (_tileRect[i] == null || !IsInstanceValid(_tileRect[i]))
                {
                    continue;
                }
                var v = _grid[i];
                _tileRect[i].Color = TileColor(v);
                if (_tileLabel[i] != null && IsInstanceValid(_tileLabel[i]))
                {
                    _tileLabel[i].Text = v == 0 ? "" : v.ToString();
                    _tileLabel[i].AddThemeColorOverride("font_color", new Color(0.10f, 0.10f, 0.12f));
                }
            }
        }
    }

    private void UpdateHud()
    {
        if (_hud != null)
        {
            _hud.Text = $"SCORE {Score}  MOVES {MoveCount}  MAX {MaxTile}";
        }
        if (_status != null)
        {
            if (GameOver)
            {
                _status.Text = Won ? "2048 REACHED - NO MOVES" : "NO MOVES LEFT";
            }
            else
            {
                _status.Text = Won ? "2048 REACHED" : "JOIN THE TILES";
            }
        }
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
        if (AutoPlay > 0.0f)
        {
            _autoAccum += dt * AutoPlay; // F-1's fix: accumulate, never (int)(delta * rate)
            var steps = 0;
            while (_autoAccum >= 1.0f && steps < 8)
            {
                _autoAccum -= 1.0f;
                if (!AutoMoveOnce())
                {
                    break;
                }
                AutoSteps++;
                steps++;
            }
            LastAutoSteps = steps;
        }
        else
        {
            LastAutoSteps = 0;
        }
    }

    /// <summary>
    /// The declared-input path. Each direction acts on the PRESS EDGE, so a key a scenario injected
    /// and never released performs exactly one move instead of repeating at the frame rate.
    /// </summary>
    private void HandleInput()
    {
        var up = Input.IsActionPressed("m2048_up");
        var right = Input.IsActionPressed("m2048_right");
        var down = Input.IsActionPressed("m2048_down");
        var left = Input.IsActionPressed("m2048_left");
        var dir = -1;
        if (up && !_prevUp)
        {
            dir = 0;
        }
        else if (right && !_prevRight)
        {
            dir = 1;
        }
        else if (down && !_prevDown)
        {
            dir = 2;
        }
        else if (left && !_prevLeft)
        {
            dir = 3;
        }
        _prevUp = up;
        _prevRight = right;
        _prevDown = down;
        _prevLeft = left;
        if (dir >= 0)
        {
            Move(dir);
            InputMoves++;
        }
    }

    // --- hooks the session drives ----------------------------------------------

    private static bool Same(int[] a, int[] b)
    {
        for (var i = 0; i < a.Length; i++)
        {
            if (a[i] != b[i])
            {
                return false;
            }
        }
        return true;
    }

    /// <summary>
    /// Requests one move: 0 up, 1 right, 2 down, 3 left. A move that changes nothing is refused --
    /// the board is left exactly as it was and <see cref="MovesRejected"/> grows.
    /// </summary>
    public string Move(int dir)
    {
        LastMoveDir = dir;
        LastMoveMerges = 0;
        LastMoveGain = 0;
        if (GameOver)
        {
            LastMoveMoved = false;
            MovesRejected++;
            LastEvent = $"rejected reason=game_over dir={dir} moves={MoveCount} rejected={MovesRejected}";
            return LastEvent;
        }
        var before = (int[])_grid.Clone();
        var gain = 0;
        var merges = 0;
        Slide(dir, ref gain, ref merges);
        var moved = !Same(before, _grid);
        LastMoveMoved = moved;
        if (!moved)
        {
            MovesRejected++;
            LastEvent = $"rejected reason=no_change dir={dir} hash={GridHash} rejected={MovesRejected}";
            return LastEvent;
        }
        Score += gain;
        TotalMerges += merges;
        MoveCount++;
        MovesAccepted++;
        LastMoveMerges = merges;
        LastMoveGain = gain;
        if (AutoSpawn)
        {
            // TASK-135 §1.A.3: the real 2048 rule -- one new tile, on an EMPTY cell.
            // `SpawnPinned` keeps the old deterministic stand-in for sessions that need
            // "this move deals exactly this tile here" (ForceTestState's `spawn=` key).
            if (SpawnPinned)
            {
                SetCell(SpawnRow, SpawnCol, SpawnValue);
                SpawnedTiles++;
            }
            else
            {
                SpawnRandomTile();
            }
        }
        Recompute();
        ApplyTiles();
        UpdateHud();
        LastEvent = $"moved dir={dir} merges={merges} gain={gain} score={Score} moves={MoveCount} "
                    + $"max={MaxTile} won={Won} over={GameOver}";
        return LastEvent;
    }

    /// <summary>One direction of the slide-and-merge rule, in the direction of travel.</summary>
    private void Slide(int dir, ref int gain, ref int merges)
    {
        var lines = dir == 0 || dir == 2 ? Cols : Rows;
        for (var line = 0; line < lines; line++)
        {
            var len = dir == 0 || dir == 2 ? Rows : Cols;
            var cells = new List<int>();
            for (var i = 0; i < len; i++)
            {
                cells.Add(CellOnLine(dir, line, i));
            }
            var values = new List<int>();
            foreach (var v in cells)
            {
                if (v != 0)
                {
                    values.Add(v);
                }
            }
            var merged = new List<int>();
            for (var i = 0; i < values.Count; i++)
            {
                if (i + 1 < values.Count && values[i] == values[i + 1])
                {
                    var m = values[i] * 2;
                    merged.Add(m);
                    gain += m;
                    merges++;
                    i++;
                }
                else
                {
                    merged.Add(values[i]);
                }
            }
            while (merged.Count < len)
            {
                merged.Add(0);
            }
            for (var i = 0; i < len; i++)
            {
                SetCellOnLine(dir, line, i, merged[i]);
            }
        }
    }

    private int CellOnLine(int dir, int line, int i)
    {
        switch (dir)
        {
            case 0: return _grid[Idx(i, line)];                 // up: top first
            case 1: return _grid[Idx(line, Cols - 1 - i)];      // right: right first
            case 2: return _grid[Idx(Rows - 1 - i, line)];      // down: bottom first
            default: return _grid[Idx(line, i)];                // left: left first
        }
    }

    private void SetCellOnLine(int dir, int line, int i, int value)
    {
        switch (dir)
        {
            case 0: _grid[Idx(i, line)] = value; break;
            case 1: _grid[Idx(line, Cols - 1 - i)] = value; break;
            case 2: _grid[Idx(Rows - 1 - i, line)] = value; break;
            default: _grid[Idx(line, i)] = value; break;
        }
    }

    /// <summary>Writes one cell. The caller decides when to recompute.</summary>
    public string SetCell(int row, int col, int value)
    {
        if (row < 0 || row >= Rows || col < 0 || col >= Cols)
        {
            LastEvent = $"rejected reason=out_of_bounds at={row},{col}";
            return LastEvent;
        }
        _grid[Idx(row, col)] = value;
        Recompute();
        ApplyTiles();
        UpdateHud();
        LastEvent = $"cell {row},{col}={value} used={TilesInUse} max={MaxTile}";
        return LastEvent;
    }

    /// <summary>Drops a tile at a pinned cell -- the deterministic stand-in for the random spawn.</summary>
    public string SpawnTile(int row, int col, int value)
    {
        var result = SetCell(row, col, value);
        LastEvent = $"spawn {row},{col}={value} used={TilesInUse} max={MaxTile}";
        return LastEvent;
    }

    /// <summary>
    /// Deals one tile the way 2048 deals it -- value 2 (or 4, one time in ten) on a
    /// uniformly chosen EMPTY cell (TASK-135 §1.A.3).
    ///
    /// <para>The cell is never overwritten: a real spawn is on an empty cell or it is not a
    /// spawn. The randomness is a seeded xorshift rather than `GD.Randi()`, so a recording
    /// replays identically (the project's determinism rule); the seed is an `[Export]`, so
    /// a session that wants another board can set it instead of editing the game.</para>
    /// </summary>
    private string SpawnRandomTile()
    {
        var empty = new List<int>();
        for (var i = 0; i < _grid.Length; i++)
        {
            if (_grid[i] == 0)
            {
                empty.Add(i);
            }
        }
        if (empty.Count == 0)
        {
            LastEvent = "spawn skipped reason=no_empty_cell";
            return LastEvent;
        }
        var pick = empty[(int)(NextRandom() % (uint)empty.Count)];
        var value = (NextRandom() % 10u) == 0u ? 4 : 2;
        SpawnedTiles++;
        SetCell(pick / Cols, pick % Cols, value);
        LastEvent = $"spawn {pick / Cols},{pick % Cols}={value} empty_before={empty.Count} "
                    + $"dealt={SpawnedTiles} used={TilesInUse} max={MaxTile}";
        return LastEvent;
    }

    /// <summary>The deterministic 32-bit xorshift behind <see cref="SpawnRandomTile"/>.</summary>
    private uint NextRandom()
    {
        var x = _spawnState;
        if (x == 0u)
        {
            x = unchecked((uint)SpawnSeed) | 1u;
        }
        x ^= x << 13;
        x ^= x >> 17;
        x ^= x << 5;
        _spawnState = x;
        return x;
    }

    /// <summary>The deterministic auto-play policy: the first legal direction from the cycle.</summary>
    private bool AutoMoveOnce()
    {
        if (GameOver)
        {
            return false;
        }
        for (var i = 0; i < AutoCycle.Length; i++)
        {
            var dir = AutoCycle[(_autoPhase + i) % AutoCycle.Length];
            Move(dir);
            if (LastMoveMoved)
            {
                _autoPhase = (dir + 1) % AutoCycle.Length;
                return true;
            }
        }
        return false;
    }

    /// <summary>Applies up to <paramref name="steps"/> deterministic auto-play moves.</summary>
    public string AutoStep(int steps)
    {
        var accepted = 0;
        var attempts = 0;
        for (var i = 0; i < steps; i++)
        {
            attempts++;
            if (!AutoMoveOnce())
            {
                break;
            }
            accepted++;
            AutoSteps++;
        }
        LastHookSteps = accepted;
        LastEvent = $"autostep requested={steps} attempts={attempts} accepted={accepted} "
                    + $"total={AutoSteps} moves={MoveCount}";
        return LastEvent;
    }

    /// <summary>Auto-play moves per second; 0 keeps the board still (the default).</summary>
    public string SetAutoPlay(float perSecond)
    {
        AutoPlay = perSecond;
        _autoAccum = 0.0f;
        LastAutoSteps = 0;
        LastEvent = $"auto_play={AutoPlay}";
        GD.Print($"GAME2048_AUTOPLAY auto={AutoPlay}");
        return LastEvent;
    }

    /// <summary>Switches the declared-input polling on or off (the default is off).</summary>
    public string SetPollInput(bool enabled)
    {
        PollInput = enabled;
        _prevUp = _prevRight = _prevDown = _prevLeft = false;
        LastEvent = $"poll_input={PollInput}";
        return LastEvent;
    }

    /// <summary>The board as a readable one-liner plus every exported fact.</summary>
    public string Dump()
    {
        return $"grid={GridString} hash={GridHash} used={TilesInUse} empty={EmptyCells} max={MaxTile} "
               + $"score={Score} moves={MoveCount} accepted={MovesAccepted} rejected={MovesRejected} "
               + $"merges={TotalMerges} last_dir={LastMoveDir} last_moved={LastMoveMoved} "
               + $"last_merges={LastMoveMerges} last_gain={LastMoveGain} can_move={CanMoveAny} "
               + $"won={Won} over={GameOver} auto={AutoPlay} auto_steps={AutoSteps} "
               + $"last_auto={LastAutoSteps} last_hook={LastHookSteps} input_moves={InputMoves} "
               + $"elapsed={Elapsed:F3} ticks={Ticks} "
               + $"auto_spawn={AutoSpawn} spawn_pinned={SpawnPinned} dealt={SpawnedTiles} "
               + $"last={LastEvent}";
    }

    /// <summary>
    /// Writes the whole deterministic state in one call --
    /// <c>"grid=r0c0,..,r0c3|r1...|r2...|r3...;score=n;auto=s;spawn=r,c,v"</c>.
    ///
    /// <para>Keys may be omitted; the ones given are applied. Auto-play, input polling and the spawn
    /// hook are switched OFF first, so a session's aim and the next readback are the same fact. A
    /// test that wants motion calls <see cref="SetAutoPlay"/> or <see cref="AutoStep"/> itself --
    /// which is why "a tile merged" can never be an accident of timing.</para>
    /// </summary>
    public string ForceTestState(string spec)
    {
        ResetBoard();
        // The documented contract, kept exactly: "Auto-play, input polling and the spawn
        // hook are switched OFF first, so a session's aim and the next readback are the
        // same fact."  TASK-135 changed what a LIVE game does (`AutoSpawn` now defaults on
        // and deals a real tile), not what a forced state does.
        AutoSpawn = false;
        SpawnPinned = false;
        foreach (var part in spec.Split(';'))
        {
            var kv = part.Split(new[] { '=' }, 2);
            if (kv.Length != 2)
            {
                continue;
            }
            switch (kv[0])
            {
                case "grid":
                    {
                        var rows = kv[1].Split('|');
                        for (var r = 0; r < Rows && r < rows.Length; r++)
                        {
                            var cells = rows[r].Split(',');
                            for (var c = 0; c < Cols && c < cells.Length; c++)
                            {
                                _grid[Idx(r, c)] = int.Parse(cells[c]);
                            }
                        }
                    }
                    break;
                case "score":
                    Score = int.Parse(kv[1]);
                    break;
                case "auto":
                    AutoPlay = float.Parse(kv[1]);
                    break;
                case "spawn":
                    {
                        var p = kv[1].Split(',');
                        AutoSpawn = true;
                        SpawnPinned = true;
                        SpawnRow = int.Parse(p[0]);
                        SpawnCol = int.Parse(p[1]);
                        SpawnValue = int.Parse(p[2]);
                    }
                    break;
            }
        }
        Recompute();
        ApplyTiles();
        UpdateHud();
        LastEvent = $"forced used={TilesInUse} max={MaxTile} score={Score} hash={GridHash} "
                    + $"can_move={CanMoveAny} over={GameOver} won={Won}";
        return LastEvent;
    }
}
