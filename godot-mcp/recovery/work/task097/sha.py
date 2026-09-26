# TASK-097 helper: a file's sha256 and size as one line (no shell parsing games).
#   python sha.py <file> [<file> ...]
import hashlib
import os
import sys

for path in sys.argv[1:]:
    if not os.path.isfile(path):
        print("MISSING %s" % path)
        continue
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    print("%s %d %s" % (digest.hexdigest().upper(), os.path.getsize(path), path))
