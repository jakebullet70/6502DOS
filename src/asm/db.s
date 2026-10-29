; 6502DOS ROM bank 5: the table and index library behind call 57, db, then the IRQ entry and
; the vectors of the bank. docs/DB.PLAN.md holds the files and the workspace.
;
; Trap: this code runs in ROM bank 5. It reaches the kernel only through the call entries in
; RAM, never by JSR to a routine in bank 0 or 1.

.setcpu "65C02"

.include "mem.inc"
.include "api.inc"
.include "far.inc"

.export api_db
.import irq

; The workspace, in the table's RAM bank: 32 bytes of state, then the table's header and its
; field table, the current record, and the record as the file holds it. The indexes' slots, the
; path, two pages and the indexes' paths follow. The table's path and db_pack's path are at the
; top.
DB_HANDLE     = BANKED_RAM      ; the table's file handle
DB_CURRENT    = BANKED_RAM + 1  ; the current record, 2 bytes, 0 for none
DB_WANT       = BANKED_RAM + 3  ; db_load and db_save: the bytes asked for, 2 bytes
DB_SPARE      = BANKED_RAM + 5  ; db_pack: the new file's handle
DB_ORDER      = BANKED_RAM + 6  ; the order: an index's offset in IX_SLOTS, or $FF for the records'
DB_SPOT       = BANKED_RAM + 7  ; $80 past the last record of the order, $40 before the first, else 0
IX_TOP        = BANKED_RAM + 8  ; the path's length, 3 bytes a level
IX_LOADED     = BANKED_RAM + 9  ; the page in IX_PAGE, 2 bytes, 0 for none
IX_FILL       = BANKED_RAM + 11 ; ix_open and ix_create: the slot's offset
IX_LEFT       = BANKED_RAM + 12 ; the key fields left to count
IX_EXACT      = BANKED_RAM + 13 ; ix_compare: nonzero to compare the record after an equal key
IX_SAME       = BANKED_RAM + 14 ; ix_compare: nonzero once an equal key was seen
IX_GREW       = BANKED_RAM + 15 ; ix_insert: nonzero when the header changed
IX_AT         = BANKED_RAM + 16 ; ix_gap: the place; ix_split: the keys that stay
IX_MOVES      = BANKED_RAM + 17 ; the keys left to move
IX_PUT        = BANKED_RAM + 18 ; ix_make: the key's bytes so far
IX_FIELD      = BANKED_RAM + 19 ; ix_make: the next key field's offset in IX_SLOTS, less 11
IX_END        = BANKED_RAM + 20 ; ix_make: the field's bytes left
IX_SIGN       = BANKED_RAM + 21 ; ix_make: the place of an N field's -, else 0
IX_KIND       = BANKED_RAM + 22 ; ix_make: 0 for an N field
IX_TAKE       = BANKED_RAM + 23 ; ix_alloc and ix_give: the page taken or given, 2 bytes
IX_KEEP       = BANKED_RAM + 25 ; ix_update and db_pack: the order before
IX_FROM       = BANKED_RAM + 26 ; ix_make: $80 to read DB_OLD, else 0
IX_DIFF       = BANKED_RAM + 27 ; ix_byte: nonzero once a key's byte changed
IX_HAD        = BANKED_RAM + 28 ; ix_update: nonzero when the file holds the record
IX_HOLE       = BANKED_RAM + 29 ; ix_delete: the path's length at the entry's node
IX_SIDE       = BANKED_RAM + 30 ; ix_mend: $FF when the page beside is before the empty one
IX_ABOVE      = BANKED_RAM + 31 ; ix_mend: the keys left in the page above
DB_HEADER     = BANKED_RAM + 32
DB_RECORD     = DB_HEADER + 16 + 16 * 32 + 1
DB_OLD        = DB_RECORD + DB_MAX_RECORD ; ix_update: the record as the file holds it
IX_GONE       = DB_OLD + DB_MAX_RECORD ; ix_mend: the empty page, 2 bytes
IX_HOLD       = IX_GONE + 2     ; ix_mend: the empty page's page below, 2 bytes
DB_PATH       = BANKED_RAM + $1E00 ; the table's path, length-prefixed, 256 bytes
DB_TEMP       = DB_PATH + 256   ; db_pack's new file: the path with its last character changed
DB_VERSION    = 1
DB_MAX_RECORD = 1000            ; the longest record, the delete flag included
IX_SLOTS      = BANKED_RAM + $0A20 ; 3 indexes, 32 bytes each: page 0's first 16 bytes, then:
IX_HANDLE     = 16              ;   the index's file handle
IX_WIDTH      = 17              ;   the key's length + 4, from one key to the next
IX_CAP        = 18              ;   the keys a page holds
IX_WORK       = 19              ;   ix_update and db_pack: nonzero to change the index
IX_PATH       = IX_SLOTS + 96   ; the path from the root, 3 bytes a level: a page, then a key
IX_DEEP       = 10              ; the levels of the path
IX_MAX_KEY    = 100             ; the longest key
IX_SIZE       = IX_PATH + 3 * IX_DEEP + 1 ; the key's length, for ix_compare
IX_ITEM       = IX_SIZE + 1     ; the entry to insert: the key, the record, the page above
IX_PAGE       = BANKED_RAM + $0C00 ; the page read, 512 bytes, and an entry past it in a split
IX_NEW        = BANKED_RAM + $0F00 ; the page built, 512 bytes
IX_NAMES      = BANKED_RAM + $1100 ; the indexes' paths, length-prefixed, 256 bytes a slot
.assert <IX_SLOTS + 64 + 16 < 256, error, "ix_area adds an offset to <IX_SLOTS alone"
.assert <IX_PAGE = 0 && <IX_NEW = 0, error, "ix_span sets r0 with stz"
.assert <IX_NAMES = 0, error, "ix_name sets r0 with stz"
.assert IX_HOLD + 2 <= IX_SLOTS, error, "the record as read runs into the slots"
.assert IX_NEW + 512 <= IX_NAMES && IX_NAMES + 3 * 256 <= DB_PATH, error, "the paths overlap"
.assert IX_ITEM + IX_MAX_KEY + 4 <= IX_PAGE, error, "the entry runs into the page"
.assert IX_PAGE + 512 + IX_MAX_KEY + 4 <= IX_NEW, error, "a split's extra entry runs into IX_NEW"

.segment "KERNELZP" : zeropage

db_ptr:       .res 2            ; a field's entry, a field's text, or the record less 1
ix_key:       .res 2            ; the key compared less 1, or where an entry is copied less 2

.segment "B5CODE"

; api_db: call 57. Y = the function, A = the table's RAM bank; X and r0 to r3 by function.
; Runs the function with that bank selected, then selects the caller's bank again. A, X and
; carry come back from the function.
api_db:
        cpy #DB_COUNT
        bcs db_bad
        phx
        ldx RAM_BANK
        sta RAM_BANK
        pla
        phx                     ; the caller's RAM bank
        tax                     ; X as it came
        jsr @call
        ply
        sty RAM_BANK
        rts
@call:
        tya
        asl
        tay
        lda db_table+1,y
        pha
        lda db_table,y
        pha
        rts                     ; to the function, with X as it came

; db_bad: the function of a number not written. Returns carry set, A = 1.
db_bad:
        lda #ERR_BAD_FUNCTION
        sec
        rts

; db_table: for each function by number, its routine less 1, for the RTS of api_db.
db_table:
        .addr db_create - 1     ; 0 create
        .addr db_open - 1       ; 1 open
        .addr db_close - 1      ; 2 close
        .addr db_info - 1       ; 3 info
        .addr db_goto - 1       ; 4 goto
        .addr db_get - 1        ; 5 get
        .addr db_put - 1        ; 6 put
        .addr db_append - 1     ; 7 append
        .addr db_write - 1      ; 8 write
        .addr db_flag - 1       ; 9 flag
        .addr db_pack - 1       ; 10 pack
        .addr ix_create - 1     ; 11 ix_create
        .addr ix_open - 1       ; 12 ix_open
        .addr ix_close - 1      ; 13 ix_close
        .addr ix_order - 1      ; 14 ix_order
        .addr ix_find - 1       ; 15 ix_find
        .addr ix_first - 1      ; 16 ix_first
        .addr ix_last - 1       ; 17 ix_last
        .addr ix_next - 1       ; 18 ix_next
        .addr ix_prev - 1       ; 19 ix_prev
        .addr ix_place - 1      ; 20 ix_place
        .assert * - db_table = 2 * DB_COUNT, error, "db_table needs a routine for each function"

; db_create: makes the table at path r0 with the X fields of the field table at r1, 16 bytes a
; field, and opens it with no records. Works out each field's offset and the record's length.
; 1 to 32 fields, each 1 byte or longer, in a record of at most DB_MAX_RECORD bytes, else error
; 13. Changes r0 and r1. A table already open in the workspace stays open: close it first.
db_create:
        stz DB_HEADER           ; no table until the file is made
        txa
        dec
        cmp #32                 ; 1 to 32 fields
        bcc @fields
@bad:
        jmp db_bad_data
@fields:
        stx DB_HEADER+3
        stz DB_HEADER+4         ; no records
        stz DB_HEADER+5
        stz DB_HEADER+13
        stz DB_HEADER+14
        stz DB_HEADER+15
        lda #1                  ; the record's length so far: the delete flag
        sta DB_HEADER+8
        stz DB_HEADER+9
        lda #<(DB_HEADER + 16)
        sta db_ptr
        lda #>(DB_HEADER + 16)
        sta db_ptr+1
@field:
        ldy #13                 ; the name, the type, the length and the decimals
@copy:
        lda (r1),y
        sta (db_ptr),y
        dey
        bpl @copy
        ldy #14                 ; the field's offset: the record's length so far
        lda DB_HEADER+8
        sta (db_ptr),y
        iny
        lda DB_HEADER+9
        sta (db_ptr),y
        ldy #12
        lda (db_ptr),y          ; the field's length
        beq @bad
        clc
        adc DB_HEADER+8
        sta DB_HEADER+8
        bcc @next
        inc DB_HEADER+9
@next:
        lda r1
        clc
        adc #16
        sta r1
        bcc @entry
        inc r1+1
@entry:
        lda db_ptr
        clc
        adc #16
        sta db_ptr
        bcc @more
        inc db_ptr+1
@more:
        dex
        bne @field
        lda #$0D
        sta (db_ptr)
        sec                     ; the header's length: up to the $0D, and 1
        lda db_ptr
        sbc #<(DB_HEADER - 1)
        sta DB_HEADER+6
        lda db_ptr+1
        sbc #>(DB_HEADER - 1)
        sta DB_HEADER+7
        jsr db_keep
        jsr db_long
        bcs @done
        lda #0                  ; no attributes
        jsr API_CREATE
        bcs @done
        stx DB_HANDLE
        stz DB_CURRENT
        stz DB_CURRENT+1
        jsr db_stamp
        ldy #2
@magic:
        lda db_magic,y
        sta DB_HEADER,y
        dey
        bpl @magic
        lda #<DB_HEADER
        sta r0
        lda #>DB_HEADER
        sta r0+1
        lda DB_HEADER+6
        sta r1
        lda DB_HEADER+7
        sta r1+1
        jsr db_save
        bcs db_shut
@done:
        rts

; db_open: opens the table at path r0 to read and write, and reads its header and field table.
; Returns r0 = the records, X = the fields; no record is current. Changes r1. A file that is not
; a table gives error 11. A table already open in the workspace stays open: close it first.
db_open:
        jsr db_keep
        lda #2                  ; read and write
        jsr API_OPEN
        bcs @done
        stx DB_HANDLE
        stz DB_CURRENT
        stz DB_CURRENT+1
        lda #<DB_HEADER
        sta r0
        lda #>DB_HEADER
        sta r0+1
        lda #16
        sta r1
        stz r1+1
        jsr db_load
        bcs db_shut
        jsr db_need
        bcs @format
        lda DB_HEADER+3         ; the fields, 1 to 32
        dec
        cmp #32
        bcs @format
        jsr db_long
        bcs @format
        lda #<(DB_HEADER + 16)
        sta r0
        lda #>(DB_HEADER + 16)
        sta r0+1
        stz r1+1                ; r1 = 16 * the fields + 1, for the $0D
        lda DB_HEADER+3
        ldy #4
@times16:
        asl
        rol r1+1
        dey
        bne @times16
        ora #1
        sta r1
        jsr db_load
        bcs db_shut
        lda DB_HEADER+4
        sta r0
        lda DB_HEADER+5
        sta r0+1
        ldx DB_HEADER+3
@done:
        rts
@format:
        lda #ERR_BAD_FORMAT
        ; fall into db_shut

; db_shut: closes the file of a failed create or open, leaves no table, and returns carry set
; and A as it came.
db_shut:
        stz DB_HEADER           ; no table
        pha
        ldx DB_HANDLE
        jsr API_CLOSE
        pla
        sec
        rts

; db_long: carry set and A = 13 when the header's record is longer than DB_MAX_RECORD.
db_long:
        lda DB_HEADER+8
        cmp #<(DB_MAX_RECORD + 1)
        lda DB_HEADER+9
        sbc #>(DB_MAX_RECORD + 1)
        lda #ERR_BAD_DATA
        rts

; db_close: closes the table and its indexes. The workspace then holds no table.
db_close:
        jsr db_need
        bcs @done
        jsr ix_shut
        stz DB_HEADER           ; no table
        ldx DB_HANDLE
        jmp API_CLOSE
@done:
        rts

; db_info: X = 0 gives r0 = the table's header; X = 1 to the number of fields gives r0 = field
; X's entry. Both are 16 bytes in the workspace.
db_info:
        jsr db_entry
        bcs @done
        lda db_ptr
        sta r0
        lda db_ptr+1
        sta r0+1
@done:
        rts

; db_get: copies field X of the current record to the buffer at r0: its length, then its text.
db_get:
        jsr db_field
        bcs @done
        tya
        sta (r0)
@copy:
        lda (db_ptr),y
        sta (r0),y
        dey
        bne @copy               ; carry clear from db_field
@done:
        rts

; db_write: brings the open indexes in step with the current record (ix_update), writes it, then
; the header, with the records and today's date. The record from db_append adds a record. A key
; already in a unique index gives error 13, and nothing is written. Changes r0 and r1.
db_write:
        jsr db_current
        bcs @done
        jsr ix_update
        bcs @done
        jsr db_seek
        bcs @done
        jsr db_record
        jsr db_save
        bcs @done
        lda DB_HEADER+4         ; the records less the current record
        cmp DB_CURRENT
        lda DB_HEADER+5
        sbc DB_CURRENT+1
        bcs db_header
        lda DB_CURRENT          ; appended
        sta DB_HEADER+4
        lda DB_CURRENT+1
        sta DB_HEADER+5
        bra db_header
@done:
        rts

; db_header: stamps today's date in the header, and writes the header's 16 bytes at the start of
; the table's file. Changes r0 and r1.
db_header:
        jsr db_stamp
        stz r0
        stz r0+1
        stz r1
        stz r1+1
        ldx DB_HANDLE
        lda #0                  ; from the start
        jsr API_SEEK
        bcs @done
        lda #<DB_HEADER
        sta r0
        lda #>DB_HEADER
        sta r0+1
        lda #16
        sta r1
        stz r1+1
        jmp db_save
@done:
        rts

; db_append: blanks the record, spaces with ? in each L field, and makes it the current record,
; number records + 1. The first db_write adds it to the file. Returns r0 = its number. A table
; of 65535 records gives error 13.
db_append:
        jsr db_need
        bcs @done
        lda DB_HEADER+4         ; the records, and 1
        ldx DB_HEADER+5
        inc
        bne @number
        inx
        beq db_bad_data
@number:
        sta DB_CURRENT
        stx DB_CURRENT+1
        ldx DB_HEADER+3
@field:
        phx
        jsr db_field            ; carry clear: the table, the record and the field are good
        ldx #' '
        cmp #'L'
        bne @fill
        ldx #'?'
@fill:
        txa
@byte:
        sta (db_ptr),y
        dey
        bne @byte
        plx
        dex
        bne @field
        lda #' '                ; not deleted
        sta DB_RECORD
        lda DB_CURRENT
        sta r0
        lda DB_CURRENT+1
        sta r0+1
        clc
@done:
        rts

; db_put: puts the text at r0, its length then its text, in field X of the current record,
; padded with spaces: right-aligned in an N field, else left-aligned. Text longer than the field
; gives error 13.
db_put:
        jsr db_field
        bcs @done
        eor #'N'
        pha                     ; 0 for an N field
        tya
        sec
        sbc (r0)                ; the spaces
        tax
        pla
        bcc db_bad_data
        beq @blank              ; an N field: the spaces before the text
        ldx #0                  ; else the text first
@blank:
        lda #' '
@space:
        sta (db_ptr),y
        dey
        bne @space
        txa
        clc
        adc db_ptr
        sta db_ptr
        bcc @text
        inc db_ptr+1
@text:
        lda (r0)
        tay
        beq @ok
@copy:
        lda (r0),y
        sta (db_ptr),y
        dey
        bne @copy
@ok:
        clc
@done:
        rts

; db_current: carry clear when the workspace holds a table and a current record; else error 6
; or 13. Keeps X.
db_current:
        jsr db_need
        bcs @done
        lda DB_CURRENT
        ora DB_CURRENT+1
        beq db_bad_data
@done:
        rts

db_bad_data:
        lda #ERR_BAD_DATA
        sec
        rts

; db_flag: X = 0 recalls the current record, X = 1 marks it deleted. db_write writes it.
db_flag:
        jsr db_current
        bcs @done
        cpx #2
        bcs db_bad_data
        lda #' '
        dex
        bne @set                ; X was 0
        lda #'*'
@set:
        sta DB_RECORD           ; carry clear from the cpx
@done:
        rts

; db_field: needs a current record and field X, 1 to the number of fields. Points db_ptr at the
; field's text less 1, and returns Y = its length and A = its type. Carry clear on success.
; Changes X.
db_field:
        jsr db_current
        bcs @done
        txa
        beq db_bad_data         ; field 0 has no text
        jsr db_entry
        bcs @done
        ldy #11
        lda (db_ptr),y          ; the type
        pha
        iny
        lda (db_ptr),y          ; the length
        pha
        ldy #14                 ; carry clear from db_entry
        lda (db_ptr),y
        adc #<(DB_RECORD - 1)
        tax
        iny
        lda (db_ptr),y
        adc #>(DB_RECORD - 1)   ; carry clear after it
        sta db_ptr+1
        stx db_ptr
        ply
        pla
@done:
        rts

; db_entry: needs a table, then points db_ptr at the entry of field X, or at the header for
; X = 0. A field past the last gives error 13. Keeps X; carry clear on success.
db_entry:
        jsr db_need
        bcs @done
        cpx DB_HEADER+3         ; the number of fields
        beq @point
        bcs db_bad_data
@point:
        stz db_ptr+1
        txa
        ldy #4
@times16:
        asl
        rol db_ptr+1
        dey
        bne @times16
        adc #<DB_HEADER         ; carry clear: db_ptr+1 stays below $80
        sta db_ptr
        lda db_ptr+1
        adc #>DB_HEADER
        sta db_ptr+1
@done:
        rts

; db_goto: reads record r0, 1 to the number of records, and makes it current. Returns X = its
; delete flag. Changes r0 and r1. A failed read leaves no record current.
db_goto:
        jsr db_need
        bcs @done
        stz DB_SPOT
        lda r0
        ora r0+1
        beq db_bad_data
        lda DB_HEADER+4         ; the records less r0
        cmp r0
        lda DB_HEADER+5
        sbc r0+1
        bcc db_bad_data
        lda r0
        sta DB_CURRENT
        lda r0+1
        sta DB_CURRENT+1
        jsr db_seek
        bcs @fail
        jsr db_record
        jsr db_load
        bcs @fail
        ldx DB_RECORD
@done:
        rts
@fail:
        stz DB_CURRENT
        stz DB_CURRENT+1
        rts

; db_pack: copies the header and the records not marked deleted to a new file, the table's path
; with its last character $, or & for a $. Then it deletes the table's file, renames the new one
; to the table's path, and opens it. Then it builds each open index again, in its slot, and keeps
; the order (ix_remake). Returns r0 = the records, X = the fields; no record is current. Changes
; r1. A failed pack leaves no table; the table's file is unchanged unless the delete or the rename
; failed. A failed build leaves that index and those after it closed, and its file deleted.
; Trap: the paths are the ones that create, open, ix_open and ix_create were given. A relative
; path names another file once the program changes its directory.
db_pack:
        jsr db_need
        bcc @table
        rts
@table:
        lda DB_ORDER
        sta IX_KEEP
        ldy #64                 ; the open indexes, to build again
@mark:
        lda IX_SLOTS,y
        sta IX_SLOTS+IX_WORK,y
        tya
        sec
        sbc #32
        tay
        bcs @mark
        jsr ix_shut
        jsr db_temp
        lda #0                  ; no attributes
        jsr API_CREATE
        bcc @made
        jmp db_shut
@made:
        stx DB_SPARE
        lda #1                  ; the first record
        sta DB_CURRENT
        stz DB_CURRENT+1
        jsr db_seek
        bcs @drop
        stz DB_CURRENT          ; the records kept
        lda #<DB_HEADER
        sta r0
        lda #>DB_HEADER
        sta r0+1
        lda DB_HEADER+6
        sta r1
        lda DB_HEADER+7
        sta r1+1
        jsr db_swap
        jsr db_save
        jsr db_swap
        bcs @drop
@next:
        lda DB_HEADER+4         ; the records left to read
        ora DB_HEADER+5
        beq @end
        lda DB_HEADER+4
        bne @count
        dec DB_HEADER+5
@count:
        dec DB_HEADER+4
        jsr db_record
        jsr db_load
        bcs @drop
        lda DB_RECORD
        cmp #'*'
        beq @next
        jsr db_record
        jsr db_swap
        jsr db_save
        jsr db_swap
        bcs @drop
        inc DB_CURRENT
        bne @next
        inc DB_CURRENT+1
        bra @next
@drop:
        pha
        ldx DB_SPARE
        jsr API_CLOSE
        jsr db_temp_r0
        jsr API_DELETE
        pla
        jmp db_shut
@end:
        lda DB_CURRENT
        sta DB_HEADER+4
        lda DB_CURRENT+1
        sta DB_HEADER+5
        jsr db_swap
        jsr db_header
        jsr db_swap
        bcs @drop
        ldx DB_SPARE
        jsr API_CLOSE
        bcs @drop
        stz DB_HEADER           ; no table
        ldx DB_HANDLE
        jsr API_CLOSE
        bcs @done
        jsr db_path_r0
        jsr API_DELETE
        bcs @done
        jsr db_temp_r0
        lda #<DB_PATH
        sta r1
        lda #>DB_PATH
        sta r1+1
        jsr API_RENAME
        bcs @done
        jsr db_path_r0
        jsr db_open
        bcs @done
        jmp ix_remake
@done:
        rts

; db_swap: swaps the table's handle and DB_SPARE. Keeps A and carry; changes X and Y.
db_swap:
        ldx DB_HANDLE
        ldy DB_SPARE
        stx DB_SPARE
        sty DB_HANDLE
        rts

; db_keep: copies the path at r0, its length then its text, to DB_PATH, and marks each index
; slot free, with the record order, and clears IX_FROM. Changes A and Y.
db_keep:
        stz IX_FROM
        stz IX_SLOTS
        stz IX_SLOTS+32
        stz IX_SLOTS+64
        lda #$FF
        jsr ix_turn
        lda (r0)
        tay
@copy:
        lda (r0),y
        sta DB_PATH,y
        dey
        cpy #$FF
        bne @copy
        rts

; db_temp: copies DB_PATH to DB_TEMP with its last character $, or & for a $, and gives r0 =
; DB_TEMP. db_temp_r0 gives r0 = DB_TEMP; db_path_r0 gives r0 = DB_PATH. Change A; db_temp
; changes Y.
db_temp:
        ldy DB_PATH
@copy:
        lda DB_PATH,y
        sta DB_TEMP,y
        dey
        cpy #$FF
        bne @copy
        ldy DB_PATH
        lda #'$'
        cmp DB_TEMP,y
        bne @last
        lda #'&'
@last:
        sta DB_TEMP,y
db_temp_r0:
        lda #<DB_TEMP
        sta r0
        lda #>DB_TEMP
        sta r0+1
        rts
db_path_r0:
        lda #<DB_PATH
        sta r0
        lda #>DB_PATH
        sta r0+1
        rts

; ix_open: opens the index at path r0 on the table, in the first free slot, and returns X = the
; slot. The order stays. A file that is not an index on the table's fields gives error 11, and
; a fourth index gives error 4. Changes r0 and r1.
ix_open:
        jsr ix_free
        bcs @done
        jsr ix_keep
        lda #2                  ; read and write
        jsr API_OPEN
        bcc @open
@done:
        rts
@open:
        txa
        ldy IX_FILL
        sta IX_SLOTS+IX_HANDLE,y
        tya
        jsr ix_area             ; page 0's first 16 bytes; carry clear from the open
        jsr db_load_x
        ldy IX_FILL
        bcs ix_drop
        lda IX_SLOTS,y
        cmp #'I'
        bne @bad
        lda IX_SLOTS+1,y
        cmp #'X'
        bne @bad
        lda IX_SLOTS+2,y
        dec                     ; the version, 1
        bne @bad
        jsr ix_fields
        bcs @bad
        cmp IX_SLOTS+3,y
        bne @bad
        jmp ix_width
@bad:
        lda #ERR_BAD_FORMAT
        ; fall into ix_drop

; ix_drop: frees the slot at IX_FILL and closes its file. Returns carry set and A as it came.
ix_drop:
        ldx IX_FILL
        stz IX_SLOTS,x
        pha
        lda IX_SLOTS+IX_HANDLE,x
        tax
        jsr API_CLOSE
        pla
        sec
        rts

; ix_create: makes the index at path r0 on the table, with the key fields at r1, 4 bytes, their
; numbers counting from 1, then 0s, and the flags X: $01 the keys are unique. Builds it from
; every record, opens it in the first free slot, and makes it the order, with no place in it.
; Returns X = the slot. Bad key fields or flags, or a key not unique, give error 13, and a
; fourth index error 4. A failed build deletes the file. Changes r0, r1 and the current record.
ix_create:
        phx                     ; the flags
        jsr ix_free
        plx
        bcc ix_build
        rts

; ix_build: ix_create in the free slot at IX_FILL, with Y = IX_FILL.
ix_build:
        cpx #2                  ; 0, or $01 unique
        bcc @flags
@bad:
        jmp db_bad_data
@done:
        rts
@flags:
        txa
        sta IX_SLOTS+15,y
        jsr ix_keep
        stz IX_LEFT             ; the key fields: the numbers not 0
        lda IX_FILL
        ora #3
        tax
        ldy #3
@copy:
        lda (r1),y
        sta IX_SLOTS+11,x
        beq @zero
        inc IX_LEFT
@zero:
        dex
        dey
        bpl @copy
        ldy IX_FILL
        lda IX_LEFT
        sta IX_SLOTS+10,y
        jsr ix_fields
        bcs @bad
        sta IX_SLOTS+3,y
        jsr ix_width
        lda #0                  ; no attributes
        jsr API_CREATE
        bcs @done
        txa
        ldx IX_FILL
        sta IX_SLOTS+IX_HANDLE,x
        lda #'I'
        sta IX_SLOTS,x
        lda #'X'
        sta IX_SLOTS+1,x
        lda #1                  ; the version, and the root, page 1
        sta IX_SLOTS+2,x
        sta IX_SLOTS+4,x
        stz IX_SLOTS+5,x
        lda #2                  ; the pages: 0 and 1
        sta IX_SLOTS+6,x
        stz IX_SLOTS+7,x
        stz IX_SLOTS+8,x        ; no free page
        stz IX_SLOTS+9,x
        txa
        jsr ix_turn             ; the order, while it is built
        jsr ix_blank
        lda #0                  ; page 0, its header written last
        tax
        ldy #>IX_NEW
        jsr ix_store
        bcs @fail
        inc IX_NEW+1            ; page 1, an empty leaf
        lda #1
        ldx #0
        ldy #>IX_NEW
        jsr ix_store
        bcs @fail
        stz DB_CURRENT
        stz DB_CURRENT+1
@record:
        lda DB_CURRENT          ; the next record
        ldx DB_CURRENT+1
        inc
        bne @number
        inx
        beq @built
@number:
        sta r0
        stx r0+1
        lda DB_HEADER+4         ; the records less r0
        cmp r0
        lda DB_HEADER+5
        sbc r0+1
        bcc @built
        jsr db_goto
        bcs @fail
        jsr ix_make
        jsr ix_insert
        bcc @record
@fail:
        jsr ix_drop
        pha
        lda #$FF
        jsr ix_turn
        jsr ix_name
        jsr API_DELETE
        pla
        sec
        rts
@built:
        jsr ix_brand
        bcs @fail
        lda IX_FILL
        jsr ix_turn
        ldy IX_FILL
        jmp ix_number

; ix_remake: after db_pack opens the table, builds again each index marked at IX_WORK, in its
; slot, from its path, then makes IX_KEEP the order, with no place in it. Returns r0 = the
; records, X = the fields; no record is current. A failed build stops there.
ix_remake:
        lda #0
@slot:
        sta IX_FILL
        tay
        lda IX_SLOTS+IX_WORK,y
        beq @next
        jsr ix_name             ; r0 = the path; carry clear
        lda IX_FILL             ; r1 = the key fields
        adc #<(IX_SLOTS + 11)
        sta r1
        lda #>(IX_SLOTS + 11)
        sta r1+1
        ldy IX_FILL
        ldx IX_SLOTS+15,y       ; the flags
        jsr ix_build
        bcs @done
@next:
        lda IX_FILL
        clc
        adc #32
        cmp #3 * 32
        bcc @slot
        lda IX_KEEP
        jsr ix_turn
        stz DB_CURRENT
        stz DB_CURRENT+1
        lda DB_HEADER+4
        sta r0
        lda DB_HEADER+5
        sta r0+1
        ldx DB_HEADER+3
@done:
        rts

; ix_keep: copies the path at r0, its length then its text, to the slot at IX_FILL's place in
; IX_NAMES, and points r0 at the copy. Changes A, X and Y.
ix_keep:
        lda r0
        sta db_ptr
        lda r0+1
        sta db_ptr+1
        jsr ix_name
        lda (db_ptr)
        tay
@copy:
        lda (db_ptr),y
        sta (r0),y
        dey
        cpy #$FF
        bne @copy
        rts

; ix_name: points r0 at the path of the slot at IX_FILL, in IX_NAMES. Returns carry clear.
; Changes A, X and Y.
ix_name:
        ldy IX_FILL
        jsr ix_number           ; X = the slot; carry clear
        txa
        adc #>IX_NAMES
        sta r0+1
        stz r0
        rts

; ix_free: needs a table, and puts the first free slot's offset at IX_FILL and in Y. Error 4
; when the 3 are open.
ix_free:
        jsr db_need
        bcs @done
        ldy #0
@free:
        lda IX_SLOTS,y
        beq @slot
        tya
        adc #32                 ; carry clear from db_need or the cpy
        tay
        cpy #3 * 32
        bcc @free
        lda #ERR_TOO_MANY_FILES
        rts
@slot:
        sty IX_FILL             ; carry clear
@done:
        rts

; ix_fields: checks the key fields of the slot at IX_FILL: 1 to 4 fields of the table, then 0s.
; Returns A = the key's length, cut to IX_MAX_KEY, and Y = IX_FILL, carry clear; carry set when
; they are bad. Changes r1 and X.
ix_fields:
        ldy IX_FILL
        lda IX_SLOTS+10,y       ; the key fields, 1 to 4
        sta IX_LEFT
        dec
        cmp #4
        bcs @done
        stz r1                  ; r1 = the key fields' lengths
        stz r1+1
        tya
        tax
@field:
        lda IX_SLOTS+11,x       ; a key field's number
        dec IX_LEFT
        bmi @zero
        dec                     ; 1 to the number of fields
        cmp DB_HEADER+3
        bcs @done
        inc
        phx
        tax
        jsr db_entry
        plx
        ldy #12
        lda (db_ptr),y          ; the field's length
        clc
        adc r1
        sta r1
        bcc @step
        inc r1+1
        bra @step
@zero:
        cmp #1                  ; past the key fields: 0
        bcs @done
@step:
        inx
        txa
        and #31                 ; the 4 numbers
        cmp #4
        bne @field
        ldy IX_FILL
        lda r1+1                ; the key's length: r1, cut to IX_MAX_KEY
        bne @cut
        lda r1
        cmp #IX_MAX_KEY + 1
        bcc @done
@cut:
        lda #IX_MAX_KEY
        clc
@done:
        rts

; ix_width: gives the slot at offset Y the width, the key's length A + 4, and the keys a page,
; then returns X = the slot, carry clear. ix_number returns X = the slot at offset Y. Change r1.
ix_width:
        clc
        adc #4
        sta IX_SLOTS+IX_WIDTH,y
        lda #<(512 - 4)         ; r1 = the page less its 4 bytes; X = the widths it holds
        sta r1
        lda #>(512 - 4)
        sta r1+1
        ldx #0
@take:
        lda r1
        sec
        sbc IX_SLOTS+IX_WIDTH,y
        sta r1
        bcs @kept
        dec r1+1
        bmi @full
@kept:
        inx
        bra @take
@full:
        txa
        sta IX_SLOTS+IX_CAP,y
ix_number:
        tya
        lsr
        lsr
        lsr
        lsr
        lsr
        tax
        clc
        rts

; ix_area: r0 = IX_SLOTS + A, with carry clear, and r1 = 16.
ix_area:
        adc #<IX_SLOTS
        sta r0
        lda #>IX_SLOTS
        sta r0+1
        lda #16
        sta r1
        stz r1+1
        rts

; ix_close: closes the index in slot X. The record order follows when it was the order.
ix_close:
        jsr ix_slot
        bcs @done
        stz IX_SLOTS,x
        cpx DB_ORDER
        bne @shut
        lda #$FF
        jsr ix_turn
@shut:
        lda IX_SLOTS+IX_HANDLE,x
        tax
        jmp API_CLOSE
@done:
        rts

; ix_shut: closes every open index.
ix_shut:
        ldx #2
@slot:
        phx
        jsr ix_close
        plx
        dex
        bpl @slot
        rts

; ix_slot: needs a table and an index open in slot X, 0 to 2, else error 6. Returns X = the
; slot's offset in IX_SLOTS.
ix_slot:
        jsr db_need
        bcs @done
        cpx #3
        bcs @bad
        txa
        asl
        asl
        asl
        asl
        asl
        tax
        lda IX_SLOTS,x
        bne @done               ; carry clear from the shifts
@bad:
        lda #ERR_BAD_HANDLE
        sec
@done:
        rts

; ix_order: makes the index in slot X the order, or the record order for X = $FF. In an index
; the place is lost: ix_next then gives the first record, and ix_prev the last.
ix_order:
        cpx #$FF
        beq @record
        jsr ix_slot
        bcs @done
        txa
        bra ix_turn
@done:
        rts
@record:
        jsr db_need
        bcs @done
        lda #$FF
        ; fall into ix_turn

; ix_turn: makes A the order, an index's offset in IX_SLOTS or $FF, with no place in it. Keeps X
; and Y.
ix_turn:
        sta DB_ORDER
        stz DB_SPOT
        stz IX_TOP
        stz IX_LOADED
        stz IX_LOADED+1
        clc
        rts

; ix_first: makes the first record of the order current. Returns r0 = it and X = its delete
; flag, or r0 = 0 when the order has none. Changes r1.
ix_first:
        jsr db_need
        bcs @done
        ldy DB_ORDER
        bpl ix_head
        lda #1
        ldx #0
        jmp ix_record
@done:
        rts

; ix_head: makes the index's first key current.
ix_head:
        jsr ix_root
        ; fall into ix_left

; ix_left: from the page at the top of the path, follows the first page below to a leaf, and
; makes its first key current. Returns at once with carry set.
ix_left:
        bcs @done
        lda IX_PAGE+1           ; the flags
        lsr
        bcs @leaf
        lda #0
        jsr ix_below
        bra ix_left
@leaf:
        lda IX_PAGE             ; the keys
        beq @none
        jmp ix_entry
@none:
        jmp ix_end
@done:
        rts

; ix_next: makes the record after the current one in the order current, or the first when none
; is. Returns r0 = it and X = its delete flag, or r0 = 0 past the last, where it stays. Changes
; r1.
; Trap: the place in an index is the index's own. db_goto does not move it; ix_place does.
ix_next:
        jsr db_need
        bcs @done
        bit DB_SPOT
        bmi @end
        ldy DB_ORDER
        bpl @index
        lda DB_CURRENT          ; the record order: the current record and 1
        ldx DB_CURRENT+1
        inc
        bne @record
        inx
        beq @end
@record:
        jmp ix_record
@index:
        ldy IX_TOP
        beq ix_head
        jsr ix_load
        bcs @done
        lda IX_PAGE+1           ; the flags
        lsr
        lda IX_PATH-1,y         ; the next key
        inc
        sta IX_PATH-1,y
        bcs @leaf
        jsr ix_below            ; a node: the first key below the next one
        jmp ix_left
@leaf:
        cmp IX_PAGE
        bcc @entry
        jsr ix_up
        bcs @done
        beq @end
@entry:
        jmp ix_entry
@end:
        jmp ix_end
@done:
        rts

; ix_last: makes the last record of the order current. Returns r0 = it and X = its delete flag,
; or r0 = 0 when the order has none. Changes r1.
ix_last:
        jsr db_need
        bcs @done
        ldy DB_ORDER
        bpl ix_tail
        lda DB_HEADER+4
        ldx DB_HEADER+5
        jmp ix_record
@done:
        rts

; ix_tail: makes the index's last key current.
ix_tail:
        jsr ix_root
        ; fall into ix_right

; ix_right: from the page at the top of the path, follows the last page below to a leaf, and
; makes its last key current. Returns at once with carry set.
ix_right:
        jsr ix_rightmost
        bcs @done
        dec                     ; the last key
        bmi @none
        sta IX_PATH-1,y
        jmp ix_entry
@none:
        jmp ix_end
@done:
        rts

; ix_rightmost: from the page at the top of the path, follows the last page below to a leaf.
; Returns A = its keys and Y = IX_TOP. Returns at once with carry set.
ix_rightmost:
        bcs @done
        lda IX_PAGE+1           ; the flags
        lsr
        lda IX_PAGE             ; the keys
        ldy IX_TOP
        bcs @leaf
        sta IX_PATH-1,y         ; past the last key
        jsr ix_below
        bra ix_rightmost
@leaf:
        clc
@done:
        rts

; ix_prev: makes the record before the current one in the order current, or the last when none
; is. Returns r0 = it and X = its delete flag, or r0 = 0 before the first, where it stays.
; Changes r1.
ix_prev:
        jsr db_need
        bcs @done
        bit DB_SPOT
        bvs @start
        ldy DB_ORDER
        bpl @index
        lda DB_CURRENT          ; the record order: the current record less 1
        ldx DB_CURRENT+1
        bne @less
        tay
        beq ix_last             ; none current
@less:
        sec
        sbc #1
        bcs @record
        dex
@record:
        jmp ix_record
@index:
        ldy IX_TOP
        beq ix_tail
        jsr ix_load
        bcs @done
        lda IX_PAGE+1           ; the flags
        lsr
        lda IX_PATH-1,y
        bcs @leaf
        jsr ix_below            ; a node: the last key below the current one
        jmp ix_right
@leaf:
        dec
        bpl @set
@up:
        ldy IX_TOP
        dey
        dey
        dey
        sty IX_TOP
        beq @start
        jsr ix_load
        bcs @done
        lda IX_PATH-1,y
        dec
        bmi @up
@set:
        sta IX_PATH-1,y
        jmp ix_entry
@start:
        jmp ix_start
@done:
        rts

; ix_place: puts the place in the order's index at the current record, for ix_next and ix_prev.
; Does nothing in the record order. Changes r0 and r1.
ix_place:
        jsr db_current
        bcs @done
        ldy DB_ORDER
        bmi @done               ; carry clear
        jsr ix_make
        jsr ix_aim
        bcs @done
        jmp ix_settle
@done:
        rts

; ix_find: makes current the first record of the index whose key starts with the key at r0, its
; length then its text, or is above it. Returns r0 = it and X = its delete flag; carry clear when
; its key starts with r0's, else carry set and A = 2. With no such key no record is current, and
; r0 = 0. The record order, or a key longer than the index's, gives error 13. Changes r1.
ix_find:
        jsr db_need
        bcs @done
        ldy DB_ORDER
        bmi @bad
        lda (r0)
        cmp IX_SLOTS+3,y        ; the index's key length
        beq @fits
        bcs @bad
@fits:
        ldx r0+1                ; ix_key = r0 less 1
        lda r0
        bne @less
        dex
@less:
        dec
        sta ix_key
        stx ix_key+1
        stz IX_EXACT
        jsr ix_descend
        bcs @done
        jsr ix_settle
        bcs @done
        beq @none
        lda IX_PATH-1,y
        jsr ix_point
        jsr ix_compare
        php
        jsr ix_entry
        bcs @fail
        plp
        bne @above
        clc
        rts
@fail:
        ply                     ; drops ix_compare's flags
        rts
@none:
        jsr ix_end
@above:
        lda #ERR_NOT_FOUND
        sec
@done:
        rts
@bad:
        jmp db_bad_data

; ix_descend: puts on the path the pages from the root to the leaf where the key at ix_key + 1
; belongs, each before its first key that is not below it. Carry set on an error.
ix_descend:
        jsr ix_root
@page:
        bcs @done
        lda #0
        jsr ix_point
@key:
        ldy IX_TOP
        lda IX_PATH-1,y
        cmp IX_PAGE
        bcs @stop               ; past the page's last key
        jsr ix_compare
        bcs @stop               ; the key is ix_key's or above it
        ldx IX_TOP
        inc IX_PATH-1,x
        jsr ix_step
        bra @key
@stop:
        lda IX_PAGE+1           ; the flags
        lsr
        bcs @leaf
        jsr ix_child            ; a node: the page before the key
        bra @page
@leaf:
        clc
@done:
        rts

; ix_aim: ix_descend to the entry in IX_ITEM, comparing the records after equal keys. Clears
; IX_SAME and IX_GREW.
ix_aim:
        lda #<(IX_ITEM - 2)
        sta ix_key
        lda #>(IX_ITEM - 2)
        sta ix_key+1
        lda #1
        sta IX_EXACT
        stz IX_SAME
        stz IX_GREW
        jmp ix_descend

; ix_make: builds the order's entry for the current record in IX_ITEM: the key, then the record
; and page 0. The key is the key fields' text, joined and cut to the key's length, with each N
; field rewritten to sort as a number. Puts the key's length at IX_SIZE. With IX_FROM set the
; key fields come from DB_OLD. IX_DIFF counts the key's bytes that changed.
ix_make:
        ldy DB_ORDER
        lda IX_SLOTS+3,y
        sta IX_SIZE
        lda IX_SLOTS+10,y
        sta IX_LEFT
        sty IX_FIELD
        stz IX_PUT
@field:
        dec IX_LEFT
        bmi @end
        ldx IX_FIELD
        inc IX_FIELD
        lda IX_SLOTS+11,x
        tax
        jsr db_field            ; db_ptr = the text less 1, Y = its length, A = its type
        bit IX_FROM
        bpl @text
        tax                     ; the text in DB_OLD
        clc
        lda db_ptr
        adc #<(DB_OLD - DB_RECORD)
        sta db_ptr
        lda db_ptr+1
        adc #>(DB_OLD - DB_RECORD)
        sta db_ptr+1
        txa
@text:
        sty IX_END
        stz IX_SIGN
        eor #'N'
        sta IX_KIND
        bne @first
@minus:
        lda (db_ptr),y          ; an N field: the place of its -
        cmp #'-'
        bne @scan
        sty IX_SIGN
@scan:
        dey
        bne @minus
        lda IX_SIGN
        beq @first
        lda #'-'                ; a negative number: the - first
        jsr ix_byte
        bcs @end
@first:
        ldy #1
@byte:
        cpy IX_SIGN
        beq @skip
        lda (db_ptr),y
        ldx IX_KIND
        bne @put
        cmp #' '                ; a space and the . count as 0
        beq @zero
        cmp #'.'
        bne @digit
@zero:
        lda #'0'
@digit:
        ldx IX_SIGN
        beq @put
        eor #$FF                ; a negative number: 9 less each digit, $69 less it
        adc #$69                ; carry set from the cmp
@put:
        jsr ix_byte
        bcs @end
@skip:
        iny
        dec IX_END
        bne @byte
        bra @field
@end:
        ldx IX_SIZE
        lda DB_CURRENT
        sta IX_ITEM,x
        lda DB_CURRENT+1
        sta IX_ITEM+1,x
        stz IX_ITEM+2,x
        stz IX_ITEM+3,x
        rts

; ix_byte: adds A to the key in IX_ITEM, and counts at IX_DIFF a byte not already there. Carry
; set when the key is full. Changes X.
ix_byte:
        ldx IX_PUT
        cmp IX_ITEM,x
        beq @same
        sta IX_ITEM,x
        inc IX_DIFF
@same:
        inx
        stx IX_PUT
        cpx IX_SIZE
        rts

; ix_insert: adds the entry in IX_ITEM to the order's index. Splits each page that overflows,
; and the root with a new root above it. Writes the pages, and the header when it changed. A key
; already in a unique index gives error 13. Changes r0 and r1, and loses the place in the index.
ix_insert:
        jsr ix_aim
        bcs @done
        ldy DB_ORDER
        lda IX_SLOTS+15,y       ; the flags
        and IX_SAME
        beq ix_level
        jmp db_bad_data         ; unique, and the key is there
@done:
        rts

; ix_level: puts the entry in IX_ITEM in IX_PAGE, the page at the top of the path, as the path's
; key, then falls into ix_spill.
ix_level:
        ldy IX_TOP
        lda IX_PATH-1,y
        jsr ix_gap
        ; fall into ix_spill

; ix_spill: writes IX_PAGE, the page at the top of the path. A page past IX_CAP keys splits, and
; the entry that goes up is put in the page above, up to a new root. Writes the header when it
; changed. Changes r0 and r1.
ix_spill:
        ldy DB_ORDER
        lda IX_SLOTS+IX_CAP,y
        cmp IX_PAGE
        bcs @fits
        jsr ix_split
        bcs @done
        ldy IX_TOP              ; the key that went up, to the page above
        dey
        dey
        dey
        sty IX_TOP
        beq @root
        jsr ix_load
        bcc ix_level
        rts
@fits:
        jsr ix_flush
        bcs @done
@brand:
        lda IX_GREW
        beq @done
        jmp ix_brand
@root:
        jsr ix_blank            ; a new root: one key, the old root below it
        inc IX_NEW
        ldy DB_ORDER
        lda IX_SLOTS+4,y
        sta IX_NEW+2
        lda IX_SLOTS+5,y
        sta IX_NEW+3
        lda #<(IX_ITEM - 2)
        sta db_ptr
        lda #>(IX_ITEM - 2)
        sta db_ptr+1
        lda #<(IX_NEW + 2)
        sta ix_key
        lda #>(IX_NEW + 2)
        sta ix_key+1
        jsr ix_copy
        jsr ix_alloc
        bcs @done
        ldy DB_ORDER
        sta IX_SLOTS+4,y
        pha
        txa
        sta IX_SLOTS+5,y
        pla
        ldy #>IX_NEW
        jsr ix_store
        bcc @brand
@done:
        rts

; ix_update: brings each open index in step with the current record, before db_write writes it.
; An appended record's entry is added. When a record's key changed, its old entry, made from
; DB_OLD, is deleted and the new one added. A key already in a unique index gives error 13 before
; any index changes. Keeps the order; in an index the place moves to the current record. Reads
; the record as the file holds it to DB_OLD. Changes r0 and r1.
ix_update:
        lda IX_SLOTS
        ora IX_SLOTS+32
        ora IX_SLOTS+64
        bne @open
        clc
        rts
@open:
        lda DB_ORDER
        sta IX_KEEP
        lda DB_HEADER+4         ; the file holds the record when the records reach it
        cmp DB_CURRENT
        lda DB_HEADER+5
        sbc DB_CURRENT+1
        lda #0
        rol
        sta IX_HAD
        beq @check
        jsr db_seek
        bcs @fail
        jsr db_record
        lda #<DB_OLD
        sta r0
        lda #>DB_OLD
        sta r0+1
        jsr db_load
        bcs @fail
@check:
        lda #0                  ; first each index's work, and the unique keys
@test:
        jsr ix_turn
        tay
        lda IX_SLOTS,y
        beq @mark               ; not open: no work
        lda #1                  ; an appended record: work
        sta IX_DIFF
        lda IX_HAD
        beq @new
        lda #$80                ; else the old key, then the new one's changes
        sta IX_FROM
        jsr ix_make
        stz IX_FROM
        stz IX_DIFF
@new:
        jsr ix_make
        lda IX_DIFF
        beq @mark
        ldy DB_ORDER
        lda IX_SLOTS+15,y       ; the flags
        lsr
        bcc @work
        jsr ix_aim
        bcs @fail
        lda IX_SAME
        bne @bad                ; unique, and the key is there
@work:
        lda #1
@mark:
        ldy DB_ORDER
        sta IX_SLOTS+IX_WORK,y
        lda DB_ORDER
        clc
        adc #32
        cmp #3 * 32
        bcc @test
        bra @second
@bad:
        lda #ERR_BAD_DATA
@fail:
        pha
        lda IX_KEEP
        jsr ix_turn
        pla
        sec
        rts
@second:
        lda #0                  ; then the work
@apply:
        jsr ix_turn
        tay
        lda IX_SLOTS+IX_WORK,y
        beq @next
        lda IX_HAD
        beq @add
        lda #$80
        sta IX_FROM
        jsr ix_make
        stz IX_FROM
        jsr ix_delete
        bcs @fail
@add:
        jsr ix_make
        jsr ix_insert
        bcs @fail
@next:
        lda DB_ORDER
        clc
        adc #32
        cmp #3 * 32
        bcc @apply
        lda IX_KEEP             ; the order again, at the current record
        jsr ix_turn
        tay
        bmi @done
        jsr ix_make
        jsr ix_aim
        bcs @done
        jmp ix_settle
@done:
        rts

; ix_delete: removes the entry in IX_ITEM from the order's index. An entry in a node takes the
; place of the last entry below it, which leaves its leaf. Then ix_mend. An entry not in the
; index gives error 11. Changes r0 and r1, and loses the place in the index.
ix_delete:
        jsr ix_aim
        bcs @done
        jsr ix_settle
        bcs @done
        beq @missing
        lda IX_PATH-1,y
        jsr ix_point
        jsr ix_compare
        beq @found
@missing:
        lda #ERR_BAD_FORMAT
        sec
@done:
        rts
@found:
        lda IX_PAGE+1           ; the flags
        lsr
        bcs @leaf
        ldy IX_TOP              ; a node: the last entry below the entry to IX_ITEM
        sty IX_HOLE
        lda IX_PATH-1,y
        jsr ix_below
        jsr ix_rightmost        ; A = the leaf's keys
        bcs @done
        dec
        sta IX_PATH-1,y
        jsr ix_point
        lda #<(IX_ITEM - 2)
        sta ix_key
        lda #>(IX_ITEM - 2)
        sta ix_key+1
        jsr ix_copy
        ldx IX_TOP              ; to the node, keeping the leaf's place
        lda IX_HOLE
        stx IX_HOLE
        sta IX_TOP
        jsr ix_load
        bcs @done
        lda IX_PATH-1,y
        jsr ix_point
        lda db_ptr              ; ix_key = the entry less 2
        sta ix_key
        lda db_ptr+1
        sta ix_key+1
        ldy DB_ORDER            ; the entry keeps its page above
        lda IX_SLOTS+IX_WIDTH,y
        tax
        tay
        lda (ix_key),y
        sta IX_ITEM-2,x
        iny
        lda (ix_key),y
        sta IX_ITEM-1,x
        lda #<(IX_ITEM - 2)
        sta db_ptr
        lda #>(IX_ITEM - 2)
        sta db_ptr+1
        jsr ix_copy
        jsr ix_flush
        bcs @done
        lda IX_HOLE             ; the leaf again
        sta IX_TOP
        jsr ix_load
        bcs @done
@leaf:
        ldy IX_TOP
        lda IX_PATH-1,y
        jsr ix_cut
        jmp ix_mend

; ix_mend: after ix_cut, writes IX_PAGE, the page at the top of the path. A page left with no
; keys takes the key between it and the page beside it from the page above, and goes into the
; page beside, then to the free list; the page beside splits when it overflows. Then the page
; above, which lost that key, is mended the same way. A root node left with no keys gives way to
; its page below. Writes the header when it changed. Changes r0 and r1.
ix_mend:
        lda IX_PAGE
        beq @none
@spill:
        jmp ix_spill            ; keys left
@none:
        ldy IX_TOP
        cpy #3
        bne @empty
        lda IX_PAGE+1           ; the root: a leaf stays, with no keys
        lsr
        bcs @spill
        ldy DB_ORDER            ; a node: its page below is the root
        lda IX_PAGE+2
        sta IX_SLOTS+4,y
        lda IX_PAGE+3
        sta IX_SLOTS+5,y
        lda IX_PATH
        ldx IX_PATH+1
        jsr ix_give
        bcs @done
        jmp ix_brand
@done:
        rts
@empty:
        lda IX_PATH-3,y         ; the empty page, and its page below
        sta IX_GONE
        lda IX_PATH-2,y
        sta IX_GONE+1
        lda IX_PAGE+2
        sta IX_HOLD
        lda IX_PAGE+3
        sta IX_HOLD+1
        jsr ix_pop              ; the page above
        bcs @done
        stz IX_SIDE
        lda IX_PATH-1,y         ; the key the empty page is below
        cmp IX_PAGE
        bcc @right
        dec IX_SIDE             ; past the last key: the page beside is before it
        dec
        sta IX_PATH-1,y
        jsr ix_point
        bra @take
@right:
        jsr ix_point            ; the key's page above, beside it, is now below it
        ldy DB_ORDER
        lda IX_SLOTS+IX_WIDTH,y
        tay
        lda (db_ptr),y
        sta (db_ptr)
        iny
        lda (db_ptr),y
        ldy #1
        sta (db_ptr),y
@take:
        lda #<(IX_ITEM - 2)     ; the key between them to IX_ITEM
        sta ix_key
        lda #>(IX_ITEM - 2)
        sta ix_key+1
        jsr ix_copy
        ldy IX_TOP
        lda IX_PATH-1,y
        jsr ix_cut
        lda IX_PAGE
        sta IX_ABOVE
        jsr ix_flush
        bcs @done
        ldy IX_TOP              ; the page beside, on the path in the empty page's place
        lda IX_PATH-1,y
        jsr ix_below
        bcs @done
        ldy DB_ORDER
        ldx IX_SLOTS+IX_WIDTH,y
        bit IX_SIDE
        bmi @last
        lda IX_PAGE+2           ; first: its page above is the page beside's first page below,
        sta IX_ITEM-2,x         ; whose place the empty page's page below takes
        lda IX_PAGE+3
        sta IX_ITEM-1,x
        lda IX_HOLD
        sta IX_PAGE+2
        lda IX_HOLD+1
        sta IX_PAGE+3
        lda #0
        bra @merge
@last:
        lda IX_HOLD             ; last: its page above is the empty page's page below
        sta IX_ITEM-2,x
        lda IX_HOLD+1
        sta IX_ITEM-1,x
        lda IX_PAGE
@merge:
        jsr ix_gap
        lda IX_GONE
        ldx IX_GONE+1
        jsr ix_give
        bcs @end
        ldy DB_ORDER
        lda IX_SLOTS+IX_CAP,y
        cmp IX_PAGE
        bcs @fits
        jmp ix_spill            ; it splits, and the key that goes up returns to the page above
@fits:
        jsr ix_flush
        bcs @end
        lda IX_ABOVE
        beq @up
        jmp ix_brand
@up:
        jsr ix_pop              ; the page above has no keys
        bcs @end
        jmp ix_mend
@end:
        rts

; ix_pop: drops the top level of the path, and loads the page now at the top. Returns Y = IX_TOP.
ix_pop:
        ldy IX_TOP
        dey
        dey
        dey
        sty IX_TOP
        jmp ix_load

; ix_cut: removes key A from IX_PAGE, moves the keys after it down one, and fills the bytes freed
; with 0s. The page below the key stays. Changes X and Y.
ix_cut:
        sta IX_AT
        lda IX_PAGE             ; the keys after it
        clc
        sbc IX_AT
        sta IX_MOVES
        lda IX_AT
        jsr ix_point
@move:
        dec IX_MOVES
        bmi @clear
        lda db_ptr
        sta ix_key
        lda db_ptr+1
        sta ix_key+1
        jsr ix_step
        jsr ix_copy
        bra @move
@clear:
        ldy DB_ORDER
        lda IX_SLOTS+IX_WIDTH,y
        tay
        iny
        lda #0
@zero:
        sta (db_ptr),y
        dey
        cpy #2
        bcs @zero
        dec IX_PAGE
        rts

; ix_gap: puts the entry in IX_ITEM in IX_PAGE as key A, and moves the keys from A on up one.
; Changes X and Y.
ix_gap:
        sta IX_AT
        lda IX_PAGE
        sec
        sbc IX_AT
        sta IX_MOVES
        lda IX_PAGE
        jsr ix_point            ; past the last key, less 2
@move:
        lda db_ptr
        sta ix_key
        lda db_ptr+1
        sta ix_key+1
        dec IX_MOVES
        bmi @put
        jsr ix_back
        jsr ix_copy
        bra @move
@put:
        lda #<(IX_ITEM - 2)
        sta db_ptr
        lda #>(IX_ITEM - 2)
        sta db_ptr+1
        jsr ix_copy
        inc IX_PAGE
        rts

; ix_split: splits IX_PAGE, at the top of the path, of one key more than a page holds. The first
; half of the keys stays, the key after them goes to IX_ITEM, and the rest go to a new page,
; which becomes IX_ITEM's page above. Writes both pages. Changes r0 and r1.
ix_split:
        jsr ix_blank
        lda IX_PAGE+1           ; the flags
        sta IX_NEW+1
        lda IX_PAGE             ; the keys that stay: half, rounded down
        lsr
        sta IX_AT
        lda IX_PAGE             ; the keys that go: the rest less the one that goes up
        clc
        sbc IX_AT
        sta IX_NEW
        sta IX_MOVES
        lda IX_AT
        sta IX_PAGE
        jsr ix_point
        lda #<(IX_ITEM - 2)
        sta ix_key
        lda #>(IX_ITEM - 2)
        sta ix_key+1
        jsr ix_copy             ; the key that goes up
        ldy DB_ORDER
        ldx IX_SLOTS+IX_WIDTH,y
        lda IX_ITEM-2,x         ; its page above is the new page's page below
        sta IX_NEW+2
        lda IX_ITEM-1,x
        sta IX_NEW+3
        lda #<(IX_NEW + 2)
        sta ix_key
        lda #>(IX_NEW + 2)
        sta ix_key+1
@move:
        dec IX_MOVES
        bmi @moved
        jsr ix_step
        jsr ix_copy
        ldy DB_ORDER
        clc
        lda ix_key
        adc IX_SLOTS+IX_WIDTH,y
        sta ix_key
        bcc @move
        inc ix_key+1
        bra @move
@moved:
        lda IX_PAGE             ; 0s past the keys that stay
        jsr ix_point
        lda db_ptr              ; Y = the first 0's offset in its half of the page
        clc
        adc #2
        tay
        lda db_ptr+1
        adc #0
        cmp #>(IX_PAGE + 256)
        lda #0
        bcs @high
@low:
        sta IX_PAGE,y
        iny
        bne @low
@high:
        sta IX_PAGE+256,y
        iny
        bne @high
        jsr ix_alloc
        bcs @done
        ldy DB_ORDER
        pha
        lda IX_SLOTS+IX_WIDTH,y
        tay
        pla
        sta IX_ITEM-2,y
        pha
        txa
        sta IX_ITEM-1,y
        pla
        ldy #>IX_NEW
        jsr ix_store
        bcs @done
        jmp ix_flush
@done:
        rts

; ix_alloc: takes a page for the order's index: the first free page, else the page past the
; last. Returns it in X A; carry set on an error. Changes r0 and r1.
ix_alloc:
        inc IX_GREW
        ldy DB_ORDER
        lda IX_SLOTS+8,y        ; the first free page
        ldx IX_SLOTS+9,y
        bne @free
        tay
        bne @free
        ldy DB_ORDER            ; none: the page past the last, and one more page
        lda IX_SLOTS+6,y
        ldx IX_SLOTS+7,y
        pha
        inc
        sta IX_SLOTS+6,y
        bne @end
        txa
        inc
        sta IX_SLOTS+7,y
@end:
        pla
        clc
        rts
@free:
        jsr ix_link             ; the next free page, from the free page's first 2 bytes
        bcs @done
        jsr db_load_x
        bcs @done
        lda IX_TAKE
        ldx IX_TAKE+1
@done:
        rts

; ix_give: puts page X A of the order's index first on its free list: writes the first free page
; in the page's first 2 bytes. Changes r0 and r1.
ix_give:
        jsr ix_link
        bcs @done
        jsr db_save_x
        bcs @done
        ldy DB_ORDER
        lda IX_TAKE
        sta IX_SLOTS+8,y
        lda IX_TAKE+1
        sta IX_SLOTS+9,y
        inc IX_GREW
@done:
        rts

; ix_link: keeps page X A at IX_TAKE, and moves the order's index to it. Gives r0 = the slot's
; first free page and r1 = 2, X = the handle. Carry set on an error.
ix_link:
        sta IX_TAKE
        stx IX_TAKE+1
        jsr ix_seek
        bcs @done
        lda DB_ORDER            ; carry clear from the seek
        adc #8
        jsr ix_area
        lda #2
        sta r1
@done:
        rts

; ix_copy: copies the order's width of bytes from db_ptr + 2 to ix_key + 2. Changes A and Y.
ix_copy:
        ldy DB_ORDER
        lda IX_SLOTS+IX_WIDTH,y
        tay
        iny
@byte:
        lda (db_ptr),y
        sta (ix_key),y
        dey
        cpy #2
        bcs @byte
        rts

; ix_back: moves db_ptr back by the order's width, to the key before. Keeps X.
ix_back:
        ldy DB_ORDER
        sec
        lda db_ptr
        sbc IX_SLOTS+IX_WIDTH,y
        sta db_ptr
        bcs @done
        dec db_ptr+1
@done:
        rts

; ix_blank: fills IX_NEW with 0s. Changes X.
ix_blank:
        ldx #0
@zero:
        stz IX_NEW,x
        stz IX_NEW+256,x
        inx
        bne @zero
        rts

; ix_brand: writes the order's slot's 16 bytes at the start of its file. Changes r0 and r1.
ix_brand:
        lda #0
        tax
        jsr ix_seek
        bcs @done
        lda DB_ORDER            ; carry clear from the seek
        jsr ix_area
        jmp db_save_x
@done:
        rts

; ix_flush: writes IX_PAGE to the page at the top of the path. Changes r0 and r1.
ix_flush:
        ldy IX_TOP
        lda IX_PATH-3,y
        ldx IX_PATH-2,y
        ldy #>IX_PAGE
        ; fall into ix_store

; ix_store: writes the 512 bytes at Y * 256 to page X A of the order's index. Changes r0 and r1.
ix_store:
        phy
        jsr ix_seek
        ply
        bcs @done
        jsr ix_span
        jmp db_save_x
@done:
        rts

; ix_seek: moves the order's index to page X A: r0 r1 = the page * 512. Returns X = its handle.
; Changes Y.
ix_seek:
        stz r0
        asl
        sta r0+1
        txa
        rol
        sta r1
        lda #0
        rol
        sta r1+1
        ldy DB_ORDER
        ldx IX_SLOTS+IX_HANDLE,y
        phx
        lda #0                  ; from the start
        jsr API_SEEK
        plx
        rts

; ix_span: r0 = Y * 256, r1 = 512.
ix_span:
        stz r0
        sty r0+1
        stz r1
        lda #>512
        sta r1+1
        rts

; ix_entry: makes current the record of the key at the top of the path.
ix_entry:
        ldy IX_TOP
        lda IX_PATH-1,y
        jsr ix_point
        ldy DB_ORDER
        lda IX_SLOTS+IX_WIDTH,y
        tay
        dey                     ; the record, after the key
        lda (db_ptr),y
        sta r0+1
        dey
        lda (db_ptr),y
        sta r0
        bra ix_go

; ix_record: makes record X A current in the record order. Record 0 is before the first, and a
; record past the last is past the last.
ix_record:
        sta r0
        stx r0+1
        ora r0+1
        beq ix_start
        lda DB_HEADER+4         ; the records less r0
        cmp r0
        lda DB_HEADER+5
        sbc r0+1
        bcs ix_go
        ; fall into ix_end

; ix_end and ix_start: leave no record current, past the last of the order or before the first.
; Return r0 = 0.
ix_end:
        lda #$80
        bra ix_edge
ix_start:
        lda #$40
ix_edge:
        sta DB_SPOT
        stz IX_TOP
        stz DB_CURRENT
        stz DB_CURRENT+1
        stz r0
        stz r0+1
        clc
        rts

; ix_go: makes record r0 current, and returns r0 = it and X = its delete flag.
ix_go:
        jsr db_goto
        bcs @done
        lda DB_CURRENT
        sta r0
        lda DB_CURRENT+1
        sta r0+1
@done:
        rts

; ix_settle: after ix_descend, when the path stands past its leaf's last key, drops levels to the
; next key up the path. Returns Z set when none is left; else Y = IX_TOP. Carry set on an error.
ix_settle:
        ldy IX_TOP
        lda IX_PATH-1,y
        cmp IX_PAGE
        bcs ix_up
        rts                     ; carry and Z clear

; ix_up: drops levels from the path until one stands before a key of its page. Returns Z set when
; none is left; else that page loaded and Y = IX_TOP. Carry set on an error.
ix_up:
        ldy IX_TOP
        dey
        dey
        dey
        sty IX_TOP
        bne @load
        clc
        rts
@load:
        jsr ix_load
        bcs @done
        lda IX_PATH-1,y
        cmp IX_PAGE
        bcs ix_up
@done:
        rts

; ix_below: puts the page below key A of IX_PAGE, the page before it, on the path, and loads it.
ix_below:
        jsr ix_point
        ; fall into ix_child

; ix_child: puts the page at db_ptr on the path, and loads it.
ix_child:
        ldy #1
        lda (db_ptr),y
        tax
        lda (db_ptr)
        bra ix_push

; ix_root: puts the index's root alone on the path, and loads it.
ix_root:
        stz IX_TOP
        ldy DB_ORDER
        lda IX_SLOTS+4,y
        ldx IX_SLOTS+5,y
        ; fall into ix_push

; ix_push: puts page X A on the path, before its first key, and loads it. A path past IX_DEEP
; levels gives error 11.
ix_push:
        ldy IX_TOP
        cpy #3 * IX_DEEP
        bcc @room
        lda #ERR_BAD_FORMAT
        rts
@room:
        sta IX_PATH,y
        txa
        sta IX_PATH+1,y
        lda #0
        sta IX_PATH+2,y
        iny
        iny
        iny
        sty IX_TOP
        ; fall into ix_load

; ix_load: reads the page at the top of the path to IX_PAGE, unless it is there. Returns Y =
; IX_TOP. Changes r0, r1 and X.
ix_load:
        ldy IX_TOP
        lda IX_PATH-3,y
        ldx IX_PATH-2,y
        cmp IX_LOADED
        bne @read
        cpx IX_LOADED+1
        beq @ok
@read:
        stz IX_LOADED           ; none until the read ends
        stz IX_LOADED+1
        jsr ix_seek
        bcs @done
        ldy #>IX_PAGE
        jsr ix_span
        jsr db_load_x
        bcs @done
        ldy IX_TOP
        lda IX_PATH-3,y
        sta IX_LOADED
        lda IX_PATH-2,y
        sta IX_LOADED+1
@ok:
        clc
@done:
        rts

; ix_point: points db_ptr at the page below key A of IX_PAGE, the 2 bytes before the key:
; IX_PAGE + 2 + A * the width. Changes X and Y.
ix_point:
        tax
        lda #<(IX_PAGE + 2)
        sta db_ptr
        lda #>(IX_PAGE + 2)
        sta db_ptr+1
        inx
@add:
        dex
        beq @done
        jsr ix_step
        bra @add
@done:
        rts

; ix_step: moves db_ptr on by the order's width, to the next key. Keeps X.
ix_step:
        ldy DB_ORDER
        clc
        lda db_ptr
        adc IX_SLOTS+IX_WIDTH,y
        sta db_ptr
        bcc @done
        inc db_ptr+1
@done:
        rts

; ix_compare: compares the key at ix_key + 1, its length then its text, with as many bytes of the
; key at db_ptr + 2. Z set when they match; else carry set when the key at db_ptr + 2 is above.
; With IX_EXACT set, the records after equal keys are compared too, and IX_SAME is set. Changes
; X and Y.
ix_compare:
        sec
        ldy #1
        lda (ix_key),y          ; the length
        beq @done
        tax
@byte:
        iny
        lda (db_ptr),y
        cmp (ix_key),y
        bne @done
        dex
        bne @byte
        lda IX_EXACT
        beq @done
        sta IX_SAME
        iny                     ; the record's high byte
        iny
        lda (db_ptr),y
        cmp (ix_key),y
        bne @done
        dey
        lda (db_ptr),y
        cmp (ix_key),y
@done:
        rts

; db_seek: moves the table's file to the current record: the header's length + (the record
; - 1) * the record's length. Changes r0 and r1.
db_seek:
        lda DB_CURRENT          ; db_ptr = the record - 1
        sec
        sbc #1
        sta db_ptr
        lda DB_CURRENT+1
        sbc #0
        sta db_ptr+1
        stz r0                  ; r0 r1 = db_ptr * the record's length
        stz r0+1
        stz r1
        stz r1+1
        ldy #16
@bit:
        asl r0
        rol r0+1
        rol r1
        rol r1+1
        asl db_ptr
        rol db_ptr+1
        bcc @next
        ldx #8                  ; the record's length
        jsr db_add
@next:
        dey
        bne @bit
        ldx #6                  ; the header's length
        jsr db_add
        ldx DB_HANDLE
        lda #0                  ; from the start
        jmp API_SEEK

; db_add: adds the 2 bytes at DB_HEADER + X to r0 r1. Changes A.
db_add:
        clc
        lda r0
        adc DB_HEADER,x
        sta r0
        lda r0+1
        adc DB_HEADER+1,x
        sta r0+1
        bcc @done
        inc r1
        bne @done
        inc r1+1
@done:
        rts

; db_record: r0 = the current record in the workspace, r1 = the record's length.
db_record:
        lda #<DB_RECORD
        sta r0
        lda #>DB_RECORD
        sta r0+1
        lda DB_HEADER+8
        sta r1
        lda DB_HEADER+9
        sta r1+1
        rts

; db_stamp: puts today's date in the header. Changes r0.
db_stamp:
        jsr API_GETDATE
        stx DB_HEADER+11        ; the month
        sty DB_HEADER+12        ; the day
        lda r0
        sec
        sbc #<2000
        sta DB_HEADER+10
        rts

; db_load: reads r1 bytes from the table's file to r0; db_load_x reads them from file X. A file
; that ends first gives error 11.
; db_save: writes r1 bytes at r0 to the table's file; db_save_x writes them to file X. A short
; write gives error 29.
; All change X and r1.
db_load:
        ldx DB_HANDLE
db_load_x:
        jsr db_want
        jsr API_READ
        ldy #ERR_BAD_FORMAT
        bra db_count
db_save:
        ldx DB_HANDLE
db_save_x:
        jsr db_want
        jsr API_WRITE
        ldy #ERR_WRITE_FAULT
db_count:
        bcs @done
        lda r1
        eor DB_WANT
        bne @short
        lda r1+1
        eor DB_WANT+1
        beq @done               ; carry clear from the call
@short:
        tya
        sec
@done:
        rts

; db_want: keeps r1 at DB_WANT. Keeps X.
db_want:
        lda r1
        sta DB_WANT
        lda r1+1
        sta DB_WANT+1
        rts

; db_need: carry clear when the workspace holds a table: its header starts with DB and the
; version. Else carry set and A = 6. Keeps X.
db_need:
        ldy #2
@check:
        lda DB_HEADER,y
        cmp db_magic,y
        bne @none
        dey
        bpl @check
        clc
        rts
@none:
        lda #ERR_BAD_HANDLE
        sec
        rts

db_magic:
        .byte "DB", DB_VERSION

nmi5:
        rti

.segment "FARIRQ5"

irq_entry5:
        FAR_IRQ_ENTRY
        FAR_IRQ_EXIT

; The vector pull selects bank 0, so these serve only a machine that does not.
.segment "B5VECTORS"

        .word nmi5
        .word nmi5              ; reset selects bank 0
        .word irq_entry5
