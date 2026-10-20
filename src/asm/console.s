; The console: text on VERA layer 1, keys from the SMC.
;
; The screen is 80 columns by 30 rows of the CP437 font, in colour con_colour. con_out obeys CR,
; LF, BS, TAB, BEL and FF, skips $0F, obeys the ANSI.SYS escape sequences below, and shows every
; other byte as its glyph. CR moves to the start of the next line, and an LF right after a CR
; does nothing: CR, LF and CR LF each end a line, as the stock KERNAL's CR does. The screen
; scrolls in hardware: screen row 0 is map row con_top, and a scroll moves con_top and blanks one
; row.
;
; An escape sequence is Esc [, up to ANSI_PARAMS decimal parameters split by ;, then a final
; byte. A missing parameter is 0. Rows and columns count from 1.
;   Esc[r;cH            the cursor to row r, column c; 0 means 1, and past the edge means the
;                       last
;   Esc[2J              clear the screen and put the cursor home
;   Esc[K               blank from the cursor to the end of the line
;   Esc[...m            0 the colour api_con_colour last set; 7 swaps the foreground and the
;                       background, so a second 7 swaps them back; 30 to 37 the foreground; 40
;                       to 47 the background
; The colours are black, red, green, yellow, blue, magenta, cyan and white, in the X16 palette
; entries of ansi_colours. Other final bytes, other parameters, and the bytes $30 to $3F other
; than digits and ; do nothing. Esc then a byte other than [ shows that byte.
; Checklist: a sequence added or removed here changes lib/CONS.UXI, LX_TAGS in
; UXCBASIC/pyuxc/uxc_lex.py, con_out in tools/api.py, and tests/ANSI.S.
; Keys come from the keyboard queue in RAM bank 0, then from the SMC keycode register in a US
; layout. An extended key, an arrow, Home, End, PgUp, PgDn, Insert, Delete or F1 to F10, gives
; two characters, as in MS-DOS: 0, then its IBM PC scan code. In the queue, KBD_EXTENDED then a
; scan code is an extended key.

.setcpu "65C02"

.include "mem.inc"
.include "api.inc"

.export con_init, api_con_line, api_con_edit, api_con_screen, api_con_status, api_con_out, api_con_in, api_con_cursor
.export api_con_getkey
.export api_con_colour, api_con_break
.export CHRIN, CHROUT
.import font, i2c_read_byte, sft_find, bank_restore, api_read, exec_break
.importzp ticks

COLUMNS       = 80
ROWS          = 30
MAP_ROWS      = 64
CON_COLOUR    = $05             ; at boot: background 0 black, foreground 5 green
BLINK         = 30              ; frames between cursor blinks

; kbd_mods bits
MOD_SHIFT     = $01             ; bit 0: kbd_get shifts it into carry
MOD_CAPS      = $04
MOD_ALT       = $40             ; bit 6: kbd_get tests it with V
MOD_CTRL      = $80             ; bit 7: kbd_get tests it with N

KEY_1         = $02             ; the keycodes 1 to 0, - and = run KEY_1 to KEY_EQUALS
KEY_EQUALS    = $0D
KEY_Z_ROW     = $2D             ; the first keycode past the A row
KEY_CAPSLOCK  = $1E
KEY_SPACE     = $3D             ; the last keycode in kbd_lower and kbd_upper
KEY_F1        = $70             ; F1 to F10 are keycodes KEY_F1 to KEY_F1 + 9
SCAN_F1       = $3B             ; F1 to F10 are scan codes SCAN_F1 to SCAN_F1 + 9
SCAN_ALT_1    = $78             ; Alt+1 to Alt+= are scan codes SCAN_ALT_1 to SCAN_ALT_1 + 11
EXTENDED      = $80             ; in kbd_special_chars: the low 7 bits are a scan code
KBD_EXTENDED  = $E0             ; in KBD_QUEUE: the scan code of an extended key comes next, as the
                                ; IBM PC BIOS gives the grey keys; x16emu -bas pastes \XE0\X48 as Up.
                                ; Trap: -bas ends the paste at \X00, so 0 cannot be the prefix
ANSI_ESC      = 1               ; ansi_state after Esc
ANSI_CSI      = 2               ; ansi_state after Esc [
ANSI_PARAMS   = 4               ; the parameters kept; more add into the last

.segment "KERNELZP" : zeropage

con_row:      .res 1            ; the cursor's screen row, 0 to ROWS - 1
con_col:      .res 1            ; the cursor's column, 0 to COLUMNS - 1
con_top:      .res 1            ; the map row shown on screen row 0
con_key:      .res 1            ; the character con_status read, 0 when none
con_scan:     .res 1            ; the scan code of an extended key before its 0, 0 when none
con_cursor:   .res 1            ; bit 0 set while the cursor shows
con_blink:    .res 1            ; the low byte of ticks at the last blink
kbd_mods:     .res 1            ; MOD_ bits
pointer:      .res 2            ; con_init: the font; api_con_line: the buffer
con_limit:    .res 1            ; api_con_line: the buffer offset of the last character, then the end key
con_end_key:  .res 1            ; api_con_line: $09 when Tab ends the line, $FF in api_con_screen, else $0D
con_after_cr: .res 1            ; 1 when the last byte written was CR
con_colour:   .res 1            ; the colour of new cells: background high nibble, foreground low
ansi_state:   .res 1            ; 0, ANSI_ESC after Esc, ANSI_CSI after Esc [

.segment "KERNELRAM"

con_default:  .res 1            ; the colour Esc[0m sets: the one api_con_colour last set
con_broke:    .res 1            ; 1 when Ctrl+C came in BREAK_CATCH since api_con_break's last get
ansi_count:   .res 1            ; the index of the parameter being read
ansi_params:  .res ANSI_PARAMS  ; the parameters, each modulo 256
scr_row:      .res 1            ; api_con_screen: the row and column the line started at
scr_col:      .res 1
scr_insert:   .res 1            ; api_con_screen: bit 7 set in insert mode

.segment "CODE"

; con_init: sets up VERA, loads the font and clears the screen. Changes A, X and Y.
con_init:
        stz VERA_CTRL           ; trap: bit 7 resets VERA, so never write it set here
        .assert <PALETTE = 0, error, "stz VERA_ADDR_L needs PALETTE on a page boundary"
        stz VERA_ADDR_L
        lda #>PALETTE
        sta VERA_ADDR_M
        lda #$10 | ^PALETTE     ; increment 1
        sta VERA_ADDR_H
        stz VERA_DATA0          ; entry 0 black: green and blue 0
        stz VERA_DATA0          ; red 0
        lda #$80                ; 1 to 1 across
        sta VERA_DC_HSCALE
        lsr a                   ; 2 to 1 down: 640 by 240
        sta VERA_DC_VSCALE
        stz VERA_DC_BORDER
        stz con_broke
        lda #$60                ; map 64 rows by 128 columns, 1 bpp tiles
        sta VERA_L1_CONFIG
        lda #SCREEN_MAP >> 9
        sta VERA_L1_MAPBASE
        lda #CHARSET >> 11 << 2 ; 8 by 8 tiles
        sta VERA_L1_TILEBASE
        stz VERA_L1_HSCROLL_L
        stz VERA_L1_HSCROLL_H
        .assert <CHARSET = 0, error, "stz VERA_ADDR_L needs CHARSET on a page boundary"
        stz VERA_ADDR_L
        lda #>CHARSET
        sta VERA_ADDR_M
        lda #$10 | ^CHARSET
        sta VERA_ADDR_H
        lda #<font
        sta pointer
        lda #>font
        sta pointer+1
        ldx #8                  ; pages: 256 glyphs of 8 bytes
        ldy #0
@font:
        lda (pointer),y
        sta VERA_DATA0
        iny
        bne @font
        inc pointer+1
        dex
        bne @font
        lda #$21                ; VGA output, layer 1 on
        sta VERA_DC_VIDEO
        lda #CON_COLOUR
        sta con_colour
        sta con_default
        ; fall through

; clear: blanks the whole map and puts the cursor home. Changes A, X and Y.
clear:
        stz con_top
        jsr vscroll
        stz con_row
        stz con_col
        ldx #0
        ldy #0
        jsr point
        ldy #MAP_ROWS * 128 / 256
@page:
        jsr blank               ; X = 0: 256 cells
        dey
        bne @page
        rts

; con_out: writes the byte in A to the screen. Keeps A, X and Y.
con_out:
        pha
        phx
        phy
        jsr write
        ply
        plx
        pla
        rts

write:
        ldx ansi_state
        bne @ansi
        cmp #$0A
        beq @lf
        stz con_after_cr
        cmp #$0F                ; the stock KERNAL's switch to ISO mode
        beq @done
        cmp #$0E
        bcs @glyph
        cmp #$0D
        beq cr
        cmp #$08
        beq bs
        cmp #$09
        beq tab
        cmp #$0C
        beq clear
        cmp #$07                ; BEL: no sound yet
        bne put
@done:
        rts
@ansi:
        jmp ansi
@lf:
        lsr con_after_cr        ; and clears it
        bcc lf
        rts
@glyph:
        cmp #$1B
        bne put
        inc ansi_state          ; ANSI_ESC
        rts

cr:
        stz con_col
        inc con_after_cr        ; 0 before: write cleared it
        bra lf

bs:
        lda con_col
        beq @done
        dec con_col
@done:
        rts

tab:
        lda #' '
        jsr put
        lda con_col
        and #7
        bne tab
        rts

; put: shows the glyph of A at the cursor and moves the cursor on, to the next line after the
; last column.
put:
        pha
        ldx con_row
        ldy con_col
        jsr point
        pla
        sta VERA_DATA0
        lda con_colour
        sta VERA_DATA0
        inc con_col
        lda con_col
        cmp #COLUMNS
        bne @done
        stz con_col
        bra lf
@done:
        rts

lf:
        lda con_row
        cmp #ROWS - 1
        beq @scroll
        inc con_row
        rts
@scroll:
        lda con_top
        inc
        and #MAP_ROWS - 1
        sta con_top
        jsr vscroll
        ldx #ROWS - 1
        ldy #0
        jsr point
        ldx #COLUMNS
        ; fall through

; blank: writes X blank cells, 256 when X is 0, at the VERA address. Returns X = 0.
blank:
        lda #' '
        sta VERA_DATA0
        lda con_colour
        sta VERA_DATA0
        dex
        bne blank
        rts

; vscroll: shows map row con_top on screen row 0. Changes A.
vscroll:
        lda con_top
        asl
        asl
        asl                     ; carry = bit 5 of con_top
        sta VERA_L1_VSCROLL_L
        lda #0
        rol
        sta VERA_L1_VSCROLL_H
        rts

; point: points VERA data port 0 at the cell of screen row X, column Y, increment 1.
; Changes A.
point:
        .assert <SCREEN_MAP = 0 && >SCREEN_MAP = 0, error, "point needs SCREEN_MAP at $x0000"
        txa
        clc
        adc con_top
        and #MAP_ROWS - 1
        sta VERA_ADDR_M         ; a map row is 256 bytes
        tya
        asl
        sta VERA_ADDR_L
        lda #$10 | ^SCREEN_MAP
        sta VERA_ADDR_H
        rts

; ansi: obeys byte A of an escape sequence, X = ansi_state.
ansi:
        cpx #ANSI_CSI
        beq @csi
        cmp #'['
        beq @open
        stz ansi_state
        jmp write               ; drop the Esc
@open:
        inc ansi_state          ; ANSI_CSI
        ldx #ANSI_PARAMS
@clear:
        stz ansi_count,x        ; ansi_count and ansi_params
        dex
        bpl @clear
        rts
@csi:
        eor #'0'
        cmp #10
        bcc @digit
        cmp #';' ^ '0'
        beq @next
        eor #'0'
        cmp #'@'
        bcc @done               ; a parameter byte
        stz ansi_state          ; the final byte
        cmp #'m'
        beq @sgr
        cmp #'K'
        beq @erase_line
        cmp #'J'
        beq @erase_screen
        cmp #'H'
        bne @done
        ldx #1                  ; the locate: the column, then the row
@axis:
        lda ansi_params,x
        beq @first              ; 0 means 1
        dec
@first:
        cmp ansi_last,x
        bcc @store
        lda ansi_last,x
@store:
        .assert con_col = con_row + 1, error, "ansi needs con_col right after con_row"
        sta con_row,x
        dex
        bpl @axis
@done:
        rts
@erase_line:
        ldx con_row
        ldy con_col
        jsr point
        lda #COLUMNS
        sec
        sbc con_col
        tax
        jmp blank
@erase_screen:
        lda ansi_params
        cmp #2
        bne @done
        jmp clear
@digit:                         ; the parameter times 10, plus A
        pha
        ldx ansi_count
        lda ansi_params,x
        asl
        asl
        adc ansi_params,x
        asl
        sta ansi_params,x
        pla
        adc ansi_params,x
        sta ansi_params,x
        rts
@next:
        lda ansi_count
        cmp #ANSI_PARAMS - 1
        bcs @done
        inc ansi_count
        rts
@sgr:                           ; each parameter in turn
        ldx #$FF
@each:
        inx
        lda ansi_params,x
        beq @reset
        cmp #7
        beq @reverse
        sec
        sbc #30
        cmp #8
        bcc @foreground
        sbc #10                 ; carry set
        cmp #8
        bcs @after
        tay
        lda ansi_colours,y
        asl
        asl
        asl
        asl
        eor con_colour
        and #$F0
        bra @merge
@reset:
        lda con_default
        bra @color
@reverse:
        lda con_colour
        asl                     ; swap the nibbles
        adc #$80
        rol
        asl
        adc #$80
        rol
        bra @color
@foreground:
        tay
        lda ansi_colours,y
        eor con_colour
        and #$0F
@merge:
        eor con_colour
@color:
        sta con_colour
@after:
        cpx ansi_count
        bcc @each
        rts

; cursor_flip: shows or hides the cursor by swapping the nibbles of its cell's colour. A cell
; whose two nibbles match shows no cursor. Changes A, X and Y.
cursor_flip:
        inc con_cursor
        ldx con_row
        ldy con_col
        jsr point
        inc VERA_ADDR_L         ; the colour byte
        lda #^SCREEN_MAP        ; increment 0
        sta VERA_ADDR_H
        lda VERA_DATA0
        asl                     ; swap the nibbles
        adc #$80
        rol
        asl
        adc #$80
        rol
        sta VERA_DATA0
        rts

; con_in: waits for a key and returns its character in A. The cursor blinks while it waits.
; In api_con_screen a Ctrl+C that con_status caught returns 0 with con_scan 0. Changes X and Y.
con_in:
        jsr cursor_flip
        lda ticks
        sta con_blink
@wait:
        jsr con_status
        bne @key
        bit con_end_key
        bpl @blink
        lda con_broke
        bne @key
@blink:
        lda ticks
        sec
        sbc con_blink
        cmp #BLINK
        bcc @wait
        lda ticks
        sta con_blink
        jsr cursor_flip
        bra @wait
@key:
        lda con_cursor
        lsr
        bcc @hidden
        jsr cursor_flip
@hidden:
        lda con_key             ; 0 for an extended key
        ldx con_scan            ; its scan code comes next
        stx con_key
        stz con_scan
        rts

; con_status: returns A nonzero with Z clear when a character waits, or A = 0 with Z set when
; none waits. The character stays waiting for con_in. Ctrl+C obeys PSP_BREAK: BREAK_END does
; not return, BREAK_CATCH drops it and sets con_broke. Changes X and Y.
con_status:
        lda con_key
        ora con_scan
        bne @done
        php
        sei                     ; x16emu pastes only while I is clear
        ldx RAM_BANK
        stz RAM_BANK
        lda KBD_COUNT
        beq @smc
        ldy KBD_QUEUE
        cpy #KBD_EXTENDED
        bne @plain
        cmp #2                  ; the scan code of an extended key follows
        lda #0
        bcc @queued             ; the scan code is not in yet
        jsr kbd_pop
        jsr kbd_pop
        sta con_scan
        lda #0
        bra @queued
@plain:
        jsr kbd_pop
@queued:
        stx RAM_BANK
        plp
        bra @key
@smc:
        stx RAM_BANK
        plp
        jsr kbd_get
@key:
        cmp #$03                ; Ctrl+C
        beq @break
@store:
        sta con_key
        ora con_scan            ; kbd_get sets con_scan for an extended key
@done:
        rts
@break:
        ldx PSP_BREAK
        beq @store              ; BREAK_OFF: a character
        dex
        bne @catch
        jmp exec_break          ; BREAK_END
@catch:
        stx con_broke           ; X = 1
        lda #0                  ; no character
        rts
        .assert BREAK_OFF = 0 && BREAK_END = 1 && BREAK_CATCH = 2, error, "con_status counts the modes with dex"

; kbd_pop: takes the oldest character of KBD_QUEUE into A, with RAM bank 0 set. Changes Y.
kbd_pop:
        dec KBD_COUNT
        lda KBD_QUEUE
        pha
        ldy #0
@shift:
        lda KBD_QUEUE+1,y
        sta KBD_QUEUE,y
        iny
        cpy #KBD_QUEUE_SIZE - 1
        bne @shift
        pla
        rts

; api_con_break: with carry set returns PSP_BREAK in A and con_broke in X, and clears con_broke.
; With carry clear sets PSP_BREAK to A, a BREAK_ mode, else returns ERR_BAD_DATA.
api_con_break:
        bcc @set
        lda PSP_BREAK
        ldx con_broke
        stz con_broke
        clc
        rts
@set:
        cmp #BREAK_CATCH + 1
        bcs @bad
        sta PSP_BREAK
        rts                     ; carry clear
@bad:
        lda #ERR_BAD_DATA       ; carry set
        rts

; api_con_cursor: with carry set returns the cursor's row in X and column in Y, and the screen's
; rows in r0L and columns in r0H. With carry clear moves the cursor to row X, below ROWS, and
; column Y, below COLUMNS. Returns carry clear.
api_con_cursor:
        bcc @move
        lda #ROWS
        sta r0
        lda #COLUMNS
        sta r0+1
        ldx con_row
        ldy con_col
        clc
        rts
@move:
        stx con_row
        sty con_col
        rts

; api_con_colour: with carry set returns con_colour in A. With carry clear sets con_colour to A,
; for the cells written from now on. Returns carry clear.
api_con_colour:
        bcc @set
        lda con_colour
        clc
        rts
@set:
        sta con_colour
        sta con_default
        rts

; api_con_out and api_con_in go through CHROUT and CHRIN, so x16emu's -echo shows the character
; and -bas types the key.
api_con_out:
        jsr CHROUT
        clc
        rts

api_con_in:
        jsr CHRIN
        clc
        rts

; api_con_status: returns A = $FF when a character waits, else 0, and kbd_mods in X: MOD_SHIFT,
; MOD_ALT and MOD_CTRL while held, MOD_CAPS while Caps Lock is on. Returns carry clear.
api_con_status:
        jsr con_status
        beq @none
        lda #$FF
@none:
        ldx kbd_mods
        clc
        rts

; api_con_getkey: with carry clear waits for a key, the cursor blinking; with carry set returns
; at once. Returns the character in A, 0 for an extended key or for none; the scan code in X,
; 0 for any other key or for none; kbd_mods in Y. Returns carry clear.
api_con_getkey:
        bcc @wait
        jsr con_status
        bne @wait               ; a key waits: con_in takes it at once
        tax                     ; no key: A = 0
        bra @mods
@wait:
        jsr CHRIN               ; X = con_scan, which con_in moved to con_key
        stz con_key
@mods:
        ldy kbd_mods
        clc
        rts

; api_con_edit: r0 = the buffer: the most characters, CR included, then the length of the text
; kept from offset 2, which is shown and edited; 0 for an empty line. Enter, Tab or an extended
; key ends the line. Sets the length, and a CR after the text. Returns as api_con_getkey does:
; the key that ended the line in A, $0D, $09 or 0 for an extended key; its scan code in X, 0 for
; Enter and Tab; kbd_mods in Y. Returns carry clear.
; api_con_line: api_con_edit of an empty line; Tab and the extended keys are dropped.
; When handle 0 is a file, both read the line from it without echo, from offset 2. They skip
; LF and drop the characters past the most; the end of the file ends the line.
; Trap: keys come through CHRIN, $FFCF, and the echo through CHROUT, so x16emu -bas pastes
; and -echo shows them.
api_con_edit:
        lda #$09                ; Tab ends the line too
        bra con_read
api_con_line:
        ldy #1
        lda #0
        sta (r0),y              ; no kept text
        lda #$0D                ; Enter alone: the compare with Enter comes first
con_read:
        sta con_end_key
        lda (r0)                ; the most characters, CR included
        sta con_limit
        inc con_limit           ; the offset of the last CR
        jsr con_file
        bpl @file
        ldy #1
        lda (r0),y
        tax                     ; X = the kept characters left to show
        iny
@show:
        txa
        beq @key
        lda (r0),y
        jsr CHROUT              ; keeps A, X and Y
        iny
        dex
        bra @show
@key:
        phy
        jsr CHRIN               ; changes X and Y
        ply
        cmp #$0D
        beq @end
        cmp con_end_key
        beq @tab
        cmp #$08
        beq @back
        cmp #' '
        bcs @text
        tax
        bne @key                ; another control character
        phy                     ; 0: the scan code of the extended key comes next
        jsr CHRIN
        ply
        ldx con_end_key
        cpx #$0D
        beq @key                ; api_con_line drops it
        tax
        lda #0
        bra @done
@text:
        cpy con_limit
        bcs @key                ; full
        sta (r0),y
        jsr CHROUT
        iny
        bra @key
@back:
        cpy #2
        beq @key
        dey
        jsr CHROUT
        lda #' '
        jsr CHROUT
        lda #$08
        jsr CHROUT
        bra @key
@end:
        jsr CHROUT              ; keeps A, X and Y
        lda #$0A
        jsr CHROUT
        lda #$0D
@tab:
        ldx #0                  ; no scan code
@done:                          ; A = the key that ended the line, X = its scan code, Y = the offset after the text
        sta con_limit
        lda #$0D
        sta (r0),y
        dey
        dey
        tya
        ldy #1
        sta (r0),y
        lda con_limit
        ldy kbd_mods
        clc
        rts

@file:
        lda r0
        sta pointer
        lda r0+1
        sta pointer+1
        lda #1                  ; api_read leaves r1 = 1 until the end of the file
        sta r1
        stz r1+1
        ldy #2
@byte:                          ; reads one byte to offset Y of the buffer
        phy
        tya
        clc
        adc pointer
        sta r0
        lda pointer+1
        adc #0
        sta r0+1
        ldx #0
        jsr api_read
        ply
        bcs @last               ; an error ends the line
        lda r1
        beq @last               ; the end of the file
        lda (pointer),y
        cmp #$0D
        beq @last
        cmp #$0A
        beq @byte
        cpy con_limit
        bcs @byte               ; full
        iny
        bra @byte
@last:
        lda pointer
        sta r0
        lda pointer+1
        sta r0+1
        lda #$0D
        bra @tab

; con_file: returns N clear when handle 0 is a file, N set when it is a device or closed. Changes
; A, X and Y.
con_file:
        ldx #0
        jsr sft_find
        bcs @closed
        ldx SFT + SFT_FLAGS,y   ; bit 7 set for a device
        jsr bank_restore
        txa
        rts
@closed:
        lda #$FF
        rts

; api_con_screen: r0 = the buffer, as api_con_line takes it. When handle 0 is a file, it is
; api_con_line. From the keys it is the full-screen editor of GW-BASIC. The cursor moves over the
; whole screen, and Enter returns the text of its row, without the blanks at the end. On the row
; the call started at, the text starts at the column it started at, past a prompt; on any other
; row at column 0. A Ctrl+C caught in BREAK_CATCH ends the line with no text. A line is one row:
; typing in the last column stays there. Returns A = $0D and carry clear.
; Trap: only typed characters, Backspace and the end of the line go through CHROUT; -echo shows
; nothing of the other edits.
api_con_screen:
        jsr con_file
        bmi @screen
        jmp api_con_line
@screen:
        lda #$FF                ; con_in returns on a caught Ctrl+C
        sta con_end_key
        lda (r0)
        inc
        sta con_limit           ; the offset of the last CR
        lda con_row
        sta scr_row
        lda con_col
        sta scr_col
        stz scr_insert
@key:
        jsr CHRIN               ; A = the character, X = the scan code of an extended key
        stz con_key
        cmp #' '
        bcs @text
        cmp #$0D
        beq @enter
        tay
        bne @control
        txa
        beq @broke              ; neither: a caught Ctrl+C
@control:                       ; A = a control character or a scan code
        ldy #scr_keys_end - scr_keys - 1
@find:
        cmp scr_keys,y
        beq @found
        dey
        bpl @find
        bra @key
@found:
        cpy #SCR_KEEP_INSERT
        bcc @keep
        stz scr_insert          ; a cursor move ends insert mode
@keep:
        tya
        asl
        tax
        jsr @run
        bra @key
@run:
        jmp (scr_jumps,x)
@text:
        bit scr_insert
        bpl @over
        pha
        ldy con_col
        jsr scr_open
        pla
@over:
        ldy con_col
        cpy #COLUMNS - 1
        beq @last
        jsr CHROUT              ; shows it and moves on
        bra @key
@last:
        pha
        ldx con_row
        jsr point
        pla
        sta VERA_DATA0
        lda con_colour
        sta VERA_DATA0
        bra @key
@broke:
        stz pointer+1           ; no text
        bra @copied
@enter:
        jsr scr_start           ; A = the first column
        sta pointer
        jsr scr_end             ; Y = the column after the text
        tya
        sec
        sbc pointer
        bcs @length
        lda #0                  ; the row is blank from the first column
@length:
        ldx con_limit
        dex
        dex                     ; X = the most characters
        stx pointer+1
        cmp pointer+1
        bcs @copy
        sta pointer+1           ; the count
@copy:
        ldx con_row
        ldy pointer
        jsr point
        lda #$20 | ^SCREEN_MAP  ; increment 2: the characters only
        sta VERA_ADDR_H
        ldy #2
        ldx pointer+1
        beq @copied
@char:
        lda VERA_DATA0
        sta (r0),y
        iny
        dex
        bne @char
@copied:
        lda pointer+1
        ldy #1
        sta (r0),y
        tay
        iny
        iny
        lda #$0D
        sta (r0),y
        jsr CHROUT              ; the cursor to the next row
        lda #$0A
        jsr CHROUT
        stz con_end_key         ; con_in checks it
        lda #$0D
        clc
        rts

; The editor's keys. scr_jumps holds a routine for each, in the same order. The first
; SCR_KEEP_INSERT keep insert mode on. Each routine may change A, X and Y.
SCR_KEEP_INSERT = 4
.segment "RODATA"
scr_keys:
        .byte $52, $53, $08, $09                ; Ins, Del, Backspace, Tab
        .byte $1B, $48, $50, $4B, $4D           ; Esc, Up, Down, Left, Right
        .byte $47, $4F, $77, $75, $73, $74      ; Home, End, Ctrl+Home, Ctrl+End, Ctrl+Left, Ctrl+Right
scr_keys_end:
scr_jumps:
        .word scr_ins, scr_del, scr_back, scr_tab
        .word scr_esc, scr_up, scr_down, scr_left, scr_right
        .word scr_home, scr_end_key, scr_clear, scr_erase, scr_word_left, scr_word_right
        .assert * - scr_jumps = 2 * (scr_keys_end - scr_keys), error, "scr_jumps needs a routine a key"
.segment "CODE"

scr_ins:
        lda scr_insert
        eor #$80
        sta scr_insert
        rts

scr_del:
        ldy con_col
        bra scr_close

scr_back:                       ; not past the first column
        jsr scr_start
        cmp con_col
        bcs scr_done
        lda #$08
        jsr CHROUT              ; the cursor one left
        ldy con_col
        ; fall through

; scr_close: moves the cells of the cursor's row right of column Y one left, and blanks the last
; column. Changes A, X and Y.
scr_close:
        lda #1                  ; ADDRSEL: port 1 writes
        sta VERA_CTRL
        ldx con_row
        jsr point
        stz VERA_CTRL
        iny
        jsr point
@cell:
        cpy #COLUMNS
        beq @last
        lda VERA_DATA0
        sta VERA_DATA1
        lda VERA_DATA0
        sta VERA_DATA1
        iny
        bra @cell
@last:
        lda #' '
        sta VERA_DATA1
        lda con_colour
        sta VERA_DATA1
        rts


scr_tab:                        ; to the next column of 8; insert mode opens blanks
        bit scr_insert
        bpl @move
        ldy con_col
        jsr scr_open
@move:
        jsr scr_right
        bcs scr_done            ; the last column
        lda con_col
        and #7
        bne scr_tab
        rts

scr_esc:                        ; blanks the row from the first column
        jsr scr_start
        sta con_col
        ; fall through
scr_erase:                      ; blanks from the cursor to the end of the row: Esc[K
        ldx #ANSI_CSI
        lda #'K'
        jmp ansi

scr_up:
        lda con_row
        beq scr_done
        dec con_row
        rts

scr_down:
        lda con_row
        cmp #ROWS - 1
        beq scr_done
        inc con_row
        rts

scr_left:
        lda con_col
        beq scr_done
        dec con_col
        rts

; scr_right: the cursor one right. Returns carry set in the last column.
scr_right:
        lda con_col
        cmp #COLUMNS - 1
        bcs scr_done
        inc con_col
scr_done:
        rts

scr_home:
        stz con_row
        stz con_col
        rts

scr_end_key:                    ; after the text, or the last column
        jsr scr_end
        cpy #COLUMNS
        bcc @column
        dey
@column:
        sty con_col
        rts

scr_clear:                      ; the screen, and the line starts at the top
        stz scr_row
        stz scr_col
        jmp clear

scr_word_left:                  ; to the start of the word on the left, or column 0
        ldy con_col
@blank:
        dey
        bmi @start
        jsr scr_cell
        cmp #' '
        beq @blank
@word:
        dey
        bmi @start
        jsr scr_cell
        cmp #' '
        bne @word
@start:
        iny
        sty con_col
        rts

scr_word_right:                 ; to the start of the next word, or the last column
        ldy con_col
@word:
        jsr scr_cell
        cmp #' '
        beq @blank
        iny
        cpy #COLUMNS
        bcc @word
        bra @last
@blank:
        jsr scr_cell
        cmp #' '
        bne @column
        iny
        cpy #COLUMNS
        bcc @blank
@last:
        ldy #COLUMNS - 1
@column:
        sty con_col
        rts

; scr_start: returns in A the first column of the cursor's row: scr_col on the row the line
; started at, else 0. Changes X.
scr_start:
        lda #0
        ldx con_row
        cpx scr_row
        bne @done
        lda scr_col
@done:
        rts

; scr_end: returns in Y the column after the last character but a blank of the cursor's row, 0
; when the row is blank. Changes A and X.
scr_end:
        ldx con_row
        ldy #COLUMNS - 1
        jsr point
        lda #$28 | ^SCREEN_MAP  ; increment 2, down: the characters right to left
        sta VERA_ADDR_H
@back:
        lda VERA_DATA0
        cmp #' '
        bne @found
        dey
        bpl @back
@found:
        iny
        rts

; scr_cell: returns in A the character of the cursor's row at column Y. Changes X.
scr_cell:
        ldx con_row
        jsr point
        lda VERA_DATA0
        rts

; scr_open: moves the cells of the cursor's row from column Y one right, dropping the last, and
; blanks column Y. Changes A, X, Y and pointer.
; Trap: port 0 reads one byte ahead of port 1, so it fetches each byte before port 1 writes it.
scr_open:
        lda #' '
        sta pointer             ; pointer and pointer+1: the cell to write next
        lda con_colour
        sta pointer+1
        lda #1                  ; ADDRSEL: port 1 writes
        sta VERA_CTRL
        ldx con_row
        jsr point
        stz VERA_CTRL
        jsr point
@cell:
        lda VERA_DATA0
        ldx pointer
        stx VERA_DATA1
        sta pointer
        lda VERA_DATA0
        ldx pointer+1
        stx VERA_DATA1
        sta pointer+1
        iny
        cpy #COLUMNS
        bne @cell
        rts

; kbd_get: reads one keycode from the SMC. Returns its character in A, or 0 when there is
; none or the key gives no character. For an extended key returns 0 and sets con_scan to its
; scan code. Keeps track of Shift, Ctrl, Alt and Caps Lock. Alt and Ctrl give the IBM PC BIOS
; codes: Alt+letter, Alt+1 to Alt+= and Ctrl+2 give a scan code, and Ctrl+digit gives nothing
; but Ctrl+6 $1E and Ctrl+- $1F. Changes X and Y.
kbd_get:
        ldx #SMC
        ldy #SMC_KEYCODE
        jsr i2c_read_byte
        bcs @none
        beq @none
        tay                     ; Y = keycode, bit 7 set on release
        and #$7F
        ldx #kbd_mod_bits - kbd_mod_keys - 1
@modifier:
        cmp kbd_mod_keys,x
        beq @mod
        dex
        bpl @modifier
        cpy #$80
        bcs @none               ; another key released
        cmp #KEY_CAPSLOCK
        beq @caps
        cmp #KEY_SPACE + 1
        bcs @special
        tay
        bit kbd_mods
        bvs @alt
        bmi @ctrl
        lda kbd_mods
        and #MOD_CAPS
        beq @shift
        lda kbd_lower-1,y
        cmp #'a'
        bcc @shift              ; kbd_lower holds nothing past 'z'
        lda #MOD_SHIFT          ; Caps Lock swaps Shift on letters
        eor kbd_mods
        bra @pick
@shift:
        lda kbd_mods
@pick:
        lsr                     ; MOD_SHIFT -> C
        lda kbd_lower-1,y
        bcc @done
        lda kbd_upper-1,y
@done:
        rts
@mod:
        lda kbd_mod_bits,x
        cpy #$80
        bcs @release
        tsb kbd_mods
        bra @none
@release:
        trb kbd_mods
        bra @none
@caps:
        lda #MOD_CAPS
        eor kbd_mods
        sta kbd_mods
@none:
        lda #0
        rts
@ctrl:                         ; letters, [ \ ] and Shift's @ ^ _ give control codes
        lda kbd_lower-1,y
        cmp #' ' + 1
        bcc @done               ; a control character or Space stays
        cmp #'['
        bcs @code               ; ` gives 0, so nothing
        lda kbd_upper-1,y
        cmp #'@'
        beq @nul
        cmp #'^'
        bcc @none
@code:
        and #$1F
        rts
@nul:                           ; Ctrl+2: 0 then 3
        lda #3
        bra @extended
@alt:
        tya
        cpy #KEY_EQUALS + 1
        bcs @letter
        cpy #KEY_1
        bcc @none
        adc #SCAN_ALT_1 - KEY_1 - 1 ; carry set
        bra @extended
@letter:
        ldx kbd_lower-1,y
        cpx #'a'
        bcc @none
        dec a                   ; the Q and A rows: keycode - 1
        cpy #KEY_Z_ROW
        bcc @extended
        dec a                   ; the Z row: keycode - 2
        bra @extended
@special:
        cmp #KEY_F1
        bcc @table
        cmp #KEY_F1 + 10
        bcs @table
        ldx #kbd_fkey_bases - kbd_fkey_mods
@fmod:                          ; Alt, then Ctrl, then Shift
        lda kbd_fkey_mods-1,x
        and kbd_mods
        bne @fkey
        dex
        bne @fmod
@fkey:                          ; X = 0 without a modifier
        tya
        adc kbd_fkey_bases,x    ; carry clear
        bra @extended
@table:
        ldx #kbd_special_chars - kbd_special_keys - 1
@find:
        cmp kbd_special_keys,x
        beq @found
        dex
        bpl @find
        bra @none
@found:
        bit kbd_mods
        bpl @plain
        cpx #kbd_ctrl_scans_end - kbd_ctrl_scans
        bcs @plain
        lda kbd_ctrl_scans,x
        bra @extended
@plain:
        lda kbd_special_chars,x
        bpl @code               ; a character, below $20
        and #$7F
@extended:
        sta con_scan
        bra @none

.segment "RODATA"

kbd_mod_keys:
        .byte $2C, $39          ; left and right Shift
        .byte $3A, $40          ; left and right Ctrl
        .byte $3C, $3E          ; left and right Alt
kbd_mod_bits:
        .byte MOD_SHIFT, MOD_SHIFT
        .byte MOD_CTRL, MOD_CTRL
        .byte MOD_ALT, MOD_ALT

; The modifiers F1 to F10 check, the last first, and the scan code of F1 less KEY_F1 with no
; modifier and with each.
kbd_fkey_mods:
        .byte MOD_SHIFT, MOD_CTRL, MOD_ALT
kbd_fkey_bases:
        .byte <(SCAN_F1 - KEY_F1), <($54 - KEY_F1), <($5E - KEY_F1), <($68 - KEY_F1)

; The keycodes past KEY_SPACE that give a character, and their characters. EXTENDED marks a
; scan code. The first keys have the scan codes of kbd_ctrl_scans with Ctrl.
kbd_special_keys:
        .byte $4F, $59, $51, $56, $50, $55      ; Left, Right, End, PgDn, Home, PgUp
        .byte $53, $54                          ; Up, Down
        .byte $4B, $4C                          ; Insert, Delete
        .byte $6E, $6C                          ; Esc, keypad Enter
kbd_special_chars:
        .byte EXTENDED | $4B, EXTENDED | $4D, EXTENDED | $4F, EXTENDED | $51
        .byte EXTENDED | $47, EXTENDED | $49
        .byte EXTENDED | $48, EXTENDED | $50
        .byte EXTENDED | $52, EXTENDED | $53
        .byte $1B, $0D
        .assert * - kbd_special_chars = kbd_special_chars - kbd_special_keys, error, "kbd_special_chars needs one byte a key"
kbd_ctrl_scans:
        .byte $73, $74, $75, $76, $77, $84
kbd_ctrl_scans_end:

; The last row and the last column, for ansi.
ansi_last:
        .byte ROWS - 1, COLUMNS - 1

; The X16 palette entries of ANSI colours 0 to 7.
ansi_colours:
        .byte 0, 2, 5, 9, 6, 4, 3, 15                   ; brown for yellow, light grey for white

; The character of keycodes 1 to KEY_SPACE, without and with Shift. 0: no character.
kbd_lower:
        .byte "`1234567890-=", 0, $08, $09     ; $01-$10
        .byte "qwertyuiop[]\", 0               ; $11-$1E
        .byte "asdfghjkl;'", 0, $0D, 0         ; $1F-$2C
        .byte "\zxcvbnm,./", 0, 0              ; $2D-$39
        .byte 0, 0, 0, " "                     ; $3A-$3D
kbd_upper:
        .byte "~!@#$%^&*()_+", 0, $08, $09
        .byte "QWERTYUIOP{}|", 0
        .byte "ASDFGHJKL:", '"', 0, $0D, 0
        .byte "|ZXCVBNM<>?", 0, 0
        .byte 0, 0, 0, " "
        .assert kbd_upper - kbd_lower = KEY_SPACE, error, "kbd_lower needs one byte a keycode"
        .assert * - kbd_upper = KEY_SPACE, error, "kbd_upper needs one byte a keycode"

; The two KERNAL entries x16emu needs, at the stock KERNAL's addresses. They are not API.
; Trap: x16emu -bas pastes keys once the PC reaches $FFCF, and x16emu -echo prints A whenever
; the PC reaches $FFD2. So every console read goes through CHRIN and every console write
; through CHROUT. x16emu does both only when "MIST" is at $FFF6 (segment SIGNATURE in boot.s).
.segment "KERNALJUMPS"

; CHRIN: con_in.
CHRIN:
        jmp con_in

; CHROUT: con_out.
CHROUT:
        jmp con_out
