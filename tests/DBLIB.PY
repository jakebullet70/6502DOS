"""DBLIB's card: the tables and indexes of tools/db.py's make, and DBLIB.COM. Its check: NEW.DB
holds the run's 2 records, and NEWIX.IDX is good against it; no BAD.IDX is left."""

import datetime
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import db  # noqa: E402
import mksd  # noqa: E402

FOLDER = os.path.join(ROOT, "build", "tests", "DBLIB")
CARD = os.path.join(FOLDER, "card")
OUT = os.path.join(FOLDER, "out")
PROGRAM = os.path.join(ROOT, "build", "tests", "DBLIB.COM")


def card(image):
    shutil.rmtree(FOLDER, ignore_errors=True)
    db.make(CARD)
    mksd.make(CARD, image, date=datetime.date(2026, 10, 13), extra=[PROGRAM])


def check(image):
    files = {path: data for path, data, when in mksd.read(image) if data is not None}
    faults = []
    if "BAD.IDX" in files:
        faults.append("BAD.IDX is left")
    for name in ("NEW.DB", "NEWIX.IDX"):
        if name not in files:
            return faults + ["%s is missing" % name]
    os.makedirs(OUT, exist_ok=True)
    for name in ("NEW.DB", "NEWIX.IDX"):
        open(os.path.join(OUT, name), "wb").write(files[name])
    want = db.Table([("NAME", "C", 10), ("CITY", "C", 8), ("AGE", "N", 3)])
    want.append(["ZOE", "PARIS", 30])
    want.append(["AMY", "ROME", -5])
    table, table_faults = db.read_table(os.path.join(OUT, "NEW.DB"))
    faults += ["NEW.DB: %s" % fault for fault in table_faults]
    if table.records != want.records:
        faults.append("NEW.DB: the records differ from the run's; it is at %s" % OUT)
    faults += ["NEWIX.IDX: %s" % fault
               for fault in db.check_index(os.path.join(OUT, "NEWIX.IDX"), table)]
    return faults
