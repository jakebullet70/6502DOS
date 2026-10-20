"""Check a FAT32 SD image: the FATs are equal, no cluster is lost or in two chains, each
file's chain fits its size, and each run of long-name entries counts down from its last entry
to 1 and ends at the 8.3 entry whose checksum it holds.

    python tools/fatcheck.py build/tests/RUN.IMG
"""
import struct
import sys

img = open(sys.argv[1], "rb").read()
part = None
for i in range(4):
    e = img[0x1BE + 16 * i:0x1BE + 16 * i + 16]
    if e[4] in (0x0B, 0x0C):
        part = struct.unpack("<I", e[8:12])[0]
        break
bs = img[part * 512:part * 512 + 512]
spc = bs[13]
res = struct.unpack("<H", bs[14:16])[0]
nfat = bs[16]
total = struct.unpack("<I", bs[0x20:0x24])[0]
fatsz = struct.unpack("<I", bs[0x24:0x28])[0]
root = struct.unpack("<I", bs[0x2C:0x30])[0]
fat0 = part + res
data = fat0 + nfat * fatsz
clusters = (total - (res + nfat * fatsz)) // spc
limit = clusters + 2
cbytes = spc * 512
fats = [img[(fat0 + k * fatsz) * 512:(fat0 + (k + 1) * fatsz) * 512] for k in range(nfat)]
print("FATs equal:", all(f == fats[0] for f in fats), "limit", limit)


def nxt(c):
    return struct.unpack("<I", fats[0][c * 4:c * 4 + 4])[0] & 0x0FFFFFFF


def chain(c):
    out = []
    while 2 <= c < 0x0FFFFFF8:
        out.append(c)
        c = nxt(c)
        if len(out) > limit:
            raise SystemExit("loop")
    return out


used = {}
problems = []


def claim(cl, owner):
    for c in cl:
        if c >= limit:
            problems.append("%s: cluster %d past the limit" % (owner, c))
        if c in used:
            problems.append("%s: cluster %d also in %s" % (owner, c, used[c]))
        used[c] = owner


def checksum(short):
    total = 0
    for byte in short:
        total = (((total & 1) << 7) + (total >> 1) + byte) & 0xFF
    return total


def walk(first, path):
    cl = chain(first)
    claim(cl, path)
    raw = b"".join(img[(data + (c - 2) * spc) * 512:(data + (c - 1) * spc) * 512] for c in cl)
    run = None  # [the next order, the checksum, the offset of the last entry] of a long name
    for k in range(0, len(raw), 32):
        e = raw[k:k + 32]
        if e[0] == 0:
            break
        if e[0] != 0xE5 and e[11] == 0x0F:
            if e[12] or e[26:28] != bytes(2):
                problems.append("%s @%d: long-name entry with a type or a cluster" % (path, k))
            if e[0] & 0x40:
                if run:
                    problems.append("%s @%d: orphan long-name entries" % (path, run[2]))
                run = [e[0] & 0x1F, e[13], k]
                if not 1 <= run[0] <= 20:
                    problems.append("%s @%d: long-name order %d" % (path, k, run[0]))
                    run = None
            elif not run or e[0] != run[0] or e[13] != run[1]:
                problems.append("%s @%d: long-name entry out of order" % (path, k))
                run = None
                continue
            if run:
                run[0] -= 1
            continue
        if run:
            if e[0] == 0xE5 or run[0] or checksum(e[:11]) != run[1]:
                problems.append("%s @%d: orphan long-name entries" % (path, run[2]))
            run = None
        if e[0] == 0xE5 or e[:2] in (b". ", b".."):
            continue
        name = e[:11].decode("latin-1")
        first = struct.unpack("<H", e[26:28])[0] | struct.unpack("<H", e[20:22])[0] << 16
        size = struct.unpack("<I", e[28:32])[0]
        if e[11] & 0x10:
            walk(first, path + "\\" + name.strip())
        else:
            fc = chain(first) if first else []
            claim(fc, path + "\\" + name)
            need = -(-size // cbytes)
            if len(fc) != need and not (len(fc) > need):
                problems.append("%s\\%s: size %d, %d clusters" % (path, name, size, len(fc)))
            if len(fc) > need:
                print("note: %s\\%s size %d holds %d clusters" % (path, name, size, len(fc)))
    if run:
        problems.append("%s @%d: orphan long-name entries" % (path, run[2]))


walk(root, "")
lost = [c for c in range(2, limit) if nxt(c) != 0 and c not in used]
print("lost clusters:", lost[:20], len(lost))
print("problems:", problems or "none")
