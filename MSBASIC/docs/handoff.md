# Handoff: project state, engine internals, a pre-pass for full names and CONST

Status on 2026-10-07, at commit 6dd0bf6. This note is for a developer (or a new session) who
picks up the work. It explains how the interpreter works inside, where the project stands, and a
design for a pass over the program before `RUN` starts it, which gives full variable names and
`CONST`. Check `git log` and `TODO.md` first; they may be newer than this note.

## 1. Where the project stands

ux6502Basic is Microsoft BASIC for the NMOS 6502, built with ca65. `src/` is a fork of
mist64/msbasic. One source tree builds three targets:

| Target | Purpose | Check |
|---|---|---|
| `cbmbasic1`, `cbmbasic2` | Original Commodore ROMs | `make verify` must match the ROM dumps byte for byte |
| `sim` | Our build for sim65, headless | `make test` (31 tests) |

The new hardware and its Unix-style kernal do not exist as a target yet. The `sim` target stands
in for them. Everything the kernal must supply is a small set of target primitives (`K_OPEN`,
`K_CLOSE`, `K_READ`, `K_WRITE`, `K_JIFFY`, `K_VPEEK`, `K_VPOKE`, `K_SCREEN`), so the port means
writing those, not changing the interpreter.

Size of the sim image: 12056 bytes at $C000-$EF17, 4072 bytes free below $FF00. 99 tokens are in
use ($80-$E2).

Done, in the sim build only (each behind a `CONFIG_` switch in `src/defines_sim.s`):

- Files through Unix-style handles: `OPEN`, `CLOSE`, `PRINT#`, `INPUT#`, `GET#`, `CMD`, `ST`.
- Block `IF`/`ELSE`/`END IF`, `DO`/`LOOP`/`EXIT`/`CONTINUE`.
- Labels: `100 name:`, `GOTO name`, `GOSUB name`, `RUN name`, `RESTORE name`, names in `ON`.
- Functions and operators: `INSTR`, `HEX$`, `BIN$`, `UCASE$`, `LCASE$`, `RPT$`, `MOD`, `XOR`,
  `SHL`, `SHR`, `DEEK`/`DOKE`, `PI`, `$FF` and `%1010` literals, `POS(1)`.
- Screen: `TEXTAT`, `CLS`, `LOCATE`, `COLOR` (ANSI codes), `SCREEN`, `VPEEK`/`VPOKE` (stubs).
- `PAUSE n`.
- Speed: GOTO target cache, simple-variable cache, faster number input (`CONFIG_FAST_FIN`).
- Removed to save bytes: `LET`, `SPC(`, the startup prompts.
- Long names: no keyword search inside a name (`CONFIG_NAME_NOCRUNCH`), so `TOTAL` is a name.

Next in `TODO.md`, in order: `'` as `REM`; the `FINDATA` bug (`10 X=1: DATA 5` is missed); maybe
drop `TAB(`. After that: SUB and FUNCTION (TODO 2, `docs/sub-function.md`), integer math
(TODO 3), inline assembly (TODO 4, `docs/inline-asm.md`), a user reference (TODO 5).

Open decisions are listed in `docs/inline-asm.md` and `docs/sub-function.md`. The far-memory
`PEEK`/`POKE` idea is deferred; do not build it yet.

## 2. How the engine works

### Memory map (sim)

```
$0000-$00FF  zero page: interpreter state, CHRGET routine, our extras at $F0-$F9
$0100-$01FF  6502 stack: FOR, GOSUB and DO frames, expression temporaries
$0200-$024F  input buffer (INPUTBUFFER, 80 characters, LINE_MAX)
$0400        a zero byte, then the program text from $0401 (TXTTAB)
   ...       program text, ends with a link of $0000
VARTAB       simple variables, 7 bytes each
ARYTAB       arrays
STREND       end of arrays; free space starts here
   ...       free space
FRETOP       string heap grows down from MEMSIZ
MEMSIZ       top of BASIC RAM ($C000, found by the cold-start scan, which stops at SIM_RAMTOP)
$C000-$EF17  BASIC ROM image; the IORAM segment (file table, caches) is inside it, writable
             only because sim65 has RAM there. The new hardware needs that segment in real RAM.
```

`CHKMEM` and `GETSPA` keep STREND below FRETOP. When they meet, the string garbage collector
(`GARBAG`, `string.s`) runs; if that does not help, the result is `?OUT OF MEMORY`.

### Program lines

A stored line is: 2-byte link to the next line, 2-byte line number, tokenized text, a zero byte.
A link of zero ends the program. Keywords are one byte, $80 and up. With
`CONFIG_NAME_NOCRUNCH`, a letter right after a letter is stored as text, so long names and
label names are plain ASCII in the line.

- `PARSE_INPUT_LINE` (`program.s`) tokenizes the typed line in place in the input buffer.
  It walks the keyword table with `KW_PTR` (`CONFIG_KW16`), so the table may pass 256 bytes.
  Lowercase keywords and names are folded; strings, `REM` and `DATA` keep their case.
- `NUMBERED_LINE` / `PUT_NEW_LINE` insert or replace the line, then `FIX_LINKS` rebuilds the
  link chain and `SETPTRS` sets VARTAB behind the program and clears everything. So any edit
  loses all variables, as in every Microsoft BASIC.

### CHRGET

`CHRGET` is a small routine copied into zero page at cold start. It holds `TXTPTR` inside its own
`LDA` instruction (self-modifying code). `JSR CHRGET` steps to the next non-space byte and sets
flags: carry clear for a digit, Z set for end of statement (`:` or zero). `CHRGOT` reads the
current byte again. Every parser in the interpreter reads text through these two.

### Statement loop

`NEWSTT` (`flow1.s`) is the main loop:

1. Call `ISCNTC` (break key).
2. At a zero byte, step to the next line: read the link (zero means end of program), store the
   line number in `CURLIN`, move `TXTPTR`. In direct mode `CURLIN+1` is $FF.
3. `CHRGET`, then `EXECUTE_STATEMENT`.

`EXECUTE_STATEMENT` subtracts $80 from a token and jumps through `TOKEN_ADDRESS_TABLE` with the
RTS trick (push address-1, `JMP CHRGET`, the `RTS` in CHRGET lands in the handler with the next
byte loaded). A byte below $80 is an assignment; with `CONFIG_LABELS` it first goes to
`LABEL_SKIP`, which skips a `name:` label at a line start.

`RUN` with no argument calls `SETPTRS` (TXTPTR to the start of the program, then `CLEARC`) and
returns into `NEWSTT`. `RUN n` or `RUN name` calls `CLEARC` and then `GOTO`.

`CLEARC` (`program.s`) empties the GOTO and variable caches, sets FRETOP = MEMSIZ, closes all
files, sets ARYTAB = STREND = VARTAB (so all variables are gone), resets `DATA`, and resets the
6502 stack. It runs on NEW, RUN, CLR and every program line entry.

### Expressions

`FRMEVL` (`eval.s`) is a precedence parser. The result is in `FAC`, a 5-byte float plus sign;
`ARG` is the second operand. `VALTYP` says string ($FF) or number. Strings are 3-byte
descriptors (length, address); temporary descriptors sit on a small stack at `TEMPST`, with
`TEMPPT` as its pointer. All arithmetic is floating point; `%` variables are converted on every
access (TODO 3 would change that).

### Variables

`PTRGET` (`var.s`) reads a name and returns the address of its value in `VARPNT` (also A/Y).
Only the first 2 characters count; the rest are skipped (section 3 plans full names). The type
goes into bit 7 of the 2 name bytes: `A$` sets bit 7 of the second byte, `A%` sets both. A
simple variable is 7 bytes: 2 name bytes and 5 value bytes (a float, an integer in 2 bytes, or a
string descriptor in 3).

Search: `VC_FIND` (`varcache.s`) looks the name up in a 64-entry direct-mapped cache. On a miss,
PTRGET searches from VARTAB to ARYTAB, and makes a new entry at ARYTAB if the name is not found,
moving all arrays up 7 bytes. A simple variable never moves once it exists, which is why the
cache stays valid until `CLEARC`.

Stores go through `LET` (`misc1.s`, also used by `FOR`) and `PROCESS_INPUT_ITEM` (`input.s`,
used by `INPUT`, `READ` and `GET`). Both call PTRGET and save the address in `FORPNT`. `DEF FN`
also writes its parameter variable for the length of the call.

### GOTO, labels and caches

- `GOTO n` (`flow2.s`) searches the line chain for line n, from the current line when n is
  higher, else from the start.
- `GOTO_CACHED` (`gotocache.s`): the key is the text address of the line number after `GOTO`;
  the value is the target `TXTPTR`. 64 entries, direct-mapped. Direct-mode lines are not cached.
- `LABEL_FIND` (`labels.s`) walks every line from TXTTAB and compares the name with the text
  after the line number, up to `:`. All characters of a label count. The result is cached the
  same way as a line number, so the walk runs only once per call site.

### Blocks and loops

- `FOR` pushes an 18-byte frame (variable address, step, limit, line, text pointer). `GOSUB`
  pushes 5 bytes plus the return address. `DO` pushes a 5-byte frame like `GOSUB`. All on the
  256-byte 6502 stack; `STACK_TOP` is $FA.
- Block `IF` pushes nothing: a false condition scans forward over the tokenized text to the
  matching `ELSE` or `END IF`, counting nesting (`block.s`, state in `BLK_DEPTH`, `BLK_LAST`,
  `BLK_MODE`). `EXIT` and `CONTINUE` scan the same way.

### I/O

The interpreter reaches the console and files only through `IO_CHKIN`, `IO_CHKOUT`, `IO_CLRCH`,
`IO_CHRIN`, `IO_CLALL`, `MONCOUT`, `MONRDKEY` and `ISCNTC`. `handle_io.s` maps logical file
numbers to Unix-style handles and calls the `K_` primitives. In the sim those are sim65
paravirtual calls at $FFF4-$FFF9. Handle 0 is stdin, 1 is stdout.

### Errors

`ERROR` (`error.s`) takes an error number in X, prints `?message ERROR`, adds `IN line` when
`CURLIN` is a program line, resets the stack and returns to the prompt. Each new message costs
its text plus a table entry, so reuse an existing message where the meaning fits.

### Build and test

Run `make all`, `make test` and `make verify` in Git Bash. Tests type `tests/NAME.bas` into the
sim and compare the output with `tests/NAME.out`. Every `src/` change gets a test, an entry in
`docs/changes.md` in the same commit, and a size note in `docs/keywords.md` when a keyword
changes. Changes that are not for `cbmbasic1`/`cbmbasic2` go behind `.ifdef`.

## 3. A pre-pass at RUN: full names and CONST

### What the pre-pass is

Today `RUN` starts executing at once, and everything is found lazily: a label on its first
`GOTO`, a variable on its first use. The pre-pass is a pass over the program text that runs
before the first statement executes. It is not part of the statement loop, so it is not bound
by the shortcuts the run-time code takes for speed. It runs once per `RUN`, so it may be slow
compared with one statement.

It does two jobs, in this order:

1. **Names.** It finds every variable name in the program and picks a hash seed that gives each
   distinct spelling its own 2-byte key. After that, all characters of a name count.
2. **Constants.** It runs the `CONST` lines, so the constants exist before any other variable.

```
RUN
 └─ SETPTRS / CLEARC            (as now: clear variables, caches, stack)
 └─ PREPASS                     (new)
     NAMES: repeat
              walk every name in the text, check for two spellings with one key
            until no clash (else next seed)
     CLEARC                     (drop the entries the name walk made)
     CONST: for each line
              CURLIN = line number   (so errors print "IN line")
              first byte = CONST?  → evaluate and create the constants
            CONSTEND = ARYTAB   (end of the constants)
 └─ NEWSTT                      (as now)
```

### Full names

The 2-character limit is a run-time limit, not a limit of the program text. With
`CONFIG_NAME_NOCRUNCH` a name is stored in the line as plain ASCII, all of it. `PTRGET` already
reads every character of the name: it keeps characters 1 and 2 in `VARNAM` and skips the rest
in the loop at `L2ECE` (`var.s`).

**Run time: hash the rest of the name into the key.** In that loop, fold each character from the
third on into the second key byte, together with a seed byte (`NAMESEED`, 1 byte of RAM). The key
keeps its 2-byte form, so the variable table, the 7-byte entries, the variable cache and arrays
stay as they are. A lookup costs a few cycles more per character after the second.

- Names of 1 or 2 characters keep the key they have now. So the `ST` test in `eval.s`, which
  compares `VARNAM` with `S`,`T`, still works.
- The hash goes into bits 0-6 of the second byte only. Bit 7 stays the type flag (`$`, `%`).
- The hash must depend on the order of the characters and on the seed (for example rotate,
  add the character, add the seed), so `ABCD` and `ABDC` do not get the same key for every seed.
- `DEF FN` names and array names go through the same code, so they get full names too.

**Pre-pass: make sure no two spellings share a key.** A hash alone is not enough: with 7 bits per
first letter, 10 names that start with the same letter clash about one time in three. The
pre-pass checks the whole program, and when two different spellings get the same key, it changes
the seed and checks again. This is perfect hashing, picked at `RUN`, so the user never sees a
clash.

The check uses the normal `PTRGET`, so it needs no new table:

- Walk the text. At each name, call `PTRGET` (it creates the entry if it is new).
- A new entry has a zero value. Store the text address of this spelling in its value bytes.
- An entry that exists holds the text address of the first spelling. Compare the two spellings
  up to the end of the name. If they differ, it is a clash: next seed, `CLEARC`, walk again.
- When a walk ends with no clash, `CLEARC` drops all entries. The seed stays for the run.
- If every seed fails (very unlikely, but possible), stop with an error in the line of the
  second spelling, so the user can rename one name.

**What the walk must see.** Missing a name is a bug: its key is not checked. Seeing too much is
safe: a word that is not a variable (a label, the `FF` of `$FF`, a word in a string) only makes
an entry that is dropped, and at worst a clash that costs one more seed. So the walk can be
simple:

- A name starts at a letter that does not follow a letter or a digit.
- Skip strings, and skip to the end of the line after `REM` and to the end of the statement
  after `DATA`. This is to keep the name count low, not for correctness.
- Treat `X(` like the simple name `X`: stop at `(`, do not go into `ARRAY`. Arrays and simple
  variables use the same hash, so checking the spelling once covers both. `SUBFLG = $40` stops
  the array branch, but it also turns `%` into a syntax error, so the walk needs its own flag.
- Labels after `GOTO`, `GOSUB`, `RUN` and `RESTORE` and `name:` at a line start may be skipped
  or not; both are correct.

**When the seed is stale.** A new line can add a name that clashes. Any program line entry
already clears all variables and makes `CONT` impossible, and the next `RUN` runs the pre-pass.
What is left:

- `GOTO 100` typed at the prompt starts the program without `RUN`. Same case as for `CONST`
  below; one dirty flag covers both.
- A name typed only in direct mode is not checked. It can share a key with a program name, and
  then reads that variable. Rare, and only at the prompt. Accept and document it.

### What CONST does

Syntax: `CONST name = expression [, name = expression ...]`, alone at the start of a line.

- In the pre-pass, after the name check, each `name = expression` is handed to the normal `LET`
  code. LET calls PTRGET, which creates the variable at the start of the variable table, because
  the table is empty at that point. The expression may use numbers, strings, `PI`, functions and
  earlier constants.
- After the pre-pass, the constants are the first entries from VARTAB up to a new pointer,
  `CONSTEND`.
- `CLEARC` sets ARYTAB and STREND to `CONSTEND` instead of VARTAB. So `CLR` keeps the
  constants, and normal variables are made above them. `NEW` and line entry must set
  `CONSTEND` back to VARTAB.
- At run time, a `CONST` line does nothing: its token jumps to the `DATA` handler, which skips
  to the end of the statement.
- A store into a constant is an error. The check sits where LET and PROCESS_INPUT_ITEM save the
  address in `FORPNT`: if the address is below `CONSTEND` and the pre-pass is not running,
  stop with an error. One shared routine (store FORPNT, compare) replaces the two `STA`/`STY`
  pairs, so the check costs little. `FOR` on a constant fails through LET.
- Reads need no change. A constant is found like any variable, and the variable cache makes it
  as fast as a normal variable.
- A string constant points into the program text, as a string literal in an assignment already
  does, so it takes no heap space.
- Names are full names (see above), so `CONST MAXSPEED=5` and `CONST MAXSIZE=9` are two
  constants, and a variable `MA` is a third name. A second `CONST` with the same full name
  overwrites the first, because the store check is off while the pre-pass runs. Report it (the
  entry already exists before LET) or document it.

This solves the main problem in `TODO.md`, "all CONSTs must run before any other variable is
created": the pre-pass makes that true by construction, wherever the CONST lines are in the
program.

### Cases to handle

- **GOTO in direct mode.** `GOTO 100` typed at the prompt starts the program without `RUN`, so
  the pre-pass does not run: the seed may be stale and the constants do not exist. Options: run
  the pre-pass from the direct-mode branch of `GOTO_CACHED` too (it already tests for direct
  mode), or use a flag that line entry and `NEW` set and the pre-pass clears, and run the
  pre-pass when the flag is set.
- **CONT.** Line entry already makes `CONT` impossible, so the seed and the constants are always
  current.
- **A normal variable in a CONST expression.** `CONST B=A*2` with no constant `A` would create
  `A` during the pre-pass, so `A` becomes read-only. Either accept and document it, or let
  PTRGET give an error for a new name while the CONST part runs (a few bytes more).
- **CONST not at a line start.** `10 X=1: CONST Y=2` is not seen by the pre-pass, and at run
  time the line does nothing. Either document it or make the run-time handler give an error when
  the constant does not exist.
- **DEF FN parameter.** `DEF FN F(C)` with a constant `C` writes `C` during the call. Rare;
  document it or check it.
- **Array constants.** Not planned. `DIM` stays the way to make arrays.

### Cost estimate

Guesses until code exists:

| Part | Bytes |
|---|---|
| Hash in the `PTRGET` name loop (`and #$7F`, seed) | 10-14 |
| Name walk (letters, strings, `REM`, `DATA`, `(`) | 40-60 |
| Spelling check (store text address, compare) and seed retry | 25-35 |
| `CONST` keyword entry and token | 6-8 |
| Pre-pass line loop (can share code with `LABEL_FIND`) | 20-30 |
| CONST in the pre-pass (loop over `LET`, commas) | 10-15 |
| `CONSTEND` pointer, set in pre-pass, used by `CLEARC` | 8-10 |
| Read-only check (shared FORPNT routine) | 12-18 |
| Direct-mode GOTO or dirty flag | 8-12 |
| New error message, if one is added | 12-16 |
| **Total** | **about 150-220** |

The full names alone (first three rows plus the line loop) are about 95-140 bytes, and they help
every program, not only programs with constants. RAM: `NAMESEED` (1 byte) and `CONSTEND`
(2 bytes); check `defines_sim.s` for free zero page.

### What else the pre-pass can do later

Once the walk exists, more declarations can use it for a few bytes each:

- **SUB and FUNCTION** (TODO 2): record each `SUB name` address in the pre-pass, so the first
  `CALL` does not scan. The pre-pass can also check that every `SUB` has an `END SUB`. Full names
  remove the name clash between parameters, LOCALs and globals noted in `docs/sub-function.md`.
- **Labels**: report a duplicate label at `RUN` instead of silently using the first one.
- **Block checks**: report an `IF ... THEN` block with no `END IF`, or a `DO` with no `LOOP`, at
  `RUN` instead of when the scan runs off the end.
- **Inline assembly** (TODO 4): full names remove the label clash noted in `docs/inline-asm.md`
  (`.LOOP1` and `.LOOP2`). The pre-pass could also run the assembler's first pass, so forward
  labels are known and the program no longer needs the `FOR P=0 TO 1` loop. This would reverse
  the decision that two passes are not automatic, so ask first.

### Questions for the user

1. Which error for a store into a constant: a new message (for example `?CONST ERROR`, about
   14 bytes) or an existing one? The same question for "every seed failed".
2. Hash into the second key byte only (1- and 2-character names keep their keys, `ST` keeps
   working), or into both bytes (14 bits, fewer seed retries, but `ST` and the type bits in
   the first byte need care)?
3. Direct-mode `GOTO`: run the pre-pass there, use a dirty flag, or document it?
4. Should the pre-pass also take over the SUB lookup and the assembler's first pass when those
   are built?
5. Where in the TODO order: before or after `'` as REM and the FINDATA bug? Full names could be
   built first, alone, since they do not need `CONST`.

### Ways to save bytes

- Reuse the `DATA` handler for the run-time CONST (no new handler).
- Reuse `LET` for the CONST evaluation (no new parser).
- Reuse `PTRGET` and the variable table for the spelling check (no new table).
- One shared routine for the read-only check at both store points.
- Share the line walk with `LABEL_FIND`, and the string and `REM` skips with `block.s`.
- Let the name walk over-count (labels, `$FF`, words in strings) instead of adding skip code.
- Reuse an existing error message.
- Infer BYTE or WORD from the value in the assembler (see `docs/inline-asm.md`), so typed
  `CONST BYTE` keywords are never needed.
