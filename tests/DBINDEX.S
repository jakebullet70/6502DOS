; DBINDEX: call 57, db, walks the indexes of DBINDEX.PY's card. Keeps A, X, the flags N, Z and
; C, $00, and r0 after each call at RESULTS, 6 bytes a call, for DBINDEX.IN to dump. Each $00
; must be the bank selected at the start. A walk keeps each record it gives, 2 bytes, at its
; own buffer, and its result after the last step.
; 1: ix_open with no table: error 6. 2: open PEOPLE.DB: X = 7, r0 = 40.
; 3 to 9, the record order: first 1, prev 0, prev 0, next 1, last 40, next 0, prev 40.
; 10 to 12: ix_open PNAME.IDX, PBAL.IDX, PID.IDX: X = 0, 1, 2. 13: ix_open PCITY.IDX: error 4.
; 14: ix_close 2. 15: ix_close 2 again: error 6. 16: ix_open BIG.IDX, not on PEOPLE: error 11.
; 17: ix_find in the record order: error 13. 18: ix_order 0, PNAME.
; 19: walk PNAME with next to WALK1. 20: walk it back with prev to WALK2.
; 21: ix_order 1, PBAL. 22: first. 23: last. 24: ix_order 0.
; 25: find D: carry clear. 26: next. 27: find ZZZ: error 2, r0 = 0. 28: find a 21-byte key:
; error 13. 29: find the empty key: the first. 30: ix_order $FF. 31: next: the record after.
; 32: close. 33: ix_order 0 with no table: error 6.
; 34: open BIG.DB. 35: ix_open BIG.IDX. 36: ix_order 0. 37: walk 12 with next to WALK3.
; 38: last. 39: walk 12 with prev to WALK4. 40: find 5: carry clear, the first key that starts 5.
; 41: close. 42: open EMPTY.DB. 43: ix_open EMPTY.IDX. 44: ix_order 0.
; 45: first: r0 = 0. 46: last: r0 = 0. 47: next: r0 = 0. 48: find A: error 2. 49: close.

.setcpu "65C02"

.include "api.inc"

RAM_BANK = $00
r0      = $02
first   = $51                   ; the bank selected at the start
table   = $52                   ; the workspace's bank
results = $53                   ; the next result, 2 bytes
RESULTS = $2000
WALK1   = $2200
WALK2   = $2260
WALK3   = $22C0
WALK4   = $22E0

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

; walk: calls function at most steps times, until it gives r0 = 0 or an error, and keeps each r0
; at where.
.macro walk function, steps, where
        .local step, done
        ldx #0
step:
        phx
        ldy #function
        lda table
        jsr API_DB
        plx
        bcs done
        lda r0
        sta where,x
        lda r0+1
        sta where+1,x
        inx
        inx
        lda r0
        ora r0+1
        beq done
        cpx #2 * steps
        bne step
done:
        jsr save
.endmacro

        lda RAM_BANK
        sta first
        lda #<RESULTS
        sta results
        lda #>RESULTS
        sta results+1
        lda #1
        jsr API_BANK_ALLOC
        sta table
        set pname               ; 1
        db DB_IX_OPEN, 0
        set people              ; 2
        db DB_OPEN, 0
        db DB_IX_FIRST, 0       ; 3
        db DB_IX_PREV, 0        ; 4
        db DB_IX_PREV, 0        ; 5
        db DB_IX_NEXT, 0        ; 6
        db DB_IX_LAST, 0        ; 7
        db DB_IX_NEXT, 0        ; 8
        db DB_IX_PREV, 0        ; 9
        set pname               ; 10
        db DB_IX_OPEN, 0
        set pbal                ; 11
        db DB_IX_OPEN, 0
        set pid                 ; 12
        db DB_IX_OPEN, 0
        set pcity               ; 13
        db DB_IX_OPEN, 0
        db DB_IX_CLOSE, 2       ; 14
        db DB_IX_CLOSE, 2       ; 15
        set bigix               ; 16
        db DB_IX_OPEN, 0
        set key_d               ; 17
        db DB_IX_FIND, 0
        db DB_IX_ORDER, 0       ; 18
        walk DB_IX_NEXT, 48, WALK1 ; 19
        walk DB_IX_PREV, 48, WALK2 ; 20
        db DB_IX_ORDER, 1       ; 21
        db DB_IX_FIRST, 0       ; 22
        db DB_IX_LAST, 0        ; 23
        db DB_IX_ORDER, 0       ; 24
        set key_d               ; 25
        db DB_IX_FIND, 0
        db DB_IX_NEXT, 0        ; 26
        set key_zzz             ; 27
        db DB_IX_FIND, 0
        set key_long            ; 28
        db DB_IX_FIND, 0
        set key_none            ; 29
        db DB_IX_FIND, 0
        db DB_IX_ORDER, $FF     ; 30
        db DB_IX_NEXT, 0        ; 31
        db DB_CLOSE, 0          ; 32
        db DB_IX_ORDER, 0       ; 33
        set big                 ; 34
        db DB_OPEN, 0
        set bigix               ; 35
        db DB_IX_OPEN, 0
        db DB_IX_ORDER, 0       ; 36
        walk DB_IX_NEXT, 12, WALK3 ; 37
        db DB_IX_LAST, 0        ; 38
        walk DB_IX_PREV, 12, WALK4 ; 39
        set key_5               ; 40
        db DB_IX_FIND, 0
        db DB_CLOSE, 0          ; 41
        set empty               ; 42
        db DB_OPEN, 0
        set emptyix             ; 43
        db DB_IX_OPEN, 0
        db DB_IX_ORDER, 0       ; 44
        db DB_IX_FIRST, 0       ; 45
        db DB_IX_LAST, 0        ; 46
        db DB_IX_NEXT, 0        ; 47
        set key_a               ; 48
        db DB_IX_FIND, 0
        db DB_CLOSE, 0          ; 49
        lda table
        jsr API_BANK_FREE
        lda first
        sta RAM_BANK
        rts

; save: keeps A, X, the flags N, Z and C, $00 and r0 at results, and moves results on.
save:
        php
        sta (results)
        ldy #1
        txa
        sta (results),y
        iny
        pla
        and #$83                ; N, Z and C
        sta (results),y
        iny
        lda RAM_BANK
        sta (results),y
        iny
        lda r0
        sta (results),y
        iny
        lda r0+1
        sta (results),y
        lda results
        clc
        adc #6
        sta results
        bcc @done
        inc results+1
@done:
        rts

people:   .byte 9, "PEOPLE.DB"
pname:    .byte 9, "PNAME.IDX"
pbal:     .byte 8, "PBAL.IDX"
pid:      .byte 7, "PID.IDX"
pcity:    .byte 9, "PCITY.IDX"
big:      .byte 6, "BIG.DB"
bigix:    .byte 7, "BIG.IDX"
empty:    .byte 8, "EMPTY.DB"
emptyix:  .byte 9, "EMPTY.IDX"
key_d:    .byte 1, "D"
key_zzz:  .byte 3, "ZZZ"
key_long: .byte 21, "ABCDEFGHIJKLMNOPQRSTU"
key_none: .byte 0
key_5:    .byte 1, "5"
key_a:    .byte 1, "A"
