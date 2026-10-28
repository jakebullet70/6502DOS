; DBPACK: call 57, db, packs the table PACK.DB, and DBPACK.PY checks it after the run. Keeps
; A, X, the flags N, Z and C, $00, and r0 after each call at RESULTS, 6 bytes a call, for
; DBPACK.IN to dump. Each $00 must be the bank selected at the start.
; 1: pack with no table: error 6. 2: create PACK.DB, 1 field.
; 3 to 14: append, put and write A, B, C and D.
; 15 to 17: goto 2, flag 1, write. 18 to 20: goto 4, flag 1, write.
; 21: pack: X = 1, r0 = 2. 22: get with no record current: error 13.
; 23, 24: goto 2, get NAME to BUF1: C. 25: close. 26: open PACK.DB: X = 1, r0 = 2.
; 27: pack again, nothing deleted: r0 = 2. 28: close.

.setcpu "65C02"

.include "api.inc"

RAM_BANK = $00
r0      = $02
r1      = $04
index   = $50                   ; the offset of the next result
first   = $51                   ; the bank selected at the start
table   = $52                   ; the workspace's bank
keep_a  = $53
keep_x  = $54
RESULTS = $1400
BUF1    = $1500

.macro set value
        lda #<(value)
        sta r0
        lda #>(value)
        sta r0+1
.endmacro

.macro db function, field
        ldx #field
        ldy #function
        lda table
        jsr API_DB
        jsr save
.endmacro

; add: appends a record, puts the text at value in NAME, and writes it.
.macro add value
        db DB_APPEND, 0
        set value
        db DB_PUT, 1
        db DB_WRITE, 0
.endmacro

; drop: makes record number current, marks it deleted, and writes it.
.macro drop number
        set number
        db DB_GOTO, 0
        db DB_FLAG, 1
        db DB_WRITE, 0
.endmacro

        lda RAM_BANK
        sta first
        stz index
        lda #1
        jsr API_BANK_ALLOC
        sta table
        db DB_PACK, 0           ; 1
        set path                ; 2
        lda #<fields
        sta r1
        lda #>fields
        sta r1+1
        db DB_CREATE, 1
        add text_a              ; 3 to 5
        add text_b              ; 6 to 8
        add text_c              ; 9 to 11
        add text_d              ; 12 to 14
        drop 2                  ; 15 to 17
        drop 4                  ; 18 to 20
        db DB_PACK, 0           ; 21
        set BUF1                ; 22
        db DB_GET, 1
        set 2                   ; 23
        db DB_GOTO, 0
        set BUF1                ; 24
        db DB_GET, 1
        db DB_CLOSE, 0          ; 25
        set path                ; 26
        db DB_OPEN, 0
        db DB_PACK, 0           ; 27
        db DB_CLOSE, 0          ; 28
        lda table
        jsr API_BANK_FREE
        lda first
        sta RAM_BANK
        rts

; save: keeps A, X, the flags N, Z and C, $00 and r0 at the next result.
save:
        php
        sta keep_a
        stx keep_x
        ldy index
        lda keep_a
        sta RESULTS,y
        lda keep_x
        sta RESULTS+1,y
        pla
        and #$83                ; N, Z and C
        sta RESULTS+2,y
        lda RAM_BANK
        sta RESULTS+3,y
        lda r0
        sta RESULTS+4,y
        lda r0+1
        sta RESULTS+5,y
        tya
        clc
        adc #6
        sta index
        rts

; The field table's entry: the name, then 0 to 11 bytes, the type, the length, the decimals and
; the offset, which db_create works out.
fields:
        .byte "NAME"
        .res 7, 0
        .byte 'C', 4, 0
        .word $FFFF

path:   .byte 7, "PACK.DB"
text_a: .byte 1, "A"
text_b: .byte 1, "B"
text_c: .byte 1, "C"
text_d: .byte 1, "D"
