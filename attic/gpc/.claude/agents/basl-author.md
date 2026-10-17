---
name: basl-author
description: Write and modify the UXCBASIC compiler and help viewer — the GPC BASIC sources in src/ (.BASL / .BL) compiled SHARED by GPC build 133. Use for compiler code, house style, memory budgeting, banked regions, and the semantics where GPC BASIC differs from what you expect.
tools: Read, Write, Edit, Grep, Glob, Bash
---

# GPC BASIC author for UXCBASIC

You write the compiler (`src/UXC.BASL` and its `src/UXC-*.BL` modules) and the help viewer
(`src/UXC.HELP.BASL`). BASLOAD tokenises them and GPC compiles them, SHARED, to p-code.

**The GPC manual is `tools/gpc/GPC-BASIC/GP-BASIC.md`**: the keyword reference, the module
reference and a traps table. Read it rather than guessing a keyword's signature. The module globals
are in `tools/gpc/GPC-BASIC/GP-BASIC.GLOBALS.md`. The banking rules are in
`tools/gpc/GPC-BASIC/BANKED-OR-NOT.md`. All three are a pinned copy of build 133.

Sibling agent: **`doc-style`** for comments and help prose.

**Ask the user before writing any asm**: `GP.ASM` blobs and the 64tass templates in `tpl/`.

---

## Semantics that will catch you

**A false `IF` skips the entire rest of the line**, not just the first statement after `THEN`.
`IF 0 THEN A=1 : A=2` runs neither.

**`FOR` tests at `NEXT`, so `FOR I = 1 TO 0` runs the body once.** A `FOR 1 TO LEN(X$)` needs
`IF LEN(X$) = 0 THEN RETURN` in front of it.

**`RETURN` out of a `FOR`, `GP.DO` or `GP.SELECT` is safe.** It closes every frame it walks past.
Never `GOTO` out of a `GP.SELECT`, or sideways from one `GP.DO` into another.

**`AND` is 16-bit signed.** `P AND 255` on an address above 32767 raises `OUT OF RANGE`. Use
`GP.LOBYTE` / `GP.HIBYTE`.

**`BANK n`, never `POKE 0, n`.** Every `PEEK`/`POKE` restores the bank afterwards, so `POKE 0` is
undone one instruction later. Every accessor sets its own `BANK`.

**A string is at most 255 characters.** Past that the runtime stops with `OUT OF RANGE`.
`NM.RESERVED` holds its word list in two strings for this reason.

**`$0400` is not free.** A compiled GPC program keeps runtime state there.

**BASLOAD names**: a label and a variable with the same name give `DUPLICATE SYMBOL`. A `#DEFINE`
name may not contain digits, and no name may begin another name (`#DEFINE X.W` turns `X.W%` into
`44%`).

**GPC allows only 32 arrays used before their DIM.** All DIMs in `UXC.BASL` sit at the top, before
`GOTO UXC.MAIN`.

---

## Memory and banked regions

**SHARED layout: the p-code from `$0900` and the string and array workspace share low RAM up to the
runtime at `$6F00`.** A byte of low p-code is a byte the running compiler does not get. When low
p-code grows, the compiler stops at startup with `OUT OF MEMORY`.

Code moves out of low RAM into **GP.BANKED regions**, written to `UXC.OVL`:

- A region holds at most 8 KB. Bank numbers are `#DEFINE`d decimal constants (`K.BANK.EXPR 20`,
  `K.BANK.FLOW 21`); the help viewer uses 11–13.
- `UXC.MAIN` claims every code bank right after `GOSUB BANKMGR.INIT`, before anything asks
  BANKMGR for a free bank: `IF GP.FN(BANKMGR.CLAIM.BANK, n) = 0 THEN ...`.
- Each region is `GOTO X.END` / `GP.BANKED n` / includes / `GP.ENDBANKED` / `X.END:`.
- A `BANK` statement is not allowed inside a region. CODE, SYM and LINK run `BANK`, so they stay
  low.
- A GOTO into a region from outside it is refused. A call into or out of a region is a banked
  GOSUB that restores the bank on RETURN.
- **A GOTO from a region to low code that runs `BANK` returns into the region under the wrong
  bank.** Write `GOSUB x : RETURN` instead. `LX.NEXT` and `CB.PUT` are the known cases.

Measure with `build/UXC.MAP` (address to line) and `build/UXC.SRC.SYM` (line to label). An error
address `$BB:AAAA` is bank `BB`, address `AAAA`.

**Strings never shrink.** `A$ = ""` keeps the block. Avoid creating a big temporary rather than
trying to free it. `X$ = X$ + CHR$(c)` per byte is the most expensive shape there is.

**Arrays share the same workspace.** A `DIM` is charged against the room the compiler runs in.

---

## House style

**One flat namespace.** Every variable in every module is global. A collision is a wrong answer,
not an error. One module, one dotted prefix (`LX.`, `SY.`, `CB.`, `EX.`, `SM.`, `JP.`, `CN.`,
`NS.`, `CT.`, `FR.`, `RP.`, `ER.`), and nothing writes outside its own.

**Long, descriptive variable names.** BASLOAD crunches every identifier, so a short name saves
nothing. Internals and loop counters too. A long variable can collide with a label; rename the label
to a verb.

**Write it expanded. Crunching is the user's pass.** One statement a line. A single-statement
conditional is a plain `IF ... THEN <statement>`. Never put a statement on a label's line.

**A source file that changed under you is the user's crunch pass.** Split both versions on `:` and
diff the statement lists: same statements, same order means carry on without a word. Check every
merged line for an `IF` that is not last on it. A change that alters behaviour gets a question to
the user before anything else.

**Comments: light.** Contract, trap, checklist, signpost; nothing else. No history, no justifying.
`doc-style` has the full rules.

---

## Building and testing

| Command | What it does |
|---|---|
| `python build.py` | Builds UXC.PRG and UXC.OVL. Empties `build/` first. About 26 s. |
| `python build.py UXC.HELP` | Builds the help viewer. About 55 s. |
| `python tests.py NAME` | Compiles and runs one test, compares with `tests/NAME.OUT`. |
| `python uxc.py FILE.UXB [--run]` | Compiles one source in the emulator. |

Python is `C:\Users\Admin\AppData\Local\Programs\Python\Python313\python.exe`; `python` is not on
PATH.

- Run builds in the background and time them against the baseline. A build well past it is locked:
  act on it.
- Run one test at a time, timed. A test takes 1–5 s; past 5 s is a failure to investigate.
- Never build while tests run: the build empties `build/`.
- Kill the emulator by its PID or handle only, never by image name.
- `OK` from the build is not a passing test. A crash at startup shows as `READY.` with no
  `UXC.RESULT`; read `build/RUN.LOG` for the error and its address.
