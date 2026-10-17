# UXCBASIC work history, 2026-10-09 to 2026-10-10

The old handoff notes, in the order they were written. `docs/HANDOFF.md` holds the current state.
Read this file only to trace how something came to be.

## The project

UXCBASIC is a small native-code BASIC compiler for the Commander X16, a 65C02
machine. Version 1 of the compiler is written in GPC BASIC (GP.BASIC source,
`.BASL`/`.BL`). It compiles in the emulator to `build/UXC.PRG`. The compiler
reads a `.UXB` source and writes a native PRG built from machine-code templates.

- Design and order of work: `docs/UXCBASIC.PLAN.md`. The user approved it, and it
  holds the to-do list.
- Compiler source:
  - `src/UXC.BASL` is the main file.
  - The modules are `src/UXC-DEFS.BL`, `-LEX`, `-SYM`, `-CODE`, `-LINK`,
    `-EXPR`, `-STMT` and `-FLOW`.
- Templates: `tpl/*.ASM`, assembled by 64tass and built by `tpl/MKTPL.PY` into
  `UXC.TPL.BIN`. The record ids are regenerated into `UXC.TPL.BL` as
  `T.NAME.ID`.
- Help viewer: `src/UXC.HELP.BASL`. Its content is `help/UXC-HELP.md`, built by
  `help/MKHELP.PY`.
- Tests: `tests/NAME.UXB` with the expected output in `NAME.OUT`. An error test's
  `.OUT` is its `ERROR,<line>,<msg>` line.

## Tools and commands

Python is `/c/Users/Admin/AppData/Local/Programs/Python/Python313/python.exe`;
`python` is not on PATH. Open files with `encoding='utf-8'`.

| Command | What it does |
|---|---|
| `build.py` | Builds UXC.PRG. **Empties build/ first.** About 26 s. |
| `build.py UXC.HELP` | Builds the help viewer. About 55 s. |
| `tests.py NAME` | Compiles and runs one test, then compares it with its `.OUT`. |
| `tests.py` | Runs the whole suite. |
| `uxc.py FILE.UXB [--run]` | Compiles one source in the emulator; `--run` also runs the PRG. |
| `run.py [NAME]` | Runs a PRG headless and writes the output to `build/RUN.LOG`. |

The emulator and the GPC scripts come from `C:\dev\CmdrX16\dos_tools\x16-blitz-compiler`.
`tools/gpc` holds a pinned copy of GPC build 133. GPC's banking rules are in
`tools/gpc/GPC-BASIC/BANKED-OR-NOT.md`; the copy in `build/` is wiped by every
build.

## Standing orders from the user

- Ask before writing any asm, which includes the templates in `tpl/`.
- Time every build, and run builds in the background.
- Compile SHARED.
- Kill the emulator only by its PID or handle, never by image name.
- **Run one compile or test at a time, time it, and report it before the next.**
  A test normally takes 1–3 s in warp mode. One that runs past about 5 s is a
  failure to investigate at once, not something to wait on. Run the full suite
  only when single tests pass. The user follows along.
- Do not build while tests run, because each build empties `build/`.
- Remind the user to `/compact` after each step.
- No `git init` until the user says so.
- Bash heredocs with complex quoting fail. Use Write/Edit, or a Python script in
  the scratchpad.
- Reply style: the user runs `/caveman ultra`, so keep replies terse. Code,
  comments, docs and memory are written in normal prose.
- Explain new syntax to the user with an example.

## Where the work stands

Step 4.1 (expressions) is done: 25 tests passed and UXC.PRG was 10462 bytes.

Step 4.2 (control flow) is **written but not tested.** It adds IF/ELSEIF/ELSE/ENDIF,
DO/LOOP, FOR/NEXT, REPEAT/END REPEAT, EXIT, CONTINUE, GOTO and short-circuit AND/OR
in conditions. The design decisions are in the plan doc and in the help topics.

- `tpl/T-FLOW.ASM` is new and holds template ids 61–83. The user approved these
  templates.
- `src/UXC-FLOW.BL` is new, about 30 KB of source, with these parts:
  - JP.*: jumps and the lists of forward jumps.
  - CN.*: conditions.
  - NS.*: the nesting stack.
  - CT.*: the statements.
  - FR.*: FOR.
  - RP.*: REPEAT.
- `src/UXC-EXPR.BL` changed:
  - Values spill lazily.
  - EX.FAST uses the no-push templates.
  - EX.TEST handles NOT.
  - The paren depth is EX.PD.
  - At depth 0 in a condition, AND/OR become LAND/LOR (21/22).
- `src/UXC-STMT.BL` changed:
  - SM.STMT dispatches the statements.
  - SM.END handles END IF and END REPEAT.
  - The reserved words list is updated.
- `src/UXC.BASL`:
  - **All DIMs are at the top**, before `GOTO UXC.MAIN`. GPC allows only 32
    arrays used before their DIM.
  - It includes UXC-FLOW.BL.
  - UXC.LINK calls CT.OPEN.
- `help/UXC-HELP.md` has the Control, IF, DO, FOR, REPEAT, EXIT and CONTINUE, and
  GOTO topics.

There are 12 new tests that have never run:

- FLOWIF, FLOWLOOP, FLOWFOR, FLOWREP, FLOWGOTO
- ERRNEXT, ERRIFOPEN, ERRSTEP, ERRTHEN, ERRELSE1, ERREXIT, ERRDOCOND

### Update, 2026-10-09 12:35: the banking fix is in, and the old tests pass

The user approved the plan below, and it is done:

- JP.* and CN.* are now in `src/UXC-COND.BL`.
- Region `K.BANK.EXPR` (bank 20) holds EXPR and COND. Region `K.BANK.FLOW` (bank 21)
  holds STMT and FLOW. UXC.MAIN claims both banks right after BANKMGR.INIT.
- The cross-region GOTOs are now `GOSUB x : RETURN`, and so are the GOTOs from a region
  to low code (LX.NEXT, and CB.PUT, which runs BANK).
- The build takes 26–27 s. UXC.PRG is 6198 bytes, and UXC.OVL is 12805 bytes.
- SM.RESERVED's word list passed 255 characters (OUT OF RANGE). It is now split into two
  strings, SM.R$ and SM.Q$.
- In `uxc.py`, `compile_source` now also stops at the third READY., so a compile that
  crashes fails in about 1 s instead of waiting 30 s.
- SKEL and the 24 other old tests pass, one at a time, in 1.1–4.1 s each. EXPR1 is the
  slowest.

**Next:** run the FLOW* tests one at a time (FLOWIF, FLOWLOOP, FLOWFOR, FLOWREP, FLOWGOTO),
then the new ERR* tests. The helper `one.sh` runs the named tests one by one with a
10 s limit, and stops at the first failure. It was in the old session's scratchpad, so
write it again if you need it. The sections below describe the state before this fix.

### Update, 2026-10-09: step 4.2 is done

All 37 tests pass. The full suite takes 70 s. The FLOW* tests take 2.5–5.1 s each:
FLOWFOR takes 5.1 s and FLOWIF 4.9 s. The ERR* tests take 1.1–1.3 s each.

The scratchpad helper `one.sh` stops a test at 7000 ms.

**Next:** step 4.3, `SUB`/`CALL`/`RETURN`. Its design is in the plan doc. The user has
not yet said go.

### Update, 2026-10-09: step 4.3 is done

`SUB`/`ENDSUB`/`RETURN`/`CALL` work. The user chose: `CALL` is optional, and the brackets
are required, even empty (`F()`). All 47 tests pass; the suite takes 100 s.

- New templates T_RTS, T_POPB_V, T_POPW_V at the end of `tpl/T-CORE.ASM` (approved).
- `src/UXC-SUB.BL` runs from a third region, `K.BANK.SUB` (bank 22).
- The compiler reads the source twice. `SB.SCAN` declares every SUB and its parameters;
  the second pass compiles. Each test now takes about 1 s more.
- Symbol records have an owner (+25) and a parameter count (+27). `SY.FIND` takes `SY.OW`.
  `SM.NAME` looks in the current SUB, then in the main program.
- `EX.EXPR` starts its operators at `EX.OP.BASE`, so a call's arguments parse inside an
  expression. `SB.CALL` keeps its state per depth in the `SB.CALL.*` arrays.
- Build: 31 s (new baseline). UXC.PRG 6424 bytes, UXC.OVL 15879 bytes.
- The help topic Subroutines is written. `build.py UXC.HELP` was not run.
- New tests: SUB1, SUBFWD, SUBNEST, ERRSUBSELF, ERRSUBARGS, ERRSUBRET, ERRSUBNOVAL,
  ERRSUBEND, ERRSUBPAREN, ERRSUBNORET.

**Next:** step 4.4: arrays, strings, `INPUT`, `GETKEY`. The user has not said go.

### Update, 2026-10-09: step 4.4a is done

Arrays, `GETKEY()` and `ERRORS ON`/`ERRORS OFF` work. All 53 tests pass; the suite takes
112 s.

- Build: 34 s. UXC.PRG 6649 bytes, UXC.OVL 17415 bytes.
- RUNSUB.OUT is written and checked. The error address `$0848` is the `JSR R_ESUB` after
  `CMP #10`.
- RUNDIV0.OUT now expects `$082D`.
- The help topics Arrays, GETKEY and ERRORS ON and OFF are written. MKHELP gives 20 topics.
  `build.py UXC.HELP` was not run.
- The plan has step 4.4a marked done. A user to-do was added to its open points: more types,
  as in XC=BASIC.
- `SYS` does not exist yet. It is step 4.6.

### Update, 2026-10-09: namespaces and BIND are done

The user chose these after a review of Prog8. All 60 tests pass; the suite takes 130 s.

- Build: 39 s. UXC.PRG 6778 bytes, UXC.OVL 18951 bytes. Bank 21 ends at `$BD23`, bank 22
  at `$B15F`.
- `NAMESPACE name ... END NAMESPACE` (or `ENDNAMESPACE`). They nest and can be reopened.
  The body holds only `DIM`, `VAR`, `SUB`, `BIND`, `ERRORS` and namespaces.
- `BIND name = target` names a variable, an array, a `SUB` or a namespace. The new name
  must carry the target's mark.
- A dot always separates scopes, as in Prog8. `_` is a name character. A part of a name is
  16 characters at most. `MY.COUNT.2` now stops the compile with BAD NAME.
- A `SUB`'s own names can be read from outside it: `SHOW.N!`.
- New module `src/UXC-NAME.BL`, in bank 22:
  - `NM.FIND` replaced `SM.NAME`.
  - `NM.RESERVED` replaced `SM.RESERVED`, which moved out of bank 21. It also refuses a
    dotted name in a declaration. `UXC`, `NAMESPACE`, `ENDNAMESPACE` and `BIND` are
    reserved.
  - `NM.CURRENT` is the open namespace. `NM.SCOPE` is where a new name goes.
- `SY.GET` returns `SY.OWNER`. New kinds `K.SK.SPACE` (5) and `K.SK.BIND` (6).
- The first pass (`SB.SCAN`) calls `NM.SCAN`, so a `SUB` header gets its namespace as owner.
- Tests: NS1, NS2, ERRNSBODY, ERRNSUNDEC, ERRBINDMARK, ERRNSOPEN and ERRBADNAME are new.
  NAMES.UXB uses `_` now.
- Help: Namespaces and BIND are new, and Types has a Names part. `build.py UXC.HELP` was
  not run.
- The plan also has these new to-do items: `DIM I! AT ZP`, split WORD arrays, and CP437.
- CP437 is done (the plan's ASCII item). The user approved the asm, option A: convert the
  screen on exit.
  - `S_INIT` in `tpl/SYS.ASM`: keep `$0372` in `ZP_MODE` ($27), send `$0F`, call `$FF62`
    with A = 7. `T_START` calls it.
  - `S_EXIT` in `tpl/SYS.ASM`: if the kept mode is not ISO, convert every screen code to
    PETSCII through VERA ports 0 and 1. Then `$FF62` with the kept byte AND 63, store the
    kept byte to `$0372`, restore the stack, RTS. `T_END` and `R_ERROR` jump to it.
  - Unmatched codes become spaces. Charsets 3 and 5 count as upper/lower. It assumes the
    KERNAL screen at VRAM `$1B000`, 256 bytes a row.
  - Every PRG grows by about 140 bytes. Every code address moved by 3, so RUNDIV0.OUT and
    RUNSUB.OUT were updated.
  - `uxc.py` and `run.py` run x16emu with `-echo iso`. `run_prg` drops the `\X0F` echo.
  - 60/60 tests pass (126 s). The tests do not see the screen, so the conversion on exit
    is not tested. Check it by eye in the emulator.

### Step 4.4b, strings: design agreed, no asm yet

The user approved this design on 2026-10-09.

- A string variable is a `[max][len][data]` block in the array space (BSS), outside the file.
  The startup work sets each `max`. The startup clear leaves each `len` at 0.
- `DIM S$ * n` and `DIM S AS STRING * n` give max n, 1 to 255. A STRING without a size is a
  compile error. `(n)` stays an array: a later string array is `DIM N$(10) * 20`.
  A STRING parameter has no size: `SUB SHOW(T$)`.
- A string value is its block address in A/Y. A literal is already one (`K.SEC.STR`).
- An assignment copies the text into the destination and cuts it at the destination's max.
- **Temps.** `+`, `MID$`, `CHR$` and `STR$` write into hidden temp blocks of max 255.
  - The compiler counts the temps that one statement needs at once and reserves the most.
  - Each SUB has its own temps, and the main program has its own, so a SUB called inside a
    string expression cannot overwrite the caller's temps.
  - `X$ + Y$` copies X$ into a temp, then appends Y$. A left side that is already a temp is
    appended to with no copy.
- All six compares work on strings. `R_SCMP` leaves C and Z as `CMP` does, so the WORD
  compare branches serve.
- A STRING parameter of a SUB is passed by reference: a WORD that holds the block address.
- `LEN(A$)` of a variable is a load of its len byte, with no new template.
- A number and a string in one operator: compile error TYPE MISMATCH.
- New zero-page word `ZP_DST` at `$28`: the destination block of a string routine.
- Not in 4.4b: string arrays, a SUB that returns a STRING, a start value, `INPUT` (4.4c).

**The string asm is in `tpl/`, approved by the user.** `tpl/T-STRING.ASM`, `tpl/R-STRING.ASM`,
and `ZP_DST` in `tpl/ZP.ASM`. MKTPL: 118 records, 2538 bytes. Ids 102-117:
- Templates: T_SCOPY, T_SCOPY_P, T_SCAT, T_SCMP_LR, T_SCMP_RL, T_SLEN, T_ASC, T_CHR,
  T_STR, T_VAL, T_MID.
- Routines: R_SCAT (63 bytes), R_SCMP (75), R_STR (82), R_VAL (125), R_MID (84).
- R_VAL skips spaces and a `+`, and reads a `-` right before the digits: `VAL("-5")` is
  65531. A `-` calls the digit loop as a subroutine and subtracts the result from 0.
- R_PRSTR is 29 bytes and R_PRWORD 79. R_PRWORD stays separate from R_STR: sharing them grows
  every program that prints a number without using STR$.
- Conventions: a routine takes the destination block in A/Y. R_SCAT copies with C clear and
  appends with C set, so there is no R_SCOPY. R_SCMP compares left to right with C clear and
  right to left with C set.
- The compiler must give MID$ a temp other than its source. It must copy a literal argument
  to a STRING parameter into a temp, so that the SUB cannot write into the literal.

### Update, 2026-10-09: step 4.4b compiler side is written and tested

- New module `src/UXC-STR.BL` (SG.*) in a fourth region, `K.BANK.STR` (bank 23), claimed in
  UXC.MAIN. Its header comment has the design.
- A string variable: kind VAR, type STR, value = BSS offset, SY.CNT = max. A STRING parameter:
  SY.CNT = 0, value = VAR offset of a WORD holding the block address (2 bytes of VR).
- A string entry on the value stack is K.EK.ADDR (block address) or K.EK.MEM (parameter).
  EX.FLUSH never pushes a string. A temp has section `K.SEC.TEMP` (7), which LK.FIX resolves
  as BSS (`>= K.SEC.BSS`).
- Temps are hidden VARs `%T 1`, `%T 2`... owned by SB.CURRENT, max 255. SG.N counts them per
  statement; SM.STMT and each PRINT item reset it.
- `+`: SG.LEFT (called from EX.OPERATOR.PUSH) copies a left side that is not a temp into a
  new temp; SG.JOIN appends the right side. Compares: push left, load right, T_SCMP_LR/RL.
- Functions parse each argument with SB.NEST / SB.UNNEST (new in UXC-SUB.BL, shared with
  SB.CALL); `SG.CALLED$()` keeps the name per depth.
- Folded at compile time: LEN and ASC of a literal (the literal is taken back out of the
  strings), CHR$ and STR$ of a constant (they become literals).
- Startup: SG.MAXES walks the symbol table after T_ZERO and emits T_LDB_C (only when the max
  changes) + T_STB_V per block.
- TYPE MISMATCH: `ER.MISMATCH` in UXC.BASL; checks in EX.TO, EX.UNARY, EX.TEST, EX.PEEK,
  EX.INDEX, SM.POKE, CT.FOR, SG.*.
- PRINT of a literal now goes through EX.EXPR (same code as before).
- Build 42 s. UXC.PRG 6854 bytes, UXC.OVL 21513 bytes. Suite: 67 tests, 0 failed, 160 s.
- New tests: STR1, STR2, STRSUB (4.5–4.9 s each), ERRSTRSIZE, ERRSTRNOSIZE, ERRMISMATCH,
  ERRMISMATCH2.
- Help: Strings topic written; Types and Subroutines updated. `build.py UXC.HELP` not run.

### Update, 2026-10-10: the five string savings are done

- `A$ = A$ + x` appends straight onto A$, when A$ is named once on the right and the right
  side has no possible SUB call. `A$ = A$` emits nothing. SG.LET, SG.LEFT, SG.IS.DESTINATION.
- `PRINT a + b` prints each part, when the item has no compare and no possible SUB call. The
  printed part is a temp entry of value K.TEMP.PRINTED (UXC-DEFS.BL). SG.PRINT.ITEM, called
  from SM.PRINT.ONE, now does the string side of a PRINT item.
- SG.SCAN reads the statement or PRINT item ahead (like CN.SCAN) for both: it counts names
  whose last part matches, and flags a name before ( that is not a known function or
  operator, and any compare.
- A compare with "" on either side is a compare of the length byte with 0 (SG.EMPTY.TEST,
  then GOSUB EX.BINARY for the numeric path). SG.LENGTH is shared with LEN.
- SP.ADD keeps each literal once and returns SP.NEW. SG.TAKE.LITERAL drops a literal only when
  it was new. SG.EMPTY.OFFSET / SG.EMPTY.KNOWN track "".
- T_SMAX is removed from tpl/T-STRING.ASM. UXC.TPL.BIN 2553 to 2538 bytes. Template ids from
  T_SCOPY on moved down by 1.
- Measured: `A$ = A$ + B$` 37 bytes smaller than `A$ = B$ + A$` (32 code, 5 temp max init).
  `IF A$ = ""` 91 bytes smaller than `IF A$ = "X"` (R_SCMP not linked). `PRINT A$ + B$` the
  same size as `PRINT A$; B$`. A repeated "HELLO" costs 0 bytes instead of 7.
- Build 44 s (machine loaded). UXC.PRG 6965 bytes (+111), UXC.OVL 22793 bytes (+1280).
- New tests: STR3 (append, print parts, dedupe, 4.1 s) and STR4 (compares with "", append
  fallback, 4.7 s). Suite: 69 tests, 0 failed, 172 s.

**Next:** 4.4c, INPUT and LINPUT.

### Earlier: step 4.4a was done before namespaces

**Next (then):** step 4.4b, strings. Show the user the asm templates first.

The section below is the record of the work in progress before the build.

### Update, 2026-10-09: step 4.4a in progress, code written, not built

The user crunched some lines in `src/`. After that, the build took 45 s (the machine was
loaded), UXC.PRG was 6411 bytes and UXC.OVL 16135 bytes, and all 47 tests passed in 121 s.

The user split step 4.4 in three:
- 4.4a: arrays, `GETKEY()` and `ERRORS ON`/`ERRORS OFF`. This is the work in progress.
- 4.4b: strings.
- 4.4c: `INPUT` and `LINPUT`.

Each part has its own asm review. The user also chose `GETKEY()` with brackets, the same rule
as a SUB call.

The 4.4a asm is approved and written. `tpl/MKTPL.PY` gives 100 records, and `--test` passes.
- New macro `aby` (absolute,Y) in `tpl/MACROS.ASM`.
- New `tpl/T-ARRAY.ASM`, included last. It holds T_LDB_AY, T_STB_SY, T_IDXB, T_IDXW,
  T_PEEKW, T_POKEW, T_CHKB, T_CHKW, T_ZERO, R_ZERO and T_GETKEY.
- `S_GETIN` is at the end of `SYS.ASM`, and `R_ESUB` ("BAD SUBSCRIPT") at the end of
  `R-ERROR.ASM`. The ids after them shifted.

The compiler code is written and has not been built yet.
- **DEFS:**
  - `K.SK.ARRAY` 4 and `K.SEC.BSS` 6.
  - `K.EO.INDEX` 21. LOR and LAND moved to 22 and 23.
- **SYM:** the element count is a word at +28. SY.ADD writes `SY.CNT`, and SY.GET reads it.
- **LINK:**
  - `LK.INIT.CALL` runs after T_START. It emits a JSR to the hidden label `%INIT`.
  - `LK.LINK` places `%INIT` on T_ZERO + T_RTS. With no arrays, it turns the JSR into a BIT
    ($2C).
  - The array space is `LK.BSS`, after the variables and outside the file.
- **EXPR:**
  - `EX.ELEMENT` pushes INDEX with the record in `EX.OA()`. `EX.INDEX` runs at the `)`.
  - `EX.AT` accepts an array.
  - `EX.GETKEY` handles `GETKEY()`.
- **STMT:**
  - `SM.BRACKET` sends `name(` to `SM.LET.ELEMENT` or to a SUB call.
  - `SM.STORE` is split out of `SM.LET`.
  - `SM.DIM.COUNT` reads the array size, which must be a constant.
  - `SM.ERRORS` handles `ERRORS ON` and `ERRORS OFF`, and ERRORS is reserved.
- **Main:** `BS.N` and `SM.ERRORS.ON` are set at the start, and `EX.OA()` is DIMed.
- **New tests:** ARRAY1, ARRAY2, GETKEY1, RUNSUB, ERRSUBSCR, ERRARRSIZE.
  - RUNSUB.OUT has not been written yet. Run it with `--update`, then check it: " 5 ", ON,
    then `?BAD SUBSCRIPT ERROR AT $xxxx`.

Next:
1. Build.
2. Run the new tests one at a time.
3. RUNDIV0.OUT changes, because every program is now 3 bytes longer at the start:
   `$082A` becomes `$082D`.
4. Run the full suite.
5. Write the help topics Arrays and `GETKEY()`, and the plan step 4.4a.

A user to-do was added to the plan's open points: ASCII, not PETSCII.

### The blocker: OUT OF MEMORY at startup (fixed)

The compiler builds in 26 s and gives an 18290-byte UXC.PRG. Then it stops at
once with `OUT OF MEMORY @ $43D5`, which is the string concatenation in
UI.READ.MORE. The cause is the SHARED layout: the p-code (from $0900) and the
string and array workspace share low RAM up to the runtime at $6F00. The p-code
now runs to about $4F69, so too little workspace is left.

The p-code sizes, estimated from `build/UXC.MAP`:

| Part | Size |
|---|---|
| EXPR | 4.3 KB |
| STMT | 2.0 KB |
| FLOW, JP and CN parts | 1.5 KB |
| FLOW, NS/CT/FR/RP parts | 4.7 KB |
| All p-code | about 18 KB |

### The proposed fix (NOT yet approved by the user)

The fix is to move code into GP.BANKED regions, as `src/UXC.HELP.BASL` does in
lines 6–66 and 250–262. Read `tools/gpc/GPC-BASIC/BANKED-OR-NOT.md` first. The
plan:

1. Split the JP.* and CN.* parts out of `UXC-FLOW.BL` into a new `UXC-COND.BL`.
2. Make region A: EXPR plus COND, about 5.8 KB.
3. Make region B: STMT plus the rest of FLOW, about 6.7 KB.
4. A region holds at most 8 KB.
5. Keep main, LEX, SYM, CODE and LINK in low memory. CODE, SYM and LINK run
   `BANK` statements, which are not allowed inside a region.
6. `#DEFINE` the two bank numbers above the GP.BANKED lines, as decimal
   constants, for example `K.BANK.EXPR 20` and `K.BANK.FLOW 21`.
   - The help viewer uses banks 11–13.
   - Check which banks the compiler itself takes at runtime: UXC.B and the
     others come from BANKMGR.GET.FREE.BANK.
7. Claim both code banks right after `GOSUB BANKMGR.INIT` and before `TP.LOAD`, or
   anything else that asks for free banks:
   `IF GP.FN(BANKMGR.CLAIM.BANK, n) = 0 THEN ...` (the form the help viewer uses).
8. Wrap each region in `GOTO X.END` / `GP.BANKED n` / includes / `GP.ENDBANKED` /
   `X.END:`.
9. A GOTO into a region from outside it is refused. Turn each one into
   `GOSUB target : RETURN`. Known cases:
   - SM.STMT to CT.*: the same region, which is fine.
   - SM.END to CT.ENDIF/CT.ENDREP: the same region.
   - CT.IF to CN.JT: crosses from B to A.
   - CT.GOTO/JP.BACK to JP.BR: check which side each one is on.
   - EX.REDUCE to CN.LOGIC: the same region, A.

   GOTOs out to low code may be allowed. The GPC compiler will report any it
   refuses.
10. The regions are written to `UXC.OVL`. Check that the build and the tests
    copy that file and that the PRG finds it at runtime. The help viewer's
    build is a working example.

The user's last word was a question about compacting, so the plan has not been
approved. **Ask the user before you start it.**

### After the fix

1. Build in the background and time it.
2. Run `tests.py SKEL` alone, time it and report it.
3. Run the old tests one at a time, then the FLOW* tests, then the new ERR* tests.
4. Fix the failures.
5. Run the full suite.
6. Update the memory file `uxcbasic-plan.md`, and the plan doc if needed.
7. Remind the user to compact.

## Things that went wrong before

- A label and a variable with the same name give DUPLICATE SYMBOL.
- BASLOAD `#DEFINE` names may not contain digits, and no name may begin another
  name.
- `?RTB133` at boot means the runtime file is missing from `build/`. On
  2026-10-09 a build ran during a test run and emptied `build/`; it stopped at the
  locked RUN.LOG. Rebuild when you see it.
- A suite ran 10+ minutes on 30 s timeouts before anyone noticed. That is the
  reason for the one-test-at-a-time rule.

## Later to-do items (from the plan doc)

- `ERRORS ON`/`OFF`.
- Passing variables in a RAM bank between programs.
- Removing unused code by default, with a keep instruction. It comes before any library of
  include files.
- Code for a set memory address, as Prog8 `%address` does.
- Added 2026-10-09, plan only, no code: `PEEKW`, `POKEW`, `MEM(a)` and `MEMW(a)`; `CONST`,
  with `#DEFINE` kept for `UXC.*` options only; `ENUM`, built on `CONST` and namespaces;
  `SHL`, `SHR`, `ROL`, `ROR`; `ON IRQ CALL name`; hardware registers as variables
  (`DIM VERA_DATA0! AT $9F23`), with the X16 names in a shipped `X16.UXH` read by
  `#INCLUDE`; CPU registers as variables, with `SYS` loading and saving A, X, Y and P at
  `$030C`–`$030F` and the carry as bit 0 of `REG_P!`; removing unused variables, with an
  `UNUSED VARIABLE` warning; debugging, as a map file, `STOP`, then `DEBUG ON`/`OFF` with
  `ASSERT` and `TRACE`.
- Added 2026-10-10, plan only, no code: `IIF`; overloaded `SUB`s; `BIND` to a statement, a
  macro with no parameters; `BIND` to a statement keyword, as in `BIND PRT = PRINT`.

## 2026-10-10: two more string savings

- SG.SCAN.ARRAY: SG.SCAN looks up the name before a `(` with NM.FIND, and sets SG.SCAN.CALL
  only when it is not an array. GETKEY was added to SG.SCAN.KNOWN after GETKEY1 failed with
  UNDECLARED NAME GETKEY.
- T_SCLEAR (`#ab stz, S0, 1`), approved by the user. SG.LET emits it for `A$ = ""` into a BSS
  block and takes the "" literal back. 16 bytes become 3. STR5.PRG 734 to 719 bytes. Template
  ids from T_SCAT on moved up by 1.
- run.py sets `errors="replace"` on stdout: a piped run died on a `\x9f` byte under cp1252.
  MKTPL.PY `--test` drops the `\X0F` that T_START prints. `--test` passes again.
- New test STR5. Suite: 70 tests, 0 failed, 175 s.
- The plan's ON IRQ CALL item points to XC=BASIC 3's interrupt code (user).

## 2026-10-10: step 4.4c, INPUT and LINPUT

- R_INPUT, S_CHRIN, and an offset on `#rec`, approved by the user. The first design kept the
  rest of a typed line for the next INPUT. It failed: the KERNAL drops the rest when anything
  is printed between two reads. Approved second design: C on entry drops the rest, and the
  last field of an INPUT sets it. Five templates: T_INPUT, T_INPUT_FIRST, T_INPUT_NEXT,
  T_INPUT_LAST, T_LINPUT.
- KERNAL CHRIN from the screen leaves the cursor on the typed line, so R_INPUT prints the CR.
- tests.py types tests/NAME.IN through x16emu `-bas`, with LOAD and RUN typed first.
- New tests INPUT1, INPUT2, ERRLINPUT. Suite: 73 tests, 0 failed, 187 s.

## 2026-10-10: T_PRCHR, one character printed from A

- T_PRCHR (`jsr S_CHROUT`), approved by the user. A PRINT item that is a one-character
  literal becomes `lda #c` and T_PRCHR, and the literal is dropped. For `CHR$(x)` with nothing
  emitted after its T_CHR, SG.PRINT.ITEM takes the T_CHR code and fixups back out, since A
  still holds x. `PRINT CHR$(N!);` is 6 bytes with no temp.
- New test PRCHR. Suite: 74 tests, 0 failed, 178 s.

## 2026-10-10: step 4.5a, OPEN, CLOSE and PRINT #

- Probed the emulator DOS from plain BASIC first. `OPEN` always gives ST 0; a missing file is
  `62,FILE NOT FOUND` on the command channel, and `,S,W` on an existing file is
  `63,FILE EXISTS`. `@:` replaces. LKUPLA ($FF59) works on ROM R49: C clear when open.
- Approved by the user: R_FILE (open, close, chkout, clrchn entries), R_EFILE, nine S_ jmp
  records (READST, SETLFS, SETNAM, OPEN, CLOSE, CHKIN, CHKOUT, CLRCHN, LKUPLA), T-FILE.ASM.
  The KERNAL's table replaces a handle table, so a second RUN without a LOAD sees no stale
  state. R_FILE is 162 bytes.
- The user chose: a comma in `PRINT #` writes ","; the mode must be a constant name, so the
  compiler builds the DOS name and the runtime has no buffer.
- New tests FILEW, FILEERR, ERROPENMODE. Suite: 77 tests, 0 failed, 228 s.

## 2026-10-10: step 4.5b, INPUT #, LINPUT # and EOF

- Approved by the user: R_FIN (open, chkin, eof, field, line, with getc and fetch inside),
  213 bytes, ZP_FILE at $2A, and five templates: T_FOPEN, T_CHKIN, T_FINPUT, T_FLINPUT, T_EOF.
- The read-ahead is set up by OPEN with O.READ, so no handle state survives a CLOSE and a new
  OPEN, or a second RUN. A program that never reads does not link R_FIN.
- The user chose: INPUT # and LINPUT # from handles 0-2 stop with FILE NOT OPEN, as the KERNAL
  gives it.
- EOF is a compare entry, so a loop test on it costs one branch.
- The user set a new rule: the full suite every 5th step; between them, only the tests of the
  code touched.
- New tests FILER, FILEINERR. Related tests passed: FILEW, FILEERR, ERROPENMODE, ERRLINPUT,
  INPUT1, INPUT2. The machine was at 92% CPU from elsewhere, so test times doubled.

## 2026-10-10: step 4.5c, READ and WRITE

- Approved by the user: R_FREAD (68 bytes) and R_FWRITE (54 bytes) in tpl/R-FILE.ASM, and
  T_READ and T_WRITE, one `jsr` each. The handle and the address go on the expression stack,
  the max or count in A/Y, as MID$ does.
- The user chose two records over one with a shared argument pop. The shared pop saves 12
  bytes only in a program that uses both.
- R_FREAD reads through R_FIN.chkin and R_FIN.getc, so READ and the line reads can be mixed
  on one handle and EOF stays right.
- Compiler: SG.READ, SG.WRITE and SG.BLOCK.ARGUMENTS in UXC-STR.BL. `@name` (EX.AT) gives the
  address.
- New tests FILEB (5.5 s) and FILEBERR (3 s). Related tests passed: FILER 6.4 s, FILEW 5.6 s
  and 5.1 s on a rerun. The laptop was in battery saver: ARRAY1 took 5.1 s with the CPU idle. Build
  51 s. UXC.PRG 6965 bytes, UXC.OVL 24585 bytes. Templates: 152 records, 3576 bytes.

## 2026-10-10: step 4.6a, ASM

- `ASM b, b, ...` on one line, and `ASM` ... `END ASM` or `ENDASM` as a block. An item is a
  constant, one byte for 0–255 and two for 256–65535, or `@name`, two bytes fixed up at link.
- The code first went in UXC-STMT.BL, and bank 21 went over 8K (`GP.BANKED REGION OVER 8K`).
  It is now src/UXC-ASM.BL (81 lines, AS.*) in bank 22, after UXC-NAME.BL.
- EX.FOLD.ADDRESS: `@name` plus or minus a constant now folds to an address everywhere, so
  `POKE @W% + 1, v` is one store and `READ(F%, @C! + 15, 45)` loads a constant.
- No templates changed: 152 records, 3576 bytes.
- New tests ASM1 (3.1 s), ERRASMITEM (1.6 s) and ERRASMOPEN (1.3 s). Related tests passed:
  ARRAY2 3.7 s, EXPR2 3.8 s, FILEB 5.5 s and 6.0 s, FILEBERR 3.5 s, NS1 4.0 s. The machine
  was on AC at 1696 of 1896 MHz with 28% load from other work, so every test took about twice
  its quiet time. Suite: 84 tests.
- Build 51–52 s. UXC.PRG 6972 bytes (+7), UXC.OVL 25353 bytes (+768).
- The user put off step 4.5d, `DIR`: it may become code in a `DIR` namespace.

## 2026-10-10: step 4.6b, SYS

- Approved by the user: R_SYS (43 bytes) in tpl/SYS.ASM, linked once when used, and T_SYS,
  one `jsr R_SYS`. Each `SYS` is the address in A/Y plus T_SYS, 7 bytes for a constant
  address.
- R_SYS loads A, X, Y and P from `$030C`–`$030F`, P with `AND #$F3`, calls through
  `jmp (ZP_PTR)`, and stores the four back. It keeps X with `phx`/`plx`.
- Compiler: AS.SYS in src/UXC-ASM.BL (bank 22). SM.STMT dispatches `SYS`; bank 21 still fits.
- Templates: 154 records, 3636 bytes. `MKTPL.PY --test` passes.
- New tests SYS1 (3.3 s) and ERRSYS (1.3 s). Related tests passed: ASM1 2.9 s, ERRASMITEM
  1.3 s, ERRASMOPEN 1.3 s, FILEB 4.7 s. Suite: 86 tests.
- Build 49 s on a loaded machine. UXC.PRG 6972 bytes, UXC.OVL 25353 bytes.

## 2026-10-10: step 4.7a, BYTE by default

- The user asked for it: the byte is the default type, so its mark should be blank.
- The `!` mark is gone. A name, an array or a `SUB` parameter with no mark and no `AS` is a
  BYTE: `DIM B` is `DIM B AS BYTE`. `A!` is a SYNTAX ERROR, because `!` is not part of a name.
- The marks left are `%` WORD and `$` STRING. `AS BYTE`, `AS WORD` and `AS STRING` still
  work, and a mark with `AS` is still A MARK AND AS.
- A `SUB` name with no mark and no `AS` still returns no value. A `SUB` that returns a BYTE is
  `SUB F() AS BYTE`.
- `BIND` still needs the same mark on both sides: `BIND B = A%` is BIND NEEDS THE SAME MARK.
- The error NO TYPE FOR name is gone, and its test ERRNOTYPE with it.
- New tests TYPEDEF (a no-mark BYTE as a variable and a parameter, and `AS BYTE` the same) and
  ERRBANG (`DIM A!` is SYNTAX ERROR). Every test and `examples/HELLO.UXB` was converted:
  `B!` became `B`, and `SUB NOARGS!()` became `SUB NOARGS() AS BYTE`. Suite: 87 tests.
- The help, the plan and the handoff were changed to match.
- Full suite: 87 tests, 0 failed, 236 s on a loaded machine.

## 2026-10-10: Notes moved from HANDOFF.md at step 4.7a

## Strings and input

- A string variable is a `[max][len][data]` block in BSS. Its value is the block address in A/Y.
  A routine takes its destination block in A/Y or in `ZP_DST` (`$28`). A STRING parameter is a
  WORD that holds the block address.
- `A$ = ""` is T_SCLEAR, one `STZ` of the length byte. A STRING parameter still copies "".
- SG.SCAN looks up a name before `(` with NM.FIND. An array does not block the append in
  place or the printed parts; anything else does.
- `INPUT` and `LINPUT` are SG.INPUT and R_INPUT. R_INPUT has three entries: 0 prints "? ",
  `field` and `line`. On a field, C set drops the rest of the line. `#rec jsr, R, offset`
  calls into a record past its start.
- KERNAL `CHRIN` from the screen leaves the prompt out of the line, and leaves the cursor on
  the typed line: R_INPUT prints the CR. Any output before the next `CHRIN` drops the rest of
  a typed line.
- Temps are hidden VARs `%T 1`, `%T 2`... of max 255, owned by the current `SUB`. SG.N counts
  them per statement.

## Files

- A handle is the KERNAL logical file number, 3–14, on unit 8 with the same secondary
  address. `R_FILE` (tpl/R-FILE.ASM) finds a free one with `LKUPLA` ($FF59). Logical file 15
  is the command channel; the first `OPEN` opens it and it stays open.
- `OPEN` reads the command channel after the KERNAL `OPEN`, which never fails on a missing
  file. A status that does not start with "0" closes the file and returns NOFILE ($FFFF).
- SG.OPEN builds the DOS name from the mode: `name,S,R`, `@:name,S,W`, `name,S,A`. `,S,W` on
  an existing file is `63,FILE EXISTS`; `@:` replaces.
- Reading is `R_FIN`. Each handle 3–14 holds its next byte back in `ahead`, with `state` 0
  (more follow), $40 (the byte held is the last) or $80 (nothing held). T_FOPEN reads the
  first byte, so a reused handle never sees stale state. `READ` (R_FREAD), `INPUT #`,
  `LINPUT #` and `EOF` all read through R_FIN and can be mixed on one handle.
- `EOF(h)` is a K.EK.CMP entry with tail CTRUE, so `DO WHILE NOT EOF(F%)` is a `bcs`.
- SG.READ, SG.WRITE and SG.BLOCK.ARGUMENTS are in `UXC-STR.BL`. READ is in SG.FUNCTION and
  SG.SCAN.KNOWN. WRITE is dispatched in SM.STMT.
- Emulator DOS (ROM R49, `-fsroot`): the last byte of a file comes with ST 64. A read past
  the end gives 0 with ST 66, and so does the first read of an empty file.
- Handles 0–2 cannot be read: KERNAL CHKIN gives FILE NOT OPEN.
- The probes are plain BASIC typed with `x16emu -bas FILE -run` and `-fsroot` a scratch
  folder. `SYS 65369` with `POKE 780,lfn` and `PEEK(783) AND 1` tests LKUPLA.

## ASM and SYS

- `src/UXC-ASM.BL` (bank 22) holds AS.ASM, AS.LINE, AS.ITEMS, AS.CONSTANT, AS.ADDRESS,
  AS.STRAY, AS.OPEN and AS.SYS. SM.STMT dispatches `ASM`, `ENDASM` and `SYS`; SM.END
  dispatches `END ASM`. AS.OPEN reports a block still open at the line of its `ASM`.
- AS.ITEMS folds each item with EX.EXPR. A K.EK.CONST of 0–255 is one byte, 256–65535 two. A
  K.EK.ADDR is two bytes and a K.F.ABS fixup.
- EX.FOLD.ADDRESS in EX.BINARY: K.EK.ADDR + or - K.EK.CONST stays K.EK.ADDR, with the sum mod
  65536. `POKE @W% + 1, v` is one store, and `@C + 15` is a constant load.
- `SYS a` is EX.EXPR, EX.TOW and T_SYS, `jsr R_SYS`: 7 bytes for a constant address. R_SYS,
  43 bytes in `tpl/SYS.ASM`, loads A, X, Y and P from `$030C`–`$030F`, P with `AND #$F3`,
  calls through `jmp (ZP_PTR)`, and stores the four back. It keeps X with `phx`/`plx`.
- Tests: ASM1, ERRASMITEM, ERRASMOPEN, SYS1, ERRSYS.
- Plan step 7, the line assembler, is to take mnemonics inside the same block.

## 2026-10-10: step 4.7b, DIM ... AT

- `DIM name AT address` puts a BYTE or WORD variable at a fixed address. The type comes from
  the mark or `AS`: `DIM W% AT $0400`, `DIM H AS BYTE AT $0400 + 1`. Several go on one line.
- NM.AT in src/UXC-NAME.BL (bank 22). The variable takes no space. Its record holds the
  address and the flag K.SY.FIXED (2, in UXC-DEFS.BL). Loads and stores use K.SEC.CONST, so
  `P = 5` is `LDA #5`, `STA $030F`: absolute addressing, also at a zero-page address.
- It works in expressions, assignment, `FOR` (NS.VS% keeps the section), `INPUT` and `BIND`.
  `@name` is a K.EK.ADDR in K.SEC.CONST; AS.ADDRESS writes it with no fixup.
- Errors: ADDRESS NOT A CONSTANT, and NOT YET: AN ARRAY OR A STRING AT AN ADDRESS.
- Not done: arrays and strings at an address, `DIM ... AT ZP`, the X16.UXH header.
- No templates changed: 154 records, 3636 bytes.
- New tests DIMAT (3.6 s), ERRATCONST (1.6 s) and ERRATKIND (1.4 s). Rerun and passing:
  FLOWFOR, INPUT1, INPUT2, ASM1, SKEL, ERRMARKAS, ARRAY1, NS2, SYS1. Suite: 90 tests.
- Build 74 s on a loaded machine. UXC.PRG 6968 bytes (+8), UXC.OVL 25609 bytes (+256).

## Notes moved from HANDOFF.md on 2026-10-10

### Editor

- UXCEDIT is the editor. The source is in `src/UXCEDIT/`: `UXCEDIT.BASL` and `UXCEDIT-CLIP`,
  `-FIND`, `-KEYS`, `-LOW`, `-PREFS`, `-STORE`, `-THEME`, `-UNDO` and `-VIEW` (`.BL`).
  Internal labels keep the `TURBO.*` prefix.
- `MKKEYS.PY` makes the key table `UXCEDIT.KEYS.BIN`. It holds GPC BASIC's keywords; the switch
  to UXCBASIC's words is a later step.
- `build.py UXCEDIT` builds `UXCEDIT.PRG` (8,446 bytes) and `UXCEDIT.OVL`, SHARED, in
  112–160 s: tokenise 62–76 s, compile 52–81 s.
- The menu bar is File, Edit, Search, Window, Build and Help. Build holds Compile (F5).
  Help holds Help, Settings and About.
- F5 is command 7. TURBO.BUILD (bank 38 region) saves, writes the relay files and sets
  TURBO.BUILDING%. The key loop ends into TURBO.BUILD.HOP, the editor's copy of UI.CHAIN.
  TURBO.DOCUMENT.KEEP stores the document on screen in the TURBO.KEPT arrays.
- The start after a compile: when `UXCEDIT.RUN` exists, TURBO.RESUME (bank 39 region)
  reads it, deletes it, loads each named document and shows the one compiled through
  TURBO.DOCUMENT.RESTORE. TURBO.RESULT.SHOW shows the `UXC.RESULT` line in a message box:
  the line number and message of an error, or the PRG name and size.
  The bank 38 region is full: past 8K the build stops with `GP.BANKED REGION OVER 8K`.
  No bank is free for a new region.
- The user drives the editor tests by hand. Do not run a headless drive of UXCEDIT unless
  the user asks.
- Settings are in `/SETTINGS.KVB`. The clipboard spills to `UXCEDIT.CLP`.
- `src/UXCEDIT/bench/` is not ported. It expects the GPC repo layout.
- `build.py [NAME ...]` takes `UXC`, `UXC.HELP`, `UXCEDIT` or `ALL`. `BUILD.BAT` builds.
  `RUNUXC.BAT`, `RUNHELP.BAT` and `RUNEDIT.BAT` run from `disk/` with
  `run.py NAME --disk --window`. `RUNTESTS.BAT` runs `tests.py`.
- `disk/` is the user's drive. `build.py` copies each program built there with its run-time
  files, and the GPC runtime to `disk/GPC/`. It copies a `.UXB` sample from `examples/` or
  `samples/` only when `disk/` has no file of that name. It deletes nothing in `disk/`.
  The user put the file manager XFMGR there; leave it.
  Builds and tests use `build/`.
