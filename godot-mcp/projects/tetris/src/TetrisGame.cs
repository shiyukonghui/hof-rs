using Godot;
using System.Text;

namespace tetris;

/// <summary>
/// Tetris — the fourth C# game of the godot-mcp series (TASK-096, DECISIONS.md D138).
///
/// <para><b>Design rule</b> (inherited from Pong, Breakout and Snake): everything the
/// evidence model needs is a real Godot property on the root node — <see cref="Score"/>,
/// <see cref="Lines"/>, <see cref="Level"/>, <see cref="GameOver"/>, <see cref="PieceKind"/>,
/// <see cref="PieceX"/>, <see cref="PieceY"/>, <see cref="PieceRot"/>, <see cref="FilledCells"/>,
/// <see cref="BoardHash"/>, <see cref="Ticks"/>. A session asserts these with
/// <c>running_game_assert_node_state</c>; it never has to parse a log line.</para>
///
/// <para><b>Determinism rule</b> (Pong's run-1 defect P-1). Gravity is OFF by default:
/// a piece moves when a test hook says so, not when the clock does. The startup window
/// the driver spends waiting for the endpoint therefore cannot change the board behind
/// the session's back. <see cref="SetGravity"/> turns gravity on for the one test that
/// exists to watch a piece fall frame by frame.</para>
///
/// <para><b>The piece stream is deterministic</b>: the bag is not shuffled, the next kind
/// is <c>(current + 1) % 7</c>. A replayed session has to produce the same board or the
/// assertion in it means nothing.</para>
///
/// <para><b>No drop points.</b> A hard drop scores nothing; only completed lines score
/// (100/300/500/800 for 1/2/3/4). Fewer sources of score means an assertion about
/// <see cref="Score"/> can name exactly which rule produced it.</para>
/// </summary>
public partial class TetrisGame : Node2D
{
    /// <summary>Playfield width in cells.</summary>
    [Export] public int Columns = 10;

    /// <summary>Playfield height in cells.</summary>
    [Export] public int Rows = 20;

    /// <summary>Cell size in pixels.</summary>
    [Export] public int CellSize = 24;

    /// <summary>Playfield origin: x.</summary>
    [Export] public int BoardX = 280;

    /// <summary>Playfield origin: y.</summary>
    [Export] public int BoardY = 40;

    // --- observable state, all of it a real Godot property ---------------------
    /// <summary>Points.</summary>
    [Export] public int Score = 0;

    /// <summary>Lines cleared.</summary>
    [Export] public int Lines = 0;

    /// <summary>Level = 1 + Lines / 10.</summary>
    [Export] public int Level = 1;

    /// <summary>True once a piece cannot be spawned.</summary>
    [Export] public bool GameOver = false;

    /// <summary>Kind of the falling piece: 0..6 = I O T S Z J L.</summary>
    [Export] public int PieceKind = 0;

    /// <summary>Column of the falling piece's 4x4 box origin.</summary>
    [Export] public int PieceX = 3;

    /// <summary>Row of the falling piece's 4x4 box origin; may be negative.</summary>
    [Export] public int PieceY = 0;

    /// <summary>Rotation state 0..3.</summary>
    [Export] public int PieceRot = 0;

    /// <summary>Kind of the next piece.</summary>
    [Export] public int NextKind = 1;

    /// <summary>Gravity steps taken.</summary>
    [Export] public int Ticks = 0;

    /// <summary>Occupied playfield cells.</summary>
    [Export] public int FilledCells = 0;

    /// <summary>Order-independent digest of the playfield: sum of (index + 1) over occupied cells.</summary>
    [Export] public int BoardHash = 0;

    /// <summary>Seconds per automatic gravity step (see <see cref="SetGravity"/>).</summary>
    [Export] public float DropInterval = 1.0f;

    /// <summary>When true the piece falls on its own; false by default (determinism rule).</summary>
    [Export] public bool Gravity = false;

    /// <summary>What the last hook did — the readback string a session quotes.</summary>
    [Export] public string LastEvent = "";

    /// <summary>Points per line count: index = lines cleared in one step.</summary>
    private static readonly int[] LineScores = { 0, 100, 300, 500, 800 };

    private bool[] _cells = new bool[200];
    private readonly int[] _shape = new int[8];
    private float _accum;
    private float _logTimer;
    private int _locks;

    public override void _Ready()
    {
        _cells = new bool[Columns * Rows];
        SpawnPiece(PieceKind);
        Recount();
        GD.Print($"TETRIS_READY cols={Columns} rows={Rows} cell={CellSize} piece={Tetromino.Names[PieceKind]} "
                 + $"at={PieceX},{PieceY} next={Tetromino.Names[NextKind]} gravity={Gravity}");
    }

    /// <summary>The piece falls only when a test says so (see the class doc).</summary>
    public string SetGravity(float seconds)
    {
        DropInterval = seconds;
        Gravity = seconds > 0.0f;
        _accum = 0.0f;
        LastEvent = $"gravity interval={DropInterval}";
        GD.Print($"TETRIS_GRAVITY interval={DropInterval}");
        return LastEvent;
    }

    /// <summary>Row occupied count, for the "which row is full" read.</summary>
    public int RowFilled(int row)
    {
        var n = 0;
        for (var c = 0; c < Columns; c++)
        {
            if (InBounds(c, row) && _cells[row * Columns + c])
            {
                n++;
            }
        }
        return n;
    }

    /// <summary>The four occupied cells of the falling piece as <c>"x,y;x,y;..."</c>.</summary>
    public string PieceCells()
    {
        Tetromino.Cells(PieceKind, PieceRot, _shape);
        var sb = new StringBuilder();
        for (var i = 0; i < 4; i++)
        {
            if (i > 0)
            {
                sb.Append(';');
            }
            sb.Append(PieceX + _shape[i * 2]).Append(',').Append(PieceY + _shape[i * 2 + 1]);
        }
        return sb.ToString();
    }

    /// <summary>
    /// The whole board as text: the 20 rows, the falling piece, and every exported fact.
    /// A test hook, because "the piece is at row 3" and "the piece landed on row 3" are
    /// different claims and only the board text shows which one a readback is making.
    /// </summary>
    public string Dump()
    {
        var sb = new StringBuilder();
        for (var r = 0; r < Rows; r++)
        {
            for (var c = 0; c < Columns; c++)
            {
                sb.Append(InBounds(c, r) && _cells[r * Columns + c] ? '#' : '.');
            }
            if (r + 1 < Rows)
            {
                sb.Append('/');
            }
        }
        return $"board={sb} filled={FilledCells} hash={BoardHash} score={Score} lines={Lines} level={Level} "
               + $"over={GameOver} piece={Tetromino.Names[PieceKind]} at={PieceX},{PieceY},{PieceRot} "
               + $"cells=[{PieceCells()}] next={Tetromino.Names[NextKind]} ticks={Ticks} locks={_locks}";
    }

    /// <summary>The playfield without the falling piece, one row per '/'-separated field.</summary>
    public string BoardRows()
    {
        var sb = new StringBuilder();
        for (var r = 0; r < Rows; r++)
        {
            for (var c = 0; c < Columns; c++)
            {
                sb.Append(InBounds(c, r) && _cells[r * Columns + c] ? '#' : '.');
            }
            if (r + 1 < Rows)
            {
                sb.Append('/');
            }
        }
        return sb.ToString();
    }

    /// <summary>True when any of the piece's four cells overlaps the playfield or a filled cell.</summary>
    public bool Collides(int kind, int rot, int px, int py)
    {
        Tetromino.Cells(kind, rot, _shape);
        for (var i = 0; i < 4; i++)
        {
            var bx = px + _shape[i * 2];
            var by = py + _shape[i * 2 + 1];
            if (bx < 0 || bx >= Columns || by >= Rows)
            {
                return true;
            }
            if (by >= 0 && _cells[by * Columns + bx])
            {
                return true;
            }
        }
        return false;
    }

    /// <summary>
    /// Test hook: writes a whole deterministic board in one call —
    /// <c>"piece=1;x=7;y=18;rot=0;board=....|...."</c> (20 rows of <see cref="Columns"/>
    /// characters each, <c>#</c> or <c>1</c> = filled).
    ///
    /// <para>Gravity is switched OFF here, so a session's aim and the next readback are
    /// the same fact. A test that wants to watch gravity calls <see cref="SetGravity"/>
    /// itself, which is why "the piece fell" can never be an accident of timing.</para>
    /// </summary>
    public string ForceTestState(string spec)
    {
        Gravity = false;
        Score = 0;
        Lines = 0;
        Level = 1;
        Ticks = 0;
        _locks = 0;
        GameOver = false;
        _accum = 0.0f;
        for (var i = 0; i < _cells.Length; i++)
        {
            _cells[i] = false;
        }

        PieceRot = 0;
        NextKind = (PieceKind + 1) % Tetromino.KindCount;

        foreach (var part in spec.Split(';'))
        {
            var kv = part.Split('=');
            if (kv.Length != 2)
            {
                continue;
            }
            var key = kv[0].Trim();
            var val = kv[1].Trim();
            switch (key)
            {
                case "piece": PieceKind = int.Parse(val); break;
                case "x": PieceX = int.Parse(val); break;
                case "y": PieceY = int.Parse(val); break;
                case "rot": PieceRot = int.Parse(val); break;
                case "next": NextKind = int.Parse(val); break;
                case "board": WriteBoard(val); break;
            }
        }

        Recount();
        QueueRedraw();
        LastEvent = $"force {spec}";
        GD.Print($"TETRIS_FORCE {Dump()}");
        return LastEvent;
    }

    /// <summary>Writes the playfield from a '/'-separated 20-row text.</summary>
    public string WriteBoard(string rows)
    {
        // Both separators are accepted: the session payload writes '|' (a ';'- and '='-free
        // character), while Dump() prints '/'. Defect T-1 of the first round: the spec used
        // '|' and this method only split on '/', so the whole board landed in row 0 and the
        // assertion about FilledCells read 0 while the call honestly reported success.
        var parts = rows.Replace('|', '/').Split('/');
        for (var r = 0; r < Rows && r < parts.Length; r++)
        {
            var row = parts[r];
            for (var c = 0; c < Columns; c++)
            {
                _cells[r * Columns + c] = c < row.Length && (row[c] == '#' || row[c] == '1');
            }
        }
        Recount();
        QueueRedraw();
        return $"board rows={parts.Length} filled={FilledCells}";
    }

    /// <summary>One gravity step: down if it fits, otherwise lock.</summary>
    public bool StepDown()
    {
        if (GameOver)
        {
            return false;
        }
        if (!Collides(PieceKind, PieceRot, PieceX, PieceY + 1))
        {
            PieceY++;
            Ticks++;
            QueueRedraw();
            return false;
        }
        LockPiece();
        return true;
    }

    /// <summary>Drops the piece to its resting row and locks it there.</summary>
    public string HardDrop()
    {
        if (GameOver)
        {
            return $"already over score={Score} lines={Lines}";
        }
        var dropped = 0;
        while (!Collides(PieceKind, PieceRot, PieceX, PieceY + 1))
        {
            PieceY++;
            dropped++;
        }
        var kind = Tetromino.Names[PieceKind];
        LockPiece();
        // Read back AFTER the lock: defect T-2 of the first round was that this string was
        // built before LockPiece(), so the one readback a session is most likely to quote
        // ("what did the hard drop do?") reported the state of the previous step.
        LastEvent = $"harddrop dropped={dropped} piece={kind} score={Score} lines={Lines} over={GameOver}";
        GD.Print($"TETRIS_HARDDROP piece={kind} x={PieceX} dropped={dropped} "
                 + $"score={Score} lines={Lines} over={GameOver}");
        return LastEvent;
    }

    /// <summary>Tries a horizontal or rotational move; a refused move is recorded, not silently obeyed.</summary>
    public bool TryMove(int dx, int dy, int drot)
    {
        if (GameOver)
        {
            return false;
        }
        var rot = ((PieceRot + drot) % Tetromino.RotationCount + Tetromino.RotationCount) % Tetromino.RotationCount;
        if (Collides(PieceKind, rot, PieceX + dx, PieceY + dy))
        {
            LastEvent = $"refused dx={dx} dy={dy} drot={drot}";
            GD.Print($"TETRIS_REFUSED dx={dx} dy={dy} drot={drot} at={PieceX},{PieceY},{PieceRot}");
            return false;
        }
        PieceX += dx;
        PieceY += dy;
        PieceRot = rot;
        QueueRedraw();
        return true;
    }

    /// <summary>Locks the piece into the playfield, clears lines, spawns the next piece.</summary>
    private void LockPiece()
    {
        Tetromino.Cells(PieceKind, PieceRot, _shape);
        var above = false;
        for (var i = 0; i < 4; i++)
        {
            var bx = PieceX + _shape[i * 2];
            var by = PieceY + _shape[i * 2 + 1];
            if (by < 0)
            {
                above = true;
                continue;
            }
            if (InBounds(bx, by))
            {
                _cells[by * Columns + bx] = true;
            }
        }
        _locks++;
        Recount();
        var cleared = ClearFullLines();
        GD.Print($"TETRIS_LOCK piece={Tetromino.Names[PieceKind]} filled={FilledCells} cleared={cleared} "
                 + $"score={Score} lines={Lines} above={above}");
        SpawnPiece(NextKind);
        QueueRedraw();
    }

    /// <summary>Removes the full rows and reports how many went.</summary>
    public int ClearFullLines()
    {
        var cleared = 0;
        for (var r = Rows - 1; r >= 0; r--)
        {
            var full = true;
            for (var c = 0; c < Columns; c++)
            {
                if (!_cells[r * Columns + c])
                {
                    full = false;
                    break;
                }
            }
            if (!full)
            {
                continue;
            }
            cleared++;
            for (var rr = r; rr > 0; rr--)
            {
                for (var c = 0; c < Columns; c++)
                {
                    _cells[rr * Columns + c] = _cells[(rr - 1) * Columns + c];
                }
            }
            for (var c = 0; c < Columns; c++)
            {
                _cells[c] = false;
            }
            r++;
        }
        if (cleared > 0 && cleared < LineScores.Length)
        {
            Score += LineScores[cleared];
            Lines += cleared;
            Level = 1 + Lines / 10;
            GD.Print($"TETRIS_CLEAR lines={cleared} total={Lines} score={Score} level={Level}");
        }
        Recount();
        return cleared;
    }

    /// <summary>Puts the next piece at the top; a piece that cannot be placed ends the game.</summary>
    private void SpawnPiece(int kind)
    {
        PieceKind = ((kind % Tetromino.KindCount) + Tetromino.KindCount) % Tetromino.KindCount;
        PieceX = 3;
        PieceY = 0;
        PieceRot = 0;
        NextKind = (PieceKind + 1) % Tetromino.KindCount;
        if (Collides(PieceKind, PieceRot, PieceX, PieceY))
        {
            GameOver = true;
            LastEvent = $"gameover spawn blocked kind={Tetromino.Names[PieceKind]} score={Score} lines={Lines}";
            GD.Print($"TETRIS_GAMEOVER spawn_blocked kind={Tetromino.Names[PieceKind]} score={Score} lines={Lines}");
        }
    }

    private bool InBounds(int c, int r)
    {
        return c >= 0 && c < Columns && r >= 0 && r < Rows;
    }

    /// <summary>Recomputes the two digests after any write.</summary>
    private void Recount()
    {
        var filled = 0;
        var hash = 0;
        for (var i = 0; i < _cells.Length; i++)
        {
            if (!_cells[i])
            {
                continue;
            }
            filled++;
            hash += i + 1;
        }
        FilledCells = filled;
        BoardHash = hash;
    }

    public override void _Process(double delta)
    {
        if (GameOver)
        {
            return;
        }
        var dt = (float)delta;
        if (Gravity)
        {
            _accum += dt;
            var guard = 0;
            while (_accum >= DropInterval && !GameOver && guard < 64)
            {
                _accum -= DropInterval;
                guard++;
                StepDown();
            }
        }
        _logTimer += dt;
        if (_logTimer < 0.5f)
        {
            return;
        }
        _logTimer = 0.0f;
        GD.Print($"TETRIS_TICK piece={Tetromino.Names[PieceKind]} at={PieceX},{PieceY},{PieceRot} "
                 + $"filled={FilledCells} score={Score} lines={Lines} over={GameOver} ticks={Ticks}");
    }

    public override void _Input(InputEvent @event)
    {
        if (@event.IsActionPressed("tetris_left")) { TryMove(-1, 0, 0); }
        if (@event.IsActionPressed("tetris_right")) { TryMove(1, 0, 0); }
        if (@event.IsActionPressed("tetris_rotate")) { TryMove(0, 0, 1); }
        if (@event.IsActionPressed("tetris_down")) { StepDown(); }
        if (@event.IsActionPressed("tetris_drop")) { HardDrop(); }
    }

    public override void _Draw()
    {
        // Playfield background and border.
        DrawRect(new Rect2(BoardX - 2, BoardY - 2, Columns * CellSize + 4, Rows * CellSize + 4),
                 new Color(0.16f, 0.18f, 0.24f, 1f), true);
        DrawRect(new Rect2(BoardX, BoardY, Columns * CellSize, Rows * CellSize),
                 new Color(0.05f, 0.06f, 0.09f, 1f), true);

        // Locked cells.
        var locked = new Color(0.55f, 0.62f, 0.72f, 1f);
        for (var r = 0; r < Rows; r++)
        {
            for (var c = 0; c < Columns; c++)
            {
                if (!_cells[r * Columns + c])
                {
                    continue;
                }
                DrawRect(new Rect2(BoardX + c * CellSize, BoardY + r * CellSize, CellSize - 1, CellSize - 1), locked, true);
            }
        }

        // The falling piece.
        Tetromino.Cells(PieceKind, PieceRot, _shape);
        var color = Tetromino.Colors[PieceKind];
        for (var i = 0; i < 4; i++)
        {
            var bx = PieceX + _shape[i * 2];
            var by = PieceY + _shape[i * 2 + 1];
            if (by < 0)
            {
                continue;
            }
            DrawRect(new Rect2(BoardX + bx * CellSize, BoardY + by * CellSize, CellSize - 1, CellSize - 1), color, true);
        }
    }
}
