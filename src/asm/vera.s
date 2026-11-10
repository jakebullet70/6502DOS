; 6502DOS ROM bank 5: call 61, vera. VRAM, the sprites and the palette, through VERA's data
; port 0.
;
; Trap: the console keeps VERA_CTRL at 0, so ADDRSEL selects port 0; these routines rely on it.

.setcpu "65C02"

.include "mem.inc"
.include "api.inc"

.export api_vera, api_gfx
.import sprite_hits, gfx_mode, gfx_clear, gfx_pset, gfx_point, gfx_line, gfx_frame, gfx_rect, gfx_circle, gfx_char
.importzp gate_a

.segment "B5CODE"

; api_gfx: call 62. Y = the function; A and r0 to r3 by function. Runs function Y of gfx.s, as api_vera.
api_gfx:
        cpy #GFX_COUNT
        bcs vera_bad            ; carry set
        tya
        adc #VERA_COUNT         ; carry clear: gfx's routines follow vera's in vera_table
        bcc vera_run            ; always

; api_vera: call 61. Y = the function; A, X and r0 to r3 by function. Runs the function, which
; ends with carry clear, or with carry set and A = the error.
api_vera:
        cpy #VERA_COUNT
        bcs vera_bad            ; carry set
        tya
vera_run:
        asl
        tay
        lda vera_table+1,y
        pha
        lda vera_table,y
        pha
        lda gate_a              ; the caller's A
        rts                     ; to the function, with X as it came
vera_bad:
        lda #ERR_BAD_FUNCTION
        rts

; vera_table: for each function by number, its routine less 1, for the RTS of api_vera; then
; gfx's.
vera_table:
        .addr vera_vpeek - 1    ; 0 vpeek
        .addr vera_vpoke - 1    ; 1 vpoke
        .addr vera_vfill - 1    ; 2 vfill
        .addr vera_vwrite - 1   ; 3 vwrite
        .addr vera_vread - 1    ; 4 vread
        .addr vera_vload - 1    ; 5 vload
        .addr vera_sprset - 1   ; 6 sprset
        .addr vera_sprmove - 1  ; 7 sprmove
        .addr vera_sprshape - 1 ; 8 sprshape
        .addr vera_sprhits - 1  ; 9 sprhits
        .addr vera_sprclear - 1 ; 10 sprclear
        .addr vera_palette - 1  ; 11 palette
        .assert * - vera_table = 2 * VERA_COUNT, error, "vera_table needs a routine for each function"
        .addr gfx_mode - 1      ; gfx 0 mode
        .addr gfx_clear - 1     ; gfx 1 clear
        .addr gfx_pset - 1      ; gfx 2 pset
        .addr gfx_point - 1     ; gfx 3 point
        .addr gfx_line - 1      ; gfx 4 line
        .addr gfx_frame - 1     ; gfx 5 frame
        .addr gfx_rect - 1      ; gfx 6 rect
        .addr gfx_circle - 1    ; gfx 7 circle
        .addr gfx_char - 1      ; gfx 8 char
        .assert * - vera_table = 2 * (VERA_COUNT + GFX_COUNT), error, "vera_table needs a routine for each gfx function"

; vera_vpeek: A = the VRAM byte at r0, bit 16 in X.
vera_vpeek:
        jsr vera_point
        lda VERA_DATA0
        clc
        rts

; vera_vpoke: writes A to the VRAM byte at r0, bit 16 in X.
vera_vpoke:
        jsr vera_point
        sta VERA_DATA0
        clc
        rts

; vera_vfill: writes A to r1 VRAM bytes from r0, bit 16 in X. r1 = 0 writes none.
vera_vfill:
        jsr vera_point_inc
        ldx r1+1                ; the whole pages
        beq @tail
        ldy #0
@page:
        sta VERA_DATA0
        dey
        bne @page
        dex
        bne @page
@tail:
        ldy r1                  ; the bytes after the pages
        beq @done
@rest:
        sta VERA_DATA0
        dey
        bne @rest
@done:
        clc
        rts

; vera_vwrite: copies r2 bytes from RAM at r1 to VRAM at r0, bit 16 in X. r2 = 0 copies none.
vera_vwrite:
        jsr vera_point_inc
        lda r1+1
        pha                     ; r1 comes back at the end
        ldy #0
        ldx r2+1                ; the whole pages
        beq @tail
@page:
        lda (r1),y
        sta VERA_DATA0
        iny
        bne @page
        inc r1+1
        dex
        bne @page
@tail:
        ldx r2                  ; the bytes after the pages; Y is 0
        beq @done
@rest:
        lda (r1),y
        sta VERA_DATA0
        iny
        dex
        bne @rest
@done:
        pla
        sta r1+1
        clc
        rts

; vera_vread: copies r2 bytes from VRAM at r0, bit 16 in X, to RAM at r1. r2 = 0 copies none.
vera_vread:
        jsr vera_point_inc
        lda r1+1
        pha                     ; r1 comes back at the end
        ldy #0
        ldx r2+1                ; the whole pages
        beq @tail
@page:
        lda VERA_DATA0
        sta (r1),y
        iny
        bne @page
        inc r1+1
        dex
        bne @page
@tail:
        ldx r2                  ; the bytes after the pages; Y is 0
        beq @done
@rest:
        lda VERA_DATA0
        sta (r1),y
        iny
        dex
        bne @rest
@done:
        pla
        sta r1+1
        clc
        rts

; vera_vload: reads r1 bytes of file X to VRAM at r0, bit 16 in A, through call 3 into the I/O
; page. Returns r1 = the bytes read, fewer at the end of the file, or carry set and A = the
; error of the read. X must be a file's handle: a device writes its bytes across the I/O page.
vera_vload:
        ora #$10                ; ADDR_H bits 4 to 7: the increment, 1
        sta VERA_ADDR_H
        lda r0
        sta VERA_ADDR_L
        pha                     ; r0 comes back at the end
        lda r0+1
        sta VERA_ADDR_M
        pha
        lda #<VERA_DATA0
        sta r0
        lda #>VERA_DATA0
        sta r0+1
        jsr API_READ
        ply
        sty r0+1
        ply
        sty r0
        rts                     ; carry and A from the read

; vera_sprset: sets field A of sprite X, 0 to 127, to the value in r0's low byte. The other
; bits of the attribute byte stay. It turns the sprites on; exec_quit turns them off.
vera_sprset:
        tay                     ; Y = the field
        lda #$40                ; DC_VIDEO bit 6: the sprites on
        tsb VERA_DC_VIDEO
        lda vera_field_byte,y
        jsr vera_sprite_at
        lda r0
        ldx vera_field_shift,y
        beq @placed
@shift:
        asl
        dex
        bne @shift
@placed:
        eor VERA_DATA0          ; the old bits under the mask become the value's
        and vera_field_mask,y
        eor VERA_DATA0
        sta VERA_DATA0
        clc
        rts

; The fields of vera_sprset by number: the attribute byte, the shift, the mask.
vera_field_byte:
        .byte 6, 6, 6, 7, 7, 7, 1       ; 0 depth, 1 flip, 2 mask, 3 palette, 4 width, 5 height, 6 mode
vera_field_shift:
        .byte 2, 0, 4, 0, 4, 6, 7
vera_field_mask:
        .byte $0C, $03, $F0, $0F, $30, $C0, $80

; vera_sprmove: puts sprite X, 0 to 127, at x r0 and y r1.
vera_sprmove:
        lda #2                  ; byte 2: x, then y
        jsr vera_sprite_at
        lda #$11                ; increment 1
        sta VERA_ADDR_H
        lda r0
        sta VERA_DATA0
        lda r0+1
        sta VERA_DATA0
        lda r1
        sta VERA_DATA0
        lda r1+1
        sta VERA_DATA0
        clc
        rts

; vera_sprshape: points sprite X, 0 to 127, at the shape at VRAM address r0 times 32. The mode
; bit stays.
vera_sprshape:
        lda #0                  ; byte 0: address bits 5 to 12
        jsr vera_sprite_at
        lda r0
        sta VERA_DATA0
        inc VERA_ADDR_L         ; byte 1: bits 0 to 3, address bits 13 to 16
        lda r0+1
        eor VERA_DATA0
        and #$0F
        eor VERA_DATA0
        sta VERA_DATA0
        clc
        rts

; vera_sprhits: A bits 0 to 3 = the collision groups hit since the last vera_sprclear.
vera_sprhits:
        lda sprite_hits
        lsr
        lsr
        lsr
        lsr
        clc
        rts

; vera_sprclear: clears the collision groups hit.
vera_sprclear:
        stz sprite_hits
        clc
        rts

; vera_palette: sets palette entry X to the color r0, $0RGB.
vera_palette:
        txa
        asl                     ; carry: entry bit 7
        sta VERA_ADDR_L
        lda #>PALETTE
        adc #0
        sta VERA_ADDR_M
        lda #$11                ; bit 16, increment 1
        sta VERA_ADDR_H
        lda r0                  ; green and blue, then red
        sta VERA_DATA0
        lda r0+1
        sta VERA_DATA0
        clc
        rts

; vera_sprite_at: points data port 0 at byte A, 0 to 7, of sprite X, 0 to 127, with no
; increment.
vera_sprite_at:
        sta VERA_ADDR_L         ; the byte, until the sprite's offset joins it
        txa
        asl
        asl
        asl
        ora VERA_ADDR_L
        sta VERA_ADDR_L
        txa
        lsr
        lsr
        lsr
        lsr
        lsr
        ora #>SPRITES
        sta VERA_ADDR_M
        lda #^SPRITES           ; bit 16, no increment
        sta VERA_ADDR_H
        rts

; vera_point_inc: points data port 0 at r0, bit 16 in X, 0 or 1, with an increment of 1. Keeps A.
vera_point_inc:
        pha
        txa
        ora #$10                ; ADDR_H bits 4 to 7: the increment, 1
        tax
        pla
; vera_point: points data port 0 at r0, bit 16 in X, 0 or 1, with no increment. Keeps A.
vera_point:
        ldy r0
        sty VERA_ADDR_L
        ldy r0+1
        sty VERA_ADDR_M
        stx VERA_ADDR_H
        rts
