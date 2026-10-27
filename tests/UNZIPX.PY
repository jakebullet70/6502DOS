"""UNZIPX's card: the programs of the test card, and in its root the archives that UNZIP
extracts, made here with zipfile:

- TEST.ZIP: HELLO.TXT, EMPTY.TXT, the folder DOCS/, DOCS/SUB/NOTE.TXT and BIN/DATA.BIN
  stored, DOCS/LONG.TXT deflated;
- BAD.ZIP: GOOD.TXT; CORRUPT.TXT, a byte of its data changed; SECRET.TXT, marked encrypted;
  ../EVIL.TXT and C:/EVIL.TXT, unsafe names.
"""

import glob
import os
import shutil
import struct
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import mksd  # noqa: E402

FOLDER = os.path.join(ROOT, "build", "tests", "UNZIPX")
STAMP = (2026, 10, 13, 12, 0, 0)


def add(archive, name, data, method=zipfile.ZIP_STORED):
    entry = zipfile.ZipInfo(name, STAMP)
    entry.compress_type = method
    archive.writestr(entry, data)


def patch(path, name, change):
    """Calls change(data, local, central) for the entry name of the archive at path, with the
    offsets of its local header and central directory entry, and writes the archive back."""
    data = bytearray(open(path, "rb").read())
    at = data.find(b"PK\x01\x02")
    while at >= 0:
        size = struct.unpack_from("<H", data, at + 28)[0]
        if data[at + 46:at + 46 + size] == name.encode():
            change(data, struct.unpack_from("<I", data, at + 42)[0], at)
        at = data.find(b"PK\x01\x02", at + 46)
    open(path, "wb").write(data)


def corrupt(data, local, central):
    size, extra = struct.unpack_from("<HH", data, local + 26)
    data[local + 30 + size + extra] ^= 0xFF


def encrypted(data, local, central):
    data[local + 6] |= 1
    data[central + 8] |= 1


def card(image):
    shutil.rmtree(FOLDER, ignore_errors=True)
    os.makedirs(FOLDER)
    with zipfile.ZipFile(os.path.join(FOLDER, "TEST.ZIP"), "w") as archive:
        add(archive, "HELLO.TXT", b"HELLO, WORLD\r\n")
        add(archive, "EMPTY.TXT", b"")
        add(archive, "DOCS/", b"")
        add(archive, "DOCS/SUB/NOTE.TXT", b"A NOTE TWO FOLDERS DOWN\r\n")
        add(archive, "DOCS/LONG.TXT", b"THE QUICK BROWN FOX\r\n" * 100, zipfile.ZIP_DEFLATED)
        add(archive, "BIN/DATA.BIN", bytes(range(256)) * 12)
    bad = os.path.join(FOLDER, "BAD.ZIP")
    with zipfile.ZipFile(bad, "w") as archive:
        add(archive, "GOOD.TXT", b"GOOD\r\n")
        add(archive, "CORRUPT.TXT", b"CORRUPT\r\n")
        add(archive, "SECRET.TXT", b"SECRET\r\n")
        add(archive, "../EVIL.TXT", b"EVIL\r\n")
        add(archive, "C:/EVIL.TXT", b"EVIL\r\n")
    patch(bad, "CORRUPT.TXT", corrupt)
    patch(bad, "SECRET.TXT", encrypted)
    programs = sorted(glob.glob(os.path.join(ROOT, "build", "bas", "*.COM")))
    programs += [os.path.join(ROOT, "build", "DOS"), os.path.join(ROOT, "build", "UTILS")]
    mksd.make(FOLDER, image, extra=programs)
