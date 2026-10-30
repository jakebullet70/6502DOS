"""DBMOD's card: DBDOT's, with DOS/EDIT.COM from the build for MODIFY COMMAND, and
DOS/HELPDB.COM and DOS/HELPDB.HLP for HELP. The card has no HELPDB.IDX."""
import os
import runpy

TESTS = os.path.dirname(os.path.abspath(__file__))
DOS = os.path.join(os.path.dirname(TESTS), "build", "DOS")
FILES = ("EDIT.COM", "HELPDB.COM", "HELPDB.HLP")

_dbdot = runpy.run_path(os.path.join(TESTS, "DBDOT.PY"))["card"]


def card(image):
    files = {}
    for name in FILES:
        with open(os.path.join(DOS, name), "rb") as source:
            files["DOS/" + name] = source.read()
    _dbdot(image, files)
