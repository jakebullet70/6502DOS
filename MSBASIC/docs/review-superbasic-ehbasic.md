# Review: F256 SuperBASIC and EhBASIC

This review looks at how two other 6502 BASICs solve the problems we face in the X16 port, before
Step 5 (X16 target on the new Unix-style kernal). It covers design only; no code was copied, and
none may be: EhBASIC derivatives must carry "Derived from EhBASIC".

Sources (read October 2026):

- F256 SuperBASIC: github.com/paulscottrobson/superbasic (commit 1d18424), maintained now at
  github.com/FoenixRetro/f256-superbasic. Kernel: github.com/ghackwrench/F256_MicroKernel.
- EhBASIC: github.com/Klaus2m5/6502_EhBASIC_V2.22 (`basic.asm`, `min_mon.asm`, `bugsnquirks.txt`,
  manual), lgblgblgb/6502_EhBASIC_V2.22, rumbledethumps/ehbasic (RP6502 port).
- picocomputer/msbasic: msbasic on the RP6502, a Unix-style OS. It is the closest earlier
  project to ours and was found while researching EhBASIC.

File paths below are relative to those repositories.

## 1. Line input and editing

### SuperBASIC

- BASIC owns all editing. The kernel only sends key events, and BASIC draws text straight into
  text and colour RAM (`modules/hardware/charout.asm`).
- It is a full-screen editor. On Enter it finds where the logical line starts, copies the screen
  rows into a line buffer, trims trailing spaces and adds a terminator
  (`system.f256/ab.system/input.asm`).
- Long lines: one bit per screen row marks rows that continue the row above. Typing on a full
  row pushes characters into the next row; backspace pulls them back. The line buffer is 253
  bytes, and a line holds at most 252 characters.
- `INPUT` uses a simpler editor: 80 characters, backspace only, no screen read-back.
- Keys include arrows, Ctrl-A/E (start/end of line), Ctrl-D (delete), Ctrl-K (delete to end of
  line), Shift+Enter (move down without running the line) and Ctrl-C (break). BASIC does key
  repeat itself, using kernel timers.
- Lowercase: the line is folded to uppercase outside quotes before tokenizing. LIST prints
  keywords and names in lowercase.
- Variables are looked up or created at tokenize time, and the program stores a reference to the
  variable record, so finding a variable at run time costs nothing.

### EhBASIC

- The input buffer is 71 characters (`Ibuffe = Ibuffs+$47`), the same limit as msbasic. The
  source says the buffer must stay inside one page.
- The only editing is backspace ($08). There is no DEL, no line delete and no cursor movement.
  Control characters and spaces are dropped while the buffer is empty.
- When the buffer is full the character is dropped and BELL is printed.
- BASIC echoes every character, so the terminal must not echo locally.
- Keywords must be uppercase; a patch (`mixed_case_keywords_mod.txt`) folds them. Variable names
  are case-sensitive.

### For our port

- The 71-character limit is the old Microsoft teletype limit (`cpx #$47` in `src/inline.s`).
  Both programs show it is a choice, not a need.
- Move the input buffer out of zero page (msbasic already supports $0200, as on CBM machines),
  make its size one constant, and turn off the `@`/`_` edit keys in favour of BS/DEL.
- Who owns the screen editor depends on whether the new kernal returns whole lines or single
  keys. If it returns keys, the SuperBASIC model (editor in BASIC, behind `MONRDKEY`/`MONCOUT`)
  is a proven design. 80 characters is a good first step; up to 255 with wrapped rows is a good
  later goal.

## 2. File and channel I/O

### SuperBASIC

- There are no file channels: no OPEN, CLOSE, PRINT#, INPUT#, GET# or EOF test. Delete, rename and
  make-directory are also missing, even though the kernel provides them.
- File statements: `LOAD`, `SAVE`, `VERIFY`, `BLOAD "f",addr`, `BSAVE`, `DIR`, `DRIVE n`, `CD`, and
  `DIR LOAD`, which reads up to 127 entries for `dir(n)` / `dir$(n)`.
- `TRY BLOAD|BSAVE ... TO var` stores the error code in a variable instead of stopping with an
  error (`files/try.asm`).
- Programs are saved as plain text and tokenized again on LOAD. LOAD turns tab into space and LF
  into CR, and skips leading spaces and control characters. SAVE ends lines with CR.
- LOAD and NEW ask before they throw away unsaved changes.
- Only two I/O errors exist: "File not found" and "Storage error". End of file is never an error.
- One file is open at a time, read in 64-byte blocks.

### EhBASIC

- The core has no files. `LOAD` and `SAVE` jump through RAM vectors that the porter fills in; the
  minimal monitor points them at an RTS.
- In the RP6502 port, SAVE sends output to the file and calls LIST. LOAD clears the program,
  takes input from the file and lets the normal line-entry loop "type" it; at end of file it
  closes the file and returns to the console. All errors in that port give SYNTAX ERROR, and the
  port uses 65C02 instructions.

### picocomputer/msbasic

- `OPEN lfn,name$[,mode$]` with Unix mode strings, plus PRINT#, INPUT#, GET#, CMD, text LOAD/SAVE
  and `RUN "file"`.
- A short read means end of file.
- LOAD hooks the line-input routine, because `STKINI` resets the stack on every line, so the
  line-entry code cannot be called as a subroutine (`src/loadsave.s`).
- On any error (from `ERROR`) or Ctrl-C during LOAD or SAVE, a cleanup routine closes the file and
  restores the console.
- Bad data in a file gives `?FILE DATA ERROR`.

### For our port

- Our OPEN, PRINT#, INPUT#, GET# and CMD already go further than SuperBASIC and EhBASIC. Read
  picocomputer/msbasic before adding LOAD/SAVE; it solves the same problems on the same
  interpreter.
- Save programs as text with LF line ends; accept CR, LF and CRLF on load.
- Do SAVE by sending LIST output to the file, and LOAD by feeding the file to the line-input
  routine.
- After any error or Ctrl-C during LOAD or SAVE, close the file and return to the console.
- Keep end of file in ST, not as an error. Map kernal errors to a few clear messages, never to
  SYNTAX ERROR. A TRY-style form is optional.
- Add DIR, delete and rename when the kernal offers them.
- Optional: ask before NEW or LOAD discards unsaved changes.

## 3. Kernal interface

### SuperBASIC

- The kernel jump table is at $FF00. Arguments go in a zero-page block ($F0-$FF), carry set means
  failure, and X and Y are kept.
- Everything comes back as an 8-byte event. File open, read, write and close only queue a
  request; the result arrives later as an event (OPENED, DATA, EOF, ERROR, WROTE, CLOSED).
- One wrapper layer (`system.f256/ab.system/wrapper.asm`) makes these calls blocking: it sends
  the request, then reads events (yielding when none are waiting) until the matching one
  arrives, and returns carry plus an error code.
- Break check: each statement tests a "pending events" byte and only handles events when it is
  not zero. The usual case costs one load and one branch.
- BASIC keeps the console, the editor, keyboard handling, key repeat and break. The kernel keeps
  the file system, drives, raw input devices and timers.

### EhBASIC

- Page 2 holds three Ctrl-C bytes (`ccflag`, `ccbyte`, `ccnull`) and RAM vectors for Ctrl-C,
  input, output, LOAD and SAVE. They can be changed while a program runs.
- Input does not wait: a character comes back with carry set, no character gives A=0 and carry
  clear. Output keeps A.
- The Ctrl-C check runs once per statement and can be turned off with `ccflag`. If it reads a key
  that is not Ctrl-C, it keeps the key in `ccbyte` for a while, so a later GET still gets it.
- Interrupts are polled: the IRQ/NMI handler only sets a flag, and the per-statement check jumps
  into the BASIC handler line. Klaus2m5 calls this badly broken, because the handler does not
  clear the interrupt source, so the interrupt fires again at once.

### For our port

- If the new kernal works by request and event, our `K_*` primitives in `handle_io.s` are the
  wrapper layer; each returns carry and an error code.
- Make `ISCNTC` cheap: test a flag or counter, and do the full poll only when it is set.
- Keep any key that the Ctrl-C check reads, so GET does not lose it.
- If we add interrupt statements, BASIC should only poll a flag, and the kernal handler must
  clear the interrupt source.

## 4. Extensions

### SuperBASIC

- Tokens $81 and $82 are prefix bytes for two more keyword pages. Keywords that open a block
  (WHILE, IF, REPEAT, FOR, PROC) and keywords that close one have consecutive token ranges, so
  code that skips a block can track nesting with range compares.
- Dispatch tables and error tables are generated by scripts from tags in the source (`;; [while]`)
  and from a text file of messages.
- Structured statements: PROC/ENDPROC with LOCAL, WHILE/WEND, REPEAT/UNTIL, multi-line
  IF/ELSE/ENDIF, FN/ENDFN, sharing one 512-byte BASIC stack.

### EhBASIC

- Tokens are numbered in sequence from $80, so inserting one renumbers all that follow.
- Keyword lookup is faster than in msbasic: a table of first characters points to a sub-table
  per character, with longer keywords first. LIST uses the same text, so keywords are not stored
  twice.
- Error messages are reached through a table of pointers, not 8-bit offsets.
- DO/LOOP pushes a 5-byte frame like GOSUB.
- Additions include ELSE, INC/DEC, DEEK/DOKE, SWAP, BITSET/BITCLR/BITTST, MAX/MIN, HEX$,
  LCASE$/UCASE$, `<<`, `>>`, EOR, VARPTR, `$hex` and `%binary` literals.

### Bugs fixed in EhBASIC forks (`bugsnquirks.txt`)

Some of these may also be in msbasic and are worth testing:

- An input buffer at $xx00 makes direct statements read from 256 bytes below the buffer.
- The first statement after RUN in direct mode does not set the CONT pointer.
- The "is this string in the input buffer?" test compares against the wrong address.
- Equal strings compare false in direct mode, because the FAC rounding byte is not cleared.
- `x=a$=b$` stores a string pointer.
- The stack check leaves no room for interrupts.
- NEXT or LOOP after IF THEN fails, because IF leaves an extra return address.
- Floating-point multiply rounding, VAL destroying strings, garbage-collection overlap, and a TO
  expression with a subtraction changing sign.

### For our port

- New keywords should go in prefix-byte token pages, so the single msbasic token page and its
  dispatch table stay as they are.
- Error tables with pointers (or one table per group, as our I/O error table already is) avoid
  the 8-bit offset limit.
- A first-character keyword index is a cheap speed-up once many keywords are added.

## Open questions for Step 5

1. Does the new X16 kernal return whole lines (with its own editor) or single keys?
2. Line length: 80 now and up to 255 later, or 255 at once? Decided: 80 now (done in the sim
   target, buffer at $0200).
3. OPEN mode: keep numbers (0, 1, 2) or use mode strings (`"r"`, `"w"`, `"a"`) like
   picocomputer/msbasic? Decided: numbers.
