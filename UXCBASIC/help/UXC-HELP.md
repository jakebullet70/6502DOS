# Getting started

## What UXCBASIC is

UXCBASIC is a small compiled BASIC for the system programs and utilities of
UXDOS16. UXDOS16 is a replacement ROM operating system for the Commander X16,
modelled on MS-DOS 2.0. pyuxc, the compiler, runs on the PC. It turns one source
file into a 65C02 program that calls the UXDOS16 API.

See [[Using this help]], [[Types]] and [[Compiling]].

## Using this help

help/MKHELP.PY builds this help from help/UXC-HELP.md. Each ## topic becomes one
.HLP file in help/HELP-TXT, and the index is help/HELP-TXT/UXC.HELP.IDX. Each
program in samples/ gets a row under EXAMPLE PROGRAMS at the end of the index.

Edit the markdown, then run, from the UXCBASIC folder:

```
python help/MKHELP.PY
```

MKHELP.PY stops on a cross reference to a missing topic, on a code line over 76
columns, and on any character outside printable ASCII.

# The language

## Types

A number takes its type from AS. A string takes the $ mark or AS STRING.

```
DIM B AS BYTE, W AS WORD, N AS INT, U AS UBYTE
VAR T AS STRING * 20
B = -5
PRINT B / 2
```

This prints -2.

### The types

- BYTE is -128 to 127, 1 byte.
- UBYTE is 0 to 255, 1 byte.
- WORD is -32768 to 32767, 2 bytes, low byte first. INT is a second name for
  it.
- UWORD is 0 to 65535, 2 bytes, low byte first. UINT is a second name for it.
- LONG is -2147483648 to 2147483647, 4 bytes, low byte first.
- ULONG is 0 to 4294967295, 4 bytes, low byte first.
- STRING is text of up to 255 characters. A STRING needs a size.
- An array, a parameter, a FUNCTION result and a TYPE field take every number
  type: FUNCTION HALF(N AS WORD) AS WORD, DIM A(3) AS LONG.
- A number with no AS stops the compile with MISSING AS: name, so DIM B gives
  MISSING AS: B. The same holds for a CONST, a parameter and the result of a
  FUNCTION.

### Signed numbers

BYTE and WORD are signed. UBYTE and UWORD are unsigned.

- An operator is signed when either side is signed. A negative constant, such
  as -1, is signed.
- A signed side with a UBYTE, or with a constant from 128 to 255, on the other
  side works at WORD width. With a UBYTE U of 200 and a BYTE B of -5, U > B is
  true and U + B is 195.
- <, <=, > and >= are signed when a side is signed. = and <> compare the bits.
- / rounds toward 0, and MOD has the sign of the left side: -7 / 2 is -3, and
  -7 MOD 2 is -1.
- >> on a signed left side keeps the sign: -1000 >> 2 is -250. << is the same
  for signed and unsigned.
- Unary minus gives a signed value: a BYTE for a BYTE, a LONG for a LONG or
  ULONG, else a WORD. With a UWORD M of 7, -M is -7.
- An operator on two BYTEs is a BYTE operator: with a BYTE C of -128, C - 1 is
  127.
- A BYTE stored in a WORD keeps its sign: W = B gives -5.
- PRINT and STR$ show a signed value with a minus sign: PRINT -1 prints -1. An
  unsigned value has no sign: a UWORD of 65535 prints 65535.
- INPUT and VAL read a leading minus. See [[Strings]].

### LONG and ULONG

LONG and ULONG are 32 bits. LONG is signed and ULONG is unsigned.

```
DIM L AS LONG, W AS WORD
L = 100000
PRINT L * 3; -L / 7; -L MOD 7
L = 1000000
W = L
PRINT W
```

This prints 300000 -14285 -5, then 16960.

- An operator with a LONG or ULONG side works at 32 bits. The other side is
  widened, with its sign when it is signed. It is signed when either side is
  signed, as for BYTE and WORD.
- + - * / MOD, the compares, AND, OR, XOR, <<, >>, unary minus and NOT work at
  32 bits. >> on a signed left side keeps the sign.
- A LONG stored in a BYTE or WORD keeps its low bits: W = L above gives 16960.
  A BYTE or WORD stored in a LONG is widened, with its sign when it is signed.
- PRINT shows a LONG as it shows a WORD. STR$ gives its digits: STR$(-L) above
  is "-1000000".
- INPUT reads a LONG or ULONG variable in 32 bits, with a leading minus. VAL
  gives a 16-bit value. LVAL reads a string in 32 bits.

### LONG constants and limits

- A number literal goes up to 4294967295, in decimal, $hex or %binary. A
  bigger one stops the compile with OVERFLOW.
- A literal over 65535 is a LONG. A negative constant under -32768, such as
  -70000, is a LONG.
- Constants fold at 32 bits when a side is a LONG, and wrap at 32 bits:
  4294967295 + 1 is 0, and 70000 * 70000 is 605032704. Two constants that are
  not LONG fold at 16 bits.
- A LONG constant where the compiler needs 16 bits stops the compile with
  NUMBER TOO BIG: an array size, a DIM ... AT, PEEK or POKE address, an ENUM
  value, a REPEAT count, an ASM operand.
- A FOR counter that is a LONG or ULONG stops the compile with A FOR COUNTER
  IS A BYTE OR A WORD.
- + -, the compares and the bit operators are inline code. * / MOD, the
  shifts, PRINT, STR$ and INPUT call run-time routines, linked only when used.
- An unsigned / or MOD by a constant power of 2 compiles as >> or AND: N / 256
  is N >> 8, and N MOD 256 is N AND 255. It links no divide routine.
  A program that uses a LONG gets 32 more bytes for the expression stack.

### The $ mark

- A $ after a name makes it a STRING: DIM L$ * 80. AS STRING is the same.
- A $ and AS on one name stop the compile with A MARK AND AS.
- % is not a mark. A % right after a name stops the compile with % IS NOT A
  MARK: USE AS UWORD. %1010 is a binary number.
- ! is not a mark. DIM A! AS UBYTE stops the compile with SYNTAX ERROR.

### Names

A name is a letter, then letters, digits and _, 16 at most, then a $ for a
string. The $ is part of the name: S and S$ are two names. A name declared with
AS has no mark, so after VAR T AS STRING * 20 the name is T. Upper and lower
case are the same, so my_count and MY_COUNT are one name. A dot joins the parts
of a qualified name: GFX.COLOR is COLOR in namespace GFX. A reserved word with
a $ is reserved too: PRINT$ is not a name.

See [[Declarations]], [[Strings]], [[Namespaces]].

## Declarations

DIM and VAR mean the same thing. Every variable must be declared.

### DIM ... AT

DIM name AS type AT address puts a number variable at a fixed address.
The variable takes no space in the program.

```
DIM REG_A AS UBYTE AT $030C, REG_P AS UBYTE AT $030F
REG_P = 0
REG_A = 65
SYS $FFD2                    ' CHROUT prints A
IF REG_P AND 1 THEN PRINT "CARRY"
```

- The address is a constant expression: DIM H AS UBYTE AT $0400 + 1.
- A WORD or UWORD takes the address and the next byte, low byte first. A LONG
  or ULONG takes 4 bytes.
- The variable works wherever a variable does: in expressions, as the target
  of =, as a FOR counter, in INPUT and as a BIND target.
- Each read or write is one absolute load or store, 3 bytes, also at a
  zero-page address. REG_P = 5 is LDA #5, STA $030F.
- AddrOf(name) is the address. In ASM it is two bytes.
- Two variables may share an address: DIM P AS UWORD AT $0400, L AS UBYTE AT
  $0400.
- The address is not checked against the program's own memory.
- An address that is not a constant stops the compile with ADDRESS NOT A
  CONSTANT.
- An array or a string with AT stops the compile with NOT YET: AN ARRAY OR A
  STRING AT AN ADDRESS.

See [[Types]], [[SYS]], [[Pointers]].

## CONST

CONST name AS type = value makes a named constant. The type is BYTE, UBYTE,
WORD, UWORD, LONG, ULONG or STRING.
Several go on one line, separated by commas. The value is a constant
expression.

```
CONST MAX_LEN AS UBYTE = 80
CONST ROWS AS UBYTE = 2 * 30, COLS AS UBYTE = MAX_LEN + 1
CONST BASE AS UWORD = $9F20
CONST BIG AS UWORD = 1000
PRINT MAX_LEN; ROWS; COLS; BASE; BIG
```

This prints 80  60  81  40736  1000.

- A number CONST with no AS stops the compile with MISSING AS: name.
- The value must fit the type: CONST LOW AS BYTE = -100 is fine.
- A value over the type's range stops the compile with TOO BIG FOR A BYTE:
  name, TOO BIG FOR A WORD: name or TOO BIG FOR A LONG: name. A WORD takes at
  most 32767, a UWORD 65535, a LONG 2147483647 and a ULONG 4294967295.
- CONST BIG AS LONG = -70000 and CONST HUGE AS ULONG = 4000000000 are valid.
- A value under the type's range stops the compile with TOO SMALL: name, as
  CONST N AS UBYTE = -1 does.
- A record type stops the compile with A CONST IS A NUMBER OR A STRING.
- A value that is not a constant stops the compile with VALUE NOT A CONSTANT.
- A constant belongs to the SUB or namespace it is in. BIND can name it.
- A number constant is used like a number. It takes no RAM and no space in
  the PRG.
- An assignment to a constant stops the compile with NOT A VARIABLE: name.

### String CONSTs

A CONST whose name ends in $, or a CONST AS STRING, is a string. Its value is
string literals, CHR$(n) and other string CONSTs, joined by +.

```
NAMESPACE CONS
  CONST CSI$ = CHR$(27) + "["
END NAMESPACE
CONST SGR_REVERSE$ = CONS.CSI$ + "7m", SGR_NORMAL$ = CONS.CSI$ + "0m"
PRINT SGR_REVERSE$; "NOTE"; SGR_NORMAL$; LEN(SGR_REVERSE$)
```

- A string CONST needs no AS. AS STRING takes no size: CONST STAR AS STRING =
  "*".
- n in CHR$(n) is a constant expression, and may use a number CONST. The
  character is the low byte of n.
- A literal may be an escaped string: CONST REVERSE$ = !"\27[7m". See
  [[Escaped strings]].
- A literal may hold tags: CONST REVERSE$ = "{REVERSE}". See [[Tags]].
- A string CONST of a namespace is named in full: CONS.CSI$.
- A use is a string literal of the text. LEN and ASC of a string CONST are
  worked out by the compiler, as for a literal.
- The text is up to 255 characters. A longer one stops the compile with TOO BIG
  FOR A STRING: name.
- The texts of all string CONSTs take up to 2048 bytes together. More stops the
  compile with TOO MANY CONST STRINGS.
- A number or a number CONST in the value stops the compile with TYPE MISMATCH.
- A variable, a function other than CHR$, or CHR$ of a value that is not a
  constant stops the compile with VALUE NOT A CONSTANT.

See [[Types]], [[Namespaces]], [[BIND]], [[Strings]].

## ENUM

ENUM name ... END ENUM makes a set of named constants, the members. ENDENUM is
the same as END ENUM. A line holds one member, or several separated by commas.

```
ENUM STATE
  READY, RUNNING
  BLOCKED = 10
  DONE             ' 11
  LAST = DONE + 5
END ENUM
PRINT STATE.READY; STATE.RUNNING; STATE.BLOCKED; STATE.DONE; STATE.LAST
```

This prints 0  1  10  11  16.

- Members number from 0. NAME = value sets a member's number, and the members
  after it count on by 1. The value is a constant expression, and can use an
  earlier member bare and any CONST.
- Inside the ENUM a member is used bare, in a value only. Outside it is
  qualified: STATE.READY. An ENUM MODE in namespace GFX gives GFX.MODE.TEXT.
- The members are UBYTE when every value is 0 to 255. When one passes 255, the
  ENUM and every member are UWORD.
- A member is a constant. It takes no RAM and no space in the PRG.
- A member name takes no mark. A $ is a syntax error. A % stops the compile
  with % IS NOT A MARK: USE AS UWORD.
- An ENUM may be in a namespace or a SUB.
- Errors: ENUM WITHOUT END ENUM at the ENUM's line when the source ends inside
  it, END ENUM WITHOUT ENUM, TOO BIG FOR A WORD: name for a count past 65535,
  VALUE NOT A CONSTANT.

AS ENUM.name gives a parameter, a FUNCTION result, a variable or a field the
type of the ENUM's members.

```
SUB SHOW(S AS ENUM.STATE)
  PRINT S
END SUB
SHOW(STATE.BLOCKED)
DIM M AS ENUM.GFX.MODE
```

- Outside the ENUM's namespace the name is qualified: ENUM.GFX.MODE.
- A constant passed to such a parameter must be a member of that ENUM, or the
  compile stops with NOT A MEMBER OF name. A variable passes unchecked. The
  check is made by the compiler and takes no space in the PRG.
- In an argument to such a parameter, a name without a dot is first looked for
  among the ENUM's members: SHOW(BLOCKED) passes STATE.BLOCKED. A member found
  this way hides a variable of the same name in that argument.
- A parameter can name an ENUM declared above its SUB, outside a SUB body.
- Errors: USE AS ENUM.name for an ENUM's name after AS without ENUM., NOT AN
  ENUM: name, TOO BIG FOR A PARAMETER: name when a member of an ENUM that a
  parameter or a FUNCTION result uses passes 255.

See [[CONST]], [[Namespaces]], [[Types]].

## Arrays

DIM name(count) AS type makes an array of count elements, numbered 0 to
count - 1. The type is any number type.

```
DIM B(10) AS UBYTE, W(5) AS UWORD
B(0) = 7
W(4) = B(0) * 1000
PRINT W(4)
```

- The count is a constant, 1 or more. It may be a constant expression, such as
  2 * 8. A LONG count stops the compile with NUMBER TOO BIG.
- Every element of a main program array is 0 when the program starts.
- An index is any number expression. A negative index is out of range.
- A constant index out of range stops the compile with BAD SUBSCRIPT.
- An index out of range at run time stops the program with ?BAD SUBSCRIPT
  ERROR AT $addr. ERRORS OFF leaves out this check.
- AddrOf(B) is the address of element 0. ContentsAt(AddrOf(B) + 2) reads
  B(2).
- An array DIMed in a SUB is a local of the SUB. Its elements start undefined
  and do not keep their values between calls.
- Arrays sit in memory after the program and take no space in the PRG file.

See [[Declarations]], [[ERRORS ON and OFF]], [[Pointers]], [[Subroutines]].

## Comments

A line is a comment when its first word, after any spaces, is REM, ', ;, ## or
//. The compiler skips the whole line.

```
REM THE WHOLE LINE
' THE WHOLE LINE
; THE WHOLE LINE
## THE WHOLE LINE
// THE WHOLE LINE
```

Only REM and ' can follow a statement. The comment runs to the end of the line.

```
X = 1 ' THE REST OF THE LINE
X = 1 REM THE REST OF THE LINE
```

- ; is a comment only at the start of a line, so PRINT A; B is a PRINT.
- ## is a comment and #DEFINE is not: a directive has one #.
- Inside a string none of these starts a comment.

There is no character literal. Write ASC("A"), and the compiler folds it to 65.

## Line continuation

A _ at the end of a line joins the next line to it. The compiler reads the
lines as one.

```
DIM A AS UBYTE, _
    B AS UWORD
B = 1000 + _
    234
IF B > 1000 THEN _
  PRINT "BIG"
```

- The _ is the last character of the line other than spaces and tabs, and a
  space or a tab comes right before it. PRINT C_ ends in a name and joins
  nothing.
- The joined line is the text before the _, then the next line. Several lines
  in a row can join.
- A _ inside a string, after ' or REM, or on a comment line does not join.
- An error in a joined line reports the number of its first line.
- The compile stops with NO LINE AFTER _ when a _ is on the last line of the
  source.
- A joined line over 254 characters stops the compile with LINE TOO LONG.

See [[Comments]].

## Strings

DIM name$ * size makes a string of up to size characters, 1 to 255. The form
name AS STRING * size does the same. A string must have a size.

```
DIM L$ * 80, N AS STRING * 20
N = "ADA"
L$ = "HELLO, " + N
PRINT L$; LEN(L$)
IF L$ <> "" THEN PRINT MID$(L$, 1, 5)
```

- A main program string is empty when the program starts. A string DIMed in a
  SUB is set empty each time its DIM line runs.
- An assignment cuts the text at the string's size.
- + joins two strings. A joined string is cut at 255 characters.
- The six compares work on strings. The first character that differs decides,
  by its code. When one string starts with the other, the longer one is
  greater.
- A string and a number in one operator stop the compile with TYPE MISMATCH.
- A string holds any byte, 0 included.
- @L$ is the address of the string's block: the size byte, the length byte,
  then the characters.
- Strings sit in memory after the program, as arrays do, and take no space in
  the PRG file.

The functions:

- LEN(s) is the length, a UBYTE.
- ASC(s) is the code of the first character, or 0 when s is empty.
- CHR$(n) is the one character with code n.
- STR$(n) is n in decimal, with a space or a minus sign in front: STR$(5) is
  " 5" and STR$(-3) is "-3".
- VAL(s) is the number s starts with. Spaces and a + before it are skipped. A -
  right before the digits gives the bits of the negative number: PRINT
  VAL("-42") prints 65494, and X = VAL("-42") with X AS INT gives -42.
  VAL("12AB") is 12, and VAL("ABC") is 0. VAL gives a 16-bit value, also when
  it is stored in a LONG.
- LVAL(s) is the number s starts with, read in 32 bits, as a ULONG. Stored in
  a LONG it is the signed value: L = LVAL("-1234567") with L AS LONG gives
  -1234567, and PRINT LVAL("3000000000") prints 3000000000. LVAL is a reserved
  word.
- MID$(s, start, count) is count characters of s from position start. The
  first position is 1, and 0 is the same as 1. Without count, it is the rest of
  s. A start past the end gives "".
- LEFT$(s, count) is the first count characters of s, and RIGHT$(s, count) the
  last count. A count past the length of s gives all of s: LEFT$("HELLO", 9) is
  "HELLO", and RIGHT$("HELLO", 3) is "LLO". Both are reserved words.
- STR.name is the same function as name: STR.MID$ is MID$. STR.UXI in the
  UXDOS16 library binds them in NAMESPACE STR.
- INSTR(s, find, start) is the position of the first find in s at or after
  position start, a UBYTE. It is 0 when there is none, or when find is empty.
  Without start, the search starts at 1, and 0 is the same as 1.

LEN and ASC of a literal, and CHR$ and STR$ of a constant, are worked out by
the compiler.

A SUB takes a STRING parameter with no size: SUB SHOW(T$). The SUB works on the
caller's string, so an assignment to T$ changes it. A literal argument is
copied first, so the SUB cannot change the literal.

Not yet: string arrays, a start value.

See [[Types]], [[Subroutines]], [[Including files]], [[Escaped strings]].

## Escaped strings

!"text" is a string literal that takes FreeBASIC's escapes, except \u. A \ and
the characters after it are one escape, and stand for one byte. An escaped
string works wherever a string literal does, in a string CONST too. A string
with no ! keeps each \ as it is.

```
PRINT !"\27[7mREVERSE\27[0m"
PRINT !"A\\B\"C"; " C:\DOS"
```

The second line prints A\B"C C:\DOS.

- \a is 7, \b 8, \t 9, \n 10, \l 10, \v 11, \f 12 and \r 13.
- \\ is \, \" is " and \' is '. A \" does not end the string.
- \ and 1 to 3 decimal digits is that byte: \27 is 27, \0 is 0.
- \&h and 1 or 2 hex digits, \&o and 1 to 3 octal digits, and \&b and 1 to 8
  binary digits: \&h1B, \&o33 and \&b11011 are 27.
- Letters may be upper or lower case: \T is \t, and \&H1b is \&h1B.
- The digits stop at the most for their kind: !"\0654" is A, then 4.
- The ! comes right before the quote. ! "A" stops the compile with SYNTAX
  ERROR.
- Any other character after the \ or the \&, \u among them, or no digit
  after \&h, \&o or \&b, stops the compile with BAD ESCAPE.
- A value over 255, such as \256 or \&o400, stops the compile with ESCAPE OUT
  OF RANGE.
- A \ at the end of the line stops the compile with MISSING QUOTE.

See [[Strings]], [[CONST]], [[Tags]].

## Tags

A tag in a string literal is a name in braces, and stands for an ANSI escape
sequence of the console. Tags work in every string literal, with or without
the !.

```
CONST STATUS$ = "{BLACK}{ON WHITE}"
PRINT STATUS$; " Saved{CLEAR EOL}{NORMAL}"
```

The first line makes STATUS$ Esc[30;47m, 7 bytes.

| Tag | Sequence |
|---|---|
| {CURSOR HOME} | Esc[H |
| {CLS} | Esc[2J |
| {CLEAR EOL} | Esc[K |
| {NORMAL} | Esc[0m |
| {REVERSE} | Esc[7m |
| {BLACK} {RED} {GREEN} {YELLOW} {BLUE} {MAGENTA} {CYAN} {WHITE} | Esc[30m to Esc[37m |
| {ON BLACK} {ON RED} {ON GREEN} {ON YELLOW} {ON BLUE} {ON MAGENTA} {ON CYAN} {ON WHITE} | Esc[40m to Esc[47m |

- Upper and lower case are the same: {on white} is {ON WHITE}. The words take
  one space between them.
- An m tag right after another m tag joins its sequence, up to 4 parameters:
  {NORMAL}{RED}{ON BLUE}{REVERSE}{GREEN} is Esc[0;31;44;7m Esc[32m.
- An escape does not join a tag: !"\27[0m{RED}" is Esc[0m Esc[31m.
- {{ is one {. A } alone stays as it is: "{{A}" prints {A}.
- Any other {, an unknown name, or a { with no } before the quote stops the
  compile with BAD TAG.
- The tags give the same bytes as the CONSTs of lib/CONS.UXI: {CLEAR EOL} is
  CONS.CLEAR_EOL$.

See [[Strings]], [[Escaped strings]].

## Pointers

AddrOf(name) is the address of a variable, an array or a string, as a UWORD.
@name is the same. ContentsAt and ContentsAtW read and write memory at any
address.

```
DIM X AS UBYTE, P AS UWORD, W AS UWORD
X = 42
P = AddrOf(X)
PRINT ContentsAt(P)          ' 42
ContentsAt(P) = 7            ' X is now 7
ContentsAtW(AddrOf(W)) = 1000
```

- ContentsAt(a) is the UBYTE at address a, as PEEK(a) is.
- ContentsAt(a) = v writes the UBYTE v to a, as POKE a, v does.
- ContentsAtW(a) is the UWORD at a and a + 1, low byte first.
- ContentsAtW(a) = v writes the UWORD v to a and a + 1.
- The address is any UWORD expression: ContentsAt(P + 3) = 33.
- A constant address or AddrOf(name) compiles to one load or store. Any other
  address goes through a pointer at run time.
- In ASM, AddrOf(name) is two bytes, as @name is.
- PEEK and POKE work as well.
- Case does not matter: AddrOf and ADDROF are the same word.
- ADDROF, CONTENTSAT and CONTENTSATW are reserved words.
- AddrOf(X with no closing bracket stops the compile with MISSING ).
- ContentsAt 5 = 1 stops the compile with MISSING ( AFTER CONTENTSAT.

See [[Arrays]], [[Strings]], [[Declarations]], [[ASM]].

# Commands

## Control

IF chooses, and DO, FOR and REPEAT loop. EXIT leaves a loop, CONTINUE starts its
next pass, GOTO jumps to a label, and END ends the program.

A condition is true when it is not 0. A compare is compiled straight to a branch,
with no 0 or 1 in between. AND and OR between compares stop as soon as the answer
is known: in A AND B, B is not tested when A is false.

AND and OR are bitwise, so IF A AND 4 tests bit 2. To test two values for not 0,
write IF A <> 0 AND B <> 0.

See [[IF]], [[SELECT CASE]], [[DO]], [[FOR]], [[REPEAT]], [[EXIT and CONTINUE]],
[[GOTO]], [[END]].

## IF

A block, with any number of ELSEIF parts and one ELSE. THEN is optional at the
end of the line. ENDIF can be written END IF.

```
DIM N AS UWORD
IF N = 0
  PRINT "NONE"
ELSEIF N < 10 THEN
  PRINT "A FEW"
ELSE
  PRINT "MANY"
ENDIF
```

On one line, with THEN and one statement. A one-line IF has no ELSE.

```
IF K = 27 THEN PRINT "ESC"
IF K = 13 THEN EXIT DO
IF N > 100 GOTO DONE
```

A part before ELSEIF or ELSE that ends in RETURN, GOTO, EXIT, CONTINUE or END
has no jump to ENDIF.

## SELECT CASE

SELECT CASE v ... END SELECT runs the first CASE whose test matches v. v is a
number or a string. ENDSELECT is the same as END SELECT.

```
DIM N AS UBYTE, M$ * 8
SELECT CASE N
  CASE 1
    PRINT "ONE"
  CASE 2, 4
    PRINT "TWO OR FOUR"
  CASE 5 TO 7
    PRINT "FIVE TO SEVEN"
  CASE IS >= 8
    PRINT "EIGHT UP"
  CASE ELSE
    PRINT "NONE"
END SELECT
SELECT CASE M$
  CASE "IF", "ELSE"
    PRINT "FLOW"
END SELECT
```

- A test is a value, a range low TO high with both ends in, or IS with =, <>,
  <, >, <= or >= and a value. Commas separate the tests of a CASE.
- CASE ELSE is last, and runs when no CASE before it ran. A CASE after it stops
  the compile with CASE AFTER CASE ELSE.
- It compiles to the same code as an IF and ELSEIF chain. A CASE that ends in
  RETURN, GOTO, EXIT, CONTINUE or END has no jump to END SELECT.
- A variable is read again at each test. Any other number is worked out once.
- A string selector is a variable or a literal. Any other string stops the
  compile with SELECT CASE NEEDS A STRING VARIABLE.
- Trap: a function in a test that changes the selector variable changes the
  tests after it.

## DO

DO ... LOOP, with a WHILE or UNTIL test at the top, at the bottom, at both or at
neither. With no test the loop runs until EXIT DO.

```
DIM N AS UWORD
DO WHILE N < 10
  N = N + 1
LOOP
DO
  N = N - 1
LOOP UNTIL N = 0
```

A test at the top is compiled at the bottom, so it costs no more per pass.

## FOR

FOR v = a TO b [STEP k] ... NEXT [v]. The variable is a BYTE, UBYTE, WORD or
UWORD. STEP is a constant, 1 when it is left out. STEP -1 counts down.

```
DIM I AS UBYTE, W AS UWORD
FOR I = 0 TO 255
  POKE $0400 + I, I
NEXT
FOR W = 1000 TO 0 STEP -100
  PRINT W
NEXT W
```

- The body runs zero times when the range is empty.
- The test is made before the step, so FOR I = 0 TO 255 ends, and I never wraps.
- After the loop, v holds the last value the body saw: 255 above.
- The TO value is read once, at the start.
- A signed counter counts through 0 and takes negative limits and steps: FOR
  B = 2 TO -2 STEP -1 runs 2, 1, 0, -1, -2.
- STEP may be a negative CONST: STEP N with CONST N AS BYTE = -2 counts down
  by 2.
- A constant TO value outside the counter's type stops the compile with TO
  VALUE OUT OF RANGE, as FOR B = 0 TO 200 does with B a BYTE. Over an unsigned
  counter's range it stops with TO VALUE TOO BIG.
- A LONG or ULONG counter stops the compile with A FOR COUNTER IS A BYTE OR A
  WORD.
- A signed counter's STEP is at most half the range: 128 for a BYTE, 32768 for
  a WORD. A bigger STEP stops the compile with STEP TOO BIG.

## REPEAT

REPEAT n ... END REPEAT runs the body n times. n is read once. REPEAT 0 skips the
body. With no count the loop runs until EXIT REPEAT. ENDREPEAT is the same as
END REPEAT.

```
REPEAT 3
  PRINT "HI"
END REPEAT
```

It has no loop variable, so it is the fastest counted loop.

## EXIT and CONTINUE

EXIT DO, EXIT FOR and EXIT REPEAT leave the innermost loop of that kind. CONTINUE
goes to the test, or the step, of the innermost loop.

```
DIM I AS UBYTE
FOR I = 1 TO 10
  IF I = 3 THEN CONTINUE
  IF I = 8 THEN EXIT FOR
  PRINT I
NEXT
```

## GOTO

GOTO jumps to a label. A label is a name and a colon, alone on its line.

```
GOTO DONE
PRINT "SKIPPED"
DONE:
END
```

## END

END ends the program and returns to the program that ran it. END code returns
code as the exit code, a byte. END alone returns 0. A constant code outside 0
to 255 stops the compile with EXIT CODE OUT OF RANGE. A variable's code keeps
its low byte. END works anywhere, in a SUB too.

```
DIM MISSING AS UBYTE
MISSING = 3
IF MISSING = 0 THEN END
END MISSING
```

- A run-time error ends the program with exit code 0.
- Errors: a string code, as in END "B", stops the compile with TYPE MISMATCH.

## GETKEY

GETKEY() gives the next key from the keyboard buffer as a UBYTE, or 0 when no
key is waiting. It does not wait. The brackets are required.

```
DIM K AS UBYTE
DO
  K = GETKEY()
LOOP UNTIL K <> 0
PRINT K
```

The value is the key's character code: 13 is ENTER. An extended key, such as
an arrow or F1, gives 0, then its scan code at the next GETKEY(). KEYS.UXI names
the codes.

- Trap: 0 is both no key and the start of an extended key.
- GETEXTKEY() gives an extended key in one call.

See [[GETEXTKEY, WAITKEY and KEYMODS]], [[The STOP key]].

## GETEXTKEY, WAITKEY and KEYMODS

GETEXTKEY() gives the next key as a UWORD, or 0 when no key is waiting. It
does not wait. WAITKEY() waits for a key, the cursor blinking, and gives it as
GETEXTKEY() does. The brackets are required.

- A plain key gives its character code, 1 to 255: 13 is ENTER.
- An extended key, such as an arrow or F1, gives its scan code * 256: Up
  gives $4800.
- A key over 255 is an extended key.

KEYMODS() gives the modifier bits of the last GETEXTKEY() or WAITKEY() as a
UBYTE: 1 Shift, 4 Caps Lock on, 64 Alt, 128 Ctrl. KEYS.UXI names the keys
KEY_UP, KEY_F1 and so on, and the bits MOD_SHIFT to MOD_CTRL.

```
#INCLUDE "KEYS.UXI"
DIM K AS UWORD
K = WAITKEY()
IF K = KEYS.KEY_UP THEN PRINT "UP"
IF K > 255 THEN PRINT "SCAN CODE"; K >> 8
IF (KEYMODS() AND KEYS.MOD_CTRL) <> 0 THEN PRINT "CTRL"
```

- KEYMODS() gives 0 before the first GETEXTKEY() or WAITKEY().
- Ctrl+2 gives KEY_CTRL_2, $0300.

See [[GETKEY]], [[The STOP key]].

## The STOP key

Ctrl+C is the STOP key. A program starts with Ctrl+C ending it: the DOS prints
^C and the program ends with exit code 0. DOS.STOP_KEY(mode), in DOS.UXI, sets
what Ctrl+C does. The modes are the members of DOS.STOP:

- OFF: Ctrl+C is a key like any other, code 3.
- ENDS: Ctrl+C ends the program. Each program starts in ENDS.
- CATCH: Ctrl+C is dropped and sets a flag. DOS.STOP_PRESSED() gives 1 when the
  flag is set, and clears it.

```
#INCLUDE "DOS.UXI"
DIM K AS UBYTE
DOS.STOP_KEY(CATCH)
DO
  K = GETKEY()
  IF K <> 0 THEN PRINT K
LOOP UNTIL DOS.STOP_PRESSED() = 1
PRINT "STOPPED"
```

- Ctrl+C is seen only while the program asks for a key: GETKEY, GETEXTKEY,
  WAITKEY, INPUT and LINPUT. A long loop that asks for no key cannot be
  stopped.
- The mode belongs to the program. A program it runs starts in ENDS, and the
  mode comes back when that program ends.
- STOP_KEY sets DOS.ERROR to 13 for a mode above 2.

See [[ENUM]], [[GETKEY]].

## POS

POS(n) gives a UBYTE:

- POS(0): the cursor column, from 0.
- POS(1): the cursor row, from 0.
- POS(2): the screen's rows, 30.
- POS(3): the screen's columns, 80.

POS(2) and POS(3) ask the DOS each time; no copy is stored.

POS(0) = v moves the cursor to column v and keeps the row. POS(1) = v moves it
to row v and keeps the column. v is any expression and is used as a UBYTE.

The number in the brackets must be a number, not a variable or an expression.
A read of anything but 0 to 3 is the compile error "POS NEEDS 0 TO 3". An assignment to anything but
POS(0) or POS(1) is the compile error "POS NEEDS 0 OR 1".

```
DIM C AS UBYTE
PRINT "ABC";
C = POS(0)
PRINT C
POS(0) = C * 3 + 1
PRINT POS(0)
```

This prints 3 after ABC, then 10 starting at column 10.

## INPUT and LINPUT

INPUT reads what the user types into number and STRING variables. It prints
"? " first. A string and a semicolon after INPUT are printed before the "? ".

```
DIM AGE AS UWORD, N$ * 20
INPUT "NAME"; N$
INPUT "AGE"; AGE
PRINT N$; AGE
```

- Each variable takes one field. A field ends at a comma or at RETURN.
- Several variables take their fields from one line: INPUT A, B$ takes 5,BOB.
- The rest of the line after the last field is dropped.
- When RETURN comes before the last field, the next field is read from a new
  line, with no prompt.
- A number field is read as VAL reads it. A signed variable takes a minus
  sign. A LONG or ULONG variable is read in 32 bits.
- A string field is cut at the string's size.
- The variable cannot be an array element.

LINPUT reads a whole line into a STRING variable, commas and quotes included. It
prints no prompt. A line longer than the string is cut.

```
DIM L$ * 80
LINPUT L$
```

## Subroutines

A SUB runs its body and has no value. A FUNCTION has a value and is used in an
expression.

SUB name(parameters) ... ENDSUB. ENDSUB can be written END SUB. A SUB is called
by its name and its brackets. CALL in front is optional. The brackets are not:
they make the name a call, even with no arguments.

```
SUB SHOW(N AS UBYTE)
  PRINT N
ENDSUB
SHOW(7)
CALL SHOW(7)
```

- A parameter is a BYTE, UBYTE, WORD, UWORD or STRING. A number parameter
  needs AS: SUB SHOW(N) stops the compile with MISSING AS: N. A STRING
  parameter takes the $ mark or AS STRING.
- An argument is worked into its parameter's type: a UWORD into a UBYTE
  parameter keeps its low byte. A STRING parameter has no size, and the SUB
  works on the caller's string. See [[Strings]].
- The number of arguments must match the parameters.
- RETURN leaves the SUB at once. In a SUB, RETURN has nothing after it.
- A SUB name with a $, or an AS type after the brackets, stops the compile
  with SUB WITH A TYPE: USE FUNCTION.
- A SUB or a FUNCTION may be called before it is written.
- The main program jumps over a SUB or a FUNCTION, so either can sit anywhere
  outside a block.
- A SUB or a FUNCTION cannot call itself. One that calls itself stops the
  compile with A SUB CANNOT CALL ITSELF.
- SUBs and FUNCTIONs cannot call each other. A loop of calls between them, A
  calls B and B calls A or a longer loop, stops the compile with SUBS CALL EACH
  OTHER at the line of one of the calls.

### FUNCTION

FUNCTION name(parameters) AS type ... ENDFUNCTION. ENDFUNCTION can be written
END FUNCTION. The parameters and the call are as in a SUB. AS after the
brackets gives the type of the value. RETURN gives the value.

```
FUNCTION MAX(A AS UWORD, B AS UWORD) AS UWORD
  IF A > B THEN RETURN A
  RETURN B
ENDFUNCTION
FUNCT HALF(N AS UWORD) AS UWORD
  RETURN N / 2
END FUNCT
DIM T AS UWORD
T = MAX(3, HALF(100))
```

- A number FUNCTION with no AS stops the compile with MISSING AS: name. A
  STRING FUNCTION may take the $ mark in place of AS, as in STRING results
  below.
- FUNCT is FUNCTION and ENDFUNCT is ENDFUNCTION, so END FUNCT is END FUNCTION.
  Every source has them, as if it began with BIND FUNCT FUNCTION and BIND
  ENDFUNCT ENDFUNCTION.
- A FUNCTION needs at least one RETURN with a value. Its end, when the body
  reaches it, gives 0, or "" in a STRING FUNCTION.
- A FUNCTION may be called as a statement. The value is lost.
- The end must match the start. END SUB or ENDSUB in a FUNCTION stops the
  compile with ENDSUB IN A FUNCTION. END FUNCTION or ENDFUNCTION in a SUB
  stops it with ENDFUNCTION IN A SUB.
- END FUNCTION outside a SUB or a FUNCTION stops the compile with ENDFUNCTION
  WITHOUT FUNCTION.
- A FUNCTION still open at the end of the source stops the compile with
  FUNCTION WITHOUT ENDFUNCTION at the FUNCTION line. A SUB gives SUB WITHOUT
  ENDSUB.

### STRING results

A FUNCTION that returns a STRING has the $ mark or AS STRING: FUNCTION
FIRST3$(S$) or FUNCTION WRAP(T AS STRING) AS STRING. Its value is assigned,
printed, compared and joined with + as any string is.

```
DIM A$ * 20
FUNCTION FIRST3$(S$)
  RETURN MID$(S$, 1, 3)
ENDFUNCTION
A$ = FIRST3$("HELLO")
PRINT FIRST3$("WORLD") + "!"
```

- A STRING result is at most 255 characters. An assignment cuts it to the
  size of the destination.
- A STRING result passed to a SUB or a FUNCTION is passed as a copy.

### Locals

Parameters, and names DIMed in a SUB or a FUNCTION, are its locals. In this
section SUB means either. A local with the same name as a main program variable
hides it inside the SUB. Main program variables DIMed before the SUB can be
used in it. Labels belong to the SUB too, so no GOTO crosses into or out of
one.

- A local does not keep its value between calls.
- A UBYTE or UWORD local, and a local array, starts undefined. Set it before you
  read it.
- A local string is set empty each time its DIM line runs.
- Only the SUB itself can name its locals. Inside SHOW, SHOW.N is N. Outside
  SHOW, PRINT SHOW.N stops the compile with LOCAL TO A SUB: SHOW.N.
- The locals of one SUB take at most 16384 bytes. The DIM that passes it stops
  the compile with LOCALS TOO BIG.
- The SUBs of one level of the call graph share the memory of their locals.
  The compiler does not see a call through a pointer or SYS. A SUB called that
  way may share that memory with a SUB that is running.
- The main program's variables are not locals. Each has its own address and
  keeps its value.

## Namespaces

NAMESPACE name ... END NAMESPACE groups names. Inside it a name is used bare.
Outside it the name is qualified with a dot. ENDNAMESPACE is the same as END
NAMESPACE.

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

- A namespace body holds DIM, VAR, CONST, ENUM, SUB, FUNCTION, BIND, ERRORS
  and other namespaces, and nothing that runs.
- A namespace may hold namespaces: OUTER.INNER.B is B in INNER in OUTER.
- A NAMESPACE with the name of one already made opens it again, to add names.
- A name is found in the SUB or FUNCTION first, then in each namespace around
  it, then in the main program. Inside OUTER, INNER.B and OUTER.INNER.B are the
  same.
- A SUB's parameters and DIMs are local to it. Outside the SUB, SHOW.N stops
  the compile with LOCAL TO A SUB: SHOW.N.
- UXC is a reserved name.

See [[BIND]], [[Types]], [[Subroutines]].

## BIND

BIND name = target gives a second name to a variable, an array, a constant, a
SUB, a FUNCTION or a namespace. It costs nothing at run time.

```
BIND G = GFX
BIND P = GFX.PLOT
BIND C = GFX.COLOR
P(1, 2)
```

- The new name has the same mark as the target: BIND C$ = GFX.COLOR stops the
  compile with BIND NEEDS THE SAME MARK.
- A BIND belongs to the scope it is written in. A BIND in a SUB is the SUB's.
- A label cannot be bound.

See [[Namespaces]].

## Files

OPEN opens a file or a device by its UXDOS16 path and returns a handle. PRINT #
writes to the handle, INPUT # and LINPUT # read from it, and CLOSE closes it.
READ and WRITE move bytes between the handle and memory.

```
DIM F AS UWORD
F = OPEN("C:\LOG.TXT", O.WRITE)
IF F = NOFILE
  PRINT "CANNOT OPEN"
  END
ENDIF
PRINT #F, "SCORE"; 120
CLOSE F
```

When the program ends, UXDOS16 closes every handle it left open.

### OPEN

F = OPEN(name$, mode) returns a handle, a UWORD. The name is a literal or any
string expression. It is a UXDOS16 path, such as C:\DATA\LOG.TXT, or a device
name, such as CON. A path with no drive is on the current drive. The mode is one
of three names, written as the argument itself:

- O.READ opens the file to read.
- O.WRITE makes the file, and empties one that is there. The handle reads and
  writes.
- O.APPEND opens the file to write at its end, and makes the file when it is
  missing.

Any other mode stops the compile with MODE MUST BE O.READ, O.WRITE OR O.APPEND.

OPEN returns NOFILE when UXDOS16 cannot open or make the file: the file is
missing for O.READ, a directory of the path is missing, the file is read-only
for O.WRITE or O.APPEND, or no open-file entry is free. NOFILE is a built-in
constant, 65535.

- UXDOS16 has 8 open-file entries in all, and the console takes one. Files
  that a parent program holds open take entries too.
- PRINT # and WRITE to a handle opened with O.READ write nothing.
- O.APPEND on a file that is there gives a handle that only writes. READ from
  it returns 0, and INPUT # and LINPUT # read nothing.

### PRINT # and CLOSE

PRINT #F, items works as PRINT does, and writes to the handle.

- Each line ends with CR LF, 13 and 10. A trailing ; leaves them out.
- A comma between items writes a "," character, not spaces to a print zone.
- A number has a space before and after it, as on the screen.
  PRINT #F, "AB"; 5, "CD" writes AB 5 ,CD and CR LF.
- A constant handle 0, 1 or 2 is standard output: PRINT #2, "HI" is
  PRINT "HI". A handle in a variable writes to that handle.
- A handle that is not open stops the program with ?FILE NOT OPEN ERROR AT
  $xxxx.

CLOSE F closes the handle. CLOSE of handle 0, 1 or 2 does nothing. CLOSE of a
handle that is not open, NOFILE included, does nothing.

### INPUT #, LINPUT # and EOF

INPUT #F, variables reads fields from the file. LINPUT #F, L$ reads a whole
line, commas and quotes included. EOF(F) is 1 when the next read would return
nothing, and 0 otherwise.

```
DIM F AS UWORD, L$ * 80
F = OPEN("DATA.TXT", O.READ)
IF F = NOFILE
  PRINT "NO FILE"
  END
ENDIF
DO WHILE NOT EOF(F)
  LINPUT #F, L$
  PRINT L$
LOOP
CLOSE F
```

- A field ends at a comma or at the end of a line. A number variable gets the
  field's value as VAL reads it. A LONG or ULONG variable is read in 32 bits.
- The rest of the line stays for the next read. Keyboard INPUT drops it.
- No prompt string is allowed after #F,.
- A line ends at CR, LF or CR LF. The line ending is not stored.
- A field or line longer than the string is cut, and the rest of it is skipped.
- At the end of the file a string gets "" and a number gets 0.
- EOF is 1 right after an empty file is opened. EOF(NOFILE) is 1.
- Handle 0 is standard input: LINPUT #0, L$ reads it.
- A read from a handle that is not open stops the program with ?FILE NOT OPEN
  ERROR AT $xxxx.

See [[INPUT and LINPUT]].

### READ and WRITE

N = READ(F, address, max) reads up to max bytes from the file into memory at
the address. It returns the count read, a UWORD. WRITE F, address, count
writes count bytes from memory at the address to the file.

```
DIM F AS UWORD, N AS UWORD, B(100) AS UBYTE
F = OPEN("DATA.BIN", O.READ)
N = READ(F, @B, 100)
CLOSE F
F = OPEN("COPY.BIN", O.WRITE)
WRITE F, @B, N
CLOSE F
```

- The address is any UWORD expression. @B is the address of an array or a
  variable. @S$ + 2 is the text of a string, after its max and length bytes.
  A number such as $A000 is a fixed address.
- Bytes move as they are, CR, LF and 0 included. No line ending is added or
  dropped.
- READ returns 0 at the end of the file, and on any error but a handle that
  is not open.
- READ, INPUT #, LINPUT # and EOF can be mixed on the same handle. EOF stays
  right after a READ.
- READ(0, ...) reads standard input. WRITE 1 writes to standard output, and
  WRITE 2 to standard error. WRITE 1, @S$ + 2, 2 prints the first two
  characters of S$.
- READ or WRITE on a handle that is not open, NOFILE included, stops the
  program with ?FILE NOT OPEN ERROR AT $xxxx.
- PRINT #, INPUT # and LINPUT # make a UXDOS16 call for each character. READ
  and WRITE make one call for the whole block.

See [[Arrays]] and [[Strings]] for @name.

## ASM

ASM puts bytes into the code where the statement stands. ASM with items puts
them in on one line. ASM alone opens a block, and END ASM or ENDASM closes it.
When the bytes end, the program goes on with the next statement.

```
DIM N AS UBYTE, W AS UWORD
ASM $A9, 65, $20, $FFD2      ' lda #65 : jsr CHROUT
ASM
    $A9, 66          ' lda #66
    $8D, @N          ' sta N
    $8D, @W + 1      ' sta the high byte of W
END ASM
```

- A line of a block is a 65C02 instruction or a list of items split by commas.
- A line may start with a label, name:.
- Empty lines and comments are allowed in a block.
- The code must keep X. X indexes the expression stack.

### Items

An item is a constant expression, @name or AddrOf(name). The compiler folds
it to a value.

- A constant 0 to 255 is one byte.
- A constant 256 to 65535 is two bytes, low byte first.
- A negative constant n is 65536 + n, so -1 is two bytes, $FF, $FF.
- A LONG constant, over 65535 or under -32768, stops the compile with NUMBER
  TOO BIG.
- @name and AddrOf(name) are two bytes, the address of the variable or array.
- @name + n and @name - n, with n a constant, are addresses too.

$0050 is one byte, $50. The size follows the value, not the digits written.
Write $50, $00 for a two-byte operand below 256.

### Instructions

A line whose first word is a 65C02 mnemonic is an instruction. Upper and lower
case are the same.

```
DIM M$ * 8
DIM PTR AS UWORD AT $24
M$ = "HI"
ASM
    lda #<@M$
    sta @PTR
    lda #>@M$
    sta @PTR + 1
    ldy #2
next: lda (@PTR),y
    jsr $FFD2
    iny
    cpy #4
    bne next
END ASM
```

The operands:

- None, or A: implied, or the accumulator.
- #n, #<n, #>n: immediate. n, its low byte, its high byte.
- n, n,X, n,Y: zero page or absolute.
- (n), (n,X), (n),Y: indirect.
- label: a branch, JMP or JSR.
- n, label: BBR0-BBR7 and BBS0-BBS7.

- An operand is a constant expression, @name or AddrOf(name).
- A known value below 256 takes the zero-page form when the instruction has
  one. A constant and the @name of a DIM ... AT are known values.
- Any other @name takes the absolute form. #<@name and #>@name are its bytes.
- An operand that starts with ( is indirect.
- A label belongs to its block. A branch, JMP or JSR may name a label further
  down.
- A block holds 32 labels, and 32 uses of a label further down.

### Errors

- An item that is not a constant or @name stops the compile with ASM TAKES A
  CONSTANT OR @NAME.
- A string item stops the compile with TYPE MISMATCH.
- An instruction without the mode its operand asks for stops the compile with
  NO SUCH ADDRESS MODE.
- An immediate or zero-page operand over 255 stops the compile with NOT A
  BYTE. So does #@name.
- A branch to a name that is not a label stops the compile with BRANCH TAKES
  A LABEL.
- A branch further than 127 bytes stops the compile with BRANCH OUT OF RANGE.
- A label defined twice in a block stops the compile with DUPLICATE LABEL.
- A label that the block does not define stops the compile with LABEL NOT
  FOUND, at the line that uses it.
- A 33rd label, or a 33rd use of a label further down, stops the compile with
  TOO MANY ASM LABELS.
- ASM alone with no END ASM before the end of the source stops the compile
  with ASM WITHOUT END ASM, at the line of the ASM.
- END ASM or ENDASM with no block open stops the compile with END ASM WITHOUT
  ASM.

See [[Arrays]] and [[Strings]] for @name, and [[Pointers]].

## SYS

SYS a calls the machine code at address a. The address is any UWORD
expression: a constant, a variable or @name.

```
DIM REG_A AS UBYTE AT $030C, REG_X AS UBYTE AT $030D
DIM REG_Y AS UBYTE AT $030E, REG_P AS UBYTE AT $030F
REG_A = 65
SYS $FFD2                    ' CHROUT prints A
```

- Before the call SYS loads A, X, Y and P from $030C, $030D, $030E and $030F.
  After the call it stores the four back there. X16 ROM BASIC does the same.
- DIM ... AT names the four bytes, as in the example.
- SYS ANDs P with $F3, so D and I are clear during the call.
- Carry is bit 0 of REG_P. IF REG_P AND 1 THEN PRINT "FAILED" tests the carry
  a call returns.
- The four bytes are not cleared when the program starts. Set what the call
  reads.
- The called code may change X. SYS keeps the program's X, which indexes the
  expression stack.
- A SYS to a constant address is 7 bytes of code. The routine behind it, 43
  bytes, is in the program once.
- A string address stops the compile with TYPE MISMATCH.

See [[ASM]], [[Declarations]].

# The compiler

## Compiling

pyuxc, the compiler, runs on the PC. Run it from the UXCBASIC folder with one
source file:

```
python pyuxc/pyuxc.py HELLO.UXB -I ../lib
```

- -I FOLDER adds an include folder. It may be given more than once. lib/ at the
  repo root holds CONS.UXI, DOS.UXI, HEAP.UXI, KEYS.UXI and STR.UXI.
- -o FOLDER is the folder of the PRG. The folder must exist. The default is
  the source's folder.
- --result FILE writes the result line to FILE as well.
- --keep-subs keeps every SUB and FUNCTION, as #KEEP ALL does.
- --keep-vars keeps every global variable, array and string literal.
- A relative folder is from the current folder.
- Any other option, or a count of sources other than one, prints the usage and
  exits with status 1.

The PRG is named after the source, in capitals: hello.uxb writes HELLO.PRG.

### Output

pyuxc prints the compiler's screen lines, then one result line. The screen
lines start with UXCBASIC 0.1 and COMPILING NAME.UXB.

- On success it prints NAME.PRG and its size, then OK,NAME.PRG,size. The size
  is the bytes of the file. The exit status is 0.
- The SUBs and FUNCTIONs that the main program never reaches are left out of
  the PRG. The result line then gets REMOVED n SUBS m BYTES, n the count and m
  the bytes saved.
- The global variables and arrays that no code names get no room. The result
  line then gets REMOVED n VARS m BYTES. m counts the variables and the array
  space.
- The string literals that no code names are left out. The result line then
  gets REMOVED n STRINGS m BYTES.
- On an error it prints ?MESSAGE IN N and the source line, then
  ERROR,N,MESSAGE. N is the line number. The exit status is 1. The first error
  stops the compile.

See [[Including files]], [[Errors]].

## Including files

#INCLUDE "NAME" compiles the file NAME in place of its line. The compiler reads
NAME, then the lines after the #INCLUDE.

```
' TOOLS.UXI holds FUNCTION TWICE(N AS UBYTE) AS UWORD
#INCLUDE "TOOLS.UXI"
PRINT TWICE(21)
```

- The compiler looks for NAME in the source's folder, then in each -I folder
  in the order given. See [[Compiling]].
- A file that is not found stops the compile with FILE NOT FOUND: NAME. An
  empty file counts as not found.
- An included file cannot include another file. A #INCLUDE in one stops the
  compile with #INCLUDE IN AN INCLUDED FILE.
- An error in an included file reports the line of the #INCLUDE, with the file
  name and its own line: SYNTAX ERROR (LIB.UXI 2).

See [[Strings]], [[Subroutines]].

## Targets

pyuxc, the compiler on the PC, makes a program for UXDOS16. The program calls
the UXDOS16 API in place of the KERNAL, and does not run on the stock X16 ROM.

```
python pyuxc/pyuxc.py HELLO.UXB
```

On UXDOS16:

- A handle is a UXDOS16 handle. Handles 0, 1 and 2 are standard input,
  output and error. PRINT #1 writes to standard output, and READ and INPUT #
  read handle 0.
- PRINT writes to standard output. PRINT and PRINT # end a line with CR LF.
- INPUT and LINPUT read a line of up to 80 characters with UXDOS16's line
  editor.
- The screen stays in CP437. The start and the end do not change the
  character set.
- END returns to the program that ran this one, with the exit code after END,
  or 0. A run-time error returns 0.
- At its start the program gives UXDOS16 the page where its variables end.
  When it runs another program, UXDOS16 saves its RAM only up to that page.
  RAM above it, written with POKE or ContentsAt, is lost then.

See [[Files]], [[INPUT and LINPUT]], [[END]].

## Options

To be written: the #DEFINE UXC.* lines.

## ERRORS ON and OFF

ERRORS OFF leaves out the run-time index checks on arrays in the code after it.
ERRORS ON puts them back. ON is the default.

```
DIM B(10) AS UBYTE, I AS UBYTE
ERRORS OFF
B(I) = 1
ERRORS ON
```

- The switch follows the source, not the run: it applies to the lines below it
  in the file.
- With the checks off, an index out of range reads or writes the memory past
  the array.
- Code under ERRORS OFF is smaller and faster.
- A constant index is checked at compile time in both modes.

See [[Arrays]].

## Errors

To be written.
