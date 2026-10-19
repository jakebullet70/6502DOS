# Changes to the msbasic sources

This is a log of what we changed in `src/` compared with mist64/msbasic (commit 2a0bc2f), and why.
Add an entry with each fix. Changes to shared files are wrapped in `.ifdef SIM` (or a later
target symbol), so the original targets still build byte for byte (`make verify`).

## sim target (headless sim65 build)

New files: `defines_sim.s`, `sim_extra.s`, `sim_iscntc.s`, `sim.cfg`. The hooks in shared files
are listed below.

- `defines.s`, `extra.s`, `iscntc.s`: include the sim files when ca65 runs with `-D sim`.
- `header.s`: writes the sim65 file header (signature, version 2, CPU 6502, C stack pointer
  `SIM_CSP`, load address $C000, reset address `COLD_START`).
- `init.s`, RAM scan at `L40D7`: in sim65 all 64K is RAM, so the scan stops at page
  `SIM_RAMTOP` ($C0), just below the interpreter.

## Zero-page overlap in the w65c816sxb layout

`defines_sim.s` started as a copy of `defines_w65c816sxb.s`. That layout puts `Z14` and
`TEMPPT` both at $65, so `FRE` hangs. `defines_sim.s` sets `ZP_START4 = $66`. Upstream
`defines_w65c816sxb.s` is unchanged.

## No MEMORY SIZE? or TERMINAL WIDTH? prompt at cold start

- `init.s` (two places): the prompt blocks were `.ifndef CONFIG_CBM_ALL`. They are now
  `.if (!.def(CONFIG_CBM_ALL)) && (!.def(SIM))`.
- Memory: the cold start scans RAM, as it does when you answer the prompt with Return.
- Width: `defines_sim.s` sets `WIDTH = 80` and `WIDTH2 = 70` (the last comma tab stop, the value
  BASIC derives for width 80). The X16 text screen is at most 80x60.
- Pitfall: in ca65, `!` binds more loosely than `&&`. Without the parentheses,
  `.if !.def(A) && !.def(B)` means `!(.def(A) && !.def(B))`, and the prompts come back.

## Echo only when asked

An interactive Windows console echoes typed input itself, so the sim echoed every line twice.
`MONRDKEY` in `sim_extra.s` now echoes only when sim65 gets an argument after the program file
(`sim65 build/sim.bin echo`). The test runner uses that argument, so stdout is a full session
transcript. The check runs on the first key read: `SIMARGS` calls the sim65 `PVArgs` paravirt
call ($FFF8) with the C stack pointer set to `SIM_ARGS_TOP` ($0400), and stores the result in
`SIMECHO`.

Side effect: a piped run without the argument shows blank lines where the input would be.

## Lowercase keywords and variable names

Typed `list` gave `?SYNTAX ERROR`, because the tokenizer only knows uppercase. `program.s`
(`PARSE_INPUT_LINE`) now calls `SIM_UPPER` (in `sim_extra.s`) in two places:

- after the quote and DATA checks: the character is folded and stored back in the input buffer,
  so variable names are saved in uppercase;
- in the keyword lookahead at `L2498`: the next characters are folded before they are compared
  with the keyword table.

Text in quotes, `REM` and `DATA` keeps its case, because those paths skip both calls.

## I/O layer

The interpreter used to call CBM KERNAL routines by name. It now calls neutral entry points, so a
target without the CBM KERNAL can supply its own. `io.s` (included at the end of `defines.s`)
documents each entry point and the register rules the interpreter relies on, and maps them to the
KERNAL for CBM targets:

| Layer       | CBM KERNAL | Called from                          |
|-------------|------------|--------------------------------------|
| `IO_CHKIN`  | `CHKIN`    | `input.s` (GET#, INPUT#)             |
| `IO_CHKOUT` | `CHKOUT`   | `misc1.s` (CMD, PRINT#)              |
| `IO_CLRCH`  | `CLRCH`    | `input.s`, `program.s` (ERROR)       |
| `IO_CHRIN`  | `CHRIN`    | `inline.s` (GETLN)                   |
| `IO_CLALL`  | `CLALL`    | `program.s` (RUN, NEW, CLEAR)        |

`MONCOUT`, `MONRDKEY` and `ISCNTC` stay as they are; every target already provides them.

Rules that are not obvious from the KERNAL documentation: `IO_CHKIN` and `IO_CHKOUT` must keep X
(the caller stores it in `CURDVC`), `IO_CHRIN` must keep X (INLIN's buffer index), and `IO_CLRCH`
must keep X (ERROR holds the error number in X).

Other shared-file changes:

- `init.s` (clear `CURDVC`) and `program.s` (`IO_CLALL`): the condition was `CONFIG_CBM_ALL`; it
  is now `CONFIG_FILE`, which is what the code depends on. For the original targets this is the
  same set (only the CBM targets have `CONFIG_FILE`).
- `program.s`: new label `ERROR_PRINTED` after the error message loop, so `handle_io.s` can print
  its own messages and then finish like ERROR.

The labels are aliases of the same addresses, so the CBM builds are unchanged (`make verify`).

## Files in the sim target (handle-based I/O)

`defines_sim.s` now sets `CONFIG_FILE` and `CONFIG_HANDLE_IO`. The sim build has PRINT#, INPUT#,
GET#, CMD, OPEN, CLOSE, SYS and the status variable ST. This is a test bed for the X16 target: the
new X16 kernal also uses Unix-style handles (0 stdin, 1 stdout).

- `handle_io.s` (new, shared by handle-based targets): implements the I/O layer and the OPEN,
  CLOSE and SYS statements on top of four target primitives, `K_OPEN`, `K_CLOSE`, `K_READ` and
  `K_WRITE` (contract at the top of the file). It keeps a table of up to 10 open files (logical
  file number, handle, mode). Its variables are in segment `IORAM`, which the target's `.cfg`
  places in RAM.
- Syntax: `OPEN lf,"name"[,mode]`, with lf 1-255 and mode 0 read (default), 1 write (create or
  truncate), 2 append. There is no device number; on the X16 the kernal picks the driver from the
  name. `CLOSE lf` on a file that is not open is ignored, as on CBM. When the closed file is the
  current input or output (for example after CMD), the console takes over again.
- End of file: files opened for reading are read one byte ahead, so ST gets bit 6 ($40) with the
  last byte, as on CBM machines. Reading past the end returns CR: first with ST = 64 (this ends a
  last line that has no line end), then with ST = 66. Bit 1 makes INPUT# stop (existing code in
  `input.s`).
- Errors: the main error table has only 6 bytes left (offsets are 8 bits), so `handle_io.s` has
  its own table (FILE OPEN, FILE NOT OPEN, FILE NOT FOUND, NOT INPUT FILE, NOT OUTPUT FILE, TOO
  MANY FILES) and prints it the way ERROR does.
- `sim_extra.s`: the console routines became the four primitives, using the sim65 calls PVOpen,
  PVClose, PVRead and PVWrite. Handles are host file descriptors. Every handle converts line ends
  (BASIC CR, host LF). Echo and exit on end of stdin are unchanged and apply only to the console.
- `eval.s`: under `CONFIG_HANDLE_IO`, reading the variable ST gives `Z96` (the status byte). The
  CBM code for TI and ST depends on the KERNAL clock, so it is not reused. ST can still be
  assigned like a normal variable, but reading it always gives the status.
- `print.s` (`OUTSP`): with `CONFIG_FILE`, BASIC prints CRSR RIGHT ($1D) to the screen, for
  example after the INPUT prompt. Handle-based targets print a space.
- `defines_sim.s`: `CURDVC` = $F2, `Z96` = $F3, console handles `K_STDIN` = 0 and
  `K_STDOUT` = 1. `sim.cfg`: segment `IORAM` at the end of the BASIC image (all RAM in sim65).

Known limits:

- INPUT# goes through the console line editor: lines are cut at 80 characters (see below), BS
  and DEL delete, and control characters are dropped.
- GET# converts line ends like text, so binary files cannot be read byte for byte.

## 80-character input line

Typed lines were cut at 71 characters (`cpx #$47` in `inline.s`), the old Microsoft teletype limit,
and the buffer was in zero page. The X16 screen is 80 characters wide.

- `defines_sim.s`: `INPUTBUFFER = $0200`, as on CBM machines. Upstream already supports this
  layout (`CONFIG_NO_INPUTBUFFER_ZP`, `CONFIG_INPUTBUFFER_0200`): the direct-mode test compares the
  high byte of `TXTPTR` with $02, and the bytes at $01FD-$01FF in front of the buffer are used, so
  `STACK_TOP` is $FA as in CBM BASIC 2. `LINE_MAX = 80` is the longest typed line.
- `inline.s`: the sim has its own `INLIN`. It takes up to `LINE_MAX` characters and rings BEL when
  the line is full. BS ($08) and DEL ($7F) delete the last character; `@` and `_` are ordinary
  characters now. Other control characters are dropped. The upstream editing code depends on a
  zero-page buffer, so it cannot be reused.
- `print.s` (`L29B9`): the end of the line is handled as in CBM2 (`.if .def(CBM2) || .def(SIM)`),
  which returns the buffer pointer for a buffer outside zero page.
- Test: `tests/linein.bas` (80-character program line, INPUT and direct lines cut at 80, BS, STOP
  and CONT, strings in direct mode).

## Block IF / ELSE / END IF

msbasic has only the one-line IF. `CONFIG_BLOCK` (set in `defines_sim.s`) adds a block form:

```
IF c THEN
  ...
ELSE
  ...
END IF
```

- `IF c THEN` with nothing after THEN on the line starts a block. A false condition skips to the
  matching ELSE or END IF; ELSE, reached after the true part, skips to the matching END IF.
  Statements after ELSE on its line run, so `ELSE IF c THEN` chains blocks (each needs its own
  END IF) and `ELSE 100` jumps like `THEN 100`. Blocks push nothing on the stack, so GOTO in or
  out of a block is harmless.
- New file `block.s`: the ELSE statement and the forward scan. The scan reads the tokenized text:
  a line whose last token (spaces skipped) is THEN opens a block, END followed by IF closes one,
  text in quotes and after REM is skipped. It keeps `CURLIN` up to date line by line. If the
  program ends first: `?MISSING END IF ERROR`, in the extra error table of `handle_io.s` (so
  `CONFIG_BLOCK` needs `CONFIG_HANDLE_IO`). Zero page: `BLK_DEPTH`, `BLK_LAST`, `BLK_MODE` at
  $F4-$F6.
- `token.s`: new statement token ELSE after NEW (our own token values; programs are text, so
  token numbers need not match other BASICs). `TOKEN_END` and `TOKEN_IF` are now named.
- `flow2.s` (`IF`): after THEN, end of line means a block; a false block calls `BLK_FALSE`.
- `flow1.s` (`END`): END followed by IF is END IF and does nothing. A `jsr CHRGOT` restores the Z
  flag that the rest of END tests (end of statement), which the compare destroys. The label
  `EXEC_CHRGET` marks the `jmp CHRGET` that END IF branches to.
- No new token for END IF: the tokenizer already makes END + IF; `ENDIF` works too.
- Pitfall: keywords are found inside names, so a variable such as `ELSEX` no longer works.
- Size: 159 bytes in the sim build.
- Test: `tests/block.bas`.

## DO / LOOP / EXIT

`CONFIG_BLOCK` also adds a loop without a counter or condition; `IF c THEN EXIT` ends it:

```
DO
  ...
  IF c THEN EXIT
  ...
LOOP
```

- `DO` pushes a 5-byte frame like GOSUB (token, line number, text pointer) and checks the stack
  with `CHKMEM`. `LOOP` finds the frame with `GTFORPNT` (FOR frames above it are dropped, as
  RETURN does), pops it and falls into DO, which pushes it again, so LOOP and DO share code.
- `EXIT [DO]` (the DO is ignored) drops the frame and runs the block scan in a third mode
  (`BLK_MODE` = `TOKEN_LOOP`): DO opens a level unless it follows EXIT, LOOP closes one. The
  statements after the matching LOOP run. IF/THEN and END IF are not counted in this mode, so a
  block IF inside the loop does not disturb it.
- LOOP without a DO frame, or EXIT that finds no LOOP before the end of the program, gives
  `?MISSING DO/LOOP ERROR` (one message for both, to save bytes; for EXIT the line number is the
  last line scanned).
- No count (`DO n`): FOR does counted loops.
- Limits: RETURN inside a DO loop gives RETURN WITHOUT GOSUB; GOTO out of a DO loop leaves its
  frame on the stack (not allowed by rule, not checked); in `EXIT:DO` the DO is taken as part of
  `EXIT DO` by the scan. Keywords are found inside names, so names such as `DONE` no longer work.
- `token.s`: statement tokens DO, LOOP and EXIT after ELSE. The EXIT handler is `BLK_EXIT`,
  because `eval.s` already has a label `EXIT`.
- Size: about 145 bytes in the sim build.
- Test: `tests/do.bas`.

## Keyword table longer than 256 bytes, no LET

With DO, LOOP and EXIT the keyword table grew to 266 bytes. The tokenizer and LIST index it with
Y, so it can hold only 256, and every typed line hung.

- `CONFIG_KW16` (`program.s`): the tokenizer and LIST keep a pointer `KW_PTR` ($F7-$F8) to the
  current keyword and index into it with Y. `KW_INIT` points it at the first keyword, `KW_NEXT`
  skips to the next one. The table can now have any length (tokens still end at $FF). About 21
  bytes.
- `CONFIG_NO_LET` (`token.s`): the LET keyword is gone. Assignment without LET (`A=1`) works as
  before; `LET A=1` is now a syntax error. Saves 5 bytes and one token.

## Only the CBM and sim targets

The upstream targets for other machines (OSI, Apple, KIM-1, KIM BASIC, Microtan, AIM-65, SYM-1,
W65C816SXB) are not ours to support and only slowed every build and check.

- Removed their `defines_*.s`, `*_extra.s`, `*_iscntc.s`, `*_loadsave.s` and `.cfg` files, and
  their branches in `defines.s`, `extra.s`, `iscntc.s` and `program.s`. `loadsave.s` held only
  their includes and is gone too.
- Kept: `cbmbasic1` and `cbmbasic2` (byte-compared with the ROM dumps by `make verify`; BASIC 2
  also runs in xpet), and `sim`.
- The `.ifdef APPLE`, `.ifdef KIM` and similar code inside the shared sources stays. It assembles
  to nothing, and stripping it by hand risks breaking the verified builds.
- Size: no change. The sim build is still 9779 bytes; only the source tree is smaller.

## Faster number reading (FIN)

`tests/bench.py` showed that numeric literals were the most expensive part of a statement:
`A=12345` took about 5900 cycles against 1100 for `A=B`. FIN did a float multiply by 10 and a
float add for every digit, each time the line ran. VAL, INPUT and READ use the same routine.

- `CONFIG_FAST_FIN` (`float.s`, sim only): while FAC (the exponent byte) is 0, the digits go into
  FAC+1..FAC_LAST as an unsigned integer, multiplied by 10 with shifts and one add. `FIN_FLOAT`
  normalizes it into a float once, before the exponent is applied, or earlier if the next digit
  could overflow the integer (high byte $19 or more). From then on the old float code runs.
- Results are bit for bit the same as before: the integer is exact, and the float path also gives
  exact values for integers that fit the mantissa. Checked on 331 literals and their VAL forms.
- Cycles per statement: `A=1` 1525 to 1376, `A=12345` 5883 to 2220, `POKE 1000,1` 6019 to 3696.
- Size: about 120 bytes.
- Test: `tests/numbers.bas`.

## INSTR function

`INSTR([start,] a$, b$)` returns the 1-based position of `b$` in `a$`, searching from `start`
(default 1), or 0 when it is not found.

- `CONFIG_INSTR` (sim only). Code in `instr.s`, included from `extra.s`. The token goes after
  MID$ in `token.s` with no vector entry; `eval.s` catches it before the `UNARY` dispatch, because
  the optional first argument does not fit the `LEFT$`/`RIGHT$`/`MID$` calling form.
- `start` of 0, below 0 or above 255 gives ILLEGAL QUANTITY. A `start` past the end gives 0.
- An empty `b$` returns `start` when `start` <= LEN(a$)+1, else 0 (as in QuickBASIC).
- Both strings are released as temporaries (`b$` first, since it is the newer one), so FRE does
  not drop. The search reads the text after the release; nothing allocates in between.
- Size: 167 bytes.
- Test: `tests/instr.bas`.

## GOTO target cache

GOTO and GOSUB used to search the line list for the target on every jump. Now the result is
remembered, so a repeated jump costs the same however far away the target line is.

- `CONFIG_GOTO_CACHE` (sim only). Code in `gotocache.s`, included from `extra.s`. `GOTO` in
  `flow2.s` jumps to `GOTO_CACHED`; the old code stays as `GOTO_SLOW`. GOSUB, `IF ... THEN
  <line>`, `IF ... GOTO`, ON GOTO/GOSUB and `RUN <line>` all go through `GOTO`, so they all use
  the cache.
- Key: TXTPTR at entry, which points at the first digit of the line number. In a stored program
  that address always leads to the same target. Value: the TXTPTR that `GOTO_SLOW` leaves.
- Direct-mapped, 64 entries; the entry is the key's low byte AND 63. Four 64-byte tables
  (256 bytes) in the `IORAM` segment. An entry whose key high byte is 0 is empty.
- Direct-mode lines are not cached, because the input buffer is reused.
- `CLEARC` (in `program.s`) empties the cache. It runs on NEW, RUN, CLR and after every program
  line is typed, so the cache never points at old text. A future LOAD must also reach `CLEARC`
  (the CBM LOAD does, through `SETPTRS`). A POKE into the program text is not noticed.
- On a miss, `CHRGOT` is called again before `GOTO_SLOW`, because `LINGET` needs the carry flag
  of the first digit and the cache lookup clobbers it.
- Speed (`tests/bench.py`): GOSUB to the next line 1382 to 732 cycles, GOSUB 100 lines on 6900 to
  751 cycles.
- Size: 91 bytes of code plus the 256-byte tables.
- Test: `tests/gotocache.bas` (changed and deleted target lines, inserted lines, ON GOTO/GOSUB,
  IF GOTO, RUN <line>, direct mode, and two GOTOs that share a cache entry).

## Simple variable cache

PTRGET used to search the simple variable table from the start on every use, so a variable made
late cost more than one made early. Now the address of each variable's entry is remembered.

- `CONFIG_VAR_CACHE` (sim only). Code in `varcache.s`, included from `extra.s`. In `var.s`,
  PTRGET calls `VC_FIND` before the search and jumps straight to `SET_VARPNT_AND_YA` on a hit.
  On a miss the old search runs; when it finds the variable (`VC_FOUND`) or makes a new one,
  `VC_STORE` remembers it.
- Key: the two name bytes in VARNAM. Value: the address of the 7-byte entry (LOWTR). A simple
  variable never moves once made: a new one is added at the end of the simple variables and only
  the arrays move up. VARTAB only changes through `SETPTRS`, which runs `CLEARC`, and `CLEARC`
  empties the cache (NEW, RUN, CLR, every program line entry).
- Arrays are not cached; they move whenever a simple variable is made.
- When an undefined variable is read in an expression, BASIC returns zero without making the
  variable. Nothing is cached then.
- Direct-mapped, 64 entries. The index is `(VARNAM+1)*2 + VARNAM`, with bit 5 flipped for
  strings and integers and bit 4 also flipped for integers, AND 63. Single-letter floats get
  entries 1 to 26 and strings and integers mostly land elsewhere. Four 64-byte tables plus
  `VC_IDX` (257 bytes) in the `IORAM` segment. An entry whose first name byte is 0 is empty.
- Speed (`tests/bench.py`): `Z=Z+1` with Z last of 25 variables 4200 to 2744 cycles, `A$=B$`
  1763 to 1363. The first one or two variables in the table get about 25 cycles slower per use,
  because the hash costs about as much as one step of the old search.
- Size: 101 bytes of code plus the 257-byte tables.
- Test: `tests/varcache.bas` (names that share an entry, strings and integers, a new variable made
  after DIM, DEF FN, CLEAR, program edits, NEW).

## HEX$ and BIN$

- `CONFIG_HEXBIN` (sim only). Code in `hexbin.s`, included from `extra.s`. `HEX$(n)` and
  `BIN$(n)` return n in hex or binary, for -65535 <= n <= 65535 (anything else is ILLEGAL
  QUANTITY). A negative n is taken mod 65536, as two's complement, so `HEX$(-1)` is "FFFF" and
  `HEX$(-32768)` is "8000"; this suits `%` variables, which are signed 16-bit. The routine uses
  `QINT` directly instead of `GETADR`, which rejects negative values. A result below 256 gives 2
  hex or 8 binary digits, otherwise 4 or 16, with leading zeros.
- The keywords sit in the function table after `CHR$` and before `LEFT$`, so UNARY parses their
  one argument; this moves the tokens of LEFT$, RIGHT$, MID$, INSTR and GO up by 2. Like `CHR$`,
  the routine drops UNARY's return so its numeric type check is skipped, and it builds the
  string in place with `STRSPA` and `PUTNEW`. The value and digit sizes are kept on the stack
  across `STRSPA`, which can collect garbage.
- Size: 106 bytes.
- Test: `tests/hexbin.bas`.

## RPT$

- `CONFIG_RPT` (sim only). Code in `rpt.s`, included from `extra.s`. `RPT$(a$, n)` returns a$
  repeated n times; `RPT$(c, n)` returns `CHR$(c)` repeated n times. n is 0 to 255, c is 0 to 255
  (else ILLEGAL QUANTITY), and a result longer than 255 characters gives STRING TOO LONG.
- The first argument may be a string or a number, which UNARY cannot parse, so the keyword sits
  after `INSTR` with no table address and `FRM_ELEMENT` sends its token to `RPTSTR` directly, as
  it does for INSTR. This moves the GO token up by 1. A numeric first argument is first turned
  into a one-character temporary string, so both forms share the copy loop. The descriptor
  address and n are kept across `STRSPA` (which can collect garbage), then `FRETMP` reads the
  source text and `MOVSTR1` copies it n times.
- Size: 101 bytes, plus 7 in `FRM_ELEMENT` and the 4-byte keyword.
- Test: `tests/rpt.bas` (both forms, empty results, the 255 limit, errors, and a loop that forces
  garbage collection).

## MOD

- `CONFIG_MOD` (sim only). Code in `mod.s`, included from `extra.s`. `a MOD b` works as in
  QBasic: both operands are rounded to the nearest integer (halves away from zero, so
  `2.5 MOD 2` is 1), the result has the sign of `a` (`-7 MOD 3` is -1), and it has the same
  precedence as `*` and `/`. An operand of 2^31 or more in size gives OVERFLOW, and a right
  operand that rounds to 0 gives DIVISION BY ZERO.
- The keyword sits after `OR`, inside the binary operator range `TOKEN_PLUS`..`TOKEN_GREATER`,
  with a `MATHTBL` entry after `OR` (precedence $7B). This moves the tokens of `>`, `=`, `<` and
  every function up by 1. The hard-coded `MATHTBL` offsets became symbols so they follow the
  table: `adc #$07` in `FRMEVL` is `TOKEN_GREATER-TOKEN_PLUS`, the `ldy #$15/$18/$1B` loads in
  `eval.s` are `MT_NEGOP`, `MT_EQUOP` and `MT_RELOPS` (defined in `token.s`), and
  `MATHTBL+28+1` in the tokenizer is `MATHTBL+MT_RELOPS+2`. The CBM builds are unchanged.
- The remainder comes from a 32-bit shift-and-subtract division on the integer magnitudes
  (`QINT` after adding 0.5), so it is exact for every allowed operand, unlike `a-b*INT(a/b)`
  in floating point.
- Size: 154 bytes, plus the 3-byte table entry and the 3-byte keyword.
- Test: `tests/mod.bas` (signs, rounding, precedence, the 2^31 limit, errors).

## Unknown variable check compares the whole caller address

- `CONFIG_SAFE_NAMENOTFOUND` (upstream option, now on in the sim build). When `PTRGET` does
  not find a simple variable, `NAMENOTFOUND` decides whether the caller only reads it (an
  expression, which gets the constant 0 at `C_ZERO` and creates nothing) or will store into it
  (which needs a new variable). It decided by comparing only the low byte of the caller's
  return address with `FRM_VARIABLE_CALL`. When code moves, another `PTRGET` call can share
  that low byte. The hex literal work moved the call in `PROCESS_INPUT_ITEM` onto it, so
  `INPUT A` and `READ A` with a new numeric variable stored the value over `C_ZERO`, which is
  `CON_HALF+2` in the ROM. That broke number output (`FOUT` rounds with `CON_HALF`) until the
  next start. The option also compares the high byte. Cost: 8 bytes.
- No dedicated test: the failure needs a particular code layout. `tests/data.bas` and
  `tests/files.bas` showed it.

## Hex and binary literals

- `CONFIG_RADIX_LIT` (sim only, needs `CONFIG_FAST_FIN`). Code in `radixlit.s`, included from
  `extra.s`. `$FF` is a hex number and `%1010` a binary number. Hex digits may be lowercase.
  Values are unsigned and may use up to 32 bits (`$FFFFFFFF` is 4294967295); more gives
  OVERFLOW. Leading zeros are allowed. A prefix with no digits gives 0, as `.` does.
- `FIN` calls `LIT_FIN` when the first character is not a digit, so the literals work in
  program text, `VAL`, `INPUT` and `DATA`. `LIT_FIN` shifts the digits into FAC+1..4 (cleared
  by `FIN`) and floats the result with `FIN_FLOAT`. A sign is not read before the prefix, so
  `VAL("-$10")` is 0; in an expression `-$10` is -16 through the unary minus. `FIN` skips
  spaces between digits, as it does for decimal numbers.
- `FRM_ELEMENT` sends `$` and `%` to `FIN`, like a digit or `.`.
- Tokenizer: without help, `$DEF` would become `$`, the `DEF` token. `PARSE_INPUT_LINE` calls
  `LIT_TOKEN` for each `$`. After a letter or digit the `$` is a type suffix (`A$`, `B1$`) and
  tokenizing goes on as before. Otherwise the `$` and the hex digits after it are stored
  untokenized and in uppercase. A literal must be followed by a space or a non-hex character
  before a keyword: `$FFAND1` reads `$FFA` then `ND1`. `%` needs no help, since 0 and 1 never
  start a keyword.
- Size: 127 bytes, plus 9 in the tokenizer, 3 in `FIN` and 8 in `FRM_ELEMENT`.
- Test: `tests/radixlit.bas` (values, limits, lowercase, `$DEF`, `VAL`, `DATA`, `INPUT`, the
  `$` suffix on string variables, `LIST`).

## PI

- `CONFIG_PI` (sim only). `PI` is a keyword that gives 3.14159265 in expressions, as the
  π character (byte $FF) does in the CBM builds. It is a token, not a variable, so `PI=5` is a
  SYNTAX ERROR, and like every keyword it is found inside longer names: `SPIN` reads as
  `S PI N`.
- The keyword sits at the end of the function names (after `RPT$`), so no existing token
  moves except `GO`. `FRM_ELEMENT` checks for `TOKEN_PI` before `ISLETC` and branches to
  `PI_CONST`, placed just before `FRM_ELEMENT`, which loads `CON_PI` (same bytes as the CBM
  constant). The check goes before the letter test because the `bcs FRM_VARIABLE` after it has
  no room left in its branch range. The CBM builds are unchanged.
- Size: 15 bytes for `PI_CONST` and the constant, 4 for the check, 3 for the keyword.
- Test: `tests/pi.bas` (value, trig, a program and `LIST`, `PI=5`, `PI(1)`).

## XOR, SHL and SHR

- `CONFIG_BITFN` (sim only). Code in `bitfn.s`, included from `extra.s`. `XOR(a, b)` is the
  bitwise exclusive or, `SHL(a, n)` and `SHR(a, n)` shift a left or right by n bits. They are
  functions rather than operators, and work on 16 bits like `AND` and `OR`.
- a and b may be -65535 to 65535; a negative value is taken mod 65536, as `HEX$` does, so
  `$FFFF` and -1 are the same bits. n is 0 to 255 (`GETBYT`); 16 or more gives 0. `SHR` is a
  logical shift (zeros come in at the top). The result is signed, -32768 to 32767, like `AND`
  and `OR`, so it fits a `%` variable and can be fed back into `AND` and `OR`:
  `SHL(1, 15)` is -32768 and `SHR(-1, 1)` is 32767. Out of range values are ILLEGAL QUANTITY.
- The three keywords follow `PI` at the end of the function names, so only `GO` moves.
  `FRM_ELEMENT` checks the token range before `ISLETC` (the same branch range limit as `PI`)
  and jumps to `BITFN`, which parses both arguments itself. The first argument and the token
  are kept on the stack while the second is evaluated. Like every keyword, `XOR` is found in
  names: `IFXORY` now reads as `IF XOR Y`, so write `IF X OR Y`.
- Size: 108 bytes in `bitfn.s`, 11 in `FRM_ELEMENT`, 9 for the keywords.
- Test: `tests/bitfn.bas` (values, sign and wrap, shift limits, `%` variable, a program and
  `LIST`, errors).

## DEEK and DOKE

- `CONFIG_DEEK` (sim only). Code in `deek.s`, included from `extra.s`. `DEEK(addr)` reads the
  16-bit word at addr (low byte first) and returns it unsigned, 0 to 65535, like `PEEK` returns
  0 to 255. `DOKE addr, n` stores n as a word at addr. addr is 0 to 65535 (`GETADR`, as for
  `PEEK` and `POKE`). n may be -65535 to 65535; a negative value is taken mod 65536, as `HEX$`
  and `XOR` do, so `DOKE a, -1` stores $FFFF. Out of range values are ILLEGAL QUANTITY.
- `DOKE` follows `POKE` in the statement names and `DEEK` follows `PEEK` in the function
  names, so the tokens after each move up by one (sim only; the CBM builds are unchanged).
  `DEEK` is a normal one-argument function called through `UNFNC`; it floats the word with
  `FLOAT2` (positive) instead of `GIVAYF`, which would make values over 32767 negative.
- `DOKE`, like `POKE`, keeps the address in `LINNUM` while it evaluates the value, so anything
  in that expression that changes `LINNUM` makes it write to the wrong address. Two such cases
  were found and fixed:
  - `PEEK` uses `LINNUM` for its address, so `POKE 1001,PEEK(1000)` wrote to 1000. The sim
    build now sets `CONFIG_PEEK_SAVE_LINNUM` (already used by BASIC 2), and `DEEK` saves and
    restores `LINNUM` the same way.
  - `HEX$` and `BIN$` kept the value in `LINNUM`, so `POKE a,LEN(HEX$(n))` went wrong. They now
    keep it in `FAC_LAST-1` and `FAC_LAST`, where `QINT` leaves it (pulled back from the
    stack after `STRSPA`); the new string's descriptor uses only `FAC` to `FAC+2`. This also
    saves 8 bytes.
- Size: 68 bytes in `deek.s`, 12 for the keywords, 12 for the `PEEK` save, 8 fewer in
  `hexbin.s`.
- Test: `tests/deek.bas` (byte order, sign and wrap, `DOKE a,DEEK(b)`, `POKE a,PEEK(b)`,
  `POKE a,LEN(HEX$(n))`, a program and `LIST`, errors).

## UCASE$ and LCASE$

- `CONFIG_CASE` (sim only). Code in `casestr.s`, included from `extra.s`. `UCASE$(a$)` returns a
  copy of a$ with the ASCII letters a-z turned into A-Z; `LCASE$(a$)` turns A-Z into a-z. Other
  characters, including `@[`{`, are copied unchanged.
- Both names follow `BIN$` in the function names, before `LEFT$`, so they are normal
  one-argument functions called through `UNFNC`; the tokens from `LEFT$` on move up by two
  (sim only; the CBM builds are unchanged). Like `LEFT$`, the code gets the new string space
  first (`STRINI`, which may collect garbage; `DSCPTR` points to the descriptor, which garbage
  collection updates) and only then frees the argument (`FRETMP`). It copies and converts in one
  loop into the new string and drops `UNARY`'s return, as `CHR$` does.
- Size: 54 bytes in `casestr.s`, 16 for the keywords.
- Test: `tests/case.bas` (both directions, letters next to the ranges, empty string, nested
  calls, a program that forces garbage collection, `LIST`, errors).

## TEXTAT

- `CONFIG_TEXTAT` (sim only). Code in `textat.s`, included from `extra.s`. Statement
  `TEXTAT x,y,a$[,c]` prints a$ at column x, row y (0,0 is top left) in color c, and leaves the
  cursor and `POS()` where they were. `TEXTAT x,y,code[,c]` prints `CHR$(code)`, so one keyword
  also covers the planned `CHARAT` (saves its table entry and a second parser).
- The name follows `EXIT` in the statement names, so the tokens from `TAB(` on move up by one
  (sim only; the CBM builds are unchanged).
- A number is turned into a one-character string by calling `CHRSTR` through a 3-byte
  `jsr CHRSTR` stub: `CHRSTR` drops one return address (it expects `UNARY`'s), so it returns to
  the caller of the stub. The string descriptor waits on the stack while the color is parsed, as
  in `RPT$`.
- The sim has no screen, so the code sends ANSI codes to the current output, written byte by byte
  through `MONCOUT` (not `OUTDO`, so `POSX` and the line width are not touched): `ESC 7` (save
  cursor and color), `ESC[38;5;CCCm` if a color is given (xterm 256-color index), `ESC[YYY;XXXH`
  (1-based, three digits each), the text, `ESC 8` (restore). All parsing is done before anything
  that moves the cursor, so an error leaves at most an unmatched `ESC 7`, which shows nothing.
  x or y = 255 sends 000, which terminals take as 1. Under `CMD` the codes go to the file. The
  new kernal will replace the ANSI part with its own screen calls.
- Size: 173 bytes in `textat.s`, 9 for the keyword.
- Test: `tests/textat.bas` (string, code, color, empty string, `POS()` kept, expressions, inside
  a loop, `LIST`, errors).

## Shared CHR$ stub (RPT$, TEXTAT)

- `RPT$(code, n)` built its one-character string with its own copy of the `CHR$` code (18
  bytes). It now calls `CHRSTUB` (`jsr CHRSTR`, in `rpt.s`), the same trick `TEXTAT` used.
  `TEXTAT` uses that stub too and keeps its own copy only when `CONFIG_RPT` is off.
- Saves 15 bytes in the sim image. Tests unchanged.

## CONTINUE

- Part of `CONFIG_BLOCK`, code in `block.s`. `CONTINUE` starts the next pass of the innermost
  loop. It calls `GTFORPNT` with `FORPNT+1` = 0, which stops at the first FOR frame or at the
  first other frame. A DO frame on top: the rest is `LOOP`'s code. A FOR frame on top: the block
  scanner runs in a new mode, `TOKEN_NEXT`, finds the matching `NEXT` and runs it there, so the
  loop either goes on or ends after that `NEXT`. No loop frame: `?MISSING DO/LOOP`, which is
  also the error for a FOR loop that has no `NEXT` after the `CONTINUE`.
- The scanner's loop mode is now generic: `BLK_MODE` holds the closing token and the token just
  before it opens a loop (`DO`/`LOOP` and `FOR`/`NEXT` are next to each other in the table).
  A `NEXT` that closes two loops (`NEXT J,I`) counts as one.
- The name sits before `CONT` in the table: the tokenizer takes the first name that matches, so
  after `CONT` it would read as `CONT` `INUE`. The tokens from `CONT` on move up by one (sim
  only). `NEXT` gets the label `TOKEN_NEXT` (no bytes).
- Size: 38 bytes (10 table, 28 code).
- Test: `tests/continue.bas` (FOR and DO, nested loops of both kinds, inside a block IF, a REM
  that holds NEXT, in a one-line FOR, `CONT` still listed as `CONT`, errors).

## block.s: 8 bytes saved, ?MISSING NEXT

- `CONTINUE`, `EXIT`, `LOOP` and `DO` now come before the block scanner. `LOOP` reaches the
  scanner's FOR entry (`BLK_CONTF`) with a branch, so the 3-byte `jmp` hop is gone. `EXIT`
  jumps back into the scanner with `bcc` instead of `jmp` (the carry is always clear there,
  since the DO frame ends at $1FF or below): 1 byte.
- When the scan finds its token, it no longer reads `BLK_MODE` and calls `CHRGET`. The token is
  still in A: for `NEXT` TXTPTR stays on it, so `L288D` runs `NEXT`; for the others `iny`
  moves past the token and `L288D`'s `CHRGOT` skips the spaces: 4 bytes.
- The error exit (`BLK_NODO`, `BLK_ERR`) sits in the middle of the scan, so both the scan and
  `LOOP` reach it with branches. It has an unnamed label, because a named label there would end
  the scope of the scan's `@` labels; `BLK_NODO = :-` names it at the end of the file.
- A FOR loop with no `NEXT` after `CONTINUE` now gives `?MISSING NEXT ERROR` instead of
  `?MISSING DO/LOOP` (new message in the extra error table of `handle_io.s`, 12 bytes, plus 4
  bytes of code). The variable after `NEXT` is not checked by the scan.
- Net: 8 bytes saved, 16 spent, image 8 bytes larger (11818). `tests/continue.out` updated.

## block.s: one ?UNMATCHED BLOCK error (42 bytes saved)

- `?MISSING END IF`, `?MISSING DO/LOOP` and `?MISSING NEXT` are replaced by one message,
  `?UNMATCHED BLOCK ERROR`, in the extra error table of `handle_io.s`. It covers a block IF
  without END IF, DO without LOOP, LOOP, EXIT or CONTINUE without a loop, and CONTINUE in a FOR
  loop without NEXT. Text: 41 bytes down to 15.
- The end-of-program path of the scan no longer picks a message from `BLK_MODE`; it branches
  straight to the error exit (`BLK_NODO`). The 16-byte `@missing` code and `BLK_ERR` are gone.
- Net: 42 bytes saved, image 11776 bytes. `tests/block.out`, `tests/do.out` and
  `tests/continue.out` updated.

## No SPC( and one ?FILE MODE error (36 bytes saved)

- `SPC(` is removed from the sim build (`CONFIG_NO_SPC` in `defines_sim.s`). `RPT$(32,n)` prints
  the same spaces. `token.s` drops the keyword (4 bytes; the tokens after it move down by one).
  In `print.s`, PRINT no longer tests for `TOKEN_SPC` (5 bytes), and the shared TAB(/SPC( code
  at `L29F5` no longer saves the token test in carry with `php`/`plp`/`bcc` (4 bytes): only TAB(
  is left, and the carry is set by `cmp #')'`. 13 bytes. The CBM builds keep SPC(.
- `?NOT INPUT FILE` and `?NOT OUTPUT FILE` in `handle_io.s` are replaced by one message,
  `?FILE MODE ERROR`, raised from `HIO_BADMODE` (`HIO_MODE` is already the mode table). Text:
  29 bytes down to 9, plus 3 bytes for the second entry point. 23 bytes.
- Net: 36 bytes saved, image 11740 bytes. `tests/files.out` updated.

## Shared ?FILE prefix, ?FILE LIMIT (10 bytes saved)

- The four file messages in `handle_io.s` all began with `FILE `. The table now holds them
  without it (`OPEN`, `NOT OPEN`, `NOT FOUND`, `MODE`) plus one prefix entry `?FILE `.
  `HIO_ERROR` prints the prefix first when the message offset is below `HIO_ERR_NOFILE`, then
  the message, through the new subroutine `HIO_PUTS` (indexed by Y; OUTDO keeps X and Y).
  The `?` moved into the table (`?FILE `, `?UNMATCHED BLOCK`), so `jsr OUTQUES` is gone.
- `?TOO MANY FILES ERROR` becomes `?FILE LIMIT ERROR` and shares the prefix.
- Text: 74 bytes down to 52 (22 saved). Code: 12 bytes more (range test, two calls, `rts`,
  minus `jsr OUTQUES`).
- Net: 10 bytes saved, image 11730 bytes. `tests/files.out` updated.

## POSX fix, POS(1) gives the line (10 bytes)

- Bug: after a new line, `POSX` stayed at 13. `CRDO` stores the CR code in `POSX`, and with
  `CONFIG_2` the reset in `PRINTNULLS` is left out (AppleSoft clears it elsewhere). So
  `POS(0)`, `TAB(` and the comma zones were all off by 13 after the first line.
- New flag `CONFIG_POS_LINE` (sim build). `PRINTNULLS`, which runs after every new line (also
  after a CR inside a printed string), clears `POSX` and counts the line in `POSY` ($F9).
  `CRDO` no longer stores CR in `POSX` (2 bytes saved; `PRINTNULLS` clears it anyway).
- `POS(n)`: `POS(0)` is the column as before; any other argument gives `POSY`. `POS` tests the
  FAC exponent, so the argument needs no conversion (6 bytes). In the sim, `POSY` counts the
  lines printed since the start (modulo 256); the new kernal port must read the row from its
  screen call. `TEXTAT` does not move the cursor, so it does not change either value.
- Net: 10 bytes more, image 11740 bytes. New test `tests/pos`. `arith`, `arrays`, `files`,
  `strings` and `textat` expected outputs updated: comma zones and `POS(0)` are now right.

## Labels (126 bytes)

- New flag `CONFIG_LABELS` (sim build), code in `labels.s`, included from `extra.s`. A label is
  a name and a colon at the start of a line: `100 MAIN:` or `100 MAIN: PRINT X`. `GOTO name`,
  `GOSUB name`, `RUN name`, `RESTORE name` and `ON x GOTO/GOSUB a,200,b` take labels.
- Names: a letter, then letters, digits and keywords. The tokenizer crunches keywords inside
  names (`MYPRINT` is stored as `MY` and the PRINT token), and the search compares the stored
  bytes, so such names still match. All characters count. A name must not start with a
  keyword: `TOTAL` is stored as TO+`TAL`, and `PRINTIT:` is the statement `PRINT IT:`.
- `LABEL_FIND` walks the program from `TXTTAB` and compares the name at `TXTPTR` with the start
  of each line, from the colon backwards. `INDEX` is set to `TXTPTR`-4 so one Y index reaches
  both texts. It returns the line in `LOWTR` or raises ?UNDEF'D STATEMENT.
- `GOTO_SLOW` (`flow2.s`): when the target does not start with a digit, it calls `LABEL_FIND`
  and joins the line-number path at the new label `GOTO_FOUND`. The GOTO cache works on labels
  unchanged, because its key is the address of the target text.
- Executing a label: `LET1` (`flow1.s`) now jumps to `LABEL_SKIP`. A statement that starts with
  a letter is a label when it reaches `:` before an `=` token or any character below `0`; then
  TXTPTR moves to the colon. Otherwise it goes on to `LET`. Every assignment pays this short
  look-ahead.
- `ON`: `LINGET` in the list loop is replaced by `LABEL_ONSKIP`, which skips any target up to
  `,` or the end of the statement.
- `RESTORE`: the keyword entry points to `RESTORE_STMT` (`token.s`). Without an argument it is
  the old `RESTORE` (which `CLEARC` still calls); with a name it sets `DATPTR` to the byte in
  front of the label line and skips the name.
- Placement: `LABEL_SKIP` sits just before `LET` in `misc1.s`, so an assignment falls through
  into `LET` (no `jmp LET`). `RESTORE_STMT` sits just before `RESTORE` in `flow1.s`: a short
  `beq RESTORE` replaces `bne`+`jmp`, and with a name it loads `LOWTR` into A/Y and joins the
  subtract-one code of `RESTORE`, whose start now loads `TXTTAB` the same way (under
  `CONFIG_LABELS`; the CBM builds keep the old `RESTORE`). It calls `DATA` first to skip the
  name, because `DATA` leaves `LOWTR` alone. These two moves saved 12 bytes over the first
  version, which kept both routines in `labels.s`.
- Not done: `IF c THEN name` runs the label as a statement and does nothing; write
  `THEN GOTO name`.
- Net: 126 bytes (CODE 43, EXTRA 83), image 11866 bytes. New test `tests/labels`.

## No keyword search inside a name (21 bytes)

The tokenizer crunched keywords wherever they appeared, also inside names: `BORDER` became
`B`,`OR`,`DER` and `SCORE` became `SC`,`OR`,`E`, so `POKE BORDER,1` or `SCORE=5` broke.
`CONFIG_NAME_NOCRUNCH` (sim only) fixes this in `PARSE_INPUT_LINE` (`program.s`):

- A letter whose last stored byte is also a letter is inside a name. It is stored as it is,
  without searching the keyword table. Tokens, digits and spaces do not count as letters, so
  `PRINTCHR$(65)` and `FORI=1TO3` still tokenize; `IFA=BTHEN` now needs spaces.
- The check reads the last stored byte with `INPUTBUFFER-5,y`, like `LIT_TOKEN` does. For the
  first character that is `INPUTBUFFER-1`, which can hold the high byte of the last line number
  (line 20000 gives "N"). `PARSE_INPUT_LINE` now stores 4 there first. This also fixes the same
  case in `LIT_TOKEN`.
- Still a limit: a name must not start with a keyword (`TOTAL` is `TO`,`TAL`), because the first
  letter of a name has no letter in front of it.
- Labels keep working: `LABEL_FIND` compares raw bytes, and both the label line and the name
  after `GOTO` are now stored as plain letters.
- Net: 21 bytes (CODE), image 11887 bytes. New test `tests/names`.

## Names may start with a keyword (25 bytes)

With the change above, a name still could not start with a keyword: `TOTAL` became `TO`,`TAL`,
and `ONE`, `ENDX` and `FORMAT` broke the same way. `CONFIG_NAME_NOCRUNCH` now also checks the end
of a keyword match in `PARSE_INPUT_LINE` (`program.s`):

- When the keyword ends in a letter and a letter follows it, the match is the start of a name.
  The search goes on with the next keyword (`GOTOX` tries `GOTO`, then `GO`), and when none fits,
  the letter is stored as it is. `AND #$DF` makes the next character uppercase for `ISLETC`;
  the last keyword character is read from the table with `AND #$5F`, which also clears bit 7.
- The check sits behind the string copy loop, outside the tokenizer loop, because the loop's
  branches were at the edge of their range. In the loop, `ORA EOLPNTR` became a `BEQ` of the
  same size; the token is built in the new code.
- Run-together keywords now need a space: `FOR I` (not `FORI`), `PRINT X`, `FN F(`, `END IF`
  (not `ENDIF`), `GOTO AGAIN`. A digit or other sign after a keyword is fine: `GOTO10`, `1TO3`.
  `tests/block` now writes `END IF`.
- Labels may now start with a keyword (`TOTAL:`).
- Net: 25 bytes (CODE), image 11912 bytes. `tests/names` covers `TOTAL`, `ONE`, `ENDX`,
  `FORMAT` and `NEXTI`.

## PAUSE statement (54 bytes)

`PAUSE [n]` waits n+1 jiffies (1/60 s), like `SLEEP` on the X16: `PAUSE` and `PAUSE 0` wait for
the next jiffy, `PAUSE 60` about a second. n is 0 to 65535 (`GETADR`), so a negative or larger
value gives ?ILLEGAL QUANTITY.

- New file `pause.s` (`CONFIG_PAUSE`). The keyword sits after `TEXTAT` in the statement part of
  the table, so `TAB(` and every token after it move up by one.
- The count goes in `LINNUM`. `PHP`/`PLP` keep the Z flag from `CHRGOT` across the zeroing, so
  no argument means 0 without a second `CHRGOT` (saves 1 byte).
- Waiting for one jiffy is a new target primitive, `K_JIFFY`, which may change X and Y. The sim
  has no clock in sim65 2.19, so `K_JIFFY` in `sim_extra.s` is a busy loop of about 16700 cycles
  (one jiffy at 1 MHz); real time depends on how fast sim65 runs. The new kernal port must wait
  for the next VSYNC there.
- `ISCNTC` runs every jiffy, so the break key can stop a long pause on a target that has one.
- Net: 54 bytes (5 keyword, 2 dispatch, 47 EXTRA), image 11966 bytes. New test `tests/pause`.

## PAUSE needs its argument (10 bytes saved)

`PAUSE` without a number now gives ?SYNTAX ERROR (from `FRMNUM`) instead of waiting one jiffy;
write `PAUSE 0` for that. This drops the `PHP`/`PLP` test and the zeroing of `LINNUM` (10
bytes). PAUSE now costs 44 bytes, image 11956 bytes. The test types `PAUSE` to check the error.

## VPEEK and VPOKE for video memory (80 bytes)

`VPEEK(bank, addr)` reads and `VPOKE bank, addr, n` writes a byte of video memory, with the same
syntax as on the X16. bank and n are 0 to 255 (`GETBYT`), addr is 0 to 65535 (`GETADR`); the
target decides what a bank means.

- New file `vera.s` (`CONFIG_VERA`). `VPOKE` is a statement keyword after `PAUSE`, `VPEEK` a
  function keyword after `SHR`, so tokens shift again (95 tokens, $80-$DE).
- Video memory is reached through two new target primitives: `K_VPEEK` (A = bank, `LINNUM` =
  address, returns the byte in A) and `K_VPOKE` (the same, with the byte in X). The sim has no
  video chip, so in `sim_extra.s` `K_VPEEK` returns 0 and `K_VPOKE` does nothing. The new kernal
  port must supply real ones.
- `VPEEK` takes two arguments, so `FRM_ELEMENT` dispatches it by token, like `XOR`. The test sits
  before `ISLETC`, because between `ISLETC` and `FRM_VARIABLE` a `BCS` is already near the end of
  its range.
- `VPEEK` keeps `LINNUM`, like `PEEK` and `DEEK`, so `VPOKE B,A,VPEEK(B,C)` works. `VPOKE` ends in
  `GTNUM` (address and byte), the same parser `POKE` uses.
- Net: 80 bytes (10 keywords, 2 dispatch, 7 in `FRM_ELEMENT`, 61 EXTRA with the 3-byte stubs),
  image 12036 bytes. New test `tests/vera`.

## CLS, LOCATE and COLOR (79 bytes, plus 10 in TEXTAT)

`CLS` clears the screen, `LOCATE x, y` moves the cursor to column x, row y (0,0 is top left), and
`COLOR fg[, bg]` sets the text colors (0 to 255 each) until the next `COLOR`.

- All three are in `textat.s` (`CONFIG_SCREEN`, needs `CONFIG_TEXTAT`) and send ANSI codes to the
  current output, like `TEXTAT`: `ESC[H ESC[2J`, `ESC[row;colH`, `ESC[38;5;fgm` and
  `ESC[48;5;bgm`. The new kernal's console is planned as a POSIX-style terminal that understands
  these codes, so there are no target primitives; the sim code is the real code.
- `CLS` and `LOCATE` set `POSX` and `POSY`, so `POS(0)`, `POS(1)`, `TAB(` and comma output stay
  right. `TEXTAT` leaves them alone, because it puts the cursor back. A terminal cannot report
  the cursor row cheaply (`ESC[6n` needs a reply to parse), so BASIC keeps counting it.
- `TEXTAT` gave up its inline code for the color and the position: the new subroutines `TA_SGR`
  (prefix, decimal, `m`) and `TA_GOTO` (`ESC[row;colH`) serve `TEXTAT`, `COLOR` and `LOCATE`.
  `COLOR` falls into `TA_SGR` for the background, `LOCATE` falls into `TA_GOTO`. That makes
  `TEXTAT` 10 bytes larger on its own (189 bytes).
- `LOCATE 1,` sets `POSX` before the row fails with an error. The error message starts a new line,
  which clears `POSX` again; only `POSY` may be one off, which is harmless.
- `CLS`, `LOCATE` and `COLOR` are statement keywords after `VPOKE`, so tokens shift again
  (98 tokens, $80-$E1). New test `tests/screen`. Net: 89 bytes (14 keywords, 6 dispatch, 69
  EXTRA), image 12125 bytes.

## SCREEN mode, a stub in the sim (14 bytes)

`SCREEN mode` sets the screen mode, mode 0 to 255 (`GETBYT`). The target decides what each mode
means; the sim has no video modes, so it is a stub there.

- In `vera.s` (`CONFIG_VERA`), because it belongs to the video hardware like `VPEEK` and
  `VPOKE`. Statement keyword after `VPOKE`, so tokens shift again (99 tokens, $80-$E2).
- New target primitive `K_SCREEN` (X = mode). `SCREEN` passes the mode in X as `GETBYT` leaves
  it, so the code is only `jsr GETBYT` and `jmp K_SCREEN`. The sim stub shares the `rts` of
  `K_VPOKE` and costs nothing. The new kernal port must supply a real one.
- Net: 14 bytes (6 keyword, 2 dispatch, 6 EXTRA), image 12139 bytes. Tests added to
  `tests/vera`.

## Startup banner: UX6502BASIC V0.1 (saves 15 bytes)

The sim build printed Microsoft's `COPYRIGHT 1977 BY MICROSOFT CO.` under the bytes-free line.
It now prints `UX6502BASIC V0.1`, the name and version of this project.

- `QT_BASIC` in `init.s` gets an `.elseif .def(SIM)` branch with the new text. The other targets
  keep their strings, so `make verify` still passes.
- The string is 15 bytes shorter: image 12124 bytes. Every `tests/*.out` file starts with the
  banner, so all were updated.

## Sim: dead startup strings left out (saves 66 bytes)

The sim skips the MEMORY SIZE? and TERMINAL WIDTH? prompts, but `init.s` still assembled their
strings and the "WRITTEN BY" message that answering `A` to MEMORY SIZE? prints.

- `QT_WRITTEN_BY` (the message), `QT_MEMORY_SIZE` and `QT_TERMINAL_WIDTH` sit in one
  `.ifndef CONFIG_CBM_ALL` block; it becomes `.if !(.def(CONFIG_CBM_ALL) || .def(SIM))`.
- The code at `PR_WRITTEN_BY` that prints the message gets the same condition. Only the prompt
  code (not built for the sim) and the SYM1 header jump there. The label stays and falls into
  `COLD_START`.
- Net: 66 bytes (all INIT), image 12058 bytes. Output does not change.

## Sim: banner and free count on one line, fewer blank lines at startup (saves 2 bytes)

The start-up output was a blank line, the free count, two blank lines, the banner, a blank line
and OK, because the Microsoft code prints the count before the banner. The sim now prints:

```
UX6502BASIC V0.1 - 48127 BYTES FREE

OK
```

- `init.s`: the `jsr CRDO` before the memory scan is left out for the sim
  (`.ifndef SIM`).
- The sim prints `QT_BASIC` with STROUT where the other targets call CRDO, as CBM2 does
  (`.if .def(CBM2) || .def(SIM)`).
- `QT_BASIC` for the sim is `"UX6502BASIC V0.1 -",0`; LINPRT puts a space before the number.
  `QT_BYTES_FREE` ends with CR LF and its 0; RESTART adds the blank line before OK.
- Net: 2 bytes (INIT), image 12056 bytes. All `tests/*.out` files change in their first lines
  only.
