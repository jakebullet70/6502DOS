# 6502 notes for this project

The target CPU is the **NMOS 6502**. Do not use 65C02 opcodes. `65c02-instruction-reference.md`
in this folder describes the 65C02, which is a superset; this file lists what differs and the rules
we follow. Adapted from the x16-blitz `asm-65c02` agent notes.

## Not allowed (65C02 only)

- Instructions: `STZ`, `BRA`, `PHX`, `PLX`, `PHY`, `PLY`, `TRB`, `TSB`, `STP`, `WAI`,
  `BBRx`, `BBSx`, `RMBx`, `SMBx`.
- Addressing modes: `(zp)` without an index (for example `LDA ($10)`), `JMP (abs,X)`,
  `BIT #imm`, `BIT zp,X`, `BIT abs,X`, `INC A`, `DEC A`.
- ca65 enforces this when the source uses `.setcpu "6502"` (the default for ca65).

## NMOS behaviour to remember

- **`JMP ($xxFF)` page-wrap bug:** the high byte is read from `$xx00`, not from the next page.
  Never place an indirect vector so that it starts on the last byte of a page.
- **Decimal mode:** after `ADC`/`SBC` in decimal mode, N, V and Z are not valid. The CPU does not
  clear D on interrupt, so an IRQ handler that does arithmetic must `CLD` first.
- **Read-modify-write** instructions (`INC abs`, `ASL abs`, …) write the old value back before
  the new one. This matters for I/O registers.
- Undocumented opcodes exist on NMOS parts. Do not use them.

## Flags

- **Z** is set when the result is 0. **N** is bit 7 of the result. **C** is unsigned carry/borrow
  and the shift carry; `CMP` sets C when `register >= operand`. **V** is signed overflow.
- **`LDA`/`LDX`/`LDY` do not change Carry.** Only `ADC`, `SBC`, `CMP`/`CPX`/`CPY` and the
  shifts/rotates do.
- `BIT abs`/`BIT zp` copy bit 7 of memory to N and bit 6 to V, and set Z from `A AND memory`.
- **B is not a real flag bit.** It exists only in the byte pushed by `PHP`/`BRK` (1) or by a
  hardware IRQ (0).
- **`BRK` skips the byte after it**: the pushed return address is +2.

## Comparison branches (unsigned)

| logic | code |
|---|---|
| `A == imm` | `CMP #imm` / `BEQ` |
| `A != imm` | `CMP #imm` / `BNE` |
| `A < imm` | `CMP #imm` / `BCC` |
| `A >= imm` | `CMP #imm` / `BCS` |
| `A <= imm` | `CMP #imm` / `BEQ hit` / `BCC hit` |
| `A > imm` | `CMP #imm` / `BEQ skip` / `BCS hit` |

Signed: `SEC` / `SBC #imm` / `BVC :+` / `EOR #$80` / `:` then `BMI` or `BPL`.

## Cycles

Most instructions take 2–4 cycles. `JSR` and `RTS` take 6. Branches take 2 when not taken, 3 when
taken, 4 when taken across a page boundary. Zero page is 1 cycle and 1 byte cheaper than absolute.
`INX`/`DEX` beat `CLC`/`ADC #1` and leave Carry alone. `CMP` sets Carry, so no `CLC` before `BCC`.

Reference with cycle counts: <https://www.pagetable.com/c64ref/6502/?tab=4>

## ca65 basics

Assembler: `C:\8bitProgramming\cc65\bin\ca65.exe` (V2.19), linker `ld65.exe`, simulator
`sim65.exe`. Not on PATH.

- Segments: `.segment "CODE"`; memory layout comes from the ld65 `.cfg` file.
- Data: `.byte`, `.word`, `.dbyt` (big-endian word), `.res n`, `.asciiz`.
- Equates: `NAME = value`. Labels: `name:`. Cheap locals: `@name:` (scope ends at next normal
  label).
- Anonymous labels: `:` defines one; `:+` / `:-` refer to the next / previous one, `:++` two away.
- Conditionals: `.if` / `.elseif` / `.else` / `.endif`, `.ifdef`, `.ifndef`.
- Macros: `.macro name args` … `.endmacro`. Scopes: `.proc name` … `.endproc`.
- Numbers: `$1234`, `%1010`, `123`. Octal has no prefix in ca65; convert MACRO-10 `^O` values.
- Build: `ca65 -D TARGET file.s -o file.o` then `ld65 -C target.cfg file.o -o file.bin -Ln file.lbl`.
- `.feature` can enable extras; `.feature org_per_seg` and `.feature force_range` are common.
