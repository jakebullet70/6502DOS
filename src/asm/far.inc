; Calls between ROM banks. gate.s holds the bank 0 copies of jsrfar and the IRQ entry, bank1.s
; the bank 1 copies. Include mem.inc first.

; FARCALL target [, entry]: calls target in its ROM bank, from any bank. entry is the jsrfar of
; the calling bank: jsrfar in bank 0, the default; jsrfar1 in bank 1. 6 bytes.
.macro FARCALL target, entry
    .ifblank entry
        jsr jsrfar
    .else
        jsr entry
    .endif
        .addr target
        .byte <.bank(target)
.endmacro

; JSRFAR: the body of jsrfar. Entered by JSR, then a routine's address and its ROM bank, 3
; bytes. Calls the routine in its bank and returns past the 3 bytes, in the caller's bank. A,
; X, Y and C go in and come out; N and Z come out from A. Uses gate_a, gate_x and gate_vector,
; and ends in the gate's tail, gate_far.
.macro JSRFAR
        sta gate_a
        stx gate_x
        pla                     ; the return address: the JSR's last byte
        sta gate_vector
        pla
        sta gate_vector+1
        php
        clc
        lda gate_vector
        adc #3
        tax
        lda gate_vector+1
        adc #0
        plp                     ; C as it came
        pha                     ; the return address past the 3 bytes
        phx
        lda ROM_BANK
        pha                     ; the caller's bank, for gate_far
        phy
        ldy #1
        lda (gate_vector),y
        tax                     ; the routine's address
        iny
        lda (gate_vector),y
        pha
        iny
        lda (gate_vector),y     ; its bank
        stx gate_vector
        plx
        stx gate_vector+1
        ply
        jmp gate_far
.endmacro

; FAR_IRQ_ENTRY: the IRQ entry of every ROM bank. Saves A and the interrupted ROM bank, selects
; bank 0 and jumps to irq. FAR_IRQ_EXIT selects the saved bank again and returns from the
; interrupt.
; Trap: an interrupt's vector pull selects bank 0, but ROM_BANK still reads the interrupted
; bank until written. A write to ROM_BANK goes on at the next address in the other bank, so
; every bank holds these bytes at the same address: segment FARIRQ0 in bank 0, FARIRQ1 in bank 1.
.macro FAR_IRQ_ENTRY
        pha
        lda ROM_BANK
        pha
        stz ROM_BANK
        jmp irq
.endmacro

.macro FAR_IRQ_EXIT
        pla
        sta ROM_BANK
        pla
        rti
.endmacro
