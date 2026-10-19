; UCASE$ and LCASE$ functions (CONFIG_CASE).

; ----------------------------------------------------------------------------
; "UCASE$" AND "LCASE$" FUNCTIONS: UCASE$(A$), LCASE$(A$)
; RETURN A COPY OF A$ WITH THE ASCII LETTERS a-z TURNED INTO A-Z (UCASE$)
; OR A-Z INTO a-z (LCASE$). OTHER CHARACTERS ARE COPIED UNCHANGED.
; CALLED FROM UNARY WITH THE ARGUMENT IN FAC; RETURNS A STRING LIKE CHR$
; (DROPS UNARY'S RETURN SO ITS CHKNUM IS SKIPPED).
; ----------------------------------------------------------------------------
UCASESTR:
        lda     #$61		; first letter to change: "a"
        .byte   $2C
LCASESTR:
        lda     #$41		; "A"
        pha
        jsr     CHKSTR
        ldy     #$00
        lda     (FAC_LAST-1),y	; A = LEN
        jsr     STRINI		; may collect garbage; DSCPTR stays valid
        lda     DSCPTR
        ldy     DSCPTR+1
        jsr     FRETMP		; A = LEN, INDEX = text
        tay
        pla
        sta     DSCPTR		; DSCPTR is free now: holds the first letter
        pla
        pla
        tya
        beq     L_CASE3
L_CASE1:
        dey
        lda     (INDEX),y
        pha
        sec
        sbc     DSCPTR
        cmp     #26		; C = 0 if the character is a letter to change
        pla
        bcs     L_CASE2
        eor     #$20
L_CASE2:
        sta     (FAC+1),y
        tya
        bne     L_CASE1
L_CASE3:
        jmp     PUTNEW
