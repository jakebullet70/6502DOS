"""DBPATH's card: DBDOT's, with LIB\\HI.PRG, LIB2\\HI.PRG, LIB2\\HI2.PRG and LIB2\\PEOPLE.DB, a
table of 1 record, for SET PATH TO."""
import os
import runpy
import sys

TESTS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(TESTS), "tools"))
import db  # noqa: E402

_dbdot = runpy.run_path(os.path.join(TESTS, "DBDOT.PY"))["card"]


def card(image):
    folder = os.path.join(os.path.dirname(TESTS), "build", "tests", "DBPATH")
    os.makedirs(folder, exist_ok=True)
    people = db.Table([("NAME", "C", 8)])
    people.append(["ANN"])
    path = os.path.join(folder, "PEOPLE.DB")
    people.write(path)
    with open(path, "rb") as source:
        table = source.read()
    _dbdot(image, {
        "LIB/HI.PRG": b'? "hi lib"\n',
        "LIB2/HI.PRG": b'? "hi lib2"\n',
        "LIB2/HI2.PRG": b'? "hi2 lib2"\n',
        "LIB2/PEOPLE.DB": table,
    })
