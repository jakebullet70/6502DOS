# Handoff

## State

- The golden outputs `tests/*.OUT`, `UXCBASIC/tests/*.OUT` and `MSBASIC/tests/*.out` are
  gitignored and stay local (1d306c9). The test sources in those folders are tracked. Goldens
  change on disk only.
- MSBASIC moved in (2026-10-19). `C:\dev\BASIC-M6502` was copied at its commit 52ae025, not
  changed; the user retires it.
  - `MSBASIC/` holds the tracked files and its own `CLAUDE.md`. The old repo's memory notes
    are folded into that `CLAUDE.md`. Its `.gitignore` is gone; the root one ignores
    `MSBASIC/ref/`, `MSBASIC/docs/x16/` and `MSBASIC/docs/x16-basic-compare.md`. Those are
    copied in and stay local.
  - `make all` in `MSBASIC/`: 1099 ms, the baseline. `make verify` matches. `make test` not run.
  - Committed by the user (295e2df).
- UXCBASIC moved in (2026-10-17). `C:\dev\UXCBASIC` was copied, not changed; the user
  retires it, then puts this folder in git.
  - `UXCBASIC/` holds pyuxc (`pyuxc/`), the templates (`tpl/`), the help (`help/`), the
    tests (`tests/`, `tests.py`), `samples/` (the old `samples/` and `examples/`), `docs/`
    and its own `CLAUDE.md`. `RUNUXCTESTS.BAT` runs its tests; they write `build/uxctests/`.
  - `attic/gpc/` holds the GPC UXC (`src/`), `tools/gpc`, `tools/prof`, the GPC build and run
    scripts, `pyuxc/golden.py`, `compare.py`, `golden/`, `cases/`, `disk/` and the old
    `CLAUDE.md` as `NOTES.md`. Its `README.md` lists them. Nothing uses the attic.
  - `tools/64tass` holds 64tass 1.60 and its licences. `tpl/MKTPL.PY` uses it and no longer
    has `--test`, which ran a stock-ROM program. Its tables are byte-identical to the old ones,
    1.36 s. The tables `UXC.TPL.BIN`, `UXC.TPL.IDS` and `UXDOS/UXC.TPL.BIN` are kept in the
    repo; `.gitignore` drops the listings and `UXC.TPL.BL`.
  - `tools/build.py` runs MKTPL when a template is newer than `tpl/UXDOS/UXC.TPL.BIN`.
    `tools/uxb.py` and `UXCBASIC/tests.py` find pyuxc, the table and the ROM from the repo.
  - `.claude/agents/doc-style.md` is the doc-style agent. Root `.gitignore` and
    `.gitattributes` are new.
  - Build 1.95 s with all ten programs recompiled by the new pyuxc, the new baseline. The
    ROM, `TEST.ROM` and every COM and CBI are byte-identical to the build before the move.
    UXCBASIC suite, run on the user's word: 175 tests, 0 failed, 45.7 s, the longest
    `ONCASE` 0.8 s.
  - `dump.bin` is gone from the root. `tools/64tass/SOURCE.md` names where the source of the
    GPL-2 exe (V1.60.3243) is.
  - Every script finds its paths from its own location, so renaming the base folder breaks no
    build or test. The `.LST` files hold absolute paths; they are ignored and rebuilt.
- pyuxc leaves out unused global variables (UXCBASIC HANDOFF, S3).
- `EXIST.UXB` (2026-10-16): the user's header tweak, and comments on how the shell calls it, where
  the arguments and the result go, and that the shell does not read the `END` exit code.
  `EXIST.CBI` 1578 bytes. Build 711 ms (`EXIST` 0.1 s, the ROM 0.57 s), the new baseline.
  Tests: `CMDLETS` 0.7 s, `DIRS` 0.8, `DISK` 0.4, all ok with no golden change.
- System strings (2026-10-16): `HEAP.UXI`'s `SYSTEM_STRINGS` is now `SYS_STRINGS_BASE`, which
  ends the clash with the asm count `SYSTEM_STRINGS = 32`. New in `HEAP.UXI`:
  `SYS_STRINGS_GET(SLOT)` and `SYS_STRINGS_SET(SLOT, TEXT)`, slot 0 to 31, which set `PSP_HEAP`
  to VARBANK for the call and restore it. `STR_GET` and `STR_SET` use the bank in `PSP_HEAP`, so
  they miss the system strings after a `STR_HEAP` to another bank. pyuxc names: 16 characters a
  part at most.
  - `EXIST` uses the new subs: 1578 to 1735 bytes. The get costs 86, the set 117, both 157; the
    `PSP_HEAP` switch is 34 of it. The shell: 17723, no change. `SLOTKID` keeps the descriptors.
  - Build 943 ms (the shell 0.3 s, `EXIST` 0.1, the ROM 0.82), the new baseline. Tests:
    `CMDLETS` 0.7 s, `SHRUN` 0.7, ok.
  - `EXIST` keeps the new subs, with `CONST SLOT_P1 AS UBYTE = 0` and `SLOT_P2 = 1`: 1735 bytes.
    `STRING * 128` costs no bytes on the card. Build 727 ms, the new baseline. `CMDLETS` 0.7 s ok.
  - Long names: PLAN §5 sets 32 characters a name; §13 leaves when open. No step in §11.
  - `EXIST`'s `FILENAME_2_CHK` is `STRING * 255`, the longest path: 1733 bytes. Build 803 ms,
    the new baseline. `CMDLETS` 0.7 s ok.
- Shell comments (2026-10-16): a line that starts with `REM`, `'` or `//` does nothing, in a
  skipped block too. `RUN_LINE` checks before `READ_NAME`, so a `|` or `TO` in a comment is
  never read. A comment may follow an `IF` condition: `IF A = 1 ' NOTE`. Other statements take
  no comment after them. `REMARK` is a command name, not a comment.
  - The shell: 17723 to 17799 bytes (+76). RAM: none.
  - Build 1103 ms (the shell 0.3 s, the ROM 0.97), the new baseline. `SHIF` 0.4 s ok; its golden
    and `tests/sd/SCRIPTS/IF.CMD` gained comment lines.
- Docs step after the comments (2026-10-16); no docs are owed. PLAN §3 String heaps:
  `SYS_STRINGS_GET`/`SET` and the `STR_GET` trap. §8: comments, `CD`, the `.CBI` trap, the
  Commandlets list, `\DOS`, `EXIST`. §11: 7i split into 7i1 to 7i5. No build, no test.
  - Byte saving seen, not applied: `FIND_IN` in the shell asks for `".CBIN"`; `".CBI"` finds the
    same file and saves 1 byte.
- 7i2 `DISKFREE` (2026-10-16): `src/cbin/DISKFREE.UXB`, `DISKFREE [d:]`. It prints
  `885 KB free`, free clusters times sectors per cluster over 2, in a `ULONG`. The colon is
  optional and a small letter is the same as a capital. A first character that is not a letter,
  a second that is not `:`, a longer name, or a drive the kernel refuses prints `Invalid drive`
  and gives exit code 1.
  - `DISKFREE.CBI` 1861 bytes on the card. ROM, shell and RAM: none.
  - Build 632 ms (`DISKFREE` 0.1 s, the ROM 0.50), the new baseline. `CMDLETS` 0.7 s ok; its
    `.IN` and golden gained six `DISKFREE` lines.
  - Full suite after it: 28 tests, 14.5 s. `DISK` and `FILES` failed on stale goldens, both
    rewritten and then ok at 0.4 s. `DISK`: the find buffer's folder cluster at offset 13 went
    from $3E to $40, since `DISKFREE.CBI` takes 2 clusters. `FILES`: `CMDSHELL.COM` 17799 (the
    comments step) and `SLOTKID.COM` 1155 (the system strings step).
  - Trap: a failed run of `tests.py` prints the output cut short, so a cut does not mean a crash.
    Rerun with `--update` and diff the golden to see all of it.
- 7i2b `CBIN.UXI` and `DISKFREE SILENT` (2026-10-16): `src/cbin/CBIN.UXI` holds `SLOT_P1` to
  `SLOT_P9` (0 to 8) and `DIM SILENT AS UBYTE`. Include it after `DOS.UXI` and `HEAP.UXI`.
  `EXIST` and `DISKFREE` use it. `DISKFREE [d:] [SILENT]` sets P1$ to the free KB, `884`, and
  to an empty string on an invalid drive. `SILENT` is P1$ with no drive, else P2$. A SUB
  `INVALID_DRIVE` clears P1$, prints unless `SILENT`, and ends with code 1.
  - `tools/uxb.py` `includes()` now looks in the source's folder, then `src/bas`, as `#INCLUDE`
    does, so a change to `CBIN.UXI` recompiles the commandlets.
  - `DISKFREE.CBI` 1861 to 2353 bytes (+492). `EXIST.CBI` 1733, unchanged. RAM +11
    (`FREE_TEXT`). ROM and shell: none.
  - Build 783 ms (2 compiles), the new baseline. `DISKFREE.CBI` now takes 3 clusters, so the card
    has 884 KB free. Goldens rewritten and diffed: `CMDLETS` (885 to 884, 15 new lines) ok 0.9 s,
    `DISK` ($130D $40 to $41) ok 0.5 s, `DIRS` (each free count -1) ok 0.7 s.
  - User: running a commandlet needs `PATH$ = "C:\DOS"`; the shell's default stays empty for now.
- 7i3 `DISKINFO` (2026-10-16): `src/cbin/DISKINFO.UXB`, `DISKINFO [d:] [SILENT]`, CHKDSK style
  (the user's choice). Five lines: KB total, KB free, bytes a cluster, clusters, clusters free,
  each number right-aligned in 9 columns. P1$ to P5$ get the five numbers; P1$ is empty on an
  invalid drive. Drive parsing and `SILENT` as in `DISKFREE`. KB is figured from sectors, so
  a card past 4 GB does not overflow the `ULONG`.
  - A FUNCTION gives its value with `RETURN value`; assigning to the FUNCTION's name is an
    error (`NOT A VARIABLE`).
  - `DISKINFO.CBI` 3262 bytes, 4 clusters. ROM and shell: none. RAM: the three `ULONG`s (12),
    the SUB's `STRING * 10` (11).
  - Build 761 ms, the new baseline. The card has 880 KB free. Goldens rewritten and diffed:
    `CMDLETS` (884 to 880, 13 new lines) ok 1.0 s, `DISK` ($130D $41 to $45) ok 0.4 s, `DIRS`
    (each free count -4) ok 0.8 s.
- 7i5 `HELP` (2026-10-16): `src/dos/HELP.UXB`, a DOS utility `HELP.COM` in the card's `\DOS`,
  not a commandlet (the user), `HELP [topic]`, and its text `src/dos/HELP.TXT`.
  - `src/dos` holds the DOS utilities (the user). `build.py` compiles each `src/dos/NAME.UXB` to
    `build/DOS/NAME.COM` and copies each `src/dos/NAME.TXT` to `build/DOS`.
  - The user's choices: topics, the fixed path `C:\DOS\HELP.TXT`, no paging.
  - In `HELP.TXT` a line `:NAME` starts a topic, in capitals; its text runs to the next `:` line.
    `HELP` lists the names on one line. `HELP dir` upper-cases the topic and prints its lines.
  - `No help for TOPIC`, exit code 1. No `HELP.TXT`: `File not found`, exit code 2. Exit 0
    otherwise. A line past 80 characters is cut (`LINPUT` into `STRING * 80`).
  - `HELP.TXT` has the topics `HELP`, `EXIST`, `DISKFREE`, `DISKINFO`. No shell command has a
    topic yet.
  - `HELP.UXB` defines `SLOT_P1` itself: `#INCLUDE` looks in the source's folder, then `src/bas`,
    so `src/dos` does not see `CBIN.UXI`.
  - `HELP.COM` 1718 bytes, `HELP.TXT` 721. ROM and shell: none. RAM: three `STRING * 80` (246),
    a `UWORD` and three `UBYTE`s.
  - Build 716 ms, the new baseline. The card has 877 KB free. Goldens rewritten and diffed:
    `CMDLETS` (880 to 877, `HELP` lines) ok 1.1 s, `DIRS` (each free count -3) ok 0.8 s, `DISK`
    ($130D $45 to $48) ok 0.4 s. `FILES` ok 0.4 s.
  - Moved to `src/dos`: build 672 ms. `CMDLETS` ok 1.3 s, `DIRS` ok 0.8 s, `DISK` ok 0.4 s. No
    golden changed.
  - `HELP.TXT` rewritten (the user asked): the `HELP` topic says `DISKFREE` and `DISKINFO` work
    at the prompt and in a script, `EXIST` is for scripts, each puts its result in `P1$`,
    `SILENT` prints nothing, not even an error, and an error empties `P1$`. `DISKFREE` and
    `DISKINFO` show one line for the prompt and two for a script. `EXIST` shows a script with
    one file name and says wildcards are not allowed. `DISKINFO` lists `P1$` to `P5$`.
    No line passes 80 characters.
  - The user's rule: `EXIST` is script only and takes one file, no wildcard. `EXIST` does not
    check for `*` or `?` (the user, 2026-10-17): a wildcard check cost 235 bytes and was
    taken out. `EXIST.CBI` 1439 bytes. Build 677 ms. `CMDLETS` ok 1.3 s.
  - `PROMPT$` `$` codes (2026-10-17). `PRINT_PROMPT` in `CMDSHELL.UXB` prints the prompt.
    `$P` the drive and directory, `$N` the drive, `$G` `>`, `$L` `<`, `$B` `|`, `$Q` `=`, `$_`
    a new line, `$$` `$`. The letter is either case (`OR 32`). A `$` before another character
    prints nothing. Empty `PROMPT$` prints the drive and `>`. The text is copied to
    `LEFT_TEXT` first and read with `ContentsAt`.
    - `CMDSHELL.COM` 17799 to 18108 bytes (+309), no RAM beyond 3 local bytes. A form where
      each case sets the character and one `PRINT CHR$` follows cost 18125, so it was dropped.
    - Build 954 ms (the shell 0.3 s, the ROM 0.81), the new baseline.
    - `SHVARS.IN` adds `PROMPT$ = "$p$G"` (prompt `C:\>`) and
      `PROMPT$ = "[$N$Q$L$B$$$X]$_$P$g"` (prompt `[C=<|$]`, a new line, `C:\>`). Golden
      rewritten and diffed (3 lines added, 1 changed). `SHVARS` ok 0.6 s, `SHELL` ok 0.4 s.
  - Short names (2026-10-17): `CASE "RENAME", "REN"` and `CASE "VERSION", "VER"` in the shell
    dispatch. `CMDSHELL.COM` 18108 to 18164 bytes (+56, 28 a name). Build 953 ms, the new
    baseline. `SHELL` ok 0.6 s, `SHFILES` ok 0.6 s.
  - Short names, part 2 (2026-10-17): `DEL`, `MD` and `RD` added to the `DO_ONE_PATH` case,
    which picks the command by the first letter. `CMDSHELL.COM` 18164 to 18326 bytes (+162, 54
    a name, against 28 a name for `REN` and `VER`; cause not looked at). Build 902 ms, the new
    baseline. `SHELL.IN` has a `VER` line. `SHFILES.IN` uses `MD`, `REN`, `DEL` and `RD`.
    `HELP.TXT` has topics `CHDIR`, `DELETE`, `MKDIR`, `RMDIR`, `RENAME` and `VERSION`, each
    followed by a one-line topic for its short name, such as `:REN` with `REN is short for
    RENAME`. `HELP.COM` ends a topic at the next `:` line, so two `:` lines in a row do not
    share one text. `HELP.TXT` "Commanmd" typo fixed. `CMDLETS.OUT` updated: the topic list,
    the `DISKFREE` marker, and free space 876 to 875 KB, since `HELP.TXT` takes one more
    cluster. `SHELL` ok 0.6 s, `SHFILES` ok 0.6 s, `CMDLETS` ok 1.3 s.
  - Boot shell (2026-10-17): `boot.s` runs `C:\CMDSHELL.COM` after the banner, with an empty
    tail (r1 points at the banner's 0). When the shell ends, `boot.s` runs it again. When
    `exec` fails, such as with no `C:\CMDSHELL.COM`, the ROM goes to the monitor and prints
    nothing. A BRK still goes to the monitor. This stands in for `SYSINIT.COM` (PLAN step 8).
    - The byte `boot_shell` (exported, `$C09C` now) is 1 in `build/6502DOS.ROM`. `build.py`
      copies the ROM to `build/TEST.ROM` with `boot_shell` 0, found through the label file;
      `TEST.ROM` boots to the monitor. `tests.py` boots `TEST.ROM`, except for the tests in
      `SHELL_ROM_TESTS`, which boot `6502DOS.ROM`. No golden file changed.
    - Trap: ca65 takes no string in an `=` constant; `SHELL_PATH` is a `.define`.
    - ROM +43 bytes: 26 of code, the flag, and the 16-byte path. `boot.o` CODE 173 bytes. ROM
      bank 0: 5536 bytes free below `$FFCF`. RAM: 0.
    - UXCBASIC's `tests.py` boots `6502DOS.ROM`; its card has no `CMDSHELL.COM`, so it gets the
      monitor. UXCBASIC `ARRAY1` ok 0.5 s.
    - New test `SHBOOT`: `VER`, `END`, `VER`; the second `C>` is the shell run again. Build
      548 ms, the new baseline. `BOOT` ok 0.5 s, `SHBOOT` ok 0.4 s, `SHELL` ok 0.4 s.
    - Docs owed: PLAN section 11 step 8 and section 13 (boot).
  - Console color (2026-10-17): call 46 `con_colour`, entry `$03CA`. Carry set returns the
    color in A; carry clear sets it from A. High nibble background, low nibble foreground.
    `console.s` keeps it in zp `con_colour`; `con_init` sets it to `CON_COLOUR` ($05, green on
    black). `put` and `blank` write it, so FF and a scroll blank in the current color.
    - `cursor_flip` swaps the nibbles of its cell's color (asl, adc #$80, rol twice) instead
      of an eor with a fixed mask; `CURSOR_COLOUR` is gone. A cell whose nibbles match shows
      no cursor.
    - ROM +22 bytes; bank 0: 5514 bytes free below `$FFCF`. Zero page +1: `KERNELZP` ends at
      `$FB`, 4 bytes free.
    - Not tested on screen: the text tests do not see color. No shell command uses the call
      yet; a shell `COLOR` is the next step.
    - Build 919 ms, the new baseline (`CMDSHELL.COM` recompiled, since `api.py` changed).
      `BOOT` ok 0.5 s, `SHELL` ok 0.4 s.
  - Color names (2026-10-17): `DOS.UXI` has `API_CON_COLOUR` and the 16 palette names as
    CONSTs, `BLACK` 0 to `LIGHTGRAY` 15, as `DOS.BLUE` in UXCBASIC. The shell's numbers take
    the same names: `PRINT LIGHTGRAY * 16 + WHITE` prints 241. No `_` in the names, since
    `READ_NAME` does not take it.
    - `COLOR_NUMBER` in `CMDSHELL.UXB`: an `INSTR` in a 176-byte table, 11 characters a
      name, and the position less 1, divided by 11, is the value. EVAL_NUMBER calls it for a
      name that is not a variable; an unknown name is a syntax error. A color name cannot be
      assigned (syntax error).
    - Trap: the table's order is the values' order in `DOS.UXI`; change both together.
    - `CMDSHELL.COM` 18672 bytes, +369. Tried: string `SELECT CASE` +624; a word-count
      function with the table as an argument +428 (a literal argument is copied, 112 more).
    - `SHELL` test gained 3 lines. Build 887 ms, the new baseline. `SHELL` ok 0.6 s, `SHIF`
      ok 0.4 s.
    - Docs owed: PLAN section 7 or the console bullets (the color byte, the cursor rule);
      PLAN line 364 says the color is fixed.
  - Shell `COLOR foreground,background` (2026-10-17): each 0 to 15, else syntax error; both
    are needed. `COLOR WHITE, BLUE`. It calls `DOS.SET_COLOR(background * 16 + foreground)`.
    - `DOS.UXI`: `SUB SET_COLOR(COLOR)` (REG_P 0) and `FUNCT GET_COLOR() AS UBYTE` (REG_P
      1). Neither touches ERROR. An uncalled one costs 0 bytes.
    - `EVAL_PAIR` reads `first,second` into the UWORDs `FIRST_NUMBER` and `SECOND_NUMBER`;
      LOCATE and COLOR share it, 48 bytes less than two copies.
    - `CMDSHELL.COM` 18854 bytes, +182. The `SHELL` test gained 4 lines (the color itself is
      not seen by the text tests).
    - Build 965 ms, the new baseline. `SHELL` ok 0.6 s, `SHSCREEN` ok 0.6 s.
    - Docs owed: PLAN's shell statements list and `HELP.TXT` (COLOR, the color names).
    - Full suite after it: 29 tests, 4 failed on golden churn only. The `DOS.UXI` change
      recompiled the test programs with pyuxc's dead-code pass (`uxc_dead.py`, 2026-10-16),
      1 to 1.6 KB smaller each: `CWD.COM` 2406, `DUP.COM` 3887, `SEEK.COM` 1948.
      Golden files changed: `FILES` (the sizes), `DIRS` FREE 6 more, `CMDLETS` 882 KB free,
      `DISK` F33 cluster `$46`. Each then ok one at a time: `FILES` 0.4 s, `DIRS` 0.7,
      `DISK` 0.4, `CMDLETS` 1.3.
  - Docs step after `COLOR` (2026-10-17); no docs are owed from the bullets above. PLAN §4: the
    `con_*` calls in the table. §6: the color byte, the cursor rule. §8: the boot run, `COLOR`,
    the short names table, the color names and the table trap, the `PROMPT$` codes, `HELP` as a
    DOS utility and the `HELP.TXT` format, `EXIST` with no `SILENT`, `WHICH` renamed `WHERE`.
    §10: `src/cbin`, `src/dos`, `TEST.ROM`, `SHELL_ROM_TESTS`. §11: 7h `COLOR`, 7i4 put off,
    step 8 note. §13: what the ROM prints when the shell will not run. The `api_bad` claim
    (calls 8, 9, 33 to 36) holds: none is `written` in `api.py`.
    - `HELP.TXT` gained topics `COLOR` and `COLORS`: 2844 bytes, no cluster more, free space
      unchanged. Build 523 ms, the new baseline. `CMDLETS` golden rewritten and diffed (the
      topic list only) ok 1.3 s.
  - 4 MB card (2026-10-17): the X16's standard card is 4 MB (the user). `tools/mksd.py`'s
    defaults are now 6016 clusters of 1 sector, so `build/SD.IMG` is 4194304 bytes: 3008 KB of
    clusters after the 1 MB before the partition. PLAN §10 says so. The test card in `tests.py`
    stays 1024 clusters of 2 sectors, so no golden changes and no test ran. Build 502 ms, the
    new baseline.
  - Extended keys (2026-10-17), the DOS way (the user chose it over Esc lead-ins, WordStar keys
    and ANSI input): an extended key gives two characters from `con_in`, 0 then its IBM PC scan
    code. The keys: Up $48, Down $50, Left $4B, Right $4D, Home $47, End $4F, PgUp $49, PgDn
    $51, Insert $52, Delete $53, F1 to F10 $3B to $44. The SMC keycodes are IBM key numbers:
    Up $53, Down $54, Left $4F, Right $59, Home $50, End $51, PgUp $55, PgDn $56, Insert $4B,
    Delete $4C, F1 to F10 $70 to $79. `kbd_get` sets the new zero page byte `con_scan` and
    returns 0; `con_status` reports a key while `con_key` or `con_scan` is set; `con_in` returns
    `con_key` and moves `con_scan` into it. `kbd_special_chars` marks a scan code with bit 7
    (`EXTENDED`); F1 to F10 are a range, not table entries (8 bytes fewer). `api_con_line`
    drops the scan code after a 0. Cost: CODE +36, RODATA +20, ZP +1 (KERNELZP now ends at
    $FC). Trap: UXCBASIC's `GETKEY()` returns 0 both for no key and for the lead-in, so a
    `GETKEY` poll sees the scan code as a plain character ($48 is "H"); a program that wants
    extended keys reads with `API_IN` ($03BB), which waits. `PAUSE` still ends on one press.
    No test can press these keys: x16emu `-bas` pastes ASCII into the keyboard queue. Not yet
    tried by hand. Tests: `ASK` ok 0.6 s, `SHELL` 0.5, `SHBOOT` 0.4. Build 879 ms, the new
    baseline. API.md has it (`con_in`).
  - ANSI output (2026-10-17), a light ANSI.SYS in `con_out`, always on (the user). `console.s`'s
    header lists the sequences: `Esc[r;cH` and `f`, `Esc[nA` to `D`, `Esc[2J`, `Esc[K`,
    `Esc[...m` with 0, 1, 30 to 37 and 40 to 47. Up to 4 parameters, each modulo 256; parameter
    bytes `$30` to `$3F` other than digits and `;` are skipped, so `Esc[?7h` does nothing. Esc
    then a byte other than `[` shows that byte. `Esc[0m` sets `con_default`, the color
    `api_con_colour` last set (boot: `CON_COLOUR`), so a program's reset keeps the user's
    `COLOR`. Bold maps the foreground through `ansi_bright`, now and for each 3x after it, so
    `Esc[37;1m` and `Esc[1;37m` both give white. The ANSI colors are X16 palette entries 0, 2,
    5, 9, 6, 4, 3, 15 (brown for yellow, light grey for white); bright black is 11, red 10,
    green 13, yellow 7, blue 14, white 1; magenta and cyan stay 4 and 3. Not done: 7 reverse,
    `s` and `u` save and restore, `n` status report, `J` other than 2. The normal path costs
    `ldx ansi_state` and `bne`, 5 cycles a byte; Esc goes through `@glyph`. The ansi block sits
    after `vscroll`, reached by `jmp`, so `write`'s branches stay in range. Cost: CODE +305,
    RODATA +26, ZP +1 (`ansi_state`; KERNELZP now ends at $FD, 2 bytes left), KERNELRAM +7 (ends
    at $06B8). About 5080 bytes of ROM stay free. New test `ANSI` (`tests/ANSI.S`): 14
    sequences, the cursor and color after each; the dump was checked by hand against the
    expected values. Tests: `ANSI` ok 0.4 s, `SHELL` 0.4, `SHBOOT` 0.4, `MONITOR` 0.3. Then
    `inc ansi_state` for `Esc[` saved 2 bytes: `ANSI` ok 0.5 s, `SHELL` 0.4. Build 507 ms, the
    new baseline. Not yet seen on screen by hand. API.md (`con_out`) and PLAN section 6 have it.
  - Alt and Ctrl keys (2026-10-17), the IBM PC BIOS codes, each 0 then a scan code from
    `con_in`: Alt+letter the letter's scan code (keycode - 1 for the Q and A rows, keycode - 2
    for the Z row); Alt+1 to Alt+= $78 to $83 (`SCAN_ALT_1`); F1 to F10 from $3B, with Shift
    $54, Ctrl $5E, Alt $68 (`kbd_fkey_mods`, `kbd_fkey_bases`; Alt wins over Ctrl, Ctrl over
    Shift); Ctrl+Left $73, Right $74, End $75, PgDn $76, Home $77, PgUp $84
    (`kbd_ctrl_scans`, for the first 6 entries of `kbd_special_keys`, now reordered). Ctrl:
    letters and `[ \ ]` give $01 to $1D; Ctrl+2 gives 0 then 3, Ctrl+6 $1E, Ctrl+- $1F; Ctrl
    with a control character or Space keeps it; Ctrl with any other key gives nothing. Alt
    with a key other than a letter, a digit, - or = gives nothing. The Alt keycodes are $3C and
    $3E; `MOD_ALT` = $40, so `bit kbd_mods` puts Ctrl in N and Alt in V. `api_con_status` also
    returns `kbd_mods` in X; the gate's `lda gate_a` sets Z from A, so `S_GETIN`'s `beq` holds.
    The Caps Lock letter test lost `cmp #'z' + 1` (`kbd_lower` holds nothing past 'z'); a
    special character goes out through `@code`'s `and #$1F`, since both are below $20. Not
    done: Alt + keypad digits, Ctrl+Alt+Del, the enhanced BIOS codes (Ctrl+Up, Alt+arrows,
    Alt+punctuation, F11, F12). Cost: CODE +82, RODATA +17; about 4980 bytes of ROM stay free.
    No test can press these keys (`-bas` fills the keyboard queue, past `kbd_get`); not yet
    tried by hand; the x16emu Ctrl shortcuts are off on this machine. Tests: `ASK` ok 0.5 s,
    `SHELL` 0.4, `DUP` 0.4 (`API_STATUS`). Build 440 ms, the new baseline. API.md has it
    (`con_in`, `con_status`).
  - Key constants and KEYTEST (2026-10-17, the user's request):
    - `src/bas/KEYS.UXI`, namespace `KEY`, constants only, for any file, with or without
      `DOS.UXI`: `EXTENDED` 0, `BACKSPACE`, `TAB`, `ENTER`, `ESC`, `SPACE`, `CTRL_A`, `CTRL_6`,
      `CTRL_MINUS`; `MOD_SHIFT`, `MOD_CAPS`, `MOD_ALT`, `MOD_CTRL`; the `SCAN_` codes of
      every key `kbd_get` gives (cursor, editing, Ctrl+cursor, F1 to F10 with each modifier,
      Alt+1 to Alt+=, Ctrl+2, Alt+letter). Checklist comment: change it with `console.s`.
    - `DOS.UXI` gained `API_CON_STATUS` ($0388) and `API_CON_IN` ($03BB). CMDSHELL.COM stays
      18854 bytes.
    - `src/bas/KEYTEST.UXB`, `KEYTEST.COM` 2702 bytes on `build/SD.IMG`: polls
      `API_CON_STATUS`, prints the modifiers each time they change, and for each key its
      codes and name. Esc twice ends it. It reads an extended key as `GETKEY()` 0, then
      `GETKEY()` the scan code; the `SCANKEY()` step changes that, and the `KEYS.UXI` header
      with it. Not run: no test can press the keys; for the user to try by hand.
    - Build 1713 ms (every UXB recompiled after the `DOS.UXI` change), the new baseline.
      Tests: `SHELL` ok 0.8 s.
  - VIEW step V1 of 4 (2026-10-17), `src/dos/VIEW.UXB`, `build/DOS/VIEW.COM` 4368 bytes. The
    user chose: build it now on `GETKEY()` 0 then `GETKEY()` (the `SCANKEY()` step changes
    it), an index entry every 16th line, Q or Esc quits, 4 steps (V2 sideways scroll and wrap,
    V3 find with a highlight, V4 G to a line).
    - 29 text rows and a footer on row 29 in `Esc[30;47m`: the name cut to 24, `Line n` (the
      top line), the keys; cut to 79 characters, since column 80 wraps and scrolls. Up, Down,
      PgUp, PgDn, Space (as PgDn), Home, End; Q, q or Esc clears the screen and ends, exit 0.
      No name: `Required parameter missing`, exit 1. Open fails: `DOS.ERRMSG`, exit 2.
    - Its own reader: `DOS.READ_FILE` into a 512-byte buffer, `BUFFER_START` a ULONG. The
      runtime's `LINPUT #` reads 1 byte a call. CR, LF, CR LF end a line; a tab goes to the
      next multiple of 8; BS, BEL, FF, $0F, Esc show as "."; 255 characters a line, the rest
      dropped. A row goes out with one `WRITE 1`, then `Esc[K` when under 80.
    - Index: `INDEX_LOW` UWORD and `INDEX_HIGH` UBYTE arrays, 1024 entries, 3072 bytes, 16384
      lines; a line past them reads on from the last entry. `INDEX_SHIFT` 4 sets the step:
      the user wants it changed for a 60-row screen. Entry 0 is set at start; the others as
      `READ_LINE` passes them. The high byte goes in and out with `ContentsAt(@SEEK_TARGET +
      2)`, no ULONG shift. `GO_TO_LINE` reads on with no seek when the reader is between the
      entry and the target. Lines count to 65535.
    - Down scrolls in hardware with no asm: a CR on the footer row scrolls the screen up, and
      the new line goes on row 28. Up redraws the page. End reads to the end, building the
      index.
    - RAM: 3072 index, 512 buffer, 255 line, 200 strings and words. Not yet tried by hand.
    - New test `VIEW` (`tests/VIEW.IN`): no name, a missing file, then `DOCS\LONG.TXT` (50
      lines) with Space and q: page 1, page 2 (lines 30 to 50, 9 blank rows, `Line 30`). The
      golden was checked by hand. A lone space on a `.IN` line is lost: the Write tool strips
      it; Space and q share a line. `VIEW` ok 0.5 s. Build 647 ms, the new baseline.
    - The user tried V1 by hand: it works (2026-10-17).
  - VIEW step V2a (2026-10-17), sideways scroll; V2 was split into V2a and V2b (wrap).
    `LEFT_COLUMN` is the first column shown. Left and Right move it by `SHIFT_STEP` 8, from 0
    to `SHIFT_MAX` 176, the last multiple of 8 that shows a character of a 255-character line;
    each redraws the page. `SHOW_LINE` writes from `@LINE_TEXT + LEFT_COLUMN`. The footer shows
    `Col n` after `Line n`. `VIEW.COM` 4368 to 4551 bytes (+183), 1 byte of RAM.
    - Tests: the `VIEW` golden changed in its two footers only. `VIEW` ok 0.6 s. Left and Right
      are not tested: the harness types no extended key. Build 618 ms, the new baseline.
  - VIEW step V2b (2026-10-17), wrap. W or w turns `WRAP` on and off and redraws the page.
    With wrap a line takes 1 to 4 rows (`LINE_ROWS`), Left and Right do nothing, and the
    footer shows `Wrap` in place of `Col n`. The footer keys are now `Arrows PgUp PgDn Home
    End  W wrap  Q quits`; Space still pages down.
    - `SHOW_PAGE` fills the 29 rows and sets `PAGE_LINES`, the lines shown in full; the last
      line may show in part, and `AT_END` is then 0. PgDn adds `PAGE_LINES` to `TOP_LINE`.
      `SHOW_LINE(ROW, FIRST)` takes the first column: `LEFT_COLUMN`, or 0, 80, 160, 240.
    - `FIT_BACK(LAST)` gives the top line of the page that ends at line `LAST - 1`: it reads the
      up to 29 lines before `LAST` into `PAGE_ROWS(29)`, then sums back. PgUp and End use it in
      both modes. Down with wrap redraws the page.
    - `VIEW.COM` 4551 to 5079 bytes (+528), 31 bytes of RAM. Still 5 clusters on the test card.
    - Tests: `tests/VIEW.IN` adds `VIEW SCRIPTS\BIG.CMD` and `Wq`: lines 3 and 7 are cut to 255
      and take 4 rows each, 16 blank rows; checked by hand. Footers changed. `VIEW` ok 0.7 s.
      Build 669 ms, the new baseline.
    - `sd/WIDE.TXT` (user card only, not the test card): 300 lines, CR LF, 41039 bytes, for
      trying VIEW by hand. Lengths cycle 20, 0, 79, 80, 81, 120, 159, 160, 161, 200, 240, 241,
      255, 300, 64, 1. Each line starts `Lnnn len mmm`, then a ruler: the tens digit at each
      tenth column, `:` at each fifth, else `.`; the last character is `|`. `sd/README.TXT`
      says so. The user said V2b looks good (2026-10-17).
  - VIEW step V3 (2026-10-17), find. F, f or / prints `Find: ` on the footer row and reads
    `FIND_TEXT` (40 characters) with `LINPUT`; its CR scrolls the screen, and the page is drawn
    again. An empty text only redraws. Case does not count (V3b). The footer keys are now `F find
    N next  W wrap  Q quits`; the movement keys left it for room.
    - `LINE_TEXT` is now a `STRING * 255`: characters at `@LINE_TEXT + 2`; `FIND_NEXT` puts
      `LINE_LENGTH` in the length byte at `@LINE_TEXT + 1` before `INSTR`.
    - `FIND_NEXT(FROM_LINE)` reads on from that line and sets `MATCH_LINE` and `MATCH_COLUMN`
      (from 0) at the first line that has the text. `FIND_FROM` moves `TOP_LINE` to the match
      line when it is not shown in full, and without wrap sets `LEFT_COLUMN` to the match
      column rounded down to 8, at most `SHIFT_MAX`, when the match is not all on screen.
    - F searches from `TOP_LINE`; N or n from `MATCH_LINE + 1`. No match: `MATCH_LINE` is 65535,
      the footer says `Not found: text` (`PUT_FOOTER`, shared with `SHOW_FOOTER`), and the next
      N starts at line 0.
    - `SHOW_LINE`: when `READER_LINE - 1` is `MATCH_LINE`, the part of the first match on the
      row is written again in `Esc[7m` (reversed, V3c), then `Esc[0m`.
    - `VIEW.COM` 5079 to 6325 bytes (+1246): `LINPUT` 209, `INSTR` 147, VIEW's own code 890
      (variants compiled by `sizes.py` in the scratchpad). RAM +48: `FIND_TEXT` 42, the match
      3, `LINE_TEXT` 2, and locals. 7 clusters on the test card, was 5.
    - Tests: `tests/VIEW.IN` adds `VIEW DOCS\LONG.TXT`, `FLine 45`, `nq`: the page from line
      45 with `Line 45` in `Esc[30;43m` on row 0, footer `Line 45`; then `Not found: Line 45`
      and no highlight; checked by hand. `VIEW` ok 0.9 s. Golden churn of the 2 clusters, 874
      to 872 KB free, diffed: `CMDLETS` ok 1.4 s, `DIRS` 0.8, `DISK` 0.4 (the cluster byte $4E
      to $50). `FILES` ok 0.4 without change. Build 1135 ms, the new baseline.
    - Byte savings not yet looked at: the 890 bytes of VIEW's own code. Not tried by hand.
  - VIEW step V3b (2026-10-17), the user's change: find in any case. `TO_UPPER(ADDRESS,
    COUNT)` turns a to z into A to Z in place. F folds `FIND_TEXT` after `LINPUT`, so `Not
    found:` shows it in upper case. `FIND_NEXT` folds each `LINE_TEXT` before `INSTR`;
    `SHOW_PAGE` reads the lines again, so the page and the highlight show them as they are.
    - `VIEW.COM` 6325 to 6476 bytes (+151), still 7 clusters, so no golden churn. RAM +1.
    - `tests/VIEW.IN`: `Fline 45` finds `Line 45`; the golden differs only in the echo and
      `Not found: LINE 45`, diffed. `VIEW` ok 0.9 s. Build 655 ms, the new baseline.
    - The user, 2026-10-17: no G (go to a line). VIEW's steps end at V3.
  - VIEW step V3c (2026-10-17), the user's change: the highlight is the colors reversed. The
    asm was agreed. `console.s` `sgr`: parameter 7 swaps the nibbles of `con_colour` (asl, adc
    #$80, rol twice, as `cursor_flip`), so a second 7 swaps them back; there is no 27. `Esc[0m`
    restores `con_default`. `SHOW_LINE` writes `Esc[7m` in place of `Esc[30;43m`.
    - ROM +16 bytes, counted by hand. `CODE` and `RODATA` end at `$EC3A`; 5012 bytes free below
      `$FFCF`. RAM 0. `VIEW.COM` 6476 to 6472 bytes.
    - `tests/ANSI.S` adds `Esc[7m` twice after bold white: `$10`, then `$01`. The golden's later
      results move 6 bytes, otherwise the same, checked by hand. `ANSI` ok 0.4 s.
    - `VIEW` golden differs only in `[7m` for `[30;43m`, checked by script. `VIEW` ok 1.1 s.
      Build 648 ms, the new baseline.
  - `EXIST` prints nothing (the user's rule) and takes no `SILENT`: `EXIST name` sets `P1$` and
    the exit code only. No name: exit 2, `P1$` stays empty. Header example `EXIST
    DOCS\README.TXT`. `HELP.TXT` `EXIST` topic and the `HELP` topic say it prints nothing.
    `EXIST.CBI` 1733 to 1439 bytes (-294), still 2 clusters. `HELP.TXT` 1177 bytes. Build 781 ms,
    the new baseline. `CMDLETS.IN` drops `EXIST DOCS\*.TXT SILENT` and prints `P1$` after
    `EXIST DOCS`. `CMDLETS` golden rewritten and diffed (the four `EXIST` print lines gone) ok
    1.1 s.
  - `HELP.TXT` is 1204 bytes, 2 clusters (was 1). The card has 876 KB free. Build 584 ms, the
    new baseline. Goldens rewritten and diffed: `CMDLETS` (877 to 876, `HELP` lines) ok 1.4 s,
    `DIRS` (each free count -1) ok 0.7 s, `DISK` ($130D $48 to $49) ok 0.4 s. `FILES` ok 0.4 s.
- `docs/PLAN.md` is draft 3, written 2026-10-14. MS-DOS 2.0 is its model. The user has not
  reviewed it yet.
- PLAN §3 "Banked RAM" designs extended memory blocks after XMS: `xms_alloc`, `xms_free`,
  `xms_move`, a chain of banks per handle, owner and next-bank tables in bank 0. It is step 10
  of §11, not built. The UXCBASIC plan §5 has "Arrays that span RAM banks" to match.
- PLAN §2 lists which parts are UXCBASIC now, which wait for a compiler feature, and which stay
  asm. It also defines `DOS.UXI`, the API library, `src/bas/DOS.UXI`.
- Licence: MIT, in `LICENSE`. `NOTICE` lists third-party code: none in the ROM yet, and the cc65
  build tools. PLAN §9 has the checklist for each file ported from x16-rom.
- ca65 and ld65 V2.19 (Git e11fb5c) are in `tools/cc65/bin`, with the zlib licence in
  `tools/cc65/LICENSE`.
- Step 0 is done:
  - `src/asm/rom.cfg` links ROM bank 0, 16384 bytes, to `build/6502DOS.ROM`.
  - `tools/build.py` builds it. `tools/tests.py` runs the tests in `tests/`.
  - The test output channel is `-echo raw`, in PLAN §10.
- Step 1 is done, for the user to review:
  - `src/asm/mem.inc` holds the PLAN section 3 addresses and the VERA registers.
  - `tools/api.py` lists 39 calls, numbered 0 to 38, with their registers and errors, the 15
    error numbers with their messages, and the find buffer. The registers of each call are a
    first design. Errors 9 and 13 joined PLAN section 4.
  - `tools/genapi.py` writes `build/gen/api.inc`, `build/gen/api.s` and `docs/API.md`.
    `tools/build.py` runs it first. Every call maps to `api_bad` (error 1) until its routine
    exists and api.py marks it `written`.
  - The banner's version comes from `VERSION` in api.py.
- Settled after step 1: the kernel takes `\` and `/` as path separators; `CMDSHELL` options
  start with `-`; an `ALIAS` or `BIND` command comes later (PLAN sections 5 and 8).
- Step 2 is done, for the user to look at in a window:
  - `src/asm/console.s`: VERA setup, the font load, `con_out` with CR, LF, BS, TAB, BEL and
    FF, hardware scroll, `con_in` with a blinking cursor, `con_status`, and the SMC keyboard
    in a US layout with Shift, Ctrl and Caps Lock. ANSI came later (the ANSI output bullet).
  - `src/asm/font.s`: the CP437 font from x16-rom. `src/asm/i2c.s`: the I2C read from
    x16-rom. Both are in `NOTICE`. x16-rom's LICENSE.md does not name the CP437 file; it is
    treated as BSD-2, the rule for unlisted code.
  - `boot.s` clears the kernel zero page, calls `con_init`, turns on the VSYNC IRQ (a 32-bit
    tick counter), prints the banner with CR LF, and echoes keys. `$FFD2` jumps to `con_out`.
  - A headless `-gif` capture showed the green banner on black and the cursor blinking.
    Typing was not tested headless: no test feeds keys yet.
  - ROM use: `boot.s` 127 bytes, `console.s` 488 bytes of code and 134 of key tables,
    `font.s` 2048, `i2c.s` 178, `api.s` 371.
- Step 3 is done:
  - `src/asm/gate.s`: the gate code, copied to `$0310` at boot, and the call entries at `$0340`,
    written by a loop. `api_table` records are 3 bytes: the routine and its ROM bank (`.bank`,
    from `bank = 0` in `rom.cfg`).
  - `src/asm/kernel.s`: the driver chain, `NUL` then `CON`, both in ROM; the SFT in RAM bank 0;
    the handles in the PSP; the calls `open` (devices only), `close`, `read`, `write`,
    `version`, `ticks` and `errmsg`. `kernel_init` calls each driver's init, so `con_init`
    runs from the chain.
  - `src/asm/console.s`: `con_line` and `con_status` calls; keys come from the stock keyboard
    queue at `$A800` first.
  - `src/asm/monitor.s`: `D`, `E`, `F`, `G`, and BRK shows the registers. It reads and writes
    through the gate.
  - `boot.s`: `CHRIN` at `$FFCF`; the IRQ sends a BRK to the monitor; boot ends in the monitor.
  - `tools/tests.py` types keys with `x16emu -bas`: `tests/NAME.S` and `tests/NAME.IN`
    (PLAN section 10).
  - ROM use: `boot.s` 122 bytes, `console.s` 613 + 134 tables, `gate.s` 38 + 45 copied to RAM,
    `kernel.s` 575 + 62 driver headers, `monitor.s` 658 + 29, `api.s` 410, `i2c.s` 178,
    `font.s` 2048. Kernel zero page `$80–$BB`.
- Step 4 is done:
  - `src/asm/sdcard.s`: the SD card block driver, ported from x16-rom `fat32/sdcard.s` (BSD-2,
    in `NOTICE`). One unit, read only, slow SPI loop. The start-up commands come from a table.
  - `src/asm/fat.s`: the drive table at `$0600` (4 drives, 32 bytes each), mounting at boot
    (MBR, first partition of type `$0B` or `$0C`, FAT32 boot sector), the sector buffer at
    `$0400` with the last sector kept, paths with a drive and `\` or `/`, 8.3 names with `*` and
    `?`, directory search, file reads, and the calls `findfirst`, `findnext`, `getdrive`,
    `setdrive`.
  - `src/asm/kernel.s`: `open` finds a device by the last part of the path first, then a file.
    A file opens with access 0 only. The SFT holds a file's drive, clusters, size and position.
    The chain is `NUL`, `CON`, SD card; `kernel_init` gives each block unit a drive letter from
    `C:` and mounts it.
  - `src/asm/monitor.s`: `DIR [path]` and `TYPE path`. API errors print their message.
  - Errors 21 (drive not ready) and 30 (read fault) joined `tools/api.py`. The find buffer is
    63 bytes, with a 32-character name field. PLAN section 5 has the name and path lengths.
  - `tools/mksd.py` writes a FAT32 SD image from a folder. `build.py` makes `build/SD.IMG` from
    `sd`; `tests.py` makes `build/tests/SD.IMG` from `tests/sd`.
  - Not written: long names, delete, rename, mkdir, rmdir, the FSInfo free count.
  - ROM use: `fat.s` 1319 bytes, `sdcard.s` 370 + 53, `kernel.s` 578 + 62, `monitor.s`
    1013 + 47, `api.s` 439. Kernel zero page `$80–$DE`; kernel RAM `$0600–$0690`. ROM bank 0
    holds 7.1 KB of 16 KB.
- Step 5 is done, without the KERNAL file entries, which are step 5b (PLAN section 11):
  - `src/asm/exec.s`: the calls `exec`, `exit` and `exitcode`. `exec` copies the parent's PSP,
    `$0801–$9EFF` and `r0`–`$7F` to 5 RAM banks a level, 4 levels (banks 1 to 20), builds the
    child's PSP in place (handles inherited, the command tail with CR after it), loads the program
    and calls its start: `SYS n` from a BASIC first line, else `$0801`. `exit` and `RTS` close
    the child's handles and copy the parent back. PLAN section 7 has the PSP layout.
  - `src/asm/fat.s`: `file_copy`, the file read without the SFT, copies up to a page at a time
    (about 18 cycles a byte, was about 75). `exec` loads through it.
  - `src/asm/kernel.s`: `handles_inherit` and `handles_close`.
  - `src/asm/console.s`: CR ends a line and an LF right after a CR does nothing; `$0F` shows
    nothing; `con_getin` and `con_plot`.
  - `src/asm/boot.s`: the KERNAL entries `screen_set_charset` (`$FF62`, does nothing), `CHRIN`,
    `CHROUT`, `GETIN` (`$FFE4`) and `PLOT` (`$FFF0`). Segment `KERNALJUMPS` starts at `$FF62`.
  - `src/asm/gate.s`: writes `$47` to `$0372`, the stock charset byte, over the entry of call
    16. `tools/api.py` reserves number 16, so the calls from 16 on moved up by one.
  - `src/asm/monitor.s`: `RUN path [tail]`.
  - `src/bas/ARGS.UXB`: a UXCBASIC program that prints its command tail. `build.py` compiles it
    with `tools/uxb.py` when the COM file is older than the source, and puts it on both SD
    images.
  - `tests/com/CHILD.S`: the program the `EXEC` test runs. `tests.py` assembles `tests/com/*.S`
    to COM files on the test card.
  - ROM use: `exec.s` 386 bytes, `fat.s` 1366, `kernel.s` 608 + 62, `console.s` 645 + 134,
    `monitor.s` 1061 + 50, `api.s` 442. Kernel zero page `$80–$E9`; kernel RAM `$0600–$0691`.
    ROM bank 0 holds 7.4 KB of 16 KB.
- Step 5b is done (PLAN section 7):
  - `src/asm/compat.s`: every KERNAL entry, moved from `boot.s`. The file entries `SETLFS`,
    `SETNAM`, `OPEN`, `CLOSE`, `CHKIN`, `CHKOUT`, `CLRCHN`, `READST`, `LKUPLA`, the command
    channel, and `CHRIN` and `CHROUT` through the channels. Segment `KERNALJUMPS` starts at
    `$FF59`.
  - The PSP holds the logical file table and the two channels, at `$0730–$0745`.
  - `src/asm/kernel.s`: `handle_end`, for `READST`'s `$40`. The `CON` driver sets `con_direct`
    around its reads and writes, and so does `con_line` in `console.s`.
  - `src/bas/SHOW.UXB`: a UXCBASIC program that prints the file its tail names with `LINPUT #`.
  - `tests/KERNAL.S` and `KERNAL.IN`: each entry's results and errors, the status lines, and
    `SHOW.COM` on three files.
  - ROM use: `compat.s` 538 + 26 + 154 bytes of entries, `kernel.s` 649 + 62, `console.s`
    649 + 134, `boot.s` 125. Kernel zero page `$80–$ED`; kernel RAM `$0600–$069C`. ROM bank 0
    holds 8.2 KB of 16 KB.
- The console line editor behind `CHRIN` is done (PLAN section 7):
  - `src/asm/compat.s`: `CHRIN` from the console reads a line with `con_edit` into `CON_LINE`,
    `$0200`, then returns one character a call, CR last. `chrin_next` holds the offset of the
    next one. With `con_direct` set, `CHRIN` still returns a key without echo.
  - `src/asm/console.s`: `con_edit` is `api_con_line` without the echo of CR LF.
    `api_con_line` calls it, then echoes CR LF.
  - `src/asm/monitor.s`: its input line shares `$0200`, and its prompt clears `chrin_next`.
  - `tests/KERNAL.S` reads a typed line and prints it in brackets.
  - ROM use: `compat.s` 571 + 26 + 154, `console.s` 659 + 134, `monitor.s` 1063 + 50. Kernel
    zero page `$80–$EE`.
- `tools/uxb.py` compiles with pyuxc, `UXCBASIC/pyuxc`, into `build/uxc`, and copies
  the program to where the caller asked, as `NAME.COM`. `#INCLUDE` looks in the source's folder, then `src/bas`,
  the folder of `DOS.UXI`. `ARGS`, `ASK` and `SHOW` compile to the same bytes as the GPC UXC,
  in under 0.1 s each. The build with those compiles took 0.83 s.
- Tests after the line editor, one at a time: `KERNAL` ok 0.5 s (new golden file), `BOOT` ok
  0.5 s, `MONITOR` ok 0.5 s, `HANDLES` ok 0.4 s, `DISK` ok 0.4 s, `FILES` ok 0.4 s, `EXEC` ok
  1.1 s.
- Tests after the move to pyuxc: `KERNAL` ok 0.9 s, `EXEC` ok 0.7 s.
- Step 6a of PLAN section 11 is done:
  - `src/bas/DOS.UXI`: each call sets its
    registers, `SYS` to its entry at `$0340`, and takes the carry and A into `DOS.ERROR`. `R0`
    to `R5` are `DIM ... AT $02`. A path goes as the string's address + 1, its length byte.
    `CON_LINE` passes the string itself as the buffer. `SEEK` puts the new position in
    `POSITION_LOW` and `POSITION_HIGH`. `VERSION` gives "0.1.0".
  - Trap: UXCBASIC's `LONG` routines use `$02-$0D`, r0 to r5. A call sets its registers right
    before its `SYS`.
  - `tests.py` compiles each `tests/NAME.UXB` and runs it with `RUN NAME.COM`.
  - `tests/DOSAPI.OUT`: the calls not written give E 1. A file's LF shows as a new line.
- Step 6b part 1 is done: the current directory.
  - `src/asm/fat.s`: `DPB_CWD`, the first cluster of each drive's current directory, set to the
    root at mount. `path_walk` starts at the root after a separator, else at `DPB_CWD`.
    `dir_enter` steps into one directory; `.` and `..` missing, at the root, give the root.
    `component` keeps leading dots in the name. `drive_ready` is `drive_exists` and the
    file-system check. `fcb_fill` fills `fcb_name`.
  - `chdir` (3Bh) and `getcwd` (47h) are written. `getcwd` keeps no text: it walks the `..`
    entries up and finds each directory's name in its parent by cluster, building the path back
    from the buffer's end. Errors 3, 15, 21.
  - `tests/CWD.UXB` and `CWD.OUT`: `chdir`, `getcwd`, relative paths with `.` and `..`, drives.
    `tests/sd/MANY/SUB.DIR/INNER/DEEP.TXT` is new: `SUB.DIR` lies in the second cluster of
    `MANY`.
  - Golden files changed: `DISK` (F33's search state now holds cluster $19), `FILES` (the root
    lists `ASK`, `CWD`, `DOSAPI`), `DOSAPI` (`GETCWD 1` E 15; `CHDIR` E 3 until `mkdir`).
  - ROM use: `fat.s` 1720 bytes (was 1366).
- Build after 6b part 1: 0.48 s (baseline, no UXB compiles).
- Full suite after 6b part 1: 10 tests ok, 5.2 s. `CWD` 0.5 s, `DOSAPI` 0.4 s, `STOCK/DOSAPI`
  0.9 s.
- Step 6b part 2 is done: `seek` (42h).
  - `src/asm/fat.s`: `api_seek` adds the offset to 0, the position or the size, stores the
    position, and walks the chain from `SFT_FIRST` to the cluster that holds it. A position at
    or past the size leaves `SFT_CLUSTER` unused. `file_copy` reads 0 bytes past the size. A
    device gives position 0. `kernel.s` exports `sft_find`.
  - `tests/SEEK.UXB` and `SEEK.OUT`: each origin, cluster edges, the end, past the end, a bad
    origin, `CON`, a closed handle. The test card has 2 sectors a cluster.
  - Golden files changed: `DOSAPI` (`SEEK END`, `SEEK START` E 6, the handle of a failed open),
    `FILES` (the root lists `SEEK.COM`, 10 files).
  - ROM use: `fat.s` 1912 bytes (was 1720).
- Build after 6b part 2: 0.34 s.
- Tests after 6b part 2: `SEEK` ok 0.5 s, `DOSAPI` ok 0.4 s, `FILES` ok 0.4 s, `EXEC` ok
  0.7 s, `KERNAL` ok 0.5 s, `HANDLES` ok 0.4 s.
- Step 6b part 3 is done: FAT32 writes, `create` (3Ch), `write` to a file, `close` writes back.
  - `sdcard.s`: `sd_output`, SD command 8, writes with CMD24. Trap: x16emu R49 writes the
    sector and sends no data response; the driver takes 255 bytes of `$FF` as accepted, and
    any other byte must be `xxx00101`.
  - `fat.s`: the buffer has `buf_dirty`, the copies to write: 1, or `DPB_FATS` for a FAT
    sector. `read_sector` writes it back before it reads another sector; every file `close`
    writes it back. `mount` fills `DPB_FATS`, `DPB_FAT_SIZE` and `DPB_LIMIT` (clusters + 2).
  - A file's `cluster` is 0 when not known, after an open or a seek. `cluster_at` walks from
    `file_first` then; after that `cluster` holds the byte before `pos`, and a step happens at a
    cluster start. `api_seek` only sets the position and clears the cluster. `writing` bit 7
    makes `next_cluster` add a cluster at the end of a chain (`cluster_add`), bit 6 zeroes it
    (a directory). `cluster_free` scans the FAT from `free_next`, one hint for all drives,
    back to cluster 2 once; a full drive is `ERR_ACCESS`, and a write then returns a short
    count. Directory clusters go through `dir_step` and stay eager.
  - The SFT entry adds `SFT_ENTRY` (the sector of the directory entry), `SFT_ENTRY_PTR` and
    `SFT_MODIFIED`. `file_close` writes the size, the first cluster and the archive bit.
  - `file_create`: a blank name, a leading dot or a wildcard gives 3; a directory or a
    read-only file 5. It empties an existing file (`chain_free`) or takes the first free slot.
    The new entry has time and date 0: no clock yet. A 0-byte write does not cut the file.
  - `kernel.s`: `api_create` opens with access 2 through `open_common`; open refuses access 1
    or 2 on a read-only file. `api_close` leaves A undefined (it was `$FF`).
  - `ATTR_*` moved to `mem.inc`. Error 29, write fault, is new. `api.py`: `create` written.
  - `tests.py` gives each test a new copy of the card, `build/tests/RUN.IMG`.
  - `tests/WRITE.UXB` and `WRITE.OUT`: create, cluster edges, append, overwrite, a write past
    the end, emptying, read-only, errors, `CON`, 30 files growing `\DOCS` by a cluster.
    `tools/fatcheck.py build/tests/RUN.IMG` checks the card a test leaves: both FATs equal, no
    lost or shared clusters, after WRITE and after DOSAPI.
  - Golden files changed: `DOSAPI` (writes work; `ACCESS 2` opens and stays open, so `NUL`
    gets handle 4), `KERNAL` (`,S,W` opens; leftover registers), `EXEC`, `HANDLES`, `DISK`
    (A after `close`), `FILES` (`WRITE.COM`, 11 files).
  - `src/bas/DOS.UXI`: the user renamed `TAKE_ERROR`; it is `READ_ERR_STATUS`, as 17
    characters passed the limit of 16.
  - ROM use: `fat.s` 2863 bytes (was 1912), `kernel.s` 692 (649), `sdcard.s` 465 (370).
    Kernel zero page `$80–$F8`, 7 bytes left; kernel RAM to `$06A3`. CODE and RODATA end at
    `$E698`.
- Build after 6b part 3: 0.36 s.
- Tests after 6b part 3, one at a time: `WRITE` ok 0.6 s, `FILES` 0.4, `SEEK` 0.4, `CWD` 0.4,
  `BOOT` 0.3, `MONITOR` 0.4, `EXEC` 0.7, `KERNAL` 0.6, `HANDLES` 0.4, `DISK` 0.4, `DOSAPI` 0.4.
- Compiled programs are `NAME.COM`; no file is `.PRG`. The format is the same: the load address
  `$0801`, then the program. `build.py`, `tests.py` and `uxb.py` write `.COM`; pyuxc still
  writes `NAME.PRG` into `build/uxc`, and `uxb.py` copies it to `NAME.COM`. The test programs in
  asm moved from `tests/prg` to `tests/com`.
- Step 6b part 4 is done: `delete` (41h), `rename` (56h), `mkdir` (39h), `rmdir` (3Ah),
  `diskfree` (36h).
  - `fat.s`: `api_delete` takes files only: a directory gives 2, a read-only file 5.
    `entry_drop` marks the entry `$E5`, then frees the chain from `file_first`.
  - `mkdir` is `file_create` with `ATTR_DIR` in `create_attr`: any name that exists gives 5.
    `dir_make` takes a zeroed cluster and writes `.` and `..` into the buffer, which
    `buf_claim` makes the cluster's first sector without reading it. `..` holds 0 in a
    directory of the root. `api_create` clears `ATTR_DIR` from its A.
  - `rmdir`: 3 for a missing name or a file, 16 for the current directory of the drive, 5 when
    any entry but `.` and `..` is left.
  - `rename` copies bytes 11 to 31 of the old entry to `entry_copy` (21 bytes of kernel RAM),
    takes a slot for the new name (`dir_slot`, growing the directory when full), then marks the
    old entry `$E5`. The new path resolves on its own, as in MS-DOS: `RENAME \DOCS\A.TXT B.TXT`
    moves the file to the current directory. A directory renames only in its own directory: a
    move gives 5. Another drive gives 17.
  - `diskfree` reads every FAT sector up to `DPB_LIMIT` and counts the zero entries: r0
    sectors per cluster, r1 r2 free clusters, r3 512, r4 r5 the clusters from 2. A large card
    has a large FAT: this call is slow there until the FSInfo count is kept.
  - `is_root` and `cluster_is` compare `cluster` with a DPB field; `getcwd` and `rmdir` use
    them.
  - Not done: long-name entries before a deleted or renamed entry stay; the kernel does not
    check for open handles on `delete` or `rename` (`docs/API.md` says to close first).
  - `DOS.UXI`: `DISKFREE(DRIVE)`, with `CLUSTER_SECTORS`, `SECTOR_BYTES`, `FREE_LOW`,
    `FREE_HIGH`, `TOTAL_LOW`, `TOTAL_HIGH`.
  - `tests/DIRS.UXB` and `DIRS.OUT`: each call, its errors, `..` two levels down, a directory
    grown past one cluster, the free count back to its start. `fatcheck.py` passes after it.
  - Golden files changed: `DOSAPI` (the calls give their results; `RENAME IN DOCS` names
    `\DOCS\MOVED.TXT`), `FILES` (`DIRS.COM`, 12 files; each `DOS.UXI` program is 104 bytes
    longer), `EXEC` and `HANDLES` (the bytes of the names and calls typed in). `HANDLES.S`
    record 15 calls `attrib`, not written.
  - ROM use: `fat.s` 3563 bytes (was 2863), `kernel.s` 694 (692). Kernel RAM to `$06B9`. CODE
    and RODATA end at `$E956`.
- Build after 6b part 4: 0.35 s.
- Tests after 6b part 4, one at a time: `DIRS` ok 0.7 s, `CWD` 0.4, `DOSAPI` 0.5, `WRITE` 0.6,
  `FILES` 0.4, `HANDLES` 0.4, `KERNAL` 0.6, `EXEC` 0.7, `SEEK` 0.4, `STOCK/DOSAPI` 0.8.
- Step 6b part 5 is done: `ioctl` (44h) subfunction 6, `dup` (45h), `dup2` (46h). Step 6b is
  done.
  - `kernel.s`: `api_dup` takes the first closed handle (`handle_free`); `api_dup2` closes the
    second handle, ignoring its error, then copies; the same handle twice does nothing. Both
    end in `handle_copy`, which counts the SFT entry once more with `sft_share`. The handles
    share the SFT entry, so they share the position.
  - `api_ioctl`: any subfunction but 6 gives 1. A file gives r0 = 0 at or past its size, else
    `$FF` (`sft_end`, `handle_end` after its `sft_find`). A device calls driver command 6,
    `DRV_INPUT_STATUS`: `CON` is `api_con_status`, `NUL` is `nul_status`, which gives 0. MS-DOS's
    `NUL` reports ready; 6502DOS's gives 0 so that `EOF` is true at once.
  - `open_common` and `handles_inherit` use `handle_free` and `sft_share`; `handle_io` and
    `api_ioctl` use `sft_driver`.
  - `DOS.UXI`: `IOCTL(HANDLE, SUBFUNCTION)`, `DUP(HANDLE)`, `DUP2(HANDLE, SECOND)`, and the
    constant `IOCTL_IN_STATUS`.
  - `tests/DUP.UXB` and `DUP.OUT`: the shared position, `dup2` over an open handle, onto
    itself, to a closed handle, handle 1 sent to a file and back, input status of a file, `CON`
    and `NUL`, every handle open (error 4 at the 18th `dup`). `fatcheck.py` passes after it.
  - Golden files changed: `FILES` (`DUP.COM`, 13 files; each `DOS.UXI` program is 113 bytes
    longer), `DISK` (F33's search state holds cluster $27).
  - Trap: `DISK.OUT` holds a cluster number of `MANY`. A new or longer program on the test card
    that sorts before `MANY` moves it. `DISK` was stale from 6b part 4 until this step.
  - ROM use: `kernel.s` 811 bytes (was 694). Savings applied: `api_ioctl` shares `api_errmsg`'s
    error-1 exit (4 bytes) and enters `handle_end` after its `sft_find` (3 bytes). CODE and
    RODATA end at `$E9CB`.
- Build after 6b part 5: 0.39 s.
- Tests after 6b part 5, one at a time: `DUP` ok 0.5 s, `HANDLES` 0.4, `EXEC` 0.7, `KERNAL` 0.5,
  `DOSAPI` 0.6, `FILES` 0.4, `MONITOR` 0.4, `DISK` 0.4, `STOCK/DOSAPI` 0.8.
- Step 6c is done: the stock harness is gone.
  - Deleted: `src/bas/stock/`, `tests/stock/`, `build/tests/stock/`, `STOCK.IMG` and
    `STOCKRUN.IMG`. `tests/stock/DOSAPI.OUT` differed from `tests/DOSAPI.OUT` only in the stock
    banner, the CBM commands `-echo iso` showed, and the limits the stock head comment listed.
  - `src/bas/uxdos/DOS.UXI` moved to `src/bas/DOS.UXI`; `src/bas/uxdos/` is gone.
  - `tools/uxb.py`: `compile(source, program)`. `#INCLUDE` looks in the source's folder, then
    `src/bas`. A program is older than its inputs when `DOS.UXI` is newer and the source
    includes it.
  - `tools/build.py` compiles each `src/bas/NAME.UXB` once, to `build/bas/`. `tools/tests.py`
    has no stock branch: no `STOCK/NAME`, `-echo iso` or `READY.` cut.
  - PLAN sections 2, 10 and 11 name the one `DOS.UXI`.
- Build after 6c: 0.50 s, with `ARGS`, `ASK` and `SHOW` recompiled.
- Tests after 6c, one at a time: `DOSAPI` ok 0.6 s, `DUP` 0.4, `KERNAL` 0.5, `FILES` 0.4.
- Step 6d is done: pyuxc has a 6502DOS target (PLAN section 11, 6d).
  - The stock ROM is not supported (user, 2026-10-15). pyuxc compiles for 6502DOS and has no
    `--target`. `compile_file`'s `target` is `"stock"` in UXCBASIC's `pyuxc/compare.py` only,
    against the GPC golden output, until the port ends.
  - UXCBASIC's `tests.py` runs on `build/6502DOS.ROM` here: `TEST.COM` on a new SD card image,
    `RUN TEST.COM` typed at the monitor, the output up to the prompt. 155 tests ok, 36 s, the
    slowest 0.6 s. A tests run there needs the ROM built here first. Ten goldens changed: the line
    editor echoes typed keys, file output is no longer in the echo, `FILEBERR`'s error address.
    `FILEINERR` read handle 0, standard input here: its source moved to `pyuxc/cases`, and
    `FILEINCLOSED` reads handle 9. `compare.py` counts a source with no GPC golden as NO GOLDEN.
  - `UXCBASIC/tpl/MKTPL.PY` assembles `UXC.TPL.ASM` twice: `-D UXDOS=0` to
    `tpl/UXC.TPL.BIN`, `-D UXDOS=1` to `tpl/UXDOS/UXC.TPL.BIN`. The 6502DOS table takes
    `tpl/UXDOS/SYS.ASM`, `tpl/UXDOS/R-FILE.ASM` and `tpl/UXDOS/API.ASM` (the call addresses).
    `R-PRINT.ASM` (`R_PRSTR`, `R_PRNL`) and `R-STRING.ASM` (`R_INPUT`'s CR echo) test `UXDOS`.
    Both tables have 251 records with the same ids; MKTPL stops when they differ. The stock
    table is byte for byte the one before; `compare.py`: 572 of 572 match.
  - On 6502DOS: `S_CHROUT` writes one byte to the output handle, `STDOUT` or the handle of
    `PRINT #`; `R_PRSTR` sends a string with one `write`; a line ends with CR LF; `S_CHRIN`
    reads a line with `con_line` into its own 83-byte buffer; `S_PLOT` is `con_cursor`;
    `S_GETIN` is `con_status` then `con_in`; `S_INIT` is an RTS; `S_EXIT` calls `exit` with
    code 0. The KERNAL file records are an RTS each.
  - `OPEN`'s name ends with the mode letter, R, W or A; `R_FILE` cuts the length by 1 for the
    call and puts it back. O.APPEND opens with access 1, creates on error 2, and seeks to the
    end. `chkout`, `chkin` and `EOF` use `ioctl` 6. LINPUT # drops an LF after a CR and seeks
    back 1 over any other byte. `CLOSE` of 0 to 2 does nothing.
  - The jump table has calls 40 `con_out`, 41 `con_in`, 42 `con_cursor` (`tools/api.py`,
    `console.s`). `con_out` and `con_in` go through `CHROUT` and `CHRIN` with `con_direct`
    set. `con_plot` returns carry clear and is `api_con_cursor`. ROM: +26 bytes.
  - Programs: 608 bytes smaller over the 9 UXB programs (`ARGS` 266, `ASK` 703, `SHOW` 976).
  - `tools/uxb.py` compiles again when `tpl/UXDOS/UXC.TPL.BIN` is newer than the program.
  - `tools/tests.py`: the stop check leaves out a CR at the end, the start of a CR LF still
    arriving.
  - Golden files: the stock startup's `$0F` is gone from the 8 that run a UXB program. `DIRS`'s
    FREE counts and `FILES`'s list follow the COM files on the test card; both changed.
    Trap: any COM file added to the card, or one that crosses a 1 KB cluster, moves `DIRS`.
  - New tests: `ASK` (`INPUT` through `con_line`) and `TARGET` (`PRINT #`, `INPUT #`,
    `LINPUT #`, O.APPEND, `EOF`, `READ`, `WRITE`, zones, `POS`, `GETKEY`, FILE NOT OPEN).
  - PLAN sections 10, 11 and 12 describe the target; UXCBASIC's plan section 5, help topic
    Targets, `pyuxc/README.md` and `docs/HANDOFF.md` too.
  - The UXCBASIC plan, section 5, holds `END [code]`: an optional exit code byte, 0 when left out.
- Build after 6d: 0.62 s, with `ASK` and `SHOW` recompiled.
- Tests after 6d, one at a time, all 15: `DOSAPI` ok 0.6 s, `DUP` 0.4, `CWD` 0.4, `DIRS` 0.7,
  `SEEK` 0.4, `WRITE` 0.6, `EXEC` 0.7, `KERNAL` 0.5, `ASK` 0.5, `TARGET` 0.4, `FILES` 0.4,
  `BOOT` 0.4, `DISK` 0.4, `HANDLES` 0.4, `MONITOR` 0.4.
- After 6d, `END [code]` and the monitor's CR LF (user, 2026-10-15). Code done and tested; docs
  not done:
  - UXCBASIC: `END code` is a BYTE expression, then `T_ENDCODE` (`jmp API_EXIT`, at the end
    of `tpl/T-CORE.ASM`; the stock table jumps to `S_EXIT`). `END` alone is `T_END`. A constant
    code is 5 bytes. SM.END in `pyuxc/uxc_stmt.py`. New test `tests/ERRENDSTR` (`END "B"`, TYPE
    MISMATCH). The case `pyuxc/cases/EXERRENDX` (`END 5`, once SYNTAX ERROR) is removed; a copy
    is in the session scratchpad `removed/`. `compare.py` compares the template table with
    golden's record by record, by name, so moved ids do not warn: 571 MATCH, 1 NO GOLDEN before
    ERRENDSTR was added.
  - Trap: a `#rec` fixup holds the target id in one byte. The table has 252 records.
  - `monitor.s`: `RUN` ends with CR LF before the prompt, as `G` does and as MS-DOS `COMMAND`
    does (`CRLF2`). 3 bytes less ROM. The UXCBASIC `tests.py` strips line ends before the prompt,
    so its goldens did not change.
  - New test `tests/ENDCODE.S`: exec `tests/com/ENDCHILD.UXB` with tails A to E; codes 0, 20,
    253, 30 (END in a SUB), 8. `tools/tests.py` compiles `tests/com/*.UXB` too.
  - Goldens regenerated: a blank line after `RUN` and `G` in 11 tests; `DIRS` FREE 1 less,
    `FILES` lists `ENDCHILD.COM`, and `DISK`'s find state shows the next entry index, all from
    `ENDCHILD.COM` on the card. All 16 tests ok, each under 1 s. Build 1.96 s with 3 UXB
    recompiled.
  - Still to do, each a small step: help topic `END` and the Targets bullet in
    `help/UXC-HELP.md`; the UXCBASIC plan §5 item marked done, plus two new items (a run-time
    error exits with code 0; a second `JMP S_EXIT` follows a final `END`, 3 bytes, after the
    port); `pyuxc/README.md` line on the table warning; UXCBASIC HANDOFF; PLAN §10 on
    `tests/com/*.UXB`.
- A run-time error exits with code 0: the user accepts it (2026-10-15).
- Docs are updated every 3 or 4 steps, not after each step (user, 2026-10-15). HANDOFF still
  follows each step.
- Screen and prompt step (user, 2026-10-15):
  - `console.s`: the screen is 80 by 30. `ROWS` is 30; `VERA_DC_VSCALE` is `$40` (2 to 1 down,
    `lsr a` from the HSCALE `$80`, 1 byte). The font stays 8 by 8.
  - `monitor.s`: the prompt is `>>`. `LINE_MAX` is 79, the prompt then 78 characters. `error`
    puts X + 2 spaces before `^ Error`. ROM: +4 bytes. CODE and RODATA end at `$E9E7`.
  - Goldens: all 16 regenerated; each diff was only the prompt and the caret one column right.
  - UXCBASIC `tests.py`: `PROMPT = ">>"`, `RUN_LINE = PROMPT + "RUN TEST.COM"`. `ARRAY1` ok
    0.5 s there; its full suite not run.
  - `SHOW.COM` with no tail prints `NO FILE`, as written; with a name, in either case, it works.
  - `build/SD.IMG` was not rebuilt: the user's x16emu window held it open. The ROM was linked.
    The build time was not taken.
- Tests after the screen and prompt step: all 16 ok, one at a time, each under 1 s; and a full
  suite run, 16 ok, 8.9 s.
- Step 6e part 1 is done (user, 2026-10-15): the KERNAL entries leave the ROM.
  - `src/asm/compat.s` and `tests/KERNAL.*` are gone; a copy is in the session scratchpad
    `removed6e/`. Gone with them: the file entries, the command channel, `GETIN`, `PLOT`,
    `screen_set_charset`, `LKUPLA`, `READST`, the PSP's `$0730–$0745`, `con_direct`,
    `chrin_next`, `con_getin`, `con_edit` (folded into `api_con_line`), `handle_end`.
  - `console.s` holds the two entries x16emu needs, segment `KERNALJUMPS` from `$FFCF`:
    `CHRIN` is `jmp con_in`, `CHROUT` is `jmp con_out`. They are not API. `api_con_cursor`
    is the routine `con_plot` was.
  - `gate.s` no longer writes `$0372`. `mem.inc` drops `KERNAL_MODE`, `CON_LINE` (now
    `MONITOR_LINE = $0200`) and the PSP channel names. Call 16 stays reserved in `tools/api.py`:
    "Free: the next new call takes it", so calls 17 on keep their numbers.
  - ROM: CODE and RODATA end at `$E762`, was `$E9E7`: 645 bytes less. Kernel zero page
    `$80–$F4`; kernel RAM `$0600–$06AE`.
  - UXCBASIC's tests `ASM1`, `ASM2`, `SYS1`, `DIMAT` still call `$FFD2`, which still works.
- Build after 6e part 1: 0.67 s, the new baseline. `build/SD.IMG` was written.
- Tests after 6e part 1, one at a time, all 15: `BOOT` ok 0.6 s, `MONITOR` 0.4, `ASK` 0.4,
  `HANDLES` 0.4, `EXEC` 0.7, `ENDCODE` 0.5, `DOSAPI` 0.5, `TARGET` 0.5, `FILES` 0.4, `DISK`
  0.4, `DUP` 0.4, `CWD` 0.4, `DIRS` 0.7, `SEEK` 0.4, `WRITE` 0.6. No golden changed. UXCBASIC
  there: `ASM1` 0.5, `ASM2` 0.5, `SYS1` 0.6, `DIMAT` 0.5, `EXPR2` 0.5, `POINTER` 0.5, `ARRAY1`
  0.5, all ok.
- Step 6e part 2 is done (2026-10-15): UXCBASIC's tests no longer call `$FFD2`.
  - `ASM1`, `ASM2`, `DIMAT` and `SYS1` moved to `pyuxc/cases`, where they still match their
    GPC golden. Their copies in `tests/` call `con_out` at `$03B8`: `ASMBYTES`, `ASMOPS`,
    `DIMADDR`, `SYSREGS`, the old `.OUT` files renamed. An `ASM` call saves X and Y around it,
    since the API changes them.
  - `ERRSYS` keeps `SYS $FFD2`: it does not compile, so it never runs.
  - Tests: `ASMBYTES` ok 0.8 s, `ASMOPS` 0.5, `DIMADDR` 0.5, `SYSREGS` 0.5. `compare.py` on the
    8 names: 4 MATCH, 4 NO GOLDEN.
- Step 6e part 3 is done (2026-10-15): UXCBASIC's tests no longer write the sector buffer.
  - `EXPR2` and `POINTER` moved to `pyuxc/cases`, where they still match their GPC golden. Their
    copies in `tests/` are `EXPRPEEK` and `POINTERS`, the old `.OUT` files renamed.
  - `EXPRPEEK`, `POINTERS`, `DIMADDR` and `SYSREGS` use `$9E00–$9E11`, the top of program RAM,
    in place of `$0400–$0411`.
  - `ERRATKIND` keeps `AT $0400`: it does not compile, so it never runs. `RECORD1` only reads
    the PSP at `$0700`.
  - Tests: `EXPRPEEK` ok 0.7 s, `POINTERS` 0.6, `DIMADDR` 0.5, `SYSREGS` 0.5. `compare.py` on the
    4 names: 2 MATCH, 2 NO GOLDEN.
- Step 6e part 4 is done (2026-10-15): `RECORD2` moved to `pyuxc/cases`, where it still matches
  its GPC golden. Its copy in `tests/` is `RECSTR`, with `RECORD2.OUT` and `RECORD2.IN` renamed.
  `RECSTR`'s `F` record and its two `POKE`s use `$9E00–$9E01` in place of `$0600–$0601`, the
  kernel variables. Tests: `RECSTR` ok 0.7 s. `compare.py` on `RECORD2` and `RECSTR`: 1 MATCH,
  1 NO GOLDEN.
- Step 6e part 5 is done (2026-10-15), and with it step 6e: `ZP_MODE` (`$27`) in UXCBASIC's
  `tpl/ZP.ASM` is defined only when `UXDOS == 0`. The stock table's `S_INIT` and `S_EXIT` use
  it; the 6502DOS table does not, so `$27` is free there. `MKTPL.PY` 0.28 s; both tables are byte
  for byte the same as before, so no test ran.
- Docs step done (2026-10-15); no docs are owed:
  - UXCBASIC `help/UXC-HELP.md`: a new topic `END`, linked from Control and Targets; the Targets
    bullet gives the exit code. `help/MKHELP.PY` rebuilt `help/HELP-TXT/`: 33 topics, 0.16 s.
    The copies in UXCBASIC's `disk/` and `build/` were not refreshed.
  - UXCBASIC plan §5: `END [code]` marked done, with the run-time error's code 0 and the 3 bytes
    of `JMP S_EXIT` after a final `END` (after the port). Its test names are the new ones.
  - UXCBASIC `pyuxc/README.md`: `compare.py` names the changed records, matched by name.
  - UXCBASIC HANDOFF: 156 tests, the prompt `>>`, the seven copies, `ZP_MODE`, `END [code]`.
    `compare.py` run for it: 571 MATCH, 9 NO GOLDEN of 580, 2.2 s.
  - `tools/api.py`: `con_cursor` says 30 rows. `tools/genapi.py` 0.11 s; `api.s` and `api.inc`
    unchanged, only `docs/API.md`.
  - `CLAUDE.md`: the `$0372` line says only UXCBASIC's stock table uses it.
  - PLAN: 6d's `END code`; 6e's checklist is now the table of moved tests, `ERRSYS`,
    `ERRATKIND` and `ZP_MODE`. PLAN is up to date.
- `END` range (2026-10-15): a constant exit code outside 0 to 255 stops the compile with
  `EXIT CODE OUT OF RANGE`, in `sm_end` in UXCBASIC's `pyuxc/uxc_stmt.py`. The check is at
  compile time: 0 ROM bytes, 0 cycles. A variable's code is still its low byte. New test
  `ERRENDRANGE` in UXCBASIC's `tests/`. `tests/com/ENDCHILD.UXB` here says `END 253`, not
  `END -3`.
- Full suite (2026-10-15), after the `END` range step: 6502DOS 15 ok, 8.1 s, slowest `ASK`
  0.9 s; UXCBASIC 157 ok, 37 s, slowest `EXPR1` 0.6 s. `compare.py`: 571 MATCH, 10 NO GOLDEN
  of 581, 1.6 s.
- The shell is a small BASIC (user, 2026-10-15). The design is in PLAN section 8, from the
  user's `docs/1st run - new shell.txt`; PLAN section 11 step 7 has its parts 7a to 7i. The
  user's choices:
  - One shell, still `CMDSHELL.COM`. `CMDBASIC`, `.BAT`, `AUTOEXEC.BAT` and `!SHELL=` are gone.
  - Commandlets are `.CBIN`, the `.COM` format. A name is looked for as `.CBIN`, `.COM`, `.CMD`.
  - `A` to `Z` and the slots `P1` to `P9` are `WORD`. Strings are 80 characters at most.
  - The slots lie in RAM bank 0 at `$A400`, 747 bytes, reached by two new calls, `slots_get`
    and `slots_put`. They are asm: ask before writing them.
  - A `.CMD` script loads whole into a RAM bank. A script run by name ends its caller.
  - `RUN name` ends the script, then runs `name`.
  - `IF` has no `THEN` and no `ELSE`: one statement after the condition, or a block to `ENDIF`.
  - Redirection is the words `TO`, `APPEND`, `FROM`; the pipe `|` stays. Script arguments and
    `-` options stay.
  - `STARTUP.CMD` runs at boot.
  - A number prints with no spaces around it: `PRINT 42` gives `42`.
  - Number expressions: `+ - * /`, brackets and a unary minus. The six comparisons work only in
    `IF`. No `MOD`, `AND`, `OR` or `NOT`.
  - Strings join with `+`. The six comparisons work on strings, in `IF`.
  - A file argument is a string expression when it starts with a quote, `A$` to `Z$` or
    `CURDIR$`; any other word is text up to a space. `MKDIR A` makes the directory `A`.
  - `COPY` takes `*` and `?` and copies into a directory. `FILES` prints as the monitor's `DIR`.
    `CURDIR$` is `C:\DOCS`, and `C:\` at the root.
  - Still open, in PLAN section 13: the script's bank before `bank_alloc`, system variables in
    the environment, `END`'s exit code.
- Trap for 7b: UXCBASIC has no string arrays and no recursion; SUBs cannot call each other in a
  loop. `A$` to `Z$` go in one byte array; expressions need an explicit stack, not recursive
  descent.
- Step 7a, redone (2026-10-15): `src/bas/CMDSHELL.UXB`, 3616 bytes as a COM file. It reads a
  line with `DOS.CON_LINE` at the prompt, the drive letter and `>`, and runs `PRINT`, `CLS`,
  `VERSION` and `END`. `VER`, `ECHO` and `EXIT` are gone.
  - A cursor walks `LINE_TEXT`: `CURRENT_CHAR`, `SKIP_SPACES`, `READ_NAME` (a letter, then
    letters, digits and `$`, in capitals).
  - `PRINT` takes items separated by `;`: a quoted string, which may lack its closing quote, or
    a whole number. A `;` at the end keeps the line. UXCBASIC prints a number with a space
    before and after: `PRINT 42` gives ` 42 `.
  - A bad item, or text after `CLS`, `VERSION` or `END`, prints `Syntax error` on a line of its
    own. An unknown name prints `Bad command or file name`.
  - Golden files changed: `SHELL` (new `.IN`); `FILES`, `DIRS` and `DISK` were stale since the
    first 7a put `CMDSHELL.COM` on the test card: `FILES` lists it, `DIRS` FREE is 4 less,
    `DISK`'s F33 state holds cluster `$2C`, and X after a failed open is `$04`, a leftover.
- Build after 7a: 4.24 s cold, the first of the session; 0.43 s warm, the new baseline.
- Tests after 7a, one at a time: `SHELL` ok 0.4 s, `FILES` 0.4, `DIRS` 0.8, `DISK` 0.4.
- Step 7b (2026-10-15): `CMDSHELL.COM` is 6532 bytes.
  - `name = expression`, `INPUT name`, `PRINT` of expressions separated by `;`.
  - `A` to `Z` are `NUMBER_VARIABLES(26) AS WORD`. `A$` to `Z$` are `STRING_VARIABLES(2106)`,
    81 bytes each, read and written with `ContentsAt`.
  - `EVAL_NUMBER` works the order of the operators and the brackets with two stacks of 16,
    `OPERATOR_STACK` and `VALUE_STACK`. A 17th open operator is a syntax error.
  - `EVAL_STRING` joins quoted strings and string variables into `STRING_RESULT`, 255 at most;
    a store cuts it to 80.
  - Errors: `Syntax error`, `Type mismatch`, `Division by zero`. Each prints on a line of its
    own and sets `FAILED`, which stops the statement.
  - A number after `+` in a string, as `N$ + 1`, and `A$ = 5`, give `Syntax error`, not
    `Type mismatch`.
  - Trap: UXCBASIC names are 16 characters at most; `build.py` exits 0 when a compile fails.
  - Golden files changed: `SHELL`; `FILES` (the size); `DIRS` FREE 3 less; `DISK` F33 cluster
    `$2F`.
- Build after 7b: 0.82 s with the shell compile, the new baseline.
- Tests after 7b, one at a time: `SHELL` ok 0.4 s, `FILES` 0.4, `DIRS` 0.8, `DISK` 0.4.
- Step 7c (2026-10-15): `CMDSHELL.COM` is 9817 bytes, 3285 more.
  - `FILES [pattern]`: the monitor's `DIR` format, 23 columns, then `N File(s)`. A directory's
    name lists the names in it; no pattern lists the current directory. Sizes are `ULONG`.
  - `LIST file` writes the file to handle 1 through `COPY_BUFFER`, 1024 bytes, and adds a new
    line when the file does not end in a line feed.
  - `COPY from to`: one `FINDFIRST` loop for one file or many. `to` is a directory when it ends
    in `\`, `/` or `:`, or names one; then each file keeps its name. A wildcard with a file `to`
    gives `Target must be a directory`. It prints `N File(s) copied`. A drive that fills gives
    `Insufficient disk space`.
  - `DELETE`, `RENAME`, `MKDIR`, `RMDIR`, `CHDIR`: one call each. An API error prints the
    kernel's message from `DOS.ERRMSG`.
  - `CURDIR$` is read only: `CURDIR$ = "X"` gives `Syntax error`.
  - Trap: `COPY` onto the same file, as `COPY A.TXT .\A.TXT`, empties it. The shell does not
    compare the two paths.
  - `DELETE` takes no wildcard.
  - Byte saving applied: `LAST_ARGUMENT` and `END_SEARCH` share the argument end and the count
    line, 64 bytes.
  - New test `SHFILES`. Golden files changed: `FILES` (the size); `DIRS` FREE 3 less; `DISK`
    F33 cluster `$32`.
- Build after 7c: 0.75 s with the shell compile, the new baseline.
- Tests after 7c, one at a time: `SHFILES` ok 0.7 s, `SHELL` 0.5, `FILES` 0.4, `DIRS` 0.8,
  `DISK` 0.4.
- Steps since the last full suite: 6. It ran after the doc batch for `TREE` to `TAIL`,
  2026-10-18: 43 tests, 1 failed (`TREE`, below), 27.4 s, the longest `CMDLETS` 1.7 s.
- UXCBASIC: 174 tests, 0 failed, 43 s. `compare.py`: 566 MATCH, 5 RESULT, 31 NO GOLDEN of 602,
  1.7 s. The RESULTs are `STRLR`, `STRNS`, `EXERRCONSTSTR`, and the two below, all expected:
  `EXERRPOS` (`POS(2)`) now compiles, and `EXERRPOSVAR` says `POS NEEDS 0 TO 3`.
- VARBANK step (2026-10-15): string heaps with GC, in `src/asm/strings.s`, 553 bytes. Not yet
  in PLAN or `DOS.UXI`.
  - Calls: 16 `str_alloc` (A length, r0 descriptor address; out A the heap's bank, r1 the length
    byte), 43 `str_free` (r0), 44 `str_gc` (out r0 free bytes), 45 `str_heap` (A bank, r0 the
    first block). Errors 8 and 9. Call 16 is no longer reserved.
  - A heap is one RAM bank: `HEAP_BUMP` `$A000`, `HEAP_FLOORS` `$A002`, a word for each exec
    depth 0 to 4, then the blocks. VARBANK is bank 21, the first after the save banks; no
    allocator exists, so it is fixed. VARBANK has 32 system descriptors at `HEAP_SYSTEM`
    `$A00C`, its blocks from `$A04C`.
  - Block: owner (2), length (1), text. Owner 0 is free. A descriptor holds the address of the
    length byte, so it points at a length-prefixed string. No level byte: the owner's address
    tells exit what to keep.
  - `PSP_HEAP`, `$0701`: the running program's heap bank. Boot and `exec` set it to VARBANK.
    `str_heap` with a bank above 21 makes that bank a new empty heap, all floors at r0.
  - `str_alloc` refuses a descriptor at `$0000-$0001`, `$9F00-$9FFF` or `$C000` up. A full heap
    runs GC once, then gives 8. A new string on a descriptor makes its old block dead: no free
    needed before a reassign. `str_free` of a 0 descriptor does nothing; one whose block does
    not point back gives 9.
  - GC: one pass from `floor[exec_depth]` to the bump pointer, 18 cycles a byte moved; a block
    that need not move is skipped. `exec` (`heap_exec`, after `handles_inherit`) sets the child's
    floor in VARBANK to the bump pointer. `exit` (`heap_exit`, after `handles_close`) runs GC on
    VARBANK where an owner below `$A000` is dead: it keeps the system strings and drops the
    child's.
  - Kernel zero page `$80-$FA`, 5 bytes left; kernel RAM to `$06B1`. CODE and RODATA end at
    `$E99D`.
  - Not done: `keep` (call 28) is not written, so its VARBANK rule waits. A program's own bank
    is not freed at exit until `bank_alloc` exists.
  - Trap: a GC inside `str_alloc` moves strings. A caller copying from a heap string must read its
    descriptor again after the call.
  - New test `HEAP` (`tests/HEAP.S`, child `tests/com/HEAPKID.S`). Its dumps stop where banked
    RAM holds bytes no block wrote: x16emu fills banked RAM with random bytes.
  - Golden files changed: `EXEC` and `ENDCODE` (X after `exec` is `$02`, a leftover, was `$FF`);
    `FILES` (`HEAPKID.COM`, 17 files), `DIRS` FREE 1 less, `DISK` (F33 state, X after a failed
    open).
- Build after the VARBANK step: 0.41 s.
- Tests after the VARBANK step, one at a time: `HEAP` ok 0.4 s, `EXEC` 0.7, `ENDCODE` 0.5,
  `BOOT` 0.4, `DOSAPI` 0.6, `DIRS` 0.8, `FILES` 0.4, `DISK` 0.4, `HANDLES` 0.4.
- Shell strings step (2026-10-15): the shell's strings are on VARBANK. `CMDSHELL.COM` is 10390
  bytes, 573 more; its BSS is 2054 bytes less.
  - Choices: `A$` to `Z$` have their descriptors in the shell's RAM, `STRING_VARIABLES(26) AS
    UWORD`. `P1$` to `P9$` are VARBANK's system descriptors 0 to 8, so they outlive a program.
    The number slots `P1` to `P9` are dropped; a program's error goes back in its exit code.
    Strings hold up to 255 characters.
  - `lib/HEAP.UXI`: the heap calls, in `NAMESPACE HEAP`, after `#INCLUDE "DOS.UXI"`:
    `STR_ALLOC`, `STR_FREE`, `STR_GC`, `STR_HEAP`, `STR_SET` (descriptor, text), `STR_READ`
    (into `DOS.CALL_TEXT`), `STR_GET`. Inside it, the names of `DOS.UXI` take `DOS.`:
    `DOS.REG_A`, `DOS.R0`, `DOS.ERROR`. A separate file because pyuxc links every SUB of an
    include: in `DOS.UXI` they added 520 bytes to each of the 7 test programs.
  - `STR_SET` and `STR_READ` select the bank in `PSP_HEAP` at `$00`, and restore the caller's.
  - `tools/uxb.py` rebuilds a program when any `src/bas` file it includes is newer.
  - Shell: `NAME_KIND` takes `P1$` to `P9$`; `DESCRIPTOR_OF()` gives a string variable's
    descriptor. `DO_ASSIGN` and `DO_INPUT` take it before `EVAL_STRING` changes `NAME_TEXT`.
    A full heap prints `ERRMSG(8)`.
  - New test `SHVARS`: 195 characters, `P1$` to `P9$`, `P0$` and `P10$` errors, 40 assigns that
    overrun the heap so GC runs. Golden files changed: `FILES` (the size), `DIRS` FREE 1 less,
    `DISK` F33 cluster `$34`.
  - PLAN sections 2, 8, 10 and 13 follow the step: `HEAP.UXI`, the rebuild rule, string
    file arguments, the open question of reading an exit code.
- Build after the shell strings step: 0.70 s, the new baseline.
- Tests after the shell strings step, one at a time: `SHVARS` ok 0.5 s, `SHELL` 0.4,
  `SHFILES` 0.6, `FILES` 0.5, `DIRS` 0.4, `DISK` 0.4.
- Step 7d (2026-10-15): the shell runs programs by name. `CMDSHELL.COM` is 11586 bytes, 1196
  more.
  - A line whose first name is no statement runs a program: the word up to the first space is
    the name. `RUN name` takes the name as a file argument, so `RUN "TO" + "OL"` works, and it
    skips the statement names: `RUN FILES` looks for a program.
  - `FIND_PROGRAM`: a name with `*` or `?` finds none. A name with an extension is taken as
    typed, else `NAME.CBIN`, then `NAME.COM`. A name with a directory is looked for there
    only; any other in the current directory, then in each directory of `PATH$`, split at `;`,
    empty parts skipped, a `\` added when missing. `.CMD` waits for 7e. Not found prints `Bad
    command or file name`.
  - `RUN_PROGRAM`: frees `P1$` to `P9$`, then reads each argument with `READ_ARGUMENT` (a string
    expression or a word) into the next slot, up to 9, and onto the tail after a space. Then
    `DOS.EXEC`; its error prints `ERRMSG`. The exit code is not read.
  - `PATH$` is VARBANK system descriptor 9, `DOS.PATH_STRING` `$A01E` in `HEAP.UXI`. `NAME_KIND`
    and `DESCRIPTOR_OF` take it, so `PATH$ = "C:\BIN"` sets it until `SETSYS` (7f).
  - `READ_WORD` split out of `READ_ARGUMENT`. `CLS`, `VERSION` and `END` each call
    `EXPECT_END`.
  - pyuxc's name limit: the shell needs 525 names, past the 496 of `TOO MANY NAMES`. In
    `UXCBASIC/pyuxc/uxc_defs.py` `K_SYM_BANKS` is 4 and `K_SY_MAX` 1008; the output is
    the same. UXCBASIC HANDOFF notes it. Of the 525: 178 hidden `%C` call records, 161
    variables, 74 SUBs, 74 constants, 30 temps. `DOS.UXI` and `HEAP.UXI` give 223.
  - New test `SHRUN`, child `tests/com/SLOTKID.UXB`: it prints its tail, `P1$`, `P2$`, `P9$`
    and `PATH$`, sets `P1$` to `DONE`, frees `P2$`, ends with code 5. Golden files changed:
    `FILES` (the size, `SLOTKID.COM`, 18 files), `DIRS` FREE 5 less, `DISK` F33 cluster `$35`.
- Build after 7d: 2.2 s, the ROM rebuilt too (2.1 s); the shell compile 0.2 s. New baseline 2.2 s.
- Full suite after 7d: 20 tests ok, 9.7 s, slowest `SHRUN` 0.8 s, `EXEC` 0.7.
- Step 7e is split in three: 7e1 scripts that run line by line, 7e2 labels, `GOTO`, `GOSUB` and
  `RETURN`, 7e3 `IF` and `ENDIF`, `REPEAT` and `ENDREP`.
- Step 7e1 (2026-10-15): scripts. `CMDSHELL.COM` is 12885 bytes, 1299 more.
  - `FIND_IN` tries `NAME.CMD` after `NAME.COM`. `RUN_PROGRAM` changes the name to capitals,
    fills the slots as for a program, then calls `LOAD_SCRIPT` when the path ends in `.CMD`.
  - `LOAD_SCRIPT`: reads the whole file into bank 22 (`SCRIPT_BANK`) at `$A000`, the caller's
    bank selected again after the read. The kernel's `file_copy` writes with the caller's bank
    selected, so `READ_FILE` into `$A000` works. A file past 8192 bytes gives `Insufficient
    memory` (error 8). The script that ran it ends, also when the load fails.
  - `SCRIPT_NEXT` is the next line's address, `SCRIPT_END` the address past the last byte; a
    script runs while `SCRIPT_NEXT < SCRIPT_END`. `READ_SCRIPT_LINE` copies a line into
    `LINE_TEXT`: it ends at LF, a CR is dropped, it is cut at 127 characters. Lines are not
    echoed.
  - The main loop sets `IN_SCRIPT` for a script line. An error in a script line prints `in
    PATH line N` after the message and ends the script, unless `ONERROR(1)`.
  - `ONERROR(1)` and `ONERROR(0)` (`DO_ONERROR`): the argument is a number expression, and
    `RESUMING` takes its low byte. Every load starts with `ONERROR(0)`. At the prompt it has no
    effect.
  - `END` in a script ends the script; at the prompt it ends the shell. `RUN` ends the script,
    then runs the name.
  - `STARTUP.CMD` in the root of the current drive runs when the shell starts, nested shells
    included. (Since the boot drive step: `C:\STARTUP.CMD`.) It gets no arguments; the slots stay as they are.
  - Trap: bank 22 is fixed. A child that writes it, such as a child `CMDSHELL` running a
    script, overwrites the parent's script.
  - New test `SHSCRIPT` with the scripts in `tests/sd/SCRIPTS`: CR LF and LF lines, a last line
    with no LF, an error, `ONERROR`, a chain to another script, `RUN` and `END` in a script,
    an empty script, `BIG.CMD` of 8193 bytes, `STARTUP.CMD` in a nested shell. Golden files
    changed: `FILES` (the size, `SCRIPTS`, 19 files), `DIRS` FREE 20 less, `DISK` F33 cluster
    `$36`.
- Build after 7e1: the shell compile 0.2 s, the ROM 1.05 s; `build.py` rebuilt the ROM again.
  The total was not measured (`bc` is missing); about 1.3 s, the new baseline.
- Tests after 7e1, one at a time: `SHSCRIPT` ok 0.8 s, `SHRUN` 0.8, `SHELL` 0.5, `SHVARS` 0.6,
  `SHFILES` 0.6, `FILES` 0.4, `DIRS` 0.8, `DISK` 0.5.
- `ONERROR(N)` (2026-10-15) replaces `ON ERROR RESUME NEXT` and `ON ERROR STOP`. It reuses
  `EVAL_NUMBER`, so `CMDSHELL.COM` is 12731 bytes, 154 less. `ON_ERROR` would cost 23 bytes
  more, since `READ_NAME` does not take `_`. `RESUME.CMD`, `SHSCRIPT.IN`, `SHSCRIPT.OUT` and the
  size in `FILES.OUT` changed. Build 0.73 s, the new baseline. Tests: `SHSCRIPT` ok 0.7 s,
  `FILES` 0.4, `DIRS` 0.9, `DISK` 0.5.
- Docs step (2026-10-15); no docs are owed:
  - The VARBANK docs and UXCBASIC's `END` docs were already in place: PLAN sections 3, 4 and 7,
    `HEAP.UXI` in section 2, `END 253` in UXCBASIC's help topic `END` and plan §5.
  - PLAN section 3: bank 22 is the shell's script, banks 23 and up the environment and the
    allocator; VARBANK's system descriptors 0 to 8 are the slots, 9 is `PATH$`.
  - PLAN section 8: `ONERROR(n)` in the Flow row; `PATH$` is descriptor 9. Running a name has
    the 7d rules: the first word, `RUN`, capitals, wildcards, the extension order, the
    directory search, the error, the slots and the tail. A new subsection Scripts has the 7e1
    rules, with the bank 22 trap.
  - PLAN section 11: 7e is split in 7e1, 7e2 and 7e3. Section 13: the script bank question is
    replaced by whether each shell takes its own script bank, and whether `STARTUP.CMD` comes
    from the boot drive. Descriptors 10 to 31 are open.
- Boot drive step (2026-10-15): `STARTUP.CMD` is read from `C:\STARTUP.CMD`, the boot drive,
  in place of the current drive's root. `C:` is the only boot drive. `CMDSHELL.COM` is 12692
  bytes, 39 less: the `CHR$` and `DOS.GETDRIVE` call are gone. `FILES.OUT` size changed. Build
  0.76 s, the new baseline. Tests: `SHSCRIPT` ok 0.9 s, `FILES` 0.5, `DIRS` 0.8, `DISK` 0.5.
  - Docs owed: PLAN section 8 Scripts (`STARTUP.CMD` in the root of `C:`), section 13 (the boot
    drive question is answered).
  - The script bank question is closed by the DOS-way step.
- DOS-way step (2026-10-15): a script is read as MS-DOS 2.0 reads a batch file (its
  `TCODE3.ASM` `BATOPEN`, `TCODE5.ASM` `GETBATBYT`): no script bank. Bank 22 is free.
  - `START_SCRIPT` (was `LOAD_SCRIPT`) keeps the full path in `SCRIPT_PATH`: a path without a
    drive takes the current drive and directory, so a `CHDIR` in the script keeps its file.
    `C:NAME.CMD` is kept as it is (trap comment). The position is `SCRIPT_HIGH:SCRIPT_LOW`.
    `SCRIPT_ACTIVE` is set while a script runs; `SCRIPT_NEXT`, `SCRIPT_END`, `SCRIPT_BANK`
    are gone.
  - `READ_SCRIPT_LINE`: opens, `DOS.SEEK`s, reads 128-byte chunks into `COPY_BUFFER` up to
    the LF, adds the bytes taken to the position, closes. The end of the file ends the script
    after its last line runs. An open or read error is reported, the line is empty, and the
    script ends. The 8 KB limit is gone.
  - Measured with a scratch program, 100 open, seek, read 128, close: `C:\SCRIPTS\HELLO.CMD`
    at 0, 0.55 ticks a line, about 9 ms; `\DOCS\LONG.TXT` at 0, 0.50; at 3000, 0.91 (the FAT
    walk after a seek); `BIG.CMD` at 8000, 0.68. A line from the bank cost almost nothing.
  - `tests/sd/SCRIPTS/BIG.CMD` is rewritten, still 8193 bytes so free space is unchanged:
    `CHDIR \DOCS`, a line cut at 127 characters that crosses a 128-byte chunk, `CHDIR \`, `END`,
    then padding. `SHSCRIPT.IN` runs it as `SCRIPTS\BIG` (a relative path).
  - `CMDSHELL.COM` 13011 bytes, 319 more than 12692 (13110 before the drive-path cut, 99
    saved). Build 0.65 s, the new baseline. Tests: `SHSCRIPT` ok 1.0 s, `FILES` 0.4 (size
    changed), `DIRS` 0.8, `DISK` 0.5.
  - A read-ahead buffer of the script's own is on the to-do list (Next item 2).
  - Docs owed: PLAN section 3 (bank 22 is free), section 8 Scripts (the DOS way, the full
    path, no size limit, the edit-while-running trap), section 13 (the script bank question
    is closed).
- `PSP_TOP` step (2026-10-15, approved with its asm): `exec` saves only the parent's used RAM.
  - `PSP_TOP` = `$0702` (`mem.inc`): the last page `exec` saves. Boot and `tail_copy` (for
    the child) set it to `>PROGRAM_END`. `parent_copy` copies from `PSP` while the page just
    copied is below `PSP_TOP`, and stops at `PROGRAM_END` whatever `PSP_TOP` holds. The copy
    back restores the PSP first, so `PSP_TOP` is the parent's from the second page on.
  - The init went into `tail_copy`: in `api_exec` the first `bcs @no_memory` fell out of range.
  - ROM +16 bytes: boot 5, `tail_copy` 5, `parent_copy` 6 (the clamp). ROM bank 0 ends at
    `$E9AD`, 5665 bytes free before `KERNALJUMPS`.
  - UXCBASIC: a new template `T_TOP` at the end of `tpl/UXC.TPL.ASM` (`#hi lda, S0` /
    `sta $0702`), record 252 in both tables. `lk_link` emits it after `sb_pools` for the
    6502DOS target only, with S0 = the BSS end (`lk_bss + bs_n`): its high byte is the page
    of the last byte, or one page more when the end is page-aligned. The stock output and
    the goldens are unchanged. A program grows 5 bytes, 6 when it had no startup work (the
    `BIT` turns back into `JSR`, plus `RTS`). The GPC compiler's `TPL.COUNT` check now fails
    against the new table; GPC is frozen.
  - The shell stores `$56` (its end is `$5600`, aligned): 80 pages copied in place of 152,
    each way. 72 pages x 256 bytes x about 16 cycles x 2 is about 590,000 cycles, about 74 ms
    a run at 8 MHz (counted, not timed). `ARGS` stores `$0A`, `SHOW` `$0D`.
  - Trap to document: a program that writes RAM above its top page, by `POKE` or
    `ContentsAt`, loses it across an `exec`.
  - Build 1.02 s with all four COMs recompiled, the new baseline. Tests: `EXEC` ok 1.2 s,
    `SHSCRIPT` 0.9, `SHRUN` 0.8, `FILES` 0.5 after its 13 sizes were raised (+5, `ENDCHILD`
    +6). The UXCBASIC tests were not run.
  - Docs owed: PLAN section 7 (the PSP table, the `exec` copy, the trap); UXCBASIC's
    `UXCBASIC.PLAN.md` or help on the startup store.
- Step 7e2 (2026-10-16): labels, `GOTO`, `GOSUB`, `RETURN`. `CMDSHELL.COM` is 14219 bytes,
  1203 more than 13016.
  - `NAME:` alone on a line is a label; it does nothing when it runs. A label has 2 characters
    at least: one letter and a colon is a drive, as in `C:\BIN\TOOL 4` (SHRUN caught it). `D:`
    alone still gives `Bad command or file name`. Text after a label's colon is a syntax error.
  - `READ_OPEN_LINE(HANDLE)` is the line reader split out of `READ_SCRIPT_LINE`: it seeks to the
    script position, reads the line, counts it in `SCRIPT_LINE`, and returns 10 when an LF ended
    it. `CLOSE_KEEP_ERROR` closes and keeps `DOS.ERROR`.
  - `DO_GOTO`: reads the label into `SEARCH_DIRECTORY`, keeps the position in `BACK_LOW`,
    `BACK_HIGH`, `BACK_LINE`, opens the script once and reads lines from 0 (a seek a line) until
    a line is `NAME :` with the name. Spaces may come before the name and the colon; text after
    the colon is not checked in the scan. Found: `SCRIPT_ACTIVE` is set again, since a `GOTO` on
    a last line with no LF had cleared it. Not found: `Label not found`, the position put back,
    so the error's line number is the `GOTO`'s and `ONERROR(1)` goes on after it.
  - `DO_GOSUB` pushes the `BACK_` position after a good `DO_GOTO`. The stack holds 16
    (`GOSUB_SIZE`; `GOSUB_LOW`, `GOSUB_HIGH`, `GOSUB_LINE`, 96 bytes of BSS); a 17th gives
    `ERRMSG(8)`, `Insufficient memory`. `DO_RETURN` pops; an empty stack gives `RETURN without
    GOSUB`. `START_SCRIPT` empties the stack.
  - At the prompt `GOTO`, `GOSUB` and `RETURN` check their syntax, then do nothing.
  - New test `SHGOTO`, scripts `GOTO.CMD`, `GOSUB.CMD`, `NOLABEL.CMD`, `DEEP.CMD` in
    `tests/sd/SCRIPTS`. Golden files changed: `FILES` (the size), `DIRS` FREE 5 less, `DISK`
    F33 cluster `$37`.
  - Docs owed: PLAN section 8 (the label rules; "the shell finds a script's labels once, at
    load" is wrong now: `GOTO` scans the file), section 11 (7e2 done).
- Build after 7e2: 0.73 s, the new baseline.
- Tests after 7e2, one at a time: `SHGOTO` ok 0.7 s, `SHRUN` 0.9, `FILES` 0.4, `DIRS` 0.8,
  `DISK` 0.4, `SHSCRIPT` 0.8, `SHELL` 0.5.
- Size pass after 7e2 (2026-10-16): `CMDSHELL.COM` is 14063 bytes, 156 less. Each change was
  measured alone by compiling a variant with pyuxc (`DIM` storage is not in the file).
  - `DO_GOTO`: a label shorter than 2 sets `CURSOR = 1`, so `EXPECT_END` reports the syntax
    error (-25). The label goes in `SEARCH_DIRECTORY`, free outside `FIND_PROGRAM`, and
    `LABEL_TEXT` is gone (-3, 128 bytes of BSS). Not found: `REPORT_DOS(DOS.ERROR)`, then
    `Label not found` when `FAILED` is 0 (-3). `IF DOS.ERROR THEN EXIT DO` (-2).
  - `IF FAILED OR IN_SCRIPT = 0 THEN RETURN` is two `IF`s in `DO_GOTO`, `DO_GOSUB`,
    `DO_RETURN` (-11 each).
  - `DO_GOSUB` full: `REPORT_DOS(DOS.ERR_NO_MEMORY)` (-37). `STORE_STRING`:
    `REPORT_DOS(DOS.ERROR)` (-47).
  - `IF DOS.ERROR <> 0 THEN RETURN` drops the `<> 0` in `IS_DIRECTORY` and twice in
    `COPY_HANDLE` (-6).
  - Measured and not taken: three `GOSUB_` slots in place of `BACK_` (+72; an array access
    costs about 12 bytes); `OR` split in a `RETURN 1` test (+3 to +6); one close path in
    `DO_GOTO` (+3). Open: `RETURN without GOSUB` as `Syntax error` saves 22.
  - Pyuxc compiles `IF A OR B = 0` larger than two `IF`s; `IF X <> 0` 2 bytes larger than
    `IF X`.
  - Build 0.83 s (compile 0.2, ROM 0.63), the new baseline.
  - Full suite: 22 tests, all ok after one golden update, 12.9 s. `DOSAPI` failed first: its
    `FIND *` now lists the `SCRIPTS` folder of 7e1. No test passed 5 s.
- Docs step (2026-10-16); no docs are owed. `RETURN without GOSUB` stays.
  - PLAN section 3: banks 22 and up are the environment and the allocator.
  - PLAN section 7: `PSP_TOP` in the PSP table; `exec` copies from the PSP to `PSP_TOP`; the
    trap of RAM written above it.
  - PLAN section 8 Scripts: the DOS-way read, the full path, no size limit, the edit trap,
    `C:\STARTUP.CMD`, the label, `GOTO`, `GOSUB` and `RETURN` rules. The bank 22 trap and "labels
    once, at load" are gone.
  - PLAN section 11: 7e1 no longer names a RAM bank. Section 12: `T_TOP`. Section 13: the script
    bank and boot drive questions are gone.
  - UXCBASIC: help topic Targets has the start-up page store (`MKHELP.PY` 0.14 s, 33 topics);
    its HANDOFF has `T_TOP` and the symbol limits.
- Step 7e3 is split in two: 7e3a `IF` and `ENDIF` with the six comparisons, 7e3b `REPEAT` and
  `ENDREP`.
- Step 7e3a (2026-10-16): `IF`, `ENDIF` and the comparisons. `CMDSHELL.COM` is 14674 bytes, 611
  more than 14063. The shell ends at `$5DD9` (pyuxc link values): 21976 bytes used, 16679 free
  of `$0801–$9EFF`. New BSS: `LEFT_TEXT` 256 bytes, `SKIP_DEPTH` 1, the locals of `DO_IF`.
  - `DO_IF` (a `FUNCT`): the left expression is a string when `IS_STRING_START` says so, else a
    number; a left string is kept in `LEFT_TEXT`. The comparison is read as bits, `<` 1, `=` 2,
    `>` 4, from any run of `<`, `=`, `>`; none is a syntax error. The right expression is of the
    same kind (else `Syntax error` or `Type mismatch`, as in an assignment). `RELATION` is 1, 2
    or 4; the condition holds when `MASK AND RELATION` is not 0. WORD compares are signed:
    `-1 < 0` holds.
  - With text after the condition `DO_IF` returns the result, and `RUN_LINE` runs the rest of
    the line as a statement: `RUN_LINE` is a `DO` loop, `IF DO_IF() THEN CONTINUE`, `RETURN`
    at the end. So `IF A=1 IF B=2 PRINT "X"` works; UXCBASIC has no recursion.
  - A condition alone on the line starts a block. In a script, a block whose condition fails
    sets `SKIP_DEPTH = 1`. While `SKIP_DEPTH` is not 0, `RUN_LINE` reads only the first name:
    `IF` runs `DO_IF` (a block adds 1), `ENDIF` takes 1; any other line is skipped. A taken
    block keeps no state: `ENDIF` outside a skip checks its syntax and does nothing, so a `GOTO`
    out of a block is safe. At the prompt a block `IF` does nothing.
  - While skipping, `REPORT_ERROR` sets `FAILED` and prints nothing, and `RUN_LINE` clears
    `FAILED`. A division by 0 divides by 1 instead, so a skipped `IF A/B=1` block still counts.
    Trap (comment on `DO_IF`): a skipped `IF` line with a syntax error opens no block.
  - `SKIP_DEPTH` is set to 0 at the prompt (main loop) and on a script read error
    (`READ_SCRIPT_LINE`), so the error prints. `START_SCRIPT` runs only when not skipping.
  - Measured and not taken: `ELSEIF` for the relation (+3), the mask read from `CODE - 59`
    (+0), the division guard folded into one `IF` (-1, it stores a quotient on the error path).
    The division guard costs 20 bytes, the quiet `REPORT_ERROR` 9.
  - New test `SHIF`, script `tests/sd/SCRIPTS/IF.CMD`: all six comparisons on numbers and
    strings, a signed compare, lower case, `IF` in `IF`, a taken block, a skipped block with a
    nested block, a skipped division by 0, a skipped single-line `IF` and a broken line, `GOTO`
    after `IF`, a script that ends inside a skipped block; at the prompt the errors and a block
    `IF`. Golden files changed: `FILES` (the size), `DIRS` FREE 2 less, `DISK` F33 `TXT8`.
  - Docs owed: PLAN section 8 (the `IF` rules: the block skip, nesting, the prompt, the trap),
    section 11 (7e3 split in 7e3a and 7e3b).
- Build after 7e3a: 0.72 s, the new baseline.
- Tests after 7e3a, one at a time: `SHIF` ok 0.5 s, `SHGOTO` 0.7, `SHSCRIPT` 0.8, `SHVARS` 0.6,
  `SHELL` 0.5, `FILES` 0.4, `DIRS` 0.8, `DISK` 0.5 (the last three after their golden update).
- Step 7e3b (2026-10-16): `REPEAT n` and `ENDREP`. `CMDSHELL.COM` is 15295 bytes, 621 more than
  14674. The shell ends at `$6069`: 22632 bytes used, 16023 free of `$0801–$9EFF`. New BSS:
  `FLOW_TIMES` 32 bytes and the locals.
  - The GOSUB stack is now the flow stack: `FLOW_LOW`, `FLOW_HIGH`, `FLOW_LINE`, `FLOW_TIMES`,
    `FLOW_COUNT`, `FLOW_SIZE` 16. A GOSUB entry has `FLOW_TIMES` 0; a REPEAT entry the runs it
    has left, from n down to 1. `BACK_LOW`, `BACK_HIGH`, `BACK_LINE` are locals of `DO_GOTO`.
  - `PUSH_FLOW(TIMES)` pushes the script position (the line after the one running); a full
    stack gives `Insufficient memory`. `JUMP_FLOW` sets the position from entry `FLOW_COUNT` and
    sets `SCRIPT_ACTIVE`. `DO_GOSUB` pushes first, then pops when `DO_GOTO` fails.
  - `DO_REPEAT`: n below 1 sets `SKIP_DEPTH = 1`, so the body is skipped. `DO_ENDREP`: the top
    entry must be a REPEAT, else `Syntax error` and the stack is unchanged; with 1 run
    left it pops, else it counts down and jumps. `DO_RETURN` pops the REPEAT entries above the
    last GOSUB, so a `RETURN` inside a loop works. At the prompt both check syntax only.
  - While skipping, `REPEAT` adds 1 to `SKIP_DEPTH` and `ENDREP` takes 1, as `IF` and `ENDIF`
    do; `ENDIF` and `ENDREP` each close a block of either kind.
  - Trap (comment on the flow stack): a `GOTO` out of a loop leaves its entry on the stack; 16
    of them fill it.
  - Measured: the `ENDREP` body costs 259 bytes; `FLOW_TIMES(FLOW_COUNT - 1)` alone 61, a
    plain index variable `TOP` saved 9; `IF FAILED = 0 THEN RETURN` / `IF IN_SCRIPT` in
    `DO_GOSUB` saved 4 on `IF FAILED AND IN_SCRIPT`. Not taken: the skip branch split in two
    `ELSEIF`s (+12); count-first `ENDREP` (+13).
  - New test `SHREPEAT`, script `tests/sd/SCRIPTS/REPEAT.CMD`: a loop, nested loops, `REPEAT 0`
    with a nested loop skipped, a negative count in lower case, a loop in a taken and in a
    skipped `IF` block, `GOSUB` in a loop with `RETURN` from inside a loop, `ENDREP` with an
    empty stack and with a GOSUB on top (under `ONERROR(1)`), a script that ends in a loop; at
    the prompt the syntax errors. Golden files changed: `FILES` (the size), `DIRS` FREE 1 less.
  - Docs owed: PLAN section 8 (the `REPEAT` rules: n below 1, the shared stack and its 16
    entries, `RETURN` in a loop, the `GOTO` trap, the error), section 11 (7e3 done).
- Build after 7e3b: 1.14 s (compile 0.2, ROM 1.05; the ROM step was 0.63 s), the new baseline.
- Tests after 7e3b, one at a time: `SHREPEAT` ok 0.9 s, `SHGOTO` 0.7, `SHIF` 0.5, `SHSCRIPT`
  0.8, `FILES` 0.4, `DIRS` 0.8, `DISK` 0.5 (`FILES` and `DIRS` after their golden update).
- Step 7e4 (2026-10-16): the shell's chains on one value are `SELECT CASE`. `CMDSHELL.COM` is
  15291 bytes, 4 less than 15295.
  - `RUN_LINE`: the statement names are one `SELECT CASE NAME_TEXT`, with `CASE "DELETE",
    "MKDIR", "RMDIR", "CHDIR"` in place of a chain of `OR`s. The assignment and the label come
    first, each with its own `RETURN`. The skip branch is a second `SELECT CASE NAME_TEXT`.
  - `APPLY_OPERATOR` and `DO_ONE_PATH` select on their `UBYTE`.
  - Measured and not taken: `PRIORITY` as a `SELECT CASE` (+6): a `CASE` body that ends in
    `RETURN` still gets a jump out. `EVAL_STRING`'s chain tests `CODE` and `NAME_TEXT`, two values.
  - Golden files changed: `FILES` (the size). The shell still takes 15 clusters, so `DIRS` and
    `DISK` are unchanged.
- Build after 7e4: 0.75 s, the new baseline.
- Tests after 7e4, one at a time: `SHELL` ok 0.6 s, `SHSCRIPT` 0.8, `SHIF` 0.6, `SHGOTO` 0.7,
  `SHREPEAT` 0.8, `SHFILES` 0.6, `FILES` 0.4 (after its golden update).
- Docs step (2026-10-16); no docs are owed.
  - PLAN section 8 Statements: `IF` in `IF`; blocks and `REPEAT` work in a script only.
    Variables: a number comparison is signed. Scripts: the stack that `GOSUB` and `REPEAT` share,
    the block skip, the skipped error and division, the two traps, `REPEAT n` below 1,
    `ENDREP` with no `REPEAT`, `RETURN` in a loop, the end of a skip, the prompt.
  - PLAN section 11: 7e in five parts, 7e3a, 7e3b and 7e4 named.
  - UXCBASIC: help topic `SELECT CASE`, linked from Control (`MKHELP.PY` 0.13 s, 34 topics);
    plan section 1 has `SELECT CASE` in the Control row, its rules and errors, and `ENDSELECT`
    in the two-word ends. Its HANDOFF owes nothing for it.
- No jump out, in pyuxc (2026-10-16). A body before `ELSEIF`, `ELSE` or a `CASE` (of `SELECT
  CASE` or `ON CASE`) that ends in `RETURN`, `GOTO`, `EXIT`, `CONTINUE` or `END` has no `JMP`
  to the end. A statement after `IF c THEN` does not count. The 6502DOS table only, so
  `compare.py` still matches GPC: 571 MATCH, 16 NO GOLDEN, 1.4 s. The pyuxc README,
  "Differences from GPC UXC", has the rule; UXCBASIC's HANDOFF has the rest.
  - The shell: 15291 to 15285 bytes. UXCBASIC test `JUMPOUT` ok 0.7 s, 644 to 620 bytes. Every
    other UXCBASIC test PRG is unchanged.
  - Build 0.84 s (the stale `.COM` files deleted first: `uxb.py` does not see a pyuxc change),
    the new baseline.
  - Full suite: 24 tests, 23 ok in 17.4 s, the slowest seen `SHREPEAT` 2.3 s. `FILES` failed on
    the shell's size only; after its golden update, ok 0.5 s.
  - Docs owed: UXCBASIC's help and plan section 1 lack the rule.
- `ENDREP` with no `REPEAT` on top of the stack gives `Syntax error` (2026-10-16). The shell:
  15285 to 15262 bytes (-23). Build 0.75 s, the new baseline. `SHREPEAT` ok 0.9 s and `FILES`
  ok 0.4 s, their goldens updated.
- `PRIORITY` is a `SELECT CASE` (2026-10-16). The shell stays 15262 bytes. Build 0.85 s, the
  new baseline. `SHVARS` ok 0.7 s, `SHELL` ok 0.5 s.
- `FLOW_TIMES` is `UBYTE` (2026-10-16). `REPEAT n` with n above 255 gives `Syntax error`, in a
  script only. The shell: 15262 to 15148 bytes (-114), BSS 16 bytes less.
  - The type change alone saved 165 bytes; the guard `IF NUMBER_RESULT > 255` costs 51.
    Measured and not taken: `IF NUMBER_RESULT AND $FF00` (+14 on that).
  - `REPEAT.CMD` has `REPEAT 256` after `ONERROR(1)`; `SHREPEAT.OUT` has its `Syntax error`.
  - Build 0.72 s, the new baseline.
  - Tests: `SHREPEAT` ok 0.8 s, `SHGOTO` 0.7, `FILES` 0.5 (its golden updated), `DIRS` 0.8,
    `DISK` 0.5.
  - Docs owed: PLAN section 8 (`REPEAT n` above 255).
- Docs step (2026-10-16); no docs are owed. PLAN section 8 Scripts has `REPEAT n` above 255.
  UXCBASIC help topics `IF` and `SELECT CASE` (`MKHELP.PY` 0.12 s, 34 topics) and plan section
  1, under IF, have the no-jump-out rule.
- Read-ahead buffer (2026-10-16). `SCRIPT_BUFFER(128)` with `BUFFER_COUNT` and `BUFFER_INDEX`;
  the byte at `BUFFER_INDEX` is at the script position. `READ_NEXT_LINE` takes the line from
  the buffer and opens the script into `SCRIPT_HANDLE` only to refill it; `CLOSE_SCRIPT` closes
  it after the line. `GOTO` scans through the buffer with one open. `START_SCRIPT`,
  `JUMP_FLOW` and a failed `GOTO` call `EMPTY_READ_AHEAD`. `READ_OPEN_LINE` and
  `CLOSE_KEEP_ERROR` are gone. The read no longer uses `COPY_BUFFER`.
  - Names are 16 characters at most (pyuxc `NAME TOO LONG`).
  - The shell: 15148 to 15187 bytes (+39). The new globals are 132 bytes (the buffer 128, the
    handle 2, the count and the index 1 each); the BSS total is not measured.
  - Build 1.03 s (ROM step 0.89 s), the new baseline.
  - Tests: `SHSCRIPT` ok 0.8 s (was 1.0), `SHGOTO` 0.6, `SHREPEAT` 0.6, `SHRUN` 0.7, `FILES`
    0.5 (its golden updated), `DIRS` 0.8, `DISK` 0.5. `BIG.CMD` (8193 bytes), `IF.CMD`,
    `REPEAT.CMD` and `GOSUB.CMD` cross refills.
  - Not measured: the time a line in the emulator.
  - Proposal, not taken: `JUMP_FLOW` keeps the buffer when the target is in it (a loop body
    under 255 bytes then reads no file). Cost: the buffer's file position, 4 bytes, and a guess
    of 40 bytes of code.
- Read-ahead in `COPY_BUFFER` (2026-10-16). `SCRIPT_BUFFER` is gone: the read-ahead is the
  first 255 bytes of `COPY_BUFFER`, and `COPY_HANDLE` (`LIST`, `COPY`) calls
  `EMPTY_READ_AHEAD` first. A refill reads 255 bytes, not 128.
  - The shell: 15187 to 15183 bytes (-4). Globals: 128 bytes less.
  - Build 0.76 s (ROM step 0.63 s), the new baseline.
  - `tests/sd/SCRIPTS/RUNS.CMD` starts with `LIST "C:\HELLO.TXT"` (70 bytes, one cluster, so
    free space is unchanged); `SHSCRIPT.OUT` gains one line.
  - Tests: `SHSCRIPT` ok 0.7 s, `SHGOTO` 0.6, `SHREPEAT` 0.5, `FILES` 0.4 (its golden updated),
    `SHFILES` 0.6, `DIRS` 0.8.
  - Trap for the docs: a script edited while it runs takes up to 255 bytes from the read-ahead.
- 7f1 (2026-10-16): `PROMPT$` and `EDITOR$`. They are VARBANK system descriptors 10 and 11,
  `DOS.PROMPT_STRING` `$A020` and `DOS.EDITOR_STRING` `$A022` in `HEAP.UXI`. `NAME_KIND` takes
  them in a `SELECT CASE` with `PATH$`; `DESCRIPTOR_OF` tells them apart by length 7 and the
  first letter. The prompt prints `PROMPT$`, and the drive and `>` when `PROMPT$` is empty.
  `EDITOR$` is a variable only: nothing reads it yet.
  - The shell: 15183 to 15321 bytes (+138). The prompt as one string joined with `CHR$` was 35
    bytes more; the `SELECT CASE` and the `OR` chain are the same size.
  - Build 0.85 s (ROM step 0.73 s), the new baseline.
  - `SHVARS.IN` sets both, prints them, sees the `X16>` prompt, and empties `PROMPT$`.
  - Tests: `SHVARS` ok 0.6 s, `FILES` 0.4 (its golden updated). Full suite: 24 tests, 0
    failed, 13.6 s; the slowest `DIRS` 0.9 s.
- 7f2 (2026-10-16): `SETSYS`. `DO_SETSYS`: alone, it prints `PATH$=`, `CURDIR$=`, `PROMPT$=`
  and `EDITOR$=`, each with its value, one a line. `SETSYS name = expression` takes a name of 5
  or more characters followed by `=`, then calls `DO_ASSIGN`, which rejects a name that is no
  variable. So `SETSYS CURDIR$ = ...`, `SETSYS A$ = ...` and `SETSYS PROMPT$` are syntax errors.
  `PRINT_SYSTEM(DESCRIPTOR)` prints a VARBANK string on a line. `READ_CURDIR` sets `NAME_TEXT` to
  the drive and directory; `EVAL_STRING` and `DO_SETSYS` share it.
  - The shell: 15321 to 15589 bytes (+268), no RAM. The first form was +376: a label as a
    string parameter of `PRINT_SYSTEM` cost 66 bytes more than a `PRINT` of it before the call,
    and the shared `READ_CURDIR` saved 42.
  - Build 0.80 s (ROM step 0.67 s), the new baseline.
  - `SHVARS.IN` gains 7 `SETSYS` lines: two sets, the list, three errors, one empty set.
  - Tests: `SHVARS` ok 0.6 s, `FILES` 0.4 (its golden updated), `SHFILES` 0.6.
  - The user chose the `BIND` store (2026-10-16): a VARBANK string slot.
- 7f3 (2026-10-16): `BIND`. The aliases are VARBANK system string 12, `DOS.BIND_STRING`
  (`$A024`, in `HEAP.UXI`): `NAME=command`, a CR after each. `BIND` alone prints the string.
  `BIND name = command` replaces the alias of that name with the rest of the line; an empty
  command removes it. A store past 255 characters reports error 8, "Insufficient memory".
  `FIND_ALIAS` reads the store into `DOS.CALL_TEXT` and finds `CR NAME=` in it, after a CR put
  in front. In `RUN_LINE`'s `CASE ELSE`, a word that is a whole name (`LEN` of the word read
  equals `LEN(NAME_TEXT)`) goes to `EXPAND_ALIAS`, which makes `LINE_TEXT` the command plus
  the rest of the line, and the line runs again. `BOUND` stops a second expansion, so
  `BIND V=XV` with an alias `XV` runs a program `XV`. A built-in name never reaches an alias.
  - Helpers: `APPEND_LINE(FIRST, PAST)` and `APPEND_CALL(FIRST, PAST)` add part of `LINE_TEXT`
    or `DOS.CALL_TEXT` to `STRING_RESULT`; `EVAL_STRING` uses `APPEND_LINE` too.
    `SYNTAX_ERROR()` replaces the 17 calls of `REPORT_ERROR("Syntax error")`: -386 bytes.
  - The shell: 15589 to 16012 bytes (+423): `BIND` +809, `SYNTAX_ERROR` -386. No RAM but
    `ALIAS_END`, a byte. The first form was +1054: a string join costs 115 to 135 bytes, an
    `APPEND_TEXT` with two computed arguments 57 to 72, `DOS.STR_GET` 37 against
    `DOS.STR_READ` 13.
  - Trap found: `IF CURRENT_CHAR() AND CURSOR = X` is a bitwise `AND`: 46 AND 1 is 0.
  - LEFT$ and RIGHT$ are pyuxc built-ins now (UXCBASIC HANDOFF). In the shell they cost more
    than `MID$` for one use each, their runtime records being 17 and 38 bytes, so the shell
    keeps `MID$`.
  - Builds: 0.83 s, 0.98 s, 0.87 s (ROM step 0.72 s), the last the new baseline.
  - New test `SHBIND`: list, set, an alias with arguments, `V.COM` not taken for `V`, one
    expansion only, removal, syntax errors, a full store, an alias in the middle of the store.
  - Tests: `SHBIND` ok 0.4 s, `SHVARS` 0.5, `SHELL` 0.4, `SHRUN` 0.6, `FILES` 0.3 (golden:
    the shell size), `SHFILES` 0.6, `SHIF` 0.4, `SHGOTO` 0.5, `SHREPEAT` 0.5, `SHSCRIPT` 0.7,
    `DOSAPI` 1.0.
- 7g1 (2026-10-16): `TO file`. `START_REDIRECT` finds the word `TO` outside quotes, in any
  case, after a space and before a space or the end. It reads the file with `LAST_ARGUMENT`
  (a word, a quoted string or a string variable), cuts `LINE_TEXT` before the space in front
  of `TO`, creates the file, keeps handle 1 in `SAVED_OUTPUT` with `DUP`, and `DUP2`s the file
  onto handle 1. `RUN_LINE` calls it before the `SELECT CASE`, for every statement but `IF`
  and `BIND`, then reads the name again. `END_REDIRECT` runs after `RUN_LINE` in the main loop
  and at the start of `REPORT_ERROR`, so errors print on the screen.
  - Facts: `IF A = 2 PRINT "NO" TO N.TXT` creates no file. An error in the statement leaves the
    file with what was written before it. A child program inherits the redirected handle 1.
    `RUN X.CMD TO F` leaves `F` empty: the script's lines run after the redirect ends. An alias
    whose command has its own `TO` ends the first one, leaving that file empty.
  - The shell: 16012 to 16451 bytes (+439). RAM: `SAVED_OUTPUT`, 2 bytes.
  - Build 0.82 s (pyuxc 0.2 s, ROM step 0.62 s), the new baseline.
  - New test `SHREDIR`: a quoted `TO`, lower case, `FILES`, `IF` both ways, an error, the
    syntax errors, a bad drive, an alias with `TO`, a child program.
  - Tests: `SHREDIR` ok 0.5 s, `SHBIND` 0.4, `SHIF` 0.4, `FILES` 0.4 (golden: the shell size),
    `SHSCRIPT` 0.7, `SHRUN` 0.7.
  - Docs owed (PLAN section 8, Redirection): the facts above.
- 7g2 (2026-10-16): `APPEND file`. The scan of `START_REDIRECT` calls `READ_NAME` after each
  space outside quotes, and stops at `TO` or `APPEND` before a space or the end. `APPEND` opens
  the file with access 1 and seeks to its end (`SEEK` from 2); a missing file is created.
  `LEN(NAME_TEXT) - 2` keeps which word was found, since `LAST_ARGUMENT` may read a name.
  - The shell: 16451 to 16581 bytes (+130). RAM: none.
  - Build 0.78 s (pyuxc 0.2 s, ROM step 0.62 s), the new baseline.
  - `SHREDIR` gains: `APPEND` creating then adding, lower case, `FILES ... APPEND`, a quoted
    `APPEND`, `TO X APPEND` (a syntax error).
  - Tests: `SHREDIR` ok 0.5 s, `FILES` 0.4 (golden: the shell size), `DIRS` 0.8 (golden: 2 fewer free
    clusters on every line; it had not run since the read-ahead step, and the shell went from 16
    to 17 clusters at 7g1; the other cluster is not traced), `SHBIND` 0.4, `SHIF` 0.5, `SHSCRIPT` 0.7.
  - `tools/tests.py --help` is not an option: it runs the full suite.
  - Docs owed (PLAN section 8, Redirection): `APPEND` with the `TO` facts.
- 7g3 (2026-10-16): `FROM file`. `api_con_line` (`console.s`) checks handle 0 with `sft_find`:
  when its SFT entry is a file (flags bit 7 clear), it reads the line from handle 0 with
  `api_read`, one byte at a time into the buffer, without echo. It skips LF, drops the
  characters past the most, and ends the line at CR, at the end of the file (`r1` = 0) or on an
  error. The end of the file gives an empty line. `pointer` keeps the buffer address, since
  `r0` points at each byte. The keyboard path echoes CR LF before it stores the line, which
  shares the store with the file path.
  - The shell: `FROM` opens the file with access 0 and `DUP2`s it onto handle 0. `SAVED_OUTPUT`
    is now `SAVED_HANDLE`, and `REDIRECTED` (1 byte) holds the handle sent: 1 for `TO` and
    `APPEND`, 0 for `FROM`. `LEN(NAME_TEXT) - 2` gives 0 for `TO`, 2 for `FROM`, 4 for
    `APPEND`. One redirect a statement.
  - Bug fixed from 7g1: the scan found the word only after a space, but `RUN_LINE` calls it
    with `CURSOR` past the spaces after the name, so `ASK FROM F` and `VERSION TO F` did not
    redirect. `START_REDIRECT` now starts at `CURSOR - 1`.
  - Facts: a child program reads its `INPUT` from the file (`ASK FROM Q.TXT` gives
    `NAME? AGE? [BOB] 42`, on one line, since nothing echoes). `INPUT A FROM NONE.TXT` gives
    `File not found`.
  - ROM: about +86 bytes, counted by hand (`CODE` and `RODATA` end at `$EA03`; 5579 bytes free
    before `KERNALJUMPS`). RAM: none in the ROM; the shell's `REDIRECTED`, 1 byte.
  - The shell: 16581 to 16670 bytes (+89: `FROM` +80, the fix +9).
  - Build 0.76 s (pyuxc 0.2 s, ROM step 0.62 s), the new baseline. A ROM-only rebuild took 0.53 s.
  - `SHREDIR` gains: `INPUT N$ FROM`, `ASK FROM` (a child), `FROM` a missing file,
    `VERSION TO V.TXT` (the fix).
  - Tests: `SHREDIR` ok 0.6 s, `ASK` 0.4, `SHELL` 0.4, `SHVARS` 0.5, `FILES` 0.4 (golden: the
    shell size), `DIRS` 0.8, `SHRUN` 0.7, `SHIF` 0.4, `SHBIND` 0.4.
  - `tests.py --update` takes 2.0 s a test: it waits out the end. A new test needs an empty
    `NAME.OUT` first; `tests.py` finds tests by their `.OUT`.
  - Saving candidate, not applied: the file path of `api_con_line` adds `pointer` and Y into
    `r0` for each byte (13 bytes, about 20 cycles a byte). Incrementing `r0` instead needs
    `api_read` to keep `r0`; not checked.
  - Docs owed: API.md `con_line` (reads handle 0 when it is a file); PLAN section 8,
    Redirection (`FROM`, the one-redirect rule, no echo).
- 7g4 (2026-10-16): the pipe, `A | B`. `START_PIPE` finds a `|` outside quotes, keeps the text
  after it in `PIPE_TEXT` (128), cuts the line, creates the pipe file and sends handle 1 to it.
  `RUN_LINE` calls it before `START_REDIRECT`, for every statement but `IF` and `BIND`. The
  main loop calls `RUN_PIPE` when `PIPE_NUMBER` is set: it sends handle 1 back, sends handle 0
  to the pipe file just written, runs `PIPE_TEXT` with `RUN_LINE`, and goes on while that
  statement starts a pipe of its own. The pipe files are `C:\PIPE1.$$$` and `C:\PIPE2.$$$`, in
  turn; `RUN_PIPE` deletes both at the end. The pipe keeps its own saved handles,
  `PIPE_OUTPUT` and `PIPE_INPUT`, so a stage may have its own `TO`, `APPEND` or `FROM`.
  `REPORT_ERROR` sends handle 1 back from the pipe, so an error shows on the screen and ends
  the line. An alias whose command has a `|` puts its rest before `PIPE_TEXT`, with a `|`.
  - New `SEND_HANDLE(FILE, HANDLE)` (returns the saved handle) and `RESTORE_HANDLE(SAVED,
    HANDLE)`; `START_REDIRECT` and `END_REDIRECT` use them.
  - Facts: `PRINT "A|B"|ASK` gives `[A|B]`. `IF A = 2 PRINT "NO" | INPUT N$` runs neither
    side. `PRINT 1 TO | PRINT 2` is a syntax error and runs no `PRINT 2`. No pipe file is left.
  - The shell: 16670 to 17427 bytes (+757). RAM: 147 bytes (`PIPE_TEXT` 129, `PIPE_PATH` 13,
    `PIPE_OUTPUT`, `PIPE_INPUT`, `PIPE_NUMBER`), outside the file.
  - Measured by compiling variants: the alias join costs 79 bytes; the delete loop is 31 bytes
    smaller than two `DELETE`s of literals.
  - Build 0.77 s (pyuxc 0.2 s, ROM step 0.63 s), the new baseline.
  - `SHREDIR` gains: a pipe into `INPUT`, a quoted `|` with no spaces, a chain of three, an
    alias with a `|`, errors on each side, `FILES C:\PIPE*.*`, an `IF` that fails, a stage with
    `TO`.
  - Tests: `SHREDIR` ok 0.8 s, `FILES` 0.4 (golden: the shell size), `SHBIND` 0.4, `SHIF` 0.5,
    `SHELL` 0.4.
  - Full suite: the first run failed 3. `DIRS` (every `FREE` 1 less: the shell is one cluster
    more) and `DISK` (the cluster of `MANY` in the find buffer, `$38` to `$3B`: the shell grew
    3 clusters since 7f1) got new goldens. `SHSCRIPT` failed from 7g3: `HELLO FROM CHAIN` in
    `tests/sd/SCRIPTS/CHAIN.CMD` redirected from a file `CHAIN`; the line is now
    `HELLO WITH CHAIN`. Rerun: 26 passed, 15.1 s.
  - Fact for the docs: a word `TO`, `APPEND` or `FROM` among a program's arguments is a
    redirect; in quotes it is an argument.
  - Saving candidates, not applied: drop the alias join (79 bytes; the rest after the alias
    would then be lost, or a syntax error); one scan in place of the two of `START_PIPE` and
    `START_REDIRECT` (not measured).
  - Docs owed: PLAN section 8, Redirection (the pipe facts above, the argument fact).
- Docs step after 7g (2026-10-16); no docs are owed. PLAN section 8 Redirection has the facts of
  7g1 to 7g4. API.md `con_line` reads a file on handle 0.
- 7h1 (2026-10-16): `LOCATE`, `BEEP`, `PAUSE`. The user chose: rows and columns from 0, BEEP
  prints the BEL and the console makes no sound yet, PAUSE prints nothing.
  - `LOCATE row,column` takes two number expressions, row 0 to 29 and column 0 to 79, and sets
    `POS(1)` and `POS(0)`. A value out of range, a missing comma or more after the column gives
    `Syntax error`; a string gives `Type mismatch`.
  - `BEEP` prints `CHR$(7)`. `PAUSE` waits for a key with `GETKEY()` and drops it. The key
    comes from the keyboard, even under `FROM`. Both take nothing after the name.
  - The shell: 17427 to 17740 bytes (+313). RAM: none. `CLS` and `BEEP` as one case with
    `CHR$((ASC(NAME_TEXT) - 66) * 5 + 7)` was 16 bytes more than two cases.
  - Build 782 ms (the first 978). Tests: new `SHSCREEN` ok 0.4 s, `SHELL` 0.4, `FILES` 0.4
    (golden: the shell size).
  - `tools/tests.py --help` runs every test: a `--` argument other than `--update` is ignored.
  - Docs owed: PLAN section 8 (`LOCATE` from 0 and its range, `BEEP` is the BEL, `PAUSE` and the
    keyboard).
- 7h2 (2026-10-16): `WAIT seconds`. The user chose: no key ends it.
  - `DOS.UXI` has `API_TICKS` ($03B2) and `FUNCT TICKS() AS UWORD`, the low word of `r0`. It
    leaves `DOS.ERROR` as it is.
  - `DO_WAIT` takes one number expression. A value below 0 gives `Syntax error`; a string gives
    `Type mismatch`. Each second reads `TICKS` and waits until 60 more have passed: the UWORD
    difference is right across the wrap.
  - Without `-warp`, `WAIT 2` took 2.01 s (scratchpad script). The tests run with `-warp`, so
    they do not time it.
  - The shell: 17740 to 17936 bytes (+196: `WAIT` 179, `TICKS` 17). Every program that
    includes `DOS.UXI` grows 17 bytes: pyuxc keeps a FUNCT that nothing calls. RAM: none.
    Tried and larger: a FOR loop (+33), `SYS` inline in the shell (+20), one start and a
    running target (+41).
  - Build 836 ms. Tests: `SHSCREEN` 0.6 s (golden: the `WAIT` lines), `FILES` 0.4 (golden: the
    sizes), `SHELL` 0.4.
  - Docs owed: PLAN section 8 (`WAIT`, 60 ticks a second, no key ends it).
- Docs step after 7h (2026-10-16); no docs are owed. PLAN section 8 Statements has `LOCATE`,
  `BEEP`, `PAUSE` and `WAIT`.
- 7i scope, the user's choice (2026-10-16): no `MOUNT`, no `FORMAT`. `FREE` is renamed
  `DISKFREE` and shows the free kilobytes of a disk. `MEM` waits for PLAN section 11 step 10
  (`bank_alloc`). The commandlets live in the card folder `\DOS`. `HELP` reads its text from
  `HELP.TXT` on the card. Order: `EXIST`, `DISKFREE`, `DISKINFO`, `WHICH`, `HELP`.
- 7i1 (2026-10-16): `EXIST name [SILENT]`, `src/cbin/EXIST.UXB`.
  - `FINDFIRST` with the directory, hidden and system bits: a directory and a wildcard match.
    `P1$` is `1` or `0`; prints `Found` or `File not found`. `SILENT` in capitals prints
    nothing. Exit code 0, 1, or 2 with no name (`Required parameter missing`, `P1$` stays
    empty).
  - `tools/build.py` compiles each `src/cbin/NAME.UXB` to `build/DOS/NAME.CBI` and puts the
    folder `build/DOS` on the card as `\DOS` (mksd takes a folder in `extra`). `tools/tests.py`
    adds `build/DOS` to the test card.
  - Trap: the kernel keeps 3 characters of an extension, so `NAME.CBIN` is `NAME.CBI` on disk.
    mksd rejects a 4-character extension.
  - The shell's `PATH$` is empty at boot, so `EXIST` runs only after `PATH$ = "C:\DOS"`.
  - `EXIST.CBI` 3239 bytes on the card; ROM and the shell: 0 bytes. About 2.9 KB of it is
    `DOS.UXI` and `HEAP.UXI` (`ARGS.COM`, with no include, is 271 bytes): pyuxc keeps the
    FUNCTs nothing calls.
  - Build 917 ms (one compile, 0.1 s). Tests: new `CMDLETS` 0.6 s; `FILES` 0.4 (golden: `DOS`,
    20 files), `DIRS` 0.8 (golden: FREE 5 less), `DISK` 0.4 (golden: F33 cluster `$40`),
    `SHFILES` 0.7.
- pyuxc leaves out uncalled SUBs (2026-10-16; UXCBASIC handoff, "Removing unused code", S1).
  `EXIST.CBI` 1594 bytes, `CMDSHELL.COM` 17708. Goldens: `FILES` (shell size), `DIRS` (FREE 2
  more), `DISK` (F33 cluster `$3E`). `CMDLETS`, `FILES`, `DIRS`, `DISK` and the 11 shell tests
  pass, 0.3-0.8 s. Build 922 ms; a later one 3000 ms (the ROM step 2.87 s, nothing else
  changed).
  - Trap: `uxb.py` does not count the compiler as an input. After a compiler change, delete
    `build/bas/*.COM` and `build/DOS/*.CBI` so the build compiles them again.
- One card (2026-10-16): `build.py` also puts the files and folders of `tests/sd` on
  `build/SD.IMG` (`DOCS`, `HELLO.TXT`, `MANY`, `SCRIPTS`). `fatcheck.py` finds no problems.
  Build 522 ms, the new baseline. No ROM change, no test touched.
  - The ROM boots to `CMDSHELL` since the boot shell step (2026-10-17), ahead of `SYSINIT.COM`.
- `CD` (2026-10-16): the shell takes `CD` as a second name of `CHDIR`. `DO_ONE_PATH` runs
  `CHDIR` for any first letter but D, M and R. The kernel's path parser takes `/` and `\`, so
  `CD C:/DOCS` works.
  - The shell: 17708 to 17723 bytes. S3 saved 12 and `CD` costs 27: the `"CD"` literal and one
    more string compare in the `SELECT CASE`. RAM and ROM: 0 bytes.
  - `SHFILES` gains `CD C:/DOCS`, `cd \` and a `PRINT CURDIR$` after each.
  - Build 1105 ms (the shell compile 0.3 s, the ROM 0.95 s), the new baseline.
  - Tests: `SHFILES` 0.6 s, `FILES` 0.4 (golden: the shell's size), `DIRS` 0.7, `DISK` 0.4.
    Full suite: 28 tests, 27 ok, `DOSAPI` failed, 14.2 s. Its golden predated `\DOS` on the test
    card: `FIND *` now lists `DOS`. Updated; `DOSAPI` ok 0.5 s.
- Names: layer 1 is `UXDOS.SYS`, the shell is `CMDSHELL.COM`.
- `DOS.UXI` (PLAN section 2):
  - `NAMESPACE DOS`, each call a `SUB` or `FUNCTION` that sets `DOS.ERROR`.
  - UXCBASIC reserves `OPEN`, so the handle calls are `OPEN_FILE`, `CREATE_FILE`,
    `CLOSE_FILE`, `READ_FILE` and `WRITE_FILE`. Names are 16 characters at most, so the
    error constants are `ERR_` and the asm names of `api.inc`, cut where too long.
  - Every source uses UXCBASIC's `AS` types, with no `$` or `%` mark: a number is `UBYTE` or
    `UWORD`, a string `AS STRING * n`, a string parameter or result `AS STRING`.
  - A function is `FUNCT ... END FUNCT`. A sub ends with `END SUB`.
- UXCBASIC state, 2026-10-14: `LONG` and `ULONG` are done. Records (`TYPE ... END TYPE`) are
  done to step 5 of 7: record parameters and the help topic are not. PLAN section 12 and
  `DOS.UXI` still describe 32-bit values as two words.
- A VSYNC IRQ sampler of the GPC runtime and its scripts are in `attic/gpc/tools/prof`: `profrun.py` runs
  a sampled compile, `profmap.py` ranks the samples by label.
- No git repository. Do not run `git init` until the user says so.

## Run

- `python tools/build.py`, then `python tools/tests.py`. `BUILD.BAT` runs `build.py`.
- In a window: `C:\8bitProgramming\x16emu\x16emu.exe -rom build\6502DOS.ROM -sdcard build\SD.IMG`,
  or `RUN.BAT`, which adds `-scale 2 -noemucmdkeys`. With `-noemucmdkeys`, Ctrl and Alt keys
  reach the X16, and the emulator's Ctrl hotkeys (reset, paste, fullscreen) are off.
  The ROM boots to the shell. `-rom build\TEST.ROM` boots to the monitor; there try `DIR`,
  `TYPE C:\README.TXT`, `RUN ARGS.COM ONE TWO`, `RUN SHOW.COM README.TXT`,
  `RUN CMDSHELL.COM`, `D C000`.

## Next

0. PLAN section 11 step 6, CBM DOS leaves: 6a to 6e done. Full suite passed after the `END`
   range step.
1. The user reviews `docs/PLAN.md` and `docs/API.md`, and tries `RUN SHOW.COM` in a window.
2. Step 7 of PLAN section 11: `CMDSHELL`, the BASIC shell. 7a to 7c and the shell strings
   step, 7d, 7e1, 7e2, 7e3a, 7e3b, 7e4 and the docs steps done.
   `SELECT CASE` is in pyuxc (2026-10-16); UXCBASIC's HANDOFF has the syntax and the tests. It
   compiles to the same code as an `IF`/`ELSEIF` chain: a test source of three selects was
   409 bytes both ways. 7e4 is done: the shell uses it.
   The docs step after 7e4, the pyuxc no-jump-out step, `FLOW_TIMES` as `UBYTE` and the docs
   step after it, the read-ahead buffer, 7f1 (`PROMPT$`, `EDITOR$`), 7f2 (`SETSYS`) and 7f3
   (`BIND`) are done, and the docs step after them (PLAN section 3: system descriptors 10 to
   12; section 8: the system variables, `SETSYS`, the prompt, Aliases, the read-ahead; section
   13: descriptors 13 to 31 still open). 7g1 (`TO`), 7g2 (`APPEND`), 7g3 (`FROM`) and 7g4 (the pipe) are done.
   The docs step after 7g, 7h1 (`LOCATE`, `BEEP`, `PAUSE`), 7h2 (`WAIT`) and the docs step
   after 7h are done. `DATE` and `TIME` have their clock calls now (the clock step, Next). 7i1 (`EXIST`), 7i2 (`DISKFREE`) and
   7i3 (`DISKINFO`) are done, and the docs step after them (PLAN section 8: `CBIN.UXI`,
   `DISKFREE`, `DISKINFO`). 7i4 is done as `WHERE`. 7i5
   (`HELP`), `PROMPT$` codes, short names, the boot shell, console color and `COLOR` are done,
   and the docs step after them, the 4 MB card, extended keys, ANSI output and Alt and Ctrl
   keys. Next, agreed with the user on 2026-10-17:
   - UXCBASIC, in `UXCBASIC.PLAN.md` first, then pyuxc: `GETKEY()` stays a UBYTE; on an
     extended key `S_GETIN` reads both bytes, returns 0 and keeps the scan code. `SCANKEY()`
     gives that scan code, 0 after a plain key or no key. `KEYMODS()` gives the modifiers held
     now: 1 Shift, 4 Caps Lock, 64 Alt, 128 Ctrl. The `GETKEY` help says PETSCII; fix it to
     the 6502DOS codes.
   - Then a `DOS.UXI` key reader on `API_IN`. VIEW did not wait for it (the user, 2026-10-17).
   - `VIEW file`, a DOS utility in `src/dos`, command line only, not for scripts (the user,
     2026-10-17). Agreed so far: 29 rows of text and a footer of one row with the keys;
     PgUp, PgDn, the arrows, Home, End; Left and Right scroll sideways, with an option to wrap;
     find, with the match highlighted; the line number in the footer; Space pages down. Keys
     come as 0 and a scan code (extended keys, above). V1, V2a (sideways), V2b (wrap), V3 and
     V3b (find) and V3c (reversed highlight) are done (State). G was dropped (the user,
     2026-10-17). VIEW's steps and its docs are done.
   - Next (the user, 2026-10-17): three pyuxc features, in `UXCBASIC/pyuxc`, one step each,
     then VIEW uses them. The design is in `docs/UXCBASIC.PLAN.md` section 5, the last three
     entries (written 2026-10-17; no code yet).
     1. String `CONST`s: `CONST SGR_REVERSE$ = CHR$(27) + "[7m"`. Done 2026-10-17; UXCBASIC's
        HANDOFF has it.
     2. Line continuation, ` _` at the end of a line. Done 2026-10-17; UXCBASIC's HANDOFF
        has it.
     3. FreeBASIC escapes in `!"..."`. Done 2026-10-17; UXCBASIC's HANDOFF has it.
     4. `src/bas/CONS.UXI`, `NAMESPACE CONS` (2026-10-17): `CSI$`, `CUU$` `CUD$` `CUF$` `CUB$`,
        `CUP_HOME$`, `ED$` (`Esc[2J`), `EL$`, `SGR_RESET$` `SGR_BOLD$` `SGR_REVERSE$`, and
        `SGR_FG_` and `SGR_BG_` with `BLACK` `RED` `GREEN` `YELLOW` `BLUE` `MAGENTA` `CYAN`
        `WHITE`. Each is built on `CSI$` with `+`. Checked by a scratch compile with pyuxc: the
        include alone adds 0 bytes (95 both ways); `PRINT CONS.SGR_REVERSE$` is 158 bytes,
        against 162 for `PRINT CHR$(27); "[7m"`; a second use adds 10 bytes, and the literal is
        stored once; every sequence's bytes were checked in the PRG. No test in `tests/` yet;
        VIEW is its test.
     5. VIEW uses `CONS.UXI` (2026-10-17): no `CHR$(27)` is left. `CONST FOOTER_SGR$ =
        CONS.CSI$ + "30;47m"` serves the footer and the `Find: ` prompt. `VIEW.COM` 6472 to 6422
        bytes (-50), RAM 0. Build 745 ms, the new baseline. `VIEW` ok 1.1 s, the golden
        unchanged.
     6. Docs batch (2026-10-17):
        - `tools/api.py`, so `docs/API.md`: `con_status` gives the modifiers in X; `con_out`
          lists the ANSI sequences; `con_in` lists every scan code, Alt and Ctrl.
        - PLAN section 2: `KEYS.UXI` and `CONS.UXI`. Section 6: ANSI, the ANSI colors,
          extended keys, Alt, the `GETKEY()` trap. Section 8: `VIEW`. Section 10: the
          `src/bas` row.
        - `src/dos/HELP.TXT`: topic `VIEW`, for the command line only.
        - UXCBASIC: `help/UXC-HELP.md` has a section String CONSTs in topic CONST, and new
          topics Line continuation and Escaped strings; `help/MKHELP.PY` made the `.HLP` files,
          36 topics. UXCBASIC's HANDOFF has it. The copies in `disk/HELP-TXT/` and
          `build/HELP-TXT/` stay old until `build.py UXC.HELP` runs. `UXCBASIC.PLAN.md`'s CONST
          entry no longer says a string CONST stops the compile.
        - HELP.TXT grew past a cluster, so the test card has 1 KB less free: `CMDLETS.OUT` and
          `DIRS.OUT` each lost 1 from every free count. Build 425 ms, the new baseline. Tests:
          `CMDLETS` ok 1.5 s, `DIRS` ok 0.8 s.
     7. Screen size (2026-10-17), the user's option B. Step 1 done: `api_con_cursor` with carry
        set also returns the screen's rows in r0L (30) and columns in r0H (80). ROM +8 bytes,
        RAM 0. Build 517 ms, the new baseline. `ANSI` ok 0.5 s; no test reads r0 yet. Owed in
        the docs batch: `tools/api.py` `con_cursor` (out r0L rows, r0H columns), so API.md.
        The rest, as the user asked: POS(2) the rows and POS(3) the columns in pyuxc, filled
        at startup or by a future SCREEN command from `con_cursor`; a wrapper in `CONS.UXI`;
        `SCREEN_ROWS` and `SCREEN_COLS`. BIND cannot name `POS(2)`, an expression. The user
        chose the live form (option B): no stored copy, no startup code.
        Step 2 done: UXCBASIC `POS(2)` gives the rows and `POS(3)` the columns, by new records
        T_POSROWS and T_POSCOLS, 8 bytes each use: `phx`, `sec`, `jsr S_PLOT`, `lda $02` or
        `$03`, `plx`. RAM 0. `POS(2) = v` and `POS(3) = v` stop with `POS NEEDS 0 OR 1`; a read
        past 3 or of a variable stops with `POS NEEDS 0 TO 3`. Test `POSSCREEN` ok 0.6 s, `POS`
        ok 0.5 s. MKTPL 0.23 s.
        Step 3 done: `CONS.UXI` has `FUNCTION SCREEN_ROWS() AS UBYTE` and `SCREEN_COLS()`,
        returning `POS(2)` and `POS(3)`. No BIND. Dead-code stripping leaves them out of a
        program that does not call them: `VIEW.COM` stays 6422 bytes. One call of each costs
        14 bytes more than `POS(2); POS(3)` (212 against 198). Test `SCRSIZE` (`tests/SCRSIZE.UXB`)
        ok 0.4 s, `VIEW` ok 0.9 s. Build 1.29 s, the new baseline. The feature is complete; the
        docs batch is owed: `api.py`/API.md `con_cursor`, the UXC-HELP POS topic, PLAN.
   - Library refactor, agreed with the user on 2026-10-17. The compiler repo keeps the language;
     every `.UXI` library lives in 6502DOS. The repos stay apart. Each file holds one
     namespace of the same name. BINDs that rename built-ins stay and grow: the coming editor
     lists a namespace's members after `STR.`, so every built-in of a kind gets a BIND in its
     namespace. Constants and BINDs cost 0 bytes; dead-code stripping drops uncalled FUNCTIONs.
     `VIEW.COM` (6422 bytes) checks that. No asm. Steps, one at a time:
     1. A new `lib/` folder in 6502DOS. Move `DOS.UXI`, `HEAP.UXI`, `CONS.UXI` and `KEYS.UXI`
        from `src/bas` into it. Point `uxb.py`'s include folder (`LIBRARY_FOLDER`) and
        `build.py` at it.
        Step 1 done: `lib/` holds the four files; `uxb.py` `LIBRARY_FOLDER` is `lib`; `build.py`
        needed no change. `api.py` names `lib/KEYS.UXI` and `lib/CONS.UXI`. `src/cbin/CBIN.UXI`
        stays, for commandlets only. Build 1.56 s with every program recompiled, the new
        baseline. `VIEW.COM` stays 6422 bytes. Tests: `VIEW` ok 1.1 s, `CMDLETS` ok 1.5 s,
        `DIRS` ok 0.8 s. `CMDLETS` and `DIRS` failed first on stale free counts: step 3's
        `SCRSIZE.COM` on the test card takes one cluster, so each free count in
        `CMDLETS.OUT` and `DIRS.OUT` is one less (871 is 870). Docs owed: PLAN names
        `src/bas/*.UXI` at lines 63 to 74, 211 and 923.
     2. `KEYS.UXI` holds `NAMESPACE KEYS` (now `KEY`); update its callers.
        Step 2 done: `KEYS.UXI` holds `NAMESPACE KEYS`. `VIEW.UXB` and `KEYTEST.UXB` write
        `KEYS.`; no other file used `KEY.`. Build 0.80 s, two programs recompiled, the new
        baseline. `VIEW.COM` stays 6422 bytes. Test: `VIEW` ok 1.0 s. `KEYTEST` has no test.
        Docs owed: PLAN line 73 names `KEY.SCAN_UP` and `KEY.MOD_CTRL`.
     3. `HEAP.UXI` holds `NAMESPACE HEAP` (now a second `DOS`); update `CMDSHELL`,
        `DISKFREE`, `DISKINFO` and `EXIST`.
        Step 3 done: `HEAP.UXI` holds `NAMESPACE HEAP`, and its callers write `HEAP.`:
        `CMDSHELL`, `DISKFREE`, `DISKINFO`, `EXIST`, `HELP`, `VIEW`, `tests/com/SLOTKID` and
        the comment of `CBIN.UXI`. Build 1.29 s, six programs recompiled, the new baseline.
        `VIEW.COM`, `HELP.COM` and `CMDSHELL.COM` keep their sizes. Tests: `CMDLETS` ok 1.5 s,
        `SHRUN` ok 0.7 s, `VIEW` ok 0.9 s, `SHVARS` ok 0.5 s. Docs owed: PLAN lines 66 and
        211 to 212 say `HEAP.UXI` is in namespace `DOS`.
     4. `CONS.UXI` takes `LOCATE`, `PrintAt`, `print_bool`, `PRINT_USING` and the BINDs of
        UXCBASIC's `lib/CONSOLE.UXI` (`LOCATE`, `CursorCol`, `CursorRow`, `nl`, `spc`, `PRINT`,
        `INPUT`, `LINPUT`), plus new BINDs for the other console built-ins.
        Step 4 done: `CONS.UXI` binds `PRINT`, `INPUT`, `LINPUT`, `POS` and `NEWLINE` (PRINT
        alone), and holds `SUB LOCATE(ROW, COLUMN)`, `SUB PRINT_AT(ROW, COLUMN, TEXT$)` and
        `SUB PRINT_BOOL(VALUE)`. `KEYS.UXI` binds `GETKEY`. A BIND takes a word, not a word
        with arguments, so `CursorCol` (`POS(0)`), `CursorRow` and `spc` (`PRINT " ";`) are
        not bound: `CONS.POS(0)` and `CONS.LOCATE` serve. `PRINT_USING` was an empty SUB and
        is not ported. The top-level `BIND con` and `BIND txt` are not ported. The new test
        `CONSLIB` runs them. Build 1.31 s, the new baseline. Tests: `CONSLIB` ok 0.4 s,
        `SCRSIZE` ok 0.5 s, `VIEW` ok 1.0 s, `FILES` ok 0.4 s, `DIRS` ok 0.8 s, `CMDLETS` ok
        1.7 s, `SHFILES` ok 0.6 s, `SHREDIR` ok 0.9 s, `SHRUN` ok 0.7 s, `SHSCRIPT` ok 0.8 s.
        `CONSLIB.COM` takes one cluster: `DIRS.OUT` and `CMDLETS.OUT` show 869 free, not 870.
        `FILES.OUT` lists `CONSLIB.COM` and `SCRSIZE.COM`, 23 files.
        pyuxc leaves out the string literals that no code left in names (`ds_strip` in
        `uxc_dead.py`), so `PRINT_BOOL`'s "true" and "false" cost a program nothing when it
        does not call it. `VIEW.COM` is 6419 bytes, `SCRSIZE.COM` 239, `KEYTEST.COM` 2697.
        `tools/uxb.py` recompiles a program when a file of pyuxc is newer than it. Build
        1.96 s with every program compiled, the new baseline. Tests: `SCRSIZE` ok 0.6 s,
        `VIEW` ok 0.9 s, `CONSLIB` ok 0.4 s, `FILES` ok 0.4 s (golden rewritten: 7 programs
        shrink 2 to 13 bytes), `DIRS` ok 0.8 s, `DUP` ok 0.4 s, `SEEK` ok 0.4 s, `WRITE` ok
        0.6 s, `SHRUN` ok 0.7 s, `CMDLETS` ok 1.4 s.
        BIND to a word: pyuxc holds at most 64 (`K_ALIASES`) in a program. `CONS` takes 5
        and `KEYS` 1.
     5. A new `lib/STR.UXI` with `NAMESPACE STR`: the BINDs of UXCBASIC's `lib/STRINGS.UXI`
        plus every other string built-in.
        Step 5 done: `lib/STR.UXI` binds `LEN`, `ASC`, `VAL`, `LVAL` (new), `CHR$`, `STR$`,
        `MID$`, `INSTR`, `LEFT$`, `RIGHT$` and `AddressOf` (`AddrOf`). These are all the string
        built-ins in pyuxc's reserved words (`nm_word` in `uxc_name.py`). `InStrRev` is ported as
        `FUNCTION INSTR_REV(TEXT$, FIND$, START)`: the last match that starts at or before
        `START`, with `START` 0 meaning the whole text. It calls `INSTR` once for each match up
        to `START`. The ported backward scan cost 325 bytes more (scratch `revcost.py`). The
        TODO notes of `STRINGS.UXI` (TRIM, PAD, StartsWith, UPPER) are not ported. Scratch
        compile: the include and `STR.MID$` add 0 bytes (415 bytes all three ways). New test
        `STRLIB` (`tests/STRLIB.UXB`), checked by hand, ok 0.5 s; `STRLIB.COM` 1981 bytes.
        Golden churn only: `FILES` ok 0.4 s, `DIRS` 0.8, `CMDLETS` 1.4, `DISK` 0.4. Build 575 ms with no compile, the new baseline. Full suite after it, the
        7th step: 34 tests, 0 failed, 18.3 s. `STR` takes 11 of a program's 64 BINDs.
     6. The user, 2026-10-17: the working ideas of UXCBASIC's `lib/DISK_FILEIO.UXI` (`EXISTS`,
        `SIZE`, `COPY`) move into `DOS.UXI` as `DOS` functions, and `DISK_FILEIO.UXI` is deleted.
        Step 6 done in 6502DOS: `DOS.UXI` ends with a section of whole-file routines built on
        the calls. `FUNCT EXISTS(PATH) AS UBYTE` gives 1 when a file or directory matches,
        through `FINDFIRST`. `FUNCT SIZE(PATH) AS ULONG` gives a file's size, through
        `FINDFIRST`; a directory gives error 2. Both end a search in progress and set the
        `FOUND_` variables. `SUB COPY(SOURCE, TARGET)` copies 256 bytes at a time through
        `CALL_TEXT`, so it takes no RAM. The new `CONST DISK_FULL = 255` is its error when the
        target takes fewer bytes than it is given. The other stubs of `DISK_FILEIO.UXI` were
        empty and are not ported. Scratch compile (`doscost.py`): a program of `DOS.UXI` alone
        is 40 bytes; with one call of `EXISTS` 716, `SIZE` 781, `COPY` 865, all three 1471.
        No program in the build changed size. `tests/DOSAPI.UXB` section 7 tests them, the
        golden checked by hand: `DOSAPI` ok 0.5 s. Golden churn only: `FILES` ok 0.4 s, `DIRS`
        0.8, `CMDLETS` 1.4, `DISK` 0.4. Build 1.41 s with seven programs recompiled, the new
        baseline.
        UXCBASIC's `lib/DISK_FILEIO.UXI` and its copy `disk/DISK_FILEIO.UXI` are deleted.
        UXCBASIC's HANDOFF line 274 and `UXCBASIC.PLAN.md` line 1328 still name the file; the
        docs batch fixes them.
     7. UXCBASIC: delete `lib/`; move `STRINGS.UXI` into `tests/` for `STRLR` and `STRNS`; the
        UXC-HELP topic at about line 405 points to the 6502DOS library.
        Step 7 done: `lib/` is gone. `STRINGS.UXI` is `tests/STRINGS.UXI`. `lib/CONSOLE.UXI`,
        which no source included, is deleted. `tests.py`, `pyuxc/compare.py` and
        `pyuxc/golden.py` no longer search `lib/`. `build.py` no longer copies `lib/` onto
        `disk/`. The Strings topic of UXC-HELP says `STR.UXI` in the 6502DOS library binds the
        built-ins in `NAMESPACE STR`; `MKHELP.PY` rebuilt the pages, 0.17 s. `disk/CONSOLE.UXI`,
        `disk/STRINGS.UXI` and `disk/STRINGS2.UXI` stay; `disk/STR-TEST.UXB` includes
        `STRINGS2.UXI`. No asm, no 6502DOS build. Tests in UXCBASIC: `STRLR` ok 0.7 s, `STRNS`
        ok 0.5 s.
     8. `genapi.py` writes the `API_*` constants that `DOS.UXI` now holds by hand.
        Step 8 done: `genapi.py` writes one `API_` CONST for each call in `api.py`, 47, into
        `lib/DOS.UXI` between the lines `UXI_BEGIN` and `UXI_END`, packed to 100 columns. It
        writes the file only when the block changes, so a build that changes nothing in
        `api.py` recompiles nothing. The 25 hand-written values all matched. The new names
        include the calls not yet written in the kernel (`API_ATTRIB`, `API_GETDATE` and so
        on), which give error 1. Build 1.48 s with every program recompiled, the new
        baseline. `VIEW.COM` stays 6419 bytes. Tests: `DOSAPI` ok 0.9 s, `FILES` ok 0.3 s (no
        size changed), `SHELL` ok 0.5 s.
        Step 8b done (2026-10-18), the end of the library refactor: `genapi.py` also writes
        `DOS.UXI`'s `ERR_` and `FIND_` CONSTs into the block, now marked "generated by
        tools/genapi.py" and "end of the generated CONSTs". `api.py`'s `UXI_ERROR_NAMES` gives
        the short UXCBASIC name of the four errors whose name runs past pyuxc's 16 characters
        a name part (`TOO_MANY`, `BAD_ACCESS`, `NOT_SAME`, `NO_MORE`); `genapi.py` fails on
        any other name past 16. The asm names are unchanged. New in `DOS.UXI`:
        `ERR_WRITE_FAULT` (29) and `FIND_BUFFER_SIZE` (63). `FIND_ATTRIBUTES` is now
        `FIND_ATTR`, as in asm; only `UPDATE_FOUND` used it. `HEAP.UXI` drops its four
        `API_STR_*` CONSTs and calls `DOS.API_STR_*`. No asm. Every program keeps its size.
        Build 1.49 s with every program recompiled, the new baseline. Tests: `DOSAPI` ok
        0.7 s, `SHVARS` ok 0.5 s.
        The full suite after it failed 4 on the prompt step's column 0, not on 8b. `SHELL.OUT`
        and `SHSCREEN.OUT` were back at their committed text, dated 07:01 on 2026-10-18 while
        `/tests` was in `.gitignore`; `FILES.OUT` (`CMDSHELL.COM` 18864) and `SHREDIR.OUT`
        (the prompt on a new line after `INPUT`'s `? `) were never rewritten. All four
        rewritten and diffed: only the prompt moved. `FILES` ok 0.4 s, `SHELL` 0.5,
        `SHREDIR` 0.9, `SHSCREEN` 0.7.
     9. Docs batch (2026-10-17), no code, no build:
        - `tools/api.py`, so `docs/API.md`: `con_cursor` gives the screen's rows in r0L and
          columns in r0H on a get. `genapi.py` 0.21 s; `DOS.UXI` unchanged.
        - UXC-HELP topic POS: POS(2), POS(3), both errors. `MKHELP.PY` 0.20 s, 36 topics.
        - PLAN section 2: a table of `lib/` (five files, their namespaces), the generated
          `API_` block, dead-code stripping, the 64-BIND limit. Section 4: `con_cursor`.
          Section 10: the `lib/` row, the include search, pyuxc as a rebuild input. 6a: `lib/`.
        - UXCBASIC, by the doc-style agent: `docs/HANDOFF.md` rewritten to the current state,
          103 lines; the old 694 lines appended to `docs/HISTORY.md`. `UXCBASIC.PLAN.md`: the
          old layout lines (`examples/`, `disk/`, `DISK_FILEIO.UXI`, `BANK.UXI`, `CONSOLE.UXI`,
          `compare.py`). `pyuxc/README.md` rewritten as a reference, 155 lines. `CLAUDE.md`'s
          line counts.
        - Fixed in the docs step after break (2026-10-18), by the doc-style agent, each
          example compiled: UXC-HELP "What UXCBASIC is", "Using this help" (no X16 viewer
          here), "Compiling" (was "Compiling from UXCEDIT", now pyuxc's command line and
          result line), "Including files", "Files" and its four sections (6502DOS paths and
          handles, 8 SFT entries, two `handle_io` traps); `UXCBASIC.PLAN.md` section 3 (the
          pyuxc layout, `tests.py`, `RUNUXCTESTS.BAT`).
        - Still stale: `UXCBASIC.PLAN.md` lines 3 to 6 and 13 (UXC.PRG, UXCEDIT, "Unix-style
          X16", PETSCII), sections 4 and 5 (`run.py`, UXCEDIT), section 3's `#DEFINE UXC.*`
          and `.LST` lines (pyuxc has neither). `MKHELP.PY`'s docstring names
          `src/UXC.HELP.BASL`, which is only in `attic/gpc`.
     - Names follow ECMA-48 (CUU, CUD, CUF, CUB, CUP, ED, EL, SGR).
     - The user, 2026-10-17: the ANSI string CONSTs go in `NAMESPACE CONS`, as the key codes are
       in `NAMESPACE KEYS` (`lib/KEYS.UXI`). VIEW then writes `CONS.SGR_REVERSE$`.
     - Not chosen: escapes in plain strings (clash with paths such as `"C:\DOS\HELP.TXT"`),
       `$` codes (clash with `PROMPT$`), and named escapes like `/x(CUD 4)`.
   - Done (2026-10-18): the shell prompt starts in column 0. `PRINT_PROMPT` calls
     `START_LINE` (`CMDSHELL.UXB`), which prints a new line when `POS(0) > 0`;
     `REPORT_ERROR` calls it too. No asm. `CMDSHELL.COM` 18854 to 18864 bytes (+10;
     the check inline in both places was 18871). Build 972 ms, the new baseline.
     Goldens rewritten and diffed: `SHELL` (`PRINT "A";`, then the prompt on the next
     line), `SHSCREEN` (after `LOCATE 29,79` and `LOCATE 5,6` the prompt moves to a new
     line). Tests: `SHELL` ok 0.4 s, `SHVARS` 0.6, `SHRUN` 0.7, `SHSCREEN` 0.6, `SHBOOT`
     0.4. PLAN section 8 has it.
   - Bug, to do (the user, 2026-10-18): `VIEW.COM` must eat the keyboard queue between Up and
     Down arrow moves.
   - 7i4 `WHERE` done 2026-10-18: `src/cbin/WHERE.UXB`, `WHERE name [SILENT]`, for the
     command line and scripts. The user's choices: the first match only, the one the shell
     runs; a name with no extension tries `.CBIN`, `.COM`, `.CMD`; `*` or `?` names nothing.
     The look-up copies the shell's `FIND_PROGRAM`, but a match in the current directory is
     printed after the drive and the current directory: `C:\ARGS.COM`. Aliases and the
     statements are not looked up. `P1$` is the path, empty when not found. `File not found`
     exit 1, `Required parameter missing` exit 2. `WHERE.CBI` 3160 bytes. Build 884 ms, the new
     baseline. `tests/WHERE.IN` new; `WHERE` ok 1.1 s. `TREE` golden gains `WHERE.CBI` in
     `\DOS`; `TREE` ok 1.1 s, `CMDLETS` ok 1.7 s. Owed to the doc batch: the `HELP.TXT` topic
     `WHERE` (`(Command line or Script)`), PLAN section 8 entry, section 11 7i4 no longer put
     off. Steps since the full suite: 2.
   - `GREP` done 2026-10-18: `src/dos/GREP.UXB`, `GREP [-i] [-n] [-v] [-c] pattern [file]`,
     for the command line. The user's choices: a small regex (`^` `$` `.` `*` `[a-z]` `[^...]`),
     the four switches, one file or handle 0. `\` before a letter or a digit is a plain `\`,
     so `C:\DOS` matches itself. The pattern compiles to atoms, each a list of ranges; the
     matcher steps a list of states over the line, with no backtracking. A line over 512
     characters is taken as two or more lines. Exit code 0 when a line is written or counted,
     1 when none is, 2 on an error. Trap: a name part is 16 characters at most (`NAME TOO
     LONG`). `GREP.COM` 5046 bytes. Build 1206 ms, the new baseline. `tests/GREP.IN` new;
     `GREP` ok 1.6 s. `TREE` golden gains `GREP.COM`; `TREE` ok 1.1 s. Owed to the doc
     batch: the `HELP.TXT` topic `GREP` (`(Command line)`), PLAN sections 8 and 11. Steps
     since the full suite: 3.
   - Doc batch done 2026-10-18: `HELP.TXT` topics `WHERE` `(Command line or Script)`, after
     `UPTIME`, and `GREP` `(Command line only)`, after `TAIL`; the `HELP` topic names `WHERE`
     with the commandlets that work at the prompt and in a script. Every line is 80 at most.
     PLAN section 8 entries for `GREP` and `WHERE` after `TAIL`; section 11 step 7i: 7i4 is no
     longer put off, and `GREP` follows `TAIL`. No docs are owed. Build 642 ms, the new
     baseline. `CMDLETS` failed on the `HELP` list (gains `WHERE` and `GREP`), as expected;
     updated, `CMDLETS` ok 1.7 s. Steps since the full suite: 4.
   - `XCOPY` done 2026-10-18: `src/dos/XCOPY.UXB`, `XCOPY source [target] [-s] [-e] [-p] [-l]
     [-y]`, for the command line. The user's choices: all five switches; a target file that
     exists asks `Overwrite path (Y/N/A)?`, `-y` does not ask; a missing target is made with
     the directories above it; the source is a directory or a directory and a pattern, the
     pattern used at every level; a target in the source refuses; the MS-DOS exit codes 0 1 2
     4 5. `-p`'s N skips the file, as in MS-DOS; Esc at a question stops with exit code 2.
     Ctrl+C ends it with exit code 0, as any program. `-e` takes `-s` with it. Hidden and
     system names are skipped. The walk is `TREE`'s, with the find state saved a level. The
     roots are made full by `CHDIR` and `GETCWD`; the guard compares them, and on a refusal
     the directories made for the target are removed. The target file is checked by an open,
     not `DOS.EXISTS`, which would end the search. `XCOPY.COM` 7137 bytes. Build 949 ms, the
     new baseline. Trap: `\X` in a test line is x16emu's hex escape, so `Q:\X` is typed as
     `Q:` and a byte. A `--update` run lasts 2 s, so the test is split: `tests/XCOPY.IN` (the
     errors, plain copies, the questions) ok 1.3 s, `tests/XCOPYS.IN` (`-s`, `-e`, `-l`) ok
     1.1 s. `TREE` failed on `XCOPY.COM` in `\DOS`, as expected; updated, ok 1.3 s. Owed to the
     doc batch: the `HELP.TXT` topic `XCOPY` (`(Command line only)`), the `CMDLETS` golden's
     `HELP` list after it, PLAN sections 8 and 11. Steps since the full suite: 5.
   - Tab completion in the shell (the user, 2026-10-18): the ROM hook and the shell, files and
     commands, Tab cycles as in cmd.exe and Shift+Tab goes back. Two steps.
     1. ROM hook, done 2026-10-18. `api_con_line`: buffer byte 1 is the length of the text kept
        from offset 2, which is shown and edited, as the MS-DOS 0Ah template. Tab ends the line
        with no echo. Returns the end key in A ($0D or $09) and `kbd_mods` in X. A file on
        handle 0 still reads from offset 2. The monitor clears byte 1 and calls again on Tab.
        `DOS.UXI`: `CON_LINE` clears the line and calls again on Tab; new `FUNCT CON_EDIT(LINE)`
        keeps the text and returns the end key, and sets `CON_EDIT_MODS`. ROM +35 bytes, counted
        by hand: `RODATA` ends at `$EDCE`, 4608 bytes free below `$FFCF`. `CMDSHELL.COM` and
        `DOSAPI.COM` +25 (the `CON_LINE` loop). Build 3214 ms: `DOS.UXI` changed, so every
        program recompiled; the baseline stays 949 ms. Tests: `SHVARS` ok 0.8 s, `ANSI` ok
        0.4 s, `FILES` failed on the two sizes, as expected; updated, ok 0.4 s; `DIRS` ok 0.8 s.
        No test types a Tab yet: step 2 adds them (`\X09` in a `.IN` line). Shift+Tab cannot be
        typed by x16emu -bas. Steps since the full suite: 6.
     2. The shell: on Tab, `CON_EDIT` at the prompt, complete the last word. A file or
        directory name, `\` after a directory; the first word also built-ins and `.COM`/`.CMD`
        on PATH$. Done 2026-10-18, see 2b. Design: save `POS(0)` after the prompt; `DO WHILE
        DOS.CON_EDIT(LINE_TEXT) = 9`; redraw by locating the row and column of the prompt end,
        spaces over the old text, locate again; the match list is the built-ins (first word, no
        directory part, prefix compared with `UCASE$`), then `FINDFIRST` of the stem + `*`
        (+ `.*` when the name part has no dot), then `.COM`/`.CMD` on PATH$ (first word).
        Shift+Tab is `CON_EDIT_MODS AND 1`.
     1b. UXCBASIC `UCASE$` and `LCASE$`, done 2026-10-18, asm approved. `R_CASE` 54 bytes,
        `T_UCASE`/`T_LCASE` 12 bytes a call; about 28 cycles a letter. A literal is folded by
        the compiler. The 3 new records pushed `R_RELEM` and `R_RMAX` past id 255, which a
        fixup byte cannot hold: new fixup kind `F_REC_HI` (6), record <arg> + 256, in
        `MACROS.ASM`, `MKTPL.PY`, `uxc_defs.py`, `uxc_code.py`. Help topic and PLAN done.
        Build 3087 ms (templates changed, all recompiled). Tests: `CASE` (new) ok 0.9 s,
        `RECORD3` ok 0.8 s, `RECSTR` failed 0.8 s on a step 1 bug, fixed in 1c.
     1c. Step 1 bugs, fixed 2026-10-18, asm approved. `S_CHRIN` (`tpl/UXDOS/SYS.ASM`) called
        `con_line` with byte 1 left from the last line, so the second `INPUT` line started
        with the first one's text. On Tab, `CON_LINE`'s loop and the monitor called again, and
        the kept text showed twice: `INPUT A$` with `ab` Tab `c` showed `? ababc`. Fix: new
        API call 49 `con_edit` (`$03D3`, `api_con_edit` in `console.s`) has the step 1
        contract; `con_line` clears byte 1 and drops Tab, as before step 1. The two share the
        body; `con_end_key` (1 byte of RAM) is `$09` for `con_edit` and `$0D` for `con_line`,
        and the compare with Enter comes first. The monitor and `DOS.CON_LINE` are back to their
        pre-step-1 code; `DOS.CON_EDIT` calls `API_CON_EDIT`. ROM +10 bytes over step 1:
        `RODATA` ends at `$EDD8`, 4598 bytes free below `$FFCF`. `CMDSHELL.COM` 19179 and
        `DOSAPI.COM` 8562, 25 less each. Build 2903 ms. Tests: `RECSTR` ok 0.8 s, `MONITOR`
        ok 0.7 s, `ASK` ok 0.7 s, `SHVARS` ok 0.9 s, `FILES` failed on the two sizes, as
        expected; updated, ok 0.4 s, and the golden equals HEAD again; `DOSAPI` ok 0.9 s,
        `INPUT2` ok 0.8 s. A throwaway shell test of `INPUT` with Tab showed `? abc`.
        Owed to the doc batch: PLAN's `con_line` row (line 261) and a `con_edit` row.
        Full suite, the 7th step: shell 47 tests, 0 failed, 33.2 s; UXCBASIC 185 tests, 0
        failed, 48 s; none past 5 s.
     2b. Shell Tab completion, done 2026-10-18 (UXCBASIC only). `CMDSHELL.UXB`: the prompt
        reads with `DOS.CON_EDIT` until Enter; each Tab runs `COMPLETE_WORD`. It clears the
        line from the screen (locate the prompt end, spaces, locate again; `PROMPT_COLUMN` is
        `POS(0)` after the prompt), then puts match `COMPLETE_INDEX` of the last word in its
        place. `FIND_MATCH` counts the matches in order: the names of `BUILTIN_NAMES$` (a
        first word with no directory part and no dot, `UCASE$` prefix), then `FINDFIRST` of
        the stem + `*` (+ `.*` with no dot in the name part), with directories and a `\` on
        each, names starting with `.` left out, then `*.COM` and `*.CMD` in each directory of
        PATH$ for a first word, shown without the extension. Shift+Tab goes back; both wrap.
        A line Tab did not leave (`COMPLETE_TEXT`) starts again. `START_PATH` and
        `NEXT_DIRECTORY` walk PATH$, for `FIND_PROGRAM` too. Trap: a UXCBASIC name is at most
        16 characters (`NAME TOO LONG`). CMDSHELL passed 4096 fixups (`TOO MANY FIXUPS`):
        pyuxc `K_FIX_BANKS` 4 to 8, `K_FX_MAX` 8192, UXCBASIC PLAN line 405 done.
        `CMDSHELL.COM` 21024, +1845: built-ins 506 (the list 208), PATH programs 202. The
        CONST used in place, not copied to `LEFT_TEXT`, saved 17 bytes and a 208-byte copy a
        match; the `MID$` prefix form and a `FOR` redraw were bigger. Builds 3007 ms (the
        compiler changed, all recompiled), 1049 ms. Tests: `SHTAB` (new: files, a directory
        argument, lower case, built-ins cycling and wrapping, typing after Tab, two
        directories, no match, PATH$) ok 0.7 s; `SHRUN` ok 0.9 s, `SHELL` ok 0.5 s, `FILES`
        failed on the size, as expected; updated, ok 0.4 s; `DIRS` ok 0.8 s, `DISK` ok
        0.5 s, `CMDLETS` ok 1.7 s, `TREE` ok 1.1 s. x16emu -bas cannot type Shift+Tab, so no
        test covers it. Owed to the doc batch: the shell's Tab in `HELP.TXT` and PLAN
        section 8. Steps since the full suite: 1.
   - Command history in the shell (the user, 2026-10-18): the last 8 lines, Up and Down. The
     lines live in VARBANK system strings 13 to 20 (`HEAP.SYS_STRINGS_SET` and `_GET`), 13 the
     newest; on Enter 19 to 20 down to 13 to 14 move, then the line goes to 13. An empty line
     or a repeat of the newest is not kept. Two steps.
     1. `con_edit` ends on an extended key, done 2026-10-18, asm approved. `api_con_edit`
        returns as `con_getkey` does: A = $0D, $09 or 0 for an extended key; X = the scan
        code, 0 for Enter and Tab; Y = `kbd_mods`. `con_line` still drops the extended keys
        (`con_end_key` = $0D). The scan code rides in X through the tail. ROM +12 bytes,
        counted by hand. `DOS.UXI`: new `REG_AX AS UWORD AT $030C` (REG_X * 256 + REG_A);
        `CON_EDIT` returns `REG_AX`, a UWORD as `WAITKEY()` gives it (`KEYS.KEY_UP` and so
        on), and `CON_EDIT_MODS = REG_Y`. `REG_AX` in place of `REG_X * 256 + REG_A` saved
        32 bytes. `tools/api.py` contract updated; `docs/API.md` regenerated. `CMDSHELL.COM`
        21031, +7 (the UWORD compare with 9). Builds 3171 ms, 2811 ms (`DOS.UXI` changed,
        all recompiled). Tests: `SHTAB` ok 0.6 s, `SHELL` ok 0.5 s, `FILES` failed on the
        size, as expected; updated, ok 0.4 s. No test types an extended key. Steps since the
        full suite: 2.
     2. The shell, done 2026-10-18. The slots are a ring, not a shift: `HISTORY_NEXT` (0 to
        7) is the slot the next line goes to, and `HISTORY_SLOT(BACK)` gives the descriptor
        BACK lines before it (1 the newest). `HISTORY_BACK` counts the lines Up went back;
        Down past the newest gives an empty line. The prompt loop: `KEY_TYPED =
        DOS.CON_EDIT(LINE_TEXT)`; 13 ends it; any other key runs `CLEAR_LINE` (the redraw
        taken out of `COMPLETE_WORD`), then 9 runs `COMPLETE_WORD` and the rest `RECALL_LINE`,
        which acts on Up and Down only. `KEEP_LINE` after the loop. Trap: `#INCLUDE
        "KEYS.UXI"` stops the compile with TOO MANY NAMES (`K_SY_MAX` 1008), so the shell has
        its own `KEY_UP` $4800 and `KEY_DOWN` $5000. The shell is near that limit.
        `CMDSHELL.COM` 21459, +428. Builds 721 ms (NAME TOO LONG), 860 ms (TOO MANY NAMES),
        1082 ms. Tests: `SHTAB` ok 0.7 s, `SHELL` ok 0.5 s, `FILES` failed on the size, as
        expected; updated, ok 0.4 s. No test types an arrow. Steps since the full suite: 3.
        Option, its own step: a pasted 0 takes the next queued byte as its scan code (about
        10 bytes of asm), so a test could type the arrows. Owed to the doc batch: Up and Down
        in `HELP.TXT` and PLAN section 8.
   - To do, commands the user listed (2026-10-17). None is in PLAN section 11 yet; each needs a
     step and a talk with the user first.
     - Search and text: `FIND` (text in files), `SORT`, `GREP` (done), `HEAD` (first n lines), `TAIL` (last n lines), `WC` (line, word
       and byte counts). `FC` (text compare) and `COMP` (binary compare) are for version 2.0.
     - Files: `XCOPY` (done), `MOVE`, `MORE` (paged display), `ATTRIB`, `TREE`. The
       shell already has `COPY`, `RENAME` or `REN`, and `DELETE` or `DEL`.
     - System: `TIME`, `DATE`, `UPTIME`.
     - Paths: `PUSH` saves the current path, and `POP` loads it back (the user, 2026-10-17).
     - The API calls `attrib` (8) and `filetime` (9) go to `api_bad`: `ATTRIB` needs asm
       first.
     - Clock, the user's order (2026-10-18), asm approved. Steps:
       1. Done 2026-10-18, the clock calls. `src/asm/clock.s`: `getdate`, `setdate`,
          `gettime` and `settime` (33 to 36) on the MCP7940N, I2C device `$6F`, years 2000 to
          2099. A read takes three registers, then the first again, and starts over when it
          changed. `getdate` works out the weekday from the date (Sakamoto, checked against
          Python for every day of 2000 to 2099). `setdate` checks the days of each month and
          February 29, and writes the weekday with VBATEN. `settime` writes the seconds as 0
          first, then the minutes, the hours and the seconds with ST. `i2c_write_byte` is new
          in `src/asm/i2c.s`. `tools/api.py` marks the four calls written. `lib/DOS.UXI`:
          `GETDATE`, `SETDATE`, `GETTIME`, `SETTIME`, `TICKS_LONG` (all 32 bits) and the
          variables `YEAR`, `MONTH`, `DAY`, `WEEKDAY`, `HOURS`, `MINUTES`, `SECONDS` and
          `TICK_COUNT`, 12 bytes of RAM in each program. ROM +353 bytes: `clock.s` 289 of
          code and 31 of tables, `i2c_write_byte` 33; KERNELRAM +3, to `$06BC`. CODE and
          RODATA end at `$EDAB`. No other program changed size. Build 2566 ms, all programs
          compiled, the new baseline. New test `CLOCK`; golden `FILES` gains `CLOCK.COM`.
          Tests: `CLOCK` ok 0.4 s, `DOSAPI` 0.6, `FILES` 0.4, `SHFILES` 0.6, `DIRS` 0.8,
          `SHELL` 0.5. The tests boot x16emu without `-rtc`.
       2. Done 2026-10-18, the commandlets `C:\DOS\DATE.CBIN`, `TIME.CBIN` and
          `UPTIME.CBIN`, from `src/cbin/DATE.UXB`, `TIME.UXB` and `UPTIME.UXB`, on
          `CBIN.UXI` as `DISKFREE` is. Not shell built-ins (the user, 2026-10-18). ISO, 24
          hours. `DATE [yyyy-m-d] [SILENT]` prints `Sun 2026-10-18`; P1$ `2026-10-18`, P2$
          `Sun`, P3$ to P5$ the year, month and day. `TIME [h:mm[:ss]] [SILENT]` prints
          `13:45:07`; P1$ `13:45:07`, P2$ to P4$ the hours, minutes and seconds. Each number
          of a time is 1 or 2 digits, the seconds 0 when left out. With an argument they set
          the clock, print nothing and read it back into the P$. A bad argument prints
          `Invalid date` or `Invalid time` unless SILENT, sets P1$ to "" and gives exit code
          1. `UPTIME [SILENT]` prints `0 days 00:00:03`; P1$ the seconds since boot, P2$ the
          days, P3$ `00:00:03`. VSYNCs times 21 over 1250, in two parts so the product stays
          in 32 bits. Sizes: `DATE` 2897 bytes, `TIME` 2698, `UPTIME` 2968. CMDSHELL
          unchanged. Build 935 ms, the 3 compiled, the new baseline. Test `CLOCKCMD` ok 2.0
          s, then 1.2 s. Trap: the emulator's RTC runs on host time, so the test reads the
          time back only straight after a set.
       3. Done 2026-10-18, the docs batch, no code. PLAN: `DATE` and `TIME` out of the
          shell's statements and 7h; the commandlets list and their text in section 8; 7i6;
          the RTC under the drivers; `HEAP.SYS_STRINGS_GET`, not `DOS.`. UXCBASIC.PLAN: the
          power-of-2 rule of `ex_power`. `HELP.TXT`: topics `DATE`, `TIME` and `UPTIME`,
          each `(Command line or Script)`. Build 523 ms, the new baseline. Test `CMDLETS`
          ok 2.0 s, its golden gains the 3 topics in the `HELP` list.
   - `TREE` done 2026-10-18: `C:\DOS\TREE.COM` from `src/dos/TREE.UXB`, for the command line,
     no P$ and no SILENT (the user, 2026-10-18). `TREE [d:][path] [-F]` draws a tree, the
     layout the user gave (2026-10-18): a blank line, `ROOT` or the start path, then one line a
     directory, depth first, `" +- "` and the name, 4 columns in a level. A `" |  "` bar runs
     down past the lines of a directory that has a later directory beside it; the last one is
     `" +- "` too. `-F` (or `-f`) lists each directory's files under its line, 4 columns in,
     after a bar when it has a directory, then a line of the bars alone (trailing spaces). A
     start with no directories prints `No sub-directories exist`. The path may be relative or
     hold `..`: `CHDIR` checks it, `GETCWD` gives it from the root, and the old directory
     comes back. UXCBASIC has no recursion, so `STATES` keeps the 21 bytes before `FIND_ATTR`
     of each level's find buffer, 32 levels, and `FINDNEXT` resumes from them. Each directory
     costs a look-ahead scan to the next directory beside it, for the bar, and the resume
     scans that stretch again; `-F` adds a scan for a sub-directory and one for the files. A
     directory 32 levels down, or whose path passes 237 characters, is listed, not entered.
     Errors, exit code 1: `Invalid drive`, `Invalid path` (a file too), `Invalid switch`,
     `Too many parameters`; a read error prints its message, exit code 2. `TREE.COM` 3595
     bytes; RAM 672 of states, 32 of path lengths, 5 strings of 255. ROM and shell: none.
     Build 785 ms, the new baseline. `TREE` ok 1.0 s; `DISK` 0.5 and `FILES` 0.4 ok, no golden
     change. Traps: a number DIMed in a SUB keeps its value from the last call, only a string
     is cleared, so `LIST_FILES` sets `ANY_FILE = 0`; a name over 16 characters is an error
     (`NAME TOO LONG`); a one-line `IF` takes no `ELSE`. Owed to the doc batch: the
     `HELP.TXT` topic `TREE` (it changes the `CMDLETS` golden's `HELP` list), PLAN section 8
     and 11.
   - `MORE` done 2026-10-18: `C:\DOS\MORE.COM` from `src/dos/MORE.UXB`, for the command line,
     not for scripts (the user). `MORE [file]` reads the file, or handle 0 with no file, in
     512-byte blocks and writes runs of it with `WRITE 1`. After the screen's rows less 1
     (`CONS.SCREEN_ROWS() - 1`, 29) it prints `-- More --` on the last row, waits on
     `WAITKEY()` (the keyboard, not handle 0, so it works after a `|`), then `POS(0) = 0` and
     `Esc[K` clear the prompt. The prompt shows only when another byte follows. Rows are counted
     as `console.s` writes them: CR ends a line, an LF right after a CR does nothing, an LF
     alone moves a row, the 80th column wraps, a tab goes to the next multiple of 8, BS back a
     column, FF clears (count 0), BEL and $0F nothing; each escape sequence byte counts as a
     column. Ctrl+Z ends the text. Before each read, `IOCTL_IN_STATUS` 0 ends it: a read of
     `CON` waits for keys, so `MORE` alone at the prompt prints nothing. A second name: `Too
     many parameters`, exit 1. Open fails: `DOS.ERRMSG`, exit 2. Any key goes on; there is no
     Q. `MORE.COM` 2131 bytes; RAM 512 buffer, 255 name, 12 of numbers. ROM and shell: none.
     Build 771 ms, the new baseline. New test `MORE` (`tests/MORE.IN`): a missing file, two
     names, `README.TXT` (no prompt), `LONG.TXT` and `LIST DOCS\LONG.TXT | MORE` (29 lines,
     the prompt, key `x`, lines 30 to 50; the `x` line's CR gives the shell an empty line);
     checked by hand. `MORE` ok 0.7 s; `DISK` 0.4 and `FILES` 0.4 ok, no golden change. Owed
     to the doc batch: the `HELP.TXT` topic `MORE`, PLAN section 8 and 11.
   - `HEAD` done 2026-10-18: `C:\DOS\HEAD.COM` from `src/dos/HEAD.UXB`, for the command line,
     no P$ and no SILENT (the user, 2026-10-18). `HEAD [-n count] [file]`, Unix form, count 0
     to 65535, 10 when left out (the user). No file reads handle 0, with the `IOCTL_IN_STATUS`
     check of `MORE`. A CR, an LF, or CR LF ends a line; the first byte after the last line end
     stops it, so the LF of a CR LF is written. Ctrl+Z ends the text. `-n` or `-N`. Errors, exit
     code 1: `Invalid switch`, `Required parameter missing` (`-n` alone), `Invalid parameter`
     (not digits, or past 65535), `Too many parameters`; open fails: `DOS.ERRMSG`, exit 2. The
     count is built digit by digit with an overflow check, 248 bytes less than `LVAL`.
     `HEAD.COM` 2583 bytes; RAM 512 buffer, 2 strings of 255, 13 of numbers. ROM and shell:
     none. Build 724 ms, the new baseline. New test `HEAD` (`tests/HEAD.IN`): the errors,
     `README.TXT`, `LONG.TXT` (10 lines), `-n 3`, `-n 0`, `LIST ... | HEAD -N 2`; checked by
     hand. `HEAD` ok 0.9 s, `MORE` 0.7 ok. Next: `TAIL`, the same form. Owed to the doc batch:
     the `HELP.TXT` topic `HEAD`, PLAN section 8 and 11.
   - `TAIL` done 2026-10-18: `C:\DOS\TAIL.COM` from `src/dos/TAIL.UXB`, the form, switches,
     errors and exit codes of `HEAD`. A pipe and `FROM` give handle 0 a file, so `TAIL` seeks:
     it takes the start (seek from the position) and the end (seek from the end), reads back
     from the end in blocks of 512 until count line ends, then seeks to the byte after and
     copies forward up to a Ctrl+Z or the end. A device stays at 0, so start = end gives no
     text, and `TAIL` alone at the prompt prints nothing. A line end in the last byte of the
     text ends no line before it; the CR of a CR LF is no line end of its own; a Ctrl+Z met
     on the way back resets the count. The scan reads only the tail, so a Ctrl+Z before it is
     not seen. Positions are word pairs with a hand borrow: a `ULONG` form was 4274 bytes,
     830 more. `TAIL.COM` 3444 bytes; RAM 512 buffer, 2 strings of 255, 22 of numbers. ROM and
     shell: none. Build 792 ms, the new baseline. New test `TAIL` (`tests/TAIL.IN`): the
     errors, `README.TXT`, `LONG.TXT` (10), `-n 3`, `-n 0`, `-n 60`, `LIST ... | TAIL -N 2`,
     a CR LF file by `PRINT TO`/`APPEND` with `FROM`, `TAIL` alone; checked by hand. No Ctrl+Z
     test: the shell has no `CHR$`. `TAIL` ok 1.2 s. Owed to the doc batch: the `HELP.TXT`
     topic `TAIL`, PLAN section 8 and 11.
   - Doc batch done 2026-10-18: `HELP.TXT` topics `TREE`, `MORE`, `HEAD`, `TAIL`, each
     `(Command line only)`. PLAN section 8 entries for the four after `VIEW`; section 11 step
     7i names `VIEW`, `TREE`, `MORE`, `HEAD`, `TAIL` as the DOS utilities after it. Four
     `HELP.TXT` lines past 80 characters, cut by `HELP`, are split in two: the `P1$` line of
     `DATE`, the seconds line of `TIME`, and the count lines of `HEAD` and `TAIL`. Every line
     is now 80 at most. Build 743 ms, the new baseline. Goldens changed: `CMDLETS` (the `HELP`
     list gains `TREE MORE HEAD TAIL`) and `TREE` (`-F` lists `HEAD.COM`, `MORE.COM`,
     `TAIL.COM` in `\DOS`; `MORE.COM` was missing since the `MORE` step). Full suite: `TREE`
     failed on that; updated, `TREE` ok 1.3 s.
     Trap: `tests.py` stops reading at the first byte that departs from the golden, so a
     stale golden shows output cut mid-line, as if the program hung.
   - `TREE` switch `-F` done 2026-10-18: the user's rule, switches start with `-`, never `/`.
     `TREE.UXB` tests the first character for `-`; `TREE.COM` 3595 bytes, no change. `-F`
     in `TREE.UXB`, `HELP.TXT`, PLAN section 8 and `tests/TREE.IN` (`-F`, `-f`, `-X`). Build
     744 ms. `TREE` ok 1.1 s, `CMDLETS` ok 1.6 s. Steps since the full suite: 1.
   - `HELP.TXT`: the user marks each topic as for scripts, the command line, or both
     (2026-10-17).
   - Done: `PROMPT$` `$` codes (see State). No `$T`, `$D`, `$V`, `$H` or `$E`. `HELP.TXT` has
     no `PROMPT$` topic.
   - Long file names are needed (the user, 2026-10-16). Talk the design over with the user
     before a step goes into PLAN section 11. PLAN section 5 has the target: 32 characters a
     name, 255 a path.
     - The user's choice (2026-10-18): take the x16-rom FAT32 library (X16Community/x16-rom,
       `fat32/fat32.s`, master `fbe32a6`, Frank van den Hoef and Michael Steil, 2-clause BSD)
       for its testing; it replaces `fat.s`. The limits stay 32 and 255. Not started: the
       open questions below go to the user first. `src/asm/sdcard.s` is already a port of its
       `sdcard.s`, with the notice.
     - Measured with our ca65 against stubs: `fat32.s` code 7977 bytes, of it 483 the 65816
       `fat32_read_long` and `fat32_write_long`; `match.s` 453 (CMDR-DOS policy: ISO-8859-15,
       `*` ends a part, `,` refused). BSS 1199 bytes, of it `lfn_buf` 640 (20 entries);
       `fat32_dirent` 278 (name 256). Zero page 8 bytes, and the KERNAL's `krn_ptr1` (2) and
       `bank_save` (1). Our `fat.o` is 3563 bytes.
     - What it does: `read_dirent` collects LFN entries into `lfn_buf` with index and checksum
       checks, and falls back to the 8.3 name with the case flags of byte 12. Every create
       writes an LFN, even for an 8.3 name; the 8.3 alias is 8 hex digits of the entry's LBA,
       `~`, its slot, `~`, so no `~1` search. `delete_entry` marks the LFN entries too. Rename
       is create, then delete. One shared `sector_buffer`; `FAT32_CONTEXTS` 4 (8 fit in the
       256-byte limit). The cwd is per volume; `fat32_walk_tree` gives the names up to the
       root. Paths are Unix: `/`, no drive. Free space reads the FSInfo count.
       `mount` needs an MBR partition of type $0B or $0C and 2 FATs: `mksd.py` images pass.
       Its BSS sits in RAM bank 0; `x16_banked_copy` selects `bank_save` for a buffer at
       `$A000-$BFFF` and goes back to bank 0.
     - Trap: `add_lfn_entry` has no bound: an LFN of more entries than `lfn_buf` holds
       overwrites what follows. A smaller `lfn_buf` needs a check on the entry count.
     - Trap: ca65 V2.19 has no `.macpack longbranch` file here, and a cheap local label is not
       seen inside a macro (`jmi @stream_save`, `jcc @error`).
     - Draft layout: ROM bank 1 holds the library, its callbacks, a layer for our calls, and
       the SD driver. The gate already calls a routine in any ROM bank. RAM bank 0 holds the
       BSS and a 256-byte path buffer. Bank 0 drops `fat.s`.
     - The user's answers (2026-10-19): keep the case as typed on create; Windows wildcard
       rules; grow the find buffer from 63 bytes to about 84; keep the library's hex 8.3
       aliases. The asm of F1 to F7 is approved.
     - Steps: F1 two ROM banks and the far calls; F2 the library in bank 1, unused, with the
       callbacks and the SD glue (65816 code dropped); F3 reads on it (open, read, seek,
       close, exec load, findfirst, findnext); F4 writes (create, write, delete, rename,
       mkdir, rmdir, free space); F5 chdir and getcwd; F6 the 32/255 limits, LFN in `mksd.py`
       and `fatcheck.py`, new tests, the shell's 12-character pipe path; F7 delete `fat.s`,
       docs. Each step runs the tests of the code it touches.
     - Done, F1 (2026-10-19): `rom.cfg` links banks 0 and 1; `build/6502DOS.ROM` is 32768
       bytes. `src/asm/far.inc` holds `FARCALL target [, entry]` (6 bytes a call), `JSRFAR`
       and the IRQ entry and exit. `jsrfar` (bank 0, `gate.s`) and `jsrfar1` (bank 1,
       `bank1.s`) read the 3 bytes after the JSR, push the caller's bank and end in the gate's
       tail at `gate_far`; A, X, Y and C go in and out. About 140 cycles a call. No RAM, no
       zero page: they share `gate_a`, `gate_x` and `gate_vector` with the gate.
       - Trap, found in x16emu's source (`vp6502`): an interrupt's vector pull selects ROM
         bank 0, but `$01` reads the interrupted bank until written. So bank 0's vectors serve
         every interrupt. `irq_entry` saves A and the bank, `irq_exit` selects the bank and
         RTIs; both sit at `$FFA0` with the same 14 bytes in each bank, since a write to `$01`
         goes on at the next address in the new bank. `irq` and `nmi` in `boot.s` exit
         through `irq_exit`; a BRK drops the bank and goes to the monitor in bank 0. x16-rom's
         `__irq` does the same in RAM. Bank 1's own vectors point at its copy.
       - `bank1.s` holds `b1_probe` at `$C000` for the new test `FAR` (`tests/FAR.S`): it
         waits for an IRQ in bank 1, writes "B" through `FARCALL CHROUT, jsrfar1`, and returns
         `api_con_colour`'s A with carry set going in: A $05, X $5A, Y $A5, carry clear. F2
         puts the library's jump table at `$C000`: move the probe, or drop `FAR`.
       - Cost: bank 0 +74 bytes (`jsrfar` 49, `irq` and `nmi` 11, entry and exit 14), about
         4430 bytes free below `$FFA0`; bank 1 holds 96. An IRQ costs about 22 cycles more.
         RAM and zero page: none.
       - Build 1.14 s, the new ROM-only baseline. Tests: `FAR` ok 0.8 s, `MONITOR` 0.7 (has a
         BRK), `BOOT` 0.8, `SHBOOT` 1.0, `CLOCK` 0.9, `BREAK` 0.9, `SHELL` 1.1. Steps since the
         full suite: 4.
       - Docs owed: PLAN §3 (ROM banks, `jsrfar`, the vector-pull trap), §9 (the ROM layout);
         `mem.inc`'s `GATE_PAGE` comment names jsrfar and the IRQ vectors, which are not there.
       - Committed by the user.
     - Done, F2 (2026-10-19): the library in bank 1, linked, not called.
       - `src/asm/fat32.s`, `fat32_match.s`, `fat32_lib.inc`, `fat32_regs.inc`: copies of
         x16-rom `fat32.s`, `match.s`, `lib.inc`, `regs.inc` (master `fbe32a6`), made by
         `port_fat32.py` in the session scratchpad, from the upstream copy in the old session's
         `scratchpad/x16fat`. Each header names the changes and holds the BSD-2 text. Changes:
         code in `B1CODE`, variables in `FATBSS`; `fat32_read_long`, `fat32_write_long` and
         the MVN trampoline gone; the 2 long branches written out; `krn_ptr1` and `bank_save`
         imported at the top; `regs.inc` takes `mem.inc` and `ram_bank = RAM_BANK`.
       - `src/asm/fat32glue.s` (bank 1): the library's zero page (`fat32_bufptr`,
         `fat32_lfn_bufptr`, `fat32_ptr`, `fat32_ptr2`, `krn_ptr1`, 10 bytes); `bank_save` is
         kernel.s `saved_bank`; `fat32_size`, `fat32_dirent`, `fat32_errno`, `fat32_readonly`,
         `skip_mask`, `sector_lba`; `sdcard_read_sector` and `sdcard_write_sector` fill BLK_*
         and FARCALL `sd_input`/`sd_output` (now exported), carry flipped;
         `sdcard_set_fast_mode` does nothing; `to_lower` ASCII only. No `sdcard_init`: the
         library does not call it. Trap: `fat32_init` does not clear the glue's variables;
         the caller sets `fat32_readonly`. No library jump table: bank 0 calls by FARCALL.
       - RAM bank 0: `FATBSS` $A100-$A6CC (1485 bytes, rom.cfg `FATRAM` to $A7FF), the sector
         buffer `FATBUF` $A900-$AAFF (`FATBUFRAM`), past `KBD_QUEUE` at $A800. `mem.inc` has
         `FAT32_RAM` and `FAT32_BUFFER`.
       - Zero page: moved to KERNELRAM, from `fat.s` `path_len`, `path_index`, `path_drive`,
         `fcb_limit`, `sft_entry` (back to zero page or gone in F7), from `kernel.s`
         `io_refused`, `open_access`, `open_flags`, `open_create`. KERNELZP is full, $80-$FF.
         `fcb_name` and `free_next` cannot move: the find buffer copies `dpb` to `pos+1`, and
         `fat_entry` takes `free_next` and `cluster` by zero page address. KERNELRAM ends $06C5.
       - Cost: bank 0 CODE +35 bytes; 4445 bytes free below $FFA0. Bank 1 B1CODE 8050 bytes,
         8212 free below $FFA0.
       - Build 758 ms, the new baseline. Tests: `FAR` ok 0.6 s, `DISK` 0.4, `DIRS` 0.9,
         `FILES` 0.4, `HANDLES` 0.4, `WRITE` 0.6. The user stopped testing there (low tokens);
         then `SHELL` ok 0.9 s, `BOOT` 0.4, `SHBOOT` 0.5, `EXEC` 0.9 (build 1.93 s, rc 0).
         Steps since the full suite: 5.
       - Committed by the user (F1 and F2 in ab76f5e and 8fb9ae1).
     - F3 split: F3a open for reading, read, seek, close, exec load; F3b findfirst and
       findnext (the find buffer grows, `match.s` needs Windows `*` rules: today `*` ends the
       part, so `A*.TXT` matches `ABC.DOC`).
     - Done, F3a (2026-10-19), committed by the user as 7081af3 "Step 3". Build 756 ms:
       - New `src/asm/fat32dos.s` (bank 1): `lib_init` (`fat32_init`, `fat32_readonly` 1,
         `skip_mask` 0, `sector_lba` all $FF), `lib_open` (path at r0 in the caller's bank,
         read byte by byte with `path_char`; drive checks on fat.s's `DPB`; `\` to `/` into
         `lib_path`; `*` or `?` gives error 2; the library's cwd set from `DPB_CWD`; the
         directory part by `fat32_chdir`, error 3 when missing; returns A = the context,
         `file_size`, and `cluster` = context then 7 zeros for the SFT), `lib_read`,
         `lib_seek`, `lib_close` (context in A, RAM bank 0 selected), `errno_errors` table.
       - `fat32_regs.inc`: `FAT32_CONTEXTS` 8, `FAT32_VOLUMES` 1. `fat32.s` exports
         `fat32_cwd`. `mem.inc`: the `DPB_` fields moved there from fat.s; `SFT_LIB` = $01 in
         `SFT_FLAGS`, the context in `SFT_CLUSTER`. fat.s exports `DPB`, `current_drive`.
       - kernel.s: `open_common` sends access 0 (no create) to `lib_open`, flags `SFT_LIB`;
         `@refused` closes the context when no handle or SFT entry is free; `handle_io` sends
         `SFT_LIB` reads to `lib_io` (adds r1 to `SFT_POS`); `api_close` closes the context
         only when `SFT_REFS` reaches 0; `bank_return`. fat.s: `api_seek` keeps the context and
         calls `lib_seek`; `buf_flush` calls `lib_forget` after each write (sets `sector_lba`
         to $FF). exec.s: `lib_open`, `exec_read`, `exec_close` (`exec_file` in KERNELRAM);
         every failure after the open closes the file.
       - boot.s copies `SHELL_PATH` to `MONITOR_LINE` before `API_EXEC`: bank 1 cannot read
         ROM bank 0, where the path lies.
       - Bug fixed in `lib_io`: `cpx` in the add loop clobbered the carry, so `SFT_POS` went
         wrong (15 read as $03000F) and IOCTL status said end of file early (DUP failed).
         Now a straight add, 2 bytes shorter.
       - Trap: tools/tests.py stops at the first line that departs from the golden, and the
         "got" printed after that line is cut short. A cut-off line is not a bug; capture the
         whole output with `--update` on a copy.
       - Goldens updated (not committed; their own commit): `EXEC`, `HANDLES`, `DISK`. Only
         leftovers changed, none in a call's contract: X after a failed open or exec ($FF or
         7 to 0), A after a close (0 to 1).
       - Tests: `SHBOOT` ok 0.5 s, `EXEC` 0.7, `BOOT` 0.4, `HANDLES` 0.4, `FILES` 0.4, `DISK`
         0.4, `DIRS` 0.8, `WRITE` 0.7, `FAR` 0.4, `SHELL` 0.5, `DUP` 0.4, `SEEK` 0.4, `TAIL`
         1.2, `HEAD` 0.9, `GREP` 1.6, `SHSCRIPT` 0.8, `XCOPY` 1.3. Steps since the full suite:
         6; F3b is the 7th, so the full suite runs after it.
       - `lib_path` $A574, `lib_len` $A674, `lib_slash` $A675; `fat32_errno` $A792,
         `sector_lba` $A795. FATBSS $A100-$A798.
     - Done, F3b (2026-10-19), committed 1a12853 (code) and 1331cb4 (goldens). Build 1.54 s (7
       commandlet compiles), ROM only
       about 0.9 s, the new baseline:
       - findfirst and findnext on the library: `api_findfirst` and `api_findnext` live in
         `fat32dos.s`, bank 1; the gate calls them there (api_table holds the bank). fat.s lost
         its find code, `FIND_STATE` and the find-buffer order rule on its zero page (`dpb` to
         `pos+1`): `fcb_name` and `free_next` may move now.
       - Find buffer 63 to 83 bytes (`tools/api.py`): the search 0-40 (`FIND_PATTERN` 0, 33
         bytes, the name part ended by 0 and zero-filled; `FIND_SEARCH` 33, findfirst's A;
         `FIND_POS` 34, 7 bytes: cluster, sector in it, offset in `sector_buffer`), `FIND_ATTR`
         41, `FIND_TIME` 42, `FIND_DATE` 44, `FIND_SIZE` 46, `FIND_NAME` 50. A pattern over 32
         characters gives error 2. The volume label never matches ($08 dropped from the doc).
         find_put copies up to the end of the name only.
       - `fat32dos.s`: `lib_enter` (bank, path, context, chdir) shared by `lib_open` and
         `api_findfirst`; `lib_drop` closes and frees the context on a fault. `path_copy` sets
         `lib_wild` (bit 7: the name part holds `*` or `?`); a wildcard in a directory part
         gives error 3 (was 2) for open and find. The find buffer is built in `lib_path`
         (`lib_find`): the pattern copy runs forward, so it cannot overrun its source.
       - `fat32.s` adds `fat32_tell_dir` and `fat32_seek_dir` (import `fat32_dir_pos`, which
         fat32dos.s sets to `lib_find + FIND_POS`). `fat32_match.s` `match_name`: Windows
         rules: `*` any run, dots too, by one backtrack point (`star_pattern`, `star_name`);
         `?` one character; a trailing `.` or `.*` matches the end of a name with no dot.
         `*.` lists the names with no dot; `*` lists every name.
       - `DIR_` entry fields moved from fat.s to `mem.inc`. Monitor `MONITOR_FIND` is
         `MONITOR_OUT + $20` (an assert keeps it below `GATE_PAGE`).
       - LFN in `tools/mksd.py` (the user, 2026-10-19: commandlets named `.CBIN`): a name that
         is not 8.3, up to 32 characters, goes in as a long name as typed, with an alias
         `BASE~N.EXT`. build.py compiles commandlets to `build/DOS/NAME.CBIN`. Stale `.CBI`
         outputs in build/DOS must be deleted by hand once (done here). fatcheck.py already
         skips LFN entries.
       - `lib/DOS.UXI` `DIM FIND_BUFFER(FIND_BUFFER_SIZE)`. TREE and XCOPY `STATE_SIZE` 41,
         `STATES_SIZE` 1312: RAM +640 bytes each.
       - Cost: bank 0 CODE -164 bytes; bank 1 B1CODE +483 (end $E2FD, 7330 free below $FFA0);
         FATBSS +3 ($A100-$A79B).
       - Tests: `DISK` ok 0.5 s (DISK.IN dumps $1300-$1352), `DOSAPI` 0.9 (`FIND *` became
         `FIND *.`, `FIND \DOCS\*O*.TXT` added), `CWD` 0.5, `WRITE` 0.7, `MONITOR` 0.4, `DIRS`
         0.9, `TREE` 1.4, `XCOPY` 1.5, `XCOPYS` 1.3, `SHFILES` 0.7, `SHELL` 0.5, `FILES` 0.5,
         `SHTAB` 0.5, `WHERE` 1.2, `CMDLETS` 1.5.
       - Full suite (step 7), 34.7 s: 46 ok, 3 failed. Fixed, rerun: `TREE` ok 1.2 s (`.CBIN`
         names), `CLOCKCMD` ok 1.5 s (UPTIME 4 to 5 s: lookups through the library are
         slower). Still failing: `SHRUN`: `COPY ARGS.COM BIN\TOOL.CBIN` creates through fat.s,
         which cuts the name to `TOOL.CBI`, so `TOOL` is not found. F4 (create on the library)
         fixes it; the golden stays as it is.
       - Goldens updated (their own commit): `DISK`, `DOSAPI`, `FILES` (DOSAPI.COM size),
         `TREE`, `CLOCKCMD`. Test sources changed: `DISK.IN`, `DOSAPI.UXB`.
       - Steps since the full suite: 0.
       - Docs owed: API.md is generated; PLAN wildcard rules (§ names: `*` fills with `?`),
         the `.CBIN`/`.CBI` trap (PLAN line ~654), the 8.3-only line, §3, §9; NOTICE;
         `GATE_PAGE` comment.
     - F4 split (2026-10-20): the user's choice: a library create, mkdir or rename of a name
       that fits 8.3 gets that name, upper case, as its short name; a long name keeps the hex
       alias. So fat.s still finds every name the library makes, and the steps stay small: F4a
       create, write, close; F4b delete, rename, mkdir, rmdir, diskfree; F5 chdir, getcwd.
     - Done, F4a (2026-10-20), committed 493144d. Build 845 ms, ROM only:
       - Every file handle is the library's now. `lib_open` (bank 1) takes A = access and
         carry set to create with `create_attr` (masked to read only, hidden, system, archive);
         access 1 or 2 on a read-only file gives 5; a blank or wildcard name on create gives 3.
         kernel.s `open_common` sends every non-device open there; exec.s passes A = 0, carry
         clear. `api_close` closes every non-device through `lib_close`.
       - `lib_io` (bank 1, replaces the kernel's) takes Y = the SFT entry, X = 1 read or 0
         write, moves `SFT_POS`. `lib_write`: a position past the size first takes zeros
         (`fat32_write_byte`, a byte at a time); a full drive (errno 0) gives r1 short, carry
         clear; sets `SFT_FILE_SIZE` from the context. `errno_errors` maps errno 0 to 5.
       - Two sector buffers: the library's writes empty fat.s's (`buf_forget`: `buf_drive` =
         $FF after a create, a write, a close). fat.s `lib_forget` empties the library's only
         when it holds `BLK_SECTOR`, the sector just written: a blind empty would lose a file's
         data not yet written, since `save_sector_buffer` writes to `sector_lba`. It keeps carry:
         `buf_flush` returns the carry after it (bug found: fat.s reads failed after a write).
       - `fat32.s`: `fat32_create` takes A = the attributes; `fat32_close` sets the archive bit
         of a file written; `create_shortname` makes a name that fits 8.3 (no `+,;=[]~`, no
         byte under `!` or over `~`) its own short name, upper case, else the hex alias
         (`short_limit`, 1 byte). Upstream bug fixed: `fat32_write` looped to its start, so the
         `ror krn_ptr1` took a stale carry as the stream flag: an overwrite across a sector end
         repeated one byte. It loops to `fat32_write_again` now.
       - `fat32_readonly` 0: the library writes. fat.s lost `file_io`, `file_close`,
         `file_copy`, `cluster_at`, `walk`; kernel.s lost its `lib_io` and the `SFT_MODIFIED`
         store. `file_find` and `file_create` stay for delete and mkdir.
       - Trap until F4b: fat.s `DEL` marks only the 8.3 entry, so a file the library made
         leaves its long-name entries orphaned. The library skips them (checksum); fatcheck
         skips long-name entries.
       - Names the library creates keep the case as typed: `DIR` shows `out.txt`, `Mixed.Txt`.
       - Cost: bank 0 CODE -579 bytes (4947 free below $FFA0); bank 1 B1CODE +387 (end $E480,
         6943 free); FATBSS +7 ($A100-$A7A2); KERNELRAM -3.
       - Tests: `SHRUN` ok 0.9 s (fixed), `WRITE` 1.1, `DUP` 0.5, `SEEK` 0.5, `HANDLES` 0.4,
         `FILES` 0.4, `DOSAPI` 0.7, `DISK` 0.5, `DIRS` 1.0, `EXEC` 0.7, `SHFILES` 0.8,
         `SHREDIR` 1.3, `SHSCRIPT` 1.1, `SHVARS` 0.8, `XCOPY` 1.7, `XCOPYS` 1.2, `TARGET` 0.5,
         `CLOCK` 0.4, `TED` 1.1, `SHELL` 0.5, `BOOT` 0.4, `SHBOOT` 0.5, `CMDLETS` 1.5, `WHERE`
         1.1, `TREE` 1.3, `GREP` 1.7, `HEAD` 1.0, `TAIL` 1.3, `MORE` 0.9, `VIEW` 1.0. No golden
         changed. fatcheck after creates, a long name, a mkdir and a DEL: no problems.
       - Steps since the full suite: 1.
       - Docs owed, added: PLAN on the short-name rule and the case kept on create.
     - Done, F4b (2026-10-20), committed b6bb965. Build 713 ms, ROM only:
       - `api_delete`, `api_rename`, `api_mkdir`, `api_rmdir`, `api_diskfree` live in
         `fat32dos.s`, bank 1, on the library. fat.s reads only now: it lost delete, rename,
         mkdir, rmdir, diskfree, `file_find`, `file_create`, `dir_make`, `dir_slot`,
         `buf_flush`, `buf_claim`, `lib_forget`, the cluster allocation and freeing, and the
         variables `free_next`, `buf_dirty`, `writing`, `free_pass`, `entry_copy`,
         `rename_drive`. It keeps chdir, getcwd, seek, mount and the path walk for F5.
       - `lib_enter` points `fat32_ptr` at the name part. `cwd_set` gives the library the
         drive's current directory with cluster 0 for the root, as a `..` entry holds it, so a
         directory made in the root gets `..` = 0. `name_check`: a blank name, only dots, or `*`
         `?` gives 3 on create, mkdir and the new name of rename, 2 on delete and the old name.
         `dir_change` maps a missing directory to 3. `drive_check` is split out of `path_start`.
       - rmdir: `fat32_chdir` into the name gives its cluster; equal to `DPB_CWD` gives 16. The
         library refuses a read-only directory (5).
       - rename: `lib_enter` on the new path (its directory checked, cluster kept in `lib_dir`),
         the path copied to `lib_new`; then `lib_enter` on the old path. Directories differ and
         `fat32_chdir` into the old name succeeds: a directory moved, 5. Then `fat32_rename`
         with both paths from the current directory. Trap: `lib_new` is fat.s's
         `SECTOR_BUFFER` ($0400); `lib_close` empties that buffer by `buf_drive`.
       - diskfree: the free clusters are the library's FS info count (`fat32_free_clusters`,
         exported); sectors per cluster and the clusters still come from fat.s's DPB. The
         FS info count equals a count of the FAT on the test card, before and after writes.
         `tools/api.py` says so.
       - Upstream bug fixed in `mount`: `cluster_count` was the partition's sectors minus the
         card-relative `lba_data`, 0 on the test card, so `find_free_cluster` never stopped at
         the end of the FAT and could hand out a cluster past the volume on a full drive. It is
         now the cluster past the last (1026 on the test card). A scratch run filled the drive:
         694 clusters exactly, then a short write with no error, mkdir 5, delete back to 694
         free; fatcheck clean.
       - The F4a trap is gone: the library's delete marks the long-name entries too.
       - Cost: bank 0 CODE -1430 bytes (6377 free below $FFA0); bank 1 B1CODE +505 (end $E679,
         6438 free); FATBSS +1 ($A100-$A7A3); KERNELRAM -25 ($0600-$06AA); KERNELZP -4 (ends
         $FB).
       - Tests: `DIRS` ok 1.2 s, `DOSAPI` 0.6, `SHFILES` 0.7, `CMDLETS` 1.5, `XCOPYS` 1.3,
         `SHRUN` 0.8, `CWD` 0.5, `DISK` 0.4, `WRITE` 0.9, `GREP` 1.8, `SHSCRIPT` 1.0, `SHTAB`
         0.5, `TREE` 1.3, `WHERE` 1.1, `XCOPY` 2.2, `FILES` 0.5, `HANDLES` 0.5, `SEEK` 0.5, `DUP`
         0.5, `EXEC` 0.8, `SHELL` 0.5, `BOOT` 0.4, `SHBOOT` 0.5, `SHREDIR` 1.5, `CLOCKCMD` 1.7;
         after the `cluster_count` fix again `DIRS` 1.3, `DOSAPI` 0.7, `WRITE` 0.9, `XCOPY` 1.5,
         `XCOPYS` 1.6, `SHFILES` 0.8, `SHRUN` 0.8, `DISK` 0.4, `CMDLETS` 1.7, `TREE` 1.4. No
         golden changed. A scratch shell run of long names (MD, COPY, REN across directories,
         DEL, RD): fatcheck clean.
       - Proposal for F7: the SFT state copy is 22 bytes, from `cluster` to `entry_ptr`; the
         library needs the context byte only, so `file_first`, `entry_sector` and `entry_ptr`
         (10 zero page bytes) and most of `SFT_STATE` can go.
       - Steps since the full suite: 2.
       - Docs owed, added: PLAN on rmdir of a read-only directory, the dots-only name, diskfree
         from FS info; NOTICE on the two upstream fixes.
     - Done, F5 (2026-10-20), committed 9730384. Build 731 ms, ROM only, the new baseline:
       - `api_chdir` and `api_getcwd` live in `fat32dos.s`, bank 1, on the library. fat.s lost
         them and the code only they used: the directory search, the cluster chain, `path_walk`,
         `dir_enter`, `drive_ready`, `lba_add`, and the zero page `search_attr` and `ptr`. It
         keeps the drive table, `mount`, `read_sector`, `path_last` (the kernel's device names),
         getdrive, setdrive and seek.
       - chdir: `lib_enter`, then `dir_change` on the name part unless it is empty; a wildcard
         gives 3. The library's current directory goes back to `DPB_CWD`, cluster 0 as
         `DPB_ROOT`.
       - getcwd: `fat32_open_tree` and `fat32_walk_tree` give each directory's entry in its
         parent, long names included. The path is built backward in `lib_path`; the length
         byte goes where the first `\` is, and the result is copied to r0 in the caller's bank.
         Over 254 characters gives 3. chdir does not check the length yet (F6).
       - `drive_enter` (bank switch, drive 0 the current one, then `drive_check`) is shared by
         getcwd and diskfree: 13 bytes saved.
       - Upstream change in `find_dirent`: `.` and `..` in the root name the root, as fat.s
         had it, so `CD ..` at the root and `\..\DOCS` work for every library call. The faked
         root entry fails a search for files only, so `OPEN ..` at the root gives 2.
         `fat32_walk_tree` now calls `find_dir`: it called `find_dirent` with A = the high byte
         of a ROM address, which reads as files only.
       - Cost: bank 0 CODE -734 bytes (7111 free below $FFA0); bank 1 B1CODE +260 (end $E77D,
         6178 free); KERNELZP -3 (ends $F8).
       - Tests: `CWD` ok 0.7 s, `DIRS` 1.0, `DOSAPI` 0.7, `SHELL` 0.5, `SHFILES` 0.7, `TREE`
         1.4, `XCOPY` 1.6, `CMDLETS` 1.5, `SHRUN` 0.8, `XCOPYS` 1.3, `WHERE` 1.1, `SHBOOT` 0.5;
         after `drive_enter` `CWD` 0.6, `DISK` 1.0, `DIRS` 1.1. No golden changed. A scratch
         test (deleted): `CD \..`, `CD \..\DOCS`, `CD ..\..\.`, `CD ./`, `CD D*` 3, `OPEN ..`
         and `OPEN \` 2, a long-name directory shown as created, 7 levels of 32-character
         names to 252 characters, the 8th gives getcwd 3; fatcheck clean.
       - For F7: `mount` still fills `DPB_FAT`, `DPB_BASE`, `DPB_FATS` and `DPB_FAT_SIZE`,
         which nothing reads now.
       - Steps since the full suite: 3.
       - Docs owed, added: PLAN on `.` and `..` in the root and long names from getcwd; NOTICE
         on the `find_dirent` change.
     - F6 split (2026-10-20), the user's answers: a long name over 32 characters made on a PC
       reads as its 8.3 alias everywhere; the shell's pipe files go to the directory in a
       `TEMP$` variable, `PIPE_PATH` 128. F6a the limits in the ROM; F6b `fatcheck.py` LFN
       checks and new tests (a PC name over 32 in `tests/sd`, goldens in their own commit);
       F6c the shell's `TEMP$` pipe directory.
     - Done, F6a (2026-10-20), committed b005cc4. Build 965 ms, ROM only, the new baseline:
       - `name_check` refuses a name part over `NAME_MAX` (32) characters: 3 on create, mkdir
         and the new name of rename.
       - `cwd_build`, split out of `api_getcwd`, builds the path in `lib_path`; `api_chdir`
         calls it before it sets `DPB_CWD`, so a directory whose path is over 254 characters
         gives 3 and getcwd always fits. A chdir now walks the tree up to the root.
       - Upstream change in `read_dirent`: a long name over 32 characters reads as the entry's
         short name, so find, open, chdir, getcwd and delete use the alias; delete still marks
         the long-name entries (`lfn_count`).
       - `tools/mksd.py`: long names up to 255 characters, as a PC writes them.
       - Cost: bank 1 B1CODE +35 bytes (end $E7A0, 6143 free). Bank 0, RAM, zero page: none.
       - Tests: `CWD` ok 0.7 s, `DIRS` 1.2, `DOSAPI` 0.8, `SHFILES` 0.8. No golden changed. A
         scratch test (deleted), with a 39-character `.txt` in `tests/sd/DOCS`: `FILES DOCS`
         shows `THISNA~1.TXT`, `LIST` by the alias works, by the long name gives 2; a 32-character
         MD and COPY work, 33 gives 3 on MD, COPY and REN; 7 levels of 32 characters, the 8th
         CD gives 3; fatcheck clean.
       - For F6c: the shell's `CURDIR$` is cut at 128 characters.
       - Steps since the full suite: 4.
       - Docs owed, added: PLAN §5 (a name over 32 shows as its alias; chdir refuses a path over
         254); NOTICE on the `read_dirent` change.
     - Done, F6b (2026-10-20), committed ee6fa0f, goldens e7431de. Build 1534 ms, the ROM and
       3 programs, the new baseline:
       - `tools/fatcheck.py` checks each run of long-name entries: the orders count down from
         the entry with bit 6 to 1, each entry holds the run's checksum, type 0 and cluster 0,
         and the run ends at the 8.3 entry whose checksum it holds. A run cut by a deleted entry,
         another run or the end of the directory is an orphan. A scratch check on copies of the
         card with a bad checksum, a broken order, a deleted 8.3 entry and a cluster in a
         long-name entry: each reported.
       - `tools/mksd.py`: a long name of exactly 13·n characters takes n entries, with no 0 and
         no padding.
       - `tests/sd/MANY/SUB.DIR/INNER` holds `Notes from the PC with a long name.txt` (38,
         `NOTESF~1.TXT`), `Twenty-six characters.text` (26, two full entries) and the directory
         `A directory with a longer name too` (34, `ADIREC~1`) with `IN.TXT`.
       - `tests/LFN.IN`, new: FILES, LIST by the long name and by the alias, CD by the alias and
         `CURDIR$`, CD by the long name gives Path not found, REN of a long name to a long name,
         DEL by the alias. fatcheck after: no problems.
       - Shell `FILES`: a name and size over 22 characters get one space between them; the
         count went negative and printed about 250 spaces. CMDSHELL.COM +32 bytes.
       - `TREE.UXB` and `XCOPY.UXB` leave room for `\` and a 32-character name (33), not 13:
         TREE enters a directory whose path is up to 217 characters, XCOPY up to 222 less the
         root.
       - Tests: `LFN` ok 0.5 s (new), `TREE` 1.4, `XCOPYS` 1.5, `CMDLETS` 1.6, `DIRS` 1.1,
         `DOSAPI` 0.7, `CWD` 0.5, `FILES` 0.4, `SHFILES` 0.8, `XCOPY` 1.5, `WHERE` 1.6.
         Golden files changed: `LFN` (new), `TREE` and `XCOPYS` (the files in `INNER`),
         `CMDLETS` and `DIRS` (free space), `FILES` (the size of CMDSHELL.COM).
       - Steps since the full suite: 5.
       - Docs owed, added: PLAN on fatcheck's long-name checks; TREE and XCOPY path room.
     - Done, F6c (2026-10-20), committed bfb262e, goldens 787e021. Builds 3022 ms (HEAP.UXI
       changed, 17 programs compiled), then 1312 ms, the ROM and the shell, the new baseline:
       - `TEMP$` is a shell system variable, VARBANK system string 13, `HEAP.TEMP_STRING`
         ($A026). The shell's history ring moved from strings 13 to 20 to 14 to 21.
         `NAME_KIND`, `DESCRIPTOR_OF` (`PATH$` and `TEMP$` both have 5 characters: P picks
         `PATH$`) and `SETSYS`, which lists `TEMP$=` last, know it.
       - The first `|` of a line names both pipe files: `TEMP$`, a `\` unless it ends in `\`,
         `/` or `:`, then `PIPE1.$$$`. An empty `TEMP$` puts them in the root of the current
         drive, as MS-DOS 2.0 does; before, they were in `C:\`. A `TEMP$` over 118 characters
         gives Path not found. `PIPE_PATH` is `STRING * 128`, and `PIPE_DIGIT` holds the
         address of its digit.
       - Bytes: CMDSHELL.COM 21491 to 21759 (+268). The pipe-path block is 177 of it. Building
         the path in `PIPE_PATH`, with no `C:\` default, saved 47 bytes over a first form in
         `STRING_RESULT`.
       - Tests: `SHREDIR` ok 1.6 s (new lines: `TEMP$` with and without the `\`, a pipe of 3
         parts, the files gone after, a missing directory and a 129-character `TEMP$` give
         Path not found), `SHVARS` 0.6 (sets and prints `TEMP$`), `FILES` 0.5 (the size),
         `HEAD` 1.2, `MORE` 0.9, `SHELL` 0.5, `SHFILES` 0.8, `SHIF` 0.6, `SHRUN` 0.9, `TAIL`
         1.3, `GREP` 1.9. `GREP` failed once on its first run and passed 10 times after; the
         failing output was not kept. Golden files changed: `SHREDIR`, `SHVARS`, `FILES`.
       - `fatcheck.py` lists about 108 lost clusters on every test card: they are the free part
         of the program block that `tests.py` reserves with `mksd.make(reserve=256)`, which the
         FAT marks as used. Not a problem.
       - Steps since the full suite: 6.
       - Docs owed, added: PLAN section 8 on `TEMP$` (the system variables, `SETSYS`, the pipe
         files at line 773), HEAP.UXI's slot list in PLAN at line 213, HELP.TXT.
     - F7 split (2026-10-20): F7a deletes `fat.s`; F7b is the doc batch.
     - Done, F7a (2026-10-20), committed 253276d, goldens f32e071. Build 786 ms, ROM only, the new baseline:
       - `src/asm/fat.s` is gone. `kernel.s` holds the drive table (`drives_init`,
         `drives_add`), `api_getdrive`, `api_setdrive`, `api_seek` and `path_device`, which
         replaces `path_last` and `component`: the last part of the path after `\`, `/` or `:`,
         up to 8 characters before a dot, for the device names.
       - The library mounts the volume when a call first takes a context; fat.s's `mount`,
         `read_sector` and its sector buffer are gone. A drive with no file system gives its
         error at that point (no media or no FS: Not ready), not at `drive_check`.
       - DPB: `DPB_DRIVER` (2) and `DPB_CWD` (4, 0 for the root), `DPB_SIZE` 8. `cwd_set` maps
         the volume's root cluster to 0 with `fat32_root`. diskfree takes the sectors per
         cluster and the clusters from the library (`fat32_sectors_per_cluster`,
         `fat32_cluster_count`, exported from `fat32.s` with `fat32_root`).
       - SFT: `SFT_CONTEXT` 5, `SFT_POS` 6, `SFT_FILE_SIZE` 10, `SFT_STATE` 9. The zero page
         `file_context`, `file_pos`, `file_size` (kernel.s) take lib_open's result.
       - RAM: `$0400-$05FF` is free. api_rename's new path is `RENAME_PATH`, `$AB00-$ABFF` in RAM
         bank 0. The glue's `blk_request` sets `BLK_UNIT` to 0.
       - Cost: bank 0 CODE -583 bytes (end $D80C); bank 1 B1CODE -53 (end $E76B); KERNELZP -30
         (ends $DA); KERNELRAM -98 ($0600-$0648).
       - Tests: `BOOT` ok 0.5 s, `SHBOOT` 0.5, `DISK` 0.5 (golden: X after setdrive, $40 to
         $10, a leftover), `SEEK` 0.4, `CWD` 0.5, `DOSAPI` 0.7. Full suite (step 7), 38.6 s: 50
         ok, the slowest 1.8 s.
       - Steps since the full suite: 0.
       - Docs owed, added: PLAN's RAM table (`$0400-$05FF` free, `$0600` no sector buffer,
         bank 0 `$AB00`), PLAN line 377 (the kernel's sector buffer), section 6 (who fills
         the block request), the DPB and SFT fields if PLAN lists them.
     - Done, F7b (2026-10-20), the doc batch of F1 to F7a. Build 726 ms, the new baseline; the
       ROM is byte-identical:
       - PLAN §3: `$0300-$030B` and `$0400-$05FF` free, `$0600` kernel variables, RAM bank 0's
         FAT32 areas, ROM bank 1, `FARCALL` and `jsrfar`, the vector-pull trap, the SFT holds
         the context, system descriptors 13 `TEMP$` and 14 to 21 the history. §5: Windows
         wildcards, 32-character names, case kept, the 8.3 alias, a name over 32 as its alias,
         the `name_check` errors, chdir's 254, rmdir and rename's 5, one volume `C:`, `.` and
         `..` in the root. §6: the library in bank 1, the glue fills the block request, the
         mount on the first call, the sector buffer at `$A900`, diskfree from FS info. §8:
         `TEMP$`, `SETSYS`, the pipe files, `.CBIN` as a long name, DISKFREE, TREE's 217, the
         command history. §9: the FAT32 port. §10: `rom.cfg`, `mksd.py` long names,
         `fatcheck.py` and its lost-cluster trap. §13: two items settled.
       - NOTICE: the four FAT32 files. `mem.inc`: the `GATE_PAGE` comment, "color". Long
         comment lines rewrapped in `fat32.s` and `mksd.py`.
       - `HELP.TXT`: new topic `SETSYS` (Command line or Script), with `TEMP$`.
       - Tests: `CMDLETS` failed on the `HELP` list (`SETSYS` added), as expected; updated, ok
         1.5 s. Golden changed: `CMDLETS`.
       - Steps since the full suite: 1.
       - Docs still owed, from before the F steps: written in S3, below.
     - Done, SCOM (2026-10-20, the user): commandlets are `.SCOM`, scriptable COM files, not
       `.CBIN`. The 8.3 alias ends in `.SCO`. `src/cbin/` is `src/scom/`, `CBIN.UXI` is
       `SCOM.UXI`. Changed: the shell's and `WHERE`'s search order, `build.py` (`SCOM`,
       `SCOM_OUT`, `compile_scom`), `tests.py`, PLAN, `HELP.TXT` `WHERE`, UXCBASIC HANDOFF's
       folder table, `SHRUN.IN`. Entries above this one keep the old name.
       - Build 1913 ms, 8 programs recompiled, the new baseline.
       - Tests: `WHERE` ok 1.3 s, `TREE` 1.4, `SHRUN` 0.8, `CMDLETS` 1.6. Goldens changed:
         `WHERE`, `TREE`, `SHRUN`.
       - Steps since the full suite: 2.
   - Spaces in names (2026-10-20, the user). The shell splits arguments at spaces, so
     `TED MY FILE.TXT` edited `MY`. A quoted argument keeps its spaces. Three steps:
     - Done, S1: `TED` prints Too many parameters and gives exit code 1 for a second
       argument, as `MORE` does. `TED.IN` adds `TED MY FILE.TXT` and a save to
       `"MY NOTES.TXT"`, read back with `TYPE`.
       - `TED.COM` 10748 to 10819 bytes, +71; no ROM change.
       - Build 1013 ms, the new baseline. `TED` ok 1.2 s; golden changed.
       - Steps since the full suite: 3.
     - Done, S2: Tab takes the word after the last space outside quotes, and skips a quote
       at its start. A match with a space goes in quotes; a directory's closing quote is
       left off, so a name can follow it: `CD Z` Tab gives `CD "Z DIR\`. `SHTAB.IN` adds
       `"Q R.TXT"` and `"Z DIR"`.
       - `CMDSHELL.COM` 21759 to 21966 bytes, +207, over the estimate. Each string
         assignment costs about 40 bytes. Skipping the quote with `CURSOR` and
         `CURRENT_CHAR`, in place of `MID$`, saved 98. A closing quote on a word the user
         typed is not stripped; that would cost 48 more.
       - Build 1234 ms, the new baseline. `SHTAB` ok 0.6 s, `FILES` ok 0.4 s; both
         goldens changed (`FILES` the shell size only).
       - Steps since the full suite: 4.
     - Done, S3 (2026-10-20), with the doc batch owed from before the F steps. No docs are
       owed.
       - `HELP.TXT`: new topic `PROMPT` after `COLORS` (Tab, Shift+Tab, Up and Down, quotes,
         the tail drops them); new topic `XCOPY` (Command line only) after `GREP`.
       - PLAN §4: the `con_line` row (Tab does nothing) and a `con_edit` row. §8: Arguments
         (a quoted argument keeps its spaces), `XCOPY` after `GREP`, Tab completion before
         Command history. §11 step 7i: `XCOPY` follows `GREP`.
       - Build 743 ms, the new baseline. `CMDLETS` failed on the `HELP` list (`PROMPT`,
         `XCOPY` added), as expected; updated, ok 1.8 s. Golden changed: `CMDLETS`.
       - Steps since the full suite: 5.
       - Gap found, by reading the code, not tested: `FIND_MATCH` looks for `*.COM` and
         `*.CMD` on `PATH$`, not `*.SCOM`, so a commandlet's name does not complete.
     - Done, S4 (2026-10-20, the user): Tab completes `.SCOM` programs on `PATH$`.
       `FIND_MATCH` looks for `*.SCOM`, then `*.COM`, then `*.CMD` in each `PATH$` directory,
       the order the shell runs them. `HELP.TXT` `PROMPT` and PLAN §8 Tab completion say so.
       - `CMDSHELL.COM` 21966 to 22056 bytes (+90).
       - Build 1212 ms (the shell recompiled), the new baseline.
       - `SHTAB.IN`: `WHE`, Tab, ` HEAD` gives `WHERE HEAD` and `C:\DOS\HEAD.COM`. `SHTAB`
         failed on the new line, as expected; updated, diffed, ok 0.7 s. `CMDLETS` ok 1.6 s.
         Golden changed: `SHTAB`.
       - Steps since the full suite: 6. The next step runs the full suite.
     - Full suite after M0 (step 7), 39.5 s: 50 tests, 49 ok, the slowest 1.6 s. `FILES`
       failed on the size of CMDSHELL.COM (22056, from S4); updated, ok 0.4 s, golden
       1ce2fb5. Steps since the full suite: 0.
   - MSBASIC in ROM (planned 2026-10-20), after F7b. Steps M0 to M5; each asm step asks first.
     - Facts:
       - The `sim` build is 12068 bytes. It goes in ROM bank 2, `$C000-$FFFF`; the ROM image
         grows from 32 KB to 48 KB.
       - The `sim` zero page is `$00-$12`, `$5B-$DF` and `$F0-$F9`: 162 bytes. `CHRGET` is at `$C3`. `TXTPTR` sits inside `CHRGET` and 19 places read
         `(TXTPTR),y`, so it must stay in zero page.
       - A program owns `$22-$7F`, 94 bytes. The kernel owns `$80-$FF`; `$DB-$FF` is unused.
       - `exec` saves a parent's `r0` to `$7F` and its pages from `$0700` to `PSP_TOP`.
         It does not save `$0200-$05FF`. BASIC's RAM data goes at `$0801`, before the
         program text, so it survives a child.
       - The console obeys `Esc[r;cH`, `Esc[2J`, `Esc[K` and `Esc[..m` (0, 7, 30-37, 40-47),
         so `CLS` and `LOCATE` work as in the sim. It has no `Esc 7`, `Esc 8` or
         `Esc[38;5;n`, so `TEXTAT` and `COLOR` use `con_cursor` and `con_colour`.
     - Done, M0 (2026-10-20), the zero page audit, no code: `MSBASIC/docs/6502dos-zeropage.md`.
       - 89 bytes need zero page: `(zp),y`, `sty zp,x`, `sta 0,x` on `TEMPST`, `SHIFT_RIGHT`'s
         `sty n,x` on `RESULT`, `FAC` and `ARG`, and `CHRGET` with `TXTPTR`. 71 bytes do not.
       - The proposed layout fills `$22-$7F`: the 89, then `CURLIN`, `VALTYP` and `EOLPNTR`.
         66 bytes move to the RAM data at `$0801`: about 328 instructions take the absolute
         form, about +328 bytes of ROM and 1 cycle each.
       - Traps found: `REASON` relies on zero page wrap in the `TEMP1` block; `INPUTBUFFER` at
         `$0200` is the monitor's line, and `exec` does not save it.
       - The user took the proposed layout (2026-10-20).
     - Decided by the user (2026-10-20):
       - The start is a stub, `MSBASIC.COM`.
       - `EXIT` ends BASIC and returns to the shell. `END` ends the program and returns to
         BASIC's prompt, as now.
       - `INPUTBUFFER` is on page `$08`, after the stub and the 66 bytes of RAM data, 81 bytes,
         with the 5 bytes `INPUTBUFFER-5` to `-1` in front. The program text starts at `$0901`.
       - The `6502dos` target may use 65C02 opcodes. The `sim` target and `make verify` stay
         NMOS.
     - Why page `$08` for `INPUTBUFFER`:
       - `$0200` fails: it is `CON_LINE` and the monitor's line, `exec` does not save it, and
         `INPUTBUFFER-5` to `-1` land in `$01FB-$01FF`.
       - The buffer must not cross a page (`INPUTBUFFERX,x`). No program text or string may share
         its page: `flow1.s` and `string.s` test `#>INPUTBUFFER` for direct mode.
       - The `CONFIG_INPUTBUFFER_0200` code in `program.s` stays: it copies `LINNUM` in front
         of the buffer, as any buffer outside zero page needs.
     - Trap for M1: the cold start does `ldx #$FB` and `txs`, and `ldx #STACK_TOP`, `txs` on each
       error. That throws away the stack of the shell that ran BASIC, and `STACK+STACK_TOP+1`
       writes over it. The `6502dos` target must take its stack top from the `S` it starts with.
     - M1, a `6502dos` target in `MSBASIC/` (`defines_6502dos.s`, `6502dos.cfg`):
       - the M0 layout;
       - `K_OPEN`, `K_CLOSE`, `K_READ`, `K_WRITE` on the API through the gate entries at
         `$0340`, with `OPEN` modes as in 6d;
       - `ISCNTC` on `con_break` in `BREAK_CATCH`, `K_JIFFY` on the clock, `POS(1)` on
         `con_cursor`, and the VERA primitives on the hardware;
       - bank 2's IRQ entry at `$FFA0` and its vectors at `$FFFA`, as in `bank1.s`.

       `make verify` and `make test` must still pass. The target is not in the ROM yet.
     - M2, bank 2 in the ROM:
       - `build.py` builds the `6502dos` target and links it as bank 2.
       - `MSBASIC.COM`, a stub of a few bytes, clears the screen, selects ROM bank 2 and jumps
         to the cold start.
       - `QUIT [n]` ends BASIC and returns to the shell with exit code n.
       - `MSBASIC NAME.BAS` loads NAME.BAS and runs it.
       - Tests `BASBOOT` and `BASRUN`.
     - M3, files: `OPEN`, `CLOSE`, `PRINT#`, `INPUT#`, `GET#` on the SD card. `LOAD` and
       `SAVE` of program text. One test.
     - M4, `tests.py` runs MSBASIC's `tests/*.bas` on the ROM against their `.out`.
     - M5, docs: PLAN sections 2, 3 and 11, `HELP.TXT`, `MSBASIC/CLAUDE.md` and
       `MSBASIC/docs/changes.md`.
   - Rename (2026-10-20, the user): `UXDOS16` is `6502DOS` in every tracked file but `attic/`,
     and in the memory notes. The ROM is `build/6502DOS.ROM`, with `.MAP` and `.LBL`; pyuxc's
     target is `"6502dos"`; `UXCBASIC/tests.py`'s `UXDOS16_REPO` is `DOS_REPO`. The name
     `tpl/UXDOS` stays; the MSBASIC target is `6502dos` since M1. Same length, so no size changed.
     - Build 4.26 s, every program recompiled (the `lib` files changed): the full-build
       baseline. Tests: `BOOT` ok 0.5 s, `SHBOOT` 0.5, `DISK` 0.5, `CMDLETS` 1.6, `TARGET`
       0.4, UXCBASIC `ARRAY1` 0.5. 50 goldens changed in the banner only.
     - Steps since the full suite: 1.
   - Decisions recorded (2026-10-20), docs only, no test: `INPUTBUFFER` on page `$08`, 65C02
     for the `6502dos` target. Doc edits go in one commit per batch. Steps since the full
     suite: 2.
   - Done, M1 (2026-10-20), code and docs in one commit. The user renamed
     the target: `uxdos` is now `6502dos` (files) and `DOS6502` (the ca65 symbol; a symbol
     cannot start with a digit; the Makefile maps it with `DEFINE_6502dos`).
     - New files in `MSBASIC/src/`: `defines_6502dos.s`, `6502dos_zp.s`, `6502dos_extra.s`,
       `6502dos_iscntc.s`, `6502dos.cfg`. The Makefile builds `6502dos` in `make all`, with
       `-I ../src/asm -I ../build/gen` (mem.inc, far.inc, api.inc).
     - Shared changes, each behind `DOS6502` or the new `CONFIG_HOSTED` (sim and 6502dos):
       `.ifdef SIM` became `CONFIG_HOSTED` where both targets share it; `SIM_UPPER` moved to
       `extra.s` as `UPPER`; `macros.s` has `bne_far`, `beq_far`, `bcs_far` (long branches in
       6502dos only, 7 sites); `defines.s` takes `STACK` from mem.inc.
     - Layout: zero page as M0 at `$22-$7F`; RAM data 66 bytes at `$0810`; `INPUTBUFFER` at
       `$0860`; `IORAM` (handle_io, the GOTO and variable caches, the DOS variables, 645
       bytes) at `$9C00`, and `MEMSIZ` is `$9C00`, no RAM scan. `$C000` holds `jmp COLD_START`
       for the stub.
     - Cold start sets `BREAK_CATCH` and keeps `S` in `DOS_STACK`; `STKINI` goes back to it.
       `ISCNTC` polls `con_status` and `con_break` once in 256 calls (I2C is slow); `K_JIFFY`
       waits for a tick on `API_TICKS` and forces the next poll. Console lines come through
       `con_line` into `INPUTBUFFER-2`, with no CRDO after; a Ctrl+C in the line breaks a
       running program. `K_READ`/`K_WRITE` are one-byte `read`/`write`; `K_READ` drops LF.
       `K_OPEN` as 6d: read `open` 0, write `create`, append `open` 1, create on error 2, seek
       to the end. `POS(1)` is `con_cursor`'s row. `TEXTAT` keeps the cursor and the color with
       `con_cursor`/`con_colour`; `COLOR fg[,bg]` is `con_colour` (0-15). `CLS` and `LOCATE`
       stay ANSI. `SCREEN` does nothing. VPEEK/VPOKE drive VERA's address 0.
     - Size: bank 2 holds 11821 bytes, +410 over the sim's 11411 bytes of code; 4563 bytes free.
       The IRQ entry at `$FFA0` matches banks 0 and 1 but the `jmp irq` operand (0; never run).
     - Tests: `cbmbasic1`, `cbmbasic2` and `sim` binaries are byte for byte as before;
       `make verify` matches; `make test` 31/31 ok, 1.7 s. The 6502dos image is not run yet:
       that needs M2. MSBASIC build 980 ms (`make all` after the docs).
     - Docs: `MSBASIC/docs/6502dos-zeropage.md` (was `uxdos-zeropage.md`) has the real RAM map
       and cost; `MSBASIC/docs/changes.md` has a `6502dos target` section; `MSBASIC/CLAUDE.md`
       lists the target and its files.
     - The 6502DOS API name `con_colour` (`API_CON_COLOUR`) breaks the "color" spelling rule.
       Renaming it is a separate step.
     - A 65C02 savings pass over the 6502dos code is a later separate step.
   - Done, M2 (2026-10-20), code and docs in one commit, the goldens in the next. The user
     replaced `EXIT` (to the shell) with `QUIT [n]`, n the exit code, 0 by default; `EXIT [DO]`
     stays. The user added the screen clear and `MSBASIC NAME.BAS`.
     - `tools/build.py`: `build_basic()` builds the 6502dos target with the repo's ca65/ld65
       (`-D DOS6502 -I MSBASIC/src -I src/asm -I build/gen`), to `build/MSBASIC.BIN` and
       `build/MSBASIC.LBL`, appends it to `6502DOS.ROM` as bank 2 (ROM 49152 bytes; TEST.ROM
       too), and assembles `MSBASIC/src/6502dos_com.s` to `build/bas/MSBASIC.COM`, 14 bytes
       (`$0801`, `lda #FF / jsr API_CON_OUT / lda #2 / sta ROM_BANK / jmp ROM`; 12 of the 15
       code bytes), on the card root.
     - `tools/cc65/asminc/longbranch.mac`, new, copied from `C:\8bitProgramming\cc65\asminc`:
       the repo's ca65 found no `.macpack longbranch` without it.
     - `QUIT`: `CONFIG_QUIT` in `defines_6502dos.s`, the keyword in `token.s` after `COLOR`,
       the code in `6502dos_extra.s`. 18 bytes with the keyword.
     - `MSBASIC NAME.BAS`, 118 bytes: `DOS_BOOT` in `6502dos_extra.s` ends the cold start
       (`init.s` jumps to it). It opens the first word of the command tail as logical file 0,
       entry 0, and makes it the input, with no OK first. `INLIN` reads a line of logical file 0
       with `CURDVC` not 0, so no CRDO follows it; at the end of the file it closes it, calls
       `IO_CLRCH` and returns the line `RUN`. `IO_CLALL`, the clear after each line entered,
       keeps the input while `HIO_IN` is a file (`IO_CLROUT`, new). A missing file: ?FILE NOT
       FOUND ERROR, then OK. The file needs CR LF line ends (`K_READ` drops LF);
       `.gitattributes` gives `tests/sd/*.BAS` CR LF.
     - Bug fixed, `program.s` end of `PARSE_INPUT_LINE`: `dec TXTPTR+1` is assembled only when
       `>(INPUTBUFFER-1) <> >INPUTBUFFER`. With INPUTBUFFER at `$0860` it made TXTPTR `$075F`,
       so every direct statement gave ?SYNTAX ERROR. 6502dos 2 bytes less; others unchanged.
     - Bank 2: 11955 bytes used, 4429 free (was 11821 / 4563).
     - Tests, in `SHELL_ROM_TESTS`: `BASBOOT` (`MSBASIC`, `PRINT 1+1`, `QUIT 300` (?ILLEGAL
       QUANTITY), `QUIT 7`, `VER`, `MSBASIC`, `QUIT`, `VER`) and `BASRUN` (`MSBASIC HELLO.BAS`
       with `tests/sd/HELLO.BAS`, 3 lines; `LIST`, `QUIT 3`, `MSBASIC NOSUCH.BAS`, `QUIT`,
       `VER`). The goldens show the FF before each banner. `BASRUN` ok 0.5 s, `BASBOOT` 0.6,
       `SHBOOT` 0.5. MSBASIC `make all verify` ok, `make test` 31/31, 1.1 s. ROM build 983 ms,
       the new baseline.
     - MSBASIC's `Makefile` calls the ca65 and ld65 of `C:\8bitProgramming\cc65\bin`, not
       `tools/cc65/bin`.
     - Steps since the full suite: 5.
     - Next: M3, files. `LOAD` and `SAVE` can open their file as `DOS_BOOT` does.
   - BASIC help (2026-10-20), the user's request, in steps: (1) `HELPBAS.COM` and
     `HELPBAS.HLP`; (2) `HELP [topic]` in MSBASIC, direct mode only, reading the same file.
     - Step 1 done. `src/dos/HELPBAS.UXB`, `HELP.UXB` with the path `C:\DOS\HELPBAS.HLP`; the
       topic list starts a new line before a name that would pass column 79. 1769 bytes.
     - `src/dos/HELPBAS.HLP`: 91 topics, one for each keyword of the 6502dos target, plus
       `LABELS` and `ST`, in A to Z order; 8791 bytes. No topics for `LOAD` and `SAVE` (stubs)
       or `USR`. Lines of 80 characters at most. CR LF line ends (`.gitattributes`), because
       MSBASIC's `K_READ` drops LF; UXC `LINPUT` takes CR LF.
     - Facts checked in the source: PRINT's comma zones are 14 columns (no `CONFIG_CBM_ALL`);
       `GET`, `GET#`, `INPUT` and `DEF` give ?ILLEGAL DIRECT; `CLEAR` closes the files; `FRE`
       over 32767 is negative.
     - Test `HELPBAS`, in `SHELL_ROM_TESTS`: `PATH$ = "C:\DOS"`, `HELPBAS`, `HELPBAS print`,
       `HELPBAS str$`, `HELPBAS NOSUCH`, `VER`. The boot shell has no `PATH$`. ok 1.5 s.
     - Goldens changed: `CMDLETS` and `DIRS` (free space), `TREE` (also `HELLO.BAS` and
       `MSBASIC.COM` of M2, which had not updated it). `CMDLETS` ok 1.6 s, `DIRS` 1.1, `TREE`
       1.4, `BASBOOT` 0.5, `BASRUN` 0.5. Build 1340 ms, the new baseline.
     - Docs owed to the batch: a `HELP.TXT` topic `HELPBAS`, PLAN's utilities list.
     - Steps since the full suite: 6.
     - Step 2 done (2026-10-20). The user chose ?SYNTAX ERROR in a program and approved the asm.
       `HELP [topic]`, `CONFIG_HELP`, in `6502dos_extra.s`; the keyword follows `QUIT` in `token.s`.
       311 bytes: 6 for the keyword, 273 of code, 32 of text. Bank 2: 12266 bytes used, 4118 free
       (was 11955 / 4429). No new RAM: the topic and a `:NAME` line go in `HIO_NAME` after the
       path; the handle and the found flag use `DOS_ROW` and `DOS_COLUMN` (TEXTAT's).
     - A token in the topic is spelled out with `KW_INIT`/`KW_NEXT`; `(` is dropped, so
       `HELP TAB(` finds `TAB`. A missing topic prints `NO HELP FOR NAME`; a missing file gives
       ?FILE NOT FOUND ERROR. The list matches `HELPBAS`'s.
     - Speed: `K_READ` is one API call a byte. A topic near the end of the file, or a missing
       one, takes 1.2 s at real speed; `HELP ABS` 0.02 s. A buffered `K_READ` would speed this
       and every file read of BASIC: a later step, if the user wants it.
     - `HELPBAS.HLP`: topic `HELP`, 92 topics, 8997 bytes.
     - Test `BASHELP`, in `SHELL_ROM_TESTS`: `MSBASIC`, `HELP`, `help print`, `HELP str$`,
       `HELP tab(`, `HELP nosuch`, `10 HELP` and `RUN` (?SYNTAX ERROR IN 10), `QUIT`. ok 1.6 s.
       Its golden needed a 10 s update window (`--update` stops at 2 s); the scratch script
       ran `tests.py` with `UPDATE_SECONDS` raised. `tests.py` calls `main()` at import.
     - Goldens changed: `HELPBAS` (the list has `HELP`), `DISK` (from the files added to
       `\DOS`).
     - Tests: `BASHELP` ok 1.6 s, `HELPBAS` 1.6, `DISK` 0.4, `CMDLETS` 1.7, `DIRS` 1.2, `TREE`
       1.5, `BASBOOT` 0.6, `BASRUN` 0.5. MSBASIC `make all verify` ok (1353 ms), `make test`
       31/31 (1336 ms). ROM build 1083 ms, the new baseline.
     - Full suite: 54 tests, 52.1 s. 3 failed from M2's `HELLO.BAS` and `MSBASIC.COM` on the
       card root, which M2 had not run: `DOSAPI` and `FILES` list them; `SHTAB` now completes
       `LIST HEL` to `HELLO.BAS`. Goldens updated, then ok: `DOSAPI` 0.7 s, `FILES` 0.4, `SHTAB`
       0.7.
     - Step 3 done (2026-10-20): `LOAD "name"` and `SAVE "name"` of program text, in
       `6502dos_extra.s`; the details are in `MSBASIC/docs/changes.md`. +114 bytes, 1 byte of
       RAM (`DOS_LOADRUN`). Bank 2: 12380 bytes used, 4004 free. `sim` +4 bytes, from
       `HIO_GETNAME`, which `OPEN`, `LOAD` and `SAVE` share.
     - LOAD does a NEW, then reads the file as `MSBASIC NAME.BAS` does (both through `DOS_LOAD`),
       then OK; in a program it runs the loaded program. A missing file keeps the program.
     - SAVE drives LIST from the new label `LIST_LINE` (no blank first line) and points
       `GOSTROUT` at `SAVE_END`, which closes the file at RESTART's OK. It ends a program.
     - `HELPBAS.HLP`: topics `LOAD` and `SAVE`, 94 topics, 9287 bytes.
     - Test `BASLOAD`, new, in `SHELL_ROM_TESTS`: SAVE, NEW, LOAD, LIST, RUN, a missing file, a
       LOAD in a program (chains to `HELLO.BAS`), `HELP SAVE`, then `TYPE T.BAS` in the shell.
     - Tests: `BASLOAD` ok 0.7 s, `BASBOOT` 0.5, `BASRUN` 0.5, `BASHELP` 1.6, `HELPBAS` 1.4,
       `CMDLETS` 1.5, `DIRS` 1.1, `TREE` 1.5, `DISK` 0.4, `FILES` 0.5. Goldens changed:
       `BASHELP` and `HELPBAS` (the list has LOAD and SAVE). MSBASIC `make all verify` ok
       (1127 ms), `make test` 31/31 (1019 ms). ROM build 966 ms, the new baseline.
     - Step 4 done (2026-10-20), the user's three picks, details in `MSBASIC/docs/changes.md`:
       - `K_READ` reads a file 64 bytes a call into `DOS_BUF`; a read of another handle seeks
         the holder back by its unread bytes. +90 bytes, RAM +67 (`IORAM` 713 of 768).
         `K_OPEN` empties the buffer when it hands out the holder's handle again (+11);
         `DOS_BOOT` empties it at the cold start (+6).
       - `LIST_NUMBER`: a file gets no space before LIST's line number, so SAVE writes
         `10 PRINT`. +23.
       - `HELP_FOUND` starts as the topic length; the two topic CR checks are gone. -7.
       - Bug fixed: `ISCNTC`'s poll changed Y, and LIST then listed a wrong line
         (`8369 3:PRINT`), at random, one poll in 256. `phy`/`ply`, +2.
       - +125 bytes. Bank 2: 12505 used, 3879 free. `sim`, `cbmbasic1`, `cbmbasic2` unchanged.
       - `BASLOAD` gained a program that reads `T.BAS` and `HELLO.BAS` a byte each in turn with
         `GET#`, which drives the seek-back. Its golden: that part, and `TYPE T.BAS` with no
         leading spaces.
       - Tests: `BASLOAD` ok 0.6 s, `BASHELP` 0.7 (was 1.6), `BASRUN` 0.5, `BASBOOT` 0.5,
         `HELPBAS` 2.0. MSBASIC `make all verify` ok (1108 ms), `make test` 31/31 (1001 ms).
         ROM build 949 ms, the new baseline.
     - Step 5 done (2026-10-20), step A of the user's FILES/KILL/NAME request:
       - `KILL "name"` (17 bytes) and `NAME "old" AS "new"` (62 bytes; GW-BASIC's syntax, the
         user's pick). NAME's new name taken: ?FILE EXISTS ERROR (new message, 6 bytes); other
         failures ?FILE NOT FOUND. NAME keeps the old name in `DOS_BUF` after `DOS_GIVEBACK`,
         the seek-back of `K_READ` made a routine (+7). Keywords 12. +104 bytes in all. Bank 2:
         12609 used, 3775 free. RAM unchanged (`IORAM` 713 of 768).
       - SAVE over an existing file: the user wants it to overwrite and saw an error once. Not
         reproduced: SAVE replaced the same file twice, longer then shorter (over 1 KB),
         `HELLO.TXT`, a long name, lowercase, a name with a space, `DOCS\README.TXT`, no
         extension. SAVE is unchanged. Any `create` failure there shows as ?FILE NOT FOUND.
         Ask the user for the exact message and steps.
       - `HELPBAS.HLP`: topics KILL and NAME; SAVE says no space before a line number and that
         a file of that name is replaced. `BASLOAD` tests SAVE over T.BAS, NAME, NAME onto
         HELLO.BAS (EXISTS), NAME of a missing file, KILL twice.
       - Trap: `tools/build.py` cannot write `build/SD.IMG` while the user's emulator runs
         (PermissionError at mksd); the ROM and `build/DOS` are written before it. Tests use
         their own card.
       - Trap: `tests.py --update` cut `HELPBAS.OUT` at 2 s; its golden was spliced by hand.
       - Tests: `BASLOAD` ok 0.8 s, `BASHELP` 1.2, `HELPBAS` 2.4, `BASRUN` 0.8, `BASBOOT` 0.9.
         `make all verify` ok (1459 ms). ROM build 1205 ms, the new baseline.
     - Step 6 done (2026-10-20), step B: `FILES ["pattern"]`, details in
       `MSBASIC/docs/changes.md`. The shell's format, hidden, system and directories listed, a
       directory's name lists its names, no pattern the current directory, `ISCNTC` each name.
       The find buffer is `DOS_BUF` plus 19 bytes; `FILES_COUNT` 4. +275 bytes (estimate was
       185), RAM +23 (`IORAM` 736 of 768). Bank 2: 12884 used, 3500 free. `sim`, `cbmbasic1`,
       `cbmbasic2` unchanged.
       - `HELPBAS.HLP`: topic FILES. `BASLOAD` tests `FILES "*.BAS"`, `FILES "DOCS"`,
         `FILES "NOSUCH.*"`, `HELP FILES`. Checked by hand once: plain `FILES` (the card root,
         29 files), `FILES "docs\"`, FILES in a program followed by PRINT.
       - Tests: `BASLOAD` ok 0.8 s, `BASHELP` 0.7, `HELPBAS` 1.6 (golden list spliced from
         BASHELP's), `BASRUN` 0.6, `BASBOOT` 0.5. `make all verify` ok (1035 ms). ROM build
         979 ms, the new baseline; `build/SD.IMG` was written.
     - Step 7 done (2026-10-20): the GW-BASIC full-screen editor (the user's request: "what
       GW-BASIC does"). The user asked what `EDIT n` is; it is not built, and no answer came.
       - ROM call 50 `con_screen` (`console.s`): the arrows, Ctrl+Left and Ctrl+Right a word,
         Home, End, Ctrl+Home, Ctrl+End, Esc, Ins (a cursor move ends insert mode), Del,
         Backspace, Tab. Enter returns the cursor's row, trimmed, from the start column on the
         start row. A line is one row (`LINE_MAX` 80). A Ctrl+C caught in mode 2 ends the line
         empty: `con_in` returns 0 then, while `con_end_key` is $FF. `con_file` is the handle-0
         test, shared with `con_read`. VERA port 1 (`VERA_DATA1`, new in `mem.inc`) shifts a
         row for Del and insert.
       - The paste queue: `KBD_EXTENDED` $E0 then a scan code is an extended key; `\XE0\X48` in
         a `.IN` is Up. Trap: x16emu -bas ends the paste at `\X00`. `kbd_pop` is the queue's
         shift as a routine.
       - MSBASIC `inline.s` calls `con_screen` in place of `con_line`: 0 bytes.
       - Bank 0 +618 bytes (CODE +573, RODATA +45; estimate was 450), 7076 free below $FFA0.
         KERNELRAM +3 (`scr_row`, `scr_col`, `scr_insert`).
       - Not done: the insert-mode cursor shape, lines longer than a row. `EDIT n` and the
         F-key soft keys were started, then cancelled by the user and moved to
         `MSBASIC/TODO.md` section 6 with their design.
       - New test `BASEDIT` (in `SHELL_ROM_TESTS`): insert, Del, Backspace, Esc, Ctrl+Left,
         Ctrl+C, Up onto a listed line to fix it, INPUT past its prompt. ok 0.5 s.
       - Tests: `BASBOOT` ok 0.7 s, `BASRUN` 0.5, `BASLOAD` 0.9, `BASHELP` 0.8, `HELPBAS` 1.5,
         `SHTAB` 0.6, `SHELL` 0.5, `SHVARS` 0.6. `make verify` ok (792 ms). ROM build 932 ms
         after a 3767 ms build that recompiled everything for the new `DOS.UXI`.
     - `.IN` files untracked (bda8b39); `.gitignore` drops `tests/*.IN`, `UXCBASIC/tests/*.IN`.
     - Done, M4 (2026-10-20, 72b6511): `tools/tests.py --msbasic [name ...]` types each
       `MSBASIC/tests/name.bas` into MSBASIC at the shell, then `QUIT`, and compares the
       transcript after the banner with `name.out` (the sim's), or `name.rom.out` where the
       target differs by design. `--msbasic --update` writes `name.rom.out`; both are local.
       - Test changes: `labels.bas` names its label `FINISH`, not `QUIT` (a 6502dos keyword: the
         line `400 QUIT:` left BASIC). `vera.bas` pokes VRAM 0 with 66 before it reads it; the
         ROM read random values there. Sim goldens regenerated, only the echoed lines changed.
       - `name.rom.out` written for `hexbin` (FRE(0) -28008), `vera` (real VRAM), `textat` (no
         Esc 7/8 or color codes; `con_cursor`/`con_colour`).
       - 31 tests, run one at a time: 28 ok, 0.5 to 1.0 s each (`pause` 1.0). 3 fail, waiting
         on the user:
         - `files`: the 8th OPEN gives ?FILE NOT FOUND, the sim ?FILE LIMIT at the 11th. The
           kernel's handles run out first. Fix proposed: in `handle_io.s`'s open, under
           `DOS6502`, `cmp #ERR_TOO_MANY_FILES` / `beq @toomany`, 4 bytes. Then a `rom.out`.
         - `linein`: lines of 80 and more are cut at 79 (`con_screen` is one row; known).
         - `screen`: `con_screen` returns the whole row, so text left on the row right of a
           typed line joins it: `COLOR 2:COLOR 255,4:PRINT "C"` typed on a row with old output
           gave ?SYNTAX ERROR. Shown also with `PRINT 1` on a row holding `JUNK` at column 40:
           ` 1  0`. GW-BASIC's editor does the same. Option: clear the rest of the start row
           when `con_screen` starts. Plus the color codes, which need a `rom.out`.
       - `tests.py`'s docstring: `\XE0` escaped, which ended a SyntaxWarning at each run.
       - ROM build 1933 ms (recompiled after the revert of `console.s`). `BASBOOT` 0.5 s and
         `BOOT` 0.4 s still ok with the normal mode. MSBASIC `make all` 819 ms; sim `labels` and
         `vera` ok.
     - Done, the 65C02 savings pass over `6502dos_extra.s` (2026-10-20), the user's request:
       -31 bytes, `IORAM` -1 (`DOS_TICK`). Details in `MSBASIC/docs/changes.md`. Bank 2: 12853
       used, 3531 free. `IORAM` 735 of 768.
       - `TA_INK` merges by `eor`/`and #$0F`/`eor` (-5, -6 cycles) and shares `DOS_SETCOLOR`
         with `TA_RESTORE` (-2); `COLOR` ends in `TA_INK` (-13); `DOS_R0NAME` for `K_OPEN`,
         `KILL`, `FILES_FIRST` (-9); `K_JIFFY` keeps the tick on the stack (-2).
       - Checked by hand with `VPEEK(1,1)` after `CLS`: `COLOR 3,5` gives $53, `TEXTAT ..,2`
         then $52, `COLOR 12` and a `TEXTAT` with no color $5C.
       - Not done, a proposal: the shared sources assemble as 65C02 for `6502dos`, but use no
         65C02 opcode outside `.ifdef DOS6502`. `stz` and the like there need an `.ifdef` or
         a macro at each site.
       - Tests: `--msbasic` `textat` ok 0.7 s, `pause` 1.2, `hexbin` 0.7, `vera` 0.6; `screen`
         and `files` fail as before. `BASLOAD` 0.9, `BASBOOT` 0.5, `BASHELP` 1.5, `BASRUN` 0.7.
         MSBASIC `make all verify` ok (1236 ms), `make test` 31/31 (1246 ms). ROM build 1007 ms,
         the new baseline.
     - Full suite after the 65C02 pass: 56 tests, 0 failed, 48.2 s; the longest `SHREDIR`
       2.0 s. Steps since the full suite: 0.
     - Done, the card keeps the X16's files (2026-10-20), the user's request: a BASIC program
       saved on `build/SD.IMG` was lost at the next build. HostFS (`-fsroot`) is out: x16emu
       traps the stock KERNAL's entry points, and 6502DOS reads the card by SPI.
       - `mksd.read(image)` returns each file and folder of a FAT32 image: the path, the bytes,
         the time.
       - `build.py` `make_card`: gathers `sd`, the build outputs, `tests/sd` and `card` in
         `build/card`, `card` winning a shared name, then writes `SD.IMG` and `build/SD.SUM`
         (each path and its SHA-1). Before that, `pull_card` copies into `card` what the X16
         added or changed since `SD.SUM`, and deletes from `card` what it deleted. Without
         `SD.SUM`, only paths not in `build/card` are copied. It prints `card: kept`/`deleted`.
         `SD.IMG` open in x16emu: exit 1, "close x16emu".
       - `card/` is gitignored. A build file deleted on the X16 comes back at the next build.
       - Checked with a fake X16 save (an image rewritten by `mksd.make`): a new file, a
         long-named folder and a changed `README.TXT` reached `card/` and the next image; a
         second build kept nothing; deleting them on the card emptied `card/`.
       - ROM build 1314 ms, the new baseline (+0.3 s: the copy to `build/card` and the read
         back). `BOOT` ok 0.5 s. Steps since the full suite: 1.
       - Docs owed: PLAN's card paragraph (line 1112) names `build.py` writing `SD.IMG` from
         `sd` only.
     - Done, test files in `C:\TEST` (2026-10-20), the user's request, to keep the root for
       their own folders (`PROGRAMMING\BASIC` samples): `make_card` puts the `src/bas` COM
       files but `CMDSHELL.COM` (ARGS, ASK, KEYTEST, SHOW) and the `tests/sd` entries in the
       card's folder `TEST`. The test card `build/tests/SD.IMG` is unchanged. ROM build 1179 ms,
       the new baseline. `BOOT` ok 0.5 s. Steps since the full suite: 2.
     - Done, lower-case 8.3 names (2026-10-20): `mksd` gave a name that fits 8.3 only its 8.3
       entry, so the user's `sd/programming/basic` showed as `BASIC`. A name that fits 8.3 with
       a lower-case letter now also gets a long name, as typed, with its upper-case 8.3 name as
       the alias. `startup.cmd` now shows in lower case too. `tests/sd` has no such name, so the
       tests are unchanged. ROM build 1363 ms, the new baseline. `BOOT` ok 0.5 s. Steps since
       the full suite: 3.
     - Done, LIST with no space (2026-10-20): MSBASIC's `LIST` printed a space before each line
       number, the sign place of `FOUT`. `LIST_NUMBER` moves to `float.s` for `CONFIG_HOSTED`
       and always skips it, so `sim` and the ROM match. 6 bytes and 7 cycles a line saved in
       bank 2; `sim` 17 bytes more; `make verify` matches. The 19 local `.out` goldens with
       LIST output and `hexbin.rom.out`, `textat.rom.out` are updated. ROM `bitfn`, `hexbin`,
       `textat`, `block` ok 0.5 to 0.6 s; ROM `files` fails only on the known FILE LIMIT line.
       ROM build 1275 ms, the new baseline. Steps since the full suite: 4.
     - Done, HDIR (2026-10-20): a HotDIR port from the user's FreeBASIC source
       (github.com/jakebullet70/HotDir). `src/utils/hotdir/HDIR.UXB` compiles to the card's
       `UTILS\HDIR.COM`, 13372 bytes; its source goes to `UTILS\SRC\HOTDIR`. `build.py`
       `compile_utils` does each `src/utils/FOLDER`; `tests.py` puts `build/UTILS` on the test
       card. The user's choices: the name `HDIR`, `src/utils/hotdir`, a short X16 list of
       extension colors, the extras `-a` (skip hidden and system), `-t` dates (and `-d`), plain
       output when redirected, `C:\UTILS` in `PATH$` (the user's `sd/startup.cmd`).
       - Switches `-1`..`-9`, `-l`, `-n -e -d -s`, `-t`, `-a`, `-c`, `-?`, combinable. 256
         names at most, 43-byte records in an 11 KB table, insertion sort of an index array.
         Pause at each full screen; Esc or Ctrl+C there ends it. The footer is the counts and
         `DISKFREE`'s free space and size.
       - Tests `HDIR` 1.3 s, `HDIRARG` 1.2 s, local `.IN`/`.OUT`. `TREE` and `FILES` goldens
         updated for the folder `UTILS` in the root; `SHTAB`, `WHERE`, `CMDLETS`, `DIRS`,
         `BASBOOT` ok. Build 1595 ms, the new baseline. Steps since the full suite: 5.
     - Done, HDIR plain output (2026-10-20; the user agreed the asm): `api_ioctl` subfunction
       0, device info: r0 = the driver's `DEV_` bits for a device, 0 for a file. +26 bytes in
       the kernel. `DOS.UXI`: `IOCTL_INFO` and `DEVICE_CHAR`, `_CLOCK`, `_NUL`, `_STDOUT`,
       `_STDIN`. HDIR is plain when handle 1 lacks `DEVICE_STDOUT` (a file, `NUL`): no colors,
       no pause, no `-c` clear, lines drawn with `-`, `|`, `+`. The footer counts its own
       columns, not `POS(0)`, which is the screen's column. HDIR 13713 bytes (+341).
       - Tests `HDIRRED` 0.7 s (new, local: `HDIR -1c TO \OUT.TXT`, `HDIR DOCS TO NUL`),
         `HDIR` 1.3 s, `HDIRARG` 1.1 s, `MORE` 0.8 s, `HEAD` 1.0 s. Build 1598 ms, the new
         baseline (a full rebuild after the kernel and `DOS.UXI` change took 4065 ms). Steps
         since the full suite: 6.
     - Done, the doc batch (2026-10-20). `HELP.TXT`: topics `HELPBAS` and `HDIR`. PLAN:
       `HELPBAS`, the card's `\UTILS`, `HDIR`, the `src/utils` folder row, `ioctl` subfunction
       0 under the driver header, the card paragraph (`card`, `SD.SUM`, `\TEST`), section 11's
       utilities. `MSBASIC/CLAUDE.md`: `HELP`, `LOAD`, `SAVE`, `KILL`, `NAME`, `FILES`,
       `K_READ`'s buffer, `con_screen`. `MSBASIC/TODO.md` section 6. No docs are owed.
       - The `CMDLETS` golden's topic list gains `HELPBAS HDIR`; the free counts are
         unchanged. `CMDLETS` ok 1.6 s. Build 1964 ms, the new baseline. Steps since the full
         suite: 7; the full suite is due next.
     - Open: the user's SAVE error, not reproduced; wait for the message and steps.
   - Banked RAM review (the user, 2026-10-20). The fixed save banks 1 to 20 hold 160 KB of a
     512 KB machine. Banks 1 to 5 (level 0) take the boot's RAM when `boot.s` runs the shell
     with `exec`, and nothing restores it: `boot.s` runs the shell again when it ends. Banks 6
     to 10 (level 1) save the shell while a program runs. Banks 11 to 20 serve levels 2 and 3.
     The order proposed; only 1 is agreed:
     1. Done (2026-10-20), the packed save stack (the user's choice over fixed levels: depth 0
        is also the monitor, whose tests at $1000 exec and need their RAM back). Each `exec`
        saves the pages from `PSP` to `PSP_TOP` and a page of zero page right after the save
        of the level before, in banks 1 to `SAVE_BANKS` (10). `save_bank` and `save_page`
        (KERNELZP, `EXEC_LEVELS + 1` bytes each, relative so reset's zeroing starts level 0
        at bank 1 `$A000`) hold where each level's save starts. `next_page` steps to the next
        save page and returns carry set at VARBANK: the save fails with error 8, and
        `api_exec` restores `RAM_BANK` and closes the file. `EXEC_LEVELS` stays 4 for the
        heap floors. Boot sets `PSP_TOP` to `>PSP` before it runs the shell, so it saves 2
        pages; `@monitor` sets it back to `>PROGRAM_END`. VARBANK is bank 11 (`HEAP.UXI`,
        `tests/HEAP.S`). Frees 80 KB (banks 12 to 21). Two full-size saves fit (306 of 320
        pages); a UXCBASIC program saves only to its end, which `uxc_link` puts in `PSP_TOP`.
        - CODE +36 B (bank 0), KERNELZP +10 B (now `$80-$E4`). A save costs about 12 cycles
          a page more (the `jsr next_page`). Boot's shell `exec` copies 2 pages, not 153.
        - X after `exec` is now `exec_depth`; the call promises no X. The goldens of `EXEC`
          (also: the `N` chain is 2 deep, exit code 9), `HEAP` and `ENDCODE` take it.
        - `tools/api.py`: `exec` describes the save and error 8; `str_heap` says bank 11.
        - Build 4308 ms (all programs recompiled for `HEAP.UXI`), then 1355 ms, the new
          baseline. Tests: `EXEC` ok 0.7 s, `HEAP` 0.5, `BOOT` 0.4. Full suite 52.4 s: 6 of
          59 failed, re-run one at a time after a golden update: `ENDCODE` ok 0.5 (X), `DUP`
          0.4 (stale since 6a0177e: `IOCTL 0` is now subfunction 0), `DOSAPI` 0.7 (stale since
          6188bdd: the root has `UTILS`), `BASRUN` 0.5, `BASLOAD` 0.8, `BASEDIT` 0.4 (stale
          since 8a795f5: LIST prints no space before a line number). Steps since the full
          suite: 0.
        - No test runs boot's re-run of the shell: no shell command ends the shell.
        - Done, the doc batch (2026-10-21). PLAN section 3: the memory map (save banks 1 to
          10, VARBANK bank 11, banks 12 and up free) and VARBANK; section 7: the packed save,
          boot's `PSP_TOP`, the nesting rule; section 13: the allocator question names banks 1
          to 10. Items 2 to 5 stay here until agreed. No docs are owed. No build, no test.
          Steps since the full suite: 1.
     2. PLAN step 10: a kernel allocator, GPC `BANKMGR` style (lowest free bank, free, count)
        with an owner byte per bank in a 256-byte table in bank 0 (`$AC00`), so `exit` frees a
        program's banks. Owner = a unique PSP id, so `keep` needs no re-tag. `exec` takes its
        save banks from it, only as many as `PSP_TOP` needs. `str_heap` checks the owner.
        Boot counts the banks. Calls 29 and 30 take a size in A (XMS-style blocks later). XMS
        chains and `xms_move` wait for a RAM disk or arrays that span banks. No fixed bank
        numbers (`CLAIM n`) in 6502DOS. About 110 B ROM, in ROM bank 1.
        - Done, 2a (2026-10-21; the user said go): `src/asm/banks.s`, in ROM bank 0 beside
          `exec`, which calls it. `BANK_OWNER` `$AC00` in RAM bank 0: 0 free, `BANK_SYSTEM`
          $FF for bank 0, the save banks, VARBANK and the banks the machine lacks, else
          `exec_depth` + 1 of the taker; `BANK_FIRST` $80 marks a run's first bank.
          `bank_init` (reset, after `heap_init`) probes bank 64, then 128: missing when a byte
          written there reads back wrong or lands in bank 0. Call 29 `bank_alloc`: A = a size,
          the lowest run of that many free banks that follow each other; A = 0 counts the free
          banks. Error 8. Call 30 `bank_free`: A = a run's first bank of the running program,
          else error 9; frees the run. `bank_exit` in `exec_unwind`, before `dec exec_depth`,
          frees the ending program's banks (256 entries, about 4400 cycles).
          - CODE +189 B, KERNELRAM +1 (`bank_want`). Not in this step: `exec`'s save banks from
            the allocator (2b), `str_heap` checks the owner and `HEAP.S` takes its bank from
            `bank_alloc` (2c), `MEM`, `keep`.
          - New test `BANKS` (`tests/BANKS.S`, child `tests/com/BANKKID.S`): counts, runs,
            a run past a lone free bank, errors 8 and 9, a child's 3 banks freed at exit.
          - Build 1403 ms, the new baseline. Tests: `BANKS` ok 0.4 s, `EXEC` 0.7, `HEAP` 0.5,
            `BOOT` 0.3. Docs owed: PLAN section 3 (the owner table, the probe, the run calls,
            bank 0 not bank 1), section 4's row, section 11 step 10 in part. Steps since the
            full suite: 2.
        - Done, 2b (2026-10-21; the user said go): each `exec` save is its own run from
          `bank_alloc`, (`PSP_TOP` - `>PSP` + 2 pages + 31) / 32 banks, from `$A000` of its first
          bank; no packing. `save_bank` (KERNELZP, `EXEC_LEVELS` bytes) holds each level's first
          bank; `save_page` and `next_page` are gone (the page step is inline). The save is
          tagged as the parent's (`exec_depth` + 1 before the `inc`), so the parent's
          `bank_free` frees it at the end of the copy back, in `parent_copy`. No free run gives
          error 8. `SAVE_BANKS` is gone; VARBANK stays 11 (`= 11` in `mem.inc`). `bank_init`
          frees banks 1 to the top and marks VARBANK system: 62 free on x16emu. A full save
          takes 5 banks, boot's shell save 1. The depth is now bound by `EXEC_LEVELS` (4).
          - CODE +11 B, KERNELZP -6 B (now `$80-$DE`). A save or copy back costs about 14
            cycles a page less (no `jsr next_page`), plus the scan of `bank_alloc`.
          - `tools/api.py`: `exec` says a run from `bank_alloc`.
          - Goldens: `BANKS` (new bank numbers; the save takes 12 to 16), `EXEC` (the `N`
            chain is 4 deep, exitcode 11; X after `exec` is now the bank after the freed run),
            `HEAP` and `ENDCODE` (X only). `tests/BANKS.S` and `tests/EXEC.S` comments updated.
          - `str_heap` still refuses banks below VARBANK (`HEAP.S` result 10, bank 5): 2c.
          - Trap: a test whose output departs from its golden shows "got" cut at the first
            differing line, which looks like a hang after `G 1000`. Run `--update` and diff.
          - Build 1847 ms, the new baseline. Tests: `BANKS` ok 0.4 s, `EXEC` 0.8, `HEAP` 0.5,
            `ENDCODE` 0.6, `BOOT` 0.4, `SHELL` 0.5. Docs owed: as 2a, plus PLAN section 3's map
            rows for banks 1 to 10, section 7's packed save (now runs), section 13's allocator
            question (answered). Steps since the full suite: 3.
        - Done, 2c (2026-10-21; the user said go): `str_heap` takes bank 11 as before; any
          other bank must have `BANK_OWNER` & ~`BANK_FIRST` = `exec_depth` + 1 (a bank of any
          run the program took), else error 9. It reads `BANK_OWNER` with `RAM_BANK` 0 and puts
          the caller's back by hand, not by `bank0`.
          - CODE +18 B. Not checked: a program that frees its heap's bank keeps `PSP_HEAP` on
            it until its exit.
          - `tests/HEAP.S` takes its bank from `bank_alloc` (`heap` at `$54`, one result more)
            in place of bank 22. Result 10 (bank 5) is a free bank, still error 9. Golden:
            `bank_alloc` gives 1, `str_alloc` A = 1, the results after it shift 3 bytes; SNAP3
            is the same. `tools/api.py` `str_heap` text and the `lib/HEAP.UXI` comments updated.
          - Trap: `git stash` then `build.py` regenerates `docs/API.md` from the stashed
            `api.py`, and `stash pop` then refuses. `git checkout -- docs/API.md`, then pop.
          - Build 1414 ms, the new baseline. Test: `HEAP` ok 0.7 s. Docs owed: as 2b, plus PLAN
            section 3's `str_heap` rule. Item 2 left: `MEM`, `keep`. Steps since the full
            suite: 4.
        - Done, 2d `MEM` (2026-10-21; the user said go): `src/scom/MEM.UXB`, `MEM [SILENT]`.
          `bank_alloc` with A = 0 gives the free banks; it prints `53 banks free, 424 KB` and
          sets `P1$` to the count. The call is inline, not a `DOS.UXI` wrapper: pyuxc keeps a
          FUNCT nothing calls, so a wrapper would grow every program. The saves of the
          programs that ran `MEM` are not free: from the monitor through the shell, 62 less 9.
          `HELP.TXT` has a `MEM` topic, and the `HELP` line names it.
          - `MEM.SCOM` 1511 bytes. ROM: none. No asm.
          - New test `MEMCMD` (`tests/MEMCMD.IN`, local): `MEM`, `MEM SILENT`, `P1$`. Golden
            `CMDLETS`: the topic list gains `MEM`.
          - Builds: 4134 ms (every `.UXB` compiled, the first build with a new `.UXB`), then
            1499 and 1381 ms; 1381 ms is the new baseline. Tests: `MEMCMD` ok 0.5 s, `CMDLETS`
            1.7. Docs owed: as 2c, plus PLAN section 8's `MEM` entry (no longer waits) and
            section 11 step 10's `MEM`. Item 2 left: `keep`. Steps since the full suite: 5.
        - Done, the doc batch (2026-10-21; the user said go). PLAN section 3: the memory map
          rows, Banked RAM (the owner table, the probe, the run calls, `exit`; XMS blocks marked
          not written), the `str_heap` rule and its trap; section 4's row for calls 29 and 30;
          section 7: the save as a run, its size, the parent frees it, the depth; section 8:
          `MEM`; section 11 step 10; section 13: the allocator question is gone. No docs are
          owed for item 2. No build, no test. Steps since the full suite: 6.
        - Done, 2e `keep` (2026-10-21; the user said go for the asm): call 28. `api_keep` in
          `exec.s` gives the program's banks to `BANK_KEPT` (`$FE`, `mem.inc`), which nothing
          frees, then ends as `exit` does with `exitcode` X = 3. `bank_exit` takes the new owner
          in Y: 0 frees, `exec_unwind` passes 0. `keep` with no program running is error 1. The
          kept program's handles close and its VARBANK strings drop, as with `exit`. The IRQ hook
          waits for `setvect`. `tools/api.py`: call 28 written.
          - ROM +18 bytes: `api_keep` 15, `ldy #0` 2, `tya`/`sta` for `stz` 1. `exit` +2 cycles,
            plus 2 a freed bank. `keep` scans the owner table twice, about 8800 cycles.
          - New test `KEEP` (`tests/KEEP.S`, `tests/com/KEEPKID.S`; `.IN` local): keep from the
            monitor (error 1), a child keeps 2 banks (code 7, X = 3), the count stays 60 after
            `BANKKID` exits at the same depth, `bank_free` of a kept bank (error 9).
          - Build 1466 ms, the new baseline. Tests: `KEEP` ok 2.0 s, `BANKS` 0.4, `EXEC` 0.7.
          - Full suite (step 7): 62 tests, 5 failed, 45.1 s. `FILES`, `HDIR`, `HDIRARG`, `TREE`:
            the root gains `BANKKID.COM` and `KEEPKID.COM`, `C:\DOS` gains `MEM.SCOM`.
            `CLOCKCMD`: `UPTIME` reads 6 s, not 5. Goldens regenerated, each diff only that;
            each 2.0 s.
          - Docs owed: PLAN section 3 (`keep is not written` in String heaps; `BANK_KEPT` in
            Banked RAM), section 7's `keep` bullet, section 11 step 10. Item 2 is done. Steps
            since the full suite: 0.
     3. UXCBASIC ROM-able output (PLAN section 12 item 6), then `CMDSHELL` in ROM banks (it is
        about 19 KB, so two banks). New commands stay `.SCOM` files on disk; a `BIND` alias
        can replace a ROM built-in. `CONFIG.SYS` `SHELL=` loads a disk shell instead.
        Parts (the user, 2026-10-21): 3a pyuxc only; 3b and 3c are asm, ask first.
        - Done, 3a (2026-10-21; the user said go, `#ORG`/`#DATA` spelling): pyuxc only.
          `#ORG address` puts the code at the address, with no `T_STUB` and no load address
          in the file. `#DATA address` puts the variables, then the array space, at the
          address, outside the file; the startup's one `T_ZERO` then clears both (`vr_n +
          bs_n` from VAR 0). Each once (`#ORG TWICE`, `#DATA TWICE`). `sb_scan` reads them
          (`dd_place_scan` in `uxc_dead.py`), so ON CASE tables see `lk_org`; `dd_keep_line`
          skips them in pass 2. Link: code past `$FFFF` is `PROGRAM TOO BIG`; data that
          meets the code is `#DATA OVERLAPS THE CODE`. `g.lk_size` is the file's bytes.
          - Without the directives the output is byte for byte the same: 103 programs
            (the tests, `src/bas`, `src/scom`) compiled by HEAD and by the new pyuxc.
          - New test `DATASEP` (`#DATA $6000`): the variables read 0, the addresses $6000,
            $6002, $6003, the string block at $6007, the array at $6013. It cannot show the
            clear of dirty RAM; checked by hand that `#ORG $C000` + `#DATA $0801` clears
            `$0801` for `vr_n + bs_n` bytes and stores page `$08` in `PSP_TOP`.
          - Test: `DATASEP` ok 0.6 s. No ROM build. Docs owed: `UXC-HELP.md` on `#ORG` and
            `#DATA`, UXCBASIC PLAN's ROM-able entry, PLAN section 12 item 6. Steps since the
            full suite: 1.
          - Left for 3b (asm): writable bytes inside runtime records (`R_ESTKH` 32,
            `R_KEY.mods` 1, `R_PRLONG.buffer` 13, `S_CHROUT` `got`/`out` (`out` starts at
            `STDOUT`), `S_CHRIN` `next`/`line` 84, `R_FIN.got`), and 6502DOS `R_FILE`'s
            `dec`/`inc` of a name's length byte, which is a literal for `OPEN("X", ...)`.
        - Done, 3b1 (2026-10-21; the user said "go asm"): no runtime record writes its own
          code.
          - Data records (`tpl/MACROS.ASM`): `#data size, zero` writes `.byte size, $FE +
            zero` and no code. Fields are `=` names in the `.block`. `#recdw` is a data word
            holding another record's address. MKTPL reads them (fixup count 254 or 255).
          - pyuxc: `rt_close` adds every record a used record names, before the startup, so
            the data records are known (`g.rt_dn_all`). They follow the temp pools, outside
            the file; `T_TOP` covers them. `rt_data_zero` emits `T_STZ` (new, `stz abs`) for
            each one with zero = 1. `rt_data_place` sets their addresses after the layout; a
            data record that joins later is `DATA RECORD LINKED LATE`. `dd_runtime_bytes`
            skips them.
          - Records: `R_ESTKH` data 32. New data `R_KEYMODS` 1 (zeroed), `R_LBUF` 13 (for
            `R_PRLONG`), `R_LINE` 84 (`next` zeroed, `line`; for `S_CHRIN`). `ZP_OUT` `$2B`
            (the output handle; `S_INIT` sets `STDOUT`, `chkout`/`clrchn` write it) and
            `ZP_GOT` `$2E` (the byte `S_CHROUT` writes and `R_FIN.getc` reads; `r0` points
            at it, no address word).
          - Sizes, 103 programs against 3a: every one smaller, 1671 bytes in all. 58 by 8
            (`S_CHROUT` 11 fewer, `R_PRSTR` 1 fewer, `S_INIT` 4 more), INPUT ones by 89 to
            102, LONG print by 53, files by 17 or 18, `KEYMODS` users by 5 or 6.
            `CMDSHELL.COM` 22048 (8 fewer). 6502DOS table 6866 to 6701 bytes. Cycles:
            `S_CHROUT` 9 fewer a character, `R_PRSTR` 1 fewer a string, `getc` 7 fewer a
            byte. Startup: 4 more each zeroed data record, 5 for `S_INIT`.
          - Checked by hand: `INPUT1` stores 0 at `$0BC8` (`R_LINE`, past the file's end
            `$0AAB`), and `PSP_TOP` gets page `$0C`.
          - Build 4258 ms, 24 programs compiled (2.8 s), the new baseline for a build that
            recompiles all. Tests: `PRINTS` ok 0.8 s, `INPUT1` 0.5, `LONGIN` 0.6, `LONG1` 0.5,
            `FILEW` 0.6, `FILER` 0.5, `KEYEXT1` 0.5, `DATASEP` 0.5. Steps since the full
            suite: 2.
        - Done, 3b2 (2026-10-21; the user said go): the 6502DOS `R_FILE` does not write the
          name. It has 3 entries, `append`, `write`, `read` (that order; BIT skips), which set
          `ZP_TMP` bit 7 for read, else bit 6 for append. `T_OPEN` calls `R_FILE.write`, new
          `T_OPENA` (id 270) `R_FILE.append`, `R_FIN` jumps to `R_FILE.read`. The stock
          `R_FILE` labels `write` and `append` at its start. pyuxc: on 6502DOS `sg_open` passes
          the name as it is (no letter, no `sg_open_join`) and emits `T_FOPEN`, `T_OPEN` or
          `T_OPENA`. An appended file that was made new is not sought.
          - Sizes against 3b1: `R_FILE` 24 bytes fewer (6502DOS table 6701 to 6685, `T_OPENA`
            8 of it). 6 programs smaller, 306 bytes: `FILEW` 114 (variable names lose the
            copy and the joins), `SHOW` 61, `FILEB`/`FILER` 39, `FILEERR` 27, `FILEINCLOSED`
            26. Cycles: an OPEN for reading about 60 fewer.
          - Build 4668 ms (24 programs recompiled), the new baseline. Tests: `FILEW` ok 0.7 s,
            `FILER` 0.5, `FILEB` 0.5, `FILEERR` 0.5, `FILEINCLOSED` 0.5. No test appends to a
            missing file (checked by reading). Steps since the full suite: 3.
          - Docs owed: PLAN line 1251 and UXCBASIC PLAN line 1493 still say `OPEN` passes the
            mode letter.
        - Done, 3b3 (2026-10-21; the user said go, asm ok): `R_FILE` drops `bra handle`, so a
          made file is sought to its end too (offset 0, one more API call per `O.WRITE`).
          `R_FILE` 2 bytes fewer (table 6683), the 6 programs with `OPEN` 2 bytes each. Build
          5136 ms, the new baseline. Tests: `FILEW` ok 0.7 s, `FILEB` 0.5, `FILEERR` 0.5.
          Steps since the full suite: 4.
        - Done, 3b4 (2026-10-21; the user said go): audit, no code changed. No template in
          `tpl/` or `tpl/UXDOS/` writes to a source string. Every store through a pointer goes
          to a destination block (`ZP_DST`, the temp `S0`, a READ buffer), an array element,
          a record field or POKE's address. `S_CHROUT` and `S_CHRIN` write data records only.
          3b is done. Steps since the full suite: 4.
        - Done, the doc batch (2026-10-21; the user said go). UXC-HELP: new topic Placing the
          code and the variables (`#ORG`, `#DATA`); `MKHELP.PY` 0.24 s, 40 topics. UXCBASIC
          PLAN: the ROM-able entry is done; the 6502DOS `OPEN` passes the name as it is. PLAN
          section 3: `BANK_KEPT`, `keep is not written` gone; section 7: the `keep` bullet;
          section 11 step 6d: `OPEN`; section 12 item 6. No docs are owed. No build, no test.
          Steps since the full suite: 5.
        - Done, 3c (2026-10-21; the user said "go on asm"): a UXCBASIC program in ROM bank 3.
          - `src/bank3/` holds one `NAME.UXB` (now `ROM3TEST.UXB`, with `#ORG $C000` and
            `#DATA $0801`), `bank3.s` (`.incbin` of the program at `$C000`, the `$FFA0` IRQ
            entry, the `$FFFA` vectors), `bank3.cfg`, and `stub.s` (7 bytes: `lda #3`,
            `sta ROM_BANK`, `jmp ROM`). `build.py` `build_bank3` compiles it to
            `build/bank3/BANK3.BIN`, links bank 3, appends it after MSBASIC's bank 2 (the ROM
            is 65536 bytes), and writes the stub to `build/bas/NAME.COM`. `make_templates` now
            runs before it. ld65 stops the link when the code reaches `$FFA0`.
          - Found: the kernel runs in bank 0 or 1, so a pointer it gets into `$C000-$FFFF`
            reads bank 0. A literal handed to `write` (PRINT), `open`/`create` or `exec`
            failed. The user chose: literals to RAM.
          - pyuxc: with `#DATA`, the strings lie at its address, then the variables, then the
            array space. New template `T_LITCOPY` (id 271, 50 bytes, inline) copies the
            literals there at startup from the label `%STRS` in the file (`lk_strs_copy`).
            Strings that join after it stop the link: `STRINGS ADDED LATE`. The overlap check
            starts at `lk_data`. Cost: RAM = the literals (CMDSHELL 1096 bytes), about 16
            cycles a byte at start (CMDSHELL about 18000). Table 6683 to 6755 bytes.
          - Without `#DATA` the output is byte for byte the same: 125 programs compiled by
            HEAD and by the new pyuxc; only `DATASEP` (its source changed) differs.
          - `DATASEP` now peeks the literal `"HI"` at `$6001` (2, 72) and W at `$6004`.
          - New test `ROM3` (`.IN` local): INPUT, a FUNCTION's string, an array, LONG, a file
            written and read back, `DOS.EXEC` of `ARGS.COM`, then `PEEK($01)` reads 3.
          - Build 4699 ms (all recompiled), the new baseline; bank 3 alone 1810 ms. Tests:
            `ROM3` ok 0.4 s, `DATASEP` 0.5, `SHBOOT` 0.5, `ASK` 0.4.
          - Full suite (step 7): 63 tests, 4 failed, 47.0 s. `FILES`, `HDIR`, `HDIRARG`,
            `TREE`: the root gains `ROM3TEST.COM` (9 bytes), and the compiled `.COM` sizes
            follow 3a and 3b (most smaller, `ENDCHILD.COM` 126 to 130). Goldens regenerated,
            each diff only that; each 2.0 s. Re-runs: `FILES` ok 0.4 s, `HDIR` 1.4, `HDIRARG`
            1.2, `TREE` 1.5. Steps since the full suite: 0.
          - Left for 3d: `CMDSHELL.COM` is 22048 bytes, more than one bank; the user chose a
            split across banks 3 and 4 (3d below).
        - Done, the doc batch (2026-10-21; the user said go). UXC-HELP Placing the code and
          the variables: the literals at `#DATA`, the kernel trap; `MKHELP.PY` 0.26 s, 40
          topics. UXCBASIC PLAN: the ROM-able entry. PLAN section 3: the ROM map (banks 2 and
          3), the trap on a pointer into `$C000-$FFFF` and the IRQ hook; section 10: the
          65536-byte ROM and `src/bank3`; section 12 item 6. No docs are owed. No build, no
          test. Steps since the full suite: 1.
        - 3d, `CMDSHELL` split across ROM banks 3 and 4 (the user, 2026-10-21; asm ok).
          `CMDSHELL` is 22046 bytes of code: 390 main, 18967 in 122 SUBs, 1523 startup and
          runtime, 1096 strings. A bank holds 16288 bytes below `$FFA0`. Parts, one a step:
          - 3d1 (done): ON CASE tables as fixups.
          - 3d2 (done): pyuxc `#ROMBANKS 3, 4` with `#ORG`. The SUBs at the tail, in code order, go
            to the second bank, as many as the first bank needs. Main code, the startup and
            the strings stay in the first. Each bank holds its own copy of the runtime records
            (CMDSHELL about 1.5 KB more). A call to a SUB in the other bank goes to a veneer
            in the caller's bank, 7 bytes a target: `lda #<S`, `ldy #>S`, `jmp far`. `far`, 23
            bytes at the same address in both banks just below `$FFA0`: `sta`/`sty` a RAM
            vector (a 2-byte data record), `lda #other`, `sta ROM_BANK`; in the other bank
            `jsr` to `jmp (vector)`; then `pha`, `lda #other`, `sta ROM_BANK`; back home `pla`,
            `rts`. It keeps X (the expression stack) and returns A/Y. About 50 cycles a call
            more than a JSR. A GOTO, a label or a jump into the other bank is an error. The
            JMP around each moved SUB is dropped (3 bytes). pyuxc writes two images.
          - 3d3 (done): `build.py` bank 4 (`bank4.s`, the `$FFA0` IRQ entry and vectors); the ROM
            becomes 81920 bytes. `ROM3TEST` splits across banks 3 and 4 and tests the calls
            both ways, X kept, BYTE, WORD, LONG and STRING results.
          - 3d4: `CMDSHELL` in banks 3 and 4 (a wrapper source in `src/bank3` with `#ORG`,
            `#DATA`, `#ROMBANKS` and `#INCLUDE`); then the boot shell.
        - Done, 3d1 (2026-10-21; the user said split across banks 3 and 4): ON CASE tables
          are fixups. Bug found: `cs_table` wrote each target as `g.lk_org + offset` with no
          fixup, so when dead-code stripping cut a SUB before an ON CASE, every target pointed
          past its body by the bytes cut (14 in a scratch test). Each table byte is now a
          `K_F_LO` or `K_F_HI` `K_SEC_CODE` fixup (`uxc_case.py`), so the split can move the
          table with its code too. No byte or cycle change; 2 fixups an entry at compile time.
          - 211 sources (tests, `src`, `src/utils`) compiled by HEAD and by the new pyuxc: only
            `ONCASE` differs, the same size, the table bytes fixed.
          - `tests/ONCASE.UXB` gains `SUB NEVER_CALLED` before the first ON CASE; the golden
            is unchanged.
          - Tests: `ONCASE` ok 0.7 s, `JUMPOUT` 0.5. No ROM build. Docs owed: none. Steps since
            the full suite: 2.
        - Done, aside before 3d2 (2026-10-21; the user asked for the free low RAM in `MEM`):
          `MEM` prints `38655 bytes low RAM free` first, then the banks line, and sets `P2$`
          to `38655`. The value is a constant: `exec` saves the parent, so every program gets
          all of `$0801–$9EFF`, and `keep` holds banks only. `HELP.TXT`'s `MEM` topic and PLAN
          section 8's `MEM` entry name the line and `P2$`, in that order.
          - `MEM.SCOM` 1582 bytes, 79 more. ROM: none. No asm.
          - `tests/MEMCMD.IN` (local) prints `P2$` too; golden updated (local).
          - Build 1922 ms, the new baseline. Test: `MEMCMD` ok 0.6 s. Docs owed: none.
            Steps since the full suite: 4.
        - Done, 3d2 (2026-10-21): pyuxc `#ROMBANKS first, second`, with `#ORG` and `#DATA`
          (else an error). New `uxc_rombank.py`; its docstring has the layout.
          - The link cuts the SUBs at the tail, in code order, into the second bank, the
            fewest that let the first bank fit. Each bank's file runs from `#ORG` to `$FFA0`,
            filled with `$FF`, and ends with `T_FAR` at `K_FAR` (`$FF89`). The second file is
            `NAME.PR2`; the result line adds `,SECOND NAME.PR2 <bytes>`, and the screen says
            each bank's bytes used.
          - New templates, ids at the end: `R_FARVEC` (2 bytes of RAM), `T_FAR` (23 bytes,
            S0 the other bank), `T_FARCALL` (the 7-byte veneer). New macro `#recind`
            (`jmp (record)`) in `MACROS.ASM`.
          - Each bank places only the runtime records its code names; the data records are
            placed once, for both. A GOTO or jump between the banks stops the link (`JUMP
            ACROSS ROM BANKS`, `GOTO ACROSS ROM BANKS`).
          - Bug found: `dd_strip` moved each live SUB's start but not its `K_SY_END`, so the
            ends were stale once a dead SUB was cut. `dd_records` moves it too. No output
            change.
          - Cost: 7 bytes a SUB called across, 23 a bank, 2 of RAM; 3 bytes saved a SUB moved.
            About 50 cycles a call across. No change without `#ROMBANKS`: the 211 sources
            compile byte-identical to HEAD.
          - Checked with a scratch checker (`T_FAR` in both, every veneer, every SUB call):
            a generated 28-FUNCTION program, one with STRING and LONG FUNCTIONs, one small
            program, and `CMDSHELL` with `#ORG $C000`, `#DATA $0801`: bank 3 16008 bytes,
            bank 4 7120; SUBs 104 to 121 moved; 114 calls across, 10 veneers in bank 3 and 56
            in bank 4. Not yet run: that is 3d3.
          - Build 4423 ms (every program recompiled, the template table changed), the new
            baseline. Test: `ROM3` ok 0.6 s. Docs owed: `UXC-HELP.md` (`#ROMBANKS`),
            `pyuxc/README.md` (the result line). Steps since the full suite: 5.
        - Done, 3d3 (2026-10-21; the user said go): `ROM3TEST` runs from ROM banks 3 and 4.
          - pyuxc: `#ROMBANKS first, second, NAME` takes an optional SUB or FUNCTION name: it
            and every SUB after it in code order go to the second bank, and more before it
            when the first bank needs (`g.rb_name`, `g.rb_start`). A name that is not a live
            SUB stops the link: `#ROMBANKS SUB NOT FOUND`. Compile time only. `ROM3TEST` (2 KB)
            needs it to split at all.
          - `src/bank3/bank3.s` and `bank3.cfg` are now `bank.s` and `bank.cfg`, assembled
            once a bank with `-D BANK=3` and `-D BANK=4`; `.incbin .sprintf("BANK%d.BIN",
            BANK)`. Segment `FARIRQ` (was `FARIRQ3`); `nmi` (an `rti`) moved there from CODE,
            since the file now fills CODE to `$FFA0`.
          - `build.py` `build_bank3` compiles to `BANK3.BIN` and `BANK4.BIN` (empty when the
            program fits bank 3) and appends banks 3 and 4: the ROM is 81920 bytes.
            `uxb.compile(source, program, second)` copies the `,SECOND` file to `second`, or
            removes it; a `#ROMBANKS` source counts as up to date only when both exist.
          - `ROM3TEST`: `#ROMBANKS 3, 4, FAR_BYTE`. Bank 3 2365 bytes, bank 4 698; 6 veneers
            in bank 3, 2 in bank 4; 11 of 14 SUB calls cross. It prints `42 2000 1000000`
            (BYTE, WORD, LONG), `217` (`5 + FAR_WORD(3) * 2 + FAR_BYTE(1) * 100`: X kept),
            `HELLO, ADA! BANK 4` (a STRING; bank 4 calls `GREETING` in bank 3), `115` (bank 4
            to 3 to 4) and `SUB IN BANK 4`. `ROM3.OUT` updated (local).
          - Cost: ROM 16 KB more (bank 4). The scratch checker: bad 0. The 211 sources: only
            `ROM3TEST` differs from HEAD.
          - Build 4582 ms (every program recompiled, pyuxc changed), the new baseline. Tests:
            `ROM3` ok 0.4 s, `SHBOOT` 0.4. Docs owed: `UXC-HELP.md` (`#ROMBANKS` with the
            name), `pyuxc/README.md` (the result line), PLAN line 1183 (`bank.s`, bank 4, the
            81920-byte ROM). Steps since the full suite: 6; the next step runs it.
     4. Relocation (section 12 item 7) is optional after 3.
     5. Any time: `HELP NAME` with no topic in `HELP.TXT` reads `NAME.TXT` beside the command.
     PLAN sections 3, 7, 11 and 13 take items 2 to 5 at the doc batch after each is agreed.
   - To do: find what the 492 bytes of 7i2b cost in `DISKFREE.CBI` (1861 to 2353 bytes), with
     pyuxc's link map, and cut them. Ideas: read `P2$` once, drop `FREE_TEXT` and pass the
     `MID$` straight to `SYS_STRINGS_SET`, reuse `DRIVE_NAME` for the text (11 bytes of RAM).
   Before the buffer: about 9 ms a line at the start of a file, 15 ms at 3000 bytes.
   Relocatable output (UXCBASIC plan, "Relocatable output") is the later step: the child loads
   above the parent with no copy. Measured on the shell: 2518 fixups, 2178 bytes to patch (1838
   addresses, 340 high bytes), the runtime templates not counted; a table of 2.2 to 4.4 KB.
   To do, after 7e2, taken from MS-DOS 2.0's `COMMAND` (agreed 2026-10-15):
   - Break, in 3 steps (the user, 2026-10-18): B1 the kernel, B2 the shell, B3 UXCBASIC.
     The STOP key is Ctrl+C (the user's choice over Ctrl+Break and Esc). The asm was agreed.
     - Done, B1 (2026-10-18): call 47 `con_break` (MS-DOS 33h). Carry set gets the mode in A
       and the flag in X and clears the flag; carry clear sets the mode from A, 0 to 2, else
       error 13. `api.py` `BREAK_MODES`: `BREAK_OFF` 0 (Ctrl+C is $03), `BREAK_END` 1 (prints
       `^C` CR LF and ends the program with code 0; `exitcode` gives X = 1), `BREAK_CATCH` 2
       (drops the key, sets the flag). `genapi.py` writes them to `api.inc` and a table in
       `API.md`.
       - The mode is `PSP_BREAK` (`$0703`). `tail_copy` sets a child's to `BREAK_END`; the
         parent's comes back with its PSP. Boot sets 0 for the monitor. The flag is
         `con_broke` (KERNELRAM), cleared by `con_init`.
       - `con_status` checks at `@key`, so the key queue and the SMC both count, and so do
         `con_in`, `con_line` and `GETKEY`. Ctrl+C is seen only while a program asks for a
         key. `exec_break` (`exec.s`) unwinds to `PSP_STACK` from inside any call;
         `exit_how` (KERNELRAM) holds X for `exitcode`. `api_exit` and the RTS path go through
         `exit_normal` and `exec_quit`.
       - Trap: the store of `PSP_BREAK` in `api_exec` put `bcs @no_memory` out of range; it
         went into `tail_copy`.
       - ROM: CODE +84, RODATA +4 (`^C` CR LF), KERNELRAM +2. RODATA ends at `$EC9A`; 4916
         bytes free below `$FFCF`. Byte saving not applied: `con_broke` in zero page saves 6
         bytes (no `stz` in `con_init`, 1 byte shorter each use) and takes 1 of the 2 zp
         bytes left.
       - New test `BREAK` (`tests/BREAK.UXB`, child `tests/com/BRKKID.UXB`): the start mode 1,
         set 2, Ctrl+C then A reads 65 with flag 1, a second get flag 0, set 0 reads 3, set 3
         gives carry and 13, the child ends at `^C` with exit 0 how 1, the parent's mode 0
         back. `BREAK.IN` holds raw $03 bytes: x16emu `-bas` pastes them. `BREAK` ok 0.4 s.
       - Build 1508 ms with every program recompiled, then 603 ms for the ROM alone, the new
         baseline. Tests: `EXEC` ok 0.7 s, `ENDCODE` 0.5, `SHBOOT` 0.5, `SHELL` 0.5, `ASK`
         0.4, `DUP` 0.4. Golden churn of the 2 new files, rewritten and diffed: `FILES` ok 0.4,
         `DIRS` 0.9, `DISK` 0.4, `CMDLETS` 1.5.
       - Docs owed: PLAN section 4 (call 47), section 7 (lines on the break handler: the PSP
         byte, the modes; `getvect`/`setvect` vector 1 is not used).
     - Done, B2 (2026-10-18): `CMDSHELL` sets `BREAK_CATCH` at start. `STOPPED` is set by `POLL_BREAK` (`con_status`, then `BREAK_FLAG`,
       the get) or by `RUN_PROGRAM` when `exitcode` gives X = 1. After each line while
       `SCRIPT_ACTIVE`, the main loop polls, and `STOPPED` runs `ASK_TERMINATE`: `Terminate
       CMD job (Y/N)?` until y, Y, n or N (`AND 223`), echoed in capitals; Ctrl+C counts as
       Y; Y clears `SCRIPT_ACTIVE`. The main loop clears `STOPPED` after each line. At the
       prompt the flag is read and dropped after `CON_LINE`, so a Ctrl+C in the line does
       nothing. `PAUSE` and `WAIT` (once a second) poll too and end at Ctrl+C.
       - Trap: the poll reads only the key at the head of the queue. A Ctrl+C typed ahead is
         seen after the line before the program that would read it; one behind another key
         is seen only when a program reads up to it.
       - `BRKKID` now prints `KEY` and the code of each key until Ctrl+C. `BREAK.OUT` holds.
       - `CMDSHELL.COM` 18864 to 19163 bytes (+299; `AND 223` saved 11).
       - New test `SHBREAK` (`SHBREAK.IN` written by Python, raw $03 bytes; scripts
         `tests/sd/SCRIPTS/BRKRUN.CMD`, `BRKPOLL.CMD`): Ctrl+C in a prompt line, `PAUSE` at
         the prompt after it, a child ended twice (N, then x and Y), the poll path (n, then
         Ctrl+C as Y). Not tested: Ctrl+C inside `PAUSE` or `WAIT` in a script, since the
         poll before them takes a typed-ahead one.
       - Build 1578 ms, then 1077 ms (shell only). Tests: `SHBREAK` ok 0.5 s, `BREAK` 0.4,
         `SHELL` 0.5, `SHSCRIPT` 0.8, `SHSCREEN` 0.6, `SHBOOT` 0.5, `SHRUN` 0.7, `DISK` 0.4,
         `SHFILES` 0.6, `SHGOTO` 0.6, `SHIF` 0.5, `SHREPEAT` 0.6, `SHREDIR` 0.9, `SHVARS` 0.5,
         `SHBIND` 0.4. Churn, rewritten and diffed: `FILES` ok 0.4, `DIRS` 0.8, `CMDLETS` 1.4.
       - Docs owed: PLAN section 8 (Ctrl+C in scripts, the question, `PAUSE` and `WAIT`).
     - Done, B3 (2026-10-18): `lib/DOS.UXI` has `ENUM STOP` (`OFF` 0, `ENDS` 1, `CATCH` 2),
       `SUB STOP_KEY(MODE)` (sets the mode, then `READ_ERR_STATUS`: a bad mode gives error 13)
       and `FUNCT STOP_PRESSED()` (the get; returns the flag, leaves `ERROR`). `CMDSHELL` calls
       `DOS.STOP_KEY(DOS.STOP.CATCH)` and `DOS.STOP_PRESSED()`; its `BREAK_FLAG` is gone.
       - Trap: `ON` is a reserved name in UXCBASIC (`?RESERVED NAME ON`), so the mode that
         ends the program is `ENDS`.
       - `CMDSHELL.COM` 19163 to 19179 bytes (+16: the call of `STOP_KEY` with its parameter
         and `READ_ERR_STATUS` is longer than the 3 stores and `SYS` inline). Programs that do
         not call them keep their sizes. PLAN section 2 (`DOS.UXI`) has the names. No compiler work, so
         nothing goes in `UXCBASIC.PLAN.md` or PLAN section 12.
       - Build 1624 ms (every program), the new baseline. Tests: `SHBREAK` ok 0.6 s, `BREAK`
         0.4, `FILES` ok 0.4 (golden rewritten: `CMDSHELL.COM` 19179, diffed), `DIRS` 0.8,
         `CMDLETS` 1.5, `SHELL` 0.5, `SHSCRIPT` 0.7.
       - Docs owed for break, a batch: PLAN section 4 (call 47), section 7 (the PSP byte, the
         modes), section 8 (Ctrl+C in scripts); `UXC-HELP.md` has no topic on the STOP key.
     - Done, B4 (2026-10-18), in pyuxc: `AS ENUM.name` types a parameter, a FUNCTION result,
       a variable or a field (the user chose the `ENUM.` prefix). A constant passed to such a
       parameter must be a member of that ENUM (`NOT A MEMBER OF STOP`). `STOP_KEY` takes
       `MODE AS ENUM.STOP`. UXCBASIC's `docs/HANDOFF.md` and `UXCBASIC.PLAN.md` have the
       design; UXC-HELP "ENUM" has the reference.
       - 0 bytes: `CMDSHELL.COM` stays 19179. Build 1548 ms, the new baseline.
       - Tests: UXCBASIC `ENUMAS` ok 0.7 s (new), `ERRENUMMEMBER` ok 0.0 (new), `ENUM` 0.5,
         `ERRENUMOPEN` 0.0, `SUB1` 0.5, `FUNC1` 0.6, `NAMES` 0.5, `ERRSUBTYPE` 0.0, `TYPEDEF`
         0.5; repo `SHBREAK` 0.5, `BREAK` 0.4.
     - Done, B5 (2026-10-18), in pyuxc: a bare member in an argument to a parameter of an
       ENUM's type, `DOS.STOP_KEY(CATCH)`. The member hides a variable of the same name in
       that argument. UXC-HELP "ENUM" and `UXCBASIC.PLAN.md` have it.
       - 0 bytes: `CMDSHELL.COM` stays 19179. Build 1615 ms, the new baseline.
       - Tests: UXCBASIC `ENUMBARE` ok 0.6 s (new), `ENUMAS` 0.5, `ERRENUMMEMBER` 0.0,
         `ENUM` 0.5, `SUB1` 0.5, `FUNC1` 0.5, `NAMES` 0.5, `TYPEDEF` 0.5, `STRSUB` 0.5,
         `STRNS` 0.6, `RECSTR` 0.5, `RECORD4` 0.5; repo `SHBREAK` 0.5, `BREAK` 0.4.
     - Docs step after break (2026-10-18); the break docs owed above are written. PLAN
       section 2: the IRQ row drops "the break check". Section 4: the `con_break` row. Section
       7: `PSP_BREAK` in the PSP table, the STOP key modes table and its rules, vector 1 not
       used. Section 8: the prompt in column 0, the shell in `BREAK_CATCH`, `PAUSE` and `WAIT`
       end at Ctrl+C, the `Terminate CMD job (Y/N)?` rules and the type-ahead trap.
       UXC-HELP: topic "The STOP key" (its example compiles, 419 bytes); GETKEY gives the
       character code and the extended-key 0, no PETSCII. `MKHELP.PY` ok, 37 topics. No build,
       no test.
       - Byte saving seen, not applied: none. `CMDSHELL.UXB` line 1660 could read
         `DOS.STOP_KEY(CATCH)`; 0 bytes.
       - Next: the VIEW.COM key bug.
     - TED, the Tiny Editor, a full-screen editor (2026-10-18), `src/dos/TED.UXB`, built to `C:\DOS\TED.COM`.
       The user's choices: Shift+arrows select (no mark key), Ctrl+X cuts, insert mode only.
       Its steps:
       - E1 load, show, the cursor keys, PgUp/PgDn, Home/End, the status row, Ctrl+Q. Done.
       - E2 typing, Enter, Tab, Backspace, Delete (joins lines), the `*` modified mark. Done.
       - E3 Ctrl+S save through `TED.$$$`, delete, rename; `Save changes (Y/N)?` at Ctrl+Q.
         Done.
       - E4 Shift+arrow select, Ctrl+C copy, Ctrl+X cut, Ctrl+V paste; Ctrl+C or Ctrl+X with
         no selection takes the line. A 2 KB clipboard. Done.
       - E5 docs: PLAN section 8, a `HELP.TXT` topic.
       - Design: a gap buffer in the pool from the page after `PSP_TOP` to `$9EFF`. The gap stays at
         the end in E1; E2 moves it. Load turns CR LF and CR into LF; `CR_ENDS` keeps the first
         line end's style for save. `STOP_KEY(OFF)`, so Ctrl+C reads as 3. Keys come from
         `API_CON_IN`, which blinks the cursor. The page is drawn only when no key waits, the
         first page always. A move one line below the page scrolls in hardware (a CR on the status
         row, as VIEW), else the page is drawn again; the console has no insert or delete line.
       - Shift: `kbd_get` reads the SMC keycodes in order when asked, so `kbd_mods` is right for
         each key. After the 0 of an extended key, `API_CON_STATUS` returns at once with
         `kbd_mods` in X. Shift+arrows need no asm.
       - Test trap: `-bas` cannot type an extended key; a queued 0 reads as no key. The arrows,
         Home, End, PgUp and PgDn are untested by `tests/TED`. A hook in `con_status` (a queued
         0 takes the next queued byte as the scan code, about 10 bytes) would let a test type them;
         it is asm, so the user decides.
       - E1: `TED.COM` 5399 bytes; its variables end at `$227A`, so the pool is `$2300–$9EFF`,
         31744 bytes. Build 770 ms, the new baseline.
       - Test `TED` (new): no name, a new file, path not found, the `LONG.TXT` page, Ctrl+Q. ok
         0.6 s. Full suite: 37 tests, 3 failed, 20.4 s: `CMDLETS`, `DIRS`, `DISK`, disk layout
         only from the new file. Their goldens regenerated; re-run ok: `CMDLETS` 1.5 s, `DIRS`
         0.8, `DISK` 0.5.
       - Test card layout (2026-10-18): `tools/tests.py` gives the programs (`build/bas`,
         `build/tests`, `build/DOS`) a block of 256 clusters after the files of `tests/sd`, and
         the root directory 2 clusters. `mksd.make(reserve=, root_clusters=)` does it; the FAT
         marks the unused clusters of the block bad ($0FFFFFF7), and `api_diskfree` and
         `cluster_free` count only zero entries. A new or resized program no longer changes
         `CMDLETS`, `DIRS` or `DISK`. mksd exits with an error when the programs outgrow the
         block. Their goldens regenerated once. Proof: a 20 KB dummy in `build/DOS`, then
         `DISK` ok 0.5 s, `CMDLETS` 1.7, `DIRS` 0.9.
       - E2 (2026-10-18): `MOVE_GAP` moves the gap a byte at a time (the language has no block
         copy). `INSERT` puts a byte at the cursor, `REMOVE` takes one out. A character from 32
         up goes in; Enter puts in LF, Tab a tab. Backspace and Delete take out LF too, so they
         join lines. A full pool shows `Insufficient memory` on the status row. A change on one
         line draws only that row (`NEED_ROW`, `ROW_LINE`, `ROW_START`); a second line changed
         before a draw, or LF in or out, draws the page. `MODIFIED` puts `*` in column 0 of the
         status row.
       - E2 cost: `TED.COM` 6583 bytes, 1184 more; the pool starts later by as much. Build
         816 ms, the new baseline.
       - Test trap: the keys of a test all wait in the queue, so TED draws nothing after the
         first page and the golden does not show an edit. `tests/TED.IN` types
         `ab`, Tab, `c`, Backspace, Enter, `xy`, Backspace three times, `Z`; the golden is
         unchanged. A build that drew after each key showed each step right, the tab to column
         9 and both joins included. E3's save, then `TYPE`, will test the text.
       - Test `TED` ok 0.7 s.
       - E3 (2026-10-18): `SAVE` writes `TED.$$$` in the file's directory (the part up to the
         last `\`, `/` or `:`), deletes the file (not found is no error), then renames
         `TED.$$$` to it. A failed create, write or delete deletes `TED.$$$`; a failed
         rename keeps it, since the file is gone. `WRITE_PART` writes the gap buffer's two parts,
         each LF as CR LF from `CR_LF` when `CR_ENDS` is 1, so a new file gets CR LF. A short
         write gives `DOS.DISK_FULL`, shown as `Insufficient disk space`; another error shows
         `DOS.ERRMSG`. Success clears `MODIFIED` and shows `Saved`. `ASK_QUIT` at Ctrl+Q:
         no changes quits; else `Save changes (Y/N)?`, N quits, Y quits when the save worked,
         another key (an extended key's scan code read too) goes back.
       - Wildcards: `name_check` in `fat.s` rejects a `?`, so open, create and delete refuse a
         wildcard name; a save of one fails with its error.
       - E3 cost: `TED.COM` 8011 bytes, 1428 more; the pool starts later by as much. Build
         766 ms, the new baseline.
       - Test `TED`: saves the E2 edits and `TYPE`s them (`ab`, tab, `Z`); `DOCS\NEW.TXT`
         typed, Ctrl+Q, `x` goes back, Ctrl+Q, `y` saves; `TYPE` shows two lines; edited
         again, Ctrl+Q, `n`: `TYPE` shows it unchanged; `FILES DOCS\*.$$$` finds none. Golden
         regenerated, read, ok 0.8 s.
       - E4 (2026-10-18): after the 0 of an extended key, `API_CON_STATUS` gives `MODIFIERS`.
         Shift with Home, Up, PgUp, Left, Right, End, Down or PgDn sets `ANCHOR` at the cursor
         when no selection runs and sets `SELECTING`; another key but Ctrl+C clears it.
         `SELECTION_BEGIN` and `SELECTION_END` (both 0 for none) are set after each key, after
         the key's action, so Ctrl+X still sees an ended selection. `SHOW_ROW` writes the row in
         three runs, the marked one in reverse video (`CSI 7m`, `sgr` in `console.s`); a marked
         LF shows as one space. A changed selection draws the cursor's row when the cursor
         stayed on its line, else the page.
       - Clipboard: a fixed 2048 bytes at `CLIPBOARD` $9700–$9EFF; `POOL_END` is now $9700.
         `TAKE` (Ctrl+C 0, Ctrl+X 1) takes the selection, or the cursor's line with its LF;
         over 2048 bytes shows `Selection too large`. It moves the gap to the part's end, so a
         cut is a gap grow. `PASTE` (Ctrl+V) inserts at the cursor; no room shows
         `Insufficient memory`. `COPY_CLIP` is the copy loop of both and counts LFs. Typing
         does not replace a selection.
       - E4 cost: `TED.COM` 9846 bytes, 1835 more, and the clipboard takes 2048 bytes of the
         pool. Sharing `COPY_CLIP` saved 97 bytes. Build 903 ms, the new baseline.
       - Test `TED`: `DOCS\NEW.TXT` edited: Ctrl+X, Ctrl+V twice, Ctrl+C on the last line
         (no LF), Ctrl+V, Ctrl+S, Ctrl+Q; `TYPE` shows `one`, `one`, `twotwo`. Golden gained
         only those lines, read, ok 0.9 s. Shift selection and its reverse video are untested
         (the extended-key trap above); try them by hand.
       - Keys row (2026-10-18): 28 text rows, the status row on row 28, `KEYS_ROW` 29 with
         `KEYS_TEXT$` (^S Save, ^Q Quit, Shift+Arrows Select, ^C Copy, ^X Cut, ^V Paste) in
         the status colors. The status row lost `^Q Quit`. `SHOW_KEYS` draws it at the start
         and after a scroll; the scroll's CR now goes on `KEYS_ROW`. PgUp and PgDn move 28
         lines. `TED.COM` 9923 bytes, 77 more. Build 996 ms, the new baseline. Golden
         regenerated, read, ok 1.0 s.
       - Rename (2026-10-18): EDLIN is TED, the Tiny Editor: `src/dos/TED.UXB`, `C:\DOS\TED.COM`,
         test `TED`, the save file `TED.$$$`. Ctrl+Q prints `TED - The Tiny Editor... Bye!`
         after it clears the screen. `TED.COM` 9962 bytes, 39 more. Build 784 ms, the new
         baseline. Golden regenerated, read, ok 1.3 s.
       - Help (2026-10-18): Ctrl+G or F1 runs `SHOW_HELP`: it clears the screen, prints
         `C:\DOS\TED.HLP` raw through `API_CON_OUT` 80 bytes at a time, waits for a key, then
         draws the keys row and the page again. No TED.HLP puts its error on the status row.
         `src/dos/TED.HLP` stays under 30 rows, so the screen does not scroll. `tools/build.py`
         copies each `src/dos/*.HLP` to build/DOS, as it does `*.TXT`. `^G Help` leads the keys
         row, 76 characters. `TED.COM` 10341 bytes, 379 more; TED.HLP 802 bytes on disk. Build
         815 ms, the new baseline. Golden: the new keys row, and a new run `^G`, a space, `^Q`.
         Ok 0.9 s. F1 is untested: the tests cannot type extended keys.
         Trap: a test stops reading at the first line that departs from the golden, so a
         changed early line looks like a crash. Run `--update` and diff instead.
       - Footer (2026-10-18): the keys row is gone. 29 text rows, the status row on row 29 with
         `F1 Help` after the column; a scroll's CR goes on the status row. PgUp and PgDn move 29
         lines. `SHOW_HELP` puts out a CR before each LF of TED.HLP, since the console's LF
         keeps the column. TED.HLP lists F1 first. `TED.COM` 10279 bytes, 62 less. Build 868 ms,
         the new baseline. Golden regenerated, diffed, ok 1.0 s. The help page's layout on
         screen is not in the golden (it holds the byte stream); check it by hand.
         Trap: Python's text-mode write on Windows makes CR LF; the sources are LF. Write bytes.
       - `SHOW_STATUS`, from the user's hand edit: the status text cut to `COLUMNS - 9`, then
         `CONS.LOCATE` to column `COLUMNS - 9` and `F1 Help`. Fixed in the edit: a missing `;`
         after `CLEAR_EOL$` (a newline on the last row scrolls), no `"  "` before `MESSAGE`, the
         column 71 written as a number, a second `STATUS_COLORS$` before `F1 Help`.
       - The console names, in three steps, then E5. The user chose all three:
         1. A, done 2026-10-18: plain names in `lib/CONS.UXI`. `CURSOR_UP$` `CURSOR_DOWN$`
            `CURSOR_RIGHT$` `CURSOR_LEFT$` `CURSOR_HOME$`, `CLEAR_SCREEN$` `CLEAR_EOL$`,
            `NORMAL$` `BOLD$` `REVERSE$`, `BLACK$` to `WHITE$` (SGR 30 to 37), `ON_BLACK$` to
            `ON_WHITE$` (40 to 47); `CSI$` stays. TED's `STATUS_COLORS$` and VIEW's
            `FOOTER_COLORS$` were `CSI$ + "30;47m"`, 3 bytes under `BLACK$ + ON_WHITE$`.
            TED's `SELECTION_SGR$` is gone; it uses `CONS.REVERSE$`. The CONS row of PLAN's
            `DOS.UXI` table updated. `TED.COM` 10302 bytes, 23 more (the second `LOCATE`). `VIEW.COM` 6419.
            Build 1044 ms. VIEW ok 1.1 s. TED golden regenerated, diffed (only `F1 Help` moved
            after `CLEAR_EOL$`), ok 0.9 s. Goldens not committed.
         2. B, done 2026-10-18: tags in every UXCBASIC string literal, `"..."` and `!"..."`.
            `{NAME}` is Esc [ and the sequence, expanded by `lx_tag` in `pyuxc/uxc_lex.py` from
            the table `LX_TAGS`: `{CURSOR HOME}` `{CLS}` `{CLEAR EOL}` `{NORMAL}`
            `{REVERSE}`, `{BLACK}` to `{WHITE}`, `{ON BLACK}` to `{ON WHITE}`. No tags for the
            moves or bold, which the trim drops. Case is free; one space between words.
            Adjacent m tags join, up to 4 parameters: `{BLACK}{ON WHITE}` is `Esc[30;47m`.
            An escape does not join a tag. `{{` is `{`; a lone `}` stays; any other `{`, an
            unknown name or no `}` is `BAD TAG`. No source had a `{` in a string before.
            TED's `STATUS_COLORS$` and VIEW's `FOOTER_COLORS$` are now `"{BLACK}{ON WHITE}"`;
            `TED.COM` and `VIEW.COM` byte-identical. UXC-HELP: section Tags, and a bullet in
            String CONSTs. New tests `TAGS` (ok 0.6 s), `ERRTAG`, `ERRTAGOPEN` (ok 0.0 s).
            ESCAPES ok 0.5, ENUM 0.5, TED 0.9, VIEW 1.0, SHELL 0.5. Build 1570 ms, the new
            baseline. Before it, the user's rule: color, not colour. Renamed outside asm:
            `STATUS_COLORS$`, `FOOTER_COLORS$`, `DOS.SET_COLOR`, `DOS.GET_COLOR`, the comments,
            PLAN, API.md, api.py's prose, HELP.TXT, the ENUM test. Left for the trim step (asm):
            `con_colour`, `api_con_colour`, `API_CON_COLOUR` (api.inc and DOS.UXI),
            `CON_COLOUR`, `ansi_colours`, console.s comments, tests/ANSI.S. The user: no
            rename in the asm. Then `{CLEAR SCREEN}` became `{CLS}`; `CONS.CLEAR_SCREEN$`
            keeps its name. TAGS ok 0.6 s.
         3. Trim, done 2026-10-18: `ansi` in `src/asm/console.s` drops the moves `Esc[nA` to
            `D`, the `f` alias of `H`, and bold (`1m`, `ansi_bold`, `ansi_bright`); they do
            nothing now. `sgr` is inlined in the `m` loop; the locate loop holds the clamp,
            from the table `ansi_last` (`ROWS - 1`, `COLUMNS - 1`). Saved: CODE 86 bytes,
            RODATA 16, RAM 1, so 102 bytes of ROM. The erase handlers sit before `@digit`, or
            the branches from the dispatch run out of range. `CONS.UXI` drops `CURSOR_UP$`
            `CURSOR_DOWN$` `CURSOR_RIGHT$` `CURSOR_LEFT$` `BOLD$`; its checklist names
            `LX_TAGS`. console.s's header has a checklist. API.md (`con_out`, from api.py) and
            PLAN section 6 updated. `tests/ANSI.S`: A, C, `f` and `1m` checked as ignored;
            golden regenerated, each of the 14 results checked by hand, ok 0.4 s. TED ok 1.0,
            VIEW 0.9, SHELL 0.4. Build 1802 ms, the new baseline.
       - Del with a selection (2026-10-18): Delete takes out the selection and leaves the
         clipboard as it was. `REMOVE_PART(BEGIN, FINISH)` holds the take-out that Ctrl+X used;
         it counts the LFs itself when the cursor is at `FINISH`. TED.HLP's Del row says so.
         `TED.COM` 10519 bytes, 217 more. Build 931 ms, the new baseline. `tests/TED` cannot
         type Shift or Del; golden regenerated for the TED.HLP row only, ok 1.1 s.
       - Backspace with a selection (2026-10-18): Backspace takes out the selection through
         `REMOVE_PART`, the same as Delete. TED.HLP's Backspace row says so. `TED.COM` 10567
         bytes, 48 more. Build 885 ms, the new baseline. Golden regenerated for the TED.HLP
         row, ok 1.0 s.
       - One-call key read, the user's plan (2026-10-18), in steps:
         1. Done 2026-10-18: API 48 `con_getkey` (`api_con_getkey`, console.s, 19 bytes of
            CODE). Carry clear waits through `CHRIN`, so x16emu -bas still types; carry set
            returns at once. A = the character, 0 for an extended key or none; X = the scan
            code, 0 for a plain key or none; Y = `kbd_mods`. After `con_in`, X holds the old
            `con_scan` and `con_key` the scan code; `stz con_key` drops it. TED's 3 reads (the
            help screen, `ASK_QUIT`, the main loop) use it, with `DOS.REG_P = 0` first.
            `TED.COM` 10519 bytes, 48 less. Build 1771 ms, the new baseline (DOS.UXI changed,
            so every program recompiled). TED ok 1.1 s.
         2. Done 2026-10-18: built-ins `GETEXTKEY()` (at once) and `WAITKEY()` (waits, the
            cursor blinking), UWORD in A/Y: a plain key its character, an extended key
            scan * 256, no key 0; `KEYMODS()`, UBYTE, the Y of the last of the two. pyuxc
            `ex_key(template, type)` in `uxc_expr.py` serves all four key functions; the names
            are in `nm_q` (`uxc_name.py`) and `sg_scan_known` (`uxc_str.py`). Templates:
            `R_KEY` (14 B with its `mods` byte, once; `tpl/T-ARRAY.ASM`) took `T_GETKEY`'s id
            192, since a `#rec` target needs an id below 256 and 0-255 were full; `T_GETKEY`
            moved to 259, and `T_GETEXTKEY` 260 (4 B a call), `T_WAITKEY` 261 (4 B),
            `T_KEYMODS` 262 (3 B, `lda R_KEY.mods`) follow it in `UXC.TPL.ASM`. The stock
            table's `R_KEY` gives 0. `API_GETKEY = $03d0` in `tpl/UXDOS/API.ASM`. KEYS.UXI:
            new header, BINDs for the three, `KEY_name = SCAN_name * 256` for every SCAN_.
            UXC-HELP topic `GETEXTKEY, WAITKEY and KEYMODS`; the STOP key topic lists them.
            New tests `KEYEXT1` (no keys: 0, 0, 1) ok 0.8 s, `KEYEXT2` (types `aB`: 97, 0, 66,
            0, 13; the paste gives no Shift) ok 0.5 s; `GETKEY1` ok 0.5 s. Build 2319 ms, the
            new baseline.
         3. Done 2026-10-18, TED and VIEW in one step (the user's choice). TED: `KEY AS UWORD`
            from `WAITKEY()`, `MODIFIERS` from `KEYMODS()`; one `SELECT CASE KEY` with
            `KEYS.KEY_` names and the characters, Ctrl+Q a CASE of it, `CASE KEYS.SPACE TO 255`
            inserts; `ASK_QUIT` reads `ANSWER`, `SHOW_HELP` `KEY`, both with `WAITKEY()`.
            `CHARACTER` and `SCAN` are gone. VIEW: `DO KEY = GETEXTKEY() LOOP UNTIL KEY <> 0`
            (no blinking cursor, as before), Space becomes `KEYS.KEY_PGDN`, one `SELECT CASE
            KEY`. Cost: a CASE on a UWORD costs 7 B more than on a UBYTE (probe: 28 B against
            21). `TED.COM` 10748 bytes, 229 more; `VIEW.COM` 6544, 125 more. Build 2735 ms, the
            new baseline. Tests: `TED` ok 1.1 s, `VIEW` 0.9 s; neither types an extended key.
         4. Done 2026-10-18, KEYTEST. The loop polls `KEY = GETEXTKEY()` and
            `MODIFIERS = KEYMODS()`; `con_getkey` gives the modifiers with no key too, so the
            modifier lines still show as they change. `SCAN = KEY >> 8` for a key over 255;
            `KEY / 256` links the divide, 180 bytes more. `KEYTEST.COM` 2700 bytes, 3 more.
            `tests/FILES.OUT` holds the new size. Test: `FILES` ok 0.4 s. Build 718 ms, after
            the KEYTEST compile only.
         5. Done 2026-10-18, the compiler. `ex_power` in `uxc_expr.py`, called from
            `ex_binary`: an unsigned `/` by a constant power of 2 from 2 up becomes `>>`, and
            `MOD` becomes `AND` by the constant less 1. A signed side keeps the divide. Probe:
            `A = N / 256` 223 bytes against 403, `A = N MOD 256` 219 against 407. No program
            in `src/` divides by a power of 2, so the ROM is the same. New test `POW2`: UBYTE,
            UWORD and ULONG by 2 to 65536, the signed sides, and by 1 and 3. The help example
            of `GETEXTKEY` uses `K >> 8`; the costs list in UXC-HELP has the rule. Build 1835
            ms, all programs compiled, the new baseline. Tests: `FILES` ok 0.5 s, `POW2` 0.5,
            `FUNC1` 0.5, `SIGNSUB` 0.5, `TYPEDEF` 0.5, `SIGNED1` 0.5, `EXPR1` 0.5.
         ANSI stays: the goldens hold the byte stream, so the escapes are what the tests see of
         color, position and clear to end of line; no other API clears to end of line. The
         ANSI code costs about 335 bytes of ROM (ansi 211, sgr 90, tables 26, the hook in
         write) and 9 of RAM before the trim, 102 less after it.
   - `ERRORLEVEL`: a read-only number variable, the code from `exitcode` (API 27) after each
     child ends.
   - `EXIST(file)` in `IF`: 1 when the file opens.
   - `TRACE(n)`: 1 prints each script line before it runs, 0 stops.
   - `JUMP_FLOW` keeps the read-ahead when the target is in it, so a loop body under 255 bytes
     reads no file. Cost: 4 bytes of RAM (the buffer's file position) and a guess of 40 bytes
     of code. Measure the time a loop line takes first, to see whether it is worth it.
   - Open, the user to decide: a loop over file names. `REPEAT n` does not serve, since the
     count is not known first. Proposal: `FIND$(pattern)` gives the first name, `FIND$("")`
     the next, `""` at the end, in a loop of `IF` and `GOTO`.
- Idea, not yet in PLAN: tools in ROM banks 1 and up (an editor, the monitor, `DEBUG`,
  `FORMAT`, `CHKDSK`, the commandlets, `CMDSHELL`). It needs a ROM exec in bank 0 (a table of
  ROM program names; set up the PSP, select the bank, jump; a guess of 100 to 200 bytes) and
  IRQ and NMI vectors with a trampoline to bank 0 in every tool bank. A ROM tool uses
  `$0801–$9EFF` as a COM does. A tool in UXCBASIC waits for ROM-able output (PLAN section 12
  item 6). X16Edit calls the stock KERNAL and CBDOS, and is GPL v3.
- Shell memory, measured 2026-10-15 from pyuxc's link: code `$0801–$2BC2` (9154 bytes), the
  runtime `$2BC3–$3931` (3439), the strings `$3932–$3AA2` (369), the variables (47), then
  6953 bytes of arrays, strings and SUB locals outside the file. The shell ends at `$55FB`:
  19963 bytes of the 38655 in `$0801–$9EFF`, 18693 free (5 bytes more since `PSP_TOP`).
  `exec` saves the shell's pages to bank RAM, so a child gets all of `$0801–$9EFF` whatever
  the shell's size. The largest buffers: `COPY_BUFFER`
  1024, eleven `STRING * 128` of 129 bytes each, `STRING_RESULT` and `DOS.CALL_TEXT` 256 each.
3. The GPC compiler is frozen. pyuxc, a Python port in `UXCBASIC/pyuxc`, replaces it:
   its `README.md` has the plan, the port steps and the status. pyuxc matches the GPC output
   byte for byte on the corpus in `attic/gpc/pyuxc/golden/`. UXCBASIC's `tests.py` and `tools/uxb.py`
   here compile with it. The features below go into pyuxc next, and the compiler is rewritten
   in UXCBASIC (UXCBASIC PLAN §4 step 6). The UXC source uses these features that UXCBASIC
   lacks:
   - code in banked RAM, and calls from one bank to another;
   - data in banked RAM: `BANK n` with `PEEK` and `POKE` for the symbol table, the code buffer,
     the fixups and the templates;
   - string arrays: `NM.ALIAS.NAME$()`, `NM.ALIAS.TARGET$()`, `SG.CALLED$()`, `NS.L$()`,
     `AS.REFERENCE.NAME$()` and `AS.LABEL.NAME$()`.
