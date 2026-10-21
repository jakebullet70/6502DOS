; T-ARRAY.ASM -- array elements, the startup clear of the array space, and R_KEY.
;
; An array is S0, the address of its element 0. B(I) with a BYTE index is T_LDB_AY. Any
; other index is a WORD: T_IDXB or T_IDXW makes it the element's address, then T_PEEK or
; T_PEEKW reads the element, or T_POKE or T_POKEW writes it through the expression stack.
; T_CHKB and T_CHKW stop the program when the index is not below the count S0.

; A = the BYTE array S0, element A.
T_LDB_AY .block
        #tpl
        tay
        #aby lda, S0
        #endtpl
        .endblock

; The BYTE array S0, at the index popped off the expression stack, = A.
T_STB_SY .block
        #tpl
        dex
        dex
        ldy ESTK,x
        #aby sta, S0
        #endtpl
        .endblock

; A/Y = the address of the BYTE array S0, element A/Y.
T_IDXB  .block
        #tpl
        clc
        #lo adc, S0
        pha
        tya
        #hi adc, S0
        tay
        pla
        #endtpl
        .endblock

; A/Y = the address of the WORD array S0, element A/Y.
T_IDXW  .block
        #tpl
        asl a
        pha
        tya
        rol a
        tay
        pla
        clc
        #lo adc, S0
        pha
        tya
        #hi adc, S0
        tay
        pla
        #endtpl
        .endblock

; A/Y = the WORD at the address in A/Y.
T_PEEKW .block
        #tpl
        sta ZP_PTR
        sty ZP_PTR+1
        ldy #1
        lda (ZP_PTR),y
        tay
        lda (ZP_PTR)
        #endtpl
        .endblock

; The WORD at the address popped off the expression stack = A/Y.
T_POKEW .block
        #tpl
        dex
        dex
        sta (ESTK,x)
        inc ESTK,x
        bne +
        inc ESTK+1,x
+       tya
        sta (ESTK,x)
        #endtpl
        .endblock

; Stop with BAD SUBSCRIPT unless the BYTE index in A is below the count S0, 1 to 255.
T_CHKB  .block
        #tpl
        #lo cmp, S0
        bcc ok
        #rec jsr, R_ESUB
ok
        #endtpl
        .endblock

; Stop with BAD SUBSCRIPT unless the WORD index in A/Y is below the count S0.
T_CHKW  .block
        #tpl
        #hi cpy, S0
        bcc ok
        bne bad
        #lo cmp, S0
        bcc ok
bad     #rec jsr, R_ESUB
ok
        #endtpl
        .endblock

; At startup: clear S1 bytes from the address S0, the array space.
T_ZERO  .block
        #tpl
        #lo lda, S0
        sta ZP_PTR
        #hi lda, S0
        sta ZP_PTR+1
        #lo lda, S1
        sta ZP_TMP
        #hi lda, S1
        sta ZP_TMP+1
        #rec jsr, R_ZERO
        #endtpl
        .endblock

; Clear ZP_TMP bytes from the address in ZP_PTR. Keeps X.
R_ZERO  .block
        #tpl
        phx
        ldx ZP_TMP+1            ; the whole pages
        ldy #0
        tya
page    cpx #0
        beq part
whole   sta (ZP_PTR),y
        iny
        bne whole
        inc ZP_PTR+1
        dex
        bra page
part    ldy ZP_TMP              ; the rest, from the top down
        beq done
rest    dey
        sta (ZP_PTR),y
        bne rest
done    plx
        rts
        #endtpl
        .endblock

; GETEXTKEY() and WAITKEY(): C clear waits for a key, the cursor blinking; C set returns at
; once. A/Y = the key: a plain key its character, an extended key its scan code * 256, no key
; 0. R_KEYMODS = the modifiers, for KEYMODS(). Keeps X. The stock table has no con_getkey; its
; record returns no key.
R_KEY   .block
        #tpl
        .if UXDOS != 0
        phx
        jsr API_GETKEY
        #rec sty, R_KEYMODS
        pha
        txa
        tay
        pla
        plx
        .else
        lda #0
        tay
        .endif
        rts
        #endtpl
        .endblock

; A/Y = the address of the LONG array S0, element A/Y.
T_IDXL  .block
        #tpl
        asl a
        pha
        tya
        rol a
        tay
        pla
        asl a
        pha
        tya
        rol a
        tay
        pla
        clc
        #lo adc, S0
        pha
        tya
        #hi adc, S0
        tay
        pla
        #endtpl
        .endblock

; A/Y/ZP_HI = the LONG at the address in A/Y.
T_PEEKL .block
        #tpl
        sta ZP_PTR
        sty ZP_PTR+1
        ldy #3
        lda (ZP_PTR),y
        sta ZP_HI+1
        dey
        lda (ZP_PTR),y
        sta ZP_HI
        dey
        lda (ZP_PTR),y
        tay
        lda (ZP_PTR)
        #endtpl
        .endblock

; The LONG at the address popped off the expression stack = A/Y/ZP_HI.
T_POKEL .block
        #tpl
        dex
        dex
        pha
        lda ESTK,x
        sta ZP_PTR
        lda ESTK+1,x
        sta ZP_PTR+1
        pla
        sta (ZP_PTR)
        tya
        ldy #1
        sta (ZP_PTR),y
        iny
        lda ZP_HI
        sta (ZP_PTR),y
        iny
        lda ZP_HI+1
        sta (ZP_PTR),y
        #endtpl
        .endblock
