; The host file system: the kernel's disk calls on a folder of the PC, when x16emu runs with
; HostFS, in ROM bank 1. fat32dos.s includes this file; each of its calls comes here when
; host_on is set. lib_init sets it when x16emu answers host_probe. Real hardware, -sdcard and
; -nohostfs leave it clear, and the FAT32 library serves the calls.
;
; x16emu traps a JSR to these KERNAL addresses in a ROM bank that holds "MIST" at $FFF6. It then
; talks the CBM DOS protocol of its source file ieee.c, on unit 8.
;
; Limits, set by x16emu: a path holds at most HOST_NAME_MAX characters and no comma; a name in a
; listing over 32 characters is left out; a file has only the read-only and directory
; attributes, and a new one gets neither; diskfree gives fixed numbers; absread and abswrite fail with ERR_NOT_READY. On a case-sensitive host,
; only a path's last name ignores case.
;
; Trap: x16emu closes a file when its last byte is read. A channel closed so is marked
; HOST_EOF, and host_reopen opens it again from its path in HOST_PATHS when it is next sought
; or written.
; Trap: FAR_IRQ_ENTRY and FAR_IRQ_EXIT sit on $FFA5, $FFA8 and $FFAB, which x16emu traps while a
; transaction is open. host_listen and host_talk mask interrupts until the transaction ends.
; Trap: x16emu resolves a new file's absolute path from its current directory, so its current
; directory stays the root. Only host_list and host_chdir leave the root, and they come back.
; Trap: x16emu keeps one directory listing, so a listing is read to its end within one call.
; findnext lists the directory again, from the index in the find buffer; HOST_WINDOW keeps
; HOST_WINDOW_COUNT entries so that most calls do not.

LISTEN        = $FFB1           ; host_probe: bank 1 has an RTS there for when x16emu does not trap
SECOND        = $FF93
TALK          = $FFB4
TKSA          = $FF96
ACPTR         = $FFA5
CIOUT         = $FFA8
UNTLK         = $FFAB
UNLSN         = $FFAE
MACPTR        = $FF44
MCIOUT        = $FEB1

HOST_UNIT     = 8
SA_DATA       = $60             ; the secondary address of a channel's data
SA_CLOSE      = $E0
SA_OPEN       = $F0
CHANNEL_LIST  = 0               ; x16emu's channels 0 and 1 are read only and write only
CHANNEL_FIRST = 2
CHANNEL_LAST  = 14
CHANNEL_COMMAND = 15

HOST_NAME_MAX = 72              ; x16emu's 79 byte channel name, less @: and ,S,W
HOST_LINE_MAX = 127

HOST_OPEN     = $80             ; host_flags: the channel holds a file
HOST_EOF      = $40             ; host_flags: x16emu closed it at the last byte
HOST_ACCESS   = $03             ; host_flags: lib_open's access

MODE_READ     = 0               ; host_channel_open: open to read
MODE_MODIFY   = 1               ; to read and write; x16emu creates a missing file
MODE_CREATE   = 2               ; to write, emptied

; An entry of HOST_WINDOW.
ITEM_ATTR     = 0
ITEM_TIME     = 1               ; the time and the date, as FIND_TIME and FIND_DATE
ITEM_SIZE     = 5
ITEM_NAME     = 9               ; ended by 0
        .assert ITEM_NAME + NAME_MAX + 1 = HOST_ITEM_SIZE, error, "an item holds a name of NAME_MAX"

HOST_DIR_COUNT = 40             ; the directories of the searches in progress

; The positions in FIND_POS.
FIND_INDEX    = FIND_POS        ; the index of the next entry of the listing, 2 bytes
FIND_SLOT     = FIND_POS + 2    ; the directory, in HOST_DIRS
FIND_GENERATION = FIND_POS + 3  ; host_generation of the slot

.segment "KERNELRAM"

host_on:      .res 1            ; $FF: the calls go to the host; bit 7 tests it
host_status:  .res 1            ; x16emu's STATUS, which host_readst shows it
host_irq:     .res 1            ; host_begin: the flags before it masked interrupts

.segment "REGRAM"

host_name:    .res 80           ; the path in hand, from the root, / for \, ended by 0
host_item:    .res HOST_ITEM_SIZE
host_ptr_save: .res 1           ; read and written with another RAM bank selected

.segment "FATBSS"

host_flags:   .res 16           ; a byte for each channel
host_generation: .res HOST_DIR_COUNT ; moves on each time a slot of HOST_DIRS is taken over
host_channel: .res 1            ; the channel in hand
host_nibble:  .res 1            ; host_hex: the high digit
host_next_dir: .res 1           ; the slot of HOST_DIRS to take next
host_slot:    .res 1            ; the directory of findfirst
host_valid:   .res 1            ; not 0: HOST_WINDOW holds entries of host_w_slot
host_w_slot:  .res 1
host_w_generation: .res 1
host_w_start: .res 2            ; the listing index of HOST_WINDOW's first entry
host_w_count: .res 1
host_gone:    .res 1            ; files deleted since findfirst: the listing has moved up by these
host_want:    .res 2            ; host_list: the listing index of the first entry to keep
host_seen:    .res 2            ; host_list: the index of the line in hand
host_index:   .res 1            ; host_read_cwd: the start of the path built in host_name
host_cd_left: .res 1            ; not 0: host_list changed directory

.segment "B1CODE"

; host_probe: sets host_on when x16emu traps LISTEN, closes the channels and goes to the root.
; RAM bank 0 must be selected. Changes A, X and Y.
host_probe:
        stz host_on
        lda #HOST_UNIT
        sec
        jsr LISTEN              ; x16emu clears carry; the RTS of bank 1 keeps it
        bcs @done
        jsr UNLSN
        dec host_on
        ldx #15
@flag:
        stz host_flags,x
        dex
        bpl @flag
        stz host_next_dir
        stz host_valid
        ldx #HOST_DIR_COUNT - 1
@generation:
        stz host_generation,x
        dex
        bpl @generation
        stz HOST_CWD
        stz host_gone
        jsr host_read_status    ; x16emu's first message
        jsr host_cd_root
@done:
        rts

; host_begin: keeps the flags and masks interrupts for a transaction. Changes A.
host_begin:
        php
        pla
        sta host_irq
        sei
        rts

; host_finish: unmasks interrupts if host_begin found them unmasked. Keeps A, X, Y and carry.
host_finish:
        pha
        lda host_irq
        and #$04
        bne @masked
        cli
@masked:
        pla
        rts

; host_listen: starts sending to secondary address A. host_unlisten ends it. Keeps X and Y.
host_listen:
        pha
        jsr host_begin
        lda #HOST_UNIT
        jsr LISTEN
        pla
        jmp SECOND

host_unlisten:
        jsr UNLSN
        jmp host_finish

; host_talk: starts reading from secondary address A. host_untalk ends it. Keeps X and Y.
host_talk:
        pha
        jsr host_begin
        lda #HOST_UNIT
        jsr TALK
        pla
        jmp TKSA

host_untalk:
        jsr UNTLK
        jmp host_finish

; host_put_name: sends host_name. Changes A and X.
host_put_name:
        ldx #0
@char:
        lda host_name,x
        beq @done
        jsr CIOUT
        inx
        bra @char
@done:
        rts

; host_read_status: reads the command channel to HOST_LINE. Returns A = the status number, X the
; index after its two digits. Changes Y.
host_read_status:
        lda #SA_DATA | CHANNEL_COMMAND
        jsr host_talk
        ldx #0
@char:
        jsr ACPTR
        sta HOST_LINE,x
        inx
        cmp #$0D
        beq @end
        cpx #HOST_LINE_MAX
        bcc @char
@end:
        jsr host_untalk
        ldx #0
        ; fall through

; host_hex: returns A = the two hex digits at HOST_LINE,X, and moves X past them.
host_hex:
        lda HOST_LINE,x
        jsr host_digit
        asl
        asl
        asl
        asl
        sta host_nibble
        inx
        lda HOST_LINE,x
        jsr host_digit
        ora host_nibble
        inx
        rts

; host_digit: returns A = the value of the hex digit in A.
host_digit:
        cmp #'A'
        bcc @number
        and #$07                ; carry set adds 1
        adc #8
        rts
@number:
        and #$0F
        rts

; host_result: reads the command channel. Returns carry clear, or carry set and A = the error of
; its status. Changes X and Y.
host_result:
        jsr host_read_status
        cmp #$10                ; 00 OK, 01 FILES SCRATCHED, 07 from T
        bcc @done
        ldx #status_errors - status_numbers - 1
@number:
        cmp status_numbers,x
        beq @found
        dex
        bpl @number
        lda #ERR_ACCESS
        sec
        rts
@found:
        lda status_errors,x
        sec
@done:
        rts

status_numbers:
        .byte $62, $39, $32, $33, $34, $70
status_errors:
        .byte ERR_NOT_FOUND, ERR_NO_PATH, ERR_NO_PATH, ERR_NO_PATH, ERR_NO_PATH, ERR_TOO_MANY_FILES

; host_command: sends the command of the characters A and X, 0 for none, then a colon, then
; host_name, and returns as host_result.
host_command:
        pha
        phx
        lda #SA_DATA | CHANNEL_COMMAND
        jsr host_listen
        plx
        pla
        jsr CIOUT
        txa
        beq @colon
        jsr CIOUT
@colon:
        lda #':'
        jsr CIOUT
        jsr host_put_name
        jsr host_unlisten
        jmp host_result

; host_cd_root: makes the root x16emu's current directory. host_cd makes it host_name, the root
; when empty, and returns carry set and A = the error, ERR_NO_PATH when it is missing. Change X
; and Y; host_cd_root empties host_name.
host_cd_root:
        stz host_name
host_cd:
        lda host_name
        bne @send
        lda #'/'
        sta host_name
        stz host_name+1
        jsr @send
        stz host_name
        rts
@send:
        lda #'C'
        ldx #'D'
        jsr host_command
        bcc @done
        cmp #ERR_NOT_FOUND
        bne @error
        lda #ERR_NO_PATH
@error:
        sec
@done:
        rts

; host_abs: builds host_name from the path in lib_path, up to its index X, which holds a /, or its
; end. It starts at the root when the path starts with /, else at HOST_CWD. It takes out . and ..;
; .. at the root stays there, as in FAT32. host_name has no / at its start or end, and is empty for
; the root. Returns carry set and A = ERR_NO_PATH when the name is too long. Changes X and Y.
host_abs:
        stx host_nibble         ; the end
        ldy #0
        ldx #0
        lda lib_path
        cmp #'/'
        beq @segment
@cwd:
        lda HOST_CWD,x
        beq @cwd_end
        sta host_name,y
        iny
        inx
        bra @cwd
@cwd_end:
        ldx #0
@segment:
        cpx host_nibble
        beq @end
        lda lib_path,x
        beq @end
        cmp #'/'
        beq @skip
        cmp #'.'
        bne @name
        lda lib_path+1,x
        beq @skip
        cmp #'/'
        beq @skip
        cmp #'.'
        bne @name
        lda lib_path+2,x
        beq @up
        cmp #'/'
        bne @name
@up:
        inx
        inx
@back:
        cpy #0
        beq @segment
        dey
        beq @segment
        lda host_name,y
        cmp #'/'
        bne @back
        bra @segment
@skip:
        inx
        bra @segment
@name:
        cpy #0
        beq @char
        lda #'/'
        sta host_name,y
        iny
@char:
        lda lib_path,x
        beq @end
        cmp #'/'
        beq @segment
        sta host_name,y
        inx
        iny
        cpy #HOST_NAME_MAX + 1
        bcc @char
        lda #ERR_NO_PATH
        rts                     ; carry set
@end:
        lda #0
        sta host_name,y
        clc
        rts

; host_missing: A, carry set, is the error of a file or a new file in host_name. Gives
; ERR_NO_PATH in place of ERR_NOT_FOUND when the file's directory is missing. Changes X and Y.
host_missing:
        cmp #ERR_NOT_FOUND
        bne @error
        ldy #$FF
        ldx #$FF
@scan:
        iny
        lda host_name,y
        beq @scanned
        cmp #'/'
        bne @scan
        tya
        tax
        bra @scan
@scanned:
        lda #ERR_NOT_FOUND
        cpx #$FF
        beq @error
        stz host_name,x
        jsr host_cd
        bcs @error              ; ERR_NO_PATH, still at the root
        jsr host_cd_root
        lda #ERR_NOT_FOUND
@error:
        sec
        rts

; host_channel_open: opens channel host_channel on host_name with MODE_ X. Returns as host_result.
host_channel_open:
        phx
        lda host_channel
        ora #SA_OPEN
        jsr host_listen
        plx
        phx
        cpx #MODE_CREATE
        bne @colon
        lda #'@'
        jsr CIOUT
@colon:
        lda #':'
        jsr CIOUT
        jsr host_put_name
        plx
        beq @sent               ; PLX sets Z: MODE_READ
        lda #','
        jsr CIOUT
        lda #'S'
        jsr CIOUT
        lda #','
        jsr CIOUT
        lda #'M'
        cpx #MODE_MODIFY
        beq @mode
        lda #'W'
@mode:
        jsr CIOUT
@sent:
        jsr host_unlisten
        jmp host_result

; host_channel_close: closes channel host_channel at x16emu. Changes A.
host_channel_close:
        lda host_channel
        ora #SA_CLOSE
        jsr host_listen
        jmp host_unlisten

; host_path_ptr: points fat32_ptr2 at channel A's path in HOST_PATHS. Changes A.
host_path_ptr:
        lsr
        pha
        lda #0
        ror
        sta fat32_ptr2
        pla
        clc
        adc #>HOST_PATHS
        sta fat32_ptr2+1
        rts
        .assert <HOST_PATHS = 0, error, "host_path_ptr adds to the high byte"

; host_open: lib_open on the host.
host_open:
        php
        pha
        jsr lib_take
        plx                     ; the access
        ply                     ; the flags: carry in bit 0
        bcc @taken
        jmp lib_bank
@taken:
        stx lib_access
        ldx #CHANNEL_FIRST
@free:
        lda host_flags,x
        beq @found
        inx
        cpx #CHANNEL_LAST + 1
        bne @free
        lda #ERR_TOO_MANY_FILES
        jmp lib_error
@found:
        stx host_channel
        tya
        lsr
        bcc @existing
        jsr name_check
        lda #ERR_NO_PATH        ; keeps carry
        bcs @fail
        ldx #$FF
        jsr host_abs
        bcs @fail
        ldx #MODE_CREATE
        jsr host_channel_open
        bcc @created
        jsr host_missing
        bra @fail
@created:
        jsr host_channel_close
        lda #1
        sta lib_access          ; created: the channel must be able to read and write
        bra @modify
@existing:
        lda #ERR_NOT_FOUND
        bit lib_wild
        bmi @fail
        ldx #$FF
        jsr host_abs
        bcs @fail
        ldx #MODE_READ          ; first: x16emu's modify mode creates a missing file
        jsr host_channel_open
        bcc @exists
        jsr host_missing
        bra @fail
@exists:
        lda lib_access
        beq @keep
        jsr host_channel_close
@modify:
        ldx #MODE_MODIFY
        jsr host_channel_open
        bcc @keep
        lda #ERR_ACCESS         ; the file is read only
@fail:
        jmp lib_error
@keep:
        lda host_channel        ; the path, for host_reopen
        jsr host_path_ptr
        ldy #$FF
@copy:
        iny
        lda host_name,y
        sta (fat32_ptr2),y
        bne @copy
        ldx host_channel
        lda lib_access
        ora #HOST_OPEN
        sta host_flags,x
        lda #SA_DATA | CHANNEL_COMMAND  ; T: the status holds the position and the size
        jsr host_listen
        lda #'T'
        jsr CIOUT
        lda host_channel
        jsr CIOUT
        jsr host_unlisten
        jsr host_read_status
        ldx #12                 ; "07,PPPPPPPP SSSSSSSS"
        ldy #3
@size:
        jsr host_hex
        sta file_size,y
        lda #0
        sta file_context+1,y    ; the position
        dey
        bpl @size
        lda host_channel
        sta file_context
        clc
        jmp lib_bank

; host_close: lib_close on the host. Context 0 is no channel: host_split's.
host_close:
        cmp #CHANNEL_FIRST
        bcc @done
        sta host_channel
        tax
        stz host_flags,x
        jsr host_channel_close
@done:
        clc
        rts

; host_reopen: opens channel A again from its path when x16emu closed it. Returns carry set and A
; = the error. Changes X and Y.
host_reopen:
        sta host_channel
        tax
        lda host_flags,x
        and #HOST_EOF
        beq @done
        lda host_channel
        jsr host_path_ptr
        ldy #$FF
@copy:
        iny
        lda (fat32_ptr2),y
        sta host_name,y
        bne @copy
        ldx host_channel
        lda host_flags,x
        and #<~HOST_EOF
        sta host_flags,x
        and #HOST_ACCESS
        beq @read
        ldx #MODE_MODIFY
        jmp host_channel_open
@read:
        ldx #MODE_READ
        jmp host_channel_open
@done:
        clc
        rts

; host_position: sends the position of channel host_channel, the 4 bytes at fat32_ptr. Changes A
; and Y.
host_position:
        lda #SA_DATA | CHANNEL_COMMAND
        jsr host_listen
        lda #'P'
        jsr CIOUT
        lda host_channel
        jsr CIOUT
        ldy #0
@byte:
        lda (fat32_ptr),y
        jsr CIOUT
        iny
        cpy #4
        bne @byte
        jmp host_unlisten

; host_seek: lib_seek on the host.
host_seek:
        jsr host_reopen
        bcs @done
        lda #r0
        sta fat32_ptr
        stz fat32_ptr+1
        jsr host_position
        clc
@done:
        rts

; host_advance: after MACPTR or MCIOUT moved X and Y (high) bytes: takes them from fat32_ptr2,
; the bytes left, adds them to krn_ptr1, the bytes moved, and moves fat32_ptr on, keeping it in
; $A000-$BFFF when it was there. Returns Z set when no bytes moved. Changes A.
host_advance:
        txa
        clc
        adc krn_ptr1
        sta krn_ptr1
        tya
        adc krn_ptr1+1
        sta krn_ptr1+1
        sec
        lda fat32_ptr2
        stx host_ptr_save
        sbc host_ptr_save
        sta fat32_ptr2
        lda fat32_ptr2+1
        sty host_ptr_save
        sbc host_ptr_save
        sta fat32_ptr2+1
        txa
        clc
        adc fat32_ptr
        sta fat32_ptr
        tya
        adc fat32_ptr+1
        cmp #>ROM               ; x16emu wrapped to $A000 and moved to the next bank
        bcc @kept
        sbc #>(ROM - BANKED_RAM) ; carry set
@kept:
        sta fat32_ptr+1
        txa
        bne @done
        tya
@done:
        rts

; host_block: sets A, X and Y for MACPTR or MCIOUT: up to 256 bytes of those left, at fat32_ptr.
host_block:
        lda fat32_ptr2
        ldx fat32_ptr2+1
        beq @few
        lda #0                  ; 256 bytes
@few:
        ldx fat32_ptr
        ldy fat32_ptr+1
        clc
        rts

; host_prepare: fat32_ptr = r0, fat32_ptr2 = r1, the bytes left, krn_ptr1 = 0, the bytes moved.
; Changes A.
host_prepare:
        lda r0
        sta fat32_ptr
        lda r0+1
        sta fat32_ptr+1
        lda r1
        sta fat32_ptr2
        lda r1+1
        sta fat32_ptr2+1
        stz krn_ptr1
        stz krn_ptr1+1
        rts

; host_read: lib_read on the host. Interrupts stay masked for the whole read.
host_read:
        sta host_channel
        tax
        lda host_flags,x
        and #HOST_EOF
        bne @nothing
        jsr host_prepare
        lda host_channel
        ora #SA_DATA
        jsr host_talk
        lda saved_bank
        sta RAM_BANK
@block:
        lda fat32_ptr2
        ora fat32_ptr2+1
        beq @end
        stz host_status
        jsr host_block
        jsr MACPTR
        bcs @end                ; x16emu has no such file open
        jsr host_advance
        beq @end
        lda host_status
        beq @block
@end:
        stz RAM_BANK
        jsr host_untalk
        lda host_status
        and #$40
        beq @moved
        ldx host_channel
        lda host_flags,x
        ora #HOST_EOF
        sta host_flags,x
@moved:
        lda krn_ptr1
        sta r1
        lda krn_ptr1+1
        sta r1+1
        clc
        rts
@nothing:
        stz r1
        stz r1+1
        clc
        rts

; host_write: lib_write on the host. A position past the end of the file: the host fills the
; gap with zeros.
host_write:
        jsr host_reopen
        bcc @opened
        rts
@opened:
        lda lib_entry
        clc
        adc #<(SFT + SFT_POS)
        sta fat32_ptr
        lda #>(SFT + SFT_POS)
        adc #0
        sta fat32_ptr+1
        jsr host_position
        jsr host_prepare
        lda host_channel
        ora #SA_DATA
        jsr host_listen
        lda saved_bank
        sta RAM_BANK
@block:
        lda fat32_ptr2
        ora fat32_ptr2+1
        beq @end
        jsr host_block
        jsr MCIOUT
        bcs @end
        jsr host_advance
        bne @block
@end:
        stz RAM_BANK
        jsr host_unlisten
        lda krn_ptr1
        sta r1
        lda krn_ptr1+1
        sta r1+1
        ldy lib_entry           ; host_item = the end of the bytes written
        clc
        lda SFT + SFT_POS,y
        adc r1
        sta host_item
        lda SFT + SFT_POS+1,y
        adc r1+1
        sta host_item+1
        lda SFT + SFT_POS+2,y
        adc #0
        sta host_item+2
        lda SFT + SFT_POS+3,y
        adc #0
        sta host_item+3
        sec                     ; carry clear below when the size is under it
        lda SFT + SFT_FILE_SIZE,y
        sbc host_item
        lda SFT + SFT_FILE_SIZE+1,y
        sbc host_item+1
        lda SFT + SFT_FILE_SIZE+2,y
        sbc host_item+2
        lda SFT + SFT_FILE_SIZE+3,y
        sbc host_item+3
        bcs @same
        ldx #0
@store:
        lda host_item,x
        sta SFT + SFT_FILE_SIZE,y
        iny
        inx
        cpx #4
        bne @store
@same:
        clc
        rts

; host_delete: api_delete on the host.
host_delete:
        jsr lib_take
        bcs @bank
        jsr name_check
        lda #ERR_NOT_FOUND      ; keeps carry
        bcs @bank
        ldx #$FF
        jsr host_abs
        bcs @bank
        jsr host_is_dir
        lda #ERR_NOT_FOUND
        bcc @refuse
        lda #'S'
        ldx #0
        jsr host_command
        bcc @gone
        jsr host_missing
        bra @bank
@gone:
        inc host_gone
@bank:
        jmp lib_bank
@refuse:
        sec
        bra @bank

; host_mkdir: api_mkdir on the host.
host_mkdir:
        jsr lib_take
        bcs @bank
        jsr name_check
        lda #ERR_NO_PATH        ; keeps carry
        bcs @bank
        ldx #$FF
        jsr host_abs
        bcs @bank
        lda #'M'
        ldx #'D'
        jsr host_command
        bcc @bank
        jsr host_missing
@bank:
        jmp lib_bank

; host_rmdir: api_rmdir on the host.
host_rmdir:
        jsr lib_take
        bcs @bank
        jsr path_trim
        jsr name_check
        lda #ERR_NO_PATH        ; keeps carry
        bcs @bank
        ldx #$FF
        jsr host_abs
        bcs @bank
        ldx #$FF
@compare:
        inx
        lda host_name,x
        cmp HOST_CWD,x
        bne @other
        cmp #0
        bne @compare
        lda #ERR_CURRENT_DIR
        sec
        bra @bank
@other:
        lda #'R'
        ldx #'D'
        jsr host_command
        bcc @bank
        cmp #ERR_NOT_FOUND
        bne @error
        lda #ERR_NO_PATH
@error:
        sec
@bank:
        jmp lib_bank

; host_chdir: api_chdir on the host. x16emu's $=C lists the directory, then each one above it, up
; to /. They become HOST_CWD, built from the end of host_name.
host_chdir:
        jsr lib_take
        bcs @bank
        lda #ERR_NO_PATH
        bit lib_wild
        bmi @error
        lda lib_path            ; an empty path keeps the current directory
        beq @bank_clear
        ldx #$FF
        jsr host_abs
        bcs @bank
        jsr host_cd
        bcs @bank
        jsr host_read_cwd
        jsr host_cd_root
@bank_clear:
        clc
@bank:
        jmp lib_bank
@error:
        sec
        bra @bank

; host_read_cwd: sets HOST_CWD from x16emu's current directory. Changes A, X and Y.
host_read_cwd:
        lda #'C'
        jsr host_list_start
        lda #HOST_NAME_MAX + 1
        sta host_index
        stz host_name + HOST_NAME_MAX + 1
@line:
        jsr host_read_line
        bcs @end
        jsr host_quotes
        bcs @line
        lda HOST_LINE,x
        cmp #'/'
        beq @line               ; the root: read on to the end of the listing
        stx host_ptr_save       ; the name's first character
@copy:
        dey
        cpy host_ptr_save
        bcc @slash
        lda HOST_LINE,y
        dec host_index
        ldx host_index
        sta host_name,x
        bra @copy
@slash:
        lda #'/'
        dec host_index
        ldx host_index
        sta host_name,x
        bra @line
@end:
        jsr host_list_close
        ldx host_index
        lda host_name,x
        beq @root
        inx                     ; HOST_CWD has no / at its start
@root:
        ldy #$FF
@move:
        iny
        lda host_name,x
        sta HOST_CWD,y
        inx
        cmp #0
        bne @move
        rts

; host_getcwd: api_getcwd on the host: a length byte, then the path with \ for /.
host_getcwd:
        jsr drive_enter
        bcs @bank
        ldx #$FF
@length:
        inx
        lda HOST_CWD,x
        bne @length
        txa
        ldy #0
        ldx saved_bank
        stx RAM_BANK
        sta (r0)
        stz RAM_BANK
        ldx #0
@copy:
        lda HOST_CWD,x
        beq @end
        cmp #'/'
        bne @put
        lda #'\'
@put:
        iny
        phx
        ldx saved_bank
        stx RAM_BANK
        sta (r0),y
        stz RAM_BANK
        plx
        inx
        bra @copy
@end:
        clc
@bank:
        jmp lib_bank

; host_rename: api_rename on the host. The host allows a directory to move.
host_rename:
        lda r0+1                ; the old path, for later
        pha
        lda r0
        pha
        lda r1
        sta r0
        lda r1+1
        sta r0+1
        jsr lib_take            ; the new path
        ply                     ; keeps carry
        sty r0
        ply
        sty r0+1
        bcs @early
        jsr name_check
        lda #ERR_NO_PATH        ; keeps carry
        bcs @early
        ldx #$FF
        jsr host_abs
        bcs @early
        lda lib_dpb
        sta lib_new_dpb
        ldx #$FF
@copy:
        inx
        lda host_name,x
        sta lib_new,x
        bne @copy
        lda saved_bank          ; lib_take keeps the bank it finds
        sta RAM_BANK
        jsr lib_take            ; the old path
        bcs @early
        jsr name_check
        lda #ERR_NOT_FOUND      ; keeps carry
        bcs @early
        lda lib_dpb
        cmp lib_new_dpb
        beq @same_drive
        lda #ERR_NOT_SAME_DEVICE
        sec
@early:
        jmp lib_bank
@same_drive:
        ldx #$FF
        jsr host_abs
        bcs @bank
        jsr host_is_dir
        bcc @directory
        stz host_channel        ; CHANNEL_LIST: the old file must exist, and then 62 means the new
        ldx #MODE_READ          ; name exists: x16emu R49 gives that on Windows
        jsr host_channel_open
        bcc @source
        jsr host_missing
        bra @bank
@source:
        jsr host_channel_close
        jsr host_same
        beq @refuse
        bra @send
@directory:                     ; a directory stays in its parent
        jsr host_same
        beq @refuse
        txa
        tay
@in_new:
        lda lib_new,x
        cmp #'/'
        beq @refuse
        inx
        cmp #0
        bne @in_new
@in_old:
        lda host_name,y
        cmp #'/'
        beq @refuse
        iny
        cmp #0
        bne @in_old
@send:
        lda #SA_DATA | CHANNEL_COMMAND
        jsr host_listen
        lda #'R'
        jsr CIOUT
        lda #':'
        jsr CIOUT
        ldx #0
@new:
        lda lib_new,x
        beq @old
        jsr CIOUT
        inx
        bra @new
@old:
        lda #'='
        jsr CIOUT
        jsr host_put_name
        jsr host_unlisten
        jsr host_result
        bcc @bank
        cmp #ERR_NOT_FOUND
        bne @bank               ; keeps carry
@refuse:
        lda #ERR_ACCESS
        sec
@bank:
        jmp lib_bank

; host_same: Z is set when lib_new equals host_name; else X = where they first differ. Changes A.
host_same:
        ldx #$FF
@char:
        inx
        lda lib_new,x
        cmp host_name,x
        bne @done
        cmp #0
        bne @char
@done:
        rts

; host_is_dir: returns carry clear when host_name is a directory. Changes A, X and Y.
host_is_dir:
        lda host_name+1         ; host_cd_root changes the first two
        pha
        lda host_name
        pha
        jsr host_cd
        php
        bcs @keep
        jsr host_cd_root
@keep:
        plp
        pla
        sta host_name
        pla
        sta host_name+1
        rts

; host_diskfree: api_diskfree on the host: fixed numbers, 2 GB free of 2 GB.
host_diskfree:
        jsr drive_enter
        bcs @bank
        lda #$FF
        sta r1
        sta r1+1
        sta r4
        sta r4+1
        stz r2
        stz r2+1
        stz r5
        stz r5+1
        lda #64
        sta r0
        stz r0+1
        stz r3
        lda #>512
        sta r3+1
        clc
@bank:
        jmp lib_bank

; host_abs_io: api_absread and api_abswrite on the host: a folder has no sectors.
host_abs_io:
        lda #ERR_NOT_READY
        sec
        rts

; host_split: lib_split on the host: no context.
host_split:
        stz lib_context
        clc
        rts

; host_find_dir: api_findfirst on the host, before the pattern overwrites lib_path: takes a slot
; of HOST_DIRS for the path's directory in host_slot. A slot with the same directory serves
; again. Returns carry set and A = the error. Changes X and Y.
host_find_dir:
        ldx lib_slash
        inx
        beq @end                ; no directory: X = 0
        dex
@end:
        jsr host_abs
        bcs @done
        lda #HOST_BANK
        sta RAM_BANK
        lda #HOST_DIR_COUNT - 1
        sta host_ptr_save
@slot:
        lda host_ptr_save
        jsr host_dir_ptr
        ldy #$FF
@compare:
        iny
        lda (fat32_ptr2),y
        cmp host_name,y
        bne @differ
        cmp #0
        bne @compare
        lda host_ptr_save       ; RAM bank 0 again below
        bra @found
@differ:
        dec host_ptr_save
        bpl @slot
        stz RAM_BANK
        lda host_next_dir
        pha
        tax
        inc host_generation,x
        inx
        cpx #HOST_DIR_COUNT
        bcc @next
        ldx #0
@next:
        stx host_next_dir
        pla
        pha
        jsr host_dir_ptr
        lda #HOST_BANK
        sta RAM_BANK
        ldy #$FF
@copy:
        iny
        lda host_name,y
        sta (fat32_ptr2),y
        bne @copy
        pla
@found:
        stz RAM_BANK
        sta host_slot
        clc
@done:
        rts

; host_dir_ptr: points fat32_ptr2 at slot A of HOST_DIRS. Changes A.
host_dir_ptr:
        lsr
        pha
        lda #0
        ror
        sta fat32_ptr2
        pla
        clc
        adc #>HOST_DIRS
        sta fat32_ptr2+1
        rts
        .assert <HOST_DIRS = 0, error, "host_dir_ptr adds to the high byte"
        .assert HOST_DIRS + HOST_DIR_COUNT * 128 = HOST_WINDOW, error, "HOST_DIRS ends at HOST_WINDOW"

; host_find_init: api_findfirst on the host: the search state.
host_find_init:
        stz lib_find + FIND_INDEX
        stz lib_find + FIND_INDEX + 1
        ldx host_slot
        stx lib_find + FIND_SLOT
        lda host_generation,x
        sta lib_find + FIND_GENERATION
        stz host_valid
        stz host_gone
        rts

; host_find_search: find_search on the host.
host_find_search:
        stz lib_context
        lda lib_find + FIND_INDEX
        ora lib_find + FIND_INDEX + 1
        bne @next
        ldy #$FF                ; findfirst left the directory in host_name
@dir_end:
        iny
        lda host_name,y
        bne @dir_end
        cpy #0
        beq @pattern
        lda #'/'
        sta host_name,y
        iny
@pattern:
        ldx #$FF
@copy:                          ; one name: a missing one needs no listing
        inx
        lda lib_find + FIND_PATTERN,x
        sta host_name,y
        beq @one_name
        cmp #'*'
        beq @next
        cmp #'?'
        beq @next
        iny
        cpy #HOST_NAME_MAX + 1
        bcc @copy
        jmp @no_more
@one_name:
        jsr host_is_dir
        bcc @next
        stz host_channel        ; CHANNEL_LIST
        ldx #MODE_READ
        jsr host_channel_open
        bcc @exists
        jsr host_missing
        cmp #ERR_NO_PATH
        bne @none
        rts                     ; carry set
@none:
        jmp @no_more
@exists:
        jsr host_channel_close
@next:
        ldx lib_find + FIND_SLOT
        lda lib_find + FIND_GENERATION
        cmp host_generation,x
        beq @current
        jmp @no_more            ; so many directories since that the slot was taken
@current:
        jsr host_in_window
        bcc @have
        lda host_valid          ; a short window: the listing ended there
        beq @list
        lda host_w_slot
        cmp lib_find + FIND_SLOT
        bne @list
        lda lib_find + FIND_GENERATION
        cmp host_w_generation
        bne @list
        lda lib_find + FIND_INDEX
        cmp host_w_start
        lda lib_find + FIND_INDEX + 1
        sbc host_w_start + 1
        bcc @list               ; below the window
        lda host_w_count
        cmp #HOST_WINDOW_COUNT
        bcc @no_more
@list:
        jsr host_list
        bcs @fail
        jsr host_in_window
        bcs @no_more
@have:
        jsr host_item_get
        inc lib_find + FIND_INDEX
        bne @filter
        inc lib_find + FIND_INDEX + 1
@filter:
        lda lib_find + FIND_SEARCH ; directories, hidden and system files need their bit in A
        eor #$FF
        and host_item + ITEM_ATTR
        and #ATTR_HIDDEN | ATTR_SYSTEM | ATTR_DIR
        bne @next
        ldx #NAME_MAX
@dirent:
        lda host_item + ITEM_NAME,x
        sta fat32_dirent + dirent::name,x
        dex
        bpl @dirent
        lda #<lib_find
        sta fat32_ptr
        lda #>lib_find
        sta fat32_ptr+1
        ldy #0
        jsr match_name
        bcc @next
        ldx #3
@time:
        lda host_item + ITEM_TIME,x
        sta lib_find + FIND_TIME,x
        lda host_item + ITEM_SIZE,x
        sta lib_find + FIND_SIZE,x
        dex
        bpl @time
        lda host_item + ITEM_ATTR
        sta lib_find + FIND_ATTR
        inx                     ; 0
@name:
        lda host_item + ITEM_NAME,x
        beq @named
        sta lib_find + FIND_NAME + 1,x
        inx
        bra @name
@named:
        stx lib_find + FIND_NAME
        clc
        rts
@no_more:
        lda #ERR_NO_MORE_FILES
        sec
@fail:
        rts

; host_in_window: returns carry clear and host_want = the entry's offset in HOST_WINDOW when
; the search's next entry is there. Changes A.
host_in_window:
        lda host_valid
        beq @out
        lda host_w_slot
        cmp lib_find + FIND_SLOT
        bne @out
        lda host_w_generation
        cmp lib_find + FIND_GENERATION
        bne @out
        sec
        lda lib_find + FIND_INDEX
        sbc host_w_start
        sta host_want
        lda lib_find + FIND_INDEX + 1
        sbc host_w_start + 1
        bne @out                ; below the window, or far above it
        lda host_want
        cmp host_w_count        ; carry clear when it is below the count
        rts
@out:
        sec
        rts

; host_item_get: copies entry host_want of HOST_WINDOW to host_item. Changes A and Y.
host_item_get:
        jsr host_window_ptr
        lda #HOST_BANK
        sta RAM_BANK
        ldy #HOST_ITEM_SIZE - 1
@copy:
        lda (fat32_ptr2),y
        sta host_item,y
        dey
        bpl @copy
        stz RAM_BANK
        rts

; host_window_ptr: points fat32_ptr2 at entry host_want of HOST_WINDOW. Changes A and Y.
host_window_ptr:
        lda #<HOST_WINDOW
        sta fat32_ptr2
        lda #>HOST_WINDOW
        sta fat32_ptr2+1
        ldy host_want
        beq @done
@add:
        clc
        lda fat32_ptr2
        adc #HOST_ITEM_SIZE
        sta fat32_ptr2
        bcc @same
        inc fat32_ptr2+1
@same:
        dey
        bne @add
@done:
        rts

; host_list: fills HOST_WINDOW from the search's next entry, less the files deleted since. Returns
; carry set and A = the error. Changes X and Y.
host_list:
        sec
        lda lib_find + FIND_INDEX
        sbc host_gone
        sta lib_find + FIND_INDEX
        sta host_w_start
        lda lib_find + FIND_INDEX + 1
        sbc #0
        sta lib_find + FIND_INDEX + 1
        sta host_w_start + 1
        stz host_gone
        lda lib_find + FIND_SLOT
        sta host_w_slot
        jsr host_dir_ptr
        lda #HOST_BANK
        sta RAM_BANK
        ldy #$FF
@dir:
        iny
        lda (fat32_ptr2),y
        sta host_name,y
        bne @dir
        stz RAM_BANK
        lda lib_find + FIND_GENERATION
        sta host_w_generation
        stz host_valid
        stz host_w_count
        stz host_cd_left
        lda host_name
        beq @root
        jsr host_cd
        bcs @fail
        dec host_cd_left
@root:
        lda #'L'
        jsr host_list_start
        stz host_seen
        stz host_seen+1
@line:
        jsr host_read_line
        bcs @end
        jsr host_parse
        bcs @line
        lda host_cd_left
        bne @listed
        lda host_item + ITEM_NAME ; x16emu lists . in the root; FAT32 has none there
        cmp #'.'
        bne @listed
        lda host_item + ITEM_NAME + 1
        beq @line
@listed:
        lda host_seen+1         ; before the window?
        cmp host_w_start+1
        bcc @count
        bne @keep
        lda host_seen
        cmp host_w_start
        bcc @count
@keep:
        lda host_w_count
        cmp #HOST_WINDOW_COUNT
        bcs @line               ; x16emu's listing must be read to its end
        sta host_want
        jsr host_window_ptr
        lda #HOST_BANK
        sta RAM_BANK
        ldy #HOST_ITEM_SIZE - 1
@store:
        lda host_item,y
        sta (fat32_ptr2),y
        dey
        bpl @store
        stz RAM_BANK
        inc host_w_count
@count:
        inc host_seen
        bne @line
        inc host_seen+1
        bra @line
@end:
        jsr host_list_close
        dec host_valid
        lda host_cd_left
        beq @done
        jsr host_cd_root
@done:
        clc
@fail:
        rts

; host_list_start: opens the listing $=A, $=C or $=L, on the listing channel, starts reading it,
; and skips its heading. Changes A, X and Y.
host_list_start:
        pha
        lda #SA_OPEN | CHANNEL_LIST
        jsr host_listen
        lda #'$'
        jsr CIOUT
        lda #'='
        jsr CIOUT
        pla
        jsr CIOUT
        jsr host_unlisten
        lda #SA_DATA | CHANNEL_LIST
        jsr host_talk
        ldx #6                  ; the load address, the link and the line number
@skip:
        jsr ACPTR
        dex
        bne @skip
        jmp host_read_text

; host_list_close: ends reading the listing and closes its channel. Changes A.
host_list_close:
        jsr host_untalk
        lda #CHANNEL_LIST
        sta host_channel
        jmp host_channel_close

; host_read_line: reads a line of the listing to HOST_LINE: the link, the number, then the text.
; Returns carry set at the end of the listing, whose link is 0. Changes A, X and Y.
host_read_line:
        jsr ACPTR
        tax
        jsr ACPTR
        stx host_nibble
        ora host_nibble
        bne @text
        sec
        rts
@text:
        jsr ACPTR
        jsr ACPTR
        ; fall through

; host_read_text: reads to the 0 that ends a line, to HOST_LINE, which keeps HOST_LINE_MAX
; characters and the 0. Returns carry clear. Changes A and X.
host_read_text:
        ldx #0
@char:
        jsr ACPTR
        sta HOST_LINE,x
        beq @end
        cpx #HOST_LINE_MAX
        bcs @char               ; the rest of a long line is lost
        inx
        bra @char
@end:
        clc
        rts

; host_quotes: finds the name between the quotes in HOST_LINE. Returns X = its first character and
; Y = the closing quote's index, or carry set when the line has none. Changes A.
host_quotes:
        ldx #$FF
@open:
        inx
        lda HOST_LINE,x
        beq @none
        cmp #'"'
        bne @open
        inx
        txa
        tay
@close:
        lda HOST_LINE,y
        beq @none
        cmp #'"'
        beq @found
        iny
        bra @close
@found:
        clc
        rts
@none:
        sec
        rts

; host_parse: fills host_item from a line of the $=L listing:
; "NAME" padding TYPE, two spaces, YYYY-MM-DD HH:MM:SS, a space, AA SSSSSSSS. Returns carry set
; when it holds no entry, or a name over NAME_MAX. Changes A, X and Y.
host_parse:
        jsr host_quotes
        bcs @none
        tya
        stx host_ptr_save
        sec
        sbc host_ptr_save
        cmp #NAME_MAX + 1
        bcc @fits
@none:
        sec
        rts
@fits:
        ldy #0
@name:
        lda HOST_LINE,x
        cmp #'"'
        beq @named
        sta host_item + ITEM_NAME,y
        inx
        iny
        bra @name
@named:
        lda #0
        sta host_item + ITEM_NAME,y
        inx                     ; past the quote
@space:
        lda HOST_LINE,x
        inx
        cmp #' '
        beq @space
        inx                     ; the first of the type's 3 letters was read
        inx
        inx                     ; the two spaces
        inx
        jsr host_dec            ; the century
        cmp #19
        php
        jsr host_dec            ; the year
        plp
        beq @last_century
        clc
        adc #20                 ; from 1980
        bra @year
@last_century:
        sec
        sbc #80
@year:
        asl
        sta host_item + ITEM_TIME + 3
        inx
        jsr host_dec            ; the month
        pha
        lsr
        lsr
        lsr
        ora host_item + ITEM_TIME + 3
        sta host_item + ITEM_TIME + 3
        pla
        asl
        asl
        asl
        asl
        asl
        sta host_item + ITEM_TIME + 2
        inx
        jsr host_dec            ; the day
        ora host_item + ITEM_TIME + 2
        sta host_item + ITEM_TIME + 2
        inx
        jsr host_dec            ; the hours
        asl
        asl
        asl
        sta host_item + ITEM_TIME + 1
        inx
        jsr host_dec            ; the minutes
        pha
        lsr
        lsr
        lsr
        ora host_item + ITEM_TIME + 1
        sta host_item + ITEM_TIME + 1
        pla
        asl
        asl
        asl
        asl
        asl
        sta host_item + ITEM_TIME
        inx
        jsr host_dec            ; the seconds
        lsr
        ora host_item + ITEM_TIME
        sta host_item + ITEM_TIME
        inx                     ; the space
        jsr host_hex
        sta host_item + ITEM_ATTR
        inx                     ; the space
        ldy #3
@size:
        jsr host_hex
        sta host_item + ITEM_SIZE,y
        dey
        bpl @size
        clc
        rts

; host_dec: returns A = the two decimal digits at HOST_LINE,X, and moves X past them.
host_dec:
        lda HOST_LINE,x
        and #$0F
        asl
        sta host_nibble
        asl
        asl
        adc host_nibble         ; carry clear: digits are small
        sta host_nibble
        inx
        lda HOST_LINE,x
        and #$0F
        adc host_nibble
        inx
        rts
