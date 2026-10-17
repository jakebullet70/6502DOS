# Working in this repo

UXCBASIC is a native-code BASIC compiler for the Commander X16. The compiler is written in GPC BASIC
(`src/`) and builds to `build/UXC.PRG` plus `build/UXC.OVL`. The editor, UXCEDIT, is in
`src/UXCEDIT/` and builds to `build/UXCEDIT.PRG` plus `build/UXCEDIT.OVL`. The design and the
to-do list are in `docs/UXCBASIC.PLAN.md`. The current state is in `docs/HANDOFF.md`; read it first.
`docs/HISTORY.md` holds the old notes; read it only to trace a past decision.

## Standing orders

- Ask before writing any asm: `GP.ASM` blobs and the templates in `tpl/`.
- Compile SHARED.
- Time every build and run it in the background. Baselines: `build.py UXC` about 31 s quiet and
  72 s loaded, `build.py UXC.HELP` about 55 s, `build.py UXCEDIT` about 160 s loaded (tokenise
  76 s, compile 81 s). A build well past its baseline is locked: stop it and say so.
- Run one compile or test at a time, time it, and report it before the next. A test takes up to 1.1 s;
  past 5 s is a failure to investigate at once. Run the full suite only when single tests pass.
- Run the full suite every 10th step only. After any other step, run the tests of the code
  touched: the new tests and the old tests of that area. `docs/HANDOFF.md` counts the steps
  since the last full suite.
- Never build while tests run. `build.py` empties `build/`.
- Kill the emulator by its PID or handle only, never by image name.
- No `git init` until the user says so.
- Bash heredocs with complex quoting fail. Use Write/Edit, or a Python script in the scratchpad.
- Explain new syntax to the user with an example.

## Tools

Python is `/c/Users/Admin/AppData/Local/Programs/Python/Python313/python.exe`; `python` is not on
PATH. Open files with `encoding='utf-8'`.

| Command | What it does |
|---|---|
| `build.py [NAME ...]` | Builds each program named: `UXC` (the default), `UXC.HELP`, `UXCEDIT`, or `ALL` for the three. Stages `build/` once, builds each, then copies them to `disk/`. |
| `tests.py NAME` | Compiles one test with pyuxc, runs it on the UXDOS16 ROM in the emulator, and compares it with `tests/NAME.OUT`. Needs `build/UXDOS16.ROM` in `C:\dev\CmdrX16\UXDOS16`. |
| `tests.py` | Runs the whole suite. |
| `uxc.py FILE.UXB [--run]` | Compiles one source in the emulator; `--run` runs the PRG too. |
| `run.py [NAME]` | Runs a PRG headless, output to `build/RUN.LOG`. |
| `run.py NAME --window` | Runs a PRG in an emulator window at `-scale 2`, with `-noemucmdkeys` so the Ctrl keys reach the program. |
| `run.py NAME --disk ...` | Runs a PRG from `disk/` instead of `build/`. The headless log stays `build/RUN.LOG`. |
| `help/MKHELP.PY` | Builds the help content from `help/UXC-HELP.md`. |
| `tpl/MKTPL.PY` | Assembles `tpl/*.ASM` into `UXC.TPL.BIN` and `UXC.TPL.BL`. |

`build.py` empties `build/` first and keeps the folder. It keeps `SETTINGS.KVB` and the PRG, OVL, MAP and DEAD of
the programs it does not build. It warns when the `{VAR}` names in `NAME.SRC.SYM` pass 32,768
bytes; past that the compile gets very slow.

`disk/` is the user's drive. A build copies each program built there, its PRG and OVL, with the
files it reads at run time. The GPC runtime goes to `disk/GPC/`. A `.UXB` sample in `examples/`
or `samples/` is copied only when `disk/` has no file of that name. Nothing in `disk/` is deleted.
Builds and tests use `build/`.

The BAT files in the repo root wrap these. `BUILD.BAT` builds `ALL` with no arguments, else the
names given. `RUNUXC.BAT`, `RUNHELP.BAT` and `RUNEDIT.BAT` only run, with
`run.py NAME --disk --window`. Each stops with "Run BUILD first" when `disk/` has no copy of its
PRG. `RUNTESTS.BAT` runs `tests.py` with its arguments.

The emulator and GPC scripts come from `C:\dev\CmdrX16\dos_tools\x16-blitz-compiler`. `tools/gpc`
is a pinned copy of GPC build 133, with its manual in `tools/gpc/GPC-BASIC/`.

## Never read these whole

| File | Lines |
|---|---|
| `src/UXC.HELP.BASL` | 1,978 |
| `src/UXC-FLOW.BL` | 556 |
| `src/UXC-STR.BL` | 876 |
| `src/UXC-EXPR.BL` | 571 |
| `src/UXCEDIT/UXCEDIT.BASL` | 902 |
| `src/UXCEDIT/UXCEDIT-STORE.BL` | 1,629 |
| `src/UXCEDIT/UXCEDIT-VIEW.BL` | 1,510 |
| `docs/UXCBASIC.PLAN.md` | 851 |
| `docs/HISTORY.md` | 651 |
| `tools/gpc/GPC-BASIC/GP-BASIC.md` | 3,690 |
| `build/UXC.MAP`, `build/UXC.SRC.SYM` | generated |

Find the place first, then read only around it:

    grep -n "SM.RESERVED" src/UXC-STMT.BL
    sed -n '60,80p' src/UXC-STMT.BL

Every routine is a dotted label, so the thing you want has a name to grep for.

## Build output

Keep the last ~20 lines and the numbers that matter: the build time, the PRG and OVL sizes, the
test result and time. Do not echo the whole log. A failed test prints what it expected and
what it got.

## Compact

Remind the user to `/compact` after every step, not at the end of a phase. Update
`docs/HANDOFF.md` first, so the work survives the compact.

## Comments

Four kinds earn a place: the **contract** on a callable routine, a **trap** that will cost an hour,
a **checklist** of what else to change, and a `## ---- signpost ----` in a long routine. Nothing
else.

Never write history, and never justify. State what is true now. One person reads this code and it
is the person who wrote it.

No ALL CAPS except in a labelled `WARNING`. No em-dash asides. One fact a sentence. A comment that
restates the code is a naming bug; fix the name.

`.claude/agents/doc-style.md` has the full rules. Invoke `doc-style` for any prose work.

## Code

**Long, descriptive variable names.** BASLOAD crunches every identifier, so a short name saves
nothing in the PRG.

**Write it expanded. Crunching is the user's pass.** One statement a line. A single-statement
conditional is a plain `IF ... THEN <statement>`. Never put a statement on a label's line.

`.claude/agents/basl-author.md` has the rest: GPC semantics, the SHARED memory layout, banked
regions and the build.

## Reply style

The user runs `/caveman ultra`, so replies are terse. Code, comments, docs and memory are normal
prose.
