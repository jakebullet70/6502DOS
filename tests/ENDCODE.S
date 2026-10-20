; ENDCODE: runs tests/com/ENDCHILD.UXB through exec with the tails A to E, and keeps exec's and
; then exitcode's A, carry and X at RESULTS, 6 bytes a run, for ENDCODE.IN to dump.
;   A  END: 0
;   B  END 20
;   C  END -3: 253
;   D  END in a SUB, with its parameter: 30
;   E  END with an expression: 8

.setcpu "65C02"

.include "api.inc"

r0      = $02
r1      = $04
index   = $50                   ; the offset of the next result
RESULTS = $1200

        stz index
        lda #'A'
@run:
        sta tail + 2
        lda #<child
        sta r0
        lda #>child
        sta r0+1
        lda #<tail
        sta r1
        lda #>tail
        sta r1+1
        jsr API_EXEC
        jsr save
        jsr API_EXITCODE
        jsr save
        lda tail + 2
        inc
        cmp #'E' + 1
        bne @run
        rts

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

child:    .byte 13, "\ENDCHILD.COM"
tail:     .byte 2, " A"
