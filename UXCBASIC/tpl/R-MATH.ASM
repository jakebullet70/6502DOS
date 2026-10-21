; R-MATH.ASM -- the runtime routines for *, / and MOD.

; A/Y = the WORD on the stack times A/Y, the low 16 bits. Pops the stack.
R_MULW  .block
        #tpl
        dex
        dex
        sta ZP_TMP              ; the right side, shifted out a bit at a time
        sty ZP_TMP+1
        stz ZP_PTR              ; the product
        stz ZP_PTR+1
loop    lda ZP_TMP
        ora ZP_TMP+1
        beq done                ; no bits left
        lsr ZP_TMP+1
        ror ZP_TMP
        bcc next
        clc
        lda ZP_PTR
        adc ESTK,x
        sta ZP_PTR
        lda ZP_PTR+1
        adc ESTK+1,x
        sta ZP_PTR+1
next    asl ESTK,x              ; the left side, doubled for each bit
        rol ESTK+1,x
        bra loop
done    lda ZP_PTR
        ldy ZP_PTR+1
        rts
        #endtpl
        .endblock

; A/Y = the WORD on the stack divided by A/Y, unsigned, and ZP_PTR = the remainder. Pops the
; stack. A divisor of 0 stops the program with ?DIVISION BY ZERO ERROR.
R_DIVW  .block
        #tpl
        dex
        dex
        sta ZP_TMP              ; the divisor
        sty ZP_TMP+1
        ora ZP_TMP+1
        bne ok
        #rec jmp, R_EDIVZ
ok      stz ZP_PTR              ; the remainder
        stz ZP_PTR+1
        ldy #16
loop    asl ESTK,x              ; the dividend turns into the quotient, a bit at a time
        rol ESTK+1,x
        rol ZP_PTR
        rol ZP_PTR+1
        bcs sub                 ; a 17th bit: the divisor surely goes in
        lda ZP_PTR
        cmp ZP_TMP
        lda ZP_PTR+1
        sbc ZP_TMP+1
        bcc next
sub     lda ZP_PTR              ; C is set on both ways in
        sbc ZP_TMP
        sta ZP_PTR
        lda ZP_PTR+1
        sbc ZP_TMP+1
        sta ZP_PTR+1
        inc ESTK,x              ; this quotient bit is 1
next    dey
        bne loop
        lda ESTK,x
        ldy ESTK+1,x
        rts
        #endtpl
        .endblock

; A/Y = the WORD on the stack divided by A/Y, signed, rounded toward 0, and ZP_PTR = the
; remainder, which has the sign of the dividend. Pops the stack.
R_DIVS  .block
        #tpl
        sta ZP_TMP              ; the divisor
        sty ZP_TMP+1
        tya
        eor ESTK-1,x
        pha                     ; bit 7: the quotient is negative
        lda ESTK-1,x
        pha                     ; bit 7: the remainder is negative
        bpl divisor
        sec                     ; the dividend made positive
        lda #0
        sbc ESTK-2,x
        sta ESTK-2,x
        lda #0
        sbc ESTK-1,x
        sta ESTK-1,x
divisor lda ZP_TMP
        ldy ZP_TMP+1
        bpl divide
        sec                     ; the divisor made positive
        lda #0
        sbc ZP_TMP
        pha
        lda #0
        sbc ZP_TMP+1
        tay
        pla
divide  #rec jsr, R_DIVW
        sta ZP_TMP              ; the quotient
        sty ZP_TMP+1
        pla
        bpl quotient
        sec                     ; the remainder made negative
        lda #0
        sbc ZP_PTR
        sta ZP_PTR
        lda #0
        sbc ZP_PTR+1
        sta ZP_PTR+1
quotient pla
        bpl done
        sec                     ; the quotient made negative
        lda #0
        sbc ZP_TMP
        sta ZP_TMP
        lda #0
        sbc ZP_TMP+1
        sta ZP_TMP+1
done    lda ZP_TMP
        ldy ZP_TMP+1
        rts
        #endtpl
        .endblock

; The high words of the expression stack: R_ESTKH,x is the high word of the LONG at ESTK,x.
R_ESTKH .block
        #data 32, 0
        .endblock

; A/Y/ZP_HI = 0 - A/Y/ZP_HI
R_NEGL  .block
        #tpl
        eor #$ff
        clc
        adc #1
        pha
        tya
        eor #$ff
        adc #0
        tay
        lda ZP_HI
        eor #$ff
        adc #0
        sta ZP_HI
        lda ZP_HI+1
        eor #$ff
        adc #0
        sta ZP_HI+1
        pla
        rts
        #endtpl
        .endblock

; ZP_LL = A/Y/ZP_HI
R_LTOZ  .block
        #tpl
        sta ZP_LL
        sty ZP_LL+1
        lda ZP_HI
        sta ZP_LL+2
        lda ZP_HI+1
        sta ZP_LL+3
        rts
        #endtpl
        .endblock

; ZP_LR = A/Y/ZP_HI, and ZP_LL = the LONG popped off the stack.
R_LARGS .block
        #tpl
        dex
        dex
        sta ZP_LR
        sty ZP_LR+1
        lda ZP_HI
        sta ZP_LR+2
        lda ZP_HI+1
        sta ZP_LR+3
        lda ESTK,x
        sta ZP_LL
        lda ESTK+1,x
        sta ZP_LL+1
        #recx lda, R_ESTKH
        sta ZP_LL+2
        #recx lda, R_ESTKH, 1
        sta ZP_LL+3
        rts
        #endtpl
        .endblock

; A/Y/ZP_HI = ZP_LL
R_LQUOT .block
        #tpl
        lda ZP_LL+2
        sta ZP_HI
        lda ZP_LL+3
        sta ZP_HI+1
        lda ZP_LL
        ldy ZP_LL+1
        rts
        #endtpl
        .endblock

; A/Y/ZP_HI = ZP_LX
R_LREM  .block
        #tpl
        lda ZP_LX+2
        sta ZP_HI
        lda ZP_LX+3
        sta ZP_HI+1
        lda ZP_LX
        ldy ZP_LX+1
        rts
        #endtpl
        .endblock

; A/Y/ZP_HI = the LONG at ESTK,x, the one just popped.
R_LPOP  .block
        #tpl
        #recx lda, R_ESTKH
        sta ZP_HI
        #recx lda, R_ESTKH, 1
        sta ZP_HI+1
        lda ESTK,x
        ldy ESTK+1,x
        rts
        #endtpl
        .endblock

; A/Y/ZP_HI = the LONG on the stack times A/Y/ZP_HI, the low 32 bits. Pops the stack.
R_MULL  .block
        #tpl
        #rec jsr, R_LARGS
        stz ZP_LX               ; the product
        stz ZP_LX+1
        stz ZP_LX+2
        stz ZP_LX+3
        ldy #32
loop    asl ZP_LX               ; the product doubled for each bit of the right side
        rol ZP_LX+1
        rol ZP_LX+2
        rol ZP_LX+3
        asl ZP_LR               ; the right side's top bit
        rol ZP_LR+1
        rol ZP_LR+2
        rol ZP_LR+3
        bcc next
        clc
        lda ZP_LX
        adc ZP_LL
        sta ZP_LX
        lda ZP_LX+1
        adc ZP_LL+1
        sta ZP_LX+1
        lda ZP_LX+2
        adc ZP_LL+2
        sta ZP_LX+2
        lda ZP_LX+3
        adc ZP_LL+3
        sta ZP_LX+3
next    dey
        bne loop
        #rec jmp, R_LREM
        #endtpl
        .endblock

; ZP_LL = ZP_LL / ZP_LR, unsigned, and ZP_LX = the remainder. A divisor of 0 stops the
; program with ?DIVISION BY ZERO ERROR.
R_UDIVL .block
        #tpl
        lda ZP_LR
        ora ZP_LR+1
        ora ZP_LR+2
        ora ZP_LR+3
        bne ok
        #rec jmp, R_EDIVZ
ok      stz ZP_LX
        stz ZP_LX+1
        stz ZP_LX+2
        stz ZP_LX+3
        ldy #32
loop    asl ZP_LL               ; the dividend turns into the quotient, a bit at a time
        rol ZP_LL+1
        rol ZP_LL+2
        rol ZP_LL+3
        rol ZP_LX
        rol ZP_LX+1
        rol ZP_LX+2
        rol ZP_LX+3
        bcs sub                 ; a 33rd bit: the divisor surely goes in
        lda ZP_LX
        cmp ZP_LR
        lda ZP_LX+1
        sbc ZP_LR+1
        lda ZP_LX+2
        sbc ZP_LR+2
        lda ZP_LX+3
        sbc ZP_LR+3
        bcc next
sub     lda ZP_LX               ; C is set on both ways in
        sbc ZP_LR
        sta ZP_LX
        lda ZP_LX+1
        sbc ZP_LR+1
        sta ZP_LX+1
        lda ZP_LX+2
        sbc ZP_LR+2
        sta ZP_LX+2
        lda ZP_LX+3
        sbc ZP_LR+3
        sta ZP_LX+3
        inc ZP_LL               ; this quotient bit is 1
next    dey
        bne loop
        rts
        #endtpl
        .endblock

; A/Y/ZP_HI = the LONG on the stack divided by A/Y/ZP_HI, unsigned. Pops the stack.
R_DIVL  .block
        #tpl
        #rec jsr, R_LARGS
        #rec jsr, R_UDIVL
        #rec jmp, R_LQUOT
        #endtpl
        .endblock

; A/Y/ZP_HI = the LONG on the stack MOD A/Y/ZP_HI, unsigned. Pops the stack.
R_MODL  .block
        #tpl
        #rec jsr, R_LARGS
        #rec jsr, R_UDIVL
        #rec jmp, R_LREM
        #endtpl
        .endblock

; ZP_LL = the LONG on the stack divided by A/Y/ZP_HI, signed, rounded toward 0, and ZP_LX =
; the remainder, which has the sign of the dividend. Pops the stack.
R_SDIVL .block
        #tpl
        #rec jsr, R_LARGS
        lda ZP_LL+3
        eor ZP_LR+3
        pha                     ; bit 7: the quotient is negative
        lda ZP_LL+3
        pha                     ; bit 7: the remainder is negative
        bpl divisor
        lda #ZP_LL
        #self jsr, negate
divisor bit ZP_LR+3
        bpl divide
        lda #ZP_LR
        #self jsr, negate
divide  #rec jsr, R_UDIVL
        pla
        bpl quotient
        lda #ZP_LX
        #self jsr, negate
quotient pla
        bpl done
        lda #ZP_LL
        #self jsr, negate
done    rts
negate  phx                     ; the 4 bytes at the zero page address in A = 0 - them
        tax
        sec
        lda #0
        sbc 0,x
        sta 0,x
        lda #0
        sbc 1,x
        sta 1,x
        lda #0
        sbc 2,x
        sta 2,x
        lda #0
        sbc 3,x
        sta 3,x
        plx
        rts
        #endtpl
        .endblock

; A/Y/ZP_HI = the LONG on the stack divided by A/Y/ZP_HI, signed. Pops the stack.
R_DIVLS .block
        #tpl
        #rec jsr, R_SDIVL
        #rec jmp, R_LQUOT
        #endtpl
        .endblock

; A/Y/ZP_HI = the LONG on the stack MOD A/Y/ZP_HI, signed. Pops the stack.
R_MODLS .block
        #tpl
        #rec jsr, R_SDIVL
        #rec jmp, R_LREM
        #endtpl
        .endblock

; A/Y/ZP_HI = the LONG on the stack << A. Pops the stack.
R_SHLL  .block
        #tpl
        dex
        dex
        tay
        beq done
loop    asl ESTK,x
        rol ESTK+1,x
        #recx rol, R_ESTKH
        #recx rol, R_ESTKH, 1
        dey
        bne loop
done    #rec jmp, R_LPOP
        #endtpl
        .endblock

; A/Y/ZP_HI = the LONG on the stack >> A. Pops the stack.
R_SHRL  .block
        #tpl
        dex
        dex
        tay
        beq done
loop    #recx lsr, R_ESTKH, 1
        #recx ror, R_ESTKH
        ror ESTK+1,x
        ror ESTK,x
        dey
        bne loop
done    #rec jmp, R_LPOP
        #endtpl
        .endblock

; A/Y/ZP_HI = the LONG on the stack >> A, the sign kept. Pops the stack.
R_SARL  .block
        #tpl
        dex
        dex
        tay
        beq done
loop    #recx lda, R_ESTKH, 1
        asl a                   ; C = the sign
        #recx ror, R_ESTKH, 1
        #recx ror, R_ESTKH
        ror ESTK+1,x
        ror ESTK,x
        dey
        bne loop
done    #rec jmp, R_LPOP
        #endtpl
        .endblock
