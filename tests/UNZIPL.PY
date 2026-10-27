"""UNZIPL's card: the programs of the test card, and in its root the archives that UNZIP -l
lists, made here with zipfile:

- TEST.ZIP: HELLO.TXT stored, the folder DOCS/, DOCS/LONG.TXT deflated, and a comment;
- BIG.ZIP: DATA.BIN stored, and a comment of 1000 bytes, so the end record is 3 blocks back;
- EMPTY.ZIP: no entries;
- NOTZIP.TXT: text with no end record.
"""

import glob
import os
import shutil
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import mksd  # noqa: E402

FOLDER = os.path.join(ROOT, "build", "tests", "UNZIPL")
STAMP = (2026, 10, 13, 12, 0, 0)


def add(archive, name, data, method):
    entry = zipfile.ZipInfo(name, STAMP)
    entry.compress_type = method
    archive.writestr(entry, data)


def card(image):
    shutil.rmtree(FOLDER, ignore_errors=True)
    os.makedirs(FOLDER)
    with zipfile.ZipFile(os.path.join(FOLDER, "TEST.ZIP"), "w") as archive:
        add(archive, "HELLO.TXT", b"HELLO, WORLD\r\n", zipfile.ZIP_STORED)
        add(archive, "DOCS/", b"", zipfile.ZIP_STORED)
        add(archive, "DOCS/LONG.TXT", b"THE QUICK BROWN FOX\r\n" * 100, zipfile.ZIP_DEFLATED)
        archive.comment = b"A TEST ARCHIVE"
    with zipfile.ZipFile(os.path.join(FOLDER, "BIG.ZIP"), "w") as archive:
        add(archive, "DATA.BIN", bytes(range(256)) * 12, zipfile.ZIP_STORED)
        archive.comment = b"PK" * 500
    with zipfile.ZipFile(os.path.join(FOLDER, "EMPTY.ZIP"), "w"):
        pass
    with open(os.path.join(FOLDER, "NOTZIP.TXT"), "wb") as out:
        out.write(b"NO ARCHIVE HERE, JUST TEXT LONG ENOUGH FOR AN END RECORD\r\n")
    programs = sorted(glob.glob(os.path.join(ROOT, "build", "bas", "*.COM")))
    programs += [os.path.join(ROOT, "build", "DOS"), os.path.join(ROOT, "build", "UTILS")]
    mksd.make(FOLDER, image, extra=programs)
