; DB: call 57, db, in ROM bank 5. Takes a bank for the workspace and makes six calls. Keeps
; A, X, the flags N, Z and C, $00, and r0 after each call at RESULTS, 6 bytes a call, for
; DB.IN to dump. Each $00 must be the bank selected at the start.
; 1: db_info of field 0, the workspace's header DB with version 2: no table, error 6.
; 2: function 20, past the last: error 1.
; 3: ix_create with no table: error 6.
; 4: db_info of field 0, the header DB with version 1 and 2 fields: r0 = $A020.
; 5: db_info of field 2: r0 = $A040.
; 6: db_info of field 3: error 13.

.setcpu "65C02"

.include "api.inc"

RAM_BANK = $00
r0      = $02
index   = $50                   ; the offset of the next result
first   = $51                   ; the bank selected at the start
table   = $52                   ; the workspace's bank
keep_a  = $53
keep_x  = $54
HEADER  = $A020                 ; the table's header in the workspace
RESULTS = $1400

.macro header version
        lda table
        sta RAM_BANK
        lda #'D'
        sta HEADER
        lda #'B'
        sta HEADER+1
        lda #version
        sta HEADER+2
        lda #2
        sta HEADER+3            ; fields
        lda first
        sta RAM_BANK
.endmacro

.macro db function, field
        stz r0
        stz r0+1
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
        header 2
        db DB_INFO, 0           ; 1
        db DB_COUNT, 0          ; 2
        db DB_IX_CREATE, 0      ; 3
        header 1
        db DB_INFO, 0           ; 4
        db DB_INFO, 2           ; 5
        db DB_INFO, 3           ; 6
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
