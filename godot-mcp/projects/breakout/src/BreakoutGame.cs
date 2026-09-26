using Godot;

namespace breakout;

/// <summary>
/// Breakout — the second C# game of the godot-mcp series (TASK-093, DECISIONS.md D138).
///
/// <para><b>Design rule</b> (inherited from Pong, D139): the state that decides
/// whether a call worked has to be a Godot property — an <c>[Export]</c> or a node
/// property — so the MCP trace carries it, the ledger judges it, and a pixel diff
/// corroborates it. The score is also mirrored into a <c>Label</c> because
/// <c>running_game_assert_screen_text</c> can only see rendered text; the label
/// and <see cref="Score"/> are written in the same statement, so they cannot drift.</para>
///
/// <para><b>Determinism rule</b> (learned from Pong's run-1 defect P-1): a fresh
/// process does not start playing by itself. The ball is parked on the paddle with
/// a padding of 0 and <c>Launched=false</c>; the test driver spends several seconds
/// bringing both endpoints up and that window must not move anything.</para>
///
/// <para><b>Physics are stepped, not integrated</b>: <see cref="StepSeconds"/> is a
/// fixed step, so one call and one replay move the ball by exactly the same
/// distance. Two speeds are therefore meaningful: <see cref="BallSpeedX"/> /
/// <see cref="BallSpeedY"/> drive the simulation, and the ball is parked with a
/// zero speed while <c>Launched</c> is false.</para>
///
/// <para>Playfield: 800x600. Paddle 96x16 at y=540, ball 14x14, wall of
/// <see cref="Columns"/> x <see cref="Rows"/> bricks, 10 points each.</para>
/// </summary>
public partial class BreakoutGame : Node2D
{
    // --- the playfield, all of it exported so a session can re-aim the test ----
    [Export] public float FieldWidth = 800.0f;
    [Export] public float FieldHeight = 600.0f;

    /// <summary>Ball position at rest: horizontal centre.</summary>
    [Export] public float ParkX = 392.0f;

    /// <summary>Ball position at rest: top edge of the paddle.</summary>
    [Export] public float ParkY = 500.0f;

    /// <summary>Ball position in the field, relative to <see cref="ParkX"/> / <see cref="ParkY"/>.</summary>
    [Export] public float BallX = 0.0f;
    [Export] public float BallY = 0.0f;

    /// <summary>Horizontal ball speed, pixels per second (negative = left).</summary>
    [Export] public float BallSpeedX = 184.0f;

    /// <summary>Vertical ball speed, pixels per second (negative = up).</summary>
    [Export] public float BallSpeedY = -276.0f;

    /// <summary>Speed of one physics step; the simulation advances in whole steps.</summary>
    [Export] public float StepSeconds = 0.02f;

    /// <summary>Bricks in the wall — the width and the height of the rectangle.</summary>
    [Export] public int Columns = 5;
    [Export] public int Rows = 3;

    /// <summary>Vertical band the paddle is allowed to occupy; the ball's rest line.</summary>
    [Export] public float PaddleTop = 540.0f;

    /// <summary>The ball is parked (false) or flying (true).</summary>
    [Export] public bool Launched = false;

    /// <summary>True from the first step that takes the last brick out.</summary>
    [Export] public bool Won = false;

    /// <summary>True when the ball was missed, or after a win.</summary>
    [Export] public bool Over = false;

    /// <summary>Bricks taken out so far.</summary>
    [Export] public int BricksBroken = 0;

    /// <summary>Remaining bricks (computed once in _Ready).</summary>
    [Export] public int BricksRemaining = 0;

    /// <summary>Points scored; 10 per brick.</summary>
    [Export] public int Score = 0;

    /// <summary>The side-effect counter of the whole run, for a fine-grained trace.</summary>
    [Export] public int Ticks = 0;

    /// <summary>Paddle contacts so far — the bounce as a counter, not as a sampled velocity.</summary>
    [Export] public int PaddleBounces = 0;

    public const float BallSize = 14.0f;

    private ColorRect _ball;
    private Paddle _paddle;
    private Label _scoreLabel;
    private Label _statusLabel;
    private Brick[] _bricks = System.Array.Empty<Brick>();
    private float _accum;
    private float _logTimer;

    public override void _Ready()
    {
        _ball = GetNode<ColorRect>("Ball");
        _paddle = GetNode<Paddle>("Paddle");
        _scoreLabel = GetNode<Label>("HudScore");
        _statusLabel = GetNode<Label>("HudStatus");

        var bricks = new System.Collections.Generic.List<Brick>();
        foreach (var child in GetChildren())
        {
            if (child is Brick brick)
            {
                bricks.Add(brick);
            }
        }
        _bricks = bricks.ToArray();
        BricksRemaining = _bricks.Length;

        if (BricksRemaining != Columns * Rows)
        {
            // A scene/target mismatch is a fact worth hunting down, not a silent
            // clamp: the win condition is "every brick of the wall is gone".
            GD.Print($"BREAKOUT_WARN brick_count={BricksRemaining} expected={Columns * Rows}");
        }

        ResetBall();
        WriteHud("");
        GD.Print($"BREAKOUT_READY name={Name} bricks={BricksRemaining} score={Score} "
                 + $"ball={BallX},{BallY} launched={Launched}");
    }

    public override void _Process(double delta)
    {
        if (Over)
        {
            return;
        }

        var dt = (float)delta;

        if (Input.IsActionPressed("breakout_left")) { _paddle.Step(-1.0f, dt); }
        if (Input.IsActionPressed("breakout_right")) { _paddle.Step(1.0f, dt); }

        _accum += dt;
        var guard = 0;
        while (_accum >= StepSeconds && !Over && guard < 64)
        {
            _accum -= StepSeconds;
            guard++;
            SimulateStep();
        }

        TickLog(dt);
    }

    /// <summary>
    /// The injected-input path: the MCP scenario step delivers one press and one
    /// release, so a one-shot press is a discrete nudge of
    /// `Speed * StepSeconds` (the same contract Pong's paddle has).
    /// </summary>
    public override void _Input(InputEvent @event)
    {
        if (@event.IsActionPressed("breakout_left")) { _paddle.Step(-1.0f, StepSeconds); }
        if (@event.IsActionPressed("breakout_right")) { _paddle.Step(1.0f, StepSeconds); }
        if (@event.IsActionPressed("breakout_launch")) { Launch(); }
    }

    /// <summary>Puts the ball back on the paddle, at rest, and re-arms the wall.</summary>
    public void ResetBall()
    {
        BallX = 0.0f;
        BallY = 0.0f;
        Launched = false;
        SyncBall();
    }

    /// <summary>Starts the ball moving from wherever it is parked.</summary>
    public void Launch()
    {
        if (Over)
        {
            return;
        }
        Launched = true;
        GD.Print($"BREAKOUT_LAUNCH ball={BallX},{BallY} speed={BallSpeedX},{BallSpeedY}");
    }

    /// <summary>
    /// Test hook: writes the ball's field position and both speeds in one
    /// transaction, so a session can pin a collision to known coordinates.
    /// The values are properties, not internals — the trace shows exactly what was
    /// written and the next frame's sample shows what came of it.
    ///
    /// <para><b>Coordinates.</b> <paramref name="x"/> / <paramref name="y"/> are
    /// FIELD-relative, i.e. relative to <see cref="ParkX"/> / <see cref="ParkY"/> —
    /// the same space the simulation steps in and the same space the brick and
    /// paddle tests compare against. To aim at a known screen point subtract the
    /// park point: the brick at screen (35,160) is `AimBall(35-ParkX, 160-ParkY,
    /// ...)`. Session defect B-2: the first version of this session passed absolute
    /// coordinates here, put the ball a screen and a half away, and the "brick was
    /// destroyed" assertion then passed on an unrelated brick the unguided ball
    /// happened to hit.</para>
    /// </summary>
    public string AimBall(float x, float y, float vx, float vy)
    {
        BallX = x;
        BallY = y;
        BallSpeedX = vx;
        BallSpeedY = vy;
        Launched = true;
        SyncBall();
        return $"aimed ball={BallX},{BallY} speed={BallSpeedX},{BallSpeedY} launched={Launched}";
    }

    /// <summary>
    /// Test hook: the paddle/ball contact test evaluated on demand, plus the numbers
    /// it is made of. A session whose assertion disagrees with its aim needs to be
    /// able to ask "what did the test actually compare", and this answers it in one
    /// call instead of a re-run per hypothesis.
    /// </summary>
    public string PaddleTest()
    {
        var tx = BallX + BallSpeedX * StepSeconds;
        var ty = BallY + BallSpeedY * StepSeconds;
        var px = _paddle.Position.X - ParkX;
        var py = _paddle.Position.Y - ParkY;
        return $"ball_field={BallX},{BallY} step={tx},{ty} "
               + $"ball_screen={_ball.Position} paddle_screen={_paddle.Position} "
               + $"paddle_field_rect=x[{px},{px + Paddle.Width}] y[{py},{py + Paddle.Height}] "
               + $"hits={HitsPaddle(tx, ty)} vdown={BallSpeedY > 0.0f} over={Over} launched={Launched}";
    }

    /// <summary>One physics step: paddle-driven field, wall, bricks, paddle, floor.</summary>
    private void SimulateStep()
    {
        Ticks++;
        if (!Launched)
        {
            SyncBall();
            return;
        }

        var tx = BallX + BallSpeedX * StepSeconds;
        var ty = BallY + BallSpeedY * StepSeconds;

        // Walls: the ball has to stay inside the field.
        //
        // Defect B-1 of the session: the wall branch wrote
        // `Mathf.Abs(BallSpeedX)` unconditionally, and a ball aimed straight down
        // one of the side walls arrives with BallSpeedX == 0, so it lost its
        // horizontal component and fell dead straight to the floor. A ball that
        // arrives at a wall with no horizontal speed is deflected inwards instead
        // of being left with none.
        if (tx < 8.0f)
        {
            tx = 8.0f;
            BallSpeedX = BallSpeedX < 0.0f ? Mathf.Abs(BallSpeedX) : Mathf.Abs(BallSpeedX) + 96.0f;
        }
        else if (tx + BallSize > FieldWidth - 8.0f)
        {
            tx = FieldWidth - 8.0f - BallSize;
            BallSpeedX = BallSpeedX > 0.0f ? -Mathf.Abs(BallSpeedX) : -Mathf.Abs(BallSpeedX) - 96.0f;
        }

        if (ty < 8.0f)
        {
            ty = 8.0f;
            BallSpeedY = Mathf.Abs(BallSpeedY);
        }

        // Bricks: find the first live brick the trajectory would enter, then ask
        // which face it is entering through (`BounceAxis`).
        var hit = FindBrick(tx, ty);
        if (hit is not null)
        {
            BreakBrick(hit, tx, ty);
        }

        // Paddle: only while the ball is falling. Everything here is field space
        // (see HitsPaddle): the paddle's top is `_paddle.Position.Y - ParkY` and the
        // ball's x is compared against the paddle's own x, which is absolute in a
        // field whose origin is 0 — that is why only Y needs the park point removed.
        if (BallSpeedY > 0.0f && HitsPaddle(tx, ty))
        {
            ty = (_paddle.Position.Y - ParkY) - BallSize;
            BallSpeedY = -Mathf.Abs(BallSpeedY);
            var offset = (tx + BallSize * 0.5f) - (_paddle.Position.X + Paddle.Width * 0.5f);
            BallSpeedX = Mathf.Clamp(offset * 4.0f, -320.0f, 320.0f);
            PaddleBounces++;
            GD.Print($"BREAKOUT_BOUNCE who=paddle n={PaddleBounces} ball={tx},{ty} speed={BallSpeedX},{BallSpeedY}");
        }

        // Floor: the ball is lost.
        if (ty + BallSize > FieldHeight)
        {
            GameOver(false, "BREAKOUT_GAMEOVER reason=lost");
            return;
        }

        BallX = tx;
        BallY = ty;
        SyncBall();
    }

    private Brick FindBrick(float tx, float ty)
    {
        foreach (var brick in _bricks)
        {
            if (!brick.Alive)
            {
                continue;
            }
            var r = brick.Position;
            var s = brick.Size;
            if (tx + BallSize >= r.X && tx <= r.X + s.X
                && ty + BallSize >= r.Y && ty <= r.Y + s.Y)
            {
                return brick;
            }
        }
        return null;
    }

    /// <summary>
    /// Which face of the brick the moving ball is entering through.
    ///
    /// <para>The decision is made on the trajectory's contact box against the
    /// neighbouring bricks, not on the ball's current velocity: a trajectory whose
    /// box would also have touched a vertically adjacent brick on its way in came
    /// from above or below, so the vertical speed flips (Pong's "which side just
    /// scored" mistake, avoided in advance).</para>
    /// </summary>
    private bool BounceIsHorizontal(Brick brick, float tx, float ty)
    {
        var r = brick.Position;
        var s = brick.Size;
        var pad = BallSize - 1.0f;
        foreach (var other in _bricks)
        {
            if (other == brick || !other.Alive)
            {
                continue;
            }
            var o = other.Position;
            var os = other.Size;
            var xOverlap = tx + BallSize >= o.X && tx <= o.X + os.X;
            var yOverlap = ty + BallSize >= o.Y && ty <= o.Y + os.Y;
            var yNear = r.Y - pad <= o.Y + os.Y && r.Y + s.Y + pad >= o.Y;
            var xNear = r.X - pad <= o.X + os.X && r.X + s.X + pad >= o.X;
            if (xOverlap && yNear)
            {
                return false;
            }
            if (yOverlap && xNear)
            {
                return true;
            }
        }
        return true;
    }

    /// <summary>Takes a brick out, scores it, and bounces the trajectory.</summary>
    private void BreakBrick(Brick brick, float tx, float ty)
    {
        var horizontal = BounceIsHorizontal(brick, tx, ty);
        brick.Destroy();
        BricksBroken++;
        BricksRemaining--;
        Score += brick.Points;
        // Defect B-3: this line used to write the bare number while _Ready wrote
        // "SCORE 0", so the HUD's own format changed the moment the first brick
        // broke — the score readback said 10 and the screen said "10". One writer
        // for the HUD (WriteHud) is the whole fix.
        WriteHud(_statusLabel.Text);
        GD.Print($"BREAKOUT_HIT name={brick.Name} destroyed={BricksBroken} remaining={BricksRemaining} score={Score}");

        if (BricksRemaining <= 0)
        {
            GameOver(true, "BREAKOUT_WON");
            return;
        }

        // Keep the trajectory clear of the removed brick, then send it away from
        // the face it came in through.
        if (horizontal)
        {
            var r = brick.Position;
            if (BallSpeedX > 0.0f)
            {
                tx = r.X - BallSize;
                BallSpeedX = -Mathf.Abs(BallSpeedX);
            }
            else
            {
                tx = r.X + brick.Size.X;
                BallSpeedX = Mathf.Abs(BallSpeedX);
            }
        }
        else
        {
            var r = brick.Position;
            if (BallSpeedY > 0.0f)
            {
                ty = r.Y - BallSize;
                BallSpeedY = -Mathf.Abs(BallSpeedY);
            }
            else
            {
                ty = r.Y + brick.Size.Y;
                BallSpeedY = Mathf.Abs(BallSpeedY);
            }
        }
    }

    /// <summary>
    /// The paddle/ball contact test, in ONE coordinate space.
    ///
    /// <para><b>Defect B-2 (found by the contact probe).</b> The ball is simulated
    /// field-relative (see <see cref="AimBall"/>), while a node's <c>position</c> is
    /// absolute — the paddle sits at screen `(352, 540)`. The first version of this
    /// test compared the two spaces directly, so the rectangle it actually required
    /// the ball to enter was `x[352,448] y[540,556]` of *field* space — a band far
    /// below the floor — and every ball fell straight through the paddle. The fix is
    /// to move the paddle's position into the field space by subtracting the park
    /// point, which is exactly how <see cref="SyncBall"/> maps the other way.</para>
    /// </summary>
    private bool HitsPaddle(float tx, float ty)
    {
        var px = _paddle.Position.X - ParkX;
        var py = _paddle.Position.Y - ParkY;
        return tx + BallSize >= px
            && tx <= px + Paddle.Width
            && ty + BallSize >= py
            && ty <= py + Paddle.Height;
    }

    /// <summary>Ends the run; <paramref name="won"/> tells the two endings apart.</summary>
    private void GameOver(bool won, string logLine)
    {
        Over = true;
        Won = won;
        Launched = false;
        BallSpeedX = 0.0f;
        BallSpeedY = 0.0f;
        WriteHud(won
            ? $"GAME OVER - YOU CLEARED {BricksBroken} BRICKS SCORE {Score}"
            : $"GAME OVER - BALL LOST SCORE {Score}");
        GD.Print($"{logLine} score={Score} bricks_broken={BricksBroken} remaining={BricksRemaining}");
    }

    /// <summary>The ball's on-screen position, in one place so the two agree.</summary>
    private void SyncBall()
    {
        _ball.Position = new Vector2(Mathf.Round(ParkX + BallX), Mathf.Round(ParkY + BallY));
    }

    private void WriteHud(string status)
    {
        _scoreLabel.Text = $"SCORE {Score}";
        _statusLabel.Text = status;
    }

    private void TickLog(float dt)
    {
        _logTimer += dt;
        if (_logTimer < 0.5f)
        {
            return;
        }
        _logTimer = 0.0f;
        GD.Print($"BREAKOUT_TICK ball={BallX},{BallY} speed={BallSpeedX},{BallSpeedY} "
                 + $"paddle={_paddle.Position.X} score={Score} remaining={BricksRemaining} launched={Launched}");
    }
}
