# -*- coding: utf-8 -*-
"""TASK-139: show exact bytes of a line range, so an edit can quote them verbatim."""
from __future__ import print_function

import io
import sys


def main(argv):
    path = argv[0]
    a = int(argv[1])
    b = int(argv[2])
    lines = io.open(path, encoding="utf-8").read().splitlines()
    for i in range(a - 1, min(b, len(lines))):
        print("%4d %s" % (i + 1, repr(lines[i])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
