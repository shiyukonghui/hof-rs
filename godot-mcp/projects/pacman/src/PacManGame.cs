using Godot;
using System.Collections.Generic;
using System.Text;

namespace pacman;

/// <summary>
/// Pac-Man -- the seventh C# game of the godot-mcp series (TASK-098, DECISIONS.md D138).
///
/// <para><b>Design rule</b> (inherited from Pong / Breakout / Snake / Tetris / Space Invaders /
/// Asteroids): every fact the evidence model needs is a real Godot property on the root node --
/// <see cref="Score"/>, <see cref="PelletsRemaining"/>, <see cref="PelletsEaten"/>,
/// <see cref="TotalPellets"/>, <see cref="PacCol"/>, <see cref="PacRow"/>, <see cref="PacX"/>,
/// <see cref="PacY"/>, <see cref="Lives"/>, <see cref="GhostCount"/>, <see cref="GhostSteps"/>,
/// <see cref="Ghost0Col"/>, <see cref="Ghost0Row"/>, <see cref="Ghost0X"/>, <see cref="Ghost0Y"/>,
/// <see cref="GameOver"/>, <see cref="Won"/>, <see cref="Ticks"/>. A session asserts these with
/// <c>running_game_assert_node_state</c>; it never parses a log line.</para>
///
/// <para><b>Determinism rule.</b> Three things are OFF by default and each is switched on only by
/// an explicit test call: the ghosts do not patrol on their own (<see cref="GhostSpeed"/> = 0),
/// Pac-Man does not poll input (<see cref="PollInput"/> = false), and every move is reachable
/// through a fixed-step hook (<see cref="StepPac"/>, <see cref="StepGhosts"/>) so a fact like
/// "Pac-Man ate a pellet" can never be an accident of frame timing.
/// <see cref="ForceTestState"/> pins the whole board in one call.</para>
///
/// <para><b>The maze, the pellets, the ghosts and Pac-Man are all runtime-created.</b>
/// <see cref="_Ready"/> walks <see cref="Maze"/> and builds one <c>ColorRect</c> per wall, plus
/// one per pellet, plus the four ghosts and Pac-Man; the scene file carries only the three static
/// nodes (Background, Hud, Status). That keeps the edited scene small, keeps it immune to the D-3
/// duplicate-name trap, and makes "a node created at run time really is drawn" part of this
/// game's own evidence.</para>
///
/// <para><b>Scoring has exactly one source.</b> One pellet eaten = 10 points; nothing else scores.
/// An assertion about <see cref="Score"/> therefore names the pellet that produced it.</para>
/// </summary>
public partial class PacManGame : Node2D
{
    // --- the maze --------------------------------------------------------------
    /// <summary>
    /// The maze, one string per row. <c>#</c> = wall, <c>.</c> = pellet, space = empty.
    /// Nineteen columns by thirteen rows, and the empty cell at (9,9) is where Pac-Man starts,
    /// so the starting cell can never be confused with the first pellet he eats.
    /// </summary>
    [Export] public string[] Maze =
    {
        "###################",
        "#........#........#",
        "#.##.###.#.###.##.#",
        "#.................#",
        "#.##.#.#####.#.##.#",
        "#....#...#...#....#",
        "##.#.#.#.#.#.#.#.##",
        "#....#...#...#....#",
        "#.##.#.#####.#.##.#",
        "#........ ........#",
        "#.##.###.#.###.##.#",
        "#........#........#",
        "###################",
    };

    /// <summary>Size of one maze cell in pixels.</summary>
    [Export] public int Cell = 40;

    /// <summary>Left edge of the maze in pixels.</summary>
    [Export] public int OriginX = 20;

    /// <summary>Top edge of the maze in pixels.</summary>
    [Export] public int OriginY = 60;

    /// <summary>Pac-Man's square size in pixels.</summary>
    [Export] public float PacSize = 26.0f;

    /// <summary>Ghost square size in pixels.</summary>
    [Export] public float GhostSize = 26.0f;

    /// <summary>Pellet square size in pixels.</summary>
    [Export] public float PelletSize = 10.0f;

    /// <summary>Columns in the maze (derived from <see cref="Maze"/> on every rebuild).</summary>
    [Export] public int Cols = 19;

    /// <summary>Rows in the maze (derived from <see cref="Maze"/> on every rebuild).</summary>
    [Export] public int Rows = 13;

    // --- observable state, all of it a real Godot property ---------------------
    /// <summary>Points: 10 per pellet.</summary>
    [Export] public int Score = 0;

    /// <summary>Pellets still on the board (recomputed from the board, never decremented by hand).</summary>
    [Export] public int PelletsRemaining = 0;

    /// <summary>Pellets eaten so far.</summary>
    [Export] public int PelletsEaten = 0;

    /// <summary>Pellets the maze starts with, counted from <see cref="Maze"/> at build time.</summary>
    [Export] public int TotalPellets = 0;

    /// <summary>Pac-Man's column, or -1 before the board is built.</summary>
    [Export] public int PacCol = 9;

    /// <summary>Pac-Man's row.</summary>
    [Export] public int PacRow = 9;

    /// <summary>Pac-Man's centre x in pixels.</summary>
    [Export] public float PacX = 0.0f;

    /// <summary>Pac-Man's centre y in pixels.</summary>
    [Export] public float PacY = 0.0f;

    /// <summary>Lives left. A ghost meeting Pac-Man costs exactly one.</summary>
    [Export] public int Lives = 3;

    /// <summary>How many ghosts are on the board.</summary>
    [Export] public int GhostCount = 4;

    /// <summary>Ghost patrol steps taken (by the hook or by the clock).</summary>
    [Export] public int GhostSteps = 0;

    /// <summary>Steps the LAST <see cref="StepGhosts"/> call took. A patch of the total alone
    /// cannot be asserted exactly: the clock may have advanced the patrol before the hook ran.</summary>
    [Export] public int LastPatrolSteps = 0;

    /// <summary>Column of ghost 0 -- a real property, so a multi-frame sample can show patrol.</summary>
    [Export] public int Ghost0Col = -1;

    /// <summary>Row of ghost 0.</summary>
    [Export] public int Ghost0Row = -1;

    /// <summary>Centre x of ghost 0 in pixels.</summary>
    [Export] public float Ghost0X = 0.0f;

    /// <summary>Centre y of ghost 0 in pixels.</summary>
    [Export] public float Ghost0Y = 0.0f;

    /// <summary>True when every pellet is eaten (win) or the last life is gone (loss).</summary>
    [Export] public bool GameOver = false;

    /// <summary>True when <see cref="GameOver"/> was reached by eating every pellet.</summary>
    [Export] public bool Won = false;

    /// <summary>Ghost patrol steps per second; 0 keeps them still (the default).</summary>
    [Export] public float GhostSpeed = 0.0f;

    /// <summary>When true the game reads its player's keyboard. The test driver switches this
    /// OFF explicitly (<see cref="SetPollInput"/>, <see cref="ForceTestState"/>) when it needs
    /// a frozen, deterministic state; the deterministic defaults live in AutoClock / AutoPlay /
    /// DriftSpeed, not here (TASK-116 defect D1).</summary>
    [Export] public bool PollInput = true;

    /// <summary>Seconds between two input-driven cell moves. A held key moves Pac-Man one cell
    /// per interval instead of one cell per frame, so an input test's expectation is a range
    /// rather than a race.</summary>
    [Export] public float InputRepeat = 0.12f;

    /// <summary>Steps the game refused (a wall, or after the game was over). TASK-116 D11: a
    /// refusal is a real answer to the player's key and must be an observable property.</summary>
    [Export] public int RejectedSteps = 0;

    /// <summary>Frames processed since the last reset.</summary>
    [Export] public int Ticks = 0;

    /// <summary>What the last hook did -- the readback string a session quotes.</summary>
    [Export] public string LastEvent = "";

    // --- private model ---------------------------------------------------------
    private class Ghost
    {
        public int Col;
        public int Row;
        public int DirCol;
        public int DirRow;
        public ColorRect Node;
    }

    private readonly List<Ghost> _ghosts = new List<Ghost>();
    private readonly Dictionary<int, ColorRect> _pellets = new Dictionary<int, ColorRect>();
    private ColorRect _pac;
    private ColorRect _bg;
    private Label _hud;
    private Label _status;
    private float _patrolAccum;
    private float _inputAccum;
    private int _ghostSeq;

    /// <summary>Where the four ghosts start. All four cells are open in <see cref="Maze"/>.</summary>
    private static readonly int[,] GhostStart =
    {
        { 1, 2 }, { 1, 10 }, { 17, 2 }, { 17, 10 },
    };

    private int Key(int col, int row)
    {
        return row * 64 + col;
    }

    private char CellAt(int col, int row)
    {
        if (row < 0 || row >= Maze.Length)
        {
            return '#';
        }
        var line = Maze[row];
        if (col < 0 || col >= line.Length)
        {
            return '#';
        }
        return line[col];
    }

    private bool IsWall(int col, int row)
    {
        return CellAt(col, row) == '#';
    }

    public override void _Ready()
    {
        _bg = GetNodeOrNull<ColorRect>("Background");
        _hud = GetNodeOrNull<Label>("Hud");
        _status = GetNodeOrNull<Label>("Status");
        if (GetNodeOrNull<ColorRect>("Pac") == null)
        {
            _pac = MakeRect("Pac", new Vector2(PacSize, PacSize), new Color(1.0f, 0.92f, 0.25f));
        }
        BuildBoard();
        UpdateHud();
        GD.Print($"PAC_READY pellets={TotalPellets} ghosts={GhostCount} pac={PacCol},{PacRow} "
                 + $"speed={GhostSpeed} poll={PollInput}");
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
    /// like <c>Wall_r2_c3</c> in the same frame would find that name still taken and Godot would
    /// quietly rename the new node to <c>@ColorRect@NNN</c>. <c>RemoveChild()</c> first releases
    /// the name immediately, so every name this game creates is exactly the name it asked for.</para>
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

    /// <summary>Builds the whole board from <see cref="Maze"/>: walls, pellets, ghosts, Pac-Man.</summary>
    private void BuildBoard()
    {
        Cols = 0;
        for (var r = 0; r < Maze.Length; r++)
        {
            if (Maze[r].Length > Cols)
            {
                Cols = Maze[r].Length;
            }
        }
        Rows = Maze.Length;
        foreach (var child in GetChildren())
        {
            var node = child as Node;
            if (node == null)
            {
                continue;
            }
            var name = node.Name.ToString();
            if (name == "Hud" || name == "Status" || name == "Background" || name == "Pac")
            {
                continue;
            }
            DropNode(node);
        }
        _pellets.Clear();
        _ghosts.Clear();
        _ghostSeq = 0;
        TotalPellets = 0;
        for (var r = 0; r < Rows; r++)
        {
            for (var c = 0; c < Cols; c++)
            {
                var ch = CellAt(c, r);
                if (ch == '#')
                {
                    var wall = MakeRect($"Wall_r{r}_c{c}", new Vector2(Cell, Cell),
                                        new Color(0.12f, 0.20f, 0.62f));
                    wall.Position = CellPosition(c, r, Cell, Cell);
                }
                else if (ch == '.')
                {
                    var pellet = MakeRect($"Pellet_r{r}_c{c}",
                                          new Vector2(PelletSize, PelletSize),
                                          new Color(0.95f, 0.85f, 0.65f));
                    pellet.Position = CellPosition(c, r, PelletSize, PelletSize);
                    _pellets[Key(c, r)] = pellet;
                    TotalPellets++;
                }
            }
        }
        if (_pac == null || !IsInstanceValid(_pac))
        {
            _pac = MakeRect("Pac", new Vector2(PacSize, PacSize), new Color(1.0f, 0.92f, 0.25f));
        }
        PacCol = 9;
        PacRow = 9;
        for (var i = 0; i < GhostStart.GetLength(0); i++)
        {
            var col = GhostStart[i, 0];
            var row = GhostStart[i, 1];
            var node = MakeRect($"Ghost_{_ghostSeq++}", new Vector2(GhostSize, GhostSize),
                                i == 0 ? new Color(0.95f, 0.30f, 0.35f)
                                       : (i == 1 ? new Color(0.95f, 0.60f, 0.25f)
                                                 : (i == 2 ? new Color(0.60f, 0.95f, 0.95f)
                                                           : new Color(0.90f, 0.50f, 0.95f))));
            _ghosts.Add(new Ghost { Col = col, Row = row, DirCol = i % 2 == 0 ? 1 : -1, DirRow = 0,
                                    Node = node });
        }
        GhostCount = _ghosts.Count;
        GhostSteps = 0;
        LastPatrolSteps = 0;
        PelletsEaten = 0;
        Recount();
        ApplyPac();
        ApplyGhosts();
    }

    private Vector2 CellPosition(int col, int row, float w, float h)
    {
        return new Vector2(OriginX + col * Cell + (Cell - w) / 2.0f,
                           OriginY + row * Cell + (Cell - h) / 2.0f);
    }

    /// <summary>Recomputes the counters from the board, so a forced state cannot lie about them.
    /// <see cref="PelletsEaten"/> is deliberately NOT derived here: it counts the eats this
    /// session actually observed, which is a different question from "how many pellets are not
    /// on the board" once a test has replaced the board with <see cref="ForceTestState"/>.</summary>
    private void Recount()
    {
        PelletsRemaining = _pellets.Count;
    }

    private void ApplyPac()
    {
        if (_pac == null)
        {
            return;
        }
        PacX = CellPosition(PacCol, PacRow, PacSize, PacSize).X + PacSize / 2.0f;
        PacY = CellPosition(PacCol, PacRow, PacSize, PacSize).Y + PacSize / 2.0f;
        _pac.Position = CellPosition(PacCol, PacRow, PacSize, PacSize);
    }

    private void ApplyGhosts()
    {
        foreach (var ghost in _ghosts)
        {
            if (ghost.Node == null)
            {
                continue;
            }
            ghost.Node.Position = CellPosition(ghost.Col, ghost.Row, GhostSize, GhostSize);
        }
        if (_ghosts.Count > 0)
        {
            Ghost0Col = _ghosts[0].Col;
            Ghost0Row = _ghosts[0].Row;
            Ghost0X = CellPosition(_ghosts[0].Col, _ghosts[0].Row, GhostSize, GhostSize).X + GhostSize / 2.0f;
            Ghost0Y = CellPosition(_ghosts[0].Col, _ghosts[0].Row, GhostSize, GhostSize).Y + GhostSize / 2.0f;
        }
        else
        {
            Ghost0Col = -1;
            Ghost0Row = -1;
            Ghost0X = -1.0f;
            Ghost0Y = -1.0f;
        }
    }

    private void UpdateHud()
    {
        if (_hud != null)
        {
            _hud.Text = $"SCORE {Score}  LIVES {Lives}  PELLETS {PelletsRemaining}";
        }
        if (_status != null)
        {
            _status.Text = GameOver ? (Won ? "MAZE CLEARED" : "GAME OVER")
                                    : $"PELLETS {PelletsRemaining}";
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
            // The input path is off by default; a test that wants it switches it on.
            var dc = 0;
            var dr = 0;
            if (Input.IsActionPressed("pac_left"))
            {
                dc = -1;
            }
            else if (Input.IsActionPressed("pac_right"))
            {
                dc = 1;
            }
            else if (Input.IsActionPressed("pac_up"))
            {
                dr = -1;
            }
            else if (Input.IsActionPressed("pac_down"))
            {
                dr = 1;
            }
            if (dc != 0 || dr != 0)
            {
                _inputAccum += dt;
                if (_inputAccum >= InputRepeat)
                {
                    _inputAccum = 0.0f;
                    StepPac(dc, dr);
                }
            }
            else
            {
                _inputAccum = 0.0f;
            }
        }
        if (GhostSpeed > 0.0f)
        {
            _patrolAccum += dt * GhostSpeed;
            var steps = 0;
            while (_patrolAccum >= 1.0f && steps < 32)
            {
                _patrolAccum -= 1.0f;
                steps++;
                PatrolOnce();
                if (GameOver)
                {
                    break;
                }
            }
        }
    }

    /// <summary>One ghost patrol step, shared by the clock path and by <see cref="StepGhosts"/>.</summary>
    private void PatrolOnce()
    {
        foreach (var ghost in _ghosts)
        {
            MoveGhost(ghost);
        }
        GhostSteps++;
        ApplyGhosts();
        CheckGhostHit();
    }

    /// <summary>
    /// One patrol step for one ghost: try the current direction, and if the next cell is a wall
    /// turn through a fixed direction cycle until an open cell is found. Deterministic by
    /// construction -- no randomness anywhere in this game.
    /// </summary>
    private void MoveGhost(Ghost ghost)
    {
        int[][] cycle =
        {
            new[] { 1, 0 }, new[] { 0, 1 }, new[] { -1, 0 }, new[] { 0, -1 },
        };
        for (var attempt = 0; attempt < 4; attempt++)
        {
            var nextCol = ghost.Col + ghost.DirCol;
            var nextRow = ghost.Row + ghost.DirRow;
            if (!IsWall(nextCol, nextRow))
            {
                ghost.Col = nextCol;
                ghost.Row = nextRow;
                return;
            }
            for (var i = 0; i < cycle.Length; i++)
            {
                if (cycle[i][0] == ghost.DirCol && cycle[i][1] == ghost.DirRow)
                {
                    var pick = cycle[(i + 1) % cycle.Length];
                    ghost.DirCol = pick[0];
                    ghost.DirRow = pick[1];
                    break;
                }
            }
        }
    }

    /// <summary>Charges one life when a ghost stands on Pac-Man's cell.</summary>
    private void CheckGhostHit()
    {
        if (GameOver)
        {
            return;
        }
        foreach (var ghost in _ghosts)
        {
            if (ghost.Col != PacCol || ghost.Row != PacRow)
            {
                continue;
            }
            Lives--;
            LastEvent = $"pac caught at={PacCol},{PacRow} lives={Lives}";
            ResetActors();
            if (Lives <= 0)
            {
                GameOver = true;
                Won = false;
                LastEvent += " game over";
            }
            ApplyPac();
            ApplyGhosts();
            UpdateHud();
            return;
        }
    }

    /// <summary>Puts Pac-Man and every ghost back on their starting cells (no pellet changes).</summary>
    private void ResetActors()
    {
        PacCol = 9;
        PacRow = 9;
        for (var i = 0; i < _ghosts.Count && i < GhostStart.GetLength(0); i++)
        {
            _ghosts[i].Col = GhostStart[i, 0];
            _ghosts[i].Row = GhostStart[i, 1];
            _ghosts[i].DirCol = i % 2 == 0 ? 1 : -1;
            _ghosts[i].DirRow = 0;
        }
    }

    // --- hooks the session drives ----------------------------------------------

    /// <summary>
    /// Moves Pac-Man exactly one cell if that cell is not a wall, then eats the pellet under him.
    /// This is the whole game rule in one place: blocked -> nothing happens; pellet -> 10 points;
    /// board empty -> win.
    /// </summary>
    public string StepPac(int dcol, int drow)
    {
        if (GameOver)
        {
            RejectedSteps++;
            LastEvent = "step refused: game over";
            return LastEvent;
        }
        var nextCol = PacCol + dcol;
        var nextRow = PacRow + drow;
        if (IsWall(nextCol, nextRow))
        {
            // TASK-116 D11: a step into a wall is a real answer to the player's key, and the
            // project's own design convention says observable state must be a Godot property.
            // Before this counter the refusal left no trace, so "there is a wall above the
            // start cell" was indistinguishable from "the up key is not wired".
            RejectedSteps++;
            LastEvent = $"blocked at={nextCol},{nextRow} from={PacCol},{PacRow}";
            return LastEvent;
        }
        PacCol = nextCol;
        PacRow = nextRow;
        ApplyPac();
        var key = Key(PacCol, PacRow);
        if (_pellets.ContainsKey(key))
        {
            var node = _pellets[key];
            DropNode(node);
            _pellets.Remove(key);
            Score += 10;
            PelletsEaten++;
            Recount();
            LastEvent = $"ate pellet at={PacCol},{PacRow} score={Score} left={PelletsRemaining}";
            if (PelletsRemaining == 0)
            {
                GameOver = true;
                Won = true;
                LastEvent += " maze cleared";
            }
        }
        else
        {
            LastEvent = $"moved to={PacCol},{PacRow} score={Score} left={PelletsRemaining}";
        }
        UpdateHud();
        // Walking into a ghost costs a life exactly like a ghost walking into Pac-Man.
        if (!GameOver)
        {
            CheckGhostHit();
        }
        return LastEvent;
    }

    /// <summary>Advances the ghost patrol by an exact number of steps (a fixed-step test hook).</summary>
    public string StepGhosts(int steps)
    {
        LastPatrolSteps = 0;
        for (var i = 0; i < steps && !GameOver; i++)
        {
            PatrolOnce();
            LastPatrolSteps++;
        }
        LastEvent = $"patrol steps={steps} took={LastPatrolSteps} total={GhostSteps} "
                    + $"ghost0={Ghost0Col},{Ghost0Row}";
        return LastEvent;
    }

    /// <summary>Ghost patrol steps per second; 0 keeps them still (the default).</summary>
    public string SetGhostSpeed(float perSecond)
    {
        GhostSpeed = perSecond;
        _patrolAccum = 0.0f;
        LastEvent = $"ghost speed={GhostSpeed}";
        GD.Print($"PAC_SPEED speed={GhostSpeed}");
        return LastEvent;
    }

    /// <summary>Switches Pac-Man's input polling on or off (the default is off).</summary>
    public string SetPollInput(bool enabled)
    {
        PollInput = enabled;
        LastEvent = $"poll_input={PollInput}";
        return LastEvent;
    }

    /// <summary>The board as rows of <c>#</c>/<c>.</c>/space, plus every exported fact.</summary>
    public string Dump()
    {
        var sb = new StringBuilder();
        for (var r = 0; r < Rows; r++)
        {
            for (var c = 0; c < Cols; c++)
            {
                if (_ghosts.Count > 0)
                {
                    var onGhost = false;
                    foreach (var ghost in _ghosts)
                    {
                        if (ghost.Col == c && ghost.Row == r)
                        {
                            onGhost = true;
                            break;
                        }
                    }
                    if (onGhost)
                    {
                        sb.Append('G');
                        continue;
                    }
                }
                if (c == PacCol && r == PacRow)
                {
                    sb.Append('P');
                    continue;
                }
                if (_pellets.ContainsKey(Key(c, r)))
                {
                    sb.Append('.');
                    continue;
                }
                sb.Append(CellAt(c, r) == '#' ? '#' : ' ');
            }
            if (r + 1 < Rows)
            {
                sb.Append('/');
            }
        }
        return $"board={sb} score={Score} pellets={PelletsRemaining} eaten={PelletsEaten} "
               + $"total={TotalPellets} pac={PacCol},{PacRow} pac_px={PacX:F1},{PacY:F1} "
               + $"lives={Lives} over={GameOver} won={Won} ghosts={GhostCount} "
               + $"ghost0={Ghost0Col},{Ghost0Row}={Ghost0X:F1},{Ghost0Y:F1} "
               + $"patrol={GhostSteps} last_patrol={LastPatrolSteps} ticks={Ticks} speed={GhostSpeed} poll={PollInput} "
               + $"last={LastEvent}";
    }

    /// <summary>The two readback shortcuts: where Pac-Man is and where ghost 0 is.</summary>
    public string Geometry()
    {
        return $"pac={PacCol},{PacRow} pac_px={PacX:F0},{PacY:F0} "
               + $"ghost0={Ghost0Col},{Ghost0Row} ghost0_px={Ghost0X:F0},{Ghost0Y:F0} "
               + $"patrol={GhostSteps}";
    }

    /// <summary>
    /// Writes the whole deterministic state in one call --
    /// <c>"pac=c,r;ghosts=c,r|...;pellets=all|none|c,r|...;score=n;lives=n;speed=s"</c>.
    ///
    /// <para>Keys may be omitted; the ones given are applied. The ghost speed and polling are
    /// switched OFF here, so a session's aim and the next readback are the same fact. A test that
    /// wants motion calls <see cref="SetGhostSpeed"/> or <see cref="StepGhosts"/> itself -- which
    /// is why "a ghost moved" can never be an accident of timing.</para>
    /// </summary>
    public string ForceTestState(string spec)
    {
        GhostSpeed = 0.0f;
        PollInput = false;
        _patrolAccum = 0.0f;
        Ticks = 0;
        Score = 0;
        Lives = 3;
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
                case "pac":
                    {
                        var p = kv[1].Split(',');
                        PacCol = int.Parse(p[0]);
                        PacRow = int.Parse(p[1]);
                    }
                    break;
                case "ghosts":
                    if (kv[1] == "none")
                    {
                        foreach (var ghost in _ghosts)
                        {
                            DropNode(ghost.Node);
                        }
                        _ghosts.Clear();
                    }
                    else
                    {
                        var index = 0;
                        foreach (var cellPart in kv[1].Split('|'))
                        {
                            if (cellPart.Length == 0 || index >= _ghosts.Count)
                            {
                                continue;
                            }
                            var p = cellPart.Split(',');
                            _ghosts[index].Col = int.Parse(p[0]);
                            _ghosts[index].Row = int.Parse(p[1]);
                            index++;
                        }
                    }
                    break;
                case "pellets":
                    if (kv[1] == "all")
                    {
                        break; // BuildBoard already left every pellet in place.
                    }
                    foreach (var node in new List<ColorRect>(_pellets.Values))
                    {
                        DropNode(node);
                    }
                    _pellets.Clear();
                    if (kv[1] == "none")
                    {
                        break;
                    }
                    foreach (var cellPart in kv[1].Split('|'))
                    {
                        if (cellPart.Length == 0)
                        {
                            continue;
                        }
                        var p = cellPart.Split(',');
                        var c = int.Parse(p[0]);
                        var r = int.Parse(p[1]);
                        var node = MakeRect($"Pellet_r{r}_c{c}", new Vector2(PelletSize, PelletSize),
                                            new Color(0.95f, 0.85f, 0.65f));
                        node.Position = CellPosition(c, r, PelletSize, PelletSize);
                        _pellets[Key(c, r)] = node;
                    }
                    break;
                case "score":
                    Score = int.Parse(kv[1]);
                    break;
                case "lives":
                    Lives = int.Parse(kv[1]);
                    break;
                case "speed":
                    GhostSpeed = float.Parse(kv[1]);
                    break;
            }
        }
        GhostCount = _ghosts.Count;
        GhostSteps = 0;
        LastPatrolSteps = 0;
        PelletsEaten = 0;
        _inputAccum = 0.0f;
        Recount();
        ApplyPac();
        ApplyGhosts();
        UpdateHud();
        LastEvent = $"forced pellets={PelletsRemaining} total={TotalPellets} pac={PacCol},{PacRow} "
                    + $"ghosts={GhostCount} lives={Lives} score={Score} speed={GhostSpeed}";
        return LastEvent;
    }
}
