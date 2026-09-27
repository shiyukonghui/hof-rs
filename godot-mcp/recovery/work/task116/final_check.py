import io, json, os, glob

R = r"F:\moonbit-hof-rs\godot-mcp"
print("== deliverables")
for p in ["tools/playtest_agent.py", "tools/playability_gate.py", "tools/playability_report.py",
          "tools/playability_controls.json", "runs/playability/playability.json",
          "runs/playability/playability.before.json", "runs/playability/summary.txt",
          "runs/playability/agent-probe.json",
          "recovery/reports/PLAYABILITY-REPORT.md", "recovery/reports/PLAYABILITY-DEFECTS.md"]:
    full = os.path.join(R, p)
    print("  %-52s %s %s" % (p, "OK " if os.path.isfile(full) else "MISSING",
                             os.path.getsize(full) if os.path.isfile(full) else ""))

games = sorted(d for d in os.listdir(os.path.join(R, "runs", "playability"))
               if os.path.isdir(os.path.join(R, "runs", "playability", d)))
print("\n== per game (frames / filmstrip / window)")
ok = True
for g in games:
    fd = os.path.join(R, "runs", "playability", g, "frames")
    n = len(glob.glob(os.path.join(fd, "*.png"))) if os.path.isdir(fd) else 0
    fs = os.path.join(R, "runs", "playability", g, "filmstrip.png")
    gj = os.path.join(R, "runs", "playability", g, "gate.json")
    wc = json.load(io.open(gj, encoding="utf-8")).get("window_conformance", {}) if os.path.isfile(gj) else {}
    print("  %-16s frames=%-3d filmstrip=%-5s window=%s declared=%s match=%s" % (
        g, n, os.path.isfile(fs), wc.get("os_window"), wc.get("declared_viewport"),
        wc.get("matches_declared")))
    if n == 0 or not os.path.isfile(fs) or wc.get("matches_declared") is not True:
        ok = False

doc = json.load(io.open(os.path.join(R, "runs/playability/playability.json"), encoding="utf-8"))
print("\n== totals", json.dumps(doc["totals"], ensure_ascii=False))
bef = json.load(io.open(os.path.join(R, "runs/playability/playability.before.json"), encoding="utf-8"))
print("== before  ", json.dumps(bef["totals"], ensure_ascii=False))
print("\nall per-game artefacts present, all windows match:", ok)
