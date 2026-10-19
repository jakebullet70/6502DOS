# Working in this repo

UXDOS16 is a replacement ROM operating system for the Commander X16, modelled on MS-DOS 2.0. The
base is ca65 asm, and the rest is UXCBASIC. The design and the order of work are in
`docs/PLAN.md`. The current state is in `docs/HANDOFF.md`; read it first.

MS-DOS 2.0's source is at `github.com/microsoft/MS-DOS`, folder `v2.0`, MIT licence. Take ideas
from it, not code.

UXCBASIC, the compiler, lives in `UXCBASIC/`. Its `CLAUDE.md` covers how to run the compiler and
its tests. The language reference is `UXCBASIC/help/UXC-HELP.md`; grep it for a topic, it is
long. `UXCBASIC/docs/UXCBASIC.PLAN.md` is the compiler's to-do list, where the features in PLAN
§12 must land. `attic/gpc` holds the frozen GPC compiler; nothing uses it.

MSBASIC, Microsoft BASIC for 6502 in ca65 (a fork of mist64/msbasic), lives in `MSBASIC/`. Its
`CLAUDE.md` covers its build, tests and rules. It builds with its own `Makefile`, apart from the
ROM.

The memory notes of the old `C:\dev\UXCBASIC` folder do not load in this folder. The rules from
them that apply here are below.

## Standing orders

- Ask before writing any asm.
- Time every build and run it in the background. Record each build time as the next baseline.
  A build well past its baseline is locked: stop it, kill the emulator by PID, and say so.
- Run one test at a time, time it, and report it before the next: the name, pass or fail, and
  the time. A test past 5 s is a failure to investigate at once.
- Run the full suite every 7th step only, and only when single tests pass. After any other step,
  run the tests of the code touched. `docs/HANDOFF.md` counts the steps since the last full
  suite.
- Kill the emulator by its PID or handle only, never by image name.
- No `git init` until the user says so.
- Bash heredocs with complex quoting fail. Use Write/Edit, or a Python script in the scratchpad.
- Explain new syntax to the user with an example.

## Tools

| Tool | Where |
|---|---|
| ca65, ld65 V2.19 | `tools/cc65/bin`, in the repo. Never call the copies on PATH. |
| 64tass 1.60 | `tools/64tass`, in the repo, for the UXCBASIC templates only |
| make 4.4.1 | `C:\8bitProgramming\make-4.4.1`, on PATH |
| x16emu R49 | `C:\8bitProgramming\x16emu\x16emu.exe` |
| Python | `/c/Users/Admin/AppData/Local/Programs/Python/Python313/python.exe`; `python` is not on PATH. Open files with `encoding='utf-8'`. |

## Compact

Remind the user to `/compact` after every step. Update `docs/HANDOFF.md` first, so the work
survives the compact.

## Prose

Docs and comments follow `.claude/agents/doc-style.md`: flat reference prose,
one fact a sentence, no history, no justification, never invent a detail.

Four kinds of comment earn a place: the contract on a callable routine, a trap that will cost an
hour, a checklist of what else to change, and a signpost in a long routine.

## Code

- UXCBASIC code: long, descriptive names, one statement a line. Crunching is the user's pass.
- ROM space and run time count. When touching code, propose shorter or faster forms with the
  bytes and cycles saved.
- Report only real problems. Skip cosmetic nits such as a trailing space.

## X16 facts

- `$0372` holds the stock KERNAL's charset number in bits 0 to 5, and bit 6 is set in ISO mode.
  It reads 2 at boot. No KERNAL call returns it. UXDOS16 does not use it. Only UXCBASIC's stock
  table does: `S_INIT` keeps it in `ZP_MODE`, and `S_EXIT` restores the charset from it.

## Reply style

The user runs `/caveman ultra`, so replies are terse. Code, comments, docs and memory are normal
prose.
