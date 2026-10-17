; HEAPKID: the program the HEAP test runs. Its code starts at $0801, with no BASIC line. In
; VARBANK it takes CHILD1 on $50, the system string SYS2, TMP on $60, then Z on $50, which frees
; CHILD1. Its str_gc must not move its parent's free block below its floor. It exits with the low
; byte of the free count.

.setcpu "65C02"

.include "api.inc"

RAM_BANK = $00
r0      = $02
r1      = $04
r2      = $06

.macro point register, address
        lda #<(address)
        sta register
        lda #>(address)
        sta register+1
.endmacro

        point r0, $50
        point r2, child1
        jsr take
        point r0, $A00E
        point r2, sys2
        jsr take
        point r0, $60
        point r2, tmp
        jsr take
        point r0, $50
        point r2, letter
        jsr take
        jsr API_STR_GC
        lda r0
        jsr API_EXIT

; take: takes a string on the descriptor at r0 and copies the length-prefixed string at r2
; into it. Changes A, X and Y.
take:
        lda (r2)
        jsr API_STR_ALLOC
        ldy RAM_BANK
        phy
        sta RAM_BANK
        lda (r2)
        tay
@char:
        lda (r2),y
        sta (r1),y
        dey
        bne @char
        pla
        sta RAM_BANK
        rts

child1:   .byte 6, "CHILD1"
sys2:     .byte 4, "SYS2"
tmp:      .byte 3, "TMP"
letter:   .byte 1, "Z"
