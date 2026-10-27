"""ZIPS's card: the programs of the test card, and in its root the files that ZIP adds:

- HELLO.TXT and NOTE.TXT;
- BIG.BIN, 5000 bytes, more than the 512 bytes ZIP reads at a time;
- DOCS/A.TXT, DOCS/SUB/B.TXT and the empty folder DOCS/EMPTY;
- OLD.ZIP, made here with zipfile: HELLO.TXT, the old text; KEEP.TXT stored; LONG.TXT
  deflated; DESC.TXT written as a stream, with a data descriptor.
"""

import datetime
import glob
import io
import os
import shutil
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import mksd  # noqa: E402

FOLDER = os.path.join(ROOT, "build", "tests", "ZIPS")
STAMP = (2026, 10, 13, 12, 0, 0)


class Stream:
    """A file that only takes writes, so zipfile writes data descriptors."""

    def __init__(self):
        self.data = io.BytesIO()

    def write(self, data):
        return self.data.write(data)

    def flush(self):
        pass


def add(archive, name, data, method=zipfile.ZIP_STORED):
    entry = zipfile.ZipInfo(name, STAMP)
    entry.compress_type = method
    archive.writestr(entry, data)


def write(name, data):
    path = os.path.join(FOLDER, *name.split("/"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "wb").write(data)


def card(image):
    shutil.rmtree(FOLDER, ignore_errors=True)
    os.makedirs(os.path.join(FOLDER, "DOCS", "EMPTY"))
    write("HELLO.TXT", b"HELLO, NEW WORLD\r\n")
    write("NOTE.TXT", b"A NOTE\r\n")
    write("BIG.BIN", bytes((n * 7 + n // 256) & 255 for n in range(5000)))
    write("DOCS/A.TXT", b"A IN DOCS\r\n")
    write("DOCS/SUB/B.TXT", b"B TWO FOLDERS DOWN\r\n")
    with zipfile.ZipFile(os.path.join(FOLDER, "OLD.ZIP"), "w") as archive:
        add(archive, "HELLO.TXT", b"HELLO, OLD WORLD\r\n")
        add(archive, "KEEP.TXT", b"KEPT FROM THE OLD ARCHIVE\r\n")
        add(archive, "LONG.TXT", b"THE QUICK BROWN FOX\r\n" * 100, zipfile.ZIP_DEFLATED)
    stream = Stream()
    with zipfile.ZipFile(stream, "w") as archive:
        add(archive, "DESC.TXT", b"WRITTEN AS A STREAM\r\n")
    old = open(os.path.join(FOLDER, "OLD.ZIP"), "rb").read()
    desc = stream.data.getvalue()
    # OLD.ZIP with DESC.TXT's local entry and descriptor after its last entry, and its central
    # entry after OLD.ZIP's.
    with zipfile.ZipFile(io.BytesIO(old)) as archive:
        directory = archive.start_dir
        count = len(archive.infolist())
    with zipfile.ZipFile(io.BytesIO(desc)) as archive:
        desc_directory = archive.start_dir
    local = desc[:desc_directory]
    central = bytearray(desc[desc_directory:desc.find(b"PK\x05\x06")])
    central[42:46] = directory.to_bytes(4, "little")
    end = bytearray(old[old.find(b"PK\x05\x06"):])
    end[8:10] = end[10:12] = (count + 1).to_bytes(2, "little")
    size = len(old) - len(end) - directory + len(central)
    end[12:16] = size.to_bytes(4, "little")
    end[16:20] = (directory + len(local)).to_bytes(4, "little")
    merged = old[:directory] + local + old[directory:len(old) - len(end)] + bytes(central)
    open(os.path.join(FOLDER, "OLD.ZIP"), "wb").write(merged + bytes(end))
    with zipfile.ZipFile(os.path.join(FOLDER, "OLD.ZIP")) as archive:
        assert archive.testzip() is None
        assert archive.getinfo("DESC.TXT").flag_bits & 8
    programs = sorted(glob.glob(os.path.join(ROOT, "build", "bas", "*.COM")))
    programs += [os.path.join(ROOT, "build", "DOS"), os.path.join(ROOT, "build", "UTILS")]
    mksd.make(FOLDER, image, extra=programs, date=datetime.date(2026, 10, 13))
