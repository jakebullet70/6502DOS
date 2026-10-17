# UXCBASIC handoff, 2026-10-13

The current state, for the next agent. The standing orders and the commands are in `CLAUDE.md`.
The design and the to-do list are in `docs/UXCBASIC.PLAN.md`: the order of work is section 4,
and the to-do items are section 5. The old notes are in `docs/HISTORY.md`; do not read it unless
you need to trace a past decision.

## pyuxc

The GPC UXC is frozen from 2026-10-14: no speed work, no new features. `pyuxc/` holds its
Python port. `pyuxc/README.md` has the plan, the port steps and the status.
Port steps 1 to 12 are done: every corpus source with a GPC golden matches it, and `tests.py`
compiles with pyuxc. Part 2 is done: UXDOS16's `tools/uxb.py` compiles with pyuxc too. Part 3
is next: data in banked RAM, code in banked RAM, and string arrays.
The stock ROM is not supported (user, 2026-10-15). pyuxc compiles for UXDOS16 and has no
`--target`. `compare.py` alone compiles for stock, against the GPC UXC's golden output, until the
port ends. `tpl/MKTPL.PY` builds both tables; the UXDOS16 one is `tpl/UXDOS/UXC.TPL.BIN`, from
`tpl/UXDOS/SYS.ASM` and `tpl/UXDOS/R-FILE.ASM`.
`tests.py` runs on the UXDOS16 ROM (`C:\dev\CmdrX16\UXDOS16\build\UXDOS16.ROM`), whose prompt
is `>>`: 175 tests. The last full run, after POS(2) and POS(3) (2026-10-17), was 174 ok in
43 s. `compare.py`: 566 MATCH, 5 RESULT and 31 NO GOLDEN of 602, 1.7 s; the two new RESULTs,
`EXERRPOS` and `EXERRPOSVAR`, are expected, since POS takes 0 to 3 now;
a NO GOLDEN source is newer than the GPC reference. `FILEINERR` read handle 0, which is standard input on
UXDOS16; its source moved to `pyuxc/cases`, and `tests/FILEINCLOSED` reads handle 9.
`tests/CHAIN.NEXT` is gone.
`ASM1`, `ASM2`, `DIMAT`, `SYS1`, `EXPR2`, `POINTER` and `RECORD2` called the KERNAL's `$FFD2` or
wrote UXDOS16's sector buffer or kernel variables. They moved to `pyuxc/cases`, where they match
the GPC output. Their copies in `tests/` are `ASMBYTES`, `ASMOPS`, `DIMADDR`, `SYSREGS`,
`EXPRPEEK`, `POINTERS` and `RECSTR`: they call `con_out` at `$03B8`, and use `$9E00–$9E11` in
place of `$0400–$0411` and `$0600–$0601`. `ZP_MODE` (`$27`) is in the stock table only.
`END [code]` is done (plan section 5): help topic `END`, test `ERRENDSTR`.
`LEFT$` and `RIGHT$` are pyuxc built-ins (2026-10-16): `sg_left_right` in `uxc_str.py`,
records `T_LEFT`, `T_RIGHT`, `R_LEFT` (17 bytes) and `R_RIGHT` (38 bytes), which jump into
`R_MID` at `pop` and `take`. They are reserved words. `lib/STRINGS.UXI` keeps only their `BIND`
lines; its asm FUNCTIONs are gone. `STRLR` and `STRNS` pass. `compare.py` gives RESULT for both
against the GPC golden, as expected: the GPC UXC has no such built-ins.
`SELECT CASE` is done, in pyuxc only (2026-10-16): `pyuxc/uxc_select.py` has the syntax and the
code layout. A CASE holds values, ranges (`low TO high`) and `IS` compares; `CASE ELSE` and
`END SELECT` or `ENDSELECT` close it. It compiles to the same code as the `IF`/`ELSEIF` chain,
with no new template. A variable selector is read at each test; any other number goes into a
hidden variable; any other string is an error. `K_NS_SEL` is 4, and DO, FOR and REPEAT moved to
5, 6 and 7. SELECT and ENDSELECT are reserved. Tests: SELECT, ERRSELSTR, ERRSELOPEN, ERRSELEND,
ERRSELELSE. Help topic `SELECT CASE` (`MKHELP.PY` 0.13 s, 34 topics) and plan section 1 have it.
No jump out (2026-10-16): a body before `ELSEIF`, `ELSE` or a `CASE` that ends in `RETURN`,
`GOTO`, `EXIT`, `CONTINUE` or `END` has no `JMP` to the end, for the UXDOS16 table only. The
pyuxc README, "Differences from GPC UXC", has the rule. Test `JUMPOUT` (0.7 s): 644 to 620
bytes; UXDOS16's shell 15291 to 15285. Every other test PRG is unchanged; `compare.py` 571
MATCH, 16 NO GOLDEN, 1.4 s. Help topics `IF` and `SELECT CASE` (`MKHELP.PY` 0.12 s, 34
topics) and plan section 1, under IF, have it.
Removing unused code, pyuxc only (user, 2026-10-16). The user's choices:
- Remove the `SUB`s and `FUNCTION`s nothing reaches, and unused variables. Both on by default,
  each with a command-line switch to turn it off.
- Keep syntax: `#KEEP NAME[, NAME]` anywhere, and a `#KEEP` ... `#ENDKEEP` region. `#KEEP ALL`
  keeps every routine.
- Report: a field on the result line. A command-line switch writes a list file of what was
  removed.
- Steps: S1 dead SUBs at link (done); S2 `#KEEP NAME`, `#KEEP ALL`, `#KEEP`/`#ENDKEEP`; S3
  unused variables and `--keep-vars`; S4 the list-file switch; S5 docs (help topic, plan section
  5 "Removing unused code", README "Differences from GPC UXC", `pyuxc.py` usage).

S1 (2026-10-16): `pyuxc/uxc_dead.py`, `dd_strip`, first in `lk_link`.
- A SUB is live when a K_SEC_LABEL fixup of the main program, or of a live SUB, names it, or
  names a label it owns. Flag `K_SY_LIVE` (128).
- A dead SUB's range is its around-`JMP` (3 bytes before its value) to `K_SY_END`, the word
  `sb_endsub` stores at offset 28 (it overlays `K_SY_LEVEL`/`K_SY_TEMPS`, which `sb_pools`
  writes later). Every code reference is a fixup or a LABEL/SUB value, so the cut shifts
  only those (`dd_shift`, a binary search over `dd_to`/`dd_sum`, `K_DD_MAX` 512 ranges).
- Trap: a fixup is dropped by its place, not its owner. `sb_call` stores the arguments with the
  called SUB as owner, in the caller's code (`uxc_sub.py` 480-509).
- Dead SUBs, and the call records and temps they own, become `K_SK_DEAD` (12), so `sb_pools`
  skips them. The runtime list is counted again from the fixups kept, in their order.
- Result line: `OK,NAME.PRG,bytes,REMOVED n SUBS m BYTES`; m is the code cut plus the runtime
  records dropped. `compile_file(..., keep_subs=True)` and `pyuxc.py --keep-subs` keep them;
  `compare.py` passes it, so 569 MATCH, STRLR and STRNS RESULT as before, 17 NO GOLDEN.
- String literals only dead SUBs use stay in the PRG.
- Test `DEADSUB` (0.5 s): 652 to 555 bytes. SUB1, SUBFWD, SUBNEST, FUNC1, LOCALPOOL,
  INCLUDE, STRNS, STRLR, JUMPOUT and SELECT pass, 0.5 s each.
- UXDOS16: `EXIST.CBI` 3239 to 1594 bytes (28 SUBs), `CMDSHELL.COM` 17936 to 17708. Its
  goldens FILES, DIRS and DISK changed by those sizes; its shell tests pass.

S2 (2026-10-16): `#KEEP`, in `uxc_dead.py` (`dd_keep_line`, `dd_keep_name`, `dd_open`).
- `sm_line` sends a line that starts with `#` to `dd_keep_line`, outside ASM, ENUM and TYPE
  blocks. Pass 1 skips such lines.
- `#KEEP NAME[, NAME]` finds each name with `nm_find`, as CALL does, and sets `K_SY_LIVE` at
  once. `dd_live` no longer clears `K_SY_LIVE`; it seeds from the SUBs kept. `sb_sub` keeps the
  flag, and sets it inside a region.
- `#KEEP ALL` sets `g.dd_keep_subs`. `#KEEP` alone opens a region, `#ENDKEEP` closes it;
  `g.dd_region_line` is the open line, 0 when none.
- Errors: `#ENDKEEP WITHOUT #KEEP`, `#KEEP INSIDE #KEEP`, `#KEEP WITHOUT #ENDKEEP` (at the
  `#KEEP` line, from `dd_open` in `finish`), `NOT A SUB: X`, `UNDECLARED NAME X`, and SYNTAX
  ERROR for another word after `#`, a trailing comma, or a word after `#KEEP ALL`.
- Tests: `KEEPSUB` (0.7 s; 376 bytes, REMOVED 1 SUBS 14 BYTES, 390 with `--keep-subs`) and
  `KEEPOPEN` (0.0 s). DEADSUB and SUB1 pass, 0.5 s each; DEADSUB still 555 bytes.

S3 (2026-10-16): unused global variables, in `uxc_dead.py` (`dv_log`, `dv_strip`).
- `sb_place_variable` and `sb_place_block` call `dv_log` for a global: the start of each
  variable in the variables (`g.dv_s` 0) or the array space (1), up to `K_DV_MAX` 1024 each.
  A variable of 0 bytes is not logged. A full log keeps every variable.
- `dv_strip` runs in `lk_link` after `dd_strip`, so the fixups of dead SUBs are gone, and
  before `T_ZERO`, `sg_maxes` and `sb_pools`, so their fixups do not keep a variable.
- A variable is used when a K_SEC_VAR or K_SEC_BSS fixup below `K_FRAME_BASE` falls in its
  range (binary search, `dv_find`). The rest are cut: fixup values and VAR/ARRAY record
  values move down by `g.dv_cut`; the records cut become `K_SK_DEAD`; `vr_n` and `bs_n`
  shrink. Locals, temps and `DIM ... AT` are never logged.
- Result line: `,REMOVED <n> VARS <m> BYTES`; n counts named records, m the bytes of both
  spaces. `--keep-vars` (`compile_file(keep_vars=True)`) turns it off; `compare.py` sets it.
- Not done: a variable only written is kept; locals in a live SUB are kept.
- Test `DEADVAR` (0.6 s): 469 to 461 bytes, 5 VARS 78 BYTES. DEADSUB and RECORD1 pass, 0.5 s
  each. `compare.py` 569 MATCH, STRLR and STRNS RESULT as before, 21 NO GOLDEN, 1.6 s.
- UXDOS16, not rebuilt: `CMDSHELL.COM` 17708 to 17696, `EXIST.CBI` 1594 to 1578. Its goldens
  FILES, DIRS and DISK need `--update` at the next build.
`T_TOP`, record 252 of both tables, stores the page of the BSS end in UXDOS16's `PSP_TOP`
(`$0702`), so `exec` saves the program's RAM only up to it. `lk_link` emits it after `sb_pools`,
for UXDOS16 only; a program grows 5 bytes, 6 when it had no other startup work. The help topic
Targets has it. The GPC compiler's `TPL.COUNT` check fails against the new table.
`K_SYM_BANKS` is 4 and `K_SY_MAX` 1008 in `pyuxc/uxc_defs.py`, for UXDOS16's shell.
A variable that GPC reads before it sets it needs a 0 default in `uxc_state.dim()`; a
`CRASH` with `AttributeError` in `compare.py` is that.
String `CONST`s, pyuxc only (user, 2026-10-17; plan section 5, step 1 of 3):
- `CONST E$ = CHR$(27) + "[7m"`, or `AS STRING`. `nm_const_string` in `uxc_name.py` folds the
  value: string literals, `CHR$` of a constant expression (`nm_const_chr`, the low byte) and
  string CONSTs, joined by `+`.
- The texts are in `g.cn_bank`, a bank of its own, up to `K_CN_SIZE` 2,048 bytes; `g.cn_n` is
  the end. The record is `K_SK_CONST` with `K_TY_STR`: offset in `sy_val`, length in `sy_cnt`.
- `ex_operand` pushes a use as a literal (`nm_const_get`, then `sg_push_literal`).
- Errors: TYPE MISMATCH (a number, a number CONST), VALUE NOT A CONSTANT (a variable, a
  function, CHR$ of a variable), `TOO BIG FOR A STRING: B$`, `TOO MANY CONST STRINGS`, and
  `A CONST IS A NUMBER OR A STRING` for a record type. Each was checked by hand.
- Tests: `CONSTSTR` (0.5 s; literals, CHR$, joins, AS STRING, NAMESPACE CONS, a SUB, BIND,
  LEN, a compare) and `ERRCONSTSTR` (0.0 s). CONST, ENUM, NS1, NS2 pass, 0.5 s each.
- `compare.py`: `pyuxc/cases/EXERRCONSTSTR` (`CONST A$ = 1`) gives RESULT, as expected: GPC says
  A CONST IS A NUMBER, pyuxc TYPE MISMATCH.
Line continuation, pyuxc only (user, 2026-10-17; plan section 5, step 2 of 3):
- A ` _` at the end of a line joins the next line. `lx_read` in `uxc_lex.py` calls
  `lx_join_lines` after the CR is cut and before `lx_include_find`, so the lexer and `sg_scan`
  see one line.
- `lx_join_find` finds the `_`: the last character that is not a space or a tab, with a space or
  a tab before it, outside a string, a `'` comment, a `REM` (`lx_join_rem`) and a whole-line
  comment. The joined line is the text before the `_`, then the next line.
- `lx_no` keeps the first line's number; `g.lx_join_skip` counts the lines joined, and the next
  `lx_read` adds it. `lx_include_start` saves `lx_no + lx_join_skip`, the lines read.
- Errors: `NO LINE AFTER _`, and `LINE TOO LONG` for a joined line over 254 characters.
- Tests: `LINEJOIN` (0.5 s) and `ERRLINEJOIN` (0.0 s); INCLUDE and ERRINCLUDE pass. Probes
  checked by hand: the last line, with and without LF; the line after two joins; a joined
  `#INCLUDE`; CR and CR LF sources; `A_`; `REMARK`.
- `compare.py`: 568 MATCH, 3 RESULT, 26 NO GOLDEN of 597, no change.
Escaped strings, pyuxc only (user, 2026-10-17; plan section 5, step 3 of 3):
- `lx_next` sends `!"` to `lx_escaped`; `lx_escape` reads one escape after a `\`, and
  `lx_escape_digits` reads its digits. A string with no `!` goes to `lx_string`, unchanged.
- `lx_join_find` notes a `"` opened after `!` in `g.lx_join_escaped`; in such a string a `\`
  skips the next character, so `\"` does not close it.
- Errors: `BAD ESCAPE`, `ESCAPE OUT OF RANGE`, and `MISSING QUOTE` for a `\` at the end of the
  line.
- Tests: `ESCAPES` (0.6 s) and `ERRESCAPE` (0.0 s); LINEJOIN and CONSTSTR pass. Probes checked
  by hand: `\256`, `\&o400`, `\&x1`, `\&hG`, `\&o8`, `\&` at the end, `!"AB\"`, a `\` at the
  end, `! "A"` (SYNTAX ERROR), and a joined `!"\" _"` line.
- `compare.py`: 568 MATCH, 3 RESULT, 28 NO GOLDEN of 599, no change.
- Trap: the Write tool turns `\u0041` into `A`. Write a source holding `\u` from a Python
  script with `chr(92)`.
The help for the three is done (2026-10-17): topic CONST has a section String CONSTs, and the
topics Line continuation and Escaped strings are new. `MKHELP.PY` 0.11 s, 36 topics. The copies
in `disk/HELP-TXT/` and `build/HELP-TXT/` are the old ones until the next `build.py UXC.HELP`.
Unused string literals, pyuxc only (2026-10-17):
- `ds_strip` in `uxc_dead.py` runs in `lk_link` after `dv_strip`. It indexes the starts of
  the literals in `g.sp_bank` (`g.ds_at`, up to `K_DS_MAX` 4096), marks each one a
  `K_SEC_STR` fixup names (binary search, `ds_find`), moves those fixups down by `g.ds_cut`,
  and copies the literals used down over the rest (`ds_pool`); `sp_n` shrinks.
- A literal of a dead SUB, or of a string CONST used only in one, is left out; a literal
  shared with live code is kept. A CONST nothing uses never enters the pool.
- Result line: `,REMOVED <n> STRINGS <m> BYTES`. `--keep-vars` keeps every literal too, so
  `compare.py` is unchanged: 566 MATCH, 5 RESULT, 31 NO GOLDEN of 602, 1.8 s.
- Test `DEADSTR` (0.6 s): 277 to 237 bytes, 3 STRINGS 40 BYTES. DEADVAR, DEADSUB and
  CONSTSTR pass, 0.5 s each.
`python pyuxc/compare.py` shows how many corpus sources match the GPC output. A new source in
`pyuxc/cases/` gets its reference from `python pyuxc/golden.py NAME`, about 2 s a source.

## Where the work stands

Steps 4.1 to 4.7b are done: expressions, control flow, `SUB`, arrays, `GETKEY()`,
`ERRORS ON`/`OFF`, namespaces, `BIND`, CP437 on exit, strings, `INPUT`/`LINPUT`, the file
commands (4.5a to 4.5c), `ASM` and `SYS` (4.6), BYTE by default (4.7a), `DIM ... AT`
(4.7b) and pointers by name (4.7c: `AddrOf`, `ContentsAt`, `ContentsAtW`). Step 4.5d, `DIR`,
is put off by the user: it may become code in a `DIR` namespace.

Plan section 4 item 5, the UXCEDIT compile relay, is done: the user disk (5a), UXC chains
(5b), F5 in the editor (5c) and the editor start with the result in a message box (5d).

A `SUB` has no value. A `FUNCTION` has one: `FUNCTION name[mark](params) [AS type]` ...
`ENDFUNCTION` or `END FUNCTION`, a BYTE with no mark and no AS. `FUNCT` and `ENDFUNCT` are
built-in BINDs, put in the alias table by SB.SCAN. The end must match the start. A `SUB` with a
type stops the compile with `SUB WITH A TYPE: USE FUNCTION`. Every value `SUB` in `tests/`
and `lib/` is now a `FUNCTION`. Tests FUNC1, ERRSUBTYPE, ERRFUNCEND, ERRSUBENDF and
ERRFUNCOPEN pass, and 33 tests of SUBs, namespaces, BIND, ENUM and the includes pass.
UXC-NAME.BL is in its own region, bank 25 (K.BANK.NAME), because SUB and NAME together
passed 8K. STRLR and STRNS take 9-10 s: compiling the user's InStrRev in `lib/STRINGS.UXI`
costs 3 s (STRNS is 5.9 s without it). The user's notes and stubs in `lib/STRINGS.UXI` are
commented out with `//`; the notes ask for SELECT CASE, `ON CASE`, `_` line continuation, a
SYS2, `conv.UXI` (CBYTE, CWORD), a TEXT_GUI namespace and timers. They are not yet in the plan.

Shared temps and locals are done: plan section 5, "Shared temps and locals". The string
temps and the locals of all `SUB`s of one call-graph level share one pool. A local does not
keep its value between calls, and only its `SUB` can name it. Tests LOCALPOOL (4.3 s),
ERRSUBLOCAL (1.5 s) and ERRSUBLOCALS (1.3 s) pass. NS2 lost its SHOW.N/SHOW.SEEN print. All
`SUB`, string, namespace, array, FOR, `INPUT` and file tests pass, 1.3–6.7 s: STRRET 6.7 s,
FLOWFOR 6.1 s and FILER 6.3 s on a loaded machine.

`#INCLUDE "FILE"` is done: LX.INCLUDE.FIND, LX.INCLUDE.START and LX.INCLUDE.END in
src/UXC-LEX.BL. One level only. At the end of the included file the source is opened again
and read up to the line after the `#INCLUDE`.
An include file has the extension `.UXI`. `build.py` copies `lib/` to `disk/`, and `tests.py` copies `lib/*.UXI` and `tests/*.UXI` to
`build/`. Tests INCLUDE (5.8 s) and ERRINCLUDE (2.8 s) pass. The help has a topic "Including
files"; UXC.HELP is rebuilt (2026-10-11, 10070 bytes, 55 s).

`INSTR(S$, F$[, START])` is a built-in: SG.INSTR in src/UXC-STR.BL, T_INSTR and R_INSTR in
the templates. Without a start it searches from 1. SG.INSTR and SG.MID share SG.LAST.WORD,
the optional last argument. R_INSTR is 123 bytes and takes 25 cycles a position tried, when
the first character differs. `INSTR` is a reserved word. Tests INSTR (3.5 s, was 9.0 s as a
`SUB`) and STR2 (4.9 s) pass. The help topic Strings lists `INSTR`; UXC.HELP is rebuilt.

BIND to a word of the language is done. `BIND name [=] word`, where the word is in the list of
NM.WORD (src/UXC-NAME.BL), makes an alias: `BIND INSTR INSTR` in `NAMESPACE STR` makes
`STR.INSTR`, and `BIND FIND = INSTR` outside a namespace makes `FIND`. The `=` is optional in
every BIND. NM.BIND.SCAN adds each alias in the first pass, to NM.ALIAS.NAME$() and
NM.ALIAS.TARGET$() (K.ALIASES = 64), so an alias works on every line, before its `#INCLUDE`
too. LX.WORD.END in src/UXC-LEX.BL reads an alias as its word. NM.BIND passes over a BIND to a
word. A BIND to a SUB declared above it, outside a SUB body, is made in the first pass by
NM.BIND.SCAN.SUB, with the flag K.SY.SCANNED; NM.BIND.SCANNED clears the flag in the second
pass, so a second BIND of the name is a duplicate. NM.FIND.QUIET makes NM.FIND give SY.R = 0
for a name not found. SB.SCAN.IN.SUB is set from SUB to ENDSUB or END SUB. A BIND to a
variable, an array or a namespace is still made in the second pass.
NM.RESERVED calls NM.WORD. An alias in a namespace is found only by its qualified name.
`lib/STRINGS.UXI` is `NAMESPACE STR` with one `BIND` for each string function. Test STRNS
(4.1 s) passes, with the `#INCLUDE` at the end. UXC.PRG is 7907 bytes, built in 61 s.

`LEFT$(S$, N)` and `RIGHT$(S$, N)` are global SUBs in `lib/STRINGS.UXI`, with ASM bodies,
before `NAMESPACE STR`. `BIND LEFT$ LEFT$` and `BIND RIGHT$ RIGHT$` in it make `STR.LEFT$`
and `STR.RIGHT$`.
Each copies into a local `R$ * 255` and returns it. `P% = @S$` takes the block address,
because `@S$` of a STRING parameter is not a constant and ASM refuses it. The ASM uses r0
($02-$03) as the pointer, and RIGHT$ uses $04. Test STRLR, with the `#INCLUDE` at the end,
passes in 6.5 s, over the 5 s limit, and was not rerun. UXC.PRG is 7907 bytes, built in 62 s.

Mnemonics in `ASM` are done: plan section 5, "Mnemonics in `ASM`". src/UXC-ASM.BL moved to
its own region, `K.BANK.ASM` (24). The opcode table is six string literals in AS.TABLE.CHUNK,
written by a generator script: `/`, the mnemonic, then a mode letter and two hex digits per
opcode. The mode letters are in the header comment of UXC-ASM.BL. Tests ASM2 (3.7 s) and
ERRASMLABEL (1.5 s) pass, and ASM1, ERRASMITEM, ERRASMOPEN and SYS1 still pass. The help
topic ASM has the instructions; UXC.HELP is rebuilt.

- Build: about 31 s on a quiet machine, 57–89 s loaded; 83 s for `#INCLUDE`.
  The last build: 89–95 s loaded. UXC.PRG 8197 bytes, UXC.HELP.PRG 10070 bytes (60 s, built
  before the LONG help; rebuild it). Templates: 250 records, 6645 bytes.
  `MKTPL.PY --test` passes.
- Suite: 155 tests. The last full run, on 2026-10-14 with pyuxc: 155 tests, 0 failed, 69 s.
  Steps since the last full suite: 5 (SELECT CASE, LEFT$ and RIGHT$, dead SUBs S1, S2, S3). The suite runs every 10th step.
- `POS(0)` gives the cursor column and `POS(1)` the row, as a BYTE, by T_POSCOL and T_POSROW
  inline. `POS(2)` gives the screen's rows and `POS(3)` its columns, by T_POSROWS and T_POSCOLS,
  from r0L and r0H of UXDOS16's `con_cursor`. `POS(0) = v` and `POS(1) = v` are SM.POS, by
  R_POSSETCOL and R_POSSETROW. pyuxc's `ex_pos_axis(last, message)` takes a number from 0 to
  last: 3 for a read, 1 for a write. Test `POSSCREEN`.
- Templates: 259 records. An F_REC fixup holds a record id in one byte, so a record that `#rec`
  names needs an id below 256. T_TOP is 256; T_POSROWS and T_POSCOLS, which no `#rec` names,
  follow it at the end of `tpl/UXC.TPL.ASM`.
  `CONST NAME = value` is NM.CONST in `src/UXC-NAME.BL`, a record of kind K.SK.CONST that
  EX.OPERAND folds as a number. It is in the SUB bank because the STMT and FLOW bank passed
  8K. NM.AS.TYPE in `src/UXC-NAME.BL` reads `AS type` for DIM and CONST. Test CONST passes in
  3.7 s; ERRCONSTBIG is written and not run.
  `ENUM name` ... `END ENUM` is NM.ENUM in `src/UXC-NAME.BL`, a record of kind K.SK.ENUM. Its
  members are K.SK.CONST records owned by it, the records after it. NM.ENUM.RECORD is set from
  ENUM to END ENUM, and SM.LINE then sends each line to NM.ENUM.MEMBERS. A member past 255
  makes the ENUM and every member WORD at END ENUM. Test ENUM passes in 3.5 s; ERRENUMOPEN is
  written and not run. UXC.PRG is 7910 bytes, built in 64 s. The help topic is in
  `help/UXC-HELP.md`; UXC.HELP is rebuilt. Next in the plan: `AS` enum, then bare members.
  `lib/CONSOLE.UXI` and `lib/DISK_FILEIO.UXI` are the user's work in progress; review them
  only when asked.
  Until 2026-10-13 the user is short of tokens: run only the new tests
  and one or two old ones, and the user runs the full suite.
- A single test takes up to 1.1 s with pyuxc. An error test does not start the emulator.
- The help topics for every done step are written. All but "Including files" and the ASM
  instructions are built:
  UXC.HELP.PRG 10,070 bytes,
  27 topics, 58 s.

**Next: record types** (user, 2026-10-13). Plan section 5 "Record types" has the design and a
list of 7 steps. Step 1 is done:

- `TY.SIZE` (`src/UXC-SYM.BL`, low code) gives TY.BYTES for TY.CODE: 1 for a BYTE, 2 for
  anything else. SM.DIM, SM.LET.ELEMENT, EX.INDEX and SB.PARAMETER call it. EX.LOAD and
  EX.SPILL test `= K.TY.WORD OR = K.TY.STR` for a wide value.
- Trap: an expression entry of type 0 is a constant that fits a BYTE. A test of
  `<> K.TY.BYTE` makes it wide; RUNDIV0 caught that.

Step 2 is done:

- `src/UXC-RECORD.BL` is bank 26 (`K.BANK.RECORD`), prefix `RD.`. RD.TYPE makes a K.SK.TYPE
  record: type K.TY.RECORD (16) plus the TYPE's number, value its size. RD.FIELDS makes one
  K.SK.FIELD record a line, owned by the TYPE: type, offset as value, string max as count.
  RD.TYPE.RECORD is set from TYPE to END TYPE, and SM.LINE sends each line to RD.FIELDS.
- RD.LEN, called from SG.FUNCTION, makes `LEN(typename)` a constant. Any other argument goes
  back to the ( and parses as before.
- NM.DECLARATION (`src/UXC-NAME.BL`) now dispatches CONST, NAMESPACE, ENDNAMESPACE, BIND,
  ENUM and TYPE, with one GOSUB line in SM.STMT, to make room in bank 21.
- `TYPE` and `ENDTYPE` are reserved words.
- Tests TYPEDECL (4.5 s), ERRTYPEOPEN, ERRTYPEEND, ERRTYPEBIG, ERRTYPEFIELD, ERRTYPEDUP and
  ERRTYPESUB (1.5–2.0 s) pass. ENUM, CONST, NS1, NS2, ERRBINDMARK and STR1 still pass.
- For step 6: TYPEs are declared in the second pass, and the first pass reads SUB headers.
  A record parameter needs its TYPE in the first pass.

Step 3 is done:

- `DIM R AS ITEM [AT addr]` is RD.DIM, from SM.DIM. NM.AS.TYPE calls RD.AS.TYPE for a name
  that is no built-in type. A record variable is a K.SK.VAR of the TYPE's type, in the block
  space (flag K.SY.BLOCK, K.SEC.BSS) or at a fixed address (NM.AT, K.SY.FIXED). Its TYPE's
  record is at +30, K.SY.RECORD.TYPE.
- `R.FIELD`: NM.FIND.TARGET calls RD.MEMBER for the part after a record variable. It gives
  SY.* as a variable at the record's value plus the field's offset, with the record's flags
  and K.SY.MEMBER. SY.R stays the record variable's. Every reader then works unchanged.
- RD.SECTION gives the section from the flags. EX.OPERAND, EX.AT.NAME, SM.LET, CT.FOR and
  SG.INPUT.NEXT call it; RD.SECTION.VALUE also stops on a whole record, RD.SECTION.COUNTER
  also on a field.
- `A = B` is RD.LET, from SM.LET: T_RCOPY in `tpl/T-RECORD.ASM`, 11 bytes, the user approved
  the asm. `LEN(R)` is a constant, in RD.LEN.
- Errors: "A RECORD IS NOT A VALUE: R", "NOT A FIELD: R.X", "TYPE MISMATCH" for a copy of
  another TYPE, "A FIELD IS NO FOR COUNTER: R.X", "BIND OF A FIELD", and for later steps
  "NOT YET: A STRING FIELD" and "NOT YET: AN ARRAY OF RECORDS".
- Tests RECORD1 (7.8 s loaded), ERRRECVALUE, ERRRECFIELD, ERRRECCOPY and ERRRECFOR (2.6–3.0 s)
  pass. TYPEDECL, DIMAT, POINTER, FLOWFOR, INPUT1, INPUT2, CONST, NS1, ERRBINDMARK and ASM1
  still pass, each 1.4–2 times its quiet time on the loaded machine.
- `NEXT R.X` is not caught: CT.NEXT compares only the value.

Step 4 is done:

- A string field is a block, as a string variable is: RD.MEMBER gives its max as SY.CNT.
- RD.SECTION gives K.SEC.BSS for any string block, K.SEC.CONST for a fixed address.
  SG.LET, SG.LET.CLEAR, SG.IS.DESTINATION, SG.AT, SG.INPUT.BLOCK and EX.OPERAND take the
  section from it, so a field in a record at a fixed address works too.
- The max: RD.MAXES, from SG.MAXES at startup, for a record of the main program. RD.DIM sets
  the max and a 0 length each time the DIM of a local record runs. Both walk the fields after
  the TYPE's record. LK.LINK now calls SG.MAXES when the array space is empty too.
- A record at a fixed address gets no max (the user's choice to confirm): the memory is not
  the program's, as with `DIM ... AT` of a number. The program sets the max byte itself.
- `A$ = A$ + x` appending: SG.SCAN counts the last part of a name, so `R.NICK = R.NICK +
  S.NICK` counts NICK twice and copies through a temp. That is safe, only slower.
- Test RECORD2 (5.5 s): assign and cut at the max, append, copy, compare, MID$, INSTR, ASC,
  VAL, `@`, a fixed address, INPUT and LINPUT, a STRING parameter, a local record. RECORD1,
  STR1, STR2, STR3, STRRET, STRSUB, INPUT1, INPUT2 and POINTER still pass (3.3–5.7 s; the
  string tests ran 6–17 s in the last full suite).

Step 5 is done:

- `DIM STOCK(n) AS ITEM` is RD.DIM.ARRAY: a K.SK.ARRAY record of the TYPE's type, with the
  TYPE's record at K.SY.RECORD.TYPE, in the block space or a SUB's frame. `AT` is refused,
  as for any array.
- `STOCK(i).field` in an expression: EX.INDEX calls RD.INDEX. Statement `STOCK(i).field = x`
  and `STOCK(i) = record`: SM.BRACKET calls RD.LET.ELEMENT. `@STOCK`, `@STOCK(i)` and
  `@STOCK(i).field`: EX.AT.NAME calls RD.AT.ELEMENT, which parses the index nested and keeps
  the array's record in EX.OA() under a ( of its own. `LEN(STOCK(i))` is the TYPE's size,
  from RD.SKIP.INDEX, with no code for the index.
- RD.ELEMENT: a constant index gives a fixed address. A variable index is T_RELEM: a JSR
  to R_RELEM, then the count (0 under ERRORS OFF), the size and the base plus the field
  offset, 8 bytes in all. R_RELEM checks the index, multiplies, adds and returns past the
  data. On a bad index it pushes the return address back, so R_ERROR reports the JSR.
- A string field at a variable index is read and written through a hidden WORD, `%E n`,
  numbered with the %P words by SG.POINTERS. SG.POINTER.WORD (UXC-STR.BL) makes the word
  and stores A/Y into it, for both.
- A copy: RD.LET and RD.LET.ELEMENT push the destination's address as an entry, and
  RD.LET.SOURCE reads the source (a record or an element). Two fixed addresses use T_RCOPY,
  any other T_RCOPY_P with R_RCOPY. The user approved the asm.
- The maxes: RD.STRING.MAX emits T_RMAX with R_RMAX for an array, at startup or at each
  DIM in a SUB. It sets the max and a 0 length in every element.
- INPUT into an element is not supported, as for any array (SM.VAR).
- Tests: RECORD3 (8.7 s; it compiles for 7 s, so its time scales with its size),
  RECORD4 (5.5 s), ERRRECINDEX and ERRRECELEM (1.5–1.8 s) pass. RECORD1, RECORD2, ERRRECCOPY,
  ARRAY1, ARRAY2, STRRET, STR1, POINTER, ERRADDROF and ERRSUBSCR still pass (1.5–6.3 s; the
  machine was loaded, and the build took 84 s).
- R_RELEM (97 bytes) and the `#dw`/`#db` data macros in `tpl/MACROS.ASM`: the user approved
  the asm. RUNRECSUB tests the range check at run time, with ERRORS OFF and ON. RECORD3,
  RECORD4, RUNRECSUB and RUNSUB pass (3.5–9.0 s). RECORD3's PRG is 2551 bytes.

Record step 6, record parameters (`SUB SHOW(P AS ITEM)`), waits for the types work below.
The TYPE must be known in the first pass (see the step 2 notes).

## Types (user, 2026-10-13)

The user's decisions:

- Numbers have no marks. `$` stays the string mark, and strings are unchanged.
- A number needs `AS`. `DIM B` stops the compile with `MISSING AS: B`; so do a CONST, a
  parameter and a FUNCTION result with no `AS` (a `$` FUNCTION needs none).
- The types: `BYTE` −128..127 and `UBYTE` 0..255; `WORD` or `INT` −32768..32767, and `UWORD`
  or `UINT` 0..65535; `LONG` signed 32 bits and `ULONG` unsigned 32 bits.
- All the steps in a row. The user approved the asm for the signed runtime and for LONG.
- The fixup table is raised for UXDOS16's COMMAND: K.FX.MAX 4096 in K.FIX.BANKS 4 (was
  2048 in 2). Done, no test of its own.

**T1, done:** the `%` mark is gone (LX.WORD.END stops with `% IS NOT A MARK: USE AS UWORD`).
NM.TYPE.NAME (UXC-NAME.BL) reads a type word for NM.AS.TYPE, SB.AS and the record fields:
UBYTE gives K.TY.BYTE, UWORD and UINT give K.TY.WORD, and BYTE, WORD, INT, LONG and ULONG stop
with `NOT YET: name`. ER.MISSING.AS is in UXC.BASL. UBYTE, UWORD, INT, UINT, LONG and ULONG
are reserved. Every test, `lib/`, `examples/` and `samples/` source was converted by a script
(`X%` to `X` with `AS UWORD`, a bare number gets `AS UBYTE`, `AS BYTE`/`AS WORD` become
`AS UBYTE`/`AS UWORD`). New tests ERRPERCENT, ERRNOAS and ERRNOASPARAM. The help and plan
section 1 are rewritten (plan 4.9). In the compiler K.TY.BYTE and K.TY.WORD still mean the
unsigned types.

**T2, done: BYTE and WORD/INT, signed.** As built:

- NM.TYPE.NAME gives NM.TYPE.SIGNED: BYTE, WORD and INT are signed, LONG and ULONG stop with
  `NOT YET`. The type code is still the width. K.SY.SIGNED (64) in SY.FLAGS marks a signed
  variable, array, field, parameter and FUNCTION result, and a CONST below 0. Set in SM.DIM,
  NM.AT, NM.CONST, SB.PARAMETER, SB.HEADER.CLOSE (SB.AS gives SB.SIGNED), RD.FIELDS;
  RD.MEMBER adds the field's flag; the SUB placing keeps it. SB.CALL.RESULT() holds the
  result type + 256 for a signed one, and SB.CALL gives SB.CALL.SIGNED.
- EX.VG%() beside EX.VT%(): 1 for a signed value. EX.PUSHV takes EX.SG and clears it;
  EX.SETC takes EX.CG and clears it. EX.RG is a binary result's sign. A constant is signed
  only when it is below 0: its EX.VV is the bits, and from 65408 up it is type 0 (fits a
  BYTE). PEEK, RD.ELEMENT and NOT give unsigned; EX.INDEX and RD.INDEX give the array's or
  field's sign.
- EX.LOAD widens a signed BYTE with T_SWIDEN (a MEM BYTE: T_LDB_V then T_SWIDEN). EX.SPILL
  pushes a signed BYTE as a WORD.
- EX.BINARY: EX.G = 1 when a side is signed (for a shift, the left side). EX.MIXED makes the
  width WORD for a signed side against an unsigned BYTE or a constant 128-255.
- Compares do not bias. The signed templates (T_SCMPB_LR/RL, T_SCMPW_LR/RL in T-EXPR,
  T_SCMPB_C/V, T_SCMPW_C/V in T-FLOW) end `bvs +`, `eor #$80`, `asl a`: C = signed >=, Z is
  not set, A is lost. `=` and `<>` use the unsigned ones. EX.COMPARE and EX.FAST.SIGNED pick
  them; EX.FAST.NEXT does the k + 1 for `>` and `<=` against a constant, signed.
- `/` and MOD signed: T_DIVS, T_MODS, R_DIVS (88 bytes; wraps R_DIVW). `>>` signed: T_SARB,
  T_SARW. PRINT: T_PRSWORD, R_PRSWORD (26 bytes, enters R_PRWORD at `sign`). `STR$`: T_SSTR,
  R_SSTR (32 bytes, enters R_STR at `sign`). R_VAL already read a `-`.
- Unary `-` gives a signed value: a BYTE for a signed BYTE, else a WORD. So `-M` of a UWORD
  7 prints -7 (EX.UNARY; EXPR1.OUT changed for it).
- Folding moved to src/UXC-FOLD.BL and FOR/NEXT to src/UXC-FOR.BL, both in the new region
  bank 27 (K.BANK.FOR). EX.BINARY reaches EX.FOLD and EX.FOLD.ADDRESS by GOSUB; SM.STMT
  reaches CT.FOR and CT.NEXT by GOSUB. A fold works on whole numbers (a signed constant is
  EX.VV - 65536): `/` rounds toward 0, `>>` floors.
- FOR: a signed counter is worked in the biased range (FR.BIAS, half the range added; its
  own inverse). FR.SG is kept in NS.VT%() as + 4. Compares through FR.CMPC and FR.CMPV pick
  the signed templates. FR.VAR clamps the bound on overflow with T_BVC. A signed STEP is at
  most half the range; a negative CONST STEP turns the direction. FR.LIMIT checks the
  constant limit: `TO VALUE OUT OF RANGE`.
- NM.CONST.RANGE: `TOO SMALL: name`, `TOO BIG FOR A BYTE: name`, `TOO BIG FOR A WORD: name`.
- Tests: SIGNED1 (6.1 s), SIGNFOR (5.1 s), SIGNSUB (4.7 s), SIGNIN (4.1 s, with SIGNIN.IN),
  ERRCONSTNEG (1.5 s), ERRFORRANGE (1.5 s). The old tests of the areas touched pass:
  expressions, FOR, IF, loops, CONST, SUBs, records, arrays, strings, files, INPUT.
- The help and plan section 5 were updated by the doc-style agent.

**T3, built, testing not finished: LONG and ULONG.** Plan section 5 step 3 has the design as
built. In short:
- K.TY.LONG 4, 4 bytes. A register LONG is A/Y plus ZP_HI ($2C); a stacked one has its high
  word in R_ESTKH,x (a 32-byte runtime record). EX.WD/EX.CW/EX.W = 2 mean LONG.
- src/UXC-LONG.BL in the new region bank 28 (K.BANK.LONG): EX.LONG.LOAD, .BITS, .CONST,
  .STACK (widens a narrower left side on the stack), .FAST (+/- a constant), .OPCODE,
  .COMPARE, .TEST. EX.PEEK and EX.INDEX moved to src/UXC-INDEX.BL in bank 27.
- A CONST keeps its high word at +28 (SY.CNT). EX.WHOLE, EX.TEXT (STR$ of a constant),
  EX.CONST.WORD (`NUMBER TOO BIG` where 16 bits are needed) are in UXC-FOLD.BL.
- Trap, found in T3: a GPC number is exact only below 4294967296; a sum or product past it
  wraps with no error. UXC-FOLD.BL and the lexer never form it (16-bit halves, bitwise long
  division, sign by compares, overflow checked before the digit is added).
- A LONG or ULONG FOR counter is an error, `A FOR COUNTER IS A BYTE OR A WORD` (user,
  2026-10-13: not needed). VAL is a WORD; `LVAL(s$)` is SG.LVAL, a ULONG by T_LVAL and R_LVAL.
  LVAL is in the SG lists and the NM.Q$ reserved names.
- Tests, new: LONG1, LONG2, LONG3, LONGIN (+ .IN), ERRLONGCONST, ERRLONGFOR. ERROVER uses
  4294967296. The lexer's overflow check compares with small limits (429496729, and 268435455
  or 2147483647 for $ and %), because `(4294967295 - d) / 10` in GPC did not stop 4294967296.
  Current build: UXC.PRG 8275 bytes, 88 s.
- T3-test-a done on the current build: ERROVER 1.7 s, LONG3 5.5, LONG1 5.3, LONG2 5.5,
  LONGIN 3.5, ERRLONGCONST 1.5, ERRLONGFOR 1.5, all ok. Over 5 s is the compile time of big
  programs, not a hang.
- Next, as small steps (user, 2026-10-13: a step fits one session; run only the tests named
  here; docs are their own step). Each step ends with a HANDOFF update and a /compact stop.
  - T3-test-b done: EXPR1 5.3 s, EXPR2 3.7, CONST 3.9, SIGNED1 6.1, FUNC1 5.0, RECORD3 9.2,
    STR2 5.4, ASM1 3.3, FLOWREP 5.1, all ok. SIGNED1 and RECORD3 match their baselines.
  - T3-help done: UXC.HELP.PRG 10,070 bytes, build 57 s, copied to disk/.
  - LVAL done: UXC.PRG 8275 bytes, build 91 s loaded. ERRLONGFOR 1.7 s (new message), LVAL1
    3.9 s (new), both ok.
  - LVAL-docs done: LVAL bullet after VAL in the Strings topic of help/UXC-HELP.md, and a line
    in Types. `NOT YET: A LONG COUNTER` is gone from the help and the plan. LVAL is in
    HELP.KW.FUNCTION. MKHELP 31 topics; UXC.HELP.PRG 10,070 bytes, build 58 s, copied to disk/.
  - The full suite is now every 10th step (CLAUDE.md). OC1 is done.
    Next: OC-docs, ON CASE in help/UXC-HELP.md and the plan, with the doc-style agent.
  - The user asked for `ON CASE` and for more low RAM in the compiler. Low RAM goes first.
    Analysis on 2026-10-13, nothing changed yet: low p-code is 7,751 bytes (LEX 2,065,
    UXC.BASL 1,930, CODE 1,577, LINK 919, SYM 796, BANKMGR 464). The DIMs take 7,702 bytes.
    `build/UXC.SRC.SYM` is not kept by the build; scratchpad scripts rebuilt the numbering.
    Bank free bytes: 20: 863, 21: 2019, 22: 3709, 23: 2357, 24: 4523, 25: 3606, 26: 4171,
    27: 3096, 28: 7272.
    - M1: done. UXC-LEX.BL is in the bank 28 region, after UXC-LONG.BL. UXC.PRG went from
      8,275 to 6,205 bytes; UXC.OVL from 43,027 to 45,075. Bank 28 has about 5,200 free.
      INCLUDE and ERRINCLUDE pass. Build 97 s on a loaded machine.
    - M2: done. RT.ON%, RT.L% and RT.ADDR are gone. The runtime record table is in bank
      RT.BANK, claimed by CB.INIT: K.RT.USED, K.RT.LIST and K.RT.ADDR in UXC-DEFS.BL, room
      for 1024 records. RT.USE leaves RT.BANK selected. UXC.PRG 6,205 to 6,351 bytes (the
      code grew 146; the DIM space shrank about 2,260). UXC.OVL 45,075. Build 97 s loaded.
      STR1 5.5 s and LONG2 6.1 s (5.5 before; the machine is loaded), both ok.
    - M3: done. New src/UXC-ONCE.BL in the bank 29 region (K.BANK.ONCE): UXC.START,
      UXC.FINISH, UI.READ, UI.RESULT, UI.CHAIN and ER.REPORT. ER.STOP stays low and is
      GOSUB ER.REPORT. UXC.START claims banks 20 to 29 with one FOR loop. UXC.PRG 6,351 to
      5,102 bytes; UXC.OVL 46,101; bank 29 uses about 1,000. Build 98 s loaded. STR1 5.5 s
      and ERRINCLUDE 2.0 s ok, so END from a banked GOSUB works. The chain to UI.NEXT$
      (POKE 1 and KBDBUF.PUT from bank 29) has no test; the editor's compile-and-run uses it.
    - M4: done. UXC-LINK.BL is in the bank 29 region, after UXC-ONCE.BL. CB.INIT moved to
      UXC-ONCE.BL. The BANK work stays low in UXC-CODE.BL as RT.CLEAR, RT.PLACE, RT.ADDRESS
      and SP.COPY. LK.FIX ends in `GOSUB CB.PUT` and `RETURN`. UXC.PRG 5,102 to 4,180 bytes;
      UXC.OVL 47,125. Build 96 s loaded. STR1 5.7 s, LOCALPOOL 5.5 s, FLOWGOTO 3.5 s, all ok.
    - M5: done. EM.FO%, EM.FK% and EM.FG% are gone; EM.FIX selects TP.BANK and reads fixup
      EM.J at EM.FA + EM.J * 3. EX.OA%, NS.NO%, NS.P%, AS.REFERENCE.NO% and the 8 SB.CALL.*
      and SB.SAVED.* arrays are `%`. NS.ST stays float: a WORD step reaches 65,535.
      SB.SAVED.HIDDEN stays float: it holds SB.PLACE, which reaches 65,535. A source past
      32,767 lines would overflow NS.NO% and AS.REFERENCE.NO%. UXC.PRG 4,180 to 4,099 bytes;
      UXC.OVL 47,125. Build 95 s loaded. FUNC1 4.3 s, ARRAY1 4.5 s, ASM2 3.9 s, FLOWFOR
      6.7 s (6.1 s before, loaded), FLOWLOOP 4.5 s, all ok.
    - Keep low: SY.*, CB.*, FX.*, SP.*, EM.EMIT, TP.LOAD, UXC.BANK (all run BANK), EM.FIX
      (hot), SY.HASH, RT.USE. Untested: BANKMGR and the DIM block in a region.
    - Then `ON CASE`, from the note in lib/STRINGS.UXI:115: a numeric-only select by jump
      table. Design agreed with the user on 2026-10-13: closed by END CASE; CASE ELSE is
      allowed; no ranges, a CASE lists its values (CASE 1, 2, 5); the selector is a BYTE,
      so the table has at most 256 entries. The R_* template is asm: ask before writing it.
    - OC1: done. src/UXC-CASE.BL (prefix CS.) is in the bank 28 region, after UXC-LEX.BL; its
      header has the code layout. SM.STMT sends ON, CASE and ENDCASE there, and SM.END sends
      END CASE. One new template, T_CASE_JMP in tpl/T-FLOW.ASM (user approved): TAY, the target
      from the low and high tables by Y into ZP_TMP, JMP (ZP_TMP); X is kept. The tables are
      written by CS.TABLE as LK.ORG + offset with no fixups, because the code never moves; with
      EMIT and fixups a 256-entry table cost 3 s of compile. The targets of the open ON CASE at
      depth d are words in CS.BANK (claimed by CB.INIT) at (d - 1) * K.CS.SIZE; CS.CLEAR,
      CS.PUT and CS.GET are low in UXC-CODE.BL. K.NS.CASE is 3, and DO, FOR and REPEAT moved to
      4, 5 and 6: NS.FIND takes any kind from K.NS.DO up as a loop. ON, CASE and ENDCASE are
      reserved. Errors: STATEMENT BEFORE CASE, CASE AFTER CASE ELSE, CASE NEEDS A CONSTANT,
      CASE VALUE OVER 255, CASE VALUE TWICE, ON CASE NEEDS A BYTE, CASE WITHOUT ON CASE,
      END CASE WITHOUT ON CASE, ON CASE WITHOUT END CASE. All are compile-time only. UXC.PRG
      4,099 to 4,214 bytes; UXC.OVL 48,405. Build 98 s loaded. ONCASE 5.3 s, ERRCASEBEFORE,
      ERRCASETWICE and ERRCASEWORD 1.7 s each, FLOWLOOP 4.7 s, FLOWREP 5.7 s (5.1 before,
      loaded), all ok.
- The help and plan were updated by the doc-style agent; it ran help/MKHELP.PY.

UXDOS16 (`C:\dev\CmdrX16\UXDOS16`) needs ROM-able output, a register-entry `SUB`, `LONG`,
`CALL AT` and banked variables; plan section 5 holds each, with the order. UXDOS16 wanted an unsigned
`LONG`; that is now `ULONG` (user, 2026-10-13). `SUB ... REGS` keeps the registers at `$030C`–`$030F`,
the bytes `SYS` uses; the program names them, `REG.A` or `REG_A`. UXDOS16 PLAN section 12 lists
its own order and says the features are not in our plan; that is UXDOS16's to update.

**Later, in this order** (user, 2026-10-11). The user approved asm for this step; ask again
only for asm outside it.

1. **The string library as asm runtime.** The user wants as much of the core in asm as
   possible. `INSTR` is done. Make `LEFT$`, `RIGHT$`, `UCASE$` and `LCASE$` built-in
   functions, like `MID$` and `INSTR` (SG.FUNCTION in src/UXC-STR.BL), with `R_*` routines in
   tpl/R-STRING.ASM, linked only when used. A new name goes in SG.FUNCTION, SG.SCAN.KNOWN,
   NM.WORD (src/UXC-NAME.BL) and a `BIND` line in `lib/STRINGS.UXI`.

**Proposed, not approved: DIM in the first pass.** SB.SCAN declares each DIM, so a BIND to a
variable and a use before the DIM work on any line. The second pass then only emits the
storage.

Plan section 5 also holds the new items "A compile report", "`FRE`", "`FILE.SEEK`" and "A RAM
bank manager". The bank manager is decided: built in, asm approved, names through
`lib/BANK.UXI`, with `BANK.SELECT` to select a bank. It stays on the to-do list until the user
schedules it.

Plan section 5 "Record types" holds the plan for `TYPE ... END TYPE`, with `BYTE`, `WORD`
and `STRING * n` fields. Section 5 "More types" holds `INT`, `LONG` (32 bits) and `FLOAT`
(the ROM math library). Neither is scheduled. Both start with the step that stops type codes
being sizes.

## Editor

The UXCEDIT notes are in `docs/HISTORY.md`, under "Notes moved from HANDOFF.md on 2026-10-10".
The user drives the editor tests by hand. Do not run a headless drive of UXCEDIT.

## Compiler map

| Region | Bank | Modules |
|---|---|---|
| low RAM | | `UXC.BASL` (main, all DIMs at the top), `-DEFS`, `-LEX`, `-SYM`, `-CODE`, `-LINK` |
| `K.BANK.EXPR` | 20 | `UXC-EXPR.BL` (EX.*), `UXC-COND.BL` (JP.*, CN.*) |
| `K.BANK.FLOW` | 21 | `UXC-STMT.BL` (SM.*), `UXC-FLOW.BL` (NS.*, CT.*, FR.*, RP.*) |
| `K.BANK.SUB` | 22 | `UXC-SUB.BL` (SB.*), `UXC-NAME.BL` (NM.*) |
| `K.BANK.STR` | 23 | `UXC-STR.BL` (SG.*); its header comment has the string design |
| `K.BANK.ASM` | 24 | `UXC-ASM.BL` (AS.*): `ASM`, `SYS`, the 65C02 assembler |
| `K.BANK.FOR` | 27 | `UXC-FOR.BL`, `UXC-FOLD.BL`, `UXC-INDEX.BL` (EX.PEEK, EX.INDEX) |
| `K.BANK.LONG` | 28 | `UXC-LONG.BL` (EX.LONG.*), `UXC-LEX.BL`, `UXC-CASE.BL` (CS.*) |

- UXC.MAIN claims banks 20–24 right after BANKMGR.INIT. The regions are written to `UXC.OVL`.
- A GOTO from one region to another, or from a region to low code, is written
  `GOSUB x : RETURN`.
- The source is read twice. `SB.SCAN` declares every `SUB` and calls `NM.SCAN`; the second pass
  compiles.
- Templates: `tpl/*.ASM`, built by `tpl/MKTPL.PY`. Ids are `T.NAME.ID` in `UXC.TPL.BL`;
  inserting a template moves every id after it.
- Error tests: the `.OUT` is the `ERROR,<line>,<msg>` line. RUNDIV0.OUT, RUNSUB.OUT and RUNRECSUB.OUT hold code
  addresses, which move when the start code changes.

## Code notes

- The string design is in the header comment of `UXC-STR.BL`. A string variable is a
  `[max][len][data]` block in BSS, and its value is the block address in A/Y.
- STRING results: SG.RESULT, SG.IS.RESULT and SG.RETURN.EMPTY in `UXC-STR.BL` (bank 23),
  called from SB.FUNCTION, SB.RETURN and SB.FALL.OUT in `UXC-SUB.BL`. No new templates.
  The `SUB` returns in A/Y the address of the block that holds the result: a literal, one of
  its temps, a parameter's block or another variable. `RETURN` makes no copy. The caller
  reads the block and never writes it, and keeps its address in a hidden WORD (`%P 1` and
  on). The caller copies the result into a temp of its own when it passes the result to a
  `SUB`, or when another call comes later in the same statement: a temp of the `SUB` holds
  the result only until the `SUB` runs again. A body that ends without a `RETURN` gives "".
  A result has no size of its own and is at most 255 characters.
- Files: R_FILE, R_FIN, R_FREAD and R_FWRITE are in `tpl/R-FILE.ASM`; SG.OPEN, SG.READ and
  SG.WRITE are in `UXC-STR.BL`. A handle is the KERNAL logical file number 3–14 on unit 8.
  File 15 is the command channel; the first `OPEN` opens it and it stays open.
- R_FIN holds each handle's next byte in `ahead`, so `READ`, `INPUT #`, `LINPUT #` and `EOF`
  can be mixed on one handle.
- The chain: `UXC.INPUT` line 3 names the program UI.CHAIN (`src/UXC.BASL`) loads after
  the result line. The hop is in plan section 4 item 5. A test with `tests/NAME.NEXT`
  chains to the PRG it names.
- `ASM` and `SYS`: AS.* in `src/UXC-ASM.BL` (bank 24), R_SYS in `tpl/SYS.ASM`.
- `ASM` labels: AS.LABEL.* and AS.REFERENCE.* arrays, DIMed in `UXC.BASL`. A use of a label
  further down is kept and patched at END ASM by AS.RESOLVE. JMP and JSR to a label take a
  K.F.ABS fixup in K.SEC.CODE.
- Pointers: `AddrOf(name)` is EX.ADDROF, `@name` with brackets (EX.AT.NAME). A read of
  `ContentsAt` or `ContentsAtW` is EX.PEEK, by the operator K.EO.PEEK or K.EO.WORDPEEK. A
  write is SM.CONTENTS, which shares SM.POKE.ADDRESS with `POKE`; a computed address goes
  through SM.STORE.THROUGH, the tail of the array store. Tests POINTER, ERRADDROF and
  ERRCONTENTS.
- Fixed addresses: NM.AT (`src/UXC-NAME.BL`) adds a variable record with flag K.SY.FIXED (2)
  and the address as its value. Its loads and stores use section K.SEC.CONST, an absolute
  address with no fixup. The FOR stack keeps the counter's section in NS.VS%. AS.ADDRESS
  writes a K.SEC.CONST `@name` as it is. Checklist: a new reader of a variable record checks
  K.SY.FIXED, as EX.OPERAND, EX.AT, SM.LET, CT.FOR and SG.INPUT.NEXT do.
- Temp pools: SB.POOLS (`UXC-SUB.BL`, bank 22) places the pools at link, after the array
  space. SB.EDGE adds a hidden K.SK.CALL record, `%C n`, for each `SUB` a `SUB` calls. It is
  owned by the caller; its value is the `SUB` called and its count is the line of the first
  such call. A call from the main program adds none. These records and the temps count
  toward the 1008 names of TOO MANY NAMES: pyuxc keeps the symbol table in 4 banks, GPC UXC in 2.
- A temp record has flag K.SY.TEMP (4), and its value is its offset in its owner's pool. A
  K.SEC.TEMP fixup holds its owner, SB.CURRENT, in bytes +6/+7. LK.FIX adds the owner's pool
  offset from SB.POOL.OF. A `SUB` record holds its level at +28 (K.SY.LEVEL, a byte), its
  temp count at +29 (K.SY.TEMPS, a byte), and at +30 (K.SY.POOL, a word) its frame bytes,
  then its pool offset.
- Locals: SB.PLACE.VARIABLE and SB.PLACE.BLOCK (`UXC-SUB.BL`) place a variable or a block in
  the frame of the `SUB` being compiled, or in the main program's space. Inside a `SUB`, a
  K.SEC.VAR or K.SEC.BSS value from K.FRAME.BASE (49152) up is 65536 less the local's
  distance below its pool's offset. LK.FIX resolves it through the fixup's owner. SB.CALL.STORE
  and SB.CALL.POP set SB.CURRENT to the `SUB` called while they emit: the parameter is in the
  callee's frame.
- Temps are not cleared at startup. The startup code sets the max byte, 255, of each temp.
- A KERNAL probe is plain BASIC typed with `x16emu -bas FILE -run` and `-fsroot` a scratch
  folder.
- The detail of steps 4.4c to 4.6b is in `docs/HISTORY.md`, under "Notes moved from
  HANDOFF.md at step 4.7a".

## Traps

- There is no `!` mark: a name with no mark is a BYTE. A SUB with no mark and no AS returns
  nothing.
- KERNAL `CHRIN` from the screen leaves the prompt out of the line, and leaves the cursor on
  the typed line: R_INPUT prints the CR. Any output before the next `CHRIN` drops the rest of
  a typed line.
- The KERNAL `OPEN` never fails on a missing file. `OPEN` reads the command channel, and a
  status that does not start with "0" closes the file and returns NOFILE ($FFFF).
- Emulator DOS (ROM R49, `-fsroot`): the last byte of a file comes with ST 64. A read past
  the end gives 0 with ST 66, and so does the first read of an empty file.
- Handles 0–2 cannot be read: KERNAL CHKIN gives FILE NOT OPEN.
- Bank free bytes on 2026-10-13, after T2: 20 has 521, 21 has 2203, 22 has 3824, 23 has
  2485, 24 has 4537, 25 has 3676, 26 has 4188, 27 has 4610. Measure from `build/UXC.MAP`: a line `BB:AAAA n` is bank
  `BB` in hex; 8K less the highest address in a bank is its free bytes. Past 8K the
  build stops with `GP.BANKED REGION OVER 8K @ line`; the line is the region's own
  `GP.BANKED` in `build/UXC.SRC.PRG`. New statement code goes in another region, with one
  `GOSUB` line in SM.STMT.
- Git Bash `sed -i` turns CRLF into LF. Edit the CRLF files (UXC-STR, UXC-EXPR, UXC-STMT,
  UXC-FLOW, UXC-ASM, UXC.BASL, HISTORY.md, UXC-HELP.md) with a Python script that keeps the
  endings.
- A label and a variable with the same name give DUPLICATE SYMBOL.
- EX.PREC ranks every operator id from K.EO.LOR up as AND or OR. A new K.EO id goes below
  K.EO.LOR, and LOR and LAND move up.
- BASLOAD `#DEFINE` names may not contain digits, and no name may begin another name.
- GPC allows only 32 arrays used before their DIM, so every DIM sits at the top of `UXC.BASL`.
- A string literal in GPC source passes 255 characters as OUT OF RANGE. NM.R$ and NM.Q$ in
  NM.RESERVED split the reserved words for this reason.
- `?RTB133` at boot means `build/` lost the runtime file. A build during a test run causes it.
  Rebuild.
- A test with `tests/NAME.IN` gets its lines typed on the keyboard. The harness types `LOAD`
  and `RUN` through `-bas`, because `-bas` loses keys while `-prg` loads. Typed text is not
  in the output; the CR R_INPUT prints is.
- `-echo` logs every CHROUT, so what `PRINT #` writes to a file shows in a test's output.
- `-echo` also logs every byte `WRITE` sends, and tests.py prints the log as cp1252, which
  fails on some bytes. Keep a binary-file test's data printable apart from the bytes under
  test.
- `PRINT CHR$(147)` clears the screen and then prints its own Return, so the next PRINT
  lands on the second row.
- The tests do not see the screen. Check the CP437 conversion on exit by eye in the emulator.
- A new built-in function in EX.OPERAND goes in SG.SCAN.KNOWN too, or SG.SCAN reports it as
  UNDECLARED NAME.
- GPC's banking rules are in `tools/gpc/GPC-BASIC/BANKED-OR-NOT.md`.
- BASLOAD stops a source line of 230 characters with LINE TOO LONG. A line of 190 passes.
- The Write tool strips the trailing spaces of a line. A PRINT of numbers ends in a space, so
  write a test's `.OUT` from Python.
- The emulator prints a warning into the test output at the first RMB, SMB, BBR or BBS
  it runs. A test that runs one fails on the warning.
