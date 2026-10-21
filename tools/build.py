r"""Build the 6502DOS ROM image.

    python tools/build.py

Runs tools/genapi.py, assembles every src/asm/*.s and build/gen/*.s with ca65, links them
with src/asm/rom.cfg into build/6502DOS.ROM, ROM banks 0 and 1, and copies LICENSE and NOTICE
beside it. MSBASIC's 6502dos target, MSBASIC/src/msbasic.s with MSBASIC/src/6502dos.cfg, is
ROM bank 2, appended to the image; its labels are build/MSBASIC.LBL. MSBASIC/src/6502dos_com.s
assembles to build/bas/MSBASIC.COM, which starts it. ROM banks 3 and 4, appended next, are the
one src/bank3/NAME.UXB, which sets #ORG $C000 and #ROMBANKS 3, 4, compiled and linked with
src/bank3/bank.s and bank.cfg; src/bank3/stub.s assembles to build/bas/NAME.COM, which starts
it. ca65 and ld65 come from tools/cc65/bin only. Includes are found in src/asm and build/gen. The map is
build/6502DOS.MAP, the label file build/6502DOS.LBL, and each listing build/obj/NAME.LST.
build/TEST.ROM is the same image with boot_shell cleared: it boots to the monitor, not the shell.

UXCBASIC/tpl/MKTPL.PY rebuilds the template tables when a UXCBASIC/tpl or UXCBASIC/tpl/UXDOS
.ASM file is newer than UXCBASIC/tpl/UXDOS/UXC.TPL.BIN. Each src/bas/NAME.UXB compiles to
build/bas/NAME.COM with tools/uxb.py when the COM file is older than the source, than a file it
includes, than the template table or than pyuxc. Each src/scom/NAME.UXB, a
commandlet, compiles the same way to build/DOS/NAME.SCOM, a long name on the card. Each
src/dos/NAME.UXB, a DOS utility, compiles to
build/DOS/NAME.COM, and each src/dos/NAME.TXT and NAME.HLP is copied to build/DOS. Each
src/utils/FOLDER/NAME.UXB, a utility, compiles to build/UTILS/NAME.COM, and the files of
src/utils/FOLDER are copied to build/UTILS/SRC/FOLDER.

Then tools/mksd.py makes the SD card image build/SD.IMG from the folder sd, CMDSHELL.COM,
ROMSHELL.COM and MSBASIC.COM, the folder build/DOS, which is the card's folder DOS, the folder build/UTILS, which
is the card's folder UTILS, the card's folder TEST, and
the folder card, gathered in build/card. TEST holds the other COM files in build/bas and the
files and folders of the test card's folder tests/sd. A file in card wins a
name it shares with the others. Before that, each file and folder that the X16 added to the old
build/SD.IMG or changed goes into card, and each one it deleted leaves card; build/SD.SUM lists
what the last build wrote. Exit status 1 when a tool or a compile failed, api.py is inconsistent
or build/SD.IMG is open in x16emu.
"""

import glob
import hashlib
import json
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
ROM = os.path.join(BUILD, "6502DOS.ROM")
TEST_ROM = os.path.join(BUILD, "TEST.ROM")
LABELS = os.path.join(BUILD, "6502DOS.LBL")
BANK0_START = 0xC000
SD_FOLDER = os.path.join(ROOT, "sd")
TEST_SD_FOLDER = os.path.join(ROOT, "tests", "sd")
SD_IMAGE = os.path.join(BUILD, "SD.IMG")
CARD = os.path.join(ROOT, "card")
STAGE = os.path.join(BUILD, "card")
CARD_SUM = os.path.join(BUILD, "SD.SUM")
BAS = os.path.join(ROOT, "src", "bas")
BAS_OUT = os.path.join(BUILD, "bas")
SCOM = os.path.join(ROOT, "src", "scom")
SCOM_OUT = os.path.join(BUILD, "DOS")
UTILITIES = os.path.join(ROOT, "src", "dos")
UTILS = os.path.join(ROOT, "src", "utils")
UTILS_OUT = os.path.join(BUILD, "UTILS")
TEMPLATES = os.path.join(ROOT, "UXCBASIC", "tpl")
MSBASIC_SRC = os.path.join(ROOT, "MSBASIC", "src")
BANK3_SRC = os.path.join(ROOT, "src", "bank3")
BANK3_OUT = os.path.join(BUILD, "bank3")
BANK_SIZE = 0x4000
PROGRAM_START = 0x0801


def run(command):
    result = subprocess.run(command, capture_output=True, text=True)
    sys.stdout.write(result.stdout + result.stderr)
    if result.returncode != 0:
        sys.exit("build: %s failed" % os.path.basename(command[0]))


def make_templates():
    """Run MKTPL.PY when a template source is newer than the 6502DOS table. Print its last line,
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


def compile_scom():
    """Compile each src/scom/NAME.UXB to build/DOS/NAME.SCOM and each src/dos/NAME.UXB to
    build/DOS/NAME.COM, and copy each src/dos/NAME.TXT and NAME.HLP to build/DOS. Return the folder build/DOS."""
    os.makedirs(SCOM_OUT, exist_ok=True)
    for source in sorted(glob.glob(os.path.join(SCOM, "*.UXB"))):
        name = os.path.splitext(os.path.basename(source))[0].upper() + ".SCOM"
        uxb.compile(source, os.path.join(SCOM_OUT, name))
    for source in sorted(glob.glob(os.path.join(UTILITIES, "*.UXB"))):
        name = os.path.splitext(os.path.basename(source))[0].upper() + ".COM"
        uxb.compile(source, os.path.join(SCOM_OUT, name))
    for text in sorted(glob.glob(os.path.join(UTILITIES, "*.TXT")) + glob.glob(os.path.join(UTILITIES, "*.HLP"))):
        shutil.copyfile(text, os.path.join(SCOM_OUT, os.path.basename(text).upper()))
    return SCOM_OUT


def compile_utils():
    """Compile each src/utils/FOLDER/NAME.UXB to build/UTILS/NAME.COM, and copy the files of
    src/utils/FOLDER to build/UTILS/SRC/FOLDER. Return the folder build/UTILS."""
    os.makedirs(UTILS_OUT, exist_ok=True)
    for folder in sorted(glob.glob(os.path.join(UTILS, "*", ""))):
        folder = os.path.dirname(folder)
        for source in sorted(glob.glob(os.path.join(folder, "*.UXB"))):
            name = os.path.splitext(os.path.basename(source))[0].upper() + ".COM"
            uxb.compile(source, os.path.join(UTILS_OUT, name))
        shutil.copytree(folder, os.path.join(UTILS_OUT, "SRC", os.path.basename(folder).upper()),
                        ignore=shutil.ignore_patterns(".*"), dirs_exist_ok=True)
    return UTILS_OUT


def build_basic():
    """Append MSBASIC's 6502dos target to build/6502DOS.ROM as ROM bank 2, and assemble
    build/bas/MSBASIC.COM. Return the COM path."""
    obj = os.path.join(OBJ, "msbasic.o")
    image = os.path.join(BUILD, "MSBASIC.BIN")
    run([CA65, "-D", "DOS6502", "-I", MSBASIC_SRC, "-I", ASM, "-I", GEN, "-o", obj,
         "-l", os.path.join(OBJ, "MSBASIC.LST"), os.path.join(MSBASIC_SRC, "msbasic.s")])
    run([LD65, "-C", os.path.join(MSBASIC_SRC, "6502dos.cfg"), "-o", image,
         "-Ln", os.path.join(BUILD, "MSBASIC.LBL"), obj])
    bank2 = open(image, "rb").read()
    if os.path.getsize(ROM) != 2 * BANK_SIZE or len(bank2) != BANK_SIZE:
        sys.exit("build: banks 0, 1 or 2 are not 16 KB each")
    with open(ROM, "ab") as out:
        out.write(bank2)
    obj = os.path.join(OBJ, "msbasic_com.o")
    stub = os.path.join(OBJ, "MSBASIC_COM.BIN")
    config = os.path.join(OBJ, "program.cfg")
    with open(config, "w", encoding="utf-8") as out:
        out.write("MEMORY { RAM: start = $%04X, size = $0F, file = %%O; }\n"
                  "SEGMENTS { CODE: load = RAM, type = rw; }\n" % PROGRAM_START)
    run([CA65, "-I", ASM, "-I", GEN, "-o", obj, os.path.join(MSBASIC_SRC, "6502dos_com.s")])
    run([LD65, "-C", config, "-o", stub, obj])
    os.makedirs(BAS_OUT, exist_ok=True)
    program = os.path.join(BAS_OUT, "MSBASIC.COM")
    with open(program, "wb") as out:
        out.write(PROGRAM_START.to_bytes(2, "little") + open(stub, "rb").read())
    return program


def build_bank3():
    """Append ROM banks 3 and 4 to build/6502DOS.ROM: the one src/bank3/NAME.UXB, compiled to
    build/bank3/BANK3.BIN and BANK4.BIN, each assembled with src/bank3/bank.s, which holds it
    at $C000 and adds the IRQ entry and the vectors. BANK4.BIN is empty when the program fits
    bank 3. Assemble src/bank3/stub.s to build/bas/NAME.COM, which starts it. Return the COM
    path."""
    sources = glob.glob(os.path.join(BANK3_SRC, "*.UXB"))
    if len(sources) != 1:
        sys.exit("build: src/bank3 must hold one .UXB file")
    os.makedirs(BANK3_OUT, exist_ok=True)
    second = os.path.join(BANK3_OUT, "BANK4.BIN")
    uxb.compile(sources[0], os.path.join(BANK3_OUT, "BANK3.BIN"), second)
    if not os.path.exists(second):
        open(second, "wb").close()
    for bank in (3, 4):
        obj = os.path.join(OBJ, "bank%d.o" % bank)
        image = os.path.join(BANK3_OUT, "BANK%d.ROM" % bank)
        run([CA65, "-D", "BANK=%d" % bank, "-I", ASM, "-I", GEN, "--bin-include-dir", BANK3_OUT,
             "-o", obj, "-l", os.path.join(OBJ, "BANK%d.LST" % bank),
             os.path.join(BANK3_SRC, "bank.s")])
        run([LD65, "-C", os.path.join(BANK3_SRC, "bank.cfg"), "-o", image, obj])
        if os.path.getsize(ROM) != bank * BANK_SIZE or os.path.getsize(image) != BANK_SIZE:
            sys.exit("build: banks 0 to %d are not 16 KB each" % bank)
        with open(ROM, "ab") as out:
            out.write(open(image, "rb").read())
    obj = os.path.join(OBJ, "stub.o")
    stub = os.path.join(OBJ, "STUB.BIN")
    run([CA65, "-I", ASM, "-I", GEN, "-o", obj, os.path.join(BANK3_SRC, "stub.s")])
    run([LD65, "-C", os.path.join(OBJ, "program.cfg"), "-o", stub, obj])
    name = os.path.splitext(os.path.basename(sources[0]))[0].upper() + ".COM"
    program = os.path.join(BAS_OUT, name)
    with open(program, "wb") as out:
        out.write(PROGRAM_START.to_bytes(2, "little") + open(stub, "rb").read())
    return program


def make_test_rom():
    """Copy build/6502DOS.ROM to build/TEST.ROM with boot_shell cleared, so it boots to the monitor."""
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


def stage_card(sources, tests):
    """Fill build/card with the folder sd, the files and folders in sources, and those in tests
    under the folder TEST. Return the upper-case paths it holds, joined by "/"."""
    shutil.rmtree(STAGE, ignore_errors=True)
    ignore = shutil.ignore_patterns(".*")
    shutil.copytree(SD_FOLDER, STAGE, ignore=ignore)
    os.makedirs(os.path.join(STAGE, "TEST"), exist_ok=True)
    for source, folder in [(s, STAGE) for s in sources] + [(s, os.path.join(STAGE, "TEST"))
                                                          for s in tests]:
        target = os.path.join(folder, os.path.basename(source))
        if os.path.isdir(source):
            shutil.copytree(source, target, ignore=ignore, dirs_exist_ok=True)
        else:
            shutil.copy2(source, target)
    held = set()
    for folder, dirs, files in os.walk(STAGE):
        for name in dirs + files:
            held.add(os.path.relpath(os.path.join(folder, name), STAGE).replace("\\", "/").upper())
    return held


def digest(data):
    return None if data is None else hashlib.sha1(data).hexdigest()


def pull_card(staged):
    """Copy into the folder card each file and folder that the X16 added to build/SD.IMG or
    changed since the last build, and delete from card each one the X16 deleted.

    build/SD.SUM lists what the last build wrote. Without it, only paths not in staged, the
    upper-case paths of build/card, are copied, and nothing is deleted."""
    if not os.path.exists(SD_IMAGE):
        return
    try:
        with open(CARD_SUM, encoding="utf-8") as listing:
            built = json.load(listing)
    except FileNotFoundError:
        built = None
    found = {}
    for path, data, when in mksd.read(SD_IMAGE):
        key = path.upper()
        found[key] = path
        if built is None:
            if key in staged:
                continue
        elif key in built and built[key][1] == digest(data):
            continue
        target = os.path.join(CARD, *path.split("/"))
        if data is None:
            os.makedirs(target, exist_ok=True)
        else:
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "wb") as out:
                out.write(data)
            if when is not None:
                os.utime(target, (when.timestamp(), when.timestamp()))
        print("card: kept %s" % path)
    for key, (path, _) in (built or {}).items():
        target = os.path.join(CARD, *path.split("/"))
        if key not in found and os.path.lexists(target):
            if os.path.isdir(target):
                shutil.rmtree(target)
            else:
                os.remove(target)
            print("card: deleted %s" % path)


def make_card(sources, tests):
    """Write build/SD.IMG from the folder sd, the files and folders in sources, those in tests
    under TEST, and the folder card, which wins a name they share, after pull_card. Write
    build/SD.SUM."""
    staged = stage_card(sources, tests)
    pull_card(staged)
    if os.path.isdir(CARD):
        shutil.copytree(CARD, STAGE, ignore=shutil.ignore_patterns(".*"), dirs_exist_ok=True)
    try:
        mksd.make(STAGE, SD_IMAGE)
    except PermissionError:
        sys.exit("build: cannot write %s; close x16emu" % os.path.relpath(SD_IMAGE, ROOT))
    listing = {path.upper(): [path, digest(data)] for path, data, when in mksd.read(SD_IMAGE)}
    with open(CARD_SUM, "w", encoding="utf-8") as out:
        json.dump(listing, out, indent=0)


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
         "-m", os.path.join(BUILD, "6502DOS.MAP"), "-Ln", LABELS]
        + objects)
    basic = build_basic()
    make_templates()
    bank3 = build_bank3()
    make_test_rom()
    for name in ("LICENSE", "NOTICE"):
        shutil.copyfile(os.path.join(ROOT, name), os.path.join(BUILD, name))
    test_files = [os.path.join(TEST_SD_FOLDER, entry) for entry in os.listdir(TEST_SD_FOLDER)
                  if not entry.startswith(".")]
    programs = compile_bas() + [bank3]
    shell = [p for p in programs if os.path.basename(p) in ("CMDSHELL.COM", "ROMSHELL.COM")]
    make_card(shell + [basic, compile_scom(), compile_utils()],
              [p for p in programs if p not in shell] + test_files)
    print("built %s, %d bytes, %.2f s" % (os.path.relpath(ROM, ROOT), os.path.getsize(ROM),
                                          time.time() - started))


main()
