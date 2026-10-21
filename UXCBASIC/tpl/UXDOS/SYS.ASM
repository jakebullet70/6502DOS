; SYS.ASM for 6502DOS -- the system table of the 6502DOS target. Each record reaches 6502DOS
; through its API (API.ASM). The records are tpl/SYS.ASM's, in the same order. The 6502DOS
; R-FILE.ASM uses handles and links none of the KERNAL file records, so those are a bare RTS.

; Write A to the output handle: STDOUT, or the handle R_FILE.chkout chose. Keeps A, X and Y.
S_CHROUT .block
        #tpl
        sta ZP_GOT
        phx
        phy
        lda #ZP_GOT
        sta API_R0
        stz API_R0+1
        lda #1
        sta API_R1
        stz API_R1+1
        ldx ZP_OUT
        jsr API_WRITE
        ply
        plx
        lda ZP_GOT
        rts
        #endtpl
        .endblock

; The cursor: C set gets the row in X and the column in Y, C clear moves it there.
S_PLOT  .block
        #tpl
        jmp API_CURSOR
        #endtpl
        .endblock

; A = the waiting key, or 0 when no key waits.
S_GETIN .block
        #tpl
        jsr API_STATUS          ; Z set: no key
        beq +
        jmp API_IN
+       rts
        #endtpl
        .endblock

; The next character of a line typed at the console, CR last. Reads a line with con_line when
; none is left. Changes X and Y.
S_CHRIN .block
        #tpl
        #rec ldx, R_LINE, R_LINE.next
        bne take
        lda #81                 ; 80 characters, then the CR
        #rec sta, R_LINE, R_LINE.line
        #self lda, line_at
        sta API_R0
        #self lda, line_at+1
        sta API_R0+1
        jsr API_LINE
        ldx #2
take    #recx lda, R_LINE, R_LINE.line
        inx
        cmp #13
        bne +
        ldx #0                  ; the line is done
+       #rec stx, R_LINE, R_LINE.next
        rts
line_at #recdw R_LINE, R_LINE.line
        #endtpl
        .endblock

S_READST .block
        #tpl
        rts
        #endtpl
        .endblock

S_SETLFS .block
        #tpl
        rts
        #endtpl
        .endblock

S_SETNAM .block
        #tpl
        rts
        #endtpl
        .endblock

S_OPEN  .block
        #tpl
        rts
        #endtpl
        .endblock

S_CLOSE .block
        #tpl
        rts
        #endtpl
        .endblock

S_CHKIN .block
        #tpl
        rts
        #endtpl
        .endblock

S_CHKOUT .block
        #tpl
        rts
        #endtpl
        .endblock

S_CLRCHN .block
        #tpl
        rts
        #endtpl
        .endblock

S_LKUPLA .block
        #tpl
        rts
        #endtpl
        .endblock

; Startup: the output goes to STDOUT. 6502DOS keeps the screen in CP437, so there is nothing
; else to set.
S_INIT  .block
        #tpl
        lda #STDOUT
        sta ZP_OUT
        rts
        #endtpl
        .endblock

; The exit: back to the program that ran this one, with exit code 0. T_END and R_ERROR jump
; here.
S_EXIT  .block
        #tpl
        lda #0
        jmp API_EXIT
        #endtpl
        .endblock

; SYS: call the address in A/Y with A, X, Y and P from $030C-$030F, as X16 BASIC does, and
; store the four back after the call. P loses D and I. Keeps X.
R_SYS   .block
        #tpl
        sta ZP_PTR
        sty ZP_PTR+1
        phx
        lda $030f
        and #$f3
        pha
        lda $030c
        ldx $030d
        ldy $030e
        plp
        #self jsr, call
        php
        sta $030c
        stx $030d
        sty $030e
        pla
        sta $030f
        plx
        rts
call    jmp (ZP_PTR)
        #endtpl
        .endblock

; SYS a: the address is in A/Y.
T_SYS   .block
        #tpl
        #rec jsr, R_SYS
        #endtpl
        .endblock
