using Godot;
using System.Collections.Generic;
using System.Text;

namespace missilecommand;

/// <summary>
/// Missile Command -- the seventeenth C# game of the godot-mcp series (TASK-103, DECISIONS.md D151).
///
/// <para><b>Design rule</b> (inherited from the sixteen games before it): every fact the evidence
/// model needs is a real Godot property on the root node -- <see cref="CitiesAlive"/>,
/// <see cref="CityList"/>, <see cref="Ammo"/>, <see cref="AmmoList"/>, <see cref="IncomingAlive"/>,
/// <see cref="IncomingList"/>, <see cref="InterceptorAlive"/>, <see cref="InterceptorList"/>,
/// <see cref="ExplosionsActive"/>, <see cref="ExplosionList"/>, <see cref="Destroyed"/>,
/// <see cref="Leaked"/>, <see cref="Score"/>, <see cref="Wave"/>, <see cref="Steps"/>,
/// <see cref="CityHash"/>, <see cref="WorldHash"/>, <see cref="Won"/>, <see cref="GameOver"/>.
/// A session asserts these with <c>running_game_assert_node_state</c>; it never parses a log
/// line.</para>
///
/// <para><b>Integer, and therefore recomputable.</b> Nothing here is a float. A missile travels
/// from <c>(x0,y0)</c> to <c>(tx,ty)</c> in <c>dur</c> steps and its position at step <c>k</c> is
/// <c>x0 + DivFloor((tx-x0)*k, dur)</c> -- floor division, spelled out in both implementations so
/// the two cannot disagree about a negative numerator. An explosion destroys every incoming missile
/// inside <see cref="ExplosionRadius"/> (squared distance, integer) and an incoming missile that
/// arrives destroys every city inside <see cref="BlastRadius"/>. The wave table, the spawn order and
/// the linear congruential generator (<c>seed = (seed*1103515245 + 12345) mod 2^31</c>, x from
/// <c>(seed &gt;&gt; 16) % 760 + 20</c>) are integers too, so the whole run is reproduced exactly by the
/// Python second implementation in <c>recovery\work\task103\make_session_missilecommand.py</c> --
/// whose outputs are the session's assertion literals.</para>
///
/// <para><b>Frame-rate independence (the F-1 lesson).</b> The auto clock is a FLOAT ACCUMULATOR
/// (<c>_autoAccum += delta * AutoClock</c>), never <c>(int)(delta * rate)</c>. Two producers, two
/// properties: <see cref="LastAutoSteps"/> is what the clock applied on the last frame and
/// <see cref="LastHookSteps"/> is what the last <see cref="StepFrames"/> CALL applied. 2048's r1 run
/// (TASK-100, defect G1) proved that one property read by both producers reads the wrong number.
/// <see cref="Elapsed"/> is a monotonic float second counter that is never truncated.</para>
///
/// <para><b>All world nodes are runtime-created.</b> The scene file carries only the three static
/// nodes (Background, Hud, Status); the six cities, the three batteries and the three sprite pools
/// (incoming missiles, interceptors, explosions) are built by <see cref="CreateNodes"/>.</para>
/// </summary>
public partial class MissileCommandGame : Node2D
{
    // --- the field ---------------------------------------------------------------
    /// <summary>Playfield width in pixels.</summary>
    [Export] public int FieldW = 800;

    /// <summary>Playfield height in pixels.</summary>
    [Export] public int FieldH = 600;

    /// <summary>X of each city's centre.</summary>
    [Export] public int[] CityXs = { 80, 200, 320, 440, 560, 680 };

    /// <summary>Y of each city's centre.</summary>
    [Export] public int CityY = 548;

    /// <summary>X of each battery; every battery fires straight from its own muzzle.</summary>
    [Export] public int[] BatteryXs = { 40, 400, 760 };

    /// <summary>Y of every battery muzzle.</summary>
    [Export] public int BatteryY = 586;

    // --- rules -----------------------------------------------------------------
    /// <summary>Shots one battery holds; refilled at the start of every wave.</summary>
    [Export] public int AmmoPerBattery = 10;

    /// <summary>Pixels one interceptor covers per step.</summary>
    [Export] public int InterceptorSpeed = 12;

    /// <summary>Steps an interceptor's explosion lasts (it resolves on every one of them).</summary>
    [Export] public int ExplosionTicks = 8;

    /// <summary>Reach of an interceptor explosion, in pixels.</summary>
    [Export] public int ExplosionRadius = 34;

    /// <summary>Reach of an incoming missile's arrival blast, in pixels.</summary>
    [Export] public int BlastRadius = 28;

    /// <summary>Points one destroyed incoming missile is worth.</summary>
    [Export] public int PointsPerKill = 25;

    /// <summary>Points one surviving city is worth at the end of a wave.</summary>
    [Export] public int PointsPerCity = 100;

    /// <summary>How many incoming missiles wave w (1-based) contains.</summary>
    [Export] public int[] WaveCounts = { 4, 6, 8 };

    /// <summary>Pixels per step an incoming missile of wave w covers.</summary>
    [Export] public int[] WaveSpeeds = { 8, 10, 12 };

    /// <summary>Steps between two spawns of wave w.</summary>
    [Export] public int[] WaveIntervals = { 45, 36, 30 };

    // --- observable state, all of it a real Godot property ---------------------
    /// <summary>Seed of the spawn generator.</summary>
    [Export] public int Seed = 20250927;

    /// <summary>Cities still standing.</summary>
    [Export] public int CitiesAlive = 6;

    /// <summary>Cities as <c>alive|alive|...</c>, in x order.</summary>
    [Export] public string CityList = "";

    /// <summary>Shots left across every battery.</summary>
    [Export] public int Ammo = 30;

    /// <summary>Shots left per battery, <c>a|b|c</c>.</summary>
    [Export] public string AmmoList = "";

    /// <summary>Incoming missiles in flight.</summary>
    [Export] public int IncomingAlive = 0;

    /// <summary>Incoming missiles as <c>x,y,tx,ty,k,dur,x0,y0</c>, in spawn order.</summary>
    [Export] public string IncomingList = "";

    /// <summary>Interceptors in flight.</summary>
    [Export] public int InterceptorAlive = 0;

    /// <summary>Interceptors as <c>x,y,tx,ty,k,dur,x0,y0</c>, in fire order.</summary>
    [Export] public string InterceptorList = "";

    /// <summary>Explosions alive right now.</summary>
    [Export] public int ExplosionsActive = 0;

    /// <summary>Explosions as <c>x,y,ticks</c>, in creation order.</summary>
    [Export] public string ExplosionList = "";

    /// <summary>Incoming missiles destroyed by an explosion.</summary>
    [Export] public int Destroyed = 0;

    /// <summary>Incoming missiles that arrived (each may have taken a city with it).</summary>
    [Export] public int Leaked = 0;

    /// <summary>Incoming missiles spawned over the whole game.</summary>
    [Export] public int Spawned = 0;

    /// <summary>Interceptors fired over the whole game.</summary>
    [Export] public int Fired = 0;

    /// <summary>Cities lost over the whole game.</summary>
    [Export] public int CitiesLost = 0;

    /// <summary>Points.</summary>
    [Export] public int Score = 0;

    /// <summary>Current wave, 1-based.</summary>
    [Export] public int Wave = 1;

    /// <summary>How many waves a full game has.</summary>
    [Export] public int WaveMax = 3;

    /// <summary>Incoming missiles of the current wave still to spawn.</summary>
    [Export] public int WaveLeftToSpawn = 0;

    /// <summary>Steps until the next spawn of the current wave.</summary>
    [Export] public int SpawnCountdown = 0;

    /// <summary>Multiply-31 hash of <see cref="CityList"/>.</summary>
    [Export] public int CityHash = 0;

    /// <summary>Multiply-31 hash of the whole deterministic world (see <see cref="Recompute"/>).</summary>
    [Export] public int WorldHash = 0;

    /// <summary>Simulation steps taken (one per fixed tick; see <see cref="StepFrames"/>).</summary>
    [Export] public int Steps = 0;

    /// <summary>Seconds since the last reset: a monotonic FLOAT accumulator, never truncated.</summary>
    [Export] public float Elapsed = 0.0f;

    /// <summary>Frames processed since the last reset.</summary>
    [Export] public int Ticks = 0;

    /// <summary>Auto steps per second; 0 keeps the field still (the default).</summary>
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

    /// <summary>True when every wave was cleared with at least one city standing.</summary>
    [Export] public bool Won = false;

    /// <summary>True when the game ended: every wave cleared, or every city lost.</summary>
    [Export] public bool GameOver = false;

    /// <summary>X the last <see cref="ProbePoint"/> looked at.</summary>
    [Export] public int ProbeX = -1;

    /// <summary>Y the last <see cref="ProbePoint"/> looked at.</summary>
    [Export] public int ProbeY = -1;

    /// <summary>Index of the city or battery the probed point is inside, -1 for plain ground.</summary>
    [Export] public int ProbeValue = -1;

    /// <summary>A readable name for the probed point: outside / ground / city / battery.</summary>
    [Export] public string ProbeState = "";

    /// <summary>When false the field ignores input (determinism rule: no polling by default).</summary>
    [Export] public bool PollInput = false;

    /// <summary>Shots that arrived through the declared input action.</summary>
    [Export] public int InputShots = 0;

    /// <summary>What the last hook did -- the readback string a session quotes.</summary>
    [Export] public string LastEvent = "";

    // --- private model -----------------------------------------------------------
    private readonly List<bool> _cityAlive = new List<bool>();
    private readonly List<int> _batteryAmmo = new List<int>();
    // incoming: x, y, target x, target y, step, duration
    private readonly List<int[]> _incoming = new List<int[]>();
    private readonly List<int[]> _interceptor = new List<int[]>();
    private readonly List<int[]> _explosion = new List<int[]>();
    private readonly List<ColorRect> _cityRects = new List<ColorRect>();
    private readonly List<ColorRect> _batteryRects = new List<ColorRect>();
    private readonly List<ColorRect> _incomingRects = new List<ColorRect>();
    private readonly List<ColorRect> _interceptorRects = new List<ColorRect>();
    private readonly List<ColorRect> _explosionRects = new List<ColorRect>();
    private const int IncomingPool = 40;
    private const int InterceptorPool = 40;
    private const int ExplosionPool = 40;
    private Label _hud;
    private Label _status;
    private int _randState;
    private float _autoAccum;
    private bool _prevFire;

    /// <summary>C# truncates toward zero; Python's <c>//</c> floors. This is the floor, in both.</summary>
    private static int DivFloor(int a, int b)
    {
        var q = a / b;
        if (a % b != 0 && (a < 0) != (b < 0))
        {
            q--;
        }
        return q;
    }

    private static int CeilDiv(int a, int b)
    {
        return (a + b - 1) / b;
    }

    private int NextRand()
    {
        _randState = unchecked((int)(((long)_randState * 1103515245L + 12345L) & 0x7FFFFFFFL));
        return _randState;
    }

    private int CountOfWave(int wave)
    {
        var index = wave - 1;
        return index >= 0 && index < WaveCounts.Length ? WaveCounts[index] : 4;
    }

    private int SpeedOfWave(int wave)
    {
        var index = wave - 1;
        return index >= 0 && index < WaveSpeeds.Length ? WaveSpeeds[index] : 8;
    }

    private int IntervalOfWave(int wave)
    {
        var index = wave - 1;
        return index >= 0 && index < WaveIntervals.Length ? WaveIntervals[index] : 45;
    }

    /// <summary>
    /// The floor interpolation both implementations share. Static on purpose: the
    /// pinned-missile reader (<see cref="AddMissiles"/>) is static too, and the two must be the same
    /// function or a pinned trajectory would not be the trajectory the rules produce.
    /// </summary>
    private static int PosAt(int from, int to, int step, int duration)
    {
        if (duration <= 0)
        {
            return to;
        }
        return from + DivFloor((to - from) * step, duration);
    }

    private void RebuildListStrings()
    {
        var cities = new StringBuilder();
        for (var i = 0; i < _cityAlive.Count; i++)
        {
            if (i > 0)
            {
                cities.Append('|');
            }
            cities.Append(_cityAlive[i] ? 1 : 0);
        }
        CityList = cities.ToString();
        var ammo = new StringBuilder();
        for (var i = 0; i < _batteryAmmo.Count; i++)
        {
            if (i > 0)
            {
                ammo.Append('|');
            }
            ammo.Append(_batteryAmmo[i]);
        }
        AmmoList = ammo.ToString();
        IncomingList = JoinMissiles(_incoming);
        InterceptorList = JoinMissiles(_interceptor);
        var blasts = new StringBuilder();
        for (var i = 0; i < _explosion.Count; i++)
        {
            if (i > 0)
            {
                blasts.Append('|');
            }
            blasts.Append(_explosion[i][0]).Append(',').Append(_explosion[i][1]).Append(',')
                  .Append(_explosion[i][2]);
        }
        ExplosionList = blasts.ToString();
        IncomingAlive = _incoming.Count;
        InterceptorAlive = _interceptor.Count;
        ExplosionsActive = _explosion.Count;
    }

    private static string JoinMissiles(List<int[]> list)
    {
        var text = new StringBuilder();
        for (var i = 0; i < list.Count; i++)
        {
            if (i > 0)
            {
                text.Append('|');
            }
            // x,y,tx,ty,k,dur,x0,y0 -- x0/y0 are the launch point, so the whole trajectory of every
            // missile in flight is in the evidence and a second implementation can continue it.
            for (var f = 0; f < 8; f++)
            {
                if (f > 0)
                {
                    text.Append(',');
                }
                text.Append(list[i][f]);
            }
        }
        return text.ToString();
    }

    private void Recompute()
    {
        CitiesAlive = 0;
        for (var i = 0; i < _cityAlive.Count; i++)
        {
            if (_cityAlive[i])
            {
                CitiesAlive++;
            }
        }
        var cityHash = 0;
        foreach (var alive in _cityAlive)
        {
            cityHash = unchecked(cityHash * 31 + (alive ? 1 : 0));
        }
        CityHash = cityHash;
        var ammo = 0;
        foreach (var left in _batteryAmmo)
        {
            ammo += left;
        }
        Ammo = ammo;
        RebuildListStrings();
        var hash = 0;
        foreach (var alive in _cityAlive)
        {
            hash = unchecked(hash * 31 + (alive ? 1 : 0));
        }
        foreach (var m in _incoming)
        {
            hash = unchecked(hash * 31 + m[0]);
            hash = unchecked(hash * 31 + m[1]);
            hash = unchecked(hash * 31 + m[4]);
        }
        foreach (var m in _interceptor)
        {
            hash = unchecked(hash * 31 + m[0]);
            hash = unchecked(hash * 31 + m[1]);
            hash = unchecked(hash * 31 + m[4]);
        }
        foreach (var b in _explosion)
        {
            hash = unchecked(hash * 31 + b[0]);
            hash = unchecked(hash * 31 + b[1]);
            hash = unchecked(hash * 31 + b[2]);
        }
        hash = unchecked(hash * 31 + Score);
        hash = unchecked(hash * 31 + Wave);
        hash = unchecked(hash * 31 + Steps);
        WorldHash = hash;
    }

    public override void _Ready()
    {
        CreateNodes();
        ResetCounters();
        Recompute();
        ApplyBoard();
        GD.Print($"MISSILECOMMAND_READY name={Name} cities={CitiesAlive} wave={Wave} city_hash={CityHash}");
    }

    private void ResetCounters()
    {
        _cityAlive.Clear();
        foreach (var unused in CityXs)
        {
            _cityAlive.Add(true);
        }
        _batteryAmmo.Clear();
        foreach (var unused in BatteryXs)
        {
            _batteryAmmo.Add(AmmoPerBattery);
        }
        _incoming.Clear();
        _interceptor.Clear();
        _explosion.Clear();
        _randState = Seed;
        Wave = 1;
        WaveMax = WaveCounts.Length;
        WaveLeftToSpawn = CountOfWave(1);
        SpawnCountdown = 0;
        Destroyed = 0;
        Leaked = 0;
        Spawned = 0;
        Fired = 0;
        CitiesLost = 0;
        Score = 0;
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
        ProbeX = -1;
        ProbeY = -1;
        ProbeValue = -1;
        ProbeState = "";
        LastEvent = "reset";
    }

    private void FreeGenerated()
    {
        FreePool(_cityRects);
        FreePool(_batteryRects);
        FreePool(_incomingRects);
        FreePool(_interceptorRects);
        FreePool(_explosionRects);
    }

    private void FreePool(List<ColorRect> pool)
    {
        foreach (var node in pool)
        {
            if (GodotObject.IsInstanceValid(node))
            {
                node.GetParent()?.RemoveChild(node);
                node.QueueFree();
            }
        }
        pool.Clear();
    }

    /// <summary>Builds the HUD pair, the cities, the batteries and the three sprite pools.</summary>
    private void CreateNodes()
    {
        _hud = GetNodeOrNull<Label>("Hud");
        _status = GetNodeOrNull<Label>("Status");
        FreeGenerated();
        for (var i = 0; i < CityXs.Length; i++)
        {
            var rect = new ColorRect
            {
                Name = $"City_{i}",
                Position = new Vector2(CityXs[i] - 30, CityY - 20),
                Size = new Vector2(60, 40),
                Color = new Color(0.35f, 0.85f, 0.45f),
            };
            AddChild(rect);
            _cityRects.Add(rect);
        }
        for (var i = 0; i < BatteryXs.Length; i++)
        {
            var rect = new ColorRect
            {
                Name = $"Battery_{i}",
                Position = new Vector2(BatteryXs[i] - 18, BatteryY - 10),
                Size = new Vector2(36, 20),
                Color = new Color(0.40f, 0.60f, 0.95f),
            };
            AddChild(rect);
            _batteryRects.Add(rect);
        }
        FillPool(_incomingRects, "Incoming_", new Vector2(6, 14), new Color(0.95f, 0.35f, 0.35f), IncomingPool);
        FillPool(_interceptorRects, "Interceptor_", new Vector2(5, 5), new Color(0.40f, 0.95f, 0.95f), InterceptorPool);
        FillPool(_explosionRects, "Blast_", new Vector2(4, 4), new Color(0.98f, 0.85f, 0.30f), ExplosionPool);
    }

    private void FillPool(List<ColorRect> pool, string prefix, Vector2 size, Color color, int count)
    {
        for (var i = 0; i < count; i++)
        {
            var rect = new ColorRect
            {
                Name = $"{prefix}{i}",
                Size = size,
                Color = color,
                Visible = false,
            };
            AddChild(rect);
            pool.Add(rect);
        }
    }

    /// <summary>Puts every sprite where the model says it is, and rewrites the HUD.</summary>
    private void ApplyBoard()
    {
        for (var i = 0; i < _cityRects.Count && i < _cityAlive.Count; i++)
        {
            _cityRects[i].Color = _cityAlive[i]
                ? new Color(0.35f, 0.85f, 0.45f)
                : new Color(0.22f, 0.16f, 0.16f);
        }
        for (var i = 0; i < _batteryRects.Count && i < _batteryAmmo.Count; i++)
        {
            _batteryRects[i].Color = _batteryAmmo[i] > 0
                ? new Color(0.40f, 0.60f, 0.95f)
                : new Color(0.25f, 0.25f, 0.30f);
        }
        for (var i = 0; i < _incomingRects.Count; i++)
        {
            if (i < _incoming.Count)
            {
                var m = _incoming[i];
                _incomingRects[i].Position = new Vector2(m[0] - 3, m[1] - 7);
                _incomingRects[i].Visible = true;
            }
            else
            {
                _incomingRects[i].Visible = false;
            }
        }
        for (var i = 0; i < _interceptorRects.Count; i++)
        {
            if (i < _interceptor.Count)
            {
                var m = _interceptor[i];
                _interceptorRects[i].Position = new Vector2(m[0] - 2, m[1] - 2);
                _interceptorRects[i].Visible = true;
            }
            else
            {
                _interceptorRects[i].Visible = false;
            }
        }
        for (var i = 0; i < _explosionRects.Count; i++)
        {
            if (i < _explosion.Count)
            {
                var b = _explosion[i];
                _explosionRects[i].Position = new Vector2(b[0] - ExplosionRadius, b[1] - ExplosionRadius);
                _explosionRects[i].Size = new Vector2(ExplosionRadius * 2, ExplosionRadius * 2);
                _explosionRects[i].Visible = true;
            }
            else
            {
                _explosionRects[i].Visible = false;
            }
        }
        if (_hud != null)
        {
            _hud.Text = $"WAVE {Wave}/{WaveMax}  CITIES {CitiesAlive}  AMMO {Ammo}  "
                        + $"INCOMING {IncomingAlive}  BLASTS {ExplosionsActive}  SCORE {Score}";
        }
        if (_status != null)
        {
            _status.Text = GameOver ? (Won ? "SECTOR SAVED" : "ALL CITIES LOST") : "DEFEND THE CITIES";
        }
    }

    // --- the rules ---------------------------------------------------------------

    private void SpawnIncoming()
    {
        var r1 = NextRand();
        var x0 = 20 + ((r1 >> 16) % 760);
        var r2 = NextRand();
        var selector = (r2 >> 16) % 8;
        int tx;
        int ty;
        if (selector < CityXs.Length)
        {
            tx = CityXs[selector];
            ty = CityY;
        }
        else
        {
            tx = 20 + ((r2 >> 16) % 760);
            ty = FieldH;
        }
        var span = System.Math.Max(System.Math.Abs(tx - x0), System.Math.Abs(ty - 0));
        var dur = CeilDiv(span, SpeedOfWave(Wave));
        if (dur < 1)
        {
            dur = 1;
        }
        _incoming.Add(new[] { x0, 0, tx, ty, 0, dur, x0, 0 });
        Spawned++;
    }

    /// <summary>One fixed simulation step: spawn, move, arrive, explode, age, wave check.</summary>
    private void Tick()
    {
        if (GameOver)
        {
            return;
        }
        Steps++;

        // 1. spawn at most one incoming missile of the current wave
        if (WaveLeftToSpawn > 0)
        {
            if (SpawnCountdown <= 0)
            {
                SpawnIncoming();
                WaveLeftToSpawn--;
                SpawnCountdown = IntervalOfWave(Wave);
            }
            else
            {
                SpawnCountdown--;
            }
        }

        // 2. move every incoming missile, in spawn order (the position is a function of the LAUNCH
        //    point and the step, so the interpolation never accumulates a rounding error)
        for (var i = 0; i < _incoming.Count; i++)
        {
            var m = _incoming[i];
            m[4]++;
            m[0] = PosAt(m[6], m[2], m[4], m[5]);
            m[1] = PosAt(m[7], m[3], m[4], m[5]);
        }
        // 3. the ones that arrived take a city with them (order preserved)
        for (var i = _incoming.Count - 1; i >= 0; i--)
        {
            if (_incoming[i][4] >= _incoming[i][5])
            {
                var tx = _incoming[i][2];
                var ty = _incoming[i][3];
                _incoming.RemoveAt(i);
                Leaked++;
                for (var c = 0; c < _cityAlive.Count; c++)
                {
                    if (!_cityAlive[c])
                    {
                        continue;
                    }
                    var dx = CityXs[c] - tx;
                    var dy = CityY - ty;
                    if (dx * dx + dy * dy <= BlastRadius * BlastRadius)
                    {
                        _cityAlive[c] = false;
                        CitiesLost++;
                    }
                }
            }
        }
        if (CitiesAliveAfter() == 0)
        {
            Recompute();
            GameOver = true;
            Won = false;
            LastEvent = $"lost steps={Steps} wave={Wave} destroyed={Destroyed} leaked={Leaked} "
                        + $"score={Score} cities=0";
            return;
        }

        // 4. move every interceptor; the ones that arrive become an explosion
        for (var i = _interceptor.Count - 1; i >= 0; i--)
        {
            var m = _interceptor[i];
            m[4]++;
            m[0] = PosAt(m[6], m[2], m[4], m[5]);
            m[1] = PosAt(m[7], m[3], m[4], m[5]);
            if (m[4] >= m[5])
            {
                _interceptor.RemoveAt(i);
                _explosion.Add(new[] { m[2], m[3], ExplosionTicks });
            }
        }

        // 5. every explosion destroys the incoming missiles inside it, in creation order
        for (var b = 0; b < _explosion.Count; b++)
        {
            var blast = _explosion[b];
            for (var i = _incoming.Count - 1; i >= 0; i--)
            {
                var dx = _incoming[i][0] - blast[0];
                var dy = _incoming[i][1] - blast[1];
                if (dx * dx + dy * dy <= ExplosionRadius * ExplosionRadius)
                {
                    _incoming.RemoveAt(i);
                    Destroyed++;
                    Score += PointsPerKill;
                }
            }
        }
        // 6. age every explosion (it resolved this step, so the first tick still counts)
        for (var i = _explosion.Count - 1; i >= 0; i--)
        {
            _explosion[i][2]--;
            if (_explosion[i][2] <= 0)
            {
                _explosion.RemoveAt(i);
            }
        }

        // 7. the wave is over when nothing is left to spawn and nothing is in the air
        if (WaveLeftToSpawn == 0 && _incoming.Count == 0 && _interceptor.Count == 0)
        {
            if (Wave >= WaveMax)
            {
                Score += PointsPerCity * CitiesAliveAfter();
                Recompute();
                Won = true;
                GameOver = true;
                LastEvent = $"saved steps={Steps} waves={Wave} destroyed={Destroyed} leaked={Leaked} "
                            + $"score={Score} cities={CitiesAlive}";
                return;
            }
            Score += PointsPerCity * CitiesAliveAfter();
            Wave++;
            WaveLeftToSpawn = CountOfWave(Wave);
            SpawnCountdown = 0;
            for (var i = 0; i < _batteryAmmo.Count; i++)
            {
                _batteryAmmo[i] = AmmoPerBattery;
            }
        }
        Recompute();
    }

    private int CitiesAliveAfter()
    {
        var alive = 0;
        foreach (var value in _cityAlive)
        {
            if (value)
            {
                alive++;
            }
        }
        return alive;
    }

    /// <summary>
    /// Runs <paramref name="steps"/> fixed simulation steps. The hook, and the only frame-rate
    /// independent way to advance the field: <see cref="LastHookSteps"/> is its own property.
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
                    + $"incoming={IncomingAlive} destroyed={Destroyed} leaked={Leaked} "
                    + $"cities={CitiesAlive} over={GameOver} won={Won}";
        Recompute();
        ApplyBoard();
        return LastEvent;
    }

    /// <summary>
    /// Fires one interceptor at <c>(x,y)</c> from the battery with ammo nearest in x (ties: the
    /// lowest battery index). Every reason it can be refused is named in the answer.
    /// </summary>
    public string Fire(int x, int y)
    {
        if (GameOver)
        {
            LastEvent = $"rejected reason=game_over at={x},{y} won={Won}";
            return LastEvent;
        }
        if (x < 0 || x > FieldW || y < 0 || y > FieldH)
        {
            LastEvent = $"rejected reason=out_of_bounds at={x},{y}";
            return LastEvent;
        }
        var pick = -1;
        var bestDistance = 0;
        for (var i = 0; i < BatteryXs.Length; i++)
        {
            if (_batteryAmmo[i] <= 0)
            {
                continue;
            }
            var distance = System.Math.Abs(BatteryXs[i] - x);
            if (pick < 0 || distance < bestDistance)
            {
                pick = i;
                bestDistance = distance;
            }
        }
        if (pick < 0)
        {
            LastEvent = $"rejected reason=no_ammo at={x},{y} ammo={Ammo}";
            return LastEvent;
        }
        var bx = BatteryXs[pick];
        var by = BatteryY;
        var span = System.Math.Max(System.Math.Abs(x - bx), System.Math.Abs(y - by));
        var dur = CeilDiv(span, InterceptorSpeed);
        if (dur < 1)
        {
            dur = 1;
        }
        _interceptor.Add(new[] { bx, by, x, y, 0, dur, bx, by });
        _batteryAmmo[pick]--;
        Fired++;
        Recompute();
        ApplyBoard();
        LastEvent = $"fired from={bx},{by} to={x},{y} dur={dur} battery={pick} ammo={_batteryAmmo[pick]} "
                    + $"total_ammo={Ammo} fired={Fired}";
        return LastEvent;
    }

    /// <summary>Records what stands at one point into the Probe* properties, so an assert can name it.</summary>
    public string ProbePoint(int x, int y)
    {
        ProbeX = x;
        ProbeY = y;
        if (x < 0 || x > FieldW || y < 0 || y > FieldH)
        {
            ProbeValue = -1;
            ProbeState = "outside";
        }
        else
        {
            ProbeValue = -1;
            ProbeState = "ground";
            for (var i = 0; i < CityXs.Length; i++)
            {
                if (System.Math.Abs(x - CityXs[i]) <= 30 && System.Math.Abs(y - CityY) <= 20)
                {
                    ProbeValue = i;
                    ProbeState = _cityAlive[i] ? "city" : "city_ruins";
                }
            }
            for (var i = 0; i < BatteryXs.Length; i++)
            {
                if (System.Math.Abs(x - BatteryXs[i]) <= 18 && System.Math.Abs(y - BatteryY) <= 10)
                {
                    ProbeValue = i;
                    ProbeState = "battery";
                }
            }
        }
        Recompute();
        LastEvent = $"probe at={x},{y} state={ProbeState} index={ProbeValue}";
        return LastEvent;
    }

    /// <summary>Steps per second; 0 keeps the field still (the default).</summary>
    public string SetAutoClock(float perSecond)
    {
        AutoClock = perSecond;
        _autoAccum = 0.0f;
        LastAutoSteps = 0;
        LastEvent = $"auto_clock={AutoClock}";
        GD.Print($"MISSILECOMMAND_AUTO auto={AutoClock}");
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
        var fire = Input.IsActionPressed("mc_auto_fire");
        // Press edges only: a key a scenario injected and never released performs exactly one shot
        // instead of repeating at the frame rate. The aim is deterministic: the oldest incoming
        // missile's current position, or the middle of the field when the sky is empty.
        if (fire && !_prevFire && !GameOver)
        {
            var x = FieldW / 2;
            var y = FieldH / 2;
            if (_incoming.Count > 0)
            {
                x = _incoming[0][0];
                y = _incoming[0][1];
            }
            Fire(x, y);
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
                // The clock deliberately does NOT touch LastHookSteps: that property belongs to the
                // StepFrames hook alone (two producers, two properties -- the G1 lesson).
                ApplyBoard();
            }
        }
        else
        {
            LastAutoSteps = 0;
        }
    }

    /// <summary>Every exported fact and every list, on one line.</summary>
    public string Dump()
    {
        return $"field={FieldW}x{FieldH} city_y={CityY} battery_y={BatteryY} city_list={CityList} "
               + $"city_hash={CityHash} cities={CitiesAlive} ammo_list={AmmoList} ammo={Ammo} "
               + $"incoming={IncomingList} interceptors={InterceptorList} blasts={ExplosionList} "
               + $"incoming_alive={IncomingAlive} interceptor_alive={InterceptorAlive} "
               + $"blasts_active={ExplosionsActive} spawned={Spawned} destroyed={Destroyed} "
               + $"leaked={Leaked} fired={Fired} cities_lost={CitiesLost} score={Score} wave={Wave} "
               + $"wave_max={WaveMax} wave_left={WaveLeftToSpawn} countdown={SpawnCountdown} "
               + $"world_hash={WorldHash} steps={Steps} won={Won} over={GameOver} auto={AutoClock} "
               + $"auto_ticks={AutoTicks} last_auto={LastAutoSteps} last_hook={LastHookSteps} "
               + $"input_shots={InputShots} elapsed={Elapsed:F3} ticks={Ticks} last={LastEvent}";
    }

    /// <summary>
    /// Writes the whole deterministic world in one call. Recognised keys (semicolon separated,
    /// <c>key=value</c>):
    ///
    /// <list type="bullet">
    /// <item><c>seed=N</c>, <c>wave=N</c> (1-based), <c>maxwave=N</c>, <c>score=N</c>;</item>
    /// <item><c>left=N</c>, <c>countdown=N</c> -- exactly how much of the current wave is unspawned;</item>
    /// <item><c>cities=1,0,1,1,0,1</c> -- pin which cities stand;</item>
    /// <item><c>ammo=a,b,c</c> -- pin the batteries;</item>
    /// <item><c>incoming=x0,y0,tx,ty,k,dur|...</c>, <c>interceptors=x0,y0,tx,ty,k,dur|...</c>,
    /// <c>blasts=x,y,ticks|...</c> -- pin the sky, which is what makes a single-step explosion
    /// assertion a statement about a state the session itself chose. The current position of a pinned
    /// missile is derived with the same floor interpolation the simulation uses.</item>
    /// </list>
    ///
    /// <para>The auto clock and input polling are switched OFF first, so a session's aim and the next
    /// readback are the same fact.</para>
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
                case "seed":
                    Seed = int.Parse(kv[1]);
                    _randState = Seed;
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
                case "cities":
                    _cityAlive.Clear();
                    foreach (var flag in kv[1].Split(','))
                    {
                        _cityAlive.Add(flag == "1");
                    }
                    break;
                case "ammo":
                    _batteryAmmo.Clear();
                    foreach (var left in kv[1].Split(','))
                    {
                        _batteryAmmo.Add(int.Parse(left));
                    }
                    break;
                case "incoming":
                    AddMissiles(_incoming, kv[1]);
                    break;
                case "interceptors":
                    AddMissiles(_interceptor, kv[1]);
                    break;
                case "blasts":
                    if (kv[1].Length > 0)
                    {
                        foreach (var item in kv[1].Split('|'))
                        {
                            var f = item.Split(',');
                            _explosion.Add(new[] { int.Parse(f[0]), int.Parse(f[1]), int.Parse(f[2]) });
                        }
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
        Recompute();
        ApplyBoard();
        LastEvent = $"forced wave={Wave}/{WaveMax} left={WaveLeftToSpawn} cities={CitiesAlive} "
                    + $"ammo={Ammo} incoming={IncomingAlive} interceptors={InterceptorAlive} "
                    + $"blasts={ExplosionsActive} score={Score} seed={Seed}";
        return LastEvent;
    }

    /// <summary>
    /// Pins a list of missiles from <c>x0,y0,tx,ty,k,dur</c> records. The current position is derived
    /// with the same <see cref="PosAt"/> the simulation uses, so a pinned missile is in exactly the
    /// state the rules would have put it in at that step.
    /// </summary>
    private static void AddMissiles(List<int[]> list, string spec)
    {
        if (spec.Length == 0)
        {
            return;
        }
        foreach (var item in spec.Split('|'))
        {
            var f = item.Split(',');
            var x0 = int.Parse(f[0]);
            var y0 = int.Parse(f[1]);
            var tx = int.Parse(f[2]);
            var ty = int.Parse(f[3]);
            var k = int.Parse(f[4]);
            var dur = int.Parse(f[5]);
            list.Add(new[] { PosAt(x0, tx, k, dur), PosAt(y0, ty, k, dur), tx, ty, k, dur, x0, y0 });
        }
    }
}
