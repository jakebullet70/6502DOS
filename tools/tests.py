"""Run the 6502DOS tests: boot build/TEST.ROM headless and compare what it prints.

    python tools/tests.py [NAME ...] [--update]

build/TEST.ROM boots to the monitor. The tests in SHELL_ROM_TESTS boot build/6502DOS.ROM, which
runs C:\\ROMSHELL.COM at boot.

Each test is an expected output tests/NAME.OUT. A test boots the ROM in x16emu with -echo raw
and reads what the ROM writes through $FFD2. It passes when that output equals NAME.OUT. It
fails when the output departs from NAME.OUT or when NAME.OUT is not complete within 5 s. The
boot banner, up to the line "For the Commander X16", is left out of both, except in BOOT.

Every test runs with the SD card image build/tests/SD.IMG, which tools/mksd.py makes from
tests/sd at the start: 256 MB, 2 sectors per cluster, 259079 clusters, the files dated
2026-10-13. Its root also holds build/bas/NAME.COM, from tools/build.py, tests/com/NAME.S
assembled to NAME.COM: the load address $0801, then the code from $0801, and tests/com/NAME.UXB and
tests/NAME.UXB compiled to NAME.COM. Its folder DOS is build/DOS, the commandlets from
tools/build.py, and its folder UTILS is build/UTILS. Each test gets a new copy of the image.
tests/NAME.PY, when it exists, defines card(image), which then changes the copy or writes a card
of its own in its place. It may also define check(image), which reads the card after the run and
returns a list of faults; a fault fails the test.

A test can type keys into the monitor with x16emu -bas:
- tests/NAME.S, a program assembled with ca65 to run at $1000, typed in with E commands;
- or RUN NAME.COM, when tests/NAME.UXB exists: it compiles to NAME.COM on the test card;
- then tests/NAME.IN, each line ended by CR. \\XE0 then a scan code types an extended key:
  \\XE0\\X48 is Up.

NAMEs pick tests; with none, every test runs but those in STOPPED_TESTS. --update runs each test for 4.5 s and writes
NAME.OUT from what it printed: read the .OUT before you keep it. Build first
(tools/build.py). Exit status 1 when a test failed or a program did not assemble.

--msbasic runs MSBASIC's tests instead, on build/6502DOS.ROM: MSBASIC/tests/name.bas is typed
into MSBASIC at the shell, then QUIT. The transcript after the banner must equal name.out after
its banner, the sim's transcript, with line ends and trailing spaces ignored. name.rom.out, when
it exists, replaces name.out: the ROM's transcript where the target differs from the sim.
NAMEs pick tests, in any case. --update writes name.rom.out from the transcript: read it before
you keep it.
"""

import datetime
import difflib
import glob
import os
import runpy
import shutil
import subprocess
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mksd  # noqa: E402
import uxb  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EMU = r"C:\8bitProgramming\x16emu\x16emu.exe"
ROM = os.path.join(ROOT, "build", "TEST.ROM")
SHELL_ROM = os.path.join(ROOT, "build", "6502DOS.ROM")
SHELL_ROM_TESTS = ("SHBOOT",)   # these boot 6502DOS.ROM, into the shell
# The full run skips these; a NAME still runs one.
STOPPED_TESTS = (
    "ABSIO", "ANSI", "ASK", "BANKCALL", "BREAK", "CHKDSK", "CLOCK", "CLOCKCMD", "CMDLETS",
    "CONSLIB", "CWD", "DIRS", "DISK", "DOSAPI", "DUP", "EDIT", "EDIT2", "EDITBIG", "EDITSET",
    "ENDCODE", "FONTED", "FONTFILE", "FONTIO", "FONTOPS", "GREP", "HANDLES", "HDIRRED", "HEAD",
    "INILIB", "KEEP", "MORE", "REGLIB", "RGBYTES", "RGCALL", "RGDATA", "RGERR", "RGMULTI",
    "RGPASS", "RGPTR", "RGRUN", "SEEK", "TAIL", "TARGET", "TED", "TEDBIG", "THEMED", "VERABOX",
    "VIEW", "WHERE", "WRITE", "XCOPY", "XCOPYS")
TESTS = os.path.join(ROOT, "tests")
OBJ = os.path.join(ROOT, "build", "tests")
KEYS = os.path.join(OBJ, "keys.txt")
SD_FOLDER = os.path.join(TESTS, "sd")
SD_IMAGE = os.path.join(OBJ, "SD.IMG")
RUN_IMAGE = os.path.join(OBJ, "RUN.IMG")
# The test card: 256 MB at 2 sectors per cluster, and a block of 4 MB for the programs.
CLUSTERS = 259079
RESERVE = 4096
CC65 = os.path.join(ROOT, "tools", "cc65", "bin")
COM_FOLDER = os.path.join(TESTS, "com")
BAS_OUT = os.path.join(ROOT, "build", "bas")
SCOM_OUT = os.path.join(ROOT, "build", "DOS")
UTILS_OUT = os.path.join(ROOT, "build", "UTILS")
PROGRAM_START = 0x1000
COM_START = 0x0801
BYTES_PER_LINE = 24             # "E 1000 " and 24 bytes fit the monitor's 79 characters
LIMIT = 5.0
UPDATE_SECONDS = 4.5
BANNER_END = "For the Commander X16\n"   # the last line of the boot banner
# x16emu prints these itself: when the ROM has no stock KERNAL symbols, and at -sdcard.
EMULATOR_LINES = ("Unable to find KERNAL ", "SD card attached.")
BASIC_TESTS = os.path.join(ROOT, "MSBASIC", "tests")
BASIC_END = "\nQUIT\nC>"        # the QUIT typed after a test, then the shell's prompt


def clean(raw):
    # x16emu's stdout turns LF into CR LF, so the console's CR LF arrives as CR CR LF.
    text = raw.decode("latin-1").replace("\r\n", "\n").replace("\r\n", "\n").replace("\r", "\n")
    lines = [l for l in text.split("\n") if not l.startswith(EMULATOR_LINES)]
    # The last line may be an emulator line still arriving.
    if lines and any(e.startswith(lines[-1]) for e in EMULATOR_LINES):
        lines[-1] = ""
    return "\n".join(lines)


def assemble(source, start):
    """Assemble source to run at start and return its bytes."""
    name = os.path.splitext(os.path.basename(source))[0]
    obj = os.path.join(OBJ, name + ".o")
    binary = os.path.join(OBJ, name + ".BIN")
    config = os.path.join(OBJ, "program.cfg")
    with open(config, "w", encoding="utf-8") as out:
        out.write("MEMORY { RAM: start = $%04X, size = $8000, file = %%O; }\n"
                  "SEGMENTS { CODE: load = RAM, type = rw; }\n" % start)
    for command in ([os.path.join(CC65, "ca65.exe"), "--cpu", "65C02",
                     "-I", os.path.join(ROOT, "build", "gen"), "-o", obj, source],
                    [os.path.join(CC65, "ld65.exe"), "-C", config, "-o", binary, obj]):
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            sys.exit("tests: %s%s" % (result.stdout, result.stderr))
    return open(binary, "rb").read()


def program_keys(source):
    """Assemble source to run at PROGRAM_START and return the E commands that enter it."""
    data = assemble(source, PROGRAM_START)
    lines = []
    for offset in range(0, len(data), BYTES_PER_LINE):
        chunk = data[offset:offset + BYTES_PER_LINE]
        lines.append("E %04X %s\n" % (PROGRAM_START + offset, " ".join("%02X" % b for b in chunk)))
    return "".join(lines)


def after_dos_banner(text):
    """The text after the boot banner, whose first line names the version; None until the
    banner is complete."""
    end = text.find(BANNER_END)
    return None if end < 0 else text[end + len(BANNER_END):]


def boot(rom, want, keys, done=None, cut=lambda text: text):
    """Boot rom, type keys when it is not None, and return what the ROM
    printed. Stop when cut(output) is as long as want or departs from it, or after LIMIT
    seconds; cut returns None while it cannot tell yet. With want None, stop after
    UPDATE_SECONDS, or, with done, when done(output) is true or after LIMIT seconds."""
    env = dict(os.environ, SDL_VIDEODRIVER="dummy")
    command = [EMU, "-rom", rom, "-warp", "-sound", "none", "-nohostfs", "-echo", "raw",
               "-sdcard", RUN_IMAGE]
    if keys is not None:
        with open(KEYS, "w", encoding="latin-1", newline="") as out:
            out.write(keys.replace("\r\n", "\n").replace("\n", "\r"))
        command += ["-bas", KEYS]
    emu = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    chunks = []

    def reader():
        while True:
            chunk = emu.stdout.read1(4096)
            if not chunk:
                return
            chunks.append(chunk)

    thread = threading.Thread(target=reader, daemon=True)
    thread.start()
    deadline = time.time() + (UPDATE_SECONDS if want is None and done is None else LIMIT)
    while time.time() < deadline:
        if want is not None:
            # A CR at the end may be the start of a CR LF still arriving.
            got = cut(clean(b"".join(chunks).rstrip(b"\r")))
            if got is not None and (len(got) >= len(want) or not want.startswith(got)):
                break
        elif done is not None and done(clean(b"".join(chunks))):
            break
        time.sleep(0.02)
    # Kill by this handle only: never by image name, other emulators may be running.
    emu.kill()
    emu.wait(timeout=5)
    thread.join(timeout=5)
    return clean(b"".join(chunks))


def normalize(text):
    """As MSBASIC/tests/run.py: no CRs, no trailing spaces, one line end at the end."""
    return "\n".join(l.rstrip() for l in text.replace("\r", "").split("\n")).rstrip() + "\n"


def after_banner(text):
    """The transcript after MSBASIC's banner line, which names the free bytes."""
    start = text.find("UX6502BASIC ")
    return text[text.index("\n", start) + 1:] if start >= 0 else text


def basic_tests(names, update):
    """Run MSBASIC's tests on the shell ROM and return the names that failed. With update,
    write name.rom.out instead."""
    if not names:
        names = sorted(os.path.splitext(f)[0] for f in os.listdir(BASIC_TESTS)
                       if f.endswith(".bas"))
    failed = []
    for name in [n.lower() for n in names]:
        expected = os.path.join(BASIC_TESTS, name + ".rom.out")
        if not os.path.exists(expected):
            expected = os.path.join(BASIC_TESTS, name + ".out")
        want = normalize(after_banner(open(expected, encoding="latin-1").read()))
        source = open(os.path.join(BASIC_TESTS, name + ".bas"), encoding="latin-1").read()
        shutil.copyfile(SD_IMAGE, RUN_IMAGE)
        took = time.time()
        got = boot(SHELL_ROM, None, "MSBASIC\n" + source + "QUIT\n",
                   done=lambda output: BASIC_END in output)
        took = time.time() - took
        quit = BASIC_END in got
        got = normalize(after_banner(got[:got.index(BASIC_END)] if quit else got))
        if update:
            with open(os.path.join(BASIC_TESTS, name + ".rom.out"), "w", encoding="latin-1",
                      newline="\n") as out:
                out.write(got)
            print("WROTE %-12s %4.1f s%s" % (name, took, "" if quit else ", no QUIT"))
            continue
        if quit and got == want and took <= LIMIT:
            print("ok    %-12s %4.1f s" % (name, took))
            continue
        failed.append(name)
        print("FAIL  %-12s %4.1f s%s" % (name, took, "" if quit else ", no QUIT"))
        sys.stdout.writelines("      " + l for l in difflib.unified_diff(
            want.splitlines(True), got.splitlines(True), os.path.basename(expected), "ROM"))
    return failed


def test_name(out_path):
    """NAME for tests/NAME.OUT."""
    return os.path.splitext(os.path.basename(out_path))[0].upper()


def main():
    args = sys.argv[1:]
    update = "--update" in args
    msbasic = "--msbasic" in args
    names = [a.upper() for a in args if not a.startswith("--")]
    if not os.path.exists(ROM):
        sys.exit("tests: no build/TEST.ROM; run tools/build.py first")
    outs = sorted(glob.glob(os.path.join(TESTS, "*.OUT")))
    if msbasic:
        outs = []
    elif names:
        outs = [o for o in outs if test_name(o) in names]
        if len(outs) != len(names):
            sys.exit("tests: no such test among %s" % " ".join(names))
    else:
        outs = [o for o in outs if test_name(o) not in STOPPED_TESTS]
    os.makedirs(OBJ, exist_ok=True)
    programs = sorted(glob.glob(os.path.join(BAS_OUT, "*.COM")))
    for source in sorted(glob.glob(os.path.join(COM_FOLDER, "*.S"))):
        program = os.path.join(OBJ, os.path.splitext(os.path.basename(source))[0] + ".COM")
        with open(program, "wb") as out:
            out.write(COM_START.to_bytes(2, "little") + assemble(source, COM_START))
        programs.append(program)
    uxb_sources = glob.glob(os.path.join(COM_FOLDER, "*.UXB")) + glob.glob(os.path.join(TESTS, "*.UXB"))
    for source in sorted(uxb_sources):
        program = os.path.join(OBJ, os.path.splitext(os.path.basename(source))[0].upper() + ".COM")
        uxb.compile(source, program)
        programs.append(program)
    for folder in (SCOM_OUT, UTILS_OUT):
        if os.path.isdir(folder):
            programs.append(folder)
    # The programs go in a block of their own, so the free space and the clusters of the files
    # of tests/sd stay the same when a program changes.
    mksd.make(SD_FOLDER, SD_IMAGE, sectors_per_cluster=2, clusters=CLUSTERS,
              date=datetime.date(2026, 10, 13), extra=programs, reserve=RESERVE, root_clusters=2)
    failed = []
    started = time.time()
    count = len(outs)
    if msbasic:
        failed = basic_tests(names, update)
        count = len(names or glob.glob(os.path.join(BASIC_TESTS, "*.bas")))
    for out_path in outs:
        name = os.path.splitext(os.path.basename(out_path))[0]
        want = open(out_path, encoding="latin-1").read().replace("\r\n", "\n")
        base = os.path.splitext(out_path)[0]
        keys = None
        shutil.copyfile(SD_IMAGE, RUN_IMAGE)
        hooks = runpy.run_path(base + ".PY") if os.path.exists(base + ".PY") else {}
        if "card" in hooks:
            hooks["card"](RUN_IMAGE)
        if os.path.exists(base + ".S"):
            keys = program_keys(base + ".S")
        elif os.path.exists(base + ".UXB"):
            keys = "RUN %s.COM\n" % name.upper()
        if os.path.exists(base + ".IN"):
            keys = (keys or "") + open(base + ".IN", encoding="latin-1").read()
        took = time.time()
        rom = SHELL_ROM if test_name(out_path) in SHELL_ROM_TESTS else ROM
        # Only BOOT checks the banner, so a new version changes one golden.
        cut = (lambda text: text) if name == "BOOT" else after_dos_banner
        got = boot(rom, None if update else cut(want), keys, cut=cut)
        took = time.time() - took
        faults = hooks["check"](RUN_IMAGE) if "check" in hooks else []
        if update:
            with open(out_path, "w", encoding="latin-1", newline="\n") as out:
                out.write(got)
            print("WROTE %-12s %4.1f s" % (test_name(out_path), took))
            for fault in faults:
                print("      fault: " + fault)
            continue
        if cut(got) == cut(want) and took <= LIMIT and not faults:
            print("ok    %-12s %4.1f s" % (test_name(out_path), took))
            continue
        failed.append(test_name(out_path))
        print("FAIL  %-12s %4.1f s" % (test_name(out_path), took))
        for fault in faults:
            print("      fault: " + fault)
        print("      expected:")
        for line in want.split("\n"):
            print("      | " + line)
        print("      got:")
        for line in got.split("\n"):
            print("      | " + line)
    print("%d tests, %d failed, %.1f s" % (count, len(failed), time.time() - started))
    if failed:
        print("failed: " + " ".join(failed))
        sys.exit(1)


main()
