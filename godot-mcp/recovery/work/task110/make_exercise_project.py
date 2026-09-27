#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-110: instantiate the exercise projects used by the coverage batches.

Read-only against the game projects it copies from; writes ONLY under
projects/_exercises/<name>. Iron rule 6: the existing 20 game projects under
projects/ and everything under runs/ are treated as frozen inputs.

The Godot cache directories (.godot, obj, bin) are deliberately NOT copied: the
driver runs `--import` itself and the batch sessions build the C# assembly with
project_build_csharp, so a copied cache would only carry stale absolute paths.

Usage:
    python recovery/work/task110/make_exercise_project.py ex_files
"""
import io
import os
import shutil
import struct
import sys
import zlib

ROOT = r"F:\moonbit-hof-rs\godot-mcp"
EX = os.path.join(ROOT, "projects", "_exercises")
SOURCE = os.path.join(ROOT, "projects", "pong")
SKIP_DIRS = {".godot", "obj", "bin", ".vs"}


def copy_project(name, source=SOURCE):
    dest = os.path.join(EX, name)
    if os.path.isdir(dest):
        print("already present: %s" % dest)
        return dest
    if not os.path.isdir(source):
        raise SystemExit("source project missing: %s" % source)
    os.makedirs(dest)
    copied = []
    for dirpath, dirnames, filenames in os.walk(source):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        rel = os.path.relpath(dirpath, source)
        target_dir = dest if rel == "." else os.path.join(dest, rel)
        if not os.path.isdir(target_dir):
            os.makedirs(target_dir)
        for fname in filenames:
            shutil.copy2(os.path.join(dirpath, fname), os.path.join(target_dir, fname))
            copied.append(os.path.join(rel, fname).replace("\\", "/") if rel != "." else fname)
    print("created %s from %s (%d files)" % (dest, source, len(copied)))
    for item in sorted(copied):
        print("   ", item)
    return dest


def _png(width, height, rgb):
    """A minimal valid PNG (no third-party imaging library on this machine)."""
    raw = b""
    for _y in range(height):
        raw += b"\x00" + bytes(rgb) * width

    def chunk(kind, payload):
        body = kind + payload
        return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def seed_pngs(name, count=5):
    """Five tiny images, so project_get_resource_preview has something to preview.

    The tool only previews resources that HAVE an image preview; without an
    imported Texture the whole family answers -32602 ('does not have an image
    preview'), which is a legitimate boundary but leaves the tool with zero
    effective calls. A texture is the precondition the tool actually needs.
    """
    dest_dir = os.path.join(EX, name, "assets")
    if not os.path.isdir(dest_dir):
        os.makedirs(dest_dir)
    written = []
    for i in range(count):
        path = os.path.join(dest_dir, "seed%d.png" % (i + 1))
        with open(path, "wb") as h:
            h.write(_png(8, 8, (20 + 40 * i, 60, 200 - 20 * i)))
        written.append(path)
    print("seeded %d PNG(s) in %s" % (len(written), dest_dir))
    for p in written:
        print("   ", p)


if __name__ == "__main__":
    names = sys.argv[1:] or ["ex_files"]
    for n in names:
        copy_project(n)
        seed_pngs(n)

