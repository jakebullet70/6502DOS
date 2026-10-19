; INSTR function (CONFIG_INSTR).

; ----------------------------------------------------------------------------
; "INSTR" FUNCTION: INSTR([START,] A$, B$)
; RETURNS THE 1-BASED POSITION OF B$ IN A$ AT OR AFTER START, OR 0.
; AN EMPTY B$ RETURNS START WHEN START <= LEN(A$)+1.
; ----------------------------------------------------------------------------
INSTR:
        jsr     CHRGET
        jsr     CHKOPN
        jsr     FRMEVL
        ldx     #$01
        bit     VALTYP
        bmi     L_INSTR1
        jsr     CONINT
        txa
        bne     L_INSTR0
        jmp     IQERR
L_INSTR0:
        pha
        jsr     CHKCOM
        jsr     FRMEVL
        jmp     L_INSTR2
L_INSTR1:
        txa
        pha
L_INSTR2:
        jsr     CHKSTR
        lda     FAC_LAST-1
        pha
        lda     FAC_LAST
        pha
        jsr     CHKCOM
        jsr     FRMEVL
        jsr     CHKCLS
        jsr     FRESTR		; release B$ first: it is the newer temporary
        sta     TEMP3		; TEMP3 = LEN(B$)
        lda     INDEX
        sta     STRNG2		; STRNG2 = B$ text
        lda     INDEX+1
        sta     STRNG2+1
        pla
        tay
        pla
        jsr     FRETMP		; release A$
        sta     TEMP3+1		; TEMP3+1 = LEN(A$), INDEX = A$ text
        pla
        tax
        dex
        stx     DSCPTR		; DSCPTR = 0-based position
        txa
        cmp     TEMP3+1
        beq     L_INSTR3
        bcs     L_INSTR_ZERO	; START > LEN(A$)+1
L_INSTR3:
        ldy     TEMP3
        beq     L_INSTR_FOUND	; empty B$
        lda     TEMP3+1
        sec
        sbc     DSCPTR
        sbc     TEMP3
        bcc     L_INSTR_ZERO	; B$ does not fit
        sta     DSCPTR+1	; DSCPTR+1 = positions left after this one
        lda     INDEX
        clc
        adc     DSCPTR
        sta     INDEX
        bcc     L_INSTR_TRY
        inc     INDEX+1
L_INSTR_TRY:
        ldy     TEMP3
L_INSTR_CMP:
        dey
        lda     (INDEX),y
        cmp     (STRNG2),y
        bne     L_INSTR_NEXT
        tya
        bne     L_INSTR_CMP
L_INSTR_FOUND:
        ldy     DSCPTR
        iny
        bne     L_INSTR_RET
L_INSTR_NEXT:
        lda     DSCPTR+1
        beq     L_INSTR_ZERO
        dec     DSCPTR+1
        inc     DSCPTR
        inc     INDEX
        bne     L_INSTR_TRY
        inc     INDEX+1
        bne     L_INSTR_TRY
L_INSTR_ZERO:
        ldy     #$00
L_INSTR_RET:
        ldx     #$00
        stx     VALTYP
        jmp     SNGFLT
