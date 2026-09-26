# TASK-097 (C): pull the Space Invaders run's own decisive facts out of its
# response files, one line each.
#   python check_si.py <run-dir>
import json
import os
import sys

RUN = sys.argv[1]


def load(tag):
    path = os.path.join(RUN, tag + ".json")
    if not os.path.isfile(path):
        return None
    doc = json.loads(open(path, encoding="utf-8-sig").read())
    if "error" in doc:
        return {"__error__": doc["error"]}
    return json.loads(doc["result"]["content"][0]["text"])


def gdscript(tag):
    got = load(tag)
    return got.get("result") if got else None


print("== %s" % RUN)
a = load("e05-read-1")
b = load("e09-read-2")
print("A. scene file sha A=%s (%d B) / B=%s (%d B) -> equal=%s" % (
    a["sha256"], a["size"], b["sha256"], b["size"], a["sha256"] == b["sha256"]))
create = load("e03-batch-add-static")
print("B. first batch: count=%d names=%s" % (
    create["count"], ",".join(e["name"] for e in create["created"])))
refused = load("e06-batch-add-static-again")
if refused and "__error__" in refused:
    err = refused["__error__"]
    print("C. second batch (REAL-DEVELOPMENT PROOF): code=%d message=%s" % (err["code"], err["message"]))
    print("   conflicts=%s" % json.dumps(err["data"]["conflicts"], ensure_ascii=False))
else:
    print("C. second batch: NOT REFUSED -> %s" % json.dumps(refused, ensure_ascii=False)[:200])
tree = load("e07-tree-after-refusal")


def names_of(node, out):
    out.append(node.get("name"))
    for child in node.get("children", []) or []:
        names_of(child, out)


names = []
names_of(tree["tree"], names)
print("D. editor tree after refusal: %s" % ",".join(names))
print("   auto-named (@Type@N) nodes: %s" % [n for n in names if n and n.startswith("@")])
build = load("e13-build-csharp")
print("E. build: %s" % json.dumps({k: build[k] for k in build if k in (
    "succeeded", "exit_code", "error_count", "errors", "duration_ms", "skipped")}, ensure_ascii=False)[:300])
validate = load("e14-validate-scripts")
print("F. validate: invalid_count=%s count=%s" % (validate.get("invalid_count"), validate.get("count")))
for tag in ("g02-readback-t0", "g25-readback-won", "g32-readback-lost", "g45-final-readback"):
    print("G. %s -> %s" % (tag, gdscript(tag)))
for tag in ("g07-samples-frozen", "g09-samples-moving", "g14-samples-flight",
            "g38-samples-overlay", "g44-final-samples"):
    got = load(tag)
    samples = got["samples"]
    keys = sorted(samples[0].keys() - {"frame"})
    print("H. %s: %d frames, keys=%s" % (tag, len(samples), ",".join(keys)))
    for key in keys:
        values = [s[key] for s in samples]
        distinct = []
        for value in values:
            if value not in distinct:
                distinct.append(value)
        print("     %-18s first=%s last=%s distinct=%d %s" % (
            key, values[0], values[-1], len(distinct),
            json.dumps(distinct, ensure_ascii=False)[:160]))
final = load("g46-final-tree")
allnames = []
names_of(final["tree"], allnames)
invaders = [n for n in allnames if n and n.startswith("Invader_")]
print("I. runtime tree: total=%d Invader_*=%d overlay=%s" % (
    len(allnames), len(invaders), "ProbeOverlay" in allnames))
