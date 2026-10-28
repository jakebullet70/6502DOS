"""DBREAD's card: in its root the tables and indexes of tools/db.py's make, and:

- WIDE.DB, 4 fields, 100 records of 1000 bytes, so record 100 starts past 64 KB;
- NOTDB.DB, text that is not a table.
"""

import datetime
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import db  # noqa: E402
import mksd  # noqa: E402

FOLDER = os.path.join(ROOT, "build", "tests", "DBREAD")


def card(image):
    shutil.rmtree(FOLDER, ignore_errors=True)
    db.make(FOLDER)
    wide = db.Table([("A", "C", 254), ("B", "C", 254), ("C", "C", 254), ("D", "C", 237)])
    for n in range(1, 101):
        wide.append(["A%d" % n, "B%d" % n, "C%d" % n, "RECORD %d" % n])
    wide.write(os.path.join(FOLDER, "WIDE.DB"))
    open(os.path.join(FOLDER, "NOTDB.DB"), "wb").write(b"THIS IS NOT A TABLE\r\n")
    mksd.make(FOLDER, image, date=datetime.date(2026, 10, 13))
