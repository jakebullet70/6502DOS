"""UNZIPD's card: the programs of the test card, and in its root the archives that UNZIP
inflates, made here with zipfile:

- DEFL.ZIP: FIXED.TXT, a fixed-code block; DYN.TXT, dynamic blocks; RAND.BIN, random bytes in
  stored blocks; BIG.BIN, 12000 random bytes three times, so its matches reach 12000 bytes
  back and its 36000 bytes go round the 32 KB window; NONE.TXT, empty; all deflated.
- BADD.ZIP: KIND.TXT, its first block of the reserved type 3; SHORT.TXT, its packed size cut
  to 4 bytes.
"""

import glob
import os
import random
import shutil
import struct
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import mksd  # noqa: E402

FOLDER = os.path.join(ROOT, "build", "tests", "UNZIPD")
STAMP = (2026, 10, 27, 12, 0, 0)
WORDS = ("THE QUICK BROWN FOX JUMPS OVER A LAZY DOG WHILE SIX WIZARDS BOX AND "
         "JACKDAWS LOVE MY BIG SPHINX OF QUARTZ").split()


def add(archive, name, data):
    entry = zipfile.ZipInfo(name, STAMP)
    entry.compress_type = zipfile.ZIP_DEFLATED
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


def reserved(data, local, central):
    size, extra = struct.unpack_from("<HH", data, local + 26)
    data[local + 30 + size + extra] |= 0x07


def short(data, local, central):
    struct.pack_into("<I", data, central + 20, 4)


def card(image):
    shutil.rmtree(FOLDER, ignore_errors=True)
    os.makedirs(FOLDER)
    chance = random.Random(27)
    text = "".join(" ".join(chance.choice(WORDS) for _ in range(12)) + "\r\n"
                   for _ in range(400)).encode()
    block = bytes(chance.randrange(256) for _ in range(12000))
    with zipfile.ZipFile(os.path.join(FOLDER, "DEFL.ZIP"), "w") as archive:
        add(archive, "FIXED.TXT", b"HELLO HELLO HELLO FIXED\r\n")
        add(archive, "DYN.TXT", text)
        add(archive, "RAND.BIN", bytes(chance.randrange(256) for _ in range(3000)))
        add(archive, "BIG.BIN", block * 3)
        add(archive, "NONE.TXT", b"")
    bad = os.path.join(FOLDER, "BADD.ZIP")
    with zipfile.ZipFile(bad, "w") as archive:
        add(archive, "KIND.TXT", b"KIND KIND KIND\r\n")
        add(archive, "SHORT.TXT", text)
    patch(bad, "KIND.TXT", reserved)
    patch(bad, "SHORT.TXT", short)
    programs = sorted(glob.glob(os.path.join(ROOT, "build", "bas", "*.COM")))
    programs += [os.path.join(ROOT, "build", "DOS"), os.path.join(ROOT, "build", "UTILS")]
    mksd.make(FOLDER, image, extra=programs)
