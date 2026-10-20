r"""Compile UXCBASIC sources with pyuxc, UXCBASIC's compiler in Python.

pyuxc lives in UXCBASIC/pyuxc. A compile writes NAME.PRG to build/uxc, and the program is
copied from there to where the caller asked, as NAME.COM. #INCLUDE looks in the source's folder
first, then lib, the folder of the libraries. pyuxc compiles for 6502DOS, with the template table
UXCBASIC/tpl/UXDOS/UXC.TPL.BIN.
"""

import glob
import os
import re
import shutil
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYUXC = os.path.join(ROOT, "UXCBASIC", "pyuxc")
TABLE = os.path.join(ROOT, "UXCBASIC", "tpl", "UXDOS", "UXC.TPL.BIN")
OUT = os.path.join(ROOT, "build", "uxc")
LIBRARY_FOLDER = os.path.join(ROOT, "lib")


def includes(source):
    """The files that source includes, as paths, each looked for as #INCLUDE does."""
    text = open(source, encoding="latin-1").read()
    names = re.findall(r'^\s*#INCLUDE\s+"([^"]+)"', text, re.IGNORECASE | re.MULTILINE)
    paths = []
    for name in names:
        for folder in (os.path.dirname(source), LIBRARY_FOLDER):
            path = os.path.join(folder, name)
            if os.path.exists(path):
                paths.append(path)
                break
    return paths


def compile(source, program):
    """Compile source to program when program is missing or older than source, than the template
    table, than a file that source includes or than a file of pyuxc. Print the time a compile
    took, and exit on a compile error."""
    inputs = [source, TABLE] + includes(source) + glob.glob(os.path.join(PYUXC, "*.py"))
    if os.path.exists(program) and all(os.path.getmtime(program) >= os.path.getmtime(i) for i in inputs):
        return
    if PYUXC not in sys.path:
        sys.path.insert(0, PYUXC)
    import pyuxc
    os.makedirs(OUT, exist_ok=True)
    took = time.time()
    result, screen = pyuxc.compile_file(source, [LIBRARY_FOLDER], OUT)
    fields = result.split(",")
    if fields[0] != "OK":
        sys.stdout.write("\n".join(screen) + "\n")
        sys.exit("%s did not compile: %s" % (os.path.basename(source), result))
    os.makedirs(os.path.dirname(program), exist_ok=True)
    shutil.copyfile(os.path.join(OUT, fields[1]), program)
    print("compiled %s, %.1f s" % (os.path.relpath(program, ROOT), time.time() - took))
