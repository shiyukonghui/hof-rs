using Godot;
using System.Collections.Generic;
using System.Text;

namespace flappy;

/// <summary>
/// Flappy Bird -- the ninth C# game of the godot-mcp series (TASK-099, DECISIONS.md D138).
///
/// <para><b>Design rule</b> (inherited from Pong / Breakout / Snake / Tetris / Space Invaders /
/// Asteroids / Pac-Man / Frogger): every fact the evidence model needs is a real Godot property on
/// the root node -- <see cref="BirdY"/>, <see cref="BirdVelocity"/>, <see cref="BirdX"/>,
/// <see cref="Score"/>, <see cref="PipesPassed"/>, <see cref="FrameCount"/>, <see cref="Pipe0X"/>,
/// <see cref="Pipe0GapY"/>, <see cref="GameOver"/>, <see cref="Won"/>, <see cref="Ticks"/>. A
/// session asserts these with <c>running_game_assert_node_state</c>; it never parses a log line.</para>
///
/// <para><b>Determinism rule.</b> The world does NOT advance by itself: <see cref="AutoRun"/> is
/// false by default, so <c>_Process</c> only counts <see cref="Ticks"/>. Everything the game does
/// is reachable through fixed-step hooks: <see cref="Flap"/>, <see cref="StepFrames"/>,
/// <see cref="StepUntilPass"/>. That is what makes "the bird rose after a flap" or "the third pipe
/// was passed" a property of the calls rather than of the machine's frame rate.</para>
///
/// <para><b>One fixed frame is 1/60 s.</b> Gravity, velocity and pipe motion are integrated on
/// that exact step, so <see cref="StepFrames"/> is reproducible to the last pixel.</para>
///
/// <para><b>The bird and the pipes are all runtime-created.</b> <see cref="_Ready"/> builds the
/// bird and three pipes as <c>ColorRect</c>s; the scene file carries only the three static nodes
/// (Background, Hud, Status), which keeps the edited scene immune to the D-3 duplicate-name
/// trap and makes "a node created at run time really is drawn" part of this game's evidence.</para>
///
/// <para><b>Scoring has exactly one source.</b> One pipe passed = 10 points; nothing else scores.
/// Five pipes clear the course.</para>
/// </summary>
public partial class FlappyBirdGame : Node2D
{
    // --- the fixed step ---------------------------------------------------------
    /// <summary>Frames per simulated second. One <see cref="StepFrames"/> step is 1/60 of this.</summary>
    [Export] public float FixedFps = 60.0f;

    // --- the bird ---------------------------------------------------------------
    /// <summary>The bird's left edge in pixels.</summary>
    [Export] public float BirdX = 180.0f;

    /// <summary>The bird's top edge in pixels.</summary>
    [Export] public float BirdY = 300.0f;

    /// <summary>The bird's vertical velocity in pixels per second (positive = falling).</summary>
    [Export] public float BirdVelocity = 0.0f;

    /// <summary>The bird's square size in pixels.</summary>
    [Export] public float BirdSize = 36.0f;

    /// <summary>Downward acceleration in pixels per second squared.</summary>
    [Export] public float Gravity = 1400.0f;

    /// <summary>The upward velocity a flap gives, in pixels per second (positive number).</summary>
    [Export] public float FlapImpulse = 420.0f;

    // --- the pipes --------------------------------------------------------------
    /// <summary>Width of one pipe in pixels.</summary>
    [Export] public float PipeWidth = 70.0f;

    /// <summary>The vertical opening between a pipe's two halves, in pixels.</summary>
    [Export] public float GapSize = 160.0f;

    /// <summary>Horizontal distance between two pipe centres, in pixels.</summary>
    [Export] public float PipeSpacing = 300.0f;

    /// <summary>Pipe speed in pixels per second (the world scrolls left).</summary>
    [Export] public float PipeSpeed = 180.0f;

    /// <summary>How many pipes are on the screen at once.</summary>
    [Export] public int PipeCount = 0;

    /// <summary>Left edge of pipe 0 -- a real property, so a sample can show the world scroll.</summary>
    [Export] public float Pipe0X = -1.0f;

    /// <summary>Centre y of pipe 0's gap.</summary>
    [Export] public float Pipe0GapY = -1.0f;

    /// <summary>World height; falling past it is the ground hit.</summary>
    [Export] public float WorldHeight = 600.0f;

    // --- observable state, all of it a real Godot property ---------------------
    /// <summary>Points: 10 per pipe passed.</summary>
    [Export] public int Score = 0;

    /// <summary>Pipes passed so far.</summary>
    [Export] public int PipesPassed = 0;

    /// <summary>Pipes recycled to the right edge so far.</summary>
    [Export] public int PipesRecycled = 0;

    /// <summary>Pipes needed to clear the course.</summary>
    [Export] public int PipesToClear = 5;

    /// <summary>Fixed frames simulated since the last reset (not the engine's frame count).</summary>
    [Export] public int FrameCount = 0;

    /// <summary>Frames the LAST <see cref="StepUntilPass"/> call took to the next pass.</summary>
    [Export] public int LastPassFrames = 0;

    /// <summary>Pipes the LAST <see cref="StepUntilPass"/> call produced (0 when it timed out).</summary>
    [Export] public int LastPassDelta = 0;

    /// <summary>True after a pipe hit, a ground hit or the cleared course.</summary>
    [Export] public bool GameOver = false;

    /// <summary>True when <see cref="GameOver"/> was reached by passing every pipe.</summary>
    [Export] public bool Won = false;

    /// <summary>When false (the default) the world only advances through the step hooks.</summary>
    [Export] public bool AutoRun = false;

    /// <summary>When true the game reads its player's keyboard. The test driver switches this
    /// OFF explicitly (<see cref="SetPollInput"/>, <see cref="ForceTestState"/>) when it needs
    /// a frozen, deterministic state; the deterministic defaults live in AutoClock / AutoPlay /
    /// DriftSpeed, not here (TASK-116 defect D1).</summary>
    [Export] public bool PollInput = true;

    /// <summary>Restarts that arrived through the declared `flappy_restart` action (TASK-116 D11).</summary>
    [Export] public int Restarts = 0;

    /// <summary>Engine frames processed since the last reset (the clock, not the simulation).</summary>
    [Export] public int Ticks = 0;

    /// <summary>What the last hook did -- the readback string a session quotes.</summary>
    [Export] public string LastEvent = "";

    // --- private model ---------------------------------------------------------
    private class Pipe
    {
        public float X;
        public float GapY;
        public bool Passed;
        public ColorRect Top;
        public ColorRect Bottom;
    }

    private readonly List<Pipe> _pipes = new List<Pipe>();
    private ColorRect _bird;
    private ColorRect _bg;
    private Label _hud;
    private Label _status;
    private float _autoAccum;

    /// <summary>Where the three pipes start: x and the gap centre, both fixed.</summary>
    private static readonly float[,] PipeStart =
    {
        { 600.0f, 300.0f }, { 900.0f, 210.0f }, { 1200.0f, 390.0f },
    };

    public override void _Ready()
    {
        _bg = GetNodeOrNull<ColorRect>("Background");
        _hud = GetNodeOrNull<Label>("Hud");
        _status = GetNodeOrNull<Label>("Status");
        BuildWorld();
        UpdateHud();
        GD.Print($"FLAPPY_READY pipes={PipeCount} bird={BirdX},{BirdY} gravity={Gravity} "
                 + $"speed={PipeSpeed} auto={AutoRun}");
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
    /// Removes a runtime node from the tree and then frees it. The order is the D-3 trap: a
    /// <c>QueueFree()</c> alone leaves the name taken until the end of the frame, and a rebuild
    /// that recreates <c>Pipe_0_Top</c> in the same frame would get <c>@ColorRect@NNN</c> instead.
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

    private void BuildWorld()
    {
        foreach (var child in GetChildren())
        {
            var node = child as Node;
            if (node == null)
            {
                continue;
            }
            var name = node.Name.ToString();
            if (name == "Hud" || name == "Status" || name == "Background" || name == "Bird")
            {
                continue;
            }
            DropNode(node);
        }
        _pipes.Clear();
        for (var i = 0; i < PipeStart.GetLength(0); i++)
        {
            var pipe = new Pipe { X = PipeStart[i, 0], GapY = PipeStart[i, 1], Passed = false };
            pipe.Top = MakeRect($"Pipe_{i}_Top", new Vector2(PipeWidth, 10.0f),
                                new Color(0.25f, 0.80f, 0.30f));
            pipe.Bottom = MakeRect($"Pipe_{i}_Bottom", new Vector2(PipeWidth, 10.0f),
                                   new Color(0.25f, 0.80f, 0.30f));
            _pipes.Add(pipe);
        }
        if (_bird == null || !IsInstanceValid(_bird))
        {
            _bird = MakeRect("Bird", new Vector2(BirdSize, BirdSize), new Color(0.98f, 0.80f, 0.15f));
        }
        PipeCount = _pipes.Count;
        BirdY = 300.0f;
        BirdVelocity = 0.0f;
        ApplyBird();
        ApplyPipes();
    }

    private void ApplyBird()
    {
        if (_bird == null)
        {
            return;
        }
        _bird.Position = new Vector2(BirdX, BirdY);
    }

    /// <summary>Places both halves of every pipe from its x and gap centre.</summary>
    private void ApplyPipes()
    {
        foreach (var pipe in _pipes)
        {
            var gapTop = pipe.GapY - GapSize / 2.0f;
            var gapBottom = pipe.GapY + GapSize / 2.0f;
            if (pipe.Top != null)
            {
                pipe.Top.Position = new Vector2(pipe.X, 0.0f);
                pipe.Top.Size = new Vector2(PipeWidth, gapTop);
            }
            if (pipe.Bottom != null)
            {
                pipe.Bottom.Position = new Vector2(pipe.X, gapBottom);
                pipe.Bottom.Size = new Vector2(PipeWidth, WorldHeight - gapBottom);
            }
        }
        if (_pipes.Count > 0)
        {
            Pipe0X = _pipes[0].X;
            Pipe0GapY = _pipes[0].GapY;
        }
        else
        {
            Pipe0X = -1.0f;
            Pipe0GapY = -1.0f;
        }
    }

    private void UpdateHud()
    {
        if (_hud != null)
        {
            _hud.Text = $"SCORE {Score}  PASSED {PipesPassed}/{PipesToClear}  FRAME {FrameCount}";
        }
        if (_status != null)
        {
            _status.Text = GameOver ? (Won ? "COURSE CLEARED" : "GAME OVER")
                                    : $"PIPES {PipesPassed}/{PipesToClear}";
        }
    }

    public override void _Process(double delta)
    {
        Ticks++;
        if (PollInput && Input.IsActionPressed("flappy_restart"))
        {
            // TASK-116 D11: the restart is observable even from a fresh game. Before this
            // counter it only wrote values that were already at their defaults, so "the R key
            // restarts" had no evidence a machine (or a player) could see.
            Restarts++;
            AutoRun = false;
            _autoAccum = 0.0f;
            Score = 0;
            PipesPassed = 0;
            PipesRecycled = 0;
            FrameCount = 0;
            LastPassFrames = 0;
            LastPassDelta = 0;
            GameOver = false;
            Won = false;
            BuildWorld();
            UpdateHud();
            LastEvent = "restarted by the declared action";
            return;
        }
        if (PollInput && !GameOver && Input.IsActionJustPressed("flap"))
        {
            Flap();
        }
        if (!AutoRun || GameOver)
        {
            return;
        }
        // The clock is an ACCUMULATOR, not `(int)(delta * FixedFps)`: on this machine the
        // windowed game process runs well above 60 fps, so a single frame's delta is a
        // fraction of a fixed frame and truncating it turns the self-running clock into a
        // clock that never ticks (found by the Flappy run-1 `g44` multi-frame sample: Ticks
        // advanced while Pipe0X stood still). The accumulator keeps the total simulated time
        // equal to the wall time the process actually spent.
        _autoAccum += (float)delta * FixedFps;
        var frames = (int)_autoAccum;
        if (frames > 0)
        {
            _autoAccum -= frames;
            StepFrames(frames);
        }
    }

    /// <summary>True when the bird's box and the pipe's two boxes share any pixel.</summary>
    private bool HitsPipe(Pipe pipe)
    {
        var left = BirdX;
        var right = BirdX + BirdSize;
        var top = BirdY;
        var bottom = BirdY + BirdSize;
        if (right <= pipe.X || left >= pipe.X + PipeWidth)
        {
            return false;
        }
        var gapTop = pipe.GapY - GapSize / 2.0f;
        var gapBottom = pipe.GapY + GapSize / 2.0f;
        if (bottom <= gapTop)
        {
            return true;
        }
        if (top >= gapBottom)
        {
            return true;
        }
        return false;
    }

    /// <summary>One exact 1/60 s frame of the whole world.</summary>
    private void StepOnce()
    {
        var dt = 1.0f / FixedFps;
        BirdVelocity += Gravity * dt;
        BirdY += BirdVelocity * dt;
        if (BirdY < 0.0f)
        {
            BirdY = 0.0f;
            if (BirdVelocity < 0.0f)
            {
                BirdVelocity = 0.0f;
            }
        }
        FrameCount++;
        var maxX = 0.0f;
        foreach (var pipe in _pipes)
        {
            pipe.X -= PipeSpeed * dt;
            if (pipe.X > maxX)
            {
                maxX = pipe.X;
            }
        }
        foreach (var pipe in _pipes)
        {
            if (pipe.X + PipeWidth < 0.0f)
            {
                pipe.X = maxX + PipeSpacing;
                pipe.Passed = false;
                maxX = pipe.X;
                PipesRecycled++;
            }
        }
        foreach (var pipe in _pipes)
        {
            if (!pipe.Passed && pipe.X + PipeWidth < BirdX)
            {
                pipe.Passed = true;
                PipesPassed++;
                Score += 10;
                LastEvent = $"pipe passed at={pipe.X:F1} gap={pipe.GapY:F0} passed={PipesPassed} score={Score}";
                if (PipesPassed >= PipesToClear)
                {
                    Won = true;
                    GameOver = true;
                    LastEvent += " course cleared";
                }
            }
        }
        if (!GameOver)
        {
            foreach (var pipe in _pipes)
            {
                if (HitsPipe(pipe))
                {
                    GameOver = true;
                    Won = false;
                    LastEvent = $"pipe hit at={pipe.X:F1} bird={BirdX:F0},{BirdY:F1}";
                    break;
                }
            }
        }
        if (!GameOver && BirdY + BirdSize >= WorldHeight)
        {
            BirdY = WorldHeight - BirdSize;
            GameOver = true;
            Won = false;
            LastEvent = $"ground hit bird_y={BirdY:F1} frames={FrameCount}";
        }
        ApplyBird();
        ApplyPipes();
        UpdateHud();
    }

    // --- hooks the session drives ----------------------------------------------

    /// <summary>A flap: the bird's velocity becomes the upward impulse, exactly.</summary>
    public string Flap()
    {
        if (GameOver)
        {
            LastEvent = "flap refused: game over";
            return LastEvent;
        }
        BirdVelocity = -FlapImpulse;
        LastEvent = $"flap velocity={BirdVelocity:F0} bird_y={BirdY:F1}";
        return LastEvent;
    }

    /// <summary>Advances the world by an exact number of 1/60 s frames.</summary>
    public string StepFrames(int frames)
    {
        var taken = 0;
        for (var i = 0; i < frames && !GameOver; i++)
        {
            StepOnce();
            taken++;
        }
        LastEvent = $"stepped={taken} of={frames} frames={FrameCount} bird_y={BirdY:F1} "
                    + $"vel={BirdVelocity:F1} pipes_passed={PipesPassed} over={GameOver}";
        return LastEvent;
    }

    /// <summary>
    /// Steps one frame at a time until the next pipe is passed, the game ends or
    /// <paramref name="maxFrames"/> is spent. Deterministic: the frame count it took is
    /// <see cref="LastPassFrames"/> and how many pipes it produced is <see cref="LastPassDelta"/>.
    /// </summary>
    public string StepUntilPass(int maxFrames)
    {
        var start = PipesPassed;
        var taken = 0;
        while (taken < maxFrames && !GameOver && PipesPassed == start)
        {
            StepOnce();
            taken++;
        }
        LastPassFrames = taken;
        LastPassDelta = PipesPassed - start;
        LastEvent = $"until_pass took={LastPassFrames} delta={LastPassDelta} passed={PipesPassed} "
                    + $"frame={FrameCount} bird_y={BirdY:F1} over={GameOver} won={Won}";
        return LastEvent;
    }

    /// <summary>Gravity in pixels per second squared.</summary>
    public string SetGravity(float value)
    {
        Gravity = value;
        LastEvent = $"gravity={Gravity}";
        GD.Print($"FLAPPY_GRAVITY gravity={Gravity}");
        return LastEvent;
    }

    /// <summary>Pipe speed in pixels per second.</summary>
    public string SetPipeSpeed(float value)
    {
        PipeSpeed = value;
        LastEvent = $"pipe speed={PipeSpeed}";
        GD.Print($"FLAPPY_SPEED speed={PipeSpeed}");
        return LastEvent;
    }

    /// <summary>Switches the self-running clock on or off (the default is off).</summary>
    public string SetAutoRun(bool enabled)
    {
        AutoRun = enabled;
        _autoAccum = 0.0f;
        LastEvent = $"auto_run={AutoRun}";
        return LastEvent;
    }

    /// <summary>Switches the bird's input polling on or off (the default is off).</summary>
    public string SetPollInput(bool enabled)
    {
        PollInput = enabled;
        LastEvent = $"poll_input={PollInput}";
        return LastEvent;
    }

    /// <summary>The world as a readable one-liner plus every exported fact.</summary>
    public string Dump()
    {
        var sb = new StringBuilder();
        foreach (var pipe in _pipes)
        {
            sb.Append($"pipe[{pipe.X:F1},{pipe.GapY:F0}{(pipe.Passed ? ",P" : "")}] ");
        }
        return $"pipes={sb}bird={BirdX:F0},{BirdY:F1} vel={BirdVelocity:F1} size={BirdSize:F0} "
               + $"gap={GapSize:F0} width={PipeWidth:F0} speed={PipeSpeed:F0} gravity={Gravity:F0} "
               + $"score={Score} passed={PipesPassed}/{PipesToClear} recycled={PipesRecycled} "
               + $"frame={FrameCount} frames_hook={LastPassFrames} delta_hook={LastPassDelta} "
               + $"over={GameOver} won={Won} auto={AutoRun} ticks={Ticks} last={LastEvent}";
    }

    /// <summary>The readback shortcuts: where the bird is and where pipe 0 is.</summary>
    public string Geometry()
    {
        return $"bird={BirdX:F0},{BirdY:F1} vel={BirdVelocity:F1} pipe0={Pipe0X:F1},{Pipe0GapY:F0} "
               + $"passed={PipesPassed} frame={FrameCount}";
    }

    /// <summary>
    /// Writes the whole deterministic state in one call --
    /// <c>"bird=y,vy;pipes=all|none|x:gapY|...;score=n;passed=n;frames=n;gravity=g;speed=s"</c>.
    ///
    /// <para>Keys may be omitted; the ones given are applied. The self-running clock is switched
    /// OFF here, so a session's aim and the next readback are the same fact.</para>
    /// </summary>
    public string ForceTestState(string spec)
    {
        AutoRun = false;
        PollInput = false;
        _autoAccum = 0.0f;
        Ticks = 0;
        Score = 0;
        PipesPassed = 0;
        PipesRecycled = 0;
        FrameCount = 0;
        LastPassFrames = 0;
        LastPassDelta = 0;
        GameOver = false;
        Won = false;
        BuildWorld();
        foreach (var part in spec.Split(';'))
        {
            var kv = part.Split(new[] { '=' }, 2);
            if (kv.Length != 2)
            {
                continue;
            }
            switch (kv[0])
            {
                case "bird":
                    {
                        var p = kv[1].Split(',');
                        BirdY = float.Parse(p[0]);
                        BirdVelocity = p.Length > 1 ? float.Parse(p[1]) : 0.0f;
                    }
                    break;
                case "pipes":
                    if (kv[1] == "none")
                    {
                        foreach (var pipe in _pipes)
                        {
                            DropNode(pipe.Top);
                            DropNode(pipe.Bottom);
                        }
                        _pipes.Clear();
                    }
                    else if (kv[1] != "all")
                    {
                        var index = 0;
                        foreach (var cellPart in kv[1].Split('|'))
                        {
                            if (cellPart.Length == 0 || index >= _pipes.Count)
                            {
                                continue;
                            }
                            var p = cellPart.Split(':');
                            _pipes[index].X = float.Parse(p[0]);
                            if (p.Length > 1)
                            {
                                _pipes[index].GapY = float.Parse(p[1]);
                            }
                            _pipes[index].Passed = false;
                            index++;
                        }
                    }
                    break;
                case "score":
                    Score = int.Parse(kv[1]);
                    break;
                case "passed":
                    PipesPassed = int.Parse(kv[1]);
                    break;
                case "frames":
                    FrameCount = int.Parse(kv[1]);
                    break;
                case "gravity":
                    Gravity = float.Parse(kv[1]);
                    break;
                case "speed":
                    PipeSpeed = float.Parse(kv[1]);
                    break;
            }
        }
        PipeCount = _pipes.Count;
        ApplyBird();
        ApplyPipes();
        UpdateHud();
        LastEvent = $"forced bird={BirdX:F0},{BirdY:F1} vel={BirdVelocity:F1} pipes={PipeCount} "
                    + $"score={Score} passed={PipesPassed}/{PipesToClear} gravity={Gravity} speed={PipeSpeed}";
        return LastEvent;
    }
}
