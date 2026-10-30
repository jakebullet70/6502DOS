# XFMGR plan: an XTree-style file manager in UXCBASIC

This plan ports XFMGR2, a Prog8 program at `C:\dev\CmdrX16\dos_tools\XFMGR2` (build 197), to
UXCBASIC on 6502DOS. The port is a rewrite: Prog8's source and its KERNAL calls do not carry over.
Each step is one part, built and tested on its own, with a compact after it. Sizes are estimates
until the step is built. Asm is approved for this plan.

The program is `src/utils/xfmgr/XFMGR.UXB`. It compiles to `build/sys/XFMGR.COM`.

## What XFMGR2 does

A tree of folders on the left, the files of the selected folder on the right, and a two-row
command menu that changes while Ctrl or Alt is held. Files carry tags across folders. Showall,
Branch and Global fill the file window from many folders. Commands act on the highlighted file
or on every tagged file.

| Prog8 module | Size | Holds | In the port |
|---|---|---|---|
| `xfmgr.p8` | 34634, with the next three | the screen, the key loop, the file commands | `XFMGR.UXB` and its regions |
| `xarena.p8` | | a bump allocator over RAM banks | `XFMFILE.UXI` |
| `xtree.p8` | | the folder tree | `XFMTREE.UXI` |
| `xfiles.p8`, `xscan.p8` | | file records, the index, logging | `XFMFILE.UXI`, `XFMTREE.UXI` |
| `uiutil.ovl` | 6121 | dialogs, frames, the menu | `GUI.UXI` dialogs; the menu in `XFMGR.UXB` |
| `miscutil.ovl` | 5528 | wildcard rename, prune, history, copy, the Find crawl | `XFMOPS.UXI` |
| `tview.ovl` | 7251 | the text and hex viewer | `VIEW.COM`, by `exec` |
| `xsyntax.ovl` | 5473 | syntax colors, the viewer's footer | not taken |
| `ximgview.ovl` | 2111 | the BMX viewer | `BMXVIEW.COM`, by `exec` |
| `xmusic.ovl` | 2487 | the WAV player | `WAVPLAY.COM`, by `exec` |
| `zsmkit.bin` | 5380 | the ZSM engine | `ZSMPLAY.COM`, by `exec`, step X17 |
| `xfsetup.prg` | 5551 | the settings screen | a dialog in `XFMOPS.UXI` |
| `install.prg` | 5804 | the installer | not taken: `XFMGR.COM` is on the card |

## Not taken

- The PETSCII display of the viewer, `I`.
- The BASLOAD and Markdown syntax colors, `C` in the viewer.
- The split of Ctrl keys between the emulator and hardware, and the `Force hardware` setting.
  `RUN.BAT` passes `-noemucmdkeys`, so Ctrl keys reach the X16 in both.
- The KERNAL R49 check, the `/xt` launcher, `install.prg` and `xfsetup.prg`.
- X16 Edit. `E` runs the editor in `EDITOR$`, or `EDIT` when it is empty.
- The dates of a copy. A copy takes the current date, as `COPY` and `DOS.COPY` do, since the
  `filetime` call is not written.
- Browsing inside an archive.

## The screen

- 80 by 30, drawn with `VERA.UXI`. VIEW fixes the same size.
- Row 0 is the title: the path, the counts, the clock. Rows 28 and 29 are the menu.
- The tree takes columns 0 to 26. The file window takes columns 28 to 79. A row of it holds the
  tag mark, the name in up to 32 columns, the size in bytes, and the date. Showall and Branch
  widen it to columns 0 to 79, and add the time.
- Colors come from `GUI.THEME` and its `ENUM ROLE`. `THEMED.COM` edits a theme file.
- The disk's free space shows only in the About box. `DOS.DISKFREE` reads the whole FAT.

## The keys

As in XFMGR2, but for these. `KEYS.UXI` gives Ctrl+A to Ctrl+Z as 1 to 26, so some Ctrl keys are
other keys.

| Command | XFMGR2 | Here | Why |
|---|---|---|---|
| Invert tags | Ctrl-I | Ctrl-N | Ctrl-I is Tab, 9 |
| Move tagged | Ctrl-M | Ctrl-O | Ctrl-M is Enter, 13 |
| Find | Ctrl-F or Ctrl-N | Ctrl-F | Ctrl-N is Invert |
| Search tagged | Ctrl-S or Ctrl-E | Ctrl-S | |
| View tagged | Ctrl-V or Ctrl-L | Ctrl-V | |
| Delete tagged | Ctrl-D or Ctrl-X | Ctrl-D | |
| Settings | Alt-F10, by another program | Alt-F10, a dialog | |
| Execute | Alt-X quits, then runs | Alt-X runs, then returns | `exec` returns here |

- Ctrl-C is Copy tagged. The program calls `DOS.STOP_KEY(DOS.STOP.OFF)` at its start, so Ctrl-C
  is the key 3.
- Alt+letter gives an extended key, `KEYS.SCAN_ALT_T` and so on. `KEYS.SCAN_ALT_F1` + 2 is Alt-F3.
- `Alt` on the menu comes from `KEYMODS()`. `GETEXTKEY()` updates it with no key waiting, so the
  menu changes as the modifier is pressed and released.

## Memory

| Bank run | Banks | Holds |
|---|---|---|
| Regions 1 to 4 | 4 | `GUI.UXI` and `VERA.UXI`, whose slots are fixed |
| Regions 5 to 9 | 5 | XFMGR's cold code |
| Names | 1 | 254 folder names, 32 bytes each, zero-padded, at `$A000 + node * 32`: 8128 bytes |
| Folder extras | 1 | 254 records of 7 bytes: file count, first file's bank and offset, tag count; then the history |
| Index | 2 | 2048 rows of 8 bytes: bank, offset, owner folder, 4-byte sort key |
| Arena | the rest, from 1 | file records |

- A file record is the record's length, the 4-byte size, the date, the time, the attributes, the
  flags (the tag is bit 0), and the name with a zero after it: 12 bytes and the name.
- A name of 12 characters makes 24 bytes a record, so a bank holds 341. A length of 0 sends the
  walker to the next bank.
- The bank run is taken with `BANK.ALLOC`. A folder's records never move, and a release frees
  nothing until the whole arena is reset, as in XFMGR2.
- The sort key is the first 4 characters of the name, case folded, or of the extension; or the
  size or the date and time, high byte first.
- The tree stays in low RAM: 5 arrays of 254 bytes, 1270 bytes.
- Code that selects a bank lives in low RAM. `#REGION_SLOT` code gets RAM BANK WRITE IN A REGION.
- x16emu has 62 free banks at boot. XFMGR takes 13 and an `exec` save up to 5, which leaves about
  43 for the arena: about 14000 files.

Estimated use of low RAM, 38655 bytes from `$0801` to `$9EFF`:

| Part | Bytes |
|---|---|
| The runtime, and the loader and gates of 9 regions | 3800 |
| `DOS.UXI`, `GUI.UXI` low-RAM parts | 3500 |
| The tree's arrays, paths, buffers | 3000 |
| The key loop, row drawing, bank accessors | 7000 |
| Free | about 21000 |

The file comes to about 55 KB: 18 KB of low RAM and 37 KB of regions. XFMGR2's seven binaries
come to 63 KB. A program that passes `$9EFF` reads the rest with `exec_rest` at its start.

## Tests

- A test is `tests/XFMn.UXB`, which calls `DOS.EXEC("C:\SYS\XFMGR.COM", "-K")` and then prints
  screen cells with `VERA.GET_CELL`. `-K` leaves the screen as it is when the program ends. It is
  a one-line switch in `XFMGR.UXB`, and the help does not list it.
- `tests/XFMn.IN` types the keys. The child reads them through the console. `\XE0\X13` is Alt+R.
- `tests/XFMn.PY` defines `card(image)` for the files and `check(image)` for what a command left
  on the card. No golden holds a card listing.
- The runner stops at 5 s. XFMGR's load counts: one scenario a test.
- Only the test of the step runs, then the tests of the code touched. Standing orders cover the
  full suite.

## Steps

Bytes are code added, estimated, then RAM. Each step lists the region its code goes in.

### X1. The frame (2500 B, low RAM)

`XFMGR.UXB`: the switches, `STOP_KEY`, the banks, the theme, the frame, the title, the clock
polled by ticks, the menu's three states, Q, F1 (`HELP XFMGR` by `exec`), `-K`. Test XFM1: Q at
once, the title and the menu cells.

### X2. The tree (2500 B low RAM, 1500 B region 5, 1270 B arrays)

`XFMTREE.UXI`: the node pool, the names bank, logging one folder with `FINDFIRST`, the tree
anchored at `C:\`, the launch folder selected at the start with its parents logged and expanded,
Up, Down, PgUp, PgDn, Enter, +, -, Left. Test XFM2: a card with nested folders; open, close, move.

### X3. The files (3000 B low RAM, 1500 B region 6)

`XFMFILE.UXI`: the arena, the file log, the index, the file window, Tab, Right, the row format.
The sort is a shell sort on the 8-byte rows. Test XFM3: a folder of 300 files, PgDn, last row.
Time 2048 rows at the end of this step. If it passes 2 s, write the compare in `ASM`.

### X4. Sort and filespec (800 B, region 6)

Alt-S cycles name, extension, size, date; the sort runs when Alt is released. F sets the
filespec, matched as `findfirst` matches. Test XFM4.

### X5. Tags (800 B, region 6)

T, U, Ctrl-T, Ctrl-U, Ctrl-N, Ctrl-W, Alt-T, Alt-U, and the counts in the title. Tags live in the
file record. Test XFM5.

### X6. Scopes (1200 B, region 6)

S, B, G and Esc: the index fills from the walk of the tree's logged folders, the row's owner folder
gives the path, and the path line follows the highlighted row. G shares S's handler. Alt-R, Alt-F3,
Alt-J. Test XFM6: S, a tag in another folder, Esc, Alt-U.

### X7. Delete, rename, mkdir (2000 B, region 7)

File window D and R, with `*` and `?` in the new name. Tree window D (empty folders), R and M.
Dialogs are `GUI.YESNO`, `GUI.MSGBOX` and `GUI.INPUTBOX`. Test XFM7, `check(image)`.

### X8. Copy and move (2500 B, region 7)

C, M, Ctrl-C, Ctrl-O, Ctrl-D. The copy reads and writes 8 KB at a time through a bank, in place
of `DOS.COPY`'s 256 bytes. Move is `DOS.RENAME`: a file moves on the same drive in one call. A
destination that does not exist is made and added to the tree. A name that exists asks Yes, No,
All or Skip all. Test XFM8, `check(image)`, and XFM8B for the collisions.

### X9. History and the folder picker (1500 B, region 8)

The prompt becomes a form of one `INPUT2` field, so Up opens the history and F2 the tree picker.
INPUTBOX gives no way to take them. Check first that `INPUT2`'s ending key reports them; if not,
add that to `GUI.UXI`. A ring of 8 entries per prompt lives in the extras bank, saved to
`C:\XFMGR.HIS`. Test XFM9.

### X10. Prune (700 B, region 8)

Alt-P, with the word `prune` typed to confirm. Root refused. Deepest folder first; a counter on
the menu row. Reuses the walk of `XCOPY.UXB` or `TREE.UXB`. Test XFM10, `check(image)`.

### X11. Find (1000 B, region 8)

Ctrl-F crawls from the root, logs the folders with a match, and shows the hits with `GUI.LISTBOX`;
Enter jumps to the file. Test XFM11.

### X12. Search tagged (600 B, region 8)

Ctrl-S scans each tagged file, 1 KB at a time, in any case, across a block's edge, and untags the
files without the text. The bar walks the files and the count falls as it goes. Test XFM12.

### X13. The children (1000 B, region 9)

V runs `VIEW`. E runs `EDITOR$`, else `EDIT`. Alt-X runs the highlighted `.COM`, with a tail from
a prompt, from its folder, then returns. Each repaints the whole screen after. Trap: `exec`'s
fifth level gives error 8: the message comes from `DOS.ERRMSG`. Alt-Q leaves the shell in the
selected folder; Q changes back to the launch folder first. Test XFM13.

### X14. View tagged (VIEW.COM +600 B, XFMGR 500 B region 9)

VIEW gains `-S text`, which opens on the first match, and `-W n/m`, which shows the count and makes
+, -, and N past the last match end with exit codes 10 (next) and 11 (previous). Ctrl-V walks the
tagged files with them. VIEW gains H, a hex page (+900 B). Tests VIEW, XFM14.

### X15. Settings and help (600 B, region 9)

Alt-F10 picks the theme and the sort, saved in `[XFMGR]` of `C:\6502DOS.INI` with `INI.UXI`. A
is the About box: version, free banks, disk free. `HELP.HLP` gains the topic `XFMGR`. PLAN gets
the row, and `README.md`. Test XFM15.

### X16. BMX and WAV

- `src/utils/bmxview/BMXVIEW.COM`: reads a BMX file, sets the bitmap mode, waits for a key, and
  puts the console's mode, font and palette back. About 1500 B. V picks it for `.bmx`.
- `src/utils/wavplay/WAVPLAY.COM`: PCM 8 or 16 bits, mono or stereo, up to 48 kHz. It polls AFLOW,
  so it needs no IRQ. Inline `ASM` moves the bytes from a buffer to `$9F3D`. About 2000 B. P picks it
  for `.wav`.
- Tests: BMXVIEW by a cell or VRAM read after, WAVPLAY by an exit code on a short file.

### X17. ZSM

- First, an audit of `ZSMKIT-A000.BIN`, release 2.8: which KERNAL calls it makes when a song is in
  memory. 6502DOS has no KERNAL calls. The step stops if zsmkit needs any.
- Trap: zsmkit's scratch is at `$0400`. 6502DOS holds `reg_get`'s variables at `$0400–$056A`.
- It needs the IRQ hook: `setvect`, call 32, is not written. Asm in `src/asm`, about 60 B of ROM.
- `ZSMPLAY.COM`: loads a song into banks, runs the tick, Space pauses, Esc ends.

## Traps

- `VERA.UXI` runs from region 3 and `GUI.UXI` from 1 to 4. XFMGR's slots start at 5.
- A child can leave the screen in another state. XFMGR repaints from its own records, and keeps
  none of the screen.
- `exec` keeps banks of the running program. RAM written past `PSP_TOP` by `POKE` is lost.
- `rename` does not check for open handles. A folder moved to another folder gives error 5, so
  Move takes files only.
- A name over 32 characters shows as its alias.
- A `.CMD` is not a program: Alt-X takes `.COM` only.

## Order and budget

| Steps | Adds to the file | Low RAM left, estimated |
|---|---|---|
| X1 to X3 | 11 KB and the GUI's 14 KB | 25 KB |
| X4 to X6 | 3 KB | 24 KB |
| X7 to X9 | 6 KB | 23 KB |
| X10 to X13 | 3 KB | 22 KB |
| X14 to X15 | 1 KB | 21 KB |
| X16, X17 | other programs | |
