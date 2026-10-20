; FAR: calls b1_probe at $C000 in ROM bank 1, which takes an IRQ in bank 1, writes "B" through
; a far call to bank 0, and returns api_con_colour's result from a far call with carry set. Keeps
; A, X, Y and P at RESULTS, for FAR.IN to dump: $05, $5A, $A5, carry clear.

.setcpu "65C02"

ROM_BANK = $01
RESULTS = $1200

        lda #1
        sta ROM_BANK
        jsr $C000
        stz ROM_BANK
        sta RESULTS
        stx RESULTS+1
        sty RESULTS+2
        php
        pla
        sta RESULTS+3
        rts
