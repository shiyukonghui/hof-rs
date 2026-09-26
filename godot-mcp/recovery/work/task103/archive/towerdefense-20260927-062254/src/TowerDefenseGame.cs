using Godot;
using System.Collections.Generic;
using System.Text;

namespace towerdefense;

/// <summary>
/// Tower Defense -- the sixteenth C# game of the godot-mcp series (TASK-103, DECISIONS.md D151).
///
/// <para><b>Design rule</b> (inherited from the fifteen games before it): every fact the evidence
/// model needs is a real Godot property on the root node -- <see cref="MapHash"/>,
/// <see cref="PathLength"/>, <see cref="PathHash"/>, <see cref="Gold"/>, <see cref="Lives"/>,
/// <see cref="Wave"/>, <see cref="WaveLeftToSpawn"/>, <see cref="EnemiesSpawned"/>,
/// <see cref="EnemiesAlive"/>, <see cref="EnemiesKilled"/>, <see cref="EnemiesLeaked"/>,
/// <see cref="Score"/>, <see cref="TowersPlaced"/>, <see cref="TowerList"/>,
/// <see cref="EnemyList"/>, <see cref="Steps"/>, <see cref="Elapsed"/>, <see cref="Ticks"/>,
/// <see cref="Won"/>, <see cref="GameOver"/>. A session asserts these with
/// <c>running_game_assert_node_state</c>; it never parses a log line.</para>
///
/// <para><b>Integer, and therefore recomputable.</b> There is no float in the simulation. An enemy
/// advances one <b>path index</b> every <see cref="EnemySpeedOf"/> steps; a tower fires when its
/// cooldown is 0 and picks the alive enemy with the greatest path index inside
/// <see cref="RangeCells"/> (Chebyshev distance in cells); a wave of the table below spawns one
/// enemy every N steps. Every one of those is an integer rule, so the whole run is reproduced
/// exactly by the Python second implementation in
/// <c>recovery\work\task103\make_session_towerdefense.py</c> -- whose outputs are the session's
/// assertion literals.</para>
///
/// <para><b>The path is derived, not stored.</b> <see cref="MapRows"/> is an ASCII grid
/// (<c>'.'</c> ground, <c>'#'</c> path, <c>'S'</c> spawn, <c>'E'</c> exit) and the ordered path is
/// found by a deterministic walk: from <c>S</c>, repeatedly take the first path neighbour in the
/// fixed order right, down, left, up that is not the cell just left. The corridor has no branches
/// (each path cell has at most two path neighbours), so the walk is unique -- and the Python second
/// implementation runs the same walk over the same printed ASCII, which is what makes
/// <see cref="PathHash"/> recomputable from the evidence rather than from this file.</para>
///
/// <para><b>Frame-rate independence (the F-1 lesson).</b> The auto clock is a FLOAT ACCUMULATOR
/// (<c>_autoAccum += delta * AutoClock</c>), never <c>(int)(delta * rate)</c>. Two producers, two
/// properties: <see cref="LastAutoSteps"/> is what the clock applied on the last frame and
/// <see cref="LastHookSteps"/> is what the last <see cref="StepFrames"/> CALL applied. 2048's r1 run
/// (TASK-100, defect G1) proved that one property read by both producers reads the wrong number.
/// <see cref="Elapsed"/> is a monotonic float second counter that is never truncated.</para>
///
/// <para><b>All world nodes are runtime-created.</b> The scene file carries only the three static
/// nodes (Background, Hud, Status); the 101 path tiles and every tower and enemy sprite are built by
/// <see cref="CreateNodes"/> / the sprite pool. That keeps the edited scene immune to the D-3
/// duplicate-name trap and makes "a node created at run time really is drawn" part of this game's
/// own evidence.</para>
/// </summary>
public partial class TowerDefenseGame : Node2D
{
    // --- the grid ---------------------------------------------------------------
    /// <summary>Columns of the grid.</summary>
    [Export] public int Cols = 16;

    /// <summary>Rows of the grid.</summary>
    [Export] public int Rows = 12;

    /// <summary>Side of one cell in pixels.</summary>
    [Export] public int Tile = 50;

    // --- rules -----------------------------------------------------------------
    /// <summary>Tower reach, in cells (Chebyshev distance: <c>max(|dc|, |dr|)</c>).</summary>
    [Export] public int RangeCells = 3;

    /// <summary>Gold one tower costs.</summary>
    [Export] public int TowerCost = 50;

    /// <summary>Hit points one tower shot removes.</summary>
    [Export] public int TowerDamage = 10;

    /// <summary>Steps a tower waits after a shot before it may fire again.</summary>
    [Export] public int TowerCooldown = 3;

    /// <summary>Gold per kill.</summary>
    [Export] public int KillBounty = 10;

    /// <summary>Gold at the start of a fresh game.</summary>
    [Export] public int StartGold = 100;

    /// <summary>Lives at the start of a fresh game.</summary>
    [Export] public int StartLives = 5;

    /// <summary>How many enemies wave w (1-based) contains.</summary>
    [Export] public int[] WaveCounts = { 4, 5, 6 };

    /// <summary>Hit points of an enemy of wave w.</summary>
    [Export] public int[] WaveHps = { 30, 45, 60 };

    /// <summary>Steps an enemy of wave w needs per path index.</summary>
    [Export] public int[] WaveSpeeds = { 5, 4, 4 };

    /// <summary>Steps between two spawns of wave w.</summary>
    [Export] public int[] WaveIntervals = { 10, 10, 8 };

    // --- the map, and the three hashes a sample can watch ----------------------
    /// <summary>The ASCII grid, rows joined by <c>/</c>. Set from <see cref="MapRows"/> in <c>_Ready</c>.</summary>
    [Export] public string Map = "";

    /// <summary>Multiply-31 hash of <see cref="Map"/> (ground 2, path 1, spawn 4, exit 5).</summary>
    [Export] public int MapHash = 0;

    /// <summary>Number of cells on the path (spawn and exit included).</summary>
    [Export] public int PathLength = 0;

    /// <summary>Multiply-31 hash of the ordered path, one cell index (<c>row*Cols+col</c>) per step.</summary>
    [Export] public int PathHash = 0;

    // --- observable state, all of it a real Godot property ---------------------
    /// <summary>Gold in hand.</summary>
    [Export] public int Gold = 100;

    /// <summary>Lives left; an enemy that reaches the exit costs one.</summary>
    [Export] public int Lives = 5;

    /// <summary>Current wave, 1-based.</summary>
    [Export] public int Wave = 1;

    /// <summary>How many waves a full game has.</summary>
    [Export] public int WaveMax = 3;

    /// <summary>Enemies of the current wave still to spawn.</summary>
    [Export] public int WaveLeftToSpawn = 0;

    /// <summary>Steps until the next spawn of the current wave.</summary>
    [Export] public int SpawnCountdown = 0;

    /// <summary>Enemies spawned over the whole game.</summary>
    [Export] public int EnemiesSpawned = 0;

    /// <summary>Enemies alive right now.</summary>
    [Export] public int EnemiesAlive = 0;

    /// <summary>Enemies killed by towers.</summary>
    [Export] public int EnemiesKilled = 0;

    /// <summary>Enemies that reached the exit (each cost a life).</summary>
    [Export] public int EnemiesLeaked = 0;

    /// <summary>Points: <see cref="KillBounty"/> per kill.</summary>
    [Export] public int Score = 0;

    /// <summary>Towers built.</summary>
    [Export] public int TowersPlaced = 0;

    /// <summary>Towers as <c>"col,row|col,row"</c>, in build order.</summary>
    [Export] public string TowerList = "";

    /// <summary>Alive enemies as <c>"hp,path_index,accum,speed|..."</c>, in spawn order.</summary>
    [Export] public string EnemyList = "";

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

    /// <summary>Column the last <see cref="ProbeCell"/> looked at.</summary>
    [Export] public int ProbeCol = -1;

    /// <summary>Row the last <see cref="ProbeCell"/> looked at.</summary>
    [Export] public int ProbeRow = -1;

    /// <summary>Path index of the probed cell, -1 when it is not on the path.</summary>
    [Export] public int ProbeValue = -1;

    /// <summary>A readable name for the probed cell: outside / ground / path / spawn / exit / tower.</summary>
    [Export] public string ProbeState = "";

    /// <summary>When false the world ignores input (determinism rule: no polling by default).</summary>
    [Export] public bool PollInput = false;

    /// <summary>Hook steps that arrived through the declared input action.</summary>
    [Export] public int InputSteps = 0;

    /// <summary>What the last hook did -- the readback string a session quotes.</summary>
    [Export] public string LastEvent = "";

    // --- the map -----------------------------------------------------------------
    /// <summary>
    /// 16x12 corridor, serpentine, no branches: the six full rows (1, 3, 5, 7, 9, 11) are the
    /// straight runs and the five single-cell rows (2, 4, 6, 8, 10) are the links between them,
    /// alternating ends. Every path cell has at most two path neighbours, which is what makes the
    /// walk below unique.
    /// </summary>
    private static readonly string[] MapRows =
    {
        "................",
        "S###############",
        "...............#",
        "################",
        "#...............",
        "################",
        "...............#",
        "################",
        "#...............",
        "################",
        "...............#",
        "E###############",
    };

    // --- private model -----------------------------------------------------------
    private readonly List<int> _pathCells = new List<int>();
    private readonly List<int> _towerCell = new List<int>();
    private readonly List<int> _towerCd = new List<int>();
    private readonly List<int> _enemyHp = new List<int>();
    private readonly List<int> _enemyPath = new List<int>();
    private readonly List<int> _enemyAccum = new List<int>();
    private readonly List<int> _enemySpeed = new List<int>();
    private readonly List<ColorRect> _pathRects = new List<ColorRect>();
    private readonly List<ColorRect> _towerRects = new List<ColorRect>();
    private readonly List<ColorRect> _enemyRects = new List<ColorRect>();
    private const int EnemyPool = 32;
    private Label _hud;
    private Label _status;
    private float _autoAccum;
    private bool _prevStep;

    private int Idx(int col, int row)
    {
        return row * Cols + col;
    }

    private bool InGrid(int col, int row)
    {
        return col >= 0 && col < Cols && row >= 0 && row < Rows;
    }

    private char CharAt(int col, int row)
    {
        return InGrid(col, row) ? MapRows[row][col] : '?';
    }

    private static bool IsPathChar(char ch)
    {
        return ch == '#' || ch == 'S' || ch == 'E';
    }

    private int SpeedOfWave(int wave)
    {
        var index = wave - 1;
        return index >= 0 && index < WaveSpeeds.Length ? WaveSpeeds[index] : 5;
    }

    private int CountOfWave(int wave)
    {
        var index = wave - 1;
        return index >= 0 && index < WaveCounts.Length ? WaveCounts[index] : 4;
    }

    private int HpOfWave(int wave)
    {
        var index = wave - 1;
        return index >= 0 && index < WaveHps.Length ? WaveHps[index] : 30;
    }

    private int IntervalOfWave(int wave)
    {
        var index = wave - 1;
        return index >= 0 && index < WaveIntervals.Length ? WaveIntervals[index] : 10;
    }

    /// <summary>
    /// The ordered path: a deterministic walk from <c>S</c> that always takes the first path
    /// neighbour in the order right, down, left, up, skipping the cell it just came from.
    /// </summary>
    private void BuildPath()
    {
        _pathCells.Clear();
        var startCol = -1;
        var startRow = -1;
        for (var row = 0; row < Rows && startCol < 0; row++)
        {
            for (var col = 0; col < Cols; col++)
            {
                if (MapRows[row][col] == 'S')
                {
                    startCol = col;
                    startRow = row;
                    break;
                }
            }
        }
        if (startCol < 0)
        {
            return;
        }
        var currentCol = startCol;
        var currentRow = startRow;
        var previousCol = -1;
        var previousRow = -1;
        var guard = 0;
        while (guard++ < Cols * Rows)
        {
            _pathCells.Add(Idx(currentCol, currentRow));
            if (MapRows[currentRow][currentCol] == 'E')
            {
                break;
            }
            var moved = false;
            int[] dc = { 1, 0, -1, 0 };
            int[] dr = { 0, 1, 0, -1 };
            for (var k = 0; k < 4 && !moved; k++)
            {
                var nc = currentCol + dc[k];
                var nr = currentRow + dr[k];
                if (!InGrid(nc, nr))
                {
                    continue;
                }
                if (nc == previousCol && nr == previousRow)
                {
                    continue;
                }
                if (!IsPathChar(MapRows[nr][nc]))
                {
                    continue;
                }
                previousCol = currentCol;
                previousRow = currentRow;
                currentCol = nc;
                currentRow = nr;
                moved = true;
            }
            if (!moved)
            {
                break;
            }
        }
    }

    private void Recompute()
    {
        Map = string.Join("/", MapRows);
        var mapHash = 0;
        foreach (var row in MapRows)
        {
            foreach (var ch in row)
            {
                var weight = ch == '#' ? 1 : ch == 'S' ? 4 : ch == 'E' ? 5 : 2;
                mapHash = unchecked(mapHash * 31 + weight);
            }
        }
        MapHash = mapHash;
        PathLength = _pathCells.Count;
        var pathHash = 0;
        foreach (var cell in _pathCells)
        {
            pathHash = unchecked(pathHash * 31 + cell);
        }
        PathHash = pathHash;
        EnemiesAlive = _enemyHp.Count;
        RebuildListStrings();
    }

    private void RebuildListStrings()
    {
        var towers = new StringBuilder();
        for (var i = 0; i < _towerCell.Count; i++)
        {
            if (i > 0)
            {
                towers.Append('|');
            }
            towers.Append(_towerCell[i] % Cols).Append(',').Append(_towerCell[i] / Cols);
        }
        TowerList = towers.ToString();
        var enemies = new StringBuilder();
        for (var i = 0; i < _enemyHp.Count; i++)
        {
            if (i > 0)
            {
                enemies.Append('|');
            }
            enemies.Append(_enemyHp[i]).Append(',').Append(_enemyPath[i]).Append(',')
                   .Append(_enemyAccum[i]).Append(',').Append(_enemySpeed[i]);
        }
        EnemyList = enemies.ToString();
    }

    public override void _Ready()
    {
        BuildPath();
        CreateNodes();
        ResetCounters();
        Recompute();
        ApplyBoard();
        GD.Print($"TOWERDEFENSE_READY name={Name} path={PathLength} map_hash={MapHash} path_hash={PathHash}");
    }

    private void ResetCounters()
    {
        Gold = StartGold;
        Lives = StartLives;
        Wave = 1;
        WaveMax = WaveCounts.Length;
        WaveLeftToSpawn = CountOfWave(1);
        SpawnCountdown = 0;
        EnemiesSpawned = 0;
        EnemiesKilled = 0;
        EnemiesLeaked = 0;
        Score = 0;
        TowersPlaced = 0;
        Steps = 0;
        Elapsed = 0.0f;
        Ticks = 0;
        AutoClock = 0.0f;
        AutoTicks = 0;
        LastAutoSteps = 0;
        LastHookSteps = 0;
        _autoAccum = 0.0f;
        PollInput = false;
        InputSteps = 0;
        _prevStep = false;
        Won = false;
        GameOver = false;
        ProbeCol = -1;
        ProbeRow = -1;
        ProbeValue = -1;
        ProbeState = "";
        _towerCell.Clear();
        _towerCd.Clear();
        _enemyHp.Clear();
        _enemyPath.Clear();
        _enemyAccum.Clear();
        _enemySpeed.Clear();
        LastEvent = "reset";
    }

    private Color TileColor(int pathIndex, char ch)
    {
        if (ch == 'S')
        {
            return new Color(0.95f, 0.85f, 0.25f);
        }
        if (ch == 'E')
        {
            return new Color(0.30f, 0.85f, 0.40f);
        }
        // a gradient along the path so the picture visibly encodes progress
        var t = PathLength > 1 ? (float)pathIndex / (PathLength - 1) : 0.0f;
        return new Color(0.16f + 0.20f * t, 0.18f + 0.10f * t, 0.26f + 0.30f * t);
    }

    private void FreeGenerated()
    {
        foreach (var node in _pathRects)
        {
            if (GodotObject.IsInstanceValid(node))
            {
                node.GetParent()?.RemoveChild(node);
                node.QueueFree();
            }
        }
        _pathRects.Clear();
        foreach (var node in _towerRects)
        {
            if (GodotObject.IsInstanceValid(node))
            {
                node.GetParent()?.RemoveChild(node);
                node.QueueFree();
            }
        }
        _towerRects.Clear();
        foreach (var node in _enemyRects)
        {
            if (GodotObject.IsInstanceValid(node))
            {
                node.GetParent()?.RemoveChild(node);
                node.QueueFree();
            }
        }
        _enemyRects.Clear();
    }

    /// <summary>Builds the static HUD pair and every path tile (run once per map).</summary>
    private void CreateNodes()
    {
        _hud = GetNodeOrNull<Label>("Hud");
        _status = GetNodeOrNull<Label>("Status");
        FreeGenerated();
        for (var i = 0; i < _pathCells.Count; i++)
        {
            var cell = _pathCells[i];
            var col = cell % Cols;
            var row = cell / Cols;
            var rect = new ColorRect
            {
                Name = $"Path_{row}_{col}",
                Position = new Vector2(col * Tile + 2, row * Tile + 2),
                Size = new Vector2(Tile - 4, Tile - 4),
                Color = TileColor(i, CharAt(col, row)),
            };
            AddChild(rect);
            _pathRects.Add(rect);
        }
        for (var i = 0; i < EnemyPool; i++)
        {
            var rect = new ColorRect
            {
                Name = $"Enemy_{i}",
                Size = new Vector2(30, 30),
                Color = new Color(0.95f, 0.30f, 0.30f),
                Visible = false,
            };
            AddChild(rect);
            _enemyRects.Add(rect);
        }
    }

    private void AddTowerSprite(int col, int row)
    {
        var rect = new ColorRect
        {
            Name = $"Tower_{row}_{col}",
            Position = new Vector2(col * Tile + 5, row * Tile + 5),
            Size = new Vector2(Tile - 10, Tile - 10),
            Color = new Color(0.30f, 0.85f, 0.95f),
        };
        AddChild(rect);
        _towerRects.Add(rect);
    }

    /// <summary>Puts every sprite where the model says it is, and rewrites the HUD.</summary>
    private void ApplyBoard()
    {
        for (var i = 0; i < _towerCell.Count && i < _towerRects.Count; i++)
        {
            var cell = _towerCell[i];
            var col = cell % Cols;
            var row = cell / Cols;
            _towerRects[i].Position = new Vector2(col * Tile + 5, row * Tile + 5);
            _towerRects[i].Visible = true;
        }
        for (var i = 0; i < _enemyRects.Count; i++)
        {
            if (i < _enemyHp.Count && _enemyPath[i] < _pathCells.Count)
            {
                var cell = _pathCells[_enemyPath[i]];
                var col = cell % Cols;
                var row = cell / Cols;
                _enemyRects[i].Position = new Vector2(col * Tile + 10, row * Tile + 10);
                var hurt = HpOfWave(Wave) > 0 ? (float)_enemyHp[i] / (HpOfWave(Wave) * 3.0f) : 0.0f;
                _enemyRects[i].Color = new Color(0.95f, 0.30f + 0.45f * (1.0f - hurt), 0.30f);
                _enemyRects[i].Visible = true;
            }
            else
            {
                _enemyRects[i].Visible = false;
            }
        }
        if (_hud != null)
        {
            _hud.Text = $"WAVE {Wave}/{WaveMax}  LIVES {Lives}  GOLD {Gold}  ALIVE {EnemiesAlive}  "
                        + $"KILLED {EnemiesKilled}  LEAK {EnemiesLeaked}  STEP {Steps}";
        }
        if (_status != null)
        {
            _status.Text = GameOver ? (Won ? "PATH HELD" : "OVERRUN") : "DEFEND THE PATH";
        }
    }

    // --- the rules ---------------------------------------------------------------

    private void SpawnOne()
    {
        _enemyHp.Add(HpOfWave(Wave));
        _enemyPath.Add(0);
        _enemyAccum.Add(0);
        _enemySpeed.Add(SpeedOfWave(Wave));
        EnemiesSpawned++;
    }

    /// <summary>One fixed simulation step: spawn, move, fire, then the wave and win checks.</summary>
    private void Tick()
    {
        if (GameOver)
        {
            return;
        }
        Steps++;

        // 1. spawn at most one enemy of the current wave
        if (WaveLeftToSpawn > 0)
        {
            if (SpawnCountdown <= 0)
            {
                SpawnOne();
                WaveLeftToSpawn--;
                SpawnCountdown = IntervalOfWave(Wave);
            }
            else
            {
                SpawnCountdown--;
            }
        }

        // 2. move every enemy along the path, in spawn order
        for (var i = 0; i < _enemyHp.Count; i++)
        {
            _enemyAccum[i]++;
            if (_enemyAccum[i] >= _enemySpeed[i])
            {
                _enemyAccum[i] = 0;
                _enemyPath[i]++;
            }
        }
        // 3. remove the ones that reached the exit (order preserved)
        for (var i = _enemyHp.Count - 1; i >= 0; i--)
        {
            if (_enemyPath[i] >= PathLength - 1)
            {
                _enemyHp.RemoveAt(i);
                _enemyPath.RemoveAt(i);
                _enemyAccum.RemoveAt(i);
                _enemySpeed.RemoveAt(i);
                EnemiesLeaked++;
                Lives--;
            }
        }
        if (Lives <= 0)
        {
            Lives = 0;
            GameOver = true;
            Won = false;
            LastEvent = $"lost steps={Steps} wave={Wave} killed={EnemiesKilled} leaked={EnemiesLeaked} "
                        + $"score={Score}";
            return;
        }

        // 4. towers fire, in build order; each shot kills at most one enemy
        for (var t = 0; t < _towerCell.Count; t++)
        {
            if (_towerCd[t] > 0)
            {
                _towerCd[t]--;
                continue;
            }
            var towerCol = _towerCell[t] % Cols;
            var towerRow = _towerCell[t] / Cols;
            var best = -1;
            var bestPath = -1;
            for (var i = 0; i < _enemyHp.Count; i++)
            {
                if (_enemyPath[i] >= _pathCells.Count)
                {
                    continue;
                }
                var cell = _pathCells[_enemyPath[i]];
                var dc = System.Math.Abs(cell % Cols - towerCol);
                var dr = System.Math.Abs(cell / Cols - towerRow);
                var distance = dc > dr ? dc : dr;
                if (distance > RangeCells)
                {
                    continue;
                }
                if (_enemyPath[i] > bestPath)
                {
                    bestPath = _enemyPath[i];
                    best = i;
                }
            }
            if (best < 0)
            {
                continue;
            }
            _towerCd[t] = TowerCooldown;
            _enemyHp[best] -= TowerDamage;
            if (_enemyHp[best] <= 0)
            {
                _enemyHp.RemoveAt(best);
                _enemyPath.RemoveAt(best);
                _enemyAccum.RemoveAt(best);
                _enemySpeed.RemoveAt(best);
                EnemiesKilled++;
                Score += KillBounty;
                Gold += KillBounty;
            }
        }

        // 5. wave transition, and the win
        if (WaveLeftToSpawn == 0 && _enemyHp.Count == 0)
        {
            if (Wave >= WaveMax)
            {
                Won = true;
                GameOver = true;
                LastEvent = $"held steps={Steps} waves={Wave} killed={EnemiesKilled} leaked={EnemiesLeaked} "
                            + $"score={Score} lives={Lives}";
                return;
            }
            Wave++;
            WaveLeftToSpawn = CountOfWave(Wave);
            SpawnCountdown = 0;
        }
        EnemiesAlive = _enemyHp.Count;
        RebuildListStrings();
    }

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
        LastEvent = $"stepframes requested={steps} applied={applied} steps={Steps} wave={Wave} "
                    + $"alive={EnemiesAlive} killed={EnemiesKilled} leaked={EnemiesLeaked} lives={Lives} "
                    + $"over={GameOver} won={Won}";
        Recompute();
        ApplyBoard();
        return LastEvent;
    }

    /// <summary>Builds a tower on a ground cell, or refuses with a named reason.</summary>
    public string PlaceTower(int col, int row)
    {
        if (GameOver)
        {
            LastEvent = $"rejected reason=game_over at={col},{row} won={Won}";
            return LastEvent;
        }
        if (!InGrid(col, row))
        {
            LastEvent = $"rejected reason=out_of_bounds at={col},{row}";
            return LastEvent;
        }
        if (CharAt(col, row) != '.')
        {
            LastEvent = $"rejected reason=not_buildable at={col},{row} cell={CharAt(col, row)}";
            return LastEvent;
        }
        if (_towerCell.Contains(Idx(col, row)))
        {
            LastEvent = $"rejected reason=occupied at={col},{row}";
            return LastEvent;
        }
        if (Gold < TowerCost)
        {
            LastEvent = $"rejected reason=no_gold at={col},{row} gold={Gold} cost={TowerCost}";
            return LastEvent;
        }
        Gold -= TowerCost;
        _towerCell.Add(Idx(col, row));
        _towerCd.Add(0);
        TowersPlaced++;
        AddTowerSprite(col, row);
        Recompute();
        ApplyBoard();
        LastEvent = $"tower placed at={col},{row} towers={TowersPlaced} gold={Gold} "
                    + $"range={RangeCells} damage={TowerDamage} cooldown={TowerCooldown}";
        return LastEvent;
    }

    /// <summary>Records what stands on one cell into the Probe* properties, so an assert can name it.</summary>
    public string ProbeCell(int col, int row)
    {
        ProbeCol = col;
        ProbeRow = row;
        if (!InGrid(col, row))
        {
            ProbeValue = -1;
            ProbeState = "outside";
        }
        else
        {
            var cell = Idx(col, row);
            var index = _pathCells.IndexOf(cell);
            ProbeValue = index;
            if (_towerCell.Contains(cell))
            {
                ProbeState = "tower";
            }
            else if (index >= 0)
            {
                ProbeState = CharAt(col, row) == 'S' ? "spawn" : CharAt(col, row) == 'E' ? "exit" : "path";
            }
            else
            {
                ProbeState = "ground";
            }
        }
        Recompute();
        LastEvent = $"probe at={col},{row} state={ProbeState} path_index={ProbeValue}";
        return LastEvent;
    }

    /// <summary>Steps per second; 0 keeps the world still (the default).</summary>
    public string SetAutoClock(float perSecond)
    {
        AutoClock = perSecond;
        _autoAccum = 0.0f;
        LastAutoSteps = 0;
        LastEvent = $"auto_clock={AutoClock}";
        GD.Print($"TOWERDEFENSE_AUTO auto={AutoClock}");
        return LastEvent;
    }

    /// <summary>Switches the declared-input polling on or off (the default is off).</summary>
    public string SetPollInput(bool enabled)
    {
        PollInput = enabled;
        _prevStep = false;
        LastEvent = $"poll_input={PollInput}";
        return LastEvent;
    }

    private void HandleInput()
    {
        var step = Input.IsActionPressed("td_auto_step");
        // Press edges only: a key a scenario injected and never released performs exactly one step
        // instead of repeating at the frame rate.
        if (step && !_prevStep && !GameOver)
        {
            StepFrames(1);
            InputSteps++;
        }
        _prevStep = step;
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
                // The clock deliberately does NOT touch LastHookSteps: that property belongs to the
                // StepFrames hook alone (two producers, two properties -- the G1 lesson).
                Recompute();
                ApplyBoard();
            }
        }
        else
        {
            LastAutoSteps = 0;
        }
    }

    /// <summary>The map, the path facts and every exported fact, on one line.</summary>
    public string Dump()
    {
        return $"map={Map} map_hash={MapHash} cols={Cols} rows={Rows} tile={Tile} "
               + $"path_len={PathLength} path_hash={PathHash} range={RangeCells} cost={TowerCost} "
               + $"damage={TowerDamage} cooldown={TowerCooldown} bounty={KillBounty} wave={Wave} "
               + $"wave_max={WaveMax} wave_left={WaveLeftToSpawn} countdown={SpawnCountdown} "
               + $"spawned={EnemiesSpawned} alive={EnemiesAlive} killed={EnemiesKilled} "
               + $"leaked={EnemiesLeaked} lives={Lives} gold={Gold} score={Score} "
               + $"towers={TowersPlaced} tower_list={TowerList} enemy_list={EnemyList} steps={Steps} "
               + $"won={Won} over={GameOver} auto={AutoClock} auto_ticks={AutoTicks} "
               + $"last_auto={LastAutoSteps} last_hook={LastHookSteps} input_steps={InputSteps} "
               + $"elapsed={Elapsed:F3} ticks={Ticks} last={LastEvent}";
    }

    /// <summary>
    /// Writes the whole deterministic state in one call. Recognised keys (semicolon separated,
    /// <c>key=value</c>):
    ///
    /// <list type="bullet">
    /// <item><c>gold=N</c>, <c>lives=N</c>, <c>score=N</c>;</item>
    /// <item><c>wave=N</c> (1-based), <c>maxwave=N</c>;</item>
    /// <item><c>left=N</c>, <c>countdown=N</c> -- exactly how much of the current wave is unspawned;</item>
    /// <item><c>towers=c,r|c,r</c> -- pin towers without paying for them;</item>
    /// <item><c>enemies=hp,path,accum,speed|...</c> -- pin the enemy list, which is what makes a
    /// single-step damage assertion a statement about a state the session itself chose.</item>
    /// </list>
    ///
    /// <para>The auto clock and input polling are switched OFF first, so a session's aim and the next
    /// readback are the same fact. A test that wants motion calls <see cref="SetAutoClock"/> or
    /// <see cref="StepFrames"/> itself.</para>
    /// </summary>
    public string ForceTestState(string spec)
    {
        _towerCell.Clear();
        _towerCd.Clear();
        _enemyHp.Clear();
        _enemyPath.Clear();
        _enemyAccum.Clear();
        _enemySpeed.Clear();
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
                case "gold":
                    Gold = int.Parse(kv[1]);
                    break;
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
                case "towers":
                    if (kv[1].Length > 0)
                    {
                        foreach (var item in kv[1].Split('|'))
                        {
                            var cr = item.Split(',');
                            _towerCell.Add(Idx(int.Parse(cr[0]), int.Parse(cr[1])));
                            _towerCd.Add(0);
                        }
                        TowersPlaced = _towerCell.Count;
                    }
                    break;
                case "enemies":
                    if (kv[1].Length > 0)
                    {
                        foreach (var item in kv[1].Split('|'))
                        {
                            var f = item.Split(',');
                            _enemyHp.Add(int.Parse(f[0]));
                            _enemyPath.Add(int.Parse(f[1]));
                            _enemyAccum.Add(int.Parse(f[2]));
                            _enemySpeed.Add(int.Parse(f[3]));
                        }
                        EnemiesSpawned = _enemyHp.Count;
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
        WaveLeftToSpawn = leftArg >= 0 ? leftArg : CountOfWave(Wave);
        SpawnCountdown = countdownArg >= 0 ? countdownArg : 0;
        CreateNodes();
        for (var i = 0; i < _towerCell.Count; i++)
        {
            AddTowerSprite(_towerCell[i] % Cols, _towerCell[i] / Cols);
        }
        Recompute();
        ApplyBoard();
        LastEvent = $"forced wave={Wave}/{WaveMax} left={WaveLeftToSpawn} lives={Lives} gold={Gold} "
                    + $"towers={TowersPlaced} alive={EnemiesAlive} score={Score}";
        return LastEvent;
    }
}
