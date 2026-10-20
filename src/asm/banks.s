; The bank allocator: the calls bank_alloc and bank_free (PLAN section 3, Banked RAM).
;
; BANK_OWNER in RAM bank 0 holds a byte for each RAM bank: 0 when free, BANK_SYSTEM for the
; kernel's banks and the banks the machine lacks, else the exec depth of the program that took it
; plus 1. BANK_FIRST marks the first bank of a run bank_alloc handed out. exit frees the banks of
; the program that ends.

.setcpu "65C02"

.include "mem.inc"
.include "api.inc"

.export api_bank_alloc, api_bank_free, bank_init, bank_exit
.import bank0
.importzp exec_depth, saved_bank

.segment "KERNELRAM"

bank_want:    .res 1            ; bank_alloc: the length of the run; bank_exit: the owner

.segment "CODE"

; bank_init: marks bank 0, the save banks and VARBANK as the system's, the banks after them as
; free, and the banks the machine lacks as the system's. A machine has 64, 128 or 256 banks. Bank
; 64 or 128 is missing when a byte written to it reads back wrong or lands in bank 0. Needs RAM
; bank 0 selected. Changes A, X and Y.
bank_init:
        stz BANK_OWNER          ; bank 0's probe byte
        lda #64
@probe:
        sta RAM_BANK
        sta BANK_OWNER          ; the same address in bank A
        cmp BANK_OWNER
        stz RAM_BANK            ; keeps Z
        bne @size               ; bank A reads back wrong
        ldx BANK_OWNER
        bne @size               ; bank A is bank 0
        asl
        bne @probe              ; 128, then 0 for 256 banks
@size:
        tay                     ; the number of banks, 0 for 256
        ldx #0
        lda #BANK_SYSTEM
@system:
        sta BANK_OWNER,x
        inx
        bne @system
        tya
        tax
@free:
        dex
        stz BANK_OWNER,x
        cpx #VARBANK + 1
        bne @free
        rts
        .assert VARBANK < 63, error, "bank_init frees banks from VARBANK + 1 up"

; api_bank_alloc: takes the lowest run of A free banks. A = 0 counts the free banks instead.
api_bank_alloc:
        sta bank_want
        jsr bank0
        ldx #0
        ldy #0
        lda bank_want
        bne @scan
@count:
        lda BANK_OWNER,x
        bne @used
        iny
@used:
        inx
        bne @count
        tya
        clc
        bra bank_done
@scan:                          ; Y = the length of the free run that ends at bank X
        inx
        beq @none
        lda BANK_OWNER,x
        beq @free
        ldy #0
        bra @scan
@free:
        iny
        cpy bank_want
        bne @scan
        lda exec_depth          ; the run ends at bank X
        inc
@take:
        sta BANK_OWNER,x
        dex
        dey
        bne @take
        inx
        ora #BANK_FIRST
        sta BANK_OWNER,x
        txa
        clc
        bra bank_done
@none:
        lda #ERR_NO_MEMORY
        sec
        ; fall through

; bank_done: selects the caller's RAM bank and returns. Keeps A, X and carry.
bank_done:
        ldy saved_bank
        sty RAM_BANK
        rts

; api_bank_free: frees the run of banks that starts at bank A.
api_bank_free:
        tax
        jsr bank0
        lda exec_depth
        inc
        ora #BANK_FIRST
        cmp BANK_OWNER,x
        bne @bad                ; not the first bank of a run of this program
        and #<~BANK_FIRST
@free:
        stz BANK_OWNER,x
        inx
        beq @done
        cmp BANK_OWNER,x
        beq @free
@done:
        clc
        bra bank_done
@bad:
        lda #ERR_BAD_BLOCK
        sec
        bra bank_done

; bank_exit: frees the banks of the program at exec_depth. Selects RAM bank 0. Changes A and X.
bank_exit:
        stz RAM_BANK
        ldx exec_depth
        inx
        stx bank_want
        ldx #0
@bank:
        lda BANK_OWNER,x
        and #<~BANK_FIRST
        cmp bank_want
        bne @next
        stz BANK_OWNER,x
@next:
        inx
        bne @bank
        rts
