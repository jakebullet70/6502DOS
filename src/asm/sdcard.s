; The SD card block driver: one unit over VERA's SPI port.
;
; Ported from x16-rom, fat32/sdcard.s, github.com/X16Community/x16-rom. Kept: wait_ready,
; deselect, select, spi_read, spi_write, send_cmd, the start-up sequence of sdcard_init, the
; read loops of sdcard_read_sector and the steps of sdcard_write_sector. Changed: the commands
; come from a table, the sectors go to and from BLK_BUFFER, and the routines sit behind a driver
; header. Left out: the alive check and the fast write loop.
;
; Original header:
; Copyright (C) 2020 Frank van den Hoef
; fat32/README.md gives the licence: Copyright 2020 Frank van den Hoef, Michael Steil,
; 2-clause BSD.
;
; Redistribution and use in source and binary forms, with or without
; modification, are permitted provided that the following conditions are met:
;
; 1. Redistributions of source code must retain the above copyright notice, this
;    list of conditions and the following disclaimer.
; 2. Redistributions in binary form must reproduce the above copyright notice,
;    this list of conditions and the following disclaimer in the documentation
;    and/or other materials provided with the distribution.
;
; THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
; ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
; WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
; DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
; ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
; (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
; ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
; (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
; SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

.setcpu "65C02"

.include "mem.inc"
.include "api.inc"

.export sd_driver, sd_input, sd_output

SPI_SELECT    = $01             ; VERA_SPI_CTRL bits
SPI_SLOW      = $02
SPI_AUTOTX    = $04             ; each read of VERA_SPI_DATA starts the next transfer

.segment "KERNELZP" : zeropage

sd_ptr:       .res 2            ; where the next sector goes

.segment "KERNELRAM"

sd_ready:     .res 1            ; $FF once the card has started, 0 without a card
sd_cmd:       .res 6            ; the command in the order sent: index, argument high byte first, CRC
sd_count:     .res 1            ; wait_ready's timeout, then the pages of a sector left
sd_fast:      .res 1            ; bit 7 set: read_sector uses the fast loop

.segment "CODE"

; sd_init: SD command 0. Starts the card. The drive exists with or without a card, so it
; returns carry clear.
sd_init:
        stz sd_ready
        stz sd_fast
        lda #SPI_SLOW           ; deselected, below 400 kHz
        sta VERA_SPI_CTRL
        ldx #10                 ; at least 74 clocks with the card deselected
@clock:
        jsr spi_read
        dex
        bne @clock
        ldx #cmd_go_idle - sd_commands
        jsr send_table
        bcc @fail
        cmp #1                  ; idle
        bne @fail
        ldx #cmd_if_cond - sd_commands
        jsr send_table          ; SDv2: SDHC or SDXC
        bcc @fail
        cmp #1
        bne @fail
        ldx #4                  ; the rest of the R7 response
@r7:
        jsr spi_read
        dex
        bne @r7
@idle:                          ; wait for the card to leave the idle state
        ldx #cmd_app - sd_commands
        jsr send_table
        bcc @fail
        ldx #cmd_op_cond - sd_commands
        jsr send_table
        bcc @fail
        cmp #0
        bne @idle
        ldx #cmd_read_ocr - sd_commands
        jsr send_table
        jsr spi_read
        and #$40                ; CCS: the card takes block addresses
        beq @fail
        ldx #3
@ocr:
        jsr spi_read
        dex
        bne @ocr
        jsr deselect
        stz VERA_SPI_CTRL       ; full speed
        dec sd_ready
@fail:
        jsr deselect
        clc
        rts

; sd_control: SD command 12, IOCTL output. Bit 0 of the first byte at r0 set selects the fast
; read loop, clear the slow one. Returns r1 = 1, or 0 when r1 is 0.
sd_control:
        lda r1
        ora r1+1
        beq @done
        lda (r0)
        lsr                     ; bit 0 to carry
        ror sd_fast             ; carry to bit 7
        lda #1
        sta r1
        stz r1+1
@done:
        clc
        rts

; sd_input: SD command 4. Reads BLK_COUNT sectors from BLK_SECTOR into BLK_BUFFER. Returns
; carry set and A = ERR_NOT_READY without a card, ERR_READ_FAULT when a read fails.
sd_input:
        ldx #$40 | 17           ; READ_SINGLE_BLOCK
        bra sd_request

; sd_output: SD command 8. Writes BLK_COUNT sectors from BLK_BUFFER to BLK_SECTOR. Returns
; carry set and A = ERR_NOT_READY without a card, ERR_WRITE_FAULT when a write fails.
sd_output:
        ldx #$40 | 24           ; WRITE_BLOCK
        ; fall through

; sd_request: moves BLK_COUNT sectors with the command X, one sector a command.
sd_request:
        lda sd_ready
        bne @ready
        lda #ERR_NOT_READY
        sec
        rts
@ready:
        stx sd_cmd
        lda BLK_BUFFER
        sta sd_ptr
        lda BLK_BUFFER+1
        sta sd_ptr+1
        ldx #3
        ldy #1
@argument:
        lda BLK_SECTOR,x
        sta sd_cmd,y
        iny
        dex
        bpl @argument
        lda #1                  ; the CRC is not checked
        sta sd_cmd+5
@sector:
        lda sd_cmd
        cmp #$40 | 24
        beq @write
        jsr read_sector
        bcc @read_fault
        bra @next
@write:
        jsr write_sector
        bcc @write_fault
@next:                          ; the next sector
        ldx #4
@count:
        inc sd_cmd,x
        bne @counted
        dex
        bne @count
@counted:
        dec BLK_COUNT
        bne @sector
        clc
        rts
@read_fault:
        lda #ERR_READ_FAULT
        sec
        rts
@write_fault:
        lda #ERR_WRITE_FAULT
        sec
        rts

; read_sector: reads the sector of sd_cmd to sd_ptr and moves sd_ptr on by 512. Returns carry
; set on success.
read_sector:
        jsr send_cmd
        bcc @error
        cmp #0
        bne @error
        ldx #0                  ; wait for the data token
@outer:
        ldy #0
@token:
        jsr spi_read
        cmp #$FE
        beq @start
        dey
        bne @token
        dex
        bne @outer
@error:
        jmp sd_fail
@start:
        lda #2
        sta sd_count
        bit sd_fast
        bmi @fast
        ldx #$FF
@page:
        ldy #0
@byte:
        stx VERA_SPI_DATA       ; 4
@busy:
        bit VERA_SPI_CTRL       ; 4
        bmi @busy               ; 2 + 1 when it branches
        lda VERA_SPI_DATA       ; 4
        sta (sd_ptr),y          ; 6
        iny
        bne @byte
        inc sd_ptr+1
        dec sd_count
        bne @page
        jsr spi_read            ; the CRC
@crc:
        jsr spi_read
        jsr deselect
        sec
        rts
; Trap: a read of VERA_SPI_DATA during a transfer returns the last byte and starts no new
; transfer. A transfer is busy for 5.12 cycles at 8 MHz on VERA, 6.4 on x16emu R49. The reads
; here are 12 cycles apart.
@fast:
        lda #$FF
        sta VERA_SPI_DATA       ; starts the first transfer
        lda VERA_SPI_CTRL
        ora #SPI_AUTOTX
        sta VERA_SPI_CTRL
        ldy #0
@fast_byte:
        .repeat 4
        lda VERA_SPI_DATA       ; 4
        sta (sd_ptr),y          ; 6
        iny                     ; 2
        .endrepeat
        bne @fast_byte
        inc sd_ptr+1
        dec sd_count
        bne @fast_byte
        lda VERA_SPI_CTRL       ; the last read started the first CRC byte
        and #<~SPI_AUTOTX
        sta VERA_SPI_CTRL
        bra @crc

; write_sector: writes the sector at sd_ptr to the sector of sd_cmd and moves sd_ptr on by 512.
; Returns carry set on success.
write_sector:
        jsr send_cmd
        bcc sd_fail
        cmp #0
        bne sd_fail
        jsr wait_ready
        bcc sd_fail
        lda #$FE                ; the data token
        jsr spi_write
        lda #2
        sta sd_count
        ldy #0
@byte:
        lda (sd_ptr),y
        jsr spi_write
        iny
        bne @byte
        inc sd_ptr+1
        dec sd_count
        bne @byte
        jsr spi_read            ; the CRC is not checked
        jsr spi_read
        ldx #0                  ; the data response within 255 bytes: xxx00101 when the card took
@response:                      ; the data
        dex
        beq @taken              ; trap: x16emu R49 writes the sector and sends no response
        jsr spi_read
        cmp #$FF
        beq @response
        and #$1F
        cmp #$05
        bne sd_fail
@taken:
        jsr deselect            ; select waits while the card is busy
        sec
        rts

; sd_fail: deselects the card and returns carry clear.
sd_fail:
        jsr deselect
        clc
        rts

; wait_ready: waits for the card to send $FF, about 500 ms at 8 MHz at most. Returns carry set
; when it did. Changes A, X and Y.
wait_ready:
        lda #2
        sta sd_count
@1:
        ldx #0
@2:
        ldy #0
@3:
        jsr spi_read            ; 22
        cmp #$FF
        beq @done
        dey
        bne @3
        dex
        bne @2
        dec sd_count
        bne @1
        clc
        rts
@done:
        sec
        rts

; deselect: deselects the card. Changes A.
deselect:
        lda VERA_SPI_CTRL
        and #<~SPI_SELECT
        sta VERA_SPI_CTRL
        jmp spi_read

; select: selects the card and waits for it. Returns carry set when it is ready. Changes A, X
; and Y.
select:
        lda VERA_SPI_CTRL
        ora #SPI_SELECT
        sta VERA_SPI_CTRL
        jsr spi_read
        jsr wait_ready
        bcc @error
        rts
@error:
        jsr deselect
        clc
        rts

; spi_read: returns the next byte from the card in A.
spi_read:
        lda #$FF
        ; fall through

; spi_write: sends A.
spi_write:
        sta VERA_SPI_DATA
@busy:
        bit VERA_SPI_CTRL
        bmi @busy
        lda VERA_SPI_DATA
        rts

; send_table: copies the command at sd_commands + X to sd_cmd, then sends it.
send_table:
        ldy #0
@copy:
        lda sd_commands,x
        sta sd_cmd,y
        inx
        iny
        cpy #6
        bne @copy
        ; fall through

; send_cmd: sends sd_cmd. Returns carry set and the first byte of the response in A, or carry
; clear when the card does not answer. Changes X and Y.
send_cmd:
        jsr deselect
        jsr select
        bcc @error
        ldx #0
@byte:
        lda sd_cmd,x
        jsr spi_write
        inx
        cpx #6
        bne @byte
        ldy #10 + 1             ; wait for the response
@wait:
        dey
        beq @error
        jsr spi_read
        bit #$80
        bne @wait
        sec
        rts
@error:
        clc
        rts

.segment "RODATA"

; The start-up commands, each in the order sent.
sd_commands:
cmd_go_idle:  .byte $40 | 0, 0, 0, 0, 0, $95
cmd_if_cond:  .byte $40 | 8, 0, 0, $01, $AA, $87
cmd_app:      .byte $40 | 55, 0, 0, 0, 0, 1
cmd_op_cond:  .byte $40 | 41, $40, 0, 0, 0, 1
cmd_read_ocr: .byte $40 | 58, 0, 0, 0, 0, 1

; The driver header: a block device with one unit, the end of the chain.
sd_driver:
        .word $FFFF
        .byte DEV_IOCTL, DRV_ABI_VERSION, 13
        .byte 1, 0, 0, 0, 0, 0, 0, 0
        .word sd_init, 0, 0, 0, sd_input, 0, 0, 0, sd_output, 0, 0, 0, sd_control
