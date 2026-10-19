# Inline assembly: design notes

These notes cover TODO 4: 6502 code inside a BASIC program, with BASIC variables passed in and
out. Nothing here is built yet. All byte counts are estimates, and some design decisions are
still open (see the end).

## Goal

Today machine code is POKEd from `DATA` and started with `SYS`. That works, but the code is hard
to read, and values pass only through memory that the program has to PEEK and POKE. The aim:

```
100 ASM AUTO
110 .START
120   LDA #N
130   STA VARPTR(X)
140   JSR $FFD2
150   RTS
160 END ASM
170 SYS START,65
```

`ASM AUTO` puts the code in the code area, so the program does not pick an address. `ASM $C000`
puts it at a fixed address instead.

## Budget

| Phase | What | Bytes (est.) |
|---|---|---|
| A | `SYS addr[,a[,x[,y]]]` and `VARPTR(v)` | 45-70 |
| B | fixed code area, `ASM AUTO` | 35-50 |
| C | assembler in ROM (`ASM` ... `END ASM`) | 1000-1500 |
| C, other option | assembler loaded into RAM from disk | about 10 in ROM (a hook) |

The image has 4072 bytes free. SUB and FUNCTION (TODO 2) are estimated at 580-1030 bytes, and
real integer math (TODO 3) at a large amount. An assembler in ROM would take about a third of
the free space.

## What other BASICs do

### EhBASIC 2.22

EhBASIC has no inline assembler. What it has for machine code (`basic.asm`):

- `CALL addr` pushes a return address and jumps. It loads no registers and returns nothing.
- `USR(x)` calls through a `JMP` vector in zero page, as ours does.
- `VARPTR(v)` is 4 calls: next character, get variable address, check `)`, convert the address
  to a number. About 15 bytes of code, so our 20-30 estimate was high.
- `SADD(a$)` gives the address of a string's text (about 20 bytes). We do not need it:
  `DEEK(VARPTR(A$)+1)` gives the same value.

### BBC BASIC

BBC BASIC has the classic inline 6502 assembler. Lessons from it:

- `[` starts assembly and `]` ends it. No keyword is needed.
- `OPT n` at the start of each pass controls it: bit 0 lists the code, bit 1 reports errors, and
  bit 2 (BASIC 2 and later) turns on offset assembly. The usual form:

  ```
  DIM code% 100
  FOR pass% = 0 TO 3 STEP 3
    P% = code%
    [OPT pass%
    ...
    ]
  NEXT pass%
  ```

  Pass 0 reports no errors, so forward labels do no harm. Pass 3 lists and reports errors.
- `P%` is the program counter, an ordinary variable that the program sets and reads.
- **Offset assembly:** the code is assembled for the address in `P%` but stored at `O%`. This is
  how code is built in one place and run in another. It is the model for the future bank option
  (see Phase B).
- `DIM code% 100` reserves 101 bytes in the heap. That works because variables in BBC BASIC never
  move. In MS BASIC arrays and strings move, so this does not carry over. `ASM AUTO` and the fixed
  code area take its place.
- `.name` sets a variable to the current address. All characters of the name count. Ours count
  only 2 (see Labels).
- `EQUB`, `EQUW`, `EQUD` and `EQUS` (BASIC 2) put bytes, words, 4-byte values and strings in the
  code.
- `CALL addr` loads A, X and Y from `A%`, `X%` and `Y%`, and the carry from `C%`. `USR(addr)`
  does the same and returns P, Y, X and A packed into one 32-bit integer. Our `SYS` arguments and
  4 RAM bytes do the same job with less code.
- `\` starts a comment after an instruction. Ours: `:REM`, or `'` once it works as REM.

## Phase A: pass values to machine code

Phase A is useful without an assembler, and every later phase needs it.

### SYS with registers

`SYS addr[,a[,x[,y]]]`

- Loads A, X and Y from the optional arguments, then calls the code.
- After the `RTS`, stores A, X, Y and the status flags in 4 fixed RAM bytes, so `PEEK` reads
  them (as on the C64). The address of the 4 bytes is set per target.
- Today `SYS` in `handle_io.s` is only `FRMNUM`, `GETADR` and `jmp (LINNUM)`. The register
  arguments reuse `COMBYTE`, so no new parse code is needed.
- Estimate 30-40 bytes.

### VARPTR

`VARPTR(v)` gives the address of a variable's value.

- It reuses `PTRGET`, as EhBASIC does. Estimate 15-20 bytes, plus about 8 for the keyword table
  entry.
- The value at that address:
  - float: 5 bytes in MS format;
  - `%` integer: 2 bytes, high byte first;
  - string: a 3-byte descriptor (length, then the address, low byte first).
- **A simple variable keeps its address** until `CLR`, `RUN` or a program edit. New simple
  variables go at the end of the simple-variable table and move only the arrays.
- **An array moves** each time a new simple variable is created. Take `VARPTR` of an array
  element after all simple variables exist.

`USR(x)` is already in the sim build. It passes FAC to the code at the `USR` vector and returns
FAC, which covers a single number.

## Phase B: where the code lives

Code stored inside the program text is not an option: the program text moves whenever lines are
edited, and an absolute `JMP` inside it would break.

### Fixed code area

- Each target sets a RAM area for code, for example 1 KB right below the ROM. In the sim that is
  below $C000, so the RAM scan at cold start must stop under it.
- The area never moves, so labels set while assembling stay valid.
- The SUB and FUNCTION RAM stack (see `docs/sub-function.md`) is taken from the top of BASIC's
  memory, which ends below the code area. The two cannot overlap.
- `ASM addr` can still write anywhere the program likes.

### ASM AUTO

- A 2-byte pointer, the code top, starts at the bottom of the code area.
- `ASM AUTO` starts the program counter at the code top. On the final pass, `END ASM` moves the
  code top to the program counter, so the next `ASM AUTO` block goes after this one.
- On a first pass (see Two passes) the code top does not move, so both passes write to the same
  place.
- If the code passes the end of the area: `?OUT OF MEMORY`.
- `RUN` and `CLR` reset the code top, because the program assembles its code again when it runs.
- The program finds the start through a label: `.START` as the first line of the block, then
  `SYS START`. No extra ROM code.
- `AUTO` is not a keyword. With `CONFIG_NAME_NOCRUNCH` it is stored as plain text, and `ASM`
  compares the 4 letters. A variable named `AUTO` cannot be the address; write `ASM (AUTO)` if
  that is needed.
- Estimate 35-50 bytes: the word test, the pointer setup, the update in `END ASM` with the range
  check, and the reset at `RUN`.

### Later: code in a bank

The new hardware may have banked RAM. Later, `ASM AUTO` could put the code in a bank:

- Every byte the assembler stores goes through one store routine. A bank version replaces only
  that routine, with a target primitive like `K_VPOKE` or the planned far-memory `POKE`.
- The code is assembled for the address where it runs (the bank window) and stored in the bank,
  as in BBC BASIC's offset assembly.
- This waits for the far-memory decision (deferred, see the project status). Nothing in the first
  version should block it: keep the store routine in one place.

## Phase C: the assembler

### Syntax

- `ASM addr[,pass]` or `ASM AUTO[,pass]` ... `END ASM`, the same block style as `IF` / `END IF`
  and `DO` / `LOOP`. `END` is already a token, so only `ASM` is a new keyword.
- The other option is the BBC BASIC style `[` ... `]`. It needs no keyword, but `[` and `]` are
  not used anywhere else in this BASIC.
- One instruction per statement; `:` separates statements, as in BASIC.

### How it runs

- The block runs while the program runs. Each instruction writes its bytes from the start
  address onward, and a program counter (the next address) moves along.
- **Operands are BASIC expressions.** `LDA #N`, `STA VARPTR(X)`, `JSR $FFD2` and `LDA #%1010`
  all work, because the `$` and `%` literals already exist (`radixlit.s`).

### Labels

- `.L1` sets the BASIC variable `L1` to the current address.
- Only 2 characters of a variable name count, so label names collide easily: `.LOOP1` and
  `.LOOP2` are the same label. A label lookup that scans the program text, as `LABEL_FIND`
  does, would let every character count, at about 60-100 extra bytes.

### Two passes

- A jump to a label further down needs two passes. The program runs the block twice, as in BBC
  BASIC:

  ```
  100 FOR P=0 TO 1
  110 ASM AUTO,P
  ...
  190 END ASM
  200 NEXT P
  ```

- The optional `pass` argument works like BBC BASIC's `OPT`, cut down to one bit: 0 is a first
  pass, 1 (the default) is the final pass. A first pass gives no error for an unknown label and
  does not move the code top. A block without forward jumps needs only one run, without the
  argument.
- No listing option. That saves bytes.

### How the tokenizer sees assembly lines

Assembly lines are tokenized like any other line, so the assembler reads tokens.

- With `CONFIG_NAME_NOCRUNCH`, a keyword with a letter right behind it is not a keyword, and a
  letter right after a letter is stored as it is. So `ORA` and `EOR` stay plain text.
- `AND` is the one 6502 mnemonic that is also a BASIC keyword. It is stored as `TOKEN_AND`,
  and the assembler accepts that token as the `AND` mnemonic.
- `#`, `(`, `)`, `,X` and `,Y` stay plain text.

### Tables and code size

| Part | Bytes (est.) |
|---|---|
| 56 mnemonic names (plain text 168, or packed 5 bits per letter) | 112-168 |
| opcode and addressing-mode tables | about 100 |
| operand parser (`#`, `(zp,X)`, `(zp),Y`, `abs,X`, zero page or absolute) | 300-500 |
| statement dispatch, program counter, byte output | 100-200 |
| labels (`.name`) | 40 |
| two passes (`pass` argument, no error on a first pass) | 30 |
| branch offsets and range check | 50 |
| **Total** | **about 750-1100**, with margin **1000-1500** |
| optional: `BYTE` / `WORD` / string data, like BBC BASIC's `EQUB` | 40-60 |

### The option of an assembler in RAM

The assembler could be a program loaded from disk into RAM. The ROM then needs only a hook:
`ASM` jumps through a RAM vector that the loaded program sets (about 10 bytes). This costs
almost no ROM, but it needs the new kernal's file calls, and the assembler takes RAM while it
is loaded.

## CONST and typed BYTE / WORD

`CONST` is parked in TODO 4, because `BYTE` and `WORD` declarations belong to this design.

- In an assembler, BYTE and WORD have a real use: they pick zero-page or absolute addressing
  and range-check immediate operands (`LDA #WHITE`).
- A cheap form uses the program text as the symbol table: a `CONST name value` line is found by
  a scan like `LABEL_FIND`. All characters of a name count, and labels, constants and assembly
  labels share one namespace. Estimate 60-100 bytes on top of the assembler.
- Infer the size from the value (below 256 is a BYTE) and keep `WORD` only as an override. That
  drops the `BYTE` keyword.
- `PI` is a keyword, so no constant can be named `PI`.

## Plan

1. Phase A: `SYS` with registers, then `VARPTR`. Each with tests, an entry in
   `docs/changes.md` and its own commit, behind `.ifdef` so `cbmbasic1` and `cbmbasic2` stay
   unchanged.
2. Phase B: the fixed code area in the sim memory map (cold-start RAM scan stops under it). The
   code top pointer and `ASM AUTO` come with the assembler, since they need `ASM`.
3. Decide on the assembler after SUB and FUNCTION are built and their real size is known.
4. If the assembler goes in ROM: mnemonic table and one addressing mode first (implied, as
   `RTS`), then immediate, then zero page and absolute, then the indexed and indirect modes,
   then branches, labels and the `pass` argument, then `ASM AUTO`. Test each mode against bytes
   that ca65 produces for the same code.

## Open decisions

1. Assembler in ROM, as a program loaded into RAM later, or phase A only?
2. `ASM` / `END ASM` or BBC-style `[` ... `]`? With `[` the form would be `[AUTO` or `[addr`.
3. Start now, ahead of `'` as REM and SUB, or keep the TODO order?
4. Size of the code area in the sim (1 KB suggested), and its address on the new hardware.

Decided: `ASM AUTO` picks the address from a fixed code area, the program finds the start
through a label, and a bank may hold the code later.

Recommendation: build phase A now, because it is cheap and every option needs it. Decide on the
assembler after SUB and FUNCTION show their real cost.

## Ways to save bytes

- `VARPTR` reuses `PTRGET`, and the `SYS` register arguments reuse `COMBYTE`.
- Leave out `SADD`: `DEEK(VARPTR(A$)+1)` does the same.
- Pack the mnemonic names at 5 bits per letter (saves about 56 bytes; the unpack code costs
  about 20).
- Let BASIC expressions parse every operand; the assembler parses only the addressing-mode
  marks around them.
- One pass bit instead of BBC BASIC's `OPT` bits, and no listing.
- `AUTO` as plain text, not a keyword: no token, no keyword table entry.
- Reuse existing error messages (`?SYNTAX ERROR`, `?ILLEGAL QUANTITY`, `?OUT OF MEMORY`) instead
  of new text.
