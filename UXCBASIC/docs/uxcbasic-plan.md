---
name: uxcbasic-plan
description: "UXCBASIC (formerly called FBASIC): a ~20-command native-code BASIC compiler run from UXCEDIT, bootstrapped in GPC then self-hosted; the agreed shape before the design doc"
metadata:
  node_type: memory
  type: project
  originSessionId: 43e5164f-20f2-4482-bd3a-4ec033d4f8bc
  modified: 2026-10-08T16:49:57.052Z
---

On 2026-10-08 the user asked for a one-page design for UXCBASIC, and said to draft it after a compact.
UXCBASIC is a small, fast compiled BASIC for writing the system and utilities of the planned Unix-style
X16. On that machine BASIC is not in ROM, and GPC waits on a new MSBASIC that is parked behind the
kernel. Small-C on the machine was dropped (see [[x16-workstation-smallc]]).

The shape agreed in conversation:
- UXCEDIT is the editor. The UXCBASIC compiler is a separate program that UXCEDIT runs, like
  the GPC compile relay (see [[turbo-gpc-ide-plan]]).
- The compiler writes machine code directly from fixed templates, then patches the jump
  addresses. An optional `.LST` file gives a listing. It writes no asm text, because no
  stand-alone assembler runs on the X16 in our chain.
- The code is native, in the Prog8 style: `byte` and `word` types, static variables, no p-code
  and no stack frames. The PRG carries only the runtime routines it uses.
- Every system call goes through one jump table to the KERNAL. A port rewrites only that table.
- The bootstrap: v1 of the compiler is written in GPC. When UXCBASIC has files, byte arrays and
  strings, the compiler is rewritten in UXCBASIC. It then runs with no BASIC ROM and no GPC.
- The draft command set has about 20 commands:
  - `BYTE` `WORD` `BUF`
  - `IF/ELSE/ENDIF` `WHILE/WEND` `FOR/NEXT` `GOTO`
  - `PROC` `CALL` `RETURN`
  - `PRINT` `INPUT` `GETKEY`
  - `OPEN` `CLOSE` `READ` `WRITE` `DIR`
  - `PEEK` `POKE` `SYS` `ASM`

  Copy and sort are library procedures, not commands.

The user named it UXCBASIC on 2026-10-08. The parked Small-C fork in the WSL project is also in a
folder called `uxcbasic`; that folder is not this compiler.

**How to apply:** the design doc covers the command list, the types, the memory map and the output
format. Put it in docs/blitz/ as a `.PLAN.md` unless the user says otherwise. Write no code until the
user approves it. [[ask-before-writing-asm]] applies to the templates.
remind user to compact after each step.

