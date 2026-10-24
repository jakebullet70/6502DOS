"""The 6502DOS API: every call and every error number. PLAN section 4.

tools/genapi.py reads this file and writes build/gen/api.inc, build/gen/api.s and
docs/API.md. Edit this file, never those.

Conventions for every call:
- A program makes a call with JSR to its entry in RAM: GATE_ENTRIES + 3 * the call number.
  The Entry column gives it; api.inc names it API_NAME.
- Arguments go in A, X, Y and r0-r15. A 32-bit value spans two registers: the low word in the
  first.
- On success carry is clear. On error carry is set and A holds the error number.
- A call changes A, X, Y and the flags. It keeps r0-r15, except the registers it lists as out.
- A path is a pointer to a length-prefixed string.
- A handle goes in X, in and out.
- A drive number is 0 for A:, 1 for B:, and so on, except where a call says 0 is the current
  drive.
"""

VERSION = (0, 1, 0)

# The entry of call 0, in RAM. The gate code runs below it; the page holds 64 entries.
GATE_ENTRIES = 0x0340

# Numbers that are never a call: {number: why}. Their entries run api_bad.
RESERVED = {}


def call(number, name, msdos, does, in_=(), out=(), errors=(), written=False):
    """number: the call number, fixed once released. msdos: the MS-DOS 2.0 function, or None.
    in_ and out: (register, meaning) pairs. errors: the error numbers the call can return.
    written: True when the kernel has the routine api_NAME."""
    return dict(number=number, name=name, msdos=msdos, does=does, in_=list(in_), out=list(out),
                errors=list(errors), written=written)


CALLS = [
    call(0, "create", 0x3C, ("Creates a file, or empties it if it exists, and opens it for reading "
          "and writing. The attributes take read only, hidden, system and archive. A directory, a "
          "read-only file, or a full drive gives error 5. A device name opens the device."),
         in_=[("r0", "path"), ("A", "attributes")],
         out=[("X", "handle")],
         errors=[3, 4, 5, 15, 21, 29, 30],
         written=True),
    call(1, "open", 0x3D, "Opens a file or a device. Access 1 or 2 on a read-only file gives error 5.",
         in_=[("r0", "path"), ("A", "access: 0 read, 1 write, 2 read and write")],
         out=[("X", "handle")],
         errors=[2, 3, 4, 5, 12, 15, 21, 30],
         written=True),
    call(2, "close", 0x3E, ("Closes a handle. The directory entry of a file written through it "
          "takes the file's size and the archive bit."),
         in_=[("X", "handle")],
         errors=[6, 21, 29, 30],
         written=True),
    call(3, "read", 0x3F, "Reads bytes from a handle into memory.",
         in_=[("X", "handle"), ("r0", "buffer"), ("r1", "count")],
         out=[("r1", "bytes read, 0 at the end of the file")],
         errors=[1, 5, 6, 21, 30],
         written=True),
    call(4, "write", 0x40, ("Writes bytes from memory to a handle. A write past the end of a file "
          "makes it longer. On a full drive r1 is less than the count."),
         in_=[("X", "handle"), ("r0", "buffer"), ("r1", "count")],
         out=[("r1", "bytes written")],
         errors=[1, 5, 6, 21, 29, 30],
         written=True),
    call(5, "seek", 0x42, ("Moves the position of a handle. A position may pass the end of the file; a read there "
          "gives 0 bytes. A device stays at 0."),
         in_=[("X", "handle"), ("A", "from: 0 the start, 1 the position, 2 the end"),
              ("r0 r1", "offset, signed 32-bit")],
         out=[("r0 r1", "the new position")],
         errors=[1, 6],
         written=True),
    call(6, "delete", 0x41, ("Deletes a file. A read-only file gives error 5, a directory error 2. "
          "The kernel does not check for open handles: close the file first."),
         in_=[("r0", "path")],
         errors=[2, 3, 5, 15, 21, 29, 30],
         written=True),
    call(7, "rename", 0x56, ("Renames a file or a directory, or moves a file to another "
          "directory on the same drive. A new name that exists, or a directory moved to another "
          "directory, gives error 5. The kernel does not check for open handles: close the file "
          "first."),
         in_=[("r0", "old path"), ("r1", "new path")],
         errors=[2, 3, 5, 15, 17, 21, 29, 30],
         written=True),
    call(8, "attrib", 0x43, "Gets or sets the attributes of a file.",
         in_=[("r0", "path"), ("A", "0 get, 1 set"), ("X", "attributes, to set")],
         out=[("X", "attributes")],
         errors=[1, 2, 3, 5]),
    call(9, "filetime", 0x57, "Gets or sets the time and date of an open file.",
         in_=[("X", "handle"), ("A", "0 get, 1 set"), ("r0", "time, to set"),
              ("r1", "date, to set")],
         out=[("r0", "time"), ("r1", "date")],
         errors=[1, 6]),
    call(10, "ioctl", 0x44, ("The subfunctions are those of MS-DOS 2.0 function 44h. Two are "
          "written. Subfunction 0, device info: r0 = the driver's DEV_ bits for a device, 0 for a "
          "file. `CON` gives $83, `NUL` $84. Subfunction 6, input status: r0 = $FF when a read "
          "would give a byte, else 0. A file gives 0 at or past its end. A device asks its "
          "driver: `CON` gives $FF when a key waits, `NUL` gives 0. Any other subfunction gives "
          "error 1."),
         in_=[("X", "handle"), ("A", "subfunction")],
         out=[("r0", "data")],
         errors=[1, 6],
         written=True),
    call(11, "dup", 0x45, ("Gives the first closed handle to the file of a handle. Both handles "
          "share the position."),
         in_=[("X", "handle")],
         out=[("X", "new handle")],
         errors=[4, 6],
         written=True),
    call(12, "dup2", 0x46, ("Makes a second handle refer to the file of the first, and closes "
          "the second first if it is open. Both handles share the position. A second handle equal "
          "to the first does nothing."),
         in_=[("X", "handle"), ("Y", "second handle")],
         errors=[6],
         written=True),
    call(13, "findfirst", 0x4E, "Finds the first name that matches a pattern with `*` and `?`. "
         "`*` matches any run of characters, dots too, and `?` matches one character. A "
         "pattern that ends in `.` or `.*` also matches a name with no dot. A pattern that "
         "ends in a separator matches every name in that directory. The pattern is up to 32 "
         "characters. Normal files always match; directories, hidden files and system files "
         "match only when their attribute bit is set in A. The volume label never matches.",
         in_=[("r0", "pattern"), ("A", "attributes to include: $02 hidden, $04 system, "
               "$10 directory"), ("r1", "find buffer, 83 bytes")],
         out=[("r1", "find buffer, filled")],
         errors=[2, 3, 15, 21, 30],
         written=True),
    call(14, "findnext", 0x4F, "Finds the next name that matches the pattern of a find buffer.",
         in_=[("r1", "find buffer from findfirst")],
         out=[("r1", "find buffer, filled")],
         errors=[18, 21, 30],
         written=True),
    call(15, "mkdir", 0x39, ("Makes a directory. A name that exists, or a full drive, gives "
          "error 5."),
         in_=[("r0", "path")],
         errors=[3, 5, 15, 21, 29, 30],
         written=True),
    call(16, "str_alloc", None, ("Takes a block of A bytes in the program's string heap and "
          "points the descriptor at r0 to its length byte. The text follows the length byte. A "
          "descriptor is 2 bytes in program RAM, or at $A000-$BFFF in the heap's bank. A full heap "
          "is compacted first. Compaction moves strings and rewrites their descriptors: read a "
          "descriptor again after any str_alloc or str_gc. The block of the descriptor's old "
          "string becomes free."),
         in_=[("A", "length"), ("r0", "descriptor address")],
         out=[("A", "the heap's RAM bank"), ("r1", "the length byte's address in that bank")],
         errors=[8, 9],
         written=True),
    call(17, "rmdir", 0x3A, ("Removes an empty directory. A directory that holds entries "
          "other than . and .. gives error 5, the current directory of its drive error 16."),
         in_=[("r0", "path")],
         errors=[3, 5, 15, 16, 21, 29, 30],
         written=True),
    call(18, "chdir", 0x3B, "Sets the current directory of a drive.",
         in_=[("r0", "path")],
         errors=[3, 15, 21],
         written=True),
    call(19, "getcwd", 0x47,
         "Gives the current directory of a drive, without the drive letter and the first \\.",
         in_=[("A", "drive: 0 the current drive, 1 A:, 2 B:"), ("r0", "buffer, 256 bytes")],
         out=[("r0", "buffer, filled with a length-prefixed path")],
         errors=[3, 15, 21],
         written=True),
    call(20, "getdrive", 0x19, "Gives the current drive.",
         out=[("A", "drive")],
         written=True),
    call(21, "setdrive", 0x0E, "Sets the current drive.",
         in_=[("A", "drive")],
         out=[("A", "number of drive letters")],
         errors=[15],
         written=True),
    call(22, "diskfree", 0x36, ("Gives the size and free space of a drive. The free clusters "
          "are the count in the FS info sector."),
         in_=[("A", "drive: 0 the current drive, 1 A:, 2 B:")],
         out=[("r0", "sectors per cluster"), ("r1 r2", "free clusters"),
              ("r3", "bytes per sector"), ("r4 r5", "total clusters")],
         errors=[15, 21, 30],
         written=True),
    call(23, "con_line", 0x0A, "Reads a line from the console with editing. Byte 0 of the "
         "buffer holds the most characters it takes, CR included, from 1 to 254. The call "
         "puts the length read, CR not included, in byte 1 and the text after it, ended by "
         "CR. Tab does nothing.",
         in_=[("r0", "buffer")],
         written=True),
    call(24, "con_status", 0x0B, "Tells whether a key is waiting, and which modifier keys "
         "are held. `lib/KEYS.UXI` names the modifier bits.",
         out=[("A", "$FF when a key is waiting, 0 when not"),
              ("X", "modifiers: $01 Shift, $04 Caps Lock on, $40 Alt, $80 Ctrl")],
         written=True),
    call(25, "exec", 0x4B, "Runs a program and returns when it ends. `exitcode` gives its "
         "code. The file starts with its load address, which must be $0801, and the rest loads "
         "at $0801, up to $9EFF. A file with more stays open for `exec_rest`. A program that starts with a BASIC line `SYS n` starts at n, any other at "
         "$0801. The program gets the command tail in its PSP at $0780: cut to 126 characters, "
         "and followed by a CR that the length does not count. Its handles are copies of the "
         "caller's. `exec` saves the caller's pages from $0700 to the page in its `PSP_TOP`, "
         "$0702, then its zero page from r0 to $7F, in a run of RAM banks from `bank_alloc`, and "
         "frees the run when the program ends. No free run gives error 8, and so does a fifth "
         "program inside 4.",
         in_=[("r0", "path"), ("r1", "command tail, length-prefixed")],
         errors=[2, 3, 8, 11, 15, 21, 30],
         written=True),
    call(26, "exit", 0x4C, "Ends the program and returns to its parent. `RTS` from the "
         "program's start is `exit` with code 0. Does not return, except with error 1 when no "
         "program is running.",
         in_=[("A", "exit code")],
         errors=[1],
         written=True),
    call(27, "exitcode", 0x4D, "Gives the exit code of the last program that ended.",
         out=[("A", "exit code"), ("X", "how it ended: 0 exit, 1 break, 2 disk error, 3 keep")],
         written=True),
    call(28, "keep", 0x31, "Ends the program as `exit` does, but keeps its RAM banks and its "
         "IRQ hook. Nothing frees the banks. Does not return, except with error 1 when no "
         "program is running.",
         in_=[("A", "exit code")],
         errors=[1],
         written=True),
    call(29, "bank_alloc", 0x48, "Hands out a run of 8 KB RAM banks that follow each other: "
         "the lowest run that is free. A size of 0 gives the number of free banks and hands out "
         "nothing. The banks belong to the running program, and `exit` frees them. Error 8 "
         "when no run of the size is free.",
         in_=[("A", "size in banks, 0 to count")],
         out=[("A", "the first bank of the run, or the number of free banks")],
         errors=[8],
         written=True),
    call(30, "bank_free", 0x49, "Frees a run of banks from `bank_alloc`. Error 9 when A is not "
         "the first bank of a run of the running program.",
         in_=[("A", "the first bank of the run")],
         errors=[9],
         written=True),
    call(31, "getvect", 0x35, "Gives a handler address.",
         in_=[("A", "vector: 0 the IRQ hook, 1 the break handler, 2 the disk error handler")],
         out=[("r0", "address")],
         errors=[1]),
    call(32, "setvect", 0x25, "Sets a handler address.",
         in_=[("A", "vector: 0 the IRQ hook, 1 the break handler, 2 the disk error handler"),
              ("r0", "address")],
         errors=[1]),
    call(33, "getdate", 0x2A, "Gives the date from the RTC. The day of the week is worked out "
         "from the date.",
         out=[("r0", "year, 2000 to 2099"), ("X", "month, 1 to 12"), ("Y", "day, 1 to 31"),
              ("A", "day of the week, 0 Sunday")],
         written=True),
    call(34, "setdate", 0x2B, "Sets the date of the RTC. A date that does not exist gives "
         "error 13. It also sets the RTC's weekday and its battery backup bit, VBATEN.",
         in_=[("r0", "year, 2000 to 2099"), ("X", "month, 1 to 12"), ("Y", "day, 1 to 31")],
         errors=[13],
         written=True),
    call(35, "gettime", 0x2C, "Gives the time from the RTC.",
         out=[("X", "hours, 0 to 23"), ("Y", "minutes"), ("A", "seconds")],
         written=True),
    call(36, "settime", 0x2D, "Sets the time of the RTC, and starts its oscillator.",
         in_=[("X", "hours, 0 to 23"), ("Y", "minutes"), ("A", "seconds")],
         errors=[13],
         written=True),
    call(37, "version", 0x30, "Gives the system version.",
         out=[("A", "major"), ("X", "minor"), ("Y", "patch")],
         written=True),
    call(38, "ticks", None, "Gives the number of VSYNCs since boot.",
         out=[("r0 r1", "ticks")],
         written=True),
    call(39, "errmsg", None, "Gives the message of an error number. Changes r1.",
         in_=[("A", "error number"), ("r0", "buffer, 128 bytes")],
         out=[("r0", "buffer, filled with a length-prefixed message")],
         errors=[1],
         written=True),
    call(40, "con_out", 0x02, "Writes a character to the screen. A handle redirected does not "
         "take it. It obeys CR, LF, BS, TAB, BEL and FF, skips $0F, and obeys these escape "
         "sequences of MS-DOS's ANSI.SYS: `Esc[r;cH` moves the cursor to row r, column c; "
         "`Esc[2J` clears the screen and puts the cursor home; `Esc[K` blanks from the cursor "
         "to the end of the line; `Esc[...m` takes 0 for the color `con_colour` last set, 7 "
         "to swap the foreground and the background, 30 to 37 for the foreground and 40 to 47 "
         "for the background. Rows and columns count from 1. A missing parameter is 0, and 0 "
         "means 1 in `Esc[r;cH`. A row or column past the edge means the last. A sequence "
         "takes up to 4 parameters, each modulo 256. Other sequences do nothing. Esc "
         "then a byte other than `[` shows that byte. `lib/CONS.UXI` names the sequences.",
         in_=[("A", "character")],
         written=True),
    call(41, "con_in", 0x08, "Waits for a key, without echo. An extended key gives two "
         "characters: 0, then its IBM PC BIOS scan code. The scan codes: Up $48, Down $50, Left "
         "$4B, Right $4D, Home $47, End $4F, PgUp $49, PgDn $51, Insert $52, Delete $53, F1 to "
         "F10 $3B to $44, with Shift $54 to $5D, with Ctrl $5E to $67, with Alt $68 to $71. "
         "Alt wins over Ctrl, and Ctrl over Shift. Ctrl+Left $73, Ctrl+Right $74, Ctrl+End $75, "
         "Ctrl+PgDn $76, Ctrl+Home $77, Ctrl+PgUp $84. Alt+1 to Alt+0, Alt+- and Alt+= $78 to "
         "$83. Alt with a letter gives the letter's scan code. Ctrl+2 gives 0, then 3. Ctrl with "
         "a letter, `[`, `\\` or `]` gives $01 to $1D, Ctrl+6 $1E, Ctrl+- $1F. Ctrl with Space "
         "or with a key that gives a control character gives that character. Ctrl with any "
         "other key gives nothing, and so does Alt with a key other than a letter, a digit, - "
         "or =. `lib/KEYS.UXI` names every code.",
         out=[("A", "character")],
         written=True),
    call(42, "con_cursor", None, ("Gets the cursor's row and column with carry set, moves the cursor "
          "with carry clear. The screen has 30 rows and 80 columns. With carry clear, X = $80 or "
          "above leaves the cursor where it is and sets whether it shows: bit 6 set hides it while "
          "a call waits for a key, clear shows it. A program's end shows it again. In UXCBASIC, "
          "`CURSOR OFF` hides it and `CURSOR ON` shows it."),
         in_=[("carry", "set: get, clear: set"), ("X", "row, to set; $80 or above: the cursor's state"),
              ("Y", "column, to set")],
         out=[("X", "row"), ("Y", "column"), ("r0L", "the screen's rows, on a get"),
              ("r0H", "the screen's columns, on a get")],
         written=True),
    call(43, "str_free", None, ("Frees the string of the descriptor at r0 and sets the "
          "descriptor to 0. A descriptor of 0 does nothing."),
         in_=[("r0", "descriptor address")],
         errors=[9],
         written=True),
    call(44, "str_gc", None, "Compacts the program's string heap.",
         out=[("r0", "free bytes")],
         written=True),
    call(45, "str_heap", None, ("Chooses the program's string heap. Bank 11 is the shared heap, "
          "every program's at its start. Any other bank must be one the program took from "
          "`bank_alloc`; it becomes a new, empty heap whose blocks start at r0, and the bytes "
          "from $A00C to r0 are the program's."),
         in_=[("A", "bank: 11, or a bank of the program's"), ("r0", "the first block, $A00C or higher; not for bank 11")],
         errors=[9],
         written=True),
    call(46, "con_colour", None, ("Gets the console color with carry set, sets it with carry clear. "
          "The high nibble is the background and the low nibble the foreground, from VERA's "
          "palette. A new color takes effect for the characters written after the call."),
         in_=[("carry", "set: get, clear: set"), ("A", "color, to set")],
         out=[("A", "color")],
         written=True),
    call(47, "con_break", 0x33, ("Gets the break mode and the break flag with carry set, sets the "
          "mode with carry clear. The mode says what Ctrl+C from the console does: 0 nothing, "
          "it is the character $03; 1 prints ^C and ends the program with exit code 0, and "
          "`exitcode` then gives X = 1; 2 drops the key and sets the flag. A get clears the flag. `exec` "
          "starts each program in mode 1. The console sees Ctrl+C only while a program asks "
          "it for a key."),
         in_=[("carry", "set: get, clear: set"), ("A", "mode, to set: 0 to 2")],
         out=[("A", "mode"), ("X", "flag: 1 when Ctrl+C came in mode 2 since the last get, "
               "else 0")],
         errors=[13],
         written=True),
    call(48, "con_getkey", None, ("Reads a key in one call, extended or not, with carry clear "
          "waiting for it with the cursor blinking, with carry set returning at once. A plain "
          "key gives its character in A and 0 in X. An extended key gives 0 in A and its scan "
          "code in X, the codes of `con_in`. No key gives 0 in both. Y gives the modifiers, as "
          "`con_status` gives them in X."),
         in_=[("carry", "clear: wait, set: return at once")],
         out=[("A", "character, 0 for an extended key or none"),
              ("X", "scan code, 0 for a plain key or none"),
              ("Y", "modifiers: $01 Shift, $04 Caps Lock on, $40 Alt, $80 Ctrl")],
         written=True),
    call(49, "con_edit", None, ("Edits a line from the console, as `con_line` reads one, from "
          "the text in the buffer: byte 1 holds its length, 0 for none, and the text follows "
          "it. The call shows the text first. Enter, Tab or an extended key ends the line. Tab "
          "and the extended key are not echoed, and leave the cursor after the text. The "
          "registers come back as `con_getkey` gives them."),
         in_=[("r0", "buffer")],
         out=[("A", "the key that ended the line: $0D Enter, $09 Tab, 0 an extended key"),
              ("X", "scan code, 0 for Enter and Tab"),
              ("Y", "modifiers: $01 Shift, $04 Caps Lock on, $40 Alt, $80 Ctrl")],
         written=True),
    call(50, "con_screen", None, ("Reads a line from the console with the full-screen editor, "
          "into a buffer as `con_line` fills it. The cursor moves over the whole screen, and Enter "
          "returns the text of the cursor's row without the blanks at its end: from the column "
          "the call started at on the row it started at, from column 0 on any other row. A line "
          "is one row. The keys: the arrows; Ctrl+Left and Ctrl+Right a word; Home the top left "
          "corner; End after the row's text; Ctrl+Home clears the screen; Ctrl+End blanks to the "
          "end of the row; Esc blanks the row; Ins turns insert mode on or off, and a cursor move "
          "turns it off; Del and Backspace delete; Tab moves to the next column of 8, and in "
          "insert mode opens blanks. A Ctrl+C in break mode 2 ends the line with no text. When "
          "handle 0 is a file, the call is `con_line`."),
         in_=[("r0", "buffer")],
         written=True),
    call(51, "bank_call", None, ("Calls the routine at r0 with RAM bank A selected, then selects "
          "the caller's RAM bank again. The routine gets X, and its A, X, Y and carry come back. "
          "The routine may make calls, `bank_call` among them."),
         in_=[("A", "RAM bank"), ("r0", "routine"), ("X", "the routine's X")],
         out=[("A", "the routine's A"), ("X", "the routine's X"), ("Y", "the routine's Y"),
              ("carry", "the routine's carry")],
         written=True),
    call(52, "exec_rest", None, ("Reads the part of the running program's file past $9EFF, "
          "which `exec` leaves open: r1 bytes to r0, from where the last read ended. A buffer at "
          "$A000-$BFFF is in the selected RAM bank. A count of 0 closes the file. The file also "
          "closes when the program ends or calls `exec`. Error 6 when the file is not open."),
         in_=[("r0", "buffer"), ("r1", "count, 0 to close the file")],
         out=[("r1", "the count read, fewer at the end of the file")],
         errors=[6],
         written=True),
]

# The break modes of con_break: (number, name). The name becomes BREAK_NAME in asm.
BREAK_MODES = [
    (0, "OFF"),
    (1, "END"),
    (2, "CATCH"),
]

# Errors: (number, name, message). The numbers and messages are MS-DOS 2.0's. 21, 29 and 30
# are MS-DOS 3.0's numbers for the critical errors drive not ready, write fault and read fault.
# The name becomes ERR_NAME in asm.
ERRORS = [
    (1, "BAD_FUNCTION", "Invalid function"),
    (2, "NOT_FOUND", "File not found"),
    (3, "NO_PATH", "Path not found"),
    (4, "TOO_MANY_FILES", "Too many open files"),
    (5, "ACCESS", "Access denied"),
    (6, "BAD_HANDLE", "Invalid handle"),
    (8, "NO_MEMORY", "Insufficient memory"),
    (9, "BAD_BLOCK", "Invalid memory block"),
    (11, "BAD_FORMAT", "Invalid format"),
    (12, "BAD_ACCESS_CODE", "Invalid access code"),
    (13, "BAD_DATA", "Invalid data"),
    (15, "BAD_DRIVE", "Invalid drive"),
    (16, "CURRENT_DIR", "Attempt to remove the current directory"),
    (17, "NOT_SAME_DEVICE", "Not the same device"),
    (18, "NO_MORE_FILES", "No more files"),
    (21, "NOT_READY", "Drive not ready"),
    (29, "WRITE_FAULT", "Write fault"),
    (30, "READ_FAULT", "Read fault"),
]

# The UXCBASIC names of the errors whose ERR_NAME runs past pyuxc's 16 characters a name part.
# lib/DOS.UXI gets ERR_ and this name; the other errors keep their asm name there.
UXI_ERROR_NAMES = {
    "TOO_MANY_FILES": "TOO_MANY",
    "BAD_ACCESS_CODE": "BAD_ACCESS",
    "NOT_SAME_DEVICE": "NOT_SAME",
    "NO_MORE_FILES": "NO_MORE",
}

# The find buffer of findfirst and findnext, laid out as MS-DOS 2.0's DTA after the search:
# (offset, size, name, field). The name becomes FIND_NAME in asm.
FIND_BUFFER = [
    (0, 41, None, "the search, for findnext"),
    (41, 1, "ATTR", "attributes"),
    (42, 2, "TIME", "time"),
    (44, 2, "DATE", "date"),
    (46, 4, "SIZE", "size"),
    (50, 33, "NAME", "name: a length byte, then up to 32 characters"),
]
