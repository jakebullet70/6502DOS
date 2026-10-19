; MOD operator (CONFIG_MOD).

; ----------------------------------------------------------------------------
; "MOD" OPERATOR: FAC = ARG MOD FAC, QBASIC STYLE
; BOTH OPERANDS ARE ROUNDED TO THE NEAREST INTEGER (HALF AWAY FROM ZERO);
; |N| MUST BE BELOW 2^31 (ELSE ?OVERFLOW). THE RESULT HAS THE SIGN OF THE
; LEFT OPERAND: -7 MOD 3 = -1. A ZERO RIGHT OPERAND GIVES ?DIVISION BY ZERO.
; THE REMAINDER COMES FROM A 32-BIT SHIFT-AND-SUBTRACT DIVISION:
; DIVIDEND IN FAC+1..4, REMAINDER IN ARG+1..4, DIVISOR IN RESULT..RESULT+3.
; ----------------------------------------------------------------------------
MODT:
        jsr     STORE_FAC_IN_TEMP1_ROUNDED	; save the divisor
        jsr     COPY_ARG_TO_FAC
        lda     FACSIGN
        pha				; sign of the result
        jsr     L_MODINT
        ldx     #$03
L_MOD1:
        lda     FAC+1,x
        sta     RESULT,x
        dex
        bpl     L_MOD1
        lda     #TEMP1X
        ldy     #$00
        jsr     LOAD_FAC_FROM_YA
        jsr     L_MODINT
        lda     FAC+1
        ora     FAC+2
        ora     FAC+3
        ora     FAC+4
        bne     L_MOD2
        ldx     #ERR_ZERODIV
        jmp     ERROR
L_MOD2:
        ldx     #$03		; divisor to RESULT, dividend to FAC, clear ARG
L_MOD3:
        lda     FAC+1,x
        ldy     RESULT,x
        sta     RESULT,x
        sty     FAC+1,x
        lda     #$00
        sta     ARG+1,x
        dex
        bpl     L_MOD3
        ldy     #32
L_MOD4:
        asl     FAC+4
        rol     FAC+3
        rol     FAC+2
        rol     FAC+1
        rol     ARG+4
        rol     ARG+3
        rol     ARG+2
        rol     ARG+1
        ldx     #$00		; remainder >= divisor?
L_MOD5:
        lda     ARG+1,x
        cmp     RESULT,x
        bne     L_MOD6
        inx
        cpx     #$04
        bne     L_MOD5
L_MOD6:
        bcc     L_MOD8
        ldx     #$03
L_MOD7:
        lda     ARG+1,x
        sbc     RESULT,x
        sta     ARG+1,x
        dex
        bpl     L_MOD7
L_MOD8:
        dey
        bne     L_MOD4
        ldx     #$03
L_MOD9:
        lda     ARG+1,x
        sta     FAC+1,x
        dex
        bpl     L_MOD9
        pla
        sta     FACSIGN
        sty     FACEXTENSION	; Y = 0
        lda     #120+8*BYTES_FP
        sta     FAC
        jmp     NORMALIZE_FAC2

; ----------------------------------------------------------------------------
; FAC+1..4 = ROUND(|FAC|) AS A 32-BIT INTEGER, ?OVERFLOW IF 2^31 OR MORE
; ----------------------------------------------------------------------------
L_MODINT:
        lda     #$00
        sta     FACSIGN
        lda     #<CON_HALF
        ldy     #>CON_HALF
        jsr     FADD
        lda     FAC
        cmp     #120+8*BYTES_FP
        bcc     L_MODINT1
        jmp     OVERFLOW
L_MODINT1:
        jmp     QINT
