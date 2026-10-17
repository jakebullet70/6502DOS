"""Compile a UXCBASIC source with build/UXC.PRG in the emulator, and run what it wrote.

    python uxc.py FILE.UXB [--run] [--seconds N]

FILE.UXB is copied onto build/, the emulator's drive, under its own name. build/UXC.INPUT
then names it and the result file UXC.RESULT, and UXC.PRG runs headless until it has
written the result, or for N seconds (default 30). The compiler's screen output and the
result line are printed. With --run, the PRG the compile wrote is run next, until BASIC
prints READY. again (10 seconds at most), and its output printed.

Exit status 0 when the compile (and the run) succeeded. build.py UXC builds UXC.PRG, and
empties build/, so build first and compile after. It runs on the stock ROM, which only the
GPC UXC needs. pyuxc/golden.py imports compile_source from here.
"""

import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
GPC_REPO = os.environ.get("GPC_REPO", r"C:\dev\CmdrX16\dos_tools\x16-blitz-compiler")
EMUDIR = os.path.join(GPC_REPO, "bin", "x16emu")
EMU = os.path.join(EMUDIR, "x16emu.exe")
ROM = os.path.join(EMUDIR, "rom.bin")
DRIVE = os.path.join(HERE, "build")
RESULT = os.path.join(DRIVE, "UXC.RESULT")


def emulate(prg, seconds, until=None, typed=None):
    """Run prg headless with the CHROUT echo, for at most seconds. until, when given, is
    called with the echo text so far, and the run stops when it returns true. typed, when
    given, is text typed on the keyboard after the RUN, one line per Return. Return the
    echoed text, with its line ends made LF."""
    env = dict(os.environ, SDL_VIDEODRIVER="dummy")
    log = os.path.join(DRIVE, "RUN.LOG")
    start = ["-prg", prg, "-run"]
    if typed is not None:
        # -bas loses keys typed while -prg loads, so the LOAD and the RUN are typed too.
        keys = os.path.join(DRIVE, "RUN.KEYS")
        with open(keys, "w", encoding="latin-1", newline="\n") as out:
            out.write('LOAD"%s"\nRUN\n%s' % (os.path.basename(prg), typed))
        start = ["-bas", keys]
    cmd = [EMU, "-rom", ROM, "-fsroot", DRIVE] + start + ["-warp", "-sound", "none", "-echo", "iso"]
    with open(log, "wb") as out:
        # Kill by this handle only: never by image name, other emulators may be running.
        emu = subprocess.Popen(cmd, cwd=DRIVE, stdout=out, stderr=subprocess.STDOUT, env=env)
        started = time.time()
        while time.time() - started < seconds:
            time.sleep(0.2)
            if until and until(read_log(log)):
                time.sleep(0.3)  # let the last line, and a file being closed, land
                break
        emu.kill()
        try:
            emu.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass
    return read_log(log)


def read_log(log):
    text = open(log, "rb").read().decode("latin-1")
    return text.replace("\r\n", "\n").replace("\r", "\n")


def compile_source(source, seconds=30):
    """Compile source with build/UXC.PRG. Return (result, screen): the result line, or None
    when UXC wrote none in time, and the compiler's screen output."""
    name = os.path.basename(source).upper()
    target = os.path.join(DRIVE, name)
    if not (os.path.exists(target) and os.path.samefile(source, target)):
        shutil.copyfile(source, target)
    with open(os.path.join(DRIVE, "UXC.INPUT"), "w", newline="\n") as out:
        out.write("%s\nUXC.RESULT\n" % name)
    if os.path.exists(RESULT):
        os.remove(RESULT)
    # The third READY. is BASIC back after UXC ended: a runtime error stops it with no result.
    text = emulate(os.path.join(DRIVE, "UXC.PRG"), seconds,
                   until=lambda t: os.path.exists(RESULT) or t.count("READY.") >= 3)
    # x16emu echoes every CHROUT, the bytes UXC writes to its files too. Drop those lines.
    lines = (program_output(text) or text).split(chr(10))
    screen = chr(10).join(l for l in lines if "\\X" not in l and not l.startswith(("OK,", "ERROR,")))
    if not os.path.exists(RESULT):
        return None, screen
    return open(RESULT, "rb").read().decode("latin-1").strip(), screen


def program_output(text):
    """What a program printed, out of the echo of its run, or None when it never loaded.

    The echo shows the boot banner, READY., the load, READY. again, then the program, then
    READY. when it ends. The program's output lies between the second READY. and the third.
    The blank line the RUN leaves, and the one BASIC prints before READY., are cut."""
    lines = text.split(chr(10))
    ready = [i for i, l in enumerate(lines) if l == "READY."]
    if len(ready) < 2:
        return None
    end = ready[2] if len(ready) >= 3 else len(lines)
    body = lines[ready[1] + 1:end]
    if body and body[0] == "":
        body = body[1:]
    if len(ready) >= 3 and body and body[-1] == "":
        body = body[:-1]
    return chr(10).join(body)


def run_prg(prg, seconds=10, typed=None):
    """Run a compiled PRG until BASIC prints READY. after it, or for at most seconds, and
    return what it printed, or None when it never loaded. typed is as for emulate. The
    keyboard does not echo, so what is typed is not in the output."""
    text = emulate(os.path.join(DRIVE, prg), seconds, until=lambda t: t.count("READY.") >= 3,
                   typed=typed)
    # The startup's ISO mode switch, $0F, echoes as an escape.
    return program_output(text.replace("\\X0F", "", 1))


def main():
    args = sys.argv[1:]
    seconds = 30
    if "--seconds" in args:
        seconds = int(args[args.index("--seconds") + 1])
        del args[args.index("--seconds"):args.index("--seconds") + 2]
    names = [a for a in args if not a.startswith("--")]
    if len(names) != 1:
        sys.exit(__doc__)
    if not os.path.exists(os.path.join(DRIVE, "UXC.PRG")):
        sys.exit("uxc: no build/UXC.PRG; run build.py first")
    started = time.time()
    result, screen = compile_source(names[0], seconds)
    print(screen)
    if result is None:
        sys.exit("uxc: no UXC.RESULT after %d s" % seconds)
    print("uxc: %s (%d s)" % (result, time.time() - started))
    fields = result.split(",")
    if fields[0] != "OK":
        sys.exit(1)
    if "--run" in args:
        out = run_prg(fields[1])
        if out is None:
            sys.exit("uxc: %s did not load" % fields[1])
        print(out)


if __name__ == "__main__":
    main()
