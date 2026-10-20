; Programs: the calls exec, exit and exitcode (PLAN section 7).
;
; exec copies the parent's PSP, memory and zero page to RAM banks, gives the child copies of the
; parent's handles and the command tail in the same PSP, loads the program and calls its start.
; exit, or RTS from the start, closes the child's handles and copies the parent back.

.setcpu "65C02"

.include "mem.inc"
.include "api.inc"
.include "far.inc"

.export api_exec, api_exit, api_exitcode, exec_break
.import handles_inherit, handles_close, heap_exec, heap_exit, CHROUT
.import jsrfar, bank0, lib_open, lib_read, lib_close
.importzp file_size, saved_bank
.exportzp exec_depth

SYS_TOKEN     = $9E             ; BASIC's SYS
PROGRAM_SIZE  = PROGRAM_END + 1 - PROGRAM

.segment "KERNELZP" : zeropage

exec_depth:   .res 1            ; the programs running under exec, 0 to EXEC_LEVELS
exit_code:    .res 1            ; the code of the last program that ended
copy_low:     .res 2            ; parent_copy: a page from PSP to PROGRAM_END
copy_high:    .res 2            ; parent_copy: a page of the save banks
copy_back:    .res 1            ; parent_copy: bit 7 set to copy to the parent
exec_entry:   .res 2            ; the load address, then the program's start
save_bank:    .res EXEC_LEVELS + 1 ; where the save of each level starts: the bank - 1
save_page:    .res EXEC_LEVELS + 1 ; and the page EOR >BANKED_RAM; reset zeroes level 0's

.segment "KERNELRAM"

exec_result:  .res 1            ; exec_unwind: A to return
exit_how:     .res 1            ; how the last program ended: 0 exit, 1 break
exec_file:    .res 1            ; the program file's context in the FAT32 library

.segment "CODE"

api_exec:
        ldx exec_depth
        cpx #EXEC_LEVELS
        bcc @open
        lda #ERR_NO_MEMORY
        rts                     ; carry set
@open:
        lda #0                  ; read; carry clear: no create
        FARCALL lib_open
        bcc @opened
        rts
@opened:
        sta exec_file
        lda file_size+2         ; the load address, then up to PROGRAM_SIZE bytes
        ora file_size+3
        bne @too_big
        lda file_size
        cmp #<(PROGRAM_SIZE + 3)
        lda file_size+1
        sbc #>(PROGRAM_SIZE + 3)
        bcs @too_big
        lda file_size+1
        bne @fits
        lda file_size
        cmp #3
        bcc @bad_format
@fits:
        lda RAM_BANK
        pha                     ; the child's bank, then the parent's again
        clc
        jsr parent_copy
        bcs @full
        inc exec_depth
        jsr tail_copy           ; r0 and r1 are the caller's up to here
        jsr handles_inherit
        jsr heap_exec
        lda #<exec_entry
        sta r0
        lda #>exec_entry
        sta r0+1
        lda #2
        sta r1
        stz r1+1
        jsr exec_read
        bcs exec_fail
        lda exec_entry
        cmp #<PROGRAM
        bne exec_bad
        lda exec_entry+1
        cmp #>PROGRAM
        bne exec_bad
        lda #<PROGRAM
        sta r0
        lda #>PROGRAM
        sta r0+1
        lda #$FF                ; the rest of the file
        sta r1
        sta r1+1
        jsr exec_read
        bcs exec_fail
        jsr exec_close
        jsr find_start
        pla
        pha
        sta RAM_BANK
        tsx
        stx PSP_STACK
        jsr @start
        lda #0                  ; RTS from the program: exit code 0
        bra exit_normal
@start:
        jmp (exec_entry)
@bad_format:
        lda #ERR_BAD_FORMAT
        bra @refused
@full:                          ; the save banks are full
        pla
        sta RAM_BANK
@too_big:
        lda #ERR_NO_MEMORY
@refused:                       ; the program file is open
        pha
        jsr exec_close
        pla
        sec
        rts

exec_bad:
        lda #ERR_BAD_FORMAT
exec_fail:                      ; A = the error; the child has not run
        pha
        jsr exec_close
        pla
        sec
        bra exec_unwind

; exec_read: reads r1 bytes of the program file to r0. Returns carry set and A = the error.
; Changes X and Y.
exec_read:
        jsr bank0
        lda exec_file
        FARCALL lib_read
        bra exec_bank

; exec_close: closes the program file. Changes A, X and Y.
exec_close:
        jsr bank0
        lda exec_file
        FARCALL lib_close
exec_bank:
        ldx saved_bank          ; keeps A and carry
        stx RAM_BANK
        rts

api_exit:
        ldx exec_depth
        bne exit_normal
        lda #ERR_BAD_FUNCTION   ; no program to end
        sec
        rts

; exec_break: prints ^C and ends the running program with code 0, by break. con_status jumps
; here for Ctrl+C in BREAK_END, from inside any call; exec sets that mode only for a child.
exec_break:
        ldx #0
@echo:
        lda break_text,x
        jsr CHROUT              ; keeps X
        inx
        cpx #BREAK_TEXT_SIZE
        bne @echo
        lda #0
        ldx #1                  ; ended by break
        bra exec_quit

exit_normal:
        ldx #0                  ; ended by exit
        ; fall through

; exec_quit: the program ended with code A, in the way X. Unwinds the stack to PSP_STACK.
exec_quit:
        stx exit_how
        ldx PSP_STACK
        txs
        sta exit_code
        cld
        clc
        ; fall through

; exec_unwind: closes the child's handles, copies the parent back and returns from exec with A
; and carry. The parent's RAM bank is on the stack.
exec_unwind:
        sta exec_result
        php
        jsr handles_close
        jsr heap_exit
        dec exec_depth
        sec
        jsr parent_copy
        plp
        pla
        sta RAM_BANK
        lda exec_result
        rts

api_exitcode:
        lda exit_code
        ldx exit_how
        clc
        rts

.segment "RODATA"

break_text:
        .byte "^C", $0D, $0A
BREAK_TEXT_SIZE = * - break_text

.segment "CODE"

; tail_copy: sets PSP_TOP to the whole program area and PSP_BREAK to BREAK_END, copies the
; command tail at r1 to COMMAND_TAIL, cut to TAIL_MAX characters, and puts CR after it. Changes A
; and Y.
tail_copy:
        lda #>PROGRAM_END
        sta PSP_TOP
        lda #BREAK_END
        sta PSP_BREAK
        lda (r1)
        cmp #TAIL_MAX + 1
        bcc @length
        lda #TAIL_MAX
@length:
        tay
        lda #$0D
        sta COMMAND_TAIL+1,y
        sty COMMAND_TAIL
        tya
        beq @done
@char:
        lda (r1),y
        sta COMMAND_TAIL,y
        dey
        bne @char
@done:
        rts

; find_start: sets exec_entry to n when the program starts with the BASIC line SYS n, else to
; PROGRAM. Changes A, X, Y and r2.
find_start:
        stz exec_entry
        stz exec_entry+1
        lda PROGRAM+1           ; the next line's address: a short first line ends in page 8
        cmp #>PROGRAM
        bne @machine
        lda PROGRAM+4           ; after the next line's address and the line number
        cmp #SYS_TOKEN
        bne @machine
        ldx #5
@digit:
        lda PROGRAM,x
        inx
        cmp #' '
        beq @digit
        eor #'0'
        cmp #10
        bcs @done
        tay
        lda exec_entry          ; exec_entry * 10 + the digit
        sta r2
        lda exec_entry+1
        sta r2+1
        asl exec_entry
        rol exec_entry+1
        asl exec_entry
        rol exec_entry+1
        clc
        lda exec_entry
        adc r2
        sta exec_entry
        lda exec_entry+1
        adc r2+1
        sta exec_entry+1
        asl exec_entry
        rol exec_entry+1
        tya
        clc
        adc exec_entry
        sta exec_entry
        bcc @digit
        inc exec_entry+1
        bra @digit
@machine:
        lda #<PROGRAM
        sta exec_entry
        lda #>PROGRAM
        sta exec_entry+1
@done:
        rts

; parent_copy: copies the pages from PSP to PSP_TOP, at most to PROGRAM_END, then a page of r0
; to PROGRAM_ZP_END, to the save of level exec_depth with carry clear, or back from it with
; carry set. Sets the start of the next level's save to the page after. The copy back restores
; the PSP first, so PSP_TOP is the parent's from the second page on. Returns carry set when the
; save does not fit in the save banks. Changes A, X, Y and RAM_BANK.
parent_copy:
        ror copy_back
        ldx exec_depth
        lda save_bank,x
        inc
        sta RAM_BANK
        lda save_page,x
        eor #>BANKED_RAM
        sta copy_high+1
        stz copy_low
        stz copy_high
        lda #>PSP
        sta copy_low+1
        ldy #0
@page:
        bit copy_back
        bmi @back
@save:
        lda (copy_low),y
        sta (copy_high),y
        iny
        bne @save
        bra @next
@back:
        lda (copy_high),y
        sta (copy_low),y
        iny
        bne @back
@next:
        inc copy_low+1
        jsr next_page
        bcs @full               ; only a save: a copy back fits
        lda copy_low+1
        cmp #>(PROGRAM_END + 1)
        beq @zero_page
        dec                     ; the page just copied
        cmp PSP_TOP
        bcc @page
@zero_page:
        ldy #r0                 ; the zero page, after the last page
@zp:
        bit copy_back
        bmi @zp_back
        lda a:0,y
        sta (copy_high),y
        bra @zp_next
@zp_back:
        lda (copy_high),y
        sta a:0,y
@zp_next:
        iny
        bpl @zp
        jsr next_page           ; a copy back writes the same start again
        lda RAM_BANK
        dec
        sta save_bank+1,x
        lda copy_high+1
        eor #>BANKED_RAM
        sta save_page+1,x
        clc
@full:
        rts
        .assert PROGRAM_ZP_END = $7F, error, "parent_copy ends the zero page with BPL"
        .assert <PSP = 0 && <(PROGRAM_END + 1) = 0, error, "parent_copy copies whole pages"
        .assert >(PROGRAM_END + 1) - >PSP < SAVE_BANKS * 32, error, "a full save fits the save banks"
        .assert VARBANK <= 64, error, "the save banks pass 512 KB"

; next_page: moves copy_high to the next page of the save banks. Returns carry set when that page
; is in VARBANK. Changes A and RAM_BANK.
next_page:
        inc copy_high+1
        lda copy_high+1
        cmp #>ROM
        clc
        bne @done
        lda #>BANKED_RAM
        sta copy_high+1
        inc RAM_BANK
        lda RAM_BANK
        cmp #VARBANK
@done:
        rts
