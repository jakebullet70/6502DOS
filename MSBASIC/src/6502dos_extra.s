; I/O for the 6502DOS target through the 6502DOS API (docs/API.md): the
; handle primitives of handle_io.s, PAUSE's jiffy, VERA, the screen calls of
; TEXTAT and COLOR, and bank 2's IRQ entry. A call changes A, X, Y, the flags
; and its out registers; BASIC keeps nothing in r0 to r15.

.segment "IORAM"

DOS_STACK:	.res 1		; S at the cold start; STKINI goes back to it
DOS_BYTE:	.res 1		; the byte of K_READ and K_WRITE; temporary
DOS_X:		.res 1		; X in K_READ and K_WRITE; the handle in K_OPEN
DOS_Y:		.res 1		; Y in K_READ and K_WRITE
DOS_MODE:	.res 1		; K_OPEN: the mode
DOS_POLL:	.res 1		; ISCNTC looks for Ctrl+C when this counts to 0
DOS_ROW:	.res 1		; TEXTAT: the cursor and the color to restore
DOS_COLUMN:	.res 1
DOS_COLOR:	.res 1		; COLOR: the background
DOS_LOADRUN:	.res 1		; logical file 0 ends with OK if $FF, else with RUN
DOS_FILE	:= DOS_ROW	; LOAD and SAVE: the handle
DOS_BUFMAX	= 64		; K_READ: bytes a read call
DOS_BUFHND:	.res 1		; K_READ: the handle whose bytes DOS_BUF holds
DOS_BUFPOS:	.res 1		; K_READ: the next byte in DOS_BUF
DOS_BUFLEN:	.res 1		; K_READ: the bytes in DOS_BUF
DOS_BUF:	.res DOS_BUFMAX
		.res FIND_BUFFER_SIZE-DOS_BUFMAX ; FILES: the find buffer goes on past DOS_BUF
FILES_COUNT:	.res 4		; FILES: the names listed

.segment "EXTRA"

; Sets r0 to DOS_BYTE and r1 to 1, a read or write of one byte. Keeps X and Y.
DOS_FRAME:
        lda     #<DOS_BYTE
        sta     r0
        lda     #>DOS_BYTE
        sta     r0+1
        lda     #1
        sta     r1
        stz     r1+1
        rts

; X = handle. Returns carry clear and the byte in A, or carry set at the end
; of the file or on an error. Keeps X and Y. LF is dropped: a file ends its
; lines with CR LF, BASIC with CR. A file is read DOS_BUFMAX bytes a call
; into DOS_BUF, which holds the bytes of one handle at a time. A read of
; another handle seeks the holder back by the bytes not yet taken. The
; console, K_STDIN, is read a byte a call.
K_READ:
        stx     DOS_X
        sty     DOS_Y
@again:
        ldx     DOS_X
        bne     @file			; K_STDIN is 0
        jsr     DOS_FRAME
        jsr     API_READ
        bcs     @done
        lda     r1
        beq     @eof
        lda     DOS_BYTE
@byte:
        cmp     #LF
        beq     @again
        clc
        bra     @done
@file:
        cpx     DOS_BUFHND
        beq     @take
        jsr     DOS_GIVEBACK		; empty: @take reads
        ldx     DOS_X
        stx     DOS_BUFHND
@take:
        ldy     DOS_BUFPOS
        cpy     DOS_BUFLEN
        bcs     @fill
        inc     DOS_BUFPOS
        lda     DOS_BUF,y
        bra     @byte
@fill:
        lda     #<DOS_BUF
        sta     r0
        lda     #>DOS_BUF
        sta     r0+1
        lda     #DOS_BUFMAX
        sta     r1
        stz     r1+1
        jsr     API_READ		; X = handle
        stz     DOS_BUFPOS
        lda     #0
        bcs     @fail			; an error ends the file
        lda     r1
@fail:
        sta     DOS_BUFLEN
        bne     @take
@eof:
        sec
@done:
        ldx     DOS_X
        ldy     DOS_Y
        rts

; Seeks the file whose bytes DOS_BUF holds back by the bytes not yet taken,
; and empties DOS_BUF, so that other code may use it. Changes A, X and Y.
DOS_GIVEBACK:
        lda     DOS_BUFPOS
        sec
        sbc     DOS_BUFLEN		; minus the bytes not taken, 0 to -64
        beq     @empty
        sta     r0
        lda     #$FF
        sta     r0+1
        sta     r1
        sta     r1+1
        ldx     DOS_BUFHND
        lda     #1			; from the position
        jsr     API_SEEK
        lda     DOS_BUFPOS
        sta     DOS_BUFLEN		; empty: POS = LEN
@empty:
        rts

; X = handle, A = byte. Keeps A, X and Y; N and Z come from A.
K_WRITE:
        sta     DOS_BYTE
        stx     DOS_X
        sty     DOS_Y
        jsr     DOS_FRAME
        jsr     API_WRITE
        ldx     DOS_X
        ldy     DOS_Y
        lda     DOS_BYTE
        rts

; Sets r0 to HIO_NAMELEN, the length-prefixed name. Keeps A and Y.
DOS_R0NAME:
        ldx     #<HIO_NAMELEN
        stx     r0
        ldx     #>HIO_NAMELEN
        stx     r0+1
        rts

; Name at HIO_NAMELEN, length-prefixed; A = mode: 0 read, 1 write, 2 append.
; Returns carry clear and the handle in A, or carry set. Write makes the file
; or empties it. Append opens the file for writing at its end, and makes it
; when it is missing.
K_OPEN:
        sta     DOS_MODE
        jsr     DOS_R0NAME
        cmp     #1
        beq     @create
        lsr     a			; 0: access 0, read; 2: access 1, write
        jsr     API_OPEN
        bcc     @opened
        cmp     #ERR_NOT_FOUND
        bne     @fail
        lda     DOS_MODE
        beq     @fail			; read
@create:
        lda     #0			; no attributes
        jsr     API_CREATE
        bcs     @fail
@opened:
        stx     DOS_X
        cpx     DOS_BUFHND		; the handle of a closed file: DOS_BUF
        bne     @new			; holds that file's bytes
        stz     DOS_BUFLEN
        stz     DOS_BUFPOS
@new:
        lda     DOS_MODE
        cmp     #2
        bne     @done
        stz     r0			; append: 0 from the end
        stz     r0+1
        stz     r1
        stz     r1+1
        jsr     API_SEEK		; A = 2, X = handle
@done:
        lda     DOS_X
        clc
        rts
@fail:
        sec
        rts

; X = handle. Changes A, X and Y.
K_CLOSE		:= API_CLOSE

.ifdef CONFIG_PAUSE
; Waits for the next VSYNC, one jiffy, and makes the next ISCNTC look for
; Ctrl+C. Changes A, X and Y.
K_JIFFY:
        jsr     API_TICKS
        lda     r0
        pha				; the low byte of ticks
@wait:
        jsr     API_TICKS
        pla
        pha
        cmp     r0
        beq     @wait
        pla
        lda     #1
        sta     DOS_POLL
        rts
.endif

.ifdef CONFIG_VERA
; K_VPEEK: A = bank, LINNUM = address; returns the byte in A.
K_VPEEK:
        jsr     DOS_VADDR
        lda     VERA_DATA0
        rts

; K_VPOKE: A = bank, LINNUM = address, X = byte.
K_VPOKE:
        jsr     DOS_VADDR
        stx     VERA_DATA0
; K_SCREEN: X = mode. Does nothing: the console keeps its 80x30 text mode.
K_SCREEN:
        rts

; Points VERA's address 0 at bank A, bit 0 only, and LINNUM, with no
; increment. Keeps X.
DOS_VADDR:
        and     #$01
        stz     VERA_CTRL		; ADDRSEL 0
        sta     VERA_ADDR_H
        lda     LINNUM
        sta     VERA_ADDR_L
        lda     LINNUM+1
        sta     VERA_ADDR_M
        rts
.endif

.ifdef CONFIG_TEXTAT
; TEXTAT: keeps the cursor and the color for TA_RESTORE.
TA_KEEP:
        sec
        jsr     API_CON_CURSOR		; X = row, Y = column
        stx     DOS_ROW
        sty     DOS_COLUMN
        sec
        jsr     API_CON_COLOUR
        sta     DOS_COLOR
        rts

; TEXTAT and COLOR: sets the color to DOS_COLOR's background and X's
; foreground.
TA_INK:
        txa
        eor     DOS_COLOR
        and     #$0F
        eor     DOS_COLOR		; DOS_COLOR's high bits, X's low bits
        bra     DOS_SETCOLOR

; TEXTAT: puts the cursor and the color back.
TA_RESTORE:
        ldx     DOS_ROW
        ldy     DOS_COLUMN
        clc
        jsr     API_CON_CURSOR
        lda     DOS_COLOR
DOS_SETCOLOR:
        clc
        jmp     API_CON_COLOUR
.endif

.ifdef CONFIG_SCREEN
; ----------------------------------------------------------------------------
; "COLOR" STATEMENT: COLOR FG[,BG], 0-15 EACH, FROM VERA'S PALETTE. THE
; BACKGROUND STAYS WHEN IT IS LEFT OUT.
; ----------------------------------------------------------------------------
COLOR:
        jsr     GETBYT			; X = foreground
        phx
        sec
        jsr     API_CON_COLOUR
        sta     DOS_COLOR
        jsr     CHRGOT
        beq     @set
        jsr     COMBYTE			; X = background
        txa
        asl     a
        asl     a
        asl     a
        asl     a
        sta     DOS_COLOR
@set:
        plx
        jmp     TA_INK
.endif

.ifdef CONFIG_QUIT
; ----------------------------------------------------------------------------
; "QUIT" STATEMENT: QUIT [N]. ENDS BASIC AND RETURNS TO THE PROGRAM THAT RAN
; MSBASIC.COM, WITH THE EXIT CODE N, 0-255, OR 0. exit closes BASIC's files.
; ----------------------------------------------------------------------------
QUIT:
        beq     @zero			; no N
        jsr     GETBYT			; X = N
        .byte   $2C			; skip the ldx
@zero:
        ldx     #0
        txa
        jmp     API_EXIT		; returns only with no parent, to NEWSTT
.endif

.ifdef CONFIG_HELP
; ----------------------------------------------------------------------------
; "HELP" STATEMENT: HELP [TOPIC], DIRECT MODE ONLY; ?SYNTAX ERROR IN A
; PROGRAM. PRINTS THE TOPIC'S TEXT FROM C:\DOS\HELPBAS.HLP, OR WITH NO TOPIC
; THE TOPIC NAMES, A NEW LINE BEFORE A NAME THAT WOULD PASS COLUMN 79.
; THE FILE IS HELP.TXT'S FORMAT: A LINE :NAME STARTS THE TOPIC NAME, CR LF
; LINE ENDS. A TOKEN IN THE TOPIC IS SPELLED OUT AND "(" IS DROPPED, SO
; HELP PRINT AND HELP TAB( FIND PRINT AND TAB.
; ----------------------------------------------------------------------------
; Trap: the topic and the name buffers share HIO_NAME with the path, which
; K_OPEN needs only while it opens.
HELP_TOPIC	:= HIO_NAME+20		; the topic, CR at its end
HELP_NAME	:= HIO_NAME+40		; a :NAME line, CR at its end
HELP_MAX	= 19			; longest topic and name
.assert HELP_NAME+HELP_MAX < HIO_NAME+HIO_NAMEMAX+1, error, "HELP's buffers pass HIO_NAME"
HELP_HND	:= DOS_ROW		; TEXTAT's bytes, free while HELP runs
HELP_FOUND	:= DOS_COLUMN		; the topic's length, 0 for the list;
					; bit 7 after the topic's :NAME line
HELP:
        ldx     CURLIN+1
        inx
        jne     SYNERR			; CURLIN+1 is $FF in direct mode
        ldx     #0
        jsr     CHRGOT
@topic:
        beq     @topic_end		; 0 or ":"
        cmp     #$80
        bcs     @token
        cmp     #'('
        beq     @topic_next
        jsr     HELP_PUT
        bra     @topic_next
@token:
        sbc     #$7F			; carry is set: 1 is the first keyword
        sta     HELP_HND		; keyword count
        jsr     KW_INIT			; KW_INIT and KW_NEXT keep X
@find:
        dec     HELP_HND
        beq     @letter
        jsr     KW_NEXT
        bra     @find
@letter:
        lda     (KW_PTR),y
        pha
        and     #$7F
        cmp     #'('
        beq     @skip
        jsr     HELP_PUT
@skip:
        iny
        pla
        bpl     @letter
@topic_next:
        jsr     CHRGET
        bra     @topic
@topic_end:
        lda     #CR
        sta     HELP_TOPIC,x
        stx     HELP_FOUND
        ldx     #HELP_PATH_END-HELP_PATH-1
@path:
        lda     HELP_PATH,x
        sta     HIO_NAMELEN,x
        dex
        bpl     @path
        lda     #0			; read
        jsr     K_OPEN
        bcc     @opened
        ldx     #HIO_ERR_NOTFOUND
        jmp     HIO_ERROR
@opened:
        sta     HELP_HND
@line:
        jsr     HELP_READ
        cmp     #':'
        beq     @name
@text:
        cmp     #CR
        beq     @text_end
        bit     HELP_FOUND
        bpl     @text_next
        jsr     OUTDO
@text_next:
        jsr     HELP_READ
        bra     @text
@text_end:
        bit     HELP_FOUND
        bpl     @line
        jsr     CRDO
        bra     @line
@name:
        bit     HELP_FOUND
        bmi     HELP_CLOSE		; the next topic ends the text
        ldy     #0			; HELP_READ keeps Y
@name_letter:
        jsr     HELP_READ
        sta     HELP_NAME,y
        cmp     #CR
        beq     @name_end
        cpy     #HELP_MAX
        bcs     @name_letter
        iny
        bra     @name_letter
@name_end:
        lda     HELP_FOUND
        beq     @list
        ldx     #$FF
@compare:
        inx
        lda     HELP_NAME,x
        cmp     HELP_TOPIC,x
        bne     @line
        cmp     #CR
        bne     @compare
        ror     HELP_FOUND		; carry is set: bit 7
        bra     @line
@list:
        tya				; Y = the name's length
        clc
        adc     POSX
        cmp     #79
        bcc     @fits
        jsr     CRDO
@fits:
        ldx     #HELP_NAME-HELP_TOPIC
        jsr     HELP_PRINT
        jsr     OUTSP
        bra     @line

; Returns the next byte of the help file in A; keeps Y. At the end of the
; file it drops its caller's return, closes the file and returns from HELP.
HELP_READ:
        ldx     HELP_HND
        jsr     K_READ
        bcc     HELP_RTS
        pla
        pla
HELP_CLOSE:
        ldx     HELP_HND
        jsr     K_CLOSE
        lda     HELP_FOUND
        beq     @list_end
        bmi     HELP_RTS
        lda     #<HELP_NONE
        ldy     #>HELP_NONE
        jsr     STROUT
        ldx     #0
        jsr     HELP_PRINT
@list_end:
        jmp     CRDO

; Prints HELP_TOPIC,X up to the CR.
HELP_PRINT:
        lda     HELP_TOPIC,x
        cmp     #CR
        beq     HELP_RTS
        jsr     OUTDO
        inx
        bra     HELP_PRINT

; Stores A at HELP_TOPIC,X; X counts up to HELP_MAX.
HELP_PUT:
        sta     HELP_TOPIC,x
        cpx     #HELP_MAX
        bcs     HELP_RTS
        inx
HELP_RTS:
        rts

HELP_PATH:
        .byte   HELP_PATH_END-HELP_PATH-1, "C:\DOS\HELPBAS.HLP"
HELP_PATH_END:
HELP_NONE:
        .byte   "NO HELP FOR ",0
.endif

; ----------------------------------------------------------------------------
; The end of the cold start. MSBASIC NAME.BAS loads NAME.BAS, the first word
; of the command tail, as DOS_LOAD does, and runs it. Without a name the OK
; prompt follows.
; ----------------------------------------------------------------------------
DOS_BOOT:
        ldx     #0
        stx     DOS_BUFLEN		; K_READ: DOS_BUF empty
        stx     DOS_BUFPOS
@skip:
        inx
        lda     COMMAND_TAIL,x
        cmp     #' '
        beq     @skip
        ldy     #0
@copy:
        cmp     #' '+1
        bcc     @end			; a space or the CR ends the name
        sta     HIO_NAME,y
        inx
        iny
        lda     COMMAND_TAIL,x
        cpy     #HIO_NAMEMAX
        bcc     @copy
@end:
        sty     HIO_NAMELEN
        tya				; the length, not $FF: RUN
        bne     DOS_LOAD
        jmp     RESTART

; ----------------------------------------------------------------------------
; "LOAD" STATEMENT: LOAD "name" does a NEW, then reads the file's lines as
; typed ones, then gives the OK prompt. In a program, RUN follows instead.
; ----------------------------------------------------------------------------
LOAD:
        jsr     HIO_GETNAME
        lda     CURLIN+1		; $FF in direct mode
; Opens the file named at HIO_NAMELEN as logical file 0, BASIC's input
; (entry 0), and does a NEW. INLIN reads its lines; at the end it gives the
; OK prompt if A was $FF, else the line RUN. A missing file is ?FILE NOT
; FOUND ERROR, and the program stays.
DOS_LOAD:
        sta     DOS_LOADRUN
        lda     #0			; read
        jsr     K_OPEN
        bcs     DOS_NOTFOUND
        sta     DOS_FILE		; NEW resets the stack
        jsr     SCRTCH			; and frees every entry
        lda     DOS_FILE
        sta     HIO_HND
        stz     HIO_MODE
        stz     HIO_EOF
        stz     HIO_IN
        ldx     #0
        jsr     HIO_AHEAD
        jmp     L2351			; no OK before the file's lines
DOS_NOTFOUND:
        ldx     #HIO_ERR_NOTFOUND
        jmp     HIO_ERROR

; ----------------------------------------------------------------------------
; "KILL" STATEMENT: KILL "name" deletes the file. Any failure is ?FILE NOT
; FOUND ERROR. The kernel does not check for open handles: close it first.
; ----------------------------------------------------------------------------
KILL:
        jsr     HIO_GETNAME
        jsr     DOS_R0NAME
        jsr     API_DELETE
        bcs     DOS_NOTFOUND
        rts

; ----------------------------------------------------------------------------
; "NAME" STATEMENT: NAME "old" AS "new" renames a file or a directory, or
; moves a file to another directory of the same drive. A new name that exists
; is ?FILE EXISTS ERROR, any other failure ?FILE NOT FOUND ERROR. AS is two
; letters, not a keyword.
; ----------------------------------------------------------------------------
NAME:
        jsr     HIO_GETNAME		; the old name
        jsr     DOS_GIVEBACK		; DOS_BUF takes the old name
        ldx     HIO_NAMELEN
@copy:
        lda     HIO_NAMELEN,x
        sta     DOS_BUF,x
        dex
        bpl     @copy
        lda     #'A'
        jsr     SYNCHR
        lda     #'S'
        jsr     SYNCHR
        jsr     HIO_GETNAME		; the new name
        lda     #<DOS_BUF
        sta     r0
        lda     #>DOS_BUF
        sta     r0+1
        lda     #<HIO_NAMELEN
        sta     r1
        lda     #>HIO_NAMELEN
        sta     r1+1
        jsr     API_RENAME
        bcc     @done
        cmp     #ERR_ACCESS
        bne     DOS_NOTFOUND
        ldx     #HIO_ERR_EXISTS
        jmp     HIO_ERROR
@done:
        rts
.assert HIO_NAMEMAX < DOS_BUFMAX, error, "NAME's old name does not fit DOS_BUF"

; ----------------------------------------------------------------------------
; "SAVE" STATEMENT: SAVE "name" writes the program to the file as LIST shows
; it, with no space before a line number and CR LF line ends, and makes the
; file or empties it. As LIST, it ends
; a program. RESTART prints OK through GOSTROUT, which SAVE points at
; SAVE_END, so the file closes after the last line or after a Ctrl+C break.
; ----------------------------------------------------------------------------
SAVE:
        jsr     HIO_GETNAME
        lda     #1			; write
        jsr     K_OPEN
        bcs     DOS_NOTFOUND
        sta     HIO_OUT
        sta     DOS_FILE
        lda     #<SAVE_END
        sta     GOSTROUT+1
        lda     #>SAVE_END
        sta     GOSTROUT+2
        lda     TXTTAB
        ldy     TXTTAB+1
        sta     LOWTRX
        sty     LOWTRX+1
        lda     #$FF			; to the last line
        sta     LINNUM
        sta     LINNUM+1
        pla				; LIST ends at RESTART, not NEWSTT
        pla
        ldy     #1
        lda     (LOWTRX),y
        jne     LIST_LINE		; no CRDO before the first line
        jmp     RESTART

; RESTART's GOSTROUT after SAVE: ends the last line, closes the file, gives
; the output back to the console, then prints A/Y as STROUT does.
SAVE_END:
        pha
        phy
        jsr     CRDO
        ldx     DOS_FILE
        jsr     K_CLOSE
        jsr     IO_CLRCH
        lda     #<STROUT
        sta     GOSTROUT+1
        lda     #>STROUT
        sta     GOSTROUT+2
        ply
        pla
        jmp     STROUT

; ----------------------------------------------------------------------------
; "FILES" STATEMENT: FILES ["pattern"] lists the names that match, with
; hidden and system files and directories, each with its size or <DIR> to
; column 23, then their count, as the shell's FILES does. A directory's name
; lists the names in it; no pattern lists the current directory. A pattern
; that matches nothing is ?FILE NOT FOUND ERROR. Ctrl+C stops it.
; ----------------------------------------------------------------------------
FILES_FIND	:= DOS_BUF		; the find buffer, FIND_BUFFER_SIZE bytes
FILES:
        stz     HIO_NAMELEN		; keeps Z: no pattern
        beq     @search
        jsr     HIO_GETNAME
@search:
        jsr     DOS_GIVEBACK		; DOS_BUF takes the find buffer
        ldx     HIO_NAMELEN
        beq     @first			; the current directory
        lda     HIO_NAME-1,x
        cmp     #'\'
        beq     @first			; ends in a separator: lists that directory
        cmp     #'/'
        beq     @first
        cmp     #':'
        beq     @first
@wild:
        lda     HIO_NAME-1,x
        cmp     #'*'
        beq     @first
        cmp     #'?'
        beq     @first
        dex
        bne     @wild
        jsr     FILES_FIRST
        bcs     @first			; the search below gives the error
        lda     FILES_FIND+FIND_ATTR
        and     #ATTR_DIR
        beq     @first
        ldx     HIO_NAMELEN		; a directory: list the names in it
        lda     #'\'
        sta     HIO_NAME,x
        inc     HIO_NAMELEN
@first:
        jsr     FILES_FIRST
        jcs     DOS_NOTFOUND
        ldx     #3
@zero:
        stz     FILES_COUNT,x
        dex
        bpl     @zero
@entry:
        jsr     ISCNTC
        ldx     #0
@name:
        lda     FILES_FIND+FIND_NAME+1,x
        jsr     OUTDO
        inx
        cpx     FILES_FIND+FIND_NAME
        bcc     @name
        lda     FILES_FIND+FIND_ATTR
        and     #ATTR_DIR
        beq     @size
        lda     #<FILES_DIR
        ldy     #>FILES_DIR
        bra     @right
@size:
        ldx     #FIND_SIZE+3
        jsr     FILES_NUMBER
@right:
        ldx     #23
        jsr     FILES_RIGHT
        jsr     CRDO
        inc     FILES_COUNT
        bne     @next
        inc     FILES_COUNT+1
@next:
        jsr     FILES_R1
        jsr     API_FINDNEXT
        bcc     @entry
        cmp     #ERR_NO_MORE_FILES
        jne     DOS_NOTFOUND
        ldx     #FILES_COUNT-FILES_FIND+3
        jsr     FILES_NUMBER
        ldx     #6
        jsr     FILES_RIGHT
        lda     #<FILES_TEXT
        ldy     #>FILES_TEXT
        jsr     STROUT
        jmp     CRDO
.assert FILES_COUNT-FILES_FIND < 253, error, "FILES_NUMBER cannot index FILES_COUNT"

; Starts the search for the pattern at HIO_NAMELEN.
FILES_FIRST:
        jsr     DOS_R0NAME
        jsr     FILES_R1
        lda     #ATTR_DIR | ATTR_HIDDEN | ATTR_SYSTEM
        jmp     API_FINDFIRST

FILES_R1:
        lda     #<FILES_FIND
        sta     r1
        lda     #>FILES_FIND
        sta     r1+1
        rts

; Turns the 4-byte number at FILES_FIND,X down to FILES_FIND,X-3, high byte
; first, into text: A/Y = the text, a space first, as FOUT gives it.
FILES_NUMBER:
        ldy     #1
@byte:
        lda     FILES_FIND,x
        sta     FAC,y
        dex
        iny
        cpy     #5
        bcc     @byte
        ldx     #$A0			; 32 bits
        lda     #0
        jsr     LDB21			; positive
        jmp     FOUT

; Prints the text at A/Y, 0 at its end, so that it ends before column X.
FILES_RIGHT:
        pha
        phy
        sta     INDEX
        sty     INDEX+1
        ldy     #0
@length:
        lda     (INDEX),y
        beq     @pad
        iny
        dex
        bra     @length
@pad:
        cpx     POSX
        beq     @print
        bcc     @print
        jsr     OUTSP			; keeps X
        bra     @pad
@print:
        ply
        pla
        jmp     STROUT

FILES_DIR:
        .byte   " <DIR>",0
FILES_TEXT:
        .byte   " File(s)",0

DOS_RUN:
        .byte   "RUN",0

; ----------------------------------------------------------------------------
; Bank 2's IRQ entry and vectors, as bank1.s has them. An interrupt's vector
; pull selects bank 0, so bank 0 runs the entry; this bank runs only the end
; of FAR_IRQ_EXIT, after the write to ROM_BANK. Trap: these bytes must sit at
; the same address in every bank. Bank 0 runs its own jmp irq, so irq here
; only fills the bytes.
; ----------------------------------------------------------------------------
irq		:= 0

nmi2:
        rti

.segment "FARIRQ2"

irq_entry2:
        FAR_IRQ_ENTRY
        FAR_IRQ_EXIT

.segment "CPUVECTORS"

        .word   nmi2
        .word   nmi2			; reset selects bank 0
        .word   irq_entry2

.segment "EXTRA"			; extra.s goes on in EXTRA
