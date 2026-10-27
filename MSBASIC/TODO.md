# TODO

Planned work for ux6502Basic. Items are done in order unless noted. Each `src/` change is logged
in `docs/changes.md` and gets a test in `tests/`.

## 1. New functions and literals

HEX$, BIN$, RPT$, MOD, π, and `$` and `%` literals (hex and binary). Then the `XOR`, `SHL` and
`SHR` operators (bitwise, on integers like `AND` and `OR`). Then `DEEK(addr)` and
`DOKE addr,value` (16-bit PEEK and POKE), and `LCASE$` and `UCASE$`. Then `TEXTAT` from
XC-BASIC: `TEXTAT x, y, text or code[, color]` prints at column x, row y without moving the
cursor (a code replaces XC-BASIC's `CHARAT`). Done for the sim with ANSI codes; the new kernal
port must replace the ANSI part with its screen calls.

Then `CONTINUE` in `FOR`/`NEXT` and `DO`/`LOOP` loops: it skips the rest of the body and goes on
with the next pass, through the matching `NEXT` or `LOOP` (the counterpart of `EXIT DO`, in
`block.s`). Done.

Then `'` as a short form of `REM`: `' text` and `PRINT X: ' text` make the rest of the line a
comment.

Then functions that read the cursor position: `POS(0)` gives the column and `POS(1)` the line
(`CONFIG_POS_LINE`). Done; in the sim the line is a count of the lines printed, and the new
kernal port must read the row from its screen call. `TEXTAT` is the matching way to set the
position.

Then maybe drop `TAB(` (`CONFIG_NO_TAB`, like `CONFIG_NO_SPC`) to save about 20 bytes: the
keyword table entry, the token test in PRINT and the column code. `RPT$(32,n-POS(0))` or
`TEXTAT` do the same job. Unlike `TAB(`, `RPT$` gives an error when the cursor is already past
column n, so decide first whether that matters.

Bug from Microsoft BASIC: `READ` misses a `DATA` statement that follows `:` and a space
(`10 X=1: DATA 5` gives ?OUT OF DATA). `FINDATA` in `input.s` compares the byte right after
the colon with the DATA token and does not skip spaces. `X=1:DATA 5` works.

Deferred: `MEMCPY` and `MEMSET` (block copy and fill). Argument order and overlapping copies are
still to be decided.

Deferred: far memory through `PEEK` and `POKE`, to revisit. Addresses go up to 24 bits:
0-$FFFF is normal CPU memory, read and written directly as now; from $10000 up the high byte is
a bank, reached through one kernal call that decides what each bank is (video memory, banked
RAM). `K_VPEEK`/`K_VPOKE` become `K_FARPEEK`/`K_FARPOKE` with the same registers, and the
`VPEEK`/`VPOKE` keywords and `vera.s` go away (80 bytes). A shared converter (`GETFAR`: `LINNUM`
plus a bank byte, about 25 bytes) and two byte routines (about 20 bytes) serve `PEEK`, `POKE`,
`DEEK` and `DOKE`, so `DOKE $1F000,N` writes a word to video memory; a word access needs an
address increment that carries into the bank. `GETADR` stays for `SYS` and `WAIT`. Estimated net
saving about 30 bytes. Open points: whether the sim gets a small real far bank for tests (about
30 bytes, sim only; the stubs return 0 now), whether to keep `DEEK`/`DOKE` (80 bytes;
`PEEK(A)+256*PEEK(A+1)` does the same), and whether memory-mapped ports on the new hardware make
all of this unnecessary.

## 2. Labels, SUB and FUNCTION

QBasic-style syntax, matching the block `IF` and `DO` already in place. Design notes and byte
estimates: `docs/sub-function.md`. Three phases:

- **A. Labels.** `GOTO name` / `GOSUB name` with `name:` label lines. Reuses the GOTO cache.
  Done (`CONFIG_LABELS`): also `RUN name`, `RESTORE name` and names in `ON` lists. Not done:
  `THEN name` (`IF c THEN name` silently does nothing; write `THEN GOTO name`).
- **B. SUB.** `SUB name(a,b$)` ... `END SUB`, `CALL name(args)`, `LOCAL v,...`. The first call
  scans for the SUB and caches its address; normal flow skips SUB bodies. Parameters and LOCAL
  use save/restore (old values pushed on entry, restored on exit, like `DEF FN` does for its one
  parameter), so variables never move and the variable cache stays valid. GARBAG must also scan
  the saved string descriptors. Frames and saved values go on a RAM stack, not the 256-byte
  6502 stack.
- **C. FUNCTION.** `FUNCTION name(x)` ... `END FUNCTION` called from expressions. Needs a
  re-entrant statement loop (run until END FUNCTION, then return into FRMEVL) and must keep FAC,
  ARG and the temporary string descriptors intact. Highest risk, so last.

## 3. Real integer math (last)

`%` variables are stored as 16-bit integers but every operation converts them to float and
back. Doing integer arithmetic directly would speed up `A%=A%+1` and similar code. It is a big
change to the expression evaluator for a modest gain, so it comes after the items above.

## 4. Inline assembly with variable passing

Put 6502 code inside a BASIC program and pass BASIC variables in and out, instead of POKEing
bytes and calling SYS. The design is still open: the syntax, where the code is stored or
assembled, and how variables reach the code (registers, a parameter block, or variable
addresses). Design notes, byte estimates and the open decisions: `docs/inline-asm.md`.

`CONST` is parked here. A proposal for typed constants (`CONST BYTE/WORD/INT/FLOAT/STRING
name = value`) was looked at and set aside: `BYTE` and `WORD` are meant for this item, so typed
declarations belong to its design. What stands in the way of a plain `CONST`:

- Only 2 characters of a variable name count, so `COLOR` and `COLORRAM` are the same variable.
  Planned fix, for all names, not only constants: `PTRGET` hashes the characters after the
  second into the 2-byte key with a seed, and a pre-pass at `RUN` walks the program and picks a
  seed under which no two spellings share a key (guess: 95-140 bytes). The same pre-pass runs
  the `CONST` lines first, so the read-only form below no longer needs the CONSTs to come first.
  Design: `docs/handoff.md`, section 3.
- `PI` is a keyword, so no constant can be named `PI`.
- No speed gain: a constant is read like a variable, and the variable cache already makes that
  fast. Every expression runs on floats, so a `WORD` type only adds a range check.
- The cheap form is a read-only variable (about 50-70 bytes): constants at the start of the
  variable table, a pointer to their end, and an error when an assignment hits one. All `CONST`s
  must run before any other variable is created. It adds safety only.

## 5. User reference of working commands

There is no user-facing list of what works yet: `CLAUDE.md` names the features briefly for
development, and `docs/changes.md` explains how each change was made. Write a reference
(for example `docs/reference.md`) that lists every statement, function and operator the sim
build supports, with syntax, a short example and its errors, and marks what is new compared
with Microsoft BASIC. Keep it updated with each new feature.

## 6. GW-BASIC's EDIT and soft keys (6502dos target)

- **`EDIT n`.** Lists line n with no OK and puts the cursor at its start, for the full-screen
  editor. A missing line is ?UNDEF'D STATEMENT ERROR. Design: `LINGET`, `FNDLIN`, point
  `GOSTROUT` at an `EDIT_END` hook (as SAVE does), drop NEWSTT's return, `jmp LIST_LINE`.
  `EDIT_END` puts `GOSTROUT` back and moves the cursor to column 0 of the line's row with
  `con_cursor`; LIST prints a CRDO after the line when another line follows, so the row is
  one up when the column is 0. A shared `DOS_HOOK`/`DOS_UNHOOK` pair for SAVE and EDIT saves
  about 9 bytes. Estimate: 55 bytes and 6 of keyword table.
- **F1 to F10 soft keys, `KEY n,a$`, `KEY LIST`.** ROM: `con_screen` takes r1 = 10 slots of
  16 bytes, each a text ended by 0; F1 to F10 type their slot, a CR as Enter. One KERNELRAM
  byte holds the offset of the next character; 15, the 0 that ends slot 0, means none.
  Estimate: 36 bytes of bank 0. MSBASIC: `KEY_TABLE` (160 bytes) in `IORAM`, which moves to
  `$9B80` (BASIC loses 128 bytes), GW-BASIC's defaults packed in ROM, with FILES, EDIT, HELP
  and CLS for LPT1, TRON, TROFF and SCREEN 0,0,0. `KEY LIST` shows a control character as `^`
  and a letter. `LIST` needs `TOKEN_LIST`. Estimate: 200 bytes.
- Not planned: `KEY ON`/`KEY OFF` and the key labels on the bottom row, which need a scroll
  region in the console.

## 7. LOADFONT and the settings store (6502dos target)

- **`LOADFONT "name"`.** Loads a 2048-byte 8x8 font file into VRAM `$1F000`, as `FONT.COM`
  does. The ROM has no font call, so the keyword reads the file through `K_READ` and writes
  VRAM through `K_VPOKE`. Syntax, errors and cost to be decided.
- **Read and save a key of `C:\6502DOS.REG`.** The ROM calls `reg_get` (55) and `reg_set`
  (56) read and set a key; `docs/API.md` of the 6502DOS repo has their registers and errors.
  The keyword or function names, syntax and cost are to be decided.

## Parked (long term)

Not scheduled. They need the new kernal's file calls first.

- `CHAIN "name"`: load another program and run it, as a way to split programs that do not fit
  in memory.
- `DIR`: list the files on the disk.
