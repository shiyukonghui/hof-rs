using Godot;
using System.Collections.Generic;
using System.Text;

namespace platformer;

/// <summary>
/// Platformer -- the fourteenth C# game of the godot-mcp series (TASK-102, DECISIONS.md D138).
///
/// <para><b>Design rule</b> (inherited from the thirteen games before it): every fact the evidence
/// model needs is a real Godot property on the root node -- <see cref="PlayerX"/>, <see cref="PlayerY"/>,
/// <see cref="VelX"/>, <see cref="VelY"/>, <see cref="OnGround"/>, <see cref="Jumps"/>,
/// <see cref="AirJumps"/>, <see cref="Collected"/>, <see cref="Score"/>, <see cref="Lives"/>,
/// <see cref="Falls"/>, <see cref="Won"/>, <see cref="GameOver"/>, <see cref="MapHash"/>,
/// <see cref="X"/>, <see cref="Y"/>, <see cref="Moves"/>, <see cref="AutoTicks"/>, <see cref="Ticks"/>.
/// A session asserts these with <c>running_game_assert_node_state</c>; it never parses a log line.</para>
///
/// <para><b>INTEGER kinematics, on purpose.</b> The world is a 40x30 grid of 20-pixel tiles. One
/// fixed frame (1/60 s) is: <c>x += vx</c>, resolve the horizontal overlap, <c>vy += gravity</c>
/// (clamped to <see cref="MaxFall"/>), <c>y += vy</c>, resolve the vertical overlap. Every quantity
/// is an <c>int</c>, so a jump arc is an exact integer sequence -- not "about 47.3 pixels" -- and a
/// second implementation of the rules in Python can reproduce the landing cell frame for frame.
/// That is what makes "the parabola lands here" an independently checkable fact rather than a
/// tolerance.</para>
///
/// <para><b>Frame-rate independence (the F-1 lesson).</b> The auto clock is a FLOAT ACCUMULATOR
/// (<c>_autoAccum += delta * AutoClock</c>), never <c>(int)(delta * rate)</c>. Two producers, two
/// properties: <see cref="LastAutoSteps"/> is what the clock applied on the last frame and
/// <see cref="LastHookSteps"/> is what the last <see cref="StepFrames"/> CALL applied. 2048's r1 run
/// (TASK-100, defect G1) proved a single property read by both producers reads the wrong number.
/// <see cref="Elapsed"/> is a monotonic float second counter that is never truncated.</para>
///
/// <para><b>Rules.</b> <see cref="SetRun"/> sets the horizontal speed (+-<see cref="RunSpeed"/>);
/// <see cref="Jump"/> launches the player when they are on the ground, and again once in mid-air when
/// <see cref="DoubleJump"/> is on (the optional double jump). Solid tiles stop the player on every
/// side. Every collectible the player's box covers is taken and scores
/// <see cref="PointsPerGem"/>. Reaching the goal tile wins. Falling below the map costs a life and
/// respawns the player at the spawn tile; the last life ends the game.</para>
///
/// <para><b>All tiles are runtime-created.</b> <see cref="_Ready"/> builds one <c>ColorRect</c> per
/// solid tile, per collectible and for the goal plus the player; the scene file carries only the
/// three static nodes (Background, Hud, Status). That keeps the edited scene small, keeps it immune
/// to the D-3 duplicate-name trap, and makes "a node created at run time really is drawn" part of
/// this game's own evidence.</para>
/// </summary>
public partial class PlatformerGame : Node2D
{
    // --- the level catalogue (the default board is Levels[0]) ---------------------
    // The map, one character per tile, rows separated by '/':
    //   '#' solid   '.' empty   'C' collectible   'G' goal   '@' spawn
    // `make_session_platformer.py` writes these two literals (see the marker comments) so the
    // Python re-implementation and the payload can never disagree about the level data.
    private static readonly string[] Levels =
    {
        // LEVEL0: the full course -- a ground with two pits, four floating platforms,
        // collectibles above each of them, and the goal on the ground at the far right.
        "......................................../......................................../......................................../......................................../......................................../......................................../......................................../......................................../......................................../...............................C.C.C..../..............................#######.../......................................../......................................../.......................C.C.C............/......................#######.........../......................................../......................................../...............C.C.C..................../..............########................../......................................../......................................../.......C.C............................../......######............................/......................................../......................................../......................................../......................................../..@.................C....C....C.......G./############...##################....###/############...##################....###",
        // LEVEL1: a flat strip for the pure-physics tests -- no pits, no goal in reach.
        "......................................../......................................../......................................../......................................../......................................../......................................../......................................../......................................../......................................../......................................../......................................../......................................../......................................../......................................../......................................../......................................../......................................../......................................../......................................../......................................../......................................../......................................../......................................../......................................../......................................../......................................../......................................../..@...................................../########################################/########################################",
    };

    // --- the grid ---------------------------------------------------------------
    /// <summary>Columns of the map.</summary>
    [Export] public int Cols = 0;

    /// <summary>Rows of the map.</summary>
    [Export] public int Rows = 0;

    /// <summary>Size of one tile in pixels.</summary>
    [Export] public int Tile = 20;

    /// <summary>Index of the level currently loaded.</summary>
    [Export] public int LevelIndex = 0;

    /// <summary>The map string currently loaded, rows separated by '/'.</summary>
    [Export] public string LevelSpec = "";

    // --- the physics constants, all of them integer ------------------------------
    /// <summary>Width of the player's box in pixels.</summary>
    [Export] public int PlayerW = 16;

    /// <summary>Height of the player's box in pixels.</summary>
    [Export] public int PlayerH = 16;

    /// <summary>Pixels per frame the player runs when a direction is held.</summary>
    [Export] public int RunSpeed = 4;

    /// <summary>Pixels per frame the vertical velocity gains each frame.</summary>
    [Export] public int Gravity = 1;

    /// <summary>Terminal downward speed, in pixels per frame.</summary>
    [Export] public int MaxFall = 16;

    /// <summary>Upward speed the ground jump starts with.</summary>
    [Export] public int JumpVel = 12;

    /// <summary>Upward speed the mid-air (second) jump starts with.</summary>
    [Export] public int AirJumpVel = 10;

    /// <summary>Whether the optional second, mid-air jump is enabled.</summary>
    [Export] public bool DoubleJump = true;

    /// <summary>Points one collectible is worth.</summary>
    [Export] public int PointsPerGem = 10;

    /// <summary>Lives the player starts with.</summary>
    [Export] public int LivesPerGame = 3;

    // --- observable state, all of it a real Godot property ----------------------
    /// <summary>Spawn tile row, read from the map's '@'.</summary>
    [Export] public int SpawnRow = 0;

    /// <summary>Spawn tile column.</summary>
    [Export] public int SpawnCol = 0;

    /// <summary>Spawn pixel X (top-left of the player's box).</summary>
    [Export] public int SpawnX = 0;

    /// <summary>Spawn pixel Y.</summary>
    [Export] public int SpawnY = 0;

    /// <summary>Goal tile row, read from the map's 'G'.</summary>
    [Export] public int GoalRow = -1;

    /// <summary>Goal tile column.</summary>
    [Export] public int GoalCol = -1;

    /// <summary>Left edge of the player's box, in pixels.</summary>
    [Export] public int PlayerX = 0;

    /// <summary>Top edge of the player's box, in pixels.</summary>
    [Export] public int PlayerY = 0;

    /// <summary>Horizontal speed in pixels per frame: -RunSpeed, 0, or +RunSpeed.</summary>
    [Export] public int VelX = 0;

    /// <summary>Vertical speed in pixels per frame; positive is downward.</summary>
    [Export] public int VelY = 0;

    /// <summary>The direction the player last faced: -1, 0, or 1.</summary>
    [Export] public int Facing = 1;

    /// <summary>True when the last frame ended standing on a solid tile.</summary>
    [Export] public bool OnGround = false;

    /// <summary>Frames since the level was pinned (a monotonic frame counter).</summary>
    [Export] public int Frames = 0;

    /// <summary>Jumps started: ground jumps plus accepted mid-air jumps.</summary>
    [Export] public int Jumps = 0;

    /// <summary>Mid-air (second) jumps accepted.</summary>
    [Export] public int AirJumps = 0;

    /// <summary>Jumps refused because the player was already in the air with no air jump left.</summary>
    [Export] public int JumpsRejected = 0;

    /// <summary>Times a horizontal move was stopped by a solid tile.</summary>
    [Export] public int WallHits = 0;

    /// <summary>Times a vertical move ended on a solid tile (a landing or a ceiling stop).</summary>
    [Export] public int Landings = 0;

    /// <summary>Collectibles the level started with.</summary>
    [Export] public int GemsTotal = 0;

    /// <summary>Collectibles taken so far.</summary>
    [Export] public int Collected = 0;

    /// <summary>Collectibles still in the map.</summary>
    [Export] public int GemsRemaining = 0;

    /// <summary>Points: PointsPerGem per collectible.</summary>
    [Export] public int Score = 0;

    /// <summary>A stable hash of the whole map (solid / empty / collectible / goal).</summary>
    [Export] public int MapHash = 0;

    /// <summary>A stable hash of the player's kinematic state, so "a different jump" is checkable.</summary>
    [Export] public int StateHash = 0;

    /// <summary>Lives left.</summary>
    [Export] public int Lives = 3;

    /// <summary>Times the player fell below the map.</summary>
    [Export] public int Falls = 0;

    /// <summary>True when the goal tile was reached.</summary>
    [Export] public bool Won = false;

    /// <summary>True when the level ended, by the goal or by the last life.</summary>
    [Export] public bool GameOver = false;

    /// <summary>Row the last <see cref="ProbeCell"/> looked at.</summary>
    [Export] public int ProbeRow = -1;

    /// <summary>Column the last <see cref="ProbeCell"/> looked at.</summary>
    [Export] public int ProbeCol = -1;

    /// <summary>Probed tile state: solid / empty / gem / goal / spawn / player.</summary>
    [Export] public string ProbeState = "";

    /// <summary>Probed tile value, -1 for empty.</summary>
    [Export] public int ProbeValue = -1;

    /// <summary>Seconds since the last reset: a monotonic FLOAT accumulator, never truncated.</summary>
    [Export] public float Elapsed = 0.0f;

    /// <summary>Fixed frames per second; 0 keeps the world still (the default).</summary>
    [Export] public float AutoClock = 0.0f;

    /// <summary>Frames the auto clock has applied over the whole level.</summary>
    [Export] public int AutoTicks = 0;

    /// <summary>Frames the auto clock applied on the LAST frame (0 while the clock is off).</summary>
    [Export] public int LastAutoSteps = 0;

    /// <summary>
    /// Frames the LAST <see cref="StepFrames"/> CALL applied. Its own property, and the clock never
    /// writes it: 2048's r1 run (TASK-100, defect G1) found that one property used by two producers
    /// reads 0 by the time the assertion runs, because the next frame's clock pass overwrites it.
    /// Two producers, two properties.
    /// </summary>
    [Export] public int LastHookSteps = 0;

    /// <summary>When false the map ignores input (determinism rule: no polling by default).</summary>
    [Export] public bool PollInput = false;

    /// <summary>Horizontal directions that arrived through the declared input actions.</summary>
    [Export] public int InputMoves = 0;

    /// <summary>Jumps that arrived through the declared input actions.</summary>
    [Export] public int InputJumps = 0;

    /// <summary>Frames processed since the last reset.</summary>
    [Export] public int Ticks = 0;

    /// <summary>What the last hook did -- the readback string a session quotes.</summary>
    [Export] public string LastEvent = "";

    // --- private model ---------------------------------------------------------
    private bool[] _solid = new bool[1];
    private bool[] _gem = new bool[1];
    private bool[] _goal = new bool[1];
    private readonly List<ColorRect> _solidRect = new List<ColorRect>();
    private readonly List<ColorRect> _gemRect = new List<ColorRect>();
    private ColorRect _goalRect;
    private ColorRect _playerRect;
    private Label _hud;
    private Label _status;
    private float _autoAccum;
    private bool _prevLeft;
    private bool _prevRight;
    private bool _prevJump;

    private int Idx(int row, int col)
    {
        return row * Cols + col;
    }

    private bool InBounds(int row, int col)
    {
        return row >= 0 && row < Rows && col >= 0 && col < Cols;
    }

    private bool IsSolid(int row, int col)
    {
        return !InBounds(row, col) || _solid[Idx(row, col)];
    }

    public override void _Ready()
    {
        _hud = GetNodeOrNull<Label>("Hud");
        _status = GetNodeOrNull<Label>("Status");
        LoadLevel(LevelIndex);
        GD.Print($"PLATFORMER_READY level={LevelIndex} cols={Cols} rows={Rows} tile={Tile} "
                 + $"gems={GemsTotal} lives={Lives} run={RunSpeed} g={Gravity} jump={JumpVel} "
                 + $"air={AirJumpVel} double={DoubleJump} auto={AutoClock} poll={PollInput}");
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
        _solid = new bool[total];
        _gem = new bool[total];
        _goal = new bool[total];
        SpawnRow = 0;
        SpawnCol = 0;
        GoalRow = -1;
        GoalCol = -1;
        for (var r = 0; r < Rows; r++)
        {
            var line = raw[r];
            for (var c = 0; c < Cols; c++)
            {
                var ch = c < line.Length ? line[c] : '.';
                var i = Idx(r, c);
                switch (ch)
                {
                    case '#':
                        _solid[i] = true;
                        break;
                    case 'C':
                        _gem[i] = true;
                        break;
                    case 'G':
                        _goal[i] = true;
                        GoalRow = r;
                        GoalCol = c;
                        break;
                    case '@':
                        SpawnRow = r;
                        SpawnCol = c;
                        break;
                }
            }
        }
        SpawnX = SpawnCol * Tile + (Tile - PlayerW) / 2;
        SpawnY = SpawnRow * Tile + (Tile - PlayerH) / 2;
    }

    private void ResetCounters()
    {
        GemsTotal = 0;
        for (var i = 0; i < _gem.Length; i++)
        {
            if (_gem[i])
            {
                GemsTotal++;
            }
        }
        GemsRemaining = GemsTotal;
        Collected = 0;
        Score = 0;
        MapHash = 0;
        StateHash = 0;
        Lives = LivesPerGame;
        Falls = 0;
        Won = false;
        GameOver = false;
        Jumps = 0;
        AirJumps = 0;
        JumpsRejected = 0;
        WallHits = 0;
        Landings = 0;
        Frames = 0;
        ProbeRow = -1;
        ProbeCol = -1;
        ProbeState = "";
        ProbeValue = -1;
        PlayerX = SpawnX;
        PlayerY = SpawnY;
        VelX = 0;
        VelY = 0;
        Facing = 1;
        OnGround = false;
        AutoClock = 0.0f;
        AutoTicks = 0;
        LastAutoSteps = 0;
        LastHookSteps = 0;
        _autoAccum = 0.0f;
        PollInput = false;
        InputMoves = 0;
        InputJumps = 0;
        _prevLeft = false;
        _prevRight = false;
        _prevJump = false;
        Ticks = 0;
    }

    // --- rendering --------------------------------------------------------------
    private void CreateNodes()
    {
        // RemoveChild BEFORE QueueFree: a node queued for deletion still holds its name for the rest
        // of the frame, and re-adding a child with the same name makes the engine rename the new one
        // to "@ColorRect@N" (the Pac-Man lesson from TASK-098, the same trap D-3 was about).
        foreach (var rect in _solidRect)
        {
            if (rect != null && IsInstanceValid(rect))
            {
                RemoveChild(rect);
                rect.QueueFree();
            }
        }
        foreach (var rect in _gemRect)
        {
            if (rect != null && IsInstanceValid(rect))
            {
                RemoveChild(rect);
                rect.QueueFree();
            }
        }
        if (_goalRect != null && IsInstanceValid(_goalRect))
        {
            RemoveChild(_goalRect);
            _goalRect.QueueFree();
        }
        if (_playerRect != null && IsInstanceValid(_playerRect))
        {
            RemoveChild(_playerRect);
            _playerRect.QueueFree();
        }
        _solidRect.Clear();
        _gemRect.Clear();
        for (var r = 0; r < Rows; r++)
        {
            for (var c = 0; c < Cols; c++)
            {
                if (!_solid[Idx(r, c)])
                {
                    continue;
                }
                var rect = new ColorRect();
                rect.Name = $"Tile_{r}_{c}";
                rect.Position = new Vector2(c * Tile, r * Tile);
                rect.Size = new Vector2(Tile, Tile);
                rect.Color = new Color(0.30f, 0.34f, 0.42f);
                AddChild(rect);
                _solidRect.Add(rect);
            }
        }
        for (var r = 0; r < Rows; r++)
        {
            for (var c = 0; c < Cols; c++)
            {
                if (!_gem[Idx(r, c)])
                {
                    continue;
                }
                var rect = new ColorRect();
                rect.Name = $"Gem_{r}_{c}";
                rect.Position = new Vector2(c * Tile + 5, r * Tile + 5);
                rect.Size = new Vector2(Tile - 10, Tile - 10);
                rect.Color = new Color(0.98f, 0.78f, 0.22f);
                AddChild(rect);
                _gemRect.Add(rect);
            }
        }
        _goalRect = new ColorRect();
        _goalRect.Name = "Goal";
        _goalRect.Size = new Vector2(Tile - 4, Tile - 4);
        _goalRect.Color = new Color(0.20f, 0.85f, 0.45f);
        AddChild(_goalRect);
        _playerRect = new ColorRect();
        _playerRect.Name = "PlayerSprite";
        _playerRect.Size = new Vector2(PlayerW, PlayerH);
        _playerRect.Color = new Color(0.35f, 0.72f, 1.00f);
        AddChild(_playerRect);
    }

    private void ApplyBoard()
    {
        var index = 0;
        for (var r = 0; r < Rows; r++)
        {
            for (var c = 0; c < Cols; c++)
            {
                if (!_solid[Idx(r, c)])
                {
                    continue;
                }
                if (index < _solidRect.Count)
                {
                    var rect = _solidRect[index];
                    if (rect != null && IsInstanceValid(rect))
                    {
                        rect.Position = new Vector2(c * Tile, r * Tile);
                        rect.Visible = true;
                    }
                }
                index++;
            }
        }
        var gemIndex = 0;
        for (var r = 0; r < Rows; r++)
        {
            for (var c = 0; c < Cols; c++)
            {
                if (!_gem[Idx(r, c)])
                {
                    continue;
                }
                if (gemIndex < _gemRect.Count)
                {
                    var rect = _gemRect[gemIndex];
                    if (rect != null && IsInstanceValid(rect))
                    {
                        rect.Position = new Vector2(c * Tile + 5, r * Tile + 5);
                        rect.Visible = true;
                    }
                }
                gemIndex++;
            }
        }
        if (_goalRect != null && IsInstanceValid(_goalRect))
        {
            if (GoalRow >= 0)
            {
                _goalRect.Position = new Vector2(GoalCol * Tile + 2, GoalRow * Tile + 2);
                _goalRect.Visible = true;
            }
            else
            {
                _goalRect.Visible = false;
            }
        }
        if (_playerRect != null && IsInstanceValid(_playerRect))
        {
            _playerRect.Position = new Vector2(PlayerX, PlayerY);
        }
    }

    private void UpdateHud()
    {
        if (_hud != null)
        {
            _hud.Text = $"GEMS {Collected}/{GemsTotal}  SCORE {Score}  LIVES {Lives}  "
                        + $"AIR {AirJumps}  TILE {PlayerX / Tile},{PlayerY / Tile}";
        }
        if (_status != null)
        {
            if (Won)
            {
                _status.Text = "GOAL REACHED";
            }
            else if (GameOver)
            {
                _status.Text = "ALL LIVES LOST";
            }
            else
            {
                _status.Text = "RUN AND JUMP";
            }
        }
    }

    // --- the fixed frame --------------------------------------------------------
    private bool BoxOverlapsSolid(int x, int y)
    {
        // The world walls are the left edge, the right edge and the ceiling. There is deliberately
        // NO floor: below the last map row is open air, which is exactly what makes a pit a pit
        // instead of a ledge the player could stand on.
        if (x < 0 || y < 0)
        {
            return true;
        }
        if (x + PlayerW > Cols * Tile)
        {
            return true;
        }
        var c0 = x / Tile;
        var c1 = (x + PlayerW - 1) / Tile;
        var r0 = y / Tile;
        var r1 = (y + PlayerH - 1) / Tile;
        for (var r = r0; r <= r1; r++)
        {
            for (var c = c0; c <= c1; c++)
            {
                if (OutOfMapSolid(r, c))
                {
                    return true;
                }
            }
        }
        return false;
    }

    private bool OutOfMapSolid(int r, int c)
    {
        if (r < 0)
        {
            return true;
        }
        if (c < 0 || c >= Cols)
        {
            return true;
        }
        if (r >= Rows)
        {
            return false; // open air below the map: the pit
        }
        return _solid[Idx(r, c)];
    }

    private void ResolveHorizontal()
    {
        if (!BoxOverlapsSolid(PlayerX, PlayerY))
        {
            return;
        }
        if (VelX > 0)
        {
            PlayerX = ((PlayerX + PlayerW - 1) / Tile) * Tile - PlayerW;
        }
        else if (VelX < 0)
        {
            PlayerX = (PlayerX / Tile + 1) * Tile;
        }
        else
        {
            PlayerX = SpawnX;
        }
        VelX = 0;
        WallHits++;
    }

    private void ResolveVertical()
    {
        if (!BoxOverlapsSolid(PlayerX, PlayerY))
        {
            return;
        }
        if (VelY > 0)
        {
            PlayerY = ((PlayerY + PlayerH - 1) / Tile) * Tile - PlayerH;
            OnGround = true;
        }
        else if (VelY < 0)
        {
            PlayerY = (PlayerY / Tile + 1) * Tile;
        }
        VelY = 0;
        Landings++;
    }

    private void CheckPickups()
    {
        var c0 = PlayerX / Tile;
        var c1 = (PlayerX + PlayerW - 1) / Tile;
        var r0 = PlayerY / Tile;
        var r1 = (PlayerY + PlayerH - 1) / Tile;
        for (var r = r0; r <= r1; r++)
        {
            for (var c = c0; c <= c1; c++)
            {
                if (!InBounds(r, c))
                {
                    continue;
                }
                var i = Idx(r, c);
                if (_gem[i])
                {
                    _gem[i] = false;
                    Collected++;
                    Score += PointsPerGem;
                    LastEvent = $"gem at={r},{c} collected={Collected} score={Score}";
                }
                if (_goal[i])
                {
                    Won = true;
                    GameOver = true;
                    LastEvent = $"goal at={r},{c} reached=true score={Score}";
                }
            }
        }
    }

    private void Fall()
    {
        Falls++;
        Lives--;
        if (Lives <= 0)
        {
            GameOver = true;
            Won = false;
            LastEvent = $"fell lives=0 falls={Falls} over=true";
            return;
        }
        PlayerX = SpawnX;
        PlayerY = SpawnY;
        VelX = 0;
        VelY = 0;
        OnGround = false;
        LastEvent = $"fell lives={Lives} falls={Falls} respawn={PlayerX},{PlayerY}";
    }

    /// <summary>One fixed frame of the whole world. Pure integer arithmetic.</summary>
    private void Frame()
    {
        // NOTE: Ticks belongs to `_Process` alone. Two producers, two properties: Frames counts the
        // fixed frames this hook/clock applied, Ticks counts the engine frames that were processed.
        // (TASK-100's G1 was exactly one property written by two producers.)
        if (GameOver)
        {
            return;
        }
        Frames++;
        // 1. horizontal
        PlayerX += VelX;
        ResolveHorizontal();
        // 2. vertical
        VelY += Gravity;
        if (VelY > MaxFall)
        {
            VelY = MaxFall;
        }
        PlayerY += VelY;
        OnGround = false;
        ResolveVertical();
        // 3. pickups, the goal, and the pit
        CheckPickups();
        if (PlayerY > Rows * Tile)
        {
            Fall();
        }
        Recompute();
        ApplyBoard();
        UpdateHud();
    }

    private void Recompute()
    {
        var hash = 17;
        var gems = 0;
        unchecked
        {
            for (var r = 0; r < Rows; r++)
            {
                for (var c = 0; c < Cols; c++)
                {
                    var i = Idx(r, c);
                    var code = _solid[i] ? 1 : (_goal[i] ? 5 : (_gem[i] ? 3 : 2));
                    hash = hash * 31 + code;
                }
            }
            var sh = 17;
            sh = sh * 31 + PlayerX;
            sh = sh * 31 + PlayerY;
            sh = sh * 31 + VelX;
            sh = sh * 31 + VelY;
            sh = sh * 31 + (OnGround ? 1 : 0);
            StateHash = sh;
        }
        MapHash = hash;
        for (var i = 0; i < _gem.Length; i++)
        {
            if (_gem[i])
            {
                gems++;
            }
        }
        GemsRemaining = gems;
        Collected = GemsTotal - gems;
        Score = Collected * PointsPerGem;
    }

    // --- hooks the session drives ----------------------------------------------

    /// <summary>Sets the running direction: -1 left, 0 stop, +1 right.</summary>
    public string SetRun(int dir)
    {
        if (GameOver)
        {
            LastEvent = $"rejected reason=game_over run={dir} won={Won} lives={Lives}";
            return LastEvent;
        }
        var d = dir < 0 ? -1 : (dir > 0 ? 1 : 0);
        VelX = d * RunSpeed;
        if (d != 0)
        {
            Facing = d;
        }
        LastEvent = $"run dir={d} vx={VelX} x={PlayerX} y={PlayerY}";
        return LastEvent;
    }

    /// <summary>
    /// Jumps: a ground jump whenever the player is standing on something, and one more mid-air jump
    /// while <see cref="DoubleJump"/> is on. Anything else is refused and counted.
    /// </summary>
    public string Jump()
    {
        if (GameOver)
        {
            JumpsRejected++;
            LastEvent = $"rejected reason=game_over jumps={Jumps} rejected={JumpsRejected}";
            return LastEvent;
        }
        if (OnGround)
        {
            VelY = -JumpVel;
            Jumps++;
            LastEvent = $"jumped kind=ground vy={VelY} jumps={Jumps} y={PlayerY}";
            return LastEvent;
        }
        if (DoubleJump && AirJumps < 1)
        {
            VelY = -AirJumpVel;
            AirJumps++;
            Jumps++;
            LastEvent = $"jumped kind=air vy={VelY} jumps={Jumps} air={AirJumps} y={PlayerY}";
            return LastEvent;
        }
        JumpsRejected++;
        LastEvent = $"rejected reason=no_jump_left on_ground={OnGround} air={AirJumps} "
                    + $"rejected={JumpsRejected}";
        return LastEvent;
    }

    /// <summary>Applies <paramref name="steps"/> fixed frames. The frame-rate independent hook.</summary>
    public string StepFrames(int steps)
    {
        var applied = 0;
        for (var t = 0; t < steps; t++)
        {
            if (GameOver)
            {
                break;
            }
            Frame();
            applied++;
        }
        LastHookSteps = applied;
        LastEvent = $"stepframes requested={steps} applied={applied} x={PlayerX} y={PlayerY} "
                    + $"vy={VelY} ground={OnGround} gems={Collected} lives={Lives} over={GameOver}";
        return LastEvent;
    }

    /// <summary>Records what is at one tile into the Probe* properties, so an assert can name it.</summary>
    public string ProbeCell(int row, int col)
    {
        ProbeRow = row;
        ProbeCol = col;
        ProbeValue = -1;
        if (!InBounds(row, col) || _solid[Idx(row, col)])
        {
            ProbeState = "solid";
        }
        else if (row == PlayerY / Tile && col == PlayerX / Tile)
        {
            ProbeState = "player";
        }
        else if (_goal[Idx(row, col)])
        {
            ProbeState = "goal";
        }
        else if (_gem[Idx(row, col)])
        {
            ProbeState = "gem";
            ProbeValue = 1;
        }
        else if (row == SpawnRow && col == SpawnCol)
        {
            ProbeState = "spawn";
        }
        else
        {
            ProbeState = "empty";
        }
        LastEvent = $"probe at={row},{col} state={ProbeState}";
        return LastEvent;
    }

    /// <summary>Switches the optional mid-air jump on or off.</summary>
    public string SetDoubleJump(bool enabled)
    {
        DoubleJump = enabled;
        LastEvent = $"double_jump={DoubleJump}";
        return LastEvent;
    }

    /// <summary>Frames per second; 0 keeps the world still (the default).</summary>
    public string SetAutoClock(float perSecond)
    {
        AutoClock = perSecond;
        _autoAccum = 0.0f;
        LastAutoSteps = 0;
        LastEvent = $"auto_clock={AutoClock}";
        GD.Print($"PLATFORMER_AUTO auto={AutoClock}");
        return LastEvent;
    }

    /// <summary>Switches the declared-input polling on or off (the default is off).</summary>
    public string SetPollInput(bool enabled)
    {
        PollInput = enabled;
        _prevLeft = false;
        _prevRight = false;
        _prevJump = false;
        LastEvent = $"poll_input={PollInput}";
        return LastEvent;
    }

    private void HandleInput()
    {
        var left = Input.IsActionPressed("plat_left");
        var right = Input.IsActionPressed("plat_right");
        var jump = Input.IsActionPressed("plat_jump");
        // Press edges only: a key a scenario injected and never released performs exactly one action
        // instead of repeating at the frame rate.
        if (left && !_prevLeft && !GameOver)
        {
            SetRun(-1);
            InputMoves++;
        }
        if (right && !_prevRight && !GameOver)
        {
            SetRun(1);
            InputMoves++;
        }
        if (jump && !_prevJump && !GameOver)
        {
            Jump();
            InputJumps++;
        }
        _prevLeft = left;
        _prevRight = right;
        _prevJump = jump;
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
                Frame();
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

    /// <summary>The map as a readable one-liner plus every exported fact.</summary>
    public string Dump()
    {
        var sb = new StringBuilder();
        for (var r = 0; r < Rows; r++)
        {
            for (var c = 0; c < Cols; c++)
            {
                var i = Idx(r, c);
                if (r == PlayerY / Tile && c == PlayerX / Tile && !GameOver)
                {
                    sb.Append('@');
                }
                else if (_solid[i])
                {
                    sb.Append('#');
                }
                else if (_goal[i])
                {
                    sb.Append('G');
                }
                else if (_gem[i])
                {
                    sb.Append('C');
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
        return $"level={LevelIndex} map={sb} cols={Cols} rows={Rows} tile={Tile} "
               + $"gems_total={GemsTotal} gems_left={GemsRemaining} collected={Collected} "
               + $"score={Score} map_hash={MapHash} player={PlayerX},{PlayerY} vel={VelX},{VelY} "
               + $"on_ground={OnGround} facing={Facing} frames={Frames} jumps={Jumps} "
               + $"air_jumps={AirJumps} jumps_rejected={JumpsRejected} wall_hits={WallHits} "
               + $"landings={Landings} state_hash={StateHash} spawn={SpawnX},{SpawnY} "
               + $"spawn_tile={SpawnRow},{SpawnCol} goal_tile={GoalRow},{GoalCol} lives={Lives} "
               + $"falls={Falls} won={Won} over={GameOver} probe={ProbeRow},{ProbeCol}:{ProbeState} "
               + $"double={DoubleJump} auto={AutoClock} auto_ticks={AutoTicks} "
               + $"last_auto={LastAutoSteps} last_hook={LastHookSteps} input_moves={InputMoves} "
               + $"input_jumps={InputJumps} elapsed={Elapsed:F3} ticks={Ticks} last={LastEvent}";
    }

    /// <summary>
    /// Writes the whole deterministic world in one call:
    /// <c>"level=N"</c> or <c>"level=&lt;rows separated by /&gt;"</c>, plus optional
    /// <c>;player=x,y</c> (pixels), <c>;gems=r,c|r,c|-</c>, <c>;goal=r,c</c>, <c>;lives=N</c>,
    /// <c>;vel=vx,vy</c> and <c>;ground=0|1</c>.
    ///
    /// <para>The auto clock and input polling are switched OFF first, so a session's aim and the next
    /// readback are the same fact. A test that wants motion calls <see cref="SetAutoClock"/> or
    /// <see cref="StepFrames"/> itself -- which is why "the parabola lands on this tile in this
    /// frame" can never be an accident of timing.</para>
    /// </summary>
    public string ForceTestState(string spec)
    {
        var levelArg = "";
        var playerArg = "";
        var gemsArg = "-";
        var goalArg = "";
        var livesArg = "";
        var velArg = "";
        var groundArg = "";
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
                case "gems":
                    gemsArg = kv[1];
                    break;
                case "goal":
                    goalArg = kv[1];
                    break;
                case "lives":
                    livesArg = kv[1];
                    break;
                case "vel":
                    velArg = kv[1];
                    break;
                case "ground":
                    groundArg = kv[1];
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
        if (gemsArg != "-")
        {
            for (var i = 0; i < _gem.Length; i++)
            {
                _gem[i] = false;
            }
            if (gemsArg.Length > 0)
            {
                foreach (var cell in gemsArg.Split('|'))
                {
                    var p = cell.Split(',');
                    if (p.Length == 2 && InBounds(int.Parse(p[0]), int.Parse(p[1])))
                    {
                        _gem[Idx(int.Parse(p[0]), int.Parse(p[1]))] = true;
                    }
                }
            }
        }
        if (goalArg.Length > 0)
        {
            for (var i = 0; i < _goal.Length; i++)
            {
                _goal[i] = false;
            }
            var p = goalArg.Split(',');
            if (p.Length == 2 && InBounds(int.Parse(p[0]), int.Parse(p[1])))
            {
                _goal[Idx(int.Parse(p[0]), int.Parse(p[1]))] = true;
                GoalRow = int.Parse(p[0]);
                GoalCol = int.Parse(p[1]);
            }
            else
            {
                GoalRow = -1;
                GoalCol = -1;
            }
        }
        if (playerArg.Length > 0)
        {
            var p = playerArg.Split(',');
            if (p.Length == 2)
            {
                PlayerX = int.Parse(p[0]);
                PlayerY = int.Parse(p[1]);
            }
        }
        if (velArg.Length > 0)
        {
            var p = velArg.Split(',');
            if (p.Length == 2)
            {
                VelX = int.Parse(p[0]);
                VelY = int.Parse(p[1]);
            }
        }
        if (groundArg.Length > 0)
        {
            OnGround = groundArg == "1";
        }
        var gemsTotal = 0;
        for (var i = 0; i < _gem.Length; i++)
        {
            if (_gem[i])
            {
                gemsTotal++;
            }
        }
        GemsTotal = gemsTotal;
        GemsRemaining = gemsTotal;
        Collected = 0;
        Score = 0;
        Falls = 0;
        Won = false;
        GameOver = false;
        Jumps = 0;
        AirJumps = 0;
        JumpsRejected = 0;
        WallHits = 0;
        Landings = 0;
        Frames = 0;
        AutoClock = 0.0f;
        AutoTicks = 0;
        LastAutoSteps = 0;
        LastHookSteps = 0;
        _autoAccum = 0.0f;
        PollInput = false;
        InputMoves = 0;
        InputJumps = 0;
        _prevLeft = false;
        _prevRight = false;
        _prevJump = false;
        Recompute();
        ApplyBoard();
        UpdateHud();
        LastEvent = $"forced level={LevelIndex} gems={GemsRemaining} lives={Lives} "
                    + $"player={PlayerX},{PlayerY} vel={VelX},{VelY} ground={OnGround} "
                    + $"over={GameOver} won={Won}";
        return LastEvent;
    }
}
