; 6502DOS ROM bank 1: jsrfar1, the IRQ entry and the vectors of the bank.

.setcpu "65C02"

.include "mem.inc"
.include "far.inc"

.export jsrfar1
.importzp gate_a, gate_x, gate_vector, ticks
.import gate_far, irq, CHROUT, api_con_colour

.segment "B1JUMPS"

; b1_probe: tests/FAR.S calls it with bank 1 selected. Waits for a VSYNC IRQ taken in bank 1,
; writes "B" through CHROUT in bank 0, and returns api_con_colour's A and C from bank 0, with
; X = $5A and Y = $A5.
b1_probe:
        lda ticks
@wait:
        cmp ticks
        beq @wait
        ldx #$5A
        ldy #$A5
        lda #'B'
        FARCALL CHROUT, jsrfar1
        sec                     ; get the color
        FARCALL api_con_colour, jsrfar1
        rts

.segment "B1CODE"

; jsrfar1: JSRFAR in far.inc, for bank 1. FARCALL with entry jsrfar1 calls it.
jsrfar1:
        JSRFAR

nmi1:
        rti

.segment "FARIRQ1"

irq_entry1:
        FAR_IRQ_ENTRY
        FAR_IRQ_EXIT

; The vector pull selects bank 0, so these serve only a machine that does not.
.segment "B1VECTORS"

        .word nmi1
        .word nmi1              ; reset selects bank 0
        .word irq_entry1
