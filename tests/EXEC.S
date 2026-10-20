; EXEC: runs tests/prg/CHILD.S through exec: errors, exit codes, RTS, programs inside programs,
; and a handle the child shares. Keeps each call's A, carry and X at RESULTS, 3 bytes a call,
; for EXEC.IN to dump. Each child writes over $1000, $8000 and index, so the program goes on
; only when exec copies them back.

.setcpu "65C02"

.include "api.inc"

r0      = $02
r1      = $04
index   = $50                   ; the offset of the next result
handle  = $51
RESULTS = $1200
BUFFER  = $1300
MARK    = $8000

.macro point register, address
        lda #<(address)
        sta register
        lda #>(address)
        sta register+1
.endmacro

        stz index
        lda #$5A
        sta MARK
        point r0, nope          ; 1: a missing program: error 2
        point r1, empty
        jsr API_EXEC
        jsr save
        point r0, hello         ; 2: a file that does not load at $0801: error 11
        jsr API_EXEC
        jsr save
        point r0, child         ; 3: CHILD E exits with 42: A = 42, then exitcode 42
        point r1, tail_e
        jsr API_EXEC
        jsr save
        jsr API_EXITCODE
        jsr save
        point r1, tail_r        ; 4: CHILD R returns with RTS: exitcode 0
        jsr API_EXEC
        jsr save
        jsr API_EXITCODE
        jsr save
        point r1, tail_n        ; 5: CHILD N inside CHILD N, then error 8: exitcode 9
        jsr API_EXEC
        jsr save
        jsr API_EXITCODE
        jsr save
        point r0, readme        ; 6: CHILD H reads 5 bytes of handle 3, then this reads the next 5
        lda #0
        jsr API_OPEN
        jsr save
        stx handle
        point r0, child
        point r1, tail_h
        jsr API_EXEC
        jsr save
        point r0, BUFFER
        point r1, 5
        ldx handle
        jsr API_READ
        jsr save_r1
        ldx handle
        jsr API_CLOSE
        jsr save
        lda #7                  ; 7: exit with no program running: error 1
        jsr API_EXIT
        jsr save
        lda MARK                ; 8: the mark: $5A
        jsr save
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

; save_r1: keeps r1, low byte, carry, high byte.
save_r1:
        php
        ldx r1+1
        lda r1
        plp
        bra save

nope:     .byte 9, "\NOPE.COM"
hello:    .byte 10, "\HELLO.TXT"
child:    .byte 10, "\CHILD.COM"
readme:   .byte 16, "\DOCS\README.TXT"
empty:    .byte 0
tail_e:   .byte 2, " E"
tail_r:   .byte 2, " R"
tail_n:   .byte 2, " N"
tail_h:   .byte 2, " H"
