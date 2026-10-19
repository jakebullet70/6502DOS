; What the FAT32 library imports, in ROM bank 1: its zero page, its variables, the sector
; buffer, the sector reads and writes through the SD card driver in bank 0, and to_lower.

.setcpu "65C02"

.include "mem.inc"
.include "far.inc"

.exportzp fat32_bufptr, fat32_lfn_bufptr, fat32_ptr, fat32_ptr2, krn_ptr1, bank_save
.export fat32_size, fat32_dirent, fat32_errno, fat32_readonly, skip_mask
.export sector_buffer, sector_buffer_end, sector_lba
.export sdcard_read_sector, sdcard_write_sector, sdcard_set_fast_mode, to_lower
.importzp saved_bank
.import jsrfar1, sd_input, sd_output

; bank_save: the RAM bank of a buffer at $A000-$BFFF: the caller's bank.
bank_save = saved_bank

.segment "KERNELZP" : zeropage

fat32_bufptr:     .res 2        ; the current context's byte in sector_buffer
fat32_lfn_bufptr: .res 2
fat32_ptr:        .res 2        ; the first path or buffer of a call
fat32_ptr2:       .res 2        ; the second path of fat32_rename
krn_ptr1:         .res 2        ; fat32_read, fat32_write: bit 7 set for a stream copy

.segment "FATBUF"

sector_buffer:    .res 512
sector_buffer_end:

; Trap: fat32_init clears the library's variables, not these. The caller sets fat32_readonly.
.segment "FATBSS"

fat32_size:       .res 4
fat32_dirent:     .res 256 + 22 ; struct dirent in fat32_regs.inc
fat32_errno:      .res 1
fat32_readonly:   .res 1        ; not 0: the library writes no sector
skip_mask:        .res 1        ; match_type: the attribute bits that skip an entry
sector_lba:       .res 4        ; the sector in sector_buffer

.segment "B1CODE"

; sdcard_read_sector: reads sector sector_lba into sector_buffer. RAM bank 0 must be selected.
; Returns carry set on success. Changes A, X and Y.
sdcard_read_sector:
        jsr blk_request
        FARCALL sd_input, jsrfar1
        bra flip_carry

; sdcard_write_sector: writes sector_buffer to sector sector_lba. RAM bank 0 must be selected.
; Returns carry set on success. Changes A, X and Y.
sdcard_write_sector:
        jsr blk_request
        FARCALL sd_output, jsrfar1
flip_carry:                     ; the driver returns carry set on an error
        bcs sector_failed
        sec
; sdcard_set_fast_mode: does nothing. sdcard.s has the slow read loop only.
sdcard_set_fast_mode:
        rts
sector_failed:
        clc
        rts

; blk_request: the request of one sector between sector_lba and sector_buffer. Changes A and X.
blk_request:
        ldx #3
@lba:
        lda sector_lba,x
        sta BLK_SECTOR,x
        dex
        bpl @lba
        lda #<sector_buffer
        sta BLK_BUFFER
        lda #>sector_buffer
        sta BLK_BUFFER+1
        lda #1
        sta BLK_COUNT
        rts

; to_lower: A to Z in A become a to z; any other byte stays. Changes carry.
; The names of the library are ISO-8859-15: a letter past Z keeps its case.
to_lower:
        cmp #'A'
        bcc @done
        cmp #'Z' + 1
        bcs @done
        ora #$20
@done:
        rts
