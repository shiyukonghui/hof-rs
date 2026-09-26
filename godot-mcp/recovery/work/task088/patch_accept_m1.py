# -*- coding: utf-8 -*-
"""task088 (2): rewrite the four stale expectations of accept_m1.ps1 and graft
back the two recorded cases the TASK-087 reconstruction could not add.

Every replacement asserts its anchor first, so a drifted file fails loudly
instead of being silently rewritten.

  A. `Compare-ToolListToFixture` - the M1-era `$ActualTools.Count -eq 2`
     literal is replaced by the per-endpoint expectation DERIVED from
     `docs/tool-rename-map.json` + `docs/tool-groups-added.json` + the six
     implemented-group manifests, cross-checked against the contract's own
     entry count.  The comparison is widened from "these two tools verbatim" to
     "exactly this endpoint's tools, verbatim, with no extra and none missing".
  B. `case1_GET_mcp_200` - `$firstJson.tools -eq 2` -> the derived editor count.
  C. `case12_game_process_endpoint` - passes the derived *game* set, which the
     editor-only form of the old function could not express.
  D. `guard_user_port_9877` - `$userPortAlive -and $userPortSame` required a
     listener to exist on 9877.  The listener was retired; the invariant that
     survives is "this script never touches 9877": the pid is unchanged, a
     listener that existed before still exists with the same pid, and no pid
     this script started is listening there.
  E. `case0_repo_exit_code_propagation` and
     `case20_tools_list_cross_process_restart` - replayed from the recorded
     edit stream.  NB the TASK-087 manifest named `seq=1030` for case0 without
     the path; BOTH the `editor_shader_write.h` edit and the `accept_m1.ps1`
     edit carry `seq=1030`, and the manifest picked the wrong one.  This script
     selects on (path, seq, time).

usage: python patch_accept_m1.py [--apply]
"""
from __future__ import print_function
import io, json, os, sys

TREE = r"H:\rebuild\godot\modules\mcp_server\scripts\accept_m1.ps1"
IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"

NEW_COMPARE = '''# -----------------------------------------------------------------------------
#  TASK-088: the per-endpoint expectation is DERIVED, never literal.
#
#  The M1-era form of this gate asserted `tools == 2` (the two tools of
#  DESIGN-DETAIL.md section 9).  That number described the M1 build, not the
#  server, and four call sites still carried it long after the registry had
#  grown to the full contract.  What the gate has to state is the invariant the
#  contract already carries: an editor process serves exactly the implemented
#  tools whose scope is not `game`, a game process exactly those whose scope is
#  not `editor`.
#
#  The scope authority is `docs/tool-rename-map.json` (the `scope` of a ported
#  tool) plus `docs/tool-groups-added.json` (the scope an added tool's group
#  declares) - the same two sources `check_contract_subset.ps1` reads - and the
#  implemented set is the union of the six group manifests' `implemented`
#  groups.  Two cross-checks keep a missing manifest from silently shrinking
#  the expectation: the union must equal the contract's entry count, and every
#  expected name must exist in the contract.
# -----------------------------------------------------------------------------
function Get-EndpointExpectation {
    $renameMap = Join-Path $RepoRoot 'modules\\mcp_server\\docs\\tool-rename-map.json'
    $addedManifest = Join-Path $RepoRoot 'modules\\mcp_server\\docs\\tool-groups-added.json'
    if (-not (Test-Path $RenamedContract)) { Write-Host ("FATAL: renamed contract not found: {0}" -f $RenamedContract); exit 2 }
    if (-not (Test-Path $renameMap)) { Write-Host ("FATAL: rename map not found: {0}" -f $renameMap); exit 2 }
    if (-not (Test-Path $addedManifest)) { Write-Host ("FATAL: added-tool manifest not found: {0}" -f $addedManifest); exit 2 }
    $contractJson = ConvertFrom-Json (Get-Content -Raw -Encoding UTF8 $RenamedContract)
    $contractNames = @($contractJson.result.tools | ForEach-Object { $_.name })
    $scopeOf = @{}
    foreach ($entry in @((ConvertFrom-Json (Get-Content -Raw -Encoding UTF8 $renameMap)).tools)) {
        $scopeOf[[string]$entry.new_name] = [string]$entry.scope
    }
    foreach ($g in @((ConvertFrom-Json (Get-Content -Raw -Encoding UTF8 $addedManifest)).groups)) {
        foreach ($t in @($g.tools)) { $scopeOf[[string]$t] = [string]$g.scope }
    }
    $implemented = New-Object System.Collections.Generic.List[string]
    $seen = @{}
    $manifestNames = @('tool-groups.json', 'tool-groups-b2.json', 'tool-groups-b3.json',
                       'tool-groups-b4.json', 'tool-groups-b5.json', 'tool-groups-added.json')
    $present = @()
    foreach ($name in $manifestNames) {
        $p = Join-Path $RepoRoot ('modules\\mcp_server\\docs\\' + $name)
        if (-not (Test-Path $p)) { continue }
        $present += $name
        foreach ($g in @((ConvertFrom-Json (Get-Content -Raw -Encoding UTF8 $p)).groups)) {
            if ($g.implemented -ne $true) { continue }
            foreach ($t in @($g.tools)) {
                if (-not $seen.ContainsKey([string]$t)) { $seen[[string]$t] = $true; $implemented.Add([string]$t) }
            }
        }
    }
    if ($implemented.Count -ne $contractNames.Count) {
        Write-Host ("FATAL: the implemented union is {0} tool(s) but the contract carries {1}; the per-endpoint expectation cannot be derived" -f $implemented.Count, $contractNames.Count)
        Write-Host ("       manifests read: {0}" -f ($present -join ', '))
        exit 2
    }
    $editor = @($implemented | Where-Object { $scopeOf[$_] -ne 'game' })
    $game = @($implemented | Where-Object { $scopeOf[$_] -ne 'editor' })
    $unscoped = @($implemented | Where-Object { -not $scopeOf.ContainsKey($_) })
    if ($unscoped.Count -gt 0) {
        Write-Host ("FATAL: {0} implemented tool(s) carry no scope in the rename map or the added manifest: {1}" -f $unscoped.Count, ($unscoped -join ', '))
        exit 2
    }
    foreach ($n in @($editor + $game)) {
        if ($contractNames -notcontains $n) {
            Write-Host ("FATAL: {0} is implemented but is not a contract entry" -f $n)
            exit 2
        }
    }
    Write-Host ("expectation : derived from {0} manifest(s) + rename map: implemented union={1}, editor={2}, game={3} (contract={4})" -f `
        $present.Count, $implemented.Count, $editor.Count, $game.Count, $contractNames.Count)
    return @{ Editor = $editor; Game = $game; All = $contractNames }
}

$script:EndpointTools = Get-EndpointExpectation
$ExpectedEditorTools = @($script:EndpointTools.Editor)
$ExpectedGameTools = @($script:EndpointTools.Game)

# Compares a `tools/list` payload against the authoritative snapshot, restricted
# to the tools the contract says THIS endpoint must serve. Every field is
# compared verbatim (case sensitive): name, description and inputSchema. There is
# deliberately no tolerance for a Latin-1 recovery of a description - that
# fallback used to make this gate unable to reject a server that emits mojibake
# (GDR-13). The name set is compared in both directions, so a leaked
# out-of-scope tool and a missing in-scope tool are both red.
function Compare-ToolListToFixture {
    param($ActualTools, [string[]]$ExpectedNames, [string]$Label)
    if (-not (Test-Path $RenamedContract)) {
        Write-Host ("FATAL: renamed contract not found: {0}" -f $RenamedContract)
        Write-Host '        regenerate it with modules\\mcp_server\\scripts\\gen_renamed_contract.py'
        exit 2
    }
    $fixtureJson = ConvertFrom-Json (Get-Content -Raw -Encoding UTF8 $RenamedContract)
    $fixtureTools = @($fixtureJson.result.tools | Where-Object { $ExpectedNames -ccontains $_.name })
    # TASK-088: an `inputSchema` override is a DELIBERATE, declared deviation:
    # the generator's own docstring says a schema override replaces the whole
    # object and must carry a reason. Three tools in this contract are in that
    # class (the published schema is looser than the contract's). The exception
    # is therefore read out of the contract's `_meta.overrides` - not out of a
    # hand-written list - and the number honoured is printed, so the exclusion
    # cannot grow silently.
    $declaredSchema = @{}
    foreach ($rec in @($fixtureJson._meta.overrides)) {
        if ([string]$rec.kind -ceq 'inputSchema') { $declaredSchema[[string]$rec.old_name] = $true }
    }
    $schemaDeviations = @{}
    $renameMapPath = Join-Path $RepoRoot 'modules/mcp_server/docs/tool-rename-map.json'
    if (Test-Path $renameMapPath) {
        foreach ($e in @((ConvertFrom-Json (Get-Content -Raw -Encoding UTF8 $renameMapPath)).tools)) {
            if ($declaredSchema.ContainsKey([string]$e.old_name)) { $schemaDeviations[[string]$e.new_name] = $true }
        }
    }
    $actualNames = @($ActualTools | ForEach-Object { $_.name })
    $notes = @()
    $ok = $true
    if ($fixtureTools.Count -ne $ExpectedNames.Count) {
        $ok = $false
        $notes += ("the contract carries {0} of the {1} tool(s) expected on the {2} endpoint" -f $fixtureTools.Count, $ExpectedNames.Count, $Label)
    }
    if ($ActualTools.Count -ne $ExpectedNames.Count) {
        $ok = $false
        $notes += ("{0} endpoint served {1} tool(s); the manifests + contract expect {2}" -f $Label, $ActualTools.Count, $ExpectedNames.Count)
    }
    $extra = @($actualNames | Where-Object { $ExpectedNames -notcontains $_ })
    if ($extra.Count -gt 0) { $ok = $false; $notes += ("served but not expected on the {0} endpoint: {1}" -f $Label, ($extra -join ', ')) }
    $missing = @($ExpectedNames | Where-Object { $actualNames -notcontains $_ })
    if ($missing.Count -gt 0) { $ok = $false; $notes += ("expected on the {0} endpoint but not served: {1}" -f $Label, ($missing -join ', ')) }
    $verbatim = 0
    $deviations = 0
    $deviationNames = @()
    foreach ($name in $ExpectedNames) {
        $actual = @($ActualTools | Where-Object { $_.name -ceq $name })
        $expected = @($fixtureTools | Where-Object { $_.name -ceq $name })
        if ($actual.Count -ne 1 -or $expected.Count -ne 1) {
            $ok = $false
            $notes += ("{0}: count actual={1} fixture={2}" -f $name, $actual.Count, $expected.Count)
            continue
        }
        $descriptionEqual = ([string]$actual[0].description -ceq [string]$expected[0].description)
        if (-not $descriptionEqual) { $ok = $false; $notes += ("{0}: description differs" -f $name) }
        $schemaEqual = (Get-CanonicalJson $actual[0].inputSchema) -ceq (Get-CanonicalJson $expected[0].inputSchema)
        if (-not $schemaEqual) {
            if ($schemaDeviations.ContainsKey([string]$name)) {
                # A declared deviation that really differs from the published
                # schema is the only thing the override exists for.
                $deviations++
                $deviationNames += [string]$name
            } else {
                $ok = $false
                $notes += ("{0}: inputSchema differs and no inputSchema override declares it" -f $name)
            }
        }
        if (($schemaEqual -or $schemaDeviations.ContainsKey([string]$name)) -and $descriptionEqual) { $verbatim++ }
    }
    $notes += ("{0} verbatim {1}/{2} (declared schema deviations that really differ: {3} [{4}])" -f `
        $Label, $verbatim, $ExpectedNames.Count, $deviations, ($deviationNames -join ', '))
    return @{ ok = $ok; notes = ($notes -join ' | ') }
}
'''

CASE1_OLD = "              ($firstJson.tools -eq 2) -and ($null -ne $secondJson) -and"
CASE1_NEW = "              ($firstJson.tools -eq $ExpectedEditorTools.Count) -and ($null -ne $secondJson) -and"

CASE3_OLD = "        $comparison = Compare-ToolListToFixture -ActualTools $actualTools"
CASE3_NEW = "        $comparison = Compare-ToolListToFixture -ActualTools $actualTools -ExpectedNames $ExpectedEditorTools -Label 'editor'"

CASE12_OLD = "        $comparison = Compare-ToolListToFixture -ActualTools @($gameListJson.result.tools)"
CASE12_NEW = "        $comparison = Compare-ToolListToFixture -ActualTools @($gameListJson.result.tools) -ExpectedNames $ExpectedGameTools -Label 'game'"

GUARD_OLD = """    # Only the PIDs started by this script are gone; 9877 must be untouched.
    $userPortPidAfter = Get-ListenerPid -Port $UserPort
    $userPortAlive = Test-Listener -Port $UserPort
    $userPortSame = ($userPortPidBefore -eq $userPortPidAfter)
    Record-Result 'guard_user_port_9877' ($userPortAlive -and $userPortSame) ("listening={0} pid_before={1} pid_after={2}" -f $userPortAlive, $userPortPidBefore, $userPortPidAfter)"""

GUARD_NEW = """    # Only the PIDs started by this script are gone; 9877 must be untouched.
    #
    # TASK-088: the invariant this guard states is "this script never touched
    # 9877", not "a listener exists on 9877". The user's editor listener was
    # retired during the project (it reads -1 for "no listener" on every run),
    # so the old form `$userPortAlive -and $userPortSame` was red for a fact
    # about the environment rather than a defect in the run. The three claims
    # below are what the guard was always for, and the middle one is strictly
    # stronger than the old form whenever a listener does exist:
    #   * same pid before and after (also true when neither exists: -1 == -1);
    #   * a listener that existed before is still there, with the same pid;
    #   * no pid this script started is listening on 9877.
    $userPortPidAfter = Get-ListenerPid -Port $UserPort
    $userPortAliveAfter = Test-Listener -Port $UserPort
    $userPortSame = ($userPortPidBefore -eq $userPortPidAfter)
    $userPortSurvived = $true
    if ($userPortPidBefore -gt 0) {
        $userPortSurvived = ($userPortAliveAfter -and ($userPortPidAfter -eq $userPortPidBefore))
    }
    $userPortTouched = ($userPortPidAfter -gt 0) -and ($script:StartedPids -contains $userPortPidAfter)
    Record-Result 'guard_user_port_9877' ($userPortSame -and $userPortSurvived -and (-not $userPortTouched)) ("listening_before={0} listening_after={1} pid_before={2} pid_after={3} same_pid={4} survived={5} touched_by_this_run={6}" -f $(if ($userPortPidBefore -gt 0) { 'true' } else { 'false' }), $userPortAliveAfter, $userPortPidBefore, $userPortPidAfter, $userPortSame, $userPortSurvived, $userPortTouched)"""


def edit_row(seq, psub, time_):
    hits = []
    with io.open(os.path.join(IDX, "events-edit.jsonl"), encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            ln = ln.strip()
            if not ln:
                continue
            try:
                o = json.loads(ln)
            except Exception:
                continue
            if str(o.get("seq")) != str(seq):
                continue
            p = (o.get("path") or "").replace("/", "\\")
            if psub.lower() not in p.lower():
                continue
            if str(o.get("time")) != str(time_):
                continue
            hits.append(o)
    if len(hits) != 1:
        raise SystemExit("REFUSED: seq=%s path~%s time=%s matched %d rows" % (seq, psub, time_, len(hits)))
    return hits[0]


def main():
    apply = "--apply" in sys.argv
    # `--base <file>` reads the pristine revision from somewhere else (e.g. the
    # output of `git show HEAD:<path>`), so the patch can be re-applied from
    # scratch instead of being layered on its own earlier result.
    base_path = None
    if "--base" in sys.argv:
        base_path = sys.argv[sys.argv.index("--base") + 1]
    if "--base-from-git" in sys.argv:
        # Binary-safe: `git show` through a PowerShell pipe rewrites LF to CRLF
        # and adds a BOM, which would silently re-line-end the whole file.
        import subprocess
        rev = sys.argv[sys.argv.index("--base-from-git") + 1]
        raw = subprocess.check_output(
            ["git", "-C", r"H:\rebuild\godot", "show", "%s:modules/mcp_server/scripts/accept_m1.ps1" % rev])
        base_path = os.path.join(r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task088",
                                 "accept_m1_pristine.ps1")
        io.open(base_path, "wb").write(raw)
        print("pristine base written from %s: %d bytes" % (rev, len(raw)))
    src_path = base_path if base_path else TREE
    buf = io.open(src_path, encoding="utf-8").read()
    orig = buf
    log = []

    def sub(old, new, why):
        nonlocal_ = buf
        n = nonlocal_.count(old)
        if n != 1:
            raise SystemExit("REFUSED: anchor for '%s' occurs %d time(s), expected 1" % (why, n))
        log.append("  %-28s replaced (%d -> %d bytes)" % (why, len(old.encode("utf-8")), len(new.encode("utf-8"))))
        return nonlocal_.replace(old, new, 1)

    # --- A: the comparison function -----------------------------------------
    start = buf.find("# Compares a `tools/list` payload against the authoritative snapshot. Every")
    end_marker = "function Test-Listener {"
    end = buf.find(end_marker)
    if start < 0 or end < 0 or end < start:
        raise SystemExit("REFUSED: cannot locate the Compare-ToolListToFixture span")
    old_span = buf[start:end]
    if "function Compare-ToolListToFixture {" not in old_span:
        raise SystemExit("REFUSED: the located span does not hold the function")
    log.append("  %-28s replaced (%d -> %d bytes)" % ("Compare-ToolListToFixture", len(old_span.encode("utf-8")), len(NEW_COMPARE.encode("utf-8"))))
    buf = buf[:start] + NEW_COMPARE + "\n" + buf[end:]

    buf = sub(CASE1_OLD, CASE1_NEW, "case1 tools count")
    buf = sub(CASE3_OLD, CASE3_NEW, "case3 expectation")
    buf = sub(CASE12_OLD, CASE12_NEW, "case12 expectation")
    buf = sub(GUARD_OLD, GUARD_NEW, "guard_user_port_9877")

    # --- E: graft the two recorded cases ------------------------------------
    # Replay the recorded (old, new) pair VERBATIM. TASK-087 grafted case20 by
    # anchoring on the three banner lines alone, which put the new case *after*
    # the `Stop-Engine` that closes the editor half - so case20 ran with a dead
    # editor and died on `Invoke-Mcp`'s unguarded ConnectAsync. The recorded
    # `old` is the six lines that start with `Stop-Engine`, and the recorded
    # `new` re-emits them after the case, so replacing old with new is both
    # faithful and correctly placed.
    e20 = edit_row(858, "accept_m1.ps1", 1790015088330)
    buf = sub(e20["old"], e20["new"], "case20 (recorded seq=858)")

    e0 = edit_row(1030, "accept_m1.ps1", 1790321324515)
    buf = sub(e0["old"], e0["new"], "case0 (recorded seq=1030)")

    # The restored case20 carries the M1 table size on its own count assertion.
    buf = sub("($toolCount -eq $ToolNames.Count)",
              "($toolCount -eq $ExpectedEditorTools.Count)",
              "case20 tools count")

    log.append("  total %d -> %d bytes" % (len(orig.encode("utf-8")), len(buf.encode("utf-8"))))
    print("\n".join(log))
    if not apply:
        print("DRY RUN (pass --apply to write %s)" % TREE)
        return 0
    io.open(TREE, "w", encoding="utf-8", newline="\n").write(buf)
    print("wrote %s" % TREE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
