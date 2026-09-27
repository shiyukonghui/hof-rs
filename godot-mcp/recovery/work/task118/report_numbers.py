#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-118: print the ledger's channel delta as text (no shell redirection)."""
import io
import json
import os

ROOT = r"F:\moonbit-hof-rs\godot-mcp"


def main():
    with io.open(os.path.join(ROOT, "coverage.json"), "r", encoding="utf-8") as fh:
        d = json.load(fh)
    print("corpus:", d["corpus"])
    print("buckets:", d["buckets"], "status:", d["status_counts"])
    print("channel_counts(measured):", d["evidence_channel_counts"],
          "declared:", d["channel_delta"]["channel_counts_declared"])
    rb = d["readback_declarations"]
    print("readback declared=%d verified=%d content_checked=%d rejected=%d"
          % (rb["declared"], rb["verified"], rb["content_checked"], len(rb["rejected"])))
    for r in rb["rejected"]:
        print("  REJECTED %s <- %s @ %s: %s" % (r["tool"], r["witness_tool"], r["run"],
                                                (r.get("reason") or "")[:140]))
    dl = d["channel_delta"]
    print("promoted=%d demoted=%d" % (len(dl["promoted_from_legacy_rule"]),
                                      len(dl["demoted_from_legacy_rule"])))
    for x in dl["demoted_from_legacy_rule"]:
        print("  DEMOTED", x)
    print("channel_status:", json.dumps(dl["channel_status"], ensure_ascii=False))
    print("channel_evidence:", json.dumps(dl["channel_evidence"], ensure_ascii=False))
    print()
    names = ["editor_connect_signal", "running_game_find_node_when_available", "editor_add_gridmap",
             "editor_set_node_script_batch", "editor_set_auto_dismiss_dialogs",
             "os_list_android_devices", "project_get_android_preset_info",
             "os_deploy_to_android_device", "editor_simulate_key"]
    index = {r["tool"]: r for r in d["tools"]}
    for name in names:
        r = index[name]
        print("%-42s calls=%-3d bnd=%-2d ch=%-13s ev=%-3d status=%-9s legacy=%-9s tier=%s"
              % (name, r["calls"], r["boundary"], r["evidence_channel"], r["channel_evidence"],
                 r["status"], r["status_legacy"], r["evidence_tier"]))
    print()
    print("still_short (%d):" % len(dl["still_short"]))
    for item in dl["still_short"]:
        print("  %-42s ch=%-13s calls=%-3d bnd=%-2d ev=%-3d  %s"
              % (item["tool"], item["channel"], item["calls"], item["boundary"],
                 item["channel_evidence"], item["reason"]))
    print()
    print("promoted:")
    for item in dl["promoted_from_legacy_rule"]:
        print("  %-42s ch=%-13s calls=%-3d bnd=%-2d ev=%d" % (item["tool"], item["channel"],
                                                              item["calls"], item["boundary"],
                                                              item["channel_evidence"]))


if __name__ == "__main__":
    main()
