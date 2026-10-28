"""DBIXEDIT's card: PEOPLE.DB, PNAME.IDX and PID.IDX of tools/db.py's make, and TALL.DB, 40
records of a 100-byte key with two equal keys, with TALL.IDX, and TINY.DB, the keys A to E, with
TINY.IDX. Its check: each table holds the
records the run wrote, and each index is good against its table."""

import datetime
import os
import random
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import db  # noqa: E402
import mksd  # noqa: E402

FOLDER = os.path.join(ROOT, "build", "tests", "DBIXEDIT")
CARD = os.path.join(FOLDER, "card")
OUT = os.path.join(FOLDER, "out")
FILES = ["PEOPLE.DB", "PNAME.IDX", "PID.IDX", "TALL.DB", "TALL.IDX", "TINY.DB", "TINY.IDX"]


def tall():
    rand = random.Random(16)
    table = db.Table([("KEY", "C", 100), ("N", "N", 4)])
    keys = ["%06d" % rand.randrange(10 ** 6) + "+" * 94 for _ in range(40)]
    keys[22] = keys[6]
    for n, key in enumerate(keys):
        table.append([key, n])
    return table


def tiny(keys="ABCDE"):
    table = db.Table([("KEY", "C", 100), ("N", "N", 4)])
    for n, key in enumerate(keys):
        table.append([key, n])
    return table


def card(image):
    shutil.rmtree(FOLDER, ignore_errors=True)
    os.makedirs(CARD)
    db.make(FOLDER)
    for name in FILES[:3]:
        shutil.copy(os.path.join(FOLDER, name), CARD)
    table = tall()
    table.write(os.path.join(CARD, "TALL.DB"))
    db.build_index(table, [1]).write(os.path.join(CARD, "TALL.IDX"))
    table = tiny()
    table.write(os.path.join(CARD, "TINY.DB"))
    db.build_index(table, [1]).write(os.path.join(CARD, "TINY.IDX"))
    mksd.make(CARD, image, date=datetime.date(2026, 10, 13))


def people():
    """PEOPLE.DB as the run leaves it: the first name becomes ZZZ, record 41 is added, and the
    deleted records are packed away."""
    table = db.read_table(os.path.join(CARD, "PEOPLE.DB"))[0]
    name = table.fields[1]
    first = min((db.record_key(table, [2], r), n) for n, r in enumerate(table.records))[1]
    record = table.records[first]
    table.records[first] = (record[:name.offset] + b"ZZZ".ljust(name.length)
                            + record[name.offset + name.length:])
    table.append([1000, "AAA", None, None, None, None, None])
    table.records = [r for r in table.records if r[:1] != b"*"]
    return table


def tall_after():
    """TALL.DB as the run leaves it: record n's key Z and the byte 126 - n."""
    table = tall()
    key = table.fields[0]
    for n, record in enumerate(table.records, 1):
        text = (b"Z" + bytes([126 - n])).ljust(key.length)
        table.records[n - 1] = record[:key.offset] + text + record[key.offset + key.length:]
    return table


def check(image):
    files = {path: data for path, data, when in mksd.read(image) if data is not None}
    faults = []
    if sorted(files) != sorted(FILES):
        faults.append("the files are %s, not %s" % (sorted(files), sorted(FILES)))
    os.makedirs(OUT, exist_ok=True)
    for name in FILES:
        if name in files:
            open(os.path.join(OUT, name), "wb").write(files[name])
    for name, want, indexes in (("PEOPLE.DB", people(), ["PNAME.IDX", "PID.IDX"]),
                                ("TALL.DB", tall_after(), ["TALL.IDX"]),
                                ("TINY.DB", tiny("AECDB"), ["TINY.IDX"])):
        if name not in files:
            continue
        table, table_faults = db.read_table(os.path.join(OUT, name))
        faults += ["%s: %s" % (name, fault) for fault in table_faults]
        if table.records != want.records:
            faults.append("%s: the records differ from the run's; it is at %s" % (name, OUT))
        for index in indexes:
            if index in files:
                faults += ["%s: %s" % (index, fault)
                           for fault in db.check_index(os.path.join(OUT, index), table)]
    return faults
