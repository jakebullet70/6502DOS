; 6502DOS ROM bank 1: the functions of call 62, gfx, which api_gfx in vera.s runs. The bitmap
; on VERA's layer 0, under the console's text on layer 1.
;
; Trap: the console keeps VERA_CTRL at 0, so DCSEL selects DC_VIDEO and ADDRSEL data port 0;
; these routines rely on it.

.setcpu "65C02"

.include "mem.inc"
.include "api.inc"
.include "far.inc"

.export gfx_mode, gfx_clear, gfx_pset, gfx_point, gfx_line, gfx_frame, gfx_rect, gfx_circle, gfx_char
.import jsrfar1, clear
.importzp con_last_row, con_last_col

.segment "B1CODE"

; gfx_mode: shows screen A, clears the text and puts the cursor home. 0: 80 by 30 text alone.
; 1: 80 by 30 text over 640 by 240, 2 bpp. 2: 40 by 30 text over 320 by 240, 4 bpp. 3: 40 by 25
; text over 320 by 200, 8 bpp, both layers 200 lines between borders. Screens 1 to 3 clear the
; bitmap to color 0. Changes A, X and Y.
gfx_mode:
        tax
        lda gfx_config,x
        sta VERA_L0_CONFIG
        lda gfx_tilebase,x
        sta VERA_L0_TILEBASE
        stz VERA_L0_HSCROLL_H   ; palette offset 0
        lda gfx_hscale,x
        sta VERA_DC_HSCALE
        lda gfx_last_col,x
        sta con_last_col
        lda gfx_last_row,x
        sta con_last_row
        lda #1 << 1             ; DCSEL 1: DC_VSTART and DC_VSTOP
        sta VERA_CTRL
        lda gfx_vstart,x
        sta VERA_DC_VSTART
        lda gfx_vstop,x
        sta VERA_DC_VSTOP
        stz VERA_CTRL
        lda #$10                ; DC_VIDEO bit 4: layer 0 on
        trb VERA_DC_VIDEO
        cpx #1
        bcc @text               ; screen 0: layer 0 off
        tsb VERA_DC_VIDEO
        lda #0
        jsr gfx_clear
@text:
        FARCALL clear, jsrfar1
        clc
        rts

; The screens of gfx_mode by number. DC_VSTART and DC_VSTOP count 2 lines of the 480.
gfx_config:                     ; L0_CONFIG: a bitmap of 2, 4, 8 bpp
        .byte $00, $05, $06, $07
gfx_tilebase:                   ; L0_TILEBASE: bit 0 set, 640 pixels across
        .byte $00, BITMAP >> 11 << 2 | 1, BITMAP >> 11 << 2, BITMAP >> 11 << 2
gfx_hscale:
        .byte $80, $80, $40, $40
gfx_last_col:
        .byte 79, 79, 39, 39
gfx_last_row:
        .byte 29, 29, 29, 24
gfx_vstart:
        .byte 0, 0, 0, 20
gfx_vstop:
        .byte 240, 240, 240, 220

; gfx_clear: sets every pixel of the bitmap to color A: 0 to 3 on screen 1, 0 to 15 on screen
; 2, any on screen 3. Out of contract on screen 0. Changes A, X and Y.
gfx_clear:
        jsr gfx_spread
        .assert BITMAP = 0, error, "stz VERA_ADDR_L and _M need BITMAP at $00000"
        stz VERA_ADDR_L
        stz VERA_ADDR_M
        ldx #$10                ; bit 16 0, increment 1
        stx VERA_ADDR_H
        .assert <BITMAP_SIZE = 0 && <BITMAP3_SIZE = 0, error, "gfx_clear writes whole pages"
        ldx #>BITMAP_SIZE
        cpy #$07
        bne @pages
        ldx #>BITMAP3_SIZE
@pages:
        ldy #0
@byte:
        sta VERA_DATA0
        dey
        bne @byte
        dex
        bne @byte
        clc
        rts

; gfx_pset: sets the pixel at x r0, y r1 to color A, in the ranges of gfx_clear. Out of
; contract on screen 0 or off the bitmap. Changes A, X and Y.
gfx_pset:
        jsr gfx_spread
; gfx_plot: pset with A = the color in every pixel of a byte, as gfx_spread gives it.
gfx_plot:
        pha
        jsr gfx_at
        pla
        eor VERA_DATA0          ; the old bits under the mask become the color's
        and gfx_mask,y
        eor VERA_DATA0
        sta VERA_DATA0
        clc
        rts

; gfx_point: A = the color of the pixel at x r0, y r1. Out of contract on screen 0 or off the
; bitmap. Changes X and Y.
gfx_point:
        jsr gfx_at
        lda VERA_DATA0
        and gfx_mask,y
        ldx gfx_shift,y
        beq @done
@shift:
        lsr
        dex
        bne @shift
@done:
        clc
        rts

; gfx_line: draws a line from x r0, y r1 to x r2, y r3 in color A, both ends included, in the
; ranges of gfx_clear. Out of contract on screen 0 or with an end off the bitmap. Returns r0 =
; r2 and r1 = r3. Changes A, X, Y and r4 to r7.
gfx_line:
        jsr gfx_spread
        sta r7+1                ; the color in every pixel of a byte
        ldx #$FF                ; r5 = minus |y1 - y0|
        lda r3
        sec
        sbc r1
        ror r7                  ; bit 7: y rises
        bpl @dy
        eor #$FF
        inc a
        bne @dy
        tax                     ; y1 = y0: the high byte 0
@dy:
        sta r5
        stx r5+1
        sec                     ; r4 = |x1 - x0|
        lda r2
        sbc r0
        sta r4
        lda r2+1
        sbc r0+1
        ror r7                  ; bit 7: x rises, bit 6: y rises
        bmi @dx
        eor #$FF                ; minus: the high byte NOT, plus 1 when the low byte is 0
        tax
        lda #0
        sec
        sbc r4
        sta r4
        txa
        adc #0
@dx:
        sta r4+1
        jsr gfx_line_fx         ; carry set: VERA FX drew the line
        bcs @done
        clc                     ; r6 = the error, r4 + r5
        lda r4
        adc r5
        sta r6
        lda r4+1
        adc r5+1
        sta r6+1
@pixel:
        lda r7+1
        jsr gfx_plot
        lda r1                  ; done at x r2, y r3
        cmp r3
        bne @step
        lda r0
        cmp r2
        bne @step
        lda r0+1
        cmp r2+1
        beq @done
@step:
        lda r6                  ; X:Y = the error times 2
        asl a
        tay
        lda r6+1
        rol a
        tax
        tya                     ; a step in x when X:Y >= r5
        cmp r5
        txa
        sbc r5+1
        bmi @y
        clc
        lda r6
        adc r5
        sta r6
        lda r6+1
        adc r5+1
        sta r6+1
        bit r7
        bpl @left
        inc r0
        bne @y
        inc r0+1
        bra @y
@left:
        lda r0
        bne @low
        dec r0+1
@low:
        dec r0
@y:
        tya                     ; a step in y when X:Y <= r4: X:Y - r4 - 1 below 0
        clc
        sbc r4
        txa
        sbc r4+1
        bpl @pixel
        clc
        lda r6
        adc r4
        sta r6
        lda r6+1
        adc r4+1
        sta r6+1
        bit r7
        bvc @fall
        inc r1
        bra @pixel
@fall:
        dec r1
        bra @pixel
@done:
        clc
        rts

; gfx_line_fx: draws gfx_line's line with VERA FX's line helper, on 4 or 8 bpp with a VERA of
; version 0.3.1 or later. Takes Y = L0_CONFIG, r4 = |x1 - x0|, r5 = minus |y1 - y0|, r7 bit 7
; set when x rises and bit 6 when y rises, and r7+1 = the color in every pixel of a byte.
; Returns carry set when it drew the line, with r0 = r2 and r1 = r3, else carry clear. The
; slope has 9 bits of fraction, rounded, so a pixel between the ends can differ by one from
; gfx_line's own steps. Changes A, X, Y and r4 to r6.
;
; Trap: FX stays on until the last pixel. irq touches only VERA_ISR; an IRQ that wrote VRAM or
; VERA_CTRL would break the line.
gfx_line_fx:
        cpy #$06
        bcc @no                 ; 2 bpp: FX has no 2 bpp line; carry clear
        jsr gfx_fx_ok
        bcs @fx
@no:
        rts
@fx:
        sec                     ; r5 = |y1 - y0|, below 240
        lda #0
        sbc r5
        sta r5
        stz r5+1
        lda r4                  ; carry set: x the major axis
        cmp r5
        lda r4+1
        sbc #0
        bcs @major
        ldx r4                  ; y the major axis: r4 and r5 swap, both below 256
        lda r5
        sta r4
        stx r5
@major:
        ror r6                  ; r4 = the major, r5 = the minor; r6 bit 7: x the major axis
        lda #1                  ; ADDRSEL 1: gfx_at points data port 1 at the first pixel
        sta VERA_CTRL
        jsr gfx_at              ; Y = the place: 4 or 5 on 4 bpp, 6 on 8 bpp
        tya
        and #1                  ; the nibble address, ADDR1_H bit 1
        asl a
        sta VERA_ADDR_H
        lda gfx_fx_y_step - 4,y
        bit r7
        bvs @down
        ora #$08                ; DECR
@down:
        tax
        lda gfx_fx_x_step - 4,y
        bit r7
        bmi @right
        ora #$08
@right:
        bit r6
        bmi @steps
        pha                     ; y the major axis: A and X swap
        txa
        plx
@steps:
        tsb VERA_ADDR_H         ; ADDR1: a step on the major axis at every pixel
        stz VERA_CTRL
        stx VERA_ADDR_H         ; ADDR0: a step on the minor axis when the slope carries
        ldx gfx_fx_ctrl - 4,y
        stz r6+1                ; r6 = minor * 1024 / major; the 10 steps carry out bit 6
        lda #$40
        sta r6
@divide:
        asl r5
        rol r5+1
        lda r5
        sec
        sbc r4
        tay
        lda r5+1
        sbc r4+1
        bcc @bit
        sta r5+1
        sty r5
@bit:
        rol r6
        rol r6+1
        bcc @divide
        lda #2 << 1             ; DCSEL 2: FX_CTRL
        sta VERA_CTRL
        stx VERA_FX_CTRL
        lda #3 << 1             ; DCSEL 3: the slope, (r6 + 1) / 2; its high byte, written in
        sta VERA_CTRL           ; line draw, puts the position at half a pixel
        lsr r6+1
        lda r6
        ror a
        adc #0
        sta VERA_FX_X_INCR_L
        lda r6+1
        adc #0
        sta VERA_FX_X_INCR_H
        ldx r4                  ; r4 + 1 pixels
        ldy r4+1
        lda r7+1
@pixel:
        sta VERA_DATA1
        dex
        cpx #$FF
        bne @pixel
        dey
        bpl @pixel
        lda #2 << 1             ; FX off
        sta VERA_CTRL
        stz VERA_FX_CTRL
        stz VERA_CTRL
        lda r2
        sta r0
        lda r2+1
        sta r0+1
        lda r3
        sta r1
        sec
        rts

; By the place of gfx_at, 4 to 6: the FX line's ADDRx_H step in x and in y, rising, and its
; FX_CTRL, line draw with 4-bit mode on 4 bpp.
gfx_fx_x_step:
        .byte $04, $04, $10     ; half a byte by the nibble increment, or 1
gfx_fx_y_step:
        .byte $D0, $D0, $E0     ; 160 or 320
gfx_fx_ctrl:
        .byte $05, $05, $01

; gfx_fx_ok: carry set when VERA has FX: version 0.3.1 or later. Changes A and X.
gfx_fx_ok:
        lda #63 << 1            ; DCSEL 63: the version
        sta VERA_CTRL
        lda VERA_DC_VER3        ; carry set: version 0.3.1 or later
        cmp #1
        lda VERA_DC_VER2
        sbc #3
        lda VERA_DC_VER1
        sbc #0
        ldx VERA_DC_VER0
        stz VERA_CTRL
        bcc @done
        cpx #'V'
        beq @done               ; a VERA too old to give its version: no FX
        clc
@done:
        rts

; gfx_frame: draws the edge of the box from x r0, y r1 to x r2, y r3 in color A, in the ranges
; of gfx_clear, with r0 <= r2 and r1 <= r3. Out of contract on screen 0 or with a corner off
; the bitmap. Changes A, X, Y and r4 to r7.
gfx_frame:
        sec                     ; r7 bit 7: the edge alone
        .byte $24               ; BIT zp: skips the clc, keeps carry
; gfx_rect: fills the box of gfx_frame.
gfx_rect:
        clc
        ror r7
        jsr gfx_spread
        sta r7+1                ; the color in every pixel of a byte
        jsr gfx_fx_ok
        ror r7                  ; r7 bit 7: FX, bit 6: the edge alone
        bpl @top
        lda #6 << 1             ; DCSEL 6: the color in the 4 bytes of the FX cache
        sta VERA_CTRL
        lda r7+1
        sta VERA_FX_CACHE_L
        sta VERA_FX_CACHE_M
        sta VERA_FX_CACHE_H
        sta VERA_FX_CACHE_U
        stz VERA_CTRL
@top:
        lda r1
        sta r6                  ; the top row, for frame and the return
@row:
        bit r7
        bvc @span               ; rect: every row whole
        lda r1
        cmp r6
        beq @span               ; frame: the top and bottom rows whole
        cmp r3
        beq @span
        lda r7+1                ; frame: the sides
        jsr gfx_plot
        jsr gfx_swap
        lda r7+1
        jsr gfx_plot
        jsr gfx_swap
        bra @next
@span:
        jsr gfx_span
@next:
        lda r1
        inc r1
        cmp r3
        bcc @row
        lda r6
        sta r1
        clc
        rts

; gfx_span: fills row r1 from x r0 to x r2, r0 <= r2, with r7+1, the color in every pixel of a
; byte. With r7 bit 7 set, the FX cache holds r7+1 in its 4 bytes and the whole bytes go 4 at a
; store. Changes A, X, Y, r4 and r5.
;
; Trap: FX stays on through the groups of 4. irq touches only VERA_ISR; an IRQ that wrote VRAM
; or VERA_CTRL would break the row.
gfx_span:
        jsr gfx_swap
        jsr gfx_at              ; the last byte
        lda gfx_right,y
        sta r5                  ; its mask: the pixels to x r2
        lda VERA_ADDR_L
        sta r4
        lda VERA_ADDR_M
        sta r4+1
        jsr gfx_swap
        jsr gfx_at              ; the first byte
        clc                     ; X and r4+1 = the bytes between the first and the last
        lda r4
        sbc VERA_ADDR_L
        tax
        lda r4+1
        sbc VERA_ADDR_M
        sta r4+1
        bmi @one                ; $FFFF: the first byte is the last
        lda r7+1
        eor VERA_DATA0
        and gfx_left,y          ; the pixels from x r0
        eor VERA_DATA0
        sta VERA_DATA0
        lda #$10                ; increment 1
        sta VERA_ADDR_H
        lda VERA_DATA0          ; the read steps to the next byte
        bit r7
        bmi @fx                 ; FX: 4 bytes a store
@bytes:
        ldy r4+1
        txa
        beq @whole
        iny                     ; X bytes, then Y - 1 runs of 256
@whole:
        tya
        beq @last               ; no bytes between
        lda r7+1
@middle:
        sta VERA_DATA0
        dex
        bne @middle
        dey
        bne @middle
@last:
        stz VERA_ADDR_H         ; no increment; the address write fetches the byte again
        lda r7+1
        eor VERA_DATA0
        and r5
        eor VERA_DATA0
        sta VERA_DATA0
        rts
@one:
        lda gfx_left,y
        and r5
        sta r5
        bra @last
@fx:
        lda VERA_ADDR_L         ; r5+1 = the bytes up to a 4-byte boundary
        eor #$FF
        inc a
        and #3
        sta r5+1
        txa                     ; A:Y = the bytes after them
        sec
        sbc r5+1
        tay
        lda r4+1
        sbc #0
        bcc @bytes              ; fewer bytes than that
        lsr a                   ; A = the groups of 4
        tya
        ror a
        lsr a
        beq @bytes              ; none
        tax
        tya
        and #3
        sta r4                  ; the bytes after the groups
        ldy r5+1
        beq @groups
        lda r7+1
@head:
        sta VERA_DATA0
        dey
        bne @head
@groups:
        lda #$30                ; increment 4
        sta VERA_ADDR_H
        lda #2 << 1             ; DCSEL 2: FX_CTRL
        sta VERA_CTRL
        lda #$40                ; cache write: a store puts the 4 bytes of the cache
        sta VERA_FX_CTRL
@group:
        stz VERA_DATA0          ; the nibble mask: every nibble
        dex
        bne @group
        stz VERA_FX_CTRL
        stz VERA_CTRL
        lda #$10                ; increment 1
        sta VERA_ADDR_H
        ldx r4                  ; the bytes after, byte by byte
        stz r4+1
        jmp @bytes

; gfx_circle: draws the circle about x r0, y r1 with radius r2 in color A, in the ranges of
; gfx_clear. Out of contract on screen 0 or with a pixel off the bitmap. Changes A, X, Y and r4
; to r7.
gfx_circle:
        jsr gfx_spread
        sta r7+1                ; the color in every pixel of a byte
        lda r0                  ; r4 = the center's x, r5 its y
        sta r4
        lda r0+1
        sta r4+1
        lda r1
        sta r5
        lda r2                  ; r5+1 = x, from the radius; r7 = y, from 0
        sta r5+1
        stz r7
        lda #1                  ; r6 = the error, 1 - the radius
        sec
        sbc r2
        sta r6
        lda #0
        sbc #0
        sta r6+1
@step:
        jsr @eight
        inc r7
        ldy r6+1                ; Y bit 7: the error was below 0
        lda r7                  ; the error + 2y + 1
        sec
        rol a
        clc
        adc r6
        sta r6
        bcc @sign
        inc r6+1
@sign:
        tya
        bmi @more
        dec r5+1                ; x - 1, and the error - 2x
        lda r5+1
        asl a
        eor #$FF
        sec
        adc r6
        sta r6
        bcs @more
        dec r6+1
@more:
        lda r5+1                ; on while x >= y; radius 0 makes x -1
        sec
        sbc r7
        bpl @step
        lda r4
        sta r0
        lda r4+1
        sta r0+1
        lda r5
        sta r1
        clc
        rts
; @eight: plots the 8 points of x r5+1, y r7.
@eight:
        jsr @four
        jsr @swap
        jsr @four
@swap:
        lda r5+1
        ldx r7
        sta r7
        stx r5+1
        rts
; @four: plots the center's x +- r5+1 at the center's y +- r7.
@four:
        lda r5
        clc
        adc r7
        sta r1
        jsr @two
        lda r5
        sec
        sbc r7
        sta r1
; @two: plots the center's x +- r5+1 at y r1.
@two:
        lda r4
        clc
        adc r5+1
        sta r0
        lda r4+1
        adc #0
        sta r0+1
        lda r7+1
        jsr gfx_plot
        lda r4
        sec
        sbc r5+1
        sta r0
        lda r4+1
        sbc #0
        sta r0+1
        lda r7+1
        jmp gfx_plot

; gfx_char: draws the glyph of character r2, 0 to 255, from the font at CHARSET, with its top
; left at x r0, y r1. Its set bits take color A, in the ranges of gfx_clear; its clear bits keep
; the bitmap's pixels. Returns r0 = x + 8, for the next character. Out of contract on screen 0
; or with the glyph off the bitmap. Changes A, X, Y and r4 to r6.
;
; Trap: data port 1 holds the glyph's address through the rows; an IRQ that moved port 1 would
; break the glyph.
gfx_char:
        jsr gfx_spread
        sta r6+1                ; the color in every pixel of a byte
        lda #1                  ; ADDRSEL 1: data port 1 at CHARSET + the code times 8
        sta VERA_CTRL
        lda r2
        asl a
        asl a
        asl a
        sta VERA_ADDR_L
        lda r2
        lsr a
        lsr a
        lsr a
        lsr a
        lsr a
        .assert <CHARSET = 0 && (>CHARSET & 7) = 0, error, "gfx_char ORs the code into CHARSET"
        ora #>CHARSET
        sta VERA_ADDR_M
        lda #^CHARSET | $10     ; increment 1
        sta VERA_ADDR_H
        stz VERA_CTRL
        lda r0                  ; r4 = the left x
        sta r4
        lda r0+1
        sta r4+1
        lda #8                  ; r5 = the rows left
        sta r5
@row:
        lda VERA_DATA1          ; r5+1 = the row's bits, the left pixel in bit 7
        sta r5+1
        lda r4
        sta r0
        lda r4+1
        sta r0+1
@bit:
        asl r5+1
        bcc @next
        lda r6+1
        jsr gfx_plot
@next:
        inc r0
        bne @more
        inc r0+1
@more:
        lda r5+1                ; on while a set bit is left
        bne @bit
        inc r1
        dec r5
        bne @row
        lda r1                  ; r1 back to the top
        sec
        sbc #8
        sta r1
        lda r4
        clc
        adc #8
        sta r0
        lda r4+1
        adc #0
        sta r0+1
        clc
        rts

; gfx_swap: swaps r0 and r2. Changes X and Y.
gfx_swap:
        ldx r0
        ldy r2
        stx r2
        sty r0
        ldx r0+1
        ldy r2+1
        stx r2+1
        sty r0+1
        rts

; gfx_spread: A = color A in every pixel of a byte at the depth of layer 0. Returns Y =
; L0_CONFIG. Changes X.
gfx_spread:
        ldy VERA_L0_CONFIG      ; $05 2 bpp, $06 4 bpp, $07 8 bpp
        cpy #$07
        beq @done               ; 8 bpp: the color is the byte
        cpy #$06
        beq @nibble
        tax
        lda gfx_nibble,x        ; 2 bpp: the color in both pixels of a nibble
@nibble:
        pha                     ; the nibble in both halves of the byte
        asl a
        asl a
        asl a
        asl a
        tsx
        ora $0101,x
        plx
@done:
        rts

; gfx_at: points data port 0 at the byte of the pixel at x r0, y r1, with no increment. Returns
; Y = the pixel's place in gfx_mask and gfx_shift. Changes A and X.
gfx_at:
        ldx r1                  ; VERA_ADDR_M:A = y times 160
        lda gfx_row_high,x
        sta VERA_ADDR_M
        txa
        and #7
        tax
        lda gfx_row_low,x
        ldy VERA_L0_CONFIG
        cpy #$07
        bne @row
        asl a                   ; times 320 on screen 3
        rol VERA_ADDR_M
@row:
        sta VERA_ADDR_L
        lda r0+1                ; X:A = the byte in the row
        cpy #$07
        beq @eight
        lsr a                   ; carry: x bit 8
        lda r0
        ror a                   ; x / 2, below 160 on screen 2
        cpy #$06
        beq @four
        ldx r0+1
        cpx #2                  ; carry: x bit 9
        ror a                   ; x / 4
@four:
        ldx #0
        bra @add
@eight:
        tax
        lda r0
@add:
        clc
        adc VERA_ADDR_L
        sta VERA_ADDR_L
        txa
        adc VERA_ADDR_M
        sta VERA_ADDR_M
        stz VERA_ADDR_H         ; bit 16 0, no increment
        lda r0
        and gfx_place_and - $05,y
        ora gfx_place_or - $05,y
        tay
        rts

; By L0_CONFIG, $05 to $07: the pixel's place is x AND gfx_place_and OR gfx_place_or.
gfx_place_and:
        .byte 3, 1, 0
gfx_place_or:
        .byte 0, 4, 6
; By place: the pixel's bits in its byte, and the shift that brings them down to bit 0.
gfx_mask:
        .byte $C0, $30, $0C, $03, $F0, $0F, $FF
gfx_shift:
        .byte 6, 4, 2, 0, 4, 0, 0
; By place: the pixels of the byte from the pixel on, and up to it.
gfx_left:
        .byte $FF, $3F, $0F, $03, $FF, $0F, $FF
gfx_right:
        .byte $C0, $F0, $FC, $FF, $F0, $FF, $FF
gfx_nibble:
        .byte $0, $5, $A, $F
; By y: the address of row y at 160 bytes a row. The low byte repeats every 8 rows.
        .assert BITMAP = 0, error, "gfx_row_low and _high need BITMAP at $00000"
gfx_row_low:
        .repeat 8, I
        .byte <(I * 160)
        .endrepeat
gfx_row_high:
        .repeat 240, I
        .byte >(I * 160)
        .endrepeat
