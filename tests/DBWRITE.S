; DBWRITE: call 57, db, writes the table NEW.DB, and DBWRITE.PY checks it after the run. Keeps
; A, X, the flags N, Z and C, $00, and r0 after each call at RESULTS, 6 bytes a call, for
; DBWRITE.IN to dump. Each $00 must be the bank selected at the start.
; 1: create with 0 fields: error 13. 2: a field of length 0: error 13.
; 3: a record of 1001 bytes: error 13. 4: create NEW.DB, 4 fields.
; 5: get with no record current: error 13. 6: goto 1 of 0 records: error 13.
; 7: append: r0 = 1. 8 to 11: put NAME, AGE, OK and BORN.
; 12: put 11 characters in NAME: error 13. 13: put field 0: error 13. 14: write.
; 15 to 17: append, r0 = 2, put NAME, write. 18 to 21: append, r0 = 3, put NAME and AGE, write.
; 22: goto 2: X = ' '. 23: flag 2: error 13. 24: flag 1. 25: write.
; 26: goto 1. 27: put NAME again, shorter. 28: write. 29: get NAME to BUF1. 30: close.
; 31: flag with no table: error 6.
; 32: open NEW.DB: X = 4, r0 = 3. 33: goto 2: X = '*'.
; 34, 35: goto 3, get AGE to BUF2. 36: get OK to BUF3. 37: close.

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
BUF2    = $1520
BUF3    = $1540

.macro set value
        lda #<(value)
        sta r0
        lda #>(value)
        sta r0+1
.endmacro

.macro create fields, count
        set new
        lda #<fields
        sta r1
        lda #>fields
        sta r1+1
        db DB_CREATE, count
.endmacro

.macro db function, field
        ldx #field
        ldy #function
        lda table
        jsr API_DB
        jsr save
.endmacro

; A field table's entry: the name, then 0 to 11 bytes, the type, the length and the decimals.
; The offset is $FFFF: db_create works it out.
.macro field name, type, length, decimals
        .byte name
        .res 11 - .strlen(name), 0
        .byte type, length, decimals
        .word $FFFF
.endmacro

        lda RAM_BANK
        sta first
        stz index
        lda #1
        jsr API_BANK_ALLOC
        sta table
        create fields, 0        ; 1
        create zero, 2          ; 2
        create big, 4           ; 3
        create fields, 4        ; 4
        set BUF1                ; 5
        db DB_GET, 1
        set 1                   ; 6
        db DB_GOTO, 0
        db DB_APPEND, 0         ; 7
        set ada                 ; 8
        db DB_PUT, 1
        set age                 ; 9
        db DB_PUT, 2
        set true                ; 10
        db DB_PUT, 3
        set born                ; 11
        db DB_PUT, 4
        set eleven              ; 12
        db DB_PUT, 1
        set ada                 ; 13
        db DB_PUT, 0
        db DB_WRITE, 0          ; 14
        db DB_APPEND, 0         ; 15
        set bob                 ; 16
        db DB_PUT, 1
        db DB_WRITE, 0          ; 17
        db DB_APPEND, 0         ; 18
        set cy                  ; 19
        db DB_PUT, 1
        set minus               ; 20
        db DB_PUT, 2
        db DB_WRITE, 0          ; 21
        set 2                   ; 22
        db DB_GOTO, 0
        db DB_FLAG, 2           ; 23
        db DB_FLAG, 1           ; 24
        db DB_WRITE, 0          ; 25
        set 1                   ; 26
        db DB_GOTO, 0
        set adal                ; 27
        db DB_PUT, 1
        db DB_WRITE, 0          ; 28
        set BUF1                ; 29
        db DB_GET, 1
        db DB_CLOSE, 0          ; 30
        db DB_FLAG, 0           ; 31
        set new                 ; 32
        db DB_OPEN, 0
        set 2                   ; 33
        db DB_GOTO, 0
        set 3                   ; 34
        db DB_GOTO, 0
        set BUF2                ; 35
        db DB_GET, 2
        set BUF3                ; 36
        db DB_GET, 3
        db DB_CLOSE, 0          ; 37
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

fields:
        field "NAME", 'C', 10, 0
        field "AGE", 'N', 6, 1
        field "OK", 'L', 1, 0
        field "BORN", 'D', 8, 0
zero:
        field "A", 'C', 5, 0
        field "B", 'C', 0, 0
big:
        field "A", 'C', 250, 0
        field "B", 'C', 250, 0
        field "C", 'C', 250, 0
        field "D", 'C', 250, 0

new:    .byte 6, "NEW.DB"
ada:    .byte 3, "ADA"
adal:   .byte 5, "ADA L"
age:    .byte 4, "36.5"
true:   .byte 1, "T"
born:   .byte 8, "18151210"
eleven: .byte 11, "ELEVENCHARS"
bob:    .byte 3, "BOB"
cy:     .byte 2, "CY"
minus:  .byte 4, "-2.0"
