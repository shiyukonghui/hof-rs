import io
import json
import sys

trace = sys.argv[1]
want = set(int(x) for x in sys.argv[2].split(",")) if len(sys.argv) > 2 else None
for line in io.open(trace, encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    row = json.loads(line)
    if row.get("event") == "trace_opened":
        print("TRACE_OPENED", json.dumps(row, ensure_ascii=False))
        continue
    if want is not None and row.get("seq") not in want:
        continue
    if row.get("event") == "capture":
        print("  capture seq=%s tool=%s changed=%s changed_pixels=%s ratio=%s status=%s" % (
            row.get("seq"), row.get("tool"), row.get("changed"), row.get("changed_pixels"),
            row.get("changed_pixel_ratio"), row.get("status")))
        continue
    print("seq=%s id=%s tool=%s ok=%s err=%s dur=%s result_bytes=%s file_effect_status=%s" % (
        row.get("seq"), row.get("id"), row.get("tool"), row.get("ok"), row.get("error_code"),
        row.get("duration_ms"), row.get("result_bytes"), row.get("file_effect_status")))
    print("    args=%s" % row.get("args"))
    if row.get("file_effects"):
        for effect in row["file_effects"]:
            print("    file_effect path=%s abs=%s kind=%s changed=%s failed=%s" % (
                effect.get("path"), effect.get("abs_path"), effect.get("kind"),
                effect.get("changed"), effect.get("failed")))
            print("        before=%s after=%s" % (json.dumps(effect.get("before")), json.dumps(effect.get("after"))))
            if effect.get("diff"):
                print("        diff=%s" % json.dumps(effect["diff"], ensure_ascii=False))
