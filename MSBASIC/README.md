# ux6502Basic

Microsoft BASIC for the 6502, brought forward from its 1978 source and extended for new 6502
hardware with a new Unix-style kernal. This code is an exercise at the moment; maybe something
will come of it.

The code is a fork of [mist64/msbasic](https://github.com/mist64/msbasic), a ca65 version of the
original source. It is NMOS 6502 code only, with no 65C02 opcodes.

**Status:** early work. BASIC runs headless under sim65 and passes its tests. The new kernal
does not exist yet, so the screen and video commands go to ANSI codes or stubs in the sim.

## What is new

Compared to Commodore BASIC 2:

- Structure: block `IF c THEN` / `ELSE` / `END IF` (with `ELSE IF` chains), `DO` / `LOOP` /
  `EXIT [DO]`, `CONTINUE` in `FOR` and `DO` loops.
- Labels: `100 name:` at a line start, then `GOTO name`, `GOSUB name`, `RUN name`,
  `RESTORE name` and names in `ON` lists.
- Functions and operators: `INSTR([start,] a$, b$)`, `HEX$(n)`, `BIN$(n)`, `UCASE$(a$)`,
  `LCASE$(a$)`, `RPT$(a$ or code, n)`, `a MOD b`, `XOR(a,b)`, `SHL(a,n)`, `SHR(a,n)`, `PI`,
  `DEEK(addr)` and `DOKE addr,n` (16-bit PEEK and POKE), `POS(1)` for the cursor line.
- Literals: `$FF` hex and `%1010` binary.
- Screen: `CLS`, `LOCATE x,y`, `COLOR fg[,bg]`, `TEXTAT x,y,a$ or code[,color]` (prints without
  moving the cursor), `SCREEN mode`, `VPEEK(bank,addr)` and `VPOKE bank,addr,n` for video
  memory, `PAUSE n` (waits n+1 jiffies).
- File I/O by name: `OPEN lf,"name"[,mode]` (0 read, 1 write, 2 append), `CLOSE`, `PRINT#`,
  `INPUT#`, `GET#`, `CMD` and `ST`, on top of four primitives: open, close, read and write.
- `SYS address` calls machine code.
- Keywords and variable names may be typed in lowercase. Keywords are not found inside names,
  so `TOTAL` and `BORDER` are variables, but run-together code needs spaces (`FOR I`).
- 80-character input lines with backspace, for an 80x60 screen.
- Faster: `GOTO`/`GOSUB` targets and simple variable addresses are cached.
- Removed to save ROM: `LET` (`A=1` still works) and `SPC(` (use `RPT$(32,n)`).

Every keyword, with its cost in bytes, is listed in `docs/keywords.md`. Planned work is in
`TODO.md`.

Example:

```basic
10 OPEN 1,"DATA.TXT",1
20 FOR I=1 TO 3: PRINT#1,I*I: NEXT
30 CLOSE 1
40 OPEN 1,"DATA.TXT"
50 DO
60 INPUT#1,N
70 IF N>4 THEN
80 PRINT N;"IS BIG"
90 ELSE
100 PRINT N
110 END IF
120 IF ST THEN EXIT
130 LOOP
140 CLOSE 1
```

## Build

You need [cc65](https://cc65.github.io/) (ca65, ld65 and sim65), GNU make and Python 3.

```sh
make all      # build every target into build/
make test     # run the BASIC test programs under sim65
make verify   # compare cbmbasic1 and cbmbasic2 with the original ROM dumps
make run      # start the sim build interactively
```

`make verify` needs the original ROM dumps from mist64/msbasic:

```sh
git clone https://github.com/mist64/msbasic.git ref/msbasic
```

## Targets

- `sim`: headless build for sim65, with the console on stdin and stdout. This is where new
  features are developed and tested.
- `cbmbasic1`, `cbmbasic2`: Commodore PET BASIC 1 and 2. They still build byte for byte equal to
  the original ROMs, which checks that changes to the shared sources do not break the old code.
  `make pet` runs BASIC 2 in the VICE PET emulator.

## Layout

- `m6502.asm`: the original 1978 Microsoft source (MACRO-10 syntax). It is kept as history and
  is not edited.
- `src/`: the ca65 sources. `msbasic.s` builds every target; `make` passes `-D <target>`.
- `tests/`: each `NAME.bas` is typed into the sim build and its output is compared with
  `NAME.out`.
- `docs/changes.md`: every change made to the msbasic sources, and why.
- `docs/`: 6502 notes and design notes.

## Licenses and credits

- `m6502.asm`: Microsoft Corporation, MIT license (`LICENSE-microsoft`). Microsoft's notes on
  the source are in `docs/README-microsoft.md`.
- `src/`: forked from msbasic by Michael Steil and the msbasic contributors, 2-clause BSD
  (`LICENSE-msbasic`, `src/README-msbasic.md`).
- ux6502Basic, our changes and new files: public domain under the Unlicense (`LICENSE`).
  Anyone may use them for any purpose, without conditions.

This project is not affiliated with Microsoft or Commodore.
