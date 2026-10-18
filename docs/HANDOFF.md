# Handoff

## State

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
    - The byte `boot_shell` (exported, `$C09C` now) is 1 in `build/UXDOS16.ROM`. `build.py`
      copies the ROM to `build/TEST.ROM` with `boot_shell` 0, found through the label file;
      `TEST.ROM` boots to the monitor. `tests.py` boots `TEST.ROM`, except for the tests in
      `SHELL_ROM_TESTS`, which boot `UXDOS16.ROM`. No golden file changed.
    - Trap: ca65 takes no string in an `=` constant; `SHELL_PATH` is a `.define`.
    - ROM +43 bytes: 26 of code, the flag, and the 16-byte path. `boot.o` CODE 173 bytes. ROM
      bank 0: 5536 bytes free below `$FFCF`. RAM: 0.
    - UXCBASIC's `tests.py` boots `UXDOS16.ROM`; its card has no `CMDSHELL.COM`, so it gets the
      monitor. UXCBASIC `ARRAY1` ok 0.5 s.
    - New test `SHBOOT`: `VER`, `END`, `VER`; the second `C>` is the shell run again. Build
      548 ms, the new baseline. `BOOT` ok 0.5 s, `SHBOOT` ok 0.4 s, `SHELL` ok 0.4 s.
    - Docs owed: PLAN section 11 step 8 and section 13 (boot).
  - Console colour (2026-10-17): call 46 `con_colour`, entry `$03CA`. Carry set returns the
    colour in A; carry clear sets it from A. High nibble background, low nibble foreground.
    `console.s` keeps it in zp `con_colour`; `con_init` sets it to `CON_COLOUR` ($05, green on
    black). `put` and `blank` write it, so FF and a scroll blank in the current colour.
    - `cursor_flip` swaps the nibbles of its cell's colour (asl, adc #$80, rol twice) instead
      of an eor with a fixed mask; `CURSOR_COLOUR` is gone. A cell whose nibbles match shows
      no cursor.
    - ROM +22 bytes; bank 0: 5514 bytes free below `$FFCF`. Zero page +1: `KERNELZP` ends at
      `$FB`, 4 bytes free.
    - Not tested on screen: the text tests do not see colour. No shell command uses the call
      yet; a shell `COLOR` is the next step.
    - Build 919 ms, the new baseline (`CMDSHELL.COM` recompiled, since `api.py` changed).
      `BOOT` ok 0.5 s, `SHELL` ok 0.4 s.
  - Colour names (2026-10-17): `DOS.UXI` has `API_CON_COLOUR` and the 16 palette names as
    CONSTs, `BLACK` 0 to `LIGHTGRAY` 15, as `DOS.BLUE` in UXCBASIC. The shell's numbers take
    the same names: `PRINT LIGHTGRAY * 16 + WHITE` prints 241. No `_` in the names, since
    `READ_NAME` does not take it.
    - `COLOR_NUMBER` in `CMDSHELL.UXB`: an `INSTR` in a 176-byte table, 11 characters a
      name, and the position less 1, divided by 11, is the value. EVAL_NUMBER calls it for a
      name that is not a variable; an unknown name is a syntax error. A colour name cannot be
      assigned (syntax error).
    - Trap: the table's order is the values' order in `DOS.UXI`; change both together.
    - `CMDSHELL.COM` 18672 bytes, +369. Tried: string `SELECT CASE` +624; a word-count
      function with the table as an argument +428 (a literal argument is copied, 112 more).
    - `SHELL` test gained 3 lines. Build 887 ms, the new baseline. `SHELL` ok 0.6 s, `SHIF`
      ok 0.4 s.
    - Docs owed: PLAN section 7 or the console bullets (the colour byte, the cursor rule);
      PLAN line 364 says the colour is fixed.
  - Shell `COLOR foreground,background` (2026-10-17): each 0 to 15, else syntax error; both
    are needed. `COLOR WHITE, BLUE`. It calls `DOS.SET_COLOUR(background * 16 + foreground)`.
    - `DOS.UXI`: `SUB SET_COLOUR(COLOUR)` (REG_P 0) and `FUNCT GET_COLOUR() AS UBYTE` (REG_P
      1). Neither touches ERROR. An uncalled one costs 0 bytes.
    - `EVAL_PAIR` reads `first,second` into the UWORDs `FIRST_NUMBER` and `SECOND_NUMBER`;
      LOCATE and COLOR share it, 48 bytes less than two copies.
    - `CMDSHELL.COM` 18854 bytes, +182. The `SHELL` test gained 4 lines (the colour itself is
      not seen by the text tests).
    - Build 965 ms, the new baseline. `SHELL` ok 0.6 s, `SHSCREEN` ok 0.6 s.
    - Docs owed: PLAN's shell statements list and `HELP.TXT` (COLOR, the colour names).
    - Full suite after it: 29 tests, 4 failed on golden churn only. The `DOS.UXI` change
      recompiled the test programs with pyuxc's dead-code pass (`uxc_dead.py`, 2026-10-16),
      1 to 1.6 KB smaller each: `CWD.COM` 2406, `DUP.COM` 3887, `SEEK.COM` 1948.
      Golden files changed: `FILES` (the sizes), `DIRS` FREE 6 more, `CMDLETS` 882 KB free,
      `DISK` F33 cluster `$46`. Each then ok one at a time: `FILES` 0.4 s, `DIRS` 0.7,
      `DISK` 0.4, `CMDLETS` 1.3.
  - Docs step after `COLOR` (2026-10-17); no docs are owed from the bullets above. PLAN §4: the
    `con_*` calls in the table. §6: the colour byte, the cursor rule. §8: the boot run, `COLOR`,
    the short names table, the colour names and the table trap, the `PROMPT$` codes, `HELP` as a
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
    then a byte other than `[` shows that byte. `Esc[0m` sets `con_default`, the colour
    `api_con_colour` last set (boot: `CON_COLOUR`), so a program's reset keeps the user's
    `COLOR`. Bold maps the foreground through `ansi_bright`, now and for each 3x after it, so
    `Esc[37;1m` and `Esc[1;37m` both give white. The ANSI colours are X16 palette entries 0, 2,
    5, 9, 6, 4, 3, 15 (brown for yellow, light grey for white); bright black is 11, red 10,
    green 13, yellow 7, blue 14, white 1; magenta and cyan stay 4 and 3. Not done: 7 reverse,
    `s` and `u` save and restore, `n` status report, `J` other than 2. The normal path costs
    `ldx ansi_state` and `bne`, 5 cycles a byte; Esc goes through `@glyph`. The ansi block sits
    after `vscroll`, reached by `jmp`, so `write`'s branches stay in range. Cost: CODE +305,
    RODATA +26, ZP +1 (`ansi_state`; KERNELZP now ends at $FD, 2 bytes left), KERNELRAM +7 (ends
    at $06B8). About 5080 bytes of ROM stay free. New test `ANSI` (`tests/ANSI.S`): 14
    sequences, the cursor and colour after each; the dump was checked by hand against the
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
  - VIEW step V3c (2026-10-17), the user's change: the highlight is the colours reversed. The
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
  - `src/asm/rom.cfg` links ROM bank 0, 16384 bytes, to `build/UXDOS16.ROM`.
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
    `NUL` reports ready; UXDOS16's gives 0 so that `EOF` is true at once.
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
- Step 6d is done: pyuxc has a UXDOS16 target (PLAN section 11, 6d).
  - The stock ROM is not supported (user, 2026-10-15). pyuxc compiles for UXDOS16 and has no
    `--target`. `compile_file`'s `target` is `"stock"` in UXCBASIC's `pyuxc/compare.py` only,
    against the GPC golden output, until the port ends.
  - UXCBASIC's `tests.py` runs on `build/UXDOS16.ROM` here: `TEST.COM` on a new SD card image,
    `RUN TEST.COM` typed at the monitor, the output up to the prompt. 155 tests ok, 36 s, the
    slowest 0.6 s. A tests run there needs the ROM built here first. Ten goldens changed: the line
    editor echoes typed keys, file output is no longer in the echo, `FILEBERR`'s error address.
    `FILEINERR` read handle 0, standard input here: its source moved to `pyuxc/cases`, and
    `FILEINCLOSED` reads handle 9. `compare.py` counts a source with no GPC golden as NO GOLDEN.
  - `UXCBASIC/tpl/MKTPL.PY` assembles `UXC.TPL.ASM` twice: `-D UXDOS=0` to
    `tpl/UXC.TPL.BIN`, `-D UXDOS=1` to `tpl/UXDOS/UXC.TPL.BIN`. The UXDOS16 table takes
    `tpl/UXDOS/SYS.ASM`, `tpl/UXDOS/R-FILE.ASM` and `tpl/UXDOS/API.ASM` (the call addresses).
    `R-PRINT.ASM` (`R_PRSTR`, `R_PRNL`) and `R-STRING.ASM` (`R_INPUT`'s CR echo) test `UXDOS`.
    Both tables have 251 records with the same ids; MKTPL stops when they differ. The stock
    table is byte for byte the one before; `compare.py`: 572 of 572 match.
  - On UXDOS16: `S_CHROUT` writes one byte to the output handle, `STDOUT` or the handle of
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
  it; the UXDOS16 table does not, so `$27` is free there. `MKTPL.PY` 0.28 s; both tables are byte
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
- Full suite (2026-10-15), after the `END` range step: UXDOS16 15 ok, 8.1 s, slowest `ASK`
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
- Steps since the last full suite: 5 (break steps B1, B2, B3, B4, B5). It ran after library refactor step 8b
  (generated `ERR_` and `FIND_`), 2026-10-18: 34 tests, 0 failed, 19.5 s, the longest
  `CMDLETS` 1.6 s.
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
    UXDOS16 target only, with S0 = the BSS end (`lk_bss + bs_n`): its high byte is the page
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
  to the end. A statement after `IF c THEN` does not count. The UXDOS16 table only, so
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
- In a window: `C:\8bitProgramming\x16emu\x16emu.exe -rom build\UXDOS16.ROM -sdcard build\SD.IMG`,
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
   after 7h are done. `DATE` and `TIME` wait for a clock call. 7i1 (`EXIST`), 7i2 (`DISKFREE`) and
   7i3 (`DISKINFO`) are done, and the docs step after them (PLAN section 8: `CBIN.UXI`,
   `DISKFREE`, `DISKINFO`). 7i4 (`WHICH`) is put off by the user (2026-10-16). 7i5
   (`HELP`), `PROMPT$` codes, short names, the boot shell, console colour and `COLOR` are done,
   and the docs step after them, the 4 MB card, extended keys, ANSI output and Alt and Ctrl
   keys. Next, agreed with the user on 2026-10-17:
   - UXCBASIC, in `UXCBASIC.PLAN.md` first, then pyuxc: `GETKEY()` stays a UBYTE; on an
     extended key `S_GETIN` reads both bytes, returns 0 and keeps the scan code. `SCANKEY()`
     gives that scan code, 0 after a plain key or no key. `KEYMODS()` gives the modifiers held
     now: 1 Shift, 4 Caps Lock, 64 Alt, 128 Ctrl. The `GETKEY` help says PETSCII; fix it to
     the UXDOS16 codes.
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
        - PLAN section 2: `KEYS.UXI` and `CONS.UXI`. Section 6: ANSI, the ANSI colours,
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
     every `.UXI` library lives in UXDOS16. The repos stay apart. Each file holds one
     namespace of the same name. BINDs that rename built-ins stay and grow: the coming editor
     lists a namespace's members after `STR.`, so every built-in of a kind gets a BIND in its
     namespace. Constants and BINDs cost 0 bytes; dead-code stripping drops uncalled FUNCTIONs.
     `VIEW.COM` (6422 bytes) checks that. No asm. Steps, one at a time:
     1. A new `lib/` folder in UXDOS16. Move `DOS.UXI`, `HEAP.UXI`, `CONS.UXI` and `KEYS.UXI`
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
        Step 6 done in UXDOS16: `DOS.UXI` ends with a section of whole-file routines built on
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
        UXC-HELP topic at about line 405 points to the UXDOS16 library.
        Step 7 done: `lib/` is gone. `STRINGS.UXI` is `tests/STRINGS.UXI`. `lib/CONSOLE.UXI`,
        which no source included, is deleted. `tests.py`, `pyuxc/compare.py` and
        `pyuxc/golden.py` no longer search `lib/`. `build.py` no longer copies `lib/` onto
        `disk/`. The Strings topic of UXC-HELP says `STR.UXI` in the UXDOS16 library binds the
        built-ins in `NAMESPACE STR`; `MKHELP.PY` rebuilt the pages, 0.17 s. `disk/CONSOLE.UXI`,
        `disk/STRINGS.UXI` and `disk/STRINGS2.UXI` stay; `disk/STR-TEST.UXB` includes
        `STRINGS2.UXI`. No asm, no UXDOS16 build. Tests in UXCBASIC: `STRLR` ok 0.7 s, `STRNS`
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
        - Stale, not yet fixed, for the next docs batch: UXC-HELP's "Compiling from UXCEDIT"
          topic and line 7 (the GPC UXC), "Including files" (pyuxc searches the source's
          folder, then each `-I` folder), "Files" (drive 8, KERNAL CHRIN, READST, CHROUT), the
          GETKEY topic's "PETSCII code". `UXCBASIC.PLAN.md` section 3 names the GPC layout
          (`src/UXC.BASL`, `uxc.py`, `RUNTESTS.BAT`, `run.py`).
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
     0.4. Docs owed: PLAN section 8, the prompt starts in column 0.
   - Bug, to do (the user, 2026-10-18): `VIEW.COM` must eat the keyboard queue between Up and
     Down arrow moves.
   - To do: 7i4, renamed `WHERE` (the user, 2026-10-17). It is still put off.
   - To do, commands the user listed (2026-10-17). None is in PLAN section 11 yet; each needs a
     step and a talk with the user first.
     - Search and text: `FIND` (text in files), `SORT`, `GREP` (the feature set is to be talked
       over with the user), `HEAD` (first n lines), `TAIL` (last n lines), `WC` (line, word
       and byte counts). `FC` (text compare) and `COMP` (binary compare) are for version 2.0.
     - Files: `XCOPY` (directory trees), `MOVE`, `MORE` (paged display), `ATTRIB`, `TREE`. The
       shell already has `COPY`, `RENAME` or `REN`, and `DELETE` or `DEL`.
     - System: `TIME`, `DATE`, `UPTIME`.
     - Paths: `PUSH` saves the current path, and `POP` loads it back (the user, 2026-10-17).
     - The API calls `attrib` (8), `filetime` (9) and `getdate` to `settime` (33 to 36) go to
       `api_bad`: `ATTRIB`, `TIME` and `DATE` need asm first.
   - `HELP.TXT`: the user marks each topic as for scripts, the command line, or both
     (2026-10-17).
   - Done: `PROMPT$` `$` codes (see State). No `$T`, `$D`, `$V`, `$H` or `$E`. `HELP.TXT` has
     no `PROMPT$` topic.
   - Long file names are needed (the user, 2026-10-16). Talk the design over with the user
     before a step goes into PLAN section 11. PLAN section 5 has the target: 32 characters a
     name, 255 a path.
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
       - Next: the docs batch owed for break (above), then the VIEW.COM key bug.
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
