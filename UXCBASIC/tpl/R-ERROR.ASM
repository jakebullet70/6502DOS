; R-ERROR.ASM -- run-time errors.
;
; Each message is a stub: a JSR to R_ERROR, then the message as [len][text]. A runtime routine
; that finds an error JMPs to the stub. User code called that routine with a JSR, so under the
; stub's return address the stack holds the error site.

; Stop with ?<message> ERROR AT $<site>, where the site is the address of the user code's JSR,
; and end the program as T_END does.
R_ERROR .block
        #tpl
        pla                     ; the message address, less 1
        sta ZP_PTR
        pla
        sta ZP_PTR+1
        pla                     ; the error site: the last byte of its JSR
        sta ZP_TMP
        pla
        sta ZP_TMP+1
        ldx #0                  ; CR, "?"
        #self jsr, put
        ldy #1
        lda (ZP_PTR),y          ; the message length
        tax
msg     iny
        lda (ZP_PTR),y
        #rec jsr, S_CHROUT      ; CHROUT keeps X and Y
        dex
        bne msg
        ldx #tail - head        ; " ERROR AT $"
        #self jsr, put
        sec                     ; the JSR's own address is the site - 2
        lda ZP_TMP
        sbc #2
        tax
        lda ZP_TMP+1
        sbc #0
        #self jsr, hex
        txa
        #self jsr, hex
        lda #13
        #rec jsr, S_CHROUT
        #rec jmp, S_EXIT
put    #selfx lda, head        ; print from head+X up to a 0 byte
        beq done
        #rec jsr, S_CHROUT
        inx
        bra put
done    rts
hex     pha                     ; print A as two hex digits
        lsr a
        lsr a
        lsr a
        lsr a
        #self jsr, nib
        pla
        and #$0f
nib     cmp #10
        bcc dig
        adc #6                  ; C is set, so this adds 7: past "9" to "A"
dig     adc #"0"
        #rec jmp, S_CHROUT
head    .byte 13
        .text "?"
        .byte 0
tail    .text " ERROR AT $"
        .byte 0
        #endtpl
        .endblock

; The message stubs.
R_EDIVZ .block
        #tpl
        #rec jsr, R_ERROR
        .byte 16
        .text "DIVISION BY ZERO"
        #endtpl
        .endblock

R_ESUB  .block
        #tpl
        #rec jsr, R_ERROR
        .byte 13
        .text "BAD SUBSCRIPT"
        #endtpl
        .endblock

R_EFILE .block
        #tpl
        #rec jsr, R_ERROR
        .byte 13
        .text "FILE NOT OPEN"
        #endtpl
        .endblock
