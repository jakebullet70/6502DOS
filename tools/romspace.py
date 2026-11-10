"""Print the free bytes of each ROM bank and RAM area of the build, and the change since the
last build.

    python tools/romspace.py

Banks 0, 1 and 5 and the kernel's RAM areas come from build/6502DOS.MAP with src/asm/rom.cfg,
bank 2 and MSBASIC's RAM areas from build/MSBASIC.MAP with MSBASIC/src/6502dos.cfg, and banks
3, 4, 6, 7 and 8 from build/bankF/BANKn.BIN, whose $FF fill before T_FAR at K_FAR is free; a
code byte of $FF at the end of the code counts as free. An area's free bytes are its size, cut
at the lowest fixed-start segment in it, less the sizes of the segments loaded or run in it; a
fixed-start segment at the area's start counts as used. An area with no segment, and MSBASIC's
DUMMY area, are not printed.
build/space.json holds the sizes of the last build, and the last line names each segment and
bank whose bytes changed. tools/build.py runs this after the banks are built.
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "build")
LAST = os.path.join(BUILD, "space.json")
sys.path.insert(0, os.path.join(ROOT, "UXCBASIC", "pyuxc"))
from uxc_defs import K_FAR  # noqa: E402

# Each ld65 link: its map in build, its config, the prefix of its segment and RAM area names,
# and the bank number of each ROM area, printed as "bank N".
LINKS = (("6502DOS.MAP", os.path.join("src", "asm", "rom.cfg"), "",
          {"BANK0": 0, "BANK1": 1, "BANK5": 5}),
         ("MSBASIC.MAP", os.path.join("MSBASIC", "src", "6502dos.cfg"), "MSBASIC ",
          {"BANK2": 2}))
# Each pyuxc ROM program: the folder of its BANKn.BIN files in build, and its banks.
PROGRAMS = (("bank3", (3, 4)), ("bank6", (6, 7, 8)))
BANK_START = 0xC000
ATTRIBUTE = re.compile(r"(\w+)\s*=\s*([^,;]+)")
MAP_SEGMENT = re.compile(r"^(\w+)\s+[0-9A-F]{6}\s+[0-9A-F]{6}\s+([0-9A-F]{6})\s+[0-9A-F]+$",
                         re.MULTILINE)


def read_config(path):
    """The MEMORY areas of an ld65 config as {name: (start, size)} and its SEGMENTS as
    {name: {attribute: value}}, a $ number as an int. Each area and segment is on one line."""
    areas = {}
    segments = {}
    block = None
    for line in open(path, encoding="utf-8"):
        line = line.split("#")[0].strip()
        if line.endswith("{"):
            block = line.split()[0]
        elif ":" in line:
            name, rest = line.split(":", 1)
            values = {}
            for key, value in ATTRIBUTE.findall(rest):
                value = value.strip()
                values[key] = int(value[1:], 16) if value.startswith("$") else value
            if block == "MEMORY":
                areas[name.strip()] = (values["start"], values["size"])
            elif block == "SEGMENTS":
                segments[name.strip()] = values
    return areas, segments


def read_map(path):
    """The segment sizes of an ld65 map as {name: size}."""
    section = open(path, encoding="utf-8").read().split("Segment list:")[1].split("\n\n")[0]
    return {name: int(size, 16) for name, size in MAP_SEGMENT.findall(section)}


def link_space(map_name, config, prefix, banks):
    """The free bytes of each area of one link as {label: free}, the label "bank N" for a ROM
    area and the prefix and the area's name for the rest, and the size of each segment as
    {prefix and name: size}."""
    sizes = read_map(os.path.join(BUILD, map_name))
    areas, segments = read_config(os.path.join(ROOT, config))
    free = {}
    for area, (start, size) in areas.items():
        top = start + size
        used = 0
        for name, values in segments.items():
            if area not in (values.get("load"), values.get("run")):
                continue
            if values.get("start", start) == start:
                used += sizes.get(name, 0)
            else:
                top = min(top, values["start"])
        if used and area != "DUMMY":
            label = "bank %d" % banks[area] if area in banks else prefix + area
            free[label] = top - start - used
    return free, {prefix + name: size for name, size in sizes.items()}


def program_space(folder, banks):
    """The free bytes of each bank of a pyuxc ROM program as {"bank N": free}: the $FF bytes
    before T_FAR in build/folder/BANKn.BIN. A later bank's empty file is all free."""
    free = {}
    end = K_FAR - BANK_START
    for bank in banks:
        image = open(os.path.join(BUILD, folder, "BANK%d.BIN" % bank), "rb").read()
        used = min(end, len(image))
        while used and image[used - 1] == 0xFF:
            used -= 1
        free["bank %d" % bank] = end - used
    return free


def main():
    free = {}
    sizes = {}
    for map_name, config, prefix, banks in LINKS:
        link_free, link_sizes = link_space(map_name, config, prefix, banks)
        free.update(link_free)
        sizes.update(link_sizes)
    for folder, banks in PROGRAMS:
        for label, bank_free in program_space(folder, banks).items():
            free[label] = bank_free
            sizes[label + " code"] = K_FAR - BANK_START - bank_free
    banks = sorted((label for label in free if label.startswith("bank ")),
                   key=lambda label: int(label[5:]))
    print("free: " + ", ".join("%s %d" % (label, free[label]) for label in banks))
    print("free RAM: " + ", ".join("%s %d" % (label, free[label]) for label in free
                                   if label not in banks))
    last = json.load(open(LAST, encoding="utf-8")) if os.path.exists(LAST) else {}
    changes = ["%s %+d" % (name, size - last[name]) for name, size in sizes.items()
               if name in last and last[name] != size]
    if changes:
        print("changed since the last build: " + ", ".join(changes))
    with open(LAST, "w", encoding="utf-8") as out:
        json.dump(sizes, out, indent=1)


if __name__ == "__main__":
    main()
