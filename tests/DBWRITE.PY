"""DBWRITE's check: NEW.DB on the card after the run is the table tools/db.py writes for the same
fields and records, but for the date, and no other .DB file was made."""

import datetime
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import db  # noqa: E402
import mksd  # noqa: E402

FOLDER = os.path.join(ROOT, "build", "tests", "DBWRITE")


def check(image):
    files = {path: data for path, data, when in mksd.read(image) if data is not None}
    tables = sorted(path for path in files if path.upper().endswith(".DB"))
    if tables != ["NEW.DB"]:
        return ["the .DB files are %s, not NEW.DB" % tables]
    os.makedirs(FOLDER, exist_ok=True)
    path = os.path.join(FOLDER, "NEW.DB")
    data = files["NEW.DB"]
    open(path, "wb").write(data)
    faults = db.read_table(path)[1]
    want = db.Table([("NAME", "C", 10), ("AGE", "N", 6, 1), ("OK", "L", 1), ("BORN", "D", 8)])
    want.append(["ADA L", 36.5, True, datetime.date(1815, 12, 10)])
    want.append(["BOB", None, None, None], deleted=True)
    want.append(["CY", -2.0, None, None])
    want = want.to_bytes()
    if data[:10] + data[13:] != want[:10] + want[13:]:
        faults.append("NEW.DB is not the table of db.py: %s" % data.hex())
    return faults
