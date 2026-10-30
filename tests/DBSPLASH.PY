"""DBSPLASH's card: DBDOT's, with sys/xbase/splash.dot from the folder card."""
import os
import runpy

TESTS = os.path.dirname(os.path.abspath(__file__))
SPLASH = os.path.join(os.path.dirname(TESTS), "card", "sys", "xbase", "splash.dot")

_dbdot = runpy.run_path(os.path.join(TESTS, "DBDOT.PY"))["card"]


def card(image):
    with open(SPLASH, "rb") as source:
        _dbdot(image, {"sys/xbase/splash.dot": source.read()})
