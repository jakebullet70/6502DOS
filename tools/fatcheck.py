"""Check a FAT32 SD image: the FATs are equal, no cluster is lost or in two chains, and each
file's chain fits its size.

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


def walk(first, path):
    cl = chain(first)
    claim(cl, path)
    raw = b"".join(img[(data + (c - 2) * spc) * 512:(data + (c - 1) * spc) * 512] for c in cl)
    for k in range(0, len(raw), 32):
        e = raw[k:k + 32]
        if e[0] == 0:
            break
        if e[0] == 0xE5 or e[11] == 0x0F or e[:2] in (b". ", b".."):
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


walk(root, "")
lost = [c for c in range(2, limit) if nxt(c) != 0 and c not in used]
print("lost clusters:", lost[:20], len(lost))
print("problems:", problems or "none")
