"""DBIXMAKE's card: PEOPLE.DB of tools/db.py's make, and TALL.DB, 40 records of a 100-byte key, 4
keys a page, with two equal keys. Its check: each index the run builds is the index db.py builds
for the same fields, and the builds that fail leave no file."""

import datetime
import os
import random
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import db  # noqa: E402
import mksd  # noqa: E402

FOLDER = os.path.join(ROOT, "build", "tests", "DBIXMAKE")
CARD = os.path.join(FOLDER, "card")

# The indexes the run builds: (file, table, key fields).
BUILT = [("PNAME.IDX", "PEOPLE.DB", [2]), ("PCITY.IDX", "PEOPLE.DB", [3, 2]),
         ("PBAL.IDX", "PEOPLE.DB", [5]), ("PID.IDX", "PEOPLE.DB", [1]),
         ("TALL.IDX", "TALL.DB", [1])]
UNIQUE = ["PID.IDX"]


def tall():
    rand = random.Random(16)
    table = db.Table([("KEY", "C", 100), ("N", "N", 4)])
    keys = ["%06d" % rand.randrange(10 ** 6) + "+" * 94 for _ in range(40)]
    keys[22] = keys[6]
    for n, key in enumerate(keys):
        table.append([key, n])
    return table


def card(image):
    shutil.rmtree(FOLDER, ignore_errors=True)
    os.makedirs(CARD)
    db.make(FOLDER)
    shutil.copy(os.path.join(FOLDER, "PEOPLE.DB"), CARD)
    tall().write(os.path.join(CARD, "TALL.DB"))
    mksd.make(CARD, image, date=datetime.date(2026, 10, 13))


def check(image):
    files = {path: data for path, data, when in mksd.read(image) if data is not None}
    faults = []
    want = sorted(["PEOPLE.DB", "TALL.DB"] + [name for name, _, _ in BUILT])
    if sorted(files) != want:
        faults.append("the files are %s, not %s" % (sorted(files), want))
    tables = {"PEOPLE.DB": db.read_table(os.path.join(CARD, "PEOPLE.DB"))[0],
              "TALL.DB": db.read_table(os.path.join(CARD, "TALL.DB"))[0]}
    for name, table, numbers in BUILT:
        if name not in files:
            continue
        built = db.build_index(tables[table], numbers, name in UNIQUE).to_bytes()
        if files[name] != built:
            path = os.path.join(FOLDER, name)
            open(path, "wb").write(files[name])
            faults.append("%s is not the index of db.py; it is at %s" % (name, path))
    return faults
