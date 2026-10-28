; DBIXEDIT: call 57, db, changes records of tables with open indexes on DBIXEDIT.PY's card, and
; DBIXEDIT.PY checks each index against its table after the run. Keeps A, X, the flags N, Z and C,
; $00, and r0 after each call at RESULTS, 6 bytes a call, for DBIXEDIT.IN to dump. Each $00 must
; be the bank selected at the start.
; 1: open PEOPLE.DB: X = 7, r0 = 40. 2, 3: ix_open PNAME.IDX and PID.IDX: X = 0, 1.
; 4: ix_order 0. 5: ix_first: the first name. 6, 7: put ZZZ in NAME, write.
; 8: ix_next: r0 = 0, the record now last. 9: ix_prev: r0 = the record of 5.
; 10, 11: goto 5, get ID to BUF. 12, 13: goto 4, put BUF in ID. 14: write: error 13.
; 15: goto 4. 16 to 19: append: r0 = 41, put AAA in NAME, put 1000 in ID, write.
; 20: ix_first: r0 = 41. 21: pack, 4 records deleted: X = 7, r0 = 37. 22: ix_first, the
; indexes built again in their slots and the order kept: r0 = 37. 23: close.
; 24: open TALL.DB: X = 2, r0 = 40. 25: ix_open TALL.IDX: X = 0. 26: ix_order 0.
; 27: for each record n from 1 to 40: goto n, put Z and the byte 126 - n in KEY, write. Keeps A
; = 0 and carry clear, or the failed call's result, with X = the record reached, 41 when all were
; written. 28: walk TALL.IDX with next to WALK from the place, record 40, the last written: 39
; down to 1. 29: close.
; 30: open TINY.DB, 5 records, the keys A to E: X = 2, r0 = 5. 31: ix_open TINY.IDX: X = 0.
; 32: ix_order 0. 33 to 38: goto, put and write the keys of records 1 Z, 2 Y, 5 F, 1 A, 5 B and
; 2 E: a page left with no keys merges with the page after it, then with the page before it, the
; root gives way twice, and an entry leaves a node. 39: ix_first: r0 = 1. 40: walk TINY.IDX to
; WALK2: 5, 3, 4, 2. 41: close.

.setcpu "65C02"

.include "api.inc"

RAM_BANK = $00
r0      = $02
r1      = $04
first   = $51                   ; the bank selected at the start
table   = $52                   ; the workspace's bank
results = $53                   ; the next result, 2 bytes
count   = $55                   ; the record of a loop
RESULTS = $2000
WALK    = $2200
WALK2   = $2260
BUF     = $2300

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

; call: calls function with X = field, and goes to fail on an error.
.macro call function, field, fail
        ldx #field
        ldy #function
        lda table
        jsr API_DB
        bcs fail
.endmacro

; rekey: makes record number current, puts the one character text in KEY, and writes it. Keeps the
; write's result, or the result of the call that failed.
.macro rekey number, text
        .local done
        set number
        call DB_GOTO, 0, done
        lda #text
        sta key+1
        lda #1
        sta key
        set key
        call DB_PUT, 1, done
        call DB_WRITE, 0, done
done:
        jsr save
.endmacro

; walk: calls ix_next at most steps times, until it gives r0 = 0 or an error, and keeps each r0
; at where.
.macro walk steps, where
        .local step, done
        ldx #0
step:
        phx
        ldy #DB_IX_NEXT
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
        set people              ; 1
        db DB_OPEN, 0
        set pname               ; 2
        db DB_IX_OPEN, 0
        set pid                 ; 3
        db DB_IX_OPEN, 0
        db DB_IX_ORDER, 0       ; 4
        db DB_IX_FIRST, 0       ; 5
        set zzz                 ; 6
        db DB_PUT, 2
        db DB_WRITE, 0          ; 7
        db DB_IX_NEXT, 0        ; 8
        db DB_IX_PREV, 0        ; 9
        set 5                   ; 10
        db DB_GOTO, 0
        set BUF                 ; 11
        db DB_GET, 1
        set 4                   ; 12
        db DB_GOTO, 0
        set BUF                 ; 13
        db DB_PUT, 1
        db DB_WRITE, 0          ; 14
        set 4                   ; 15
        db DB_GOTO, 0
        db DB_APPEND, 0         ; 16
        set aaa                 ; 17
        db DB_PUT, 2
        set id                  ; 18
        db DB_PUT, 1
        db DB_WRITE, 0          ; 19
        db DB_IX_FIRST, 0       ; 20
        db DB_PACK, 0           ; 21
        db DB_IX_FIRST, 0       ; 22
        db DB_CLOSE, 0          ; 23
        set tall                ; 24
        db DB_OPEN, 0
        set tallix              ; 25
        db DB_IX_OPEN, 0
        db DB_IX_ORDER, 0       ; 26
        lda #1                  ; 27
        sta count
@key:
        lda count
        sta r0
        stz r0+1
        call DB_GOTO, 0, @keyed
        lda #126
        sec
        sbc count
        sta key+2
        set key
        call DB_PUT, 1, @keyed
        call DB_WRITE, 0, @keyed
        inc count
        lda count
        cmp #41
        bne @key
        lda #0
        clc
@keyed:
        ldx count
        jsr save
        walk 48, WALK           ; 28
        db DB_CLOSE, 0          ; 29
        set tiny                ; 30
        db DB_OPEN, 0
        set tinyix              ; 31
        db DB_IX_OPEN, 0
        db DB_IX_ORDER, 0       ; 32
        rekey 1, 'Z'            ; 33
        rekey 2, 'Y'            ; 34
        rekey 5, 'F'            ; 35
        rekey 1, 'A'            ; 36
        rekey 5, 'B'            ; 37
        rekey 2, 'E'            ; 38
        db DB_IX_FIRST, 0       ; 39
        walk 8, WALK2           ; 40
        db DB_CLOSE, 0          ; 41
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
tall:     .byte 7, "TALL.DB"
pname:    .byte 9, "PNAME.IDX"
pid:      .byte 7, "PID.IDX"
tallix:   .byte 8, "TALL.IDX"
tiny:     .byte 7, "TINY.DB"
tinyix:   .byte 8, "TINY.IDX"
zzz:      .byte 3, "ZZZ"
aaa:      .byte 3, "AAA"
id:       .byte 4, "1000"
key:      .byte 2, 'Z', 0
