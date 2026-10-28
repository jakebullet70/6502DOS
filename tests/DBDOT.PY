"""DBDOT's card: CLUB.DB, 4 records with record 3 deleted, EMPTY.DB, no records, and DB.COM."""

import datetime
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import db  # noqa: E402
import mksd  # noqa: E402

FOLDER = os.path.join(ROOT, "build", "tests", "DBDOT")
PROGRAM = os.path.join(ROOT, "build", "bas", "DB.COM")


def card(image):
    shutil.rmtree(FOLDER, ignore_errors=True)
    os.makedirs(FOLDER)
    club = db.Table([("NAME", "C", 10), ("AGE", "N", 3), ("BAL", "N", 7, 2), ("MEMBER", "L", 1),
                     ("JOINED", "D", 8)])
    club.append(["ZOE", 30, 12.5, True, datetime.date(2024, 3, 1)])
    club.append(["AMY", 25, -4, False, None])
    club.append(["BOB", 41, None, None, datetime.date(2021, 12, 31)], deleted=True)
    club.append(["KAI", 19, 1000, True, datetime.date(2026, 1, 15)])
    club.write(os.path.join(FOLDER, "CLUB.DB"))
    db.Table([("NAME", "C", 10)]).write(os.path.join(FOLDER, "EMPTY.DB"))
    mksd.make(FOLDER, image, date=datetime.date(2026, 10, 13), extra=[PROGRAM])
