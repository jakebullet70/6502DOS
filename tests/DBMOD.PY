"""DBMOD's card: DBDOT's, with sys/EDIT.COM from the build for MODIFY COMMAND, and
sys/HELPXBASE.COM and sys/HELPDB.HLP for HELP. The card has no HELPDB.IDX."""
import os
import runpy

TESTS = os.path.dirname(os.path.abspath(__file__))
DOS = os.path.join(os.path.dirname(TESTS), "build", "sys")
FILES = ("EDIT.COM", "HELPXBASE.COM", "HELPDB.HLP")

_dbdot = runpy.run_path(os.path.join(TESTS, "DBDOT.PY"))["card"]


def card(image):
    files = {}
    for name in FILES:
        with open(os.path.join(DOS, name), "rb") as source:
            files["sys/" + name] = source.read()
    _dbdot(image, files)
