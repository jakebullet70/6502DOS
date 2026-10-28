; Programs: the calls exec, exit and exitcode (PLAN section 7).
;
; exec copies the parent's PSP, memory and zero page to RAM banks, gives the child copies of the
; parent's handles and the command tail in the same PSP, loads the program and calls its start.
; exit, or RTS from the start, closes the child's handles and copies the parent back. keep does
; the same but keeps the child's banks. A file that fills $0801-$9EFF stays open, and exec_rest
; reads the rest of it.

.setcpu "65C02"

.include "mem.inc"
.include "api.inc"
.include "far.inc"

.export api_exec, api_exec_rest, api_exit, api_exitcode, api_keep, exec_break
.import handles_inherit, handles_close, heap_exec, heap_exit, CHROUT, con_hide
.import api_bank_alloc, api_bank_free, bank_exit
.import jsrfar, bank0, lib_open, lib_read, lib_close
.importzp file_size, saved_bank
.exportzp exec_depth

SYS_TOKEN     = $9E             ; BASIC's SYS
PROGRAM_SIZE  = PROGRAM_END + 1 - PROGRAM

.segment "KERNELZP" : zeropage

exec_depth:   .res 1            ; the programs running under exec, 0 to EXEC_LEVELS
exit_code:    .res 1            ; the code of the last program that ended
copy_low:     .res 2            ; parent_copy: a page from PSP to PROGRAM_END
copy_high:    .res 2            ; parent_copy: a page of the save
copy_back:    .res 1            ; parent_copy: bit 7 set to copy to the parent
exec_entry:   .res 2            ; the load address, then the program's start
save_bank:    .res EXEC_LEVELS  ; the first bank of each level's save
exec_open:    .res 1            ; bit 7 set while the running program's file is open

.segment "KERNELRAM"

exec_result:  .res 1            ; exec_unwind: A to return
exit_how:     .res 1            ; how the last program ended: 0 exit, 1 break, 3 keep
exec_file:    .res 1            ; the program file's context in the FAT32 library

.segment "CODE"

api_exec:
        ldx exec_depth
        cpx #EXEC_LEVELS
        bcc @open
        lda #ERR_NO_MEMORY
        rts                     ; carry set
@open:
        jsr rest_close          ; exec_file takes the new program's file
        lda #0                  ; read; carry clear: no create
        FARCALL lib_open
        bcc @opened
        rts
@opened:
        sta exec_file
        lda file_size+1         ; the load address, then a byte at least
        ora file_size+2
        ora file_size+3
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
        lda #<PROGRAM_SIZE      ; up to PROGRAM_END
        sta r1
        lda #>PROGRAM_SIZE
        sta r1+1
        jsr exec_read
        bcs exec_fail
        lda r1                  ; a full area stays open for exec_rest
        eor #<PROGRAM_SIZE
        bne @short
        lda r1+1
        eor #>PROGRAM_SIZE
        bne @short
        dec exec_open           ; $FF: exec_open is 0 since rest_close
        bra @loaded
@short:
        jsr exec_close
@loaded:
        jsr find_start
        pla
        pha
        sta RAM_BANK
        tsx
        stx PSP_STACK
        stz SYS_P               ; a UXCBASIC program's first SYS loads P from it
        jsr @start
        lda #0                  ; RTS from the program: exit code 0
        bra exit_normal
@start:
        jmp (exec_entry)
@bad_format:
        lda #ERR_BAD_FORMAT
        bra @refused
@full:                          ; no run of banks for the save
        pla
        sta RAM_BANK
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

; api_exec_rest: exec_rest, call 52. Reads r1 bytes of the running program's file to r0, or
; closes the file for r1 = 0.
api_exec_rest:
        bit exec_open
        bpl @none
        lda r1
        ora r1+1
        bne exec_read
        jsr rest_close
        clc
        rts
@none:
        lda #ERR_BAD_HANDLE
        sec
        rts

; rest_close: closes the running program's file when exec left it open. Changes A, X and Y.
rest_close:
        bit exec_open
        bpl exec_open_rts
        stz exec_open
        ; fall through

; exec_close: closes the program file. Changes A, X and Y.
exec_close:
        jsr bank0
        lda exec_file
        FARCALL lib_close
exec_bank:
        ldx saved_bank          ; keeps A and carry
        stx RAM_BANK
exec_open_rts:
        rts

; exec_read: reads r1 bytes of the program file to r0. Returns carry set and A = the error.
; Changes X and Y.
exec_read:
        jsr bank0
        lda exec_file
        FARCALL lib_read
        bra exec_bank

api_keep:
        ldy #BANK_KEPT
        ldx exec_depth
        beq exit_none
        pha
        jsr bank_exit           ; exec_unwind's bank_exit then finds none
        pla
        ldx #3                  ; ended by keep
        bra exec_quit

api_exit:
        ldx exec_depth
        bne exit_normal
exit_none:
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

; exec_quit: the program ended with code A, in the way X. Unwinds the stack to PSP_STACK and
; shows the cursor again.
exec_quit:
        stx exit_how
        ldx PSP_STACK
        txs
        sta exit_code
        stz con_hide
        cld
        clc
        ; fall through

; exec_unwind: closes the child's handles, copies the parent back and returns from exec with A
; and carry. The parent's RAM bank is on the stack.
exec_unwind:
        sta exec_result
        php
        jsr rest_close
        jsr handles_close
        jsr heap_exit
        ldy #0                  ; free the child's banks
        jsr bank_exit
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
; carry set. A save takes a run of banks from bank_alloc, and the copy back frees it. The copy
; back restores the PSP first, so PSP_TOP is the parent's from the second page on. Returns carry
; set when no run is free. Changes A, X, Y and RAM_BANK.
parent_copy:
        ror copy_back
        bmi @bank
        lda PSP_TOP             ; the banks of PSP_TOP - >PSP + 2 pages, rounded up
        clc
        adc #32 + 1 - >PSP
        ror
        lsr
        lsr
        lsr
        lsr
        bne @take
        inc                     ; PSP_TOP below PSP: one page, then the zero page
@take:
        jsr api_bank_alloc
        bcs @full
        ldx exec_depth
        sta save_bank,x
@bank:
        ldx exec_depth
        lda save_bank,x
        sta RAM_BANK
        lda #>BANKED_RAM
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
        inc copy_high+1
        lda copy_high+1
        cmp #>ROM
        bne @in_bank
        lda #>BANKED_RAM
        sta copy_high+1
        inc RAM_BANK
@in_bank:
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
        bit copy_back
        bpl @saved
        lda save_bank,x
        jmp api_bank_free       ; carry clear
@saved:
        clc
@full:
        rts
        .assert PROGRAM_ZP_END = $7F, error, "parent_copy ends the zero page with BPL"
        .assert <PSP = 0 && <(PROGRAM_END + 1) = 0, error, "parent_copy copies whole pages"