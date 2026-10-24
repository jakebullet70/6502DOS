# Working in UXCBASIC

UXCBASIC is the native-code BASIC compiler of 6502DOS. pyuxc, in Python, is the compiler; it
compiles for the 6502DOS API only. The standing orders of the 6502DOS `CLAUDE.md` apply here.

The design and the to-do list are in `docs/UXCBASIC.PLAN.md`. The compiler's state is in
`docs/HANDOFF.md`. `docs/HISTORY.md` holds the old notes; read it only to trace a past decision.
The language reference is `help/UXC-HELP.md`; grep it for a topic.

The GPC UXC, the frozen compiler that pyuxc is a port of, is in `../attic/gpc`. Nothing here
uses it.

## Layout

| Path | What it is |
|---|---|
| `pyuxc/` | The compiler. `pyuxc.py` is the command line; `README.md` maps each module to its GPC source. |
| `tpl/` | The runtime templates in 64tass asm; `tpl/UXDOS/` holds the 6502DOS versions of `API.ASM`, `R-FILE.ASM` and `SYS.ASM`. |
| `help/` | `UXC-HELP.md` and `MKHELP.PY` |
| `tests/` | Each test is `NAME.UXB` and `NAME.OUT`, with `NAME.IN` for typed input. |
| `samples/` | Sample programs |
| `docs/` | The plan, the handoff, the history, and the 65C02 and X16 references in `asm/` and `x16/` |

## Tools

Run each from the 6502DOS folder.

| Command | What it does |
|---|---|
| `UXCBASIC/tests.py NAME` | Compiles one test with pyuxc, runs it on `build/6502DOS.ROM` in the emulator, and compares it with `tests/NAME.OUT`. Build the ROM first. |
| `UXCBASIC/tests.py` | Runs the whole suite. `RUNUXCTESTS.BAT` wraps it. |
| `UXCBASIC/pyuxc/pyuxc.py FILE.UXB` | Compiles one source. |
| `UXCBASIC/tpl/MKTPL.PY` | Assembles `tpl/*.ASM` into the template tables with `tools/64tass`. `tools/build.py` runs it when a template is newer than `tpl/UXDOS/UXC.TPL.BIN`. |
| `UXCBASIC/help/MKHELP.PY` | Builds the help pages in `help/HELP-TXT/` from `help/UXC-HELP.md`. |

The tables `tpl/UXC.TPL.BIN`, `tpl/UXC.TPL.IDS` and `tpl/UXDOS/UXC.TPL.BIN` are kept in the repo.
pyuxc reads the ids from `tpl/UXC.TPL.IDS` and the 6502DOS table from `tpl/UXDOS/UXC.TPL.BIN`.
The records of both tables must have the same ids; MKTPL stops when they do not.

A test takes up to 1.1 s; past 5 s is a failure to investigate at once.

## Never read these whole

| File | Lines |
|---|---|
| `docs/UXCBASIC.PLAN.md` | 1,730 |
| `help/UXC-HELP.md` | 1,254 |
| `pyuxc/uxc_str.py` | 1,141 |
| `pyuxc/uxc_expr.py` | 1,053 |
| `docs/HISTORY.md` | 1,383 |

Find the place first, then read only around it.

## Code

pyuxc uses only what UXCBASIC can express: fixed tables, no recursion, the same passes. A GPC
variable is an attribute of `g`: `CB.N` is `g.cb_n`. A GPC routine is a function of the same
name in lower case: `TP.LOAD` is `tp_load`.
