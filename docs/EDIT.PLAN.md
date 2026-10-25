# EDIT plan: the GPC editor's features

This plan brings EDIT (`src/dos/EDIT.UXB`) up to UXCEDIT, the GPC editor in
`attic/gpc/src/UXCEDIT`. Each step is one part, built and tested on its own. Sizes are
estimates until the step is built.

## The menus

| Menu | UXCEDIT | EDIT now | Step |
|---|---|---|---|
| File | New Ctrl+N | New, no key | E5 |
| File | Open... Ctrl+O | Open..., no key | E5 |
| File | Save Ctrl+S or F2 | Save Ctrl+S | E5 adds F2 |
| File | Save As... | Save As... | — |
| File | — | the recent files | — |
| File | Encoding Ctrl+F7, ASCII or PETSCII | — | not taken |
| File | Exit | Exit Ctrl+Q | — |
| Edit | Undo Ctrl+Z, Redo Ctrl+Y | — | E7 |
| Edit | Cut, Copy, Paste | Cut, Copy, Paste | — |
| Edit | — | Clear Del | — |
| Edit | Select All Ctrl+A | — | E5 |
| Edit | Delete Line Ctrl+L | — | E5 |
| Search | Find... Ctrl+F or F6 | Find... Ctrl+F | — |
| Search | Find Next F3 | Repeat Last Find F3 | — |
| Search | Replace... Ctrl+H | Change... Ctrl+R | E8 adds the verify run |
| Search | Go to Line... Ctrl+G | — | E6 |
| Window | Next Document F7, Document A, B, C | — | E4 |
| Build | Compile F5 | — | not taken |
| Options | — | Display... | — |
| Help | Help F1 | DOS Help Shift+F1 | the help is to come; F1 does nothing |
| Help | Settings... | Options, Display... | — |
| Help | About, with the memory each document holds | About | E9 |

EDIT keeps MS-DOS EDIT's names: Change, Repeat Last Find, Clear and the Options menu.

Not taken:

- Encoding. 6502DOS files are ASCII.
- Build, Compile. The compiler runs on the PC. The item comes with a compiler on the X16.
- The Custom theme builder of `UXCEDIT-THEME.BL`. THEMED.COM builds theme files, which
  `GUI.THEME_FILE` loads.

## The keys

| Key | UXCEDIT | EDIT now | Plan |
|---|---|---|---|
| Ctrl+Left, Ctrl+Right | the word in front, the next word | — | E6 |
| Ctrl+PgUp, Ctrl+PgDn | the first line, the last line | — | E6; Ctrl+Home and Ctrl+End do the same, as MS-DOS EDIT |
| Ctrl+G | Go to Line | — | E6 |
| Ctrl+L | Delete Line | — | E5 |
| Ctrl+Z, Ctrl+Y | Undo, Redo | — | E7 |
| Shift+Delete, Ctrl+Insert | cut, copy | — | E5; E5 adds Shift+Insert for paste |
| Enter | keeps the line's indent | no indent | E6 |
| F6 | Find | — | E5 |
| F7 | the next document | — | E3 |

Trap: UXCEDIT notes that Ctrl+Y arrives as 25, the code of Delete, with Ctrl held. E5 and E7
check what KEYS.UXI gives for Ctrl+Y, Ctrl+Z and Ctrl+L before they take the keys.

The keys help came from TED and is gone: F1, Ctrl+G, Help, Keys, Options, Help Path and the
key `HELP=` of `[EDIT]`. EDIT's own help is to come.

## The text in RAM banks

### How UXCEDIT stores a document

`UXCEDIT-STORE.BL` keeps each document as a line table and an arena in RAM banks:

- The line table holds 3 bytes a line: the bank and the address of the line's record. A bank
  holds 2048 lines.
- The arena holds the records, each a length byte and the characters. A bump allocator hands
  them out from `$A000` to `$BEFF` of the arena's banks. A record is never freed.
- The cursor's line is edited in an edit buffer in low RAM, and stored as a new record when
  the cursor leaves it.
- A line holds 250 characters. A longer line in a file is broken.
- The banks are fixed: document A takes banks 2 to 5 and 16 to 37, 7936 lines. B and C take 13
  banks each, 3840 lines. The clipboard is document 3, in bank 40.
- The undo ring keeps line table slots, since the arena keeps every old record.
- A full arena refuses a record and sets the document full.

### What EDIT does

E1 keeps EDIT's gap buffer and moves it to RAM banks:

- The text is a gap buffer of up to 65535 bytes. Byte `P` of the buffer is in the document's
  bank `P / 8192`, at `$A000 + P MOD 8192`.
- A document takes banks from `BANK.ALLOC(1)` as its text grows, up to 8. Its bank numbers are
  in a table of 8 bytes. The banks need not be next to each other.
- No bank left shows Insufficient memory.
- The routines that read or write the text are in the low part. Trap: a `#REGION_SLOT` SUB
  runs from `$A000`, the window the text banks use.
- `MOVE_GAP` copies across banks through `RUN_BUFFER`, 255 bytes in low RAM.
- Every routine that works on positions keeps working: the cursor, the selection, Find,
  Change, the clipboard and the draw.

UXCEDIT's line table is not taken:

- Its arena never frees a record, so a long session fills it.
- Its lines hold 250 characters.
- Every routine of EDIT works on byte positions, and would be written again for lines and
  columns.
- It needs asm kernels for the slot moves, the load, the save and the find.

A line table gives a line's start at once. EDIT finds a line by counting line ends. Go to Line
and Ctrl+End on a 64 KB text count up to 65535 bytes.

### Memory

| Part | Now | After E2 |
|---|---|---|
| The text | up to 8 banks, 64 KB | the same |
| The clipboard | `$9700` to `$9EFF`, 2048 bytes | one bank, 8192 bytes |

Each read of the text costs a bank select. A page of 26 rows reads about 2 KB.

## The three documents

E3 and E4 give EDIT three documents, A, B and C, as UXCEDIT has:

- Each document has its own banks, gap, cursor, view, selection, file name, line ends and
  changed flag. A record of them is kept for each document, and swapped in when the document
  shows.
- The clipboard, the find text, the settings and the recent files are shared.
- New, Open, Save and Save As work on the document on screen.
- F7 and Window, Next Document show the next document. Window, Document A, B and C show that one.
- The menu bar shows A, B and C at its right end. The letter on screen is lit. The letter of
  a document with changes is yellow.
- Exit asks to save each document with changes, in turn.
- A document never shown takes no bank.
- EDIT with a file name loads it into A.

RAM: about 130 bytes a document for the record, 390 bytes in all.

## The steps

The full suite runs first, as step 7 since the last one.

| Step | Part | Code | Tests |
|---|---|---|---|
| E1, done | The text in RAM banks, one document. A 40 KB file loads. | 836 bytes, then 63 for E1b's copy loop and key drop; the low part is about 15.6 KB | EDIT, EDIT2, EDITSET, and EDITBIG for the 40 KB file |
| E2 | The clipboard in its own bank, 8192 bytes | about 50 bytes | EDIT |
| E3 | Three documents: the records, the swap, F7 | about 400 bytes code, 390 bytes RAM | EDITWIN |
| E4 | The Window menu, the letters on the bar, Exit's questions | about 300 bytes in region 2 | EDITWIN |
| E5 | Ctrl+N, Ctrl+O, F2, F6, Select All, Delete Line, Shift+Delete, Ctrl+Insert, Shift+Insert | about 300 bytes | EDIT2 |
| E6 | Word moves, the first and the last line, Go to Line, the indent on Enter | about 500 bytes | EDIT2 |
| E7 | Undo and Redo: a ring in one bank of edits, each its position, length and bytes. The characters typed in a run are one edit. | about 1200 bytes, one bank | EDITUNDO |
| E8 | Find: Wrap Around and the selection as the find text. Change: Find and Verify asks Yes, No or Esc at each match. The last 6 find texts in a list. | about 800 bytes | EDIT2 |
| E9 | The status row: the line count, CR LF or LF, the tab stops. About: the banks of each document and the free banks. | about 300 bytes | EDIT |
| E10 | The scroll bar on the box's right edge | about 250 bytes | EDIT |

E1 and E3 change the most. E1 comes first, since the documents each need their own banks.

Open:

- EDIT's own help, for F1 and the Help menu.
- A line-number gutter and a lit cursor line, as UXCEDIT draws them, take 6 columns and a
  draw a row. They are not in the steps.
