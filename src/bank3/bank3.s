; ROM bank 3: the UXCBASIC program that tools/build.py compiles to build/bank3/BANK3.BIN, at
; $C000, then the IRQ entry and the vectors that every bank holds.
; Trap: the program's code ends below $FFA0; ld65 stops the link when it does not.

.setcpu "65C02"

.include "mem.inc"
.include "far.inc"

; Bank 0 runs its own jmp irq, so irq here only fills the bytes.
irq             := 0

.segment "CODE"

        .incbin "BANK3.BIN"

nmi3:
        rti

.segment "FARIRQ3"

irq_entry3:
        FAR_IRQ_ENTRY
        FAR_IRQ_EXIT

; The vector pull selects bank 0, so these serve only a machine that does not.
.segment "VECTORS"

        .word nmi3
        .word nmi3              ; reset selects bank 0
        .word irq_entry3
