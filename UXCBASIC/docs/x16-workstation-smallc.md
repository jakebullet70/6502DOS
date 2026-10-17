---
name: x16-workstation-smallc
description: "The user's separate Small-C 6502 compiler project in WSL (uxcbasic, lib6502); paths, pipeline and how to test it"
metadata:
  node_type: memory
  type: project
  originSessionId: 43e5164f-20f2-4482-bd3a-4ec033d4f8bc
  modified: 2026-10-08T16:37:56.682Z
---

A second project, outside this repo: `\\wsl$\Ubuntu\home\steve\projects\x16-workstation`.
`uxcbasic/` is a git fork of SvenMichaelKlose/small-c (upstream moved to tunix) that writes
binary IR. Pipeline: `scc x.c` writes IR to `x.o`, `ir2txt` turns it into macro calls,
`bin/ca65-macros.asm` (master: `uxcbasic/src/6502/ca65-macros.asm`) assembles them,
ld65 links `lib6502/crt0.o2` first plus `lib6502/lib6502.lib` with `lib6502/x16.cfg` ($0801 PRG, SYS 2061).

Full state, rebuild steps and open items: `x16-workstation/SMALLC-NOTES.md`. Read it first
when the user comes back to this project.

The user's goal: a small compiler that runs on the X16 itself, with a dead-simple compiled BASIC on
top for a Unix-style workstation. The BASIC needs only a few commands: read, write, sort, dir,
input and copy. GPC already covers most of that goal (see [[name-the-compiler-gpc]]). On
2026-10-08 the user decided Small-C on the machine is not worth it, and the project is parked. The
user also declined trying cc64.

The planned Unix-style X16 has no BASIC in ROM. BASIC becomes a program you load, built from an
MSBASIC stub that is already on disk. GPC is to move over to it. The want behind the C work is a
small, fast compiled BASIC for writing the system and its utilities.

Upstream Small-C is not self-hosting on the X16. ops.c is 163 lines and compiles to 10,950 bytes.
At that rate, scc's 5,637 lines would not fit in main RAM.

On 2026-10-08 Claude made it run on the X16. Uncommitted at the time.
- Fixed: IR table params, ir2txt, `ir.c` emitters, text leaking into the IR, inverted
  import/export, signed compares, struct member index.
- Wrote: the macros, plus `lib6502` (crt0, runtime, putchar, puts).
- C names get a `_` prefix.

**How to apply:** after a compiler change, copy `scc`/`ir2txt`/macros into `bin/`, then
rebuild `lib6502`. Run from Windows with `wsl -d Ubuntu -- bash /tmp/script.sh`, passing
`MSYS_NO_PATHCONV=1`. Non-interactive WSL bash has no `bin/` on PATH. Test PRGs in x16emu with
`-warp -echo -run -prg` under `timeout`. Tests live in `test-src/compiler-tests` (ops.c
prints ALL PASS, ops2.c ALL PASS 2); `run.sh` there runs one from Git Bash. Original files
are in `research/claude-backup-2026-10-08`.

Known gaps:
- A function name used as a value fails with "undeclared variable".
- A bare `unsigned` declaration is not unsigned.
- Compiler errors print through libc `perror`, with no line number, and write junk into the `.o` file.
- `#asm` blocks write text into the `.o` file.
- C locals live on the 256-byte 6502 stack.
