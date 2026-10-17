"""Rank UXC labels by profile samples.

    python profmap.py SAMPLES.TXT [BASE]

BASE is the hex address the low map offsets count from. It is 0A00 for UXC: $0900 plus the
bootstrap extension page a program with banked regions has.
"""
import bisect
import collections
import sys

BUILD = r"C:\dev\UXCBASIC\build"
samples_file = sys.argv[1]
base = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x0A00

# map: (bank, address) -> BASLOAD line; bank None for low memory
low, banked = [], collections.defaultdict(list)
for line in open(BUILD + r"\UXC.MAP", encoding="utf-8"):
    parts = line.split()
    if len(parts) != 2:
        continue
    where, number = parts[0], int(parts[1])
    if ":" in where:
        bank, address = where.split(":")
        banked[int(bank, 16)].append((int(address, 16), number))
    else:
        low.append((base + int(where, 16), number))
low.sort()
for bank in banked:
    banked[bank].sort()

# labels: BASLOAD line -> label, with its file
labels = []
current_file = "?"
section = None
for line in open(BUILD + r"\UXC.SRC.SYM", encoding="utf-8"):
    if line.startswith("VARIABLES"):
        break
    if line.startswith("FILE:"):
        current_file = line[5:].strip()
        continue
    if "=" in line and line.strip():
        name = line.split()[1]
        number = int(line.rsplit("=", 1)[1].rstrip(";\n "))
        labels.append((number, name, current_file))
labels.sort()
label_lines = [l[0] for l in labels]


def line_of(table, address):
    keys = [a for a, _ in table]
    i = bisect.bisect_right(keys, address) - 1
    return table[i][1] if i >= 0 else None


def label_of(number):
    i = bisect.bisect_right(label_lines, number) - 1
    return labels[i][1:] if i >= 0 else ("?", "?")


by_label = collections.Counter()
by_file = collections.Counter()
by_line = collections.Counter()
by_kind = collections.Counter()
total = 0
for line in open(samples_file, encoding="utf-8"):
    bank, lo, hi = (int(x, 16) for x in line.split())
    address = lo | hi << 8
    total += 1
    if address >= 0xA000:
        table = banked.get(bank)
        kind = "bank %d" % bank
    elif address >= base:
        table = low
        kind = "low"
    else:
        by_kind["below base %04x" % address] += 1
        continue
    if not table:
        by_kind["unmapped " + kind] += 1
        continue
    number = line_of(table, address)
    if number is None:
        by_kind["before map " + kind] += 1
        continue
    name, file = label_of(number)
    by_kind[kind] += 1
    by_label[(name, file)] += 1
    by_file[file] += 1
    by_line[number] += 1

print("samples", total)
print("\nby region")
for k, v in by_kind.most_common(20):
    print("  %6d %5.1f%%  %s" % (v, 100 * v / total, k))
print("\nby file")
for k, v in by_file.most_common(25):
    print("  %6d %5.1f%%  %s" % (v, 100 * v / total, k))
print("\nby label")
for (name, file), v in by_label.most_common(40):
    print("  %6d %5.1f%%  %-32s %s" % (v, 100 * v / total, name, file))
print("\nby BASLOAD line")
for k, v in by_line.most_common(25):
    print("  %6d %5.1f%%  line %d  %s" % (v, 100 * v / total, k, label_of(k)[0]))
