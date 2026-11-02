# DB plan: tables and indexes

This plan adds a database to 6502DOS: a library in ROM that reads and writes tables and their
indexes, and a program with a dot prompt and command files that uses it. The design follows
dBASE II, which ran in 64 KB. The files are 6502DOS's own. No other program reads or writes
them, and no dBASE file is read. Each step is one part, built and tested on its own. Sizes are
estimates until the step is built.

## What is taken from dBASE II

| dBASE II | 6502DOS DB |
|---|---|
| A table: a header, a field table, fixed-width records | the same, with its own header |
| Field types C, N, L | C, N, L, and D, a date |
| A record is ASCII, with a delete flag in its first byte | the same |
| DELETE marks a record, PACK removes the marked ones | the same |
| An index is a B-tree in 512-byte pages | the same, with its own page layout |
| An index key is an expression, stored as text | a key is one to four fields, joined |
| A write to the table updates its open indexes | the same |
| Two work areas, PRIMARY and SECONDARY | the same |
| 64 memory variables, numbers in BCD | 64 memory variables, numbers in MSBASIC's 5-byte float |
| The dot prompt and `.PRG` command files | the same, in the program `XBASE.COM` |
| Overlays swapped from the disk | none: the code is in ROM banks |

## The table file

A table is a file with the extension `.DB`. All numbers in it are little-endian.

### The header, 16 bytes

| Offset | Bytes | Value |
|---|---|---|
| 0 | 2 | `DB`, the magic |
| 2 | 1 | the version, 1 |
| 3 | 1 | the number of fields, 1 to 32 |
| 4 | 2 | the number of records, 0 to 65535 |
| 6 | 2 | the header's length: the offset of the first record |
| 8 | 2 | the record's length, the delete flag included, 2 to 1000 |
| 10 | 3 | the date of the last write: the year less 2000, the month, the day |
| 13 | 3 | 0 |

### The field table

One 16-byte entry a field follows the header, then the byte `$0D`. The header's length is
16 + 16 × fields + 1: 529 bytes for 32 fields.

| Offset | Bytes | Value |
|---|---|---|
| 0 | 11 | the name: 1 to 10 characters, `A` to `Z`, `0` to `9` and `_`, upper case, the rest 0 |
| 11 | 1 | the type: `C`, `N`, `L` or `D` |
| 12 | 1 | the length |
| 13 | 1 | the decimals, for `N`; else 0 |
| 14 | 2 | the field's offset in the record |

### The record

Byte 0 is the delete flag: a space, or `*` for a deleted record. The fields follow in the
order of the field table, with no separators. Record n, counting from 1, starts at
header length + (n − 1) × record length.

| Type | Length | Text |
|---|---|---|
| `C` | 1 to 255 | left-aligned, padded with spaces |
| `N` | 1 to 10 | right-aligned, padded with spaces, a `-` before the digits, a `.` before the decimals |
| `L` | 1 | `T`, `F`, or `?` for not set |
| `D` | 8 | `YYYYMMDD`, or 8 spaces for no date |

A table holds at most 65535 records of 1000 bytes: 65,535,000 bytes, which `seek`'s 32-bit
offset reaches.

## The index file

An index is a file with the extension `.NDX`, of 512-byte pages. Page n starts at offset
512 × n. Page 0 is the index's header, and pages 1 and up are B-tree nodes.

### Page 0

| Offset | Bytes | Value |
|---|---|---|
| 0 | 2 | `IX`, the magic |
| 2 | 1 | the version, 1 |
| 3 | 1 | the key's length, 1 to 100 |
| 4 | 2 | the root's page number |
| 6 | 2 | the number of pages, page 0 included |
| 8 | 2 | the first free page, 0 for none |
| 10 | 1 | the number of key fields, 1 to 4 |
| 11 | 4 | the key fields' numbers, counting from 1, the rest 0 |
| 15 | 1 | flags: $01 the keys are unique |
| 16 | 496 | 0 |

### A node page

| Offset | Bytes | Value |
|---|---|---|
| 0 | 1 | the number of keys in the page |
| 1 | 1 | flags: $01 a leaf |
| 2 | 2 | the page of the keys below the first key; 0 in a leaf |
| 4 | | the entries, each the key, then the record number, 2 bytes, then the page of the keys above it, 2 bytes, 0 in a leaf |

A page holds (512 − 4) / (key length + 4) entries: 4 for a key of 100 bytes, 36 for a key
of 10. A freed page holds the next free page at offset 0 to 1.

An empty index has one page, page 1, an empty leaf. A page that overflows holds its entries
and the new one, n in all. It keeps the first n / 2, rounded down, sends entry n / 2 up to its
parent, and moves the rest to a new page. A new page is the first free page, else the page
after the last. A root that splits gets a new root above it.

The tree is at most 10 levels deep. 65535 keys of 100 bytes reach 10 levels when they are added
in order, and 9 in random order.

### The key

The key is the key fields' text from the record, joined in order, with no separators, cut to
100 bytes. Keys compare byte by byte. Equal keys keep the order of their record numbers.

An `N` field enters the key rewritten, so that it sorts as a number. A space and the `.` count
as `0`, so a blank field sorts as 0.

- A number of 0 or more: each space and the `.` become `0`. 12.50 in a field of 8 becomes
  `00012050`.
- A negative number: `-` in the first byte, then the field's other bytes in order, each digit
  d written as 9 − d. −12.50 in a field of 8 becomes `-9987949`.

A field's text is never `-0`: 0 is written without its sign.

A key passed to `ix_find` is in the same form.

## The library

The library is asm in ROM bank 5. It keeps a table and its indexes in step, and it holds
every field as text. It does no arithmetic on a field.

### The call

A program reaches the library through one new call in the jump table:

| Call | Number | Entry | In | Out |
|---|---|---|---|---|
| `db` | 57 | `$03EB` | `Y` function<br>`A` the table's RAM bank<br>`X`, `r0` to `r3` by function | by function; carry set and `A` the error on an error |

### The functions

| Y | Function | In | Out |
|---|---|---|---|
| 0 | `db_create` | `r0` path<br>`r1` field table, 16 bytes a field<br>`X` fields | none; the table is open, with no records |
| 1 | `db_open` | `r0` path | `r0` records<br>`X` fields |
| 2 | `db_close` | none | none |
| 3 | `db_info` | `X` field, 0 for the table | `r0` the field's 16-byte entry, or the table's 16-byte header |
| 4 | `db_goto` | `r0` record | `X` the delete flag |
| 5 | `db_get` | `X` field<br>`r0` buffer | the buffer, filled with the length-prefixed text |
| 6 | `db_put` | `X` field<br>`r0` length-prefixed text | none |
| 7 | `db_append` | none | `r0` the new record, blank and current |
| 8 | `db_write` | none | none |
| 9 | `db_flag` | `X` 0 recall, 1 delete | none |
| 10 | `db_pack` | none | `r0` records |
| 11 | `ix_create` | `r0` path<br>`r1` key fields, 4 bytes<br>`X` flags | none; the index is built from the table and opened |
| 12 | `ix_open` | `r0` path | `X` the index's slot, 0 to 2 |
| 13 | `ix_close` | `X` slot | none |
| 14 | `ix_order` | `X` slot, $FF for record order | none |
| 15 | `ix_find` | `r0` length-prefixed key | the first record whose key starts with it, or is above it, is current; carry clear when it starts with it |
| 16 | `ix_first` | none | `r0` record, 0 when the index is empty |
| 17 | `ix_last` | none | `r0` record, 0 when the index is empty |
| 18 | `ix_next` | none | `r0` record, 0 at the end |
| 19 | `ix_prev` | none | `r0` record, 0 at the start |
| 20 | `ix_place` | none | none; the place in the order's index is at the current record, for `ix_next` and `ix_prev`. Nothing in the record order |

`db_write` writes the current record, and updates each open index whose key changed.
`db_append` does not write: the first `db_write` adds the record. `db_pack` copies the table
without its deleted records to a new file, then renames it over the old, and rebuilds the open
indexes.

### The workspace

A program takes one RAM bank from `bank_alloc` for each open table and passes it in `A`. The
library keeps the table's state there:

| Use | Where | Bytes |
|---|---|---|
| the state: the handles, the current record, the order, the work bytes | `$A000` | 32 |
| the header and the field table | `$A020` | 529 |
| the current record, `DB_RECORD` | `$A231` | 1000 |
| the record as the file holds it, `DB_OLD`, for the keys that change | `$A619` | 1000 |
| the delete's empty page and its page below | `$AA01` | 4 |
| 3 index slots: page 0's first 16 bytes, the handle, the key width, the keys a page holds, the work flag | `$AA20` | 3 × 32 |
| the path from the root, 10 levels of a page and an entry, 3 bytes each, and the key's length | `$AA80` | 31 |
| the entry to insert: the key, the record, the page above | `$AAA0` | 104 |
| the page read, and an entry past it in a split | `$AC00` | 512 |
| the page built | `$AF00` | 512 |
| the indexes' paths, length-prefixed | `$B100` | 3 × 256 |
| the table's path, length-prefixed | `$BE00` | 256 |
| `pack`'s new file: the path with its last character changed | `$BF00` | 256 |

- Trap: the library runs with the table's RAM bank selected. A buffer the program passes in
  `r0` or `r1` lies in `$0400–$9EFF`, never in `$A000–$BFFF`.
- Trap: a table and each of its indexes take one entry each in the system file table, which
  has 16, entry 0 `CON`.
- The library reads and writes through `read`, `write` and `seek`, which keep the caller's RAM
  bank.

### Sizes

| Part | Bytes |
|---|---|
| The library, `src/asm/db.s` | 4342 |
| MSBASIC's float, `src/asm/fp.s`, call 58 | 2258 |
| total, `$C000–$D9C7` | 6600 |

ROM bank 5 has 16,384 bytes. `$D9C8–$FF9F`, 9,688 bytes, are free.

## The program, XBASE.COM

`XBASE.COM` is a stub that starts the program in ROM banks 6 to 8, as `ROMSHELL.COM` starts the
shell. The program is UXCBASIC, `src/bank6/XBASE.UXB` and the files it includes: `DB_EXPR.UXI`,
`DB_FUNC.UXI`, `DB_MEM.UXI`, `DB_SCOPE.UXI`, `DB_CHANGE.UXI`, `DB_INDEX.UXI`, `DB_DO.UXI`,
`DB_SCREEN.UXI`, `DB_BROWSE.UXI` and `DB_LINE.UXI`. It is compiled with `#ROMBANKS 6, 7, 8`. It calls the library through
`lib/DB.UXI` and the float through `lib/FLOAT.UXI`.

`XBASE` with no command file clears the screen and prints `C:\sys\xbase\splash.dot`, CP437 text,
before the dot prompt. Without the file it does neither.

`DB name` runs the command file `name`, as `DO name` does, then gives the dot prompt. A `QUIT`
in the file ends DB.

Ctrl+C does not end `XBASE.COM`. It is key code 3 in the program. A typed line and a GET drop it.
`WAIT` takes it as a key, and `LASTKEY()` gives 3. A command file that loops on a key cannot be ended
with Ctrl+C. A cmdlet or other program that `XBASE.COM` runs starts with Ctrl+C ending it, and the
mode comes back when it ends.

### The commands

A command word may be cut to its first 4 letters, as `DISP STRU`.

| Group | Commands |
|---|---|
| Tables | `USE`, `CLOSE`, `CREATE`, `COPY TO`, `DISPLAY STRUCTURE` |
| Work areas | `SELECT PRIMARY`, `SELECT SECONDARY`, `PUSH`, `POP` |
| Moving | `GO`, `GOTO`, `GO TOP`, `GO BOTTOM`, `SKIP`, `LOCATE`, `CONTINUE`, `FIND` |
| Showing | `LIST`, `DISPLAY`, `BROWSE`, `?`, `COUNT`, `SUM` |
| Changing | `APPEND`, `APPEND BLANK`, `EDIT`, `REPLACE ... WITH`, `DELETE`, `RECALL`, `PACK`, `ZAP` |
| Indexes | `INDEX ON ... TO`, `SET INDEX TO`, `USE ... INDEX`, `FIND`, `REINDEX` |
| Variables | `STORE ... TO`, `name = expression`, `RELEASE`, `DISPLAY MEMORY`, `REG ... TO` |
| Screens | `@ ... SAY`, `@ ... GET`, `READ`, `CLEAR`, `CLEAR GETS`, `CLS`, `@ ... TO`, `BOX`, `SET REVERSE` |
| Menus | `@ ... PROMPT`, `MENU TO`, the function `MENU()` |
| Screen files | `SAVE SCREEN TO`, `RESTORE SCREEN FROM` |
| Command files | `DO`, `IF`, `ELSE`, `ENDIF`, `DO WHILE`, `ENDDO`, `PROC`, `ENDPROC`, `GOSUB`, `ON KEY`, `RETURN`, `CANCEL`, `ACCEPT`, `INPUT`, `WAIT`, `MODIFY COMMAND`, `QUIT` |
| Settings | `SET INDEX TO`, `SET PATH TO`, `SET FILTER TO`, `SET VALID TO`, `SET DELETED`, `SET FIELDS TO`, `SET REVERSE` |
| Other programs | `HELP`, `!`, `RUN`, `SHELL` |

#### Scopes

`LIST`, `DISPLAY`, `COUNT`, `SUM`, `LOCATE`, `REPLACE`, `DELETE` and `RECALL` take a scope
(`ALL`, `NEXT n`, `RECORD n`) and a `FOR` condition, in any order. With no scope, `FOR` means
all the records. The scope of `DISPLAY`, `REPLACE`, `DELETE` and `RECALL` is the current
record; that of `LIST`, `COUNT`, `SUM` and `LOCATE` is every record. `ALL` and `NEXT n` follow
the order.

- `COUNT scope TO name` prints `n records`. `SUM list scope TO names` sums at most 8 number
  expressions, prints `n records summed`, then each sum on a line. `TO` stores the results in
  memory variables.
- `LOCATE scope` makes the first record that meets the condition current and prints
  `Record n`, else `End of LOCATE`. `CONTINUE` looks on from the record after the current
  one in the order. With no `LOCATE` since the start, the last `USE`, `CREATE`, `SELECT` or
  `POP`, `CONTINUE` prints `No LOCATE active`.
- `DELETE scope` and `RECALL scope` mark or clear each record and print `n records deleted`
  or `n records recalled`.
- `NEXT n` that runs off the end leaves the place past the last record.

#### Tables

- `USE path` closes the table in use, then opens `path`, with `.DB` added when it has no
  extension. `USE` alone only closes. `USE path INDEX names` opens the indexes too, as
  `SET INDEX TO`. Another word after the path is `Syntax error`, and no table is in use.
- `CLOSE` closes the table in use and its indexes, as `USE` alone does. The other area's table
  stays open. The filter and the `SET FIELDS TO` list are cleared, and the `LOCATE` ends. Words
  after it are ignored.
- `CREATE path` prints `Name,type,length,decimals`, then asks `Field  n: ` for each field, one
  a line, as `NAME,C,20`, `BAL,N,8,2`, `MEMBER,L` or `JOINED,D`, spaces allowed, in either
  case.
  - A name is 1 to 10 letters, digits and `_`, from a letter. The type is `C`, `N`, `L` or
    `D`. A `C` field takes a length of 1 to 255. An `N` field takes a length of 1 to 10, then
    decimals, 0 when left out, at most the length less 2. `L` has length 1, `D` length 8.
  - A wrong line prints `Syntax error`, `Number out of range` or `Duplicate field`, and is
    asked again. An empty line ends the fields, at most 32.
  - With no fields no table is made, and the table in use stays. Else the table in use
    closes, and the new one is in use with no records. A file of that path is emptied.
  - A failed create leaves no table in use. A record past 1000 bytes gives `Invalid data`.
- `COPY TO path` makes the table `path`, with `.DB` added when it has no extension, with the
  fields of the table in use. It copies the records that are not deleted and meet the filter,
  in the order, and prints `n records copied`. The place past the last record is then
  current. A file of that path is emptied. The path of either area's table prints
  `Table in use`.
  - Trap: another path to the table in use, such as `.\CLUB.DB` for `CLUB.DB`, empties it.
- `PACK` removes the deleted records, prints `n records left`, and makes the first record of
  the order current. A failed `PACK` leaves no table in use.
- `ZAP` marks every record deleted, then packs. It asks nothing and prints `0 records left`.
  The open indexes are rebuilt.

#### Changing records

- `REPLACE scope field WITH expression, ... scope` sets at most 8 fields, left to right, in
  each record, and prints `n records replaced`. The scope goes before the fields, after them,
  or both. An N field takes a number at the field's decimals; a number longer than the field
  is `Number out of range`. An L field takes a logical. A C or D field takes text, cut to the
  field's length.
- `APPEND BLANK` adds a blank record. `APPEND` prints `Record n`, then asks for each field by
  name. An empty answer to the first field ends `APPEND`, and that record is not added. An
  empty answer to another field leaves it blank. An N field takes a number expression; an L
  field `T`, `Y`, `F` or `N`; a C or D field the answer, cut to its length. A wrong answer
  prints its error, and the field is asked again. The last record added is current.
- `EDIT` prints `Record n`, then for each field of the current record its name, padded to 10,
  `: `, the field's text and ` ? `. An empty answer keeps the value; another is read as
  `APPEND` reads it. Then the record is written. `EDIT word` is `Syntax error`. Past the last
  record, or with no records, `EDIT` prints `Record out of range`.

#### Indexes and the order

- `INDEX ON key TO name [UNIQUE]` builds the index `name`, with `.NDX` added when it has no
  extension, and prints `n records indexed`. The key is 1 to 4 field names joined by `+`,
  spaces allowed. The open indexes close first; the new index is the only one open, and the
  order. `UNIQUE` refuses two records with one key. A bad key field, or a key not unique,
  gives `Invalid data`, and the indexes stay closed.
- `SET INDEX TO a, b, c` closes the open indexes and opens the names, with `.NDX` added when
  one has no extension. The first is the order. `SET INDEX TO` alone leaves the record order.
- `INDEX ON`, `SET INDEX TO` and `USE ... INDEX` make the first record of the order current.
- `GO TOP` and `GO BOTTOM` are the first and last records of the order. `GO n` is record n.
  `SKIP n` moves n records along the order, back when n is negative. A move goes on in the
  order from a record reached by `GO n`.
- `FIND key` makes current the first record of the order whose key starts with `key`, the rest
  of the line, with matching `"` or `'` quotes taken off. It prints nothing. With no such
  record it prints `No find`, and the place past the last is current. In the record order, or
  with a key longer than the index's, it gives `Invalid data`. `FIND` alone is
  `Syntax error`. An N field is in the key rewritten (The key, above).
- `REINDEX` builds each open index again from the table and prints `n records indexed` for
  each. The first index is then the order, and its first record current. A failed build prints
  its error and closes the indexes.

#### Work areas

- `SELECT PRIMARY` and `SELECT SECONDARY` make that area the one in use. Each area keeps its
  table, its indexes, its current record and its filter. Another word after them is
  `Syntax error`.
- `P.name` and `S.name` in an expression are a field of the PRIMARY or SECONDARY area's table.
  When that area has no table or no such field, `P` or `S` is a memory variable and `.` an
  operator, so `P.AND..T.` works with a variable `P`.
- `PUSH` saves the area in use, its current record, and whether `SKIP` stopped before the
  first record. It holds 4 levels; a 5th prints `Stack full`. `POP` selects the area of the
  last level, makes its record current when a table is in use, and drops the level. With no
  level it prints `Stack empty`. A record past the last of the table now in use is past the
  last. The table, the filter and the indexes are not saved. A word after `PUSH` or `POP` is
  `Syntax error`.
- `QUIT` closes the tables of both areas.

#### Settings

- `SET PATH TO dirs` keeps a list of directories, apart by `;`, at most 80 characters. A name
  with no `:` or `\` that is not in the current directory is looked for in each directory in
  turn. `USE`, the index names of `USE` and `SET INDEX TO`, `DO` and `DB name` search it.
  `SET PATH TO` alone clears it.
- `SET FILTER TO condition` takes a logical condition: another type is `Type mismatch`, more
  after it `Syntax error`. `GO TOP`, `GO BOTTOM`, `SKIP`, the scopes and `COPY TO` pass over the
  records that do not meet it. `GO n` and the first record of `RECORD n` and `NEXT n` are not
  checked. The current record stays. Each area keeps its own filter. `SET FILTER TO` alone
  clears it, and `USE` and `CREATE` clear it.
- `SET VALID TO condition` takes a logical condition, at most 240 characters, and is checked as
  `SET FILTER TO` is. `BROWSE` and `READ` check it after the GETs are stored and before the record
  is written. A false condition beeps, the record is not written, and it is read again. `READ` then
  prints `Invalid value`. `REPLACE` and `APPEND` do not check it. Each area keeps its own condition,
  and the `.DB` file does not hold it. `SET VALID TO` alone clears it, and `USE` and `CREATE` clear
  it.
- `SET DELETED ON` makes `GO TOP`, `GO BOTTOM`, `SKIP`, the scopes and `BROWSE` pass over deleted
  records, in both areas and across `USE`. `GO n`, `RECORD n` and `FIND` do not check it. `SET
  DELETED OFF`, the default, ends it.
- `SET FIELDS TO list` adds to the fields `BROWSE` alone shows, at most 32 an area, not checked. The
  list is a field list, in the section BROWSE. A bad name adds none, and gives `Field not found`.
  `SET FIELDS TO` alone clears them, and `USE`, `CREATE` and `CLOSE` clear them.
- `SET REVERSE ON` prints `ESC[7m`, and what prints after it shows in reverse video.
  `SET REVERSE OFF` prints `ESC[0m`, the default colors. `SET REV` is the same command.

#### Variables and the registry

- `REG key TO expression` sets `key` in `C:\6502DOS.REG` to the text value. `""` removes the
  key. A value that is not text is `Type mismatch`.
- The function `REG(key)` gives the value of `key`, `""` when it is missing.

#### Command files

- `DO name` runs `name`, with `.PRG` added when it has no extension, a line at a time, as if
  typed at the prompt, with no echo. `DO` alone is `Syntax error`; a missing file prints its
  DOS error. Each file stays open while it runs. Files nest 8 deep; a 9th prints
  `Too many DO levels`.
- `RETURN` ends the innermost file, and its caller goes on. The end of a file does the same.
  `RETURN` in a `PROC` goes back after its `GOSUB`. `CANCEL` ends every file, and so does `QUIT`. At
  the prompt `RETURN` does nothing.
- A line ends in LF; a CR is dropped. A last line with no LF runs. A line is cut at 240
  characters. A command file is under 64 KB.
- A tab reads as a space, in quoted text too.
- A line that starts with `*` or `//` is a comment, in a file and at the prompt.
- A line that ends in a space and `_` joins the next. The `_` goes, the space stays, and the next
  line loses its leading spaces. Joined lines count together toward the 240 characters and toward
  the 256 bytes of a `DO WHILE` line. An error names the last line joined. A comment joins too. The
  prompt has no joining.
- An error in a file prints `Line n: text` and ends every file. A read error prints its error
  and ends every file.
- `IF condition`, `ELSE`, `ENDIF`: when the condition is false, the lines up to the `ELSE` or
  `ENDIF` of this `IF` are skipped. An `ELSE` run skips up to its `ENDIF`. `IF`s nest. An `IF`
  has at most one `ELSE`. The condition is logical, else `Type mismatch`; more after it is
  `Syntax error`.
- `DO WHILE condition` and `ENDDO`: when the condition is true, the lines up to its `ENDDO`
  run, and `ENDDO` goes back to the `DO WHILE`. When false, they are skipped. Loops and `GOSUB`s
  nest 8 deep together in all the files; a 9th prints `Too many DO levels`. A `DO WHILE` line is
  under 256 bytes. `RETURN` inside a loop ends the file, or goes back after the `GOSUB` of a `PROC`.
  `ENDDO` with no loop running does nothing.
- `PROC name` and `ENDPROC` hold lines that run only by `GOSUB name`. A `PROC` line that runs skips
  to its `ENDPROC`. A `PROC` is not inside an `IF`, a `DO WHILE` or a `PROC`, not checked. It has no
  parameters or locals.
- `GOSUB name` runs the first `PROC name` of the file running, then goes on at the next line. The
  search reads the file from its first line. A name not found prints `Proc not found: NAME` and ends
  every file.
- `ENDPROC`, and `RETURN` in a `PROC`, go back after the `GOSUB` and end the `DO WHILE`s since it. An
  `ENDPROC` with no `GOSUB` ends the file.
- `ON KEY Fn GOSUB name` binds F1 to F10 in a `BROWSE` to `PROC name` of the file running the
  `BROWSE`. A name is at most 10 characters, not checked. `ON KEY Fn` alone drops the key, and the
  last file's end drops every key. A bound key's line, the `BROWSE`, is under 256 bytes, joined lines
  counted together.
- At the prompt `IF`, `DO WHILE`, `PROC`, `GOSUB` and `ON` print `Only in a command file`. `ELSE`,
  `ENDIF`, `ENDDO` and `ENDPROC` there do nothing.
- `ACCEPT [prompt] TO name` stores the line typed as text. `INPUT [prompt] TO name` stores the
  value of the expression typed; one that does not evaluate prints its error and is not asked
  again. The prompt is a text expression, else `Type mismatch`.
- `WAIT [TO name]` prints `WAITING ` and waits for a key. `TO` stores the key as a text of 1
  character, `""` for an extended key.
- `MODIFY COMMAND name` runs `C:\sys\EDIT.COM` on `name`, with `.PRG` added when it has no
  extension, then gives the dot prompt. The tables, indexes and command files stay open, and
  each takes one of the files the editor could open.

#### Screens

- `@ row, column [SAY expression]` puts the cursor at row and column, from 0, each 0 to 255,
  and prints the value with no line end. With no `SAY` and no `GET` it blanks the row from the
  column to its end. The line is checked whole before the cursor moves. `@` and `?` need no
  space after them.
- `CLEAR` blanks the screen, puts the cursor at row 0, column 0, and drops the pending GETs.
  `CLEAR GETS` only drops them. `CLS` blanks the screen and keeps them. `CLEAR` and `CLS` drop
  the prompts of `MENU TO`. A word after `CLEAR` or `CLS` is `Syntax error`.
- `BOX row, column, width, height [DOUBLE]` draws a box of single lines, or double, its top
  left corner at row and column. `@ row, column TO row, column [DOUBLE]` draws one from the
  first corner to the second, the bottom right. The inside is cleared to spaces, and the box
  takes the current console color. Width and height are at least 2; that is not checked.
  - Trap: a box that ends in the screen's last column moves the cursor to the next line, and
    on the last row that scrolls the screen.

#### GET and READ

- `@ row, column [SAY expression] GET name [PICTURE text]` adds a pending GET and shows it at
  once: after the `SAY` value and a space, or at row and column.
  - `name` is a field of the current record, past the last `Record out of range`. Else it is a
    memory variable that exists, else `Variable not found`.
  - The width is the picture's length. Without a picture it is the field's length, a text
    variable's length, 10 or more for a number variable, or 1 for a logical.
  - Without a picture the mask is all `#` for a number, `L` for a logical, `99999999` for a
    `D` field, else all `X`. A number is right-aligned, other values left-aligned, cut to the
    width. A GET must fit on its row.
- `PICTURE` takes a text expression, a mask of one character a place:

| Character | Takes |
|---|---|
| `9` | a digit |
| `#` | a digit, a space, a sign or a point |
| `A` | a letter |
| `L` | `T`, `F`, `Y` or `N`, made upper case |
| `X` | any character |
| `!` | any character, a letter made upper case |
| any other | nothing: it is fixed, and the cursor skips it |

- At most 32 GETs are pending, in a 2048-byte pool; a GET of width w takes 2 × w + 4 bytes.
  Past either limit: `Too many GETs`.
- `READ` edits the GETs in turn, from the first. In a GET a typed character types over the one
  at the cursor when the mask takes it. Delete puts a space; Backspace moves left and puts a
  space. Left, Right, Home and End move.

| Key | In `READ` |
|---|---|
| Enter, Tab, Down | the next GET |
| Up | the GET before |
| Enter, Tab or Down at the last GET, PgDn, Ctrl+W | end, and store every GET |
| Esc | end, and store none |
| Ctrl+U | the start of the same GET |

- Stored, a text is put as it is, a number read as a number expression, blank as 0, and a
  logical true for `T` or `Y`. A field takes it as `REPLACE` does, and the record is written.
  A wrong value prints its error, the GETs after it are not stored, and the record is read
  again. A variable takes it as `STORE` does.
- Then the GETs are dropped, and the cursor goes to column 0 of the row after the last GET.
  `READ` with no GETs does nothing; a word after it is `Syntax error`.

#### BROWSE

- `BROWSE [FIELDS list] [@ row, column TO row, column] [DOUBLE] [TITLE expression] [FOOTER
  expression] [NOEDIT] [FREEZE n] [FIND]` shows a page of records from the current one, one a row, and
  picks a cell. The clauses come in any order. The record picked at the end is current. Records that
  `SET FILTER TO` and `SET DELETED ON` hide are passed over. `BROWSE` drops the pending GETs.
- With no record from the current one on, it starts at the first record of the order. With none at
  all, the page has the field names and no rows, only Esc, Ctrl+W and a key of `ON KEY` act, and the
  place past the last record is current at the end.
- With no `FIELDS` it shows the `SET FIELDS TO` list. With no list it shows the record's number and
  every field. A row has `*` at its left on a deleted record.
- A field list is `name[:width] ["column name"]`, apart by commas, at most 32, not checked.
  - `RECNO()` as a name shows the record's number there. Its width is at least 5, not checked.
  - The width is a number expression. It cuts the values and the column name, and a field wider than
    it is not edited.
  - The quoted text is the column's name, and changes nothing else. With no width, the column is as
    wide as the longer of the field and the name.
  - The column names of a list fit in 85 bytes, each its length and 2, not checked.
- `@` draws a box from the top left corner to the bottom right corner, and `BROWSE` stays inside it.
  What was under the box comes back at the end. `DOUBLE` gives it double lines. A box is at least 5
  rows by 19 columns, and does not end at row 29, column 79. That is not checked.
- `TITLE` and `FOOTER` are centered on the box's top and bottom lines, or on rows 0 and 29, in place
  of the table's name and the keys. Each fits between the sides of the box. That is not checked.
- `NOEDIT` changes no record. Enter and Ctrl+Enter end the `BROWSE` as Ctrl+W does, and `LASTKEY()`
  gives 13. Ctrl+U does nothing, and the keys row leaves out the edit.
- `FREEZE n` keeps the first n fields on the screen when the columns move. They fit, with a column
  left for the rest, not checked. A field wider than the columns left after them is cut and is not
  edited, frozen or not.
- `FIND` turns on Ctrl+F, and the keys row lists it. Without the clause, Ctrl+F does nothing.

| Key | In `BROWSE` |
|---|---|
| Up, Down, PgUp, PgDn | move through the records |
| Ctrl+Home, Ctrl+End | the first and last record |
| Left, Ctrl+Left | the field before |
| Right, Ctrl+Right, Tab, Enter | the next field |
| Ctrl+Enter | edit the picked cell |
| Ctrl+U | delete the picked record, or recall it when it is deleted, and write it |
| Ctrl+F | with `FIND`, search the picked field |
| F1 to F10 | with `ON KEY`, run the `PROC` |
| Ctrl+W, Esc | end |

- An edit is a GET on the cell. `RECNO()` and a field wider than its column are not edited. Esc ends
  it with the old value back. Any other key that leaves the cell writes it, then acts. Left and
  Right stay in the cell. A wrong value shows its error on the names' row until a key. After that,
  or after a record that breaks `SET VALID TO`, the page is drawn again with the record unchanged.
- An edited or marked record stays on its row until the page is drawn again.
- Ctrl+F asks for a text after `Find: ` on the names' row, blank at the start. Enter searches from the
  record after the picked one along the order, in the picked field, in either case, past the records
  `SET FILTER TO` and `SET DELETED ON` hide. Any other key that leaves the row cancels. It does not
  wrap, and Esc cannot stop a search. No match beeps and the pick stays, and an empty text finds no
  match. A match on the page moves the pick, and one off it is drawn at the top. On `RECNO()` Ctrl+F
  does nothing.
- A key of `ON KEY` writes an open cell, ends the `BROWSE` and runs its `PROC`. The `PROC`'s `ENDPROC`
  runs the `BROWSE` line again, and the field, the row and what was under the box stay as they were.
  The page stays on the screen while the `PROC` runs, and the return draws it again.
  - A `PROC` that changes the table or the fields, or runs a `BROWSE`, loses the field and the row.
    After a `BROWSE` in a `PROC`, the first box's lines can stay on the screen at its end.
  - A `PROC` that fails leaves the page on the screen, and what was under the box is not restored.

#### Menus

- `@ row, column PROMPT text` prints `text` there and adds it as a prompt for `MENU TO`. The
  text is a text expression, else `Type mismatch`. At most 16 prompts; that is not checked.
- `MENU TO name` shows the prompts picked one at a time, the colors of the one picked
  swapped. Up and Left go to the prompt before, Down and Right to the next, around the ends.
  Enter picks the prompt shown. A key picks the first prompt whose first character it is, in
  either case. Esc picks none. It stores the number of the prompt picked, from 1 in the order
  they were made, or 0, in the memory variable `name`, then drops the prompts. With no prompt
  it stores 0 and waits for no key.
- The function `MENU(row, column, items)` draws a box of single lines, its top left corner at
  row and column, with the items inside, one a row, and gives the number picked as `MENU TO`
  does. `items` is a text of at most 254 characters, the items apart by `;`, at most 16; that
  is not checked. The box is as wide as the widest item, and stays on the screen. The prompts
  of `@ ... PROMPT` are dropped. Row or column not a number, or items not text, is
  `Type mismatch`; another count of arguments is `Syntax error`. `? MENU(...)` prints the
  value right after the box's last item.

```
@ 5, 10 PROMPT "Add"
@ 6, 10 PROMPT "Edit"
@ 7, 10 PROMPT "Quit"
MENU TO CHOICE
? MENU(5, 30, "Add;Edit;Quit")
```

#### Screen files

- `SAVE SCREEN TO path` writes the screen's cells to `path`, with `.SCR` added when it has no
  extension. `RESTORE SCREEN FROM path` puts them back.
- The file is the 80 by 30 screen's cells, each its character then its color, 160 bytes a
  row, 4800 bytes, with no header. A short file restores the rows it holds.
- A missing file prints `File not found`. A missing `SCREEN`, `TO` or `FROM`, or path, is
  `Syntax error`.

#### Other programs

- `HELP [topic]` runs `C:\sys\HELPXBASE.COM`, which prints the topic from `C:\sys\xbase\HELPXBASE.HLP`,
  or with no topic lists the topics.
- `!`, `RUN` and `SHELL` alone run `C:\sys\ROMSHELL.COM -N`, a shell that skips `STARTUP.CMD`. Its
  `END` comes back to DB, with the tables and records kept. With a command line after them,
  they run `C:\sys\ROMSHELL.COM -C line`: the shell runs the line, and the script it starts, then
  ends. `!` needs a space after it. `! DIR` lists files.

### The expressions

- Types: text, number, logical and date.
- Operators: `+ - * /`, `( )`, `= # < > <= >=`, `.AND.`, `.OR.`, `.NOT.`.
- Functions: `RECNO()`, `EOF()`, `BOF()`, `DELETED()`, `STR()`, `VAL()`, `SUBSTR()`, `TRIM()`,
  `LEN()`, `INT()`, `UPPER()`, `DATE()`, `FILE()`, `REG()`, `MENU()`, `LASTKEY()`, `CENTER()`,
  `INSTR()`, `INLIST()`, `POPUP()`.
- `LASTKEY()` is the last key `BROWSE`, `READ`, `MENU()` or `WAIT` read, as `WAITKEY()` gives it, 0
  before the first. Enter is 13, Esc is 27, Ctrl+W is 23 and Ctrl+C is 3.
- `CENTER(text, width)` is text centered in width characters, at most 82, the odd space after it. A
  longer text comes back whole.
- `INSTR(text, part)` is the place where part starts in text, from 1. It is 0 when part is absent or
  `""`.
- `INLIST(list, text)` is `.T.` when text, without trailing spaces and in either case, is an item of
  list. The items are apart by `;`. A list that ends in `;` has a blank item.
- `POPUP(list, text)` is `INLIST()`, with a list to pick from when it is in `SET VALID TO`:
  - The field is text, and the list must not be the field read last.
  - In `READ`, a miss shows the list under the field's GET when the GETs are stored. The box stays
    on the screen.
  - In `BROWSE`, Ctrl+Enter on the field shows the list inside the page, hit or miss, and the field
    cannot be typed into. The page is drawn again after it. The check on leaving a cell shows no box.
  - The bar starts on the first item. The item picked goes in the field, cut to its length, and
    `POPUP()` is `.T.`. Esc makes it `.F.`.
- Numbers are MSBASIC's 5-byte float: a 32-bit mantissa, about 9 significant digits. A
  field's text becomes a number through `FIN`, and a number becomes text through `FOUT`.

The float code is a copy of MSBASIC's `src/float.s` in ROM bank 5, `src/asm/fp.s`, behind call
58, `fp`, with its own zero page for FAC and ARG. The copy leaves out `LOG`, `SQR`, `FPWRT`,
`EXP` and the polynomial routines.

- Trap: `float.s` reaches outside itself. `FIN` reads its text through `CHRGET`, and an
  overflow or a division by 0 jumps to `ERROR`. The copy brings its own of each.

### Memory

| Use | Where | Bytes |
|---|---|---|
| 2 work areas | 2 RAM banks from `bank_alloc` | 2 × 8192 |
| 64 memory variables, names and values | 1 RAM bank | 8192 |
| the GETs' pool | program RAM | 2048 |
| `CREATE`'s field table | program RAM | 512 |
| the command file's read-ahead | program RAM | 255 |
| the command line, the expression stack, the rest | program RAM | not measured |

- A table, each of its indexes and each running command file take one entry of the system
  file table, which has 16, entry 0 `CON`. A child that `MODIFY COMMAND`, `HELP` or `!` runs needs
  one for its program file and one for each file it opens.

### Sizes

ROM banks 6 to 8 have 49,152 bytes. Each bank's code runs from `$C000` to `$FF9F`, 16,288
bytes, and ends with the 43-byte `T_FAR`. The bytes free up to `K_FAR`: bank 6 161, bank 7 317,
bank 8 644. The compiler moves the SUBs at the program's tail from bank 6 to
banks 7 and 8 by itself.

`XBASE.COM` stays in ROM banks 6, 7 and 8. Room comes from refactoring the code there, in asm where a
form in UXCBASIC does not save enough.

## Cmdlets

Steps 1 and 2 are built. A cmdlet is a command that is a file in `C:\sys\xbase\`, not in the ROM, and that
is typed as an internal command.

```
. MODSTRU PEOPLE        runs C:\sys\xbase\MODSTRU.COM, with the tail " PEOPLE"
. TOOLS PEOPLE          runs C:\sys\xbase\TOOLS.CMD through the shell, with P1$ = "PEOPLE"
. BIRTHDAYS 11          runs C:\sys\xbase\BIRTHDAYS.PRG, with ARGS = "11"
. MODSTRX               no such file exists, and gives Unknown command
```

### The lookup

- The lookup is in the last `ELSE` of the command loop in `XBASE.UXB`, in place of
  `REPORT_ERROR("Unknown command")`. An internal command and `name = expression` come first.
- The name is the first word of the line. `name.COM` is tried first, then `name.CMD`, then
  `name.PRG`.
- The lookup reads `C:\sys\xbase\` only. It does not read the current folder or `SET PATH`.
- A file that exists and fails to start gives its file error, not `Unknown command`.

### A .COM cmdlet

- It is a UXCBASIC program of at most 38,655 bytes, `$0801` to `$9EFF`.
- `DOS.EXEC` runs it, as `HELP` runs `HELPXBASE.COM`. XBASE's RAM is saved to banks and restored.
- The text after the command word is the tail and `P1$`.
- It gives back an exit code, a system string, or a `REG` key.
- It does not see the open tables, the memory variables, or the expression code. It has no `FOR`
  conditions.
- It carries its own copy of `DB.UXI` to read a table. That costs disk and its own RAM, not ROM.
  The size is not measured.
- Each table, index and command file XBASE holds open takes one of the 16 system file table
  entries. The cmdlet needs one for its program file and one for each file it opens.

WARNING: XBASE's copy of a table goes stale when a `.COM` cmdlet rewrites it. The contract is that
the user runs `CLOSE` first. Nothing checks this.

### A .CMD cmdlet

- `DOS.EXEC` runs `C:\sys\ROMSHELL.COM` with `-C`, as `!` does, and the shell runs the script.
- The words after the command word are `P1$` to `P9$`, by the shell's rules for arguments.
- The script runs a `.COM` in any folder by its full path, or a bare name from the current folder
  or `PATH$`, and goes on when the child ends. A `.CMD` it runs ends it.
- It does not see the open tables or the memory variables. The `CLOSE` contract of a `.COM`
  cmdlet applies.
- The command tail holds at most 126 characters. The shell's switch and the path take 22 and the
  length of the name.
- At most 4 programs run one inside another, and the shell takes a level.

### A .PRG cmdlet

- It runs as `DO` runs a file, and counts against the 8 levels of `DO`.
- The text after the command word is the character memory variable `ARGS`. `ARGS` takes one of
  the 64 memory variables, and a value already in it is lost.
- It sees the open tables and the memory variables, and gives back memory variables.
- It does only what the language does.

### Limits

- `MODIFY` and `APPEND` are internal, so `MODIFY STRUCTURE` and `APPEND FROM` do not reach the
  lookup. Each takes a line in its internal command, or a cmdlet of its own name.
- The list for Tab in `DB_LINE.UXI` is fixed, so a cmdlet name does not complete.
- A cmdlet has a `HELP` topic only if `HELPXBASE.HLP` holds one.

### Cost

The `.COM` and `.CMD` lookup takes 249 bytes of ROM and 40 bytes of low RAM. The `.PRG` lookup
takes 140 bytes of ROM and 6 bytes of low RAM. A cmdlet itself takes no ROM.

### Steps

1. The `.COM` and `.CMD` lookup.
2. The `.PRG` lookup and `ARGS`.
3. `MODSTRU.COM`, which changes a table's fields and keeps its records, matched by field name.
4. An `APPEND FROM` cmdlet, which adds the records of one table to another.
5. Rare commands such as `PACK` and `COPY TO` move out of the ROM. The bytes saved are not measured.

### Still to decide

- Whether `MODIFY STRUCTURE` and `APPEND FROM` forward to a cmdlet. Both act on the table in use,
  and that table must be closed while a `.COM` cmdlet rewrites it.

### The date check, planned

This is not built. The GET of a `D` field checks that each place holds a digit, so month 45 is
stored.

`DATECHK.COM` is a `.COM` cmdlet in `C:\sys\xbase\`:

- It reads the typed text from `P1$`. It writes the cleaned date to `P1$` and ends with exit code
  0, or ends with exit code 1 for a bad date. `src/scom/DISKINFO.UXB` reads and writes its strings
  the same way.
- It takes `20261101`, `11/1/26` and `11-01-26`. A date with a separator is month, day, year, and a
  2-digit year is 20xx. `11/1/2026` does not fit an 8-character cell.
- It checks month 1 to 12, the day limit of the month, and leap years. A blank date is valid.
- It is not named `DATE`, as `DATE` at the prompt would run it as a cmdlet.

The ROM side:

- `STORE_GETS` runs it for each GET of a `D` field, before `PUSH_TEXT` in the text branch. Exit code
  0 stores `P1$`. Exit code 1 gives `Invalid value`, and the error path leaves the record unchanged.
- A missing `DATECHK.COM` stores the date unchecked, with no error.
- A `D` field's mask goes back to all `X`, as `99999999` blocks `/`, and `DATE_MASK$` goes. Letters
  are rejected on save, not on the keypress.
- `PICTURE "@NAME"` names another cmdlet: `@ 5,10 GET BORN PICTURE "@FISCAL"` runs `FISCAL.COM`.
  `BROWSE` has no `PICTURE`, so it needs the default for `D` fields.

Limits:

- `EDIT`, `APPEND` and `REPLACE` do not use GET, so a bad date still gets in through them.
- `READ` checks on save, not on leaving the field. A bad date drops all pending GETs.
- Each date save loads a `.COM` and swaps XBASE's RAM to banks. The time is not measured.

The cost is estimated, and the placement is not checked. The fixed `DATECHK` takes 100 to 150 bytes
of ROM. `PICTURE "@NAME"` takes 200 to 300, plus name storage for each GET. `DATECHK.COM` takes no
ROM.

The steps:

1. `DATECHK.COM` and the fixed hook on `D` fields.
2. `PICTURE "@NAME"`.

A popup calendar can also be a cmdlet. It needs a key to open it and a redraw of the page after it.

## The steps

D1 to D7 are the library and its UXCBASIC face; A1 to A7 are the program; B1 and B2 its help;
C2 to C8 and the steps after them are commands added since. Each step asks before its asm is
written. Every step below is done.

1. **D1. The reference in Python.** `tools/db.py` writes and reads `.DB` and `.IDX` files
   on the PC: create a table, add records, build an index, dump a file. It checks the files
   the X16 writes. Its `make(folder)` writes the test tables, and a test's `NAME.PY` puts them
   on that test's card. No asm.
2. **D2. ROM bank 5.** The bank in the image with its gate tail and IRQ entry, the `db` call
   57 in the jump table and in `docs/API.md`, and `db_info` of no table. A test calls it.
3. **D3. Reading a table.** `db_open`, `db_close`, `db_info`, `db_goto`, `db_get`. A test
   reads a table that D1 made.
4. **D4. Writing a table.** `db_create`, `db_put`, `db_append`, `db_write`, `db_flag`,
   `db_pack`. A test writes a table, and D1 checks it.
5. **D5. Reading an index.** `ix_open`, `ix_close`, `ix_order`, `ix_find`, `ix_first`,
   `ix_last`, `ix_next`, `ix_prev`. A test walks an index that D1 made.
6. **D6. Writing an index.** The insert with its split, the delete, `ix_create`, and
   `db_write`'s update of the open indexes. A test adds and changes records, and D1 checks
   the index.
7. **D7. `lib/DB.UXI`.** A `SUB` or `FUNCTION` for each function, a test program in
   UXCBASIC, and a help topic.
8. **A1. The prompt.** `XBASE.COM`, the stub, the dot prompt, `USE`, `LIST` with no expression,
   `GO`, `SKIP`, `DISPLAY STRUCTURE`, `QUIT`.
9. **A2. Expressions.** The evaluator, the float code, the functions, `?`, `STORE`, the memory
   variables.
10. **A3. Scopes.** `FOR`, `NEXT`, `ALL`, `LOCATE`, `CONTINUE`, `COUNT`, `SUM`, `DISPLAY`.
    - A3a. The scopes and `FOR`, on `LIST` and `DISPLAY`.
    - A3b. `COUNT` and `SUM`.
    - A3c. `LOCATE` and `CONTINUE`.
11. **A4. Changes.** `CREATE`, `APPEND`, `REPLACE`, `DELETE`, `RECALL`, `PACK`, `EDIT`.
    - A4a. `DELETE`, `RECALL`, `PACK`.
    - A4b. `REPLACE`.
    - A4c. `APPEND BLANK`, and `APPEND` with a prompt for each field.
    - A4d. `CREATE`, with prompts for the fields.
    - A4e. `EDIT`, with a prompt for each field of the current record.
12. **A5. Indexes.** `INDEX ON`, `SET INDEX TO`, `FIND`, `REINDEX`, two work areas.
    - A5a. `INDEX ON`, `SET INDEX TO`, `USE path INDEX names`.
    - A5b. The moves follow the order: `GO TOP`, `GO BOTTOM`, `SKIP`, the scopes. Library call
      `ix_place`.
    - A5c. `FIND`, `REINDEX`.
    - A5d. `SELECT PRIMARY`, `SELECT SECONDARY`, two work areas, `P.name` and `S.name`.
13. **A6. Command files.** The system file table and the FAT32 library raised to 16 entries
    first.
    - A6a. `DO name`, `RETURN`, `CANCEL`, nested `DO`.
    - A6b. `IF`, `ELSE`, `ENDIF`.
    - A6c. `DO WHILE`, `ENDDO`.
    - A6d. `ACCEPT`, `INPUT`, `WAIT`.
    - A6e. `MODIFY COMMAND`.
14. **A7. Screens.**
    - A7a. `CLEAR`, `CLS`, `@ row, column SAY`.
    - A7b. `@ row, column GET`, `READ`, `PICTURE`, `CLEAR GETS`. The program takes ROM bank 8:
      `#ROMBANKS` takes a third bank.
    - A7c. The help topic.
15. **B1. `HELPXBASE.COM`.** `src/dos/HELPXBASE.UXB` and `card/sys/xbase/HELPXBASE.HLP`, the DB help as its own
    program, as `HELPBAS`.
16. **`DB name`** runs a command file.
17. **B2. `HELP [topic]`** at the dot prompt runs `HELPXBASE.COM`.
18. **C2. `REG`**, the statement and the function.
19. **C3. `SET PATH TO`.**
20. **C4. `!`, `RUN`, `SHELL`** run the shell.
21. **C5. The shell's `-C line`**, and `!`, `RUN` and `SHELL` with a command line.
22. **C6. `ZAP`.**
23. **C7. `COPY TO`.**
24. **C8. `SET FILTER TO`.**
25. **`BOX` and `@ ... TO`.**
26. **`SET REVERSE`.**
27. **`@ ... PROMPT` and `MENU TO`.**
28. **The function `MENU()`.**
29. **`SAVE SCREEN TO` and `RESTORE SCREEN FROM`.**
30. **`PUSH` and `POP`.**

## Limitations

- A table has at most 32 fields, 1000 bytes a record and 65535 records.
- A work area has at most 3 open indexes.
- A key is at most 100 bytes, of at most 4 fields.
- An `N` field holds at most 10 characters. A number holds about 9 significant digits.
- Two programs that open one table at once each keep their own copy of its header.
- A command line is cut at 240 characters; the prompt takes 239.
- Command files nest 8 deep, and `DO WHILE` loops and `GOSUB`s 8 deep together. `PUSH` holds 4 levels.
- At most 32 GETs in 2048 bytes, 16 prompts, and 16 items in `MENU()`.
- The screen files are 80 by 30.

## Still to decide

- Whether MSBASIC gets statements for the `db` call.
- Whether `XBASE.COM` has a report command, as dBASE II's `REPORT`.

## To do

- A `COLOR` statement.
- A second kind of `CONST`, kept like a `.MEM` file, in the memory-variable bank. That bank has
  about 7K free.
- `SET TALK`.
- `REG key TO expression` and `REG(key)` use a private `.REG` file.
- Check the handling of `D` fields, and add date functions with date arithmetic.
- The help says what form a `D` field is typed in.
