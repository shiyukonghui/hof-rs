using Godot;
using System.Collections.Generic;
using System.Text;

namespace lunarlander;

/// <summary>
/// Lunar Lander -- the twentieth C# game of the godot-mcp series (TASK-104, DECISIONS.md D152),
/// and the game that closes the twenty-game target of D138.
///
/// <para><b>Design rule</b> (inherited from the nineteen games before it): every fact the evidence
/// model needs is a real Godot property on the root node -- <see cref="Lx"/>, <see cref="Ly"/>,
/// <see cref="Vx"/>, <see cref="Vy"/>, <see cref="AngleIndex"/>, <see cref="Fuel"/>,
/// <see cref="ThrustOn"/>, <see cref="ThrustCount"/>, <see cref="Rotations"/>,
/// <see cref="Landed"/>, <see cref="Crashed"/>, <see cref="Won"/>, <see cref="PadIndex"/>,
/// <see cref="Score"/>, <see cref="StateHash"/>, <see cref="Steps"/>, <see cref="Elapsed"/>,
/// <see cref="Ticks"/>. A session asserts these with <c>running_game_assert_node_state</c>; it
/// never parses a log line.</para>
///
/// <para><b>Integer, and therefore recomputable.</b> There is no float in the simulation -- not even
/// for the rotation. The attitude is one of TWELVE discrete angles (30 degrees apart) and the thrust
/// of each one is an integer pair in <see cref="ThrustX"/>/<see cref="ThrustY"/>; a burn adds that
/// pair to the velocity and costs one fuel unit, gravity adds <see cref="GravityStep"/> every step,
/// and the position is integrated by integer addition. The whole trajectory is therefore an exact
/// integer sequence, and the Python second implementation in
/// <c>recovery\work\task104\make_session_lunarlander.py</c> reproduces it step for step -- its
/// outputs are the session's assertion literals, including every checkpoint of both descents.</para>
///
/// <para><b>The landing test</b> (<see cref="Tick"/>): the lander touches down when its belly reaches
/// <see cref="GroundY"/>. It survives only when it is over one of the three pads, when
/// <c>|Vx| &lt;= MaxLandVx</c>, when <c>|Vy| &lt;= MaxLandVy</c> and when the attitude is within
/// <see cref="MaxLandAngle"/> steps of upright; otherwise the landing is a crash. The score of a
/// survived landing is the remaining fuel times the pad's multiplier -- the remaining-fuel score.</para>
///
/// <para><b>Frame-rate independence (the F-1 lesson).</b> The auto clock is a FLOAT ACCUMULATOR
/// (<c>_autoAccum += delta * AutoClock</c>). Two producers, two properties:
/// <see cref="LastAutoSteps"/> belongs to the clock and <see cref="LastHookSteps"/> to the
/// <see cref="StepFrames"/> hook. <see cref="Elapsed"/> is a monotonic float second counter that is
/// never truncated.</para>
/// </summary>
public partial class LunarLanderGame : Node2D
{
    // --- the field ---------------------------------------------------------------
    /// <summary>Field width in pixels.</summary>
    [Export] public int FieldW = 800;

    /// <summary>Field height in pixels.</summary>
    [Export] public int FieldH = 600;

    /// <summary>The ground line in pixels.</summary>
    [Export] public int GroundY = 560;

    /// <summary>Half the lander's height in pixels (the belly is this far below the centre).</summary>
    [Export] public int HalfH = 8;

    /// <summary>Half the lander's width in pixels.</summary>
    [Export] public int HalfW = 10;

    // --- the rules ---------------------------------------------------------------
    /// <summary>Velocity added every step, downwards.</summary>
    [Export] public int GravityStep = 1;

    /// <summary>Fuel one burn costs.</summary>
    [Export] public int ThrustCost = 1;

    /// <summary>Fuel at the start of a fresh game.</summary>
    [Export] public int StartFuel = 500;

    /// <summary>How many discrete attitudes the lander has (30 degrees apart).</summary>
    [Export] public int AngleCount = 12;

    /// <summary>Degrees between two attitudes.</summary>
    [Export] public int AngleStepDeg = 30;

    /// <summary>Largest horizontal speed a landing survives.</summary>
    [Export] public int MaxLandVx = 2;

    /// <summary>Largest vertical speed a landing survives.</summary>
    [Export] public int MaxLandVy = 6;

    /// <summary>How many attitude steps away from upright a landing survives.</summary>
    [Export] public int MaxLandAngle = 1;

    /// <summary>X at the start of a fresh game.</summary>
    [Export] public int StartX = 400;

    /// <summary>Y at the start of a fresh game.</summary>
    [Export] public int StartY = 100;

    // --- observable state, all of it a real Godot property ------------------------
    /// <summary>Lander centre x in pixels.</summary>
    [Export] public int Lx = 400;

    /// <summary>Lander centre y in pixels.</summary>
    [Export] public int Ly = 100;

    /// <summary>Horizontal velocity in pixels per step.</summary>
    [Export] public int Vx = 0;

    /// <summary>Vertical velocity in pixels per step (positive is downwards).</summary>
    [Export] public int Vy = 0;

    /// <summary>The attitude, 0 is upright, 1..11 turn clockwise in 30 degree steps.</summary>
    [Export] public int AngleIndex = 0;

    /// <summary>The attitude in degrees (<see cref="AngleIndex"/> times <see cref="AngleStepDeg"/>).</summary>
    [Export] public int AngleDeg = 0;

    /// <summary>Fuel left.</summary>
    [Export] public int Fuel = 500;

    /// <summary>X of the burn the current attitude applies.</summary>
    [Export] public int ThrustX = 0;

    /// <summary>Y of the burn the current attitude applies.</summary>
    [Export] public int ThrustY = -4;

    /// <summary>True while the continuous burn is on.</summary>
    [Export] public bool ThrustOn = false;

    /// <summary>Burns applied over the whole game.</summary>
    [Export] public int ThrustCount = 0;

    /// <summary>Fuel burned over the whole game.</summary>
    [Export] public int FuelUsed = 0;

    /// <summary>Attitude changes over the whole game.</summary>
    [Export] public int Rotations = 0;

    /// <summary>Burns the fuel rule refused.</summary>
    [Export] public int RejectedThrusts = 0;

    /// <summary>Attitude changes the rules refused.</summary>
    [Export] public int RejectedRotations = 0;

    /// <summary>The three pads as <c>"x0,x1|x0,x1|x0,x1"</c>.</summary>
    [Export] public string PadList = "";

    /// <summary>The pad multipliers as <c>"1,2,1"</c>.</summary>
    [Export] public string PadMultipliers = "";

    /// <summary>True when the lander came down on a pad inside every limit.</summary>
    [Export] public bool Landed = false;

    /// <summary>True when the lander came down outside a limit, or left the field.</summary>
    [Export] public bool Crashed = false;

    /// <summary>True when the game ended, and it was survived.</summary>
    [Export] public bool Won = false;

    /// <summary>True when the game ended, either way.</summary>
    [Export] public bool GameOver = false;

    /// <summary>The pad the lander came down on, -1 when it missed every pad.</summary>
    [Export] public int PadIndex = -1;

    /// <summary>Remaining fuel times the pad multiplier.</summary>
    [Export] public int Score = 0;

    /// <summary>The y the lander ended on.</summary>
    [Export] public int TouchY = 0;

    /// <summary>The most negative <see cref="Vy"/> the flight reached (the top of the arc).</summary>
    [Export] public int MinVy = 0;

    /// <summary>The largest <see cref="Vy"/> the flight reached.</summary>
    [Export] public int MaxVy = 0;

    /// <summary>Multiply-31 hash of the flight, recomputable from the printed state.</summary>
    [Export] public int StateHash = 0;

    /// <summary>Simulation steps taken (one per fixed tick; see <see cref="StepFrames"/>).</summary>
    [Export] public int Steps = 0;

    /// <summary>Seconds since the last reset: a monotonic FLOAT accumulator, never truncated.</summary>
    [Export] public float Elapsed = 0.0f;

    /// <summary>Frames processed since the last reset.</summary>
    [Export] public int Ticks = 0;

    /// <summary>Auto steps per second; 0 keeps the world still (the default).</summary>
    [Export] public float AutoClock = 0.0f;

    /// <summary>Steps the auto clock has applied over the whole game.</summary>
    [Export] public int AutoTicks = 0;

    /// <summary>Steps the auto clock applied on the LAST frame (0 while the clock is off).</summary>
    [Export] public int LastAutoSteps = 0;

    /// <summary>
    /// Steps the LAST <see cref="StepFrames"/> CALL applied. Its own property, and the clock never
    /// writes it (2048's r1 run, TASK-100 defect G1). Two producers, two properties.
    /// </summary>
    [Export] public int LastHookSteps = 0;

    /// <summary>Column the last <see cref="Probe"/> looked at.</summary>
    [Export] public int ProbeX = -1;

    /// <summary>Row the last <see cref="Probe"/> looked at.</summary>
    [Export] public int ProbeY = -1;

    /// <summary>A readable name for the probed point: outside / lander / pad / ground / sky.</summary>
    [Export] public string ProbeState = "";

    /// <summary>Index of the pad the probe named, -1 when the point is not on a pad.</summary>
    [Export] public int ProbeValue = -1;

    /// <summary>When false the world ignores input (determinism rule: no polling by default).</summary>
    [Export] public bool PollInput = false;

    /// <summary>Burns that arrived through the declared input action.</summary>
    [Export] public int InputThrusts = 0;

    /// <summary>What the last hook did -- the readback string a session quotes.</summary>
    [Export] public string LastEvent = "";

    // --- the tables ----------------------------------------------------------------
    // The attitude table: 12 integer thrust pairs, 30 degrees apart, index 0 upright.
    // It is written out as integers precisely so that the Python second implementation
    // has nothing to agree about but the numbers themselves.
    private static readonly int[] ThrustTableX = { 0, 2, 3, 4, 3, 2, 0, -2, -3, -4, -3, -2 };
    private static readonly int[] ThrustTableY = { -4, -3, -2, 0, 2, 3, 4, 3, 2, 0, -2, -3 };
    private static readonly int[] PadX0 = { 120, 360, 600 };
    private static readonly int[] PadX1 = { 200, 440, 680 };
    private static readonly int[] PadMult = { 1, 2, 1 };

    // --- private model ---------------------------------------------------------------
    private Label _hud;
    private Label _status;
    private ColorRect _lander;
    private ColorRect _flame;
    private readonly List<ColorRect> _decor = new List<ColorRect>();
    private readonly List<ColorRect> _padRects = new List<ColorRect>();
    private readonly List<ColorRect> _stars = new List<ColorRect>();
    private float _autoAccum;
    private bool _prevThrust;
    private const int StarCount = 56;

    private int PadOf(int x)
    {
        for (var i = 0; i < PadX0.Length; i++)
        {
            if (x >= PadX0[i] && x <= PadX1[i])
            {
                return i;
            }
        }
        return -1;
    }

    private int AngleDistanceFromUpright()
    {
        var forward = AngleIndex;
        var backward = AngleCount - AngleIndex;
        return forward < backward ? forward : backward;
    }

    private void RefreshTable()
    {
        ThrustX = ThrustTableX[AngleIndex];
        ThrustY = ThrustTableY[AngleIndex];
        AngleDeg = AngleIndex * AngleStepDeg;
        var pads = new StringBuilder();
        for (var i = 0; i < PadX0.Length; i++)
        {
            if (i > 0)
            {
                pads.Append('|');
            }
            pads.Append(PadX0[i]).Append(',').Append(PadX1[i]);
        }
        PadList = pads.ToString();
        PadMultipliers = string.Join(",", PadMult);
    }

    // --- the rules --------------------------------------------------------------------

    private void CheckEnd()
    {
        if (GameOver)
        {
            return;
        }
        if (Ly + HalfH >= GroundY)
        {
            TouchY = Ly;
            PadIndex = PadOf(Lx);
            Landed = PadIndex >= 0
                     && System.Math.Abs(Vx) <= MaxLandVx
                     && System.Math.Abs(Vy) <= MaxLandVy
                     && AngleDistanceFromUpright() <= MaxLandAngle;
            Crashed = !Landed;
            Won = Landed;
            GameOver = true;
            Score = Landed ? Fuel * PadMult[PadIndex] : 0;
            LastEvent = Landed
                ? $"landed pad={PadIndex} x={Lx} y={Ly} vx={Vx} vy={Vy} angle={AngleDeg} fuel={Fuel} score={Score}"
                : $"crashed x={Lx} y={Ly} vx={Vx} vy={Vy} angle={AngleDeg} pad={PadIndex} fuel={Fuel}";
            return;
        }
        if (Lx < 0 || Lx >= FieldW)
        {
            TouchY = Ly;
            Crashed = true;
            Won = false;
            GameOver = true;
            PadIndex = -1;
            Score = 0;
            LastEvent = $"crashed reason=out_of_field x={Lx} y={Ly} vx={Vx} vy={Vy}";
        }
    }

    /// <summary>One fixed simulation step: burn, gravity, integrate, then the ground test.</summary>
    private void Tick()
    {
        if (GameOver)
        {
            return;
        }
        Steps++;
        if (ThrustOn && Fuel >= ThrustCost)
        {
            Vx += ThrustTableX[AngleIndex];
            Vy += ThrustTableY[AngleIndex];
            Fuel -= ThrustCost;
            FuelUsed += ThrustCost;
            ThrustCount++;
        }
        Vy += GravityStep;
        Lx += Vx;
        Ly += Vy;
        if (Vy < MinVy)
        {
            MinVy = Vy;
        }
        if (Vy > MaxVy)
        {
            MaxVy = Vy;
        }
        CheckEnd();
        if (!GameOver)
        {
            LastEvent = $"flight x={Lx} y={Ly} vx={Vx} vy={Vy} fuel={Fuel} steps={Steps}";
        }
    }

    private void Recompute()
    {
        RefreshTable();
        var hash = 0;
        hash = unchecked(hash * 31 + Lx);
        hash = unchecked(hash * 31 + Ly);
        hash = unchecked(hash * 31 + Vx);
        hash = unchecked(hash * 31 + Vy);
        hash = unchecked(hash * 31 + AngleIndex);
        hash = unchecked(hash * 31 + Fuel);
        hash = unchecked(hash * 31 + Steps);
        StateHash = hash;
    }

    // --- nodes -------------------------------------------------------------------------

    private void FreeGenerated()
    {
        foreach (var list in new[] { _decor, _padRects, _stars })
        {
            foreach (var node in list)
            {
                if (GodotObject.IsInstanceValid(node))
                {
                    node.GetParent()?.RemoveChild(node);
                    node.QueueFree();
                }
            }
            list.Clear();
        }
        foreach (var node in new[] { _lander, _flame })
        {
            if (node != null && GodotObject.IsInstanceValid(node))
            {
                node.GetParent()?.RemoveChild(node);
                node.QueueFree();
            }
        }
        _lander = null;
        _flame = null;
    }

    /// <summary>Builds the ground, the three pads, the starfield, the lander and the flame.</summary>
    private void CreateNodes()
    {
        _hud = GetNodeOrNull<Label>("Hud");
        _status = GetNodeOrNull<Label>("Status");
        FreeGenerated();
        for (var i = 0; i < StarCount; i++)
        {
            var x = (i * 149) % FieldW;
            var y = ((i * 197) % (GroundY - 40)) + 30;
            var rect = new ColorRect
            {
                Name = $"Star_{i}",
                Position = new Vector2(x, y),
                Size = new Vector2(2, 2),
                Color = i % 4 == 0 ? new Color(0.75f, 0.78f, 0.90f) : new Color(0.32f, 0.34f, 0.42f),
            };
            AddChild(rect);
            _stars.Add(rect);
        }
        var ground = new ColorRect
        {
            Name = "Ground",
            Position = new Vector2(0, GroundY),
            Size = new Vector2(FieldW, FieldH - GroundY),
            Color = new Color(0.30f, 0.28f, 0.26f),
        };
        AddChild(ground);
        _decor.Add(ground);
        for (var i = 0; i < PadX0.Length; i++)
        {
            var rect = new ColorRect
            {
                Name = $"Pad_{i}",
                Position = new Vector2(PadX0[i], GroundY - 4),
                Size = new Vector2(PadX1[i] - PadX0[i], 8),
                Color = PadMult[i] > 1 ? new Color(0.95f, 0.80f, 0.25f) : new Color(0.45f, 0.85f, 0.95f),
            };
            AddChild(rect);
            _padRects.Add(rect);
        }
        _lander = new ColorRect
        {
            Name = "Lander",
            Position = new Vector2(Lx - HalfW, Ly - HalfH),
            Size = new Vector2(HalfW * 2, HalfH * 2),
            Color = new Color(0.90f, 0.92f, 0.95f),
        };
        AddChild(_lander);
        _flame = new ColorRect
        {
            Name = "Flame",
            Position = new Vector2(Lx - 4, Ly + HalfH),
            Size = new Vector2(8, 14),
            Color = new Color(0.98f, 0.55f, 0.20f),
            Visible = false,
        };
        AddChild(_flame);
    }

    /// <summary>Puts every sprite where the model says it is, and rewrites the HUD.</summary>
    private void ApplyBoard()
    {
        if (_lander != null)
        {
            _lander.Position = new Vector2(Lx - HalfW, Ly - HalfH);
            _lander.Color = GameOver
                ? (Won ? new Color(0.45f, 0.95f, 0.55f) : new Color(0.95f, 0.35f, 0.35f))
                : new Color(0.90f, 0.92f, 0.95f);
        }
        if (_flame != null)
        {
            _flame.Visible = ThrustOn && Fuel >= ThrustCost && !GameOver;
            _flame.Position = new Vector2(Lx - 4, Ly + HalfH);
        }
        if (_hud != null)
        {
            var altitude = GroundY - (Ly + HalfH);
            _hud.Text = $"ALT {altitude}  VX {Vx}  VY {Vy}  FUEL {Fuel}  ANGLE {AngleDeg}  "
                        + $"BURNS {ThrustCount}  STEP {Steps}";
        }
        if (_status != null)
        {
            _status.Text = GameOver
                ? (Won ? "THE EAGLE HAS LANDED" : "CRASH")
                : "LAND SAFELY";
        }
    }

    public override void _Ready()
    {
        CreateNodes();
        ResetCounters();
        Recompute();
        ApplyBoard();
        GD.Print($"LUNARLANDER_READY name={Name} ground={GroundY} pads={PadList} state_hash={StateHash}");
    }

    private void ResetCounters()
    {
        Lx = StartX;
        Ly = StartY;
        Vx = 0;
        Vy = 0;
        AngleIndex = 0;
        Fuel = StartFuel;
        ThrustOn = false;
        ThrustCount = 0;
        FuelUsed = 0;
        Rotations = 0;
        RejectedThrusts = 0;
        RejectedRotations = 0;
        Landed = false;
        Crashed = false;
        Won = false;
        GameOver = false;
        PadIndex = -1;
        Score = 0;
        TouchY = 0;
        MinVy = 0;
        MaxVy = 0;
        Steps = 0;
        Elapsed = 0.0f;
        Ticks = 0;
        AutoClock = 0.0f;
        AutoTicks = 0;
        LastAutoSteps = 0;
        LastHookSteps = 0;
        _autoAccum = 0.0f;
        PollInput = false;
        InputThrusts = 0;
        _prevThrust = false;
        ProbeX = -1;
        ProbeY = -1;
        ProbeValue = -1;
        ProbeState = "";
        RefreshTable();
        LastEvent = "reset";
    }

    // --- the public surface a session drives ---------------------------------------------

    /// <summary>
    /// Runs <paramref name="steps"/> fixed simulation steps. The hook, and the only frame-rate
    /// independent way to advance the world: <see cref="LastHookSteps"/> is its own property.
    /// </summary>
    public string StepFrames(int steps)
    {
        var applied = 0;
        for (var i = 0; i < steps; i++)
        {
            if (GameOver)
            {
                break;
            }
            Tick();
            applied++;
        }
        LastHookSteps = applied;
        Recompute();
        ApplyBoard();
        LastEvent = $"stepframes requested={steps} applied={applied} steps={Steps} x={Lx} y={Ly} "
                    + $"vx={Vx} vy={Vy} fuel={Fuel} angle={AngleDeg} burns={ThrustCount} "
                    + $"over={GameOver} won={Won} crashed={Crashed} min_vy={MinVy} max_vy={MaxVy}";
        return LastEvent;
    }

    /// <summary>One burn: adds the attitude's thrust pair and spends the fuel, or refuses.</summary>
    public string Thrust()
    {
        if (GameOver)
        {
            RejectedThrusts++;
            LastEvent = $"rejected reason=game_over burns={ThrustCount}";
            return LastEvent;
        }
        if (Fuel < ThrustCost)
        {
            RejectedThrusts++;
            LastEvent = $"rejected reason=no_fuel fuel={Fuel} cost={ThrustCost}";
            return LastEvent;
        }
        Vx += ThrustTableX[AngleIndex];
        Vy += ThrustTableY[AngleIndex];
        Fuel -= ThrustCost;
        FuelUsed += ThrustCost;
        ThrustCount++;
        Recompute();
        ApplyBoard();
        LastEvent = $"burn tx={ThrustX} ty={ThrustY} vx={Vx} vy={Vy} fuel={Fuel} burns={ThrustCount}";
        return LastEvent;
    }

    /// <summary>Turns the continuous burn on or off; <see cref="Tick"/> applies it every step.</summary>
    public string SetThrust(bool enabled)
    {
        ThrustOn = enabled;
        LastEvent = $"thrust_on={ThrustOn} fuel={Fuel}";
        return LastEvent;
    }

    /// <summary>Turns the attitude one step clockwise.</summary>
    public string RotateRight()
    {
        if (GameOver)
        {
            RejectedRotations++;
            LastEvent = $"rejected reason=game_over angle={AngleDeg}";
            return LastEvent;
        }
        AngleIndex = (AngleIndex + 1) % AngleCount;
        Rotations++;
        Recompute();
        ApplyBoard();
        LastEvent = $"rotated angle={AngleDeg} tx={ThrustX} ty={ThrustY} rotations={Rotations}";
        return LastEvent;
    }

    /// <summary>Turns the attitude one step anticlockwise.</summary>
    public string RotateLeft()
    {
        if (GameOver)
        {
            RejectedRotations++;
            LastEvent = $"rejected reason=game_over angle={AngleDeg}";
            return LastEvent;
        }
        AngleIndex = (AngleIndex + AngleCount - 1) % AngleCount;
        Rotations++;
        Recompute();
        ApplyBoard();
        LastEvent = $"rotated angle={AngleDeg} tx={ThrustX} ty={ThrustY} rotations={Rotations}";
        return LastEvent;
    }

    /// <summary>Records what stands at one field point into the Probe* properties.</summary>
    public string Probe(int x, int y)
    {
        ProbeX = x;
        ProbeY = y;
        ProbeValue = -1;
        if (x < 0 || x >= FieldW || y < 0 || y >= FieldH)
        {
            ProbeState = "outside";
        }
        else if (x >= Lx - HalfW && x < Lx + HalfW && y >= Ly - HalfH && y < Ly + HalfH)
        {
            ProbeState = "lander";
        }
        else if (y >= GroundY)
        {
            var pad = PadOf(x);
            if (pad >= 0)
            {
                ProbeState = "pad";
                ProbeValue = pad;
            }
            else
            {
                ProbeState = "ground";
            }
        }
        else
        {
            ProbeState = "sky";
        }
        LastEvent = $"probe at={x},{y} state={ProbeState} value={ProbeValue}";
        return LastEvent;
    }

    /// <summary>Steps per second; 0 keeps the world still (the default).</summary>
    public string SetAutoClock(float perSecond)
    {
        AutoClock = perSecond;
        _autoAccum = 0.0f;
        LastAutoSteps = 0;
        LastEvent = $"auto_clock={AutoClock}";
        GD.Print($"LUNARLANDER_AUTO auto={AutoClock}");
        return LastEvent;
    }

    /// <summary>Switches the declared-input polling on or off (the default is off).</summary>
    public string SetPollInput(bool enabled)
    {
        PollInput = enabled;
        _prevThrust = false;
        LastEvent = $"poll_input={PollInput}";
        return LastEvent;
    }

    private void HandleInput()
    {
        var thrust = Input.IsActionPressed("ll_thrust");
        // Press edges only: a key a scenario injected and never released burns exactly once.
        if (thrust && !_prevThrust && !GameOver)
        {
            Thrust();
            InputThrusts++;
        }
        _prevThrust = thrust;
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
                Tick();
                applied++;
                if (GameOver)
                {
                    break;
                }
            }
            AutoTicks += applied;
            LastAutoSteps = applied;
            if (applied > 0)
            {
                // The clock deliberately does NOT touch LastHookSteps (the G1 lesson).
                Recompute();
                ApplyBoard();
            }
        }
        else
        {
            LastAutoSteps = 0;
        }
    }

    /// <summary>Every exported fact on one line.</summary>
    public string Dump()
    {
        return $"field={FieldW}x{FieldH} ground={GroundY} half={HalfW},{HalfH} gravity={GravityStep} "
               + $"fuel_start={StartFuel} cost={ThrustCost} angles={AngleCount} angle_step={AngleStepDeg} "
               + $"pads={PadList} mult={PadMultipliers} max_vx={MaxLandVx} max_vy={MaxLandVy} "
               + $"max_angle={MaxLandAngle} pos={Lx},{Ly} vel={Vx},{Vy} angle={AngleDeg} "
               + $"angle_index={AngleIndex} thrust={ThrustX},{ThrustY} fuel={Fuel} used={FuelUsed} "
               + $"thrust_on={ThrustOn} burns={ThrustCount} rotations={Rotations} landed={Landed} "
               + $"crashed={Crashed} won={Won} over={GameOver} pad={PadIndex} score={Score} "
               + $"touch_y={TouchY} min_vy={MinVy} max_vy={MaxVy} state_hash={StateHash} steps={Steps} "
               + $"auto={AutoClock} auto_ticks={AutoTicks} last_auto={LastAutoSteps} "
               + $"last_hook={LastHookSteps} input_thrusts={InputThrusts} elapsed={Elapsed:F3} "
               + $"ticks={Ticks} last={LastEvent}";
    }

    /// <summary>
    /// Writes the whole deterministic state in one call. Recognised keys (semicolon separated,
    /// <c>key=value</c>):
    ///
    /// <list type="bullet">
    /// <item><c>l=X,Y</c> -- the lander's centre; <c>v=VX,VY</c> -- its velocity;</item>
    /// <item><c>angle=N</c> -- the attitude index; <c>fuel=N</c>; <c>score=N</c>;</item>
    /// <item><c>thrust=0|1</c> -- the continuous burn flag.</item>
    /// </list>
    ///
    /// <para>Pinning the position and the velocity just above the ground is what makes a single-step
    /// landing assertion a statement about a state the session itself chose.</para>
    /// </summary>
    public string ForceTestState(string spec)
    {
        ResetCounters();
        foreach (var part in spec.Split(';'))
        {
            var kv = part.Split(new[] { '=' }, 2);
            if (kv.Length != 2)
            {
                continue;
            }
            switch (kv[0])
            {
                case "l":
                    var pos = kv[1].Split(',');
                    Lx = int.Parse(pos[0]);
                    Ly = int.Parse(pos[1]);
                    break;
                case "v":
                    var vel = kv[1].Split(',');
                    Vx = int.Parse(vel[0]);
                    Vy = int.Parse(vel[1]);
                    break;
                case "angle":
                    var angle = int.Parse(kv[1]);
                    AngleIndex = angle < 0 ? 0 : angle >= AngleCount ? AngleCount - 1 : angle;
                    break;
                case "fuel":
                    Fuel = int.Parse(kv[1]);
                    break;
                case "score":
                    Score = int.Parse(kv[1]);
                    break;
                case "thrust":
                    ThrustOn = kv[1] == "1";
                    break;
            }
        }
        MinVy = Vy;
        MaxVy = Vy;
        Recompute();
        ApplyBoard();
        LastEvent = $"forced pos={Lx},{Ly} vel={Vx},{Vy} angle={AngleDeg} fuel={Fuel} thrust_on={ThrustOn} "
                    + $"score={Score}";
        return LastEvent;
    }
}
