; I2C bus over VIA 1 port A: SDA on bit 0, SCL on bit 1.
;
; Ported from x16-rom, kernal/drivers/x16/i2c.s, github.com/X16Community/x16-rom. Kept: the
; subroutine form of the pin functions, i2c_write, i2c_read, i2c_start, i2c_stop, i2c_init,
; and the sequences of i2c_read_byte and i2c_write_byte. Left out: the mutex and the batch
; calls.
;
; Original header:
; (C)2015-2022 Dieter Hauer, Michael Steil, Joe Burks
; License: 2-clause BSD
;
; Copyright (c) 2015, Dieter Hauer
; All rights reserved.
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

.export i2c_read_byte, i2c_write_byte

pr  = VIA1_PRA
ddr = VIA1_DDRA
SDA = (1 << 0)
SCL = (1 << 1)

.segment "CODE"

; i2c_read_byte: reads register Y of the I2C device X. Returns the byte in A, with Z and N
; set from it and carry clear, or carry set when the device does not answer. Changes X and Y.
i2c_read_byte:
        jsr i2c_init
        jsr i2c_start
        txa                     ; device
        asl
        pha                     ; device * 2: write
        phy
        jsr i2c_write
        ply
        bcs @error
        tya                     ; register
        jsr i2c_write
        jsr i2c_stop
        jsr i2c_start
        pla
        inc                     ; device * 2 + 1: read
        jsr i2c_write
        jsr i2c_read
        pha
        sec                     ; NAK: the last byte wanted
        jsr send_bit
        jsr i2c_stop
        pla
        clc
        rts
@error:
        pla
        jsr i2c_stop
        sec
        rts

; i2c_write_byte: writes A to register Y of the I2C device X. Returns carry clear, or carry set
; when the device does not answer. Changes A, X and Y.
i2c_write_byte:
        pha                     ; the value
        phy
        jsr i2c_init
        jsr i2c_start
        txa                     ; device
        asl                     ; device * 2: write
        jsr i2c_write
        ply
        bcs @error
        tya                     ; register
        jsr i2c_write
        bcs @error
        pla
        jsr i2c_write
        jmp i2c_stop            ; keeps carry
@error:
        pla
        jmp i2c_stop

; i2c_write: sends the byte in A. Returns carry clear on ACK, set on NAK. Changes A, X and Y.
i2c_write:
        ldx #8
@loop:
        rol
        tay
        jsr send_bit
        tya
        dex
        bne @loop
        jmp rec_bit             ; C = 0: success

; i2c_read: returns the byte read in A. Changes X and Y.
i2c_read:
        ldx #8
@loop:
        tay
        jsr rec_bit
        tya
        rol
        dex
        bne @loop
        rts

; i2c_stop: SDA goes high while SCL is high.
i2c_stop:
        jsr sda_low
        jsr i2c_brief_delay
        jsr scl_high
        jsr i2c_brief_delay
        jsr sda_high
        jmp i2c_brief_delay

; i2c_start: SDA goes low while SCL is high, then SCL goes low.
i2c_start:
        jsr sda_low
        jsr i2c_brief_delay
        jmp scl_low

; i2c_init: sets the port bits to 0, so a pin is driven low by setting its DDR bit.
i2c_init:
        lda #SDA | SCL
        trb pr
        jsr sda_high
        jmp scl_high

sda_low:
        lda #SDA
        tsb ddr
        rts

sda_high:
        lda #SDA
        trb ddr
        rts

scl_high:
        lda #SCL
        trb ddr
@wait:
        lda pr                  ; a device may hold the clock low
        and #SCL
        beq @wait
        rts

scl_low:
        lda #SCL
        tsb ddr
        rts

; send_bit: sends the bit in carry.
send_bit:
        bcs @one
        jsr sda_low
        bra @clock
@one:
        jsr sda_high
@clock:
        jsr scl_high
        bra scl_low

; rec_bit: returns the bit read in carry.
rec_bit:
        jsr sda_high            ; the device drives SDA
        jsr scl_high
        lda pr
        .assert SDA = (1 << 0), error, "update the shift if SDA is not bit 0"
        lsr                     ; bit -> C
        bra scl_low

i2c_brief_delay:
        pha
        pla
        pha
        pla
        rts
