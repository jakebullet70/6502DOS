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
| The dot prompt and `.PRG` command files | the same, in the program `DB.COM` |
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
| `C` | 1 to 254 | left-aligned, padded with spaces |
| `N` | 1 to 10 | right-aligned, padded with spaces, a `-` before the digits, a `.` before the decimals |
| `L` | 1 | `T`, `F`, or `?` for not set |
| `D` | 8 | `YYYYMMDD`, or 8 spaces for no date |

A table holds at most 65535 records of 1000 bytes: 65,535,000 bytes, which `seek`'s 32-bit
offset reaches.

## The index file

An index is a file with the extension `.IDX`, of 512-byte pages. Page n starts at offset
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
  has 8.
- The library reads and writes through `read`, `write` and `seek`, which keep the caller's RAM
  bank.

### Sizes

| Part | Bytes |
|---|---|
| The library, `src/asm/db.s` | 4318 |
| MSBASIC's float, `src/asm/fp.s`, call 58 | 2258 |
| total, `$C000–$D9AF` | 6576 |

ROM bank 5 has 16,384 bytes. About 9,700 are free.

## The program, DB.COM

`DB.COM` is a stub that starts the program in ROM banks 6 and 7, as `ROMSHELL.COM` starts the
shell. The program is UXCBASIC, `src/bank6/DB.UXB`, compiled with `#ROMBANKS 6, 7`. It calls
the library through `lib/DB.UXI` and the float through `lib/FLOAT.UXI`. ROM bank 8 is kept for
its growth.

### The commands

| Group | Commands |
|---|---|
| Tables | `USE`, `SELECT PRIMARY`, `SELECT SECONDARY`, `CREATE`, `DISPLAY STRUCTURE` |
| Moving | `GO`, `GOTO`, `GO TOP`, `GO BOTTOM`, `SKIP`, `LOCATE FOR`, `CONTINUE` |
| Showing | `LIST`, `DISPLAY`, `?`, `COUNT`, `SUM` |
| Changing | `APPEND`, `APPEND BLANK`, `EDIT`, `REPLACE ... WITH`, `DELETE`, `RECALL`, `PACK` |
| Indexes | `INDEX ON ... TO`, `SET INDEX TO`, `FIND`, `REINDEX` |
| Variables | `STORE ... TO`, `RELEASE`, `DISPLAY MEMORY` |
| Screens | `@ ... SAY`, `@ ... GET`, `READ`, `CLEAR`, `ACCEPT`, `INPUT`, `WAIT` |
| Command files | `DO`, `IF`, `ELSE`, `ENDIF`, `DO WHILE`, `ENDDO`, `RETURN`, `CANCEL`, `QUIT` |
| Settings | `SET TALK`, `SET DELETED` |

`LIST`, `DISPLAY`, `COUNT`, `SUM`, `LOCATE`, `REPLACE`, `DELETE` and `RECALL` take a scope
(`ALL`, `NEXT n`, `RECORD n`) and a `FOR` condition, in any order. With no scope, `FOR` means
all the records. The scope of `DISPLAY`, `REPLACE`, `DELETE` and `RECALL` is the current
record; that of `LIST`, `COUNT`, `SUM` and `LOCATE` is every record.

- `COUNT scope TO name` prints `n records`. `SUM list scope TO names` sums at most 8 number
  expressions, prints `n records summed`, then each sum on a line. `TO` stores the results in
  memory variables.
- `LOCATE scope` makes the first record that meets the condition current and prints
  `Record n`, else `End of LOCATE`. `CONTINUE` looks on from the record after the current
  one. With no `LOCATE` since the start or the last `USE`, `CONTINUE` prints
  `No LOCATE active`.
- `DELETE scope` and `RECALL scope` mark or clear each record and print `n records deleted`
  or `n records recalled`.
- `PACK` removes the deleted records, prints `n records left`, and makes record 1 current. A
  failed `PACK` leaves no table in use.
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

### The expressions

- Types: text, number, logical and date.
- Operators: `+ - * /`, `( )`, `= # < > <= >=`, `$` (text in text), `.AND.`, `.OR.`, `.NOT.`.
- Functions: `RECNO()`, `EOF()`, `BOF()`, `DELETED()`, `STR()`, `VAL()`, `SUBSTR()`, `TRIM()`,
  `LEN()`, `INT()`, `UPPER()`, `DATE()`, `FILE()`.
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
| the command line, the expression stack, the `DO` nesting, 16 deep | program RAM | 2048 |

### Sizes

ROM banks 6 to 8 have 49,152 bytes. Through A4c, bank 6 has 23 bytes free and bank 7 has
11,793. The program spills from bank 6 to bank 7 by itself.

## The steps

D1 to D6 are the library and D7 is its UXCBASIC face; A1 to A7 are the program. Each step
asks before its asm is written. D1 to D7, A1 to A3, and A4a to A4c are done.

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
8. **A1. The prompt.** `DB.COM`, the stub, banks 6 and 7, the dot prompt, `USE`, `LIST` with
   no expression, `GO`, `SKIP`, `DISPLAY STRUCTURE`, `QUIT`.
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
13. **A6. Command files.** `DO`, `IF`, `ELSE`, `ENDIF`, `DO WHILE`, `ENDDO`, `RETURN`,
    `CANCEL`, `ACCEPT`, `INPUT`, `WAIT`, `MODIFY COMMAND`.
14. **A7. Screens.** `@ SAY`, `@ GET`, `READ`, `CLEAR`, and a help topic.

## Limitations

- A table has at most 32 fields, 1000 bytes a record and 65535 records.
- A work area has at most 3 open indexes.
- A key is at most 100 bytes, of at most 4 fields.
- An `N` field holds at most 10 characters. A number holds about 9 significant digits.
- Two programs that open one table at once each keep their own copy of its header.

## Still to decide

- Whether MSBASIC gets statements for the `db` call.
- Whether `DB.COM` has a report command, as dBASE II's `REPORT`.

## To do

- A `COLOR` statement.
- A second kind of `CONST`, kept like a `.MEM` file, in the memory-variable bank. That bank has
  about 7K free.
- Reading and writing the registry, `6502DOS.REG`, through `DOS.REG_GET` and `DOS.REG_SET`.
- More open files. A table or an index takes an SFT entry and a FAT32 context, and a child
  run by `exec` needs one of each for its own program file and one for each file it opens.
  - The SFT has 8 entries of 32 bytes in RAM bank 0, `$A000-$A0FF`, and entry 0 is `CON`. An
    entry uses 14 bytes, so `SFT_SIZE` 16 gives 16 entries in the same page.
  - The FAT32 library has 8 contexts of 32 bytes, `FAT32_CONTEXTS`; it refuses more than fit
    in 256 bytes. More needs a change to the library's context indexing.
  - With neither change, `MODIFY COMMAND` can close both areas' tables and indexes before the
    editor runs and open them again after it.
