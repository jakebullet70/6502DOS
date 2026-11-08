; RPT$ function (CONFIG_RPT).

; ----------------------------------------------------------------------------
; "RPT$" FUNCTION: RPT$(A$, N) OR RPT$(C, N)
; RETURNS A$ REPEATED N TIMES, OR CHR$(C) REPEATED N TIMES (0 <= N <= 255).
; A RESULT LONGER THAN 255 CHARACTERS GIVES ?STRING TOO LONG.
; ----------------------------------------------------------------------------
RPTSTR:
        jsr     CHRGET
        jsr     CHKOPN
        jsr     FRMSTRCHR	; A$, or CHR$(C)
        lda     FAC_LAST-1	; keep the descriptor address
        pha
        lda     FAC_LAST
        pha
        jsr     CHKCOM
        jsr     GETBYT		; X = N
        jsr     CHKCLS
        pla
        sta     DSCPTR+1
        pla
        sta     DSCPTR
        txa
        pha
        ldy     #$00
        tya
        cpx     #$00
        beq     L_RPT3
L_RPT2:
        clc
        adc     (DSCPTR),y	; total length = LEN * N
        bcc     L_RPT2A
        ldx     #ERR_STRLONG
        jmp     ERROR
L_RPT2A:
        dex
        bne     L_RPT2
L_RPT3:
        jsr     STRSPA		; may collect garbage; DSCPTR stays valid
        lda     DSCPTR
        ldy     DSCPTR+1
        jsr     FRETMP		; A = LEN, INDEX = text
        sta     DSCPTR
        pla
        tax
        beq     L_RPT5
L_RPT4:
        lda     DSCPTR
        jsr     MOVSTR1		; copy one LEN to FRESPC and advance it
        dex
        bne     L_RPT4
L_RPT5:
        jmp     PUTNEW

.ifndef CONFIG_TEXTAT
; FRMSTRCHR: AS IN TEXTAT.S, FOR A BUILD WITHOUT TEXTAT.
FRMSTRCHR:
        jsr     FRMEVL
        bit     VALTYP
        bmi     L_RPT6		; a string
        jsr     CHRSTR		; a code: returns to our caller
L_RPT6:
        rts
.endif
