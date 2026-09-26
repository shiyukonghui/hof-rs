using Godot;
using System.Collections.Generic;
using System.Text;

namespace minesweeper;

/// <summary>
/// Minesweeper -- the eleventh C# game of the godot-mcp series (TASK-100, DECISIONS.md D138).
///
/// <para><b>Design rule</b> (inherited from the ten games before it): every fact the evidence model
/// needs is a real Godot property on the root node -- <see cref="MineCount"/>,
/// <see cref="RevealedCount"/>, <see cref="FlaggedCount"/>, <see cref="RemainingSafe"/>,
/// <see cref="Moves"/>, <see cref="RejectedMoves"/>, <see cref="RevealsAccepted"/>,
/// <see cref="FlagToggles"/>, <see cref="MinesRelocated"/>, <see cref="Exploded"/>,
/// <see cref="ExplodedRow"/>, <see cref="ExplodedCol"/>, <see cref="ProbeHint"/>,
/// <see cref="ProbeState"/>, <see cref="ProbeMine"/>, <see cref="MineHash"/>,
/// <see cref="RevealHash"/>, <see cref="Won"/>, <see cref="GameOver"/>,
/// <see cref="AutoSteps"/>, <see cref="LastAutoSteps"/>, <see cref="Elapsed"/>,
/// <see cref="Ticks"/>. A session asserts these with <c>running_game_assert_node_state</c>; it
/// never parses a log line.</para>
///
/// <para><b>Determinism rule.</b> The minefield is a function of <see cref="MineSeed"/> plus a fixed
/// LCG, and a board is pinned with ONE <see cref="ForceTestState"/> call (which can also name the
/// mines explicitly). Nothing moves on its own: <see cref="AutoReveal"/> is 0 and
/// <see cref="PollInput"/> is false by default, and the only other way to change the board is a
/// named hook (<see cref="Reveal"/>, <see cref="ToggleFlag"/>, <see cref="AutoStep"/>).</para>
///
/// <para><b>Frame-rate independence (the F-1 lesson).</b> The auto-sweep clock is a FLOAT ACCUMULATOR
/// (<c>_autoAccum += delta * AutoReveal</c>), never <c>(int)(delta * rate)</c>. The two quantities a
/// sample reads are <see cref="LastAutoSteps"/> (reveals the clock applied on the last frame) and
/// <see cref="LastHookSteps"/> (reveals the last <see cref="AutoStep"/> call applied -- two producers,
/// two properties) plus <see cref="Elapsed"/> (a monotonic float second counter that is never
/// truncated).</para>
///
/// <para><b>Rules.</b> The first reveal is SAFE: if it lands on a mine the mine is relocated to the
/// first mine-free cell in row-major order (<see cref="MinesRelocated"/> counts it), so a first click
/// can never explode. Revealing a cell with no adjacent mine floods its neighbours. Revealing an
/// already revealed cell, revealing a flagged cell, or acting after the game is over is ILLEGAL:
/// the board is left exactly as it was and <see cref="RejectedMoves"/> grows. All non-mine cells
/// revealed is the win; revealing a mine is the loss.</para>
///
/// <para><b>All eighty-one cells are runtime-created.</b> <see cref="_Ready"/> builds one
/// <c>ColorRect</c> and one <c>Label</c> per cell; the scene file carries only the three static nodes
/// (Background, Hud, Status). That keeps the edited scene small, keeps it immune to the D-3
/// duplicate-name trap, and makes "a node created at run time really is drawn" part of this game's
/// own evidence.</para>
/// </summary>
public partial class MinesweeperGame : Node2D
{
    // --- the grid ---------------------------------------------------------------
    /// <summary>Columns of the board.</summary>
    [Export] public int Cols = 9;

    /// <summary>Rows of the board.</summary>
    [Export] public int Rows = 9;

    /// <summary>Size of one cell in pixels.</summary>
    [Export] public int Cell = 56;

    /// <summary>Left edge of the board in pixels.</summary>
    [Export] public int OriginX = 148;

    /// <summary>Top edge of the board in pixels.</summary>
    [Export] public int OriginY = 60;

    /// <summary>How many mines the seed places.</summary>
    [Export] public int MineTarget = 10;

    /// <summary>The seed the deterministic LCG minefield is a function of.</summary>
    [Export] public int MineSeed = 12345;

    /// <summary>When true the first reveal relocates a mine instead of exploding.</summary>
    [Export] public bool FirstClickSafe = true;

    // --- observable state, all of it a real Godot property ----------------------
    /// <summary>Mines actually on the board right now.</summary>
    [Export] public int MineCount = 0;

    /// <summary>Mines in row-major order, "r,c|r,c|..." -- the layout an assert can name.</summary>
    [Export] public string MineList = "";

    /// <summary>A stable hash of the minefield -- changes when a mine is relocated.</summary>
    [Export] public int MineHash = 0;

    /// <summary>A stable hash of the revealed/flagged state -- a sample can watch it change.</summary>
    [Export] public int RevealHash = 0;

    /// <summary>Non-mine cells revealed so far.</summary>
    [Export] public int RevealedCount = 0;

    /// <summary>Cells that are not mines.</summary>
    [Export] public int SafeCells = 71;

    /// <summary>Safe cells still hidden.</summary>
    [Export] public int RemainingSafe = 71;

    /// <summary>Cells carrying a flag.</summary>
    [Export] public int FlaggedCount = 0;

    /// <summary>Board-changing operations accepted.</summary>
    [Export] public int Moves = 0;

    /// <summary>Operations refused: bounds, game over, already revealed, flagged, or a no-op.</summary>
    [Export] public int RejectedMoves = 0;

    /// <summary>Reveals accepted.</summary>
    [Export] public int RevealsAccepted = 0;

    /// <summary>Flag toggles accepted.</summary>
    [Export] public int FlagToggles = 0;

    /// <summary>How many times the first-click-safety rule moved a mine.</summary>
    [Export] public int MinesRelocated = 0;

    /// <summary>True once the first reveal has happened.</summary>
    [Export] public bool FirstRevealDone = false;

    /// <summary>True when a mine was revealed.</summary>
    [Export] public bool Exploded = false;

    /// <summary>Row of the mine that was revealed.</summary>
    [Export] public int ExplodedRow = -1;

    /// <summary>Column of the mine that was revealed.</summary>
    [Export] public int ExplodedCol = -1;

    /// <summary>True when every safe cell is revealed.</summary>
    [Export] public bool Won = false;

    /// <summary>True when the game ended, by a win or by a mine.</summary>
    [Export] public bool GameOver = false;

    /// <summary>True when a hidden, unflagged safe cell is left.</summary>
    [Export] public bool CanRevealAny = true;

    /// <summary>Row the last <see cref="ProbeCell"/> looked at.</summary>
    [Export] public int ProbeRow = -1;

    /// <summary>Column the last <see cref="ProbeCell"/> looked at.</summary>
    [Export] public int ProbeCol = -1;

    /// <summary>How many mines touch the probed cell (0..8).</summary>
    [Export] public int ProbeHint = -1;

    /// <summary>Probed cell state: hidden / revealed / mine / flagged / exploded.</summary>
    [Export] public string ProbeState = "";

    /// <summary>True when the probed cell carries a mine.</summary>
    [Export] public bool ProbeMine = false;

    /// <summary>Seconds since the last reset: a monotonic FLOAT accumulator, never truncated.</summary>
    [Export] public float Elapsed = 0.0f;

    /// <summary>Auto-sweep reveals per second; 0 keeps the board still (the default).</summary>
    [Export] public float AutoReveal = 0.0f;

    /// <summary>Reveals the auto-sweep clock has applied over the whole game.</summary>
    [Export] public int AutoSteps = 0;

    /// <summary>Reveals the auto-sweep clock applied on the LAST frame (0 while the clock is off).</summary>
    [Export] public int LastAutoSteps = 0;

    /// <summary>
    /// Reveals the LAST <see cref="AutoStep"/> CALL took. Its own property, and the clock never
    /// writes it: 2048's r1 run (TASK-100) found that a single property used by both producers reads
    /// 0 by the time the assertion runs, because the next frame's clock pass overwrites it. Two
    /// producers, two properties.
    /// </summary>
    [Export] public int LastHookSteps = 0;

    /// <summary>When false the board ignores input (determinism rule: no polling by default).</summary>
    [Export] public bool PollInput = false;

    /// <summary>Reveals that arrived through the declared input actions.</summary>
    [Export] public int InputReveals = 0;

    /// <summary>Flag toggles that arrived through the declared input actions.</summary>
    [Export] public int InputFlags = 0;

    /// <summary>Frames processed since the last reset.</summary>
    [Export] public int Ticks = 0;

    /// <summary>What the last hook did -- the readback string a session quotes.</summary>
    [Export] public string LastEvent = "";

    // --- private model ---------------------------------------------------------
    private bool[] _mine = new bool[81];
    private bool[] _revealed = new bool[81];
    private bool[] _flag = new bool[81];
    private readonly ColorRect[] _cellRect = new ColorRect[81];
    private readonly Label[] _cellLabel = new Label[81];
    private Label _hud;
    private Label _status;
    private float _autoAccum;
    private bool _prevReveal;
    private bool _prevFlag;

    private int Cells()
    {
        return Rows * Cols;
    }

    private int Idx(int row, int col)
    {
        return row * Cols + col;
    }

    private bool InBounds(int row, int col)
    {
        return row >= 0 && row < Rows && col >= 0 && col < Cols;
    }

    public override void _Ready()
    {
        _hud = GetNodeOrNull<Label>("Hud");
        _status = GetNodeOrNull<Label>("Status");
        CreateNodes();
        ResetBoard();
        PlaceMinesFromSeed(MineSeed);
        Recompute();
        ApplyBoard();
        UpdateHud();
        GD.Print($"MINESWEEPER_READY cols={Cols} rows={Rows} mines={MineCount} seed={MineSeed} "
                 + $"auto={AutoReveal} poll={PollInput}");
    }

    private ColorRect MakeRect(string name, Vector2 position, Vector2 size, Color color)
    {
        var node = new ColorRect();
        node.Name = name;
        node.Position = position;
        node.Size = size;
        node.Color = color;
        AddChild(node);
        return node;
    }

    private Label MakeLabel(string name, Vector2 position, Vector2 size)
    {
        var node = new Label();
        node.Name = name;
        node.Position = position;
        node.Size = size;
        node.HorizontalAlignment = HorizontalAlignment.Center;
        node.VerticalAlignment = VerticalAlignment.Center;
        node.AddThemeFontSizeOverride("font_size", 26);
        AddChild(node);
        return node;
    }

    /// <summary>Builds the eighty-one runtime cells. Called once.</summary>
    private void CreateNodes()
    {
        for (var r = 0; r < Rows; r++)
        {
            for (var c = 0; c < Cols; c++)
            {
                var i = Idx(r, c);
                var at = new Vector2(OriginX + c * Cell + 2, OriginY + r * Cell + 2);
                var size = new Vector2(Cell - 4, Cell - 4);
                _cellRect[i] = MakeRect($"Cell_{r}_{c}", at, size, new Color(0.30f, 0.32f, 0.38f));
                _cellLabel[i] = MakeLabel($"Num_{r}_{c}", at, size);
            }
        }
    }

    private void ResetBoard()
    {
        for (var i = 0; i < _mine.Length; i++)
        {
            _mine[i] = false;
            _revealed[i] = false;
            _flag[i] = false;
        }
        MineCount = 0;
        MineList = "";
        MineHash = 0;
        RevealHash = 0;
        RevealedCount = 0;
        FlaggedCount = 0;
        Moves = 0;
        RejectedMoves = 0;
        RevealsAccepted = 0;
        FlagToggles = 0;
        MinesRelocated = 0;
        FirstRevealDone = false;
        Exploded = false;
        ExplodedRow = -1;
        ExplodedCol = -1;
        Won = false;
        GameOver = false;
        CanRevealAny = true;
        ProbeRow = -1;
        ProbeCol = -1;
        ProbeHint = -1;
        ProbeState = "";
        ProbeMine = false;
        AutoReveal = 0.0f;
        AutoSteps = 0;
        LastAutoSteps = 0;
        LastHookSteps = 0;
        _autoAccum = 0.0f;
        PollInput = false;
        InputReveals = 0;
        InputFlags = 0;
        _prevReveal = false;
        _prevFlag = false;
        Ticks = 0;
    }

    /// <summary>The deterministic minefield: a fixed LCG over <paramref name="seed"/>.</summary>
    private void PlaceMinesFromSeed(int seed)
    {
        for (var i = 0; i < _mine.Length; i++)
        {
            _mine[i] = false;
        }
        var total = Cells();
        var target = MineTarget;
        if (target > total - 1)
        {
            target = total - 1;
        }
        unchecked
        {
            var s = (uint)seed;
            if (s == 0u)
            {
                s = 1u;
            }
            var placed = 0;
            while (placed < target)
            {
                s = s * 1664525u + 1013904223u;
                var idx = (int)(s % (uint)total);
                if (_mine[idx])
                {
                    continue;
                }
                _mine[idx] = true;
                placed++;
            }
        }
    }

    /// <summary>How many mines touch a cell.</summary>
    private int Hint(int row, int col)
    {
        var count = 0;
        for (var dr = -1; dr <= 1; dr++)
        {
            for (var dc = -1; dc <= 1; dc++)
            {
                if (dr == 0 && dc == 0)
                {
                    continue;
                }
                if (InBounds(row + dr, col + dc) && _mine[Idx(row + dr, col + dc)])
                {
                    count++;
                }
            }
        }
        return count;
    }

    /// <summary>Recomputes every derived fact: counts, the hashes, the verdicts.</summary>
    private void Recompute()
    {
        var mines = 0;
        var mineHash = 17;
        var mineList = new StringBuilder();
        var revealedCount = 0;
        var flagged = 0;
        var revealHash = 19;
        for (var r = 0; r < Rows; r++)
        {
            for (var c = 0; c < Cols; c++)
            {
                var i = Idx(r, c);
                if (_mine[i])
                {
                    mines++;
                    if (mineList.Length > 0)
                    {
                        mineList.Append('|');
                    }
                    mineList.Append(r).Append(',').Append(c);
                }
                if (_revealed[i] && !_mine[i])
                {
                    revealedCount++;
                }
                if (_flag[i])
                {
                    flagged++;
                }
                unchecked
                {
                    mineHash = mineHash * 31 + (_mine[i] ? 1 : 0);
                    revealHash = revealHash * 37 + ((_revealed[i] ? 2 : 0) + (_flag[i] ? 1 : 0));
                }
            }
        }
        MineCount = mines;
        MineHash = mineHash;
        MineList = mineList.ToString();
        RevealHash = revealHash;
        RevealedCount = revealedCount;
        FlaggedCount = flagged;
        SafeCells = Cells() - mines;
        RemainingSafe = SafeCells - revealedCount;
        Won = SafeCells > 0 && revealedCount >= SafeCells;
        GameOver = Won || Exploded;
        var any = false;
        if (!GameOver)
        {
            for (var i = 0; i < Cells(); i++)
            {
                if (!_mine[i] && !_revealed[i] && !_flag[i])
                {
                    any = true;
                    break;
                }
            }
        }
        CanRevealAny = any;
    }

    private void ApplyBoard()
    {
        for (var r = 0; r < Rows; r++)
        {
            for (var c = 0; c < Cols; c++)
            {
                var i = Idx(r, c);
                if (_cellRect[i] == null || !IsInstanceValid(_cellRect[i]))
                {
                    continue;
                }
                string text;
                Color color;
                Color textColor = new Color(0.95f, 0.95f, 0.95f);
                if (_mine[i] && _revealed[i])
                {
                    text = "*";
                    color = new Color(0.85f, 0.15f, 0.15f);
                }
                else if (_revealed[i])
                {
                    var hint = Hint(r, c);
                    text = hint == 0 ? "" : hint.ToString();
                    color = new Color(0.80f, 0.80f, 0.74f);
                    textColor = new Color(0.10f, 0.10f, 0.14f);
                }
                else if (_flag[i])
                {
                    text = "F";
                    color = new Color(0.95f, 0.75f, 0.20f);
                    textColor = new Color(0.15f, 0.10f, 0.02f);
                }
                else
                {
                    text = "";
                    color = new Color(0.30f, 0.32f, 0.38f);
                }
                _cellRect[i].Color = color;
                if (_cellLabel[i] != null && IsInstanceValid(_cellLabel[i]))
                {
                    _cellLabel[i].Text = text;
                    _cellLabel[i].AddThemeColorOverride("font_color", textColor);
                }
            }
        }
    }

    private void UpdateHud()
    {
        if (_hud != null)
        {
            _hud.Text = $"MINES {MineCount}  FLAGS {FlaggedCount}  SAFE LEFT {RemainingSafe}";
        }
        if (_status != null)
        {
            if (Won)
            {
                _status.Text = "CLEARED";
            }
            else if (GameOver)
            {
                _status.Text = "BOOM - GAME OVER";
            }
            else
            {
                _status.Text = "SWEEP THE FIELD";
            }
        }
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
        if (AutoReveal > 0.0f)
        {
            _autoAccum += dt * AutoReveal; // F-1's fix: accumulate, never (int)(delta * rate)
            var steps = 0;
            while (_autoAccum >= 1.0f && steps < 8)
            {
                _autoAccum -= 1.0f;
                if (!AutoRevealOnce())
                {
                    break;
                }
                AutoSteps++;
                steps++;
            }
            LastAutoSteps = steps;
        }
        else
        {
            LastAutoSteps = 0;
        }
    }

    /// <summary>
    /// The declared-input path. Both actions act on the PRESS EDGE, so a key a scenario injected and
    /// never released performs exactly one action instead of repeating at the frame rate.
    /// </summary>
    private void HandleInput()
    {
        var reveal = Input.IsActionPressed("mine_reveal_next");
        var flag = Input.IsActionPressed("mine_flag_next");
        if (reveal && !_prevReveal && AutoRevealOnce())
        {
            InputReveals++;
        }
        if (flag && !_prevFlag && FlagNext())
        {
            InputFlags++;
        }
        _prevReveal = reveal;
        _prevFlag = flag;
    }

    private bool FlagNext()
    {
        for (var i = 0; i < Cells(); i++)
        {
            if (!_mine[i] && !_revealed[i] && !_flag[i])
            {
                var row = i / Cols;
                var col = i % Cols;
                ToggleFlag(row, col);
                return true;
            }
        }
        return false;
    }

    // --- hooks the session drives ----------------------------------------------

    /// <summary>
    /// Reveals a cell. The first reveal is safe (a mine there is relocated); a reveal of an already
    /// revealed cell, of a flagged cell, or after the game is over is refused with no board change.
    /// </summary>
    public string Reveal(int row, int col)
    {
        if (!InBounds(row, col))
        {
            RejectedMoves++;
            LastEvent = $"rejected reason=out_of_bounds at={row},{col}";
            return LastEvent;
        }
        var i = Idx(row, col);
        if (GameOver)
        {
            RejectedMoves++;
            LastEvent = $"rejected reason=game_over at={row},{col} moves={Moves} "
                        + $"rejected={RejectedMoves} over={GameOver}";
            return LastEvent;
        }
        if (_flag[i])
        {
            RejectedMoves++;
            LastEvent = $"rejected reason=flagged at={row},{col} flags={FlaggedCount}";
            return LastEvent;
        }
        if (_mine[i] && !FirstRevealDone && FirstClickSafe)
        {
            RelocateMine(row, col);
        }
        if (_mine[i])
        {
            _revealed[i] = true;
            Exploded = true;
            ExplodedRow = row;
            ExplodedCol = col;
            Moves++;
            RevealsAccepted++;
            Recompute();
            ApplyBoard();
            UpdateHud();
            LastEvent = $"boom at={row},{col} revealed={RevealedCount} over={GameOver} "
                        + $"rejected={RejectedMoves}";
            return LastEvent;
        }
        if (_revealed[i])
        {
            RejectedMoves++;
            LastEvent = $"rejected reason=already_revealed at={row},{col} hash={RevealHash} "
                        + $"rejected={RejectedMoves}";
            return LastEvent;
        }
        FloodReveal(row, col);
        FirstRevealDone = true;
        Moves++;
        RevealsAccepted++;
        Recompute();
        ApplyBoard();
        UpdateHud();
        LastEvent = $"revealed at={row},{col} count={RevealedCount} remaining={RemainingSafe} "
                    + $"won={Won} over={GameOver}";
        return LastEvent;
    }

    /// <summary>Moves the mine under the first click to the first mine-free cell in row-major order.</summary>
    private void RelocateMine(int row, int col)
    {
        var from = Idx(row, col);
        _mine[from] = false;
        for (var i = 0; i < Cells(); i++)
        {
            if (i != from && !_mine[i])
            {
                _mine[i] = true;
                break;
            }
        }
        MinesRelocated++;
    }

    private void FloodReveal(int row, int col)
    {
        var stack = new List<int>();
        stack.Add(Idx(row, col));
        while (stack.Count > 0)
        {
            var i = stack[stack.Count - 1];
            stack.RemoveAt(stack.Count - 1);
            if (_revealed[i] || _mine[i])
            {
                continue;
            }
            _revealed[i] = true;
            _flag[i] = false;
            var r = i / Cols;
            var c = i % Cols;
            if (Hint(r, c) != 0)
            {
                continue;
            }
            for (var dr = -1; dr <= 1; dr++)
            {
                for (var dc = -1; dc <= 1; dc++)
                {
                    if (dr == 0 && dc == 0)
                    {
                        continue;
                    }
                    if (!InBounds(r + dr, c + dc))
                    {
                        continue;
                    }
                    var n = Idx(r + dr, c + dc);
                    if (!_revealed[n] && !_mine[n])
                    {
                        stack.Add(n);
                    }
                }
            }
        }
    }

    /// <summary>Puts a flag on a hidden cell, or takes it off -- a revealed cell is refused.</summary>
    public string ToggleFlag(int row, int col)
    {
        if (!InBounds(row, col))
        {
            RejectedMoves++;
            LastEvent = $"rejected reason=out_of_bounds at={row},{col}";
            return LastEvent;
        }
        var i = Idx(row, col);
        if (GameOver)
        {
            RejectedMoves++;
            LastEvent = $"rejected reason=game_over at={row},{col} over={GameOver}";
            return LastEvent;
        }
        if (_revealed[i])
        {
            RejectedMoves++;
            LastEvent = $"rejected reason=already_revealed at={row},{col} flagged={_flag[i]}";
            return LastEvent;
        }
        _flag[i] = !_flag[i];
        Moves++;
        FlagToggles++;
        Recompute();
        ApplyBoard();
        UpdateHud();
        LastEvent = $"flag at={row},{col} now={_flag[i]} flags={FlaggedCount} hash={RevealHash}";
        return LastEvent;
    }

    /// <summary>Records what is at one cell into the Probe* properties, so an assert can name it.</summary>
    public string ProbeCell(int row, int col)
    {
        if (!InBounds(row, col))
        {
            ProbeRow = row;
            ProbeCol = col;
            ProbeHint = -1;
            ProbeState = "out_of_bounds";
            ProbeMine = false;
            LastEvent = $"probe rejected reason=out_of_bounds at={row},{col}";
            return LastEvent;
        }
        var i = Idx(row, col);
        ProbeRow = row;
        ProbeCol = col;
        ProbeMine = _mine[i];
        ProbeHint = Hint(row, col);
        if (_mine[i] && _revealed[i])
        {
            ProbeState = "exploded";
        }
        else if (_mine[i] && _flag[i])
        {
            ProbeState = "flagged";
        }
        else if (_mine[i])
        {
            ProbeState = "mine";
        }
        else if (_revealed[i])
        {
            ProbeState = "revealed";
        }
        else if (_flag[i])
        {
            ProbeState = "flagged";
        }
        else
        {
            ProbeState = "hidden";
        }
        LastEvent = $"probe at={row},{col} state={ProbeState} hint={ProbeHint} mine={ProbeMine}";
        return LastEvent;
    }

    /// <summary>The deterministic auto-sweep policy: reveal the first hidden safe unflagged cell.</summary>
    private bool AutoRevealOnce()
    {
        for (var i = 0; i < Cells(); i++)
        {
            if (_mine[i] || _revealed[i] || _flag[i])
            {
                continue;
            }
            var row = i / Cols;
            var col = i % Cols;
            var before = Moves;
            Reveal(row, col);
            // The accepted-operation count is the only honest "did it happen" signal: a reveal
            // refused because the game ended changes nothing, and the reveal hash would still
            // differ from a stale one.
            return Moves > before;
        }
        return false;
    }

    /// <summary>Applies up to <paramref name="steps"/> deterministic auto-sweep reveals.</summary>
    public string AutoStep(int steps)
    {
        var accepted = 0;
        var attempts = 0;
        for (var i = 0; i < steps; i++)
        {
            attempts++;
            if (!AutoRevealOnce())
            {
                break;
            }
            accepted++;
            AutoSteps++;
        }
        LastHookSteps = accepted;
        LastEvent = $"autostep requested={steps} attempts={attempts} accepted={accepted} "
                    + $"total={AutoSteps} revealed={RevealedCount}";
        return LastEvent;
    }

    /// <summary>Auto-sweep reveals per second; 0 keeps the board still (the default).</summary>
    public string SetAutoReveal(float perSecond)
    {
        AutoReveal = perSecond;
        _autoAccum = 0.0f;
        LastAutoSteps = 0;
        LastEvent = $"auto_reveal={AutoReveal}";
        GD.Print($"MINESWEEPER_AUTO auto={AutoReveal}");
        return LastEvent;
    }

    /// <summary>Switches the declared-input polling on or off (the default is off).</summary>
    public string SetPollInput(bool enabled)
    {
        PollInput = enabled;
        _prevReveal = false;
        _prevFlag = false;
        LastEvent = $"poll_input={PollInput}";
        return LastEvent;
    }

    /// <summary>The board as a readable one-liner plus every exported fact.</summary>
    public string Dump()
    {
        var sb = new StringBuilder();
        for (var r = 0; r < Rows; r++)
        {
            for (var c = 0; c < Cols; c++)
            {
                var i = Idx(r, c);
                if (_mine[i] && _revealed[i])
                {
                    sb.Append('*');
                }
                else if (_revealed[i])
                {
                    var hint = Hint(r, c);
                    sb.Append(hint == 0 ? '.' : (char)('0' + hint));
                }
                else if (_flag[i])
                {
                    sb.Append('F');
                }
                else if (_mine[i])
                {
                    sb.Append('M');
                }
                else
                {
                    sb.Append('#');
                }
            }
            if (r + 1 < Rows)
            {
                sb.Append('/');
            }
        }
        return $"board={sb} mines={MineCount} seed={MineSeed} mine_list={MineList} "
               + $"mine_hash={MineHash} reveal_hash={RevealHash} revealed={RevealedCount} "
               + $"safe={SafeCells} remaining={RemainingSafe} flags={FlaggedCount} moves={Moves} "
               + $"rejected={RejectedMoves} reveals={RevealsAccepted} toggles={FlagToggles} "
               + $"relocated={MinesRelocated} first_done={FirstRevealDone} exploded={Exploded} "
               + $"boom={ExplodedRow},{ExplodedCol} won={Won} over={GameOver} can_reveal={CanRevealAny} "
               + $"probe={ProbeRow},{ProbeCol}:{ProbeState}:{ProbeHint}:{ProbeMine} "
               + $"auto={AutoReveal} auto_steps={AutoSteps} last_auto={LastAutoSteps} "
               + $"last_hook={LastHookSteps} input_reveals={InputReveals} input_flags={InputFlags} "
               + $"elapsed={Elapsed:F3} ticks={Ticks} last={LastEvent}";
    }

    /// <summary>
    /// Writes the whole deterministic state in one call --
    /// <c>"mines=r,c|r,c|... ;revealed=r,c|...;flags=r,c|...;first=yes|no;auto=s"</c>, where
    /// <c>mines=seed:N</c> asks for the LCG layout instead of an explicit list.
    ///
    /// <para>Keys may be omitted. Auto-sweep and input polling are switched OFF first, so a session's
    /// aim and the next readback are the same fact. A test that wants motion calls
    /// <see cref="SetAutoReveal"/> or <see cref="AutoStep"/> itself -- which is why "a mine was hit"
    /// can never be an accident of timing.</para>
    /// </summary>
    public string ForceTestState(string spec)
    {
        ResetBoard();
        bool? first = null;
        foreach (var part in spec.Split(';'))
        {
            var kv = part.Split(new[] { '=' }, 2);
            if (kv.Length != 2)
            {
                continue;
            }
            switch (kv[0])
            {
                case "mines":
                    if (kv[1].StartsWith("seed:"))
                    {
                        MineSeed = int.Parse(kv[1].Substring(5));
                        PlaceMinesFromSeed(MineSeed);
                    }
                    else
                    {
                        for (var i = 0; i < _mine.Length; i++)
                        {
                            _mine[i] = false;
                        }
                        foreach (var cell in kv[1].Split('|'))
                        {
                            var p = cell.Split(',');
                            if (p.Length != 2)
                            {
                                continue;
                            }
                            var row = int.Parse(p[0]);
                            var col = int.Parse(p[1]);
                            if (InBounds(row, col))
                            {
                                _mine[Idx(row, col)] = true;
                            }
                        }
                    }
                    break;
                case "revealed":
                    foreach (var cell in kv[1].Split('|'))
                    {
                        var p = cell.Split(',');
                        if (p.Length != 2)
                        {
                            continue;
                        }
                        var row = int.Parse(p[0]);
                        var col = int.Parse(p[1]);
                        if (InBounds(row, col))
                        {
                            _revealed[Idx(row, col)] = true;
                        }
                    }
                    break;
                case "flags":
                    foreach (var cell in kv[1].Split('|'))
                    {
                        var p = cell.Split(',');
                        if (p.Length != 2)
                        {
                            continue;
                        }
                        var row = int.Parse(p[0]);
                        var col = int.Parse(p[1]);
                        if (InBounds(row, col))
                        {
                            _flag[Idx(row, col)] = true;
                        }
                    }
                    break;
                case "first":
                    first = kv[1] == "yes" || kv[1] == "true" || kv[1] == "1";
                    break;
                case "auto":
                    AutoReveal = float.Parse(kv[1]);
                    break;
            }
        }
        FirstRevealDone = first ?? false;
        Recompute();
        ApplyBoard();
        UpdateHud();
        LastEvent = $"forced mines={MineCount} revealed={RevealedCount} flags={FlaggedCount} "
                    + $"first_done={FirstRevealDone} over={GameOver} won={Won} seed={MineSeed}";
        return LastEvent;
    }
}
