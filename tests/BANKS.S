; BANKS: the bank allocator, bank_alloc and bank_free, on x16emu's 64 banks: banks 12 to 63 are
; free at boot. tests/com/BANKKID.S takes banks and exits without freeing them. Keeps each call's
; A, carry and X at RESULTS, 3 bytes a call, for BANKS.IN to dump.

.setcpu "65C02"

.include "api.inc"

r0      = $02
r1      = $04
index   = $50                   ; the offset of the next result
RESULTS = $1200

.macro point register, address
        lda #<(address)
        sta register
        lda #>(address)
        sta register+1
.endmacro

        stz index
        lda #0                  ; 1: the free count: 52
        jsr alloc
        lda #1                  ; 2: one bank: 12
        jsr alloc
        lda #3                  ; 3: three: 13
        jsr alloc
        lda #1                  ; 4: one: 16
        jsr alloc
        lda #14                 ; 5: not the first of a run: error 9
        jsr free
        lda #13                 ; 6: 13 to 15
        jsr free
        lda #0                  ; 7: 50
        jsr alloc
        lda #2                  ; 8: two: 13, then 17 past the lone 15
        jsr alloc
        lda #2
        jsr alloc
        lda #0                  ; 9: bank 0, VARBANK and a bank the machine lacks: error 9
        jsr free
        lda #11
        jsr free
        lda #255
        jsr free
        lda #200                ; 10: too many: error 8
        jsr alloc
        lda #0                  ; 11: 46
        jsr alloc
        point r0, kid           ; 12: BANKKID takes 19 and 20, then 15, and exits with 19
        point r1, empty
        jsr API_EXEC
        jsr save
        jsr API_EXITCODE
        jsr save
        lda #0                  ; 13: exit freed them: 46
        jsr alloc
        lda #1                  ; 14: 15
        jsr alloc
        lda #12                 ; 15: free 12, then again: error 9
        jsr free
        lda #12
        jsr free
        rts

alloc:
        jsr API_BANK_ALLOC
        bra save

free:
        jsr API_BANK_FREE
        ; fall through

; save: keeps A, carry and X at the next result. Changes A and Y.
save:
        php
        ldy index
        sta RESULTS,y
        pla
        and #$01                ; carry
        sta RESULTS+1,y
        txa
        sta RESULTS+2,y
        iny
        iny
        iny
        sty index
        rts

kid:      .byte 12, "\BANKKID.COM"
empty:    .byte 0
