#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-103 scratch: print the TD path walk."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_session_towerdefense as td

print("path length: %d" % len(td.PATH))
for index, cell in enumerate(td.PATH):
    print("%3d %s" % (index, cell))
print("map hash %d path hash %d" % (td.map_hash(), td.path_hash(td.PATH)))
