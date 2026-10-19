# SUB and FUNCTION: design notes

These notes cover TODO 2, phases B (SUB) and C (FUNCTION). Phase A (labels) is done
(`labels.s`, `CONFIG_LABELS`). Nothing here is built yet. All byte counts are estimates, until
the code is written.

## Goal

QBasic-style procedures, in the same style as the block `IF` and `DO` that already exist:

```
100 CALL BOX(2,3,"HI")
110 PRINT FN AREA(3,4)+1
120 END
200 SUB BOX(X,Y,T$)
210   LOCAL I
220   FOR I=1 TO 3: TEXTAT X,Y+I,T$: NEXT
230 END SUB
300 FUNCTION AREA(W,H)
310   RETURN W*H
320 END FUNCTION
```

## Budget

| Part | Table | Code (est.) | Total (est.) |
|---|---|---|---|
| B: `SUB` / `END SUB`, `CALL`, `LOCAL` | 18 | 450-600 | 470-620 |
| C: `FUNCTION` / `END FUNCTION`, `RETURN expr` | 10 | 200-400 | 210-410 |
| C, optional: drop `DEF FN` (the `FN` token is reused) | -4 | about -100 | about -100 |
| **B + C** | | | **about 580-1030** |

The image has 4072 bytes free (image 12056 bytes). `docs/keywords.md` keeps the upper estimates
(618 and 410) until the code is written.

## How MS BASIC limits the design

- **There is only one global variable table.** A per-call table would mean rewriting `PTRGET`,
  and the variable cache would break.
- **Only 2 characters of a variable name count.** Parameters and LOCALs share those names with
  the rest of the program.
- **The 6502 stack has 256 bytes**, and `FRMEVL` uses a lot of it. `GOSUB` pushes 5 bytes, a FOR
  frame 18. Frames for nested or recursive calls cannot all fit there.
- **`TEMPST` holds only 3 temporary string descriptors.**
- **`GARBAG` sees only variables, arrays and `TEMPST`.** A string descriptor saved anywhere else
  is not seen, so its string can be moved or freed.
- **`NEWSTT` never returns.** The statement loop only jumps forward, so running statements from
  inside an expression needs a way back.

## Phase B: SUB

### Syntax

- `SUB name(a, b$, ...)` ... `END SUB`.
  - The name is a label-style name: all of its characters count, as with `name:` labels.
  - Parameters are simple variables only, passed by value. No arrays.
- `CALL name(args)`. The parentheses are left out when there are no arguments.
- `LOCAL v, w$, ...` on any line inside the SUB. It saves each variable and clears it.
- Not planned: `EXIT SUB`. Use `GOTO` to a line holding `END SUB`.

New keywords: `SUB`, `CALL`, `LOCAL` (and `FUNCTION` for phase C). `END` is already a token,
and `END SUB` is handled like `END IF`.

### Finding the SUB

- `CALL` scans the program for a line that starts with the `SUB` token followed by the name. The
  scan reuses the name compare in `LABEL_FIND`.
- The result is cached in the GOTO cache. The key is the text address of the `CALL`, as for
  `GOTO`, so later calls cost no scan.
- When normal flow reaches a `SUB` line, it skips to the matching `END SUB`. The skip reuses
  `BLK_SCAN` in `block.s` with a new mode.

### The RAM stack

Frames and saved values go on a separate stack in RAM, not on the 6502 stack.

- **Where:** at cold start, lower `MEMSIZ` by a fixed size, for example 256 bytes, so that the
  stack sits above string space. This costs about 10 bytes, and `FRE` shows the smaller number.
- **Frame:**
  - 1 byte: frame type (SUB or FUNCTION).
  - 1 byte: the 6502 stack pointer S on entry.
  - 2 bytes: `CURLIN` to return to.
  - 2 bytes: `TXTPTR` to return to.
  - 1 byte: count of saved variables.
  - 7 bytes for each saved variable: its address (2) and its old value (5).
- With 256 bytes, 10 nested calls with 3 variables each fit. A full stack gives
  `?OUT OF MEMORY`.
- `RUN`, `CLR`, `NEW` and every error reset the stack pointer, in the same places that reset
  the 6502 stack (`STKINI`).

### CALL, step by step

1. Evaluate all arguments first, with the old variable values. `CALL F(N-1)` with a parameter
   `N` must read the caller's `N`. Store each value in the RAM stack as a temporary.
   - A string argument stays a temporary descriptor in `TEMPST`, so a call takes at most 3
     string arguments. More give `?FORMULA TOO COMPLEX`. Lifting this limit means copying the
     strings, which costs more code.
2. Push the frame: type, S, `CURLIN` and the `TXTPTR` after the `CALL`.
3. Set `TXTPTR` to the SUB line and read the parameter list. For each parameter:
   - get its address with `PTRGET`;
   - push the address and the old value (5 bytes; an integer or a string descriptor uses fewer,
     but 5 keeps the code simple);
   - store the argument with the normal assignment code, so string arguments are copied into
     string space.
4. A count mismatch between arguments and parameters gives `?SYNTAX ERROR`.
5. Go on with the statement after the parameter list.

### LOCAL

`LOCAL` pushes the address and old value of each named variable onto the current frame, and
sets the variable to 0 or "". `LOCAL` outside a SUB or FUNCTION gives an error (reuse
`?RETURN WITHOUT GOSUB` or `?UNMATCHED BLOCK`).

### END SUB

1. Find the top frame. If there is none, or it is a FUNCTION frame, give an error.
2. Copy the saved values back, newest first, so a variable named twice gets its oldest value.
3. Restore S from the frame. This drops any FOR, DO or GOSUB frames left open inside the SUB,
   in the way `RETURN` drops FOR frames now.
4. Restore `CURLIN` and `TXTPTR`, pop the frame, and go on after the `CALL`.

### What stays valid

- **Variables never move.** A saved address points to a simple variable. Simple variables keep
  their place when new ones are created; only arrays move. So the variable cache stays valid,
  and so do the saved addresses.
- **Recursion works**, because each call saves the values it overwrites.

### Required fix: garbage collection

A saved string descriptor lies in the RAM stack, where `GARBAG` does not look. Without a fix,
`GARBAG` frees or moves that string, and `END SUB` restores a broken string.

- `GARBAG` must also walk the RAM stack and treat each saved string value like a variable.
  `CHECK_VARIABLE` in `string.s` does the work for one descriptor. Estimate 30-40 bytes.
- The saved entry needs to say whether it is a string. The type comes from the variable name,
  at the address minus 2. An extra flag byte for each entry is simpler, but it costs RAM.

### Byte estimate for phase B

| Part | Bytes (est.) |
|---|---|
| keyword table: `SUB`, `CALL`, `LOCAL` | 18 |
| skip SUB bodies in normal flow (new `BLK_SCAN` mode) | 30 |
| `CALL`: scan and cache (reusing `LABEL_FIND` and the GOTO cache) | 60 |
| argument evaluation and temporaries | 80 |
| parameter binding: `PTRGET`, save, assign | 90 |
| `LOCAL` | 40 |
| RAM stack: push, pop, reset, room check | 80 |
| `END SUB` restore loop | 60 |
| `GARBAG` scan of saved strings | 40 |
| **Total** | **about 500** |

Errors reuse existing messages, so no message text is added.

## Phase C: FUNCTION

### Syntax

- `FUNCTION name(a, b$)` ... `END FUNCTION`. A name that ends in `$` returns a string.
- `RETURN expr` inside the function sets the result and leaves. A plain `RETURN` still means
  the end of a `GOSUB`.
- The call is written `FN name(args)` inside an expression. The `FN` token already exists and
  makes the call plain to the expression evaluator. Without a prefix, `AREA(3,4)` looks like an
  array.
- `END FUNCTION` reached without a `RETURN expr` gives 0 or "".

### Option: drop DEF FN

`DEF FN` is a one-line function with one parameter. `FUNCTION` does everything it does. The sim
build could drop `DEF` and the `FN` code in `misc2.s` (`DEF`, `FNC`, `L31F3`), about 100 bytes
(to measure), and give the `FN` token to `FUNCTION`. Old programs with `DEF FN` would stop
working, which the project rules allow.

### Running statements from inside an expression

This is the hard part. `X = FN AREA(3,4)+1` must run whole statements and then come back into
`FRMEVL`.

The plan works like setjmp and longjmp:

1. The `FN` handler in `UNARY` evaluates the arguments and binds the parameters, as `CALL` does.
   It pushes a FUNCTION frame with the `TXTPTR` and `CURLIN` of the expression.
2. It calls `FN_RUN` with `jsr`. `FN_RUN` stores S, which now points at that return address,
   in the frame. Then it jumps to `NEWSTT` and the body runs as normal statements.
3. `RETURN expr` evaluates the expression into FAC, restores the saved variables and loads S
   from the frame. That one step drops everything the body pushed: the return addresses of
   `NEWSTT`, and FOR, DO and GOSUB frames.
4. It restores `TXTPTR` and `CURLIN` and does `rts`. That returns from `FN_RUN` into the `FN`
   handler, with the result in FAC, and the expression goes on.

### What must survive the call

- **FAC and ARG.** `FRMEVL` pushes the left operand on the 6502 stack before it evaluates the
  right one, so FAC and ARG should be free when a unary function starts. Check this in
  `eval.s` before building.
- **`TEMPST`.** In `A$ + FN F$(1)`, the descriptor of `A$` sits in `TEMPST` while the body runs.
  Statements inside the body that free temporaries must not take it. Check whether `NEWSTT` or
  a statement resets `TEMPPT`.
- **The 6502 stack.** Each nested call keeps a whole `FRMEVL` state on the 6502 stack, so
  recursion depth is limited, perhaps to 8-15 levels. `CHKMEM` must catch the overflow with
  `?OUT OF MEMORY` before the stack wraps.
- **The input buffer.** In direct mode, `PRINT FN F(1)` runs from the input buffer at $0200.
  An `INPUT` inside the function overwrites it. MS BASIC has the same problem with `GOSUB` from
  direct mode, so this is a known limit, not a fix.

### Byte estimate for phase C

| Part | Bytes (est.) |
|---|---|
| keyword table: `FUNCTION` | 10 |
| `FN` dispatch in `UNARY` to the new handler | 20 |
| `FN_RUN` (store S, jump to `NEWSTT`) | 20 |
| `RETURN expr`: frame test, evaluate, unwind | 60 |
| result type check (number or string) | 20 |
| keeping `TEMPST` and FAC safe | 40-80 |
| `END FUNCTION` without `RETURN` | 20 |
| skip FUNCTION bodies (shares the SUB skip) | 10 |
| **Total** | **about 200-240** |

Binding, the RAM stack and the `GARBAG` fix come from phase B, so phase C is smaller than the
first guess of 400. Keep the 400 in `docs/keywords.md` until the code shows the real size.

## Plan

Each step gets tests in `tests/`, an entry in `docs/changes.md` and its own commit. The code
goes in a new `sub.s` under `CONFIG_SUB`, so `cbmbasic1` and `cbmbasic2` stay unchanged.

1. RAM stack: reserve it at cold start, add push and pop, reset it in `STKINI`. No keyword yet.
2. `SUB` / `END SUB` with no parameters, `CALL name`. Skip bodies in normal flow. Test that
   FOR, DO and GOSUB frames left open inside a SUB are dropped.
3. Parameters, numbers only. Test recursion (a factorial with a parameter).
4. String parameters and the `GARBAG` fix. Test: a SUB that builds many strings and forces a
   collection while a saved string is out.
5. `LOCAL`.
6. `FUNCTION`, `FN name(...)`, `RETURN expr`. Test nested calls in one expression and
   `A$ + FN F$(...)`.
7. Optional: drop `DEF FN`.
8. Update `docs/keywords.md` with the measured sizes, and `CLAUDE.md`.

## Open decisions

1. Call syntax for SUB: `CALL name(args)` (planned), or the name alone as a statement (saves
   the `CALL` keyword, but needs a new path in the statement dispatcher).
2. Return value: `RETURN expr` (planned), or assignment to the function name as in QBasic. With
   2-character variable names, assignment to the name collides with variables.
3. Drop `DEF FN` in the sim build?
4. RAM stack size: fixed at 256 bytes, or set by the program?

## Ways to save bytes

- Store every saved value as 5 bytes. A per-type size saves RAM but costs code.
- Reuse existing error messages; add no new text.
- Share one routine for "save a variable onto the frame" between parameters and `LOCAL`.
- Share one routine for "restore and pop the frame" between `END SUB`, `END FUNCTION` and
  `RETURN expr`.
- Drop `DEF FN` (about 100 bytes) once `FUNCTION` works.
