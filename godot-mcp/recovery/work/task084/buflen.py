# -*- coding: utf-8 -*-
"""Compare the replayed-buffer length against the newest recorded revision."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rec  # noqa: E402


def main():
    print("%-52s %6s %6s %6s %6s" % ("file", "target", "buf", "tree", "bal"))
    for f in sys.argv[1:]:
        try:
            skel, meta = rec.newest_reads(f)
            buf, st = rec.replay(f, verbose=False)
            import io
            t = io.open(os.path.join(r"H:\rebuild\godot", f), encoding="utf-8", errors="replace").read().split("\n")
            if t and t[-1] == "":
                t = t[:-1]
            b = buf[:-1] if buf and buf[-1] == "" else buf
            d, p, _n = rec_balance(b)
            print("%-52s %6d %6d %6d  {%d,%d} applied=%d skipped=%d" % (
                os.path.basename(f), meta["rev"], len(b), len(t), d, p, st["applied"], len(st["skipped"])))
        except Exception as e:  # noqa: BLE001
            print("%-52s  EXC %s" % (os.path.basename(f), e))


def rec_balance(lines):
    d = p = 0
    for l in lines:
        s = l.split("//", 1)[0]
        for ch in s:
            if ch == "{":
                d += 1
            elif ch == "}":
                d -= 1
            elif ch == "(":
                p += 1
            elif ch == ")":
                p -= 1
    return d, p, None


if __name__ == "__main__":
    main()
