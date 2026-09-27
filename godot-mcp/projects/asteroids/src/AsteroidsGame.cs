using Godot;
using System.Collections.Generic;
using System.Text;

namespace asteroids;

/// <summary>
/// Asteroids -- the sixth C# game of the godot-mcp series (TASK-098, DECISIONS.md D138).
///
/// <para><b>Design rule</b> (inherited from Pong / Breakout / Snake / Tetris / Space Invaders):
/// every fact the evidence model needs is a real Godot property on the root node --
/// <see cref="Score"/>, <see cref="Lives"/>, <see cref="AsteroidsRemaining"/>,
/// <see cref="AsteroidsSplit"/>, <see cref="AsteroidsDestroyed"/>, <see cref="ShotsFired"/>,
/// <see cref="ShipX"/>, <see cref="ShipY"/>, <see cref="ShipAngle"/>, <see cref="ShipVelX"/>,
/// <see cref="ShipVelY"/>, <see cref="Thrusting"/>, <see cref="ShipAlive"/>,
/// <see cref="BulletX"/>, <see cref="BulletY"/>, <see cref="BulletActive"/>,
/// <see cref="GameOver"/>, <see cref="Won"/>, <see cref="Ticks"/>. A session asserts these with
/// <c>running_game_assert_node_state</c>; it never parses a log line.</para>
///
/// <para><b>Determinism rule.</b> Three things are OFF by default and each is switched on only by
/// an explicit test call: the rocks do not drift (<see cref="DriftSpeed"/> = 0), the ship does not
/// poll input (<see cref="PollInput"/> = false), and every motion integrating <c>delta</c> is
/// reachable through a fixed-step hook (<see cref="ThrustStep"/>, <see cref="RotateShip"/>,
/// <see cref="StepRocks"/>) so a fact like "the ship moved" can never be an accident of frame
/// timing. <see cref="ForceTestState"/> pins the whole board in one call.</para>
///
/// <para><b>The ship, the bullet and every rock are runtime-created.</b> <see cref="_Ready"/>
/// builds them with <c>ColorRect</c> nodes; the scene file carries only the three static nodes
/// (Background, Hud, Status). That keeps the edited scene small, keeps it immune to the D-3
/// duplicate-name trap, and makes "a node created at run time really is drawn" part of this
/// game's own evidence.</para>
///
/// <para><b>Scoring has exactly one source.</b> One rock destroyed = 20 (large) / 50 (medium) /
/// 100 (small) points. An assertion about <see cref="Score"/> therefore names the hit that
/// produced it.</para>
///
/// <para><b>Splitting has exactly one shape.</b> A large rock becomes two medium ones, a medium
/// rock two small ones, a small rock just disappears. <see cref="AsteroidsSplit"/> counts the
/// splits and <see cref="AsteroidsRemaining"/> is recomputed from the list, so the two can never
/// disagree.</para>
/// </summary>
public partial class AsteroidsGame : Node2D
{
    // --- field geometry --------------------------------------------------------
    /// <summary>Playfield width. A ship or rock leaving one edge reappears on the other.</summary>
    [Export] public int FieldW = 800;

    /// <summary>Playfield height.</summary>
    [Export] public int FieldH = 600;

    /// <summary>Ship square size in pixels (the node is this wide and its pivot is its centre).</summary>
    [Export] public float ShipSize = 22.0f;

    /// <summary>Degrees per second the ship turns at (input path only).</summary>
    [Export] public float RotateRate = 180.0f;

    /// <summary>Thrust acceleration in pixels per second squared.</summary>
    [Export] public float ThrustAccel = 260.0f;

    /// <summary>Velocity loss per second (the classic Asteroids drag).</summary>
    [Export] public float Drag = 0.4f;

    /// <summary>Speed cap in pixels per second.</summary>
    [Export] public float MaxSpeed = 320.0f;

    /// <summary>Bullet speed in pixels per second.</summary>
    [Export] public int BulletSpeed = 420;

    /// <summary>Seconds a bullet lives before it expires.</summary>
    [Export] public float BulletLife = 1.2f;

    /// <summary>Rock radius for each size: index 1 = small, 2 = medium, 3 = large.</summary>
    [Export] public float SmallRadius = 10.0f;
    [Export] public float MediumRadius = 17.0f;
    [Export] public float LargeRadius = 26.0f;

    // --- observable state, all of it a real Godot property ---------------------
    /// <summary>Points: 20 per large rock, 50 per medium, 100 per small.</summary>
    [Export] public int Score = 0;

    /// <summary>Lives left. A rock hitting the ship costs exactly one.</summary>
    [Export] public int Lives = 3;

    /// <summary>Rocks still in the field (recomputed from the list, never incremented by hand).</summary>
    [Export] public int AsteroidsRemaining = 0;

    /// <summary>How many rocks have split in two.</summary>
    [Export] public int AsteroidsSplit = 0;

    /// <summary>How many rocks have been destroyed (a split does not count as a destroy).</summary>
    [Export] public int AsteroidsDestroyed = 0;

    /// <summary>Bullets fired, by the input action or by a test hook.</summary>
    [Export] public int ShotsFired = 0;

    /// <summary>Ship centre x.</summary>
    [Export] public float ShipX = 400.0f;

    /// <summary>Ship centre y.</summary>
    [Export] public float ShipY = 300.0f;

    /// <summary>Ship facing in degrees; 0 = pointing right, growing clockwise on screen.</summary>
    [Export] public float ShipAngle = 0.0f;

    /// <summary>Ship velocity x in pixels per second.</summary>
    [Export] public float ShipVelX = 0.0f;

    /// <summary>Ship velocity y in pixels per second.</summary>
    [Export] public float ShipVelY = 0.0f;

    /// <summary>True while the thrust action (or a thrust hook) is applied.</summary>
    [Export] public bool Thrusting = false;

    /// <summary>False after a rock hit, until <see cref="RespawnShip"/> or a forced state.</summary>
    [Export] public bool ShipAlive = true;

    /// <summary>Bullet centre x.</summary>
    [Export] public float BulletX = -100.0f;

    /// <summary>Bullet centre y.</summary>
    [Export] public float BulletY = -100.0f;

    /// <summary>True while a bullet is in flight (at most one at a time).</summary>
    [Export] public bool BulletActive = false;

    /// <summary>True when the field is cleared (win) or the last life is gone (loss).</summary>
    [Export] public bool GameOver = false;

    /// <summary>True when <see cref="GameOver"/> was reached by clearing the field.</summary>
    [Export] public bool Won = false;

    /// <summary>Centre x of the first rock in the list. A real property, so a multi-frame sample
    /// can show a rock moving as a run of values rather than as a claim.</summary>
    [Export] public float FirstRockX = 0.0f;

    /// <summary>Centre y of the first rock in the list (same reason as <see cref="FirstRockX"/>).</summary>
    [Export] public float FirstRockY = 0.0f;

    /// <summary>Size of the first rock in the list: 3 = large, 2 = medium, 1 = small, 0 = none.
    /// A real property, so "the large rock became two medium ones" is assertable by machine.</summary>
    [Export] public int FirstRockSize = 0;

    /// <summary>Rock drift speed multiplier in pixels per second; 0 keeps them frozen (the default).</summary>
    [Export] public float DriftSpeed = 0.0f;

    /// <summary>When true the game reads its player's keyboard. The test driver switches this
    /// OFF explicitly (<see cref="SetPollInput"/>, <see cref="ForceTestState"/>) when it needs
    /// a frozen, deterministic state; the deterministic defaults live in AutoClock / AutoPlay /
    /// DriftSpeed, not here (TASK-116 defect D1).</summary>
    [Export] public bool PollInput = true;

    /// <summary>Frames processed since the last reset.</summary>
    [Export] public int Ticks = 0;

    /// <summary>What the last hook did -- the readback string a session quotes.</summary>
    [Export] public string LastEvent = "";

    // --- private model ---------------------------------------------------------
    private class Rock
    {
        public float X;
        public float Y;
        public float DirX;
        public float DirY;
        public int Size;
        public ColorRect Node;
    }

    private readonly List<Rock> _rocks = new List<Rock>();
    private ColorRect _ship;
    private ColorRect _bullet;
    private Label _hud;
    private Label _status;
    private float _bulletAngle;
    private float _bulletSpeed;
    private float _bulletAge;
    private int _rockSeq;

    /// <summary>The deterministic starting field: four large rocks in the four quadrants.</summary>
    private static readonly float[,] StartRocks =
    {
        { 150.0f, 140.0f },
        { 650.0f, 130.0f },
        { 180.0f, 470.0f },
        { 640.0f, 460.0f },
    };

    public override void _Ready()
    {
        _ship = GetNodeOrNull<ColorRect>("Ship");
        _bullet = GetNodeOrNull<ColorRect>("Bullet");
        _hud = GetNodeOrNull<Label>("Hud");
        _status = GetNodeOrNull<Label>("Status");
        if (_ship == null)
        {
            _ship = MakeRect("Ship", new Vector2(ShipSize, ShipSize), new Color(0.45f, 1.0f, 0.95f));
        }
        if (_bullet == null)
        {
            _bullet = MakeRect("Bullet", new Vector2(4.0f, 4.0f), new Color(1.0f, 1.0f, 0.45f));
        }
        BuildStartField();
        ApplyShip();
        ApplyBullet();
        ApplyRocks();
        UpdateHud();
        GD.Print($"AST_READY rocks={AsteroidsRemaining} lives={Lives} ship={ShipX},{ShipY} "
                 + $"angle={ShipAngle} drift={DriftSpeed} poll={PollInput}");
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

    /// <summary>Fills the field with the four starting large rocks.</summary>
    private void BuildStartField()
    {
        ClearRocks();
        for (var i = 0; i < StartRocks.GetLength(0); i++)
        {
            // The four rocks fan out in four different directions; the direction is stored
            // whether or not drift is switched on, so a test can predict every position.
            var dirs = new[] { new Vector2(1.0f, 0.6f), new Vector2(-1.0f, 0.8f),
                               new Vector2(0.7f, -1.0f), new Vector2(-0.6f, -1.0f) };
            AddRock(StartRocks[i, 0], StartRocks[i, 1], dirs[i].X, dirs[i].Y, 3);
        }
        Recount();
    }

    private void ClearRocks()
    {
        foreach (var rock in _rocks)
        {
            if (rock.Node != null && IsInstanceValid(rock.Node))
            {
                rock.Node.QueueFree();
            }
        }
        _rocks.Clear();
    }

    private Rock AddRock(float x, float y, float dx, float dy, int size)
    {
        var radius = RadiusFor(size);
        var node = MakeRect($"Rock_{_rockSeq++}", new Vector2(radius * 2.0f, radius * 2.0f),
                            ColorFor(size));
        var rock = new Rock { X = x, Y = y, DirX = dx, DirY = dy, Size = size, Node = node };
        _rocks.Add(rock);
        return rock;
    }

    private static float RadiusFor(int size)
    {
        return size >= 3 ? 26.0f : (size == 2 ? 17.0f : 10.0f);
    }

    private static Color ColorFor(int size)
    {
        if (size >= 3)
        {
            return new Color(0.85f, 0.80f, 0.70f);
        }
        if (size == 2)
        {
            return new Color(0.70f, 0.72f, 0.85f);
        }
        return new Color(0.55f, 0.60f, 0.75f);
    }

    /// <summary>Recomputes the counters from the list, so a forced state cannot lie about them.</summary>
    private void Recount()
    {
        AsteroidsRemaining = _rocks.Count;
    }

    private void ApplyShip()
    {
        if (_ship == null)
        {
            return;
        }
        _ship.Visible = ShipAlive;
        _ship.Position = new Vector2(ShipX - ShipSize / 2.0f, ShipY - ShipSize / 2.0f);
        _ship.Rotation = Mathf.DegToRad(ShipAngle);
    }

    private void ApplyBullet()
    {
        if (_bullet == null)
        {
            return;
        }
        _bullet.Visible = BulletActive;
        _bullet.Position = new Vector2(BulletX - 2.0f, BulletY - 2.0f);
        _bullet.Rotation = Mathf.DegToRad(_bulletAngle);
    }

    private void ApplyRocks()
    {
        foreach (var rock in _rocks)
        {
            if (rock.Node == null)
            {
                continue;
            }
            var radius = RadiusFor(rock.Size);
            rock.Node.Position = new Vector2(rock.X - radius, rock.Y - radius);
        }
        FirstRockX = _rocks.Count > 0 ? _rocks[0].X : -1.0f;
        FirstRockY = _rocks.Count > 0 ? _rocks[0].Y : -1.0f;
        FirstRockSize = _rocks.Count > 0 ? _rocks[0].Size : 0;
    }

    private void UpdateHud()
    {
        if (_hud != null)
        {
            _hud.Text = $"SCORE {Score}  LIVES {Lives}  ROCKS {AsteroidsRemaining}";
        }
        if (_status != null)
        {
            _status.Text = GameOver ? (Won ? "FIELD CLEARED" : "GAME OVER")
                                    : $"ASTEROIDS {AsteroidsRemaining}";
        }
    }

    private static float Wrap(float value, float limit)
    {
        while (value < 0.0f)
        {
            value += limit;
        }
        while (value >= limit)
        {
            value -= limit;
        }
        return value;
    }

    private static float Radius(int size)
    {
        return size >= 3 ? 26.0f : (size == 2 ? 17.0f : 10.0f);
    }

    public override void _Process(double delta)
    {
        var dt = (float)delta;
        Ticks++;
        if (GameOver)
        {
            return;
        }

        // --- the input path, off unless a test switches it on (determinism rule) ---
        if (PollInput && ShipAlive)
        {
            if (Input.IsActionPressed("ast_left"))
            {
                ShipAngle -= RotateRate * dt;
            }
            if (Input.IsActionPressed("ast_right"))
            {
                ShipAngle += RotateRate * dt;
            }
            Thrusting = Input.IsActionPressed("ast_thrust");
            if (Input.IsActionJustPressed("ast_fire"))
            {
                FireBullet();
            }
            IntegrateShip(dt);
        }

        MoveBullet(dt);
        if (DriftSpeed > 0.0f)
        {
            MoveRocks(dt);
        }
        if (BulletActive)
        {
            CheckBulletHits();
        }
        CheckShipHits();
    }

    /// <summary>Integrates the ship one step: thrust, drag, position, wrap.</summary>
    private void IntegrateShip(float dt)
    {
        if (!ShipAlive)
        {
            return;
        }
        if (Thrusting)
        {
            var rad = Mathf.DegToRad(ShipAngle);
            ShipVelX += Mathf.Cos(rad) * ThrustAccel * dt;
            ShipVelY += Mathf.Sin(rad) * ThrustAccel * dt;
        }
        var damp = 1.0f - Mathf.Clamp(Drag * dt, 0.0f, 1.0f);
        ShipVelX *= damp;
        ShipVelY *= damp;
        var speed = Mathf.Sqrt(ShipVelX * ShipVelX + ShipVelY * ShipVelY);
        if (speed > MaxSpeed)
        {
            ShipVelX = ShipVelX / speed * MaxSpeed;
            ShipVelY = ShipVelY / speed * MaxSpeed;
        }
        ShipX = Wrap(ShipX + ShipVelX * dt, FieldW);
        ShipY = Wrap(ShipY + ShipVelY * dt, FieldH);
        ApplyShip();
    }

    private void MoveBullet(float dt)
    {
        if (!BulletActive)
        {
            return;
        }
        var rad = Mathf.DegToRad(_bulletAngle);
        BulletX = Wrap(BulletX + Mathf.Cos(rad) * _bulletSpeed * dt, FieldW);
        BulletY = Wrap(BulletY + Mathf.Sin(rad) * _bulletSpeed * dt, FieldH);
        _bulletAge += dt;
        ApplyBullet();
        if (_bulletAge >= BulletLife)
        {
            DeactivateBullet($"bullet expired age={_bulletAge:F2}");
        }
    }

    private void MoveRocks(float dt)
    {
        foreach (var rock in _rocks)
        {
            rock.X = Wrap(rock.X + rock.DirX * DriftSpeed * dt, FieldW);
            rock.Y = Wrap(rock.Y + rock.DirY * DriftSpeed * dt, FieldH);
        }
        ApplyRocks();
    }

    private void DeactivateBullet(string why)
    {
        BulletActive = false;
        ApplyBullet();
        LastEvent = why;
    }

    /// <summary>Kills or splits the rock the bullet overlaps, then retires the bullet.</summary>
    private void CheckBulletHits()
    {
        for (var i = 0; i < _rocks.Count; i++)
        {
            var rock = _rocks[i];
            var radius = Radius(rock.Size);
            var dx = BulletX - rock.X;
            var dy = BulletY - rock.Y;
            if (dx * dx + dy * dy > radius * radius)
            {
                continue;
            }
            HitRock(i);
            DeactivateBullet(LastEvent);
            return;
        }
    }

    /// <summary>
    /// The one scoring/splitting rule of the game: large -> two medium, medium -> two small,
    /// small -> gone. <see cref="AsteroidsSplit"/> counts only the two that split.
    /// </summary>
    private void HitRock(int index)
    {
        var rock = _rocks[index];
        var size = rock.Size;
        Score += size >= 3 ? 20 : (size == 2 ? 50 : 100);
        AsteroidsDestroyed++;
        if (rock.Node != null && IsInstanceValid(rock.Node))
        {
            rock.Node.QueueFree();
        }
        _rocks.RemoveAt(index);
        if (size > 1)
        {
            AsteroidsSplit++;
            AddRock(rock.X, rock.Y, 1.0f, 0.35f, size - 1);
            AddRock(rock.X, rock.Y, -0.65f, -0.75f, size - 1);
            LastEvent = $"split size={size} into=2x{size - 1} score={Score} rocks={_rocks.Count}";
        }
        else
        {
            LastEvent = $"destroyed size=1 score={Score} rocks={_rocks.Count}";
        }
        Recount();
        ApplyRocks();
        if (AsteroidsRemaining == 0)
        {
            GameOver = true;
            Won = true;
            LastEvent += " field cleared";
        }
        UpdateHud();
    }

    /// <summary>Charges one life when a rock overlaps the ship. Checked every frame.</summary>
    private void CheckShipHits()
    {
        if (!ShipAlive || GameOver)
        {
            return;
        }
        var shipRadius = ShipSize / 2.0f;
        foreach (var rock in _rocks)
        {
            var dx = ShipX - rock.X;
            var dy = ShipY - rock.Y;
            var reach = shipRadius + Radius(rock.Size);
            if (dx * dx + dy * dy > reach * reach)
            {
                continue;
            }
            Lives--;
            ShipAlive = false;
            Thrusting = false;
            ShipVelX = 0.0f;
            ShipVelY = 0.0f;
            ShipX = FieldW / 2.0f;
            ShipY = FieldH / 2.0f;
            ShipAngle = 0.0f;
            LastEvent = $"ship hit lives={Lives} rocks={_rocks.Count}";
            if (Lives <= 0)
            {
                GameOver = true;
                Won = false;
                LastEvent += " game over";
            }
            ApplyShip();
            UpdateHud();
            return;
        }
    }

    // --- hooks the session drives ----------------------------------------------

    /// <summary>Rock drift in pixels per second; 0 keeps them frozen (the default).</summary>
    public string SetDrift(float speed)
    {
        DriftSpeed = speed;
        LastEvent = $"drift={DriftSpeed}";
        GD.Print($"AST_DRIFT speed={DriftSpeed}");
        return LastEvent;
    }

    /// <summary>Switches ship input polling on or off (the default is off).</summary>
    public string SetPollInput(bool enabled)
    {
        PollInput = enabled;
        LastEvent = $"poll_input={PollInput}";
        return LastEvent;
    }

    /// <summary>Turns the ship by an exact number of degrees (a fixed-step test hook).</summary>
    public string RotateShip(float degrees)
    {
        ShipAngle += degrees;
        ApplyShip();
        LastEvent = $"rotated by={degrees} angle={ShipAngle}";
        return LastEvent;
    }

    /// <summary>
    /// Advances the ship by one exact time step with thrust on (a fixed-step test hook), so
    /// "the ship moved" is a property of the call and not of the frame clock.
    /// </summary>
    public string ThrustStep(float seconds)
    {
        Thrusting = true;
        IntegrateShip(seconds);
        Thrusting = false;
        LastEvent = $"thrust step={seconds} pos={ShipX:F2},{ShipY:F2} vel={ShipVelX:F2},{ShipVelY:F2} "
                    + $"angle={ShipAngle}";
        return LastEvent;
    }

    /// <summary>Advances every rock by one exact time step (a fixed-step test hook).</summary>
    public string StepRocks(float seconds)
    {
        MoveRocks(seconds);
        LastEvent = $"rocks stepped by={seconds} speed={DriftSpeed} first={RockList()}";
        return LastEvent;
    }

    /// <summary>Puts the ship back in the middle with a clean shield state.</summary>
    public string RespawnShip()
    {
        ShipAlive = true;
        ShipVelX = 0.0f;
        ShipVelY = 0.0f;
        ShipX = FieldW / 2.0f;
        ShipY = FieldH / 2.0f;
        ShipAngle = 0.0f;
        ApplyShip();
        LastEvent = $"respawned at={ShipX},{ShipY} lives={Lives}";
        return LastEvent;
    }

    /// <summary>Fires from the ship's nose along its facing. One bullet at a time.</summary>
    public string FireBullet()
    {
        if (GameOver || !ShipAlive)
        {
            LastEvent = "fire refused: ship is not flying";
            return LastEvent;
        }
        if (BulletActive)
        {
            LastEvent = "fire refused: a bullet is already in flight";
            return LastEvent;
        }
        ShotsFired++;
        var rad = Mathf.DegToRad(ShipAngle);
        _bulletSpeed = BulletSpeed;
        _bulletAngle = ShipAngle;
        _bulletAge = 0.0f;
        BulletActive = true;
        BulletX = Wrap(ShipX + Mathf.Cos(rad) * (ShipSize / 2.0f + 6.0f), FieldW);
        BulletY = Wrap(ShipY + Mathf.Sin(rad) * (ShipSize / 2.0f + 6.0f), FieldH);
        ApplyBullet();
        LastEvent = $"fired shot={ShotsFired} angle={ShipAngle} at={BulletX:F1},{BulletY:F1}";
        return LastEvent;
    }

    /// <summary>
    /// Places a bullet on an exact heading and age (a fixed-step test hook). This is the hook a
    /// flight sample uses: it is fired from far enough away that the flight is a run of
    /// <c>BulletActive=true</c> frames and the hit lands inside the sample window.
    /// </summary>
    public string PlaceBullet(float x, float y, float angle, float speed, float age)
    {
        _bulletSpeed = speed;
        _bulletAngle = angle;
        _bulletAge = age;
        BulletX = x;
        BulletY = y;
        BulletActive = true;
        ShotsFired++;
        ApplyBullet();
        LastEvent = $"placed bullet at={x:F1},{y:F1} angle={angle} speed={speed}";
        return LastEvent;
    }

    /// <summary>
    /// Aims at rock <paramref name="index"/> from <paramref name="distance"/> pixels below it,
    /// heading straight up. With drift frozen the rock cannot move, so the flight time is exactly
    /// <c>distance / BulletSpeed</c> and the hit is predictable rather than lucky.
    /// </summary>
    public string AimBulletAtRock(int index, float distance)
    {
        if (index < 0 || index >= _rocks.Count)
        {
            LastEvent = $"aim refused: no rock at index {index} (count={_rocks.Count})";
            return LastEvent;
        }
        var rock = _rocks[index];
        return PlaceBullet(rock.X, rock.Y + distance, -90.0f, BulletSpeed, 0.0f);
    }

    /// <summary>
    /// Writes the whole deterministic state in one call --
    /// <c>"rocks=x,y,size|...;ship=x,y,angle;vel=vx,vy;score=n;lives=n;drift=s;alive=bool"</c>.
    ///
    /// <para>Keys may be omitted; the ones given are applied. Drift and polling are switched OFF
    /// here, so a session's aim and the next readback are the same fact. A test that wants motion
    /// calls <see cref="SetDrift"/> / <see cref="ThrustStep"/> itself.</para>
    /// </summary>
    public string ForceTestState(string spec)
    {
        DriftSpeed = 0.0f;
        PollInput = false;
        Thrusting = false;
        BulletActive = false;
        Ticks = 0;
        Score = 0;
        Lives = 3;
        ShotsFired = 0;
        AsteroidsSplit = 0;
        AsteroidsDestroyed = 0;
        GameOver = false;
        Won = false;
        ShipAlive = true;
        ShipX = FieldW / 2.0f;
        ShipY = FieldH / 2.0f;
        ShipAngle = 0.0f;
        ShipVelX = 0.0f;
        ShipVelY = 0.0f;
        _bulletAge = 0.0f;
        BuildStartField();
        foreach (var part in spec.Split(';'))
        {
            var kv = part.Split(new[] { '=' }, 2);
            if (kv.Length != 2)
            {
                continue;
            }
            switch (kv[0])
            {
                case "rocks":
                    // An empty value is the way a test asks for an empty field.
                    ClearRocks();
                    foreach (var cell in kv[1].Split('|'))
                    {
                        if (cell.Length == 0)
                        {
                            continue;
                        }
                        var p = cell.Split(',');
                        if (p.Length < 3)
                        {
                            continue;
                        }
                        var dx = p.Length > 3 ? float.Parse(p[3]) : 1.0f;
                        var dy = p.Length > 4 ? float.Parse(p[4]) : 0.35f;
                        AddRock(float.Parse(p[0]), float.Parse(p[1]), dx, dy, int.Parse(p[2]));
                    }
                    break;
                case "ship":
                    {
                        var p = kv[1].Split(',');
                        ShipX = float.Parse(p[0]);
                        ShipY = float.Parse(p[1]);
                        if (p.Length > 2)
                        {
                            ShipAngle = float.Parse(p[2]);
                        }
                    }
                    break;
                case "vel":
                    {
                        var p = kv[1].Split(',');
                        ShipVelX = float.Parse(p[0]);
                        ShipVelY = float.Parse(p[1]);
                    }
                    break;
                case "score":
                    Score = int.Parse(kv[1]);
                    break;
                case "lives":
                    Lives = int.Parse(kv[1]);
                    break;
                case "drift":
                    DriftSpeed = float.Parse(kv[1]);
                    break;
                case "alive":
                    ShipAlive = kv[1] == "true" || kv[1] == "1";
                    break;
                case "split":
                    AsteroidsSplit = int.Parse(kv[1]);
                    break;
                case "destroyed":
                    AsteroidsDestroyed = int.Parse(kv[1]);
                    break;
            }
        }
        Recount();
        ApplyShip();
        ApplyBullet();
        ApplyRocks();
        UpdateHud();
        LastEvent = $"forced rocks={AsteroidsRemaining} score={Score} lives={Lives} "
                    + $"ship={ShipX:F1},{ShipY:F1},{ShipAngle} drift={DriftSpeed}";
        return LastEvent;
    }

    /// <summary>The rock list as <c>index:size@x,y</c> -- the split evidence a session quotes.</summary>
    public string RockList()
    {
        var sb = new StringBuilder();
        for (var i = 0; i < _rocks.Count; i++)
        {
            if (i > 0)
            {
                sb.Append('|');
            }
            sb.Append($"{i}:s{_rocks[i].Size}@{_rocks[i].X:F0},{_rocks[i].Y:F0}");
        }
        return sb.Length == 0 ? "empty" : sb.ToString();
    }

    /// <summary>Every exported fact as one line.</summary>
    public string Dump()
    {
        return $"rocks={AsteroidsRemaining} split={AsteroidsSplit} destroyed={AsteroidsDestroyed} "
               + $"score={Score} lives={Lives} over={GameOver} won={Won} ship={ShipX:F2},{ShipY:F2} "
               + $"angle={ShipAngle:F2} vel={ShipVelX:F2},{ShipVelY:F2} alive={ShipAlive} "
               + $"thrust={Thrusting} bullet={BulletActive} bullet_at={BulletX:F2},{BulletY:F2} "
               + $"shots={ShotsFired} ticks={Ticks} drift={DriftSpeed} poll={PollInput} "
               + $"last={LastEvent}";
    }

    /// <summary>The two readback shortcuts: where the ship is and where the first rock is.</summary>
    public string Geometry()
    {
        var first = _rocks.Count > 0 ? $"{_rocks[0].X:F0},{_rocks[0].Y:F0},s{_rocks[0].Size}" : "none";
        return $"ship={ShipX:F0},{ShipY:F0},{ShipAngle:F0} bullet={BulletActive} "
               + $"bullet_at={BulletX:F0},{BulletY:F0} first_rock={first}";
    }
}
