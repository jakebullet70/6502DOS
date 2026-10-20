# UXDOS16 — design

Draft 3, 2026-10-14. `docs/HANDOFF.md` gives what is built. Section 13 lists what is still open.

## 1. Goal

- UXDOS16 is a replacement ROM operating system for the Commander X16, on the 65C02.
- MS-DOS 2.0 is the model for its ideas: file handles, a device driver chain, a per-program
  header block, a command shell, `CONFIG.SYS`, a start-up script and scripts. The shell's
  language is BASIC (section 8).
- One user, and one program runs at a time. A program can run another and get its exit code.
- The base system is asm, assembled with ca65.
- Everything above the base is written in UXCBASIC.
- No code comes from MS-DOS, FreeDOS. MS-DOS 2.0 is x86 code, so only its design
  carries over.
- UXDOS16 is under the MIT licence, in `LICENSE`. Code ported from x16-rom keeps its BSD-2
  licence (section 9).

Where to read MS-DOS 2.0: `github.com/microsoft/MS-DOS`, folder `v2.0`, MIT licence.

## 2. Layers

The layers follow MS-DOS's split into `IO.SYS`, `MSDOS.SYS` and `COMMAND.COM`.

| Layer | Part (MS-DOS part) | Language | Contents |
|---|---|---|---|
| 0 | `IO.SYS` | asm, about 2–4 KB | Reset, vectors, IRQ and NMI entry, the syscall gate, `jsrfar`, bank switching, the built-in drivers' inner loops: SPI and I2C bits, the 512-byte sector copy, the VERA glyph write |
| 1 | `UXDOS.SYS` (`MSDOS.SYS`) | asm first, then UXCBASIC | The system file table, handles, path parsing, drives and current directories, FAT32, the bank allocator, the driver chain, `exec` and `exit` |
| 2 | `SYSINIT`, the shell and the utilities (`COMMAND.COM`) | UXCBASIC from the start | `SYSINIT`, `CMDSHELL`, scripts, the commandlets, `DEBUG` |

- Layer 1 is written in asm until UXCBASIC has the features in section 12. Each part then moves
  to UXCBASIC one at a time, and its tests stay the same.
- `SYSINIT.COM` runs at boot. It reads `CONFIG.SYS`, loads the `DEVICE=` drivers, sets `FILES=`,
  and runs the `SHELL=` program.
- `DEBUG.COM` is the full monitor. The asm monitor in ROM is the bring-up tool.

### What each part is written in

| Part | Language | Needs |
|---|---|---|
| `SYSINIT`, `CMDSHELL`, scripts, the commandlets, `DEBUG` | UXCBASIC | nothing new |
| Path splitting, drive letters, 8.3 names, wildcard matching | UXCBASIC `.UXI` | nothing new |
| The bank allocator: the owner and next-bank tables | UXCBASIC `.UXI` | nothing new: `POKE 0, bank`, then `ContentsAt($A000 + n)` |
| Walking the driver chain and calling a vector | UXCBASIC `.UXI` | nothing new: `SYS P%` takes a variable address |
| FAT32: cluster maths, file sizes, `seek` | UXCBASIC | `LONG`, section 12 item 2 |
| The system file table in bank 0, and the drive table | UXCBASIC | records, item 1, and `DIM ... AT ... BANK`, item 3 |
| The API entries in the jump table | UXCBASIC | `SUB ... REGS`, item 5 |
| Layer 1 in ROM | UXCBASIC | ROM-able output, item 6 |
| Loadable drivers that the kernel calls | UXCBASIC | items 4 and 5 |
| The `exec` and `exit` swap | UXCBASIC | item 6. The code must lie outside `$0801–$9EFF`, the range it swaps. |
| Reset, the vectors, IRQ and NMI entry, the gate, `jsrfar`, bank switching | asm | |
| The SPI and I2C bits, the 512-byte sector copy, the VERA glyph write | asm | |
| The copy loop of `xms_move` | asm | |
| Code that runs inside an IRQ: the keyboard scan, the tick | asm | |

- Code that runs inside an IRQ stays asm. A UXCBASIC `SUB` is not re-entrant.
- Compiled UXCBASIC is larger than asm. Layer 1 in UXCBASIC spans more than one 16 KB ROM bank,
  and its calls between banks go through `jsrfar`.

### `DOS.UXI`

The UXCBASIC library is the folder `lib/`. Each file holds one namespace of the same name. A
`BIND` renames a built-in into its namespace.

| File | Namespace | Holds |
|---|---|---|
| `lib/DOS.UXI` | `DOS` | one `SUB` or `FUNCTION` for each API call in section 4; the whole-file routines `EXISTS`, `SIZE` and `COPY` |
| `lib/HEAP.UXI` | `HEAP` | the string heap calls and the system descriptors; include it after `DOS.UXI` |
| `lib/KEYS.UXI` | `KEYS` | the characters and scan codes the console gives for keys, the modifier bits of `con_status`, and a `BIND` of `GETKEY`: `KEYS.SCAN_UP`, `KEYS.MOD_CTRL` |
| `lib/CONS.UXI` | `CONS` | the escape sequences the console obeys, as string constants with plain names (`CONS.CSI$`, `CONS.REVERSE$`, `CONS.RED$`, `CONS.ON_WHITE$`, `CONS.CLEAR_EOL$`); `BIND`s of `PRINT`, `INPUT`, `LINPUT`, `POS`, and `NEWLINE` for `PRINT`; `LOCATE`, `PRINT_AT`, `PRINT_BOOL`, `SCREEN_ROWS`, `SCREEN_COLS` |
| `lib/STR.UXI` | `STR` | a `BIND` of each string built-in; `INSTR_REV` |

- Every UXCBASIC program in UXDOS16 calls the API through `DOS.UXI`. Each call goes to the
  UXDOS16 jump table through `SYS`.
- `tools/genapi.py` writes the `API_` constants of `DOS.UXI`, one for each call's entry,
  between two marker lines. The rest of the file is written by hand.
- `DOS.STOP_KEY(mode)` sets the mode of the STOP key, Ctrl+C, with call 47. The modes are the
  members of `ENUM STOP`: `DOS.STOP.OFF` 0, `DOS.STOP.ENDS` 1, `DOS.STOP.CATCH` 2.
  `DOS.STOP_PRESSED()` gives 1 when Ctrl+C was pressed in `CATCH`, and clears the flag.
- A constant or a `BIND` adds no bytes to a program. pyuxc leaves out each `SUB` and `FUNCTION`
  that the program does not call.
- A program holds at most 64 `BIND`s (`K_ALIASES` in pyuxc). `CONS.UXI` takes 5, `KEYS.UXI` 1
  and `STR.UXI` 11.

## 3. Memory map

`src/asm/mem.inc` defines these addresses for asm.

| Range | Use |
|---|---|
| `$00` | RAM bank select (hardware) |
| `$01` | ROM bank select (hardware) |
| `$02–$21` | `r0–r15`, the API registers, laid out as in the stock KERNAL |
| `$22–$7F` | the program. The UXCBASIC runtime uses `$22–$4F`, and `$50–$7F` is free |
| `$80–$FF` | the kernel |
| `$0100–$01FF` | 6502 stack |
| `$0200–$02FF` | the monitor's input line at `$0200`, its output line at `$0280` |
| `$0300–$030B` | free |
| `$030C–$030F` | the A, X, Y and P bytes of UXCBASIC's `SYS` |
| `$0310–$033F` | the gate code |
| `$0340–$03FF` | the call entries, 3 bytes each: room for 64 calls |
| `$0400–$05FF` | free |
| `$0600–$06F7` | kernel variables: the drive table, and the state of the console, the SD driver, `exec` and the string heaps |
| `$06F8–$06FF` | the request of a block driver's input command (section 6) |
| `$0700–$07FF` | the PSP of the running program (section 7) |
| `$0801–$9EFF` | the program |
| `$9F00–$9FFF` | I/O: VIAs, VERA, YM2151 |
| `$A000–$BFFF` bank 0 | kernel tables: the system file table at `$A000`, the FAT32 library's variables at `$A100–$A7FF`, the keyboard queue at `$A800–$A80A`, the library's sector buffer at `$A900–$AAFF`, `rename`'s new path at `$AB00–$ABFF`; later the bank owner and next-bank tables |
| `$A000–$BFFF` banks 1 to 20 | `exec`'s save banks: 5 for each of 4 levels |
| `$A000–$BFFF` bank 21 | VARBANK, the shared string heap (String heaps, below) |
| `$A000–$BFFF` banks 22 and up | the environment, and banks handed out by the allocator |
| `$C000–$FFFF` ROM bank 0 | kernel core and the vectors. `$FFCF` and `$FFD2` jump to `con_in` and `con_out`, and `$FFF6–$FFF9` hold `MIST` (section 10) |
| `$C000–$FFFF` ROM bank 1 | the FAT32 library, the kernel's file calls on it, and its glue to the SD driver |
| `$C000–$FFFF` ROM banks 2 and up | not in the image yet |

VRAM:

| Range | Use |
|---|---|
| `$10000–$13FFF` | the text map of layer 1: 64 rows of 128 cells, each a character and a color byte |
| `$1F000–$1F7FF` | the CP437 font |
| `$1FA00–$1FBFF` | the palette |

- Trap: code in ROM that writes `$01` fetches its next instruction from the new bank. Every
  change of ROM bank goes through the gate at `$0310`.
- `FARCALL target` (`src/asm/far.inc`) calls a routine in another ROM bank: 6 bytes a call,
  about 140 cycles. A, X, Y and carry pass both ways. Each bank has its own `jsrfar`, which
  ends in the gate's tail: `jsrfar` in bank 0, `jsrfar1` in bank 1.
- Trap: an interrupt's vector pull selects ROM bank 0, but `$01` reads the interrupted bank
  until code writes it. Each bank holds the same IRQ entry and exit at `$FFA0`: the entry
  saves A and the bank and selects bank 0, the exit selects the saved bank and returns. A BRK
  drops the bank and goes to the monitor in bank 0.
- Trap: UXCBASIC's `SYS` loads A, X, Y and P from `$030C–$030F` and stores them back. The gate
  and the vectors must not use those four bytes.
- Trap: `$01` reads back as noise until code writes it. Reset writes 0 to it before the gate
  saves it.
- The system file table has 8 entries of 32 bytes. An entry holds the number of handles that
  refer to it, the access mode and the driver's address. A file's entry also holds its context
  in the FAT32 library, its position and its size. The library has 8 contexts, one for each
  entry.

### Banked RAM

A program gets banked RAM in 8 KB banks that it selects itself, or as extended memory blocks
that it reaches through a copy call. The blocks follow XMS, the interface of MS-DOS's
`HIMEM.SYS`.

- A block is a chain of banks under one handle. `xms_alloc` takes a size in banks in A and
  gives the handle in A. `xms_free` gives back the block whose handle is in A.
- `bank_alloc` is `xms_alloc` of one bank. Its handle is the bank number, and the program
  selects it by writing `$00`.
- The handle is the number of the block's first bank. Handle 0 means main RAM, where an offset
  is an address. Bank 0 is the kernel's, so no block has handle 0.
- Bank 0 holds two tables of 256 bytes: the owner of each bank, and the next bank in its chain,
  0 for the last. Bit 7 of the owner byte marks the first bank of a block. The banks of a block
  need not be contiguous, so any free bank serves.
- An offset into a block is 21 bits: 256 banks of 8 KB is 2 MB. The bank of offset `n` is
  `n >> 13` steps along the chain from the handle, at address `$A000 + (n AND $1FFF)`.
  `xms_move` keeps the bank and step of its last walk and starts the next walk from there when
  it can.
- `xms_move` takes in `r0` the address of a move record in main RAM:

  | Offset | Size | Field |
  |---|---|---|
  | 0 | 4 | the length in bytes |
  | 4 | 1 | the source handle |
  | 5 | 4 | the source offset |
  | 9 | 1 | the destination handle |
  | 10 | 4 | the destination offset |

- `xms_move` copies in runs that end at the end of a bank on either side. Its loop is
  `LDA (src),Y`, `STA (dst),Y`, `INY`, `BNE`: 16 cycles a byte, about 16 ms for 8 KB at 8 MHz.
  A load from a selected bank, `LDA (zp),Y`, takes 5 cycles.
- `xms_move` restores the RAM bank the caller had selected.
- `xms_alloc` with a size of 0 gives the number of free banks in A and allocates nothing.
- Errors: `xms_alloc` with too few free banks gives error 8. A handle that is not the first
  bank of a block, or a length that runs past the end of a block, gives error 9.
- `exit` frees a program's blocks with its other banks. `keep` keeps them.
- Data that fits in one bank is faster in a bank from `bank_alloc`. A block suits data larger
  than 8 KB read in pieces: a whole file, a RAM disk.

### String heaps

A string heap is one RAM bank of strings with garbage collection, in `src/asm/strings.s`. The
calls are `str_alloc`, `str_free`, `str_gc` and `str_heap` (section 4). Heaps hold strings
only; numbers stay at fixed addresses in the program.

- VARBANK, bank 21, is the shared heap: the system's, and every program's at its start. A
  program should take a bank of its own with `str_heap`. VARBANK is the first bank after
  `exec`'s save banks, fixed until `bank_alloc` exists.
- A heap's bank starts with a header:

  | Address | Size | Field |
  |---|---|---|
  | `$A000` | 2 | the bump pointer: the address of the next block |
  | `$A002` | 10 | the floors: a word for each exec depth, 0 to 4, the lowest block GC moves |
  | `$A00C` | 64 | VARBANK only: 32 system descriptors |

  Blocks follow, from `$A04C` in VARBANK. In a program's own bank they start at the address
  `str_heap` gives; the bytes from `$A00C` up to it are the program's.
- A block is the owner, 2 bytes, the length, 1 byte, then the text. The owner is the address of
  the block's descriptor, 0 for a free block.
- A descriptor is 2 bytes holding the address of its block's length byte, so it points at a
  length-prefixed string. It lies in program RAM, from `$0002`, or at `$A000–$BFFF` in the
  heap's own bank. 0 means no string.
- A block is live while its descriptor points back at it. `str_alloc` on a descriptor that
  holds a string makes the old block dead, so a reassign needs no `str_free` first.
- `str_alloc` takes a block at the bump pointer. When the heap is full it runs GC once, then
  gives error 8.
- GC is one pass from the floor of the current exec depth to the bump pointer. Each live block
  slides down over the dead ones, and its descriptor follows. A block with no dead block below
  it does not move. A byte moved costs 18 cycles.
- `exec` sets the child's floor in VARBANK to the bump pointer, so the child's GC never moves
  its parents' blocks. Their descriptors are in the save banks while the child runs.
- `exit` drops the child's blocks in VARBANK whose owner is below `$A000`, then runs GC from the
  child's floor. A block whose descriptor is a system descriptor stays: that is how a program
  leaves a string for the system.
- `keep` treats VARBANK as `exit` does: the parent's copy-back overwrites the TSR's descriptors.
  A TSR's strings go in its own bank, descriptors included. `keep` is not written.
- `PSP_HEAP`, byte `$01` of the PSP, holds the bank of the running program's heap. Boot and
  `exec` set it to VARBANK.
- VARBANK's system descriptors 0 to 8 are the slots `P1$` to `P9$`, 9 is `PATH$`, 10 is
  `PROMPT$`, 11 is `EDITOR$`, 12 holds the shell's `BIND` aliases, 13 is `TEMP$`, and 14 to 21
  hold the shell's command history (section 8). Their addresses are constants in
  `lib/HEAP.UXI`: descriptor n is at `$A00C + 2n`.
- `HEAP.UXI`'s `SYS_STRINGS_GET(slot)` reads system descriptor `slot`, 0 to 31, and
  `SYS_STRINGS_SET(slot, text)` sets it. Each sets `PSP_HEAP` to VARBANK for the call and
  restores it.
- Trap: `STR_GET` and `STR_SET` use the bank in `PSP_HEAP`. After a `STR_HEAP` to another bank
  they miss the system descriptors; `SYS_STRINGS_GET` and `SYS_STRINGS_SET` do not.
- Trap: GC moves strings, and a `str_alloc` may run GC. A caller that holds a heap address
  across `str_alloc` or `str_gc` reads the descriptor again after the call.
- Trap: the calls select the heap's bank and restore the caller's. A program reading a string
  selects the bank `str_alloc` gave in A.
- Trap: x16emu fills banked RAM with random bytes at power-on. A heap's free space holds
  noise.
- Not written: freeing a program's own heap bank at `exit`, which needs `bank_alloc`.

## 4. The API

- One source file, `tools/api.py`, lists every call: its number, registers in, registers out,
  errors, and the MS-DOS 2.0 function it matches. `tools/genapi.py` writes from it
  `build/gen/api.inc` (the call and error numbers), `build/gen/api.s` (the routine table and the
  error messages) and `docs/API.md`, the reference for each call's registers.
- The call entries are in RAM from `$0340`, 3 bytes each: a program makes call `n` with
  `JSR $0340 + 3n`. Every entry is `JSR` to the gate. The gate finds `n` from its return address,
  selects ROM bank 0, reads the call's routine and ROM bank from `api_table`, calls the routine
  and restores the caller's ROM bank. A program never writes `$01`.
- MS-DOS has one entry, `INT 21h`, with the function number in `AH`. UXDOS16 has one jump table
  entry for each call instead.
- Arguments go in A, X, Y and `r0–r15`. A call keeps `r0–r15`, except its outputs.
- On error the call returns with carry set and the error number in A. On success carry is clear.
  This is MS-DOS 2.0's convention for its handle calls.
- A string argument is a pointer in `r0` to a length-prefixed string.

Calls, with the MS-DOS 2.0 function each matches:

| Call | MS-DOS | Does |
|---|---|---|
| `create` | 3Ch | creates or empties a file and gives a handle |
| `open`, `close` | 3Dh, 3Eh | open a path and give a handle; close a handle |
| `read`, `write` | 3Fh, 40h | move bytes between a handle and memory |
| `seek` | 42h | moves the position of a handle |
| `delete`, `rename` | 41h, 56h | change a directory entry |
| `attrib`, `filetime` | 43h, 57h | get or set a file's attributes and time |
| `ioctl` | 44h | a device request, and whether a handle is a device or a file |
| `dup`, `dup2` | 45h, 46h | copy a handle, for redirection |
| `findfirst`, `findnext` | 4Eh, 4Fh | list the names that match a wildcard pattern |
| `mkdir`, `rmdir`, `chdir`, `getcwd` | 39h, 3Ah, 3Bh, 47h | directories |
| `getdrive`, `setdrive`, `diskfree` | 19h, 0Eh, 36h | the current drive and its free space |
| `con_line` | 0Ah | reads a line from the console with editing |
| `con_status` | 0Bh | whether a key is waiting |
| `con_out`, `con_in` | 02h, 08h | write a character; wait for a key, with no echo |
| `con_cursor` | none; BIOS 10h, 02h and 03h | get or set the cursor's row and column; a get also gives the screen's rows and columns |
| `con_colour` | none | get or set the console color (section 6) |
| `con_break` | 33h | get or set the mode of the STOP key, and read the break flag (section 7) |
| `exec` | 4Bh | runs a program |
| `exit`, `exitcode` | 4Ch, 4Dh | ends a program with a code; gives the last child's code |
| `keep` | 31h | ends a program and keeps its banks: a TSR |
| `bank_alloc`, `bank_free` | 48h, 49h | hand out 8 KB RAM banks |
| `xms_alloc`, `xms_free`, `xms_move` | none; XMS 09h, 0Ah, 0Bh | extended memory blocks (section 3) |
| `str_alloc`, `str_free`, `str_gc`, `str_heap` | none | string heaps with garbage collection (section 3) |
| `getvect`, `setvect` | 35h, 25h | the IRQ hook, the break handler, the disk error handler |
| `getdate`, `setdate`, `gettime`, `settime` | 2Ah–2Dh | the RTC |
| `version` | 30h | the system version |
| `ticks` | none | the VSYNC counter |
| `errmsg` | none | the text of an error number |

Errors use MS-DOS 2.0's numbers:

| Number | Error |
|---|---|
| 1 | invalid function |
| 2 | file not found |
| 3 | path not found |
| 4 | too many open files |
| 5 | access denied |
| 6 | invalid handle |
| 8 | insufficient memory |
| 9 | invalid memory block |
| 11 | invalid format |
| 12 | invalid access code |
| 13 | invalid data |
| 15 | invalid drive |
| 16 | attempt to remove the current directory |
| 17 | not the same device |
| 18 | no more files |

## 5. Files, drives and handles

- A path is a drive letter, a directory path and a name: `C:\GAMES\TREK.COM`.
- Each drive has its own current directory. The kernel keeps the current drive.
- A character device has a name with no drive: `CON`, `NUL`, `CLOCK$`. The name works in any
  directory, as in MS-DOS.
- The kernel takes `\` (`$5C` in CP437) and `/` (`$2F`) as path separators. A path the kernel
  gives back, as from `getcwd`, uses `\`.
- Wildcards `*` and `?` work in `findfirst`, `DIR`, `DEL` and `COPY`, by Windows rules. `*`
  matches any run of characters, dots too, and `?` one character. A pattern that ends in `.`
  or `.*` also matches a name with no dot. `*` matches every name, and `*.` the names with no
  dot.
- A wildcard in a directory part of a path gives error 3. A pattern over 32 characters gives
  error 2.
- A name is up to 32 characters, and a path up to 255, the most its length byte holds. FAT32
  keeps a long name in entries of 13 characters, so 32 characters take 3 entries. The find
  buffer's name field holds 32 characters.
- A name keeps the case it was made with. A look-up takes `A` to `Z` and `a` to `z` as the
  same.
- Every name also has an 8.3 alias, which works wherever the name does. A name the kernel
  makes that fits 8.3 is its own alias, in capitals. Any other gets an alias of hex digits
  and `~`.
- A name over 32 characters, made on another system, shows as its alias in every call.
- Create, mkdir and the new name of rename give error 3 for a name part over 32 characters,
  a blank name, a name of dots only, or a name with `*` or `?`. Delete and the old name of
  rename give error 2 for the last three.
- chdir gives error 3 for a directory whose path would pass 254 characters, so getcwd always
  fits.
- rmdir of a read-only directory gives error 5. rename of a directory into another directory
  gives error 5.
- Each unit of a block driver gets the next drive letter from `C:`. The SD card is `C:`, and
  `C:` is the current drive at boot. There are 4 drive letters, `A:` to `D:`. The FAT32
  library serves one volume, `C:`.
- A path with no drive is on the current drive. A path that starts with a separator starts at
  the root directory, any other at the drive's current directory.
- Each drive's DPB keeps the first cluster of its current directory, 0 for the root. `getcwd`
  finds the names through the `..` entries up to the root, long names included, so no path
  text is kept.
- `.` and `..` are the entries a FAT directory holds. The root directory has none; there both
  name the root, as in Unix, in every call. A search for files finds neither, so `open` of
  `..` in the root gives error 2.
- The system file table in bank 0 holds every open file. Each program's PSP holds its own table
  of 20 handles, each the number of a system file table entry.
- Handles 0, 1 and 2 are stdin, stdout and stderr. A child gets copies of its parent's handles, so
  redirection set up by `CMDSHELL` passes to the program it runs.

## 6. Drivers

Drivers follow MS-DOS 2.0's device drivers.

- Each driver starts with a header:

  | Offset | Size | Field |
  |---|---|---|
  | 0 | 2 | the address of the next driver in the chain, or `$FFFF` for the last |
  | 2 | 1 | attribute bits: `$80` character device, `$40` IOCTL, `$08` clock, `$04` `NUL`, `$02` standard output, `$01` standard input |
  | 3 | 1 | the ABI version, 1 |
  | 4 | 1 | the number of vectors |
  | 5 | 8 | a character device's name, padded with spaces, or a block device's number of units |
  | 13 | 2 each | the vectors |
- MS-DOS calls a driver through a strategy entry and an interrupt entry with a request packet.
  UXDOS16 calls a vector from the table instead, with the arguments in registers.
- Vector slot `n` is MS-DOS 2.0's driver command `n`:

  | Slot | Command |
  |---|---|
  | 0 | init |
  | 1 | media check |
  | 2 | build BPB |
  | 3 | IOCTL input |
  | 4 | input |
  | 5 | non-destructive input |
  | 6 | input status |
  | 7 | input flush |
  | 8 | output |
  | 9 | output with verify |
  | 10 | output status |
  | 11 | output flush |
  | 12 | IOCTL output |

- A vector of 0, or a slot past the number of vectors, means the driver lacks that command.
  The kernel then returns error 1.
- Input and output take the buffer in `r0` and the count in `r1`, and return the bytes moved in
  `r1`.
- `NUL` is the head of the chain. A driver loaded by `DEVICE=` in `CONFIG.SYS` joins the chain
  after it, so it replaces a built-in driver of the same name.
- A block driver only reads and writes 512-byte sectors. The kernel holds the FAT code, as
  MS-DOS does: x16-rom's FAT32 library, in ROM bank 1. Each unit of a block driver gets the
  next drive letter.
- A block driver has `DEV_CHAR` clear and holds its number of units in the name field. Its
  input and output commands take a request at `$06F8`: the unit, the number of sectors, the
  buffer, and the first sector in 4 bytes. They return carry set and A = the error on a fault.
- The library's glue, `src/asm/fat32glue.s`, fills the request for each sector the library
  reads or writes: unit 0, one sector, the library's sector buffer. It calls the SD card
  driver's input and output by `FARCALL`.
- The library mounts `C:` when a call first takes a context: it reads the partition table,
  takes the first partition of type `$0B` or `$0C`, and reads its FAT32 boot sector. The
  volume needs 2 FATs. A drive with no card or no FAT32 gives error 21, drive not ready, at
  that call.
- Media check and build BPB are not used yet, so a card changed after the mount is not seen.
- The library's sector buffer at `$A900` in RAM bank 0 keeps the last sector read, and a read
  of the same sector does not reach the driver.
- `diskfree` takes the free clusters from the FAT32 FS information sector, so it reads no FAT.
- The SD card driver is ported from x16-rom. It reads one unit over VERA's SPI port, at the slow
  speed of 1 byte a loop. Without a card its input gives error 21.
- The console font is CP437, ported from x16-rom.
- The console color is one byte: the background times 16 plus the foreground, each a color of
  VERA's default palette, 0 to 15. It starts at `$05`, green on black. Call 46 `con_colour`
  gives it in A with carry set, and sets it from A with carry clear.
- A character written, a form feed and a scroll take the current color.
- The cursor swaps the two halves of its cell's color byte. A cell whose halves match shows no
  cursor.
- The console is 80 columns by 30 rows on VERA layer 1. It obeys CR, LF, BS, TAB, BEL and FF,
  skips `$0F`, and shows every other byte as its CP437 glyph.
- CR moves to the start of the next line, and an LF right after a CR does nothing. So CR, LF and
  CR LF each end one line.
- The console obeys a part of MS-DOS's `ANSI.SYS`, always: `Esc[r;cH`, `Esc[2J`, `Esc[K` and
  `Esc[...m`. `docs/API.md` lists them under `con_out`.
- `Esc[0m` gives the color `con_colour` last set, so a program's reset keeps the user's `COLOR`.
- The ANSI colors black, red, green, yellow, blue, magenta, cyan and white are palette entries
  0, 2, 5, 9, 6, 4, 3 and 15.
- The screen scrolls in hardware: the map has 64 rows, the vertical scroll register picks the
  top one, and a scroll blanks one row.
- The keyboard reads keycodes from SMC register `$07` over I2C and maps them in a US layout,
  with Shift, Ctrl, Alt and Caps Lock. The cursor blinks while the console waits for a key.
- An extended key gives two characters, as in MS-DOS: 0, then its IBM PC BIOS scan code.
  `docs/API.md` lists the codes under `con_in`.
- Trap: UXCBASIC's `GETKEY()` gives 0 both for no key and for an extended key's first
  character. A `GETKEY()` poll then takes the scan code for a plain character: Up's $48 is `H`.
  A program polls `con_status` until a key waits, then reads `GETKEY()`, and after a 0 reads
  `GETKEY()` again for the scan code.
- The console takes a key from the keyboard queue in RAM bank 0 before it reads the SMC. The
  queue is the stock KERNAL's: 10 characters at `$A800`, the count at `$A80A`.
- Built-in drivers: `CON` (VERA screen and SMC keyboard), `NUL`, `CLOCK$` (RTC), and the SD card
  block driver. `NUL`, `CON` and the SD card driver exist; their headers are in ROM. The chain
  runs `NUL`, `CON`, SD card.
- The RTC is the MCP7940N, I2C device `$6F`. `getdate`, `setdate`, `gettime` and `settime`
  read and write it in `src/asm/clock.s`, with no `CLOCK$` driver. Its registers hold BCD,
  and its year register the year less 2000, so the calls take the years 2000 to 2099.
- Trap: a `DEVICE=` driver joins the chain after `NUL`, so `NUL`'s header must move to RAM first.
- A driver lives in RAM or in a ROM bank. The kernel calls a banked driver through the gate.
- IRQ:
  - A driver with the IRQ bit in its header joins the IRQ chain.
  - While the kernel is busy, an IRQ only sets a flag. It never calls the file API.
  - The tick counter runs on VSYNC.

## 7. Programs

- A `.COM` file loads at `$0801`, as an MS-DOS `.COM` file loads at offset `100h`. A relocatable
  format, like MS-DOS's `.EXE`, comes later with UXCBASIC's relocatable output (UXCBASIC plan §5).
- A `.COM` file starts with its load address, which must be `$0801`: else `exec` gives error 11.
  The rest loads at `$0801`, up to `$9EFF`: a larger file gives error 8.
- A program that starts with a BASIC line `SYS n`, as a UXCBASIC program does, starts at `n`. Any
  other program starts at `$0801`.
- The PSP at `$0700`:

  | Offset | Size | Field |
  |---|---|---|
  | `$00` | 1 | the stack pointer `exec` called the program with; `exit` returns to it |
  | `$01` | 1 | `PSP_HEAP`: the RAM bank of the program's string heap (section 3) |
  | `$02` | 1 | `PSP_TOP`: the last page of the program's RAM that `exec` saves |
  | `$03` | 1 | `PSP_BREAK`: the mode of the STOP key |
  | `$18` | 20 | the handles: each a system file table entry number, or `$FF` when closed |
  | `$80` | 128 | the command tail: a length byte, the text after the program's name, then CR |

  - At boot handles 0, 1 and 2 share the `CON` entry.
  - The tail keeps the space before the first argument, as MS-DOS's does. `exec` cuts it to 126
    characters.
  - Still to add: the disk error handler in force when the program started, and the bank of
    the environment.
- `exec` copies the parent's pages from the PSP up to `PSP_TOP`, then `r0` to `$7F`, to 5 RAM
  banks. Boot and `exec` set `PSP_TOP` to the page of `$9EFF`; a UXCBASIC program sets
  its own at start-up (section 12). `exec` copies no page past `$9EFF`, whatever `PSP_TOP` holds.
  It builds the child's PSP in place: copies of the parent's handles, each counted once more in its
  system file table entry, and the command tail. The child starts with the parent's RAM bank.
  `exec` sets the child's `PSP_HEAP` to VARBANK and its floor there to the bump pointer.
- `RTS` from the program's start is `exit(0)`. `exit(code)` closes the child's handles, drops
  the child's strings in VARBANK and compacts it from the child's floor, and copies the parent
  back; `exec` then returns to the parent, and the parent reads the code with
  `exitcode`. This replaces MS-DOS's split of `COMMAND.COM` into a resident part and a transient
  part.
- Trap: a program that writes RAM above its `PSP_TOP` page, by `POKE` or `ContentsAt`, loses it
  across an `exec`.
- Up to 4 programs run one inside another, each level with its own 5 save banks. A fifth `exec`
  gives error 8.
- The ROM monitor is the top level: `RUN path [tail]` runs a program from it.
- `keep` ends a program but leaves its banks allocated, with its IRQ hook in place: a TSR.
- Every RAM bank records the PSP that owns it. `exit` frees the banks of the program that ends.
- The environment is a bank of `NAME=value` strings. A child gets a copy of its parent's.
- The STOP key is Ctrl+C. Call 47 `con_break` sets its mode, which `PSP_BREAK` holds:

  | Mode | Name | Ctrl+C |
  |---|---|---|
  | 0 | `BREAK_OFF` | is the character `$03` |
  | 1 | `BREAK_END` | prints `^C`, CR and LF, and ends the program with code 0; `exitcode` then gives X = 1 |
  | 2 | `BREAK_CATCH` | is dropped and sets the break flag |

  - `exec` starts each child in `BREAK_END`. The parent's mode comes back with its PSP. Boot
    sets `BREAK_OFF` for the monitor.
  - A get, with carry set, gives the mode in A and the flag in X, and clears the flag. A set,
    with carry clear, takes the mode in A; a mode above 2 gives error 13.
  - `con_status` checks for Ctrl+C, in the key queue and from the SMC. Ctrl+C is seen only
    while a program asks for a key: `con_status`, `con_in`, `con_line`, UXCBASIC's `GETKEY`.
  - `BREAK_END` ends the program from inside any call: the stack goes back to the pointer at
    PSP offset `$00`.
  - Vector 1 of `getvect` and `setvect`, the break handler, is not used.
- A disk error calls the disk error handler. The default one asks "Abort, Retry, Ignore?".

KERNAL entries:

- The ROM has no KERNAL calls. A program calls the API (section 4).
- `$FFCF` jumps to `con_in` and `$FFD2` to `con_out`, at the stock KERNAL's addresses, for
  x16emu's `-bas` and `-echo` (section 10). They are not API.

## 8. The shell

- `CMDSHELL.COM` is the one shell: a UXCBASIC program on the boot drive. `SHELL=` in
  `CONFIG.SYS` names another.
- After the banner the ROM runs `C:\CMDSHELL.COM` with an empty tail, and runs it again each
  time it ends. When `exec` fails, as with no `C:\CMDSHELL.COM`, the ROM goes to the monitor and
  prints nothing.
- It calls the API through `DOS.UXI` (section 2).
- Its language is a small BASIC, not MS-DOS's command language.
- The prompt and a script take the same language. A line typed at the prompt runs as a script of
  one line.
- The prompt starts in column 0: when the cursor is past column 0, the shell prints a new line
  first. An error message does the same.
- The shell runs in `BREAK_CATCH` (section 7). At the prompt a Ctrl+C typed in the line does
  nothing.
- Statement names, variable names and labels are taken in capitals, whatever the case typed.

### Statements

| Group | Statements |
|---|---|
| Screen | `PRINT`, `INPUT`, `CLS`, `LOCATE row,column`, `COLOR foreground,background`, `BEEP`, `WAIT seconds` |
| Flow | `IF`, `ENDIF`, `GOTO`, `GOSUB`, `RETURN`, `REPEAT n`, `ENDREP`, `END`, `ONERROR(n)` |
| Files | `FILES [pattern]`, `LIST file`, `COPY from to`, `DELETE file`, `RENAME old new`, `MKDIR`, `RMDIR`, `CHDIR` |
| System | `VERSION`, `PAUSE`, `SETSYS`, `BIND`, `RUN` |

Short names:

| Name | Short name |
|---|---|
| `CHDIR` | `CD` |
| `DELETE` | `DEL` |
| `MKDIR` | `MD` |
| `RMDIR` | `RD` |
| `RENAME` | `REN` |
| `VERSION` | `VER` |

- `name = expression` sets a variable.
- A line that starts with `REM`, `'` or `//` is a comment and does nothing. A comment may follow
  an `IF` condition: `IF A=1 ' NOTE`. No other statement takes a comment after it. `REMARK` is
  a name, not a comment.
- `NAME:` alone on a line is a label, a place for `GOTO` and `GOSUB`.
- `IF condition statement` runs the statement when the condition holds. The statement may be an
  `IF`: `IF A=1 IF B=2 PRINT "X"`.
- `IF condition` with nothing after it starts a block, and `ENDIF` ends it. There is no `THEN`
  and no `ELSE`. Blocks work in a script only (Scripts, below).
- `REPEAT n` runs the lines up to `ENDREP` n times, in a script only.
- `END` ends the script. At the prompt it ends the shell.
- `RUN name` ends the script, then runs the program or script `name`.
- `LIST file` prints a text file.
- `LOCATE row,column` moves the cursor. Rows run 0 to 29 and columns 0 to 79. A value out of
  range gives `Syntax error`.
- `COLOR foreground,background` sets the color of the characters written after it:
  `COLOR WHITE, BLUE`. Each value runs 0 to 15 (Variables, below). Both are needed. A value out
  of range gives `Syntax error`.
- `BEEP` prints the BEL, `CHR$(7)`. The console makes no sound for it yet.
- `PAUSE` waits for a key and drops it. It prints nothing. The key comes from the keyboard, even
  under `FROM`. Ctrl+C ends it too.
- `WAIT seconds` waits that many seconds, 60 VSYNCs each. Only Ctrl+C ends it, checked once a
  second. A value below 0 gives `Syntax error`.
- `BIND LS=FILES` makes `LS` run `FILES` (Aliases, below).

### Variables

- `A` to `Z` are numbers: signed 16-bit, UXCBASIC's `WORD`.
- `A$` to `Z$` are strings of up to 255 characters. Their text lies in VARBANK (section 3), and
  their 26 descriptors in the shell's RAM.
- A number prints with no spaces around it: `PRINT 42` gives `42`.
- The color names are numbers that cannot be set: `BLACK` 0, `WHITE` 1, `RED` 2, `CYAN` 3,
  `PURPLE` 4, `GREEN` 5, `BLUE` 6, `YELLOW` 7, `ORANGE` 8, `BROWN` 9, `LIGHTRED` 10, `DARKGRAY`
  11, `GRAY` 12, `LIGHTGREEN` 13, `LIGHTBLUE` 14, `LIGHTGRAY` 15. `DOS.UXI` gives the same
  names as CONSTs: `DOS.BLUE`.
- Trap: the shell's color table in `COLOR_NUMBER` lists the names in the order of their values
  in `DOS.UXI`. Change both together.
- A number expression takes `+`, `-`, `*`, `/`, brackets and a unary minus. `*` and `/` come
  before `+` and `-`. `/` gives a whole number, cut toward 0: `-7 / 2` is `-3`.
- A string expression joins quoted strings and string variables with `+`.
- The six comparisons `=`, `<>`, `<`, `>`, `<=`, `>=` work on two numbers or two strings, in
  `IF` only. A number comparison is signed: `-1 < 0` holds. There is no `MOD`, `AND`, `OR` or
  `NOT`.
- `PRINT` takes expressions separated by `;`. A `;` at the end keeps the line.
- Errors print on a line of their own and stop the statement: `Syntax error`, `Type mismatch`,
  `Division by zero`, and `Bad command or file name` for an unknown name.
- The system variables are `CURDIR$`, `PATH$`, `PROMPT$`, `EDITOR$` and `TEMP$`. `CURDIR$` is
  read only. `PATH$`, `PROMPT$` and `EDITOR$` are VARBANK system descriptors 9 to 11, and
  `TEMP$` is 13 (section 3), so they outlast a program.
- `PATH$ = "C:\BIN"` sets a system variable, as `SETSYS PATH$ = "C:\BIN"` does.
- `SETSYS name = expression` takes a name of 5 characters or more, then `=`, and sets it as an
  assignment does. `SETSYS CURDIR$ = ...`, `SETSYS A$ = ...` and `SETSYS PROMPT$` are syntax
  errors.
- `SETSYS` alone prints `PATH$=`, `CURDIR$=`, `PROMPT$=`, `EDITOR$=` and `TEMP$=`, each with
  its value, one a line.
- `PATH$` holds directories separated by `;`.
- The prompt prints `PROMPT$`. When `PROMPT$` is empty it prints the current drive and `>`:
  `C>`.
- `PROMPT$` takes MS-DOS's `$` codes, the letter in either case:

  | Code | Prints |
  |---|---|
  | `$P` | the current drive and directory |
  | `$N` | the current drive |
  | `$G` | `>` |
  | `$L` | `<` |
  | `$B` | `\|` |
  | `$Q` | `=` |
  | `$_` | a new line |
  | `$$` | `$` |

  A `$` before any other character prints nothing. `PROMPT$ = "$P$G"` gives `C:\>`.
- No part of the system reads `EDITOR$` yet.

### Aliases

- `BIND name = command` makes the name run the command: `BIND LS = FILES`. The command is the
  rest of the line, spaces at its start dropped. A `BIND` of a name that has an alias replaces
  it.
- `BIND name =` with no command removes the alias.
- `BIND` alone prints each alias as `NAME=command`, one a line.
- `BIND name` with no `=`, and `BIND = command`, are syntax errors.
- A line whose first word is an alias runs as the command followed by the rest of the line:
  after `BIND SAY = PRINT "A";`, the line `SAY "B"` prints `AB`.
- The word is the whole name: after `BIND V = VERSION`, `V.COM` runs a program `V.COM`.
- An alias is expanded once. After `BIND XV = VERSION` and `BIND V = XV`, the line `V` runs a
  program `XV`.
- A statement name never reaches an alias.
- The aliases are one string, VARBANK system descriptor 12 (section 3): `NAME=command`, a CR
  after each. A `BIND` that takes the string past 255 characters gives `Insufficient memory`.

### Arguments

- A file argument is a string expression when it starts with a quote, a string variable or
  `CURDIR$`: `FILES "*.CMD"`, `LIST F$`. Any other word is text up to a space:
  `LIST STARTUP.CMD`, and `MKDIR A` makes the directory `A`.
- An option starts with `-`: `FILES -W`. A `/` is always a path separator.
- `CURDIR$` is the current drive and directory: `C:\DOCS`, and `C:\` at the root.

### Files

- `FILES [pattern]` prints as the monitor's `DIR`, then `N File(s)`. A pattern that names a
  directory lists the names in it; no pattern lists the current directory.
- `LIST file` writes the file to handle 1, and ends with a new line when the file does not end
  in a line feed.
- `COPY from to` takes `*` and `?`. `to` is a directory when it ends in `\`, `/` or `:`, or names
  one; each file then keeps its name. A wildcard with a file `to` gives `Target must be a
  directory`. It prints `N File(s) copied`, and `Insufficient disk space` when the drive fills.
- `DELETE` takes no wildcard.
- An API error prints the kernel's message for it.
- Trap: `COPY` onto the same file, as `COPY A.TXT .\A.TXT`, empties it. The shell does not
  compare the two paths.

### Running a name

- A line whose first word is not a statement runs that word as a name. The word ends at the
  first space.
- `RUN name` takes the name as a file argument, and skips the statement names and the aliases:
  `RUN FILES` runs a program `FILES`, and `RUN "TO" + "OL"` runs `TOOL`.
- The name is taken in capitals. A name with `*` or `?` names nothing.
- A name with an extension is looked for as typed. Any other is looked for as `NAME.SCOM`, then
  `NAME.COM`, then `NAME.CMD`.
- A name with a directory is looked for in that directory only. Any other is looked for in the
  current directory, then in each directory of `PATH$`. An empty part of `PATH$` is skipped, and
  a `\` is added to a part that does not end in one. An alias (Aliases, above) comes before
  all of them.
- A name not found prints `Bad command or file name`.
- A `.SCOM` file, a scriptable COM file, is a commandlet. Its format is a `.COM` file's (section 7).
- `NAME.SCOM` is a long name on the card, with an 8.3 alias that ends in `.SCO`.
- A `.SCOM` or `.COM` program runs as a child with `exec`. The script goes on when the child ends.
  An `exec` error prints the kernel's message for it.
- The words after the name are file arguments (Arguments, above). The shell sets `P1$` to `P9$`
  to empty, then puts the first 9 arguments in them, one each. The command tail is every
  argument, each after a space: `TOOL A "B C"` sets `P2$` to `B C` and the tail to ` A B C`.

### Scripts

- A `.CMD` file is a script, in the language of the prompt.
- A script run by name or by `RUN` ends the script that ran it, as an MS-DOS 2.0 batch file
  does. It ends it also when the new script cannot be read.
- The shell reads a script through a read-ahead of 255 bytes, the start of `COPY_BUFFER`. A line
  in the read-ahead is read from it. Otherwise the shell opens the file, seeks to the script's
  position, reads 255 bytes into the read-ahead, and closes the file. A script has no size
  limit.
- A jump empties the read-ahead: `GOTO`, `GOSUB`, `RETURN`, and an `ENDREP` that goes back.
  `LIST` and `COPY` empty it too, since they use `COPY_BUFFER`.
- The shell keeps the script's full path, with the drive and the current directory at the start,
  so a `CHDIR` in the script does not lose its file. A path with a drive and no root, as
  `C:NAME.CMD`, is kept as it is.
- An open or read error is reported and ends the script.
- The end of the file ends the script after its last line runs.
- Trap: a script edited while it runs goes on at its old position. Up to 255 bytes after it
  come from the read-ahead, the text from before the edit.
- A line ends at a line feed. A CR is dropped. A line is cut at 127 characters. The lines are
  not echoed.
- An error in a script line prints the message, then the script and the line number, and ends
  the script:

  ```
  Syntax error
  in C:\SCRIPTS\ERR.CMD line 2
  ```

- `ONERROR(1)` makes an error go on to the next line, with no line number printed. `ONERROR(0)`
  makes an error end the script. The argument is a number expression, of which the low byte
  counts. Each script starts with `ONERROR(0)`. At the prompt `ONERROR` does nothing.
- `END` ends the script. `RUN name` ends the script, then runs `name`.
- `C:\STARTUP.CMD` runs when the shell starts. `C:` is the boot drive. A shell run as a child
  runs it too. It gets no arguments, and the slots keep their values.
- A label is a name of 2 characters at least, then a colon, alone on a line; spaces may come
  before the name and the colon. A letter and a colon is a drive: `D:` alone gives `Bad command
  or file name`. Text after a label's colon is a syntax error. A label does nothing when it runs.
- `GOTO name` reads the script from its start, one line at a time, to the first line that is the
  label. Not found gives `Label not found`, and the script stays at the line after the `GOTO`.
- `GOSUB name` keeps the line after it, then goes to the label as `GOTO` does. `RETURN` goes back
  to the line kept. `RETURN` with no `GOSUB` gives `RETURN without GOSUB`.
- `GOSUB` and `REPEAT` share one stack of 16 entries; a 17th gives `Insufficient memory`. Each
  script starts with an empty stack.
- A block `IF` whose condition fails skips the lines up to its `ENDIF`. A skipped line is read
  only to its first name: `IF` and `REPEAT` open a block, `ENDIF` and `ENDREP` close one, and
  any other line is skipped. `ENDIF` and `ENDREP` each close a block of either kind. A comment
  is skipped, so `REM ENDIF` closes no block.
- A skipped line prints no error. A skipped division by 0 divides by 1, so a skipped
  `IF A/B=1` block still counts.
- Trap: a skipped `IF` line with a syntax error opens no block.
- A block that runs keeps no state: its `ENDIF` checks its syntax and does nothing, so a `GOTO`
  out of a block is safe.
- `REPEAT n` takes a number expression. An n below 1 skips the body, as a failed block does.
  An n above 255 gives `Syntax error`.
- `ENDREP` goes back to the line after its `REPEAT` until the body has run n times. With no
  `REPEAT` on top of the stack it gives `Syntax error`.
- `RETURN` inside a loop drops the loops above the last `GOSUB`.
- Trap: a `GOTO` out of a loop leaves its entry on the stack; 16 of them fill it.
- A script that ends inside a skipped block ends the skip. So does a script read error.
- At the prompt `GOTO`, `GOSUB`, `RETURN`, `REPEAT` and `ENDREP` check their syntax, then do
  nothing. A block `IF` does nothing.
- A script's arguments go into the string slots: `BACKUP A B` sets `P1$` to `A` and `P2$` to `B`.
- Trap: the next program the script runs clears the slots. A script copies its arguments into its
  own variables first.
- Ctrl+C during a script line, or a program the line runs that Ctrl+C ends, asks after the line:

  ```
  Terminate CMD job (Y/N)?
  ```

  The shell waits for y, Y, n or N and echoes it in capitals. Ctrl+C counts as Y. Y ends the
  script; N goes on to the next line. `PAUSE` and `WAIT` end at Ctrl+C, then the question
  comes.
- Trap: the shell checks only the key at the head of the queue. A Ctrl+C typed ahead is seen
  after the line, before the program that would read it. A Ctrl+C behind another key is seen
  only when a program reads up to it.

### Slots

- The slots pass arguments to a program and results back.
- The slots are `P1$` to `P9$`, strings of up to 255 characters. There are no number slots.
- They are VARBANK's system descriptors 0 to 8 (section 3), so they outlast the program's
  `exit`. A program reaches them with the string heap calls; the kernel has no slot call.
- Before it runs a program the shell sets every slot to empty. It then puts the arguments in
  `P1$`, `P2$` and on, one word each.
- A program may change any slot. The shell reads them back when the program ends.
- The convention: `P1$` holds the main result.
- The convention: a commandlet given the argument `SILENT` prints nothing and gives its result in
  the slots only.

### Redirection

- `TO file` after a statement sends its output, handle 1, to a new file. `APPEND file` adds the
  output to the file's end; a missing file is created. `FROM file` takes the input, handle 0,
  from the file. `FROM` a missing file gives `File not found`.
- They are words, so `IF A>1 FILES` is a comparison.
- The word is found in any case, outside quotes, before a space or the end of the line. The file
  is a file argument (Arguments, above). `PRINT 1 TO` and `PRINT 1 TO A B` are syntax errors.
- A statement takes one redirect: `PRINT 1 TO X APPEND` is a syntax error.
- A word `TO`, `APPEND` or `FROM` among a program's arguments is a redirect. In quotes it is an
  argument: `TOOL "FROM" A`.
- `IF` passes its redirect to the statement after the condition: `IF A=2 PRINT "NO" TO N.TXT`
  creates no file when `A` is not 2. `BIND` keeps the redirect in the alias's command.
- A child program gets the redirected handles, so its `INPUT` reads from a `FROM` file.
- Input from a file is not echoed: `con_line` reads a file on handle 0 (section 4).
- An error prints on the screen and ends the redirect. The file keeps what was written before
  it.
- `RUN X.CMD TO F` leaves `F` empty: the script's lines run after the redirect ends.
- An alias whose command has its own `TO` ends the first one, which leaves that file empty.
- A pipe, `A | B`, runs `A` with its output into a pipe file, then `B` with its input from that
  file. The end of the file gives `B` an empty line.
- A chain, `A | B | C`, takes the pipe files `PIPE1.$$$` and `PIPE2.$$$` in turn. The shell
  deletes both when the line ends.
- The pipe files go in the directory `TEMP$` names: `TEMP$ = "C:\TMP"` gives `C:\TMP\PIPE1.$$$`.
  A `\` goes between unless `TEMP$` ends in `\`, `/` or `:`. An empty `TEMP$` puts them in the
  root of the current drive, as MS-DOS 2.0 does.
- A `TEMP$` over 118 characters, or a missing directory, gives `Path not found`.
- A `|` in quotes is text: `PRINT "A|B"` prints `A|B`.
- A comment line is not read for `|`, `TO`, `APPEND` or `FROM`.
- Each part of a pipe may have its own `TO`, `APPEND` or `FROM`.
- An error in any part prints on the screen and ends the line: `PRINT 1 TO | PRINT 2` gives
  `Syntax error` and runs no `PRINT 2`.
- An `IF` condition covers the whole pipe: `IF A=2 PRINT "NO" | INPUT N$` runs neither part
  when `A` is not 2.
- An alias whose command has a `|` takes the rest of the line into the part after its `|`.

### Commandlets

- These stay out of the shell, as `.SCOM` UXCBASIC programs: `EXIST`, `DISKFREE`, `DISKINFO`,
  `DATE`, `TIME`, `UPTIME`, `WHERE`, `MEM`. There is no `FORMAT` and no `MOUNT`.
- `HELP` is a DOS utility, `HELP.COM`, not a commandlet.
- Both lie in the card's folder `\DOS`. `PATH$` is empty at boot, so the shell finds them only
  after `PATH$ = "C:\DOS"`.
- The build compiles each `src/scom/NAME.UXB` to `build/DOS/NAME.SCOM`, and each
  `src/dos/NAME.UXB` to `build/DOS/NAME.COM`. It copies each `src/dos/NAME.TXT` to `build/DOS`.
- `src/scom/SCOM.UXI` is included by each commandlet, after `DOS.UXI` and `HEAP.UXI`. It gives
  the constants `SLOT_P1` to `SLOT_P9`, the system string numbers 0 to 8 of `P1$` to `P9$`,
  and the flag `SILENT AS UBYTE`. `HEAP.SYS_STRINGS_GET(SLOT_P1)` reads `P1$`, and
  `HEAP.SYS_STRINGS_SET(SLOT_P1, text)` writes it.
- `DISKFREE [d:] [SILENT]` prints the free kilobytes of drive `d`, or of the current drive with
  no `d:`: `880 KB free`.
  - It sets `P1$` to the number.
  - The colon may be left off, and a small letter is the same as a capital. `SILENT`, in
    capitals, prints nothing. It is `P1$` with no `d:`, else `P2$`.
  - A drive that is not a letter, or that the kernel does not know, prints `Invalid drive`, sets
    `P1$` to empty, and gives exit code 1. The exit code is 0 otherwise.
  - The kernel's `diskfree` reads the free count of the FS information sector (section 6).
- `DISKINFO [d:] [SILENT]` prints the size of a drive, as `CHKDSK` does:

  ```
       1024 KB total
        880 KB free
       1024 bytes a cluster
       1024 clusters
        880 clusters free
  ```

  - It sets `P1$` to `P5$` to the five numbers, in that order.
  - It takes the drive and `SILENT` as `DISKFREE` does, and fails as it does.
  - The kilobytes are counted from the sectors, so a card past 4 GB does not overflow.
- `DATE [yyyy-m-d] [SILENT]` prints the date of the RTC with its weekday, in ISO form:
  `Sun 2026-10-18`.
  - It sets `P1$` to the date, `2026-10-18`, `P2$` to the weekday, `Sun`, and `P3$` to `P5$`
    to the year, the month and the day, `2026`, `10` and `18`.
  - With a date it sets the RTC, prints nothing, and reads the date back into the slots. The
    year is 1 to 4 digits and runs 2000 to 2099. The month and the day are 1 or 2 digits.
  - `SILENT`, in capitals, prints nothing. It is `P1$` with no date, else `P2$`.
  - A date not in that form, or that does not exist, prints `Invalid date`, sets `P1$` to
    empty, and gives exit code 1. The exit code is 0 otherwise.
- `TIME [h:mm[:ss]] [SILENT]` prints the time of the RTC in 24 hours: `13:45:07`.
  - It sets `P1$` to the time, `13:45:07`, and `P2$` to `P4$` to the hours, the minutes and
    the seconds, `13`, `45` and `7`.
  - With a time it sets the RTC, prints nothing, and reads the time back into the slots.
    Each number is 1 or 2 digits. The seconds are 0 when left out.
  - It takes `SILENT` as `DATE` does. A time not in that form, or out of range, prints
    `Invalid time`, sets `P1$` to empty, and gives exit code 1.
- `UPTIME [SILENT]` prints the time since boot: `0 days 01:12:33`.
  - It sets `P1$` to the seconds since boot, `4353`, `P2$` to the days, `0`, and `P3$` to the
    rest, `01:12:33`.
  - It counts VSYNCs, 1250 in 21 seconds: VERA's 25 MHz pixel clock over 800 by 525 pixels.
    The count times 21 over 1250 is worked in two parts, so the product stays in 32 bits.
  - Trap: x16emu's RTC runs on the host's clock. A test reads the time back only straight
    after it sets it.
- `HELP [topic]` prints the help on a topic from `C:\DOS\HELP.TXT`. `HELP` alone lists the
  topics on one line.
  - The topic is taken in capitals: `HELP dir` is `HELP DIR`.
  - In `HELP.TXT` a line `:NAME`, in capitals, starts a topic. Its text runs to the next line
    that starts with `:`.
  - A line past 80 characters is cut. There is no paging.
  - An unknown topic prints `No help for TOPIC` and gives exit code 1. With no `HELP.TXT` it
    prints `File not found` and gives exit code 2. The exit code is 0 otherwise.
- `VIEW name` is a DOS utility, `VIEW.COM`, for the command line. It shows a text file a page at
  a time.
  - The page is 29 rows of text and a footer row in black on light grey. The footer shows the
    name cut to 24 characters, the number of the top line, `Wrap` or the first column shown,
    and the keys.
  - Up and Down move one line, PgUp and PgDn a page, Space a page down. Home goes to the first
    line, End to the last page. Left and Right move the view 8 columns sideways.
  - W turns wrap on and off. A wrapped line takes 1 to 4 rows, and Left and Right do nothing.
  - F, f or `/` asks for a text on the footer row and finds it from the top line down, in any
    case. N finds it on the next line after the match. The first match on a line shows in
    reversed colors. When no line has it, the footer says `Not found`, and the next N starts
    at line 1. An empty text finds nothing.
  - Q, q or Esc clears the screen and ends it.
  - A line ends at CR, LF or CR LF. A tab goes to the next column that is a multiple of 8. BS,
    BEL, FF, `$0F` and Esc show as `.`. A line is 255 characters at most; the rest is cut.
  - It keeps an index entry for every 16th line, 1024 entries in 3072 bytes, so it seeks to any
    of the first 16384 lines. A line past them reads on from the last entry.
  - No name prints `Required parameter missing` and gives exit code 1. A file that does not open
    prints its error message and gives exit code 2. The exit code is 0 otherwise.
- `TREE [d:][path] [-F]` is a DOS utility, `TREE.COM`, for the command line. It draws every
  directory below `path`, or below the root of drive `d`, as a tree.
  - The first line is `ROOT`, or the start path. Each directory prints one line, ` +- ` and its
    name, under its parent and 4 columns in. A ` |  ` bar runs down past the lines of a
    directory that has a later directory beside it.
  - `-F` adds the names of each directory's files under its line, then a line of bars.
  - `.` and `..` are skipped. Hidden and system names are listed.
  - A start with no directories prints `No sub-directories exist`.
  - A directory 32 levels down, or one whose path passes 217 characters, is listed but not
    entered. The `F` may be small.
  - A drive that is not a letter, or that the kernel does not know, prints `Invalid drive`. A
    path that is not a directory prints `Invalid path`. A switch other than `-F` prints
    `Invalid switch`, and a second path prints `Too many parameters`. Each gives exit code 1.
    A read error prints its error message and gives exit code 2. The exit code is 0 otherwise.
- `MORE [file]` is a DOS utility, `MORE.COM`, for the command line. It shows `file`, or with no
  file the input on handle 0, a screen at a time.
  - After each screen of rows less 1 it prints `-- More --` on the last row and waits for a
    key. Any key clears the prompt and shows the next screen. The prompt shows only when more
    text follows. Ctrl+C at the prompt ends it.
  - Rows are counted as the console writes them: CR, LF and CR LF end a line, a line wider
    than the screen takes more rows, a tab goes to the next column that is a multiple of 8, BS
    moves back a column, and FF clears the screen. Each byte of an escape sequence counts as a
    column. Ctrl+Z ends the text.
  - With no file, `MORE` ends when handle 0 has nothing to read, so `MORE` alone at the prompt
    prints nothing.
  - A second name prints `Too many parameters` and gives exit code 1. A file that does not open
    prints its error message and gives exit code 2. The exit code is 0 otherwise.
- `HEAD [-n count] [file]` is a DOS utility, `HEAD.COM`, for the command line. It writes the
  first `count` lines of `file`, or with no file of the input on handle 0.
  - `count` is 0 to 65535, 10 when left out. A file with fewer lines is written whole. The
    `n` may be a capital.
  - CR, LF and CR LF end a line. Ctrl+Z ends the text.
  - With no file, `HEAD` ends when handle 0 has nothing to read, so `HEAD` alone at the prompt
    prints nothing.
  - `-n` with no count prints `Required parameter missing`, a count that is not a number up to
    65535 prints `Invalid parameter`, another switch prints `Invalid switch`, and a second name
    prints `Too many parameters`. Each gives exit code 1. A file that does not open prints its
    error message and gives exit code 2. The exit code is 0 otherwise.
- `TAIL [-n count] [file]` is a DOS utility, `TAIL.COM`, for the command line. It writes the
  last `count` lines of `file`, or with no file of the input on handle 0. It takes the count,
  the line ends and the errors as `HEAD` does.
  - It reads back from the end in blocks of 512 bytes until it has found the lines, then
    writes them forward up to a Ctrl+Z or the end.
  - A line end in the last byte ends no line before it.
  - It reads back only as far as the lines it writes, so it does not see a Ctrl+Z before them.
  - A pipe and `FROM` give handle 0 a file, so `TAIL` seeks on it. A device stays at 0, so
    `TAIL` alone at the prompt prints nothing.
- `GREP [-i] [-n] [-v] [-c] pattern [file]` is a DOS utility, `GREP.COM`, for the command
  line. It writes each line of `file`, or with no file of the input on handle 0, that
  matches `pattern`.
  - The pattern matches anywhere in the line. `^` first matches the start of the line, and
    `$` last matches its end. `.` matches any character.
  - `[abc]` matches one of `a`, `b` and `c`, `[a-z]` one of `a` to `z`, and `[^abc]` any
    other character. A `]` first in the set is one of its characters.
  - `*` after any of these matches it 0 or more times. A `*` first in the pattern is a `*`.
  - `\` before a character that is not a letter or a digit takes that character as it is:
    `\.`, `\*`, `\[`, `\\`. Any other character matches itself, so `C:\DOS` matches
    `C:\DOS`.
  - `-i` takes the pattern and each line in capitals. `-n` writes the line number and a
    colon before each line. `-v` writes the lines that do not match. `-c` writes only the
    number of lines it would write. Switches may share one `-`: `-in`.
  - CR, LF and CR LF end a line. Ctrl+Z ends the text. A line over 512 characters is taken
    as two or more lines.
  - Each line is matched in one pass, with no backtracking.
  - With no file, `GREP` ends when handle 0 has nothing to read.
  - The exit code is 0 when a line is written or counted, and 1 when none is. No pattern
    prints `Required parameter missing`, a `[` with no `]` prints `Invalid parameter`,
    another switch prints `Invalid switch`, and a third name prints `Too many parameters`.
    A file that does not open prints its error message. Each gives exit code 2.
- `WHERE name [SILENT]` prints the path of the program the shell runs for `name`:
  `C:\DOS\HEAD.COM`. It is for the command line and scripts.
  - The look-up is the shell's. A name with an extension is looked for as typed, any other
    as `NAME.SCOM`, then `NAME.COM`, then `NAME.CMD`. A name with a directory is looked for
    there only, any other in the current directory, then in each directory of `PATH$`.
  - Only the first match prints. A match in the current directory prints after the drive
    and the current directory.
  - Aliases and the shell's statements are not looked up. A name with `*` or `?` names
    nothing.
  - It sets `P1$` to the path, and to an empty string when nothing is found. `SILENT`, in
    capitals, prints nothing.
  - A name not found prints `File not found` and gives exit code 1. No name prints
    `Required parameter missing` and gives exit code 2. The exit code is 0 otherwise.
- `MEM` shows the free banks. It waits for `bank_alloc` (section 11, step 10).
- `EXIST name` is for scripts. It tells whether a file or a directory `name` exists, and prints
  nothing.
  - It takes one name with no wildcard. It does not check for a wildcard.
  - It sets `P1$` to `1` when the name exists and to `0` when it does not. With no name `P1$`
    stays empty.
  - The exit code is 0 when the name exists, 1 when it does not, and 2 with no name. The shell
    does not read the exit code.

Command history:

- The shell keeps the last 8 lines typed at the prompt, in VARBANK system descriptors 14 to
  21 (section 3). Up brings back the line before, and Down the line after. Down past the
  newest gives an empty line.
- An empty line, or a repeat of the newest, is not kept.

## 9. Reuse

- x16-rom is BSD-2. These parts are ported from it as drivers or kernel code, with their copyright
  headers:
  - SD card over SPI, and FAT32. The FAT32 library is `fat32/` at master `fbe32a6`:
    `src/asm/fat32.s`, `fat32_match.s`, `fat32_lib.inc` and `fat32_regs.inc`. Each file's
    header lists its changes.
  - SMC over I2C, the keyboard and the mouse
  - the RTC
  - the VERA console and the charset
- Checklist for each file ported from x16-rom:
  - Read its own header for its licence. A subfolder can differ from the top-level `LICENSE`.
  - Keep its copyright notice, the two BSD-2 conditions and the disclaimer in the source.
  - Add its copyright notice and the BSD-2 text to `NOTICE`.
- `build.py` copies `LICENSE` and `NOTICE` into `build/` beside the ROM image. BSD-2 requires
  the notice with every binary.
- New code: the kernel, the gate, the API, the monitor and the shell.
- Ideas taken:
  - MS-DOS 2.0: handles, the system file table, the driver chain and its commands, the PSP,
    `exec` and exit codes, the environment, `CONFIG.SYS`, `AUTOEXEC.BAT`, batch files, pipes
    through temporary files, TSRs, the break and disk error handlers, the error numbers.
  - CP/M-65: relocatable programs.
  - A syscall gate in RAM, so the kernel spans ROM banks.

## 10. Tools and build

| Tool | Where |
|---|---|
| ca65, ld65 V2.19 | `tools/cc65/bin`, in the repo, zlib licence |
| x16emu R49 | `C:\8bitProgramming\x16emu\x16emu.exe` |
| Python 3.13 | `C:\Users\Admin\AppData\Local\Programs\Python\Python313\python.exe` |
| UXCBASIC | `UXCBASIC/`; its compiler pyuxc, in `UXCBASIC/pyuxc/`, runs on the PC |
| 64tass 1.60 | `tools/64tass`, for the UXCBASIC templates |

Folders:

| Folder | Holds |
|---|---|
| `src/asm/` | layer 0 and the asm parts of layer 1 |
| `src/bas/` | the UXCBASIC programs |
| `lib/` | the UXCBASIC library: `DOS.UXI`, `HEAP.UXI`, `KEYS.UXI`, `CONS.UXI` and `STR.UXI` |
| `src/scom/` | the commandlets and `SCOM.UXI` |
| `src/dos/` | the DOS utilities and their text files |
| `tools/` | `api.py`, the generator, `build.py`, `tests.py` |
| `tools/cc65/` | `ca65.exe`, `ld65.exe` and the cc65 licence |
| `tests/` | test programs and their expected output |
| `docs/` | this plan, `HANDOFF.md`, the generated API reference |
| `build/` | the ROM image, the SD card image, logs |

- `build.py` runs ca65 and ld65 from `tools/cc65/bin` only, never from `PATH`.
- `build.py` assembles the ROM, compiles each `src/bas/NAME.UXB` to `build/bas/NAME.COM` with
  `tools/uxb.py`, and puts the COM files in the root of the SD card image. A compile takes under
  0.1 s.
- `uxb.py` compiles with pyuxc for its default target, UXDOS16. A source compiles again when its
  COM file is older than the source, than `UXCBASIC/tpl/UXDOS/UXC.TPL.BIN`, or than a
  file the source includes, or than a file of pyuxc. `#INCLUDE` looks in the source's folder,
  then `lib/`.
- `src/asm/rom.cfg` links ROM banks 0 and 1, so `build/UXDOS16.ROM` is 32768 bytes.
- `tools/mksd.py` writes an SD card image from a folder: an MBR, one partition of type `$0C` at
  sector 2048, and FAT32. A name that is 8.3 goes in as its 8.3 name in capitals. Any other
  name, up to 255 characters, goes in as a long name as typed, with an 8.3 alias `BASE~N.EXT`.
  `build.py` makes `build/SD.IMG` from the folder `sd`, 4 MB with 1 sector per cluster: 6016
  clusters, 3008 KB.
- `tools/fatcheck.py IMAGE` checks a card image: the FATs are equal, no cluster is lost or in
  two chains, and each file's chain fits its size. Each run of long-name entries must count
  down from the entry with bit 6 to 1, hold one checksum, type 0 and cluster 0, and end at the
  8.3 entry whose checksum it holds. A run cut by a deleted entry, another run or the end of
  the directory is reported as an orphan.
- Trap: `fatcheck.py` lists about 108 lost clusters on each test card. They are the program
  block that `tests.py` reserves, which the FAT marks as used.
- The emulator runs `x16emu -rom build/UXDOS16.ROM -sdcard build/SD.IMG`.
- `build.py` copies the ROM to `build/TEST.ROM` with the byte `boot_shell` 0, found through the
  label file. `TEST.ROM` boots to the monitor, `UXDOS16.ROM` to the shell (section 8).
- `tests.py` boots `TEST.ROM`, except for the tests in its list `SHELL_ROM_TESTS`, which boot
  `UXDOS16.ROM`.
- The emulator's host file system needs the stock KERNAL. UXDOS16 reads files only from the SD
  card image.
- `tests.py` boots a test ROM headless and compares what it prints with a golden file, as in
  UXCBASIC.
- The test output channel is `x16emu -echo raw`. It prints A each time the PC reaches `$FFD2`,
  which jumps to `con_out`. Every console write goes through `$FFD2`.
- Trap: x16emu turns on `-echo` only when ROM bank 0 holds `MIST` at `$FFF6`.
- Trap: x16emu's stdout turns LF into CR LF, so a console CR LF arrives as CR CR LF.
  `tests.py` folds it back.
- Trap: Windows reserves the file names `CON`, `NUL`, `AUX`, `PRN`, `COM1`–`COM9` and
  `LPT1`–`LPT9`, with any extension. A source file named `con.s` cannot be opened.
- x16emu prints `Unable to find KERNAL cbdos_flags` for a ROM without the stock symbols.
  `tests.py` drops that line.
- A test types keys with `x16emu -bas`: first `tests/NAME.S`, a program that `tests.py`
  assembles to run at `$1000` and types in with the monitor's `E`, or `RUN NAME.COM` for
  `tests/NAME.UXB`; then the lines of `tests/NAME.IN`.
- Every test runs with an SD card image that `tests.py` makes from `tests/sd`: 2 sectors per
  cluster and 1024 clusters, so files cross sectors and clusters. Its root also holds the COM files in
  `build/bas`, each `tests/com/NAME.S` assembled to `NAME.COM` with its code from `$0801`, and each
  `tests/com/NAME.UXB` compiled to `NAME.COM`. A test runs these as child programs. x16emu prints
  `SD card attached.`, and `tests.py` drops that line.
- Trap: x16emu `-bas` stopped typing at the text `\X` in a test. Test input avoids `\X`.
- Trap: `-bas` writes into the keyboard queue at `$A800` and its count at `$A80A` in RAM bank 0.
  It starts once the PC reaches `$FFCF`, and writes only while the I flag is clear. So
  every console read goes through `$FFCF`, and the console takes from the queue with I set.

## 11. Order of work

Each step boots and shows something, and each has a test.

0. Skeleton: `build.py`, the ld65 config, a ROM that boots to a colored screen, and `tests.py`
   with one boot test.
1. The memory map and `tools/api.py` with its generator.
2. Console: reset, stack, IRQ, the `CON` driver with scrolling, CR and LF and a cursor, and the
   SMC keyboard. Keys echo to the screen.
3. Gate and monitor: the syscall gate, the driver chain with `CON` and `NUL`, handles 0, 1 and 2,
   and an asm monitor in ROM with commands named after MS-DOS `DEBUG`: `D` dump, `E` enter,
   `F` fill, `G` go.
4. Reading files: the SD block driver, FAT32 read, drive letters, `findfirst`, and `DIR` and
   `TYPE` in the monitor.
5. Programs: `exec`, `exit`, the PSP with its command tail, and the KERNAL console entries.
   A UXCBASIC "hello" runs from the SD card and prints its command tail.
   5b. The KERNAL file entries: `SETLFS`, `SETNAM`, `OPEN`, `CLOSE`, `CHKIN`, `CHKOUT`, `CLRCHN`,
   `READST`, `LKUPLA`, and logical file 15. A UXCBASIC program reads a file.
6. CBM DOS leaves. A program works with handles only: no device numbers, logical files,
   secondary addresses, command channel, status lines, `@0:NAME,S,W` names or `$` listings.
   6a. `lib/DOS.UXI`: each call goes to the jump table at `$0340` through `SYS`, with
       its arguments in A, X, Y and `r0–r15`. Calls not written give error 1. `DOSAPI` runs on
       UXDOS16 against `tests/sd`.
   6b. The kernel's file calls, each with a test: the current directory of each drive with `.`
       and `..` (`chdir`, `getcwd`); `seek`; FAT32 write (`write` to a file, `create`); `delete`,
       `rename`, `mkdir`, `rmdir`, `diskfree`; `dup`, `dup2`; `ioctl` input status (MS-DOS 44h
       subfunction 6), which UXCBASIC's `EOF` uses.
   6c. The stock harness goes: the stock `DOS.UXI`, the stock tests, the stock branch of
       `tools/tests.py`, and the folder choice in `tools/uxb.py`.
   6d. A UXDOS16 target in pyuxc (UXCBASIC plan section 5).
       - pyuxc compiles for UXDOS16. The stock ROM is not supported; `compile_file`'s
         `target` is `"stock"` in UXCBASIC's `compare.py` only.
       - `tpl/MKTPL.PY` builds a second table, `tpl/UXDOS/UXC.TPL.BIN`, with `tpl/UXDOS/SYS.ASM`
         and `tpl/UXDOS/R-FILE.ASM`. Its record ids are the stock table's.
       - `OPEN` passes the name with the mode's letter last: R, W or A. It calls `open` with
         access 0 for `O.READ`, `create` for `O.WRITE`, and `open` with access 1 then `seek` to
         the end for `O.APPEND`, which creates a missing file. Carry set gives `NOFILE`.
       - `PRINT` sends a string with one `write` to the output handle, 1 or the handle of
         `PRINT #`. A line ends with CR LF. `INPUT` reads with `con_line`. `EOF` calls `ioctl`
         input status. `POS` calls `con_cursor`. `GETKEY` calls `con_status`, then `con_in`.
       - The startup and exit drop the `$0372` charset save and the screen rewrite. `END` calls
         `exit` with code 0, and `END code` with that code. A run-time error exits with code 0.
       - Calls 40 to 42, `con_out`, `con_in` and `con_cursor`, are in the jump table.
       - UXCBASIC's `tests.py` runs its tests on this ROM.
   6e. The KERNAL entries leave the ROM: the file entries, the PSP's `$30–$45`, `CHANNEL_CMD`,
       `tests/KERNAL.*`, and `CHROUT`, `CHRIN`, `GETIN`, `PLOT`, `screen_set_charset` and the
       `$0372` byte. In their place:

       | KERNAL | UXDOS16 call | MS-DOS |
       |---|---|---|
       | `CHROUT` | `con_out`: writes the character in A | 02h |
       | `CHRIN` | `con_in`: waits for a key, returns it in A, no echo | 08h |
       | `GETIN` | `con_status`, then `con_in` | 0Bh, 08h |
       | a string through `CHROUT` | `write` to handle 1 | 40h |
       | `PLOT` | `con_cursor`: gets the row and column with carry set, sets them with carry clear | BIOS 10h, 02h and 03h |
       | `screen_set_charset`, `$0372` | none: the console keeps CP437 | |

       The three calls are in the jump table from 6d. `con_in` still passes through `$FFCF` and
       `con_out` through `$FFD2`, and `MIST` stays at `$FFF6`, for x16emu's `-bas` and `-echo`
       (section 10). Those addresses are not API. Call 16 stays free, so the calls after it keep
       their numbers.
       UXCBASIC's tests that called `$FFD2`, or wrote the sector buffer at `$0400` or the kernel
       variables at `$0600`, moved to `pyuxc/cases`, where they match their GPC golden. Their
       copies in `tests/` call `con_out` at `$03B8` and use `$9E00–$9E11`, the top of program RAM:

       | In `pyuxc/cases` | In `tests/` |
       |---|---|
       | `ASM1` | `ASMBYTES` |
       | `ASM2` | `ASMOPS` |
       | `DIMAT` | `DIMADDR` |
       | `SYS1` | `SYSREGS` |
       | `EXPR2` | `EXPRPEEK` |
       | `POINTER` | `POINTERS` |
       | `RECORD2` | `RECSTR` |

       `ERRSYS` keeps `SYS $FFD2` and `ERRATKIND` keeps `AT $0400`: neither compiles, so neither
       runs. `ZP_MODE` (`$27`) is defined in UXCBASIC's stock table only.
   Order: 6a, then 6b and 6d, 6c when 6b is done, 6e when 6d is done.
7. `CMDSHELL`, the BASIC shell of section 8, built with the one `DOS.UXI`:
   7a. `PRINT` of strings and numbers, `CLS`, `VERSION`, `END`. They replace the first 7a's
       `VER`, `ECHO` and `EXIT`.
   7b. The variables `A` to `Z` and `A$` to `Z$`, `=`, expressions, `PRINT` lists, `INPUT`.
   7c. `FILES`, `LIST`, `CHDIR`, `MKDIR`, `RMDIR`, `DELETE`, `RENAME`, `COPY`, `CURDIR$`.
   7d. `A$` to `Z$` in VARBANK. The slots `P1$` to `P9$` in VARBANK's system descriptors.
       Running `.SCOM` and `.COM` by name, with `PATH$`. `RUN`.
   7e. Scripts, in five parts:
       7e1. A `.CMD` file, read and run one line at a time. `ONERROR`, script arguments,
            `STARTUP.CMD`.
       7e2. Labels, `GOTO`, `GOSUB`, `RETURN`.
       7e3a. `IF` and `ENDIF`, with the six comparisons.
       7e3b. `REPEAT` and `ENDREP`, on the stack `GOSUB` uses.
       7e4. The shell's chains on one value become UXCBASIC's `SELECT CASE`.
   7f. `SETSYS`, `BIND`, `PROMPT$`, `EDITOR$`.
   7g. `TO`, `APPEND`, `FROM`, and the pipe.
   7h. `LOCATE`, `BEEP`, `WAIT`, `PAUSE`, `COLOR`.
   7i. The commandlets of section 8, one a part: 7i1 `EXIST`, 7i2 `DISKFREE`, 7i3 `DISKINFO`,
       7i4 `WHERE`, 7i5 `HELP`, 7i6 `DATE`, `TIME` and `UPTIME` on the clock calls. `MEM`
       comes with step 10. The DOS utilities `VIEW`, `TREE`, `MORE`, `HEAD`, `TAIL` and
       `GREP` follow, one a part.
8. `SYSINIT.COM` with `CONFIG.SYS` and `DEVICE=`. Until then the ROM runs `C:\CMDSHELL.COM`
   itself (section 8).
9. Layer 1 moves to UXCBASIC, one part at a time, as the compiler features land. The parts that
   need nothing new (section 2) are written as `.UXI` libraries first and tested on UXDOS16.
10. Extended memory blocks: `xms_alloc`, `xms_free`, `xms_move`, with `bank_alloc` on top of
    them, and `MEM` shows the free banks. It needs step 5 and can run at any time after it.

## 12. What UXCBASIC needs

Steps 0 to 8 need nothing new from UXCBASIC but the UXDOS16 target of step 6d. A program reads its command tail at `$0780` with
`PEEK`. Section 2 lists which parts need which feature. Step 9 needs these features. They are in
the UXCBASIC plan, section 5, in this order:

1. **Records with `AT`.** `TYPE ... END TYPE` declares a record of `BYTE`, `WORD` and
   `STRING * n` fields. A record at a fixed address describes a kernel table: an SFT entry, a
   DPB, the PSP.
2. **`LONG`**, a 32-bit unsigned type. File sizes, positions and FAT32 sector numbers are 32-bit.
   A 32-bit field is two `WORD` fields until `LONG` exists.
3. **Banked variables:** `DIM SFT(15) AT $A000 BANK 0` puts a kernel table in banked RAM.
4. **Calling a `SUB` by address:** `CALL AT P%`, where `P% = AddrOf(KOPEN)`. Driver vector
   tables need it.
5. **Register-entry `SUB`.** A `SUB` entered by `JSR`, with the registers as variables:

   ```
   SUB KOPEN() REGS        ' REG.A, REG.X, REG.Y hold the registers on entry
     IF REG.A = 0 THEN RETURN ERROR 12   ' sets carry, A = 12
     REG.X = HANDLE                       ' X on exit
   END SUB
   ```

   Such a `SUB` is a valid entry in the jump table.
6. **ROM-able output.** `UXC.DATA $xxxx` puts the variables at a RAM address apart from the code,
   with a raw output that has no load address. The start values are copied at boot.
7. **Relocatable output.**

`LONG` and records are the features being written in UXCBASIC now.

Layer 1 does not need arrays that span RAM banks, in the UXCBASIC plan section 5. Programs use
them for data larger than 8 KB, and on UXDOS16 their banks come from one extended memory block
(section 3).

pyuxc compiles for UXDOS16 (step 6d). The stock ROM is not supported. UXCBASIC's tests run on
the UXDOS16 ROM. A program's start-up stores the page of the end of its variables in `PSP_TOP`
(section 7), with the template `T_TOP`: 5 bytes.

The UXCBASIC compiler is pyuxc, in Python, and programs are compiled on the PC and copied to the
SD card image. The GPC BASIC compiler is frozen. The compiler runs on UXDOS16 only once UXCBASIC
is self-hosted. UXCEDIT is GPC BASIC, and the GPC runtime needs the stock KERNAL, so it does not
run on UXDOS16.

## 13. Still to decide

- The rest of the PSP: the handlers, the environment's bank.
- Whether `exec` takes its 5 save banks from the bank allocator at each level, in place of the
  fixed banks 1 to 20 (section 7). The depth is then bound by free RAM, not by 4 levels. It
  needs step 10.
- Which ROM bank holds which part past banks 0 and 1.
- Whether `A:` and `B:` stay free, or go to IEC drives.
- FAT12 and FAT16: the kernel reads FAT32 only.
- Whether an API string pointer points at UXCBASIC's max byte or at its length byte.
  `tpl/R-FILE.ASM` passes the max byte, with the length at offset 1.
- Whether `CMDSHELL` moves into ROM once UXCBASIC output is ROM-able.
- What the ROM prints when it cannot run `C:\CMDSHELL.COM`.
- The shell (section 8):
  - Whether a child program sees `PATH$` and the other system variables, through the
    environment (section 7).
  - The exit code `END` gives.
  - How a script reads the exit code of the program it ran.
- An editor that runs on UXDOS16.
- Graphics, sound and loadable drivers: not before step 5 works.
- The 65C816: not in the first version.
- What `xms_move` does when the source and the destination overlap.
- How a program reads the bank list of a block, for a UXCBASIC array that spans banks.
- String heaps (section 3): which of VARBANK's system descriptors 22 to 31 go to which use;
  whether `str_free` of the last block lowers the bump pointer, so a temporary string costs no
  GC; how UXCBASIC's strings use a heap.
