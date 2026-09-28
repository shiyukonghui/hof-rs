#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, json, sys
d = json.load(io.open('recovery/work/accept-147/recount.json', encoding='utf-8'))
rows = d['ids']['TC-PY']
keys = sys.argv[1:]
for ln, i in rows:
    if any(k in i for k in keys):
        print(ln, i)
