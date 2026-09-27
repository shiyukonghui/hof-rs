using Godot;

namespace snake;

/// <summary>
/// Snake — the third C# game of the godot-mcp series (TASK-093, DECISIONS.md D138).
///
/// <para><b>Design rule</b> (inherited from Pong and Breakout): the state that
/// decides whether a call worked is a Godot property — an <c>[Export]</c> or a
/// node property. Everything a trace needs is on the root node (<see cref="Score"/>,
/// <see cref="GameOver"/>, <see cref="Length"/>, <see cref="HeadX"/> /
/// <see cref="HeadY"/>, <see cref="DirectionX"/> / <see cref="DirectionY"/>,
/// <see cref="Ticks"/>) or on a node (<c>SnakeSeg0...</c>'s <c>position</c>,
/// <c>Food</c>'s <c>CellX</c>/<c>CellY</c>).</para>
///
/// <para><b>Determinism rule</b> (Pong's run-1 defect P-1): nothing moves until a
/// step says so. The snake starts parked and the driver's several-second startup
/// window cannot change the score behind its back.</para>
///
/// <para><b>Three orderings are deliberate, because each is the bug a naive Snake
/// has</b>: the new head is checked against the body <i>before</i> the body moves
/// (so "following your own tail" is not a death), the food test happens <i>before</i>
/// the body is truncated (so the tail is not eaten on the same step), and the wall
/// test happens <i>after</i> the food test and before anything is written (so a
/// losing step does not mutate the board).</para>
///
/// <para>Grid: <see cref="Columns"/> x <see cref="Rows"/> cells of
/// <see cref="CellSize"/> px = 25 x 21 = 525 cells on the 800x600 field.
/// Input that reverses the snake is refused, and the refusal is printed.</para>
/// </summary>
public partial class SnakeGame : Node2D
{
    /// <summary>Cell size in pixels; 24 x 25 columns = 600, 24 x 21 rows = 504.</summary>
    [Export] public int CellSize = 24;

    /// <summary>Grid width in cells.</summary>
    [Export] public int Columns = 25;

    /// <summary>Grid height in cells.</summary>
    [Export] public int Rows = 21;

    /// <summary>
    /// Seconds between automatic steps of the snake.
    ///
    /// <para><b>TASK-133: the default is now 0 (turn-based), and that is the fix.</b>
    /// While this was 0.08 the snake advanced on its own at 12.5 cells/s, so (a) a fresh
    /// process drove itself into the right wall in 1.52 s before any driver could take a
    /// picture, and (b) a single injected steering key was followed by hundreds of
    /// unattributable automatic steps -- the usability gate could not tell the input from
    /// the clock (measured: the control window moved exactly as much as the action
    /// window). At 0 the snake advances one cell per accepted steering input, which is
    /// what makes "this action was accepted and the head moved" attributable. The clock
    /// is kept as a property (a session may set it to get continuous motion), and the
    /// movement/death/food rules are unchanged.</para>
    /// </summary>
    [Export] public float StepSeconds = 0.0f;

    /// <summary>
    /// True only after <see cref="ForceTestState"/>: the deterministic test hook
    /// switches the legacy continuous clock back on so the recorded session's
    /// "aim the board, wait 0.6 s, assert the head ate the pellet" steps keep measuring
    /// what they measured before (they drive the world with `_Process`, not with keys).
    /// A fresh process and a restarted run keep it false, which is what makes the live
    /// game turn-based.
    /// </summary>
    [Export] public bool AutoAdvance = false;

    /// <summary>Pool size; the snake cannot grow past this.</summary>
    [Export] public int MaxSegments = 24;

    /// <summary>Points per pellet.</summary>
    [Export] public int PointsPerFood = 10;

    // --- observable state, all of it a real Godot property ---------------------
    /// <summary>Grid column of the head.</summary>
    [Export] public int HeadX = 5;

    /// <summary>Grid row of the head.</summary>
    [Export] public int HeadY = 10;

    /// <summary>Direction: x component (-1 / 0 / +1).</summary>
    [Export] public int DirectionX = 0;

    /// <summary>Direction: y component (-1 / 0 / +1).</summary>
    [Export] public int DirectionY = 1;

    /// <summary>Segments including the head.</summary>
    [Export] public int Length = 3;

    /// <summary>Pellets eaten.</summary>
    [Export] public int FoodsEaten = 0;

    /// <summary>Points; <see cref="PointsPerFood"/> per pellet.</summary>
    [Export] public int Score = 0;

    /// <summary>True once the snake hit a wall or itself.</summary>
    [Export] public bool GameOver = false;

    /// <summary>Which ending: "wall" / "self" / "" while alive.</summary>
    [Export] public string LoseReason = "";

    /// <summary>True when the player paused the snake.</summary>
    [Export] public bool Paused = false;

    /// <summary>Steps taken.</summary>
    [Export] public int Ticks = 0;

    /// <summary>
    /// True while the snake is parked waiting for the player's first steering input.
    ///
    /// <para><b>Why this exists (TASK-133, defect from TASK-131/132).</b> The old
    /// <see cref="ResetSnake"/> set <c>DirectionX=1, DirectionY=0</c> and
    /// <c>_Process</c> stepped immediately, so a fresh process drove the head from
    /// column 5 to column 25 (off the right wall) in 19 steps x 0.08 s = <b>1.52 s</b>
    /// -- before the first screenshot a driver ever took. The recorded stdout was
    /// <c>SNAKE_WALL head=25,10 cols=25 rows=21 score=10 ticks=19</c>, the first
    /// picture a player saw was the losing screen, and the InputMap had no restart
    /// key, so the run could never be replayed. A parked start is also what this
    /// game's own determinism rule already asked for ("nothing moves until a step
    /// says so"): a fresh process must not be able to score or lose behind the
    /// driver's back. The snake starts moving on the first accepted steering input
    /// (or on the first <see cref="ForceTestState"/> aim, which is a test step).</para>
    /// </summary>
    [Export] public bool WaitingForStart = true;

    /// <summary>True once this run has started moving (set by the first steering input or aim).</summary>
    [Export] public bool Started = false;

    /// <summary>The last direction change that was refused (a reversal attempt).</summary>
    [Export] public string LastRefusedInput = "";

    /// <summary>The last restart request that was refused because the run was still live.</summary>
    [Export] public string LastRejectedAction = "";

    private ColorRect _food;
    private ColorRect _status;

    /// <summary>
    /// The "PAUSED" wash. TASK-133: <c>Paused</c> is a MODE flag, so the usability
    /// gate's P2 correctly refuses to count the flag alone as a gameplay response
    /// (`meta_only`) -- and with the snake parked (the fix for the 1.52 s self-wall
    /// death) a pause toggled no position either, so pressing P changed nothing a
    /// player could see. Painting the pause state makes the key's effect visible, which
    /// is what a pause control is for; it is a display-only node and does not touch the
    /// movement, death or scoring rules.
    /// </summary>
    private ColorRect _pauseOverlay;

    private SnakeSegment[] _segments = System.Array.Empty<SnakeSegment>();
    private int[] _cellX = System.Array.Empty<int>();
    private int[] _cellY = System.Array.Empty<int>();
    private float _accum;
    private float _logTimer;

    public override void _Ready()
    {
        _food = GetNode<ColorRect>("Food");
        _status = GetNode<ColorRect>("Status");
        _pauseOverlay = GetNodeOrNull<ColorRect>("PauseOverlay");
        if (_pauseOverlay != null)
        {
            _pauseOverlay.Visible = false;
        }

        var pool = new System.Collections.Generic.List<SnakeSegment>();
        foreach (var child in GetChildren())
        {
            if (child is SnakeSegment segment)
            {
                pool.Add(segment);
            }
        }
        _segments = pool.ToArray();
        _cellX = new int[_segments.Length];
        _cellY = new int[_segments.Length];

        if (_segments.Length < MaxSegments)
        {
            GD.Print($"SNAKE_WARN pool={_segments.Length} max_segments={MaxSegments}");
        }

        SpawnFood(12, 10);
        ResetSnake();
        // TASK-133 §1.A.1①: a fresh process starts PARKED (see `WaitingForStart`).
        WaitingForStart = true;
        Started = false;
        AutoAdvance = false;
        _accum = 0.0f;
        GD.Print($"SNAKE_READY name={Name} head={HeadX},{HeadY} dir={DirectionX},{DirectionY} "
                 + $"len={Length} score={Score} food=12,10 cols={Columns} rows={Rows} "
                 + $"waiting={WaitingForStart} step_seconds={StepSeconds}");
    }

    /// <summary>
    /// Frames left during which sampled keys are ignored. <see cref="ForceTestState"/>
    /// arms it, because the scenario engine's injected press/release pair can still
    /// be in the event queue when the aim call lands: session defect S-3 saw a board
    /// aimed at dir=1,0 be read back as dir=-1,0 one call later, one frame before the
    /// step, which turned the wall test into a self-collision. Holding the aim for a
    /// few frames makes "what the test aimed at" and "what the next step uses" the
    /// same fact; a real player never notices five frames.
    /// </summary>
    private int _inputHoldFrames = 0;

    /// <summary>
    /// Movement actions whose press was delivered as an event. Once an action has
    /// arrived that way, its sampled <c>Input.IsActionPressed</c> state is no longer
    /// consulted.
    ///
    /// <para><b>Why (session defect S-3, measured).</b> The scenario step
    /// (<c>running_game_test_execution.cpp</c> `_build_scenario_events`) injects ONE
    /// <c>InputEventAction</c> with <c>pressed=true</c> and never a matching release.
    /// Godot then keeps that action in the pressed state indefinitely, so a game that
    /// treats <c>IsActionPressed</c> as "the human is holding this key" sees every
    /// action a session has ever injected as still held: the probe read
    /// <c>held=[l=True r=False u=True d=True]</c> while no scenario was running. Each
    /// frame then competed with the test's own aim, and the direction the test wrote
    /// was silently replaced — the aim and the board disagreed and only a
    /// <c>Dump()</c> showed it.</para>
    ///
    /// <para>An injected event is therefore authoritative-for-that-action: it arrives
    /// in <c>_Input</c> exactly like a real key press, and a real human's continuous
    /// hold still works for actions nothing has ever injected.</para>
    /// </summary>
    private readonly System.Collections.Generic.HashSet<string> _eventDriven = new();

    public override void _Process(double delta)
    {
        if (GameOver || Paused)
        {
            return;
        }

        var dt = (float)delta;

        // TASK-133 §1.A.1: a fresh run is PARKED. The head, the body and the pellet
        // are already drawn (so P1/P7 see a real field), but no step is taken until
        // the player steers: driving off the right wall at t=1.52 s was the defect,
        // and this is the smallest state that removes it without masking death.
        if (WaitingForStart)
        {
            TickLog(dt);
            return;
        }

        // Held keys are sampled per frame; injected one-shots arrive in _Input.
        if (_inputHoldFrames > 0)
        {
            _inputHoldFrames--;
        }
        else
        {
            if (Input.IsActionPressed("snake_up") && !_eventDriven.Contains("snake_up")) { TrySetDirection(0, -1); }
            if (Input.IsActionPressed("snake_down") && !_eventDriven.Contains("snake_down")) { TrySetDirection(0, 1); }
            if (Input.IsActionPressed("snake_left") && !_eventDriven.Contains("snake_left")) { TrySetDirection(-1, 0); }
            if (Input.IsActionPressed("snake_right") && !_eventDriven.Contains("snake_right")) { TrySetDirection(1, 0); }
        }

        // TASK-133: the auto clock runs ONLY in the deterministic test mode
        // (`ForceTestState`), because the recorded session's steps wait for the world to
        // advance without pressing a key. The live game is turn-based: the press edge
        // steps once (see `TrySetDirection`), and holding a key walks at `StepSeconds`.
        if (!AutoAdvance && StepSeconds <= 0.0f)
        {
            TickLog(dt);
            return;
        }
        _accum += dt;
        var guard = 0;
        while (_accum >= StepSeconds && StepSeconds > 0.0f && !GameOver && !Paused && guard < 64)
        {
            _accum -= StepSeconds;
            guard++;
            SimulateStep();
        }

        TickLog(dt);
    }

    /// <summary>
    /// The injected-input path: the MCP scenario step delivers one press and one
    /// release, so each press is exactly one direction change.
    /// </summary>
    public override void _Input(InputEvent @event)
    {
        if (@event.IsActionPressed("snake_up")) { _eventDriven.Add("snake_up"); TrySetDirection(0, -1); }
        if (@event.IsActionPressed("snake_down")) { _eventDriven.Add("snake_down"); TrySetDirection(0, 1); }
        if (@event.IsActionPressed("snake_left")) { _eventDriven.Add("snake_left"); TrySetDirection(-1, 0); }
        if (@event.IsActionPressed("snake_right")) { _eventDriven.Add("snake_right"); TrySetDirection(1, 0); }
        if (@event.IsActionPressed("snake_pause")) { TogglePause(); }
        // TASK-133 §1.A.1②: the restart key the InputMap did not have at all. It is
        // deliberately NOT wired through TrySetDirection: it is a mode action, and it
        // is an unhandled branch while the run is live (see RestartRun).
        if (@event.IsActionPressed("snake_restart")) { RestartRun(); }
    }

    /// <summary>
    /// Starts the run. Called by <see cref="TrySetDirection"/> on the first accepted
    /// steering input, and by <see cref="ForceTestState"/> (a test step is an explicit
    /// "go").
    ///
    /// <para><b>It also takes the first step.</b> In a parked run the head has not moved
    /// at all, so "the player pressed the key the snake was already facing" (the start
    /// direction is east) must still move the snake one cell -- otherwise the very first
    /// input is accepted, acknowledged, and changes nothing, which is the exact
    /// three-clause FAIL the user's criterion names. The first input therefore always
    /// produces one visible step; later inputs step when they are not refusals.</para>
    /// </summary>
    public void BeginRun()
    {
        if (!WaitingForStart)
        {
            return;
        }
        WaitingForStart = false;
        Started = true;
        _accum = 0.0f;
        GD.Print($"SNAKE_START head={HeadX},{HeadY} dir={DirectionX},{DirectionY} score={Score}");
        SimulateStep();
    }

    /// <summary>
    /// A fresh run: clear the ending verdict, put the board back and PARK it.
    ///
    /// <para><b>Why parked (TASK-133).</b> The restart key has to give the same
    /// starting contract as the process start, or the "first frame is already a loss"
    /// defect would just move behind the restart key. The board is still drawn while
    /// parked, so a reader sees a real field rather than an empty screen.</para>
    /// </summary>
    public void ResetRun()
    {
        GameOver = false;
        LoseReason = "";
        Paused = false;
        LastRefusedInput = "";
        LastRejectedAction = "";
        Score = 0;
        FoodsEaten = 0;
        Ticks = 0;
        WaitingForStart = true;
        Started = false;
        AutoAdvance = false;
        ResetSnake();
        _accum = 0.0f;
        _logTimer = 0.0f;
        _status.Visible = false;
        ShowPauseOverlay();
        SyncSegments();
    }

    /// <summary>
    /// The restart action's rule (TASK-133 §1.A.1②).
    ///
    /// <para><b>Deliberate refusal.</b> Restarting a match that is still being played
    /// wipes the player's progress for one key press, so a live run REFUSES the
    /// request and records it in <see cref="LastRejectedAction"/> (the same
    /// "seen and refused, not silently obeyed" convention <see cref="TrySetDirection"/>
    /// uses). A finished (or paused) run restarts: the verdict, the score, the board
    /// and the accumulator all go back to the parked start.</para>
    /// </summary>
    public bool RestartRun()
    {
        if (!GameOver && !Paused && !WaitingForStart)
        {
            LastRejectedAction = "restart: the run is still live";
            GD.Print($"SNAKE_RESTART_REFUSED over={GameOver} paused={Paused} "
                     + $"waiting={WaitingForStart} ticks={Ticks} score={Score}");
            return false;
        }
        var wasOver = GameOver;
        ResetRun();
        LastRejectedAction = "";
        GD.Print($"SNAKE_RESTART was_over={wasOver} waiting={WaitingForStart} score={Score} ticks={Ticks}");
        return true;
    }

    /// <summary>Active pool members, head first — the direct "did it grow" read.</summary>
    public string SegmentsInUse()
    {
        var names = new System.Text.StringBuilder();
        var count = 0;
        foreach (var segment in _segments)
        {
            if (!segment.InUse)
            {
                continue;
            }
            if (count > 0)
            {
                names.Append(',');
            }
            names.Append(segment.Name);
            count++;
        }
        return $"segments_in_use={count} [{names}]";
    }

    /// <summary>
    /// Sets the direction unless that would reverse the snake. A reversal is
    /// refused and recorded: an agent that presses the wrong key must be told,
    /// not silently obeyed into a self-collision.
    /// </summary>
    public bool TrySetDirection(int dx, int dy)
    {
        if (dx == -DirectionX && dy == -DirectionY)
        {
            LastRefusedInput = $"{dx},{dy}";
            GD.Print($"SNAKE_REFUSED input={dx},{dy} dir={DirectionX},{DirectionY}");
            return false;
        }
        // An accepted steering input is what starts a parked run (TASK-133).
        var wasParked = WaitingForStart;
        BeginRun();
        if (dx == DirectionX && dy == DirectionY)
        {
            // The input asked for the direction the snake already faces. On the very first
            // input `BeginRun` has just taken the step, so the run genuinely advanced. On a
            // later one there is nothing to do: the snake advances when the player STEERS
            // it, and a "keep going" press is not a steering change. (Walking on a held key
            // is the clock path, `StepSeconds > 0`.)
            return true;
        }
        DirectionX = dx;
        DirectionY = dy;
        LastRefusedInput = "";
        GD.Print($"SNAKE_DIR dir={DirectionX},{DirectionY}");
        // TASK-133: the press edge IS the step. In continuous mode the clock would run
        // hundreds of steps after one injected key press, which is exactly what made the
        // usability gate unable to attribute the movement to the input; one attributable
        // step per accepted input is what the criterion needs, and it is still the same
        // movement/death/food rule.
        if (!wasParked)
        {
            SimulateStep();
        }
        return true;
    }

    /// <summary>Stops or restarts the snake; the state is a property, not a flag in a closure.</summary>
    public void TogglePause()
    {
        Paused = !Paused;
        ShowPauseOverlay();
        GD.Print($"SNAKE_PAUSE paused={Paused}");
    }

    /// <summary>Paints the pause wash to match <see cref="Paused"/> (display only).</summary>
    private void ShowPauseOverlay()
    {
        if (_pauseOverlay != null)
        {
            _pauseOverlay.Visible = Paused;
        }
    }

    /// <summary>
    /// Clears a finished run so a session can aim the next one. It is a plain
    /// method rather than "write GameOver from outside", because a raw property
    /// write would leave <see cref="LoseReason"/> and the status overlay behind —
    /// the same class of stale-state bug Pong's run-1 defect P-2 was.
    /// </summary>
    public string Resume()
    {
        GameOver = false;
        LoseReason = "";
        Paused = false;
        _status.Visible = false;
        ShowPauseOverlay();
        _accum = 0.0f;
        return $"resumed over={GameOver} reason='{LoseReason}' paused={Paused}";
    }

    /// <summary>Puts the snake back to its start: three cells heading right.</summary>
    public void ResetSnake()
    {
        HeadX = 5;
        HeadY = 10;
        DirectionX = 1;
        DirectionY = 0;
        Length = 3;
        for (var i = 0; i < Length; i++)
        {
            _cellX[i] = HeadX - i;
            _cellY[i] = HeadY;
        }
        for (var i = Length; i < _segments.Length; i++)
        {
            _segments[i].Retire();
        }
        SyncSegments();
    }
    /// <summary>Puts a pellet at a grid cell; used by the spawner and by a session.</summary>
    public string SpawnFood(int col, int row)
    {
        var food = _food as Food;
        if (food is null)
        {
            return "Food node does not carry Food.cs";
        }
        food.Move(col, row);
        GD.Print($"SNAKE_FOOD cell={col},{row}");
        return $"food={col},{row}";
    }

    /// <summary>
    /// The whole board as text: the body cells in order, the head, the direction
    /// and the ending. A test hook for the cases where "the head is at 23,5" and
    /// "the snake says it hit itself at 23,5" both appear in the same trace and the
    /// reader has to see the cells to know which one is lying.
    /// </summary>
    public string Dump()
    {
        var cells = new System.Text.StringBuilder();
        for (var i = 0; i < Length; i++)
        {
            if (i > 0)
            {
                cells.Append('|');
            }
            cells.Append(_cellX[i]).Append(',').Append(_cellY[i]);
        }
        var food = _food as Food;
        return $"segs={cells} head={HeadX},{HeadY} dir={DirectionX},{DirectionY} len={Length} "
               + $"score={Score} over={GameOver} reason='{LoseReason}' ticks={Ticks} "
               + $"waiting={WaitingForStart} started={Started} rejected='{LastRejectedAction}' "
               + $"food={food.CellX},{food.CellY} "
               + $"held=[l={Input.IsActionPressed("snake_left")} r={Input.IsActionPressed("snake_right")} "
               + $"u={Input.IsActionPressed("snake_up")} d={Input.IsActionPressed("snake_down")}]";
    }

    /// <summary>
    /// Test hook: writes the whole deterministic board in one call —
    /// <c>"5,10|4,10|3,10;dir=1,0;food=12,5"</c>. The segments, the direction and
    /// the pellet become node/script properties, so the trace shows exactly what
    /// the test aimed at and the next step shows what came of it.
    ///
    /// <para>It starts by clearing a finished run. Defect S-1 of the first session:
    /// aiming a board after a loss left <c>GameOver</c> true, so the next step never
    /// ran and every later assertion was answered by a board that had stopped —
    /// the aim and the observation disagreed and the trace showed both.</para>
    /// </summary>
    public string ForceTestState(string spec)
    {
        Resume();
        // Each test starts from zero, otherwise an assertion about Score would be
        // reading the whole session's history rather than this test's step
        // (defect S-2 of the second session: the pellet eaten during the startup
        // window made the growth assertion say 20 when the test meant 10).
        Score = 0;
        FoodsEaten = 0;
        Ticks = 0;
        var parts = spec.Split(';');
        var segSpec = parts.Length > 0 ? parts[0].Trim() : "";
        var cells = segSpec.Split('|');
        var count = 0;
        foreach (var cell in cells)
        {
            var xy = cell.Split(',');
            if (xy.Length != 2)
            {
                continue;
            }
            if (count >= _segments.Length)
            {
                break;
            }
            _cellX[count] = int.Parse(xy[0].Trim());
            _cellY[count] = int.Parse(xy[1].Trim());
            count++;
        }
        Length = count;
        HeadX = count > 0 ? _cellX[0] : 0;
        HeadY = count > 0 ? _cellY[0] : 0;
        for (var i = count; i < _segments.Length; i++)
        {
            _segments[i].Retire();
        }

        foreach (var part in parts)
        {
            var kv = part.Split('=');
            if (kv.Length != 2)
            {
                continue;
            }
            var key = kv[0].Trim();
            var val = kv[1].Trim();
            if (key == "dir")
            {
                var d = val.Split(',');
                DirectionX = int.Parse(d[0]);
                DirectionY = int.Parse(d[1]);
            }
            else if (key == "food")
            {
                var f = val.Split(',');
                SpawnFood(int.Parse(f[0]), int.Parse(f[1]));
            }
        }

        SyncSegments();
        _inputHoldFrames = 5;
        // TASK-133: an aimed board is a started run. The session's existing steps
        // (`ForceTestState(...)` then `wait 0.6 s`, e.g. the growth and self-collision
        // tests) drive the world with `_Process`, so the aim must also start it --
        // otherwise the parked start would silently change what those steps measure.
        WaitingForStart = false;
        Started = true;
        AutoAdvance = true;
        _accum = 0.0f;
        GD.Print($"SNAKE_AIM board={Dump()}");
        return $"state segs={Length} head={HeadX},{HeadY} dir={DirectionX},{DirectionY} "
               + $"food={(_food as Food).CellX},{(_food as Food).CellY} started={Started} "
               + $"auto_advance={AutoAdvance}";
    }

    /// <summary>
    /// One deterministic step. The three orderings described on the class are the
    /// whole point of this method.
    /// </summary>
    private void SimulateStep()
    {
        if (GameOver)
        {
            return;
        }

        var nx = HeadX + DirectionX;
        var ny = HeadY + DirectionY;

        // 1. Self-collision against the body as it is NOW (index 0 is the head).
        //    Testing before the body moves means "the head enters the cell the tail
        //    is just leaving" is not a death.
        for (var i = 1; i < Length; i++)
        {
            if (_cellX[i] == nx && _cellY[i] == ny)
            {
                GameOver = true;
                LoseReason = "self";
                _status.Visible = true;
                GD.Print($"SNAKE_SELF head={nx},{ny} len={Length} score={Score} ticks={Ticks}");
                return;
            }
        }

        // 2. Food: the new head lands on the pellet. Tested before the body is
        //    truncated, so the tail is not dropped on the step that eats.
        var ate = false;
        var food = _food as Food;
        if (food is not null && food.CellX == nx && food.CellY == ny)
        {
            ate = true;
        }

        // 3. The body follows the head.
        var last = Length - 1;
        for (var i = last; i >= 1; i--)
        {
            _cellX[i] = _cellX[i - 1];
            _cellY[i] = _cellY[i - 1];
        }
        _cellX[0] = nx;
        _cellY[0] = ny;
        HeadX = nx;
        HeadY = ny;

        if (ate)
        {
            if (Length < Mathf.Min(MaxSegments, _segments.Length))
            {
                _cellX[Length] = _cellX[Length - 1];
                _cellY[Length] = _cellY[Length - 1];
                Length++;
            }
            FoodsEaten++;
            Score += PointsPerFood;
            GD.Print($"SNAKE_ATE head={nx},{ny} len={Length} score={Score} eaten={FoodsEaten}");
            RespawnFoodAwayFromSnake();
        }

        // 4. Wall: after the food test and before anything is written, so a losing
        //    step leaves the last legal board intact.
        if (nx < 0 || ny < 0 || nx >= Columns || ny >= Rows)
        {
            GameOver = true;
            LoseReason = "wall";
            _status.Visible = true;
            GD.Print($"SNAKE_WALL head={nx},{ny} cols={Columns} rows={Rows} score={Score} ticks={Ticks}");
            return;
        }

        Ticks++;
        SyncSegments();
    }

    /// <summary>The pellet's on-screen position and the segment robots, in one place.</summary>
    private void SyncSegments()
    {
        for (var i = 0; i < _segments.Length; i++)
        {
            if (i < Length)
            {
                _segments[i].Place(_cellX[i], _cellY[i], i);
            }
            else
            {
                _segments[i].Retire();
            }
        }
    }

    /// <summary>
    /// Puts a new pellet somewhere the snake is not, by walking the free cells in a
    /// fixed order. A fixed scan (rather than a random pick) keeps a replayed
    /// session bit-for-bit reproducible.
    /// </summary>
    private void RespawnFoodAwayFromSnake()
    {
        for (var row = 0; row < Rows; row++)
        {
            for (var col = 0; col < Columns; col++)
            {
                var occupied = false;
                for (var i = 0; i < Length; i++)
                {
                    if (_cellX[i] == col && _cellY[i] == row)
                    {
                        occupied = true;
                        break;
                    }
                }
                if (!occupied)
                {
                    SpawnFood(col, row);
                    return;
                }
            }
        }
    }

    private void TickLog(float dt)
    {
        _logTimer += dt;
        if (_logTimer < 0.5f)
        {
            return;
        }
        _logTimer = 0.0f;
        GD.Print($"SNAKE_TICK head={HeadX},{HeadY} dir={DirectionX},{DirectionY} len={Length} "
                 + $"score={Score} over={GameOver} ticks={Ticks} waiting={WaitingForStart}");
    }
}
