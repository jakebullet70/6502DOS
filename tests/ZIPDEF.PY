"""ZIPDEF's card: the programs of the test card, and in its root the files that ZIP deflates:

- EMPTY.TXT, no bytes;
- TEXT.TXT, lines of text that repeat with changes;
- MIX.BIN, 16000 bytes of random bytes and copies of what came before, 3 to 258 bytes long and
  1 to 15999 bytes back;
- RAND.BIN, 8000 random bytes;
- HALF.BIN, 2000 random bytes, then 8008 bytes of a short run repeated.
"""

import datetime
import glob
import os
import random
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import mksd  # noqa: E402

FOLDER = os.path.join(ROOT, "build", "tests", "ZIPDEF")


def write(name, data):
    open(os.path.join(FOLDER, name), "wb").write(data)


def mix(chance, size):
    """size bytes of random bytes and copies, as a deflate stream would give them back."""
    data = bytearray()
    while len(data) < size:
        if len(data) < 300 or chance.random() < 0.3:
            data += bytes(chance.randrange(256) for _ in range(chance.randrange(1, 20)))
        else:
            back = chance.choice([chance.randrange(1, 300), chance.randrange(1, min(len(data), 31743) + 1)])
            back = min(back, len(data))
            length = chance.choice([chance.randrange(3, 20), chance.randrange(3, 259)])
            for _ in range(length):
                data.append(data[-back])
    return bytes(data[:size])


def card(image):
    shutil.rmtree(FOLDER, ignore_errors=True)
    os.makedirs(FOLDER)
    chance = random.Random(1983)
    write("EMPTY.TXT", b"")
    lines = []
    for n in range(60):
        lines.append(b"LINE %d OF THE TEXT, WITH WORDS THAT COME BACK AGAIN AND AGAIN\r\n" % (n * 7))
    write("TEXT.TXT", b"".join(lines))
    write("MIX.BIN", mix(chance, 16000))
    write("RAND.BIN", bytes(chance.randrange(256) for _ in range(8000)))
    write("HALF.BIN", bytes(chance.randrange(256) for _ in range(2000)) + b"RUN OF BYTES " * 616)
    programs = sorted(glob.glob(os.path.join(ROOT, "build", "bas", "*.COM")))
    programs += [os.path.join(ROOT, "build", "DOS"), os.path.join(ROOT, "build", "UTILS")]
    mksd.make(FOLDER, image, extra=programs, date=datetime.date(2026, 10, 13))
