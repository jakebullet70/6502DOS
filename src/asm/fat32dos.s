; The kernel's calls on the FAT32 library, in ROM bank 1. Bank 0 calls each by FARCALL.
;
; lib_open takes a path and gives a context; lib_read, lib_seek and lib_close take that context
; in A. Each returns carry set and A = the error, an ERR_ of api.inc, on a fault.
;
; The library has one volume: drive C:. Its current directory is set from the drive's DPB at
; each open, so fat.s keeps the current directories.

.setcpu "65C02"

.include "fat32_regs.inc"        ; and mem.inc
.include "api.inc"

.export lib_init, lib_open, lib_read, lib_seek, lib_close
.import fat32_init, fat32_alloc_context, fat32_free_context, fat32_set_context
.import fat32_chdir, fat32_open, fat32_read, fat32_seek, fat32_close, fat32_get_size
.import fat32_cwd, fat32_size, fat32_errno, fat32_readonly, skip_mask, sector_lba
.import DPB, current_drive
.importzp saved_bank, cluster, file_size

.segment "FATBSS"

lib_path:     .res 256          ; lib_open: the path, / for \, the drive left out, ended by 0
lib_len:      .res 1            ; lib_open: the length of the path at r0
lib_slash:    .res 1            ; lib_open: the index of the last / in lib_path, $FF when none
lib_dpb:      .res 1            ; lib_open: the DPB offset of the path's drive
lib_context:  .res 1

.segment "B1CODE"

; lib_init: clears the library's variables. The library writes nothing. RAM bank 0 must be
; selected. Changes A, X and Y.
lib_init:
        jsr fat32_init
        lda #1
        sta fat32_readonly
        stz skip_mask
        lda #$FF                ; no sector in the buffer: fat32_init sets the low byte only
        sta sector_lba+1
        sta sector_lba+2
        sta sector_lba+3
        rts

; lib_fault: returns carry set and A = the error of the library's errno, in the caller's bank.
lib_fault:
        jsr lib_errno
lib_error:
        sec
lib_bank:
        ldx saved_bank          ; keeps A and carry
        stx RAM_BANK
        rts

; lib_open: opens the file of the path at r0 for reading. A path with no drive is on the
; current drive. Returns carry clear, A = the context, file_size the size, and cluster to
; cluster+7 the SFT state of the file: the context, then 7 zeros. Selects RAM bank 0 while it
; runs and keeps the caller's bank in saved_bank. Changes X and Y.
lib_open:
        lda RAM_BANK
        sta saved_bank
        stz RAM_BANK
        jsr path_start
        bcs lib_error
        lda #0                  ; the volume
        jsr fat32_alloc_context
        bcc lib_fault
        sta lib_context
        jsr fat32_set_context
        bcc @drop
        lda lib_dpb
        ora #DPB_CWD
        tax
        ldy #0
@cwd:
        lda DPB,x
        sta fat32_cwd,y
        inx
        iny
        cpy #4
        bne @cwd
        ldx lib_slash
        inx
        beq @name               ; no directory
        dex
        beq @root
        stz lib_path,x          ; the directory ends at the last /
        lda #<lib_path
        sta fat32_ptr
        lda #>lib_path
        sta fat32_ptr+1
        jsr fat32_chdir
        bcs @name
        lda fat32_errno
        cmp #ERRNO_FILE_NOT_FOUND
        bne @drop
        lda #ERR_NO_PATH
        bra @drop_error
@root:
        stz fat32_cwd
        stz fat32_cwd+1
        stz fat32_cwd+2
        stz fat32_cwd+3
@name:
        ldx lib_slash           ; the name starts after the last /, or at 0
        inx
        txa
        clc
        adc #<lib_path
        sta fat32_ptr
        lda #>lib_path
        adc #0
        sta fat32_ptr+1
        jsr fat32_open
        bcc @drop
        jsr fat32_get_size
        ldx #3
@size:
        lda fat32_size,x
        sta file_size,x
        stz cluster,x
        stz cluster+4,x
        dex
        bpl @size
        lda lib_context
        sta cluster
        clc
        jmp lib_bank
@drop:
        jsr lib_errno
@drop_error:
        pha
        lda lib_context
        jsr fat32_free_context
        pla
        jmp lib_error

; path_start: checks the drive of the path at r0, sets lib_dpb, and copies the rest of the path
; to lib_path with path_copy. Returns carry set and A = the error. Changes X and Y.
path_start:
        ldy #0
        jsr path_char
        sta lib_len
        ldx current_drive
        ldy #1                  ; the first character after the drive
        cmp #2
        bcc @drive
        iny
        jsr path_char
        cmp #':'
        beq @letter
        ldy #1
        bra @drive
@letter:
        dey
        jsr path_char
        and #$DF                ; upper case
        sec
        sbc #'A'
        tax
        ldy #3
@drive:
        cpx #DRIVES
        bcs @bad_drive
        txa
        asl
        asl
        asl
        asl
        asl                     ; DPB_SIZE 32; carry clear
        sta lib_dpb
        tax
        lda DPB + DPB_DRIVER+1,x
        beq @bad_drive
        lda DPB + DPB_SHIFT,x
        bmi @not_ready
        jsr path_copy
        bcc @done
        lda #ERR_NOT_FOUND
        rts
@bad_drive:
        lda #ERR_BAD_DRIVE
        bra @fail
@not_ready:
        lda #ERR_NOT_READY
@fail:
        sec
@done:
        rts

; path_char: returns character Y of the path at r0, in RAM bank saved_bank. Changes A.
path_char:
        lda saved_bank
        sta RAM_BANK
        lda (r0),y
        stz RAM_BANK
        rts

; path_copy: copies the path at r0 from index Y to lib_path, with / for \, and ends it with 0.
; Sets lib_slash. Returns carry set when the path holds * or ?. Changes A, X and Y.
path_copy:
        ldx #$FF
        stx lib_slash
        inx
@char:
        dey
        cpy lib_len
        iny
        bcs @end                ; Y - 1 >= the length: past the last character
        jsr path_char
        cmp #'*'
        beq @wild
        cmp #'?'
        beq @wild
        cmp #'\'
        bne @put
        lda #'/'
@put:
        sta lib_path,x
        cmp #'/'
        bne @next
        stx lib_slash
@next:
        inx
        iny
        bne @char
@end:
        stz lib_path,x
        clc
        rts
@wild:
        sec
        rts

; lib_errno: returns A = the error of the library's errno. Changes X.
lib_errno:
        ldx fat32_errno
        lda errno_errors,x
        rts

; lib_read: reads r1 bytes of context A to r0. Returns r1 = the bytes read, fewer at the end of
; the file. RAM bank 0 must be selected, and saved_bank must be the bank of a buffer at
; $A000-$BFFF. Changes X and Y.
lib_read:
        ldx r1
        bne @read
        ldx r1+1
        beq @done               ; fat32_read takes 0 bytes as 256
@read:
        jsr fat32_set_context
        bcc lib_errno_set
        lda r0
        sta fat32_ptr
        lda r0+1
        sta fat32_ptr+1
        lda r1
        sta fat32_size
        lda r1+1
        sta fat32_size+1
        clc                     ; not a stream
        jsr fat32_read          ; carry clear at the end of the file
        lda fat32_size
        sta r1
        lda fat32_size+1
        sta r1+1
        lda fat32_errno
        bne lib_errno_set
@done:
        clc
        rts

; lib_errno_set: returns carry set and A = the error of the library's errno.
lib_errno_set:
        jsr lib_errno
        sec
        rts

; lib_seek: moves context A to the position in r0 and r1. A position past the end of the file
; stays at the end. RAM bank 0 must be selected. Changes X and Y.
lib_seek:
        jsr fat32_set_context
        bcc lib_errno_set
        ldx #3
@position:
        lda r0,x
        sta fat32_size,x
        dex
        bpl @position
        jsr fat32_seek
        bcc lib_errno_set
        clc
        rts

; lib_close: closes context A and frees it, even on a fault. RAM bank 0 must be selected.
; Changes X and Y.
lib_close:
        sta lib_context
        jsr fat32_set_context
        bcc @free
        jsr fat32_close
@free:
        php
        lda lib_context
        jsr fat32_free_context
        plp
        bcc lib_errno_set
        clc
        rts

; errno_errors: the error of each errno of the library.
errno_errors:
        .byte ERR_BAD_FUNCTION  ; ERRNO_OK: a call refused with no errno
        .byte ERR_READ_FAULT    ; ERRNO_READ
        .byte ERR_WRITE_FAULT   ; ERRNO_WRITE
        .byte ERR_NO_PATH       ; ERRNO_ILLEGAL_FILENAME
        .byte ERR_ACCESS        ; ERRNO_FILE_EXISTS
        .byte ERR_NOT_FOUND     ; ERRNO_FILE_NOT_FOUND
        .byte ERR_ACCESS        ; ERRNO_FILE_READ_ONLY
        .byte ERR_ACCESS        ; ERRNO_DIR_NOT_EMPTY
        .byte ERR_NOT_READY     ; ERRNO_NO_MEDIA
        .byte ERR_NOT_READY     ; ERRNO_NO_FS
        .byte ERR_READ_FAULT    ; ERRNO_FS_INCONSISTENT
        .byte ERR_WRITE_FAULT   ; ERRNO_WRITE_PROTECT_ON
        .byte ERR_TOO_MANY_FILES ; ERRNO_OUT_OF_RESOURCES
        .assert * - errno_errors = ERRNO_OUT_OF_RESOURCES + 1, error, "an error for each errno"
