using Godot;
using System.Collections.Generic;
using System.Text;

namespace bomberman;

/// <summary>
/// Bomberman -- the thirteenth C# game of the godot-mcp series (TASK-101, DECISIONS.md D138).
///
/// <para><b>Design rule</b> (inherited from the twelve games before it): every fact the evidence
/// model needs is a real Godot property on the root node -- <see cref="BricksRemaining"/>,
/// <see cref="BricksDestroyed"/>, <see cref="BombsPlaced"/>, <see cref="BombsActive"/>,
/// <see cref="LastBlast"/>, <see cref="LastBlastCount"/>, <see cref="EnemiesAlive"/>,
/// <see cref="EnemiesKilled"/>, <see cref="Lives"/>, <see cref="Score"/>, <see cref="PlayerRow"/>,
/// <see cref="PlayerCol"/>, <see cref="Moves"/>, <see cref="RejectedMoves"/>, <see cref="Exploded"/>,
/// <see cref="Won"/>, <see cref="GameOver"/>, <see cref="Elapsed"/>, <see cref="Ticks"/>. A session
/// asserts these with <c>running_game_assert_node_state</c>; it never parses a log line.</para>
///
/// <para><b>Determinism rule.</b> The whole world is a pure function of a level string (hard walls,
/// floor, bricks, the player spawn, enemy spawns), and it is pinned with ONE
/// <see cref="ForceTestState"/> call. Nothing moves on its own: <see cref="AutoClock"/> is 0 and
/// <see cref="PollInput"/> is false by default. A bomb's fuse advances ONLY through
/// <see cref="StepFuse"/> (or the fixed-step clock), and enemies move ONLY through
/// <see cref="StepEnemies"/>. That is what makes "the blast covers exactly these cells" a fact an
/// independent recomputation can check instead of a timing accident.</para>
///
/// <para><b>Frame-rate independence (the F-1 lesson).</b> The auto clock is a FLOAT ACCUMULATOR
/// (<c>_autoAccum += delta * AutoClock</c>), never <c>(int)(delta * rate)</c>. Two producers, two
/// properties: <see cref="LastAutoSteps"/> is what the clock applied on the last frame and
/// <see cref="LastHookSteps"/> is what the last <see cref="StepTick"/> CALL applied. 2048's r1 run
/// (TASK-100, defect G1) proved a single property read by both producers reads the wrong number.
/// <see cref="Elapsed"/> is a monotonic float second counter that is never truncated.</para>
///
/// <para><b>Rules.</b> The player moves one cell orthogonally; a wall, a brick, or a live bomb is
/// refused (<see cref="RejectedMoves"/> grows and the board is unchanged).
/// <see cref="PlaceBomb"/> drops a bomb with a fixed fuse on the player's own cell. When the fuse
/// runs out the blast spreads up to <see cref="BlastRange"/> cells in the four directions, is
/// stopped by a hard wall, destroys the FIRST brick it meets and stops there, and sets off any other
/// bomb it touches (a chain). Bricks destroyed, enemies caught and a player caught are all counted;
/// a caught player loses a life and respawns at the spawn cell, and the loss of the last life ends
/// the game. Every brick gone AND every enemy gone is the win.</para>
///
/// <para><b>TASK-140 §1.B.3: the `AutoClock` trade-off, written down.</b> A bomb has always been
/// DRAWN (one <c>ColorRect</c> per slot), but until this batch it was drawn in
/// <c>Color(0.15, 0.15, 0.20)</c> on an empty-floor cell of <c>Color(0.15, 0.17, 0.21)</c> -- a
/// visible-in-the-tree, invisible-on-the-screen 0.02 difference. That is fixed here, and the
/// contrast is exported (<see cref="BombsVisible"/>, <see cref="BombMinContrast"/>). The
/// <see cref="AutoClock"/> choice is NOT changed: it stays 0, because the determinism rule above
/// is what makes the blast cells recomputable, and TASK-136 measured the alternative (clock on)
/// to be worse in the only way that matters here -- the bomb went off next to the player, the
/// player lost lives and the run was over in 3 injected steps ("一按就死", TASK-136 §6.2).
/// The consequence is stated plainly rather than hidden: with the clock off,
/// <see cref="Detonations"/> stays 0 in a playtest run and only a driver that calls
/// <see cref="StepFuse"/> (or switches the clock on) produces a blast. Visibility does not
/// depend on the fuse: the bomb appears on the frame it is placed.</para>
///
/// <para><b>All cells are runtime-created.</b> <see cref="_Ready"/> builds one <c>ColorRect</c> per
/// cell plus one <c>ColorRect</c> per unit; the scene file carries only the three static nodes
/// (Background, Hud, Status). That keeps the edited scene small, keeps it immune to the D-3
/// duplicate-name trap, and makes "a node created at run time really is drawn" part of this game's
/// own evidence.</para>
/// </summary>
public partial class BombermanGame : Node2D
{
    // --- the level catalogue (the default board is Levels[0]) ---------------------
    private static readonly string[] Levels =
    {
        // 0: the classic field -- pillars, ten bricks, two enemies, three lives.
        "#############/#@..........#/#.#.#.#.#.#.#/#.B.B.B.B.B.#/#...........#/#.B.B.B.B.B.#/#.#.#.#.#.#.#/#E.........E#/#############",
        // 1: one brick, one enemy, one bomb -- the whole win in one blast.
        "#############/#@..........#/#...........#/#.....B.....#/#...........#/#...........#/#.....E.....#/#...........#/#############",
        // 2: the blast boundary -- a brick stops the spread, a wall stops the spread.
        "#############/#@.B.B.....#/#...........#/#..B........#/#...........#/#############",
    };

    // --- the grid ---------------------------------------------------------------
    /// <summary>Columns of the field.</summary>
    [Export] public int Cols = 0;

    /// <summary>Rows of the field.</summary>
    [Export] public int Rows = 0;

    /// <summary>Size of one cell in pixels.</summary>
    [Export] public int Cell = 44;

    /// <summary>Left edge of the field in pixels.</summary>
    [Export] public int OriginX = 124;

    /// <summary>Top edge of the field in pixels.</summary>
    [Export] public int OriginY = 72;

    /// <summary>Index of the level currently loaded.</summary>
    [Export] public int LevelIndex = 0;

    /// <summary>The level string currently loaded, rows separated by '/'.</summary>
    [Export] public string LevelSpec = "";

    /// <summary>How far a blast reaches before a wall or a brick stops it.</summary>
    [Export] public int BlastRange = 2;

    /// <summary>Fixed fuse length of a bomb, in StepFuse ticks.</summary>
    [Export] public int FuseSteps = 3;

    /// <summary>How many bombs may be live at once.</summary>
    [Export] public int MaxBombs = 3;

    /// <summary>Lives the player starts with.</summary>
    [Export] public int LivesPerGame = 3;

    // --- observable state, all of it a real Godot property ----------------------
    /// <summary>The spawn cell, read from the level's '@'.</summary>
    [Export] public int SpawnRow = 0;

    /// <summary>The spawn column.</summary>
    [Export] public int SpawnCol = 0;

    /// <summary>Bricks the level started with.</summary>
    [Export] public int BricksTotal = 0;

    /// <summary>Bricks still standing.</summary>
    [Export] public int BricksRemaining = 0;

    /// <summary>Bricks destroyed so far.</summary>
    [Export] public int BricksDestroyed = 0;

    /// <summary>A stable hash of the wall/floor/brick grid -- a sample can watch it change.</summary>
    [Export] public int GridHash = 0;

    /// <summary>A stable hash of the moving units (player, enemies, bombs).</summary>
    [Export] public int UnitHash = 0;

    /// <summary>Bombs placed over the whole level.</summary>
    [Export] public int BombsPlaced = 0;

    /// <summary>Bombs live right now.</summary>
    [Export] public int BombsActive = 0;

    /// <summary>Live bombs, "r,c,fuse|..." in placement order.</summary>
    [Export] public string BombList = "";

    // --- TASK-140 §1.B.3: the placed bomb has to be VISIBLE --------------------------------
    // Measured by TASK-136 (registered, unfixed): after two `bomb_place` steps the HUD read
    // `BOMBS 2` while the screen showed only the floor -- the bomb's rect was drawn with
    // `Color(0.15, 0.15, 0.20)` on top of an empty floor cell painted `Color(0.15, 0.17, 0.21)`,
    // i.e. a difference of 0.02 in one channel: a bomb nobody can see.  A player cannot avoid
    // (or use) what is not on the screen.
    //
    // The bomb now has its own contrast and the contrast is EXPORTED, so "the bomb is visible"
    // is a machine-checked number and not a description of a screenshot: `BombMinContrast` is
    // the smallest per-channel difference between a live bomb's rect and the cell under it, and
    // `BombsVisible` counts the bomb rects that are actually visible in the tree.
    /// <summary>Bomb colour while the fuse has more than one tick left.</summary>
    [Export] public Color BombColor = new Color(0.95f, 0.35f, 0.10f);

    /// <summary>Bomb colour on the last tick before the blast (the "it is about to go" read).</summary>
    [Export] public Color BombColorDue = new Color(1.0f, 0.94f, 0.25f);

    /// <summary>Live bombs whose rect is actually visible in the tree.</summary>
    [Export] public int BombsVisible = 0;

    /// <summary>Smallest per-channel difference between a live bomb rect and the cell under it
    /// (0 when no bomb is live).  The TASK-140 §1.B.3 evidence number.</summary>
    [Export] public float BombMinContrast = 0.0f;

    /// <summary>Placements the game REFUSED (a bomb already on the cell, or the limit
    /// reached).  TASK-140 §1.B.3: without this counter a refused `bomb_place` changed
    /// NOTHING at all, so "the key is not wired" and "the rule said no" were the same
    /// evidence -- the project's own convention #1 (observable state must be a Godot
    /// property) applied to the one refusal path this game had missed.</summary>
    [Export] public int RejectedPlaces = 0;

    /// <summary>Row of the most recently placed bomb.</summary>
    [Export] public int LastBombRow = -1;

    /// <summary>Column of the most recently placed bomb.</summary>
    [Export] public int LastBombCol = -1;

    /// <summary>The cells of the most recent detonation, "r,c|r,c|..." in generation order.</summary>
    [Export] public string LastBlast = "";

    /// <summary>How many cells that detonation covered.</summary>
    [Export] public int LastBlastCount = 0;

    /// <summary>A stable hash of the most recent blast, so "a different blast" is checkable.</summary>
    [Export] public int BlastHash = 0;

    /// <summary>Detonations so far.</summary>
    [Export] public int Detonations = 0;

    /// <summary>Enemies the level started with.</summary>
    [Export] public int EnemiesTotal = 0;

    /// <summary>Enemies still alive.</summary>
    [Export] public int EnemiesAlive = 0;

    /// <summary>Enemies killed by blasts.</summary>
    [Export] public int EnemiesKilled = 0;

    /// <summary>Live enemies, "r,c|r,c|..." in spawn order -- the layout an assert can name.</summary>
    [Export] public string EnemyList = "";

    /// <summary>Lives left.</summary>
    [Export] public int Lives = 3;

    /// <summary>Times the player was caught.</summary>
    [Export] public int Deaths = 0;

    /// <summary>Points: 10 per brick, 100 per enemy.</summary>
    [Export] public int Score = 0;

    /// <summary>Player row.</summary>
    [Export] public int PlayerRow = 0;

    /// <summary>Player column.</summary>
    [Export] public int PlayerCol = 0;

    /// <summary>Moves accepted.</summary>
    [Export] public int Moves = 0;

    /// <summary>Moves refused: a wall, a brick, a live bomb, or a finished game.</summary>
    [Export] public int RejectedMoves = 0;

    /// <summary>True when the last death was a blast.</summary>
    [Export] public bool Exploded = false;

    /// <summary>True when the last death was an enemy catching the player.</summary>
    [Export] public bool DeadByEnemy = false;

    /// <summary>True when no brick and no enemy is left.</summary>
    [Export] public bool Won = false;

    /// <summary>True when the level ended, by the win or by the last life.</summary>
    [Export] public bool GameOver = false;

    /// <summary>Row the last <see cref="ProbeCell"/> looked at.</summary>
    [Export] public int ProbeRow = -1;

    /// <summary>Column the last <see cref="ProbeCell"/> looked at.</summary>
    [Export] public int ProbeCol = -1;

    /// <summary>Probed cell state: wall / floor / brick / bomb / enemy / player / player_bomb.</summary>
    [Export] public string ProbeState = "";

    /// <summary>Seconds since the last reset: a monotonic FLOAT accumulator, never truncated.</summary>
    [Export] public float Elapsed = 0.0f;

    /// <summary>Fixed-step ticks per second; 0 keeps the world still (the default).</summary>
    [Export] public float AutoClock = 0.0f;

    /// <summary>Ticks the auto clock has applied over the whole level.</summary>
    [Export] public int AutoTicks = 0;

    /// <summary>Ticks the auto clock applied on the LAST frame (0 while the clock is off).</summary>
    [Export] public int LastAutoSteps = 0;

    /// <summary>
    /// Ticks the LAST <see cref="StepTick"/> CALL applied. Its own property, and the clock never
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

    /// <summary>Bombs that arrived through the declared input actions.</summary>
    [Export] public int InputBombs = 0;

    /// <summary>Frames processed since the last reset.</summary>
    [Export] public int Ticks = 0;

    /// <summary>What the last hook did -- the readback string a session quotes.</summary>
    [Export] public string LastEvent = "";

    // --- private model ---------------------------------------------------------
    private bool[] _wall = new bool[1];
    private bool[] _brick = new bool[1];
    private readonly List<int> _bombRow = new List<int>();
    private readonly List<int> _bombCol = new List<int>();
    private readonly List<int> _bombFuse = new List<int>();
    private readonly List<int> _enemyRow = new List<int>();
    private readonly List<int> _enemyCol = new List<int>();
    private readonly List<ColorRect> _cellRect = new List<ColorRect>();
    private readonly List<ColorRect> _enemyRect = new List<ColorRect>();
    private readonly List<ColorRect> _bombRect = new List<ColorRect>();
    private ColorRect _playerRect;
    private Label _hud;
    private Label _status;
    private float _autoAccum;
    private bool _prevUp;
    private bool _prevRight;
    private bool _prevDown;
    private bool _prevLeft;
    private bool _prevBomb;

    private int Idx(int row, int col)
    {
        return row * Cols + col;
    }

    private bool InBounds(int row, int col)
    {
        return row >= 0 && row < Rows && col >= 0 && col < Cols;
    }

    private bool IsWall(int row, int col)
    {
        return !InBounds(row, col) || _wall[Idx(row, col)];
    }

    private bool IsBrick(int row, int col)
    {
        return InBounds(row, col) && _brick[Idx(row, col)];
    }

    private int BombAt(int row, int col)
    {
        for (var i = 0; i < _bombRow.Count; i++)
        {
            if (_bombRow[i] == row && _bombCol[i] == col)
            {
                return i;
            }
        }
        return -1;
    }

    private int EnemyAt(int row, int col)
    {
        for (var i = 0; i < _enemyRow.Count; i++)
        {
            if (_enemyRow[i] == row && _enemyCol[i] == col)
            {
                return i;
            }
        }
        return -1;
    }

    public override void _Ready()
    {
        _hud = GetNodeOrNull<Label>("Hud");
        _status = GetNodeOrNull<Label>("Status");
        LoadLevel(LevelIndex);
        GD.Print($"BOMBERMAN_READY level={LevelIndex} cols={Cols} rows={Rows} bricks={BricksTotal} "
                 + $"enemies={EnemiesTotal} lives={Lives} range={BlastRange} fuse={FuseSteps} "
                 + $"auto={AutoClock} poll={PollInput}");
    }

    // --- level loading ----------------------------------------------------------
    private void LoadLevel(int index)
    {
        LevelIndex = index;
        LevelSpec = Levels[index];
        ParseLevel(LevelSpec);
        CreateNodes();
        ResetCounters();
        Recompute();
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
        _brick = new bool[total];
        _bombRow.Clear();
        _bombCol.Clear();
        _bombFuse.Clear();
        _enemyRow.Clear();
        _enemyCol.Clear();
        for (var r = 0; r < Rows; r++)
        {
            var line = raw[r];
            for (var c = 0; c < Cols; c++)
            {
                var ch = c < line.Length ? line[c] : '#';
                var i = Idx(r, c);
                switch (ch)
                {
                    case '#':
                        _wall[i] = true;
                        break;
                    case 'B':
                        _brick[i] = true;
                        break;
                    case '@':
                        PlayerRow = r;
                        PlayerCol = c;
                        SpawnRow = r;
                        SpawnCol = c;
                        break;
                    case 'E':
                        _enemyRow.Add(r);
                        _enemyCol.Add(c);
                        break;
                }
            }
        }
    }

    private void ResetCounters()
    {
        BricksTotal = 0;
        for (var i = 0; i < _brick.Length; i++)
        {
            if (_brick[i])
            {
                BricksTotal++;
            }
        }
        BricksRemaining = BricksTotal;
        BricksDestroyed = 0;
        GridHash = 0;
        UnitHash = 0;
        BombsPlaced = 0;
        BombsActive = 0;
        BombList = "";
        RejectedPlaces = 0;
        // TASK-140 §1.B.3: the visibility readings belong to the board, so a reset clears them
        // with it (a stale contrast would otherwise read as "a bomb is visible" on an empty field).
        BombsVisible = 0;
        BombMinContrast = 0.0f;
        LastBombRow = -1;
        LastBombCol = -1;
        LastBlast = "";
        LastBlastCount = 0;
        BlastHash = 0;
        Detonations = 0;
        EnemiesTotal = _enemyRow.Count;
        EnemiesAlive = _enemyRow.Count;
        EnemiesKilled = 0;
        EnemyList = "";
        Lives = LivesPerGame;
        Deaths = 0;
        Score = 0;
        Moves = 0;
        RejectedMoves = 0;
        Exploded = false;
        DeadByEnemy = false;
        Won = false;
        GameOver = false;
        ProbeRow = -1;
        ProbeCol = -1;
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
        InputBombs = 0;
        _prevUp = false;
        _prevRight = false;
        _prevDown = false;
        _prevLeft = false;
        _prevBomb = false;
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
        foreach (var rect in _enemyRect)
        {
            if (rect != null && IsInstanceValid(rect))
            {
                RemoveChild(rect);
                rect.QueueFree();
            }
        }
        foreach (var rect in _bombRect)
        {
            if (rect != null && IsInstanceValid(rect))
            {
                RemoveChild(rect);
                rect.QueueFree();
            }
        }
        if (_playerRect != null && IsInstanceValid(_playerRect))
        {
            RemoveChild(_playerRect);
            _playerRect.QueueFree();
        }
        _cellRect.Clear();
        _enemyRect.Clear();
        _bombRect.Clear();
        for (var r = 0; r < Rows; r++)
        {
            for (var c = 0; c < Cols; c++)
            {
                var rect = new ColorRect();
                rect.Name = $"Cell_{r}_{c}";
                rect.Position = new Vector2(OriginX + c * Cell + 1, OriginY + r * Cell + 1);
                rect.Size = new Vector2(Cell - 2, Cell - 2);
                rect.Color = new Color(0.13f, 0.14f, 0.18f);
                AddChild(rect);
                _cellRect.Add(rect);
            }
        }
        for (var i = 0; i < _enemyRow.Count; i++)
        {
            var rect = new ColorRect();
            rect.Name = $"Enemy_{i}";
            rect.Size = new Vector2(Cell - 16, Cell - 16);
            rect.Color = new Color(0.90f, 0.25f, 0.35f);
            AddChild(rect);
            _enemyRect.Add(rect);
        }
        for (var i = 0; i < MaxBombs; i++)
        {
            var rect = new ColorRect();
            rect.Name = $"Bomb_{i}";
            rect.Size = new Vector2(Cell - 18, Cell - 18);
            // TASK-140 §1.B.3: the OLD colour here was (0.15, 0.15, 0.20) -- two hundredths
            // away from the empty-floor cell it is drawn on.  The declared colours are used
            // instead, and `ApplyBoard` reports their measured contrast.
            rect.Color = BombColor;
            rect.Visible = false;
            AddChild(rect);
            _bombRect.Add(rect);
        }
        _playerRect = new ColorRect();
        _playerRect.Name = "PlayerSprite";
        _playerRect.Size = new Vector2(Cell - 12, Cell - 12);
        _playerRect.Color = new Color(0.30f, 0.75f, 1.00f);
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
                if (rect == null || !IsInstanceValid(rect))
                {
                    continue;
                }
                if (_wall[i])
                {
                    rect.Color = new Color(0.38f, 0.41f, 0.50f);
                }
                else if (_brick[i])
                {
                    rect.Color = new Color(0.68f, 0.34f, 0.20f);
                }
                else
                {
                    rect.Color = new Color(0.15f, 0.17f, 0.21f);
                }
            }
        }
        for (var i = 0; i < _enemyRect.Count; i++)
        {
            var rect = _enemyRect[i];
            if (rect == null || !IsInstanceValid(rect))
            {
                continue;
            }
            var alive = i < _enemyRow.Count;
            rect.Visible = alive;
            if (alive)
            {
                rect.Position = new Vector2(OriginX + _enemyCol[i] * Cell + 9,
                                            OriginY + _enemyRow[i] * Cell + 9);
            }
        }
        for (var i = 0; i < _bombRect.Count; i++)
        {
            var rect = _bombRect[i];
            if (rect == null || !IsInstanceValid(rect))
            {
                continue;
            }
            var live = i < _bombRow.Count;
            rect.Visible = live;
            if (live)
            {
                rect.Position = new Vector2(OriginX + _bombCol[i] * Cell + 10,
                                            OriginY + _bombRow[i] * Cell + 10);
                rect.Color = _bombFuse[i] <= 1 ? BombColorDue : BombColor;
            }
        }
        // TASK-140 §1.B.3: the visibility evidence, measured from the rects and the cells they
        // sit on -- not from a screenshot description.
        BombsVisible = 0;
        var minContrast = 0.0f;
        for (var i = 0; i < _bombRow.Count; i++)
        {
            if (i >= _bombRect.Count)
            {
                continue;
            }
            var rect = _bombRect[i];
            if (rect == null || !IsInstanceValid(rect))
            {
                continue;
            }
            if (rect.Visible)
            {
                BombsVisible++;
            }
            var cellIdx = Idx(_bombRow[i], _bombCol[i]);
            var cell = (cellIdx >= 0 && cellIdx < _cellRect.Count) ? _cellRect[cellIdx] : null;
            var c = rect.Color;
            if (cell != null && IsInstanceValid(cell))
            {
                var k = cell.Color;
                var d = Mathf.Max(Mathf.Abs(c.R - k.R),
                                  Mathf.Max(Mathf.Abs(c.G - k.G), Mathf.Abs(c.B - k.B)));
                if (minContrast == 0.0f || d < minContrast)
                {
                    minContrast = d;
                }
            }
        }
        BombMinContrast = minContrast;
        if (_playerRect != null && IsInstanceValid(_playerRect))
        {
            _playerRect.Position = new Vector2(OriginX + PlayerCol * Cell + 6,
                                               OriginY + PlayerRow * Cell + 6);
        }
    }

    private void UpdateHud()
    {
        if (_hud != null)
        {
            _hud.Text = $"BRICKS {BricksRemaining}/{BricksTotal}  ENEMIES {EnemiesAlive}/{EnemiesTotal}  "
                        + $"LIVES {Lives}  SCORE {Score}  BOMBS {BombsActive}";
        }
        if (_status != null)
        {
            if (Won)
            {
                _status.Text = "FIELD CLEARED";
            }
            else if (GameOver)
            {
                _status.Text = "GAME OVER";
            }
            else
            {
                _status.Text = "BOMB THE BRICKS";
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

    /// <summary>The blast of one bomb, in generation order: centre first, then up/down/left/right.</summary>
    private List<int[]> BlastCells(int row, int col)
    {
        var cells = new List<int[]> { new[] { row, col } };
        var dirs = new[] { new[] { -1, 0 }, new[] { 1, 0 }, new[] { 0, -1 }, new[] { 0, 1 } };
        foreach (var d in dirs)
        {
            for (var step = 1; step <= BlastRange; step++)
            {
                var r = row + d[0] * step;
                var c = col + d[1] * step;
                if (IsWall(r, c))
                {
                    break;
                }
                cells.Add(new[] { r, c });
                if (IsBrick(r, c))
                {
                    break; // the first brick takes the hit and stops the spread
                }
            }
        }
        return cells;
    }

    private void Recompute()
    {
        var hash = 17;
        unchecked
        {
            for (var r = 0; r < Rows; r++)
            {
                for (var c = 0; c < Cols; c++)
                {
                    var i = Idx(r, c);
                    var code = _wall[i] ? 1 : (_brick[i] ? 3 : 2);
                    hash = hash * 31 + code;
                }
            }
        }
        GridHash = hash;

        var bricks = 0;
        for (var i = 0; i < _brick.Length; i++)
        {
            if (_brick[i])
            {
                bricks++;
            }
        }
        BricksRemaining = bricks;
        BricksDestroyed = BricksTotal - bricks;

        var unitHash = 17;
        var enemyList = new StringBuilder();
        for (var i = 0; i < _enemyRow.Count; i++)
        {
            if (enemyList.Length > 0)
            {
                enemyList.Append('|');
            }
            enemyList.Append(_enemyRow[i]).Append(',').Append(_enemyCol[i]);
        }
        EnemyList = enemyList.ToString();
        EnemiesAlive = _enemyRow.Count;

        var bombList = new StringBuilder();
        for (var i = 0; i < _bombRow.Count; i++)
        {
            if (bombList.Length > 0)
            {
                bombList.Append('|');
            }
            bombList.Append(_bombRow[i]).Append(',').Append(_bombCol[i]).Append(',').Append(_bombFuse[i]);
        }
        BombList = bombList.ToString();
        BombsActive = _bombRow.Count;

        unchecked
        {
            for (var r = 0; r < Rows; r++)
            {
                for (var c = 0; c < Cols; c++)
                {
                    var v = 0;
                    if (BombAt(r, c) >= 0)
                    {
                        v += 5;
                    }
                    if (EnemyAt(r, c) >= 0)
                    {
                        v += 11;
                    }
                    if (r == PlayerRow && c == PlayerCol)
                    {
                        v += 23;
                    }
                    unitHash = unitHash * 31 + v;
                }
            }
        }
        UnitHash = unitHash;

        Score = BricksDestroyed * 10 + EnemiesKilled * 100;
        Won = BricksRemaining == 0 && EnemiesAlive == 0;
        GameOver = Won || Lives <= 0;
    }

    // --- hooks the session drives ----------------------------------------------

    /// <summary>Moves the player one cell; a wall, a brick or a live bomb is refused.</summary>
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
            LastEvent = $"rejected reason=game_over dir={dir} won={Won} lives={Lives} "
                        + $"moves={Moves} rejected={RejectedMoves}";
            return LastEvent;
        }
        var nr = PlayerRow + dr;
        var nc = PlayerCol + dc;
        if (IsWall(nr, nc))
        {
            RejectedMoves++;
            LastEvent = $"rejected reason=wall dir={dir} at={nr},{nc} moves={Moves} "
                        + $"rejected={RejectedMoves}";
            return LastEvent;
        }
        if (IsBrick(nr, nc))
        {
            RejectedMoves++;
            LastEvent = $"rejected reason=brick dir={dir} at={nr},{nc} moves={Moves} "
                        + $"rejected={RejectedMoves}";
            return LastEvent;
        }
        if (BombAt(nr, nc) >= 0)
        {
            RejectedMoves++;
            LastEvent = $"rejected reason=bomb dir={dir} at={nr},{nc} moves={Moves} "
                        + $"rejected={RejectedMoves}";
            return LastEvent;
        }
        var caught = EnemyAt(nr, nc);
        PlayerRow = nr;
        PlayerCol = nc;
        Moves++;
        if (caught >= 0)
        {
            // B-1 (found by this game's own r1 run): walking into an enemy costs the player a life
            // and the enemy SURVIVES -- it is not consumed. The first version removed it, which made
            // EnemiesAlive and the unit hash disagree with the rules the evidence quotes.
            KillPlayer("enemy");
            Recompute();
            ApplyBoard();
            UpdateHud();
            LastEvent = $"walked_into_enemy dir={dir} at={nr},{nc} lives={Lives} moves={Moves} "
                        + $"alive={EnemiesAlive} over={GameOver}";
            return LastEvent;
        }
        Recompute();
        ApplyBoard();
        UpdateHud();
        LastEvent = $"moved dir={dir} to={PlayerRow},{PlayerCol} moves={Moves} lives={Lives}";
        return LastEvent;
    }

    /// <summary>Drops a bomb with the fixed fuse on the player's own cell.</summary>
    public string PlaceBomb()
    {
        if (GameOver)
        {
            RejectedMoves++;
            RejectedPlaces++;
            LastEvent = $"rejected reason=game_over at={PlayerRow},{PlayerCol} over={GameOver} "
                        + $"rejected_places={RejectedPlaces}";
            return LastEvent;
        }
        if (BombAt(PlayerRow, PlayerCol) >= 0)
        {
            RejectedMoves++;
            RejectedPlaces++;
            LastEvent = $"rejected reason=bomb_already_here at={PlayerRow},{PlayerCol} "
                        + $"rejected={RejectedMoves} rejected_places={RejectedPlaces}";
            return LastEvent;
        }
        if (_bombRow.Count >= MaxBombs)
        {
            RejectedMoves++;
            RejectedPlaces++;
            LastEvent = $"rejected reason=max_bombs active={_bombRow.Count} "
                        + $"rejected={RejectedMoves} rejected_places={RejectedPlaces}";
            return LastEvent;
        }
        _bombRow.Add(PlayerRow);
        _bombCol.Add(PlayerCol);
        _bombFuse.Add(FuseSteps);
        BombsPlaced++;
        LastBombRow = PlayerRow;
        LastBombCol = PlayerCol;
        Recompute();
        ApplyBoard();
        UpdateHud();
        LastEvent = $"bomb at={PlayerRow},{PlayerCol} fuse={FuseSteps} active={BombsActive} "
                    + $"placed={BombsPlaced}";
        return LastEvent;
    }

    /// <summary>
    /// Advances every live fuse by <paramref name="steps"/> ticks and detonates the bombs that reach
    /// zero, including any bomb the blast touches (a chain).
    /// </summary>
    public string StepFuse(int steps)
    {
        var fired = 0;
        for (var t = 0; t < steps; t++)
        {
            var due = new List<int>();
            for (var i = 0; i < _bombFuse.Count; i++)
            {
                _bombFuse[i] = _bombFuse[i] - 1;
            }
            for (var i = _bombFuse.Count - 1; i >= 0; i--)
            {
                if (_bombFuse[i] <= 0)
                {
                    due.Insert(0, i);
                }
            }
            if (due.Count == 0)
            {
                continue;
            }
            Detonate(due);
            fired++;
        }
        Recompute();
        ApplyBoard();
        UpdateHud();
        LastEvent = $"fuse steps={steps} fired={fired} detonations={Detonations} "
                    + $"blast={LastBlastCount} bricks={BricksRemaining} enemies={EnemiesAlive} "
                    + $"lives={Lives} over={GameOver}";
        return LastEvent;
    }

    private readonly List<int[]> applied = new List<int[]>();

    /// <summary>
    /// Detonates the bombs whose indices are given, then every bomb those blasts touch, and applies
    /// the blast to bricks, enemies and the player. The union of every cell in the chain, in
    /// generation order and without repeats, becomes <see cref="LastBlast"/>.
    /// </summary>
    private List<int[]> Detonate(List<int> seeds)
    {
        applied.Clear();
        var queue = new List<int[]>();
        foreach (var index in seeds)
        {
            queue.Add(new[] { _bombRow[index], _bombCol[index] });
        }
        foreach (var index in seeds)
        {
            LastBombRow = _bombRow[index];
            LastBombCol = _bombCol[index];
        }
        // remove the seed bombs from the live list
        for (var i = seeds.Count - 1; i >= 0; i--)
        {
            var index = seeds[i];
            _bombRow.RemoveAt(index);
            _bombCol.RemoveAt(index);
            _bombFuse.RemoveAt(index);
        }
        var seen = new HashSet<int>();
        var blob = new List<int>();
        var head = 0;
        while (head < queue.Count)
        {
            var bomb = queue[head];
            head++;
            foreach (var cell in BlastCells(bomb[0], bomb[1]))
            {
                var h = Idx(cell[0], cell[1]);
                if (seen.Add(h))
                {
                    blob.Add(h);
                    applied.Add(new[] { cell[0], cell[1] });
                }
                var other = BombAt(cell[0], cell[1]);
                if (other >= 0)
                {
                    queue.Add(new[] { _bombRow[other], _bombCol[other] });
                    _bombRow.RemoveAt(other);
                    _bombCol.RemoveAt(other);
                    _bombFuse.RemoveAt(other);
                }
            }
        }
        Detonations++;
        LastBlastCount = applied.Count;
        var sb = new StringBuilder();
        var hash = 17;
        foreach (var cell in applied)
        {
            if (sb.Length > 0)
            {
                sb.Append('|');
            }
            sb.Append(cell[0]).Append(',').Append(cell[1]);
            unchecked
            {
                hash = hash * 31 + (cell[0] * Cols + cell[1]);
            }
        }
        LastBlast = sb.ToString();
        BlastHash = hash;

        // bricks first: the brick that stops a spread is inside the blast cells
        foreach (var cell in applied)
        {
            var i = Idx(cell[0], cell[1]);
            if (_brick[i])
            {
                _brick[i] = false;
            }
        }
        // then the enemies the blast caught
        for (var i = _enemyRow.Count - 1; i >= 0; i--)
        {
            if (seen.Contains(Idx(_enemyRow[i], _enemyCol[i])))
            {
                _enemyRow.RemoveAt(i);
                _enemyCol.RemoveAt(i);
                EnemiesKilled++;
            }
        }
        // and the player, if the blast covers the cell the player is standing on
        if (seen.Contains(Idx(PlayerRow, PlayerCol)))
        {
            KillPlayer("blast");
        }
        return applied;
    }

    private void KillPlayer(string reason)
    {
        Lives--;
        Deaths++;
        Exploded = reason == "blast";
        DeadByEnemy = reason == "enemy";
        if (Lives <= 0)
        {
            GameOver = true;
        }
        else
        {
            PlayerRow = SpawnRow;
            PlayerCol = SpawnCol;
        }
        LastEvent = $"killed reason={reason} lives={Lives} deaths={Deaths} over={GameOver} "
                    + $"at={PlayerRow},{PlayerCol}";
    }

    /// <summary>Advances every live enemy by <paramref name="steps"/> deterministic steps.</summary>
    public string StepEnemies(int steps)
    {
        var moved = 0;
        for (var t = 0; t < steps; t++)
        {
            if (GameOver)
            {
                break;
            }
            for (var i = 0; i < _enemyRow.Count; i++)
            {
                if (StepEnemy(i))
                {
                    moved++;
                }
                if (GameOver)
                {
                    break;
                }
            }
        }
        Recompute();
        ApplyBoard();
        UpdateHud();
        LastEvent = $"enemies steps={steps} moved={moved} alive={EnemiesAlive} "
                    + $"list={EnemyList} player={PlayerRow},{PlayerCol} lives={Lives} over={GameOver}";
        return LastEvent;
    }

    /// <summary>
    /// One enemy's deterministic step: head for the player, preferring the axis with the larger gap,
    /// falling back to the other axis, and stay put when both are blocked.
    /// </summary>
    private bool StepEnemy(int index)
    {
        var row = _enemyRow[index];
        var col = _enemyCol[index];
        var dr = PlayerRow - row;
        var dc = PlayerCol - col;
        var sr = dr == 0 ? 0 : (dr > 0 ? 1 : -1);
        var sc = dc == 0 ? 0 : (dc > 0 ? 1 : -1);
        var tryVerticalFirst = Mathf.Abs(dr) >= Mathf.Abs(dc);
        var first = tryVerticalFirst ? new[] { sr, 0 } : new[] { 0, sc };
        var second = tryVerticalFirst ? new[] { 0, sc } : new[] { sr, 0 };
        foreach (var d in new[] { first, second })
        {
            if (d[0] == 0 && d[1] == 0)
            {
                continue;
            }
            var nr = row + d[0];
            var nc = col + d[1];
            if (IsWall(nr, nc) || IsBrick(nr, nc))
            {
                continue;
            }
            if (BombAt(nr, nc) >= 0)
            {
                continue;
            }
            if (EnemyAt(nr, nc) >= 0)
            {
                continue;
            }
            _enemyRow[index] = nr;
            _enemyCol[index] = nc;
            if (nr == PlayerRow && nc == PlayerCol)
            {
                KillPlayer("enemy");
            }
            return true;
        }
        return false;
    }

    /// <summary>One deterministic tick: the fuses advance one step, then the enemies do.</summary>
    public string StepTick(int ticks)
    {
        var appliedTicks = 0;
        for (var t = 0; t < ticks; t++)
        {
            if (GameOver)
            {
                break;
            }
            StepFuse(1);
            appliedTicks++;
            if (GameOver)
            {
                break;
            }
            StepEnemies(1);
        }
        Recompute();
        ApplyBoard();
        UpdateHud();
        LastHookSteps = appliedTicks;
        LastEvent = $"steptick ticks={ticks} applied={appliedTicks} fuse_steps={appliedTicks} "
                    + $"detonations={Detonations} bricks={BricksRemaining} enemies={EnemiesAlive} "
                    + $"lives={Lives} over={GameOver}";
        return LastEvent;
    }

    /// <summary>Records what is at one cell into the Probe* properties, so an assert can name it.</summary>
    public string ProbeCell(int row, int col)
    {
        ProbeRow = row;
        ProbeCol = col;
        if (!InBounds(row, col) || _wall[Idx(row, col)])
        {
            ProbeState = "wall";
        }
        else if (_brick[Idx(row, col)])
        {
            ProbeState = BombAt(row, col) >= 0 ? "brick_bomb" : "brick";
        }
        else if (BombAt(row, col) >= 0)
        {
            ProbeState = row == PlayerRow && col == PlayerCol ? "player_bomb" : "bomb";
        }
        else if (EnemyAt(row, col) >= 0)
        {
            ProbeState = "enemy";
        }
        else if (row == PlayerRow && col == PlayerCol)
        {
            ProbeState = "player";
        }
        else
        {
            ProbeState = "floor";
        }
        LastEvent = $"probe at={row},{col} state={ProbeState}";
        return LastEvent;
    }

    /// <summary>Ticks per second; 0 keeps the world still (the default).</summary>
    public string SetAutoClock(float perSecond)
    {
        AutoClock = perSecond;
        _autoAccum = 0.0f;
        LastAutoSteps = 0;
        LastEvent = $"auto_clock={AutoClock}";
        GD.Print($"BOMBERMAN_AUTO auto={AutoClock}");
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
        _prevBomb = false;
        LastEvent = $"poll_input={PollInput}";
        return LastEvent;
    }

    private void HandleInput()
    {
        var up = Input.IsActionPressed("bomb_up");
        var right = Input.IsActionPressed("bomb_right");
        var down = Input.IsActionPressed("bomb_down");
        var left = Input.IsActionPressed("bomb_left");
        var place = Input.IsActionPressed("bomb_place");
        // Press edges only: a key a scenario injected and never released performs exactly one action
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
        // TASK-140 §1.B.3: a REFUSED placement must leave a trace.  This guard used to drop
        // the key silently (`place && !_prevBomb && BombsActive < MaxBombs && BombAt(...) < 0`)
        // when the limit was reached or the cell already held a bomb: measured on the
        // TASK-140 pre-fix run, steps 5/7/9 were `accepted and nothing changed` with an EMPTY
        // state delta -- indistinguishable from an unwired key.  `PlaceBomb` already records
        // every refusal (RejectedMoves + the new RejectedPlaces), so the edge is handed to it
        // and the decision is the game's, not this guard's.
        if (place && !_prevBomb && !GameOver)
        {
            var placedBefore = BombsPlaced;
            PlaceBomb();
            if (BombsPlaced > placedBefore)
            {
                InputBombs++;
            }
        }
        _prevUp = up;
        _prevRight = right;
        _prevDown = down;
        _prevLeft = left;
        _prevBomb = place;
    }

    private bool DoInput(string dir)
    {
        var before = Moves;
        Move(dir);
        return Moves > before;
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
            var appliedTicks = 0;
            var guard = 0;
            while (_autoAccum >= 1.0f && guard < 8)
            {
                _autoAccum -= 1.0f;
                guard++;
                StepFuse(1);
                appliedTicks++;
                if (GameOver)
                {
                    break;
                }
                StepEnemies(1);
                if (GameOver)
                {
                    break;
                }
            }
            AutoTicks += appliedTicks;
            LastAutoSteps = appliedTicks;
        }
        else
        {
            LastAutoSteps = 0;
        }
    }

    /// <summary>The field as a readable one-liner plus every exported fact.</summary>
    public string Dump()
    {
        var sb = new StringBuilder();
        for (var r = 0; r < Rows; r++)
        {
            for (var c = 0; c < Cols; c++)
            {
                var i = Idx(r, c);
                if (_wall[i])
                {
                    sb.Append('#');
                }
                else if (r == PlayerRow && c == PlayerCol)
                {
                    sb.Append('@');
                }
                else if (EnemyAt(r, c) >= 0)
                {
                    sb.Append('E');
                }
                else if (BombAt(r, c) >= 0)
                {
                    sb.Append('o');
                }
                else if (_brick[i])
                {
                    sb.Append('B');
                }
                else
                {
                    sb.Append('.');
                }
            }
            if (r + 1 < Rows)
            {
                sb.Append('/');
            }
        }
        return $"level={LevelIndex} field={sb} cols={Cols} rows={Rows} range={BlastRange} "
               + $"fuse={FuseSteps} bricks_total={BricksTotal} bricks_left={BricksRemaining} "
               + $"bricks_destroyed={BricksDestroyed} grid_hash={GridHash} unit_hash={UnitHash} "
               + $"bombs_placed={BombsPlaced} bombs_active={BombsActive} bomb_list={BombList} "
               + $"bombs_visible={BombsVisible} bomb_min_contrast={BombMinContrast:F3} "
               + $"bomb_color={BombColor} bomb_color_due={BombColorDue} "
               + $"last_bomb={LastBombRow},{LastBombCol} last_blast={LastBlast} "
               + $"blast_count={LastBlastCount} blast_hash={BlastHash} detonations={Detonations} "
               + $"enemies_total={EnemiesTotal} enemies_alive={EnemiesAlive} "
               + $"enemies_killed={EnemiesKilled} enemy_list={EnemyList} lives={Lives} "
               + $"deaths={Deaths} score={Score} player={PlayerRow},{PlayerCol} moves={Moves} "
               + $"rejected={RejectedMoves} rejected_places={RejectedPlaces} "
               + $"exploded={Exploded} dead_by_enemy={DeadByEnemy} "
               + $"won={Won} over={GameOver} probe={ProbeRow},{ProbeCol}:{ProbeState} "
               + $"auto={AutoClock} auto_ticks={AutoTicks} last_auto={LastAutoSteps} "
               + $"last_hook={LastHookSteps} input_moves={InputMoves} input_bombs={InputBombs} "
               + $"elapsed={Elapsed:F3} ticks={Ticks} last={LastEvent}";
    }

    /// <summary>
    /// Writes the whole deterministic world in one call:
    /// <c>"level=N"</c> or <c>"level=&lt;rows separated by /&gt;"</c>, plus optional
    /// <c>;player=r,c</c>, <c>;bricks=r,c|r,c|-</c>, <c>;enemies=r,c|r,c|-</c>, <c>;bombs=r,c,fuse|...</c>
    /// and <c>;lives=N</c>.
    ///
    /// <para>The auto clock and input polling are switched OFF first, so a session's aim and the next
    /// readback are the same fact. A test that wants motion calls <see cref="SetAutoClock"/> or
    /// <see cref="StepTick"/> itself -- which is why "the blast covered these cells" can never be an
    /// accident of timing.</para>
    /// </summary>
    public string ForceTestState(string spec)
    {
        var levelArg = "";
        var playerArg = "";
        var bricksArg = "-";
        var enemiesArg = "-";
        var bombsArg = "-";
        var livesArg = "";
        foreach (var part in spec.Split(';'))
        {
            var kv = part.Split(new[] { '=' }, 2);
            if (kv.Length != 2)
            {
                continue;
            }
            switch (kv[0])
            {
                case "level":
                    levelArg = kv[1];
                    break;
                case "player":
                    playerArg = kv[1];
                    break;
                case "bricks":
                    bricksArg = kv[1];
                    break;
                case "enemies":
                    enemiesArg = kv[1];
                    break;
                case "bombs":
                    bombsArg = kv[1];
                    break;
                case "lives":
                    livesArg = kv[1];
                    break;
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
            CreateNodes();
            ResetCounters();
        }
        if (livesArg.Length > 0)
        {
            Lives = int.Parse(livesArg);
        }
        if (bricksArg != "-")
        {
            for (var i = 0; i < _brick.Length; i++)
            {
                _brick[i] = false;
            }
            if (bricksArg.Length > 0)
            {
                foreach (var cell in bricksArg.Split('|'))
                {
                    var p = cell.Split(',');
                    if (p.Length == 2 && InBounds(int.Parse(p[0]), int.Parse(p[1])))
                    {
                        _brick[Idx(int.Parse(p[0]), int.Parse(p[1]))] = true;
                    }
                }
            }
        }
        if (enemiesArg != "-")
        {
            _enemyRow.Clear();
            _enemyCol.Clear();
            if (enemiesArg.Length > 0)
            {
                foreach (var cell in enemiesArg.Split('|'))
                {
                    var p = cell.Split(',');
                    if (p.Length == 2)
                    {
                        _enemyRow.Add(int.Parse(p[0]));
                        _enemyCol.Add(int.Parse(p[1]));
                    }
                }
            }
        }
        if (bombsArg != "-")
        {
            _bombRow.Clear();
            _bombCol.Clear();
            _bombFuse.Clear();
            if (bombsArg.Length > 0)
            {
                foreach (var cell in bombsArg.Split('|'))
                {
                    var p = cell.Split(',');
                    if (p.Length == 3)
                    {
                        _bombRow.Add(int.Parse(p[0]));
                        _bombCol.Add(int.Parse(p[1]));
                        _bombFuse.Add(int.Parse(p[2]));
                    }
                }
            }
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
        // the remaining per-level counters
        var bricksTotal = 0;
        for (var i = 0; i < _brick.Length; i++)
        {
            if (_brick[i])
            {
                bricksTotal++;
            }
        }
        BricksTotal = bricksTotal;
        BricksRemaining = bricksTotal;
        BricksDestroyed = 0;
        EnemiesTotal = _enemyRow.Count;
        EnemiesAlive = _enemyRow.Count;
        EnemiesKilled = 0;
        BombsPlaced = _bombRow.Count;
        Moves = 0;
        RejectedMoves = 0;
        Deaths = 0;
        Exploded = false;
        DeadByEnemy = false;
        LastBlast = "";
        LastBlastCount = 0;
        BlastHash = 0;
        Detonations = 0;
        AutoClock = 0.0f;
        AutoTicks = 0;
        LastAutoSteps = 0;
        LastHookSteps = 0;
        _autoAccum = 0.0f;
        PollInput = false;
        InputMoves = 0;
        InputBombs = 0;
        Recompute();
        ApplyBoard();
        UpdateHud();
        LastEvent = $"forced level={LevelIndex} bricks={BricksRemaining} enemies={EnemiesAlive} "
                    + $"bombs={BombsActive} lives={Lives} player={PlayerRow},{PlayerCol} "
                    + $"over={GameOver} won={Won}";
        return LastEvent;
    }
}
