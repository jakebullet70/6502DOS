"""Run the BASIC test programs in sim65 and compare with the expected transcripts.

Each tests/NAME.bas is fed to `sim65 build/sim.bin echo` on stdin. The output (a session
transcript, because the `echo` argument makes BASIC echo its input) is compared with
tests/NAME.out. sim65 runs in build/, so files the tests write land there. Line endings and trailing spaces are ignored. Only failures are printed.

Usage: python tests/run.py [--update] [NAME ...]
  --update  write the actual output to NAME.out instead of comparing
"""
import difflib
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS = os.path.join(ROOT, "tests")
SIM65 = os.environ.get("SIM65", r"C:\8bitProgramming\cc65\bin\sim65")
BIN = os.path.join(ROOT, "build", "sim.bin")
CYCLES = "200000000"


def normalize(text):
    return "\n".join(line.rstrip() for line in text.replace("\r", "").split("\n")).rstrip() + "\n"


def run(name):
    with open(os.path.join(TESTS, name + ".bas"), "rb") as f:
        src = f.read().replace(b"\r", b"")  # a checkout may have CRLF
    p = subprocess.run([SIM65, "-x", CYCLES, BIN, "echo"], input=src,
                       capture_output=True, timeout=60, cwd=os.path.dirname(BIN))
    return p.returncode, normalize(p.stdout.decode("latin-1"))


def main(argv):
    update = "--update" in argv
    names = [a for a in argv if not a.startswith("--")]
    if not names:
        names = sorted(f[:-4] for f in os.listdir(TESTS) if f.endswith(".bas"))
    failed = 0
    for name in names:
        code, out = run(name)
        exp_path = os.path.join(TESTS, name + ".out")
        if update:
            with open(exp_path, "w", newline="\n") as f:
                f.write(out)
        if code != 0:
            print(f"FAIL {name}: sim65 exit code {code} (cycle limit or crash)")
            failed += 1
            continue
        if update:
            continue
        try:
            with open(exp_path, newline="") as f:
                exp = normalize(f.read())
        except FileNotFoundError:
            print(f"FAIL {name}: no {name}.out (run with --update)")
            failed += 1
            continue
        if out != exp:
            print(f"FAIL {name}")
            sys.stdout.writelines(difflib.unified_diff(
                exp.splitlines(True), out.splitlines(True), name + ".out", "actual"))
            failed += 1
    if not update:
        print(f"test: {len(names) - failed}/{len(names)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
