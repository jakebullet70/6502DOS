"""CHKFIX's card: 4 MB at 1 sector per cluster, with CMDSHELL.COM and the folder DOS from
build, then damaged for CHKDSK -F. From the first free cluster F:
- F to F+2 chained in the FAT with no entry: a lost chain;
- SHORT.DAT: a size of 5000 on the chain F+3 to F+4;
- LONG.DAT: a size of 100 on the chain F+5 to F+7;
- BROKEN.DAT: a size of 2048 on F+8, F+9, whose entry is 1, and F+10 to F+11 lost after them;
- FAT 2 only: the entry of the free cluster F+100 is 7;
- the FS info sector: a free count of 12345.
The 3 entries take the root's first free entries.
"""

import datetime
import os
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import mksd  # noqa: E402

SECTOR = 512
END = 0x0FFFFFFF
DATE = datetime.date(2026, 10, 13)


def card(image):
    folder = os.path.join(ROOT, "build", "tests", "CHKFIX")
    os.makedirs(folder, exist_ok=True)
    mksd.make(folder, image, date=DATE,
              extra=[os.path.join(ROOT, "build", "bas", "CMDSHELL.COM"),
                     os.path.join(ROOT, "build", "DOS")])
    with open(image, "r+b") as disk:
        def read(number):
            disk.seek(number * SECTOR)
            return bytearray(disk.read(SECTOR))

        def write(number, data):
            disk.seek(number * SECTOR)
            disk.write(data)

        start = struct.unpack_from("<I", read(0), 0x1C6)[0]
        boot = read(start)
        reserved = struct.unpack_from("<H", boot, 14)[0]
        fat_count = boot[16]
        fat_size, root = struct.unpack_from("<I4xI", boot, 0x24)
        info_number = start + struct.unpack_from("<H", boot, 0x30)[0]
        fat_start = start + reserved
        data_start = fat_start + fat_count * fat_size
        info = read(info_number)
        free = struct.unpack_from("<I", info, 492)[0]

        def set_entry(cluster, value, fats=range(fat_count)):
            for copy in fats:
                number = fat_start + copy * fat_size + cluster // 128
                sector = read(number)
                struct.pack_into("<I", sector, cluster % 128 * 4, value)
                write(number, sector)

        def chain(first, count):
            for cluster in range(first, first + count - 1):
                set_entry(cluster, cluster + 1)
            set_entry(first + count - 1, END)

        chain(free, 3)
        chain(free + 3, 2)
        chain(free + 5, 3)
        chain(free + 8, 4)
        set_entry(free + 9, 1)
        set_entry(free + 100, 7, fats=[1])
        struct.pack_into("<I", info, 488, 12345)
        write(info_number, info)

        time, date = mksd.dos_time(datetime.datetime.combine(DATE, datetime.time(12, 0)))
        files = [(b"SHORT   DAT", free + 3, 5000), (b"LONG    DAT", free + 5, 100),
                 (b"BROKEN  DAT", free + 8, 2048)]
        number = data_start + root - 2
        sector = read(number)
        place = 0
        for name, first, size in files:
            while sector[place] not in (0, 0xE5):
                place += 32
            sector[place:place + 32] = struct.pack(
                "<11sBBBHHHHHHHI", name, mksd.ATTR_ARCHIVE, 0, 0, time, date, date,
                first >> 16, time, date, first & 0xFFFF, size)
        write(number, sector)
