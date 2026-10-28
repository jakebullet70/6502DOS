; FP: the program the FP test runs. Makes the calls of its table to call 58, fp, and prints a
; line for each: A, X, the flags N, Z and C, r1 and r2, in hex. Then prints the 16 texts. The
; values are at VALUES, 8 bytes apart, and the texts at TEXTS, 16 bytes apart. Its code starts at
; $0801, with no BASIC line.

.setcpu "65C02"

.include "api.inc"

r0      = $02
r1      = $04
r2      = $06
call    = $50                   ; the record of the next call, 2 bytes
keep    = $52                   ; A, X, the flags, r1 and r2 after the call, 7 bytes
count   = $59                   ; the bytes printed, or the text's number
text    = $5A                   ; the text printed, 2 bytes
VALUES  = $1600
TEXTS   = $1700

.define V(n) VALUES + 8 * (n)
.define T(n) TEXTS + 16 * (n)

; try function, X, r0, r1, r2: a record of the table.
.macro try function, xin, in0, in1, in2
        .byte function, xin
        .word in0, in1, in2
.endmacro

        lda #<calls
        sta call
        lda #>calls
        sta call+1
@next:
        ldy #7
@copy:
        lda (call),y
        sta r0 - 2,y
        dey
        cpy #2
        bcs @copy
        lda (call),y
        tax
        lda (call)
        tay
        jsr API_FP
        php
        sta keep
        stx keep+1
        pla
        and #$83                ; N, Z and C
        sta keep+2
        ldx #3
@keep:
        lda r1-3,x
        sta keep,x
        inx
        cpx #7
        bne @keep
        stz count
@print:
        ldx count
        lda keep,x
        jsr hex
        lda #' '
        jsr API_CON_OUT
        inc count
        lda count
        cmp #7
        bne @print
        jsr newline
        clc
        lda call
        adc #8
        sta call
        bcc @end
        inc call+1
@end:
        lda call
        cmp #<calls_end
        bne @next
        lda call+1
        cmp #>calls_end
        bne @next
        stz count
@text:
        lda count                ; text = TEXTS + 16 * count
        asl
        asl
        asl
        asl
        sta text
        lda #>TEXTS
        sta text+1
        ldy #0
@char:
        tya
        cmp (text)
        beq @line
        iny
        phy
        lda (text),y
        jsr API_CON_OUT
        ply
        bra @char
@line:
        jsr newline
        inc count
        lda count
        cmp #16
        bne @text
        lda #0
        jsr API_EXIT

; hex: prints A as two hex digits.
hex:
        pha
        lsr
        lsr
        lsr
        lsr
        jsr @digit
        pla
        and #$0F
@digit:
        cmp #10
        bcc @number
        adc #'A' - '0' - 10 - 1 ; carry is set
@number:
        adc #'0'
        jmp API_CON_OUT

; newline: prints CR and LF.
newline:
        lda #$0D
        jsr API_CON_OUT
        lda #$0A
        jmp API_CON_OUT

calls:
        try FP_FIN, 0, t_sp125, V(0), 0         ; 1: 12.5, X = 6
        try FP_FIN, 0, t_m3, V(1), 0            ; 2: -3, X = 2
        try FP_FIN, 0, t_7e2, V(2), 0           ; 3: 700, X = 3
        try FP_FIN, 0, t_abc, V(15), 0          ; 4: error 13
        try FP_FOUT, 0, V(0), T(0), 0           ; 5: 12.5
        try FP_FOUT, 0, V(1), T(1), 0           ; 6: -3
        try FP_FOUT, 0, V(2), T(2), 0           ; 7: 700
        try FP_FIN, 0, t_125, V(3), 0           ; 8
        try FP_ADD, 0, V(3), V(1), 0            ; 9: 12.5 + -3
        try FP_FOUT, 0, V(3), T(3), 0           ; 10: 9.5
        try FP_FIN, 0, t_125, V(4), 0           ; 11
        try FP_SUB, 0, V(4), V(1), 0            ; 12: 12.5 - -3
        try FP_FOUT, 0, V(4), T(4), 0           ; 13: 15.5
        try FP_FIN, 0, t_125, V(5), 0           ; 14
        try FP_MUL, 0, V(5), V(1), 0            ; 15: 12.5 * -3
        try FP_FOUT, 0, V(5), T(5), 0           ; 16: -37.5
        try FP_FIN, 0, t_125, V(6), 0           ; 17
        try FP_DIV, 0, V(6), V(1), 0            ; 18: 12.5 / -3
        try FP_FOUT, 0, V(6), T(6), 0           ; 19: -4.16666667
        try FP_FIN, 0, t_0, V(7), 0             ; 20
        try FP_DIV, 0, V(0), V(7), 0            ; 21: 12.5 / 0, error 13
        try FP_CMP, 0, V(0), V(1), 0            ; 22: A = 1
        try FP_CMP, 0, V(1), V(0), 0            ; 23: A = $FF
        try FP_CMP, 0, V(0), V(0), 0            ; 24: A = 0
        try FP_FIN, 0, t_m25, V(8), 0           ; 25
        try FP_INT, 0, V(8), 0, 0               ; 26: INT(-2.5)
        try FP_FOUT, 0, V(8), T(7), 0           ; 27: -3
        try FP_FROM_LONG, 0, V(9), $7960, $FFFE ; 28: -100000
        try FP_FOUT, 0, V(9), T(8), 0           ; 29: -100000
        try FP_TO_LONG, 0, V(0), 0, 0           ; 30: r1 r2 = 12
        try FP_TO_LONG, 0, V(8), 0, 0           ; 31: r1 r2 = -3
        try FP_FIN, 0, t_1e10, V(10), 0         ; 32
        try FP_TO_LONG, 0, V(10), 0, 0          ; 33: error 13
        try FP_FOUT, 0, V(10), T(9), 0          ; 34: 1E+10
        try FP_FIX, 2, V(2), T(10), 0           ; 35: 700.00
        try FP_FIN, 0, t_2, V(11), 0            ; 36
        try FP_FIN, 0, t_3, V(12), 0            ; 37
        try FP_DIV, 0, V(11), V(12), 0          ; 38: 2 / 3
        try FP_FIX, 2, V(11), T(11), 0          ; 39: 0.67
        try FP_FIN, 0, t_m001, V(13), 0         ; 40
        try FP_FIX, 2, V(13), T(12), 0          ; 41: 0.00
        try FP_FOUT, 0, V(13), T(13), 0         ; 42: -1E-03
        try FP_FIN, 0, t_12345, V(14), 0        ; 43
        try FP_FIX, 0, V(14), T(14), 0          ; 44: 1235
        try FP_FIX, 10, V(14), T(15), 0         ; 45: error 13
        try FP_FIX, 1, V(8), T(15), 0           ; 46: -3.0
        try FP_COUNT, 0, 0, 0, 0                ; 47: error 1
calls_end:

t_sp125: .byte 6, "  12.5"
t_m3:    .byte 2, "-3"
t_7e2:   .byte 4, "7E2X"
t_abc:   .byte 3, "ABC"
t_125:   .byte 4, "12.5"
t_0:     .byte 1, "0"
t_m25:   .byte 4, "-2.5"
t_1e10:  .byte 4, "1E10"
t_2:     .byte 1, "2"
t_3:     .byte 1, "3"
t_m001:  .byte 5, "-.001"
t_12345: .byte 6, "1234.5"
