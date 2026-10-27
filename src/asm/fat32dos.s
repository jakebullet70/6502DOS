; The kernel's calls on the FAT32 library, in ROM bank 1. Bank 0 calls each by FARCALL.
;
; lib_open takes a path and gives a context; lib_read, lib_seek and lib_close take that context
; in A, lib_io an SFT entry in Y. Each returns carry set and A = the error, an ERR_ of api.inc,
; on a fault. The gate calls api_findfirst, api_findnext, api_delete, api_rename, api_mkdir,
; api_rmdir, api_chdir, api_getcwd, api_diskfree, api_absread and api_abswrite here.
;
; The library has one volume: drive C:. It mounts the volume when a call first takes a context.
; Its current directory is set from the drive's DPB at each call, so the DPBs keep the current
; directories.

.setcpu "65C02"

.include "fat32_regs.inc"        ; and mem.inc
.include "api.inc"
.include "far.inc"

.export lib_init, lib_open, lib_read, lib_io, lib_seek, lib_close, api_findfirst, api_findnext
.export api_delete, api_rename, api_mkdir, api_rmdir, api_chdir, api_getcwd, api_diskfree
.export api_absread, api_abswrite
.export fat32_dir_pos
.import fat32_init, fat32_alloc_context, fat32_free_context, fat32_set_context
.import fat32_chdir, fat32_open, fat32_read, fat32_seek, fat32_close, fat32_get_size
.import fat32_create, fat32_write, fat32_write_byte
.import fat32_delete, fat32_rename, fat32_mkdir, fat32_rmdir, fat32_free_clusters
.import fat32_open_dir, fat32_read_dirent_filtered, fat32_tell_dir, fat32_seek_dir
.import fat32_open_tree, fat32_walk_tree
.import fat32_cwd, fat32_size, fat32_dirent, fat32_errno, fat32_readonly, skip_mask, sector_lba
.import fat32_root, fat32_sectors_per_cluster, fat32_cluster_count
.import sync_sector_buffer, sdcard_read_sector, sd_input, sd_output, jsrfar1
.import DPB, current_drive, create_attr
.importzp saved_bank, file_context, file_size

; The search state of a find buffer, before FIND_ATTR.
FIND_PATTERN  = 0               ; the name part of findfirst's path, ended by 0
FIND_SEARCH   = 33              ; findfirst's A
FIND_POS      = 34              ; the position after the entry found: fat32_tell_dir's 7 bytes
PATTERN_MAX   = 32
NAME_MAX      = 32
        .assert FIND_SEARCH = FIND_PATTERN + PATTERN_MAX + 1 && FIND_POS + 7 = FIND_ATTR, error, "the search state fills the bytes before FIND_ATTR"

.segment "FATBSS"

lib_path:     .res 256          ; lib_enter: the path, / for \, the drive left out, ended by 0
lib_len:      .res 1            ; lib_enter: the length of the path at r0
lib_slash:    .res 1            ; lib_enter: the index of the last / in lib_path, $FF when none
lib_wild:     .res 1            ; lib_enter: bit 7 set when the name part holds * or ?
lib_dpb:      .res 1            ; lib_enter: the DPB offset of the path's drive
lib_context:  .res 1
lib_access:   .res 1            ; lib_open: the access, 0 to read only
abs_write     = lib_access      ; api_absread, api_abswrite: bit 7 set to write
lib_entry:    .res 1            ; lib_io: the SFT entry
lib_gap:      .res 4            ; lib_write: the bytes from the end of the file to the position
lib_dir       = lib_gap         ; api_rename, api_rmdir: a directory's cluster
lib_new_dpb:  .res 1            ; api_rename: the DPB offset of the new path's drive
lib_find      = lib_path        ; findfirst, findnext: the find buffer, built here
lib_new       = RENAME_PATH     ; api_rename: the new path, as lib_path
fat32_dir_pos = lib_find + FIND_POS

.segment "B1CODE"

; lib_init: clears the library's variables. RAM bank 0 must be selected. Changes A, X and Y.
lib_init:
        jsr fat32_init
        stz fat32_readonly
        stz skip_mask
        lda #$FF                ; no sector in the buffer: fat32_init sets the low byte only
        sta sector_lba+1
        sta sector_lba+2
        sta sector_lba+3
        rts

; api_findfirst: findfirst, call 13. Selects RAM bank 0 while it runs and keeps the caller's
; bank in saved_bank.
api_findfirst:
        pha                     ; the attributes
        jsr lib_enter
        bcs @fail
        ldx lib_slash           ; the name part to FIND_PATTERN: lib_find is lib_path
        ldy #$FF
@pattern:
        inx
        iny
        lda lib_path,x
        sta lib_find + FIND_PATTERN,y
        beq @copied
        cpy #PATTERN_MAX
        bne @pattern
        pla
        bra @not_found
@copied:
        tya
        tax
        bne @clear
        lda #'*'                ; no name: every name
        sta lib_find + FIND_PATTERN
        inx
@clear:                         ; zeros after the pattern: lib_path leaves bytes there
        stz lib_find + FIND_PATTERN,x
        inx
        cpx #FIND_SEARCH
        bne @clear
        pla
        sta lib_find + FIND_SEARCH
        stz fat32_ptr           ; the current directory, which lib_enter set
        stz fat32_ptr+1
        jsr fat32_open_dir
        bcc lib_drop_errno
        jsr find_search
        bcc find_put
        cmp #ERR_NO_MORE_FILES
        bne lib_drop
@not_found:
        lda #ERR_NOT_FOUND
        bra lib_drop
@fail:
        plx                     ; keeps A and carry
        bra lib_bank

; api_findnext: findnext, call 14. Selects RAM bank 0 while it runs and keeps the caller's
; bank in saved_bank.
api_findnext:
        lda RAM_BANK
        sta saved_bank
        stz RAM_BANK
        ldy #FIND_ATTR - 1
@state:
        lda saved_bank
        sta RAM_BANK
        lda (r1),y
        stz RAM_BANK
        sta lib_find,y
        dey
        bpl @state
        lda #0                  ; the volume
        jsr fat32_alloc_context
        bcc lib_fault
        sta lib_context
        jsr fat32_set_context
        bcc lib_drop_errno
        jsr fat32_seek_dir
        bcc lib_drop_errno
        jsr find_search
        bcs lib_drop
        ; fall through

; find_put: copies lib_find up to the end of the name to the find buffer at r1, closes
; lib_context, and returns carry clear in the caller's bank.
find_put:
        lda lib_find + FIND_NAME
        clc
        adc #FIND_NAME
        tay
@copy:
        lda lib_find,y
        ldx saved_bank
        stx RAM_BANK
        sta (r1),y
        stz RAM_BANK
        dey
        bpl @copy
        lda lib_context
        jsr lib_close
        clc
        bra lib_bank

; lib_fault: returns carry set and A = the error of the library's errno, in the caller's bank.
lib_fault:
        jsr lib_errno
lib_error:
        sec
lib_bank:
        ldx saved_bank          ; keeps A and carry
        stx RAM_BANK
        rts

; lib_drop: closes and frees lib_context, then returns carry set and A = the error, in the
; caller's bank. lib_drop_errno takes the error of the library's errno.
lib_drop_errno:
        jsr lib_errno
lib_drop:
        pha
        lda lib_context
        jsr lib_close
        pla
        bra lib_error

; lib_no_path: lib_drop with ERR_NO_PATH.
lib_no_path:
        lda #ERR_NO_PATH
        bra lib_drop

; lib_done: closes and frees lib_context after a call of the library, which returns carry
; clear on a fault. Returns in the caller's bank, carry set and A = the error on a fault.
lib_done:
        bcc lib_drop_errno
        lda lib_context
        jsr lib_close
        bra lib_bank

; api_delete: delete, call 6. Selects RAM bank 0 while it runs and keeps the caller's bank in
; saved_bank.
api_delete:
        jsr lib_enter
        bcs lib_bank
        jsr name_check
        lda #ERR_NOT_FOUND      ; keeps carry
        bcs lib_drop
        jsr fat32_delete
        bra lib_done

; api_mkdir: mkdir, call 15. Selects RAM bank 0 while it runs and keeps the caller's bank in
; saved_bank.
api_mkdir:
        jsr lib_enter
        bcs lib_bank
        jsr name_check
        bcs lib_no_path
        jsr fat32_mkdir
        bra lib_done

; lib_open: opens the file of the path at r0 with access A: 0 read, 1 write, 2 read and write.
; With carry set it creates the file with the attributes create_attr, or empties it when it
; exists. A path with no drive is on the current drive. Returns carry clear, A = the context,
; and file_context to file_size the SFT state of the file: the context, the position 0 and the
; size. Access 1 or 2 on a read-only file gives ERR_ACCESS. Selects RAM bank 0 while it runs
; and keeps the caller's bank in saved_bank. Changes X and Y.
lib_open:
        php
        pha
        jsr lib_enter
        plx                     ; the access
        ply                     ; the flags: carry in bit 0
        bcs lib_bank
        stx lib_access
        tya
        lsr
        bcs @create
        bit lib_wild
        bpl @open
        lda #ERR_NOT_FOUND
        bra lib_drop
@open:
        jsr fat32_open
        bcc lib_drop_errno
        lda lib_access
        beq @opened
        lda fat32_dirent + dirent::attributes
        and #ATTR_READ_ONLY
        beq @opened
        lda #ERR_ACCESS
        bra lib_drop
@create:
        jsr name_check
        bcs lib_no_path
        lda create_attr
        and #ATTR_READ_ONLY | ATTR_HIDDEN | ATTR_SYSTEM | ATTR_ARCHIVE
        sec                     ; empty a file that exists
        jsr fat32_create
        bcc lib_drop_errno
@opened:
        jsr fat32_get_size
        ldx #3
@size:
        lda fat32_size,x
        sta file_size,x
        stz file_context+1,x    ; the position
        dex
        bpl @size
        lda lib_context
        sta file_context
        clc
        jmp lib_bank

; api_rmdir: rmdir, call 17. The current directory of the path's drive gives ERR_CURRENT_DIR.
; A \ at the end of the path is left out. Selects RAM bank 0 while it runs and keeps the
; caller's bank in saved_bank.
api_rmdir:
        jsr lib_take
        bcs @bank
        jsr path_trim
        jsr lib_split
        bcs @bank
        jsr name_check
        lda #ERR_NO_PATH        ; keeps carry
        bcs @drop
        ldx #3
@parent:
        lda fat32_cwd,x
        sta lib_dir,x
        dex
        bpl @parent
        jsr dir_change          ; fat32_cwd = the directory's cluster
        bcs @drop
        lda lib_dpb
        ora #DPB_CWD
        tax
        ldy #0
@current:
        lda DPB,x
        cmp fat32_cwd,y
        bne @other
        inx
        iny
        cpy #4
        bne @current
        lda #ERR_CURRENT_DIR
        bra @drop
@other:
        ldx #3
@back:
        lda lib_dir,x
        sta fat32_cwd,x
        dex
        bpl @back
        jsr fat32_rmdir
        jmp lib_done
@bank:
        jmp lib_bank
@drop:
        jmp lib_drop

; api_chdir: chdir, call 18. Selects RAM bank 0 while it runs and keeps the caller's bank in
; saved_bank.
api_chdir:
        jsr lib_enter
        bcs @bank
        bit lib_wild
        bmi @no_path
        lda (fat32_ptr)         ; the name part
        beq @set                ; the path ends at a separator
        jsr dir_change
        bcs @drop
@set:
        jsr cwd_build           ; getcwd must be able to return the path
        bcs @drop
        ldx lib_dpb
        ldy #0
@byte:
        lda fat32_cwd,y
        sta DPB + DPB_CWD,x
        inx
        iny
        cpy #4                  ; carry set at the end
        bne @byte
        jmp lib_done
@bank:
        jmp lib_bank
@no_path:
        lda #ERR_NO_PATH
@drop:
        jmp lib_drop

; api_rename: rename, call 7. Checks the directories of both paths, then hands the library both
; paths from the current directory. A directory moved to another directory gives ERR_ACCESS.
; Selects RAM bank 0 while it runs and keeps the caller's bank in saved_bank.
api_rename:
        lda r0+1                ; the old path, for later
        pha
        lda r0
        pha
        lda r1
        sta r0
        lda r1+1
        sta r0+1
        jsr lib_enter           ; the new path
        ply                     ; keeps carry
        sty r0
        ply
        sty r0+1
        bcs @bank
        jsr name_check
        lda #ERR_NO_PATH        ; keeps carry
        bcs @drop
        lda lib_dpb
        sta lib_new_dpb
        ldx #3
@new_dir:
        lda fat32_cwd,x
        sta lib_dir,x
        dex
        bpl @new_dir
        jsr path_join
        ldx #0
@copy:
        lda lib_path,x
        sta lib_new,x
        inx
        bne @copy
        lda lib_context
        jsr lib_close
        lda saved_bank          ; lib_enter keeps the bank it finds
        sta RAM_BANK
        jsr lib_enter           ; the old path
        bcs @bank
        jsr name_check
        lda #ERR_NOT_FOUND      ; keeps carry
        bcs @drop
        lda lib_dpb
        cmp lib_new_dpb
        beq @same_drive
        lda #ERR_NOT_SAME_DEVICE
        bra @drop
@same_drive:
        ldx #3
@same:
        lda fat32_cwd,x
        cmp lib_dir,x
        bne @moved
        dex
        bpl @same
        bra @rename
@moved:
        jsr fat32_chdir         ; carry set: the old name is a directory
        lda #ERR_ACCESS         ; keeps carry
        bcs @drop
@rename:
        jsr cwd_set
        jsr path_join
        lda #<lib_path
        sta fat32_ptr
        lda #>lib_path
        sta fat32_ptr+1
        lda #<lib_new
        sta fat32_ptr2
        lda #>lib_new
        sta fat32_ptr2+1
        jsr fat32_rename
        jmp lib_done
@bank:
        jmp lib_bank
@drop:
        jmp lib_drop

; api_diskfree: diskfree, call 22. The free clusters are the FS info sector's count, which the
; library keeps. Selects RAM bank 0 while it runs and keeps the caller's bank in saved_bank.
api_diskfree:
        jsr drive_enter
        bcs @bank
        lda #0                  ; the volume: a context mounts it
        jsr fat32_alloc_context
        bcs @mounted
        jmp lib_fault
@mounted:
        jsr fat32_free_context
        ldx #3
@free:
        lda fat32_free_clusters,x
        sta r1,x                ; r1 and r2
        dex
        bpl @free
        lda fat32_sectors_per_cluster
        sta r0
        stz r0+1
        stz r3
        lda #>512
        sta r3+1
        lda fat32_cluster_count ; r4 and r5: the clusters from cluster 2
        sec
        sbc #2
        sta r4
        ldx #1
@clusters:
        lda fat32_cluster_count,x
        sbc #0
        sta r4,x
        inx
        txa
        eor #4                  ; keeps carry
        bne @clusters
        clc
@bank:
        jmp lib_bank

; api_absread: absread, call 53. api_abswrite: abswrite, call 54. Moves X sectors between the
; buffer at r0, in the caller's RAM bank, and the unit of drive A, from sector r1 r2. Writes the
; library's dirty sector first; after a write, reads the library's sector again. Selects RAM
; bank 0 while it runs and keeps the caller's bank in saved_bank.
api_abswrite:
        sec
        bra abs_io
api_absread:
        clc
abs_io:
        ldy RAM_BANK
        sty saved_bank
        stz RAM_BANK
        ror abs_write           ; carry to bit 7
        cpx #1                  ; a count of 0 moves nothing; carry clear
        bcc @bank
        stx BLK_COUNT
        tax                     ; the drive
        sbc #FIRST_DRIVE        ; carry set
        sta BLK_UNIT            ; the unit once drive_check passes: C: is unit 0
        jsr drive_check
        bcs @bank
        jsr sync_sector_buffer
        bcc @write_fault
        ldx #3
@sector:
        lda r1,x                ; r1 and r2
        sta BLK_SECTOR,x
        dex
        bpl @sector
        lda r0
        sta BLK_BUFFER
        lda r0+1
        sta BLK_BUFFER+1
        ldy saved_bank          ; the driver moves the bytes in the selected bank
        bit abs_write
        sty RAM_BANK            ; keeps N
        bmi @write
        FARCALL sd_input, jsrfar1
        bra @moved
@write:
        FARCALL sd_output, jsrfar1
@moved:
        stz RAM_BANK            ; keeps carry
        bcs @bank
        bit abs_write
        bpl @bank
        lda sector_lba+3        ; $FF: no sector in the buffer
        inc
        beq @bank
        jsr sdcard_read_sector  ; the write may have changed it
        lda #ERR_READ_FAULT
        bcc @fault
        clc
@bank:
        jmp lib_bank
@write_fault:
        lda #ERR_WRITE_FAULT
@fault:
        jmp lib_error

; api_getcwd: getcwd, call 19. Copies the path cwd_build makes to r0. Selects RAM bank 0 while
; it runs and keeps the caller's bank in saved_bank.
api_getcwd:
        jsr drive_enter
        bcs @bank
        lda #0                  ; the volume
        jsr fat32_alloc_context
        bcs @taken
        jmp lib_fault
@taken:
        sta lib_context
        jsr fat32_set_context
        bcc @fault
        jsr cwd_set
        jsr cwd_build
        bcs @drop
        ldy #0
@copy:
        lda lib_path,x
        phx
        ldx saved_bank
        stx RAM_BANK
        sta (r0),y
        stz RAM_BANK
        plx
        iny
        inx
        bne @copy
        sec
        jmp lib_done
@bank:
        jmp lib_bank
@fault:
        jmp lib_drop_errno
@drop:
        jmp lib_drop

; cwd_build: builds the path of the library's current directory at the end of lib_path, a \
; and a name for each directory from the current one up to the root, with the length where the
; first \ is. Uses context lib_context. Returns X = the index of the length, or carry set and
; A = the error, ERR_NO_PATH when the path is over 254 characters. lib_len holds the index of
; the path's first \, 0 while the path is empty. Changes Y.
cwd_build:
        jsr fat32_open_tree
        stz lib_len
@level:
        jsr fat32_walk_tree     ; the entry of the directory, in its parent
        bcc @fault
        lda fat32_dirent + dirent::name
        cmp #'/'                ; the root
        beq @root
        ldx #$FF
@length:
        inx
        lda fat32_dirent + dirent::name,x
        bne @length
        txa                     ; A = lib_len - the length - 1: the new \
        eor #$FF
        clc
        adc lib_len
        bcs @room
        ldy lib_len             ; 0: the path is empty, and 256 bytes are free
        bne @long
@room:
        tay
        beq @long               ; index 0 would read as the empty path
        sta lib_len
        lda #'\'
        sta lib_path,y
        ldx #0
@name:
        iny
        lda fat32_dirent + dirent::name,x
        beq @level
        sta lib_path,y
        inx
        bra @name
@root:
        ldx lib_len
        bne @path
        dex                     ; the empty path: its length goes in the last byte
@path:
        txa
        eor #$FF                ; the length: 255 - the index
        sta lib_path,x
        clc
        rts
@fault:
        jmp lib_errno_set
@long:
        lda #ERR_NO_PATH
        sec
        rts

; lib_enter: selects RAM bank 0 and keeps the caller's bank in saved_bank, takes the path at r0
; with path_start, takes the context lib_context, makes the path's directory the library's
; current directory, and points fat32_ptr at the name part. Returns carry set and A = the error,
; with no context taken. Changes X and Y.
lib_enter:
        jsr lib_take
        bcc lib_split
        rts

; lib_split: lib_enter after lib_take.
lib_split:
        lda #0                  ; the volume
        jsr fat32_alloc_context
        bcs @taken
        jmp lib_errno_set
@taken:
        sta lib_context
        jsr fat32_set_context
        bcc @drop
        jsr cwd_set
        ldx lib_slash
        inx
        beq @entered            ; no directory
        dex
        beq @root
        stz lib_path,x          ; the directory ends at the last /
        lda #<lib_path
        sta fat32_ptr
        lda #>lib_path
        sta fat32_ptr+1
        jsr dir_change
        bcs @drop_error
        bra @entered
@root:
        jsr cwd_root
@entered:
        ldx lib_slash           ; fat32_ptr = the name, after the last / or at 0
        inx
        txa
        clc
        adc #<lib_path
        sta fat32_ptr
        lda #>lib_path
        adc #0
        sta fat32_ptr+1
        clc
        rts
@drop:
        jsr lib_errno
@drop_error:
        pha
        lda lib_context
        jsr lib_close
        pla
        sec
        rts

; lib_take: selects RAM bank 0, keeps the caller's bank in saved_bank, and takes the path at r0
; with path_start. Returns carry set and A = the error. Changes X and Y.
lib_take:
        lda RAM_BANK
        sta saved_bank
        stz RAM_BANK
        jmp path_start

; path_trim: leaves out the / at the end of lib_path, unless it is the root's, and sets
; lib_slash to the / before it, $FF when none. Changes A and X.
path_trim:
        ldx lib_slash
        beq @done               ; the root's /
        inx
        beq @done               ; no /
        lda lib_path,x
        bne @done               ; a name after the last /
        dex
        stz lib_path,x
@back:
        dex
        cpx #$FF
        beq @set
        lda lib_path,x
        cmp #'/'
        bne @back
@set:
        stx lib_slash
@done:
        rts

; cwd_set: makes the current directory of drive lib_dpb the library's, with cluster 0 for the
; root, as a .. entry holds it. The volume must be mounted. Changes A, X and Y.
cwd_set:
        lda lib_dpb
        ora #DPB_CWD + 3
        tax
        ldy #3
@root:
        lda DPB,x
        sta fat32_cwd,y
        cmp fat32_root,y
        bne @copy
        dex
        dey
        bpl @root
        bra cwd_root
@copy:                          ; the bytes below the one that differs
        dex
        dey
        bmi @done
        lda DPB,x
        sta fat32_cwd,y
        bra @copy
@done:
        rts

; cwd_root: makes the root the library's current directory. Changes nothing else.
cwd_root:
        stz fat32_cwd
        stz fat32_cwd+1
        stz fat32_cwd+2
        stz fat32_cwd+3
        rts

; dir_change: makes the directory at fat32_ptr the library's current directory. Returns carry
; set and A = the error, ERR_NO_PATH when the directory is missing. Changes X and Y.
dir_change:
        jsr fat32_chdir
        bcc @fault
        clc
        rts
@fault:
        lda fat32_errno
        cmp #ERRNO_FILE_NOT_FOUND
        bne lib_errno_set
        lda #ERR_NO_PATH
        sec
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

; lib_io: reads (X = 1) or writes (X = 0) r1 bytes between r0 and the file of the library at
; SFT entry Y, and moves the entry's position on by the bytes moved. Returns r1 = the bytes
; moved. RAM bank 0 must be selected, and saved_bank must be the bank of a buffer at
; $A000-$BFFF. Changes X and Y.
lib_io:
        sty lib_entry
        lda SFT + SFT_CONTEXT,y
        dex
        bne @write
        jsr lib_read
        bra @moved
@write:
        jsr lib_write
@moved:
        bcs @done
        ldy lib_entry
        lda SFT + SFT_POS,y
        adc r1                  ; carry clear
        sta SFT + SFT_POS,y
        lda SFT + SFT_POS+1,y
        adc r1+1
        sta SFT + SFT_POS+1,y
        bcc @done
        lda SFT + SFT_POS+2,y
        adc #0
        sta SFT + SFT_POS+2,y
        lda SFT + SFT_POS+3,y
        adc #0
        sta SFT + SFT_POS+3,y
        clc
@done:
        rts

; lib_write: writes r1 bytes from r0 to context A at the position of SFT entry lib_entry, and
; sets the entry's size. A position past the end of the file first takes zeros up to it. A full
; drive stops the write early, with no error. Returns r1 = the bytes written. RAM bank 0 must be
; selected, and saved_bank must be the bank of a buffer at $A000-$BFFF. Changes X and Y.
lib_write:
        jsr fat32_set_context
        bcc @fault
        jsr fat32_get_size      ; lib_gap = the position - the size
        ldy lib_entry
        ldx #0
        sec
@gap:
        lda SFT + SFT_POS,y
        sbc fat32_size,x
        sta lib_gap,x
        iny
        inx
        txa
        eor #4                  ; keeps carry
        bne @gap
        bcc @data               ; the position is inside the file
@fill:
        lda lib_gap
        ora lib_gap+1
        ora lib_gap+2
        ora lib_gap+3
        beq @data
        lda #0
        jsr fat32_write_byte
        bcc @short
        ldx #$FF
@borrow:
        inx
        dec lib_gap,x
        lda lib_gap,x
        inc
        beq @borrow             ; $FF: the byte was 0
        bra @fill
@fault:
        jmp lib_errno_set
@short:                         ; nothing of r1 written
        lda r1
        sta fat32_size
        lda r1+1
        sta fat32_size+1
        bra @stopped
@data:
        lda r1
        ora r1+1
        beq @written            ; fat32_write takes 0 bytes as 256
        lda r0
        sta fat32_ptr
        lda r0+1
        sta fat32_ptr+1
        lda r1
        sta fat32_size
        lda r1+1
        sta fat32_size+1
        clc                     ; not a stream
        jsr fat32_write         ; fat32_size = the bytes not written
@stopped:
        php
        sec
        lda r1
        sbc fat32_size
        sta r1
        lda r1+1
        sbc fat32_size+1
        sta r1+1
        plp
        bcs @written
        lda fat32_errno         ; a full drive sets no errno
        bne @fault
@written:
        jsr fat32_get_size
        ldy lib_entry
        ldx #0
@size:
        lda fat32_size,x
        sta SFT + SFT_FILE_SIZE,y
        iny
        inx
        cpx #4
        bne @size
        clc
        rts

; find_search: finds the next entry of the directory open in lib_context whose name matches
; the pattern at lib_find and whose attributes pass, and fills lib_find from it. Returns carry
; set and A = the error, ERR_NO_MORE_FILES at the end of the directory. Changes X and Y.
find_search:
        lda #<lib_find
        sta fat32_ptr
        lda #>lib_find
        sta fat32_ptr+1
@next:
        jsr fat32_read_dirent_filtered
        bcc @end
        lda lib_find + FIND_SEARCH ; directories, hidden and system files need their bit in A
        eor #$FF
        and fat32_dirent + dirent::attributes
        and #ATTR_HIDDEN | ATTR_SYSTEM | ATTR_DIR
        bne @next
        jsr fat32_tell_dir
        sec
        lda fat32_bufptr        ; the entry: fat32_read_dirent moved past it
        sbc #32
        sta fat32_ptr2
        lda fat32_bufptr+1
        sbc #0
        sta fat32_ptr2+1
        ldy #DIR_TIME           ; the time and the date
@time:
        lda (fat32_ptr2),y
        sta lib_find + FIND_TIME - DIR_TIME,y
        iny
        cpy #DIR_TIME + 4
        bne @time
        lda fat32_dirent + dirent::attributes
        sta lib_find + FIND_ATTR
        ldx #3
@size:
        lda fat32_dirent + dirent::size,x
        sta lib_find + FIND_SIZE,x
        dex
        bpl @size
        inx                     ; 0
@name:
        lda fat32_dirent + dirent::name,x
        beq @named
        sta lib_find + FIND_NAME + 1,x
        inx
        cpx #NAME_MAX
        bne @name
@named:
        stx lib_find + FIND_NAME
        clc
        rts
@end:
        lda fat32_errno
        beq @no_more
        jmp lib_errno_set
@no_more:
        lda #ERR_NO_MORE_FILES
        sec
        rts
        .assert FIND_DATE = FIND_TIME + 2, error, "find_search copies the time and the date"

; lib_errno: returns A = the error of the library's errno. Changes X.
lib_errno:
        ldx fat32_errno
        lda errno_errors,x
        rts

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
        jsr drive_check
        bcs @done
        jsr path_copy
        bcc @done
        lda #ERR_NO_PATH
@done:
        rts

; drive_enter: selects RAM bank 0 and keeps the caller's bank in saved_bank, then does
; drive_check on drive A, 0 for the current drive, 1 for A:. Changes A and X.
drive_enter:
        ldx RAM_BANK
        stx saved_bank
        stz RAM_BANK
        dec                     ; 0, the current drive, becomes $FF
        bpl @drive
        lda current_drive
@drive:
        tax
        ; fall through

; drive_check: sets lib_dpb to the DPB offset of drive X, 0 for A:. Returns carry set and A =
; ERR_BAD_DRIVE when the drive does not exist. A drive with no file system gives its error when
; the call takes a context. Changes A and X.
drive_check:
        cpx #DRIVES
        bcs @bad_drive
        txa
        asl
        asl
        asl                     ; DPB_SIZE 8; carry clear
        sta lib_dpb
        tax
        lda DPB + DPB_DRIVER+1,x
        beq @bad_drive
        rts
@bad_drive:
        lda #ERR_BAD_DRIVE
        sec
        rts
        .assert DPB_SIZE = 8, error, "drive_check multiplies by 8"

; path_char: returns character Y of the path at r0, in RAM bank saved_bank. Changes A.
path_char:
        lda saved_bank
        sta RAM_BANK
        lda (r0),y
        stz RAM_BANK
        rts

; path_copy: copies the path at r0 from index Y to lib_path, with / for \, and ends it with 0.
; Sets lib_slash and lib_wild. Returns carry set when a directory part holds * or ?. Changes A,
; X and Y.
path_copy:
        ldx #$FF
        stx lib_slash
        inx
        stz lib_wild
@char:
        dey
        cpy lib_len
        iny
        bcs @end                ; Y - 1 >= the length: past the last character
        jsr path_char
        cmp #'*'
        beq @wild
        cmp #'?'
        bne @slash
@wild:
        sec                     ; keeps A
        ror lib_wild
@slash:
        cmp #'\'
        bne @put
        lda #'/'
@put:
        sta lib_path,x
        cmp #'/'
        bne @next
        stx lib_slash
        bit lib_wild
        bmi @wild_directory
@next:
        inx
        iny
        bne @char
@end:
        stz lib_path,x
        clc
        rts
@wild_directory:
        sec
        rts

; name_check: returns carry set when the name part of lib_path is blank, only dots, over
; NAME_MAX characters, or holds * or ?. Changes A and X.
name_check:
        bit lib_wild
        bmi @bad
        ldx lib_slash
@char:
        inx
        lda lib_path,x
        beq @bad
        cmp #'.'
        beq @char
@end:
        inx
        lda lib_path,x
        bne @end
        txa                     ; the length: the end - lib_slash - 1
        clc
        sbc lib_slash
        cmp #NAME_MAX + 1       ; carry set over NAME_MAX
        rts
@bad:
        sec
        rts

; path_join: puts back the / that lib_enter ended the directory part with. Changes A and X.
path_join:
        ldx lib_slash
        inx
        beq @done               ; no /
        lda #'/'
        sta lib_path - 1,x
@done:
        rts

; errno_errors: the error of each errno of the library.
errno_errors:
        .byte ERR_ACCESS        ; ERRNO_OK: a full drive, or a call refused with no errno
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
