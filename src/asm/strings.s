; String heaps: the calls str_alloc, str_free, str_gc and str_heap (PLAN section 3).
;
; A heap is one RAM bank. HEAP_BUMP holds the address of the next block, HEAP_FLOORS the lowest
; block that GC moves at each exec depth, then the blocks follow. A block is the owner, 2 bytes,
; the length, 1 byte, then the text. The owner is the address of the descriptor, 0 for a free
; block. A descriptor is 2 bytes that hold the address of the block's length byte: in program
; RAM, or at $A000-$BFFF in the heap's own bank. A block is live while its owner points back
; at it.
;
; VARBANK is the shared heap. PSP_HEAP holds the bank of the running program's heap; exec gives
; the child VARBANK. exec sets the child's floor in VARBANK to the bump pointer, so a child's GC
; never moves a block whose descriptor is in a save bank. exit drops the child's blocks in
; VARBANK whose owners are in program RAM and compacts from the child's floor.

.setcpu "65C02"

.include "mem.inc"
.include "api.inc"

.export api_str_alloc, api_str_free, api_str_gc, api_str_heap
.export heap_init, heap_exec, heap_exit
.importzp exec_depth

.segment "KERNELZP" : zeropage

gc_from:      .res 2            ; heap_gc: the block it looks at; room: the end of the new block
gc_to:        .res 2            ; heap_gc: where the next live block goes; room: the new block
gc_owner:     .res 2            ; heap_gc: the owner of the block at gc_from

.segment "KERNELRAM"

str_len:      .res 1            ; str_alloc: the length; heap_gc: the length of the block
gc_exit:      .res 1            ; heap_gc: bit 7 set when exit drops program RAM owners
heap_caller:  .res 1            ; the caller's RAM bank, while the heap's bank is selected

.segment "CODE"

; heap_init: makes VARBANK an empty heap with no system strings, and the running program's
; heap. Selects RAM bank 0 after. Changes A, X, r0.
heap_init:
        lda #VARBANK
        sta PSP_HEAP
        sta RAM_BANK
        ldx #SYSTEM_STRINGS * 2
@zero:
        stz HEAP_SYSTEM - 1,x
        dex
        bne @zero
        lda #<VARBANK_BLOCKS
        sta r0
        lda #>VARBANK_BLOCKS
        sta r0+1
        jsr heap_fill
        stz RAM_BANK
        rts
        .assert SYSTEM_STRINGS * 2 < 256, error, "heap_init counts the system descriptors in X"

; heap_fill: sets the bump pointer and every floor of the selected heap to r0. Changes A and X.
heap_fill:
        ldx #(EXEC_LEVELS + 2) * 2
@word:
        lda r0+1
        sta HEAP_BUMP - 1,x
        dex
        lda r0
        sta HEAP_BUMP - 1,x
        dex
        bne @word
        rts
        .assert HEAP_FLOORS = HEAP_BUMP + 2, error, "heap_fill writes the bump pointer, then the floors"

; heap_exec: gives the child of exec_depth VARBANK, and sets its floor there to the bump
; pointer. Changes A, X and RAM_BANK.
heap_exec:
        lda #VARBANK
        sta PSP_HEAP
        sta RAM_BANK
        lda exec_depth
        asl
        tax
        lda HEAP_BUMP
        sta HEAP_FLOORS,x
        lda HEAP_BUMP+1
        sta HEAP_FLOORS+1,x
        rts

; heap_exit: drops the blocks in VARBANK of the program at exec_depth whose owners are in program
; RAM, and compacts VARBANK from its floor. Changes A, X, Y and RAM_BANK.
heap_exit:
        lda #VARBANK
        sta RAM_BANK
        sec
        jmp heap_gc

api_str_alloc:
        sta str_len
        jsr owner_check
        bcs @done
        jsr heap_bank
        jsr room
        bcc @fits
        clc
        jsr heap_gc
        jsr room
        bcc @fits
        lda #ERR_NO_MEMORY
        jmp heap_done
@fits:
        lda r0                  ; the block at gc_to: the owner, the length
        sta (gc_to)
        ldy #1
        lda r0+1
        sta (gc_to),y
        iny
        lda str_len
        sta (gc_to),y
        clc                     ; r1 and the descriptor: the length byte
        lda gc_to
        adc #2
        sta r1
        sta (r0)
        lda gc_to+1
        adc #0
        sta r1+1
        dey
        sta (r0),y
        lda gc_from
        sta HEAP_BUMP
        lda gc_from+1
        sta HEAP_BUMP+1
        lda PSP_HEAP
        clc
        jmp heap_done
@done:
        rts

api_str_free:
        jsr owner_check
        bcs @done
        jsr heap_bank
        ldy #1
        lda (r0)
        ora (r0),y
        beq @empty
        lda (r0)                ; gc_to: the block, 2 bytes before the length byte
        sec
        sbc #2
        sta gc_to
        lda (r0),y
        sbc #0
        sta gc_to+1
        cmp #>BANKED_RAM
        bcc @bad
        cmp #>ROM
        bcs @bad
        lda (gc_to)
        cmp r0
        bne @bad
        lda (gc_to),y
        cmp r0+1
        bne @bad
        lda #0
        sta (gc_to)
        sta (gc_to),y
        sta (r0)
        sta (r0),y
@empty:
        clc
        jmp heap_done
@bad:
        lda #ERR_BAD_BLOCK
        sec
        jmp heap_done
@done:
        rts

api_str_gc:
        jsr heap_bank
        clc
        jsr heap_gc
        sec
        lda #<ROM
        sbc HEAP_BUMP
        sta r0
        lda #>ROM
        sbc HEAP_BUMP+1
        sta r0+1
        clc
        bra heap_done

api_str_heap:
        cmp #VARBANK
        bne @own
        sta PSP_HEAP
        clc
        rts
@own:                           ; a bank of a run the program took from bank_alloc
        tax
        ldy RAM_BANK
        stz RAM_BANK
        lda BANK_OWNER,x
        sty RAM_BANK
        and #<~BANK_FIRST
        dec
        cmp exec_depth
        bne bad_block
        stx PSP_HEAP
        jsr heap_bank
        jsr heap_fill
        clc
        bra heap_done

; owner_check: returns carry set and A = ERR_BAD_BLOCK when r0 can not hold a descriptor: at $0000
; or $0001, in the I/O page, or at $C000 and above. Changes X.
owner_check:
        ldx r0+1
        bne @page
        ldx r0
        cpx #r0
        bcc bad_block
        clc
        rts
@page:
        cpx #>(PROGRAM_END + 1)
        beq bad_block
        cpx #>ROM
        bcs bad_block
        rts
bad_block:
        lda #ERR_BAD_BLOCK
        sec
        rts

; heap_bank: selects the heap of the running program and keeps the caller's bank in
; heap_caller. Changes A.
heap_bank:
        lda RAM_BANK
        sta heap_caller
        lda PSP_HEAP
        sta RAM_BANK
        rts

; heap_done: selects the bank heap_bank kept and returns from the call. Keeps A and carry.
heap_done:
        ldx heap_caller
        stx RAM_BANK
        rts

; room: sets gc_to to the bump pointer and gc_from to the end of a block of str_len bytes there.
; Returns carry clear when the block ends at ROM or below. Changes A and X.
room:
        lda HEAP_BUMP+1
        sta gc_to+1
        tax
        lda HEAP_BUMP
        sta gc_to
        sec                     ; + str_len + 1
        adc str_len
        bcc @add
        inx
        clc
@add:
        adc #2
        bcc @end
        inx
@end:
        sta gc_from
        stx gc_from+1
        cpx #>ROM
        bcc @done
        bne @done
        cmp #1
@done:
        rts

; heap_gc: compacts the selected heap from the floor of exec_depth to the bump pointer, and sets
; the bump pointer after the last live block. Each live block moves down and its descriptor
; follows. With carry set a block whose owner is below BANKED_RAM is dead too. Changes A, X
; and Y.
heap_gc:
        ror gc_exit
        lda exec_depth
        asl
        tax
        lda HEAP_FLOORS,x
        sta gc_from
        sta gc_to
        lda HEAP_FLOORS+1,x
        sta gc_from+1
        sta gc_to+1
@block:
        lda gc_from
        cmp HEAP_BUMP
        lda gc_from+1
        sbc HEAP_BUMP+1
        bcs @end
        lda (gc_from)
        sta gc_owner
        ldy #1
        lda (gc_from),y
        sta gc_owner+1
        iny
        lda (gc_from),y
        sta str_len
        bit gc_exit
        bpl @owner
        lda gc_owner+1
        cmp #>BANKED_RAM
        bcc @dead
@owner:
        lda gc_owner
        ora gc_owner+1
        beq @dead               ; free
        lda gc_from             ; live when the descriptor holds gc_from + 2
        clc
        adc #2
        tax
        lda gc_from+1
        adc #0
        dey
        cmp (gc_owner),y
        bne @dead
        txa
        cmp (gc_owner)
        bne @dead
        lda gc_to
        cmp gc_from
        bne @move
        lda gc_to+1
        cmp gc_from+1
        bne @move
        jsr gc_skip_block       ; no dead block below: it stays
        lda gc_from
        sta gc_to
        lda gc_from+1
        sta gc_to+1
        bra @block
@move:
        clc                     ; the descriptor: gc_to + 2
        lda gc_to
        adc #2
        sta (gc_owner)
        lda gc_to+1
        adc #0
        sta (gc_owner),y
        lda #3
        jsr gc_move
        lda str_len
        jsr gc_move
        bra @block
@dead:
        jsr gc_skip_block
        bra @block
@end:
        lda gc_to
        sta HEAP_BUMP
        lda gc_to+1
        sta HEAP_BUMP+1
        rts

; gc_move: copies A bytes, 0 to 255, from gc_from to gc_to, and adds A to both. Changes A, X
; and Y.
gc_move:
        tax
        beq gc_done
        ldy #0
@byte:
        lda (gc_from),y
        sta (gc_to),y
        iny
        dex
        bne @byte
        tya
        clc
        adc gc_to
        sta gc_to
        bcc @to
        inc gc_to+1
@to:
        tya
        bra gc_skip

; gc_skip_block: adds the block's size, str_len + 3, to gc_from. Changes A.
gc_skip_block:
        lda str_len
        sec
        adc #2
        bcc gc_skip
        inc gc_from+1
        ; fall through

; gc_skip: adds A to gc_from. Changes A.
gc_skip:
        clc
        adc gc_from
        sta gc_from
        bcc gc_done
        inc gc_from+1
gc_done:
        rts
