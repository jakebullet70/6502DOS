; Drives, paths and FAT32: the drive table, the sector buffer, path parsing, directory search,
; findfirst and findnext, file reads, writes, creation, deletion and renaming, directories, and
; the free space of a drive.
;
; A drive's DPB holds its block driver and unit and the layout of its FAT32 file system. A
; directory is read as a chain like a file, 32 bytes an entry: cluster holds the byte at pos.
; Names are 8.3 and upper case.
;
; A file's cluster is 0 when not known: after an open or a seek. The next read or write walks
; the chain from file_first. After that, cluster holds the byte before pos, and a read or write
; steps to the next cluster when pos is at the start of one. A write past the end of the chain
; adds clusters.
;
; The sector buffer is written back before another sector is read into it, and at each close of
; a file. A FAT sector is written to each FAT.
;
; Each drive keeps the first cluster of its current directory, and no path text: getcwd finds
; the names through the .. entries. . and .. in a path are the directory's own entries; the
; root directory has none, and there both name the root.

.setcpu "65C02"

.include "mem.inc"
.include "api.inc"
.include "far.inc"

.export drives_init, drives_add, path_last, file_find, file_create, file_io, file_close
.export file_copy, create_attr
.export api_getdrive, api_setdrive, api_chdir, api_getcwd
.export api_seek, api_delete, api_rename, api_mkdir, api_rmdir, api_diskfree
.export DPB, current_drive
.exportzp fcb_name, cluster, dpb, file_size
.import drv_call, bank0, bank_restore, sft_find, io_start, io_done, to_upper
.importzp driver, io_ptr, io_left
.import jsrfar, lib_seek, sector_lba

.segment "KERNELZP" : zeropage

; Keep the order from cluster to entry_ptr: an SFT entry holds them. Keep lba and ptr in order:
; entry_keep copies them.
dpb:          .res 1            ; the DPB offset of the drive in use: drive * DPB_SIZE
search_attr:  .res 1            ; the attributes dir_search takes
fcb_name:     .res 11           ; a name: 8 and 3 characters, padded with spaces; ? matches any
cluster:      .res 4
pos:          .res 4
file_size:    .res 4
file_first:   .res 4
entry_sector: .res 4            ; the sector of a file's directory entry
entry_ptr:    .res 2            ; the entry in SECTOR_BUFFER
lba:          .res 4            ; a sector number
ptr:          .res 2            ; a byte in SECTOR_BUFFER
free_next:    .res 4            ; the next cluster cluster_free looks at, on any drive
chunk:        .res 1           ; file_copy: the bytes it copies from the buffer page, minus 1
        .assert SFT_POS - SFT_CLUSTER = pos - cluster && SFT_FIRST - SFT_CLUSTER = file_first - cluster, error, "the SFT state follows the zero page order"
        .assert SFT_ENTRY - SFT_CLUSTER = entry_sector - cluster && SFT_STATE = entry_ptr + 2 - cluster, error, "the SFT state follows the zero page order"
        .assert ptr = lba + 4 && entry_ptr = entry_sector + 4, error, "entry_keep copies lba and ptr"

.segment "KERNELRAM"

DPB:          .res DRIVES * DPB_SIZE
buf_sector:   .res 4            ; the sector in SECTOR_BUFFER
buf_drive:    .res 1            ; its DPB offset, $FF when the buffer holds none
buf_dirty:    .res 1            ; the copies of the buffer to write back: 0, 1, or DPB_FATS
writing:      .res 1            ; bit 7: a cluster chain grows at its end; bit 6: a new cluster is zeroed
free_pass:    .res 1            ; cluster_free: 1 after it went back to cluster 2
walk:         .res 3            ; cluster_at: the clusters to step
create_attr:  .res 1            ; file_create: the attributes; ATTR_DIR makes a directory
entry_copy:   .res 21           ; rename: bytes 11 to 31 of the directory entry
rename_drive: .res 1            ; rename: the dpb of the old path
current_drive: .res 1
next_dpb:     .res 1            ; drives_add: the DPB of the next drive letter
add_unit:     .res 1
add_units:    .res 1
path_len:     .res 1
path_index:   .res 1            ; the path index of the last character read
path_drive:   .res 1
fcb_limit:    .res 1            ; the end of the fcb_name field being filled
sft_entry:    .res 1

.segment "CODE"

; drives_init: clears the drive table and the sector buffer. Changes A and X.
drives_init:
        ldx #DRIVES * DPB_SIZE - 1
@clear:
        stz DPB,x
        dex
        bpl @clear
        lda #$FF
        sta buf_drive
        stz buf_dirty
        stz writing
        lda #FIRST_DRIVE
        sta current_drive
        lda #FIRST_DRIVE * DPB_SIZE
        sta next_dpb
        rts
        .assert DRIVES * DPB_SIZE <= 128, error, "drives_init counts X down with BPL"

; drives_add: gives each unit of the block driver at driver the next drive letter and mounts
; it. Changes A, X and Y.
drives_add:
        ldy #DRV_NAME
        lda (driver),y
        sta add_units
        stz add_unit
@unit:
        lda add_unit
        cmp add_units
        bcs @done
        lda next_dpb
        cmp #DRIVES * DPB_SIZE
        bcs @done
        sta dpb
        tax
        lda driver
        sta DPB + DPB_DRIVER,x
        lda driver+1
        sta DPB + DPB_DRIVER+1,x
        lda add_unit
        sta DPB + DPB_UNIT,x
        jsr mount
        lda dpb
        clc
        adc #DPB_SIZE
        sta next_dpb
        inc add_unit
        bra @unit
@done:
        rts

; mount: finds the first FAT32 partition in the partition table of the drive at dpb and fills
; its DPB. DPB_SHIFT stays $FF when there is none. Changes A, X and Y.
mount:
        ldx dpb
        lda #$FF
        sta DPB + DPB_SHIFT,x
        stz lba
        stz lba+1
        stz lba+2
        stz lba+3
        jsr read_sector
        bcs @done
        ldx #$C2                ; the type of partition 1, at $1C2
@partition:
        lda SECTOR_BUFFER + $100,x
        cmp #$0B                ; FAT32
        beq @found
        cmp #$0C                ; FAT32 with LBA
        beq @found
        txa
        clc
        adc #16
        tax
        bcc @partition          ; after partition 4
@done:
        rts
@found:
        ldy #0                  ; the partition's first sector
@first:
        lda SECTOR_BUFFER + $104,x
        sta lba,y
        inx
        iny
        cpy #4
        bne @first
        jsr read_sector         ; its boot sector
        bcs @done
        lda SECTOR_BUFFER + $0B ; bytes per sector: 512
        bne @done
        lda SECTOR_BUFFER + $0C
        cmp #2
        bne @done
        lda SECTOR_BUFFER + $0D ; sectors per cluster
        beq @done
        ldy #$FF
@log:
        iny
        lsr
        bcc @log
        phy                     ; DPB_SHIFT is stored last
        clc                     ; the FAT follows the reserved sectors
        lda lba
        adc SECTOR_BUFFER + $0E
        sta lba
        lda lba+1
        adc SECTOR_BUFFER + $0F
        sta lba+1
        bcc @fat
        inc lba+2
        bne @fat
        inc lba+3
@fat:
        lda dpb
        ora #DPB_FAT
        tax
        jsr lba_store
        ldx dpb
        ldy #0
@fat_size:
        lda SECTOR_BUFFER + $24,y
        sta DPB + DPB_FAT_SIZE,x
        inx
        iny
        cpy #4
        bne @fat_size
        ldx dpb
        lda SECTOR_BUFFER + $10 ; the number of FATs
        sta DPB + DPB_FATS,x
        tay
@fats:                          ; the data area follows the FATs
        ldx #0
        clc
@add:
        lda lba,x
        adc SECTOR_BUFFER + $24,x
        sta lba,x
        inx
        txa
        eor #4                  ; keeps carry
        bne @add
        dey
        bne @fats
        ldx dpb
        lda SECTOR_BUFFER + $0D
        asl
        dec
        sta DPB + DPB_CMASK,x
        clc                     ; cluster 0 is 2 clusters before the data area
        lda lba
        sbc DPB + DPB_CMASK,x   ; carry clear: minus CMASK + 1
        sta lba
        lda lba+1
        sbc #0
        sta lba+1
        lda lba+2
        sbc #0
        sta lba+2
        lda lba+3
        sbc #0
        sta lba+3
        txa
        ora #DPB_BASE
        tax
        jsr lba_store
        ldx dpb                 ; DPB_LIMIT: (the partition's end - DPB_BASE) >> DPB_SHIFT
        ldy #0
        clc
@end:                           ; buf_sector: the partition's first sector
        lda buf_sector,y
        adc SECTOR_BUFFER + $20,y
        sta DPB + DPB_LIMIT,x
        inx
        iny
        tya
        eor #4                  ; keeps carry
        bne @end
        ldx dpb
        ldy #0
        sec
@less:
        lda DPB + DPB_LIMIT,x
        sbc lba,y
        sta DPB + DPB_LIMIT,x
        inx
        iny
        tya
        eor #4                  ; keeps carry
        bne @less
        pla                     ; DPB_SHIFT
        pha
        tay
        beq @limit
        ldx dpb
@clusters:
        lsr DPB + DPB_LIMIT+3,x
        ror DPB + DPB_LIMIT+2,x
        ror DPB + DPB_LIMIT+1,x
        ror DPB + DPB_LIMIT,x
        dey
        bne @clusters
@limit:
        ldx dpb
        ldy #0
@root:
        lda SECTOR_BUFFER + $2C,y
        sta DPB + DPB_ROOT,x
        sta DPB + DPB_CWD,x
        inx
        iny
        cpy #4
        bne @root
        ldx dpb
        pla
        sta DPB + DPB_SHIFT,x
        rts

; lba_store: copies lba to the 4 bytes at DPB + X. Changes A, X and Y.
lba_store:
        ldy #0
@copy:
        lda lba,y
        sta DPB,x
        inx
        iny
        cpy #4
        bne @copy
        rts

; lba_add: adds the 4 bytes at DPB + X to lba. Changes A, X and Y.
lba_add:
        ldy #0
        clc
@byte:
        lda lba,y
        adc DPB,x
        sta lba,y
        inx
        iny
        tya
        eor #4                  ; keeps carry
        bne @byte
        rts

; read_sector: reads sector lba of the drive at dpb into SECTOR_BUFFER, unless the buffer holds
; it. Writes the buffer back first. Returns carry set and A = the error when the driver fails.
; Changes A, X and Y.
read_sector:
        lda dpb
        cmp buf_drive
        bne @read
        ldx #3
@same:
        lda lba,x
        cmp buf_sector,x
        bne @read
        dex
        bpl @same
        clc
        rts
@read:
        jsr buf_flush
        bcs @done
        ldx #3
@copy:
        lda lba,x
        sta buf_sector,x
        sta BLK_SECTOR,x
        dex
        bpl @copy
        ldx dpb
        jsr blk_request
        lda #$FF                ; no sector until the read succeeds
        sta buf_drive
        ldy #DRV_INPUT
        jsr drv_call
        bcs @done
        lda dpb
        sta buf_drive
@done:
        rts

; api_mkdir makes the directory through file_create, then writes the buffer back.
api_mkdir:
        lda #ATTR_DIR
        sta create_attr
        jsr file_create
        bcc buf_flush
        rts

; buf_flush: writes the buffer back when buf_dirty says so, to each FAT for a FAT sector.
; Returns carry set and A = the error on a fault: the buffer then holds no sector. Changes A, X
; and Y.
buf_flush:
        clc
        lda buf_dirty
        beq @done
        ldx #3
@copy:
        lda buf_sector,x
        sta BLK_SECTOR,x
        dex
        bpl @copy
@write:
        ldx buf_drive
        jsr blk_request
        ldy #DRV_OUTPUT
        jsr drv_call
        bcs @fault
        jsr lib_forget
        dec buf_dirty
        beq @done               ; carry clear
        ldx buf_drive           ; the next FAT
        ldy #0
        clc
@next:
        lda BLK_SECTOR,y
        adc DPB + DPB_FAT_SIZE,x
        sta BLK_SECTOR,y
        inx
        iny
        tya
        eor #4                  ; keeps carry
        bne @next
        bra @write
@fault:
        ldx #$FF
        stx buf_drive
        stz buf_dirty
@done:
        rts

; lib_forget: empties the FAT32 library's sector buffer, which may hold a sector fat.s wrote.
; Changes A and X.
lib_forget:
        ldx RAM_BANK
        stz RAM_BANK
        lda #$FF
        sta sector_lba
        sta sector_lba+1
        sta sector_lba+2
        sta sector_lba+3
        stx RAM_BANK
        rts

; buf_claim: makes the buffer sector lba of the drive at dpb, to be written back, without
; reading it. Changes A and X.
buf_claim:
        ldx #3
@copy:
        lda lba,x
        sta buf_sector,x
        dex
        bpl @copy
        lda dpb
        sta buf_drive
        lda #1
        sta buf_dirty
        rts

; blk_request: sets the block request for one sector to or from SECTOR_BUFFER on the drive at
; DPB offset X, and points driver at its driver. Changes A.
blk_request:
        lda DPB + DPB_UNIT,x
        sta BLK_UNIT
        lda DPB + DPB_DRIVER,x
        sta driver
        lda DPB + DPB_DRIVER+1,x
        sta driver+1
        lda #1
        sta BLK_COUNT
        lda #<SECTOR_BUFFER
        sta BLK_BUFFER
        lda #>SECTOR_BUFFER
        sta BLK_BUFFER+1
        rts

; cursor_sector: reads the sector that holds pos in cluster and points ptr at pos in it.
; Returns carry set and A = the error on a fault. Changes A, X and Y.
cursor_sector:
        ldx dpb
        lda pos+1               ; the sector within the cluster
        and DPB + DPB_CMASK,x
        lsr
        jsr cluster_lba
        jsr read_sector
        bcs @done
        lda pos
        sta ptr
        lda pos+1
        and #1
        ora #>SECTOR_BUFFER
        sta ptr+1
@done:
        rts
        .assert <SECTOR_BUFFER = 0 && >SECTOR_BUFFER & 1 = 0, error, "cursor_sector ORs pos into ptr"

; cluster_lba: lba = sector A of the cluster at cluster, on the drive at dpb. Changes A, X and Y.
cluster_lba:
        pha
        ldx #3
@copy:
        lda cluster,x
        sta lba,x
        dex
        bpl @copy
        ldx dpb
        ldy DPB + DPB_SHIFT,x
        beq @sector
@shift:
        asl lba
        rol lba+1
        rol lba+2
        rol lba+3
        dey
        bne @shift
@sector:
        pla                     ; the sector fills the low bits
        ora lba
        sta lba
        txa
        ora #DPB_BASE
        tax
        jmp lba_add

; cluster_step: called when pos is at the start of a sector. Moves cluster to the next cluster
; of the chain when pos is at the start of a cluster. Returns carry set and A = the error on a
; fault. Changes A, X and Y.
cluster_step:
        ldx dpb
        lda pos+1
        and DPB + DPB_CMASK,x
        beq next_cluster
        clc
        rts

; next_cluster: moves cluster to the next cluster of its chain. At the end of the chain it adds
; a cluster when writing has bit 7 set, else it leaves cluster at the end mark, $0Fxxxxxx.
; Returns carry set and A = the error on a fault. Changes A, X and Y.
next_cluster:
        ldx #cluster
        jsr fat_entry
        bcs @done
        ldy #3
        lda (ptr),y
        and #$0F                ; FAT32 entries are 28 bits
        cmp #$0F                ; the end of the chain: $0FFFFFF8 and up
        bcc @copy
        bit writing
        bmi cluster_add
@copy:
        sta cluster+3
        ldy #2
@byte:
        lda (ptr),y
        sta cluster,y
        dey
        bpl @byte
        clc
@done:
        rts

; cluster_add: takes a free cluster and ends the chain there. Links it after cluster, or makes
; it file_first when cluster is 0. Zeroes it when writing has bit 6 set. Returns cluster = the
; new cluster. Returns carry set and A = ERR_ACCESS when the drive is full, or the error of a
; fault. Changes A, X and Y.
cluster_add:
        jsr cluster_free
        bcs @done
        ldy #3                  ; the end of the chain; the top 4 bits stay
        lda (ptr),y
        ora #$0F
        sta (ptr),y
        lda #$FF
@end:
        dey
        sta (ptr),y
        bne @end
        jsr fat_dirty
        lda cluster
        ora cluster+1
        ora cluster+2
        ora cluster+3
        beq @first
        ldx #cluster
        jsr fat_entry
        bcs @done
        ldy #3
        lda (ptr),y
        and #$F0
        ora free_next+3
        sta (ptr),y
        dey
@link:
        lda free_next,y
        sta (ptr),y
        dey
        bpl @link
        jsr fat_dirty
        bra @move
@first:
        ldx #3
@copy_first:
        lda free_next,x
        sta file_first,x
        dex
        bpl @copy_first
@move:
        ldx #3
@copy:
        lda free_next,x
        sta cluster,x
        dex
        bpl @copy
        inc free_next
        bne @zero
        inc free_next+1
        bne @zero
        inc free_next+2
        bne @zero
        inc free_next+3
@zero:
        bit writing
        bvs cluster_zero
        clc
@done:
        rts

; cluster_free: finds a free cluster from free_next on, going back to cluster 2 once, and points
; free_next and ptr at it. Returns carry set and A = ERR_ACCESS when the drive has none, or the
; error of a fault. Changes A, X and Y.
cluster_free:
        stz free_pass
@check:
        ldx dpb                 ; free_next < DPB_LIMIT
        lda free_next
        cmp DPB + DPB_LIMIT,x
        lda free_next+1
        sbc DPB + DPB_LIMIT+1,x
        lda free_next+2
        sbc DPB + DPB_LIMIT+2,x
        lda free_next+3
        sbc DPB + DPB_LIMIT+3,x
        bcc @entry
        lda free_pass
        bne @full
        inc free_pass
        lda #2                  ; FAT entries 0 and 1 are never free
        sta free_next
        stz free_next+1
        stz free_next+2
        stz free_next+3
@entry:
        ldx #free_next
        jsr fat_entry
        bcs @done
        ldy #3
        lda (ptr),y
        and #$0F
        ldy #2
@zero:
        ora (ptr),y
        dey
        bpl @zero
        tax
        beq @done               ; carry clear, from fat_entry
        inc free_next
        bne @check
        inc free_next+1
        bne @check
        inc free_next+2
        bne @check
        inc free_next+3
        bra @check
@full:
        lda #ERR_ACCESS
        sec
@done:
        rts

; cluster_zero: writes zeros to each sector of the cluster at cluster. The buffer then holds its
; last sector. Returns carry set and A = the error on a fault. Changes A, X and Y.
cluster_zero:
        jsr buf_flush
        bcs @done
        ldx #0
@clear:
        stz SECTOR_BUFFER,x
        stz SECTOR_BUFFER + $100,x
        inx
        bne @clear
        lda #0
        jsr cluster_lba
        ldx dpb
        lda DPB + DPB_CMASK,x   ; the sectors of a cluster, minus 1
        lsr
        sta chunk
@sector:
        jsr buf_claim
        jsr buf_flush
        bcs @done
        inc lba
        bne @next
        inc lba+1
        bne @next
        inc lba+2
        bne @next
        inc lba+3
@next:
        dec chunk
        bpl @sector
        clc
@done:
        rts

; chain_free: frees the chain from the cluster at cluster. Returns carry set and A = the error
; on a fault. Changes A, X and Y, and cluster.
chain_free:
        lda cluster+3
        cmp #$0F                ; the end of the chain
        bcs @end
        ora cluster+2
        ora cluster+1
        ora cluster
        beq @end
        ldx #cluster
        jsr fat_entry
        bcs @done
        ldy #3                  ; the next cluster to cluster, 0 to the entry; the top 4 bits stay
        lda (ptr),y
        and #$0F
        sta cluster+3
        lda (ptr),y
        and #$F0
        sta (ptr),y
        dey
@byte:
        lda (ptr),y
        sta cluster,y
        lda #0
        sta (ptr),y
        dey
        bpl @byte
        jsr fat_dirty
        bra chain_free
@end:
        clc
@done:
        rts

; fat_dirty: marks the buffer, a FAT sector, to be written to each FAT. Changes A and X.
fat_dirty:
        ldx dpb
        lda DPB + DPB_FATS,x
        sta buf_dirty
        rts

; fat_entry: reads the FAT sector that holds the entry of the cluster at zero page X, on the
; drive at dpb, and points ptr at the entry. Returns carry set and A = the error on a fault.
; Keeps X. Changes A and Y.
fat_entry:
        lda 0,x                 ; the FAT sector: cluster / 128
        asl
        lda 1,x
        rol
        sta lba
        lda 2,x
        rol
        sta lba+1
        lda 3,x
        rol
        sta lba+2
        lda #0
        rol
        sta lba+3
        phx
        lda dpb
        ora #DPB_FAT
        tax
        jsr lba_add
        jsr read_sector
        plx
        bcs @done
        lda 0,x                 ; the entry: (cluster & 127) * 4
        asl
        asl
        sta ptr
        lda #>SECTOR_BUFFER
        adc #0
        sta ptr+1
@done:
        rts

; cluster_at: makes cluster hold the byte at pos of a file, before it is read or written. Walks
; the chain from file_first when cluster is 0, else steps when pos is at the start of a
; cluster. Returns carry set and A = the error on a fault. Changes A, X and Y.
cluster_at:
        lda cluster
        ora cluster+1
        ora cluster+2
        ora cluster+3
        beq @walk
        lda pos
        bne @here
        ldx dpb
        lda pos+1
        and DPB + DPB_CMASK,x
        bne @here
        jmp next_cluster
@walk:
        lda pos+3               ; walk = pos >> 9 >> DPB_SHIFT
        lsr
        sta walk+2
        lda pos+2
        ror
        sta walk+1
        lda pos+1
        ror
        sta walk
        ldx dpb
        ldy DPB + DPB_SHIFT,x
        beq @first
@shift:
        lsr walk+2
        ror walk+1
        ror walk
        dey
        bne @shift
@first:
        ldx #3
@copy:
        lda file_first,x
        sta cluster,x
        dex
        bpl @copy
        ora cluster+1
        ora cluster+2
        ora cluster+3
        bne @step
        bit writing             ; an empty file; a read never gets here
        bpl @step
        jsr cluster_add
        bcs @done
@step:
        lda walk
        ora walk+1
        ora walk+2
        beq @here
        jsr next_cluster
        bcs @done
        lda walk
        bne @low
        lda walk+1
        bne @middle
        dec walk+2
@middle:
        dec walk+1
@low:
        dec walk
        bra @step
@here:
        clc
@done:
        rts

; cluster_cwd: sets cluster to the current directory of the drive at dpb. Returns carry
; clear. Changes A, X and Y.
cluster_cwd:
        lda #DPB_CWD + 3
        bra cluster_field

; cluster_root: sets cluster to the root directory of the drive at dpb. Returns carry clear.
; Changes A, X and Y.
cluster_root:
        lda #DPB_ROOT + 3
cluster_field:
        ora dpb
        tax
        ldy #3
@copy:
        lda DPB,x
        sta cluster,y
        dex
        dey
        bpl @copy
        clc
        rts

; entry_cluster: sets cluster to the first cluster of the directory entry at ptr. Cluster 0,
; as in a ".." entry, is the root directory. Changes A, X and Y.
entry_cluster:
        ldy #DIR_CLUSTER_LOW
        lda (ptr),y
        sta cluster
        iny
        lda (ptr),y
        sta cluster+1
        ldy #DIR_CLUSTER_HIGH
        lda (ptr),y
        sta cluster+2
        iny
        lda (ptr),y
        sta cluster+3
        ora cluster+2
        ora cluster+1
        ora cluster
        beq cluster_root
        rts

; dir_first: dir_search from the first entry of the directory at cluster.
dir_first:
        stz pos
        stz pos+1
        stz pos+2
        stz pos+3
        ; fall through

; dir_search: finds the first entry from pos on whose name matches fcb_name and whose
; attributes pass search_attr. Returns carry clear and ptr at the entry. Returns carry set and
; A = ERR_NO_MORE_FILES at the end of the directory, or another error. Changes A, X and Y.
dir_search:
        jsr cursor_sector
        bcs @done
        lda (ptr)
        beq @end                ; no entries follow
        cmp #$E5                ; deleted
        beq @next
        ldy #DIR_ATTR
        lda (ptr),y
        cmp #ATTR_LONG_NAME
        beq @next
        lda search_attr         ; hidden, system, label and directory need their bit in A
        eor #$FF
        and (ptr),y
        and #ATTR_HIDDEN | ATTR_SYSTEM | ATTR_LABEL | ATTR_DIR
        bne @next
        ldy #10
@char:
        lda fcb_name,y
        cmp #'?'
        beq @match
        cmp (ptr),y
        bne @next
@match:
        dey
        bpl @char
        clc
@done:
        rts
@next:
        jsr dir_step
        bcc dir_search
        rts
@end:
        lda #ERR_NO_MORE_FILES
        sec
        rts

; dir_step: moves pos to the next directory entry. Returns carry set and A =
; ERR_NO_MORE_FILES after the last cluster of the directory, or another error. Changes A, X
; and Y.
dir_step:
        lda pos
        clc
        adc #32
        sta pos
        bcc @same
        inc pos+1               ; a directory never reaches 64 KB
        lda pos+1
        lsr
        bcs @same               ; the second half of the sector
        jsr cluster_step
        bcs @done
        lda cluster+3
        cmp #$0F                ; the end of the chain: $0FFFFFF8 and up
        bcc @done
        lda #ERR_NO_MORE_FILES
@done:
        rts
@same:
        clc
        rts

; drive_ready: drive_exists, and returns carry set and A = ERR_NOT_READY when the drive has no
; file system. Changes A and X.
drive_ready:
        jsr drive_exists
        bcs @done
        lda DPB + DPB_SHIFT,x
        bpl @done               ; carry clear
        lda #ERR_NOT_READY
        sec
@done:
        rts

; drive_exists: makes drive A the drive at dpb, and X = dpb. Returns carry set and A =
; ERR_BAD_DRIVE when the drive does not exist. Changes A and X.
drive_exists:
        cmp #DRIVES
        bcs @bad
        asl
        asl
        asl
        asl
        asl                     ; carry clear
        sta dpb
        tax
        lda DPB + DPB_DRIVER+1,x
        bne @done
@bad:
        lda #ERR_BAD_DRIVE
        sec
@done:
        rts
        .assert DPB_SIZE = 32, error, "drive_exists multiplies by 32"

; next_char: returns the next character of the path at r0 in A, with Y its index. Returns
; carry set at the end of the path.
next_char:
        cpy path_len
        bcs @end
        iny
        lda (r0),y
        clc
@end:
        rts

; is_separator: returns Z set when A is \ or /.
is_separator:
        cmp #'\'
        beq @done
        cmp #'/'
@done:
        rts

; path_start: reads the drive of the path at r0 into path_drive, the current drive when it
; has none, and moves path_index past the drive and one separator. Changes A and Y.
path_start:
        lda (r0)
        sta path_len
        lda current_drive
        sta path_drive
        ldy #0
        lda path_len
        cmp #2
        bcc @separator
        ldy #2
        lda (r0),y
        cmp #':'
        beq @drive
        ldy #0
        bra @separator
@drive:
        dey
        lda (r0),y
        jsr to_upper
        sec
        sbc #'A'
        sta path_drive
        iny
@separator:
        jsr next_char
        bcs @done
        jsr is_separator
        beq @done
        dey                     ; not a separator: read it again
@done:
        sty path_index
        rts

; fcb_fill: fills fcb_name with A. Returns X = $FF.
fcb_fill:
        ldx #10
@fill:
        sta fcb_name,x
        dex
        bpl @fill
        rts

; is_dots: returns Z set when fcb_name is . or .. Changes A.
is_dots:
        lda fcb_name
        cmp #'.'
        bne @done
        lda fcb_name+2
        cmp #' '
        bne @done
        lda fcb_name+1
        cmp #' '
        beq @done
        cmp #'.'
@done:
        rts

; component: reads the path from path_index to the next separator into fcb_name. A * fills the
; rest of its field with ?. Dots at the start of the name stay in it, for . and .. Returns
; carry clear when a separator ended it, carry set at the end of the path. Changes A, X and Y.
component:
        lda #' '
        jsr fcb_fill
        inx
        lda #8
        sta fcb_limit
        ldy path_index
@char:
        jsr next_char
        bcs @end
        jsr is_separator
        beq @separator
        cmp #'.'
        beq @dot
        cmp #'*'
        beq @star
        cpx fcb_limit
        bcs @char               ; the field is full: drop the character
        jsr to_upper
@put:
        sta fcb_name,x
        inx
        bra @char
@star:
        lda #'?'
@fill:
        cpx fcb_limit
        bcs @char
        sta fcb_name,x
        inx
        bra @fill
@dot:
        cpx #8
        bcs @extension
        txa
        beq @literal
        lda fcb_name-1,x
        cmp #'.'
        bne @extension
@literal:
        lda #'.'
        bra @put
@extension:
        ldx #8
        lda #11
        sta fcb_limit
        bra @char
@separator:
        clc
@end:
        sty path_index
        rts

; path_last: puts the last part of the path at r0 in fcb_name. Changes A, X and Y.
path_last:
        jsr path_start
@part:
        jsr component
        bcc @part
        rts

; path_walk: finds the directory that holds the last part of the path at r0. A path that
; starts with a separator starts at the root, any other at the current directory. Returns
; carry clear, dpb at its drive, cluster at the directory and fcb_name the last part. Returns
; carry set and A = the error. Changes A, X and Y.
path_walk:
        jsr path_start
        lda path_drive
        jsr drive_ready
        bcs @done
        jsr cluster_cwd
        ldy path_index          ; 0, or the index of the separator path_start passed
        beq @part
        lda (r0),y
        jsr is_separator
        bne @part
        jsr cluster_root
@part:
        jsr component
        bcs @last
        jsr dir_enter
        bcc @part
        rts
@last:
        clc
@done:
        rts

; dir_enter: moves cluster to the directory that fcb_name names in the directory at cluster.
; Returns carry set and A = the error. Changes A, X and Y.
dir_enter:
        lda #ATTR_DIR | ATTR_HIDDEN | ATTR_SYSTEM
        sta search_attr
        jsr dir_first
        bcs @missing
        ldy #DIR_ATTR
        lda (ptr),y
        and #ATTR_DIR
        beq @no_path
        jmp entry_cluster       ; carry clear
@missing:
        cmp #ERR_NO_MORE_FILES
        bne @fail
        jsr is_dots             ; . and .. are missing only from the root
        bne @no_path
        jmp cluster_root
@no_path:
        lda #ERR_NO_PATH
@fail:
        sec
        rts

; name_check: returns carry set when fcb_name is blank, starts with a dot or holds a ?. Changes
; A and X.
name_check:
        lda fcb_name
        cmp #' '
        beq @done               ; carry set
        cmp #'.'
        beq @done
        ldx #10
@char:
        lda fcb_name,x
        cmp #'?'
        beq @done
        dex
        bpl @char
        clc
@done:
        rts

; entry_keep: keeps lba and ptr, the sector and the address of a directory entry, in
; entry_sector and entry_ptr. Changes A and X.
entry_keep:
        ldx #5
@copy:
        lda lba,x
        sta entry_sector,x
        dex
        bpl @copy
        rts

; entry_load: reads the sector at entry_sector and points ptr at entry_ptr. Returns carry set
; and A = the error on a fault. Changes A, X and Y.
entry_load:
        ldx #5
@copy:
        lda entry_sector,x
        sta lba,x
        dex
        bpl @copy
        jmp read_sector

; file_find: finds the file of the path at r0. Returns carry clear, A = its attributes, dpb at
; its drive, file_first at its first cluster, file_size its size, entry_sector and entry_ptr at
; its directory entry, and cluster and pos 0. Returns carry set and A = the error. Clears
; writing. Changes A, X and Y.
file_find:
        stz writing
        jsr path_walk
        bcs @done
        jsr name_check
        bcs @not_found
        lda #ATTR_HIDDEN | ATTR_SYSTEM
        sta search_attr
        jsr dir_first
        bcc @found
        cmp #ERR_NO_MORE_FILES
        bne @fail
@not_found:
        lda #ERR_NOT_FOUND
@fail:
        sec
@done:
        rts
@found:
        jsr entry_keep
        ldy #DIR_FILE_SIZE + 3
@size:
        lda (ptr),y
        sta file_size - DIR_FILE_SIZE,y
        dey
        cpy #DIR_FILE_SIZE - 1
        bne @size
        ldx #3
@first:
        ldy cluster_fields,x
        lda (ptr),y
        sta file_first,x
        stz pos,x
        stz cluster,x
        dex
        bpl @first
        ldy #DIR_ATTR
        lda (ptr),y
        clc
        rts

; file_create: creates the file of the path at r0 with the attributes create_attr, or empties
; it when it exists. Returns what file_find returns, for the empty file, but A. Returns carry
; set and A = ERR_NO_PATH for a name that is blank or has a wildcard, ERR_ACCESS for a
; directory, a read-only file or a full drive, or another error. With ATTR_DIR in create_attr
; it makes a directory instead, and any name that exists gives ERR_ACCESS. The buffer then
; holds the new entry, not yet written back. Changes A, X and Y.
file_create:
        stz writing
        jsr path_walk
        bcs @done
        jsr name_check
        bcc @named
@no_path:
        lda #ERR_NO_PATH
@fail:
        sec
@done:
        rts
@denied:
        lda #ERR_ACCESS
        bra @fail
@named:
        ldx #3                  ; file_first keeps the directory: the search moves cluster
@keep:
        lda cluster,x
        sta file_first,x
        dex
        bpl @keep
        lda #ATTR_HIDDEN | ATTR_SYSTEM | ATTR_DIR
        sta search_attr
        jsr dir_first
        bcc @exists
        cmp #ERR_NO_MORE_FILES
        bne @fail
        ldx #3
@back:
        lda file_first,x
        sta cluster,x
        dex
        bpl @back
        lda #$C0                ; a full directory grows by a zeroed cluster
        sta writing
        jsr dir_slot
        stz writing
        bcs @fail
        jsr entry_keep
        lda create_attr
        and #ATTR_DIR
        beq @fill
        jsr dir_make
        bcs @fail
        jsr entry_load
        bcc @fill
        rts
@exists:
        ldy #DIR_ATTR
        lda create_attr         ; a directory to make: any entry refuses it
        and #ATTR_DIR
        ora (ptr),y
        and #ATTR_READ_ONLY | ATTR_DIR
        bne @denied
        jsr entry_keep
        ldx #3
@first:
        ldy cluster_fields,x
        lda (ptr),y
        sta cluster,x
        dex
        bpl @first
        jsr chain_free
        bcs @fail
        jsr entry_load
        bcs @fail
@fill:                          ; the name, the attributes, then 0: no clock, no cluster, size 0
        lda #0
        ldy #31
@zero:
        sta (ptr),y
        dey
        cpy #DIR_ATTR
        bne @zero
        lda create_attr
        and #ATTR_READ_ONLY | ATTR_HIDDEN | ATTR_SYSTEM | ATTR_DIR | ATTR_ARCHIVE
        sta (ptr),y
@name:
        dey
        lda fcb_name,y
        sta (ptr),y
        tya
        bne @name
        lda create_attr
        and #ATTR_DIR
        beq @dirty
        ldx #3                  ; a directory: its first cluster
@cluster:
        ldy cluster_fields,x
        lda file_first,x
        sta (ptr),y
        dex
        bpl @cluster
@dirty:
        lda #1
        sta buf_dirty
        ldx #15                 ; cluster, pos, file_size and file_first
@state:
        stz cluster,x
        dex
        bpl @state
        clc
        rts
        .assert file_first + 4 - cluster = 16, error, "file_create clears cluster to file_first"

; dir_make: takes a zeroed cluster for a new directory in the directory at file_first, and puts
; its . and .. entries in the buffer, to be written back. Returns file_first = the new cluster.
; Returns carry set and A = ERR_ACCESS when the drive is full, or the error of a fault. Changes
; A, X and Y.
dir_make:
        ldx #3                  ; file_size = the parent, 0 for the root
@parent:
        lda file_first,x
        sta cluster,x
        sta file_size,x
        dex
        bpl @parent
        jsr is_root
        bne @new
        ldx #3
@root:
        stz file_size,x
        dex
        bpl @root
@new:
        ldx #3                  ; cluster 0: cluster_add starts a chain at file_first
@clear:
        stz cluster,x
        dex
        bpl @clear
        lda #$40
        sta writing
        jsr cluster_add
        stz writing
        bcs @done
        lda #0                  ; the buffer holds zeros: it becomes the first sector
        jsr cluster_lba
        jsr buf_claim
        ldx #10
@names:
        lda #' '
        sta SECTOR_BUFFER,x
        sta SECTOR_BUFFER + 32,x
        dex
        bpl @names
        lda #'.'
        sta SECTOR_BUFFER
        sta SECTOR_BUFFER + 32
        sta SECTOR_BUFFER + 33
        lda #ATTR_DIR
        sta SECTOR_BUFFER + DIR_ATTR
        sta SECTOR_BUFFER + 32 + DIR_ATTR
        ldx #3
@clusters:
        ldy cluster_fields,x
        lda cluster,x
        sta SECTOR_BUFFER,y
        lda file_size,x
        sta SECTOR_BUFFER + 32,y
        dex
        bpl @clusters
        clc
@done:
        rts

; is_root: returns Z set when cluster is the root directory of the drive at dpb. Changes A, X
; and Y.
is_root:
        lda #DPB_ROOT + 3
        ; fall through

; cluster_is: returns Z set when cluster equals the DPB field that ends at A of the drive at
; dpb. Changes A, X and Y.
cluster_is:
        ora dpb
        tax
        ldy #3
@byte:
        lda cluster,y
        cmp DPB,x
        bne @done
        dex
        dey
        bpl @byte
        iny                     ; Y = 0: Z set
@done:
        rts

; dir_slot: finds the first unused or deleted entry of the directory at cluster and points ptr
; at it. When writing is $C0, a full directory grows by a zeroed cluster. Returns carry set and
; A = the error. Changes A, X and Y.
dir_slot:
        stz pos
        stz pos+1
        stz pos+2
        stz pos+3
@entry:
        jsr cursor_sector
        bcs @done
        lda (ptr)
        beq @done               ; carry clear
        cmp #$E5
        beq @found
        jsr dir_step
        bcc @entry
@done:
        rts
@found:
        clc
        rts

; file_io: the read (A = 0) or write (A = $80) call for a file, entered with RAM bank 0 selected
; and Y = the offset of its SFT entry. Moves r1 bytes between r0 and the file. Returns r1 = the
; bytes moved, and the caller's bank.
file_io:
        sta writing
        sty sft_entry
        lda SFT + SFT_FLAGS,y
        sta dpb
        ldx #0
@load:
        lda SFT + SFT_CLUSTER,y
        sta cluster,x
        iny
        inx
        cpx #SFT_ENTRY - SFT_CLUSTER
        bne @load
        jsr bank_restore
        jsr file_copy
        bcs @fault
        jsr bank0
        ldy sft_entry
        ldx #0
        lda writing
        beq @store
        sta SFT + SFT_MODIFIED,y
@store:                         ; cluster, pos, file_size and file_first
        lda cluster,x
        sta SFT + SFT_CLUSTER,y
        iny
        inx
        cpx #SFT_ENTRY - SFT_CLUSTER
        bne @store
        clc
        jsr bank_restore
@fault:
        stz writing
        rts

; file_close: the close call for a file, entered with RAM bank 0 selected and Y = the offset of
; its SFT entry. The directory entry of a written file takes its size, its first cluster and
; the archive bit. Then the buffer is written back. Returns the caller's bank, and carry set and
; A = the error on a fault.
file_close:
        lda SFT + SFT_MODIFIED,y
        beq @flush
        lda #0
        sta SFT + SFT_MODIFIED,y
        lda SFT + SFT_FLAGS,y
        sta dpb
        ldx #0
@load:                          ; file_size, file_first, entry_sector and entry_ptr
        lda SFT + SFT_FILE_SIZE,y
        sta file_size,x
        iny
        inx
        cpx #SFT_STATE - (SFT_FILE_SIZE - SFT_CLUSTER)
        bne @load
        jsr bank_restore
        jsr entry_load
        bcs @done
        ldy #DIR_FILE_SIZE + 3
@size:
        lda file_size - DIR_FILE_SIZE,y
        sta (ptr),y
        dey
        cpy #DIR_FILE_SIZE - 1
        bne @size
        ldx #3
@first:
        ldy cluster_fields,x
        lda file_first,x
        sta (ptr),y
        dex
        bpl @first
        ldy #DIR_ATTR
        lda (ptr),y
        ora #ATTR_ARCHIVE
        sta (ptr),y
        lda #1
        sta buf_dirty
        jmp buf_flush
@flush:
        jsr bank_restore
        jmp buf_flush
@done:
        rts

; file_copy: moves r1 bytes between r0 and the file at dpb, cluster, pos, file_size and
; file_first: reads when writing is 0, writes when it is $80. A read stops at the end of the
; file. A write past the end makes the file longer, and stops when the drive is full. Returns
; r1 = the bytes moved, and the file's state after them. Returns carry set and A = the error on
; a fault. Changes A, X and Y.
file_copy:
        jsr io_start
        bit writing
        bmi @chunk
        sec                     ; lba = the bytes left in the file
        ldx #0
@left:
        lda file_size,x
        sbc pos,x
        sta lba,x
        inx
        txa
        eor #4                  ; keeps carry
        bne @left
        bcs @inside             ; a position past the size reads 0 bytes
        stz io_left
        stz io_left+1
@inside:
        lda lba+2
        ora lba+3
        bne @count              ; 64 KB or more
        lda lba
        cmp io_left
        lda lba+1
        sbc io_left+1
        bcs @count
        lda lba
        sta io_left
        lda lba+1
        sta io_left+1
@count:
        lda io_left
        sta r1
        lda io_left+1
        sta r1+1
@chunk:
        jsr io_done
        bne @more
        jmp @done
@more:
        jsr cluster_at
        bcs @stop
        jsr cursor_sector
        bcs @stop               ; a fault: @stop passes it on
        lda pos                 ; chunk = the bytes to the end of the buffer page, minus 1,
        eor #$FF                ; or io_left - 1 when that is less
        ldx io_left+1
        bne @take
        ldx io_left
        dex
        stx chunk
        cmp chunk
        bcc @take
        txa
@take:
        sta chunk
        tax
        inx                     ; the bytes to copy, 0 for 256
        ldy #0
        bit writing
        bmi @write
@copy:
        lda (ptr),y
        sta (io_ptr),y
        iny
        dex
        bne @copy
        bra @moved
@write:
        lda (io_ptr),y
        sta (ptr),y
        iny
        dex
        bne @write
        lda #1
        sta buf_dirty
@moved:
        sec                     ; io_ptr += chunk + 1
        lda io_ptr
        adc chunk
        sta io_ptr
        bcc @less
        inc io_ptr+1
@less:
        clc                     ; io_left -= chunk + 1
        lda io_left
        sbc chunk
        sta io_left
        bcs @ahead
        dec io_left+1
@ahead:
        sec                     ; pos += chunk + 1
        lda pos
        adc chunk
        sta pos
        bcc @chunk
        inc pos+1
        bne @chunk
        inc pos+2
        bne @chunk
        inc pos+3
        bra @chunk
@stop:
        cmp #ERR_ACCESS         ; the drive is full: r1 = the bytes written
        bne @fault
        stz cluster             ; a walk may have stopped short of pos
        stz cluster+1
        stz cluster+2
        stz cluster+3
        sec
        lda r1
        sbc io_left
        sta r1
        lda r1+1
        sbc io_left+1
        sta r1+1
@done:
        bit writing
        bpl @end
        sec                     ; file_size = pos when pos is past it
        ldx #0
@past:
        lda file_size,x
        sbc pos,x
        inx
        txa
        eor #4                  ; keeps carry
        bne @past
        bcs @end
        ldx #3
@grow:
        lda pos,x
        sta file_size,x
        dex
        bpl @grow
@end:
        clc
@fault:
        rts

; api_seek: moves handle X by the signed offset in r0 and r1 from the start (A = 0), the
; position (1) or the end (2). Returns r0 and r1 = the new position. A position may pass the
; end; a read there gives 0 bytes. A device stays at 0. The next read or write finds the
; cluster; a file of the FAT32 library moves its context.
api_seek:
        cmp #3
        bcc @from
        lda #ERR_BAD_FUNCTION
@fail:
        rts
@device:
        stz r0
        stz r0+1
        stz r1
        stz r1+1
        clc
        jmp bank_restore
@from:
        sta chunk
        jsr sft_find            ; bank 0
        bcs @fail
        lda SFT + SFT_FLAGS,y
        bmi @device
        sty sft_entry
        ldx chunk
        beq @set
        tya
        ora seek_base-1,x
        tay
        clc                     ; r0 and r1 += the position or the size
        ldx #0
@add:
        lda SFT,y
        adc r0,x
        sta r0,x
        iny
        inx
        txa
        eor #4                  ; keeps carry
        bne @add
@set:
        ldy sft_entry
        lda SFT + SFT_CLUSTER,y
        pha                     ; a file of the library: its context
        ldx #0
@store:
        lda r0,x
        sta SFT + SFT_POS,y
        lda #0
        sta SFT + SFT_CLUSTER,y
        iny
        inx
        cpx #4
        bne @store
        ldy sft_entry
        pla
        tax
        lda SFT + SFT_FLAGS,y
        lsr                     ; SFT_LIB
        bcc @done
        txa
        sta SFT + SFT_CLUSTER,y
        FARCALL lib_seek
        bcc @done
        pha
        jsr bank_restore
        pla
        rts
@done:
        jmp bank_restore        ; carry clear

seek_base:
        .byte SFT_POS, SFT_FILE_SIZE

api_getdrive:
        lda current_drive
        clc
        rts

api_setdrive:
        tay
        jsr drive_exists
        bcs @done
        sty current_drive
        lda #DRIVES
@done:
        rts

api_chdir:
        jsr path_walk
        bcs @done
        lda fcb_name
        cmp #' '
        beq @set                ; the path ends at a separator, or names no directory
        jsr dir_enter
        bcs @done
@set:
        lda dpb
        ora #DPB_CWD + 3
        tax
        ldy #3
@copy:
        lda cluster,y
        sta DPB,x
        dex
        dey
        bpl @copy
        clc
@done:
        rts

; api_delete deletes a file: directories are not found.
api_delete:
        jsr file_find
        bcs @done
        and #ATTR_READ_ONLY
        beq entry_drop
        lda #ERR_ACCESS
        sec
@done:
        rts

; entry_drop: marks the directory entry at entry_sector deleted, frees the chain from
; file_first, and writes the buffer back. Returns carry set and A = the error on a fault.
; Changes A, X and Y.
entry_drop:
        jsr entry_erase
        bcs @done
        ldx #3
@first:
        lda file_first,x
        sta cluster,x
        dex
        bpl @first
        jsr chain_free
        bcs @done
        jmp buf_flush
@done:
        rts

; entry_erase: marks the directory entry at entry_sector deleted, in the buffer. Returns carry
; set and A = the error on a fault. Changes A, X and Y.
entry_erase:
        jsr entry_load
        bcs @done
        lda #$E5
        sta (ptr)
        lda #1
        sta buf_dirty
@done:
        rts

; api_rmdir refuses a directory that holds any entry but . and .., and the current directory
; of its drive.
api_rmdir:
        jsr path_walk
        bcs @done
        jsr name_check
        bcs @no_path
        lda #ATTR_DIR | ATTR_HIDDEN | ATTR_SYSTEM
        sta search_attr
        jsr dir_first
        bcs @missing
        ldy #DIR_ATTR
        lda (ptr),y
        and #ATTR_DIR
        beq @no_path
        jsr entry_keep
        ldx #3
@first:
        ldy cluster_fields,x
        lda (ptr),y
        sta file_first,x
        sta cluster,x
        dex
        bpl @first
        lda #DPB_CWD + 3
        jsr cluster_is
        bne @scan
        lda #ERR_CURRENT_DIR
        sec
        rts
@scan:
        lda #'?'
        jsr fcb_fill
        lda #ATTR_DIR | ATTR_HIDDEN | ATTR_SYSTEM | ATTR_LABEL
        sta search_attr
        jsr dir_first
@entry:
        bcs @end
        lda (ptr)
        cmp #'.'
        bne @denied
        jsr dir_step
        bcs @entry              ; the end: @entry takes the error
        jsr dir_search
        bra @entry
@end:
        cmp #ERR_NO_MORE_FILES
        bne @fail
        jmp entry_drop
@denied:
        lda #ERR_ACCESS
        bra @fail
@missing:
        cmp #ERR_NO_MORE_FILES
        bne @fail
@no_path:
        lda #ERR_NO_PATH
@fail:
        sec
@done:
        rts

; api_rename makes the new entry from the old one, then marks the old one deleted. A directory
; keeps its parent: moving it gives ERR_ACCESS. file_size holds the old parent, and file_first
; the new one while its name is searched.
api_rename:
        jsr path_walk
        bcs @exit
        jsr name_check
        bcs @not_found
        ldx #3
@old_parent:
        lda cluster,x
        sta file_size,x
        dex
        bpl @old_parent
        lda #ATTR_DIR | ATTR_HIDDEN | ATTR_SYSTEM
        sta search_attr
        jsr dir_first
        bcc @found
        cmp #ERR_NO_MORE_FILES
        bne @exit_fail
@not_found:
        lda #ERR_NOT_FOUND
@exit_fail:
        sec
@exit:
        rts
@found:
        jsr entry_keep
        ldy #31
@save:
        lda (ptr),y
        sta entry_copy - DIR_ATTR,y
        dey
        cpy #DIR_ATTR - 1
        bne @save
        lda dpb
        sta rename_drive
        lda r1
        sta r0
        lda r1+1
        sta r0+1
        jsr path_walk
        bcs @done
        lda dpb
        cmp rename_drive
        bne @not_same
        jsr name_check
        bcs @no_path
        ldx #3
@new_parent:
        lda cluster,x
        sta file_first,x
        cmp file_size,x
        beq @same
        lda entry_copy          ; the attributes
        and #ATTR_DIR
        bne @denied
@same:
        dex
        bpl @new_parent
        jsr dir_first           ; search_attr is still every kind
        bcc @denied             ; the new name exists
        cmp #ERR_NO_MORE_FILES
        bne @fail
        ldx #3
@back:
        lda file_first,x
        sta cluster,x
        dex
        bpl @back
        lda #$C0                ; a full directory grows by a zeroed cluster
        sta writing
        jsr dir_slot
        stz writing
        bcs @fail
        ldy #31
@entry:
        lda entry_copy - DIR_ATTR,y
        sta (ptr),y
        dey
        cpy #DIR_ATTR - 1
        bne @entry
@name:
        lda fcb_name,y
        sta (ptr),y
        dey
        bpl @name
        lda #1
        sta buf_dirty
        jsr entry_erase
        bcs @done
        jmp buf_flush
@not_same:
        lda #ERR_NOT_SAME_DEVICE
        bra @fail
@denied:
        lda #ERR_ACCESS
        bra @fail
@no_path:
        lda #ERR_NO_PATH
@fail:
        sec
@done:
        rts

; api_diskfree counts the free entries of the FAT, sector by sector. pos counts down the
; entries left, from DPB_LIMIT, and file_size counts the free ones. Entries 0 and 1 are never
; 0.
api_diskfree:
        dec                     ; 0, the current drive, becomes $FF
        bpl @drive
        lda current_drive
@drive:
        jsr drive_ready
        bcc @ready
@fault:
        rts
@ready:
        ldy #0
@start:
        lda DPB + DPB_LIMIT,x
        sta pos,y
        lda DPB + DPB_FAT,x
        sta lba,y
        lda #0
        sta file_size,y
        inx
        iny
        cpy #4
        bne @start
@sector:
        jsr read_sector
        bcs @fault
        lda #<SECTOR_BUFFER
        sta ptr
        lda #>SECTOR_BUFFER
        sta ptr+1
@entry:
        ldy #3
        lda (ptr),y
        and #$0F                ; FAT32 entries are 28 bits
        dey
        ora (ptr),y
        dey
        ora (ptr),y
        dey
        ora (ptr),y
        bne @used
        inc file_size
        bne @used
        inc file_size+1
        bne @used
        inc file_size+2
        bne @used
        inc file_size+3
@used:
        lda pos
        bne @low
        lda pos+1
        bne @middle
        lda pos+2
        bne @high
        dec pos+3
@high:
        dec pos+2
@middle:
        dec pos+1
@low:
        dec pos
        lda pos
        ora pos+1
        ora pos+2
        ora pos+3
        beq @count
        lda ptr
        clc
        adc #4
        sta ptr
        bne @entry
        inc ptr+1
        lda ptr+1
        cmp #>SECTOR_BUFFER + 2
        bne @entry
        inc lba
        bne @sector
        inc lba+1
        bne @sector
        inc lba+2
        bne @sector
        inc lba+3
        bra @sector
@count:
        ldx #3
@free:
        lda file_size,x
        sta r1,x                ; r1 and r2
        dex
        bpl @free
        ldx dpb
        lda DPB + DPB_CMASK,x   ; the sectors per cluster * 2 - 1
        lsr
        inc
        sta r0
        stz r0+1
        stz r3
        lda #>512
        sta r3+1
        lda DPB + DPB_LIMIT,x   ; r4 and r5: the clusters from cluster 2
        sec
        sbc #2
        sta r4
        lda DPB + DPB_LIMIT+1,x
        sbc #0
        sta r4+1
        lda DPB + DPB_LIMIT+2,x
        sbc #0
        sta r5
        lda DPB + DPB_LIMIT+3,x
        sbc #0
        sta r5+1
        clc
@done:
        rts

; getcwd builds the path from the end of the buffer back: a \ and a name for each directory,
; from the current one up to the root. Then it moves the path down after the length byte,
; without its first \. path_index holds the index of the path's first character, 0 while it is
; empty. file_first holds the cluster of the directory whose name is wanted, and file_size the
; first cluster of its parent: the search leaves cluster at the cluster that holds the entry.
api_getcwd:
        dec                     ; 0, the current drive, becomes $FF
        bpl @drive
        lda current_drive
@drive:
        jsr drive_ready
        bcs @done
        jsr cluster_cwd
        stz path_index
@level:
        jsr is_root             ; at the root: done
        bne @up
        clc                     ; ptr = r0 + path_index: the path's first \ is at ptr + 0
        lda r0
        adc path_index
        sta ptr
        lda r0+1
        adc #0
        sta ptr+1
        lda path_index
        beq @length             ; the root: length 0
        eor #$FF                ; the length: 255 - path_index
        tax
        ldy #1
@move:
        lda (ptr),y
        sta (r0),y
        iny
        dex
        bne @move
        dey
        tya
@length:
        sta (r0)
        clc
@done:
        rts
@missing:
        cmp #ERR_NO_MORE_FILES
        bne @fail
@no_path:
        lda #ERR_NO_PATH
@fail:
        sec
        rts
@up:
        lda path_index          ; room for a \ and 12 characters
        beq @room
        cmp #14
        bcc @no_path
@room:
        ldx #3
@child:
        lda cluster,x
        sta file_first,x
        dex
        bpl @child
        lda #' '                ; the parent: the cluster in the .. entry
        jsr fcb_fill
        lda #'.'
        sta fcb_name
        sta fcb_name+1
        jsr dir_enter
        bcs @done
        ldx #3
@parent:
        lda cluster,x
        sta file_size,x
        dex
        bpl @parent
        lda #'?'                ; the child's entry in the parent
        jsr fcb_fill
        jsr dir_first
@entry:
        bcs @missing
        lda (ptr)
        cmp #'.'
        beq @next
        ldy #DIR_ATTR
        lda (ptr),y
        and #ATTR_DIR
        beq @next
        ldx #3
@same:
        ldy cluster_fields,x
        lda (ptr),y
        cmp file_first,x
        bne @next
        dex
        bpl @same
        ldy #10
@name:
        lda (ptr),y
        sta fcb_name,y
        dey
        bpl @name
        ldy path_index          ; the extension, a dot, the name and a \, back from path_index
        ldx #10
@extension:
        lda fcb_name,x
        jsr put_back
        dex
        cpx #8
        bcs @extension
        cpy path_index
        beq @base
        lda #'.'
        jsr put_back
@base:
        lda fcb_name,x
        jsr put_back
        dex
        bpl @base
        lda #'\'
        jsr put_back
        sty path_index
        ldx #3                  ; the parent is the next level
@next_level:
        lda file_size,x
        sta cluster,x
        dex
        bpl @next_level
        jmp @level
@next:
        jsr dir_step
        bcs @entry              ; the end: @entry takes the error
        jsr dir_search
        bra @entry

; put_back: puts A before the byte at r0 + Y and moves Y back, unless A is a space.
put_back:
        cmp #' '
        beq @done
        dey
        sta (r0),y
@done:
        rts

; cluster_fields: the bytes of a directory entry's first cluster, the low byte first.
cluster_fields:
        .byte DIR_CLUSTER_LOW, DIR_CLUSTER_LOW + 1, DIR_CLUSTER_HIGH, DIR_CLUSTER_HIGH + 1
