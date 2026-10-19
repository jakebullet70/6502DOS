; $hex and %binary number literals (CONFIG_RADIX_LIT, needs CONFIG_FAST_FIN).

; ----------------------------------------------------------------------------
; CALLED FROM FIN WITH THE FIRST CHARACTER (NOT A DIGIT) IN A.
; "$" READS HEX DIGITS (0-9, A-F, a-f), "%" READS BINARY DIGITS; ANY OTHER
; CHARACTER RETURNS TO FIN. THE VALUE IS UNSIGNED, UP TO 32 BITS
; ($FFFFFFFF = 4294967295), ELSE ?OVERFLOW. NO DIGITS GIVES 0, LIKE VAL("").
; THE DIGITS ARE SHIFTED INTO FAC+1..4 (CLEARED BY FIN), THEN FLOATED.
; RETURNS TO FIN'S CALLER.
; ----------------------------------------------------------------------------
LIT_FIN:
        cmp     #'$'
        beq     L_LIT0
        cmp     #'%'
        bne     L_LIT4		; keep X and Y for FIN
        ldx     #$01		; bits per digit
        ldy     #2		; radix
        bne     L_LIT1
L_LIT0:
        ldx     #$04
        ldy     #16
L_LIT1:
        pla			; drop the return into FIN
        pla
        stx     EXPON
        sty     EXPSGN
L_LIT2:
        jsr     CHRGET
        jsr     LIT_DIGIT
        cmp     EXPSGN
        bcs     L_LIT5
        ldx     EXPON
L_LIT3:
        asl     FAC+4
        rol     FAC+3
        rol     FAC+2
        rol     FAC+1
        bcs     L_LIT6
        dex
        bne     L_LIT3
        ora     FAC+4
        sta     FAC+4
        bcc     L_LIT2		; carry is clear
L_LIT4:
        rts
L_LIT5:
        jmp     FIN_FLOAT
L_LIT6:
        jmp     OVERFLOW

; ----------------------------------------------------------------------------
; A = CHARACTER; RETURNS A = ITS HEX DIGIT VALUE, OR 16 OR MORE IF IT IS
; NOT A HEX DIGIT
; ----------------------------------------------------------------------------
LIT_DIGIT:
        cmp     #'a'
        bcc     L_DIG1
        sbc     #$20		; carry is set: fold a-f to A-F
L_DIG1:
        sec
        sbc     #'0'
        cmp     #10
        bcc     L_DIG2
        sbc     #7		; carry is set: "A" gives 10
        cmp     #10
        bcs     L_DIG2
        lda     #$FF		; between "9" and "A"
L_DIG2:
        rts

; ----------------------------------------------------------------------------
; CALLED FROM PARSE_INPUT_LINE FOR A "$" AT INPUTBUFFERX,X. AFTER A LETTER
; OR DIGIT IT IS A TYPE SUFFIX (A$, B1$): RETURNS C=0 AND A = "$".
; ELSE IT STARTS A HEX LITERAL: THE "$" AND THE HEX DIGITS AFTER IT ARE
; STORED UNTOKENIZED (SO $DEF IS NOT READ AS THE DEF KEYWORD) AND IN
; UPPERCASE; RETURNS C=1 WITH X AND Y ADVANCED PAST THEM.
; ----------------------------------------------------------------------------
LIT_TOKEN:
        lda     INPUTBUFFER-5,y	; last stored byte
        jsr     ISLETC
        bcs     L_TOK1
        cmp     #'0'
        bcc     L_TOK2
        cmp     #'9'+1
        bcs     L_TOK2
L_TOK1:
        lda     #'$'
        clc
        rts
L_TOK2:
        lda     #'$'
L_TOK3:
        inx
        iny
        sta     INPUTBUFFER-5,y
        lda     INPUTBUFFERX,x
.ifdef SIM
        jsr     SIM_UPPER
.endif
        pha
        jsr     LIT_DIGIT
        cmp     #16
        pla
        bcc     L_TOK3
        rts			; C=1
