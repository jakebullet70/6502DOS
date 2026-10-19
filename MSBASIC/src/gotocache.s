; GOTO target cache (CONFIG_GOTO_CACHE).

; ----------------------------------------------------------------------------
; GOTO, GOSUB, IF ... THEN <LINE>, ON ... GOTO/GOSUB AND RUN <LINE> ALL REACH
; GOTO WITH TXTPTR ON THE FIRST CHARACTER OF THE LINE NUMBER. IN A PROGRAM THAT
; ADDRESS ALWAYS LEADS TO THE SAME TARGET, SO IT IS THE CACHE KEY AND THE VALUE
; IS THE TXTPTR THAT GOTO LEAVES. DIRECT-MODE LINES ARE NOT CACHED (THE INPUT
; BUFFER IS REUSED). CLEARC EMPTIES THE CACHE; IT RUNS ON NEW, RUN, CLR AND
; EVERY PROGRAM LINE ENTRY.
; DIRECT-MAPPED: ENTRY = LOW BYTE OF THE KEY AND GC_MASK. GC_KHI = 0 IS EMPTY
; (A PROGRAM NEVER LIVES IN THE ZERO PAGE).
; ----------------------------------------------------------------------------
GC_SIZE = 64
GC_MASK = GC_SIZE-1

GOTO_CACHED:
        ldx     CURLIN+1
        inx
        bne     L_GC1
        jmp     GOTO_SLOW	; direct mode; X and INX keep the carry
L_GC1:
        lda     TXTPTR
        and     #GC_MASK
        tax
        lda     TXTPTR
        cmp     GC_KLO,x
        bne     L_GC2
        lda     TXTPTR+1
        cmp     GC_KHI,x
        bne     L_GC2
        lda     GC_VLO,x
        sta     TXTPTR
        lda     GC_VHI,x
        sta     TXTPTR+1
        rts
L_GC2:
        lda     TXTPTR+1
        pha
        lda     TXTPTR
        pha
        jsr     CHRGOT		; LINGET needs the carry of the first digit
        jsr     GOTO_SLOW	; UNDERR does not come back
        pla
        tay
        and     #GC_MASK
        tax
        tya
        sta     GC_KLO,x
        pla
        sta     GC_KHI,x
        lda     TXTPTR
        sta     GC_VLO,x
        lda     TXTPTR+1
        sta     GC_VHI,x
        rts

; ----------------------------------------------------------------------------
; EMPTY THE CACHE (CALLED FROM CLEARC; CHANGES A AND X)
; ----------------------------------------------------------------------------
GC_CLEAR:
        lda     #$00
        ldx     #GC_MASK
L_GC3:
        sta     GC_KHI,x
        dex
        bpl     L_GC3
        rts

.segment "IORAM"
GC_KLO:	.res GC_SIZE
GC_KHI:	.res GC_SIZE
GC_VLO:	.res GC_SIZE
GC_VHI:	.res GC_SIZE
.segment "EXTRA"
