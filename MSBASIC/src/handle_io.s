; Handle-based I/O (CONFIG_HANDLE_IO): the I/O layer of io.s and the OPEN,
; CLOSE and SYS statements, on top of four target primitives that work with
; Unix-style handles:
;
; K_OPEN   Name at HIO_NAME (NUL-terminated), A = mode (0 read, 1 write,
;          2 append). Returns carry clear and the handle in A, or carry set.
; K_CLOSE  X = handle. May change A, X and Y.
; K_READ   X = handle. Returns carry clear and the byte in A, or carry set
;          at end of file. Keeps X and Y.
; K_WRITE  X = handle, A = byte. Keeps A, X and Y.
;
; K_STDIN and K_STDOUT are the console handles. The target converts line
; ends: BASIC uses CR, files and terminals may use LF.
;
; OPEN lf,"name"[,mode] opens a file as logical file lf (1-255).
; Files opened for reading are read one byte ahead, so ST gets bit 6 (end of
; file) with the last byte, as on CBM machines.

HIO_FILES	= 10		; files open at the same time
HIO_NAMEMAX	= 63		; longest file name

.segment "IORAM"
HIO_LF:		.res HIO_FILES	; logical file number, 0 = free entry
HIO_HND:	.res HIO_FILES	; handle
HIO_MODE:	.res HIO_FILES	; 0 read, 1 write, 2 append
HIO_NEXT:	.res HIO_FILES	; read files: next byte
HIO_EOF:	.res HIO_FILES	; read files: $80 after end of file
HIO_IN:		.res 1		; entry of the input file, $FF = console
HIO_OUT:	.res 1		; output handle
HIO_ENT:	.res 1		; temporaries
HIO_XSAVE:	.res 1
HIO_XSAVE2:	.res 1
HIO_NEWLF:	.res 1
HIO_NEWMODE:	.res 1
HIO_NAME:	.res HIO_NAMEMAX+1

.segment "EXTRA"

MONCOUT		:= IO_CHROUT
MONRDKEY	:= IO_CHRIN	; GET reads from the current input too

; ----------------------------------------------------------------------------
; Cold start: no files open, console input and output. Keeps A and X.
; ----------------------------------------------------------------------------
HIO_INIT:
        pha
        txa
        pha
        lda     #0
        ldx     #HIO_FILES-1
@loop:
        sta     HIO_LF,x
        dex
        bpl     @loop
        jsr     IO_CLRCH
        pla
        tax
        pla
        rts

; ----------------------------------------------------------------------------
; Find the entry of logical file A (A = 0 finds a free entry).
; Returns the entry in X with N clear, or X = $FF with N set. Keeps Y.
; ----------------------------------------------------------------------------
HIO_FIND:
        ldx     #HIO_FILES-1
@loop:
        cmp     HIO_LF,x
        beq     @done
        dex
        bpl     @loop
@done:
        rts

; ----------------------------------------------------------------------------
; Read the next byte of entry X into HIO_NEXT and set ST. Keeps X.
; ----------------------------------------------------------------------------
HIO_AHEAD:
        stx     HIO_ENT
        lda     HIO_HND,x
        tax
        jsr     K_READ
        ldx     HIO_ENT
        bcs     @eof
        sta     HIO_NEXT,x
        lda     #$00
        sta     Z96
        rts
@eof:
        lda     #$80
        sta     HIO_EOF,x
        lda     #$40		; end of file
        sta     Z96
        rts

; ----------------------------------------------------------------------------
; Close entry X and free it. Keeps X.
; ----------------------------------------------------------------------------
HIO_FREE:
        stx     HIO_ENT
        lda     HIO_HND,x
        tax
        jsr     K_CLOSE
        ldx     HIO_ENT
        lda     #0
        sta     HIO_LF,x
        rts

; ----------------------------------------------------------------------------
; I/O errors (and the block errors of block.s). The main error table is full
; (its offsets are 8 bits), so these messages have their own table;
; HIO_ERROR prints like ERROR does. File messages (offsets below
; HIO_ERR_NOFILE) get the shared prefix "?FILE ", the others carry their own "?".
; ----------------------------------------------------------------------------
HIO_NOTOPEN:
        ldx     #HIO_ERR_NOTOPEN
        .byte   $2C
HIO_BADMODE:
        ldx     #HIO_ERR_MODE

HIO_ERROR:
        lsr     Z14
        lda     CURDVC
        beq     @msg
        jsr     IO_CLRCH
        lda     #$00
        sta     CURDVC
@msg:
        jsr     CRDO
        cpx     #HIO_ERR_NOFILE
        bcs     @msg2
        ldy     #HIO_ERR_FILE
        jsr     HIO_PUTS
@msg2:
        txa
        tay
        jsr     HIO_PUTS
        jmp     ERROR_PRINTED

; Print message Y of HIO_ERRORS (OUTDO keeps X and Y).
HIO_PUTS:
        lda     HIO_ERRORS,y
        pha
        and     #$7F
        jsr     OUTDO
        iny
        pla
        bpl     HIO_PUTS
        rts

; ----------------------------------------------------------------------------
; The I/O layer (see io.s)
; ----------------------------------------------------------------------------
IO_CHKIN:
        stx     HIO_XSAVE
        txa
        beq     HIO_NOTOPEN
        jsr     HIO_FIND
        bmi     HIO_NOTOPEN
        lda     HIO_MODE,x
        bne     HIO_BADMODE	; not an input file
        stx     HIO_IN
        ldx     HIO_XSAVE
        rts

IO_CHKOUT:
        stx     HIO_XSAVE
        txa
        beq     HIO_NOTOPEN
        jsr     HIO_FIND
        bmi     HIO_NOTOPEN
        lda     HIO_MODE,x
        beq     HIO_BADMODE	; not an output file
        lda     HIO_HND,x
        sta     HIO_OUT
        ldx     HIO_XSAVE
        rts

IO_CLRCH:
        lda     #$FF
        sta     HIO_IN
        lda     #K_STDOUT
        sta     HIO_OUT
        rts

; Keeps X and Y. After end of file it returns CR: the first time with
; ST = $40 (ends a last line that has no line end), then with ST = $42, so
; INPUT# stops instead of waiting for a line that never comes.
IO_CHRIN:
        stx     HIO_XSAVE
        ldx     HIO_IN
        bpl     @file
        ldx     #K_STDIN
        jsr     K_READ
        ldx     HIO_XSAVE
        rts
@file:
        lda     HIO_EOF,x
        bmi     @eof
        lda     HIO_NEXT,x
        pha
        jsr     HIO_AHEAD
        pla
        ldx     HIO_XSAVE
        rts
@eof:
        lda     HIO_EOF,x
        cmp     #$C0
        lda     #$42		; again: read error, INPUT# stops
        bcs     @status
        lda     #$C0
        sta     HIO_EOF,x
        lda     #$40		; first time: the CR ends a last line
@status:				; that has no line end
        sta     Z96
        lda     #CR
        ldx     HIO_XSAVE
        rts

; Keeps A, X and Y.
IO_CHROUT:
        stx     HIO_XSAVE2
        ldx     HIO_OUT
        jsr     K_WRITE
        ldx     HIO_XSAVE2
        rts

IO_CLALL:
        ldx     #HIO_FILES-1
@loop:
        lda     HIO_LF,x
        beq     @next
        jsr     HIO_FREE
@next:
        dex
        bpl     @loop
        jmp     IO_CLRCH

; ----------------------------------------------------------------------------
; "OPEN" STATEMENT: OPEN lf,"name"[,mode]
; ----------------------------------------------------------------------------
OPEN:
        jsr     GETBYT
        txa
        beq     @iq
        sta     HIO_NEWLF
        jsr     HIO_FIND
        bpl     @isopen
        lda     #0
        jsr     HIO_FIND
        bmi     @toomany
        jsr     CHKCOM
        jsr     FRMEVL
        jsr     FRESTR		; A = length, INDEX = text
        cmp     #HIO_NAMEMAX+1
        bcs     @long
        tay
        lda     #0
        sta     HIO_NAME,y
        beq     @next		; always
@copy:
        lda     (INDEX),y
        sta     HIO_NAME,y
@next:
        dey
        bpl     @copy
        lda     #0
        sta     HIO_NEWMODE
        jsr     CHRGOT
        beq     @open
        jsr     CHKCOM
        jsr     GETBYT
        cpx     #3
        bcs     @iq
        stx     HIO_NEWMODE
@open:
        lda     HIO_NEWMODE
        jsr     K_OPEN
        bcs     @notfound
        pha
        lda     #0
        jsr     HIO_FIND	; the free entry found above
        pla
        sta     HIO_HND,x
        lda     HIO_NEWLF
        sta     HIO_LF,x
        lda     #0
        sta     HIO_EOF,x
        lda     HIO_NEWMODE
        sta     HIO_MODE,x
        bne     @done
        jmp     HIO_AHEAD	; read file: fetch the first byte
@done:
        rts
@iq:
        jmp     IQERR
@long:
        ldx     #ERR_STRLONG
        jmp     ERROR
@isopen:
        ldx     #HIO_ERR_OPEN
        .byte   $2C
@toomany:
        ldx     #HIO_ERR_TOOMANY
        .byte   $2C
@notfound:
        ldx     #HIO_ERR_NOTFOUND
        jmp     HIO_ERROR

; ----------------------------------------------------------------------------
; "CLOSE" STATEMENT: CLOSE lf. A file that is not open is ignored, as on CBM.
; If the file is the current input or output, the console takes over.
; ----------------------------------------------------------------------------
CLOSE:
        jsr     GETBYT
        txa
        beq     @done
        jsr     HIO_FIND
        bmi     @done
        cpx     HIO_IN
        beq     @console
        lda     HIO_HND,x
        cmp     HIO_OUT
        bne     @free
@console:
        jsr     IO_CLRCH
        lda     #$00
        sta     CURDVC
@free:
        jmp     HIO_FREE
@done:
        rts

; ----------------------------------------------------------------------------
; "SYS" STATEMENT: SYS address calls machine code; RTS returns to BASIC.
; ----------------------------------------------------------------------------
SYS:
        jsr     FRMNUM
        jsr     GETADR
        jmp     (LINNUM)

HIO_ERRORS:
HIO_ERR_OPEN = *-HIO_ERRORS
        htasc   "OPEN"
HIO_ERR_NOTOPEN = *-HIO_ERRORS
        htasc   "NOT OPEN"
HIO_ERR_NOTFOUND = *-HIO_ERRORS
        htasc   "NOT FOUND"
HIO_ERR_MODE = *-HIO_ERRORS
        htasc   "MODE"
HIO_ERR_TOOMANY = *-HIO_ERRORS
        htasc   "LIMIT"		; no free file entry
HIO_ERR_NOFILE = *-HIO_ERRORS
HIO_ERR_FILE = *-HIO_ERRORS
        htasc   "?FILE "
.ifdef CONFIG_BLOCK
HIO_ERR_BLOCK = *-HIO_ERRORS
        htasc   "?UNMATCHED BLOCK"
.endif
