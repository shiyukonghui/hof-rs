# -*- coding: utf-8 -*-
"""TASK-083 recon 6: how far do the read-window revisions agree with the
TASK-044 backup (which is revision 640)?"""
import io
import json
import os

IDX = r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\__payload-index"
BAK = r"C:\Users\wyl\AppData\Local\Temp\mcp044-module-backup\mcp_server"
SUB = "modules\\mcp_server\\mcp_server.cpp"


def load_rows(sub):
    out = []
    with io.open(os.path.join(IDX, "events-read.jsonl"), "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if sub in r.get("path", "").replace("/", "\\").lower():
                out.append(r)
    return out


def main():
    rows = load_rows(SUB.lower())
    bak = io.open(os.path.join(BAK, "mcp_server.cpp"), "r", encoding="utf-8",
                  errors="replace", newline="").read().split("\n")
    bak = [x.rstrip("\r") for x in bak]
    print("backup lines=%d" % len(bak))
    for rev in (539, 640, 653, 726, 760):
        rs = [r for r in rows if r["totalLines"] == rev]
        agree = dis = 0
        samples = []
        for r in rs:
            for no, txt in (r.get("lines") or []):
                if no <= len(bak):
                    if bak[no - 1] == txt:
                        agree += 1
                    else:
                        dis += 1
                        if len(samples) < 8:
                            samples.append((r["seq"], no, txt, bak[no - 1]))
        print("rev%-4d windows=%-3d vs backup640: agree=%-4d differ=%-4d" % (rev, len(rs), agree, dis))
        for seq, no, a, b in samples:
            print("     seq=%-5s line=%-4d read=%r" % (seq, no, a[:80]))
            print("                        bak =%r" % (b[:80],))


if __name__ == "__main__":
    main()
