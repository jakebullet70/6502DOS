# Zero page for the 6502dos target

The audit of the `sim` build's zero page, and the layout of the `6502dos` target
(`src/6502dos_zp.s`). Counts are of the instructions in `build/sim.lst` that emit a zero page
operand.

## The limits

- A 6502DOS program owns `$22-$7F`: 94 bytes. `$02-$21` are the API registers `r0` to `r15`.
  The kernel owns `$80-$FF`.
- The `sim` build uses 162 bytes: `$00-$12`, `$5B-$DF` and `$F0-$F9`.
- `$13-$5A` is unused in `sim`: `INPUTBUFFER` is at `$0200`.

## What needs zero page

A byte needs zero page when an instruction reaches it in one of these ways:

- `(zp),y` or `(zp,x)`: no absolute form.
- `sty zp,x` or `stx zp,y`: no absolute form.
- `n,x` with a small `n`, where `X` holds the byte's zero page address: `PUTEMP` does
  `sta 0,x` into `TEMPST`, and `SHIFT_RIGHT` does `sty 1,x` to `sty 4,x` on `RESULT`, `FAC`
  and `ARG`.
- `CHRGET` runs in zero page, and `TXTPTR` is the operand of its `lda`. 18 instructions read
  `(TXTPTR),y`.

| Address in `sim` | Bytes | Name | Accesses | Reached by |
|---|---|---|---|---|
| `$11` | 2 | `LINNUM` | 64 | 11 `(zp),y` |
| `$69` | 9 | `TEMPST` | 0 | `sta 0,x` in `PUTEMP` |
| `$72` | 2 | `INDEX` | 128 | 42 `(zp),y` |
| `$74` | 2 | `DEST` | 19 | 10 `(zp),y` |
| `$76` | 5 | `RESULT` | 31 | `sty n,x` in `SHIFT_RIGHT` |
| `$7B` | 2 | `TXTTAB` | 27 | 3 `(zp),y` |
| `$85` | 2 | `FRESPC` | 6 | 1 `(zp),y` |
| `$93` | 2 | `INPTR` | 9 | 1 `(zp),y` |
| `$97` | 2 | `VARPNT` | 15 | 1 `(zp),y` |
| `$99` | 2 | `FORPNT` | 30 | 5 `(zp),y` |
| `$9E` | 2 | `TEMP3`, `FNCNAM` | 33 | 12 `(zp),y` |
| `$A0` | 3 | `DSCPTR` | 42 | 8 `(zp),y` |
| `$A7` | 28 | `TEMP1` to `STRNG2` | 665 | 72 `(zp),y`, `sty zp,x`, `sty n,x` |
| `$C3` | 24 | `CHRGET`, `TXTPTR` at `$CA` | 105 | 18 `(TXTPTR),y` |
| `$F7` | 2 | `KW_PTR` | 10 | 5 `(zp),y` |
| | 89 | | | |

The 28-byte block from `TEMP1` to `STRNG2` holds `HIGHDS`, `HIGHTR`, `TEMP2`, `INDX`,
`EXPON`, `LOWTR`, `EXPSGN`, `FAC`, `FACSIGN`, `SERLEN`, `SHIFTSIGNEXT`, `ARG`, `ARGSIGN`,
`STRNG1` and `STRNG2`.

## What does not need zero page

These bytes are reached only by plain `zp` and `zp,x` instructions, which have absolute forms.

| Address in `sim` | Bytes | Names | Accesses |
|---|---|---|---|
| `$00` | 13 | `GORESTART`, `GOSTROUT`, `GOAYINT`, `GOGIVEAYF`, `USR` | 17 |
| `$0D` | 4 | `Z15`, `POSX`, `Z17`, `Z18` | 13 |
| `$5B` | 11 | `CHARAC`, `ENDCHR`, `EOLPNTR` (20), `DIMFLG`, `VALTYP` (28), `DATAFLG`, `SUBFLG`, `INPUTFLG`, `CPRMASK`, `Z14` | 116 |
| `$66` | 3 | `TEMPPT`, `LASTPT` | 11 |
| `$7D` | 8 | `VARTAB`, `ARYTAB`, `STREND`, `FRETOP` | 81 |
| `$87` | 2 | `MEMSIZ` | 8 |
| `$89` | 2 | `CURLIN` | 31 |
| `$8B` | 8 | `OLDLIN`, `OLDTEXT`, `Z8C`, `DATPTR` | 21 |
| `$95` | 2 | `VARNAM` | 28 |
| `$9B` | 3 | `LASTOP`, `CPRTYP` | 10 |
| `$A3` | 4 | `DSCLEN`, `JMPADRS`, `Z52`, `ARGEXTENSION` | 21 |
| `$DB` | 5 | `RNDSEED` | 0 |
| `$F2` | 5 | `CURDVC`, `Z96`, `BLK_DEPTH`, `BLK_LAST`, `BLK_MODE` | 46 |
| `$F9` | 1 | `POSY` | 4 |
| | 71 | | 407 |

`SIM_CSP` (`$F0`, 2 bytes) is for sim65 only.

## Traps

- Order inside a group counts. `JMPADRS` is `DSCLEN+1`, and `jsr JMPADRS` runs the `JMP` it
  holds. `FACEXTENSION` is `STRNG1+1`. `LOWTR` is 1 byte and `EXPSGN` is its high byte.
  `VALTYP+1` is the integer flag.
- `REASON` pushes `TEMP1` to `FAC-1` with `lda TEMP1,x` around `GARBAG`. It pulls them back
  with `ldx #<(TEMP1-FAC+1)`, an index of `$F7`, and `sta FAC,x`, which relies on zero page
  wrap. Out of zero page the store lands 247 bytes past `FAC`.
- `TEMPPT` holds only the low byte of a `TEMPST` entry, and `LASTPT+1` is 0. `cpx #TEMPST+9`
  tests for a full stack.
- `ldx #TEMP2`, `#TEMP3`, `#FAC` and `#ARG` pass an address with a high byte of 0.
- `RNDSEED` follows `CHRGET` in ROM, and `init.s` copies both in one loop. `rnd.s` passes its
  full address, so it can live outside zero page.
- `TXTPTR` must stay at `CHRGET+7`.
- ca65 picks the absolute form for a symbol of `$100` or more. No source forces the zero page
  form with `z:` or `<` on a variable.
- `STACK_TOP` is `$FA` because `$01FD-$01FF` lie in front of `INPUTBUFFER` at `$0200`. On
  6502DOS, `$0200-$02FF` is the monitor's input and output line, and `exec` does not save it.

## Layout

The 89 bytes that need zero page fill `$22-$7A`. The 5 left go to the bytes with the most
accesses for each byte: `CURLIN` (31), `VALTYP` (28) and `EOLPNTR` (20). The order of the groups
is the order of `sim`.

| Address | Bytes | Names |
|---|---|---|
| `$22` | 2 | `LINNUM` |
| `$24` | 1 | `EOLPNTR` |
| `$25` | 2 | `VALTYP` |
| `$27` | 9 | `TEMPST` |
| `$30` | 2 | `INDEX` |
| `$32` | 2 | `DEST` |
| `$34` | 5 | `RESULT` |
| `$39` | 2 | `TXTTAB` |
| `$3B` | 2 | `FRESPC` |
| `$3D` | 2 | `CURLIN` |
| `$3F` | 2 | `INPTR` |
| `$41` | 2 | `VARPNT` |
| `$43` | 2 | `FORPNT` |
| `$45` | 2 | `TEMP3`, `FNCNAM` |
| `$47` | 3 | `DSCPTR` |
| `$4A` | 28 | `TEMP1` to `STRNG2` |
| `$66` | 24 | `CHRGET`; `TXTPTR` at `$6D` |
| `$7E` | 2 | `KW_PTR` |

## RAM

| Address | Bytes | What |
|---|---|---|
| `$0801` | 15 at most | `MSBASIC.COM`, the stub |
| `$0810` | 66 | The RAM data: the 71 bytes of the second table less `CURLIN`, `VALTYP` and `EOLPNTR` |
| `$085B` | 5 | `INPUTBUFFER-5` to `-1` |
| `$0860` | 81 | `INPUTBUFFER`: `LINE_MAX` 80 characters and the CR |
| `$0900` | | A 0 byte, then the program text at `$0901` |
| `$9C00` | 645 | Segment `IORAM`: the `handle_io.s` data, the GOTO and variable caches, the DOS variables. `MEMSIZ` is `$9C00`. |

`INPUTBUFFER` must not cross a page, and no program text or string may share its page.
`CONFIG_INPUTBUFFER_0200` stays on: it copies `LINNUM` in front of the buffer, as any buffer
outside zero page needs.

## Cost

Bank 2 holds 11821 bytes, 410 more than the `sim` code. The difference is the absolute forms
of about 328 instructions, the 6502DOS calls in place of the sim65 calls, and 7 long branches. Each absolute form costs 1
cycle more; a `zp,x` that becomes `abs,x` costs nothing more unless it crosses a page.
