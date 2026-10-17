; Programs: the calls exec, exit and exitcode (PLAN section 7).
;
; exec copies the parent's PSP, memory and zero page to RAM banks, gives the child copies of the
; parent's handles and the command tail in the same PSP, loads the program and calls its start.
; exit, or RTS from the start, closes the child's handles and copies the parent back.

.setcpu "65C02"

.include "mem.inc"
.include "api.inc"

.export api_exec, api_exit, api_exitcode
.import file_find, file_copy, handles_inherit, handles_close, heap_exec, heap_exit
.importzp file_size
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

.segment "KERNELRAM"

exec_result:  .res 1            ; exec_unwind: A to return

.segment "CODE"

api_exec:
        ldx exec_depth
        cpx #EXEC_LEVELS
        bcs @no_memory
        jsr file_find
        bcs @done
        lda file_size+2         ; the load address, then up to PROGRAM_SIZE bytes
        ora file_size+3
        bne @no_memory
        lda file_size
        cmp #<(PROGRAM_SIZE + 3)
        lda file_size+1
        sbc #>(PROGRAM_SIZE + 3)
        bcs @no_memory
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
        jsr file_copy
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
        jsr file_copy
        bcs exec_fail
        jsr find_start
        pla
        pha
        sta RAM_BANK
        tsx
        stx PSP_STACK
        jsr @start
        lda #0                  ; RTS from the program: exit code 0
        bra exec_end
@start:
        jmp (exec_entry)
@bad_format:
        lda #ERR_BAD_FORMAT
        sec
        rts
@no_memory:
        lda #ERR_NO_MEMORY
        sec
@done:
        rts

exec_bad:
        lda #ERR_BAD_FORMAT
exec_fail:                      ; A = the error; the child has not run
        sec
        bra exec_unwind

api_exit:
        ldx exec_depth
        bne @running
        lda #ERR_BAD_FUNCTION   ; no program to end
        sec
        rts
@running:
        ldx PSP_STACK
        txs
        ; fall through

; exec_end: the program ended with code A. S is PSP_STACK.
exec_end:
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
        ldx #0                  ; ended by exit
        clc
        rts

; tail_copy: sets PSP_TOP to the whole program area, copies the command tail at r1 to
; COMMAND_TAIL, cut to TAIL_MAX characters, and puts CR after it. Changes A and Y.
tail_copy:
        lda #>PROGRAM_END
        sta PSP_TOP
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

; parent_copy: copies the pages from PSP to PSP_TOP, at most to PROGRAM_END, then r0 to
; PROGRAM_ZP_END, to the save banks of level exec_depth with carry clear, or back from them with
; carry set. The copy back restores the PSP first, so PSP_TOP is the parent's from the second
; page on. Changes A, X, Y and RAM_BANK.
parent_copy:
        ror copy_back
        lda exec_depth          ; the first bank: 1 + SAVE_BANKS * exec_depth
        asl
        asl
        adc exec_depth          ; carry clear: exec_depth is small
        inc
        sta RAM_BANK
        stz copy_low
        stz copy_high
        lda #>PSP
        sta copy_low+1
        lda #>BANKED_RAM
        sta copy_high+1
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
        inc copy_high+1
        lda copy_high+1
        cmp #>ROM
        bne @same_bank
        lda #>BANKED_RAM
        sta copy_high+1
        inc RAM_BANK
@same_bank:
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
        rts
        .assert SAVE_BANKS = 5, error, "parent_copy multiplies by 5"
        .assert PROGRAM_ZP_END = $7F, error, "parent_copy ends the zero page with BPL"
        .assert <PSP = 0 && <(PROGRAM_END + 1) = 0, error, "parent_copy copies whole pages"
        .assert >(PROGRAM_END + 1) - >PSP < SAVE_BANKS * 32, error, "the save banks need a page for the zero page"
        .assert 1 + SAVE_BANKS * EXEC_LEVELS <= 64, error, "the save banks pass 512 KB"
