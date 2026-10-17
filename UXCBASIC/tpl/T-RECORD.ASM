; T-RECORD.ASM -- records of a TYPE.

; The record S0 = the record S1, S2 bytes, from the last byte down.
T_RCOPY .block
        #tpl
        #lo ldy, S2
loop
        #aby lda, S1, $ffff
        #aby sta, S0, $ffff
        dey
        bne loop
        #endtpl
        .endblock

; The record at the address popped off the expression stack = the record at A/Y, S0 bytes.
T_RCOPY_P .block
        #tpl
        sta ZP_PTR
        sty ZP_PTR+1
        #lo ldy, S0
        #rec jsr, R_RCOPY
        #endtpl
        .endblock

; Copy Y bytes, 1 to 255, from the address in ZP_PTR to the address popped off the
; expression stack, from the last byte down.
R_RCOPY .block
        #tpl
        dex
        dex
        lda ESTK,x
        sta ZP_DST
        lda ESTK+1,x
        sta ZP_DST+1
loop    dey
        lda (ZP_PTR),y
        sta (ZP_DST),y
        tya
        bne loop
        rts
        #endtpl
        .endblock

; A/Y = the address of element A/Y of the array S2: the count S0 (0 for no check), the size
; S1.
T_RELEM .block
        #tpl
        #rec jsr, R_RELEM
        #dw S0
        #db S1
        #dw S2
        #endtpl
        .endblock

; A/Y = the base + the index A/Y times the size. The JSR is followed by the count (word, 0 for
; no check), the size (byte, 1-255) and the base (word). An index of the count or more stops
; the program with ?BAD SUBSCRIPT ERROR at the JSR. Keeps X.
R_RELEM .block
        #tpl
        sta ZP_TMP              ; the index, doubled for each bit of the size
        sty ZP_TMP+1
        pla                     ; the last byte of the JSR
        sta ZP_PTR
        pla
        sta ZP_PTR+1
        ldy #1
        lda (ZP_PTR),y          ; the count
        iny
        ora (ZP_PTR),y
        beq base
        dey
        lda ZP_TMP
        cmp (ZP_PTR),y
        iny
        lda ZP_TMP+1
        sbc (ZP_PTR),y
        bcc base
        lda ZP_PTR+1            ; the error site, back for R_ERROR
        pha
        lda ZP_PTR
        pha
        #rec jmp, R_ESUB
base    ldy #5
        lda (ZP_PTR),y
        sta ZP_DST+1            ; the address, from the base up
        dey
        lda (ZP_PTR),y
        sta ZP_DST
        dey
        lda (ZP_PTR),y          ; the size, shifted out a bit at a time
loop    lsr a
        bcc next
        tay
        clc
        lda ZP_DST
        adc ZP_TMP
        sta ZP_DST
        lda ZP_DST+1
        adc ZP_TMP+1
        sta ZP_DST+1
        tya
next    asl ZP_TMP
        rol ZP_TMP+1
        tay
        bne loop
        clc                     ; return past the data
        lda ZP_PTR
        adc #6
        sta ZP_PTR
        bcc done
        inc ZP_PTR+1
done    lda ZP_DST
        ldy ZP_DST+1
        jmp (ZP_PTR)
        #endtpl
        .endblock

; The max S3 and a length of 0, in S2 string blocks S1 bytes apart, from the address S0.
T_RMAX  .block
        #tpl
        #lo lda, S0
        sta ZP_PTR
        #hi lda, S0
        sta ZP_PTR+1
        #lo lda, S2
        sta ZP_TMP
        #hi lda, S2
        sta ZP_TMP+1
        #lo lda, S1
        sta ZP_DST
        #lo lda, S3
        #rec jsr, R_RMAX
        #endtpl
        .endblock

; Store A, then 0, at the address in ZP_PTR, ZP_TMP times, ZP_DST bytes apart. ZP_TMP is
; at least 1. Keeps X.
R_RMAX  .block
        #tpl
        sta ZP_DST+1            ; the max
loop    lda ZP_DST+1
        sta (ZP_PTR)
        ldy #1
        lda #0
        sta (ZP_PTR),y
        clc
        lda ZP_PTR
        adc ZP_DST
        sta ZP_PTR
        bcc +
        inc ZP_PTR+1
+       lda ZP_TMP
        bne +
        dec ZP_TMP+1
+       dec ZP_TMP
        lda ZP_TMP
        ora ZP_TMP+1
        bne loop
        rts
        #endtpl
        .endblock
