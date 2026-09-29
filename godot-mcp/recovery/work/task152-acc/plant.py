# Independent acceptance (TASK-152) non-vacuity plant + byte-exact restore.
#
# mode=baseline : inject one renamed tool NAME into the engine-internal baseline
#                 (pure byte replacement, nothing re-serialised) -> expect g05 red
#                 on B2 and B2 must name the injected name.
# mode=map      : inject one wrong new_name into the rename map (old-style name,
#                 channel prefix dropped) -> expect g05 red on exactly one check.
#
# action=plant / restore / verify.  Nothing here touches the hof-rs side.
import hashlib, json, subprocess, sys, os

ENGINE = r"F:\moonbit-hof-rs\godot-mcp\godot"
OSDIR = os.path.join(ENGINE, "modules", "mcp_server", "docs")
BASELINE = os.path.join(OSDIR, "rename-baseline-tools-list.json")
MAP = os.path.join(OSDIR, "tool-rename-map.json")
CONTRACT = os.path.join(OSDIR, "tools_list.renamed.json")
SCRIPT = os.path.join(OSDIR, "scripts", "check_rename_map.py")
FOUR = [MAP, BASELINE, SCRIPT, CONTRACT]

PLANTS = {
    "baseline": (BASELINE, b'"name":"get_filesystem_tree"', b'"name":"legacy_get_filesystem_tree"'),
    "map": (MAP, b'"new_name": "project_get_statistics"', b'"new_name": "get_statistics"'),
}


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def blob(path):
    rel = os.path.relpath(path, ENGINE).replace("\\", "/")
    out = subprocess.run(["git", "hash-object", rel], cwd=ENGINE, capture_output=True, text=True)
    return out.stdout.strip(), rel


def head_blob(path):
    rel = os.path.relpath(path, ENGINE).replace("\\", "/")
    out = subprocess.run(["git", "rev-parse", "HEAD:" + rel], cwd=ENGINE, capture_output=True, text=True)
    return out.stdout.strip()


def git(*a):
    return subprocess.run(["git"] + list(a), cwd=ENGINE, capture_output=True, text=True).stdout


mode, action = sys.argv[1], sys.argv[2]
path, old, new = PLANTS[mode]

if action == "plant":
    data = open(path, "rb").read()
    n = data.count(old)
    print("MODE %s" % mode)
    print("TARGET %s" % path)
    print("VICTIM occurrences %d" % n)
    if n != 1 or new in data:
        print("PLANT_ABORT (occurrence/duplicate guard)")
        sys.exit(2)
    planted = data.replace(old, new)
    open(path, "wb").write(planted)
    print("bytes %d -> %d" % (len(data), len(planted)))
    print("planted sha256 %s" % sha(path))
    # prove only the victim differs
    same_elsewhere = len(data) + (len(new) - len(old)) == len(planted)
    print("only-the-victim-differs %s" % same_elsewhere)
    base = os.path.join(OSDIR, "rename-baseline-tools-list.json")
    print("baseline sha256 now %s" % sha(base))
elif action == "restore":
    out = subprocess.run(["git", "checkout", "--"] + [os.path.relpath(p, ENGINE).replace("\\", "/") for p in FOUR],
                         cwd=ENGINE, capture_output=True, text=True)
    print("git checkout rc=%d %s" % (out.returncode, out.stderr.strip()))
elif action == "verify":
    status = git("status", "--porcelain")
    diffstat = git("diff", "--stat")
    print("=== git status --porcelain ===\n%s<end>" % status)
    print("=== git diff --stat ===\n%s<end>" % diffstat)
    print("=== git hash-object vs HEAD blob ===")
    ok = True
    for p in FOUR:
        wb, rel = blob(p)
        hb = head_blob(p)
        eq = (wb == hb)
        ok = ok and eq
        print("%s %s\n   work=%s\n   head=%s" % ("EQUAL" if eq else "DIFFER", rel, wb, hb))
    print("ALL_FOUR_BYTE_EQUAL=%s" % ok)
    sys.exit(0 if ok else 1)
