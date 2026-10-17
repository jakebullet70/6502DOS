"""Build UXC.HELP's content from help/UXC-HELP.md.

    python help/MKHELP.PY

Writes help/HELP-TXT/UXC.HELP.IDX and one H001.HLP ... Hnnn.HLP per topic. The
viewer, src/UXC.HELP.BASL, is GPC.HELP from the GPC repo with the GP.BASIC content
taken out. It reads the same two formats GPC's MKHELP.PY writes, so this script
writes them the same way. It is much smaller because its source is one Markdown
file written for it, not the GPC manual.

THE SOURCE, help/UXC-HELP.md:

    # Category            a heading row in the index; cannot be selected
    ## Topic title        a topic: one .HLP file
    ### Section title     a section inside the topic, with its own index row
    plain text            wrapped to WIDTH; a "- " line is a list item
    ```                   a code block: dimmed lines, what X exports
    [[Topic title]]       a cross reference; the text keeps the title, and the
                          topic gets a SEE ALSO block with a link to it
    [[NAME.UXB]]          a link to the example program samples/NAME.UXB

Every file in samples/ also gets a row under EXAMPLE PROGRAMS, at the end of
the index. The viewer opens it from //EXAMPLES/:NAME and paints it as source.

THE .HLP FORMAT is one screen line per file line, first character a marker:
    @  line 1: the topic's title       =  section header, a full-width bar
    .  text, already wrapped           :  code, dimmed, what X exports
    >  cross reference, ">row|text", where row is a 1-based index row

THE INDEX is a comment line, "N|rows", then a row each: "type|topic|line|lines|text".
Type H is a heading, T a topic, S a section, E an example. "line" is the file
line a section header sits on (the @ line is line 0). "lines" is the topic's
line count, not counting the @ line.

Line endings are LF. The script stops on any character outside printable
ASCII, because the X16 side would show it as the wrong glyph.
"""

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SOURCE = os.path.join(HERE, "UXC-HELP.md")
OUT = os.path.join(HERE, "HELP-TXT")
EXAMPLES = os.path.join(ROOT, "samples")
IDXNAME = "UXC.HELP.IDX"
EXAMPLES_NAME = "EXAMPLE PROGRAMS"

WIDTH = 76

# The viewer's limits. Each is a #DEFINE in src/UXC.HELP.BASL; change them together.
IDX_ROWS = 210      # HELP.MAXIX
IDX_REC = 9         # HELP.IXREC
IDX_WIDE = 72       # HELP.IXWIDE
BANK = 8192         # HELP.BANKSIZE
TOPIC_LINES = 2048  # HELP.MAXLINES
TEXT_BANKS = 8      # HELP.TEXTBANKS
LINE_WIDE = 78      # HELP.COLS - 2
TOPIC_LINKS = 20    # HELP.MAXPICK

LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


class Topic:
    def __init__(self, title, cat):
        self.title = title
        self.cat = cat
        self.lines = []     # the body, without the @ line
        self.secs = []      # (title, index into lines)
        self.refs = []      # link targets, in order of first use
        self.number = 0
        self.row = 0


def fail(msg):
    sys.exit("MKHELP: " + msg)


def ascii_only(text, where):
    for ch in text:
        if not (32 <= ord(ch) < 127):
            fail("%s: character U+%04X is not printable ASCII" % (where, ord(ch)))


def wrap(text, indent="", first=""):
    out, cur = [], first
    for word in text.split():
        if cur.strip() and len(cur) + 1 + len(word) > WIDTH:
            out.append(cur)
            cur = indent + word
        elif cur.strip() and not cur.endswith(" "):
            cur += " " + word
        else:
            cur += word
    out.append(cur)
    return out


def gap(t):
    """One blank line, never two."""
    if not t.lines or t.lines[-1] != ".":
        t.lines.append(".")


def header(t, title):
    """A section header: a blank line, the bar, a blank line."""
    gap(t)
    t.lines.append("=" + title)
    t.lines.append(".")
    return len(t.lines) - 2


def parse(path):
    """The Markdown source as categories, each a list of topics."""
    cats, t, para, code = [], None, [], None

    def flush():
        if not para:
            return
        text = " ".join(para)
        for target in LINK_RE.findall(text):
            if target not in t.refs:
                t.refs.append(target)
        text = LINK_RE.sub(r"\1", text)
        if text.startswith("- "):
            t.lines.extend("." + ln for ln in wrap(text[2:], "    ", "  - "))
        else:
            t.lines.extend("." + ln for ln in wrap(text))
        del para[:]

    for n, raw in enumerate(open(path, encoding="utf-8").read().split("\n"), 1):
        line = raw.rstrip()
        ascii_only(line, "UXC-HELP.md line %d" % n)
        if code is not None:
            if line.startswith("```"):
                t.lines.append(".")
                code = None
            else:
                if len(line) > WIDTH:
                    fail("UXC-HELP.md line %d: code line over %d columns" % (n, WIDTH))
                t.lines.append(":" + line)
            continue
        if line.startswith("```"):
            if t is None:
                fail("UXC-HELP.md line %d: code before the first topic" % n)
            flush()
            gap(t)
            code = []
            continue
        m = re.match(r"^(#{1,3}) (.+)$", line)
        if m:
            if t is not None:
                flush()
            level, title = len(m.group(1)), m.group(2).strip()
            if level == 1:
                cats.append((title, []))
                t = None
            elif level == 2:
                if not cats:
                    fail("UXC-HELP.md line %d: a topic before the first category" % n)
                t = Topic(title, cats[-1][0])
                cats[-1][1].append(t)
                header(t, title.upper())
            else:
                if t is None:
                    fail("UXC-HELP.md line %d: a section outside a topic" % n)
                t.secs.append((title, header(t, title)))
            continue
        if t is None:
            continue
        if not line.strip():
            flush()
            if t.lines:
                gap(t)
        elif line.startswith("- ") and para:
            flush()
            para.append(line)
        else:
            para.append(line.strip())
    if t is not None:
        flush()
    return cats


def main():
    if not os.path.exists(SOURCE):
        fail("no " + SOURCE)
    cats = parse(SOURCE)
    topics = [t for _, ts in cats for t in ts]
    examples = []
    if os.path.isdir(EXAMPLES):
        for name in sorted(os.listdir(EXAMPLES)):
            path = os.path.join(EXAMPLES, name)
            if os.path.isfile(path):
                text = open(path, encoding="latin-1").read()
                examples.append((name.upper(), len(text.splitlines())))

    # Number the topics, then lay out the index rows so each topic knows its row.
    rows, number = [], 0
    for cat, ts in cats:
        rows.append(["H", 0, 0, 0, cat.upper()])
        for t in ts:
            number += 1
            t.number = number
            t.row = len(rows) + 1
            rows.append(["T", t.number, 0, 0, "  " + t.title])
            for title, at in t.secs:
                rows.append(["S", t.number, at + 1, 0, "     " + title])
    exrow = {}
    if examples:
        rows.append(["H", 0, 0, 0, EXAMPLES_NAME])
        for name, count in examples:
            exrow[name] = len(rows) + 1
            rows.append(["E", 0, 0, count, "  " + name])

    # The SEE ALSO block, now that every target has a row.
    bytitle = dict((t.title.upper(), t) for t in topics)
    for t in topics:
        links = []
        for ref in t.refs:
            key = ref.upper()
            if key in bytitle and bytitle[key] is not t:
                links.append(">%d|%s" % (bytitle[key].row, bytitle[key].title[:WIDTH - 6]))
            elif key in exrow:
                links.append(">%d|%s" % (exrow[key], key))
            elif key not in bytitle:
                fail("topic %r links to %r, which is no topic and no example" % (t.title, ref))
        if links:
            header(t, "SEE ALSO")
            t.lines.extend(links)
        while t.lines and t.lines[-1] == ".":
            t.lines.pop()
        if len(t.lines) > TOPIC_LINES:
            fail("topic %r is %d lines; the viewer holds %d" % (t.title, len(t.lines), TOPIC_LINES))
        if len(links) > TOPIC_LINKS:
            fail("topic %r has %d links; the viewer holds %d" % (t.title, len(links), TOPIC_LINKS))
        banks, used = 1, 0
        for ln in t.lines:
            width = min(len(ln.split("|", 1)[-1] if ln.startswith(">") else ln[1:]), LINE_WIDE)
            if used + width > BANK:
                banks, used = banks + 1, 0
            used += width
        if banks > TEXT_BANKS:
            fail("topic %r needs %d text banks; the viewer has %d" % (t.title, banks, TEXT_BANKS))
    for r in rows:
        if r[0] in "TS":
            r[3] = len(next(t for t in topics if t.number == r[1]).lines)
        if len(r[4]) > IDX_WIDE:
            r[4] = r[4][:IDX_WIDE - 3] + "..."

    if len(rows) > IDX_ROWS:
        fail("%d index rows; the viewer holds %d" % (len(rows), IDX_ROWS))
    chars = sum(len(r[4]) for r in rows)
    room = BANK - IDX_ROWS * IDX_REC
    if chars > room:
        fail("%d characters of index text; the viewer holds %d" % (chars, room))

    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    for t in topics:
        with open(os.path.join(OUT, "H%03d.HLP" % t.number), "w", encoding="ascii", newline="\n") as fh:
            fh.write("\n".join(["@" + t.title[:WIDTH]] + t.lines) + "\n")
    # A shorter run than the last one leaves files no index row reaches.
    for name in os.listdir(OUT):
        if re.match(r"^H[0-9]{3}\.HLP$", name) and int(name[1:4]) > len(topics):
            os.remove(os.path.join(OUT, name))
    with open(os.path.join(OUT, IDXNAME), "w", encoding="ascii", newline="\n") as fh:
        fh.write("# UXC.HELP index, generated by help/MKHELP.PY -- do not edit\n")
        fh.write("N|%d\n" % len(rows))
        for r in rows:
            fh.write("%s|%s|%s|%s|%s\n" % tuple(r))
    print("MKHELP: %d topics, %d examples, %d of %d index rows, %d of %d index characters"
          % (len(topics), len(examples), len(rows), IDX_ROWS, chars, room))


main()
