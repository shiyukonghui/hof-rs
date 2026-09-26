# -*- coding: utf-8 -*-
"""Dry-run the reconstruction for a list of files, with verbose assembly."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rec  # noqa: E402


def main():
    for f in sys.argv[1:]:
        print("##### %s" % f)
        try:
            r, info = rec.assemble(f, verbose=True)
            print("   -> assembled %d lines (target %d)" % (len(r), info["rev"]))
        except Exception as e:  # noqa: BLE001
            print("   EXC %s" % e)


if __name__ == "__main__":
    main()
