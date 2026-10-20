"""Build UXC.TPL.BIN, the template table, with 64tass: one for the stock ROM, one for 6502DOS.

    python UXCBASIC/tpl/MKTPL.PY    assemble, check every record, write the ids, print the table

Writes, beside this script, the stock ROM's table (64tass -D UXDOS=0):
    UXC.TPL.BIN     the table the compiler loads (tpl/MACROS.ASM describes the format)
    UXC.TPL.LST     the 64tass listing
    UXC.TPL.IDS     one line per record: NAME = id
    UXC.TPL.BL      the same ids as BASLOAD #DEFINEs, for the compiler: T_LDW_C is T.LDW.C.ID

and in tpl/UXDOS the 6502DOS table (64tass -D UXDOS=1): UXC.TPL.BIN and UXC.TPL.LST. Its records
must have the ids of the stock table; MKTPL stops when they do not. 64tass is
tools/64tass/64tass.exe of the 6502DOS folder, or the file in TASS.
"""

import os
import re
import struct
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
TASS = os.environ.get("TASS", os.path.join(REPO, "tools", "64tass", "64tass.exe"))
BIN = os.path.join(HERE, "UXC.TPL.BIN")
LST = os.path.join(HERE, "UXC.TPL.LST")
IDS = os.path.join(HERE, "UXC.TPL.IDS")
DEFS = os.path.join(HERE, "UXC.TPL.BL")
UXDOS_DIR = os.path.join(HERE, "UXDOS")

F_ABS, F_LO, F_HI, F_SELF, F_REC, F_REC_HI = 1, 2, 3, 4, 5, 6
KINDS = {F_ABS: "ABS", F_LO: "LO", F_HI: "HI", F_SELF: "SELF", F_REC: "REC"}


def assemble(uxdos=0, binary=BIN, listing=LST):
    """Run 64tass. Return {record name: file offset} from its label list."""
    labels = os.path.join(HERE, "UXC.TPL.LBL")
    cmd = [TASS, "-Wall", "-q", "--nostart", "-D", "UXDOS=%d" % uxdos, "-o", binary, "-L",
           listing, "-l", labels, os.path.join(HERE, "UXC.TPL.ASM")]
    if subprocess.run(cmd, cwd=HERE).returncode != 0:
        sys.exit("MKTPL: 64tass failed")
    names = {}
    for line in open(labels):
        m = re.match(r"([TRS]_\w+)\s*=\s*(\d+)\s*$", line)
        if m:
            names[m.group(1)] = int(m.group(2))
    os.remove(labels)
    return names


def load(data):
    """Read a table. Return a list of records: (code bytes, [(offset, kind, arg)])."""
    if data[:3] != b"UXT" or data[3] != 1:
        sys.exit("MKTPL: not a version 1 UXT table")
    count, index = struct.unpack_from("<HH", data, 4)
    records = []
    for i in range(count):
        at = struct.unpack_from("<H", data, index + 2 * i)[0]
        length, nfix = data[at], data[at + 1]
        code = data[at + 2:at + 2 + length]
        fix = data[at + 2 + length:at + 2 + length + 3 * nfix]
        fixups = [tuple(fix[j:j + 3]) for j in range(0, len(fix), 3)]
        # F_REC_HI is F_REC of record <arg> + 256.
        records.append((code, [(o, F_REC, a + 256) if k == F_REC_HI else (o, k, a)
                               for o, k, a in fixups]))
    return records


def check(records, ids):
    """Stop on a fixup that points outside its record or names something that is not there."""
    bad = []
    for rid, (code, fixups) in enumerate(records):
        for off, kind, arg in fixups:
            size = 1 if kind in (F_LO, F_HI) else 2
            if kind not in KINDS or off + size > len(code) or (kind == F_REC and arg >= len(records)):
                bad.append("%s: fixup (%d, %d, %d)" % (ids[rid], off, kind, arg))
    if bad:
        sys.exit("MKTPL: bad fixups\n  " + "\n  ".join(bad))


def table(uxdos, binary, listing):
    """Assemble one table and check it. Return its records, their names in id order, and its
    size."""
    names = assemble(uxdos, binary, listing)
    data = open(binary, "rb").read()
    records = load(data)
    count, index = struct.unpack_from("<HH", data, 4)
    offsets = [struct.unpack_from("<H", data, index + 2 * i)[0] for i in range(count)]
    by_offset = {v: k for k, v in names.items()}
    ids = [by_offset.get(o, "?%d" % i) for i, o in enumerate(offsets)]
    check(records, ids)
    return records, ids, len(data)


def build():
    records, ids, size = table(0, BIN, LST)
    with open(IDS, "w", newline="\n") as out:
        for rid, name in enumerate(ids):
            out.write("%s = %d\n" % (name, rid))
    write_defines(ids)
    for rid, (code, fixups) in enumerate(records):
        fx = " ".join("%s%s@%d" % (KINDS[k], "" if k == F_SELF else
                      (":" + ids[a] if k == F_REC else ":S%d" % a), o) for o, k, a in fixups)
        print("  %3d %-10s %3d  %s" % (rid, ids[rid], len(code), fx))
    print("MKTPL: %d records, %d bytes" % (len(records), size))
    uxdos_records, uxdos_ids, uxdos_size = table(1, os.path.join(UXDOS_DIR, "UXC.TPL.BIN"),
                                                 os.path.join(UXDOS_DIR, "UXC.TPL.LST"))
    if uxdos_ids != ids:
        moved = ["%d: %s, 6502DOS %s" % (i, a, b) for i, (a, b) in enumerate(zip(ids, uxdos_ids))
                 if a != b]
        sys.exit("MKTPL: the 6502DOS table's ids differ (%d and %d records)\n  %s"
                 % (len(ids), len(uxdos_ids), "\n  ".join(moved)))
    print("MKTPL: 6502DOS table, %d records, %d bytes" % (len(uxdos_records), uxdos_size))
    return records, {n: i for i, n in enumerate(ids)}


def write_defines(ids):
    """Write UXC.TPL.BL. BASLOAD refuses a digit in a #DEFINE name, and replaces a name where
    it begins a longer one, so both are stopped here."""
    names = ["TPL.COUNT"] + [n.replace("_", ".") + ".ID" for n in ids]
    bad = [n for n in names if re.search(r"\d", n)]
    bad += ["%s begins %s" % (a, b) for a in names for b in names if a != b and b.startswith(a)]
    if bad:
        sys.exit("MKTPL: names BASLOAD cannot #DEFINE\n  " + "\n  ".join(bad))
    with open(DEFS, "w", newline="\n") as out:
        out.write("## UXC.TPL.BL -- written by tpl/MKTPL.PY, do not edit. The id of each record in\n"
                  "## UXC.TPL.BIN. The compiler checks TPL.COUNT against the table it loads.\n")
        out.write("#DEFINE TPL.COUNT %d\n" % len(ids))
        for rid, name in enumerate(names[1:]):
            out.write("#DEFINE %s %d\n" % (name, rid))


build()
