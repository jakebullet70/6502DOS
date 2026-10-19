; Block IF / ELSE / END IF and DO / LOOP / EXIT (CONFIG_BLOCK).
;
; IF c THEN with nothing after THEN on the line starts a block. A false
; condition skips to the matching ELSE or END IF. ELSE, reached after the
; true part, skips to the matching END IF. END IF itself does nothing (END
; followed by IF, see END in flow1.s). Statements after ELSE on the same
; line run, so ELSE IF c THEN chains blocks; each block needs its own END IF.
; Blocks push nothing on the stack.
;
; The scan works on the tokenized text: a line whose last token (spaces
; skipped) is THEN opens a block, END followed by IF closes one. Text in
; quotes and after REM is skipped.
;
; DO pushes a 5-byte frame like GOSUB (token, line number, text pointer).
; LOOP goes back to the statement after DO; EXIT [DO] leaves the loop and
; goes on after the matching LOOP. FOR frames above the DO frame are dropped.
; RETURN inside a DO loop gives RETURN WITHOUT GOSUB, and GOTO out of a DO
; loop leaves its frame on the stack.
;
; CONTINUE starts the next pass of the innermost loop. In a DO loop it works
; like LOOP. In a FOR loop it scans for the matching NEXT (FOR and NEXT are
; counted like DO and LOOP) and runs it. The variable after NEXT is not
; checked, so NEXT I,J counts as one NEXT.

.segment "EXTRA"

; ----------------------------------------------------------------------------
; "CONTINUE" STATEMENT: next pass of the innermost FOR or DO loop
; ----------------------------------------------------------------------------
CONTINUE:
        lda     #0
        sta     BLK_MODE
        beq     BLK_FORPNT	; always; A = 0 matches the first FOR frame

; ----------------------------------------------------------------------------
; "EXIT" STATEMENT: EXIT [DO]. Drop the DO frame, go on after the matching LOOP
; ----------------------------------------------------------------------------
BLK_EXIT:
        cmp     #TOKEN_DO	; EXIT DO: the DO is ignored
        bne     @mode
        jsr     CHRGET
@mode:
        lda     #TOKEN_LOOP
        .byte   $2C

; ----------------------------------------------------------------------------
; "LOOP" STATEMENT: go back to the statement after DO
; ----------------------------------------------------------------------------
LOOP:
        lda     #0
        sta     BLK_MODE
        lda     #$FF		; match no FOR frame
BLK_FORPNT:
        sta     FORPNT+1
        jsr     GTFORPNT
        beq     BLK_CONTF	; only CONTINUE (A = 0) finds a FOR frame
        cmp     #TOKEN_DO
        bne     BLK_NODO
        txs			; drop the FOR frames above the DO frame
        lda     BLK_MODE
        beq     @loop
        txa			; EXIT: drop the DO frame too
        adc     #4		; carry is set: +5
        tax
        txs
        bcc     BLK_SCAN	; always (the frame ends at $1FF or below)
@loop:
        pla			; pop the frame, DO pushes it again
        pla
        sta     CURLIN
        pla
        sta     CURLIN+1
        pla
        sta     TXTPTR
        pla
        sta     TXTPTR+1

; ----------------------------------------------------------------------------
; "DO" STATEMENT
; ----------------------------------------------------------------------------
DO:
        lda     #$03
        jsr     CHKMEM
        lda     TXTPTR+1
        pha
        lda     TXTPTR
        pha
        lda     CURLIN+1
        pha
        lda     CURLIN
        pha
        lda     #TOKEN_DO
        pha
        jmp     NEWSTT

; ----------------------------------------------------------------------------
; "ELSE" STATEMENT: skip to the matching END IF
; ----------------------------------------------------------------------------
ELSE:
        lda     #0		; stop at END IF only
        .byte   $2C
BLK_CONTF:				; CONTINUE in a FOR loop: scan for NEXT
        lda     #TOKEN_NEXT
        .byte   $2C

; ----------------------------------------------------------------------------
; False block IF (from IF in flow2.s): skip to the matching ELSE or END IF
; ----------------------------------------------------------------------------
BLK_FALSE:
        lda     #TOKEN_ELSE	; stop at ELSE too
        sta     BLK_MODE
BLK_SCAN:				; BLK_MODE set: TOKEN_LOOP or TOKEN_NEXT
        ldy     #0
        sty     BLK_DEPTH
        sty     BLK_LAST
@loop:
        lda     (TXTPTR),y
        beq     @eol
        cmp     #'"'
        bne     @noquote
@quote:
        iny
        lda     (TXTPTR),y
        beq     @eol
        cmp     #'"'
        bne     @quote
@noquote:
        cmp     #TOKEN_REM
        beq     @rem
        cmp     #' '
        beq     @next
        ldx     BLK_MODE
        cpx     #TOKEN_LOOP
        beq     @exit
        cpx     #TOKEN_NEXT
        beq     @exit
        cmp     BLK_MODE
        beq     @else
        cmp     #TOKEN_IF
        bne     @last
        ldx     BLK_LAST
        cpx     #TOKEN_END
        bne     @last
@close:
        ldx     BLK_DEPTH	; END IF or LOOP
        beq     @found
        dec     BLK_DEPTH
@last:
        sta     BLK_LAST
@next:
        iny
        bne     @loop		; always (a line is shorter than 256 bytes)
:       ldx     #HIO_ERR_BLOCK	; BLK_NODO
        jmp     HIO_ERROR
@else:
        ldx     BLK_DEPTH
        bne     @last
@found:
        cmp     #TOKEN_NEXT	; A = ELSE, IF, LOOP or NEXT
        beq     @run		; NEXT: run it
        iny			; others: run what follows them
@run:
        jsr     ADDON
        jmp     L288D		; run the rest of the line
@rem:
        sta     BLK_LAST	; IF c THEN REM is a one-line IF
@remloop:
        iny
        lda     (TXTPTR),y
        bne     @remloop
@eol:
        lda     BLK_LAST
        cmp     #TOKEN_THEN
        bne     @line
        inc     BLK_DEPTH	; IF c THEN at the end of a line
@line:
        jsr     ADDON		; TXTPTR at the end of the line
        ldy     #2
        lda     (TXTPTR),y
        beq     BLK_NODO	; end of the program
        iny
        lda     (TXTPTR),y
        sta     CURLIN
        iny
        lda     (TXTPTR),y
        sta     CURLIN+1
        lda     #0
        sta     BLK_LAST
        iny
        bne     @loop		; always
@exit:					; BLK_MODE closes a loop, the token before it opens one
        cmp     BLK_MODE	; (DO LOOP, FOR NEXT)
        beq     @close
        cmp     #TOKEN_EXIT
        beq     @last
        adc     #1		; carry clear if below EXIT (DO, FOR): +1
        cmp     BLK_MODE
        bne     @next		; LAST stays EXIT, LOOP or NEXT, never THEN
        ldx     BLK_LAST
        cpx     #TOKEN_EXIT
        beq     @next		; EXIT DO
        inc     BLK_DEPTH
        bne     @next		; always

; The error exit in the middle of the scan has no name, because a named label
; there would end the scope of its @ labels.
BLK_NODO = :-
