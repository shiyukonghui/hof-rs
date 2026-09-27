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

    /// <summary>Whether a point re-serves by itself (a human game) or parks.</summary>
    [Export] public bool AutoServe = true;

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
    }

    /// <summary>Puts the ball back in the middle and sends it off again.</summary>
    public void Serve()
    {
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
