# pyuxc

pyuxc is the UXCBASIC compiler, in Python. It compiles a `.UXB` source into a PRG that calls
the 6502DOS API. It is a port of the GPC UXC in `attic/gpc/src/` of the repo root, and keeps
its passes and its data layout.

Paths below are from `UXCBASIC/`, except where they name the repo root.

## Requirements

- Python 3. The repo runs Python 3.13.
- The template tables in `tpl/`: `tpl/UXDOS/UXC.TPL.BIN`, and `tpl/UXC.TPL.IDS` for the record
  ids. Both are kept in the repo. `tpl/MKTPL.PY` rebuilds them with `tools/64tass` of the repo
  root, and the repo's `tools/build.py` runs it when a template is newer than
  `tpl/UXDOS/UXC.TPL.BIN`.

pyuxc finds the tables from its own folder, so it runs from any folder.

## Usage

```
python pyuxc/pyuxc.py FILE.UXB [-I FOLDER]... [-o FOLDER] [--result FILE] [--keep-subs] [--keep-vars]
```

| Option | Effect |
|---|---|
| `-I FOLDER` | An include folder. It may be given more than once. |
| `-o FOLDER` | The folder of the PRG. The default is the source's folder. |
| `--result FILE` | Writes the result line to FILE as well. |
| `--keep-subs` | Keeps every SUB and FUNCTION, as `#KEEP ALL` does. |
| `--keep-vars` | Keeps every global variable, array and string literal. |

Any other option, or a count of sources other than one, prints the usage and exits with
status 1.

## Output

`FILE.UXB` compiles to `FILE.PRG`, the source's name in capitals: `hello.uxb` writes
`HELLO.PRG`. pyuxc prints the compiler's screen output, then one result line:

```
OK,<prg>,<bytes>[,SECOND <pr2> <bytes>][,REGION <slot> <bytes> BYTES]...[,REMOVED <n> SUBS <m> BYTES][,REMOVED <n> VARS <m> BYTES][,REMOVED <n> STRINGS <m> BYTES]
ERROR,<line>,<message>
```

`SECOND` names the second bank's file of a `#ROMBANKS` program, `NAME.PR2`, and its bytes.
A `REGION` field gives the bytes of each `#REGION_SLOT` region, in slot order. A `REMOVED` field counts what the compile left out, and the bytes saved. `VARS` counts the
bytes of both the variables and the array space.

| Exit status | Meaning |
|---|---|
| 0 | The compile succeeded. |
| 1 | A compile error, or a bad command line. |
| 2 | The compile reached a part not ported. No part of pyuxc raises it now. |

pyuxc does not read `UXC.INPUT` and does not chain to another PRG.

## Include search

`#INCLUDE "NAME"` looks for NAME in the source's folder, then in each `-I` folder in order.

- A name not found stops the compile with `FILE NOT FOUND: NAME`.
- An included file cannot include another: `#INCLUDE IN AN INCLUDED FILE`.
- `tests.py` passes `tests/`. The repo's `tools/uxb.py` passes the repo root's `lib/`.

## Calling from Python

```
import pyuxc
result, screen = pyuxc.compile_file("HELLO.UXB", ["lib"], "build", keep_subs=False,
                                    keep_vars=False)
```

`compile_file(source, include_folders=(), out_folder=None, target="6502dos", keep_subs=False,
keep_vars=False)` returns the result line and the list of screen lines. Each call starts from
a fresh state. The folder `pyuxc/` must be on `sys.path`.

## Targets

| `target` | Table | Used by |
|---|---|---|
| `"6502dos"` | `tpl/UXDOS/UXC.TPL.BIN` | the command line, `tests.py`, the repo's `tools/uxb.py` |
| `"stock"` | `tpl/UXC.TPL.BIN` | `attic/gpc/pyuxc/compare.py` only |

The stock ROM is not supported. The command line has no target option. For `"6502dos"` only:

- The startup code stores the page of the program's end in `PSP_TOP` (`$0702`), by `T_TOP`.
- `OPEN` passes the mode as one letter, with no `@:` prefix.
- A body before `ELSEIF`, `ELSE`, or a `CASE` of `SELECT CASE` or `ON CASE` has no jump out
  when its last statement is `RETURN`, `GOTO`, `EXIT`, `CONTINUE` or `END`. A statement after
  `IF c THEN` does not count. `sm_jumped` and `sm_unreached` in `uxc_stmt.py` do it. The test
  is `JUMPOUT`.

## The files

| File | GPC source |
|---|---|
| `pyuxc.py` | `UXC.BASL`: the command line and the compile |
| `uxc_state.py` | the global variables, as attributes of `g`; `ER.STOP` and the errors in `UXC.BASL` |
| `uxc_defs.py` | `UXC-DEFS.BL`: `K.ORG` is `K_ORG` |
| `uxc_tpl.py` | `UXC.TPL.BL`: the record ids, read from `tpl/UXC.TPL.IDS`; `T.STUB.ID` is `T_STUB` |
| `uxc_code.py` | `UXC-CODE.BL` |
| `uxc_link.py` | `UXC-LINK.BL` |
| `uxc_lex.py` | `UXC-LEX.BL`; channel 2 and the drive |
| `uxc_sym.py` | `UXC-SYM.BL` |
| `uxc_name.py` | `UXC-NAME.BL` |
| `uxc_sub.py` | `UXC-SUB.BL` |
| `uxc_stmt.py` | `UXC-STMT.BL` |
| `uxc_expr.py` | `UXC-EXPR.BL` |
| `uxc_fold.py` | `UXC-FOLD.BL` |
| `uxc_cond.py` | `UXC-COND.BL` |
| `uxc_long.py` | `UXC-LONG.BL` |
| `uxc_index.py` | `UXC-INDEX.BL` |
| `uxc_str.py` | `UXC-STR.BL` |
| `uxc_flow.py` | `UXC-FLOW.BL` |
| `uxc_for.py` | `UXC-FOR.BL` |
| `uxc_case.py` | `UXC-CASE.BL`: `ON CASE` |
| `uxc_select.py` | none: `SELECT CASE` |
| `uxc_dead.py` | none: `#KEEP`, and leaving out unused SUBs, variables and string literals |
| `uxc_rombank.py` | none: `#ROMBANKS`, a program in two ROM banks |
| `uxc_ramreg.py` | none: `#REGION_SLOT`, SUBs in RAM banks at `$A000` |
| `uxc_record.py` | `UXC-RECORD.BL` |
| `uxc_asm.py` | `UXC-ASM.BL` |
| `uxc_once.py` | `UXC-ONCE.BL` |

## Conventions

- A GPC variable is an attribute of `g` with the name in lower case and `.` as `_`: `CB.N` is
  `g.cb_n`, and `ER.M$` is `g.er_m`.
- A GPC routine is a function with the same name: `TP.LOAD` is `tp_load`.
- A RAM bank is a `bytearray` of 8192 bytes. `g.ram` is the bank that `BANK` selected, and
  `PEEK($A000 + n)` is `g.ram[n]`. The symbol table, the code buffer and the fixups are such
  banks, laid out as in the GPC UXC.
- A source line is a `str` of latin-1 characters, one for each byte of the file.
- `ER.STOP` raises `Stop`, and `compile_file` makes the result line from it.
- pyuxc uses only what UXCBASIC can express: fixed tables, no recursion, the same passes.

## pyuxc only

The GPC UXC has none of these:

- `SELECT CASE` (`uxc_select.py`).
- `LEFT$` and `RIGHT$` as built-ins (`sg_left_right` in `uxc_str.py`).
- `END [code]`, the exit code (`T_ENDCODE`).
- `POS(2)` and `POS(3)`, the screen's rows and columns (`T_POSROWS`, `T_POSCOLS`).
- String `CONST`s (`nm_const_string` in `uxc_name.py`).
- Line continuation with ` _` (`lx_join_lines` in `uxc_lex.py`).
- Escaped strings, `!"..."` (`lx_escaped` in `uxc_lex.py`).
- `#KEEP`, and leaving out the SUBs, global variables and string literals nothing uses
  (`uxc_dead.py`). It is on by default; `--keep-subs` and `--keep-vars` turn it off.
- `#ORG` and `#DATA`, output for ROM (`dd_place_scan` in `uxc_dead.py`, `uxc_link.py`).
- `#ROMBANKS`, a program in two ROM banks (`uxc_rombank.py`).
- `#REGION_SLOT`, SUBs in RAM banks (`uxc_ramreg.py`).

## Differences in arithmetic

Where GPC's arithmetic does not follow its source, the outputs differ:

- GPC compares a number with the constant 268435455 as if the constant were 268435966. A hex
  constant from `$100000000` to `$100001FEF` (4294967296 to 4294975471) passes `LX.RADIX` with
  no error in GPC UXC. pyuxc stops with `OVERFLOW`.
