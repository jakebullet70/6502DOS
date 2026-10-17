"""Run a UXC compile with PROF.PRG sampling, and save the samples.

    python profrun.py SOURCE SECONDS SAMPLES.TXT

Each sample line is "bank lo hi" in hex: the RAM bank and GPC's codePtr ($28/$29), the p-code
address of the last branch target. profmap.py ranks them by label. PROF.PRG is built from
prof.s with ca65 and ld65 -C prof.cfg (UXDOS16's tools/cc65/bin).

DOS.UXI is copied from UXDOS16's src/bas/stock for a source that includes it.
"""
import os
import shutil
import subprocess
import sys
import threading
import time

sys.path.insert(0, r"C:\dev\UXCBASIC")
import uxc

HERE = os.path.dirname(os.path.abspath(__file__))
source, seconds, outfile = sys.argv[1], float(sys.argv[2]), sys.argv[3]
shutil.copyfile(r"c:\dev\CmdrX16\UXDOS16\src\bas\stock\DOS.UXI", os.path.join(uxc.DRIVE, "DOS.UXI"))
shutil.copyfile(os.path.join(HERE, "PROF.PRG"), os.path.join(uxc.DRIVE, "PROF.PRG"))
name = os.path.basename(source).upper()
shutil.copyfile(source, os.path.join(uxc.DRIVE, name))
with open(os.path.join(uxc.DRIVE, "UXC.INPUT"), "w", newline="\n") as out:
    out.write("%s\nUXC.RESULT\n" % name)
if os.path.exists(uxc.RESULT):
    os.remove(uxc.RESULT)
keys = os.path.join(uxc.DRIVE, "PROF.KEYS")
with open(keys, "w", encoding="latin-1", newline="\n") as out:
    out.write('LOAD"PROF.PRG",8,1\nSYS1792\nLOAD"UXC.PRG"\nRUN\n')

cmd = [uxc.EMU, "-rom", uxc.ROM, "-fsroot", uxc.DRIVE, "-bas", keys, "-warp", "-sound", "none"]
env = dict(os.environ, SDL_VIDEODRIVER="dummy")
emu = subprocess.Popen(cmd, cwd=uxc.DRIVE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       env=env, bufsize=1 << 16)
print("pid", emu.pid, flush=True)
values = []
other = []


def reader():
    for raw in emu.stdout:
        if raw.startswith(b"User debug 1: $"):
            values.append(int(raw[15:17], 16))
        elif len(other) < 20:
            other.append(raw)


thread = threading.Thread(target=reader, daemon=True)
thread.start()
started = time.time()
while time.time() - started < seconds and not os.path.exists(uxc.RESULT):
    time.sleep(0.1)
took = time.time() - started
time.sleep(0.3)
emu.kill()
emu.wait(timeout=5)
thread.join(timeout=5)
result = open(uxc.RESULT, "rb").read().decode("latin-1").strip() if os.path.exists(uxc.RESULT) else None
n = len(values) // 3
with open(outfile, "w", encoding="utf-8") as out:
    for i in range(n):
        out.write("%02x %02x %02x\n" % tuple(values[3 * i:3 * i + 3]))
print("%.1f s, result %s, %d samples, %d stray bytes" % (took, result, n, len(values) % 3))
for raw in other:
    print("other:", raw[:100])
