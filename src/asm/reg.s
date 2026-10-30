; The settings store: the calls reg_get and reg_set on the file C:\6502DOS.REG.
;
; The file is "6502REG1", then the entries, then a $00. An entry is NAME=VALUE and a $00, the
; form of an MS-DOS environment block. A name is 1 to 32 characters, kept in upper case, with
; no = and no $00. A value is up to 255 characters with no $00. A file that does not start
; "6502REG1" reads as empty.
;
;   6502REG1FONT.FILE=C:\sys\GUI.F08<$00>EDIT.TABS=4<$00><$00>
;
; reg_set writes the whole file to C:\6502DOS.$$$, deletes C:\6502DOS.REG and renames the
; copy. Each call opens its files on handles of the running program.

.setcpu "65C02"

.include "mem.inc"
.include "api.inc"
.include "far.inc"

.export api_reg_get, api_reg_set
.import api_open, api_create, api_read, api_write, api_close, api_delete, api_rename
.import to_upper, jsrfar

REG_BUFFER    = 128             ; the size of each file buffer; reg_put tests bit 7 of its count
NAME_MAX      = 32
HEADER_LENGTH = 8

.segment "KERNELZP" : zeropage

reg_value:    .res 2            ; the caller's r1: the value

.segment "REGRAM"

reg_path:     .res 15           ; C:\6502DOS.REG, length-prefixed, from reg_paths
reg_temp:     .res 15           ; C:\6502DOS.$$$
reg_key:      .res NAME_MAX + 1 ; the caller's key in upper case, length-prefixed
reg_name:     .res NAME_MAX + 1 ; reg_entry: the name of an entry of the store
reg_save:     .res 4            ; the caller's r0 and r1
reg_sp:       .res 1            ; the stack pointer reg_fail returns to the caller with
reg_length:   .res 1            ; api_reg_set: the length of the value
reg_in:       .res 1            ; the handle of the store, $FF when closed
reg_in_count: .res 1            ; the bytes in reg_in_buf
reg_in_index: .res 1            ; the next byte of reg_in_buf
reg_out:      .res 1            ; the handle of C:\6502DOS.$$$, $FF when closed
reg_out_count: .res 1           ; the bytes in reg_out_buf
reg_in_buf:   .res REG_BUFFER
reg_out_buf:  .res REG_BUFFER

.segment "CODE"

; reg_enter: keeps the caller's stack pointer, r0 and r1, and puts the key at r0 in reg_key in
; upper case. A key of 0 or more than NAME_MAX characters, or one with an = or a $00, gives
; error 13. Changes A, X and Y.
reg_enter:
        tsx
        inx
        inx
        stx reg_sp              ; the pointer in the call, below this return address
        ldx #3
@save:
        lda r0,x
        sta reg_save,x
        dex
        bpl @save
        lda r1
        sta reg_value
        lda r1+1
        sta reg_value+1
        lda #$FF
        sta reg_in
        sta reg_out
        ldx #reg_key - reg_path - 1
@path:
        lda reg_paths,x
        sta reg_path,x
        dex
        bpl @path
        lda (r0)
        beq reg_bad_data
        cmp #NAME_MAX + 1
        bcs reg_bad_data
        sta reg_key
        tay
@key:
        lda (r0),y
        beq reg_bad_data
        cmp #'='
        beq reg_bad_data
        jsr to_upper
        sta reg_key,y
        dey
        bne @key
        rts

; api_reg_get: reg_get, call 55. Copies the value of the key at r0 to the buffer at r1.
api_reg_get:
        jsr reg_enter
        jsr reg_find
        lda #ERR_NOT_FOUND
        bcs reg_leave
        ldy #0
@byte:
        jsr reg_fetch
        beq @end
        cpy #255
        beq @byte               ; past 255 characters, dropped
        iny
        sta (reg_value),y
        bra @byte
@end:
        tya
        sta (reg_value)
        clc
        bra reg_leave

reg_bad_data:
        lda #ERR_BAD_DATA
        ; fall through

; reg_fail: returns error A to the caller of the call, from any depth.
reg_fail:
        ldx reg_sp
        txs
        sec
        ; fall through

; reg_leave: closes the files the call opened, deletes C:\6502DOS.$$$ when it is still open,
; puts back the caller's r0 and r1, and returns A and carry to the caller of the call.
reg_leave:
        php
        pha
        jsr reg_close_in
        ldx reg_out
        bmi @restore
        jsr api_close
        jsr reg_r0_temp
        FARCALL api_delete
@restore:
        ldx #3
@copy:
        lda reg_save,x
        sta r0,x
        dex
        bpl @copy
        pla
        plp
        rts

; api_reg_set: reg_set, call 56. Sets the key at r0 to the value at r1; an empty value removes
; the key. Writes nothing when the store holds the value already.
api_reg_set:
        jsr reg_enter
        lda (reg_value)
        sta reg_length
        tay
        beq @check
@scan:
        lda (reg_value),y
        beq reg_bad_data
        dey
        bne @scan
@check:
        jsr reg_find
        bcs @missing
        ldy #0
@same:
        jsr reg_fetch
        beq @end
        cpy reg_length
        bcs @write              ; the stored value is longer
        iny
        cmp (reg_value),y
        beq @same
        bra @write
@end:
        cpy reg_length
        bne @write
        clc
        bra reg_leave
@missing:                       ; a missing key holds ""
        lda reg_length
        clc
        beq reg_leave
@write:
        jsr reg_close_in
        jsr reg_r0_temp
        lda #0                  ; no attributes
        jsr api_create
        bcs reg_leave
        stx reg_out
        stz reg_out_count
        ldy #0
@header:
        lda reg_header,y
        jsr reg_put
        iny
        cpy #HEADER_LENGTH
        bne @header
        jsr reg_open
        bcs @add
@copy:
        jsr reg_entry
        bcs @add
        jsr reg_match
        beq @drop
        jsr reg_put_name
@value:
        jsr reg_fetch
        pha
        jsr reg_put
        pla
        bne @value
        bra @copy
@drop:
        jsr reg_skip
        bra @copy
@add:
        ldy reg_length
        beq @close
        ldx #NAME_MAX
@key:
        lda reg_key,x
        sta reg_name,x
        dex
        bpl @key
        jsr reg_put_name
        ldy #0
@new:
        iny
        lda (reg_value),y
        jsr reg_put
        cpy reg_length
        bne @new
        lda #0
        jsr reg_put
@close:
        lda #0                  ; the end of the entries
        jsr reg_put
        jsr reg_flush
        ldx reg_out
        jsr api_close
        bcs @leave
        lda #$FF
        sta reg_out
        jsr reg_close_in
        jsr reg_r0_path
        FARCALL api_delete      ; error 2 when there was no store
        lda #<reg_path
        sta r1
        lda #>reg_path
        sta r1+1
        jsr reg_r0_temp
        FARCALL api_rename
@leave:
        jmp reg_leave           ; with the carry and A of the last call

; reg_find: opens the store and reads it up to the value of reg_key. Returns carry clear when
; the key is there, with its value next for reg_fetch; carry set when the key or the store is
; missing. Changes A, X and Y.
reg_find:
        jsr reg_open
        bcs @done
@entry:
        jsr reg_entry
        bcs @done
        jsr reg_match
        bne @next
        clc
@done:
        rts
@next:
        jsr reg_skip
        bra @entry

; reg_open: opens the store on reg_in and reads its header. Returns carry clear when the header
; is right; carry set with the store closed when it is missing or its header is wrong. Any
; other error of open goes to reg_fail. Changes A, X and Y.
reg_open:
        jsr reg_r0_path
        lda #0                  ; read
        jsr api_open
        bcc @open
        cmp #ERR_NOT_FOUND
        beq @done               ; carry set
        jmp reg_fail
@open:
        stx reg_in
        stz reg_in_count
        stz reg_in_index
        ldy #0
@header:
        jsr reg_fetch
        cmp reg_header,y
        bne @wrong
        iny
        cpy #HEADER_LENGTH
        bne @header
        clc
@done:
        rts
@wrong:
        jsr reg_close_in
        sec
        rts

; reg_close_in: closes reg_in when it is open. Changes A and X.
reg_close_in:
        ldx reg_in
        bmi @done
        jsr api_close
        lda #$FF
        sta reg_in
@done:
        rts

; reg_r0_path: points r0 at C:\6502DOS.REG. Changes A.
reg_r0_path:
        lda #<reg_path
        sta r0
        lda #>reg_path
        sta r0+1
        rts

; reg_r0_temp: points r0 at C:\6502DOS.$$$. Changes A.
reg_r0_temp:
        lda #<reg_temp
        sta r0
        lda #>reg_temp
        sta r0+1
        rts

; reg_entry: reads the name of the next entry of the store into reg_name; characters past
; NAME_MAX are dropped. Returns carry set at the end of the entries: a $00 or the end of the
; file before an =. Changes A, X and Y.
reg_entry:
        ldy #0
@char:
        jsr reg_fetch
        beq @end
        cmp #'='
        beq @done
        cpy #NAME_MAX
        bcs @char
        iny
        sta reg_name,y
        bra @char
@done:
        sty reg_name
        clc
        rts
@end:
        sec
        rts

; reg_match: returns Z set when reg_name is reg_key. Changes A and Y.
reg_match:
        ldy reg_name
@char:
        lda reg_name,y
        cmp reg_key,y
        bne @done
        dey
        bpl @char               ; the length byte too
        lda #0
@done:
        rts

; reg_skip: reads the store past the next $00. Changes A and X.
reg_skip:
        jsr reg_fetch
        bne reg_skip
        rts

; reg_fetch: returns A = the next byte of the store, 0 at its end, and Z from A. A read error
; goes to reg_fail. Keeps Y. Changes X, r0 and r1.
reg_fetch:
        phy
        ldx reg_in_index
        cpx reg_in_count
        bne @byte
        lda #<reg_in_buf
        sta r0
        lda #>reg_in_buf
        sta r0+1
        lda #REG_BUFFER
        sta r1
        stz r1+1
        ldx reg_in
        jsr api_read
        bcc @read
        jmp reg_fail
@read:
        lda r1
        sta reg_in_count
        beq @end                ; A = 0
        ldx #0
@byte:
        lda reg_in_buf,x
        inx
        stx reg_in_index
@end:
        ply
        cmp #0
        rts

; reg_put_name: writes reg_name and an = to C:\6502DOS.$$$. Changes A, X and Y.
reg_put_name:
        ldy #0
        bra @test
@char:
        iny
        lda reg_name,y
        jsr reg_put
@test:
        cpy reg_name
        bne @char
        lda #'='
        ; fall through

; reg_put: writes A to C:\6502DOS.$$$ through reg_out_buf. Keeps Y. Changes A and X.
reg_put:
        ldx reg_out_count
        sta reg_out_buf,x
        inx
        stx reg_out_count
        bpl reg_done            ; fewer than REG_BUFFER bytes
        ; fall through

; reg_flush: writes reg_out_buf to C:\6502DOS.$$$. A short write, a full drive, gives error
; 29. Keeps Y. Changes A, X, r0 and r1.
reg_flush:
        phy
        lda #<reg_out_buf
        sta r0
        lda #>reg_out_buf
        sta r0+1
        lda reg_out_count
        sta r1
        stz r1+1
        ldx reg_out
        jsr api_write
        bcs @fail
        lda r1
        cmp reg_out_count
        beq @written
        lda #ERR_WRITE_FAULT
@fail:
        jmp reg_fail
@written:
        stz reg_out_count
        ply
reg_done:
        rts

.segment "RODATA"

reg_paths:
        .byte 14, "C:\6502DOS.REG"
        .byte 14, "C:\6502DOS.$$$"
reg_header:
        .byte "6502REG1"
