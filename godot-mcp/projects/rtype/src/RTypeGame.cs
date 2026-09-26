using Godot;
using System.Collections.Generic;
using System.Text;

namespace rtype;

/// <summary>
/// R-Type -- the eighteenth C# game of the godot-mcp series (TASK-104, DECISIONS.md D152).
///
/// <para><b>Design rule</b> (inherited from the seventeen games before it): every fact the evidence
/// model needs is a real Godot property on the root node -- <see cref="PlayerX"/>,
/// <see cref="PlayerY"/>, <see cref="Lives"/>, <see cref="Score"/>, <see cref="Wave"/>,
/// <see cref="WaveLeftToSpawn"/>, <see cref="EnemiesSpawned"/>, <see cref="EnemiesAlive"/>,
/// <see cref="EnemiesKilled"/>, <see cref="EnemiesEscaped"/>, <see cref="BulletsFired"/>,
/// <see cref="EnemyShotsFired"/>, <see cref="EnemyList"/>, <see cref="BulletList"/>,
/// <see cref="EnemyBulletList"/>, <see cref="StateHash"/>, <see cref="Steps"/>,
/// <see cref="Elapsed"/>, <see cref="Ticks"/>, <see cref="Won"/>, <see cref="GameOver"/>. A
/// session asserts these with <c>running_game_assert_node_state</c>; it never parses a log line.</para>
///
/// <para><b>Integer, and therefore recomputable.</b> There is no float in the simulation. The ship
/// moves <see cref="PlayerSpeed"/> pixels per call, a player bullet <see cref="BulletSpeed"/> pixels
/// per step, an enemy <see cref="EnemySpeed"/> pixels per step and an enemy bullet
/// <see cref="EnemyBulletSpeed"/>. A wave enters as a FORMATION: the k-th spawn of a wave is placed
/// at <c>(FormationEntryX + (k/FormationRows)*FormationColStep, FormationStartY + (k%FormationRows)*FormationRowStep)</c>,
/// so the wave arrives as a grid rather than one ship at a time. Every one of those is an integer
/// rule, so the whole run is reproduced exactly by the Python second implementation in
/// <c>recovery\work\task104\make_session_rtype.py</c> -- whose outputs are the session's assertion
/// literals.</para>
///
/// <para><b>Frame-rate independence (the F-1 lesson).</b> The auto clock is a FLOAT ACCUMULATOR
/// (<c>_autoAccum += delta * AutoClock</c>), never <c>(int)(delta * rate)</c>. Two producers, two
/// properties: <see cref="LastAutoSteps"/> is what the clock applied on the last frame and
/// <see cref="LastHookSteps"/> is what the last <see cref="StepFrames"/> CALL applied.
/// <see cref="Elapsed"/> is a monotonic float second counter that is never truncated.</para>
///
/// <para><b>All world nodes are runtime-created.</b> The scene file carries only the three static
/// nodes (Background, Hud, Status); the starfield, the ship, the formation pool and both bullet
/// pools are built by <see cref="CreateNodes"/>. That keeps the edited scene immune to the D-3
/// duplicate-name trap and makes "a node created at run time really is drawn" part of this game's
/// own evidence.</para>
/// </summary>
public partial class RTypeGame : Node2D
{
    // --- the field --------------------------------------------------------------
    /// <summary>Field width in pixels.</summary>
    [Export] public int FieldW = 800;

    /// <summary>Field height in pixels.</summary>
    [Export] public int FieldH = 600;

    /// <summary>The HUD strip is above this row; the ship may not enter it.</summary>
    [Export] public int HudBottom = 64;

    // --- the ship ---------------------------------------------------------------
    /// <summary>Ship sprite width.</summary>
    [Export] public int PlayerW = 24;

    /// <summary>Ship sprite height.</summary>
    [Export] public int PlayerH = 16;

    /// <summary>Pixels one <see cref="MovePlayer"/> call travels.</summary>
    [Export] public int PlayerSpeed = 8;

    /// <summary>Ship x at the start of a fresh game.</summary>
    [Export] public int PlayerStartX = 80;

    /// <summary>Ship y at the start of a fresh game.</summary>
    [Export] public int PlayerStartY = 300;

    /// <summary>Lives at the start of a fresh game.</summary>
    [Export] public int StartLives = 3;

    // --- the bullets ------------------------------------------------------------
    /// <summary>Player bullet width.</summary>
    [Export] public int BulletW = 10;

    /// <summary>Player bullet height.</summary>
    [Export] public int BulletH = 4;

    /// <summary>Player bullet pixels per step (rightwards).</summary>
    [Export] public int BulletSpeed = 16;

    /// <summary>How many player bullets may be in the air at once.</summary>
    [Export] public int BulletPoolSize = 12;

    /// <summary>Enemy bullet width and height.</summary>
    [Export] public int EnemyBulletSize = 8;

    /// <summary>Enemy bullet pixels per step (leftwards).</summary>
    [Export] public int EnemyBulletSpeed = 6;

    /// <summary>How many enemy bullets may be in the air at once.</summary>
    [Export] public int EnemyBulletPoolSize = 24;

    // --- the enemies ------------------------------------------------------------
    /// <summary>Enemy sprite width.</summary>
    [Export] public int EnemyW = 24;

    /// <summary>Enemy sprite height.</summary>
    [Export] public int EnemyH = 20;

    /// <summary>Enemy pixels per step (leftwards).</summary>
    [Export] public int EnemySpeed = 3;

    /// <summary>Steps between two shots of the same enemy.</summary>
    [Export] public int EnemyFirePeriod = 45;

    /// <summary>Steps between two spawns of the same wave.</summary>
    [Export] public int SpawnInterval = 6;

    /// <summary>Points one kill is worth.</summary>
    [Export] public int KillScore = 100;

    /// <summary>Formation rows: the k-th spawn sits at row <c>k % FormationRows</c>.</summary>
    [Export] public int FormationRows = 3;

    /// <summary>Formation column spacing in pixels.</summary>
    [Export] public int FormationColStep = 40;

    /// <summary>Formation row spacing in pixels.</summary>
    [Export] public int FormationRowStep = 70;

    /// <summary>Formation top row y in pixels.</summary>
    [Export] public int FormationStartY = 120;

    /// <summary>Where a formation's first column enters, in pixels (off the right edge).</summary>
    [Export] public int FormationEntryX = 830;

    /// <summary>How many enemies each wave enters with.</summary>
    [Export] public int[] WaveSizes = { 4, 5, 6 };

    // --- observable state, all of it a real Godot property ----------------------
    /// <summary>Ship centre-left x in pixels.</summary>
    [Export] public int PlayerX = 80;

    /// <summary>Ship top y in pixels.</summary>
    [Export] public int PlayerY = 300;

    /// <summary>Lives left; a hit or an escaped enemy costs one.</summary>
    [Export] public int Lives = 3;

    /// <summary>Points: <see cref="KillScore"/> per kill.</summary>
    [Export] public int Score = 0;

    /// <summary>Current wave, 1-based.</summary>
    [Export] public int Wave = 1;

    /// <summary>How many waves a full game has.</summary>
    [Export] public int WaveMax = 3;

    /// <summary>Enemies of the current wave still to enter.</summary>
    [Export] public int WaveLeftToSpawn = 0;

    /// <summary>Steps until the next spawn of the current wave.</summary>
    [Export] public int SpawnCountdown = 0;

    /// <summary>Enemies that entered over the whole game.</summary>
    [Export] public int EnemiesSpawned = 0;

    /// <summary>Enemies alive right now.</summary>
    [Export] public int EnemiesAlive = 0;

    /// <summary>Enemies shot down.</summary>
    [Export] public int EnemiesKilled = 0;

    /// <summary>Enemies that crossed the whole field (each cost a life).</summary>
    [Export] public int EnemiesEscaped = 0;

    /// <summary>Player bullets fired.</summary>
    [Export] public int BulletsFired = 0;

    /// <summary>Bullets in the air right now.</summary>
    [Export] public int BulletsActive = 0;

    /// <summary>Enemy bullets fired.</summary>
    [Export] public int EnemyShotsFired = 0;

    /// <summary>Enemy bullets in the air right now.</summary>
    [Export] public int EnemyBulletsActive = 0;

    /// <summary>Alive enemies as <c>"x,y,cd|..."</c>, in spawn order.</summary>
    [Export] public string EnemyList = "";

    /// <summary>Player bullets in the air as <c>"x,y|..."</c>, oldest first.</summary>
    [Export] public string BulletList = "";

    /// <summary>Enemy bullets in the air as <c>"x,y|..."</c>, oldest first.</summary>
    [Export] public string EnemyBulletList = "";

    /// <summary>Multiply-31 hash of the whole observable world, recomputable from the printed lists.</summary>
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
    /// writes it (2048's r1 run, TASK-100 defect G1: one property with two producers reads 0 by the
    /// time the assertion runs). Two producers, two properties.
    /// </summary>
    [Export] public int LastHookSteps = 0;

    /// <summary>True when every wave was cleared.</summary>
    [Export] public bool Won = false;

    /// <summary>True when the game ended, by clearing every wave or by losing every life.</summary>
    [Export] public bool GameOver = false;

    /// <summary>Move calls that really moved the ship.</summary>
    [Export] public int Moves = 0;

    /// <summary>Move calls the clamp or the game-over rule refused.</summary>
    [Export] public int RejectedMoves = 0;

    /// <summary>Column the last <see cref="ProbeAt"/> looked at.</summary>
    [Export] public int ProbeX = -1;

    /// <summary>Row the last <see cref="ProbeAt"/> looked at.</summary>
    [Export] public int ProbeY = -1;

    /// <summary>A readable name for the probed point: outside / player / enemy / enemy_bullet / bullet / empty.</summary>
    [Export] public string ProbeState = "";

    /// <summary>Index of the thing the probe named, -1 when the point is empty.</summary>
    [Export] public int ProbeValue = -1;

    /// <summary>When false the world ignores input (determinism rule: no polling by default).</summary>
    [Export] public bool PollInput = false;

    /// <summary>Shots that arrived through the declared input action.</summary>
    [Export] public int InputShots = 0;

    /// <summary>What the last hook did -- the readback string a session quotes.</summary>
    [Export] public string LastEvent = "";

    // --- private model -----------------------------------------------------------
    private readonly List<int> _enX = new List<int>();
    private readonly List<int> _enY = new List<int>();
    private readonly List<int> _enCd = new List<int>();
    private readonly int[] _pbX = new int[64];
    private readonly int[] _pbY = new int[64];
    private readonly bool[] _pbOn = new bool[64];
    private readonly int[] _ebX = new int[64];
    private readonly int[] _ebY = new int[64];
    private readonly bool[] _ebOn = new bool[64];
    private ColorRect _ship;
    private readonly List<ColorRect> _enemyRects = new List<ColorRect>();
    private readonly List<ColorRect> _pbRects = new List<ColorRect>();
    private readonly List<ColorRect> _ebRects = new List<ColorRect>();
    private readonly List<ColorRect> _starRects = new List<ColorRect>();
    private Label _hud;
    private Label _status;
    private float _autoAccum;
    private bool _prevFire;
    private const int EnemyPool = 16;
    private const int StarCount = 48;

    private int PlayerMaxX()
    {
        return FieldW - PlayerW;
    }

    private int PlayerMaxY()
    {
        return FieldH - PlayerH;
    }

    private int SizeOfWave(int wave)
    {
        var index = wave - 1;
        return index >= 0 && index < WaveSizes.Length ? WaveSizes[index] : 4;
    }

    private static bool Overlap(int ax, int ay, int aw, int ah, int bx, int by, int bw, int bh)
    {
        return ax < bx + bw && bx < ax + aw && ay < by + bh && by < ay + ah;
    }

    // --- the rules ---------------------------------------------------------------

    private void SpawnOne()
    {
        // The formation slot is the number of this spawn inside its wave, 0-based.
        var slot = SizeOfWave(Wave) - WaveLeftToSpawn;
        var row = slot % FormationRows;
        var col = slot / FormationRows;
        _enX.Add(FormationEntryX + col * FormationColStep);
        _enY.Add(FormationStartY + row * FormationRowStep);
        _enCd.Add(EnemyFirePeriod);
        EnemiesSpawned++;
    }

    /// <summary>
    /// One fixed simulation step: spawn, move the three moving kinds, fire, resolve both collisions,
    /// then the wave and win checks. The Python second implementation runs this exact order.
    /// </summary>
    private void Tick()
    {
        if (GameOver)
        {
            return;
        }
        Steps++;

        // 1. at most one enemy of the current wave enters
        if (WaveLeftToSpawn > 0)
        {
            if (SpawnCountdown <= 0)
            {
                SpawnOne();
                WaveLeftToSpawn--;
                SpawnCountdown = SpawnInterval;
            }
            else
            {
                SpawnCountdown--;
            }
        }

        // 2. player bullets fly right and leave the field on the right
        for (var i = 0; i < BulletPoolSize && i < _pbOn.Length; i++)
        {
            if (!_pbOn[i])
            {
                continue;
            }
            _pbX[i] += BulletSpeed;
            if (_pbX[i] >= FieldW)
            {
                _pbOn[i] = false;
            }
        }

        // 3. enemy bullets fly left and leave the field on the left
        for (var i = 0; i < EnemyBulletPoolSize && i < _ebOn.Length; i++)
        {
            if (!_ebOn[i])
            {
                continue;
            }
            _ebX[i] -= EnemyBulletSpeed;
            if (_ebX[i] + EnemyBulletSize < 0)
            {
                _ebOn[i] = false;
            }
        }

        // 4. enemies fly left; the ones that cross the field cost a life
        var escapedNow = 0;
        for (var i = _enX.Count - 1; i >= 0; i--)
        {
            _enX[i] -= EnemySpeed;
            if (_enX[i] + EnemyW < 0)
            {
                _enX.RemoveAt(i);
                _enY.RemoveAt(i);
                _enCd.RemoveAt(i);
                escapedNow++;
            }
        }
        if (escapedNow > 0)
        {
            EnemiesEscaped += escapedNow;
            Lives -= escapedNow;
        }
        if (Lives <= 0)
        {
            Lives = 0;
            GameOver = true;
            Won = false;
            LastEvent = $"lost steps={Steps} wave={Wave} killed={EnemiesKilled} escaped={EnemiesEscaped} "
                        + $"score={Score}";
            return;
        }

        // 5. enemies fire, in spawn order, one bullet each time their cooldown runs out
        for (var i = 0; i < _enX.Count; i++)
        {
            _enCd[i]--;
            if (_enCd[i] > 0 || _enX[i] >= FieldW)
            {
                continue;
            }
            var free = -1;
            for (var k = 0; k < EnemyBulletPoolSize && k < _ebOn.Length; k++)
            {
                if (!_ebOn[k])
                {
                    free = k;
                    break;
                }
            }
            if (free < 0)
            {
                continue;
            }
            _ebOn[free] = true;
            _ebX[free] = _enX[i] - EnemyBulletSize;
            _ebY[free] = _enY[i] + (EnemyH - EnemyBulletSize) / 2;
            _enCd[i] = EnemyFirePeriod;
            EnemyShotsFired++;
        }

        // 6. a player bullet takes the FIRST enemy it overlaps, in spawn order
        for (var i = 0; i < BulletPoolSize && i < _pbOn.Length; i++)
        {
            if (!_pbOn[i])
            {
                continue;
            }
            var hit = -1;
            for (var k = 0; k < _enX.Count; k++)
            {
                if (Overlap(_pbX[i], _pbY[i], BulletW, BulletH, _enX[k], _enY[k], EnemyW, EnemyH))
                {
                    hit = k;
                    break;
                }
            }
            if (hit < 0)
            {
                continue;
            }
            _pbOn[i] = false;
            _enX.RemoveAt(hit);
            _enY.RemoveAt(hit);
            _enCd.RemoveAt(hit);
            EnemiesKilled++;
            Score += KillScore;
        }

        // 7. an enemy bullet that touches the ship costs a life
        for (var i = 0; i < EnemyBulletPoolSize && i < _ebOn.Length; i++)
        {
            if (!_ebOn[i])
            {
                continue;
            }
            if (!Overlap(_ebX[i], _ebY[i], EnemyBulletSize, EnemyBulletSize,
                         PlayerX, PlayerY, PlayerW, PlayerH))
            {
                continue;
            }
            _ebOn[i] = false;
            Lives--;
            if (Lives <= 0)
            {
                Lives = 0;
                GameOver = true;
                Won = false;
                LastEvent = $"lost steps={Steps} wave={Wave} killed={EnemiesKilled} escaped={EnemiesEscaped} "
                            + $"score={Score}";
                return;
            }
        }

        // 8. wave transition, and the win
        if (WaveLeftToSpawn == 0 && _enX.Count == 0)
        {
            if (Wave >= WaveMax)
            {
                Won = true;
                GameOver = true;
                LastEvent = $"cleared steps={Steps} waves={Wave} killed={EnemiesKilled} "
                            + $"escaped={EnemiesEscaped} score={Score} lives={Lives}";
                return;
            }
            Wave++;
            WaveLeftToSpawn = SizeOfWave(Wave);
            SpawnCountdown = 0;
        }
        LastEvent = $"tick steps={Steps} wave={Wave} alive={_enX.Count} killed={EnemiesKilled}";
    }

    private void Recompute()
    {
        EnemiesAlive = _enX.Count;
        var enemies = new StringBuilder();
        for (var i = 0; i < _enX.Count; i++)
        {
            if (i > 0)
            {
                enemies.Append('|');
            }
            enemies.Append(_enX[i]).Append(',').Append(_enY[i]).Append(',').Append(_enCd[i]);
        }
        EnemyList = enemies.ToString();
        var bullets = new StringBuilder();
        var active = 0;
        for (var i = 0; i < BulletPoolSize && i < _pbOn.Length; i++)
        {
            if (!_pbOn[i])
            {
                continue;
            }
            if (active > 0)
            {
                bullets.Append('|');
            }
            bullets.Append(_pbX[i]).Append(',').Append(_pbY[i]);
            active++;
        }
        BulletList = bullets.ToString();
        BulletsActive = active;
        var ebullets = new StringBuilder();
        var eactive = 0;
        for (var i = 0; i < EnemyBulletPoolSize && i < _ebOn.Length; i++)
        {
            if (!_ebOn[i])
            {
                continue;
            }
            if (eactive > 0)
            {
                ebullets.Append('|');
            }
            ebullets.Append(_ebX[i]).Append(',').Append(_ebY[i]);
            eactive++;
        }
        EnemyBulletList = ebullets.ToString();
        EnemyBulletsActive = eactive;

        var hash = 0;
        hash = unchecked(hash * 31 + PlayerX);
        hash = unchecked(hash * 31 + PlayerY);
        hash = unchecked(hash * 31 + Lives);
        hash = unchecked(hash * 31 + Score);
        hash = unchecked(hash * 31 + Wave);
        hash = unchecked(hash * 31 + WaveLeftToSpawn);
        for (var i = 0; i < _enX.Count; i++)
        {
            hash = unchecked(hash * 31 + _enX[i]);
            hash = unchecked(hash * 31 + _enY[i]);
            hash = unchecked(hash * 31 + _enCd[i]);
        }
        for (var i = 0; i < BulletPoolSize && i < _pbOn.Length; i++)
        {
            if (!_pbOn[i])
            {
                continue;
            }
            hash = unchecked(hash * 31 + _pbX[i]);
            hash = unchecked(hash * 31 + _pbY[i]);
        }
        for (var i = 0; i < EnemyBulletPoolSize && i < _ebOn.Length; i++)
        {
            if (!_ebOn[i])
            {
                continue;
            }
            hash = unchecked(hash * 31 + _ebX[i]);
            hash = unchecked(hash * 31 + _ebY[i]);
        }
        StateHash = hash;
    }

    // --- nodes -------------------------------------------------------------------

    private void FreeGenerated()
    {
        foreach (var list in new[] { _enemyRects, _pbRects, _ebRects, _starRects })
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
        if (_ship != null && GodotObject.IsInstanceValid(_ship))
        {
            _ship.GetParent()?.RemoveChild(_ship);
            _ship.QueueFree();
        }
        _ship = null;
    }

    /// <summary>Builds the starfield, the ship and the three pools (every world node is runtime-created).</summary>
    private void CreateNodes()
    {
        _hud = GetNodeOrNull<Label>("Hud");
        _status = GetNodeOrNull<Label>("Status");
        FreeGenerated();

        for (var i = 0; i < StarCount; i++)
        {
            var x = (i * 137) % FieldW;
            var y = HudBottom + ((i * 251) % (FieldH - HudBottom));
            var rect = new ColorRect
            {
                Name = $"Star_{i}",
                Position = new Vector2(x, y),
                Size = new Vector2(2, 2),
                Color = i % 3 == 0 ? new Color(0.55f, 0.60f, 0.75f) : new Color(0.30f, 0.34f, 0.45f),
            };
            AddChild(rect);
            _starRects.Add(rect);
        }
        for (var i = 0; i < EnemyPool; i++)
        {
            var rect = new ColorRect
            {
                Name = $"Enemy_{i}",
                Size = new Vector2(EnemyW, EnemyH),
                Color = new Color(0.90f, 0.35f, 0.55f),
                Visible = false,
            };
            AddChild(rect);
            _enemyRects.Add(rect);
        }
        for (var i = 0; i < BulletPoolSize; i++)
        {
            var rect = new ColorRect
            {
                Name = $"PBullet_{i}",
                Size = new Vector2(BulletW, BulletH),
                Color = new Color(0.95f, 0.95f, 0.45f),
                Visible = false,
            };
            AddChild(rect);
            _pbRects.Add(rect);
        }
        for (var i = 0; i < EnemyBulletPoolSize; i++)
        {
            var rect = new ColorRect
            {
                Name = $"EBullet_{i}",
                Size = new Vector2(EnemyBulletSize, EnemyBulletSize),
                Color = new Color(0.95f, 0.55f, 0.25f),
                Visible = false,
            };
            AddChild(rect);
            _ebRects.Add(rect);
        }
        _ship = new ColorRect
        {
            Name = "PlayerShip",
            Position = new Vector2(PlayerX, PlayerY),
            Size = new Vector2(PlayerW, PlayerH),
            Color = new Color(0.35f, 0.90f, 0.85f),
        };
        AddChild(_ship);
    }

    /// <summary>Puts every sprite where the model says it is, and rewrites the HUD.</summary>
    private void ApplyBoard()
    {
        if (_ship != null)
        {
            _ship.Position = new Vector2(PlayerX, PlayerY);
            _ship.Color = GameOver && !Won ? new Color(0.90f, 0.25f, 0.25f) : new Color(0.35f, 0.90f, 0.85f);
        }
        for (var i = 0; i < _enemyRects.Count; i++)
        {
            if (i < _enX.Count)
            {
                _enemyRects[i].Position = new Vector2(_enX[i], _enY[i]);
                _enemyRects[i].Visible = true;
            }
            else
            {
                _enemyRects[i].Visible = false;
            }
        }
        for (var i = 0; i < _pbRects.Count; i++)
        {
            _pbRects[i].Position = new Vector2(_pbX[i], _pbY[i]);
            _pbRects[i].Visible = _pbOn[i];
        }
        for (var i = 0; i < _ebRects.Count; i++)
        {
            _ebRects[i].Position = new Vector2(_ebX[i], _ebY[i]);
            _ebRects[i].Visible = _ebOn[i];
        }
        if (_hud != null)
        {
            _hud.Text = $"WAVE {Wave}/{WaveMax}  LIVES {Lives}  SCORE {Score}  ALIVE {EnemiesAlive}  "
                        + $"KILLED {EnemiesKilled}  ESCAPED {EnemiesEscaped}  SHOTS {BulletsFired}";
        }
        if (_status != null)
        {
            _status.Text = GameOver ? (Won ? "WAVE CLEARED" : "GAME OVER") : "SECTOR 1";
        }
    }

    public override void _Ready()
    {
        CreateNodes();
        ResetCounters();
        Recompute();
        ApplyBoard();
        GD.Print($"RTYPE_READY name={Name} field={FieldW}x{FieldH} waves={WaveSizes.Length} state_hash={StateHash}");
    }

    private void ResetCounters()
    {
        PlayerX = PlayerStartX;
        PlayerY = PlayerStartY;
        Lives = StartLives;
        Score = 0;
        Wave = 1;
        WaveMax = WaveSizes.Length;
        WaveLeftToSpawn = SizeOfWave(1);
        SpawnCountdown = 0;
        EnemiesSpawned = 0;
        EnemiesAlive = 0;
        EnemiesKilled = 0;
        EnemiesEscaped = 0;
        BulletsFired = 0;
        BulletsActive = 0;
        EnemyShotsFired = 0;
        EnemyBulletsActive = 0;
        Steps = 0;
        Elapsed = 0.0f;
        Ticks = 0;
        AutoClock = 0.0f;
        AutoTicks = 0;
        LastAutoSteps = 0;
        LastHookSteps = 0;
        _autoAccum = 0.0f;
        PollInput = false;
        InputShots = 0;
        _prevFire = false;
        Won = false;
        GameOver = false;
        Moves = 0;
        RejectedMoves = 0;
        ProbeX = -1;
        ProbeY = -1;
        ProbeValue = -1;
        ProbeState = "";
        _enX.Clear();
        _enY.Clear();
        _enCd.Clear();
        for (var i = 0; i < _pbOn.Length; i++)
        {
            _pbOn[i] = false;
            _ebOn[i] = false;
        }
        LastEvent = "reset";
    }

    // --- the public surface a session drives ---------------------------------------

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
        LastEvent = $"stepframes requested={steps} applied={applied} steps={Steps} wave={Wave} "
                    + $"alive={EnemiesAlive} killed={EnemiesKilled} escaped={EnemiesEscaped} lives={Lives} "
                    + $"bullets={BulletsActive} ebullets={EnemyBulletsActive} over={GameOver} won={Won}";
        return LastEvent;
    }

    /// <summary>Moves the ship <paramref name="dx"/>,<paramref name="dy"/> pixels, or refuses at the edge.</summary>
    public string MovePlayer(int dx, int dy)
    {
        if (GameOver)
        {
            RejectedMoves++;
            LastEvent = $"rejected reason=game_over at={PlayerX},{PlayerY}";
            return LastEvent;
        }
        var nx = PlayerX + dx;
        var ny = PlayerY + dy;
        if (nx < 0)
        {
            nx = 0;
        }
        if (nx > PlayerMaxX())
        {
            nx = PlayerMaxX();
        }
        if (ny < HudBottom)
        {
            ny = HudBottom;
        }
        if (ny > PlayerMaxY())
        {
            ny = PlayerMaxY();
        }
        var moved = nx != PlayerX || ny != PlayerY;
        if (!moved)
        {
            RejectedMoves++;
            LastEvent = $"rejected reason=clamped at={PlayerX},{PlayerY} requested={dx},{dy}";
        }
        else
        {
            PlayerX = nx;
            PlayerY = ny;
            Moves++;
            LastEvent = $"moved to={PlayerX},{PlayerY} requested={dx},{dy}";
        }
        Recompute();
        ApplyBoard();
        return LastEvent;
    }

    /// <summary>Fires one player bullet from the ship's nose, or refuses when the pool is full.</summary>
    public string FireBullet()
    {
        if (GameOver)
        {
            LastEvent = $"rejected reason=game_over shots={BulletsFired}";
            return LastEvent;
        }
        var free = -1;
        for (var i = 0; i < BulletPoolSize && i < _pbOn.Length; i++)
        {
            if (!_pbOn[i])
            {
                free = i;
                break;
            }
        }
        if (free < 0)
        {
            LastEvent = $"rejected reason=pool_full shots={BulletsFired} active={BulletsActive}";
            return LastEvent;
        }
        _pbOn[free] = true;
        _pbX[free] = PlayerX + PlayerW;
        _pbY[free] = PlayerY + (PlayerH - BulletH) / 2;
        BulletsFired++;
        Recompute();
        ApplyBoard();
        LastEvent = $"fired at={_pbX[free]},{_pbY[free]} shots={BulletsFired}";
        return LastEvent;
    }

    /// <summary>Records what stands at one field point into the Probe* properties, so an assert can name it.</summary>
    public string ProbeAt(int x, int y)
    {
        ProbeX = x;
        ProbeY = y;
        ProbeValue = -1;
        if (x < 0 || x >= FieldW || y < 0 || y >= FieldH)
        {
            ProbeState = "outside";
        }
        else if (x >= PlayerX && x < PlayerX + PlayerW && y >= PlayerY && y < PlayerY + PlayerH)
        {
            ProbeState = "player";
        }
        else
        {
            var state = "empty";
            for (var i = 0; i < _enX.Count; i++)
            {
                if (x >= _enX[i] && x < _enX[i] + EnemyW && y >= _enY[i] && y < _enY[i] + EnemyH)
                {
                    state = "enemy";
                    ProbeValue = i;
                    break;
                }
            }
            if (state == "empty")
            {
                for (var i = 0; i < EnemyBulletPoolSize && i < _ebOn.Length; i++)
                {
                    if (_ebOn[i] && x >= _ebX[i] && x < _ebX[i] + EnemyBulletSize
                        && y >= _ebY[i] && y < _ebY[i] + EnemyBulletSize)
                    {
                        state = "enemy_bullet";
                        ProbeValue = i;
                        break;
                    }
                }
            }
            if (state == "empty")
            {
                for (var i = 0; i < BulletPoolSize && i < _pbOn.Length; i++)
                {
                    if (_pbOn[i] && x >= _pbX[i] && x < _pbX[i] + BulletW
                        && y >= _pbY[i] && y < _pbY[i] + BulletH)
                    {
                        state = "bullet";
                        ProbeValue = i;
                        break;
                    }
                }
            }
            ProbeState = state;
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
        GD.Print($"RTYPE_AUTO auto={AutoClock}");
        return LastEvent;
    }

    /// <summary>Switches the declared-input polling on or off (the default is off).</summary>
    public string SetPollInput(bool enabled)
    {
        PollInput = enabled;
        _prevFire = false;
        LastEvent = $"poll_input={PollInput}";
        return LastEvent;
    }

    private void HandleInput()
    {
        var fire = Input.IsActionPressed("rt_fire");
        // Press edges only: a key a scenario injected and never released fires exactly one bullet
        // instead of repeating at the frame rate.
        if (fire && !_prevFire && !GameOver)
        {
            FireBullet();
            InputShots++;
        }
        _prevFire = fire;
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
        return $"field={FieldW}x{FieldH} hud={HudBottom} player={PlayerX},{PlayerY} speed={PlayerSpeed} "
               + $"lives={Lives} score={Score} wave={Wave} wave_max={WaveMax} wave_left={WaveLeftToSpawn} "
               + $"countdown={SpawnCountdown} spawned={EnemiesSpawned} alive={EnemiesAlive} "
               + $"killed={EnemiesKilled} escaped={EnemiesEscaped} shots={BulletsFired} "
               + $"bullets={BulletsActive} eshots={EnemyShotsFired} ebullets={EnemyBulletsActive} "
               + $"enemy_list={EnemyList} bullet_list={BulletList} ebullet_list={EnemyBulletList} "
               + $"state_hash={StateHash} moves={Moves} rejected={RejectedMoves} steps={Steps} "
               + $"won={Won} over={GameOver} auto={AutoClock} auto_ticks={AutoTicks} "
               + $"last_auto={LastAutoSteps} last_hook={LastHookSteps} input_shots={InputShots} "
               + $"elapsed={Elapsed:F3} ticks={Ticks} last={LastEvent}";
    }

    /// <summary>
    /// Writes the whole deterministic state in one call. Recognised keys (semicolon separated,
    /// <c>key=value</c>):
    ///
    /// <list type="bullet">
    /// <item><c>lives=N</c>, <c>score=N</c>;</item>
    /// <item><c>wave=N</c> (1-based), <c>maxwave=N</c>;</item>
    /// <item><c>left=N</c>, <c>countdown=N</c> -- exactly how much of the current wave is unspawned;</item>
    /// <item><c>player=X,Y</c> -- pin the ship;</item>
    /// <item><c>enemies=x,y,cd|x,y,cd</c> -- pin the formation, which is what makes a single-step
    /// collision assertion a statement about a state the session itself chose;</item>
    /// <item><c>bullets=x,y|...</c>, <c>ebullets=x,y|...</c> -- pin either bullet set.</item>
    /// </list>
    ///
    /// <para>The auto clock and input polling are switched OFF first, so a session's aim and the next
    /// readback are the same fact (TASK-103's TD-1 lesson: every test段 starts from its own force).</para>
    /// </summary>
    public string ForceTestState(string spec)
    {
        ResetCounters();
        var waveArg = 0;
        var maxWaveArg = 0;
        var leftArg = -1;
        var countdownArg = -1;
        foreach (var part in spec.Split(';'))
        {
            var kv = part.Split(new[] { '=' }, 2);
            if (kv.Length != 2)
            {
                continue;
            }
            switch (kv[0])
            {
                case "lives":
                    Lives = int.Parse(kv[1]);
                    break;
                case "score":
                    Score = int.Parse(kv[1]);
                    break;
                case "wave":
                    waveArg = int.Parse(kv[1]);
                    break;
                case "maxwave":
                    maxWaveArg = int.Parse(kv[1]);
                    break;
                case "left":
                    leftArg = int.Parse(kv[1]);
                    break;
                case "countdown":
                    countdownArg = int.Parse(kv[1]);
                    break;
                case "player":
                    var xy = kv[1].Split(',');
                    PlayerX = int.Parse(xy[0]);
                    PlayerY = int.Parse(xy[1]);
                    break;
                case "enemies":
                    if (kv[1].Length > 0)
                    {
                        foreach (var item in kv[1].Split('|'))
                        {
                            var f = item.Split(',');
                            _enX.Add(int.Parse(f[0]));
                            _enY.Add(int.Parse(f[1]));
                            _enCd.Add(int.Parse(f[2]));
                        }
                        EnemiesSpawned = _enX.Count;
                    }
                    break;
                case "bullets":
                    if (kv[1].Length > 0)
                    {
                        var slot = 0;
                        foreach (var item in kv[1].Split('|'))
                        {
                            var f = item.Split(',');
                            _pbOn[slot] = true;
                            _pbX[slot] = int.Parse(f[0]);
                            _pbY[slot] = int.Parse(f[1]);
                            slot++;
                        }
                        BulletsFired = slot;
                    }
                    break;
                case "ebullets":
                    if (kv[1].Length > 0)
                    {
                        var slot = 0;
                        foreach (var item in kv[1].Split('|'))
                        {
                            var f = item.Split(',');
                            _ebOn[slot] = true;
                            _ebX[slot] = int.Parse(f[0]);
                            _ebY[slot] = int.Parse(f[1]);
                            slot++;
                        }
                        EnemyShotsFired = slot;
                    }
                    break;
            }
        }
        if (maxWaveArg > 0)
        {
            WaveMax = maxWaveArg;
        }
        if (waveArg > 0)
        {
            Wave = waveArg;
        }
        WaveLeftToSpawn = leftArg >= 0 ? leftArg : SizeOfWave(Wave);
        SpawnCountdown = countdownArg >= 0 ? countdownArg : 0;
        Recompute();
        ApplyBoard();
        LastEvent = $"forced wave={Wave}/{WaveMax} left={WaveLeftToSpawn} lives={Lives} "
                    + $"player={PlayerX},{PlayerY} alive={EnemiesAlive} shots={BulletsFired} score={Score}";
        return LastEvent;
    }
}
