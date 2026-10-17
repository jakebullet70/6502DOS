"""Make an SD card image with one FAT32 partition from a folder.

    python tools/mksd.py FOLDER IMAGE [--sectors-per-cluster N] [--clusters N] [--date YYYY-MM-DD]
                         [FILE ...]

The image has an MBR with one partition of type $0C at sector 2048. The partition holds a FAT32
file system with 512-byte sectors, 32 reserved sectors and 2 FATs. Every file and folder in
FOLDER goes in, with its 8.3 name in upper case; names that start with a dot are left out. Each
FILE goes in the root directory too. Each file's clusters follow each other. The times are the files' modification times, or noon of
--date. Exit status 1 when a name is not 8.3 or the files do not fit.

The defaults, 1 sector per cluster and 6016 clusters, make a 4 MB image, the size of the X16's
standard card. UXDOS16 reads it, but other systems take it for FAT16: FAT32 needs 65525 clusters.
"""

import datetime
import os
import struct
import sys

SECTOR = 512
PARTITION_START = 2048
RESERVED = 32
FATS = 2
NAME_CHARACTERS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!#$%&'()-@^_`{}~")
ATTR_DIR = 0x10
ATTR_ARCHIVE = 0x20
END_OF_CHAIN = 0x0FFFFFFF


def name83(name):
    """Return the 11-byte directory name of name, or None when it is not 8.3."""
    upper = name.upper()
    base, dot, extension = upper.partition(".")
    if not 1 <= len(base) <= 8 or len(extension) > 3 or "." in extension:
        return None
    if not set(base + extension) <= NAME_CHARACTERS:
        return None
    return (base.ljust(8) + extension.ljust(3)).encode("ascii")


class Node:
    def __init__(self, path, name, is_dir):
        self.path = path
        self.name = name
        self.is_dir = is_dir
        self.children = []
        self.size = 0 if is_dir else os.path.getsize(path)
        self.first = 0
        self.clusters = 0


def scan(path, name, extra=()):
    """Return the Node of the folder path, with the files in extra added to it."""
    node = Node(path, name, True)
    names = []
    fulls = [os.path.join(path, entry) for entry in os.listdir(path) if not entry.startswith(".")]
    for full in sorted(fulls + list(extra), key=lambda f: os.path.basename(f).upper()):
        entry = os.path.basename(full)
        short = name83(entry)
        if short is None:
            sys.exit("mksd: %s is not an 8.3 name" % full)
        if short in names:
            sys.exit("mksd: %s repeats a name" % full)
        names.append(short)
        if os.path.isdir(full):
            node.children.append(scan(full, short))
        else:
            node.children.append(Node(full, short, False))
    return node


def dos_time(when):
    time = (when.hour << 11) | (when.minute << 5) | (when.second // 2)
    date = ((when.year - 1980) << 9) | (when.month << 5) | when.day
    return time, date


def make(folder, image, sectors_per_cluster=1, clusters=6016, date=None, extra=()):
    """Write image from folder, with the files in extra in the root directory too."""
    cluster_bytes = sectors_per_cluster * SECTOR
    root = scan(folder, None, extra)
    fat = [0x0FFFFFF8, END_OF_CHAIN] + [0] * clusters
    next_free = [2]

    def allocate(node, count):
        if count == 0:
            return
        node.first = next_free[0]
        node.clusters = count
        for n in range(node.first, node.first + count):
            fat[n] = n + 1
        fat[node.first + count - 1] = END_OF_CHAIN
        next_free[0] += count
        if next_free[0] > clusters + 2:
            sys.exit("mksd: the files need more than %d clusters" % clusters)

    def place(node, is_root):
        entries = len(node.children) + (0 if is_root else 2)
        allocate(node, max(1, -(-entries * 32 // cluster_bytes)))
        for child in node.children:
            if child.is_dir:
                place(child, False)
            else:
                allocate(child, -(-child.size // cluster_bytes))

    place(root, True)
    fat_sectors = -(-(clusters + 2) * 4 // SECTOR)
    data_start = RESERVED + FATS * fat_sectors
    total = data_start + clusters * sectors_per_cluster

    def stamp(node):
        when = datetime.datetime.fromtimestamp(os.path.getmtime(node.path))
        if date is not None:
            when = datetime.datetime.combine(date, datetime.time(12, 0))
        return dos_time(when)

    def entry(name, attr, first, size, time, date_):
        return struct.pack("<11sBBBHHHHHHHI", name, attr, 0, 0, time, date_, date_,
                           first >> 16, time, date_, first & 0xFFFF, size)

    def cluster_offset(n):
        return (PARTITION_START + data_start + (n - 2) * sectors_per_cluster) * SECTOR

    with open(image, "wb") as out:
        mbr = bytearray(SECTOR)
        mbr[446:462] = struct.pack("<B3sB3sII", 0, b"\xFE\xFF\xFF", 0x0C, b"\xFE\xFF\xFF",
                                   PARTITION_START, total)
        mbr[510:512] = b"\x55\xAA"
        out.write(mbr)

        boot = bytearray(SECTOR)
        boot[0:3] = b"\xEB\x58\x90"
        boot[3:11] = b"UXDOS16 "
        struct.pack_into("<HBHBHHBHHHII", boot, 11, SECTOR, sectors_per_cluster, RESERVED,
                         FATS, 0, 0, 0xF8, 0, 32, 64, PARTITION_START, total)
        struct.pack_into("<IHHIHH", boot, 36, fat_sectors, 0, 0, 2, 1, 6)
        struct.pack_into("<BBBI11s8s", boot, 64, 0x80, 0, 0x29, 0x16161616, b"UXDOS16    ",
                         b"FAT32   ")
        boot[510:512] = b"\x55\xAA"
        info = bytearray(SECTOR)
        struct.pack_into("<I", info, 0, 0x41615252)
        struct.pack_into("<III", info, 484, 0x61417272, clusters + 2 - next_free[0], next_free[0])
        struct.pack_into("<I", info, 508, 0xAA550000)
        for first in (0, 6):
            out.seek((PARTITION_START + first) * SECTOR)
            out.write(boot)
            out.write(info)

        table = struct.pack("<%dI" % len(fat), *fat)
        for n in range(FATS):
            out.seek((PARTITION_START + RESERVED + n * fat_sectors) * SECTOR)
            out.write(table)

        def write(node, parent_first):
            if node.is_dir:
                time, date_ = stamp(node)
                data = bytearray()
                if node.name is not None:
                    data += entry(b".          ", ATTR_DIR, node.first, 0, time, date_)
                    data += entry(b"..         ", ATTR_DIR, parent_first, 0, time, date_)
                for child in node.children:
                    child_time, child_date = stamp(child)
                    data += entry(child.name, ATTR_DIR if child.is_dir else ATTR_ARCHIVE,
                                  child.first, child.size, child_time, child_date)
                # A subdirectory's ".." names the root as cluster 0.
                for child in node.children:
                    write(child, 0 if node.name is None else node.first)
            else:
                data = open(node.path, "rb").read()
            if data:
                out.seek(cluster_offset(node.first))
                out.write(data)

        write(root, 0)
        out.truncate((PARTITION_START + total) * SECTOR)


def main():
    args = sys.argv[1:]
    options = {"--sectors-per-cluster": 1, "--clusters": 6016, "--date": None}
    positional = []
    while args:
        arg = args.pop(0)
        if arg in options:
            if not args:
                sys.exit("mksd: %s needs a value" % arg)
            value = args.pop(0)
            options[arg] = (datetime.date.fromisoformat(value) if arg == "--date"
                            else int(value))
        else:
            positional.append(arg)
    if len(positional) < 2:
        sys.exit(__doc__)
    make(positional[0], positional[1], options["--sectors-per-cluster"], options["--clusters"],
         options["--date"], positional[2:])


if __name__ == "__main__":
    main()
