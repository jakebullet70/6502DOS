# Keywords and their cost in bytes

All keywords of the `sim` build, done and planned, with the bytes each feature adds to the
image. Measured on 2026-11-08.

## How the costs are measured

Each feature has a `CONFIG_` flag in `src/defines_sim.s`. The cost of a feature is the size of
the normal sim image minus the size of a build with only that flag turned off. That covers the
keyword table entry, the dispatch address and the code. Costs are measured one flag at a time,
so features that share code may not add up exactly. Planned costs are estimates.

A flag that another flag needs is measured with that flag off too: `CONFIG_SCREEN` with
`CONFIG_VERA` off, `CONFIG_TEXTAT` with `CONFIG_VERA` and `CONFIG_SCREEN` off, and
`CONFIG_FAST_FIN` with `CONFIG_RADIX_LIT` off.

To measure again: copy `src/` to a scratch folder, comment out one flag in `defines_sim.s`,
build with `ca65 -D sim msbasic.s` and `ld65 -C sim.cfg`, and compare the `.bin` sizes.

## Totals

| Item | Bytes |
|---|---|
| sim image, $C000-$F1B1 (without the 12-byte sim65 header) | 12722 |
| of which RAM variables of `handle_io.s` and `vera.s` (`IORAM` segment) | 643 |
| ROM space in `sim.cfg` ($C000 + $3F00) | 16128 |
| free | 3406 |
| new keywords (all items in "New keywords" below) | 2573 |
| speed-ups and internals (all items in "Internals" below) | 791 |

Segments of the sim image:

| Segment | Bytes |
|---|---|
| VECTORS (dispatch tables) | 205 |
| KEYWORDS (keyword names) | 480 |
| ERROR (error messages) | 249 |
| CODE | 7941 |
| CHRGET | 29 |
| INIT | 271 |
| EXTRA (sim I/O and most of our additions) | 2904 |
| IORAM | 643 |

## Keyword table

The sim build has 122 tokens, $80-$F9. Inserting a keyword shifts the tokens after it, so saved
tokenized programs are only valid for the build that wrote them.

| Token | Keyword | | Token | Keyword | | Token | Keyword |
|---|---|---|---|---|---|---|---|
| 80 | END | | A9 | **VPOKE** | | D2 | **MASK** |
| 81 | FOR | | AA | **SCREEN** | | D3 | **HIT** |
| 82 | NEXT | | AB | **PSET** | | D4 | SGN |
| 83 | DATA | | AC | **LINE** | | D5 | INT |
| 84 | INPUT# | | AD | **FRAME** | | D6 | ABS |
| 85 | INPUT | | AE | **RECT** | | D7 | USR |
| 86 | DIM | | AF | **CIRCLE** | | D8 | FRE |
| 87 | READ | | B0 | **CHAR** | | D9 | POS |
| 88 | GOTO | | B1 | **VMEMSET** | | DA | SQR |
| 89 | RUN | | B2 | **MEMCPYMV** | | DB | RND |
| 8A | IF | | B3 | **MEMCPYVM** | | DC | LOG |
| 8B | RESTORE | | B4 | **VLOAD** | | DD | EXP |
| 8C | GOSUB | | B5 | **SPRITE** | | DE | COS |
| 8D | RETURN | | B6 | **CLS** | | DF | SIN |
| 8E | REM | | B7 | **LOCATE** | | E0 | TAN |
| 8F | STOP | | B8 | **COLOR** | | E1 | ATN |
| 90 | ON | | B9 | TAB( | | E2 | PEEK |
| 91 | WAIT | | BA | TO | | E3 | **DEEK** |
| 92 | LOAD (stub) | | BB | FN | | E4 | LEN |
| 93 | SAVE (stub) | | BC | THEN | | E5 | STR$ |
| 94 | DEF | | BD | NOT | | E6 | VAL |
| 95 | POKE | | BE | STEP | | E7 | ASC |
| 96 | **DOKE** | | BF | + | | E8 | CHR$ |
| 97 | PRINT# | | C0 | - | | E9 | **HEX$** |
| 98 | PRINT | | C1 | * | | EA | **BIN$** |
| 99 | **CONTINUE** | | C2 | / | | EB | **UCASE$** |
| 9A | CONT | | C3 | ^ | | EC | **LCASE$** |
| 9B | LIST | | C4 | AND | | ED | **SPRITEHIT** |
| 9C | CLEAR | | C5 | OR | | EE | LEFT$ |
| 9D | CMD | | C6 | **MOD** | | EF | RIGHT$ |
| 9E | SYS | | C7 | > | | F0 | MID$ |
| 9F | OPEN | | C8 | = | | F1 | **INSTR** |
| A0 | CLOSE | | C9 | < | | F2 | **RPT$** |
| A1 | GET | | CA | **OFF** | | F3 | **PI** |
| A2 | NEW | | CB | **AT** | | F4 | **XOR** |
| A3 | **ELSE** | | CC | **SHAPE** | | F5 | **SHL** |
| A4 | **DO** | | CD | **LOWCOL** | | F6 | **SHR** |
| A5 | **LOOP** | | CE | **HICOL** | | F7 | **VPEEK** |
| A6 | **EXIT** | | CF | **XYSIZE** | | F8 | **POINT** |
| A7 | **TEXTAT** | | D0 | **XYFLIP** | | F9 | GO |
| A8 | **PAUSE** | | D1 | **ZDEPTH** | | | |

Bold keywords are new. The others come from Microsoft BASIC (CBM BASIC 2 set). `LOAD` and `SAVE`
are stubs that do nothing in the sim build. Removed from the CBM set: `LET` (`CONFIG_NO_LET`,
saves 5 bytes; `A=1` still works), `SPC(` (`CONFIG_NO_SPC`, saves 13 bytes; `RPT$(32,n)` does
the same) and `VERIFY`. `END IF` and `EXIT DO` are built from existing tokens, so they need no
table entries.

`OFF` to `HIT` are the clause words of `SPRITE`. The tokenizer crunches them only in a `SPRITE`
statement, up to the next `:`; elsewhere they are names, so `AT` and `OFF` work as variables.
`SPRITE` itself takes `COLOR`, `ON` and `CLEAR` as clause words. After a variable, a clause word
is not crunched: `Y SHAPE` reads as the variable `YS`.

## New keywords (done)

| Keywords | Flag | Bytes |
|---|---|---|
| `IF c THEN` / `ELSE` / `END IF`, `DO` / `LOOP` / `EXIT [DO]`, `CONTINUE` | `CONFIG_BLOCK` | 307 |
| labels: `name:` lines, `GOTO`/`GOSUB`/`RUN`/`RESTORE name`, names in `ON` lists (no keyword) | `CONFIG_LABELS` | 126 |
| `TEXTAT x,y,a$ or code[,color]` (ANSI codes in the sim) | `CONFIG_TEXTAT` | 181 |
| `INSTR([start,] a$, b$)` | `CONFIG_INSTR` | 167 |
| `a MOD b` | `CONFIG_MOD` | 160 |
| `$FF`, `%1010` literals (no keyword) | `CONFIG_RADIX_LIT` | 147 |
| integer digit reader that the literals need | `CONFIG_FAST_FIN` | 120 |
| `XOR(a,b)`, `SHL(a,n)`, `SHR(a,n)` | `CONFIG_BITFN` | 128 |
| `RPT$(a$ or code, n)` | `CONFIG_RPT` | 90 |
| `HEX$(n)`, `BIN$(n)` | `CONFIG_HEXBIN` | 108 |
| `UCASE$(a$)`, `LCASE$(a$)` | `CONFIG_CASE` | 70 |
| `DEEK(addr)`, `DOKE addr,n` | `CONFIG_DEEK` | 80 |
| `PAUSE jiffies` (like `SLEEP` on the X16, but n is required; busy loop in the sim) | `CONFIG_PAUSE` | 44 |
| video memory, sprites and graphics, below (stubs in the sim; needs `CONFIG_SCREEN`) | `CONFIG_VERA` | 733 |
| `CLS`, `LOCATE x,y`, `COLOR fg[,bg]` (ANSI codes; needs `CONFIG_TEXTAT`) | `CONFIG_SCREEN` | 79 |
| `PEEK` keeps LINNUM, so `DOKE a,PEEK(b)` works | `CONFIG_PEEK_SAVE_LINNUM` | 12 |
| `PI` | `CONFIG_PI` | 21 |
| **Total** | | **2573** |

`CONFIG_FAST_FIN` also makes number parsing faster; `CONFIG_RADIX_LIT` does not build without it.

`CONFIG_VERA` holds these keywords. A video address is 0 to $1FFFF; a larger one is ?ILLEGAL
QUANTITY ERROR. A len of 0 copies or fills nothing.

| Keyword | Does |
|---|---|
| `VPEEK(addr)` | the byte at a video address |
| `VPOKE addr,n` | writes a byte to video memory |
| `VMEMSET addr,n,len` | fills len bytes of video memory with n |
| `MEMCPYMV ram,addr,len` | copies len bytes from RAM to video memory |
| `MEMCPYVM addr,ram,len` | copies len bytes from video memory to RAM |
| `VLOAD "name",addr` | copies a whole file, raw, to video memory; a missing file is ?FILE NOT FOUND ERROR |
| `SPRITE n clause ...` | sets sprite n, 0 to 127, by its clauses, in any order |
| `SPRITE CLEAR HIT` | clears the groups that `SPRITEHIT` reports |
| `SPRITEHIT(g)` | -1 if sprites that share bit g, 0 to 3, of their masks collided since the last `SPRITE CLEAR HIT`, else 0 |
| `SCREEN mode` | the screen mode, 0 to 3 |
| `PSET x,y,c` | sets a pixel to color c |
| `POINT(x,y)` | the color of a pixel |
| `LINE x1,y1,x2,y2,c` | a line, both ends included |
| `FRAME x1,y1,x2,y2,c` | the edge of a box, x1 <= x2 and y1 <= y2 |
| `RECT x1,y1,x2,y2,c` | a filled box, x1 <= x2 and y1 <= y2 |
| `CIRCLE x,y,r,c` | a circle, r 0 to 255 |
| `CHAR x,y,a$ or code,c` | the text's glyphs, 8 pixels apart; clear bits keep the bitmap |

The clauses of `SPRITE`:

| Clause | Sets |
|---|---|
| `ON`, `OFF` | z-depth 3, 0 |
| `AT x,y` | the position, 0 to 65535 each |
| `SHAPE s` | the shape at video address s*32 |
| `COLOR c` | the palette offset, 0 to 15 |
| `LOWCOL`, `HICOL` | 4, 8 bits a pixel |
| `XYSIZE w,h` | the size, 8, 16, 32 or 64 pixels each |
| `XYFLIP x,y` | flip across, down: 0 or 1 each |
| `ZDEPTH z` | 0 off, 1 behind layer 0, 2 between the layers, 3 in front |
| `MASK m` | the collision mask, 0 to 15 |

`SHAPE $80` puts the shape at video address $1000:

```basic
10 SPRITE 0 SHAPE $80 XYSIZE 16,16 AT 100,50 ON
20 SCREEN 2: RECT 0,0,319,239,1: CIRCLE 160,120,50,14
30 CHAR 8,8,"HELLO",15
```

In the `6502dos` target, `CONFIG_VERA` takes 960 bytes of bank 2 and 9 bytes of `IORAM`.

`QUIT [n]` (`CONFIG_QUIT`, 18 bytes) is in the `6502dos` target only. It ends BASIC and returns
to the shell with exit code n, 0 to 255, or 0.

`HELP [topic]` (`CONFIG_HELP`, 348 bytes) is in the `6502dos` target only, in direct mode only;
in a program it gives ?SYNTAX ERROR. It prints the topic from `basic\HELPBAS.HLP` in the folder
of `BASIC.COM`, or with no topic the topic names.

`LOAD "name"` and `SAVE "name"` (114 bytes, no flag) work in the `6502dos` target only. SAVE
writes the program as text, as LIST shows it but with no space before a line number (23 bytes
more); LOAD does a NEW and reads the lines back. A LOAD in a program runs the program it loads.
SAVE ends a program, as LIST does.

`KILL "name"` (29 bytes, no flag) and `NAME "old" AS "new"` (74 bytes, no flag) work in the
`6502dos` target only. KILL deletes a file. NAME renames a file or a directory; a new name that
exists gives ?FILE EXISTS ERROR. `AS` is not a keyword.

`FILES ["pattern"]` (275 bytes, no flag; 23 bytes of RAM) works in the `6502dos` target only.
It lists the names that match, each with its size or `<DIR>`, then their count, as the shell's
`FILES` does. A directory's name lists the names in it; no pattern lists the current directory.

## Internals (no keywords)

| Feature | Flag | Bytes |
|---|---|---|
| simple variable address cache | `CONFIG_VAR_CACHE` | 358 |
| GOTO/GOSUB target cache | `CONFIG_GOTO_CACHE` | 347 |
| keyword table longer than 256 bytes | `CONFIG_KW16` | 22 |
| safer check in PTRGET | `CONFIG_SAFE_NAMENOTFOUND` | 8 |
| no keyword search inside a name (`BORDER` is not `B`,`OR`,`DER`, `TOTAL` is not `TO`,`TAL`) | `CONFIG_NAME_NOCRUNCH` | 64 |
| `POS(1)` gives the line; a new line clears the column | `CONFIG_POS_LINE` | 10 |
| no `LET` keyword | `CONFIG_NO_LET` | -5 |
| no `SPC(` keyword | `CONFIG_NO_SPC` | -13 |
| **Total** | | **791** |

File I/O (`OPEN`, `CLOSE`, `PRINT#`, `INPUT#`, `GET#`, `CMD`, `SYS`, `ST`) uses the CBM keywords
through `handle_io.s`. Its cost is not listed, because the sim build does not assemble without it.

In the `6502dos` target, `BASIC NAME.BAS` loads NAME.BAS and runs it: 118 bytes, with no flag.

## Planned keywords (estimates)

In `TODO.md` order. Table bytes are the name plus a 2-byte dispatch address. Code bytes are rough
guesses until the code is written.

| Keywords | TODO | Table | Code (est.) | Total (est.) |
|---|---|---|---|---|
| `MEMCPY`, `MEMSET` (deferred) | 1 | 16 | 90 | 106 |
| `'` as short `REM` (no table entry) | 1 | 0 | 15 | 15 |
| `SUB` / `END SUB`, `CALL`, `LOCAL` | 2B | 18 | 600 | 618 |
| `FUNCTION` / `END FUNCTION` | 2C | 10 | 400 | 410 |
| **Total** | | **44** | **1105** | **1149** |

Real integer math (TODO 3) adds no keywords but a large amount of code; inline assembly (TODO 4)
is still an open design. With the estimates above, about 2250 bytes of the 16128-byte ROM space
would remain.
