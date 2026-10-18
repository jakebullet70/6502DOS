; ANSI: writes each escape sequence below through API_CON_OUT, then keeps the cursor's row and
; column and the colour at RESULTS, 3 bytes a sequence, for ANSI.IN to dump.

.setcpu "65C02"

.include "api.inc"

index   = $50                   ; the offset of the next result
text    = $52                   ; the next byte of sequences
RESULTS = $1200
ESC     = $1B

        stz index
        lda #<sequences
        sta text
        lda #>sequences
        sta text+1
@next:
        lda (text)
        beq @end
@byte:
        jsr API_CON_OUT
        jsr step
        lda (text)
        bne @byte
        jsr step                ; past the 0
        jsr save
        bra @next
@end:
        rts

; step: moves text on one byte. Changes nothing else.
step:
        inc text
        bne @done
        inc text+1
@done:
        rts

; save: keeps the cursor's row and column and the colour at the next result. Changes A, X and Y.
save:
        sec
        jsr API_CON_CURSOR
        tya
        pha
        ldy index
        txa
        sta RESULTS,y
        pla
        sta RESULTS+1,y
        sec
        jsr API_CON_COLOUR
        ldy index
        sta RESULTS+2,y
        iny
        iny
        iny
        sty index
        rts

; Each sequence ends with 0, and the list with another 0.
sequences:
        .byte ESC, "[5;10H", 0                          ; row 4, column 9
        .byte ESC, "[2A", ESC, "[3C", 0                 ; A and C ignored
        .byte ESC, "[99;99H", 0                         ; the last row and column
        .byte ESC, "[1;1f", 0                           ; f ignored
        .byte ESC, "[H", ESC, "[0;34;42m", 0            ; home; blue on green
        .byte ESC, "[0m", 0                             ; the boot colour
        .byte ESC, "[37m", ESC, "[1m", 0                ; light grey; 1 ignored
        .byte ESC, "[7m", 0                             ; reversed: black on white
        .byte ESC, "[7m", 0                             ; back: white on black
        .byte ESC, "[0m", ESC, "[?7hX", 0               ; ? skipped, h ignored, X shown
        .byte ESC, "Q", 0                               ; Q shown
        .byte ESC, "[3;3H", ESC, "[1J", 0               ; 1J ignored
        .byte ESC, "[K", 0                              ; the cursor stays
        .byte ESC, "[2J", 0                             ; home
        .byte 0
