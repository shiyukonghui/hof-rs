using Godot;

namespace pong;

/// <summary>
/// Pong — the first C# game of the godot-mcp series (TASK-091, DECISIONS.md D138).
///
/// <para>Design rule for this and every later game: <b>the state that decides
/// whether a call worked has to be a Godot property</b> (an <c>[Export]</c> or a
/// node property), so the MCP trace can carry it, the ledger can judge it, and a
/// pixel diff can corroborate it. Nothing observable lives in a private field.</para>
///
/// <para><b>Determinism rule</b> (learned from the run-1 defect P-1): the match does
/// not start by itself. A fresh process parks the ball in the middle with zero
/// velocity and waits for an explicit serve, so the several seconds a test driver
/// spends bringing both endpoints up cannot change the score behind its back.</para>
///
/// <para>Playfield: 800x600. Ball 16x16, paddles 16x100, first to
/// <see cref="WinScore"/> wins.</para>
/// </summary>
public partial class PongGame : Node2D
{
    /// <summary>Points needed to win. Exported so a session can shorten the match.</summary>
    [Export] public int WinScore = 5;

    /// <summary>
    /// Whether a point re-serves by itself (a human game) or parks.
    ///
    /// <para><b>TASK-133: the default is now false, and that is the structural fix.</b>
    /// With it true, the right paddle -- which no key in this game can be told to track
    /// the ball -- let every auto-served ball fly straight out, so the match reached
    /// `PONG_OVER winner=LEFT 5:0` in about 12 s with no human input at all (TASK-132
    /// measured only 1-5 model steps inside a live match). A match that plays itself to
    /// a 5:0 conclusion before the player can act is not a match. With it false the
    /// rule is the one this game's own README already documents -- a point parks the
    /// ball in the middle and the next serve is an explicit `pong_serve` (SPACE) -- so
    /// the length of a match is controlled by the player, and a serve is a real action
    /// with a real, visible consequence.</para>
    /// </summary>
    [Export] public bool AutoServe = false;

    /// <summary>Top of the ball's travel (ball top edge, inclusive).</summary>
    [Export] public float TopLimit = 8.0f;

    /// <summary>Bottom of the ball's travel (ball bottom edge, inclusive).</summary>
    [Export] public float BottomLimit = 552.0f;

    /// <summary>Left edge of the playfield; the ball leaving it scores for the right.</summary>
    [Export] public float LeftLimit = 0.0f;

    /// <summary>Right edge of the playfield; the ball leaving it scores for the left.</summary>
    [Export] public float RightLimit = 800.0f;

    /// <summary>
    /// How much travel one *injected* action event is worth, in seconds.
    ///
    /// <para>The MCP input step parses a press and a release back to back
    /// (`running_game_test_execution.cpp:796-797`), so <c>Input.IsActionPressed</c>
    /// is not what an injected step looks like - the event is. A discrete nudge per
    /// press keeps the paddle drivable both by a human holding a key (the
    /// <c>_Process</c> path) and by an injected one-shot (this path), and makes the
    /// injected move one predictable distance: `Speed * InjectedStepSeconds`.</para>
    /// </summary>
    [Export] public float InjectedStepSeconds = 0.25f;

    /// <summary>
    /// Whether the right paddle tracks the ball when it is coming toward it -- the
    /// OPPONENT. Default true, because this build ships as a ONE-player game: with it
    /// false the right paddle never moves and every ball that survives the left paddle
    /// simply flies out of the right edge, so the left side wins 5:0 no matter what the
    /// player does (the pre-TASK-133 behaviour, measured at ~12 s).
    ///
    /// <para>It is a plain exported flag, not a hidden rule: set it false for two-player
    /// play and the right paddle is again driven only by `pong_right_up` /
    /// `pong_right_down`. The tracking runs only while the ball is IN FLIGHT and moving
    /// toward the right paddle, so a parked ball (the start, and every point now that
    /// `AutoServe` is off) leaves both paddles still.</para>
    /// </summary>
    [Export] public bool RightPaddleAutoFollow = true;

    /// <summary>Pixels per second the opponent paddle may travel.</summary>
    [Export] public float OpponentSpeed = 340.0f;

    /// <summary>Fraction of the opponent's travel that is applied (a beatable opponent).</summary>
    [Export] public float OpponentSkill = 0.78f;

    private const float ServeSpeedX = 280.0f;
    private const float ServeSpeedY = 180.0f;

    private Ball _ball;
    private Paddle _left;
    private Paddle _right;
    private Label _scoreLeft;
    private Label _scoreRight;
    private Label _winLabel;

    private int _leftScore;
    private int _rightScore;
    private bool _over;
    private float _serveDirection = 1.0f;
    private float _logTimer;

    /// <summary>
    /// The last mode action the game itself REFUSED, in the shape this project's
    /// convention uses (`<name>: <why>`). TASK-133: serving a ball that is already in
    /// flight is refused and recorded here rather than silently obeyed.
    /// </summary>
    [Export] public string LastRejectedAction = "";

    public override void _Ready()
    {
        _ball = GetNode<Ball>("Ball");
        _left = GetNode<Paddle>("PaddleLeft");
        _right = GetNode<Paddle>("PaddleRight");
        _scoreLeft = GetNode<Label>("ScoreLeft");
        _scoreRight = GetNode<Label>("ScoreRight");
        _winLabel = GetNode<Label>("WinLabel");

        _winLabel.Text = "";
        _scoreLeft.Text = "0";
        _scoreRight.Text = "0";
        ParkBall();

        GD.Print($"PONG_READY name={Name} ball={_ball.Position} ball_v={_ball.Velocity} "
                 + $"win_score={WinScore} auto_serve={AutoServe}");
    }

    /// <summary>
    /// The injected-input path: the MCP scenario step delivers one press and one
    /// release, so each press is turned into one discrete nudge.
    /// </summary>
    public override void _Input(InputEvent @event)
    {
        if (@event.IsActionPressed("pong_left_up")) { Nudge("left_up", _left, -1.0f); }
        if (@event.IsActionPressed("pong_left_down")) { Nudge("left_down", _left, 1.0f); }
        if (@event.IsActionPressed("pong_right_up")) { Nudge("right_up", _right, -1.0f); }
        if (@event.IsActionPressed("pong_right_down")) { Nudge("right_down", _right, 1.0f); }
        if (@event.IsActionPressed("pong_serve")) { Serve(); }
    }

    public override void _Process(double delta)
    {
        if (_over)
        {
            return;
        }

        var dt = (float)delta;
        TickLog(dt);

        if (Input.IsActionPressed("pong_left_up")) { _left.Step(-1.0f, dt); }
        if (Input.IsActionPressed("pong_left_down")) { _left.Step(1.0f, dt); }
        if (Input.IsActionPressed("pong_right_up")) { _right.Step(-1.0f, dt); }
        if (Input.IsActionPressed("pong_right_down")) { _right.Step(1.0f, dt); }
        // TASK-133: the opponent. Only while the ball is actually inbound, so a parked
        // ball leaves both paddles (and the picture) still.
        if (RightPaddleAutoFollow && _ball.Velocity.X > 0.0f)
        {
            var target = _ball.Position.Y + Ball.Size * 0.5f - Paddle.Height * 0.5f;
            var gap = target - _right.Position.Y;
            var step = OpponentSpeed * dt;
            var want = Mathf.Clamp(gap, -step, step) * OpponentSkill;
            _right.MoveBy(want);
        }

        var next = _ball.Position + _ball.Velocity * dt;

        // Walls.
        if (next.Y < TopLimit)
        {
            next.Y = TopLimit;
            _ball.Velocity = new Vector2(_ball.Velocity.X, Mathf.Abs(_ball.Velocity.Y));
        }
        if (next.Y + Ball.Size > BottomLimit)
        {
            next.Y = BottomLimit - Ball.Size;
            _ball.Velocity = new Vector2(_ball.Velocity.X, -Mathf.Abs(_ball.Velocity.Y));
        }

        // Paddles.
        if (_ball.Velocity.X < 0.0f && Hits(next, _left))
        {
            next.X = _left.Position.X + Paddle.Width;
            _ball.Velocity = new Vector2(Mathf.Abs(_ball.Velocity.X) * 1.02f, English(next, _left));
        }
        else if (_ball.Velocity.X > 0.0f && Hits(next, _right))
        {
            next.X = _right.Position.X - Ball.Size;
            _ball.Velocity = new Vector2(-Mathf.Abs(_ball.Velocity.X) * 1.02f, English(next, _right));
        }

        // Scoring.
        if (next.X + Ball.Size < LeftLimit)
        {
            _rightScore++;
            Score("RIGHT");
            return;
        }
        if (next.X > RightLimit)
        {
            _leftScore++;
            Score("LEFT");
            return;
        }

        _ball.Position = next;
    }

    /// <summary>Puts the ball back in the middle, at rest.</summary>
    private void ParkBall()
    {
        _ball.Position = new Vector2(392.0f, 268.0f);
        _ball.Velocity = Vector2.Zero;
        LastRejectedAction = "";
    }

    /// <summary>
    /// Serves the ball: puts it back in the middle and sends it off.
    ///
    /// <para><b>TASK-133: serving a ball that is already in flight is REFUSED and
    /// recorded, instead of silently teleporting it back to the middle.</b> The old
    /// version always reset `Position` and `Velocity`, so pressing SPACE mid-rally was a
    /// no-op that looked like a teleport: the ball snapped back to the centre and the
    /// net movement over the measurement window could be *smaller* than the no-input
    /// window's, which is precisely the "the model acted, the game accepted it, and the
    /// picture did not change in a way attributable to the input" state TASK-132 recorded
    /// on 9 of 10 pong steps. Refusing it makes the action honest (the game saw the
    /// input and says no) and makes the state unambiguous: `Ball.Velocity == 0` is the
    /// only state in which a serve does anything.</para>
    /// </summary>
    public void Serve()
    {
        if (_ball.Velocity != Vector2.Zero)
        {
            LastRejectedAction = "serve: the ball is already in flight";
            GD.Print($"PONG_SERVE_REFUSED ball={_ball.Position} v={_ball.Velocity} "
                     + "reason=already_in_flight");
            return;
        }
        _ball.Position = new Vector2(392.0f, 268.0f);
        _ball.Velocity = new Vector2(ServeSpeedX * _serveDirection, ServeSpeedY);
        GD.Print($"PONG_SERVE ball={_ball.Position} v={_ball.Velocity}");
    }

    private void Nudge(string name, Paddle paddle, float direction)
    {
        paddle.Step(direction, InjectedStepSeconds);
        GD.Print($"PONG_NUDGE who={name} y={paddle.Position.Y}");
    }

    private static bool Hits(Vector2 ball, Paddle paddle)
    {
        return ball.X <= paddle.Position.X + Paddle.Width
            && ball.X + Ball.Size >= paddle.Position.X
            && ball.Y + Ball.Size >= paddle.Position.Y
            && ball.Y <= paddle.Position.Y + Paddle.Height;
    }

    /// <summary>Where on the paddle the ball landed decides the outgoing angle.</summary>
    private static float English(Vector2 ball, Paddle paddle)
    {
        var centre = paddle.Position.Y + Paddle.Height * 0.5f;
        var offset = (ball.Y + Ball.Size * 0.5f) - centre;
        return Mathf.Clamp(offset * 8.0f, -320.0f, 320.0f);
    }

    /// <summary>
    /// One point was scored by <paramref name="side"/>.
    ///
    /// <para>The winner is <b>the side that just scored</b>, not "whichever side
    /// happens to be at or above the target" - run-1 defect P-2: with the target
    /// lowered mid-match the old <c>_leftScore &gt;= WinScore ? LEFT : RIGHT</c> test
    /// announced "GAME OVER - LEFT WINS 3:3" after the right had just scored.</para>
    /// </summary>
    private void Score(string side)
    {
        _scoreLeft.Text = _leftScore.ToString();
        _scoreRight.Text = _rightScore.ToString();

        var scorerScore = side == "LEFT" ? _leftScore : _rightScore;
        var conceder = side == "LEFT" ? "RIGHT" : "LEFT";
        GD.Print($"PONG_SCORE scored_by={side} left={_leftScore} right={_rightScore} win_score={WinScore}");

        if (scorerScore >= WinScore)
        {
            _over = true;
            _winLabel.Text = $"GAME OVER - {side} WINS {_leftScore}:{_rightScore}";
            _ball.Velocity = Vector2.Zero;
            GD.Print($"PONG_OVER winner={side} left={_leftScore} right={_rightScore}");
            return;
        }

        // The next serve goes toward the player who just conceded.
        _serveDirection = conceder == "LEFT" ? -1.0f : 1.0f;
        if (AutoServe)
        {
            Serve();
        }
        else
        {
            ParkBall();
            GD.Print($"PONG_PARKED ball={_ball.Position} next_serve_dir={_serveDirection}");
        }
    }

    private void TickLog(float dt)
    {
        _logTimer += dt;
        if (_logTimer < 1.0f)
        {
            return;
        }
        _logTimer = 0.0f;
        GD.Print($"PONG_TICK ball={_ball.Position} v={_ball.Velocity} left={_left.Position.Y} right={_right.Position.Y} score={_leftScore}-{_rightScore}");
    }
}
