# 6502DOS: architecture review

Written 2026-11-10 against the working tree at `bc67dfa` plus the uncommitted sprite editor
work. Every number comes from `build/6502DOS.MAP` of 2026-11-09, `git`, the sources, or a
compile named in the text. The last section lists what is not verified.

## Overview

The design in `docs/PLAN.md` holds: handles, a system file table, a driver chain, a PSP, `exec`
with exit codes, a RAM gate so the kernel spans ROM banks, and everything above the kernel in
UXCBASIC. The weaknesses are where that design meets its limits now:

- ROM, kernel zero page and the call table are full in the banks that take new work, while bank 5
  is two thirds empty.
- The compiler emits about twice the code a hand-written 6502 routine takes, which is the source
  of every "took N bytes against an estimate of M" entry in `HANDOFF.md`.
- The UXCBASIC layer carries the same editor core, line editor, argument parser, theme reader and
  help reader in several copies.
- The test suite is not tracked and runs no test of the kernel's file API by default.
- `docs/HANDOFF.md` is a log, and its history is most of the repository.

## ROM and RAM space

From the link map. Free bytes are counted below the IRQ entry at `$FFA0`.

| Resource | Used | Free | Note |
|---|---|---|---|
| ROM bank 0 | 12,082 | 4206 | `CODE` 8985, `RODATA` 3052, `GATE` 45; ends `$EF31` |
| ROM bank 1 | 15,525 | 763 | `B1CODE` ends `$FCA4` |
| ROM bank 5 | 6600 | 9688 | `db` 4342, `fp` 2258 |
| `KERNELZP` `$80-$FF` | 128 | 0 | |
| `KERNELRAM` `$0600-$06F7` | 180 | 68 | |
| `REGRAM` `$0400-$05FF` | 486 | 26 | `hostfs.inc` takes 123 |
| `FATBSS` | 1537 | 255 | |
| Call entries `$0340-$03FF` | 64 | 0 | call 63 `con_keys` is the last |
| XBASE, banks 6 to 8 | | 573 | `HANDOFF.md` line 63 |

`HANDOFF.md` reports 4972 free in bank 0 and 2,810 in bank 1. Both are stale.

Bank 0 holds 3838 bytes that do not need bank 0: `font.o` 2048 (`RODATA`, streamed to VRAM by
`con_init`), `monitor.o` 1117 (imports only `to_upper`) and `reg.o` 676 (calls `api_open`,
`api_read` and `api_write` by direct `JSR`). Bank 1 takes every disk feature: `attrib`,
`filetime`, a second volume, FAT16, and `hostfs.inc`.

The kernel zero page by module: `fp` 23, `kernel` 22, `monitor` 19, `console` 17, `exec` 14,
`fat32glue` 11, `strings` 6, `boot` 4, `db` 4, `gate` 4, `reg` 2, `sdcard` 2. The `fp`,
`monitor`, `exec` copy and `strings` GC bytes are call-scoped and never live at once.

The call table is full. Calls 57 `db`, 58 `fp`, 61 `vera` and 62 `gfx` take a function number in
Y, so a second dispatch level exists already, one shape per call. No written plan covers a full
bank 0 or a 65th call.

Changes:

- Move `gfx.s` and `vera.s` (2032 bytes) to bank 5 with a `jsrfar5`, about 60 bytes: 2 KB back
  in bank 1.
- Stream the font from bank 5 (about 20 bytes in `con_init`), and make the monitor and `reg.s`
  call through gate entries so they can leave bank 0: about 8 KB free in bank 0.
- Overlay the call-scoped zero page of `fp`, the monitor, `exec` and `strings`: 25 to 30 bytes.
- Group the single calls behind Y dispatch as `vera` does: `con` (13 calls), `clock` (4), `str`
  (4), `reg` (2), `abs` (2). This frees 20 slots, is one rebuild, and breaks every old binary, so it
  belongs in one beta with a version bump.

## The compiler

pyuxc is a stack machine over template records with no register use. Measured with
`--keep-vars` on five 3-line programs, the cost of one statement against the hand-written form:

| Statement | pyuxc | By hand |
|---|---|---|
| `A = B + C`, UBYTE | 20 bytes | 10 |
| `B = B + 1`, UBYTE | 9 | 3 (`INC B`) |
| `W = W + V`, WORD | 35 | 19 |

The causes, by file:

- A binary operator spills its left side to the expression stack at `$30` through `T_PUSH` or
  `T_PUSHB` (`tpl/T-CORE.ASM`). Fast paths exist only for a constant or address on the right of
  `+` and `-` (`ex_fast_add`, `uxc_expr.py`) and a constant or variable in a compare
  (`ex_fast_cmp`).
- Every operand is absolute. `DIM ... AT ZP` is in the plan and not built; `$50-$7F` gives 48
  bytes.
- The three peepholes, load drop (`ex_held`), `CMP #0` drop (`ex_z_set`) and tail call
  (`em_rts`), look back one record.
- `br_relax` and `br_around` in `uxc_branch.py` are off for any program with `#REGION_SLOT`, so
  XT (47,118 bytes) and EDIT get none of the short-branch saving that took 2376 bytes off XBASE.
- `rb_choose` in `uxc_rombank.py` partitions ROM banks in source order from the named SUB
  backwards. XBASE's 206 veneers cost 1442 bytes (`HANDOFF.md` line 72). Each later bank holds its
  own copy of the runtime records it names, up to 2136 bytes (`HANDOFF.md` line 72, item 9).
- `T_FAR` has three hard-coded entries (`K_FAR_ENTRY`, `uxc_defs.py`), which is the three-bank
  limit.
- The self-host rules (fixed tables, byte-at-a-time buffers, no recursion) hold in the ported
  modules and not in `uxc_rombank.py`, `uxc_branch.py` or `uxc_ramreg.py`. Any edit under
  `pyuxc/` marks every program stale: a full rebuild takes 18.7 to 19.7 s.
- The first error stops the compile. There are no warnings, no listing and no map.

Changes:

- A variable-on-the-right fast path for `+`, `-`, `AND`, `OR` and `XOR`: about 10 templates and
  30 lines in `ex_fast_add`. Saves about 8 bytes a byte operation and 10 a word operation.
- An `INC`/`DEC` store peephole for `v = v + 1` and `v = v - 1`: 6 bytes a site.
- Branch relaxation under `#REGION_SLOT`: shift `g.rg_pins` as fixups are shifted.
- A call-graph partition in `rb_choose`, and one runtime copy in low RAM.
- A far call that reads its target after the `JSR` (`jsr FAR; .word addr; .byte bank`), as
  `R_ARG` does in `tpl/T-STRING.ASM`. It ends the three-bank limit and the per-entry code.
- State the self-host goal as small programs only, and use Python lists and dicts in the
  compiler's own data.
- Warnings for unused variables (`dv_strip` already finds them), a map file, and a set of golden
  PRGs so a code generation regression is caught without the emulator.

## The programs and the library

- `src/dos/TED.UXB` lines 117 to 548 and `src/dos/EDIT.UXB` lines 163 to 600 are one 432-line
  editor core; 30 lines differ.
- The prompt line editor, with its history ring and Tab completion, is in `src/bas/CMDSHELL.UXI`
  lines 1785 to 1960 and again in `src/bank6/DB_LINE.UXI` lines 44 to 198, with the same SUB
  names. The second copy is in the ROM that has 573 bytes left.
- XBASE redoes GUI Forms: `PICK_LINES`, `SPAN` and `BOX` in `DB_SCREEN.UXI` lines 239 to 287
  match `GUI.UXI` lines 318 to 385, and `EDIT_GET`, `PICK_BAR`, `PICK_ITEM` and `POPUP_LIST` redo
  `INPUT2`, `PICKMENU` and `DROP_LIST`. A ROM program cannot use regions, so it cannot include
  `GUI.UXI`.
- `HELPBAS.UXB` and `HELPXBASE.UXB` are 173 lines each and 40 lines apart. The `.IDX` reader is in
  HELP, HELPBAS, HELPXBASE and TED.
- The `.GTH` theme file is read in TED, VIEW, CONCOLOR, `XTSET.UXI` and `GUI.THEME_FILE`.
- The argument block, `HELP_SWITCH`, the loop over `SLOT_P1` to `SLOT_P9`, the switch test and
  `FAIL`, is in HEAD, TAIL, GREP, XCOPY, DELTREE, SUBST, TREE, CHKDSK, `DIRSTACK.UXI`, ZIP and
  UNZIP. `SUB FAIL` is defined in 12 files. Exit codes differ by program: 1 and 2 in most, an
  `ENUM OUTCOME` of 0, 1, 2 and 4 in DELTREE, SUBST and XCOPY.
- Six yes/no prompts exist: `GUI.YESNO`, XT's rows 28 and 29, XBASE's `@ SAY ... GET`, TED's
  `ASK_QUIT`, DELTREE's `CONFIRM` and the shell's `ASK_YES`.
- Two argument channels: the slots `P1$` to `P9$` and the raw tail at `$0780`. XBASE sets slot 0
  before each `EXEC` to imitate the shell's split, with three `Trap` comments.
- Two settings stores: `INI.UXI` costs a RAM bank as a region in EDIT (slot 5) and XT (slot 9);
  `reg_get` and `reg_set` cost one `SYS`. EDIT's `THEME` key picks a built-in theme, never a
  `.GTH`.
- `$03CA` is hard-coded in `DOS.UXI`, `CONS.UXI` and `GUI.UXI`, and `$03FD` in `KEYS.UXI`, each
  with a checklist comment.
- `UPDATE_FOUND` in `DOS.UXI` copies the found name in a BASIC `FOR` loop on every `FINDNEXT`.
  TREE, XCOPY, DELTREE, CHKDSK, XT and `PICKFILE` pay it per directory entry.
- The language has no string arrays, so `KEY_PROCS`, `DB_LINE`'s records, XT's names,
  `PICKFILE`'s records and HDIR's table are hand-built fixed records. 104 `STRING * 255`
  declarations take 257 bytes each.

Changes:

- `ARGS.UXI`: `NEXT()` over the slots, `SWITCH(letters$)`, `FAIL(code, text$)`, one
  `ENUM EXIT_CODE` (0 done, 1 failed, 2 cancelled, 4 bad parameter), the three messages as
  `CONST`s and `HELP_SWITCH` inside. About 150 to 300 bytes off each of about 25 programs.
- `exec` fills the slots from the tail, so every parent gets the shell's split.
- `TEXTBUF.UXI` from TED's core, under TED and EDIT, later under `GUI.MEMO`.
- One line editor: history and a completion callback in the kernel's `con_edit`, or a
  `LINEEDIT.UXI` that ROMSHELL and XBASE include.
- One `HELP.COM` with the `.HLP` path as a switch.
- `GUI.THEME_FILE` plus a `THEME_PATH()` as the only `.GTH` reader.
- `API.UXI`, emitted by `tools/genapi.py`, with the entry addresses as `CONST`s.
- Drop `INI.UXI` for the REG store with dotted keys such as `EDIT.TABS`: frees a bank in EDIT and
  in XT.
- Split `GUI.UXI` by region: core (theme, boxes, `INPUT2`, hot keys, a status-row prompt), forms,
  lists with `PICKFILE`, memo. The split cuts names and region loaders, not bytes; the 9 KB that
  `LISTBOX` costs comes from the dialog path running the form engine, and a dialog that bypasses
  `SHOW` cuts it.
- XBASE: lift the three-bank limit and take bank 9, or build `XBASE.COM` for RAM with regions,
  `GUI.UXI` and the shared line editor.

## The kernel

- `keep`, call 28, marks the program's banks `BANK_KEPT`, then `exec_unwind` copies the parent
  back over `$0700-$9EFF`. The kept code survives only in RAM banks. No IRQ hook exists. The one
  user is `tests/com/KEEPKID.S`.
- `attrib`, `filetime`, `getvect` and `setvect` are `api_bad`.
- `sd_request` in `sdcard.s` issues one command a sector and fails on the first error. `sd_init`
  runs once at boot. A card inserted later is not seen. `exit_how` 2, disk error, is never set.
- The gate keeps `gate_vector`, `gate_a` and `gate_x` in zero page and dispatches by
  `jmp (gate_vector)`; `saved_bank` and the I/O pointers are single statics. An API call from a
  future IRQ hook during a call in flight corrupts it.
- `parent_copy` in `exec.s` moves 16 cycles a byte. A full save is 153 pages, about 79 ms at
  8 MHz each way and 5 banks a level. A RAM program that runs a tiny child saves its whole image.
- `hostfs.inc` is a second implementation of every disk call, selected once by `host_probe`,
  compiled into the shipping ROM, and masking interrupts from `host_begin` to `host_finish`.
- The FAT32 library keeps one sector buffer for 16 contexts and reloads it on every context switch.
  `allocate_cluster` writes both FATs and the FSInfo sector per cluster. The directory entry of a
  written file is updated at close only. Mount takes partition types `$0B` and `$0C`; media change
  is undetected; `fat32glue.s` hard-codes unit 0.
- Each `con_status`, `con_getkey` and `con_keys` poll is a full I2C transaction to the SMC.
- A program can write `$01`, the gate page, the PSP and the `save_bank` bytes. All exec levels
  share one 256-byte stack.

Changes:

- A two-retry loop in `sd_request`, about 15 bytes, and a re-init plus unmount on
  `ERR_NOT_READY`, about 20 bytes.
- Set a child's `PSP_TOP` from the file size known at `exec.s` line 58: about 30 bytes, and most
  shell-to-cmdlet saves shrink to a few pages.
- Make the gate stack-only before any IRQ hook: about 15 bytes and 10 cycles.
- Either rename `keep` to what it does, hand banks to the parent, or defer it until `setvect` runs
  the hook with the kept bank selected.
- Build `hostfs.inc` only into `TEST.ROM` under a `-D` flag, with its `LISTEN1`, `READST` and
  `SIGNATURE1` segments: about 2 KB back in the shipping bank 1.
- A one-sector FAT cache before any per-context buffer work.

## The tests

- `.gitignore` ignores `tests/*.OUT` and `tests/*.IN`. 0 of the 164 goldens are tracked; on disk
  they are 6322 lines. `tools/tests.py` enumerates `tests/*.OUT`, so a fresh clone runs zero tests.
  The same holds for UXCBASIC's 213 goldens and MSBASIC's 37.
- `STOPPED_TESTS` in `tools/tests.py` holds 52 names, so 112 tests run by default. The stopped set
  is the kernel's file, directory, handle, seek and dup API, the clock, the console, the registers,
  `KEEP`, `BANKCALL`, and every EDIT, TED, VIEW, MORE, HEAD, TAIL, GREP, XCOPY, CHKDSK, FONT and
  THEMED test. The default run covers DB, GUI, the shell and help.
- No test names `subst`, `con_keys`, `progpath` or `exec_rest`. XT, SPRITEEDIT, SPRDEMO and
  GUIDEMO have none.
- The harness reads the `$FFD2` echo. A program that writes VRAM through `VERA.PRINTAT` shows
  nothing; only a `check(image)` hook sees its files.
- The 5 s limit is wall-clock under `-warp`, so host load fails tests.
- Every shell test but `SHBOOT` runs `CMDSHELL.COM` on `TEST.ROM`, the RAM build, not the ROM
  banks 3 and 4 that ship.
- The last logged full runs: 104 tests with 5 failed on 2026-10-25, 83 tests with 1 failed on
  2026-10-29. No unit test covers the asm, `mksd.py` or `fatcheck.py`; nothing calls
  `fatcheck.py`.

Changes:

- Track the goldens. They are text and small.
- Run the stopped kernel API tests first, then the utilities, in batches, and run the full suite
  before each beta.
- A screen dump to a file at exit under a REG key, about 60 bytes in `VERA.UXI`, so the VRAM
  programs get goldens through the `.IN` and `.PY` pattern that exists.
- Boot `6502DOS.ROM` for the `SH*` tests, or keep the RAM shell as a harness and say so.

## The build and the repository

- Tracked build outputs: `card/sys/*.COM` and the themes and xbase COMs, the three `.IDX` files,
  `card/TEST/*.COM`, `release/*.zip` (4.4 MB), `UXCBASIC/tpl/*.BIN`. `tools/uxb.py` decides
  staleness by mtime, so a COM committed stale is never rebuilt, and nothing compares committed COMs
  with their sources.
- `x16emu` at `C:\8bitProgramming` is hard-coded in `tools/build.py`, `tools/tests.py`,
  `UXCBASIC/tests.py`, `RUNCARD.BAT` and `RUNHOST.BAT`. The Python path is hard-coded in
  `BUILD.BAT`, `MKGUI.BAT`, `RUNUXCTESTS.BAT`, `MSBASIC/Makefile`, `tools/gui/buildgui.py`,
  `CLAUDE.md` and `MSBASIC/CLAUDE.md`. There is no CI.
- MSBASIC is built by `tools/build.py` and by its own `Makefile` with flags kept equal by hand.
  `MKTPL.PY` still builds the stock template table, which nothing uses, as the id reference.
- `.git` is 85 MB: 2667 loose objects of 73.5 MiB and one pack of 5.5 MiB. `docs/HANDOFF.md` is
  793,734 bytes, 8270 lines, and 248 of 343 commits touch it; its versions are about 106 MB
  before delta compression.
- `build/6502DOS.MAP` is written and read by nothing. `HANDOFF.md` carries 31 hand-written
  free-space reports.
- One tag exists, `v0.1.0-beta1`. `main` is one commit ahead of `origin/main`.
- `attic/` holds 1356 files; `UXCBASIC/docs/x16` holds 26 files of the X16 reference, tracked,
  while `MSBASIC/docs/x16` is ignored by rule. `docs/image.png` is referenced nowhere.

Changes:

- Untrack the build outputs and the zips; the build makes them, and GitHub Releases hold zips.
- `EMU` and `PYTHON` as environment variables with the current paths as defaults.
- A script over the map and the bank listings that prints free bytes a bank and a segment, run by
  `build.py`, with a size-regression line against the last build.
- `git gc`. Tag each beta.
- One build path for MSBASIC.

## The docs

- `HANDOFF.md` is a step log: 4900 of its lines are dated entries from line 3380 on, with 78 build
  times. `doc-style.md` says it holds the current state in under about 100 lines.
- `PLAN.md` is "Draft 3, 2026-10-14". Section 13 lists A: and B: as open; `subst` assigns them.
- `README.md` names `6502DOS-0.1.3-beta3-win.zip`, which does not exist, and says `API.md` is
  generated by `tools/api.py`; `tools/genapi.py` generates it.
- `VERSION_LABEL` is typed again by hand in `src/bas/CMDSHELL.UXI` line 1696.
- No manual exists outside the card's `HELP.HLP` (80 topics), `HELPBAS.HLP` (97),
  `HELPXBASE.HLP` (97), `XT.HLP` and `TED.HLP`.
- Four languages ship, each with its own parser, help file and line editor: the shell's BASIC,
  UXCBASIC, MSBASIC and XBASE. UXCBASIC compiles on the PC only.

Changes:

- A `HANDOFF.md` of one or two pages, a `CHANGELOG.md` for the dated entries, and a note a
  feature under `docs/` for XBASE, ZIP, EDIT, XT and SUBST.
- `genapi.py` writes the version label into the shell's source, or the shell reads it from
  `version`.
- Fix the README's zip name and generator name, and PLAN section 13.

## Changes, in order of payoff over cost

1. Move `gfx.s` and `vera.s` to bank 5; stream the font from bank 5; overlay the call-scoped zero
   page.
2. The variable-on-the-right fast path and the `INC`/`DEC` peephole in pyuxc.
3. Branch relaxation under `#REGION_SLOT`.
4. Track the goldens; a map-reading free-space script; `git gc`; `EMU` as a variable.
5. `ARGS.UXI` with one exit-code `ENUM`; `exec` fills the slots.
6. `TEXTBUF.UXI`, one line editor, one `HELP.COM`, one theme reader, `API.UXI`.
7. The call-graph bank partition and one runtime copy.
8. The inline-operand far call; then XBASE in bank 9 or in RAM with regions.
9. Group the API calls behind Y dispatch, in one beta.
10. Retries in `sd_request`; `PSP_TOP` from the child's size; a stack-only gate; a decision on
    `keep`.
11. Drop `INI.UXI` for REG.
12. Cut `HANDOFF.md` to a state note with a changelog; untrack the build outputs.
13. State the self-host goal as small programs only and lift the data rules in pyuxc.

## Not verified

- The per-site savings of the compiler changes are estimates from the templates. The three
  statement costs in the table are measured; the savings from the new fast paths are not.
- Whether the 112 default tests pass today. No full run is logged after 2026-10-29.
- `hostfs.inc`'s share of `fat32dos.o`: 2 to 2.5 KB is an estimate; the include has no exported
  labels.
- That each zero-page byte named as call-scoped is never live across a call.
- The post-`gc` size of `.git`.
- The cycle cost of one SMC poll in `con_status`.
