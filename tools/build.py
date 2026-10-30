r"""Build the 6502DOS ROM image.

    python tools/build.py [--release]

Runs tools/genapi.py, assembles every src/asm/*.s and build/gen/*.s with ca65, links them
with src/asm/rom.cfg into build/6502DOS.ROM, ROM banks 0, 1 and 5, and copies LICENSE and NOTICE
beside it. MSBASIC's 6502dos target, MSBASIC/src/msbasic.s with MSBASIC/src/6502dos.cfg, is
ROM bank 2, appended to the image; its labels are build/MSBASIC.LBL. MSBASIC/src/6502dos_com.s
assembles to build/bas/MSBASIC.COM, which starts it. ROM banks 3 and 4, appended next, are the
one src/bank3/NAME.UXB, which sets #ORG $C000 and #ROMBANKS 3, 4, compiled and linked with
src/bank3/bank.s and bank.cfg; src/bank3/stub.s assembles to build/bas/NAME.COM, which starts
it. Bank 5, the table library, follows bank 4. ROM banks 6, 7 and 8 are src/bank6/XBASE.UXB, with
#ROMBANKS 6, 7, 8, built the same way to build/bas/XBASE.COM. ca65 and ld65 come from tools/cc65/bin only. Includes are found in src/asm and build/gen. The map is
build/6502DOS.MAP, the label file build/6502DOS.LBL, and each listing build/obj/NAME.LST.
build/TEST.ROM is the same image with boot_shell cleared: it boots to the monitor, not the shell.

UXCBASIC/tpl/MKTPL.PY rebuilds the template tables when a UXCBASIC/tpl or UXCBASIC/tpl/UXDOS
.ASM file is newer than UXCBASIC/tpl/UXDOS/UXC.TPL.BIN. Each src/bas/NAME.UXB compiles to
build/bas/NAME.COM with tools/uxb.py when the COM file is older than the source, than a file it
includes, than the template table or than pyuxc. Each src/scom/NAME.UXB, a
commandlet, compiles the same way to build/sys/NAME.SCOM, a long name on the card. Each
src/dos/NAME.UXB, a DOS utility, compiles to
build/sys/NAME.COM, and each src/dos/NAME.TXT and NAME.HLP is copied to build/sys, with
build/sys/HELP.IDX and HELPBAS.IDX, the indexes of HELP.HLP and HELPBAS.HLP that HELP -R and
HELPBAS -R write. card/sys/xbase/HELPXBASE.HLP is copied to build/sys/xbase, with HELPXBASE.IDX, the
index that HELPXBASE -R writes. Each
src/utils/FOLDER/NAME.UXB, a utility, compiles to build/sys/NAME.COM, and the files of
src/utils/FOLDER are copied to build/source/xcbasic/FOLDER. Each test named in SHOWN_TESTS, tests/NAME.UXB,
compiles to build/sys/NAME.COM as well. CMDSHELL.COM, ROMSHELL.COM and MSBASIC.COM are copied to build/sys.

Then tools/mksd.py makes the SD card image build/SD.IMG from the folder card, the folder build/sys,
which is the card's folder sys, the folder build/source, which is the card's folder source, the
folders of CARD_FOLDERS and the card's folder TEST, gathered in build/card. TEST holds the other COM files in build/bas and the
files and folders of the test card's folder tests/sd. A file in card wins a
name it shares with the others. Before that, each file and folder that the X16 added to the old
build/SD.IMG or changed goes into card, and each one it deleted leaves card; build/SD.SUM lists
what the last build wrote.

With --release, it then empties build/release and fills it with a 4 MB SD.IMG, 6502DOS.ROM,
LICENSE, NOTICE, the files of tools/release (RUN.BAT and the folder x16emu with the licences),
and x16emu with its DLLs from EMU, in the folder x16emu. It zips build/release to
release/6502DOS-VERSION-win.zip, under the folder 6502DOS, with VERSION from api.py, such as
0.1.0-beta1. That SD.IMG, staged in
build/release-card, holds the folder card less RELEASE_SKIP, sys, source and the folders of
CARD_FOLDERS. Exit status 1 when a tool or a
compile failed, api.py is inconsistent, or build/SD.IMG or build/release is open in x16emu.
"""

import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import api  # noqa: E402
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
TEST_SD_FOLDER = os.path.join(ROOT, "tests", "sd")
SD_IMAGE = os.path.join(BUILD, "SD.IMG")
CARD = os.path.join(ROOT, "card")
STAGE = os.path.join(BUILD, "card")
CARD_SUM = os.path.join(BUILD, "SD.SUM")
RELEASE = os.path.join(BUILD, "release")
RELEASE_STAGE = os.path.join(BUILD, "release-card")
RELEASE_FILES = os.path.join(ROOT, "tools", "release")
RELEASE_ZIPS = os.path.join(ROOT, "release")
# The files of the folder card left off the release card.
RELEASE_SKIP = ("WIDE.TXT", "TEST")
# x16emu and the DLLs it loads, copied to build/release/x16emu. Their licences are in
# tools/release/x16emu.
EMU = r"C:\8bitProgramming\x16emu"
EMU_FILES = ("x16emu.exe", "SDL2.dll", "zlib1.dll", "libwinpthread-1.dll")
BAS = os.path.join(ROOT, "src", "bas")
BAS_OUT = os.path.join(BUILD, "bas")
SCOM = os.path.join(ROOT, "src", "scom")
SYS_OUT = os.path.join(BUILD, "sys")
UTILITIES = os.path.join(ROOT, "src", "dos")
UTILS = os.path.join(ROOT, "src", "utils")
SOURCE_OUT = os.path.join(BUILD, "source")
# The folders of the card that start empty.
CARD_FOLDERS = ("help", "sys/temp", "sys/themes", "sys/basic", "sys/xbase", "sys/edit", "sys/uxcbasic", "source/basic",
                "source/xcbasic", "source/uxcbasic", "source/scripts", "source/xbase", "apps", "games")
# The utilities of src/utils that go to build/sys/themes, with the fonts and color themes.
THEME_PROGRAMS = ("THEMED", "FONTEDIT")
# The tests that also go to build/sys, for the user to run on the card.
SHOWN_TESTS = []
TEMPLATES = os.path.join(ROOT, "UXCBASIC", "tpl")
MSBASIC_SRC = os.path.join(ROOT, "MSBASIC", "src")
# bank.s, bank.cfg and stub.s, which each UXCBASIC program in two ROM banks is built with.
BANK_TOOLS = os.path.join(ROOT, "src", "bank3")
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
    """Compile each src/scom/NAME.UXB to build/sys/NAME.SCOM and each src/dos/NAME.UXB to
    build/sys/NAME.COM, and copy each src/dos/NAME.TXT and NAME.HLP to build/sys. Return the folder build/sys."""
    os.makedirs(SYS_OUT, exist_ok=True)
    for source in sorted(glob.glob(os.path.join(SCOM, "*.UXB"))):
        name = os.path.splitext(os.path.basename(source))[0].upper() + ".SCOM"
        uxb.compile(source, os.path.join(SYS_OUT, name))
    for source in sorted(glob.glob(os.path.join(UTILITIES, "*.UXB"))):
        name = os.path.splitext(os.path.basename(source))[0].upper() + ".COM"
        uxb.compile(source, os.path.join(SYS_OUT, name))
    for text in sorted(glob.glob(os.path.join(UTILITIES, "*.TXT")) + glob.glob(os.path.join(UTILITIES, "*.HLP"))):
        shutil.copyfile(text, os.path.join(SYS_OUT, os.path.basename(text).upper()))
    for name in ("HELP", "HELPBAS"):
        write_help_index(os.path.join(UTILITIES, name + ".HLP"), os.path.join(SYS_OUT, name + ".IDX"))
    card_xbase = os.path.join(CARD, "sys", "xbase")
    write_help_index(os.path.join(card_xbase, "HELPXBASE.HLP"), os.path.join(card_xbase, "HELPXBASE.IDX"))
    xbase = os.path.join(SYS_OUT, "xbase")
    os.makedirs(xbase, exist_ok=True)
    for name in ("HELPXBASE.HLP", "HELPXBASE.IDX"):
        shutil.copyfile(os.path.join(card_xbase, name), os.path.join(xbase, name))
    return SYS_OUT


def write_help_index(source, target):
    """Write target, the index of the help file source, byte for byte as HELP -R writes it: the
    size of source after a space, then each topic name of a :NAME line, cut at 81 characters, a
    space and the byte position of the line. Lines end with CR LF."""
    with open(source, "rb") as help_file:
        data = help_file.read()
    lines = [b" %d" % len(data)]
    for heading in re.finditer(rb"^:([^\r\n]*)[\r\n]", data, re.M):
        lines.append(heading.group(1)[:81] + b" %d" % heading.start())
    with open(target, "wb") as index:
        index.write(b"".join(line + b"\r\n" for line in lines))


def compile_utils():
    """Compile each src/utils/FOLDER/NAME.UXB to build/sys/NAME.COM, or build/sys/themes/NAME.COM
    for THEME_PROGRAMS, copy the files of
    src/utils/FOLDER to build/source/xcbasic/FOLDER, and compile each test of SHOWN_TESTS to
    build/sys/NAME.COM. Return the folder build/source."""
    themes = os.path.join(SYS_OUT, "themes")
    os.makedirs(themes, exist_ok=True)
    for folder in sorted(glob.glob(os.path.join(UTILS, "*", ""))):
        folder = os.path.dirname(folder)
        for source in sorted(glob.glob(os.path.join(folder, "*.UXB"))):
            name = os.path.splitext(os.path.basename(source))[0].upper()
            uxb.compile(source, os.path.join(themes if name in THEME_PROGRAMS else SYS_OUT, name + ".COM"))
        shutil.copytree(folder, os.path.join(SOURCE_OUT, "xcbasic", os.path.basename(folder).upper()),
                        ignore=shutil.ignore_patterns(".*"), dirs_exist_ok=True)
    for name in SHOWN_TESTS:
        uxb.compile(os.path.join(ROOT, "tests", name + ".UXB"), os.path.join(SYS_OUT, name + ".COM"))
    return SOURCE_OUT


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


def build_rom_program(first, count=2):
    """Append ROM banks first to first + count - 1, count 2 or 3, to build/6502DOS.ROM: the one
    src/bankF/NAME.UXB, F the first bank, which sets #ORG $C000 and #ROMBANKS with those banks,
    compiled to build/bankF/BANKn.BIN for each bank n, each assembled with src/bank3/bank.s,
    which holds it at $C000 and adds the IRQ entry and the vectors. A later bank's file is empty
    when the program fits the banks before it. Assemble src/bank3/stub.s to build/bas/NAME.COM,
    which starts it. Return the COM path."""
    folder = os.path.join(ROOT, "src", "bank%d" % first)
    out = os.path.join(BUILD, "bank%d" % first)
    sources = glob.glob(os.path.join(folder, "*.UXB"))
    if len(sources) != 1:
        sys.exit("build: src/bank%d must hold one .UXB file" % first)
    os.makedirs(out, exist_ok=True)
    banks = range(first, first + count)
    later = [os.path.join(out, "BANK%d.BIN" % bank) for bank in banks[1:]]
    uxb.compile(sources[0], os.path.join(out, "BANK%d.BIN" % first), *later)
    for path in later:
        if not os.path.exists(path):
            open(path, "wb").close()
    for bank in banks:
        obj = os.path.join(OBJ, "bank%d.o" % bank)
        image = os.path.join(out, "BANK%d.ROM" % bank)
        run([CA65, "-D", "BANK=%d" % bank, "-I", ASM, "-I", GEN, "--bin-include-dir", out,
             "-o", obj, "-l", os.path.join(OBJ, "BANK%d.LST" % bank),
             os.path.join(BANK_TOOLS, "bank.s")])
        run([LD65, "-C", os.path.join(BANK_TOOLS, "bank.cfg"), "-o", image, obj])
        if os.path.getsize(ROM) != bank * BANK_SIZE or os.path.getsize(image) != BANK_SIZE:
            sys.exit("build: banks 0 to %d are not 16 KB each" % bank)
        with open(ROM, "ab") as out_file:
            out_file.write(open(image, "rb").read())
    obj = os.path.join(OBJ, "stub%d.o" % first)
    stub = os.path.join(OBJ, "STUB%d.BIN" % first)
    run([CA65, "-D", "BANK=%d" % first, "-I", ASM, "-I", GEN, "-o", obj,
         os.path.join(BANK_TOOLS, "stub.s")])
    run([LD65, "-C", os.path.join(OBJ, "program.cfg"), "-o", stub, obj])
    name = os.path.splitext(os.path.basename(sources[0]))[0].upper() + ".COM"
    program = os.path.join(BAS_OUT, name)
    with open(program, "wb") as out_file:
        out_file.write(PROGRAM_START.to_bytes(2, "little") + open(stub, "rb").read())
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


def stage_card(stage, sources, tests):
    """Fill the folder stage with CARD_FOLDERS, the files and folders in sources, and those in
    tests under the folder TEST, which only tests makes. Return the upper-case paths it holds,
    joined by "/"."""
    shutil.rmtree(stage, ignore_errors=True)
    ignore = shutil.ignore_patterns(".*")
    for folder in CARD_FOLDERS:
        os.makedirs(os.path.join(stage, *folder.split("/")), exist_ok=True)
    if tests:
        os.makedirs(os.path.join(stage, "TEST"), exist_ok=True)
    for source, folder in [(s, stage) for s in sources] + [(s, os.path.join(stage, "TEST"))
                                                          for s in tests]:
        target = os.path.join(folder, os.path.basename(source))
        if os.path.isdir(source):
            shutil.copytree(source, target, ignore=ignore, dirs_exist_ok=True)
        else:
            shutil.copy2(source, target)
    held = set()
    for folder, dirs, files in os.walk(stage):
        for name in dirs + files:
            held.add(os.path.relpath(os.path.join(folder, name), stage).replace("\\", "/").upper())
    return held


def digest(data):
    return None if data is None else hashlib.sha1(data).hexdigest()


def pull_card(staged):
    """Copy into the folder card each file and folder that the X16 added to build/SD.IMG or
    changed since the last build, and delete from card each one the X16 deleted.

    build/SD.SUM lists what the last build wrote. Without it, only paths not in staged, the
    upper-case paths of build/card, are copied, and nothing is deleted. A path in staged, or under
    a folder in staged that the image lacks, is never deleted from card."""
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
        if key in found or not os.path.lexists(target):
            continue
        parts = key.split("/")
        lost = [p for p in ("/".join(parts[:n]) for n in range(1, len(parts) + 1))
                if p in staged and p not in found]
        if lost:
            print("card: kept %s; the image lacks %s" % (path, built.get(lost[0], [lost[0]])[0]))
            continue
        if os.path.isdir(target):
            shutil.rmtree(target)
        else:
            os.remove(target)
        print("card: deleted %s" % path)


def make_card(sources, tests):
    """Write build/SD.IMG from the files and folders in sources, those in tests under TEST,
    and the folder card, which wins a name they share, after pull_card. Write build/SD.SUM."""
    staged = stage_card(STAGE, sources, tests)
    pull_card(staged)
    shutil.copytree(CARD, STAGE, ignore=shutil.ignore_patterns(".*"), dirs_exist_ok=True)
    try:
        mksd.make(STAGE, SD_IMAGE)
    except PermissionError:
        sys.exit("build: cannot write %s; close x16emu" % os.path.relpath(SD_IMAGE, ROOT))
    listing = {path.upper(): [path, digest(data)] for path, data, when in mksd.read(SD_IMAGE)}
    with open(CARD_SUM, "w", encoding="utf-8") as out:
        json.dump(listing, out, indent=0)


def make_release(sources):
    """Empty build/release and write its SD.IMG from the folder card less RELEASE_SKIP and the
    files and folders in sources. Copy the ROM, LICENSE,
    NOTICE, the files of tools/release and EMU_FILES beside it. Zip build/release into
RELEASE_ZIPS."""
    try:
        if os.path.isdir(RELEASE):
            shutil.rmtree(RELEASE)
    except PermissionError:
        sys.exit("build: cannot empty %s; close x16emu" % os.path.relpath(RELEASE, ROOT))
    stage_card(RELEASE_STAGE, sources, [])
    shutil.copytree(CARD, RELEASE_STAGE, ignore=shutil.ignore_patterns(".*", *RELEASE_SKIP), dirs_exist_ok=True)
    os.makedirs(RELEASE)
    mksd.make(RELEASE_STAGE, os.path.join(RELEASE, "SD.IMG"))
    for path in (ROM, os.path.join(ROOT, "LICENSE"), os.path.join(ROOT, "NOTICE")):
        shutil.copyfile(path, os.path.join(RELEASE, os.path.basename(path)))
    shutil.copytree(RELEASE_FILES, RELEASE, dirs_exist_ok=True)
    for name in EMU_FILES:
        shutil.copyfile(os.path.join(EMU, name), os.path.join(RELEASE, "x16emu", name))
    version = "%d.%d.%d-%s" % (api.VERSION + (api.VERSION_LABEL.replace(" ", "").lower(),))
    os.makedirs(RELEASE_ZIPS, exist_ok=True)
    zip_path = os.path.join(RELEASE_ZIPS, "6502DOS-%s-win.zip" % version)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as out:
        for folder, folders, names in os.walk(RELEASE):
            for name in names:
                path = os.path.join(folder, name)
                out.write(path, os.path.join("6502DOS", os.path.relpath(path, RELEASE)))


def main():
    release = sys.argv[1:] == ["--release"]
    if sys.argv[1:] and not release:
        sys.exit("usage: build.py [--release]")
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
    image = open(ROM, "rb").read()
    if len(image) != 3 * BANK_SIZE:
        sys.exit("build: banks 0, 1 and 5 are not 16 KB each")
    with open(ROM, "wb") as out:
        out.write(image[:2 * BANK_SIZE])
    basic = build_basic()
    make_templates()
    bank3 = build_rom_program(3)
    with open(ROM, "ab") as out:
        out.write(image[2 * BANK_SIZE:])
    database = build_rom_program(6, 3)
    make_test_rom()
    for name in ("LICENSE", "NOTICE"):
        shutil.copyfile(os.path.join(ROOT, name), os.path.join(BUILD, name))
    test_files = [os.path.join(TEST_SD_FOLDER, entry) for entry in os.listdir(TEST_SD_FOLDER)
                  if not entry.startswith(".")]
    programs = compile_bas() + [bank3]
    shell = [p for p in programs if os.path.basename(p) in ("CMDSHELL.COM", "ROMSHELL.COM")]
    card_sources = [compile_scom(), compile_utils()]
    for program in shell + [basic, database]:
        shutil.copy2(program, SYS_OUT)
    make_card(card_sources, [p for p in programs if p not in shell] + test_files)
    if release:
        make_release(card_sources)
    print("built %s, %d bytes, %.2f s" % (os.path.relpath(ROM, ROOT), os.path.getsize(ROM),
                                          time.time() - started))


if __name__ == "__main__":
    main()
