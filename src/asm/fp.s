; 6502DOS ROM bank 5: the float library behind call 58, fp. A value is MSBASIC's 5-byte float:
; the exponent, then the mantissa, high byte first, whose top bit is the sign. The arithmetic
; is a copy of MSBASIC/src/float.s for the 6502DOS target, without LOG, SQR, FPWRT, EXP and the
; polynomials. Its labels are MSBASIC's.
;
; Trap: FIN clears TMPEXP to SERLEN by index, COPY_ARG_TO_FAC and MAF copy FAC and ARG through
; EXPSGN and SHIFTSIGNEXT by index, and the shifts reach FAC, ARG and RESULT by zp,X. Keep the
; order of the zero page below.

.setcpu "65C02"

.include "mem.inc"
.include "api.inc"

.export api_fp

BYTES_FP       = 5
MANTISSA_BYTES = BYTES_FP - 1
MAX_EXPON      = 10

.segment "KERNELZP" : zeropage

fp_sp:        .res 1            ; the stack pointer at api_fp, for fp_bad_data
TMPEXP:
INDX:         .res 1
EXPON:        .res 1
LOWTR:        .res 1
EXPSGN:       .res 1
FAC:          .res BYTES_FP
FAC_LAST      = FAC + BYTES_FP - 1
FACSIGN:      .res 1
SERLEN:       .res 1
SHIFTSIGNEXT: .res 1
ARG:          .res BYTES_FP
ARG_LAST      = ARG + BYTES_FP - 1
ARGSIGN:      .res 1
RESULT:       .res MANTISSA_BYTES
RESULT_LAST   = RESULT + BYTES_FP - 1

; The rest lives in r4 to r9, which fp changes.
INDEX         = r4              ; a value read or written
DEST          = r5              ; FCOMP's value
TXTPTR        = r6              ; fin: the character read; fout: the text, less 1 when positive
SGNCPR        = r7
FACEXTENSION  = r7 + 1
ARGEXTENSION  = r8
STRNG2        = r8 + 1          ; fout and fix: the text's last offset
VARPNT        = r9              ; fout: the digit table's offset; fin: TXTPTR at the number;
                                ; fix: bit 7 the sign, bit 6 once a digit is written
FP_LEFT       = r9 + 1          ; fin: the characters left; fix: the decimals

.segment "B5CODE"

; api_fp: call 58. Y = the function; X and r0 to r3 by function. Runs the function, which ends
; with carry clear, or with carry set and A = the error.
api_fp:
        cpy #FP_COUNT
        bcs @bad
        stz SHIFTSIGNEXT
        txa
        tsx
        stx fp_sp
        tax
        tya
        asl
        tay
        lda fp_table+1,y
        pha
        lda fp_table,y
        pha
        rts                     ; to the function, with X as it came
@bad:
        lda #ERR_BAD_FUNCTION
        sec
        rts

; fp_table: for each function by number, its routine less 1, for the RTS of api_fp.
fp_table:
        .addr fp_fin - 1        ; 0 fin
        .addr fp_fout - 1       ; 1 fout
        .addr fp_add - 1        ; 2 add
        .addr fp_sub - 1        ; 3 sub
        .addr fp_mul - 1        ; 4 mul
        .addr fp_div - 1        ; 5 div
        .addr fp_cmp - 1        ; 6 cmp
        .addr fp_int - 1        ; 7 int
        .addr fp_from_long - 1  ; 8 from_long
        .addr fp_to_long - 1    ; 9 to_long
        .addr fp_fix - 1        ; 10 fix
        .assert * - fp_table = 2 * FP_COUNT, error, "fp_table needs a routine for each function"

; fp_bad_data: ends the call from any depth with error 13. OVERFLOW and a division by 0 come
; here.
fp_bad_data:
        ldx fp_sp
        txs
        lda #ERR_BAD_DATA
        sec
        rts

; fp_fin: the value of the length-prefixed text at r0 to r1, X = the characters read, leading
; spaces included. Error 13 when no number starts the text.
fp_fin:
        lda r0
        sta TXTPTR
        lda r0+1
        sta TXTPTR+1
        lda (r0)
        sta FP_LEFT
@space:
        jsr CHRGET
        eor #' '                ; EOR keeps the carry
        beq @space
        eor #' '
        ldx TXTPTR
        stx VARPNT
        jsr FIN
        lda TXTPTR
        cmp VARPNT
        beq fp_bad_data
        ldx r1
        ldy r1+1
        jsr STORE_FAC_AT_YX_ROUNDED
        lda TXTPTR
        clc
        sbc r0                  ; TXTPTR - r0 - 1
        tax
        clc
        rts

; CHRGET: FIN's reader. Moves TXTPTR to the next character of the text and gives it in A,
; with carry clear for a digit. Past the text's end it gives 0, carry set.
CHRGET:
        inc TXTPTR
        bne @read
        inc TXTPTR+1
@read:
        lda FP_LEFT
        beq @end
        dec FP_LEFT
        lda (TXTPTR)
        cmp #'9' + 1
        bcs @done
        sec
        sbc #'0'
        sec
        sbc #$100 - '0'         ; A again, carry clear for a digit
@done:
        rts
@end:
        sec
        rts

; fp_fout: r1 = the value at r0 as length-prefixed text, as MSBASIC's PRINT gives it without
; the space before a value of 0 or more. r1 takes 17 bytes.
fp_fout:
        jsr fp_load_r0
        lda r1
        ldx r1+1
        bit FACSIGN
        bmi @point
        dec a                   ; the space before the digits falls on the length byte
        cmp #$FF
        bne @point
        dex
@point:
        sta TXTPTR
        stx TXTPTR+1
        jsr FOUT                ; Y = the $00 after the text, from TXTPTR
        dey
        lda TXTPTR
        cmp r1
        beq @length
        dey
@length:
        tya
        sta (r1)
        clc
        rts

; fp_add, fp_sub, fp_mul, fp_div: r0 = r0 + r1, r0 - r1, r0 * r1, r0 / r1. fp_div gives error
; 13 when r1 is 0.
fp_add:
        jsr fp_load_r0
        lda r1
        ldy r1+1
        jsr FADD
        bra fp_store_r0
fp_sub:
        jsr fp_load_r1
        lda r0
        ldy r0+1
        jsr FSUB
        bra fp_store_r0
fp_mul:
        jsr fp_load_r0
        lda r1
        ldy r1+1
        jsr FMULT
        bra fp_store_r0
fp_div:
        jsr fp_load_r1
        lda r0
        ldy r0+1
        jsr FDIV
        bra fp_store_r0

; fp_int: r0 = r0 rounded down to a whole number.
fp_int:
        jsr fp_load_r0
        jsr INT
; fp_store_r0: rounds FAC into the value at r0 and ends the function.
fp_store_r0:
        ldx r0
        ldy r0+1
        jsr STORE_FAC_AT_YX_ROUNDED
        clc
        rts

; fp_cmp: A = $FF when r0 is below r1, 0 when they are equal, 1 when r0 is above.
fp_cmp:
        jsr fp_load_r0
        lda r1
        ldy r1+1
        jsr FCOMP
        clc
        rts

; fp_from_long: r0 = the signed 32-bit number in r1 and r2.
fp_from_long:
        lda r1
        sta FAC+4
        lda r1+1
        sta FAC+3
        lda r2
        sta FAC+2
        lda r2+1
        sta FAC+1
        eor #$FF
        asl                     ; carry set for a number of 0 or more
        lda #0
        ldx #128 + 8 * MANTISSA_BYTES
        jsr LDB21
        bra fp_store_r0

; fp_to_long: r1 and r2 = the value at r0 rounded down, as a signed 32-bit number. Error 13 at
; 2^31 or beyond.
fp_to_long:
        jsr fp_load_r0
        jsr fp_qint
        lda FAC+4
        sta r1
        lda FAC+3
        sta r1+1
        lda FAC+2
        sta r2
        lda FAC+1
        sta r2+1
        clc
        rts

; fp_qint: QINT for a FAC below 2^31 in size, else error 13.
fp_qint:
        lda FAC
        cmp #128 + 8 * MANTISSA_BYTES
        bcs fp_bad
        jmp QINT
fp_bad:
        jmp fp_bad_data

; fp_fix: r1 = the value at r0 rounded to X decimals, as length-prefixed text: - when it is
; below 0, the digits, and a point before the decimals. r1 takes 13 bytes. Error 13 for X past
; 9, or when the size times 10^X rounds to 2^31 or more.
fp_fix:
        cpx #10
        bcs fp_bad
        stx FP_LEFT
        stx STRNG2
        jsr fp_load_r0
        lda FACSIGN
        and #$80
        sta VARPNT
        stz FACSIGN
@scale:
        dec STRNG2
        bmi @round
        jsr MUL10
        bra @scale
@round:
        jsr FADDH
        jsr fp_qint
        lda FAC+1
        ora FAC+2
        ora FAC+3
        ora FAC+4
        bne @sign
        stz VARPNT              ; 0 has no sign
@sign:
        stz STRNG2
        bit VARPNT
        bpl @digits
        lda #'-'
        jsr fp_put
@digits:
        stz DEST                ; the power's offset in fp_powers
        lda #9
        sta ARGEXTENSION        ; the power of 10
@power:
        ldy DEST
        ldx #'0' - 1
@less:
        inx                     ; take the power away until it goes below 0
        sec
        lda FAC+4
        sbc fp_powers+3,y
        sta FAC+4
        lda FAC+3
        sbc fp_powers+2,y
        sta FAC+3
        lda FAC+2
        sbc fp_powers+1,y
        sta FAC+2
        lda FAC+1
        sbc fp_powers,y
        sta FAC+1
        bcs @less
        clc                     ; then add it back once
        lda FAC+4
        adc fp_powers+3,y
        sta FAC+4
        lda FAC+3
        adc fp_powers+2,y
        sta FAC+3
        lda FAC+2
        adc fp_powers+1,y
        sta FAC+2
        lda FAC+1
        adc fp_powers,y
        sta FAC+1
        lda ARGEXTENSION
        cmp FP_LEFT
        beq @write              ; the units digit, always written
        bit VARPNT
        bvs @write              ; a digit after the first
        cpx #'0'
        beq @next               ; a 0 in front
@write:
        lda #$40
        tsb VARPNT
        txa
        jsr fp_put
        lda ARGEXTENSION
        cmp FP_LEFT
        bne @next
        tax
        beq @next               ; no decimals, no point
        lda #'.'
        jsr fp_put
@next:
        lda DEST
        clc
        adc #4
        sta DEST
        dec ARGEXTENSION
        bpl @power
        lda STRNG2
        sta (r1)
        clc
        rts

; fp_put: puts A after the text at r1 so far, STRNG2 characters long.
fp_put:
        inc STRNG2
        ldy STRNG2
        sta (r1),y
        rts

; fp_powers: 10^9 down to 10^0, 4 bytes each, high byte first.
fp_powers:
        .dbyt 1000000000 >> 16, 1000000000 & $FFFF
        .dbyt 100000000 >> 16, 100000000 & $FFFF
        .dbyt 10000000 >> 16, 10000000 & $FFFF
        .dbyt 1000000 >> 16, 1000000 & $FFFF
        .dbyt 100000 >> 16, 100000 & $FFFF
        .dbyt 0, 10000
        .dbyt 0, 1000
        .dbyt 0, 100
        .dbyt 0, 10
        .dbyt 0, 1

; fp_load_r0, fp_load_r1: FAC = the value at r0, at r1.
fp_load_r0:
        lda r0
        ldy r0+1
        jmp LOAD_FAC_FROM_YA
fp_load_r1:
        lda r1
        ldy r1+1
        jmp LOAD_FAC_FROM_YA

; ---- The copy of MSBASIC's float.s ----

; FADDH: FAC = FAC + 0.5.
FADDH:
        lda #<CON_HALF
        ldy #>CON_HALF
        jmp FADD

; FSUB: FAC = (Y,A) - FAC.
FSUB:
        jsr LOAD_ARG_FROM_YA
; FSUBT: FAC = ARG - FAC.
FSUBT:
        lda FACSIGN
        eor #$FF
        sta FACSIGN
        eor ARGSIGN
        sta SGNCPR
        lda FAC
        jmp FADDT
RTS3:
        rts

; FADD1: shifts the smaller value more than 7 bits.
FADD1:
        jsr SHIFT_RIGHT
        bcc FADD3

; FADD: FAC = (Y,A) + FAC.
FADD:
        jsr LOAD_ARG_FROM_YA
; FADDT: FAC = ARG + FAC.
FADDT:
        bne L365B
        jmp COPY_ARG_TO_FAC
L365B:
        ldx FACEXTENSION
        stx ARGEXTENSION
        ldx #ARG
        lda ARG
FADD2:
        tay
        beq RTS3
        sec
        sbc FAC
        beq FADD3
        bcc L367F
        sty FAC
        ldy ARGSIGN
        sty FACSIGN
        eor #$FF
        adc #$00
        ldy #$00
        sty ARGEXTENSION
        ldx #FAC
        bne L3683
L367F:
        ldy #$00
        sty FACEXTENSION
L3683:
        cmp #$F9
        bmi FADD1
        tay
        lda FACEXTENSION
        lsr 1,x
        jsr SHIFT_RIGHT4
FADD3:
        bit SGNCPR
        bpl FADD4
        ldy #FAC
        cpx #ARG
        beq L369B
        ldy #ARG
L369B:
        sec
        eor #$FF
        adc ARGEXTENSION
        sta FACEXTENSION
        lda 4,y
        sbc 4,x
        sta FAC+4
        lda 3,y
        sbc 3,x
        sta FAC+3
        lda 2,y
        sbc 2,x
        sta FAC+2
        lda 1,y
        sbc 1,x
        sta FAC+1

; NORMALIZE_FAC1: normalizes FAC.
NORMALIZE_FAC1:
        bcs NORMALIZE_FAC2
        jsr COMPLEMENT_FAC
NORMALIZE_FAC2:
        ldy #$00
        tya
        clc
L36C7:
        ldx FAC+1
        bne NORMALIZE_FAC4
        ldx FAC+2
        stx FAC+1
        ldx FAC+3
        stx FAC+2
        ldx FAC+4
        stx FAC+3
        ldx FACEXTENSION
        stx FAC+4
        sty FACEXTENSION
        adc #$08
        cmp #(MANTISSA_BYTES + 1) * 8
        bne L36C7

; ZERO_FAC: FAC = 0, by its exponent and sign.
ZERO_FAC:
        lda #$00
STA_IN_FAC_SIGN_AND_EXP:
        sta FAC
STA_IN_FAC_SIGN:
        sta FACSIGN
        rts

; FADD4: adds the mantissas of FAC and ARG into FAC.
FADD4:
        adc ARGEXTENSION
        sta FACEXTENSION
        lda FAC+4
        adc ARG+4
        sta FAC+4
        lda FAC+3
        adc ARG+3
        sta FAC+3
        lda FAC+2
        adc ARG+2
        sta FAC+2
        lda FAC+1
        adc ARG+1
        sta FAC+1
        jmp NORMALIZE_FAC5

; NORMALIZE_FAC3: finishes normalizing FAC.
NORMALIZE_FAC3:
        adc #$01
        asl FACEXTENSION
        rol FAC+4
        rol FAC+3
        rol FAC+2
        rol FAC+1
NORMALIZE_FAC4:
        bpl NORMALIZE_FAC3
        sec
        sbc FAC
        bcs ZERO_FAC
        eor #$FF
        adc #$01
        sta FAC
NORMALIZE_FAC5:
        bcc L3764
NORMALIZE_FAC6:
        inc FAC
        beq OVERFLOW
        ror FAC+1
        ror FAC+2
        ror FAC+3
        ror FAC+4
        ror FACEXTENSION
L3764:
        rts

; COMPLEMENT_FAC: the two's complement of FAC.
COMPLEMENT_FAC:
        lda FACSIGN
        eor #$FF
        sta FACSIGN
; COMPLEMENT_FAC_MANTISSA: the two's complement of FAC's mantissa alone.
COMPLEMENT_FAC_MANTISSA:
        lda FAC+1
        eor #$FF
        sta FAC+1
        lda FAC+2
        eor #$FF
        sta FAC+2
        lda FAC+3
        eor #$FF
        sta FAC+3
        lda FAC+4
        eor #$FF
        sta FAC+4
        lda FACEXTENSION
        eor #$FF
        sta FACEXTENSION
        inc FACEXTENSION
        bne RTS12
; INCREMENT_FAC_MANTISSA: adds 1 to FAC's mantissa.
INCREMENT_FAC_MANTISSA:
        inc FAC+4
        bne RTS12
        inc FAC+3
        bne RTS12
        inc FAC+2
        bne RTS12
        inc FAC+1
RTS12:
        rts
OVERFLOW:
        jmp fp_bad_data

; SHIFT_RIGHT: shifts 1,X to 4,X right by -A bits. Returns Y = 0, carry clear, and the bits
; shifted out in A.
SHIFT_RIGHT1:
        ldx #RESULT-1
SHIFT_RIGHT2:
        ldy 4,x
        sty FACEXTENSION
        ldy 3,x
        sty 4,x
        ldy 2,x
        sty 3,x
        ldy 1,x
        sty 2,x
        ldy SHIFTSIGNEXT
        sty 1,x
SHIFT_RIGHT:
        adc #$08
        bmi SHIFT_RIGHT2
        beq SHIFT_RIGHT2
        sbc #$08
        tay
        lda FACEXTENSION
        bcs SHIFT_RIGHT5
LB588:
        asl 1,x
        bcc LB58E
        inc 1,x
LB58E:
        ror 1,x
        ror 1,x
; SHIFT_RIGHT4: the short shifts, with no sign extension.
SHIFT_RIGHT4:
        ror 2,x
        ror 3,x
        ror 4,x
        ror a
        iny
        bne LB588
SHIFT_RIGHT5:
        clc
        rts

; FMULT: FAC = (Y,A) * FAC.
FMULT:
        jsr LOAD_ARG_FROM_YA
; FMULTT: FAC = ARG * FAC.
FMULTT:
        beq L3903
        jsr ADD_EXPONENTS
        lda #$00
        sta RESULT
        sta RESULT+1
        sta RESULT+2
        sta RESULT+3
        lda FACEXTENSION
        jsr MULTIPLY1
        lda FAC+4
        jsr MULTIPLY1
        lda FAC+3
        jsr MULTIPLY1
        lda FAC+2
        jsr MULTIPLY1
        lda FAC+1
        jsr MULTIPLY2
        jmp COPY_RESULT_INTO_FAC

; MULTIPLY1: adds ARG times A into RESULT.
MULTIPLY1:
        bne MULTIPLY2
        jmp SHIFT_RIGHT1
MULTIPLY2:
        lsr a
        ora #$80
L38A7:
        tay
        bcc L38C3
        clc
        lda RESULT+3
        adc ARG+4
        sta RESULT+3
        lda RESULT+2
        adc ARG+3
        sta RESULT+2
        lda RESULT+1
        adc ARG+2
        sta RESULT+1
        lda RESULT
        adc ARG+1
        sta RESULT
L38C3:
        ror RESULT
        ror RESULT+1
        ror RESULT+2
        ror RESULT+3
        ror FACEXTENSION
        tya
        lsr a
        bne L38A7
L3903:
        rts

; LOAD_ARG_FROM_YA: ARG = the value at (Y,A). Returns A = FAC's exponent.
LOAD_ARG_FROM_YA:
        sta INDEX
        sty INDEX+1
        ldy #BYTES_FP-1
        lda (INDEX),y
        sta ARG+4
        dey
        lda (INDEX),y
        sta ARG+3
        dey
        lda (INDEX),y
        sta ARG+2
        dey
        lda (INDEX),y
        sta ARGSIGN
        eor FACSIGN
        sta SGNCPR
        lda ARGSIGN
        ora #$80
        sta ARG+1
        dey
        lda (INDEX),y
        sta ARG
        lda FAC
        rts

; ADD_EXPONENTS: adds the exponents of ARG and FAC for FMULT and FDIV, sets the sign, and
; checks for overflow.
ADD_EXPONENTS:
        lda ARG
ADD_EXPONENTS1:
        beq ZERO
        clc
        adc FAC
        bcc L393C
        bmi JOV
        clc
        .byte $2C               ; BIT abs: skips the BPL
L393C:
        bpl ZERO
        adc #$80
        sta FAC
        bne L3947
        jmp STA_IN_FAC_SIGN
L3947:
        lda SGNCPR
        sta FACSIGN
        rts

; ZERO: pops the return address and sets FAC = 0.
ZERO:
        pla
        pla
        jmp ZERO_FAC
JOV:
        jmp OVERFLOW

; MUL10: FAC = FAC * 10.
MUL10:
        jsr COPY_FAC_TO_ARG_ROUNDED
        tax
        beq L3970
        clc
        adc #$02
        bcs JOV
        ldx #$00
        stx SGNCPR
        jsr FADD2
        inc FAC
        beq JOV
L3970:
        rts

CONTEN:
        .byte $84, $20, $00, $00, $00

; DIV10: FAC = FAC / 10.
DIV10:
        jsr COPY_FAC_TO_ARG_ROUNDED
        lda #<CONTEN
        ldy #>CONTEN
        ldx #$00
; DIV: FAC = ARG / (Y,A).
DIV:
        stx SGNCPR
        jsr LOAD_FAC_FROM_YA
        jmp FDIVT

; FDIV: FAC = (Y,A) / FAC.
FDIV:
        jsr LOAD_ARG_FROM_YA
; FDIVT: FAC = ARG / FAC. A division by 0 gives error 13.
FDIVT:
        beq L3A02
        jsr ROUND_FAC
        lda #$00
        sec
        sbc FAC
        sta FAC
        jsr ADD_EXPONENTS
        inc FAC
        beq JOV
        ldx #<-MANTISSA_BYTES
        lda #$01
L39A1:
        ldy ARG+1
        cpy FAC+1
        bne L39B7
        ldy ARG+2
        cpy FAC+2
        bne L39B7
        ldy ARG+3
        cpy FAC+3
        bne L39B7
        ldy ARG+4
        cpy FAC+4
L39B7:
        php
        rol a
        bcc L39C4
        inx
        sta RESULT_LAST-1,x
        beq L39F2
        bpl L39F6
        lda #$01
L39C4:
        plp
        bcs L39D5
L39C7:
        asl ARG_LAST
        rol ARG+3
        rol ARG+2
        rol ARG+1
        bcs L39B7
        bmi L39A1
        bpl L39B7
L39D5:
        tay
        lda ARG+4
        sbc FAC+4
        sta ARG+4
        lda ARG+3
        sbc FAC+3
        sta ARG+3
        lda ARG+2
        sbc FAC+2
        sta ARG+2
        lda ARG+1
        sbc FAC+1
        sta ARG+1
        tya
        jmp L39C7
L39F2:
        lda #$40
        bne L39C4
L39F6:
        asl a
        asl a
        asl a
        asl a
        asl a
        asl a
        sta FACEXTENSION
        plp
        jmp COPY_RESULT_INTO_FAC
L3A02:
        jmp fp_bad_data

; COPY_RESULT_INTO_FAC: moves RESULT into FAC's mantissa and normalizes.
COPY_RESULT_INTO_FAC:
        lda RESULT
        sta FAC+1
        lda RESULT+1
        sta FAC+2
        lda RESULT+2
        sta FAC+3
        lda RESULT+3
        sta FAC+4
        jmp NORMALIZE_FAC2

; LOAD_FAC_FROM_YA: FAC = the value at (Y,A).
LOAD_FAC_FROM_YA:
        sta INDEX
        sty INDEX+1
        ldy #MANTISSA_BYTES
        lda (INDEX),y
        sta FAC+4
        dey
        lda (INDEX),y
        sta FAC+3
        dey
        lda (INDEX),y
        sta FAC+2
        dey
        lda (INDEX),y
        sta FACSIGN
        ora #$80
        sta FAC+1
        dey
        lda (INDEX),y
        sta FAC
        sty FACEXTENSION
        rts

; STORE_FAC_AT_YX_ROUNDED: rounds FAC and stores it at (Y,X).
STORE_FAC_AT_YX_ROUNDED:
        jsr ROUND_FAC
        stx INDEX
        sty INDEX+1
        ldy #MANTISSA_BYTES
        lda FAC+4
        sta (INDEX),y
        dey
        lda FAC+3
        sta (INDEX),y
        dey
        lda FAC+2
        sta (INDEX),y
        dey
        lda FACSIGN
        ora #$7F
        and FAC+1
        sta (INDEX),y
        dey
        lda FAC
        sta (INDEX),y
        sty FACEXTENSION
        rts

; COPY_ARG_TO_FAC: FAC = ARG.
COPY_ARG_TO_FAC:
        lda ARGSIGN
        sta FACSIGN
        ldx #BYTES_FP
L3A7A:
        lda SHIFTSIGNEXT,x
        sta EXPSGN,x
        dex
        bne L3A7A
        stx FACEXTENSION
        rts

; COPY_FAC_TO_ARG_ROUNDED: rounds FAC and copies it to ARG.
COPY_FAC_TO_ARG_ROUNDED:
        jsr ROUND_FAC
        ldx #BYTES_FP+1
L3A89:
        lda EXPSGN,x
        sta SHIFTSIGNEXT,x
        dex
        bne L3A89
        stx FACEXTENSION
RTS14:
        rts

; ROUND_FAC: rounds FAC by its extension byte.
ROUND_FAC:
        lda FAC
        beq RTS14
        asl FACEXTENSION
        bcc RTS14
        jsr INCREMENT_FAC_MANTISSA
        bne RTS14
        jmp NORMALIZE_FAC6

; SIGN: A = 1 when FAC is above 0, 0 at 0, $FF below 0.
SIGN:
        lda FAC
        beq RTS15
L3AA7:
        lda FACSIGN
SIGN2:
        rol a
        lda #$FF
        bcs RTS15
        lda #$01
RTS15:
        rts

; FLOAT: FAC = A, signed, -128 to 127.
FLOAT:
        sta FAC+1
        lda #$00
        sta FAC+2
        ldx #$88
        lda FAC+1
        eor #$FF
        rol a
        lda #$00
        sta FAC+4
        sta FAC+3
; LDB21: FAC = the mantissa in FAC+1 to FAC+4 with exponent X; A = 0; carry clear to make it
; negative.
LDB21:
        stx FAC
        sta FACEXTENSION
        sta FACSIGN
        jmp NORMALIZE_FAC1

; FCOMP: A = 1, 0 or $FF as FAC is above, equal to or below the value at (Y,A).
FCOMP:
        sta DEST
        sty DEST+1
        ldy #$00
        lda (DEST),y
        iny
        tax
        beq SIGN
        lda (DEST),y
        eor FACSIGN
        bmi L3AA7
        cpx FAC
        bne L3B0A
        lda (DEST),y
        ora #$80
        cmp FAC+1
        bne L3B0A
        iny
        lda (DEST),y
        cmp FAC+2
        bne L3B0A
        iny
        lda (DEST),y
        cmp FAC+3
        bne L3B0A
        iny
        lda #$7F
        cmp FACEXTENSION
        lda (DEST),y
        sbc FAC_LAST
        beq L3B32
L3B0A:
        lda FACSIGN
        bcc L3B10
        eor #$FF
L3B10:
        jmp SIGN2

; QINT: turns FAC into a signed integer in FAC+1 to FAC+4 by shifting right with sign
; extension. FAC must be below 2^31 in size.
QINT:
        lda FAC
        beq QINT3
        sec
        sbc #120 + 8 * BYTES_FP
        bit FACSIGN
        bpl L3B27
        tax
        lda #$FF
        sta SHIFTSIGNEXT
        jsr COMPLEMENT_FAC_MANTISSA
        txa
L3B27:
        ldx #FAC
        cmp #$F9
        bpl QINT2
        jsr SHIFT_RIGHT
        sty SHIFTSIGNEXT
L3B32:
        rts
QINT2:
        tay
        lda FACSIGN
        and #$80
        lsr FAC+1
        ora FAC+1
        sta FAC+1
        jsr SHIFT_RIGHT4
        sty SHIFTSIGNEXT
        rts

; INT: FAC = FAC rounded down to a whole number.
INT:
        lda FAC
        cmp #120 + 8 * BYTES_FP
        bcs RTS17
        jsr QINT
        sty FACEXTENSION
        lda FACSIGN
        sty FACSIGN
        eor #$80
        rol a
        lda #120 + 8 * BYTES_FP
        sta FAC
        jmp NORMALIZE_FAC1
QINT3:
        sta FAC+1
        sta FAC+2
        sta FAC+3
        sta FAC+4
        tay
RTS17:
        rts

; FIN: FAC = the number at TXTPTR. A = its first character, carry clear for a digit.
FIN:
        ldy #$00
        ldx #SERLEN - TMPEXP
L3B6F:
        sty TMPEXP,x
        dex
        bpl L3B6F
        bcc FIN2
        cmp #'-'
        bne L3B7E
        stx SERLEN
        beq FIN1
L3B7E:
        cmp #'+'
        bne FIN3
FIN1:
        jsr CHRGET
FIN2:
        bcc FIN9
FIN3:
        cmp #'.'
        beq FIN10
        cmp #'E'
        bne FIN7
        jsr CHRGET
        bcc FIN5
        cmp #'-'
        beq L3BA6
        cmp #'+'
        beq FIN4
        bne FIN6
L3BA6:
        ror EXPSGN
FIN4:
        jsr CHRGET
FIN5:
        bcc GETEXP
FIN6:
        bit EXPSGN
        bpl FIN7
        lda #$00
        sec
        sbc EXPON
        jmp FIN8
; FIN10: a decimal point.
FIN10:
        ror LOWTR
        bit LOWTR
        bvc FIN1
; FIN7: the number ends; the exponent is applied.
FIN7:
        lda EXPON
FIN8:
        sec
        sbc INDX
        sta EXPON
        jsr FIN_FLOAT
        lda EXPON
        beq L3BEE
        bpl L3BE7
L3BDE:
        jsr DIV10
        inc EXPON
        bne L3BDE
        beq L3BEE
L3BE7:
        jsr MUL10
        dec EXPON
        bne L3BE7
L3BEE:
        lda SERLEN
        bmi L3BF3
        rts
L3BF3:
        jmp NEGOP

; FIN9: adds a digit into FAC. While FAC's exponent is 0, FAC+1 to FAC_LAST hold the digits
; so far as an integer; FIN_FLOAT makes it a float once.
FIN9:
        pha
        bit LOWTR
        bpl L3BFD
        inc INDX
L3BFD:
        lda FAC
        bne FIN_SLOW
        lda FAC+1
        cmp #$19                ; $19000000 or more could pass 32 bits after * 10
        bcc FIN_INT
        jsr FIN_FLOAT
FIN_SLOW:
        jsr MUL10
        pla
        sec
        sbc #'0'
        jsr ADDACC
        jmp FIN1

; ADDACC: FAC = FAC + A.
ADDACC:
        pha
        jsr COPY_FAC_TO_ARG_ROUNDED
        pla
        jsr FLOAT
        lda ARGSIGN
        eor FACSIGN
        sta SGNCPR
        ldx FAC
        jmp FADDT

; GETEXP: adds a digit to the exponent.
GETEXP:
        lda EXPON
        cmp #MAX_EXPON
        bcc L3C2C
        lda #$64
        bit EXPSGN
        bmi L3C3A
        jmp OVERFLOW
L3C2C:
        asl a
        asl a
        clc
        adc EXPON
        asl a
        clc
        adc (TXTPTR)
        sec
        sbc #'0'
L3C3A:
        sta EXPON
        jmp FIN4

FIN_INT:
        lda FAC+1               ; the integer still 0: add the digit alone
        ora FAC+2
        ora FAC+3
        ora FAC+4
        beq @digit
.repeat MANTISSA_BYTES, I       ; ARG = FAC
        lda FAC+1+I
        sta ARG+1+I
.endrepeat
        jsr FIN_SHL             ; FAC * 4
        jsr FIN_SHL
        clc                     ; + ARG = FAC * 5
.repeat MANTISSA_BYTES, I
        lda FAC_LAST-I
        adc ARG_LAST-I
        sta FAC_LAST-I
.endrepeat
        jsr FIN_SHL             ; FAC * 10
@digit:
        pla
        and #$0F
        clc
        adc FAC_LAST
        sta FAC_LAST
        bcc @done
        ldx #MANTISSA_BYTES-1
@carry:
        inc FAC,x
        bne @done
        dex
        bne @carry
@done:
        jmp FIN1

FIN_SHL:
        asl FAC_LAST
.repeat MANTISSA_BYTES-1, I
        rol FAC_LAST-1-I
.endrepeat
        rts

; FIN_FLOAT: floats the integer in FAC+1 to FAC_LAST, unless FAC is a float already.
FIN_FLOAT:
        lda FAC
        bne @done
        ldx #128 + 8 * MANTISSA_BYTES
        sec                     ; 0 or more; FIN applies the sign at the end
        jmp LDB21
@done:
        rts

; NEGOP: FAC = -FAC.
NEGOP:
        lda FAC
        beq L3E0F
        lda FACSIGN
        eor #$FF
        sta FACSIGN
L3E0F:
        rts

CON_99999999_9:
        .byte $9B, $3E, $BC, $1F, $FD
CON_999999999:
        .byte $9E, $6E, $6B, $27, $FD
CON_BILLION:
        .byte $9E, $6E, $6B, $28, $00

; FOUT: the text of FAC at TXTPTR + 1, with a space or - first, then a $00. Returns Y = the
; $00's offset from TXTPTR.
FOUT:
        ldy #$01
        lda #' '
        bit FACSIGN
        bpl L3C73
        lda #'-'
L3C73:
        sta (TXTPTR),y
        sta FACSIGN
        sty STRNG2
        iny
        lda #'0'
        ldx FAC
        bne L3C84
        jmp FOUT4
L3C84:
        lda #$00
        cpx #$80
        beq L3C8C
        bcs L3C95
L3C8C:
        lda #<CON_BILLION
        ldy #>CON_BILLION
        jsr FMULT
        lda #<-9
L3C95:
        sta INDX
; L3C97: brings FAC to 1E8 or more, below 1E9.
L3C97:
        lda #<CON_999999999
        ldy #>CON_999999999
        jsr FCOMP
        beq L3CBE
        bpl L3CB4
L3CA2:
        lda #<CON_99999999_9
        ldy #>CON_99999999_9
        jsr FCOMP
        beq L3CAD
        bpl L3CBB
L3CAD:
        jsr MUL10
        dec INDX
        bne L3CA2
L3CB4:
        jsr DIV10
        inc INDX
        bne L3C97
L3CBB:
        jsr FADDH
L3CBE:
        jsr QINT
; FAC+1 to FAC+4 is an integer now, with the power of ten in INDX. -10 < INDX < 1 prints
; without an exponent.
        ldx #$01
        lda INDX
        clc
        adc #3 * BYTES_FP - 5
        bmi L3CD3
        cmp #3 * BYTES_FP - 4
        bcs L3CD4
        adc #$FF
        tax
        lda #$02
L3CD3:
        sec
L3CD4:
        sbc #$02
        sta EXPON
        stx INDX
        txa
        beq L3CDF
        bpl L3CF2
L3CDF:
        ldy STRNG2
        lda #'.'
        iny
        sta (TXTPTR),y
        txa
        beq L3CF0
        lda #'0'
        iny
        sta (TXTPTR),y
L3CF0:
        sty STRNG2
; L3CF2: the digits, by the powers of ten.
L3CF2:
        ldy #$00
        ldx #$80
L3CF6:
        lda FAC_LAST
        clc
        adc DECTBL+3,y
        sta FAC+4
        lda FAC+3
        adc DECTBL+2,y
        sta FAC+3
        lda FAC+2
        adc DECTBL+1,y
        sta FAC+2
        lda FAC+1
        adc DECTBL,y
        sta FAC+1
        inx
        bcs L3D1A
        bpl L3CF6
        bmi L3D1C
L3D1A:
        bmi L3CF6
L3D1C:
        txa
        bcc L3D23
        eor #$FF
        adc #$0A
L3D23:
        adc #'0' - 1
        iny
        iny
        iny
        iny
        sty VARPNT
        ldy STRNG2
        iny
        tax
        and #$7F
        sta (TXTPTR),y
        dec INDX
        bne L3D3E
        lda #'.'
        iny
        sta (TXTPTR),y
L3D3E:
        sty STRNG2
        ldy VARPNT
        txa
        eor #$FF
        and #$80
        tax
        cpy #DECTBL_END - DECTBL
        bne L3CF6
; Nine digits are written. The trailing zeros and a trailing point go.
        ldy STRNG2
L3D4E:
        lda (TXTPTR),y
        dey
        cmp #'0'
        beq L3D4E
        cmp #'.'
        beq L3D5B
        iny
L3D5B:
        lda #'+'
        ldx EXPON
        beq L3D8F
        bpl L3D6B
        lda #$00
        sec
        sbc EXPON
        tax
        lda #'-'
L3D6B:
        pha
        iny
        lda #'E'
        sta (TXTPTR),y
        iny
        pla
        sta (TXTPTR),y
        txa
        ldx #'0' - 1
        sec
L3D77:
        inx
        sbc #$0A
        bcs L3D77
        adc #'9' + 1
        pha
        txa
        iny
        sta (TXTPTR),y
        pla
        iny
FOUT4:
        sta (TXTPTR),y
L3D8F:
        iny
        lda #$00
        sta (TXTPTR),y
        rts

CON_HALF:
        .byte $80, $00, $00, $00, $00

; DECTBL: the powers of 10 from 1E8 down to 1, as 32-bit integers with alternate signs.
DECTBL:
        .byte $FA, $0A, $1F, $00        ; -100000000
        .byte $00, $98, $96, $80        ; 10000000
        .byte $FF, $F0, $BD, $C0        ; -1000000
        .byte $00, $01, $86, $A0        ; 100000
        .byte $FF, $FF, $D8, $F0        ; -10000
        .byte $00, $00, $03, $E8        ; 1000
        .byte $FF, $FF, $FF, $9C        ; -100
        .byte $00, $00, $00, $0A        ; 10
        .byte $FF, $FF, $FF, $FF        ; -1
DECTBL_END:
