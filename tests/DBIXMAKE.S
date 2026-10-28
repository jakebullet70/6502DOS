; DBIXMAKE: call 57, db, builds indexes with ix_create on DBIXMAKE.PY's card. Keeps A, X, the
; flags N, Z and C, $00, and r0 after each call at RESULTS, 6 bytes a call, for DBIXMAKE.IN to
; dump. Each $00 must be the bank selected at the start. A walk keeps each record it gives, 2
; bytes, at its own buffer, and its result after the last step.
; 1: ix_create with no table: error 6. 2: open PEOPLE.DB: X = 7, r0 = 40.
; 3 to 5: ix_create PNAME.IDX on NAME, PCITY.IDX on CITY and NAME, PBAL.IDX on BAL: X = 0, 1, 2.
; 6: ix_create PID.IDX: error 4. 7: ix_close 1. 8: ix_create PID.IDX on ID, unique: X = 1.
; 9: ix_close 1. 10 to 13: ix_create BAD.IDX on field 8, on no field, on fields 1, 0, 2, and with
; the flags 2: error 13. 14: ix_create PCITYU.IDX on CITY, unique: error 13, and no file.
; 15: ix_order 0. 16: walk PNAME with next to WALK1. 17: ix_order 2. 18: walk PBAL to WALK2.
; 19: close. 20: open TALL.DB: X = 2, r0 = 40. 21: ix_create TALL.IDX on KEY: X = 0.
; 22: walk it to WALK3. 23: ix_create TALLU.IDX on KEY, unique: error 13, and no file. 24: close.

.setcpu "65C02"

.include "api.inc"

RAM_BANK = $00
r0      = $02
r1      = $04
first   = $51                   ; the bank selected at the start
table   = $52                   ; the workspace's bank
results = $53                   ; the next result, 2 bytes
RESULTS = $2000
WALK1   = $2200
WALK2   = $2260
WALK3   = $22C0

.macro set value
        lda #<(value)
        sta r0
        lda #>(value)
        sta r0+1
.endmacro

; make: ix_create of the index at path with the key fields at fields and the flags.
.macro make path, fields, flags
        set path
        lda #<(fields)
        sta r1
        lda #>(fields)
        sta r1+1
        db DB_IX_CREATE, flags
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
        make pname, f_name, 0   ; 1
        set people              ; 2
        db DB_OPEN, 0
        make pname, f_name, 0   ; 3
        make pcity, f_city, 0   ; 4
        make pbal, f_bal, 0     ; 5
        make pid, f_id, 1       ; 6
        db DB_IX_CLOSE, 1       ; 7
        make pid, f_id, 1       ; 8
        db DB_IX_CLOSE, 1       ; 9
        make bad, f_past, 0     ; 10
        make bad, f_none, 0     ; 11
        make bad, f_gap, 0      ; 12
        make bad, f_id, 2       ; 13
        make pcityu, f_town, 1  ; 14
        db DB_IX_ORDER, 0       ; 15
        walk DB_IX_NEXT, 48, WALK1 ; 16
        db DB_IX_ORDER, 2       ; 17
        walk DB_IX_NEXT, 48, WALK2 ; 18
        db DB_CLOSE, 0          ; 19
        set tall                ; 20
        db DB_OPEN, 0
        make tallix, f_id, 0    ; 21
        walk DB_IX_NEXT, 48, WALK3 ; 22
        make tallu, f_id, 1     ; 23
        db DB_CLOSE, 0          ; 24
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
pcity:    .byte 9, "PCITY.IDX"
pbal:     .byte 8, "PBAL.IDX"
pid:      .byte 7, "PID.IDX"
bad:      .byte 7, "BAD.IDX"
pcityu:   .byte 10, "PCITYU.IDX"
tallix:   .byte 8, "TALL.IDX"
tallu:    .byte 9, "TALLU.IDX"
f_name:   .byte 2, 0, 0, 0
f_city:   .byte 3, 2, 0, 0
f_bal:    .byte 5, 0, 0, 0
f_id:     .byte 1, 0, 0, 0
f_past:   .byte 8, 0, 0, 0
f_none:   .byte 0, 0, 0, 0
f_gap:    .byte 1, 0, 2, 0
f_town:   .byte 3, 0, 0, 0
