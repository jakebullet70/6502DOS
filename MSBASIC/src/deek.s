; DEEK function and DOKE statement (CONFIG_DEEK).

; ----------------------------------------------------------------------------
; "DEEK" FUNCTION: DEEK(ADDR), 0 <= ADDR <= 65535
; RETURNS THE 16-BIT WORD AT ADDR (LOW BYTE FIRST), UNSIGNED 0-65535.
; CALLED FROM UNARY WITH THE ARGUMENT IN FAC. LINNUM IS KEPT, SO
; DOKE A,DEEK(B) AND POKE A,DEEK(B) WORK.
; ----------------------------------------------------------------------------
DEEK:
        lda     LINNUM+1
        pha
        lda     LINNUM
        pha
        jsr     GETADR
        ldy     #$00
        lda     (LINNUM),y
        sta     FAC+2
        iny
        lda     (LINNUM),y
        sta     FAC+1
        pla
        sta     LINNUM
        pla
        sta     LINNUM+1
        ldx     #$90
        sec			; positive
        jmp     FLOAT2

; ----------------------------------------------------------------------------
; "DOKE" STATEMENT: DOKE ADDR,N, 0 <= ADDR <= 65535, -65535 <= N <= 65535
; STORES N AS A 16-BIT WORD AT ADDR (LOW BYTE FIRST). A NEGATIVE N IS
; TAKEN MOD 65536 (TWO'S COMPLEMENT: DOKE A,-1 STORES $FFFF).
; ----------------------------------------------------------------------------
DOKE:
        jsr     FRMNUM
        jsr     GETADR
        jsr     CHKCOM
        jsr     FRMNUM
        lda     FAC
        cmp     #$91		; |N| < 65536
        bcc     L_DOKE1
        jmp     IQERR
L_DOKE1:
        jsr     QINT
        ldy     #$00
        lda     FAC_LAST
        sta     (LINNUM),y
        iny
        lda     FAC_LAST-1
        sta     (LINNUM),y
        rts
