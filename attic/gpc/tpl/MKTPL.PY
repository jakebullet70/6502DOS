"""Build UXC.TPL.BIN, the template table, with 64tass: one for the stock ROM, one for UXDOS16.

    python tpl/MKTPL.PY            assemble, check every record, write the ids, print the table
    python tpl/MKTPL.PY --test     also link a test program from the stock table and run it

Writes, beside this script, the stock ROM's table (64tass -D UXDOS=0):
    UXC.TPL.BIN     the table the compiler loads (tpl/MACROS.ASM describes the format)
    UXC.TPL.LST     the 64tass listing
    UXC.TPL.IDS     one line per record: NAME = id
    UXC.TPL.BL      the same ids as BASLOAD #DEFINEs, for the compiler: T_LDW_C is T.LDW.C.ID

and in tpl/UXDOS the UXDOS16 table (64tass -D UXDOS=1): UXC.TPL.BIN and UXC.TPL.LST. Its records
must have the ids of the stock table; MKTPL stops when they do not.

--test is a small host-side linker. It builds build/TPLTEST.PRG from records the way the
compiler will, runs it headless in the emulator and compares the screen output. It proves the
format and the fixups before the compiler exists.
"""

import os
import re
import struct
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TASS = os.environ.get("TASS", r"C:\8bitProgramming\64tass-1.60\64tass.exe")
BIN = os.path.join(HERE, "UXC.TPL.BIN")
LST = os.path.join(HERE, "UXC.TPL.LST")
IDS = os.path.join(HERE, "UXC.TPL.IDS")
DEFS = os.path.join(HERE, "UXC.TPL.BL")
UXDOS_DIR = os.path.join(HERE, "UXDOS")

F_ABS, F_LO, F_HI, F_SELF, F_REC = 1, 2, 3, 4, 5
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
        records.append((code, [tuple(fix[j:j + 3]) for j in range(0, len(fix), 3)]))
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
        moved = ["%d: %s, UXDOS16 %s" % (i, a, b) for i, (a, b) in enumerate(zip(ids, uxdos_ids))
                 if a != b]
        sys.exit("MKTPL: the UXDOS16 table's ids differ (%d and %d records)\n  %s"
                 % (len(ids), len(uxdos_ids), "\n  ".join(moved)))
    print("MKTPL: UXDOS16 table, %d records, %d bytes" % (len(uxdos_records), uxdos_size))
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


class Linker:
    """The compiler's link step, on the host. A program is a list of (template, slots)."""

    def __init__(self, records, ids):
        self.records, self.ids = records, ids

    def link(self, program, strings, variables, org=0x0801):
        # The code: every template in order, then every record they reach, once each.
        used, todo = [], []
        for name, _ in program:
            todo.append(self.ids[name])
        while todo:
            rid = todo.pop(0)
            for _, kind, arg in self.records[rid][1]:
                if kind == F_REC and arg not in used:
                    used.append(arg)
                    todo.append(arg)
        addr = org
        places = []
        for name, slots in program:
            places.append((addr, self.ids[name], slots))
            addr += len(self.records[self.ids[name]][0])
        routine = {}
        for rid in used:
            routine[rid] = addr
            addr += len(self.records[rid][0])
        # The data: string literals ([max][len][data], max = len), then the variables.
        symbol = {}
        data = bytearray()
        for name, text in strings.items():
            symbol[name] = addr + len(data)
            data += bytes([len(text), len(text)]) + text.encode("ascii")
        for name, size in variables.items():
            symbol[name] = addr + len(data)
            data += bytes(size)
        # Copy each record and apply its fixups.
        out = bytearray()
        placed = [(a, r, s) for a, r, s in places] + [(routine[r], r, {}) for r in used]
        for at, rid, slots in placed:
            code, fixups = self.records[rid]
            code = bytearray(code)
            value = [symbol.get(v, v) for v in slots] if isinstance(slots, list) else []
            for off, kind, arg in fixups:
                word = code[off] | (code[off + 1] << 8 if off + 1 < len(code) else 0)
                if kind == F_ABS:
                    struct.pack_into("<H", code, off, (word + value[arg]) & 0xFFFF)
                elif kind == F_LO:
                    code[off] = value[arg] & 0xFF
                elif kind == F_HI:
                    code[off] = value[arg] >> 8
                elif kind == F_SELF:
                    struct.pack_into("<H", code, off, (word + at) & 0xFFFF)
                elif kind == F_REC:
                    struct.pack_into("<H", code, off, (word + routine[arg]) & 0xFFFF)
            out += code
        return struct.pack("<H", org) + bytes(out) + bytes(data)


def test(records, ids):
    """Link and run the test program:

        DIM N%, B
        N% = 12345
        B = 7
        PRINT "HELLO, UXC"
        PRINT N%
        POKE @B, 42
        PRINT B
        PRINT 0
        PRINT 65535; " END"
        END
    """
    program = [
        ("T_STUB", None),
        ("T_START", None),
        ("T_LDW_C", [12345]), ("T_STW_V", ["N"]),
        ("T_LDB_C", [7]), ("T_STB_V", ["B"]),
        ("T_LDW_C", ["S1"]), ("T_PRSTR", None), ("T_PRNL", None),
        ("T_LDW_V", ["N"]), ("T_PRWORD", None), ("T_PRNL", None),
        ("T_LDW_C", ["B"]), ("T_PUSH", None), ("T_LDB_C", [42]), ("T_POKE", None),
        ("T_LDB_V", ["B"]), ("T_PRBYTE", None), ("T_PRNL", None),
        ("T_LDW_C", [0]), ("T_PRWORD", None), ("T_PRNL", None),
        ("T_LDW_C", [65535]), ("T_PRWORD", None),
        ("T_LDW_C", ["S2"]), ("T_PRSTR", None), ("T_PRNL", None),
        ("T_END", None),
    ]
    prg = Linker(records, ids).link(program, {"S1": "HELLO, UXC", "S2": " END"}, {"N": 2, "B": 1})
    drive = os.path.join(ROOT, "build")
    os.makedirs(drive, exist_ok=True)
    open(os.path.join(drive, "TPLTEST.PRG"), "wb").write(prg)
    print("MKTPL: build/TPLTEST.PRG %d bytes" % len(prg))
    run = subprocess.run([sys.executable, os.path.join(ROOT, "run.py"), "TPLTEST", "--seconds", "4"],
                         capture_output=True, text=True)
    want = ["HELLO, UXC", "12345", "42", "0", "65535  END"]
    got = [l.replace("\\X0F", "").strip() for l in run.stdout.split("\n")]
    start = got.index(want[0]) if want[0] in got else -1
    if start < 0 or got[start:start + len(want)] != want:
        print(run.stdout)
        sys.exit("MKTPL: TPLTEST output is wrong")
    print("MKTPL: TPLTEST OK -- " + " | ".join(want))


def test_expr(records, ids):
    """Link and run build/TPLEXPR.PRG: each operator on constants, one line per group, then a
    division by zero, which must stop the program with the address of the T_DIV's JSR."""

    def const(value, word):
        return ("T_LDW_C" if word else "T_LDB_C", [value])

    def binop(left, right, word, *ops):
        # left op right; a compare is a core then a tail.
        return [const(left, word), ("T_PUSH" if word else "T_PUSHB", None), const(right, word)] + \
               [(op, None) for op in ops]

    def show(code, word):
        return code + [("T_PRWORD" if word else "T_PRBYTE", None)]

    W, B = True, False
    lines = [
        # * / MOD: 1234*56 wraps to 3568; 60000/7 = 8571 r 3; 50000/300 = 166 r 200
        ([(binop(1234, 56, W, "T_MUL"), W), (binop(60000, 7, W, "T_DIV"), W),
          (binop(60000, 7, W, "T_MOD"), W), (binop(50000, 300, W, "T_DIV"), W),
          (binop(50000, 300, W, "T_MOD"), W), (binop(40000, 40001, W, "T_DIV"), W),
          (binop(65535, 1, W, "T_DIV"), W)],
         [3568, 8571, 3, 166, 200, 0, 65535]),
        # + -: BYTE wraps at 256, WORD at 65536
        ([(binop(200, 100, B, "T_ADDB"), B), (binop(100, 200, B, "T_SUBB"), B),
          (binop(1000, 2000, W, "T_SUBW"), W), (binop(65000, 1000, W, "T_ADDW"), W),
          (binop(300, 45, W, "T_ADDW"), W)],
         [44, 156, 64536, 464, 345]),
        # AND OR XOR, shifts
        ([(binop(0xF0, 0x3C, B, "T_ANDB"), B), (binop(0x1234, 0xFF0F, W, "T_ORW"), W),
          (binop(0x1234, 0x00FF, W, "T_XORW"), W), (binop(1, 15, W, "T_SHLW"), W),
          (binop(40000, 3, W, "T_SHRW"), W), (binop(0x81, 1, B, "T_SHLB"), B),
          (binop(0x81, 0, B, "T_SHRB"), B)],
         [0x30, 0xFF3F, 0x12CB, 32768, 5000, 2, 0x81]),
        # compares, WORD: 300<301 300>=301 256=0 256<>0 5<=5 7>3 3>7
        ([(binop(300, 301, W, "T_CMPW_LR", "T_CFALSE"), B),
          (binop(300, 301, W, "T_CMPW_LR", "T_CTRUE"), B),
          (binop(256, 0, W, "T_CMPW_EQ", "T_ZTRUE"), B),
          (binop(256, 0, W, "T_CMPW_EQ", "T_ZFALSE"), B),
          (binop(5, 5, W, "T_CMPW_RL", "T_CTRUE"), B),
          (binop(7, 3, W, "T_CMPW_RL", "T_CFALSE"), B),
          (binop(3, 7, W, "T_CMPW_RL", "T_CFALSE"), B)],
         [1, 0, 0, 1, 1, 1, 0]),
        # compares, BYTE: 9<10 9>=10 4=4 4<>4 200<=100 200>100
        ([(binop(9, 10, B, "T_CMPB_LR", "T_CFALSE"), B),
          (binop(9, 10, B, "T_CMPB_LR", "T_CTRUE"), B),
          (binop(4, 4, B, "T_CMPB_RL", "T_ZTRUE"), B),
          (binop(4, 4, B, "T_CMPB_RL", "T_ZFALSE"), B),
          (binop(200, 100, B, "T_CMPB_RL", "T_CTRUE"), B),
          (binop(200, 100, B, "T_CMPB_RL", "T_CFALSE"), B)],
         [1, 0, 1, 0, 0, 1]),
        # unary: -1 (WORD), -1 (BYTE), NOT 0, NOT 7, NOT 256 (WORD), NOT 0 (WORD)
        ([([const(1, W), ("T_NEGW", None)], W), ([const(1, B), ("T_NEGB", None)], B),
          ([const(0, B), ("T_NOTB", None)], B), ([const(7, B), ("T_NOTB", None)], B),
          ([const(256, W), ("T_NOTW", None)], B), ([const(0, W), ("T_NOTW", None)], B)],
         [65535, 255, 1, 0, 0, 1]),
    ]
    program = [("T_STUB", None), ("T_START", None)]
    want = []
    for items, values in lines:
        for code, word in items:
            program += show(code, word)
        program.append(("T_PRNL", None))
        want.append("  ".join(str(v) for v in values))
    # The stack must be empty again: push a marker, run everything, pop it here. A template
    # that loses its balance shows up as a wrong marker.
    program[2:2] = [const(0xBEEF, W), ("T_PUSH", None)]
    program += [const(0, W), ("T_ADDW", None), ("T_PRWORD", None)]
    want.append(str(0xBEEF))
    program += binop(10, 0, W)
    site = 0x0801 + sum(len(records[ids[n]][0]) for n, _ in program)
    program += [("T_DIV", None), ("T_PRWORD", None), ("T_END", None)]
    want += ["?DIVISION BY ZERO ERROR AT $%04X" % site]
    prg = Linker(records, ids).link(program, {}, {})
    open(os.path.join(ROOT, "build", "TPLEXPR.PRG"), "wb").write(prg)
    print("MKTPL: build/TPLEXPR.PRG %d bytes" % len(prg))
    run = subprocess.run([sys.executable, os.path.join(ROOT, "run.py"), "TPLEXPR", "--seconds", "4"],
                         capture_output=True, text=True)
    got = [l.replace("\\X0F", "").strip() for l in run.stdout.split("\n")]
    start = got.index(want[0]) if want[0] in got else -1
    if start < 0 or got[start:start + len(want)] != want:
        print(run.stdout)
        print("want:\n  " + "\n  ".join(want))
        sys.exit("MKTPL: TPLEXPR output is wrong")
    print("MKTPL: TPLEXPR OK -- %d lines" % len(want))


def main():
    records, ids = build()
    if "--test" in sys.argv:
        test(records, ids)
        test_expr(records, ids)


main()
