; Simple variable lookup cache (CONFIG_VAR_CACHE).

; ----------------------------------------------------------------------------
; PTRGET SEARCHES VARTAB FROM THE START FOR EVERY SIMPLE VARIABLE. A SIMPLE
; VARIABLE NEVER MOVES ONCE MADE (NEW ONES GO AT THE END OF VARTAB AND ONLY
; THE ARRAYS MOVE UP), SO THE CACHE MAPS THE NAME IN VARNAM TO THE ADDRESS
; OF ITS 7-BYTE ENTRY. VARTAB ONLY CHANGES THROUGH SETPTRS, WHICH RUNS
; CLEARC, AND CLEARC EMPTIES THE CACHE (NEW, RUN, CLR, PROGRAM LINE ENTRY).
; ARRAYS ARE NOT CACHED.
; DIRECT-MAPPED: VC_KLO = 0 IS EMPTY (A NAME STARTS WITH A LETTER).
; ----------------------------------------------------------------------------
VC_SIZE = 64
VC_MASK = VC_SIZE-1

; ----------------------------------------------------------------------------
; LOOK UP VARNAM. HIT: LOWTR = ENTRY, X = LOWTR+1, CARRY SET.
; MISS: CARRY CLEAR. THE INDEX IS KEPT IN VC_IDX FOR VC_STORE.
; SINGLE-LETTER FLOATS GET SLOTS 1-26; STRINGS AND INTEGERS ARE MOVED AWAY.
; ----------------------------------------------------------------------------
VC_FIND:
        lda     VARNAM+1
        asl
        adc     VARNAM
        bit     VARNAM+1
        bpl     L_VC1
        eor     #$20		; string or integer
        bit     VARNAM
        bpl     L_VC1
        eor     #$10		; integer
L_VC1:
        and     #VC_MASK
        tax
        stx     VC_IDX
        lda     VARNAM
        cmp     VC_KLO,x
        bne     L_VC2
        lda     VARNAM+1
        cmp     VC_KHI,x
        bne     L_VC2
        lda     VC_VLO,x
        sta     LOWTR
        lda     VC_VHI,x
        sta     LOWTR+1
        tax
        sec
        rts
L_VC2:
        clc
        rts

; ----------------------------------------------------------------------------
; REMEMBER LOWTR AS THE ENTRY FOR VARNAM (AFTER VC_FIND MISSED; CHANGES A, X)
; ----------------------------------------------------------------------------
VC_STORE:
        ldx     VC_IDX
        lda     VARNAM
        sta     VC_KLO,x
        lda     VARNAM+1
        sta     VC_KHI,x
        lda     LOWTR
        sta     VC_VLO,x
        lda     LOWTR+1
        sta     VC_VHI,x
        rts

; ----------------------------------------------------------------------------
; EMPTY THE CACHE (CALLED FROM CLEARC; CHANGES A AND X)
; ----------------------------------------------------------------------------
VC_CLEAR:
        lda     #$00
        ldx     #VC_MASK
L_VC3:
        sta     VC_KLO,x
        dex
        bpl     L_VC3
        rts

.segment "IORAM"
VC_IDX:	.res 1
VC_KLO:	.res VC_SIZE
VC_KHI:	.res VC_SIZE
VC_VLO:	.res VC_SIZE
VC_VHI:	.res VC_SIZE
.segment "EXTRA"
