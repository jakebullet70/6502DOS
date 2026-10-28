r"""The DB reference: writes, reads and checks the .DB tables and .IDX indexes of docs/DB.PLAN.md.

    python tools/db.py dump FILE
    python tools/db.py check TABLE.DB [INDEX.IDX ...]
    python tools/db.py index TABLE.DB INDEX.IDX FIELD[,FIELD ...] [-u]
    python tools/db.py make FOLDER

dump prints a table's header, fields and records, or an index's header and its pages from the
root. check reads a table, and each index against it, and prints each fault; the exit status
is 1 when it found one. index builds an index on up to 4 fields, by name; -u makes its keys
unique. make writes the test tables into FOLDER: a test's NAME.PY calls make() for its card.

An index is built by inserting the records in record order into an empty leaf, page 1. A full
page splits: its entries and the new one, n in all, keep the first n // 2 in the page, send
entry n // 2 up, and move the rest to a new page. A new page is the first free page, else the
page after the last. A root that splits gets a new root above it.
"""

import datetime
import os
import random
import struct
import sys

HEADER = 16
FIELD = 16
PAGE = 512
MAX_FIELDS = 32
MAX_RECORD = 1000
MAX_RECORDS = 65535
MAX_KEY = 100
MAX_KEY_FIELDS = 4
MAX_DEPTH = 10
UNIQUE = 0x01
LEAF = 0x01
LENGTHS = {"C": (1, 254), "N": (1, 10), "L": (1, 1), "D": (8, 8)}


class DBError(Exception):
    pass


class Field:
    def __init__(self, name, type_, length, decimals=0, offset=0):
        self.name = name
        self.type = type_
        self.length = length
        self.decimals = decimals
        self.offset = offset

    def entry(self):
        name = self.name.encode("ascii").ljust(11, b"\0")
        return name + struct.pack("<cBBH", self.type.encode("ascii"), self.length, self.decimals,
                                  self.offset)

    @classmethod
    def parse(cls, data):
        name = data[0:11].rstrip(b"\0").decode("latin-1")
        type_, length, decimals, offset = struct.unpack("<cBBH", data[11:16])
        return cls(name, type_.decode("latin-1"), length, decimals, offset)


def field_faults(field):
    faults = []
    name = field.name
    if not 1 <= len(name) <= 10 or any(c not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_" for c in name):
        faults.append("field %r: the name is not 1 to 10 of A-Z, 0-9 and _" % name)
    if field.type not in LENGTHS:
        faults.append("field %s: the type %r is not C, N, L or D" % (name, field.type))
        return faults
    low, high = LENGTHS[field.type]
    if not low <= field.length <= high:
        faults.append("field %s: the length %d is not %d to %d" % (name, field.length, low, high))
    if field.type == "N":
        if field.decimals and field.decimals > field.length - 2:
            faults.append("field %s: %d decimals do not fit a length of %d"
                          % (name, field.decimals, field.length))
    elif field.decimals:
        faults.append("field %s: decimals on a %s field" % (name, field.type))
    return faults


class Table:
    """A table in memory: fields, and records as bytes, the delete flag first."""

    def __init__(self, fields, records=(), date=(2026, 10, 28)):
        self.fields = []
        offset = 1
        for name, type_, length, *decimals in fields:
            field = Field(name, type_, length, decimals[0] if decimals else 0, offset)
            faults = field_faults(field)
            if faults:
                raise DBError(faults[0])
            self.fields.append(field)
            offset += length
        if not 1 <= len(self.fields) <= MAX_FIELDS:
            raise DBError("a table has 1 to %d fields" % MAX_FIELDS)
        if len({f.name for f in self.fields}) != len(self.fields):
            raise DBError("two fields share a name")
        self.record_length = offset
        if self.record_length > MAX_RECORD:
            raise DBError("the record is %d bytes, past %d" % (offset, MAX_RECORD))
        self.records = list(records)
        self.date = date

    def field(self, name):
        for number, field in enumerate(self.fields, 1):
            if field.name == name.upper():
                return number
        raise DBError("no field %s" % name)

    def append(self, values, deleted=False):
        """values: one per field. C: text; N: a number or None; L: True, False or None; D: a
        datetime.date or None."""
        if len(self.records) == MAX_RECORDS:
            raise DBError("the table is full")
        if len(values) != len(self.fields):
            raise DBError("%d values for %d fields" % (len(values), len(self.fields)))
        record = b"*" if deleted else b" "
        for field, value in zip(self.fields, values):
            record += field_text(field, value)
        self.records.append(record)
        return len(self.records)

    def header_length(self):
        return HEADER + FIELD * len(self.fields) + 1

    def to_bytes(self):
        year, month, day = self.date
        header = b"DB" + struct.pack("<BBHHH3B3x", 1, len(self.fields), len(self.records),
                                     self.header_length(), self.record_length, year - 2000,
                                     month, day)
        fields = b"".join(field.entry() for field in self.fields) + b"\r"
        return header + fields + b"".join(self.records)

    def write(self, path):
        with open(path, "wb") as out:
            out.write(self.to_bytes())


def field_text(field, value):
    if field.type == "C":
        text = (value or "").encode("latin-1")
        if len(text) > field.length:
            raise DBError("field %s: %r is past %d" % (field.name, value, field.length))
        return text.ljust(field.length)
    if field.type == "N":
        if value is None:
            return b" " * field.length
        text = ("%.*f" % (field.decimals, value)).encode("ascii")
        if text.strip(b"-0.") == b"":
            text = text.lstrip(b"-")
        if len(text) > field.length:
            raise DBError("field %s: %s is past %d" % (field.name, text, field.length))
        return text.rjust(field.length)
    if field.type == "L":
        return {True: b"T", False: b"F", None: b"?"}[value]
    if value is None:
        return b" " * 8
    return value.strftime("%Y%m%d").encode("ascii")


def text_faults(field, text):
    """The faults of a field's text in a record."""
    if field.type == "C":
        return [] if all(32 <= c < 127 or c >= 160 for c in text) else ["a control byte"]
    if field.type == "L":
        return [] if text in (b"T", b"F", b"?") else ["not T, F or ?"]
    if field.type == "D":
        if text == b" " * 8:
            return []
        try:
            datetime.datetime.strptime(text.decode("ascii"), "%Y%m%d")
        except (UnicodeDecodeError, ValueError):
            return ["not YYYYMMDD"]
        return []
    body = text.lstrip(b" ")
    if not body:
        return []
    if text[-1:] == b" ":
        return ["not right-aligned"]
    digits = body[1:] if body[:1] == b"-" else body
    whole, dot, fraction = digits.partition(b".")
    if not whole or not whole.isdigit() or (fraction and not fraction.isdigit()):
        return ["not a number"]
    if len(fraction) != field.decimals or bool(dot) != bool(field.decimals):
        return ["not %d decimals" % field.decimals]
    return []


def read_table(path):
    """A Table from a file, and the faults found reading it."""
    data = open(path, "rb").read()
    faults = []
    if len(data) < HEADER or data[0:2] != b"DB":
        raise DBError("%s: no DB magic" % path)
    version, count, records, header_length, record_length = struct.unpack("<BBHHH", data[2:10])
    year, month, day = data[10:13]
    if version != 1:
        faults.append("the version is %d, not 1" % version)
    if data[13:16] != b"\0\0\0":
        faults.append("bytes 13 to 15 are not 0")
    try:
        datetime.date(2000 + year, month, day)
    except ValueError:
        faults.append("the date %d-%d-%d is not a date" % (2000 + year, month, day))
    if not 1 <= count <= MAX_FIELDS:
        raise DBError("%s: %d fields" % (path, count))
    if header_length != HEADER + FIELD * count + 1:
        faults.append("the header's length is %d, not %d" % (header_length, HEADER + FIELD * count + 1))
    if data[HEADER + FIELD * count:HEADER + FIELD * count + 1] != b"\r":
        faults.append("no $0D after the field table")
    fields = [Field.parse(data[HEADER + FIELD * n:HEADER + FIELD * (n + 1)]) for n in range(count)]
    offset = 1
    for field in fields:
        faults += field_faults(field)
        if field.offset != offset:
            faults.append("field %s: the offset is %d, not %d" % (field.name, field.offset, offset))
        offset += field.length
    if record_length != offset:
        faults.append("the record's length is %d, not %d" % (record_length, offset))
    if record_length > MAX_RECORD:
        faults.append("the record's length %d is past %d" % (record_length, MAX_RECORD))
    want = header_length + records * record_length
    if len(data) != want:
        faults.append("the file is %d bytes, not %d" % (len(data), want))
    table = Table.__new__(Table)
    table.fields = fields
    table.record_length = record_length
    table.date = (2000 + year, month, day)
    table.records = []
    for n in range(records):
        record = data[header_length + n * record_length:header_length + (n + 1) * record_length]
        table.records.append(record)
        if len(record) < record_length:
            break
        if record[0:1] not in b" *":
            faults.append("record %d: the delete flag is %r" % (n + 1, record[0:1]))
        for field in fields:
            for fault in text_faults(field, record[field.offset:field.offset + field.length]):
                faults.append("record %d, field %s: %s" % (n + 1, field.name, fault))
    return table, faults


def n_key(text):
    """An N field's text as it sorts in a key. A space and the . count as 0."""
    digits = text.replace(b" ", b"0").replace(b".", b"0")
    if b"-" not in digits:
        return digits
    digits = digits.replace(b"-", b"")
    return b"-" + bytes(ord("9") - c + ord("0") for c in digits)


def key_length(table, numbers):
    return min(MAX_KEY, sum(table.fields[n - 1].length for n in numbers))


def record_key(table, numbers, record):
    key = b""
    for n in numbers:
        field = table.fields[n - 1]
        text = record[field.offset:field.offset + field.length]
        key += n_key(text) if field.type == "N" else text
    return key[:MAX_KEY]


class Node:
    def __init__(self, leaf, below=0, entries=None):
        self.leaf = leaf
        self.below = below
        # (key, record, page of the keys above it)
        self.entries = entries or []


class Index:
    """An index in memory: pages 1 and up as Nodes, None for a free page."""

    def __init__(self, numbers, key_length, unique=False):
        if not 1 <= len(numbers) <= MAX_KEY_FIELDS:
            raise DBError("a key has 1 to %d fields" % MAX_KEY_FIELDS)
        self.numbers = list(numbers)
        self.key_length = key_length
        self.unique = unique
        self.capacity = (PAGE - 4) // (key_length + 4)
        self.pages = {1: Node(True)}
        self.root = 1
        self.count = 2
        self.free = 0

    def new_page(self, node):
        if self.free:
            page = self.free
            self.free = self.pages[page]
        else:
            page = self.count
            self.count += 1
        self.pages[page] = node
        return page

    def find(self, key):
        page = self.root
        while page:
            node = self.pages[page]
            for k, _, _ in node.entries:
                if k == key:
                    return True
            below = node.below
            for k, _, child in node.entries:
                if k < key:
                    below = child
            page = 0 if node.leaf else below
        return False

    def insert(self, key, record):
        key = key.ljust(self.key_length, b"\0")[:self.key_length]
        if self.unique and self.find(key):
            raise DBError("record %d: the key %r is not unique" % (record, key))
        up = self._insert(self.root, (key, record))
        if up:
            entry, right = up
            self.root = self.new_page(Node(False, self.root, [(entry[0], entry[1], right)]))

    def _insert(self, page, item):
        node = self.pages[page]
        at = sum(1 for k, r, _ in node.entries if (k, r) < item)
        if node.leaf:
            node.entries.insert(at, (item[0], item[1], 0))
        else:
            child = node.below if at == 0 else node.entries[at - 1][2]
            up = self._insert(child, item)
            if not up:
                return None
            entry, right = up
            node.entries.insert(at, (entry[0], entry[1], right))
        if len(node.entries) <= self.capacity:
            return None
        middle = len(node.entries) // 2
        key, record, child = node.entries[middle]
        right = Node(node.leaf, child, node.entries[middle + 1:])
        node.entries = node.entries[:middle]
        return (key, record), self.new_page(right)

    def to_bytes(self):
        fields = bytes(self.numbers).ljust(MAX_KEY_FIELDS, b"\0")
        header = b"IX" + struct.pack("<BBHHHB", 1, self.key_length, self.root, self.count,
                                     self.free, len(self.numbers))
        header += fields + bytes([UNIQUE if self.unique else 0])
        out = [header.ljust(PAGE, b"\0")]
        for page in range(1, self.count):
            node = self.pages[page]
            if not isinstance(node, Node):
                out.append(struct.pack("<H", node).ljust(PAGE, b"\0"))
                continue
            data = struct.pack("<BBH", len(node.entries), LEAF if node.leaf else 0, node.below)
            for key, record, child in node.entries:
                data += key + struct.pack("<HH", record, child)
            out.append(data.ljust(PAGE, b"\0"))
        return b"".join(out)

    def write(self, path):
        with open(path, "wb") as out:
            out.write(self.to_bytes())


def build_index(table, numbers, unique=False):
    index = Index(numbers, key_length(table, numbers), unique)
    for n, record in enumerate(table.records, 1):
        index.insert(record_key(table, numbers, record), n)
    return index


def read_index(path):
    """The header as a dict, and the pages' bytes, page 0 first."""
    data = open(path, "rb").read()
    if len(data) < PAGE or data[0:2] != b"IX":
        raise DBError("%s: no IX magic" % path)
    version, key_length, root, count, free, fields = struct.unpack("<BBHHHB", data[2:11])
    header = dict(version=version, key_length=key_length, root=root, count=count, free=free,
                  numbers=list(data[11:11 + fields]) if fields <= 4 else [], fields=fields,
                  rest=data[11 + min(fields, 4):15], flags=data[15], tail=data[16:PAGE])
    pages = [data[n:n + PAGE] for n in range(0, len(data), PAGE)]
    return header, pages


def parse_node(page, key_length):
    count, flags, below = struct.unpack("<BBH", page[0:4])
    entries = []
    at = 4
    for _ in range(count):
        key = page[at:at + key_length]
        record, child = struct.unpack("<HH", page[at + key_length:at + key_length + 4])
        entries.append((key, record, child))
        at += key_length + 4
    return Node(bool(flags & LEAF), below, entries), flags, at


def check_index(path, table):
    header, pages = read_index(path)
    faults = []
    size = os.path.getsize(path)
    if header["version"] != 1:
        faults.append("the version is %d, not 1" % header["version"])
    if not 1 <= header["fields"] <= MAX_KEY_FIELDS:
        return faults + ["%d key fields" % header["fields"]]
    if any(header["rest"]) or any(header["tail"]):
        faults.append("page 0 is not 0 past the key fields")
    if header["flags"] & ~UNIQUE:
        faults.append("the flags $%02X have unknown bits" % header["flags"])
    numbers = header["numbers"]
    if any(not 1 <= n <= len(table.fields) for n in numbers):
        return faults + ["the key fields %s are not fields of the table" % numbers]
    length = key_length(table, numbers)
    if header["key_length"] != length:
        return faults + ["the key's length is %d, not %d" % (header["key_length"], length)]
    count = header["count"]
    if size != PAGE * count:
        faults.append("the file is %d bytes, not %d pages" % (size, count))
    capacity = (PAGE - 4) // (length + 4)
    seen = set()
    leaves = set()
    found = []

    def walk(page, low, high, depth):
        if not 1 <= page < min(count, len(pages)):
            faults.append("a page number %d is out of range" % page)
            return
        if page in seen:
            faults.append("page %d is reached twice" % page)
            return
        seen.add(page)
        node, flags, end = parse_node(pages[page], length)
        if flags & ~LEAF:
            faults.append("page %d: the flags $%02X have unknown bits" % (page, flags))
        if len(node.entries) > capacity or end > PAGE:
            faults.append("page %d: %d keys, past %d" % (page, len(node.entries), capacity))
            return
        if any(pages[page][end:]):
            faults.append("page %d: not 0 past its entries" % page)
        if depth > MAX_DEPTH:
            faults.append("page %d is %d levels down, past %d" % (page, depth, MAX_DEPTH))
        if node.leaf:
            leaves.add(depth)
            if node.below or any(child for _, _, child in node.entries):
                faults.append("page %d: a leaf with a page below" % page)
        elif not node.entries:
            faults.append("page %d: a node with no keys" % page)
        last = low
        if not node.leaf:
            walk(node.below, low, node.entries[0][:2] if node.entries else high, depth + 1)
        for n, (key, record, child) in enumerate(node.entries):
            item = (key, record)
            if (last and item <= last) or (high and item >= high):
                faults.append("page %d: entry %d is out of order" % (page, n + 1))
            found.append(item)
            last = item
            if not node.leaf:
                after = node.entries[n + 1][:2] if n + 1 < len(node.entries) else high
                walk(child, item, after, depth + 1)

    walk(header["root"], None, None, 1)
    if len(leaves) > 1:
        faults.append("the leaves are at depths %s" % sorted(leaves))
    free = header["free"]
    while free:
        if not 1 <= free < count or free in seen:
            faults.append("the free page %d is out of range or in use" % free)
            break
        seen.add(free)
        free = struct.unpack("<H", pages[free][0:2])[0]
    lost = set(range(1, count)) - seen
    if lost:
        faults.append("pages %s are neither in the tree nor free" % sorted(lost))
    want = sorted((record_key(table, numbers, record).ljust(length, b"\0"), n)
                  for n, record in enumerate(table.records, 1))
    if sorted(found) != want:
        missing = set(want) - set(found)
        extra = set(found) - set(want)
        faults.append("the keys differ from the table: %d missing, %d extra"
                      % (len(missing), len(extra)))
    if header["flags"] & UNIQUE and len({k for k, _ in found}) != len(found):
        faults.append("the keys are not unique")
    return faults


def dump_table(path):
    table, faults = read_table(path)
    print("%s: %d records of %d bytes, %d fields, written %04d-%02d-%02d"
          % (path, len(table.records), table.record_length, len(table.fields), *table.date))
    for n, field in enumerate(table.fields, 1):
        decimals = ",%d" % field.decimals if field.type == "N" else ""
        print("  %2d %-10s %s %3d%s at %d" % (n, field.name, field.type, field.length, decimals,
                                             field.offset))
    for n, record in enumerate(table.records, 1):
        print("%5d %s" % (n, record.decode("latin-1")))
    for fault in faults:
        print("fault:", fault)


def dump_index(path):
    header, pages = read_index(path)
    length = header["key_length"]
    print("%s: key %d bytes on fields %s%s, root %d, %d pages, free %d"
          % (path, length, header["numbers"], ", unique" if header["flags"] & UNIQUE else "",
             header["root"], header["count"], header["free"]))

    def show(page, depth):
        if not 1 <= page < len(pages):
            print("  " * depth + "page %d: out of range" % page)
            return
        node, _, _ = parse_node(pages[page], length)
        kind = "leaf" if node.leaf else "node, below %d" % node.below
        print("  " * depth + "page %d, %s:" % (page, kind))
        if not node.leaf:
            show(node.below, depth + 1)
        for key, record, child in node.entries:
            print("  " * depth + "  %r #%d" % (key.decode("latin-1"), record))
            if not node.leaf:
                show(child, depth + 1)

    show(header["root"], 0)


def depth(path):
    header, pages = read_index(path)
    page, levels = header["root"], 1
    while True:
        node, _, _ = parse_node(pages[page], header["key_length"])
        if node.leaf:
            return levels
        page, levels = node.below, levels + 1


FIRST = ["ADA", "BEN", "CAROL", "DAVE", "EVE", "FRANK", "GRACE", "HAL", "IVY", "JACK", "KIM",
         "LEO", "MAY", "NED", "OLGA", "PAT"]
LAST = ["SMITH", "JONES", "BROWN", "TAYLOR", "WILSON", "DAVIES", "EVANS", "THOMAS", "ROBERTS"]
CITIES = ["BOSTON", "DENVER", "AUSTIN", "ATLANTA", "PORTLAND", "MIAMI"]


def make(folder):
    """The test tables and indexes, the same on every run:

    - PEOPLE.DB, 40 records, every type, some deleted, some blank; PNAME.IDX on NAME, PCITY.IDX
      on CITY and NAME, PBAL.IDX on BAL, with negatives, PID.IDX on ID, unique;
    - BIG.DB, 600 records of a 100-byte key, and BIG.IDX on it: 4 keys a page, 5 levels;
    - EMPTY.DB, no records, and EMPTY.IDX on it.
    """
    os.makedirs(folder, exist_ok=True)
    rand = random.Random(6502)
    people = Table([("ID", "N", 5), ("NAME", "C", 20), ("CITY", "C", 12), ("AGE", "N", 3),
                    ("BAL", "N", 8, 2), ("MEMBER", "L", 1), ("JOINED", "D", 8)])
    ids = rand.sample(range(1, 1000), 40)
    for n in range(40):
        name = "%s %s" % (rand.choice(FIRST), rand.choice(LAST))
        balance = round(rand.uniform(-500, 5000), 2) if n % 7 else None
        member = [True, False, None][n % 3]
        joined = datetime.date(2020, 1, 1) + datetime.timedelta(days=rand.randrange(2400))
        people.append([ids[n], name, rand.choice(CITIES), rand.randrange(18, 90), balance, member,
                       joined if n % 9 else None], deleted=n % 11 == 5)
    people.write(os.path.join(folder, "PEOPLE.DB"))
    for name, fields, unique in (("PNAME", ["NAME"], False), ("PCITY", ["CITY", "NAME"], False),
                                 ("PBAL", ["BAL"], False), ("PID", ["ID"], True)):
        numbers = [people.field(f) for f in fields]
        build_index(people, numbers, unique).write(os.path.join(folder, name + ".IDX"))
    big = Table([("KEY", "C", 100), ("N", "N", 4)])
    for n in range(600):
        big.append(["%08d" % rand.randrange(10 ** 8) + "-" * 92, n])
    big.write(os.path.join(folder, "BIG.DB"))
    build_index(big, [1]).write(os.path.join(folder, "BIG.IDX"))
    empty = Table([("NAME", "C", 10)])
    empty.write(os.path.join(folder, "EMPTY.DB"))
    build_index(empty, [1]).write(os.path.join(folder, "EMPTY.IDX"))


def main(args):
    if len(args) >= 2 and args[0] == "dump":
        if open(args[1], "rb").read(2) == b"IX":
            dump_index(args[1])
        else:
            dump_table(args[1])
        return 0
    if len(args) >= 2 and args[0] == "check":
        table, faults = read_table(args[1])
        failed = bool(faults)
        for fault in faults:
            print("%s: %s" % (args[1], fault))
        for path in args[2:]:
            faults = check_index(path, table)
            failed = failed or bool(faults)
            for fault in faults:
                print("%s: %s" % (path, fault))
            if not faults:
                print("%s: good, %d levels" % (path, depth(path)))
        if not failed:
            print("%s: good, %d records" % (args[1], len(table.records)))
        return 1 if failed else 0
    if len(args) >= 4 and args[0] == "index":
        table, faults = read_table(args[1])
        if faults:
            raise DBError("%s: %s" % (args[1], faults[0]))
        numbers = [table.field(name) for name in args[3].split(",")]
        build_index(table, numbers, "-u" in args[4:]).write(args[2])
        return 0
    if len(args) == 2 and args[0] == "make":
        make(args[1])
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except DBError as error:
        print("error:", error)
        sys.exit(1)
