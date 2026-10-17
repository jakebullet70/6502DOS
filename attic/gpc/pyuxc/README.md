# pyuxc

pyuxc is the UXCBASIC compiler in Python. It runs on the PC and writes the same PRG as the GPC
UXC. It is the compiler for UXDOS16 work until UXCBASIC compiles itself.

## Plan

1. Port the GPC UXC to Python, a module at a time. The Python code keeps the GPC data layout:
   the symbol table, the code buffer and the fixups stay byte arrays laid out as in the RAM
   banks. The output matches the GPC UXC byte for byte on the whole corpus.
2. Retire the GPC UXC. It stays in `src/` as a frozen reference.
3. Add the features the self-hosted compiler needs, in Python only: data in banked RAM, code in
   banked RAM with calls from one bank to another, and string arrays.
4. Rewrite the compiler in UXCBASIC, compiled by pyuxc. Its output matches pyuxc byte for byte.
   It then compiles itself.

pyuxc uses only what UXCBASIC can express: fixed tables, no recursion, the same passes.

## The corpus

The corpus is `tests/*.UXB`, `examples/*.UXB`, `samples/*.UXB` and the UXDOS16 programs in
`c:\dev\CmdrX16\UXDOS16\src\bas`. `golden.py` compiles each with the GPC UXC into `golden/`:
`NAME.RESULT`, the result line, and `NAME.PRG`. `golden/TIMES.TXT` holds the GPC compile times.
`golden.log` is the output of the last run of the whole corpus.

`cases/` holds hand-made sources and their include files. Each tests a part of pyuxc that the
rest of the corpus does not reach yet, or reaches only on a good line. The `LX` cases stop with an
error in the first pass. The `LK` cases have no statement, or stop at the first. The `EX` cases hold expressions and the
simple statements; each `EXERR` case stops with one error. The `CT` cases hold `IF`, the loops,
`FOR` and `GOTO`, and the `CS` cases `ON CASE`; each `CTERR` and `CSERR` case stops with one
error. The `SB` cases hold `SUB`, `FUNCTION` and calls, the `NM` cases `BIND`, and the `EN` cases
`ENUM`; each `SBERR`, `NMERR` and `ENERR` case stops with one error. The `SG` cases hold string
variables, the string functions, files and `INPUT`; each `SGERR` case stops with one error. The
`PT` cases hold addresses, `PEEK`, `POKE` and `ContentsAt`, and the `AR` cases array elements of
each type and index; each `PTERR` and `ARERR` case stops with one error. The `RD` cases hold
signed fields, `LEN` of records and a record at a fixed address; each `RDERR` case stops with
one error. The `AS` cases hold each operand form, the bit instructions, jumps and lines of
bytes in an `ASM` block; each `ASERR` case stops with one error. They are part of the corpus, so `golden.py` and `compare.py` take them as they
take the others. `golden-cases.log` is the output of the run that made their reference.

## Use

    python pyuxc/pyuxc.py FILE.UXB [-I FOLDER]... [-o FOLDER] [--result FILE]
    python pyuxc/compare.py [--all] [NAME ...]

`pyuxc.py` compiles one source. `#INCLUDE` looks in the source's folder, then in each `-I`
folder. The PRG goes into the `-o` folder, by default the source's folder. The exit status is
0 on OK, 1 on a compile error, and 2 when the compile reaches a part not ported yet.

The program calls the UXDOS16 API, with the table `tpl/UXDOS/UXC.TPL.BIN`. The stock ROM is not
supported.

`compare.py` compiles the corpus with pyuxc for the stock ROM's table, `tpl/UXC.TPL.BIN`, the one
the GPC UXC uses, into `out/` and compares each result line and PRG
with `golden/`. It prints a line for each source that differs, with the first byte that
differs, and counts the sources that reach each routine not ported yet. It names each record
of `tpl/UXC.TPL.BIN` that differs from the table in `golden/`. Records are matched by name, from
`UXC.TPL.IDS`, so a record whose id moved does not count as changed.

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
| `uxc_case.py` | `UXC-CASE.BL` |
| `uxc_select.py` | none: `SELECT CASE`, in pyuxc only |
| `uxc_record.py` | `UXC-RECORD.BL` |
| `uxc_asm.py` | `UXC-ASM.BL` |
| `uxc_once.py` | `UXC-ONCE.BL` |
| `compare.py`, `golden.py` | the corpus tools |
| `cases/` | hand-made sources, part of the corpus |

A GPC variable is an attribute of `g` with the name in lower case and `.` as `_`: `CB.N` is
`g.cb_n`, and `ER.M$` is `g.er_m`. A GPC routine is a function with the same name: `TP.LOAD`
is `tp_load`. A RAM bank is a `bytearray` of 8192 bytes. `g.ram` is the bank
that `BANK` selected, and `PEEK($A000 + n)` is `g.ram[n]`. A source line is a `str` of latin-1
characters, one for each byte of the file.
`ER.STOP` raises `Stop`, and `compile_file` makes the result line from it. A routine not ported
yet raises `NotPorted` with its GPC name.

pyuxc does not read `UXC.INPUT` and does not chain to another PRG.

## Port steps

Each step ends with every corpus source of its area matching `golden/`.

| Step | Module | GPC source |
|---|---|---|
| 1 | The corpus and the reference | `golden.py` |
| 2 | The command line, the templates, the compare tool | `UXC.BASL`, `UXC-CODE.BL` (templates) |
| 3 | The source reader, the tokens, `#INCLUDE`, the symbol table, the first pass's loop and `NAMESPACE` | `UXC-LEX.BL`, `UXC-SYM.BL`, `UXC-ONCE.BL`, `SB.SCAN`, `NM.SCAN` |
| 4 | The code buffer, the fixups, the link, the PRG, the end of the compile | `UXC-CODE.BL`, `UXC-LINK.BL`, `UXC.FINISH`, `SB.POOLS`, `SG.MAXES`, the start of `SM.LINE` |
| 5 | Expressions, constant folding, conditions, the simple statements | `UXC-EXPR.BL`, `UXC-FOLD.BL`, `UXC-COND.BL`, `UXC-STMT.BL`, `UXC-LONG.BL`, `UXC-INDEX.BL`, the parts of `UXC-NAME.BL`, `UXC-STR.BL`, `UXC-SUB.BL` and `UXC-RECORD.BL` that a number reaches |
| 6 | `IF`, the loops, `FOR`, `ON CASE` | `UXC-FLOW.BL`, `UXC-FOR.BL`, `UXC-CASE.BL` |
| 7 | `SUB`, `FUNCTION`, namespaces, `BIND`, `ENUM` | `UXC-SUB.BL`, `UXC-NAME.BL` |
| 8 | Strings | `UXC-STR.BL` |
| 9 | Pointers, and the array parts that step 5 leaves | the array parts of the rest |
| 10 | Record types | `UXC-RECORD.BL` |
| 11 | `ASM` | `UXC-ASM.BL` |
| 12 | The whole corpus matches; pyuxc replaces the GPC UXC in `tests.py` | |

## Status

Step 1 is done, 2026-10-14. `golden/` holds 161 sources: 79 compile to a PRG, 82 stop with an
error. Each error line matches the first line of its `tests/NAME.OUT`. The run took 429 s: 1.9 s
to 9.0 s a source, STRLR the longest. `golden/` keeps the template table it was made with.

Step 2 is done, 2026-10-14. pyuxc loads the template table. A missing table, a wrong header
and a wrong record count give the GPC error messages of `TP.LOAD`. `compare.py` runs the corpus in 0.3 s: all 161 sources stop at `SY.INIT`, not
ported.

Step 3 is done, 2026-10-14. pyuxc reads the source and its `#INCLUDE` files, makes the tokens,
keeps the symbol table, and runs the first pass up to the first `SUB` header or `BIND`. The 43
sources in `cases/` match `golden/`. Of the other 161 sources, 121 finish the first pass and stop
at `EMIT`, 38 stop at `SB.HEADER`, and 2 stop at `NM.BIND.SCAN`, all not ported. `compare.py`
runs the corpus in 0.2 s.

Step 4 is done, 2026-10-14. pyuxc emits the templates, keeps the fixups and the strings, links
the program and writes the PRG. The second pass runs each line up to `SM.STMT`: a blank line and
a comment compile, and a line that does not start with a name is a `SYNTAX ERROR`. The 52
sources in `cases/` match `golden/`, and 3 of them compile to a PRG of 172 bytes. The other 161
sources stop at `SM.STMT` (121), `SB.HEADER` (38) and `NM.BIND.SCAN` (2), not ported.
`compare.py` runs the corpus in 0.4 s.

Step 5 is done, 2026-10-14. pyuxc compiles expressions, constant folding, `LONG` operators,
array elements, `PEEK` and `ContentsAt`, and the statements `PRINT`, `DIM`, `VAR`, `CONST`,
`name = expr`, `POKE`, `POS`, `CLOSE`, `ERRORS`, `END`, labels and `NAMESPACE`. A `PRINT` of a
literal compiles. The 81 `EX` cases match `golden/`, 4 of them as a PRG of up to 4461 bytes; the
GPC UXC made their reference in 154 s. Of the 294 corpus sources, 180 match and 114 stop at a
part not ported, the most at `SB.HEADER` (38), `SG.DIM` (20) and `RD.TYPE` (12). `compare.py`
runs the corpus in 0.4 s. The jumps and conditions of `UXC-COND.BL` are ported, but nothing
reaches them before step 6.

Step 6 is done, 2026-10-14. pyuxc compiles `IF`, `ELSEIF`, `ELSE`, `DO`, `LOOP`, `REPEAT`,
`FOR`, `NEXT`, `EXIT`, `CONTINUE`, `GOTO` and `ON CASE`. The 75 `CT` and `CS` cases match
`golden/`, 6 of them as a PRG of up to 3168 bytes; the GPC UXC made their reference in 155 s. Of
the 369 corpus sources, 277 match and 92 stop at a part not ported, the most at `SB.HEADER`
(38), `SG.DIM` (20) and `RD.TYPE` (12). `compare.py` runs the corpus in 0.9 s.

Step 7 is done, 2026-10-14. pyuxc compiles `SUB`, `FUNCTION`, `ENDSUB`, `ENDFUNCTION`,
`RETURN`, `CALL`, calls in statements and expressions, `BIND` and `ENUM`. The 67 `SB`, `NM` and
`EN` cases match `golden/`, 6 of them as a PRG of up to 1620 bytes; the GPC UXC made their
reference in 123 s. Of the 436 corpus sources, 371 match and 65 stop at a part not ported, the
most at `SG.DIM` (28) and `RD.TYPE` (19). `compare.py` runs the corpus in 1.2 s. A `STRING`
parameter, result or `RETURN` reaches `SG.PASS`, `SG.RESULT` or `SG.RETURN.EMPTY`, not ported.

Step 8 is done, 2026-10-14. pyuxc compiles string variables, `name$ = expr`, joins, string
compares, `LEN`, `ASC`, `VAL`, `LVAL`, `CHR$`, `STR$`, `MID$`, `INSTR`, `OPEN`, `EOF`, `READ`,
`WRITE`, `INPUT`, `LINPUT`, and `STRING` parameters and results. The 39 `SG` cases match
`golden/`, 4 of them as a PRG of up to 2890 bytes; the GPC UXC made their reference in 75 s. Of
the 475 corpus sources, 445 match and 30 stop at a part not ported: `RD.TYPE` (19), `AS.ASM`
(8) and `AS.SYS` (3). `compare.py` runs the corpus in 1.3 s. `LEN` of a `TYPE` or of a record
reaches `RD.LEN`, not ported.

Step 9 is done, 2026-10-14. The pointer and array parts outside `UXC-RECORD.BL` were ported in
step 5, and no corpus source stopped at them. A line coverage run of the corpus shows them run.
The 37 `PT` and `AR` cases match `golden/`, 5 of them as a PRG of up to 3988 bytes; the GPC UXC
made their reference in 74 s. Of the 512 corpus sources, 482 match and 30 stop at a part not
ported: `RD.TYPE` (19), `AS.ASM` (8) and `AS.SYS` (3). `compare.py` runs the corpus in 1.4 s.
An element of a record array reaches `RD.INDEX`, `RD.AT.ELEMENT` or `RD.LET.ELEMENT`, not
ported.

Step 10 is done, 2026-10-14. `uxc_record.py` holds all of `UXC-RECORD.BL`: `TYPE`, record
variables and arrays of records, fields, record copies, string maxes and `LEN` of a record. The
38 `RD` cases match `golden/`, 1 of them as a PRG of 995 bytes; the GPC UXC made their reference
in 92 s, 28 s of it for `RDERRMANY`. Of the 550 corpus sources, 539 match and 11 stop at a part
not ported: `AS.ASM` (8) and `AS.SYS` (3). `compare.py` runs the corpus in 1.6 s.

Step 11 is done, 2026-10-14. `uxc_asm.py` holds all of `UXC-ASM.BL`: `ASM` lines and blocks,
labels and branches, and `SYS`. The 22 `AS` cases match `golden/`, 3 of them as a PRG; the GPC
UXC made their reference in 41 s. All 572 corpus sources match, and no part is left not
ported. `compare.py` runs the corpus in 1.5 s.

Step 12 is done, 2026-10-14. `tests.py` compiles each test with pyuxc into `build/`, with
`#INCLUDE` looking in `tests/`, then `lib/`, and runs the PRG in the emulator. It does not
need `build/UXC.PRG`. For a test with `tests/NAME.NEXT`, it runs the PRG that file names in
place of the compiled one. The full suite: 155 tests, 0 failed, 69 s; the slowest test takes
1.1 s.

Part 1 of the plan is done.

Part 2 is done, 2026-10-14. UXDOS16's `tools/uxb.py` compiles with pyuxc into its
`build/uxc`, with `#INCLUDE` looking in the source's folder, then the folder of the `DOS.UXI`
version. `ARGS`, `ASK` and `SHOW` give the same bytes as the GPC UXC. `DOSAPI.UXB` compiles to
14726 bytes in 0.13 s. `RUNTESTS.BAT` no longer needs `build/UXC.PRG`. The GPC UXC is used
only by `golden.py`, for a reference.

Part 3 is next: data in banked RAM, code in banked RAM, and string arrays.

## Differences from GPC UXC

pyuxc follows the GPC source as written, except as below.

- A body before `ELSEIF`, `ELSE`, or a `CASE` of `SELECT CASE` or `ON CASE` has no jump out
  when its last statement is `RETURN`, `GOTO`, `EXIT`, `CONTINUE` or `END`. A statement after
  `IF c THEN` does not count. This is for the UXDOS16 table only: for the stock table, as in
  `compare.py`, the jump stays, as in GPC UXC. `sm_jumped` and `sm_unreached` in `uxc_stmt.py`
  do it. The test is `JUMPOUT`.

Where GPC's arithmetic does not follow its source, the outputs differ:

- GPC compares a number with the constant 268435455 as if the constant were 268435966. A hex
  constant from `$100000000` to `$100001FEF` (4294967296 to 4294975471) passes `LX.RADIX` with no
  error in GPC UXC. pyuxc stops with `OVERFLOW`. The corpus has no such constant.
