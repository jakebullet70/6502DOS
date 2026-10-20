"""Make an SD card image with one FAT32 partition from a folder.

    python tools/mksd.py FOLDER IMAGE [--sectors-per-cluster N] [--clusters N] [--date YYYY-MM-DD]
                         [FILE ...]

The image has an MBR with one partition of type $0C at sector 2048. The partition holds a FAT32
file system with 512-byte sectors, 32 reserved sectors and 2 FATs. Every file and folder in
FOLDER goes in; names that start with a dot are left out. A name that is 8.3 goes in as its 8.3
name in upper case. Any other name, up to 255 characters, goes in as a long name, as typed,
with an 8.3 alias BASE~N.EXT; 6502DOS shows a long name over 32 characters as its alias. Each
FILE goes in the root directory too. Each file's clusters follow each other. The times are the
files' modification times, or noon of --date. Exit status 1 when a name is too long or holds a
character a long name cannot, or the files do not fit.

The defaults, 1 sector per cluster and 6016 clusters, make a 4 MB image, the size of the X16's
standard card. 6502DOS reads it, but other systems take it for FAT16: FAT32 needs 65525 clusters.
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
LONG_NAME_MAX = 255
LONG_NAME_BANNED = set('\\/:*?"<>|')
LONG_NAME_CHARACTERS = 13           # the characters of one long-name entry
ATTR_LONG_NAME = 0x0F
ATTR_DIR = 0x10
ATTR_ARCHIVE = 0x20
BAD_CLUSTER = 0x0FFFFFF7
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


def alias83(name, taken):
    """Return an 11-byte 8.3 alias BASE~N.EXT of the long name name, not in taken."""
    upper = name.upper()
    base, dot, extension = upper.rpartition(".")
    if not dot:
        base, extension = upper, ""
    base = "".join(c for c in base if c in NAME_CHARACTERS) or "_"
    extension = "".join(c for c in extension if c in NAME_CHARACTERS)[:3]
    for n in range(1, 1000000):
        tail = "~%d" % n
        short = (base[:8 - len(tail)] + tail).ljust(8) + extension.ljust(3)
        if short.encode("ascii") not in taken:
            return short.encode("ascii")
    sys.exit("mksd: no alias for %s" % name)


def checksum(short):
    """Return the checksum of an 11-byte 8.3 name that its long-name entries hold."""
    total = 0
    for byte in short:
        total = (((total & 1) << 7) + (total >> 1) + byte) & 0xFF
    return total


def long_entries(name, short):
    """Return the long-name entries of name, before the entry of its 8.3 alias short."""
    units = [ord(c) for c in name]
    if len(units) % LONG_NAME_CHARACTERS:
        units += [0] + [0xFFFF] * (-len(units) % LONG_NAME_CHARACTERS - 1)
    count = len(units) // LONG_NAME_CHARACTERS
    total = checksum(short)
    entries = []
    for n in range(count):
        part = units[n * LONG_NAME_CHARACTERS:(n + 1) * LONG_NAME_CHARACTERS]
        order = n + 1 | (0x40 if n == count - 1 else 0)
        entries.append(struct.pack("<B5HBBB6HH2H", order, *part[:5], ATTR_LONG_NAME, 0, total,
                                   *part[5:11], 0, *part[11:13]))
    return b"".join(reversed(entries))


class Node:
    def __init__(self, path, name, is_dir, long_name=None):
        self.path = path
        self.name = name
        self.long_name = long_name
        self.is_dir = is_dir
        self.children = []
        self.size = 0 if is_dir else os.path.getsize(path)
        self.first = 0
        self.clusters = 0
        self.extra = False


def scan(path, name, extra=()):
    """Return the Node of the folder path, with the files in extra added to it."""
    node = Node(path, name, True)
    fulls = [os.path.join(path, entry) for entry in os.listdir(path) if not entry.startswith(".")]
    fulls = sorted(fulls + list(extra), key=lambda f: os.path.basename(f).upper())
    entries = [os.path.basename(full) for full in fulls]
    uppers = [entry.upper() for entry in entries]
    taken = set(short for short in map(name83, entries) if short is not None)
    for full, entry in zip(fulls, entries):
        if uppers.count(entry.upper()) > 1:
            sys.exit("mksd: %s repeats a name" % full)
        short = name83(entry)
        long_name = None
        if short is None:
            if len(entry) > LONG_NAME_MAX:
                sys.exit("mksd: %s is longer than %d characters" % (full, LONG_NAME_MAX))
            if set(entry) & LONG_NAME_BANNED or any(ord(c) < 32 or ord(c) > 255 for c in entry):
                sys.exit("mksd: %s holds a character a long name cannot" % full)
            short = alias83(entry, taken)
            taken.add(short)
            long_name = entry
        if os.path.isdir(full):
            child = scan(full, short)
            child.long_name = long_name
        else:
            child = Node(full, short, False, long_name)
        child.extra = full in extra
        node.children.append(child)
    return node


def dos_time(when):
    time = (when.hour << 11) | (when.minute << 5) | (when.second // 2)
    date = ((when.year - 1980) << 9) | (when.month << 5) | when.day
    return time, date


def make(folder, image, sectors_per_cluster=1, clusters=6016, date=None, extra=(), reserve=0,
         root_clusters=1):
    """Write image from folder, with the files in extra in the root directory too.

    The root directory takes at least root_clusters clusters. With reserve above 0, the files
    in extra go in a block of reserve clusters after the files of folder, and the FAT marks the
    clusters of the block they leave unused as bad. Exit status 1 when they need more.
    """
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

    def place_children(node, children):
        for child in children:
            if child.is_dir:
                place(child, False)
            else:
                allocate(child, -(-child.size // cluster_bytes))

    def place(node, is_root, least=1):
        entries = (0 if is_root else 2) + sum(
            1 + (-(-(len(child.long_name) + 1) // LONG_NAME_CHARACTERS) if child.long_name else 0)
            for child in node.children)
        allocate(node, max(least, -(-entries * 32 // cluster_bytes)))
        place_children(node, [child for child in node.children if not child.extra])

    place(root, True, root_clusters)
    extras = [child for child in root.children if child.extra]
    if reserve:
        block_end = next_free[0] + reserve
        if block_end > clusters + 2:
            sys.exit("mksd: the files need more than %d clusters" % clusters)
        place_children(root, extras)
        if next_free[0] > block_end:
            sys.exit("mksd: the extra files need more than %d clusters" % reserve)
        for n in range(next_free[0], block_end):
            fat[n] = BAD_CLUSTER
        next_free[0] = block_end
    else:
        place_children(root, extras)
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
        boot[3:11] = b"6502DOS "
        struct.pack_into("<HBHBHHBHHHII", boot, 11, SECTOR, sectors_per_cluster, RESERVED,
                         FATS, 0, 0, 0xF8, 0, 32, 64, PARTITION_START, total)
        struct.pack_into("<IHHIHH", boot, 36, fat_sectors, 0, 0, 2, 1, 6)
        struct.pack_into("<BBBI11s8s", boot, 64, 0x80, 0, 0x29, 0x16161616, b"6502DOS    ",
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
                    if child.long_name:
                        data += long_entries(child.long_name, child.name)
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


def read(image):
    """Return the files and folders of image as a list of (path, data, when).

    path is the names from the root, joined by "/", each the long name when there is one, else
    the 8.3 name as BASE.EXT. data is the file's bytes, or None for a folder. when is the
    entry's modification time as a datetime, or None when the entry holds no valid date.
    """
    with open(image, "rb") as source:
        disk = source.read()
    start = 0
    for n in range(4):
        part = disk[446 + 16 * n:462 + 16 * n]
        if part[4] in (0x0B, 0x0C):
            start = struct.unpack("<I", part[8:12])[0] * SECTOR
            break
    boot = disk[start:start + SECTOR]
    cluster_sectors = boot[13]
    reserved, fats = struct.unpack("<HB", boot[14:17])
    fat_sectors = struct.unpack("<I", boot[36:40])[0]
    root_first = struct.unpack("<I", boot[44:48])[0]
    fat_start = start + reserved * SECTOR
    data_start = fat_start + fats * fat_sectors * SECTOR
    cluster_bytes = cluster_sectors * SECTOR

    def chain(first, size=None):
        out = bytearray()
        cluster = first
        while 2 <= cluster < 0x0FFFFFF7 and (size is None or len(out) < size):
            offset = data_start + (cluster - 2) * cluster_bytes
            out += disk[offset:offset + cluster_bytes]
            link = fat_start + cluster * 4
            cluster = struct.unpack("<I", disk[link:link + 4])[0] & 0x0FFFFFFF
        return bytes(out if size is None else out[:size])

    def stamp(time, date_):
        try:
            return datetime.datetime(1980 + (date_ >> 9), date_ >> 5 & 15, date_ & 31,
                                     time >> 11, time >> 5 & 63, (time & 31) * 2)
        except ValueError:
            return None

    found = []

    def walk(first, prefix):
        raw = chain(first)
        units = []
        for offset in range(0, len(raw), 32):
            e = raw[offset:offset + 32]
            if e[0] == 0:
                break
            if e[0] == 0xE5:
                units = []
                continue
            if e[11] == ATTR_LONG_NAME:
                part = struct.unpack("<5H", e[1:11]) + struct.unpack("<6H", e[14:26]) \
                    + struct.unpack("<2H", e[28:32])
                units = list(part) + ([] if e[0] & 0x40 else units)
                continue
            if e[11] & 0x08 or e[:2] in (b". ", b".."):
                units = []
                continue
            if units:
                units = units[:units.index(0)] if 0 in units else units
                name = "".join(chr(u) for u in units)
            else:
                short = (b"\xE5" + e[1:11] if e[0] == 0x05 else e[:11]).decode("latin-1")
                name = short[:8].rstrip() + ("." + short[8:].rstrip() if short[8:].strip()
                                             else "")
            units = []
            path = prefix + name
            high, low = struct.unpack("<H", e[20:22])[0], struct.unpack("<H", e[26:28])[0]
            first_cluster = high << 16 | low
            when = stamp(*struct.unpack("<HH", e[22:26]))
            if e[11] & ATTR_DIR:
                found.append((path, None, when))
                walk(first_cluster, path + "/")
            else:
                size = struct.unpack("<I", e[28:32])[0]
                found.append((path, chain(first_cluster, size) if size else b"", when))

    walk(root_first, "")
    return found


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
