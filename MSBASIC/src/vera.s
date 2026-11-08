; VPEEK function, VPOKE and SCREEN statements (CONFIG_VERA), like XC=BASIC's.

; ----------------------------------------------------------------------------
; "VPEEK" FUNCTION: VPEEK(ADDR), 0 <= ADDR <= $1FFFF
; RETURNS THE BYTE AT ADDR IN VIDEO MEMORY. THE TARGET PRIMITIVE K_VPEEK
; DOES THE READ (SIM: A STUB THAT GIVES 0). LINNUM IS KEPT, SO
; VPOKE A,VPEEK(C) WORKS. CALLED FROM FRM_ELEMENT WITH THE TOKEN IN A.
; ----------------------------------------------------------------------------
VPEEK:
        lda     LINNUM+1
        pha
        lda     LINNUM
        pha
        jsr     CHRGET
        jsr     CHKOPN
        jsr     FRMNUM
        jsr     CHKCLS
        jsr     GETVADR		; LINNUM = address, A = bit 16
        jsr     K_VPEEK
        tay
        pla
        sta     LINNUM
        pla
        sta     LINNUM+1
        jmp     SNGFLT

; ----------------------------------------------------------------------------
; "POINT" FUNCTION: POINT(X, Y), 0 <= X <= 32767, 0 <= Y <= 255
; RETURNS THE COLOR OF THE PIXEL AT X, Y. X AND Y ARE IN THE RANGES OF THE
; SCREEN; SCREEN 0 IS OUT OF CONTRACT. THE TARGET PRIMITIVE K_POINT DOES THE
; READ (SIM: A STUB THAT GIVES 0). LINNUM, VADR AND VARG ARE KEPT, SO
; PSET X, Y, POINT(X2, Y2) WORKS. CALLED FROM FRM_ELEMENT WITH THE TOKEN IN A.
; ----------------------------------------------------------------------------
VPOINT:
        jsr     CHRGET
        jsr     CHKOPN
        jsr     FRMNUM
        jsr     MKINT			; FAC_LAST-1, FAC_LAST = x
        lda     FAC_LAST-1
        pha
        lda     FAC_LAST
        pha
        jsr     COMBYTE			; X = y
        jsr     CHKCLS
        pla
        tay
        pla				; A:Y = x
        jsr     K_POINT
        tay
        jmp     SNGFLT

; ----------------------------------------------------------------------------
; "VPOKE" STATEMENT: VPOKE ADDR, N, 0 <= ADDR <= $1FFFF, 0 <= N <= 255
; STORES N AT ADDR IN VIDEO MEMORY. THE TARGET PRIMITIVE K_VPOKE
; DOES THE WRITE (SIM: A STUB THAT DOES NOTHING).
; ----------------------------------------------------------------------------
VPOKE:
        jsr     FRMNUM
        jsr     GETVADR		; LINNUM = address, A = bit 16
        pha
        jsr     COMBYTE		; X = N
        pla
        jmp     K_VPOKE

; ----------------------------------------------------------------------------
; "SCREEN" STATEMENT: SCREEN MODE, 0 <= MODE <= 3
; SETS THE SCREEN MODE. THE TARGET PRIMITIVE K_SCREEN DOES THE WORK AND
; DECIDES WHAT EACH MODE MEANS (SIM: A STUB THAT DOES NOTHING).
; ----------------------------------------------------------------------------
SCREEN:
        jsr     GETBYT		; X = mode
        jmp     K_SCREEN

; ----------------------------------------------------------------------------
; "PSET" STATEMENT: PSET X, Y, C, 0 <= C <= 255
; SETS THE PIXEL AT X, Y TO COLOR C. X, Y AND C ARE IN THE RANGES OF THE
; SCREEN; SCREEN 0 IS OUT OF CONTRACT. THE TARGET PRIMITIVE K_PSET DOES THE
; WORK (SIM: A STUB THAT DOES NOTHING).
; ----------------------------------------------------------------------------
PSET:
        jsr     VGETXY		; VADR = x, VARG = y
        jsr     COMBYTE		; X = C
        txa
        jmp     K_PSET

; ----------------------------------------------------------------------------
; "LINE", "FRAME" AND "RECT" STATEMENTS: LINE X1, Y1, X2, Y2, C
; LINE DRAWS THE LINE FROM X1, Y1 TO X2, Y2, BOTH ENDS INCLUDED. FRAME DRAWS
; THE EDGE OF THE BOX WITH CORNERS X1, Y1 AND X2, Y2; RECT FILLS IT. FRAME AND
; RECT TAKE X1 <= X2 AND Y1 <= Y2. X, Y AND C ARE IN THE RANGES OF THE SCREEN;
; SCREEN 0 IS OUT OF CONTRACT. THE TARGET PRIMITIVE K_SHAPE DOES THE WORK
; (SIM: A STUB THAT DOES NOTHING).
; ----------------------------------------------------------------------------
LINE:
        lda     #4			; call 62's line
        .byte   $2C			; skips the lda
FRAME:
        lda     #5			; call 62's frame
        .byte   $2C			; skips the lda
RECT:
        lda     #6			; call 62's rect
        pha
        jsr     VGETXY			; x1, y1
        ldx     #3
@keep:
        lda     VADR,x
        sta     VXY,x
        dex
        bpl     @keep
        jsr     CHKCOM
        jsr     VGETXY			; x2, y2
        jsr     COMBYTE			; X = C
        pla
        tay
        txa
        jmp     K_SHAPE

; ----------------------------------------------------------------------------
; "CIRCLE" STATEMENT: CIRCLE X, Y, R, C, 0 <= R <= 255
; DRAWS THE CIRCLE OF RADIUS R ABOUT X, Y IN COLOR C. X, Y, C AND THE CIRCLE
; ARE IN THE RANGES OF THE SCREEN; SCREEN 0 IS OUT OF CONTRACT. THE TARGET PRIMITIVE
; K_CIRCLE DOES THE WORK (SIM: A STUB THAT DOES NOTHING).
; ----------------------------------------------------------------------------
CIRCLE:
        jsr     VGETXY			; VADR = x, VARG = y
        jsr     VGETLEN			; LINNUM = R
        jsr     COMBYTE			; X = C
        txa
        jmp     K_CIRCLE

; ----------------------------------------------------------------------------
; "CHAR" STATEMENT: CHAR X, Y, A$, C OR CHAR X, Y, CODE, C, 0 <= CODE <= 255
; DRAWS A$, OR CHR$(CODE), ON THE BITMAP: THE FIRST CHARACTER'S TOP LEFT AT
; X, Y, EACH NEXT ONE 8 PIXELS TO THE RIGHT. A GLYPH'S SET BITS TAKE COLOR C;
; ITS CLEAR BITS KEEP THE BITMAP. X, Y, C AND EVERY GLYPH ARE IN THE RANGES
; OF THE SCREEN; SCREEN 0 IS OUT OF CONTRACT. THE TARGET PRIMITIVE K_CHAR
; DOES THE WORK (SIM: A STUB THAT DOES NOTHING).
; ----------------------------------------------------------------------------
CHAR:
        jsr     VGETXY			; VADR = x, VARG = y
        jsr     CHKCOM
        jsr     FRMSTRCHR		; A$, or CHR$(code)
        lda     FAC_LAST-1		; keep the descriptor address
        pha
        lda     FAC_LAST
        pha
        jsr     COMBYTE			; X = C
        stx     VBANK
        pla
        tay
        pla
        jsr     FRETMP			; A = LEN, INDEX = the text
        jmp     K_CHAR

.segment "IORAM"
; Trap: 6502dos_extra.s's DOS_VBLK copies VADR and VARG as one run of 4 bytes,
; and K_SHAPE copies VXY, VADR and VARG as one run of 8.
VXY:	.res 4		; LINE, FRAME, RECT: x1, y1; CHAR: the characters left
VADR:	.res 2		; VMEMSET, MEMCPYMV, MEMCPYVM: the video address, bits 0 to 15
VARG:	.res 2		; VMEMSET: the byte; MEMCPYMV, MEMCPYVM: the RAM address
VBANK:	.res 1		; bit 16 of VADR; SPRITE: the sprite; CHAR: the color
.segment "EXTRA"

; ----------------------------------------------------------------------------
; "VMEMSET" STATEMENT: VMEMSET ADDR, N, LEN
; WRITES N TO LEN BYTES OF VIDEO MEMORY FROM ADDR. LEN = 0 WRITES NONE.
; THE TARGET PRIMITIVE K_VMEMSET DOES THE WRITE.
; ----------------------------------------------------------------------------
VMEMSET:
        jsr     VGETV
        jsr     COMBYTE		; X = N
        stx     VARG
        jsr     VGETLEN
        jmp     K_VMEMSET

; ----------------------------------------------------------------------------
; "MEMCPYMV" STATEMENT: MEMCPYMV RAM, ADDR, LEN
; COPIES LEN BYTES FROM RAM TO VIDEO MEMORY AT ADDR. LEN = 0 COPIES NONE.
; THE TARGET PRIMITIVE K_VWRITE DOES THE COPY.
; ----------------------------------------------------------------------------
MEMCPYMV:
        jsr     VGETR
        jsr     CHKCOM
        jsr     VGETV
        jsr     VGETLEN
        jmp     K_VWRITE

; ----------------------------------------------------------------------------
; "MEMCPYVM" STATEMENT: MEMCPYVM ADDR, RAM, LEN
; COPIES LEN BYTES FROM VIDEO MEMORY AT ADDR TO RAM. LEN = 0 COPIES NONE.
; THE TARGET PRIMITIVE K_VREAD DOES THE COPY.
; ----------------------------------------------------------------------------
MEMCPYVM:
        jsr     VGETV
        jsr     CHKCOM
        jsr     VGETR
        jsr     VGETLEN
        jmp     K_VREAD

; ----------------------------------------------------------------------------
; "VLOAD" STATEMENT: VLOAD "NAME", ADDR
; COPIES THE WHOLE FILE, RAW, TO VIDEO MEMORY FROM ADDR. THE TARGET
; PRIMITIVE K_VLOAD OPENS, READS AND CLOSES THE FILE (SIM: A STUB THAT DOES
; NOTHING). A MISSING FILE IS ?FILE NOT FOUND ERROR.
; ----------------------------------------------------------------------------
VLOAD:
        jsr     HIO_GETNAME
        jsr     CHKCOM
        jsr     VGETV
        jmp     K_VLOAD

; X = 8, 16, 32 OR 64 PIXELS; RETURNS X = THE SPRITE SIZE CODE, 0 TO 3.
SPR_SIZE:
        txa
        ldx     #$FC
@halve:
        inx
        lsr
        bne     @halve
        rts

; EVALUATES 0 TO 65535 INTO VADR.
SPR_WORD:
        jsr     FRMNUM
        jsr     GETADR			; A = high byte, Y = low byte
        sty     VADR
        sta     VADR+1
SPR_END:
        rts

; ----------------------------------------------------------------------------
; "SPRITE" STATEMENT: SPRITE N CLAUSE ..., 0 <= N <= 127, OR SPRITE CLEAR HIT
; RUNS THE CLAUSES ON SPRITE N, IN ANY ORDER:
;   ON, OFF         Z-DEPTH 3, 0
;   AT X,Y          THE POSITION, 0 TO 65535 EACH
;   SHAPE S         THE SHAPE AT VIDEO ADDRESS S*32
;   COLOR C         THE PALETTE OFFSET, 0 TO 15
;   LOWCOL, HICOL   4, 8 BITS A PIXEL
;   XYSIZE W,H      THE SIZE: 8, 16, 32 OR 64 PIXELS EACH
;   XYFLIP X,Y      FLIP ACROSS, DOWN: 0 OR 1 EACH
;   ZDEPTH Z        0 OFF, 1 BEHIND LAYER 0, 2 BETWEEN THE LAYERS, 3 IN FRONT
;   MASK M          THE COLLISION MASK, 0 TO 15
; SPRITE CLEAR HIT CLEARS THE GROUPS THAT SPRITEHIT REPORTS. THE TARGET
; PRIMITIVES K_SPRSET, K_SPRMOVE, K_SPRSHAPE AND K_SPRCLEAR DO THE WORK (SIM:
; STUBS THAT DO NOTHING). VBANK HOLDS N.
; ----------------------------------------------------------------------------
SPRITE:
        cmp     #TOKEN_CLEAR
        bne     @number
        jsr     CHRGET			; to HIT
        jmp     SPR_CLAUSE
@number:
        jsr     GETBYT			; X = N
        stx     VBANK
SPR_CLAUSE:
        jsr     CHRGOT
        beq     SPR_END			; the end of the statement
        ldx     #SPR_ON_AT
        cmp     #TOKEN_ON
        beq     @run
        ldx     #SPR_COLOR_AT
        cmp     #TOKEN_COLOR
        beq     @run
        sec
        sbc     #TOKEN_OFF
        cmp     #TOKEN_HIT+1-TOKEN_OFF
        bcs     SPR_SN
        asl
        tax
@run:
        jsr     SPR_RUN
        jmp     SPR_CLAUSE
SPR_SN:
        jmp     SYNERR

; RUNS THE CLAUSE AT SPR_TABLE,X, WITH CHRGET'S A AND FLAGS PAST ITS TOKEN.
SPR_RUN:
        lda     SPR_TABLE+1,x
        pha
        lda     SPR_TABLE,x
        pha
        jmp     CHRGET

; THE CLAUSES, LESS 1, FOR THE RTS OF CHRGET: TOKEN_OFF TO TOKEN_HIT IN ORDER,
; THEN ON AND COLOR.
SPR_TABLE:
        .addr   SPR_OFF-1, SPR_AT-1, SPR_SHAPE-1, SPR_LOWCOL-1, SPR_HICOL-1
        .addr   SPR_XYSIZE-1, SPR_XYFLIP-1, SPR_ZDEPTH-1, SPR_MASK-1
        .addr   K_SPRCLEAR-1
SPR_ON_AT = * - SPR_TABLE
        .addr   SPR_ON-1
SPR_COLOR_AT = * - SPR_TABLE
        .addr   SPR_COLOR-1
        .assert SPR_ON_AT = 2 * (TOKEN_HIT+1-TOKEN_OFF), error, "SPR_TABLE needs a clause for each token"

SPR_ON:
        ldx     #3
        .byte   $2C			; skips the ldx
SPR_OFF:
        ldx     #0
        lda     #0			; field 0, the depth
        beq     SPR_SETX		; always
SPR_HICOL:
        ldx     #1
        .byte   $2C			; skips the ldx
SPR_LOWCOL:
        ldx     #0
        lda     #6			; field 6, the mode
        bne     SPR_SETX		; always
SPR_XYFLIP:
        jsr     GETBYT			; X = across
        stx     VADR
        jsr     COMBYTE			; X = down
        txa
        asl
        ora     VADR
        tax
        lda     #1			; field 1, the flip
        bne     SPR_SETX		; always
SPR_XYSIZE:
        jsr     GETBYT
        jsr     SPR_SIZE
        lda     #4			; field 4, the width
        jsr     SPR_SETX
        jsr     COMBYTE
        jsr     SPR_SIZE
        lda     #5			; field 5, the height
        bne     SPR_SETX		; always
SPR_ZDEPTH:
        lda     #0
        .byte   $2C			; skips the lda
SPR_MASK:
        lda     #2
        .byte   $2C			; skips the lda
SPR_COLOR:
        lda     #3
        pha
        jsr     GETBYT			; X = the value
        pla
; SETS FIELD A OF SPRITE VBANK TO X.
SPR_SETX:
        stx     VADR
        jmp     K_SPRSET

SPR_SHAPE:
        jsr     SPR_WORD
        jmp     K_SPRSHAPE
SPR_AT:
        jsr     VGETXY
        jmp     K_SPRMOVE

; EVALUATES "X, Y", 0 TO 65535 EACH, INTO VADR AND VARG.
VGETXY:
        jsr     SPR_WORD		; x
        jsr     CHKCOM
        jmp     VGETR			; y

; ----------------------------------------------------------------------------
; "SPRITEHIT" FUNCTION: SPRITEHIT(G), 0 <= G <= 3
; -1 IF SPRITES THAT SHARE BIT G OF THEIR MASKS COLLIDED SINCE THE LAST
; SPRITE CLEAR HIT, ELSE 0. THE TARGET PRIMITIVE K_SPRHITS GIVES THE GROUPS
; (SIM: 0).
; ----------------------------------------------------------------------------
SPRITEHIT:
        jsr     CONINT			; X = G
        lda     #0
        sec
@bit:
        rol
        dex
        bpl     @bit			; A = 1 SHL G
        sta     VARG
        jsr     K_SPRHITS		; A = the groups, bits 0 to 3
        and     VARG
        beq     @float
        lda     #$FF
@float:
        tay
        jmp     GIVAYF

; EVALUATES A VIDEO ADDRESS, 0 TO $1FFFF, INTO VADR AND VBANK.
VGETV:
        jsr     FRMNUM
        jsr     GETVADR		; A = bit 16, Y = bits 0 to 7
        sta     VBANK
        sty     VADR
        lda     LINNUM+1
        sta     VADR+1
        rts

; EVALUATES A RAM ADDRESS, 0 TO 65535, INTO VARG.
VGETR:
        jsr     FRMNUM
        jsr     GETADR		; A = high byte, Y = low byte
        sty     VARG
        sta     VARG+1
        rts

; EVALUATES ",LEN", 0 TO 65535, INTO LINNUM.
VGETLEN:
        jsr     CHKCOM
        jsr     FRMNUM
        jmp     GETADR
