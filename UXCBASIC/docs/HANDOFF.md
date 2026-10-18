# UXCBASIC handoff, 2026-10-17

The current state, for the next agent. The standing orders are in the repo root's `CLAUDE.md`,
and the commands in `UXCBASIC/CLAUDE.md`. The design and the to-do list are in
`docs/UXCBASIC.PLAN.md`: the order of work is section 4, and the to-do items are section 5.
`docs/HISTORY.md` holds the old notes; read it only to trace a past decision.

Paths are from `UXCBASIC/`. A path marked "repo" is from the repo root.

## Layout

| Path | What it is |
|---|---|
| `pyuxc/` | The compiler, in Python. `pyuxc/README.md` is its reference. |
| `tpl/` | The templates. `tpl/MKTPL.PY` assembles them with repo `tools/64tass`. `tpl/UXDOS/UXC.TPL.BIN` is the UXDOS16 table. |
| `help/` | `UXC-HELP.md`, and `MKHELP.PY`, which writes the pages to `help/HELP-TXT/` |
| `tests/`, `tests.py` | 175 tests. They compile into repo `build/uxctests/` and run on repo `build/UXDOS16.ROM`. Repo `RUNUXCTESTS.BAT` runs `tests.py`. |
| `tests/STRINGS.UXI` | The include of STRLR and STRNS: `NAMESPACE STR`, the user's `InStrRev`, and the user's notes as `//` lines |
| `samples/` | Sample programs. `MKHELP.PY` gives each a row under EXAMPLE PROGRAMS. |
| repo `lib/` | The library: `DOS.UXI`, `HEAP.UXI`, `KEYS.UXI`, `CONS.UXI` and `STR.UXI`, each one namespace of its own name |
| repo `src/bas/`, `src/cbin/`, `src/dos/` | UXDOS16's UXCBASIC programs. Repo `tools/build.py` compiles them with repo `tools/uxb.py`, whose `#INCLUDE` looks in the source's folder, then repo `lib/`. |
| repo `tools/build.py` | Also runs `tpl/MKTPL.PY` when a template is newer than `tpl/UXDOS/UXC.TPL.BIN` |
| repo `attic/gpc/` | The frozen GPC UXC, with `pyuxc/compare.py`, `pyuxc/golden.py`, `golden/` and `cases/`. Its `README.md` lists the rest. Nothing uses it. |

The stock ROM is not supported. pyuxc compiles for UXDOS16 and has no target option.

## State

- The last full suite (repo `docs/HANDOFF.md`, 2026-10-17): 175 tests, 0 failed, 45.7 s. The
  longest test is `ONCASE`, 0.8 s. An error test does not start the emulator.
- Parts 1 and 2 of the pyuxc plan are done: pyuxc replaces the GPC UXC in `tests.py` and in
  repo `tools/uxb.py`.

## Open items

- Part 3 of the pyuxc plan: data in banked RAM, code in banked RAM, and string arrays. Then
  the rewrite of the compiler in UXCBASIC (plan section 4 item 6).
- Removing unused code. Done: the SUBs and FUNCTIONs nothing reaches, the unused global
  variables, and the unused string literals (`pyuxc/uxc_dead.py`), with `#KEEP`,
  `--keep-subs` and `--keep-vars`. Open:
  - S4: a command-line switch that writes a list file of what was removed.
  - S5: a help topic, and plan section 5 "Removing unused code" and "Removing unused
    variables", which still describe the design as undecided.
  - A variable that is only written is kept. The locals of a live SUB are kept.
- `ON CASE` (`pyuxc/uxc_case.py`, tests `ONCASE`, `ERRCASEBEFORE`, `ERRCASETWICE`,
  `ERRCASEWORD`) has no help topic and no entry in the plan.
- `UCASE$` and `LCASE$` as built-ins with `R_*` routines in `tpl/R-STRING.ASM`, as
  `LEFT$` and `RIGHT$` are (`sg_left_right` in `pyuxc/uxc_str.py`). Checklist for a new
  built-in: `sg_function`, `sg_scan_known` (`uxc_str.py`), `nm_word` (`uxc_name.py`), and a
  `BIND` line in repo `lib/STR.UXI` and in `tests/STRINGS.UXI`.
- The user's notes in `tests/STRINGS.UXI` ask for `TRIM`, `LTRIM`, `RTRIM`, `LPAD`, `RPAD`,
  `StartsWith`, `EndsWith`, upper and lower case in place, a `SYS2`, a `conv.UXI` with
  `CBYTE` and `CWORD`, a `TEXT_GUI` namespace and timers. `SYS2` and `TEXT_GUI` are not in
  the plan.
- Record step 6, record parameters (`SUB SHOW(P AS ITEM)`): plan section 5 "Record types".
  TYPEs are declared in the second pass, and the first pass reads the SUB headers, so a record
  parameter needs its TYPE declared in the first pass.
- A record at a fixed address gets no string max. The user is to confirm this choice.
- `NEXT R.X` with a field as the name is not caught: `ct_next` (`pyuxc/uxc_for.py`) compares
  only the value.
- `INPUT` into an array element, a record element included, is not supported.
- Step 4.5d, `DIR`, is put off by the user. It may become code in a `DIR` namespace.
- Proposed, not approved: DIM in the first pass. The first pass declares each DIM, so a BIND
  to a variable and a use before the DIM work on any line; the second pass only emits the
  storage.
- For UXDOS16, in plan section 5: ROM-able output, a `SUB` entered by register (`SUB ... REGS`,
  the registers at `$030C`-`$030F`), `CALL AT` and variables in banked RAM. The plan's item
  "ROM-able output" gives UXDOS16's order. UXDOS16's own order is in repo `docs/PLAN.md`
  section 12.
- Not scheduled, in plan section 5: a compile report, `FRE`, `FILE.SEEK`, `FLOAT` (step 4 of
  "More types"), and the RAM bank manager. The bank manager is decided: built in, asm
  approved, its names to be bound in a new repo `lib/BANK.UXI`, and `BANK.SELECT` to select a bank.

## Traps

- A fixup is dropped by its place, not its owner. `sb_call_pass` and `sb_call_pop`
  (`pyuxc/uxc_sub.py`) store the arguments with the called SUB as owner, in the caller's code.
- An expression entry of type 0 is a constant that fits a BYTE. A test of `<> K_TY_BYTE`
  makes it wide.
- A variable that GPC reads before it sets it needs a 0 default in `uxc_state.dim()`, or
  pyuxc stops with an `AttributeError`.
- A new built-in function in `ex_operand` goes in `sg_scan_known` too, or it is reported as
  UNDECLARED NAME.
- `ex_prec` ranks every operator id from `K_EO_LOR` up as AND or OR. A new `K_EO_` id goes
  below `K_EO_LOR`, and `K_EO_LOR` and `K_EO_LAND` move up.
- The templates are 259 records, ids 0 to 258 in `tpl/UXC.TPL.IDS`. An `F_REC` fixup holds a
  record id in one byte, so a record that `#rec` names needs an id below 256. `T_TOP` is 256; `T_POSROWS` and `T_POSCOLS`, which no `#rec` names, follow it.
  Inserting a template moves the id of every record after it.
- `RUNDIV0.OUT`, `RUNSUB.OUT` and `RUNRECSUB.OUT` hold code addresses, which move when the
  start code changes.
- A test that calls UXDOS16 directly calls `con_out` at `$03B8` and uses `$9E00`-`$9E11` for
  its data.
- Limits in `pyuxc/uxc_defs.py`: `K_SY_MAX` 1008 names in `K_SYM_BANKS` 4 banks, which the
  hidden call records and temps count toward; `K_FX_MAX` 4096 fixups; `K_CN_SIZE` 2,048
  bytes of string CONST text.
- Git Bash `sed -i` turns CRLF into LF. `docs/HISTORY.md`, `docs/UXCBASIC.PLAN.md`,
  `help/UXC-HELP.md`, `pyuxc/uxc_str.py`, `tests/STRINGS.UXI` and some other tests and
  templates are CRLF. Edit them with a Python script that keeps the endings.
- The Write tool strips the trailing spaces of a line, and turns `A` into `A`. Write a
  test's `.OUT` from Python, since a PRINT of numbers ends in a space. Write a source holding
  `\u` from a Python script with `chr(92)`.
- The emulator prints a warning into the test output at the first RMB, SMB, BBR or BBS it
  runs. A test that runs one fails on the warning.
