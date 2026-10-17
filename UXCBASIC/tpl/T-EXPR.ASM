; T-EXPR.ASM -- the operators.
;
; A binary operator is compiled as: the left side, then T_PUSH or T_PUSHB, then the right side,
; then the operator's template. The template pops the left side and leaves the result in A (a
; BYTE) or A/Y (a WORD). The B form works on two BYTEs; the W form on two WORDs, a BYTE side
; being widened first. *, / and MOD are always WORD.

; A = left + A
T_ADDB  .block
        #tpl
        dex
        dex
        clc
        adc ESTK,x
        #endtpl
        .endblock

; A/Y = left + A/Y
T_ADDW  .block
        #tpl
        dex
        dex
        clc
        adc ESTK,x
        pha
        tya
        adc ESTK+1,x
        tay
        pla
        #endtpl
        .endblock

; A = left - A, worked as left + ~A + 1
T_SUBB  .block
        #tpl
        dex
        dex
        eor #$ff
        sec
        adc ESTK,x
        #endtpl
        .endblock

; A/Y = left - A/Y
T_SUBW  .block
        #tpl
        dex
        dex
        eor #$ff
        sec
        adc ESTK,x
        pha
        tya
        eor #$ff
        adc ESTK+1,x
        tay
        pla
        #endtpl
        .endblock

; A = left AND A
T_ANDB  .block
        #tpl
        dex
        dex
        and ESTK,x
        #endtpl
        .endblock

; A/Y = left AND A/Y
T_ANDW  .block
        #tpl
        dex
        dex
        and ESTK,x
        pha
        tya
        and ESTK+1,x
        tay
        pla
        #endtpl
        .endblock

; A = left OR A
T_ORB   .block
        #tpl
        dex
        dex
        ora ESTK,x
        #endtpl
        .endblock

; A/Y = left OR A/Y
T_ORW   .block
        #tpl
        dex
        dex
        ora ESTK,x
        pha
        tya
        ora ESTK+1,x
        tay
        pla
        #endtpl
        .endblock

; A = left XOR A
T_XORB  .block
        #tpl
        dex
        dex
        eor ESTK,x
        #endtpl
        .endblock

; A/Y = left XOR A/Y
T_XORW  .block
        #tpl
        dex
        dex
        eor ESTK,x
        pha
        tya
        eor ESTK+1,x
        tay
        pla
        #endtpl
        .endblock

; A = left << A
T_SHLB  .block
        #tpl
        dex
        dex
        tay
        beq done
loop    asl ESTK,x
        dey
        bne loop
done    lda ESTK,x
        #endtpl
        .endblock

; A/Y = left << A. Only the low byte of the count is used.
T_SHLW  .block
        #tpl
        dex
        dex
        tay
        beq done
loop    asl ESTK,x
        rol ESTK+1,x
        dey
        bne loop
done    lda ESTK,x
        ldy ESTK+1,x
        #endtpl
        .endblock

; A = left >> A
T_SHRB  .block
        #tpl
        dex
        dex
        tay
        beq done
loop    lsr ESTK,x
        dey
        bne loop
done    lda ESTK,x
        #endtpl
        .endblock

; A/Y = left >> A. Only the low byte of the count is used.
T_SHRW  .block
        #tpl
        dex
        dex
        tay
        beq done
loop    lsr ESTK+1,x
        ror ESTK,x
        dey
        bne loop
done    lda ESTK,x
        ldy ESTK+1,x
        #endtpl
        .endblock

; A/Y = left * A/Y
T_MUL   .block
        #tpl
        #rec jsr, R_MULW
        #endtpl
        .endblock

; A/Y = left / A/Y
T_DIV   .block
        #tpl
        #rec jsr, R_DIVW
        #endtpl
        .endblock

; A/Y = left MOD A/Y
T_MOD   .block
        #tpl
        #rec jsr, R_DIVW
        lda ZP_PTR
        ldy ZP_PTR+1
        #endtpl
        .endblock

; A = -A
T_NEGB  .block
        #tpl
        eor #$ff
        inc a
        #endtpl
        .endblock

; A/Y = -A/Y
T_NEGW  .block
        #tpl
        eor #$ff
        clc
        adc #1
        pha
        tya
        eor #$ff
        adc #0
        tay
        pla
        #endtpl
        .endblock

; A = NOT A: 1 when A is 0, else 0.
T_NOTB  .block
        #tpl
        cmp #1                  ; C = A is not 0
        lda #0
        rol a
        eor #1
        #endtpl
        .endblock

; A = NOT A/Y: 1 when A/Y is 0, else 0. The result is a BYTE.
T_NOTW  .block
        #tpl
        sty ZP_TMP
        ora ZP_TMP
        cmp #1
        lda #0
        rol a
        eor #1
        #endtpl
        .endblock

; The compares. A compare is a core, which sets a flag, then a tail, which turns the flag into
; a BYTE 0 or 1. IF and the loops follow the same cores with a branch instead of a tail.
;
;   op    BYTE               WORD
;   =     CMPB_RL, ZTRUE     CMPW_EQ, ZTRUE
;   <>    CMPB_RL, ZFALSE    CMPW_EQ, ZFALSE
;   >=    CMPB_LR, CTRUE     CMPW_LR, CTRUE
;   <     CMPB_LR, CFALSE    CMPW_LR, CFALSE
;   <=    CMPB_RL, CTRUE     CMPW_RL, CTRUE
;   >     CMPB_RL, CFALSE    CMPW_RL, CFALSE

; C = left >= A, Z = left = A
T_CMPB_LR .block
        #tpl
        dex
        dex
        eor #$ff
        sec
        adc ESTK,x
        #endtpl
        .endblock

; C = A >= left, Z = left = A
T_CMPB_RL .block
        #tpl
        dex
        dex
        cmp ESTK,x
        #endtpl
        .endblock

; C = left >= A/Y
T_CMPW_LR .block
        #tpl
        dex
        dex
        eor #$ff
        sec
        adc ESTK,x
        tya
        eor #$ff
        adc ESTK+1,x
        #endtpl
        .endblock

; C = A/Y >= left
T_CMPW_RL .block
        #tpl
        dex
        dex
        cmp ESTK,x
        tya
        sbc ESTK+1,x
        #endtpl
        .endblock

; Z = left = A/Y
T_CMPW_EQ .block
        #tpl
        dex
        dex
        cmp ESTK,x
        bne done
        tya
        cmp ESTK+1,x
done
        #endtpl
        .endblock

; A = C
T_CTRUE .block
        #tpl
        lda #0
        rol a
        #endtpl
        .endblock

; A = not C
T_CFALSE .block
        #tpl
        lda #0
        rol a
        eor #1
        #endtpl
        .endblock

; A = Z, which is bit 1 of P
T_ZTRUE .block
        #tpl
        php
        pla
        lsr a
        and #1
        #endtpl
        .endblock

; A = not Z
T_ZFALSE .block
        #tpl
        php
        pla
        lsr a
        and #1
        eor #1
        #endtpl
        .endblock

; A = left >> A, the sign kept
T_SARB  .block
        #tpl
        dex
        dex
        tay
        beq done
loop    lda ESTK,x
        asl a                   ; C = the sign
        ror ESTK,x
        dey
        bne loop
done    lda ESTK,x
        #endtpl
        .endblock

; A/Y = left >> A, the sign kept. Only the low byte of the count is used.
T_SARW  .block
        #tpl
        dex
        dex
        tay
        beq done
loop    lda ESTK+1,x
        asl a                   ; C = the sign
        ror ESTK+1,x
        ror ESTK,x
        dey
        bne loop
done    lda ESTK,x
        ldy ESTK+1,x
        #endtpl
        .endblock

; A/Y = left / A/Y, signed
T_DIVS  .block
        #tpl
        #rec jsr, R_DIVS
        #endtpl
        .endblock

; A/Y = left MOD A/Y, signed
T_MODS  .block
        #tpl
        #rec jsr, R_DIVS
        lda ZP_PTR
        ldy ZP_PTR+1
        #endtpl
        .endblock

; The signed compares. Each gives C as its unsigned form does, for signed values; Z is not
; set. After the subtract, N xor V is the signed "less than", and it is turned into C.

; C = left >= A, signed. A is lost.
T_SCMPB_LR .block
        #tpl
        dex
        dex
        eor #$ff
        sec
        adc ESTK,x
        bvs done
        eor #$80
done    asl a
        #endtpl
        .endblock

; C = A >= left, signed. A is lost.
T_SCMPB_RL .block
        #tpl
        dex
        dex
        sec
        sbc ESTK,x
        bvs done
        eor #$80
done    asl a
        #endtpl
        .endblock

; C = left >= A/Y, signed. A is lost.
T_SCMPW_LR .block
        #tpl
        dex
        dex
        eor #$ff
        sec
        adc ESTK,x
        tya
        eor #$ff
        adc ESTK+1,x
        bvs done
        eor #$80
done    asl a
        #endtpl
        .endblock

; C = A/Y >= left, signed. A is lost.
T_SCMPW_RL .block
        #tpl
        dex
        dex
        cmp ESTK,x
        tya
        sbc ESTK+1,x
        bvs done
        eor #$80
done    asl a
        #endtpl
        .endblock

; LONG operators: the left side is on the stack, the right side in A/Y/ZP_HI, and the result
; is in A/Y/ZP_HI.

; A/Y/ZP_HI = left + A/Y/ZP_HI
T_ADDL  .block
        #tpl
        dex
        dex
        clc
        adc ESTK,x
        pha
        tya
        adc ESTK+1,x
        tay
        lda ZP_HI
        #recx adc, R_ESTKH
        sta ZP_HI
        lda ZP_HI+1
        #recx adc, R_ESTKH, 1
        sta ZP_HI+1
        pla
        #endtpl
        .endblock

; A/Y/ZP_HI = left - A/Y/ZP_HI
T_SUBL  .block
        #tpl
        dex
        dex
        sta ZP_TMP
        sty ZP_TMP+1
        sec
        lda ESTK,x
        sbc ZP_TMP
        pha
        lda ESTK+1,x
        sbc ZP_TMP+1
        tay
        #recx lda, R_ESTKH
        sbc ZP_HI
        sta ZP_HI
        #recx lda, R_ESTKH, 1
        sbc ZP_HI+1
        sta ZP_HI+1
        pla
        #endtpl
        .endblock

; A/Y/ZP_HI = left AND A/Y/ZP_HI
T_ANDL  .block
        #tpl
        dex
        dex
        and ESTK,x
        pha
        tya
        and ESTK+1,x
        tay
        lda ZP_HI
        #recx and, R_ESTKH
        sta ZP_HI
        lda ZP_HI+1
        #recx and, R_ESTKH, 1
        sta ZP_HI+1
        pla
        #endtpl
        .endblock

; A/Y/ZP_HI = left OR A/Y/ZP_HI
T_ORL   .block
        #tpl
        dex
        dex
        ora ESTK,x
        pha
        tya
        ora ESTK+1,x
        tay
        lda ZP_HI
        #recx ora, R_ESTKH
        sta ZP_HI
        lda ZP_HI+1
        #recx ora, R_ESTKH, 1
        sta ZP_HI+1
        pla
        #endtpl
        .endblock

; A/Y/ZP_HI = left XOR A/Y/ZP_HI
T_XORL  .block
        #tpl
        dex
        dex
        eor ESTK,x
        pha
        tya
        eor ESTK+1,x
        tay
        lda ZP_HI
        #recx eor, R_ESTKH
        sta ZP_HI
        lda ZP_HI+1
        #recx eor, R_ESTKH, 1
        sta ZP_HI+1
        pla
        #endtpl
        .endblock

; A/Y/ZP_HI += the constant S0 + 65536 x S1
T_ADDL_C .block
        #tpl
        clc
        #lo adc, S0
        pha
        tya
        #hi adc, S0
        tay
        lda ZP_HI
        #lo adc, S1
        sta ZP_HI
        lda ZP_HI+1
        #hi adc, S1
        sta ZP_HI+1
        pla
        #endtpl
        .endblock

; A/Y/ZP_HI -= the constant S0 + 65536 x S1
T_SUBL_C .block
        #tpl
        sec
        #lo sbc, S0
        pha
        tya
        #hi sbc, S0
        tay
        lda ZP_HI
        #lo sbc, S1
        sta ZP_HI
        lda ZP_HI+1
        #hi sbc, S1
        sta ZP_HI+1
        pla
        #endtpl
        .endblock

; Z = left = A/Y/ZP_HI. A is lost.
T_CMPL_EQ .block
        #tpl
        dex
        dex
        cmp ESTK,x
        bne done
        tya
        cmp ESTK+1,x
        bne done
        lda ZP_HI
        #recx cmp, R_ESTKH
        bne done
        lda ZP_HI+1
        #recx cmp, R_ESTKH, 1
done
        #endtpl
        .endblock

; C = left >= A/Y/ZP_HI. A is lost.
T_CMPL_LR .block
        #tpl
        dex
        dex
        sta ZP_TMP
        sty ZP_TMP+1
        lda ESTK,x
        cmp ZP_TMP
        lda ESTK+1,x
        sbc ZP_TMP+1
        #recx lda, R_ESTKH
        sbc ZP_HI
        #recx lda, R_ESTKH, 1
        sbc ZP_HI+1
        #endtpl
        .endblock

; C = A/Y/ZP_HI >= left. A is lost.
T_CMPL_RL .block
        #tpl
        dex
        dex
        cmp ESTK,x
        tya
        sbc ESTK+1,x
        lda ZP_HI
        #recx sbc, R_ESTKH
        lda ZP_HI+1
        #recx sbc, R_ESTKH, 1
        #endtpl
        .endblock

; C = left >= A/Y/ZP_HI, signed. A is lost.
T_SCMPL_LR .block
        #tpl
        dex
        dex
        sta ZP_TMP
        sty ZP_TMP+1
        lda ESTK,x
        cmp ZP_TMP
        lda ESTK+1,x
        sbc ZP_TMP+1
        #recx lda, R_ESTKH
        sbc ZP_HI
        #recx lda, R_ESTKH, 1
        sbc ZP_HI+1
        bvs done
        eor #$80
done    asl a
        #endtpl
        .endblock

; C = A/Y/ZP_HI >= left, signed. A is lost.
T_SCMPL_RL .block
        #tpl
        dex
        dex
        cmp ESTK,x
        tya
        sbc ESTK+1,x
        lda ZP_HI
        #recx sbc, R_ESTKH
        lda ZP_HI+1
        #recx sbc, R_ESTKH, 1
        bvs done
        eor #$80
done    asl a
        #endtpl
        .endblock

; A/Y/ZP_HI = 0 - A/Y/ZP_HI
T_NEGL  .block
        #tpl
        #rec jsr, R_NEGL
        #endtpl
        .endblock

; Z = A/Y/ZP_HI is 0. A is lost.
T_TSTL  .block
        #tpl
        sty ZP_TMP
        ora ZP_TMP
        ora ZP_HI
        ora ZP_HI+1
        #endtpl
        .endblock

; A/Y/ZP_HI = left * A/Y/ZP_HI, the low 32 bits
T_MULL  .block
        #tpl
        #rec jsr, R_MULL
        #endtpl
        .endblock

; A/Y/ZP_HI = left / A/Y/ZP_HI
T_DIVL  .block
        #tpl
        #rec jsr, R_DIVL
        #endtpl
        .endblock

; A/Y/ZP_HI = left MOD A/Y/ZP_HI
T_MODL  .block
        #tpl
        #rec jsr, R_MODL
        #endtpl
        .endblock

; A/Y/ZP_HI = left / A/Y/ZP_HI, signed
T_DIVLS .block
        #tpl
        #rec jsr, R_DIVLS
        #endtpl
        .endblock

; A/Y/ZP_HI = left MOD A/Y/ZP_HI, signed
T_MODLS .block
        #tpl
        #rec jsr, R_MODLS
        #endtpl
        .endblock

; A/Y/ZP_HI = left << A
T_SHLL  .block
        #tpl
        #rec jsr, R_SHLL
        #endtpl
        .endblock

; A/Y/ZP_HI = left >> A
T_SHRL  .block
        #tpl
        #rec jsr, R_SHRL
        #endtpl
        .endblock

; A/Y/ZP_HI = left >> A, the sign kept
T_SARL  .block
        #tpl
        #rec jsr, R_SARL
        #endtpl
        .endblock
