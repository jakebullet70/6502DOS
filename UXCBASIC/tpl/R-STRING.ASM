; R-STRING.ASM -- the string routines.
;
; A block is [max][len][data], so its character i is at offset 2 + i, which passes 255 in a
; block of max 254 or 255. The copy loops therefore move a pointer to the block + 1 and run Y
; from the length down to 1.

; Copy (C clear) or append (C set) the string at ZP_PTR to the block at A/Y, cut at the block's
; max. A copy of a block onto itself is safe. Keeps X.
R_SCAT  .block
        #tpl
        sta ZP_DST
        sty ZP_DST+1
        lda #0                  ; a copy starts at 0
        bcc +
        ldy #1
        lda (ZP_DST),y          ; an append starts after the text there
+       sta ZP_TMP
        lda (ZP_DST)            ; the room: max - start
        sec
        sbc ZP_TMP
        ldy #1
        cmp (ZP_PTR),y
        bcc +                   ; less room than text: cut
        lda (ZP_PTR),y
+       sta ZP_TMP+1            ; the characters to copy
        clc
        adc ZP_TMP
        sta (ZP_DST),y          ; the new length
        ldy ZP_TMP+1
        beq done
        inc ZP_PTR              ; (ZP_PTR),y with y = 1 is the first source character
        bne +
        inc ZP_PTR+1
+       lda ZP_DST              ; (ZP_DST),y with y = 1 is the first character after start
        sec
        adc ZP_TMP
        sta ZP_DST
        bcc copy
        inc ZP_DST+1
copy    lda (ZP_PTR),y
        sta (ZP_DST),y
        dey
        bne copy
done    rts
        #endtpl
        .endblock

; Compare two strings as CMP does: C = P >= Q, Z = P = Q. The left side is on the expression
; stack and the right side in A/Y. C clear on entry: P is the left side. C set: P is the right
; side. The first character that differs decides; when one string starts with the other, the
; longer one is greater. Pops the left side, keeps X.
R_SCMP  .block
        #tpl
        dex
        dex
        bcc lr
        sta ZP_PTR
        sty ZP_PTR+1
        lda ESTK,x
        sta ZP_DST
        lda ESTK+1,x
        sta ZP_DST+1
        bra lens
lr      sta ZP_DST
        sty ZP_DST+1
        lda ESTK,x
        sta ZP_PTR
        lda ESTK+1,x
        sta ZP_PTR+1
lens    ldy #1
        lda (ZP_PTR),y
        sta ZP_TMP              ; the length of P
        lda (ZP_DST),y
        sta ZP_TMP+1            ; the length of Q
        inc ZP_PTR              ; (ZP_PTR),y with y = 1 is the first character
        bne +
        inc ZP_PTR+1
+       inc ZP_DST
        bne +
        inc ZP_DST+1
+       ldy #0
loop    cpy ZP_TMP
        beq last
        cpy ZP_TMP+1
        beq last
        iny
        lda (ZP_PTR),y
        cmp (ZP_DST),y
        beq loop
        rts
last    lda ZP_TMP
        cmp ZP_TMP+1
        rts
        #endtpl
        .endblock

; The block at A/Y = the WORD in ZP_TMP in decimal, as PRINT shows it but with no space after:
; STR$(5) is " 5". Keeps X.
R_STR   .block
        #tpl
        sta ZP_DST
        sty ZP_DST+1
        phx
        ldy #2
        lda #" "                ; the sign
sign    sta (ZP_DST),y          ; R_SSTR comes in here, with X pushed
        ldx #0
digit   lda #"0"
        sta ZP_PTR+1
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
        inc ZP_PTR+1
        bra sub
out     pla
        lda ZP_PTR+1
        cmp #"0"
        bne show
        cpy #3
        bcc next                ; only the sign is written: a leading zero
show    iny
        sta (ZP_DST),y
next    inx
        cpx #4
        bne digit
        lda ZP_TMP              ; the ones, always written
        ora #"0"
        iny
        sta (ZP_DST),y
        tya                     ; the length: the last offset - 1
        dec a
        ldy #1
        sta (ZP_DST),y
        plx
        rts
tens_lo .byte <10000, <1000, <100, <10
tens_hi .byte >10000, >1000, >100, >10
        #endtpl
        .endblock

; A/Y = the number the string at A/Y starts with, in decimal. Spaces and a + before it are
; skipped. A - right before the digits makes it 0 minus the number: VAL("-5") is 65531. It
; ends at the first character that is not a digit. A number past 65535 wraps. Keeps X.
R_VAL   .block
        #tpl
        sta ZP_PTR
        sty ZP_PTR+1
        phx
        stz ZP_TMP              ; the value
        stz ZP_TMP+1
        ldy #1
        lda (ZP_PTR),y
        tax                     ; the characters left
        inc ZP_PTR              ; (ZP_PTR),y with y = 1 is the first character
        bne +
        inc ZP_PTR+1
+       #self jsr, skip
        plx
        rts
skip    txa
        beq done
        lda (ZP_PTR),y
        iny
        dex
        cmp #" "
        beq skip
        cmp #"+"
        beq skip
        cmp #"-"
        beq minus
digit   sec
        sbc #"0"
        cmp #10
        bcs done                ; not a digit
        pha
        lda ZP_TMP              ; the value x 10: x 4, + the value, x 2
        sta ZP_DST
        lda ZP_TMP+1
        sta ZP_DST+1
        asl ZP_TMP
        rol ZP_TMP+1
        asl ZP_TMP
        rol ZP_TMP+1
        clc
        lda ZP_TMP
        adc ZP_DST
        sta ZP_TMP
        lda ZP_TMP+1
        adc ZP_DST+1
        sta ZP_TMP+1
        asl ZP_TMP
        rol ZP_TMP+1
        pla                     ; + the digit
        clc
        adc ZP_TMP
        sta ZP_TMP
        bcc more
        inc ZP_TMP+1
more    txa
        beq done
        lda (ZP_PTR),y
        iny
        dex
        bra digit
minus   #self jsr, more         ; the digits after the minus, then 0 minus them
        lda #0
        sec
        sbc ZP_TMP
        sta ZP_TMP
        lda #0
        sbc ZP_TMP+1
        sta ZP_TMP+1
done    lda ZP_TMP
        ldy ZP_TMP+1
        rts
        #endtpl
        .endblock

; The temp at A/Y = MID$(string, start, length). The length is the WORD in ZP_TMP. The string
; and the start, a WORD, are on the expression stack. A start of 0 is the same as 1. Pops
; both, keeps X.
; WARNING: the temp must not be the source block. The copy runs from the end down.
R_MID   .block
        #tpl
        sta ZP_DST
        sty ZP_DST+1
        lda ZP_TMP+1
        beq +
        lda #255                ; more than 255: the rest of the string
        sta ZP_TMP
+       dex                     ; the start
        dex
        lda #255                ; past 255: past the end of any string
        ldy ESTK+1,x
        bne +
        lda ESTK,x
        beq +                   ; 0 is the same as 1
        dec a
+       sta ZP_TMP+1            ; the first character, counted from 0
pop     dex                     ; the string. R_LEFT enters here.
        dex
        lda ESTK,x
        sta ZP_PTR
        lda ESTK+1,x
        sta ZP_PTR+1
take    ldy #1                  ; R_RIGHT enters here, with ZP_PTR set.
        lda (ZP_PTR),y
        sec
        sbc ZP_TMP+1            ; the characters from the first one on
        bcs +
        lda #0                  ; the first one is past the end
+       cmp ZP_TMP
        bcc +
        lda ZP_TMP              ; the length: the shorter of the length asked and the rest
+       sta (ZP_DST),y
        tay
        beq done
        lda ZP_PTR              ; (ZP_PTR),y with y = 1 is the first character taken
        sec
        adc ZP_TMP+1
        sta ZP_PTR
        bcc +
        inc ZP_PTR+1
+       inc ZP_DST              ; (ZP_DST),y with y = 1 is the first character of the temp
        bne copy
        inc ZP_DST+1
copy    lda (ZP_PTR),y
        sta (ZP_DST),y
        dey
        bne copy
done    rts
        #endtpl
        .endblock

; A = INSTR(string, find, start): the position of the first find in the string at or after the
; start, counted from 1. 0 when there is none, or when find is empty. The start is the WORD in
; A/Y, and 0 is the same as 1. The string and find are on the expression stack. Pops both,
; keeps X.
R_INSTR .block
        #tpl
        sta ZP_TMP              ; the start
        dex                     ; find
        dex
        lda ESTK,x
        sta ZP_DST
        lda ESTK+1,x
        sta ZP_DST+1
        dex                     ; the string
        dex
        lda ESTK,x
        sta ZP_PTR
        lda ESTK+1,x
        sta ZP_PTR+1
        tya
        bne none                ; a start past 255
        ldy #1
        lda (ZP_DST),y
        beq none                ; an empty find
        sta ZP_TMP+1            ; the length of find
        lda ZP_TMP
        bne +
        inc ZP_TMP              ; 0 is the same as 1
+       lda (ZP_PTR),y
        sec
        sbc ZP_TMP+1
        bcc none                ; find is longer than the string
        adc #0                  ; C set: the last start
        cmp ZP_TMP
        bcc none                ; the start is past it
        phx
        tay
        iny
        sbc ZP_TMP              ; C set: the tries - 1
        tax
        inx                     ; the tries, 1 to 255
        lda ZP_TMP              ; (ZP_PTR) is the character at the start
        sec
        adc ZP_PTR
        sta ZP_PTR
        bcc +
        inc ZP_PTR+1
+       sty ZP_TMP              ; the last start + 1, so the position is ZP_TMP - X
        lda ZP_DST              ; (ZP_DST) is the first character of find
        clc
        adc #2
        sta ZP_DST
        bcc scan
        inc ZP_DST+1
scan    lda (ZP_PTR)
        cmp (ZP_DST)
        beq check
next    inc ZP_PTR
        bne +
        inc ZP_PTR+1
+       dex
        bne scan
        plx
none    lda #0
        rts
check   ldy ZP_TMP+1            ; the first characters are the same: compare the rest
-       dey
        beq found
        lda (ZP_PTR),y
        cmp (ZP_DST),y
        beq -
        bra next
found   txa                     ; A = ZP_TMP - X
        eor #$ff
        sec
        adc ZP_TMP
        plx
        rts
        #endtpl
        .endblock

; Read from the input into the block at A/Y, cut at the block's max. The end is not stored,
; and a cut drops the rest up to the end. Returns the block in A/Y, keeps X. Three entries:
;   0      the first field: print "? ", then as field
;   field  a field, which ends at a comma or a CR. C set: the rest of the line is dropped
;   line   LINPUT, a line, which ends at a CR
R_INPUT .block
        #tpl
        php
        pha
        lda #"?"
        #rec jsr, S_CHROUT      ; CHROUT keeps Y
        lda #" "
        #rec jsr, S_CHROUT
        pla
        plp
field   ror ZP_TMP+1            ; C: the rest after a comma is dropped
        sec                     ; a comma ends it
        .byte $24               ; BIT zp: skips the clc
line    clc
        ror ZP_TMP+1            ; bit 7: a comma ends it. bit 6: the rest is dropped
        sta ZP_DST
        sty ZP_DST+1
        phx
        clc                     ; ZP_PTR: where the next character goes
        adc #2
        sta ZP_PTR
        tya
        adc #0
        sta ZP_PTR+1
        stz ZP_TMP              ; the length
next    #rec jsr, S_CHRIN
        cmp #13
        beq cr
        cmp #","
        bne keep
        bit ZP_TMP+1
        bpl keep                ; LINPUT keeps a comma
        bvc done                ; the rest is the next field
skip    #rec jsr, S_CHRIN       ; drop the rest of the line
        cmp #13
        bne skip
cr
        .if UXDOS == 0              ; on UXDOS16, con_line has moved the cursor to the next line
        #rec jsr, S_CHROUT      ; the editor leaves the cursor on the line typed
        .endif
        bra done
keep    tax
        lda ZP_TMP
        cmp (ZP_DST)            ; full: drop the character
        beq next
        txa
        sta (ZP_PTR)
        inc ZP_PTR
        bne +
        inc ZP_PTR+1
+       inc ZP_TMP
        bra next
done    lda ZP_TMP
        ldy #1
        sta (ZP_DST),y
        plx
        lda ZP_DST
        ldy ZP_DST+1
        rts
        #endtpl
        .endblock

; STR$ of the signed WORD in ZP_TMP into the block at A/Y: a - and the digits for a negative
; one, else as R_STR.
R_SSTR  .block
        #tpl
        bit ZP_TMP+1
        bmi minus
        #rec jmp, R_STR
minus   sta ZP_DST
        sty ZP_DST+1
        phx
        sec                     ; ZP_TMP = 0 - ZP_TMP
        lda #0
        sbc ZP_TMP
        sta ZP_TMP
        lda #0
        sbc ZP_TMP+1
        sta ZP_TMP+1
        ldy #2
        lda #"-"
        #rec jmp, R_STR, R_STR.sign - R_STR.rec_code
        #endtpl
        .endblock

; STR$ of the LONG in A/Y/ZP_HI into the block at ZP_DST.
R_LSTR  .block
        #tpl
        #rec jsr, R_LTOZ
        lda #" "                ; the sign
sign    ldy #2                  ; R_SLSTR comes in here
        sta (ZP_DST),y
        #rec jmp, R_LTEXT
        #endtpl
        .endblock

; STR$ of the signed LONG in A/Y/ZP_HI into the block at ZP_DST: a - and the digits for a
; negative one, else as R_LSTR.
R_SLSTR .block
        #tpl
        bit ZP_HI+1
        bmi minus
        #rec jmp, R_LSTR
minus   #rec jsr, R_NEGL
        #rec jsr, R_LTOZ
        lda #"-"
        #rec jmp, R_LSTR, R_LSTR.sign - R_LSTR.rec_code
        #endtpl
        .endblock

; The digits of the LONG in ZP_LL into the block at ZP_DST, after the sign at offset 2, with
; no leading zeros, and the block's length. Y = 2. Keeps X.
R_LTEXT .block
        #tpl
        phx
        ldx #0                  ; 4 x the power of ten
digit   lda #"0"
        sta ZP_PTR
sub     sec                     ; count how many times the power of ten goes
        lda ZP_LL
        #selfx sbc, tens
        sta ZP_LX
        lda ZP_LL+1
        #selfx sbc, tens+1
        sta ZP_LX+1
        lda ZP_LL+2
        #selfx sbc, tens+2
        sta ZP_LX+2
        lda ZP_LL+3
        #selfx sbc, tens+3
        bcc out
        sta ZP_LL+3
        lda ZP_LX+2
        sta ZP_LL+2
        lda ZP_LX+1
        sta ZP_LL+1
        lda ZP_LX
        sta ZP_LL
        inc ZP_PTR
        bra sub
out     lda ZP_PTR
        cmp #"0"
        bne show
        cpy #3
        bcc next                ; only the sign is written: a leading zero
show    iny
        sta (ZP_DST),y
next    inx
        inx
        inx
        inx
        cpx #36
        bne digit
        lda ZP_LL               ; the ones, always written
        ora #"0"
        iny
        sta (ZP_DST),y
        tya                     ; the length: the last offset - 1
        dec a
        ldy #1
        sta (ZP_DST),y
        plx
        rts
tens    .dword 1000000000, 100000000, 10000000, 1000000, 100000, 10000, 1000, 100, 10
        #endtpl
        .endblock

; A/Y/ZP_HI = the number the string at A/Y starts with, read as R_VAL reads it, in 32 bits.
; A number past 4294967295 wraps. Keeps X.
R_LVAL  .block
        #tpl
        sta ZP_PTR
        sty ZP_PTR+1
        phx
        stz ZP_LL               ; the value
        stz ZP_LL+1
        stz ZP_LL+2
        stz ZP_LL+3
        ldy #1
        lda (ZP_PTR),y
        tax                     ; the characters left
        inc ZP_PTR              ; (ZP_PTR),y with y = 1 is the first character
        bne +
        inc ZP_PTR+1
+       #self jsr, skip
        plx
        #rec jmp, R_LQUOT
end     rts
skip    txa
        beq end
        lda (ZP_PTR),y
        iny
        dex
        cmp #" "
        beq skip
        cmp #"+"
        beq skip
        cmp #"-"
        beq minus
digit   sec
        sbc #"0"
        cmp #10
        bcs done                ; not a digit
        pha
        lda ZP_LL               ; the value x 10: x 4, + the value, x 2
        sta ZP_LX
        lda ZP_LL+1
        sta ZP_LX+1
        lda ZP_LL+2
        sta ZP_LX+2
        lda ZP_LL+3
        sta ZP_LX+3
        asl ZP_LL
        rol ZP_LL+1
        rol ZP_LL+2
        rol ZP_LL+3
        asl ZP_LL
        rol ZP_LL+1
        rol ZP_LL+2
        rol ZP_LL+3
        clc
        lda ZP_LL
        adc ZP_LX
        sta ZP_LL
        lda ZP_LL+1
        adc ZP_LX+1
        sta ZP_LL+1
        lda ZP_LL+2
        adc ZP_LX+2
        sta ZP_LL+2
        lda ZP_LL+3
        adc ZP_LX+3
        sta ZP_LL+3
        asl ZP_LL
        rol ZP_LL+1
        rol ZP_LL+2
        rol ZP_LL+3
        pla                     ; + the digit
        clc
        adc ZP_LL
        sta ZP_LL
        bcc more
        inc ZP_LL+1
        bne more
        inc ZP_LL+2
        bne more
        inc ZP_LL+3
more    txa
        beq done
        lda (ZP_PTR),y
        iny
        dex
        bra digit
minus   #self jsr, more         ; the digits after the minus, then 0 minus them
        sec
        lda #0
        sbc ZP_LL
        sta ZP_LL
        lda #0
        sbc ZP_LL+1
        sta ZP_LL+1
        lda #0
        sbc ZP_LL+2
        sta ZP_LL+2
        lda #0
        sbc ZP_LL+3
        sta ZP_LL+3
done    rts
        #endtpl
        .endblock

; The temp at A/Y = LEFT$(string, length). The length is the WORD in ZP_TMP. The string is on
; the expression stack. Pops it, keeps X.
; WARNING: the temp must not be the source block.
R_LEFT  .block
        #tpl
        sta ZP_DST
        sty ZP_DST+1
        lda ZP_TMP+1
        beq +
        lda #255                ; more than 255: the whole string
        sta ZP_TMP
+       stz ZP_TMP+1            ; the first character, counted from 0
        #rec jmp, R_MID, R_MID.pop - R_MID.rec_code
        #endtpl
        .endblock

; The temp at A/Y = RIGHT$(string, length). The length is the WORD in ZP_TMP. The string is on
; the expression stack. Pops it, keeps X.
; WARNING: the temp must not be the source block.
R_RIGHT .block
        #tpl
        sta ZP_DST
        sty ZP_DST+1
        lda ZP_TMP+1
        beq +
        lda #255                ; more than 255: the whole string
        sta ZP_TMP
+       dex                     ; the string
        dex
        lda ESTK,x
        sta ZP_PTR
        lda ESTK+1,x
        sta ZP_PTR+1
        ldy #1
        lda (ZP_PTR),y
        sec
        sbc ZP_TMP
        bcs +
        lda #0                  ; longer than the string: all of it
+       sta ZP_TMP+1            ; the first character, counted from 0
        #rec jmp, R_MID, R_MID.take - R_MID.rec_code
        #endtpl
        .endblock
