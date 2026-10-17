"""Compile the corpus with pyuxc and compare each result with golden/.

    python pyuxc/compare.py [--all] [NAME ...]

Each source gets one line:
    MATCH         the result line and the PRG are the same as golden/
    RESULT        the result lines differ; both are shown
    PRG           the PRGs differ; the first byte that differs is shown, and both lengths
    NOT PORTED    the compile reached a GPC routine that pyuxc does not have yet
    CRASH         pyuxc raised a Python exception; with one NAME the traceback is shown
    NO GOLDEN     golden/ has no result for the source, which is newer than the reference

Only the lines other than MATCH, NOT PORTED and NO GOLDEN are printed, unless --all is given. The last
line counts each kind. NAMEs pick sources. The PRGs go into pyuxc/out/.
"""

import os
import struct
import sys
import time
import traceback

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import golden  # noqa: E402
import pyuxc  # noqa: E402
import uxc_tpl  # noqa: E402
from uxc_state import NotPorted  # noqa: E402

OUT = os.path.join(HERE, "out")
FIXUP_RECORD = 5                # a fixup kind: the address of another record, MKTPL's F_REC
INCLUDE_FOLDERS = [os.path.join(golden.ROOT, "tests"), os.path.join(golden.UXDOS16_BAS, "stock")]


def read(path, mode="rb"):
    with open(path, mode) as f:
        return f.read()


def table_records(folder):
    """{record name: (code, fixups)} of UXC.TPL.BIN in folder, named by UXC.TPL.IDS beside
    it. A record fixup holds the name of its target, so a record compares equal when the ids
    move."""
    data = read(os.path.join(folder, "UXC.TPL.BIN"))
    names = {}
    with open(os.path.join(folder, "UXC.TPL.IDS"), encoding="utf-8") as lines:
        for line in lines:
            name, _, rid = line.partition("=")
            names[int(rid)] = name.strip()
    count, index = struct.unpack_from("<HH", data, 4)
    records = {}
    for rid in range(count):
        at = struct.unpack_from("<H", data, index + 2 * rid)[0]
        length = data[at]
        fixup_count = data[at + 1]
        fixups = data[at + 2 + length:at + 2 + length + 3 * fixup_count]
        named = []
        for j in range(0, len(fixups), 3):
            offset, kind, target = fixups[j:j + 3]
            if kind == FIXUP_RECORD:
                target = names[target]
            named.append((offset, kind, target))
        records[names[rid]] = (data[at + 2:at + 2 + length], named)
    return records


def first_difference(want, got):
    """The first byte where two PRGs differ, as text."""
    at = next((i for i in range(min(len(want), len(got))) if want[i] != got[i]),
              min(len(want), len(got)))
    where = "byte %d" % at
    if at >= 2 and len(want) >= 2:
        where = "$%04X (byte %d)" % (want[0] + 256 * want[1] + at - 2, at)
    w = "$%02X" % want[at] if at < len(want) else "end"
    o = "$%02X" % got[at] if at < len(got) else "end"
    return "%s: want %s got %s; length want %d got %d" % (where, w, o, len(want), len(got))


def compare(source, show_traceback):
    """Return (kind, detail) for one source."""
    stem = os.path.splitext(os.path.basename(source))[0].upper()
    if not os.path.exists(os.path.join(golden.GOLDEN, stem + ".RESULT")):
        return "NO GOLDEN", ""
    want = read(os.path.join(golden.GOLDEN, stem + ".RESULT")).decode("latin-1").strip()
    prg = os.path.join(OUT, pyuxc.object_name(source))
    if os.path.exists(prg):
        os.remove(prg)
    try:
        got, _ = pyuxc.compile_file(source, INCLUDE_FOLDERS, OUT, "stock", keep_subs=True,
                                     keep_vars=True)
    except NotPorted as missing:
        return "NOT PORTED", str(missing)
    except Exception as crash:
        if show_traceback:
            traceback.print_exc()
        frame = traceback.extract_tb(crash.__traceback__)[-1]
        return "CRASH", "%s: %s (%s:%d)" % (type(crash).__name__, crash,
                                            os.path.basename(frame.filename), frame.lineno)
    if got != want:
        return "RESULT", "want %s  got %s" % (want, got)
    if not want.startswith("OK,"):
        return "MATCH", ""
    if not os.path.exists(prg):
        return "PRG", "pyuxc wrote no " + os.path.basename(prg)
    want_prg = read(os.path.join(golden.GOLDEN, stem + ".PRG"))
    got_prg = read(prg)
    if got_prg != want_prg:
        return "PRG", first_difference(want_prg, got_prg)
    return "MATCH", ""


def main():
    args = sys.argv[1:]
    show_all = "--all" in args
    names = [a.upper() for a in args if not a.startswith("--")]
    golden_records = table_records(golden.GOLDEN)
    records = table_records(uxc_tpl.DIR)
    changed = [name for name in golden_records if records.get(name) != golden_records[name]]
    if changed:
        print("compare: these records of tpl/UXC.TPL.BIN differ from the table golden/ was "
              "made with: " + " ".join(changed))
    os.makedirs(OUT, exist_ok=True)
    sources = golden.corpus()
    if names:
        sources = [s for s in sources if os.path.splitext(os.path.basename(s))[0].upper() in names]
    started = time.time()
    counts, missing = {}, {}
    for source in sources:
        kind, detail = compare(source, len(sources) == 1)
        counts[kind] = counts.get(kind, 0) + 1
        if kind == "NOT PORTED":
            missing[detail] = missing.get(detail, 0) + 1
        if show_all or kind not in ("MATCH", "NOT PORTED", "NO GOLDEN"):
            stem = os.path.splitext(os.path.basename(source))[0].upper()
            print("%-12s %-10s %s" % (stem, kind, detail))
    kinds = ("MATCH", "RESULT", "PRG", "NOT PORTED", "CRASH", "NO GOLDEN")
    print("%d sources: %s; %.1f s" % (len(sources), ", ".join("%d %s" % (counts.get(k, 0), k)
                                                               for k in kinds), time.time() - started))
    for routine in sorted(missing):
        print("  not ported: %s, %d sources" % (routine, missing[routine]))
    sys.exit(0 if counts.get("MATCH", 0) + counts.get("NO GOLDEN", 0) == len(sources) else 1)


if __name__ == "__main__":
    main()
