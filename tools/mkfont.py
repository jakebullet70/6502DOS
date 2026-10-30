"""Makes card/sys/themes/GUI.F08, the GUI font: the CP437 font of src/asm/font.s with GUI glyphs in
some slots. Also makes card/sys/themes/CP437.F08, the font of font.s unchanged; FONT loads it to put
the ROM's font back.

GUI.F08 is 2048 bytes raw: 256 glyphs of 8 by 8 pixels, 8 bytes each, from character 0 up, the
top row first, bit 7 the left pixel. The layout is font.s's, so the file loads to the console
font at VRAM $1F000 as is.

The screen shows each pixel twice as tall as wide, 640x240 on a 640x480 display. Vertical
strokes are 2 pixels wide and horizontal strokes 1 pixel tall, as in font.s.

Usage: mkfont.py [-n] [preview.png]. The font takes the TDCO++ glyphs; -n takes the
Norton-style glyphs instead. The preview is a PNG of the GUI slots and a mock dialog.
"""

import os
import re
import struct
import sys
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_SOURCE = os.path.join(ROOT, "src", "asm", "font.s")
FONT_OUT = os.path.join(ROOT, "card", "sys", "themes", "GUI.F08")
CP437_OUT = os.path.join(ROOT, "card", "sys", "themes", "CP437.F08")

# The GUI glyphs. $B5-$D8 are CP437's mixed single and double box junctions; $01-$06 are
# CP437's smileys and card suits. Each glyph is 8 rows of 8 pixels, '#' set.
GLYPHS = {
    0xB5: ("button shadow, right", [
        "........",
        "........",
        "####....",
        "####....",
        "####....",
        "####....",
        "####....",
        "####...."]),
    0xB6: ("button shadow, bottom left", [
        "....####",
        "....####",
        "....####",
        "........",
        "........",
        "........",
        "........",
        "........"]),
    0xB7: ("button shadow, bottom", [
        "########",
        "########",
        "########",
        "........",
        "........",
        "........",
        "........",
        "........"]),
    0xB8: ("button shadow, bottom right", [
        "####....",
        "####....",
        "####....",
        "........",
        "........",
        "........",
        "........",
        "........"]),
    0xBD: ("scroll bar track", [
        "#...#...",
        "........",
        "..#...#.",
        "........",
        "#...#...",
        "........",
        "..#...#.",
        "........"]),
    0xBE: ("scroll bar thumb", [
        ".######.",
        "########",
        "########",
        "########",
        "########",
        "########",
        "########",
        ".######."]),
    0xC6: ("scroll button, up", [
        "########",
        "########",
        "###..###",
        "##....##",
        "#......#",
        "########",
        "########",
        "########"]),
    0xC7: ("scroll button, down, and drop-down button", [
        "########",
        "########",
        "########",
        "#......#",
        "##....##",
        "###..###",
        "########",
        "########"]),
    0xCF: ("scroll button, left", [
        "########",
        "#####..#",
        "###....#",
        "#......#",
        "#......#",
        "###....#",
        "#####..#",
        "########"]),
    0xD0: ("scroll button, right", [
        "########",
        "#..#####",
        "#....###",
        "#......#",
        "#......#",
        "#....###",
        "#..#####",
        "########"]),
    0xD1: ("check box, clear", [
        "........",
        "........",
        "#######.",
        "#.....#.",
        "#.....#.",
        "#.....#.",
        "#######.",
        "........"]),
    0xD2: ("check box, checked", [
        ".......#",
        "......##",
        "####.##.",
        "#...##..",
        "#.###.#.",
        "#..#..#.",
        "#######.",
        "........"]),
    0xD3: ("radio button, clear", [
        "........",
        "..####..",
        ".##..##.",
        "##....##",
        "##....##",
        ".##..##.",
        "..####..",
        "........"]),
    0xD4: ("radio button, set", [
        "........",
        "..####..",
        ".##..##.",
        "##.##.##",
        "##.##.##",
        ".##..##.",
        "..####..",
        "........"]),
    0xD7: ("check mark", [
        "........",
        "......##",
        ".....##.",
        "##..##..",
        ".####...",
        "..##....",
        "........",
        "........"]),
    0xD8: ("ellipsis", [
        "........",
        "........",
        "........",
        "........",
        "........",
        "........",
        "#..#..#.",
        "........"]),
    0x01: ("floppy drive", [
        "........",
        "########",
        "#......#",
        "#.####.#",
        "#......#",
        "########",
        "........",
        "........"]),
    0x02: ("hard drive", [
        "........",
        "########",
        "#......#",
        "#......#",
        "#......#",
        "#....#.#",
        "########",
        "........"]),
    0x03: ("text cursor", [
        ".##.##..",
        "...#....",
        "...#....",
        "...#....",
        "...#....",
        "...#....",
        "...#....",
        ".##.##.."]),
    0x04: ("close box", [
        "........",
        "########",
        "########",
        "#......#",
        "########",
        "########",
        "........",
        "........"]),
    0x05: ("resize grip", [
        "........",
        "........",
        "......#.",
        "........",
        "....#.#.",
        "........",
        "..#.#.#.",
        "........"]),
    0x06: ("folder", [
        "........",
        "###.....",
        "########",
        "########",
        "########",
        "########",
        "########",
        "........"]),
}

# The TDCO++ glyphs, from its CUAFONT module's 8-row set, at TDCO++'s codes. Each control is 2
# or 3 cells wide. $D2 $D5 $D6 have only 16 rows in TDCO++; here they are its top row and then
# its second row 7 times. The 8-row scroll button right has 9 rows in TDCO++; here it is the
# mirror of scroll button left. The GLYPHS slots that TDCO++ does not use are added after it.
TDCO_GLYPHS = {
    0xC1: ("window edge, right", [
        ".......#",
        ".......#",
        ".......#",
        ".......#",
        ".......#",
        ".......#",
        ".......#",
        ".......#"]),
    0xC2: ("window edge, left", [
        "##......",
        "##......",
        "##......",
        "##......",
        "##......",
        "##......",
        "##......",
        "##......"]),
    0xC3: ("scroll thumb, vertical, left", [
        "##......",
        "##..####",
        "##..####",
        "##..####",
        "##..####",
        "##..####",
        "##..####",
        "##......"]),
    0xC5: ("scroll thumb, vertical, right", [
        ".......#",
        "#####..#",
        "#####..#",
        "#####..#",
        "#####..#",
        "#####..#",
        "#####..#",
        ".......#"]),
    0xC6: ("close box, left", [
        "........",
        "..######",
        "..#.....",
        "..#...##",
        "..#...##",
        "..#.....",
        "..######",
        "........"]),
    0xC7: ("check box, middle, clear", [
        "########",
        "........",
        "........",
        "........",
        "........",
        "........",
        "........",
        "########"]),
    0xCA: ("radio button, middle, clear", [
        "#######.",
        ".......#",
        "........",
        "........",
        "........",
        "........",
        ".......#",
        "#######."]),
    0xCB: ("radio button, middle, set", [
        "#######.",
        ".......#",
        ".#####..",
        "#######.",
        "#######.",
        ".#####..",
        ".......#",
        "#######."]),
    0xCC: ("radio button, left", [
        "........",
        "......##",
        ".....#..",
        ".....#..",
        ".....#..",
        ".....#..",
        "......##",
        "........"]),
    0xCE: ("check box, middle, checked", [
        "########",
        ".....##.",
        "....##..",
        "...##...",
        "#.###...",
        "####....",
        ".###....",
        "########"]),
    0xCF: ("scroll button right, left", [
        "########",
        "#.......",
        "#.......",
        "#..#####",
        "#..#####",
        "#.......",
        "#.......",
        "########"]),
    0xD0: ("window edge, bottom", [
        "........",
        "........",
        "........",
        "........",
        "........",
        "........",
        "........",
        "########"]),
    0xD1: ("scroll track, horizontal", [
        "########",
        "........",
        "........",
        "........",
        "........",
        "........",
        "........",
        "########"]),
    0xD2: ("window edge, top", [
        "########",
        "........",
        "........",
        "........",
        "........",
        "........",
        "........",
        "........"]),
    0xD3: ("window corner, bottom left", [
        "##......",
        "##......",
        "##......",
        "##......",
        "##......",
        "##......",
        "##......",
        "########"]),
    0xD4: ("window corner, bottom right", [
        ".......#",
        ".......#",
        ".......#",
        ".......#",
        ".......#",
        ".......#",
        ".......#",
        "########"]),
    0xD5: ("window corner, top right", [
        "########",
        ".......#",
        ".......#",
        ".......#",
        ".......#",
        ".......#",
        ".......#",
        ".......#"]),
    0xD6: ("window corner, top left", [
        "########",
        "##......",
        "##......",
        "##......",
        "##......",
        "##......",
        "##......",
        "##......"]),
    0xD7: ("scroll thumb, horizontal", [
        "########",
        "........",
        "########",
        "########",
        "########",
        "########",
        "........",
        "########"]),
    0xD8: ("check box, left", [
        ".....###",
        ".....##.",
        ".....##.",
        ".....##.",
        ".....##.",
        ".....##.",
        ".....##.",
        ".....###"]),
    0xDB: ("scroll button up, left", [
        "########",
        "#......#",
        "#....###",
        "#..#####",
        "#.....##",
        "#.....##",
        "#.......",
        "########"]),
    0xDD: ("scroll button down, left", [
        "########",
        "#.......",
        "#.....##",
        "#.....##",
        "#..#####",
        "#....###",
        "#......#",
        "########"]),
    0xDE: ("scroll button left, left", [
        "########",
        "#......#",
        "#....###",
        "#..#####",
        "#..#####",
        "#....###",
        "#......#",
        "########"]),
    0xE3: ("check box, right", [
        "###.....",
        ".##.....",
        ".##.....",
        ".##.....",
        ".##.....",
        ".##.....",
        ".##.....",
        "###....."]),
    0xE4: ("radio button, right", [
        "........",
        "#.......",
        ".#......",
        ".#......",
        ".#......",
        ".#......",
        "#.......",
        "........"]),
    0xE5: ("close box, right", [
        "........",
        "######..",
        ".....##.",
        "##...##.",
        "##...##.",
        ".....##.",
        "#######.",
        "........"]),
    0xE6: ("scroll button up, right", [
        "########",
        "#......#",
        "###....#",
        "#####..#",
        "##.....#",
        "##.....#",
        ".......#",
        "########"]),
    0xE7: ("scroll button down, right", [
        "########",
        ".......#",
        "##.....#",
        "##.....#",
        "#####..#",
        "###....#",
        "#......#",
        "########"]),
    0xE8: ("scroll button left, right", [
        "########",
        ".......#",
        ".......#",
        "#####..#",
        "#####..#",
        ".......#",
        ".......#",
        "########"]),
    0xE9: ("scroll button right, right", [
        "########",
        "#......#",
        "###....#",
        "#####..#",
        "#####..#",
        "###....#",
        "#......#",
        "########"]),
    0xFB: ("check mark", [
        "........",
        ".....##.",
        "....##..",
        "...##...",
        "#.###...",
        "####....",
        ".###....",
        "........"]),
}
TDCO_GLYPHS.update({code: glyph for code, glyph in GLYPHS.items() if code not in TDCO_GLYPHS})


def read_font_source(path):
    with open(path, encoding="utf-8") as source:
        rows = re.findall(r"^\.byte %([01]{8})", source.read(), re.M)
    if len(rows) != 2048:
        sys.exit(f"{path}: {len(rows)} font rows, not 2048")
    return bytearray(int(row, 2) for row in rows)


def make_font(glyphs):
    font = read_font_source(FONT_SOURCE)
    for code, (name, rows) in glyphs.items():
        if len(rows) != 8 or any(len(row) != 8 for row in rows):
            sys.exit(f"${code:02X} {name}: not 8 rows of 8")
        for y, row in enumerate(rows):
            font[code * 8 + y] = int(row.replace("#", "1").replace(".", "0"), 2)
    return bytes(font)


# The preview: VGA colors, each font pixel 3 wide and 6 tall.
BLACK, BLUE, CYAN, GRAY = (0, 0, 0), (0, 0, 170), (0, 170, 170), (170, 170, 170)
DARK_GRAY, WHITE, YELLOW = (85, 85, 85), (255, 255, 255), (255, 255, 85)
SCALE_X, SCALE_Y = 3, 6


class Screen:
    def __init__(self, columns, rows, background):
        self.columns, self.rows = columns, rows
        self.cells = [[(0x20, WHITE, background)] * columns for _ in range(rows)]

    def put(self, x, y, text, foreground, background):
        """Text is a str, or a list of codes and strs."""
        if isinstance(text, str):
            text = [text]
        for part in text:
            for code in [part] if isinstance(part, int) else map(ord, part):
                self.cells[y][x] = (code, foreground, background)
                x += 1

    def png(self, font, path):
        width, height = self.columns * 8 * SCALE_X, self.rows * 8 * SCALE_Y
        lines = []
        for y in range(height):
            cell_row, glyph_row = divmod(y // SCALE_Y, 8)
            line = bytearray()
            for code, foreground, background in self.cells[cell_row]:
                bits = font[code * 8 + glyph_row]
                for x in range(8):
                    line += bytes(foreground if bits & (0x80 >> x) else background) * SCALE_X
            lines.append(b"\0" + bytes(line))

        def chunk(kind, data):
            return (struct.pack(">I", len(data)) + kind + data
                    + struct.pack(">I", zlib.crc32(kind + data)))

        header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
        with open(path, "wb") as out:
            out.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
                      + chunk(b"IDAT", zlib.compress(b"".join(lines))) + chunk(b"IEND", b""))


def button(screen, x, y, label, width, background, face=GRAY):
    """A button face with its shadow, on a dialog of the given background."""
    screen.put(x, y, label.center(width), BLACK, face)
    screen.put(x + width, y, [0xB5], BLACK, background)
    screen.put(x, y + 1, [0xB6] + [0xB7] * (width - 1) + [0xB8], BLACK, background)


def frame(screen, left, top, width, height, foreground, background):
    """A single-line box of CP437 line characters, filled with the background."""
    screen.put(left, top, [0xDA] + [0xC4] * (width - 2) + [0xBF], foreground, background)
    for y in range(top + 1, top + height - 1):
        screen.put(left, y, [0xB3, " " * (width - 2), 0xB3], foreground, background)
    screen.put(left, top + height - 1, [0xC0] + [0xC4] * (width - 2) + [0xD9], foreground,
               background)


def window(screen, left, top, width, height, title, background):
    """A dialog: a box with a frame on its edge cells, a title row, a rule under the title, and a
    shadow two columns right and one row down. The body starts at row top + 3."""
    screen.put(left, top, " " * width, WHITE, background)
    for y in range(top + 1, top + height):
        screen.put(left, y, " " * width, WHITE, background)
        screen.put(left + width, y, "  ", BLACK, BLACK)
    screen.put(left + width, top + height, "  ", BLACK, BLACK)
    screen.put(left + 2, top + height, " " * width, BLACK, BLACK)
    frame(screen, left, top, width, height, WHITE, background)
    if title:
        screen.put(left + (width - len(title)) // 2, top + 1, title, YELLOW, background)
        screen.put(left, top + 2, [0xC3] + [0xC4] * (width - 2) + [0xB4], WHITE, background)


def slots(screen, glyphs):
    """The GUI slots, each with its code, from row 1."""
    for index, code in enumerate(sorted(glyphs)):
        x, y = (index % 8) * 10 + 1, (index // 8) * 2 + 1
        screen.put(x, y, f"{code:02X}", YELLOW, BLUE)
        screen.put(x + 3, y, [code], WHITE, BLACK)


def thin_window(screen, left, top, width, height, title, foreground, background):
    """A TDCO++ window: a frame of 1-pixel lines on the edge cells, the close box and the title
    on the top row, and a black shadow 2 columns right and 1 row down."""
    for y in range(top + 1, top + height + 1):
        screen.put(left + width, y, "  ", BLACK, BLACK)
    screen.put(left + 2, top + height, " " * width, BLACK, BLACK)
    screen.put(left, top, [0xD6] + [0xD2] * (width - 2) + [0xD5], foreground, background)
    for y in range(top + 1, top + height - 1):
        screen.put(left, y, [0xC2, " " * (width - 2), 0xC1], foreground, background)
    screen.put(left, top + height - 1, [0xD3] + [0xD0] * (width - 2) + [0xD4], foreground,
               background)
    screen.put(left + 1, top, [0xC6, 0xE5], foreground, background)
    screen.put(left + (width - len(title)) // 2, top, title, foreground, background)


def preview_tdco(font, path):
    screen = Screen(80, 40, BLUE)
    slots(screen, TDCO_GLYPHS)
    top = 12
    screen.put(0, top, " File  Disk  View  Configure  Tools  Window  Help".ljust(80), BLACK, GRAY)
    for y in range(top + 1, 39):
        screen.put(0, y, " " * 80, WHITE, DARK_GRAY)
    left, dialog_top, width = 4, top + 2, 44
    thin_window(screen, left, dialog_top, width, 18, " Format Diskette ", BLACK, GRAY)
    screen.put(left + 3, dialog_top + 2, "Drive:", BLACK, GRAY)
    screen.put(left + 3, dialog_top + 3, [0x01, " A:         "], BLACK, WHITE)
    screen.put(left + 16, dialog_top + 3, [0xDD, 0xE7], BLACK, GRAY)
    screen.put(left + 3, dialog_top + 5, "Size:", BLACK, GRAY)
    for row, (mark, label) in enumerate(((0xCA, "720K"), (0xCB, "1.44M"), (0xCA, "2.88M"))):
        screen.put(left + 3, dialog_top + 6 + row, [0xCC, mark, 0xE4, " " + label], BLACK, GRAY)
    screen.put(left + 3, dialog_top + 10, "Options:", BLACK, GRAY)
    for row, (mark, label) in enumerate(((0xCE, "Make Disk Bootable"), (0xC7, "Quick Format"),
                                         (0xCE, "Save Image Info"))):
        screen.put(left + 3, dialog_top + 11 + row, [0xD8, mark, 0xE3, " " + label], BLACK, GRAY)
    for row, label in enumerate(("Format", "Configure", "Exit")):
        button(screen, left + 28, dialog_top + 3 + row * 3, label, 12, GRAY, WHITE)
    screen.put(left + 3, dialog_top + 15, "Done:", BLACK, GRAY)
    screen.put(left + 9, dialog_top + 15, " " * 10, BLACK, BLUE)
    screen.put(left + 19, dialog_top + 15, " " * 20, BLACK, WHITE)
    # A list box with both scroll bars.
    left, box_top, width, height = 52, top + 2, 24, 16
    thin_window(screen, left, box_top, width, height, " Files ", BLACK, WHITE)
    names = ("AUTOEXEC.BAT", "COMMAND.COM", "CONFIG.SYS", "DOS", "GAMES", "TED.COM",
             "UTILS", "README.TXT", "CHKDSK.COM", "FONT.COM", "SHELL.COM")
    for row, name in enumerate(names):
        colors = (WHITE, BLUE) if row == 2 else (BLACK, WHITE)
        screen.put(left + 2, box_top + 1 + row, name.ljust(width - 6), *colors)
    column = left + width - 3
    screen.put(column, box_top + 1, [0xDB, 0xE6], BLACK, WHITE)
    for y in range(box_top + 2, box_top + height - 3):
        screen.put(column, y, [0xC2, 0xC1], BLACK, WHITE)
    screen.put(column, box_top + 4, [0xC3, 0xC5], BLACK, WHITE)
    screen.put(column, box_top + 5, [0xC3, 0xC5], BLACK, WHITE)
    screen.put(column, box_top + height - 3, [0xDD, 0xE7], BLACK, WHITE)
    row = box_top + height - 2
    screen.put(left + 1, row, [0xDE, 0xE8] + [0xD1] * (width - 7) + [0xCF, 0xE9], BLACK, WHITE)
    screen.put(left + 6, row, [0xD7, 0xD7, 0xD7], BLACK, WHITE)
    keys = "1Help  2Menu  3View  4Edit  5Find  6Print 7Move  8Copy  9Delete 10PullDn"
    screen.put(0, 39, keys.ljust(80), BLACK, CYAN)
    screen.png(font, path)


def preview(font, path):
    screen = Screen(80, 40, BLUE)
    # The GUI slots, each with its code.
    for index, code in enumerate(sorted(GLYPHS)):
        x, y = (index % 8) * 8 + 1, (index // 8) * 2 + 1
        screen.put(x, y, f"{code:02X}", YELLOW, BLUE)
        screen.put(x + 3, y, [code], WHITE, BLACK)
    # A mock "Format Diskette" dialog and a progress box on a desktop.
    top = 7
    screen.put(0, top, " File  Disk  View  Configure  Tools  Window  Help".ljust(80), BLACK, GRAY)
    for y in range(top + 1, 39):
        screen.put(0, y, " " * 80, WHITE, DARK_GRAY)
    for row, (icon, drive) in enumerate(((0x01, "A:"), (0x01, "B:"), (0x02, "C:"))):
        screen.put(1, top + 2 + row * 2, [" ", icon, " " + drive + " "], BLUE, WHITE)
    left, dialog_top, width = 20, top + 2, 38
    window(screen, left, dialog_top, width, 22, "Format Diskette", BLUE)
    screen.put(left + 2, dialog_top + 1, [0x04], WHITE, BLUE)
    fields = (("Drive:", [0x01, " A........"]), ("Size:", ["1.4M......."]),
              ("Format Type:", ["Safe......."]))
    for row, (label, value) in enumerate(fields):
        y = dialog_top + 4 + row * 3
        screen.put(left + 3, y, label, WHITE, BLUE)
        screen.put(left + 3, y + 1, ["["] + value + ["]"], WHITE, BLUE)
        screen.put(left + 16, y + 1, [0xC7], BLACK, WHITE)
    for row, label in enumerate(("Format", "Configure", "Exit")):
        button(screen, left + 21, dialog_top + 5 + row * 2, label, 12, BLUE)
    box_top = dialog_top + 13
    frame(screen, left + 3, box_top, 32, 7, WHITE, BLUE)
    screen.put(left + 5, box_top, " Options ", WHITE, BLUE)
    screen.put(left + 6, box_top + 2, [0xD1, "  Make Disk Bootable"], WHITE, BLUE)
    screen.put(left + 6, box_top + 3, [0xD2, "  Save Image Info"], WHITE, BLUE)
    screen.put(left + 6, box_top + 5, "Volume Label: [..........]", WHITE, BLUE)
    screen.put(left + 3, dialog_top + 20, [0xD1, "  Save Settings on Exit"], WHITE, BLUE)
    left, box_top, width = 16, top + 26, 46
    window(screen, left, box_top, width, 5, None, BLUE)
    screen.put(left + 9, box_top + 1, "Analyzing DOS Boot Record...", YELLOW, BLUE)
    screen.put(left + 4, box_top + 2, [0xDB] * 13, WHITE, BLUE)
    screen.put(left + 17, box_top + 2, [0xDB] * 25, GRAY, BLUE)
    screen.put(left + 21, box_top + 3, "33%", WHITE, BLUE)
    keys = "1Help  2Menu  3View  4Edit  5Find  6Print 7Move  8Copy  9Delete 10PullDn"
    screen.put(0, 39, keys.ljust(80), BLACK, CYAN)
    screen.png(font, path)


def main():
    arguments = sys.argv[1:]
    norton = "-n" in arguments
    if norton:
        arguments.remove("-n")
    glyphs = GLYPHS if norton else TDCO_GLYPHS
    font = make_font(glyphs)
    with open(FONT_OUT, "wb") as out:
        out.write(font)
    print(f"{FONT_OUT}: {len(font)} bytes, {len(glyphs)} GUI glyphs")
    cp437 = read_font_source(FONT_SOURCE)
    with open(CP437_OUT, "wb") as out:
        out.write(cp437)
    print(f"{CP437_OUT}: {len(cp437)} bytes")
    if arguments:
        (preview if norton else preview_tdco)(font, arguments[0])
        print(f"{arguments[0]}: preview")


if __name__ == "__main__":
    main()
