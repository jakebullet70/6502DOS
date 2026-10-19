; XOR, SHL and SHR functions (CONFIG_BITFN).

; ----------------------------------------------------------------------------
; "XOR", "SHL" AND "SHR" FUNCTIONS: XOR(A, B), SHL(A, N), SHR(A, N)
; A AND B ARE 16-BIT: -65535 <= A, B <= 65535, A NEGATIVE VALUE IS TAKEN
; MOD 65536 (LIKE HEX$). 0 <= N <= 255; N >= 16 GIVES 0. SHR IS A LOGICAL
; SHIFT (ZEROS COME IN AT THE TOP). THE RESULT IS SIGNED 16-BIT LIKE AND
; AND OR (-32768..32767), SO IT FITS A % VARIABLE: SHL(1, 15) = -32768.
; CALLED FROM FRM_ELEMENT WITH THE TOKEN IN A.
; ----------------------------------------------------------------------------
BITFN:
        pha			; token
        jsr     CHRGET
        jsr     CHKOPN
        jsr     FRMNUM
        jsr     L_BIT16
        lda     FAC_LAST-1	; first argument, high byte
        pha
        lda     FAC_LAST
        pha
        jsr     CHKCOM
        tsx
        lda     STACK+3,x	; token
        cmp     #TOKEN_XOR
        bne     L_BIT1
        jsr     FRMNUM
        jsr     CHKCLS
        jsr     L_BIT16
        pla
        eor     FAC_LAST
        sta     INDEX
        pla
        eor     FAC_LAST-1
        sta     INDEX+1
        pla			; token, not zero
        bne     L_BIT4
L_BIT1:
        jsr     GETBYT		; X = N
        jsr     CHKCLS
        pla
        sta     INDEX
        pla
        sta     INDEX+1
        pla			; token
        cpx     #$00
        beq     L_BIT4
        cmp     #TOKEN_SHL
        bne     L_BIT3
L_BIT2:
        asl     INDEX
        rol     INDEX+1
        dex
        bne     L_BIT2
        beq     L_BIT4
L_BIT3:
        lsr     INDEX+1
        ror     INDEX
        dex
        bne     L_BIT3
L_BIT4:
        ldy     INDEX
        lda     INDEX+1
        jmp     GIVAYF

; ----------------------------------------------------------------------------
; FAC_LAST-1 (HIGH), FAC_LAST (LOW) = FAC MOD 65536, ?ILLEGAL QUANTITY IF
; |FAC| >= 65536
; ----------------------------------------------------------------------------
L_BIT16:
        lda     FAC
        cmp     #$91
        bcc     L_BIT5
        jmp     IQERR
L_BIT5:
        jmp     QINT
