using Godot;
using System.Collections.Generic;
using System.Text;

namespace frogger;

/// <summary>
/// Frogger -- the eighth C# game of the godot-mcp series (TASK-099, DECISIONS.md D138).
///
/// <para><b>Design rule</b> (inherited from Pong / Breakout / Snake / Tetris / Space Invaders /
/// Asteroids / Pac-Man): every fact the evidence model needs is a real Godot property on the root
/// node -- <see cref="FrogCol"/>, <see cref="FrogRow"/>, <see cref="FrogX"/>, <see cref="FrogY"/>,
/// <see cref="Score"/>, <see cref="Lives"/>, <see cref="HomesReached"/>, <see cref="TotalHomes"/>,
/// <see cref="TrafficSteps"/>, <see cref="LastTrafficSteps"/>, <see cref="Car0Col"/>,
/// <see cref="Log0Col"/>, <see cref="GameOver"/>, <see cref="Won"/>, <see cref="Ticks"/>. A
/// session asserts these with <c>running_game_assert_node_state</c>; it never parses a log line.</para>
///
/// <para><b>Determinism rule.</b> Two things are OFF by default and each is switched on only by an
/// explicit test call: the traffic does not move on its own (<see cref="CarSpeed"/> = 0) and the
/// frog does not poll input (<see cref="PollInput"/> = false). Every crossing is reachable through
/// a fixed-step hook (<see cref="StepFrog"/>, <see cref="StepTraffic"/>), so "the frog crossed" or
/// "a car hit the frog" can never be an accident of frame timing. <see cref="ForceTestState"/>
/// pins the whole board in one call.</para>
///
/// <para><b>The board is a grid.</b> Rows 9..13 are the road (one car per lane), row 8 is the
/// median, rows 3..7 are the river (one two-cell log per row), rows 1..2 are the far bank, row 0 is
/// the goal line and row 14 is the start bank. A frog on a road cell a car occupies loses a life;
/// a frog on a river cell no log covers drowns; a frog that reaches row 0 fills one home and
/// scores 50. Five homes clear the course.</para>
///
/// <para><b>Cars, logs and the frog are all runtime-created.</b> <see cref="_Ready"/> builds one
/// <c>ColorRect</c> per car, per log and for the frog; the scene file carries only the three static
/// nodes (Background, Hud, Status). That keeps the edited scene small, keeps it immune to the D-3
/// duplicate-name trap, and makes "a node created at run time really is drawn" part of this game's
/// own evidence.</para>
///
/// <para><b>Scoring has exactly one source.</b> One home = 50 points; nothing else scores. An
/// assertion about <see cref="Score"/> therefore names the home that produced it.</para>
/// </summary>
public partial class FroggerGame : Node2D
{
    // --- the grid ---------------------------------------------------------------
    /// <summary>Columns of the board.</summary>
    [Export] public int Cols = 13;

    /// <summary>Rows of the board.</summary>
    [Export] public int Rows = 15;

    /// <summary>Size of one cell in pixels.</summary>
    [Export] public int Cell = 36;

    /// <summary>Left edge of the board in pixels.</summary>
    [Export] public int OriginX = 166;

    /// <summary>Top edge of the board in pixels.</summary>
    [Export] public int OriginY = 50;

    /// <summary>First road row.</summary>
    [Export] public int RoadTop = 9;

    /// <summary>Last road row.</summary>
    [Export] public int RoadBottom = 13;

    /// <summary>First river row.</summary>
    [Export] public int RiverTop = 3;

    /// <summary>Last river row.</summary>
    [Export] public int RiverBottom = 7;

    /// <summary>The goal line: reaching this row fills one home.</summary>
    [Export] public int GoalRow = 0;

    /// <summary>The start bank row.</summary>
    [Export] public int StartRow = 14;

    /// <summary>The frog's start column.</summary>
    [Export] public int StartCol = 6;

    /// <summary>The frog's size in pixels.</summary>
    [Export] public float FrogSize = 24.0f;

    /// <summary>How many cells a log carries.</summary>
    [Export] public int LogLen = 2;

    // --- observable state, all of it a real Godot property ---------------------
    /// <summary>The frog's column.</summary>
    [Export] public int FrogCol = 6;

    /// <summary>The frog's row.</summary>
    [Export] public int FrogRow = 14;

    /// <summary>The frog's centre x in pixels.</summary>
    [Export] public float FrogX = 0.0f;

    /// <summary>The frog's centre y in pixels.</summary>
    [Export] public float FrogY = 0.0f;

    /// <summary>Points: 50 per home reached.</summary>
    [Export] public int Score = 0;

    /// <summary>Lives left. A car hit or a drowning costs exactly one.</summary>
    [Export] public int Lives = 3;

    /// <summary>Homes filled so far.</summary>
    [Export] public int HomesReached = 0;

    /// <summary>Homes needed to clear the course.</summary>
    [Export] public int TotalHomes = 5;

    /// <summary>Traffic steps taken (by the hook or by the clock).</summary>
    [Export] public int TrafficSteps = 0;

    /// <summary>Steps the LAST <see cref="StepTraffic"/> call took. A patch of the total alone
    /// cannot be asserted exactly: the clock may have advanced the traffic before the hook ran.</summary>
    [Export] public int LastTrafficSteps = 0;

    /// <summary>How many cars are on the road.</summary>
    [Export] public int CarCount = 0;

    /// <summary>Column of car 0 -- a real property, so a multi-frame sample can show traffic move.</summary>
    [Export] public int Car0Col = -1;

    /// <summary>Row of car 0.</summary>
    [Export] public int Car0Row = -1;

    /// <summary>Left edge of car 0 in pixels.</summary>
    [Export] public float Car0X = 0.0f;

    /// <summary>How many logs are on the river.</summary>
    [Export] public int LogCount = 0;

    /// <summary>Left column of log 0.</summary>
    [Export] public int Log0Col = -1;

    /// <summary>Row of log 0.</summary>
    [Export] public int Log0Row = -1;

    /// <summary>Left edge of log 0 in pixels.</summary>
    [Export] public float Log0X = 0.0f;

    /// <summary>Length of log 0 in cells.</summary>
    [Export] public int Log0Len = 0;

    /// <summary>True when the last home is filled (win) or the last life is gone (loss).</summary>
    [Export] public bool GameOver = false;

    /// <summary>True when <see cref="GameOver"/> was reached by filling every home.</summary>
    [Export] public bool Won = false;

    /// <summary>Traffic steps per second; 0 keeps the cars and logs still (the default).</summary>
    [Export] public float CarSpeed = 0.0f;

    /// <summary>When false the frog ignores input (determinism rule: no polling by default).</summary>
    [Export] public bool PollInput = false;

    /// <summary>Seconds between two input-driven cell moves, so a held key is a range and not a race.</summary>
    [Export] public float InputRepeat = 0.12f;

    /// <summary>Frames processed since the last reset.</summary>
    [Export] public int Ticks = 0;

    /// <summary>What the last hook did -- the readback string a session quotes.</summary>
    [Export] public string LastEvent = "";

    // --- private model ---------------------------------------------------------
    private class Car
    {
        public int Col;
        public int Row;
        public int Dir;
        public ColorRect Node;
    }

    private class Log
    {
        public int Col;
        public int Row;
        public int Dir;
        public ColorRect Node;
    }

    private readonly List<Car> _cars = new List<Car>();
    private readonly List<Log> _logs = new List<Log>();
    private ColorRect _frog;
    private ColorRect _bg;
    private Label _hud;
    private Label _status;
    private float _trafficAccum;
    private float _inputAccum;

    /// <summary>Where the five cars start: one per road lane, alternating direction.</summary>
    private static readonly int[,] CarStart =
    {
        { 0, 9, 1 }, { 12, 10, -1 }, { 3, 11, 1 }, { 9, 12, -1 }, { 6, 13, 1 },
    };

    /// <summary>Where the five logs start: one per river row, alternating direction.</summary>
    private static readonly int[,] LogStart =
    {
        { 0, 3, 1 }, { 11, 4, -1 }, { 4, 5, 1 }, { 8, 6, -1 }, { 1, 7, 1 },
    };

    public override void _Ready()
    {
        _bg = GetNodeOrNull<ColorRect>("Background");
        _hud = GetNodeOrNull<Label>("Hud");
        _status = GetNodeOrNull<Label>("Status");
        BuildBoard();
        UpdateHud();
        GD.Print($"FROGGER_READY cols={Cols} rows={Rows} cars={CarCount} logs={LogCount} "
                 + $"frog={FrogCol},{FrogRow} speed={CarSpeed} poll={PollInput}");
    }

    private ColorRect MakeRect(string name, Vector2 size, Color color)
    {
        var node = new ColorRect();
        node.Name = name;
        node.Size = size;
        node.PivotOffset = size / 2.0f;
        node.Color = color;
        AddChild(node);
        return node;
    }

    /// <summary>
    /// Removes a runtime node from the tree and then frees it.
    ///
    /// <para>The order matters, and it is the same trap D-3 is about: <c>QueueFree()</c> alone
    /// leaves the node in the tree until the end of the frame, so a rebuild that recreates a name
    /// like <c>Car_0</c> in the same frame would find that name still taken and Godot would quietly
    /// rename the new node to <c>@ColorRect@NNN</c>. <c>RemoveChild()</c> first releases the name
    /// immediately.</para>
    /// </summary>
    private void DropNode(Node node)
    {
        if (node == null || !IsInstanceValid(node))
        {
            return;
        }
        if (node.GetParent() == this)
        {
            RemoveChild(node);
        }
        node.QueueFree();
    }

    /// <summary>Builds the whole board: the terrain strip, the cars, the logs and the frog.</summary>
    private void BuildBoard()
    {
        foreach (var child in GetChildren())
        {
            var node = child as Node;
            if (node == null)
            {
                continue;
            }
            var name = node.Name.ToString();
            if (name == "Hud" || name == "Status" || name == "Background" || name == "Frog")
            {
                continue;
            }
            DropNode(node);
        }
        _cars.Clear();
        _logs.Clear();
        var road = MakeRect("RoadStrip", new Vector2(Cols * Cell, (RoadBottom - RoadTop + 1) * Cell),
                            new Color(0.16f, 0.16f, 0.18f));
        road.Position = new Vector2(OriginX, OriginY + RoadTop * Cell);
        var river = MakeRect("RiverStrip", new Vector2(Cols * Cell, (RiverBottom - RiverTop + 1) * Cell),
                             new Color(0.08f, 0.20f, 0.42f));
        river.Position = new Vector2(OriginX, OriginY + RiverTop * Cell);
        var goal = MakeRect("GoalStrip", new Vector2(Cols * Cell, Cell), new Color(0.10f, 0.32f, 0.14f));
        goal.Position = new Vector2(OriginX, OriginY + GoalRow * Cell);
        var start = MakeRect("StartStrip", new Vector2(Cols * Cell, Cell), new Color(0.10f, 0.32f, 0.14f));
        start.Position = new Vector2(OriginX, OriginY + StartRow * Cell);

        for (var i = 0; i < CarStart.GetLength(0); i++)
        {
            var car = new Car { Col = CarStart[i, 0], Row = CarStart[i, 1], Dir = CarStart[i, 2] };
            car.Node = MakeRect($"Car_{i}", new Vector2(Cell - 4, Cell - 10),
                                i % 2 == 0 ? new Color(0.95f, 0.85f, 0.20f) : new Color(0.90f, 0.35f, 0.30f));
            _cars.Add(car);
        }
        for (var i = 0; i < LogStart.GetLength(0); i++)
        {
            var log = new Log { Col = LogStart[i, 0], Row = LogStart[i, 1], Dir = LogStart[i, 2] };
            log.Node = MakeRect($"Log_{i}", new Vector2(LogLen * Cell - 4, Cell - 12),
                                new Color(0.55f, 0.38f, 0.20f));
            _logs.Add(log);
        }
        if (_frog == null || !IsInstanceValid(_frog))
        {
            _frog = MakeRect("Frog", new Vector2(FrogSize, FrogSize), new Color(0.35f, 0.95f, 0.35f));
        }
        FrogCol = StartCol;
        FrogRow = StartRow;
        CarCount = _cars.Count;
        LogCount = _logs.Count;
        TrafficSteps = 0;
        LastTrafficSteps = 0;
        ApplyCars();
        ApplyLogs();
        ApplyFrog();
    }

    private Vector2 CellPosition(int col, int row, float w, float h)
    {
        return new Vector2(OriginX + col * Cell + (Cell - w) / 2.0f,
                           OriginY + row * Cell + (Cell - h) / 2.0f);
    }

    private bool OnRoad(int row)
    {
        return row >= RoadTop && row <= RoadBottom;
    }

    private bool OnRiver(int row)
    {
        return row >= RiverTop && row <= RiverBottom;
    }

    private void ApplyFrog()
    {
        if (_frog == null)
        {
            return;
        }
        FrogX = CellPosition(FrogCol, FrogRow, FrogSize, FrogSize).X + FrogSize / 2.0f;
        FrogY = CellPosition(FrogCol, FrogRow, FrogSize, FrogSize).Y + FrogSize / 2.0f;
        _frog.Position = CellPosition(FrogCol, FrogRow, FrogSize, FrogSize);
    }

    private void ApplyCars()
    {
        foreach (var car in _cars)
        {
            if (car.Node == null)
            {
                continue;
            }
            car.Node.Position = CellPosition(car.Col, car.Row, Cell - 4, Cell - 10);
        }
        if (_cars.Count > 0)
        {
            Car0Col = _cars[0].Col;
            Car0Row = _cars[0].Row;
            Car0X = CellPosition(_cars[0].Col, _cars[0].Row, Cell - 4, Cell - 10).X;
        }
        else
        {
            Car0Col = -1;
            Car0Row = -1;
            Car0X = -1.0f;
        }
    }

    private void ApplyLogs()
    {
        foreach (var log in _logs)
        {
            if (log.Node == null)
            {
                continue;
            }
            log.Node.Position = CellPosition(log.Col, log.Row, LogLen * Cell - 4, Cell - 12);
        }
        if (_logs.Count > 0)
        {
            Log0Col = _logs[0].Col;
            Log0Row = _logs[0].Row;
            Log0X = CellPosition(_logs[0].Col, _logs[0].Row, LogLen * Cell - 4, Cell - 12).X;
            Log0Len = LogLen;
        }
        else
        {
            Log0Col = -1;
            Log0Row = -1;
            Log0X = -1.0f;
            Log0Len = 0;
        }
    }

    private void UpdateHud()
    {
        if (_hud != null)
        {
            _hud.Text = $"SCORE {Score}  LIVES {Lives}  HOMES {HomesReached}/{TotalHomes}";
        }
        if (_status != null)
        {
            _status.Text = GameOver ? (Won ? "ALL HOMES FILLED" : "GAME OVER")
                                    : $"HOMES {HomesReached}/{TotalHomes}";
        }
    }

    public override void _Process(double delta)
    {
        var dt = (float)delta;
        Ticks++;
        if (GameOver)
        {
            return;
        }
        if (PollInput)
        {
            var dc = 0;
            var dr = 0;
            if (Input.IsActionPressed("frog_left"))
            {
                dc = -1;
            }
            else if (Input.IsActionPressed("frog_right"))
            {
                dc = 1;
            }
            else if (Input.IsActionPressed("frog_up"))
            {
                dr = -1;
            }
            else if (Input.IsActionPressed("frog_down"))
            {
                dr = 1;
            }
            if (dc != 0 || dr != 0)
            {
                _inputAccum += dt;
                if (_inputAccum >= InputRepeat)
                {
                    _inputAccum = 0.0f;
                    StepFrog(dc, dr);
                }
            }
            else
            {
                _inputAccum = 0.0f;
            }
        }
        if (CarSpeed > 0.0f && !GameOver)
        {
            _trafficAccum += dt * CarSpeed;
            var steps = 0;
            while (_trafficAccum >= 1.0f && steps < 32 && !GameOver)
            {
                _trafficAccum -= 1.0f;
                steps++;
                TrafficOnce();
            }
            LastTrafficSteps = steps;
        }
    }

    /// <summary>One traffic step, shared by the clock path and by <see cref="StepTraffic"/>.</summary>
    private void TrafficOnce()
    {
        foreach (var car in _cars)
        {
            car.Col = (car.Col + car.Dir + Cols) % Cols;
        }
        foreach (var log in _logs)
        {
            log.Col = (log.Col + log.Dir + (Cols - LogLen + 1)) % (Cols - LogLen + 1);
        }
        ApplyCars();
        ApplyLogs();
        TrafficSteps++;
        // A frog riding a log is carried with it; a frog carried off the board drowns.
        if (OnRiver(FrogRow))
        {
            foreach (var log in _logs)
            {
                if (log.Row != FrogRow || FrogCol < log.Col || FrogCol > log.Col + LogLen - 1)
                {
                    continue;
                }
                FrogCol += log.Dir;
                if (FrogCol < 0 || FrogCol >= Cols)
                {
                    FrogCol = FrogCol < 0 ? 0 : Cols - 1;
                    ApplyFrog();
                    LoseLife("washed off the log");
                    return;
                }
                ApplyFrog();
                break;
            }
        }
        CheckFrogSafety();
    }

    /// <summary>The frog's own survival rule: a car is a hit, bare water is a drowning,
    /// the goal line fills a home.</summary>
    private void CheckFrogSafety()
    {
        if (GameOver)
        {
            return;
        }
        if (FrogRow == GoalRow)
        {
            ReachHome();
            return;
        }
        if (OnRoad(FrogRow))
        {
            foreach (var car in _cars)
            {
                if (car.Row == FrogRow && car.Col == FrogCol)
                {
                    LoseLife($"hit by car at={FrogCol},{FrogRow}");
                    return;
                }
            }
            return;
        }
        if (OnRiver(FrogRow))
        {
            foreach (var log in _logs)
            {
                if (log.Row == FrogRow && FrogCol >= log.Col && FrogCol <= log.Col + LogLen - 1)
                {
                    return;
                }
            }
            LoseLife($"drowned at={FrogCol},{FrogRow}");
        }
    }

    private void ReachHome()
    {
        Score += 50;
        HomesReached++;
        LastEvent = $"home reached at={FrogCol},{FrogRow} homes={HomesReached}/{TotalHomes} score={Score}";
        if (HomesReached >= TotalHomes)
        {
            Won = true;
            GameOver = true;
            LastEvent += " course cleared";
        }
        ResetFrog();
        UpdateHud();
    }

    private void LoseLife(string reason)
    {
        Lives--;
        LastEvent = $"lives lost reason={reason} lives={Lives}";
        ResetFrog();
        if (Lives <= 0)
        {
            Lives = 0;
            GameOver = true;
            Won = false;
            LastEvent += " game over";
        }
        ApplyFrog();
        UpdateHud();
    }

    /// <summary>Puts the frog back on the start bank, leaving the traffic exactly where it is.</summary>
    private void ResetFrog()
    {
        FrogCol = StartCol;
        FrogRow = StartRow;
        ApplyFrog();
    }

    // --- hooks the session drives ----------------------------------------------

    /// <summary>
    /// Moves the frog exactly one cell if that cell is on the board, then applies the rule for the
    /// cell it landed on: a car hit or a drowning costs a life, the goal line fills a home.
    /// </summary>
    public string StepFrog(int dcol, int drow)
    {
        if (GameOver)
        {
            LastEvent = "step refused: game over";
            return LastEvent;
        }
        var nextCol = FrogCol + dcol;
        var nextRow = FrogRow + drow;
        if (nextCol < 0 || nextCol >= Cols || nextRow < 0 || nextRow >= Rows)
        {
            LastEvent = $"blocked at={nextCol},{nextRow} from={FrogCol},{FrogRow}";
            return LastEvent;
        }
        FrogCol = nextCol;
        FrogRow = nextRow;
        ApplyFrog();
        LastEvent = $"moved to={FrogCol},{FrogRow} score={Score} lives={Lives}";
        CheckFrogSafety();
        return LastEvent;
    }

    /// <summary>Advances the traffic (and every frog riding a log) by an exact number of steps.</summary>
    public string StepTraffic(int steps)
    {
        LastTrafficSteps = 0;
        for (var i = 0; i < steps && !GameOver; i++)
        {
            TrafficOnce();
            LastTrafficSteps++;
        }
        LastEvent = $"traffic steps={steps} took={LastTrafficSteps} total={TrafficSteps} "
                    + $"car0={Car0Col},{Car0Row} log0={Log0Col},{Log0Row} frog={FrogCol},{FrogRow}";
        return LastEvent;
    }

    /// <summary>Traffic steps per second; 0 keeps the cars and logs still (the default).</summary>
    public string SetCarSpeed(float perSecond)
    {
        CarSpeed = perSecond;
        _trafficAccum = 0.0f;
        LastEvent = $"car speed={CarSpeed}";
        GD.Print($"FROGGER_SPEED speed={CarSpeed}");
        return LastEvent;
    }

    /// <summary>Switches the frog's input polling on or off (the default is off).</summary>
    public string SetPollInput(bool enabled)
    {
        PollInput = enabled;
        LastEvent = $"poll_input={PollInput}";
        return LastEvent;
    }

    /// <summary>The board as a readable one-liner plus every exported fact.</summary>
    public string Dump()
    {
        var sb = new StringBuilder();
        for (var r = 0; r < Rows; r++)
        {
            for (var c = 0; c < Cols; c++)
            {
                if (c == FrogCol && r == FrogRow)
                {
                    sb.Append('F');
                    continue;
                }
                var onCar = false;
                foreach (var car in _cars)
                {
                    if (car.Row == r && car.Col == c)
                    {
                        onCar = true;
                        break;
                    }
                }
                if (onCar)
                {
                    sb.Append('C');
                    continue;
                }
                var onLog = false;
                foreach (var log in _logs)
                {
                    if (log.Row == r && c >= log.Col && c <= log.Col + LogLen - 1)
                    {
                        onLog = true;
                        break;
                    }
                }
                if (onLog)
                {
                    sb.Append('=');
                    continue;
                }
                if (r == GoalRow)
                {
                    sb.Append('G');
                }
                else if (OnRoad(r))
                {
                    sb.Append('-');
                }
                else if (OnRiver(r))
                {
                    sb.Append('~');
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
        return $"board={sb} frog={FrogCol},{FrogRow} frog_px={FrogX:F1},{FrogY:F1} score={Score} "
               + $"lives={Lives} homes={HomesReached}/{TotalHomes} over={GameOver} won={Won} "
               + $"cars={CarCount} car0={Car0Col},{Car0Row} logs={LogCount} log0={Log0Col},{Log0Row}:{Log0Len} "
               + $"traffic={TrafficSteps} last_traffic={LastTrafficSteps} ticks={Ticks} speed={CarSpeed} "
               + $"poll={PollInput} last={LastEvent}";
    }

    /// <summary>The two readback shortcuts: where the frog is and where car 0 is.</summary>
    public string Geometry()
    {
        return $"frog={FrogCol},{FrogRow} frog_px={FrogX:F0},{FrogY:F0} "
               + $"car0={Car0Col},{Car0Row} car0_px={Car0X:F0} "
               + $"log0={Log0Col},{Log0Row} log0_px={Log0X:F0} traffic={TrafficSteps}";
    }

    /// <summary>
    /// Writes the whole deterministic state in one call --
    /// <c>"frog=c,r;cars=all|none|c,r|...;logs=all|none|c,r|...;score=n;lives=n;homes=n;speed=s"</c>.
    ///
    /// <para>Keys may be omitted; the ones given are applied. The car speed and polling are
    /// switched OFF here, so a session's aim and the next readback are the same fact. A test that
    /// wants motion calls <see cref="SetCarSpeed"/> or <see cref="StepTraffic"/> itself -- which is
    /// why "a car hit the frog" can never be an accident of timing.</para>
    /// </summary>
    public string ForceTestState(string spec)
    {
        CarSpeed = 0.0f;
        PollInput = false;
        _trafficAccum = 0.0f;
        _inputAccum = 0.0f;
        Ticks = 0;
        Score = 0;
        Lives = 3;
        HomesReached = 0;
        GameOver = false;
        Won = false;
        BuildBoard();
        foreach (var part in spec.Split(';'))
        {
            var kv = part.Split(new[] { '=' }, 2);
            if (kv.Length != 2)
            {
                continue;
            }
            switch (kv[0])
            {
                case "frog":
                    {
                        var p = kv[1].Split(',');
                        FrogCol = int.Parse(p[0]);
                        FrogRow = int.Parse(p[1]);
                    }
                    break;
                case "cars":
                    if (kv[1] == "none")
                    {
                        foreach (var car in _cars)
                        {
                            DropNode(car.Node);
                        }
                        _cars.Clear();
                    }
                    else
                    {
                        var index = 0;
                        foreach (var cellPart in kv[1].Split('|'))
                        {
                            if (cellPart.Length == 0 || index >= _cars.Count)
                            {
                                continue;
                            }
                            var p = cellPart.Split(',');
                            _cars[index].Col = int.Parse(p[0]);
                            _cars[index].Row = int.Parse(p[1]);
                            index++;
                        }
                    }
                    break;
                case "logs":
                    if (kv[1] == "none")
                    {
                        foreach (var log in _logs)
                        {
                            DropNode(log.Node);
                        }
                        _logs.Clear();
                    }
                    else
                    {
                        var index = 0;
                        foreach (var cellPart in kv[1].Split('|'))
                        {
                            if (cellPart.Length == 0 || index >= _logs.Count)
                            {
                                continue;
                            }
                            var p = cellPart.Split(',');
                            _logs[index].Col = int.Parse(p[0]);
                            _logs[index].Row = int.Parse(p[1]);
                            index++;
                        }
                    }
                    break;
                case "score":
                    Score = int.Parse(kv[1]);
                    break;
                case "lives":
                    Lives = int.Parse(kv[1]);
                    break;
                case "homes":
                    HomesReached = int.Parse(kv[1]);
                    break;
                case "speed":
                    CarSpeed = float.Parse(kv[1]);
                    break;
            }
        }
        CarCount = _cars.Count;
        LogCount = _logs.Count;
        TrafficSteps = 0;
        LastTrafficSteps = 0;
        ApplyCars();
        ApplyLogs();
        ApplyFrog();
        UpdateHud();
        LastEvent = $"forced frog={FrogCol},{FrogRow} cars={CarCount} logs={LogCount} "
                    + $"score={Score} lives={Lives} homes={HomesReached}/{TotalHomes} speed={CarSpeed}";
        return LastEvent;
    }
}
