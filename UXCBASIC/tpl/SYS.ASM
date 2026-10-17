; SYS.ASM -- the system table. Code reaches the KERNAL only through these records, so a port
; to the new machine rewrites only this file. Each one is linked when something uses it.

S_CHROUT .block
        #tpl
        jmp $ffd2
        #endtpl
        .endblock

S_PLOT  .block
        #tpl
        jmp $fff0
        #endtpl
        .endblock

S_GETIN .block
        #tpl
        jmp $ffe4
        #endtpl
        .endblock

S_CHRIN .block
        #tpl
        jmp $ffcf
        #endtpl
        .endblock

S_READST .block
        #tpl
        jmp $ffb7
        #endtpl
        .endblock

S_SETLFS .block
        #tpl
        jmp $ffba
        #endtpl
        .endblock

S_SETNAM .block
        #tpl
        jmp $ffbd
        #endtpl
        .endblock

S_OPEN  .block
        #tpl
        jmp $ffc0
        #endtpl
        .endblock

S_CLOSE .block
        #tpl
        jmp $ffc3
        #endtpl
        .endblock

S_CHKIN .block
        #tpl
        jmp $ffc6
        #endtpl
        .endblock

S_CHKOUT .block
        #tpl
        jmp $ffc9
        #endtpl
        .endblock

S_CLRCHN .block
        #tpl
        jmp $ffcc
        #endtpl
        .endblock

; C clear when logical file A is open.
S_LKUPLA .block
        #tpl
        jmp $ff59
        #endtpl
        .endblock

; Startup, CBM only: keep $0372, turn on ISO mode, and load the CP437 font. Needs ROM R47.
S_INIT  .block
        #tpl
        lda $0372
        sta ZP_MODE
        lda #$0f                ; ISO mode on: CHROUT writes each byte as its screen code
        #rec jsr, S_CHROUT
        lda #7                  ; CP437
        jmp $ff62               ; screen_set_charset
        #endtpl
        .endblock

; The exit, CBM only: put back the kept charset and return to BASIC. T_END and R_ERROR jump
; here. When the kept mode is PETSCII, every screen code is first converted to the PETSCII
; screen code of the same character.
; WARNING: assumes the KERNAL text screen, VRAM $1B000 with 256 bytes a row.
S_EXIT  .block
        #tpl
        bit ZP_MODE             ; V = bit 6, set in ISO mode
        bvs font                ; an ISO screen reads the same in the kept charset
        sei                     ; the KERNAL's IRQ moves the VERA address
        jsr $ffed               ; SCREEN: X = columns, Y = rows
        stx ZP_TMP
        lda ZP_MODE             ; charsets 3 and 5 are upper/lower: upper case is $41-$5A
        lsr a
        lda #0
        bcc ug
        lda #$40
ug      sta ZP_TMP+1
        dey
row     stz $9f25               ; port 0 reads the row
        #self jsr, port
        lda #1                  ; port 1 writes the same cells
        sta $9f25
        #self jsr, port
        ldx ZP_TMP
cell    lda $9f23
        cmp #$20
        bcc blank
        cmp #$40
        bcc put                 ; $20-$3F: the same code
        cmp #$7c
        beq bar
        cmp #$7f
        bcs blank
        cmp #$41
        bcc low5
        cmp #$5b
        bcs low5
        and #$1f                ; A-Z
        ora ZP_TMP+1
        bra put
low5    and #$1f                ; @ [ \ ] ^ _ ` a-z { } ~ to $00-$1F
        bra put
bar     lda #$5d                ; | to the vertical line
        bra put
blank   lda #$20                ; no PETSCII glyph
put     sta $9f24
        dex
        bne cell
        dey
        bpl row
        stz $9f25
        cli
font    lda ZP_MODE
        and #63
        jsr $ff62
        lda ZP_MODE             ; screen_set_charset leaves bit 6 as it was
        sta $0372
        ldx ZP_SP
        txs
        rts
port    stz $9f20               ; VRAM $1B000 + Y * 256, step 2: the character bytes only
        tya
        clc
        adc #$b0
        sta $9f21
        lda #$21
        sta $9f22
        rts
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
