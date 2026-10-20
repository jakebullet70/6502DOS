# Working in MSBASIC

Microsoft BASIC for 6502 (1978 source, `m6502.asm`, DEC MACRO-10 syntax). Goal: build, run and
test it with ca65, then extend it for new hardware with a new Unix-style KERNAL. The standing
orders of the 6502DOS `CLAUDE.md` apply here. All paths below are relative to `MSBASIC/`.

## Rules

- `docs/x16/` and `docs/x16-basic-compare.md` are copies of the X16 manual. They stay local and
  git-ignored; never commit them.
- Stage files by name; never `git add -A`.
- Do not name the X16 as the target in this file or in `docs/`. The target is new hardware with a
  new Unix-style kernal.
- Run `make verify` after a change to a shared source; `cbmbasic1` and `cbmbasic2` must match.

- `m6502.asm` is frozen history. Do not edit it. Work goes into `src/` (ca65).
- CPU is NMOS 6502 only, with no 65C02 opcodes, in every target but `uxdos`. The `uxdos`
  target, for the 6502DOS ROM, may use 65C02 opcodes. See `docs/asm/6502-notes.md`.
- `m6502.asm` is about 50k tokens. Never read it whole; grep, then read line ranges.
- Use `git mv` / `git rm` for tracked files.
- Log every change to `src/` (what and why) in `docs/changes.md`, in the same commit.
- ROM space is tight. With every change, suggest ways to save bytes (in that code or nearby).
- Compatibility with CBM BASIC does not matter for the `sim` and new-kernal builds: keywords,
  tokens and behavior may change or go away if that saves bytes or helps. Old CBM programs and
  saved tokenized files need not run. The `cbmbasic1`/`cbmbasic2` builds must still pass
  `make verify`, so put such changes behind an `.ifdef` in shared sources.
- Compatibility with X16 BASIC does not matter either. X16 keywords are a source of ideas only;
  their syntax and behavior may differ.

## Tools (not on PATH)

- ca65/ld65/sim65 V2.19: `C:\8bitProgramming\cc65\bin\`
- make: `C:\8bitProgramming\make-4.4.1\bin\make.exe`
- Python: `C:\Users\Admin\AppData\Local\Programs\Python\Python313\python.exe`
- VICE 3.8 (`xpet` for the PET check): `C:\8bitProgramming\GTK3VICE-3.8-win32\`

## Layout

- `src/`: ca65 sources, forked from mist64/msbasic (2-clause BSD, `LICENSE-msbasic`;
  our changes are public domain, Unlicense, `LICENSE`). One `msbasic.s` builds every target; `-D <target>` picks it, `<target>.cfg` sets the memory map.
  Targets: `cbmbasic1` and `cbmbasic2` (checked against the ROM dumps; BASIC 2 runs in xpet) and
  `sim`. The other upstream targets were removed; their `.ifdef` code in the shared sources stays.
- `Makefile` (run in Git Bash): `make all`, `make <target>`, `make test` (see `tests/`), `make verify` (byte-compare with the
  original ROM dumps; prints only mismatches), `make clean`. Output goes to `build/`.
- `sim` target (our addition): headless build for sim65. Files `defines_sim.s`, `sim_extra.s`,
  `sim_iscntc.s`, `sim.cfg`. BASIC at $C000; console on fd 0/1 via sim65 paravirt calls. Any argument
  after the program (`sim65 build/sim.bin echo`) echoes input so stdout is a session transcript
  (for tests; an interactive console echoes by itself). EOF on stdin exits with code 0.
  Keywords and variable names may be typed in lowercase (tokenizer folds them; strings, REM and
  DATA keep their case). Cold start skips the
  MEMORY SIZE? and TERMINAL WIDTH? prompts (RAM is scanned; width is 80). `make run` starts it interactively.
  Run with `sim65 -x <cycles>` in scripts so a hang cannot block.
  Files work: `OPEN lf,"name"[,mode]` (0 read, 1 write, 2 append), CLOSE, PRINT#, INPUT#, GET#,
  CMD, SYS and ST, through `handle_io.s` (see below). Typed lines are cut at 80 characters
  (buffer at $0200, `LINE_MAX`); BS and DEL delete.
  Block `IF c THEN` / `ELSE` / `END IF` and `DO` / `LOOP` / `EXIT [DO]` / `CONTINUE` (`block.s`,
  `CONFIG_BLOCK`). `INSTR([start,] a$, b$)` (`instr.s`, `CONFIG_INSTR`). `HEX$(n)`, `BIN$(n)`
  (`hexbin.s`, `CONFIG_HEXBIN`). `UCASE$(a$)`, `LCASE$(a$)` (`casestr.s`, `CONFIG_CASE`). `TEXTAT x,y,a$ or code[,color]`
  (`textat.s`, `CONFIG_TEXTAT`; ANSI codes in the sim). `RPT$(a$ or code, n)` (`rpt.s`, `CONFIG_RPT`). `a MOD b`
  (`mod.s`, `CONFIG_MOD`). `$FF` hex and `%1010` binary literals (`radixlit.s`,
  `CONFIG_RADIX_LIT`). `PI` constant (`CONFIG_PI`). `XOR(a,b)`, `SHL(a,n)`, `SHR(a,n)`
  (`bitfn.s`, `CONFIG_BITFN`). `DEEK(addr)`, `DOKE addr,n` (`deek.s`, `CONFIG_DEEK`). `PAUSE n` waits n+1
  jiffies (`pause.s`, `CONFIG_PAUSE`; target primitive `K_JIFFY`, a busy loop in the sim).
  `VPEEK(bank,addr)`, `VPOKE bank,addr,n` for video memory, `SCREEN mode` (`vera.s`,
  `CONFIG_VERA`; target primitives `K_VPEEK`, `K_VPOKE`, `K_SCREEN`, stubs in the sim). `CLS`, `LOCATE x,y` (moves the cursor and
  sets `POS()`), `COLOR fg[,bg]` (`textat.s`, `CONFIG_SCREEN`; ANSI codes, which the new kernal's
  POSIX-style console is planned to understand, so no target primitives). `POS(0)` column,
  `POS(1)` line (`CONFIG_POS_LINE`; the sim counts printed lines in `POSY`). Labels: `100 name:`
  at a line start, `GOTO`/`GOSUB`/`RUN`/`RESTORE name`, names in `ON` lists (`labels.s`,
  `CONFIG_LABELS`). The tokenizer does not look for keywords inside a name: a letter right after
  a letter is stored as it is, and a keyword with a letter right behind it is not a keyword
  (`CONFIG_NAME_NOCRUNCH`). So `BORDER` and `TOTAL` are names, and run-together code needs
  spaces: `FOR I`, `IF A=B THEN`, `FN F(`, `END IF`. GOTO/GOSUB targets are cached
  (`gotocache.s`, `CONFIG_GOTO_CACHE`), and so are simple variable addresses (`varcache.s`,
  `CONFIG_VAR_CACHE`); `CLEARC` empties both caches. No LET keyword
  (`CONFIG_NO_LET`), no SPC( (`CONFIG_NO_SPC`; use `RPT$(32,n)`). The keyword table may pass 256 bytes
  (`CONFIG_KW16`).
- I/O layer: the interpreter reaches files only through `IO_CHKIN`, `IO_CHKOUT`, `IO_CLRCH`,
  `IO_CHRIN`, `IO_CLALL`, plus `MONCOUT`, `MONRDKEY`, `ISCNTC`. `io.s` holds the register rules and
  the CBM KERNAL mapping. `handle_io.s` implements them for Unix-style handles on top of the
  target primitives `K_OPEN`, `K_CLOSE`, `K_READ` and `K_WRITE` (sim: sim65 calls; later: the
  new kernal).
- `tests/`: `NAME.bas` is typed into the sim build, `NAME.out` is the expected transcript
  (banner included). `make test` runs `tests/run.py`, which prints only failures and the pass
  count. It ignores line endings and trailing spaces, and a run that hits the cycle limit fails.
  sim65 runs in `build/`, so files that tests write land there. Keep test lines at 80 characters
  or less.
  After an intended output change, run `python tests/run.py --update [NAME]` and review the diff.
- `make pet` starts xpet (3032) with our BASIC 2 ROM (first 8K of `cbmbasic2.bin`).
  `make pet-check` types a program headless and saves `build/pet.png`.
- `defines_sim.s` started from upstream `defines_w65c816sxb.s`, whose zero page overlaps (`Z14`
  and `TEMPPT` both at $65, so FRE hangs). It uses ZP_START4 = $66.

- `TODO.md`: planned work, in order.
- `docs/changes.md`: log of our changes to the msbasic sources.
- `docs/keywords.md`: every keyword, done and planned, with its cost in bytes and the totals.
  Update it when a keyword is added.
- `docs/sub-function.md`, `docs/inline-asm.md`: design notes, byte estimates and plans for TODO 2
  (SUB, FUNCTION) and TODO 4 (inline assembly).
- `docs/handoff.md`: project state, how the engine works inside (memory map, line format, CHRGET,
  statement loop, variables, caches), and a design for `CONST` with a pre-pass before `RUN`.
- `docs/review-superbasic-ehbasic.md`: design lessons from F256 SuperBASIC, EhBASIC and
  picocomputer/msbasic (line input, file I/O, kernal interface, extensions).
- `docs/asm/`: 6502 notes (NMOS rules, ca65) and the 65C02 instruction reference.
- `ref/msbasic/` (git-ignored): mist64/msbasic ca65 port, commit 2a0bc2f, with original ROM
  dumps in `orig/`. Clone: `git clone https://github.com/mist64/msbasic.git ref/msbasic`.
  Its kb9, cbmbasic1, applesoft and osi builds match `orig/` byte for byte with our ca65.
