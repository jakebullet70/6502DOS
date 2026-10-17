"""Run the UXCBASIC tests: compile each tests/*.UXB with pyuxc, run it on UXDOS16, and compare.

    python tests.py [NAME ...] [--update]

Each test is a source NAME.UXB and its expected output NAME.OUT, both in tests/. pyuxc
compiles the source into build/uxctests of the UXDOS16 folder, with #INCLUDE looking in tests/. A source that
compiles runs on the UXDOS16 ROM in x16emu, headless: the program is TEST.COM on a new SD card
image, and RUN TEST.COM is typed at the monitor's prompt. When tests/NAME.IN exists, its lines
are typed after it, each ended by CR; the line editor echoes them. What the program printed, up
to the monitor's prompt, is compared with NAME.OUT. Output to a file is not in it. A source that does not compile is compared by its result line, so an
error test's NAME.OUT is one line:

    ERROR,<line>,<message>

A run fails when the monitor's prompt is not back within 5 s. The ROM is build/UXDOS16.ROM of
the UXDOS16 folder, the folder above this one: build it first with tools/build.py.

NAMEs pick tests; with none, every test runs. --update writes NAME.OUT from what the test
gave, for a new test or a change made on purpose: read the .OUT it wrote before you keep
it. Exit status 1 when a test failed.
"""

import datetime
import glob
import os
import shutil
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
TESTS = os.path.join(HERE, "tests")
INCLUDE_FOLDERS = [TESTS]
UXDOS16_REPO = os.path.dirname(HERE)
DRIVE = os.path.join(UXDOS16_REPO, "build", "uxctests")
EMU = r"C:\8bitProgramming\x16emu\x16emu.exe"
ROM = os.path.join(UXDOS16_REPO, "build", "UXDOS16.ROM")
SD_FOLDER = os.path.join(DRIVE, "sd")
PROGRAM = os.path.join(DRIVE, "TEST.COM")
IMAGE = os.path.join(DRIVE, "SD.IMG")
KEYS = os.path.join(DRIVE, "RUN.KEYS")
PROMPT = ">>"
RUN_LINE = PROMPT + "RUN TEST.COM"
LIMIT = 5.0
SETTLE = 0.1
# x16emu prints these itself: when the ROM has no stock KERNAL symbols, and at -sdcard.
EMULATOR_LINES = ("Unable to find KERNAL ", "SD card attached.")
sys.path.insert(0, os.path.join(HERE, "pyuxc"))
sys.path.insert(0, os.path.join(UXDOS16_REPO, "tools"))

import mksd  # noqa: E402
import pyuxc  # noqa: E402


def clean(raw):
    # x16emu's stdout turns LF into CR LF, so the console's CR LF arrives as CR CR LF.
    text = raw.decode("latin-1").replace("\r\n", "\n").replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(l for l in text.split("\n") if not l.startswith(EMULATOR_LINES))


def program_output(text):
    """What the program printed, out of the echo of the boot, or None before RUN TEST.COM
    shows. The text is the lines after the RUN line, up to the prompt that ends the run."""
    lines = text.split("\n")
    if RUN_LINE not in lines:
        return None
    return "\n".join(lines[lines.index(RUN_LINE) + 1:])


def run(typed):
    """Boot UXDOS16 with build/TEST.COM on the card, run it, and return what it printed, or
    None when the prompt did not come back within LIMIT seconds. typed is text typed after
    the RUN, one line per CR, or None."""
    os.makedirs(SD_FOLDER, exist_ok=True)
    mksd.make(SD_FOLDER, IMAGE, sectors_per_cluster=2, clusters=1024,
              date=datetime.date(2026, 10, 13), extra=[PROGRAM])
    with open(KEYS, "w", encoding="latin-1", newline="") as out:
        out.write(("RUN TEST.COM\n" + (typed or "")).replace("\n", "\r"))
    env = dict(os.environ, SDL_VIDEODRIVER="dummy")
    command = [EMU, "-rom", ROM, "-warp", "-sound", "none", "-nohostfs", "-echo", "raw",
               "-sdcard", IMAGE, "-bas", KEYS]
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
    deadline = time.time() + LIMIT
    out = None
    while time.time() < deadline:
        time.sleep(0.02)
        got = program_output(clean(b"".join(chunks)))
        if got is None or not got.endswith(PROMPT):
            continue
        # The monitor prints CR LF after the program, then the prompt. The prompt ends the
        # run when nothing more comes; main strips the line ends before it.
        size = len(b"".join(chunks))
        time.sleep(SETTLE)
        if len(b"".join(chunks)) == size:
            out = got[:-len(PROMPT)]
            break
    # Kill by this handle only: never by image name, other emulators may be running.
    emu.kill()
    emu.wait(timeout=5)
    thread.join(timeout=5)
    return out


def outcome(source):
    """What a test gave: the program's output, or its compile result line."""
    result, _ = pyuxc.compile_file(source, INCLUDE_FOLDERS, DRIVE)
    fields = result.split(",")
    if fields[0] != "OK":
        return result
    shutil.copyfile(os.path.join(DRIVE, fields[1]), PROGRAM)
    keys = os.path.splitext(source)[0] + ".IN"
    typed = None
    if os.path.exists(keys):
        typed = open(keys, encoding="latin-1").read().replace("\r\n", "\n")
    out = run(typed)
    return "NO PROMPT WITHIN %d S" % LIMIT if out is None else out


def expected(path):
    if not os.path.exists(path):
        return None
    text = open(path, encoding="latin-1").read()
    return text.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")


def main():
    args = sys.argv[1:]
    update = "--update" in args
    names = [a.upper() for a in args if not a.startswith("--")]
    if not os.path.exists(ROM):
        sys.exit("tests: no %s; run tools/build.py first" % ROM)
    os.makedirs(DRIVE, exist_ok=True)
    sources = sorted(glob.glob(os.path.join(TESTS, "*.UXB")))
    if names:
        sources = [s for s in sources if os.path.splitext(os.path.basename(s))[0].upper() in names]
        if len(sources) != len(names):
            sys.exit("tests: no such test among %s" % " ".join(names))
    failed = []
    started = time.time()
    for source in sources:
        name = os.path.splitext(os.path.basename(source))[0]
        out_path = os.path.splitext(source)[0] + ".OUT"
        took = time.time()
        got = outcome(source).rstrip("\n")
        took = time.time() - took
        want = expected(out_path)
        if update:
            with open(out_path, "w", encoding="latin-1", newline="\n") as out:
                out.write(got + "\n")
            print("WROTE %-12s %4.1f s" % (name, took))
            continue
        if got == want:
            print("ok    %-12s %4.1f s" % (name, took))
            continue
        failed.append(name)
        print("FAIL  %-12s %4.1f s" % (name, took))
        if want is None:
            print("      no %s.OUT; it gave:" % name)
            for line in got.split("\n"):
                print("      | " + line)
            continue
        print("      expected:")
        for line in want.split("\n"):
            print("      | " + line)
        print("      got:")
        for line in got.split("\n"):
            print("      | " + line)
    print("%d tests, %d failed, %d s" % (len(sources), len(failed), time.time() - started))
    if failed:
        print("failed: " + " ".join(failed))
        sys.exit(1)


main()
