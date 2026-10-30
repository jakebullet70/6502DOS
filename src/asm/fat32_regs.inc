; The FAT32 library's registers, structures and error numbers.
;
; Ported from x16-rom, fat32/regs.inc, github.com/X16Community/x16-rom, master fbe32a6.
; Changed: mem.inc replaces io.inc, and ram_bank is RAM_BANK. FAT32_CONTEXTS is 16, one for each
; SFT entry; FAT32_VOLUMES is 1, drive C:.
;
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
;
; Original header:
.include "mem.inc"

ram_bank = RAM_BANK

.importzp fat32_bufptr, fat32_lfn_bufptr, fat32_ptr, fat32_ptr2

;-----------------------------------------------------------------------------
; Registers
;-----------------------------------------------------------------------------
SPI_CTRL      = VERA_SPI_CTRL
SPI_DATA      = VERA_SPI_DATA

;-----------------------------------------------------------------------------
; Kernel variables
;-----------------------------------------------------------------------------
.struct dirent           ; FILE             PARTITION
name          .res 256   ; file name        partition name (if FAT32, else empty)
attributes    .byte      ; file attributes  partition type
start         .dword     ; start cluster    start LBA
size          .dword     ; size in bytes    size in sectors
mtime_year    .byte
mtime_month   .byte
mtime_day     .byte
mtime_hours   .byte
mtime_minutes .byte
mtime_seconds .byte
.endstruct

; Maximum number of open files
; Optionally, fat32_alloc_context / fat32_free_context can be used to manage contexts
FAT32_CONTEXTS = 16

; Maximum number of partitions
FAT32_VOLUMES = 1

;-----------------------------------------------------------------------------
; errno
;-----------------------------------------------------------------------------
ERRNO_OK               = 0
ERRNO_READ             = 1
ERRNO_WRITE            = 2
ERRNO_ILLEGAL_FILENAME = 3
ERRNO_FILE_EXISTS      = 4
ERRNO_FILE_NOT_FOUND   = 5
ERRNO_FILE_READ_ONLY   = 6
ERRNO_DIR_NOT_EMPTY    = 7
ERRNO_NO_MEDIA         = 8
ERRNO_NO_FS            = 9
ERRNO_FS_INCONSISTENT  = 10
ERRNO_WRITE_PROTECT_ON = 11
ERRNO_OUT_OF_RESOURCES = 12

;-----------------------------------------------------------------------------
; Register bits
;-----------------------------------------------------------------------------
SPI_CTRL_SELECT_SDCARD = $01
SPI_CTRL_SELECT_MASK   = $01
SPI_CTRL_SLOWCLK       = $02
SPI_CTRL_AUTOTX        = $04
SPI_CTRL_BUSY          = $80
