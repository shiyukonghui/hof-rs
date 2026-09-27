using Godot;
using System.Collections.Generic;
using System.Text;

namespace sokoban;

/// <summary>
/// Sokoban -- the twelfth C# game of the godot-mcp series (TASK-101, DECISIONS.md D138).
///
/// <para><b>Design rule</b> (inherited from the eleven games before it): every fact the evidence
/// model needs is a real Godot property on the root node -- <see cref="Cols"/>, <see cref="Rows"/>,
/// <see cref="GoalsTotal"/>, <see cref="BoxesTotal"/>, <see cref="BoxesOnGoal"/>,
/// <see cref="BoxList"/>, <see cref="GoalList"/>, <see cref="BoardHash"/>, <see cref="PlayerRow"/>,
/// <see cref="PlayerCol"/>, <see cref="Steps"/>, <see cref="Pushes"/>, <see cref="Undone"/>,
/// <see cref="RejectedMoves"/>, <see cref="Deadlocked"/>, <see cref="DeadlockList"/>,
/// <see cref="Won"/>, <see cref="GameOver"/>, <see cref="Elapsed"/>, <see cref="Ticks"/>. A session
/// asserts these with <c>running_game_assert_node_state</c>; it never parses a log line.</para>
///
/// <para><b>Determinism rule.</b> The whole board is a pure function of a level string, and it is
/// pinned with ONE <see cref="ForceTestState"/> call. Nothing moves on its own:
/// <see cref="AutoPush"/> is 0 and <see cref="PollInput"/> is false by default, and the only other
/// ways to change the board are the named hooks <see cref="Move"/>, <see cref="Undo"/> and
/// <see cref="AutoStep"/>.</para>
///
/// <para><b>Frame-rate independence (the F-1 lesson).</b> The auto-push clock is a FLOAT ACCUMULATOR
/// (<c>_autoAccum += delta * AutoPush</c>), never <c>(int)(delta * rate)</c>. Two producers, two
/// properties: <see cref="LastAutoSteps"/> is what the clock applied on the last frame and
/// <see cref="LastHookSteps"/> is what the last <see cref="AutoStep"/> CALL applied. 2048's r1 run
/// (TASK-100, defect G1) proved a single property read by both producers reads the wrong number.
/// <see cref="Elapsed"/> is a monotonic float second counter that is never truncated.</para>
///
/// <para><b>Rules.</b> The player moves one cell orthogonally; a move into a wall or into the void is
/// refused, and a move that would push a box into a wall, the void, or another box is refused -- in
/// both cases the board is left exactly as it was and <see cref="RejectedMoves"/> grows. A push that
/// succeeds is recorded on the undo stack (<see cref="Undo"/> rolls the player and the box back
/// together). After every change a SIMPLE deadlock check runs: a box that is not on a goal and is
/// either wedged in a corner or part of a 2x2 block of walls/boxes is dead (<see cref="DeadlockList"/>
/// names them), and a dead board is lost. Every box on a goal is the win.</para>
///
/// <para><b>All cells are runtime-created.</b> <see cref="_Ready"/> builds one <c>ColorRect</c> and one
/// <c>Label</c> per cell plus one moving <c>ColorRect</c> for the player; the scene file carries only
/// the three static nodes (Background, Hud, Status). That keeps the edited scene small, keeps it
/// immune to the D-3 duplicate-name trap, and makes "a node created at run time really is drawn" part
/// of this game's own evidence.</para>
/// </summary>
public partial class SokobanGame : Node2D
{
    // --- the level catalogue (the default board is Levels[0]) ---------------------
    private static readonly string[] Levels =
    {
        // 0: one box, one goal, one push away -- the intro board.
        "#######/#     #/# .$@ #/#     #/#######",
        // 1: two boxes, two goals, a corridor push of two cells.
        "#######/#  .  #/#  $  #/#. $ @#/#     #/#######",
        // 2: two boxes, two goals, a turn between the two pushes.
        "########/# .  . #/# $  $ #/#   @  #/########",
        // 3: a corner deadlock waiting for one push to trigger it.
        "######/##.  #/#$   #/#  @ #/######",
    };

    /// <summary>The deterministic patrol the auto-push clock walks: up, right, down, left.</summary>
    private static readonly string[] Patrol = { "up", "right", "down", "left" };

    // --- the grid ---------------------------------------------------------------
    /// <summary>Columns of the board.</summary>
    [Export] public int Cols = 0;

    /// <summary>Rows of the board.</summary>
    [Export] public int Rows = 0;

    /// <summary>Size of one cell in pixels.</summary>
    [Export] public int Cell = 64;

    /// <summary>Left edge of the board in pixels.</summary>
    [Export] public int OriginX = 168;

    /// <summary>Top edge of the board in pixels.</summary>
    [Export] public int OriginY = 90;

    /// <summary>Index of the level currently loaded.</summary>
    [Export] public int LevelIndex = 0;

    /// <summary>The level string currently loaded, rows separated by '/'.</summary>
    [Export] public string LevelSpec = "";

    // --- observable state, all of it a real Godot property ----------------------
    /// <summary>Goals on the board.</summary>
    [Export] public int GoalsTotal = 0;

    /// <summary>Boxes on the board.</summary>
    [Export] public int BoxesTotal = 0;

    /// <summary>Boxes that are sitting on a goal.</summary>
    [Export] public int BoxesOnGoal = 0;

    /// <summary>Boxes that are not on a goal.</summary>
    [Export] public int BoxesOffGoal = 0;

    /// <summary>Box positions in row-major order, "r,c|r,c|..." -- the layout an assert can name.</summary>
    [Export] public string BoxList = "";

    /// <summary>Goal positions in row-major order, "r,c|r,c|...".</summary>
    [Export] public string GoalList = "";

    /// <summary>A stable hash of the whole board: walls, goals, boxes and the player.</summary>
    [Export] public int BoardHash = 0;

    /// <summary>Player row.</summary>
    [Export] public int PlayerRow = 0;

    /// <summary>Player column.</summary>
    [Export] public int PlayerCol = 0;

    /// <summary>Moves accepted, including pushes.</summary>
    [Export] public int Steps = 0;

    /// <summary>Moves that pushed a box.</summary>
    [Export] public int Pushes = 0;

    /// <summary>Undo operations accepted.</summary>
    [Export] public int Undone = 0;

    /// <summary>Moves refused: walls, the void, a box that cannot move, or a finished level.</summary>
    [Export] public int RejectedMoves = 0;

    /// <summary>Depth of the undo stack: how many moves can still be rolled back.</summary>
    [Export] public int UndoDepth = 0;

    /// <summary>True when at least one box is irrecoverably stuck off a goal.</summary>
    [Export] public bool Deadlocked = false;

    /// <summary>How many boxes the deadlock check found dead.</summary>
    [Export] public int DeadlockCount = 0;

    /// <summary>The dead boxes, "r,c|r,c|..." (empty when <see cref="Deadlocked"/> is false).</summary>
    [Export] public string DeadlockList = "";

    /// <summary>True when every box is on a goal.</summary>
    [Export] public bool Won = false;

    /// <summary>True when the level ended, by the win or by a deadlock.</summary>
    [Export] public bool GameOver = false;

    /// <summary>True when a legal move exists.</summary>
    [Export] public bool CanMoveAny = true;

    /// <summary>The direction of the last accepted move.</summary>
    [Export] public string LastDir = "";

    /// <summary>True when the last accepted move pushed a box.</summary>
    [Export] public bool LastPush = false;

    /// <summary>Row the last <see cref="ProbeCell"/> looked at.</summary>
    [Export] public int ProbeRow = -1;

    /// <summary>Column the last <see cref="ProbeCell"/> looked at.</summary>
    [Export] public int ProbeCol = -1;

    /// <summary>Probed cell state: void / wall / floor / goal / box / box_on_goal / player / player_on_goal.</summary>
    [Export] public string ProbeState = "";

    /// <summary>Seconds since the last reset: a monotonic FLOAT accumulator, never truncated.</summary>
    [Export] public float Elapsed = 0.0f;

    /// <summary>Auto-pushes per second; 0 keeps the board still (the default).</summary>
    [Export] public float AutoPush = 0.0f;

    /// <summary>Moves the auto-push clock has applied over the whole level.</summary>
    [Export] public int AutoSteps = 0;

    /// <summary>Moves the auto-push clock applied on the LAST frame (0 while the clock is off).</summary>
    [Export] public int LastAutoSteps = 0;

    /// <summary>
    /// Moves the LAST <see cref="AutoStep"/> CALL applied. Its own property, and the clock never
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

    /// <summary>Moves that arrived through the declared input actions.</summary>
    [Export] public int InputMoves = 0;

    /// <summary>Frames processed since the last reset.</summary>
    [Export] public int Ticks = 0;

    /// <summary>What the last hook did -- the readback string a session quotes.</summary>
    [Export] public string LastEvent = "";

    // --- private model ---------------------------------------------------------
    private bool[] _wall = new bool[1];
    private bool[] _void = new bool[1];
    private bool[] _goal = new bool[1];
    private bool[] _box = new bool[1];
    private readonly List<string> _undo = new List<string>();
    private readonly List<ColorRect> _cellRect = new List<ColorRect>();
    private readonly List<Label> _cellMark = new List<Label>();
    private ColorRect _playerRect;
    private Label _hud;
    private Label _status;
    private float _autoAccum;
    private int _patrolIdx;
    private bool _prevUp;
    private bool _prevRight;
    private bool _prevDown;
    private bool _prevLeft;

    private int Idx(int row, int col)
    {
        return row * Cols + col;
    }

    private bool InBounds(int row, int col)
    {
        return row >= 0 && row < Rows && col >= 0 && col < Cols;
    }

    private bool Blocked(int row, int col)
    {
        return !InBounds(row, col) || _void[Idx(row, col)] || _wall[Idx(row, col)];
    }

    private bool BoxAt(int row, int col)
    {
        return InBounds(row, col) && _box[Idx(row, col)];
    }

    public override void _Ready()
    {
        _hud = GetNodeOrNull<Label>("Hud");
        _status = GetNodeOrNull<Label>("Status");
        LoadLevel(LevelIndex);
        GD.Print($"SOKOBAN_READY level={LevelIndex} cols={Cols} rows={Rows} boxes={BoxesTotal} "
                 + $"goals={GoalsTotal} auto={AutoPush} poll={PollInput}");
    }

    // --- level loading ----------------------------------------------------------
    private void LoadLevel(int index)
    {
        LevelIndex = index;
        LevelSpec = Levels[index];
        ParseLevel(LevelSpec);
        _undo.Clear();
        ResetCounters();
        Recompute();
        CreateNodes();
        ApplyBoard();
        UpdateHud();
    }

    private void ParseLevel(string spec)
    {
        var raw = spec.Split('/');
        Rows = raw.Length;
        Cols = 0;
        foreach (var line in raw)
        {
            if (line.Length > Cols)
            {
                Cols = line.Length;
            }
        }
        var total = Cols * Rows;
        _wall = new bool[total];
        _void = new bool[total];
        _goal = new bool[total];
        _box = new bool[total];
        for (var r = 0; r < Rows; r++)
        {
            var line = raw[r];
            for (var c = 0; c < Cols; c++)
            {
                var ch = c < line.Length ? line[c] : ' ';
                var i = Idx(r, c);
                switch (ch)
                {
                    case '#':
                        _wall[i] = true;
                        break;
                    case '%':
                        // '%' is the void outside the level; a plain space is ordinary FLOOR,
                        // because every level here is fully enclosed by walls.
                        _void[i] = true;
                        break;
                    case '.':
                        _goal[i] = true;
                        break;
                    case '$':
                        _box[i] = true;
                        break;
                    case '*':
                        _box[i] = true;
                        _goal[i] = true;
                        break;
                    case '@':
                        PlayerRow = r;
                        PlayerCol = c;
                        break;
                    case '+':
                        PlayerRow = r;
                        PlayerCol = c;
                        _goal[i] = true;
                        break;
                }
            }
        }
    }

    private void ResetCounters()
    {
        GoalsTotal = 0;
        BoxesTotal = 0;
        BoxesOnGoal = 0;
        BoxesOffGoal = 0;
        BoxList = "";
        GoalList = "";
        BoardHash = 0;
        Steps = 0;
        Pushes = 0;
        Undone = 0;
        RejectedMoves = 0;
        UndoDepth = 0;
        Deadlocked = false;
        DeadlockCount = 0;
        DeadlockList = "";
        Won = false;
        GameOver = false;
        CanMoveAny = true;
        LastDir = "";
        LastPush = false;
        ProbeRow = -1;
        ProbeCol = -1;
        ProbeState = "";
        AutoPush = 0.0f;
        AutoSteps = 0;
        LastAutoSteps = 0;
        LastHookSteps = 0;
        _autoAccum = 0.0f;
        _patrolIdx = 0;
        // TASK-116 D1: was `PollInput = false;` -- that is what
        // switched player input off again right after _Ready() ran.
        // The deterministic entry point is ForceTestState / SetPollInput.
        InputMoves = 0;
        _prevUp = false;
        _prevRight = false;
        _prevDown = false;
        _prevLeft = false;
        Ticks = 0;
    }

    // --- rendering --------------------------------------------------------------
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
        foreach (var mark in _cellMark)
        {
            if (mark != null && IsInstanceValid(mark))
            {
                RemoveChild(mark);
                mark.QueueFree();
            }
        }
        if (_playerRect != null && IsInstanceValid(_playerRect))
        {
            RemoveChild(_playerRect);
            _playerRect.QueueFree();
        }
        _cellRect.Clear();
        _cellMark.Clear();
        for (var r = 0; r < Rows; r++)
        {
            for (var c = 0; c < Cols; c++)
            {
                var i = Idx(r, c);
                var at = new Vector2(OriginX + c * Cell + 2, OriginY + r * Cell + 2);
                var size = new Vector2(Cell - 4, Cell - 4);
                var rect = new ColorRect();
                rect.Name = $"Cell_{r}_{c}";
                rect.Position = at;
                rect.Size = size;
                rect.Color = new Color(0.13f, 0.14f, 0.18f);
                AddChild(rect);
                _cellRect.Add(rect);

                var mark = new Label();
                mark.Name = $"Mark_{r}_{c}";
                mark.Position = at;
                mark.Size = size;
                mark.HorizontalAlignment = HorizontalAlignment.Center;
                mark.VerticalAlignment = VerticalAlignment.Center;
                mark.AddThemeFontSizeOverride("font_size", 30);
                AddChild(mark);
                _cellMark.Add(mark);
            }
        }
        _playerRect = new ColorRect();
        _playerRect.Name = "PlayerSprite";
        _playerRect.Size = new Vector2(Cell - 26, Cell - 26);
        _playerRect.Color = new Color(0.25f, 0.95f, 0.95f);
        AddChild(_playerRect);
    }

    private void ApplyBoard()
    {
        for (var r = 0; r < Rows; r++)
        {
            for (var c = 0; c < Cols; c++)
            {
                var i = Idx(r, c);
                if (i >= _cellRect.Count)
                {
                    continue;
                }
                var rect = _cellRect[i];
                var mark = _cellMark[i];
                if (rect == null || !IsInstanceValid(rect))
                {
                    continue;
                }
                string text;
                Color back;
                Color ink = new Color(0.95f, 0.95f, 0.95f);
                if (_void[i])
                {
                    // The void is drawn as the page background: nothing here at all.
                    rect.Color = new Color(0.05f, 0.06f, 0.08f);
                    text = "";
                    back = rect.Color;
                }
                else if (_wall[i])
                {
                    back = new Color(0.32f, 0.35f, 0.44f);
                    text = "";
                }
                else if (_box[i] && _goal[i])
                {
                    back = new Color(0.20f, 0.62f, 0.32f);
                    text = "X";
                    ink = new Color(0.95f, 1.00f, 0.85f);
                }
                else if (_box[i])
                {
                    back = new Color(0.80f, 0.52f, 0.18f);
                    text = "O";
                    ink = new Color(0.20f, 0.12f, 0.02f);
                }
                else if (_goal[i])
                {
                    back = new Color(0.16f, 0.22f, 0.28f);
                    text = ".";
                    ink = new Color(0.55f, 0.80f, 0.90f);
                }
                else
                {
                    back = new Color(0.13f, 0.14f, 0.18f);
                    text = "";
                }
                rect.Color = back;
                if (mark != null && IsInstanceValid(mark))
                {
                    mark.Text = text;
                    mark.AddThemeColorOverride("font_color", ink);
                }
            }
        }
        if (_playerRect != null && IsInstanceValid(_playerRect))
        {
            _playerRect.Position = new Vector2(OriginX + PlayerCol * Cell + 13,
                                               OriginY + PlayerRow * Cell + 13);
        }
    }

    private void UpdateHud()
    {
        if (_hud != null)
        {
            _hud.Text = $"LEVEL {LevelIndex + 1}  BOXES {BoxesOnGoal}/{BoxesTotal}  "
                        + $"STEPS {Steps}  PUSHES {Pushes}  UNDO {UndoDepth}";
        }
        if (_status != null)
        {
            if (Won)
            {
                _status.Text = "LEVEL CLEARED";
            }
            else if (Deadlocked)
            {
                _status.Text = "STUCK - DEADLOCK";
            }
            else if (GameOver)
            {
                _status.Text = "GAME OVER";
            }
            else
            {
                _status.Text = "PUSH THE BOXES";
            }
        }
    }

    // --- rules ------------------------------------------------------------------
    private static bool DirOf(string dir, out int dr, out int dc)
    {
        switch (dir)
        {
            case "up":
                dr = -1;
                dc = 0;
                return true;
            case "down":
                dr = 1;
                dc = 0;
                return true;
            case "left":
                dr = 0;
                dc = -1;
                return true;
            case "right":
                dr = 0;
                dc = 1;
                return true;
            default:
                dr = 0;
                dc = 0;
                return false;
        }
    }

    private int CellCode(int row, int col)
    {
        if (!InBounds(row, col))
        {
            return 0;
        }
        var i = Idx(row, col);
        if (_void[i])
        {
            return 0;
        }
        if (_wall[i])
        {
            return 2;
        }
        var isPlayer = row == PlayerRow && col == PlayerCol;
        if (_box[i] && _goal[i])
        {
            return isPlayer ? 9 : 5;
        }
        if (_box[i])
        {
            return isPlayer ? 8 : 4;
        }
        if (_goal[i])
        {
            return isPlayer ? 7 : 3;
        }
        return isPlayer ? 6 : 1;
    }

    /// <summary>
    /// The simple deadlock check: a box that is NOT on a goal and is either wedged into a corner
    /// (two perpendicular neighbours are walls/the void) or part of a 2x2 block whose four cells are
    /// all walls or boxes is dead. It is deliberately the classic cheap rule, not a solver.
    /// </summary>
    private bool IsDeadBox(int row, int col)
    {
        if (!_box[Idx(row, col)] || _goal[Idx(row, col)])
        {
            return false;
        }
        var up = Blocked(row - 1, col);
        var down = Blocked(row + 1, col);
        var left = Blocked(row, col - 1);
        var right = Blocked(row, col + 1);
        if ((up && left) || (up && right) || (down && left) || (down && right))
        {
            return true;
        }
        for (var dr = -1; dr <= 0; dr++)
        {
            for (var dc = -1; dc <= 0; dc++)
            {
                var solid = true;
                for (var a = 0; a <= 1; a++)
                {
                    for (var b = 0; b <= 1; b++)
                    {
                        var r = row + dr + a;
                        var c = col + dc + b;
                        if (!InBounds(r, c) || !(_wall[Idx(r, c)] || _box[Idx(r, c)]))
                        {
                            solid = false;
                        }
                    }
                }
                if (solid)
                {
                    return true;
                }
            }
        }
        return false;
    }

    private void Recompute()
    {
        var goals = 0;
        var boxes = 0;
        var onGoal = 0;
        var boxList = new StringBuilder();
        var goalList = new StringBuilder();
        var deadList = new StringBuilder();
        var dead = 0;
        var hash = 17;
        unchecked
        {
            for (var r = 0; r < Rows; r++)
            {
                for (var c = 0; c < Cols; c++)
                {
                    var i = Idx(r, c);
                    if (_goal[i])
                    {
                        goals++;
                        if (goalList.Length > 0)
                        {
                            goalList.Append('|');
                        }
                        goalList.Append(r).Append(',').Append(c);
                    }
                    if (_box[i])
                    {
                        boxes++;
                        if (boxList.Length > 0)
                        {
                            boxList.Append('|');
                        }
                        boxList.Append(r).Append(',').Append(c);
                        if (_goal[i])
                        {
                            onGoal++;
                        }
                    }
                    hash = hash * 31 + CellCode(r, c);
                }
            }
            for (var r = 0; r < Rows; r++)
            {
                for (var c = 0; c < Cols; c++)
                {
                    if (!IsDeadBox(r, c))
                    {
                        continue;
                    }
                    dead++;
                    if (deadList.Length > 0)
                    {
                        deadList.Append('|');
                    }
                    deadList.Append(r).Append(',').Append(c);
                }
            }
        }
        GoalsTotal = goals;
        BoxesTotal = boxes;
        BoxesOnGoal = onGoal;
        BoxesOffGoal = boxes - onGoal;
        BoxList = boxList.ToString();
        GoalList = goalList.ToString();
        BoardHash = hash;
        DeadlockCount = dead;
        DeadlockList = deadList.ToString();
        Deadlocked = dead > 0;
        Won = boxes > 0 && onGoal == boxes;
        GameOver = Won || Deadlocked;
        UndoDepth = _undo.Count;
        var any = false;
        if (!GameOver)
        {
            foreach (var dir in Patrol)
            {
                DirOf(dir, out var dr, out var dc);
                if (TryMove(dir, dr, dc, true))
                {
                    any = true;
                    break;
                }
            }
        }
        CanMoveAny = any;
    }

    /// <summary>
    /// The legality test, shared by the real move and by <see cref="CanMoveAny"/>. With
    /// <paramref name="probe"/> true nothing is written anywhere.
    /// </summary>
    private bool TryMove(string dir, int dr, int dc, bool probe)
    {
        var nr = PlayerRow + dr;
        var nc = PlayerCol + dc;
        if (Blocked(nr, nc))
        {
            return false;
        }
        if (BoxAt(nr, nc))
        {
            var br = nr + dr;
            var bc = nc + dc;
            if (Blocked(br, bc) || BoxAt(br, bc))
            {
                return false;
            }
        }
        return true;
    }

    // --- hooks the session drives ----------------------------------------------

    /// <summary>
    /// Moves the player one cell. A move into a wall, the void, or a box that cannot be pushed is
    /// refused with no board change.
    /// </summary>
    public string Move(string dir)
    {
        if (!DirOf(dir, out var dr, out var dc))
        {
            RejectedMoves++;
            LastEvent = $"rejected reason=bad_dir dir={dir}";
            return LastEvent;
        }
        if (GameOver)
        {
            RejectedMoves++;
            LastEvent = $"rejected reason=game_over dir={dir} won={Won} deadlocked={Deadlocked} "
                        + $"steps={Steps} rejected={RejectedMoves}";
            return LastEvent;
        }
        var nr = PlayerRow + dr;
        var nc = PlayerCol + dc;
        if (Blocked(nr, nc))
        {
            RejectedMoves++;
            LastEvent = $"rejected reason=wall dir={dir} at={nr},{nc} steps={Steps} "
                        + $"rejected={RejectedMoves}";
            return LastEvent;
        }
        var pushed = false;
        if (BoxAt(nr, nc))
        {
            var br = nr + dr;
            var bc = nc + dc;
            if (Blocked(br, bc) || BoxAt(br, bc))
            {
                RejectedMoves++;
                LastEvent = $"rejected reason=blocked_box dir={dir} at={nr},{nc} into={br},{bc} "
                            + $"steps={Steps} rejected={RejectedMoves}";
                return LastEvent;
            }
            _box[Idx(nr, nc)] = false;
            _box[Idx(br, bc)] = true;
            pushed = true;
            Pushes++;
            _undo.Add($"push|{PlayerRow}|{PlayerCol}|{nr}|{nc}|{br}|{bc}");
        }
        else
        {
            _undo.Add($"walk|{PlayerRow}|{PlayerCol}|-1|-1|-1|-1");
        }
        PlayerRow = nr;
        PlayerCol = nc;
        Steps++;
        LastDir = dir;
        LastPush = pushed;
        Recompute();
        ApplyBoard();
        UpdateHud();
        LastEvent = $"moved dir={dir} to={PlayerRow},{PlayerCol} pushed={pushed} steps={Steps} "
                    + $"pushes={Pushes} on_goal={BoxesOnGoal}/{BoxesTotal} won={Won} "
                    + $"deadlocked={Deadlocked}";
        return LastEvent;
    }

    /// <summary>Rolls the player -- and the box a push moved -- back one move.</summary>
    public string Undo()
    {
        if (_undo.Count == 0)
        {
            RejectedMoves++;
            LastEvent = $"rejected reason=nothing_to_undo steps={Steps} rejected={RejectedMoves}";
            return LastEvent;
        }
        var top = _undo[_undo.Count - 1];
        _undo.RemoveAt(_undo.Count - 1);
        var parts = top.Split('|');
        var kind = parts[0];
        var wasRow = int.Parse(parts[1]);
        var wasCol = int.Parse(parts[2]);
        if (kind == "push")
        {
            var boxAtRow = int.Parse(parts[3]);
            var boxAtCol = int.Parse(parts[4]);
            var boxToRow = int.Parse(parts[5]);
            var boxToCol = int.Parse(parts[6]);
            _box[Idx(boxToRow, boxToCol)] = false;
            _box[Idx(boxAtRow, boxAtCol)] = true;
            Pushes--;
        }
        PlayerRow = wasRow;
        PlayerCol = wasCol;
        Steps--;
        Undone++;
        LastDir = "undo";
        LastPush = false;
        Recompute();
        ApplyBoard();
        UpdateHud();
        LastEvent = $"undone kind={kind} now={PlayerRow},{PlayerCol} steps={Steps} "
                    + $"pushes={Pushes} undone={Undone} on_goal={BoxesOnGoal}/{BoxesTotal}";
        return LastEvent;
    }

    /// <summary>Records what is at one cell into the Probe* properties, so an assert can name it.</summary>
    public string ProbeCell(int row, int col)
    {
        ProbeRow = row;
        ProbeCol = col;
        if (!InBounds(row, col) || _void[Idx(row, col)])
        {
            ProbeState = "void";
        }
        else if (_wall[Idx(row, col)])
        {
            ProbeState = "wall";
        }
        else
        {
            var i = Idx(row, col);
            var isPlayer = row == PlayerRow && col == PlayerCol;
            if (_box[i] && _goal[i])
            {
                ProbeState = "box_on_goal";
            }
            else if (_box[i])
            {
                ProbeState = "box";
            }
            else if (_goal[i] && isPlayer)
            {
                ProbeState = "player_on_goal";
            }
            else if (_goal[i])
            {
                ProbeState = "goal";
            }
            else
            {
                ProbeState = isPlayer ? "player" : "floor";
            }
        }
        LastEvent = $"probe at={row},{col} state={ProbeState}";
        return LastEvent;
    }

    /// <summary>One deterministic auto-push: walk one step of the fixed patrol cycle.</summary>
    private bool AutoPushOnce()
    {
        var dir = Patrol[_patrolIdx % Patrol.Length];
        _patrolIdx++;
        var before = Steps;
        Move(dir);
        return Steps > before;
    }

    /// <summary>Applies up to <paramref name="steps"/> deterministic auto-pushes.</summary>
    public string AutoStep(int steps)
    {
        var accepted = 0;
        var attempts = 0;
        for (var i = 0; i < steps; i++)
        {
            attempts++;
            if (GameOver)
            {
                break;
            }
            if (AutoPushOnce())
            {
                accepted++;
                AutoSteps++;
            }
        }
        LastHookSteps = accepted;
        LastEvent = $"autostep requested={steps} attempts={attempts} accepted={accepted} "
                    + $"total={AutoSteps} steps={Steps} on_goal={BoxesOnGoal}/{BoxesTotal}";
        return LastEvent;
    }

    /// <summary>Auto-pushes per second; 0 keeps the board still (the default).</summary>
    public string SetAutoPush(float perSecond)
    {
        AutoPush = perSecond;
        _autoAccum = 0.0f;
        LastAutoSteps = 0;
        LastEvent = $"auto_push={AutoPush}";
        GD.Print($"SOKOBAN_AUTO auto={AutoPush}");
        return LastEvent;
    }

    /// <summary>Switches the declared-input polling on or off (the default is off).</summary>
    public string SetPollInput(bool enabled)
    {
        PollInput = enabled;
        _prevUp = false;
        _prevRight = false;
        _prevDown = false;
        _prevLeft = false;
        LastEvent = $"poll_input={PollInput}";
        return LastEvent;
    }

    private void HandleInput()
    {
        var up = Input.IsActionPressed("soko_up");
        var right = Input.IsActionPressed("soko_right");
        var down = Input.IsActionPressed("soko_down");
        var left = Input.IsActionPressed("soko_left");
        // Press edges only: a key a scenario injected and never released performs exactly one move
        // instead of repeating at the frame rate.
        if (up && !_prevUp && DoInput("up"))
        {
            InputMoves++;
        }
        if (right && !_prevRight && DoInput("right"))
        {
            InputMoves++;
        }
        if (down && !_prevDown && DoInput("down"))
        {
            InputMoves++;
        }
        if (left && !_prevLeft && DoInput("left"))
        {
            InputMoves++;
        }
        _prevUp = up;
        _prevRight = right;
        _prevDown = down;
        _prevLeft = left;
    }

    private bool DoInput(string dir)
    {
        var before = Steps;
        Move(dir);
        return Steps > before;
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
        if (AutoPush > 0.0f)
        {
            _autoAccum += dt * AutoPush; // F-1's fix: accumulate, never (int)(delta * rate)
            var applied = 0;
            var guard = 0;
            while (_autoAccum >= 1.0f && guard < 8)
            {
                _autoAccum -= 1.0f;
                guard++;
                if (AutoPushOnce())
                {
                    AutoSteps++;
                    applied++;
                }
                if (GameOver)
                {
                    break;
                }
            }
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
        var sb = new StringBuilder();
        for (var r = 0; r < Rows; r++)
        {
            for (var c = 0; c < Cols; c++)
            {
                var i = Idx(r, c);
                if (_void[i])
                {
                    sb.Append(' ');
                }
                else if (_wall[i])
                {
                    sb.Append('#');
                }
                else if (r == PlayerRow && c == PlayerCol)
                {
                    sb.Append(_goal[i] ? '+' : '@');
                }
                else if (_box[i])
                {
                    sb.Append(_goal[i] ? '*' : '$');
                }
                else if (_goal[i])
                {
                    sb.Append('.');
                }
                else
                {
                    sb.Append(' ');
                }
            }
            if (r + 1 < Rows)
            {
                sb.Append('/');
            }
        }
        return $"level={LevelIndex} board={sb} cols={Cols} rows={Rows} goals={GoalsTotal} "
               + $"boxes={BoxesTotal} on_goal={BoxesOnGoal} off_goal={BoxesOffGoal} "
               + $"box_list={BoxList} goal_list={GoalList} hash={BoardHash} "
               + $"player={PlayerRow},{PlayerCol} steps={Steps} pushes={Pushes} undone={Undone} "
               + $"rejected={RejectedMoves} undo_depth={UndoDepth} deadlocked={Deadlocked} "
               + $"dead_count={DeadlockCount} dead_list={DeadlockList} won={Won} over={GameOver} "
               + $"can_move={CanMoveAny} last_dir={LastDir} last_push={LastPush} "
               + $"probe={ProbeRow},{ProbeCol}:{ProbeState} auto={AutoPush} auto_steps={AutoSteps} "
               + $"last_auto={LastAutoSteps} last_hook={LastHookSteps} input_moves={InputMoves} "
               + $"elapsed={Elapsed:F3} ticks={Ticks} last={LastEvent}";
    }

    /// <summary>
    /// Writes the whole deterministic state in one call:
    /// <c>"level=N"</c> or <c>"level=&lt;rows separated by /&gt;"</c>, plus optional
    /// <c>;player=r,c</c> to move the player without touching anything else.
    ///
    /// <para>The auto-push clock and input polling are switched OFF first, so a session's aim and the
    /// next readback are the same fact. A test that wants motion calls <see cref="SetAutoPush"/> or
    /// <see cref="AutoStep"/> itself -- which is why "a box moved" can never be an accident of
    /// timing.</para>
    /// </summary>
    public string ForceTestState(string spec)
    {
        var levelArg = "";
        var playerArg = "";
        foreach (var part in spec.Split(';'))
        {
            var kv = part.Split(new[] { '=' }, 2);
            if (kv.Length != 2)
            {
                continue;
            }
            if (kv[0] == "level")
            {
                levelArg = kv[1];
            }
            else if (kv[0] == "player")
            {
                playerArg = kv[1];
            }
        }
        if (levelArg.Length > 0)
        {
            int index;
            if (int.TryParse(levelArg, out index) && index >= 0 && index < Levels.Length)
            {
                LevelIndex = index;
                LevelSpec = Levels[index];
            }
            else
            {
                LevelSpec = levelArg;
                LevelIndex = -1;
            }
            ParseLevel(LevelSpec);
            _undo.Clear();
            ResetCountersKeepLevel();
        }
        if (playerArg.Length > 0)
        {
            var p = playerArg.Split(',');
            if (p.Length == 2)
            {
                PlayerRow = int.Parse(p[0]);
                PlayerCol = int.Parse(p[1]);
            }
        }
        Recompute();
        if (_cellRect.Count != Cols * Rows)
        {
            CreateNodes();
        }
        ApplyBoard();
        UpdateHud();
        LastEvent = $"forced level={LevelIndex} boxes={BoxesTotal} goals={GoalsTotal} "
                    + $"on_goal={BoxesOnGoal} player={PlayerRow},{PlayerCol} over={GameOver} "
                    + $"won={Won} deadlocked={Deadlocked}";
        return LastEvent;
    }

    /// <summary>Resets the per-level counters without touching the cells that were just parsed.</summary>
    private void ResetCountersKeepLevel()
    {
        Steps = 0;
        Pushes = 0;
        Undone = 0;
        RejectedMoves = 0;
        UndoDepth = 0;
        LastDir = "";
        LastPush = false;
        ProbeRow = -1;
        ProbeCol = -1;
        ProbeState = "";
        AutoPush = 0.0f;
        AutoSteps = 0;
        LastAutoSteps = 0;
        LastHookSteps = 0;
        _autoAccum = 0.0f;
        _patrolIdx = 0;
        // TASK-116 D1: was `PollInput = false;` -- that is what
        // switched player input off again right after _Ready() ran.
        // The deterministic entry point is ForceTestState / SetPollInput.
        InputMoves = 0;
        _prevUp = false;
        _prevRight = false;
        _prevDown = false;
        _prevLeft = false;
        Ticks = 0;
    }
}
