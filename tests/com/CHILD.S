; CHILD: the program the EXEC test runs. Its code starts at $0801, with no BASIC line. It writes
; $EE over $1000, $8000 and $50, which its parent holds, prints CHILD [tail], then acts on the
; tail's second character:
;   E  exit with code 42
;   N  run CHILD N, then exit with that exec's error, or with its exit code plus 1
;   H  copy 5 bytes from handle 3 to handle 1, then RTS
;   any other: RTS

.setcpu "65C02"

.include "api.inc"

r0      = $02
r1      = $04
TAIL    = $0780
BUFFER  = $0A00

.macro point register, address
        lda #<(address)
        sta register
        lda #>(address)
        sta register+1
.endmacro

        lda #$EE
        sta $1000
        sta $8000
        sta $50
        point r0, opening
        point r1, 7
        ldx #1
        jsr API_WRITE
        point r0, TAIL + 1
        lda TAIL
        sta r1
        stz r1+1
        ldx #1
        jsr API_WRITE
        point r0, closing
        point r1, 3
        ldx #1
        jsr API_WRITE
        lda TAIL + 2
        cmp #'E'
        beq exit_42
        cmp #'N'
        beq nest
        cmp #'H'
        beq handle
        rts

exit_42:
        lda #42
        jsr API_EXIT

nest:
        point r0, child
        point r1, tail_n
        jsr API_EXEC
        bcs @exit
        jsr API_EXITCODE
        inc
@exit:
        jsr API_EXIT

handle:
        point r0, BUFFER
        point r1, 5
        ldx #3
        jsr API_READ
        ldx #1                  ; r1: the bytes read
        jsr API_WRITE
        rts

opening:  .byte "CHILD ["
closing:  .byte "]", $0D, $0A
child:    .byte 10, "\CHILD.COM"
tail_n:   .byte 2, " N"
