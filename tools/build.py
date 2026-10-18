r"""Build the UXDOS16 ROM image.

    python tools/build.py

Runs tools/genapi.py, assembles every src/asm/*.s and build/gen/*.s with ca65, links them
with src/asm/rom.cfg into build/UXDOS16.ROM, and copies LICENSE and NOTICE beside it. ca65 and
ld65 come from tools/cc65/bin only. Includes are found in src/asm and build/gen. The map is
build/UXDOS16.MAP, the label file build/UXDOS16.LBL, and each listing build/obj/NAME.LST.
build/TEST.ROM is the same image with boot_shell cleared: it boots to the monitor, not the shell.

UXCBASIC/tpl/MKTPL.PY rebuilds the template tables when a UXCBASIC/tpl or UXCBASIC/tpl/UXDOS
.ASM file is newer than UXCBASIC/tpl/UXDOS/UXC.TPL.BIN. Each src/bas/NAME.UXB compiles to
build/bas/NAME.COM with tools/uxb.py when the COM file is older than the source, than a file it
includes, than the template table or than pyuxc. Each src/cbin/NAME.UXB, a
commandlet, compiles the same way to build/DOS/NAME.CBI. The kernel keeps 3 characters of an
extension, so NAME.CBIN opens NAME.CBI. Each src/dos/NAME.UXB, a DOS utility, compiles to
build/DOS/NAME.COM, and each src/dos/NAME.TXT and NAME.HLP is copied to build/DOS.

Then tools/mksd.py makes the SD card image build/SD.IMG from the folder sd, the COM files in
build/bas, the folder build/DOS, which is the card's folder DOS, and the files and folders of the
test card's folder tests/sd. Exit status 1 when a tool or a compile failed or api.py is inconsistent.
"""

import glob
import os
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import genapi  # noqa: E402
import mksd  # noqa: E402
import uxb  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CC65 = os.path.join(ROOT, "tools", "cc65", "bin")
CA65 = os.path.join(CC65, "ca65.exe")
LD65 = os.path.join(CC65, "ld65.exe")
ASM = os.path.join(ROOT, "src", "asm")
BUILD = os.path.join(ROOT, "build")
OBJ = os.path.join(BUILD, "obj")
GEN = os.path.join(BUILD, "gen")
ROM = os.path.join(BUILD, "UXDOS16.ROM")
TEST_ROM = os.path.join(BUILD, "TEST.ROM")
LABELS = os.path.join(BUILD, "UXDOS16.LBL")
BANK0_START = 0xC000
SD_FOLDER = os.path.join(ROOT, "sd")
TEST_SD_FOLDER = os.path.join(ROOT, "tests", "sd")
SD_IMAGE = os.path.join(BUILD, "SD.IMG")
BAS = os.path.join(ROOT, "src", "bas")
BAS_OUT = os.path.join(BUILD, "bas")
CBIN = os.path.join(ROOT, "src", "cbin")
CBIN_OUT = os.path.join(BUILD, "DOS")
UTILITIES = os.path.join(ROOT, "src", "dos")
TEMPLATES = os.path.join(ROOT, "UXCBASIC", "tpl")


def run(command):
    result = subprocess.run(command, capture_output=True, text=True)
    sys.stdout.write(result.stdout + result.stderr)
    if result.returncode != 0:
        sys.exit("build: %s failed" % os.path.basename(command[0]))


def make_templates():
    """Run MKTPL.PY when a template source is newer than the UXDOS16 table. Print its last line,
    or all of its output when it failed."""
    sources = (glob.glob(os.path.join(TEMPLATES, "*.ASM"))
               + glob.glob(os.path.join(TEMPLATES, "UXDOS", "*.ASM")))
    if os.path.exists(uxb.TABLE) and all(os.path.getmtime(uxb.TABLE) >= os.path.getmtime(s)
                                         for s in sources):
        return
    result = subprocess.run([sys.executable, os.path.join(TEMPLATES, "MKTPL.PY")],
                            capture_output=True, text=True)
    if result.returncode != 0:
        sys.stdout.write(result.stdout + result.stderr)
        sys.exit("build: MKTPL.PY failed")
    sys.stdout.write(result.stdout.strip().split("\n")[-1] + "\n")


def compile_bas():
    """Compile each src/bas/NAME.UXB whose COM file is missing or older. Return the COM paths."""
    os.makedirs(BAS_OUT, exist_ok=True)
    programs = []
    for source in sorted(glob.glob(os.path.join(BAS, "*.UXB"))):
        name = os.path.splitext(os.path.basename(source))[0].upper() + ".COM"
        uxb.compile(source, os.path.join(BAS_OUT, name))
        programs.append(os.path.join(BAS_OUT, name))
    return programs


def compile_cbin():
    """Compile each src/cbin/NAME.UXB to build/DOS/NAME.CBI and each src/dos/NAME.UXB to
    build/DOS/NAME.COM, and copy each src/dos/NAME.TXT and NAME.HLP to build/DOS. Return the folder build/DOS."""
    os.makedirs(CBIN_OUT, exist_ok=True)
    for source in sorted(glob.glob(os.path.join(CBIN, "*.UXB"))):
        name = os.path.splitext(os.path.basename(source))[0].upper() + ".CBI"
        uxb.compile(source, os.path.join(CBIN_OUT, name))
    for source in sorted(glob.glob(os.path.join(UTILITIES, "*.UXB"))):
        name = os.path.splitext(os.path.basename(source))[0].upper() + ".COM"
        uxb.compile(source, os.path.join(CBIN_OUT, name))
    for text in sorted(glob.glob(os.path.join(UTILITIES, "*.TXT")) + glob.glob(os.path.join(UTILITIES, "*.HLP"))):
        shutil.copyfile(text, os.path.join(CBIN_OUT, os.path.basename(text).upper()))
    return CBIN_OUT


def make_test_rom():
    """Copy build/UXDOS16.ROM to build/TEST.ROM with boot_shell cleared, so it boots to the monitor."""
    with open(LABELS, encoding="utf-8") as labels:
        address = next(int(line.split()[1], 16) for line in labels
                       if line.split()[2] == ".boot_shell")
    image = bytearray(open(ROM, "rb").read())
    offset = address - BANK0_START
    if image[offset] != 1:
        sys.exit("build: boot_shell at $%04X is not 1" % address)
    image[offset] = 0
    with open(TEST_ROM, "wb") as out:
        out.write(image)


def main():
    started = time.time()
    genapi.main()
    os.makedirs(OBJ, exist_ok=True)
    objects = []
    sources = (sorted(glob.glob(os.path.join(ASM, "*.s")))
               + sorted(glob.glob(os.path.join(GEN, "*.s"))))
    for source in sources:
        name = os.path.splitext(os.path.basename(source))[0]
        obj = os.path.join(OBJ, name + ".o")
        run([CA65, "--cpu", "65C02", "-I", ASM, "-I", GEN, "-o", obj,
             "-l", os.path.join(OBJ, name + ".LST"), source])
        objects.append(obj)
    run([LD65, "-C", os.path.join(ASM, "rom.cfg"), "-o", ROM,
         "-m", os.path.join(BUILD, "UXDOS16.MAP"), "-Ln", LABELS]
        + objects)
    make_test_rom()
    make_templates()
    for name in ("LICENSE", "NOTICE"):
        shutil.copyfile(os.path.join(ROOT, name), os.path.join(BUILD, name))
    test_files = [os.path.join(TEST_SD_FOLDER, entry) for entry in os.listdir(TEST_SD_FOLDER)
                  if not entry.startswith(".")]
    mksd.make(SD_FOLDER, SD_IMAGE, extra=compile_bas() + [compile_cbin()] + test_files)
    print("built %s, %d bytes, %.2f s" % (os.path.relpath(ROM, ROOT), os.path.getsize(ROM),
                                          time.time() - started))


main()
