; R-FILE.ASM -- the runtime routines for files.
;
; A handle is the KERNAL logical file number, 3-14, on unit 8 with the same secondary address.
; Handles 0-2 are the console. Logical file 15 is the drive's command channel: the first OPEN
; opens it, and it stays open. The KERNAL's file table is the only record of what is open.

; Open the file named by the string at A/Y, a whole DOS name with its mode, such as
; "@:LOG,S,W". A/Y = the handle, or NOFILE ($FFFF) when no handle is free or the drive
; reports an error.
R_FILE  .block
        #tpl
        phx
        sta ZP_PTR
        sty ZP_PTR+1
        lda #15                 ; the command channel, opened once
        #rec jsr, S_LKUPLA
        bcc named
        lda #0
        #rec jsr, S_SETNAM
        lda #15
        ldx #8
        tay
        #rec jsr, S_SETLFS
        #rec jsr, S_OPEN
        bcs fail
named   lda #3                  ; the first logical file the KERNAL does not know
free    sta ZP_TMP
        #rec jsr, S_LKUPLA      ; C clear: in use
        bcs found
        lda ZP_TMP
        inc a
        cmp #15
        bne free
        bra fail
found   ldy #1
        lda (ZP_PTR),y          ; the name's length
        pha
        clc                     ; X/Y = its text
        lda ZP_PTR
        adc #2
        tax
        lda ZP_PTR+1
        adc #0
        tay
        pla
        #rec jsr, S_SETNAM
        lda ZP_TMP
        ldx #8
        tay
        #rec jsr, S_SETLFS
        #rec jsr, S_OPEN
        bcs fail
        ldx #15                 ; the drive's status: "00, OK" or an error number
        #rec jsr, S_CHKIN
        #rec jsr, S_CHRIN
        pha
skip    #rec jsr, S_CHRIN       ; read the rest of the message
        cmp #13
        beq read
        #rec jsr, S_READST
        beq skip
read    #rec jsr, S_CLRCHN
        pla
        cmp #"0"
        bne shut
        lda ZP_TMP
        ldy #0
        plx
        rts
shut    lda ZP_TMP
        #rec jsr, S_CLOSE
fail    lda #$ff
        tay
        plx
        rts

; Close handle A. A handle that is not open, NOFILE included, is ignored.
close   cmp #3
        bcc done
        cmp #15
        bcs done
        phx
        #rec jsr, S_CLOSE
        plx
done    rts

; Send the output to handle A until clrchn. Handles 0-2 are the screen. A handle that is not
; open stops the program with FILE NOT OPEN.
chkout  cmp #3
        bcc done
        phx
        tax
        #rec jsr, S_CHKOUT      ; C set: not open
        plx
        bcs bad
        rts
bad     #rec jmp, R_EFILE

; Send the output back to the screen.
clrchn  phx
        #rec jsr, S_CLRCHN
        plx
        rts
        #endtpl
        .endblock

; Reading. Each handle 3-14 holds the next byte of its file back, so EOF knows the end before
; a read hits it, and a CR can look at the byte after it. state: 0 a byte is held and more
; follow, $40 the byte held is the last, $80 nothing is held.

; Open for reading: R_FILE, then the first byte is read ahead. A/Y as R_FILE.
R_FIN   .block
        #tpl
        #rec jsr, R_FILE
        cpy #0
        bne +
        phx
        pha
        #self jsr, chkin
        #self jsr, fetch
        #rec jsr, S_CLRCHN
        pla
        ldy #0
        plx
+       rts

; Take the input from handle A until clrchn. A handle that is not open, 0-2 included, stops
; the program with FILE NOT OPEN.
chkin   sta ZP_FILE
        cmp #15
        bcs bad
        phx
        tax
        #rec jsr, S_CHKIN       ; C set: not open
        plx
        bcs bad
        rts
bad     #rec jmp, R_EFILE

; EOF(handle A): C set when the next read returns nothing. Keeps X.
eof     sec
        sbc #3
        cmp #12
        bcs +                   ; not a file handle: nothing to read
        phx
        tax
        #selfx lda, state
        plx
        asl a
+       rts

; The next byte of the input in A, C clear. C set: the end of the file. Loses X and Y.
getc    ldx ZP_FILE
        #selfx ldy, ahead-3
        #selfx lda, state-3
        asl a                   ; C: nothing held. N: the byte held is the last
        bcs +
        bmi last
        phy
        #self jsr, fetch
        ply
        bra out
last    lda #$80
        #selfx sta, state-3
out     tya
        clc
+       rts

; Read the next byte of handle ZP_FILE ahead. Loses X and Y.
fetch   #rec jsr, S_CHRIN
        ldx ZP_FILE
        #selfx sta, ahead-3
        #rec jsr, S_READST      ; $40: the byte is the last. Any other bit: no byte
        ldx ZP_FILE
        bit #$bf
        beq +
        lda #$80
+       #selfx sta, state-3
        rts

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
        #selfx lda, state-3
        bmi done
        #selfx lda, ahead-3
        cmp #10
        bne done
        #self jsr, getc
done    lda ZP_TMP
        ldy #1
        sta (ZP_DST),y
        plx
        lda ZP_DST
        ldy ZP_DST+1
        rts

ahead   .fill 12                ; per handle 3-14: the byte held back
state   .fill 12
        #endtpl
        .endblock

; READ(handle, address, max): up to max bytes of the handle go to memory from the address.
; The handle and the address are on the stack, the max is in A/Y. A/Y = the count read, 0 at
; the end of the file. Pops both. A handle that is not open stops the program with FILE NOT OPEN.
R_FREAD .block
        #tpl
        sta ZP_TMP              ; the max
        sty ZP_TMP+1
        dex                     ; the address
        dex
        lda ESTK,x
        sta ZP_PTR
        lda ESTK+1,x
        sta ZP_PTR+1
        dex                     ; the handle
        dex
        lda ESTK,x
        #rec jsr, R_FIN, R_FIN.chkin - R_FIN.rec_code
        phx
        stz ZP_DST              ; the count
        stz ZP_DST+1
next    lda ZP_DST
        cmp ZP_TMP
        bne more
        lda ZP_DST+1
        cmp ZP_TMP+1
        beq done
more    #rec jsr, R_FIN, R_FIN.getc - R_FIN.rec_code
        bcs done
        sta (ZP_PTR)
        inc ZP_PTR
        bne +
        inc ZP_PTR+1
+       inc ZP_DST
        bne next
        inc ZP_DST+1
        bra next
done    #rec jsr, S_CLRCHN
        plx
        lda ZP_DST
        ldy ZP_DST+1
        rts
        #endtpl
        .endblock

; WRITE handle, address, count: count bytes from memory at the address go to the handle.
; The handle and the address are on the stack, the count is in A/Y. Pops both. Handles 0-2
; are the screen. A handle that is not open stops the program with FILE NOT OPEN.
R_FWRITE .block
        #tpl
        sta ZP_TMP              ; the count left
        sty ZP_TMP+1
        dex                     ; the address
        dex
        lda ESTK,x
        sta ZP_PTR
        lda ESTK+1,x
        sta ZP_PTR+1
        dex                     ; the handle
        dex
        lda ESTK,x
        #rec jsr, R_FILE, R_FILE.chkout - R_FILE.rec_code
        phx
next    lda ZP_TMP
        ora ZP_TMP+1
        beq done
        lda (ZP_PTR)
        #rec jsr, S_CHROUT
        inc ZP_PTR
        bne +
        inc ZP_PTR+1
+       lda ZP_TMP
        bne +
        dec ZP_TMP+1
+       dec ZP_TMP
        bra next
done    #rec jsr, S_CLRCHN
        plx
        rts
        #endtpl
        .endblock
