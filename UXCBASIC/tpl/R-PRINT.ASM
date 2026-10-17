; R-PRINT.ASM -- the runtime routines for PRINT.

; Print the string at A/Y: [max][len][data]. On UXDOS16, one write to the output handle.
R_PRSTR .block
        #tpl
        sta ZP_PTR
        sty ZP_PTR+1
        ldy #1
        lda (ZP_PTR),y
        beq done
        .if UXDOS != 0
        sta API_R1              ; the count
        stz API_R1+1
        clc                     ; the text
        lda ZP_PTR
        adc #2
        sta API_R0
        lda ZP_PTR+1
        adc #0
        sta API_R0+1
        phx
        #rec ldx, S_CHROUT, S_CHROUT.out - S_CHROUT.rec_code
        jsr API_WRITE
        plx
        rts
        .endif
        sta ZP_TMP              ; the length
        inc ZP_PTR              ; (ZP_PTR),y with y = 1 is the first character
        bne loop
        inc ZP_PTR+1
loop    lda (ZP_PTR),y
        #rec jsr, S_CHROUT      ; CHROUT keeps Y
        cpy ZP_TMP
        iny
        bcc loop
done    rts
        #endtpl
        .endblock

; Print the WORD in A/Y in decimal, as MS BASIC does: a space for the sign, the digits with
; no leading zeros, then a space. PRINT 1; 2 prints " 1  2 ".
R_PRWORD .block
        #tpl
        phx
        sta ZP_TMP
        sty ZP_TMP+1
        lda #" "                ; the sign
sign    #rec jsr, S_CHROUT      ; R_PRSWORD comes in here, with X pushed
        stz ZP_PTR              ; not 0 once a digit is printed
        ldx #0
digit   ldy #"0"
sub     lda ZP_TMP              ; count how many times the power of ten goes
        sec
        #selfx sbc, tens_lo
        pha
        lda ZP_TMP+1
        #selfx sbc, tens_hi
        bcc out
        sta ZP_TMP+1
        pla
        sta ZP_TMP
        iny
        bra sub
out     pla
        tya
        cmp #"0"
        bne show
        ldy ZP_PTR
        beq next                ; a leading zero
show    sta ZP_PTR
        #rec jsr, S_CHROUT
next    inx
        cpx #4
        bne digit
        lda ZP_TMP              ; the ones, always printed
        ora #"0"
        #rec jsr, S_CHROUT
        lda #" "
        plx
        #rec jmp, S_CHROUT
tens_lo .byte <10000, <1000, <100, <10
tens_hi .byte >10000, >1000, >100, >10
        #endtpl
        .endblock

; End the line: CR, and LF after it on UXDOS16.
R_PRNL  .block
        #tpl
        lda #13
        .if UXDOS != 0
        #rec jsr, S_CHROUT
        lda #10
        .endif
        #rec jmp, S_CHROUT
        #endtpl
        .endblock

; Move to the next 14-column print zone, as MS BASIC does on an 80-column screen: the zones
; start at columns 0, 14, 28, 42 and 56. From column 56 on, end the line instead.
R_PRCOMMA .block
        #tpl
        phx
        sec
        #rec jsr, S_PLOT        ; Y = the cursor column
        cpy #56
        bcs newline
        tya
mod     sec                     ; A = the column mod 14, minus 14
        sbc #14
        bcs mod
        eor #$ff                ; = the spaces to print, minus 1
        tax
space   lda #" "
        #rec jsr, S_CHROUT      ; CHROUT keeps X
        dex
        bpl space
        plx
        rts
newline plx
        lda #13
        #rec jmp, S_CHROUT
        #endtpl
        .endblock

; Move the cursor to the column in A, on the same row.
R_POSSETCOL .block
        #tpl
        phx
        pha
        sec
        #rec jsr, S_PLOT        ; X = the row
        ply
        clc
        #rec jsr, S_PLOT
        plx
        rts
        #endtpl
        .endblock

; Move the cursor to the row in A, in the same column.
R_POSSETROW .block
        #tpl
        phx
        pha
        sec
        #rec jsr, S_PLOT        ; Y = the column
        plx
        clc
        #rec jsr, S_PLOT
        plx
        rts
        #endtpl
        .endblock

; Print the signed WORD in A/Y: a - and the digits for a negative one, else as R_PRWORD.
R_PRSWORD .block
        #tpl
        cpy #$80
        bcs minus
        #rec jmp, R_PRWORD
minus   phx
        eor #$ff                ; C is set, so this is 0 - A/Y
        adc #0
        sta ZP_TMP
        tya
        eor #$ff
        adc #0
        sta ZP_TMP+1
        lda #"-"
        #rec jmp, R_PRWORD, R_PRWORD.sign - R_PRWORD.rec_code
        #endtpl
        .endblock

; Print the LONG in A/Y/ZP_HI in decimal, as R_PRWORD prints a WORD.
R_PRLONG .block
        #tpl
        pha
        #self lda, buffer_at
        sta ZP_DST
        #self lda, buffer_at+1
        sta ZP_DST+1
        pla
        #rec jsr, R_LSTR
print   #self lda, buffer_at    ; R_PRSLONG comes in here
        #self ldy, buffer_at+1
        #rec jsr, R_PRSTR
        lda #" "
        #rec jmp, S_CHROUT
buffer_at #selfdw buffer
buffer  .fill 13                ; [max][len], a sign and 10 digits
        #endtpl
        .endblock

; Print the signed LONG in A/Y/ZP_HI: a - and the digits for a negative one, else as
; R_PRLONG.
R_PRSLONG .block
        #tpl
        pha
        #rec lda, R_PRLONG, R_PRLONG.buffer_at - R_PRLONG.rec_code
        sta ZP_DST
        #rec lda, R_PRLONG, R_PRLONG.buffer_at + 1 - R_PRLONG.rec_code
        sta ZP_DST+1
        pla
        #rec jsr, R_SLSTR
        #rec jmp, R_PRLONG, R_PRLONG.print - R_PRLONG.rec_code
        #endtpl
        .endblock
