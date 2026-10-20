"""Cycle benchmark for the sim build.

Each case runs `FOR I=1 TO N:<body>:NEXT` under `sim65 -c` and reports the cycles one pass of
<body> costs: (cycles with body - cycles with an empty loop) / N. The cost includes the ':'
before the body. The loop row is the cost of one empty FOR/NEXT pass.

Usage: python tests/bench.py [N]   (default N=1000)
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIM65 = os.environ.get("SIM65", r"C:\8bitProgramming\cc65\bin\sim65")
BIN = os.path.join(ROOT, "build", "sim.bin")

SETUP = '10 A=0:B=2:C=3:A%=0:B%=2:C%=3:A$="":B$="HELLO":C$="AB":DIM D(10)'
VARS = [f"{v}=0" for v in "ABCDEFGHJKLMNOPQRSTUVWXY"]
VARS25 = "10 " + ":".join(VARS[:12]) + "\n11 " + ":".join(VARS[12:])
FILLER = [f"{100 + i} REM FILLER LINE" for i in range(100)]

# (label, body, extra lines before the loop, extra lines after the loop)
CASES = [
    ("A=B", "A=B", None, None),
    ("A=1", "A=1", None, None),
    ("A=12345", "A=12345", None, None),
    ("A=1.5", "A=1.5", None, None),
    ("A=A+1", "A=A+1", None, None),
    ("A=B+1", "A=B+1", None, None),
    ("A=B+C", "A=B+C", None, None),
    ("A=B*C", "A=B*C", None, None),
    ("A=B/C", "A=B/C", None, None),
    ("A=B AND C", "A=B AND C", None, None),
    ("A%=B%", "A%=B%", None, None),
    ("A%=A%+1", "A%=A%+1", None, None),
    ("A=D(5)", "A=D(5)", None, None),
    ("IF A=A THEN C=3", "IF A=A THEN C=3", None, None),
    ("A=SQR(B)", "A=SQR(B)", None, None),
    ("A=SIN(B)", "A=SIN(B)", None, None),
    ("A=PEEK(1000)", "A=PEEK(1000)", None, None),
    ("POKE 1000,1", "POKE 1000,1", None, None),
    ("A=LEN(B$)", "A=LEN(B$)", None, None),
    ("A$=B$", "A$=B$", None, None),
    ("A$=B$+C$", "A$=B$+C$", None, None),
    ("A$=LEFT$(B$,2)", "A$=LEFT$(B$,2)", None, None),
    ("Z=Z+1, Z first of 25", "Z=Z+1", "9 Z=0\n" + VARS25, None),
    ("Z=Z+1, Z last of 25", "Z=Z+1", VARS25 + "\n12 Z=0", None),
    ("GOSUB, next line", "GOSUB 9000", None, []),
    ("GOSUB, 100 lines on", "GOSUB 9000", None, FILLER),
]


def cycles(lines):
    src = ("\n".join(lines) + "\nRUN\n").encode()
    p = subprocess.run([SIM65, "-c", "-x", "2000000000", BIN], input=src,
                       capture_output=True, timeout=300)
    m = re.search(rb"(\d+) cycles", p.stdout)
    if p.returncode != 0 or not m or b"ERROR" in p.stdout:
        sys.exit(f"run failed:\n{p.stdout.decode('latin-1')}")
    return int(m.group(1))


def program(n, body, setup, tail):
    loop = f"20 FOR I=1 TO {n}" + (f":{body}" if body else "") + ":NEXT"
    lines = [setup or SETUP, loop]
    if tail is not None:
        lines += ["30 END"] + tail + ["9000 RETURN"]
    return lines


def main(argv):
    n = int(argv[0]) if argv else 1000
    empty = cycles(program(n, None, None, None))
    loop = (empty - cycles(program(1, None, None, None))) / (n - 1)
    print(f"{'empty FOR/NEXT pass':28}{loop:8.0f}")
    for label, body, setup, tail in CASES:
        base = cycles(program(n, None, setup, tail))
        per = (cycles(program(n, body, setup, tail)) - base) / n
        print(f"{label:28}{per:8.0f}")


if __name__ == "__main__":
    main(sys.argv[1:])
