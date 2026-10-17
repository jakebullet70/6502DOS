"""Compile every corpus source with the GPC UXC, and keep what it wrote as the reference.

    python pyuxc/golden.py [NAME ...]

The corpus is tests/*.UXB, examples/*.UXB, samples/*.UXB, the UXDOS16 programs in
c:\\dev\\CmdrX16\\UXDOS16\\src\\bas, and the hand-made cases in pyuxc/cases. Each source NAME.UXB gives, in pyuxc/golden/:
    NAME.RESULT   the result line: OK,<prg>,<bytes> or ERROR,<line>,<message>
    NAME.PRG      the PRG, when the compile succeeded
TIMES.TXT gets one line per source: the name, the seconds and the result. NAMEs pick sources;
with none, every source is compiled. Build UXC first (build.py UXC). The GPC UXC is frozen, so
the reference is made once. golden/UXC.TPL.BIN and UXC.TPL.IDS are the template table it was
made with. compare.py imports corpus() and includes().
"""

import glob
import os
import shutil
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from uxc import DRIVE, compile_source  # noqa: E402

UXDOS16_BAS = r"c:\dev\CmdrX16\UXDOS16\src\bas"
GOLDEN = os.path.join(HERE, "golden")
CASES = os.path.join(HERE, "cases")
SECONDS = 120


def corpus():
    """Every corpus source, sorted by name within its folder."""
    sources = []
    for folder in ("tests", "examples", "samples"):
        sources += sorted(glob.glob(os.path.join(ROOT, folder, "*.UXB")))
    sources += sorted(glob.glob(os.path.join(UXDOS16_BAS, "*.UXB")))
    sources += sorted(glob.glob(os.path.join(CASES, "*.UXB")))
    return sources


def includes():
    """Every include file a corpus source may name, from tests/, UXDOS16 and cases/."""
    return (glob.glob(os.path.join(ROOT, "tests", "*.UXI")) +
            glob.glob(os.path.join(UXDOS16_BAS, "stock", "*.UXI")) +
            glob.glob(os.path.join(CASES, "*.UXI")))


def main():
    names = [a.upper() for a in sys.argv[1:]]
    if not os.path.exists(os.path.join(DRIVE, "UXC.PRG")):
        sys.exit("golden: no build/UXC.PRG; run build.py UXC first")
    sources = corpus()
    stems = [os.path.splitext(os.path.basename(s))[0].upper() for s in sources]
    if len(set(stems)) != len(stems):
        sys.exit("golden: two corpus sources share a name")
    if names:
        sources = [s for s in sources if os.path.splitext(os.path.basename(s))[0].upper() in names]
    os.makedirs(GOLDEN, exist_ok=True)
    for include in includes():
        shutil.copyfile(include, os.path.join(DRIVE, os.path.basename(include).upper()))
    started = time.time()
    with open(os.path.join(GOLDEN, "TIMES.TXT"), "a", encoding="utf-8", newline="\n") as times:
        for source in sources:
            stem = os.path.splitext(os.path.basename(source))[0].upper()
            took = time.time()
            result, screen = compile_source(source, SECONDS)
            took = time.time() - took
            if result is None:
                result = "NO RESULT"
            with open(os.path.join(GOLDEN, stem + ".RESULT"), "w", encoding="latin-1",
                      newline="\n") as out:
                out.write(result + "\n")
            fields = result.split(",")
            if fields[0] == "OK":
                shutil.copyfile(os.path.join(DRIVE, fields[1]), os.path.join(GOLDEN, stem + ".PRG"))
            line = "%-12s %5.1f s  %s" % (stem, took, result)
            print(line, flush=True)
            times.write(line + "\n")
    print("%d sources, %d s" % (len(sources), time.time() - started))


if __name__ == "__main__":
    main()
