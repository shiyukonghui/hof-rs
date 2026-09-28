#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, json, re
p = r"F:\moonbit-hof-rs\godot-mcp\recovery\reports\ACCEPTANCE-TASK-145.md"
t = io.open(p, encoding="utf-8").read()
blocks = re.findall(r"```json\n(.*?)\n```", t, re.S)
print("json blocks:", len(blocks))
d = json.loads(blocks[-1])
print("verdict:", d["verdict"], "criteria:", len(d["criteria"]), "defects:", len(d["defects"]),
      "risks:", len(d["risks"]), "unverifiable:", len(d["unverifiable"]))
print("blockers:", [x for x in d["defects"] if x["severity"] == "blocker"])
print("ends with fence:", t.rstrip().endswith("```"))
print("bytes:", len(t.encode("utf-8")))
