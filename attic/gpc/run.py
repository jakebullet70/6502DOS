"""Run a built program in x16emu from build/, or from disk/ with --disk.

    python run.py [NAME] [--seconds N]    headless: warp, no video, CHROUT echo to build/RUN.LOG
    python run.py [NAME] --window         a normal emulator window, for hands-on use
    python run.py [NAME] --disk ...       the same, with disk/ as the drive

NAME defaults to UXC. A headless run is killed after N seconds (default 10). The log is
build/RUN.LOG, with --disk too. It is printed raw, and the exit status is 1 when a line starts
with "?" or holds "ERROR".
"""

import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
GPC_REPO = os.environ.get("GPC_REPO", r"C:\dev\CmdrX16\dos_tools\x16-blitz-compiler")
EMUDIR = os.path.join(GPC_REPO, "bin", "x16emu")
EMU = os.path.join(EMUDIR, "x16emu.exe")
ROM = os.path.join(EMUDIR, "rom.bin")
BUILD = os.path.join(HERE, "build")


def main():
    args = sys.argv[1:]
    window = "--window" in args
    drive = os.path.join(HERE, "disk") if "--disk" in args else BUILD
    seconds = 10
    if "--seconds" in args:
        seconds = int(args[args.index("--seconds") + 1])
        del args[args.index("--seconds"):args.index("--seconds") + 2]
    names = [a for a in args if not a.startswith("--")]
    name = names[0].upper() if names else "UXC"
    prg = os.path.join(drive, name + ".PRG")
    if not os.path.exists(prg):
        sys.exit("run: no %s/%s.PRG; run build.py first" % (os.path.basename(drive), name))

    cmd = [EMU, "-rom", ROM, "-fsroot", drive, "-prg", prg, "-run"]
    if window:
        # -noemucmdkeys: Ctrl+R, Ctrl+V and the rest reach the program, not the emulator.
        subprocess.run(cmd + ["-scale", "2", "-noemucmdkeys"], cwd=drive)
        return

    env = dict(os.environ, SDL_VIDEODRIVER="dummy")
    log = os.path.join(BUILD, "RUN.LOG")
    with open(log, "wb") as out:
        # Kill by this handle only: never by image name, other emulators may be running.
        emu = subprocess.Popen(cmd + ["-warp", "-sound", "none", "-echo", "iso"],
                               cwd=drive, stdout=out, stderr=subprocess.STDOUT, env=env)
        time.sleep(seconds)
        emu.kill()
        try:
            emu.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass
    text = open(log, "rb").read().decode("latin-1").replace("\r\n", "\n").replace("\r", "\n")
    sys.stdout.reconfigure(errors="replace")
    print(text)
    bad = [l for l in text.split("\n") if l.startswith("?") or "ERROR" in l]
    sys.exit(1 if bad else 0)


main()
