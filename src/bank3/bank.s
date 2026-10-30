; ROM bank BANK, one of a UXCBASIC program's banks: the program's file that tools/build.py
; compiles to BANKn.BIN, at $C000, then the IRQ entry and the vectors that every bank holds.
; tools/build.py assembles it once a bank: -D BANK=3 and 4 for build/bank3, 6, 7 and 8 for
; build/bank6. A later bank's file is empty when the program fits the banks before it.
; Trap: the program's file ends at $FFA0 at most; ld65 stops the link when it does not.

.setcpu "65C02"

.include "mem.inc"
.include "far.inc"

; Bank 0 runs its own jmp irq, so irq here only fills the bytes.
irq             := 0

.segment "CODE"

        .incbin .sprintf("BANK%d.BIN", BANK)

.segment "FARIRQ"

irq_entry:
        FAR_IRQ_ENTRY
        FAR_IRQ_EXIT

nmi:
        rti

; The vector pull selects bank 0, so these serve only a machine that does not.
.segment "VECTORS"

        .word nmi
        .word nmi               ; reset selects bank 0
        .word irq_entry
