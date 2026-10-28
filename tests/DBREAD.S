; DBREAD: call 57, db, reads the tables of DBREAD.PY's card. Keeps A, X, the flags N, Z and C,
; $00, and r0 after each call at RESULTS, 6 bytes a call, for DBREAD.IN to dump. Each $00 must
; be the bank selected at the start.
; 1: open NOSUCH.DB: error 2.
; 2: open PEOPLE.DB: X = 7 fields, r0 = 40 records.
; 3: info of field 7: r0 = $A090.
; 4: get with no record current: error 13.
; 5, 6: goto 0 and goto 41: error 13.
; 7: goto 6: X = '*', deleted.
; 8: get field 2, NAME, to BUF1.
; 9: goto 40: X = ' '.
; 10: get field 7, JOINED, to BUF2.
; 11, 12: get field 8 and field 0: error 13.
; 13: close. 14: close again: error 6.
; 15: open NOTDB.DB: error 11. 16: info: error 6.
; 17: open WIDE.DB: X = 4, r0 = 100.
; 18: goto 100, which starts past 64 KB: X = ' '.
; 19: get field 4, 237 bytes, to BUF3. 20: close.

.setcpu "65C02"

.include "api.inc"

RAM_BANK = $00
r0      = $02
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

.macro db function, field
        ldx #field
        ldy #function
        lda table
        jsr API_DB
        jsr save
.endmacro

        lda RAM_BANK
        sta first
        stz index
        lda #1
        jsr API_BANK_ALLOC
        sta table
        set nosuch              ; 1
        db DB_OPEN, 0
        set people              ; 2
        db DB_OPEN, 0
        db DB_INFO, 7           ; 3
        set BUF1                ; 4
        db DB_GET, 2
        set 0                   ; 5
        db DB_GOTO, 0
        set 41                  ; 6
        db DB_GOTO, 0
        set 6                   ; 7
        db DB_GOTO, 0
        set BUF1                ; 8
        db DB_GET, 2
        set 40                  ; 9
        db DB_GOTO, 0
        set BUF2                ; 10
        db DB_GET, 7
        db DB_GET, 8            ; 11
        db DB_GET, 0            ; 12
        db DB_CLOSE, 0          ; 13
        db DB_CLOSE, 0          ; 14
        set notdb               ; 15
        db DB_OPEN, 0
        db DB_INFO, 0           ; 16
        set wide                ; 17
        db DB_OPEN, 0
        set 100                 ; 18
        db DB_GOTO, 0
        set BUF3                ; 19
        db DB_GET, 4
        db DB_CLOSE, 0          ; 20
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

nosuch: .byte 9, "NOSUCH.DB"
people: .byte 9, "PEOPLE.DB"
notdb:  .byte 8, "NOTDB.DB"
wide:   .byte 7, "WIDE.DB"
