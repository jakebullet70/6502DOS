"""DBINDEX's card: in its root the tables and indexes of tools/db.py's make."""

import datetime
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import db  # noqa: E402
import mksd  # noqa: E402

FOLDER = os.path.join(ROOT, "build", "tests", "DBINDEX")


def card(image):
    shutil.rmtree(FOLDER, ignore_errors=True)
    db.make(FOLDER)
    mksd.make(FOLDER, image, date=datetime.date(2026, 10, 13))
