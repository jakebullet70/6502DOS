"""DBMOD's card: DBDOT's, with DOS/EDIT.COM from the build for MODIFY COMMAND."""
import os
import runpy

TESTS = os.path.dirname(os.path.abspath(__file__))
EDITOR = os.path.join(os.path.dirname(TESTS), "build", "DOS", "EDIT.COM")

_dbdot = runpy.run_path(os.path.join(TESTS, "DBDOT.PY"))["card"]


def card(image):
    with open(EDITOR, "rb") as editor:
        _dbdot(image, {"DOS/EDIT.COM": editor.read()})
