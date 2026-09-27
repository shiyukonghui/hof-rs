#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-115: write the three PNG fixtures the H7 diff probe needs.

assets/a.png  (8x8, solid red)   \
assets/b.png  (8x8, half red)     > same size as each other -> the diff runs
assets/c16.png (16x16, red)        separate size -> the size-mismatch refusal

No third-party library: a PNG is an IHDR + IDAT(zlib) + IEND chunk stream and
the encoder below is the whole of what these 8x8/16x16 pictures need.
"""
import io
import os
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
ASSETS = os.path.join(ROOT, "projects", "_exercises", "ex_editor", "assets")


def chunk(tag, payload):
    return (struct.pack(">I", len(payload)) + tag + payload
            + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF))


def write_png(path, width, height, rows):
    raw = b"".join(b"\x00" + row for row in rows)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as handle:
        handle.write(png)
    return len(png)


def solid(width, height, rgb):
    return [bytes(rgb) * width for _ in range(height)]


def half(width, height, rgb, other):
    rows = []
    for y in range(height):
        rows.append(bytes(rgb if y < height // 2 else other) * width)
    return rows


def main():
    os.makedirs(ASSETS, exist_ok=True)
    specs = [
        ("a.png", 8, 8, solid(8, 8, (255, 0, 0))),
        ("b.png", 8, 8, half(8, 8, (255, 0, 0), (0, 0, 255))),
        ("c16.png", 16, 16, solid(16, 16, (255, 0, 0))),
    ]
    for name, width, height, rows in specs:
        path = os.path.join(ASSETS, name)
        size = write_png(path, width, height, rows)
        print("wrote %s %dx%d %d bytes" % (path, width, height, size))
    return 0


if __name__ == "__main__":
    sys.exit(main())
