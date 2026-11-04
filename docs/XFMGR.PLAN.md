# XT plan: an XTree-style file manager in UXCBASIC

This plan ports XFMGR2, a Prog8 program at `C:\dev\CmdrX16\dos_tools\XFMGR2` (build 197), to
UXCBASIC on 6502DOS. The port is a rewrite: Prog8's source and its KERNAL calls do not carry over.
Sizes are estimates until the step is built. Asm is approved for this plan.

The program is `src/utils/xt/XT.UXB`. It compiles to `card/sys/XT.COM`.

Each step is one part and follows the working rule at the top of `docs/HANDOFF.md`: the edit, a
build on the user's word, the user's run on the emulator, a commit on the user's word, a compact.
A step adds no test unless the user asks.

## What XFMGR2 does

A tree of folders on the left, the files of the selected folder on the right, and a two-row
command menu that changes while Ctrl or Alt is held. Files carry tags across folders. Showall,
Branch and Global fill the file window from many folders. Commands act on the highlighted file
or on every tagged file.

| Prog8 module | Size | Holds | In the port |
|---|---|---|---|
| `xfmgr.p8` | 34634, with the next three | the screen, the key loop, the file commands | `XT.UXB` and its regions |
| `xarena.p8` | | a bump allocator over RAM banks | `XTFILE.UXI` |
| `xtree.p8` | | the folder tree | `XTTREE.UXI` |
| `xfiles.p8`, `xscan.p8` | | file records, the index, logging | `XTFILE.UXI`, `XTTREE.UXI` |
| `uiutil.ovl` | 6121 | dialogs, frames, the menu | the prompts and the menu in `XT.UXB` |
| `miscutil.ovl` | 5528 | wildcard rename, prune, history, copy, the Find crawl | `XTOPS.UXI`, `XTHIST.UXI`, `XTFIND.UXI` |
| `tview.ovl` | 7251 | the text and hex viewer | the shell command `VIEW` |
| `xsyntax.ovl` | 5473 | syntax colors, the viewer's footer | not taken |
| `ximgview.ovl` | 2111 | the BMX viewer | not taken |
| `xmusic.ovl` | 2487 | the WAV player | not taken |
| `zsmkit.bin` | 5380 | the ZSM engine | not taken |
| `xfsetup.prg` | 5551 | the settings screen | Alt-F10 on the menu's rows, in `XTSET.UXI` |
| `install.prg` | 5804 | the installer | not taken: `XT.COM` is on the card |

## Not taken

- BMX pictures, WAV playback and ZSM playback.
- The PETSCII display of the viewer, `I`, and its hex page.
- The BASLOAD and Markdown syntax colors, `C` in the viewer.
- The split of Ctrl keys between the emulator and hardware, and the `Force hardware` setting.
  `RUNHOST.BAT` and `RUNCARD.BAT` pass `-noemucmdkeys`, so Ctrl keys reach the X16 in both.
- The KERNAL R49 check, the `/xt` launcher, `install.prg` and `xfsetup.prg`.
- X16 Edit. `E` runs the shell command `EDIT`.
- The dates of a copy. A copy takes the current date, as `COPY` and `DOS.COPY` do, since the
  `filetime` call is not written.
- Browsing inside an archive.
- The clock in the title, and the setting that clears the history.

## The screen

- 80 by 30, drawn with `VERA.UXI`. VIEW fixes the same size.
- Row 0 is the title: the path and the counts. Rows 28 and 29 are the menu, and the prompts.
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
| Find | Ctrl-F or Ctrl-N | Ctrl-F or Ctrl-G | Ctrl-N is Invert |
| Search tagged | Ctrl-S or Ctrl-E | Ctrl-S or Ctrl-E | |
| View tagged | Ctrl-V or Ctrl-L | Ctrl-V | |
| Delete tagged | Ctrl-D or Ctrl-X | Ctrl-D or Ctrl-X | |
| Settings | Alt-F10, by another program | Alt-F10, on the menu's rows | |
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
| Regions 5 to 9 | 5 | XT's cold code |
| Names | 1 | 254 folder names, 32 bytes each, zero-padded, at `$A000 + node * 32`: 8128 bytes |
| Folder extras | 1 | 254 records of 7 bytes: file count, first file's bank and offset, tag count; then the open prompt's history, 512 bytes |
| Index | 2 | 2048 rows of 8 bytes: bank, offset, owner folder, 4-byte sort key |
| Copy | 1 | `COPY_BANK`: the 8 KB of a copy, and the 1 KB blocks of Search tagged |
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
- x16emu has 62 free banks at boot. XT takes 14 and an `exec` save up to 5, which leaves about 43
  for the arena: about 14000 files.

Estimated use of low RAM, 38655 bytes from `$0801` to `$9EFF`:

| Part | Bytes |
|---|---|
| The runtime, and the loader and gates of 9 regions | 3800 |
| `DOS.UXI`, `GUI.UXI` low-RAM parts | 3500 |
| The tree's arrays, paths, buffers | 3000 |
| The key loop, row drawing, bank accessors | 7000 |
| Free | about 21000 |

`XT.COM` is 44856 bytes. It passes `$9EFF`, so its start reads the rest with `exec_rest`.

## Steps

Bytes are code added, estimated, then RAM. Each step lists the region its code goes in.

### X1. The frame (2500 B, low RAM)

`XT.UXB`: the switches, `STOP_KEY`, the banks, the theme, the frame, the title, the menu's three
states, Q, F1 (`VIEW` on `XT.HLP` by `exec`).

### X2. The tree (2500 B low RAM, 1500 B region 5, 1270 B arrays)

`XTTREE.UXI`: the node pool, the names bank, logging one folder with `FINDFIRST`, the tree
anchored at `C:\`, the launch folder selected at the start with its parents logged and expanded,
Up, Down, PgUp, PgDn, Enter, +, -, Left.

### X3. The files (3000 B low RAM, 1500 B region 6)

`XTFILE.UXI`: the arena, the file log, the index, the file window, Tab, Right, the row format.
The sort is a shell sort on the 8-byte rows. A sort of 2048 rows past 2 s gets its compare in
`ASM`.

### X4. Sort and filespec (800 B, region 6)

Alt-S cycles name, extension, size, date; the sort runs when Alt is released. F sets the
filespec, matched as `findfirst` matches.

### X5. Tags (800 B, region 6)

T, U, Ctrl-T, Ctrl-U, Ctrl-N, Ctrl-W, Alt-T, Alt-U, and the counts in the title. Tags live in the
file record.

### X6. Scopes (1200 B, region 6)

S, B, G and Esc: the index fills from the walk of the tree's logged folders, the row's owner folder
gives the path, and the path line follows the highlighted row. G shares S's handler. Alt-R, Alt-F3,
Alt-J.

### X7. Delete, rename, mkdir (2000 B, region 7)

File window D and R, with `*` and `?` in the new name. Tree window D (empty folders), R and M.
The prompts are on rows 28 and 29: `ASK_TEXT`, `ASK_YES` and `TELL` in `XT.UXB`. D and R on the
root, and the tree's D on a folder that is not logged, give a message.

### X8. Copy and move (2500 B, region 7)

C, M, Ctrl-C, Ctrl-O, and Ctrl-D or Ctrl-X. The copy reads and writes 8 KB at a time through
`COPY_BANK`, in place of `DOS.COPY`'s 256 bytes. Move is `DOS.RENAME`: a file moves on the same drive in one call. A
destination that does not exist is made and added to the tree. A name that exists asks Yes, No,
All or Skip all.

### X9. History and the folder picker (1500 B, region 8)

The prompt's field is `GUI.INPUT2`, whose ending key gives Up for the history and F2 for the tree
picker. `ASK_TEXT` returns an `ASK_END`. Each prompt keeps its last 8 answers in
`C:\sys\xt\NAME.HIS`, newest first. The prompt reads its file into the one ring in the extras
bank. An answer over 64 characters is not kept.

### X10. Prune (700 B, region 8)

Alt-P, with the word `prune` typed to confirm. The root, and a branch that holds C:'s current
directory, are refused. Deepest folder first; the counts on the menu's rows. `GO_PATH` is the
walk's only state.

### X11. Find (1000 B, region 8)

Ctrl-F or Ctrl-G asks for a filespec, crawls from the root, logs the folders with a match, and
shows the hits in the whole-screen file window; Enter jumps to the file. Esc stops the crawl.

### X12. Search tagged (600 B, region 8)

Ctrl-S or Ctrl-E scans each tagged file, 1 KB at a time, with A to Z folded, across a block's
edge, and untags the files without the text. Esc stops the scan. The bar walks the files and the count falls as it goes.

### X13. The children (1000 B, region 9)

V runs `VIEW.COM` and E runs `EDIT.COM`, from `DOS.PROGRAM_FOLDER()`, with the highlighted file as
the tail. XT does not change either. Alt-X runs the highlighted `.COM`, with a tail from a prompt,
from its folder, waits for a key, then returns. Each repaints the whole screen after. Trap: `exec`'s fifth level
gives error 8: the message comes from `DOS.ERRMSG`. Alt-Q leaves the shell in the selected folder.
XT brings back C:'s folder and the current drive after each child, so Q leaves in the launch
folder.

### X14. View tagged (200 B, region 9)

Ctrl-V runs `VIEW.COM` on each tagged file in turn. Q or Esc in VIEW goes to the next file. VIEW's
exit code is 0 for both, so the walk does not stop early. An `exec` error or another exit code
stops it.

### X15. Settings and help (600 B, region 9)

Alt-F10, on the menu's rows: T picks the next `.GTH` of `C:\sys\themes`, S the next sort, Enter
saves both in `[XT]` of `C:\6502DOS.INI` with `INI.UXI`, and Esc brings back the old ones. A
shows the DOS version, the free banks and the free KB. `HELP.HLP` gains the topic `XT`. PLAN gets the row, and
`README.md`.

## Traps

- `VERA.UXI` runs from region 3 and `GUI.UXI` from 1 to 4. XT's slots start at 5.
- A child can leave the screen in another state. XT repaints from its own records, and keeps none
  of the screen.
- `exec` keeps banks of the running program. RAM written past `PSP_TOP` by `POKE` is lost.
- `rename` does not check for open handles. A folder moved to another folder gives error 5, so
  Move takes files only.
- A name over 32 characters shows as its alias.
- A `.CMD` is not a program: Alt-X takes `.COM` only.
- `VIEW.COM` and `EDIT.COM` read their file from `P1$`, which only the shell sets. XT sets `P1$`
  before each `exec`.

## Order and budget

| Steps | Adds to the file | Low RAM left, estimated |
|---|---|---|
| X1 to X3 | 11 KB and the GUI's 14 KB | 25 KB |
| X4 to X6 | 3 KB | 24 KB |
| X7 to X9 | 6 KB | 23 KB |
| X10 to X13 | 3 KB | 22 KB |
| X14 to X15 | 1 KB | 21 KB |
