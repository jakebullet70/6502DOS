; R-FILE.ASM for 6502DOS -- the runtime routines for files, through 6502DOS handles.
;
; A handle is a 6502DOS handle. Handles 0-2 are standard input, output and error. The records
; and their entries are tpl/R-FILE.ASM's. OPEN passes the name with its mode letter last:
; R for O.READ, W for O.WRITE, A for O.APPEND.

; Open the file named by the string at A/Y, its mode letter last. A/Y = the handle, or NOFILE
; ($FFFF) when the open fails. The string is whole again on return.
R_FILE  .block
        #tpl
        phx
        sta ZP_PTR
        sty ZP_PTR+1
        ldy #1
        lda (ZP_PTR),y          ; the length, the mode letter included
        dec a                   ; the path leaves the letter out until the end
        sta (ZP_PTR),y
        tay
        iny
        iny
        lda (ZP_PTR),y          ; the mode letter
        sta ZP_TMP
        clc                     ; r0 = the path, at its length byte
        lda ZP_PTR
        adc #1
        sta API_R0
        lda ZP_PTR+1
        adc #0
        sta API_R0+1
        lda ZP_TMP
        cmp #"W"
        beq create
        and #1                  ; R ($52): access 0, read. A ($41): access 1, write
        jsr API_OPEN
        bcc opened
        ldy ZP_TMP
        cpy #"A"
        bne fail
        cmp #2                  ; O.APPEND makes a file that is not there
        bne fail
create  lda #0                  ; no attributes
        jsr API_CREATE
        bcs fail
opened  stx ZP_TMP+1
        lda ZP_TMP
        cmp #"A"
        bne back
        stz API_R0              ; O.APPEND: to the end
        stz API_R0+1
        stz API_R1
        stz API_R1+1
        lda #2
        jsr API_SEEK
        bra back
fail    lda #$ff
        sta ZP_TMP+1
back    ldy #1                  ; the mode letter back into the length
        lda (ZP_PTR),y
        inc a
        sta (ZP_PTR),y
        ldy #0
        lda ZP_TMP+1
        bpl +
        dey                     ; NOFILE
+       plx
        rts

; Close handle A. Handles 0-2 stay open. A handle that is not open, NOFILE included, is
; ignored.
close   cmp #3
        bcc done
        phx
        tax
        jsr API_CLOSE
        plx
done    rts

; Send the output to handle A until clrchn. A handle that is not open stops the program with
; FILE NOT OPEN.
chkout  phx
        pha
        tax
        lda #6
        jsr API_IOCTL           ; C set: not open
        pla
        plx
        bcs bad
        sta ZP_OUT
        rts
bad     #rec jmp, R_EFILE

; Send the output back to STDOUT. Keeps X.
clrchn  lda #STDOUT
        sta ZP_OUT
        rts
        #endtpl
        .endblock

; Reading. ioctl input status tells the end of a file before a read reaches it.

; Open for reading: R_FILE. A/Y as R_FILE.
R_FIN   .block
        #tpl
        #rec jmp, R_FILE

; Take the input from handle A until clrchn. A handle that is not open stops the program with
; FILE NOT OPEN.
chkin   sta ZP_FILE
        phx
        tax
        lda #6
        jsr API_IOCTL           ; C set: not open
        plx
        bcs bad
        rts
bad     #rec jmp, R_EFILE

; EOF(handle A): C set when the next read returns nothing, or the handle is not open. Keeps X.
eof     phx
        tax
        lda #6
        jsr API_IOCTL
        plx
        bcs +
        lda #0                  ; C set when r0 is 0: no byte
        cmp API_R0
+       rts

; The next byte of the input in A, C clear. C set: the end of the file. Loses X and Y.
getc    ldx ZP_FILE
        lda #ZP_GOT
        sta API_R0
        stz API_R0+1
        lda #1
        sta API_R1
        stz API_R1+1
        jsr API_READ
        bcs +                   ; an error reads as the end
        lda #0                  ; C set when r1 is 0: no byte
        cmp API_R1
        lda ZP_GOT
+       rts

; Read from the input into the block at A/Y, cut at the block's max; the rest of the line is
; dropped. A line ends at CR, LF, CR LF or the end of the file, and the end is not stored.
; Returns the block in A/Y, keeps X.
;   field  INPUT #: a comma ends it too
;   line   LINPUT #
field   sec
        .byte $24               ; BIT zp: skips the clc
line    clc
        ror ZP_TMP+1            ; bit 7: a comma ends it
        sta ZP_DST
        sty ZP_DST+1
        phx
        lda (ZP_DST)            ; the room left
        sta ZP_PTR
        stz ZP_TMP              ; the length
next    #self jsr, getc
        bcs done
        cmp #13
        beq cr
        cmp #10
        beq done
        cmp #","
        bne keep
        bit ZP_TMP+1
        bmi done
keep    ldy ZP_PTR
        beq next                ; full: drop the byte
        dec ZP_PTR
        ldy ZP_TMP
        iny
        iny
        sta (ZP_DST),y
        inc ZP_TMP
        bra next
cr      ldx ZP_FILE             ; drop an LF after the CR
        lda #6
        jsr API_IOCTL
        lda API_R0
        beq done                ; nothing waits: a read would block on a device
        #self jsr, getc
        bcs done
        cmp #10
        beq done
        ldx ZP_FILE             ; not an LF: step back over it
        lda #$ff
        sta API_R0
        sta API_R0+1
        sta API_R1
        sta API_R1+1
        lda #1
        jsr API_SEEK
done    lda ZP_TMP
        ldy #1
        sta (ZP_DST),y
        plx
        lda ZP_DST
        ldy ZP_DST+1
        rts
        #endtpl
        .endblock

; READ(handle, address, max): up to max bytes of the handle go to memory from the address.
; The handle and the address are on the stack, the max is in A/Y. A/Y = the count read, 0 at
; the end of the file. Pops both. A handle that is not open stops the program with FILE NOT OPEN.
R_FREAD .block
        #tpl
        sta API_R1              ; the max
        sty API_R1+1
        dex                     ; the address
        dex
        lda ESTK,x
        sta API_R0
        lda ESTK+1,x
        sta API_R0+1
        dex                     ; the handle
        dex
        lda ESTK,x
        phx
        tax
        jsr API_READ
        plx
        bcc +
        cmp #6
        beq bad
        stz API_R1              ; any other error reads nothing
        stz API_R1+1
+       lda API_R1
        ldy API_R1+1
        rts
bad     #rec jmp, R_EFILE
        #endtpl
        .endblock

; WRITE handle, address, count: count bytes from memory at the address go to the handle.
; The handle and the address are on the stack, the count is in A/Y. Pops both. A handle that
; is not open stops the program with FILE NOT OPEN.
R_FWRITE .block
        #tpl
        sta API_R1              ; the count
        sty API_R1+1
        dex                     ; the address
        dex
        lda ESTK,x
        sta API_R0
        lda ESTK+1,x
        sta API_R0+1
        dex                     ; the handle
        dex
        lda ESTK,x
        phx
        tax
        jsr API_WRITE
        plx
        bcc +
        cmp #6
        beq bad
+       rts
bad     #rec jmp, R_EFILE
        #endtpl
        .endblock
