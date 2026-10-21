; BANKS: the bank allocator, bank_alloc and bank_free, on x16emu's 64 banks: banks 1 to 10 and
; 12 to 63 are free at boot. exec takes its save from them. tests/com/BANKKID.S takes banks and
; exits without freeing them. Keeps each call's A, carry and X at RESULTS, 3 bytes a call, for
; BANKS.IN to dump.

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
        lda #0                  ; 1: the free count: 62
        jsr alloc
        lda #1                  ; 2: one bank: 1
        jsr alloc
        lda #3                  ; 3: three: 2
        jsr alloc
        lda #1                  ; 4: one: 5
        jsr alloc
        lda #3                  ; 5: not the first of a run: error 9
        jsr free
        lda #2                  ; 6: 2 to 4
        jsr free
        lda #0                  ; 7: 60
        jsr alloc
        lda #2                  ; 8: two: 2, then 6 past the lone 4
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
        lda #0                  ; 11: 56
        jsr alloc
        point r0, kid           ; 12: the save takes 12 to 16; BANKKID takes 8 and 9,
                                ; then 4, and exits with 8
        point r1, empty
        jsr API_EXEC
        jsr save
        jsr API_EXITCODE
        jsr save
        lda #0                  ; 13: exit freed them and the save: 56
        jsr alloc
        lda #1                  ; 14: 4
        jsr alloc
        lda #1                  ; 15: free 1, then again: error 9
        jsr free
        lda #1
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
