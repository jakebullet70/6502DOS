# UXCBASIC — design

UXCBASIC is a small compiled BASIC for writing the system programs and utilities of the planned
Unix-style X16. The compiler `UXC.PRG` turns one source file into a native 65C02 PRG. UXCEDIT is the
editor and runs the compiler. v1 of the compiler is written in GPC. When UXCBASIC can do files,
arrays and strings, the compiler is rewritten in UXCBASIC.

Status: approved on 2026-10-09. Steps 1 to 3, the template format, the compiler skeleton and
the test harness, are done.

## 1. The language

**Source.** One file of text from UXCEDIT, ASCII or PETSCII, one statement per line. There
are no line numbers. Keywords and names are not case-sensitive: the lexer folds the case of
ASCII and PETSCII letters. A name has up to 16 characters: letters, digits and `.`, and a
string name may end in the `$` mark. A label is `name:` on its own line. Literals are `123`,
`$7F`, `%1010` and `"text"`. There is no character literal: `ASC("A")` with a literal string is
folded to `65` at compile time, so it costs nothing at run time.

**Comments.** A whole-line comment starts with any of `REM`, `'`, `;`, `##` or `//`, after
optional spaces. Only `REM` and `'` may also end a line after a statement:

```
REM the whole line           ' the whole line          ; the whole line
## the whole line            // the whole line
X = 1 ' a trailing comment
X = 1 REM a trailing comment
```

`;` is a comment only at the start of a line, so `PRINT A; B` is unchanged. `##` cannot be
confused with a `#DEFINE`, which has one `#`. Inside a string, none of these start a comment.

**Types.** A number takes its type from `AS` in the declaration. A string takes the `$` mark
or `AS STRING`. Numbers have no marks (decided by the user, 2026-10-13).

| Type | Second name | Range | Size | Done |
|---|---|---|---|---|
| `UBYTE` | | 0 to 255 | 1 byte | yes |
| `BYTE` | | −128 to 127 | 1 byte | yes |
| `UWORD` | `UINT` | 0 to 65535 | 2 bytes | yes |
| `WORD` | `INT` | −32768 to 32767 | 2 bytes | yes |
| `ULONG` | | 0 to 4294967295 | 4 bytes | yes |
| `LONG` | | −2147483648 to 2147483647 | 4 bytes | yes |
| `STRING` | | Pascal style, 1 to 255 characters | max + 2 bytes | yes |

- Each size has a signed and an unsigned type. `INT` is `WORD` and `UINT` is `UWORD`. A value
  of 2 or 4 bytes is stored low byte first.
- `BYTE`, `WORD` and `LONG` are signed, and `UBYTE`, `UWORD` and `ULONG` unsigned. The
  signed rules are in §5 "More types", step 2. The 32-bit rules are in step 3.
- A number with no `AS` stops the compile with `MISSING AS: name`: `DIM B` gives
  `MISSING AS: B`. The rule holds for a `CONST` (`CONST N AS UBYTE = 10`), a `SUB` or
  `FUNCTION` parameter (`SUB SHOW(N AS UBYTE)`) and a `FUNCTION`'s result
  (`FUNCTION MAX(A AS UWORD, B AS UWORD) AS UWORD`). A `$` `FUNCTION` needs no `AS`.
- A record field takes the same words: `COUNT AS UBYTE`.
- `$` is the only mark. It is part of the name: `S` and `S$` are two names. A name declared
  with `AS` has no mark: after `VAR T AS STRING * 20` the name is `T`.
- `%` is not a mark. A `%` right after a name stops the compile with
  `% IS NOT A MARK: USE AS UWORD`. `%1010` is a binary literal.
- A `$` and `AS` on one name stop the compile with `A MARK AND AS`.
- `!` is not a mark and not part of a name. `DIM A! AS UBYTE` stops the compile with
  `SYNTAX ERROR`.
- A reserved word with a `$`, such as `PRINT$`, is a reserved name.
- A main program variable is static: it has one fixed address. The locals of a `SUB` or a
  `FUNCTION` are in its frame, in the pool of its call-graph level (§5 "Shared temps and
  locals"). There is no stack, so a `SUB` or a `FUNCTION` cannot recurse, and no two of them
  can call each other.

**Declarations.** `DIM` and `VAR` mean the same thing. One line can declare several names.

```
DIM A AS UWORD, B(10) AS UBYTE, L$ * 80
VAR N AS UWORD, T(10) AS UBYTE
DIM C AS UBYTE = 1, P AS UWORD = $1000
```

- Every variable must be declared before use. An undeclared name is a compile error, so a
  typo cannot make a new variable. A `SUB` or `FUNCTION` header declares its parameters.
- `B(10) AS UBYTE` is a UBYTE array of 10 elements, `B(0)` to `B(9)`. `B(i)` is one
  element.
- `AddrOf(name)` is the address of any variable, array or string, as a `UWORD`. `@name` is
  the same.
- `ContentsAt(a)` is the UBYTE at address `a`, and `ContentsAtW(a)` the UWORD at `a` and
  `a + 1`, low byte first. Each can be read and assigned:

  ```
  P = AddrOf(X)
  Y = ContentsAt(P)
  ContentsAt(P + 1) = Y
  ContentsAtW(P) = 1000
  ```
- `DIM REG_P AS UBYTE AT $030F` puts a `BYTE`, `UBYTE`, `WORD` or `UWORD` variable at a fixed
  address, a constant expression. It takes no space, and two such variables may share an
  address.

**Strings.** A string is a block of `[max][len][data]`. `DIM L$ * 80` reserves 82 bytes:
`max` = 80, `len` = 0 at the start, then 80 bytes of data. A STRING must have a size, 1 to 255:
`DIM L$ * 80` or `DIM L AS STRING * 80`. `(n)` always makes an array.

- `LEN(L$)` reads the length byte, with no scan.
- An assignment or `INPUT` stops at `max`, so a string never overflows.
- A string can hold any byte, zero included.
- A string literal is stored with `max` = `len`, and is read only.
- The compiler copies the bytes of a string literal into the PRG unchanged. UXCEDIT saves
  ASCII. A compiled program starts in ISO mode, so an ASCII literal prints as typed.
- v1 string operations: assignment, `+` (join), the six compares, `LEN`, `MID$`, `LEFT$`, `RIGHT$`,
  `CHR$`, `ASC`, `STR$`, `VAL`, `LVAL`, `INSTR`, `UCASE$` and `LCASE$`. `R_LEFT` and `R_RIGHT`
  enter `R_MID`. `T_UCASE` and `T_LCASE` call `R_CASE`, with C set for `UCASE$`.
- A record id past 255 takes the fixup kind `F_REC_HI`, `F_REC` + 1, in `tpl/MACROS.ASM`.

**Expressions (v1).**

| Precedence | Operators |
|---|---|
| highest | `( )`, function calls, `PEEK(a)`, `ContentsAt(a)`, `ContentsAtW(a)`, `name(i)`, `AddrOf(name)`, `@name` |
| | unary `-` |
| | `*` `/` `MOD` |
| | `+` `-` |
| | `<<` `>>` |
| | `=` `<>` `<` `>` `<=` `>=` |
| | `NOT` |
| | `AND` |
| lowest | `OR` `XOR` |

- An operation that mixes `UBYTE` and `UWORD` is done as `UWORD`.
- Assigning a `UWORD` value to a `UBYTE` keeps the low byte.
- An operator is signed when either side is a `BYTE` or a `WORD`, as in §5 "More types",
  step 2.
- Truth: 0 is false, and any other value is true. `IF X` tests for nonzero.
- A compare yields 0 or 1. `IF` and the loop tests compile a compare straight to a branch, with no 0/1
  value in between.
- `NOT` binds below the compares, as in MS BASIC and Prog8: `NOT A = B` is `NOT (A = B)`.
- `NOT` is logical: `NOT 0` is 1, and `NOT` of any other value is 0. `NOT` of a compare is
  folded into the opposite compare. For a bit flip, use `XOR $FF` or `XOR $FFFF`.
- `AND`, `OR` and `XOR` are bitwise, as in MS BASIC, so `PEEK(A) AND 15` masks. On compare
  results they work as logic. Inside a condition, `AND` and `OR` between compares compile to
  short-circuit branches. The trap, the same as in MS BASIC: `1 AND 2` is 0, so write
  `IF A <> 0 AND B <> 0`, not `IF A AND B`.
- Two UBYTE operands give a UBYTE operation, as in Prog8: `A * 2` with `A` = 200 is 144.
  Widen first for a UWORD result: `N = A` then `N * 2`, with `N` a `UWORD`.
- A number constant takes the other side's type when
  it fits, so `B + 1` is a UBYTE add. An operation on two constants is folded.
- `*`, `/` and `MOD` call runtime routines and work at `WORD` width. `/` and `MOD` call `R_DIVS`
  when a side is signed, else `R_DIVW`. Every other operator is inline code.
- An unsigned `/` by a constant power of 2, from 2 up, compiles to `>>`, and `MOD` by one to
  `AND` with the constant less 1. A signed side keeps the divide.
- Division by zero: a constant 0 divisor is a compile error. At run time the program stops with
  `?DIVISION BY ZERO ERROR AT $xxxx` (the address of the `JSR`; the `.LST` maps it to a line).
- Shifts use only the low byte of the count.
- `LONG` and `ULONG` are in §5 "More types", step 3. Floats are not done.

**Run-time errors.** A run-time error prints `?<message> ERROR AT $<address>` and ends the
program as `END` does. `R_ERROR` and the message are linked only into a program that can hit
the error.
- The division-by-zero check is always on: it is 5 bytes in the shared divide routine and
  about 1% of a divide.
- `ERRORS ON` and `ERRORS OFF` are compile-time switches for the source lines after them, like
  Turbo Pascal's `{$R+}` and `{$R-}`. They choose a checked or an unchecked template, so
  `ERRORS OFF` code costs nothing, as in Prog8. They control the inline checks: the array
  index and the string length. The default is `ERRORS ON`, as in MS BASIC. Put `ERRORS OFF`
  around a loop that must be fast.

**Commands.**

| Group | Statements |
|---|---|
| Data | `DIM` / `VAR`, assignment `name = expr`, `name(i) = expr` |
| Control | `IF expr [THEN]` … `ELSEIF expr` … `ELSE` … `ENDIF`, `IF expr THEN statement`, `SELECT CASE v` … `CASE tests` … `CASE ELSE` … `END SELECT`, `DO [WHILE\|UNTIL c]` … `LOOP [WHILE\|UNTIL c]`, `FOR v = a TO b [STEP k]` … `NEXT`, `REPEAT [n]` … `END REPEAT`, `EXIT DO\|FOR\|REPEAT`, `CONTINUE`, `GOTO label` |
| Subroutines | `SUB name(X AS UWORD, Y AS UBYTE)` … `ENDSUB`, `FUNCTION name(X AS UWORD) AS type` or `FUNCTION name$(S$)` … `ENDFUNCTION`, `[CALL] name(x, y)`, `RETURN [expr]`. `CALL` is optional; the brackets are required, even empty. |
| Console | `PRINT item; item, …` (a trailing `;` drops the newline), `INPUT var`, `LINPUT L$`, `GETKEY` (a function, 0 when no key is waiting) |
| Files | `F = OPEN(name$, mode)`, `N = READ(F, buf, max)`, `WRITE F, buf, n`, `CLOSE F`, `PRINT #F, …`, `INPUT #F, var`, `LINPUT #F, L$`, `EOF(F)`, `DIR "pattern"` |
| Low level | `PEEK(a)`, `POKE a, v`, `ContentsAt(a)`, `ContentsAtW(a)` (read and assigned), `AddrOf(name)`, `SYS a`, `ASM $A9, $41, …` (raw bytes; `AddrOf(name)` or `@name` puts in a variable's address), `ASM` … `END ASM` (a block of byte lines) |

- **Subroutines.** A `SUB` has no value. Its end is `ENDSUB` or `END SUB`. A `FUNCTION` has a
  value. Its end is `ENDFUNCTION` or `END FUNCTION`.
  - `SUB DRAW(X AS UWORD, Y AS UBYTE)` returns no value. `RETURN` leaves it early. A `SUB`
    name with a `$`, or
    an `AS` type after the brackets, stops the compile with `SUB WITH A TYPE: USE FUNCTION`.
  - `FUNCTION FIRST(S$) AS UBYTE` returns a UBYTE and
    `FUNCTION ADD(A AS UWORD, B AS UWORD) AS UWORD` returns a UWORD, with `RETURN expr`. A
    number `FUNCTION` with no `AS` stops the compile with `MISSING AS: name`.
    A `FUNCTION` is used inside an expression. Called as a statement, its value is lost.
  - `FUNCTION FIRST3$(S$)` or `FUNCTION WRAP(T AS STRING) AS STRING` returns a STRING, as the
    address of the block that holds the result.
  - A `FUNCTION` needs a `RETURN` with a value. Its end, when the body reaches it, gives 0, or
    "" in a STRING `FUNCTION`.
  - `FUNCT` is `FUNCTION` and `ENDFUNCT` is `ENDFUNCTION`, so `END FUNCT` works too. They are
    built-in `BIND`s: every source has them, as if it began with `BIND FUNCT FUNCTION` and
    `BIND ENDFUNCT ENDFUNCTION`.
  - The end must match the start. `END SUB` or `ENDSUB` in a `FUNCTION` stops the compile with
    `ENDSUB IN A FUNCTION`. `END FUNCTION` or `ENDFUNCTION` in a `SUB` stops it with
    `ENDFUNCTION IN A SUB`. An `END FUNCTION` with no `FUNCTION` open gives
    `ENDFUNCTION WITHOUT FUNCTION`. A `FUNCTION` still open at the end of the source gives
    `FUNCTION WITHOUT ENDFUNCTION`, and a `SUB` gives `SUB WITHOUT ENDSUB`.
  - `FUNCTION` is a reserved word. A namespace body may hold a `FUNCTION` as it holds a `SUB`.
  - A number parameter with no `AS` stops the compile with `MISSING AS: name`: `SUB SHOW(N)`
    gives `MISSING AS: N`.
  - Parameters and locals are in the frame of the `SUB` or `FUNCTION`, named `sub.var` inside
    the compiler. A local does not keep its value between calls, and only its own `SUB` or
    `FUNCTION` can name it.
  - A `UBYTE` or `UWORD` argument is passed by value. A string or an array is passed as a pointer
    to it, so the `SUB` or `FUNCTION` works on the caller's data and no copy is made.
- **IF** (decided 2026-10-09). The block form has any number of `ELSEIF` parts and one `ELSE`;
  `THEN` is optional at the end of the line. The one-line form `IF c THEN statement` has no
  `ELSE`, and a block statement after `THEN` is an error. `IF c THEN GOTO`, `EXIT` or
  `CONTINUE` (and `IF c GOTO label`) compile to one branch to the target.
  - No jump out (pyuxc, 6502DOS table only). A body before `ELSEIF`, `ELSE` or a `CASE` that
    ends in `RETURN`, `GOTO`, `EXIT`, `CONTINUE` or `END` has no `JMP` to the end. A statement
    after `IF c THEN` does not count.
- **SELECT CASE** (pyuxc only). The selector is a number or a string. A `CASE` holds tests
  separated by commas: a value, a range `low TO high` with both ends in, or `IS` with a compare
  operator and a value. Only the first `CASE` that matches runs. `CASE ELSE` comes last.
  - It compiles to the same code as an `IF`/`ELSEIF` chain, with no new template.
  - A variable selector, or an address such as a string literal, is read again at each test. Any
    other number is stored once in a hidden variable of its type. Any other string stops the
    compile with `SELECT CASE NEEDS A STRING VARIABLE`.
  - The errors: `CASE AFTER CASE ELSE`, `END SELECT WITHOUT SELECT`, `SELECT WITHOUT END
    SELECT`.
  - Trap: a function in a test that changes a variable selector changes the tests after it.
- **Two-word ends** (decided 2026-10-09): `ENDIF` or `END IF`, `ENDREPEAT` or `END REPEAT`,
  `ENDSELECT` or `END SELECT`.
- **FOR.** The loop ends when the counter passes `TO`, so a `STEP` that jumps over the `TO`
  value still ends the loop. The test also catches the wrap past 255 or 65535. After the
  loop the variable holds the last value the body saw (option A, decided 2026-10-09), not
  `TO` + `STEP` as in MS BASIC: the test is made before the step.
- **Files, Unix style.** `OPEN` returns a handle. There are no fixed channel numbers.
  - Handles 0, 1 and 2 are stdin (the keyboard), stdout (the screen) and stderr, to allow
    redirection later. `PRINT #1, "HI"` is the same as `PRINT "HI"`.
  - A file is opened for one direction in v1: `O.READ`, `O.WRITE` (replaces the file) or
    `O.APPEND`.
  - The return value carries the status. `READ` returns the count, and 0 at end of file.
    There is no `READST`.
  - `OPEN` returns `NOFILE` ($FFFF) when it fails. 0 cannot mean failure, because 0 is
    stdin.
  - Two forms sit side by side. `READ` and `WRITE` move raw bytes, for binary files and
    copies. `PRINT #`, `INPUT #`, `LINPUT #` and `EOF` work in lines, for text files.
- **Built-in names.** `O.READ`, `O.WRITE`, `O.APPEND` and `NOFILE` are constants the
  compiler knows without an `#INCLUDE`. A constant is folded into the code as an immediate
  operand (`LDA #$FF`). It takes no RAM and no bytes in the PRG beyond the instruction that
  uses it. `CONST` constants work the same way.
- **Line input.** `LINPUT L$` and `LINPUT #F, L$` read a whole line into a string, commas
  and quotes included. A line ends at CR, at LF, or at CR LF, so files from the X16, from Unix
  and from DOS all read the same. The ending is not stored. After a CR the runtime looks at
  the next byte, and drops it when it is an LF. That byte is held back for the next read
  of the same handle. A line longer than the string's `max` is cut, and the rest of the line
  is skipped.
  - `INPUT` reads one field: it stops at a comma or at the end of a line. For a number
    variable it converts the text.
  - From the keyboard, `INPUT` drops the rest of the line after its last variable. The
    KERNAL drops it anyway when anything is printed before the next read. `INPUT #` keeps
    the rest for the next read.
  - `EOF(F)` is 1 when the next read would return nothing.
- **Print items.** A `PRINT` item is a number, which prints in decimal, or a string.
  `PRINT` follows MS BASIC, not CBM BASIC, because the X16 screen is 80 columns:
  - A number prints with a space for its sign before it and a space after it.
    `PRINT 1; 2` prints ` 1  2 `.
  - `;` joins two items. Two items with nothing between them are joined the same way.
  - A comma moves to the next 14-column print zone: columns 0, 14, 28, 42 and 56. From
    column 56 on, a comma ends the line instead.
  - A trailing `;` or comma leaves the cursor on the line.
  - The zone comes from the screen cursor (KERNAL PLOT). `PRINT #` will keep its own column.
  - MS BASIC also starts a new line when a number does not fit before the edge. UXCBASIC
    does not, yet.
- **Library procedures.** Copy, fill, compare and sort are library `SUB`s written in UXCBASIC,
  not commands.

**Options and constants.**
- `CONST NAME AS type = value` makes a named constant. Several go on one line, separated by
  commas, as in `DIM`. The value is a constant expression.

  ```
  CONST MAX_LEN AS UBYTE = 80
  CONST ROWS AS UBYTE = 2 * 30, COLS AS UBYTE = MAX_LEN + 1
  CONST BASE AS UWORD = $9F20
  CONST BIG AS UWORD = 1000
  ```

  - A number `CONST` with no `AS` stops the compile with `MISSING AS: NAME`.
  - The type sets the range. A `UBYTE` over 255 stops the compile with
    `TOO BIG FOR A BYTE: NAME`.
  - A `$` name or `AS STRING` makes a string `CONST`. Its value is string literals, `CHR$(n)`
    and other string `CONST`s, joined by `+`.
  - A value that is not a constant expression stops the compile with `VALUE NOT A CONSTANT`.
  - The constant belongs to the `SUB` or namespace it is in. A namespace body may hold `CONST`,
    and `BIND` can name a `CONST`.
  - A number `CONST` is used like a number. It folds into the code and takes no RAM and no PRG
    bytes.
  - An assignment to a `CONST` stops the compile with `NOT A VARIABLE: NAME`.
  - `CONST` is a reserved word.

- `#DEFINE` sets compiler options only. Its names start with `UXC.`:
  - `UXC.OBJECT "X.PRG"`: the output file name.
  - `UXC.LIST`: also write a `.LST` file.
  - `UXC.NOSTUB`: leave out the BASIC `SYS` line.
  - `UXC.ORG $xxxx`: the start address.
- `#INCLUDE "FILE"` reads another source file in place (done 2026-10-11: LX.INCLUDE.FIND in
  src/UXC-LEX.BL, tests INCLUDE and ERRINCLUDE). One level: an included file cannot include
  another. An error in it reports the `#INCLUDE` line, with `(FILE n)` after the message.

## 2. The compiled program

**PRG layout** (default origin `$0801`):

```
$0801  BASIC stub "10 SYS 2061"  (left out with UXC.NOSTUB; the code then starts at UXC.ORG)
       startup: set up zero page, JMP to the first statement
       user code
       runtime routines this program uses, and nothing else
       system table: one JMP per KERNAL entry used
       string literals, then variables with their start values
--- end of file ---
       array and string space (not in the file; each string's max byte is set at startup)
```

- Code goes through the system table to reach the KERNAL, and nothing calls `$FFxx` directly.
  A port to the new machine rewrites only that table.
- Code plus data must end below `$9F00`. The array and string space must also end below
  `$9F00`.

**Zero page at run time.**

| Address | Use |
|---|---|
| `$02–$21` | KERNAL `r0–r15`. The runtime uses these as scratch between KERNAL calls |
| `$22–$2F` | runtime pointers and temporaries |
| `$30–$4F` | expression stack: 16 words, indexed by X |
| `$50–$7F` | free for the user (`ASM`, `POKE`) |

**Value passing.** A `BYTE` value goes in A. A `WORD` value, or the address of a string or an
array, goes in A (low byte) and Y (high byte). Arguments are stored into the `SUB`'s own
parameter variables before the `JSR`. A `SUB` returns its result in A, or in A and Y.
A `SUB`'s expressions use the expression stack above its caller's, and the depth is not
checked at run time.

## 3. The compiler

**Input.** `pyuxc/pyuxc.py` is the command line:

```
python pyuxc/pyuxc.py FILE.UXB [-I FOLDER]... [-o FOLDER] [--result FILE] [--keep-subs] [--keep-vars]
```

- `FILE.UXB` compiles to `FILE.PRG`, the source's name in capitals, in the `-o` folder. The
  default is the source's folder. `HELLO.UXB` writes `HELLO.PRG`.
- `#INCLUDE` looks in the source's folder, then in each `-I` folder in order. The libraries are
  in `lib/` at the repo root.
- `--keep-subs` keeps every `SUB` and `FUNCTION`, as `#KEEP ALL` does. `--keep-vars` keeps every
  global variable, array and string literal.
- pyuxc prints the compiler's screen lines, then one result line:
  `OK,<prg>,<bytes>`, with a `,REMOVED <n> SUBS <m> BYTES`, `,REMOVED <n> VARS <m> BYTES` or
  `,REMOVED <n> STRINGS <m> BYTES` field for each kind of thing left out, or
  `ERROR,<line>,<message>`. The message may hold commas. `--result FILE` writes the line to
  FILE as well.
- The exit status is 0 on success, and 1 on a compile error or a bad command line.
- The source may use CR, LF or CR LF.

Every other option comes from `#DEFINE UXC.*` lines in the source.

**Templates.**
- Code templates and runtime routines are 65C02 source in `tpl/`. `tpl/UXDOS/` holds the 6502DOS
  versions of `API.ASM`, `R-FILE.ASM` and `SYS.ASM`. `tpl/MKTPL.PY` assembles them with 64tass
  into two tables: `tpl/UXDOS/UXC.TPL.BIN`, which pyuxc loads, and `tpl/UXC.TPL.BIN`, for the
  stock ROM, which only `attic/gpc/pyuxc/compare.py` uses. The records of both tables must have
  the same ids; MKTPL stops when they do not. A table is data the compiler loads, so the
  self-hosted compiler uses it too. `tpl/MACROS.ASM` holds the format and the macros that write
  it.
- There are three kinds of record, all in one table:
  - `T_` templates, copied inline for each use.
  - `R_` runtime routines, placed once at the end of the program.
  - `S_` system table entries. The 6502DOS table's, in `tpl/UXDOS/SYS.ASM`, call the 6502DOS
    API.
- A record's id is its place in the table. `tpl/UXC.TPL.IDS` lists them.
- The file is a header (`"UXT"`, version, count, index offset), the records, then an index of
  one word per record.
- A record is its code length, its fixup count, its code, then its fixups. A fixup is three
  bytes: offset, kind, argument.

| Kind | Effect | Argument |
|---|---|---|
| `ABS` | the word at the offset += the slot's value (the code holds the addend, as in `S0+1`) | slot |
| `LO` / `HI` | the byte at the offset = the slot's low or high byte | slot |
| `SELF` | the word += the address the record is placed at | — |
| `REC` | the word += the address of another record, which is linked too | record id |

- A slot is an operand the compiler passes to a template: a variable, a string, a label or a
  constant.
- Linking a record links every record its `REC` fixups name, so a program carries only the
  routines it uses.
- An expression's value is in A (a BYTE), or in A and Y (a WORD or an address). Assignment is
  a load template then a store template.
- This is asm, so each new template is agreed with the user before it is written.

**One pass, then link.**
1. Each line is tokenised and parsed. The compiler emits code by copying template bytes into the
   code buffer. Each absolute reference becomes a fixup entry: a variable, a string, a label, a
   runtime routine, or a system table entry.
2. Forward jumps from `IF`, the loops and `GOTO` go on a fixup list, which is resolved when their
   target is reached.
3. At the end, the compiler lays out the sections in section 2 and appends the runtime routines
   that were used. It then resolves every fixup, writes the PRG, and optionally writes the
   `.LST`.

**Compiler memory.** pyuxc keeps the GPC UXC's banks, each a `bytearray` of 8,192 bytes.
- The code buffer is `K_CODE_BANKS`, 5 banks: a program's code is at most 40,960 bytes. Past
  that the compile stops with `PROGRAM TOO BIG`.
- The symbol table is `K_SYM_BANKS`, 4 banks, and the fixups `K_FIX_BANKS`, 8 banks: 8,192 fixups of 8 bytes.
- The program and its arrays must end below `K_TOP`, `$9F00`, or the link stops with
  `PROGRAM TOO BIG`.

**Errors.**
- The first error stops the compiler. It prints `?<ERROR> IN <line>` and the line of source.
- The result line is then `ERROR,<line>,<message>`.

**Source files.** The compiler is in `pyuxc/`, one module a part. `pyuxc/README.md` maps each
module to its GPC source.

| File | Part |
|---|---|
| `pyuxc.py` | the command line and the compile |
| `uxc_defs.py` | the constants, all named `K_*` |
| `uxc_lex.py` | the source file and the tokens of a line |
| `uxc_sym.py` | the symbol table: 256 hash buckets, then 32-byte records |
| `uxc_code.py` | the template table, the code buffer, the string literals, the fixups, and `emit` |
| `uxc_link.py` | the link step and the PRG writer |
| `uxc_stmt.py` | the statements |
| `uxc_tpl.py` | the template ids, read from `tpl/UXC.TPL.IDS` |

- `emit` copies a record into the code buffer. A slot that holds a constant goes into the code
  at once. Any other slot becomes a fixup: a code offset, a kind, a section and a value.
- The sections are code, record, string, variable and label.
- A `REC` fixup adds the record to the list of routines.
- At the end of the source, the link step emits each listed routine in turn. Each one can add
  more routines to the list. The strings and the variables follow the routines. Every fixup
  is resolved last, so a forward reference needs nothing special.
- `uxc_tpl.py` gives the compiler its record ids. The compiler stops when `UXC.TPL.BIN` holds a
  different number of records.

**Tests.** `tests.py [NAME ...] [--update]`, in `UXCBASIC/`, or
`RUNUXCTESTS.BAT` at the repo root, runs the tests in `tests/`. Each test is a source
`NAME.UXB` and its expected output `NAME.OUT`, with `NAME.IN` for typed input.
- pyuxc compiles the source into `build/uxctests` of the repo root, with `#INCLUDE` looking in
  `tests/`.
- A source that compiles runs headless on `build/6502DOS.ROM` in x16emu: the program is
  `TEST.COM` on a new SD card image, and `RUN TEST.COM` is typed at the prompt. The lines of
  `NAME.IN` are typed after it. What the program printed, up to the prompt, is compared with
  `NAME.OUT`.
- A source that does not compile is compared by its result line. An error test's `NAME.OUT`
  is the one line `ERROR,<line>,<message>`.
- A run fails when the prompt is not back within 5 s.
- `--update` writes `NAME.OUT` from what the test gave. Read it before you keep it.

**Listing (`.LST`).** One row per emitted template, in the form `addr  bytes  ; source line`.

**Help.** `help/MKHELP.PY` builds `help/HELP-TXT/` from `help/UXC-HELP.md`, and each program
in `samples/` gets an index row. No program in this repo reads `HELP-TXT/`; the GPC viewer,
`UXC.HELP.BASL`, is in `attic/gpc/src/`.

## 4. Order of work

Each step ends with a build, a run and a check.

1. **Template format.** Done on 2026-10-09. The 64tass macros, the `UXC.TPL.BIN` layout and a
   first set: start and end, loads and stores, the expression stack, `POKE`, `PEEK`, and
   `PRINT` of a string, a BYTE and a WORD.
2. **Compiler skeleton in GPC.** Done on 2026-10-09.
   - It has every part: `UXC.INPUT`, the line reader and tokeniser, the symbol table in banked
     RAM, the code buffer and fixups, the link step and the PRG writer.
   - It compiles enough to test them: comments, `DIM`/`VAR` of BYTE and WORD names,
     `name = constant`, `PRINT` of strings, numbers and variables, `END`, and labels.
   - `tests/SKEL.UXB` compiles in about 1 s to a 348-byte PRG, which prints the right
     values.
3. **Test harness.** Done on 2026-10-09.
   - `tests.py` and `RUNTESTS.BAT`, as described under **Tests**.
   - 19 tests: the skeleton, `PRINT` forms, names, the three line endings, and one test for
     each compile error the skeleton can give. They all pass in about 25 s.
   - The tests found that a reserved word with a mark was taken as a name. It is now
     reserved: `PRINT$` is not a name.
   - Later on 2026-10-09 `PRINT` moved to MS BASIC spacing and print zones. COMMAS is the
     20th test.
4. **Commands**, added in this order:
   1. `DIM`/`VAR` for `BYTE` and `WORD`, expressions, `POKE`/`PEEK`, `PRINT` (done
      2026-10-09: tpl/T-EXPR.ASM, R-MATH.ASM, R-ERROR.ASM, src/UXC-EXPR.BL)
   2. `IF`, `DO`/`LOOP`, `FOR`, `REPEAT`, `EXIT`, `CONTINUE`, `GOTO` (done 2026-10-09:
      tpl/T-FLOW.ASM, src/UXC-COND.BL, src/UXC-FLOW.BL; EXPR and COND run from bank 20, STMT
      and FLOW from bank 21, both in UXC.OVL)
   3. `SUB`/`CALL`/`RETURN` (done 2026-10-09: tpl/T-CORE.ASM T_RTS, T_POPB_V, T_POPW_V,
      src/UXC-SUB.BL in bank 22). The source is read twice: the first pass declares every
      `SUB` from its header, so a call may come before its `SUB`. A body that reaches its end
      returns 0 from a `SUB` with a value. Arguments with a `(` in them are pushed and popped
      into the parameters just before the `JSR`.
   4. arrays, strings, `INPUT`, `GETKEY`, in three parts:
      1. 4.4a: arrays, `GETKEY()`, `ERRORS ON`/`ERRORS OFF` (done 2026-10-09:
         tpl/T-ARRAY.ASM). An array is `DIM B(10)`, elements 0 to 9, BYTE or WORD. The
         arrays sit after the program, outside the file, and the startup code clears them. A
         constant index is checked at compile time. Any other index is checked at run time,
         except under `ERRORS OFF`.
      2. 4.4b: strings (done 2026-10-10: tpl/T-STRING.ASM, tpl/R-STRING.ASM). A string is a
         `[max][len][data]` block in BSS. All six compares, `+`, `LEN`, `ASC`, `CHR$`. A
         STRING parameter is passed by reference. A SUB that returns a STRING is done
         2026-10-10 (test STRRET). Not done: string arrays, a start value.
      3. 4.4c: `INPUT`, `LINPUT` (done 2026-10-10: R_INPUT in tpl/R-STRING.ASM). From the
         keyboard only. `INPUT "prompt"; a, b$` prints "? ", and fields split at commas.
         `LINPUT` takes a whole line. Not done: an array element as the variable.
   5. file commands
      1. 4.5a: `OPEN`, `CLOSE`, `PRINT #`, `NOFILE` (done 2026-10-10: R_FILE in
         tpl/R-FILE.ASM). The mode must be `O.READ`, `O.WRITE` or `O.APPEND`, written as
         the argument. In `PRINT #`, a comma writes ",". Unit 8 only.
      2. 4.5b: `LINPUT #`, `INPUT #`, `EOF` (done 2026-10-10: R_FIN in tpl/R-FILE.ASM, a
         one-byte read-ahead per handle). Handles 0–2 cannot be read in v1.
      3. 4.5c: `READ`, `WRITE` (done 2026-10-10: R_FREAD and R_FWRITE in tpl/R-FILE.ASM).
         The address is any WORD expression. Bytes move as they are.
      4. 4.5d: `DIR` (put off by the user, 2026-10-10: it may become code in a `DIR`
         namespace rather than a statement).
   6. `SYS`, `ASM`, in two parts:
      1. 4.6a: `ASM` (done 2026-10-10: src/UXC-ASM.BL in bank 22). `ASM $A9, 65` puts the
         bytes in on one line. `ASM` alone opens a block that `END ASM` or `ENDASM` closes,
         with a list of items on each line. An item is a constant or `@name`: 0–255 is one
         byte, 256–65535 and `@name` are two, low byte first. `@name ± constant` is folded to
         an address everywhere. The code must keep X.
      2. 4.6b: `SYS` (done 2026-10-10: R_SYS in tpl/SYS.ASM, AS.SYS in bank 22). The
         address is any WORD expression. A, X, Y and P pass through `$030C`–`$030F`, P
         with `AND #$F3`. SYS keeps the program's X.
   7. names for memory, in three parts:
      1. 4.7a: BYTE by default (done 2026-10-10: tests TYPEDEF and ERRBANG). The `!` mark is
         gone. Step 4.9 replaces the default: a number needs `AS`.
      2. 4.7b: `DIM ... AT` (done 2026-10-10: NM.AT in src/UXC-NAME.BL, flag K.SY.FIXED;
         tests DIMADDR, ERRATCONST and ERRATKIND). `DIM REG_P AT $030F` puts a BYTE or WORD
         variable at a fixed address. The address is a constant expression. The variable
         takes no space, and each access is an absolute load or store in section
         K.SEC.CONST. Not done: an array or a string at an address, `DIM ... AT ZP`.
      3. 4.7c: pointers by name (user; done 2026-10-10: EX.ADDROF, EX.PEEK and SM.CONTENTS;
         tests POINTERS, ERRADDROF and ERRCONTENTS). `AddrOf(name)` is `@name`, and `@name`
         stays. `ContentsAt(a)` reads the BYTE at `a`, as `PEEK(a)` does, and
         `ContentsAt(a) = v` writes it, as `POKE a, v` does. `ContentsAtW(a)` reads and
         writes a WORD with T_PEEKW and T_POKEW. A constant address or `AddrOf(name)` is one
         load or store. `PEEK` and `POKE` stay. This replaces the to-do item `MEM` and
         `MEMW`.
   8. `SUB` and `FUNCTION` split; `FUNCT` and `ENDFUNCT` built-in `BIND`s (done 2026-10-13:
      src/UXC-SUB.BL; tests FUNC1, ERRSUBTYPE, ERRFUNCEND, ERRSUBENDF and ERRFUNCOPEN).
   9. A number needs `AS`, and `%` is not a mark (done 2026-10-13: LX.WORD.END in
      src/UXC-LEX.BL, NM.TYPE.NAME in src/UXC-NAME.BL, ER.MISSING.AS in src/UXC.BASL; tests
      ERRNOAS, ERRNOASPARAM and ERRPERCENT). The type words are `UBYTE`, `BYTE`, `UWORD` or
      `UINT`, `WORD` or `INT`, `LONG`, `ULONG`, and `STRING`.
5. **UXCEDIT compile relay** for UXCBASIC (decided by the user, 2026-10-10). Done on
   2026-10-10, in four parts:
   1. 5a: the user disk (done 2026-10-10). It is part of the GPC build, in `attic/gpc`.
      `publish` in `attic/gpc/build.py` copies the PRG and OVL of each program it builds,
      with the files it reads at run time, to `attic/gpc/disk/`. `RUNEDIT.BAT`,
      `RUNUXC.BAT` and `RUNHELP.BAT` in `attic/gpc` run from `disk/` with
      `run.py NAME --disk --window`. Nothing uses the attic.
   2. 5b: UXC chains (done 2026-10-10: UI.CHAIN in src/UXC.BASL; test CHAIN, with
      `tests/CHAIN.NEXT`). `UXC.INPUT` gains an optional line 3: the program to load next.
      UXC loads it after it writes the result line, on `OK` and on `ERROR`. With no line 3
      UXC ENDs as before. In `tests/`, a `NAME.NEXT` file names line 3, and the test
      compares the output of the program loaded.
   3. 5c: F5 in the editor compiles the active document (done 2026-10-10: TURBO.BUILD and
      TURBO.BUILD.HOP in src/UXCEDIT/UXCEDIT.BASL; Build, Compile on the menu). It saves the
      modified documents. F5 on an Untitled document asks for a name first. A save that
      does not happen stops the build on its document. It then deletes `UXC.RESULT`, writes
      `UXC.INPUT` (the source, `UXC.RESULT`, `UXCEDIT.PRG`) and `UXCEDIT.RUN`, and loads
      `UXC.PRG`. `UXCEDIT.RUN` holds the number of the active document, 0 to 2, then six
      lines for each document: its name, `ASCII` or `PETSCII`, its cursor line, cursor
      column, top line and left column. An Untitled document has an empty name line.
      - Open question: the hop loads `UXC.PRG` from the current directory. After the file
        picker moves into a subdirectory, the load fails.
   4. 5d: the editor start (done 2026-10-10: TURBO.RESUME and TURBO.RESULT.SHOW in
      src/UXCEDIT/UXCEDIT.BASL; help topic "Compiling from UXCEDIT"). When `UXCEDIT.RUN`
      exists, the editor reopens the documents, reads `UXC.RESULT` and deletes
      `UXCEDIT.RUN`. On `ERROR` it puts the cursor on the line and shows a message box
      titled "Compile error" with `Line N` and the message. On `OK` it shows a message box
      titled "Compiled" with the PRG name and its size in bytes. With no `UXC.RESULT` the
      box says "Compile gave no result". The result line splits at its first two commas
      only. The message may hold commas.
   - The hop: a program clears the screen, prints `LOAD"NAME.PRG",8,1` on the third row,
     and homes the cursor. It puts Return, `RUN:` and Return into the key buffer with
     `kbdbuf_put` through `GP.CALL`, with ROM bank 0, and ends. `READY.` lands on the
     second row, so the first Return runs the LOAD line. `RUN:` is typed after the LOAD's
     `READY.`. It needs no asm.
   - A crash inside UXC writes no result and loads nothing. The user is left at `READY`.
   - Not in v1: running the compiled program. See **Back to the editor** in section 5.
6. **Self-host:** rewrite the compiler in UXCBASIC, and check that it builds itself
   byte-for-byte.
7. **Later:** a small line assembler inside the compiler. It would allow mnemonics in `ASM`
   blocks, and template edits on the X16 with no host.

## 5. Open points

Settled on 2026-10-09:
- `SUB` … `ENDSUB` has no value. `FUNCTION` … `ENDFUNCTION` has a value, typed by `AS`:
  `FUNCTION FOO() AS UWORD`. A STRING `FUNCTION` may take the `$` mark: `FUNCTION FOO$()`
  (decided 2026-10-13).
- A number is typed by `AS` only. A string takes the `$` mark or `AS STRING`. A number with
  no `AS` is a compile error (decided by the user, 2026-10-13, step 4.9). `DIM` and `VAR` are
  both valid, with several names per line.
- Strings are Pascal style, `[max][len][data]`. Strings and arrays are passed to a `SUB` as
  pointers.
- File I/O uses Unix-style handles. `READST` is gone. Modes and results are built-in constants.
- `FOR` ends when the counter passes `TO`.
- The `$` mark is part of the name. A name declared with `AS` has no mark.
- Every variable must be declared.
- `DIM B(10)` makes 10 elements, 0–9.
- v1 string operations as listed under **Strings**.
- `BYTE` and `WORD` (`INT`) are done, and signed. `LONG` and `ULONG` are done (§5 "More
  types", step 3).
- File modes are the built-in names `O.READ`, `O.WRITE` and `O.APPEND`. `OPEN` returns
  `NOFILE` ($FFFF) on failure.
- The line forms `PRINT #`, `INPUT #`, `LINPUT #` and `EOF` sit beside `READ` and `WRITE`.
- `LINPUT` ends a line at CR, LF or CR LF.
- No character literal. `ASC("A")` is folded at compile time.
- Whole-line comments: `REM`, `'`, `;`, `##`, `//`. Trailing comments: `REM` and `'` only.
- `PRINT` spacing and commas follow MS BASIC (decided 2026-10-09).
- Truth is 0 or nonzero; `NOT` is logical; `AND`/`OR`/`XOR` are bitwise (option C, decided
  2026-10-09).
- Run-time errors: division by zero always stops the program; `ERRORS ON`/`ERRORS OFF` switch
  the inline checks at compile time, default on (decided 2026-10-09).
- Loops (decided 2026-10-09, built in step 4.2):
  - `DO [WHILE|UNTIL c]` ... `LOOP [WHILE|UNTIL c]`. The test can be at the top, at the bottom,
    or absent (a loop that runs until `EXIT DO`). There is no `WHILE` ... `WEND` (dropped
    2026-10-09): it is the same loop as `DO WHILE c` ... `LOOP` with the same code, so it gave
    only a second spelling. A top test is compiled at the bottom (one `JMP` to the test on entry), so a top test and a
    bottom test cost the same per pass.
  - `FOR v = a TO b [STEP k]` ... `NEXT [v]`. `STEP` must be a constant. The body runs zero
    times when the range is empty (as in Prog8, not MS BASIC). The end test is done before the
    step, so `FOR I = 0 TO 255` stops and does not wrap.
  - `REPEAT n` ... `END REPEAT` runs the body n times with a hidden counter that counts down;
    `n` = 0 runs zero times. `REPEAT` with no count runs until `EXIT REPEAT`. `REPEAT` ...
    `UNTIL c` (the BBC BASIC form) is not accepted, so BBC code fails to compile instead of
    meaning something else. There is no
    loop variable, so it is the cheapest counted loop (about 8 cycles of overhead per pass
    against about 15 for a `BYTE` `FOR`). Each nesting level needs its own hidden counter; `X`
    cannot be the counter because it is the expression-stack pointer.
  - `EXIT DO`, `EXIT FOR`, `EXIT REPEAT` leave the named loop. `CONTINUE` jumps to
    the test (or the step) of the innermost loop.
  - No `unroll`.

To do, not designed yet:
- **ASCII, not PETSCII** (user, 2026-10-09). The language, the compiler and the compiled
  programs use ASCII and depend on no PETSCII: source text, string literals, `CHR$` and `ASC`,
  `PRINT` and the key codes `GETKEY()` returns. On the X16 a program runs in CP437:
  - At startup the program sends `$0F` to `CHROUT`, which turns on ISO mode. `CHROUT` then
    writes each byte as its own screen code, and `GETIN` returns ASCII.
  - It then calls `screen_set_charset` (`$FF62`) with A = 7, which loads the CP437 font over
    the ISO font. CP437 needs ROM R47 or later.
  - Before the switch, startup keeps the byte at `$0372`. Its low 6 bits are the active
    charset number, and bit 6 is set in ISO mode. It is not documented, and APPHELP in the
    Blitz compiler relies on it.
  - Every exit puts the screen back: `END`, the end of the program, and a run-time error
    after its message. The exit calls `screen_set_charset` with the kept byte AND 63, then
    stores the whole kept byte to `$0372`. `screen_set_charset` alone leaves bit 6 set.
  - When the kept mode is not ISO, the exit first converts every code on the screen to the
    PETSCII screen code of the same character, for the kept charset, so the text stays
    readable. Upper/graph shows lower case as upper case.
  - This code sits in `tpl/SYS.ASM` and is marked CBM only. The new workstation has no CBM
    mode, and the code is removed there.
  - In ISO mode the codes `$00–$1F` and `$80–$9F` are controls, so `PRINT` cannot show the
    CP437 glyphs at those codes.
  - The tests read the `CHROUT` echo, so `run.py` and `uxc.py` run x16emu with `-echo iso`.
  - Still to decide: whether the compiler and UXCEDIT switch too.
- **Back to the editor.** A key at `READY` that reloads UXCEDIT after the user tests a PRG.
  It is a key not pressed by chance, for example Ctrl+Shift+F5. Not established: whether the
  KERNAL lets a program reprogram such a key.
- **Passing variables between programs.** A built-in, standard way for one UXCBASIC program to
  hand variables to another UXCBASIC program through a banked RAM area, for example when one
  program loads and runs the next. It is part of the language, not a library convention.
  Still to decide: the bank and layout, how a program names what it shares, and how a type or
  size mismatch is caught.
- **Removing unused code** (user, 2026-10-09). By default the compiler leaves out code the
  program never uses: run-time routines nothing calls, `SUB`s and `FUNCTION`s nothing calls,
  and code that can never be reached. A compile-time instruction keeps a named section anyway,
  for example a routine that only another program or a `SYS` call reaches. Still to decide:
  the syntax of the keep instruction, what a section is (a routine, a block of lines, or a
  whole file), and whether the compiler reports what it removed and the bytes saved.
  - It comes before any library of include files (user, 2026-10-10). Without it every `SUB`
    in an included file is compiled into every PRG, called or not.
- **Removing unused variables** (user, 2026-10-09). The compiler gives no address to a
  variable or array that nothing reads or writes. This saves RAM, not PRG bytes, because
  variables sit after the program. The compiler warns `UNUSED VARIABLE name`.
  - A variable is always kept when it is `DIM ... AT`, when `@name` is taken, or when a `BIND`
    in use names it.
  - An address is now set at the `DIM`. Stripping needs the use count first, from a prescan
    pass, or addresses set at the end with fixups.
  - Still to decide: whether a variable that is written and never read loses its stores too.
    Only a plain variable could, because a store to an `AT` variable has a side effect.
- **Debugging** (user, 2026-10-09). Three parts, built in this order.
  - **Map file.** The compiler writes `PROG.MAP`, with the address of each source line and
    each name. It costs nothing at run time. A run-time error such as
    `?BAD SUBSCRIPT ERROR AT $0A3F` is looked up there to find the line. Box16 can load the
    names into its debugger.
  - **`STOP`.** It compiles to `BRK`, which enters the X16 monitor to show the registers and
    memory. It costs 1 byte.
  - **`DEBUG ON` and `DEBUG OFF`.** They work as `ERRORS ON` and `OFF` do: the switch follows
    the source, not the run. Code inside a `DEBUG ON` region stores the line number before
    each statement, about 8 bytes a line, so a run-time error reports `AT LINE n`.
    `ASSERT condition` stops the program when the condition is false. `TRACE` prints each
    line number as it runs. Outside a `DEBUG ON` region, `ASSERT` and `TRACE` compile to
    nothing.

    ```
    DEBUG ON
    FOR I = 0 TO 9
      ASSERT I < 10
      B(I) = I
    NEXT
    DEBUG OFF
    ```

  - Still to decide: the map file format, whether `DEBUG` is a `#DEFINE UXC.*` option as well,
    and the text of an `ASSERT` failure.
- **Code for a set memory address, as in Prog8** (user, 2026-10-09). Prog8 has `%address`,
  `%output raw|prg` and `%launcher none`, and lets a variable sit at a fixed address
  (`&ubyte border = $d020`). Here `UXC.ORG` and `UXC.NOSTUB` already set the start and drop
  the `SYS` line. `DIM BORDER AT $9F2C` puts a BYTE or WORD variable at a fixed address
  (step 4.7b). Still to decide: a raw output with no load address; a separate address for
  the variables (for code in ROM or in a banked window at `$A000`); arrays and strings at a
  fixed address; and how the compiler checks that the program fits below its top.
- **Variables in zero page** (user, 2026-10-09). `DIM I AT ZP` puts a variable in the free
  zero page at `$50–$7F`, for smaller and faster code. The compiler stops with an error when
  that area is full. This replaces Prog8's `%zeropage` modes: the runtime keeps to `$22–$7F`,
  so every program can return to BASIC. Still to decide: whether `@` of a zero-page variable
  is allowed, whether arrays and strings may go there, and how this shares `$50–$7F` with
  `ASM` and `POKE`. `DIM ... AT ZP` takes only `$50–$7F`. The runtime uses `$22–$4F`, and the
  6502DOS kernel uses `$80–$FF`.
- **Split WORD arrays, as in Prog8** (user, 2026-10-09). Prog8's `splitarrays` keeps a
  `WORD` array as two byte arrays, the low bytes then the high bytes. The index is used as it
  is, with no doubling, so an element is read with `LDA lo,Y` and `LDA hi,Y`. Such an array
  has at most 256 elements. Still to decide: whether it is the default or an option, and what
  `@name` gives for a split array.
- **`ENUM`** (user, 2026-10-09; numbering done 2026-10-11: NM.ENUM in src/UXC-NAME.BL, tests
  ENUM and ERRENUMOPEN). An `ENUM` is a namespace whose lines are constants, numbered from 0.

  ```
  ENUM STATE
    READY            ' 0
    RUNNING          ' 1
    BLOCKED = 10     ' 10, and the count goes on from here
    DONE             ' 11
  END ENUM
  IF S = STATE.BLOCKED THEN PRINT "WAIT"
  ```

  - A member is a constant and folds into the code as an immediate operand. An `ENUM` takes no
    RAM and no bytes in the PRG.
  - A line may hold several members separated by commas: `RED, GREEN, BLUE`.
  - `= value` sets a member's number. The members after it count on from it.
  - The members are `BYTE` when every value fits in 0 to 255. When one passes 255, the `ENUM`
    and every member become `WORD`.
  - Inside the `ENUM` a member is used bare. Outside it is qualified: `STATE.READY`.
  - `ENDENUM` is the same as `END ENUM`.
  - A member is a `CONST` record.
  - Typed enum parameters and variables (user, 2026-10-11; `ENUM.` prefix the user,
    2026-10-18; done 2026-10-18: `nm_type_enum`, `nm_enum_scan` and `sb_call_member` in pyuxc,
    tests ENUMAS and ERRENUMMEMBER): `SUB FOO(N AS ENUM.STATE)` and `DIM S AS ENUM.STATE`.
    Outside the ENUM's namespace the name is qualified: `AS ENUM.GFX.MODE`. The value is a
    `BYTE` or `WORD`, as for the members. A constant passed to it must be a member of that
    `ENUM`. A member's record owner (+25) names its `ENUM`, and the check reads that owner. A
    member of another `ENUM` is a compile error. A plain variable passes unchecked. No check
    runs in the program, so it costs no bytes.
    - The first pass makes the record of each `ENUM` outside a SUB body (`K_SY_SCANNED`), so
      that a SUB header can name it. Its members are made in the second pass.
    - The first pass gives such a parameter a `BYTE`. An `ENUM` that a parameter or a
      FUNCTION result uses stops the compile with `TOO BIG FOR A PARAMETER` when a member
      passes 255.
    - A bare member in an argument (done 2026-10-18: `ex_enum_member`, `g.sb_call_enum`,
      test ENUMBARE): `SHOW(BLOCKED)`. A name without a dot is first looked for among the
      members of the parameter's `ENUM`; `sb_nest` clears the entry of each new depth.
  - Bare members in an argument (user, 2026-10-11). When an argument expects an `ENUM`, a bare
    name is looked for in that `ENUM` first, then as usual. The compiler gives its built-ins
    their own `ENUM`s the same way: `POS(POS.COL)`, `POS(COL)` and `POS(0)` all work.
    `EX.POS.AXIS` then takes any constant 0 or 1.
  - The order: `CONST`, then `ENUM` numbering, then `AS` enum, then bare members.
- **`CONST`** (user, 2026-10-09; done 2026-10-11: NM.CONST in src/UXC-NAME.BL, tests CONST
  and ERRCONSTBIG). A constant kind in the symbol table, which the expression parser folds as
  it does a number. See "Options and constants" in section 1. `NM.BODY` allows `CONST` in a
  namespace body.
- **`SHL`, `SHR`, `ROL` and `ROR`** (user, 2026-10-09). `<<` and `>>` exist. `SHL` and `SHR`
  are the same operators as words. `ROL` and `ROR` rotate within the left side's type, 8 bits
  for a `BYTE` and 16 for a `WORD`: the bits that leave one end come in at the other. All four
  have the precedence of `<<` and `>>`.

  ```
  B = $81 ROL 1      ' $03
  B = $81 ROR 1      ' $C0
  W = 1 SHL 15       ' $8000
  ```

- **`ON IRQ CALL name`** (user, 2026-10-09). Runs a `SUB` on each interrupt, such as a
  timer. Still to decide: the whole design. Known problems: the handler shares the runtime zero
  page `$22–$4F` with the main program and must save it, and a `SUB` has no stack frame, so
  the handler and the main program must not use the same `SUB`s. A call from the interrupt is
  not in the call graph, so it breaks the shared temps and locals.
  - XC=BASIC 3 has interrupts; review its code before the design (user, 2026-10-10). It is in
    `C:\dev\XCbasic\xcb-ext\xc-basic3-3.2.0-beta`: the runtime in `lib/irq/irq.asm` and
    `lib/irq/_x16.asm`, the compiler side in `source/statement/irq_stmt.d` and
    `source/statement/on_stmt.d`.

  ```
  SUB TIMERHANDLER()
    TICKS = TICKS + 1
  ENDSUB
  ON IRQ CALL TIMERHANDLER
  ```

- **Hardware registers as variables** (user, 2026-10-09; `DIM ... AT` done 2026-10-10, step
  4.7b). `VERA_DATA0 = 65` in place of `POKE $9F23, 65`. A store compiles to `LDA #65`,
  `STA $9F23`.

  ```
  DIM VERA_DATA0 AS UBYTE AT $9F23
  VERA_DATA0 = 65
  ```

  - The X16 names live in header files that ship with UXC, not in the compiler: `X16.UXH`,
    split by part if the symbol table needs it. Each holds a `NAMESPACE X16` of `DIM ... AT`
    and `CONST` lines. A program that does not `#INCLUDE` a header pays nothing. The header
    waits for `CONST`; `#INCLUDE` is built.
  - The virtual registers are words: `DIM R0 AS UWORD AT $02` through
    `DIM R15 AS UWORD AT $20`. A variable
    at a zero-page address is still reached with absolute addressing, 3 bytes an access.
  - Every name takes a 32-byte symbol record at compile time. About 115 fit in bank 22.

- **CPU registers as variables** (user, 2026-10-09; `SYS` done 2026-10-10, test SYSREGS;
  `DIM ... AT` done 2026-10-10, test DIMADDR). `SYS` works as X16 ROM BASIC does. It loads A,
  X, Y and P from `$030C`–`$030F` before the `JSR`, and stores them there after it. A
  program names the four bytes with `DIM ... AT`, and the header is to hold the line:

  ```
  DIM REG_A AS UBYTE AT $030C, REG_X AS UBYTE AT $030D
  DIM REG_Y AS UBYTE AT $030E, REG_P AS UBYTE AT $030F
  ```

  The carry is bit 0 of `REG_P`. The KERNAL sets it on an error, and some calls read it
  as an input. `PLOT` with the carry set reads the cursor:

  ```
  REG_P = REG_P OR 1
  SYS $FFF0
  PRINT REG_X, REG_Y
  REG_P = REG_P AND $FE
  SYS $FFC0
  IF REG_P AND 1 THEN PRINT "OPEN FAILED"
  ```

  - `SYS` loads P with `AND #$F3`, so a stray D or I bit cannot reach the call.
  - The four bytes are not cleared when the program starts. Set what the call reads.
  - The header is to add `CONST C_FLAG = 1`, `Z_FLAG = 2`, `V_FLAG = 64`, `N_FLAG = 128`.
  - Each `SYS` is 7 bytes: the address in A/Y and `jsr R_SYS`. R_SYS, 43 bytes in
    `tpl/SYS.ASM`, is linked once. It calls through `jmp (ZP_PTR)` and keeps X with
    `phx`/`plx`.
- **Namespaces and `BIND`** (user, 2026-10-09; done 2026-10-09: src/UXC-NAME.BL in bank 22,
  tests NS1, NS2 and five error tests). `NAMESPACE name ... END NAMESPACE` groups
  names. Inside it a name is used bare; outside it is qualified with a dot.

  ```
  NAMESPACE GFX
    DIM COLOR AS UBYTE
    SUB PLOT(X AS UWORD, Y AS UBYTE)
      POKE $9F20, COLOR
    ENDSUB
  END NAMESPACE
  GFX.COLOR = 5
  GFX.PLOT(10, 20)
  ```

  - A namespace may hold namespaces. A `SUB` may not hold a `SUB`.
  - A namespace body holds only `DIM`, `VAR`, `CONST`, `SUB`, `FUNCTION` and `BIND`, and no
    statements that run.
  - A `SUB`'s own names are local to it. Outside the `SUB`, `SHOW.N` stops the compile with
    `LOCAL TO A SUB: SHOW.N`.
  - `UXC` is a reserved namespace, for the `#DEFINE UXC.*` options.
  - A name is found in the `SUB`, then in each enclosing namespace, then in the main program.
  - `BIND` gives another name to a variable, a `SUB`, a `FUNCTION` or a namespace. It costs
    nothing at run time. The new name carries the same `$` mark as the target, or none. A
    `BIND` belongs to the scope it is written in.

    ```
    BIND G = GFX
    BIND P = GFX.PLOT
    BIND C = GFX.COLOR
    ```

  - In the symbol table a namespace is a new kind, and its owner is its parent. A record keeps
    only the last part of its name, so the 16-character limit is per part. `NM.FIND` splits a
    used name, walks the owners and follows `BIND`s. A declaration checks for a duplicate in
    its own scope only, with `SY.FIND`.
  - The first pass makes the namespace records too, so a `SUB` header is declared in its
    namespace. A `NAMESPACE` that names an existing namespace reopens it.
  - A dot always separates scopes, as in Prog8. A name is a letter, then letters, digits and
    `_`, then an optional `$`. `MY_COUNT_2` is one name; `MY.COUNT.2` is three.
  - The first part of a qualified name is found as a bare name is: in the `SUB`, then in each
    enclosing namespace, then in the main program. Inside `GFX`, `PLOT` and `GFX.PLOT` are
    the same.
- **Record types, `TYPE ... END TYPE`** (user, 2026-10-09; plan 2026-10-12). Not scheduled.
  The fields are the types UXCBASIC has: `BYTE`, `UBYTE`, `WORD`, `UWORD` and `STRING * n`.

  ```
  TYPE ITEM
    COUNT AS UBYTE
    PRICE AS UWORD
    NAME AS STRING * 10
  END TYPE
  DIM R AS ITEM, STOCK(20) AS ITEM
  R.COUNT = 5
  R.NAME = "BOLT"
  STOCK(3) = R
  STOCK(I).PRICE = STOCK(I).PRICE + 1
  PRINT STOCK(3).NAME
  ```

  XC=BASIC 3 (`source/statement/type_stmt.d`, `source/compiler/type.d`,
  `lib/core/stack/_udt.asm`):
  - A field line is `name AS type`. A field is of any type, a record included, but not an
    array.
  - A field's offset is the sum of the sizes of the fields before it. `X.Y.Z` adds the offsets
    down the chain.
  - A record is at most 64 bytes, because a copy goes through the 6502 stack.
  - `A = B` pushes every byte of `B` and pulls them into `A`. A record is passed and returned
    by value.
  - An array of records multiplies the index by the record size. The multiply is a shift when
    the size is a power of 2.
  - A field's address is the variable's label plus the offset. It is a constant unless the
    index is a variable.
  - A `TYPE` may hold `SUB`s, which reach the record as `THIS`.

  For UXCBASIC:
  - A field line is `name AS type`. The type is `BYTE`, `UBYTE`, `WORD` or `INT`, `UWORD` or
    `UINT`, or `STRING * n` with n from 1 to 255. A field has no mark and is not an array.
    `END TYPE` or `ENDTYPE` ends the `TYPE`.
  - A `BYTE` or `UBYTE` field is 1 byte and a `WORD` or `UWORD` field is 2. A `STRING * n`
    field is n + 2 bytes, the same block as a string variable: the max byte, the length byte,
    then the data. Every string routine works on a field.
  - A record is 1 to 255 bytes, so a field's offset fits in Y.
  - A `TYPE` is declared in the main program or in a namespace, not in a `SUB`. It comes before
    the first `DIM` that uses it.
  - `DIM R AS ITEM` makes a record. `DIM STOCK(20) AS ITEM` makes an array of 20. A record
    variable has no mark.
  - `DIM PSP AS PSPREC AT $0700` places a record at a fixed address, as `DIM ... AT` does for
    a variable (NM.AT, flag `K.SY.FIXED`). Its fields are fixed addresses. 6502DOS's PSP, system
    file table entry and FAT directory entry are records at fixed addresses.
  - A 32-bit field, such as a FAT file size, is a `LONG` or `ULONG` field.
  - A field goes wherever a variable of its type goes: in an expression, left of `=`, in
    `INPUT` and `LINPUT`. `@R.PRICE` gives the field's address and `@R` the record's.
  - `A = B` copies the bytes when both are of one `TYPE`. Two `TYPE`s stop the compile with
    `TYPE MISMATCH`. A record is in no other expression: no compare and no `PRINT`.

  Code:
  - `R.PRICE` and `STOCK(3).PRICE` are fixed addresses: the variable, plus the index times the
    record size, plus the offset. Each compiles as a plain variable does.
  - `STOCK(I).PRICE` indexes as a `WORD` array does, from the base `STOCK` plus the offset. The
    index is checked against the count and multiplied by the record size: shifts for a power of
    2, else a shift-and-add or `R_MULW`.
  - A string field of an element with a variable index is reached through its address, held
    in a hidden `WORD`. A `STRING` parameter's block is reached the same way.
  - `A = B` on two fixed addresses is an inline loop of 11 bytes: `LDY #size`, `LDA B-1,Y`,
    `STA A-1,Y`, `DEY`, `BNE`. With a variable index it calls an `R_*` copy routine.
  - A record parameter, as in `SUB SHOW(P AS ITEM)`, is passed as its 2-byte address, as a
    `STRING` is. `P.PRICE` is `LDY #offset` then `LDA (pointer),Y`.
  - Trap: the max byte of each string field is set at startup, in every element, by T_RMAX:
    a loop for each string field, over the count, with the record size as the stride. A record
    at a fixed address gets no max.

  Symbol table:
  - A `TYPE` is a new kind of record, with its size as its value. Each field is a record of
    another new kind, owned by its `TYPE`: +3 is its type, +4 its offset, and the count is a
    string's max.
  - A record variable's type byte, +3, is 16 plus the `TYPE`'s number. A table maps the number
    to the `TYPE`'s record. This allows 240 `TYPE`s and needs no new byte in the record.
  - Type codes stop being sizes. Four routines use the code as the size: `SM.DIM`, `EX.INDEX`,
    `SM.LET.ELEMENT` and `SB.PARAMETER`. Each calls a size routine instead. `EX.LOAD` and
    `EX.SPILL` test the width instead of `>= K.TY.WORD`. This change comes first, changes no
    behaviour and passes the full suite.

  Names:
  - `R.PRICE` lexes as one name, as a namespace member does. When the whole name is not found,
    the part before the last dot is looked up as a record variable and the last part as its
    field.
  - After the `)` of a record array, `.name` names a field. The lexer has no token for a `.`
    there.

  Size and `FOR`:
  - `LEN` of a record gives its size in bytes, as in QuickBASIC (user, 2026-10-12). It takes a
    record variable, an element such as `STOCK(3)`, or a `TYPE` name. QuickBASIC has no
    `TYPE` name form. The size is a constant and compiles to no code.

    ```
    WRITE F, @R, LEN(R)
    N = LEN(ITEM)
    ```

  - `LEN` of a string field is the length of the string in it. `LEN(R.NAME)` after
    `R.NAME = "BOLT"` is 4. In QuickBASIC, `LEN` of a `STRING * n` is always n.

  - `FOR` does not take a field as its counter (user, 2026-10-12).

  Not in the first version: a record or an array as a field, a `FLOAT` field,
  `SUB`s in a `TYPE`, a `FUNCTION` that returns a record, and a record `CONST`.

  Steps:
  1. Type codes stop being sizes, as under "Symbol table" above. Done 2026-10-13: TY.SIZE in
     `src/UXC-SYM.BL`.
  2. The `TYPE ... END TYPE` declaration, its symbol kinds, `LEN(typename)` and its errors.
     Done 2026-10-13: `src/UXC-RECORD.BL`, bank 26.
  3. A single record: `DIM R AS ITEM [AT addr]`, `BYTE` and `WORD` fields, `LEN(R)`, `@R`,
     `@R.field`, and `A = B` as an inline copy. Done 2026-10-13: T_RCOPY in
     `tpl/T-RECORD.ASM`.
  4. String fields: `SG.MAXES`, `INPUT` and `LINPUT`, and the string functions. Done
     2026-10-13: RD.MAXES. A record at a fixed address gets no max at startup.
  5. Arrays of records: a fixed index, a variable index, string fields through a hidden `WORD`,
     and the element copy through an `R_*` routine. The copy routine is asm: ask the user first.
     Done 2026-10-13: T_RCOPY_P and T_RMAX in `tpl/T-RECORD.ASM`.
  6. Record parameters.
  7. The help topic.

  The record code likely needs its own banked region. Bank 21 (`K.BANK.FLOW`) is nearly full.

- **More types, as in XC=BASIC** (user, 2026-10-09; plan 2026-10-12; steps 1 to 3 done
  2026-10-13). Step 4 is not scheduled.

  XC=BASIC 3 (`C:\dev\XCbasic\xcb-ext\xc-basic3-3.2.0-beta`, `source/compiler/type.d`):

  | Type | Size | Range or format |
  |---|---|---|
  | `BYTE` | 1 | 0 to 255 |
  | `INT` | 2 | −32768 to 32767 |
  | `WORD` | 2 | 0 to 65535 |
  | `LONG` | 3 | −8388608 to 8388607 |
  | `FLOAT` | 4 | its own format: the MS BASIC library cut to a 3-byte mantissa |
  | `DECIMAL` | 2 | packed BCD, 0 to 9999 |
  | `STRING * n` | n + 1 | n from 1 to 96 |

  - It has no marks. A type comes from `AS`, and `DIM X` with no `AS` is an `INT`.
  - A literal takes the smallest type that fits: 0 to 255 is a `BYTE`, −32768 to 32767 an
    `INT`, up to 65535 a `WORD`, then a `LONG`. `1.5` is a `FLOAT` and `1234d` a `DECIMAL`.
  - Every operand is converted to the widest type in the expression, so `BYTE * BYTE` wraps at
    256. `INT` with `WORD` gives `INT`. A compare of an `INT` with a `WORD` runs as `LONG`.
    `DECIMAL` mixes with no other type. A store to a narrower type truncates, with a compile
    warning.
  - `CBYTE`, `CINT`, `CWORD`, `CLONG` and `CFLOAT` convert.
  - Records are `TYPE ... END TYPE`, planned in "Record types" above.
  - The run-time stack is the 6502 stack, with one macro for each operation and type. `FLOAT`
    is about 3,000 lines of asm, `LONG` about 800.

  For UXCBASIC:

  | Type | `AS` form | Size | Range or format |
  |---|---|---|---|
  | `BYTE` | `AS BYTE` | 1 | −128 to 127 |
  | `WORD` | `AS WORD` or `AS INT` | 2 | −32768 to 32767 |
  | `LONG` | `AS LONG` | 4 | −2147483648 to 2147483647 |
  | `ULONG` | `AS ULONG` | 4 | 0 to 4294967295 |
  | `FLOAT` | `AS FLOAT` | 5 | the X16 ROM format, 40 bits, 9 digits |

  - `DECIMAL` is dropped. It mixes with no other type, and a `WORD` covers its range.
  - `LONG` and `ULONG` are 32 bits. A file size or position passes 16 MB, and `QINT` in the
    ROM gives 32 bits.
  - Each size has a signed and an unsigned type (user, 2026-10-13): `BYTE` and `UBYTE`,
    `WORD` and `UWORD`, `LONG` and `ULONG`. `ULONG` compares test C, as a `UWORD`'s do, and
    need none of the signed code.
  - Not decided: the names of the conversion functions, the `CBYTE`, `CINT` and `CWORD` of
    XC=BASIC, under these type names.
  - The order of work is the steps below. Each step is complete and tested before the next.

  **Step 1: type codes stop being sizes.** Done 2026-10-13 as step 1 of "Record types" above:
  TY.SIZE in `src/UXC-SYM.BL`.

  **Step 2: `BYTE` and `WORD`.** Done 2026-10-13: NM.TYPE.NAME in `src/UXC-NAME.BL`, FR.LIMIT
  in `src/UXC-FOR.BL`.

  - NM.TYPE.NAME gives `BYTE` the code `K.TY.BYTE` and `WORD` or `INT` the code `K.TY.WORD`,
    with `NM.TYPE.SIGNED` = 1.
  - An operator is signed when either side is signed. A negative constant, such as `-1`, is
    signed.
  - A signed side with a `UBYTE`, or with a constant from 128 to 255, on the other side works
    at `WORD` width. With a `UBYTE` `U` of 200 and a `BYTE` `B` of −5, `U > B` is true and
    `U + B` is 195.
  - `<`, `<=`, `>` and `>=` are signed when a side is signed. `=` and `<>` compare the bits.
  - `/` rounds toward 0, and `MOD` has the sign of the left side: `-7 / 2` is −3,
    `-7 MOD 2` is −1, `-1000 / 7` is −142 and `-1000 MOD 7` is −6.
  - `>>` on a signed left side keeps the sign: `-1000 >> 2` is −250. `<<` is the same for
    signed and unsigned.
  - Unary minus gives a signed value: a `BYTE` for a `BYTE`, else a `WORD`. With a `UWORD` `M`
    of 7, `-M` prints −7.
  - An operator on two `BYTE`s is a `BYTE` operator: with a `BYTE` `C` of −128, `C - 1` is 127.
  - A `BYTE` stored in a `WORD` keeps its sign.
  - `PRINT` and `STR$` show a signed value with a minus sign: `PRINT -1` prints −1 and
    `STR$(-3)` is `"-3"`. An unsigned value has no sign: a `UWORD` of 65535 prints 65535.
  - `VAL` and `INPUT` read a leading minus. `VAL("-42")` gives the bits of −42:
    `PRINT VAL("-42")` prints 65494, and stored in an `INT` it prints −42.
  - Parameters, `FUNCTION` results, arrays and `TYPE` fields take `BYTE`, `WORD` and `INT`.
  - A `CONST` value must fit its type: `CONST LOW AS BYTE = -100` is valid. A value under the
    range stops the compile with `TOO SMALL: name`, as `CONST N AS UBYTE = -1` does. A value
    over it stops the compile with `TOO BIG FOR A BYTE: name` or `TOO BIG FOR A WORD: name`.
    A `WORD` `CONST` takes at most 32767 and a `UWORD` `CONST` 65535.
  - `FOR` with a signed counter counts through 0 and takes negative limits and steps:
    `FOR B = 2 TO -2 STEP -1` runs 2, 1, 0, −1, −2. `STEP` may be a negative `CONST`.
  - A constant `TO` value outside the counter's type stops the compile with
    `TO VALUE OUT OF RANGE`.
  - A signed counter's `STEP` is at most half the range, 128 for a `BYTE` and 32768 for a
    `WORD`. A bigger `STEP` stops the compile with `STEP TOO BIG`.

  **Step 3: `LONG`.** Done 2026-10-13: `src/UXC-LONG.BL`, its own region in bank 28
  (`K.BANK.LONG`), reached from src/UXC-EXPR.BL by `GOSUB`.

  - `LONG` is signed 32 bits, −2147483648 to 2147483647. `ULONG` is 0 to 4294967295. Both are
    4 bytes, low byte first. They work for variables, arrays, `TYPE` fields, `SUB` parameters,
    `FUNCTION` results, `DIM ... AT` and `CONST`.
  - A `LONG` in the registers has its low word in A/Y and its high word in `ZP_HI`, `$2C`
    (`tpl/ZP.ASM`). On the run-time stack the high word is in `R_ESTKH`, a 32-byte record in
    `tpl/R-MATH.ASM` indexed by the same X as `ESTK`. `R_ESTKH` is linked only when a program
    uses a `LONG`.
  - A `LONG` `CONST` keeps its low word at +4 of the symbol record and its high word at +28,
    the word an array uses for its element count (src/UXC-SYM.BL).
  - A literal goes up to 4294967295, in decimal, `$` hex or `%` binary; past that is
    `OVERFLOW` (src/UXC-LEX.BL). A literal over 65535 is a `LONG`. A negative constant below
    −32768, such as `-70000`, is a `LONG`.
  - An operator with a `LONG` or `ULONG` side works at 32 bits. The other side is widened,
    with its sign when it is signed. It is signed when either side is signed. With
    `DIM L AS LONG` and `L = 100000`, `PRINT L * 3` prints 300000, `PRINT -L / 7` prints
    −14285, and `-L MOD 7` is −5.
  - `+`, `-`, `*`, `/`, `MOD`, the compares, `AND`, `OR`, `XOR`, `<<`, `>>`, unary minus and
    `NOT` work on a `LONG`. `>>` keeps the sign of a signed left side.
  - A `LONG` stored in a `BYTE` or `WORD` keeps its low bits: `W = L` with `L` = 1000000 gives
    16960. A `BYTE` or `WORD` stored in a `LONG` is widened, with its sign when it is signed.
  - Constants fold at 32 bits when a side is a `LONG`, and wrap at 32 bits: `4294967295 + 1`
    is 0 and `70000 * 70000` is 605032704. Two constants that are not `LONG` fold at 16 bits.
  - `PRINT` shows a `LONG` as it shows a `WORD`. `STR$(-L)` is `"-1000000"`.
  - `INPUT` and `INPUT #` read a `LONG` or `ULONG` variable in 32 bits, with a leading minus.
    `VAL` gives a 16-bit value.
  - `LVAL(S$)` reads a number from a string in 32 bits and gives a `ULONG`. Stored in a `LONG`
    it is the signed value: `LVAL("-1234567")` in a `LONG` prints −1234567. `LVAL` is a
    reserved name (src/UXC-NAME.BL). It compiles in SG.LVAL (src/UXC-STR.BL) to `T_LVAL`.
  - `CONST BIG AS LONG = -70000` and `CONST HUGE AS ULONG = 4000000000` are valid. A value out
    of range stops the compile with `TOO BIG FOR A LONG: name` or `TOO SMALL: name`.
  - A `LONG` or `ULONG` `FOR` counter stops the compile with
    `A FOR COUNTER IS A BYTE OR A WORD` (src/UXC-FOR.BL). A constant `TO` value or `STEP`
    that is a `LONG` gives the range errors `TO VALUE TOO BIG`, `TO VALUE OUT OF RANGE` and
    `STEP TOO BIG`.
  - A `LONG` constant where 16 bits are needed stops the compile with `NUMBER TOO BIG`
    (src/UXC-FOLD.BL): an array size, a `DIM ... AT`, `POKE` or `PEEK` address, an `ENUM`
    value, a `REPEAT` count and an `ASM` operand.
  - `+`, `-`, the compares and the bit operators compile inline. `*`, `/`, `MOD`, the shifts,
    `PRINT`, `STR$` and the `INPUT` read are `R_*` routines, linked only when used.
  - Trap: a GPC number is exact only below 4294967296. The compiler never forms that value
    (src/UXC-FOLD.BL).

  **Step 4: `FLOAT`.**

  - It uses the X16 ROM math library: ROM bank 4, the default, with its jump table at `$FE00`
    ("X16 Reference - 06 - Math Library.md" in the blitz compiler's `docs/x16`). The format is
    MS BASIC's 5 bytes. The library costs no RAM.
  - A `FLOAT` is not on `ESTK`. Its value is in the ROM's FAC, and a spill goes to a stack of
    5-byte slots in BSS.
  - `GIVAYF` converts a `WORD`, `FLOATC` a `UWORD`, `AYINT` and `GETADR` give them back, and
    `QINT` gives a `LONG`. `FOUT` is `PRINT` and `STR$`.
  - Trap: `QINT` gives a signed 32-bit value. A `FLOAT` of 2147483648 or more converts to a
    `LONG` some other way.
  - Trap: `VAL_1` runs BASIC's own `VAL` and needs BASIC's zero page intact.
  - To check before the design: the zero page the library uses, against `ESTK` and the
    program's `$50` up; and that a compiled program keeps ROM bank 4 selected.

  Decided (user, 2026-10-13): numbers have no marks. Every number type, `FLOAT` included,
  takes `AS` only.

  Still to decide:
  - Where a `FLOAT` `CONST` keeps its value. The symbol record has 2 bytes for it at +4, and
    a `LONG` `CONST` takes +28 for its high word.
  - Whether a store to a narrower type warns, as in XC=BASIC, or stays silent, as now.
- **A `BOOL` type, as in Prog8** (user, 2026-10-09: is it needed, what does it cost, is it
  worth it). Prog8's `bool` is one byte that holds only 0 or 1; it is not packed into bits.
  What it would give here: `AND`/`OR`/`NOT` on two `BOOL`s are exact logic with no `1 AND 2`
  trap, and `IF F` is `LDA F / BNE`. A BYTE that holds a compare already gives the same code,
  so the gain is safety more than speed. Cost: a type (`AS BOOL`, maybe a mark), and when a
  value that is not a compare is stored in a `BOOL`, about 7 bytes to make it 0 or 1. Bit
  flags packed 8 to a byte save RAM but cost an `AND #mask` or a read-modify-write on every
  use. Dropped (user, 2026-10-09): not worth it.
- **A faster number-to-text routine, as in Prog8** (user, 2026-10-09: review later). Prog8's
  `conv.str_uw` (`internal_uword2decimal` in `compiler/res/prog8lib/`) uses tables and is
  tuned for speed, so it is bigger than `R_PRWORD` and `R_STR`. Still to decide: whether the
  speed is worth the bytes.
- **An immediate `IIF`** (user, 2026-10-10). `IIF(c, a, b)` gives `a` when `c` is true and `b`
  otherwise, as in `PRINT IIF(N = 1, "ITEM", "ITEMS")`. It compiles inline to a test and two
  branches, with no call, and only the chosen side runs. Still to decide: whether `a` and `b`
  may be strings, and whether a constant `c` is folded at compile time.
- **Overloaded `SUB`s** (user, 2026-10-10). Two `SUB`s may share a name when their parameter
  types differ, as in `SUB PRINT_NUM(V AS WORD)` and `SUB PRINT_NUM(V AS STRING)`. The compiler
  picks one by the argument types at compile time, so a call is the same `JSR` as a call to a
  `SUB` with its own name, and costs nothing at run time. Separate names such as `PRINT_UW` and
  `PRINT_S` give the same code, so this is for the source only. It needs the parameter types in
  the symbol table's name for the `SUB`, and the call must parse an argument before it can
  choose the `SUB`, where today each argument is converted to its parameter's type as it is
  parsed. Rejected: an `AS ANY` parameter with a run-time type tag, which costs about 5 bytes
  and 6 cycles a call and a dispatch on each use.
- **`BIND` to a statement** (user, 2026-10-10). `BIND` gives a name to a statement, and each use
  of the name compiles that statement in its place. It is a macro with no parameters, and it
  costs nothing at run time: `CONSOLE.NL()` is the same code as `PRINT`.

  ```
  NAMESPACE CONSOLE
    BIND NL() PRINT
    BIND SPC() PRINT " ";
  END NAMESPACE
  CONSOLE.NL()
  ```

  - A one-statement wrapper as a `SUB` costs a `JSR` per call, an `RTS` and about 12 cycles a
    call. A `SUB` pays only when its body is bigger than a call.
  - Still to decide: whether a bound statement may take parameters, whether it may hold more
    than one statement, and how an error inside it reports its line.
- **`BIND` to a keyword** (user, 2026-10-10). When the target of `BIND` is a statement keyword,
  the bound name becomes that keyword. The arguments come from the line where the name is used,
  and the rest of the line is parsed as for the keyword. It costs nothing at run time, and the
  editor lists the name with the other members of its namespace.

  ```
  NAMESPACE CONSOLE
    BIND PRINT = PRINT
    BIND INPUT = INPUT
  END NAMESPACE
  CONSOLE.PRINT "HI"; X
  BIND PRT = PRINT
  PRT X
  ```

  - A reserved word as the target makes a keyword alias. No modifier is needed.
  - The statement parser looks up the name and jumps to the keyword's handler.
  - Statements only. A function keyword such as `LEN` is not a target.
  - An error reports the keyword: an error in `CONSOLE.PRINT` reports as in `PRINT`.
  - `BIND NL() PRINT` binds a whole statement. `BIND PRT = PRINT` binds only the keyword.
- **Benchmark suite** (user, 2026-10-10). A fixed set of standard programs, compiled and run
  the same way each time, as Prog8 keeps one. The suite measures the code size of each PRG and
  its run time.

  - It shows whether a change to the compiler or a template makes programs smaller or faster.
  - It compares UXCBASIC with other X16 compilers on the same programs.
  - Candidate programs, not yet chosen: a prime sieve, Mandelbrot in fixed point, N queens, a
    CRC, string building.
  - Still to decide: which programs, how run time is measured (the jiffy clock `TI` in the
    program, or a cycle count from the emulator), and whether the suite runs in `tests.py` or
    in its own script.
- **Banked code that calls banked code** (user, 2026-10-10). Done in pyuxc for 6502DOS,
  `uxc_ramreg.py`. `#REGION_SLOT n`, n 1 to 63, puts the `SUB`s after it in region n, a RAM
  bank of its own at `$A000`; `#REGION_SLOT 0` puts them back in low RAM. Help topic: Code in
  RAM banks.

  - The startup takes a bank for each region with `bank_alloc` and copies the region's image
    there from the file (`T_RGLOAD`, `R_RGLOAD`).
  - A call across an edge goes to a 7-byte veneer on the caller's side, then to the region's
    9-byte gate, which calls the kernel's `bank_call`: the bank is saved, selected, and
    restored on return. About 145 cycles. A call within a side is a `JSR`.
  - A literal, a global or a runtime record that only one region names moves into it.
  - Code in a region may not write `$00`.
  - Left: a WORD that holds an `@` address moved into a region, passed out of it, points into
    the wrong bank.
  - Possible later: copies of a shared runtime record in each region; `R_RGLOAD` or all of
    `%INIT` in the space the array space covers after startup (up to 71 bytes resident).
- **`INSTRREV`** (user, 2026-10-10). `INSTRREV(S$, F$)` gives the position of the last `F$`
  in `S$`, or 0 when there is none. It searches from the end, where `INSTR` searches from the
  start.

  - It is a built-in beside `INSTR`, as in §1 "Strings".
  - `INSTR(S$, F$[, START])` is done (2026-10-11): a built-in, SG.INSTR in src/UXC-STR.BL
    and R_INSTR in tpl/R-STRING.ASM, test INSTR. Without a start it searches from 1.
  - Still to decide: whether it takes a start position, as `INSTR` does, and what an empty `F$`
    gives.
- **A compile report** (user, 2026-10-10). A good compile reports more than the PRG name and
  size: the number of variables of each type, and the bytes of each part of memory.

  - Candidate lines: BYTE, WORD and STRING variables and arrays, with their bytes; the
    string temps; the code, the string literals and the runtime routines linked; the array
    and string space, which is the program's only heap; the end address against `$9F00`.
  - It goes in `UXC.RESULT` after the result line, so UXCEDIT can show it, and on the screen
    when UXC runs alone.
  - Still to decide: which lines, and whether the `.LST` carries the same table.
- **Shared temps and locals** (user, 2026-10-10; temps done 2026-10-10: SB.POOLS in
  src/UXC-SUB.BL, test TEMPPOOL; locals done 2026-10-10: SB.PLACE.VARIABLE, SB.PLACE.BLOCK
  and SB.POOLS in src/UXC-SUB.BL, test LOCALPOOL). Two `SUB`s that are never active at once
  can use the same bytes.

  - Temps: the link step gives each `SUB` a level in the call graph, at least 1 and 1 more
    than the level of each `SUB` that calls it. The main program has level 0 and a pool of
    its own. The string temps, 257 bytes each, of all `SUB`s of one level share one pool, as
    big as the most any of them needs. The pools sit after the array space.
  - A call the graph cannot see, through a pointer or `SYS`, breaks the sharing. No such call
    exists today.
  - Locals: a `SUB`'s parameters, its `DIM`s (BYTE and WORD variables, arrays and strings)
    and its hidden words are locals in the `SUB`'s frame. The frames of all `SUB`s of one
    level share that level's pool with the level's temps: the frames below the pool's
    offset, the temps from it up. The main program's variables stay static.
  - A local does not keep its value between calls (the user's choice). A BYTE or WORD local,
    or an array, starts undefined: the program sets it before it reads it. A string local is
    set empty, length 0 with its max set, each time its `DIM` line runs.
  - Only the `SUB` itself can name its locals (the user's choice). `PRINT SHOW.SEEN` in the
    main program stops the compile with `LOCAL TO A SUB: SHOW.SEEN`. Test ERRSUBLOCAL.
  - A frame holds at most 16384 bytes. Past that the compile stops with `LOCALS TOO BIG` at
    the `DIM` line. Test ERRSUBLOCALS.
- **`FRE`** (user, 2026-10-10). A function in the style of `FRE(0)` reports free memory while
  the program runs.

  - A program has no heap, so the free low RAM is fixed at link time: from the end of the
    array and string space to `$9F00`.
  - Still to decide: the arguments, for example `FRE(0)` for low RAM and another value for
    the free banks; whether the value is a constant the linker folds in; and how it fits the
    compile report above.
- **UXCEDIT bug: Caps Lock breaks the Ctrl keys** (user, 2026-10-10). With Caps Lock on, the
  Ctrl key commands in UXCEDIT fail. XFMGR has the fix for the same bug; port it from there.
- **`CONSOLE.LINPUT2`** (user, 2026-10-10). A line input in the `CONSOLE` namespace with more
  editing than `LINPUT L$`, which uses the KERNAL screen editor.
  - It is a library `SUB`, so a program that does not call it does not carry it.
  - Still to decide: the editing keys, whether it takes a starting text and a maximum
    length, and how it handles a line longer than the screen row.
- **Mnemonics in `ASM`** (user, 2026-10-11; done 2026-10-11: src/UXC-ASM.BL in its own region,
  bank 24, tests ASMOPS and ERRASMLABEL). An `ASM` block takes 65C02 instructions as well as
  byte items, as GPC's `GP.ASM` does.

  ```
  ASM
      ldy #0
  next: lda (PTR),y
      beq done
      jsr $FFD2
      iny
      bne next
  done:
  END ASM
  ```

  - A line whose first word is a mnemonic is an instruction. Any other line is byte items,
    as now, so the existing programs still compile.
  - All 65C02 mnemonics and addressing modes: `#n`, `n`, `n,X`, `n,Y`, `(n)`, `(n,X)`,
    `(n),Y`, `A` and the branches. An operand is a constant expression, `@name` or
    `AddrOf(name)`.
  - A label is `name:` at the start of a line. Labels belong to their block. A branch to a
    label further down is patched at `END ASM`. A branch out of range stops the compile.
  - A constant below 256 takes the zero-page form when the instruction has one. `@name` is
    resolved at link time, so it always takes the absolute form.
  - `AND`, `ORA`, `EOR` and `ROR` are read as mnemonics, not as operators, inside a block.
  - The code must keep X, which indexes the expression stack.
  - `#<n` and `#>n` are the low and the high byte. `#<@name` and `#>@name` are K.F.LO and
    K.F.HI fixups.
  - JMP and JSR take a label when the operand is a name alone.
  - A block holds 32 labels and 32 uses of a label further down.
  - Cost: about 3.3 KB of compiler in bank 24, and 102 bytes of low memory for the label
    arrays. Nothing at run time.
  - The `@name` of a `DIM ... AT` below 256 takes the zero-page form. Any other `@name` takes
    the absolute form.
  - Still to decide: whether a block may name a `SUB` parameter or local. `@name` of one goes
    through the frame fixup today, untested.
- **`FILE.SEEK`** (user, 2026-10-11). Moves the read or write position of an open file.

  - CMDR-DOS takes `P`, the secondary address, then the position as 4 bytes, low byte
    first, on the command channel. The secondary address of a handle is the handle.
  - R_FIN holds the next byte of each handle in `ahead`. A seek empties it.
  - A position is 32 bits under FAT32. It takes a `ULONG`.
  - Still to decide: a built-in or a `SUB` in `lib/DOS.UXI` of the repo root, and how a seek
    past the end reports. `lib/DOS.UXI` has `DOS.SEEK`, which calls `API_SEEK`.
- **A RAM bank manager** (user, 2026-10-11). A compiled program asks for banked RAM instead
  of picking bank numbers, so its own code and its libraries never take the same bank.

  - GPC's model is `BANKMGR.INC.BL` (tools/gpc/GPC-BASIC, manual section 4.13), plain GPC
    BASIC:
    - A bitmap of 32 bytes, one bit a bank, 1 for taken.
    - `INIT` reads the bank count from KERNAL `MEMTOP` ($FF99) with carry set, in A. A count
      of 0 means 256 (2 MB). A count that is not a multiple of 8 is legal and means bad RAM.
      The banks from the count up are marked taken. `INIT` takes bank 0, the KERNAL's, and
      bank 1, the GPC runtime's.
    - `CLAIM bank` takes a named bank and fails when it is taken or out of range.
      `GET.FREE.BANK` takes the lowest free bank and gives 0 when none is left. `RELEASE bank`
      gives one back and is silent about a bank not taken. `COUNT` gives the free banks.
    - `SPACE size`, 1 to 8192 bytes, hands out a piece of a bank: the pieces come from the
      bottom of a bank it takes, one after another, and none is given back. A piece that does
      not fit takes a fresh bank. It gives the bank and the address, `$A000` to `$BFFF`.
    - It tracks and does not select: nothing in it writes the bank register. Every `CLAIM`
      comes before the first `GET.FREE.BANK` or `SPACE`, or a fixed bank is handed out.
  - For UXCBASIC, the same calls as `R_*` routines in asm, linked only when used. The bitmap
    is 32 bytes of BSS. In asm, clearing a bit is a plain `AND`, so GPC's subtraction trap does
    not apply.
  - It serves "Banked code that calls banked code" and "Passing variables between
    programs": each claims its banks through it. `FRE` can report its free count.
  - Built in, with the names in an include file (user, 2026-10-11). Asm is approved for it.
    The compiler knows each routine under a raw name, and `lib/BANK.UXI` in the repo root
    gives the program its names, as `lib/CONS.UXI` does for `PRINT`:

    ```
    NAMESPACE BANK
      BIND CLAIM BANK_CLAIM
      BIND GET_FREE BANK_GET_FREE
      BIND RELEASE BANK_RELEASE
      BIND COUNT BANK_COUNT
    END NAMESPACE
    ```

    A program without `#INCLUDE "BANK.UXI"` cannot reach the routines. A raw name is accepted
    only as the target of a `BIND`; anywhere else it is an unknown name.
  - A new raw name goes in SG.FUNCTION or the statement table, SG.SCAN.KNOWN and NM.WORD
    (src/UXC-NAME.BL), as for `INSTR`.
  - `BANK.SELECT` selects a bank (user, 2026-10-11). As a function it gives the bank that was
    selected; as a statement it discards it. Reads and writes in the bank are `ContentsAt`,
    `PEEK` and `POKE` at `$A000` to `$BFFF`, which are raw memory access:

    ```
    #INCLUDE "BANK.UXI"
    OLD = BANK.SELECT(NEWBANK)
    X = ContentsAt($A000)
    BANK.SELECT(OLD)
    ```

    - It compiles inline after the expression, with no `JSR`: `LDY $00`, `STA $00`, `TYA`, 5
      bytes. It uses Y because X indexes the expression stack. The statement form is
      `STA $00`, 2 bytes.
    - It tracks nothing: the bank manager never selects a bank, and `BANK.SELECT` never claims
      one.
    - Trap: once banked code exists, the compiler refuses `BANK.SELECT` inside a banked region.
      Code running from `$A000` that writes `$00` fetches its next instruction from the new
      bank. GPC refuses `BANK` inside `GP.BANKED` for the same reason.
    - GPC has only the statement `BANK n`, and its `PEEK` selects and restores the bank around
      each access. `STASH.INC.BL` reads the old bank with a `GP.ASM` block, `LDA $00`.
  - 6502DOS has its own bank allocator. It records the program that owns each bank and frees a
    program's banks when the program exits.
  - Done for 6502DOS, as UXCBASIC: `lib/BANK.UXI`, namespace `BANK`, on the kernel's calls
    through `SYS`. `ALLOC`, `FREE`, `FREE_COUNT`, `USE`, `CURRENT`, `GET_BYTE`, `PUT_BYTE`,
    `FAR_CALL`. A routine adds bytes only when called. `PEEK`, `POKE`, `SELECT` and `CALL` are
    reserved words in pyuxc and cannot name a routine there. The raw names,
    `BANK.SELECT` inline and `SPACE` above are not built.
- **Relocatable output** (user, 2026-10-13). The compiler can emit a program that runs at any
  load address, not only at its `UXC.ORG`.

  - The code is built for a base address of 0, and a fixup table goes with it. Each fixup names
    one byte in the code that holds the high byte of an absolute address into the program. The
    loader adds the high byte of the load address to each such byte.
  - The runtime uses `$22–$4F` at fixed addresses (see "Zero page at run time" in section 2).
    If the host hands each program its own zero-page range, each zero-page address the program
    uses needs its own fixup.
  - The compiler writes every operand itself, so it knows each absolute address it emits and can
    record its fixup.
  - The runtime templates in `tpl/` hold absolute addresses too. `tpl/MKTPL.PY` assembles them
    into `UXC.TPL.BIN`. Each template needs its own fixup list.
  - It serves a CP/M-65 target, whose programs load at an address the system chooses. It also
    serves drivers and resident programs loaded anywhere in memory.
  - 6502DOS uses it for its relocatable program format.
  - Still to decide: the table format, CP/M-65's or our own; whether the runtime zero page moves
    too; whether `ASM` blocks with absolute addresses inside the program are allowed in
    relocatable output; and the directive that selects it.
- **ROM-able output** (user, 2026-10-13; for 6502DOS). Done in pyuxc. `#ORG address` puts the
  code at the address, with no load address in the file. `#DATA address` puts the string
  literals, then the variables, then the array space, at a RAM address outside the file. The
  startup copies the literals there from the file with `T_LITCOPY` and clears the rest. The
  runtime's data records follow the array space. Help topic: Placing the code and the variables.
  `#ROMBANKS first, second [, NAME]` splits such a program across two ROM banks
  (`uxc_rombank.py`); help topic: Two ROM banks.

  - Code in ROM cannot be written, so nothing in the code may be a variable. No runtime
    template writes its own code or a source string.
  - It covers the raw output and the separate variable address left open under "Code for a set
    memory address, as in Prog8".
  - 6502DOS layer 1 runs from ROM in this form.
  - 6502DOS wants its features in this order: records with `AT`, `LONG`, variables in banked
    RAM, `CALL AT`, the `SUB` entered by register, then ROM-able output.
- **A `SUB` entered by register** (user, 2026-10-13; for 6502DOS). `SUB KOPEN() REGS` is
  entered by `JSR`. On entry it stores A, X, Y and P at `$030C`–`$030F`, the bytes `SYS` uses,
  and on exit it loads them back. A program names the bytes with `DIM ... AT`: `REG.A` in a
  namespace `REG`, or `REG_A` as the `SYS` example has it. `RETURN ERROR n` sets the carry and
  puts n in A. Such a `SUB` is a valid entry in a jump table.
  - Trap: the four bytes are one set. A `SUB ... REGS` that runs `SYS`, or calls another such
    `SUB`, loses its own values.

  ```
  SUB KOPEN() REGS
    IF REG.A = 0 THEN RETURN ERROR 12
    REG.X = HANDLE
  END SUB
  ```

- **Calling a `SUB` by address** (user, 2026-10-13; for 6502DOS). `CALL AT P` calls the `SUB`
  at the address in `P`, where `P = AddrOf(KOPEN)`. Driver vector tables need it.
- **Variables in banked RAM** (user, 2026-10-13; for 6502DOS). `DIM SFT(15) AT $A000 BANK 0`
  puts a table in a RAM bank. Each use of it selects the bank.
- **Arrays that span RAM banks** (user, 2026-10-14). An array larger than 8 KB lives in banked
  RAM, and the program indexes it as one array. The compiler finds the bank and the address of
  each element.
  - The array keeps a list of its banks, one byte each. The byte offset of element `i` is `i`
    times the element size. The bank is entry `offset >> 13` of the list, and the address is
    `$A000 + (offset AND $1FFF)`.
  - The banks need not be contiguous. On the stock ROM they come from the RAM bank manager. On
    6502DOS they come from one extended memory block, whose chain of banks gives the list
    (6502DOS PLAN section 3).
  - Each access selects the element's bank and restores the bank before it.
  - It extends "Variables in banked RAM".
  - The compiler's rewrite in UXCBASIC can hold its symbol table and code buffer in such
    arrays. The GPC compiler splits an offset with `INT(X / 8192)` in its hot routines.
  - Trap: an element whose size does not divide 8192 can lie across two banks.
  - Still to decide: the syntax; element sizes that do not divide 8192; whether an array of
    more than 65535 elements takes a `ULONG` index; whether the list is filled at startup or by
    the program.
- **A 6502DOS target** (user, 2026-10-13; for 6502DOS). Done in pyuxc. The compiler emits a
  program that calls the 6502DOS API through its jump table at `$0340` in place of the KERNAL.
  - The stock ROM is not supported (user, 2026-10-15). pyuxc compiles for 6502DOS and has no
    target option. `compile_file`'s `target` argument is `"stock"` only in
    `attic/gpc/pyuxc/compare.py`, which matches pyuxc to the GPC UXC's output until the port
    ends. The stock table and the stock templates go then.
  - `tests.py` runs each test on the 6502DOS ROM: `TEST.COM` on a new SD card image, `RUN
    TEST.COM` typed at the monitor. The line editor echoes the keys of `NAME.IN`. Output to a
    file is not in the output.
  - `tpl/MKTPL.PY` builds a table for each target: `tpl/UXC.TPL.BIN` with `-D UXDOS=0`, and
    `tpl/UXDOS/UXC.TPL.BIN` with `-D UXDOS=1`. The 6502DOS table takes `SYS.ASM` and
    `R-FILE.ASM` from `tpl/UXDOS`, and `R-PRINT.ASM` and `R-STRING.ASM` test `UXDOS`. Both
    tables hold the same records in the same order; MKTPL stops when the ids differ.
  - The 6502DOS `R-FILE.ASM` uses handles. `OPEN` passes the name as it is, with no mode
    letter. `R_FILE` has an entry for each mode: `append`, `write` and `read`.
  - `PRINT` sends a whole string with one `write` call. A line ends with CR LF.
  - The GPC UXC has the stock target only.
- **An exit code on `END`** (user, 2026-10-15; for 6502DOS; done 2026-10-15: SM.END in
  `pyuxc/uxc_stmt.py`, T_ENDCODE in `tpl/T-CORE.ASM`; test ERRENDSTR, and 6502DOS's test
  ENDCODE). `END [code]` takes an optional BYTE expression. `END` alone is `END 0`.

  ```
  END          ' exit code 0
  END 20       ' exit code 20
  END 253      ' exit code 253, the byte $FD
  ```

  - A constant code outside 0 to 255 stops the compile with EXIT CODE OUT OF RANGE (test
    ERRENDRANGE). A variable's code keeps its low byte.

  - `END code` puts the code in A, then T_ENDCODE is `jmp API_EXIT`. The stock table's
    T_ENDCODE jumps to `S_EXIT`. `END` alone is T_END. The program that ran this one gets the
    code from `exec`.
  - A constant code is 5 bytes. A string code stops the compile with TYPE MISMATCH.
  - A run-time error exits with code 0 (user, 2026-10-15).
  - To do after the port: a final `END` is followed by the program's own `JMP S_EXIT`, 3 bytes
    that never run.
- **String `CONST`s** (user, 2026-10-17; for 6502DOS; pyuxc only). Step 1 of 3, then
  6502DOS's VIEW uses them. QuickBASIC's form: a `$` mark or `AS STRING`.

  ```
  CONST ESC$ = CHR$(27)
  CONST SGR_REVERSE$ = ESC$ + "[7m"
  CONST SGR_RESET AS STRING = CHR$(27) + "[0m"
  PRINT SGR_REVERSE$; "Find: "; SGR_RESET;
  ```

  - The value is a string literal, `CHR$` of a constant expression, or a string `CONST`, joined
    by `+`. The compiler folds it to one text.
  - A value of any other form stops the compile with `VALUE NOT A CONSTANT`. A number stops it
    with `TYPE MISMATCH`.
  - A text over 255 bytes stops the compile with `TOO BIG FOR A STRING: NAME`.
  - A record type stops the compile with `A CONST IS A NUMBER OR A STRING`, in place of
    `A CONST IS A NUMBER`.
  - The scope, `BIND`, the duplicate check and `NOT A VARIABLE` are as for a number `CONST`.
  - A use is the literal of that text. `sp_add` keeps one copy for every use and every equal
    literal: `[max][len][data]`, 2 + length bytes. An unused string `CONST` takes no PRG bytes.
    RAM 0.
  - The compiler keeps the texts in a table of 2,048 bytes. The symbol record holds the offset
    at +4 and the length in place of the high word. A full table stops the compile with
    `TOO MANY CONST STRINGS`.
  - Tests: `CONSTSTR`, which prints each form, and `ERRCONSTSTR`, a value that is not a constant.
- **Line continuation** (user, 2026-10-17; pyuxc only). Step 2 of 3. A `_` at the end of a line
  joins the next line to it.

  ```
  DIM A AS BYTE, _
      B AS UWORD
  ```

  - The `_` is the last character of the line that is not a space or a tab, with a space or a
    tab before it. `A_` at the end of a line is a name.
  - A `_` inside a string literal or a comment does not join.
  - The line reader joins the lines before the lexer sees them: the text before the `_`, then
    the next line. Several lines may join.
  - A joined line over 254 characters stops the compile with `LINE TOO LONG`.
  - An error in a joined line reports its first line.
  - A `_` on the last line stops the compile with `NO LINE AFTER _`.
  - The compiler only: PRG 0 bytes, RAM 0.
  - Tests: `LINEJOIN` and `ERRLINEJOIN`.
- **Escaped strings, as in FreeBASIC** (user, 2026-10-17; pyuxc only). Step 3 of 3. A string
  literal with a `!` before its opening quote takes escapes. A string with no `!` keeps its
  bytes as they are, so `"C:\DOS\HELP.TXT"` is unchanged.

  ```
  CONST SGR_REVERSE$ = !"\27[7m"
  PRINT !"Name:\t"; N$; !"\r\n"
  ```

  - The escapes are FreeBASIC's: `\a` 7, `\b` 8, `\t` 9, `\n` and `\l` 10, `\v` 11, `\f` 12,
    `\r` 13, `\\` 92, `\"` 34 and `\'` 39.
  - `\` and 1 to 3 decimal digits is that byte: `\27` is Esc. `\&h` takes 1 or 2 hex digits,
    `\&o` 1 to 3 octal digits, and `\&b` 1 to 8 binary digits.
  - A value over 255 stops the compile with `ESCAPE OUT OF RANGE`. Any other escape, `\u`
    among them, stops it with `BAD ESCAPE`.
  - `\0` is byte 0, which a UXCBASIC string holds. A FreeBASIC string ends at it.
  - Trap: the digits stop at 3, so `\1234` is byte 123 then `4`.
  - An escaped literal is a literal anywhere a literal is, a string `CONST` among them.
  - The compiler only: PRG 0 bytes, RAM 0.
  - Tests: `ESCAPES` and `ERRESCAPE`.
  - Not taken: FreeBASIC's `$"..."`, which marks a literal with no escapes, and `Option Escape`.
- **A WORD array store at a BYTE variable index, unchecked** (user, 2026-10-22; pyuxc only).
  `W(I) = v` with `ERRORS OFF`, or with no check owed, for a WORD array of 128 elements or
  fewer and an unsigned BYTE variable `I`. A template in the style of `T_POKE_AB` reads `I`
  itself, so the index is not pushed.

  ```
  pha
  phy
  lda I
  asl a
  tay
  pla
  sta W+1,y
  pla
  sta W,y
  ```

  - 15 bytes. It replaces `T_PUSHB` and `T_STW_SY`, about 6 bytes less a store.
  - It needs new asm.
