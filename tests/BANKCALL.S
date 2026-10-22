; BANKCALL: bank_call. Takes two banks, selects the first, copies two routines to $A000 in the
; second, and makes three calls. Keeps A, X, Y, the flags N, Z and C, and $00 after each call
; at RESULTS, 5 bytes a call, for BANKCALL.IN to dump. Each $00 must be the first bank.
; 1: a routine in the second bank: A = its bank, X = X + 1, Y = $5A, carry set.
; 2: a routine in the second bank that calls the low RAM routine with bank_call and the first
;    bank: A = $77, X = its bank after the inner call, Y = the inner A.
; 3: the low RAM routine with bank 0: A = 0, so Z is set.

.setcpu "65C02"

.include "api.inc"

RAM_BANK = $00
r0      = $02
index   = $50                   ; the offset of the next result
first   = $51                   ; the bank selected at the start
caller  = $52                   ; the first bank
callee  = $53                   ; the second bank
inner   = $54
keep_a  = $55
keep_x  = $56
keep_y  = $57
RESULTS = $1400

.macro point register, address
        lda #<(address)
        sta register
        lda #>(address)
        sta register+1
.endmacro

        lda RAM_BANK
        sta first
        stz index
        lda #2
        jsr API_BANK_ALLOC
        sta caller
        inc
        sta callee
        sta RAM_BANK
        ldx #IMAGE_SIZE - 1
@copy:
        lda image,x
        sta $A000,x
        dex
        bpl @copy
        lda caller
        sta RAM_BANK
        point r0, routine1      ; 1
        ldx #$41
        lda callee
        jsr API_BANK_CALL
        jsr save
        point r0, routine2      ; 2
        lda callee
        jsr API_BANK_CALL
        jsr save
        point r0, routine3      ; 3
        ldx #0
        lda #0
        jsr API_BANK_CALL
        jsr save
        lda caller
        jsr API_BANK_FREE
        lda first
        sta RAM_BANK
        rts

; save: keeps A, X, Y, the flags N, Z and C, and $00 at the next result.
save:
        php
        sta keep_a
        stx keep_x
        sty keep_y
        ldy index
        lda keep_a
        sta RESULTS,y
        lda keep_x
        sta RESULTS+1,y
        lda keep_y
        sta RESULTS+2,y
        pla
        and #$83                ; N, Z and C
        sta RESULTS+3,y
        lda RAM_BANK
        sta RESULTS+4,y
        tya
        clc
        adc #5
        sta index
        rts

; routine3: in low RAM. A = the bank selected.
routine3:
        lda RAM_BANK
        clc
        rts

; The image: the routines that run at $A000 in the second bank.
image:
.org $A000
routine1:
        lda RAM_BANK
        inx
        ldy #$5A
        sec
        rts
routine2:
        point r0, routine3
        lda caller
        jsr API_BANK_CALL
        sta inner
        ldx RAM_BANK
        ldy inner
        lda #$77
        clc
        rts
IMAGE_SIZE = * - $A000
.reloc
