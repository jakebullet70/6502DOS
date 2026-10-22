"""UXC-LEX.BL: the source file, and the tokens of one line.

    lx_open()     in  g.lx_name     open the source on channel 2
    lx_read()     out g.lx_got      1 when g.lx_l holds the next line, numbered g.lx_no
    lx_whole()                      start the line; a whole-line comment leaves nothing in it
    lx_next()     out g.tk_t        the next token:
                      g.tk_v        K_TT_NUM: the value, 0 to 4294967295
                      g.tk_s        K_TT_STR: the text. K_TT_NAME: the name in upper case,
                                    with its $ mark. A name in g.nm_alias_name is replaced by
                                    its word in g.nm_alias_target.
                      g.tk_m        K_TT_NAME: K_TY_STR for a $ mark, else 0
                      g.tk_k        K_TT_OP: the character, or K_OP_* for <> <= >= << >>

A line is a str of latin-1 characters, one for each byte of the file. GPC's PEEK(LX.A + LX.P)
is ch(g.lx_p): LX.P counts from 1.

Channel 2 is g.lx_data, the whole file, and g.lx_pos, the next byte to read. find_file stands
for the drive: the source's folder, then each -I folder.
"""

import os

from uxc_defs import K_OP_GE, K_OP_LE, K_OP_NE, K_OP_SHL, K_OP_SHR, K_TT_EOL, K_TT_NAME, \
    K_TT_NUM, K_TT_OP, K_TT_STR, K_TY_STR
from uxc_state import er_stop, er_syntax, g


def find_file(name):
    """The path of name on the drive, or None."""
    for folder in [g.source_folder] + g.include_folders:
        path = os.path.join(folder, name)
        if os.path.isfile(path):
            return path
    return None


def open_2(name):
    """OPEN 2, 8, 2, name + ",S,R". A name not found still opens; its reads fail. An empty
    file reads as a file not found, as on the emulator's drive."""
    path = find_file(name)
    g.lx_data = None
    if path is not None:
        with open(path, "rb") as source:
            g.lx_data = source.read().decode("latin-1")
        if g.lx_data == "":
            g.lx_data = None
    g.lx_pos = 0


def close_2():
    g.lx_data = None


def linput_2(delimiter):
    """LINPUT# 2, s$, delimiter. Return (s$, ST). The text keeps its first 255 bytes, and the
    read runs on to the delimiter. ST bit 6 is set when the last byte of the file was read. A
    file that was not found gives CHR$(0) with ST 66."""
    if g.lx_data is None:
        return chr(0), 66
    data = g.lx_data
    end = data.find(chr(delimiter), g.lx_pos)
    if end < 0:
        text = data[g.lx_pos:]
        g.lx_pos = len(data)
    else:
        text = data[g.lx_pos:end]
        g.lx_pos = end + 1
    status = 64 if g.lx_pos >= len(data) else 0
    return text[:255], status


def ch(position):
    """PEEK(LX.A + position): the character at position of g.lx_l, counted from 1."""
    return ord(g.lx_l[position - 1])


def instr(text, part):
    """GP.INSTR: the position of part in text, counted from 1, or 0."""
    return text.find(part) + 1


def lx_open():
    """LX.OPEN. TURBO writes CR, and files from the host are LF or CR LF. The probe read with
    delimiter 10 tells them apart: no CR is LF, a CR only at the end is CR LF, a CR before the
    end is CR."""
    g.lx_delim = 10
    open_2(g.lx_name)
    g.lx_l, g.lx_st = linput_2(10)
    close_2()
    if (g.lx_st & 2) != 0:
        er_stop("FILE NOT FOUND: " + g.lx_name)
    g.lx_c = instr(g.lx_l, chr(13))
    if g.lx_c > 0 and g.lx_c < len(g.lx_l):
        g.lx_delim = 13
    open_2(g.lx_name)
    g.lx_eof = 0
    g.lx_no = 0
    g.lx_join_skip = 0


def lx_read():
    """LX.READ. Bit 6 of ST marks the last line, which still holds text. The end of an
    included file goes back to the line after its #INCLUDE. A line joined by _ keeps the
    number of its first line; g.lx_join_skip counts the lines joined to it."""
    g.lx_got = 0
    while True:
        if g.lx_eof != 0 and g.lx_including != 0:
            lx_include_end()
        if g.lx_eof != 0:
            return
        g.lx_l, g.lx_st = linput_2(g.lx_delim)
        if (g.lx_st & 2) != 0:
            g.lx_eof = 1
            continue
        if (g.lx_st & 64) != 0:
            g.lx_eof = 1
        g.lx_no = g.lx_no + 1 + g.lx_join_skip
        g.lx_join_skip = 0
        g.lx_got = 1
        if len(g.lx_l) >= 255:
            er_stop("LINE TOO LONG")
        if len(g.lx_l) == 0:
            return
        if ord(g.lx_l[-1]) == 13:
            g.lx_l = g.lx_l[:-1]
        lx_join_lines()
        lx_include_find()
        if g.lx_include_name == "":
            return
        lx_include_start()


def lx_join_lines():
    """While g.lx_l ends with a _ that joins, put the text before the _ and the next line in
    g.lx_l."""
    while True:
        lx_join_find()
        if g.lx_join == 0:
            return
        if g.lx_eof != 0:
            er_stop("NO LINE AFTER _")
        g.lx_join_next, g.lx_st = linput_2(g.lx_delim)
        if (g.lx_st & 2) != 0:
            er_stop("NO LINE AFTER _")
        if (g.lx_st & 64) != 0:
            g.lx_eof = 1
        g.lx_join_skip = g.lx_join_skip + 1
        if len(g.lx_join_next) > 0 and ord(g.lx_join_next[-1]) == 13:
            g.lx_join_next = g.lx_join_next[:-1]
        g.lx_l = g.lx_l[:g.lx_join - 1] + g.lx_join_next
        if len(g.lx_l) >= 255:
            er_stop("LINE TOO LONG")


def lx_join_find():
    """out g.lx_join: the position of the _ that joins the next line to g.lx_l, or 0. The _
    is the last character that is not a space or a tab, with a space or a tab before it,
    outside a string literal and a comment."""
    g.lx_join = 0
    g.lx_join_end = len(g.lx_l)
    while g.lx_join_end > 0 and (ch(g.lx_join_end) == 32 or ch(g.lx_join_end) == 9):
        g.lx_join_end = g.lx_join_end - 1
    if g.lx_join_end < 2:
        return
    if ch(g.lx_join_end) != 95:
        return
    g.lx_c = ch(g.lx_join_end - 1)
    if g.lx_c != 32 and g.lx_c != 9:
        return
    lx_whole()
    if g.lx_p > g.lx_n:
        return
    g.lx_join_quote = 0
    g.lx_join_escaped = 0
    while g.lx_p < g.lx_join_end:
        g.lx_c = ch(g.lx_p)
        # A \ in a !" string takes the next character, so \" does not close it.
        if g.lx_join_quote != 0 and g.lx_join_escaped != 0 and g.lx_c == 92:
            g.lx_p = g.lx_p + 2
            continue
        if g.lx_c == 34 and g.lx_join_quote == 0:
            g.lx_join_escaped = 0
            if g.lx_p > 1 and ch(g.lx_p - 1) == 33:
                g.lx_join_escaped = 1
        if g.lx_c == 34:
            g.lx_join_quote = 1 - g.lx_join_quote
        if g.lx_join_quote == 0 and g.lx_c == 39:
            return
        if g.lx_join_quote == 0 and g.lx_c != 34:
            lx_join_rem()
            if g.lx_join_is_rem != 0:
                return
        g.lx_p = g.lx_p + 1
    if g.lx_join_quote != 0:
        return
    g.lx_join = g.lx_join_end


def lx_join_rem():
    """out g.lx_join_is_rem: 1 when the word REM, which ends the line, starts at g.lx_p."""
    g.lx_join_is_rem = 0
    if g.lx_p + 2 > g.lx_n:
        return
    if g.lx_p > 1:
        g.lx_c = ch(g.lx_p - 1)
        lx_name_char()
        if g.lx_keep != 0:
            return
    for g.lx_i in range(3):
        g.lx_c = ch(g.lx_p + g.lx_i)
        lx_upper()
        if g.lx_u != ord("REM"[g.lx_i]):
            return
    if g.lx_p + 3 <= g.lx_n:
        g.lx_c = ch(g.lx_p + 3)
        lx_name_char()
        if g.lx_keep != 0:
            return
    g.lx_join_is_rem = 1


def lx_name_char():
    """out g.lx_keep: 1 when g.lx_c is a letter, a digit, _ or the dot of a name."""
    lx_upper()
    g.lx_keep = 0
    if g.lx_u >= 65 and g.lx_u <= 90:
        g.lx_keep = 1
    if g.lx_u >= 48 and g.lx_u <= 57:
        g.lx_keep = 1
    if g.lx_u == 95 or g.lx_u == 46:
        g.lx_keep = 1


def lx_include_find():
    """LX.INCLUDE.FIND. out g.lx_include_name: the file named when g.lx_l is
    #INCLUDE "NAME", else empty."""
    g.lx_include_name = ""
    lx_whole()
    if g.lx_p + 9 > g.lx_n:
        return
    if ch(g.lx_p) != 35:
        return
    g.lx_match = 1
    for g.lx_i in range(1, 8):
        g.lx_c = ch(g.lx_p + g.lx_i)
        lx_upper()
        if g.lx_u != ord("INCLUDE"[g.lx_i - 1]):
            g.lx_match = 0
    if g.lx_match == 0:
        return
    g.lx_rest = g.lx_l[g.lx_p + 7:]
    g.lx_c = instr(g.lx_rest, chr(34))
    if g.lx_c == 0:
        er_stop("BAD #INCLUDE")
    g.lx_rest = g.lx_rest[g.lx_c:]
    g.lx_c = instr(g.lx_rest, chr(34))
    if g.lx_c < 2:
        er_stop("BAD #INCLUDE")
    g.lx_include_name = g.lx_rest[:g.lx_c - 1]


def lx_include_start():
    """LX.INCLUDE.START. An included file may not include another. It starts in the
    includer's #REGION_SLOT, which LX.INCLUDE.END sets again."""
    if g.lx_including != 0:
        er_stop("#INCLUDE IN AN INCLUDED FILE")
    g.lx_source_name = g.lx_name
    g.rg_slot_outer = g.rg_slot
    g.lx_source_no = g.lx_no + g.lx_join_skip
    close_2()
    g.lx_name = g.lx_include_name
    lx_open()
    g.lx_including = 1


def lx_include_end():
    """LX.INCLUDE.END. Open the source again and skip to the line after the #INCLUDE."""
    close_2()
    g.lx_name = g.lx_source_name
    lx_open()
    g.lx_including = 0
    g.rg_slot = g.rg_slot_outer
    for g.lx_i in range(1, g.lx_source_no + 1):
        g.lx_l, g.lx_st = linput_2(g.lx_delim)
    if (g.lx_st & 66) != 0:
        g.lx_eof = 1
    g.lx_no = g.lx_source_no


def lx_whole():
    """LX.WHOLE. A line whose first characters, after spaces, are ; or ## or // is a
    comment: g.lx_p is put past its end."""
    g.lx_p = 1
    g.lx_n = len(g.lx_l)
    while True:
        if g.lx_p > g.lx_n:
            return
        g.lx_c = ch(g.lx_p)
        if g.lx_c == 32 or g.lx_c == 160 or g.lx_c == 9:
            g.lx_p = g.lx_p + 1
            continue
        break
    g.lx_d = 0
    if g.lx_p < g.lx_n:
        g.lx_d = ch(g.lx_p + 1)
    if g.lx_c == 59:
        g.lx_p = g.lx_n + 1
    if g.lx_c == 35 and g.lx_d == 35:
        g.lx_p = g.lx_n + 1
    if g.lx_c == 47 and g.lx_d == 47:
        g.lx_p = g.lx_n + 1


def lx_upper():
    """LX.UPPER. g.lx_c folded to upper case in g.lx_u. ASCII a-z and PETSCII shifted
    letters both become $41-$5A."""
    g.lx_u = g.lx_c
    if g.lx_c >= 97 and g.lx_c <= 122:
        g.lx_u = g.lx_c - 32
    if g.lx_c >= 193 and g.lx_c <= 218:
        g.lx_u = g.lx_c - 128


def lx_next():
    """LX.NEXT."""
    g.tk_s = ""
    g.tk_m = 0
    g.tk_v = 0
    while True:
        if g.lx_p > g.lx_n:
            g.tk_t = K_TT_EOL
            return
        g.lx_c = ch(g.lx_p)
        if g.lx_c == 32 or g.lx_c == 160 or g.lx_c == 9:
            g.lx_p = g.lx_p + 1
            continue
        break
    g.lx_p = g.lx_p + 1
    # ' ends the line, as a trailing comment.
    if g.lx_c == 39:
        g.lx_p = g.lx_n + 1
        g.tk_t = K_TT_EOL
        return
    if g.lx_c == 34:
        lx_string()
        return
    # !" starts a string literal that takes escapes.
    if g.lx_c == 33 and g.lx_p <= g.lx_n and ch(g.lx_p) == 34:
        g.lx_p = g.lx_p + 1
        lx_escaped()
        return
    if g.lx_c >= 48 and g.lx_c <= 57:
        lx_decimal()
        return
    if g.lx_c == 36:
        g.lx_r = 16
        lx_radix()
        return
    if g.lx_c == 37:
        g.lx_r = 2
        lx_radix()
        return
    lx_upper()
    if g.lx_u >= 65 and g.lx_u <= 90:
        lx_word()
        return
    g.tk_t = K_TT_OP
    g.tk_k = g.lx_c
    # <> <= << >= >> are one token, written with no space inside.
    if g.lx_c != 60 and g.lx_c != 62:
        return
    if g.lx_p > g.lx_n:
        return
    g.lx_d = ch(g.lx_p)
    if g.lx_c == 60 and g.lx_d == 62:
        g.tk_k = K_OP_NE
    if g.lx_c == 60 and g.lx_d == 61:
        g.tk_k = K_OP_LE
    if g.lx_c == 60 and g.lx_d == 60:
        g.tk_k = K_OP_SHL
    if g.lx_c == 62 and g.lx_d == 61:
        g.tk_k = K_OP_GE
    if g.lx_c == 62 and g.lx_d == 62:
        g.tk_k = K_OP_SHR
    if g.tk_k > 255:
        g.lx_p = g.lx_p + 1


def lx_word():
    """LX.WORD. A name: parts joined by dots, then an optional $ mark. A part is a letter,
    then letters, digits and _, 16 at most. REM is not a name: it ends the line. A % after a
    name stops the compile."""
    g.tk_s = chr(g.lx_u)
    g.lx_part_length = 1
    while g.lx_p <= g.lx_n:
        g.lx_c = ch(g.lx_p)
        lx_upper()
        if g.lx_u == 46:
            # LX.WORD.DOT
            if g.lx_p >= g.lx_n:
                er_stop("BAD NAME")
            g.lx_c = ch(g.lx_p + 1)
            lx_upper()
            if g.lx_u < 65 or g.lx_u > 90:
                er_stop("BAD NAME")
            g.tk_s = g.tk_s + "."
            g.lx_p = g.lx_p + 1
            g.lx_part_length = 0
            continue
        g.lx_keep = 0
        if g.lx_u >= 65 and g.lx_u <= 90:
            g.lx_keep = 1
        if g.lx_u >= 48 and g.lx_u <= 57:
            g.lx_keep = 1
        if g.lx_u == 95:
            g.lx_keep = 1
        if g.lx_keep == 0:
            break
        g.tk_s = g.tk_s + chr(g.lx_u)
        g.lx_p = g.lx_p + 1
        g.lx_part_length = g.lx_part_length + 1
        if g.lx_part_length > 16:
            er_stop("NAME TOO LONG")
    # LX.WORD.END
    g.tk_t = K_TT_NAME
    if g.tk_s == "REM":
        g.lx_p = g.lx_n + 1
        g.tk_t = K_TT_EOL
        return
    if g.lx_p <= g.lx_n:
        g.lx_c = ch(g.lx_p)
        if g.lx_c == 37:
            er_stop("% IS NOT A MARK: USE AS UWORD")
        if g.lx_c == 36:
            g.tk_m = K_TY_STR
        if g.tk_m != 0:
            g.tk_s = g.tk_s + chr(g.lx_c)
            g.lx_p = g.lx_p + 1
    # LX.WORD.ALIAS
    for g.lx_alias_index in range(g.nm_alias_count):
        if g.nm_alias_name[g.lx_alias_index] == g.tk_s:
            g.tk_s = g.nm_alias_target[g.lx_alias_index]
            return


def lx_decimal():
    """LX.DECIMAL. Trap: a GPC sum past 4294967295 wraps with no error, so a digit is checked
    against small limits before it is added."""
    g.tk_v = g.lx_c - 48
    while g.lx_p <= g.lx_n:
        g.lx_c = ch(g.lx_p)
        if g.lx_c < 48 or g.lx_c > 57:
            break
        if g.tk_v > 429496729:
            er_stop("OVERFLOW")
        if g.tk_v == 429496729 and g.lx_c > 53:
            er_stop("OVERFLOW")
        g.tk_v = g.tk_v * 10 + (g.lx_c - 48)
        g.lx_p = g.lx_p + 1
    g.tk_t = K_TT_NUM


def lx_radix():
    """LX.RADIX. $hex or %binary, in radix g.lx_r. g.lx_d counts the digits."""
    g.lx_d = 0
    while g.lx_p <= g.lx_n:
        g.lx_c = ch(g.lx_p)
        lx_upper()
        g.lx_h = 99
        if g.lx_u >= 48 and g.lx_u <= 57:
            g.lx_h = g.lx_u - 48
        if g.lx_u >= 65 and g.lx_u <= 70:
            g.lx_h = g.lx_u - 55
        if g.lx_h >= g.lx_r:
            break
        if g.lx_r == 16 and g.tk_v > 268435455:
            er_stop("OVERFLOW")
        if g.lx_r == 2 and g.tk_v > 2147483647:
            er_stop("OVERFLOW")
        g.tk_v = g.tk_v * g.lx_r + g.lx_h
        g.lx_d = g.lx_d + 1
        g.lx_p = g.lx_p + 1
    if g.lx_d == 0:
        er_syntax()
    g.tk_t = K_TT_NUM


def lx_string():
    """LX.STRING. A string literal, up to the closing quote. Its bytes are kept as they are,
    except a { that starts a tag."""
    g.lx_sgr_end = -1
    while True:
        if g.lx_p > g.lx_n:
            er_stop("MISSING QUOTE")
        g.lx_c = ch(g.lx_p)
        g.lx_p = g.lx_p + 1
        if g.lx_c == 34:
            break
        if g.lx_c == 123:
            lx_tag()
            continue
        g.tk_s = g.tk_s + chr(g.lx_c)
    g.tk_t = K_TT_STR


# The tags of a string literal: {NAME} is Esc [ and this text. CONS.UXI has the same sequences.
# Checklist: a change here changes CONS.UXI and the tags in UXC-HELP.md.
LX_TAGS = (
    ("CURSOR HOME", "H"), ("CLS", "2J"), ("CLEAR EOL", "K"),
    ("NORMAL", "0m"), ("REVERSE", "7m"),
    ("BLACK", "30m"), ("RED", "31m"), ("GREEN", "32m"), ("YELLOW", "33m"),
    ("BLUE", "34m"), ("MAGENTA", "35m"), ("CYAN", "36m"), ("WHITE", "37m"),
    ("ON BLACK", "40m"), ("ON RED", "41m"), ("ON GREEN", "42m"), ("ON YELLOW", "43m"),
    ("ON BLUE", "44m"), ("ON MAGENTA", "45m"), ("ON CYAN", "46m"), ("ON WHITE", "47m"))


def lx_tag():
    """LX.TAG. In: g.lx_p after a { in a string literal. Adds to g.tk_s a { for {{, or the
    sequence of the tag, with g.lx_p after the }. An m sequence right after another one from a
    tag joins it, up to the console's 4 parameters: {BLACK}{ON WHITE} is Esc[30;47m. g.lx_sgr_end
    is the length of g.tk_s after the last m sequence of a tag, else -1."""
    if g.lx_p <= g.lx_n and ch(g.lx_p) == 123:
        g.lx_p = g.lx_p + 1
        g.tk_s = g.tk_s + "{"
        return
    g.lx_q = g.lx_p
    while g.lx_p <= g.lx_n and ch(g.lx_p) != 125 and ch(g.lx_p) != 34:
        g.lx_p = g.lx_p + 1
    if g.lx_p > g.lx_n or ch(g.lx_p) != 125:
        er_stop("BAD TAG")
    name = g.lx_l[g.lx_q - 1:g.lx_p - 1].upper()
    g.lx_p = g.lx_p + 1
    text = ""
    for tag in LX_TAGS:
        if tag[0] == name:
            text = tag[1]
    if text == "":
        er_stop("BAD TAG")
    if text[-1] != "m":
        g.tk_s = g.tk_s + "\x1b[" + text
        g.lx_sgr_end = -1
        return
    if g.lx_sgr_end == len(g.tk_s) and g.lx_sgr_count < 4:
        g.tk_s = g.tk_s[:-1] + ";" + text
        g.lx_sgr_count = g.lx_sgr_count + 1
    else:
        g.tk_s = g.tk_s + "\x1b[" + text
        g.lx_sgr_count = 1
    g.lx_sgr_end = len(g.tk_s)


def lx_escaped():
    """LX.ESCAPED. A string literal after !", up to the closing quote. A \\ and the characters
    after it are one escape, FreeBASIC's: \\a \\b \\t \\n \\l \\v \\f \\r \\\\ \\" \\', 1 to 3
    decimal digits, \\&h and 1 or 2 hex digits, \\&o and 1 to 3 octal digits, and \\&b and 1 to
    8 binary digits. A { starts a tag."""
    g.lx_sgr_end = -1
    while True:
        if g.lx_p > g.lx_n:
            er_stop("MISSING QUOTE")
        g.lx_c = ch(g.lx_p)
        g.lx_p = g.lx_p + 1
        if g.lx_c == 34:
            break
        if g.lx_c == 123:
            lx_tag()
            continue
        if g.lx_c != 92:
            g.tk_s = g.tk_s + chr(g.lx_c)
            continue
        if g.lx_p > g.lx_n:
            er_stop("MISSING QUOTE")
        g.lx_c = ch(g.lx_p)
        g.lx_p = g.lx_p + 1
        lx_escape()
        g.tk_s = g.tk_s + chr(g.lx_v)
    g.tk_t = K_TT_STR


def lx_escape():
    """LX.ESCAPE. In: g.lx_c, the character after the \\, with g.lx_p after it. Out: g.lx_v,
    the byte of the escape, with g.lx_p after the escape."""
    g.lx_v = 999
    lx_upper()
    if g.lx_u == 65:
        g.lx_v = 7
    if g.lx_u == 66:
        g.lx_v = 8
    if g.lx_u == 84:
        g.lx_v = 9
    if g.lx_u == 78 or g.lx_u == 76:
        g.lx_v = 10
    if g.lx_u == 86:
        g.lx_v = 11
    if g.lx_u == 70:
        g.lx_v = 12
    if g.lx_u == 82:
        g.lx_v = 13
    if g.lx_c == 92 or g.lx_c == 34 or g.lx_c == 39:
        g.lx_v = g.lx_c
    if g.lx_v != 999:
        return
    if g.lx_c >= 48 and g.lx_c <= 57:
        g.lx_p = g.lx_p - 1
        g.lx_r = 10
        g.lx_escape_most = 3
        lx_escape_digits()
        return
    if g.lx_c != 38 or g.lx_p > g.lx_n:
        er_stop("BAD ESCAPE")
    g.lx_c = ch(g.lx_p)
    g.lx_p = g.lx_p + 1
    lx_upper()
    g.lx_r = 0
    if g.lx_u == 72:
        g.lx_r = 16
        g.lx_escape_most = 2
    if g.lx_u == 79:
        g.lx_r = 8
        g.lx_escape_most = 3
    if g.lx_u == 66:
        g.lx_r = 2
        g.lx_escape_most = 8
    if g.lx_r == 0:
        er_stop("BAD ESCAPE")
    lx_escape_digits()


def lx_escape_digits():
    """LX.ESCAPE.DIGITS. Out: g.lx_v, the value of 1 to g.lx_escape_most digits in radix
    g.lx_r at g.lx_p, with g.lx_p after them. Trap: the digits stop at g.lx_escape_most, so
    \\1234 is byte 123 and then 4."""
    g.lx_v = 0
    g.lx_d = 0
    while g.lx_p <= g.lx_n and g.lx_d < g.lx_escape_most:
        g.lx_c = ch(g.lx_p)
        lx_upper()
        g.lx_h = 99
        if g.lx_u >= 48 and g.lx_u <= 57:
            g.lx_h = g.lx_u - 48
        if g.lx_u >= 65 and g.lx_u <= 70:
            g.lx_h = g.lx_u - 55
        if g.lx_h >= g.lx_r:
            break
        g.lx_v = g.lx_v * g.lx_r + g.lx_h
        g.lx_d = g.lx_d + 1
        g.lx_p = g.lx_p + 1
    if g.lx_d == 0:
        er_stop("BAD ESCAPE")
    if g.lx_v > 255:
        er_stop("ESCAPE OUT OF RANGE")
