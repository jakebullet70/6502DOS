"""DBPACK's check: PACK.DB on the card after the run is the table tools/db.py writes for the same
field and the records A and C, but for the date, and no PACK.D$ or other .DB file is left."""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import db  # noqa: E402
import mksd  # noqa: E402

FOLDER = os.path.join(ROOT, "build", "tests", "DBPACK")


def check(image):
    files = {path: data for path, data, when in mksd.read(image) if data is not None}
    tables = sorted(path for path in files if path.upper().endswith((".DB", ".D$")))
    if tables != ["PACK.DB"]:
        return ["the .DB and .D$ files are %s, not PACK.DB" % tables]
    os.makedirs(FOLDER, exist_ok=True)
    path = os.path.join(FOLDER, "PACK.DB")
    data = files["PACK.DB"]
    open(path, "wb").write(data)
    faults = db.read_table(path)[1]
    want = db.Table([("NAME", "C", 4)])
    want.append(["A"])
    want.append(["C"])
    want = want.to_bytes()
    if data[:10] + data[13:] != want[:10] + want[13:]:
        faults.append("PACK.DB is not the table of db.py: %s" % data.hex())
    return faults
