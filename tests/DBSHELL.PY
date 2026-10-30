"""DBSHELL's card: DBDOT's, with ROMSHELL.COM in the root, for !, SHELL and RUN."""
import os
import runpy

TESTS = os.path.dirname(os.path.abspath(__file__))
_dbdot = runpy.run_path(os.path.join(TESTS, "DBDOT.PY"))["card"]


def card(image):
    with open(os.path.join(os.path.dirname(TESTS), "build", "bas", "ROMSHELL.COM"), "rb") as stub:
        _dbdot(image, {"ROMSHELL.COM": stub.read()})
