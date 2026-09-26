using Godot;
using System.Text;

namespace spaceinvaders;

/// <summary>
/// Space Invaders — the fifth C# game of the godot-mcp series (TASK-097, DECISIONS.md D138).
///
/// <para><b>Design rule</b> (inherited from Pong / Breakout / Snake / Tetris): every fact the
/// evidence model needs is a real Godot property on the root node — <see cref="Score"/>,
/// <see cref="InvadersRemaining"/>, <see cref="InvadersKilled"/>, <see cref="ShotsFired"/>,
/// <see cref="GameOver"/>, <see cref="Won"/>, <see cref="PlayerX"/>, <see cref="WaveX"/>,
/// <see cref="WaveY"/>, <see cref="WaveDir"/>, <see cref="WaveSteps"/>, <see cref="BulletX"/>,
/// <see cref="BulletY"/>, <see cref="BulletActive"/>, <see cref="Ticks"/>. A session asserts
/// these with <c>running_game_assert_node_state</c>; it never parses a log line.</para>
///
/// <para><b>Determinism rule.</b> Two things are OFF by default: the wave does not step on its
/// own (<see cref="StepInterval"/> = 0) and player input is not polled
/// (<see cref="PollInput"/> = false). A test switches each on explicitly with
/// <see cref="SetWaveSpeed"/> / <see cref="SetPollInput"/>, so a fact like "the bullet moved"
/// can never be timing noise and the startup window cannot change the board behind a session's
/// back. <see cref="ForceTestState"/> pins the whole state in one call.</para>
///
/// <para><b>The invader grid is runtime-created.</b> <see cref="_Ready"/> builds one ColorRect
/// per invader (<c>Invader_r{row}_c{col}</c>); the scene file carries only the five static
/// nodes (Background, Hud, Status, Player, Bullet). That keeps the edited scene small and makes
/// "a node created at run time really is drawn" part of this game's own evidence.</para>
///
/// <para><b>Scoring has exactly one source.</b> One invader killed = 10 points; nothing else
/// scores. An assertion about <see cref="Score"/> therefore names the kill that produced it.</para>
/// </summary>
public partial class SpaceInvadersGame : Node2D
{
    // --- geometry --------------------------------------------------------------
    /// <summary>Invader columns.</summary>
    [Export] public int Columns = 8;

    /// <summary>Invader rows.</summary>
    [Export] public int Rows = 5;

    /// <summary>Horizontal distance between two invader cells.</summary>
    [Export] public int CellW = 60;

    /// <summary>Vertical distance between two invader cells.</summary>
    [Export] public int CellH = 44;

    /// <summary>Invader width in pixels.</summary>
    [Export] public int InvaderW = 36;

    /// <summary>Invader height in pixels.</summary>
    [Export] public int InvaderH = 26;

    /// <summary>Left edge the wave may not cross.</summary>
    [Export] public int WaveMinX = 20;

    /// <summary>Right edge the wave may not cross.</summary>
    [Export] public int WaveMaxX = 324;

    /// <summary>Player row (top edge of the player rectangle).</summary>
    [Export] public int PlayerY = 520;

    /// <summary>Player width in pixels.</summary>
    [Export] public int PlayerW = 60;

    /// <summary>Player height in pixels.</summary>
    [Export] public int PlayerH = 18;

    /// <summary>Rows of the wave at or below this line end the game (invaders reached the player).</summary>
    [Export] public int DangerY = 560;

    /// <summary>How much one descent moves the wave down.</summary>
    [Export] public int DropStep = 22;

    // --- observable state, all of it a real Godot property ---------------------
    /// <summary>Points: 10 per invader killed.</summary>
    [Export] public int Score = 0;

    /// <summary>Invaders still alive.</summary>
    [Export] public int InvadersRemaining = 0;

    /// <summary>Invaders killed so far.</summary>
    [Export] public int InvadersKilled = 0;

    /// <summary>Bullets fired (the hook and the action both count).</summary>
    [Export] public int ShotsFired = 0;

    /// <summary>True when the wave is cleared (win) or has reached the player (loss).</summary>
    [Export] public bool GameOver = false;

    /// <summary>True when <see cref="GameOver"/> was reached by clearing the wave.</summary>
    [Export] public bool Won = false;

    /// <summary>Player left edge.</summary>
    [Export] public float PlayerX = 370.0f;

    /// <summary>Wave left edge.</summary>
    [Export] public int WaveX = 140;

    /// <summary>Wave top edge.</summary>
    [Export] public int WaveY = 90;

    /// <summary>+1 = the wave moves right, -1 = left.</summary>
    [Export] public int WaveDir = 1;

    /// <summary>Horizontal steps the wave has taken.</summary>
    [Export] public int WaveSteps = 0;

    /// <summary>Bullet left edge.</summary>
    [Export] public float BulletX = -100.0f;

    /// <summary>Bullet top edge.</summary>
    [Export] public float BulletY = -100.0f;

    /// <summary>True while a bullet is in flight (at most one at a time).</summary>
    [Export] public bool BulletActive = false;

    /// <summary>Bullet speed in pixels per second.</summary>
    [Export] public int BulletSpeed = 320;

    /// <summary>Player speed in pixels per second (input only).</summary>
    [Export] public float PlayerSpeed = 220.0f;

    /// <summary>Seconds per wave step; 0 = the wave never moves on its own (determinism rule).</summary>
    [Export] public float StepInterval = 0.0f;

    /// <summary>When false the player ignores input (determinism rule: no polling by default).</summary>
    [Export] public bool PollInput = false;

    /// <summary>Frames processed since the last reset.</summary>
    [Export] public int Ticks = 0;

    /// <summary>What the last hook did — the readback string a session quotes.</summary>
    [Export] public string LastEvent = "";

    private bool[,] _alive;
    private ColorRect[,] _invaders;
    private ColorRect _player;
    private ColorRect _bullet;
    private Label _hud;
    private Label _status;
    private float _stepAccum;
    private int _stepsThisFrame;

    public override void _Ready()
    {
        _alive = new bool[Rows, Columns];
        _invaders = new ColorRect[Rows, Columns];
        _player = GetNodeOrNull<ColorRect>("Player");
        _bullet = GetNodeOrNull<ColorRect>("Bullet");
        _hud = GetNodeOrNull<Label>("Hud");
        _status = GetNodeOrNull<Label>("Status");
        for (var r = 0; r < Rows; r++)
        {
            for (var c = 0; c < Columns; c++)
            {
                _alive[r, c] = true;
                var node = new ColorRect();
                node.Name = $"Invader_r{r}_c{c}";
                node.Size = new Vector2(InvaderW, InvaderH);
                node.Color = RowColor(r);
                AddChild(node);
                _invaders[r, c] = node;
            }
        }
        Recount();
        ApplyPlayer();
        ApplyWave();
        UpdateHud();
        if (_bullet != null)
        {
            _bullet.Visible = false;
        }
        GD.Print($"SI_READY cols={Columns} rows={Rows} alive={InvadersRemaining} player={PlayerX} "
                 + $"wave={WaveX},{WaveY} dir={WaveDir} step={StepInterval} poll={PollInput}");
    }

    private static Color RowColor(int row)
    {
        return row switch
        {
            0 => new Color(0.95f, 0.35f, 0.35f),
            1 => new Color(0.95f, 0.65f, 0.30f),
            2 => new Color(0.85f, 0.90f, 0.40f),
            3 => new Color(0.45f, 0.90f, 0.55f),
            _ => new Color(0.45f, 0.75f, 0.95f),
        };
    }

    /// <summary>Recomputes the counters from the grid, so a forced state cannot lie about them.</summary>
    private void Recount()
    {
        var alive = 0;
        for (var r = 0; r < Rows; r++)
        {
            for (var c = 0; c < Columns; c++)
            {
                if (_alive[r, c])
                {
                    alive++;
                }
            }
        }
        InvadersRemaining = alive;
        InvadersKilled = Columns * Rows - alive;
    }

    private void ApplyPlayer()
    {
        if (_player != null)
        {
            _player.Position = new Vector2(PlayerX, PlayerY);
        }
    }

    private void ApplyWave()
    {
        if (_invaders == null)
        {
            return;
        }
        for (var r = 0; r < Rows; r++)
        {
            for (var c = 0; c < Columns; c++)
            {
                var node = _invaders[r, c];
                if (node == null)
                {
                    continue;
                }
                node.Visible = _alive[r, c];
                if (_alive[r, c])
                {
                    node.Position = new Vector2(WaveX + c * CellW, WaveY + r * CellH);
                }
            }
        }
    }

    private void UpdateHud()
    {
        if (_hud != null)
        {
            _hud.Text = $"SCORE {Score}";
        }
        if (_status != null)
        {
            _status.Text = GameOver ? (Won ? "WAVE CLEARED" : "GAME OVER") : $"INVADERS {InvadersRemaining}";
        }
    }

    /// <summary>The wave's bottom edge in pixels.</summary>
    private int WaveBottom()
    {
        return WaveY + (Rows - 1) * CellH + InvaderH;
    }

    public override void _Process(double delta)
    {
        var dt = (float)delta;
        Ticks++;
        if (GameOver)
        {
            return;
        }

        // The player moves only when a test has switched polling on (determinism rule).
        if (PollInput)
        {
            var dir = 0.0f;
            if (Input.IsActionPressed("si_left"))
            {
                dir -= 1.0f;
            }
            if (Input.IsActionPressed("si_right"))
            {
                dir += 1.0f;
            }
            if (dir != 0.0f)
            {
                PlayerX = Mathf.Clamp(PlayerX + dir * PlayerSpeed * dt, WaveMinX, 780 - PlayerW);
                ApplyPlayer();
            }
            if (Input.IsActionJustPressed("si_fire"))
            {
                FireBullet();
            }
        }

        if (BulletActive)
        {
            BulletY -= BulletSpeed * dt;
            if (_bullet != null)
            {
                _bullet.Position = new Vector2(BulletX, BulletY);
            }
            if (BulletY + 8.0f < 0.0f)
            {
                BulletActive = false;
                if (_bullet != null)
                {
                    _bullet.Visible = false;
                }
                LastEvent = $"bullet left the screen shots={ShotsFired}";
            }
        }

        if (StepInterval > 0.0f)
        {
            _stepAccum += dt;
            _stepsThisFrame = 0;
            while (_stepAccum >= StepInterval && _stepsThisFrame < 64)
            {
                _stepAccum -= StepInterval;
                _stepsThisFrame++;
                StepWave();
                if (GameOver)
                {
                    break;
                }
            }
        }

        if (BulletActive && !GameOver)
        {
            CheckHit();
        }

        // The loss condition is a property of the wave's position, so it is checked every
        // frame rather than only inside a step: a forced state makes it observable at once.
        if (!GameOver && WaveBottom() >= DangerY)
        {
            GameOver = true;
            Won = false;
            LastEvent = $"invaders reached the player's row bottom={WaveBottom()} limit={DangerY}";
            UpdateHud();
        }
    }

    /// <summary>One horizontal step of the wave, with the edge reversal and the descent.</summary>
    public string StepWave()
    {
        var nextX = WaveX + 12 * WaveDir;
        if (nextX < WaveMinX || nextX > WaveMaxX)
        {
            WaveDir = -WaveDir;
            WaveY += DropStep;
            LastEvent = $"wave turned at x={WaveX} dir={WaveDir} y={WaveY}";
        }
        else
        {
            WaveX = nextX;
            LastEvent = $"wave stepped x={WaveX} dir={WaveDir}";
        }
        WaveSteps++;
        ApplyWave();
        if (WaveBottom() >= DangerY)
        {
            GameOver = true;
            Won = false;
            LastEvent += $" bottom={WaveBottom()} limit={DangerY}";
            UpdateHud();
        }
        return LastEvent;
    }

    /// <summary>The wave's speed; 0 keeps it frozen (the default).</summary>
    public string SetWaveSpeed(float seconds)
    {
        StepInterval = seconds;
        _stepAccum = 0.0f;
        LastEvent = $"wave speed interval={StepInterval}";
        GD.Print($"SI_SPEED interval={StepInterval}");
        return LastEvent;
    }

    /// <summary>Switches player input polling on or off (the default is off).</summary>
    public string SetPollInput(bool enabled)
    {
        PollInput = enabled;
        LastEvent = $"poll_input={PollInput}";
        return LastEvent;
    }

    /// <summary>Fires from the player's current position. One bullet at a time.</summary>
    public string FireBullet()
    {
        if (GameOver)
        {
            LastEvent = "fire refused: game over";
            return LastEvent;
        }
        if (BulletActive)
        {
            LastEvent = "fire refused: a bullet is already in flight";
            return LastEvent;
        }
        ShotsFired++;
        BulletActive = true;
        BulletX = PlayerX + PlayerW / 2.0f - 4.0f;
        BulletY = PlayerY - 12.0f;
        if (_bullet != null)
        {
            _bullet.Position = new Vector2(BulletX, BulletY);
            _bullet.Visible = true;
        }
        LastEvent = $"fired shot={ShotsFired} at={BulletX},{BulletY}";
        UpdateHud();
        return LastEvent;
    }

    /// <summary>
    /// Deterministic aim: fires a bullet directly below the centre of invader
    /// (<paramref name="row"/>, <paramref name="col"/>), far enough below it that the hit is a
    /// frame-by-frame flight and not an instant one.
    /// </summary>
    public string FireTestBullet(int row, int col)
    {
        if (GameOver)
        {
            LastEvent = "test fire refused: game over";
            return LastEvent;
        }
        if (row < 0 || row >= Rows || col < 0 || col >= Columns || !_alive[row, col])
        {
            LastEvent = $"test fire refused: no invader at {row},{col}";
            return LastEvent;
        }
        ShotsFired++;
        BulletActive = true;
        BulletX = WaveX + col * CellW + InvaderW / 2.0f - 4.0f;
        BulletY = WaveY + row * CellH + InvaderH + 30.0f;
        if (_bullet != null)
        {
            _bullet.Position = new Vector2(BulletX, BulletY);
            _bullet.Visible = true;
        }
        LastEvent = $"test fire shot={ShotsFired} target={row},{col} from={BulletX},{BulletY}";
        return LastEvent;
    }

    /// <summary>Kills the invader the bullet overlaps, or leaves the bullet flying.</summary>
    private void CheckHit()
    {
        for (var r = 0; r < Rows; r++)
        {
            for (var c = 0; c < Columns; c++)
            {
                if (!_alive[r, c])
                {
                    continue;
                }
                var left = WaveX + c * CellW;
                var top = WaveY + r * CellH;
                var overlap = BulletX + 8.0f >= left && BulletX <= left + InvaderW
                              && BulletY <= top + InvaderH && BulletY + 12.0f >= top;
                if (!overlap)
                {
                    continue;
                }
                Kill(r, c, "bullet");
                return;
            }
        }
    }

    private void Kill(int row, int col, string how)
    {
        _alive[row, col] = false;
        if (_invaders[row, col] != null)
        {
            _invaders[row, col].Visible = false;
        }
        Score += 10;
        Recount();
        BulletActive = false;
        if (_bullet != null)
        {
            _bullet.Visible = false;
        }
        LastEvent = $"kill how={how} at={row},{col} score={Score} remaining={InvadersRemaining}";
        if (InvadersRemaining == 0)
        {
            GameOver = true;
            Won = true;
            LastEvent += " wave cleared";
        }
        UpdateHud();
    }

    /// <summary>
    /// Test hook: writes the whole deterministic state in one call —
    /// <c>"alive=r,c|r,c;player=x;wave=x,y,dir;speed=s;score=n;shots=n"</c>.
    ///
    /// <para>Keys may be omitted; the ones given are applied. The wave speed is switched OFF
    /// here and polling is switched OFF with it, so a session's aim and the next readback are
    /// the same fact. A test that wants motion calls <see cref="SetWaveSpeed"/> itself — which
    /// is why "the wave moved" can never be an accident of timing.</para>
    /// </summary>
    public string ForceTestState(string spec)
    {
        StepInterval = 0.0f;
        PollInput = false;
        _stepAccum = 0.0f;
        BulletActive = false;
        Ticks = 0;
        WaveSteps = 0;
        GameOver = false;
        Won = false;
        if (_bullet != null)
        {
            _bullet.Visible = false;
        }
        Score = 0;
        ShotsFired = 0;
        WaveX = 140;
        WaveY = 90;
        WaveDir = 1;
        PlayerX = 370.0f;
        for (var r = 0; r < Rows; r++)
        {
            for (var c = 0; c < Columns; c++)
            {
                _alive[r, c] = true;
            }
        }
        foreach (var part in spec.Split(';'))
        {
            var kv = part.Split('=', 2);
            if (kv.Length != 2)
            {
                continue;
            }
            switch (kv[0])
            {
                case "alive":
                    for (var r = 0; r < Rows; r++)
                    {
                        for (var c = 0; c < Columns; c++)
                        {
                            _alive[r, c] = false;
                        }
                    }
                    foreach (var cell in kv[1].Split('|'))
                    {
                        var rc = cell.Split(',');
                        if (rc.Length != 2)
                        {
                            continue;
                        }
                        var rr = int.Parse(rc[0]);
                        var cc = int.Parse(rc[1]);
                        if (rr >= 0 && rr < Rows && cc >= 0 && cc < Columns)
                        {
                            _alive[rr, cc] = true;
                        }
                    }
                    break;
                case "player":
                    PlayerX = float.Parse(kv[1]);
                    break;
                case "wave":
                    {
                        var p = kv[1].Split(',');
                        WaveX = int.Parse(p[0]);
                        WaveY = int.Parse(p[1]);
                        if (p.Length > 2)
                        {
                            WaveDir = int.Parse(p[2]);
                        }
                    }
                    break;
                case "speed":
                    StepInterval = float.Parse(kv[1]);
                    break;
                case "score":
                    Score = int.Parse(kv[1]);
                    break;
                case "shots":
                    ShotsFired = int.Parse(kv[1]);
                    break;
            }
        }
        Recount();
        ApplyPlayer();
        ApplyWave();
        UpdateHud();
        LastEvent = $"forced alive={InvadersRemaining} score={Score} shots={ShotsFired} "
                    + $"player={PlayerX} wave={WaveX},{WaveY},{WaveDir} step={StepInterval}";
        return LastEvent;
    }

    /// <summary>The grid as 5 rows of <c>.</c>/<c>#</c>, plus every exported fact.</summary>
    public string Dump()
    {
        var sb = new StringBuilder();
        for (var r = 0; r < Rows; r++)
        {
            for (var c = 0; c < Columns; c++)
            {
                sb.Append(_alive[r, c] ? '#' : '.');
            }
            if (r + 1 < Rows)
            {
                sb.Append('/');
            }
        }
        return $"grid={sb} alive={InvadersRemaining} killed={InvadersKilled} score={Score} "
               + $"shots={ShotsFired} over={GameOver} won={Won} player={PlayerX} "
               + $"wave={WaveX},{WaveY},{WaveDir} steps={WaveSteps} bullet={BulletActive} "
               + $"bullet_at={BulletX},{BulletY} ticks={Ticks} poll={PollInput} step={StepInterval} "
               + $"last={LastEvent}";
    }

    /// <summary>The player's centre-x and the wave's bottom edge — the two readback shortcuts.</summary>
    public string Geometry()
    {
        return $"player_x={PlayerX} wave_x={WaveX} wave_y={WaveY} wave_bottom={WaveBottom()} "
               + $"bullet={BulletActive} bullet_x={BulletX} bullet_y={BulletY}";
    }
}
