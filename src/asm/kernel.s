; The kernel: the driver chain, the system file table, the handles, and the calls on handles.
; fat.s holds the drives and the file system.
;
; A handle is an index into PSP_HANDLES, which holds an SFT entry number. The SFT is in RAM
; bank 0. A device's SFT entry holds the address of its driver header; a file's holds its drive
; and its position.

.setcpu "65C02"

.include "mem.inc"
.include "api.inc"

.export kernel_init, to_upper
.export api_create, api_open, api_close, api_read, api_write, api_version, api_ticks, api_errmsg
.export drv_call, bank0, bank_restore, io_start, io_step, io_done, handles_inherit, handles_close
.export sft_find, api_dup, api_dup2, api_ioctl
.exportzp driver, io_ptr, io_left, saved_bank
.import con_init, api_con_status, CHRIN, CHROUT, errmsg_table, sd_driver
.import drives_init, drives_add, path_last, file_find, file_create, file_io, file_close
.import create_attr
.importzp ticks, fcb_name, cluster, dpb

.segment "KERNELZP" : zeropage

driver:       .res 2            ; the driver header in use
driver_chain: .res 2            ; the first driver header
drv_vector:   .res 2
saved_bank:   .res 1            ; the caller's RAM bank, while bank 0 is selected
io_ptr:       .res 2            ; the buffer of a driver input or output
io_left:      .res 2            ; the bytes still to move
io_slot:      .res 1            ; the driver command of a read or a write
open_handle:  .res 1

.segment "KERNELRAM"

io_refused:   .res 1            ; the access mode that refuses a read or a write
open_access:  .res 1
open_flags:   .res 1            ; SFT_FLAGS of the entry api_open fills
open_create:  .res 1            ; bit 7 set for create

.segment "CODE"

; kernel_init: calls the init command of every driver, gives the units of each block driver
; drive letters, then opens handles 0, 1 and 2 on CON in SFT entry 0. Needs RAM bank 0
; selected. Changes A, X and Y.
kernel_init:
        lda #<nul_driver
        sta driver_chain
        lda #>nul_driver
        sta driver_chain+1
        jsr drives_init
        jsr chain_first
@init:
        ldy #DRV_INIT
        jsr drv_call
        ldy #DRV_ATTR
        lda (driver),y
        bmi @next               ; DEV_CHAR
        jsr drives_add
@next:
        jsr drv_next
        bcc @init
        lda #$FF
        ldx #HANDLES - 1
@handle:
        sta PSP_HANDLES,x
        dex
        bpl @handle
        stz PSP_HANDLES
        stz PSP_HANDLES+1
        stz PSP_HANDLES+2
        ldy #0
@entry:
        lda #0
        sta SFT + SFT_REFS,y
        tya
        clc
        adc #SFT_SIZE
        tay
        bne @entry
        lda #3
        sta SFT + SFT_REFS
        lda #2                  ; read and write
        sta SFT + SFT_ACCESS
        lda #SFT_DEVICE
        sta SFT + SFT_FLAGS
        lda #<con_driver
        sta SFT + SFT_DRIVER
        lda #>con_driver
        sta SFT + SFT_DRIVER+1
        rts
        .assert SFT_COUNT * SFT_SIZE = 256, error, "kernel_init and api_open step Y over a page"

; chain_first: points driver at the first driver. Changes A.
chain_first:
        lda driver_chain
        sta driver
        lda driver_chain+1
        sta driver+1
        rts

; drv_next: points driver at the next driver. Returns carry set after the last. Changes A, X
; and Y.
drv_next:
        lda (driver)
        tax
        ldy #1
        lda (driver),y
        stx driver
        sta driver+1
        cmp #$FF                ; no driver lies at $FFxx
        rts

; drv_call: calls command Y of the driver at driver. Returns what the driver returns, or carry
; set and A = ERR_BAD_FUNCTION when the driver lacks the command.
drv_call:
        tya
        ldy #DRV_COUNT
        cmp (driver),y
        bcs @lacks
        asl                     ; carry clear: fewer than 128 commands
        adc #DRV_VECTORS
        tay
        lda (driver),y
        sta drv_vector
        iny
        lda (driver),y
        sta drv_vector+1
        ora drv_vector
        beq @lacks
        jmp (drv_vector)
@lacks:
        lda #ERR_BAD_FUNCTION
        sec
        rts

; bank0: selects RAM bank 0 and keeps the caller's bank in saved_bank. Changes A.
bank0:
        lda RAM_BANK
        sta saved_bank
        stz RAM_BANK
        rts

; bank_restore: selects the bank bank0 kept. Changes A, keeps carry.
bank_restore:
        lda saved_bank
        sta RAM_BANK
        rts

; sft_find: finds the SFT entry of handle X. Returns carry clear, Y = the entry's offset in
; SFT, and RAM bank 0 selected: bank_restore selects the caller's bank. Returns carry set and
; A = ERR_BAD_HANDLE when X is not an open handle. Keeps X.
sft_find:
        cpx #HANDLES
        bcs @bad
        lda PSP_HANDLES,x
        cmp #SFT_COUNT
        bcs @bad
        asl
        asl
        asl
        asl
        asl                     ; SFT_SIZE 32; carry clear
        tay
        bra bank0
@bad:
        lda #ERR_BAD_HANDLE
        rts
        .assert SFT_SIZE = 32, error, "sft_find multiplies by 32"

; to_upper: returns A in upper case when it is a letter.
to_upper:
        cmp #'a'
        bcc @done
        cmp #'z' + 1
        bcs @done
        and #$DF
@done:
        rts

api_create:
        and #$FF ^ ATTR_DIR     ; mkdir makes directories
        sta create_attr
        lda #2                  ; read and write
        sec
        bra open_common

api_open:
        cmp #3
        bcc open_common
        lda #ERR_BAD_ACCESS_CODE
        rts

; open_common: opens the path at r0 with access A: creates the file when carry is set.
open_common:
        sta open_access
        ror open_create
        jsr path_last           ; a device name works with any drive, directory or extension
        jsr chain_first
@driver:
        ldy #DRV_ATTR
        lda (driver),y
        bpl @next               ; not DEV_CHAR
        ldy #DRV_NAME + 7
        ldx #7
@compare:
        lda (driver),y
        cmp fcb_name,x
        bne @next
        dey
        dex
        bpl @compare
        lda #SFT_DEVICE
        bra @found
@next:
        jsr drv_next
        bcc @driver
        bit open_create
        bmi @create
        jsr file_find
        bcs @done
        and #ATTR_READ_ONLY
        beq @file
        lda open_access
        beq @file
        lda #ERR_ACCESS
        sec
@done:
        rts
@create:
        jsr file_create
        bcs @done
@file:
        lda dpb
@found:
        sta open_flags
        jsr handle_free
        bcs @done
        sty open_handle
        jsr bank0
        ldy #0
@entry:
        lda SFT + SFT_REFS,y
        beq @free_entry
        tya
        clc
        adc #SFT_SIZE
        tay
        bne @entry
        jsr bank_restore
        bra too_many
@free_entry:                    ; A = 0
        sta SFT + SFT_MODIFIED,y
        lda #1
        sta SFT + SFT_REFS,y
        lda open_access
        sta SFT + SFT_ACCESS,y
        lda driver
        sta SFT + SFT_DRIVER,y
        lda driver+1
        sta SFT + SFT_DRIVER+1,y
        lda open_flags
        sta SFT + SFT_FLAGS,y
        phy
        ldx #0
@state:                         ; a file's state: from file_find or file_create
        lda cluster,x
        sta SFT + SFT_CLUSTER,y
        iny
        inx
        cpx #SFT_STATE
        bne @state
        ply
        jsr bank_restore
        tya
        lsr
        lsr
        lsr
        lsr
        lsr                     ; the entry number; carry clear
        ldx open_handle
        sta PSP_HANDLES,x
        rts

; handles_inherit: counts each open handle of the PSP once more in its SFT entry: a child's PSP
; holds copies of its parent's handles. Changes A, X and Y.
handles_inherit:
        ldx #HANDLES - 1
@handle:
        jsr sft_share
        dex
        bpl @handle
        rts

; sft_share: counts handle X once more in its SFT entry. Returns carry set and A =
; ERR_BAD_HANDLE when X is not open. Keeps X. Changes Y.
sft_share:
        jsr sft_find
        bcs @done
        lda SFT + SFT_REFS,y
        inc
        sta SFT + SFT_REFS,y
        jmp bank_restore
@done:
        rts

; handle_free: returns carry clear and Y = the first closed handle, or carry set and A =
; ERR_TOO_MANY_FILES when every handle is open. Changes A.
handle_free:
        ldy #$FF
@handle:
        iny
        cpy #HANDLES
        bcs too_many
        lda PSP_HANDLES,y
        inc                     ; $FF when closed
        bne @handle
        rts                     ; carry clear
too_many:
        lda #ERR_TOO_MANY_FILES
        sec
        rts

api_dup:
        jsr sft_find            ; error 6 comes before error 4
        bcs @done
        jsr bank_restore
        jsr handle_free
        bcc handle_copy
@done:
        rts

; api_dup2 does nothing when Y is X.
api_dup2:
        sty open_handle
        jsr sft_find            ; X must be open
        bcs @done
        jsr bank_restore
        lda #ERR_BAD_HANDLE
        ldy open_handle
        cpy #HANDLES
        bcs @done
        cpx open_handle
        beq @same
        phx
        ldx open_handle
        jsr api_close           ; error 6 when Y is closed
        plx
        ldy open_handle
        bra handle_copy
@same:
        clc
@done:
        rts

; handle_copy: makes handle Y refer to the SFT entry of handle X, and returns X = Y. Returns
; carry set and A = ERR_BAD_HANDLE when X is not open.
handle_copy:
        sty open_handle
        jsr sft_share
        bcs @done
        lda PSP_HANDLES,x
        ldx open_handle
        sta PSP_HANDLES,x
@done:
        rts

; handles_close: closes every handle of the PSP. Changes A, X and Y.
handles_close:
        ldx #HANDLES - 1
@handle:
        jsr api_close           ; error 6 for a closed handle
        dex
        bpl @handle
        rts

; api_close keeps X. It closes the handle even when writing the file back fails.
api_close:
        jsr sft_find
        bcs @done
        lda SFT + SFT_REFS,y
        dec
        sta SFT + SFT_REFS,y
        lda #$FF
        sta PSP_HANDLES,x
        lda SFT + SFT_FLAGS,y
        bmi @device
        phx
        jsr file_close
        plx
        rts
@device:
        clc
        jmp bank_restore
@done:
        rts

; sft_end: returns carry set when SFT entry Y is a file whose position is at or past its size.
; RAM bank 0 must be selected. Keeps X. Changes A and Y.
sft_end:
        lda SFT + SFT_FLAGS,y
        bmi @device             ; carry clear
        phx
        ldx #4
        iny
        iny
        iny
@byte:
        lda SFT + SFT_POS,y
        cmp SFT + SFT_FILE_SIZE,y
        bne @differ
        dey
        dex
        bne @byte
@differ:
        plx
@device:
        jmp bank_restore

api_read:
        lda #1                  ; write only
        ldy #DRV_INPUT
        bra handle_io

api_write:
        lda #0                  ; read only
        ldy #DRV_OUTPUT
        ; fall through

; handle_io: calls driver command Y for handle X, unless the handle's access mode is A.
handle_io:
        sta io_refused
        sty io_slot
        jsr sft_find
        bcs @done
        lda SFT + SFT_ACCESS,y
        cmp io_refused
        beq @denied
        lda SFT + SFT_FLAGS,y
        bpl @file
        jsr sft_driver
        ldy io_slot
        jmp drv_call
@file:
        lda io_refused          ; 1 for a read, 0 for a write
        eor #1
        lsr
        ror                     ; 0 for a read, $80 for a write
        jmp file_io
@denied:
        jsr bank_restore
        lda #ERR_ACCESS
        sec
@done:
        rts

; sft_driver: points driver at the driver of SFT entry Y, then selects the caller's bank.
; Changes A, keeps carry.
sft_driver:
        lda SFT + SFT_DRIVER,y
        sta driver
        lda SFT + SFT_DRIVER+1,y
        sta driver+1
        jmp bank_restore

api_version:
        lda #VERSION_MAJOR
        ldx #VERSION_MINOR
        ldy #VERSION_PATCH
        clc
        rts

api_ticks:
        php
        sei
        ldx #3
@copy:
        lda ticks,x
        sta r0,x                ; r0 and r1
        dex
        bpl @copy
        plp
        clc
        rts

; api_ioctl has subfunction 6 only, input status: r0 = $FF when a read would give a byte,
; else 0. A file gives 0 at or past its end; a device asks its driver.
api_ioctl:
        cmp #6
        bne bad_function
        jsr sft_find
        bcs @done
        lda SFT + SFT_FLAGS,y
        bpl @file
        jsr sft_driver
        ldy #DRV_INPUT_STATUS
        jsr drv_call
        bcc @status
        rts
@file:
        jsr sft_end             ; carry set at the end
        lda #0
        sbc #0                  ; $FF when carry is clear, else 0
@status:
        sta r0
        stz r0+1
        clc
@done:
        rts

api_errmsg:
        tax
        lda #<errmsg_table
        sta r0
        lda #>errmsg_table
        sta r0+1
@record:                        ; number, length, message
        lda (r0)
        beq bad_function
        sta drv_vector
        inc r0
        bne @length
        inc r0+1
@length:
        cpx drv_vector
        beq @found
        lda (r0)
        sec
        adc r0
        sta r0
        bcc @record
        inc r0+1
        bra @record
@found:
        clc
        rts
bad_function:
        lda #ERR_BAD_FUNCTION
        sec
        rts

; io_start: io_ptr = r0, io_left = r1. Changes A.
io_start:
        lda r0
        sta io_ptr
        lda r0+1
        sta io_ptr+1
        lda r1
        sta io_left
        lda r1+1
        sta io_left+1
        rts

; io_step: moves io_ptr on by 1 and counts down io_left. Returns Z set when io_left reaches 0.
; Changes A.
io_step:
        inc io_ptr
        bne @count
        inc io_ptr+1
@count:
        lda io_left
        bne @low
        dec io_left+1
@low:
        dec io_left
        ; fall through

; io_done: returns Z set when io_left is 0. Changes A.
io_done:
        lda io_left
        ora io_left+1
        rts

; con_input: CON command 4. Reads r1 keys into the buffer at r0, without echo.
con_input:
        jsr io_start
        jsr io_done
        beq @done
@key:
        jsr CHRIN
        sta (io_ptr)
        jsr io_step
        bne @key
@done:
        clc
        rts

; con_output: CON command 8. Writes the r1 bytes at r0 to the screen.
con_output:
        jsr io_start
        jsr io_done
        beq @done
@byte:
        lda (io_ptr)
        jsr CHROUT
        jsr io_step
        bne @byte
@done:
        clc
        rts

; nul_input: NUL command 4. Reads nothing: r1 = 0.
nul_input:
        stz r1
        stz r1+1
        ; fall through

; nul_status: NUL command 6. No input waits: A = 0.
nul_status:
        lda #0
        ; fall through

; nul_output: NUL command 8. Takes every byte.
nul_output:
        clc
        rts

.segment "RODATA"

; The built-in drivers. NUL is the head of the chain.
nul_driver:
        .word con_driver
        .byte DEV_CHAR | DEV_NUL, DRV_ABI_VERSION, 9
        .byte "NUL     "
        .word 0, 0, 0, 0, nul_input, 0, nul_status, 0, nul_output

con_driver:
        .word sd_driver
        .byte DEV_CHAR | DEV_STDIN | DEV_STDOUT, DRV_ABI_VERSION, 9
        .byte "CON     "
        .word con_init, 0, 0, 0, con_input, 0, api_con_status, 0, con_output
