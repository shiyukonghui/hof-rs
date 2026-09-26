# -*- coding: utf-8 -*-
"""Compare the override tables of two gen_renamed_contract.py candidates."""
from __future__ import print_function
import io, hashlib, re, sys
sys.path.insert(0, r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\work\task087")
import rep

PATHS = [
    r"H:\rebuild\godot\modules\mcp_server\scripts\gen_renamed_contract.py",
    r"C:\Users\wyl\AppData\Local\Temp\mcp-recovery\staging\modules\mcp_server\scripts\gen_renamed_contract.py",
]
KEY = re.compile(r'^\s{4}"([a-z0-9_]+)"\s*:', re.M)


def main():
    sets = {}
    for p in PATHS:
        b = io.open(p, "rb").read()
        s = b.decode("utf-8", errors="replace")
        tag = p.replace("\\", "/").split("/")[-2] + "/" + p.split("\\")[-1]
        rep.log("=" * 90)
        rep.log("%s" % p)
        rep.log("  bytes=%d sha256=%s lf=%d" % (len(b), hashlib.sha256(b).hexdigest(), s.count("\n")))
        rep.log("  GENERATOR_VERSION=%s" % re.findall(r'GENERATOR_VERSION\s*=\s*"([^"]+)"', s))
        for tbl in ("DESCRIPTION_OVERRIDES", "SCHEMA_OVERRIDES"):
            m = re.search(r"^%s\s*=\s*\{(.*?)^\}" % tbl, s, re.S | re.M)
            if not m:
                rep.log("  %s MISSING" % tbl)
                continue
            names = KEY.findall(m.group(1))
            sets.setdefault(tbl, []).append((tag, names))
            rep.log("  %s (%d): %s" % (tbl, len(names), ", ".join(names)))
    rep.log("")
    for tbl, lst in sets.items():
        if len(lst) == 2:
            a, b = set(lst[0][1]), set(lst[1][1])
            rep.log("%s  only-in-tree: %s" % (tbl, sorted(a - b)))
            rep.log("%s  only-in-staging: %s" % (tbl, sorted(b - a)))
    rep.flush()


if __name__ == "__main__":
    main()
